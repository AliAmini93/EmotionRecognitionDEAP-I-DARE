#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start salvage/fix preprocessed minimal training report ====="
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
import json
import pandas
print("OK_IMPORTS")
PY
echo

echo "===== 2) require expected partial outputs from completed 24 runs ====="
ls -lh \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.md \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.md \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv \
  docs/idare_minimal_subject_relative_preprocessed_training_objective.md \
  docs/idare_minimal_subject_relative_preprocessed_training_objective.json \
  docs/idare_subject_relative_representation_preprocessing_review_status.md \
  docs/idare_subject_relative_representation_preprocessing_report.md
echo

echo "===== 3) build combined report with robust metric parser ====="
"$PY" - <<'PY'
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

OBJECTIVE_MD = DOCS / "idare_minimal_subject_relative_preprocessed_training_objective.md"
OBJECTIVE_JSON = DOCS / "idare_minimal_subject_relative_preprocessed_training_objective.json"
REVIEW_MD = DOCS / "idare_subject_relative_representation_preprocessing_review_status.md"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

EEG_JSON = DOCS / "idare_subject_relative_preprocessed_minimal_eeg_primary.json"
EEG_MD = DOCS / "idare_subject_relative_preprocessed_minimal_eeg_primary.md"
EEG_PRED = DOCS / "idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv"
EMG_JSON = DOCS / "idare_subject_relative_preprocessed_minimal_emg_primary.json"
EMG_MD = DOCS / "idare_subject_relative_preprocessed_minimal_emg_primary.md"
EMG_PRED = DOCS / "idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv"

REPORT_MD = DOCS / "idare_subject_relative_preprocessed_minimal_training_report.md"
REPORT_JSON = DOCS / "idare_subject_relative_preprocessed_minimal_training_report.json"

TASKS = ["valence", "arousal"]
RECIPE = "ce_class_weighted"

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def metric_value(row, key):
    if not isinstance(row, dict):
        return None
    if key in row:
        val = row.get(key)
    elif key == "final_macro_f1" and "macro_f1" in row:
        val = row.get("macro_f1")
    elif key == "final_balanced_accuracy" and "balanced_accuracy" in row:
        val = row.get("balanced_accuracy")
    elif key == "final_accuracy" and "accuracy" in row:
        val = row.get("accuracy")
    elif isinstance(row.get("final"), dict) and key in row["final"]:
        val = row["final"][key]
    elif isinstance(row.get("metrics"), dict) and key in row["metrics"]:
        val = row["metrics"][key]
    else:
        return None
    if isinstance(val, dict):
        val = val.get("mean", val.get("value"))
    try:
        val = float(val)
    except Exception:
        return None
    if not math.isfinite(val):
        return None
    return val

def extract_runs(path):
    data = load_json(path)
    for key in ["runs", "results", "run_results"]:
        val = data.get(key)
        if isinstance(val, list):
            return val
    return []

def aggregate_by_task(runs):
    out = {}
    for task in TASKS:
        rows = []
        for r in runs:
            if not isinstance(r, dict):
                continue
            if r.get("task") != task:
                continue
            recipe = r.get("recipe")
            if recipe is not None and recipe != RECIPE:
                continue
            mf = metric_value(r, "final_macro_f1")
            ba = metric_value(r, "final_balanced_accuracy")
            if mf is None or ba is None:
                continue
            rows.append((mf, ba))
        if rows:
            out[task] = {
                "n_runs": len(rows),
                "macro_f1_mean": float(np.mean([x[0] for x in rows])),
                "bal_acc_mean": float(np.mean([x[1] for x in rows])),
            }
    if any(k in out for k in TASKS):
        vals = [out[k] for k in TASKS if k in out]
        out["ALL"] = {
            "n_runs": int(sum(v["n_runs"] for v in vals)),
            "macro_f1_mean": float(np.mean([v["macro_f1_mean"] for v in vals])),
            "bal_acc_mean": float(np.mean([v["bal_acc_mean"] for v in vals])),
        }
    return out

def fmt(x, digits=4):
    try:
        if x is None:
            return "NA"
        x = float(x)
        if not math.isfinite(x):
            return "NA"
        return f"{x:.{digits}f}"
    except Exception:
        return str(x)

def validate_primary(path, modality):
    data = load_json(path)
    runs = data.get("runs", [])
    if len(runs) != 12:
        raise SystemExit(f"ERROR: {modality} expected 12 runs, got {len(runs)}")
    missing = [
        (r.get("run_id"), r.get("task"), r.get("fold_id"))
        for r in runs
        if metric_value(r, "final_macro_f1") is None or metric_value(r, "final_balanced_accuracy") is None
    ]
    if missing:
        raise SystemExit(f"ERROR: {modality} missing metrics in runs: {missing[:5]}")
    return data, runs

objective = load_json(OBJECTIVE_JSON)
eeg_data, eeg_runs = validate_primary(EEG_JSON, "EEG")
emg_data, emg_runs = validate_primary(EMG_JSON, "EMG")
all_runs = eeg_runs + emg_runs
if len(all_runs) != 24:
    raise SystemExit(f"ERROR: expected 24 completed runs, got {len(all_runs)}")

previous_eeg_runs = extract_runs(DOCS / "idare_subject_relative_minimal_eeg_primary.json")
previous_emg_runs = extract_runs(DOCS / "idare_subject_relative_minimal_emg_primary.json")
global_eeg_runs = extract_runs(DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary.json")
global_emg_runs = extract_runs(DOCS / "idare_broader_eval_emg_feature_only_primary.json")

current_agg = {
    "EEG": aggregate_by_task(eeg_runs),
    "EMG": aggregate_by_task(emg_runs),
}
previous_agg = {
    "EEG": aggregate_by_task(previous_eeg_runs),
    "EMG": aggregate_by_task(previous_emg_runs),
}
global_agg = {
    "EEG": aggregate_by_task(global_eeg_runs),
    "EMG": aggregate_by_task(global_emg_runs),
}

comparison_rows = []
for modality in ["EEG", "EMG"]:
    for task in ["valence", "arousal", "ALL"]:
        cur = current_agg.get(modality, {}).get(task)
        if not cur:
            continue
        prev = previous_agg.get(modality, {}).get(task)
        glob = global_agg.get(modality, {}).get(task)
        comparison_rows.append({
            "modality": modality,
            "task": task,
            "current_macro_f1": cur.get("macro_f1_mean"),
            "previous_subject_relative_macro_f1": None if not prev else prev.get("macro_f1_mean"),
            "delta_vs_previous_subject_relative": None if not prev else cur.get("macro_f1_mean") - prev.get("macro_f1_mean"),
            "global_label_macro_f1_reference": None if not glob else glob.get("macro_f1_mean"),
            "delta_vs_global_label_reference": None if not glob else cur.get("macro_f1_mean") - glob.get("macro_f1_mean"),
            "current_balanced_accuracy": cur.get("bal_acc_mean"),
            "previous_subject_relative_bal_acc": None if not prev else prev.get("bal_acc_mean"),
            "delta_bal_acc_vs_previous_subject_relative": None if not prev else cur.get("bal_acc_mean") - prev.get("bal_acc_mean"),
            "global_label_bal_acc_reference": None if not glob else glob.get("bal_acc_mean"),
            "delta_bal_acc_vs_global_label_reference": None if not glob else cur.get("bal_acc_mean") - glob.get("bal_acc_mean"),
        })

one_class_by_modality_task = {}
for modality, runs in [("EEG", eeg_runs), ("EMG", emg_runs)]:
    for task in TASKS:
        rows = [r for r in runs if r.get("task") == task]
        one_class_by_modality_task[f"{modality}_{task}"] = int(sum(1 for r in rows if r.get("one_class_pred")))

all_rows = [r for r in comparison_rows if r["task"] == "ALL"]
mean_macro_all = float(np.mean([r["current_macro_f1"] for r in all_rows])) if all_rows else None
deltas_prev = [
    r["delta_vs_previous_subject_relative"]
    for r in all_rows
    if r.get("delta_vs_previous_subject_relative") is not None
]
mean_delta_prev_all = float(np.mean(deltas_prev)) if deltas_prev else None
max_one_class = max(one_class_by_modality_task.values()) if one_class_by_modality_task else 0

# Conservative diagnosis rules for this diagnostic first pass.
if mean_delta_prev_all is not None and mean_delta_prev_all >= 0.015 and max_one_class <= 1:
    diagnosis = "preprocessed_subject_relative_first_pass_promising"
    recommended_next_objective = "preprocessed_balanced_sampler_second_pass_objective"
elif mean_delta_prev_all is not None and mean_delta_prev_all >= 0.0 and max_one_class <= 1:
    diagnosis = "preprocessed_subject_relative_first_pass_mixed"
    recommended_next_objective = "subject_relative_preprocessed_training_review_closeout"
else:
    diagnosis = "preprocessed_subject_relative_first_pass_not_sufficient"
    recommended_next_objective = "subject_relative_feature_engineering_objective"

report = {
    "status": "complete_pending_review",
    "created_or_updated_utc": NOW,
    "objective": str(OBJECTIVE_MD),
    "objective_json": str(OBJECTIVE_JSON),
    "review": str(REVIEW_MD),
    "evidence_level": "24-run minimal diagnostic training; not final LOSO performance",
    "formulation": "subject_top_bottom_quantile_q33",
    "planned_runs": 24,
    "completed_runs": len(all_runs),
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next_objective,
    "mean_macro_f1_all_modalities": mean_macro_all,
    "mean_delta_macro_f1_vs_previous_subject_relative_all_modalities": mean_delta_prev_all,
    "one_class_prediction_counts_by_modality_task": one_class_by_modality_task,
    "current_aggregate": current_agg,
    "previous_subject_relative_aggregate": previous_agg,
    "global_label_reference_aggregate": global_agg,
    "comparison_rows": comparison_rows,
    "outputs": {
        "eeg_json": str(EEG_JSON),
        "eeg_md": str(EEG_MD),
        "eeg_predictions_csv": str(EEG_PRED),
        "emg_json": str(EMG_JSON),
        "emg_md": str(EMG_MD),
        "emg_predictions_csv": str(EMG_PRED),
    },
    "not_authorized": objective.get("not_authorized", []),
    "next_allowed_step": "Human review / closeout before optional second pass, feature engineering, or stopping.",
}
REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = []
md.append("# I-DARE Subject-relative Preprocessed Minimal Training Report")
md.append("")
md.append("## Status")
md.append("")
md.append("24-run minimal subject-relative preprocessed first pass complete; pending human review.")
md.append("")
md.append(f"Generated UTC: `{NOW}`")
md.append("")
md.append("## Run Matrix")
md.append("")
md.append("- Modalities: `EEG`, `EMG`")
md.append("- Tasks: `valence`, `arousal`")
md.append("- Folds: `6`")
md.append("- Seed: `11`")
md.append("- Recipe: `ce_class_weighted`")
md.append("- Formulation: `subject_top_bottom_quantile_q33`")
md.append("- EEG preprocessing: `eeg_window_channel_zscore_train_standard_scaled`")
md.append("- EMG preprocessing: `emg_signed_log1p_train_standard_scaled`")
md.append("")
md.append("## Aggregate Comparison")
md.append("")
md.append("| Modality | Task | Current macro F1 | Previous subject-relative macro F1 | Delta vs previous | Global-label reference macro F1 | Delta vs global ref | Current balanced acc |")
md.append("|---|---|---:|---:|---:|---:|---:|---:|")
for row in comparison_rows:
    md.append(
        f"| {row['modality']} | {row['task']} | {fmt(row['current_macro_f1'])} | "
        f"{fmt(row['previous_subject_relative_macro_f1'])} | {fmt(row['delta_vs_previous_subject_relative'])} | "
        f"{fmt(row['global_label_macro_f1_reference'])} | {fmt(row['delta_vs_global_label_reference'])} | "
        f"{fmt(row['current_balanced_accuracy'])} |"
    )
md.append("")
md.append("## Diagnosis")
md.append("")
md.append(f"- Diagnosis: `{diagnosis}`")
md.append(f"- Recommended next objective: `{recommended_next_objective}`")
md.append(f"- Mean macro-F1 across modality-level ALL rows: `{fmt(mean_macro_all)}`")
md.append(f"- Mean delta macro-F1 vs previous subject-relative minimal run: `{fmt(mean_delta_prev_all)}`")
md.append(f"- Max one-class prediction count per modality/task: `{max_one_class}`")
md.append("")
md.append("## Output Files")
md.append("")
for item in report["outputs"].values():
    md.append(f"- `{item}`")
md.append(f"- `{REPORT_JSON}`")
md.append("")
md.append("## Not Authorized")
md.append("")
for item in report["not_authorized"]:
    md.append(f"- {item}")
md.append("")
md.append("## Next Allowed Step")
md.append("")
md.append(report["next_allowed_step"])
md.append("")
REPORT_MD.write_text("\n".join(md), encoding="utf-8")

project_md = PROJECT_MD.read_text(encoding="utf-8")
row = "| I-DARE minimal subject-relative preprocessed training report | 24-run preprocessed subject-relative diagnostic training complete; pending human review | yes | `docs/idare_subject_relative_preprocessed_minimal_training_report.md` | Human review / closeout before optional second pass or next fix objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search; mainline change. |"
if "I-DARE minimal subject-relative preprocessed training report" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE minimal subject-relative preprocessed training objective |"):
            out.append(row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert roadmap row")
    project_md = "\n".join(out) + "\n"

bullet = f"- Minimal subject-relative preprocessed training is complete in `docs/idare_subject_relative_preprocessed_minimal_training_report.md`; diagnosis is `{diagnosis}` and next work is human review/closeout."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: project status marker not found")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = load_json(PROJECT_JSON)
decisions = project_json.setdefault("decisions", {})
decisions["idare_minimal_subject_relative_preprocessed_training_report"] = {
    "status": "complete_pending_review",
    "evidence": str(REPORT_MD),
    "evidence_json": str(REPORT_JSON),
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next_objective,
    "planned_runs": 24,
    "completed_runs": len(all_runs),
    "not_authorized": report["not_authorized"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_PREPROCESSED_MINIMAL_TRAINING_REPORT_WRITTEN")
print(REPORT_MD)
print(REPORT_JSON)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next_objective)
PY
echo

echo "===== 4) validate outputs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path

paths = [
    Path("docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json"),
    Path("docs/idare_subject_relative_preprocessed_minimal_emg_primary.json"),
    Path("docs/idare_subject_relative_preprocessed_minimal_training_report.json"),
    Path("docs/project_status_current.json"),
]
for p in paths:
    data = json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)
    if p.name.endswith("_primary.json") and len(data.get("runs", [])) != 12:
        raise SystemExit(f"ERROR: {p} expected 12 runs")

for p in [
    Path("docs/idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv"),
    Path("docs/idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv"),
]:
    with p.open(newline="", encoding="utf-8") as f:
        n = sum(1 for _ in csv.DictReader(f))
    print(p.name, "rows=", n)
    if n <= 0:
        raise SystemExit(f"ERROR: empty predictions {p}")

report = json.loads(Path("docs/idare_subject_relative_preprocessed_minimal_training_report.json").read_text(encoding="utf-8"))
if report.get("completed_runs") != 24:
    raise SystemExit("ERROR: completed_runs is not 24")
if not report.get("recommended_next_objective"):
    raise SystemExit("ERROR: missing recommended_next_objective")
print("diagnosis=", report.get("diagnosis"))
print("recommended_next_objective=", report.get("recommended_next_objective"))
PY

grep -n "## Status\|## Run Matrix\|## Aggregate Comparison\|## Diagnosis\|## Next Allowed Step" docs/idare_subject_relative_preprocessed_minimal_training_report.md
grep -n "minimal subject-relative preprocessed training report" docs/project_status_current.md
echo

echo "===== 5) file list ====="
ls -lh \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.md \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.md \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv \
  docs/idare_subject_relative_preprocessed_minimal_training_report.md \
  docs/idare_subject_relative_preprocessed_minimal_training_report.json \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push fixed/salvaged outputs ====="
git add \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.md \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.md \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv \
  docs/idare_subject_relative_preprocessed_minimal_training_report.md \
  docs/idare_subject_relative_preprocessed_minimal_training_report.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "exp: run I-DARE minimal subject-relative preprocessed training"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_minimal_subject_relative_preprocessed_training_fix.log"
