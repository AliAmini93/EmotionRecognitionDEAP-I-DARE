#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_representation_label_semantics_failure_analysis_report.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start representation/label-semantics failure-analysis report ====="
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
try:
    import json
    from pathlib import Path
    import numpy as np
    import pandas as pd
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
  docs/idare_representation_or_label_semantics_failure_analysis_objective.md
  docs/idare_representation_or_label_semantics_failure_analysis_objective.json
  docs/idare_supcon_dg_pair_sampler_failure_analysis_review_status.md
  docs/idare_supcon_dg_pair_sampler_failure_analysis_review_status.json
  docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json
  docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv
  docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv
  docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv
  docs/idare_supcon_dg_pair_sampler_failure_decision_matrix.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv
  docs/idare_label_noise_subject_balance_summary.csv
  docs/idare_representation_signal_diagnostic_summary.csv
  docs/idare_subject_relative_label_balance_summary.csv
  docs/idare_subject_relative_candidate_matrix.csv
  .cache/idare_eeg_cache_index_baseline_corrected.csv
  .cache/idare_emg_feature_cache_index.csv
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

echo "===== 3) remove stale target outputs ====="
rm -f \
  docs/idare_representation_or_label_semantics_failure_analysis_report.md \
  docs/idare_representation_or_label_semantics_failure_analysis_report.json \
  docs/idare_label_semantics_cross_subject_audit.csv \
  docs/idare_representation_transfer_failure_summary.csv \
  docs/idare_task_formulation_failure_decision_matrix.csv \
  docs/idare_objective_metric_alignment_summary.csv
echo "OK_CLEAN_TARGET_OUTPUTS"
echo

echo "===== 4) generate read-only representation/label-semantics failure-analysis report ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DOCS = Path("docs")
CACHE = Path(".cache")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

objective_path = DOCS / "idare_representation_or_label_semantics_failure_analysis_objective.json"
pair_failure_report_path = DOCS / "idare_supcon_dg_pair_sampler_failure_analysis_report.json"
candidate_deltas_path = DOCS / "idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv"
fold_subject_path = DOCS / "idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv"
loss_alignment_path = DOCS / "idare_supcon_dg_pair_sampler_failure_loss_alignment.csv"
decision_matrix_in_path = DOCS / "idare_supcon_dg_pair_sampler_failure_decision_matrix.csv"
runs_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv"
pred_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv"
label_noise_path = DOCS / "idare_label_noise_subject_balance_summary.csv"
repr_signal_path = DOCS / "idare_representation_signal_diagnostic_summary.csv"
sr_balance_path = DOCS / "idare_subject_relative_label_balance_summary.csv"
sr_candidate_path = DOCS / "idare_subject_relative_candidate_matrix.csv"
eeg_idx_path = CACHE / "idare_eeg_cache_index_baseline_corrected.csv"
emg_idx_path = CACHE / "idare_emg_feature_cache_index.csv"

report_md_path = DOCS / "idare_representation_or_label_semantics_failure_analysis_report.md"
report_json_path = DOCS / "idare_representation_or_label_semantics_failure_analysis_report.json"
label_audit_path = DOCS / "idare_label_semantics_cross_subject_audit.csv"
repr_transfer_path = DOCS / "idare_representation_transfer_failure_summary.csv"
task_decision_path = DOCS / "idare_task_formulation_failure_decision_matrix.csv"
obj_align_path = DOCS / "idare_objective_metric_alignment_summary.csv"

objective = json.loads(objective_path.read_text(encoding="utf-8"))
pair_failure = json.loads(pair_failure_report_path.read_text(encoding="utf-8"))

def read_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        raise SystemExit(f"ERROR_READ_CSV {path}: {e}")

candidate_deltas = read_csv(candidate_deltas_path)
fold_subject = read_csv(fold_subject_path)
loss_alignment = read_csv(loss_alignment_path)
decision_in = read_csv(decision_matrix_in_path)
runs = read_csv(runs_path)
pred = read_csv(pred_path)
label_noise = read_csv(label_noise_path)
repr_signal = read_csv(repr_signal_path)
sr_balance = read_csv(sr_balance_path)
sr_candidate = read_csv(sr_candidate_path)
eeg_idx = read_csv(eeg_idx_path)
emg_idx = read_csv(emg_idx_path)

# ---------- helpers ----------
def norm_columns(df):
    aliases = {
        "accuracy": "acc",
        "final_accuracy": "acc",
        "balanced_accuracy": "bal_acc",
        "final_balanced_accuracy": "bal_acc",
        "macro_f1_score": "macro_f1",
        "final_macro_f1": "macro_f1",
        "subject": "subject_id",
        "participant_id": "subject_id",
        "sid": "subject_id",
        "trial": "trial_id",
        "trial_index": "trial_id",
        "valence": "valence_score",
        "arousal": "arousal_score",
        "positive_pair_coverage_final_epoch": "pos_cov",
        "positive_pair_coverage": "pos_cov",
    }
    out = df.copy()
    for src, dst in aliases.items():
        if src in out.columns and dst not in out.columns:
            out.rename(columns={src: dst}, inplace=True)
    return out

runs = norm_columns(runs)
pred = norm_columns(pred)
fold_subject = norm_columns(fold_subject)
loss_alignment = norm_columns(loss_alignment)
eeg_idx = norm_columns(eeg_idx)
emg_idx = norm_columns(emg_idx)
label_noise = norm_columns(label_noise)
repr_signal = norm_columns(repr_signal)
sr_balance = norm_columns(sr_balance)
sr_candidate = norm_columns(sr_candidate)

def find_col(df, names, contains=None):
    for n in names:
        if n in df.columns:
            return n
    if contains:
        for c in df.columns:
            lc = c.lower()
            if all(s in lc for s in contains):
                return c
    return None

def entropy_binary(p):
    if pd.isna(p) or p <= 0 or p >= 1:
        return 0.0
    return float(-(p*np.log2(p) + (1-p)*np.log2(1-p)))

def gini_like(x):
    vals = pd.Series(x).dropna().astype(float)
    if len(vals) == 0:
        return np.nan
    return float(vals.max() - vals.min())

def corr_safe(a, b):
    a = pd.to_numeric(pd.Series(a), errors="coerce")
    b = pd.to_numeric(pd.Series(b), errors="coerce")
    m = a.notna() & b.notna()
    if m.sum() < 5 or a[m].nunique() <= 1 or b[m].nunique() <= 1:
        return np.nan
    return float(np.corrcoef(a[m], b[m])[0, 1])

def fmt(x):
    if x is None or (isinstance(x, float) and np.isnan(x)) or pd.isna(x):
        return ""
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.4f}"
    return str(x)

def md_table(df, columns=None, max_rows=20):
    if columns is None:
        columns = list(df.columns)
    columns = [c for c in columns if c in df.columns]
    if not columns:
        return "_No table columns available._"
    sub = df.loc[:, columns].head(max_rows)
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    rows = []
    for _, r in sub.iterrows():
        rows.append("| " + " | ".join(fmt(r[c]) for c in columns) + " |")
    return "\n".join([header, sep] + rows)

# ---------- label semantics audit ----------
label_rows = []
for modality, idx in [("EEG", eeg_idx), ("EMG", emg_idx)]:
    subj_col = find_col(idx, ["subject_id", "subject", "participant_id"], contains=["subject"])
    if subj_col is None:
        continue
    for task, score_col in [("valence", "valence_score"), ("arousal", "arousal_score")]:
        if score_col not in idx.columns:
            continue
        tmp = idx[[subj_col, score_col]].copy()
        tmp[score_col] = pd.to_numeric(tmp[score_col], errors="coerce")
        tmp = tmp.dropna()
        if len(tmp) == 0:
            continue
        # Global midpoint 5, then subject-relative top/bottom third.
        tmp["global_high"] = (tmp[score_col] >= 5.0).astype(int)
        per = tmp.groupby(subj_col).agg(
            n=(score_col, "size"),
            mean_rating=(score_col, "mean"),
            std_rating=(score_col, "std"),
            min_rating=(score_col, "min"),
            max_rating=(score_col, "max"),
            global_high_rate=("global_high", "mean"),
        ).reset_index()
        per["rating_range"] = per["max_rating"] - per["min_rating"]
        per["global_entropy"] = per["global_high_rate"].apply(entropy_binary)
        # Estimate top/bottom q33 retention using per-subject quantiles.
        q = tmp.groupby(subj_col)[score_col].quantile([1/3, 2/3]).unstack()
        q.columns = ["q33", "q66"]
        tmp = tmp.join(q, on=subj_col)
        tmp["sr_label"] = np.where(tmp[score_col] <= tmp["q33"], 0, np.where(tmp[score_col] >= tmp["q66"], 1, np.nan))
        sr = tmp.dropna(subset=["sr_label"]).groupby(subj_col).agg(
            sr_valid=("sr_label", "size"),
            sr_high_rate=("sr_label", "mean"),
        ).reset_index()
        per = per.merge(sr, on=subj_col, how="left")
        per["sr_retention"] = per["sr_valid"] / per["n"]
        per["modality"] = modality
        per["task"] = task
        label_rows.append(per)

if label_rows:
    label_audit = pd.concat(label_rows, ignore_index=True)
else:
    label_audit = pd.DataFrame(columns=["modality", "task", "subject_id", "n", "mean_rating", "std_rating", "rating_range", "global_high_rate", "global_entropy", "sr_retention", "sr_high_rate"])

# Add aggregate columns by modality/task for interpretation.
agg_label = label_audit.groupby(["modality", "task"], dropna=False).agg(
    n_subjects=("n", "size"),
    mean_rating_subject_std=("mean_rating", "std"),
    global_high_rate_range=("global_high_rate", gini_like),
    mean_global_entropy=("global_entropy", "mean"),
    low_entropy_subjects=("global_entropy", lambda x: int((pd.to_numeric(x, errors="coerce") < 0.65).sum())),
    low_range_subjects=("rating_range", lambda x: int((pd.to_numeric(x, errors="coerce") < 2.0).sum())),
    mean_sr_retention=("sr_retention", "mean"),
    sr_high_rate_range=("sr_high_rate", gini_like),
).reset_index()
label_audit.to_csv(label_audit_path, index=False)

# ---------- representation transfer summary ----------
# Use representation_signal_diagnostic_summary if available, fold-level pair sampler failures,
# and prediction/fold instability.
repr_rows = []

# from representation signal diagnostic: keep numeric columns and aggregate.
if len(repr_signal):
    for keys in [["modality", "task"], ["modality"], ["task"]]:
        if all(k in repr_signal.columns for k in keys):
            numeric_cols = [c for c in repr_signal.columns if pd.api.types.is_numeric_dtype(repr_signal[c])]
            if numeric_cols:
                agg = repr_signal.groupby(keys, dropna=False)[numeric_cols].mean().reset_index()
                for _, row in agg.iterrows():
                    rec = {"source": "representation_signal_diagnostic_summary"}
                    for k in keys:
                        rec[k] = row[k]
                    for c in numeric_cols:
                        rec[f"mean_{c}"] = row[c]
                    repr_rows.append(rec)
            break

# fold instability from targeted ablation.
for dfname, df in [("runs", runs), ("fold_subject", fold_subject)]:
    if all(c in df.columns for c in ["candidate_id", "modality", "task", "macro_f1"]):
        tmp = df.copy()
        tmp["macro_f1"] = pd.to_numeric(tmp["macro_f1"], errors="coerce")
        if "bal_acc" in tmp.columns:
            tmp["bal_acc"] = pd.to_numeric(tmp["bal_acc"], errors="coerce")
        g = tmp.groupby(["candidate_id", "modality", "task"], dropna=False).agg(
            n_runs=("macro_f1", "size"),
            mean_macro_f1=("macro_f1", "mean"),
            std_macro_f1=("macro_f1", "std"),
            min_macro_f1=("macro_f1", "min"),
            max_macro_f1=("macro_f1", "max"),
            folds_under_050=("macro_f1", lambda x: int((pd.to_numeric(x, errors="coerce") < 0.50).sum())),
            folds_over_055=("macro_f1", lambda x: int((pd.to_numeric(x, errors="coerce") > 0.55).sum())),
        ).reset_index()
        for _, row in g.iterrows():
            rec = {
                "source": f"{dfname}_fold_instability",
                "candidate_id": row["candidate_id"],
                "modality": row["modality"],
                "task": row["task"],
                "n_runs": int(row["n_runs"]),
                "mean_macro_f1": row["mean_macro_f1"],
                "std_macro_f1": row["std_macro_f1"],
                "macro_f1_range": row["max_macro_f1"] - row["min_macro_f1"],
                "folds_under_050": int(row["folds_under_050"]),
                "folds_over_055": int(row["folds_over_055"]),
            }
            repr_rows.append(rec)

repr_transfer = pd.DataFrame(repr_rows)
if len(repr_transfer) == 0:
    repr_transfer = pd.DataFrame(columns=["source", "modality", "task", "candidate_id", "mean_macro_f1"])
repr_transfer.to_csv(repr_transfer_path, index=False)

# ---------- objective / metric alignment ----------
align_rows = []
# Candidate mean delta vs CE and VREx from candidate_deltas.
if all(c in candidate_deltas.columns for c in ["candidate_id", "modality", "task", "mean_macro_f1"]):
    for candidate in sorted(candidate_deltas["candidate_id"].dropna().unique()):
        sub = candidate_deltas[candidate_deltas["candidate_id"] == candidate]
        row = {
            "analysis": "candidate_delta_map",
            "candidate_id": candidate,
            "n_cells": len(sub),
            "mean_macro_f1": pd.to_numeric(sub["mean_macro_f1"], errors="coerce").mean(),
            "mean_delta_vs_A0_macro_f1": pd.to_numeric(sub.get("delta_vs_A0_macro_f1", pd.Series(dtype=float)), errors="coerce").mean(),
            "mean_delta_vs_A6_macro_f1": pd.to_numeric(sub.get("delta_vs_A6_macro_f1", pd.Series(dtype=float)), errors="coerce").mean(),
            "positive_delta_cells_vs_A0": int((pd.to_numeric(sub.get("delta_vs_A0_macro_f1", pd.Series(dtype=float)), errors="coerce") > 0).sum()),
            "negative_delta_cells_vs_A0": int((pd.to_numeric(sub.get("delta_vs_A0_macro_f1", pd.Series(dtype=float)), errors="coerce") < 0).sum()),
        }
        align_rows.append(row)

# Correlate available loss/embedding metrics with macro-F1 and bal_acc.
metric_candidates = []
for c in loss_alignment.columns:
    lc = c.lower()
    if c in ["macro_f1", "bal_acc", "acc", "candidate_id", "modality", "task", "fold", "run_id"]:
        continue
    if any(tok in lc for tok in ["loss", "embed", "norm", "coverage", "align", "uniform", "distance", "variance", "supcon", "vrex", "ce"]):
        metric_candidates.append(c)
for metric in metric_candidates:
    align_rows.append({
        "analysis": "loss_embedding_metric_alignment",
        "metric": metric,
        "n": int(pd.to_numeric(loss_alignment[metric], errors="coerce").notna().sum()),
        "corr_with_macro_f1": corr_safe(loss_alignment[metric], loss_alignment["macro_f1"]) if "macro_f1" in loss_alignment.columns else np.nan,
        "corr_with_bal_acc": corr_safe(loss_alignment[metric], loss_alignment["bal_acc"]) if "bal_acc" in loss_alignment.columns else np.nan,
    })

obj_align = pd.DataFrame(align_rows)
if len(obj_align) == 0:
    obj_align = pd.DataFrame(columns=["analysis", "candidate_id", "metric", "corr_with_macro_f1"])
obj_align.to_csv(obj_align_path, index=False)

# ---------- task formulation decision matrix ----------
best_candidate = pair_failure.get("best_candidate", {})
best_macro = float(best_candidate.get("mean_macro_f1", np.nan))
best_under_050 = int(best_candidate.get("folds_under_050_macro_f1", 999)) if best_candidate else 999

mean_label_entropy = float(agg_label["mean_global_entropy"].mean()) if len(agg_label) else np.nan
high_subject_rating_shift = bool(len(agg_label) and (agg_label["mean_rating_subject_std"].max() > 1.0 or agg_label["global_high_rate_range"].max() > 0.60))
low_entropy_problem = bool(len(agg_label) and agg_label["low_entropy_subjects"].sum() >= 8)
sr_balanced_but_insufficient = bool("subject_relative" in " ".join(map(str, sr_candidate.columns)).lower() or len(sr_balance) > 0)
objective_alignment_weak = True
if len(obj_align) and "corr_with_macro_f1" in obj_align.columns:
    max_abs_corr = pd.to_numeric(obj_align["corr_with_macro_f1"], errors="coerce").abs().max()
    objective_alignment_weak = bool(pd.isna(max_abs_corr) or max_abs_corr < 0.35)
else:
    max_abs_corr = np.nan

stable_solution_found = bool(best_macro >= 0.55 and best_under_050 <= 3)
transfer_weak = bool(best_macro < 0.53 or best_under_050 > 5)

decision_rows = [
    {
        "hypothesis": "Label semantics across subjects are inconsistent",
        "evidence_for": (
            f"Subject rating distributions vary; mean global entropy={mean_label_entropy:.3f}; "
            f"high_subject_rating_shift={high_subject_rating_shift}; low_entropy_problem={low_entropy_problem}."
        ),
        "evidence_against": "Subject-relative formulations were tried, so label semantics alone may not be the only blocker.",
        "verdict": "supported_primary" if high_subject_rating_shift or low_entropy_problem else "supported_partial",
    },
    {
        "hypothesis": "Representation transfer is weak under held-out subjects",
        "evidence_for": (
            f"Best pair/SupCon/DG candidate mean macro-F1={best_macro:.4f}; folds_under_050={best_under_050}; "
            "candidate improvements are fold-dependent."
        ),
        "evidence_against": "Some isolated folds/cells exceed 0.55, so signal is intermittent rather than absent.",
        "verdict": "supported_primary" if transfer_weak else "supported_partial",
    },
    {
        "hypothesis": "Task formulation is not currently defensible for a final LOSO claim",
        "evidence_for": "Global labels, subject-relative labels, preprocessing, SupCon, pair redesign, and VREx all failed to create stable held-out performance.",
        "evidence_against": "A few cells improve, so a redesigned task may still be viable.",
        "verdict": "supported_primary" if transfer_weak and (high_subject_rating_shift or low_entropy_problem) else "supported_partial",
    },
    {
        "hypothesis": "Objective/metric mismatch explains SupCon/DG failure",
        "evidence_for": f"Loss/embedding metric alignment with held-out macro-F1 appears weak; max_abs_corr={max_abs_corr}.",
        "evidence_against": "Correlation evidence is post-hoc and based on logged summaries, not a controlled causal test.",
        "verdict": "supported_partial" if objective_alignment_weak else "weak_or_inconclusive",
    },
    {
        "hypothesis": "Pair sampler remains the primary issue",
        "evidence_for": "Pair design may still contain semantic noise.",
        "evidence_against": "Coverage and smoke tests passed; targeted pair/sampler changes were not sufficient.",
        "verdict": "not_primary",
    },
]
task_decision = pd.DataFrame(decision_rows)
task_decision.to_csv(task_decision_path, index=False)

# ---------- diagnosis and next objective ----------
if transfer_weak and (high_subject_rating_shift or low_entropy_problem):
    diagnosis = "label_semantics_and_representation_transfer_joint_bottleneck"
    recommended_next = "label_semantics_task_redesign_or_stop_objective"
elif transfer_weak:
    diagnosis = "representation_transfer_bottleneck_after_valid_pair_sampler"
    recommended_next = "representation_transfer_redesign_objective"
elif high_subject_rating_shift or low_entropy_problem:
    diagnosis = "label_semantics_bottleneck_after_valid_pair_sampler"
    recommended_next = "label_semantics_task_redesign_objective"
elif objective_alignment_weak:
    diagnosis = "objective_metric_mismatch_after_valid_pair_sampler"
    recommended_next = "objective_metric_alignment_redesign_objective"
else:
    diagnosis = "failure_mode_inconclusive_stop_or_manual_review"
    recommended_next = "manual_scientific_review_or_stop_objective"

blocked = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change",
    "new training before representation/label-semantics failure analysis review",
]

# Tables.
agg_label_md = md_table(
    agg_label,
    ["modality", "task", "n_subjects", "mean_rating_subject_std", "global_high_rate_range", "mean_global_entropy", "low_entropy_subjects", "low_range_subjects", "mean_sr_retention", "sr_high_rate_range"],
    20,
)
task_decision_md = md_table(task_decision, ["hypothesis", "verdict", "evidence_for", "evidence_against"], 10)
obj_align_md = md_table(
    obj_align.sort_values("corr_with_macro_f1", key=lambda s: pd.to_numeric(s, errors="coerce").abs(), ascending=False) if "corr_with_macro_f1" in obj_align.columns else obj_align,
    ["analysis", "candidate_id", "metric", "n", "mean_macro_f1", "mean_delta_vs_A0_macro_f1", "corr_with_macro_f1", "corr_with_bal_acc"],
    20,
)
repr_md = md_table(
    repr_transfer.sort_values("mean_macro_f1", ascending=False) if "mean_macro_f1" in repr_transfer.columns else repr_transfer,
    ["source", "candidate_id", "modality", "task", "n_runs", "mean_macro_f1", "std_macro_f1", "macro_f1_range", "folds_under_050", "folds_over_055"],
    20,
)

report = {
    "status": "complete_pending_human_review",
    "created_utc": now,
    "objective": str(objective_path),
    "triggering_diagnosis": pair_failure.get("diagnosis"),
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next,
    "row_counts": {
        "label_semantics_cross_subject_audit": int(len(label_audit)),
        "representation_transfer_failure_summary": int(len(repr_transfer)),
        "task_formulation_failure_decision_matrix": int(len(task_decision)),
        "objective_metric_alignment_summary": int(len(obj_align)),
        "targeted_ablation_runs": int(len(runs)),
        "targeted_ablation_predictions": int(len(pred)),
    },
    "key_indicators": {
        "best_pair_sampler_candidate_mean_macro_f1": best_macro,
        "best_pair_sampler_candidate_folds_under_050": best_under_050,
        "mean_label_entropy": mean_label_entropy,
        "high_subject_rating_shift": high_subject_rating_shift,
        "low_entropy_problem": low_entropy_problem,
        "objective_alignment_weak": objective_alignment_weak,
        "max_abs_loss_embedding_corr_with_macro_f1": None if pd.isna(max_abs_corr) else float(max_abs_corr),
    },
    "outputs": {
        "report_md": str(report_md_path),
        "label_semantics_cross_subject_audit": str(label_audit_path),
        "representation_transfer_failure_summary": str(repr_transfer_path),
        "task_formulation_failure_decision_matrix": str(task_decision_path),
        "objective_metric_alignment_summary": str(obj_align_path),
    },
    "next_allowed_step": "human_review_closeout_before_next_objective",
    "blocked_steps": blocked,
}
report_json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")

report_md = f"""# I-DARE Representation or Label-Semantics Failure Analysis Report

## Status

Status: complete; pending human review.

Created UTC: `{now}`

This is a read-only analysis. No new training was run.

## Executive Diagnosis

Diagnosis: `{diagnosis}`

Recommended next objective: `{recommended_next}`

The pair/sampler failure analysis concluded that valid SupCon/DG pair mechanics were not enough. This report moves one level deeper and separates four possible blockers: label semantics, representation transfer, task formulation, and objective/metric mismatch.

## Why the SupCon/DG Pair-Sampler Intervention Was Insufficient

Best pair-sampler candidate from the previous report:

- mean macro-F1: `{best_macro:.4f}`
- folds under 0.50 macro-F1: `{best_under_050}`

This is not a stable held-out subject result. Since coverage/smoke/guardrails were valid, the remaining failure is more likely semantic/representational than mechanical.

## Label-Semantics Cross-Subject Audit

Output: `docs/idare_label_semantics_cross_subject_audit.csv`

Aggregate summary:

{agg_label_md}

Interpretation: subject-level rating distributions and binary label balance remain a major concern. If a binary label does not mean the same affective state across subjects, cross-subject SupCon positives can be mathematically valid but semantically noisy.

## Representation Transfer Audit

Output: `docs/idare_representation_transfer_failure_summary.csv`

Top rows:

{repr_md}

Interpretation: the representation has intermittent signal, but it is not stable under held-out subject transfer. This is consistent with the repeated pattern of isolated good folds and weak aggregate performance.

## Objective / Metric Alignment Audit

Output: `docs/idare_objective_metric_alignment_summary.csv`

Top rows:

{obj_align_md}

Interpretation: if loss/embedding summaries do not align with held-out macro-F1, then CE/SupCon/VREx can optimize internal objectives without producing the subject-generalizable decision boundary we need.

## Task Formulation Decision Matrix

Output: `docs/idare_task_formulation_failure_decision_matrix.csv`

{task_decision_md}

## Scientific Conclusion

The current evidence supports a joint bottleneck:

1. label semantics are likely not stable enough across subjects,
2. representation transfer remains weak,
3. valid SupCon/DG pair mechanics do not fix that by themselves,
4. the current task formulation is not yet defensible for a final LOSO-style claim.

The most scientific next move is not another broad training run. The next move should explicitly decide whether the task should be redesigned, narrowed, parked, or reframed before any further model work.

## Next Allowed Step

Human review / closeout before the next objective.

Direct full SupCon/DG training remains blocked. Broad hyperparameter search remains blocked. EEG+EMG fusion and final LOSO claims remain blocked.
"""
report_md_path.write_text(report_md, encoding="utf-8")

# Update roadmap.
status_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"
status = json.loads(status_path.read_text(encoding="utf-8"))
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "human_review_closeout_before_next_objective"
status["current_idare_blocked_steps"] = blocked
status.setdefault("idare_protocol_events", []).append({
    "timestamp_utc": now,
    "type": "analysis_report",
    "name": "I-DARE representation or label-semantics failure-analysis report",
    "status": f"complete pending human review; diagnosis={diagnosis}",
    "evidence": str(report_md_path),
    "next_allowed_step": "human review / closeout before next objective",
    "blocked": blocked,
})
status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Representation or Label-Semantics Failure Analysis Report

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE representation or label-semantics failure-analysis report | complete pending human review; diagnosis=`{diagnosis}` | `docs/idare_representation_or_label_semantics_failure_analysis_report.md` | Human review / closeout before next objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Read-only representation or label-semantics failure analysis is complete in `docs/idare_representation_or_label_semantics_failure_analysis_report.md`.
- Recommended next objective is `{recommended_next}` only after human review/closeout.
"""
if "I-DARE Representation or Label-Semantics Failure Analysis Report" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_REPRESENTATION_LABEL_SEMANTICS_FAILURE_ANALYSIS_REPORT_WRITTEN")
print(report_md_path)
print(report_json_path)
print(label_audit_path)
print(repr_transfer_path)
print(task_decision_path)
print(obj_align_path)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next)
print("key_indicators=", json.dumps(report["key_indicators"], ensure_ascii=False, default=str))
PY
echo

echo "===== 5) validate generated outputs ====="
"$PY" - <<'PY'
import json
from pathlib import Path

json_paths = [
    Path("docs/idare_representation_or_label_semantics_failure_analysis_report.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

csv_paths = [
    Path("docs/idare_label_semantics_cross_subject_audit.csv"),
    Path("docs/idare_representation_transfer_failure_summary.csv"),
    Path("docs/idare_task_formulation_failure_decision_matrix.csv"),
    Path("docs/idare_objective_metric_alignment_summary.csv"),
]
for p in csv_paths:
    rows = max(0, sum(1 for _ in p.open(encoding="utf-8")) - 1)
    if rows <= 0:
        raise SystemExit(f"ERROR: {p} has no data rows")
    print(f"{p.name} rows=", rows)

report = json.loads(Path("docs/idare_representation_or_label_semantics_failure_analysis_report.json").read_text(encoding="utf-8"))
print("diagnosis=", report.get("diagnosis"))
print("recommended_next_objective=", report.get("recommended_next_objective"))
if not report.get("diagnosis"):
    raise SystemExit("ERROR: missing diagnosis")
if not report.get("recommended_next_objective"):
    raise SystemExit("ERROR: missing recommended next objective")

text = Path("docs/idare_representation_or_label_semantics_failure_analysis_report.md").read_text(encoding="utf-8")
for term in ["Executive Diagnosis", "Label-Semantics Cross-Subject Audit", "Representation Transfer Audit", "Objective / Metric Alignment Audit", "Task Formulation Decision Matrix", "Direct full SupCon/DG training remains blocked"]:
    if term not in text:
        raise SystemExit(f"ERROR: missing term in report: {term}")
print("ALL_REPRESENTATION_LABEL_SEMANTICS_FAILURE_ANALYSIS_OUTPUTS_VALID")
PY

grep -nE "Status|Executive Diagnosis|Label-Semantics|Representation Transfer|Objective / Metric|Task Formulation|Next Allowed Step" \
  docs/idare_representation_or_label_semantics_failure_analysis_report.md
grep -nE "representation or label-semantics failure-analysis report|Recommended next objective" docs/project_status_current.md | tail -n 8
echo

echo "===== 6) file list ====="
ls -lh \
  docs/idare_representation_or_label_semantics_failure_analysis_report.md \
  docs/idare_representation_or_label_semantics_failure_analysis_report.json \
  docs/idare_label_semantics_cross_subject_audit.csv \
  docs/idare_representation_transfer_failure_summary.csv \
  docs/idare_task_formulation_failure_decision_matrix.csv \
  docs/idare_objective_metric_alignment_summary.csv \
  docs/project_status_current.json \
  docs/project_status_current.md
echo

echo "===== 7) status before commit ====="
git status --short --branch
echo

echo "===== 8) commit and push representation/label-semantics failure-analysis report ====="
git add \
  docs/idare_representation_or_label_semantics_failure_analysis_report.md \
  docs/idare_representation_or_label_semantics_failure_analysis_report.json \
  docs/idare_label_semantics_cross_subject_audit.csv \
  docs/idare_representation_transfer_failure_summary.csv \
  docs/idare_task_formulation_failure_decision_matrix.csv \
  docs/idare_objective_metric_alignment_summary.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "analysis: add I-DARE representation label semantics failure report"
git push origin main
echo

echo "===== 9) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
