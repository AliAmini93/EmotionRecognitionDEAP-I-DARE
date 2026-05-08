#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start targeted SupCon/DG pair-sampler design review + ablation objective ====="
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
import json, csv, pathlib
print("OK_IMPORTS")
PY

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: repo is not clean; commit/stash before running this objective script." >&2
  git status --short
  exit 2
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required targeted pair/sampler design evidence ====="
required=(
  docs/idare_supcon_dg_failure_analysis_review_status.md
  docs/idare_supcon_dg_failure_analysis_review_status.json
  docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md
  docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.json
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_design_matrix.csv
  docs/idare_targeted_supcon_dg_pair_sampler_hyperparameter_registry.csv
  docs/idare_targeted_supcon_dg_pair_sampler_smoke_test_plan.csv
  docs/idare_targeted_supcon_dg_pair_sampler_decision_tree.csv
  docs/idare_supcon_dg_failure_analysis_report.md
  docs/idare_supcon_dg_failure_analysis_report.json
  docs/idare_minimal_supcon_dg_first_pass_report.md
  docs/idare_minimal_supcon_dg_first_pass_report.json
  docs/project_status_current.json
  docs/project_status_current.md
)
for f in "${required[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "ERROR: missing required evidence file: $f" >&2
    exit 3
  fi
  ls -lh "$f"
done
echo

echo "===== 3) create review closeout + targeted pair/sampler ablation training objective ====="
"$PY" - <<'PY'
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

design_obj_json_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.json"
failure_report_json_path = DOCS / "idare_supcon_dg_failure_analysis_report.json"
first_pass_report_json_path = DOCS / "idare_minimal_supcon_dg_first_pass_report.json"
design_matrix_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_design_matrix.csv"
hp_registry_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_hyperparameter_registry.csv"
smoke_plan_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_smoke_test_plan.csv"
decision_tree_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_decision_tree.csv"

design_obj = read_json(design_obj_json_path)
failure_report = read_json(failure_report_json_path)
first_pass_report = read_json(first_pass_report_json_path)

review_md_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_design_review_status.md"
review_json_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_design_review_status.json"
objective_md_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_objective.md"
objective_json_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_objective.json"
run_matrix_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_run_matrix.csv"
guardrail_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_guardrails.csv"

with design_matrix_path.open(newline="", encoding="utf-8") as f:
    design_rows = list(csv.DictReader(f))
design_by_id = {r["candidate_id"]: r for r in design_rows}

selected_candidate_ids = [
    "A0_CE_control",
    "A2_cross_subject_positive_only",
    "A4_rating_distance_guarded_supcon",
    "A6_vrex_only_recheck",
    "A5_cross_subject_supcon_vrex",
]
modalities = ["EEG", "EMG"]
tasks = ["valence", "arousal"]
folds = [1, 2, 3, 4, 5, 6]

run_rows = []
run_id = 1
for candidate_id in selected_candidate_ids:
    candidate = design_by_id[candidate_id]
    for modality in modalities:
        for task in tasks:
            for fold in folds:
                run_rows.append({
                    "planned_run_id": run_id,
                    "candidate_id": candidate_id,
                    "method_family": candidate["method_family"],
                    "modality": modality,
                    "task": task,
                    "fold": fold,
                    "positive_policy": candidate["positive_policy"],
                    "negative_policy": candidate["negative_policy"],
                    "sampler_policy": candidate["sampler_policy"],
                    "loss": candidate["loss"],
                    "dg_regularizer": candidate["dg_regularizer"],
                    "temperature": "0.10",
                    "lambda_supcon": "0.10" if "SupCon" in candidate["loss"] else "0.00",
                    "lambda_vrex": "0.10" if "VREx" in candidate["loss"] else "0.00",
                    "supcon_warmup_epochs": "2" if "SupCon" in candidate["loss"] else "0",
                    "vrex_warmup_epochs": "4" if "VREx" in candidate["loss"] else "0",
                    "epochs": "12",
                    "seed": "11",
                    "authorized": "yes",
                })
                run_id += 1

with run_matrix_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(run_rows[0].keys()))
    writer.writeheader()
    writer.writerows(run_rows)

guardrail_rows = [
    {
        "guardrail_id": "G1_clean_repo",
        "required": "yes",
        "pass_rule": "Repository must be clean before running the training script.",
        "failure_action": "Stop; commit/stash unrelated changes.",
    },
    {
        "guardrail_id": "G2_smokes_before_training",
        "required": "yes",
        "pass_rule": "Pair coverage, leakage guard, batch balance, rating-distance audit, micro-overfit, and shuffled-label negative control must pass.",
        "failure_action": "Stop; create smoke-fix objective.",
    },
    {
        "guardrail_id": "G3_no_broad_hp_search",
        "required": "yes",
        "pass_rule": "Only fixed first-pass hyperparameters from the run matrix are used.",
        "failure_action": "Stop; create separate hyperparameter objective.",
    },
    {
        "guardrail_id": "G4_no_full_training_claim",
        "required": "yes",
        "pass_rule": "Outputs are diagnostic only and cannot support final LOSO or mainline claims.",
        "failure_action": "Do not update claims; require review closeout.",
    },
    {
        "guardrail_id": "G5_candidate_interpretability",
        "required": "yes",
        "pass_rule": "Every candidate maps to one mechanistic question from the design matrix.",
        "failure_action": "Remove ambiguous candidate from matrix.",
    },
    {
        "guardrail_id": "G6_success_requires_consistency",
        "required": "yes",
        "pass_rule": "A candidate is promising only with consistent task/fold gains, not one isolated fold.",
        "failure_action": "Treat as inconclusive; require confirmation or failure analysis.",
    },
]
with guardrail_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(guardrail_rows[0].keys()))
    writer.writeheader()
    writer.writerows(guardrail_rows)

review_json = {
    "status": "review_closed",
    "created_utc": now,
    "reviewed_objective": str(DOCS / "idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md"),
    "reviewed_objective_json": str(design_obj_json_path),
    "review_decision": "Human review accepted the targeted SupCon/DG pair-sampler design and selected a minimal, guardrailed ablation objective.",
    "selected_next_objective": "targeted_supcon_dg_pair_sampler_ablation_objective",
    "planned_run_matrix_rows": len(run_rows),
    "selected_candidates": selected_candidate_ids,
    "blocked_until_review": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
    ],
    "next_allowed_step": "prepare_and_run_guardrailed_targeted_pair_sampler_ablation_command",
}
review_json_path.write_text(json.dumps(review_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

review_md = f"""# I-DARE Targeted SupCon/DG Pair-Sampler Design Review Status

## Status

Human review closed on: `{now}`

Reviewed design objective:

- `docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md`
- `docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.json`

## Review Decision

The targeted pair/sampler design is accepted for a **minimal diagnostic ablation**, not broad training.

The review accepts the following scientific logic:

- First-pass SupCon/DG failed despite valid smoke tests.
- The failure-analysis report recommended targeted pair/sampler ablation.
- The design now separates pair definition, negative definition, sampler policy, and DG penalty.
- The next run must be small, guardrailed, and interpretable.

## Selected First Ablation Candidates

The first ablation matrix is limited to these candidates:

1. `A0_CE_control`
2. `A2_cross_subject_positive_only`
3. `A4_rating_distance_guarded_supcon`
4. `A6_vrex_only_recheck`
5. `A5_cross_subject_supcon_vrex`

The candidate matrix is stored in:

`docs/idare_targeted_supcon_dg_pair_sampler_ablation_run_matrix.csv`

Planned diagnostic run rows: `{len(run_rows)}`

## Caution Requirement

This review does **not** authorize direct full SupCon/DG training.

It authorizes one guardrailed first-pass ablation with fixed hyperparameters and required smoke tests.

## Explicitly Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change

## Next Selected Step

Prepare/run the guardrailed targeted pair/sampler ablation command.
"""
review_md_path.write_text(review_md, encoding="utf-8")

objective_json = {
    "status": "objective_created",
    "created_utc": now,
    "objective": "targeted_supcon_dg_pair_sampler_ablation_objective",
    "review_input": str(review_json_path),
    "evidence_inputs": [
        str(failure_report_json_path),
        str(first_pass_report_json_path),
        str(design_obj_json_path),
        str(design_matrix_path),
        str(hp_registry_path),
        str(smoke_plan_path),
        str(decision_tree_path),
    ],
    "scientific_question": "Does a targeted pair/sampler definition, especially cross-subject positives or rating-distance-guarded pairs, improve subject-heldout performance compared with CE and VREx controls?",
    "authorized_scope": [
        "run required smoke tests before training",
        "run only the fixed planned candidate matrix",
        "use subject-heldout folds only",
        "use fixed hyperparameters",
        "write runs, predictions, pair audits, loss/embedding summaries, and combined report",
    ],
    "not_authorized": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
    ],
    "planned_run_matrix": str(run_matrix_path),
    "planned_run_rows": len(run_rows),
    "selected_candidates": selected_candidate_ids,
    "guardrails": str(guardrail_path),
    "pass_criteria": [
        "all required smoke tests pass before training",
        "all planned diagnostic runs complete or failures are explicitly reported",
        "run-level metrics and predictions are written",
        "candidate-level summary compares against CE and prior first-pass best cell",
        "decision tree is applied to decide next objective",
        "full training remains blocked pending human review",
    ],
    "expected_outputs": [
        "docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md",
        "docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json",
        "docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv",
        "docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv",
        "docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv",
        "docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv",
    ],
    "next_allowed_step": "prepare_and_run_guardrailed_targeted_pair_sampler_ablation_command",
}
objective_json_path.write_text(json.dumps(objective_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

objective_md = f"""# I-DARE Targeted SupCon/DG Pair-Sampler Ablation Objective

## Status

Created: `{now}`

Status: objective created for one guardrailed diagnostic ablation.

This objective follows:

- `docs/idare_supcon_dg_failure_analysis_report.md`
- `docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_design_matrix.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_smoke_test_plan.csv`

## Scientific Question

Does a targeted pair/sampler definition improve subject-heldout performance compared with CE and VREx controls?

More specifically:

1. Do cross-subject positives help more than naive label-only positives?
2. Do rating-distance-guarded positives/negatives reduce label-threshold noise?
3. Is VREx alone stronger than SupCon for this subject-variability problem?
4. Does SupCon + VREx help only when pair definitions are more careful?

## Authorized Scope

This is a **minimal diagnostic ablation**, not full training.

Authorized:

- required smoke tests before training
- fixed candidate matrix only
- fixed hyperparameters only
- EEG and EMG
- valence and arousal
- 6 subject-heldout folds
- no broad hyperparameter search

## Planned Run Matrix

Planned run matrix:

`docs/idare_targeted_supcon_dg_pair_sampler_ablation_run_matrix.csv`

Planned run rows: `{len(run_rows)}`

Selected candidates:

| Candidate | Mechanism |
|---|---|
| `A0_CE_control` | matched CE baseline |
| `A2_cross_subject_positive_only` | same-label positives across subjects only |
| `A4_rating_distance_guarded_supcon` | avoids borderline positive/negative contradictions |
| `A6_vrex_only_recheck` | checks best first-pass DG family without SupCon |
| `A5_cross_subject_supcon_vrex` | combines cross-subject SupCon with VREx |

## Required Guardrails

Guardrails are stored in:

`docs/idare_targeted_supcon_dg_pair_sampler_ablation_guardrails.csv`

The run command must stop if:

- repo is not clean
- leakage guard fails
- pair coverage fails
- batch balance fails
- rating-distance audit fails for guarded candidates
- micro-overfit fails
- shuffled-label negative control fails

## Required Smoke Tests Before Training

The run command must execute the smoke tests defined in:

`docs/idare_targeted_supcon_dg_pair_sampler_smoke_test_plan.csv`

Training is blocked if any required smoke test fails.

## Fixed Hyperparameters

The first ablation must use the fixed values in:

`docs/idare_targeted_supcon_dg_pair_sampler_ablation_run_matrix.csv`

This objective does not authorize broad hyperparameter search.

## Expected Outputs

The run command should write:

- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv`

## Pass Criteria

This objective passes only if:

- all required smoke tests are reported
- all candidate/fold/task/modality rows are either complete or explicitly failed
- pair audit shows valid pair coverage
- no leakage is detected
- candidate-level comparison is written
- the decision tree is applied
- direct full SupCon/DG training remains blocked pending human review

## Decision Rules

Use:

`docs/idare_targeted_supcon_dg_pair_sampler_decision_tree.csv`

No isolated best fold is enough. A candidate is only promising if gains are consistent across tasks/folds and interpretable against the candidate mechanism.

## Explicitly Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change

## Next Allowed Step

Prepare and run the guardrailed targeted pair/sampler ablation command.
"""
objective_md_path.write_text(objective_md, encoding="utf-8")

# Update roadmap/status.
status_json_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"
status = read_json(status_json_path)

event_review = {
    "timestamp_utc": now,
    "type": "review_closeout",
    "name": "I-DARE targeted SupCon/DG pair-sampler design review",
    "status": "human review accepted targeted design; minimal ablation objective selected",
    "evidence": str(review_md_path),
    "next_allowed_step": "create/run guardrailed targeted pair/sampler ablation",
    "blocked": objective_json["not_authorized"],
}
event_objective = {
    "timestamp_utc": now,
    "type": "objective_created",
    "name": "I-DARE targeted SupCon/DG pair-sampler ablation objective",
    "status": f"short-term diagnostic ablation objective created; planned rows={len(run_rows)}",
    "evidence": str(objective_md_path),
    "next_allowed_step": "prepare_and_run_guardrailed_targeted_pair_sampler_ablation_command",
    "blocked": objective_json["not_authorized"],
}

status["last_updated_utc"] = now
status.setdefault("idare_protocol_events", [])
status["idare_protocol_events"].extend([event_review, event_objective])
status["current_idare_next_allowed_step"] = "prepare_and_run_guardrailed_targeted_pair_sampler_ablation_command"
status["current_idare_blocked_steps"] = objective_json["not_authorized"]
status_json_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Targeted SupCon/DG Pair-Sampler Ablation Objective

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE targeted SupCon/DG pair-sampler design review | human review accepted design; minimal ablation selected | `docs/idare_targeted_supcon_dg_pair_sampler_ablation_design_review_status.md` | Prepare/run guardrailed targeted pair/sampler ablation. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE targeted SupCon/DG pair-sampler ablation objective | short-term diagnostic ablation objective created; planned rows={len(run_rows)} | `docs/idare_targeted_supcon_dg_pair_sampler_ablation_objective.md` | Prepare/run guardrailed targeted pair/sampler ablation command. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- The targeted pair/sampler ablation objective is defined in `docs/idare_targeted_supcon_dg_pair_sampler_ablation_objective.md`.
- The run matrix is fixed in `docs/idare_targeted_supcon_dg_pair_sampler_ablation_run_matrix.csv`; this is not a broad hyperparameter search.
"""
if "I-DARE Targeted SupCon/DG Pair-Sampler Ablation Objective" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")
else:
    status_md_path.write_text(status_md, encoding="utf-8")

print("OK_TARGETED_SUPCON_DG_PAIR_SAMPLER_ABLATION_OBJECTIVE_WRITTEN")
print(review_md_path)
print(review_json_path)
print(objective_md_path)
print(objective_json_path)
print(run_matrix_path)
print(guardrail_path)
print("planned_run_rows=", len(run_rows))
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path

json_paths = [
    Path("docs/idare_targeted_supcon_dg_pair_sampler_ablation_design_review_status.json"),
    Path("docs/idare_targeted_supcon_dg_pair_sampler_ablation_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

with open("docs/idare_targeted_supcon_dg_pair_sampler_ablation_run_matrix.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
print("planned_run_matrix_rows=", len(rows))
if len(rows) != 120:
    raise SystemExit(f"ERROR: expected 120 planned run rows, got {len(rows)}")

with open("docs/idare_targeted_supcon_dg_pair_sampler_ablation_guardrails.csv", newline="", encoding="utf-8") as f:
    guards = list(csv.DictReader(f))
print("guardrail_rows=", len(guards))
if len(guards) < 6:
    raise SystemExit("ERROR: expected at least 6 guardrails")

required_terms = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "Required Smoke Tests Before Training",
    "Planned Run Matrix",
    "Decision Rules",
]
text = Path("docs/idare_targeted_supcon_dg_pair_sampler_ablation_objective.md").read_text(encoding="utf-8")
for term in required_terms:
    if term not in text:
        raise SystemExit(f"ERROR: missing term in objective md: {term}")

print("ALL_TARGETED_SUPCON_DG_PAIR_SAMPLER_ABLATION_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "Status|Scientific Question|Authorized Scope|Planned Run Matrix|Required Smoke Tests|Pass Criteria|Next Allowed Step" \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_objective.md
grep -nE "targeted SupCon/DG pair-sampler" docs/project_status_current.md | tail -n 20
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_design_review_status.md \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_design_review_status.json \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_objective.md \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_objective.json \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_run_matrix.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_guardrails.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE targeted SupCon DG pair sampler ablation objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_targeted_supcon_dg_pair_sampler_ablation_objective.log"
