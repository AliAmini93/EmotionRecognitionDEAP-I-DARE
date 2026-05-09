#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

D = Path("docs")
OBJECTIVE_JSON = D / "idare_label_semantics_alternative_pairwise_target_sampling_audit_objective.json"
REVIEW_JSON = D / "idare_label_semantics_alternative_pairwise_feature_patch_archive_closeout_report_review_status.json"
ARCHIVE_CLOSEOUT_JSON = D / "idare_label_semantics_alternative_pairwise_feature_patch_archive_closeout_report.json"
PAIRWISE_FIRST_JSON = D / "idare_label_semantics_alternative_pairwise_minimal_first_pass_report.json"
PAIRWISE_SMOKE_JSON = D / "idare_label_semantics_alternative_formulation_smoke_tests_report.json"
RUNS_CSV = D / "idare_label_semantics_alternative_pairwise_minimal_first_pass_runs.csv"
METRIC_CSV = D / "idare_label_semantics_alternative_pairwise_minimal_first_pass_metric_summary.csv"
SUBJECT_CSV = D / "idare_label_semantics_alternative_pairwise_minimal_first_pass_subject_lift_summary.csv"
PAIR_TARGET_CSV = D / "idare_label_semantics_alternative_formulation_pair_target_audit.csv"
PAIR_FOLD_CSV = D / "idare_label_semantics_alternative_formulation_pair_fold_audit.csv"
PAIR_BALANCE_CSV = D / "idare_label_semantics_alternative_formulation_pair_balance_audit.csv"
REPORT_MD = D / "idare_label_semantics_alternative_pairwise_target_sampling_audit_report.md"
REPORT_JSON = D / "idare_label_semantics_alternative_pairwise_target_sampling_audit_report.json"
FOLD_OUT = D / "idare_label_semantics_alternative_pairwise_target_sampling_fold_balance_audit.csv"
SUBJECT_OUT = D / "idare_label_semantics_alternative_pairwise_target_sampling_subject_concentration_audit.csv"
ALIGN_OUT = D / "idare_label_semantics_alternative_pairwise_target_sampling_metric_alignment.csv"
DECISION_OUT = D / "idare_label_semantics_alternative_pairwise_target_sampling_decision_matrix.csv"
STATUS_JSON = D / "project_status_current.json"
STATUS_MD = D / "project_status_current.md"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise SystemExit(f"ERROR: no rows for {path}")
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in rows:
        vals = []
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


def safe_float(value: Any, default: float = float("nan")) -> float:
    try:
        return float(value)
    except Exception:
        return default


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "bal_acc": "balanced_accuracy",
        "balanced_acc": "balanced_accuracy",
        "mean_bal_acc": "mean_balanced_accuracy",
        "subject": "subject_id",
        "participant": "subject_id",
        "participant_id": "subject_id",
    }
    rename = {a: b for a, b in aliases.items() if a in df.columns and b not in df.columns}
    return df.rename(columns=rename)


def require_false(obj: dict[str, Any], key: str) -> None:
    if obj.get(key) is not False:
        raise SystemExit(f"ERROR: {key} must be false")


def best_cell(report: dict[str, Any]) -> dict[str, Any]:
    for key in ("best_learned_cell", "best_cell"):
        if isinstance(report.get(key), dict):
            return dict(report[key])
    return {}


def summarize_balance(df: pd.DataFrame) -> dict[str, Any]:
    max_dev = 0.0
    column = "not_detected"
    for col in df.columns:
        low = str(col).lower()
        if not any(t in low for t in ["rate", "ratio", "fraction", "positive", "balance"]):
            continue
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        vals = vals[(vals >= 0.0) & (vals <= 1.0)]
        if vals.empty:
            continue
        dev = float((vals - 0.5).abs().max())
        if dev > max_dev:
            max_dev, column = dev, str(col)
    return {"balance_reference_column": column, "max_abs_deviation_from_0_5": max_dev, "class_balance_issue": bool(max_dev > 0.10)}


def main() -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    objective = read_json(OBJECTIVE_JSON)
    review = read_json(REVIEW_JSON)
    archive = read_json(ARCHIVE_CLOSEOUT_JSON)
    first = read_json(PAIRWISE_FIRST_JSON)
    smoke = read_json(PAIRWISE_SMOKE_JSON)
    status = read_json(STATUS_JSON)

    if objective.get("status") != "objective_created":
        raise SystemExit("ERROR: objective status mismatch")
    for key in ["training_authorized", "rerun_authorized", "model_fitting_authorized", "feature_search_authorized", "model_search_authorized", "supcon_dg_authorized", "fusion_authorized", "final_loso_claim_authorized", "label_change_authorized", "fold_change_authorized"]:
        require_false(objective, key)
    if review.get("status") != "human_review_accepted":
        raise SystemExit("ERROR: review status mismatch")
    if archive.get("diagnosis") != "feature_patch_branch_archived_as_negative_result":
        raise SystemExit("ERROR: archive closeout diagnosis mismatch")
    if archive.get("archive_entire_pairwise_formulation") is not False:
        raise SystemExit("ERROR: whole pairwise formulation must not be archived")
    if first.get("diagnosis") != "alternative_pairwise_minimal_first_pass_weak_mixed_signal":
        raise SystemExit("ERROR: pairwise first-pass diagnosis mismatch")
    if smoke.get("diagnosis") != "alternative_pairwise_formulation_smoke_tests_passed":
        raise SystemExit("ERROR: pairwise smoke-test diagnosis mismatch")

    runs = normalize(pd.read_csv(RUNS_CSV))
    metric = normalize(pd.read_csv(METRIC_CSV))
    subject = normalize(pd.read_csv(SUBJECT_CSV))
    balance = normalize(pd.read_csv(PAIR_BALANCE_CSV))
    # These are loaded for provenance and schema failures, even when only summary stats are needed.
    target_audit = normalize(pd.read_csv(PAIR_TARGET_CSV))
    fold_audit = normalize(pd.read_csv(PAIR_FOLD_CSV))

    needed = {"model", "modality", "task", "fold", "balanced_accuracy"}
    missing = needed - set(runs.columns)
    if missing:
        raise SystemExit(f"ERROR: runs CSV missing columns after normalization: {sorted(missing)}")
    runs["balanced_accuracy"] = pd.to_numeric(runs["balanced_accuracy"], errors="coerce")
    if "n_val_pairs" not in runs.columns:
        runs["n_val_pairs"] = float("nan")
    runs["n_val_pairs"] = pd.to_numeric(runs["n_val_pairs"], errors="coerce")

    best = best_cell(first)
    best_model = str(best.get("model", "ridge_classifier_pairwise_summary_diff"))
    best_modality = str(best.get("modality", "EEG"))
    best_task = str(best.get("task", "arousal"))
    best_mean = safe_float(best.get("mean_balanced_accuracy"))
    best_delta = safe_float(best.get("delta_vs_majority_baseline_bal_acc"))
    best_folds_over = int(safe_float(best.get("folds_over_055_bal_acc", 0.0), 0.0))

    unique_pairs = runs[["task", "fold", "n_val_pairs"]].dropna().drop_duplicates().sort_values(["task", "fold"])
    fold_rows: list[dict[str, Any]] = []
    task_cv: dict[str, float] = {}
    task_ratio_range: dict[str, float] = {}
    for task, grp in unique_pairs.groupby("task", dropna=False):
        vals = pd.to_numeric(grp["n_val_pairs"], errors="coerce").dropna()
        mean_pairs = float(vals.mean()) if len(vals) else float("nan")
        std_pairs = float(vals.std(ddof=0)) if len(vals) else float("nan")
        cv = float(std_pairs / mean_pairs) if mean_pairs and not math.isnan(mean_pairs) else float("nan")
        min_pairs = float(vals.min()) if len(vals) else float("nan")
        max_pairs = float(vals.max()) if len(vals) else float("nan")
        ratio_range = float((max_pairs - min_pairs) / mean_pairs) if mean_pairs and not math.isnan(mean_pairs) else float("nan")
        task_cv[str(task)] = cv
        task_ratio_range[str(task)] = ratio_range
        learned = runs[(runs["task"].astype(str) == str(task)) & (~runs["model"].astype(str).str.contains("no_training", case=False, na=False))]
        fold_perf = learned.groupby("fold")["balanced_accuracy"].mean().to_dict()
        for _, row in grp.iterrows():
            fold = row["fold"]
            n_pairs = safe_float(row["n_val_pairs"])
            fold_rows.append({
                "task": task,
                "fold": fold,
                "n_val_pairs": n_pairs,
                "task_mean_n_val_pairs": mean_pairs,
                "ratio_to_task_mean": n_pairs / mean_pairs if mean_pairs else float("nan"),
                "task_pair_count_cv": cv,
                "task_pair_count_ratio_range": ratio_range,
                "learned_mean_balanced_accuracy_in_fold": safe_float(fold_perf.get(fold)),
                "pair_count_flag": bool(abs((n_pairs / mean_pairs) - 1.0) > 0.15) if mean_pairs else False,
            })
    max_pair_cv = max([v for v in task_cv.values() if not math.isnan(v)] or [0.0])
    max_ratio_range = max([v for v in task_ratio_range.values() if not math.isnan(v)] or [0.0])
    pair_count_issue = bool(max_pair_cv > 0.12 or max_ratio_range > 0.35)

    balance_info = summarize_balance(balance)
    class_balance_issue = bool(balance_info["class_balance_issue"])

    best_runs = runs[(runs["model"].astype(str) == best_model) & (runs["modality"].astype(str) == best_modality) & (runs["task"].astype(str) == best_task)]
    corr_pair_count_bal = float("nan")
    if len(best_runs) >= 3 and best_runs["n_val_pairs"].notna().sum() >= 3:
        corr_pair_count_bal = float(best_runs[["n_val_pairs", "balanced_accuracy"]].corr().iloc[0, 1])
    pair_count_metric_issue = bool(not math.isnan(corr_pair_count_bal) and abs(corr_pair_count_bal) > 0.60)

    subject_filtered = subject.copy()
    for col, val in [("model", best_model), ("modality", best_modality), ("task", best_task)]:
        if col in subject_filtered.columns:
            subject_filtered = subject_filtered[subject_filtered[col].astype(str) == val]
    subject_col = "subject_id" if "subject_id" in subject_filtered.columns else None
    delta_col = None
    for candidate in ["subject_delta_vs_majority_bal_acc", "subject_delta_vs_random_bal_acc", "delta_vs_majority_baseline_bal_acc", "delta_balanced_accuracy", "lift"]:
        if candidate in subject_filtered.columns:
            delta_col = candidate
            break
    if delta_col is None:
        for col in subject_filtered.columns:
            low = col.lower()
            if ("delta" in low or "lift" in low) and ("bal" in low or "acc" in low):
                delta_col = col
                break

    subject_rows: list[dict[str, Any]] = []
    n_subjects = 0
    subject_positive_fraction = float("nan")
    top20_abs_lift_share = float("nan")
    subject_concentration_issue = False
    if subject_col and delta_col and len(subject_filtered):
        subject_filtered[delta_col] = pd.to_numeric(subject_filtered[delta_col], errors="coerce")
        by_subject = subject_filtered.groupby(subject_col, dropna=False)[delta_col].mean().reset_index().rename(columns={delta_col: "mean_subject_lift"})
        by_subject["positive_lift"] = by_subject["mean_subject_lift"] > 0.0
        by_subject["abs_lift"] = by_subject["mean_subject_lift"].abs()
        n_subjects = int(len(by_subject))
        subject_positive_fraction = float(by_subject["positive_lift"].mean()) if n_subjects else float("nan")
        total_abs = float(by_subject["abs_lift"].sum())
        top_n = max(1, int(math.ceil(n_subjects * 0.20))) if n_subjects else 0
        top20_abs_lift_share = float(by_subject.sort_values("abs_lift", ascending=False).head(top_n)["abs_lift"].sum() / total_abs) if total_abs > 0 and top_n > 0 else float("nan")
        subject_concentration_issue = bool((not math.isnan(top20_abs_lift_share) and top20_abs_lift_share > 0.55) or (not math.isnan(subject_positive_fraction) and (subject_positive_fraction < 0.35 or subject_positive_fraction > 0.85)))
        for _, row in by_subject.sort_values("abs_lift", ascending=False).iterrows():
            subject_rows.append({
                "subject_id": row[subject_col],
                "best_model": best_model,
                "best_modality": best_modality,
                "best_task": best_task,
                "mean_subject_lift": safe_float(row["mean_subject_lift"]),
                "abs_lift": safe_float(row["abs_lift"]),
                "positive_lift": bool(row["positive_lift"]),
                "top20_abs_lift_share": top20_abs_lift_share,
                "subject_positive_fraction": subject_positive_fraction,
                "subject_concentration_issue": subject_concentration_issue,
            })
    else:
        subject_rows.append({"subject_id": "unavailable", "best_model": best_model, "best_modality": best_modality, "best_task": best_task, "subject_concentration_issue": "undetermined"})

    metric_rows: list[dict[str, Any]] = []
    metric = normalize(metric)
    if {"model", "modality", "task"}.issubset(metric.columns):
        for _, row in metric.iterrows():
            model = str(row.get("model", ""))
            if "no_training" in model.lower():
                continue
            modality = str(row.get("modality", ""))
            task = str(row.get("task", ""))
            mean_bal = safe_float(row.get("mean_balanced_accuracy", row.get("mean_accuracy", float("nan"))))
            delta_majority = safe_float(row.get("delta_vs_majority_baseline_bal_acc", row.get("delta_vs_majority_bal_acc", float("nan"))))
            folds_over = int(safe_float(row.get("folds_over_055_bal_acc", 0.0), 0.0))
            cell_runs = runs[(runs["model"].astype(str) == model) & (runs["modality"].astype(str) == modality) & (runs["task"].astype(str) == task)]
            corr = float("nan")
            if len(cell_runs) >= 3 and cell_runs["n_val_pairs"].notna().sum() >= 3:
                corr = float(cell_runs[["n_val_pairs", "balanced_accuracy"]].corr().iloc[0, 1])
            metric_rows.append({
                "model": model,
                "modality": modality,
                "task": task,
                "mean_balanced_accuracy": mean_bal,
                "delta_vs_majority_baseline_bal_acc": delta_majority,
                "folds_over_055_bal_acc": folds_over,
                "task_pair_count_cv": task_cv.get(task, float("nan")),
                "corr_n_val_pairs_vs_balanced_accuracy": corr,
                "metric_strength": "weak" if mean_bal < 0.53 and delta_majority < 0.03 else "potentially_actionable",
                "sampling_alignment_flag": bool(not math.isnan(corr) and abs(corr) > 0.60),
            })
    if not metric_rows:
        metric_rows.append({"model": best_model, "modality": best_modality, "task": best_task, "mean_balanced_accuracy": best_mean, "delta_vs_majority_baseline_bal_acc": best_delta, "folds_over_055_bal_acc": best_folds_over})

    weak_metric = bool(best_mean < 0.53 and best_delta < 0.03 and best_folds_over == 0)
    actionable_sampling_issue = bool(pair_count_issue or class_balance_issue or subject_concentration_issue or pair_count_metric_issue)
    if actionable_sampling_issue:
        diagnosis = "alternative_pairwise_target_sampling_audit_possible_sampling_artifact"
        recommendation = "create_spec_only_pair_sampling_rethink_after_review"
        recommended_next_objective = "label_semantics_alternative_pairwise_target_sampling_rethink_spec_objective"
        decision_reason = "Read-only audit found a possible sampling/target artifact that could explain weak pairwise signal."
    else:
        diagnosis = "alternative_pairwise_target_sampling_audit_no_actionable_sampling_artifact"
        recommendation = "pause_or_archive_pairwise_line_after_review"
        recommended_next_objective = "label_semantics_alternative_pairwise_pause_or_archive_objective"
        decision_reason = "Pair counts and class balance do not show a strong artifact; best signal remains weak and below confirmation thresholds."

    decision_rows = [
        {"decision_id": "D1", "check": "pair_count_distribution", "observed": f"max_pair_count_cv={max_pair_cv:.6f}; max_ratio_range={max_ratio_range:.6f}", "issue_found": pair_count_issue, "decision": "sampling_artifact_possible" if pair_count_issue else "no_major_pair_count_artifact"},
        {"decision_id": "D2", "check": "class_balance", "observed": f"max_abs_deviation_from_0_5={balance_info['max_abs_deviation_from_0_5']:.6f}; column={balance_info['balance_reference_column']}", "issue_found": class_balance_issue, "decision": "class_balance_artifact_possible" if class_balance_issue else "no_major_class_balance_artifact"},
        {"decision_id": "D3", "check": "subject_concentration", "observed": f"n_subjects={n_subjects}; positive_fraction={subject_positive_fraction:.6f}; top20_abs_lift_share={top20_abs_lift_share:.6f}", "issue_found": subject_concentration_issue, "decision": "subject_concentration_possible" if subject_concentration_issue else "no_strong_subject_concentration_artifact"},
        {"decision_id": "D4", "check": "pair_count_metric_alignment", "observed": f"corr_n_val_pairs_vs_balanced_accuracy={corr_pair_count_bal:.6f}", "issue_found": pair_count_metric_issue, "decision": "metric_aligned_with_pair_count" if pair_count_metric_issue else "metric_not_strongly_explained_by_pair_count"},
        {"decision_id": "D5", "check": "best_metric_strength", "observed": f"best_mean_balanced_accuracy={best_mean:.6f}; delta_vs_majority={best_delta:.6f}; folds_over_055={best_folds_over}", "issue_found": weak_metric, "decision": "weak_signal_below_confirmation_threshold" if weak_metric else "potentially_actionable_metric_signal"},
        {"decision_id": "D6", "check": "overall", "observed": decision_reason, "issue_found": actionable_sampling_issue, "decision": recommendation},
    ]

    write_csv(FOLD_OUT, fold_rows)
    write_csv(SUBJECT_OUT, subject_rows)
    write_csv(ALIGN_OUT, metric_rows)
    write_csv(DECISION_OUT, decision_rows)

    blocked = ["training or rerun", "model fitting", "new feature patch search", "broad hyperparameter search", "direct full SupCon/DG training", "EEG+EMG fusion", "final LOSO claim", "changing labels or fold definitions"]
    report = {
        "status": "complete_pending_human_review",
        "created_utc": now,
        "source_objective": str(OBJECTIVE_JSON),
        "diagnosis": diagnosis,
        "recommendation": recommendation,
        "recommended_next_objective": recommended_next_objective,
        "decision_reason": decision_reason,
        "training_authorized": False,
        "rerun_authorized": False,
        "model_fitting_authorized": False,
        "feature_search_authorized": False,
        "model_search_authorized": False,
        "supcon_dg_authorized": False,
        "fusion_authorized": False,
        "final_loso_claim_authorized": False,
        "label_change_authorized": False,
        "fold_change_authorized": False,
        "best_cell": best,
        "best_mean_balanced_accuracy": best_mean,
        "best_delta_vs_majority": best_delta,
        "best_folds_over_055_bal_acc": best_folds_over,
        "max_pair_count_cv": max_pair_cv,
        "max_pair_count_ratio_range": max_ratio_range,
        "class_balance_issue": class_balance_issue,
        "subject_positive_fraction": subject_positive_fraction,
        "top20_abs_lift_share": top20_abs_lift_share,
        "pair_count_metric_correlation_for_best_cell": corr_pair_count_bal,
        "actionable_sampling_issue": actionable_sampling_issue,
        "input_shapes": {"target_audit_rows": len(target_audit), "fold_audit_rows": len(fold_audit), "runs_rows": len(runs), "subject_rows": len(subject)},
        "outputs": {"fold_balance_audit": str(FOLD_OUT), "subject_concentration_audit": str(SUBJECT_OUT), "metric_alignment": str(ALIGN_OUT), "decision_matrix": str(DECISION_OUT)},
        "blocked": blocked,
    }
    write_json(REPORT_JSON, report)

    status["last_updated_utc"] = now
    status["current_idare_next_allowed_step"] = "human_review_then_" + recommended_next_objective
    status["current_idare_blocked_steps"] = blocked
    status["current_idare_pairwise_target_sampling_audit_report_status"] = f"complete_pending_human_review; diagnosis={diagnosis}"
    events = status.get("idare_protocol_events")
    if not isinstance(events, list):
        events = []
    status["idare_protocol_events"] = events
    events.append({"timestamp_utc": now, "type": "read_only_audit_report", "name": "I-DARE alternative pairwise target/sampling audit report", "status": f"complete pending human review; diagnosis={diagnosis}", "evidence": str(REPORT_MD), "recommended_next_objective": recommended_next_objective, "blocked": blocked})
    write_json(STATUS_JSON, status)

    report_text = f"""# I-DARE Alternative Pairwise Target/Sampling Audit Report

## Status

Status: complete; pending human review.

Created UTC: `{now}`

## Executive Diagnosis

Diagnosis: `{diagnosis}`

Recommendation: `{recommendation}`

Recommended next objective: `{recommended_next_objective}`

Decision reason: {decision_reason}

## Best Prior Pairwise Signal

Best model: `{best_model}`

Best modality/task: `{best_modality}` / `{best_task}`

Best mean balanced accuracy: `{best_mean:.6f}`

Delta vs majority baseline: `{best_delta:.6f}`

Folds over 0.55 balanced accuracy: `{best_folds_over}`

## Fold / Pair Count Audit

Max pair-count coefficient of variation across tasks: `{max_pair_cv:.6f}`

Max pair-count ratio range across tasks: `{max_ratio_range:.6f}`

Pair-count issue found: `{str(pair_count_issue).lower()}`

## Class Balance Audit

Balance reference column: `{balance_info['balance_reference_column']}`

Max absolute deviation from 0.5: `{balance_info['max_abs_deviation_from_0_5']:.6f}`

Class-balance issue found: `{str(class_balance_issue).lower()}`

## Subject Concentration Audit

Subjects audited: `{n_subjects}`

Subject positive lift fraction: `{subject_positive_fraction:.6f}`

Top-20% absolute lift share: `{top20_abs_lift_share:.6f}`

Subject concentration issue found: `{str(subject_concentration_issue).lower()}`

## Metric Alignment

Correlation between validation pair count and best-cell balanced accuracy: `{corr_pair_count_bal:.6f}`

Pair-count/metric alignment issue found: `{str(pair_count_metric_issue).lower()}`

## Decision Matrix

{md_table(decision_rows, ['decision_id', 'check', 'observed', 'issue_found', 'decision'])}

## Interpretation

This read-only audit does not perform training, reruns, model fitting, feature search, label changes, or fold changes.

The feature patch branch remains archived as a negative result. The broader pairwise formulation is evaluated here only through existing target/sampling evidence.

## Next Allowed Step

`human_review_then_{recommended_next_objective}`
"""
    REPORT_MD.write_text(report_text, encoding="utf-8")

    status_text = STATUS_MD.read_text(encoding="utf-8")
    append = f"""

## I-DARE Alternative Pairwise Target/Sampling Audit Report

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE alternative pairwise target/sampling audit report | complete pending human review; diagnosis=`{diagnosis}` | `docs/idare_label_semantics_alternative_pairwise_target_sampling_audit_report.md` | Human review then `{recommended_next_objective}`. | training; rerun; model fitting; feature/model search; SupCon/DG; fusion; final claim |

- Decision reason: {decision_reason}
- Actionable sampling issue found: `{str(actionable_sampling_issue).lower()}`.
"""
    if "I-DARE Alternative Pairwise Target/Sampling Audit Report" not in status_text:
        STATUS_MD.write_text(status_text.rstrip() + append + "\n", encoding="utf-8")

    print("OK_TARGET_SAMPLING_AUDIT_REPORT_WRITTEN")
    print(REPORT_MD)
    print(REPORT_JSON)
    print(FOLD_OUT)
    print(SUBJECT_OUT)
    print(ALIGN_OUT)
    print(DECISION_OUT)
    print("diagnosis=", diagnosis)
    print("recommendation=", recommendation)
    print("recommended_next_objective=", recommended_next_objective)
    print("actionable_sampling_issue=", actionable_sampling_issue)
    print("max_pair_count_cv=", max_pair_cv)
    print("class_balance_issue=", class_balance_issue)
    print("subject_positive_fraction=", subject_positive_fraction)
    print("top20_abs_lift_share=", top20_abs_lift_share)


if __name__ == "__main__":
    main()
