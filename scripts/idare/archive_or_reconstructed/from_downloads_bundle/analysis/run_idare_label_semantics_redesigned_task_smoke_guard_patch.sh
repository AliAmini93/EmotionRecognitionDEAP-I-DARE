#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_redesigned_task_smoke_guard_patch_run.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start redesigned-task smoke-guard patch + smoke rerun ====="
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
    import re
    from pathlib import Path
    import pandas as pd
except Exception as e:
    raise SystemExit(f"ERROR_IMPORTS: {e}")
print("OK_IMPORTS")
PY

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: repo is not clean; commit/stash before running guard patch." >&2
  git status --short
  exit 2
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required inputs ====="
required=(
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_objective.md
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_objective.json
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_manual_review_status.md
  docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_manual_review_status.json
  docs/idare_label_semantics_redesigned_task_future_matrix_manual_audit.csv
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_requirements.csv
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.md
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.json
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

echo "===== 3) remove stale patch outputs ====="
rm -f \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.md \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.json \
  docs/idare_label_semantics_redesigned_task_smoke_guard_audit.csv \
  docs/idare_label_semantics_redesigned_task_patched_smoke_decision_matrix.csv
echo "OK_CLEAN_PATCH_OUTPUTS"
echo

echo "===== 4) apply patched future-run guard and regenerate smoke-test report ====="
"$PY" - <<'PY'
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

objective_json_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_patch_objective.json"
manual_review_json_path = DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_manual_review_status.json"
future_matrix_path = DOCS / "idare_label_semantics_task_redesign_future_run_matrix.csv"
manual_audit_path = DOCS / "idare_label_semantics_redesigned_task_future_matrix_manual_audit.csv"
requirements_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_patch_requirements.csv"

smoke_report_json_path = DOCS / "idare_label_semantics_redesigned_task_smoke_tests_report.json"
smoke_report_md_path = DOCS / "idare_label_semantics_redesigned_task_smoke_tests_report.md"
smoke_decision_path = DOCS / "idare_label_semantics_redesigned_task_smoke_decision_matrix.csv"
target_audit_path = DOCS / "idare_label_semantics_redesigned_task_target_audit.csv"
fold_audit_path = DOCS / "idare_label_semantics_redesigned_task_fold_audit.csv"
metric_sanity_path = DOCS / "idare_label_semantics_redesigned_task_metric_sanity.csv"
baseline_path = DOCS / "idare_label_semantics_redesigned_task_baseline_control_summary.csv"

patch_report_md_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_patch_report.md"
patch_report_json_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_patch_report.json"
guard_audit_path = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_audit.csv"
patched_decision_path = DOCS / "idare_label_semantics_redesigned_task_patched_smoke_decision_matrix.csv"

status_json_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def truthy(x):
    if isinstance(x, bool):
        return x
    if pd.isna(x):
        return False
    return str(x).strip().lower() in {"true", "1", "yes", "y", "pass", "passed"}

def md_table(rows, columns):
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        vals = [str(row.get(c, "")).replace("\n", " ").replace("|", "\\|") for c in columns]
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)

objective = read_json(objective_json_path)
manual_review = read_json(manual_review_json_path)
old_report = read_json(smoke_report_json_path)
future = pd.read_csv(future_matrix_path)
manual_audit = pd.read_csv(manual_audit_path)
requirements = pd.read_csv(requirements_path)
decision = pd.read_csv(smoke_decision_path)
target_audit = pd.read_csv(target_audit_path)
fold_audit = pd.read_csv(fold_audit_path)
metric_sanity = pd.read_csv(metric_sanity_path)
baseline = pd.read_csv(baseline_path)

selected = old_report.get("selected_primary_formulation", objective.get("selected_primary_formulation", "subject_relative_ordinal_affect_regression_v1"))

# Patch rule:
# - scan only explicit model/method columns for forbidden model families;
# - do not scan notes;
# - use token-aware patterns so "ridge" does not trip "dg".
method_cols = [c for c in ["model", "method", "method_family", "algorithm", "candidate_id"] if c in future.columns]
if not method_cols:
    raise SystemExit("ERROR: future matrix has no explicit model/method columns")

explicit_method_text = future[method_cols].astype(str).agg(" ".join, axis=1).str.lower()
normalized = explicit_method_text.map(lambda s: re.sub(r"[^a-z0-9]+", " ", s).strip())
token_sets = normalized.map(lambda s: set(s.split()))

def has_forbidden(text, tokens):
    # Forbidden explicit rows, not free-text guardrail notes.
    if "supcon" in tokens or "contrastive" in tokens:
        return True
    if "vrex" in tokens:
        return True
    if "fusion" in tokens:
        return True
    if "dg" in tokens:
        return True
    if "domain" in tokens and "generalization" in tokens:
        return True
    if "domain_generalization" in text or "domain-generalization" in text or "domain generalization" in text:
        return True
    if "supervised_contrastive" in text or "supervised-contrastive" in text:
        return True
    return False

forbidden_mask = [has_forbidden(t, toks) for t, toks in zip(explicit_method_text.tolist(), token_sets.tolist())]
future["patched_forbidden_model_row"] = forbidden_mask

authorized_now_all_no = True
if "authorized_now" in future.columns:
    authorized_now_all_no = future["authorized_now"].astype(str).str.lower().eq("no").all()

allowed_model_values = sorted(future["model"].astype(str).unique().tolist()) if "model" in future.columns else []
notes_negative_mentions = 0
notes_mentions_supcon_dg = 0
if "notes" in future.columns:
    notes = future["notes"].astype(str)
    notes_mentions_supcon_dg = int((notes.str.contains("SupCon", case=False, regex=False) | notes.str.contains("DG", case=False, regex=False)).sum())
    notes_negative_mentions = int((notes.str.contains("no SupCon/DG", case=False, regex=False) | notes.str.contains("no contrastive", case=False, regex=False)).sum())

guard_rows = [
    {
        "check": "explicit_method_columns_present",
        "value": ",".join(method_cols),
        "passed": True,
        "details": "Patched guard scans only explicit model/method columns.",
    },
    {
        "check": "future_rows",
        "value": int(len(future)),
        "passed": int(len(future)) == 48,
        "details": "Expected future matrix size is 48.",
    },
    {
        "check": "authorized_now_all_no",
        "value": bool(authorized_now_all_no),
        "passed": bool(authorized_now_all_no),
        "details": "Future matrix must not authorize immediate training.",
    },
    {
        "check": "forbidden_explicit_model_rows",
        "value": int(sum(forbidden_mask)),
        "passed": int(sum(forbidden_mask)) == 0,
        "details": "Explicit model/method columns must not contain SupCon, VREx, DG, domain-generalization, fusion, or contrastive rows.",
    },
    {
        "check": "notes_mentions_supcon_dg_ignored",
        "value": notes_mentions_supcon_dg,
        "passed": True,
        "details": "Notes are explanatory metadata; negated guardrail text is not an authorized method.",
    },
    {
        "check": "notes_negative_guardrail_mentions",
        "value": notes_negative_mentions,
        "passed": notes_negative_mentions >= 1,
        "details": "SupCon/DG appears only as negative guardrail prose in current matrix.",
    },
    {
        "check": "ridge_not_dg",
        "value": int(future["model"].astype(str).str.contains("ridge", case=False, regex=False).sum()) if "model" in future.columns else 0,
        "passed": not any("dg" in toks for toks in token_sets.tolist()),
        "details": "Token-aware DG check must not match letters inside ridge.",
    },
]
guard_audit = pd.DataFrame(guard_rows)
guard_audit.to_csv(guard_audit_path, index=False)

future_guard_passed = bool(guard_audit["passed"].astype(bool).all())

# Patch the decision matrix: only future_run_matrix_guard changes based on patched logic.
decision_patched = decision.copy()
if "smoke_test" not in decision_patched.columns:
    raise SystemExit("ERROR: smoke decision matrix missing smoke_test column")
if "passed" not in decision_patched.columns:
    raise SystemExit("ERROR: smoke decision matrix missing passed column")

mask = decision_patched["smoke_test"].astype(str).eq("future_run_matrix_guard")
if not mask.any():
    # Add the row if absent, but keep a conservative audit trail.
    decision_patched = pd.concat([
        decision_patched,
        pd.DataFrame([{
            "smoke_test": "future_run_matrix_guard",
            "passed": future_guard_passed,
            "evidence": "patched guard generated this row",
        }])
    ], ignore_index=True)
else:
    decision_patched.loc[mask, "passed"] = future_guard_passed
    if "evidence" in decision_patched.columns:
        decision_patched.loc[mask, "evidence"] = (
            "patched token-aware guard; explicit model/method columns only; notes ignored as metadata"
        )
    if "details" in decision_patched.columns:
        decision_patched.loc[mask, "details"] = (
            "actual_forbidden_model_rows=0; ridge baseline allowed; notes-only no SupCon/DG ignored"
        )

decision_patched["_passed_bool"] = decision_patched["passed"].map(truthy)
all_passed = bool(decision_patched["_passed_bool"].all())
failed_smokes = decision_patched.loc[~decision_patched["_passed_bool"], "smoke_test"].astype(str).tolist()
decision_patched.drop(columns=["_passed_bool"], errors="ignore").to_csv(patched_decision_path, index=False)
# Update canonical smoke decision matrix too: original is preserved by git history.
decision_patched.drop(columns=["_passed_bool"], errors="ignore").to_csv(smoke_decision_path, index=False)

if all_passed:
    diagnosis = "redesigned_task_smoke_tests_passed_after_guard_patch"
    recommended_next_objective = "label_semantics_minimal_redesigned_task_first_pass_training_objective"
    next_allowed_step = "human_review_closeout_then_create_minimal_redesigned_task_first_pass_objective"
else:
    diagnosis = "redesigned_task_smoke_tests_still_failed_after_guard_patch"
    recommended_next_objective = "label_semantics_redesigned_task_smoke_patch_failure_analysis_objective"
    next_allowed_step = "human_review_closeout_then_failure_analysis"

blocked = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change",
]
if not all_passed:
    blocked.append("minimal regression training until smoke failures are fixed and reviewed")
else:
    blocked.append("minimal regression training until patched smoke-test report is reviewed")

patch_report = {
    "status": "complete_pending_human_review",
    "created_utc": now,
    "source_objective": str(objective_json_path),
    "source_manual_review": str(DOCS / "idare_label_semantics_redesigned_task_spec_fix_or_stop_manual_review_status.md"),
    "selected_primary_formulation": selected,
    "patched_guard": {
        "method_columns_scanned": method_cols,
        "notes_scanned_for_forbidden_methods": False,
        "token_aware_dg": True,
        "actual_forbidden_model_rows": int(sum(forbidden_mask)),
        "future_guard_passed": future_guard_passed,
        "allowed_model_values": allowed_model_values,
    },
    "all_passed": all_passed,
    "failed_smoke_tests": failed_smokes,
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next_objective,
    "next_allowed_step": next_allowed_step,
    "training_authorized": False,
    "blocked": blocked,
    "outputs": {
        "patch_report_md": str(patch_report_md_path),
        "patch_report_json": str(patch_report_json_path),
        "guard_audit_csv": str(guard_audit_path),
        "patched_smoke_decision_matrix_csv": str(patched_decision_path),
        "updated_smoke_report_md": str(smoke_report_md_path),
        "updated_smoke_report_json": str(smoke_report_json_path),
    },
}
patch_report_json_path.write_text(json.dumps(patch_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Update canonical smoke report JSON with patched result.
updated_smoke_report = old_report.copy()
updated_smoke_report.update({
    "status": "complete_pending_human_review",
    "patched_utc": now,
    "patch_source_objective": str(objective_json_path),
    "patch_report": str(patch_report_json_path),
    "selected_primary_formulation": selected,
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next_objective,
    "all_passed": all_passed,
    "failed_smoke_tests": failed_smokes,
    "future_run_matrix_guard_patch": patch_report["patched_guard"],
    "training_authorized": False,
})
smoke_report_json_path.write_text(json.dumps(updated_smoke_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

patch_report_rows = [
    {"item": "selected_primary_formulation", "value": selected},
    {"item": "future_guard_passed", "value": future_guard_passed},
    {"item": "actual_forbidden_model_rows", "value": int(sum(forbidden_mask))},
    {"item": "all_passed", "value": all_passed},
    {"item": "diagnosis", "value": diagnosis},
    {"item": "recommended_next_objective", "value": recommended_next_objective},
]

md = []
md.append("# I-DARE Label-Semantics Redesigned-Task Smoke-Guard Patch Report\n")
md.append("## Status\n")
md.append("Status: complete; pending human review.\n")
md.append(f"Created UTC: `{now}`\n")
md.append("## Executive Result\n")
md.append(md_table(patch_report_rows, ["item", "value"]))
md.append("\n## Patched Guard Logic\n")
md.append("- Scan explicit `model` / `method` columns only.\n")
md.append("- Do not scan `notes` as authorized-method declarations.\n")
md.append("- Use token-aware DG matching, so `ridge` is not interpreted as `DG`.\n")
md.append("- Keep actual SupCon, VREx, DG/domain-generalization, fusion, or contrastive model rows blocked.\n")
md.append("\n## Guard Audit\n")
md.append(md_table(guard_rows, ["check", "value", "passed", "details"]))
md.append("\n## Smoke-Test Decision Matrix\n")
decision_rows = decision_patched.drop(columns=["_passed_bool"], errors="ignore").to_dict("records")
decision_cols = list(decision_patched.drop(columns=["_passed_bool"], errors="ignore").columns)
md.append(md_table(decision_rows, decision_cols))
md.append("\n## Interpretation\n")
if all_passed:
    md.append(
        "The previous smoke failure is corrected by a narrow guard patch. The future run matrix contains no actual forbidden model rows; "
        "the previous failure came from over-broad scanning of explanatory notes and/or non-token-aware matching. Training is still not authorized "
        "until this patched smoke report is reviewed and a separate minimal first-pass objective is created.\n"
    )
else:
    md.append(
        "The guard patch did not clear all smoke tests. No training is authorized; the next step must analyze the remaining failures.\n"
    )
md.append("## Next Allowed Step\n")
md.append(f"`{next_allowed_step}`\n")
md.append("\nBlocked:\n")
for b in blocked:
    md.append(f"- {b}\n")
patch_report_md_path.write_text("\n".join(md), encoding="utf-8")

# Update canonical smoke tests report MD.
smoke_md = []
smoke_md.append("# I-DARE Label-Semantics Redesigned-Task Smoke Tests Report\n")
smoke_md.append("## Status\n")
smoke_md.append("Status: complete; patched guard result pending human review.\n")
smoke_md.append(f"Patched UTC: `{now}`\n")
smoke_md.append("## Executive Result\n")
smoke_md.append(f"- Selected formulation: `{selected}`\n")
smoke_md.append(f"- Diagnosis: `{diagnosis}`\n")
smoke_md.append(f"- all_passed: `{all_passed}`\n")
smoke_md.append(f"- recommended_next_objective: `{recommended_next_objective}`\n")
smoke_md.append("## Patched Future-Run Matrix Guard\n")
smoke_md.append(f"- Actual forbidden model rows: `{int(sum(forbidden_mask))}`\n")
smoke_md.append(f"- Future guard passed: `{future_guard_passed}`\n")
smoke_md.append("- Notes were not treated as authorized method declarations.\n")
smoke_md.append("- Token-aware DG check prevented `ridge` from being treated as `DG`.\n")
smoke_md.append("## Smoke-Test Decision Matrix\n")
smoke_md.append(md_table(decision_rows, decision_cols))
smoke_md.append("\n## Next Allowed Step\n")
smoke_md.append(f"`{next_allowed_step}`\n")
smoke_md.append("\nTraining remains blocked until human review/closeout.\n")
smoke_report_md_path.write_text("\n".join(smoke_md), encoding="utf-8")

# Update roadmap.
status = read_json(status_json_path)
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = next_allowed_step
status["current_idare_blocked_steps"] = blocked
events = status.get("idare_protocol_events")
if not isinstance(events, list):
    events = []
status["idare_protocol_events"] = events
events.append({
    "timestamp_utc": now,
    "type": "patch_report",
    "name": "I-DARE label-semantics redesigned-task smoke-guard patch",
    "status": f"complete pending human review; diagnosis={diagnosis}; all_passed={all_passed}",
    "evidence": str(patch_report_md_path),
    "next_allowed_step": next_allowed_step,
    "blocked": blocked,
})
status_json_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Label-Semantics Redesigned-Task Smoke-Guard Patch Report

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE redesigned-task smoke-guard patch report | complete pending human review; diagnosis=`{diagnosis}`; all_passed=`{all_passed}` | `docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.md` | `{next_allowed_step}` | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Actual forbidden future model rows: `{int(sum(forbidden_mask))}`.
- Training remains blocked until patched smoke-test review.
"""
if "I-DARE Label-Semantics Redesigned-Task Smoke-Guard Patch Report" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_SMOKE_GUARD_PATCH_REPORT_WRITTEN")
print(patch_report_md_path)
print(patch_report_json_path)
print(guard_audit_path)
print(patched_decision_path)
print("diagnosis=", diagnosis)
print("all_passed=", all_passed)
print("future_guard_passed=", future_guard_passed)
print("actual_forbidden_model_rows=", int(sum(forbidden_mask)))
print("recommended_next_objective=", recommended_next_objective)
print("next_allowed_step=", next_allowed_step)
PY
echo

echo "===== 5) validate patched outputs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_paths = [
    Path("docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.json"),
    Path("docs/idare_label_semantics_redesigned_task_smoke_tests_report.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

audit = pd.read_csv("docs/idare_label_semantics_redesigned_task_smoke_guard_audit.csv")
patched_decision = pd.read_csv("docs/idare_label_semantics_redesigned_task_patched_smoke_decision_matrix.csv")
canonical_decision = pd.read_csv("docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv")
print("guard_audit_rows=", len(audit))
print("patched_decision_rows=", len(patched_decision))
print("canonical_decision_rows=", len(canonical_decision))

if not audit["passed"].astype(bool).all():
    raise SystemExit("ERROR: guard audit did not pass")

report = json.loads(Path("docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.json").read_text(encoding="utf-8"))
if report["patched_guard"]["actual_forbidden_model_rows"] != 0:
    raise SystemExit("ERROR: actual forbidden model rows != 0")
if not report["patched_guard"]["future_guard_passed"]:
    raise SystemExit("ERROR: patched future guard did not pass")
if report["diagnosis"] not in {
    "redesigned_task_smoke_tests_passed_after_guard_patch",
    "redesigned_task_smoke_tests_still_failed_after_guard_patch",
}:
    raise SystemExit("ERROR: unexpected diagnosis")
for term in ["direct full SupCon/DG training", "broad hyperparameter search", "final LOSO claim"]:
    if term not in report.get("blocked", []):
        raise SystemExit(f"ERROR: missing blocked term {term}")

text = Path("docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.md").read_text(encoding="utf-8")
for term in ["Executive Result", "Patched Guard Logic", "Guard Audit", "Smoke-Test Decision Matrix", "Next Allowed Step"]:
    if term not in text:
        raise SystemExit(f"ERROR: missing report section {term}")

print("diagnosis=", report["diagnosis"])
print("all_passed=", report["all_passed"])
print("future_guard_passed=", report["patched_guard"]["future_guard_passed"])
print("actual_forbidden_model_rows=", report["patched_guard"]["actual_forbidden_model_rows"])
print("recommended_next_objective=", report["recommended_next_objective"])
print("next_allowed_step=", report["next_allowed_step"])
print("ALL_SMOKE_GUARD_PATCH_OUTPUTS_VALID")
PY

grep -nE "Status|Executive Result|Patched Guard Logic|Guard Audit|Smoke-Test Decision Matrix|Interpretation|Next Allowed Step" \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.md
grep -nE "Smoke-Guard Patch Report|Actual forbidden future model rows|Training remains blocked" docs/project_status_current.md | tail -n 10
echo

echo "===== 6) file list ====="
ls -lh \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.md \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.json \
  docs/idare_label_semantics_redesigned_task_smoke_guard_audit.csv \
  docs/idare_label_semantics_redesigned_task_patched_smoke_decision_matrix.csv \
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.md \
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.json \
  docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv \
  docs/project_status_current.json \
  docs/project_status_current.md
echo

echo "===== 7) status before commit ====="
git status --short --branch
echo

echo "===== 8) commit and push smoke-guard patch report ====="
git add \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.md \
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.json \
  docs/idare_label_semantics_redesigned_task_smoke_guard_audit.csv \
  docs/idare_label_semantics_redesigned_task_patched_smoke_decision_matrix.csv \
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.md \
  docs/idare_label_semantics_redesigned_task_smoke_tests_report.json \
  docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "analysis: patch I-DARE redesigned task smoke guard"
git push origin main
echo

echo "===== 9) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
