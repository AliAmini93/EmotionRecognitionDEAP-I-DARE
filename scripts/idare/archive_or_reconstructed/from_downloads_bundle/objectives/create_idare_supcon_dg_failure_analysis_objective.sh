#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start minimal SupCon/DG first-pass review + failure-analysis objective ====="
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
  echo "ERROR: repo is not clean; commit/stash changes before creating the objective." >&2
  git status --short --branch >&2
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required SupCon/DG first-pass evidence ====="
required=(
  docs/idare_minimal_supcon_dg_first_pass_training_objective.md
  docs/idare_minimal_supcon_dg_first_pass_training_objective.json
  docs/idare_minimal_supcon_dg_first_pass_report.md
  docs/idare_minimal_supcon_dg_first_pass_report.json
  docs/idare_minimal_supcon_dg_first_pass_runs.csv
  docs/idare_minimal_supcon_dg_first_pass_predictions.csv
  docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv
  docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv
  docs/idare_subject_variability_supcon_dg_design_spec.md
  docs/idare_subject_variability_supcon_dg_design_spec.json
  docs/idare_subject_variability_supcon_dg_smoke_tests_report.md
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

echo "===== 3) create review closeout + SupCon/DG failure-analysis objective ====="
"$PY" - <<'PY'
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

ROOT = Path(".")
DOCS = ROOT / "docs"

now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
review_md = DOCS / "idare_minimal_supcon_dg_first_pass_review_status.md"
review_json = DOCS / "idare_minimal_supcon_dg_first_pass_review_status.json"
objective_md = DOCS / "idare_supcon_dg_failure_analysis_objective.md"
objective_json = DOCS / "idare_supcon_dg_failure_analysis_objective.json"
status_md = DOCS / "project_status_current.md"
status_json = DOCS / "project_status_current.json"

first_pass_report_path = DOCS / "idare_minimal_supcon_dg_first_pass_report.json"
runs_csv = DOCS / "idare_minimal_supcon_dg_first_pass_runs.csv"
pred_csv = DOCS / "idare_minimal_supcon_dg_first_pass_predictions.csv"
emb_csv = DOCS / "idare_minimal_supcon_dg_first_pass_embedding_summary.csv"
loss_csv = DOCS / "idare_minimal_supcon_dg_first_pass_loss_summary.csv"

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def read_csv_rows(path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

report = read_json(first_pass_report_path)
runs = read_csv_rows(runs_csv)
pred_rows = sum(1 for _ in pred_csv.open("r", encoding="utf-8")) - 1
emb_rows = sum(1 for _ in emb_csv.open("r", encoding="utf-8")) - 1
loss_rows = sum(1 for _ in loss_csv.open("r", encoding="utf-8")) - 1

diagnosis = report.get("diagnosis", "minimal_supcon_dg_first_pass_not_sufficient")
recommended = report.get("recommended_next_objective", "supcon_dg_failure_analysis_objective")
best = report.get("best", {}) or report.get("best_cell", {}) or {}

# Robust aggregate from runs CSV.
metric_fields = ["macro_f1", "final_macro_f1", "balanced_accuracy", "bal_acc", "final_balanced_accuracy", "accuracy", "acc", "final_accuracy"]
method_stats = {}
for r in runs:
    key = (r.get("method") or r.get("recipe") or "unknown", r.get("modality") or "unknown", r.get("task") or "unknown")
    method_stats.setdefault(key, []).append(r)

def get_float(row, names):
    for n in names:
        if n in row and row[n] not in ("", None):
            try:
                return float(row[n])
            except ValueError:
                pass
    return None

summary_rows = []
for (method, modality, task), rows in method_stats.items():
    f1s = [get_float(r, ["macro_f1", "final_macro_f1"]) for r in rows]
    bas = [get_float(r, ["bal_acc", "balanced_accuracy", "final_balanced_accuracy"]) for r in rows]
    accs = [get_float(r, ["acc", "accuracy", "final_accuracy"]) for r in rows]
    f1s = [x for x in f1s if x is not None]
    bas = [x for x in bas if x is not None]
    accs = [x for x in accs if x is not None]
    summary_rows.append({
        "method": method,
        "modality": modality,
        "task": task,
        "n_runs": len(rows),
        "mean_macro_f1": mean(f1s) if f1s else None,
        "mean_balanced_accuracy": mean(bas) if bas else None,
        "mean_accuracy": mean(accs) if accs else None,
    })
summary_rows.sort(key=lambda x: (x["mean_macro_f1"] if x["mean_macro_f1"] is not None else -1), reverse=True)
best_from_runs = summary_rows[0] if summary_rows else {}

review_obj = {
    "status": "review_closed",
    "created_at_utc": now,
    "reviewed_artifact": "docs/idare_minimal_supcon_dg_first_pass_report.md",
    "accepted_diagnosis": diagnosis,
    "accepted_recommendation": recommended,
    "decision": "first-pass SupCon/DG is not sufficient; analyze failure before any broader SupCon/DG training or hyperparameter search",
    "evidence": {
        "runs": len(runs),
        "prediction_rows": pred_rows,
        "embedding_summary_rows": emb_rows,
        "loss_summary_rows": loss_rows,
        "best_report_cell": best,
        "best_recomputed_cell": best_from_runs,
    },
    "blocked_until_review": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
    ],
    "next_objective": "supcon_dg_failure_analysis_objective",
}
review_json.write_text(json.dumps(review_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

review_md.write_text(f"""# I-DARE Minimal SupCon/DG First-pass Review Status

## Status

Human review accepted the minimal SupCon/DG first-pass result as **not sufficient**.

- Created at: `{now}`
- Reviewed report: `docs/idare_minimal_supcon_dg_first_pass_report.md`
- Accepted diagnosis: `{diagnosis}`
- Accepted next objective: `{recommended}`
- Runs reviewed: `{len(runs)}`
- Prediction rows reviewed: `{pred_rows}`

## Review Decision

The first-pass SupCon/DG intervention is scientifically useful but not yet a fix.

The run completed and produced valid outputs, but the aggregate result does not justify moving to direct full SupCon/DG training, broad hyperparameter search, EEG+EMG fusion, mainline changes, or any final LOSO claim.

The correct next step is a **read-only failure analysis** to determine why the intervention did not improve robustly.

## Key Evidence

Best recomputed cell from `docs/idare_minimal_supcon_dg_first_pass_runs.csv`:

```json
{json.dumps(best_from_runs, indent=2, ensure_ascii=False)}
```

## Next Selected Step

Create and run:

- `docs/idare_supcon_dg_failure_analysis_objective.md`
- `docs/idare_supcon_dg_failure_analysis_objective.json`

This next step must explain failure modes before any new training matrix is authorized.
""", encoding="utf-8")

objective_obj = {
    "status": "objective_created",
    "created_at_utc": now,
    "objective_id": "supcon_dg_failure_analysis_objective",
    "title": "I-DARE SupCon/DG failure analysis objective",
    "scientific_question": "Why did the minimal SupCon/DG first-pass fail to produce a robust improvement, and what does that imply for the next scientifically valid intervention?",
    "authorized_scope": {
        "type": "read_only_analysis",
        "allowed_inputs": [
            "docs/idare_minimal_supcon_dg_first_pass_runs.csv",
            "docs/idare_minimal_supcon_dg_first_pass_predictions.csv",
            "docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv",
            "docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv",
            "docs/idare_subject_variability_supcon_dg_design_spec.md",
            "docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv",
            "docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv",
            "docs/idare_subject_variability_supcon_dg_smoke_tests_report.json",
            "prior diagnostic reports under docs/",
        ],
        "forbidden": [
            "new model training",
            "direct full SupCon/DG training",
            "broad hyperparameter search",
            "EEG+EMG fusion",
            "final LOSO claim",
            "mainline change",
        ],
    },
    "required_analysis_questions": [
        "Did SupCon loss decrease while validation macro-F1 / balanced accuracy stayed near chance?",
        "Did embedding diagnostics improve within train but fail under subject-heldout validation?",
        "Were positive pairs too easy, too local, too subject-specific, or too sparse for cross-subject generalization?",
        "Were negative pairs semantically noisy because affect labels are subject-relative and ambiguous?",
        "Did VREx reduce variance across subject groups or merely regularize without improving signal?",
        "Were failures modality/task-specific, fold-specific, or method-specific?",
        "Did any method improve consistency even if mean performance stayed low?",
        "Is the next rational step pair/sampler redesign, subject-aware DG, label/task redesign, representation change, or stop condition?",
    ],
    "expected_outputs": [
        "docs/idare_supcon_dg_failure_analysis_report.md",
        "docs/idare_supcon_dg_failure_analysis_report.json",
        "docs/idare_supcon_dg_failure_method_task_summary.csv",
        "docs/idare_supcon_dg_failure_fold_summary.csv",
        "docs/idare_supcon_dg_failure_loss_embedding_alignment.csv",
        "docs/idare_supcon_dg_failure_decision_matrix.csv",
    ],
    "pass_criteria": [
        "Report is read-only and uses committed outputs only.",
        "Report explains whether the failure is caused by objective mismatch, pair/sampler design, representation weakness, fold/task instability, or insufficient training evidence.",
        "Report produces a decision matrix that selects exactly one next objective or a stop condition.",
        "Report blocks broad hyperparameter search unless failure analysis justifies a specific targeted ablation.",
    ],
    "next_allowed_step": "prepare_reviewed_supcon_dg_failure_analysis_command",
}
objective_json.write_text(json.dumps(objective_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

objective_md.write_text(f"""# I-DARE SupCon/DG Failure Analysis Objective

## Status

Short-term read-only objective created.

- Created at: `{now}`
- Objective id: `supcon_dg_failure_analysis_objective`
- Previous report: `docs/idare_minimal_supcon_dg_first_pass_report.md`
- Previous diagnosis: `{diagnosis}`

## Scientific Question

Why did the minimal SupCon/DG first-pass fail to produce a robust improvement, and what does that imply for the next scientifically valid intervention?

## Motivation

The minimal first-pass did not justify full SupCon/DG training.

That does **not** mean SupCon/DG is invalid. It means we must determine whether the failure came from:

1. objective mismatch,
2. positive/negative pair design,
3. subject-domain grouping or VREx formulation,
4. representation weakness,
5. label/task ambiguity,
6. fold/task instability,
7. insufficient first-pass training evidence,
8. or a combination of the above.

## Authorized Scope

Allowed: read-only analysis of committed outputs.

Primary inputs:

- `docs/idare_minimal_supcon_dg_first_pass_runs.csv`
- `docs/idare_minimal_supcon_dg_first_pass_predictions.csv`
- `docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv`
- `docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv`
- `docs/idare_subject_variability_supcon_dg_design_spec.md`
- `docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv`
- `docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv`
- `docs/idare_subject_variability_supcon_dg_smoke_tests_report.json`
- prior diagnostic reports under `docs/`

Forbidden until review:

- new model training,
- direct full SupCon/DG training,
- broad hyperparameter search,
- EEG+EMG fusion,
- final LOSO claim,
- mainline change.

## Required Analysis Questions

The failure-analysis report must answer:

1. Did SupCon loss decrease while validation macro-F1 / balanced accuracy stayed near chance?
2. Did embedding diagnostics improve within train but fail under subject-heldout validation?
3. Were positive pairs too easy, too local, too subject-specific, or too sparse for cross-subject generalization?
4. Were negative pairs semantically noisy because affect labels are subject-relative and ambiguous?
5. Did VREx reduce variance across subject groups or merely regularize without improving signal?
6. Were failures modality/task-specific, fold-specific, or method-specific?
7. Did any method improve consistency even if mean performance stayed low?
8. Is the next rational step pair/sampler redesign, subject-aware DG, label/task redesign, representation change, or stop condition?

## Expected Outputs

The next script should create:

- `docs/idare_supcon_dg_failure_analysis_report.md`
- `docs/idare_supcon_dg_failure_analysis_report.json`
- `docs/idare_supcon_dg_failure_method_task_summary.csv`
- `docs/idare_supcon_dg_failure_fold_summary.csv`
- `docs/idare_supcon_dg_failure_loss_embedding_alignment.csv`
- `docs/idare_supcon_dg_failure_decision_matrix.csv`

## Pass Criteria

A passing report must:

- use committed outputs only,
- explain whether failure is due to objective mismatch, pair/sampler design, representation weakness, fold/task instability, or insufficient evidence,
- produce a decision matrix with one selected next objective or stop condition,
- block broad hyperparameter search unless a specific targeted ablation is justified.

## Next Allowed Step

Prepare a reviewed read-only command/script for the SupCon/DG failure analysis report.
""", encoding="utf-8")

# Update project_status_current.json conservatively.
status = read_json(status_json)
entry_review = {
    "name": "I-DARE minimal SupCon/DG first-pass review",
    "status": "human review accepted insufficient first pass; failure analysis selected",
    "active": True,
    "artifact": str(review_md),
    "next_step": "Create/run SupCon/DG failure-analysis objective.",
    "blocked": "EEG+EMG fusion; final LOSO claim; direct full SupCon/DG training; broad hyperparameter search; mainline change.",
    "created_at_utc": now,
}
entry_objective = {
    "name": "I-DARE SupCon/DG failure analysis objective",
    "status": "short-term read-only objective created to explain first-pass failure",
    "active": True,
    "artifact": str(objective_md),
    "next_step": "Prepare reviewed read-only failure-analysis command/script.",
    "blocked": "EEG+EMG fusion; final LOSO claim; direct full SupCon/DG training; broad hyperparameter search; mainline change.",
    "created_at_utc": now,
}

def append_unique_list(container, key, entries):
    if key not in container or not isinstance(container[key], list):
        container[key] = []
    existing = {json.dumps(x, sort_keys=True, ensure_ascii=False) for x in container[key] if isinstance(x, dict)}
    for e in entries:
        sig = json.dumps(e, sort_keys=True, ensure_ascii=False)
        if sig not in existing:
            container[key].append(e)
            existing.add(sig)

if isinstance(status, dict):
    # Keep compatibility with unknown schema by adding a dedicated ledger and a short current note.
    append_unique_list(status, "idare_objective_history", [entry_review, entry_objective])
    status["current_idare_next_step"] = {
        "objective": "supcon_dg_failure_analysis_objective",
        "artifact": str(objective_md),
        "next_step": "prepare_reviewed_supcon_dg_failure_analysis_command",
        "updated_at_utc": now,
    }
    status_json.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Update markdown roadmap conservatively by appending a small section if not present.
md = status_md.read_text(encoding="utf-8")
marker = "## I-DARE SupCon/DG Failure Analysis Objective"
block = f"""

{marker}

- Human review of the minimal SupCon/DG first-pass is frozen in `{review_md}`.
- A read-only SupCon/DG failure-analysis objective is defined in `{objective_md}`.
- Next work is to prepare a reviewed read-only failure-analysis command/script.
- Blocked until review: direct full SupCon/DG training, broad hyperparameter search, EEG+EMG fusion, final LOSO claim, and mainline change.
"""
if marker not in md:
    status_md.write_text(md.rstrip() + block + "\n", encoding="utf-8")

print("OK_SUPCON_DG_FAILURE_OBJECTIVE_WRITTEN")
print(review_md)
print(review_json)
print(objective_md)
print(objective_json)
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path

paths = [
    Path("docs/idare_minimal_supcon_dg_first_pass_review_status.json"),
    Path("docs/idare_supcon_dg_failure_analysis_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

checks = [
    ("docs/idare_minimal_supcon_dg_first_pass_review_status.md", [
        "direct full SupCon/DG training",
        "SupCon/DG first-pass",
        "not sufficient",
    ]),
    ("docs/idare_supcon_dg_failure_analysis_objective.md", [
        "Scientific Question",
        "positive/negative pair",
        "VREx",
        "broad hyperparameter search",
        "Expected Outputs",
    ]),
]
for path, terms in checks:
    text = Path(path).read_text(encoding="utf-8")
    for term in terms:
        if term not in text:
            raise SystemExit(f"ERROR: missing term {term!r} in {path}")
    print("OK_TERMS:", path)

obj = json.loads(Path("docs/idare_supcon_dg_failure_analysis_objective.json").read_text(encoding="utf-8"))
if obj.get("next_allowed_step") != "prepare_reviewed_supcon_dg_failure_analysis_command":
    raise SystemExit("ERROR: unexpected next_allowed_step")
print("next_allowed_step=", obj["next_allowed_step"])
print("ALL_SUPCON_DG_FAILURE_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "## Status|## Scientific Question|## Required Analysis Questions|## Expected Outputs|## Pass Criteria|## Next Allowed Step" \
  docs/idare_supcon_dg_failure_analysis_objective.md

grep -n "SupCon/DG failure" docs/project_status_current.md | tail -5 || true
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_minimal_supcon_dg_first_pass_review_status.md \
  docs/idare_minimal_supcon_dg_first_pass_review_status.json \
  docs/idare_supcon_dg_failure_analysis_objective.md \
  docs/idare_supcon_dg_failure_analysis_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE SupCon DG failure analysis objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_supcon_dg_failure_analysis_objective.log"
