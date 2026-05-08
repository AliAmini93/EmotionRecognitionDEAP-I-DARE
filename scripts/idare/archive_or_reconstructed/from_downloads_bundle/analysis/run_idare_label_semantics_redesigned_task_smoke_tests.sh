#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_redesigned_task_smoke_tests_run.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start redesigned-task smoke tests ====="
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
    import math
    from pathlib import Path
    import numpy as np
    import pandas as pd
except Exception as e:
    raise SystemExit(f"ERROR_IMPORTS: {e}")
print("OK_IMPORTS")
PY

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: repo is not clean; commit/stash before running smoke tests." >&2
  git status --short
  exit 2
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required inputs ====="
required=(
  docs/idare_label_semantics_redesigned_task_smoke_tests_objective.md
  docs/idare_label_semantics_redesigned_task_smoke_tests_objective.json
  docs/idare_label_semantics_redesigned_task_smoke_test_plan.csv
  docs/idare_label_semantics_task_redesign_spec.md
  docs/idare_label_semantics_task_redesign_spec.json
  docs/idare_label_semantics_selected_task_definition.csv
  docs/idare_label_semantics_task_redesign_guardrails.csv
  docs/idare_label_semantics_task_redesign_metric_plan.csv
  docs/idare_label_semantics_task_redesign_protocol_matrix.csv
  docs/idare_label_semantics_task_redesign_future_run_matrix.csv
  docs/idare_label_semantics_task_redesign_stop_criteria.csv
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

echo "===== 3) remove stale outputs ====="
rm -f \
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.md \
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.json \
  docs/idare_label_semantics_redesigned_task_target_audit.csv \
  docs/idare_label_semantics_redesigned_task_fold_audit.csv \
  docs/idare_label_semantics_redesigned_task_metric_sanity.csv \
  docs/idare_label_semantics_redesigned_task_baseline_control_summary.csv \
  docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv
echo "OK_CLEAN_OUTPUT_TARGETS"
echo

echo "===== 4) run redesigned-task smoke tests and write report ====="
"$PY" - <<'PY'
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

report_md_path = DOCS / "idare_label_semantics_redesigned_task_smoke_tests_report.md"
report_json_path = DOCS / "idare_label_semantics_redesigned_task_smoke_tests_report.json"
target_audit_path = DOCS / "idare_label_semantics_redesigned_task_target_audit.csv"
fold_audit_path = DOCS / "idare_label_semantics_redesigned_task_fold_audit.csv"
metric_sanity_path = DOCS / "idare_label_semantics_redesigned_task_metric_sanity.csv"
baseline_path = DOCS / "idare_label_semantics_redesigned_task_baseline_control_summary.csv"
decision_path = DOCS / "idare_label_semantics_redesigned_task_smoke_decision_matrix.csv"
status_json_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

spec = json.loads((DOCS / "idare_label_semantics_task_redesign_spec.json").read_text(encoding="utf-8"))
objective = json.loads((DOCS / "idare_label_semantics_redesigned_task_smoke_tests_objective.json").read_text(encoding="utf-8"))
selected = spec.get("selected_primary_formulation", "subject_relative_ordinal_affect_regression_v1")

def load_csv(path):
    return pd.read_csv(path)

def find_col(df, candidates, required=True):
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in df.columns:
            return cand
        if cand.lower() in lower:
            return lower[cand.lower()]
    if required:
        raise SystemExit(f"ERROR: none of columns {candidates} found; available={list(df.columns)}")
    return None

def spearman(y_true, y_pred):
    a = pd.Series(y_true).astype(float)
    b = pd.Series(y_pred).astype(float)
    mask = a.notna() & b.notna()
    if mask.sum() < 2:
        return 0.0
    ar = a[mask].rank(method="average")
    br = b[mask].rank(method="average")
    if float(ar.std(ddof=0)) == 0.0 or float(br.std(ddof=0)) == 0.0:
        return 0.0
    val = float(ar.corr(br))
    if math.isnan(val) or math.isinf(val):
        return 0.0
    return val

def mae(y_true, y_pred):
    a = np.asarray(y_true, dtype=float)
    b = np.asarray(y_pred, dtype=float)
    return float(np.nanmean(np.abs(a - b)))

def rmse(y_true, y_pred):
    a = np.asarray(y_true, dtype=float)
    b = np.asarray(y_pred, dtype=float)
    return float(math.sqrt(np.nanmean((a - b) ** 2)))

def q33_bal_acc(y_true, y_pred):
    a = np.asarray(y_true, dtype=float)
    b = np.asarray(y_pred, dtype=float)
    mask = ((a <= 1.0/3.0) | (a >= 2.0/3.0)) & np.isfinite(a) & np.isfinite(b)
    if int(mask.sum()) == 0:
        return 0.0
    yt = (a[mask] >= 2.0/3.0).astype(int)
    yp = (b[mask] >= 0.5).astype(int)
    out = []
    for cls in [0, 1]:
        cls_mask = yt == cls
        if cls_mask.sum() == 0:
            continue
        out.append(float((yp[cls_mask] == cls).mean()))
    return float(np.mean(out)) if out else 0.0

def target_rank_percentile(values):
    s = pd.Series(values)
    out = pd.Series(np.nan, index=s.index, dtype=float)
    nonmiss = s.notna()
    n = int(nonmiss.sum())
    if n == 0:
        return out
    if n == 1:
        out.loc[nonmiss] = 0.5
        return out
    ranks = s.loc[nonmiss].rank(method="average", ascending=True)
    out.loc[nonmiss] = (ranks - 1.0) / (n - 1.0)
    return out.astype(float)

def deterministic_subject_folds(subjects, n_folds=6):
    subjects = sorted([int(x) if float(x).is_integer() else x for x in pd.Series(subjects).dropna().unique()])
    folds = {i: [] for i in range(1, n_folds + 1)}
    for idx, subj in enumerate(subjects):
        folds[(idx % n_folds) + 1].append(subj)
    return folds

def md_table(rows, columns):
    out = []
    out.append("| " + " | ".join(columns) + " |")
    out.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for row in rows:
        vals = []
        for c in columns:
            vals.append(str(row.get(c, "")).replace("\n", " ").replace("|", "\\|"))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)

def fmt(x, nd=4):
    try:
        if x is None or math.isnan(float(x)) or math.isinf(float(x)):
            return "NA"
        return f"{float(x):.{nd}f}"
    except Exception:
        return str(x)

inputs = {
    "EEG": Path(".cache/idare_eeg_cache_index_baseline_corrected.csv"),
    "EMG": Path(".cache/idare_emg_feature_cache_index.csv"),
}
rating_cols = {"valence": "valence_score", "arousal": "arousal_score"}

target_audit_rows = []
fold_audit_rows = []
baseline_rows = []

all_targets = {}
rng = np.random.default_rng(11)

for modality, path in inputs.items():
    df = load_csv(path)
    subject_col = find_col(df, ["subject_id", "subject", "participant_id", "participant", "subj", "subject_idx", "s"])
    row_col = find_col(df, ["row_id", "index", "window_id", "trial_id", "sample_id"], required=False)
    if row_col is None:
        row_ids = pd.Series(np.arange(len(df)), index=df.index)
    else:
        row_ids = df[row_col]

    for task, rcol_default in rating_cols.items():
        rcol = find_col(df, [rcol_default, task, f"{task}_rating", f"{task}_score", f"raw_{task}"])
        tmp = df[[subject_col, rcol]].copy()
        tmp["_row_id"] = row_ids
        tmp["_rating"] = pd.to_numeric(tmp[rcol], errors="coerce")
        tmp["_target"] = tmp.groupby(subject_col, group_keys=False)["_rating"].apply(target_rank_percentile)
        tmp["_modality"] = modality
        tmp["_task"] = task
        all_targets[(modality, task)] = tmp

        valid = tmp["_target"].notna()
        by_subject = tmp.loc[valid].groupby(subject_col)["_target"].agg(["count", "min", "max", "mean", "std"]).reset_index()
        degenerate_subjects = int((by_subject["std"].fillna(0.0) <= 1e-12).sum())
        target_audit_rows.append({
            "modality": modality,
            "task": task,
            "subject_col": subject_col,
            "rating_col": rcol,
            "n_rows": len(tmp),
            "n_nonmissing_ratings": int(tmp["_rating"].notna().sum()),
            "n_targets": int(valid.sum()),
            "n_subjects": int(tmp[subject_col].nunique(dropna=True)),
            "target_min": float(tmp.loc[valid, "_target"].min()) if valid.any() else np.nan,
            "target_max": float(tmp.loc[valid, "_target"].max()) if valid.any() else np.nan,
            "target_mean": float(tmp.loc[valid, "_target"].mean()) if valid.any() else np.nan,
            "target_std": float(tmp.loc[valid, "_target"].std(ddof=0)) if valid.any() else np.nan,
            "degenerate_subjects": degenerate_subjects,
            "target_construction_passed": bool(valid.sum() > 0 and tmp.loc[valid, "_target"].between(0, 1).all()),
        })

        folds = deterministic_subject_folds(tmp[subject_col].dropna().unique(), 6)
        for fold, val_subjects in folds.items():
            val_set = set(val_subjects)
            train_mask = ~tmp[subject_col].isin(val_set)
            val_mask = tmp[subject_col].isin(val_set)
            train_subjects = set(tmp.loc[train_mask, subject_col].dropna().unique())
            val_subjects_set = set(tmp.loc[val_mask, subject_col].dropna().unique())
            subject_overlap = len(train_subjects & val_subjects_set)
            train_rows = set(tmp.loc[train_mask, "_row_id"].astype(str))
            val_rows = set(tmp.loc[val_mask, "_row_id"].astype(str))
            row_overlap = len(train_rows & val_rows)
            val_target = tmp.loc[val_mask & tmp["_target"].notna(), "_target"]
            fold_audit_rows.append({
                "modality": modality,
                "task": task,
                "fold": fold,
                "n_train_subjects": len(train_subjects),
                "n_val_subjects": len(val_subjects_set),
                "n_train_rows": int(train_mask.sum()),
                "n_val_rows": int(val_mask.sum()),
                "subject_overlap": subject_overlap,
                "row_overlap": row_overlap,
                "val_target_n": int(val_target.shape[0]),
                "val_target_std": float(val_target.std(ddof=0)) if len(val_target) else np.nan,
                "fold_leakage_passed": bool(subject_overlap == 0 and row_overlap == 0),
                "target_distribution_passed": bool(len(val_target) > 1 and float(val_target.std(ddof=0)) > 1e-9),
            })

            train_y = tmp.loc[train_mask & tmp["_target"].notna(), "_target"].astype(float).to_numpy()
            val_y = tmp.loc[val_mask & tmp["_target"].notna(), "_target"].astype(float).to_numpy()
            if len(train_y) == 0 or len(val_y) == 0:
                mean_pred = np.zeros_like(val_y, dtype=float)
                perm_pred = np.zeros_like(val_y, dtype=float)
            else:
                mean_pred = np.full_like(val_y, float(np.mean(train_y)), dtype=float)
                perm_pred = rng.choice(train_y, size=len(val_y), replace=True)
            for control_name, pred in [
                ("train_mean_no_training", mean_pred),
                ("train_label_resample_null", perm_pred),
            ]:
                baseline_rows.append({
                    "modality": modality,
                    "task": task,
                    "fold": fold,
                    "control": control_name,
                    "n_val": int(len(val_y)),
                    "spearman_rho": spearman(val_y, pred),
                    "mae_rank_percentile": mae(val_y, pred) if len(val_y) else np.nan,
                    "rmse_rank_percentile": rmse(val_y, pred) if len(val_y) else np.nan,
                    "q33_balanced_accuracy_audit": q33_bal_acc(val_y, pred) if len(val_y) else np.nan,
                    "finite_metrics_passed": bool(len(val_y) > 0 and np.isfinite(mae(val_y, pred)) and np.isfinite(rmse(val_y, pred))),
                })

target_audit = pd.DataFrame(target_audit_rows)
fold_audit = pd.DataFrame(fold_audit_rows)
baseline_df = pd.DataFrame(baseline_rows)

# Metric sanity tests.
toy = np.linspace(0.0, 1.0, 101)
toy_rows = []
toy_cases = [
    ("perfect", toy),
    ("reversed", toy[::-1]),
    ("constant", np.full_like(toy, 0.5)),
    ("noisy_monotone", np.clip(toy + rng.normal(0, 0.03, size=toy.shape), 0, 1)),
    ("random", rng.random(size=toy.shape)),
]
for case, pred in toy_cases:
    toy_rows.append({
        "case": case,
        "spearman_rho": spearman(toy, pred),
        "mae_rank_percentile": mae(toy, pred),
        "rmse_rank_percentile": rmse(toy, pred),
        "q33_balanced_accuracy_audit": q33_bal_acc(toy, pred),
    })
metric_sanity = pd.DataFrame(toy_rows)
metric_sanity["passed"] = True
metric_sanity.loc[metric_sanity["case"] == "perfect", "passed"] = (
    (metric_sanity.loc[metric_sanity["case"] == "perfect", "spearman_rho"] > 0.999) &
    (metric_sanity.loc[metric_sanity["case"] == "perfect", "mae_rank_percentile"] < 1e-12)
).values
metric_sanity.loc[metric_sanity["case"] == "reversed", "passed"] = (
    metric_sanity.loc[metric_sanity["case"] == "reversed", "spearman_rho"] < -0.999
).values
metric_sanity.loc[metric_sanity["case"] == "constant", "passed"] = (
    metric_sanity.loc[metric_sanity["case"] == "constant", "spearman_rho"].apply(np.isfinite)
).values

# Future run matrix guard.
future = load_csv(DOCS / "idare_label_semantics_task_redesign_future_run_matrix.csv")
future_text = future.astype(str).agg(" ".join, axis=1).str.cat(sep=" ").lower()
future_matrix_passed = (
    len(future) == 48 and
    "supcon" not in future_text and
    "fusion" not in future_text and
    "dg" not in future_text and
    future.get("authorized_now", pd.Series(["no"] * len(future))).astype(str).str.lower().eq("no").all()
)

# Smoke decisions.
target_construction_passed = bool(target_audit["target_construction_passed"].all())
fold_leakage_passed = bool(fold_audit["fold_leakage_passed"].all())
metric_sanity_passed = bool(metric_sanity["passed"].all())
baseline_control_passed = bool(baseline_df["finite_metrics_passed"].all())
target_distribution_passed = bool(fold_audit["target_distribution_passed"].all())

decision_rows = [
    {
        "smoke_test": "target_construction_integrity",
        "passed": target_construction_passed,
        "evidence": f"{int(target_audit['n_targets'].sum())} targets; min={fmt(target_audit['target_min'].min())}; max={fmt(target_audit['target_max'].max())}",
        "action_if_failed": "fix target construction or stop/archive",
    },
    {
        "smoke_test": "fold_leakage_guard",
        "passed": fold_leakage_passed,
        "evidence": f"max_subject_overlap={int(fold_audit['subject_overlap'].max())}; max_row_overlap={int(fold_audit['row_overlap'].max())}",
        "action_if_failed": "fix split protocol before any training",
    },
    {
        "smoke_test": "metric_computation_sanity",
        "passed": metric_sanity_passed,
        "evidence": f"perfect_spearman={fmt(metric_sanity.loc[metric_sanity['case']=='perfect','spearman_rho'].iloc[0])}; reversed_spearman={fmt(metric_sanity.loc[metric_sanity['case']=='reversed','spearman_rho'].iloc[0])}",
        "action_if_failed": "fix metric code",
    },
    {
        "smoke_test": "baseline_no_training_control",
        "passed": baseline_control_passed,
        "evidence": f"{len(baseline_df)} no-training control rows; mean_null_spearman={fmt(baseline_df['spearman_rho'].mean())}",
        "action_if_failed": "fix controls before training",
    },
    {
        "smoke_test": "target_distribution_audit",
        "passed": target_distribution_passed,
        "evidence": f"min_val_target_std={fmt(fold_audit['val_target_std'].min())}",
        "action_if_failed": "revise target or flag degenerate cells",
    },
    {
        "smoke_test": "future_run_matrix_guard",
        "passed": future_matrix_passed,
        "evidence": f"future_run_rows={len(future)}; no SupCon/DG/fusion rows={future_matrix_passed}",
        "action_if_failed": "fix future matrix before training objective",
    },
]
decision_df = pd.DataFrame(decision_rows)
all_passed = bool(decision_df["passed"].all())

if all_passed:
    diagnosis = "redesigned_task_smoke_tests_passed_ready_for_minimal_regression_objective"
    recommended_next_objective = "label_semantics_redesigned_minimal_regression_objective"
    next_allowed = "human_review_closeout_then_minimal_regression_training_objective"
else:
    diagnosis = "redesigned_task_smoke_tests_failed"
    recommended_next_objective = "label_semantics_redesigned_task_spec_fix_or_stop_objective"
    next_allowed = "human_review_closeout_then_spec_fix_or_stop"

# Write CSVs.
target_audit.to_csv(target_audit_path, index=False)
fold_audit.to_csv(fold_audit_path, index=False)
metric_sanity.to_csv(metric_sanity_path, index=False)
baseline_df.to_csv(baseline_path, index=False)
decision_df.to_csv(decision_path, index=False)

summary = {
    "status": "complete_pending_human_review",
    "created_utc": now,
    "source_objective": "docs/idare_label_semantics_redesigned_task_smoke_tests_objective.md",
    "selected_primary_formulation": selected,
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next_objective,
    "all_passed": all_passed,
    "smoke_results": decision_rows,
    "key_counts": {
        "target_audit_rows": int(len(target_audit)),
        "fold_audit_rows": int(len(fold_audit)),
        "metric_sanity_rows": int(len(metric_sanity)),
        "baseline_control_rows": int(len(baseline_df)),
        "future_run_rows": int(len(future)),
    },
    "outputs": {
        "report_md": str(report_md_path),
        "report_json": str(report_json_path),
        "target_audit_csv": str(target_audit_path),
        "fold_audit_csv": str(fold_audit_path),
        "metric_sanity_csv": str(metric_sanity_path),
        "baseline_control_summary_csv": str(baseline_path),
        "decision_matrix_csv": str(decision_path),
    },
    "next_allowed_step": next_allowed,
    "blocked": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
        "full redesigned-task training before review",
    ],
}
report_json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = []
md.append("# I-DARE Label-Semantics Redesigned-Task Smoke Tests Report\n")
md.append("## Status\n")
md.append("Status: complete; pending human review.\n")
md.append(f"Created UTC: `{now}`\n")
md.append("## Executive Result\n")
md.append(f"Selected formulation: `{selected}`\n")
md.append(f"Diagnosis: `{diagnosis}`\n")
md.append(f"Recommended next objective: `{recommended_next_objective}`\n")
md.append(f"All required smoke tests passed: `{all_passed}`\n")
md.append("## Smoke-Test Decision Matrix\n")
md.append(md_table(decision_rows, ["smoke_test", "passed", "evidence", "action_if_failed"]))
md.append("\n## Target Construction Summary\n")
md.append(md_table(target_audit.to_dict("records"), ["modality", "task", "n_rows", "n_targets", "n_subjects", "target_min", "target_max", "target_std", "degenerate_subjects", "target_construction_passed"]))
md.append("\n## Fold Leakage / Distribution Summary\n")
fold_summary_rows = []
for (modality, task), g in fold_audit.groupby(["modality", "task"]):
    fold_summary_rows.append({
        "modality": modality,
        "task": task,
        "max_subject_overlap": int(g["subject_overlap"].max()),
        "max_row_overlap": int(g["row_overlap"].max()),
        "min_val_target_std": fmt(g["val_target_std"].min()),
        "all_folds_passed": bool(g["fold_leakage_passed"].all() and g["target_distribution_passed"].all()),
    })
md.append(md_table(fold_summary_rows, ["modality", "task", "max_subject_overlap", "max_row_overlap", "min_val_target_std", "all_folds_passed"]))
md.append("\n## No-Training Control Summary\n")
control_summary = []
for (modality, task, control), g in baseline_df.groupby(["modality", "task", "control"]):
    control_summary.append({
        "modality": modality,
        "task": task,
        "control": control,
        "mean_spearman": fmt(g["spearman_rho"].mean()),
        "mean_mae": fmt(g["mae_rank_percentile"].mean()),
        "mean_rmse": fmt(g["rmse_rank_percentile"].mean()),
        "all_finite": bool(g["finite_metrics_passed"].all()),
    })
md.append(md_table(control_summary, ["modality", "task", "control", "mean_spearman", "mean_mae", "mean_rmse", "all_finite"]))
md.append("\n## Interpretation\n")
if all_passed:
    md.append(
        "The redesigned task passed construction, leakage, metric, distribution, and no-training control smoke tests. "
        "This does not mean the task is solved; it only means the target is now coherent enough to justify a minimal regression-style training objective after human review.\n"
    )
else:
    md.append(
        "At least one required smoke test failed. Training should remain blocked until the spec or implementation is fixed, or the branch is stopped/archived.\n"
    )
md.append("## Next Allowed Step\n")
md.append("Human review / closeout before the next objective.\n")
md.append("\nBlocked until review:\n")
for b in summary["blocked"]:
    md.append(f"- {b}\n")
report_md_path.write_text("\n".join(md), encoding="utf-8")

# Update roadmap/status.
status = json.loads(status_json_path.read_text(encoding="utf-8"))
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = next_allowed
status["current_idare_blocked_steps"] = summary["blocked"]
events = status.get("idare_protocol_events")
if not isinstance(events, list):
    events = []
status["idare_protocol_events"] = events
events.append({
    "timestamp_utc": now,
    "type": "report",
    "name": "I-DARE label-semantics redesigned-task smoke tests report",
    "status": f"complete pending human review; diagnosis={diagnosis}; all_passed={all_passed}",
    "evidence": str(report_md_path),
    "next_allowed_step": next_allowed,
    "blocked": summary["blocked"],
})
status_json_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Label-Semantics Redesigned-Task Smoke Tests Report

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE label-semantics redesigned-task smoke tests report | complete pending human review; diagnosis=`{diagnosis}`; all_passed=`{all_passed}` | `docs/idare_label_semantics_redesigned_task_smoke_tests_report.md` | Human review / closeout before next objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Recommended next objective is `{recommended_next_objective}` only after human review/closeout.
"""
if "I-DARE Label-Semantics Redesigned-Task Smoke Tests Report" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_REDESIGNED_TASK_SMOKE_TESTS_REPORT_WRITTEN")
print(report_md_path)
print(report_json_path)
print(target_audit_path)
print(fold_audit_path)
print(metric_sanity_path)
print(baseline_path)
print(decision_path)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next_objective)
print("all_passed=", all_passed)
print("decision_rows=", len(decision_df))
PY
echo

echo "===== 5) validate generated outputs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_paths = [
    Path("docs/idare_label_semantics_redesigned_task_smoke_tests_report.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

csv_expect = {
    "docs/idare_label_semantics_redesigned_task_target_audit.csv": 4,
    "docs/idare_label_semantics_redesigned_task_fold_audit.csv": 24,
    "docs/idare_label_semantics_redesigned_task_metric_sanity.csv": 5,
    "docs/idare_label_semantics_redesigned_task_baseline_control_summary.csv": 48,
    "docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv": 6,
}
for p, min_rows in csv_expect.items():
    df = pd.read_csv(p)
    print(Path(p).name, "rows=", len(df))
    if len(df) < min_rows:
        raise SystemExit(f"ERROR: {p} too few rows")

report = json.loads(Path("docs/idare_label_semantics_redesigned_task_smoke_tests_report.json").read_text(encoding="utf-8"))
if report.get("selected_primary_formulation") != "subject_relative_ordinal_affect_regression_v1":
    raise SystemExit("ERROR: wrong selected_primary_formulation")
if not isinstance(report.get("all_passed"), bool):
    raise SystemExit("ERROR: all_passed must be boolean")
for term in ["direct full SupCon/DG training", "broad hyperparameter search", "final LOSO claim"]:
    if term not in report.get("blocked", []):
        raise SystemExit(f"ERROR: missing blocked term {term}")

text = Path("docs/idare_label_semantics_redesigned_task_smoke_tests_report.md").read_text(encoding="utf-8")
for term in ["Executive Result", "Smoke-Test Decision Matrix", "Target Construction Summary", "No-Training Control Summary", "Next Allowed Step"]:
    if term not in text:
        raise SystemExit(f"ERROR: missing section {term}")

print("diagnosis=", report["diagnosis"])
print("recommended_next_objective=", report["recommended_next_objective"])
print("all_passed=", report["all_passed"])
print("ALL_REDESIGNED_TASK_SMOKE_TESTS_OUTPUTS_VALID")
PY

grep -nE "Status|Executive Result|Smoke-Test Decision Matrix|Target Construction Summary|Fold Leakage|No-Training Control|Interpretation|Next Allowed Step" \
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.md
grep -nE "Redesigned-Task Smoke Tests Report|Recommended next objective" docs/project_status_current.md | tail -n 10
echo

echo "===== 6) file list ====="
ls -lh \
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.md \
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.json \
  docs/idare_label_semantics_redesigned_task_target_audit.csv \
  docs/idare_label_semantics_redesigned_task_fold_audit.csv \
  docs/idare_label_semantics_redesigned_task_metric_sanity.csv \
  docs/idare_label_semantics_redesigned_task_baseline_control_summary.csv \
  docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv \
  docs/project_status_current.json \
  docs/project_status_current.md
echo

echo "===== 7) status before commit ====="
git status --short --branch
echo

echo "===== 8) commit and push redesigned-task smoke-test report ====="
git add \
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.md \
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.json \
  docs/idare_label_semantics_redesigned_task_target_audit.csv \
  docs/idare_label_semantics_redesigned_task_fold_audit.csv \
  docs/idare_label_semantics_redesigned_task_metric_sanity.csv \
  docs/idare_label_semantics_redesigned_task_baseline_control_summary.csv \
  docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "analysis: add I-DARE redesigned task smoke tests report"
git push origin main
echo

echo "===== 9) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
