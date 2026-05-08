#!/usr/bin/env bash
set -euo pipefail

REPO="/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE"
LOG="/tmp/idare_failure_analysis_objective.log"

cd "$REPO"

{
  echo "===== 0) start failure-analysis objective creation ====="
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
import sys, json
print(sys.executable)
print("OK_IMPORTS")
PY

  if [ -n "$(git status --short)" ]; then
    echo "ERROR: repo is not clean. Commit/stash/remove unrelated changes before creating the objective."
    git status --short --branch
    exit 1
  fi
  echo "OK_REPO_CLEAN"
  echo

  echo "===== 2) create failure-analysis objective docs and update roadmap ====="
  "$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
OBJ_MD = DOCS / "idare_failure_analysis_objective.md"
OBJ_JSON = DOCS / "idare_failure_analysis_objective.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()

required = [
    PROJECT_MD,
    PROJECT_JSON,
    DOCS / "idare_label_policy_ablation_report.md",
    DOCS / "idare_label_policy_ablation_report.json",
    DOCS / "idare_label_policy_ablation_review_status.md",
    DOCS / "idare_broader_standardized_single_modality_evaluation_report.md",
    DOCS / "idare_broader_standardized_single_modality_evaluation_report.json",
    DOCS / "idare_broader_standardized_single_modality_evaluation_review_status.md",
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("ERROR missing required files: " + ", ".join(missing))

input_artifacts = {
    "label_policy_ablation": [
        "docs/idare_label_policy_ablation_report.md",
        "docs/idare_label_policy_ablation_report.json",
        "docs/idare_label_policy_ablation_eeg_primary.json",
        "docs/idare_label_policy_ablation_eeg_primary_predictions.csv",
        "docs/idare_label_policy_ablation_emg_primary.json",
        "docs/idare_label_policy_ablation_emg_primary_predictions.csv",
        "docs/idare_label_policy_ablation_review_status.md",
    ],
    "broader_single_modality_eval": [
        "docs/idare_broader_standardized_single_modality_evaluation_report.md",
        "docs/idare_broader_standardized_single_modality_evaluation_report.json",
        "docs/idare_broader_eval_eeg_stim_bsl_only_primary.json",
        "docs/idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv",
        "docs/idare_broader_eval_emg_feature_only_primary.json",
        "docs/idare_broader_eval_emg_feature_only_primary_predictions.csv",
        "docs/idare_broader_standardized_single_modality_evaluation_review_status.md",
    ],
    "optional_context_only": [
        "docs/idare_single_modality_bsl_stats_vs_baseline_comparison.md",
        "docs/idare_single_modality_bsl_stats_vs_baseline_review_status.md",
        "docs/idare_eeg_stim_bsl_only_standardized_status.md",
        "docs/idare_emg_feature_only_status.md",
    ],
}

objective = {
    "status": "short_term_objective_created",
    "created_or_updated_utc": NOW,
    "objective_name": "I-DARE controlled failure analysis objective",
    "evidence_level": "post-hoc analysis of existing smoke/stabilization outputs; no new training",
    "parent_medium_term_objective": (
        "Improve I-DARE single-modality EEG/EMG results by identifying dominant failure modes before "
        "launching architecture, calibration, robustness, augmentation, domain-generalization, or fusion work."
    ),
    "scientific_question": (
        "Given the completed broader single-modality and label-policy matrices, which modality/task/fold/policy/recipe "
        "combinations fail, why do they fail, and what is the most justified next improvement objective?"
    ),
    "technical_questions": [
        "Which folds and subjects are consistently weak across EEG and EMG?",
        "Which runs fail to beat majority baseline on macro-F1, balanced accuracy, or both?",
        "Are failures driven by class imbalance, one-class prediction collapse, probability calibration/threshold issues, or fold-specific subject effects?",
        "Do EEG and EMG fail on the same folds, suggesting dataset/split difficulty, or on different folds, suggesting possible complementary errors?",
        "Does threshold tuning improve macro-F1 without creating unstable one-class predictions?",
        "Which next objective is best supported: threshold/calibration, subject normalization, extra-seed robustness, lightweight architecture, or a carefully scoped fusion-readiness analysis?"
    ],
    "authorized_scope": {
        "new_training": False,
        "new_model_experiment": False,
        "source": "existing committed JSON and prediction CSV reports only",
        "modalities": ["I-DARE EEG mainline", "I-DARE EMG mainline"],
        "tasks": ["valence", "arousal"],
        "label_policies": ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"],
        "recipes": ["ce_class_weighted", "balanced_sampler_ce"],
        "allowed_operations": [
            "read committed reports and prediction CSV files",
            "compute per-fold/per-task/per-modality diagnostics",
            "compare final metrics against majority baselines",
            "inspect threshold diagnostics when already present",
            "summarize failure taxonomy",
            "recommend one next objective",
        ],
    },
    "input_artifacts": input_artifacts,
    "expected_outputs": {
        "markdown_report": "docs/idare_failure_analysis_report.md",
        "json_report": "docs/idare_failure_analysis_report.json",
        "optional_csv": "docs/idare_failure_analysis_fold_summary.csv",
        "closeout_status_after_review": "docs/idare_failure_analysis_review_status.md",
    },
    "minimum_report_contents": [
        "per-modality/task/policy/recipe aggregate table",
        "per-fold weakness map",
        "majority-baseline comparison",
        "one-class/collapse summary",
        "probability/threshold diagnostics summary where available",
        "cross-modality fold-overlap summary",
        "failure taxonomy labels and counts",
        "recommended next objective with rationale",
        "explicit not-authorized list",
    ],
    "pass_criteria": [
        "All required source files are present and readable.",
        "Report covers EEG and EMG, valence and arousal, and all three label policies.",
        "Every conclusion is grounded in existing committed outputs.",
        "No new training, model patch, fusion, final LOSO claim, or final label-policy lock is introduced.",
        "The output identifies either a clear next improvement objective or states that evidence is inconclusive."
    ],
    "failure_taxonomy": {
        "majority_not_beaten": "Run or aggregate fails to beat majority baseline on key balanced metrics.",
        "fold_specific_weakness": "A small set of folds dominates performance loss.",
        "policy_instability": "Best policy changes by modality/task or fold.",
        "recipe_instability": "Best recipe changes without a consistent modality/task pattern.",
        "prediction_collapse_or_skew": "Prediction counts are one-class or highly skewed despite two-class labels.",
        "threshold_sensitive": "Threshold diagnostics improve macro-F1 materially but may indicate calibration instability.",
        "cross_modality_shared_failure": "EEG and EMG are weak on the same fold/task.",
        "cross_modality_complementary_failure": "EEG and EMG are weak on different fold/task cases.",
        "insufficient_evidence": "Existing outputs do not support a stable next action."
    },
    "not_authorized": [
        "new training runs",
        "EEG+EMG fusion",
        "full model(BSL, STIM, STIM-BSL)",
        "final LOSO / final performance claim",
        "locking a final label policy",
        "raw EMG mainline",
        "architecture ablation",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "extra seeds unless a follow-up objective is created",
    ],
    "next_step_after_this_objective": (
        "Prepare a read-only analysis command/script that consumes existing committed outputs and writes "
        "docs/idare_failure_analysis_report.md/json, then review/close out before choosing the next improvement objective."
    ),
}

OBJ_JSON.write_text(json.dumps(objective, indent=2, sort_keys=True) + "\n", encoding="utf-8")

md_lines = [
    "# I-DARE Controlled Failure Analysis Objective",
    "",
    "## Status",
    "",
    "Short-term objective created.",
    "",
    "No new training is authorized by this document.",
    "",
    "This objective is a post-hoc analysis of existing committed smoke/stabilization outputs.",
    "",
    "## Why this objective exists",
    "",
    "The broader standardized single-modality evaluation and the 144-run label-policy ablation are complete and reviewed.",
    "",
    "Both phases showed mixed or weak improvements. Before launching another model experiment, the project needs a controlled failure map.",
    "",
    "## Parent medium-term objective",
    "",
    objective["parent_medium_term_objective"],
    "",
    "## Scientific question",
    "",
    objective["scientific_question"],
    "",
    "## Technical questions",
    "",
]
md_lines.extend(f"{i}. {q}" for i, q in enumerate(objective["technical_questions"], start=1))
md_lines.extend([
    "",
    "## Authorized scope",
    "",
    "- New training: **not authorized**.",
    "- New model experiment: **not authorized**.",
    "- Source: existing committed JSON and prediction CSV reports only.",
    "- Modalities: I-DARE EEG mainline and I-DARE EMG mainline.",
    "- Tasks: valence and arousal.",
    "- Label policies: `discard_midpoint`, `midpoint_as_low`, `midpoint_as_high`.",
    "- Recipes: `ce_class_weighted`, `balanced_sampler_ce`.",
    "",
    "## Input artifacts",
    "",
    "### Label-policy ablation",
    "",
])
md_lines.extend(f"- `{p}`" for p in input_artifacts["label_policy_ablation"])
md_lines.extend([
    "",
    "### Broader single-modality evaluation",
    "",
])
md_lines.extend(f"- `{p}`" for p in input_artifacts["broader_single_modality_eval"])
md_lines.extend([
    "",
    "### Optional context only",
    "",
])
md_lines.extend(f"- `{p}`" for p in input_artifacts["optional_context_only"])
md_lines.extend([
    "",
    "## Expected outputs",
    "",
    "- `docs/idare_failure_analysis_report.md`",
    "- `docs/idare_failure_analysis_report.json`",
    "- Optional: `docs/idare_failure_analysis_fold_summary.csv`",
    "- After human review: `docs/idare_failure_analysis_review_status.md`",
    "",
    "## Minimum report contents",
    "",
])
md_lines.extend(f"- {item}" for item in objective["minimum_report_contents"])
md_lines.extend([
    "",
    "## Pass criteria",
    "",
])
md_lines.extend(f"- {item}" for item in objective["pass_criteria"])
md_lines.extend([
    "",
    "## Failure taxonomy",
    "",
    "| Failure type | Meaning |",
    "|---|---|",
])
for key, value in objective["failure_taxonomy"].items():
    md_lines.append(f"| `{key}` | {value} |")
md_lines.extend([
    "",
    "## Not authorized",
    "",
])
md_lines.extend(f"- {item}" for item in objective["not_authorized"])
md_lines.extend([
    "",
    "## Next step after this objective",
    "",
    objective["next_step_after_this_objective"],
    "",
])
OBJ_MD.write_text("\n".join(md_lines), encoding="utf-8")

# Update markdown roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")

new_row = "| I-DARE controlled failure analysis objective | short-term post-hoc analysis objective created; no new training authorized | yes | `docs/idare_failure_analysis_objective.md` | Prepare read-only analysis script/command for existing JSON/CSV outputs. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; final label-policy lock. |"

if new_row not in project_md:
    anchor = "| EEG+EMG fusion | not started intentionally | no |"
    if anchor in project_md:
        project_md = project_md.replace(anchor, new_row + "\n" + anchor)
    else:
        project_md += "\n" + new_row + "\n"

decision_bullet = "- A controlled I-DARE failure-analysis objective is defined in `docs/idare_failure_analysis_objective.md`; next work is read-only analysis of existing outputs, not new training or fusion."
if decision_bullet not in project_md:
    marker = "## Documentation Gap Closed by This File"
    if marker in project_md:
        project_md = project_md.replace(marker, decision_bullet + "\n\n" + marker)
    else:
        project_md += "\n" + decision_bullet + "\n"

PROJECT_MD.write_text(project_md, encoding="utf-8")

# Update JSON roadmap.
project = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
project.setdefault("decisions", {})
project["decisions"]["idare_failure_analysis_objective"] = {
    "status": "short_term_objective_created",
    "evidence": str(OBJ_MD),
    "evidence_json": str(OBJ_JSON),
    "evidence_level": objective["evidence_level"],
    "new_training_authorized": False,
    "scope": objective["authorized_scope"],
    "expected_outputs": objective["expected_outputs"],
    "next_allowed_step": objective["next_step_after_this_objective"],
    "not_authorized": objective["not_authorized"],
}
project["failure_analysis_objective"] = {
    "status": "created",
    "evidence": str(OBJ_MD),
    "new_training_authorized": False,
    "next_allowed_step": objective["next_step_after_this_objective"],
}
PROJECT_JSON.write_text(json.dumps(project, indent=2, sort_keys=True) + "\n", encoding="utf-8")

print("OK_FAILURE_ANALYSIS_OBJECTIVE_WRITTEN")
print(OBJ_MD)
print(OBJ_JSON)
PY
  echo

  echo "===== 3) validate docs ====="
  "$PY" - <<'PY'
import json
from pathlib import Path
for p in [
    Path("docs/idare_failure_analysis_objective.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")
PY

  grep -n "## Status\|## Scientific question\|## Authorized scope\|## Pass criteria\|## Next step after this objective" docs/idare_failure_analysis_objective.md
  grep -n "I-DARE controlled failure analysis objective\|failure-analysis objective" docs/project_status_current.md
  echo

  echo "===== 4) diff stat ====="
  git diff --stat
  echo

  echo "===== 5) status before commit ====="
  git status --short --branch
  echo

  echo "===== 6) commit and push objective ====="
  git add \
    docs/idare_failure_analysis_objective.md \
    docs/idare_failure_analysis_objective.json \
    docs/project_status_current.md \
    docs/project_status_current.json

  git commit -m "docs: add I-DARE failure analysis objective"
  git push origin main
  echo

  echo "===== 7) final status ====="
  git status --short --branch
  echo "LOG_SAVED_TO=$LOG"
} 2>&1 | tee "$LOG"
