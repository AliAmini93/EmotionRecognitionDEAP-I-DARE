#!/usr/bin/env python3
"""Build a raw I-DARE EMG waveform cache.

Raw counterpart to scripts/29_build_idare_emg_feature_cache.py.

Input:
- .cache/idare_trial_index.csv

Output:
- NPY raw EMG windows: [n_trials, 2, 10000]
- CSV cache index aligned 1:1 with rows

Policy:
- Use each 5s STIM event from the trial index.
- Extract exactly 10000 samples at 2000 Hz.
- Subtract the preceding BSL event per-channel mean.
- Apply per-window global z-score after baseline correction.
- Do not train a model here.
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
from numpy.lib.format import open_memmap

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRIAL_INDEX = ROOT / ".cache" / "idare_trial_index.csv"
DEFAULT_OUT_NPY = ROOT / ".cache" / "idare_raw_emg_windows_2x10000_float32_smoke.npy"
DEFAULT_OUT_INDEX = ROOT / ".cache" / "idare_raw_emg_cache_index_smoke.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "idare_raw_emg_cache_build_smoke.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "idare_raw_emg_cache_build_smoke.json"

SOURCE_FS = 2000.0
WINDOW_SAMPLES = 10000
EMG_CHANNELS = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial-index", type=Path, default=DEFAULT_TRIAL_INDEX)
    parser.add_argument("--limit-subjects", type=int, default=None)
    parser.add_argument("--limit-rows", type=int, default=None)
    parser.add_argument("--out-npy", type=Path, default=DEFAULT_OUT_NPY)
    parser.add_argument("--out-index", type=Path, default=DEFAULT_OUT_INDEX)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--no-baseline-correction", action="store_true")
    parser.add_argument("--no-window-zscore", action="store_true")
    return parser.parse_args()


def safe_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [safe_json(v) for v in obj]
    if isinstance(obj, tuple):
        return [safe_json(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        value = float(obj)
        return None if math.isnan(value) else value
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def finite_summary(values: list[float]) -> dict[str, float | None]:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"mean": None, "median": None, "min": None, "max": None}
    return {
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def human_size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024 or unit == "GB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} GB"


def label_value(score: Any, policy: str) -> float:
    if pd.isna(score):
        return float("nan")
    x = float(score)
    if policy == "midpoint_as_high":
        return 1.0 if x >= 5.0 else 0.0
    if policy == "midpoint_as_low":
        return 1.0 if x > 5.0 else 0.0
    if policy == "discard_midpoint":
        if x == 5.0:
            return float("nan")
        return 1.0 if x > 5.0 else 0.0
    raise ValueError(policy)


def label_counts(df: pd.DataFrame) -> dict[str, dict[str, dict[str, int]]]:
    out: dict[str, dict[str, dict[str, int]]] = {}
    for task in ["valence", "arousal"]:
        score_col = f"{task}_score"
        out[task] = {}
        for policy in ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]:
            vals = df[score_col].map(lambda x: label_value(x, policy))
            out[task][policy] = {"0": int((vals == 0).sum()), "1": int((vals == 1).sum())}
            if policy == "discard_midpoint":
                out[task][policy]["discard"] = int(vals.isna().sum())
    return out


def subject_key(path: Path) -> str:
    return path.stem


def event_begin_at(path: Path, event_index_0based: int) -> float:
    key = subject_key(path)
    with h5py.File(path, "r") as h5:
        begins = h5[key]["event_begin"]
        return float(np.asarray(begins[event_index_0based]).squeeze())


def read_h5_window(path: Path, begin_raw: float, n_samples: int = WINDOW_SAMPLES) -> np.ndarray:
    key = subject_key(path)
    start = int(round(float(begin_raw)))
    end = start + n_samples
    if start < 0:
        raise ValueError(f"negative start={start} for {path}")
    with h5py.File(path, "r") as h5:
        data = h5[key]["data"]
        if end > data.shape[0]:
            raise ValueError(f"window end {end} exceeds data len {data.shape[0]} for {path}")
        raw = np.asarray(data[start:end, :EMG_CHANNELS], dtype=np.float32).T
    if raw.shape != (EMG_CHANNELS, n_samples):
        raise ValueError(f"unexpected raw shape {raw.shape} for {path}")
    return raw


def preprocess_raw_emg(
    stim: np.ndarray,
    bsl: np.ndarray,
    *,
    baseline_correction: bool,
    window_zscore: bool,
) -> tuple[np.ndarray, dict[str, float]]:
    stim = stim.astype(np.float32, copy=False)
    bsl = bsl.astype(np.float32, copy=False)
    bsl_mean = bsl.mean(axis=1, keepdims=True)
    corrected = stim - bsl_mean if baseline_correction else stim.copy()

    corrected_mean = float(corrected.mean())
    corrected_std = float(corrected.std())

    if window_zscore:
        mean = float(corrected.mean())
        std = float(corrected.std())
        out = (corrected - mean) / std if std > 1e-8 else corrected - mean
    else:
        out = corrected

    out = out.astype(np.float32, copy=False)
    diag = {
        "baseline_mean_global": float(bsl_mean.mean()),
        "baseline_mean_abs_mean": float(np.abs(bsl_mean).mean()),
        "corrected_mean_before_zscore": corrected_mean,
        "corrected_std_before_zscore": corrected_std,
        "window_mean_after_preprocess": float(out.mean()),
        "window_std_after_preprocess": float(out.std()),
    }
    return out, diag


def select_rows(df: pd.DataFrame, limit_subjects: int | None, limit_rows: int | None) -> pd.DataFrame:
    rows = df.copy()
    if limit_subjects is not None:
        subjects = sorted(rows["subject_id"].dropna().astype(int).unique().tolist())[:limit_subjects]
        rows = rows[rows["subject_id"].isin(subjects)].copy()
    if limit_rows is not None:
        rows = rows.head(limit_rows).copy()
    return rows.reset_index(drop=True)


def build_report_md(report: dict[str, Any]) -> str:
    cfg = report["config"]
    lines: list[str] = []
    lines.append("# I-DARE Raw EMG Cache Build Smoke Report\n")
    lines.append("This report was generated by `scripts/31_build_idare_raw_emg_cache.py`.\n")
    lines.append("No model training was performed.\n")
    lines.append("## Status\n")
    lines.append(f"Status: **{report['status']}**\n")
    lines.append("## Configuration\n")
    lines.append("```json")
    lines.append(json.dumps(cfg, indent=2, ensure_ascii=False))
    lines.append("```\n")
    lines.append("## Inputs\n")
    lines.append(f"- trial_index: `{cfg['trial_index']}`\n")
    lines.append("## Outputs\n")
    lines.append(f"- raw_emg_cache_npy: `{report['outputs']['raw_emg_cache_npy']}`")
    lines.append(f"- cache_index_csv: `{report['outputs']['cache_index_csv']}`")
    lines.append(f"- build_report_md: `{report['outputs']['build_report_md']}`")
    lines.append(f"- build_report_json: `{report['outputs']['build_report_json']}`\n")
    lines.append("## Counts\n")
    lines.append("| Item | Value |")
    lines.append("|---|---:|")
    for key, value in report["counts"].items():
        lines.append(f"| {key} | {value} |")
    lines.append("")
    lines.append("## Cache\n")
    lines.append("```json")
    lines.append(json.dumps(report["cache"], indent=2, ensure_ascii=False))
    lines.append("```\n")
    lines.append("## Diagnostics\n")
    lines.append("```json")
    lines.append(json.dumps(report["diagnostics"], indent=2, ensure_ascii=False))
    lines.append("```\n")
    lines.append("## Label Counts\n")
    lines.append("```json")
    lines.append(json.dumps(report["label_counts"], indent=2, ensure_ascii=False))
    lines.append("```\n")
    lines.append("## Runtime\n")
    lines.append(f"- elapsed_sec: `{report['elapsed_sec']:.2f}`\n")
    lines.append("## Issues")
    lines.extend([f"- {x}" for x in report["issues"]] if report["issues"] else ["- None."])
    lines.append("")
    lines.append("## Warnings")
    lines.extend([f"- {x}" for x in report["warnings"]] if report["warnings"] else ["- None."])
    lines.append("")
    lines.append("## Next Step\n")
    lines.append("Validate this smoke output before training a raw EMG-only model.\n")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    start_time = time.perf_counter()
    issues: list[str] = []
    warnings: list[str] = []

    trial_index = pd.read_csv(args.trial_index)
    rows = select_rows(trial_index, args.limit_subjects, args.limit_rows)

    args.out_npy.parent.mkdir(parents=True, exist_ok=True)
    args.out_index.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)

    print("Building I-DARE raw EMG cache")
    print(f"trial_index: {args.trial_index}")
    print(f"rows selected: {len(rows)}")
    print(f"output: {args.out_npy}")

    cache = open_memmap(args.out_npy, mode="w+", dtype=np.float32, shape=(len(rows), EMG_CHANNELS, WINDOW_SAMPLES))

    out_rows: list[dict[str, Any]] = []
    diag_values: dict[str, list[float]] = {
        "baseline_mean_global": [],
        "baseline_mean_abs_mean": [],
        "corrected_mean_before_zscore": [],
        "corrected_std_before_zscore": [],
        "window_mean_after_preprocess": [],
        "window_std_after_preprocess": [],
    }

    for cache_row, row in rows.iterrows():
        if cache_row > 0 and cache_row % 250 == 0:
            print(f"extracted {cache_row}/{len(rows)}")

        emg_file = Path(str(row["emg_file"]))
        stim_begin = float(row["emg_begin_raw"])
        stim_event_index = int(row["event_index_0based"])
        bsl_event_index = stim_event_index - 1

        try:
            if bsl_event_index < 0:
                raise ValueError(f"no preceding BSL event for stim_event_index={stim_event_index}")
            bsl_begin = event_begin_at(emg_file, bsl_event_index)
            stim = read_h5_window(emg_file, stim_begin)
            bsl = read_h5_window(emg_file, bsl_begin)
            x, diag = preprocess_raw_emg(
                stim,
                bsl,
                baseline_correction=not args.no_baseline_correction,
                window_zscore=not args.no_window_zscore,
            )
        except Exception as exc:
            issues.append(f"row {cache_row}: {type(exc).__name__}: {exc}")
            bsl_begin = float("nan")
            x = np.zeros((EMG_CHANNELS, WINDOW_SAMPLES), dtype=np.float32)
            diag = {key: float("nan") for key in diag_values}

        cache[cache_row] = x
        for key, value in diag.items():
            diag_values[key].append(float(value))

        out_row = {
            "cache_row": int(cache_row),
            "subject_id": int(row["subject_id"]),
            "subject_col": row.get("subject_col"),
            "stimulus_id": row.get("stimulus_id"),
            "raw_event_name": row.get("raw_event_name"),
            "bsl_event_index_0based": int(bsl_event_index),
            "stim_event_index_0based": int(stim_event_index),
            "bsl_event_index_1based": int(bsl_event_index + 1),
            "stim_event_index_1based": int(row["event_index_1based"]),
            "emg_file": str(emg_file),
            "emg_channels": "emg_ch1,emg_ch2",
            "emg_begin_raw": float(row["emg_begin_raw"]),
            "emg_end_raw": float(row["emg_end_raw"]),
            "bsl_emg_begin_raw": float(bsl_begin),
            "fixed_window_samples": WINDOW_SAMPLES,
            "stim_event_duration_samples": float(row["emg_duration_samples"]),
            "baseline_correction": (
                "subtract_preceding_bsl_per_channel_mean_then_window_global_zscore"
                if not args.no_baseline_correction and not args.no_window_zscore
                else "custom"
            ),
            "valence_score": row.get("valence_score"),
            "arousal_score": row.get("arousal_score"),
        }
        for key, value in diag.items():
            out_row[f"diag_{key}"] = value
        for task in ["valence", "arousal"]:
            score = row.get(f"{task}_score")
            for policy in ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]:
                out_row[f"{task}_{policy}"] = label_value(score, policy)
        out_rows.append(out_row)

    del cache

    out_index = pd.DataFrame(out_rows)
    out_index.to_csv(args.out_index, index=False)

    arr = np.load(args.out_npy, mmap_mode="r")
    cache_info = {
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
        "file_size": args.out_npy.stat().st_size,
        "file_size_human": human_size(args.out_npy.stat().st_size),
        "nan_count": int(np.isnan(arr[:]).sum()),
        "inf_count": int(np.isinf(arr[:]).sum()),
    }
    if cache_info["nan_count"] or cache_info["inf_count"]:
        issues.append("cache contains non-finite values")

    report = {
        "status": "PASSED" if not issues else "FAILED",
        "generated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "config": {
            "source": "I-DARE raw_downloads/EMG HDF5 .mat",
            "trial_index": str(args.trial_index),
            "source_fs": SOURCE_FS,
            "window_sec": WINDOW_SAMPLES / SOURCE_FS,
            "window_samples": WINDOW_SAMPLES,
            "emg_channels": [
                {"name": "emg_ch1", "index_0based": 0, "channel_1based": 1},
                {"name": "emg_ch2", "index_0based": 1, "channel_1based": 2},
            ],
            "shape_policy": "[n_trials, 2, 10000]",
            "baseline_source": "preceding BSL event inferred from event_index_0based - 1",
            "baseline_correction": "disabled" if args.no_baseline_correction else "subtract preceding BSL per-channel mean",
            "normalization": "disabled" if args.no_window_zscore else "per-window global z-score after baseline correction",
            "limit_subjects": args.limit_subjects,
            "limit_rows": args.limit_rows,
        },
        "outputs": {
            "raw_emg_cache_npy": str(args.out_npy),
            "cache_index_csv": str(args.out_index),
            "build_report_md": str(args.out_md),
            "build_report_json": str(args.out_json),
        },
        "counts": {
            "selected_rows": int(len(rows)),
            "extracted_rows": int(len(out_index)),
            "cache_index_rows": int(len(out_index)),
            "subject_files": int(rows["subject_id"].nunique()),
            "emg_channels": EMG_CHANNELS,
            "window_samples": WINDOW_SAMPLES,
        },
        "cache": cache_info,
        "diagnostics": {key: finite_summary(values) for key, values in diag_values.items()},
        "label_counts": label_counts(out_index),
        "issues": issues,
        "warnings": warnings,
        "elapsed_sec": float(time.perf_counter() - start_time),
    }

    args.out_json.write_text(json.dumps(safe_json(report), indent=2, ensure_ascii=False), encoding="utf-8")
    args.out_md.write_text(build_report_md(safe_json(report)), encoding="utf-8")

    print(f"Wrote: {args.out_md}")
    print(f"Wrote: {args.out_json}")
    print(f"Status: {report['status']}")
    print(f"Rows extracted: {report['counts']['extracted_rows']} / {report['counts']['selected_rows']}")
    print(f"Cache size: {cache_info['file_size_human']}")
    print(f"Elapsed: {report['elapsed_sec']:.2f}s")
    print(f"Issues: {len(issues)}")
    print(f"Warnings: {len(warnings)}")
    return 0 if report["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
