#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start redesigned-task spec-fix-or-stop report ====="
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
  echo "ERROR: repo is not clean; commit/stash before generating report." >&2
  git status --short
  exit 2
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required committed inputs ====="
required=(
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.md
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.json
  docs/idare_label_semantics_redesigned_task_smoke_tests_review_status.md
  docs/idare_label_semantics_redesigned_task_smoke_tests_review_status.json
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.md
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.json
  docs/idare_label_semantics_redesigned_task_failed_smoke_summary.csv
  docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv
  docs/idare_label_semantics_redesigned_task_target_audit.csv
  docs/idare_label_semantics_redesigned_task_fold_audit.csv
  docs/idare_label_semantics_redesigned_task_metric_sanity.csv
  docs/idare_label_semantics_redesigned_task_baseline_control_summary.csv
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

echo "===== 3) remove stale target outputs ====="
rm -f \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.json \
  docs/idare_label_semantics_redesigned_task_failed_smoke_diagnosis.csv \
  docs/idare_label_semantics_redesigned_task_fix_or_stop_decision_matrix.csv \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_plan.csv
echo "OK_CLEAN_TARGET_OUTPUTS"
echo

echo "===== 4) generate read-only spec-fix-or-stop report ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

objective_json_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_objective.json"
smoke_report_json_path = DOCS / "idare_label_semantics_redesigned_task_smoke_tests_report.json"
failed_summary_path = DOCS / "idare_label_semantics_redesigned_task_failed_smoke_summary.csv"
smoke_decision_path = DOCS / "idare_label_semantics_redesigned_task_smoke_decision_matrix.csv"
future_matrix_path = DOCS / "idare_label_semantics_task_redesign_future_run_matrix.csv"
target_audit_path = DOCS / "idare_label_semantics_redesigned_task_target_audit.csv"
fold_audit_path = DOCS / "idare_label_semantics_redesigned_task_fold_audit.csv"
metric_sanity_path = DOCS / "idare_label_semantics_redesigned_task_metric_sanity.csv"
baseline_path = DOCS / "idare_label_semantics_redesigned_task_baseline_control_summary.csv"

report_md_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md"
report_json_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_report.json"
failed_diag_path = DOCS / "idare_label_semantics_redesigned_task_failed_smoke_diagnosis.csv"
decision_matrix_path = DOCS / "idare_label_semantics_redesigned_task_fix_or_stop_decision_matrix.csv"
patch_plan_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_patch_plan.csv"
status_json_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))

def md_table(rows, columns):
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        vals = []
        for c in columns:
            vals.append(str(row.get(c, "")).replace("\n", " ").replace("|", "\\|"))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)

objective = load_json(objective_json_path)
smoke_report = load_json(smoke_report_json_path)
failed = pd.read_csv(failed_summary_path)
smoke_decision = pd.read_csv(smoke_decision_path)
future = pd.read_csv(future_matrix_path)
target_audit = pd.read_csv(target_audit_path)
fold_audit = pd.read_csv(fold_audit_path)
metric_sanity = pd.read_csv(metric_sanity_path)
baseline = pd.read_csv(baseline_path)

selected = smoke_report.get("selected_primary_formulation", "subject_relative_ordinal_affect_regression_v1")
failed_tests = failed["smoke_test"].astype(str).tolist() if "smoke_test" in failed.columns else objective.get("failed_smoke_tests", [])
failed_tests = failed_tests or ["unknown"]

# Diagnose the specific failure. The prior smoke script rejected substring "dg" anywhere in the future matrix.
# Here we separate actual DG/SupCon/fusion tokens from innocent substrings, especially "ridge".
future_text_cols = future.astype(str)
joined_rows = future_text_cols.agg(" ".join, axis=1).str.lower()
contains_supcon = joined_rows.str.contains("supcon", regex=False)
contains_fusion = joined_rows.str.contains("fusion", regex=False)
# Token-aware DG check: only real DG markers, not substring in "ridge".
real_dg_patterns = [
    " ce_plus_vrex ",
    " vrex ",
    " domain_generalization ",
    " domain generalization ",
    " dg ",
    " d_g ",
]
padded = " " + joined_rows + " "
contains_real_dg = pd.Series(False, index=future.index)
for pat in real_dg_patterns:
    contains_real_dg = contains_real_dg | padded.str.contains(pat, regex=False)
contains_ridge = joined_rows.str.contains("ridge", regex=False)
authorized_now_ok = True
if "authorized_now" in future.columns:
    authorized_now_ok = future["authorized_now"].astype(str).str.lower().eq("no").all()

has_actual_forbidden_future_rows = bool((contains_supcon | contains_fusion | contains_real_dg).any())
ridge_false_positive_present = bool(contains_ridge.any())
future_rows_ok = int(len(future)) == 48
future_guard_is_false_positive = (
    failed_tests == ["future_run_matrix_guard"]
    and future_rows_ok
    and authorized_now_ok
    and ridge_false_positive_present
    and not has_actual_forbidden_future_rows
)

all_other_smokes_passed = True
if "passed" in smoke_decision.columns:
    tmp = smoke_decision.copy()
    tmp["_passed_bool"] = tmp["passed"].map(lambda x: str(x).strip().lower() in {"true", "1", "yes", "y"})
    other = tmp.loc[tmp["smoke_test"].astype(str) != "future_run_matrix_guard"]
    all_other_smokes_passed = bool(other["_passed_bool"].all())

target_ok = bool(target_audit.get("target_construction_passed", pd.Series([False])).astype(bool).all())
fold_ok = bool(fold_audit.get("fold_leakage_passed", pd.Series([False])).astype(bool).all())
dist_ok = bool(fold_audit.get("target_distribution_passed", pd.Series([False])).astype(bool).all())
metric_ok = bool(metric_sanity.get("passed", pd.Series([False])).astype(bool).all())
baseline_ok = bool(baseline.get("finite_metrics_passed", pd.Series([False])).astype(bool).all())

if future_guard_is_false_positive and all_other_smokes_passed and target_ok and fold_ok and dist_ok and metric_ok and baseline_ok:
    diagnosis = "future_run_matrix_guard_false_positive_due_to_ridge_substring"
    recommendation = "narrow_fix_objective"
    recommended_next_objective = "label_semantics_redesigned_task_smoke_guard_patch_objective"
    decision = "patch_future_run_matrix_guard_and_rerun_smokes"
    stop_archive = False
else:
    diagnosis = "redesigned_task_smoke_failure_not_yet_fixable"
    recommendation = "stop_archive_objective"
    recommended_next_objective = "label_semantics_redesigned_task_stop_archive_objective"
    decision = "stop_or_archive_redesigned_branch_pending_manual_review"
    stop_archive = True

failed_diag_rows = []
for test in failed_tests:
    if test == "future_run_matrix_guard" and future_guard_is_false_positive:
        failed_diag_rows.append({
            "smoke_test": test,
            "failure_classification": "implementation_bug",
            "root_cause": "substring guard searched for 'dg' anywhere in future matrix text and matched the letters inside 'ridge_regression_summary_features'",
            "actual_spec_problem": "no",
            "actual_forbidden_future_rows": has_actual_forbidden_future_rows,
            "evidence": f"future_rows={len(future)}; authorized_now_ok={authorized_now_ok}; contains_ridge={ridge_false_positive_present}; contains_real_dg={bool(contains_real_dg.any())}; contains_supcon={bool(contains_supcon.any())}; contains_fusion={bool(contains_fusion.any())}",
            "recommended_action": "patch guard to use token-aware DG detection or explicit forbidden method families, then rerun smoke tests",
        })
    else:
        failed_diag_rows.append({
            "smoke_test": test,
            "failure_classification": "unresolved_or_stop_trigger",
            "root_cause": "not proven to be a narrow implementation false positive",
            "actual_spec_problem": "unknown",
            "actual_forbidden_future_rows": has_actual_forbidden_future_rows,
            "evidence": "requires manual review",
            "recommended_action": "stop/archive or create a more focused manual audit objective",
        })
failed_diag = pd.DataFrame(failed_diag_rows)
failed_diag.to_csv(failed_diag_path, index=False)

decision_rows = [
    {
        "decision_option": "narrow_fix_objective",
        "selected": recommendation == "narrow_fix_objective",
        "rationale": "Only failed smoke is future_run_matrix_guard, and it is explained by a tokenization bug: 'dg' matched inside 'ridge'.",
        "next_step": "Create patch objective that fixes only the guard and reruns smoke tests.",
        "training_authorized": "no",
    },
    {
        "decision_option": "stop_archive_objective",
        "selected": recommendation == "stop_archive_objective",
        "rationale": "Use only if failure is a true spec/data degeneracy rather than a guard implementation bug.",
        "next_step": "Archive redesigned task branch.",
        "training_authorized": "no",
    },
    {
        "decision_option": "minimal_regression_training",
        "selected": False,
        "rationale": "Not allowed until patched smoke tests pass and are reviewed.",
        "next_step": "blocked",
        "training_authorized": "no",
    },
    {
        "decision_option": "direct_full_supcon_dg_training",
        "selected": False,
        "rationale": "Still blocked by the project guardrails and unrelated to this smoke failure.",
        "next_step": "blocked",
        "training_authorized": "no",
    },
]
pd.DataFrame(decision_rows).to_csv(decision_matrix_path, index=False)

patch_rows = [
    {
        "patch_item": "replace_substring_dg_check",
        "current_behavior": "checks whether 'dg' appears anywhere in future matrix text",
        "patched_behavior": "check explicit forbidden method names/tokens only, e.g. SupCon, VREx, domain_generalization, fusion",
        "why": "prevents false positive on ridge_regression_summary_features",
        "training_authorized": "no",
    },
    {
        "patch_item": "rerun_same_smokes",
        "current_behavior": "smoke test report is failed",
        "patched_behavior": "rerun all six smoke tests after guard patch",
        "why": "confirm no other hidden failure emerges",
        "training_authorized": "no",
    },
    {
        "patch_item": "preserve_future_matrix",
        "current_behavior": "48-row matrix contains mean baseline and ridge regression only",
        "patched_behavior": "do not change future matrix unless explicit forbidden row is found",
        "why": "the future matrix itself appears consistent with the spec",
        "training_authorized": "no",
    },
]
pd.DataFrame(patch_rows).to_csv(patch_plan_path, index=False)

report = {
    "status": "complete_pending_human_review",
    "created_utc": now,
    "source_objective": str(objective_json_path).replace("\\", "/"),
    "source_smoke_report": str(smoke_report_json_path).replace("\\", "/"),
    "selected_primary_formulation": selected,
    "diagnosis": diagnosis,
    "decision": decision,
    "recommendation": recommendation,
    "recommended_next_objective": recommended_next_objective,
    "failed_smoke_tests": failed_tests,
    "future_run_matrix_guard": {
        "future_rows": int(len(future)),
        "authorized_now_ok": bool(authorized_now_ok),
        "contains_ridge": ridge_false_positive_present,
        "contains_supcon": bool(contains_supcon.any()),
        "contains_fusion": bool(contains_fusion.any()),
        "contains_real_dg": bool(contains_real_dg.any()),
        "has_actual_forbidden_future_rows": has_actual_forbidden_future_rows,
        "future_guard_is_false_positive": future_guard_is_false_positive,
    },
    "other_smoke_status": {
        "all_other_smokes_passed": all_other_smokes_passed,
        "target_ok": target_ok,
        "fold_leakage_ok": fold_ok,
        "target_distribution_ok": dist_ok,
        "metric_sanity_ok": metric_ok,
        "baseline_controls_ok": baseline_ok,
    },
    "stop_archive_selected": stop_archive,
    "training_authorized": False,
    "next_allowed_step": "human_review_closeout_then_smoke_guard_patch_objective" if recommendation == "narrow_fix_objective" else "human_review_closeout_then_stop_archive",
    "outputs": {
        "report_md": str(report_md_path),
        "report_json": str(report_json_path),
        "failed_smoke_diagnosis_csv": str(failed_diag_path),
        "fix_or_stop_decision_matrix_csv": str(decision_matrix_path),
        "smoke_guard_patch_plan_csv": str(patch_plan_path),
    },
    "blocked": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
        "minimal regression training before patched smoke-test review",
    ],
}
report_json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = []
md.append("# I-DARE Label-Semantics Redesigned-Task Spec-Fix-or-Stop Report\n")
md.append("## Status\n")
md.append("Status: complete; pending human review.\n")
md.append(f"Created UTC: `{now}`\n")
md.append("## Executive Decision\n")
md.append(f"Selected formulation: `{selected}`\n")
md.append(f"Diagnosis: `{diagnosis}`\n")
md.append(f"Decision: `{decision}`\n")
md.append(f"Recommendation: `{recommendation}`\n")
md.append(f"Recommended next objective: `{recommended_next_objective}`\n")
md.append("## Failed Smoke Diagnosis\n")
md.append(md_table(failed_diag_rows, ["smoke_test", "failure_classification", "root_cause", "actual_spec_problem", "evidence", "recommended_action"]))
md.append("\n## Future Run Matrix Guard Audit\n")
guard_rows = [
    {"check": "future_rows", "value": int(len(future)), "expected": 48, "passed": future_rows_ok},
    {"check": "authorized_now_all_no", "value": authorized_now_ok, "expected": True, "passed": authorized_now_ok},
    {"check": "contains_ridge", "value": ridge_false_positive_present, "expected": "allowed", "passed": True},
    {"check": "contains_supcon", "value": bool(contains_supcon.any()), "expected": False, "passed": not bool(contains_supcon.any())},
    {"check": "contains_fusion", "value": bool(contains_fusion.any()), "expected": False, "passed": not bool(contains_fusion.any())},
    {"check": "contains_real_dg_token", "value": bool(contains_real_dg.any()), "expected": False, "passed": not bool(contains_real_dg.any())},
]
md.append(md_table(guard_rows, ["check", "value", "expected", "passed"]))
md.append("\n## Fix-or-Stop Decision Matrix\n")
md.append(md_table(decision_rows, ["decision_option", "selected", "rationale", "next_step", "training_authorized"]))
md.append("\n## Patch Plan\n")
md.append(md_table(patch_rows, ["patch_item", "current_behavior", "patched_behavior", "why", "training_authorized"]))
md.append("\n## Interpretation\n")
if recommendation == "narrow_fix_objective":
    md.append(
        "The smoke failure is judged to be a narrow implementation false positive, not evidence that the redesigned task is scientifically invalid. "
        "The future matrix contains `ridge_regression_summary_features`; the old guard searched for the substring `dg`, which appears inside `ridge`. "
        "Therefore the correct next step is to patch the guard and rerun the same smoke tests, not to start training.\n"
    )
else:
    md.append(
        "The smoke failure is not safely explained as a narrow implementation issue. The redesigned branch should be stopped/archived unless human review identifies a valid narrow fix.\n"
    )
md.append("## Next Allowed Step\n")
md.append("Human review / closeout before creating the selected next objective.\n")
md.append("\nBlocked:\n")
for b in report["blocked"]:
    md.append(f"- {b}\n")
report_md_path.write_text("\n".join(md), encoding="utf-8")

# Update roadmap.
status = json.loads(status_json_path.read_text(encoding="utf-8"))
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = report["next_allowed_step"]
status["current_idare_blocked_steps"] = report["blocked"]
events = status.get("idare_protocol_events")
if not isinstance(events, list):
    events = []
status["idare_protocol_events"] = events
events.append({
    "timestamp_utc": now,
    "type": "report",
    "name": "I-DARE label-semantics redesigned-task spec-fix-or-stop report",
    "status": f"complete pending human review; diagnosis={diagnosis}; recommendation={recommendation}",
    "evidence": str(report_md_path),
    "next_allowed_step": report["next_allowed_step"],
    "blocked": report["blocked"],
})
status_json_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Label-Semantics Redesigned-Task Spec-Fix-or-Stop Report

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE label-semantics redesigned-task spec-fix-or-stop report | complete pending human review; diagnosis=`{diagnosis}`; recommendation=`{recommendation}` | `docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md` | Human review / closeout before selected next objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Recommended next objective is `{recommended_next_objective}` only after human review/closeout.
- Training remains blocked.
"""
if "I-DARE Label-Semantics Redesigned-Task Spec-Fix-or-Stop Report" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_REDESIGNED_TASK_SPEC_FIX_OR_STOP_REPORT_WRITTEN")
print(report_md_path)
print(report_json_path)
print(failed_diag_path)
print(decision_matrix_path)
print(patch_plan_path)
print("diagnosis=", diagnosis)
print("decision=", decision)
print("recommendation=", recommendation)
print("recommended_next_objective=", recommended_next_objective)
print("future_guard_is_false_positive=", future_guard_is_false_positive)
PY
echo

echo "===== 5) validate generated outputs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_paths = [
    Path("docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

csv_expect = {
    "docs/idare_label_semantics_redesigned_task_failed_smoke_diagnosis.csv": 1,
    "docs/idare_label_semantics_redesigned_task_fix_or_stop_decision_matrix.csv": 4,
    "docs/idare_label_semantics_redesigned_task_smoke_guard_patch_plan.csv": 3,
}
for p, min_rows in csv_expect.items():
    df = pd.read_csv(p)
    print(Path(p).name, "rows=", len(df))
    if len(df) < min_rows:
        raise SystemExit(f"ERROR: {p} too few rows")

report = json.loads(Path("docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.json").read_text(encoding="utf-8"))
if report.get("recommendation") not in {"narrow_fix_objective", "stop_archive_objective"}:
    raise SystemExit("ERROR: invalid recommendation")
if report.get("recommendation") == "narrow_fix_objective":
    if report.get("diagnosis") != "future_run_matrix_guard_false_positive_due_to_ridge_substring":
        raise SystemExit("ERROR: expected ridge substring false positive diagnosis")
for term in ["direct full SupCon/DG training", "broad hyperparameter search", "final LOSO claim"]:
    if term not in report.get("blocked", []):
        raise SystemExit(f"ERROR: missing blocked term {term}")

text = Path("docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md").read_text(encoding="utf-8")
for term in ["Executive Decision", "Failed Smoke Diagnosis", "Future Run Matrix Guard Audit", "Fix-or-Stop Decision Matrix", "Patch Plan"]:
    if term not in text:
        raise SystemExit(f"ERROR: missing report section {term}")

print("diagnosis=", report["diagnosis"])
print("recommendation=", report["recommendation"])
print("recommended_next_objective=", report["recommended_next_objective"])
print("future_guard_is_false_positive=", report["future_run_matrix_guard"]["future_guard_is_false_positive"])
print("ALL_REDESIGNED_TASK_SPEC_FIX_OR_STOP_REPORT_OUTPUTS_VALID")
PY

grep -nE "Status|Executive Decision|Failed Smoke Diagnosis|Future Run Matrix Guard Audit|Fix-or-Stop Decision Matrix|Patch Plan|Interpretation|Next Allowed Step" \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md
grep -nE "Spec-Fix-or-Stop Report|Recommended next objective" docs/project_status_current.md | tail -n 10
echo

echo "===== 6) file list ====="
ls -lh \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.json \
  docs/idare_label_semantics_redesigned_task_failed_smoke_diagnosis.csv \
  docs/idare_label_semantics_redesigned_task_fix_or_stop_decision_matrix.csv \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_plan.csv \
  docs/project_status_current.json \
  docs/project_status_current.md
echo

echo "===== 7) status before commit ====="
git status --short --branch
echo

echo "===== 8) commit and push spec-fix-or-stop report ====="
git add \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md \
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.json \
  docs/idare_label_semantics_redesigned_task_failed_smoke_diagnosis.csv \
  docs/idare_label_semantics_redesigned_task_fix_or_stop_decision_matrix.csv \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_plan.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "analysis: add I-DARE redesigned task fix-or-stop report"
git push origin main
echo

echo "===== 9) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
