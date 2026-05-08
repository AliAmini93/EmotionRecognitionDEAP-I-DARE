#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_redesigned_task_smoke_objective.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start task-redesign spec review + redesigned-task smoke-tests objective ====="
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
try:
    import json
    from pathlib import Path
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

echo "===== 2) check required task-redesign spec evidence ====="
required=(
  docs/idare_label_semantics_task_redesign_spec_objective.md
  docs/idare_label_semantics_task_redesign_spec_objective.json
  docs/idare_label_semantics_task_redesign_spec.md
  docs/idare_label_semantics_task_redesign_spec.json
  docs/idare_label_semantics_selected_task_definition.csv
  docs/idare_label_semantics_task_redesign_guardrails.csv
  docs/idare_label_semantics_task_redesign_metric_plan.csv
  docs/idare_label_semantics_task_redesign_protocol_matrix.csv
  docs/idare_label_semantics_task_redesign_future_run_matrix.csv
  docs/idare_label_semantics_task_redesign_stop_criteria.csv
  docs/project_status_current.json
  docs/project_status_current.md
)
for f in "${required[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "ERROR: missing required input: $f" >&2
    exit 3
  fi
  ls -lh "$f"
done
echo

echo "===== 3) create task-redesign spec review closeout + smoke-tests objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

spec_md_path = DOCS / "idare_label_semantics_task_redesign_spec.md"
spec_json_path = DOCS / "idare_label_semantics_task_redesign_spec.json"
review_md_path = DOCS / "idare_label_semantics_task_redesign_spec_review_status.md"
review_json_path = DOCS / "idare_label_semantics_task_redesign_spec_review_status.json"
objective_md_path = DOCS / "idare_label_semantics_redesigned_task_smoke_tests_objective.md"
objective_json_path = DOCS / "idare_label_semantics_redesigned_task_smoke_tests_objective.json"
smoke_plan_path = DOCS / "idare_label_semantics_redesigned_task_smoke_test_plan.csv"
status_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

spec = json.loads(spec_json_path.read_text(encoding="utf-8"))
selected = spec.get("selected_primary_formulation", "subject_relative_ordinal_affect_regression_v1")
recommended = spec.get("recommended_next_objective", "label_semantics_redesigned_task_smoke_tests_objective")
claim = spec.get("scientific_claim", "Predict within-subject affect-rating order/percentile for held-out subjects.")
blocked = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change",
    "redesigned-task training before smoke-test review",
]

review = {
    "status": "human_review_accepted",
    "created_utc": now,
    "reviewed_spec": str(spec_md_path),
    "accepted_selected_primary_formulation": selected,
    "accepted_scientific_claim": claim,
    "accepted_recommended_next_objective": recommended,
    "next_selected_step": "create_redesigned_task_smoke_tests_objective",
    "training_authorized": False,
    "blocked": blocked,
}
review_json_path.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

review_md = f"""# I-DARE Label-Semantics Task Redesign Spec Review Status

## Status

Status: human review accepted.

Created UTC: `{now}`

## Review Decision

The label-semantics task redesign spec is accepted as the next design checkpoint.

Accepted selected formulation: `{selected}`

Accepted scientific claim: {claim}

Accepted recommended next objective: `{recommended}`

## Scientific Meaning

The current global binary LOSO final-performance path remains paused.

The next step is not model training. The next step is to validate the redesigned task itself.

## Next Selected Step

Create and run a redesigned-task smoke-test objective.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- redesigned-task training before smoke-test review
"""
review_md_path.write_text(review_md, encoding="utf-8")

smoke_rows = [
    {
        "smoke_test": "target_construction_integrity",
        "required": "yes",
        "purpose": "Verify per-subject rank-percentile targets are in [0,1], non-missing, and match raw ratings.",
        "pass_condition": "no out-of-range targets; expected rows for valence/arousal; ties handled deterministically",
        "blocked_if_fail": "all training",
    },
    {
        "smoke_test": "fold_leakage_guard",
        "required": "yes",
        "purpose": "Verify existing subject-heldout folds have no train/validation subject overlap.",
        "pass_condition": "zero subject overlap and zero row-id overlap",
        "blocked_if_fail": "all training",
    },
    {
        "smoke_test": "metric_computation_sanity",
        "required": "yes",
        "purpose": "Validate Spearman, MAE, RMSE, and q33 audit metrics on deterministic toy predictions.",
        "pass_condition": "perfect predictions score best; reversed predictions score worst; mean baseline is finite",
        "blocked_if_fail": "all training",
    },
    {
        "smoke_test": "baseline_no_training_control",
        "required": "yes",
        "purpose": "Compute train-mean and random/permutation controls without fitting a predictive model.",
        "pass_condition": "controls are finite and near expected null behavior",
        "blocked_if_fail": "training objective",
    },
    {
        "smoke_test": "target_distribution_audit",
        "required": "yes",
        "purpose": "Audit target distribution by subject/fold/task/modality.",
        "pass_condition": "no degenerate fold/task with near-constant target unless explicitly flagged",
        "blocked_if_fail": "training objective",
    },
    {
        "smoke_test": "future_run_matrix_guard",
        "required": "yes",
        "purpose": "Verify the 48-row future run matrix remains minimal and no SupCon/DG/fusion rows are present.",
        "pass_condition": "only baseline and ridge regression rows; no direct full SupCon/DG training",
        "blocked_if_fail": "training objective",
    },
]
pd.DataFrame(smoke_rows).to_csv(smoke_plan_path, index=False)

objective = {
    "status": "objective_created",
    "created_utc": now,
    "source_review": str(review_md_path),
    "source_spec": str(spec_md_path),
    "selected_primary_formulation": selected,
    "scientific_question": (
        "Does the redesigned subject-relative ordinal/regression task pass construction, leakage, metric, "
        "distribution, and null-control smoke tests before any training is authorized?"
    ),
    "authorized_work": [
        "read the task redesign spec and guardrails",
        "construct labels/targets for audit only",
        "run leakage and target-construction smoke tests",
        "run metric-computation sanity tests",
        "run no-training baseline and shuffled/permutation controls",
        "write smoke-test report and decision matrix",
        "no model training beyond deterministic/no-training baselines",
        "no direct full SupCon/DG training",
        "no broad hyperparameter search",
    ],
    "required_inputs": [
        "docs/idare_label_semantics_task_redesign_spec.md",
        "docs/idare_label_semantics_task_redesign_spec.json",
        "docs/idare_label_semantics_selected_task_definition.csv",
        "docs/idare_label_semantics_task_redesign_guardrails.csv",
        "docs/idare_label_semantics_task_redesign_metric_plan.csv",
        "docs/idare_label_semantics_task_redesign_protocol_matrix.csv",
        "docs/idare_label_semantics_task_redesign_future_run_matrix.csv",
        "docs/idare_label_semantics_task_redesign_stop_criteria.csv",
        ".cache/idare_eeg_cache_index_baseline_corrected.csv",
        ".cache/idare_emg_feature_cache_index.csv",
    ],
    "expected_outputs": [
        "docs/idare_label_semantics_redesigned_task_smoke_tests_report.md",
        "docs/idare_label_semantics_redesigned_task_smoke_tests_report.json",
        "docs/idare_label_semantics_redesigned_task_target_audit.csv",
        "docs/idare_label_semantics_redesigned_task_fold_audit.csv",
        "docs/idare_label_semantics_redesigned_task_metric_sanity.csv",
        "docs/idare_label_semantics_redesigned_task_baseline_control_summary.csv",
        "docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv",
    ],
    "smoke_plan_csv": str(smoke_plan_path),
    "pass_criteria": [
        "all required smoke tests pass",
        "target construction is deterministic and complete",
        "fold leakage is zero",
        "metrics behave correctly on toy predictions",
        "no-training controls are finite and documented",
        "future run matrix remains minimal",
        "direct full SupCon/DG training remains blocked",
        "broad hyperparameter search remains blocked",
        "final LOSO claim remains blocked",
    ],
    "next_allowed_step": "prepare_reviewed_label_semantics_redesigned_task_smoke_tests_command",
    "blocked": blocked,
}
objective_json_path.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

objective_md = f"""# I-DARE Label-Semantics Redesigned-Task Smoke Tests Objective

## Status

Status: objective created; smoke-test only; no training is authorized.

Created UTC: `{now}`

## Scientific Question

Does the redesigned subject-relative ordinal/regression task pass construction, leakage, metric, distribution, and null-control smoke tests before any training is authorized?

## Selected Task

Selected formulation: `{selected}`

Scientific claim: {claim}

## Authorized Scope

- Read the task redesign spec and guardrails.
- Construct labels/targets for audit only.
- Run target-construction integrity checks.
- Run fold leakage checks.
- Run metric-computation sanity checks.
- Run no-training baseline and shuffled/permutation controls.
- Audit target distribution by subject/fold/task/modality.
- Validate that the future run matrix remains minimal.
- Write a smoke-test report and decision matrix.

## Required Smoke Tests

| Smoke test | Purpose | Pass condition |
|---|---|---|
| `target_construction_integrity` | Verify per-subject rank-percentile targets are valid and deterministic. | no out-of-range targets; expected rows; ties handled deterministically |
| `fold_leakage_guard` | Verify subject-heldout split isolation. | zero subject overlap and zero row-id overlap |
| `metric_computation_sanity` | Validate Spearman/MAE/RMSE/q33 audit behavior. | perfect predictions score best; reversed predictions score worst |
| `baseline_no_training_control` | Compute no-training controls before training. | finite controls; near expected null behavior |
| `target_distribution_audit` | Find degenerate fold/task/subject target distributions. | no unflagged degenerate target cells |
| `future_run_matrix_guard` | Confirm future training plan is minimal. | no direct full SupCon/DG training; no fusion; no broad search |

## Expected Outputs

- `docs/idare_label_semantics_redesigned_task_smoke_tests_report.md`
- `docs/idare_label_semantics_redesigned_task_smoke_tests_report.json`
- `docs/idare_label_semantics_redesigned_task_target_audit.csv`
- `docs/idare_label_semantics_redesigned_task_fold_audit.csv`
- `docs/idare_label_semantics_redesigned_task_metric_sanity.csv`
- `docs/idare_label_semantics_redesigned_task_baseline_control_summary.csv`
- `docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv`

## Pass Criteria

- All required smoke tests pass.
- Target construction is deterministic and complete.
- Fold leakage is zero.
- Metrics behave correctly on toy predictions.
- No-training controls are finite and documented.
- Future run matrix remains minimal.
- direct full SupCon/DG training remains blocked.
- broad hyperparameter search remains blocked.
- final LOSO claim remains blocked.

## Next Allowed Step

Prepare a reviewed redesigned-task smoke-test command/script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- redesigned-task training before smoke-test review
"""
objective_md_path.write_text(objective_md, encoding="utf-8")

# Update status JSON.
status = json.loads(status_path.read_text(encoding="utf-8"))
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "prepare_reviewed_label_semantics_redesigned_task_smoke_tests_command"
status["current_idare_blocked_steps"] = blocked
events = status.get("idare_protocol_events")
if not isinstance(events, list):
    events = []
status["idare_protocol_events"] = events
events.extend([
    {
        "timestamp_utc": now,
        "type": "review",
        "name": "I-DARE label-semantics task redesign spec review",
        "status": f"human review accepted; selected={selected}",
        "evidence": str(review_md_path),
        "next_allowed_step": "create/use redesigned-task smoke-tests objective",
        "blocked": blocked,
    },
    {
        "timestamp_utc": now,
        "type": "objective",
        "name": "I-DARE label-semantics redesigned-task smoke-tests objective",
        "status": "objective created; smoke-test only; no training authorized",
        "evidence": str(objective_md_path),
        "next_allowed_step": "prepare reviewed redesigned-task smoke-test command",
        "blocked": blocked,
    },
])
status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Update status markdown.
status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Label-Semantics Redesigned-Task Smoke Tests Objective

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE label-semantics task redesign spec review | human review accepted; selected=`{selected}` | `docs/idare_label_semantics_task_redesign_spec_review_status.md` | Create/use redesigned-task smoke-tests objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE label-semantics redesigned-task smoke-tests objective | smoke-test objective created; no training authorized | `docs/idare_label_semantics_redesigned_task_smoke_tests_objective.md` | Prepare reviewed redesigned-task smoke-test command/script. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- A redesigned-task smoke-test objective is defined in `docs/idare_label_semantics_redesigned_task_smoke_tests_objective.md`.
- Training remains blocked until smoke-test review.
"""
if "I-DARE Label-Semantics Redesigned-Task Smoke Tests Objective" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_REDESIGNED_TASK_SMOKE_OBJECTIVE_WRITTEN")
print(review_md_path)
print(review_json_path)
print(objective_md_path)
print(objective_json_path)
print(smoke_plan_path)
print("selected_primary_formulation=", selected)
print("next_allowed_step=prepare_reviewed_label_semantics_redesigned_task_smoke_tests_command")
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_paths = [
    Path("docs/idare_label_semantics_task_redesign_spec_review_status.json"),
    Path("docs/idare_label_semantics_redesigned_task_smoke_tests_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

smoke = pd.read_csv("docs/idare_label_semantics_redesigned_task_smoke_test_plan.csv")
print("smoke_plan_rows=", len(smoke))
if len(smoke) < 6:
    raise SystemExit("ERROR: smoke test plan too short")

term_checks = {
    "docs/idare_label_semantics_task_redesign_spec_review_status.md": [
        "human review accepted",
        "subject_relative_ordinal_affect_regression_v1",
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "final LOSO claim",
    ],
    "docs/idare_label_semantics_redesigned_task_smoke_tests_objective.md": [
        "Scientific Question",
        "Required Smoke Tests",
        "target_construction_integrity",
        "fold_leakage_guard",
        "metric_computation_sanity",
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "final LOSO claim",
    ],
}
for path, terms in term_checks.items():
    text = Path(path).read_text(encoding="utf-8")
    for term in terms:
        if term not in text:
            raise SystemExit(f"ERROR: missing term {term!r} in {path}")
    print("OK_TERMS:", path)

obj = json.loads(Path("docs/idare_label_semantics_redesigned_task_smoke_tests_objective.json").read_text(encoding="utf-8"))
if obj.get("next_allowed_step") != "prepare_reviewed_label_semantics_redesigned_task_smoke_tests_command":
    raise SystemExit("ERROR: wrong next_allowed_step")
if "direct full SupCon/DG training" not in obj.get("blocked", []):
    raise SystemExit("ERROR: missing blocked direct full SupCon/DG training")

print("selected_primary_formulation=", obj.get("selected_primary_formulation"))
print("next_allowed_step=", obj.get("next_allowed_step"))
print("ALL_REDESIGNED_TASK_SMOKE_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "Status|Scientific Question|Selected Task|Authorized Scope|Required Smoke Tests|Expected Outputs|Pass Criteria|Next Allowed Step" \
  docs/idare_label_semantics_redesigned_task_smoke_tests_objective.md
grep -nE "Redesigned-Task Smoke Tests Objective|redesigned-task smoke-test objective" docs/project_status_current.md | tail -n 8
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_label_semantics_task_redesign_spec_review_status.md \
  docs/idare_label_semantics_task_redesign_spec_review_status.json \
  docs/idare_label_semantics_redesigned_task_smoke_tests_objective.md \
  docs/idare_label_semantics_redesigned_task_smoke_tests_objective.json \
  docs/idare_label_semantics_redesigned_task_smoke_test_plan.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE redesigned task smoke tests objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
