#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start SupCon/DG failure-analysis review + targeted pair/sampler ablation-design objective ====="
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
import json, pathlib, sys
print("OK_IMPORTS")
PY

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: repo is not clean; commit/stash before running this objective script." >&2
  git status --short
  exit 2
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required SupCon/DG failure-analysis evidence ====="
required=(
  docs/idare_supcon_dg_failure_analysis_report.md
  docs/idare_supcon_dg_failure_analysis_report.json
  docs/idare_supcon_dg_failure_method_task_summary.csv
  docs/idare_supcon_dg_failure_fold_summary.csv
  docs/idare_supcon_dg_failure_loss_embedding_alignment.csv
  docs/idare_supcon_dg_failure_decision_matrix.csv
  docs/idare_minimal_supcon_dg_first_pass_report.md
  docs/idare_minimal_supcon_dg_first_pass_report.json
  docs/idare_subject_variability_supcon_dg_design_spec.md
  docs/idare_subject_variability_supcon_dg_design_spec.json
  docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv
  docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv
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

echo "===== 3) create review closeout + targeted SupCon/DG pair/sampler ablation-design objective ====="
"$PY" - <<'PY'
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(".")
DOCS = ROOT / "docs"
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

failure_report_json = DOCS / "idare_supcon_dg_failure_analysis_report.json"
failure_report_md = DOCS / "idare_supcon_dg_failure_analysis_report.md"
first_pass_report_json = DOCS / "idare_minimal_supcon_dg_first_pass_report.json"
design_spec_json = DOCS / "idare_subject_variability_supcon_dg_design_spec.json"

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

failure_data = read_json(failure_report_json)
first_pass_data = read_json(first_pass_report_json)
design_data = read_json(design_spec_json)

diagnosis = failure_data.get("diagnosis", "supcon_dg_first_pass_failed_despite_valid_smokes")
recommended_next = failure_data.get(
    "recommended_next_objective",
    "targeted_supcon_dg_pair_sampler_objective_ablation_design",
)
best_cell = failure_data.get("best_cell") or first_pass_data.get("best") or {}

review_md_path = DOCS / "idare_supcon_dg_failure_analysis_review_status.md"
review_json_path = DOCS / "idare_supcon_dg_failure_analysis_review_status.json"
objective_md_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md"
objective_json_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.json"
matrix_csv_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_design_matrix.csv"
hp_csv_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_hyperparameter_registry.csv"
smoke_csv_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_smoke_test_plan.csv"
decision_csv_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_decision_tree.csv"

review_json = {
    "status": "review_closed",
    "created_utc": now,
    "reviewed_report": str(failure_report_md),
    "reviewed_report_json": str(failure_report_json),
    "accepted_diagnosis": diagnosis,
    "review_decision": "Human review accepted that first-pass SupCon/DG failed despite valid smoke tests; proceed to targeted pair/sampler ablation design before any broader training.",
    "best_cell": best_cell,
    "selected_next_objective": "targeted_supcon_dg_pair_sampler_objective_ablation_design",
    "blocked_until_next_review": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
    ],
    "next_allowed_step": "create_targeted_supcon_dg_pair_sampler_ablation_design_spec",
}
review_json_path.write_text(json.dumps(review_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

best_cell_text = json.dumps(best_cell, ensure_ascii=False, sort_keys=True)
review_md = f"""# I-DARE SupCon/DG Failure-analysis Review Status

## Status

Human review closed on: `{now}`

The read-only SupCon/DG failure-analysis report is accepted for planning purposes.

Reviewed report:

- `docs/idare_supcon_dg_failure_analysis_report.md`
- `docs/idare_supcon_dg_failure_analysis_report.json`

## Review Decision

Accepted diagnosis:

`{diagnosis}`

Scientific interpretation:

- SupCon/DG smoke tests passed, so the basic plumbing, sampler integrity, leakage guards, micro-overfit behavior, and negative-control behavior were not the obvious blocker.
- The minimal first-pass training did not produce a reliable subject-heldout improvement.
- The failure should not be treated as evidence that SupCon/DG is intrinsically unsuitable.
- The failure should be treated as evidence that the first-pass pair/sampler/objective design was probably too broad or too weak for the subject-variability mechanism.

Best first-pass cell recorded by the failure-analysis report:

```json
{best_cell_text}
```

## Caution Requirement

No broad SupCon/DG training is authorized from this review.

The next step must be a design/spec objective that makes the pair definition, negative definition, batch sampler, loss weights, and diagnostic pass/fail rules explicit before any new training run.

## Next Selected Step

Create a targeted SupCon/DG pair/sampler ablation-design objective.

Selected objective:

`targeted_supcon_dg_pair_sampler_objective_ablation_design`

## Explicitly Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
"""
review_md_path.write_text(review_md, encoding="utf-8")

ablation_rows = [
    {
        "candidate_id": "A0_CE_control",
        "method_family": "control",
        "positive_policy": "none",
        "negative_policy": "none",
        "sampler_policy": "subject_balanced_label_balanced",
        "loss": "CE",
        "dg_regularizer": "none",
        "why_included": "Anchors every targeted ablation against the same subject-relative/preprocessed feature setup.",
        "allowed_next_training": "yes_minimal_control_only",
    },
    {
        "candidate_id": "A1_label_only_supcon",
        "method_family": "SupCon",
        "positive_policy": "same task label across subjects and within subject",
        "negative_policy": "opposite task label",
        "sampler_policy": "subject_balanced_label_balanced_min_2_pos_per_anchor",
        "loss": "CE + SupCon",
        "dg_regularizer": "none",
        "why_included": "Tests whether the prior broad supervised contrastive definition is already sufficient when isolated.",
        "allowed_next_training": "yes_minimal",
    },
    {
        "candidate_id": "A2_cross_subject_positive_only",
        "method_family": "SupCon",
        "positive_policy": "same label, cross-subject positives only",
        "negative_policy": "opposite label; avoid same-subject negatives when possible",
        "sampler_policy": "multi_subject_per_class_batch",
        "loss": "CE + SupCon",
        "dg_regularizer": "none",
        "why_included": "Directly targets subject-invariant affect structure instead of reinforcing within-subject idiosyncrasies.",
        "allowed_next_training": "yes_minimal",
    },
    {
        "candidate_id": "A3_within_subject_anchor_cross_subject_positive",
        "method_family": "SupCon",
        "positive_policy": "anchor has within-subject stable examples plus cross-subject same-label positives",
        "negative_policy": "opposite label with rating-distance guard",
        "sampler_policy": "paired_subject_balanced_batch",
        "loss": "CE + SupCon",
        "dg_regularizer": "none",
        "why_included": "Tests whether subject-relative consistency can stabilize labels while cross-subject positives drive invariance.",
        "allowed_next_training": "yes_minimal",
    },
    {
        "candidate_id": "A4_rating_distance_guarded_supcon",
        "method_family": "SupCon",
        "positive_policy": "same class and close subject-relative rating quantile",
        "negative_policy": "opposite class only if rating-distance margin is large",
        "sampler_policy": "label_balanced_distance_guarded",
        "loss": "CE + SupCon",
        "dg_regularizer": "none",
        "why_included": "Reduces false positives/false negatives created by hard threshold labels.",
        "allowed_next_training": "yes_minimal",
    },
    {
        "candidate_id": "A5_cross_subject_supcon_vrex",
        "method_family": "SupCon_DG",
        "positive_policy": "same label, cross-subject positives only",
        "negative_policy": "opposite label with rating-distance guard",
        "sampler_policy": "multi_subject_per_class_batch",
        "loss": "CE + SupCon + VREx",
        "dg_regularizer": "VREx by training subject after warmup",
        "why_included": "Combines the most subject-invariant pair definition with the best first-pass DG family.",
        "allowed_next_training": "yes_minimal",
    },
    {
        "candidate_id": "A6_vrex_only_recheck",
        "method_family": "DG",
        "positive_policy": "none",
        "negative_policy": "none",
        "sampler_policy": "subject_balanced_label_balanced",
        "loss": "CE + VREx",
        "dg_regularizer": "VREx by training subject after warmup",
        "why_included": "Rechecks the best first-pass family without contrastive noise.",
        "allowed_next_training": "yes_minimal",
    },
    {
        "candidate_id": "A7_subject_adversarial_design_only",
        "method_family": "DG_design_only",
        "positive_policy": "not run in first targeted matrix",
        "negative_policy": "not run in first targeted matrix",
        "sampler_policy": "subject_balanced_label_balanced",
        "loss": "CE + optional adversarial subject confusion",
        "dg_regularizer": "domain-adversarial subject head",
        "why_included": "Kept as design candidate only; not authorized until pair/sampler ablation is reviewed.",
        "allowed_next_training": "no_design_only",
    },
]
with matrix_csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(ablation_rows[0].keys()))
    writer.writeheader()
    writer.writerows(ablation_rows)

hp_rows = [
    {
        "parameter": "temperature",
        "default": "0.10",
        "allowed_values_first_targeted_matrix": "0.10",
        "reason": "Avoid broad search; keep contrastive scale fixed unless failure analysis specifically implicates saturation.",
    },
    {
        "parameter": "lambda_supcon",
        "default": "0.10",
        "allowed_values_first_targeted_matrix": "0.05,0.10",
        "reason": "Small two-value check only if matrix budget allows; prior first pass may have over-regularized embeddings.",
    },
    {
        "parameter": "lambda_vrex",
        "default": "0.10",
        "allowed_values_first_targeted_matrix": "0.05,0.10",
        "reason": "VREx was the best family but unstable; use low values and compare against VREx-only control.",
    },
    {
        "parameter": "supcon_warmup_epochs",
        "default": "2",
        "allowed_values_first_targeted_matrix": "2",
        "reason": "Let CE stabilize before applying representation pressure.",
    },
    {
        "parameter": "vrex_warmup_epochs",
        "default": "4",
        "allowed_values_first_targeted_matrix": "4",
        "reason": "Avoid early penalty from noisy subject losses.",
    },
    {
        "parameter": "batch_subjects",
        "default": "8",
        "allowed_values_first_targeted_matrix": "8",
        "reason": "Ensure cross-subject positives/negatives exist in each batch.",
    },
    {
        "parameter": "samples_per_subject",
        "default": "4",
        "allowed_values_first_targeted_matrix": "4",
        "reason": "Maintains within-subject anchors without letting one subject dominate.",
    },
    {
        "parameter": "rating_distance_negative_margin",
        "default": "0.33",
        "allowed_values_first_targeted_matrix": "0.33",
        "reason": "Avoid pushing borderline affect states apart.",
    },
]
with hp_csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(hp_rows[0].keys()))
    writer.writeheader()
    writer.writerows(hp_rows)

smoke_rows = [
    {
        "smoke_test_id": "S1_pair_coverage",
        "required_before_training": "yes",
        "pass_rule": ">=95% eligible anchors have at least one valid positive and one valid negative under each candidate policy.",
        "failure_action": "Do not train candidate; redesign sampler.",
    },
    {
        "smoke_test_id": "S2_leakage_guard",
        "required_before_training": "yes",
        "pass_rule": "No validation row, trial, or subject appears in training pair construction for the held-out fold.",
        "failure_action": "Stop and fix split/pair construction.",
    },
    {
        "smoke_test_id": "S3_batch_balance",
        "required_before_training": "yes",
        "pass_rule": "Each sampled batch has at least two subjects per class when possible and no subject dominates more than 35%.",
        "failure_action": "Adjust batch sampler before training.",
    },
    {
        "smoke_test_id": "S4_rating_distance_audit",
        "required_before_training": "yes_for_distance_guarded_candidates",
        "pass_rule": "Negative pairs have larger subject-relative rating distance than positive pairs on average.",
        "failure_action": "Do not use distance-guarded policy until corrected.",
    },
    {
        "smoke_test_id": "S5_micro_overfit",
        "required_before_training": "yes",
        "pass_rule": "Small same-subset train/eval reaches macro_f1 >= 0.95 for CE+SupCon candidate.",
        "failure_action": "Fix loss/model plumbing.",
    },
    {
        "smoke_test_id": "S6_shuffled_label_negative_control",
        "required_before_training": "yes",
        "pass_rule": "Shuffled-label control remains near chance and below matched real-label run.",
        "failure_action": "Investigate leakage or label handling.",
    },
]
with smoke_csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(smoke_rows[0].keys()))
    writer.writeheader()
    writer.writerows(smoke_rows)

decision_rows = [
    {
        "observed_result_after_targeted_ablation": "Cross-subject-positive SupCon improves consistently across tasks/folds",
        "interpretation": "Pair definition was the primary weakness; proceed to confirmation matrix, not broad search.",
        "next_allowed_step": "targeted_confirmation_matrix_objective",
    },
    {
        "observed_result_after_targeted_ablation": "VREx-only improves while SupCon variants do not",
        "interpretation": "DG regularization helps more than contrastive pair shaping; investigate subject-domain loss and stability.",
        "next_allowed_step": "vrex_subject_generalization_confirmation_objective",
    },
    {
        "observed_result_after_targeted_ablation": "Distance-guarded pairs improve but label-only pairs do not",
        "interpretation": "Hard binary labels are noisy; continuous/ranking-aware pair definitions are needed.",
        "next_allowed_step": "rating_distance_contrastive_objective",
    },
    {
        "observed_result_after_targeted_ablation": "No candidate improves and embeddings/loss look healthy",
        "interpretation": "The current summary features/model likely lack transferable signal or task remains poorly posed.",
        "next_allowed_step": "representation_or_task_reformulation_review",
    },
    {
        "observed_result_after_targeted_ablation": "Smoke tests fail for pair coverage or leakage",
        "interpretation": "Implementation/sampler is not safe to train.",
        "next_allowed_step": "pair_sampler_fix_objective",
    },
]
with decision_csv_path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(decision_rows[0].keys()))
    writer.writeheader()
    writer.writerows(decision_rows)

objective_json = {
    "status": "objective_created",
    "created_utc": now,
    "objective": "targeted_supcon_dg_pair_sampler_objective_ablation_design",
    "review_input": str(review_json_path),
    "evidence_inputs": [
        str(failure_report_json),
        str(first_pass_report_json),
        str(design_spec_json),
    ],
    "scientific_question": "Which pair/sampler/objective design most directly tests the subject-variability hypothesis after the first SupCon/DG pass failed?",
    "authorized_scope": [
        "read existing SupCon/DG design and failure-analysis outputs",
        "produce implementation-ready targeted ablation design",
        "define positive/negative pair policies",
        "define subject-balanced batch sampler requirements",
        "define smoke tests and pass/fail interpretation",
        "define a small future ablation matrix only",
    ],
    "not_authorized": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
    ],
    "generated_outputs": {
        "markdown": str(objective_md_path),
        "json": str(objective_json_path),
        "ablation_design_matrix_csv": str(matrix_csv_path),
        "hyperparameter_registry_csv": str(hp_csv_path),
        "smoke_test_plan_csv": str(smoke_csv_path),
        "decision_tree_csv": str(decision_csv_path),
    },
    "pass_criteria": [
        "review closeout exists and blocks full training",
        "objective specifies positive/negative pair definitions",
        "objective specifies sampler and hyperparameter registry",
        "objective specifies smoke tests before any training",
        "objective defines interpretation rules for success/failure",
    ],
    "next_allowed_step": "prepare_reviewed_targeted_pair_sampler_ablation_design_report_or_run_command",
}
objective_json_path.write_text(json.dumps(objective_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

objective_md = f"""# I-DARE Targeted SupCon/DG Pair-Sampler Objective Ablation Design

## Status

Created: `{now}`

Status: objective created; no training is authorized by this document.

This objective follows:

- `docs/idare_supcon_dg_failure_analysis_report.md`
- `docs/idare_minimal_supcon_dg_first_pass_report.md`
- `docs/idare_subject_variability_supcon_dg_design_spec.md`
- `docs/idare_supcon_dg_failure_analysis_review_status.md`

## Scientific Question

The first SupCon/DG pass failed despite valid smoke tests.

The question is no longer "does SupCon/DG run?"

The question is:

**Which pair definition, negative definition, subject-balanced sampler, and domain-generalization penalty actually targets subject variability rather than adding another weak regularizer?**

## Core Hypothesis

Subject variability remains a plausible blocker, but the first intervention was likely too weak or too broad.

The most likely failure modes are:

1. Positive pairs were label-compatible but not necessarily affect-compatible.
2. Negative pairs may have pushed borderline or rating-similar samples apart.
3. Within-subject pair structure may have reinforced idiosyncratic subject patterns.
4. VREx regularized losses but may not have created subject-invariant embeddings.
5. Hyperparameters were not wrong in a generic sense; they were not tied tightly enough to the pair/sampler mechanism.

## Authorized Scope

This objective authorizes design/spec work only:

- define targeted SupCon/DG pair-sampler ablation candidates
- define positive-pair policies
- define negative-pair policies
- define batch sampler constraints
- define minimal hyperparameter registry
- define smoke tests required before any new training
- define decision rules for interpreting the next small ablation

## Not Authorized

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change

## Required Ablation Design Matrix

The implementation-ready candidate matrix is stored in:

`docs/idare_targeted_supcon_dg_pair_sampler_ablation_design_matrix.csv`

Required candidate families:

1. CE control
2. label-only SupCon
3. cross-subject-positive-only SupCon
4. within-subject anchor + cross-subject positive SupCon
5. rating-distance-guarded SupCon
6. cross-subject SupCon + VREx
7. VREx-only recheck
8. subject-adversarial design-only candidate, not first-pass training

## Positive Pair Design Rules

Candidate policies must explicitly state whether positives are:

- same binary label only
- same label and cross-subject only
- same label with rating-distance or quantile-distance guard
- within-subject stable examples plus cross-subject positives
- subject-relative top/bottom quantile aligned

A candidate is invalid if it cannot explain what "positive" means beyond matching the final binary label.

## Negative Pair Design Rules

Candidate policies must explicitly state whether negatives are:

- opposite binary label only
- opposite label plus rating-distance margin
- cross-subject only
- subject-balanced
- forbidden when rating distance is too small

A candidate is invalid if it aggressively pushes borderline affect states apart without an audit.

## Batch Sampler Design Rules

The sampler must satisfy these constraints before training:

- subject-heldout validation subjects are never used in training pairs
- batches contain multiple subjects per class when possible
- no single subject dominates a batch
- each eligible anchor has at least one positive and one negative
- pair coverage is reported by modality, task, fold, and candidate
- sampler failures block training for that candidate

## Hyperparameter Registry

The minimal hyperparameter registry is stored in:

`docs/idare_targeted_supcon_dg_pair_sampler_hyperparameter_registry.csv`

This is not a broad search. It is a constrained registry so that if a future ablation works or fails, the mechanism remains interpretable.

## Required Smoke Tests

The smoke-test plan is stored in:

`docs/idare_targeted_supcon_dg_pair_sampler_smoke_test_plan.csv`

Required tests before any future training:

1. pair coverage
2. leakage guard
3. batch balance
4. rating-distance audit
5. micro-overfit
6. shuffled-label negative control

## Failure Interpretation Decision Tree

The decision tree is stored in:

`docs/idare_targeted_supcon_dg_pair_sampler_decision_tree.csv`

The next ablation must be interpreted according to that tree. In particular:

- If cross-subject positives help, the original pair definition was weak.
- If VREx-only helps, DG regularization may matter more than SupCon.
- If distance-guarded pairs help, the binary labels are too noisy for naive supervised contrastive learning.
- If nothing helps and smoke tests are valid, representation/task formulation must be revisited.

## Pass Criteria

This objective passes only if:

- review closeout is created
- the targeted ablation matrix is written
- the pair/sampler hyperparameter registry is written
- smoke tests are defined before training
- decision rules are defined before training
- direct full SupCon/DG training remains blocked

## Next Allowed Step

Prepare a reviewed implementation/run command for the targeted pair/sampler ablation, or generate a more detailed implementation spec if the design is not yet sufficient.

No broad training is allowed before review.
"""
objective_md_path.write_text(objective_md, encoding="utf-8")

# Update current project status in a conservative, schema-preserving way.
status_json_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

status = read_json(status_json_path)
event_review = {
    "timestamp_utc": now,
    "type": "review_closeout",
    "name": "I-DARE SupCon/DG failure-analysis review",
    "status": "human review accepted failure analysis; targeted pair/sampler ablation design selected",
    "evidence": str(review_md_path),
    "next_allowed_step": "create targeted SupCon/DG pair/sampler ablation design",
    "blocked": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
    ],
}
event_objective = {
    "timestamp_utc": now,
    "type": "objective_created",
    "name": "I-DARE targeted SupCon/DG pair-sampler objective ablation design",
    "status": "short-term design objective created; no training authorized",
    "evidence": str(objective_md_path),
    "next_allowed_step": "prepare reviewed targeted pair/sampler ablation implementation command",
    "blocked": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
    ],
}

status["last_updated_utc"] = now
status.setdefault("idare_protocol_events", [])
status["idare_protocol_events"].extend([event_review, event_objective])
status["current_idare_next_allowed_step"] = "prepare_reviewed_targeted_pair_sampler_ablation_design_report_or_run_command"
status["current_idare_blocked_steps"] = event_objective["blocked"]
status_json_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE SupCon/DG Failure-analysis Review and Targeted Pair/Sampler Objective

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE SupCon/DG failure-analysis review | human review accepted first-pass failure analysis; targeted pair/sampler design selected | `docs/idare_supcon_dg_failure_analysis_review_status.md` | Create/use targeted SupCon/DG pair/sampler ablation design. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE targeted SupCon/DG pair-sampler objective ablation design | short-term design objective created; no training authorized | `docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md` | Prepare reviewed targeted pair/sampler ablation implementation command. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- A targeted SupCon/DG pair/sampler ablation design objective is defined in `docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md`.
- The first-pass failure is interpreted as evidence that the pair/sampler/objective design needs targeted ablation before any full SupCon/DG training.
"""
if "I-DARE SupCon/DG Failure-analysis Review and Targeted Pair/Sampler Objective" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")
else:
    status_md_path.write_text(status_md, encoding="utf-8")

print("OK_TARGETED_SUPCON_DG_PAIR_SAMPLER_OBJECTIVE_WRITTEN")
print(review_md_path)
print(review_json_path)
print(objective_md_path)
print(objective_json_path)
print(matrix_csv_path)
print(hp_csv_path)
print(smoke_csv_path)
print(decision_csv_path)
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path

paths_json = [
    Path("docs/idare_supcon_dg_failure_analysis_review_status.json"),
    Path("docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.json"),
    Path("docs/project_status_current.json"),
]
for p in paths_json:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

csv_expectations = {
    "docs/idare_targeted_supcon_dg_pair_sampler_ablation_design_matrix.csv": 8,
    "docs/idare_targeted_supcon_dg_pair_sampler_hyperparameter_registry.csv": 8,
    "docs/idare_targeted_supcon_dg_pair_sampler_smoke_test_plan.csv": 6,
    "docs/idare_targeted_supcon_dg_pair_sampler_decision_tree.csv": 5,
}
for path, min_rows in csv_expectations.items():
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(Path(path).name, "rows=", len(rows))
    if len(rows) < min_rows:
        raise SystemExit(f"ERROR: {path} expected at least {min_rows} rows, got {len(rows)}")

required_terms = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "Positive Pair Design Rules",
    "Negative Pair Design Rules",
    "Batch Sampler Design Rules",
    "Required Smoke Tests",
]
text = Path("docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md").read_text(encoding="utf-8")
for term in required_terms:
    if term not in text:
        raise SystemExit(f"ERROR: missing term in objective md: {term}")
print("ALL_TARGETED_SUPCON_DG_PAIR_SAMPLER_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "Status|Scientific Question|Positive Pair|Negative Pair|Batch Sampler|Required Smoke Tests|Pass Criteria|Next Allowed Step" \
  docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md
grep -nE "SupCon/DG failure-analysis review|targeted SupCon/DG pair-sampler" docs/project_status_current.md | tail -n 20
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_supcon_dg_failure_analysis_review_status.md \
  docs/idare_supcon_dg_failure_analysis_review_status.json \
  docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md \
  docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.json \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_design_matrix.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_hyperparameter_registry.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_smoke_test_plan.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_decision_tree.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE targeted SupCon DG pair sampler objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_targeted_supcon_dg_pair_sampler_objective.log"
