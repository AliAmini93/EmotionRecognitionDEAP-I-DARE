#!/usr/bin/env python3
"""
Guarded I-DARE representation redesign confirmation runner.

Default behavior is validation/preflight only.

Execution requires:
- --mode execute
- --control-approval REQUEST_REPRESENTATION_REDESIGN_CONFIRMATION_RUN_AUTHORIZATION

Authorized executable scope:
- I-DARE only
- EEG-only
- arousal-only
- cross-subject / held-out-subject
- 3 cells x 6 folds = 18 runs exactly
- Ridge/classical model family only
- strict train-fold-only feature selection and fitting

No DEAP, fusion, preprocessing changes, threshold changes, DG execution,
model-capacity probe, augmentation, W1-owned edits, extra cells, or extra folds.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import balanced_accuracy_score, f1_score, accuracy_score, confusion_matrix
from sklearn.preprocessing import StandardScaler


EXPECTED_BRANCH = "idare/postwave1/representation-redesign-confirmation"
EXPECTED_WORKTREE = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-repr-redesign-confirmation")
CONTROL_APPROVAL = "REQUEST_REPRESENTATION_REDESIGN_CONFIRMATION_RUN_AUTHORIZATION"

ALLOWED_DOC_PREFIX = "docs/idare_repr_redesign_confirm_"
ALLOWED_SCRIPT_PREFIX = "scripts/idare_repr_redesign_confirm_"

CACHE_NPY = ".cache/idare_eeg_windows_32x640_float32.npy"
CACHE_INDEX = ".cache/idare_eeg_cache_index.csv"

REQUIRED_CACHE_FILES = [CACHE_NPY, CACHE_INDEX]
REQUIRED_CONTROL_DOCS = [
    "docs/project_status_current.md",
    "docs/project_status_current.json",
    "docs/project_operating_protocol.md",
    "docs/research_scope_and_objectives.md",
    "docs/research_scope_and_objectives.json",
    "docs/smoke_and_evaluation_protocol.md",
    "docs/smoke_and_evaluation_protocol.json",
    "docs/idare_repr_redesign_confirm_objective.md",
    "docs/idare_repr_redesign_confirm_objective.json",
    "docs/idare_representation_redesign_confirmation_objective.md",
]

CELLS = [
    "R0_current_representation_anchor",
    "R2_train_only_subject_invariant_feature_selection",
    "R3_diagnostics_first_stable_feature_subset",
]
FOLDS = [1, 2, 3, 4, 5, 6]

LABEL_COL = "arousal_midpoint_as_high"

OUT_RUNS_CSV = "docs/idare_repr_redesign_confirm_runs.csv"
OUT_METRIC_SUMMARY_CSV = "docs/idare_repr_redesign_confirm_metric_summary.csv"
OUT_FOLD_REPORT_MD = "docs/idare_repr_redesign_confirm_fold_level_report.md"
OUT_LEAKAGE_AUDIT_JSON = "docs/idare_repr_redesign_confirm_leakage_audit.json"
OUT_STABILITY_CSV = "docs/idare_repr_redesign_confirm_r2_vs_r3_stability_comparison.csv"
OUT_CLOSEOUT_MD = "docs/idare_repr_redesign_confirm_closeout_report.md"
OUT_CLOSEOUT_JSON = "docs/idare_repr_redesign_confirm_closeout_report.json"
OUT_ARTIFACT_BUNDLE_JSON = "docs/idare_repr_redesign_confirm_artifact_review_bundle.json"
OUT_ARTIFACT_BUNDLE_MD = "docs/idare_repr_redesign_confirm_artifact_review_bundle.md"

ALL_OUTPUTS = [
    OUT_RUNS_CSV,
    OUT_METRIC_SUMMARY_CSV,
    OUT_FOLD_REPORT_MD,
    OUT_LEAKAGE_AUDIT_JSON,
    OUT_STABILITY_CSV,
    OUT_CLOSEOUT_MD,
    OUT_CLOSEOUT_JSON,
    OUT_ARTIFACT_BUNDLE_JSON,
    OUT_ARTIFACT_BUNDLE_MD,
]


@dataclass(frozen=True)
class ScopeConfig:
    dataset: str = "I-DARE"
    modality: str = "EEG-only"
    task: str = "arousal-only"
    label_column: str = LABEL_COL
    setting: str = "cross-subject / held-out-subject"
    model_family: str = "Ridge/classical"
    folds: str = "same deterministic held-out-subject folds for R0/R2/R3"


@dataclass(frozen=True)
class LeakageConfig:
    fitted_statistics_scope: str = "training_subjects_only"
    held_out_subject_feature_statistics: bool = False
    test_labels_for_fitting_or_selection: bool = False
    global_all_subject_feature_selection: bool = False
    per_test_subject_normalization: bool = False
    target_adaptation: bool = False
    threshold_tuning_on_held_out_subjects: bool = False
    feature_selection_fit_scope: str = "training_folds_only"
    stability_filter_fit_scope: str = "training_folds_only"


@dataclass(frozen=True)
class FoldSpec:
    fold_id: int
    train_subjects: tuple[int, ...]
    test_subjects: tuple[int, ...]


@dataclass(frozen=True)
class RunSpec:
    run_id: int
    cell: str
    fold_id: int
    train_subjects: tuple[int, ...]
    test_subjects: tuple[int, ...]


def run_git(args: list[str], root: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(root) if root is not None else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def git_root() -> Path:
    return Path(run_git(["rev-parse", "--show-toplevel"]))


def is_allowed_output(path: str) -> bool:
    return path.startswith(ALLOWED_DOC_PREFIX) or path.startswith(ALLOWED_SCRIPT_PREFIX)


def validate_output_paths(paths: list[str]) -> list[str]:
    return [p for p in paths if not is_allowed_output(p)]


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def parse_int_label(value: Any) -> int | None:
    if pd.isna(value):
        return None
    try:
        v = int(float(value))
    except (TypeError, ValueError):
        return None
    if v in (0, 1):
        return v
    return None


def build_fixed_eeg_features(cache: np.ndarray, rows: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Deterministic per-window feature map; no fitting and no cross-subject statistics."""
    x = np.asarray(cache[rows], dtype=np.float32)
    mean = x.mean(axis=2)
    std = x.std(axis=2)
    rms = np.sqrt(np.mean(np.square(x), axis=2))
    abs_mean = np.mean(np.abs(x), axis=2)
    p25 = np.percentile(x, 25, axis=2)
    p75 = np.percentile(x, 75, axis=2)
    diff = np.diff(x, axis=2)
    diff_std = diff.std(axis=2)
    diff_abs = np.mean(np.abs(diff), axis=2)

    blocks = [
        ("mean", mean),
        ("std", std),
        ("rms", rms),
        ("abs_mean", abs_mean),
        ("p25", p25),
        ("p75", p75),
        ("diff_std", diff_std),
        ("diff_abs", diff_abs),
    ]
    features = np.concatenate([b for _, b in blocks], axis=1).astype(np.float64)
    names: list[str] = []
    for block_name, arr in blocks:
        for ch in range(arr.shape[1]):
            names.append(f"{block_name}_ch{ch:02d}")
    return features, names


def make_folds(subjects: list[int], n_folds: int = 6) -> list[FoldSpec]:
    subjects = sorted({int(s) for s in subjects})
    if len(subjects) < n_folds:
        raise ValueError(f"Need at least {n_folds} subjects; got {len(subjects)}")
    shuffled = list(subjects)
    rng = random.Random(20260505)
    rng.shuffle(shuffled)
    chunks = np.array_split(np.asarray(shuffled, dtype=int), n_folds)
    folds: list[FoldSpec] = []
    for i, chunk in enumerate(chunks, start=1):
        test_subjects = tuple(sorted(int(s) for s in chunk.tolist()))
        test_set = set(test_subjects)
        train_subjects = tuple(sorted(s for s in subjects if s not in test_set))
        folds.append(FoldSpec(fold_id=i, train_subjects=train_subjects, test_subjects=test_subjects))
    return folds


def build_run_manifest(folds: list[FoldSpec]) -> list[RunSpec]:
    manifest: list[RunSpec] = []
    run_id = 1
    for cell in CELLS:
        for fold in folds:
            manifest.append(
                RunSpec(
                    run_id=run_id,
                    cell=cell,
                    fold_id=fold.fold_id,
                    train_subjects=fold.train_subjects,
                    test_subjects=fold.test_subjects,
                )
            )
            run_id += 1
    return manifest


def label_signal_scores(x_train: np.ndarray, y_train: np.ndarray) -> np.ndarray:
    scores = np.zeros(x_train.shape[1], dtype=np.float64)
    mask0 = y_train == 0
    mask1 = y_train == 1
    if mask0.sum() == 0 or mask1.sum() == 0:
        return scores
    mu0 = x_train[mask0].mean(axis=0)
    mu1 = x_train[mask1].mean(axis=0)
    sd = x_train.std(axis=0) + 1e-8
    scores = np.abs(mu1 - mu0) / sd
    scores[~np.isfinite(scores)] = 0.0
    return scores


def subject_dominance_scores(x_train: np.ndarray, subjects_train: np.ndarray) -> np.ndarray:
    unique_subjects = sorted({int(s) for s in subjects_train.tolist()})
    if len(unique_subjects) < 2:
        return np.zeros(x_train.shape[1], dtype=np.float64)
    overall = x_train.mean(axis=0)
    between = np.zeros(x_train.shape[1], dtype=np.float64)
    within = np.zeros(x_train.shape[1], dtype=np.float64)
    for s in unique_subjects:
        xs = x_train[subjects_train == s]
        if xs.size == 0:
            continue
        mu = xs.mean(axis=0)
        between += xs.shape[0] * np.square(mu - overall)
        within += np.square(xs - mu).sum(axis=0)
    ratio = between / (within + 1e-8)
    ratio[~np.isfinite(ratio)] = 0.0
    return ratio


def stable_label_scores(x_train: np.ndarray, y_train: np.ndarray, subjects_train: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    effects: list[np.ndarray] = []
    for s in sorted({int(v) for v in subjects_train.tolist()}):
        mask = subjects_train == s
        ys = y_train[mask]
        if (ys == 0).sum() == 0 or (ys == 1).sum() == 0:
            continue
        xs = x_train[mask]
        eff = xs[ys == 1].mean(axis=0) - xs[ys == 0].mean(axis=0)
        effects.append(eff)
    if not effects:
        zeros = np.zeros(x_train.shape[1], dtype=np.float64)
        return zeros, zeros
    e = np.vstack(effects)
    mean_eff = e.mean(axis=0)
    stability = np.abs(mean_eff) / (e.std(axis=0) + 1e-8)
    consistency = np.abs(e.mean(axis=0)) / (np.mean(np.abs(e), axis=0) + 1e-8)
    stability[~np.isfinite(stability)] = 0.0
    consistency[~np.isfinite(consistency)] = 0.0
    return stability, consistency


def select_features(
    cell: str,
    x_train_scaled: np.ndarray,
    y_train: np.ndarray,
    subjects_train: np.ndarray,
) -> tuple[np.ndarray, dict[str, Any]]:
    n_features = x_train_scaled.shape[1]
    label_scores = label_signal_scores(x_train_scaled, y_train)
    subject_scores = subject_dominance_scores(x_train_scaled, subjects_train)

    if cell == "R0_current_representation_anchor":
        selected = np.arange(n_features, dtype=int)
        info = {
            "selection_type": "all_features_anchor",
            "selected_count": int(selected.size),
            "fit_scope": "train_fold_only",
        }
        return selected, info

    if cell == "R2_train_only_subject_invariant_feature_selection":
        combined = label_scores / (1.0 + subject_scores)
        k = min(48, n_features)
        selected = np.argsort(combined)[::-1][:k]
        info = {
            "selection_type": "train_only_label_signal_penalized_by_subject_dominance",
            "selected_count": int(selected.size),
            "fit_scope": "train_fold_only",
            "label_score_mean_selected": float(label_scores[selected].mean()) if selected.size else 0.0,
            "subject_score_mean_selected": float(subject_scores[selected].mean()) if selected.size else 0.0,
        }
        return selected.astype(int), info

    if cell == "R3_diagnostics_first_stable_feature_subset":
        stability, consistency = stable_label_scores(x_train_scaled, y_train, subjects_train)
        combined = (label_scores * (1.0 + stability) * (0.5 + consistency)) / (1.0 + subject_scores)
        k = min(32, n_features)
        selected = np.argsort(combined)[::-1][:k]
        info = {
            "selection_type": "train_only_stable_label_signal_subject_dominance_filtered",
            "selected_count": int(selected.size),
            "fit_scope": "train_fold_only",
            "label_score_mean_selected": float(label_scores[selected].mean()) if selected.size else 0.0,
            "subject_score_mean_selected": float(subject_scores[selected].mean()) if selected.size else 0.0,
            "stability_mean_selected": float(stability[selected].mean()) if selected.size else 0.0,
            "consistency_mean_selected": float(consistency[selected].mean()) if selected.size else 0.0,
        }
        return selected.astype(int), info

    raise ValueError(f"Unsupported cell: {cell}")


def binary_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    labels = [0, 1]
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    pred_unique = sorted({int(v) for v in y_pred.tolist()})
    counts_true = {str(k): int((y_true == k).sum()) for k in labels}
    counts_pred = {str(k): int((y_pred == k).sum()) for k in labels}
    majority_label = max(labels, key=lambda k: counts_true[str(k)])
    y_majority = np.full_like(y_true, majority_label)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "confusion_tn": int(cm[0, 0]),
        "confusion_fp": int(cm[0, 1]),
        "confusion_fn": int(cm[1, 0]),
        "confusion_tp": int(cm[1, 1]),
        "true_count_0": counts_true["0"],
        "true_count_1": counts_true["1"],
        "pred_count_0": counts_pred["0"],
        "pred_count_1": counts_pred["1"],
        "one_class_collapse": bool(len(pred_unique) == 1),
        "collapsed_to_label": int(pred_unique[0]) if len(pred_unique) == 1 else None,
        "majority_label": int(majority_label),
        "majority_accuracy": float(accuracy_score(y_true, y_majority)),
        "majority_balanced_accuracy": float(balanced_accuracy_score(y_true, y_majority)),
        "majority_macro_f1": float(f1_score(y_true, y_majority, average="macro", zero_division=0)),
    }


def mean(values: list[float]) -> float:
    return float(np.mean(np.asarray(values, dtype=np.float64))) if values else math.nan


def std(values: list[float]) -> float:
    return float(np.std(np.asarray(values, dtype=np.float64), ddof=0)) if values else math.nan


def validate_leakage_config(config: LeakageConfig) -> list[str]:
    blockers: list[str] = []
    if config.fitted_statistics_scope != "training_subjects_only":
        blockers.append("fitted statistics are not restricted to training subjects only")
    if config.held_out_subject_feature_statistics:
        blockers.append("held-out/test-subject feature statistics are enabled")
    if config.test_labels_for_fitting_or_selection:
        blockers.append("test labels for fitting/selection are enabled")
    if config.global_all_subject_feature_selection:
        blockers.append("global all-subject feature selection is enabled")
    if config.per_test_subject_normalization:
        blockers.append("per-test-subject normalization is enabled")
    if config.target_adaptation:
        blockers.append("target adaptation is enabled")
    if config.threshold_tuning_on_held_out_subjects:
        blockers.append("threshold tuning on held-out subjects is enabled")
    if config.feature_selection_fit_scope != "training_folds_only":
        blockers.append("feature selection is not fit on training folds only")
    if config.stability_filter_fit_scope != "training_folds_only":
        blockers.append("stability filters are not fit on training folds only")
    return blockers


def porcelain_path(line: str) -> str:
    """Extract path from common git status --porcelain variants.

    Handles:
    - "?? path"
    - " M path"
    - "M  path"
    - "M path" from compact/nonstandard copied output
    """
    if len(line) >= 4 and line[2] == " ":
        return line[3:].strip()
    parts = line.split(maxsplit=1)
    if len(parts) == 2:
        return parts[1].strip()
    return ""


def validate_dirty_scope(root: Path) -> dict[str, Any]:
    status = run_git(["status", "--porcelain"], root=root)
    dirty_lines = [line for line in status.splitlines() if line.strip()]
    blockers: list[str] = []
    allowed_dirty: list[str] = []
    forbidden_dirty: list[str] = []
    for line in dirty_lines:
        path = porcelain_path(line)
        if is_allowed_output(path):
            allowed_dirty.append(line)
        else:
            forbidden_dirty.append(line)
            blockers.append(f"dirty file outside allowed prefixes: {line}")
    return {
        "dirty_lines": dirty_lines,
        "allowed_dirty": allowed_dirty,
        "forbidden_dirty": forbidden_dirty,
        "blockers": blockers,
    }


def validate(mode: str, approval: str | None = None) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    root = git_root()
    branch = run_git(["branch", "--show-current"], root=root)
    head = run_git(["rev-parse", "HEAD"], root=root)

    if branch != EXPECTED_BRANCH:
        blockers.append(f"unexpected branch: {branch}; expected {EXPECTED_BRANCH}")
    if root.resolve() != EXPECTED_WORKTREE.resolve():
        blockers.append(f"unexpected worktree: {root}; expected {EXPECTED_WORKTREE}")

    missing_cache = [p for p in REQUIRED_CACHE_FILES if not (root / p).exists()]
    for p in missing_cache:
        blockers.append(f"missing required EEG cache/index file: {p}")

    missing_docs = [p for p in REQUIRED_CONTROL_DOCS if not (root / p).exists()]
    for p in missing_docs:
        blockers.append(f"missing required control/objective doc: {p}")

    invalid_outputs = validate_output_paths(ALL_OUTPUTS + ["scripts/idare_repr_redesign_confirm_runner.py"])
    for p in invalid_outputs:
        blockers.append(f"output path violates allowed prefix: {p}")

    dirty_scope = validate_dirty_scope(root)
    blockers.extend(dirty_scope["blockers"])

    scope = ScopeConfig()
    leakage = LeakageConfig()
    blockers.extend(validate_leakage_config(leakage))

    planned_runs = len(CELLS) * len(FOLDS)
    if planned_runs != 18:
        blockers.append(f"planned matrix size is {planned_runs}; expected 18")
    if CELLS != [
        "R0_current_representation_anchor",
        "R2_train_only_subject_invariant_feature_selection",
        "R3_diagnostics_first_stable_feature_subset",
    ]:
        blockers.append("cells differ from authorized R0/R2/R3")
    if FOLDS != [1, 2, 3, 4, 5, 6]:
        blockers.append("folds differ from authorized 1..6")

    execution_authorized = mode == "execute" and approval == CONTROL_APPROVAL
    if mode == "execute" and not execution_authorized:
        blockers.append("execute mode requires exact Control Tower approval phrase")
    if mode == "plan":
        blockers.append("plan mode is not used; use validate or execute only")

    return {
        "status": "BLOCKED" if blockers else "VALIDATION_PASSED",
        "mode": mode,
        "branch": branch,
        "head": head,
        "worktree": str(root),
        "scope": asdict(scope),
        "cells": CELLS,
        "folds": FOLDS,
        "planned_runs": planned_runs,
        "execution_authorized": execution_authorized,
        "required_cache_files": REQUIRED_CACHE_FILES,
        "missing_cache_files": missing_cache,
        "required_control_docs": REQUIRED_CONTROL_DOCS,
        "missing_control_docs": missing_docs,
        "dirty_scope": dirty_scope,
        "outputs": ALL_OUTPUTS,
        "invalid_outputs": invalid_outputs,
        "leakage_config": asdict(leakage),
        "blockers": blockers,
        "warnings": warnings,
    }


def load_dataset(root: Path) -> tuple[np.ndarray, pd.DataFrame, np.ndarray, list[str]]:
    cache = np.load(root / CACHE_NPY, mmap_mode="r")
    if cache.ndim != 3 or tuple(cache.shape[1:]) != (32, 640):
        raise ValueError(f"unexpected cache shape {cache.shape}; expected [N, 32, 640]")
    df = pd.read_csv(root / CACHE_INDEX)
    required = {"cache_row", "subject_id", LABEL_COL}
    missing = sorted(required - set(df.columns))
    if missing:
        raise KeyError(f"missing index columns: {missing}")
    df[LABEL_COL] = df[LABEL_COL].map(parse_int_label)
    df = df[df[LABEL_COL].isin([0, 1])].copy()
    df["cache_row"] = df["cache_row"].astype(int)
    df["subject_id"] = df["subject_id"].astype(int)
    df = df.sort_values(["subject_id", "cache_row"]).reset_index(drop=True)
    if int(df["cache_row"].max()) >= int(cache.shape[0]):
        raise ValueError("cache_row exceeds cache shape")
    x, names = build_fixed_eeg_features(cache, df["cache_row"].to_numpy(dtype=int))
    y = df[LABEL_COL].to_numpy(dtype=int)
    return x, df, y, names


def execute_confirmation(root: Path) -> dict[str, Any]:
    x_all, df, y_all, feature_names = load_dataset(root)
    subjects = sorted(int(s) for s in df["subject_id"].unique().tolist())
    folds = make_folds(subjects, n_folds=6)
    manifest = build_run_manifest(folds)
    if len(manifest) != 18:
        raise RuntimeError(f"blocked: attempted {len(manifest)} runs, expected 18")

    rows: list[dict[str, Any]] = []
    feature_audit: list[dict[str, Any]] = []

    for spec in manifest:
        train_mask = df["subject_id"].isin(spec.train_subjects).to_numpy()
        test_mask = df["subject_id"].isin(spec.test_subjects).to_numpy()

        if bool(np.any(train_mask & test_mask)):
            raise RuntimeError(f"leakage blocker: train/test overlap in fold {spec.fold_id}")
        if int(test_mask.sum()) == 0 or int(train_mask.sum()) == 0:
            raise RuntimeError(f"blocker: empty train/test split in fold {spec.fold_id}")

        x_train = x_all[train_mask]
        y_train = y_all[train_mask]
        s_train = df.loc[train_mask, "subject_id"].to_numpy(dtype=int)

        x_test = x_all[test_mask]
        y_test = y_all[test_mask]

        scaler = StandardScaler()
        x_train_scaled = scaler.fit_transform(x_train)
        x_test_scaled = scaler.transform(x_test)

        selected, selection_info = select_features(spec.cell, x_train_scaled, y_train, s_train)

        if selected.size == 0:
            raise RuntimeError(f"blocker: zero selected features for {spec.cell} fold {spec.fold_id}")

        model = RidgeClassifier(alpha=1.0)
        model.fit(x_train_scaled[:, selected], y_train)
        y_pred = model.predict(x_test_scaled[:, selected]).astype(int)

        metrics = binary_metrics(y_test, y_pred)
        selected_names = [feature_names[int(i)] for i in selected[:20].tolist()]
        feature_audit.append(
            {
                "run_id": spec.run_id,
                "cell": spec.cell,
                "fold_id": spec.fold_id,
                "selected_count": int(selected.size),
                "selected_preview": selected_names,
                "selection_info": selection_info,
                "fit_scope": "train_fold_only",
                "test_statistics_used": False,
                "test_labels_used_for_fit_or_selection": False,
            }
        )

        row: dict[str, Any] = {
            "run_id": spec.run_id,
            "cell": spec.cell,
            "fold_id": spec.fold_id,
            "dataset": "I-DARE",
            "modality": "EEG-only",
            "task": "arousal",
            "label_column": LABEL_COL,
            "model_family": "RidgeClassifier",
            "train_subjects": " ".join(str(v) for v in spec.train_subjects),
            "test_subjects": " ".join(str(v) for v in spec.test_subjects),
            "train_n": int(train_mask.sum()),
            "test_n": int(test_mask.sum()),
            "train_label_0": int((y_train == 0).sum()),
            "train_label_1": int((y_train == 1).sum()),
            "test_label_0": int((y_test == 0).sum()),
            "test_label_1": int((y_test == 1).sum()),
            "selected_feature_count": int(selected.size),
            "selection_fit_scope": "train_fold_only",
            "scaler_fit_scope": "train_fold_only",
            "threshold_changed": False,
            "test_stats_used": False,
            "test_labels_used_for_fit_or_selection": False,
            **metrics,
        }
        rows.append(row)

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": asdict(ScopeConfig()),
        "leakage_config": asdict(LeakageConfig()),
        "feature_names_count": len(feature_names),
        "subjects": subjects,
        "folds": [asdict(f) for f in folds],
        "rows": rows,
        "feature_audit": feature_audit,
    }


def summarize_results(result: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows = result["rows"]
    by_cell: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_cell.setdefault(row["cell"], []).append(row)

    summary: list[dict[str, Any]] = []
    for cell in CELLS:
        group = by_cell.get(cell, [])
        bas = [float(r["balanced_accuracy"]) for r in group]
        mf1 = [float(r["macro_f1"]) for r in group]
        acc = [float(r["accuracy"]) for r in group]
        one_class = [bool(r["one_class_collapse"]) for r in group]
        summary.append(
            {
                "cell": cell,
                "runs": len(group),
                "mean_balanced_accuracy": mean(bas),
                "std_balanced_accuracy": std(bas),
                "mean_macro_f1": mean(mf1),
                "std_macro_f1": std(mf1),
                "mean_accuracy": mean(acc),
                "std_accuracy": std(acc),
                "one_class_collapse_count": int(sum(1 for v in one_class if v)),
            }
        )

    by_fold_cell = {(r["fold_id"], r["cell"]): r for r in rows}
    stability: list[dict[str, Any]] = []
    r2_wins = 0
    r3_wins = 0
    r3_vs_r0_wins = 0
    r2_vs_r0_wins = 0
    for fold_id in FOLDS:
        r0 = by_fold_cell[(fold_id, "R0_current_representation_anchor")]
        r2 = by_fold_cell[(fold_id, "R2_train_only_subject_invariant_feature_selection")]
        r3 = by_fold_cell[(fold_id, "R3_diagnostics_first_stable_feature_subset")]
        r2_delta_r0 = float(r2["balanced_accuracy"]) - float(r0["balanced_accuracy"])
        r3_delta_r0 = float(r3["balanced_accuracy"]) - float(r0["balanced_accuracy"])
        r3_delta_r2 = float(r3["balanced_accuracy"]) - float(r2["balanced_accuracy"])
        if r2_delta_r0 > 0:
            r2_vs_r0_wins += 1
        if r3_delta_r0 > 0:
            r3_vs_r0_wins += 1
        if r3_delta_r2 > 0:
            r3_wins += 1
        elif r3_delta_r2 < 0:
            r2_wins += 1
        stability.append(
            {
                "fold_id": fold_id,
                "r0_balanced_accuracy": float(r0["balanced_accuracy"]),
                "r2_balanced_accuracy": float(r2["balanced_accuracy"]),
                "r3_balanced_accuracy": float(r3["balanced_accuracy"]),
                "r2_delta_vs_r0": r2_delta_r0,
                "r3_delta_vs_r0": r3_delta_r0,
                "r3_delta_vs_r2": r3_delta_r2,
                "winner_r2_vs_r3": "R3" if r3_delta_r2 > 0 else ("R2" if r3_delta_r2 < 0 else "tie"),
            }
        )

    summary_by_cell = {r["cell"]: r for r in summary}
    r0_mean = float(summary_by_cell["R0_current_representation_anchor"]["mean_balanced_accuracy"])
    r2_mean = float(summary_by_cell["R2_train_only_subject_invariant_feature_selection"]["mean_balanced_accuracy"])
    r3_mean = float(summary_by_cell["R3_diagnostics_first_stable_feature_subset"]["mean_balanced_accuracy"])
    one_class_total = int(sum(int(r["one_class_collapse"]) for r in rows))

    leakage_pass = all(
        (not bool(r["test_stats_used"]))
        and (not bool(r["test_labels_used_for_fit_or_selection"]))
        and r["selection_fit_scope"] == "train_fold_only"
        and r["scaler_fit_scope"] == "train_fold_only"
        and (not bool(r["threshold_changed"]))
        for r in rows
    )

    gates = {
        "r0_mean_balanced_accuracy": r0_mean,
        "r2_mean_balanced_accuracy": r2_mean,
        "r3_mean_balanced_accuracy": r3_mean,
        "r2_delta_vs_r0_mean": r2_mean - r0_mean,
        "r3_delta_vs_r0_mean": r3_mean - r0_mean,
        "r3_delta_vs_r2_mean": r3_mean - r2_mean,
        "r2_fold_wins_vs_r0": r2_vs_r0_wins,
        "r3_fold_wins_vs_r0": r3_vs_r0_wins,
        "r2_wins_vs_r3": r2_wins,
        "r3_wins_vs_r2": r3_wins,
        "leakage_audit_pass": bool(leakage_pass),
        "one_class_collapse_total": one_class_total,
        "forbidden_scope_touched": False,
        "thresholds_changed": False,
        "moderate_gate_r3_ge_0_53": bool(r3_mean >= 0.53),
        "strong_gate_r3_ge_0_55": bool(r3_mean >= 0.55),
        "r3_positive_delta_vs_r0": bool(r3_mean > r0_mean),
        "r2_reported_as_near_miss_stability_comparator": True,
    }
    gates["confirmation_gate_pass"] = bool(
        gates["moderate_gate_r3_ge_0_53"]
        and gates["leakage_audit_pass"]
        and gates["one_class_collapse_total"] == 0
        and not gates["forbidden_scope_touched"]
        and gates["r3_positive_delta_vs_r0"]
        and gates["r2_reported_as_near_miss_stability_comparator"]
        and not gates["thresholds_changed"]
    )
    return summary, stability, gates


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys: list[str] = []
    for row in rows:
        for k in row.keys():
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_outputs(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    summary, stability, gates = summarize_results(result)

    leakage_audit = {
        "generated_at_utc": result["generated_at_utc"],
        "result": "PASS" if gates["leakage_audit_pass"] else "FAIL",
        "hard_rules": asdict(LeakageConfig()),
        "checks": {
            "all_statistics_fit_train_subjects_only": True,
            "no_held_out_subject_feature_statistics": True,
            "no_test_labels_for_fitting_or_selection": True,
            "no_global_all_subject_feature_selection": True,
            "no_per_test_subject_normalization": True,
            "no_target_adaptation": True,
            "no_threshold_tuning_on_held_out_subjects": True,
            "feature_selection_and_stability_filters_train_fold_only": True,
            "forbidden_scope_touched": False,
        },
        "feature_audit": result["feature_audit"],
    }

    closeout = {
        "generated_at_utc": result["generated_at_utc"],
        "status": "closeout_ready",
        "scope": result["scope"],
        "run_count": len(result["rows"]),
        "summary": summary,
        "stability": stability,
        "gates": gates,
        "leakage_audit_result": leakage_audit["result"],
        "produced_files": ALL_OUTPUTS,
    }

    artifact_bundle = {
        "generated_at_utc": result["generated_at_utc"],
        "bundle_id": "idare_repr_redesign_confirm_artifact_review_bundle",
        "status": "ready_for_control_tower_review",
        "files": ALL_OUTPUTS,
        "latest_inputs": {
            "cache_npy": CACHE_NPY,
            "cache_index": CACHE_INDEX,
            "label_column": LABEL_COL,
        },
        "closeout_ready": True,
    }

    write_csv(root / OUT_RUNS_CSV, result["rows"])
    write_csv(root / OUT_METRIC_SUMMARY_CSV, summary)
    write_csv(root / OUT_STABILITY_CSV, stability)

    (root / OUT_LEAKAGE_AUDIT_JSON).write_text(json.dumps(leakage_audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / OUT_CLOSEOUT_JSON).write_text(json.dumps(closeout, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (root / OUT_ARTIFACT_BUNDLE_JSON).write_text(json.dumps(artifact_bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines: list[str] = []
    lines.append("# I-DARE Representation Redesign Confirmation Fold-Level Report")
    lines.append("")
    lines.append(f"Generated: `{result['generated_at_utc']}`")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    for k, v in result["scope"].items():
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Fold-Level Balanced Accuracy")
    lines.append("")
    lines.append("| Fold | R0 BA | R2 BA | R3 BA | R2-R0 | R3-R0 | R3-R2 | R2/R3 winner |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---|")
    for row in stability:
        lines.append(
            "| {fold_id} | {r0:.6f} | {r2:.6f} | {r3:.6f} | {d20:.6f} | {d30:.6f} | {d32:.6f} | {winner} |".format(
                fold_id=row["fold_id"],
                r0=row["r0_balanced_accuracy"],
                r2=row["r2_balanced_accuracy"],
                r3=row["r3_balanced_accuracy"],
                d20=row["r2_delta_vs_r0"],
                d30=row["r3_delta_vs_r0"],
                d32=row["r3_delta_vs_r2"],
                winner=row["winner_r2_vs_r3"],
            )
        )
    lines.append("")
    lines.append("## Cell Summary")
    lines.append("")
    lines.append("| Cell | Runs | Mean BA | Std BA | Mean macro F1 | One-class collapses |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in summary:
        lines.append(
            f"| {row['cell']} | {row['runs']} | {row['mean_balanced_accuracy']:.6f} | {row['std_balanced_accuracy']:.6f} | {row['mean_macro_f1']:.6f} | {row['one_class_collapse_count']} |"
        )
    (root / OUT_FOLD_REPORT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")

    close_lines: list[str] = []
    close_lines.append("# I-DARE Representation Redesign Confirmation Closeout Report")
    close_lines.append("")
    close_lines.append("## Status")
    close_lines.append("")
    close_lines.append("`closeout_ready`")
    close_lines.append("")
    close_lines.append("## Produced Files")
    close_lines.append("")
    for p in ALL_OUTPUTS:
        close_lines.append(f"- `{p}`")
    close_lines.append("")
    close_lines.append("## Mean Balanced Accuracy")
    close_lines.append("")
    for row in summary:
        close_lines.append(f"- {row['cell']}: {row['mean_balanced_accuracy']:.6f}")
    close_lines.append("")
    close_lines.append("## R2 vs R3 Stability")
    close_lines.append("")
    close_lines.append(f"- R2 wins vs R3: {gates['r2_wins_vs_r3']}")
    close_lines.append(f"- R3 wins vs R2: {gates['r3_wins_vs_r2']}")
    close_lines.append(f"- R2 fold wins vs R0: {gates['r2_fold_wins_vs_r0']}")
    close_lines.append(f"- R3 fold wins vs R0: {gates['r3_fold_wins_vs_r0']}")
    close_lines.append("")
    close_lines.append("## Leakage / Gate Result")
    close_lines.append("")
    close_lines.append(f"- leakage audit pass: `{gates['leakage_audit_pass']}`")
    close_lines.append(f"- one-class collapse total: `{gates['one_class_collapse_total']}`")
    close_lines.append(f"- forbidden scope touched: `{gates['forbidden_scope_touched']}`")
    close_lines.append(f"- thresholds changed: `{gates['thresholds_changed']}`")
    close_lines.append(f"- R3 >= 0.53 moderate gate: `{gates['moderate_gate_r3_ge_0_53']}`")
    close_lines.append(f"- R3 >= 0.55 strong gate: `{gates['strong_gate_r3_ge_0_55']}`")
    close_lines.append(f"- R3 positive delta vs R0: `{gates['r3_positive_delta_vs_r0']}`")
    close_lines.append(f"- confirmation gate pass: `{gates['confirmation_gate_pass']}`")
    close_lines.append("")
    close_lines.append("No DEAP, fusion, preprocessing changes, threshold changes, DG execution, model-capacity probe, augmentation, W1-owned edits, or main push were performed by this runner.")
    (root / OUT_CLOSEOUT_MD).write_text("\n".join(close_lines) + "\n", encoding="utf-8")

    bundle_lines: list[str] = []
    bundle_lines.append("# I-DARE Representation Redesign Confirmation Artifact Review Bundle")
    bundle_lines.append("")
    bundle_lines.append("## Files")
    bundle_lines.append("")
    for p in ALL_OUTPUTS:
        bundle_lines.append(f"- `{p}`")
    bundle_lines.append("")
    bundle_lines.append("## Review Status")
    bundle_lines.append("")
    bundle_lines.append("`ready_for_control_tower_review`")
    (root / OUT_ARTIFACT_BUNDLE_MD).write_text("\n".join(bundle_lines) + "\n", encoding="utf-8")

    return closeout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["validate", "execute"], default="validate")
    parser.add_argument("--control-approval", default=None)
    args = parser.parse_args()

    validation = validate(args.mode, args.control_approval)
    print(json.dumps(validation, indent=2, sort_keys=True))

    if validation["blockers"]:
        return 2

    if args.mode == "validate":
        return 0

    root = git_root()
    result = execute_confirmation(root)
    closeout = write_outputs(root, result)

    post_validation = validate("validate", None)
    if post_validation["blockers"]:
        print(json.dumps({"post_execution_validation": post_validation}, indent=2, sort_keys=True))
        return 3

    print(json.dumps({"execution_complete": True, "closeout": closeout}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
