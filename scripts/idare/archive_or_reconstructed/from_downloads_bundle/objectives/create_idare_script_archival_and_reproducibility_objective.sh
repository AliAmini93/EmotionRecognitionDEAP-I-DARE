#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_script_archival_reproducibility_objective.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start reproducibility-layer pause + script archival objective ====="
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

echo "===== 2) check current pause-point evidence ====="
required=(
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.md
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.json
  docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.md
  docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.json
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_review_status.md
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_review_status.json
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_runs.csv
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_metric_summary.csv
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

if [[ ! -d scripts ]]; then
  echo "ERROR: scripts/ directory missing; cannot define archival target." >&2
  exit 4
fi
echo "tracked_script_files=$(git ls-files scripts | wc -l)"
echo

echo "===== 3) create pause status + script archival/reproducibility objective ====="
"$PY" - <<'PY'
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

first_pass_report_json = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_report.json"
failure_obj_md = DOCS / "idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.md"
failure_obj_json = DOCS / "idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.json"
first_pass_review_md = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_review_status.md"
first_pass_review_json = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_review_status.json"

pause_md = DOCS / "idare_reproducibility_layer_pause_status.md"
pause_json = DOCS / "idare_reproducibility_layer_pause_status.json"
objective_md = DOCS / "idare_script_archival_and_reproducibility_objective.md"
objective_json = DOCS / "idare_script_archival_and_reproducibility_objective.json"
policy_csv = DOCS / "idare_script_archival_and_reproducibility_policy.csv"
inventory_seed_csv = DOCS / "idare_script_archival_and_reproducibility_inventory_seed.csv"
script_catalog_csv = DOCS / "idare_script_archival_target_catalog.csv"

status_json_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def git(args):
    return subprocess.check_output(["git"] + args, text=True).strip()

head = git(["rev-parse", "--short", "HEAD"])
branch = git(["branch", "--show-current"])
scripts = git(["ls-files", "scripts"]).splitlines()
script_count = len([s for s in scripts if s.strip()])

first_report = read_json(first_pass_report_json)
failure_obj = read_json(failure_obj_json)
review = read_json(first_pass_review_json)

accepted_pause = {
    "head_commit_at_pause": head,
    "branch": branch,
    "first_pass_diagnosis": first_report.get("diagnosis"),
    "first_pass_recommended_next_objective": first_report.get("recommended_next_objective"),
    "active_objective": str(failure_obj_md),
    "active_objective_next_allowed_step": failure_obj.get("next_allowed_step"),
    "reproducibility_gap": (
        "workflow commands were generated/executed from ~/Downloads, while corresponding reusable scripts have not been "
        "systematically archived under scripts/ in the repository"
    ),
    "tracked_script_count": script_count,
}
if accepted_pause["first_pass_diagnosis"] != "minimal_redesigned_task_first_pass_mixed_signal":
    raise SystemExit("ERROR: unexpected first-pass diagnosis at pause point")
if accepted_pause["active_objective_next_allowed_step"] != "prepare_reviewed_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_command":
    raise SystemExit("ERROR: active objective next step does not match expected pause point")

blocked = [
    "running failure-or-confirmation analysis before reproducibility layer is fixed",
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change unrelated to script archival",
    "deep neural training for redesigned task",
    "unregistered feature engineering",
]

pause = {
    "status": "paused_for_reproducibility_layer_fix",
    "created_utc": now,
    **accepted_pause,
    "decision": (
        "Pause the active read-only failure-or-confirmation analysis until script archival/reproducibility policy is "
        "created and the next analysis command is committed under scripts/."
    ),
    "next_selected_step": "create_script_archival_and_reproducibility_objective",
    "training_authorized": False,
    "blocked": blocked,
}
write_json(pause_json, pause)

pause_text = f"""# I-DARE Reproducibility-Layer Pause Status

## Status

Status: paused for reproducibility-layer fix.

Created UTC: `{now}`

## Pause Point

HEAD at pause: `{head}`

Branch: `{branch}`

Active scientific objective: `docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.md`

Active next allowed scientific step: `{accepted_pause["active_objective_next_allowed_step"]}`

First-pass diagnosis: `{accepted_pause["first_pass_diagnosis"]}`

First-pass recommended next objective: `{accepted_pause["first_pass_recommended_next_objective"]}`

## Reason for Pause

Workflow outputs have been generated and committed, but the reusable scripts/commands have mostly lived outside the repository under `~/Downloads`.

That weakens reproducibility even when reports are committed.

## Decision

Pause the active read-only failure-or-confirmation analysis until a script archival and reproducibility objective is created.

## Next Selected Step

Create/use `docs/idare_script_archival_and_reproducibility_objective.md`.

## Blocked

- running failure-or-confirmation analysis before reproducibility layer is fixed
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change unrelated to script archival
- deep neural training for redesigned task
- unregistered feature engineering
"""
pause_md.write_text(pause_text, encoding="utf-8")

policy_rows = [
    {
        "policy_id": "P1",
        "policy": "Every future I-DARE command script must be committed under scripts/idare/ before or at the same commit as the output it generates.",
        "rationale": "Reports without committed scripts are not fully reproducible.",
        "required": "yes",
    },
    {
        "policy_id": "P2",
        "policy": "Each script must reference its objective document and write deterministic outputs to docs/.",
        "rationale": "Traceability from objective to command to report must be explicit.",
        "required": "yes",
    },
    {
        "policy_id": "P3",
        "policy": "Scripts must guard against dirty repos unless explicitly designed to salvage existing partial outputs.",
        "rationale": "Avoid accidental contamination of evidence.",
        "required": "yes",
    },
    {
        "policy_id": "P4",
        "policy": "Scripts must validate expected inputs, expected outputs, JSON parseability, and key status/diagnosis terms.",
        "rationale": "Prevent silent invalid outputs.",
        "required": "yes",
    },
    {
        "policy_id": "P5",
        "policy": "Scripts must not authorize blocked work such as SupCon/DG, fusion, broad search, or final LOSO claim unless a reviewed objective explicitly allows it.",
        "rationale": "Preserve the staged scientific protocol.",
        "required": "yes",
    },
    {
        "policy_id": "P6",
        "policy": "For historical ~/Downloads scripts, archive the current/next critical scripts first, then backfill earlier scripts only when reconstructable from logs.",
        "rationale": "Do not fabricate historical scripts; prefer honest forward reproducibility.",
        "required": "yes",
    },
]
pd.DataFrame(policy_rows).to_csv(policy_csv, index=False)

inventory_rows = [
    {
        "item_id": "I1",
        "script_name": "run_idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis.py",
        "target_path": "scripts/idare/analysis/run_idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis.py",
        "source_objective": str(failure_obj_md),
        "status": "must_create_before_running_active_analysis",
        "priority": "high",
    },
    {
        "item_id": "I2",
        "script_name": "README.md",
        "target_path": "scripts/idare/README.md",
        "source_objective": str(objective_md),
        "status": "must_create_with_archival_command",
        "priority": "high",
    },
    {
        "item_id": "I3",
        "script_name": "script_archival_manifest.csv",
        "target_path": "docs/idare_script_archival_manifest.csv",
        "source_objective": str(objective_md),
        "status": "must_create_with_archival_command",
        "priority": "high",
    },
    {
        "item_id": "I4",
        "script_name": "historical_download_scripts",
        "target_path": "scripts/idare/archive_or_reconstructed/",
        "source_objective": "logs and docs references",
        "status": "optional_backfill_only_if_reconstructable",
        "priority": "medium",
    },
]
pd.DataFrame(inventory_rows).to_csv(inventory_seed_csv, index=False)

catalog_rows = []
for s in scripts:
    p = Path(s)
    catalog_rows.append({
        "path": s,
        "name": p.name,
        "directory": str(p.parent),
        "tracked_in_git": "yes",
        "current_archival_status": "pre_existing_repo_script",
    })
pd.DataFrame(catalog_rows).to_csv(script_catalog_csv, index=False)

objective = {
    "status": "objective_created",
    "created_utc": now,
    "source_pause_status": str(pause_md),
    "source_active_scientific_objective": str(failure_obj_md),
    "scientific_question": (
        "How do we restore reproducibility before continuing the active I-DARE failure-or-confirmation analysis?"
    ),
    "authorized_work": [
        "define script archival policy",
        "create scripts/idare/ directory structure if missing",
        "commit the next active read-only analysis script under scripts/idare/analysis/",
        "create a reproducibility manifest linking objective, script, command, outputs, and commit",
        "optionally backfill earlier ~/Downloads scripts only if reconstructable from logs",
        "update docs/project_status_current.* with script archival status",
    ],
    "not_authorized": blocked,
    "required_outputs": [
        "scripts/idare/README.md",
        "scripts/idare/analysis/run_idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis.py",
        "docs/idare_script_archival_manifest.csv",
        "docs/idare_script_archival_and_reproducibility_report.md",
        "docs/idare_script_archival_and_reproducibility_report.json",
    ],
    "pass_criteria": [
        "active next analysis script exists under scripts/idare/analysis/",
        "script has executable shebang or documented command",
        "script references its objective document",
        "manifest links script to objective and expected outputs",
        "no new training is executed",
        "no broad search, SupCon/DG, fusion, or final claims are authorized",
        "after this objective is complete, active failure-or-confirmation analysis may be run from committed script path",
    ],
    "next_allowed_step": "prepare_reviewed_script_archival_and_reproducibility_command",
    "training_authorized": False,
    "blocked": blocked,
}
write_json(objective_json, objective)

objective_text = f"""# I-DARE Script Archival and Reproducibility Objective

## Status

Status: objective created; reproducibility-layer fix only; no training is authorized.

Created UTC: `{now}`

## Current Pause Point

Active scientific objective: `docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.md`

Active scientific next step is paused: `{accepted_pause["active_objective_next_allowed_step"]}`

First-pass diagnosis: `{accepted_pause["first_pass_diagnosis"]}`

## Scientific Question

How do we restore reproducibility before continuing the active I-DARE failure-or-confirmation analysis?

## Problem Statement

The scientific outputs are committed, but many command scripts have been generated/executed from `~/Downloads` rather than committed under `scripts/`.

This creates a reproducibility gap: a reviewer can see the results, but not always the exact reusable command that produced them.

## Authorized Work

- Define script archival policy.
- Create `scripts/idare/` directory structure if missing.
- Commit the next active read-only analysis script under `scripts/idare/analysis/`.
- Create a reproducibility manifest linking objective, script, command, outputs, and commit.
- Optionally backfill earlier `~/Downloads` scripts only if reconstructable from logs.
- Update `docs/project_status_current.*` with script archival status.

## Not Authorized

- running failure-or-confirmation analysis before reproducibility layer is fixed
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change unrelated to script archival
- deep neural training for redesigned task
- unregistered feature engineering

## Required Outputs

- `scripts/idare/README.md`
- `scripts/idare/analysis/run_idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis.py`
- `docs/idare_script_archival_manifest.csv`
- `docs/idare_script_archival_and_reproducibility_report.md`
- `docs/idare_script_archival_and_reproducibility_report.json`

## Pass Criteria

- Active next analysis script exists under `scripts/idare/analysis/`.
- Script has executable shebang or documented command.
- Script references its objective document.
- Manifest links script to objective and expected outputs.
- No new training is executed.
- No broad search, SupCon/DG, fusion, or final claims are authorized.
- After this objective is complete, active failure-or-confirmation analysis may be run from committed script path.

## Next Allowed Step

Prepare a reviewed script archival and reproducibility command.

## Blocked

- running failure-or-confirmation analysis before reproducibility layer is fixed
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change unrelated to script archival
- deep neural training for redesigned task
- unregistered feature engineering
"""
objective_md.write_text(objective_text, encoding="utf-8")

status = read_json(status_json_path)
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "prepare_reviewed_script_archival_and_reproducibility_command"
status["current_idare_blocked_steps"] = blocked
events = status.get("idare_protocol_events")
if not isinstance(events, list):
    events = []
status["idare_protocol_events"] = events
events.extend([
    {
        "timestamp_utc": now,
        "type": "pause",
        "name": "I-DARE reproducibility-layer pause",
        "status": "active failure-or-confirmation analysis paused until script archival layer is fixed",
        "evidence": str(pause_md),
        "next_allowed_step": "create/use script archival and reproducibility objective",
        "blocked": blocked,
    },
    {
        "timestamp_utc": now,
        "type": "objective",
        "name": "I-DARE script archival and reproducibility objective",
        "status": "objective created; no training authorized",
        "evidence": str(objective_md),
        "next_allowed_step": "prepare reviewed script archival command",
        "blocked": blocked,
    },
])
write_json(status_json_path, status)

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Script Archival and Reproducibility Objective

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE reproducibility-layer pause | active failure-or-confirmation analysis paused until scripts are archived | `docs/idare_reproducibility_layer_pause_status.md` | Create/use script archival and reproducibility objective. | running failure-or-confirmation analysis before reproducibility layer is fixed; direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim |
| I-DARE script archival and reproducibility objective | objective created; no training authorized | `docs/idare_script_archival_and_reproducibility_objective.md` | Prepare reviewed script archival command. | running failure-or-confirmation analysis before reproducibility layer is fixed; direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim |

- Pause point preserved at commit `{head}` before running the active failure-or-confirmation analysis.
- Next work is to commit the active analysis script under `scripts/idare/analysis/` and create a manifest.
"""
if "I-DARE Script Archival and Reproducibility Objective" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_SCRIPT_ARCHIVAL_REPRODUCIBILITY_OBJECTIVE_WRITTEN")
print(pause_md)
print(pause_json)
print(objective_md)
print(objective_json)
print(policy_csv)
print(inventory_seed_csv)
print(script_catalog_csv)
print("pause_commit=", head)
print("tracked_script_files=", script_count)
print("active_scientific_next_step=", accepted_pause["active_objective_next_allowed_step"])
print("next_allowed_step=prepare_reviewed_script_archival_and_reproducibility_command")
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_paths = [
    Path("docs/idare_reproducibility_layer_pause_status.json"),
    Path("docs/idare_script_archival_and_reproducibility_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

for p, expected_rows in [
    (Path("docs/idare_script_archival_and_reproducibility_policy.csv"), 6),
    (Path("docs/idare_script_archival_and_reproducibility_inventory_seed.csv"), 4),
]:
    df = pd.read_csv(p)
    print(p.name, "rows=", len(df))
    if len(df) != expected_rows:
        raise SystemExit(f"ERROR: {p} expected {expected_rows} rows, got {len(df)}")

catalog = pd.read_csv("docs/idare_script_archival_target_catalog.csv")
print("script_catalog_rows=", len(catalog))

term_checks = {
    "docs/idare_reproducibility_layer_pause_status.md": [
        "paused for reproducibility-layer fix",
        "failure-or-confirmation analysis",
        "script archival",
        "direct full SupCon/DG training",
    ],
    "docs/idare_script_archival_and_reproducibility_objective.md": [
        "Scientific Question",
        "Problem Statement",
        "Authorized Work",
        "Required Outputs",
        "Pass Criteria",
        "scripts/idare/analysis",
        "direct full SupCon/DG training",
    ],
}
for path, terms in term_checks.items():
    text = Path(path).read_text(encoding="utf-8")
    for term in terms:
        if term not in text:
            raise SystemExit(f"ERROR: missing term {term!r} in {path}")
    print("OK_TERMS:", path)

obj = json.loads(Path("docs/idare_script_archival_and_reproducibility_objective.json").read_text(encoding="utf-8"))
if obj.get("next_allowed_step") != "prepare_reviewed_script_archival_and_reproducibility_command":
    raise SystemExit("ERROR: wrong next_allowed_step")
if obj.get("training_authorized") is not False:
    raise SystemExit("ERROR: training_authorized must be false")
print("next_allowed_step=", obj["next_allowed_step"])
print("ALL_SCRIPT_ARCHIVAL_REPRODUCIBILITY_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "Status|Current Pause Point|Scientific Question|Problem Statement|Authorized Work|Required Outputs|Pass Criteria|Next Allowed Step" \
  docs/idare_script_archival_and_reproducibility_objective.md
grep -nE "Script Archival and Reproducibility|reproducibility-layer pause|Pause point preserved" docs/project_status_current.md | tail -n 10
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_reproducibility_layer_pause_status.md \
  docs/idare_reproducibility_layer_pause_status.json \
  docs/idare_script_archival_and_reproducibility_objective.md \
  docs/idare_script_archival_and_reproducibility_objective.json \
  docs/idare_script_archival_and_reproducibility_policy.csv \
  docs/idare_script_archival_and_reproducibility_inventory_seed.csv \
  docs/idare_script_archival_target_catalog.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE script archival reproducibility objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
