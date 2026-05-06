#!/usr/bin/env python3
"""Audit DEAP preprocessed Python modalities.

This script performs a non-training audit of the local DEAP
data_preprocessed_python folder.

It checks expected subject files, shapes, EEG/peripheral channel mapping,
DEAP EMG availability, per-channel finite/statistical sanity, and
trial/window-level label counts.
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
DEFAULT_OUT_MD = ROOT / "docs" / "deap_preprocessed_full_modality_audit.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "deap_preprocessed_full_modality_audit.json"

TRIALS_PER_SUBJECT = 40
CHANNELS = 40
SAMPLES_TOTAL = 8064
BASELINE_SAMPLES = 384
STIMULUS_SAMPLES = 7680
WINDOW_SAMPLES = 640
WINDOWS_PER_TRIAL = 12
SOURCE_FS = 128.0

LABEL_COLUMNS = ["valence", "arousal", "dominance", "liking"]

CHANNEL_MAP = [
    (1, "Fp1", "EEG"), (2, "AF3", "EEG"), (3, "F3", "EEG"), (4, "F7", "EEG"),
    (5, "FC5", "EEG"), (6, "FC1", "EEG"), (7, "C3", "EEG"), (8, "T7", "EEG"),
    (9, "CP5", "EEG"), (10, "CP1", "EEG"), (11, "P3", "EEG"), (12, "P7", "EEG"),
    (13, "PO3", "EEG"), (14, "O1", "EEG"), (15, "Oz", "EEG"), (16, "Pz", "EEG"),
    (17, "Fp2", "EEG"), (18, "AF4", "EEG"), (19, "Fz", "EEG"), (20, "F4", "EEG"),
    (21, "F8", "EEG"), (22, "FC6", "EEG"), (23, "FC2", "EEG"), (24, "Cz", "EEG"),
    (25, "C4", "EEG"), (26, "T8", "EEG"), (27, "CP6", "EEG"), (28, "CP2", "EEG"),
    (29, "P4", "EEG"), (30, "P8", "EEG"), (31, "PO4", "EEG"), (32, "O2", "EEG"),
    (33, "hEOG", "EOG"), (34, "vEOG", "EOG"), (35, "zEMG", "EMG"), (36, "tEMG", "EMG"),
    (37, "GSR", "GSR"), (38, "Respiration_belt", "RESP"), (39, "Plethysmograph", "PLET"),
    (40, "Temperature", "TEMP"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deap-dir", type=Path, default=DEFAULT_DEAP_DIR)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--limit-subjects", type=int, default=None)
    return parser.parse_args()


def load_deap_dat(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        return pickle.load(f, encoding="latin1")


def subject_id_from_file(path: Path) -> int:
    stem = path.stem
    if not (len(stem) == 3 and stem.startswith("s") and stem[1:].isdigit()):
        raise ValueError(f"Unexpected DEAP subject filename: {path.name}")
    return int(stem[1:])


def bin_label(score: float, policy: str) -> float:
    if policy == "discard_midpoint":
        if np.isclose(score, 5.0):
            return float("nan")
        return float(score > 5.0)
    if policy == "midpoint_as_low":
        return float(score > 5.0)
    if policy == "midpoint_as_high":
        return float(score >= 5.0)
    raise ValueError(f"Unknown policy: {policy}")


def init_channel_stats() -> dict[str, np.ndarray]:
    return {
        "n": np.zeros(CHANNELS, dtype=np.int64),
        "sum": np.zeros(CHANNELS, dtype=np.float64),
        "sumsq": np.zeros(CHANNELS, dtype=np.float64),
        "min": np.full(CHANNELS, np.inf, dtype=np.float64),
        "max": np.full(CHANNELS, -np.inf, dtype=np.float64),
        "nan": np.zeros(CHANNELS, dtype=np.int64),
        "inf": np.zeros(CHANNELS, dtype=np.int64),
    }


def accumulate_channel_stats(stats: dict[str, np.ndarray], arr: np.ndarray) -> None:
    x = np.asarray(arr)
    if x.ndim != 3 or x.shape[1] != CHANNELS:
        raise ValueError(f"Expected [trials, {CHANNELS}, samples], got {x.shape}")

    ch_values = np.transpose(x, (1, 0, 2)).reshape(CHANNELS, -1)
    finite = np.isfinite(ch_values)

    stats["n"] += finite.sum(axis=1).astype(np.int64)
    stats["nan"] += np.isnan(ch_values).sum(axis=1).astype(np.int64)
    stats["inf"] += np.isinf(ch_values).sum(axis=1).astype(np.int64)

    safe = np.where(finite, ch_values, 0.0).astype(np.float64, copy=False)
    stats["sum"] += safe.sum(axis=1)
    stats["sumsq"] += (safe * safe).sum(axis=1)

    safe_min = np.where(finite, ch_values, np.inf)
    safe_max = np.where(finite, ch_values, -np.inf)
    stats["min"] = np.minimum(stats["min"], safe_min.min(axis=1))
    stats["max"] = np.maximum(stats["max"], safe_max.max(axis=1))


def finish_channel_stats(stats: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, (ch_num, name, modality) in enumerate(CHANNEL_MAP):
        n = int(stats["n"][idx])
        if n > 0:
            mean = float(stats["sum"][idx] / n)
            var = float(max(stats["sumsq"][idx] / n - mean * mean, 0.0))
            std = float(np.sqrt(var))
            min_v = float(stats["min"][idx])
            max_v = float(stats["max"][idx])
        else:
            mean = None
            std = None
            min_v = None
            max_v = None

        rows.append(
            {
                "channel_number_1based": ch_num,
                "channel_index_0based": ch_num - 1,
                "name": name,
                "modality": modality,
                "finite_n": n,
                "nan_count": int(stats["nan"][idx]),
                "inf_count": int(stats["inf"][idx]),
                "mean": mean,
                "std": std,
                "min": min_v,
                "max": max_v,
            }
        )
    return rows


def label_count_frame(labels: np.ndarray, multiplier: int = 1) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for label_i, task in enumerate(LABEL_COLUMNS):
        scores = labels[:, label_i].astype(float)
        out[task] = {}
        for policy in ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]:
            vals = np.asarray([bin_label(float(v), policy) for v in scores], dtype=float)
            counts = {"0": int((vals == 0).sum()) * multiplier, "1": int((vals == 1).sum()) * multiplier}
            if policy == "discard_midpoint":
                counts["discard"] = int(np.isnan(vals).sum()) * multiplier
            out[task][policy] = counts
    return out


def add_nested_counts(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(a))
    for task, policies in b.items():
        out.setdefault(task, {})
        for policy, counts in policies.items():
            out[task].setdefault(policy, {})
            for k, v in counts.items():
                out[task][policy][k] = int(out[task][policy].get(k, 0)) + int(v)
    return out


def summarize_subject_labels(labels: np.ndarray) -> dict[str, Any]:
    return {
        col: {
            "min": float(labels[:, i].min()),
            "max": float(labels[:, i].max()),
            "mean": float(labels[:, i].mean()),
            "eq_5_count": int(np.isclose(labels[:, i], 5.0).sum()),
        }
        for i, col in enumerate(LABEL_COLUMNS)
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    t0 = time.perf_counter()

    expected_names = [f"s{i:02d}.dat" for i in range(1, 33)]
    subject_files_all = sorted(args.deap_dir.glob("s*.dat"))
    subject_files = subject_files_all[: args.limit_subjects] if args.limit_subjects else subject_files_all

    issues: list[str] = []
    warnings: list[str] = []

    if not subject_files_all:
        issues.append(f"No DEAP .dat files found in {args.deap_dir}")

    present_names = [p.name for p in subject_files_all]
    missing = [name for name in expected_names if name not in present_names]
    unexpected = [name for name in present_names if name not in expected_names]
    if missing:
        issues.append(f"Missing expected subject files: {missing}")
    if unexpected:
        warnings.append(f"Unexpected s*.dat files: {unexpected}")

    full_stats = init_channel_stats()
    baseline_stats = init_channel_stats()
    stimulus_stats = init_channel_stats()

    subjects: list[dict[str, Any]] = []
    trial_label_counts: dict[str, Any] = {}
    window_label_counts: dict[str, Any] = {}
    total_trials = 0

    print("Auditing DEAP preprocessed Python modalities")
    print(f"DEAP dir: {args.deap_dir}")
    print(f"subject files selected: {len(subject_files)}")

    for file_i, path in enumerate(subject_files, start=1):
        print(f"[{file_i:03d}/{len(subject_files):03d}] {path.name}")

        try:
            obj = load_deap_dat(path)
        except Exception as exc:
            issues.append(f"{path.name}: failed to load: {exc!r}")
            continue

        data = obj.get("data")
        labels = obj.get("labels")

        item: dict[str, Any] = {
            "file": path.name,
            "subject_id": None,
            "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
            "keys": sorted(obj.keys()),
            "data_shape": list(data.shape) if hasattr(data, "shape") else None,
            "labels_shape": list(labels.shape) if hasattr(labels, "shape") else None,
            "data_dtype": str(data.dtype) if hasattr(data, "dtype") else None,
            "labels_dtype": str(labels.dtype) if hasattr(labels, "dtype") else None,
        }

        try:
            item["subject_id"] = subject_id_from_file(path)
        except Exception as exc:
            issues.append(f"{path.name}: {exc!r}")

        if not isinstance(data, np.ndarray):
            issues.append(f"{path.name}: data is not ndarray")
            subjects.append(item)
            continue
        if not isinstance(labels, np.ndarray):
            issues.append(f"{path.name}: labels is not ndarray")
            subjects.append(item)
            continue

        if tuple(data.shape) != (TRIALS_PER_SUBJECT, CHANNELS, SAMPLES_TOTAL):
            issues.append(f"{path.name}: unexpected data shape {list(data.shape)}")
        if tuple(labels.shape) != (TRIALS_PER_SUBJECT, len(LABEL_COLUMNS)):
            issues.append(f"{path.name}: unexpected labels shape {list(labels.shape)}")

        item["data_nan_count"] = int(np.isnan(data).sum())
        item["data_inf_count"] = int(np.isinf(data).sum())
        item["labels_nan_count"] = int(np.isnan(labels).sum())
        item["labels_inf_count"] = int(np.isinf(labels).sum())
        item["label_summary"] = summarize_subject_labels(labels)

        if item["data_nan_count"] or item["data_inf_count"]:
            issues.append(f"{path.name}: data contains NaN/Inf")
        if item["labels_nan_count"] or item["labels_inf_count"]:
            issues.append(f"{path.name}: labels contains NaN/Inf")

        if tuple(data.shape) == (TRIALS_PER_SUBJECT, CHANNELS, SAMPLES_TOTAL):
            baseline = data[:, :, :BASELINE_SAMPLES]
            stimulus = data[:, :, BASELINE_SAMPLES:]
            if stimulus.shape[-1] != STIMULUS_SAMPLES:
                issues.append(f"{path.name}: stimulus samples after baseline = {stimulus.shape[-1]}")
            accumulate_channel_stats(full_stats, data)
            accumulate_channel_stats(baseline_stats, baseline)
            accumulate_channel_stats(stimulus_stats, stimulus)

        if tuple(labels.shape) == (TRIALS_PER_SUBJECT, len(LABEL_COLUMNS)):
            trial_counts = label_count_frame(labels, multiplier=1)
            window_counts = label_count_frame(labels, multiplier=WINDOWS_PER_TRIAL)
            trial_label_counts = add_nested_counts(trial_label_counts, trial_counts)
            window_label_counts = add_nested_counts(window_label_counts, window_counts)
            total_trials += int(labels.shape[0])

        subjects.append(item)

    full_rows = finish_channel_stats(full_stats)
    baseline_rows = finish_channel_stats(baseline_stats)
    stimulus_rows = finish_channel_stats(stimulus_stats)

    channel_rows: list[dict[str, Any]] = []
    for full, base, stim in zip(full_rows, baseline_rows, stimulus_rows):
        channel_rows.append({**full, "baseline_mean": base["mean"], "baseline_std": base["std"], "stimulus_mean": stim["mean"], "stimulus_std": stim["std"]})

    modality_counts: dict[str, int] = {}
    for _, _, modality in CHANNEL_MAP:
        modality_counts[modality] = modality_counts.get(modality, 0) + 1

    emg_channels = [row for row in channel_rows if row["modality"] == "EMG"]
    status = "PASSED" if not issues else "FAILED"

    return {
        "status": status,
        "generated_at_utc": pd.Timestamp.utcnow().isoformat(),
        "config": {
            "deap_dir": str(args.deap_dir),
            "source": "DEAP data_preprocessed_python",
            "expected_subject_files": "s01.dat ... s32.dat",
            "expected_data_shape_per_subject": [TRIALS_PER_SUBJECT, CHANNELS, SAMPLES_TOTAL],
            "expected_labels_shape_per_subject": [TRIALS_PER_SUBJECT, len(LABEL_COLUMNS)],
            "sampling_rate_hz": SOURCE_FS,
            "baseline_samples": BASELINE_SAMPLES,
            "baseline_sec": BASELINE_SAMPLES / SOURCE_FS,
            "stimulus_samples": STIMULUS_SAMPLES,
            "stimulus_sec": STIMULUS_SAMPLES / SOURCE_FS,
            "window_samples": WINDOW_SAMPLES,
            "window_sec": WINDOW_SAMPLES / SOURCE_FS,
            "windows_per_trial": WINDOWS_PER_TRIAL,
            "limit_subjects": args.limit_subjects,
        },
        "inputs": {
            "deap_dir": str(args.deap_dir),
            "subject_files_total_on_disk": len(subject_files_all),
            "subject_files_selected": len(subject_files),
            "expected_files_present": present_names == expected_names,
            "missing_expected_files": missing,
            "unexpected_files": unexpected,
        },
        "modality_summary": {
            "channel_count": CHANNELS,
            "modality_counts": modality_counts,
            "eeg_channels": [row for row in channel_rows if row["modality"] == "EEG"],
            "peripheral_channels": [row for row in channel_rows if row["modality"] != "EEG"],
            "emg_channels": emg_channels,
            "interpretation": (
                "DEAP preprocessed Python contains 32 EEG channels plus 8 peripheral channels. "
                "The EMG channels available here are zEMG and tEMG, represented as preprocessed "
                "bipolar peripheral channels in the 40-channel matrix, not raw BioSemi EXG pairs."
            ),
        },
        "subjects": subjects,
        "counts": {
            "subjects_selected": len(subject_files),
            "trials": total_trials,
            "expected_windows_if_cached": total_trials * WINDOWS_PER_TRIAL,
        },
        "label_counts": {
            "trial_level": trial_label_counts,
            "window_level_if_12x_replicated": window_label_counts,
        },
        "channel_statistics": channel_rows,
        "issues": issues,
        "warnings": warnings,
        "runtime": {"elapsed_sec": time.perf_counter() - t0},
    }


def format_float(v: Any, digits: int = 4) -> str:
    if v is None:
        return ""
    try:
        return f"{float(v):.{digits}f}"
    except Exception:
        return str(v)


def write_report_md(report: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# DEAP Preprocessed Full Modality Audit")
    lines.append("")
    lines.append("This report was generated by `scripts/26_audit_deap_full_modality.py`.")
    lines.append("")
    lines.append("No model training was performed and no cache was built.")
    lines.append("")
    lines.append("## Status")
    lines.append("")
    lines.append(f"Status: **{report['status']}**")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(report["config"], indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## Input Summary")
    lines.append("")
    inp = report["inputs"]
    lines.append(f"- deap_dir: `{inp['deap_dir']}`")
    lines.append(f"- subject_files_total_on_disk: `{inp['subject_files_total_on_disk']}`")
    lines.append(f"- subject_files_selected: `{inp['subject_files_selected']}`")
    lines.append(f"- expected_files_present: `{str(inp['expected_files_present']).lower()}`")
    lines.append(f"- missing_expected_files: `{inp['missing_expected_files']}`")
    lines.append(f"- unexpected_files: `{inp['unexpected_files']}`")
    lines.append("")
    lines.append("## Modality Summary")
    lines.append("")
    ms = report["modality_summary"]
    lines.append(f"- channel_count: `{ms['channel_count']}`")
    lines.append(f"- modality_counts: `{json.dumps(ms['modality_counts'], sort_keys=True)}`")
    lines.append("")
    lines.append(ms["interpretation"])
    lines.append("")
    lines.append("## Peripheral / EMG Channel Map")
    lines.append("")
    lines.append("| Channel | Index 0-based | Name | Modality | Full std | Baseline std | Stimulus std | NaN | Inf |")
    lines.append("|---:|---:|---|---|---:|---:|---:|---:|---:|")
    for row in ms["peripheral_channels"]:
        lines.append("| " + f"{row['channel_number_1based']} | {row['channel_index_0based']} | {row['name']} | {row['modality']} | {format_float(row['std'])} | {format_float(row['baseline_std'])} | {format_float(row['stimulus_std'])} | {row['nan_count']} | {row['inf_count']} |")
    lines.append("")
    lines.append("## EMG-Specific Summary")
    lines.append("")
    lines.append("| Channel | Name | Meaning in this project | Full mean | Full std | Stimulus std |")
    lines.append("|---:|---|---|---:|---:|---:|")
    for row in ms["emg_channels"]:
        meaning = "facial zygomaticus EMG" if row["name"] == "zEMG" else "trapezius EMG"
        lines.append("| " + f"{row['channel_number_1based']} | {row['name']} | {meaning} | {format_float(row['mean'])} | {format_float(row['std'])} | {format_float(row['stimulus_std'])} |")
    lines.append("")
    lines.append("## Label Counts")
    lines.append("")
    lines.append("### Trial level")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(report["label_counts"]["trial_level"], indent=2))
    lines.append("```")
    lines.append("")
    lines.append("### Window level if each trial is split into 12 windows")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(report["label_counts"]["window_level_if_12x_replicated"], indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## Subject Preview")
    lines.append("")
    lines.append("| File | Size MB | Data shape | Labels shape | Data dtype | Label dtype | Data NaN | Data Inf |")
    lines.append("|---|---:|---|---|---|---|---:|---:|")
    for s in report["subjects"]:
        lines.append("| " + f"{s['file']} | {s['size_mb']} | `{s.get('data_shape')}` | `{s.get('labels_shape')}` | `{s.get('data_dtype')}` | `{s.get('labels_dtype')}` | {s.get('data_nan_count', '')} | {s.get('data_inf_count', '')} |")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- DEAP preprocessed Python is suitable for the next EMG feature-cache smoke if this audit passes.")
    lines.append("- For the proposal mainline, use feature-level EMG first, not raw EMG waveform training.")
    lines.append("- Raw-vs-feature EMG-only should remain an ablation after the feature-cache path is smoke-tested.")
    lines.append("")
    lines.append("## Runtime")
    lines.append("")
    lines.append(f"- elapsed_sec: `{report['runtime']['elapsed_sec']:.2f}`")
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
    lines.append("If this audit passes, build a DEAP EMG feature-cache smoke from the zEMG/tEMG channels.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)

    report = build_report(args)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_report_md(report, args.out_md)

    print(f"Wrote: {args.out_md}")
    print(f"Wrote: {args.out_json}")
    print(f"Status: {report['status']}")
    print(f"Issues: {len(report['issues'])}")
    print(f"Warnings: {len(report['warnings'])}")
    print(f"Elapsed: {report['runtime']['elapsed_sec']:.2f}s")

    return 0 if report["status"] == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
