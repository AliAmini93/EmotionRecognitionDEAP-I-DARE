#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start subject-relative formulation review + minimal training objective ====="
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

echo "===== 2) create review closeout + minimal subject-relative training objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
REVIEW_MD = DOCS / "idare_subject_relative_task_formulation_review_status.md"
REVIEW_JSON = DOCS / "idare_subject_relative_task_formulation_review_status.json"
OBJ_MD = DOCS / "idare_minimal_subject_relative_training_objective.md"
OBJ_JSON = DOCS / "idare_minimal_subject_relative_training_objective.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

REPORT_MD = DOCS / "idare_subject_relative_task_formulation_report.md"
REPORT_JSON = DOCS / "idare_subject_relative_task_formulation_report.json"
BALANCE_CSV = DOCS / "idare_subject_relative_label_balance_summary.csv"
MATRIX_CSV = DOCS / "idare_subject_relative_candidate_matrix.csv"

NOW = datetime.now(timezone.utc).isoformat()

required = [
    REPORT_MD,
    REPORT_JSON,
    BALANCE_CSV,
    MATRIX_CSV,
    DOCS / "idare_subject_relative_task_formulation_objective.md",
    DOCS / "idare_representation_label_task_redesign_review_status.md",
    PROJECT_MD,
    PROJECT_JSON,
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("ERROR: missing required files:\n" + "\n".join(missing))

report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
selected = report.get("selected_formulation")
recommended = report.get("recommended_next_objective")

if selected != "subject_top_bottom_quantile_q33":
    raise SystemExit(f"ERROR: expected selected_formulation=subject_top_bottom_quantile_q33, got {selected!r}")
if recommended != "minimal_subject_relative_training_objective":
    raise SystemExit(f"ERROR: expected recommended_next_objective=minimal_subject_relative_training_objective, got {recommended!r}")

review = {
    "status": "frozen_human_review_closeout",
    "created_or_updated_utc": NOW,
    "reviewed_report": str(REPORT_MD),
    "reviewed_json": str(REPORT_JSON),
    "review_decision": {
        "accepted": True,
        "selected_formulation": selected,
        "selected_next_objective": recommended,
        "new_training_authorized_by_review": False,
        "training_authorized_only_by_separate_objective": True,
        "fusion_authorized": False,
        "architecture_or_dg_authorized": False,
        "final_loso_claim_authorized": False,
        "mainline_change_authorized": False,
    },
    "accepted_findings": {
        "selected_formulation": selected,
        "rationale": [
            "Subject-relative top/bottom quantile formulation directly targets the diagnosed label/task subject-dependence blocker.",
            "It uses only within-subject extremes and discards ambiguous middle trials.",
            "It is lower coverage than z-score/median candidates, but gives cleaner labels for a first controlled training test.",
        ],
        "future_matrix_draft": {
            "modalities": ["EEG STIM-BSL-only", "EMG feature-only"],
            "tasks": ["valence", "arousal"],
            "folds": 6,
            "seed": 11,
            "first_pass_recipe": "ce_class_weighted",
            "first_pass_runs": 24,
            "optional_recipe": "balanced_sampler_ce",
            "optional_additional_runs": 24,
        },
    },
    "not_authorized": [
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "final global label-policy lock",
        "architecture ablation for improvement",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "broad hyperparameter search",
        "mainline change",
    ],
}
REVIEW_JSON.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

REVIEW_MD.write_text(f"""# I-DARE Subject-relative Task Formulation Review Status

## Status

Frozen human-review closeout.

The subject-relative task formulation report has been reviewed and accepted.

Reviewed report: `docs/idare_subject_relative_task_formulation_report.md`

Reviewed JSON: `docs/idare_subject_relative_task_formulation_report.json`

## Review Decision

The report is accepted.

Selected formulation:

`{selected}`

Selected next objective:

`{recommended}`

## Accepted Findings

- Subject-relative top/bottom quantile formulation directly targets the diagnosed label/task subject-dependence blocker.
- It uses only within-subject extremes and discards ambiguous middle trials.
- It is lower coverage than z-score/median candidates, but gives cleaner labels for a first controlled training test.
- The report itself did not authorize training; a separate minimal controlled training objective is required.

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

Create the minimal subject-relative training objective.

Only that objective may authorize the first small controlled training run.
""", encoding="utf-8")

objective = {
    "status": "short_term_objective_created",
    "created_or_updated_utc": NOW,
    "objective": "I-DARE minimal subject-relative training objective",
    "evidence_level": "minimal controlled diagnostic training objective; no final LOSO claim; no mainline change",
    "source_checkpoint": {
        "subject_relative_formulation_review": str(REVIEW_MD),
        "subject_relative_formulation_report": str(REPORT_MD),
        "candidate_matrix": str(MATRIX_CSV),
        "label_balance_summary": str(BALANCE_CSV),
    },
    "selected_task_formulation": selected,
    "why_this_objective": [
        "Global binary labels appear unstable under subject-heldout evaluation.",
        "Subject-relative top/bottom quantile labels are the selected controlled first fix candidate.",
        "A minimal training run is needed to test whether the task redesign improves subject-heldout macro-F1/balanced accuracy before considering architecture, fusion, augmentation, or DG.",
    ],
    "authorized_scope": {
        "new_training_authorized": True,
        "training_type": "minimal controlled diagnostic training only",
        "modalities": ["EEG_STIM_BSL_ONLY", "EMG_FEATURE_ONLY"],
        "tasks": ["valence", "arousal"],
        "folds": 6,
        "seed": 11,
        "label_formulation": selected,
        "recipes_first_pass": ["ce_class_weighted"],
        "max_runs_first_pass": 24,
        "optional_second_pass_recipe": "balanced_sampler_ce",
        "optional_second_pass_condition": "Only run after first-pass validation, if outputs are valid and the first pass is not obviously broken.",
        "optional_additional_runs": 24,
        "claim_level": "diagnostic only",
    },
    "implementation_requirements": [
        "Create or patch scripts so subject-relative labels are generated deterministically from existing per-trial valence/arousal ratings.",
        "The selected formulation is subject_top_bottom_quantile_q33: per subject and task, bottom third is class 0, top third is class 1, middle third is discarded.",
        "Fold splitting must remain sidecar-compatible: numpy default_rng(seed=11), 6 folds.",
        "No heldout-subject predictions may be used to define labels.",
        "Generated outputs must record retained sample counts per task/fold/modality.",
        "Run EEG and EMG mainlines only; do not include BSL-stats sidecars in this first pass.",
    ],
    "expected_outputs_first_pass": [
        "docs/idare_subject_relative_minimal_eeg_primary.md",
        "docs/idare_subject_relative_minimal_eeg_primary.json",
        "docs/idare_subject_relative_minimal_eeg_primary_predictions.csv",
        "docs/idare_subject_relative_minimal_emg_primary.md",
        "docs/idare_subject_relative_minimal_emg_primary.json",
        "docs/idare_subject_relative_minimal_emg_primary_predictions.csv",
        "docs/idare_subject_relative_minimal_training_report.md",
        "docs/idare_subject_relative_minimal_training_report.json",
    ],
    "pass_criteria": [
        "First pass completes 24 planned diagnostic runs: 2 modalities x 2 tasks x 6 folds x 1 recipe x seed 11.",
        "All first-pass JSON outputs validate.",
        "All first-pass prediction CSV outputs are non-empty.",
        "Every run records subject-relative formulation and retained validation sample count.",
        "No fusion, architecture/DG/augmentation, broad hyperparameter search, final LOSO claim, or mainline change is made.",
        "A combined report compares subject-relative results against the previous global-label mainline baseline at diagnostic level.",
        "The combined report recommends exactly one next objective after human review.",
    ],
    "candidate_next_objectives_after_review": [
        "minimal_subject_relative_balanced_sampler_pass_objective",
        "subject_relative_representation_preprocessing_objective",
        "subject_relative_bsl_stats_sidecar_objective",
        "stop_or_handoff_objective",
    ],
    "not_authorized": [
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "final global label-policy lock",
        "architecture ablation for improvement",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "broad hyperparameter search",
        "mainline change",
        "BSL-stats sidecars in first pass",
    ],
    "next_allowed_step": "Prepare reviewed implementation/run command for the 24-run first-pass minimal subject-relative training matrix.",
}
OBJ_JSON.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

OBJ_MD.write_text(f"""# I-DARE Minimal Subject-relative Training Objective

## Status

Short-term objective created.

This objective authorizes only a minimal controlled diagnostic training first pass.

It does not authorize a final LOSO claim, mainline change, fusion, architecture improvement, augmentation, or domain generalization.

## Why This Objective Exists

The subject-relative task formulation report was reviewed and accepted.

Selected formulation:

`{selected}`

Reason:

- Global binary labels appear unstable under subject-heldout evaluation.
- Subject-relative top/bottom quantile labels are the selected controlled first fix candidate.
- A minimal training run is needed to test whether the task redesign improves subject-heldout macro-F1 / balanced accuracy before considering architecture, fusion, augmentation, or DG.

## Authorized Scope

### Training type

Minimal controlled diagnostic training only.

### Label formulation

`subject_top_bottom_quantile_q33`

Definition:

For each subject and task:

- bottom third of the subject's ratings -> class `0`
- top third of the subject's ratings -> class `1`
- middle third -> discarded

### Modalities

- EEG `STIM-BSL`-only
- EMG feature-only

### Tasks

- valence
- arousal

### Folds

- sidecar-compatible 6 folds
- seed `11`

### First-pass recipe

- `ce_class_weighted`

### First-pass matrix size

24 runs:

`2 modalities x 2 tasks x 6 folds x 1 recipe x seed 11`

### Optional second pass

`balanced_sampler_ce` may be run only after first-pass validation, if outputs are valid and the first pass is not obviously broken.

Optional second pass size:

24 additional runs.

## Implementation Requirements

- Create or patch scripts so subject-relative labels are generated deterministically from existing per-trial valence/arousal ratings.
- Fold splitting must remain sidecar-compatible: `numpy.default_rng(seed=11)`, 6 folds.
- No heldout-subject predictions may be used to define labels.
- Generated outputs must record retained sample counts per task/fold/modality.
- Run EEG and EMG mainlines only.
- Do not include BSL-stats sidecars in this first pass.

## Expected Outputs First Pass

- `docs/idare_subject_relative_minimal_eeg_primary.md`
- `docs/idare_subject_relative_minimal_eeg_primary.json`
- `docs/idare_subject_relative_minimal_eeg_primary_predictions.csv`
- `docs/idare_subject_relative_minimal_emg_primary.md`
- `docs/idare_subject_relative_minimal_emg_primary.json`
- `docs/idare_subject_relative_minimal_emg_primary_predictions.csv`
- `docs/idare_subject_relative_minimal_training_report.md`
- `docs/idare_subject_relative_minimal_training_report.json`

## Pass Criteria

This objective passes only if:

- first pass completes 24 planned diagnostic runs
- all first-pass JSON outputs validate
- all first-pass prediction CSV outputs are non-empty
- every run records subject-relative formulation and retained validation sample count
- no fusion, architecture/DG/augmentation, broad hyperparameter search, final LOSO claim, or mainline change is made
- a combined report compares subject-relative results against the previous global-label mainline baseline at diagnostic level
- the combined report recommends exactly one next objective after human review

## Candidate Next Objectives After Review

- `minimal_subject_relative_balanced_sampler_pass_objective`
- `subject_relative_representation_preprocessing_objective`
- `subject_relative_bsl_stats_sidecar_objective`
- `stop_or_handoff_objective`

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change
- BSL-stats sidecars in first pass

## Next Allowed Step

Prepare reviewed implementation/run command for the 24-run first-pass minimal subject-relative training matrix.
""", encoding="utf-8")

# Update roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
review_row = "| I-DARE subject-relative task formulation review | human review accepted subject-relative formulation; minimal diagnostic training selected next | yes | `docs/idare_subject_relative_task_formulation_review_status.md` | Create/run minimal subject-relative training objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |"
obj_row = "| I-DARE minimal subject-relative training objective | short-term 24-run diagnostic training objective created | yes | `docs/idare_minimal_subject_relative_training_objective.md` | Prepare reviewed implementation/run command for first-pass 24-run matrix. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |"

if "I-DARE subject-relative task formulation review" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE subject-relative task formulation report |"):
            out.append(review_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert subject-relative review row")
    project_md = "\n".join(out) + "\n"

if "I-DARE minimal subject-relative training objective" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE subject-relative task formulation review |"):
            out.append(obj_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert minimal training objective row")
    project_md = "\n".join(out) + "\n"

review_bullet = "- Human review of the subject-relative task formulation report is frozen in `docs/idare_subject_relative_task_formulation_review_status.md`; `subject_top_bottom_quantile_q33` is accepted as the first controlled formulation."
obj_bullet = "- A minimal subject-relative training objective is defined in `docs/idare_minimal_subject_relative_training_objective.md`; next work is a reviewed implementation/run command for the 24-run first-pass matrix."

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
decisions["idare_subject_relative_task_formulation_review_status"] = {
    "status": "frozen_human_review_closeout",
    "evidence": str(REVIEW_MD),
    "evidence_json": str(REVIEW_JSON),
    "reviewed_report": str(REPORT_MD),
    "selected_formulation": selected,
    "selected_next_objective": recommended,
    "training_authorized_by_review": False,
    "not_authorized": review["not_authorized"],
}
decisions["idare_minimal_subject_relative_training_objective"] = {
    "status": "short_term_objective_created",
    "evidence": str(OBJ_MD),
    "evidence_json": str(OBJ_JSON),
    "selected_task_formulation": selected,
    "new_training_authorized": True,
    "first_pass_runs": 24,
    "modalities": objective["authorized_scope"]["modalities"],
    "tasks": objective["authorized_scope"]["tasks"],
    "recipes_first_pass": objective["authorized_scope"]["recipes_first_pass"],
    "expected_outputs_first_pass": objective["expected_outputs_first_pass"],
    "next_allowed_step": objective["next_allowed_step"],
    "not_authorized": objective["not_authorized"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_MINIMAL_SUBJECT_RELATIVE_TRAINING_OBJECTIVE_WRITTEN")
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
    Path("docs/idare_subject_relative_task_formulation_review_status.json"),
    Path("docs/idare_minimal_subject_relative_training_objective.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")
PY

grep -n "## Status\|## Review Decision\|## Next Allowed Step" docs/idare_subject_relative_task_formulation_review_status.md
grep -n "## Status\|## Authorized Scope\|## Expected Outputs First Pass\|## Pass Criteria\|## Next Allowed Step" docs/idare_minimal_subject_relative_training_objective.md
grep -n "subject-relative task formulation review\|minimal subject-relative training objective" docs/project_status_current.md
echo

echo "===== 4) diff stat ====="
git diff --stat
echo

echo "===== 5) status before commit ====="
git status --short --branch
echo

echo "===== 6) commit and push ====="
git add \
  docs/idare_subject_relative_task_formulation_review_status.md \
  docs/idare_subject_relative_task_formulation_review_status.json \
  docs/idare_minimal_subject_relative_training_objective.md \
  docs/idare_minimal_subject_relative_training_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE minimal subject-relative training objective"

git push origin main
echo

echo "===== 7) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_minimal_subject_relative_training_objective.log"
