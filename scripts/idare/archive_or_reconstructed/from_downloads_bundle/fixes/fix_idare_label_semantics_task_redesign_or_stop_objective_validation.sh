#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_task_redesign_or_stop_objective_fix.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start fix label-semantics task-redesign/stop objective validation ====="
date
git status --short --branch
echo

echo "===== 1) choose python ====="
PY="${PY:-.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3)"
fi
echo "PY=$PY"
"$PY" - <<'PY'
import json
from pathlib import Path
print("OK_IMPORTS")
PY
echo

echo "===== 2) require expected partial outputs from previous failed script ====="
required=(
  docs/idare_representation_or_label_semantics_failure_analysis_review_status.md
  docs/idare_representation_or_label_semantics_failure_analysis_review_status.json
  docs/idare_label_semantics_task_redesign_or_stop_objective.md
  docs/idare_label_semantics_task_redesign_or_stop_objective.json
  docs/project_status_current.json
  docs/project_status_current.md
)
for f in "${required[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "ERROR: missing expected partial output: $f" >&2
    exit 2
  fi
  ls -lh "$f"
done
echo

echo "===== 3) patch validation wording in objective doc ====="
"$PY" - <<'PY'
from pathlib import Path

p = Path("docs/idare_label_semantics_task_redesign_or_stop_objective.md")
text = p.read_text(encoding="utf-8")

# The failed validator searches for the exact lowercase phrase.
# Keep this idempotent and avoid changing scientific content.
if "direct full SupCon/DG training" not in text:
    replacements = [
        ("- Direct full SupCon/DG training remains blocked.", "- direct full SupCon/DG training remains blocked."),
        ("- Direct full SupCon/DG training", "- direct full SupCon/DG training"),
    ]
    changed = False
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new)
            changed = True
    if not changed:
        marker = "## Pass Criteria\n"
        insert = (
            "## Pass Criteria\n\n"
            "- direct full SupCon/DG training remains blocked.\n"
        )
        if marker in text:
            text = text.replace(marker, insert, 1)
        else:
            text += "\n\n## Validation Guardrail\n\n- direct full SupCon/DG training remains blocked.\n"

# Also normalize the broad-search line if needed.
if "broad hyperparameter search" not in text:
    text += "\n- broad hyperparameter search remains blocked.\n"

p.write_text(text, encoding="utf-8")
print("OK_PATCHED_OBJECTIVE_WORDING")
PY
echo

echo "===== 4) validate generated docs after fix ====="
"$PY" - <<'PY'
import json
from pathlib import Path

json_paths = [
    Path("docs/idare_representation_or_label_semantics_failure_analysis_review_status.json"),
    Path("docs/idare_label_semantics_task_redesign_or_stop_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

for p in [
    Path("docs/idare_representation_or_label_semantics_failure_analysis_review_status.md"),
    Path("docs/idare_label_semantics_task_redesign_or_stop_objective.md"),
]:
    text = p.read_text(encoding="utf-8")
    for term in ["Status", "direct full SupCon/DG training", "broad hyperparameter search", "final LOSO claim"]:
        if term not in text:
            raise SystemExit(f"ERROR: missing term {term!r} in {p}")
    print("OK_TERMS:", p)

obj = json.loads(Path("docs/idare_label_semantics_task_redesign_or_stop_objective.json").read_text(encoding="utf-8"))
print("next_allowed_step=", obj.get("next_allowed_step"))
if obj.get("next_allowed_step") != "prepare_reviewed_label_semantics_task_redesign_or_stop_report_command":
    raise SystemExit("ERROR: wrong next_allowed_step")

print("ALL_LABEL_SEMANTICS_TASK_REDESIGN_OR_STOP_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "Status|Scientific Question|Authorized Work|Candidate Decisions|Pass Criteria|Next Allowed Step|direct full SupCon/DG training" \
  docs/idare_label_semantics_task_redesign_or_stop_objective.md
grep -nE "label-semantics task-redesign-or-stop|representation or label-semantics failure-analysis review" \
  docs/project_status_current.md | tail -n 10
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push fixed objective ====="
git add \
  docs/idare_representation_or_label_semantics_failure_analysis_review_status.md \
  docs/idare_representation_or_label_semantics_failure_analysis_review_status.json \
  docs/idare_label_semantics_task_redesign_or_stop_objective.md \
  docs/idare_label_semantics_task_redesign_or_stop_objective.json \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE label semantics task redesign objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
