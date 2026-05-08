#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start salvage/fix minimal SupCon/DG first-pass report ====="
date
git status --short --branch
echo

echo "===== 1) choose python ====="
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif [ -x ".venv/bin/python3" ]; then
  PY=".venv/bin/python3"
else
  PY="python3"
fi
echo "PY=$PY"
"$PY" - <<'PY'
import sys
print(sys.executable)
import csv
import json
print("OK_IMPORTS")
PY
echo

echo "===== 2) require partial outputs from completed 72 runs ====="
ls -lh \
  docs/idare_minimal_supcon_dg_first_pass_report.json \
  docs/idare_minimal_supcon_dg_first_pass_runs.csv \
  docs/idare_minimal_supcon_dg_first_pass_predictions.csv \
  docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv \
  docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv \
  docs/idare_minimal_supcon_dg_first_pass_training_objective.json \
  docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.md \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 3) rebuild markdown report without tabulate dependency and update roadmap ====="
"$PY" - <<'PY'
import csv
import json
from collections import defaultdict
from pathlib import Path

DOCS = Path("docs")
OUT_REPORT_MD = DOCS / "idare_minimal_supcon_dg_first_pass_report.md"
OUT_REPORT_JSON = DOCS / "idare_minimal_supcon_dg_first_pass_report.json"
OUT_RUNS_CSV = DOCS / "idare_minimal_supcon_dg_first_pass_runs.csv"
OUT_PRED_CSV = DOCS / "idare_minimal_supcon_dg_first_pass_predictions.csv"
OUT_EMBED_CSV = DOCS / "idare_minimal_supcon_dg_first_pass_embedding_summary.csv"
OUT_LOSS_CSV = DOCS / "idare_minimal_supcon_dg_first_pass_loss_summary.csv"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

for p in [OUT_REPORT_JSON, OUT_RUNS_CSV, OUT_PRED_CSV, OUT_EMBED_CSV, OUT_LOSS_CSV, PROJECT_MD, PROJECT_JSON]:
    if not p.exists():
        raise SystemExit(f"ERROR: missing required partial output: {p}")

report_json = json.loads(OUT_REPORT_JSON.read_text(encoding="utf-8"))

with OUT_RUNS_CSV.open(newline="", encoding="utf-8") as f:
    run_rows = list(csv.DictReader(f))
with OUT_PRED_CSV.open(newline="", encoding="utf-8") as f:
    pred_rows = list(csv.DictReader(f))
with OUT_EMBED_CSV.open(newline="", encoding="utf-8") as f:
    embed_rows = list(csv.DictReader(f))
with OUT_LOSS_CSV.open(newline="", encoding="utf-8") as f:
    loss_rows = list(csv.DictReader(f))

if len(run_rows) != int(report_json.get("expanded_run_count", -1)):
    raise SystemExit(f"ERROR: run count mismatch: csv={len(run_rows)} json={report_json.get('expanded_run_count')}")
if len(run_rows) != 72:
    raise SystemExit(f"ERROR: expected 72 completed runs, got {len(run_rows)}")
if len(pred_rows) <= 0 or len(embed_rows) <= 0 or len(loss_rows) <= 0:
    raise SystemExit("ERROR: one or more partial output CSVs are empty")

def fnum(x, default=0.0):
    try:
        return float(x)
    except Exception:
        return default

# Recompute aggregate table from CSV to avoid relying on pandas/tabulate.
groups = defaultdict(list)
for r in run_rows:
    key = (r["method"], r["modality"], r["task"])
    groups[key].append(r)

agg_rows = []
for (method, modality, task), rows in sorted(groups.items()):
    n = len(rows)
    one_class = sum(1 for r in rows if str(r.get("one_class_pred", "")).lower() == "true")
    agg_rows.append({
        "method": method,
        "modality": modality,
        "task": task,
        "n_runs": n,
        "mean_macro_f1": sum(fnum(r["final_macro_f1"]) for r in rows) / n,
        "mean_balanced_accuracy": sum(fnum(r["final_balanced_accuracy"]) for r in rows) / n,
        "mean_accuracy": sum(fnum(r["final_accuracy"]) for r in rows) / n,
        "one_class_pred_count": one_class,
        "mean_positive_pair_coverage": sum(fnum(r.get("positive_pair_coverage_train", 0.0)) for r in rows) / n,
    })

best_row = max(agg_rows, key=lambda r: (r["mean_macro_f1"], r["mean_balanced_accuracy"]))

def method_status(method):
    rows = [r for r in agg_rows if r["method"] == method]
    if not rows:
        return "not_run"
    min_f1 = min(r["mean_macro_f1"] for r in rows)
    mean_f1 = sum(r["mean_macro_f1"] for r in rows) / len(rows)
    collapse = sum(r["one_class_pred_count"] for r in rows)
    if collapse > 0:
        return "invalid_or_collapse"
    if min_f1 >= 0.54 and mean_f1 >= 0.56:
        return "consistent_positive_signal"
    if mean_f1 >= 0.52:
        return "mixed_or_weak_positive_signal"
    return "not_sufficient"

status_by_method = {
    "CE_plus_SupCon": method_status("CE_plus_SupCon"),
    "CE_plus_VREx": method_status("CE_plus_VREx"),
    "CE_plus_SupCon_plus_VREx": method_status("CE_plus_SupCon_plus_VREx"),
}

if "consistent_positive_signal" in status_by_method.values():
    diagnosis = "minimal_supcon_dg_first_pass_consistent_positive_signal"
    recommended_next = "supcon_dg_second_pass_confirmation_objective"
elif "mixed_or_weak_positive_signal" in status_by_method.values():
    diagnosis = "minimal_supcon_dg_first_pass_mixed_weak_signal"
    recommended_next = "supcon_dg_targeted_ablation_objective"
else:
    diagnosis = "minimal_supcon_dg_first_pass_not_sufficient"
    recommended_next = "supcon_dg_failure_analysis_objective"

# Keep JSON consistent with the recovered CSV aggregates.
report_json["aggregate_by_method_modality_task"] = agg_rows
report_json["best_aggregate_row"] = best_row
report_json["status_by_method"] = status_by_method
report_json["diagnosis"] = diagnosis
report_json["recommended_next_objective"] = recommended_next
report_json["expanded_run_count"] = len(run_rows)
report_json["prediction_rows"] = len(pred_rows)
report_json["outputs"] = {
    "runs_csv": str(OUT_RUNS_CSV),
    "predictions_csv": str(OUT_PRED_CSV),
    "embedding_summary_csv": str(OUT_EMBED_CSV),
    "loss_summary_csv": str(OUT_LOSS_CSV),
    "report_md": str(OUT_REPORT_MD),
    "report_json": str(OUT_REPORT_JSON),
}
OUT_REPORT_JSON.write_text(json.dumps(report_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

def markdown_table(rows, columns):
    if not rows:
        return "_No rows._"
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for r in rows:
        vals = []
        for c in columns:
            v = r.get(c, "")
            if isinstance(v, float):
                vals.append(f"{v:.4f}")
            else:
                vals.append(str(v))
        body.append("| " + " | ".join(vals) + " |")
    return "\n".join([header, sep] + body)

agg_columns = [
    "method",
    "modality",
    "task",
    "n_runs",
    "mean_macro_f1",
    "mean_balanced_accuracy",
    "mean_accuracy",
    "one_class_pred_count",
    "mean_positive_pair_coverage",
]

report_md = f"""# I-DARE Minimal SupCon/DG First-pass Training Report

## Status

Minimal first-pass SupCon/DG diagnostic training complete, pending human review.

Generated UTC: `{report_json.get('created_or_updated_utc', 'unknown')}`

## Run Matrix

- Design first-pass rows executed: `{report_json.get('design_first_pass_rows', 12)}`
- Expanded subject-heldout runs completed: `{len(run_rows)}`
- Prediction rows: `{len(pred_rows)}`
- Loss trace rows: `{len(loss_rows)}`
- Embedding diagnostic rows: `{len(embed_rows)}`
- Epochs: `{report_json.get('epochs', 'unknown')}`
- Device: `{report_json.get('device', 'unknown')}`

## Aggregate Results

{markdown_table(agg_rows, agg_columns)}

## Best Aggregate Cell

- method: `{best_row.get('method')}`
- modality: `{best_row.get('modality')}`
- task: `{best_row.get('task')}`
- mean macro-F1: `{best_row.get('mean_macro_f1'):.4f}`
- mean balanced accuracy: `{best_row.get('mean_balanced_accuracy'):.4f}`

## Method-level Interpretation

```json
{json.dumps(status_by_method, indent=2, sort_keys=True)}
```

## Diagnosis

`{diagnosis}`

## Recommended Next Objective

`{recommended_next}`

## Required Caution

This report does not authorize final claims, fusion, broad hyperparameter search, direct full SupCon/DG training, or mainline replacement.

The result must be reviewed before any second-pass confirmation, targeted ablation, or failure-analysis objective.

## Outputs

- `{OUT_RUNS_CSV}`
- `{OUT_PRED_CSV}`
- `{OUT_EMBED_CSV}`
- `{OUT_LOSS_CSV}`
- `{OUT_REPORT_JSON}`

## Next Allowed Step

Human review / closeout before the recommended next objective.
"""
OUT_REPORT_MD.write_text(report_md, encoding="utf-8")

project_md = PROJECT_MD.read_text(encoding="utf-8")
report_row = "| I-DARE minimal SupCon/DG first-pass training report | minimal first-pass SupCon/DG diagnostic training complete; pending human review | yes | `docs/idare_minimal_supcon_dg_first_pass_report.md` | Human review / closeout before second-pass confirmation, targeted ablation, or failure analysis. | EEG+EMG fusion; final LOSO claim; direct full SupCon/DG training; broad hyperparameter search; mainline change. |"
if report_row not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE minimal SupCon/DG first-pass training objective |"):
            out.append(report_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not find minimal SupCon/DG objective row in project_status_current.md")
    project_md = "\n".join(out) + "\n"

bullet = f"- Minimal SupCon/DG first-pass diagnostic training is complete in `docs/idare_minimal_supcon_dg_first_pass_report.md`; diagnosis is `{diagnosis}`, and full SupCon/DG training remains blocked pending review."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: marker not found in project_status_current.md")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_minimal_supcon_dg_first_pass_training_report"] = {
    "status": "first_pass_training_complete_pending_human_review",
    "evidence": str(OUT_REPORT_MD),
    "evidence_json": str(OUT_REPORT_JSON),
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next,
    "expanded_run_count": len(run_rows),
    "prediction_rows": len(pred_rows),
    "full_training_authorized": False,
    "broad_hyperparameter_search_authorized": False,
    "fusion_authorized": False,
    "mainline_change_authorized": False,
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_REBUILT_REPORT_AND_ROADMAP")
print("runs=", len(run_rows))
print("predictions=", len(pred_rows))
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next)
print("best=", best_row)
PY
echo

echo "===== 4) validate fixed outputs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path

for p in [
    Path("docs/idare_minimal_supcon_dg_first_pass_report.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

for p, expected_min in [
    (Path("docs/idare_minimal_supcon_dg_first_pass_runs.csv"), 72),
    (Path("docs/idare_minimal_supcon_dg_first_pass_predictions.csv"), 1),
    (Path("docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv"), 72),
    (Path("docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv"), 72),
]:
    with p.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(p.name, "rows=", len(rows))
    if len(rows) < expected_min:
        raise SystemExit(f"ERROR: too few rows in {p}")

report = json.loads(Path("docs/idare_minimal_supcon_dg_first_pass_report.json").read_text(encoding="utf-8"))
if report["expanded_run_count"] != 72:
    raise SystemExit(f"ERROR: expected expanded_run_count=72, got {report['expanded_run_count']}")
if not report.get("diagnosis"):
    raise SystemExit("ERROR: missing diagnosis")
if not report.get("recommended_next_objective"):
    raise SystemExit("ERROR: missing recommended_next_objective")
md = Path("docs/idare_minimal_supcon_dg_first_pass_report.md").read_text(encoding="utf-8")
for term in ["## Status", "## Aggregate Results", "## Diagnosis", "direct full SupCon/DG training", "## Next Allowed Step"]:
    if term not in md:
        raise SystemExit(f"ERROR: missing term in markdown report: {term}")
print("diagnosis=", report["diagnosis"])
print("recommended_next_objective=", report["recommended_next_objective"])
print("ALL_MINIMAL_SUPCON_DG_FIRST_PASS_FIXED_OUTPUTS_VALID")
PY

grep -n "## Status\|## Run Matrix\|## Aggregate Results\|## Diagnosis\|## Recommended Next Objective\|## Next Allowed Step" docs/idare_minimal_supcon_dg_first_pass_report.md
grep -n "minimal SupCon/DG first-pass training report\|Minimal SupCon/DG first-pass diagnostic training" docs/project_status_current.md
echo

echo "===== 5) file list ====="
ls -lh \
  docs/idare_minimal_supcon_dg_first_pass_report.md \
  docs/idare_minimal_supcon_dg_first_pass_report.json \
  docs/idare_minimal_supcon_dg_first_pass_runs.csv \
  docs/idare_minimal_supcon_dg_first_pass_predictions.csv \
  docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv \
  docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push salvaged first-pass outputs ====="
git add \
  docs/idare_minimal_supcon_dg_first_pass_report.md \
  docs/idare_minimal_supcon_dg_first_pass_report.json \
  docs/idare_minimal_supcon_dg_first_pass_runs.csv \
  docs/idare_minimal_supcon_dg_first_pass_predictions.csv \
  docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv \
  docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "exp: run I-DARE minimal SupCon DG first pass"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_minimal_supcon_dg_first_pass_report_fix.log"
