#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start intervention-failure review + SupCon/DG design objective ====="
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

echo "===== 3) create review closeout + SupCon/DG design objective ====="
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
    },
    "scientific_rationale": {
        "why_supcon_dg_design_next": [
            "SupCon and domain generalization directly target cross-subject representation alignment.",
            "The failed preprocessing/CE-only intervention did not explicitly align same-affect samples across subjects.",
            "The project already contains planned SupCon ideas, but implementation details must be audited before training.",
        ],
        "must_lock_before_training": [
            "positive-pair definition",
            "negative-pair and hard-negative definition",
            "subject/environment definition",
            "batch sampler constraints",
            "loss weights and schedule",
            "leakage controls",
            "first-pass run matrix",
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

## Next Selected Step

Create a SupCon / domain-generalization design objective:

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
    "objective_name": "I-DARE subject-variability SupCon/DG design",
    "objective_type": "read_only_design_and_implementation_spec",
    "parent_review": str(REVIEW_MD),
    "parent_review_json": str(REVIEW_JSON),
    "primary_evidence": {
        "intervention_failure_report": str(REPORT_MD),
        "intervention_failure_json": str(REPORT_JSON),
        "decision_matrix": str(DECISION_CSV),
        "fold_task_summary": str(FOLD_CSV),
    },
    "scientific_question": "How should SupCon and/or domain-generalization losses be designed so the next controlled run directly targets subject variability rather than generic feature improvement?",
    "authorized_scope": [
        "Read project docs and scripts to recover existing SupCon/DG design notes.",
        "Create an implementation-ready design spec.",
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
        "leakage controls",
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
            "area": "evaluation",
            "required_decision": "Keep first pass minimal and diagnostic; specify run count and pass/fail criteria.",
        },
        {
            "area": "leakage controls",
            "required_decision": "All preprocessing/scaling and sampler construction must be train-fold-only where relevant.",
        },
    ],
    "expected_outputs": [
        "docs/idare_subject_variability_supcon_dg_design_spec.md",
        "docs/idare_subject_variability_supcon_dg_design_spec.json",
        "docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv",
        "docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv",
    ],
    "pass_criteria": [
        "Spec must cite and summarize existing project SupCon/DG design notes found in docs/scripts.",
        "Spec must state exactly whether SupCon, VREx/DG, or both are selected for first pass.",
        "Spec must define positive/negative/hard-negative pairs.",
        "Spec must define subject-aware sampler requirements.",
        "Spec must define leakage controls.",
        "Spec must provide a minimal first-pass run matrix.",
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
    "next_allowed_step": "Search/read existing project docs and scripts, then generate the SupCon/DG design spec.",
}
NEXT_OBJECTIVE_JSON.write_text(json.dumps(next_objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

next_objective_md = f"""# I-DARE Subject-variability SupCon/DG Design Objective

## Status

Short-term design objective created.

No SupCon/DG training is authorized by this document.

Generated UTC: `{NOW}`

## Why This Objective Exists

The subject-variability intervention-failure analysis concluded:

- `{diagnosis}`

The failed subject-relative + preprocessing intervention was judged too weak/incomplete, not proof that subject variability is irrelevant.

The next method must directly target subject variability.

SupCon and domain generalization are plausible because they can directly target cross-subject representation mismatch, but only if the design is precise.

## Scientific Question

How should SupCon and/or domain-generalization losses be designed so the next controlled run directly targets subject variability rather than generic feature improvement?

## Authorized Work

Read-only design/spec work.

This objective authorizes:

1. Searching project docs and scripts for existing SupCon/DG notes.
2. Summarizing the intended implementation.
3. Locking positive-pair, negative-pair, and hard-negative definitions.
4. Locking subject-aware sampler requirements.
5. Locking VREx/domain environment definitions.
6. Creating a minimal first-pass run matrix.

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

### 7. Leakage controls

All preprocessing/scaling and sampler construction must respect train/validation separation.

## Expected Outputs

- `docs/idare_subject_variability_supcon_dg_design_spec.md`
- `docs/idare_subject_variability_supcon_dg_design_spec.json`
- `docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv`
- `docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv`

## Pass Criteria

The design passes only if it:

1. Reviews existing project SupCon/DG notes.
2. Defines positive/negative/hard-negative pairs.
3. Defines subject-aware sampler constraints.
4. Defines VREx/DG environment rules.
5. Defines minimal first-pass run matrix.
6. Avoids training and performance claims.
7. Updates the central roadmap.

## Not Authorized

- SupCon/DG training
- EEG+EMG fusion
- final LOSO / final paper claim
- mainline change
- architecture/augmentation work
- broad hyperparameter search

## Next Allowed Step

Search/read existing project docs and scripts, then generate the SupCon/DG design spec.
"""
NEXT_OBJECTIVE_MD.write_text(next_objective_md, encoding="utf-8")

project_md = PROJECT_MD.read_text(encoding="utf-8")
rows = [
    "| I-DARE subject-variability intervention-failure analysis review | human review accepted intervention-failure report; SupCon/DG design selected next | yes | `docs/idare_subject_variability_intervention_failure_analysis_review_status.md` | Create/run SupCon/DG design objective. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training; feature-engineering training; mainline change. |",
    "| I-DARE subject-variability SupCon/DG design objective | short-term design objective created; no training authorized | yes | `docs/idare_subject_variability_supcon_dg_design_objective.md` | Search/read project docs and generate implementation-ready design spec. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training before spec review; mainline change. |",
]
if "I-DARE subject-variability SupCon/DG design objective" not in project_md:
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
    "- Human review of the intervention-failure analysis is frozen in `docs/idare_subject_variability_intervention_failure_analysis_review_status.md`; SupCon/DG design is selected next, but training is not authorized.",
    "- A subject-variability SupCon/DG design objective is defined in `docs/idare_subject_variability_supcon_dg_design_objective.md`; next work is to read existing project SupCon/DG notes and create an implementation-ready design spec.",
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
}
decisions["idare_subject_variability_supcon_dg_design_objective"] = {
    "status": "short_term_design_objective_created",
    "evidence": str(NEXT_OBJECTIVE_MD),
    "evidence_json": str(NEXT_OBJECTIVE_JSON),
    "objective_type": "read_only_design_and_implementation_spec",
    "scientific_question": next_objective["scientific_question"],
    "expected_outputs": next_objective["expected_outputs"],
    "not_authorized": next_objective["not_authorized"],
    "next_allowed_step": next_objective["next_allowed_step"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_SUPCON_DG_DESIGN_OBJECTIVE_WRITTEN")
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
required_terms = ["positive", "negative", "sampler", "VREx", "SupCon"]
missing = [t for t in required_terms if t not in text]
if missing:
    raise SystemExit(f"ERROR: missing required design terms: {missing}")
if obj.get("status") != "short_term_design_objective_created":
    raise SystemExit("ERROR: wrong objective status")
PY

grep -n "## Status\|## Review Decision\|## Next Selected Step" docs/idare_subject_variability_intervention_failure_analysis_review_status.md
grep -n "## Status\|## Scientific Question\|## Design Decisions to Lock\|## Pass Criteria\|## Next Allowed Step" docs/idare_subject_variability_supcon_dg_design_objective.md
grep -n "SupCon/DG design\|intervention-failure analysis review" docs/project_status_current.md
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

git commit -m "docs: add I-DARE SupCon DG design objective"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_supcon_dg_design_objective.log"
