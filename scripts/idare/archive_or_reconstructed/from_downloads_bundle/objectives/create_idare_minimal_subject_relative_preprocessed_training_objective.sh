#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start representation/preprocessing review + minimal preprocessed training objective ====="
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
  echo "ERROR: repo is not clean; commit/stash current changes before creating review/objective."
  git status --short --branch
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) create review closeout + minimal preprocessed training objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")

REVIEW_MD = DOCS / "idare_subject_relative_representation_preprocessing_review_status.md"
REVIEW_JSON = DOCS / "idare_subject_relative_representation_preprocessing_review_status.json"
OBJECTIVE_MD = DOCS / "idare_minimal_subject_relative_preprocessed_training_objective.md"
OBJECTIVE_JSON = DOCS / "idare_minimal_subject_relative_preprocessed_training_objective.json"

REPORT_MD = DOCS / "idare_subject_relative_representation_preprocessing_report.md"
REPORT_JSON = DOCS / "idare_subject_relative_representation_preprocessing_report.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()

report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
best = report.get("best_candidate", {})
diagnosis = report.get("diagnosis", "unknown")
recommended = report.get("recommended_next_objective", "unknown")

review = {
    "status": "frozen_human_review_closeout",
    "created_or_updated_utc": NOW,
    "reviewed_document": str(REPORT_MD),
    "reviewed_json": str(REPORT_JSON),
    "evidence_level": "human-reviewed read-only representation/preprocessing diagnostic; no final performance claim",
    "human_review_decision": {
        "accepted": True,
        "mainline_changed": False,
        "best_candidate_accepted_for_minimal_test": True,
        "next_objective": "minimal_subject_relative_preprocessed_training_objective",
        "new_training_authorized_by_this_review": False,
    },
    "rationale": {
        "diagnosis": diagnosis,
        "recommended_next_objective": recommended,
        "best_candidate": best,
        "note": "The diagnostic found a low-leakage preprocessing candidate worth testing, but training still requires a separate explicit objective.",
    },
    "not_authorized": [
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "mainline change",
        "architecture ablation for improvement",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "broad hyperparameter search",
        "balanced-sampler second pass",
        "BSL-stats sidecars",
    ],
    "next_allowed_step": "Create a minimal subject-relative preprocessed training objective; then prepare a reviewed implementation/run command.",
}
REVIEW_JSON.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def fmt(x):
    try:
        return f"{float(x):.4f}"
    except Exception:
        return str(x)

lines = []
lines.append("# I-DARE Subject-relative Representation/Preprocessing Review Status")
lines.append("")
lines.append("## Status")
lines.append("")
lines.append("Frozen human review closeout.")
lines.append("")
lines.append(f"Created/updated UTC: `{NOW}`")
lines.append("")
lines.append("## Reviewed Evidence")
lines.append("")
lines.append(f"- Report: `{REPORT_MD}`")
lines.append(f"- JSON: `{REPORT_JSON}`")
lines.append("")
lines.append("## Review Decision")
lines.append("")
lines.append("The read-only representation/preprocessing diagnostic is accepted as completed and reviewed.")
lines.append("")
lines.append("Decision:")
lines.append("")
lines.append("- Accept that at least one low-leakage preprocessing candidate is worth a minimal controlled training test.")
lines.append("- Do not change mainline yet.")
lines.append("- Do not run broad search, fusion, architecture work, augmentation, or domain generalization.")
lines.append("- Create a minimal subject-relative preprocessed training objective as the next step.")
lines.append("")
lines.append("## Result Summary")
lines.append("")
lines.append(f"- Diagnosis: `{diagnosis}`")
lines.append(f"- Recommended next objective: `{recommended}`")
lines.append(f"- Best candidate: `{best.get('candidate')}`")
lines.append(f"- Best candidate modality: `{best.get('modality')}`")
lines.append(f"- Diagnostic score: `{fmt(best.get('diagnostic_score'))}`")
lines.append(f"- Mean shift reduction vs raw: `{fmt(best.get('mean_shift_reduction_vs_raw'))}`")
lines.append(f"- Mean validation-separation gain vs raw: `{fmt(best.get('mean_val_sep_gain_vs_raw'))}`")
lines.append("")
lines.append("## Not Authorized")
lines.append("")
for item in review["not_authorized"]:
    lines.append(f"- {item}")
lines.append("")
lines.append("## Next Allowed Step")
lines.append("")
lines.append(review["next_allowed_step"])
lines.append("")
REVIEW_MD.write_text("\n".join(lines), encoding="utf-8")

objective = {
    "status": "short_term_objective_created",
    "created_or_updated_utc": NOW,
    "objective_name": "I-DARE minimal subject-relative preprocessed training objective",
    "triggering_review": str(REVIEW_MD),
    "triggering_report": str(REPORT_MD),
    "evidence_level": "minimal diagnostic training objective; no final LOSO claim; no mainline change",
    "formulation": "subject_top_bottom_quantile_q33",
    "authorized_scope": {
        "total_runs": 24,
        "modalities": ["EEG", "EMG"],
        "tasks": ["valence", "arousal"],
        "folds": 6,
        "seeds": [11],
        "recipes": ["ce_class_weighted"],
        "label_formulation": "per-subject bottom third vs top third; middle third discarded",
        "preprocessing_candidates": {
            "EEG": {
                "candidate": "eeg_window_channel_zscore_train_standard_scaled",
                "description": "per-trial channel zscore summary features plus train-only standard scaling",
                "source_rank_in_diagnostic": 3,
            },
            "EMG": {
                "candidate": "emg_signed_log1p_train_standard_scaled",
                "description": "signed log1p EMG features plus train-only standard scaling",
                "source_rank_in_diagnostic": 1,
            },
        },
    },
    "authorized_work": [
        "Create a small reviewed implementation/run script for the 24-run first pass.",
        "Use the same subject-relative q33 label formulation already audited.",
        "Apply preprocessing with train-only fit where scaling is needed.",
        "For EEG, use a minimal summary-feature pipeline based on per-trial channel zscore plus train-only standard scaling.",
        "For EMG, use signed log1p feature transform plus train-only standard scaling.",
        "Write predictions, JSON, markdown report, and retained validation counts.",
        "Compare against the previous subject-relative minimal run and the global-label mainline.",
    ],
    "expected_outputs": [
        "docs/idare_subject_relative_preprocessed_minimal_eeg_primary.md",
        "docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json",
        "docs/idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv",
        "docs/idare_subject_relative_preprocessed_minimal_emg_primary.md",
        "docs/idare_subject_relative_preprocessed_minimal_emg_primary.json",
        "docs/idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv",
        "docs/idare_subject_relative_preprocessed_minimal_training_report.md",
        "docs/idare_subject_relative_preprocessed_minimal_training_report.json",
    ],
    "pass_criteria": [
        "Exactly 24 planned runs are executed or explicitly failed with a logged reason.",
        "No heldout-subject leakage is introduced; all scaling is fitted on train folds only.",
        "Every run records fold, seed, task, modality, preprocessing candidate, retained train samples, and retained validation samples.",
        "No one-class prediction collapse in more than one run per modality/task.",
        "Report compares macro-F1 and balanced accuracy against prior subject-relative minimal training and global-label mainline.",
        "Report recommends exactly one next objective after human review.",
    ],
    "candidate_next_objectives_after_review": [
        "subject_relative_preprocessed_training_review_closeout",
        "preprocessed_balanced_sampler_second_pass_objective",
        "subject_relative_feature_engineering_objective",
        "stop_or_handoff_objective",
    ],
    "not_authorized": review["not_authorized"],
    "next_allowed_step": "Prepare a reviewed implementation/run command for the 24-run minimal subject-relative preprocessed first pass.",
}
OBJECTIVE_JSON.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = []
md.append("# I-DARE Minimal Subject-relative Preprocessed Training Objective")
md.append("")
md.append("## Status")
md.append("")
md.append("Short-term diagnostic training objective created.")
md.append("")
md.append(f"Created/updated UTC: `{NOW}`")
md.append("")
md.append("This objective authorizes only a small 24-run first pass. It does not authorize final LOSO claims, fusion, mainline changes, architecture work, augmentation, domain generalization, or broad hyperparameter search.")
md.append("")
md.append("## Why This Objective Exists")
md.append("")
md.append("The subject-relative representation/preprocessing diagnostic was reviewed.")
md.append("")
md.append("The diagnostic identified a low-leakage preprocessing candidate worth minimal testing.")
md.append("")
md.append("## Authorized Scope")
md.append("")
md.append("- Total runs: `24`")
md.append("- Modalities: `EEG`, `EMG`")
md.append("- Tasks: `valence`, `arousal`")
md.append("- Folds: `6`")
md.append("- Seed: `11`")
md.append("- Recipe: `ce_class_weighted` only")
md.append("- Label formulation: `subject_top_bottom_quantile_q33`")
md.append("")
md.append("## Preprocessing Candidates")
md.append("")
md.append("| Modality | Candidate | Description | Diagnostic source rank |")
md.append("|---|---|---|---:|")
for modality, row in objective["authorized_scope"]["preprocessing_candidates"].items():
    md.append(f"| {modality} | `{row['candidate']}` | {row['description']} | {row['source_rank_in_diagnostic']} |")
md.append("")
md.append("## Authorized Work")
md.append("")
for item in objective["authorized_work"]:
    md.append(f"- {item}")
md.append("")
md.append("## Expected Outputs")
md.append("")
for item in objective["expected_outputs"]:
    md.append(f"- `{item}`")
md.append("")
md.append("## Pass Criteria")
md.append("")
for item in objective["pass_criteria"]:
    md.append(f"- {item}")
md.append("")
md.append("## Candidate Next Objectives After Review")
md.append("")
for item in objective["candidate_next_objectives_after_review"]:
    md.append(f"- `{item}`")
md.append("")
md.append("## Not Authorized")
md.append("")
for item in objective["not_authorized"]:
    md.append(f"- {item}")
md.append("")
md.append("## Next Allowed Step")
md.append("")
md.append(objective["next_allowed_step"])
md.append("")
OBJECTIVE_MD.write_text("\n".join(md), encoding="utf-8")

project_md = PROJECT_MD.read_text(encoding="utf-8")
rows = [
    "| I-DARE subject-relative representation/preprocessing review | human review accepted preprocessing diagnostic; minimal preprocessed training selected next | yes | `docs/idare_subject_relative_representation_preprocessing_review_status.md` | Create/run minimal subject-relative preprocessed training objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |",
    "| I-DARE minimal subject-relative preprocessed training objective | short-term 24-run diagnostic training objective created | yes | `docs/idare_minimal_subject_relative_preprocessed_training_objective.md` | Prepare reviewed implementation/run command for the 24-run first pass. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |",
]

if "I-DARE minimal subject-relative preprocessed training objective" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE subject-relative representation/preprocessing report |"):
            out.extend(rows)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert roadmap rows")
    project_md = "\n".join(out) + "\n"

bullet = "- Human review of the subject-relative representation/preprocessing diagnostic is frozen in `docs/idare_subject_relative_representation_preprocessing_review_status.md`; minimal subject-relative preprocessed training is selected next."
bullet2 = "- A minimal subject-relative preprocessed training objective is defined in `docs/idare_minimal_subject_relative_preprocessed_training_objective.md`; next work is a reviewed implementation/run command for the 24-run first pass."
for b in [bullet, bullet2]:
    if b not in project_md:
        marker = "\n## Documentation Gap Closed by This File"
        if marker not in project_md:
            raise SystemExit("ERROR: project status marker not found")
        project_md = project_md.replace(marker, "\n" + b + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_subject_relative_representation_preprocessing_review"] = {
    "status": "frozen_human_review_closeout",
    "evidence": str(REVIEW_MD),
    "evidence_json": str(REVIEW_JSON),
    "decision": review["human_review_decision"],
    "not_authorized": review["not_authorized"],
}
decisions["idare_minimal_subject_relative_preprocessed_training_objective"] = {
    "status": "short_term_objective_created",
    "evidence": str(OBJECTIVE_MD),
    "evidence_json": str(OBJECTIVE_JSON),
    "authorized_scope": objective["authorized_scope"],
    "next_allowed_step": objective["next_allowed_step"],
    "not_authorized": objective["not_authorized"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_MINIMAL_PREPROCESSED_TRAINING_OBJECTIVE_WRITTEN")
print(REVIEW_MD)
print(REVIEW_JSON)
print(OBJECTIVE_MD)
print(OBJECTIVE_JSON)
PY
echo

echo "===== 3) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path

for p in [
    Path("docs/idare_subject_relative_representation_preprocessing_review_status.json"),
    Path("docs/idare_minimal_subject_relative_preprocessed_training_objective.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)
PY

grep -n "## Status\|## Review Decision\|## Result Summary\|## Next Allowed Step" docs/idare_subject_relative_representation_preprocessing_review_status.md
grep -n "## Status\|## Authorized Scope\|## Preprocessing Candidates\|## Expected Outputs\|## Pass Criteria\|## Next Allowed Step" docs/idare_minimal_subject_relative_preprocessed_training_objective.md
grep -n "minimal subject-relative preprocessed\|representation/preprocessing review" docs/project_status_current.md
echo

echo "===== 4) diff stat ====="
git diff --stat
echo

echo "===== 5) status before commit ====="
git status --short --branch
echo

echo "===== 6) commit and push ====="
git add \
  docs/idare_subject_relative_representation_preprocessing_review_status.md \
  docs/idare_subject_relative_representation_preprocessing_review_status.json \
  docs/idare_minimal_subject_relative_preprocessed_training_objective.md \
  docs/idare_minimal_subject_relative_preprocessed_training_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE minimal preprocessed training objective"

git push origin main
echo

echo "===== 7) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_minimal_preprocessed_training_objective.log"
