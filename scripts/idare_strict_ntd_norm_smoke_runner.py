#!/usr/bin/env python3
"""
Guarded I-DARE strict non-transductive normalization smoke runner.

Default behavior is dry-run/plan-only. Actual execution requires:
  --execute
  --approval-phrase APPROVE_STRICT_NTD_NORM_SMOKE_EXECUTION

Scope:
- I-DARE only
- EEG-only
- arousal-only
- within-subject pairwise affect-preference ranking
- fixed ridge readout
- strict non-transductive normalization only

No raw MATLAB/HDF5 files are loaded.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

APPROVAL_PHRASE = "APPROVE_STRICT_NTD_NORM_SMOKE_EXECUTION"

DEFAULT_CACHE_NPY = ROOT / ".cache" / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
DEFAULT_CACHE_INDEX = ROOT / ".cache" / "idare_eeg_cache_index_baseline_corrected.csv"

DEFAULT_OUT_MD = ROOT / "docs" / "idare_strict_ntd_norm_smoke_report.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "idare_strict_ntd_norm_smoke_report.json"
DEFAULT_OUT_CSV = ROOT / "docs" / "idare_strict_ntd_norm_smoke_runs.csv"

CELLS = (
    "S0_current_no_additional_normalization",
    "S1_train_fold_standard_scaler",
    "S2_train_fold_robust_scaler",
    "S3_train_fold_frozen_quantile_rank_mapper",
)


@dataclass(frozen=True)
class FoldSpec:
    fold_id: int
    train_subjects: list[int]
    test_subjects: list[int]


@dataclass(frozen=True)
class RunSpec:
    run_id: int
    cell: str
    fold: FoldSpec


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-npy", type=Path, default=DEFAULT_CACHE_NPY)
    parser.add_argument("--cache-index", type=Path, default=DEFAULT_CACHE_INDEX)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    parser.add_argument("--folds", type=int, default=6)
    parser.add_argument("--fold-seed", type=int, default=11)
    parser.add_argument("--ridge-alpha", type=float, default=1.0)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--approval-phrase", default="")
    return parser.parse_args()


def require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required file is missing: {path}")


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def count_binary(values: np.ndarray) -> dict[str, int]:
    return {
        "0": int(np.sum(values == 0)),
        "1": int(np.sum(values == 1)),
    }


def binary_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    y_true = np.asarray(y_true, dtype=np.int64)
    y_pred = np.asarray(y_pred, dtype=np.int64)

    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))

    recall0 = safe_div(tn, tn + fp)
    recall1 = safe_div(tp, tp + fn)

    precision0 = safe_div(tn, tn + fn)
    precision1 = safe_div(tp, tp + fp)

    f1_0 = safe_div(2.0 * precision0 * recall0, precision0 + recall0)
    f1_1 = safe_div(2.0 * precision1 * recall1, precision1 + recall1)

    correct = int(np.sum(y_true == y_pred))
    n = int(y_true.size)

    return {
        "n": n,
        "accuracy": safe_div(correct, n),
        "balanced_accuracy": 0.5 * (recall0 + recall1),
        "macro_f1": 0.5 * (f1_0 + f1_1),
        "confusion": {
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "tp": tp,
        },
        "true_counts": count_binary(y_true),
        "pred_counts": count_binary(y_pred),
        "one_class_pred": bool(len(set(int(v) for v in y_pred.tolist())) == 1),
    }


def load_index(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {
        "cache_row",
        "subject_id",
        "stimulus_id",
        "arousal_score",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise KeyError(f"Missing required cache index columns: {missing}")

    df = df.copy()
    df["cache_row"] = df["cache_row"].astype(int)
    df["subject_id"] = df["subject_id"].astype(int)
    df["arousal_score"] = pd.to_numeric(df["arousal_score"], errors="coerce")
    df = df[np.isfinite(df["arousal_score"])].reset_index(drop=True)

    if df.empty:
        raise ValueError("No finite arousal_score rows found.")

    return df


def make_folds(subjects: list[int], n_folds: int, seed: int) -> list[FoldSpec]:
    if n_folds != 6:
        raise ValueError("This strict smoke is fixed to exactly 6 folds.")

    subjects_arr = np.asarray(sorted(set(int(s) for s in subjects)), dtype=np.int64)
    if subjects_arr.size < n_folds:
        raise ValueError(f"Need at least {n_folds} subjects, got {subjects_arr.size}.")

    rng = np.random.default_rng(seed)
    permuted = rng.permutation(subjects_arr)
    chunks = np.array_split(permuted, n_folds)
    all_subjects = set(int(s) for s in subjects_arr.tolist())

    folds: list[FoldSpec] = []
    for fold_id, chunk in enumerate(chunks, start=1):
        test_subjects = sorted(int(s) for s in chunk.tolist())
        train_subjects = sorted(all_subjects - set(test_subjects))
        folds.append(
            FoldSpec(
                fold_id=fold_id,
                train_subjects=train_subjects,
                test_subjects=test_subjects,
            )
        )
    return folds


def build_run_specs(folds: list[FoldSpec]) -> list[RunSpec]:
    specs: list[RunSpec] = []
    run_id = 1
    for cell in CELLS:
        for fold in folds:
            specs.append(RunSpec(run_id=run_id, cell=cell, fold=fold))
            run_id += 1
    if len(specs) != 24:
        raise AssertionError(f"Expected 24 runs, got {len(specs)}.")
    return specs


def build_window_features(cache_npy: Path, df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    cache = np.load(cache_npy, mmap_mode="r")
    if cache.ndim != 3 or tuple(cache.shape[1:]) != (32, 640):
        raise ValueError(f"Unexpected EEG cache shape: {cache.shape}; expected [N, 32, 640].")

    rows = df["cache_row"].to_numpy(dtype=np.int64)
    if int(rows.max()) >= int(cache.shape[0]):
        raise ValueError("cache_row exceeds cache first dimension.")

    x = np.asarray(cache[rows], dtype=np.float32)
    if not np.isfinite(x).all():
        raise ValueError("EEG cache contains non-finite values in selected rows.")

    mean = x.mean(axis=2)
    std = x.std(axis=2)
    rms = np.sqrt(np.mean(np.square(x), axis=2))
    ptp = x.max(axis=2) - x.min(axis=2)
    line_length = np.mean(np.abs(np.diff(x, axis=2)), axis=2)

    blocks = [
        ("mean", mean),
        ("std", std),
        ("rms", rms),
        ("ptp", ptp),
        ("line_length", line_length),
    ]

    features = np.concatenate([block for _, block in blocks], axis=1).astype(np.float64)
    names: list[str] = []
    for block_name, _ in blocks:
        for ch in range(32):
            names.append(f"{block_name}_ch{ch:02d}")

    if features.shape[1] != len(names):
        raise AssertionError("Feature name count does not match feature dimension.")
    if not np.isfinite(features).all():
        raise ValueError("Built EEG features contain non-finite values.")

    return features, names


def fit_transform_train_only(
    cell: str,
    all_features: np.ndarray,
    train_mask: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    train_features = all_features[train_mask]
    if train_features.shape[0] == 0:
        raise ValueError("No training rows available for transform fitting.")

    eps = 1e-8

    if cell == "S0_current_no_additional_normalization":
        return all_features.copy(), {
            "transform": "identity",
            "fit_rows": int(train_features.shape[0]),
            "fitted_on": "none",
        }

    if cell == "S1_train_fold_standard_scaler":
        mean = train_features.mean(axis=0)
        std = train_features.std(axis=0)
        std = np.where(std < eps, 1.0, std)
        out = (all_features - mean) / std
        return out, {
            "transform": "standard_scaler",
            "fit_rows": int(train_features.shape[0]),
            "fitted_on": "training_subject_rows_only",
            "zero_std_features": int(np.sum(train_features.std(axis=0) < eps)),
        }

    if cell == "S2_train_fold_robust_scaler":
        median = np.median(train_features, axis=0)
        q25 = np.quantile(train_features, 0.25, axis=0)
        q75 = np.quantile(train_features, 0.75, axis=0)
        iqr = q75 - q25
        iqr = np.where(iqr < eps, 1.0, iqr)
        out = (all_features - median) / iqr
        return out, {
            "transform": "robust_scaler",
            "fit_rows": int(train_features.shape[0]),
            "fitted_on": "training_subject_rows_only",
            "zero_iqr_features": int(np.sum((q75 - q25) < eps)),
        }

    if cell == "S3_train_fold_frozen_quantile_rank_mapper":
        n_train, n_features = train_features.shape
        out = np.empty_like(all_features, dtype=np.float64)
        for j in range(n_features):
            sorted_train = np.sort(train_features[:, j])
            ranks = np.searchsorted(sorted_train, all_features[:, j], side="right")
            uniform = ranks.astype(np.float64) / float(n_train)
            out[:, j] = (2.0 * uniform) - 1.0
        out = np.clip(out, -1.0, 1.0)
        return out, {
            "transform": "frozen_quantile_rank_mapper",
            "fit_rows": int(train_features.shape[0]),
            "fitted_on": "training_subject_rows_only",
            "output_range": [-1.0, 1.0],
        }

    raise ValueError(f"Unknown cell: {cell}")


def build_pairwise_dataset(
    window_features: np.ndarray,
    df: pd.DataFrame,
    subjects: list[int],
) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    subject_set = set(int(s) for s in subjects)
    pairs: list[np.ndarray] = []
    labels: list[int] = []
    skipped_ties = 0
    subjects_used = 0

    for subject_id in sorted(subject_set):
        local_idx = df.index[df["subject_id"].astype(int) == subject_id].to_numpy(dtype=np.int64)
        if local_idx.size < 2:
            continue

        scores = df.loc[local_idx, "arousal_score"].to_numpy(dtype=np.float64)
        subject_pair_count = 0

        for a in range(local_idx.size):
            for b in range(a + 1, local_idx.size):
                score_a = float(scores[a])
                score_b = float(scores[b])

                if score_a == score_b:
                    skipped_ties += 1
                    continue

                idx_a = int(local_idx[a])
                idx_b = int(local_idx[b])
                diff = window_features[idx_a] - window_features[idx_b]
                absdiff = np.abs(diff)

                pair_ab = np.concatenate([diff, absdiff])
                pair_ba = np.concatenate([-diff, absdiff])

                label_ab = 1 if score_a > score_b else 0
                label_ba = 1 - label_ab

                pairs.append(pair_ab)
                labels.append(label_ab)
                pairs.append(pair_ba)
                labels.append(label_ba)
                subject_pair_count += 2

        if subject_pair_count > 0:
            subjects_used += 1

    if not pairs:
        raise ValueError(f"No pairwise examples built for subjects={subjects}.")

    x_pair = np.vstack(pairs).astype(np.float64)
    y_pair = np.asarray(labels, dtype=np.int64)

    if not np.isfinite(x_pair).all():
        raise ValueError("Pairwise features contain non-finite values.")
    if len(set(y_pair.tolist())) < 2:
        raise ValueError("Pairwise labels are one-class; cannot train ridge readout.")

    meta = {
        "subjects_requested": int(len(subjects)),
        "subjects_used": int(subjects_used),
        "pairs": int(y_pair.size),
        "skipped_equal_score_unordered_pairs": int(skipped_ties),
        "label_counts": count_binary(y_pair),
        "pair_feature_dim": int(x_pair.shape[1]),
    }
    return x_pair, y_pair, meta


def fit_ridge_binary_classifier(x_train: np.ndarray, y_train: np.ndarray, alpha: float) -> np.ndarray:
    if alpha <= 0:
        raise ValueError("ridge_alpha must be > 0.")

    y_signed = np.where(y_train.astype(np.int64) == 1, 1.0, -1.0)
    ones = np.ones((x_train.shape[0], 1), dtype=np.float64)
    x_aug = np.hstack([ones, x_train])

    penalty = np.eye(x_aug.shape[1], dtype=np.float64) * float(alpha)
    penalty[0, 0] = 0.0

    lhs = x_aug.T @ x_aug + penalty
    rhs = x_aug.T @ y_signed

    try:
        coef = np.linalg.solve(lhs, rhs)
    except np.linalg.LinAlgError:
        coef = np.linalg.pinv(lhs) @ rhs

    return coef.astype(np.float64)


def predict_ridge(coef: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ones = np.ones((x.shape[0], 1), dtype=np.float64)
    x_aug = np.hstack([ones, x])
    score = x_aug @ coef
    pred = (score >= 0.0).astype(np.int64)
    return pred, score.astype(np.float64)


def run_one(
    spec: RunSpec,
    *,
    df: pd.DataFrame,
    base_features: np.ndarray,
    ridge_alpha: float,
) -> dict[str, Any]:
    subject_arr = df["subject_id"].to_numpy(dtype=np.int64)
    train_subject_set = set(spec.fold.train_subjects)
    test_subject_set = set(spec.fold.test_subjects)

    train_mask = np.asarray([int(s) in train_subject_set for s in subject_arr], dtype=bool)
    test_mask = np.asarray([int(s) in test_subject_set for s in subject_arr], dtype=bool)

    if np.any(train_mask & test_mask):
        raise AssertionError("Train/test subject masks overlap.")
    if not train_mask.any() or not test_mask.any():
        raise ValueError("Empty train or test mask.")

    transformed_features, transform_audit = fit_transform_train_only(
        spec.cell,
        base_features,
        train_mask,
    )

    x_train, y_train, train_pair_meta = build_pairwise_dataset(
        transformed_features,
        df,
        spec.fold.train_subjects,
    )
    x_test, y_test, test_pair_meta = build_pairwise_dataset(
        transformed_features,
        df,
        spec.fold.test_subjects,
    )

    coef = fit_ridge_binary_classifier(x_train, y_train, alpha=ridge_alpha)

    train_pred, train_score = predict_ridge(coef, x_train)
    test_pred, test_score = predict_ridge(coef, x_test)

    train_metrics = binary_metrics(y_train, train_pred)
    test_metrics = binary_metrics(y_test, test_pred)

    majority_label = 1 if np.sum(y_train == 1) >= np.sum(y_train == 0) else 0
    majority_pred = np.full_like(y_test, fill_value=majority_label)
    majority_metrics = binary_metrics(y_test, majority_pred)

    result = {
        "run_id": int(spec.run_id),
        "cell": spec.cell,
        "fold_id": int(spec.fold.fold_id),
        "train_subjects": [int(s) for s in spec.fold.train_subjects],
        "test_subjects": [int(s) for s in spec.fold.test_subjects],
        "ridge_alpha": float(ridge_alpha),
        "transform_audit": transform_audit,
        "leakage_audit": {
            "fit_uses_training_subjects_only": True,
            "heldout_subject_statistics_used": False,
            "global_scaler_used": False,
            "per_test_subject_normalization_used": False,
            "threshold_tuning_on_test_fold": False,
            "train_test_subject_overlap": [],
            "train_window_rows": int(train_mask.sum()),
            "test_window_rows": int(test_mask.sum()),
        },
        "train_pair_meta": train_pair_meta,
        "test_pair_meta": test_pair_meta,
        "train_metrics": train_metrics,
        "test_metrics": test_metrics,
        "majority_baseline_on_test": {
            "majority_label_from_train_pairs": int(majority_label),
            **majority_metrics,
        },
        "score_summary": {
            "train_mean": float(np.mean(train_score)),
            "train_std": float(np.std(train_score)),
            "test_mean": float(np.mean(test_score)),
            "test_std": float(np.std(test_score)),
        },
    }
    return result


def aggregate_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cell in CELLS:
        group = [r for r in results if r["cell"] == cell]
        if not group:
            continue

        def vals(metric: str) -> list[float]:
            return [float(r["test_metrics"][metric]) for r in group]

        def majority_vals(metric: str) -> list[float]:
            return [float(r["majority_baseline_on_test"][metric]) for r in group]

        bal = vals("balanced_accuracy")
        macro = vals("macro_f1")
        acc = vals("accuracy")
        maj_bal = majority_vals("balanced_accuracy")

        rows.append(
            {
                "cell": cell,
                "runs": int(len(group)),
                "mean_balanced_accuracy": float(np.mean(bal)),
                "std_balanced_accuracy": float(np.std(bal)),
                "mean_macro_f1": float(np.mean(macro)),
                "std_macro_f1": float(np.std(macro)),
                "mean_accuracy": float(np.mean(acc)),
                "mean_majority_balanced_accuracy": float(np.mean(maj_bal)),
                "mean_delta_vs_majority_balanced_accuracy": float(np.mean(bal) - np.mean(maj_bal)),
                "one_class_prediction_runs": int(sum(1 for r in group if r["test_metrics"]["one_class_pred"])),
            }
        )
    return rows


def write_csv(results: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "run_id",
        "cell",
        "fold_id",
        "test_subjects",
        "test_pairs",
        "test_accuracy",
        "test_balanced_accuracy",
        "test_macro_f1",
        "majority_balanced_accuracy",
        "delta_vs_majority_balanced_accuracy",
        "one_class_pred",
        "tn",
        "fp",
        "fn",
        "tp",
    ]

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            m = r["test_metrics"]
            maj = r["majority_baseline_on_test"]
            conf = m["confusion"]
            writer.writerow(
                {
                    "run_id": r["run_id"],
                    "cell": r["cell"],
                    "fold_id": r["fold_id"],
                    "test_subjects": " ".join(str(s) for s in r["test_subjects"]),
                    "test_pairs": r["test_pair_meta"]["pairs"],
                    "test_accuracy": m["accuracy"],
                    "test_balanced_accuracy": m["balanced_accuracy"],
                    "test_macro_f1": m["macro_f1"],
                    "majority_balanced_accuracy": maj["balanced_accuracy"],
                    "delta_vs_majority_balanced_accuracy": m["balanced_accuracy"] - maj["balanced_accuracy"],
                    "one_class_pred": m["one_class_pred"],
                    "tn": conf["tn"],
                    "fp": conf["fp"],
                    "fn": conf["fn"],
                    "tp": conf["tp"],
                }
            )


def fmt(value: float) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "nan"
    return f"{float(value):.4f}"


def write_reports(report: dict[str, Any], out_md: Path, out_json: Path, out_csv: Path) -> None:
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(report["results"], out_csv)

    lines: list[str] = []
    lines.append("# I-DARE Strict NTD Normalization Smoke Report")
    lines.append("")
    lines.append("Status: `executed`")
    lines.append("")
    lines.append("This is a smoke-level strict non-transductive normalization check, not a final LOSO claim.")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("- I-DARE only")
    lines.append("- EEG-only")
    lines.append("- arousal-only")
    lines.append("- within-subject pairwise affect-preference ranking")
    lines.append("- fixed ridge readout")
    lines.append("- strict non-transductive normalization only")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- cache_npy: `{report['config']['cache_npy']}`")
    lines.append(f"- cache_index: `{report['config']['cache_index']}`")
    lines.append("")
    lines.append("## Aggregate")
    lines.append("")
    lines.append("| Cell | Runs | Mean bal acc | Std bal acc | Mean macro F1 | Mean acc | Majority bal acc | Delta vs majority | One-class runs |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")

    for row in report["aggregate"]:
        lines.append(
            "| {cell} | {runs} | {ba} | {ba_std} | {mf1} | {acc} | {maj} | {delta} | {one} |".format(
                cell=row["cell"],
                runs=row["runs"],
                ba=fmt(row["mean_balanced_accuracy"]),
                ba_std=fmt(row["std_balanced_accuracy"]),
                mf1=fmt(row["mean_macro_f1"]),
                acc=fmt(row["mean_accuracy"]),
                maj=fmt(row["mean_majority_balanced_accuracy"]),
                delta=fmt(row["mean_delta_vs_majority_balanced_accuracy"]),
                one=row["one_class_prediction_runs"],
            )
        )

    lines.append("")
    lines.append("## Per-run Summary")
    lines.append("")
    lines.append("| Run | Cell | Fold | Test subjects | Test pairs | Bal acc | Macro F1 | Acc | Delta vs majority | One-class |")
    lines.append("|---:|---|---:|---|---:|---:|---:|---:|---:|---|")

    for r in report["results"]:
        m = r["test_metrics"]
        maj = r["majority_baseline_on_test"]
        delta = float(m["balanced_accuracy"]) - float(maj["balanced_accuracy"])
        lines.append(
            "| {run_id} | {cell} | {fold} | {subjects} | {pairs} | {ba} | {mf1} | {acc} | {delta} | {one} |".format(
                run_id=r["run_id"],
                cell=r["cell"],
                fold=r["fold_id"],
                subjects=" ".join(str(s) for s in r["test_subjects"]),
                pairs=r["test_pair_meta"]["pairs"],
                ba=fmt(m["balanced_accuracy"]),
                mf1=fmt(m["macro_f1"]),
                acc=fmt(m["accuracy"]),
                delta=fmt(delta),
                one=str(m["one_class_pred"]).lower(),
            )
        )

    lines.append("")
    lines.append("## Leakage Guard Summary")
    lines.append("")
    lines.append("- Transform fitting uses training-subject rows only.")
    lines.append("- Held-out/test-subject feature statistics are not fitted.")
    lines.append("- No global scaler is used.")
    lines.append("- No per-test-subject normalization is used.")
    lines.append("- No threshold tuning is performed on test folds.")
    lines.append("- Test arousal scores are used only as evaluation labels for held-out pairwise comparisons.")
    lines.append("")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()

    require_file(args.cache_npy)
    require_file(args.cache_index)

    df = load_index(args.cache_index)
    subjects = sorted(int(s) for s in df["subject_id"].unique().tolist())
    folds = make_folds(subjects, args.folds, args.fold_seed)
    run_specs = build_run_specs(folds)

    plan = {
        "status": "dry_run_plan_only" if not args.execute else "execution_requested",
        "cache_npy": str(args.cache_npy),
        "cache_index": str(args.cache_index),
        "subjects": len(subjects),
        "folds": args.folds,
        "fold_seed": args.fold_seed,
        "ridge_alpha": args.ridge_alpha,
        "cells": list(CELLS),
        "planned_runs": len(run_specs),
        "outputs": {
            "md": str(args.out_md),
            "json": str(args.out_json),
            "csv": str(args.out_csv),
        },
        "execution_guard": {
            "execute_flag": bool(args.execute),
            "approval_phrase_matches": args.approval_phrase == APPROVAL_PHRASE,
        },
    }

    if not args.execute:
        print(json.dumps(plan, indent=2, sort_keys=True))
        print("[DRY-RUN] No smoke experiment executed. Add --execute and the approval phrase only after review.")
        return 0

    if args.approval_phrase != APPROVAL_PHRASE:
        raise PermissionError("Execution blocked: missing or incorrect approval phrase.")

    base_features, feature_names = build_window_features(args.cache_npy, df)

    results: list[dict[str, Any]] = []
    for spec in run_specs:
        print(f"[RUN] {spec.run_id:02d}/24 cell={spec.cell} fold={spec.fold.fold_id}", flush=True)
        result = run_one(
            spec,
            df=df,
            base_features=base_features,
            ridge_alpha=args.ridge_alpha,
        )
        results.append(result)
        m = result["test_metrics"]
        print(
            json.dumps(
                {
                    "run_id": result["run_id"],
                    "cell": result["cell"],
                    "fold": result["fold_id"],
                    "balanced_accuracy": m["balanced_accuracy"],
                    "macro_f1": m["macro_f1"],
                    "accuracy": m["accuracy"],
                    "one_class_pred": m["one_class_pred"],
                },
                sort_keys=True,
            ),
            flush=True,
        )

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "executed",
        "config": {
            "cache_npy": str(args.cache_npy),
            "cache_index": str(args.cache_index),
            "folds": int(args.folds),
            "fold_seed": int(args.fold_seed),
            "ridge_alpha": float(args.ridge_alpha),
            "task": "arousal",
            "modality": "EEG",
            "dataset": "I-DARE",
            "formulation": "within_subject_pairwise_affect_preference_ranking_v1",
            "feature_blocks": [
                "per_channel_mean",
                "per_channel_std",
                "per_channel_rms",
                "per_channel_peak_to_peak",
                "per_channel_line_length",
            ],
            "window_feature_dim": int(base_features.shape[1]),
            "pair_feature_dim": int(base_features.shape[1] * 2),
            "feature_names": feature_names,
        },
        "aggregate": aggregate_results(results),
        "results": results,
    }

    write_reports(report, args.out_md, args.out_json, args.out_csv)

    print(f"[DONE] wrote {args.out_md}")
    print(f"[DONE] wrote {args.out_json}")
    print(f"[DONE] wrote {args.out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
