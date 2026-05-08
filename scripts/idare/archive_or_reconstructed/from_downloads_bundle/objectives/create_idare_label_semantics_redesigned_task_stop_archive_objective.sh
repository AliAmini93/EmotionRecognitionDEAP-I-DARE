#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_redesigned_task_stop_archive_objective.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start redesigned-task spec-fix/stop review + stop/archive objective ====="
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

echo "===== 2) check required spec-fix-or-stop evidence ====="
required=(
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.md
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.json
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.json
  docs/idare_label_semantics_redesigned_task_failed_smoke_diagnosis.csv
  docs/idare_label_semantics_redesigned_task_fix_or_stop_decision_matrix.csv
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_plan.csv
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.md
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.json
  docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv
  docs/idare_label_semantics_task_redesign_spec.md
  docs/idare_label_semantics_task_redesign_spec.json
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

echo "===== 3) create review closeout + redesigned-task stop/archive objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

report_json_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_report.json"
report_md_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md"
smoke_report_json_path = DOCS / "idare_label_semantics_redesigned_task_smoke_tests_report.json"
smoke_decision_path = DOCS / "idare_label_semantics_redesigned_task_smoke_decision_matrix.csv"
failed_diag_path = DOCS / "idare_label_semantics_redesigned_task_failed_smoke_diagnosis.csv"
fix_stop_matrix_path = DOCS / "idare_label_semantics_redesigned_task_fix_or_stop_decision_matrix.csv"
stop_criteria_path = DOCS / "idare_label_semantics_task_redesign_stop_criteria.csv"

review_md_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_report_review_status.md"
review_json_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_report_review_status.json"
objective_md_path = DOCS / "idare_label_semantics_redesigned_task_stop_archive_objective.md"
objective_json_path = DOCS / "idare_label_semantics_redesigned_task_stop_archive_objective.json"
basis_csv_path = DOCS / "idare_label_semantics_redesigned_task_stop_archive_basis.csv"

status_json_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

report = json.loads(report_json_path.read_text(encoding="utf-8"))
smoke_report = json.loads(smoke_report_json_path.read_text(encoding="utf-8"))
failed_diag = pd.read_csv(failed_diag_path)
fix_stop_matrix = pd.read_csv(fix_stop_matrix_path)
smoke_decision = pd.read_csv(smoke_decision_path)

diagnosis = report.get("diagnosis")
recommendation = report.get("recommendation")
recommended_next_objective = report.get("recommended_next_objective")
decision = report.get("decision")
selected = report.get("selected_primary_formulation", smoke_report.get("selected_primary_formulation", "subject_relative_ordinal_affect_regression_v1"))
future_guard_false_positive = report.get("future_run_matrix_guard", {}).get("future_guard_is_false_positive", None)

expected_diagnosis = "redesigned_task_smoke_failure_not_yet_fixable"
expected_recommendation = "stop_archive_objective"
expected_next = "label_semantics_redesigned_task_stop_archive_objective"

if diagnosis != expected_diagnosis:
    raise SystemExit(f"ERROR: expected diagnosis {expected_diagnosis!r}, got {diagnosis!r}")
if recommendation != expected_recommendation:
    raise SystemExit(f"ERROR: expected recommendation {expected_recommendation!r}, got {recommendation!r}")
if recommended_next_objective != expected_next:
    raise SystemExit(f"ERROR: expected recommended_next_objective {expected_next!r}, got {recommended_next_objective!r}")

failed_tests = smoke_report.get("failed_smoke_tests") or []
if not failed_tests:
    try:
        smoke_decision["_passed_bool"] = smoke_decision["passed"].astype(str).str.lower().isin(["true", "1", "yes"])
        failed_tests = smoke_decision.loc[~smoke_decision["_passed_bool"], "smoke_test"].astype(str).tolist()
    except Exception:
        failed_tests = ["future_run_matrix_guard"]
failed_tests = failed_tests or ["future_run_matrix_guard"]

blocked = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change",
    "minimal regression training for the failed redesigned task",
    "any new model search on current global-binary LOSO branch",
]

basis_rows = [
    {
        "evidence_item": "redesigned_task_smoke_tests_report",
        "path": "docs/idare_label_semantics_redesigned_task_smoke_tests_report.md",
        "finding": smoke_report.get("diagnosis", "redesigned_task_smoke_tests_failed"),
        "impact": "training blocked until smoke issue resolved",
    },
    {
        "evidence_item": "spec_fix_or_stop_report",
        "path": str(report_md_path),
        "finding": diagnosis,
        "impact": "stop/archive selected pending human review",
    },
    {
        "evidence_item": "failed_smoke_tests",
        "path": "docs/idare_label_semantics_redesigned_task_failed_smoke_diagnosis.csv",
        "finding": ",".join(failed_tests),
        "impact": "redesigned task not cleared",
    },
    {
        "evidence_item": "fix_or_stop_decision",
        "path": "docs/idare_label_semantics_redesigned_task_fix_or_stop_decision_matrix.csv",
        "finding": recommendation,
        "impact": "do not patch or train unless future human review reverses decision",
    },
    {
        "evidence_item": "future_guard_false_positive",
        "path": str(report_json_path),
        "finding": str(future_guard_false_positive),
        "impact": "not treated as narrow guard false-positive in current report",
    },
]
pd.DataFrame(basis_rows).to_csv(basis_csv_path, index=False)

review = {
    "status": "human_review_accepted",
    "created_utc": now,
    "reviewed_report": str(report_md_path),
    "accepted_selected_primary_formulation": selected,
    "accepted_diagnosis": diagnosis,
    "accepted_decision": decision,
    "accepted_recommendation": recommendation,
    "accepted_recommended_next_objective": recommended_next_objective,
    "accepted_failed_smoke_tests": failed_tests,
    "training_authorized": False,
    "next_selected_step": "create_label_semantics_redesigned_task_stop_archive_objective",
    "blocked": blocked,
}
review_json_path.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

review_md = f"""# I-DARE Label-Semantics Redesigned-Task Spec-Fix-or-Stop Report Review Status

## Status

Status: human review accepted.

Created UTC: `{now}`

## Review Decision

The redesigned-task spec-fix-or-stop report is accepted as the current checkpoint.

Accepted selected formulation: `{selected}`

Accepted diagnosis: `{diagnosis}`

Accepted decision: `{decision}`

Accepted recommendation: `{recommendation}`

Accepted recommended next objective: `{recommended_next_objective}`

Failed smoke tests: `{", ".join(failed_tests)}`

## Scientific Meaning

The redesigned subject-relative ordinal/regression branch is not cleared for training.

The current evidence path says stop/archive this redesigned task branch, not patch or continue to minimal regression training.

## Next Selected Step

Create a stop/archive objective for the redesigned task branch.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- minimal regression training for the failed redesigned task
- any new model search on current global-binary LOSO branch
"""
review_md_path.write_text(review_md, encoding="utf-8")

objective = {
    "status": "objective_created",
    "created_utc": now,
    "source_review": str(review_md_path),
    "source_report": str(report_md_path),
    "selected_primary_formulation": selected,
    "scientific_question": (
        "Can the redesigned subject-relative ordinal/regression branch be formally stopped/archived "
        "without losing reproducibility, evidence, or future restart conditions?"
    ),
    "authorized_work": [
        "write a stop/archive closeout report",
        "freeze the current redesigned-task branch status",
        "preserve all evidence artifacts and diagnostics",
        "define explicit future restart conditions",
        "define what remains scientifically blocked",
        "do not delete any artifacts",
        "do not run training",
        "do not run broad hyperparameter search",
        "do not start a new model family",
    ],
    "required_inputs": [
        "docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md",
        "docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.json",
        "docs/idare_label_semantics_redesigned_task_failed_smoke_diagnosis.csv",
        "docs/idare_label_semantics_redesigned_task_fix_or_stop_decision_matrix.csv",
        "docs/idare_label_semantics_redesigned_task_smoke_guard_patch_plan.csv",
        "docs/idare_label_semantics_redesigned_task_smoke_tests_report.md",
        "docs/idare_label_semantics_task_redesign_spec.md",
        "docs/idare_label_semantics_task_redesign_stop_criteria.csv",
    ],
    "expected_outputs": [
        "docs/idare_label_semantics_redesigned_task_stop_archive_report.md",
        "docs/idare_label_semantics_redesigned_task_stop_archive_report.json",
        "docs/idare_label_semantics_redesigned_task_archive_manifest.csv",
        "docs/idare_label_semantics_redesigned_task_restart_conditions.csv",
        "docs/idare_label_semantics_redesigned_task_blocked_work_register.csv",
    ],
    "pass_criteria": [
        "archive/stop decision is explicit",
        "all evidence artifacts are listed in an archive manifest",
        "future restart conditions are explicit and narrow",
        "training remains blocked",
        "direct full SupCon/DG training remains blocked",
        "broad hyperparameter search remains blocked",
        "final LOSO claim remains blocked",
    ],
    "next_allowed_step": "prepare_reviewed_label_semantics_redesigned_task_stop_archive_command",
    "blocked": blocked,
}
objective_json_path.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

objective_md = f"""# I-DARE Label-Semantics Redesigned-Task Stop/Archive Objective

## Status

Status: objective created; stop/archive closeout only; no training is authorized.

Created UTC: `{now}`

## Scientific Question

Can the redesigned subject-relative ordinal/regression branch be formally stopped/archived without losing reproducibility, evidence, or future restart conditions?

## Accepted Decision Basis

Selected formulation: `{selected}`

Accepted diagnosis: `{diagnosis}`

Accepted recommendation: `{recommendation}`

Failed smoke tests: `{", ".join(failed_tests)}`

## Authorized Work

- Write a stop/archive closeout report.
- Freeze the current redesigned-task branch status.
- Preserve all evidence artifacts and diagnostics.
- Define explicit future restart conditions.
- Define what remains scientifically blocked.
- Do not delete any artifacts.
- Do not run training.
- Do not run broad hyperparameter search.
- Do not start a new model family.

## Expected Outputs

- `docs/idare_label_semantics_redesigned_task_stop_archive_report.md`
- `docs/idare_label_semantics_redesigned_task_stop_archive_report.json`
- `docs/idare_label_semantics_redesigned_task_archive_manifest.csv`
- `docs/idare_label_semantics_redesigned_task_restart_conditions.csv`
- `docs/idare_label_semantics_redesigned_task_blocked_work_register.csv`

## Pass Criteria

- Archive/stop decision is explicit.
- All evidence artifacts are listed in an archive manifest.
- Future restart conditions are explicit and narrow.
- Training remains blocked.
- direct full SupCon/DG training remains blocked.
- broad hyperparameter search remains blocked.
- final LOSO claim remains blocked.

## Next Allowed Step

Prepare a reviewed stop/archive closeout command/script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- minimal regression training for the failed redesigned task
- any new model search on current global-binary LOSO branch
"""
objective_md_path.write_text(objective_md, encoding="utf-8")

status = json.loads(status_json_path.read_text(encoding="utf-8"))
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "prepare_reviewed_label_semantics_redesigned_task_stop_archive_command"
status["current_idare_blocked_steps"] = blocked
events = status.get("idare_protocol_events")
if not isinstance(events, list):
    events = []
status["idare_protocol_events"] = events
events.extend([
    {
        "timestamp_utc": now,
        "type": "review",
        "name": "I-DARE label-semantics redesigned-task spec-fix-or-stop report review",
        "status": f"human review accepted; recommendation={recommendation}",
        "evidence": str(review_md_path),
        "next_allowed_step": "create/use redesigned-task stop/archive objective",
        "blocked": blocked,
    },
    {
        "timestamp_utc": now,
        "type": "objective",
        "name": "I-DARE label-semantics redesigned-task stop/archive objective",
        "status": "objective created; stop/archive closeout only; no training authorized",
        "evidence": str(objective_md_path),
        "next_allowed_step": "prepare reviewed stop/archive closeout command",
        "blocked": blocked,
    },
])
status_json_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Label-Semantics Redesigned-Task Stop/Archive Objective

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE label-semantics redesigned-task spec-fix-or-stop report review | human review accepted; recommendation=`{recommendation}` | `docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report_review_status.md` | Create/use redesigned-task stop/archive objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE label-semantics redesigned-task stop/archive objective | stop/archive closeout objective created; no training authorized | `docs/idare_label_semantics_redesigned_task_stop_archive_objective.md` | Prepare reviewed stop/archive closeout command/script. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- A stop/archive objective is defined in `docs/idare_label_semantics_redesigned_task_stop_archive_objective.md`.
- Training remains blocked.
"""
if "I-DARE Label-Semantics Redesigned-Task Stop/Archive Objective" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_REDESIGNED_TASK_STOP_ARCHIVE_OBJECTIVE_WRITTEN")
print(review_md_path)
print(review_json_path)
print(objective_md_path)
print(objective_json_path)
print(basis_csv_path)
print("diagnosis=", diagnosis)
print("recommendation=", recommendation)
print("recommended_next_objective=", recommended_next_objective)
print("next_allowed_step=prepare_reviewed_label_semantics_redesigned_task_stop_archive_command")
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_paths = [
    Path("docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report_review_status.json"),
    Path("docs/idare_label_semantics_redesigned_task_stop_archive_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

basis = pd.read_csv("docs/idare_label_semantics_redesigned_task_stop_archive_basis.csv")
print("basis_rows=", len(basis))
if len(basis) < 5:
    raise SystemExit("ERROR: basis too short")

term_checks = {
    "docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report_review_status.md": [
        "human review accepted",
        "stop_archive_objective",
        "redesigned_task_smoke_failure_not_yet_fixable",
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "final LOSO claim",
    ],
    "docs/idare_label_semantics_redesigned_task_stop_archive_objective.md": [
        "Scientific Question",
        "Authorized Work",
        "Expected Outputs",
        "restart conditions",
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

obj = json.loads(Path("docs/idare_label_semantics_redesigned_task_stop_archive_objective.json").read_text(encoding="utf-8"))
if obj.get("next_allowed_step") != "prepare_reviewed_label_semantics_redesigned_task_stop_archive_command":
    raise SystemExit("ERROR: wrong next_allowed_step")
if "direct full SupCon/DG training" not in obj.get("blocked", []):
    raise SystemExit("ERROR: missing blocked direct full SupCon/DG training")

print("next_allowed_step=", obj.get("next_allowed_step"))
print("ALL_REDESIGNED_TASK_STOP_ARCHIVE_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "Status|Scientific Question|Accepted Decision Basis|Authorized Work|Expected Outputs|Pass Criteria|Next Allowed Step" \
  docs/idare_label_semantics_redesigned_task_stop_archive_objective.md
grep -nE "Stop/Archive Objective|stop/archive objective|Training remains blocked" docs/project_status_current.md | tail -n 10
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report_review_status.md \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report_review_status.json \
  docs/idare_label_semantics_redesigned_task_stop_archive_objective.md \
  docs/idare_label_semantics_redesigned_task_stop_archive_objective.json \
  docs/idare_label_semantics_redesigned_task_stop_archive_basis.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE redesigned task stop archive objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
