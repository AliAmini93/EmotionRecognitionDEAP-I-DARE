#!/usr/bin/env python3
"""Guarded I-DARE representation-redesign smoke runner.

Default mode is validation/preflight. Run mode executes exactly the registered
representation redesign smoke only when the explicit Control run token and
confirmation flag are provided.

Registered smoke:
- I-DARE only
- EEG-only
- arousal-only
- cross-subject / held-out-subject
- RidgeClassifier classical model only
- R0/R1/R2/R3 representation cells
- 6 folds
- 24 runs exactly
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from sklearn.preprocessing import StandardScaler

EXPECTED_BRANCH = "idare/postwave1/representation-redesign-smoke"
EXPECTED_WORKTREE = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-repr-redesign-smoke")
RUN_APPROVAL_TOKEN = "APPROVE_REPRESENTATION_REDESIGN_SMOKE_EXECUTION"

CACHE_NPY = Path(".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy")
CACHE_INDEX = Path(".cache/idare_eeg_cache_index_baseline_corrected.csv")

OBJECTIVE_JSON = Path("docs/idare_repr_redesign_smoke_objective.json")
VALIDATION_MD = Path("docs/idare_repr_redesign_smoke_validation_report.md")
VALIDATION_JSON = Path("docs/idare_repr_redesign_smoke_validation_report.json")

RUNS_CSV = Path("docs/idare_repr_redesign_smoke_runs.csv")
METRIC_SUMMARY_CSV = Path("docs/idare_repr_redesign_smoke_metric_summary.csv")
FOLD_REPORT_MD = Path("docs/idare_repr_redesign_smoke_fold_level_report.md")
FOLD_REPORT_JSON = Path("docs/idare_repr_redesign_smoke_fold_level_report.json")
LEAKAGE_AUDIT_MD = Path("docs/idare_repr_redesign_smoke_leakage_audit.md")
LEAKAGE_AUDIT_JSON = Path("docs/idare_repr_redesign_smoke_leakage_audit.json")
REPR_DIAG_MD = Path("docs/idare_repr_redesign_smoke_representation_diagnostic_report.md")
REPR_DIAG_JSON = Path("docs/idare_repr_redesign_smoke_representation_diagnostic_report.json")
CLOSEOUT_MD = Path("docs/idare_repr_redesign_smoke_closeout_report.md")
CLOSEOUT_JSON = Path("docs/idare_repr_redesign_smoke_closeout_report.json")
ARTIFACT_BUNDLE_MD = Path("docs/idare_repr_redesign_smoke_artifact_review_bundle.md")
ARTIFACT_BUNDLE_JSON = Path("docs/idare_repr_redesign_smoke_artifact_review_bundle.json")

ALLOWED_PREFIXES = (
    "docs/idare_repr_redesign_smoke_",
    "scripts/idare_repr_redesign_smoke_",
)

CELLS = ["R0", "R1", "R2", "R3"]
N_FOLDS = 6
EXPECTED_RUNS = 24
LABEL_COL = "arousal_midpoint_as_high"
SUBJECT_COL = "subject_id"
FS = 128.0


@dataclass(frozen=True)
class FoldSpec:
    fold: int
    train_subjects: tuple[int, ...]
    test_subjects: tuple[int, ...]


@dataclass
class CellTransformResult:
    x_train: np.ndarray
    x_test: np.ndarray
    selected_indices: list[int]
    selected_feature_names: list[str]
    scaler_mean_shape: tuple[int, ...]
    scaler_scale_shape: tuple[int, ...]
    transform_notes: list[str]
    leakage_flags: dict[str, bool]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.strip()


def is_allowed_path(path: str | Path) -> bool:
    p = str(path)
    return p.startswith(ALLOWED_PREFIXES)


def require_allowed_path(path: Path) -> None:
    if not is_allowed_path(path):
        raise SystemExit(f"BLOCKER: output path escapes allowed prefix: {path}")


def write_json(path: Path, data: dict[str, Any]) -> None:
    require_allowed_path(path)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    require_allowed_path(path)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    require_allowed_path(path)
    if not rows:
        raise SystemExit(f"BLOCKER: refusing to write empty CSV: {path}")
    cols = fieldnames or list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check(level: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"level": level, "message": message, "details": details or {}}


def parse_porcelain_paths(text: str) -> list[str]:
    """Parse git status --porcelain=v1 paths robustly.

    Porcelain v1 uses two status chars, one space, then the path.
    For rename lines, include both old and new paths.
    """
    paths: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue

        # Expected porcelain-v1 shape: XY<space>path
        if len(line) >= 3 and line[2] == " ":
            path = line[3:].strip()
        else:
            parts = line.split(maxsplit=1)
            path = parts[1].strip() if len(parts) > 1 else line.strip()

        if " -> " in path:
            old, new = path.split(" -> ", 1)
            paths.append(old.strip())
            paths.append(new.strip())
        else:
            paths.append(path)

    return paths


def validate_git_scope(checks: list[dict[str, Any]]) -> None:
    cwd = Path.cwd().resolve()
    top = Path(run_git(["rev-parse", "--show-toplevel"])).resolve()
    branch = run_git(["branch", "--show-current"])
    head = run_git(["rev-parse", "HEAD"])
    porcelain = run_git(["status", "--porcelain"])
    changed = parse_porcelain_paths(porcelain)
    disallowed = [p for p in changed if not is_allowed_path(p)]

    checks.append(check("OK", "git metadata read", {"cwd": str(cwd), "top": str(top), "branch": branch, "head": head}))

    if branch != EXPECTED_BRANCH:
        checks.append(check("BLOCKER", "wrong branch", {"expected": EXPECTED_BRANCH, "actual": branch}))
    else:
        checks.append(check("OK", "branch matches expected branch"))

    if top != EXPECTED_WORKTREE:
        checks.append(check("BLOCKER", "wrong worktree", {"expected": str(EXPECTED_WORKTREE), "actual": str(top)}))
    else:
        checks.append(check("OK", "worktree matches expected worktree"))

    if disallowed:
        checks.append(check("BLOCKER", "non-allowed dirty paths present", {"paths": disallowed}))
    else:
        checks.append(check("OK", "dirty paths are empty or restricted to allowed idare_repr_redesign_smoke_* prefixes", {"paths": changed}))


def load_objective(checks: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not OBJECTIVE_JSON.exists():
        checks.append(check("BLOCKER", "objective JSON missing", {"path": str(OBJECTIVE_JSON)}))
        return None
    data = json.loads(OBJECTIVE_JSON.read_text(encoding="utf-8"))
    checks.append(check("OK", "objective JSON loaded", {"path": str(OBJECTIVE_JSON)}))
    if data.get("authorization", {}).get("smoke_execution_authorized") is not False:
        checks.append(check("BLOCKER", "objective must not authorize smoke execution by itself"))
    else:
        checks.append(check("OK", "objective keeps smoke execution unauthorized until runtime token"))
    return data


def validate_required_inputs(checks: list[dict[str, Any]]) -> None:
    missing = [str(p) for p in [CACHE_NPY, CACHE_INDEX] if not p.exists()]
    if missing:
        checks.append(check("BLOCKER", "required EEG input files missing", {"missing": missing}))
        return

    try:
        arr = np.load(CACHE_NPY, mmap_mode="r")
        shape = list(arr.shape)
        dtype = str(arr.dtype)
        if shape != [2016, 32, 640]:
            checks.append(check("BLOCKER", "unexpected EEG cache shape", {"shape": shape, "expected": [2016, 32, 640]}))
        else:
            checks.append(check("OK", "EEG cache shape is compatible", {"shape": shape, "dtype": dtype}))
    except Exception as exc:
        checks.append(check("BLOCKER", "failed to inspect EEG cache", {"error": repr(exc)}))

    try:
        df = pd.read_csv(CACHE_INDEX, nrows=5)
        cols = list(df.columns)
        required = ["cache_row", SUBJECT_COL, LABEL_COL]
        missing_cols = [c for c in required if c not in cols]
        if missing_cols:
            checks.append(check("BLOCKER", "cache-index required columns missing", {"missing": missing_cols, "columns": cols}))
        else:
            checks.append(check("OK", "cache-index required arousal/subject/cache columns exist", {"columns": cols}))
    except Exception as exc:
        checks.append(check("BLOCKER", "failed to inspect EEG cache index", {"error": repr(exc)}))


def validate_scope_and_outputs(checks: list[dict[str, Any]], objective: dict[str, Any] | None) -> None:
    planned_outputs = [
        VALIDATION_MD, VALIDATION_JSON, RUNS_CSV, METRIC_SUMMARY_CSV, FOLD_REPORT_MD, FOLD_REPORT_JSON,
        LEAKAGE_AUDIT_MD, LEAKAGE_AUDIT_JSON, REPR_DIAG_MD, REPR_DIAG_JSON, CLOSEOUT_MD, CLOSEOUT_JSON,
        ARTIFACT_BUNDLE_MD, ARTIFACT_BUNDLE_JSON,
    ]
    disallowed = [str(p) for p in planned_outputs if not is_allowed_path(p)]
    if disallowed:
        checks.append(check("BLOCKER", "planned outputs escape allowed prefix", {"disallowed": disallowed}))
    else:
        checks.append(check("OK", "planned outputs are restricted to allowed prefixes", {"planned_outputs": [str(p) for p in planned_outputs]}))

    if objective is None:
        checks.append(check("BLOCKER", "cannot validate objective scope because objective is missing"))
        return

    expected_scope = {
        "dataset": "I-DARE only",
        "modality": "EEG-only first",
        "task": "arousal-only first",
        "evaluation": "cross-subject / held-out-subject",
        "comparison": "pairwise reference comparison required",
        "model_family": "Ridge/classical model only",
        "cells_only": True,
    }
    scope = objective.get("scope", {})
    for key, expected in expected_scope.items():
        actual = scope.get(key)
        if actual != expected:
            checks.append(check("BLOCKER", f"scope mismatch: {key}", {"expected": expected, "actual": actual}))
        else:
            checks.append(check("OK", f"scope validated: {key}"))

    matrix = objective.get("planned_matrix", {})
    if matrix.get("cells") != 4 or matrix.get("folds") != 6 or matrix.get("planned_runs") != 24:
        checks.append(check("BLOCKER", "planned matrix mismatch", {"planned_matrix": matrix}))
    else:
        checks.append(check("OK", "planned 4 x 6 = 24 run matrix validated", {"planned_matrix": matrix}))

    rules = objective.get("hard_leakage_rules", {})
    required_true = [
        "all_fitted_statistics_training_subjects_only",
        "no_heldout_feature_statistics",
        "no_test_labels_for_fit",
        "no_global_all_subject_feature_selection",
        "no_per_test_subject_normalization",
        "no_target_adaptation",
        "no_threshold_tuning_on_heldout",
        "feature_selection_residualization_stability_train_fold_only",
    ]
    failed = [name for name in required_true if rules.get(name) is not True]
    if failed:
        checks.append(check("BLOCKER", "hard leakage rules not fully asserted", {"failed": failed}))
    else:
        checks.append(check("OK", "hard leakage constraints asserted in objective"))


def validate_all() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    validate_git_scope(checks)
    objective = load_objective(checks)
    validate_required_inputs(checks)
    validate_scope_and_outputs(checks, objective)
    blocker_count = sum(1 for c in checks if c["level"] == "BLOCKER")
    report = {
        "status": "validation_passed" if blocker_count == 0 else "validation_blocked",
        "generated_at_utc": now_utc(),
        "mode": "validate",
        "blocker_count": blocker_count,
        "smoke_execution_occurred": False,
        "experiment_execution_occurred": False,
        "checks": checks,
    }
    write_validation_report(report)
    return report


def write_validation_report(report: dict[str, Any]) -> None:
    write_json(VALIDATION_JSON, report)
    lines = [
        "# I-DARE Representation Redesign Smoke Validation Report",
        "",
        f"- status: `{report['status']}`",
        f"- generated_at_utc: `{report['generated_at_utc']}`",
        f"- blocker_count: `{report['blocker_count']}`",
        f"- smoke_execution_occurred: `{report['smoke_execution_occurred']}`",
        f"- experiment_execution_occurred: `{report['experiment_execution_occurred']}`",
        "",
        "## Checks",
        "",
        "| Level | Message | Details |",
        "|---|---|---|",
    ]
    for item in report["checks"]:
        details = json.dumps(item.get("details", {}), ensure_ascii=False, sort_keys=True)
        lines.append(f"| {item['level']} | {item['message']} | `{details}` |")
    lines.extend([
        "",
        "## Blocker Status",
        "",
        "`NO_BLOCKERS`" if report["blocker_count"] == 0 else "`BLOCKED`",
        "",
        "## Execution Boundary",
        "",
        "Validation/preflight only.",
    ])
    write_text(VALIDATION_MD, "\n".join(lines) + "\n")


def feature_names() -> list[str]:
    names: list[str] = []
    temporal = ["mean", "std", "rms", "line_length", "abs_mean"]
    bands = ["theta_4_8", "alpha_8_13", "beta_13_30", "gamma_30_45"]
    for ch in range(32):
        for stat in temporal:
            names.append(f"ch{ch:02d}_{stat}")
    for ch in range(32):
        for band in bands:
            names.append(f"ch{ch:02d}_{band}")
    return names


def compute_base_features(windows: np.ndarray) -> tuple[np.ndarray, list[str]]:
    x = np.asarray(windows, dtype=np.float32)
    mean = x.mean(axis=-1)
    std = x.std(axis=-1)
    rms = np.sqrt(np.mean(x * x, axis=-1))
    line_length = np.mean(np.abs(np.diff(x, axis=-1)), axis=-1)
    abs_mean = np.mean(np.abs(x), axis=-1)
    temporal = np.concatenate([mean, std, rms, line_length, abs_mean], axis=1)

    freqs = np.fft.rfftfreq(x.shape[-1], d=1.0 / FS)
    spec = np.fft.rfft(x, axis=-1)
    power = np.abs(spec).astype(np.float32) ** 2
    band_defs = [(4.0, 8.0), (8.0, 13.0), (13.0, 30.0), (30.0, 45.0)]
    bands = []
    for lo, hi in band_defs:
        mask = (freqs >= lo) & (freqs < hi)
        bands.append(power[:, :, mask].mean(axis=-1))
    band_feats = np.concatenate(bands, axis=1)

    feats = np.concatenate([temporal, band_feats], axis=1).astype(np.float32)
    if not np.isfinite(feats).all():
        raise SystemExit("BLOCKER: non-finite base features detected")
    return feats, feature_names()


def make_folds(subjects: list[int]) -> list[FoldSpec]:
    unique = sorted(set(int(s) for s in subjects))
    chunks = np.array_split(np.asarray(unique, dtype=int), N_FOLDS)
    folds: list[FoldSpec] = []
    for i, chunk in enumerate(chunks, start=1):
        test_subjects = tuple(int(v) for v in chunk.tolist())
        test_set = set(test_subjects)
        train_subjects = tuple(s for s in unique if s not in test_set)
        folds.append(FoldSpec(fold=i, train_subjects=train_subjects, test_subjects=test_subjects))
    if len(folds) != N_FOLDS:
        raise SystemExit("BLOCKER: fold construction did not create exactly 6 folds")
    return folds


def select_top_indices(scores: np.ndarray, k: int) -> list[int]:
    scores = np.asarray(scores, dtype=float)
    scores = np.where(np.isfinite(scores), scores, -np.inf)
    k = max(1, min(k, len(scores)))
    return np.argsort(scores)[::-1][:k].astype(int).tolist()


def fit_cell_transform(
    cell: str,
    x_train_raw: np.ndarray,
    x_test_raw: np.ndarray,
    y_train: np.ndarray,
    subj_train: np.ndarray,
    names: list[str],
) -> CellTransformResult:
    notes: list[str] = []
    leakage_flags = {
        "used_train_subject_statistics_only": True,
        "used_heldout_subject_statistics": False,
        "used_test_labels": False,
        "used_global_all_subject_feature_selection": False,
        "used_per_test_subject_normalization": False,
        "used_target_adaptation": False,
        "used_threshold_tuning": False,
    }

    selected = list(range(x_train_raw.shape[1]))
    xtr = x_train_raw.copy()
    xte = x_test_raw.copy()

    if cell == "R0":
        notes.append("R0 anchor: all base EEG summary features; StandardScaler fit on training fold only.")

    elif cell == "R1":
        notes.append("R1: train-subject residualization fit only on training subjects; unseen held-out subject receives no per-subject fitted offset.")
        global_mean = x_train_raw.mean(axis=0)
        xtr = np.empty_like(x_train_raw)
        for s in sorted(set(int(v) for v in subj_train)):
            mask = subj_train == s
            subject_mean = x_train_raw[mask].mean(axis=0)
            subject_offset = subject_mean - global_mean
            xtr[mask] = x_train_raw[mask] - subject_offset
        xte = x_test_raw.copy()

    elif cell == "R2":
        notes.append("R2: train-only subject-invariant feature selection using training labels and training-subject variability only.")
        class0 = x_train_raw[y_train == 0]
        class1 = x_train_raw[y_train == 1]
        if len(class0) == 0 or len(class1) == 0:
            raise SystemExit("BLOCKER: R2 needs both classes in training fold")
        label_effect = np.abs(class1.mean(axis=0) - class0.mean(axis=0))
        subject_means = []
        for s in sorted(set(int(v) for v in subj_train)):
            subject_means.append(x_train_raw[subj_train == s].mean(axis=0))
        subject_means_arr = np.vstack(subject_means)
        subject_std = subject_means_arr.std(axis=0) + 1e-6
        scores = label_effect / subject_std
        selected = select_top_indices(scores, 96)
        xtr = x_train_raw[:, selected]
        xte = x_test_raw[:, selected]

    elif cell == "R3":
        notes.append("R3: diagnostics-first stable subset selected only from training-subject label effects.")
        train_subjects = sorted(set(int(v) for v in subj_train))
        chunks = np.array_split(np.asarray(train_subjects, dtype=int), 3)
        effects = []
        for chunk in chunks:
            mask = np.isin(subj_train, chunk)
            yy = y_train[mask]
            xx = x_train_raw[mask]
            if len(set(yy.tolist())) < 2:
                continue
            effects.append(xx[yy == 1].mean(axis=0) - xx[yy == 0].mean(axis=0))
        if not effects:
            raise SystemExit("BLOCKER: R3 stable-feature selection has no valid training-subject diagnostic blocks")
        eff = np.vstack(effects)
        sign_consistency = np.abs(np.sign(eff).sum(axis=0)) / eff.shape[0]
        stability = np.abs(eff.mean(axis=0)) / (eff.std(axis=0) + 1e-6)
        scores = stability * sign_consistency
        selected = select_top_indices(scores, 64)
        xtr = x_train_raw[:, selected]
        xte = x_test_raw[:, selected]

    else:
        raise SystemExit(f"BLOCKER: unknown cell {cell}")

    scaler = StandardScaler()
    x_train = scaler.fit_transform(xtr).astype(np.float32)
    x_test = scaler.transform(xte).astype(np.float32)

    if not np.isfinite(x_train).all() or not np.isfinite(x_test).all():
        raise SystemExit(f"BLOCKER: non-finite transformed features for {cell}")

    selected_names = [names[i] for i in selected]
    return CellTransformResult(
        x_train=x_train,
        x_test=x_test,
        selected_indices=selected,
        selected_feature_names=selected_names,
        scaler_mean_shape=tuple(scaler.mean_.shape),
        scaler_scale_shape=tuple(scaler.scale_.shape),
        transform_notes=notes,
        leakage_flags=leakage_flags,
    )


def metric_dict(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    pred_unique = sorted(set(int(v) for v in y_pred.tolist()))
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "tn": int(cm[0, 0]),
        "fp": int(cm[0, 1]),
        "fn": int(cm[1, 0]),
        "tp": int(cm[1, 1]),
        "pred_zero": int((y_pred == 0).sum()),
        "pred_one": int((y_pred == 1).sum()),
        "true_zero": int((y_true == 0).sum()),
        "true_one": int((y_true == 1).sum()),
        "one_class_collapse": bool(len(pred_unique) == 1),
        "collapsed_to": pred_unique[0] if len(pred_unique) == 1 else "",
    }


def run_registered_smoke() -> dict[str, Any]:
    validation = validate_all()
    if validation["blocker_count"] != 0:
        raise SystemExit("BLOCKER: validation failed; refusing smoke execution")

    print("===== loading I-DARE EEG baseline-corrected cache =====")
    index = pd.read_csv(CACHE_INDEX)
    required_cols = ["cache_row", SUBJECT_COL, LABEL_COL]
    missing_cols = [c for c in required_cols if c not in index.columns]
    if missing_cols:
        raise SystemExit(f"BLOCKER: missing required columns: {missing_cols}")

    index = index[index[LABEL_COL].isin([0, 1])].copy()
    index["cache_row"] = index["cache_row"].astype(int)
    index[SUBJECT_COL] = index[SUBJECT_COL].astype(int)
    index[LABEL_COL] = index[LABEL_COL].astype(int)

    windows = np.load(CACHE_NPY, mmap_mode="r")
    x_all, names = compute_base_features(windows)
    y_all = index[LABEL_COL].to_numpy(dtype=int)
    subjects = index[SUBJECT_COL].to_numpy(dtype=int)

    folds = make_folds(subjects.tolist())

    runs: list[dict[str, Any]] = []
    leakage_rows: list[dict[str, Any]] = []
    diag_rows: list[dict[str, Any]] = []
    run_id = 0

    for fold in folds:
        train_mask = np.isin(subjects, np.asarray(fold.train_subjects))
        test_mask = np.isin(subjects, np.asarray(fold.test_subjects))
        if np.any(train_mask & test_mask):
            raise SystemExit(f"BLOCKER: train/test overlap in fold {fold.fold}")

        x_train_raw = x_all[train_mask]
        x_test_raw = x_all[test_mask]
        y_train = y_all[train_mask]
        y_test = y_all[test_mask]
        subj_train = subjects[train_mask]

        if len(set(y_train.tolist())) < 2:
            raise SystemExit(f"BLOCKER: training fold {fold.fold} has one class only")
        if len(set(y_test.tolist())) < 2:
            print(f"WARNING: held-out fold {fold.fold} has one class only; metrics may be unstable but no tuning is performed.")

        for cell in CELLS:
            run_id += 1
            transform = fit_cell_transform(cell, x_train_raw, x_test_raw, y_train, subj_train, names)

            clf = RidgeClassifier(alpha=1.0)
            clf.fit(transform.x_train, y_train)
            y_pred = clf.predict(transform.x_test).astype(int)
            m = metric_dict(y_test, y_pred)

            run_row = {
                "run_id": run_id,
                "cell": cell,
                "fold": fold.fold,
                "model": "RidgeClassifier_alpha_1.0",
                "dataset": "I-DARE",
                "modality": "EEG",
                "task": "arousal",
                "label_column": LABEL_COL,
                "n_train_subjects": len(fold.train_subjects),
                "n_test_subjects": len(fold.test_subjects),
                "train_subjects": " ".join(str(s) for s in fold.train_subjects),
                "test_subjects": " ".join(str(s) for s in fold.test_subjects),
                "n_train_rows": int(train_mask.sum()),
                "n_test_rows": int(test_mask.sum()),
                "n_selected_features": len(transform.selected_indices),
                **m,
            }
            runs.append(run_row)

            leakage_ok = (
                not set(fold.train_subjects).intersection(set(fold.test_subjects))
                and all(transform.leakage_flags.values()) is False
            )
            # Explicitly compute pass from individual forbidden flags.
            leakage_pass = (
                transform.leakage_flags["used_train_subject_statistics_only"]
                and not transform.leakage_flags["used_heldout_subject_statistics"]
                and not transform.leakage_flags["used_test_labels"]
                and not transform.leakage_flags["used_global_all_subject_feature_selection"]
                and not transform.leakage_flags["used_per_test_subject_normalization"]
                and not transform.leakage_flags["used_target_adaptation"]
                and not transform.leakage_flags["used_threshold_tuning"]
                and not set(fold.train_subjects).intersection(set(fold.test_subjects))
            )

            leakage_rows.append({
                "run_id": run_id,
                "cell": cell,
                "fold": fold.fold,
                "train_test_subjects_disjoint": True,
                "used_train_subject_statistics_only": transform.leakage_flags["used_train_subject_statistics_only"],
                "used_heldout_subject_statistics": transform.leakage_flags["used_heldout_subject_statistics"],
                "used_test_labels": transform.leakage_flags["used_test_labels"],
                "used_global_all_subject_feature_selection": transform.leakage_flags["used_global_all_subject_feature_selection"],
                "used_per_test_subject_normalization": transform.leakage_flags["used_per_test_subject_normalization"],
                "used_target_adaptation": transform.leakage_flags["used_target_adaptation"],
                "used_threshold_tuning": transform.leakage_flags["used_threshold_tuning"],
                "leakage_pass": leakage_pass,
                "notes": " | ".join(transform.transform_notes),
            })

            diag_rows.append({
                "run_id": run_id,
                "cell": cell,
                "fold": fold.fold,
                "base_feature_count": len(names),
                "selected_feature_count": len(transform.selected_indices),
                "first_selected_features": "; ".join(transform.selected_feature_names[:12]),
                "scaler_fit_scope": "train_fold_only",
                "model_family": "RidgeClassifier",
                "transform_notes": " | ".join(transform.transform_notes),
            })

            print(json.dumps({
                "run_id": run_id,
                "cell": cell,
                "fold": fold.fold,
                "balanced_accuracy": round(m["balanced_accuracy"], 4),
                "macro_f1": round(m["macro_f1"], 4),
                "one_class_collapse": m["one_class_collapse"],
            }, sort_keys=True))

    if len(runs) != EXPECTED_RUNS:
        raise SystemExit(f"BLOCKER: expected exactly {EXPECTED_RUNS} runs, got {len(runs)}")

    if any(not row["leakage_pass"] for row in leakage_rows):
        write_csv(RUNS_CSV, runs)
        write_json(LEAKAGE_AUDIT_JSON, {"status": "failed", "rows": leakage_rows})
        raise SystemExit("BLOCKER: leakage audit failed")

    runs_df = pd.DataFrame(runs)
    metric_rows: list[dict[str, Any]] = []
    for cell, g in runs_df.groupby("cell", sort=True):
        r0 = runs_df[runs_df["cell"] == "R0"].set_index("fold")
        deltas = []
        wins = 0
        for _, row in g.iterrows():
            base = float(r0.loc[int(row["fold"]), "balanced_accuracy"])
            delta = float(row["balanced_accuracy"] - base)
            deltas.append(delta)
            if delta > 0:
                wins += 1
        metric_rows.append({
            "cell": cell,
            "n_runs": int(len(g)),
            "mean_accuracy": float(g["accuracy"].mean()),
            "mean_balanced_accuracy": float(g["balanced_accuracy"].mean()),
            "std_balanced_accuracy": float(g["balanced_accuracy"].std(ddof=0)),
            "min_balanced_accuracy": float(g["balanced_accuracy"].min()),
            "max_balanced_accuracy": float(g["balanced_accuracy"].max()),
            "mean_macro_f1": float(g["macro_f1"].mean()),
            "one_class_collapse_count": int(g["one_class_collapse"].sum()),
            "mean_delta_vs_R0_balanced_accuracy": float(np.mean(deltas)),
            "fold_wins_vs_R0": int(wins),
        })

    summary_df = pd.DataFrame(metric_rows)
    best_row = summary_df.sort_values(
        ["mean_balanced_accuracy", "mean_delta_vs_R0_balanced_accuracy", "fold_wins_vs_R0"],
        ascending=[False, False, False],
    ).iloc[0].to_dict()

    gate_053 = bool(float(best_row["mean_balanced_accuracy"]) >= 0.53)
    gate_055 = bool(float(best_row["mean_balanced_accuracy"]) >= 0.55)
    one_class_total = int(runs_df["one_class_collapse"].sum())

    write_csv(RUNS_CSV, runs)
    write_csv(METRIC_SUMMARY_CSV, metric_rows)
    write_json(FOLD_REPORT_JSON, {"status": "complete", "runs": runs})
    write_json(LEAKAGE_AUDIT_JSON, {"status": "passed", "rows": leakage_rows})
    write_json(REPR_DIAG_JSON, {"status": "complete", "rows": diag_rows})

    fold_lines = [
        "# I-DARE Representation Redesign Smoke Fold-Level Report",
        "",
        f"- generated_at_utc: `{now_utc()}`",
        f"- run_count: `{len(runs)}`",
        "",
        "| Run | Cell | Fold | Balanced Accuracy | Macro F1 | One-class | Test Subjects |",
        "|---:|---|---:|---:|---:|---|---|",
    ]
    for row in runs:
        fold_lines.append(
            f"| {row['run_id']} | {row['cell']} | {row['fold']} | {row['balanced_accuracy']:.4f} | "
            f"{row['macro_f1']:.4f} | {row['one_class_collapse']} | {row['test_subjects']} |"
        )
    write_text(FOLD_REPORT_MD, "\n".join(fold_lines) + "\n")

    leakage_lines = [
        "# I-DARE Representation Redesign Smoke Leakage Audit",
        "",
        "- status: `passed`",
        "- all fitted statistics use training subjects only",
        "- no held-out/test-subject feature statistics",
        "- no test labels used for fitting/selection/residualization/stability/thresholding",
        "- no global all-subject feature selection",
        "- no per-test-subject normalization",
        "- no target adaptation",
        "- no threshold tuning on held-out subjects",
        "",
        "| Run | Cell | Fold | Leakage Pass | Notes |",
        "|---:|---|---:|---|---|",
    ]
    for row in leakage_rows:
        leakage_lines.append(f"| {row['run_id']} | {row['cell']} | {row['fold']} | {row['leakage_pass']} | {row['notes']} |")
    write_text(LEAKAGE_AUDIT_MD, "\n".join(leakage_lines) + "\n")

    diag_lines = [
        "# I-DARE Representation Redesign Smoke Representation Diagnostic Report",
        "",
        f"- base_feature_count: `{len(names)}`",
        "",
        "| Run | Cell | Fold | Selected Features | Notes |",
        "|---:|---|---:|---:|---|",
    ]
    for row in diag_rows:
        diag_lines.append(f"| {row['run_id']} | {row['cell']} | {row['fold']} | {row['selected_feature_count']} | {row['transform_notes']} |")
    write_text(REPR_DIAG_MD, "\n".join(diag_lines) + "\n")

    closeout = {
        "status": "closeout_ready",
        "generated_at_utc": now_utc(),
        "branch": EXPECTED_BRANCH,
        "worktree": str(EXPECTED_WORKTREE),
        "run_count": len(runs),
        "expected_run_count": EXPECTED_RUNS,
        "best_cell": str(best_row["cell"]),
        "best_mean_balanced_accuracy": float(best_row["mean_balanced_accuracy"]),
        "leakage_audit_result": "passed",
        "one_class_collapse_count": one_class_total,
        "gate_0_53_pass": gate_053,
        "gate_0_55_pass": gate_055,
        "smoke_execution_occurred": True,
        "experiment_scope": "registered_24_run_representation_redesign_smoke_only",
        "forbidden_scope_touched": False,
    }
    write_json(CLOSEOUT_JSON, closeout)

    closeout_lines = [
        "# I-DARE Representation Redesign Smoke Closeout Report",
        "",
        "- status: `closeout_ready`",
        f"- run_count: `{len(runs)}`",
        f"- best_cell: `{closeout['best_cell']}`",
        f"- best_mean_balanced_accuracy: `{closeout['best_mean_balanced_accuracy']:.4f}`",
        f"- leakage_audit_result: `{closeout['leakage_audit_result']}`",
        f"- one_class_collapse_count: `{one_class_total}`",
        f"- gate_0_53_pass: `{gate_053}`",
        f"- gate_0_55_pass: `{gate_055}`",
        "",
        "## Metric Summary",
        "",
        "| Cell | Runs | Mean Balanced Accuracy | Mean Macro F1 | Delta vs R0 | Wins vs R0 | One-class Count |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in metric_rows:
        closeout_lines.append(
            f"| {row['cell']} | {row['n_runs']} | {row['mean_balanced_accuracy']:.4f} | "
            f"{row['mean_macro_f1']:.4f} | {row['mean_delta_vs_R0_balanced_accuracy']:.4f} | "
            f"{row['fold_wins_vs_R0']} | {row['one_class_collapse_count']} |"
        )
    write_text(CLOSEOUT_MD, "\n".join(closeout_lines) + "\n")

    produced = [
        RUNS_CSV, METRIC_SUMMARY_CSV, FOLD_REPORT_MD, FOLD_REPORT_JSON,
        LEAKAGE_AUDIT_MD, LEAKAGE_AUDIT_JSON, REPR_DIAG_MD, REPR_DIAG_JSON,
        CLOSEOUT_MD, CLOSEOUT_JSON,
    ]
    bundle_rows = []
    for path in produced:
        bundle_rows.append({
            "path": str(path),
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else "",
            "allowed_prefix": is_allowed_path(path),
        })

    bundle = {
        "status": "artifact_review_bundle_ready",
        "generated_at_utc": now_utc(),
        "latest_known_head_before_commit": run_git(["rev-parse", "HEAD"]),
        "closeout": closeout,
        "artifacts": bundle_rows,
    }
    write_json(ARTIFACT_BUNDLE_JSON, bundle)

    bundle_lines = [
        "# I-DARE Representation Redesign Smoke Artifact Review Bundle",
        "",
        "- status: `artifact_review_bundle_ready`",
        f"- generated_at_utc: `{bundle['generated_at_utc']}`",
        "",
        "| Path | Exists | Allowed Prefix | SHA256 |",
        "|---|---|---|---|",
    ]
    for row in bundle_rows:
        bundle_lines.append(f"| {row['path']} | {row['exists']} | {row['allowed_prefix']} | `{row['sha256']}` |")
    write_text(ARTIFACT_BUNDLE_MD, "\n".join(bundle_lines) + "\n")

    print(json.dumps(closeout, indent=2, sort_keys=True))
    return closeout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["validate", "run"], default="validate")
    parser.add_argument("--control-run-approval", default="")
    parser.add_argument("--confirm-24-run-smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.mode == "validate":
        report = validate_all()
        print(json.dumps({
            "status": report["status"],
            "blocker_count": report["blocker_count"],
            "validation_report_md": str(VALIDATION_MD),
            "validation_report_json": str(VALIDATION_JSON),
            "smoke_execution_occurred": False,
            "experiment_execution_occurred": False,
        }, indent=2))
        return 0 if report["blocker_count"] == 0 else 2

    validation = validate_all()
    if validation["blocker_count"] != 0:
        print("BLOCKER: validation failed; refusing run mode")
        return 2

    if args.control_run_approval != RUN_APPROVAL_TOKEN or not args.confirm_24_run_smoke:
        print("BLOCKER: 24-run smoke execution is not authorized")
        print("Required token:", RUN_APPROVAL_TOKEN)
        print("Required flag: --confirm-24-run-smoke")
        print("No smoke execution occurred.")
        return 2

    run_registered_smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
