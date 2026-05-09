#!/usr/bin/env python3
"""Read-only metric-debug analysis for the alternative pairwise first pass.

No training is run here. This script only analyzes already committed first-pass
outputs and writes a failure/metric-debug report.
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DOCS = Path("docs")
OBJECTIVE_JSON = DOCS / "idare_label_semantics_alternative_pairwise_failure_or_metric_debug_objective.json"
REVIEW_JSON = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_review_status.json"
FIRST_REPORT_JSON = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_report.json"
RUNS_CSV = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_runs.csv"
SUMMARY_CSV = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_metric_summary.csv"
PAIR_AUDIT_CSV = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_pair_audit.csv"
SUBJECT_CSV = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_subject_lift_summary.csv"
THRESHOLDS_CSV = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_metric_thresholds.csv"
STATUS_JSON = DOCS / "project_status_current.json"
STATUS_MD = DOCS / "project_status_current.md"

REPORT_MD = DOCS / "idare_label_semantics_alternative_pairwise_failure_or_metric_debug_report.md"
REPORT_JSON = DOCS / "idare_label_semantics_alternative_pairwise_failure_or_metric_debug_report.json"
CELL_AUDIT = DOCS / "idare_label_semantics_alternative_pairwise_failure_or_metric_debug_cell_audit.csv"
FOLD_AUDIT = DOCS / "idare_label_semantics_alternative_pairwise_failure_or_metric_debug_fold_audit.csv"
SUBJECT_CONC = DOCS / "idare_label_semantics_alternative_pairwise_failure_or_metric_debug_subject_concentration.csv"
DECISION_MATRIX = DOCS / "idare_label_semantics_alternative_pairwise_failure_or_metric_debug_decision_matrix.csv"
METRIC_ALIGNMENT = DOCS / "idare_label_semantics_alternative_pairwise_failure_or_metric_debug_metric_alignment.csv"


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


def safe_float(x: Any) -> float:
    try:
        if pd.isna(x):
            return math.nan
        return float(x)
    except Exception:
        return math.nan


def main() -> None:
    created = now_utc()
    objective = read_json(OBJECTIVE_JSON)
    review = read_json(REVIEW_JSON)
    first_report = read_json(FIRST_REPORT_JSON)
    status = read_json(STATUS_JSON)

    if objective.get("status") != "objective_created":
        raise SystemExit("ERROR: objective status mismatch")
    if objective.get("training_authorized") is not False:
        raise SystemExit("ERROR: objective must be read-only with training_authorized=false")
    if objective.get("model_search_authorized") is not False:
        raise SystemExit("ERROR: objective must not authorize model search")
    if review.get("accepted_diagnosis") != "alternative_pairwise_minimal_first_pass_weak_mixed_signal":
        raise SystemExit("ERROR: review diagnosis mismatch")
    if first_report.get("diagnosis") != "alternative_pairwise_minimal_first_pass_weak_mixed_signal":
        raise SystemExit("ERROR: first-pass diagnosis mismatch")

    runs = pd.read_csv(RUNS_CSV)
    summary = pd.read_csv(SUMMARY_CSV)
    pair_audit = pd.read_csv(PAIR_AUDIT_CSV)
    subject = pd.read_csv(SUBJECT_CSV)
    thresholds = pd.read_csv(THRESHOLDS_CSV)

    if len(runs) != 96:
        raise SystemExit(f"ERROR: expected 96 run rows, found {len(runs)}")
    if len(summary) != 16:
        raise SystemExit(f"ERROR: expected 16 summary rows, found {len(summary)}")
    if len(pair_audit) != 4:
        raise SystemExit(f"ERROR: expected 4 pair audit rows, found {len(pair_audit)}")
    if len(subject) <= 0:
        raise SystemExit("ERROR: subject summary is empty")

    best = first_report.get("best_learned_cell") or {}
    best_model = str(best.get("model"))
    best_modality = str(best.get("modality"))
    best_task = str(best.get("task"))

    learned = summary[summary["training_category"].astype(str).eq("minimal_classical_pairwise_baseline")].copy()
    controls = summary[summary["training_category"].astype(str).eq("no_training_control")].copy()

    cell_rows: list[dict[str, Any]] = []
    for r in learned.to_dict("records"):
        mean_bal = safe_float(r.get("mean_balanced_accuracy"))
        delta_majority = safe_float(r.get("delta_vs_majority_baseline_bal_acc"))
        delta_random = safe_float(r.get("delta_vs_random_baseline_bal_acc"))
        folds_over = int(r.get("folds_over_055_bal_acc", 0))
        folds_under = int(r.get("folds_under_045_bal_acc", 0))
        max_bal = safe_float(r.get("max_balanced_accuracy"))
        min_bal = safe_float(r.get("min_balanced_accuracy"))
        std_bal = safe_float(r.get("std_balanced_accuracy"))
        interesting = bool(mean_bal >= 0.55 and folds_over >= 3 and folds_under == 0)
        weak_positive = bool(mean_bal > 0.52 and delta_majority > 0.0)
        near_chance = bool(mean_bal <= 0.52)
        if interesting:
            decision = "candidate_confirmation"
        elif weak_positive:
            decision = "weak_positive_below_confirmation_threshold"
        elif near_chance:
            decision = "near_chance"
        else:
            decision = "ambiguous"
        cell_rows.append({
            "model": r["model"],
            "modality": r["modality"],
            "task": r["task"],
            "n_runs": int(r["n_runs"]),
            "mean_balanced_accuracy": mean_bal,
            "std_balanced_accuracy": std_bal,
            "min_balanced_accuracy": min_bal,
            "max_balanced_accuracy": max_bal,
            "mean_macro_f1": safe_float(r.get("mean_macro_f1")),
            "delta_vs_majority_baseline_bal_acc": delta_majority,
            "delta_vs_random_baseline_bal_acc": delta_random,
            "folds_over_055_bal_acc": folds_over,
            "folds_under_045_bal_acc": folds_under,
            "one_class_pred_count": int(r.get("one_class_pred_count", 0)),
            "interesting_threshold_met": interesting,
            "weak_positive_signal": weak_positive,
            "cell_decision": decision,
        })
    write_csv(CELL_AUDIT, cell_rows)

    # Fold-level lift vs controls.
    majority = runs[runs["model"].astype(str).eq("majority_train_label_no_training")][
        ["modality", "task", "fold", "balanced_accuracy", "macro_f1"]
    ].rename(columns={"balanced_accuracy": "majority_bal_acc", "macro_f1": "majority_macro_f1"})
    random = runs[runs["model"].astype(str).eq("random_balanced_no_training")][
        ["modality", "task", "fold", "balanced_accuracy", "macro_f1"]
    ].rename(columns={"balanced_accuracy": "random_bal_acc", "macro_f1": "random_macro_f1"})
    learned_runs = runs[runs["training_category"].astype(str).eq("minimal_classical_pairwise_baseline")].copy()
    fold = learned_runs.merge(majority, on=["modality", "task", "fold"], how="left").merge(
        random, on=["modality", "task", "fold"], how="left"
    )
    fold["delta_vs_majority_bal_acc"] = fold["balanced_accuracy"] - fold["majority_bal_acc"]
    fold["delta_vs_random_bal_acc"] = fold["balanced_accuracy"] - fold["random_bal_acc"]
    fold_rows = []
    for r in fold.to_dict("records"):
        fold_rows.append({
            "objective_run_id": int(r["objective_run_id"]),
            "model": r["model"],
            "modality": r["modality"],
            "task": r["task"],
            "fold": int(r["fold"]),
            "balanced_accuracy": safe_float(r["balanced_accuracy"]),
            "macro_f1": safe_float(r["macro_f1"]),
            "majority_bal_acc": safe_float(r["majority_bal_acc"]),
            "random_bal_acc": safe_float(r["random_bal_acc"]),
            "delta_vs_majority_bal_acc": safe_float(r["delta_vs_majority_bal_acc"]),
            "delta_vs_random_bal_acc": safe_float(r["delta_vs_random_bal_acc"]),
            "above_055": bool(safe_float(r["balanced_accuracy"]) >= 0.55),
            "below_045": bool(safe_float(r["balanced_accuracy"]) < 0.45),
        })
    write_csv(FOLD_AUDIT, fold_rows)

    # Subject concentration for best learned cell.
    best_sub = subject[
        (subject["model"].astype(str) == best_model)
        & (subject["modality"].astype(str) == best_modality)
        & (subject["task"].astype(str) == best_task)
    ].copy()
    base_sub = subject[
        (subject["model"].astype(str) == "majority_train_label_no_training")
        & (subject["modality"].astype(str) == best_modality)
        & (subject["task"].astype(str) == best_task)
    ][["fold", "subject", "balanced_accuracy"]].rename(columns={"balanced_accuracy": "majority_subject_bal_acc"})
    best_sub = best_sub.merge(base_sub, on=["fold", "subject"], how="left")
    best_sub["subject_delta_vs_majority_bal_acc"] = best_sub["balanced_accuracy"] - best_sub["majority_subject_bal_acc"]
    # Keep this boolean on the DataFrame before later aggregation.
    best_sub["positive_lift"] = best_sub["subject_delta_vs_majority_bal_acc"] > 0.0
    subject_rows = []
    for r in best_sub.to_dict("records"):
        subject_rows.append({
            "model": best_model,
            "modality": best_modality,
            "task": best_task,
            "fold": int(r["fold"]),
            "subject": str(r["subject"]),
            "n_val_pairs": int(r["n_val_pairs"]),
            "subject_balanced_accuracy": safe_float(r["balanced_accuracy"]),
            "majority_subject_bal_acc": safe_float(r["majority_subject_bal_acc"]),
            "subject_delta_vs_majority_bal_acc": safe_float(r["subject_delta_vs_majority_bal_acc"]),
            "positive_lift": bool(safe_float(r["subject_delta_vs_majority_bal_acc"]) > 0.0),
        })
    write_csv(SUBJECT_CONC, subject_rows)

    best_fold = fold[
        (fold["model"].astype(str) == best_model)
        & (fold["modality"].astype(str) == best_modality)
        & (fold["task"].astype(str) == best_task)
    ].copy()
    best_mean = safe_float(best.get("mean_balanced_accuracy"))
    best_delta = safe_float(best.get("delta_vs_majority_baseline_bal_acc"))
    best_folds_over = int(best.get("folds_over_055_bal_acc", 0) or 0)
    best_max = safe_float(best.get("max_balanced_accuracy"))
    best_min = safe_float(best.get("min_balanced_accuracy"))
    best_std = safe_float(best.get("std_balanced_accuracy"))
    best_positive_folds = int((best_fold["delta_vs_majority_bal_acc"] > 0).sum())
    best_negative_folds = int((best_fold["delta_vs_majority_bal_acc"] <= 0).sum())
    subject_positive = int(best_sub["positive_lift"].sum())
    subject_total = int(len(best_sub))
    subject_positive_frac = subject_positive / subject_total if subject_total else math.nan
    top_abs_subject_delta = float(best_sub["subject_delta_vs_majority_bal_acc"].abs().max()) if len(best_sub) else math.nan

    metric_rows = [
        {
            "metric": "mean_balanced_accuracy",
            "value": best_mean,
            "threshold_or_context": "actionable >= 0.55",
            "status": "below_actionable_threshold",
        },
        {
            "metric": "delta_vs_majority_baseline_bal_acc",
            "value": best_delta,
            "threshold_or_context": "positive but should be practically meaningful",
            "status": "positive_but_small",
        },
        {
            "metric": "folds_over_055_bal_acc",
            "value": best_folds_over,
            "threshold_or_context": "confirmation candidate requires >= 3",
            "status": "not_met",
        },
        {
            "metric": "fold_positive_delta_count",
            "value": best_positive_folds,
            "threshold_or_context": "majority of folds positive supports weak signal",
            "status": "weak_support" if best_positive_folds >= 4 else "unstable_or_weak",
        },
        {
            "metric": "subject_positive_lift_fraction",
            "value": subject_positive_frac,
            "threshold_or_context": "broad subject lift would support generality",
            "status": "to_review_below_or_near_mixed" if subject_positive_frac < 0.7 else "broad_subject_lift",
        },
    ]
    write_csv(METRIC_ALIGNMENT, metric_rows)

    # Decision logic.
    if best_mean >= 0.55 and best_folds_over >= 3 and best_delta > 0.02:
        diagnosis = "alternative_pairwise_metric_debug_supports_narrow_confirmation"
        recommendation = "create_narrow_pairwise_confirmation_objective_after_review"
        recommended_next = "label_semantics_alternative_pairwise_narrow_confirmation_objective"
        decision_reason = "Best cell meets actionable threshold and shows practical lift."
    elif best_mean > 0.52 and best_delta > 0 and best_positive_folds >= 4:
        diagnosis = "alternative_pairwise_metric_debug_weak_but_consistent_signal"
        recommendation = "create_narrow_feature_representation_patch_or_confirmation_design_after_review"
        recommended_next = "label_semantics_alternative_pairwise_feature_representation_patch_objective"
        decision_reason = "Best cell is consistently weak-positive but below confirmation threshold; summary features may be limiting."
    elif best_mean > 0.52 and best_delta > 0:
        diagnosis = "alternative_pairwise_metric_debug_weak_unstable_signal"
        recommendation = "archive_or_patch_only_after_review"
        recommended_next = "label_semantics_alternative_pairwise_archive_or_patch_objective"
        decision_reason = "Best cell is marginally above controls but not stable enough for confirmation."
    else:
        diagnosis = "alternative_pairwise_metric_debug_no_actionable_signal"
        recommendation = "archive_pairwise_first_pass_after_review"
        recommended_next = "label_semantics_alternative_pairwise_archive_closeout_objective"
        decision_reason = "Learned cells are near chance and do not show actionable lift."

    decision_rows = [
        {
            "decision_id": "D1",
            "option": "narrow confirmation",
            "status": "not_selected" if diagnosis != "alternative_pairwise_metric_debug_supports_narrow_confirmation" else "selected",
            "rationale": "Requires mean balanced accuracy >= 0.55 and at least 3 folds over 0.55.",
        },
        {
            "decision_id": "D2",
            "option": "narrow feature/representation patch",
            "status": "selected" if diagnosis == "alternative_pairwise_metric_debug_weak_but_consistent_signal" else "not_selected",
            "rationale": "Weak-positive signal is present but below confirmation threshold; avoid broad search.",
        },
        {
            "decision_id": "D3",
            "option": "archive or patch",
            "status": "selected" if diagnosis == "alternative_pairwise_metric_debug_weak_unstable_signal" else "not_selected",
            "rationale": "Marginal signal without enough stability.",
        },
        {
            "decision_id": "D4",
            "option": "archive closeout",
            "status": "selected" if diagnosis == "alternative_pairwise_metric_debug_no_actionable_signal" else "not_selected",
            "rationale": "No actionable signal beyond controls.",
        },
        {
            "decision_id": "D5",
            "option": "broad training / SupCon / fusion",
            "status": "blocked",
            "rationale": "Not authorized by evidence; would be premature.",
        },
    ]
    write_csv(DECISION_MATRIX, decision_rows)

    blocked = [
        "broad hyperparameter search",
        "direct full SupCon/DG training",
        "EEG+EMG fusion",
        "final LOSO claim",
        "training before review of this metric-debug report",
    ]

    report = {
        "status": "complete_pending_human_review",
        "created_utc": created,
        "source_objective": str(OBJECTIVE_JSON),
        "source_first_pass_report": str(FIRST_REPORT_JSON),
        "diagnosis": diagnosis,
        "recommendation": recommendation,
        "recommended_next_objective": recommended_next,
        "decision_reason": decision_reason,
        "training_authorized": False,
        "model_search_authorized": False,
        "final_loso_claim_authorized": False,
        "best_cell": best,
        "best_cell_debug": {
            "best_mean_balanced_accuracy": best_mean,
            "best_delta_vs_majority_baseline_bal_acc": best_delta,
            "best_folds_over_055_bal_acc": best_folds_over,
            "best_positive_delta_folds": best_positive_folds,
            "best_negative_or_zero_delta_folds": best_negative_folds,
            "best_min_balanced_accuracy": best_min,
            "best_max_balanced_accuracy": best_max,
            "best_std_balanced_accuracy": best_std,
            "subject_positive_lift_count": subject_positive,
            "subject_total": subject_total,
            "subject_positive_lift_fraction": subject_positive_frac,
            "top_abs_subject_delta_vs_majority": top_abs_subject_delta,
        },
        "outputs": {
            "cell_audit": str(CELL_AUDIT),
            "fold_audit": str(FOLD_AUDIT),
            "subject_concentration": str(SUBJECT_CONC),
            "decision_matrix": str(DECISION_MATRIX),
            "metric_alignment": str(METRIC_ALIGNMENT),
        },
    }
    write_json(REPORT_JSON, report)

    status["last_updated_utc"] = created
    status["current_idare_next_allowed_step"] = "human_review_closeout_before_pairwise_patch_or_archive"
    status["current_idare_blocked_steps"] = blocked
    status["current_idare_pairwise_metric_debug_diagnosis"] = diagnosis
    events = status.get("idare_protocol_events")
    if not isinstance(events, list):
        events = []
    status["idare_protocol_events"] = events
    events.append({
        "timestamp_utc": created,
        "type": "analysis_report",
        "name": "I-DARE alternative pairwise failure-or-metric-debug report",
        "status": f"complete pending human review; diagnosis={diagnosis}",
        "evidence": str(REPORT_MD),
        "recommended_next_objective": recommended_next,
        "blocked": blocked,
    })
    write_json(STATUS_JSON, status)

    top_cells = sorted(cell_rows, key=lambda r: r["mean_balanced_accuracy"], reverse=True)[:8]
    best_fold_rows = best_fold[["fold", "balanced_accuracy", "macro_f1", "delta_vs_majority_bal_acc", "delta_vs_random_bal_acc"]].to_dict("records")
    report_md = f"""# I-DARE Alternative Pairwise Failure-or-Metric-Debug Report

## Status

Status: complete; pending human review.

Created UTC: `{created}`

## Executive Diagnosis

Diagnosis: `{diagnosis}`

Recommendation: `{recommendation}`

Recommended next objective: `{recommended_next}`

Decision reason: {decision_reason}

## Best Cell Debug

Best cell: `{best_model}` / `{best_modality}` / `{best_task}`

- Mean balanced accuracy: `{best_mean:.6f}`
- Delta vs majority baseline: `{best_delta:.6f}`
- Folds over 0.55: `{best_folds_over}`
- Positive-delta folds vs majority: `{best_positive_folds}` / `6`
- Subject positive-lift fraction: `{subject_positive_frac:.6f}`

## Top Cell Audit

{md_table(top_cells, ["model", "modality", "task", "mean_balanced_accuracy", "delta_vs_majority_baseline_bal_acc", "folds_over_055_bal_acc", "weak_positive_signal", "cell_decision"])}

## Best-Cell Fold Audit

{md_table(best_fold_rows, ["fold", "balanced_accuracy", "macro_f1", "delta_vs_majority_bal_acc", "delta_vs_random_bal_acc"])}

## Metric Alignment

{md_table(metric_rows, ["metric", "value", "threshold_or_context", "status"])}

## Decision Matrix

{md_table(decision_rows, ["decision_id", "option", "status", "rationale"])}

## Interpretation

The pairwise label formulation remains healthier than the archived global/ordinal branch, but the first-pass signal is not strong enough for a final claim or broad model search.

The best cell is weak-positive, with small lift over controls and no fold reaching the predeclared actionable threshold. This points more toward a narrow feature/representation patch or patch-vs-archive decision than toward immediate confirmation.

## Next Allowed Step

`human_review_closeout_before_pairwise_patch_or_archive`
"""
    REPORT_MD.write_text(report_md, encoding="utf-8")

    status_text = STATUS_MD.read_text(encoding="utf-8")
    append = f"""

## I-DARE Alternative Pairwise Failure-or-Metric-Debug Report

Updated: `{created}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE alternative pairwise failure-or-metric-debug report | complete pending human review; diagnosis=`{diagnosis}` | `docs/idare_label_semantics_alternative_pairwise_failure_or_metric_debug_report.md` | Human review / closeout before pairwise patch-or-archive decision. | broad search; SupCon/DG; fusion; final claim; training before review |

- Decision reason: {decision_reason}
- Recommended next objective: `{recommended_next}` only after human review.
"""
    if "I-DARE Alternative Pairwise Failure-or-Metric-Debug Report" not in status_text:
        STATUS_MD.write_text(status_text.rstrip() + append + "\n", encoding="utf-8")

    print("OK_PAIRWISE_FAILURE_OR_METRIC_DEBUG_REPORT_WRITTEN")
    print(REPORT_MD)
    print(REPORT_JSON)
    print(CELL_AUDIT)
    print(FOLD_AUDIT)
    print(SUBJECT_CONC)
    print(METRIC_ALIGNMENT)
    print(DECISION_MATRIX)
    print("diagnosis=", diagnosis)
    print("recommendation=", recommendation)
    print("recommended_next_objective=", recommended_next)
    print("decision_reason=", decision_reason)
    print("best_mean_balanced_accuracy=", best_mean)
    print("best_delta_vs_majority=", best_delta)
    print("best_positive_delta_folds=", best_positive_folds)
    print("subject_positive_lift_fraction=", subject_positive_frac)


if __name__ == "__main__":
    main()
