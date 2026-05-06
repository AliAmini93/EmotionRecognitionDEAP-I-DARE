#!/usr/bin/env python3
"""Build a DEAP EMG feature-window cache from preprocessed Python .dat files.

Smoke-first script. No model training is performed.

DEAP preprocessed Python:
- data:   [40, 40, 8064]
- labels: [40, 4]
- fs: 128 Hz
- first 384 samples = 3s baseline
- remaining 7680 samples = 60s stimulus
- 12 non-overlapping 5s windows per trial
- EMG channels:
  - zEMG: channel 35, index 34
  - tEMG: channel 36, index 35

Feature policy:
- subtract 3s baseline per-channel mean
- split corrected stimulus into 12 windows
- extract amplitude/time-domain EMG features per window
- do NOT per-window z-score raw EMG before feature extraction
"""

from __future__ import annotations

import argparse
import json
import pickle
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_DEAP_DIR = Path("/mnt/HDD/AliWorks/DEAP/data_preprocessed_python")
DEFAULT_OUT_NPY = ROOT / ".cache" / "deap_emg_features_smoke.npy"
DEFAULT_OUT_INDEX = ROOT / ".cache" / "deap_emg_feature_cache_index_smoke.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "deap_emg_feature_cache_build_smoke.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "deap_emg_feature_cache_build_smoke.json"

TASKS = {
    "valence": 0,
    "arousal": 1,
    "dominance": 2,
    "liking": 3,
}

EMG_CHANNELS = [
    ("zEMG", 34),
    ("tEMG", 35),
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

SOURCE_FS = 128.0
BASELINE_SAMPLES = 384
STIMULUS_SAMPLES = 7680
WINDOW_SAMPLES = 640
WINDOWS_PER_TRIAL = 12
EXPECTED_DATA_SHAPE = (40, 40, 8064)
EXPECTED_LABEL_SHAPE = (40, 4)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deap-dir", type=Path, default=DEFAULT_DEAP_DIR)
    parser.add_argument("--limit-subjects", type=int, default=None)
    parser.add_argument("--out-npy", type=Path, default=DEFAULT_OUT_NPY)
    parser.add_argument("--out-index", type=Path, default=DEFAULT_OUT_INDEX)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    return parser.parse_args()


def load_deap_dat(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        return pickle.load(f, encoding="latin1")


def subject_id_from_file(path: Path) -> int:
    stem = path.stem
    if not stem.startswith("s"):
        raise ValueError(f"Unexpected DEAP file name: {path.name}")
    return int(stem[1:])


def label_to_binary(score: float, policy: str) -> float | int:
    if score > 5.0:
        return 1
    if score < 5.0:
        return 0
    if policy == "discard_midpoint":
        return float("nan")
    if policy == "midpoint_as_low":
        return 0
    if policy == "midpoint_as_high":
        return 1
    raise ValueError(f"Unknown policy: {policy}")


def zero_crossings(x: np.ndarray) -> int:
    if x.size < 2:
        return 0
    signs = np.signbit(x)
    return int(np.count_nonzero(signs[1:] != signs[:-1]))


def slope_sign_changes(x: np.ndarray) -> int:
    if x.size < 3:
        return 0
    dx = np.diff(x)
    signs = np.signbit(dx)
    return int(np.count_nonzero(signs[1:] != signs[:-1]))


def channel_features(x: np.ndarray) -> list[float]:
    x = np.asarray(x, dtype=np.float64)
    var = float(np.var(x))
    return [
        float(np.mean(x)),
        float(np.std(x)),
        float(np.sqrt(np.mean(x * x))),
        float(np.mean(np.abs(x))),
        float(np.sum(np.abs(x))),
        float(np.sum(np.abs(np.diff(x)))) if x.size > 1 else 0.0,
        float(zero_crossings(x)),
        float(slope_sign_changes(x)),
        float(np.min(x)),
        float(np.max(x)),
        float(np.log(var + 1e-8)),
    ]


def extract_window_features(window: np.ndarray) -> list[float]:
    feats: list[float] = []
    for ch_i in range(window.shape[0]):
        feats.extend(channel_features(window[ch_i]))
    return feats


def stats(values: list[float]) -> dict[str, float | None]:
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


def label_counts(df: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for task in TASKS:
        out[task] = {}
        for policy in ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]:
            col = f"{task}_{policy}"
            if col not in df.columns:
                continue
            vals = df[col]
            if policy == "discard_midpoint":
                out[task][policy] = {
                    "0": int((vals == 0).sum()),
                    "1": int((vals == 1).sum()),
                    "discard": int(vals.isna().sum()),
                }
            else:
                out[task][policy] = {
                    "0": int((vals == 0).sum()),
                    "1": int((vals == 1).sum()),
                }
    return out


def feature_columns() -> list[str]:
    cols: list[str] = []
    for ch_name, _ in EMG_CHANNELS:
        for feat in FEATURE_NAMES:
            cols.append(f"{ch_name}_{feat}")
    return cols


def human_size(n: int) -> str:
    value = float(n)
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024 or unit == "GB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} GB"


def write_markdown(report: dict[str, Any], path: Path) -> None:
    cfg = report["config"]
    counts = report["counts"]
    cache = report["cache"]
    diagnostics = report["diagnostics"]
    label_counts_obj = report["label_counts"]

    lines: list[str] = []

    lines.append("# DEAP EMG Feature Cache Build Smoke Report")
    lines.append("")
    lines.append("This report was generated by `scripts/27_build_deap_emg_feature_cache.py`.")
    lines.append("")
    lines.append("No model training was performed.")
    lines.append("")
    lines.append("## Status")
    lines.append("")
    lines.append(f"Status: **{report['status']}**")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(cfg, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- deap_dir: `{report['inputs']['deap_dir']}`")
    lines.append("")
    lines.append("## Outputs")
    lines.append("")
    for k, v in report["outputs"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append("| Item | Value |")
    lines.append("|---|---:|")
    for k, v in counts.items():
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("## Cache")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(cache, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## Diagnostics")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(diagnostics, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## Feature Columns")
    lines.append("")
    for col in cfg["feature_columns"]:
        lines.append(f"- `{col}`")
    lines.append("")
    lines.append("## Label Counts")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(label_counts_obj, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## Feature Stats Preview")
    lines.append("")
    lines.append("| Feature | Mean | Std | Min | Max |")
    lines.append("|---|---:|---:|---:|---:|")
    for name, st in list(report["feature_stats"].items())[:24]:
        lines.append(
            f"| {name} | {st['mean']:.6f} | {st['std']:.6f} | {st['min']:.6f} | {st['max']:.6f} |"
        )
    lines.append("")
    lines.append("## Runtime")
    lines.append("")
    lines.append(f"- elapsed_sec: `{report['elapsed_sec']}`")
    lines.append("")
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
    lines.append("## Next Step")
    lines.append("")
    lines.append("Validate this smoke output before building the full DEAP EMG feature cache or running EMG-only training.")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    t0 = time.perf_counter()

    files = sorted(args.deap_dir.glob("s*.dat"))
    if args.limit_subjects is not None:
        files = files[: args.limit_subjects]

    issues: list[str] = []
    warnings: list[str] = []

    if not args.deap_dir.exists():
        issues.append(f"DEAP dir does not exist: {args.deap_dir}")

    if not files:
        issues.append(f"No s*.dat files found in {args.deap_dir}")

    expected_rows = len(files) * 40 * WINDOWS_PER_TRIAL
    feat_cols = feature_columns()
    feature_dim = len(feat_cols)

    all_features: list[list[float]] = []
    rows: list[dict[str, Any]] = []

    baseline_mean_global_values: list[float] = []
    baseline_mean_abs_values: list[float] = []
    corrected_mean_values: list[float] = []
    corrected_std_values: list[float] = []

    print("Building DEAP EMG feature cache")
    print(f"DEAP dir: {args.deap_dir}")
    print(f"subject files: {len(files)}")
    print(f"feature_dim: {feature_dim}")
    print(f"output: {args.out_npy}")

    for file_i, path in enumerate(files, start=1):
        print(f"[{file_i:03d}/{len(files):03d}] {path.name}")
        sid = subject_id_from_file(path)

        try:
            obj = load_deap_dat(path)
        except Exception as exc:
            issues.append(f"{path.name}: failed to load: {exc!r}")
            continue

        data = obj.get("data")
        labels = obj.get("labels")

        if not hasattr(data, "shape") or tuple(data.shape) != EXPECTED_DATA_SHAPE:
            issues.append(f"{path.name}: unexpected data shape {getattr(data, 'shape', None)}")
            continue

        if not hasattr(labels, "shape") or tuple(labels.shape) != EXPECTED_LABEL_SHAPE:
            issues.append(f"{path.name}: unexpected labels shape {getattr(labels, 'shape', None)}")
            continue

        data = np.asarray(data, dtype=np.float64)
        labels = np.asarray(labels, dtype=np.float64)

        if not np.isfinite(data).all():
            issues.append(f"{path.name}: data contains NaN/Inf")
            continue

        for trial_i in range(40):
            trial = data[trial_i]
            label_vec = labels[trial_i]

            emg = trial[[idx for _, idx in EMG_CHANNELS], :]
            baseline = emg[:, :BASELINE_SAMPLES]
            stimulus = emg[:, BASELINE_SAMPLES : BASELINE_SAMPLES + STIMULUS_SAMPLES]

            if stimulus.shape != (2, STIMULUS_SAMPLES):
                issues.append(f"{path.name} trial {trial_i + 1}: unexpected stimulus shape {stimulus.shape}")
                continue

            bmean = baseline.mean(axis=1, keepdims=True)
            corrected = stimulus - bmean

            baseline_mean_global = float(bmean.mean())
            baseline_mean_abs = float(np.mean(np.abs(bmean)))
            corrected_mean = float(corrected.mean())
            corrected_std = float(corrected.std())

            baseline_mean_global_values.append(baseline_mean_global)
            baseline_mean_abs_values.append(baseline_mean_abs)
            corrected_mean_values.append(corrected_mean)
            corrected_std_values.append(corrected_std)

            for win_i in range(WINDOWS_PER_TRIAL):
                start = win_i * WINDOW_SAMPLES
                end = start + WINDOW_SAMPLES
                window = corrected[:, start:end]

                feats = extract_window_features(window)
                if len(feats) != feature_dim:
                    issues.append(
                        f"{path.name} trial {trial_i + 1} window {win_i + 1}: "
                        f"feature_dim {len(feats)} != {feature_dim}"
                    )
                    continue

                feats_arr = np.asarray(feats)
                if not np.isfinite(feats_arr).all():
                    issues.append(f"{path.name} trial {trial_i + 1} window {win_i + 1}: features contain NaN/Inf")
                    continue

                cache_row = len(all_features)
                all_features.append(feats)

                row: dict[str, Any] = {
                    "cache_row": cache_row,
                    "subject_id": sid,
                    "subject_file": path.name,
                    "trial_id": trial_i + 1,
                    "trial_index_0based": trial_i,
                    "window_id": win_i + 1,
                    "window_index_0based": win_i,
                    "window_start_sample_128hz": BASELINE_SAMPLES + start,
                    "window_end_sample_128hz_exclusive": BASELINE_SAMPLES + end,
                    "emg_channels": "zEMG,tEMG",
                    "baseline_correction": "subtract_deap_3s_baseline_per_channel_mean_then_emg_features",
                    "valence_score": float(label_vec[0]),
                    "arousal_score": float(label_vec[1]),
                    "dominance_score": float(label_vec[2]),
                    "liking_score": float(label_vec[3]),
                    "diag_baseline_mean_global": baseline_mean_global,
                    "diag_baseline_mean_abs_mean": baseline_mean_abs,
                    "diag_corrected_mean_before_features": corrected_mean,
                    "diag_corrected_std_before_features": corrected_std,
                }

                for task, label_i in TASKS.items():
                    score = float(label_vec[label_i])
                    for policy in ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]:
                        row[f"{task}_{policy}"] = label_to_binary(score, policy)

                rows.append(row)

    if all_features:
        feature_arr = np.asarray(all_features, dtype=np.float32)
    else:
        feature_arr = np.empty((0, feature_dim), dtype=np.float32)

    index_df = pd.DataFrame(rows)

    args.out_npy.parent.mkdir(parents=True, exist_ok=True)
    args.out_index.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)

    np.save(args.out_npy, feature_arr)
    index_df.to_csv(args.out_index, index=False)

    feature_stats: dict[str, Any] = {}
    if feature_arr.size:
        for i, col in enumerate(feat_cols):
            feature_stats[col] = {
                "mean": float(np.mean(feature_arr[:, i])),
                "std": float(np.std(feature_arr[:, i])),
                "min": float(np.min(feature_arr[:, i])),
                "max": float(np.max(feature_arr[:, i])),
            }

    status = "PASSED" if not issues and len(index_df) == expected_rows else "FAILED"

    report = {
        "status": status,
        "generated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "config": {
            "source": "DEAP data_preprocessed_python",
            "deap_dir": str(args.deap_dir),
            "source_fs": SOURCE_FS,
            "baseline_samples": BASELINE_SAMPLES,
            "baseline_sec": BASELINE_SAMPLES / SOURCE_FS,
            "stimulus_samples": STIMULUS_SAMPLES,
            "stimulus_sec": STIMULUS_SAMPLES / SOURCE_FS,
            "window_samples": WINDOW_SAMPLES,
            "window_sec": WINDOW_SAMPLES / SOURCE_FS,
            "windows_per_trial": WINDOWS_PER_TRIAL,
            "emg_channels": [{"name": name, "index_0based": idx, "channel_1based": idx + 1} for name, idx in EMG_CHANNELS],
            "feature_names": FEATURE_NAMES,
            "feature_columns": feat_cols,
            "feature_dim": feature_dim,
            "feature_policy": "baseline-corrected EMG time-domain features; no raw waveform z-score before feature extraction",
            "limit_subjects": args.limit_subjects,
        },
        "inputs": {
            "deap_dir": str(args.deap_dir),
        },
        "outputs": {
            "feature_cache_npy": str(args.out_npy),
            "cache_index_csv": str(args.out_index),
            "build_report_md": str(args.out_md),
            "build_report_json": str(args.out_json),
        },
        "counts": {
            "subject_files": len(files),
            "expected_rows": expected_rows,
            "extracted_rows": int(feature_arr.shape[0]),
            "cache_index_rows": int(len(index_df)),
            "feature_dim": feature_dim,
        },
        "cache": {
            "shape": list(feature_arr.shape),
            "dtype": str(feature_arr.dtype),
            "file_size": args.out_npy.stat().st_size if args.out_npy.exists() else None,
            "file_size_human": human_size(args.out_npy.stat().st_size) if args.out_npy.exists() else None,
        },
        "diagnostics": {
            "baseline_mean_global": stats(baseline_mean_global_values),
            "baseline_mean_abs_mean": stats(baseline_mean_abs_values),
            "corrected_mean_before_features": stats(corrected_mean_values),
            "corrected_std_before_features": stats(corrected_std_values),
            "feature_nan_count": int(np.isnan(feature_arr).sum()) if feature_arr.size else 0,
            "feature_inf_count": int(np.isinf(feature_arr).sum()) if feature_arr.size else 0,
        },
        "feature_stats": feature_stats,
        "label_counts": label_counts(index_df) if not index_df.empty else {},
        "issues": issues,
        "warnings": warnings,
        "elapsed_sec": round(time.perf_counter() - t0, 2),
    }

    write_markdown(report, args.out_md)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    return report


def main() -> int:
    args = parse_args()
    report = build_report(args)

    print(f"Wrote: {args.out_md}")
    print(f"Wrote: {args.out_json}")
    print(f"Status: {report['status']}")
    print(f"Rows extracted: {report['counts']['extracted_rows']} / {report['counts']['expected_rows']}")
    print(f"Feature dim: {report['counts']['feature_dim']}")
    print(f"Cache size: {report['cache']['file_size_human']}")
    print(f"Elapsed: {report['elapsed_sec']:.2f}s")
    print(f"Issues: {len(report['issues'])}")
    print(f"Warnings: {len(report['warnings'])}")

    return 0 if report["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
