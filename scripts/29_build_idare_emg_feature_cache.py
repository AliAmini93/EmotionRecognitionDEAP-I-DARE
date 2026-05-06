#!/usr/bin/env python3
"""Build an I-DARE EMG feature cache from raw/preprocessed EMG .mat files.

This script is smoke-first. It does not train a model.

Inputs:
- .cache/idare_trial_index.csv
- I-DARE EMG HDF5 .mat files referenced by emg_file

Signal convention:
- EMG source: 2000 Hz
- 2 EMG channels
- each stimulus event is treated as a 5s window: 10000 samples
- the preceding event is treated as the BSL event for baseline correction

Preprocessing:
- extract fixed 10000-sample STIM window from emg_begin_raw
- extract fixed 10000-sample BSL window from preceding event_begin
- subtract per-channel BSL mean from the STIM window
- compute time-domain EMG features per channel
- no raw waveform z-score before feature extraction
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
CACHE_DIR = ROOT / ".cache"

DEFAULT_TRIAL_INDEX = CACHE_DIR / "idare_trial_index.csv"
DEFAULT_OUT_NPY = CACHE_DIR / "idare_emg_features_smoke.npy"
DEFAULT_OUT_INDEX = CACHE_DIR / "idare_emg_feature_cache_index_smoke.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "idare_emg_feature_cache_build_smoke.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "idare_emg_feature_cache_build_smoke.json"

SOURCE_FS = 2000.0
WINDOW_SEC = 5.0
WINDOW_SAMPLES = 10000
EMG_CHANNELS = [
    {"name": "emg_ch1", "index_0based": 0, "channel_1based": 1},
    {"name": "emg_ch2", "index_0based": 1, "channel_1based": 2},
]
FEATURE_NAMES = [
    "mean",
    "std",
    "rms",
    "mav",
    "iemg",
    "waveform_length",
    "zero_crossings",
    "slope_sign_changes",
    "min",
    "max",
    "log_variance",
]
FEATURE_COLUMNS = [
    f"{ch['name']}_{feat}"
    for ch in EMG_CHANNELS
    for feat in FEATURE_NAMES
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial-index", type=Path, default=DEFAULT_TRIAL_INDEX)
    parser.add_argument("--out-npy", type=Path, default=DEFAULT_OUT_NPY)
    parser.add_argument("--out-index", type=Path, default=DEFAULT_OUT_INDEX)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--limit-subjects", type=int, default=None)
    parser.add_argument("--limit-rows", type=int, default=None)
    parser.add_argument("--window-samples", type=int, default=WINDOW_SAMPLES)
    parser.add_argument(
        "--no-baseline-correction",
        action="store_true",
        help="Do not subtract preceding BSL per-channel mean. Not recommended for main path.",
    )
    return parser.parse_args()


def safe_float(x: Any) -> float | None:
    try:
        value = float(x)
    except Exception:
        return None
    if not math.isfinite(value):
        return None
    return value


def finite_summary(values: list[float]) -> dict[str, float | None]:
    arr = np.asarray([v for v in values if math.isfinite(float(v))], dtype=np.float64)
    if arr.size == 0:
        return {"mean": None, "median": None, "min": None, "max": None}
    return {
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def file_size_human(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024.0 or unit == "GB":
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} GB"


def label_value(score: Any, policy: str) -> float | None:
    value = safe_float(score)
    if value is None:
        return None
    if policy == "discard_midpoint":
        if value == 5:
            return None
        return float(value > 5)
    if policy == "midpoint_as_low":
        return float(value > 5)
    if policy == "midpoint_as_high":
        return float(value >= 5)
    raise ValueError(f"Unknown label policy: {policy}")


def label_counts(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for task in ["valence", "arousal"]:
        score_col = f"{task}_score"
        out[task] = {}
        for policy in ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]:
            labels = [label_value(v, policy) for v in df[score_col].tolist()]
            zeros = sum(v == 0.0 for v in labels)
            ones = sum(v == 1.0 for v in labels)
            discards = sum(v is None for v in labels)
            if policy == "discard_midpoint":
                out[task][policy] = {"0": int(zeros), "1": int(ones), "discard": int(discards)}
            else:
                out[task][policy] = {"0": int(zeros), "1": int(ones)}
    return out


def read_event_arrays(h5: h5py.File, subject_col: str) -> tuple[np.ndarray, np.ndarray]:
    group = h5[subject_col]
    begins = np.asarray(group["event_begin"]).reshape(-1).astype(np.float64)
    ends = np.asarray(group["event_end"]).reshape(-1).astype(np.float64)
    return begins, ends


def extract_fixed_window(data: h5py.Dataset, begin_raw: float, n_samples: int) -> np.ndarray:
    start = int(round(float(begin_raw)))
    end = start + int(n_samples)
    if start < 0:
        raise ValueError(f"Negative start sample: {start}")
    if end > data.shape[0]:
        raise ValueError(f"Window end {end} exceeds data length {data.shape[0]}")
    raw = np.asarray(data[start:end, :], dtype=np.float32)
    if raw.shape != (n_samples, 2):
        raise ValueError(f"Unexpected EMG raw shape={raw.shape}; expected {(n_samples, 2)}")
    return raw.T.copy()


def zero_crossings(x: np.ndarray) -> float:
    signs = np.signbit(x)
    return float(np.count_nonzero(signs[1:] != signs[:-1]))


def slope_sign_changes(x: np.ndarray) -> float:
    dx = np.diff(x)
    signs = np.signbit(dx)
    return float(np.count_nonzero(signs[1:] != signs[:-1]))


def compute_features(signal_2xn: np.ndarray) -> np.ndarray:
    feats: list[float] = []
    eps = 1e-12
    for ch in range(signal_2xn.shape[0]):
        x = signal_2xn[ch].astype(np.float64, copy=False)
        variance = float(np.var(x))
        feats.extend(
            [
                float(np.mean(x)),
                float(np.std(x)),
                float(np.sqrt(np.mean(x * x))),
                float(np.mean(np.abs(x))),
                float(np.sum(np.abs(x))),
                float(np.sum(np.abs(np.diff(x)))),
                zero_crossings(x),
                slope_sign_changes(x),
                float(np.min(x)),
                float(np.max(x)),
                float(np.log(variance + eps)),
            ]
        )
    return np.asarray(feats, dtype=np.float32)


def stats_table(arr: np.ndarray) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for j, name in enumerate(FEATURE_COLUMNS):
        col = arr[:, j]
        rows.append(
            {
                "feature": name,
                "mean": float(np.mean(col)),
                "std": float(np.std(col)),
                "min": float(np.min(col)),
                "max": float(np.max(col)),
            }
        )
    return rows


def write_report_md(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# I-DARE EMG Feature Cache Build Smoke Report\n")
    lines.append("This report was generated by `scripts/29_build_idare_emg_feature_cache.py`.\n")
    lines.append("No model training was performed.\n")
    lines.append("## Status\n")
    lines.append(f"Status: **{report['status']}**\n")
    lines.append("## Configuration\n")
    lines.append("```json")
    lines.append(json.dumps(report["config"], indent=2, ensure_ascii=False))
    lines.append("```\n")
    lines.append("## Inputs\n")
    lines.append(f"- trial_index: `{report['inputs']['trial_index']}`\n")
    lines.append("## Outputs\n")
    for key, value in report["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
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
    lines.append("## Feature Columns\n")
    for col in FEATURE_COLUMNS:
        lines.append(f"- `{col}`")
    lines.append("")
    lines.append("## Label Counts\n")
    lines.append("```json")
    lines.append(json.dumps(report["label_counts"], indent=2, ensure_ascii=False))
    lines.append("```\n")
    lines.append("## Feature Stats Preview\n")
    lines.append("| Feature | Mean | Std | Min | Max |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in report["feature_stats"]:
        lines.append(
            "| {feature} | {mean:.6f} | {std:.6f} | {min:.6f} | {max:.6f} |".format(**row)
        )
    lines.append("")
    lines.append("## Runtime\n")
    lines.append(f"- elapsed_sec: `{report['runtime']['elapsed_sec']:.2f}`\n")
    lines.append("## Issues")
    if report["issues"]:
        for issue in report["issues"]:
            lines.append(f"- {issue}")
    else:
        lines.append("- None.")
    lines.append("")
    lines.append("## Warnings")
    if report["warnings"]:
        for warning in report["warnings"]:
            lines.append(f"- {warning}")
    else:
        lines.append("- None.")
    lines.append("")
    lines.append("## Next Step\n")
    lines.append("Validate this smoke output before building the full I-DARE EMG feature cache or running EMG-only training.\n")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    t0 = time.perf_counter()

    issues: list[str] = []
    warnings: list[str] = []

    if not args.trial_index.exists():
        raise FileNotFoundError(f"Trial index not found: {args.trial_index}")

    df = pd.read_csv(args.trial_index)
    required_cols = [
        "subject_id",
        "subject_col",
        "stimulus_id",
        "raw_event_name",
        "event_index_0based",
        "event_index_1based",
        "emg_file",
        "emg_begin_raw",
        "emg_end_raw",
        "emg_duration_samples",
        "emg_duration_sec",
        "valence_score",
        "arousal_score",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Trial index missing required columns: {missing}")

    df = df.copy()
    df["subject_id"] = df["subject_id"].astype(int)
    if args.limit_subjects is not None:
        subjects = sorted(df["subject_id"].unique().tolist())[: args.limit_subjects]
        df = df[df["subject_id"].isin(subjects)].copy()
    if args.limit_rows is not None:
        df = df.head(args.limit_rows).copy()

    df = df.reset_index(drop=True)
    expected_rows = len(df)
    feature_dim = len(FEATURE_COLUMNS)

    args.out_npy.parent.mkdir(parents=True, exist_ok=True)
    args.out_index.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)

    cache = open_memmap(
        args.out_npy,
        mode="w+",
        dtype=np.float32,
        shape=(expected_rows, feature_dim),
    )

    index_rows: list[dict[str, Any]] = []
    baseline_mean_global_values: list[float] = []
    baseline_mean_abs_values: list[float] = []
    corrected_mean_values: list[float] = []
    corrected_std_values: list[float] = []

    extracted = 0
    h5_cache: dict[str, h5py.File] = {}

    print("Building I-DARE EMG feature cache")
    print(f"trial_index: {args.trial_index}")
    print(f"rows selected: {expected_rows}")
    print(f"feature_dim: {feature_dim}")
    print(f"output: {args.out_npy}")

    try:
        for row_idx, row in df.iterrows():
            emg_path = str(row["emg_file"])
            subject_col = str(row["subject_col"])
            event_idx = int(row["event_index_0based"])
            if event_idx <= 0:
                issues.append(f"row {row_idx}: event_index_0based={event_idx} has no preceding BSL event")
                continue

            if emg_path not in h5_cache:
                path = Path(emg_path)
                if not path.exists():
                    issues.append(f"row {row_idx}: missing EMG file {path}")
                    continue
                h5_cache[emg_path] = h5py.File(path, "r")

            h5 = h5_cache[emg_path]
            if subject_col not in h5:
                issues.append(f"row {row_idx}: subject group {subject_col} missing in {emg_path}")
                continue

            group = h5[subject_col]
            data = group["data"]
            begins, ends = read_event_arrays(h5, subject_col)
            bsl_idx = event_idx - 1
            if event_idx >= len(begins) or bsl_idx >= len(begins):
                issues.append(f"row {row_idx}: event index out of range event={event_idx} bsl={bsl_idx}")
                continue

            stim_begin = float(row["emg_begin_raw"])
            bsl_begin = float(begins[bsl_idx])
            stim_event_end = float(row["emg_end_raw"])
            bsl_event_end = float(ends[bsl_idx])
            stim_event_duration = stim_event_end - stim_begin
            bsl_event_duration = bsl_event_end - bsl_begin

            try:
                stim = extract_fixed_window(data, stim_begin, args.window_samples)
                bsl = extract_fixed_window(data, bsl_begin, args.window_samples)
            except Exception as exc:
                issues.append(f"row {row_idx}: extraction failed: {exc}")
                continue

            baseline_mean = bsl.mean(axis=1, keepdims=True).astype(np.float32)
            if args.no_baseline_correction:
                corrected = stim
                baseline_correction = "none"
            else:
                corrected = stim - baseline_mean
                baseline_correction = "subtract_preceding_bsl_per_channel_mean_then_emg_features"

            feats = compute_features(corrected)
            if not np.isfinite(feats).all():
                issues.append(f"row {row_idx}: non-finite features")
                continue

            cache[extracted, :] = feats

            baseline_mean_global = float(baseline_mean.mean())
            baseline_mean_abs = float(np.abs(baseline_mean).mean())
            corrected_mean = float(corrected.mean())
            corrected_std = float(corrected.std())

            baseline_mean_global_values.append(baseline_mean_global)
            baseline_mean_abs_values.append(baseline_mean_abs)
            corrected_mean_values.append(corrected_mean)
            corrected_std_values.append(corrected_std)

            index_row = {
                "cache_row": extracted,
                "subject_id": int(row["subject_id"]),
                "subject_col": subject_col,
                "stimulus_id": row["stimulus_id"],
                "raw_event_name": row["raw_event_name"],
                "bsl_event_index_0based": int(bsl_idx),
                "stim_event_index_0based": int(event_idx),
                "bsl_event_index_1based": int(bsl_idx + 1),
                "stim_event_index_1based": int(event_idx + 1),
                "emg_file": emg_path,
                "emg_channels": ",".join(ch["name"] for ch in EMG_CHANNELS),
                "emg_begin_raw": stim_begin,
                "emg_end_raw": stim_event_end,
                "bsl_emg_begin_raw": bsl_begin,
                "bsl_emg_end_raw": bsl_event_end,
                "fixed_window_samples": int(args.window_samples),
                "stim_event_duration_samples": float(stim_event_duration),
                "bsl_event_duration_samples": float(bsl_event_duration),
                "baseline_correction": baseline_correction,
                "valence_score": row["valence_score"],
                "arousal_score": row["arousal_score"],
                "diag_baseline_mean_global": baseline_mean_global,
                "diag_baseline_mean_abs_mean": baseline_mean_abs,
                "diag_corrected_mean_before_features": corrected_mean,
                "diag_corrected_std_before_features": corrected_std,
            }
            for task in ["valence", "arousal"]:
                for policy in ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]:
                    index_row[f"{task}_{policy}"] = label_value(row[f"{task}_score"], policy)
            index_rows.append(index_row)
            extracted += 1

            if extracted % 250 == 0:
                print(f"extracted {extracted}/{expected_rows}")
    finally:
        for h5 in h5_cache.values():
            h5.close()

    if extracted != expected_rows:
        warnings.append(f"Extracted {extracted} rows but selected {expected_rows} rows.")

    if extracted < expected_rows:
        # Rewrite compact cache without unfilled rows.
        compact = np.asarray(cache[:extracted], dtype=np.float32)
        del cache
        np.save(args.out_npy, compact)
        feature_array = compact
    else:
        feature_array = np.asarray(cache[:], dtype=np.float32)
        del cache

    index_df = pd.DataFrame(index_rows)
    index_df.to_csv(args.out_index, index=False)

    feature_nan_count = int(np.isnan(feature_array).sum())
    feature_inf_count = int(np.isinf(feature_array).sum())
    if feature_nan_count:
        issues.append(f"Feature cache contains {feature_nan_count} NaN values.")
    if feature_inf_count:
        issues.append(f"Feature cache contains {feature_inf_count} Inf values.")

    status = "PASSED" if not issues else "FAILED"
    report = {
        "status": status,
        "generated_at_utc": pd.Timestamp.now("UTC").isoformat(),
        "config": {
            "source": "I-DARE raw_downloads/EMG HDF5 .mat",
            "trial_index": str(args.trial_index),
            "source_fs": SOURCE_FS,
            "window_sec": WINDOW_SEC,
            "window_samples": int(args.window_samples),
            "emg_channels": EMG_CHANNELS,
            "feature_names": FEATURE_NAMES,
            "feature_columns": FEATURE_COLUMNS,
            "feature_dim": feature_dim,
            "feature_policy": "baseline-corrected EMG time-domain features; no raw waveform z-score before feature extraction",
            "baseline_source": "preceding BSL event inferred from event_index_0based - 1",
            "limit_subjects": args.limit_subjects,
            "limit_rows": args.limit_rows,
            "baseline_correction": "none" if args.no_baseline_correction else "subtract preceding BSL per-channel mean",
        },
        "inputs": {
            "trial_index": str(args.trial_index),
        },
        "outputs": {
            "feature_cache_npy": str(args.out_npy),
            "cache_index_csv": str(args.out_index),
            "build_report_md": str(args.out_md),
            "build_report_json": str(args.out_json),
        },
        "counts": {
            "selected_rows": int(expected_rows),
            "extracted_rows": int(extracted),
            "cache_index_rows": int(len(index_df)),
            "subject_files": int(df["subject_id"].nunique()) if len(df) else 0,
            "feature_dim": int(feature_dim),
        },
        "cache": {
            "shape": list(feature_array.shape),
            "dtype": str(feature_array.dtype),
            "file_size": int(args.out_npy.stat().st_size) if args.out_npy.exists() else None,
            "file_size_human": file_size_human(args.out_npy.stat().st_size) if args.out_npy.exists() else None,
        },
        "diagnostics": {
            "baseline_mean_global": finite_summary(baseline_mean_global_values),
            "baseline_mean_abs_mean": finite_summary(baseline_mean_abs_values),
            "corrected_mean_before_features": finite_summary(corrected_mean_values),
            "corrected_std_before_features": finite_summary(corrected_std_values),
            "feature_nan_count": feature_nan_count,
            "feature_inf_count": feature_inf_count,
        },
        "label_counts": label_counts(index_df) if len(index_df) else {},
        "feature_stats": stats_table(feature_array) if extracted else [],
        "runtime": {
            "elapsed_sec": float(time.perf_counter() - t0),
        },
        "issues": issues,
        "warnings": warnings,
    }

    args.out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    write_report_md(report, args.out_md)

    print(f"Wrote: {args.out_md}")
    print(f"Wrote: {args.out_json}")
    print(f"Status: {status}")
    print(f"Rows extracted: {extracted} / {expected_rows}")
    print(f"Feature dim: {feature_dim}")
    print(f"Cache size: {report['cache']['file_size_human']}")
    print(f"Elapsed: {report['runtime']['elapsed_sec']:.2f}s")
    print(f"Issues: {len(issues)}")
    print(f"Warnings: {len(warnings)}")

    return 0 if status == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
