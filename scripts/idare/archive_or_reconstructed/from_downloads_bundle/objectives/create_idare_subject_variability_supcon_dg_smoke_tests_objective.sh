#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start SupCon/DG design review + smoke-tests objective ====="
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
  echo "ERROR: repository is not clean. Commit/stash changes before creating smoke objective." >&2
  git status --short --branch >&2
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required design/evidence docs ====="
ls -lh \
  docs/idare_subject_variability_supcon_dg_design_spec.md \
  docs/idare_subject_variability_supcon_dg_design_spec.json \
  docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv \
  docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv \
  docs/idare_subject_variability_supcon_dg_smoke_test_plan.csv \
  docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv \
  docs/idare_subject_variability_intervention_failure_analysis_review_status.md \
  docs/idare_subject_variability_intervention_failure_analysis_report.md \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 3) create design review closeout + SupCon/DG smoke-tests objective ====="
"$PY" - <<'PY'
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

DESIGN_MD = DOCS / "idare_subject_variability_supcon_dg_design_spec.md"
DESIGN_JSON = DOCS / "idare_subject_variability_supcon_dg_design_spec.json"
PAIR_CSV = DOCS / "idare_subject_variability_supcon_dg_pair_sampler_spec.csv"
HP_CSV = DOCS / "idare_subject_variability_supcon_dg_hyperparameter_registry.csv"
SMOKE_PLAN_CSV = DOCS / "idare_subject_variability_supcon_dg_smoke_test_plan.csv"
RUN_MATRIX_CSV = DOCS / "idare_subject_variability_supcon_dg_first_pass_run_matrix.csv"
INTERVENTION_REVIEW_MD = DOCS / "idare_subject_variability_intervention_failure_analysis_review_status.md"
INTERVENTION_REPORT_MD = DOCS / "idare_subject_variability_intervention_failure_analysis_report.md"

REVIEW_MD = DOCS / "idare_subject_variability_supcon_dg_design_spec_review_status.md"
REVIEW_JSON = DOCS / "idare_subject_variability_supcon_dg_design_spec_review_status.json"
OBJECTIVE_MD = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_objective.md"
OBJECTIVE_JSON = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_objective.json"

PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

required = [
    DESIGN_MD, DESIGN_JSON, PAIR_CSV, HP_CSV, SMOKE_PLAN_CSV, RUN_MATRIX_CSV,
    INTERVENTION_REVIEW_MD, INTERVENTION_REPORT_MD, PROJECT_MD, PROJECT_JSON
]
for p in required:
    if not p.exists():
        raise SystemExit(f"ERROR: required file missing: {p}")

design = json.loads(DESIGN_JSON.read_text(encoding="utf-8"))

def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

pair_rows = read_csv(PAIR_CSV)
hp_rows = read_csv(HP_CSV)
smoke_rows = read_csv(SMOKE_PLAN_CSV)
run_rows = read_csv(RUN_MATRIX_CSV)

required_smokes = [
    "pair_sampler_integrity_smoke",
    "leakage_guard_smoke",
    "supcon_micro_overfit_smoke",
    "shuffled_label_negative_control",
    "one_fold_one_task_minimal_smoke",
]
found_smokes = {r.get("smoke_test") for r in smoke_rows}
missing = [s for s in required_smokes if s not in found_smokes]
if missing:
    raise SystemExit(f"ERROR: missing required smoke tests in design smoke plan: {missing}")

review = {
    "status": "human_review_accepted",
    "created_or_updated_utc": NOW,
    "reviewed_artifact": str(DESIGN_MD),
    "reviewed_artifact_json": str(DESIGN_JSON),
    "review_decision": "accepted_for_smoke_tests_only",
    "summary": {
        "design_spec_complete": True,
        "pair_sampler_spec_rows": len(pair_rows),
        "hyperparameter_registry_rows": len(hp_rows),
        "smoke_test_plan_rows": len(smoke_rows),
        "draft_run_matrix_rows": len(run_rows),
        "training_authorized": False,
        "full_supcon_dg_training_authorized": False,
        "smoke_tests_authorized_next": True,
    },
    "accepted_constraints": [
        "SupCon/DG must proceed through smoke tests before any first-pass training.",
        "Positive/negative pair and sampler integrity must be audited before model training.",
        "Leakage guard must pass before any training result can be trusted.",
        "Hyperparameter changes must be registry-based and staged, not broad-grid.",
        "Failure interpretation must be tied to smoke outputs, not just aggregate metric movement.",
    ],
    "next_selected_step": "subject_variability_supcon_dg_smoke_tests_objective",
    "blocked_until_after_smoke_review": [
        "direct SupCon/DG training",
        "broad hyperparameter search",
        "fusion",
        "mainline change",
        "final LOSO claim",
    ],
}
REVIEW_JSON.write_text(json.dumps(review, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

review_md = f"""# I-DARE Subject-variability SupCon/DG Design Spec Review Status

## Status

Human review accepted the cautious SupCon/DG design spec for smoke-test preparation only.

Generated UTC: `{NOW}`

## Reviewed Artifact

- Design spec: `{DESIGN_MD}`
- Design spec JSON: `{DESIGN_JSON}`
- Pair/sampler spec: `{PAIR_CSV}`
- Hyperparameter registry: `{HP_CSV}`
- Smoke-test plan: `{SMOKE_PLAN_CSV}`
- Draft first-pass matrix: `{RUN_MATRIX_CSV}`

## Review Decision

Accepted with caution.

The design is considered sufficient to create a smoke-test objective.

It does **not** authorize full SupCon/DG training.

## Accepted Constraints

- Pair/sampler integrity must be validated before training.
- Leakage guard must pass before any model result is trusted.
- SupCon micro-overfit must pass before any subject-heldout smoke.
- Shuffled-label negative control must not show suspicious performance.
- Hyperparameter selection must remain staged and registry-based.
- Any future improvement must be explainable through sampler logs, loss traces, and embedding/risk diagnostics.

## Next Selected Step

Create and run a smoke-test-only objective:

- `docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md`

## Still Blocked

- full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- mainline change
- final LOSO claim
"""
REVIEW_MD.write_text(review_md, encoding="utf-8")

objective = {
    "status": "objective_created",
    "created_or_updated_utc": NOW,
    "objective_type": "diagnostic_smoke_tests_only",
    "parent_review": str(REVIEW_MD),
    "parent_design_spec": str(DESIGN_MD),
    "authorized_scope": {
        "training_authorized": False,
        "smoke_tests_authorized": True,
        "modalities": ["EEG", "EMG"],
        "tasks": ["valence", "arousal"],
        "fold_scope": "fold1_only unless explicitly noted",
        "label_formulation": "subject_top_bottom_quantile_q33",
        "allowed_method_components": [
            "CE baseline branch for comparison inside smoke",
            "SupCon projection head",
            "CE+SupCon loss",
            "optional VREx computation only as diagnostic if implemented readably",
        ],
    },
    "required_smoke_tests": [
        {
            "name": "pair_sampler_integrity_smoke",
            "pass_gate": "all audited batches contain both classes, at least 4 subjects, positive_pair_coverage >= 0.95, anchors_without_positive <= 0.05",
            "failure_means": "sampler/pair design invalid; do not train",
        },
        {
            "name": "leakage_guard_smoke",
            "pass_gate": "no validation sample appears in train scaler, train pairs, positive/negative pools, or environment-risk terms",
            "failure_means": "protocol invalid",
        },
        {
            "name": "supcon_micro_overfit_smoke",
            "pass_gate": "tiny train-only subset overfits; CE and SupCon losses are finite and decreasing; embeddings do not collapse",
            "failure_means": "implementation or optimization bug",
        },
        {
            "name": "shuffled_label_negative_control",
            "pass_gate": "train-label-shuffled control remains near chance and does not show suspicious gain",
            "failure_means": "leakage or invalid evaluation likely",
        },
        {
            "name": "one_fold_one_task_minimal_smoke",
            "pass_gate": "one fold/task run completes with valid logs, non-collapsed predictions, and embedding/pair diagnostics",
            "failure_means": "inspect logs before expanding",
        },
    ],
    "expected_outputs": [
        "docs/idare_subject_variability_supcon_dg_smoke_tests_report.md",
        "docs/idare_subject_variability_supcon_dg_smoke_tests_report.json",
        "docs/idare_subject_variability_supcon_dg_pair_sampler_audit.csv",
        "docs/idare_subject_variability_supcon_dg_loss_trace_summary.csv",
        "docs/idare_subject_variability_supcon_dg_embedding_diagnostic_summary.csv",
    ],
    "pass_criteria": [
        "all required smoke tests execute or clearly report why a test cannot execute",
        "pair/sampler audit is generated",
        "leakage guard passes",
        "micro-overfit passes",
        "negative control does not indicate leakage",
        "one-fold minimal smoke produces interpretable diagnostics",
        "next action is based on smoke evidence, not metric optimism",
    ],
    "not_authorized": [
        "full first-pass SupCon/DG training matrix",
        "broad hyperparameter search",
        "fusion",
        "mainline change",
        "final LOSO claim",
    ],
    "next_allowed_step_after_this_objective": "prepare reviewed implementation/run command for smoke tests only",
}
OBJECTIVE_JSON.write_text(json.dumps(objective, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

smoke_list_md = "\n".join(
    f"{i+1}. `{s['name']}` — pass gate: {s['pass_gate']}"
    for i, s in enumerate(objective["required_smoke_tests"])
)

expected_md = "\n".join(f"- `{x}`" for x in objective["expected_outputs"])
blocked_md = "\n".join(f"- {x}" for x in objective["not_authorized"])

objective_md = f"""# I-DARE Subject-variability SupCon/DG Smoke Tests Objective

## Status

Objective created.

This is a smoke-test-only objective.

No full SupCon/DG training is authorized by this document.

Generated UTC: `{NOW}`

## Parent Review

- Review: `{REVIEW_MD}`
- Design spec: `{DESIGN_MD}`

## Scientific Question

Can the proposed SupCon/DG intervention be implemented safely enough to justify a future minimal first-pass training objective?

This objective does not ask whether SupCon/DG improves final performance.

It asks whether the pair sampler, leakage guards, loss implementation, negative controls, and minimal one-fold execution are valid.

## Authorized Scope

Authorized:

- smoke tests only;
- temporary local implementation/helpers if needed;
- fold-1-only diagnostic runs unless the script is explicitly read-only;
- subject-relative q33 labels;
- CE+SupCon smoke branch;
- logs for pair coverage, loss traces, embedding separation, and negative controls.

Not authorized:

{blocked_md}

## Required Smoke Tests

{smoke_list_md}

## Expected Outputs

{expected_md}

## Pass Criteria

The smoke-test objective passes only if:

- all required smoke tests execute or fail with a clear diagnostic reason;
- leakage guard passes;
- pair sampler audit satisfies the design gates;
- micro-overfit succeeds without collapse;
- shuffled-label negative control does not show suspicious performance;
- one-fold minimal smoke produces interpretable predictions and diagnostics;
- the report recommends either implementation fixes, sampler fixes, or a future minimal training objective.

## Failure Interpretation

If smoke tests fail, the correct response is not to tune broadly.

The correct response is to localize the failure:

- sampler failure -> fix positive/negative pair construction;
- leakage failure -> fix protocol;
- micro-overfit failure -> fix implementation/optimization;
- negative-control failure -> audit leakage/evaluation;
- one-fold smoke failure -> inspect pair coverage, loss traces, embedding diagnostics, and prediction collapse.

## Next Allowed Step

Prepare a reviewed Bash command/script for smoke tests only.
"""
OBJECTIVE_MD.write_text(objective_md, encoding="utf-8")

# Update project roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
review_row = "| I-DARE subject-variability SupCon/DG design spec review | human review accepted cautious design for smoke tests only | yes | `docs/idare_subject_variability_supcon_dg_design_spec_review_status.md` | Create/run SupCon/DG smoke-tests objective. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training; broad hyperparameter search; mainline change. |"
objective_row = "| I-DARE subject-variability SupCon/DG smoke-tests objective | short-term smoke-test-only objective created; no full training authorized | yes | `docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md` | Prepare reviewed smoke-test implementation/run command. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training; broad hyperparameter search; mainline change. |"

if review_row not in project_md or objective_row not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE subject-variability SupCon/DG design spec |"):
            if review_row not in project_md:
                out.append(review_row)
            if objective_row not in project_md:
                out.append(objective_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not find SupCon/DG design spec row in project_status_current.md")
    project_md = "\n".join(out) + "\n"

bullet_review = "- Human review of the cautious SupCon/DG design spec is frozen in `docs/idare_subject_variability_supcon_dg_design_spec_review_status.md`; only smoke tests are authorized next."
bullet_obj = "- A smoke-test-only SupCon/DG objective is defined in `docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md`; full SupCon/DG training remains blocked until smoke-test review."
for bullet in [bullet_review, bullet_obj]:
    if bullet not in project_md:
        marker = "\n## Documentation Gap Closed by This File"
        if marker not in project_md:
            raise SystemExit("ERROR: marker not found in project_status_current.md")
        project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_subject_variability_supcon_dg_design_spec_review"] = {
    "status": "human_review_accepted",
    "evidence": str(REVIEW_MD),
    "evidence_json": str(REVIEW_JSON),
    "reviewed_artifact": str(DESIGN_MD),
    "decision": "accepted_for_smoke_tests_only",
    "training_authorized": False,
    "smoke_tests_authorized_next": True,
}
decisions["idare_subject_variability_supcon_dg_smoke_tests_objective"] = {
    "status": "objective_created",
    "evidence": str(OBJECTIVE_MD),
    "evidence_json": str(OBJECTIVE_JSON),
    "objective_type": "diagnostic_smoke_tests_only",
    "training_authorized": False,
    "smoke_tests_authorized": True,
    "required_smoke_tests": required_smokes,
    "next_allowed_step": "prepare reviewed smoke-test implementation/run command",
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_SUPCON_DG_SMOKE_OBJECTIVE_WRITTEN")
print(REVIEW_MD)
print(REVIEW_JSON)
print(OBJECTIVE_MD)
print(OBJECTIVE_JSON)
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path

paths = [
    Path("docs/idare_subject_variability_supcon_dg_design_spec_review_status.json"),
    Path("docs/idare_subject_variability_supcon_dg_smoke_tests_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in paths:
    data = json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)
    if p.name == "idare_subject_variability_supcon_dg_smoke_tests_objective.json":
        if data.get("status") != "objective_created":
            raise SystemExit("ERROR: wrong objective status")
        if data.get("authorized_scope", {}).get("training_authorized") is not False:
            raise SystemExit("ERROR: training should not be authorized")
        smoke_names = [x.get("name") for x in data.get("required_smoke_tests", [])]
        for required in [
            "pair_sampler_integrity_smoke",
            "leakage_guard_smoke",
            "supcon_micro_overfit_smoke",
            "shuffled_label_negative_control",
            "one_fold_one_task_minimal_smoke",
        ]:
            if required not in smoke_names:
                raise SystemExit(f"ERROR: missing required smoke test: {required}")

text = Path("docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md").read_text(encoding="utf-8")
for term in ["smoke-test-only", "Required Smoke Tests", "Failure Interpretation", "No full SupCon/DG training"]:
    if term not in text:
        raise SystemExit(f"ERROR: missing term in objective md: {term}")

print("ALL_SUPCON_DG_SMOKE_OBJECTIVE_OUTPUTS_VALID")
PY

grep -n "## Status\|## Review Decision\|## Next Selected Step" docs/idare_subject_variability_supcon_dg_design_spec_review_status.md
grep -n "## Status\|## Scientific Question\|## Authorized Scope\|## Required Smoke Tests\|## Pass Criteria\|## Next Allowed Step" docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md
grep -n "SupCon/DG design spec review\|SupCon/DG smoke-tests objective\|smoke-test-only" docs/project_status_current.md
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_subject_variability_supcon_dg_design_spec_review_status.md \
  docs/idare_subject_variability_supcon_dg_design_spec_review_status.json \
  docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md \
  docs/idare_subject_variability_supcon_dg_smoke_tests_objective.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE SupCon DG smoke-tests objective"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_supcon_dg_smoke_objective.log"
