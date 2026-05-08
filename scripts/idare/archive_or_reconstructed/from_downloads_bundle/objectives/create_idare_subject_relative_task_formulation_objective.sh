#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start representation/label-task review + subject-relative task objective ====="
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

echo "===== 2) create review closeout + subject-relative task formulation objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
REVIEW_MD = DOCS / "idare_representation_label_task_redesign_review_status.md"
REVIEW_JSON = DOCS / "idare_representation_label_task_redesign_review_status.json"
OBJ_MD = DOCS / "idare_subject_relative_task_formulation_objective.md"
OBJ_JSON = DOCS / "idare_subject_relative_task_formulation_objective.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()

required = [
    DOCS / "idare_representation_label_task_redesign_report.md",
    DOCS / "idare_representation_label_task_redesign_report.json",
    DOCS / "idare_label_noise_subject_balance_summary.csv",
    DOCS / "idare_representation_signal_diagnostic_summary.csv",
    DOCS / "idare_representation_label_task_redesign_objective.md",
    PROJECT_MD,
    PROJECT_JSON,
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("ERROR: missing required files:\n" + "\n".join(missing))

report = json.loads((DOCS / "idare_representation_label_task_redesign_report.json").read_text(encoding="utf-8"))
diagnosis = report.get("diagnosis")
leading_blocker = report.get("leading_blocker")
recommended = report.get("recommended_next_objective")

if recommended != "subject_relative_task_formulation_objective":
    raise SystemExit(f"ERROR: expected subject_relative_task_formulation_objective, got {recommended!r}")

review = {
    "status": "frozen_human_review_closeout",
    "created_or_updated_utc": NOW,
    "reviewed_report": "docs/idare_representation_label_task_redesign_report.md",
    "reviewed_json": "docs/idare_representation_label_task_redesign_report.json",
    "review_decision": {
        "accepted": True,
        "leading_blocker": leading_blocker,
        "diagnosis": diagnosis,
        "selected_next_objective": "subject_relative_task_formulation_objective",
        "global_binary_task_as_primary_fix_rejected": True,
        "new_performance_training_authorized": False,
        "fusion_authorized": False,
        "architecture_or_dg_authorized": False,
        "final_loso_claim_authorized": False,
        "mainline_change_authorized": False,
    },
    "accepted_findings": {
        "summary": [
            "The leading blocker is label/task subject dependence.",
            "Global binary labels are likely unstable under subject-heldout evaluation.",
            "Subject-relative task formulation should be tested before architecture, fusion, augmentation, or domain generalization.",
        ],
        "label_task_metrics": report.get("label_task_metrics", {}),
        "representation_metrics": report.get("representation_metrics", {}),
    },
    "not_authorized": report.get("not_authorized", []),
}
REVIEW_JSON.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
REVIEW_MD.write_text("""# I-DARE Representation and Label-task Redesign Review Status

## Status

Frozen human-review closeout.

The representation/label-task redesign diagnostic report has been reviewed and accepted.

Reviewed report: `docs/idare_representation_label_task_redesign_report.md`

Reviewed JSON: `docs/idare_representation_label_task_redesign_report.json`

## Review Decision

The report is accepted.

Leading blocker:

`label_task_subject_dependence`

Diagnosis:

`subject_relative_label_task_problem_supported`

Selected next objective:

`subject_relative_task_formulation_objective`

## Accepted Findings

- The leading blocker is label/task subject dependence.
- Global binary labels are likely unstable under subject-heldout evaluation.
- Subject-relative task formulation should be tested before architecture, fusion, augmentation, or domain generalization.
- No new performance-training claim is authorized by this review.

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

Create a subject-relative task formulation objective.

The objective must stay planning/diagnostic-first and must not start broad model training or final claims.
""", encoding="utf-8")

objective = {
    "status": "short_term_objective_created",
    "created_or_updated_utc": NOW,
    "objective": "I-DARE subject-relative task formulation objective",
    "evidence_level": "diagnostic/design objective after representation/label-task review; no final performance claim",
    "source_checkpoint": {
        "representation_label_task_review": "docs/idare_representation_label_task_redesign_review_status.md",
        "representation_label_task_report": "docs/idare_representation_label_task_redesign_report.md",
        "label_noise_subject_balance_summary": "docs/idare_label_noise_subject_balance_summary.csv",
        "representation_signal_diagnostic_summary": "docs/idare_representation_signal_diagnostic_summary.csv",
    },
    "why_this_objective": [
        "The leading blocker is label/task subject dependence.",
        "Global binary labels are likely unstable under subject-heldout evaluation.",
        "Subject-relative task formulation is the next controlled fix candidate before architecture, fusion, augmentation, or DG.",
    ],
    "scientific_questions": [
        "Can subject-relative labels reduce between-subject label skew while preserving within-subject affective ordering?",
        "Which subject-relative formulation is least leaky and most compatible with subject-heldout evaluation?",
        "Can a future small controlled training run use only train-subject statistics to define or calibrate task labels without touching heldout subjects?",
        "What exact run matrix should be used next if this formulation passes design review?",
    ],
    "authorized_scope": {
        "diagnostic_or_design_only": True,
        "new_model_training": False,
        "allowed_inputs": [
            "existing cache index CSVs",
            "existing original rating/score columns",
            "existing diagnostic CSV/JSON/MD outputs",
            "existing prediction CSVs for error context only",
        ],
        "authorized_work": [
            {
                "id": "subject_relative_label_design",
                "purpose": "Define candidate subject-relative labels using only within-subject rating structure.",
                "candidate_formulations": [
                    "subject_median_split",
                    "subject_zscore_sign",
                    "subject_top_bottom_quantile",
                    "within_subject_pairwise_or_ranking_task",
                ],
            },
            {
                "id": "leakage_audit",
                "purpose": "Specify which statistics are computed per subject and which are allowed at train/test time.",
                "must_answer": [
                    "Does the formulation require heldout-subject label distribution knowledge?",
                    "Can it be applied using only the heldout subject's own trial ratings without using predictions?",
                    "Is the formulation compatible with the project's scientific question?",
                ],
            },
            {
                "id": "class_balance_and_coverage_audit",
                "purpose": "Compute expected sample retention, per-fold balance, and subject coverage for each candidate formulation.",
            },
            {
                "id": "future_controlled_run_matrix_design",
                "purpose": "Prepare but do not execute the next minimal controlled training matrix if one formulation is selected.",
            },
        ],
    },
    "expected_outputs": [
        "docs/idare_subject_relative_task_formulation_report.md",
        "docs/idare_subject_relative_task_formulation_report.json",
        "docs/idare_subject_relative_label_balance_summary.csv",
        "docs/idare_subject_relative_candidate_matrix.csv",
    ],
    "pass_criteria": [
        "No new model training is run.",
        "No fusion, architecture improvement, augmentation, DG, or final LOSO claim is authorized.",
        "At least three subject-relative candidate formulations are audited.",
        "The report states leakage risks and whether each formulation is scientifically valid.",
        "The report recommends exactly one next objective after human review.",
        "If a future training objective is recommended, it must be small, controlled, and explicitly separated from this planning objective.",
    ],
    "candidate_next_objectives_after_review": [
        "minimal_subject_relative_training_objective",
        "subject_relative_label_quality_audit_objective",
        "representation_preprocessing_redesign_objective",
        "data_quality_or_label_noise_audit_objective",
        "stop_or_handoff_objective",
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
    "next_allowed_step": "Prepare a reviewed read-only subject-relative task formulation report command/script.",
}
OBJ_JSON.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

OBJ_MD.write_text("""# I-DARE Subject-relative Task Formulation Objective

## Status

Short-term objective created.

This is a diagnostic/design objective.

No new model training is authorized.

## Why This Objective Exists

The representation/label-task diagnostic report was reviewed.

Accepted findings:

- The leading blocker is label/task subject dependence.
- Global binary labels are likely unstable under subject-heldout evaluation.
- Subject-relative task formulation should be tested before architecture, fusion, augmentation, or domain generalization.

## Scientific Questions

1. Can subject-relative labels reduce between-subject label skew while preserving within-subject affective ordering?
2. Which subject-relative formulation is least leaky and most compatible with subject-heldout evaluation?
3. Can a future small controlled training run use only train-subject statistics to define or calibrate task labels without touching heldout subjects?
4. What exact run matrix should be used next if this formulation passes design review?

## Authorized Work

### 1. Subject-relative label design

Purpose:

Define candidate subject-relative labels using only within-subject rating structure.

Candidate formulations:

- `subject_median_split`
- `subject_zscore_sign`
- `subject_top_bottom_quantile`
- `within_subject_pairwise_or_ranking_task`

### 2. Leakage audit

Purpose:

Specify which statistics are computed per subject and which are allowed at train/test time.

Must answer:

- Does the formulation require heldout-subject label distribution knowledge?
- Can it be applied using only the heldout subject's own trial ratings without using predictions?
- Is the formulation compatible with the project's scientific question?

### 3. Class-balance and coverage audit

Purpose:

Compute expected sample retention, per-fold balance, and subject coverage for each candidate formulation.

### 4. Future controlled run-matrix design

Purpose:

Prepare but do not execute the next minimal controlled training matrix if one formulation is selected.

## Expected Outputs

- `docs/idare_subject_relative_task_formulation_report.md`
- `docs/idare_subject_relative_task_formulation_report.json`
- `docs/idare_subject_relative_label_balance_summary.csv`
- `docs/idare_subject_relative_candidate_matrix.csv`

## Pass Criteria

This objective passes only if:

- no new model training is run
- no fusion, architecture improvement, augmentation, DG, or final LOSO claim is authorized
- at least three subject-relative candidate formulations are audited
- the report states leakage risks and whether each formulation is scientifically valid
- the report recommends exactly one next objective after human review
- if a future training objective is recommended, it must be small, controlled, and explicitly separated from this planning objective

## Candidate Next Objectives After Review

- `minimal_subject_relative_training_objective`
- `subject_relative_label_quality_audit_objective`
- `representation_preprocessing_redesign_objective`
- `data_quality_or_label_noise_audit_objective`
- `stop_or_handoff_objective`

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

Prepare a reviewed read-only subject-relative task formulation report command/script.
""", encoding="utf-8")

project_md = PROJECT_MD.read_text(encoding="utf-8")
review_row = "| I-DARE representation and label-task redesign review | human review accepted blocker diagnosis; subject-relative task formulation selected next | yes | `docs/idare_representation_label_task_redesign_review_status.md` | Create/run subject-relative task formulation objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |"
obj_row = "| I-DARE subject-relative task formulation objective | short-term diagnostic/design objective created; no new model training authorized | yes | `docs/idare_subject_relative_task_formulation_objective.md` | Prepare reviewed read-only subject-relative task formulation command/script. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |"

if "I-DARE representation and label-task redesign review" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE representation and label-task redesign report |"):
            out.append(review_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert representation review row")
    project_md = "\n".join(out) + "\n"

if "I-DARE subject-relative task formulation objective" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE representation and label-task redesign review |"):
            out.append(obj_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert subject-relative objective row")
    project_md = "\n".join(out) + "\n"

review_bullet = "- Human review of the representation/label-task diagnostic is frozen in `docs/idare_representation_label_task_redesign_review_status.md`; subject-relative task formulation is selected next."
obj_bullet = "- A subject-relative task formulation objective is defined in `docs/idare_subject_relative_task_formulation_objective.md`; next work is a read-only task-formulation report command/script."

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
decisions["idare_representation_label_task_redesign_review_status"] = {
    "status": "frozen_human_review_closeout",
    "evidence": str(REVIEW_MD),
    "evidence_json": str(REVIEW_JSON),
    "reviewed_report": "docs/idare_representation_label_task_redesign_report.md",
    "leading_blocker": leading_blocker,
    "diagnosis": diagnosis,
    "selected_next_objective": "subject_relative_task_formulation_objective",
    "new_performance_training_authorized": False,
    "not_authorized": review["not_authorized"],
}
decisions["idare_subject_relative_task_formulation_objective"] = {
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

print("OK_SUBJECT_RELATIVE_OBJECTIVE_WRITTEN")
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
    Path("docs/idare_representation_label_task_redesign_review_status.json"),
    Path("docs/idare_subject_relative_task_formulation_objective.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")
PY

grep -n "## Status\|## Review Decision\|## Next Allowed Step" docs/idare_representation_label_task_redesign_review_status.md
grep -n "## Status\|## Scientific Questions\|## Authorized Work\|## Pass Criteria\|## Next Allowed Step" docs/idare_subject_relative_task_formulation_objective.md
grep -n "representation and label-task redesign review\|subject-relative task formulation objective" docs/project_status_current.md
echo

echo "===== 4) diff stat ====="
git diff --stat
echo

echo "===== 5) status before commit ====="
git status --short --branch
echo

echo "===== 6) commit and push ====="
git add \
  docs/idare_representation_label_task_redesign_review_status.md \
  docs/idare_representation_label_task_redesign_review_status.json \
  docs/idare_subject_relative_task_formulation_objective.md \
  docs/idare_subject_relative_task_formulation_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE subject-relative task objective"

git push origin main
echo

echo "===== 7) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_subject_relative_task_objective.log"
