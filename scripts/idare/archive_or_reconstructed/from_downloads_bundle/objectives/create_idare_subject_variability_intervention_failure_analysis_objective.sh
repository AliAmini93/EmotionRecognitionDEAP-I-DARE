#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start preprocessed-training review + intervention-failure objective ====="
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
  docs/idare_subject_relative_preprocessed_minimal_training_report.md \
  docs/idare_subject_relative_preprocessed_minimal_training_report.json \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.json \
  docs/idare_subject_relative_representation_preprocessing_report.md \
  docs/idare_subject_relative_representation_preprocessing_report.json \
  docs/idare_root_cause_diagnostic_report.md \
  docs/idare_diagnostic_sanity_tests_report.md \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 3) create review closeout + subject-variability intervention-failure objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

PREP_REPORT_MD = DOCS / "idare_subject_relative_preprocessed_minimal_training_report.md"
PREP_REPORT_JSON = DOCS / "idare_subject_relative_preprocessed_minimal_training_report.json"
PREP_EEG_JSON = DOCS / "idare_subject_relative_preprocessed_minimal_eeg_primary.json"
PREP_EMG_JSON = DOCS / "idare_subject_relative_preprocessed_minimal_emg_primary.json"
PREPROCESS_DIAG_MD = DOCS / "idare_subject_relative_representation_preprocessing_report.md"
PREPROCESS_DIAG_JSON = DOCS / "idare_subject_relative_representation_preprocessing_report.json"
ROOT_CAUSE_MD = DOCS / "idare_root_cause_diagnostic_report.md"
SANITY_MD = DOCS / "idare_diagnostic_sanity_tests_report.md"

REVIEW_MD = DOCS / "idare_subject_relative_preprocessed_minimal_training_review_status.md"
REVIEW_JSON = DOCS / "idare_subject_relative_preprocessed_minimal_training_review_status.json"
OBJECTIVE_MD = DOCS / "idare_subject_variability_intervention_failure_analysis_objective.md"
OBJECTIVE_JSON = DOCS / "idare_subject_variability_intervention_failure_analysis_objective.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

required = [
    PREP_REPORT_MD, PREP_REPORT_JSON, PREP_EEG_JSON, PREP_EMG_JSON,
    PREPROCESS_DIAG_MD, PREPROCESS_DIAG_JSON, ROOT_CAUSE_MD, SANITY_MD,
    PROJECT_MD, PROJECT_JSON,
]
for p in required:
    if not p.exists():
        raise SystemExit(f"ERROR: required file missing: {p}")

prep_report = json.loads(PREP_REPORT_JSON.read_text(encoding="utf-8"))
preprocess_diag = json.loads(PREPROCESS_DIAG_JSON.read_text(encoding="utf-8"))

diagnosis = prep_report.get("diagnosis", "preprocessed_subject_relative_first_pass_not_sufficient")
recommended = prep_report.get("recommended_next_objective", "subject_relative_feature_engineering_objective")
completed_runs = prep_report.get("completed_runs", 24)
mean_macro = prep_report.get("mean_macro_f1_all_modalities")
one_class_counts = prep_report.get("one_class_prediction_counts_by_modality_task", {})
preprocess_diagnosis = preprocess_diag.get("diagnosis", "preprocessing_candidate_worth_testing")
best_candidate = preprocess_diag.get("best_candidate", preprocess_diag.get("best_preprocessing_candidate", "unknown"))

review = {
    "status": "frozen_human_review_closeout",
    "created_or_updated_utc": NOW,
    "reviewed_document": str(PREP_REPORT_MD),
    "reviewed_json": str(PREP_REPORT_JSON),
    "evidence_level": "24-run minimal diagnostic training; not final LOSO performance",
    "human_review_decision": {
        "accepted": True,
        "mainline_changed": False,
        "preprocessed_subject_relative_result": diagnosis,
        "feature_engineering_objective_paused": True,
        "selected_next_step": "subject_variability_intervention_failure_analysis_objective",
        "decision": "Do not jump directly to generic feature engineering, SupCon, VREx, domain generalization, fusion, architecture changes, or broad hyperparameter search. First analyze why the subject-relative + preprocessing intervention failed.",
    },
    "rationale": {
        "why_review_needed": "If the project diagnosis is subject variability, a failed intervention must be audited before selecting the next fix.",
        "current_result": "The subject-relative preprocessed first pass remained close to chance/mixed and was not sufficient to justify a mainline change.",
        "preprocessing_result": "The preprocessing diagnostic justified a small test, but preprocessing alone did not establish a strong label-discriminative or subject-invariant representation.",
    },
    "frozen_constraints": {
        "not_authorized_until_failure_analysis_review": [
            "EEG+EMG fusion",
            "final LOSO / final paper claim",
            "mainline change",
            "generic feature engineering objective",
            "SupCon / VREx / domain generalization training",
            "architecture ablation for improvement",
            "data augmentation",
            "broad hyperparameter search",
        ],
        "allowed_next_step": str(OBJECTIVE_MD),
    },
    "source_reports": {
        "preprocessed_training_report": str(PREP_REPORT_MD),
        "preprocessing_diagnostic_report": str(PREPROCESS_DIAG_MD),
        "root_cause_diagnostic_report": str(ROOT_CAUSE_MD),
        "diagnostic_sanity_tests_report": str(SANITY_MD),
    },
}
REVIEW_JSON.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

review_md = f'''# I-DARE Subject-relative Preprocessed Minimal Training Review Status

## Status

Frozen human-review closeout.

Generated UTC: `{NOW}`

## Reviewed Evidence

- Report: `{PREP_REPORT_MD}`
- JSON: `{PREP_REPORT_JSON}`
- Evidence level: 24-run minimal diagnostic training; not final LOSO performance.

## Review Decision

Accepted.

The subject-relative preprocessed first-pass result is accepted as a failed or insufficient intervention, not as evidence that the full subject-variability diagnosis is wrong.

Current diagnosis from the report:

- `{diagnosis}`

Original recommended next objective from the report:

- `{recommended}`

Human review pauses the immediate move to generic feature engineering.

## Scientific Interpretation

The result does not prove that subject variability is not the problem.

It shows that the tested intervention was not strong enough:

- subject-relative labels
- EEG window/channel z-score summary features
- EMG signed-log1p features
- train-fold-only scaling
- CE-only first-pass training

This combination did not produce enough subject-heldout improvement to justify a mainline change.

## Review Rationale

A failed intervention should be audited before proposing another fix.

The next question is not merely:

> What else can we try?

The next question is:

> Why did this intervention fail if subject variability was the hypothesized blocker?

Possible explanations include:

1. The subject-variability diagnosis is correct, but preprocessing is too weak.
2. Subject-relative labels reduce global bias but do not create separable affective representation.
3. Subject identity remains dominant after preprocessing.
4. The tested CE-only objective does not explicitly force cross-subject affect alignment.
5. A SupCon / VREx / DG method may be justified only if the failure analysis shows the remaining blocker is specifically cross-subject representation mismatch.
6. The issue may also involve label/task formulation or low within-subject signal, in which case SupCon/DG would not be enough.

## Mainline After Review

No mainline changes.

## Next Allowed Step

Create and run the controlled subject-variability intervention-failure analysis objective:

- `{OBJECTIVE_MD}`

## Intentionally Not Authorized

- EEG+EMG fusion
- Final LOSO / final paper claim
- Mainline change
- Generic feature engineering objective
- SupCon / VREx / domain generalization training
- Architecture ablation for improvement
- Data augmentation
- Broad hyperparameter search
'''
REVIEW_MD.write_text(review_md, encoding="utf-8")

objective = {
    "status": "short_term_objective_created",
    "created_or_updated_utc": NOW,
    "objective_name": "I-DARE subject-variability intervention-failure analysis",
    "objective_type": "read_only_diagnostic_analysis",
    "parent_review": str(REVIEW_MD),
    "parent_review_json": str(REVIEW_JSON),
    "primary_evidence": {
        "preprocessed_training_report": str(PREP_REPORT_MD),
        "preprocessed_training_json": str(PREP_REPORT_JSON),
        "preprocessing_diagnostic_report": str(PREPROCESS_DIAG_MD),
        "preprocessing_diagnostic_json": str(PREPROCESS_DIAG_JSON),
        "root_cause_report": str(ROOT_CAUSE_MD),
        "sanity_tests_report": str(SANITY_MD),
    },
    "scientific_question": "Why did the subject-relative + preprocessing intervention fail, and does the failure support or weaken the hypothesis that low accuracy is primarily caused by subject variability?",
    "core_decision_tests": [
        {
            "id": "diagnosis_check",
            "question": "Does evidence still support subject variability as a leading blocker after the failed intervention?",
            "required_outputs": [
                "subject dominance / label dominance comparison before and after preprocessing when available",
                "fold and subject difficulty persistence",
                "within-subject vs subject-heldout contrast interpretation",
            ],
        },
        {
            "id": "intervention_strength_check",
            "question": "Did preprocessing reduce domain shift but fail to improve label separation?",
            "required_outputs": [
                "shift reduction vs validation separation gain",
                "per-modality interpretation",
                "whether improvement was expected to be enough for training",
            ],
        },
        {
            "id": "subject_relative_label_check",
            "question": "Did subject-relative labels create balanced labels but still fail to create separable signal?",
            "required_outputs": [
                "class balance audit",
                "retention / discarded middle-third summary",
                "fold/task metrics under subject-relative formulation",
            ],
        },
        {
            "id": "failure_localization",
            "question": "Is failure global or concentrated in specific folds, tasks, or subjects?",
            "required_outputs": [
                "per-fold macro-F1 and balanced accuracy",
                "hard subject carryover from previous diagnostics",
                "whether EEG and EMG fail differently",
            ],
        },
        {
            "id": "next_method_justification",
            "question": "Which next method directly targets the remaining failure mode?",
            "required_outputs": [
                "decision: SupCon/DG justified, feature engineering justified, task/label redesign justified, or stop",
                "evidence for or against affective SupCon across subjects",
                "evidence for or against VREx/domain generalization",
            ],
        },
    ],
    "authorized_scope": [
        "Read existing committed JSON/CSV/MD outputs only.",
        "No new performance training.",
        "No new model architecture changes.",
        "No data augmentation.",
        "No fusion.",
        "No broad hyperparameter search.",
        "Produce a report that explicitly separates diagnosis validity from intervention adequacy.",
    ],
    "expected_outputs": [
        "docs/idare_subject_variability_intervention_failure_analysis_report.md",
        "docs/idare_subject_variability_intervention_failure_analysis_report.json",
        "docs/idare_subject_variability_intervention_failure_fold_task_summary.csv",
        "docs/idare_subject_variability_intervention_failure_decision_matrix.csv",
    ],
    "pass_criteria": [
        "Report must explain why the tested intervention failed or say that current evidence is insufficient.",
        "Report must decide whether subject variability remains a leading blocker.",
        "Report must decide whether SupCon/DG is justified by the failure evidence.",
        "Report must explicitly avoid final LOSO claims and mainline changes.",
        "Report must update docs/project_status_current.md and docs/project_status_current.json.",
    ],
    "not_authorized": [
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "mainline change",
        "SupCon / VREx / domain generalization training",
        "generic feature engineering training",
        "architecture ablation for improvement",
        "data augmentation",
        "broad hyperparameter search",
    ],
    "suggested_analysis_algorithm": {
        "inputs": [
            str(PREP_REPORT_JSON),
            str(PREP_EEG_JSON),
            str(PREP_EMG_JSON),
            str(PREPROCESS_DIAG_JSON),
            "docs/idare_subject_relative_distribution_shift_summary.csv",
            "docs/idare_subject_relative_preprocessing_candidate_matrix.csv",
            "docs/idare_root_cause_subject_summary.csv",
            "docs/idare_diagnostic_sanity_tests_summary.csv",
        ],
        "outputs": [
            "failure_reason_ranking",
            "diagnosis_validity_assessment",
            "intervention_adequacy_assessment",
            "next_method_decision_matrix",
        ],
    },
    "next_allowed_step": "Prepare and run a reviewed read-only intervention-failure analysis script.",
}
OBJECTIVE_JSON.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

objective_md = f'''# I-DARE Subject-variability Intervention-failure Analysis Objective

## Status

Short-term objective created.

No new performance training is authorized by this document.

Generated UTC: `{NOW}`

## Why This Objective Exists

The minimal subject-relative preprocessed training first pass is complete, but the result was not sufficient.

Current report diagnosis:

- `{diagnosis}`

The project should not immediately jump to another fix.

Instead, it must answer why the intervention failed and whether the subject-variability diagnosis remains valid.

## Scientific Question

Why did the subject-relative + preprocessing intervention fail, and does the failure support or weaken the hypothesis that low accuracy is primarily caused by subject variability?

## Key Distinction

This objective separates two different questions:

1. Was the root-cause diagnosis wrong?
2. Or was the tested intervention too weak / incomplete for the diagnosed problem?

This distinction is required before choosing SupCon, VREx, domain generalization, feature engineering, or another task formulation.

## Authorized Scope

Read-only diagnostic analysis from existing committed outputs.

Allowed inputs include:

- `{PREP_REPORT_MD}`
- `{PREP_REPORT_JSON}`
- `{PREPROCESS_DIAG_MD}`
- `{PREPROCESS_DIAG_JSON}`
- `{ROOT_CAUSE_MD}`
- `{SANITY_MD}`
- Existing fold/task/subject/prediction summaries already committed under `docs/`

No new performance training is authorized.

## Required Analysis Questions

### 1. Diagnosis validity

Does subject variability remain a leading blocker after the failed intervention?

### 2. Intervention adequacy

Did preprocessing reduce domain shift without improving label separation enough?

### 3. Label/task formulation

Did subject-relative labels improve balance but still fail to create a separable affective task?

### 4. Failure localization

Is the failure broad or concentrated?

### 5. Next-method justification

Which next method is scientifically justified?

Candidates to evaluate:

- affective SupCon across subjects
- VREx / domain generalization
- subject-aware adaptation or calibration
- feature engineering
- further task/label redesign
- stop / handoff

The report must decide whether SupCon/DG is justified by the evidence, not merely because it exists in the project plan.

## Expected Outputs

- `docs/idare_subject_variability_intervention_failure_analysis_report.md`
- `docs/idare_subject_variability_intervention_failure_analysis_report.json`
- `docs/idare_subject_variability_intervention_failure_fold_task_summary.csv`
- `docs/idare_subject_variability_intervention_failure_decision_matrix.csv`

## Pass Criteria

The analysis passes only if it:

1. Explains the failure of the tested intervention or explicitly says evidence is insufficient.
2. Separates root-cause validity from intervention adequacy.
3. States whether subject variability remains a leading blocker.
4. States whether affective SupCon / VREx / DG is justified as a targeted next step.
5. Avoids final LOSO, fusion, architecture, augmentation, or mainline-change claims.
6. Updates the central roadmap.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- mainline change
- SupCon / VREx / domain generalization training
- generic feature engineering training
- architecture ablation for improvement
- data augmentation
- broad hyperparameter search

## Next Allowed Step

Prepare and run a reviewed read-only intervention-failure analysis script.
'''
OBJECTIVE_MD.write_text(objective_md, encoding="utf-8")

project_md = PROJECT_MD.read_text(encoding="utf-8")
rows_to_insert = [
    "| I-DARE subject-relative preprocessed minimal training review | human review accepted insufficient intervention; feature-engineering path paused | yes | `docs/idare_subject_relative_preprocessed_minimal_training_review_status.md` | Create/run subject-variability intervention-failure analysis. | EEG+EMG fusion; final LOSO claim; SupCon/DG training; feature-engineering training; mainline change. |",
    "| I-DARE subject-variability intervention-failure analysis objective | short-term read-only objective created to explain why subject-relative preprocessing failed | yes | `docs/idare_subject_variability_intervention_failure_analysis_objective.md` | Prepare reviewed read-only analysis command/script. | EEG+EMG fusion; final LOSO claim; SupCon/DG training; feature-engineering training; mainline change. |",
]
if "I-DARE subject-relative preprocessed minimal training review" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE minimal subject-relative preprocessed training report |"):
            out.extend(rows_to_insert)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not find row for preprocessed minimal training report in project_status_current.md")
    project_md = "\n".join(out) + "\n"

bullets = [
    "- Human review of the subject-relative preprocessed minimal training report is frozen in `docs/idare_subject_relative_preprocessed_minimal_training_review_status.md`; the intervention is accepted as insufficient, but this does not invalidate the subject-variability diagnosis.",
    "- A subject-variability intervention-failure analysis objective is defined in `docs/idare_subject_variability_intervention_failure_analysis_objective.md`; next work is read-only analysis explaining why the intervention failed before choosing SupCon/DG, feature engineering, or another fix.",
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
decisions["idare_subject_relative_preprocessed_minimal_training_review"] = {
    "status": "frozen_human_review_closeout",
    "evidence": str(REVIEW_MD),
    "evidence_json": str(REVIEW_JSON),
    "reviewed_report": str(PREP_REPORT_MD),
    "accepted_result": diagnosis,
    "mainline_changed": False,
    "next_step": str(OBJECTIVE_MD),
    "not_authorized": review["frozen_constraints"]["not_authorized_until_failure_analysis_review"],
}
decisions["idare_subject_variability_intervention_failure_analysis_objective"] = {
    "status": "short_term_objective_created",
    "evidence": str(OBJECTIVE_MD),
    "evidence_json": str(OBJECTIVE_JSON),
    "objective_type": "read_only_diagnostic_analysis",
    "scientific_question": objective["scientific_question"],
    "expected_outputs": objective["expected_outputs"],
    "not_authorized": objective["not_authorized"],
    "next_allowed_step": objective["next_allowed_step"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_INTERVENTION_FAILURE_OBJECTIVE_WRITTEN")
print(REVIEW_MD)
print(REVIEW_JSON)
print(OBJECTIVE_MD)
print(OBJECTIVE_JSON)
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path

paths = [
    Path("docs/idare_subject_relative_preprocessed_minimal_training_review_status.json"),
    Path("docs/idare_subject_variability_intervention_failure_analysis_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

objective = json.loads(Path("docs/idare_subject_variability_intervention_failure_analysis_objective.json").read_text(encoding="utf-8"))
text = json.dumps(objective)
if "SupCon" not in text or "VREx" not in text:
    raise SystemExit("ERROR: SupCon/VREx decision framing missing")
if objective.get("status") != "short_term_objective_created":
    raise SystemExit("ERROR: objective status not created")
PY

grep -n "## Status\|## Review Decision\|## Next Allowed Step" docs/idare_subject_relative_preprocessed_minimal_training_review_status.md
grep -n "## Status\|## Scientific Question\|## Required Analysis Questions\|## Pass Criteria\|## Next Allowed Step" docs/idare_subject_variability_intervention_failure_analysis_objective.md
grep -n "subject-variability intervention-failure\|preprocessed minimal training review" docs/project_status_current.md
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_subject_relative_preprocessed_minimal_training_review_status.md \
  docs/idare_subject_relative_preprocessed_minimal_training_review_status.json \
  docs/idare_subject_variability_intervention_failure_analysis_objective.md \
  docs/idare_subject_variability_intervention_failure_analysis_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE intervention-failure analysis objective"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_intervention_failure_objective.log"
