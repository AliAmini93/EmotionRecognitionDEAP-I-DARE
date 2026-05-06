#!/usr/bin/env python3
"""Build compact I-DARE EEG BSL summary-stat sidecar.

Purpose
-------
This is the low-volume Candidate C path agreed for I-DARE:

    response = STIM - mean(BSL)
    model(response, bsl_stats)

This script does NOT store the full triplet [BSL, STIM, STIM-BSL].
It only stores compact baseline summary features for the preceding BSL event,
aligned 1:1 with rows in `.cache/idare_trial_index.csv`.

Expected I-DARE EEG raw file convention
---------------------------------------
- HDF5/MAT file: raw_downloads/EEG/sbj_P_XX.mat
- subject group key: sbj_P_XX
- data shape: [samples, channels]
- sampling rate: 512 Hz
- STIM event in trial index has a preceding BSL event at event_index_0based - 1

Output
------
- BSL stats NPY: [n_trials, feature_dim]
- CSV sidecar index aligned with the NPY rows
- Markdown/JSON build report
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
DEFAULT_OUT_NPY = ROOT / ".cache" / "idare_eeg_bsl_stats_smoke.npy"
DEFAULT_OUT_INDEX = ROOT / ".cache" / "idare_eeg_bsl_stats_index_smoke.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "idare_eeg_bsl_stats_sidecar_build_smoke.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "idare_eeg_bsl_stats_sidecar_build_smoke.json"

SOURCE_FS = 512.0
WINDOW_SEC = 5.0
WINDOW_SAMPLES = int(SOURCE_FS * WINDOW_SEC)
EEG_CHANNELS = 32

PER_CHANNEL_FEATURES = [
    "mean",
    "std",
    "rms",
    "mav",
    "min",
    "max",
    "log_variance",
]

GLOBAL_FEATURES = [
    "global_mean",
    "global_std",
    "global_rms",
    "global_mav",
    "global_log_variance",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial-index", type=Path, default=DEFAULT_TRIAL_INDEX)
    parser.add_argument("--limit-subjects", type=int, default=None)
    parser.add_argument("--limit-rows", type=int, default=None)
    parser.add_argument("--out-npy", type=Path, default=DEFAULT_OUT_NPY)
    parser.add_argument("--out-index", type=Path, default=DEFAULT_OUT_INDEX)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    return parser.parse_args()


def safe_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [safe_json(v) for v in obj]
    if isinstance(obj, tuple):
        return [safe_json(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        value = float(obj)
        return None if math.isnan(value) else value
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def human_size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024 or unit == "GB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} GB"


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


def feature_columns() -> list[str]:
    cols: list[str] = []
    for ch in range(EEG_CHANNELS):
        ch_name = f"eeg_ch{ch + 1:02d}"
        for feat in PER_CHANNEL_FEATURES:
            cols.append(f"{ch_name}_{feat}")
    cols.extend(GLOBAL_FEATURES)
    return cols


def select_rows(df: pd.DataFrame, limit_subjects: int | None, limit_rows: int | None) -> pd.DataFrame:
    rows = df.copy()
    if limit_subjects is not None:
        subjects = sorted(rows["subject_id"].dropna().astype(int).unique().tolist())[:limit_subjects]
        rows = rows[rows["subject_id"].isin(subjects)].copy()
    if limit_rows is not None:
        rows = rows.head(limit_rows).copy()
    return rows.reset_index(drop=True)


def subject_key(path: Path) -> str:
    return path.stem


def event_begin_at(path: Path, event_index_0based: int) -> float:
    key = subject_key(path)
    with h5py.File(path, "r") as h5:
        begins = h5[key]["event_begin"]
        if event_index_0based < 0 or event_index_0based >= begins.shape[0]:
            raise ValueError(f"event_index_0based={event_index_0based} out of range for {path}")
        return float(np.asarray(begins[event_index_0based]).squeeze())


def read_h5_eeg_window(path: Path, begin_raw: float, n_samples: int = WINDOW_SAMPLES) -> np.ndarray:
    key = subject_key(path)
    start = int(round(float(begin_raw)))
    end = start + n_samples
    if start < 0:
        raise ValueError(f"negative start={start} for {path}")

    with h5py.File(path, "r") as h5:
        data = h5[key]["data"]
        if end > data.shape[0]:
            raise ValueError(f"window end {end} exceeds data len {data.shape[0]} for {path}")
        raw = np.asarray(data[start:end, :EEG_CHANNELS], dtype=np.float32).T

    if raw.shape != (EEG_CHANNELS, n_samples):
        raise ValueError(f"unexpected EEG window shape {raw.shape} for {path}")

    return raw


def compute_bsl_stats(bsl: np.ndarray) -> tuple[np.ndarray, dict[str, float]]:
    if bsl.shape != (EEG_CHANNELS, WINDOW_SAMPLES):
        raise ValueError(f"bad BSL shape: {bsl.shape}")

    bsl = bsl.astype(np.float32, copy=False)
    eps = 1e-12

    means = bsl.mean(axis=1)
    stds = bsl.std(axis=1)
    rms = np.sqrt(np.mean(np.square(bsl), axis=1))
    mav = np.mean(np.abs(bsl), axis=1)
    mins = bsl.min(axis=1)
    maxs = bsl.max(axis=1)
    log_var = np.log(np.var(bsl, axis=1) + eps)

    parts = [means, stds, rms, mav, mins, maxs, log_var]

    global_stats = np.asarray(
        [
            float(bsl.mean()),
            float(bsl.std()),
            float(np.sqrt(np.mean(np.square(bsl)))),
            float(np.mean(np.abs(bsl))),
            float(np.log(np.var(bsl) + eps)),
        ],
        dtype=np.float32,
    )

    # Interleave by channel: ch1_mean, ch1_std, ..., ch2_mean, ...
    per_channel = np.stack(parts, axis=1).reshape(-1).astype(np.float32, copy=False)
    features = np.concatenate([per_channel, global_stats]).astype(np.float32, copy=False)

    diag = {
        "bsl_mean_global": float(bsl.mean()),
        "bsl_mean_abs_mean": float(np.abs(bsl).mean()),
        "bsl_std_global": float(bsl.std()),
        "bsl_rms_global": float(np.sqrt(np.mean(np.square(bsl)))),
        "feature_mean": float(features.mean()),
        "feature_std": float(features.std()),
    }

    return features, diag


def build_report_md(report: dict[str, Any]) -> str:
    cfg = report["config"]
    lines: list[str] = []
    lines.append("# I-DARE EEG BSL Stats Sidecar Build Report\n")
    lines.append("This report was generated by `scripts/33_build_idare_eeg_bsl_stats_sidecar.py`.\n")
    lines.append("No model training was performed.\n")
    lines.append("This sidecar stores compact BSL summary statistics only. It does not store full BSL/STIM/STIM-BSL triplets.\n")

    lines.append("## Status\n")
    lines.append(f"Status: **{report['status']}**\n")

    lines.append("## Configuration\n")
    lines.append("```json")
    lines.append(json.dumps(cfg, indent=2, ensure_ascii=False))
    lines.append("```\n")

    lines.append("## Inputs\n")
    lines.append(f"- trial_index: `{cfg['trial_index']}`\n")

    lines.append("## Outputs\n")
    lines.append(f"- bsl_stats_npy: `{report['outputs']['bsl_stats_npy']}`")
    lines.append(f"- bsl_stats_index_csv: `{report['outputs']['bsl_stats_index_csv']}`")
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

    lines.append("## Feature Policy\n")
    lines.append("- Per-channel EEG BSL summary features: mean, std, rms, mav, min, max, log_variance.")
    lines.append("- Global BSL summary features: global_mean, global_std, global_rms, global_mav, global_log_variance.")
    lines.append("- Intended use: concatenate these BSL stats with the existing baseline-corrected EEG response cache inside a controlled ablation.\n")

    lines.append("## Diagnostics\n")
    lines.append("```json")
    lines.append(json.dumps(report["diagnostics"], indent=2, ensure_ascii=False))
    lines.append("```\n")

    lines.append("## Feature Stats Preview\n")
    lines.append("| Feature | Mean | Std | Min | Max |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in report["feature_stats_preview"]:
        lines.append(
            f"| {row['feature']} | {row['mean']:.6f} | {row['std']:.6f} | {row['min']:.6f} | {row['max']:.6f} |"
        )
    lines.append("")

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
    lines.append("If this sidecar passes smoke/full build validation, run a small EEG ablation using `STIM-BSL EEG response cache + BSL stats sidecar`.\n")

    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    start_time = time.perf_counter()
    issues: list[str] = []
    warnings: list[str] = []

    trial_index = pd.read_csv(args.trial_index)
    rows = select_rows(trial_index, args.limit_subjects, args.limit_rows)
    cols = feature_columns()
    feature_dim = len(cols)

    args.out_npy.parent.mkdir(parents=True, exist_ok=True)
    args.out_index.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)

    print("Building I-DARE EEG BSL stats sidecar")
    print(f"trial_index: {args.trial_index}")
    print(f"rows selected: {len(rows)}")
    print(f"feature_dim: {feature_dim}")
    print(f"output: {args.out_npy}")

    cache = open_memmap(args.out_npy, mode="w+", dtype=np.float32, shape=(len(rows), feature_dim))

    out_rows: list[dict[str, Any]] = []
    diag_values: dict[str, list[float]] = {
        "bsl_mean_global": [],
        "bsl_mean_abs_mean": [],
        "bsl_std_global": [],
        "bsl_rms_global": [],
        "feature_mean": [],
        "feature_std": [],
    }

    for cache_row, row in rows.iterrows():
        if cache_row > 0 and cache_row % 250 == 0:
            print(f"extracted {cache_row}/{len(rows)}")

        eeg_file = Path(str(row["eeg_file"]))
        stim_event_index = int(row["event_index_0based"])
        bsl_event_index = stim_event_index - 1

        try:
            if bsl_event_index < 0:
                raise ValueError(f"no preceding BSL event for stim_event_index={stim_event_index}")

            bsl_begin = event_begin_at(eeg_file, bsl_event_index)
            bsl = read_h5_eeg_window(eeg_file, bsl_begin)
            features, diag = compute_bsl_stats(bsl)

            if features.shape != (feature_dim,):
                raise ValueError(f"feature vector shape {features.shape} != {(feature_dim,)}")

        except Exception as exc:
            issues.append(f"row {cache_row}: {type(exc).__name__}: {exc}")
            bsl_begin = float("nan")
            features = np.zeros((feature_dim,), dtype=np.float32)
            diag = {key: float("nan") for key in diag_values}

        cache[cache_row] = features
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
            "eeg_file": str(eeg_file),
            "eeg_channels": EEG_CHANNELS,
            "eeg_fs": SOURCE_FS,
            "bsl_eeg_begin_raw": float(bsl_begin),
            "fixed_window_samples": WINDOW_SAMPLES,
            "feature_dim": feature_dim,
            "sidecar_policy": "preceding_bsl_eeg_summary_stats_only",
            "intended_pairing": "concat_with_baseline_corrected_eeg_response_cache",
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
    out_index.to_csv(args.out_index, index=False, lineterminator="\n")

    arr = np.load(args.out_npy, mmap_mode="r")
    nan_count = int(np.isnan(arr[:]).sum())
    inf_count = int(np.isinf(arr[:]).sum())
    if nan_count or inf_count:
        issues.append("BSL stats cache contains non-finite values")

    feature_stats: list[dict[str, Any]] = []
    arr_full = arr[:]
    for i, col in enumerate(cols):
        values = arr_full[:, i]
        feature_stats.append({
            "feature": col,
            "mean": float(values.mean()),
            "std": float(values.std()),
            "min": float(values.min()),
            "max": float(values.max()),
        })

    preview_names = [
        "eeg_ch01_mean",
        "eeg_ch01_std",
        "eeg_ch01_rms",
        "eeg_ch01_mav",
        "eeg_ch01_log_variance",
        "eeg_ch32_mean",
        "eeg_ch32_std",
        "eeg_ch32_log_variance",
        "global_mean",
        "global_std",
        "global_rms",
        "global_mav",
        "global_log_variance",
    ]
    preview_set = set(preview_names)
    feature_stats_preview = [row for row in feature_stats if row["feature"] in preview_set]

    cache_info = {
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
        "file_size": args.out_npy.stat().st_size,
        "file_size_human": human_size(args.out_npy.stat().st_size),
        "nan_count": nan_count,
        "inf_count": inf_count,
    }

    report = {
        "status": "PASSED" if not issues else "FAILED",
        "generated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "config": {
            "source": "I-DARE raw_downloads/EEG HDF5 .mat",
            "trial_index": str(args.trial_index),
            "source_fs": SOURCE_FS,
            "window_sec": WINDOW_SEC,
            "window_samples": WINDOW_SAMPLES,
            "eeg_channels": EEG_CHANNELS,
            "sidecar_policy": "store compact preceding-BSL EEG summary stats only",
            "does_not_store": ["full_BSL", "full_STIM", "full_STIM_minus_BSL_triplet"],
            "intended_mainline_response_cache": "existing baseline-corrected STIM-BSL EEG cache",
            "per_channel_features": PER_CHANNEL_FEATURES,
            "global_features": GLOBAL_FEATURES,
            "feature_dim": feature_dim,
            "limit_subjects": args.limit_subjects,
            "limit_rows": args.limit_rows,
        },
        "outputs": {
            "bsl_stats_npy": str(args.out_npy),
            "bsl_stats_index_csv": str(args.out_index),
            "build_report_md": str(args.out_md),
            "build_report_json": str(args.out_json),
        },
        "counts": {
            "selected_rows": int(len(rows)),
            "extracted_rows": int(len(out_index)),
            "cache_index_rows": int(len(out_index)),
            "subject_files": int(rows["subject_id"].nunique()),
            "feature_dim": int(feature_dim),
        },
        "cache": cache_info,
        "diagnostics": {key: finite_summary(values) for key, values in diag_values.items()},
        "feature_columns": cols,
        "feature_stats_preview": feature_stats_preview,
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
    print(f"Feature dim: {feature_dim}")
    print(f"Cache size: {cache_info['file_size_human']}")
    print(f"Elapsed: {report['elapsed_sec']:.2f}s")
    print(f"Issues: {len(issues)}")
    print(f"Warnings: {len(warnings)}")

    return 0 if report["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
