#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start root-cause review + diagnostic sanity objective ====="
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
  echo "ERROR: repo is not clean; commit/stash current changes before creating the diagnostic sanity objective."
  git status --short --branch
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) create root-cause review closeout + diagnostic sanity objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
ROOT_REVIEW_MD = DOCS / "idare_root_cause_diagnostic_review_status.md"
ROOT_REVIEW_JSON = DOCS / "idare_root_cause_diagnostic_review_status.json"
SANITY_MD = DOCS / "idare_diagnostic_sanity_tests_objective.md"
SANITY_JSON = DOCS / "idare_diagnostic_sanity_tests_objective.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()

required = [
    DOCS / "idare_root_cause_diagnostic_report.md",
    DOCS / "idare_root_cause_diagnostic_report.json",
    DOCS / "idare_root_cause_subject_summary.csv",
    DOCS / "idare_root_cause_calibration_summary.csv",
    DOCS / "idare_root_cause_error_overlap_summary.csv",
    DOCS / "idare_root_cause_diagnostic_objective.md",
    DOCS / "idare_failure_analysis_review_status.md",
    PROJECT_MD,
    PROJECT_JSON,
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("ERROR: missing required files:\n" + "\n".join(missing))

root_report = json.loads((DOCS / "idare_root_cause_diagnostic_report.json").read_text(encoding="utf-8"))
ranking = root_report.get("root_cause_ranking", [])
recommended = root_report.get("recommended_next_objective")

root_review = {
    "status": "frozen_human_review_closeout",
    "created_or_updated_utc": NOW,
    "reviewed_report": "docs/idare_root_cause_diagnostic_report.md",
    "reviewed_json": "docs/idare_root_cause_diagnostic_report.json",
    "review_decision": {
        "accepted": True,
        "recommended_next_objective_accepted": recommended == "diagnostic_sanity_tests_objective",
        "selected_next_objective": "diagnostic_sanity_tests_objective",
        "new_performance_training_authorized": False,
        "diagnostic_sanity_tests_authorized_next": True,
        "fusion_authorized": False,
        "architecture_or_dg_authorized": False,
        "final_label_policy_authorized": False,
    },
    "accepted_findings": {
        "top_ranked_causes": ranking[:5],
        "summary": [
            "Read-only evidence points most strongly to subject/fold generalization and representation weakness.",
            "Model/pipeline learning failure cannot be ruled out from read-only outputs.",
            "Calibration/threshold and label/task sensitivity are also present, but are not sufficient explanations alone.",
            "Blind training should remain paused until diagnostic sanity tests localize whether the pipeline can learn signal at all.",
        ],
    },
    "not_authorized": [
        "new performance training",
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "final global label-policy lock",
        "architecture ablation",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "mainline change",
    ],
}

ROOT_REVIEW_JSON.write_text(json.dumps(root_review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

ROOT_REVIEW_MD.write_text("""# I-DARE Root-Cause Diagnostic Review Status

## Status

Frozen human-review closeout.

The read-only root-cause diagnostic report has been reviewed and accepted.

Reviewed report: `docs/idare_root_cause_diagnostic_report.md`

Reviewed JSON: `docs/idare_root_cause_diagnostic_report.json`

## Review Decision

The report is accepted.

Selected next objective:

`diagnostic_sanity_tests_objective`

Reason:

The read-only report strongly suggests subject/fold generalization difficulty and representation weakness, but it cannot rule out a model/pipeline learning issue.

Therefore, before proposing any fix, we need diagnostic-only sanity tests.

## Accepted Findings

- The current evidence does not support another blind training sweep.
- Subject/fold generalization is the highest-ranked likely issue.
- Representation weakness is also highly plausible.
- Model/pipeline learning failure cannot be ruled out from read-only outputs.
- Calibration/threshold issues exist but do not explain everything alone.
- Label/task definition sensitivity exists but does not explain everything alone.

## Next Allowed Step

Create and run a controlled diagnostic-sanity-tests objective.

These tests are allowed only as diagnosis, not as performance training.

## Intentionally Not Started

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation
- data augmentation
- SupCon / VREx / domain generalization
- mainline change
""", encoding="utf-8")

sanity_obj = {
    "status": "short_term_objective_created",
    "created_or_updated_utc": NOW,
    "objective": "I-DARE diagnostic sanity tests objective",
    "evidence_level": "diagnostic-only objective after human-reviewed root-cause report; no performance claim",
    "source_checkpoint": {
        "root_cause_review": "docs/idare_root_cause_diagnostic_review_status.md",
        "root_cause_report": "docs/idare_root_cause_diagnostic_report.md",
        "root_cause_json": "docs/idare_root_cause_diagnostic_report.json",
    },
    "scientific_question": (
        "Can the current I-DARE data/model pipeline learn any usable signal under controlled sanity conditions, "
        "or are the near-chance results caused by cross-subject generalization difficulty, representation weakness, "
        "label/task noise, calibration, or a pipeline/model learning failure?"
    ),
    "authorized_scope": {
        "diagnostic_only": True,
        "new_performance_training": False,
        "final_claim": False,
        "tests": [
            {
                "id": "micro_overfit_subset",
                "purpose": "Check whether each mainline model can memorize a small clean subset.",
                "interpretation": {
                    "passes": "Training/data feeding/model/loss can learn at least local signal.",
                    "fails": "Strong evidence for pipeline/model/loss/data-feeding issue.",
                },
                "allowed_modalities": ["EEG STIM-BSL-only", "EMG feature-only"],
                "allowed_tasks": ["valence", "arousal"],
                "allowed_policy": "midpoint_as_high continuity/default only",
                "allowed_scope": "small subset, diagnostic-only, no validation claim",
            },
            {
                "id": "shuffled_label_negative_control",
                "purpose": "Check for leakage or suspicious behavior under randomized labels.",
                "interpretation": {
                    "passes": "Performance stays near chance/majority under shuffled labels.",
                    "fails": "Potential leakage, split bug, or metric/reporting bug.",
                },
                "allowed_modalities": ["EEG STIM-BSL-only", "EMG feature-only"],
                "allowed_tasks": ["valence", "arousal"],
                "allowed_policy": "midpoint_as_high continuity/default only",
                "allowed_scope": "diagnostic-only negative control",
            },
            {
                "id": "within_subject_vs_subject_heldout_contrast",
                "purpose": "Separate learnability from cross-subject generalization difficulty.",
                "interpretation": {
                    "within_subject_good_subject_heldout_bad": "Primary issue is subject/domain generalization.",
                    "both_bad": "Representation, label/task, or pipeline learning issue remains likely.",
                },
                "allowed_modalities": ["EEG STIM-BSL-only", "EMG feature-only"],
                "allowed_tasks": ["valence", "arousal"],
                "allowed_policy": "midpoint_as_high continuity/default only",
                "allowed_scope": "diagnostic contrast, no final performance claim",
            },
            {
                "id": "simple_classical_baseline",
                "purpose": "Check whether simple models on existing features can beat the neural setup or reveal linearly available signal.",
                "interpretation": {
                    "classical_better": "Neural setup/training may be weak.",
                    "classical_also_chance": "Representation/label/generalization issue is more likely.",
                },
                "allowed_modalities": ["EMG feature-only", "EEG simple summary features derived from existing cache if script already supports or patch is limited"],
                "allowed_tasks": ["valence", "arousal"],
                "allowed_policy": "midpoint_as_high continuity/default only",
                "allowed_scope": "diagnostic baseline only",
            },
        ],
    },
    "expected_outputs": [
        "docs/idare_diagnostic_sanity_tests_report.md",
        "docs/idare_diagnostic_sanity_tests_report.json",
        "docs/idare_diagnostic_sanity_tests_summary.csv",
        "optional docs/idare_diagnostic_sanity_tests_predictions.csv only if needed and not too large",
    ],
    "pass_criteria": [
        "The command/script runs only diagnostic sanity tests, not performance-training experiments.",
        "Outputs include pass/fail interpretation for micro-overfit, shuffled-label control, within-subject contrast, and classical baseline.",
        "The report explicitly states whether model/pipeline learning issue is supported, weakened, or still unresolved.",
        "The report distinguishes subject/domain generalization difficulty from total learnability failure.",
        "The report recommends exactly one next objective after review.",
        "No fusion, architecture, augmentation, DG, or final claim is started.",
    ],
    "stop_conditions": [
        "If micro-overfit fails, stop and recommend pipeline/data-feeding/loss audit.",
        "If shuffled-label control performs suspiciously above chance, stop and recommend leakage/split audit.",
        "If within-subject is strong but subject-heldout weak, recommend subject-generalization objective.",
        "If all diagnostics remain near chance, recommend representation/label-task redesign objective.",
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
    ],
    "next_allowed_step": "Prepare a reviewed command/script that runs the diagnostic sanity tests and writes the diagnostic report.",
}

SANITY_JSON.write_text(json.dumps(sanity_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

SANITY_MD.write_text("""# I-DARE Diagnostic Sanity Tests Objective

## Status

Short-term objective created.

This is diagnostic-only.

No performance-training claim is authorized.

## Why this objective exists

The read-only root-cause diagnostic report was reviewed.

It showed that subject/fold generalization and representation weakness are likely, but a model/pipeline learning issue cannot be ruled out.

Before proposing fixes, we need sanity tests that answer a simpler question:

Can the current pipeline learn any usable signal under controlled conditions?

## Scientific Question

Can the current I-DARE EEG/EMG data/model pipeline learn signal at all?

Or are near-chance results caused by:

1. subject/fold generalization difficulty
2. representation weakness
3. label/task noise
4. calibration/threshold weakness
5. model/pipeline learning failure

## Authorized Tests

### 1. Micro-overfit subset test

Purpose:

Check whether each mainline model can memorize a small clean subset.

Interpretation:

- Pass: training/data feeding/model/loss can learn at least local signal.
- Fail: strong evidence for pipeline/model/loss/data-feeding issue.

Allowed scope:

- EEG `STIM-BSL`-only
- EMG feature-only
- valence and arousal
- `midpoint_as_high` continuity/default policy only
- small subset
- diagnostic-only

### 2. Shuffled-label negative control

Purpose:

Check for leakage or suspicious behavior under randomized labels.

Interpretation:

- Pass: performance stays near chance/majority.
- Fail: potential leakage, split bug, or metric/reporting bug.

### 3. Within-subject vs subject-heldout contrast

Purpose:

Separate learnability from cross-subject generalization difficulty.

Interpretation:

- within-subject good and subject-heldout bad: subject/domain generalization is the likely core issue.
- both bad: representation, label/task, or pipeline learning issue remains likely.

### 4. Simple classical baseline

Purpose:

Check whether simple models on existing features can beat the neural setup or reveal linearly available signal.

Interpretation:

- classical better than neural: neural setup/training may be weak.
- classical also near chance: representation/label/generalization issue is more likely.

## Expected Outputs

- `docs/idare_diagnostic_sanity_tests_report.md`
- `docs/idare_diagnostic_sanity_tests_report.json`
- `docs/idare_diagnostic_sanity_tests_summary.csv`
- optional `docs/idare_diagnostic_sanity_tests_predictions.csv` only if needed and not too large

## Pass Criteria

The objective passes only if the report:

- runs diagnostic sanity tests only
- gives pass/fail interpretation for each test
- states whether model/pipeline learning failure is supported, weakened, or unresolved
- distinguishes subject/domain generalization difficulty from total learnability failure
- recommends exactly one next objective after review
- does not start fusion, architecture, augmentation, DG, or final claim work

## Stop Conditions

- If micro-overfit fails: stop and recommend pipeline/data-feeding/loss audit.
- If shuffled-label control performs suspiciously above chance: stop and recommend leakage/split audit.
- If within-subject is strong but subject-heldout is weak: recommend subject-generalization objective.
- If all diagnostics remain near chance: recommend representation/label-task redesign objective.

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

Prepare a reviewed command/script that runs these diagnostic sanity tests and writes the diagnostic report.
""", encoding="utf-8")

# Update central roadmap Markdown.
project_md = PROJECT_MD.read_text(encoding="utf-8")

review_row = "| I-DARE root-cause diagnostic review | human review accepted read-only root-cause report; diagnostic sanity tests selected next | yes | `docs/idare_root_cause_diagnostic_review_status.md` | Create/run diagnostic sanity tests objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |"
sanity_row = "| I-DARE diagnostic sanity tests objective | short-term diagnostic-only objective created; no performance training claim authorized | yes | `docs/idare_diagnostic_sanity_tests_objective.md` | Prepare reviewed diagnostic sanity command/script. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |"

if "I-DARE root-cause diagnostic review" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE root-cause diagnostic report |"):
            out.append(review_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert root-cause review row")
    project_md = "\n".join(out) + "\n"

if "I-DARE diagnostic sanity tests objective" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE root-cause diagnostic review |"):
            out.append(sanity_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert diagnostic sanity objective row")
    project_md = "\n".join(out) + "\n"

review_bullet = "- Human review of the I-DARE root-cause diagnostic report is frozen in `docs/idare_root_cause_diagnostic_review_status.md`; diagnostic sanity tests are selected as the next controlled step."
sanity_bullet = "- A diagnostic-only I-DARE sanity-tests objective is defined in `docs/idare_diagnostic_sanity_tests_objective.md`; next work is a reviewed command/script, not performance training or fusion."

if review_bullet not in project_md or sanity_bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: project status marker not found")
    block = ""
    if review_bullet not in project_md:
        block += "\n" + review_bullet + "\n"
    if sanity_bullet not in project_md:
        block += "\n" + sanity_bullet + "\n"
    project_md = project_md.replace(marker, block + marker)

PROJECT_MD.write_text(project_md, encoding="utf-8")

# Update central roadmap JSON.
project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})

decisions["idare_root_cause_diagnostic_review_status"] = {
    "status": "frozen_human_review_closeout",
    "evidence": "docs/idare_root_cause_diagnostic_review_status.md",
    "evidence_json": "docs/idare_root_cause_diagnostic_review_status.json",
    "reviewed_report": "docs/idare_root_cause_diagnostic_report.md",
    "selected_next_objective": "diagnostic_sanity_tests_objective",
    "new_performance_training_authorized": False,
    "not_authorized": root_review["not_authorized"],
}

decisions["idare_diagnostic_sanity_tests_objective"] = {
    "status": "short_term_objective_created",
    "evidence": "docs/idare_diagnostic_sanity_tests_objective.md",
    "evidence_json": "docs/idare_diagnostic_sanity_tests_objective.json",
    "diagnostic_only": True,
    "new_performance_training_authorized": False,
    "authorized_tests": [t["id"] for t in sanity_obj["authorized_scope"]["tests"]],
    "expected_outputs": sanity_obj["expected_outputs"],
    "next_allowed_step": sanity_obj["next_allowed_step"],
    "not_authorized": sanity_obj["not_authorized"],
}

PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_DIAGNOSTIC_SANITY_OBJECTIVE_WRITTEN")
print(ROOT_REVIEW_MD)
print(ROOT_REVIEW_JSON)
print(SANITY_MD)
print(SANITY_JSON)
PY
echo

echo "===== 3) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
for p in [
    Path("docs/idare_root_cause_diagnostic_review_status.json"),
    Path("docs/idare_diagnostic_sanity_tests_objective.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")
PY

grep -n "## Status\|## Review Decision\|## Next Allowed Step" docs/idare_root_cause_diagnostic_review_status.md
grep -n "## Status\|## Scientific Question\|## Authorized Tests\|## Pass Criteria\|## Next Allowed Step" docs/idare_diagnostic_sanity_tests_objective.md
grep -n "root-cause diagnostic review\|diagnostic sanity tests objective" docs/project_status_current.md
echo

echo "===== 4) diff stat ====="
git diff --stat
echo

echo "===== 5) status before commit ====="
git status --short --branch
echo

echo "===== 6) commit and push diagnostic sanity objective ====="
git add \
  docs/idare_root_cause_diagnostic_review_status.md \
  docs/idare_root_cause_diagnostic_review_status.json \
  docs/idare_diagnostic_sanity_tests_objective.md \
  docs/idare_diagnostic_sanity_tests_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE diagnostic sanity tests objective"

git push origin main
echo

echo "===== 7) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_diagnostic_sanity_objective.log"
