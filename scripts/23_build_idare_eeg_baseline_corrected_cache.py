#!/usr/bin/env python3
"""Build a separate baseline-corrected NumPy cache of I-DARE EEG windows.

Outputs default to new files and never overwrite the original cache unless
explicitly requested with --force:

- .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy
- .cache/idare_eeg_cache_index_baseline_corrected.csv
- docs/idare_eeg_baseline_corrected_cache_build_report.md/json

This script is cache-building only. No model training is performed.

Baseline correction policy:
- For each STIM_<id>, use the immediately preceding BSL_<id> event.
- Extract both 5s windows from the same subject EEG file.
- Downsample 512Hz -> 128Hz by stride 4, matching script 12.
- Subtract the per-channel mean of the BSL window from the STIM window.
- Apply the same final per-trial global z-score used by script 12.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CACHE_DIR = ROOT / ".cache"
TRIAL_INDEX = CACHE_DIR / "idare_trial_index.csv"
STIMULI_SPECS = Path("/mnt/HDD/AliWorks/I-DARE/metadata/Stimuli_Specifications.csv")

OUT_NPY = CACHE_DIR / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
OUT_INDEX = CACHE_DIR / "idare_eeg_cache_index_baseline_corrected.csv"
OUT_JSON = ROOT / "docs" / "idare_eeg_baseline_corrected_cache_build_report.json"
OUT_MD = ROOT / "docs" / "idare_eeg_baseline_corrected_cache_build_report.md"

SOURCE_FS = 512.0
TARGET_FS = 128.0
SOURCE_SAMPLES = 2560
TARGET_SAMPLES = 640
TARGET_CHANNELS = 32
DOWNSAMPLE = 4
POLICIES = ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]
TASKS = ["valence", "arousal"]


def safe(v: Any) -> Any:
    if isinstance(v, dict):
        return {str(k): safe(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [safe(x) for x in v]
    if isinstance(v, np.ndarray):
        return safe(v.tolist())
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return None if math.isnan(float(v)) else float(v)
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    return v


def human_size(n: int | float) -> str:
    n = float(n)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024 or unit == "TB":
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} TB"


def read_csv_normalized(path: Path) -> pd.DataFrame:
    read_attempts = [
        {"sep": ",", "engine": "python"},
        {"sep": ";", "engine": "python"},
        {"sep": None, "engine": "python"},
    ]

    last_error: Exception | None = None
    df: pd.DataFrame | None = None

    for kwargs in read_attempts:
        try:
            candidate = pd.read_csv(path, dtype=str, encoding="utf-8-sig", **kwargs)
            candidate.columns = [
                str(c).replace("\ufeff", "").replace("\xa0", " ").strip()
                for c in candidate.columns
            ]

            if "Stimulus" in candidate.columns:
                df = candidate
                break

            if candidate.shape[1] > 1 and df is None:
                df = candidate

        except Exception as exc:
            last_error = exc

    if df is None:
        raise RuntimeError(f"Could not read CSV file {path}. Last error: {last_error!r}")

    df.columns = [
        str(c).replace("\ufeff", "").replace("\xa0", " ").strip()
        for c in df.columns
    ]

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].map(
                lambda x: x.replace("\ufeff", "").replace("\xa0", " ").strip()
                if isinstance(x, str)
                else x
            )

    if "Stimulus" not in df.columns:
        raise KeyError(f"Column 'Stimulus' not found in {path}. Parsed columns: {list(df.columns)}")

    return df


def subject_key(h5: h5py.File, preferred: str) -> str:
    if preferred in h5:
        return preferred
    cands = sorted(k for k in h5.keys() if k.startswith("sbj_P_"))
    if not cands:
        raise KeyError(f"No sbj_P_* group found. Keys={list(h5.keys())}")
    return cands[0]


def label_from_score(score: Any, policy: str) -> int | None:
    if score is None or pd.isna(score):
        return None
    s = float(score)
    if policy == "discard_midpoint":
        return None if s == 5.0 else int(s > 5.0)
    if policy == "midpoint_as_low":
        return int(s > 5.0)
    if policy == "midpoint_as_high":
        return int(s >= 5.0)
    raise ValueError(policy)


def label_counts(df: pd.DataFrame, task: str, policy: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for score in df[f"{task}_score"].tolist():
        label = label_from_score(score, policy)
        key = "discard" if label is None else str(label)
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items()))


def extract_raw_window(data: h5py.Dataset, begin_raw: float) -> np.ndarray:
    start = int(begin_raw)
    stop = start + SOURCE_SAMPLES
    shape = tuple(int(x) for x in data.shape)
    if len(shape) != 2:
        raise ValueError(f"Expected 2D data, got {shape}")

    if shape[0] >= stop and shape[1] >= TARGET_CHANNELS:
        raw = np.asarray(data[start:stop, :TARGET_CHANNELS], dtype=np.float32)
    elif shape[1] >= stop and shape[0] >= TARGET_CHANNELS:
        raw = np.asarray(data[:TARGET_CHANNELS, start:stop], dtype=np.float32).T
    else:
        raise ValueError(
            f"Cannot extract {start}:{stop} first {TARGET_CHANNELS} channels from shape={shape}"
        )

    if raw.shape != (SOURCE_SAMPLES, TARGET_CHANNELS):
        raise ValueError(f"Unexpected raw window shape={raw.shape}")

    return raw.astype(np.float32, copy=False)


def preprocess_baseline_corrected(stim_raw: np.ndarray, bsl_raw: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    stim = stim_raw[::DOWNSAMPLE, :].T.astype(np.float32, copy=False)
    bsl = bsl_raw[::DOWNSAMPLE, :].T.astype(np.float32, copy=False)

    if stim.shape != (TARGET_CHANNELS, TARGET_SAMPLES):
        raise ValueError(f"Unexpected downsampled STIM shape={stim.shape}")
    if bsl.shape != (TARGET_CHANNELS, TARGET_SAMPLES):
        raise ValueError(f"Unexpected downsampled BSL shape={bsl.shape}")

    baseline_mean = bsl.mean(axis=1, keepdims=True).astype(np.float32)
    corrected = stim - baseline_mean

    mean = float(corrected.mean())
    std = float(corrected.std())
    if not np.isfinite(mean) or not np.isfinite(std):
        raise ValueError("Non-finite mean/std before normalization")

    x = corrected - mean
    if std >= 1e-8:
        x = x / std

    diag = {
        "baseline_mean_global": float(baseline_mean.mean()),
        "baseline_mean_abs_mean": float(np.abs(baseline_mean).mean()),
        "corrected_mean_before_zscore": mean,
        "corrected_std_before_zscore": std,
    }
    return x.astype(np.float32, copy=False), diag


def build_bsl_lookup(specs: pd.DataFrame) -> dict[str, dict[str, Any]]:
    specs = specs.copy()
    specs["_event_index_0based"] = list(range(len(specs)))
    specs["_stimulus"] = specs["Stimulus"].astype(str)

    out: dict[str, dict[str, Any]] = {}

    stim_rows = specs[specs["_stimulus"].str.startswith("STIM_", na=False)]
    for _, stim_row in stim_rows.iterrows():
        stim_name = str(stim_row["_stimulus"])
        stimulus_id = stim_name.replace("STIM_", "", 1)
        stim_idx = int(stim_row["_event_index_0based"])
        bsl_idx = stim_idx - 1

        if bsl_idx < 0:
            raise ValueError(f"STIM row has no preceding BSL row: {stim_name}")

        bsl_name = str(specs.iloc[bsl_idx]["_stimulus"])
        expected = "BSL_" + stimulus_id
        if bsl_name != expected:
            raise ValueError(
                f"Expected preceding baseline {expected} before {stim_name}, got {bsl_name}"
            )

        out[stimulus_id] = {
            "stim_event_index_0based": stim_idx,
            "stim_event_index_1based": stim_idx + 1,
            "bsl_event_index_0based": bsl_idx,
            "bsl_event_index_1based": bsl_idx + 1,
            "bsl_raw_event_name": bsl_name,
        }

    return out


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# I-DARE EEG Baseline-Corrected Cache Build Report",
        "",
        "This report was generated by `scripts/23_build_idare_eeg_baseline_corrected_cache.py`.",
        "",
        "No model training was performed.",
        "",
        "## Status",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Configuration",
        "",
        "```json",
        json.dumps(safe(report["config"]), indent=2, ensure_ascii=False),
        "```",
        "",
        "## Inputs",
        "",
    ]
    for k, v in report["inputs"].items():
        lines.append(f"- {k}: `{v}`")

    lines += ["", "## Outputs", ""]
    for k, v in report["outputs"].items():
        lines.append(f"- {k}: `{v}`")

    lines += ["", "## Counts", "", "| Item | Value |", "|---|---:|"]
    for k, v in report["counts"].items():
        lines.append(f"| {k} | {v} |")

    lines += [
        "",
        "## Cache",
        "",
        "```json",
        json.dumps(safe(report["cache"]), indent=2, ensure_ascii=False),
        "```",
        "",
        "## Baseline Correction Diagnostics",
        "",
        "```json",
        json.dumps(safe(report["baseline_correction_diagnostics"]), indent=2, ensure_ascii=False),
        "```",
        "",
        "## Label Counts",
        "",
        "```json",
        json.dumps(safe(report["label_counts"]), indent=2, ensure_ascii=False),
        "```",
        "",
        "## Runtime",
        "",
        f"- elapsed_sec: `{report['elapsed_sec']:.2f}`",
        "",
        "## Issues",
    ]
    lines += [f"- {x}" for x in report["issues"]] if report["issues"] else ["- None."]

    lines += ["", "## Warnings"]
    lines += [f"- {x}" for x in report["warnings"]] if report["warnings"] else ["- None."]

    lines += [
        "",
        "## Next Step",
        "",
        "Validate the generated cache before any training smoke.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def summarize_diagnostics(diags: list[dict[str, float]]) -> dict[str, dict[str, float | None]]:
    if not diags:
        return {}
    out: dict[str, dict[str, float | None]] = {}
    keys = sorted(diags[0].keys())
    for key in keys:
        vals = np.asarray([d[key] for d in diags], dtype=np.float64)
        out[key] = {
            "mean": float(vals.mean()),
            "median": float(np.median(vals)),
            "min": float(vals.min()),
            "max": float(vals.max()),
        }
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial-index", type=Path, default=TRIAL_INDEX)
    parser.add_argument("--stimuli-specs", type=Path, default=STIMULI_SPECS)
    parser.add_argument("--out-npy", type=Path, default=OUT_NPY)
    parser.add_argument("--out-index", type=Path, default=OUT_INDEX)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    t0 = time.perf_counter()
    issues: list[str] = []
    warnings: list[str] = []

    if not args.trial_index.exists():
        raise FileNotFoundError(f"Missing trial index: {args.trial_index}")
    if not args.stimuli_specs.exists():
        raise FileNotFoundError(f"Missing stimuli specs: {args.stimuli_specs}")

    if args.out_npy.exists() and not args.force:
        raise FileExistsError(f"Cache exists: {args.out_npy}. Use --force to rebuild.")
    if args.out_index.exists() and not args.force:
        raise FileExistsError(f"Cache index exists: {args.out_index}. Use --force to rebuild.")

    args.out_npy.parent.mkdir(parents=True, exist_ok=True)
    args.out_index.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)

    specs = read_csv_normalized(args.stimuli_specs)
    bsl_lookup = build_bsl_lookup(specs)

    df = pd.read_csv(args.trial_index)
    if args.limit is not None:
        df = df.head(args.limit).copy()
    df = df.reset_index(drop=True)

    required = [
        "subject_id",
        "subject_col",
        "stimulus_id",
        "raw_event_name",
        "event_index_0based",
        "eeg_file",
        "eeg_begin_raw",
        "valence_score",
        "arousal_score",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in trial index: {missing}")

    tmp_npy = args.out_npy.with_name(args.out_npy.stem + ".tmp.npy")
    tmp_index = args.out_index.with_name(args.out_index.stem + ".tmp.csv")
    for p in [tmp_npy, tmp_index]:
        if p.exists():
            p.unlink()

    n = int(len(df))
    arr = np.lib.format.open_memmap(
        tmp_npy,
        mode="w+",
        dtype=np.float32,
        shape=(n, TARGET_CHANNELS, TARGET_SAMPLES),
    )

    rows = []
    diags: list[dict[str, float]] = []
    extracted = 0
    grouped = list(df.groupby("eeg_file", sort=False))

    print("Building baseline-corrected I-DARE EEG cache")
    print(f"rows: {n}")
    print(f"subject files: {len(grouped)}")
    print(f"output: {args.out_npy}")

    for file_i, (eeg_file, g) in enumerate(grouped, 1):
        eeg_path = Path(str(eeg_file))
        subject = str(g.iloc[0]["subject_col"])
        print(f"[{file_i:03d}/{len(grouped):03d}] {subject}: {len(g)} trials", flush=True)

        try:
            with h5py.File(eeg_path, "r") as h5:
                key = subject_key(h5, subject)
                group = h5[key]
                data = group["data"]
                event_begin = np.asarray(group["event_begin"]).reshape(-1).astype(float)

                for row_i, row in g.iterrows():
                    try:
                        stimulus_id = str(row["stimulus_id"])
                        lookup = bsl_lookup.get(stimulus_id)
                        if lookup is None:
                            raise KeyError(f"No BSL lookup for stimulus_id={stimulus_id}")

                        stim_idx = int(row["event_index_0based"])
                        bsl_idx = int(lookup["bsl_event_index_0based"])

                        if int(lookup["stim_event_index_0based"]) != stim_idx:
                            raise ValueError(
                                "Trial index STIM event index does not match metadata lookup: "
                                f"trial={stim_idx}, lookup={lookup['stim_event_index_0based']}"
                            )

                        stim_begin = float(row["eeg_begin_raw"])
                        bsl_begin = float(event_begin[bsl_idx])

                        stim_raw = extract_raw_window(data, stim_begin)
                        bsl_raw = extract_raw_window(data, bsl_begin)
                        x, diag = preprocess_baseline_corrected(stim_raw, bsl_raw)

                        arr[int(row_i)] = x
                        extracted += 1
                        diags.append(diag)

                        outrow = {
                            "cache_row": int(row_i),
                            "subject_id": int(row["subject_id"]),
                            "subject_col": str(row["subject_col"]),
                            "stimulus_id": stimulus_id,
                            "raw_event_name": str(row["raw_event_name"]),
                            "bsl_raw_event_name": str(lookup["bsl_raw_event_name"]),
                            "eeg_file": str(eeg_path),
                            "eeg_begin_raw": stim_begin,
                            "bsl_eeg_begin_raw": bsl_begin,
                            "stim_event_index_0based": stim_idx,
                            "bsl_event_index_0based": bsl_idx,
                            "stim_event_index_1based": int(lookup["stim_event_index_1based"]),
                            "bsl_event_index_1based": int(lookup["bsl_event_index_1based"]),
                            "baseline_correction": "subtract_bsl_per_channel_mean_then_trial_global_zscore",
                            "valence_score": safe(row["valence_score"]),
                            "arousal_score": safe(row["arousal_score"]),
                            **{f"diag_{k}": v for k, v in diag.items()},
                        }
                        for task in TASKS:
                            for pol in POLICIES:
                                outrow[f"{task}_{pol}"] = label_from_score(row[f"{task}_score"], pol)
                        rows.append(outrow)
                    except Exception as exc:
                        issues.append(
                            f"row={row_i} subject={subject} stimulus={row.get('stimulus_id')}: {exc!r}"
                        )
        except Exception as exc:
            issues.append(f"file={eeg_path}: {exc!r}")

    arr.flush()
    del arr

    index_df = pd.DataFrame(rows).sort_values("cache_row")
    index_df.to_csv(tmp_index, index=False)

    status = "PASSED" if not issues and extracted == n else "FAILED"
    if status == "PASSED":
        if args.out_npy.exists():
            args.out_npy.unlink()
        if args.out_index.exists():
            args.out_index.unlink()
        tmp_npy.rename(args.out_npy)
        tmp_index.rename(args.out_index)
        cache_path = args.out_npy
        index_path = args.out_index
    else:
        warnings.append("Temporary cache files were kept for debugging.")
        cache_path = tmp_npy
        index_path = tmp_index

    size = cache_path.stat().st_size if cache_path.exists() else 0
    report = {
        "status": status,
        "config": {
            "source_fs": SOURCE_FS,
            "target_fs": TARGET_FS,
            "source_samples": SOURCE_SAMPLES,
            "target_samples": TARGET_SAMPLES,
            "target_channels": TARGET_CHANNELS,
            "downsample": DOWNSAMPLE,
            "baseline_correction": "subtract BSL per-channel mean before final z-score",
            "normalization": "per-trial global z-score after baseline correction",
            "limit": args.limit,
        },
        "inputs": {
            "trial_index": str(args.trial_index),
            "stimuli_specs": str(args.stimuli_specs),
        },
        "outputs": {
            "eeg_cache_npy": str(cache_path),
            "cache_index_csv": str(index_path),
            "build_report_md": str(args.out_md),
            "build_report_json": str(args.out_json),
        },
        "counts": {
            "trial_index_rows": n,
            "extracted_rows": extracted,
            "cache_index_rows": int(len(index_df)),
            "subject_files": len(grouped),
            "bsl_lookup_stimuli": int(len(bsl_lookup)),
        },
        "cache": {
            "shape": [n, TARGET_CHANNELS, TARGET_SAMPLES],
            "dtype": "float32",
            "file_size": size,
            "file_size_human": human_size(size),
        },
        "baseline_correction_diagnostics": summarize_diagnostics(diags),
        "label_counts": {task: {pol: label_counts(df, task, pol) for pol in POLICIES} for task in TASKS},
        "elapsed_sec": time.perf_counter() - t0,
        "issues": issues,
        "warnings": warnings,
    }

    args.out_json.write_text(json.dumps(safe(report), indent=2, ensure_ascii=False), encoding="utf-8")
    args.out_md.write_text(render_md(report), encoding="utf-8")

    print(f"Wrote: {args.out_md}")
    print(f"Wrote: {args.out_json}")
    print(f"Status: {status}")
    print(f"Rows extracted: {extracted} / {n}")
    print(f"Cache size: {human_size(size)}")
    print(f"Elapsed: {report['elapsed_sec']:.2f}s")
    print(f"Issues: {len(issues)}")
    print(f"Warnings: {len(warnings)}")
    if status != "PASSED":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
