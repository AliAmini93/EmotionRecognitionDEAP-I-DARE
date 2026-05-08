#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_task_redesign_or_stop_objective.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start representation/label-semantics review + task-redesign/stop objective ====="
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
except Exception as e:
    raise SystemExit(f"ERROR_IMPORTS: {e}")
print("OK_IMPORTS")
PY

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: repo is not clean; commit/stash before generating objective." >&2
  git status --short
  exit 2
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required evidence docs ====="
required=(
  docs/idare_representation_or_label_semantics_failure_analysis_objective.md
  docs/idare_representation_or_label_semantics_failure_analysis_objective.json
  docs/idare_representation_or_label_semantics_failure_analysis_report.md
  docs/idare_representation_or_label_semantics_failure_analysis_report.json
  docs/idare_label_semantics_cross_subject_audit.csv
  docs/idare_representation_transfer_failure_summary.csv
  docs/idare_task_formulation_failure_decision_matrix.csv
  docs/idare_objective_metric_alignment_summary.csv
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

echo "===== 3) create review closeout + label-semantics task-redesign/stop objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

report_path = DOCS / "idare_representation_or_label_semantics_failure_analysis_report.json"
report_md_path = DOCS / "idare_representation_or_label_semantics_failure_analysis_report.md"
review_md_path = DOCS / "idare_representation_or_label_semantics_failure_analysis_review_status.md"
review_json_path = DOCS / "idare_representation_or_label_semantics_failure_analysis_review_status.json"
objective_md_path = DOCS / "idare_label_semantics_task_redesign_or_stop_objective.md"
objective_json_path = DOCS / "idare_label_semantics_task_redesign_or_stop_objective.json"
status_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

report = json.loads(report_path.read_text(encoding="utf-8"))
diagnosis = report.get("diagnosis", "label_semantics_and_representation_transfer_joint_bottleneck")
recommended = report.get("recommended_next_objective", "label_semantics_task_redesign_or_stop_objective")
key_indicators = report.get("key_indicators", {})

blocked = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change",
    "new model training before task-redesign/stop review",
]

review = {
    "status": "human_review_accepted",
    "created_utc": now,
    "reviewed_report": str(report_md_path),
    "accepted_diagnosis": diagnosis,
    "accepted_recommended_next_objective": recommended,
    "decision": "Proceed to a read-only label-semantics task-redesign-or-stop objective before any further training.",
    "rationale": [
        "SupCon/DG pair sampler mechanics were validated but not sufficient.",
        "The latest report identified a joint bottleneck in label semantics and representation transfer.",
        "The next scientific decision is whether the current binary affect task should be redesigned, narrowed, paused, or stopped.",
    ],
    "next_allowed_step": "create/use label-semantics task-redesign-or-stop objective",
    "blocked_steps": blocked,
}
review_json_path.write_text(json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

review_md = f"""# I-DARE Representation or Label-Semantics Failure Analysis Review Status

## Status

Status: human review accepted.

Created UTC: `{now}`

## Review Decision

The read-only representation/label-semantics failure analysis is accepted.

Accepted diagnosis: `{diagnosis}`

Accepted recommended next objective: `{recommended}`

## Evidence Accepted

- `docs/idare_representation_or_label_semantics_failure_analysis_report.md`
- `docs/idare_label_semantics_cross_subject_audit.csv`
- `docs/idare_representation_transfer_failure_summary.csv`
- `docs/idare_task_formulation_failure_decision_matrix.csv`
- `docs/idare_objective_metric_alignment_summary.csv`

## Key Accepted Indicators

- best pair-sampler candidate mean macro-F1: `{key_indicators.get("best_pair_sampler_candidate_mean_macro_f1")}`
- best pair-sampler candidate folds under 0.50 macro-F1: `{key_indicators.get("best_pair_sampler_candidate_folds_under_050")}`
- high subject rating shift: `{key_indicators.get("high_subject_rating_shift")}`
- low entropy problem: `{key_indicators.get("low_entropy_problem")}`
- objective alignment weak: `{key_indicators.get("objective_alignment_weak")}`

## Scientific Interpretation

The failure is no longer treated as primarily a SupCon pair/sampler implementation issue. The current evidence points to a deeper problem: the label semantics and subject transfer assumptions may not support the current binary cross-subject task well enough.

## Next Selected Step

Create/use a read-only label-semantics task-redesign-or-stop objective.

## Blocked

The following remain blocked:

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new model training before task-redesign/stop review
"""
review_md_path.write_text(review_md, encoding="utf-8")

objective = {
    "status": "objective_created",
    "created_utc": now,
    "objective_name": "I-DARE label-semantics task-redesign-or-stop objective",
    "triggering_review": str(review_md_path),
    "triggering_diagnosis": diagnosis,
    "scientific_question": (
        "Given the joint label-semantics and representation-transfer bottleneck, should the current I-DARE binary "
        "affect-recognition task be redesigned, narrowed, paused, or stopped before any further training?"
    ),
    "authorized_work": [
        "Read existing reports and committed CSV/JSON outputs only.",
        "Compare feasible task alternatives against leakage, subject validity, class balance, and scientific usefulness.",
        "Create a decision matrix covering stop/pause, subject-relative task, within-subject/personalization task, ordinal/regression task, and restricted-cohort task.",
        "Define what evidence would be required before any future training is allowed.",
        "Recommend exactly one next objective: stop/archive, task redesign implementation spec, or narrow validation diagnostic.",
    ],
    "explicitly_not_authorized": blocked,
    "required_analysis_questions": [
        "Does the current binary global-label task have enough semantic consistency for a final cross-subject claim?",
        "Would a subject-relative binary task be scientifically meaningful, or did previous results already rule it out as a primary fix?",
        "Would ordinal/regression modeling preserve more label semantics than binary discretization?",
        "Would a restricted-cohort or high-confidence-label task be defensible without cherry-picking?",
        "Would personalization/few-shot adaptation be more scientifically honest than LOSO-only generalization?",
        "What result would justify stopping or parking the current line of experiments?",
    ],
    "expected_outputs": {
        "report_md": "docs/idare_label_semantics_task_redesign_or_stop_report.md",
        "report_json": "docs/idare_label_semantics_task_redesign_or_stop_report.json",
        "decision_matrix_csv": "docs/idare_label_semantics_task_redesign_or_stop_decision_matrix.csv",
        "task_candidate_matrix_csv": "docs/idare_label_semantics_task_candidate_matrix.csv",
        "evidence_gap_audit_csv": "docs/idare_label_semantics_evidence_gap_audit.csv",
    },
    "pass_criteria": [
        "No new model training is run.",
        "The report explicitly distinguishes redesign, stop, pause, and narrow-validation options.",
        "The recommendation is falsifiable and includes blocked next steps.",
        "The report prevents another broad hyperparameter or SupCon/DG run without a task-level decision.",
    ],
    "next_allowed_step": "prepare_reviewed_label_semantics_task_redesign_or_stop_report_command",
}
objective_json_path.write_text(json.dumps(objective, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

objective_md = f"""# I-DARE Label-Semantics Task-Redesign-or-Stop Objective

## Status

Status: objective created; read-only decision analysis only.

Created UTC: `{now}`

## Scientific Question

Given the diagnosis `{diagnosis}`, should the current I-DARE binary affect-recognition task be redesigned, narrowed, paused, or stopped before any further training?

## Core Principle

No more model-side fixes should be tried until the task-level assumptions are explicitly reviewed.

The problem may not be "SupCon not strong enough." The problem may be that the current labels, subject variability, and LOSO claim do not define a stable enough supervised target.

## Authorized Work

This objective authorizes only read-only decision analysis:

1. Review existing reports and committed output tables.
2. Compare task-level alternatives.
3. Identify evidence gaps.
4. Recommend one next objective only after a task-level decision.

## Candidate Decisions to Evaluate

| Candidate | Meaning |
|---|---|
| Stop/archive current path | Conclude current task is not scientifically defensible enough for continued training. |
| Pause and redesign labels | Keep data and pipeline, but redefine the target before new training. |
| Subject-relative binary task | Use per-subject top/bottom affect labels only if evidence supports semantic validity. |
| Ordinal/regression task | Preserve rating information instead of binary discretization. |
| Restricted high-confidence cohort/task | Use only subjects/items with sufficient rating spread and label confidence, with anti-cherry-picking guardrails. |
| Personalization/few-shot adaptation | Treat subject variability as the central scientific problem rather than a nuisance. |

## Required Analysis Questions

- Does the current global binary task have enough cross-subject semantic consistency?
- Did subject-relative labels fail because the idea is wrong, or because the representation/training setup was too weak?
- Is LOSO-only final performance still a valid scientific target?
- Would ordinal/regression labels better match the DEAP-style affect scores?
- Is there a defensible restricted-cohort task that avoids cherry-picking?
- What condition would make us stop this experimental branch?

## Expected Outputs

- `docs/idare_label_semantics_task_redesign_or_stop_report.md`
- `docs/idare_label_semantics_task_redesign_or_stop_report.json`
- `docs/idare_label_semantics_task_redesign_or_stop_decision_matrix.csv`
- `docs/idare_label_semantics_task_candidate_matrix.csv`
- `docs/idare_label_semantics_evidence_gap_audit.csv`

## Pass Criteria

- No new training is run.
- The report clearly distinguishes stop, pause, redesign, and narrow-validation options.
- Any recommended continuation must explain exactly what assumption it tests.
- Direct full SupCon/DG training remains blocked.
- Broad hyperparameter search remains blocked.
- EEG+EMG fusion and final LOSO claim remain blocked.

## Next Allowed Step

Prepare reviewed read-only label-semantics task-redesign-or-stop report command.
"""
objective_md_path.write_text(objective_md, encoding="utf-8")

# Update project status JSON.
status = json.loads(status_path.read_text(encoding="utf-8"))
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "prepare_reviewed_label_semantics_task_redesign_or_stop_report_command"
status["current_idare_blocked_steps"] = blocked
status.setdefault("idare_protocol_events", []).append({
    "timestamp_utc": now,
    "type": "review_closeout",
    "name": "I-DARE representation or label-semantics failure-analysis review",
    "status": f"human review accepted; diagnosis={diagnosis}",
    "evidence": str(review_md_path),
    "next_allowed_step": "create/use label-semantics task-redesign-or-stop objective",
    "blocked": blocked,
})
status.setdefault("idare_protocol_events", []).append({
    "timestamp_utc": now,
    "type": "objective",
    "name": "I-DARE label-semantics task-redesign-or-stop objective",
    "status": "read-only objective created; no training authorized",
    "evidence": str(objective_md_path),
    "next_allowed_step": "prepare reviewed read-only decision-analysis command",
    "blocked": blocked,
})
status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Update project status Markdown.
status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Representation/Label-Semantics Review and Task-Redesign-or-Stop Objective

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE representation or label-semantics failure-analysis review | human review accepted; diagnosis=`{diagnosis}` | `docs/idare_representation_or_label_semantics_failure_analysis_review_status.md` | Create/use label-semantics task-redesign-or-stop objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE label-semantics task-redesign-or-stop objective | read-only decision-analysis objective created; no training authorized | `docs/idare_label_semantics_task_redesign_or_stop_objective.md` | Prepare reviewed read-only report command/script. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Human review of the representation/label-semantics failure analysis is frozen in `docs/idare_representation_or_label_semantics_failure_analysis_review_status.md`.
- A label-semantics task-redesign-or-stop objective is defined in `docs/idare_label_semantics_task_redesign_or_stop_objective.md`.
"""
if "I-DARE Representation/Label-Semantics Review and Task-Redesign-or-Stop Objective" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_LABEL_SEMANTICS_TASK_REDESIGN_OR_STOP_OBJECTIVE_WRITTEN")
print(review_md_path)
print(review_json_path)
print(objective_md_path)
print(objective_json_path)
print("diagnosis=", diagnosis)
print("next_allowed_step=", objective["next_allowed_step"])
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path

paths = [
    Path("docs/idare_representation_or_label_semantics_failure_analysis_review_status.json"),
    Path("docs/idare_label_semantics_task_redesign_or_stop_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in paths:
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

grep -nE "Status|Scientific Question|Authorized Work|Candidate Decisions|Pass Criteria|Next Allowed Step" \
  docs/idare_label_semantics_task_redesign_or_stop_objective.md
grep -nE "label-semantics task-redesign-or-stop|representation or label-semantics failure-analysis review" \
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
