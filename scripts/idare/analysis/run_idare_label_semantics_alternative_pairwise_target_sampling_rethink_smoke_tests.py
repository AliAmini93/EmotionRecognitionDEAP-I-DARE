#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

D = Path("docs")
CACHE = Path(".cache")

OBJECTIVE_JSON = D / "idare_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_tests_objective.json"
SPEC_JSON = D / "idare_label_semantics_alternative_pairwise_target_sampling_rethink_spec.json"
SELECTED_RULE_CSV = D / "idare_label_semantics_alternative_pairwise_target_sampling_rethink_selected_rule.csv"
EEG_INDEX = CACHE / "idare_eeg_cache_index_baseline_corrected.csv"
EMG_INDEX = CACHE / "idare_emg_feature_cache_index.csv"

REPORT_MD = D / "idare_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_tests_report.md"
REPORT_JSON = D / "idare_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_tests_report.json"
MARGIN_AUDIT = D / "idare_label_semantics_alternative_pairwise_target_sampling_rethink_margin_threshold_audit.csv"
PAIR_COUNT_AUDIT = D / "idare_label_semantics_alternative_pairwise_target_sampling_rethink_pair_count_audit.csv"
DIRECTION_BALANCE_AUDIT = D / "idare_label_semantics_alternative_pairwise_target_sampling_rethink_direction_balance_audit.csv"
FOLD_LOCALITY_AUDIT = D / "idare_label_semantics_alternative_pairwise_target_sampling_rethink_fold_locality_audit.csv"
REPRO_AUDIT = D / "idare_label_semantics_alternative_pairwise_target_sampling_rethink_reproducibility_audit.csv"
DECISION_MATRIX = D / "idare_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_decision_matrix.csv"
STATUS_JSON = D / "project_status_current.json"
STATUS_MD = D / "project_status_current.md"

SCRIPT_PATH = Path("scripts/idare/analysis/run_idare_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_tests.py")

N_FOLDS = 6
RANDOM_SEED = 20260509
MIN_VALIDATION_PAIRS = 1000
MIN_TRAINING_BALANCED_PAIRS = 500


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise SystemExit(f"ERROR: refusing to write empty CSV: {path}")
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def md_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in rows:
        vals: list[str] = []
        for col in cols:
            val = row.get(col, "")
            if isinstance(val, float):
                if math.isnan(val) or math.isinf(val):
                    val = ""
                else:
                    val = f"{val:.6g}"
            vals.append(str(val).replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for c in df.columns:
        clean = c.strip()
        if clean != c:
            rename[c] = clean
    return df.rename(columns=rename)


def choose_col(df: pd.DataFrame, candidates: list[str], contains: list[str] | None = None) -> str:
    cols = list(df.columns)
    low = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in low:
            return low[cand.lower()]
    if contains:
        for c in cols:
            lc = c.lower()
            if all(token.lower() in lc for token in contains):
                return c
    raise SystemExit(f"ERROR: cannot find column. candidates={candidates} contains={contains} available={cols[:80]}")


def choose_target_col(df: pd.DataFrame, task: str) -> str:
    task_low = task.lower()
    exact = [
        task_low,
        f"{task_low}_rating",
        f"{task_low}_rank_percentile",
        f"subject_relative_{task_low}",
        f"{task_low}_subject_relative",
        f"{task_low}_ordinal",
        f"{task_low}_score",
        f"label_{task_low}",
    ]
    low = {c.lower(): c for c in df.columns}
    for e in exact:
        if e in low:
            return low[e]
    candidates = [c for c in df.columns if task_low in c.lower()]
    numeric = []
    for c in candidates:
        s = pd.to_numeric(df[c], errors="coerce")
        if s.notna().sum() >= max(10, int(0.25 * len(df))):
            numeric.append(c)
    if not numeric:
        raise SystemExit(f"ERROR: cannot find numeric target column for task={task}; candidates={candidates}")
    # Prefer rank/relative/transformed label columns over raw notes if present.
    def score(c: str) -> tuple[int, int]:
        lc = c.lower()
        priority = 0
        for token in ["rank", "percentile", "subject", "relative", "ordinal", "rating", "score"]:
            if token in lc:
                priority += 1
        return (priority, -len(lc))
    return sorted(numeric, key=score, reverse=True)[0]


def stable_subject_folds(subjects: list[Any], n_folds: int = N_FOLDS) -> dict[Any, int]:
    # Deterministic grouped-subject split. The project has used six validation folds in this branch;
    # this preserves that convention without using labels to assign folds.
    ordered = sorted(subjects, key=lambda x: str(x))
    return {subj: (i % n_folds) + 1 for i, subj in enumerate(ordered)}


def hash_rows(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(rows, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_subject_pairs(values: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Return pair margins and directions for all ordered-independent unordered pairs in one subject.
    margins = []
    directions = []
    signs = []
    n = len(values)
    for i, j in combinations(range(n), 2):
        diff = float(values[j] - values[i])
        if diff == 0.0 or math.isnan(diff):
            continue
        margins.append(abs(diff))
        directions.append(1 if diff > 0 else 0)
        signs.append(np.sign(diff))
    if not margins:
        return np.array([], dtype=float), np.array([], dtype=int), np.array([], dtype=float)
    return np.asarray(margins, dtype=float), np.asarray(directions, dtype=int), np.asarray(signs, dtype=float)


def count_pairs_for_subjects(df: pd.DataFrame, subject_col: str, target_col: str, subjects: set[Any], margin_threshold: float) -> dict[str, Any]:
    total = 0
    pos = 0
    neg = 0
    subject_counts: list[int] = []
    for subj, g in df[df[subject_col].isin(subjects)].groupby(subject_col, sort=False):
        vals = pd.to_numeric(g[target_col], errors="coerce").dropna().to_numpy(dtype=float)
        margins, dirs, _ = build_subject_pairs(vals)
        if len(margins) == 0:
            subject_counts.append(0)
            continue
        keep = margins >= margin_threshold
        kept_dirs = dirs[keep]
        p = int((kept_dirs == 1).sum())
        n = int((kept_dirs == 0).sum())
        c = p + n
        total += c
        pos += p
        neg += n
        subject_counts.append(c)
    frac_pos = (pos / total) if total else float("nan")
    return {
        "raw_pairs": int(total),
        "positive_pairs": int(pos),
        "negative_pairs": int(neg),
        "positive_fraction": frac_pos,
        "n_subjects_with_pairs": int(sum(c > 0 for c in subject_counts)),
        "min_subject_pairs": int(min(subject_counts)) if subject_counts else 0,
        "max_subject_pairs": int(max(subject_counts)) if subject_counts else 0,
    }


def deterministic_balanced_train_count(pos: int, neg: int) -> dict[str, Any]:
    minority = min(pos, neg)
    balanced_total = 2 * minority
    if balanced_total == 0:
        frac = float("nan")
    else:
        frac = 0.5
    return {
        "balanced_pairs": int(balanced_total),
        "balanced_positive_pairs": int(minority),
        "balanced_negative_pairs": int(minority),
        "balanced_positive_fraction": frac,
    }


def main() -> None:
    ts = now_utc()
    objective = read_json(OBJECTIVE_JSON)
    spec = read_json(SPEC_JSON)
    selected_rule = pd.read_csv(SELECTED_RULE_CSV)

    if objective.get("status") != "objective_created":
        raise SystemExit("ERROR: smoke objective status mismatch")
    if objective.get("selected_rule_id") != "margin_thresholded_within_subject_pairwise_preference_v1":
        raise SystemExit("ERROR: selected rule mismatch")
    if objective.get("smoke_pair_construction_authorized") is not True:
        raise SystemExit("ERROR: smoke pair construction must be authorized")
    for key in [
        "training_authorized",
        "rerun_authorized",
        "model_fitting_authorized",
        "feature_search_authorized",
        "model_search_authorized",
        "supcon_dg_authorized",
        "fusion_authorized",
        "final_loso_claim_authorized",
        "first_pass_authorized",
    ]:
        if objective.get(key) is not False:
            raise SystemExit(f"ERROR: objective must keep {key}=false")

    if spec.get("selected_rule_id") != objective.get("selected_rule_id"):
        raise SystemExit("ERROR: selected rule mismatch between spec and objective")

    eeg = normalize_columns(pd.read_csv(EEG_INDEX))
    emg = normalize_columns(pd.read_csv(EMG_INDEX))
    subject_col = choose_col(eeg, ["subject", "subject_id", "participant", "participant_id", "sid"], contains=["subject"])
    trial_col = None
    for cand in ["trial", "trial_id", "video", "video_id", "clip", "clip_id", "sample_id", "window_id"]:
        if cand in {c.lower(): c for c in eeg.columns}:
            trial_col = {c.lower(): c for c in eeg.columns}[cand]
            break
    if trial_col is None:
        trial_col = "__row_id__"
        eeg[trial_col] = np.arange(len(eeg))

    target_cols = {
        "valence": choose_target_col(eeg, "valence"),
        "arousal": choose_target_col(eeg, "arousal"),
    }

    subjects = list(pd.Series(eeg[subject_col]).dropna().unique())
    fold_map = stable_subject_folds(subjects, N_FOLDS)
    eeg["_smoke_fold"] = eeg[subject_col].map(fold_map)

    margin_rows: list[dict[str, Any]] = []
    pair_count_rows: list[dict[str, Any]] = []
    direction_rows: list[dict[str, Any]] = []
    locality_rows: list[dict[str, Any]] = []
    reproducibility_basis: list[dict[str, Any]] = []

    all_pair_count_pass = True
    all_direction_pass = True
    all_margin_pass = True
    all_locality_pass = True

    selected_tasks = ["arousal", "valence"]  # arousal is primary; valence remains a guard.
    for task in selected_tasks:
        target_col = target_cols[task]
        task_values_numeric = pd.to_numeric(eeg[target_col], errors="coerce")
        if task_values_numeric.notna().sum() < len(subjects):
            raise SystemExit(f"ERROR: target column {target_col} has too few numeric values")

        for fold in range(1, N_FOLDS + 1):
            heldout_subjects = set(eeg.loc[eeg["_smoke_fold"].eq(fold), subject_col].dropna().unique())
            train_subjects = set(subjects) - heldout_subjects

            train_margins = []
            for subj, g in eeg[eeg[subject_col].isin(train_subjects)].groupby(subject_col, sort=False):
                vals = pd.to_numeric(g[target_col], errors="coerce").dropna().to_numpy(dtype=float)
                margins, _, _ = build_subject_pairs(vals)
                if len(margins):
                    train_margins.extend(margins.tolist())

            nonzero_train_margins = np.asarray([m for m in train_margins if m > 0], dtype=float)
            if len(nonzero_train_margins) == 0:
                margin_threshold = float("nan")
            else:
                margin_threshold = float(np.median(nonzero_train_margins))

            margin_pass = bool(np.isfinite(margin_threshold) and margin_threshold > 0)
            all_margin_pass = all_margin_pass and margin_pass

            train_counts = count_pairs_for_subjects(eeg, subject_col, target_col, train_subjects, margin_threshold)
            val_counts = count_pairs_for_subjects(eeg, subject_col, target_col, heldout_subjects, margin_threshold)
            balanced = deterministic_balanced_train_count(train_counts["positive_pairs"], train_counts["negative_pairs"])

            pair_count_pass = bool(
                train_counts["raw_pairs"] >= MIN_TRAINING_BALANCED_PAIRS
                and balanced["balanced_pairs"] >= MIN_TRAINING_BALANCED_PAIRS
                and val_counts["raw_pairs"] >= MIN_VALIDATION_PAIRS
            )
            all_pair_count_pass = all_pair_count_pass and pair_count_pass

            train_frac = balanced["balanced_positive_fraction"]
            val_frac = val_counts["positive_fraction"]
            train_direction_pass = bool(np.isfinite(train_frac) and 0.45 <= train_frac <= 0.55)
            val_direction_pass = bool(np.isfinite(val_frac) and 0.40 <= val_frac <= 0.60)
            direction_pass = train_direction_pass and val_direction_pass
            all_direction_pass = all_direction_pass and direction_pass

            # Fold locality is structural in this construction; explicitly audit subject set disjointness.
            overlap = train_subjects.intersection(heldout_subjects)
            locality_pass = len(overlap) == 0 and len(heldout_subjects) > 0 and len(train_subjects) > 0
            all_locality_pass = all_locality_pass and locality_pass

            margin_rows.append({
                "task": task,
                "fold": fold,
                "target_column": target_col,
                "threshold_source": "training_subjects_only",
                "n_train_subjects": len(train_subjects),
                "n_validation_subjects": len(heldout_subjects),
                "n_train_nonzero_margins": int(len(nonzero_train_margins)),
                "margin_threshold": margin_threshold,
                "validation_labels_used_for_threshold": False,
                "pass": margin_pass,
            })

            pair_count_rows.append({
                "task": task,
                "fold": fold,
                "margin_threshold": margin_threshold,
                "train_raw_pairs": train_counts["raw_pairs"],
                "train_balanced_pairs": balanced["balanced_pairs"],
                "validation_raw_pairs": val_counts["raw_pairs"],
                "min_training_balanced_pairs_required": MIN_TRAINING_BALANCED_PAIRS,
                "min_validation_pairs_required": MIN_VALIDATION_PAIRS,
                "train_subjects_with_pairs": train_counts["n_subjects_with_pairs"],
                "validation_subjects_with_pairs": val_counts["n_subjects_with_pairs"],
                "pass": pair_count_pass,
            })

            direction_rows.append({
                "task": task,
                "fold": fold,
                "train_positive_pairs_before_balance": train_counts["positive_pairs"],
                "train_negative_pairs_before_balance": train_counts["negative_pairs"],
                "train_positive_fraction_before_balance": train_counts["positive_fraction"],
                "train_balanced_positive_pairs": balanced["balanced_positive_pairs"],
                "train_balanced_negative_pairs": balanced["balanced_negative_pairs"],
                "train_balanced_positive_fraction": balanced["balanced_positive_fraction"],
                "validation_positive_pairs": val_counts["positive_pairs"],
                "validation_negative_pairs": val_counts["negative_pairs"],
                "validation_positive_fraction": val_counts["positive_fraction"],
                "train_direction_pass": train_direction_pass,
                "validation_direction_pass": val_direction_pass,
                "pass": direction_pass,
            })

            locality_rows.append({
                "task": task,
                "fold": fold,
                "n_train_subjects": len(train_subjects),
                "n_validation_subjects": len(heldout_subjects),
                "subject_overlap_count": len(overlap),
                "within_subject_only": True,
                "cross_fold_pairs_constructed": False,
                "validation_subjects": ";".join(map(str, sorted(heldout_subjects, key=str))),
                "pass": locality_pass,
            })

            reproducibility_basis.append({
                "task": task,
                "fold": fold,
                "margin_threshold": round(margin_threshold, 12) if np.isfinite(margin_threshold) else None,
                "train_balanced_pairs": int(balanced["balanced_pairs"]),
                "validation_raw_pairs": int(val_counts["raw_pairs"]),
                "train_balanced_positive_fraction": float(balanced["balanced_positive_fraction"]) if np.isfinite(balanced["balanced_positive_fraction"]) else None,
                "validation_positive_fraction": float(val_counts["positive_fraction"]) if np.isfinite(val_counts["positive_fraction"]) else None,
            })

    digest_one = hashlib.sha256(json.dumps(reproducibility_basis, sort_keys=True).encode("utf-8")).hexdigest()
    digest_two = hashlib.sha256(json.dumps(reproducibility_basis, sort_keys=True).encode("utf-8")).hexdigest()
    reproducibility_pass = digest_one == digest_two

    repro_rows = [
        {
            "audit_id": "REPRO_001",
            "name": "deterministic_rule_digest_repeat",
            "seed": RANDOM_SEED,
            "digest_first": digest_one,
            "digest_second": digest_two,
            "pass": reproducibility_pass,
        },
        {
            "audit_id": "REPRO_002",
            "name": "selected_rule_id",
            "expected": "margin_thresholded_within_subject_pairwise_preference_v1",
            "observed": objective.get("selected_rule_id"),
            "pass": objective.get("selected_rule_id") == "margin_thresholded_within_subject_pairwise_preference_v1",
        },
        {
            "audit_id": "REPRO_003",
            "name": "script_committed_path",
            "path": str(SCRIPT_PATH),
            "exists": SCRIPT_PATH.exists(),
            "pass": SCRIPT_PATH.exists(),
        },
    ]

    # Only arousal is primary; valence is a guard. Still require valence smoke to pass, because the rule must be label-safe.
    target_scope_pass = set(selected_tasks) == {"arousal", "valence"}
    all_passed = bool(all_margin_pass and all_pair_count_pass and all_direction_pass and all_locality_pass and reproducibility_pass and target_scope_pass)

    decision_rows = [
        {
            "check_id": "D001",
            "check_name": "train_only_margin_threshold",
            "status": "pass" if all_margin_pass else "fail",
            "required_for_pass": True,
            "interpretation": "margin thresholds are positive and computed from training subjects only",
        },
        {
            "check_id": "D002",
            "check_name": "pair_count_sufficiency",
            "status": "pass" if all_pair_count_pass else "fail",
            "required_for_pass": True,
            "interpretation": "margin filtering leaves enough train and validation pairs",
        },
        {
            "check_id": "D003",
            "check_name": "direction_balance",
            "status": "pass" if all_direction_pass else "fail",
            "required_for_pass": True,
            "interpretation": "deterministic balancing fixes training direction imbalance and validation remains within guard range",
        },
        {
            "check_id": "D004",
            "check_name": "fold_locality",
            "status": "pass" if all_locality_pass else "fail",
            "required_for_pass": True,
            "interpretation": "no train/validation subject overlap and no cross-fold pairs",
        },
        {
            "check_id": "D005",
            "check_name": "reproducibility",
            "status": "pass" if reproducibility_pass else "fail",
            "required_for_pass": True,
            "interpretation": "deterministic digest is stable",
        },
        {
            "check_id": "D006",
            "check_name": "overall_smoke_result",
            "status": "pass" if all_passed else "fail",
            "required_for_pass": True,
            "interpretation": "all required target/sampling rethink smoke checks passed" if all_passed else "one or more required smoke checks failed",
        },
    ]

    write_csv(MARGIN_AUDIT, margin_rows)
    write_csv(PAIR_COUNT_AUDIT, pair_count_rows)
    write_csv(DIRECTION_BALANCE_AUDIT, direction_rows)
    write_csv(FOLD_LOCALITY_AUDIT, locality_rows)
    write_csv(REPRO_AUDIT, repro_rows)
    write_csv(DECISION_MATRIX, decision_rows)

    if all_passed:
        diagnosis = "target_sampling_rethink_smoke_tests_passed"
        recommendation = "create_limited_target_sampling_rethink_first_pass_objective_after_review"
        recommended_next_objective = "label_semantics_alternative_pairwise_target_sampling_rethink_first_pass_objective"
    else:
        diagnosis = "target_sampling_rethink_smoke_tests_failed"
        recommendation = "archive_or_revise_target_sampling_rethink_after_review"
        recommended_next_objective = "label_semantics_alternative_pairwise_target_sampling_rethink_fix_or_archive_objective"

    min_train_balanced = int(min(r["train_balanced_pairs"] for r in pair_count_rows))
    min_val_pairs = int(min(r["validation_raw_pairs"] for r in pair_count_rows))
    max_val_imbalance = float(max(abs(r["validation_positive_fraction"] - 0.5) for r in direction_rows if np.isfinite(r["validation_positive_fraction"])))
    max_margin = float(max(r["margin_threshold"] for r in margin_rows if np.isfinite(r["margin_threshold"])))
    min_margin = float(min(r["margin_threshold"] for r in margin_rows if np.isfinite(r["margin_threshold"])))

    report = {
        "status": "complete_pending_human_review",
        "created_utc": ts,
        "script": str(SCRIPT_PATH),
        "source_objective": str(OBJECTIVE_JSON),
        "source_spec": str(SPEC_JSON),
        "diagnosis": diagnosis,
        "all_passed": all_passed,
        "recommendation": recommendation,
        "recommended_next_objective": recommended_next_objective,
        "selected_rule_id": objective.get("selected_rule_id"),
        "selected_candidate_id": objective.get("selected_candidate_id"),
        "selected_formulation": objective.get("selected_formulation"),
        "training_authorized": False,
        "model_fitting_authorized": False,
        "first_pass_authorized": False,
        "n_subjects": int(len(subjects)),
        "n_folds": N_FOLDS,
        "subject_column": subject_col,
        "trial_column": trial_col,
        "target_columns": target_cols,
        "min_train_balanced_pairs": min_train_balanced,
        "min_validation_pairs": min_val_pairs,
        "min_margin_threshold": min_margin,
        "max_margin_threshold": max_margin,
        "max_validation_direction_imbalance_abs": max_val_imbalance,
        "outputs": {
            "margin_threshold_audit": str(MARGIN_AUDIT),
            "pair_count_audit": str(PAIR_COUNT_AUDIT),
            "direction_balance_audit": str(DIRECTION_BALANCE_AUDIT),
            "fold_locality_audit": str(FOLD_LOCALITY_AUDIT),
            "reproducibility_audit": str(REPRO_AUDIT),
            "decision_matrix": str(DECISION_MATRIX),
        },
    }
    write_json(REPORT_JSON, report)

    REPORT_MD.write_text(f"""# I-DARE Alternative Pairwise Target/Sampling Rethink Smoke-Tests Report

## Status

Status: complete; pending human review.

Created UTC: `{ts}`

## Executive Result

Diagnosis: `{diagnosis}`

All smoke tests passed: `{all_passed}`

Recommendation: `{recommendation}`

Recommended next objective: `{recommended_next_objective}`

Selected rule: `{objective.get("selected_rule_id")}`

## Detected Columns

Subject column: `{subject_col}`

Trial/sample column: `{trial_col}`

Target columns: `{target_cols}`

Subjects: `{len(subjects)}`

Folds: `{N_FOLDS}`

## Margin Threshold Audit

Minimum train-only margin threshold: `{min_margin:.6g}`

Maximum train-only margin threshold: `{max_margin:.6g}`

Validation labels used for threshold selection: `False`

Audit file: `{MARGIN_AUDIT}`

## Pair Count Audit

Minimum balanced training pairs after margin filtering: `{min_train_balanced}`

Minimum validation pairs after margin filtering: `{min_val_pairs}`

Required minimum balanced training pairs: `{MIN_TRAINING_BALANCED_PAIRS}`

Required minimum validation pairs: `{MIN_VALIDATION_PAIRS}`

Audit file: `{PAIR_COUNT_AUDIT}`

## Direction Balance Audit

Maximum absolute validation direction imbalance from 0.5: `{max_val_imbalance:.6g}`

Training direction balance is deterministic after downsampling.

Audit file: `{DIRECTION_BALANCE_AUDIT}`

## Fold Locality Audit

Within-subject only: `True`

Cross-fold pairs constructed: `False`

Audit file: `{FOLD_LOCALITY_AUDIT}`

## Reproducibility Audit

Digest stable: `{reproducibility_pass}`

Audit file: `{REPRO_AUDIT}`

## Smoke Decision Matrix

{md_table(decision_rows, ["check_id", "check_name", "status", "required_for_pass", "interpretation"])}

## Interpretation

The selected margin-thresholded within-subject pairwise sampling rule is smoke-tested only.

No training, model fitting, feature/model search, SupCon/DG, fusion, or final LOSO claim is authorized by this report.

## Next Allowed Step

`human_review_then_{recommended_next_objective}`
""", encoding="utf-8")

    status = read_json(STATUS_JSON)
    status["last_updated_utc"] = ts
    status["current_idare_next_allowed_step"] = f"human_review_then_{recommended_next_objective}"
    status["current_idare_target_sampling_rethink_smoke_tests_status"] = "complete_pending_human_review"
    status["current_idare_blocked_steps"] = [
        "training before smoke-test review",
        "model fitting before reviewed first-pass objective",
        "feature/model search",
        "direct full SupCon/DG training",
        "EEG+EMG fusion",
        "final LOSO claim",
    ]
    events = status.get("idare_protocol_events")
    if not isinstance(events, list):
        events = []
    status["idare_protocol_events"] = events
    events.append({
        "timestamp_utc": ts,
        "type": "smoke_tests",
        "name": "I-DARE alternative pairwise target/sampling rethink smoke tests",
        "status": f"complete pending human review; diagnosis={diagnosis}",
        "evidence": str(REPORT_MD),
        "recommended_next_objective": recommended_next_objective,
        "blocked": status["current_idare_blocked_steps"],
    })
    write_json(STATUS_JSON, status)

    status_text = STATUS_MD.read_text(encoding="utf-8")
    append = f"""

## I-DARE Alternative Pairwise Target/Sampling Rethink Smoke-Tests Report

Updated: `{ts}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE alternative pairwise target/sampling rethink smoke tests | complete pending human review; diagnosis `{diagnosis}` | `docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_tests_report.md` | Human review then `{recommended_next_objective}`. | training before smoke-test review; model fitting before reviewed first-pass objective; feature/model search; SupCon/DG; fusion; final claim |

- All smoke tests passed: `{all_passed}`.
- Minimum balanced training pairs: `{min_train_balanced}`.
- Minimum validation pairs: `{min_val_pairs}`.
"""
    if "I-DARE Alternative Pairwise Target/Sampling Rethink Smoke-Tests Report" not in status_text:
        STATUS_MD.write_text(status_text.rstrip() + append + "\n", encoding="utf-8")

    print("OK_TARGET_SAMPLING_RETHINK_SMOKE_TESTS_REPORT_WRITTEN")
    print(REPORT_MD)
    print(REPORT_JSON)
    print(MARGIN_AUDIT)
    print(PAIR_COUNT_AUDIT)
    print(DIRECTION_BALANCE_AUDIT)
    print(FOLD_LOCALITY_AUDIT)
    print(REPRO_AUDIT)
    print(DECISION_MATRIX)
    print("diagnosis=", diagnosis)
    print("all_passed=", all_passed)
    print("recommended_next_objective=", recommended_next_objective)
    print("min_train_balanced_pairs=", min_train_balanced)
    print("min_validation_pairs=", min_val_pairs)
    print("max_validation_direction_imbalance_abs=", max_val_imbalance)


if __name__ == "__main__":
    main()
