#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start SupCon/DG smoke review + minimal first-pass objective ====="
date
git status --short --branch
echo

echo "===== 1) choose python and require clean repo ====="
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif [ -x ".venv/bin/python3" ]; then
  PY=".venv/bin/python3"
else
  PY="python3"
fi
echo "PY=$PY"
"$PY" - <<'PY'
import sys
print(sys.executable)
import json
from pathlib import Path
print("OK_IMPORTS")
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repository is not clean. Commit/stash changes before creating the objective." >&2
  git status --short --branch >&2
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required smoke-test/design evidence ====="
ls -lh \
  docs/idare_subject_variability_supcon_dg_smoke_tests_report.md \
  docs/idare_subject_variability_supcon_dg_smoke_tests_report.json \
  docs/idare_subject_variability_supcon_dg_pair_sampler_audit.csv \
  docs/idare_subject_variability_supcon_dg_loss_trace_summary.csv \
  docs/idare_subject_variability_supcon_dg_embedding_diagnostic_summary.csv \
  docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md \
  docs/idare_subject_variability_supcon_dg_design_spec.md \
  docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv \
  docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 3) create smoke review closeout + minimal SupCon/DG first-pass objective ====="
"$PY" - <<'PY'
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

SMOKE_REPORT_MD = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_report.md"
SMOKE_REPORT_JSON = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_report.json"
SMOKE_OBJECTIVE_MD = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_objective.md"
DESIGN_SPEC_MD = DOCS / "idare_subject_variability_supcon_dg_design_spec.md"
RUN_MATRIX_CSV = DOCS / "idare_subject_variability_supcon_dg_first_pass_run_matrix.csv"
HP_REGISTRY_CSV = DOCS / "idare_subject_variability_supcon_dg_hyperparameter_registry.csv"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

REVIEW_MD = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_review_status.md"
REVIEW_JSON = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_review_status.json"
OBJECTIVE_MD = DOCS / "idare_minimal_supcon_dg_first_pass_training_objective.md"
OBJECTIVE_JSON = DOCS / "idare_minimal_supcon_dg_first_pass_training_objective.json"

for p in [
    SMOKE_REPORT_MD, SMOKE_REPORT_JSON, SMOKE_OBJECTIVE_MD, DESIGN_SPEC_MD,
    RUN_MATRIX_CSV, HP_REGISTRY_CSV, PROJECT_MD, PROJECT_JSON
]:
    if not p.exists():
        raise SystemExit(f"ERROR: missing required evidence: {p}")

smoke = json.loads(SMOKE_REPORT_JSON.read_text(encoding="utf-8"))
if smoke.get("diagnosis") != "supcon_dg_smoke_tests_passed_ready_for_minimal_first_pass_objective":
    raise SystemExit(f"ERROR: unexpected smoke diagnosis: {smoke.get('diagnosis')}")
if smoke.get("all_passed") is not True:
    raise SystemExit("ERROR: smoke tests did not all pass; minimal first-pass objective is not authorized")

# Count design matrix rows.
with RUN_MATRIX_CSV.open(newline="", encoding="utf-8") as f:
    run_rows = list(csv.DictReader(f))
run_matrix_count = len(run_rows)
if run_matrix_count <= 0:
    raise SystemExit("ERROR: first-pass run matrix is empty")

with HP_REGISTRY_CSV.open(newline="", encoding="utf-8") as f:
    hp_rows = list(csv.DictReader(f))
hp_count = len(hp_rows)

review_doc = f"""# I-DARE Subject-variability SupCon/DG Smoke Tests Review Status

## Status

Human review accepted the SupCon/DG smoke-test report.

Created UTC: `{NOW}`

Smoke-test report: `{SMOKE_REPORT_MD}`

Smoke-test objective: `{SMOKE_OBJECTIVE_MD}`

Design spec: `{DESIGN_SPEC_MD}`

## Review Decision

The smoke-test gate is accepted as passed.

Accepted evidence:

- pair/sampler integrity passed for EEG/EMG valence/arousal;
- leakage guard passed with no row or subject overlap;
- SupCon micro-overfit passed for all selected modality/task checks;
- shuffled-label negative control stayed near chance;
- one-fold minimal smoke did not collapse and produced finite two-class predictions.

## Scientific Interpretation

This does **not** prove SupCon/DG improves performance.

It only proves that the implementation path is safe enough for a minimal first-pass training objective.

Full SupCon/DG training, broad hyperparameter search, fusion, and final claims remain blocked.

## Next Selected Step

Create and run a minimal first-pass SupCon/DG training objective.

The first pass must remain diagnostic and small. It should use the reviewed design spec and first-pass run matrix, not invent new settings mid-run.

## Explicitly Still Blocked

- direct full SupCon/DG training;
- broad hyperparameter search;
- EEG+EMG fusion;
- final LOSO/paper claim;
- mainline/default replacement.
"""

review_payload = {
    "status": "review_accepted",
    "created_or_updated_utc": NOW,
    "reviewed_report": str(SMOKE_REPORT_MD),
    "reviewed_report_json": str(SMOKE_REPORT_JSON),
    "decision": "smoke_tests_passed_accept_minimal_first_pass_objective",
    "accepted_evidence": {
        "all_passed": True,
        "diagnosis": smoke.get("diagnosis"),
        "recommended_next_objective": smoke.get("recommended_next_objective"),
        "by_test": smoke.get("by_test", {}),
    },
    "next_selected_step": "minimal_supcon_dg_first_pass_training_objective",
    "blocked": [
        "direct_full_supcon_dg_training",
        "broad_hyperparameter_search",
        "eeg_emg_fusion",
        "final_loso_claim",
        "mainline_default_replacement",
    ],
}
REVIEW_MD.write_text(review_doc, encoding="utf-8")
REVIEW_JSON.write_text(json.dumps(review_payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

objective_doc = f"""# I-DARE Minimal SupCon/DG First-pass Training Objective

## Status

Short-term diagnostic training objective created.

Created UTC: `{NOW}`

Preceded by:

- smoke-test objective: `{SMOKE_OBJECTIVE_MD}`
- smoke-test report: `{SMOKE_REPORT_MD}`
- smoke-test review: `{REVIEW_MD}`
- design spec: `{DESIGN_SPEC_MD}`

## Scientific Question

Does the cautious SupCon/DG design improve subject-heldout generalization over the current subject-relative/preprocessed diagnostic baselines, without relying on leakage, broad tuning, or post-hoc threshold selection?

## Authorized Scope

This objective authorizes a **minimal first-pass** SupCon/DG training run only.

Authorized:

- use the reviewed pair/sampler design;
- use the reviewed hyperparameter registry;
- use the first-pass run matrix from `{RUN_MATRIX_CSV}`;
- log CE loss, SupCon loss, total loss, embedding diagnostics, prediction counts, and per-fold metrics;
- compare only against already committed subject-relative and preprocessed first-pass baselines;
- commit raw outputs and a combined report.

Not authorized:

- broad hyperparameter search;
- direct full-scale SupCon/DG training;
- changing the selected pair/sampler semantics during the run;
- adding EEG+EMG fusion;
- final LOSO or paper-level claims;
- replacing project mainline/default model.

## Required First-pass Matrix

Use the reviewed first-pass run matrix:

- file: `{RUN_MATRIX_CSV}`
- planned rows: `{run_matrix_count}`

The implementation command may reduce only if a technical smoke failure occurs. Otherwise, all planned rows should run.

## Hyperparameter Handling

Use the reviewed registry:

- file: `{HP_REGISTRY_CSV}`
- registry rows: `{hp_count}`

For every run, the output must record:

- modality;
- task;
- fold;
- seed;
- label formulation;
- encoder/feature path;
- SupCon temperature;
- SupCon loss weight;
- batch sampler type;
- CE/class weighting choice;
- epochs;
- learning rate;
- batch size.

## Required Safety Checks Before Training

The run script must fail before training if:

- repo is dirty;
- required cache/index/design/report files are missing;
- smoke-test review is missing;
- first-pass run matrix is empty;
- subject-heldout fold construction deviates from the reviewed seed/fold policy;
- a batch has no positive cross-subject pair availability;
- any train/validation row overlap or subject overlap is detected.

## Required Outputs

Expected output files:

- `docs/idare_minimal_supcon_dg_first_pass_report.md`
- `docs/idare_minimal_supcon_dg_first_pass_report.json`
- `docs/idare_minimal_supcon_dg_first_pass_runs.csv`
- `docs/idare_minimal_supcon_dg_first_pass_predictions.csv`
- `docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv`
- `docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv`

## Pass Criteria

The objective passes execution if:

1. all authorized runs complete or any skipped run is explicitly justified;
2. every run has valid finite metrics;
3. no one-class prediction collapse occurs without being flagged;
4. no leakage guard fails;
5. per-run hyperparameters are recorded;
6. a report states whether SupCon/DG is better, mixed, or not useful versus the prior diagnostic baselines.

Scientific success is stricter than execution success.

A positive scientific signal requires consistent improvement over prior subject-relative/preprocessed baselines, not just one isolated fold.

## Decision Tree After Report

If improved consistently:

- create a second-pass confirmation objective with a narrow hyperparameter expansion.

If mixed:

- inspect which modality/task/fold benefits, then create a targeted ablation objective.

If not improved:

- do not continue SupCon/DG blindly; diagnose whether pair definition, representation backbone, label formulation, or DG regularizer is the limiting factor.

## Next Allowed Step

Prepare a reviewed implementation/run command for the minimal SupCon/DG first-pass matrix.
"""

objective_payload = {
    "status": "objective_created",
    "created_or_updated_utc": NOW,
    "objective": str(OBJECTIVE_MD),
    "scientific_question": "Does cautious SupCon/DG improve subject-heldout generalization over current subject-relative/preprocessed diagnostic baselines?",
    "authorized_scope": {
        "minimal_first_pass_training_authorized": True,
        "direct_full_training_authorized": False,
        "broad_hyperparameter_search_authorized": False,
        "fusion_authorized": False,
        "final_claim_authorized": False,
        "mainline_change_authorized": False,
    },
    "evidence": {
        "smoke_report": str(SMOKE_REPORT_MD),
        "smoke_report_json": str(SMOKE_REPORT_JSON),
        "smoke_review": str(REVIEW_MD),
        "design_spec": str(DESIGN_SPEC_MD),
        "first_pass_run_matrix": str(RUN_MATRIX_CSV),
        "hyperparameter_registry": str(HP_REGISTRY_CSV),
        "smoke_diagnosis": smoke.get("diagnosis"),
    },
    "planned_run_matrix_rows": run_matrix_count,
    "hyperparameter_registry_rows": hp_count,
    "expected_outputs": [
        "docs/idare_minimal_supcon_dg_first_pass_report.md",
        "docs/idare_minimal_supcon_dg_first_pass_report.json",
        "docs/idare_minimal_supcon_dg_first_pass_runs.csv",
        "docs/idare_minimal_supcon_dg_first_pass_predictions.csv",
        "docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv",
        "docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv",
    ],
    "next_allowed_step": "prepare_reviewed_minimal_supcon_dg_first_pass_run_command",
    "blocked": [
        "direct_full_supcon_dg_training",
        "broad_hyperparameter_search",
        "eeg_emg_fusion",
        "final_loso_claim",
        "mainline_default_replacement",
    ],
}
OBJECTIVE_MD.write_text(objective_doc, encoding="utf-8")
OBJECTIVE_JSON.write_text(json.dumps(objective_payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

project_md = PROJECT_MD.read_text(encoding="utf-8")
review_row = "| I-DARE subject-variability SupCon/DG smoke-tests review | human review accepted smoke tests; minimal first-pass training selected next | yes | `docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.md` | Create/run minimal SupCon/DG first-pass objective. | EEG+EMG fusion; final LOSO claim; direct full SupCon/DG training; broad hyperparameter search; mainline change. |"
objective_row = "| I-DARE minimal SupCon/DG first-pass training objective | short-term diagnostic training objective created | yes | `docs/idare_minimal_supcon_dg_first_pass_training_objective.md` | Prepare reviewed implementation/run command for minimal first-pass matrix. | EEG+EMG fusion; final LOSO claim; direct full SupCon/DG training; broad hyperparameter search; mainline change. |"

if review_row not in project_md or objective_row not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE subject-variability SupCon/DG smoke-tests report |"):
            if review_row not in project_md:
                out.append(review_row)
            if objective_row not in project_md:
                out.append(objective_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not find smoke-tests report row in project_status_current.md")
    project_md = "\n".join(out) + "\n"

bullet1 = "- Human review of SupCon/DG smoke tests is frozen in `docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.md`; minimal first-pass training is selected, but full training remains blocked."
bullet2 = "- A minimal SupCon/DG first-pass training objective is defined in `docs/idare_minimal_supcon_dg_first_pass_training_objective.md`; next work is a reviewed implementation/run command, not broad search."
for bullet in [bullet1, bullet2]:
    if bullet not in project_md:
        marker = "\n## Documentation Gap Closed by This File"
        if marker not in project_md:
            raise SystemExit("ERROR: marker not found in project_status_current.md")
        project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)

PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_subject_variability_supcon_dg_smoke_tests_review"] = {
    "status": "review_accepted",
    "evidence": str(REVIEW_MD),
    "evidence_json": str(REVIEW_JSON),
    "decision": "minimal_supcon_dg_first_pass_training_selected",
    "full_training_authorized": False,
}
decisions["idare_minimal_supcon_dg_first_pass_training_objective"] = {
    "status": "objective_created",
    "evidence": str(OBJECTIVE_MD),
    "evidence_json": str(OBJECTIVE_JSON),
    "planned_run_matrix_rows": run_matrix_count,
    "next_allowed_step": "prepare_reviewed_minimal_supcon_dg_first_pass_run_command",
    "minimal_first_pass_training_authorized": True,
    "direct_full_training_authorized": False,
    "broad_hyperparameter_search_authorized": False,
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_MINIMAL_SUPCON_DG_FIRST_PASS_OBJECTIVE_WRITTEN")
print(REVIEW_MD)
print(REVIEW_JSON)
print(OBJECTIVE_MD)
print(OBJECTIVE_JSON)
print("planned_run_matrix_rows=", run_matrix_count)
print("hp_registry_rows=", hp_count)
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
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

echo "===== 7) commit and push ====="
git add \
  docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.md \
  docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.json \
  docs/idare_minimal_supcon_dg_first_pass_training_objective.md \
  docs/idare_minimal_supcon_dg_first_pass_training_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE minimal SupCon DG first-pass objective"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_minimal_supcon_dg_first_pass_objective.log"
