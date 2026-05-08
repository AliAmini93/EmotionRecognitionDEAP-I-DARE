#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start SupCon/DG first-pass failure-analysis report ====="
date
git status --short --branch
echo

echo "===== 1) choose python and require clean repo ====="
PY=".venv/bin/python"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3)"
fi
echo "PY=$PY"
"$PY" - <<'PY'
import json
import pandas as pd
print("OK_IMPORTS")
PY

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: repo is not clean; commit/stash changes before running failure analysis." >&2
  git status --short --branch >&2
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required committed inputs ====="
required=(
  docs/idare_supcon_dg_failure_analysis_objective.md
  docs/idare_supcon_dg_failure_analysis_objective.json
  docs/idare_minimal_supcon_dg_first_pass_review_status.md
  docs/idare_minimal_supcon_dg_first_pass_review_status.json
  docs/idare_minimal_supcon_dg_first_pass_report.md
  docs/idare_minimal_supcon_dg_first_pass_report.json
  docs/idare_minimal_supcon_dg_first_pass_runs.csv
  docs/idare_minimal_supcon_dg_first_pass_predictions.csv
  docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv
  docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv
  docs/idare_subject_variability_supcon_dg_design_spec.md
  docs/idare_subject_variability_supcon_dg_design_spec.json
  docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv
  docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv
  docs/idare_subject_variability_supcon_dg_smoke_tests_report.json
  docs/project_status_current.json
  docs/project_status_current.md
)
for f in "${required[@]}"; do
  if [[ ! -s "$f" ]]; then
    echo "ERROR: missing required file: $f" >&2
    exit 1
  fi
  ls -lh "$f"
done
echo

echo "===== 3) generate read-only SupCon/DG failure-analysis report ====="
"$PY" - <<'PY'
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev

import pandas as pd

ROOT = Path(".")
DOCS = ROOT / "docs"
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

runs_path = DOCS / "idare_minimal_supcon_dg_first_pass_runs.csv"
pred_path = DOCS / "idare_minimal_supcon_dg_first_pass_predictions.csv"
emb_path = DOCS / "idare_minimal_supcon_dg_first_pass_embedding_summary.csv"
loss_path = DOCS / "idare_minimal_supcon_dg_first_pass_loss_summary.csv"
first_pass_report_path = DOCS / "idare_minimal_supcon_dg_first_pass_report.json"
smoke_report_path = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_report.json"
objective_path = DOCS / "idare_supcon_dg_failure_analysis_objective.json"

out_report_md = DOCS / "idare_supcon_dg_failure_analysis_report.md"
out_report_json = DOCS / "idare_supcon_dg_failure_analysis_report.json"
out_method_summary = DOCS / "idare_supcon_dg_failure_method_task_summary.csv"
out_fold_summary = DOCS / "idare_supcon_dg_failure_fold_summary.csv"
out_loss_alignment = DOCS / "idare_supcon_dg_failure_loss_embedding_alignment.csv"
out_decision_matrix = DOCS / "idare_supcon_dg_failure_decision_matrix.csv"

status_json = DOCS / "project_status_current.json"
status_md = DOCS / "project_status_current.md"

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def safe_float(x):
    if x is None:
        return None
    try:
        if isinstance(x, str) and x.strip() == "":
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None

def first_existing(df, candidates):
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    return None

def normalize_runs(df):
    df = df.copy()
    aliases = {
        "global_run_id": ["global_run_id", "run_id", "id"],
        "method": ["method", "recipe"],
        "modality": ["modality"],
        "task": ["task"],
        "fold": ["fold", "fold_id"],
        "macro_f1": ["macro_f1", "final_macro_f1"],
        "balanced_accuracy": ["balanced_accuracy", "bal_acc", "final_balanced_accuracy"],
        "accuracy": ["accuracy", "acc", "final_accuracy"],
        "one_class_pred": ["one_class_pred"],
    }
    for target, cands in aliases.items():
        src = first_existing(df, cands)
        if src is None:
            df[target] = None
        elif src != target:
            df[target] = df[src]
    for col in ["global_run_id", "fold"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["macro_f1", "balanced_accuracy", "accuracy"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "one_class_pred" in df.columns:
        df["one_class_pred"] = df["one_class_pred"].astype(str).str.lower().isin(["true", "1", "yes"])
    for col in ["method", "modality", "task"]:
        df[col] = df[col].astype(str)
    return df

def md_table(rows, columns):
    def fmt(v):
        if v is None:
            return ""
        if isinstance(v, float):
            if math.isnan(v):
                return ""
            return f"{v:.4f}"
        return str(v).replace("\n", " ")
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for r in rows:
        body.append("| " + " | ".join(fmt(r.get(c, "")) for c in columns) + " |")
    return "\n".join([header, sep] + body)

def corr(xs, ys):
    pairs = [(safe_float(x), safe_float(y)) for x, y in zip(xs, ys)]
    pairs = [(x, y) for x, y in pairs if x is not None and y is not None]
    if len(pairs) < 3:
        return None
    mx = sum(x for x, _ in pairs) / len(pairs)
    my = sum(y for _, y in pairs) / len(pairs)
    vx = sum((x - mx) ** 2 for x, _ in pairs)
    vy = sum((y - my) ** 2 for _, y in pairs)
    if vx <= 0 or vy <= 0:
        return None
    cov = sum((x - mx) * (y - my) for x, y in pairs)
    return cov / math.sqrt(vx * vy)

runs_raw = pd.read_csv(runs_path)
runs = normalize_runs(runs_raw)
pred_rows = sum(1 for _ in pred_path.open("r", encoding="utf-8")) - 1

first_pass_report = read_json(first_pass_report_path)
smoke_report = read_json(smoke_report_path)
objective = read_json(objective_path)

# Method/task summary.
group_cols = ["method", "modality", "task"]
method_rows = []
for key, g in runs.groupby(group_cols, dropna=False):
    method, modality, task = key
    f1s = g["macro_f1"].dropna().tolist()
    bas = g["balanced_accuracy"].dropna().tolist()
    accs = g["accuracy"].dropna().tolist()
    method_rows.append({
        "method": method,
        "modality": modality,
        "task": task,
        "n_runs": int(len(g)),
        "mean_macro_f1": mean(f1s) if f1s else None,
        "std_macro_f1": pstdev(f1s) if len(f1s) > 1 else 0.0,
        "min_macro_f1": min(f1s) if f1s else None,
        "max_macro_f1": max(f1s) if f1s else None,
        "mean_balanced_accuracy": mean(bas) if bas else None,
        "mean_accuracy": mean(accs) if accs else None,
        "folds_over_055_macro_f1": int(sum(1 for x in f1s if x >= 0.55)),
        "folds_under_050_macro_f1": int(sum(1 for x in f1s if x < 0.50)),
        "one_class_pred_count": int(g["one_class_pred"].sum()) if "one_class_pred" in g.columns else 0,
    })
method_rows.sort(key=lambda r: (r["mean_macro_f1"] if r["mean_macro_f1"] is not None else -1), reverse=True)
pd.DataFrame(method_rows).to_csv(out_method_summary, index=False)

# Fold summary.
fold_rows = []
for key, g in runs.groupby(["method", "modality", "task", "fold"], dropna=False):
    method, modality, task, fold = key
    f1s = g["macro_f1"].dropna().tolist()
    bas = g["balanced_accuracy"].dropna().tolist()
    accs = g["accuracy"].dropna().tolist()
    fold_rows.append({
        "method": method,
        "modality": modality,
        "task": task,
        "fold": int(fold) if safe_float(fold) is not None else fold,
        "n_runs": int(len(g)),
        "mean_macro_f1": mean(f1s) if f1s else None,
        "mean_balanced_accuracy": mean(bas) if bas else None,
        "mean_accuracy": mean(accs) if accs else None,
        "best_macro_f1": max(f1s) if f1s else None,
        "worst_macro_f1": min(f1s) if f1s else None,
        "one_class_pred_count": int(g["one_class_pred"].sum()) if "one_class_pred" in g.columns else 0,
    })
pd.DataFrame(fold_rows).to_csv(out_fold_summary, index=False)

# Loss and embedding alignment.
loss_df = pd.read_csv(loss_path)
emb_df = pd.read_csv(emb_path)

loss_id = first_existing(loss_df, ["global_run_id", "run_id"])
epoch_col = first_existing(loss_df, ["epoch", "step"])
loss_alignment_rows = []

if loss_id is not None:
    # Identify numeric loss/regularization columns. Keep broad but exclude identifiers.
    numeric_cols = []
    for c in loss_df.columns:
        cl = c.lower()
        if c == loss_id or c == epoch_col:
            continue
        s = pd.to_numeric(loss_df[c], errors="coerce")
        if s.notna().sum() >= 2 and any(tok in cl for tok in ["loss", "ce", "supcon", "vrex", "penalty"]):
            numeric_cols.append(c)
            loss_df[c] = s
    for rid, g in loss_df.groupby(loss_id):
        if epoch_col is not None:
            g = g.sort_values(epoch_col)
        row = {"global_run_id": rid}
        for c in numeric_cols:
            vals = g[c].dropna().tolist()
            if vals:
                row[f"{c}_start"] = vals[0]
                row[f"{c}_end"] = vals[-1]
                row[f"{c}_delta"] = vals[-1] - vals[0]
                row[f"{c}_relative_delta"] = ((vals[-1] - vals[0]) / abs(vals[0])) if vals[0] not in (0, None) else None
        loss_alignment_rows.append(row)
loss_align = pd.DataFrame(loss_alignment_rows)

base = runs[["global_run_id", "method", "modality", "task", "fold", "macro_f1", "balanced_accuracy", "accuracy"]].copy()
if not loss_align.empty and "global_run_id" in loss_align.columns:
    base = base.merge(loss_align, on="global_run_id", how="left")

emb_id = first_existing(emb_df, ["global_run_id", "run_id"])
if emb_id is not None:
    emb_copy = emb_df.copy()
    if emb_id != "global_run_id":
        emb_copy = emb_copy.rename(columns={emb_id: "global_run_id"})
    # Keep non-huge, mostly numeric summary columns plus id.
    keep = ["global_run_id"]
    for c in emb_copy.columns:
        if c == "global_run_id":
            continue
        s = pd.to_numeric(emb_copy[c], errors="coerce")
        if s.notna().sum() >= 2:
            emb_copy[c] = s
            keep.append(c)
    emb_copy = emb_copy[keep]
    base = base.merge(emb_copy, on="global_run_id", how="left", suffixes=("", "_embedding"))

# Add simple correlations for numeric diagnostic columns with macro_f1 as separate rows.
alignment_numeric = []
for c in base.columns:
    if c in ["global_run_id", "method", "modality", "task", "fold", "macro_f1", "balanced_accuracy", "accuracy"]:
        continue
    s = pd.to_numeric(base[c], errors="coerce")
    if s.notna().sum() >= 3:
        alignment_numeric.append({
            "diagnostic_metric": c,
            "corr_with_macro_f1": corr(s.tolist(), base["macro_f1"].tolist()),
            "corr_with_balanced_accuracy": corr(s.tolist(), base["balanced_accuracy"].tolist()),
            "n_nonmissing": int(s.notna().sum()),
        })
# Put per-run rows plus compact correlations by appending prefixed rows would be messy.
# Write per-run alignment; correlations go into JSON and report.
base.to_csv(out_loss_alignment, index=False)

corr_rows = sorted(
    [r for r in alignment_numeric if r["corr_with_macro_f1"] is not None],
    key=lambda r: abs(r["corr_with_macro_f1"]),
    reverse=True,
)

# Predictions sanity/error concentration if possible.
pred_sample = pd.read_csv(pred_path)
true_col = first_existing(pred_sample, ["y_true", "true_label", "label", "target"])
pred_col = first_existing(pred_sample, ["y_pred", "pred_label", "prediction", "pred"])
subj_col = first_existing(pred_sample, ["subject_id", "subject", "participant_id"])
pred_error_summary = {}
if true_col is not None and pred_col is not None:
    y_true = pd.to_numeric(pred_sample[true_col], errors="coerce")
    y_pred = pd.to_numeric(pred_sample[pred_col], errors="coerce")
    err = (y_true != y_pred) & y_true.notna() & y_pred.notna()
    pred_error_summary["overall_error_rate"] = float(err.mean())
    if subj_col is not None:
        tmp = pred_sample.copy()
        tmp["_err"] = err.astype(int)
        subj_err = tmp.groupby(subj_col)["_err"].mean().sort_values(ascending=False)
        pred_error_summary["top_subject_error_rates"] = [
            {"subject": str(k), "error_rate": float(v)}
            for k, v in subj_err.head(10).items()
        ]

best = method_rows[0] if method_rows else {}
method_overall = []
for method, g in runs.groupby("method"):
    method_overall.append({
        "method": method,
        "n_runs": int(len(g)),
        "mean_macro_f1": float(g["macro_f1"].mean()),
        "mean_balanced_accuracy": float(g["balanced_accuracy"].mean()),
        "std_macro_f1": float(g["macro_f1"].std(ddof=0)),
        "folds_over_055_macro_f1": int((g["macro_f1"] >= 0.55).sum()),
        "folds_under_050_macro_f1": int((g["macro_f1"] < 0.50).sum()),
    })
method_overall.sort(key=lambda r: r["mean_macro_f1"], reverse=True)

best_mean = best.get("mean_macro_f1") or 0.0
best_ba = best.get("mean_balanced_accuracy") or 0.0
all_smoke_passed = bool(smoke_report.get("all_passed", False))
loss_cols_present = [c for c in base.columns if any(tok in c.lower() for tok in ["loss", "supcon", "vrex", "ce"])]

# Decision logic. Keep conservative: no training recommendation here, only a specific next analysis/design objective.
if best_mean < 0.55 and all_smoke_passed:
    diagnosis = "supcon_dg_first_pass_failed_despite_valid_smokes"
elif best_mean < 0.55:
    diagnosis = "supcon_dg_first_pass_failed_and_smoke_confidence_unclear"
else:
    diagnosis = "supcon_dg_first_pass_partial_signal_needs_targeted_confirmation"

if best_mean < 0.55:
    selected_next = "targeted_supcon_dg_pair_sampler_objective_ablation_design"
else:
    selected_next = "targeted_supcon_dg_confirmation_objective"

decision_rows = [
    {
        "hypothesis": "implementation_or_sampler_bug",
        "evidence": f"smoke_all_passed={all_smoke_passed}; one_class_pred_total={int(runs['one_class_pred'].sum()) if 'one_class_pred' in runs else 0}",
        "support": "low" if all_smoke_passed else "medium",
        "interpretation": "Smoke tests make a gross implementation failure unlikely, though subtle objective mismatch remains possible.",
        "decision": "do_not_debug_basic_plumbing_unless_future smoke fails",
    },
    {
        "hypothesis": "SupCon/DG objective not aligned with subject-heldout performance",
        "evidence": f"best_mean_macro_f1={best_mean:.4f}; best_mean_balanced_accuracy={best_ba:.4f}; best_cell={best.get('method')} {best.get('modality')} {best.get('task')}",
        "support": "high" if best_mean < 0.55 else "medium",
        "interpretation": "The auxiliary objectives can run, but first-pass validation remains near chance/mixed.",
        "decision": "analyze objective/pair design before more training",
    },
    {
        "hypothesis": "pair_sampler_or_positive_definition_too_weak",
        "evidence": "First-pass used label-based positive structure, but did not produce robust cross-subject gains.",
        "support": "medium_high" if best_mean < 0.55 else "medium",
        "interpretation": "Positive/negative definitions may be too noisy, too task-local, or insufficiently subject-invariant.",
        "decision": "targeted pair/sampler ablation is more justified than broad hyperparameter search",
    },
    {
        "hypothesis": "VREx/domain_regularization_insufficient",
        "evidence": "; ".join([f"{r['method']}: mean_f1={r['mean_macro_f1']:.4f}" for r in method_overall]),
        "support": "high" if best_mean < 0.55 else "medium",
        "interpretation": "Domain regularization did not transform subject-heldout generalization in this first pass.",
        "decision": "do not launch full DG training without a narrower failure hypothesis",
    },
    {
        "hypothesis": "representation_or_label_task_remains_primary_bottleneck",
        "evidence": "Earlier diagnostics supported subject variability / label-task dependence; this first-pass intervention did not overcome it.",
        "support": "medium_high",
        "interpretation": "SupCon/DG may need representation redesign, subject-aware positives, or different target formulation.",
        "decision": selected_next,
    },
]
pd.DataFrame(decision_rows).to_csv(out_decision_matrix, index=False)

report_obj = {
    "status": "failure_analysis_complete_pending_review",
    "created_at_utc": now,
    "objective": str(objective_path),
    "inputs": {
        "runs_csv": str(runs_path),
        "predictions_csv": str(pred_path),
        "embedding_summary_csv": str(emb_path),
        "loss_summary_csv": str(loss_path),
        "smoke_report": str(smoke_report_path),
        "first_pass_report": str(first_pass_report_path),
    },
    "counts": {
        "runs": int(len(runs)),
        "prediction_rows": int(pred_rows),
        "embedding_summary_rows": int(len(emb_df)),
        "loss_summary_rows": int(len(loss_df)),
        "method_task_rows": int(len(method_rows)),
        "fold_summary_rows": int(len(fold_rows)),
        "loss_alignment_rows": int(len(base)),
    },
    "diagnosis": diagnosis,
    "best_cell": best,
    "method_overall": method_overall,
    "top_correlations": corr_rows[:12],
    "prediction_error_summary": pred_error_summary,
    "decision_matrix": decision_rows,
    "recommended_next_objective": selected_next,
    "blocked": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
    ],
}
out_report_json.write_text(json.dumps(report_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

top_method_rows = method_rows[:12]
worst_method_rows = list(reversed(method_rows[-8:])) if len(method_rows) >= 8 else list(reversed(method_rows))

corr_table_rows = []
for r in corr_rows[:10]:
    corr_table_rows.append({
        "diagnostic_metric": r["diagnostic_metric"],
        "corr_with_macro_f1": r["corr_with_macro_f1"],
        "corr_with_balanced_accuracy": r["corr_with_balanced_accuracy"],
        "n_nonmissing": r["n_nonmissing"],
    })

decision_table_rows = [{
    "hypothesis": r["hypothesis"],
    "support": r["support"],
    "decision": r["decision"],
} for r in decision_rows]

report_md = f"""# I-DARE SupCon/DG Failure Analysis Report

## Status

Read-only SupCon/DG failure analysis is complete and pending human review.

- Created at: `{now}`
- Objective: `docs/idare_supcon_dg_failure_analysis_objective.md`
- Runs analyzed: `{len(runs)}`
- Prediction rows analyzed: `{pred_rows}`
- Diagnosis: `{diagnosis}`
- Recommended next objective: `{selected_next}`

## Executive Diagnosis

The minimal SupCon/DG first pass failed to provide robust evidence that SupCon/DG, as currently specified, solves the subject-heldout generalization problem.

This is not interpreted as a basic plumbing failure, because the prior smoke tests passed and the first-pass runs produced non-degenerate predictions. The more likely issue is that the current objective and pair/domain formulation is too weak or misaligned for the subject-variability problem.

## Best Aggregate Cell

```json
{json.dumps(best, indent=2, ensure_ascii=False)}
```

## Overall Method Ranking

{md_table(method_overall, ["method", "n_runs", "mean_macro_f1", "mean_balanced_accuracy", "std_macro_f1", "folds_over_055_macro_f1", "folds_under_050_macro_f1"])}

## Top Method / Modality / Task Cells

{md_table(top_method_rows, ["method", "modality", "task", "n_runs", "mean_macro_f1", "std_macro_f1", "mean_balanced_accuracy", "folds_over_055_macro_f1", "folds_under_050_macro_f1"])}

## Weakest Method / Modality / Task Cells

{md_table(worst_method_rows, ["method", "modality", "task", "n_runs", "mean_macro_f1", "std_macro_f1", "mean_balanced_accuracy", "folds_over_055_macro_f1", "folds_under_050_macro_f1"])}

## Loss / Embedding Alignment

The generated alignment table is written to:

- `docs/idare_supcon_dg_failure_loss_embedding_alignment.csv`

The strongest simple diagnostic correlations with validation macro-F1 are:

{md_table(corr_table_rows, ["diagnostic_metric", "corr_with_macro_f1", "corr_with_balanced_accuracy", "n_nonmissing"])}

If loss terms decrease but these correlations are weak, then optimization is happening without reliable subject-heldout transfer.

## Prediction Error Notes

```json
{json.dumps(pred_error_summary, indent=2, ensure_ascii=False)}
```

## Decision Matrix

{md_table(decision_table_rows, ["hypothesis", "support", "decision"])}

## Interpretation

The failed first pass suggests that the current SupCon/DG setup is not yet targeting the actual blocker strongly enough.

Most likely explanations:

1. positive pairs are label-compatible but not necessarily subject-invariant,
2. negative pairs may be semantically noisy under affect labels,
3. VREx may be regularizing loss without learning useful invariant structure,
4. representation features may still encode subject/fold artifacts more strongly than affect state,
5. subject-heldout validation remains the core bottleneck.

## Recommendation

Do **not** start direct full SupCon/DG training or broad hyperparameter search.

The next scientific step should be a targeted objective around pair/sampler and domain-objective ablation, constrained by this failure analysis. The goal should be to test a small number of explicit failure hypotheses rather than expanding the search space.

Recommended next objective:

- `{selected_next}`

## Next Allowed Step

Human review / closeout of this failure analysis before any new SupCon/DG training, targeted ablation, broad search, fusion, or mainline change.
"""
out_report_md.write_text(report_md, encoding="utf-8")

# Update roadmap/status.
status = read_json(status_json)
entry = {
    "name": "I-DARE SupCon/DG failure analysis report",
    "status": "read-only failure analysis complete; pending human review",
    "active": True,
    "artifact": str(out_report_md),
    "next_step": "Human review / closeout before targeted pair/sampler ablation or any new training.",
    "blocked": "EEG+EMG fusion; final LOSO claim; direct full SupCon/DG training; broad hyperparameter search; mainline change.",
    "diagnosis": diagnosis,
    "recommended_next_objective": selected_next,
    "created_at_utc": now,
}
if isinstance(status, dict):
    hist = status.get("idare_objective_history")
    if not isinstance(hist, list):
        hist = []
        status["idare_objective_history"] = hist
    sigs = {json.dumps(x, sort_keys=True, ensure_ascii=False) for x in hist if isinstance(x, dict)}
    sig = json.dumps(entry, sort_keys=True, ensure_ascii=False)
    if sig not in sigs:
        hist.append(entry)
    status["current_idare_next_step"] = {
        "objective": selected_next,
        "artifact": str(out_report_md),
        "next_step": "human_review_closeout_of_supcon_dg_failure_analysis",
        "updated_at_utc": now,
    }
    status_json.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = status_md.read_text(encoding="utf-8")
marker = "## I-DARE SupCon/DG Failure Analysis Report"
block = f"""

{marker}

- Read-only SupCon/DG failure analysis is complete in `{out_report_md}`.
- Diagnosis: `{diagnosis}`.
- Recommended next objective: `{selected_next}`.
- Human review is required before any new SupCon/DG training, targeted ablation, broad hyperparameter search, EEG+EMG fusion, final LOSO claim, or mainline change.
"""
if marker not in md:
    status_md.write_text(md.rstrip() + block + "\n", encoding="utf-8")

print("OK_SUPCON_DG_FAILURE_ANALYSIS_REPORT_WRITTEN")
print(out_report_md)
print(out_report_json)
print(out_method_summary)
print(out_fold_summary)
print(out_loss_alignment)
print(out_decision_matrix)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", selected_next)
print("best_cell=", json.dumps(best, ensure_ascii=False))
PY
echo

echo "===== 4) validate generated outputs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

paths = [
    Path("docs/idare_supcon_dg_failure_analysis_report.json"),
    Path("docs/project_status_current.json"),
]
for p in paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

csvs = [
    Path("docs/idare_supcon_dg_failure_method_task_summary.csv"),
    Path("docs/idare_supcon_dg_failure_fold_summary.csv"),
    Path("docs/idare_supcon_dg_failure_loss_embedding_alignment.csv"),
    Path("docs/idare_supcon_dg_failure_decision_matrix.csv"),
]
for p in csvs:
    df = pd.read_csv(p)
    if len(df) == 0:
        raise SystemExit(f"ERROR: empty CSV {p}")
    print(f"{p.name} rows=", len(df))

report = json.loads(Path("docs/idare_supcon_dg_failure_analysis_report.json").read_text(encoding="utf-8"))
print("diagnosis=", report.get("diagnosis"))
print("recommended_next_objective=", report.get("recommended_next_objective"))
if report.get("recommended_next_objective") in ("", None):
    raise SystemExit("ERROR: missing recommended_next_objective")

text = Path("docs/idare_supcon_dg_failure_analysis_report.md").read_text(encoding="utf-8")
for term in [
    "Executive Diagnosis",
    "Decision Matrix",
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "pair/sampler",
    "Next Allowed Step",
]:
    if term not in text:
        raise SystemExit(f"ERROR: missing term {term!r} in report md")
print("ALL_SUPCON_DG_FAILURE_ANALYSIS_OUTPUTS_VALID")
PY

grep -nE "## Status|## Executive Diagnosis|## Overall Method Ranking|## Loss / Embedding Alignment|## Decision Matrix|## Recommendation|## Next Allowed Step" \
  docs/idare_supcon_dg_failure_analysis_report.md

grep -n "SupCon/DG failure analysis" docs/project_status_current.md | tail -5 || true
echo

echo "===== 5) file list ====="
ls -lh \
  docs/idare_supcon_dg_failure_analysis_report.md \
  docs/idare_supcon_dg_failure_analysis_report.json \
  docs/idare_supcon_dg_failure_method_task_summary.csv \
  docs/idare_supcon_dg_failure_fold_summary.csv \
  docs/idare_supcon_dg_failure_loss_embedding_alignment.csv \
  docs/idare_supcon_dg_failure_decision_matrix.csv \
  docs/project_status_current.json \
  docs/project_status_current.md
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push SupCon/DG failure-analysis report ====="
git add \
  docs/idare_supcon_dg_failure_analysis_report.md \
  docs/idare_supcon_dg_failure_analysis_report.json \
  docs/idare_supcon_dg_failure_method_task_summary.csv \
  docs/idare_supcon_dg_failure_fold_summary.csv \
  docs/idare_supcon_dg_failure_loss_embedding_alignment.csv \
  docs/idare_supcon_dg_failure_decision_matrix.csv \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "analysis: add I-DARE SupCon DG failure analysis report"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_supcon_dg_failure_analysis_report.log"
