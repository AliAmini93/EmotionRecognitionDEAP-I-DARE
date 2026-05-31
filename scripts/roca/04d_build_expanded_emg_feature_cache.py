#!/usr/bin/env python3
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


ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / ".cache"
ROCA_DIR = ROOT / "docs" / "roca"

TRIAL_INDEX = CACHE_DIR / "idare_trial_index.csv"

OUT_NPY = CACHE_DIR / "roca_idare_emg_expanded_features.npy"
OUT_INDEX = CACHE_DIR / "roca_idare_emg_expanded_feature_index.csv"
OUT_COLUMNS = CACHE_DIR / "roca_idare_emg_expanded_feature_columns.json"
OUT_MD = ROCA_DIR / "emg_expanded_feature_cache_report_current.md"
OUT_JSON = ROCA_DIR / "emg_expanded_feature_cache_report_current.json"

FS = 2000.0
WINDOW_SEC = 5.0
WINDOW_SAMPLES = 10000
N_CHANNELS = 2
EPS = 1e-12


def parse_args():
    parser = argparse.ArgumentParser(description="Build expanded ROCA EMG feature cache for I-DARE.")
    parser.add_argument("--trial-index", type=Path, default=TRIAL_INDEX)
    parser.add_argument("--out-npy", type=Path, default=OUT_NPY)
    parser.add_argument("--out-index", type=Path, default=OUT_INDEX)
    parser.add_argument("--out-columns", type=Path, default=OUT_COLUMNS)
    parser.add_argument("--out-md", type=Path, default=OUT_MD)
    parser.add_argument("--out-json", type=Path, default=OUT_JSON)
    parser.add_argument("--limit-rows", type=int, default=None)
    return parser.parse_args()


def safe_float(x: Any):
    try:
        v = float(x)
    except Exception:
        return None
    return v if math.isfinite(v) else None


def clean_json(x):
    if isinstance(x, dict):
        return {str(k): clean_json(v) for k, v in x.items()}
    if isinstance(x, list):
        return [clean_json(v) for v in x]
    if isinstance(x, tuple):
        return [clean_json(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        v = float(x)
        return None if math.isfinite(v) else None
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    return x


def file_size_human(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024 or unit == "GB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} GB"


def read_event_arrays(h5: h5py.File, subject_col: str):
    group = h5[subject_col]
    begins = np.asarray(group["event_begin"]).reshape(-1).astype(np.float64)
    ends = np.asarray(group["event_end"]).reshape(-1).astype(np.float64)
    return begins, ends


def extract_window(data: h5py.Dataset, begin_raw: float, n_samples: int = WINDOW_SAMPLES) -> np.ndarray:
    start = int(round(float(begin_raw)))
    stop = start + int(n_samples)
    if start < 0:
        raise ValueError(f"Negative start sample: {start}")
    if stop > data.shape[0]:
        raise ValueError(f"Window stop {stop} exceeds data length {data.shape[0]}")
    arr = np.asarray(data[start:stop, :], dtype=np.float32)
    if arr.shape != (n_samples, N_CHANNELS):
        raise ValueError(f"Unexpected EMG window shape {arr.shape}")
    return arr.T.copy()


def zero_crossings(x: np.ndarray) -> float:
    signs = np.signbit(x)
    return float(np.count_nonzero(signs[1:] != signs[:-1]))


def slope_sign_changes(x: np.ndarray) -> float:
    dx = np.diff(x)
    signs = np.signbit(dx)
    return float(np.count_nonzero(signs[1:] != signs[:-1]))


def moving_average(x: np.ndarray, win: int) -> np.ndarray:
    win = int(max(1, win))
    if win == 1:
        return x.astype(np.float64, copy=False)
    kernel = np.ones(win, dtype=np.float64) / float(win)
    return np.convolve(x.astype(np.float64, copy=False), kernel, mode="same")


def skewness(x: np.ndarray) -> float:
    x = x.astype(np.float64, copy=False)
    sd = float(np.std(x))
    if sd < EPS:
        return 0.0
    z = (x - float(np.mean(x))) / sd
    return float(np.mean(z ** 3))


def kurtosis_excess(x: np.ndarray) -> float:
    x = x.astype(np.float64, copy=False)
    sd = float(np.std(x))
    if sd < EPS:
        return 0.0
    z = (x - float(np.mean(x))) / sd
    return float(np.mean(z ** 4) - 3.0)


def robust_stats(prefix: str, x: np.ndarray, names: list[str], vals: list[float]) -> None:
    x = x.astype(np.float64, copy=False)
    absx = np.abs(x)
    q10, q25, q50, q75, q90, q95, q99 = np.quantile(x, [0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99])
    aq50, aq75, aq90, aq95, aq99 = np.quantile(absx, [0.50, 0.75, 0.90, 0.95, 0.99])
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med)))
    var = float(np.var(x))

    feats = {
        "mean": float(np.mean(x)),
        "std": float(np.std(x)),
        "var": var,
        "log_var": float(np.log(var + EPS)),
        "rms": float(np.sqrt(np.mean(x * x))),
        "mav": float(np.mean(absx)),
        "iemg": float(np.sum(absx)),
        "min": float(np.min(x)),
        "max": float(np.max(x)),
        "ptp": float(np.ptp(x)),
        "median": med,
        "mad": mad,
        "q10": float(q10),
        "q25": float(q25),
        "q50": float(q50),
        "q75": float(q75),
        "q90": float(q90),
        "q95": float(q95),
        "q99": float(q99),
        "iqr": float(q75 - q25),
        "abs_median": float(aq50),
        "abs_q75": float(aq75),
        "abs_q90": float(aq90),
        "abs_q95": float(aq95),
        "abs_q99": float(aq99),
        "waveform_length": float(np.sum(np.abs(np.diff(x)))),
        "zero_crossings": zero_crossings(x),
        "slope_sign_changes": slope_sign_changes(x),
        "skewness": skewness(x),
        "kurtosis_excess": kurtosis_excess(x),
    }

    for k, v in feats.items():
        names.append(f"{prefix}_{k}")
        vals.append(float(v))


def frequency_features(prefix: str, x: np.ndarray, fs: float, names: list[str], vals: list[float]) -> None:
    x = x.astype(np.float64, copy=False)
    x = x - float(np.mean(x))
    freqs = np.fft.rfftfreq(len(x), d=1.0 / fs)
    spec = np.fft.rfft(x)
    power = np.abs(spec) ** 2
    total_power = float(np.sum(power) + EPS)

    def band_power(lo: float, hi: float) -> float:
        m = (freqs >= lo) & (freqs < hi)
        return float(np.sum(power[m]))

    bands = {
        "bp_20_60": band_power(20, 60),
        "bp_60_100": band_power(60, 100),
        "bp_100_250": band_power(100, 250),
        "bp_250_500": band_power(250, 500),
        "bp_500_900": band_power(500, 900),
    }

    mean_freq = float(np.sum(freqs * power) / total_power)
    cumsum = np.cumsum(power)
    med_freq = float(freqs[np.searchsorted(cumsum, total_power / 2.0)])
    p_norm = power / total_power
    spectral_entropy = float(-np.sum(p_norm * np.log(p_norm + EPS)) / np.log(len(p_norm)))

    base = {
        "total_power": total_power,
        "log_total_power": float(np.log(total_power + EPS)),
        "mean_freq": mean_freq,
        "median_freq": med_freq,
        "spectral_entropy": spectral_entropy,
    }
    base.update(bands)
    for k, v in bands.items():
        base[f"{k}_ratio"] = float(v / total_power)

    for k, v in base.items():
        names.append(f"{prefix}_{k}")
        vals.append(float(v))


def envelope_features(prefix: str, x: np.ndarray, fs: float, names: list[str], vals: list[float]) -> np.ndarray:
    absx = np.abs(x.astype(np.float64, copy=False))
    env = moving_average(absx, int(round(0.100 * fs)))  # 100 ms envelope

    robust_stats(f"{prefix}_env", env, names, vals)

    peak_idx = int(np.argmax(env))
    peak_val = float(env[peak_idx])
    names.extend([
        f"{prefix}_env_time_to_peak_sec",
        f"{prefix}_env_peak_to_mean",
        f"{prefix}_env_peak_to_median",
    ])
    vals.extend([
        float(peak_idx / fs),
        float(peak_val / (np.mean(env) + EPS)),
        float(peak_val / (np.median(env) + EPS)),
    ])
    return env


def burst_features(prefix: str, stim_abs: np.ndarray, bsl_abs: np.ndarray, fs: float, names: list[str], vals: list[float]) -> None:
    b_mean = float(np.mean(bsl_abs))
    b_std = float(np.std(bsl_abs))
    thr = b_mean + 2.0 * b_std

    above = stim_abs > thr
    count = int(np.sum(above))
    duration_sec = float(count / fs)

    burst_count = 0
    longest = 0
    first_onset = None
    current = 0

    for i, flag in enumerate(above):
        if flag:
            if current == 0:
                burst_count += 1
                if first_onset is None:
                    first_onset = i / fs
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    names.extend([
        f"{prefix}_burst_threshold",
        f"{prefix}_above_thr_rate",
        f"{prefix}_above_thr_duration_sec",
        f"{prefix}_burst_count",
        f"{prefix}_longest_burst_sec",
        f"{prefix}_first_burst_onset_sec",
        f"{prefix}_burst_area",
    ])
    vals.extend([
        float(thr),
        float(np.mean(above)),
        duration_sec,
        float(burst_count),
        float(longest / fs),
        float(first_onset) if first_onset is not None else 5.0,
        float(np.sum(stim_abs[above] - thr)) if count else 0.0,
    ])


def temporal_bin_features(prefix: str, x: np.ndarray, fs: float, names: list[str], vals: list[float]) -> None:
    n_bins = 5
    bin_len = int(round(fs))
    absx = np.abs(x.astype(np.float64, copy=False))

    rms_vals = []
    mav_vals = []
    q95_vals = []

    for b in range(n_bins):
        seg = x[b * bin_len:(b + 1) * bin_len].astype(np.float64, copy=False)
        aseg = np.abs(seg)
        rms = float(np.sqrt(np.mean(seg * seg)))
        mav = float(np.mean(aseg))
        q95 = float(np.quantile(aseg, 0.95))
        rms_vals.append(rms)
        mav_vals.append(mav)
        q95_vals.append(q95)

        names.extend([
            f"{prefix}_bin{b+1}_rms",
            f"{prefix}_bin{b+1}_mav",
            f"{prefix}_bin{b+1}_abs_q95",
        ])
        vals.extend([rms, mav, q95])

    for metric_name, arr in [
        ("rms", np.asarray(rms_vals)),
        ("mav", np.asarray(mav_vals)),
        ("abs_q95", np.asarray(q95_vals)),
    ]:
        early = float(np.mean(arr[:2]))
        late = float(np.mean(arr[3:]))
        slope = float(np.polyfit(np.arange(n_bins, dtype=float), arr, deg=1)[0])
        names.extend([
            f"{prefix}_bins_{metric_name}_early_mean",
            f"{prefix}_bins_{metric_name}_late_mean",
            f"{prefix}_bins_{metric_name}_late_minus_early",
            f"{prefix}_bins_{metric_name}_max",
            f"{prefix}_bins_{metric_name}_argmax_1based",
            f"{prefix}_bins_{metric_name}_slope",
        ])
        vals.extend([
            early,
            late,
            float(late - early),
            float(np.max(arr)),
            float(np.argmax(arr) + 1),
            slope,
        ])


def channel_features(ch_name: str, stim: np.ndarray, bsl: np.ndarray, fs: float, names: list[str], vals: list[float]) -> dict[str, float]:
    stim = stim.astype(np.float64, copy=False)
    bsl = bsl.astype(np.float64, copy=False)

    bsl_mean = float(np.mean(bsl))
    bsl_std = float(np.std(bsl))
    bsl_abs = np.abs(bsl)
    stim_abs = np.abs(stim)

    corrected = stim - bsl_mean
    abs_delta = stim_abs - float(np.mean(bsl_abs))
    z_by_bsl = (stim - bsl_mean) / (bsl_std + EPS)

    robust_stats(f"{ch_name}_stim_raw", stim, names, vals)
    robust_stats(f"{ch_name}_bsl_raw", bsl, names, vals)
    robust_stats(f"{ch_name}_stim_minus_bslmean", corrected, names, vals)
    robust_stats(f"{ch_name}_stim_abs_minus_bsl_absmean", abs_delta, names, vals)
    robust_stats(f"{ch_name}_stim_z_by_bsl", z_by_bsl, names, vals)

    stim_env = envelope_features(f"{ch_name}_stim", stim, fs, names, vals)
    bsl_env = envelope_features(f"{ch_name}_bsl", bsl, fs, names, vals)
    envelope_features(f"{ch_name}_stim_minus_bslmean", corrected, fs, names, vals)

    burst_features(f"{ch_name}_stim_abs_vs_bsl_abs", stim_abs, bsl_abs, fs, names, vals)
    temporal_bin_features(f"{ch_name}_stim", stim, fs, names, vals)
    temporal_bin_features(f"{ch_name}_stim_minus_bslmean", corrected, fs, names, vals)

    frequency_features(f"{ch_name}_stim", stim, fs, names, vals)
    frequency_features(f"{ch_name}_bsl", bsl, fs, names, vals)
    frequency_features(f"{ch_name}_stim_minus_bslmean", corrected, fs, names, vals)

    summary = {
        "stim_rms": float(np.sqrt(np.mean(stim * stim))),
        "bsl_rms": float(np.sqrt(np.mean(bsl * bsl))),
        "corr_rms": float(np.sqrt(np.mean(corrected * corrected))),
        "stim_mav": float(np.mean(stim_abs)),
        "bsl_mav": float(np.mean(bsl_abs)),
        "stim_env_mean": float(np.mean(stim_env)),
        "bsl_env_mean": float(np.mean(bsl_env)),
        "stim_env_max": float(np.max(stim_env)),
        "bsl_env_max": float(np.max(bsl_env)),
    }

    for key in ["rms", "mav", "env_mean", "env_max"]:
        if key == "rms":
            stim_v, bsl_v = summary["stim_rms"], summary["bsl_rms"]
        elif key == "mav":
            stim_v, bsl_v = summary["stim_mav"], summary["bsl_mav"]
        elif key == "env_mean":
            stim_v, bsl_v = summary["stim_env_mean"], summary["bsl_env_mean"]
        else:
            stim_v, bsl_v = summary["stim_env_max"], summary["bsl_env_max"]

        names.extend([
            f"{ch_name}_{key}_delta_stim_minus_bsl",
            f"{ch_name}_{key}_ratio_stim_over_bsl",
            f"{ch_name}_{key}_log_ratio_stim_over_bsl",
        ])
        vals.extend([
            float(stim_v - bsl_v),
            float(stim_v / (bsl_v + EPS)),
            float(np.log(stim_v + EPS) - np.log(bsl_v + EPS)),
        ])

    return summary


def add_interaction_features(summaries: list[dict[str, float]], names: list[str], vals: list[float]) -> None:
    a, b = summaries[0], summaries[1]
    keys = sorted(a.keys())

    for key in keys:
        av = float(a[key])
        bv = float(b[key])
        names.extend([
            f"interaction_{key}_ch1_minus_ch2",
            f"interaction_{key}_ch1_plus_ch2",
            f"interaction_{key}_abs_diff",
            f"interaction_{key}_ratio_ch1_over_ch2",
            f"interaction_{key}_asymmetry",
            f"interaction_{key}_max_channel",
        ])
        vals.extend([
            float(av - bv),
            float(av + bv),
            float(abs(av - bv)),
            float(av / (bv + EPS)),
            float((av - bv) / (abs(av) + abs(bv) + EPS)),
            float(max(av, bv)),
        ])


def compute_expanded_features(stim_2xn: np.ndarray, bsl_2xn: np.ndarray, fs: float = FS):
    names: list[str] = []
    vals: list[float] = []
    summaries = []

    for ch in range(N_CHANNELS):
        ch_name = f"ch{ch+1}"
        summaries.append(channel_features(ch_name, stim_2xn[ch], bsl_2xn[ch], fs, names, vals))

    add_interaction_features(summaries, names, vals)

    arr = np.asarray(vals, dtype=np.float32)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)

    return names, arr


def feature_stats_preview(x: np.ndarray, columns: list[str], limit: int = 40):
    rows = []
    for j, col in enumerate(columns[:limit]):
        v = x[:, j].astype(float)
        rows.append({
            "feature": col,
            "mean": safe_float(np.mean(v)),
            "std": safe_float(np.std(v)),
            "min": safe_float(np.min(v)),
            "max": safe_float(np.max(v)),
        })
    return rows


def write_md(report: dict[str, Any], path: Path) -> None:
    lines = []
    lines.append("# ROCA-I-DARE Expanded EMG Feature Cache Report\n")
    lines.append("No model training was performed.\n")

    lines.append("## Status\n")
    lines.append(f"Status: **{report['status']}**\n")

    lines.append("## Counts\n")
    lines.append("| Item | Value |")
    lines.append("|---|---:|")
    for k, v in report["counts"].items():
        lines.append(f"| {k} | {v} |")
    lines.append("")

    lines.append("## Outputs\n")
    for k, v in report["outputs"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")

    lines.append("## Feature Groups\n")
    for item in report["feature_groups"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## Diagnostics\n")
    lines.append("```json")
    lines.append(json.dumps(report["diagnostics"], indent=2, ensure_ascii=False))
    lines.append("```")
    lines.append("")

    lines.append("## Feature Stats Preview\n")
    lines.append("| Feature | Mean | Std | Min | Max |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in report["feature_stats_preview"]:
        lines.append(
            "| {feature} | {mean:.6f} | {std:.6f} | {min:.6f} | {max:.6f} |".format(**row)
        )
    lines.append("")

    lines.append("## Issues\n")
    if report["issues"]:
        for issue in report["issues"]:
            lines.append(f"- {issue}")
    else:
        lines.append("- None.")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    args = parse_args()
    t0 = time.perf_counter()

    args.out_npy.parent.mkdir(parents=True, exist_ok=True)
    args.out_index.parent.mkdir(parents=True, exist_ok=True)
    args.out_columns.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)

    if not args.trial_index.exists():
        raise FileNotFoundError(args.trial_index)

    df = pd.read_csv(args.trial_index)
    required = [
        "subject_id",
        "subject_col",
        "stimulus_id",
        "event_index_0based",
        "emg_file",
        "emg_begin_raw",
        "valence_score",
        "arousal_score",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Trial index missing columns: {missing}")

    df = df.copy()
    df["subject_id"] = df["subject_id"].astype(int)
    if args.limit_rows is not None:
        df = df.head(args.limit_rows).copy()
    df = df.reset_index(drop=True)

    feature_rows = []
    index_rows = []
    issues = []
    h5_cache: dict[str, h5py.File] = {}
    feature_columns = None

    print("Building expanded ROCA EMG feature cache")
    print(f"trial_index: {args.trial_index}")
    print(f"rows selected: {len(df)}")

    try:
        for i, row in df.iterrows():
            emg_path = str(row["emg_file"])
            subject_col = str(row["subject_col"])
            event_idx = int(row["event_index_0based"])

            if event_idx <= 0:
                issues.append(f"row {i}: no preceding BSL event")
                continue

            if emg_path not in h5_cache:
                if not Path(emg_path).exists():
                    issues.append(f"row {i}: missing EMG file {emg_path}")
                    continue
                h5_cache[emg_path] = h5py.File(emg_path, "r")

            h5 = h5_cache[emg_path]
            if subject_col not in h5:
                issues.append(f"row {i}: missing subject group {subject_col}")
                continue

            group = h5[subject_col]
            data = group["data"]
            begins, ends = read_event_arrays(h5, subject_col)

            bsl_idx = event_idx - 1
            if event_idx >= len(begins) or bsl_idx >= len(begins):
                issues.append(f"row {i}: event index out of range")
                continue

            stim_begin = float(row["emg_begin_raw"])
            bsl_begin = float(begins[bsl_idx])

            try:
                stim = extract_window(data, stim_begin)
                bsl = extract_window(data, bsl_begin)
                names, feats = compute_expanded_features(stim, bsl, FS)
            except Exception as exc:
                issues.append(f"row {i}: extraction/features failed: {exc}")
                continue

            if feature_columns is None:
                feature_columns = names
                print(f"feature_dim: {len(feature_columns)}")
            elif names != feature_columns:
                raise ValueError("Feature column mismatch across rows.")

            feature_rows.append(feats)

            index_rows.append({
                "cache_row": len(feature_rows) - 1,
                "source_trial_index_row": int(i),
                "subject_id": int(row["subject_id"]),
                "subject_col": subject_col,
                "stimulus_id": str(row["stimulus_id"]),
                "event_index_0based": int(event_idx),
                "bsl_event_index_0based": int(bsl_idx),
                "emg_file": emg_path,
                "emg_begin_raw": stim_begin,
                "bsl_emg_begin_raw": bsl_begin,
                "valence_score": row["valence_score"],
                "arousal_score": row["arousal_score"],
            })

            if len(feature_rows) % 250 == 0:
                print(f"extracted {len(feature_rows)}/{len(df)}")
    finally:
        for h5 in h5_cache.values():
            h5.close()

    if not feature_rows:
        raise RuntimeError("No feature rows extracted.")

    x = np.vstack(feature_rows).astype(np.float32)
    idx = pd.DataFrame(index_rows)
    feature_columns = feature_columns or []

    np.save(args.out_npy, x)
    idx.to_csv(args.out_index, index=False)
    args.out_columns.write_text(json.dumps(feature_columns, indent=2), encoding="utf-8")

    feature_nan_count = int(np.isnan(x).sum())
    feature_inf_count = int(np.isinf(x).sum())
    if feature_nan_count:
        issues.append(f"Feature cache has {feature_nan_count} NaN values")
    if feature_inf_count:
        issues.append(f"Feature cache has {feature_inf_count} Inf values")

    report = {
        "status": "PASSED" if not issues else "FAILED",
        "generated_at_utc": pd.Timestamp.now("UTC").isoformat(),
        "inputs": {
            "trial_index": str(args.trial_index),
        },
        "outputs": {
            "feature_npy": str(args.out_npy),
            "feature_index_csv": str(args.out_index),
            "feature_columns_json": str(args.out_columns),
            "report_md": str(args.out_md),
            "report_json": str(args.out_json),
        },
        "counts": {
            "selected_rows": int(len(df)),
            "extracted_rows": int(len(idx)),
            "subjects": int(idx["subject_id"].nunique()),
            "stimuli": int(idx["stimulus_id"].nunique()),
            "feature_dim": int(x.shape[1]),
            "cache_file_size_bytes": int(args.out_npy.stat().st_size),
            "cache_file_size_human": file_size_human(args.out_npy.stat().st_size),
        },
        "feature_groups": [
            "raw STIM statistics per channel",
            "raw BSL statistics per channel",
            "STIM minus BSL mean statistics per channel",
            "absolute activation delta statistics",
            "BSL-z-scored STIM statistics",
            "rectified/smoothed envelope features",
            "burst features using BSL-derived threshold",
            "1-second temporal-bin features",
            "frequency-domain bandpower features",
            "channel interaction/asymmetry features",
        ],
        "diagnostics": {
            "feature_nan_count": feature_nan_count,
            "feature_inf_count": feature_inf_count,
            "feature_abs_max": safe_float(np.max(np.abs(x))),
            "feature_mean_abs": safe_float(np.mean(np.abs(x))),
            "elapsed_sec": safe_float(time.perf_counter() - t0),
        },
        "feature_stats_preview": feature_stats_preview(x, feature_columns, limit=40),
        "issues": issues,
    }

    args.out_json.write_text(json.dumps(clean_json(report), indent=2, ensure_ascii=False), encoding="utf-8")
    write_md(report, args.out_md)

    print(f"Wrote: {args.out_npy}")
    print(f"Wrote: {args.out_index}")
    print(f"Wrote: {args.out_columns}")
    print(f"Wrote: {args.out_md}")
    print(f"Wrote: {args.out_json}")
    print(f"Status: {report['status']}")
    print(f"Rows extracted: {len(idx)} / {len(df)}")
    print(f"Feature dim: {x.shape[1]}")
    print(f"Cache size: {report['counts']['cache_file_size_human']}")
    print(f"Elapsed: {report['diagnostics']['elapsed_sec']:.2f}s")
    print(f"Issues: {len(issues)}")

    return 0 if report["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
