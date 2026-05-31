#!/usr/bin/env python3
"""
W1D Feature Discriminability Audit for I-DARE.

Read-only with respect to datasets and caches:
- reads existing EEG/EMG cache/index artifacts
- writes only W1D docs-prefixed diagnostic outputs
- performs 0 training runs
- performs no fusion
- uses no DEAP data
- overwrites no cache files
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_EEG_NPY = ROOT / ".cache" / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
DEFAULT_EEG_INDEX = ROOT / ".cache" / "idare_eeg_cache_index_baseline_corrected.csv"
DEFAULT_EMG_NPY = ROOT / ".cache" / "idare_emg_features.npy"
DEFAULT_EMG_INDEX = ROOT / ".cache" / "idare_emg_feature_cache_index.csv"

OUT_REPORT_MD = ROOT / "docs" / "idare_w1d_feat_discrim_report.md"
OUT_REPORT_JSON = ROOT / "docs" / "idare_w1d_feat_discrim_report.json"
OUT_TOP_FEATURES_CSV = ROOT / "docs" / "idare_w1d_feat_discrim_top_features.csv"
OUT_DECISION_MD = ROOT / "docs" / "idare_w1d_feat_discrim_decision_matrix.md"

TASKS = ("valence", "arousal")


@dataclass(frozen=True)
class LabelInfo:
    task: str
    column: str
    policy_note: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run W1D read-only feature discriminability audit.")
    parser.add_argument("--eeg-npy", type=Path, default=DEFAULT_EEG_NPY)
    parser.add_argument("--eeg-index", type=Path, default=DEFAULT_EEG_INDEX)
    parser.add_argument("--emg-npy", type=Path, default=DEFAULT_EMG_NPY)
    parser.add_argument("--emg-index", type=Path, default=DEFAULT_EMG_INDEX)
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--folds", type=int, default=6)
    parser.add_argument("--max-emg-features", type=int, default=5000)
    parser.add_argument("--max-eeg-rows", type=int, default=0, help="0 means all rows.")
    parser.add_argument("--overwrite-docs", action="store_true", help="Allow overwriting W1D docs outputs.")
    return parser.parse_args()


def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"{label} is not a regular file: {path}")


def safe_numeric_label(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    values = values.where(values.isin([0, 1, 0.0, 1.0]))
    return values.astype("float")


def find_subject_column(df: pd.DataFrame) -> str:
    candidates = ["subject_id", "subject", "participant_id", "subject_col", "subj"]
    for col in candidates:
        if col in df.columns:
            return col
    raise KeyError(f"No subject column found. Available columns: {list(df.columns)}")


def find_label_info(df: pd.DataFrame, task: str) -> LabelInfo:
    binary_candidates = [
        f"{task}_midpoint_as_high",
        f"{task}_label_midpoint_as_high",
        f"{task}_label",
        f"{task}_binary",
        f"{task}_label_gt5",
        f"{task}_gt5",
        f"{task}_high",
    ]
    for col in binary_candidates:
        if col in df.columns:
            values = safe_numeric_label(df[col])
            if values.notna().sum() > 0:
                return LabelInfo(task=task, column=col, policy_note="binary column detected")

    score_candidates = [f"{task}_score", f"{task}", f"{task}_rating"]
    for col in score_candidates:
        if col in df.columns:
            scores = pd.to_numeric(df[col], errors="coerce")
            if scores.notna().sum() > 0:
                df[f"{task}_derived_midpoint_as_high"] = np.where(scores >= 5.0, 1.0, 0.0)
                return LabelInfo(
                    task=task,
                    column=f"{task}_derived_midpoint_as_high",
                    policy_note=f"derived midpoint_as_high from score column {col}",
                )

    raise KeyError(f"No usable label column found for task={task}. Available columns: {list(df.columns)}")


def to_subject_ids(series: pd.Series) -> np.ndarray:
    raw = series.astype(str).str.extract(r"(\d+)", expand=False)
    numeric = pd.to_numeric(raw, errors="coerce")
    if numeric.notna().sum() == len(series):
        return numeric.astype(int).to_numpy()
    cat = pd.Categorical(series.astype(str))
    return cat.codes.astype(int)


def cohen_d_matrix(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    y = y.astype(int)
    mask0 = y == 0
    mask1 = y == 1
    if mask0.sum() < 2 or mask1.sum() < 2:
        return np.full(x.shape[1], np.nan, dtype=np.float64)
    x0 = x[mask0]
    x1 = x[mask1]
    n0 = x0.shape[0]
    n1 = x1.shape[0]
    m0 = np.nanmean(x0, axis=0)
    m1 = np.nanmean(x1, axis=0)
    v0 = np.nanvar(x0, axis=0, ddof=1)
    v1 = np.nanvar(x1, axis=0, ddof=1)
    pooled = np.sqrt(((n0 - 1) * v0 + (n1 - 1) * v1) / max(n0 + n1 - 2, 1))
    with np.errstate(divide="ignore", invalid="ignore"):
        d = (m1 - m0) / pooled
    d[~np.isfinite(d)] = np.nan
    return d.astype(np.float64)


def subject_center(x: np.ndarray, subjects: np.ndarray) -> np.ndarray:
    out = x.copy()
    for sid in np.unique(subjects):
        mask = subjects == sid
        out[mask] = out[mask] - np.nanmean(out[mask], axis=0, keepdims=True)
    return out


def impute_and_standardize(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    med = np.nanmedian(x, axis=0)
    inds = np.where(~np.isfinite(x))
    if inds[0].size:
        x[inds] = np.take(med, inds[1])
    mean = np.mean(x, axis=0)
    std = np.std(x, axis=0)
    std[std < 1e-12] = 1.0
    return (x - mean) / std


def topk_mean_abs(values: np.ndarray, k: int) -> float:
    arr = np.abs(values[np.isfinite(values)])
    if arr.size == 0:
        return math.nan
    k = min(k, arr.size)
    return float(np.mean(np.sort(arr)[-k:]))


def quantile_abs(values: np.ndarray, q: float) -> float:
    arr = np.abs(values[np.isfinite(values)])
    if arr.size == 0:
        return math.nan
    return float(np.quantile(arr, q))


def top_indices(values: np.ndarray, k: int) -> list[int]:
    arr = np.abs(values.copy())
    arr[~np.isfinite(arr)] = -np.inf
    valid = np.where(np.isfinite(values))[0]
    if valid.size == 0:
        return []
    k = min(k, valid.size)
    return [int(i) for i in np.argsort(arr)[-k:][::-1]]


def eta_squared_oneway(x: np.ndarray, groups: np.ndarray) -> np.ndarray:
    grand = np.nanmean(x, axis=0)
    total_ss = np.nansum((x - grand) ** 2, axis=0)
    between_ss = np.zeros(x.shape[1], dtype=np.float64)
    for g in np.unique(groups):
        mask = groups == g
        if mask.sum() == 0:
            continue
        group_mean = np.nanmean(x[mask], axis=0)
        between_ss += mask.sum() * ((group_mean - grand) ** 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        eta = between_ss / total_ss
    eta[~np.isfinite(eta)] = np.nan
    return eta


def jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return math.nan
    union = len(a | b)
    if union == 0:
        return math.nan
    return len(a & b) / union


def make_subject_folds(subjects: np.ndarray, n_folds: int) -> list[np.ndarray]:
    unique = np.array(sorted(np.unique(subjects).tolist()), dtype=int)
    if unique.size == 0:
        return []
    n_folds = max(1, min(n_folds, unique.size))
    rng = np.random.default_rng(20260511)
    shuffled = unique.copy()
    rng.shuffle(shuffled)
    return [chunk.astype(int) for chunk in np.array_split(shuffled, n_folds)]


def fold_top_feature_stability(x, y, subjects, global_top, n_folds, top_k) -> dict[str, Any]:
    folds = make_subject_folds(subjects, n_folds)
    fold_sets: list[set[int]] = []
    for fold_subjects in folds:
        heldout = set(int(v) for v in fold_subjects.tolist())
        train_mask = np.array([int(s) not in heldout for s in subjects], dtype=bool)
        if train_mask.sum() < 4:
            continue
        if len(np.unique(y[train_mask])) < 2:
            continue
        d = cohen_d_matrix(x[train_mask], y[train_mask])
        fold_sets.append(set(top_indices(d, top_k)))

    global_set = set(global_top)
    vs_global = [jaccard(s, global_set) for s in fold_sets if s]
    pairwise = []
    for i in range(len(fold_sets)):
        for j in range(i + 1, len(fold_sets)):
            pairwise.append(jaccard(fold_sets[i], fold_sets[j]))

    return {
        "folds_requested": int(n_folds),
        "folds_usable": int(len(fold_sets)),
        "top_k": int(top_k),
        "mean_jaccard_vs_global": float(np.nanmean(vs_global)) if vs_global else math.nan,
        "mean_pairwise_jaccard": float(np.nanmean(pairwise)) if pairwise else math.nan,
    }


def within_subject_signal(x, y, subjects, top_k) -> dict[str, Any]:
    vals = []
    usable_subjects = 0
    for sid in np.unique(subjects):
        mask = subjects == sid
        if mask.sum() < 4:
            continue
        if len(np.unique(y[mask])) < 2:
            continue
        d = cohen_d_matrix(x[mask], y[mask])
        vals.append(topk_mean_abs(d, top_k))
        usable_subjects += 1
    return {
        "usable_subjects": int(usable_subjects),
        "topk_abs_d_mean_across_subjects": float(np.nanmean(vals)) if vals else math.nan,
        "topk_abs_d_median_across_subjects": float(np.nanmedian(vals)) if vals else math.nan,
    }


def eeg_window_features(cache_path: Path, max_rows: int = 0) -> tuple[np.ndarray, list[str]]:
    arr = np.load(cache_path, mmap_mode="r")
    if arr.ndim != 3:
        raise ValueError(f"Unexpected EEG cache ndim={arr.ndim}; expected [N, C, T].")
    n, c, _t = arr.shape
    rows = n if max_rows <= 0 else min(max_rows, n)
    data = np.asarray(arr[:rows], dtype=np.float32)
    chunks = []
    names = []
    funcs = [
        ("mean", lambda z: np.mean(z, axis=2)),
        ("std", lambda z: np.std(z, axis=2)),
        ("rms", lambda z: np.sqrt(np.mean(z * z, axis=2))),
        ("abs_mean", lambda z: np.mean(np.abs(z), axis=2)),
        ("ptp", lambda z: np.ptp(z, axis=2)),
        ("q05", lambda z: np.quantile(z, 0.05, axis=2)),
        ("q95", lambda z: np.quantile(z, 0.95, axis=2)),
        (
            "late_minus_early",
            lambda z: np.mean(z[:, :, int(z.shape[2] * 2 / 3):], axis=2)
            - np.mean(z[:, :, : int(z.shape[2] / 3)], axis=2),
        ),
    ]
    for fname, func in funcs:
        feat = np.asarray(func(data), dtype=np.float64)
        chunks.append(feat)
        for ch in range(c):
            names.append(f"eeg_ch{ch:02d}_{fname}")
    x = np.concatenate(chunks, axis=1)
    return x, names


def emg_features(cache_path: Path, max_features: int) -> tuple[np.ndarray, list[str]]:
    arr = np.load(cache_path, mmap_mode="r")
    x = np.asarray(arr, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    elif x.ndim > 2:
        x = x.reshape(x.shape[0], -1)
    if max_features > 0 and x.shape[1] > max_features:
        x = x[:, :max_features]
    names = [f"emg_f{i:04d}" for i in range(x.shape[1])]
    return x, names


def align_by_cache_row(x: np.ndarray, index_df: pd.DataFrame) -> tuple[np.ndarray, pd.DataFrame]:
    if "cache_row" in index_df.columns:
        rows = pd.to_numeric(index_df["cache_row"], errors="coerce")
        ok = rows.notna() & (rows >= 0) & (rows < x.shape[0])
        df = index_df.loc[ok].copy()
        return x[rows.loc[ok].astype(int).to_numpy()], df.reset_index(drop=True)
    if len(index_df) != x.shape[0]:
        n = min(len(index_df), x.shape[0])
        return x[:n], index_df.iloc[:n].copy().reset_index(drop=True)
    return x, index_df.copy().reset_index(drop=True)


def merge_labels_if_needed(df: pd.DataFrame, fallback_df: pd.DataFrame) -> pd.DataFrame:
    has_any = any(any(col.startswith(task) for col in df.columns) for task in TASKS)
    if has_any:
        return df
    keys = [k for k in ("subject_id", "stimulus_id") if k in df.columns and k in fallback_df.columns]
    if not keys:
        return df
    label_cols = []
    for task in TASKS:
        for col in fallback_df.columns:
            if col.startswith(task):
                label_cols.append(col)
    if not label_cols:
        return df
    label_cols = sorted(set(label_cols))
    small = fallback_df[keys + label_cols].drop_duplicates(keys)
    return df.merge(small, on=keys, how="left")


def diagnose(metrics: dict[str, Any]) -> str:
    cross = metrics["d1_cross_subject"]["subject_centered_topk_abs_d_mean"]
    within = metrics["d2_within_vs_cross"]["within_subject_topk_abs_d_mean"]
    dominance = metrics["d3_subject_vs_label"]["subject_to_label_eta2_ratio_mean"]
    label_eta = metrics["d3_subject_vs_label"]["label_eta2_mean"]

    cross_ok = np.isfinite(cross) and cross >= 0.20
    within_ok = np.isfinite(within) and within >= 0.30
    subject_dominated = np.isfinite(dominance) and dominance >= 5.0
    no_signal = (not cross_ok) and (not within_ok) and (not np.isfinite(label_eta) or label_eta < 0.01)

    if cross_ok and not subject_dominated:
        return "cross_subject_signal_present_model_or_formulation_bottleneck_if_classifiers_are_weak"
    if within_ok and not cross_ok:
        return "within_subject_signal_present_cross_subject_signal_collapses_subject_normalization_or_domain_generalization_priority"
    if subject_dominated and not cross_ok:
        return "subject_dominated_signal_subject_identity_explains_features_more_than_label"
    if no_signal:
        return "no_measurable_label_signal_in_current_features_representation_bottleneck"
    return "mixed_or_weak_signal_requires_controlled_followup"


def analyze_modality_task(modality, x_raw, feature_names, df, task, top_k, n_folds):
    label_info = find_label_info(df, task)
    subject_col = find_subject_column(df)

    labels = safe_numeric_label(df[label_info.column])
    subjects = to_subject_ids(df[subject_col])
    ok = labels.notna().to_numpy()
    x = x_raw[ok]
    y = labels.loc[ok].astype(int).to_numpy()
    subjects = subjects[ok]

    if x.shape[0] != y.shape[0]:
        raise ValueError(f"Shape mismatch for {modality}/{task}: x rows={x.shape[0]} labels={y.shape[0]}")
    if len(np.unique(y)) < 2:
        raise ValueError(f"Only one class available for {modality}/{task}")

    x = impute_and_standardize(x)
    centered = subject_center(x, subjects)

    d_global = cohen_d_matrix(x, y)
    d_centered = cohen_d_matrix(centered, y)

    global_top = top_indices(d_centered, top_k)
    within = within_subject_signal(x, y, subjects, top_k)
    eta_label = eta_squared_oneway(x, y)
    eta_subject = eta_squared_oneway(x, subjects)
    stability = fold_top_feature_stability(centered, y, subjects, global_top, n_folds, top_k)

    label_eta_mean = float(np.nanmean(eta_label))
    subject_eta_mean = float(np.nanmean(eta_subject))
    ratio_mean = subject_eta_mean / label_eta_mean if label_eta_mean > 1e-12 else math.inf

    metrics = {
        "modality": modality,
        "task": task,
        "n_rows": int(x.shape[0]),
        "n_features": int(x.shape[1]),
        "n_subjects": int(len(np.unique(subjects))),
        "label_column": label_info.column,
        "label_policy_note": label_info.policy_note,
        "label_counts": {"0": int(np.sum(y == 0)), "1": int(np.sum(y == 1))},
        "d1_cross_subject": {
            "global_topk_abs_d_mean": topk_mean_abs(d_global, top_k),
            "global_abs_d_p95": quantile_abs(d_global, 0.95),
            "subject_centered_topk_abs_d_mean": topk_mean_abs(d_centered, top_k),
            "subject_centered_abs_d_p95": quantile_abs(d_centered, 0.95),
        },
        "d2_within_vs_cross": {
            "within_subject_usable_subjects": within["usable_subjects"],
            "within_subject_topk_abs_d_mean": within["topk_abs_d_mean_across_subjects"],
            "within_subject_topk_abs_d_median": within["topk_abs_d_median_across_subjects"],
            "within_minus_subject_centered_topk_gap": (
                within["topk_abs_d_mean_across_subjects"] - topk_mean_abs(d_centered, top_k)
                if np.isfinite(within["topk_abs_d_mean_across_subjects"])
                and np.isfinite(topk_mean_abs(d_centered, top_k))
                else math.nan
            ),
        },
        "d3_subject_vs_label": {
            "label_eta2_mean": label_eta_mean,
            "label_eta2_median": float(np.nanmedian(eta_label)),
            "subject_eta2_mean": subject_eta_mean,
            "subject_eta2_median": float(np.nanmedian(eta_subject)),
            "subject_to_label_eta2_ratio_mean": float(ratio_mean),
        },
        "d4_top_feature_stability": stability,
    }
    metrics["diagnosis"] = diagnose(metrics)

    top_rows = []
    for rank, idx in enumerate(global_top, start=1):
        top_rows.append(
            {
                "modality": modality,
                "task": task,
                "rank": rank,
                "feature_index": idx,
                "feature_name": feature_names[idx] if idx < len(feature_names) else f"f{idx}",
                "subject_centered_cohen_d": float(d_centered[idx]) if np.isfinite(d_centered[idx]) else math.nan,
                "abs_subject_centered_cohen_d": float(abs(d_centered[idx])) if np.isfinite(d_centered[idx]) else math.nan,
                "global_cohen_d": float(d_global[idx]) if np.isfinite(d_global[idx]) else math.nan,
                "label_eta2": float(eta_label[idx]) if np.isfinite(eta_label[idx]) else math.nan,
                "subject_eta2": float(eta_subject[idx]) if np.isfinite(eta_subject[idx]) else math.nan,
            }
        )

    return metrics, top_rows


def format_float(v: Any) -> str:
    try:
        fv = float(v)
    except (TypeError, ValueError):
        return str(v)
    if math.isnan(fv):
        return "nan"
    if math.isinf(fv):
        return "inf"
    return f"{fv:.4f}"


def write_outputs(report: dict[str, Any], top_rows: list[dict[str, Any]], overwrite: bool) -> None:
    outputs = [OUT_REPORT_MD, OUT_REPORT_JSON, OUT_TOP_FEATURES_CSV, OUT_DECISION_MD]
    if not overwrite:
        existing = [str(p) for p in outputs if p.exists()]
        if existing:
            raise FileExistsError("Refusing to overwrite existing W1D outputs without --overwrite-docs: " + ", ".join(existing))

    OUT_REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with OUT_TOP_FEATURES_CSV.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "modality",
            "task",
            "rank",
            "feature_index",
            "feature_name",
            "subject_centered_cohen_d",
            "abs_subject_centered_cohen_d",
            "global_cohen_d",
            "label_eta2",
            "subject_eta2",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in top_rows:
            writer.writerow(row)

    lines = []
    lines.append("# W1D Feature Discriminability Report")
    lines.append("")
    lines.append(f"Generated UTC: `{report['generated_at_utc']}`")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("- I-DARE only.")
    lines.append("- EEG and EMG.")
    lines.append("- Arousal and valence.")
    lines.append("- Read-only feature diagnostic.")
    lines.append("- 0 training runs.")
    lines.append("- No fusion.")
    lines.append("- No DEAP.")
    lines.append("- No cache overwrite.")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    for key, value in report["inputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Modality | Task | N | Features | Subjects | Label counts | Centered top-k | Within top-k | Subject/label eta2 ratio | Stability Jaccard | Diagnosis |")
    lines.append("|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|")
    for row in report["results"]:
        counts = row["label_counts"]
        lines.append(
            "| {modality} | {task} | {n} | {f} | {s} | 0={c0}, 1={c1} | {cross} | {within} | {ratio} | {stab} | `{diag}` |".format(
                modality=row["modality"],
                task=row["task"],
                n=row["n_rows"],
                f=row["n_features"],
                s=row["n_subjects"],
                c0=counts["0"],
                c1=counts["1"],
                cross=format_float(row["d1_cross_subject"]["subject_centered_topk_abs_d_mean"]),
                within=format_float(row["d2_within_vs_cross"]["within_subject_topk_abs_d_mean"]),
                ratio=format_float(row["d3_subject_vs_label"]["subject_to_label_eta2_ratio_mean"]),
                stab=format_float(row["d4_top_feature_stability"]["mean_pairwise_jaccard"]),
                diag=row["diagnosis"],
            )
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Cohen's d is computed on diagnostic feature summaries, not by training any classifier.")
    lines.append("- EEG cache windows are converted into simple channel-level summary features for this diagnostic only.")
    lines.append("- EMG uses the existing feature cache directly.")
    lines.append("- Subject-centered effect sizes are used as the main cross-subject signal proxy.")
    lines.append("- This report is diagnostic and cannot be treated as final model performance.")
    OUT_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    dm = []
    dm.append("# W1D Feature Discriminability Decision Matrix")
    dm.append("")
    dm.append("| Condition | Interpretation | Priority |")
    dm.append("|---|---|---|")
    dm.append("| Cross-subject signal present, classifiers weak | Model/formulation/preprocessing bottleneck | Improve formulation before bigger runs |")
    dm.append("| Within-subject signal present, cross-subject signal weak | Subject normalization/domain generalization bottleneck | Prioritize normalization/DG |")
    dm.append("| Subject eta2 dominates label eta2 | Subject identity dominates feature geometry | Control subject effects before training expansion |")
    dm.append("| No measurable label signal | Representation bottleneck | Revisit feature extraction/representation |")
    dm.append("")
    dm.append("## Observed diagnoses")
    dm.append("")
    dm.append("| Modality | Task | Diagnosis |")
    dm.append("|---|---|---|")
    for row in report["results"]:
        dm.append(f"| {row['modality']} | {row['task']} | `{row['diagnosis']}` |")
    OUT_DECISION_MD.write_text("\n".join(dm) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()

    require_file(args.eeg_npy, "baseline-corrected EEG cache")
    require_file(args.eeg_index, "baseline-corrected EEG index")
    require_file(args.emg_npy, "EMG feature cache")
    require_file(args.emg_index, "EMG feature index")

    eeg_df = pd.read_csv(args.eeg_index)
    emg_df = pd.read_csv(args.emg_index)
    emg_df = merge_labels_if_needed(emg_df, eeg_df)

    print("[INFO] W1D feature discriminability audit")
    print("[INFO] No training will be run.")
    print("[INFO] No cache files will be written.")
    print(f"[INFO] EEG cache: {args.eeg_npy}")
    print(f"[INFO] EEG index: {args.eeg_index}")
    print(f"[INFO] EMG cache: {args.emg_npy}")
    print(f"[INFO] EMG index: {args.emg_index}")

    eeg_x, eeg_names = eeg_window_features(args.eeg_npy, max_rows=args.max_eeg_rows)
    eeg_x, eeg_df = align_by_cache_row(eeg_x, eeg_df)

    emg_x, emg_names = emg_features(args.emg_npy, max_features=args.max_emg_features)
    emg_x, emg_df = align_by_cache_row(emg_x, emg_df)

    results = []
    top_rows = []

    for modality, x, names, df in (("EEG", eeg_x, eeg_names, eeg_df), ("EMG", emg_x, emg_names, emg_df)):
        for task in TASKS:
            print(f"[RUN] modality={modality} task={task}")
            metrics, rows = analyze_modality_task(
                modality=modality,
                x_raw=x,
                feature_names=names,
                df=df,
                task=task,
                top_k=args.top_k,
                n_folds=args.folds,
            )
            results.append(metrics)
            top_rows.extend(rows)
            print(
                json.dumps(
                    {
                        "modality": modality,
                        "task": task,
                        "centered_topk_abs_d": metrics["d1_cross_subject"]["subject_centered_topk_abs_d_mean"],
                        "within_topk_abs_d": metrics["d2_within_vs_cross"]["within_subject_topk_abs_d_mean"],
                        "subject_label_eta2_ratio": metrics["d3_subject_vs_label"]["subject_to_label_eta2_ratio_mean"],
                        "diagnosis": metrics["diagnosis"],
                    },
                    sort_keys=True,
                )
            )

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "branch_scope": "W1D Feature Discriminability",
        "training_runs": 0,
        "fusion": False,
        "deap_used": False,
        "cache_overwrite": False,
        "inputs": {
            "eeg_npy": str(args.eeg_npy),
            "eeg_index": str(args.eeg_index),
            "emg_npy": str(args.emg_npy),
            "emg_index": str(args.emg_index),
        },
        "config": {
            "top_k": int(args.top_k),
            "folds": int(args.folds),
            "max_emg_features": int(args.max_emg_features),
            "max_eeg_rows": int(args.max_eeg_rows),
        },
        "results": results,
    }

    write_outputs(report, top_rows, overwrite=args.overwrite_docs)

    print(f"[DONE] wrote {OUT_REPORT_MD}")
    print(f"[DONE] wrote {OUT_REPORT_JSON}")
    print(f"[DONE] wrote {OUT_TOP_FEATURES_CSV}")
    print(f"[DONE] wrote {OUT_DECISION_MD}")


if __name__ == "__main__":
    main()
