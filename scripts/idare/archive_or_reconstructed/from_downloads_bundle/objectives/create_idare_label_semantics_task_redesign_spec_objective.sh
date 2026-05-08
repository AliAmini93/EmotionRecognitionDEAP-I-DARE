#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_task_redesign_spec_objective.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start label-semantics task decision review + redesign-spec objective ====="
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

echo "===== 2) check required decision evidence ====="
required=(
  docs/idare_label_semantics_task_redesign_or_stop_objective.md
  docs/idare_label_semantics_task_redesign_or_stop_objective.json
  docs/idare_label_semantics_task_redesign_or_stop_report.md
  docs/idare_label_semantics_task_redesign_or_stop_report.json
  docs/idare_label_semantics_task_redesign_or_stop_decision_matrix.csv
  docs/idare_label_semantics_task_candidate_matrix.csv
  docs/idare_label_semantics_evidence_gap_audit.csv
  docs/idare_representation_or_label_semantics_failure_analysis_report.md
  docs/idare_representation_or_label_semantics_failure_analysis_report.json
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

echo "===== 3) create review closeout + label-semantics task-redesign spec objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

report_json_path = DOCS / "idare_label_semantics_task_redesign_or_stop_report.json"
review_md_path = DOCS / "idare_label_semantics_task_redesign_or_stop_report_review_status.md"
review_json_path = DOCS / "idare_label_semantics_task_redesign_or_stop_report_review_status.json"
objective_md_path = DOCS / "idare_label_semantics_task_redesign_spec_objective.md"
objective_json_path = DOCS / "idare_label_semantics_task_redesign_spec_objective.json"
status_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

report = json.loads(report_json_path.read_text(encoding="utf-8"))
diagnosis = report.get("diagnosis", "current_global_binary_loso_task_not_defensible_for_more_model_search")
decision = report.get("decision", "pause_current_global_binary_loso_training_and_prepare_task_redesign_spec")
recommended = report.get("recommended_next_objective", "label_semantics_task_redesign_spec_objective")
stop_condition = report.get("stop_condition", "If a defensible redesign spec cannot be accepted, stop/archive the current binary LOSO branch.")

candidate_df = pd.read_csv(DOCS / "idare_label_semantics_task_candidate_matrix.csv")
decision_df = pd.read_csv(DOCS / "idare_label_semantics_task_redesign_or_stop_decision_matrix.csv")
gap_df = pd.read_csv(DOCS / "idare_label_semantics_evidence_gap_audit.csv")

review = {
    "status": "human_review_accepted",
    "created_utc": now,
    "reviewed_report": "docs/idare_label_semantics_task_redesign_or_stop_report.md",
    "accepted_diagnosis": diagnosis,
    "accepted_decision": decision,
    "accepted_recommended_next_objective": recommended,
    "stop_condition": stop_condition,
    "next_selected_step": "create_label_semantics_task_redesign_spec_objective",
    "blocked": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
        "new training before redesign spec review",
    ],
}
review_json_path.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

review_md = f"""# I-DARE Label-Semantics Task-Redesign-or-Stop Report Review Status

## Status

Status: human review accepted.

Created UTC: `{now}`

## Review Decision

The label-semantics task-redesign-or-stop report is accepted as the current decision checkpoint.

Accepted diagnosis: `{diagnosis}`

Accepted decision: `{decision}`

Accepted recommended next objective: `{recommended}`

Stop condition: {stop_condition}

## Scientific Meaning

The current global binary LOSO training path is paused as a final-performance path.

More model-side intervention is not authorized until a defensible task redesign spec is written and reviewed.

## Next Selected Step

Create a label-semantics task-redesign specification objective.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new training before redesign spec review
"""
review_md_path.write_text(review_md, encoding="utf-8")

objective = {
    "status": "objective_created",
    "created_utc": now,
    "source_review": str(review_md_path),
    "source_report": "docs/idare_label_semantics_task_redesign_or_stop_report.md",
    "scientific_question": (
        "Can we define one defensible label/task formulation that directly addresses "
        "the accepted label-semantics and representation-transfer bottleneck without "
        "cherry-picking or resuming broad model search?"
    ),
    "diagnosis_context": diagnosis,
    "authorized_work": [
        "read existing decision/candidate/evidence-gap reports",
        "write an implementation-ready task-redesign specification",
        "lock candidate task definitions, inclusion rules, metrics, and anti-cherry-picking guardrails",
        "choose exactly one primary next task formulation or recommend stop/archive",
        "no model training",
        "no broad hyperparameter search",
    ],
    "candidate_formulations_to_evaluate": [
        "ordinal_or_regression_affect_rating_task",
        "subject_relative_binary_top_bottom_q33",
        "restricted_high_confidence_label_task",
        "personalization_or_few_shot_adaptation_task",
        "stop_archive_current_global_binary_loso_path",
    ],
    "required_spec_sections": [
        "scientific claim",
        "label definition",
        "allowed samples and excluded samples",
        "train/validation/test protocol",
        "metrics and pass criteria",
        "leakage controls",
        "anti-cherry-picking rules",
        "minimal future run matrix if training is later authorized",
        "explicit stop/archive criteria",
    ],
    "pass_criteria": [
        "spec is complete enough to implement without guessing",
        "exactly one primary candidate is selected, or stop/archive is selected",
        "all inclusion/exclusion rules are pre-registered before training",
        "metrics align with the scientific claim",
        "direct full SupCon/DG training remains blocked",
        "broad hyperparameter search remains blocked",
        "final LOSO claim remains blocked",
    ],
    "next_allowed_step": "prepare_reviewed_label_semantics_task_redesign_spec_command",
    "blocked": review["blocked"],
}
objective_json_path.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

objective_md = f"""# I-DARE Label-Semantics Task-Redesign Spec Objective

## Status

Status: objective created; design/spec only; no training is authorized.

Created UTC: `{now}`

## Scientific Question

Can we define one defensible label/task formulation that directly addresses the accepted label-semantics and representation-transfer bottleneck without cherry-picking or resuming broad model search?

## Diagnosis Context

Accepted diagnosis: `{diagnosis}`

Accepted decision: `{decision}`

Stop condition: {stop_condition}

## Core Principle

Do not improve the model until the target is scientifically defensible.

The current global binary LOSO branch is paused as a final-performance path. The next work must define the task first.

## Authorized Work

- Read the existing decision report, candidate matrix, evidence-gap audit, and representation/label-semantics failure analysis.
- Create an implementation-ready task-redesign specification.
- Lock label definition, inclusion/exclusion rules, split protocol, metrics, and anti-cherry-picking guardrails.
- Select exactly one primary next formulation, or select stop/archive.
- No model training.
- No broad hyperparameter search.

## Candidate Formulations to Evaluate

| Candidate | Role in the spec |
|---|---|
| `ordinal_or_regression_affect_rating_task` | Primary redesign candidate if rating magnitude should be preserved. |
| `subject_relative_binary_top_bottom_q33` | Candidate if subject-relative binary semantics remain preferred. |
| `restricted_high_confidence_label_task` | Secondary diagnostic candidate only if inclusion rules can be locked before training. |
| `personalization_or_few_shot_adaptation_task` | Alternative scientific claim if pure LOSO is not the right target. |
| `stop_archive_current_global_binary_loso_path` | Required fallback if no defensible redesign is accepted. |

## Required Spec Sections

1. Scientific claim.
2. Label definition.
3. Allowed samples and excluded samples.
4. Train/validation/test protocol.
5. Metrics and pass criteria.
6. Leakage controls.
7. Anti-cherry-picking rules.
8. Minimal future run matrix if training is later authorized.
9. Explicit stop/archive criteria.

## Evidence That Must Be Addressed

- Best targeted pair-sampler candidate remained weak and unstable.
- Pair sampler was judged valid but not the primary failure mode.
- Prior report diagnosed a joint label-semantics and representation-transfer bottleneck.
- Current global binary LOSO task is not defensible for more model search.
- Subject-relative labeling alone was not sufficient.
- direct full SupCon/DG training remains blocked.
- broad hyperparameter search remains blocked.
- final LOSO claim remains blocked.

## Pass Criteria

- The spec is complete enough to implement without guessing.
- Exactly one primary candidate is selected, or stop/archive is selected.
- All inclusion/exclusion rules are pre-registered before training.
- Metrics align with the scientific claim.
- The spec explicitly blocks direct full SupCon/DG training until reviewed.
- The spec explicitly blocks broad hyperparameter search.
- The spec explicitly blocks final LOSO claim.

## Next Allowed Step

Prepare a reviewed label-semantics task-redesign spec command/script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new training before redesign spec review
"""
objective_md_path.write_text(objective_md, encoding="utf-8")

# Update project status JSON.
status = json.loads(status_path.read_text(encoding="utf-8"))
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "prepare_reviewed_label_semantics_task_redesign_spec_command"
status["current_idare_blocked_steps"] = review["blocked"]
status.setdefault("idare_protocol_events", []).extend([
    {
        "timestamp_utc": now,
        "type": "review",
        "name": "I-DARE label-semantics task-redesign-or-stop report review",
        "status": f"human review accepted; diagnosis={diagnosis}",
        "evidence": str(review_md_path),
        "next_allowed_step": "create/use label-semantics task-redesign spec objective",
        "blocked": review["blocked"],
    },
    {
        "timestamp_utc": now,
        "type": "objective",
        "name": "I-DARE label-semantics task-redesign spec objective",
        "status": "objective created; no training authorized",
        "evidence": str(objective_md_path),
        "next_allowed_step": "prepare reviewed task-redesign spec command",
        "blocked": review["blocked"],
    },
])
status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Update project status markdown.
status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Label-Semantics Task-Redesign Spec Objective

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE label-semantics task-redesign-or-stop report review | human review accepted; diagnosis=`{diagnosis}` | `docs/idare_label_semantics_task_redesign_or_stop_report_review_status.md` | Create/use label-semantics task-redesign spec objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE label-semantics task-redesign spec objective | design/spec objective created; no training authorized | `docs/idare_label_semantics_task_redesign_spec_objective.md` | Prepare reviewed task-redesign spec command/script. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- A label-semantics task-redesign spec objective is defined in `docs/idare_label_semantics_task_redesign_spec_objective.md`.
- Training remains blocked until this design/spec is reviewed.
"""
if "I-DARE Label-Semantics Task-Redesign Spec Objective" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_LABEL_SEMANTICS_TASK_REDESIGN_SPEC_OBJECTIVE_WRITTEN")
print(review_md_path)
print(review_json_path)
print(objective_md_path)
print(objective_json_path)
print("diagnosis=", diagnosis)
print("decision=", decision)
print("next_allowed_step=prepare_reviewed_label_semantics_task_redesign_spec_command")
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_paths = [
    Path("docs/idare_label_semantics_task_redesign_or_stop_report_review_status.json"),
    Path("docs/idare_label_semantics_task_redesign_spec_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

term_checks = {
    "docs/idare_label_semantics_task_redesign_or_stop_report_review_status.md": [
        "human review accepted",
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "final LOSO claim",
    ],
    "docs/idare_label_semantics_task_redesign_spec_objective.md": [
        "Scientific Question",
        "Candidate Formulations",
        "Required Spec Sections",
        "Pass Criteria",
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "final LOSO claim",
        "stop/archive",
    ],
}
for path, terms in term_checks.items():
    text = Path(path).read_text(encoding="utf-8")
    for term in terms:
        if term not in text:
            raise SystemExit(f"ERROR: missing term {term!r} in {path}")
    print("OK_TERMS:", path)

obj = json.loads(Path("docs/idare_label_semantics_task_redesign_spec_objective.json").read_text(encoding="utf-8"))
if obj.get("next_allowed_step") != "prepare_reviewed_label_semantics_task_redesign_spec_command":
    raise SystemExit("ERROR: wrong next_allowed_step")
if "direct full SupCon/DG training" not in obj.get("blocked", []):
    raise SystemExit("ERROR: missing blocked direct full SupCon/DG training")

print("next_allowed_step=", obj.get("next_allowed_step"))
print("ALL_LABEL_SEMANTICS_TASK_REDESIGN_SPEC_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "Status|Scientific Question|Core Principle|Authorized Work|Candidate Formulations|Required Spec Sections|Pass Criteria|Next Allowed Step" \
  docs/idare_label_semantics_task_redesign_spec_objective.md
grep -nE "Label-Semantics Task-Redesign Spec Objective|label-semantics task-redesign spec objective" \
  docs/project_status_current.md | tail -n 8
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_label_semantics_task_redesign_or_stop_report_review_status.md \
  docs/idare_label_semantics_task_redesign_or_stop_report_review_status.json \
  docs/idare_label_semantics_task_redesign_spec_objective.md \
  docs/idare_label_semantics_task_redesign_spec_objective.json \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE label semantics task redesign spec objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
