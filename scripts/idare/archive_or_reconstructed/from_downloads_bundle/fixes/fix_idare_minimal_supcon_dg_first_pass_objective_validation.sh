#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start fix minimal SupCon/DG first-pass objective validation ====="
date
git status --short --branch
echo

echo "===== 1) choose python ====="
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif [ -x ".venv/bin/python3" ]; then
  PY=".venv/bin/python3"
else
  PY="python3"
fi
echo "PY=$PY"
"$PY" - <<'PY'
import sys, json
from pathlib import Path
print(sys.executable)
print("OK_IMPORTS")
PY
echo

echo "===== 2) require expected partial outputs from previous failed script ====="
ls -lh \
  docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.md \
  docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.json \
  docs/idare_minimal_supcon_dg_first_pass_training_objective.md \
  docs/idare_minimal_supcon_dg_first_pass_training_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 3) patch validation wording in objective doc ====="
"$PY" - <<'PY'
from pathlib import Path

p = Path("docs/idare_minimal_supcon_dg_first_pass_training_objective.md")
text = p.read_text(encoding="utf-8")

# The prior script wrote "direct full-scale SupCon/DG training", but its validator
# checked the exact phrase "direct full SupCon/DG training".
if "direct full SupCon/DG training" not in text:
    if "direct full-scale SupCon/DG training" in text:
        text = text.replace("direct full-scale SupCon/DG training", "direct full SupCon/DG training")
    else:
        marker = "## Next Allowed Step"
        insert = "\nNote: direct full SupCon/DG training remains explicitly blocked until first-pass review.\n\n"
        if marker not in text:
            raise SystemExit("ERROR: could not find insertion marker in objective doc")
        text = text.replace(marker, insert + marker)

p.write_text(text, encoding="utf-8")
print("OK_PATCHED_OBJECTIVE_WORDING")
PY
echo

echo "===== 4) validate generated docs after fix ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path

paths = [
    Path("docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.json"),
    Path("docs/idare_minimal_supcon_dg_first_pass_training_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

checks = {
    Path("docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.md"): [
        "Review Decision",
        "smoke-test gate is accepted",
        "Full SupCon/DG training",
    ],
    Path("docs/idare_minimal_supcon_dg_first_pass_training_objective.md"): [
        "Minimal SupCon/DG First-pass Training Objective",
        "Required First-pass Matrix",
        "Pass Criteria",
        "direct full SupCon/DG training",
    ],
}
for p, terms in checks.items():
    text = p.read_text(encoding="utf-8")
    for term in terms:
        if term not in text:
            raise SystemExit(f"ERROR: missing term {term!r} in {p}")

objective = json.loads(Path("docs/idare_minimal_supcon_dg_first_pass_training_objective.json").read_text(encoding="utf-8"))
if objective["authorized_scope"]["minimal_first_pass_training_authorized"] is not True:
    raise SystemExit("ERROR: minimal first-pass not authorized in objective")
if objective["authorized_scope"]["direct_full_training_authorized"] is not False:
    raise SystemExit("ERROR: direct full training should remain blocked")
if objective.get("planned_run_matrix_rows", 0) <= 0:
    raise SystemExit("ERROR: planned run matrix rows missing")

with Path("docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv").open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
if len(rows) != objective.get("planned_run_matrix_rows"):
    raise SystemExit(f"ERROR: run matrix row mismatch: csv={len(rows)} json={objective.get('planned_run_matrix_rows')}")

print("planned_run_matrix_rows=", objective.get("planned_run_matrix_rows"))
print("next_allowed_step=", objective.get("next_allowed_step"))
print("ALL_MINIMAL_SUPCON_DG_OBJECTIVE_OUTPUTS_VALID")
PY

grep -n "## Status\|## Review Decision\|## Next Selected Step" docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.md
grep -n "## Status\|## Scientific Question\|## Required First-pass Matrix\|## Pass Criteria\|## Next Allowed Step" docs/idare_minimal_supcon_dg_first_pass_training_objective.md
grep -n "SupCon/DG smoke-tests review\|minimal SupCon/DG first-pass training objective\|Human review of SupCon/DG smoke tests" docs/project_status_current.md
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push fixed objective ====="
git add \
  docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.md \
  docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.json \
  docs/idare_minimal_supcon_dg_first_pass_training_objective.md \
  docs/idare_minimal_supcon_dg_first_pass_training_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

if git diff --cached --quiet; then
  echo "NO_CHANGES_STAGED_TO_COMMIT"
else
  git commit -m "docs: add I-DARE minimal SupCon DG first-pass objective"
  git push origin main
fi
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_minimal_supcon_dg_first_pass_objective_fix.log"
