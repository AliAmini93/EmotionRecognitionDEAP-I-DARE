#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_minimal_redesigned_task_first_pass_objective.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start patched-smoke review + minimal redesigned-task first-pass objective ====="
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

echo "===== 2) check required patched-smoke evidence ====="
required=(
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_objective.md
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_objective.json
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_manual_review_status.md
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_manual_review_status.json
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.md
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.json
  docs/idare_label_semantics_redesigned_task_smoke_guard_audit.csv
  docs/idare_label_semantics_redesigned_task_patched_smoke_decision_matrix.csv
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.md
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.json
  docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv
  docs/idare_label_semantics_task_redesign_future_run_matrix.csv
  docs/idare_label_semantics_task_redesign_spec.md
  docs/idare_label_semantics_task_redesign_spec.json
  docs/idare_label_semantics_selected_task_definition.csv
  docs/idare_label_semantics_task_redesign_guardrails.csv
  docs/idare_label_semantics_task_redesign_metric_plan.csv
  docs/idare_label_semantics_task_redesign_protocol_matrix.csv
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

echo "===== 3) create patched-smoke review closeout + minimal first-pass objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

patch_report_json_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_patch_report.json"
patch_report_md_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_patch_report.md"
patched_decision_path = DOCS / "idare_label_semantics_redesigned_task_patched_smoke_decision_matrix.csv"
guard_audit_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_audit.csv"
future_matrix_path = DOCS / "idare_label_semantics_task_redesign_future_run_matrix.csv"
spec_json_path = DOCS / "idare_label_semantics_task_redesign_spec.json"
selected_task_path = DOCS / "idare_label_semantics_selected_task_definition.csv"
metric_plan_path = DOCS / "idare_label_semantics_task_redesign_metric_plan.csv"
guardrails_path = DOCS / "idare_label_semantics_task_redesign_guardrails.csv"
protocol_matrix_path = DOCS / "idare_label_semantics_task_redesign_protocol_matrix.csv"

review_md_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_patch_review_status.md"
review_json_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_patch_review_status.json"
objective_md_path = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.md"
objective_json_path = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.json"
run_matrix_path = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_run_matrix.csv"
guardrail_register_path = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_guardrails.csv"

status_json_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

patch_report = read_json(patch_report_json_path)
spec = read_json(spec_json_path)
decision = pd.read_csv(patched_decision_path)
guard_audit = pd.read_csv(guard_audit_path)
future = pd.read_csv(future_matrix_path)
selected_task = pd.read_csv(selected_task_path)
metric_plan = pd.read_csv(metric_plan_path)
guardrails = pd.read_csv(guardrails_path)
protocol = pd.read_csv(protocol_matrix_path)

diagnosis = patch_report.get("diagnosis")
all_passed = bool(patch_report.get("all_passed"))
recommended_next = patch_report.get("recommended_next_objective")
expected_next = "label_semantics_minimal_redesigned_task_first_pass_training_objective"
future_guard_passed = bool(patch_report.get("patched_guard", {}).get("future_guard_passed"))
actual_forbidden = int(patch_report.get("patched_guard", {}).get("actual_forbidden_model_rows", -1))

if diagnosis != "redesigned_task_smoke_tests_passed_after_guard_patch":
    raise SystemExit(f"ERROR: patched smoke diagnosis not passed: {diagnosis}")
if not all_passed:
    raise SystemExit("ERROR: patched smoke report all_passed is not true")
if recommended_next != expected_next:
    raise SystemExit(f"ERROR: expected recommended_next_objective {expected_next!r}, got {recommended_next!r}")
if not future_guard_passed or actual_forbidden != 0:
    raise SystemExit("ERROR: patched future guard evidence is not clean")
if not guard_audit["passed"].astype(bool).all():
    raise SystemExit("ERROR: guard audit has failed row")

decision_bool = decision["passed"].map(lambda x: str(x).strip().lower() in {"true", "1", "yes", "y"})
if not decision_bool.all():
    raise SystemExit("ERROR: patched smoke decision matrix still has failed rows")

if len(future) != 48:
    raise SystemExit(f"ERROR: expected 48 future run rows, got {len(future)}")
if "authorized_now" in future.columns and not future["authorized_now"].astype(str).str.lower().eq("no").all():
    raise SystemExit("ERROR: future run matrix contains authorized_now != no")

model_values = sorted(future["model"].astype(str).unique().tolist()) if "model" in future.columns else []
allowed_models = {"mean_baseline_no_training", "ridge_regression_summary_features"}
if not set(model_values).issubset(allowed_models):
    raise SystemExit(f"ERROR: future matrix contains unexpected models: {model_values}")

selected_primary_formulation = patch_report.get(
    "selected_primary_formulation",
    spec.get("selected_primary_formulation", "subject_relative_ordinal_affect_regression_v1"),
)

# Convert future matrix into the frozen first-pass matrix. It is a minimal baseline/regression pass,
# not SupCon/DG or broad model search.
run_matrix = future.copy()
run_matrix.insert(0, "objective_run_id", range(1, len(run_matrix) + 1))
run_matrix["objective"] = "label_semantics_minimal_redesigned_task_first_pass_training"
run_matrix["selected_primary_formulation"] = selected_primary_formulation
run_matrix["training_category"] = run_matrix["model"].map({
    "mean_baseline_no_training": "no_training_control",
    "ridge_regression_summary_features": "minimal_classical_regression_baseline",
}).fillna("unknown")
run_matrix["authorized_now"] = "yes_for_this_objective_only"
run_matrix["blocked_from_expansion"] = "yes"
run_matrix.to_csv(run_matrix_path, index=False)

blocked = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change",
    "deep neural training for redesigned task",
    "unregistered feature engineering",
]

guardrail_rows = [
    {
        "guardrail": "frozen_run_matrix",
        "requirement": "Run exactly the 48 rows in docs/idare_label_semantics_minimal_redesigned_task_first_pass_run_matrix.csv.",
        "blocked_if_violated": "yes",
    },
    {
        "guardrail": "allowed_models_only",
        "requirement": "Only mean_baseline_no_training and ridge_regression_summary_features are authorized.",
        "blocked_if_violated": "yes",
    },
    {
        "guardrail": "no_supcon_dg_fusion",
        "requirement": "No SupCon, DG/VREx/domain-generalization, contrastive learning, or EEG+EMG fusion.",
        "blocked_if_violated": "yes",
    },
    {
        "guardrail": "no_broad_search",
        "requirement": "No hyperparameter sweep beyond the fixed minimal baseline specification.",
        "blocked_if_violated": "yes",
    },
    {
        "guardrail": "fold_protocol",
        "requirement": "Use the locked subject-heldout protocol and the selected redesigned task definition.",
        "blocked_if_violated": "yes",
    },
    {
        "guardrail": "report_before_next_step",
        "requirement": "Write report and require human review before any next model/training objective.",
        "blocked_if_violated": "yes",
    },
]
pd.DataFrame(guardrail_rows).to_csv(guardrail_register_path, index=False)

review = {
    "status": "human_review_accepted",
    "created_utc": now,
    "reviewed_report": str(patch_report_md_path),
    "accepted_diagnosis": diagnosis,
    "accepted_all_passed": all_passed,
    "accepted_future_guard_passed": future_guard_passed,
    "accepted_actual_forbidden_model_rows": actual_forbidden,
    "accepted_selected_primary_formulation": selected_primary_formulation,
    "accepted_recommended_next_objective": recommended_next,
    "training_authorized": False,
    "next_selected_step": "create_minimal_redesigned_task_first_pass_objective",
    "blocked": blocked,
}
review_json_path.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

review_md = f"""# I-DARE Redesigned-Task Smoke-Guard Patch Review Status

## Status

Status: human review accepted.

Created UTC: `{now}`

## Review Decision

The patched smoke-guard report is accepted.

Accepted diagnosis: `{diagnosis}`

Accepted all_passed: `{all_passed}`

Accepted future_guard_passed: `{future_guard_passed}`

Accepted actual forbidden model rows: `{actual_forbidden}`

Selected primary formulation: `{selected_primary_formulation}`

Accepted recommended next objective: `{recommended_next}`

## Scientific Meaning

The redesigned task has passed smoke tests after the narrow future-run guard patch.

This authorizes creating a minimal first-pass objective only. It does not authorize broad model search, SupCon/DG, fusion, or final claims.

## Next Selected Step

Create the minimal redesigned-task first-pass objective.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- deep neural training for redesigned task
- unregistered feature engineering
"""
review_md_path.write_text(review_md, encoding="utf-8")

objective = {
    "status": "objective_created",
    "created_utc": now,
    "source_review": str(review_md_path),
    "source_patch_report": str(patch_report_md_path),
    "selected_primary_formulation": selected_primary_formulation,
    "scientific_question": (
        "Does the redesigned subject-relative ordinal/regression task produce a defensible signal under a minimal, frozen "
        "baseline/regression first-pass matrix before any neural, SupCon/DG, fusion, or broad-search work?"
    ),
    "authorized_scope": {
        "run_matrix": str(run_matrix_path),
        "planned_rows": int(len(run_matrix)),
        "models": model_values,
        "modalities": sorted(run_matrix["modality"].astype(str).unique().tolist()) if "modality" in run_matrix.columns else [],
        "tasks": sorted(run_matrix["task"].astype(str).unique().tolist()) if "task" in run_matrix.columns else [],
        "folds": sorted([int(x) for x in run_matrix["fold"].unique().tolist()]) if "fold" in run_matrix.columns else [],
    },
    "authorized_work": [
        "run exactly the frozen 48-row minimal first-pass matrix",
        "compute no-training mean baselines",
        "compute ridge regression summary-feature baselines",
        "use the selected redesigned task target only",
        "write predictions, run summary, metric summary, and report",
        "compare against smoke-test expectations and stop criteria",
    ],
    "not_authorized": blocked,
    "expected_outputs": [
        "docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.md",
        "docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.json",
        "docs/idare_label_semantics_minimal_redesigned_task_first_pass_runs.csv",
        "docs/idare_label_semantics_minimal_redesigned_task_first_pass_predictions.csv",
        "docs/idare_label_semantics_minimal_redesigned_task_first_pass_metric_summary.csv",
    ],
    "pass_criteria": [
        "all 48 planned rows are executed or explicitly accounted for",
        "no unregistered model/method appears",
        "metrics include regression and directional/ordinal summaries per metric plan",
        "results are compared against no-training baseline",
        "no final claim is made",
        "next step is selected only after human review",
    ],
    "next_allowed_step": "prepare_reviewed_label_semantics_minimal_redesigned_task_first_pass_run_command",
    "training_authorized": False,
    "blocked": blocked,
}
objective_json_path.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

objective_md = f"""# I-DARE Label-Semantics Minimal Redesigned-Task First-Pass Objective

## Status

Status: objective created; minimal first-pass only; no broad search is authorized.

Created UTC: `{now}`

## Scientific Question

Does the redesigned subject-relative ordinal/regression task produce a defensible signal under a minimal, frozen baseline/regression first-pass matrix before any neural, SupCon/DG, fusion, or broad-search work?

## Selected Task

Selected primary formulation: `{selected_primary_formulation}`

## Authorized Scope

Frozen run matrix: `docs/idare_label_semantics_minimal_redesigned_task_first_pass_run_matrix.csv`

Planned rows: `{len(run_matrix)}`

Authorized models only:

- `mean_baseline_no_training`
- `ridge_regression_summary_features`

## Authorized Work

- Run exactly the frozen 48-row minimal first-pass matrix.
- Compute no-training mean baselines.
- Compute ridge regression summary-feature baselines.
- Use the selected redesigned task target only.
- Write predictions, run summary, metric summary, and report.
- Compare against smoke-test expectations and stop criteria.

## Not Authorized

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- deep neural training for redesigned task
- unregistered feature engineering

## Expected Outputs

- `docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.md`
- `docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.json`
- `docs/idare_label_semantics_minimal_redesigned_task_first_pass_runs.csv`
- `docs/idare_label_semantics_minimal_redesigned_task_first_pass_predictions.csv`
- `docs/idare_label_semantics_minimal_redesigned_task_first_pass_metric_summary.csv`

## Pass Criteria

- All 48 planned rows are executed or explicitly accounted for.
- No unregistered model/method appears.
- Metrics include regression and directional/ordinal summaries per metric plan.
- Results are compared against no-training baseline.
- No final claim is made.
- Next step is selected only after human review.

## Next Allowed Step

Prepare a reviewed minimal redesigned-task first-pass run command/script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- deep neural training for redesigned task
- unregistered feature engineering
"""
objective_md_path.write_text(objective_md, encoding="utf-8")

status = read_json(status_json_path)
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "prepare_reviewed_label_semantics_minimal_redesigned_task_first_pass_run_command"
status["current_idare_blocked_steps"] = blocked
events = status.get("idare_protocol_events")
if not isinstance(events, list):
    events = []
status["idare_protocol_events"] = events
events.extend([
    {
        "timestamp_utc": now,
        "type": "review",
        "name": "I-DARE redesigned-task smoke-guard patch review",
        "status": f"human review accepted; diagnosis={diagnosis}; all_passed={all_passed}",
        "evidence": str(review_md_path),
        "next_allowed_step": "create/use minimal redesigned-task first-pass objective",
        "blocked": blocked,
    },
    {
        "timestamp_utc": now,
        "type": "objective",
        "name": "I-DARE minimal redesigned-task first-pass objective",
        "status": f"objective created; planned_rows={len(run_matrix)}; no broad search authorized",
        "evidence": str(objective_md_path),
        "next_allowed_step": "prepare reviewed minimal first-pass run command",
        "blocked": blocked,
    },
])
status_json_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Minimal Redesigned-Task First-Pass Objective

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE redesigned-task smoke-guard patch review | human review accepted; diagnosis=`{diagnosis}`; all_passed=`{all_passed}` | `docs/idare_label_semantics_redesigned_task_smoke_guard_patch_review_status.md` | Create/use minimal redesigned-task first-pass objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE minimal redesigned-task first-pass objective | minimal 48-row baseline/regression objective created | `docs/idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.md` | Prepare reviewed run command/script. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Frozen first-pass run matrix: `docs/idare_label_semantics_minimal_redesigned_task_first_pass_run_matrix.csv`.
- Training remains limited to the authorized minimal matrix; broad search remains blocked.
"""
if "I-DARE Minimal Redesigned-Task First-Pass Objective" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_MINIMAL_REDESIGNED_TASK_FIRST_PASS_OBJECTIVE_WRITTEN")
print(review_md_path)
print(review_json_path)
print(objective_md_path)
print(objective_json_path)
print(run_matrix_path)
print(guardrail_register_path)
print("accepted_diagnosis=", diagnosis)
print("selected_primary_formulation=", selected_primary_formulation)
print("planned_rows=", len(run_matrix))
print("authorized_models=", ",".join(model_values))
print("next_allowed_step=prepare_reviewed_label_semantics_minimal_redesigned_task_first_pass_run_command")
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_paths = [
    Path("docs/idare_label_semantics_redesigned_task_smoke_guard_patch_review_status.json"),
    Path("docs/idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

run_matrix = pd.read_csv("docs/idare_label_semantics_minimal_redesigned_task_first_pass_run_matrix.csv")
guardrails = pd.read_csv("docs/idare_label_semantics_minimal_redesigned_task_first_pass_guardrails.csv")
print("run_matrix_rows=", len(run_matrix))
print("guardrail_rows=", len(guardrails))
if len(run_matrix) != 48:
    raise SystemExit("ERROR: run matrix must have 48 rows")
allowed = {"mean_baseline_no_training", "ridge_regression_summary_features"}
models = set(run_matrix["model"].astype(str).unique())
if not models.issubset(allowed):
    raise SystemExit(f"ERROR: unallowed models: {models - allowed}")

term_checks = {
    "docs/idare_label_semantics_redesigned_task_smoke_guard_patch_review_status.md": [
        "human review accepted",
        "redesigned_task_smoke_tests_passed_after_guard_patch",
        "direct full SupCon/DG training",
        "final LOSO claim",
    ],
    "docs/idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.md": [
        "Scientific Question",
        "Authorized Scope",
        "Authorized models only",
        "mean_baseline_no_training",
        "ridge_regression_summary_features",
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

obj = json.loads(Path("docs/idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.json").read_text(encoding="utf-8"))
if obj.get("next_allowed_step") != "prepare_reviewed_label_semantics_minimal_redesigned_task_first_pass_run_command":
    raise SystemExit("ERROR: wrong next_allowed_step")
if "direct full SupCon/DG training" not in obj.get("blocked", []):
    raise SystemExit("ERROR: missing blocked direct full SupCon/DG training")

print("planned_rows=", obj["authorized_scope"]["planned_rows"])
print("next_allowed_step=", obj["next_allowed_step"])
print("ALL_MINIMAL_REDESIGNED_TASK_FIRST_PASS_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "Status|Scientific Question|Selected Task|Authorized Scope|Authorized Work|Not Authorized|Expected Outputs|Pass Criteria|Next Allowed Step" \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.md
grep -nE "Minimal Redesigned-Task First-Pass Objective|Frozen first-pass run matrix|Training remains limited" docs/project_status_current.md | tail -n 10
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_review_status.md \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_review_status.json \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.md \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.json \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_run_matrix.csv \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_guardrails.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE minimal redesigned task first-pass objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
