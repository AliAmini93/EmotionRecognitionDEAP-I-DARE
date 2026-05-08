#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start diagnostic-sanity review + calibration/subject-generalization objective ====="
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
  echo "ERROR: repo is not clean; commit/stash current changes before creating objective."
  git status --short --branch
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) create review closeout + calibration/subject-generalization objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
REVIEW_MD = DOCS / "idare_diagnostic_sanity_tests_review_status.md"
REVIEW_JSON = DOCS / "idare_diagnostic_sanity_tests_review_status.json"
OBJ_MD = DOCS / "idare_calibration_and_subject_generalization_objective.md"
OBJ_JSON = DOCS / "idare_calibration_and_subject_generalization_objective.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()

required = [
    DOCS / "idare_diagnostic_sanity_tests_report.md",
    DOCS / "idare_diagnostic_sanity_tests_report.json",
    DOCS / "idare_diagnostic_sanity_tests_summary.csv",
    DOCS / "idare_diagnostic_sanity_tests_objective.md",
    DOCS / "idare_root_cause_diagnostic_review_status.md",
    PROJECT_MD,
    PROJECT_JSON,
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("ERROR: missing required files:\n" + "\n".join(missing))

report = json.loads((DOCS / "idare_diagnostic_sanity_tests_report.json").read_text(encoding="utf-8"))
diag = report.get("diagnostic_summary", {})
recommended = diag.get("recommended_next_objective")

if recommended != "calibration_and_subject_generalization_objective":
    raise SystemExit(f"ERROR: unexpected recommended_next_objective={recommended!r}")

review = {
    "status": "frozen_human_review_closeout",
    "created_or_updated_utc": NOW,
    "reviewed_report": "docs/idare_diagnostic_sanity_tests_report.md",
    "reviewed_json": "docs/idare_diagnostic_sanity_tests_report.json",
    "review_decision": {
        "accepted": True,
        "selected_next_objective": "calibration_and_subject_generalization_objective",
        "micro_overfit_result_accepted": bool(diag.get("micro_overfit_all_passed")),
        "shuffled_label_result_accepted": bool(diag.get("shuffled_label_control_all_passed")),
        "diagnosis": diag.get("diagnosis"),
        "new_performance_training_authorized": False,
        "calibration_and_subject_generalization_objective_authorized_next": True,
        "fusion_authorized": False,
        "architecture_or_dg_authorized": False,
        "final_label_policy_authorized": False,
    },
    "accepted_findings": {
        "summary": [
            "Micro-overfit passed for EEG and EMG, so total model/data-path learning failure is weakened.",
            "Shuffled-label negative control passed, so major leakage/split/metric failure is not supported by this diagnostic.",
            "Within-subject vs subject-heldout evidence is mixed, not a clean single-cause subject-generalization proof.",
            "Simple classical baselines are mostly near chance, except weak EEG arousal signal.",
            "The next objective should focus on calibration and subject/fold generalization diagnostics, not fusion or architecture escalation.",
        ],
        "diagnostic_summary": diag,
    },
    "not_authorized": report.get("not_authorized", []),
}

REVIEW_JSON.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

REVIEW_MD.write_text("""# I-DARE Diagnostic Sanity Tests Review Status

## Status

Frozen human-review closeout.

The diagnostic sanity tests report has been reviewed and accepted.

Reviewed report: `docs/idare_diagnostic_sanity_tests_report.md`

Reviewed JSON: `docs/idare_diagnostic_sanity_tests_report.json`

## Review Decision

The report is accepted.

Selected next objective:

`calibration_and_subject_generalization_objective`

## Accepted Findings

- Micro-overfit passed for EEG and EMG.
- Shuffled-label negative control passed.
- A total pipeline/model/data-feeding failure is weakened.
- Major leakage/split/metric failure is not supported by this diagnostic.
- Within-subject vs subject-heldout evidence is mixed.
- Simple classical baselines are mostly near chance, except weak EEG arousal signal.
- The next step should focus on calibration and subject/fold generalization diagnostics.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Next Allowed Step

Create a calibration and subject-generalization objective.

This objective must remain diagnostic/analysis-first and must not start fusion or architecture escalation.
""", encoding="utf-8")

objective = {
    "status": "short_term_objective_created",
    "created_or_updated_utc": NOW,
    "objective": "I-DARE calibration and subject-generalization objective",
    "evidence_level": "post-diagnostic objective after reviewed sanity tests; no final performance claim",
    "source_checkpoint": {
        "diagnostic_sanity_review": "docs/idare_diagnostic_sanity_tests_review_status.md",
        "diagnostic_sanity_report": "docs/idare_diagnostic_sanity_tests_report.md",
        "diagnostic_sanity_json": "docs/idare_diagnostic_sanity_tests_report.json",
        "diagnostic_sanity_summary": "docs/idare_diagnostic_sanity_tests_summary.csv",
    },
    "why_this_objective": [
        "Micro-overfit passed, weakening a total data-path/model/loss failure explanation.",
        "Shuffled-label controls passed, weakening a major leakage/split/metric bug explanation.",
        "Results are still weak/mixed, so calibration and subject/fold effects are the most useful next diagnostic target.",
        "The goal is to identify whether better thresholds/calibration or subject/fold-specific instability explains a meaningful part of the failure.",
    ],
    "scientific_questions": [
        "Are the models producing useful ranking/probability information that is hidden by a fixed 0.5 threshold?",
        "Do fold-specific thresholds or calibration improve macro-F1/balanced accuracy enough to justify a calibration protocol?",
        "Are a small number of subjects/folds systematically driving failure across modalities and tasks?",
        "Are errors consistent across EEG and EMG for the same subject/task, suggesting subject-level difficulty rather than modality-specific failure?",
        "Can subject/fold grouping reveal trainable strata without starting fusion or architecture changes?",
    ],
    "authorized_scope": {
        "diagnostic_only": True,
        "new_performance_training": False,
        "allowed_inputs": [
            "existing primary prediction CSVs",
            "existing label-policy ablation prediction CSVs",
            "existing root-cause and diagnostic sanity summary files",
        ],
        "allowed_analyses": [
            {
                "id": "threshold_sweep_by_modality_task_policy",
                "purpose": "Quantify whether fixed 0.5 threshold hides useful score/ranking information.",
                "outputs": [
                    "best threshold per modality/task/policy/recipe",
                    "macro-F1 gain",
                    "balanced-accuracy gain",
                    "one-class threshold risk",
                ],
            },
            {
                "id": "fold_specific_calibration_diagnostic",
                "purpose": "Measure threshold instability across folds.",
                "outputs": [
                    "fold-wise best thresholds",
                    "threshold variance",
                    "fold-wise gain distribution",
                    "calibration instability flag",
                ],
            },
            {
                "id": "subject_difficulty_ranking",
                "purpose": "Rank subjects by repeated failure across existing outputs.",
                "outputs": [
                    "subject failure count",
                    "mean correctness",
                    "task/modality failure overlap",
                    "hard-subject shortlist",
                ],
            },
            {
                "id": "cross_modality_error_overlap",
                "purpose": "Check whether EEG and EMG fail on the same subjects/tasks.",
                "outputs": [
                    "overlap rates",
                    "subject-level common-failure score",
                    "modality-specific vs subject-level failure flag",
                ],
            },
            {
                "id": "recipe_policy_stability_map",
                "purpose": "Identify whether any recipe/policy is consistently less fragile.",
                "outputs": [
                    "ranking by macro-F1",
                    "ranking by balanced accuracy",
                    "ranking by threshold gain",
                    "stability flag",
                ],
            },
        ],
    },
    "expected_outputs": [
        "docs/idare_calibration_subject_generalization_report.md",
        "docs/idare_calibration_subject_generalization_report.json",
        "docs/idare_calibration_subject_threshold_summary.csv",
        "docs/idare_subject_difficulty_ranking.csv",
        "docs/idare_cross_modality_error_overlap.csv",
    ],
    "pass_criteria": [
        "The report is generated from existing outputs only.",
        "No new performance training is run.",
        "The report separates threshold/calibration failure from subject/fold generalization difficulty.",
        "The report identifies whether hard subjects/folds are stable across modalities/tasks.",
        "The report recommends exactly one next objective after review.",
        "The report does not authorize fusion, architecture, augmentation, DG, or final claims.",
    ],
    "stop_conditions": [
        "If threshold gains are large but unstable across folds, recommend calibration protocol objective, not architecture work.",
        "If hard subjects dominate failure across modalities/tasks, recommend subject-generalization or subject-stratified diagnostic objective.",
        "If neither calibration nor subject effects explain the weakness, recommend representation/label-task redesign objective.",
        "If evidence suggests a data/split inconsistency, recommend data-integrity audit objective.",
    ],
    "not_authorized": [
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "final global label-policy lock",
        "new performance training",
        "architecture ablation for improvement",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "broad hyperparameter search",
        "mainline change",
    ],
    "next_allowed_step": "Prepare a reviewed read-only analysis command/script for calibration and subject-generalization diagnostics.",
}

OBJ_JSON.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

OBJ_MD.write_text("""# I-DARE Calibration and Subject-Generalization Objective

## Status

Short-term objective created.

This is diagnostic/analysis-first.

No new performance training is authorized.

## Why This Objective Exists

The diagnostic sanity tests were reviewed.

Main findings:

- Micro-overfit passed for EEG and EMG.
- Shuffled-label negative control passed.
- Total pipeline/model/data-feeding failure is weakened.
- Major leakage/split/metric failure is not supported by this diagnostic.
- Results remain weak/mixed.
- The next useful target is calibration and subject/fold generalization.

## Scientific Questions

1. Are the models producing useful ranking/probability information that is hidden by a fixed 0.5 threshold?
2. Do fold-specific thresholds or calibration improve macro-F1/balanced accuracy enough to justify a calibration protocol?
3. Are a small number of subjects/folds systematically driving failure across modalities and tasks?
4. Are EEG and EMG failing on the same subjects/tasks?
5. Can subject/fold grouping reveal trainable strata without starting fusion or architecture changes?

## Authorized Analyses

### 1. Threshold sweep by modality/task/policy

Purpose:

Quantify whether fixed-threshold inference hides useful signal.

Outputs:

- best threshold
- macro-F1 gain
- balanced-accuracy gain
- one-class threshold risk

### 2. Fold-specific calibration diagnostic

Purpose:

Measure threshold instability across folds.

Outputs:

- fold-wise best thresholds
- threshold variance
- fold-wise gain distribution
- calibration instability flag

### 3. Subject difficulty ranking

Purpose:

Rank subjects by repeated failure across existing outputs.

Outputs:

- subject failure count
- mean correctness
- task/modality failure overlap
- hard-subject shortlist

### 4. Cross-modality error overlap

Purpose:

Check whether EEG and EMG fail on the same subjects/tasks.

Outputs:

- overlap rates
- subject-level common-failure score
- modality-specific vs subject-level failure flag

### 5. Recipe/policy stability map

Purpose:

Identify whether any recipe or label policy is consistently less fragile.

Outputs:

- ranking by macro-F1
- ranking by balanced accuracy
- ranking by threshold gain
- stability flag

## Expected Outputs

- `docs/idare_calibration_subject_generalization_report.md`
- `docs/idare_calibration_subject_generalization_report.json`
- `docs/idare_calibration_subject_threshold_summary.csv`
- `docs/idare_subject_difficulty_ranking.csv`
- `docs/idare_cross_modality_error_overlap.csv`

## Pass Criteria

This objective passes only if the report:

- is generated from existing outputs only
- runs no new performance training
- separates threshold/calibration failure from subject/fold generalization difficulty
- identifies whether hard subjects/folds are stable across modalities/tasks
- recommends exactly one next objective after review
- does not authorize fusion, architecture, augmentation, DG, or final claims

## Stop Conditions

- If threshold gains are large but unstable across folds: recommend calibration protocol objective, not architecture work.
- If hard subjects dominate failure across modalities/tasks: recommend subject-generalization or subject-stratified diagnostic objective.
- If neither calibration nor subject effects explain the weakness: recommend representation/label-task redesign objective.
- If evidence suggests a data/split inconsistency: recommend data-integrity audit objective.

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

Prepare a reviewed read-only analysis command/script for calibration and subject-generalization diagnostics.
""", encoding="utf-8")

# Update roadmap Markdown.
project_md = PROJECT_MD.read_text(encoding="utf-8")

review_row = "| I-DARE diagnostic sanity tests review | human review accepted sanity tests; calibration and subject-generalization selected next | yes | `docs/idare_diagnostic_sanity_tests_review_status.md` | Create/run calibration and subject-generalization diagnostic objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |"
obj_row = "| I-DARE calibration and subject-generalization objective | short-term diagnostic objective created; no new performance training authorized | yes | `docs/idare_calibration_and_subject_generalization_objective.md` | Prepare reviewed read-only analysis command/script. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |"

if "I-DARE diagnostic sanity tests review" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE diagnostic sanity tests report |"):
            out.append(review_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert diagnostic sanity review row")
    project_md = "\n".join(out) + "\n"

if "I-DARE calibration and subject-generalization objective" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE diagnostic sanity tests review |"):
            out.append(obj_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert calibration/objective row")
    project_md = "\n".join(out) + "\n"

review_bullet = "- Human review of the diagnostic sanity tests is frozen in `docs/idare_diagnostic_sanity_tests_review_status.md`; calibration and subject-generalization diagnostics are selected as the next controlled step."
obj_bullet = "- A calibration and subject-generalization objective is defined in `docs/idare_calibration_and_subject_generalization_objective.md`; next work is read-only analysis from existing outputs."

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

# Update roadmap JSON.
project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})

decisions["idare_diagnostic_sanity_tests_review_status"] = {
    "status": "frozen_human_review_closeout",
    "evidence": "docs/idare_diagnostic_sanity_tests_review_status.md",
    "evidence_json": "docs/idare_diagnostic_sanity_tests_review_status.json",
    "reviewed_report": "docs/idare_diagnostic_sanity_tests_report.md",
    "selected_next_objective": "calibration_and_subject_generalization_objective",
    "new_performance_training_authorized": False,
    "not_authorized": review["not_authorized"],
}

decisions["idare_calibration_and_subject_generalization_objective"] = {
    "status": "short_term_objective_created",
    "evidence": "docs/idare_calibration_and_subject_generalization_objective.md",
    "evidence_json": "docs/idare_calibration_and_subject_generalization_objective.json",
    "diagnostic_only": True,
    "new_performance_training_authorized": False,
    "authorized_analyses": [a["id"] for a in objective["authorized_scope"]["allowed_analyses"]],
    "expected_outputs": objective["expected_outputs"],
    "next_allowed_step": objective["next_allowed_step"],
    "not_authorized": objective["not_authorized"],
}

PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_CALIBRATION_SUBJECT_OBJECTIVE_WRITTEN")
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
    Path("docs/idare_diagnostic_sanity_tests_review_status.json"),
    Path("docs/idare_calibration_and_subject_generalization_objective.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")
PY

grep -n "## Status\|## Review Decision\|## Next Allowed Step" docs/idare_diagnostic_sanity_tests_review_status.md
grep -n "## Status\|## Scientific Questions\|## Authorized Analyses\|## Pass Criteria\|## Next Allowed Step" docs/idare_calibration_and_subject_generalization_objective.md
grep -n "diagnostic sanity tests review\|calibration and subject-generalization objective" docs/project_status_current.md
echo

echo "===== 4) diff stat ====="
git diff --stat
echo

echo "===== 5) status before commit ====="
git status --short --branch
echo

echo "===== 6) commit and push ====="
git add \
  docs/idare_diagnostic_sanity_tests_review_status.md \
  docs/idare_diagnostic_sanity_tests_review_status.json \
  docs/idare_calibration_and_subject_generalization_objective.md \
  docs/idare_calibration_and_subject_generalization_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE calibration and subject-generalization objective"

git push origin main
echo

echo "===== 7) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_calibration_subject_objective.log"
