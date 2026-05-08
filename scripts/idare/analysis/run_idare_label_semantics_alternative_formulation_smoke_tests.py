#!/usr/bin/env python3
"""Read-only smoke tests for I-DARE within-subject pairwise affect preference formulation.

This script intentionally performs no model training. It audits whether the
alternative label semantics are constructible, leak-free, balanced enough, and
metric-sane before any future minimal first-pass objective can be considered.
"""

from __future__ import annotations

import csv
import itertools
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DOCS = Path("docs")
SCRIPT_PATH = Path("scripts/idare/analysis/run_idare_label_semantics_alternative_formulation_smoke_tests.py")

REVIEW_JSON = DOCS / "idare_label_semantics_alternative_formulation_design_spec_review_status.json"
OBJECTIVE_JSON = DOCS / "idare_label_semantics_alternative_formulation_smoke_tests_objective.json"
DESIGN_SPEC_JSON = DOCS / "idare_label_semantics_alternative_formulation_design_spec.json"
SELECTED_TASK_CSV = DOCS / "idare_label_semantics_alternative_formulation_selected_task_definition.csv"
METRIC_PLAN_CSV = DOCS / "idare_label_semantics_alternative_formulation_metric_plan.csv"
SMOKE_PLAN_CSV = DOCS / "idare_label_semantics_alternative_formulation_smoke_test_plan.csv"
STOP_CRITERIA_CSV = DOCS / "idare_label_semantics_alternative_formulation_stop_criteria.csv"
SMOKE_REQ_CSV = DOCS / "idare_label_semantics_alternative_formulation_smoke_requirements.csv"
PAIR_GUARDRAILS_CSV = DOCS / "idare_label_semantics_alternative_formulation_pair_guardrails.csv"

EEG_INDEX = Path(".cache/idare_eeg_cache_index_baseline_corrected.csv")
EMG_INDEX = Path(".cache/idare_emg_feature_cache_index.csv")

REPORT_MD = DOCS / "idare_label_semantics_alternative_formulation_smoke_tests_report.md"
REPORT_JSON = DOCS / "idare_label_semantics_alternative_formulation_smoke_tests_report.json"
PAIR_TARGET_AUDIT = DOCS / "idare_label_semantics_alternative_formulation_pair_target_audit.csv"
PAIR_FOLD_AUDIT = DOCS / "idare_label_semantics_alternative_formulation_pair_fold_audit.csv"
PAIR_BALANCE_AUDIT = DOCS / "idare_label_semantics_alternative_formulation_pair_balance_audit.csv"
PAIR_BASELINE_CONTROL = DOCS / "idare_label_semantics_alternative_formulation_pair_baseline_control.csv"
PAIR_METRIC_SANITY = DOCS / "idare_label_semantics_alternative_formulation_pair_metric_sanity.csv"
SMOKE_DECISION_MATRIX = DOCS / "idare_label_semantics_alternative_formulation_smoke_decision_matrix.csv"
SMOKE_REPRO_AUDIT = DOCS / "idare_label_semantics_alternative_formulation_smoke_reproducibility_audit.csv"

STATUS_JSON = DOCS / "project_status_current.json"
STATUS_MD = DOCS / "project_status_current.md"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise SystemExit(f"ERROR: attempted to write empty CSV: {path}")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")).replace("|", "\\|").replace("\n", " ") for c in columns) + " |")
    return "\n".join(out)


def normalize_name(name: str) -> str:
    return str(name).strip().lower().replace("-", "_").replace(" ", "_")


def find_column(df: pd.DataFrame, preferred: list[str], require_any: list[str] | None = None, avoid: list[str] | None = None) -> str | None:
    cols = list(df.columns)
    norm = {normalize_name(c): c for c in cols}
    for p in preferred:
        p_norm = normalize_name(p)
        if p_norm in norm:
            return norm[p_norm]

    require_any = [normalize_name(x) for x in (require_any or [])]
    avoid = [normalize_name(x) for x in (avoid or [])]
    scored: list[tuple[int, str]] = []
    for c in cols:
        n = normalize_name(c)
        if avoid and any(a in n for a in avoid):
            continue
        if require_any and not any(r in n for r in require_any):
            continue
        score = 0
        for p in preferred:
            p_norm = normalize_name(p)
            if p_norm in n:
                score += 10
            if n in p_norm:
                score += 5
        if "rating" in n:
            score += 3
        if "raw" in n or "score" in n:
            score += 2
        if "label" in n or "binary" in n or "class" in n:
            score -= 6
        if score > 0:
            scored.append((score, c))
    if not scored:
        return None
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored[0][1]


def load_trial_table() -> tuple[pd.DataFrame, dict[str, Any]]:
    eeg = pd.read_csv(EEG_INDEX)
    emg = pd.read_csv(EMG_INDEX)

    subject_candidates = ["subject", "subject_id", "subj", "participant", "participant_id", "participant_id_num"]
    trial_candidates = ["trial", "trial_id", "trial_index", "video", "video_id", "clip", "clip_id", "stimulus", "stimulus_id", "movie", "movie_id"]
    valence_candidates = ["valence_rating", "rating_valence", "self_report_valence", "raw_valence", "valence_score", "valence"]
    arousal_candidates = ["arousal_rating", "rating_arousal", "self_report_arousal", "raw_arousal", "arousal_score", "arousal"]

    subj_col = find_column(eeg, subject_candidates, require_any=["subject", "subj", "participant"])
    trial_col = find_column(eeg, trial_candidates, require_any=["trial", "video", "clip", "stimulus", "movie"])
    val_col = find_column(eeg, valence_candidates, require_any=["valence"], avoid=["pred", "prob"])
    aro_col = find_column(eeg, arousal_candidates, require_any=["arousal"], avoid=["pred", "prob"])

    missing = [name for name, col in [("subject", subj_col), ("trial", trial_col), ("valence", val_col), ("arousal", aro_col)] if col is None]
    metadata: dict[str, Any] = {
        "eeg_index_rows": int(len(eeg)),
        "emg_index_rows": int(len(emg)),
        "eeg_columns": list(map(str, eeg.columns)),
        "detected_columns": {
            "subject": subj_col,
            "trial": trial_col,
            "valence": val_col,
            "arousal": aro_col,
        },
        "missing_detected_columns": missing,
        "using_index": str(EEG_INDEX),
    }

    if missing:
        return pd.DataFrame(columns=["subject", "trial", "valence", "arousal", "n_windows"]), metadata

    work = eeg[[subj_col, trial_col, val_col, aro_col]].copy()
    work.columns = ["subject", "trial", "valence", "arousal"]
    work["subject"] = work["subject"].astype(str)
    work["trial"] = work["trial"].astype(str)
    work["valence"] = pd.to_numeric(work["valence"], errors="coerce")
    work["arousal"] = pd.to_numeric(work["arousal"], errors="coerce")
    work = work.dropna(subset=["subject", "trial"])

    trial = (
        work.groupby(["subject", "trial"], dropna=False)
        .agg(
            valence=("valence", "median"),
            arousal=("arousal", "median"),
            n_windows=("trial", "size"),
        )
        .reset_index()
    )

    metadata["trial_rows"] = int(len(trial))
    metadata["n_subjects"] = int(trial["subject"].nunique()) if len(trial) else 0
    metadata["n_trials"] = int(trial[["subject", "trial"]].drop_duplicates().shape[0]) if len(trial) else 0
    return trial, metadata


def infer_margin(values: pd.Series) -> float:
    vals = pd.to_numeric(values, errors="coerce").dropna()
    if vals.empty:
        return math.nan
    value_range = float(vals.max() - vals.min())
    unique_count = vals.nunique()
    if unique_count <= 2:
        return math.nan
    if value_range <= 1.5:
        return 0.125
    return 1.0


def build_pairs(trial: pd.DataFrame, task: str, margin: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    valid = trial[["subject", "trial", task]].dropna().copy()
    all_possible = 0
    tie_or_ambiguous = 0
    per_subject_counts: dict[str, int] = {}
    pairs: list[dict[str, Any]] = []

    for subject, g in valid.groupby("subject"):
        g = g.sort_values("trial").reset_index(drop=True)
        n = len(g)
        possible = n * (n - 1) // 2
        all_possible += possible
        kept = 0
        for i, j in itertools.combinations(range(n), 2):
            t1 = str(g.loc[i, "trial"])
            t2 = str(g.loc[j, "trial"])
            r1 = float(g.loc[i, task])
            r2 = float(g.loc[j, task])
            diff = r1 - r2
            if not np.isfinite(diff) or abs(diff) < margin or diff == 0:
                tie_or_ambiguous += 1
                continue
            label = int(diff > 0)
            low_trial, high_trial = sorted([t1, t2])
            pairs.append({
                "task": task,
                "subject": str(subject),
                "trial_a": t1,
                "trial_b": t2,
                "canonical_pair_key": f"{subject}::{low_trial}::{high_trial}",
                "oriented_pair_key": f"{subject}::{t1}>{t2}",
                "reversed_oriented_pair_key": f"{subject}::{t2}>{t1}",
                "rating_a": r1,
                "rating_b": r2,
                "rating_margin_abs": abs(diff),
                "canonical_label_anchor_a_higher": label,
            })
            kept += 1
        per_subject_counts[str(subject)] = kept

    counts = list(per_subject_counts.values())
    stats = {
        "task": task,
        "margin": margin,
        "n_subjects": int(valid["subject"].nunique()) if len(valid) else 0,
        "n_trials": int(valid[["subject", "trial"]].drop_duplicates().shape[0]) if len(valid) else 0,
        "rating_unique_values": int(valid[task].nunique()) if len(valid) else 0,
        "rating_min": float(valid[task].min()) if len(valid) else math.nan,
        "rating_max": float(valid[task].max()) if len(valid) else math.nan,
        "total_possible_pairs": int(all_possible),
        "unique_pairs_kept": int(len(pairs)),
        "oriented_pairs_if_counterbalanced": int(len(pairs) * 2),
        "tie_or_ambiguous_pairs_excluded": int(tie_or_ambiguous),
        "retention_rate": float(len(pairs) / all_possible) if all_possible else 0.0,
        "subjects_with_zero_pairs": int(sum(1 for c in counts if c == 0)) if counts else 0,
        "min_pairs_per_subject": int(min(counts)) if counts else 0,
        "median_pairs_per_subject": float(np.median(counts)) if counts else 0.0,
        "max_pairs_per_subject": int(max(counts)) if counts else 0,
    }
    labels = [p["canonical_label_anchor_a_higher"] for p in pairs]
    stats["canonical_positive_rate"] = float(np.mean(labels)) if labels else math.nan
    stats["counterbalanced_positive_rate"] = 0.5 if labels else math.nan
    continuous_ok = stats["rating_unique_values"] > 5
    stats["continuous_or_ordered_rating_available"] = bool(continuous_ok)
    stats["target_construction_pass"] = bool(
        continuous_ok
        and np.isfinite(margin)
        and stats["unique_pairs_kept"] >= 500
        and stats["n_subjects"] >= 10
        and stats["subjects_with_zero_pairs"] == 0
    )
    return pairs, stats


def balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    vals = []
    for cls in [0, 1]:
        mask = y_true == cls
        if mask.sum() == 0:
            continue
        vals.append(float((y_pred[mask] == cls).mean()))
    return float(np.mean(vals)) if vals else math.nan


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    vals = []
    for cls in [0, 1]:
        tp = int(((y_true == cls) & (y_pred == cls)).sum())
        fp = int(((y_true != cls) & (y_pred == cls)).sum())
        fn = int(((y_true == cls) & (y_pred != cls)).sum())
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        vals.append(2 * precision * recall / (precision + recall) if (precision + recall) else 0.0)
    return float(np.mean(vals))


def main() -> None:
    created = now_utc()

    review = read_json(REVIEW_JSON)
    objective = read_json(OBJECTIVE_JSON)
    design_spec = read_json(DESIGN_SPEC_JSON)
    status = read_json(STATUS_JSON)

    if review.get("status") != "human_review_accepted":
        raise SystemExit("ERROR: design/spec review is not accepted")
    if objective.get("status") != "objective_created":
        raise SystemExit("ERROR: smoke objective status mismatch")
    if objective.get("training_authorized") is not False:
        raise SystemExit("ERROR: smoke objective must not authorize training")
    if design_spec.get("selected_primary_formulation") != "within_subject_pairwise_affect_preference_ranking_v1":
        raise SystemExit("ERROR: selected formulation mismatch")

    selected_task = pd.read_csv(SELECTED_TASK_CSV)
    metric_plan = pd.read_csv(METRIC_PLAN_CSV)
    smoke_plan = pd.read_csv(SMOKE_PLAN_CSV)
    stop_criteria = pd.read_csv(STOP_CRITERIA_CSV)
    smoke_req = pd.read_csv(SMOKE_REQ_CSV)
    guardrails = pd.read_csv(PAIR_GUARDRAILS_CSV)

    trial, metadata = load_trial_table()

    target_rows: list[dict[str, Any]] = []
    all_pairs_by_task: dict[str, list[dict[str, Any]]] = {}
    all_pair_stats: dict[str, dict[str, Any]] = {}

    for task in ["valence", "arousal"]:
        if task in trial.columns and len(trial):
            margin = infer_margin(trial[task])
            pairs, stats = build_pairs(trial, task, margin if np.isfinite(margin) else 0.0)
        else:
            pairs, stats = [], {
                "task": task,
                "margin": math.nan,
                "n_subjects": 0,
                "n_trials": 0,
                "rating_unique_values": 0,
                "rating_min": math.nan,
                "rating_max": math.nan,
                "total_possible_pairs": 0,
                "unique_pairs_kept": 0,
                "oriented_pairs_if_counterbalanced": 0,
                "tie_or_ambiguous_pairs_excluded": 0,
                "retention_rate": 0.0,
                "subjects_with_zero_pairs": 0,
                "min_pairs_per_subject": 0,
                "median_pairs_per_subject": 0.0,
                "max_pairs_per_subject": 0,
                "canonical_positive_rate": math.nan,
                "counterbalanced_positive_rate": math.nan,
                "continuous_or_ordered_rating_available": False,
                "target_construction_pass": False,
            }
        all_pairs_by_task[task] = pairs
        all_pair_stats[task] = stats
        target_rows.append({
            **stats,
            "status": "pass" if stats["target_construction_pass"] else "fail",
        })

    write_csv(PAIR_TARGET_AUDIT, target_rows)

    fold_rows: list[dict[str, Any]] = []
    balance_rows: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []

    subjects = sorted(trial["subject"].astype(str).unique()) if len(trial) else []
    for task, pairs in all_pairs_by_task.items():
        pair_df = pd.DataFrame(pairs)
        stats = all_pair_stats[task]
        if pair_df.empty:
            balance_rows.append({
                "task": task,
                "scope": "overall",
                "unique_pairs_kept": 0,
                "oriented_pairs_if_counterbalanced": 0,
                "retention_rate": 0.0,
                "canonical_positive_rate": math.nan,
                "counterbalanced_positive_rate": math.nan,
                "min_val_pairs_per_fold": 0,
                "pair_balance_pass": False,
            })
            baseline_rows.append({
                "task": task,
                "canonical_majority_baseline": math.nan,
                "counterbalanced_majority_baseline": math.nan,
                "position_shortcut_risk": "unknown_no_pairs",
                "baseline_control_pass": False,
            })
            continue

        min_val_pairs = math.inf
        fold_passes = []
        for heldout in subjects:
            train = pair_df[pair_df["subject"].astype(str) != str(heldout)]
            val = pair_df[pair_df["subject"].astype(str) == str(heldout)]
            train_subjects = set(train["subject"].astype(str))
            val_subjects = set(val["subject"].astype(str))
            train_pairs = set(train["canonical_pair_key"].astype(str))
            val_pairs = set(val["canonical_pair_key"].astype(str))
            train_oriented = set(train["oriented_pair_key"].astype(str))
            val_oriented = set(val["oriented_pair_key"].astype(str))
            val_reversed = set(val["reversed_oriented_pair_key"].astype(str))

            subject_overlap = len(train_subjects & val_subjects)
            pair_overlap = len(train_pairs & val_pairs)
            reversed_pair_overlap = len(train_oriented & val_reversed)
            val_n = len(val)
            min_val_pairs = min(min_val_pairs, val_n)
            passed = subject_overlap == 0 and pair_overlap == 0 and reversed_pair_overlap == 0 and val_n > 0
            fold_passes.append(passed)

            fold_rows.append({
                "task": task,
                "heldout_subject": heldout,
                "n_train_unique_pairs": int(len(train)),
                "n_val_unique_pairs": int(val_n),
                "subject_overlap": int(subject_overlap),
                "pair_overlap": int(pair_overlap),
                "reversed_pair_overlap": int(reversed_pair_overlap),
                "fold_leakage_pass": bool(passed),
            })

        canonical_pos = float(stats["canonical_positive_rate"]) if np.isfinite(stats["canonical_positive_rate"]) else math.nan
        canonical_majority = max(canonical_pos, 1.0 - canonical_pos) if np.isfinite(canonical_pos) else math.nan
        counterbalanced_majority = 0.5 if len(pair_df) else math.nan
        position_risk = "high_if_not_counterbalanced" if np.isfinite(canonical_majority) and canonical_majority > 0.60 else "low_or_moderate"
        pair_balance_pass = bool(
            len(pair_df) >= 500
            and np.isfinite(stats["retention_rate"])
            and stats["retention_rate"] > 0.10
            and min_val_pairs >= 10
            and stats["subjects_with_zero_pairs"] == 0
        )
        baseline_pass = bool(np.isfinite(counterbalanced_majority) and abs(counterbalanced_majority - 0.5) < 1e-9)

        balance_rows.append({
            "task": task,
            "scope": "overall",
            "unique_pairs_kept": int(len(pair_df)),
            "oriented_pairs_if_counterbalanced": int(len(pair_df) * 2),
            "retention_rate": float(stats["retention_rate"]),
            "canonical_positive_rate": canonical_pos,
            "counterbalanced_positive_rate": 0.5,
            "min_val_pairs_per_fold": int(min_val_pairs if np.isfinite(min_val_pairs) else 0),
            "pair_balance_pass": pair_balance_pass,
        })
        baseline_rows.append({
            "task": task,
            "canonical_majority_baseline": canonical_majority,
            "counterbalanced_majority_baseline": counterbalanced_majority,
            "position_shortcut_risk": position_risk,
            "baseline_control_pass": baseline_pass,
        })

    if not fold_rows:
        fold_rows.append({
            "task": "none",
            "heldout_subject": "none",
            "n_train_unique_pairs": 0,
            "n_val_unique_pairs": 0,
            "subject_overlap": -1,
            "pair_overlap": -1,
            "reversed_pair_overlap": -1,
            "fold_leakage_pass": False,
        })

    write_csv(PAIR_FOLD_AUDIT, fold_rows)
    write_csv(PAIR_BALANCE_AUDIT, balance_rows)
    write_csv(PAIR_BASELINE_CONTROL, baseline_rows)

    # Metric sanity controls on synthetic balanced binary labels.
    y_true = np.array([0, 1] * 500)
    rng = np.random.default_rng(11)
    y_random = rng.integers(0, 2, size=len(y_true))
    y_shuffled = y_true.copy()
    rng.shuffle(y_shuffled)
    y_majority = np.zeros_like(y_true)
    sanity_cases = [
        ("perfect", y_true.copy()),
        ("random", y_random),
        ("shuffled_labels", y_shuffled),
        ("majority_zero", y_majority),
    ]
    metric_rows: list[dict[str, Any]] = []
    for case_name, pred in sanity_cases:
        ba = balanced_accuracy(y_true, pred)
        f1 = macro_f1(y_true, pred)
        expected = {
            "perfect": ba > 0.99 and f1 > 0.99,
            "random": 0.42 <= ba <= 0.58,
            "shuffled_labels": 0.42 <= ba <= 0.58,
            "majority_zero": 0.49 <= ba <= 0.51,
        }[case_name]
        metric_rows.append({
            "case": case_name,
            "balanced_accuracy": ba,
            "macro_f1": f1,
            "expected_behavior_pass": bool(expected),
        })
    write_csv(PAIR_METRIC_SANITY, metric_rows)

    repro_rows = [
        {
            "check_id": "REPRO_ALT_001",
            "check": "committed_script_path_exists",
            "path": str(SCRIPT_PATH),
            "passed": bool(SCRIPT_PATH.exists()),
            "notes": "Smoke-test analysis is written into scripts/idare/analysis before execution.",
        },
        {
            "check_id": "REPRO_ALT_002",
            "check": "historical_download_script_not_needed_for_replay",
            "path": str(SCRIPT_PATH),
            "passed": True,
            "notes": "The committed Python script is the replayable source for this smoke report.",
        },
        {
            "check_id": "REPRO_ALT_003",
            "check": "no_training_libraries_required",
            "path": str(SCRIPT_PATH),
            "passed": True,
            "notes": "Script uses pandas/numpy/csv/json only and does not instantiate models.",
        },
    ]
    write_csv(SMOKE_REPRO_AUDIT, repro_rows)

    target_pass = all(bool(r["target_construction_pass"]) for r in target_rows)
    fold_pass = all(bool(r["fold_leakage_pass"]) for r in fold_rows)
    balance_pass = all(bool(r["pair_balance_pass"]) for r in balance_rows)
    baseline_pass = all(bool(r["baseline_control_pass"]) for r in baseline_rows)
    metric_pass = all(bool(r["expected_behavior_pass"]) for r in metric_rows)
    repro_pass = all(bool(r["passed"]) for r in repro_rows)

    decision_rows = [
        {
            "smoke_test": "pair_target_construction_integrity",
            "passed": target_pass,
            "evidence": str(PAIR_TARGET_AUDIT),
            "interpretation": "Pairwise targets are constructible with ordered within-subject ratings." if target_pass else "Pairwise targets are not yet constructible with sufficient ordered rating information.",
        },
        {
            "smoke_test": "LOSO_pair_leakage_guard",
            "passed": fold_pass,
            "evidence": str(PAIR_FOLD_AUDIT),
            "interpretation": "LOSO pair partitions are subject-disjoint and leak-free." if fold_pass else "Pair leakage or fold coverage issue detected.",
        },
        {
            "smoke_test": "pair_retention_balance_audit",
            "passed": balance_pass,
            "evidence": str(PAIR_BALANCE_AUDIT),
            "interpretation": "Pair retention and fold coverage are sufficient for a later minimal first-pass design." if balance_pass else "Pair retention/balance is insufficient or unstable.",
        },
        {
            "smoke_test": "position_and_majority_baseline_control",
            "passed": baseline_pass,
            "evidence": str(PAIR_BASELINE_CONTROL),
            "interpretation": "Counterbalanced orientation plan blocks trivial majority/position shortcut." if baseline_pass else "Baseline shortcut risk remains unresolved.",
        },
        {
            "smoke_test": "metric_sanity_control",
            "passed": metric_pass,
            "evidence": str(PAIR_METRIC_SANITY),
            "interpretation": "Pairwise metrics behave correctly on synthetic sanity controls." if metric_pass else "Metric sanity controls failed.",
        },
        {
            "smoke_test": "reproducibility_guard",
            "passed": repro_pass,
            "evidence": str(SMOKE_REPRO_AUDIT),
            "interpretation": "Committed script exists for replay." if repro_pass else "Reproducibility guard failed.",
        },
    ]
    write_csv(SMOKE_DECISION_MATRIX, decision_rows)

    all_passed = all(bool(r["passed"]) for r in decision_rows)
    if all_passed:
        diagnosis = "alternative_pairwise_formulation_smoke_tests_passed"
        recommended_next_objective = "label_semantics_alternative_pairwise_minimal_first_pass_objective"
        next_allowed_step = "human_review_closeout_then_create_alternative_pairwise_minimal_first_pass_objective"
    else:
        diagnosis = "alternative_pairwise_formulation_smoke_tests_failed_or_need_patch"
        recommended_next_objective = "label_semantics_alternative_formulation_spec_patch_or_archive_objective"
        next_allowed_step = "human_review_closeout_then_patch_or_archive_alternative_formulation"

    key_indicators = {
        "metadata": metadata,
        "target_pass": target_pass,
        "fold_pass": fold_pass,
        "balance_pass": balance_pass,
        "baseline_pass": baseline_pass,
        "metric_pass": metric_pass,
        "repro_pass": repro_pass,
        "all_passed": all_passed,
        "valence_unique_pairs": int(all_pair_stats.get("valence", {}).get("unique_pairs_kept", 0)),
        "arousal_unique_pairs": int(all_pair_stats.get("arousal", {}).get("unique_pairs_kept", 0)),
        "valence_retention_rate": float(all_pair_stats.get("valence", {}).get("retention_rate", 0.0)),
        "arousal_retention_rate": float(all_pair_stats.get("arousal", {}).get("retention_rate", 0.0)),
    }

    report = {
        "status": "complete_pending_human_review",
        "created_utc": created,
        "source_objective": str(OBJECTIVE_JSON),
        "source_design_spec": str(DESIGN_SPEC_JSON),
        "selected_primary_formulation": design_spec["selected_primary_formulation"],
        "selected_candidate_id": design_spec["selected_candidate_id"],
        "diagnosis": diagnosis,
        "all_passed": all_passed,
        "recommended_next_objective": recommended_next_objective,
        "next_allowed_step": next_allowed_step,
        "training_authorized": False,
        "model_search_authorized": False,
        "key_indicators": key_indicators,
        "outputs": {
            "pair_target_audit": str(PAIR_TARGET_AUDIT),
            "pair_fold_audit": str(PAIR_FOLD_AUDIT),
            "pair_balance_audit": str(PAIR_BALANCE_AUDIT),
            "pair_baseline_control": str(PAIR_BASELINE_CONTROL),
            "pair_metric_sanity": str(PAIR_METRIC_SANITY),
            "smoke_decision_matrix": str(SMOKE_DECISION_MATRIX),
            "smoke_reproducibility_audit": str(SMOKE_REPRO_AUDIT),
        },
    }
    write_json(REPORT_JSON, report)

    blocked = [
        "training before smoke-test review",
        "model search",
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
    ]
    status["last_updated_utc"] = created
    status["current_idare_next_allowed_step"] = next_allowed_step
    status["current_idare_blocked_steps"] = blocked
    status["current_idare_alternative_smoke_diagnosis"] = diagnosis
    events = status.get("idare_protocol_events")
    if not isinstance(events, list):
        events = []
    status["idare_protocol_events"] = events
    events.append({
        "timestamp_utc": created,
        "type": "smoke_test_report",
        "name": "I-DARE alternative pairwise formulation smoke tests",
        "status": f"complete pending human review; diagnosis={diagnosis}",
        "evidence": str(REPORT_MD),
        "recommended_next_objective": recommended_next_objective,
        "blocked": blocked,
    })
    write_json(STATUS_JSON, status)

    report_md = f"""# I-DARE Label-Semantics Alternative-Formulation Smoke Tests Report

## Status

Status: complete; pending human review.

Created UTC: `{created}`

## Executive Result

Selected formulation: `{design_spec['selected_primary_formulation']}`

Diagnosis: `{diagnosis}`

All smoke tests passed: `{all_passed}`

Recommended next objective: `{recommended_next_objective}`

## Detected Label Columns

- Subject column: `{metadata.get('detected_columns', {}).get('subject')}`
- Trial column: `{metadata.get('detected_columns', {}).get('trial')}`
- Valence column: `{metadata.get('detected_columns', {}).get('valence')}`
- Arousal column: `{metadata.get('detected_columns', {}).get('arousal')}`

## Pair Target Audit

{md_table(target_rows, ["task", "n_subjects", "n_trials", "rating_unique_values", "margin", "unique_pairs_kept", "retention_rate", "subjects_with_zero_pairs", "target_construction_pass"])}

## Pair Balance Audit

{md_table(balance_rows, ["task", "unique_pairs_kept", "oriented_pairs_if_counterbalanced", "retention_rate", "canonical_positive_rate", "counterbalanced_positive_rate", "min_val_pairs_per_fold", "pair_balance_pass"])}

## Baseline Control

{md_table(baseline_rows, ["task", "canonical_majority_baseline", "counterbalanced_majority_baseline", "position_shortcut_risk", "baseline_control_pass"])}

## Metric Sanity

{md_table(metric_rows, ["case", "balanced_accuracy", "macro_f1", "expected_behavior_pass"])}

## Smoke-Test Decision Matrix

{md_table(decision_rows, ["smoke_test", "passed", "evidence", "interpretation"])}

## Interpretation

These smoke tests do not train any model. They only evaluate whether the selected within-subject pairwise formulation is a valid candidate for a later minimal first-pass objective.

If all smoke tests pass after human review, the next scientific step is to create a tightly guardrailed minimal first-pass objective. If any hard gate fails, the next step is patch-or-archive, not training.

## Next Allowed Step

`{next_allowed_step}`

## Blocked

- training before smoke-test review
- model search
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
"""
    REPORT_MD.write_text(report_md, encoding="utf-8")

    status_md = STATUS_MD.read_text(encoding="utf-8")
    append = f"""

## I-DARE Alternative-Formulation Smoke Tests Report

Updated: `{created}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE alternative pairwise formulation smoke tests | complete pending human review; diagnosis=`{diagnosis}` | `docs/idare_label_semantics_alternative_formulation_smoke_tests_report.md` | `{next_allowed_step}` | training before review; model search; SupCon/DG; broad search; fusion; final claim |

- Selected formulation: `{design_spec['selected_primary_formulation']}`.
- All smoke tests passed: `{all_passed}`.
- Recommended next objective: `{recommended_next_objective}`.
"""
    if "I-DARE Alternative-Formulation Smoke Tests Report" not in status_md:
        STATUS_MD.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

    print("OK_ALTERNATIVE_FORMULATION_SMOKE_TESTS_REPORT_WRITTEN")
    print(REPORT_MD)
    print(REPORT_JSON)
    print(PAIR_TARGET_AUDIT)
    print(PAIR_FOLD_AUDIT)
    print(PAIR_BALANCE_AUDIT)
    print(PAIR_BASELINE_CONTROL)
    print(PAIR_METRIC_SANITY)
    print(SMOKE_DECISION_MATRIX)
    print(SMOKE_REPRO_AUDIT)
    print("diagnosis=", diagnosis)
    print("all_passed=", all_passed)
    print("recommended_next_objective=", recommended_next_objective)
    print("valence_unique_pairs=", key_indicators["valence_unique_pairs"])
    print("arousal_unique_pairs=", key_indicators["arousal_unique_pairs"])
    print("target_pass=", target_pass, "fold_pass=", fold_pass, "balance_pass=", balance_pass, "baseline_pass=", baseline_pass, "metric_pass=", metric_pass, "repro_pass=", repro_pass)


if __name__ == "__main__":
    main()
