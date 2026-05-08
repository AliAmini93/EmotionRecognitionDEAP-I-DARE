#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start intervention-failure review + cautious SupCon/DG design objective ====="
date
git status --short --branch
echo

echo "===== 1) choose python and require clean repo ====="
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
print("OK_IMPORTS")
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repository is not clean. Commit/stash changes before creating this objective." >&2
  git status --short --branch >&2
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required evidence docs ====="
ls -lh \
  docs/idare_subject_variability_intervention_failure_analysis_report.md \
  docs/idare_subject_variability_intervention_failure_analysis_report.json \
  docs/idare_subject_variability_intervention_failure_decision_matrix.csv \
  docs/idare_subject_variability_intervention_failure_fold_task_summary.csv \
  docs/idare_subject_variability_intervention_failure_analysis_objective.md \
  docs/idare_subject_variability_intervention_failure_analysis_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 3) create review closeout + cautious SupCon/DG design objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

REPORT_MD = DOCS / "idare_subject_variability_intervention_failure_analysis_report.md"
REPORT_JSON = DOCS / "idare_subject_variability_intervention_failure_analysis_report.json"
DECISION_CSV = DOCS / "idare_subject_variability_intervention_failure_decision_matrix.csv"
FOLD_CSV = DOCS / "idare_subject_variability_intervention_failure_fold_task_summary.csv"
OBJECTIVE_PREV_MD = DOCS / "idare_subject_variability_intervention_failure_analysis_objective.md"
OBJECTIVE_PREV_JSON = DOCS / "idare_subject_variability_intervention_failure_analysis_objective.json"

REVIEW_MD = DOCS / "idare_subject_variability_intervention_failure_analysis_review_status.md"
REVIEW_JSON = DOCS / "idare_subject_variability_intervention_failure_analysis_review_status.json"
NEXT_OBJECTIVE_MD = DOCS / "idare_subject_variability_supcon_dg_design_objective.md"
NEXT_OBJECTIVE_JSON = DOCS / "idare_subject_variability_supcon_dg_design_objective.json"

PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

required = [
    REPORT_MD, REPORT_JSON, DECISION_CSV, FOLD_CSV,
    OBJECTIVE_PREV_MD, OBJECTIVE_PREV_JSON,
    PROJECT_MD, PROJECT_JSON,
]
for p in required:
    if not p.exists():
        raise SystemExit(f"ERROR: required file missing: {p}")

report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
diagnosis = report.get("diagnosis", "subject_variability_diagnosis_still_supported_intervention_too_weak")
recommended = report.get("recommended_next_objective", "subject_variability_supcon_dg_design_objective")
interpretation = report.get("interpretation", {})
overall = report.get("overall_preprocessed_subject_relative", {})

review = {
    "status": "frozen_human_review_closeout",
    "created_or_updated_utc": NOW,
    "reviewed_document": str(REPORT_MD),
    "reviewed_json": str(REPORT_JSON),
    "review_decision": {
        "accepted": True,
        "mainline_changed": False,
        "diagnosis": diagnosis,
        "accepted_interpretation": "Subject variability remains a leading blocker; the failed intervention is interpreted as too weak/incomplete, not as falsification of the diagnosis.",
        "selected_next_step": str(NEXT_OBJECTIVE_MD),
        "direct_training_authorized": False,
        "caution_required": True,
    },
    "scientific_rationale": {
        "why_supcon_dg_design_next": [
            "SupCon and domain generalization directly target cross-subject representation alignment.",
            "The failed preprocessing/CE-only intervention did not explicitly align same-affect samples across subjects.",
            "The project already contains planned SupCon ideas, but implementation details and assumptions must be audited before training.",
            "Hyperparameters and smoke tests must be planned before any performance run, otherwise improvements/failures will not be diagnosable.",
        ],
        "must_lock_before_training": [
            "positive-pair definition",
            "negative-pair and hard-negative definition",
            "subject/environment definition",
            "batch sampler constraints",
            "loss weights and schedule",
            "temperature and projection-head hyperparameters",
            "smoke tests and acceptance gates",
            "leakage controls",
            "diagnostic decision tree for success/failure interpretation",
            "minimal first-pass run matrix",
        ],
    },
    "frozen_constraints": {
        "not_authorized_until_design_review": [
            "SupCon/DG training",
            "EEG+EMG fusion",
            "final LOSO claim",
            "mainline change",
            "broad hyperparameter search",
            "architecture/augmentation work",
        ]
    },
    "source_evidence": {
        "intervention_failure_report": str(REPORT_MD),
        "decision_matrix": str(DECISION_CSV),
        "fold_task_summary": str(FOLD_CSV),
    },
}
REVIEW_JSON.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

review_md = f"""# I-DARE Subject-variability Intervention-failure Analysis Review Status

## Status

Frozen human-review closeout.

Generated UTC: `{NOW}`

## Reviewed Evidence

- Report: `{REPORT_MD}`
- JSON: `{REPORT_JSON}`
- Decision matrix: `{DECISION_CSV}`
- Fold/task summary: `{FOLD_CSV}`

## Review Decision

Accepted.

The intervention-failure analysis conclusion is accepted:

- `{diagnosis}`

Mainline is unchanged.

Direct SupCon/DG training is not authorized yet.

## Scientific Interpretation

The failed subject-relative + preprocessing intervention does not falsify the subject-variability diagnosis.

It shows that the tested intervention was too weak/incomplete because:

- it relied on preprocessing and CE-only training;
- it did not explicitly align same-affect samples across subjects;
- it did not explicitly penalize subject/environment risk instability;
- it did not lock a positive/negative pair strategy or subject-aware sampler.

## Caution Requirement

The next step must stay diagnostic and staged.

Before any SupCon/DG training, the project must lock:

- explicit assumptions;
- positive/negative/hard-negative pair definitions;
- sampler validity tests;
- hyperparameter candidates and isolation rules;
- smoke tests;
- failure interpretation rules.

## Next Selected Step

Create a cautious SupCon / domain-generalization design objective:

- `{NEXT_OBJECTIVE_MD}`

This is a design/spec step, not a training step.

## Not Authorized

- SupCon/DG training
- EEG+EMG fusion
- final LOSO / final paper claim
- mainline change
- architecture/augmentation work
- broad hyperparameter search
"""
REVIEW_MD.write_text(review_md, encoding="utf-8")

next_objective = {
    "status": "short_term_design_objective_created",
    "created_or_updated_utc": NOW,
    "objective_name": "I-DARE cautious subject-variability SupCon/DG design",
    "objective_type": "read_only_design_and_implementation_spec",
    "parent_review": str(REVIEW_MD),
    "parent_review_json": str(REVIEW_JSON),
    "primary_evidence": {
        "intervention_failure_report": str(REPORT_MD),
        "intervention_failure_json": str(REPORT_JSON),
        "decision_matrix": str(DECISION_CSV),
        "fold_task_summary": str(FOLD_CSV),
    },
    "scientific_question": "How should SupCon and/or domain-generalization losses be designed, staged, smoke-tested, and interpreted so the next controlled run directly targets subject variability and remains scientifically diagnosable?",
    "authorized_scope": [
        "Read project docs and scripts to recover existing SupCon/DG design notes.",
        "Create an implementation-ready design spec.",
        "Define smoke tests before any performance run.",
        "Define a small controlled hyperparameter plan, not a broad search.",
        "Define decision logic for interpreting success/failure.",
        "No new model training.",
        "No performance claim.",
        "No mainline change.",
    ],
    "must_review_existing_project_docs_for": [
        "SupCon implementation plan",
        "positive-pair definition",
        "negative-pair definition",
        "hard-negative definition",
        "subject-aware batch sampler",
        "domain generalization / VREx references",
        "loss weighting and scheduling",
        "temperature and projection-head settings",
        "leakage controls",
        "existing smoke-test conventions",
    ],
    "design_decisions_to_lock": [
        {
            "area": "task formulation",
            "required_decision": "Use subject-relative q33 labels initially or justify another label policy.",
        },
        {
            "area": "positive pairs",
            "required_decision": "Define same-task/same-class positives, with cross-subject positives required when feasible.",
        },
        {
            "area": "negative pairs",
            "required_decision": "Define opposite-class negatives and hard negatives, including same-stimulus/different-label cases if available.",
        },
        {
            "area": "sampler",
            "required_decision": "Guarantee each contrastive batch contains enough subjects and class diversity for valid positives/negatives.",
        },
        {
            "area": "domain generalization",
            "required_decision": "Define subject as environment for VREx/DG or justify a coarser fold/task environment.",
        },
        {
            "area": "loss",
            "required_decision": "Choose CE+SupCon, CE+VREx, or CE+SupCon+VREx first-pass; specify weights and warmup.",
        },
        {
            "area": "hyperparameters",
            "required_decision": "Define candidate ranges for temperature, SupCon weight, VREx weight, projection dimension, batch size, warmup, and optimizer/lr; specify which are smoke-only versus first-pass ablations.",
        },
        {
            "area": "smoke tests",
            "required_decision": "Define sampler integrity, leakage guard, micro-overfit, shuffled-label negative control, and minimal fold/task smoke gates.",
        },
        {
            "area": "evaluation",
            "required_decision": "Keep first pass minimal and diagnostic; specify run count, metrics, and pass/fail criteria.",
        },
        {
            "area": "leakage controls",
            "required_decision": "All preprocessing/scaling and sampler construction must respect train/validation separation.",
        },
        {
            "area": "decision tree",
            "required_decision": "Define what to conclude if smoke fails, if embeddings align but macro-F1 does not improve, or if VREx reduces risk variance without performance gain.",
        },
    ],
    "preliminary_hyperparameter_registry_to_refine": {
        "supcon_temperature_tau": [0.07, 0.1, 0.2],
        "lambda_supcon": [0.05, 0.1, 0.2, 0.5],
        "lambda_vrex": [0.01, 0.05, 0.1],
        "projection_dim": [32, 64, 128],
        "warmup_epochs": [0, 3, 5],
        "batch_size_policy": ["largest_valid_subject_class_balanced_batch", "fixed_64_if_valid", "fixed_128_if_valid"],
        "optimizer_policy": ["reuse_current_mainline_first", "only_change_if_smoke_fails_due_to_optimization"],
        "grid_policy": "Do not run full Cartesian grid in first pass; choose a small staged matrix after smoke tests.",
    },
    "required_smoke_tests": [
        {
            "name": "pair_sampler_integrity_smoke",
            "purpose": "Verify every contrastive batch has valid positives/negatives and enough subjects/classes.",
            "failure_interpretation": "Sampler/design issue; do not train.",
        },
        {
            "name": "leakage_guard_smoke",
            "purpose": "Verify preprocessing/scaling and pair selection do not use validation labels/features improperly.",
            "failure_interpretation": "Protocol invalid; do not train.",
        },
        {
            "name": "supcon_micro_overfit_smoke",
            "purpose": "Verify CE+SupCon can overfit a tiny train-only subset and loss decreases.",
            "failure_interpretation": "Implementation/optimization bug.",
        },
        {
            "name": "shuffled_label_negative_control",
            "purpose": "Verify contrastive setup does not produce meaningful performance on shuffled labels.",
            "failure_interpretation": "Leakage or invalid metric interpretation.",
        },
        {
            "name": "one_fold_one_task_minimal_smoke",
            "purpose": "Run one task/fold/config only after integrity tests pass.",
            "failure_interpretation": "Use embedding diagnostics to decide if loss, sampler, or task signal is failing.",
        },
    ],
    "diagnostic_metrics_to_log": [
        "macro_f1",
        "balanced_accuracy",
        "accuracy",
        "one_class_pred",
        "environment_risk_variance",
        "within_subject_vs_cross_subject_embedding_distance",
        "same_class_cross_subject_distance",
        "different_class_cross_subject_distance",
        "positive_pair_coverage",
        "anchors_without_positive_count",
        "batch_subject_count_distribution",
        "loss_ce",
        "loss_supcon",
        "loss_vrex",
    ],
    "expected_outputs": [
        "docs/idare_subject_variability_supcon_dg_design_spec.md",
        "docs/idare_subject_variability_supcon_dg_design_spec.json",
        "docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv",
        "docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv",
        "docs/idare_subject_variability_supcon_dg_smoke_test_plan.csv",
        "docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv",
    ],
    "pass_criteria": [
        "Spec must cite and summarize existing project SupCon/DG design notes found in docs/scripts.",
        "Spec must state exactly whether SupCon, VREx/DG, or both are selected for first pass.",
        "Spec must define positive/negative/hard-negative pairs.",
        "Spec must define subject-aware sampler constraints.",
        "Spec must define smoke tests before training.",
        "Spec must define a small staged hyperparameter plan, not a broad search.",
        "Spec must define VREx/DG environment rules.",
        "Spec must define leakage controls.",
        "Spec must provide a minimal first-pass run matrix.",
        "Spec must include failure-interpretation logic.",
        "Spec must update docs/project_status_current.md and docs/project_status_current.json.",
    ],
    "not_authorized": [
        "Training SupCon/DG models",
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "mainline change",
        "architecture/augmentation work",
        "broad hyperparameter search",
    ],
    "next_allowed_step": "Search/read existing project docs and scripts, then generate the cautious SupCon/DG design spec with smoke tests and hyperparameter registry.",
}
NEXT_OBJECTIVE_JSON.write_text(json.dumps(next_objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

next_objective_md = f"""# I-DARE Cautious Subject-variability SupCon/DG Design Objective

## Status

Short-term design objective created.

No SupCon/DG training is authorized by this document.

Generated UTC: `{NOW}`

## Why This Objective Exists

The subject-variability intervention-failure analysis concluded:

- `{diagnosis}`

The failed subject-relative + preprocessing intervention was judged too weak/incomplete, not proof that subject variability is irrelevant.

The next method must directly target subject variability.

SupCon and domain generalization are plausible because they can directly target cross-subject representation mismatch, but only if the design is precise and staged.

## Scientific Question

How should SupCon and/or domain-generalization losses be designed, staged, smoke-tested, and interpreted so the next controlled run directly targets subject variability and remains scientifically diagnosable?

## Core Principle

Do not jump directly to a performance run.

First lock:

- assumptions;
- pair definitions;
- sampler guarantees;
- smoke tests;
- hyperparameter registry;
- staged run matrix;
- failure interpretation rules.

## Authorized Work

Read-only design/spec work.

This objective authorizes:

1. Searching project docs and scripts for existing SupCon/DG notes.
2. Summarizing the intended implementation.
3. Locking positive-pair, negative-pair, and hard-negative definitions.
4. Locking subject-aware sampler requirements.
5. Locking VREx/domain environment definitions.
6. Creating smoke-test gates.
7. Creating a small staged hyperparameter registry.
8. Creating a minimal first-pass run matrix.

No new model training is authorized.

## Design Decisions to Lock

### 1. Task formulation

Decide whether the first pass should use subject-relative q33 labels, and justify the choice.

### 2. Positive pairs

Define valid positives.

Minimum expected principle:

- same task
- same class
- cross-subject preferred/required when feasible

### 3. Negative pairs

Define valid negatives.

Minimum expected principle:

- same task
- opposite class
- hard negatives should be considered if same-stimulus/different-label or same-subject/opposite-class cases are available.

### 4. Sampler

Define a sampler that makes SupCon batches valid.

It should specify:

- minimum subjects per batch
- minimum samples per class
- whether each anchor must have at least one positive
- fallback behavior when a fold/task lacks enough positives
- logging for anchors without positives
- batch subject/class distribution diagnostics

### 5. Domain generalization

Define environment.

Expected default:

- subject ID as domain/environment

Alternative definitions must be justified.

### 6. Loss and schedule

Choose one first-pass setup:

- CE + SupCon
- CE + VREx/DG
- CE + SupCon + VREx/DG

Specify weights, warmup, and when each loss is active.

### 7. Hyperparameter registry

Define candidate values before any run.

Initial registry to refine:

- SupCon temperature tau: `0.07`, `0.1`, `0.2`
- SupCon weight: `0.05`, `0.1`, `0.2`, `0.5`
- VREx/DG weight: `0.01`, `0.05`, `0.1`
- projection dimension: `32`, `64`, `128`
- warmup epochs: `0`, `3`, `5`
- batch policy: largest valid subject/class-balanced batch first

The first pass must not be a full Cartesian grid.

### 8. Smoke tests

Before any full training run, define and require:

1. pair sampler integrity smoke;
2. leakage guard smoke;
3. SupCon micro-overfit smoke;
4. shuffled-label negative control;
5. one-fold/one-task minimal smoke.

### 9. Evaluation

Keep first pass minimal and diagnostic.

Metrics must include:

- macro-F1
- balanced accuracy
- one-class prediction flag
- environment risk variance
- same-class cross-subject embedding distance
- different-class cross-subject embedding distance
- positive-pair coverage
- anchors without positives
- CE/SupCon/VREx loss components

### 10. Failure interpretation

The design spec must explain what to conclude if:

- smoke tests fail;
- SupCon loss decreases but validation macro-F1 does not improve;
- embeddings align but task performance remains near chance;
- VREx reduces risk variance but not performance;
- only one modality/task improves;
- improvement appears only under one temperature/loss-weight combination.

## Expected Outputs

- `docs/idare_subject_variability_supcon_dg_design_spec.md`
- `docs/idare_subject_variability_supcon_dg_design_spec.json`
- `docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv`
- `docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv`
- `docs/idare_subject_variability_supcon_dg_smoke_test_plan.csv`
- `docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv`

## Pass Criteria

The design passes only if it:

1. Reviews existing project SupCon/DG notes.
2. Defines positive/negative/hard-negative pairs.
3. Defines subject-aware sampler constraints.
4. Defines smoke tests before training.
5. Defines a small staged hyperparameter plan.
6. Defines VREx/DG environment rules.
7. Defines leakage controls.
8. Defines minimal first-pass run matrix.
9. Includes failure-interpretation logic.
10. Avoids training and performance claims.
11. Updates the central roadmap.

## Not Authorized

- SupCon/DG training
- EEG+EMG fusion
- final LOSO / final paper claim
- mainline change
- architecture/augmentation work
- broad hyperparameter search

## Next Allowed Step

Search/read existing project docs and scripts, then generate the cautious SupCon/DG design spec with smoke tests and hyperparameter registry.
"""
NEXT_OBJECTIVE_MD.write_text(next_objective_md, encoding="utf-8")

project_md = PROJECT_MD.read_text(encoding="utf-8")
rows = [
    "| I-DARE subject-variability intervention-failure analysis review | human review accepted intervention-failure report; cautious SupCon/DG design selected next | yes | `docs/idare_subject_variability_intervention_failure_analysis_review_status.md` | Create/run cautious SupCon/DG design objective. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training; feature-engineering training; mainline change. |",
    "| I-DARE cautious subject-variability SupCon/DG design objective | short-term design objective created; smoke tests and hyperparameter registry required; no training authorized | yes | `docs/idare_subject_variability_supcon_dg_design_objective.md` | Search/read project docs and generate implementation-ready design spec. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training before spec review; broad hyperparameter search; mainline change. |",
]
if "I-DARE cautious subject-variability SupCon/DG design objective" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE subject-variability intervention-failure analysis report |"):
            out.extend(rows)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not find intervention-failure report row in project_status_current.md")
    project_md = "\n".join(out) + "\n"

bullets = [
    "- Human review of the intervention-failure analysis is frozen in `docs/idare_subject_variability_intervention_failure_analysis_review_status.md`; cautious SupCon/DG design is selected next, but training is not authorized.",
    "- A cautious subject-variability SupCon/DG design objective is defined in `docs/idare_subject_variability_supcon_dg_design_objective.md`; next work is to read existing project SupCon/DG notes and create an implementation-ready design spec with smoke tests and a staged hyperparameter registry.",
]
for bullet in bullets:
    if bullet not in project_md:
        marker = "\n## Documentation Gap Closed by This File"
        if marker not in project_md:
            raise SystemExit("ERROR: marker not found in project_status_current.md")
        project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_subject_variability_intervention_failure_analysis_review"] = {
    "status": "frozen_human_review_closeout",
    "evidence": str(REVIEW_MD),
    "evidence_json": str(REVIEW_JSON),
    "reviewed_report": str(REPORT_MD),
    "accepted_diagnosis": diagnosis,
    "selected_next_step": str(NEXT_OBJECTIVE_MD),
    "mainline_changed": False,
    "direct_training_authorized": False,
    "caution_required": True,
}
decisions["idare_subject_variability_supcon_dg_design_objective"] = {
    "status": "short_term_design_objective_created",
    "evidence": str(NEXT_OBJECTIVE_MD),
    "evidence_json": str(NEXT_OBJECTIVE_JSON),
    "objective_type": "read_only_design_and_implementation_spec",
    "scientific_question": next_objective["scientific_question"],
    "required_smoke_tests": next_objective["required_smoke_tests"],
    "preliminary_hyperparameter_registry_to_refine": next_objective["preliminary_hyperparameter_registry_to_refine"],
    "expected_outputs": next_objective["expected_outputs"],
    "not_authorized": next_objective["not_authorized"],
    "next_allowed_step": next_objective["next_allowed_step"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_CAUTIOUS_SUPCON_DG_DESIGN_OBJECTIVE_WRITTEN")
print(REVIEW_MD)
print(REVIEW_JSON)
print(NEXT_OBJECTIVE_MD)
print(NEXT_OBJECTIVE_JSON)
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path

paths = [
    Path("docs/idare_subject_variability_intervention_failure_analysis_review_status.json"),
    Path("docs/idare_subject_variability_supcon_dg_design_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

obj = json.loads(Path("docs/idare_subject_variability_supcon_dg_design_objective.json").read_text(encoding="utf-8"))
text = json.dumps(obj)
required_terms = ["positive", "negative", "sampler", "VREx", "SupCon", "smoke", "hyperparameter", "temperature"]
missing = [t for t in required_terms if t not in text]
if missing:
    raise SystemExit(f"ERROR: missing required design terms: {missing}")
if obj.get("status") != "short_term_design_objective_created":
    raise SystemExit("ERROR: wrong objective status")
if not obj.get("required_smoke_tests"):
    raise SystemExit("ERROR: smoke tests missing")
if not obj.get("preliminary_hyperparameter_registry_to_refine"):
    raise SystemExit("ERROR: hyperparameter registry missing")
PY

grep -n "## Status\|## Review Decision\|## Caution Requirement\|## Next Selected Step" docs/idare_subject_variability_intervention_failure_analysis_review_status.md
grep -n "## Status\|## Scientific Question\|## Core Principle\|## Design Decisions to Lock\|## Pass Criteria\|## Next Allowed Step" docs/idare_subject_variability_supcon_dg_design_objective.md
grep -n "cautious SupCon/DG design\|intervention-failure analysis review\|hyperparameter registry" docs/project_status_current.md
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_subject_variability_intervention_failure_analysis_review_status.md \
  docs/idare_subject_variability_intervention_failure_analysis_review_status.json \
  docs/idare_subject_variability_supcon_dg_design_objective.md \
  docs/idare_subject_variability_supcon_dg_design_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add cautious I-DARE SupCon DG design objective"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_cautious_supcon_dg_design_objective.log"
