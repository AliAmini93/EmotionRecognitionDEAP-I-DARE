#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start calibration report review + calibration protocol objective ====="
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

echo "===== 2) create calibration-subject review closeout + calibration protocol objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
REVIEW_MD = DOCS / "idare_calibration_subject_generalization_review_status.md"
REVIEW_JSON = DOCS / "idare_calibration_subject_generalization_review_status.json"
OBJ_MD = DOCS / "idare_calibration_protocol_objective.md"
OBJ_JSON = DOCS / "idare_calibration_protocol_objective.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()

required = [
    DOCS / "idare_calibration_subject_generalization_report.md",
    DOCS / "idare_calibration_subject_generalization_report.json",
    DOCS / "idare_calibration_subject_threshold_summary.csv",
    DOCS / "idare_subject_difficulty_ranking.csv",
    DOCS / "idare_cross_modality_error_overlap.csv",
    DOCS / "idare_calibration_and_subject_generalization_objective.md",
    PROJECT_MD,
    PROJECT_JSON,
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("ERROR: missing required files:\n" + "\n".join(missing))

report = json.loads((DOCS / "idare_calibration_subject_generalization_report.json").read_text(encoding="utf-8"))
summary = report.get("diagnostic_summary", {})
recommended = summary.get("recommended_next_objective")
diagnosis = summary.get("diagnosis")

if recommended != "calibration_protocol_objective":
    raise SystemExit(f"ERROR: expected calibration_protocol_objective, got {recommended!r}")

review = {
    "status": "frozen_human_review_closeout",
    "created_or_updated_utc": NOW,
    "reviewed_report": "docs/idare_calibration_subject_generalization_report.md",
    "reviewed_json": "docs/idare_calibration_subject_generalization_report.json",
    "review_decision": {
        "accepted": True,
        "diagnosis": diagnosis,
        "selected_next_objective": "calibration_protocol_objective",
        "new_performance_training_authorized": False,
        "fusion_authorized": False,
        "architecture_or_dg_authorized": False,
        "final_loso_claim_authorized": False,
        "mainline_change_authorized": False,
    },
    "accepted_findings": {
        "summary": [
            "Calibration instability is supported by the read-only diagnostic.",
            "Threshold sweeps show repeated macro-F1 gains.",
            "Best thresholds vary substantially across folds and conditions.",
            "Hard-subject and cross-modality effects exist, but the selected immediate next step is a calibration protocol.",
            "The next objective must define a validation-only calibration protocol without new performance-training claims.",
        ],
        "diagnostic_summary": summary,
    },
    "not_authorized": report.get("not_authorized", []),
}

REVIEW_JSON.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
REVIEW_MD.write_text("""# I-DARE Calibration and Subject-Generalization Review Status

## Status

Frozen human-review closeout.

The calibration and subject-generalization report has been reviewed and accepted.

Reviewed report: `docs/idare_calibration_subject_generalization_report.md`

Reviewed JSON: `docs/idare_calibration_subject_generalization_report.json`

## Review Decision

The report is accepted.

Selected next objective:

`calibration_protocol_objective`

## Accepted Findings

- Calibration instability is supported.
- Threshold sweeps show repeated macro-F1 gains.
- Best thresholds vary substantially across folds and conditions.
- Hard-subject and cross-modality effects exist.
- The immediate next step is a calibration protocol objective.
- No new performance-training claim is authorized.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- new performance training
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Next Allowed Step

Create a calibration protocol objective.

The objective must define a validation-only calibration plan and must not start fusion, broad architecture work, or final claims.
""", encoding="utf-8")

objective = {
    "status": "short_term_objective_created",
    "created_or_updated_utc": NOW,
    "objective": "I-DARE validation-only calibration protocol objective",
    "evidence_level": "post-diagnostic objective after reviewed calibration/subject-generalization report; no final performance claim",
    "source_checkpoint": {
        "calibration_subject_review": "docs/idare_calibration_subject_generalization_review_status.md",
        "calibration_subject_report": "docs/idare_calibration_subject_generalization_report.md",
        "calibration_subject_json": "docs/idare_calibration_subject_generalization_report.json",
        "threshold_summary_csv": "docs/idare_calibration_subject_threshold_summary.csv",
        "subject_difficulty_csv": "docs/idare_subject_difficulty_ranking.csv",
        "cross_modality_error_overlap_csv": "docs/idare_cross_modality_error_overlap.csv",
    },
    "why_this_objective": [
        "Calibration instability is supported by the read-only diagnostic.",
        "Threshold sweeps show repeated macro-F1 gains.",
        "Best thresholds vary substantially across folds and conditions.",
        "A calibration protocol must be defined before any model-change objective.",
    ],
    "scientific_questions": [
        "Can a validation-only calibration rule improve macro-F1/balanced accuracy without using test labels?",
        "Is a global threshold per modality/task enough, or are fold/task/policy-specific thresholds required?",
        "Do calibrated predictions reduce one-class/collapse risk without inflating performance through leakage?",
        "Can calibration be defined in a reproducible way suitable for future LOSO-style evaluation?",
    ],
    "authorized_scope": {
        "diagnostic_or_protocol_only": True,
        "new_model_training": False,
        "allowed_inputs": [
            "existing prediction CSVs",
            "existing threshold summary CSV",
            "existing report JSON files",
        ],
        "allowed_work": [
            {
                "id": "define_validation_only_threshold_protocol",
                "purpose": "Define how thresholds are learned only from train/validation folds and applied to held-out fold predictions.",
                "must_prevent": [
                    "choosing threshold directly on the held-out/test fold",
                    "using test labels for calibration",
                    "reporting oracle-threshold results as performance",
                ],
            },
            {
                "id": "simulate_non_oracle_calibration_from_existing_folds",
                "purpose": "Use existing fold predictions to approximate leave-one-fold-out threshold selection.",
                "outputs": [
                    "per-modality/task/policy/recipe calibrated metrics",
                    "oracle-vs-non-oracle calibration gap",
                    "collapse/one-class risk",
                ],
            },
            {
                "id": "compare_global_vs_fold_transfer_thresholds",
                "purpose": "Check if one global threshold transfers better than fold-specific thresholds.",
                "outputs": [
                    "global threshold stability",
                    "fold-transfer threshold stability",
                    "recommended protocol granularity",
                ],
            },
            {
                "id": "calibration_protocol_pass_fail_report",
                "purpose": "Decide whether calibration is worth becoming part of the next controlled evaluation.",
                "outputs": [
                    "pass/fail decision",
                    "recommended next objective",
                    "explicit non-authorization list",
                ],
            },
        ],
    },
    "expected_outputs": [
        "docs/idare_calibration_protocol_report.md",
        "docs/idare_calibration_protocol_report.json",
        "docs/idare_calibration_protocol_summary.csv",
    ],
    "pass_criteria": [
        "No new model training is run.",
        "No held-out/test labels are used to choose thresholds for the same held-out/test predictions.",
        "Oracle threshold gains are clearly separated from validation-only simulated gains.",
        "The report states whether calibration is strong enough to justify a controlled calibration evaluation.",
        "The report recommends exactly one next objective after review.",
        "The report does not authorize fusion, architecture, augmentation, DG, or final claims.",
    ],
    "stop_conditions": [
        "If validation-only calibration gains are materially smaller than oracle gains, recommend against calibration as a fix.",
        "If validation-only calibration gives stable gains without collapse, recommend a controlled calibration evaluation objective.",
        "If calibration gains are unstable or subject-specific, recommend subject-stratified/generalization objective.",
        "If neither calibration nor subject grouping helps, recommend representation/label-task redesign objective.",
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
    "next_allowed_step": "Prepare a reviewed read-only calibration protocol analysis command/script.",
}
OBJ_JSON.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

OBJ_MD.write_text("""# I-DARE Calibration Protocol Objective

## Status

Short-term objective created.

This is a validation-only calibration protocol objective.

No new model training is authorized.

## Why This Objective Exists

The calibration and subject-generalization report was reviewed.

Accepted finding:

- Calibration instability is supported.
- Threshold sweeps show repeated macro-F1 gains.
- Best thresholds vary substantially across folds and conditions.
- A calibration protocol must be defined before any model-change objective.

## Scientific Questions

1. Can a validation-only calibration rule improve macro-F1/balanced accuracy without using test labels?
2. Is a global threshold per modality/task enough, or are fold/task/policy-specific thresholds required?
3. Do calibrated predictions reduce one-class/collapse risk without inflating performance through leakage?
4. Can calibration be defined in a reproducible way suitable for future LOSO-style evaluation?

## Authorized Work

### 1. Define validation-only threshold protocol

Purpose:

Define how thresholds are learned only from train/validation folds and applied to held-out fold predictions.

This must prevent:

- choosing threshold directly on the held-out/test fold
- using test labels for calibration
- reporting oracle-threshold results as performance

### 2. Simulate non-oracle calibration from existing folds

Purpose:

Use existing fold predictions to approximate leave-one-fold-out threshold selection.

Outputs:

- per-modality/task/policy/recipe calibrated metrics
- oracle-vs-non-oracle calibration gap
- collapse/one-class risk

### 3. Compare global vs fold-transfer thresholds

Purpose:

Check if one global threshold transfers better than fold-specific thresholds.

Outputs:

- global threshold stability
- fold-transfer threshold stability
- recommended protocol granularity

### 4. Calibration protocol pass/fail report

Purpose:

Decide whether calibration is worth becoming part of the next controlled evaluation.

Outputs:

- pass/fail decision
- recommended next objective
- explicit non-authorization list

## Expected Outputs

- `docs/idare_calibration_protocol_report.md`
- `docs/idare_calibration_protocol_report.json`
- `docs/idare_calibration_protocol_summary.csv`

## Pass Criteria

This objective passes only if:

- no new model training is run
- no held-out/test labels are used to choose thresholds for the same held-out/test predictions
- oracle threshold gains are clearly separated from validation-only simulated gains
- the report states whether calibration is strong enough to justify a controlled calibration evaluation
- the report recommends exactly one next objective after review
- the report does not authorize fusion, architecture, augmentation, DG, or final claims

## Stop Conditions

- If validation-only calibration gains are materially smaller than oracle gains, recommend against calibration as a fix.
- If validation-only calibration gives stable gains without collapse, recommend a controlled calibration evaluation objective.
- If calibration gains are unstable or subject-specific, recommend subject-stratified/generalization objective.
- If neither calibration nor subject grouping helps, recommend representation/label-task redesign objective.

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

Prepare a reviewed read-only calibration protocol analysis command/script.
""", encoding="utf-8")

project_md = PROJECT_MD.read_text(encoding="utf-8")
review_row = "| I-DARE calibration and subject-generalization review | human review accepted calibration-subject diagnostic; calibration protocol selected next | yes | `docs/idare_calibration_subject_generalization_review_status.md` | Create/run calibration protocol objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |"
obj_row = "| I-DARE calibration protocol objective | short-term validation-only calibration protocol objective created; no new model training authorized | yes | `docs/idare_calibration_protocol_objective.md` | Prepare reviewed read-only calibration protocol analysis command/script. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |"

if "I-DARE calibration and subject-generalization review" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE calibration and subject-generalization report |"):
            out.append(review_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert calibration review row")
    project_md = "\n".join(out) + "\n"

if "I-DARE calibration protocol objective" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE calibration and subject-generalization review |"):
            out.append(obj_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert calibration protocol objective row")
    project_md = "\n".join(out) + "\n"

review_bullet = "- Human review of the calibration and subject-generalization report is frozen in `docs/idare_calibration_subject_generalization_review_status.md`; calibration protocol is selected as the next controlled step."
obj_bullet = "- A validation-only calibration protocol objective is defined in `docs/idare_calibration_protocol_objective.md`; next work is a read-only calibration protocol analysis command/script."

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
decisions["idare_calibration_subject_generalization_review_status"] = {
    "status": "frozen_human_review_closeout",
    "evidence": str(REVIEW_MD),
    "evidence_json": str(REVIEW_JSON),
    "reviewed_report": "docs/idare_calibration_subject_generalization_report.md",
    "selected_next_objective": "calibration_protocol_objective",
    "new_performance_training_authorized": False,
    "not_authorized": review["not_authorized"],
}
decisions["idare_calibration_protocol_objective"] = {
    "status": "short_term_objective_created",
    "evidence": str(OBJ_MD),
    "evidence_json": str(OBJ_JSON),
    "validation_only": True,
    "new_model_training_authorized": False,
    "authorized_work": [x["id"] for x in objective["authorized_scope"]["allowed_work"]],
    "expected_outputs": objective["expected_outputs"],
    "next_allowed_step": objective["next_allowed_step"],
    "not_authorized": objective["not_authorized"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_CALIBRATION_PROTOCOL_OBJECTIVE_WRITTEN")
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
    Path("docs/idare_calibration_subject_generalization_review_status.json"),
    Path("docs/idare_calibration_protocol_objective.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")
PY

grep -n "## Status\|## Review Decision\|## Next Allowed Step" docs/idare_calibration_subject_generalization_review_status.md
grep -n "## Status\|## Scientific Questions\|## Authorized Work\|## Pass Criteria\|## Next Allowed Step" docs/idare_calibration_protocol_objective.md
grep -n "calibration and subject-generalization review\|calibration protocol objective" docs/project_status_current.md
echo

echo "===== 4) diff stat ====="
git diff --stat
echo

echo "===== 5) status before commit ====="
git status --short --branch
echo

echo "===== 6) commit and push ====="
git add \
  docs/idare_calibration_subject_generalization_review_status.md \
  docs/idare_calibration_subject_generalization_review_status.json \
  docs/idare_calibration_protocol_objective.md \
  docs/idare_calibration_protocol_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE calibration protocol objective"

git push origin main
echo

echo "===== 7) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_calibration_protocol_objective.log"
