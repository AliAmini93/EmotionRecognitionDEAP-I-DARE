#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start calibration protocol review + representation/label-task redesign objective ====="
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
from pathlib import Path
print("OK_IMPORTS")
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repo is not clean; commit/stash current changes before creating review/objective."
  git status --short --branch
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) create calibration protocol review closeout + representation/label-task redesign objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
REVIEW_MD = DOCS / "idare_calibration_protocol_review_status.md"
REVIEW_JSON = DOCS / "idare_calibration_protocol_review_status.json"
OBJ_MD = DOCS / "idare_representation_label_task_redesign_objective.md"
OBJ_JSON = DOCS / "idare_representation_label_task_redesign_objective.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()

required = [
    DOCS / "idare_calibration_protocol_report.md",
    DOCS / "idare_calibration_protocol_report.json",
    DOCS / "idare_calibration_protocol_summary.csv",
    DOCS / "idare_calibration_protocol_objective.md",
    PROJECT_MD,
    PROJECT_JSON,
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("ERROR: missing required files:\n" + "\n".join(missing))

report = json.loads((DOCS / "idare_calibration_protocol_report.json").read_text(encoding="utf-8"))
summary = report.get("protocol_summary", {})
diagnosis = summary.get("diagnosis")
recommended = summary.get("recommended_next_objective")
if recommended != "representation_label_task_redesign_objective":
    raise SystemExit(f"ERROR: expected representation_label_task_redesign_objective, got {recommended!r}")

review = {
    "status": "frozen_human_review_closeout",
    "created_or_updated_utc": NOW,
    "reviewed_report": "docs/idare_calibration_protocol_report.md",
    "reviewed_json": "docs/idare_calibration_protocol_report.json",
    "review_decision": {
        "accepted": True,
        "diagnosis": diagnosis,
        "selected_next_objective": "representation_label_task_redesign_objective",
        "calibration_as_primary_fix_rejected": True,
        "new_performance_training_authorized": False,
        "fusion_authorized": False,
        "architecture_or_dg_authorized": False,
        "final_loso_claim_authorized": False,
        "mainline_change_authorized": False,
    },
    "accepted_findings": {
        "summary": [
            "Validation-only calibration gains are too small or inconsistent.",
            "Calibration alone should not be treated as the main fix.",
            "The next objective should inspect representation, labels, and task formulation before any model-change or fusion objective.",
        ],
        "protocol_summary": summary,
    },
    "not_authorized": report.get("not_authorized", []),
}
REVIEW_JSON.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
REVIEW_MD.write_text("""# I-DARE Calibration Protocol Review Status

## Status

Frozen human-review closeout.

The validation-only calibration protocol report has been reviewed and accepted.

Reviewed report: `docs/idare_calibration_protocol_report.md`

Reviewed JSON: `docs/idare_calibration_protocol_report.json`

## Review Decision

The report is accepted.

Diagnosis:

`calibration_not_sufficient_as_primary_fix`

Selected next objective:

`representation_label_task_redesign_objective`

## Accepted Findings

- Validation-only calibration gains are too small or inconsistent.
- Calibration alone should not be treated as the main fix.
- The next step should inspect representation, labels, and task formulation before any model-change or fusion objective.
- No new performance-training claim is authorized.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- new model training
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Next Allowed Step

Create a representation/label-task redesign objective.

The objective must stay diagnostic/planning-first and must not start broad model training or final claims.
""", encoding="utf-8")

objective = {
    "status": "short_term_objective_created",
    "created_or_updated_utc": NOW,
    "objective": "I-DARE representation and label-task redesign objective",
    "evidence_level": "post-calibration diagnostic objective; no final performance claim",
    "source_checkpoint": {
        "calibration_protocol_review": "docs/idare_calibration_protocol_review_status.md",
        "calibration_protocol_report": "docs/idare_calibration_protocol_report.md",
        "calibration_protocol_json": "docs/idare_calibration_protocol_report.json",
        "calibration_protocol_summary": "docs/idare_calibration_protocol_summary.csv",
        "root_cause_report": "docs/idare_root_cause_diagnostic_report.md",
        "diagnostic_sanity_report": "docs/idare_diagnostic_sanity_tests_report.md",
        "failure_analysis_report": "docs/idare_failure_analysis_report.md",
    },
    "why_this_objective": [
        "Calibration is not sufficient as the primary fix.",
        "Repeated near-chance/mixed results remain after BSL-stats, label-policy, failure, sanity, and calibration diagnostics.",
        "Before changing architecture or starting fusion, the project needs a diagnostic redesign of representation, label construction, and task framing.",
    ],
    "scientific_questions": [
        "Are the current binary labels too noisy, unstable, or subject-dependent for the current subject-heldout setup?",
        "Is the current STIM-BSL representation preserving emotion-related signal or mostly subject/session nuisance structure?",
        "Are arousal/valence being treated as single global binary tasks when subject-relative or trial-relative formulations would be more appropriate?",
        "Which future fix should be tested first: label redesign, representation redesign, or subject-normalized task formulation?",
    ],
    "authorized_scope": {
        "diagnostic_or_design_only": True,
        "new_model_training": False,
        "allowed_inputs": [
            "existing cache index CSVs",
            "existing prediction CSVs",
            "existing JSON/MD diagnostic reports",
            "existing label columns and rating distributions",
        ],
        "authorized_work": [
            {
                "id": "label_noise_and_policy_diagnosis",
                "purpose": "Audit original rating distributions, midpoint density, class balance by subject/fold/task, and label-policy disagreement.",
                "outputs": [
                    "per-subject/task label balance",
                    "midpoint/near-midpoint burden",
                    "policy disagreement map",
                    "candidate label policies for future controlled test",
                ],
            },
            {
                "id": "subject_dependency_diagnosis",
                "purpose": "Quantify whether errors and labels are dominated by subject identity, fold composition, or subject-specific baselines.",
                "outputs": [
                    "hard-subject clusters",
                    "subject-label skew table",
                    "subject-vs-task confounding indicators",
                ],
            },
            {
                "id": "representation_signal_diagnosis",
                "purpose": "Test whether current EEG/EMG representations separate labels beyond subject/session nuisance using read-only feature summaries.",
                "outputs": [
                    "representation separability checks",
                    "subject separability vs label separability",
                    "feature/representation redesign recommendations",
                ],
            },
            {
                "id": "task_redesign_options",
                "purpose": "Define a small set of future controlled objectives without running them yet.",
                "outputs": [
                    "recommended task formulation",
                    "candidate future objective list",
                    "one selected next objective after review",
                ],
            },
        ],
    },
    "expected_outputs": [
        "docs/idare_representation_label_task_redesign_report.md",
        "docs/idare_representation_label_task_redesign_report.json",
        "docs/idare_label_noise_subject_balance_summary.csv",
        "docs/idare_representation_signal_diagnostic_summary.csv",
    ],
    "pass_criteria": [
        "No new model training is run.",
        "No fusion, architecture improvement, augmentation, DG, or final LOSO claim is authorized.",
        "The report identifies whether the leading blocker is label/task design, representation design, subject generalization, or unresolved/mixed.",
        "The report recommends exactly one next objective after human review.",
        "The report states which tempting next steps are still not authorized.",
    ],
    "candidate_next_objectives_after_review": [
        "subject_normalized_labeling_objective",
        "subject_relative_task_formulation_objective",
        "representation_preprocessing_redesign_objective",
        "minimal_controlled_training_objective",
        "data_quality_or_label_noise_audit_objective",
    ],
    "not_authorized": [
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "final global label-policy lock",
        "new model training",
        "architecture ablation for improvement",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "broad hyperparameter search",
        "mainline change",
    ],
    "next_allowed_step": "Prepare a reviewed read-only representation/label-task diagnostic report command/script.",
}
OBJ_JSON.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

OBJ_MD.write_text("""# I-DARE Representation and Label-task Redesign Objective

## Status

Short-term objective created.

This is a diagnostic/design objective.

No new model training is authorized.

## Why This Objective Exists

The validation-only calibration protocol report was reviewed.

Accepted finding:

- Calibration is not sufficient as the primary fix.
- Near-chance/mixed results remain after BSL-stats, label-policy, failure, sanity, and calibration diagnostics.
- Before changing architecture or starting fusion, the project needs a diagnostic redesign of representation, label construction, and task framing.

## Scientific Questions

1. Are the current binary labels too noisy, unstable, or subject-dependent for the current subject-heldout setup?
2. Is the current `STIM-BSL` representation preserving emotion-related signal or mostly subject/session nuisance structure?
3. Are arousal/valence being treated as single global binary tasks when subject-relative or trial-relative formulations would be more appropriate?
4. Which future fix should be tested first: label redesign, representation redesign, or subject-normalized task formulation?

## Authorized Work

### 1. Label-noise and label-policy diagnosis

Purpose:

Audit original rating distributions, midpoint density, class balance by subject/fold/task, and label-policy disagreement.

Outputs:

- per-subject/task label balance
- midpoint/near-midpoint burden
- policy disagreement map
- candidate label policies for future controlled test

### 2. Subject-dependency diagnosis

Purpose:

Quantify whether errors and labels are dominated by subject identity, fold composition, or subject-specific baselines.

Outputs:

- hard-subject clusters
- subject-label skew table
- subject-vs-task confounding indicators

### 3. Representation-signal diagnosis

Purpose:

Test whether current EEG/EMG representations separate labels beyond subject/session nuisance using read-only feature summaries.

Outputs:

- representation separability checks
- subject separability vs label separability
- feature/representation redesign recommendations

### 4. Task-redesign options

Purpose:

Define a small set of future controlled objectives without running them yet.

Outputs:

- recommended task formulation
- candidate future objective list
- one selected next objective after review

## Expected Outputs

- `docs/idare_representation_label_task_redesign_report.md`
- `docs/idare_representation_label_task_redesign_report.json`
- `docs/idare_label_noise_subject_balance_summary.csv`
- `docs/idare_representation_signal_diagnostic_summary.csv`

## Pass Criteria

This objective passes only if:

- no new model training is run
- no fusion, architecture improvement, augmentation, DG, or final LOSO claim is authorized
- the report identifies whether the leading blocker is label/task design, representation design, subject generalization, or unresolved/mixed
- the report recommends exactly one next objective after human review
- the report states which tempting next steps are still not authorized

## Candidate Next Objectives After Review

- `subject_normalized_labeling_objective`
- `subject_relative_task_formulation_objective`
- `representation_preprocessing_redesign_objective`
- `minimal_controlled_training_objective`
- `data_quality_or_label_noise_audit_objective`

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- new model training
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Next Allowed Step

Prepare a reviewed read-only representation/label-task diagnostic report command/script.
""", encoding="utf-8")

project_md = PROJECT_MD.read_text(encoding="utf-8")
review_row = "| I-DARE calibration protocol review | human review accepted calibration protocol report; calibration rejected as primary fix | yes | `docs/idare_calibration_protocol_review_status.md` | Create/run representation and label-task redesign objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |"
obj_row = "| I-DARE representation and label-task redesign objective | short-term diagnostic/design objective created; no new model training authorized | yes | `docs/idare_representation_label_task_redesign_objective.md` | Prepare reviewed read-only representation/label-task diagnostic command/script. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |"

if "I-DARE calibration protocol review" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE calibration protocol report |"):
            out.append(review_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert calibration protocol review row")
    project_md = "\n".join(out) + "\n"

if "I-DARE representation and label-task redesign objective" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE calibration protocol review |"):
            out.append(obj_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert representation objective row")
    project_md = "\n".join(out) + "\n"

review_bullet = "- Human review of the calibration protocol report is frozen in `docs/idare_calibration_protocol_review_status.md`; calibration is rejected as the primary fix."
obj_bullet = "- A representation and label-task redesign objective is defined in `docs/idare_representation_label_task_redesign_objective.md`; next work is a read-only diagnostic/design report command/script."

if review_bullet not in project_md or obj_bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: project status marker not found")
    block = ""
    if review_bullet not in project_md:
        block += "\n" + review_bullet + "\n"
    if obj_bullet not in project_md:
        block += "\n" + obj_bullet + "\n"
    project_md = project_md.replace(marker, block + marker)

PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_calibration_protocol_review_status"] = {
    "status": "frozen_human_review_closeout",
    "evidence": str(REVIEW_MD),
    "evidence_json": str(REVIEW_JSON),
    "reviewed_report": "docs/idare_calibration_protocol_report.md",
    "diagnosis": diagnosis,
    "selected_next_objective": "representation_label_task_redesign_objective",
    "new_performance_training_authorized": False,
    "not_authorized": review["not_authorized"],
}
decisions["idare_representation_label_task_redesign_objective"] = {
    "status": "short_term_objective_created",
    "evidence": str(OBJ_MD),
    "evidence_json": str(OBJ_JSON),
    "new_model_training_authorized": False,
    "authorized_work": [x["id"] for x in objective["authorized_scope"]["authorized_work"]],
    "expected_outputs": objective["expected_outputs"],
    "candidate_next_objectives_after_review": objective["candidate_next_objectives_after_review"],
    "next_allowed_step": objective["next_allowed_step"],
    "not_authorized": objective["not_authorized"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_REPRESENTATION_LABEL_TASK_OBJECTIVE_WRITTEN")
print(REVIEW_MD)
print(REVIEW_JSON)
print(OBJ_MD)
print(OBJ_JSON)
PY
echo

echo "===== 3) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
for p in [
    Path("docs/idare_calibration_protocol_review_status.json"),
    Path("docs/idare_representation_label_task_redesign_objective.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")
PY

grep -n "## Status\|## Review Decision\|## Next Allowed Step" docs/idare_calibration_protocol_review_status.md
grep -n "## Status\|## Scientific Questions\|## Authorized Work\|## Pass Criteria\|## Next Allowed Step" docs/idare_representation_label_task_redesign_objective.md
grep -n "calibration protocol review\|representation and label-task redesign objective" docs/project_status_current.md
echo

echo "===== 4) diff stat ====="
git diff --stat
echo

echo "===== 5) status before commit ====="
git status --short --branch
echo

echo "===== 6) commit and push ====="
git add \
  docs/idare_calibration_protocol_review_status.md \
  docs/idare_calibration_protocol_review_status.json \
  docs/idare_representation_label_task_redesign_objective.md \
  docs/idare_representation_label_task_redesign_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE representation label-task objective"

git push origin main
echo

echo "===== 7) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_representation_label_task_objective.log"
