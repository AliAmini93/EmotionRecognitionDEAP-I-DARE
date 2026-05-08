#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_redesigned_task_smoke_guard_patch_objective.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start manual audit + smoke-guard patch objective ====="
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
  echo "ERROR: repo is not clean; commit/stash before creating patch objective." >&2
  git status --short
  exit 2
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required evidence docs ====="
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
  docs/idare_label_semantics_task_redesign_future_run_matrix.csv
  docs/idare_label_semantics_task_redesign_spec.md
  docs/idare_label_semantics_task_redesign_spec.json
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

echo "===== 3) create manual-audit review + narrow smoke-guard patch objective ====="
"$PY" - <<'PY'
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

future_matrix_path = DOCS / "idare_label_semantics_task_redesign_future_run_matrix.csv"
fix_stop_report_json_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_report.json"
fix_stop_report_md_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md"
smoke_report_json_path = DOCS / "idare_label_semantics_redesigned_task_smoke_tests_report.json"

manual_review_md_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_manual_review_status.md"
manual_review_json_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_manual_review_status.json"
objective_md_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_patch_objective.md"
objective_json_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_patch_objective.json"
manual_audit_csv_path = DOCS / "idare_label_semantics_redesigned_task_future_matrix_manual_audit.csv"
patch_requirements_csv_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_patch_requirements.csv"

status_json_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

future = pd.read_csv(future_matrix_path)
fix_stop_report = json.loads(fix_stop_report_json_path.read_text(encoding="utf-8"))
smoke_report = json.loads(smoke_report_json_path.read_text(encoding="utf-8"))

required_cols = {"planned_run_id", "model", "modality", "task", "fold", "target", "authorized_now", "requires_prior_objective", "notes"}
missing = sorted(required_cols - set(future.columns))
if missing:
    raise SystemExit(f"ERROR: future run matrix missing columns: {missing}")

model_series = future["model"].astype(str).str.strip()
notes_series = future["notes"].astype(str)
authorized_now_all_no = future["authorized_now"].astype(str).str.lower().eq("no").all()
future_rows = int(len(future))

# Exact model-level audit. Notes are guardrail prose and must not be treated as authorized methods.
forbidden_model_regex = re.compile(r"(supcon|supervised_contrastive|contrastive|vrex|domain[_ -]?generalization|(^|[^a-z])dg([^a-z]|$)|fusion)", re.I)
actual_forbidden_model_mask = model_series.map(lambda x: bool(forbidden_model_regex.search(x)))
actual_forbidden_rows = future.loc[actual_forbidden_model_mask].copy()

notes_negative_guardrail_mask = notes_series.str.contains("no SupCon/DG", case=False, regex=False) | notes_series.str.contains("no contrastive", case=False, regex=False)
notes_mentions_supcon_dg = notes_series.str.contains("SupCon", case=False, regex=False) | notes_series.str.contains("DG", case=False, regex=False)
ridge_model_rows = future.loc[model_series.str.contains("ridge", case=False, regex=False)].copy()

allowed_models = sorted(model_series.unique().tolist())
only_expected_models = set(allowed_models) <= {"mean_baseline_no_training", "ridge_regression_summary_features"}

manual_audit_rows = [
    {
        "check": "future_run_matrix_rows",
        "finding": future_rows,
        "expected": 48,
        "passed": future_rows == 48,
        "interpretation": "The planned matrix has the expected 48 minimal rows.",
    },
    {
        "check": "authorized_now_all_no",
        "finding": bool(authorized_now_all_no),
        "expected": True,
        "passed": bool(authorized_now_all_no),
        "interpretation": "The matrix is a future plan, not an immediate training authorization.",
    },
    {
        "check": "unique_model_values",
        "finding": ";".join(allowed_models),
        "expected": "mean_baseline_no_training;ridge_regression_summary_features",
        "passed": bool(only_expected_models),
        "interpretation": "Model column contains only no-training mean baseline and ridge summary-feature baseline.",
    },
    {
        "check": "actual_forbidden_model_rows",
        "finding": int(actual_forbidden_model_mask.sum()),
        "expected": 0,
        "passed": int(actual_forbidden_model_mask.sum()) == 0,
        "interpretation": "No actual model/method row requests SupCon, DG, VREx, fusion, or contrastive learning.",
    },
    {
        "check": "notes_mentions_supcon_dg",
        "finding": int(notes_mentions_supcon_dg.sum()),
        "expected": "allowed only as negative guardrail prose",
        "passed": bool(notes_negative_guardrail_mask.all()),
        "interpretation": "SupCon/DG appears in notes only as 'no SupCon/DG or broad search', so it should not fail the guard.",
    },
    {
        "check": "ridge_rows",
        "finding": int(len(ridge_model_rows)),
        "expected": 24,
        "passed": int(len(ridge_model_rows)) == 24,
        "interpretation": "Ridge rows are allowed baseline rows; the substring 'dg' inside 'ridge' must not be interpreted as DG.",
    },
]
manual_audit = pd.DataFrame(manual_audit_rows)
manual_audit.to_csv(manual_audit_csv_path, index=False)

if int(actual_forbidden_model_mask.sum()) != 0:
    actual_forbidden_rows.to_csv(DOCS / "idare_label_semantics_redesigned_task_actual_forbidden_future_rows.csv", index=False)
    raise SystemExit("ERROR: actual forbidden model rows found; cannot create narrow guard patch objective.")

if not bool(manual_audit["passed"].all()):
    raise SystemExit("ERROR: manual audit did not fully pass; cannot create narrow guard patch objective.")

accepted_previous_report = {
    "diagnosis": fix_stop_report.get("diagnosis"),
    "recommendation": fix_stop_report.get("recommendation"),
    "recommended_next_objective": fix_stop_report.get("recommended_next_objective"),
}
selected_primary_formulation = smoke_report.get("selected_primary_formulation", "subject_relative_ordinal_affect_regression_v1")

new_diagnosis = "future_run_matrix_guard_false_positive_from_notes_and_ridge_token"
new_recommendation = "narrow_smoke_guard_patch_and_rerun_smokes"
new_next_objective = "label_semantics_redesigned_task_smoke_guard_patch_objective"

blocked = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change",
    "minimal regression training before patched smoke-test review",
]

patch_requirements = [
    {
        "requirement_id": "R1",
        "requirement": "Guard must evaluate explicit model/method columns, not free-text notes.",
        "reason": "Notes contain negated text such as 'no SupCon/DG or broad search'.",
        "pass_condition": "Rows with notes-only negated SupCon/DG do not fail.",
    },
    {
        "requirement_id": "R2",
        "requirement": "Guard must use token-aware DG detection.",
        "reason": "The substring 'dg' appears inside 'ridge_regression_summary_features'.",
        "pass_condition": "Ridge baseline rows do not fail the DG guard.",
    },
    {
        "requirement_id": "R3",
        "requirement": "Actual forbidden future model rows remain blocked.",
        "reason": "SupCon, VREx, domain-generalization, fusion, or contrastive model rows must still fail before authorization.",
        "pass_condition": "Explicit forbidden model names in model/method columns fail the guard.",
    },
    {
        "requirement_id": "R4",
        "requirement": "Patch must rerun the same smoke tests after guard correction.",
        "reason": "A narrow patch is not sufficient unless the smoke report is regenerated.",
        "pass_condition": "all_passed=True or any new failure is explicitly reported.",
    },
    {
        "requirement_id": "R5",
        "requirement": "Patch must not authorize training.",
        "reason": "Training can only follow patched smoke-test review.",
        "pass_condition": "No training outputs are produced by the patch objective.",
    },
]
pd.DataFrame(patch_requirements).to_csv(patch_requirements_csv_path, index=False)

manual_review = {
    "status": "human_review_supersedes_prior_stop_archive_recommendation",
    "created_utc": now,
    "reviewed_report": str(fix_stop_report_md_path),
    "prior_report_conclusion": accepted_previous_report,
    "manual_audit_file": str(manual_audit_csv_path),
    "selected_primary_formulation": selected_primary_formulation,
    "manual_audit_diagnosis": new_diagnosis,
    "manual_review_decision": "do_not_stop_archive_yet_create_narrow_smoke_guard_patch_objective",
    "rationale": [
        "future matrix model column contains only mean_baseline_no_training and ridge_regression_summary_features",
        "SupCon/DG appears only in notes as a negative guardrail phrase",
        "ridge rows are valid baseline rows and must not be interpreted as DG",
        "there are zero actual forbidden model rows",
    ],
    "training_authorized": False,
    "next_selected_step": new_next_objective,
    "blocked": blocked,
}
manual_review_json_path.write_text(json.dumps(manual_review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

manual_review_md = f"""# I-DARE Redesigned-Task Spec-Fix-or-Stop Manual Review Status

## Status

Status: human review supersedes the prior stop/archive recommendation for this specific smoke-guard failure.

Created UTC: `{now}`

## Manual Review Decision

Prior report diagnosis: `{accepted_previous_report.get("diagnosis")}`

Prior report recommendation: `{accepted_previous_report.get("recommendation")}`

Manual audit diagnosis: `{new_diagnosis}`

Manual review decision: `do_not_stop_archive_yet_create_narrow_smoke_guard_patch_objective`

## Evidence

Manual inspection of `docs/idare_label_semantics_task_redesign_future_run_matrix.csv` shows:

- model column contains only `mean_baseline_no_training` and `ridge_regression_summary_features`;
- there are zero actual SupCon/DG/VREx/fusion/contrastive model rows;
- `SupCon/DG` appears only in notes as a negative guardrail phrase: `no SupCon/DG or broad search`;
- `ridge_regression_summary_features` is an allowed baseline and must not trigger a substring `dg` check.

## Scientific Meaning

The redesigned task is not cleared for training yet.

However, the current failure is now interpreted as a smoke-guard implementation/spec mismatch, not sufficient evidence for stop/archive.

## Next Selected Step

Create a narrow smoke-guard patch objective and then rerun the same redesigned-task smoke tests.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- minimal regression training before patched smoke-test review
"""
manual_review_md_path.write_text(manual_review_md, encoding="utf-8")

objective = {
    "status": "objective_created",
    "created_utc": now,
    "source_manual_review": str(manual_review_md_path),
    "source_future_matrix": str(future_matrix_path),
    "source_prior_report": str(fix_stop_report_md_path),
    "selected_primary_formulation": selected_primary_formulation,
    "scientific_question": (
        "Can the redesigned-task smoke future-run guard be patched narrowly so that it blocks actual SupCon/DG/fusion/broad-search rows "
        "without failing on negated notes or the substring 'dg' inside 'ridge'?"
    ),
    "manual_audit_diagnosis": new_diagnosis,
    "authorized_work": [
        "patch only the future_run_matrix_guard logic in the smoke-test script/command",
        "evaluate forbidden methods only from explicit model/method columns",
        "use token-aware matching for DG/domain-generalization",
        "treat notes as explanatory metadata unless an explicit authorization field says otherwise",
        "rerun the same redesigned-task smoke tests",
        "write a patched smoke-test report",
        "do not run minimal regression training",
        "do not run SupCon/DG training",
        "do not run broad hyperparameter search",
    ],
    "required_inputs": [
        "docs/idare_label_semantics_redesigned_task_smoke_tests_report.md",
        "docs/idare_label_semantics_redesigned_task_smoke_tests_report.json",
        "docs/idare_label_semantics_task_redesign_future_run_matrix.csv",
        "docs/idare_label_semantics_redesigned_task_future_matrix_manual_audit.csv",
        "docs/idare_label_semantics_redesigned_task_smoke_guard_patch_requirements.csv",
    ],
    "expected_outputs": [
        "docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.md",
        "docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.json",
        "docs/idare_label_semantics_redesigned_task_smoke_guard_audit.csv",
        "updated docs/idare_label_semantics_redesigned_task_smoke_tests_report.md",
        "updated docs/idare_label_semantics_redesigned_task_smoke_tests_report.json",
    ],
    "pass_criteria": [
        "future matrix guard passes for the current mean/ridge-only matrix",
        "actual forbidden model rows would still fail the guard",
        "all other smoke tests are rerun and reported",
        "training remains blocked unless patched smoke report passes and is reviewed",
        "direct full SupCon/DG training remains blocked",
        "broad hyperparameter search remains blocked",
        "final LOSO claim remains blocked",
    ],
    "next_allowed_step": "prepare_reviewed_label_semantics_redesigned_task_smoke_guard_patch_command",
    "blocked": blocked,
}
objective_json_path.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

objective_md = f"""# I-DARE Label-Semantics Redesigned-Task Smoke-Guard Patch Objective

## Status

Status: objective created; narrow smoke-guard patch only; no training is authorized.

Created UTC: `{now}`

## Scientific Question

Can the redesigned-task smoke future-run guard be patched narrowly so that it blocks actual SupCon/DG/fusion/broad-search rows without failing on negated notes or the substring `dg` inside `ridge`?

## Manual Audit Diagnosis

Diagnosis: `{new_diagnosis}`

Prior stop/archive recommendation is superseded for this specific smoke-guard failure.

## Evidence Summary

- Future run matrix rows: `{future_rows}`.
- Authorized-now rows all `no`: `{authorized_now_all_no}`.
- Unique model values: `{", ".join(allowed_models)}`.
- Actual forbidden model rows: `{int(actual_forbidden_model_mask.sum())}`.
- Notes mention SupCon/DG only as negative guardrail prose.
- Ridge baseline rows: `{int(len(ridge_model_rows))}`.

## Authorized Work

- Patch only the `future_run_matrix_guard` logic in the smoke-test script/command.
- Evaluate forbidden methods only from explicit `model` / `method` columns.
- Use token-aware matching for DG / domain-generalization.
- Treat notes as explanatory metadata unless an explicit authorization field says otherwise.
- Rerun the same redesigned-task smoke tests.
- Write a patched smoke-test report.
- Do not run minimal regression training.
- Do not run SupCon/DG training.
- Do not run broad hyperparameter search.

## Required Inputs

- `docs/idare_label_semantics_redesigned_task_smoke_tests_report.md`
- `docs/idare_label_semantics_redesigned_task_smoke_tests_report.json`
- `docs/idare_label_semantics_task_redesign_future_run_matrix.csv`
- `docs/idare_label_semantics_redesigned_task_future_matrix_manual_audit.csv`
- `docs/idare_label_semantics_redesigned_task_smoke_guard_patch_requirements.csv`

## Expected Outputs

- `docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.md`
- `docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.json`
- `docs/idare_label_semantics_redesigned_task_smoke_guard_audit.csv`
- Updated `docs/idare_label_semantics_redesigned_task_smoke_tests_report.md`
- Updated `docs/idare_label_semantics_redesigned_task_smoke_tests_report.json`

## Pass Criteria

- Future matrix guard passes for the current mean/ridge-only matrix.
- Actual forbidden model rows would still fail the guard.
- All other smoke tests are rerun and reported.
- Training remains blocked unless patched smoke report passes and is reviewed.
- direct full SupCon/DG training remains blocked.
- broad hyperparameter search remains blocked.
- final LOSO claim remains blocked.

## Next Allowed Step

Prepare a reviewed redesigned-task smoke-guard patch command/script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- minimal regression training before patched smoke-test review
"""
objective_md_path.write_text(objective_md, encoding="utf-8")

status = json.loads(status_json_path.read_text(encoding="utf-8"))
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "prepare_reviewed_label_semantics_redesigned_task_smoke_guard_patch_command"
status["current_idare_blocked_steps"] = blocked
events = status.get("idare_protocol_events")
if not isinstance(events, list):
    events = []
status["idare_protocol_events"] = events
events.extend([
    {
        "timestamp_utc": now,
        "type": "manual_review",
        "name": "I-DARE redesigned-task spec-fix-or-stop manual review",
        "status": f"prior stop/archive superseded; diagnosis={new_diagnosis}",
        "evidence": str(manual_review_md_path),
        "next_allowed_step": "create/use narrow smoke-guard patch objective",
        "blocked": blocked,
    },
    {
        "timestamp_utc": now,
        "type": "objective",
        "name": "I-DARE redesigned-task smoke-guard patch objective",
        "status": "objective created; narrow guard patch only; no training authorized",
        "evidence": str(objective_md_path),
        "next_allowed_step": "prepare reviewed smoke-guard patch command",
        "blocked": blocked,
    },
])
status_json_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Redesigned-Task Smoke-Guard Patch Objective

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE redesigned-task spec-fix-or-stop manual review | prior stop/archive recommendation superseded for this smoke-guard failure; diagnosis=`{new_diagnosis}` | `docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_manual_review_status.md` | Create/use narrow smoke-guard patch objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE redesigned-task smoke-guard patch objective | narrow patch objective created; no training authorized | `docs/idare_label_semantics_redesigned_task_smoke_guard_patch_objective.md` | Prepare reviewed smoke-guard patch command/script. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Manual future-matrix audit found zero actual forbidden model rows.
- Training remains blocked until patched smoke tests pass and are reviewed.
"""
if "I-DARE Redesigned-Task Smoke-Guard Patch Objective" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_SMOKE_GUARD_PATCH_OBJECTIVE_WRITTEN")
print(manual_review_md_path)
print(manual_review_json_path)
print(objective_md_path)
print(objective_json_path)
print(manual_audit_csv_path)
print(patch_requirements_csv_path)
print("manual_audit_diagnosis=", new_diagnosis)
print("actual_forbidden_model_rows=", int(actual_forbidden_model_mask.sum()))
print("unique_model_values=", ",".join(allowed_models))
print("next_allowed_step=prepare_reviewed_label_semantics_redesigned_task_smoke_guard_patch_command")
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_paths = [
    Path("docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_manual_review_status.json"),
    Path("docs/idare_label_semantics_redesigned_task_smoke_guard_patch_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

manual = pd.read_csv("docs/idare_label_semantics_redesigned_task_future_matrix_manual_audit.csv")
requirements = pd.read_csv("docs/idare_label_semantics_redesigned_task_smoke_guard_patch_requirements.csv")
print("manual_audit_rows=", len(manual))
print("patch_requirements_rows=", len(requirements))
if not manual["passed"].astype(bool).all():
    raise SystemExit("ERROR: manual audit contains failed checks")
if len(requirements) < 5:
    raise SystemExit("ERROR: patch requirements too short")

term_checks = {
    "docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_manual_review_status.md": [
        "supersedes",
        "zero actual SupCon/DG/VREx/fusion/contrastive model rows",
        "ridge_regression_summary_features",
        "direct full SupCon/DG training",
        "final LOSO claim",
    ],
    "docs/idare_label_semantics_redesigned_task_smoke_guard_patch_objective.md": [
        "Scientific Question",
        "Manual Audit Diagnosis",
        "Authorized Work",
        "Expected Outputs",
        "future_run_matrix_guard",
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

obj = json.loads(Path("docs/idare_label_semantics_redesigned_task_smoke_guard_patch_objective.json").read_text(encoding="utf-8"))
if obj.get("next_allowed_step") != "prepare_reviewed_label_semantics_redesigned_task_smoke_guard_patch_command":
    raise SystemExit("ERROR: wrong next_allowed_step")
if "direct full SupCon/DG training" not in obj.get("blocked", []):
    raise SystemExit("ERROR: missing blocked direct full SupCon/DG training")

print("manual_audit_diagnosis=", obj.get("manual_audit_diagnosis"))
print("next_allowed_step=", obj.get("next_allowed_step"))
print("ALL_SMOKE_GUARD_PATCH_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "Status|Scientific Question|Manual Audit Diagnosis|Evidence Summary|Authorized Work|Expected Outputs|Pass Criteria|Next Allowed Step" \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_objective.md
grep -nE "Smoke-Guard Patch Objective|Manual future-matrix audit|Training remains blocked" docs/project_status_current.md | tail -n 10
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_manual_review_status.md \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_manual_review_status.json \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_objective.md \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_objective.json \
  docs/idare_label_semantics_redesigned_task_future_matrix_manual_audit.csv \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_requirements.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE redesigned task smoke guard patch objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
