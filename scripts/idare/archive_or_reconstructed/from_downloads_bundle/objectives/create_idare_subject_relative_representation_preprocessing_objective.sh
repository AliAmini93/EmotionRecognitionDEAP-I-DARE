#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start subject-relative minimal review + representation preprocessing objective ====="
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

echo "===== 2) create review closeout + representation preprocessing objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
REVIEW_MD = DOCS / "idare_subject_relative_minimal_training_review_status.md"
REVIEW_JSON = DOCS / "idare_subject_relative_minimal_training_review_status.json"
OBJECTIVE_MD = DOCS / "idare_subject_relative_representation_preprocessing_objective.md"
OBJECTIVE_JSON = DOCS / "idare_subject_relative_representation_preprocessing_objective.json"
REPORT_MD = DOCS / "idare_subject_relative_minimal_training_report.md"
REPORT_JSON = DOCS / "idare_subject_relative_minimal_training_report.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()

report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
comparison = report.get("comparison_against_global_label_mainline", [])
diagnosis = report.get("diagnosis", "unknown")
recommended = report.get("recommended_next_objective", "subject_relative_representation_preprocessing_objective")

def fmt_float(x):
    if x is None:
        return "NA"
    return f"{float(x):.4f}"

review = {
    "status": "frozen_human_review_closeout",
    "created_or_updated_utc": NOW,
    "reviewed_document": str(REPORT_MD),
    "reviewed_json": str(REPORT_JSON),
    "evidence_level": "human-reviewed minimal diagnostic training; no final LOSO claim; no mainline change",
    "human_review_decision": {
        "accepted": True,
        "mainline_changed": False,
        "subject_relative_formulation_accepted_as_tested": True,
        "subject_relative_first_pass_promoted": False,
        "balanced_sampler_second_pass_authorized": False,
        "next_objective": "subject_relative_representation_preprocessing_objective",
    },
    "rationale": {
        "diagnosis": diagnosis,
        "mean_delta_macro_f1": report.get("comparison_summary", {}).get("mean_delta_macro_f1"),
        "note": "The subject-relative q33 first pass did not improve enough over the prior global-label mainline; only one modality/task cell was positive and the recommended next objective is representation/preprocessing.",
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
        "BSL-stats sidecars",
        "balanced-sampler second pass before a separate objective",
    ],
    "next_allowed_step": "Create a representation/preprocessing diagnostic objective and then prepare a reviewed command/script.",
}
REVIEW_JSON.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

lines = []
lines.append("# I-DARE Subject-relative Minimal Training Review Status")
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
lines.append("The 24-run minimal subject-relative first pass is accepted as completed and reviewed.")
lines.append("")
lines.append("Decision:")
lines.append("")
lines.append("- Do not promote subject-relative q33 as a mainline change.")
lines.append("- Do not run the optional balanced-sampler second pass yet.")
lines.append("- Do not start fusion or final LOSO claims.")
lines.append("- Move to a controlled representation/preprocessing objective.")
lines.append("")
lines.append("## Result Summary")
lines.append("")
lines.append(f"- Diagnosis: `{diagnosis}`")
lines.append(f"- Recommended next objective in the report: `{recommended}`")
lines.append("")
lines.append("| Modality | Task | Subject-relative macro F1 | Global-label macro F1 | Delta macro F1 | Subject-relative bal acc | Global-label bal acc | Delta bal acc |")
lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
for row in comparison:
    lines.append(
        f"| {row.get('modality')} | {row.get('task')} | "
        f"{fmt_float(row.get('subject_relative_macro_f1'))} | "
        f"{fmt_float(row.get('global_label_macro_f1'))} | "
        f"{fmt_float(row.get('delta_macro_f1'))} | "
        f"{fmt_float(row.get('subject_relative_balanced_accuracy'))} | "
        f"{fmt_float(row.get('global_label_balanced_accuracy'))} | "
        f"{fmt_float(row.get('delta_balanced_accuracy'))} |"
    )
lines.append("")
lines.append("## Next Allowed Step")
lines.append("")
lines.append("Create and review a controlled representation/preprocessing objective before any new training.")
lines.append("")
lines.append("## Not Authorized")
lines.append("")
for item in review["not_authorized"]:
    lines.append(f"- {item}")
lines.append("")
REVIEW_MD.write_text("\n".join(lines), encoding="utf-8")

objective = {
    "status": "short_term_objective_created",
    "created_or_updated_utc": NOW,
    "objective_name": "I-DARE subject-relative representation/preprocessing objective",
    "triggering_review": str(REVIEW_MD),
    "triggering_report": str(REPORT_MD),
    "evidence_level": "diagnostic/design objective; no final performance claim",
    "scientific_questions": [
        "Is the remaining blocker primarily representation/preprocessing rather than label formulation alone?",
        "Can controlled preprocessing candidates improve train/validation separability without leakage?",
        "Which minimal preprocessing candidate should be tested first in a separately reviewed training objective?",
    ],
    "authorized_work": [
        "Read existing caches, cache indices, diagnostics, and prediction outputs.",
        "Audit EEG and EMG feature distributions under subject-relative labels.",
        "Compare train-only scaling, robust scaling, per-channel/window normalization, and summary-feature extraction as design candidates.",
        "For EEG, create read-only diagnostics on baseline-corrected STIM-BSL windows and summary features; no model training in this objective.",
        "For EMG, create read-only diagnostics on feature scaling and subject/fold distribution shift; no model training in this objective.",
        "Produce a ranked candidate list for a future minimal preprocessing training objective.",
    ],
    "expected_outputs": [
        "docs/idare_subject_relative_representation_preprocessing_report.md",
        "docs/idare_subject_relative_representation_preprocessing_report.json",
        "docs/idare_subject_relative_preprocessing_candidate_matrix.csv",
        "docs/idare_subject_relative_distribution_shift_summary.csv",
    ],
    "pass_criteria": [
        "Report is generated from existing committed/cached artifacts only.",
        "No new performance training is run.",
        "No heldout subject leakage is introduced.",
        "Candidate preprocessing options are ranked by diagnostic evidence and implementation risk.",
        "Report recommends exactly one next objective after human review.",
    ],
    "candidate_next_objectives_after_review": [
        "minimal_subject_relative_preprocessed_training_objective",
        "subject_relative_feature_engineering_objective",
        "stop_or_handoff_objective",
    ],
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
    "next_allowed_step": "Prepare reviewed read-only representation/preprocessing diagnostic command/script.",
}
OBJECTIVE_JSON.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = []
md.append("# I-DARE Subject-relative Representation/Preprocessing Objective")
md.append("")
md.append("## Status")
md.append("")
md.append("Short-term diagnostic/design objective created.")
md.append("")
md.append(f"Created/updated UTC: `{NOW}`")
md.append("")
md.append("This objective does not authorize new performance training, final LOSO claims, fusion, architecture improvement, augmentation, or domain generalization.")
md.append("")
md.append("## Why This Objective Exists")
md.append("")
md.append("The minimal subject-relative first-pass training report was reviewed.")
md.append("")
md.append("The selected subject-relative formulation was tested, but it was not sufficient alone.")
md.append("")
md.append("The next controlled step is to diagnose representation and preprocessing before trying another training pass.")
md.append("")
md.append("## Scientific Questions")
md.append("")
for q in objective["scientific_questions"]:
    md.append(f"- {q}")
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
    "| I-DARE subject-relative minimal training review | human review accepted 24-run first pass; subject-relative q33 not sufficient alone | yes | `docs/idare_subject_relative_minimal_training_review_status.md` | Create/run representation/preprocessing diagnostic objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; mainline change. |",
    "| I-DARE subject-relative representation/preprocessing objective | short-term diagnostic/design objective created; no new performance training authorized | yes | `docs/idare_subject_relative_representation_preprocessing_objective.md` | Prepare reviewed read-only representation/preprocessing diagnostic command/script. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |",
]
for row in rows:
    key = row.split("|")[1].strip()
    if key not in project_md:
        lines = project_md.splitlines()
        out = []
        inserted = False
        for line in lines:
            out.append(line)
            if line.startswith("| I-DARE minimal subject-relative training report |"):
                if not inserted:
                    out.extend(rows)
                    inserted = True
        if not inserted:
            raise SystemExit("ERROR: could not insert roadmap rows")
        project_md = "\n".join(out) + "\n"
        break

bullet = "- Human review of the minimal subject-relative training first pass is frozen in `docs/idare_subject_relative_minimal_training_review_status.md`; representation/preprocessing diagnosis is selected next."
bullet2 = "- A subject-relative representation/preprocessing objective is defined in `docs/idare_subject_relative_representation_preprocessing_objective.md`; next work is a reviewed read-only diagnostic command/script."
for b in [bullet, bullet2]:
    if b not in project_md:
        marker = "\n## Documentation Gap Closed by This File"
        if marker not in project_md:
            raise SystemExit("ERROR: project status marker not found")
        project_md = project_md.replace(marker, "\n" + b + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_subject_relative_minimal_training_review"] = {
    "status": "frozen_human_review_closeout",
    "evidence": str(REVIEW_MD),
    "evidence_json": str(REVIEW_JSON),
    "decision": review["human_review_decision"],
    "not_authorized": review["not_authorized"],
}
decisions["idare_subject_relative_representation_preprocessing_objective"] = {
    "status": "short_term_objective_created",
    "evidence": str(OBJECTIVE_MD),
    "evidence_json": str(OBJECTIVE_JSON),
    "next_allowed_step": objective["next_allowed_step"],
    "not_authorized": objective["not_authorized"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_REPRESENTATION_PREPROCESSING_OBJECTIVE_WRITTEN")
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
    Path("docs/idare_subject_relative_minimal_training_review_status.json"),
    Path("docs/idare_subject_relative_representation_preprocessing_objective.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")
PY

grep -n "## Status\|## Review Decision\|## Result Summary\|## Next Allowed Step" docs/idare_subject_relative_minimal_training_review_status.md
grep -n "## Status\|## Scientific Questions\|## Authorized Work\|## Pass Criteria\|## Next Allowed Step" docs/idare_subject_relative_representation_preprocessing_objective.md
grep -n "subject-relative representation/preprocessing\|minimal subject-relative training review" docs/project_status_current.md
echo

echo "===== 4) diff stat ====="
git diff --stat
echo

echo "===== 5) status before commit ====="
git status --short --branch
echo

echo "===== 6) commit and push ====="
git add \
  docs/idare_subject_relative_minimal_training_review_status.md \
  docs/idare_subject_relative_minimal_training_review_status.json \
  docs/idare_subject_relative_representation_preprocessing_objective.md \
  docs/idare_subject_relative_representation_preprocessing_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE subject-relative preprocessing objective"

git push origin main
echo

echo "===== 7) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_subject_relative_preprocessing_objective.log"
