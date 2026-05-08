#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start redesigned-task smoke review + spec-fix-or-stop objective ====="
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

echo "===== 2) check required smoke-test evidence ====="
required=(
  docs/idare_label_semantics_redesigned_task_smoke_tests_objective.md
  docs/idare_label_semantics_redesigned_task_smoke_tests_objective.json
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.md
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.json
  docs/idare_label_semantics_redesigned_task_target_audit.csv
  docs/idare_label_semantics_redesigned_task_fold_audit.csv
  docs/idare_label_semantics_redesigned_task_metric_sanity.csv
  docs/idare_label_semantics_redesigned_task_baseline_control_summary.csv
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

echo "===== 3) create smoke-test review closeout + spec-fix-or-stop objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

report_json_path = DOCS / "idare_label_semantics_redesigned_task_smoke_tests_report.json"
decision_csv_path = DOCS / "idare_label_semantics_redesigned_task_smoke_decision_matrix.csv"
target_audit_csv_path = DOCS / "idare_label_semantics_redesigned_task_target_audit.csv"
fold_audit_csv_path = DOCS / "idare_label_semantics_redesigned_task_fold_audit.csv"
metric_sanity_csv_path = DOCS / "idare_label_semantics_redesigned_task_metric_sanity.csv"
baseline_csv_path = DOCS / "idare_label_semantics_redesigned_task_baseline_control_summary.csv"
spec_json_path = DOCS / "idare_label_semantics_task_redesign_spec.json"

review_md_path = DOCS / "idare_label_semantics_redesigned_task_smoke_tests_review_status.md"
review_json_path = DOCS / "idare_label_semantics_redesigned_task_smoke_tests_review_status.json"
objective_md_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.md"
objective_json_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.json"
failed_smokes_csv_path = DOCS / "idare_label_semantics_redesigned_task_failed_smoke_summary.csv"

status_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

report = json.loads(report_json_path.read_text(encoding="utf-8"))
spec = json.loads(spec_json_path.read_text(encoding="utf-8"))
decision_df = pd.read_csv(decision_csv_path)
target_audit = pd.read_csv(target_audit_csv_path)
fold_audit = pd.read_csv(fold_audit_csv_path)
metric_sanity = pd.read_csv(metric_sanity_csv_path)
baseline = pd.read_csv(baseline_csv_path)

selected = report.get("selected_primary_formulation", spec.get("selected_primary_formulation", "subject_relative_ordinal_affect_regression_v1"))
diagnosis = report.get("diagnosis", "redesigned_task_smoke_tests_failed")
recommended = report.get("recommended_next_objective", "label_semantics_redesigned_task_spec_fix_or_stop_objective")
all_passed = bool(report.get("all_passed", False))

# Normalize passed column robustly.
def to_bool(x):
    if isinstance(x, bool):
        return x
    s = str(x).strip().lower()
    return s in {"true", "1", "yes", "y"}

decision_df["_passed_bool"] = decision_df["passed"].map(to_bool)
failed = decision_df.loc[~decision_df["_passed_bool"]].copy()
failed_out = failed.drop(columns=["_passed_bool"], errors="ignore")
failed_out.to_csv(failed_smokes_csv_path, index=False)

failed_names = failed["smoke_test"].astype(str).tolist()
if not failed_names and not all_passed:
    failed_names = ["unknown_or_report_level_failure"]

blocked = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change",
    "minimal regression training before smoke-fix/stop review",
]

review = {
    "status": "human_review_accepted",
    "created_utc": now,
    "reviewed_report": "docs/idare_label_semantics_redesigned_task_smoke_tests_report.md",
    "accepted_selected_primary_formulation": selected,
    "accepted_diagnosis": diagnosis,
    "accepted_all_passed": all_passed,
    "accepted_failed_smoke_tests": failed_names,
    "accepted_recommended_next_objective": recommended,
    "next_selected_step": "create_label_semantics_redesigned_task_spec_fix_or_stop_objective",
    "training_authorized": False,
    "blocked": blocked,
}
review_json_path.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

failed_lines = "\n".join([f"- `{x}`" for x in failed_names]) if failed_names else "- none"
review_md = f"""# I-DARE Label-Semantics Redesigned-Task Smoke Tests Review Status

## Status

Status: human review accepted.

Created UTC: `{now}`

## Review Decision

The redesigned-task smoke-test report is accepted as the current checkpoint.

Accepted selected formulation: `{selected}`

Accepted diagnosis: `{diagnosis}`

All smoke tests passed: `{all_passed}`

Failed smoke tests:

{failed_lines}

Accepted recommended next objective: `{recommended}`

## Scientific Meaning

The redesigned target is not yet cleared for training.

The next step must determine whether the failed smoke condition is a fixable spec/implementation issue or a reason to stop/archive this redesigned branch.

## Next Selected Step

Create a redesigned-task spec-fix-or-stop objective.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- minimal regression training before smoke-fix/stop review
"""
review_md_path.write_text(review_md, encoding="utf-8")

objective = {
    "status": "objective_created",
    "created_utc": now,
    "source_review": str(review_md_path),
    "source_smoke_report": "docs/idare_label_semantics_redesigned_task_smoke_tests_report.md",
    "selected_primary_formulation": selected,
    "scientific_question": (
        "Why did the redesigned-task smoke tests fail, and should the issue be fixed with a "
        "narrow spec/implementation patch or should the redesigned branch be stopped/archived?"
    ),
    "failed_smoke_tests": failed_names,
    "authorized_work": [
        "read the smoke-test decision matrix and all smoke audit CSVs",
        "identify the exact failed smoke condition(s)",
        "classify each failure as implementation bug, spec mismatch, data/label degeneracy, or stop/archive trigger",
        "recommend either one narrow fix objective or a stop/archive closeout",
        "no training",
        "no minimal regression run",
        "no direct full SupCon/DG training",
        "no broad hyperparameter search",
    ],
    "required_inputs": [
        "docs/idare_label_semantics_redesigned_task_smoke_tests_report.md",
        "docs/idare_label_semantics_redesigned_task_smoke_tests_report.json",
        "docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv",
        "docs/idare_label_semantics_redesigned_task_target_audit.csv",
        "docs/idare_label_semantics_redesigned_task_fold_audit.csv",
        "docs/idare_label_semantics_redesigned_task_metric_sanity.csv",
        "docs/idare_label_semantics_redesigned_task_baseline_control_summary.csv",
        "docs/idare_label_semantics_task_redesign_spec.md",
        "docs/idare_label_semantics_task_redesign_stop_criteria.csv",
    ],
    "expected_outputs": [
        "docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md",
        "docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.json",
        "docs/idare_label_semantics_redesigned_task_failed_smoke_diagnosis.csv",
        "docs/idare_label_semantics_redesigned_task_fix_or_stop_decision_matrix.csv",
    ],
    "pass_criteria": [
        "every failed smoke test has an explicit cause classification",
        "the recommendation is exactly one of: narrow_fix_objective, stop_archive_objective",
        "if a fix is recommended, it must be narrow and must not authorize training",
        "if stop/archive is recommended, no further redesigned-task training is authorized",
        "direct full SupCon/DG training remains blocked",
        "broad hyperparameter search remains blocked",
        "final LOSO claim remains blocked",
    ],
    "next_allowed_step": "prepare_reviewed_label_semantics_redesigned_task_spec_fix_or_stop_command",
    "blocked": blocked,
}
objective_json_path.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

objective_md = f"""# I-DARE Label-Semantics Redesigned-Task Spec-Fix-or-Stop Objective

## Status

Status: objective created; read-only failure triage only; no training is authorized.

Created UTC: `{now}`

## Scientific Question

Why did the redesigned-task smoke tests fail, and should the issue be fixed with a narrow spec/implementation patch or should the redesigned branch be stopped/archived?

## Current Smoke-Test Result

Selected formulation: `{selected}`

Diagnosis: `{diagnosis}`

All smoke tests passed: `{all_passed}`

Failed smoke tests:

{failed_lines}

## Authorized Work

- Read the smoke-test decision matrix and all smoke audit CSVs.
- Identify the exact failed smoke condition(s).
- Classify each failure as one of:
  - implementation bug;
  - spec mismatch;
  - data/label degeneracy;
  - stop/archive trigger.
- Recommend exactly one of:
  - `narrow_fix_objective`;
  - `stop_archive_objective`.
- No training.
- No minimal regression run.
- No direct full SupCon/DG training.
- No broad hyperparameter search.

## Required Inputs

- `docs/idare_label_semantics_redesigned_task_smoke_tests_report.md`
- `docs/idare_label_semantics_redesigned_task_smoke_tests_report.json`
- `docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv`
- `docs/idare_label_semantics_redesigned_task_target_audit.csv`
- `docs/idare_label_semantics_redesigned_task_fold_audit.csv`
- `docs/idare_label_semantics_redesigned_task_metric_sanity.csv`
- `docs/idare_label_semantics_redesigned_task_baseline_control_summary.csv`
- `docs/idare_label_semantics_task_redesign_spec.md`
- `docs/idare_label_semantics_task_redesign_stop_criteria.csv`

## Expected Outputs

- `docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md`
- `docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.json`
- `docs/idare_label_semantics_redesigned_task_failed_smoke_diagnosis.csv`
- `docs/idare_label_semantics_redesigned_task_fix_or_stop_decision_matrix.csv`

## Pass Criteria

- Every failed smoke test has an explicit cause classification.
- The recommendation is exactly one of:
  - `narrow_fix_objective`;
  - `stop_archive_objective`.
- If a fix is recommended, it is narrow and does not authorize training.
- If stop/archive is recommended, no further redesigned-task training is authorized.
- direct full SupCon/DG training remains blocked.
- broad hyperparameter search remains blocked.
- final LOSO claim remains blocked.

## Next Allowed Step

Prepare a reviewed redesigned-task spec-fix-or-stop analysis command/script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- minimal regression training before smoke-fix/stop review
"""
objective_md_path.write_text(objective_md, encoding="utf-8")

# Update project status.
status = json.loads(status_path.read_text(encoding="utf-8"))
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "prepare_reviewed_label_semantics_redesigned_task_spec_fix_or_stop_command"
status["current_idare_blocked_steps"] = blocked
events = status.get("idare_protocol_events")
if not isinstance(events, list):
    events = []
status["idare_protocol_events"] = events
events.extend([
    {
        "timestamp_utc": now,
        "type": "review",
        "name": "I-DARE label-semantics redesigned-task smoke-tests review",
        "status": f"human review accepted; diagnosis={diagnosis}; all_passed={all_passed}",
        "evidence": str(review_md_path),
        "next_allowed_step": "create/use redesigned-task spec-fix-or-stop objective",
        "blocked": blocked,
    },
    {
        "timestamp_utc": now,
        "type": "objective",
        "name": "I-DARE label-semantics redesigned-task spec-fix-or-stop objective",
        "status": f"objective created; failed_smokes={failed_names}; no training authorized",
        "evidence": str(objective_md_path),
        "next_allowed_step": "prepare reviewed spec-fix-or-stop command",
        "blocked": blocked,
    },
])
status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Label-Semantics Redesigned-Task Spec-Fix-or-Stop Objective

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE label-semantics redesigned-task smoke-tests review | human review accepted; diagnosis=`{diagnosis}`; all_passed=`{all_passed}` | `docs/idare_label_semantics_redesigned_task_smoke_tests_review_status.md` | Create/use redesigned-task spec-fix-or-stop objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE label-semantics redesigned-task spec-fix-or-stop objective | read-only triage objective created; no training authorized | `docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.md` | Prepare reviewed spec-fix-or-stop analysis command/script. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Failed smoke tests: `{", ".join(failed_names)}`.
- Training remains blocked until this failure triage is reviewed.
"""
if "I-DARE Label-Semantics Redesigned-Task Spec-Fix-or-Stop Objective" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_REDESIGNED_TASK_SPEC_FIX_OR_STOP_OBJECTIVE_WRITTEN")
print(review_md_path)
print(review_json_path)
print(objective_md_path)
print(objective_json_path)
print(failed_smokes_csv_path)
print("diagnosis=", diagnosis)
print("all_passed=", all_passed)
print("failed_smoke_tests=", ",".join(failed_names))
print("next_allowed_step=prepare_reviewed_label_semantics_redesigned_task_spec_fix_or_stop_command")
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_paths = [
    Path("docs/idare_label_semantics_redesigned_task_smoke_tests_review_status.json"),
    Path("docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

failed = pd.read_csv("docs/idare_label_semantics_redesigned_task_failed_smoke_summary.csv")
print("failed_smoke_rows=", len(failed))

term_checks = {
    "docs/idare_label_semantics_redesigned_task_smoke_tests_review_status.md": [
        "human review accepted",
        "redesigned_task_smoke_tests_failed",
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "final LOSO claim",
    ],
    "docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.md": [
        "Scientific Question",
        "Authorized Work",
        "Expected Outputs",
        "narrow_fix_objective",
        "stop_archive_objective",
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

obj = json.loads(Path("docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.json").read_text(encoding="utf-8"))
if obj.get("next_allowed_step") != "prepare_reviewed_label_semantics_redesigned_task_spec_fix_or_stop_command":
    raise SystemExit("ERROR: wrong next_allowed_step")
if "direct full SupCon/DG training" not in obj.get("blocked", []):
    raise SystemExit("ERROR: missing blocked direct full SupCon/DG training")

print("failed_smoke_tests=", obj.get("failed_smoke_tests"))
print("next_allowed_step=", obj.get("next_allowed_step"))
print("ALL_REDESIGNED_TASK_SPEC_FIX_OR_STOP_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "Status|Scientific Question|Current Smoke-Test Result|Authorized Work|Expected Outputs|Pass Criteria|Next Allowed Step" \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.md
grep -nE "Spec-Fix-or-Stop Objective|Failed smoke tests" docs/project_status_current.md | tail -n 8
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_label_semantics_redesigned_task_smoke_tests_review_status.md \
  docs/idare_label_semantics_redesigned_task_smoke_tests_review_status.json \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.md \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.json \
  docs/idare_label_semantics_redesigned_task_failed_smoke_summary.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE redesigned task fix-or-stop objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
