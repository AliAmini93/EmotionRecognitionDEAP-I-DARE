#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_objective.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start minimal redesigned-task first-pass review + failure/confirmation objective ====="
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

echo "===== 2) check required first-pass evidence ====="
required=(
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.md
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.json
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_run_matrix.csv
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_guardrails.csv
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.md
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.json
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_runs.csv
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_predictions.csv
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_metric_summary.csv
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_subject_error_summary.csv
  docs/idare_label_semantics_task_redesign_metric_plan.csv
  docs/idare_label_semantics_task_redesign_protocol_matrix.csv
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

echo "===== 3) create first-pass review closeout + failure/confirmation analysis objective ====="
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

first_report_md = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_report.md"
first_report_json = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_report.json"
runs_csv = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_runs.csv"
pred_csv = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_predictions.csv"
metric_csv = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_metric_summary.csv"
subject_csv = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_subject_error_summary.csv"

review_md = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_review_status.md"
review_json = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_review_status.json"
objective_md = DOCS / "idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.md"
objective_json = DOCS / "idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.json"

status_json_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

report = read_json(first_report_json)
runs = pd.read_csv(runs_csv)
metric = pd.read_csv(metric_csv)
subjects = pd.read_csv(subject_csv)

diagnosis = report.get("diagnosis")
expected = "minimal_redesigned_task_first_pass_mixed_signal"
if diagnosis != expected:
    raise SystemExit(f"ERROR: expected diagnosis {expected!r}, got {diagnosis!r}")

recommended = report.get("recommended_next_objective")
expected_next = "label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective"
if recommended != expected_next:
    raise SystemExit(f"ERROR: expected recommended_next_objective {expected_next!r}, got {recommended!r}")

if int(report.get("n_runs", -1)) != 48 or len(runs) != 48:
    raise SystemExit("ERROR: first-pass run count is not 48")
if int(report.get("n_predictions", -1)) <= 0:
    raise SystemExit("ERROR: report n_predictions invalid")
if "ridge_regression_summary_features" not in set(runs["model"].astype(str)):
    raise SystemExit("ERROR: ridge rows missing")
if "mean_baseline_no_training" not in set(runs["model"].astype(str)):
    raise SystemExit("ERROR: mean baseline rows missing")

key = report.get("key_indicators", {})
ridge_best_spearman = key.get("ridge_best_spearman")
ridge_cells_over_010 = key.get("ridge_cells_over_010_spearman")
ridge_cells_positive = key.get("ridge_cells_positive_spearman")
mae_improved = key.get("ridge_cells_mae_improved_vs_mean_baseline")
perm_abs = key.get("permutation_abs_max_mean_spearman")

blocked = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change",
    "deep neural training for redesigned task",
    "unregistered feature engineering",
    "confirmation training before this analysis closes",
]

review = {
    "status": "human_review_accepted",
    "created_utc": now,
    "reviewed_report": str(first_report_md),
    "accepted_diagnosis": diagnosis,
    "accepted_recommended_next_objective": recommended,
    "accepted_key_indicators": key,
    "interpretation": (
        "First pass is mixed: a few positive Spearman folds exist, but no cell exceeds the >0.10 mean-Spearman threshold, "
        "MAE does not beat mean baseline, and evidence is not strong enough for confirmation without read-only analysis."
    ),
    "next_selected_step": "create_failure_or_confirmation_analysis_objective",
    "training_authorized": False,
    "blocked": blocked,
}
write_json(review_json, review)

review_text = f"""# I-DARE Minimal Redesigned-Task First-Pass Review Status

## Status

Status: human review accepted.

Created UTC: `{now}`

## Review Decision

The minimal redesigned-task first-pass report is accepted as mixed evidence.

Accepted diagnosis: `{diagnosis}`

Accepted recommended next objective: `{recommended}`

## Accepted Key Indicators

- ridge_best_spearman: `{ridge_best_spearman}`
- ridge_cells_over_010_spearman: `{ridge_cells_over_010}`
- ridge_cells_positive_spearman: `{ridge_cells_positive}`
- ridge_cells_mae_improved_vs_mean_baseline: `{mae_improved}`
- permutation_abs_max_mean_spearman: `{perm_abs}`

## Scientific Interpretation

The first pass is neither a clean failure nor a clean confirmation.

It is not strong enough to authorize confirmation training because no ridge cell passed the >0.10 mean-Spearman screen and MAE did not improve over the mean baseline.

It is also not empty, because some fold/task cells had positive Spearman and permutation control stayed near zero.

Therefore the next step must be read-only failure-or-confirmation analysis.

## Next Selected Step

Create a read-only failure-or-confirmation analysis objective.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- deep neural training for redesigned task
- unregistered feature engineering
- confirmation training before this analysis closes
"""
review_md.write_text(review_text, encoding="utf-8")

objective = {
    "status": "objective_created",
    "created_utc": now,
    "source_review": str(review_md),
    "source_first_pass_report": str(first_report_md),
    "source_runs": str(runs_csv),
    "source_predictions": str(pred_csv),
    "source_metric_summary": str(metric_csv),
    "source_subject_error_summary": str(subject_csv),
    "scientific_question": (
        "Should the minimal redesigned-task first-pass result be interpreted as a real but weak signal worth confirming, "
        "or as another failure mode requiring redesign/stop?"
    ),
    "authorized_work": [
        "read-only fold/task/cell instability analysis",
        "compare ridge cells against mean baseline and permutation control",
        "identify whether positive Spearman is concentrated in specific modality/task/folds",
        "audit whether MAE/RMSE worsening invalidates the small positive Spearman signal",
        "audit hard-subject concentration from subject-error summary",
        "produce a decision matrix with one of: confirmation objective, targeted metric/debug analysis, or stop/archive",
    ],
    "not_authorized": blocked,
    "required_analysis_questions": [
        "Are positive Spearman values robust across folds or driven by one/two folds?",
        "Does any modality/task cell beat mean baseline on both Spearman and MAE/RMSE?",
        "Is q33 balanced accuracy consistent with ordinal Spearman or just noise around 0.5?",
        "Does permutation control remain near zero for every candidate cell?",
        "Are errors concentrated in particular held-out subjects?",
        "Is the redesigned task promising enough for a confirmation run, or should it stop?",
    ],
    "expected_outputs": [
        "docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_report.md",
        "docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_report.json",
        "docs/idare_label_semantics_minimal_redesigned_task_cell_decision_matrix.csv",
        "docs/idare_label_semantics_minimal_redesigned_task_fold_instability_audit.csv",
        "docs/idare_label_semantics_minimal_redesigned_task_subject_error_audit.csv",
        "docs/idare_label_semantics_minimal_redesigned_task_metric_conflict_audit.csv",
    ],
    "pass_criteria": [
        "uses only committed first-pass outputs",
        "does not run new training",
        "explains why mixed signal is or is not confirmable",
        "selects exactly one next objective",
        "keeps SupCon/DG, fusion, broad search, and final claims blocked",
    ],
    "next_allowed_step": "prepare_reviewed_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_command",
    "training_authorized": False,
    "blocked": blocked,
}
write_json(objective_json, objective)

objective_text = f"""# I-DARE Minimal Redesigned-Task Failure-or-Confirmation Analysis Objective

## Status

Status: objective created; read-only analysis only; no training is authorized.

Created UTC: `{now}`

## Scientific Question

Should the minimal redesigned-task first-pass result be interpreted as a real but weak signal worth confirming, or as another failure mode requiring redesign/stop?

## Triggering Evidence

- First-pass diagnosis: `{diagnosis}`
- Recommended next objective from first pass: `{recommended}`
- ridge_best_spearman: `{ridge_best_spearman}`
- ridge_cells_over_010_spearman: `{ridge_cells_over_010}`
- ridge_cells_positive_spearman: `{ridge_cells_positive}`
- ridge_cells_mae_improved_vs_mean_baseline: `{mae_improved}`
- permutation_abs_max_mean_spearman: `{perm_abs}`

## Authorized Work

- Read-only fold/task/cell instability analysis.
- Compare ridge cells against mean baseline and permutation control.
- Identify whether positive Spearman is concentrated in specific modality/task/folds.
- Audit whether MAE/RMSE worsening invalidates the small positive Spearman signal.
- Audit hard-subject concentration from subject-error summary.
- Produce a decision matrix with one of: confirmation objective, targeted metric/debug analysis, or stop/archive.

## Required Analysis Questions

1. Are positive Spearman values robust across folds or driven by one/two folds?
2. Does any modality/task cell beat mean baseline on both Spearman and MAE/RMSE?
3. Is q33 balanced accuracy consistent with ordinal Spearman or just noise around 0.5?
4. Does permutation control remain near zero for every candidate cell?
5. Are errors concentrated in particular held-out subjects?
6. Is the redesigned task promising enough for a confirmation run, or should it stop?

## Expected Outputs

- `docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_report.md`
- `docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_report.json`
- `docs/idare_label_semantics_minimal_redesigned_task_cell_decision_matrix.csv`
- `docs/idare_label_semantics_minimal_redesigned_task_fold_instability_audit.csv`
- `docs/idare_label_semantics_minimal_redesigned_task_subject_error_audit.csv`
- `docs/idare_label_semantics_minimal_redesigned_task_metric_conflict_audit.csv`

## Pass Criteria

- Uses only committed first-pass outputs.
- Does not run new training.
- Explains why mixed signal is or is not confirmable.
- Selects exactly one next objective.
- Keeps SupCon/DG, fusion, broad search, and final claims blocked.

## Next Allowed Step

Prepare a reviewed read-only failure-or-confirmation analysis command/script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- deep neural training for redesigned task
- unregistered feature engineering
- confirmation training before this analysis closes
"""
objective_md.write_text(objective_text, encoding="utf-8")

status = read_json(status_json_path)
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "prepare_reviewed_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_command"
status["current_idare_blocked_steps"] = blocked
events = status.get("idare_protocol_events")
if not isinstance(events, list):
    events = []
status["idare_protocol_events"] = events
events.extend([
    {
        "timestamp_utc": now,
        "type": "review",
        "name": "I-DARE minimal redesigned-task first-pass review",
        "status": f"human review accepted; diagnosis={diagnosis}",
        "evidence": str(review_md),
        "next_allowed_step": "create/use failure-or-confirmation analysis objective",
        "blocked": blocked,
    },
    {
        "timestamp_utc": now,
        "type": "objective",
        "name": "I-DARE minimal redesigned-task failure-or-confirmation analysis objective",
        "status": "read-only objective created; no training authorized",
        "evidence": str(objective_md),
        "next_allowed_step": "prepare reviewed read-only analysis command",
        "blocked": blocked,
    },
])
write_json(status_json_path, status)

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Minimal Redesigned-Task Failure-or-Confirmation Objective

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE minimal redesigned-task first-pass review | human review accepted; diagnosis=`{diagnosis}` | `docs/idare_label_semantics_minimal_redesigned_task_first_pass_review_status.md` | Create/use failure-or-confirmation analysis objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |
| I-DARE minimal redesigned-task failure-or-confirmation analysis objective | read-only objective created; no training authorized | `docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.md` | Prepare reviewed read-only analysis command/script. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- The first-pass result is mixed, not confirmatory.
- Next work is read-only analysis before any confirmation, failure, redesign, or archive decision.
"""
if "I-DARE Minimal Redesigned-Task Failure-or-Confirmation Objective" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_FAILURE_OR_CONFIRMATION_OBJECTIVE_WRITTEN")
print(review_md)
print(review_json)
print(objective_md)
print(objective_json)
print("accepted_diagnosis=", diagnosis)
print("ridge_best_spearman=", ridge_best_spearman)
print("ridge_cells_over_010_spearman=", ridge_cells_over_010)
print("ridge_cells_positive_spearman=", ridge_cells_positive)
print("ridge_cells_mae_improved_vs_mean_baseline=", mae_improved)
print("next_allowed_step=prepare_reviewed_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_command")
PY
echo

echo "===== 4) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path

json_paths = [
    Path("docs/idare_label_semantics_minimal_redesigned_task_first_pass_review_status.json"),
    Path("docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

term_checks = {
    "docs/idare_label_semantics_minimal_redesigned_task_first_pass_review_status.md": [
        "human review accepted",
        "minimal_redesigned_task_first_pass_mixed_signal",
        "direct full SupCon/DG training",
        "confirmation training before this analysis closes",
    ],
    "docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.md": [
        "Scientific Question",
        "Authorized Work",
        "Required Analysis Questions",
        "Expected Outputs",
        "Pass Criteria",
        "direct full SupCon/DG training",
        "final LOSO claim",
    ],
}
for path, terms in term_checks.items():
    text = Path(path).read_text(encoding="utf-8")
    for term in terms:
        if term not in text:
            raise SystemExit(f"ERROR: missing term {term!r} in {path}")
    print("OK_TERMS:", path)

obj = json.loads(Path("docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.json").read_text(encoding="utf-8"))
if obj.get("next_allowed_step") != "prepare_reviewed_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_command":
    raise SystemExit("ERROR: wrong next_allowed_step")
if obj.get("training_authorized") is not False:
    raise SystemExit("ERROR: training_authorized must be false")
print("next_allowed_step=", obj["next_allowed_step"])
print("ALL_FAILURE_OR_CONFIRMATION_OBJECTIVE_OUTPUTS_VALID")
PY

grep -nE "Status|Scientific Question|Triggering Evidence|Authorized Work|Required Analysis Questions|Expected Outputs|Pass Criteria|Next Allowed Step" \
  docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.md
grep -nE "Minimal Redesigned-Task Failure-or-Confirmation|first-pass result is mixed|read-only analysis" docs/project_status_current.md | tail -n 10
echo

echo "===== 5) diff stat ====="
git diff --stat
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push ====="
git add \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_review_status.md \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_review_status.json \
  docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.md \
  docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.json \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE redesigned task failure confirmation objective"
git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
