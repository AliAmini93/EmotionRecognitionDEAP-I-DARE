#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_supcon_dg_pair_sampler_failure_objective.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start targeted SupCon/DG ablation review + pair-sampler failure-analysis objective ====="
date
git status --short --branch
echo

echo "===== 1) choose python and require clean repo ====="
PY="${PY:-.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3)"
fi
echo "PY=$PY"
"$PY" - <<'PY'
import json
import csv
from pathlib import Path
print("OK_IMPORTS")
PY

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: repo is not clean; commit/stash before creating objective docs." >&2
  git status --short
  exit 2
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required targeted ablation evidence ====="
required=(
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_objective.md
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_objective.json
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv
  docs/idare_supcon_dg_failure_analysis_report.md
  docs/idare_supcon_dg_failure_analysis_report.json
  docs/project_status_current.json
  docs/project_status_current.md
)
for f in "${required[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "ERROR: missing required evidence: $f" >&2
    exit 3
  fi
  ls -lh "$f"
done
echo

echo "===== 3) create review closeout + SupCon/DG pair-sampler failure-analysis objective ====="
"$PY" - <<'PY'
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

ablation_report_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_report.json"
ablation_report_md = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_report.md"
runs_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv"
pred_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv"
pair_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv"
loss_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv"
candidate_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv"
method_task_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv"
smoke_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv"

review_md_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_review_status.md"
review_json_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_review_status.json"
objective_md_path = DOCS / "idare_supcon_dg_pair_sampler_failure_analysis_objective.md"
objective_json_path = DOCS / "idare_supcon_dg_pair_sampler_failure_analysis_objective.json"

ablation = json.loads(ablation_report_path.read_text(encoding="utf-8"))
diagnosis = ablation.get("diagnosis", "targeted_pair_sampler_ablation_not_sufficient")
recommended = ablation.get("recommended_next_objective", "supcon_dg_pair_sampler_failure_analysis_objective")
best_candidate = ablation.get("best_candidate", {})
best_id = best_candidate.get("candidate_id", "unknown")
best_macro = best_candidate.get("mean_macro_f1", None)
best_bal = best_candidate.get("mean_balanced_accuracy", None)

def count_csv_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as f:
        return max(0, sum(1 for _ in f) - 1)

row_counts = {
    "runs": count_csv_rows(runs_path),
    "predictions": count_csv_rows(pred_path),
    "pair_audit": count_csv_rows(pair_path),
    "loss_embedding": count_csv_rows(loss_path),
    "candidate_summary": count_csv_rows(candidate_path),
    "method_task_summary": count_csv_rows(method_task_path),
    "smoke_summary": count_csv_rows(smoke_path),
}

blocked = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change",
    "new training before failure-analysis review",
]

review = {
    "status": "human_review_accepted_targeted_pair_sampler_ablation_insufficient",
    "created_utc": now,
    "reviewed_report": str(ablation_report_md),
    "review_decision": {
        "accepted": True,
        "diagnosis": diagnosis,
        "best_candidate": best_candidate,
        "interpretation": (
            "The targeted pair/sampler ablation completed all guardrails and training rows, but the best aggregate "
            "candidate did not provide a stable, review-ready improvement. The result is accepted as insufficient, "
            "not as a failed implementation."
        ),
    },
    "next_selected_step": "supcon_dg_pair_sampler_failure_analysis_objective",
    "blocked": blocked,
}

objective = {
    "status": "objective_created",
    "created_utc": now,
    "objective_id": "idare_supcon_dg_pair_sampler_failure_analysis_objective",
    "title": "I-DARE SupCon/DG Pair-Sampler Failure Analysis Objective",
    "scientific_question": (
        "Why did the targeted SupCon/DG pair-sampler ablation fail to produce a stable subject-heldout improvement, "
        "despite passing smoke tests, leakage guards, and positive-pair coverage checks?"
    ),
    "evidence_inputs": {
        "ablation_report": str(ablation_report_md),
        "ablation_report_json": str(ablation_report_path),
        "runs": str(runs_path),
        "predictions": str(pred_path),
        "pair_audit": str(pair_path),
        "loss_embedding_summary": str(loss_path),
        "candidate_summary": str(candidate_path),
        "method_task_summary": str(method_task_path),
        "smoke_summary": str(smoke_path),
        "previous_supcon_dg_failure_report": "docs/idare_supcon_dg_failure_analysis_report.md",
    },
    "required_analysis_questions": [
        "Did pair/sampler variants improve any modality/task/fold pattern consistently, or only isolated cells?",
        "Was A5 better because of cross-subject SupCon, VREx, or their interaction?",
        "Did positive-pair coverage hide semantic label noise, subject-specific label meaning, or rating-distance mismatch?",
        "Did SupCon lower contrastive loss without improving class-separable validation embeddings?",
        "Did VREx reduce fold variance or suppress weak useful signal?",
        "Are improvements concentrated in EMG/arousal, EEG/arousal, or particular folds/subjects?",
        "Do prediction errors overlap with the earlier subject-variability hard-subject patterns?",
        "Which failure mode is now most supported: pair design, label/task semantics, representation weakness, optimization, or domain-generalization regularizer mismatch?",
    ],
    "authorized_scope": [
        "read existing committed CSV/JSON outputs only",
        "aggregate by candidate, modality, task, fold, and subject",
        "compare pair-audit coverage to actual metrics",
        "align loss/embedding summaries with validation outcomes",
        "compare against first-pass SupCon/DG and CE controls",
        "write markdown/json/csv report",
        "update roadmap",
    ],
    "blocked": blocked,
    "expected_outputs": [
        "docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md",
        "docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json",
        "docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv",
        "docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv",
        "docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv",
        "docs/idare_supcon_dg_pair_sampler_failure_decision_matrix.csv",
    ],
    "pass_criteria": [
        "No new training is run.",
        "Report identifies whether failure is more likely from pair design, labels/task, representation, optimization, or regularizer mismatch.",
        "Report explains why A5 was best but insufficient.",
        "Report recommends exactly one next objective or a stop/rollback decision.",
        "Full SupCon/DG training remains blocked unless the analysis provides a specific, reviewable justification.",
    ],
    "next_allowed_step": "prepare_reviewed_supcon_dg_pair_sampler_failure_analysis_command",
}

review_json_path.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
objective_json_path.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

best_macro_txt = "unknown" if best_macro is None else f"{float(best_macro):.4f}"
best_bal_txt = "unknown" if best_bal is None else f"{float(best_bal):.4f}"

review_md = f"""# I-DARE Targeted SupCon/DG Pair-Sampler Ablation Review Status

## Status

Status: human review accepted targeted pair/sampler ablation as insufficient.

Created UTC: `{now}`

## Review Decision

The targeted SupCon/DG pair-sampler ablation is accepted as a completed diagnostic run, not as a successful fix.

Primary diagnosis from the report:

`{diagnosis}`

Recommended next objective:

`{recommended}`

Best aggregate candidate:

- Candidate: `{best_id}`
- Mean macro-F1: `{best_macro_txt}`
- Mean balanced accuracy: `{best_bal_txt}`

## Evidence Reviewed

- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv`

## Result Summary

The ablation completed `{row_counts["runs"]}` runs and `{row_counts["predictions"]}` prediction rows. Guardrails passed, but the best candidate was still not stable enough to justify full SupCon/DG training.

The failure should now be analyzed before any new training or broad hyperparameter search.

## Next Selected Step

Create and run a read-only SupCon/DG pair-sampler failure-analysis objective.

## Blocked Until Review

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new training before failure-analysis review
"""
review_md_path.write_text(review_md, encoding="utf-8")

objective_md = f"""# I-DARE SupCon/DG Pair-Sampler Failure Analysis Objective

## Status

Status: objective created; read-only analysis only.

Created UTC: `{now}`

No new training is authorized by this document.

## Scientific Question

Why did the targeted SupCon/DG pair-sampler ablation fail to produce a stable subject-heldout improvement, despite passing smoke tests, leakage guards, and positive-pair coverage checks?

## Immediate Context

The targeted ablation completed `{row_counts["runs"]}` runs and `{row_counts["predictions"]}` prediction rows.

The report diagnosis was:

`{diagnosis}`

The best aggregate candidate was `{best_id}` with mean macro-F1 `{best_macro_txt}` and mean balanced accuracy `{best_bal_txt}`.

This means the pair/sampler direction was not obviously broken, but also not sufficient.

## Authorized Scope

This objective is read-only. It may use only committed evidence files.

Allowed inputs:

- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv`
- `docs/idare_supcon_dg_failure_analysis_report.md`
- `docs/idare_supcon_dg_failure_analysis_report.json`

## Required Analysis Questions

1. Did pair/sampler variants improve any modality/task/fold pattern consistently, or only isolated cells?
2. Was A5 better because of cross-subject SupCon, VREx, or their interaction?
3. Did positive-pair coverage hide semantic label noise, subject-specific label meaning, or rating-distance mismatch?
4. Did SupCon lower contrastive loss without improving class-separable validation embeddings?
5. Did VREx reduce fold variance or suppress weak useful signal?
6. Are improvements concentrated in EMG/arousal, EEG/arousal, or particular folds/subjects?
7. Do prediction errors overlap with earlier subject-variability hard-subject patterns?
8. Which failure mode is most supported now:
   - pair design failure
   - label/task semantic mismatch
   - representation weakness
   - optimization/hyperparameter issue
   - DG regularizer mismatch
   - insufficient data per subject/fold

## Expected Outputs

- `docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md`
- `docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json`
- `docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv`
- `docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv`
- `docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv`
- `docs/idare_supcon_dg_pair_sampler_failure_decision_matrix.csv`

## Pass Criteria

- No new training is run.
- The report explains why `{best_id}` was best but insufficient.
- The report distinguishes implementation failure from scientific/assumption failure.
- The report recommends exactly one next objective or a stop/rollback decision.
- Full SupCon/DG training remains blocked unless a later reviewed analysis explicitly justifies it.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new training before failure-analysis review

## Next Allowed Step

Prepare a reviewed read-only command/script for this failure analysis.
"""
objective_md_path.write_text(objective_md, encoding="utf-8")

# Update roadmap/status robustly.
status_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"
status = json.loads(status_path.read_text(encoding="utf-8"))
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "prepare_reviewed_supcon_dg_pair_sampler_failure_analysis_command"
status["current_idare_blocked_steps"] = blocked
status.setdefault("idare_protocol_events", []).append({
    "timestamp_utc": now,
    "type": "review_closeout",
    "name": "I-DARE targeted SupCon/DG pair-sampler ablation review",
    "status": "human review accepted insufficient ablation; failure analysis selected",
    "evidence": str(review_md_path),
    "next_allowed_step": "create/run pair-sampler failure-analysis objective",
    "blocked": blocked,
})
status.setdefault("idare_protocol_events", []).append({
    "timestamp_utc": now,
    "type": "objective",
    "name": "I-DARE SupCon/DG pair-sampler failure analysis objective",
    "status": "read-only objective created; no training authorized",
    "evidence": str(objective_md_path),
    "next_allowed_step": "prepare reviewed read-only failure-analysis command",
    "blocked": blocked,
})
status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Targeted SupCon/DG Pair-Sampler Ablation Review and Failure Analysis Objective

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE targeted SupCon/DG pair-sampler ablation review | human review accepted insufficient ablation; failure analysis selected | `docs/idare_targeted_supcon_dg_pair_sampler_ablation_review_status.md` | Create/run pair-sampler failure-analysis objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE SupCon/DG pair-sampler failure analysis objective | read-only objective created; no training authorized | `docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.md` | Prepare reviewed read-only failure-analysis command. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Human review of the targeted pair/sampler ablation is frozen in `docs/idare_targeted_supcon_dg_pair_sampler_ablation_review_status.md`.
- A read-only SupCon/DG pair-sampler failure-analysis objective is defined in `docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.md`.
"""
if "I-DARE Targeted SupCon/DG Pair-Sampler Ablation Review and Failure Analysis Objective" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_PAIR_SAMPLER_FAILURE_OBJECTIVE_WRITTEN")
print(review_md_path)
print(review_json_path)
print(objective_md_path)
print(objective_json_path)
print("ablation_diagnosis=", diagnosis)
print("next_allowed_step=prepare_reviewed_supcon_dg_pair_sampler_failure_analysis_command")
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path

paths = [
    Path("docs/idare_targeted_supcon_dg_pair_sampler_ablation_review_status.json"),
    Path("docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

terms = {
    "docs/idare_targeted_supcon_dg_pair_sampler_ablation_review_status.md": [
        "targeted_pair_sampler_ablation_not_sufficient",
        "direct full SupCon/DG training",
        "Next Selected Step",
    ],
    "docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.md": [
        "No new training is authorized",
        "Required Analysis Questions",
        "positive-pair coverage",
        "VREx",
        "Next Allowed Step",
    ],
}
for path, required_terms in terms.items():
    text = Path(path).read_text(encoding="utf-8")
    for term in required_terms:
        if term not in text:
            raise SystemExit(f"ERROR: missing term {term!r} in {path}")
    print("OK_TERMS:", path)

obj = json.loads(Path("docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.json").read_text(encoding="utf-8"))
if obj.get("next_allowed_step") != "prepare_reviewed_supcon_dg_pair_sampler_failure_analysis_command":
    raise SystemExit("ERROR: unexpected next_allowed_step")
print("next_allowed_step=", obj.get("next_allowed_step"))
print("ALL_PAIR_SAMPLER_FAILURE_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "Status|Scientific Question|Required Analysis Questions|Pass Criteria|Next Allowed Step" \
  docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.md
grep -nE "pair-sampler failure analysis|Targeted SupCon/DG Pair-Sampler" docs/project_status_current.md | tail -n 10
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_review_status.md \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_review_status.json \
  docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.md \
  docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.json \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE SupCon DG pair sampler failure objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
