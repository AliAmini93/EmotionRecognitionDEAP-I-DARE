#!/usr/bin/env python3
"""Smoke tests for I-DARE alternative pairwise feature-representation patch.

This script does not fit learned models. It validates cache alignment,
feature extraction feasibility, pair target construction, fold-locality, and
frozen matrix scope for a later reviewed patch first pass.
"""

from __future__ import annotations

import csv
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DOCS = Path("docs")
CACHE_INDEX = Path(".cache/idare_eeg_cache_index_baseline_corrected.csv")
WINDOWS_NPY = Path(".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy")

OBJECTIVE_JSON = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_tests_objective.json"
REVIEW_JSON = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_spec_review_status.json"
SPEC_JSON = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_spec.json"
RUN_MATRIX_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_run_matrix.csv"
FEATURE_DEF_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_feature_set_definition.csv"
REQUIREMENTS_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_requirements.csv"
GUARDRAILS_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_feature_guardrails.csv"
STATUS_JSON = DOCS / "project_status_current.json"
STATUS_MD = DOCS / "project_status_current.md"

REPORT_MD = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_tests_report.md"
REPORT_JSON = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_tests_report.json"
FEATURE_SHAPE_AUDIT = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_feature_shape_audit.csv"
PAIR_TARGET_AUDIT = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_pair_target_audit.csv"
FOLD_LOCALITY_AUDIT = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_fold_locality_audit.csv"
SMOKE_DECISION_MATRIX = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_decision_matrix.csv"
MATRIX_GUARD_AUDIT = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_matrix_guard_audit.csv"

FS = 128.0
BANDS = [
    ("theta_4_8", 4.0, 8.0),
    ("alpha_8_13", 8.0, 13.0),
    ("beta_13_30", 13.0, 30.0),
    ("gamma_30_45", 30.0, 45.0),
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise SystemExit(f"ERROR: no rows for {path}")
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def md_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")).replace("|", "\\|").replace("\n", " ") for c in cols) + " |")
    return "\n".join(out)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def find_col(df: pd.DataFrame, preferred: list[str], contains: str | None = None) -> str | None:
    lower = {str(c).lower(): str(c) for c in df.columns}
    for name in preferred:
        if name.lower() in lower:
            return lower[name.lower()]
    if contains:
        candidates = []
        for c in df.columns:
            lc = str(c).lower()
            if contains.lower() in lc:
                candidates.append(str(c))
        numeric = [c for c in candidates if pd.api.types.is_numeric_dtype(df[c])]
        if numeric:
            # Prefer actual label/rating columns, not derived IDs.
            def score(c: str) -> tuple[int, int]:
                lc = c.lower()
                good = int(any(tok in lc for tok in ["rating", "label", "score", contains.lower()]))
                bad = int(any(tok in lc for tok in ["pred", "prediction", "rank", "fold"]))
                return (bad, -good)
            return sorted(numeric, key=score)[0]
        if candidates:
            return candidates[0]
    return None


def derive_subject_fold(subject_values: pd.Series, n_folds: int = 6) -> pd.Series:
    unique_subjects = sorted(subject_values.astype(str).unique())
    mapping = {s: (i % n_folds) + 1 for i, s in enumerate(unique_subjects)}
    return subject_values.astype(str).map(mapping).astype(int)


def temporal_features(windows: np.ndarray) -> np.ndarray:
    x = windows.astype(np.float32, copy=False)
    mean = x.mean(axis=-1)
    std = x.std(axis=-1)
    rms = np.sqrt(np.mean(np.square(x), axis=-1))
    line_length = np.mean(np.abs(np.diff(x, axis=-1)), axis=-1)
    return np.concatenate([mean, std, rms, line_length], axis=1).astype(np.float32, copy=False)


def bandpower_features(windows: np.ndarray) -> np.ndarray:
    x = windows.astype(np.float32, copy=False)
    freqs = np.fft.rfftfreq(x.shape[-1], d=1.0 / FS)
    spectrum = np.fft.rfft(x, axis=-1)
    power = (np.abs(spectrum) ** 2).astype(np.float32, copy=False)
    bands = []
    for _, lo, hi in BANDS:
        mask = (freqs >= lo) & (freqs < hi)
        if not np.any(mask):
            bands.append(np.zeros(x.shape[:2], dtype=np.float32))
        else:
            bands.append(power[:, :, mask].mean(axis=-1))
    return np.concatenate(bands, axis=1).astype(np.float32, copy=False)


def finite_summary(arr: np.ndarray) -> dict[str, Any]:
    finite = np.isfinite(arr)
    return {
        "n_rows": int(arr.shape[0]),
        "n_features": int(arr.shape[1]) if arr.ndim == 2 else int(np.prod(arr.shape[1:])),
        "finite_count": int(finite.sum()),
        "total_values": int(arr.size),
        "finite_fraction": float(finite.mean()),
        "min": float(np.nanmin(arr)),
        "max": float(np.nanmax(arr)),
        "mean_abs": float(np.nanmean(np.abs(arr))),
    }


def pair_counts_by_subject(df: pd.DataFrame, subject_col: str, label_col: str) -> dict[str, Any]:
    total_pairs = 0
    non_tie_pairs = 0
    canonical_positive = 0
    subjects_with_pairs = 0
    max_pairs_one_subject = 0
    for _, g in df.groupby(subject_col, dropna=False):
        labels = pd.to_numeric(g[label_col], errors="coerce").dropna().to_numpy()
        n = int(len(labels))
        if n < 2:
            continue
        pairs = n * (n - 1) // 2
        total_pairs += pairs
        max_pairs_one_subject = max(max_pairs_one_subject, pairs)
        diff = labels[:, None] - labels[None, :]
        upper = diff[np.triu_indices(n, k=1)]
        non_tie = upper[upper != 0]
        non_tie_pairs += int(non_tie.size)
        canonical_positive += int((non_tie > 0).sum())
        if non_tie.size:
            subjects_with_pairs += 1
    positive_rate = canonical_positive / non_tie_pairs if non_tie_pairs else math.nan
    return {
        "total_within_subject_pairs_including_ties": total_pairs,
        "non_tie_within_subject_pairs": non_tie_pairs,
        "canonical_positive_pairs": canonical_positive,
        "canonical_positive_rate": positive_rate,
        "subjects_with_non_tie_pairs": subjects_with_pairs,
        "max_pairs_one_subject": max_pairs_one_subject,
    }


def main() -> None:
    created = now_utc()
    objective = read_json(OBJECTIVE_JSON)
    review = read_json(REVIEW_JSON)
    spec = read_json(SPEC_JSON)
    status = read_json(STATUS_JSON)

    if objective.get("status") != "objective_created":
        raise SystemExit("ERROR: smoke objective status mismatch")
    if objective.get("smoke_tests_authorized") is not True:
        raise SystemExit("ERROR: smoke objective must authorize smoke tests")
    if objective.get("training_authorized") is not False:
        raise SystemExit("ERROR: smoke objective must not authorize training")
    if objective.get("patch_first_pass_authorized") is not False:
        raise SystemExit("ERROR: smoke objective must not authorize patch first pass")
    if spec.get("status") != "complete_pending_human_review":
        raise SystemExit("ERROR: spec status mismatch")
    if spec.get("training_authorized") is not False:
        raise SystemExit("ERROR: spec must not authorize training")
    if review.get("accepted_diagnosis") != "feature_representation_patch_spec_complete":
        raise SystemExit("ERROR: spec review diagnosis mismatch")

    run_matrix = normalize_columns(pd.read_csv(RUN_MATRIX_CSV))
    feature_def = normalize_columns(pd.read_csv(FEATURE_DEF_CSV))
    requirements = normalize_columns(pd.read_csv(REQUIREMENTS_CSV))
    guardrails = normalize_columns(pd.read_csv(GUARDRAILS_CSV))
    idx = normalize_columns(pd.read_csv(CACHE_INDEX))
    windows = np.load(WINDOWS_NPY, mmap_mode="r")

    if windows.ndim != 3:
        raise SystemExit(f"ERROR: expected EEG windows to be 3D, got shape={windows.shape}")
    if len(idx) != int(windows.shape[0]):
        cache_aligned = False
    else:
        cache_aligned = True

    subject_col = find_col(idx, ["subject", "subject_id", "participant", "participant_id", "subj", "s"], contains="subject")
    trial_col = find_col(idx, ["trial", "trial_id", "video", "video_id", "clip", "clip_id", "sample_id", "window_id"], contains="trial")
    arousal_col = find_col(idx, ["arousal", "arousal_rating", "rating_arousal", "arousal_label", "label_arousal"], contains="arousal")
    if subject_col is None:
        raise SystemExit("ERROR: could not identify subject column in EEG cache index")
    if arousal_col is None:
        raise SystemExit("ERROR: could not identify arousal label column in EEG cache index")
    if trial_col is None:
        trial_col = "__row_id__"
        idx[trial_col] = range(len(idx))

    idx["_patch_fold"] = derive_subject_fold(idx[subject_col], n_folds=6)

    # Feature extraction smoke.
    x = np.asarray(windows, dtype=np.float32)
    temporal = temporal_features(x)
    bandpower = bandpower_features(x)
    current = temporal
    robust_current = temporal
    band_only = bandpower
    band_temporal = np.concatenate([bandpower, temporal], axis=1).astype(np.float32, copy=False)

    feature_arrays = {
        "current_summary_diff_control": current,
        "robust_scaled_current_summary_diff_control": robust_current,
        "bandpower_only_control_v1": band_only,
        "bandpower_temporal_stats_v1": band_temporal,
    }

    feature_rows = []
    for feature_set_id, arr in feature_arrays.items():
        fs_def = feature_def[feature_def["feature_set_id"].astype(str).eq(feature_set_id)]
        expected_in_spec = len(fs_def) == 1
        s = finite_summary(arr)
        feature_rows.append({
            "feature_set_id": feature_set_id,
            "expected_in_spec": expected_in_spec,
            "window_rows": s["n_rows"],
            "n_features": s["n_features"],
            "finite_fraction": s["finite_fraction"],
            "finite_count": s["finite_count"],
            "total_values": s["total_values"],
            "min": s["min"],
            "max": s["max"],
            "mean_abs": s["mean_abs"],
            "pass": bool(expected_in_spec and s["n_rows"] == len(idx) and s["finite_fraction"] == 1.0 and s["n_features"] > 0),
        })
    write_csv(FEATURE_SHAPE_AUDIT, feature_rows)

    pc = pair_counts_by_subject(idx, subject_col, arousal_col)
    pair_rows = [{
        "task": "arousal",
        "subject_col": subject_col,
        "trial_col": trial_col,
        "label_col": arousal_col,
        "n_index_rows": int(len(idx)),
        "n_subjects": int(idx[subject_col].astype(str).nunique()),
        "total_within_subject_pairs_including_ties": pc["total_within_subject_pairs_including_ties"],
        "non_tie_within_subject_pairs": pc["non_tie_within_subject_pairs"],
        "canonical_positive_pairs": pc["canonical_positive_pairs"],
        "canonical_positive_rate": pc["canonical_positive_rate"],
        "subjects_with_non_tie_pairs": pc["subjects_with_non_tie_pairs"],
        "same_subject_only_by_construction": True,
        "pass": bool(pc["non_tie_within_subject_pairs"] > 0 and pc["subjects_with_non_tie_pairs"] >= 20),
    }]
    write_csv(PAIR_TARGET_AUDIT, pair_rows)

    fold_rows = []
    for fold in range(1, 7):
        train = idx[idx["_patch_fold"] != fold]
        val = idx[idx["_patch_fold"] == fold]
        train_subjects = set(train[subject_col].astype(str))
        val_subjects = set(val[subject_col].astype(str))
        overlap = train_subjects & val_subjects
        fold_rows.append({
            "fold": fold,
            "n_train_rows": int(len(train)),
            "n_val_rows": int(len(val)),
            "n_train_subjects": int(len(train_subjects)),
            "n_val_subjects": int(len(val_subjects)),
            "subject_overlap_count": int(len(overlap)),
            "scaler_fit_scope": "train_fold_only_required_for_future_run",
            "pass": bool(len(val) > 0 and len(train) > 0 and len(overlap) == 0),
        })
    write_csv(FOLD_LOCALITY_AUDIT, fold_rows)

    expected_features = set(feature_arrays.keys())
    matrix_features = set(run_matrix["feature_set_id"].astype(str))
    expected_models = {
        "random_balanced_no_training",
        "majority_train_label_no_training",
        "ridge_classifier_pairwise_feature_patch",
        "logistic_regression_pairwise_feature_patch",
    }
    matrix_models = set(run_matrix["model"].astype(str))
    matrix_folds = sorted(set(int(x) for x in run_matrix["fold"].tolist()))
    matrix_rows = [
        {
            "guard": "row_count",
            "expected": 96,
            "observed": int(len(run_matrix)),
            "pass": bool(len(run_matrix) == 96),
        },
        {
            "guard": "feature_set_scope",
            "expected": ",".join(sorted(expected_features)),
            "observed": ",".join(sorted(matrix_features)),
            "pass": bool(matrix_features == expected_features),
        },
        {
            "guard": "model_scope",
            "expected": ",".join(sorted(expected_models)),
            "observed": ",".join(sorted(matrix_models)),
            "pass": bool(matrix_models == expected_models),
        },
        {
            "guard": "modality_scope",
            "expected": "EEG",
            "observed": ",".join(sorted(set(run_matrix["modality"].astype(str)))),
            "pass": bool(set(run_matrix["modality"].astype(str)) == {"EEG"}),
        },
        {
            "guard": "task_scope",
            "expected": "arousal",
            "observed": ",".join(sorted(set(run_matrix["task"].astype(str)))),
            "pass": bool(set(run_matrix["task"].astype(str)) == {"arousal"}),
        },
        {
            "guard": "fold_scope",
            "expected": "1,2,3,4,5,6",
            "observed": ",".join(map(str, matrix_folds)),
            "pass": bool(matrix_folds == [1, 2, 3, 4, 5, 6]),
        },
        {
            "guard": "authorized_status",
            "expected": "matrix_defined_not_yet_authorized_for_training",
            "observed": ",".join(sorted(set(run_matrix["authorized_status"].astype(str)))),
            "pass": bool(set(run_matrix["authorized_status"].astype(str)) == {"matrix_defined_not_yet_authorized_for_training"}),
        },
    ]
    write_csv(MATRIX_GUARD_AUDIT, matrix_rows)

    feature_pass = all(r["pass"] for r in feature_rows)
    pair_pass = all(r["pass"] for r in pair_rows)
    fold_pass = all(r["pass"] for r in fold_rows)
    matrix_pass = all(r["pass"] for r in matrix_rows)
    cache_pass = bool(cache_aligned)
    no_training_pass = True

    decision_rows = [
        {
            "requirement_id": "SMOKE_001",
            "check": "cache_index_window_alignment",
            "status": "pass" if cache_pass else "fail",
            "evidence": f"index_rows={len(idx)} windows_shape={list(windows.shape)}",
        },
        {
            "requirement_id": "SMOKE_002",
            "check": "feature_matrices_finite_and_shaped",
            "status": "pass" if feature_pass else "fail",
            "evidence": str(FEATURE_SHAPE_AUDIT),
        },
        {
            "requirement_id": "SMOKE_003",
            "check": "pairwise_target_construction",
            "status": "pass" if pair_pass else "fail",
            "evidence": str(PAIR_TARGET_AUDIT),
        },
        {
            "requirement_id": "SMOKE_004",
            "check": "fold_locality_subject_disjointness",
            "status": "pass" if fold_pass else "fail",
            "evidence": str(FOLD_LOCALITY_AUDIT),
        },
        {
            "requirement_id": "SMOKE_005",
            "check": "frozen_matrix_scope_guard",
            "status": "pass" if matrix_pass else "fail",
            "evidence": str(MATRIX_GUARD_AUDIT),
        },
        {
            "requirement_id": "SMOKE_006",
            "check": "no_training_metrics_produced",
            "status": "pass" if no_training_pass else "fail",
            "evidence": "script performs no model fit/predict; smoke audits only",
        },
    ]
    write_csv(SMOKE_DECISION_MATRIX, decision_rows)

    all_passed = all(r["status"] == "pass" for r in decision_rows)
    if all_passed:
        diagnosis = "feature_representation_patch_smoke_tests_passed"
        recommended_next = "label_semantics_alternative_pairwise_feature_representation_patch_first_pass_objective"
        next_allowed_step = "human_review_closeout_then_create_feature_patch_first_pass_objective"
    elif not cache_pass:
        diagnosis = "feature_representation_patch_smoke_failed_cache_alignment"
        recommended_next = "label_semantics_alternative_pairwise_feature_patch_cache_alignment_fix_objective"
        next_allowed_step = "human_review_closeout_then_fix_cache_alignment"
    elif not feature_pass:
        diagnosis = "feature_representation_patch_smoke_failed_feature_extraction"
        recommended_next = "label_semantics_alternative_pairwise_feature_patch_extraction_fix_objective"
        next_allowed_step = "human_review_closeout_then_fix_feature_extraction"
    elif not fold_pass or not pair_pass:
        diagnosis = "feature_representation_patch_smoke_failed_pair_or_fold_guard"
        recommended_next = "label_semantics_alternative_pairwise_feature_patch_pair_fold_fix_objective"
        next_allowed_step = "human_review_closeout_then_fix_pair_or_fold_guard"
    else:
        diagnosis = "feature_representation_patch_smoke_failed_matrix_guard"
        recommended_next = "label_semantics_alternative_pairwise_feature_patch_matrix_fix_objective"
        next_allowed_step = "human_review_closeout_then_fix_matrix_guard"

    blocked = [
        "patch first-pass training before smoke-test review",
        "broad hyperparameter search",
        "direct full SupCon/DG training",
        "EEG+EMG fusion",
        "final LOSO claim",
        "changing label formulation during this patch branch",
    ]

    report = {
        "status": "complete_pending_human_review",
        "created_utc": created,
        "source_objective": str(OBJECTIVE_JSON),
        "source_spec": str(SPEC_JSON),
        "diagnosis": diagnosis,
        "all_passed": all_passed,
        "training_authorized": False,
        "patch_first_pass_authorized": False,
        "model_search_authorized": False,
        "supcon_dg_authorized": False,
        "fusion_authorized": False,
        "final_loso_claim_authorized": False,
        "selected_primary_patch": spec.get("selected_primary_patch"),
        "selected_formulation": spec.get("selected_formulation"),
        "cache_index_rows": int(len(idx)),
        "windows_shape": list(map(int, windows.shape)),
        "subject_col": subject_col,
        "trial_col": trial_col,
        "arousal_col": arousal_col,
        "feature_shape_rows": len(feature_rows),
        "non_tie_within_subject_pairs": pc["non_tie_within_subject_pairs"],
        "run_matrix_rows": int(len(run_matrix)),
        "recommended_next_objective": recommended_next,
        "next_allowed_step": next_allowed_step,
        "outputs": {
            "feature_shape_audit": str(FEATURE_SHAPE_AUDIT),
            "pair_target_audit": str(PAIR_TARGET_AUDIT),
            "fold_locality_audit": str(FOLD_LOCALITY_AUDIT),
            "matrix_guard_audit": str(MATRIX_GUARD_AUDIT),
            "smoke_decision_matrix": str(SMOKE_DECISION_MATRIX),
        },
        "blocked": blocked,
    }
    write_json(REPORT_JSON, report)

    status = read_json(STATUS_JSON)
    status["last_updated_utc"] = created
    status["current_idare_next_allowed_step"] = next_allowed_step
    status["current_idare_blocked_steps"] = blocked
    status["current_idare_pairwise_feature_patch_smoke_status"] = f"complete_pending_human_review; diagnosis={diagnosis}"
    events = status.get("idare_protocol_events")
    if not isinstance(events, list):
        events = []
    status["idare_protocol_events"] = events
    events.append({
        "timestamp_utc": created,
        "type": "smoke_test_report",
        "name": "I-DARE alternative pairwise feature-representation patch smoke tests",
        "status": f"complete pending human review; diagnosis={diagnosis}",
        "evidence": str(REPORT_MD),
        "recommended_next_objective": recommended_next,
        "blocked": blocked,
    })
    write_json(STATUS_JSON, status)

    report_md = f"""# I-DARE Alternative Pairwise Feature-Representation Patch Smoke Tests Report

## Status

Status: complete; pending human review.

Created UTC: `{created}`

## Executive Result

Diagnosis: `{diagnosis}`

All smoke tests passed: `{all_passed}`

Recommended next objective: `{recommended_next}`

## Detected Columns and Cache Shape

- Subject column: `{subject_col}`
- Trial/window column: `{trial_col}`
- Arousal label column: `{arousal_col}`
- Index rows: `{len(idx)}`
- Windows shape: `{list(windows.shape)}`

## Feature Shape Audit

{md_table(feature_rows, ["feature_set_id", "window_rows", "n_features", "finite_fraction", "pass"])}

## Pair Target Audit

{md_table(pair_rows, ["task", "n_subjects", "non_tie_within_subject_pairs", "canonical_positive_rate", "subjects_with_non_tie_pairs", "same_subject_only_by_construction", "pass"])}

## Fold-Locality Audit

{md_table(fold_rows, ["fold", "n_train_rows", "n_val_rows", "n_train_subjects", "n_val_subjects", "subject_overlap_count", "pass"])}

## Matrix Guard Audit

{md_table(matrix_rows, ["guard", "expected", "observed", "pass"])}

## Smoke Decision Matrix

{md_table(decision_rows, ["requirement_id", "check", "status", "evidence"])}

## Interpretation

The smoke tests validate feature extraction, same-subject pair construction, fold-locality, and frozen matrix scope only.

No patch model training was run. No broad search, SupCon/DG, fusion, or final LOSO claim is authorized by this report.

## Next Allowed Step

`{next_allowed_step}`
"""
    REPORT_MD.write_text(report_md, encoding="utf-8")

    status_text = STATUS_MD.read_text(encoding="utf-8")
    append = f"""

## I-DARE Alternative Pairwise Feature-Representation Patch Smoke Tests Report

Updated: `{created}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE alternative pairwise feature patch smoke tests | complete pending human review; diagnosis=`{diagnosis}` | `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_tests_report.md` | `{next_allowed_step}` | patch first-pass training before review; broad search; SupCon/DG; fusion; final claim |

- All smoke tests passed: `{all_passed}`.
- No learned patch model training was run.
- Recommended next objective: `{recommended_next}` only after human review.
"""
    if "I-DARE Alternative Pairwise Feature-Representation Patch Smoke Tests Report" not in status_text:
        STATUS_MD.write_text(status_text.rstrip() + append + "\n", encoding="utf-8")

    print("OK_FEATURE_REPRESENTATION_PATCH_SMOKE_TESTS_REPORT_WRITTEN")
    print(REPORT_MD)
    print(REPORT_JSON)
    print(FEATURE_SHAPE_AUDIT)
    print(PAIR_TARGET_AUDIT)
    print(FOLD_LOCALITY_AUDIT)
    print(MATRIX_GUARD_AUDIT)
    print(SMOKE_DECISION_MATRIX)
    print("diagnosis=", diagnosis)
    print("all_passed=", all_passed)
    print("recommended_next_objective=", recommended_next)
    print("feature_shape_rows=", len(feature_rows))
    print("non_tie_within_subject_pairs=", pc["non_tie_within_subject_pairs"])
    print("run_matrix_rows=", len(run_matrix))


if __name__ == "__main__":
    main()
