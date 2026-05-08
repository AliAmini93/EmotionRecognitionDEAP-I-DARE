#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_representation_label_semantics_failure_objective.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start pair-sampler failure review + representation/label-semantics objective ====="
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
from pathlib import Path
try:
    import pandas as pd
except Exception as e:
    raise SystemExit(f"ERROR_IMPORTS: {e}")
print("OK_IMPORTS")
PY

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: repo is not clean; commit/stash before creating objective." >&2
  git status --short
  exit 2
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required evidence docs ====="
required=(
  docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.md
  docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.json
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_review_status.md
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_review_status.json
  docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md
  docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json
  docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv
  docs/idare_supcon_dg_pair_sampler_failure_decision_matrix.csv
  docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv
  docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv
  docs/idare_supcon_dg_failure_analysis_report.json
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json
  docs/project_status_current.json
  docs/project_status_current.md
)
for f in "${required[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "ERROR: missing required evidence file: $f" >&2
    exit 3
  fi
  ls -lh "$f"
done
echo

echo "===== 3) create review closeout + representation/label-semantics failure-analysis objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

review_md = DOCS / "idare_supcon_dg_pair_sampler_failure_analysis_review_status.md"
review_json = DOCS / "idare_supcon_dg_pair_sampler_failure_analysis_review_status.json"
objective_md = DOCS / "idare_representation_or_label_semantics_failure_analysis_objective.md"
objective_json = DOCS / "idare_representation_or_label_semantics_failure_analysis_objective.json"

pair_report_path = DOCS / "idare_supcon_dg_pair_sampler_failure_analysis_report.json"
pair_report = json.loads(pair_report_path.read_text(encoding="utf-8"))

diagnosis = pair_report.get("diagnosis", "pair_sampler_valid_but_not_primary_failure_mode")
recommended = pair_report.get("recommended_next_objective", "representation_or_label_semantics_failure_analysis_objective")
best_candidate = pair_report.get("best_candidate", {})
best_candidate_id = best_candidate.get("candidate_id", "A5_cross_subject_supcon_vrex")
best_macro = best_candidate.get("mean_macro_f1", None)
best_bal = best_candidate.get("mean_bal_acc", best_candidate.get("mean_balanced_accuracy", None))
a5 = pair_report.get("a5_vs_controls", {})

blocked_steps = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change",
    "new training before representation/label-semantics failure analysis review",
]

review_obj = {
    "artifact_type": "review_status",
    "name": "I-DARE SupCon/DG pair-sampler failure-analysis review",
    "created_utc": now,
    "status": "human_review_accepted",
    "reviewed_artifacts": [
        "docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md",
        "docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json",
        "docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv",
        "docs/idare_supcon_dg_pair_sampler_failure_decision_matrix.csv",
        "docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv",
        "docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv",
    ],
    "accepted_diagnosis": diagnosis,
    "accepted_interpretation": {
        "pair_sampler_valid_but_not_primary_failure_mode": True,
        "best_candidate": best_candidate_id,
        "best_candidate_mean_macro_f1": best_macro,
        "best_candidate_mean_balanced_accuracy": best_bal,
        "full_supcon_dg_training_authorized": False,
        "broad_hyperparameter_search_authorized": False,
    },
    "next_selected_step": "representation_or_label_semantics_failure_analysis_objective",
    "next_allowed_step": "prepare_reviewed_representation_or_label_semantics_failure_analysis_command",
    "blocked_steps": blocked_steps,
}

review_json.write_text(json.dumps(review_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

review_md.write_text(f"""# I-DARE SupCon/DG Pair-Sampler Failure Analysis Review Status

## Status

Status: human review accepted.

Created UTC: `{now}`

## Review Decision

The read-only SupCon/DG pair-sampler failure analysis is accepted as the current controlling evidence.

Accepted diagnosis: `{diagnosis}`

Accepted next selected step: `representation_or_label_semantics_failure_analysis_objective`

## Result Summary

The targeted pair/sampler ablation showed that pair/sampler mechanics were valid but not the primary failure mode.

Best candidate:

- Candidate: `{best_candidate_id}`
- Mean macro-F1: `{best_macro}`
- Mean balanced accuracy: `{best_bal}`

The evidence indicates that positive-pair coverage and smoke/guardrail validity were not enough to produce stable held-out subject performance.

## Interpretation Accepted by Review

The failure mode should no longer be treated as a simple pair-sampler implementation issue.

The next diagnosis must localize whether the remaining blocker is primarily:

1. label semantics across subjects,
2. representation weakness under held-out subject transfer,
3. task formulation mismatch,
4. objective/metric mismatch between training losses and held-out macro-F1.

## Blocked Steps

The following remain blocked:

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new training before representation/label-semantics failure analysis review

## Next Selected Step

Create a read-only representation or label-semantics failure-analysis objective.

## Next Allowed Step

Prepare a reviewed read-only analysis command/script for representation or label-semantics failure analysis.
""", encoding="utf-8")

objective_obj = {
    "artifact_type": "objective",
    "name": "I-DARE representation or label-semantics failure-analysis objective",
    "created_utc": now,
    "status": "objective_created",
    "triggering_evidence": [
        "docs/idare_supcon_dg_pair_sampler_failure_analysis_review_status.md",
        "docs/idare_supcon_dg_pair_sampler_failure_analysis_report.md",
        "docs/idare_supcon_dg_pair_sampler_failure_decision_matrix.csv",
        "docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv",
        "docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md",
        "docs/idare_supcon_dg_failure_analysis_report.md",
    ],
    "scientific_question": (
        "After valid SupCon/DG smoke tests and targeted pair/sampler ablations failed to deliver stable "
        "held-out subject gains, is the remaining blocker primarily label semantics, representation transfer, "
        "task formulation, or objective/metric mismatch?"
    ),
    "authorized_work": {
        "read_only_analysis": True,
        "new_training": False,
        "new_model_changes": False,
        "feature_engineering_training": False,
        "fusion": False,
        "full_supcon_dg_training": False,
        "broad_hyperparameter_search": False,
    },
    "required_analysis_questions": [
        "Do same binary valence/arousal labels represent comparable affective semantics across subjects?",
        "Do subject-relative labels improve semantic consistency, or do they remove between-subject transfer signal?",
        "Do EEG/EMG representations separate class labels in ways that are stable across held-out subjects?",
        "Are hard folds/hard subjects explained by label distribution, representation shift, or model objective mismatch?",
        "Do SupCon/DG loss or embedding diagnostics correlate with held-out macro-F1 after controlling for modality/task/fold?",
        "Is the currently selected task formulation scientifically defensible for LOSO-style claims?",
        "Which next step is justified: label/task redesign, representation redesign, objective redesign, or stopping this path?",
    ],
    "required_inputs": [
        "docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json",
        "docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv",
        "docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv",
        "docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv",
        "docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv",
        "docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv",
        "docs/idare_label_noise_subject_balance_summary.csv",
        "docs/idare_representation_signal_diagnostic_summary.csv",
        "docs/idare_subject_relative_label_balance_summary.csv",
        "docs/idare_subject_relative_candidate_matrix.csv",
        ".cache/idare_eeg_cache_index_baseline_corrected.csv",
        ".cache/idare_emg_feature_cache_index.csv",
    ],
    "expected_outputs": [
        "docs/idare_representation_or_label_semantics_failure_analysis_report.md",
        "docs/idare_representation_or_label_semantics_failure_analysis_report.json",
        "docs/idare_label_semantics_cross_subject_audit.csv",
        "docs/idare_representation_transfer_failure_summary.csv",
        "docs/idare_task_formulation_failure_decision_matrix.csv",
        "docs/idare_objective_metric_alignment_summary.csv",
    ],
    "pass_criteria": [
        "Report is read-only and uses only committed outputs/caches.",
        "Report explicitly separates label semantics, representation transfer, task formulation, and objective/metric mismatch.",
        "Report explains why valid pair/sampler and SupCon/DG interventions were insufficient.",
        "Report recommends exactly one next objective or recommends stopping/parking the path.",
        "No new training, fusion, or broad hyperparameter search is authorized.",
    ],
    "next_allowed_step": "prepare_reviewed_representation_or_label_semantics_failure_analysis_command",
    "blocked_steps": blocked_steps,
}
objective_json.write_text(json.dumps(objective_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

objective_md.write_text(f"""# I-DARE Representation or Label-Semantics Failure Analysis Objective

## Status

Status: objective created; read-only analysis only.

Created UTC: `{now}`

No new training is authorized by this document.

## Scientific Question

After valid SupCon/DG smoke tests and targeted pair/sampler ablations failed to deliver stable held-out subject gains, is the remaining blocker primarily:

1. label semantics,
2. representation transfer,
3. task formulation,
4. objective/metric mismatch?

## Core Rationale

The pair/sampler failure analysis accepted this diagnosis:

`{diagnosis}`

The strongest targeted candidate was `{best_candidate_id}`, but it remained insufficient.

This means the next analysis must move one level deeper. The question is no longer "did the pair sampler work?" but "why did valid pairs and valid regularization not produce generalizable affect recognition?"

## Authorized Scope

Authorized:

- read-only analysis of committed predictions, run summaries, label audits, representation diagnostics, and cache indices
- cross-subject label-semantics audit
- representation transfer audit
- task formulation audit
- objective/metric alignment audit

Not authorized:

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new model training
- new feature-engineering training

## Required Analysis Questions

The report must answer:

1. Do same binary valence/arousal labels represent comparable affective semantics across subjects?
2. Do subject-relative labels improve semantic consistency, or do they remove between-subject transfer signal?
3. Do EEG/EMG representations separate class labels in ways that are stable across held-out subjects?
4. Are hard folds/hard subjects explained by label distribution, representation shift, or model objective mismatch?
5. Do SupCon/DG loss or embedding diagnostics correlate with held-out macro-F1 after controlling for modality/task/fold?
6. Is the current task formulation scientifically defensible for LOSO-style claims?
7. Which next step is justified: label/task redesign, representation redesign, objective redesign, or stopping this path?

## Required Inputs

Use the following evidence where available:

- `docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json`
- `docs/idare_supcon_dg_pair_sampler_failure_candidate_deltas.csv`
- `docs/idare_supcon_dg_pair_sampler_failure_fold_subject_summary.csv`
- `docs/idare_supcon_dg_pair_sampler_failure_loss_alignment.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv`
- `docs/idare_label_noise_subject_balance_summary.csv`
- `docs/idare_representation_signal_diagnostic_summary.csv`
- `docs/idare_subject_relative_label_balance_summary.csv`
- `docs/idare_subject_relative_candidate_matrix.csv`
- `.cache/idare_eeg_cache_index_baseline_corrected.csv`
- `.cache/idare_emg_feature_cache_index.csv`

## Expected Outputs

The next command/script should create:

- `docs/idare_representation_or_label_semantics_failure_analysis_report.md`
- `docs/idare_representation_or_label_semantics_failure_analysis_report.json`
- `docs/idare_label_semantics_cross_subject_audit.csv`
- `docs/idare_representation_transfer_failure_summary.csv`
- `docs/idare_task_formulation_failure_decision_matrix.csv`
- `docs/idare_objective_metric_alignment_summary.csv`

## Pass Criteria

The objective passes only if:

1. analysis is read-only and uses committed outputs/caches,
2. label semantics, representation transfer, task formulation, and objective/metric mismatch are separated,
3. the report explains why valid pair/sampler and SupCon/DG interventions were insufficient,
4. exactly one next objective is recommended, or the path is explicitly stopped/parked,
5. no new training, fusion, or broad hyperparameter search is authorized.

## Next Allowed Step

Prepare a reviewed read-only representation or label-semantics failure-analysis command/script.

## Blocked Steps

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new training before representation/label-semantics failure analysis review
""", encoding="utf-8")

# Update roadmap/status.
status_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

status = json.loads(status_path.read_text(encoding="utf-8"))
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "prepare_reviewed_representation_or_label_semantics_failure_analysis_command"
status["current_idare_blocked_steps"] = blocked_steps
status.setdefault("idare_protocol_events", []).extend([
    {
        "timestamp_utc": now,
        "type": "review_status",
        "name": review_obj["name"],
        "status": f"human review accepted; diagnosis={diagnosis}",
        "evidence": str(review_md),
        "next_allowed_step": "create/use representation or label-semantics failure-analysis objective",
        "blocked": blocked_steps,
    },
    {
        "timestamp_utc": now,
        "type": "objective",
        "name": objective_obj["name"],
        "status": "objective created; read-only analysis only",
        "evidence": str(objective_md),
        "next_allowed_step": objective_obj["next_allowed_step"],
        "blocked": blocked_steps,
    },
])
status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE SupCon/DG Pair-Sampler Failure Review and Representation/Label-Semantics Objective

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE SupCon/DG pair-sampler failure analysis review | human review accepted; diagnosis=`{diagnosis}` | `docs/idare_supcon_dg_pair_sampler_failure_analysis_review_status.md` | Create/use representation or label-semantics failure-analysis objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE representation or label-semantics failure-analysis objective | read-only objective created; no training authorized | `docs/idare_representation_or_label_semantics_failure_analysis_objective.md` | Prepare reviewed read-only analysis command/script. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Human review of the pair-sampler failure analysis is frozen in `docs/idare_supcon_dg_pair_sampler_failure_analysis_review_status.md`.
- A read-only representation or label-semantics failure-analysis objective is defined in `docs/idare_representation_or_label_semantics_failure_analysis_objective.md`.
- The next allowed step is to prepare the analysis command/script; new training remains blocked.
"""
if "I-DARE SupCon/DG Pair-Sampler Failure Review and Representation/Label-Semantics Objective" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_REPRESENTATION_LABEL_SEMANTICS_OBJECTIVE_WRITTEN")
print(review_md)
print(review_json)
print(objective_md)
print(objective_json)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended)
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path

paths = [
    Path("docs/idare_supcon_dg_pair_sampler_failure_analysis_review_status.json"),
    Path("docs/idare_representation_or_label_semantics_failure_analysis_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

checks = {
    Path("docs/idare_supcon_dg_pair_sampler_failure_analysis_review_status.md"): [
        "human review accepted",
        "pair-sampler failure analysis",
        "direct full SupCon/DG training",
        "representation or label-semantics failure-analysis objective",
    ],
    Path("docs/idare_representation_or_label_semantics_failure_analysis_objective.md"): [
        "read-only analysis only",
        "Scientific Question",
        "label semantics",
        "representation transfer",
        "objective/metric mismatch",
        "direct full SupCon/DG training",
        "Next Allowed Step",
    ],
}
for p, terms in checks.items():
    text = p.read_text(encoding="utf-8")
    for term in terms:
        if term not in text:
            raise SystemExit(f"ERROR: missing term {term!r} in {p}")
    print("OK_TERMS:", p)

status = json.loads(Path("docs/project_status_current.json").read_text(encoding="utf-8"))
print("next_allowed_step=", status.get("current_idare_next_allowed_step"))
if status.get("current_idare_next_allowed_step") != "prepare_reviewed_representation_or_label_semantics_failure_analysis_command":
    raise SystemExit("ERROR: wrong next allowed step")
print("ALL_REPRESENTATION_LABEL_SEMANTICS_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "Status|Review Decision|Scientific Question|Required Analysis Questions|Pass Criteria|Next Allowed Step" \
  docs/idare_supcon_dg_pair_sampler_failure_analysis_review_status.md \
  docs/idare_representation_or_label_semantics_failure_analysis_objective.md
grep -nE "representation or label-semantics failure-analysis|pair-sampler failure analysis review|Next allowed step" docs/project_status_current.md | tail -n 12
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_supcon_dg_pair_sampler_failure_analysis_review_status.md \
  docs/idare_supcon_dg_pair_sampler_failure_analysis_review_status.json \
  docs/idare_representation_or_label_semantics_failure_analysis_objective.md \
  docs/idare_representation_or_label_semantics_failure_analysis_objective.json \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE representation label semantics failure objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
