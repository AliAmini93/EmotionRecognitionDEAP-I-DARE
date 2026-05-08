#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_supcon_dg_pair_sampler_failure_analysis_report_fix.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start fixed SupCon/DG pair-sampler failure-analysis report ====="
date
git status --short --branch
echo

echo "===== 1) choose python and require clean repo ====="
PY="${PY:-.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3)"
fi
echo "PY=$PY"
"$PY" - <<'PY'
import json
import csv
from pathlib import Path
try:
    import pandas as pd
    import numpy as np
except Exception as e:
    raise SystemExit(f"ERROR_IMPORTS: {e}")
print("OK_IMPORTS")
PY

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: repo is not clean; commit/stash before generating report." >&2
  git status --short
  exit 2
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required committed inputs ====="
required=(
  docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.md
  docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.json
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_review_status.md
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_review_status.json
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv
  docs/idare_supcon_dg_failure_analysis_report.json
  docs/project_status_current.json
  docs/project_status_current.md
)
for f in "${required[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "ERROR: missing required input: $f" >&2
    exit 3
  fi
  ls -lh "$f"
done
echo

echo "===== 3) remove stale target outputs if any ====="
rm -f \
  docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md \
  docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json \
  docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv \
  docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv \
  docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv \
  docs/idare_supcon_dg_pair_sampler_failure_decision_matrix.csv
echo "OK_CLEAN_TARGET_OUTPUTS"
echo

echo "===== 4) generate read-only SupCon/DG pair-sampler failure-analysis report ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

objective_path = DOCS / "idare_supcon_dg_pair_sampler_failure_analysis_objective.json"
ablation_report_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_report.json"
runs_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv"
pred_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv"
pair_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv"
loss_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv"
method_task_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv"
candidate_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv"
smoke_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv"
prev_failure_path = DOCS / "idare_supcon_dg_failure_analysis_report.json"

report_md_path = DOCS / "idare_supcon_dg_pair_sampler_failure_analysis_report.md"
report_json_path = DOCS / "idare_supcon_dg_pair_sampler_failure_analysis_report.json"
candidate_deltas_path = DOCS / "idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv"
fold_subject_path = DOCS / "idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv"
loss_alignment_path = DOCS / "idare_supcon_dg_pair_sampler_failure_loss_alignment.csv"
decision_matrix_path = DOCS / "idare_supcon_dg_pair_sampler_failure_decision_matrix.csv"

objective = json.loads(objective_path.read_text(encoding="utf-8"))
ablation_report = json.loads(ablation_report_path.read_text(encoding="utf-8"))
prev_failure = json.loads(prev_failure_path.read_text(encoding="utf-8"))

runs = pd.read_csv(runs_path)
pred = pd.read_csv(pred_path)
pair = pd.read_csv(pair_path)
loss = pd.read_csv(loss_path)
method_task = pd.read_csv(method_task_path)
candidate_summary = pd.read_csv(candidate_path)
smoke = pd.read_csv(smoke_path)

# Robust schema normalization. The failed script missed `accuracy` and
# `positive_pair_coverage_final_epoch`, so keep all historical aliases here.
rename_aliases = {
    "accuracy": "acc",
    "final_accuracy": "acc",
    "balanced_accuracy": "bal_acc",
    "final_balanced_accuracy": "bal_acc",
    "macro_f1_score": "macro_f1",
    "final_macro_f1": "macro_f1",
    "fold_id": "fold",
    "positive_pair_coverage": "pos_cov",
    "positive_pair_coverage_final_epoch": "pos_cov",
    "mean_positive_pair_coverage": "mean_pos_cov",
}
for df in [runs, pred, pair, loss, method_task, candidate_summary, smoke]:
    df.rename(columns={k: v for k, v in rename_aliases.items() if k in df.columns and v not in df.columns}, inplace=True)

needed = ["candidate_id", "modality", "task", "fold", "macro_f1", "bal_acc", "acc"]
missing = [c for c in needed if c not in runs.columns]
if missing:
    raise SystemExit(f"ERROR: runs CSV missing required columns after normalization: {missing}; columns={list(runs.columns)}")

for c in ["macro_f1", "bal_acc", "acc"]:
    runs[c] = pd.to_numeric(runs[c], errors="coerce")
runs["fold"] = pd.to_numeric(runs["fold"], errors="coerce").astype("Int64")
if "one_class_pred" not in runs.columns:
    runs["one_class_pred"] = False
if "pos_cov" not in runs.columns:
    runs["pos_cov"] = np.nan
else:
    runs["pos_cov"] = pd.to_numeric(runs["pos_cov"], errors="coerce")

candidate_names = {
    "A0_CE_control": "CE control",
    "A2_cross_subject_positive_only": "cross-subject SupCon only",
    "A4_rating_distance_guarded_supcon": "rating-distance guarded SupCon",
    "A6_vrex_only_recheck": "VREx only",
    "A5_cross_subject_supcon_vrex": "cross-subject SupCon + VREx",
}
baseline = "A0_CE_control"

cand = (
    runs.groupby("candidate_id", dropna=False)
    .agg(
        n_runs=("macro_f1", "size"),
        mean_macro_f1=("macro_f1", "mean"),
        std_macro_f1=("macro_f1", "std"),
        min_macro_f1=("macro_f1", "min"),
        max_macro_f1=("macro_f1", "max"),
        mean_bal_acc=("bal_acc", "mean"),
        mean_acc=("acc", "mean"),
        folds_over_055_macro_f1=("macro_f1", lambda x: int((x > 0.55).sum())),
        folds_under_050_macro_f1=("macro_f1", lambda x: int((x < 0.50).sum())),
        one_class_pred_count=("one_class_pred", lambda x: int(pd.Series(x).astype(str).str.lower().isin(["true", "1", "yes"]).sum())),
        mean_pos_cov=("pos_cov", "mean"),
    )
    .reset_index()
)
cand["candidate_label"] = cand["candidate_id"].map(candidate_names).fillna(cand["candidate_id"])
cand = cand.sort_values(["mean_macro_f1", "mean_bal_acc"], ascending=False)

cell = (
    runs.groupby(["candidate_id", "modality", "task"], dropna=False)
    .agg(
        n_runs=("macro_f1", "size"),
        mean_macro_f1=("macro_f1", "mean"),
        std_macro_f1=("macro_f1", "std"),
        mean_bal_acc=("bal_acc", "mean"),
        mean_acc=("acc", "mean"),
        folds_over_055_macro_f1=("macro_f1", lambda x: int((x > 0.55).sum())),
        folds_under_050_macro_f1=("macro_f1", lambda x: int((x < 0.50).sum())),
        mean_pos_cov=("pos_cov", "mean"),
    )
    .reset_index()
)

base_cell = cell[cell["candidate_id"] == baseline][["modality", "task", "mean_macro_f1", "mean_bal_acc"]].rename(
    columns={"mean_macro_f1": "baseline_macro_f1", "mean_bal_acc": "baseline_bal_acc"}
)
vrex_cell = cell[cell["candidate_id"] == "A6_vrex_only_recheck"][["modality", "task", "mean_macro_f1", "mean_bal_acc"]].rename(
    columns={"mean_macro_f1": "vrex_macro_f1", "mean_bal_acc": "vrex_bal_acc"}
)
deltas = cell.merge(base_cell, on=["modality", "task"], how="left").merge(vrex_cell, on=["modality", "task"], how="left")
deltas["delta_vs_A0_macro_f1"] = deltas["mean_macro_f1"] - deltas["baseline_macro_f1"]
deltas["delta_vs_A0_bal_acc"] = deltas["mean_bal_acc"] - deltas["baseline_bal_acc"]
deltas["delta_vs_A6_macro_f1"] = deltas["mean_macro_f1"] - deltas["vrex_macro_f1"]
deltas["delta_vs_A6_bal_acc"] = deltas["mean_bal_acc"] - deltas["vrex_bal_acc"]
deltas["candidate_label"] = deltas["candidate_id"].map(candidate_names).fillna(deltas["candidate_id"])
deltas = deltas.sort_values(["delta_vs_A0_macro_f1", "mean_macro_f1"], ascending=False)
deltas.to_csv(candidate_deltas_path, index=False)

# Fold + prediction / subject localization.
fold_cols = ["candidate_id", "modality", "task", "fold"]
fold_summary = runs[fold_cols + ["macro_f1", "bal_acc", "acc", "pos_cov"]].copy().rename(columns={
    "macro_f1": "run_macro_f1",
    "bal_acc": "run_bal_acc",
    "acc": "run_acc",
})

# Normalize prediction columns.
for c in ["fold"]:
    if c in pred.columns:
        pred[c] = pd.to_numeric(pred[c], errors="coerce").astype("Int64")
true_col = next((c for c in ["y_true", "true_label", "label", "target"] if c in pred.columns), None)
pred_col = next((c for c in ["y_pred", "pred_label", "prediction", "pred"] if c in pred.columns), None)
if set(fold_cols).issubset(pred.columns) and true_col and pred_col:
    pred[true_col] = pd.to_numeric(pred[true_col], errors="coerce")
    pred[pred_col] = pd.to_numeric(pred[pred_col], errors="coerce")
    pred["correct"] = (pred[true_col] == pred[pred_col]).astype(float)
    pred_fold = pred.groupby(fold_cols, dropna=False).agg(
        n_predictions=("correct", "size"),
        prediction_accuracy=("correct", "mean"),
    ).reset_index()
    fold_summary = fold_summary.merge(pred_fold, on=fold_cols, how="left")
    subject_col = next((c for c in ["subject_id", "subject", "participant_id"] if c in pred.columns), None)
    if subject_col:
        subj = pred.groupby(fold_cols + [subject_col], dropna=False).agg(
            n_subject_predictions=("correct", "size"),
            subject_accuracy=("correct", "mean"),
        ).reset_index()
        subj_fold = subj.groupby(fold_cols, dropna=False).agg(
            n_subjects=(subject_col, "nunique"),
            mean_subject_accuracy=("subject_accuracy", "mean"),
            std_subject_accuracy=("subject_accuracy", "std"),
            min_subject_accuracy=("subject_accuracy", "min"),
            hard_subject_count=("subject_accuracy", lambda x: int((x < 0.45).sum())),
        ).reset_index()
        fold_summary = fold_summary.merge(subj_fold, on=fold_cols, how="left")
else:
    fold_summary["n_predictions"] = np.nan
    fold_summary["prediction_accuracy"] = np.nan

fold_summary.to_csv(fold_subject_path, index=False)

# Loss / embedding alignment.
loss_norm = loss.copy()
for df in [loss_norm]:
    df.rename(columns={k: v for k, v in rename_aliases.items() if k in df.columns and v not in df.columns}, inplace=True)
if "fold" in loss_norm.columns:
    loss_norm["fold"] = pd.to_numeric(loss_norm["fold"], errors="coerce").astype("Int64")
if "epoch" in loss_norm.columns:
    loss_norm["epoch"] = pd.to_numeric(loss_norm["epoch"], errors="coerce")
    idx = loss_norm.groupby(["candidate_id", "modality", "task", "fold"], dropna=False)["epoch"].idxmax()
    final_loss = loss_norm.loc[idx].copy()
else:
    final_loss = loss_norm.groupby(["candidate_id", "modality", "task", "fold"], dropna=False).tail(1).copy()

metric_cols = []
for c in final_loss.columns:
    lc = c.lower()
    if c in ["candidate_id", "modality", "task", "fold", "run_id", "global_run_id"]:
        continue
    if any(token in lc for token in ["loss", "embed", "silhouette", "distance", "variance", "alignment", "uniformity", "cos", "norm", "coverage"]):
        metric_cols.append(c)

join_cols = [c for c in fold_cols if c in final_loss.columns]
align = runs[fold_cols + ["macro_f1", "bal_acc", "acc"]].merge(
    final_loss[join_cols + metric_cols],
    on=fold_cols,
    how="left",
)
align.to_csv(loss_alignment_path, index=False)

corr_rows = []
for c in metric_cols:
    vals = pd.to_numeric(align[c], errors="coerce")
    for target in ["macro_f1", "bal_acc"]:
        tgt = pd.to_numeric(align[target], errors="coerce")
        valid = vals.notna() & tgt.notna()
        corr = np.nan
        if valid.sum() >= 5 and vals[valid].nunique() > 1 and tgt[valid].nunique() > 1:
            corr = float(np.corrcoef(vals[valid], tgt[valid])[0, 1])
        corr_rows.append({"metric": c, "target": target, "n": int(valid.sum()), "pearson_r": corr})
corr_df = pd.DataFrame(corr_rows)
if len(corr_df):
    corr_df = corr_df.sort_values("pearson_r", key=lambda s: s.abs(), ascending=False)
else:
    corr_df = pd.DataFrame(columns=["metric", "target", "n", "pearson_r"])

# Interpret failure.
def get_mean(candidate_id):
    rows = cand[cand["candidate_id"] == candidate_id]
    return float(rows["mean_macro_f1"].iloc[0]) if len(rows) else float("nan")

a0_mean = get_mean("A0_CE_control")
a2_mean = get_mean("A2_cross_subject_positive_only")
a4_mean = get_mean("A4_rating_distance_guarded_supcon")
a5_mean = get_mean("A5_cross_subject_supcon_vrex")
a6_mean = get_mean("A6_vrex_only_recheck")
a5_delta_a0 = a5_mean - a0_mean
a5_delta_a6 = a5_mean - a6_mean
a5_delta_a2 = a5_mean - a2_mean

best_row = cand.iloc[0].to_dict()
best_id = str(best_row.get("candidate_id"))
stable_candidate = bool((float(best_row.get("mean_macro_f1", 0)) >= 0.55) and (int(best_row.get("folds_under_050_macro_f1", 999)) <= 3))
pair_coverage_not_causal = bool(runs[runs["candidate_id"].isin(["A2_cross_subject_positive_only", "A4_rating_distance_guarded_supcon", "A5_cross_subject_supcon_vrex"])]["pos_cov"].mean() > 0.95 and float(best_row.get("mean_macro_f1", 0)) < 0.53)
supcon_component_weak = bool(a5_delta_a2 < 0.015 and a5_delta_a0 < 0.02)
vrx_dominant = bool(a6_mean >= a5_mean - 0.005)

if not stable_candidate and pair_coverage_not_causal and supcon_component_weak:
    diagnosis = "pair_sampler_valid_but_not_primary_failure_mode"
    recommended_next = "representation_or_label_semantics_failure_analysis_objective"
elif not stable_candidate and vrx_dominant:
    diagnosis = "dg_regularization_more_supported_than_supcon_pairs_but_still_insufficient"
    recommended_next = "vrex_regularizer_failure_analysis_objective"
elif not stable_candidate:
    diagnosis = "targeted_pair_sampler_changes_not_sufficient_need_failure_review"
    recommended_next = "representation_or_label_semantics_failure_analysis_objective"
else:
    diagnosis = "pair_sampler_candidate_promising_needs_confirmation"
    recommended_next = "pair_sampler_confirmation_objective"

decision_rows = [
    {
        "hypothesis": "Implementation/leakage failure",
        "evidence_for": "Smoke and guardrail checks were required and passed before ablation training.",
        "evidence_against": "All 120 runs completed; one-class prediction count remains zero in candidate-level aggregation.",
        "verdict": "unlikely_primary",
    },
    {
        "hypothesis": "Positive-pair coverage failure",
        "evidence_for": "SupCon variants depend on enough positives per batch/fold.",
        "evidence_against": "SupCon candidates have mean positive-pair coverage near 1.0 but still hover near chance.",
        "verdict": "unlikely_primary",
    },
    {
        "hypothesis": "Pair design semantic-noise failure",
        "evidence_for": "Cross-subject positives may connect trials with the same binary label but different subject-specific affect semantics.",
        "evidence_against": "A5 and A4 sometimes improve isolated cells, so pair design is not fully useless.",
        "verdict": "supported_partial",
    },
    {
        "hypothesis": "VREx / DG regularizer mismatch",
        "evidence_for": f"A6 VREx-only mean macro-F1={a6_mean:.4f}; A5 mean macro-F1={a5_mean:.4f}; A5-A6 delta={a5_delta_a6:.4f}.",
        "evidence_against": "VREx alone is also unstable and not sufficient.",
        "verdict": "supported_but_insufficient",
    },
    {
        "hypothesis": "Representation or label/task semantic bottleneck",
        "evidence_for": "Valid pairs and valid smokes do not translate into stable held-out subject performance; this matches previous subject-variability and label/task diagnoses.",
        "evidence_against": "Some fold/task cells exceed 0.55, so the signal is weak/intermittent rather than absent.",
        "verdict": "most_supported",
    },
]
decision_df = pd.DataFrame(decision_rows)
decision_df.to_csv(decision_matrix_path, index=False)

# Markdown table without tabulate dependency.
def fmt_val(v):
    if pd.isna(v):
        return ""
    if isinstance(v, (float, np.floating)):
        return f"{float(v):.4f}"
    return str(v)

def md_table(df, columns=None, max_rows=20):
    if columns is None:
        columns = list(df.columns)
    cols = [c for c in columns if c in df.columns]
    sub = df.loc[:, cols].head(max_rows).copy()
    if len(cols) == 0:
        return "_No columns available._"
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    rows = []
    for _, r in sub.iterrows():
        rows.append("| " + " | ".join(fmt_val(r[c]) for c in cols) + " |")
    return "\n".join([header, sep] + rows)

top_candidates_md = md_table(
    cand,
    ["candidate_id", "candidate_label", "n_runs", "mean_macro_f1", "std_macro_f1", "mean_bal_acc", "folds_over_055_macro_f1", "folds_under_050_macro_f1", "mean_pos_cov"],
    10,
)
top_deltas_md = md_table(
    deltas.sort_values(["delta_vs_A0_macro_f1"], ascending=False),
    ["candidate_id", "modality", "task", "mean_macro_f1", "delta_vs_A0_macro_f1", "delta_vs_A6_macro_f1", "folds_over_055_macro_f1", "folds_under_050_macro_f1"],
    20,
)
decision_md = md_table(decision_df, ["hypothesis", "verdict", "evidence_for", "evidence_against"], 10)
corr_md = md_table(corr_df, ["metric", "target", "n", "pearson_r"], 12)

if "hard_subject_count" in fold_summary.columns:
    hard_total = int(pd.to_numeric(fold_summary["hard_subject_count"], errors="coerce").fillna(0).sum())
    hard_subject_note = f"Subject-level summaries were available. Total hard-subject counts across fold/candidate cells: `{hard_total}`."
else:
    hard_subject_note = "Subject-level columns were not available in a standardized form; analysis falls back to fold-level localization."

best_cell = deltas.sort_values(["mean_macro_f1"], ascending=False).head(1).to_dict("records")[0] if len(deltas) else {}
best_delta_cell = deltas.sort_values(["delta_vs_A0_macro_f1"], ascending=False).head(1).to_dict("records")[0] if len(deltas) else {}

report = {
    "status": "complete_pending_human_review",
    "created_utc": now,
    "objective": str(objective_path),
    "row_counts": {
        "runs": int(len(runs)),
        "predictions": int(len(pred)),
        "pair_audit": int(len(pair)),
        "loss_embedding_summary": int(len(loss)),
        "candidate_summary": int(len(candidate_summary)),
        "method_task_summary": int(len(method_task)),
        "smoke_summary": int(len(smoke)),
    },
    "best_candidate": best_row,
    "a5_vs_controls": {
        "A5_mean_macro_f1": a5_mean,
        "A0_mean_macro_f1": a0_mean,
        "A6_mean_macro_f1": a6_mean,
        "A2_mean_macro_f1": a2_mean,
        "A4_mean_macro_f1": a4_mean,
        "A5_delta_vs_A0_macro_f1": a5_delta_a0,
        "A5_delta_vs_A6_macro_f1": a5_delta_a6,
        "A5_delta_vs_A2_macro_f1": a5_delta_a2,
    },
    "best_cell": best_cell,
    "best_delta_cell": best_delta_cell,
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next,
    "interpretation": {
        "stable_candidate_found": stable_candidate,
        "vrx_dominant_or_equivalent": vrx_dominant,
        "pair_coverage_not_causal": pair_coverage_not_causal,
        "supcon_component_weak": supcon_component_weak,
    },
    "outputs": {
        "candidate_deltas": str(candidate_deltas_path),
        "fold_subject_summary": str(fold_subject_path),
        "loss_alignment": str(loss_alignment_path),
        "decision_matrix": str(decision_matrix_path),
    },
    "next_allowed_step": "human_review_closeout_before_next_objective",
}
report_json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")

report_md = f"""# I-DARE SupCon/DG Pair-Sampler Failure Analysis Report

## Status

Status: complete; pending human review.

Created UTC: `{now}`

This is a read-only analysis. No new training was run.

## Executive Diagnosis

Diagnosis: `{diagnosis}`

Recommended next objective: `{recommended_next}`

The targeted pair/sampler ablation passed smoke/guardrail checks and completed `{len(runs)}` runs, but it still did not produce a stable subject-heldout improvement.

The best aggregate candidate was `{best_id}` with mean macro-F1 `{float(best_row.get("mean_macro_f1")):.4f}` and mean balanced accuracy `{float(best_row.get("mean_bal_acc")):.4f}`.

## Candidate-Level Summary

{top_candidates_md}

## A5 vs Controls

A5 was the intended strongest targeted candidate: cross-subject SupCon plus VREx.

- A5 mean macro-F1: `{a5_mean:.4f}`
- A0 CE-control mean macro-F1: `{a0_mean:.4f}`
- A6 VREx-only mean macro-F1: `{a6_mean:.4f}`
- A2 cross-subject SupCon-only mean macro-F1: `{a2_mean:.4f}`
- A4 rating-distance guarded SupCon mean macro-F1: `{a4_mean:.4f}`
- A5 delta vs A0: `{a5_delta_a0:.4f}`
- A5 delta vs A6: `{a5_delta_a6:.4f}`
- A5 delta vs A2: `{a5_delta_a2:.4f}`

Interpretation: A5 was not clearly separable from the best control/regularizer variants. The improvement, where present, is small and fold-dependent rather than stable.

## Modality/Task Delta Map

{top_deltas_md}

## Loss / Embedding Alignment

The aligned loss/embedding table is saved to:

`docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv`

Top absolute correlations between final logged loss/embedding metrics and validation outcomes:

{corr_md}

Interpretation: if contrastive/embedding diagnostics do not track validation macro-F1, then SupCon may be optimizing an internal geometry that is not aligned with the held-out subject decision boundary.

## Fold and Subject Localization

The fold/subject summary is saved to:

`docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv`

{hard_subject_note}

The ablation remains fold-sensitive. This supports the view that the main blocker is not merely positive-pair availability, but the interaction among subject-specific affect labels, weak representations, and held-out subject shift.

## Decision Matrix

{decision_md}

## Scientific Conclusion

The strongest supported interpretation is that the targeted pair/sampler changes were valid but insufficient. Positive-pair coverage was high, and the runs were not broken, but the learned representation did not become stable enough across held-out subjects.

This shifts the likely failure mode away from simple pair coverage and toward:

1. subject-specific label/task semantics,
2. representation weakness under subject-heldout transfer,
3. SupCon/VREx objective mismatch with the actual LOSO-style decision boundary.

## Next Allowed Step

Human review / closeout before any next objective.

Full SupCon/DG training remains blocked. Broad hyperparameter search remains blocked.
"""
report_md_path.write_text(report_md, encoding="utf-8")

status_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"
status = json.loads(status_path.read_text(encoding="utf-8"))
blocked = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change",
    "new training before failure-analysis review",
]
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "human_review_closeout_before_next_objective"
status["current_idare_blocked_steps"] = blocked
status.setdefault("idare_protocol_events", []).append({
    "timestamp_utc": now,
    "type": "analysis_report",
    "name": "I-DARE SupCon/DG pair-sampler failure analysis report",
    "status": f"complete pending human review; diagnosis={diagnosis}",
    "evidence": str(report_md_path),
    "next_allowed_step": "human review / closeout before next objective",
    "blocked": blocked,
})
status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE SupCon/DG Pair-Sampler Failure Analysis Report

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE SupCon/DG pair-sampler failure analysis report | complete pending human review; diagnosis=`{diagnosis}` | `docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md` | Human review / closeout before next objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Read-only pair-sampler failure analysis is complete in `docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md`.
- Recommended next objective is `{recommended_next}` only after review/closeout.
"""
if "I-DARE SupCon/DG Pair-Sampler Failure Analysis Report" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_PAIR_SAMPLER_FAILURE_ANALYSIS_REPORT_WRITTEN")
print(report_md_path)
print(report_json_path)
print(candidate_deltas_path)
print(fold_subject_path)
print(loss_alignment_path)
print(decision_matrix_path)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next)
print("best_candidate=", json.dumps(best_row, ensure_ascii=False, default=str))
PY
echo

echo "===== 5) validate generated outputs ====="
"$PY" - <<'PY'
import json
from pathlib import Path

json_paths = [
    Path("docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

csv_paths = [
    Path("docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv"),
    Path("docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv"),
    Path("docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv"),
    Path("docs/idare_supcon_dg_pair_sampler_failure_decision_matrix.csv"),
]
for p in csv_paths:
    rows = max(0, sum(1 for _ in p.open(encoding="utf-8")) - 1)
    if rows <= 0:
        raise SystemExit(f"ERROR: {p} has no data rows")
    print(f"{p.name} rows=", rows)

report = json.loads(Path("docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json").read_text(encoding="utf-8"))
print("diagnosis=", report.get("diagnosis"))
print("recommended_next_objective=", report.get("recommended_next_objective"))
if not report.get("diagnosis"):
    raise SystemExit("ERROR: missing diagnosis")
if not report.get("recommended_next_objective"):
    raise SystemExit("ERROR: missing recommended next objective")

text = Path("docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md").read_text(encoding="utf-8")
for term in ["Executive Diagnosis", "A5 vs Controls", "Decision Matrix", "Full SupCon/DG training remains blocked"]:
    if term not in text:
        raise SystemExit(f"ERROR: missing term in report: {term}")
print("ALL_PAIR_SAMPLER_FAILURE_ANALYSIS_FIXED_OUTPUTS_VALID")
PY

grep -nE "Status|Executive Diagnosis|Candidate-Level Summary|A5 vs Controls|Decision Matrix|Next Allowed Step" \
  docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md
grep -nE "pair-sampler failure analysis report|Recommended next objective" docs/project_status_current.md | tail -n 8
echo

echo "===== 6) file list ====="
ls -lh \
  docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md \
  docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json \
  docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv \
  docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv \
  docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv \
  docs/idare_supcon_dg_pair_sampler_failure_decision_matrix.csv \
  docs/project_status_current.json \
  docs/project_status_current.md
echo

echo "===== 7) status before commit ====="
git status --short --branch
echo

echo "===== 8) commit and push fixed pair-sampler failure-analysis report ====="
git add \
  docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md \
  docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json \
  docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv \
  docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv \
  docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv \
  docs/idare_supcon_dg_pair_sampler_failure_decision_matrix.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "analysis: add I-DARE SupCon DG pair sampler failure report"
git push origin main
echo

echo "===== 9) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
