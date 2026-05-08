#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start root-cause diagnostic objective creation ====="
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

echo "===== 2) create failure-analysis review closeout + root-cause diagnostic objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")

FAIL_REVIEW_MD = DOCS / "idare_failure_analysis_review_status.md"
FAIL_REVIEW_JSON = DOCS / "idare_failure_analysis_review_status.json"
ROOT_MD = DOCS / "idare_root_cause_diagnostic_objective.md"
ROOT_JSON = DOCS / "idare_root_cause_diagnostic_objective.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()

required = [
    DOCS / "idare_failure_analysis_report.md",
    DOCS / "idare_failure_analysis_report.json",
    DOCS / "idare_failure_analysis_fold_summary.csv",
    DOCS / "idare_label_policy_ablation_report.md",
    DOCS / "idare_broader_standardized_single_modality_evaluation_report.md",
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("ERROR: missing required source docs:\n" + "\n".join(missing))

failure_report = json.loads((DOCS / "idare_failure_analysis_report.json").read_text(encoding="utf-8"))

fail_review = {
    "status": "frozen_human_review_closeout",
    "created_or_updated_utc": NOW,
    "reviewed_report": "docs/idare_failure_analysis_report.md",
    "reviewed_json": "docs/idare_failure_analysis_report.json",
    "review_decision": {
        "accepted": True,
        "main_problem_statement": "Current I-DARE EEG/EMG results remain near chance/majority in many aggregates; additional blind training is not justified until root causes are localized.",
        "new_training_authorized": False,
        "fusion_authorized": False,
        "architecture_or_dg_authorized": False,
        "next_objective": "Create a controlled root-cause diagnostic objective.",
    },
    "accepted_findings": [
        "Many aggregate rows are weak-signal / near-chance or fold-specific unstable.",
        "Best label policies are mixed by modality/task, so no final global label policy is locked.",
        "BSL-stats and label-policy changes do not yet justify fusion, architecture escalation, augmentation, or DG.",
        "Next useful work is diagnosis of calibration, fold/subject difficulty, representation strength, and possible model/pipeline issues.",
    ],
    "not_authorized": [
        "new performance training from this review",
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "locking final global label policy",
        "architecture ablation",
        "data augmentation",
        "SupCon / VREx / domain generalization",
    ],
}

FAIL_REVIEW_JSON.write_text(json.dumps(fail_review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

FAIL_REVIEW_MD.write_text("""# I-DARE Failure Analysis Review Status

## Status

Frozen human-review closeout.

The failure-analysis report has been reviewed and accepted as the current diagnostic checkpoint.

Reviewed report: `docs/idare_failure_analysis_report.md`

Reviewed JSON: `docs/idare_failure_analysis_report.json`

## Review Decision

The report confirms that the current problem is not solved by simply switching BSL-stats, label policy, or recipe.

Main decision:

- Do not start new blind training.
- Do not start EEG+EMG fusion.
- Do not start architecture / augmentation / DG work.
- Do not lock a final global label policy.
- Move to a controlled root-cause diagnostic objective.

## Accepted Findings

- Many aggregate rows remain close to chance/majority behavior.
- Failure labels are dominated by weak-signal / near-chance and fold-specific instability.
- Best label policies are mixed by modality/task.
- BSL-stats and label-policy changes do not justify mainline changes or fusion.
- The next work should localize likely root causes before prescribing fixes.

## Next Allowed Step

Create and review `docs/idare_root_cause_diagnostic_objective.md`.

That objective must start with read-only diagnosis from existing predictions and reports.

## Intentionally Not Started

- new performance training
- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation
- data augmentation
- SupCon / VREx / domain generalization
""", encoding="utf-8")

root_obj = {
    "status": "short_term_objective_created",
    "created_or_updated_utc": NOW,
    "objective": "I-DARE root-cause diagnostic objective",
    "evidence_level": "diagnostic planning from existing smoke/stabilization outputs; no new performance claim",
    "source_checkpoint": {
        "failure_analysis_review": "docs/idare_failure_analysis_review_status.md",
        "failure_analysis_report": "docs/idare_failure_analysis_report.md",
        "failure_analysis_json": "docs/idare_failure_analysis_report.json",
        "fold_summary": "docs/idare_failure_analysis_fold_summary.csv",
    },
    "scientific_question": (
        "Why do current I-DARE EEG/EMG models remain near chance/majority or unstable across folds, "
        "and which root cause is most likely: label/task definition, subject/fold difficulty, calibration/threshold, "
        "representation weakness, or model/pipeline inability to learn?"
    ),
    "diagnostic_hypotheses": [
        {
            "id": "H1_label_task_definition",
            "question": "Are valence/arousal binary labels too noisy, boundary-sensitive, or subject-dependent for the current setup?",
            "evidence_to_check": [
                "label-policy sensitivity by subject/fold",
                "class balance by subject/fold/task/policy",
                "subject-level error changes across discard_midpoint / midpoint_as_low / midpoint_as_high",
            ],
        },
        {
            "id": "H2_subject_fold_generalization",
            "question": "Are failures concentrated in specific subjects or folds, suggesting cross-subject generalization difficulty?",
            "evidence_to_check": [
                "per-subject macro F1 / balanced accuracy",
                "fold hardness ranking",
                "EEG-vs-EMG weak-fold overlap",
                "valence-vs-arousal weak-subject overlap",
            ],
        },
        {
            "id": "H3_calibration_threshold",
            "question": "Are classifiers learning weak rankings but failing at the default threshold or calibration?",
            "evidence_to_check": [
                "Brier score",
                "ECE",
                "probability quantiles",
                "threshold-sweep gains",
                "prediction skew and mean probability by fold",
            ],
        },
        {
            "id": "H4_representation_weakness",
            "question": "Are current EEG/EMG representations too weak for subject-held-out generalization?",
            "evidence_to_check": [
                "comparison of EEG STIM-BSL-only vs EEG BSL-stats",
                "comparison of EMG feature-only vs EMG BSL-stats",
                "subject-level complementarity across EEG and EMG",
                "classical baseline feasibility on existing features, if later authorized",
            ],
        },
        {
            "id": "H5_model_pipeline_learning_issue",
            "question": "Is the neural training pipeline failing to learn even when signal should be learnable?",
            "evidence_to_check": [
                "micro-overfit sanity test, only after read-only diagnosis if still needed",
                "shuffled-label negative control, only after read-only diagnosis if still needed",
                "within-subject vs subject-held-out contrast, only after read-only diagnosis if still needed",
            ],
        },
    ],
    "authorized_scope": {
        "phase_1_read_only": {
            "authorized": True,
            "inputs": [
                "docs/idare_label_policy_ablation_eeg_primary_predictions.csv",
                "docs/idare_label_policy_ablation_emg_primary_predictions.csv",
                "docs/idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv",
                "docs/idare_broader_eval_eeg_bsl_stats_primary_predictions.csv",
                "docs/idare_broader_eval_emg_feature_only_primary_predictions.csv",
                "docs/idare_broader_eval_emg_bsl_stats_primary_predictions.csv",
                "corresponding JSON reports",
            ],
            "expected_outputs": [
                "docs/idare_root_cause_diagnostic_report.md",
                "docs/idare_root_cause_diagnostic_report.json",
                "docs/idare_root_cause_subject_summary.csv",
                "docs/idare_root_cause_calibration_summary.csv",
                "docs/idare_root_cause_error_overlap_summary.csv",
            ],
        },
        "phase_2_diagnostic_sanity_tests": {
            "authorized": False,
            "requires_followup_review": True,
            "candidate_tests": [
                "micro-overfit subset test",
                "shuffled-label negative control",
                "within-subject vs subject-held-out contrast",
                "simple classical baseline on existing feature representations",
            ],
        },
    },
    "root_cause_ranking_output": [
        "label/task definition issue",
        "subject/fold generalization issue",
        "calibration/threshold issue",
        "representation weakness",
        "model/pipeline learning issue",
    ],
    "pass_criteria": [
        "Report reconstructs per-subject, per-fold, per-task, per-policy diagnostics from existing predictions.",
        "Report computes calibration and threshold diagnostics where probabilities are available.",
        "Report identifies repeated weak subjects/folds and cross-modality/task overlaps.",
        "Report ranks likely root causes with evidence, confidence, and next diagnostic or fix recommendation.",
        "No new performance training is run.",
        "No fusion or architecture work is started.",
    ],
    "not_authorized": [
        "new training for performance improvement",
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "final global label-policy lock",
        "architecture ablation",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "diagnostic sanity tests before read-only root-cause report is reviewed",
    ],
    "next_allowed_step": "Prepare a read-only root-cause diagnostic script/command that consumes existing committed outputs and writes the root-cause diagnostic report.",
}

ROOT_JSON.write_text(json.dumps(root_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

ROOT_MD.write_text("""# I-DARE Root-Cause Diagnostic Objective

## Status

Short-term objective created.

No new performance training is authorized by this document.

## Why this objective exists

Recent I-DARE EEG/EMG experiments did not produce a clear performance improvement.

The controlled failure analysis shows that the project should stop blind ablations and diagnose the root cause first.

## Scientific Question

Why do current I-DARE EEG/EMG models remain near chance/majority or unstable across folds?

The diagnosis must rank the most likely cause:

1. label/task definition issue
2. subject/fold generalization issue
3. calibration/threshold issue
4. representation weakness
5. model/pipeline learning issue

## Authorized Scope

### Phase 1: read-only root-cause report

Authorized now.

Use only existing committed outputs:

- label-policy ablation prediction CSVs and JSON reports
- broader single-modality prediction CSVs and JSON reports
- failure-analysis report and fold summary

Expected outputs:

- `docs/idare_root_cause_diagnostic_report.md`
- `docs/idare_root_cause_diagnostic_report.json`
- `docs/idare_root_cause_subject_summary.csv`
- `docs/idare_root_cause_calibration_summary.csv`
- `docs/idare_root_cause_error_overlap_summary.csv`

### Phase 2: diagnostic-only sanity tests

Not authorized yet.

These may be proposed only after the read-only report is reviewed:

- micro-overfit subset test
- shuffled-label negative control
- within-subject vs subject-held-out contrast
- simple classical baseline on existing features

## Required Analyses

### Subject and fold difficulty

- per-subject macro F1
- per-subject balanced accuracy
- per-fold macro F1
- per-fold balanced accuracy
- repeated weak subjects/folds
- overlap across EEG and EMG
- overlap across valence and arousal

### Label and class-balance sensitivity

- class balance by subject/fold/task/policy
- label-policy sensitivity by subject
- label-policy sensitivity by fold
- whether `discard_midpoint`, `midpoint_as_low`, or `midpoint_as_high` creates unstable subjects

### Calibration and threshold behavior

- probability mean/median/quantiles
- Brier score
- expected calibration error
- threshold sensitivity
- prediction skew
- whether ranking is better than default threshold classification

### Representation and modality behavior

- EEG STIM-BSL-only vs EEG BSL-stats
- EMG feature-only vs EMG BSL-stats
- whether EEG and EMG fail on the same subjects
- whether one modality is complementary or just equally weak

### Model/pipeline suspicion flags

The read-only report should flag whether later diagnostic sanity tests are needed.

Possible flags:

- model cannot separate even easy folds
- probability distributions collapse
- repeated one-sided prediction skew
- no representation/label-policy setting consistently beats majority
- suspiciously strong/weak behavior that suggests leakage or data feeding issues

## Pass Criteria

The objective passes only if the generated report:

- reconstructs per-subject and per-fold diagnostics from existing predictions
- computes calibration/threshold diagnostics where probabilities are available
- identifies repeated weak subjects/folds and overlap patterns
- ranks likely root causes with evidence and confidence
- recommends exactly one next objective
- does not run new performance training
- does not start fusion or architecture work

## Not Authorized

- new training for performance improvement
- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation
- data augmentation
- SupCon / VREx / domain generalization
- diagnostic sanity tests before read-only root-cause report review

## Next Allowed Step

Prepare a read-only root-cause diagnostic script/command.

That command should consume existing committed outputs and write the root-cause diagnostic report files.
""", encoding="utf-8")

# Update central roadmap Markdown.
md = PROJECT_MD.read_text(encoding="utf-8")

fail_review_row = "| I-DARE failure analysis review | human review accepted failure-analysis report; root-cause diagnosis selected as next step | yes | `docs/idare_failure_analysis_review_status.md` | Create root-cause diagnostic objective and read-only report. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work. |"
root_row = "| I-DARE root-cause diagnostic objective | short-term objective created to localize likely causes of near-chance/mixed results; no new performance training authorized | yes | `docs/idare_root_cause_diagnostic_objective.md` | Prepare read-only root-cause diagnostic report from existing predictions. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; diagnostic sanity tests before report review. |"

if "I-DARE failure analysis review" not in md:
    anchor = "| I-DARE controlled failure analysis report |"
    lines = md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith(anchor):
            out.append(fail_review_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert failure-analysis review row")
    md = "\n".join(out) + "\n"

if "I-DARE root-cause diagnostic objective" not in md:
    lines = md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE failure analysis review |"):
            out.append(root_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert root-cause objective row")
    md = "\n".join(out) + "\n"

review_bullet = "- Human review of the controlled I-DARE failure-analysis report is frozen in `docs/idare_failure_analysis_review_status.md`; blind training is paused and root-cause diagnosis is the selected next step."
root_bullet = "- A controlled I-DARE root-cause diagnostic objective is defined in `docs/idare_root_cause_diagnostic_objective.md`; next work is a read-only diagnostic report from existing predictions, not new training or fusion."

if review_bullet not in md or root_bullet not in md:
    marker = "\n## Documentation Gap Closed by This File"
    block = ""
    if review_bullet not in md:
        block += "\n" + review_bullet + "\n"
    if root_bullet not in md:
        block += "\n" + root_bullet + "\n"
    if marker not in md:
        raise SystemExit("ERROR: project status marker not found")
    md = md.replace(marker, block + marker)

PROJECT_MD.write_text(md, encoding="utf-8")

# Update central roadmap JSON decisions.
data = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = data.setdefault("decisions", {})

decisions["idare_failure_analysis_review_status"] = {
    "status": "frozen_human_review_closeout",
    "evidence": "docs/idare_failure_analysis_review_status.md",
    "evidence_json": "docs/idare_failure_analysis_review_status.json",
    "reviewed_report": "docs/idare_failure_analysis_report.md",
    "main_decision": "Pause blind training and proceed to root-cause diagnosis.",
    "next_allowed_step": "Create root-cause diagnostic objective and then a read-only root-cause report.",
    "not_authorized": fail_review["not_authorized"],
}

decisions["idare_root_cause_diagnostic_objective"] = {
    "status": "short_term_objective_created",
    "evidence": "docs/idare_root_cause_diagnostic_objective.md",
    "evidence_json": "docs/idare_root_cause_diagnostic_objective.json",
    "new_training_authorized": False,
    "phase_1_read_only_authorized": True,
    "phase_2_diagnostic_sanity_tests_authorized": False,
    "root_cause_candidates": root_obj["root_cause_ranking_output"],
    "next_allowed_step": root_obj["next_allowed_step"],
    "not_authorized": root_obj["not_authorized"],
}

PROJECT_JSON.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_ROOT_CAUSE_OBJECTIVE_WRITTEN")
print(FAIL_REVIEW_MD)
print(FAIL_REVIEW_JSON)
print(ROOT_MD)
print(ROOT_JSON)
PY
echo

echo "===== 3) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
for p in [
    Path("docs/idare_failure_analysis_review_status.json"),
    Path("docs/idare_root_cause_diagnostic_objective.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")
PY

grep -n "## Status\|## Scientific Question\|## Authorized Scope\|## Pass Criteria\|## Next Allowed Step" docs/idare_root_cause_diagnostic_objective.md
grep -n "failure analysis review\|root-cause diagnostic objective" docs/project_status_current.md
echo

echo "===== 4) diff stat ====="
git diff --stat
echo

echo "===== 5) status before commit ====="
git status --short --branch
echo

echo "===== 6) commit and push root-cause diagnostic objective ====="
git add \
  docs/idare_failure_analysis_review_status.md \
  docs/idare_failure_analysis_review_status.json \
  docs/idare_root_cause_diagnostic_objective.md \
  docs/idare_root_cause_diagnostic_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE root-cause diagnostic objective"

git push origin main
echo

echo "===== 7) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_root_cause_diagnostic_objective.log"
