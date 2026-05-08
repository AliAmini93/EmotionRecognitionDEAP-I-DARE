#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_task_redesign_spec.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start label-semantics task redesign spec generation ====="
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
    import math
    from pathlib import Path
    import pandas as pd
except Exception as e:
    raise SystemExit(f"ERROR_IMPORTS: {e}")
print("OK_IMPORTS")
PY

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: repo is not clean; commit/stash before generating spec." >&2
  git status --short
  exit 2
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required objective/evidence inputs ====="
required=(
  docs/idare_label_semantics_task_redesign_spec_objective.md
  docs/idare_label_semantics_task_redesign_spec_objective.json
  docs/idare_label_semantics_task_redesign_or_stop_report_review_status.md
  docs/idare_label_semantics_task_redesign_or_stop_report_review_status.json
  docs/idare_label_semantics_task_redesign_or_stop_report.md
  docs/idare_label_semantics_task_redesign_or_stop_report.json
  docs/idare_label_semantics_task_redesign_or_stop_decision_matrix.csv
  docs/idare_label_semantics_task_candidate_matrix.csv
  docs/idare_label_semantics_evidence_gap_audit.csv
  docs/idare_label_semantics_cross_subject_audit.csv
  docs/idare_representation_transfer_failure_summary.csv
  docs/idare_objective_metric_alignment_summary.csv
  docs/idare_subject_relative_candidate_matrix.csv
  docs/idare_subject_relative_label_balance_summary.csv
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
  docs/idare_label_semantics_task_redesign_spec.md \
  docs/idare_label_semantics_task_redesign_spec.json \
  docs/idare_label_semantics_selected_task_definition.csv \
  docs/idare_label_semantics_task_redesign_guardrails.csv \
  docs/idare_label_semantics_task_redesign_metric_plan.csv \
  docs/idare_label_semantics_task_redesign_protocol_matrix.csv \
  docs/idare_label_semantics_task_redesign_future_run_matrix.csv \
  docs/idare_label_semantics_task_redesign_stop_criteria.csv
echo "OK_CLEAN_TARGET_OUTPUTS"
echo

echo "===== 4) generate implementation-ready task redesign spec ====="
"$PY" - <<'PY'
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

spec_md_path = DOCS / "idare_label_semantics_task_redesign_spec.md"
spec_json_path = DOCS / "idare_label_semantics_task_redesign_spec.json"
task_def_csv_path = DOCS / "idare_label_semantics_selected_task_definition.csv"
guardrails_csv_path = DOCS / "idare_label_semantics_task_redesign_guardrails.csv"
metric_csv_path = DOCS / "idare_label_semantics_task_redesign_metric_plan.csv"
protocol_csv_path = DOCS / "idare_label_semantics_task_redesign_protocol_matrix.csv"
future_run_csv_path = DOCS / "idare_label_semantics_task_redesign_future_run_matrix.csv"
stop_csv_path = DOCS / "idare_label_semantics_task_redesign_stop_criteria.csv"
status_json_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def read_csv(path):
    return pd.read_csv(Path(path))

def fmt(x, nd=4):
    if x is None:
        return "NA"
    try:
        if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
            return "NA"
        return f"{float(x):.{nd}f}"
    except Exception:
        return str(x)

def md_table(rows, columns):
    out = []
    out.append("| " + " | ".join(columns) + " |")
    out.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for row in rows:
        vals = []
        for c in columns:
            vals.append(str(row.get(c, "")).replace("\n", " ").replace("|", "\\|"))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)

def numeric_mean(df, col):
    if df.empty or col not in df.columns:
        return None
    s = pd.to_numeric(df[col], errors="coerce")
    if s.notna().sum() == 0:
        return None
    return float(s.mean())

def numeric_max(df, col):
    if df.empty or col not in df.columns:
        return None
    s = pd.to_numeric(df[col], errors="coerce")
    if s.notna().sum() == 0:
        return None
    return float(s.max())

objective = load_json(DOCS / "idare_label_semantics_task_redesign_spec_objective.json")
decision_report = load_json(DOCS / "idare_label_semantics_task_redesign_or_stop_report.json")
failure_report = load_json(DOCS / "idare_representation_or_label_semantics_failure_analysis_report.json")
candidate_df = read_csv(DOCS / "idare_label_semantics_task_candidate_matrix.csv")
gap_df = read_csv(DOCS / "idare_label_semantics_evidence_gap_audit.csv")
label_audit = read_csv(DOCS / "idare_label_semantics_cross_subject_audit.csv")
repr_summary = read_csv(DOCS / "idare_representation_transfer_failure_summary.csv")
metric_alignment = read_csv(DOCS / "idare_objective_metric_alignment_summary.csv")
subject_rel_candidates = read_csv(DOCS / "idare_subject_relative_candidate_matrix.csv")
subject_rel_balance = read_csv(DOCS / "idare_subject_relative_label_balance_summary.csv")

diagnosis_context = objective.get("diagnosis_context", decision_report.get("diagnosis"))
decision_context = decision_report.get("decision")
key = decision_report.get("key_indicators", {})
prev_key = failure_report.get("key_indicators", {})

# Select a primary formulation that directly addresses both failure axes:
# (1) subject-specific rating scale semantics and (2) loss of information from binary thresholding.
selected_formulation = "subject_relative_ordinal_affect_regression_v1"
selected_claim = (
    "Predict within-subject affect-rating order/percentile for held-out subjects, "
    "not global high/low affect by an absolute threshold."
)
recommended_next_objective = "label_semantics_redesigned_task_smoke_tests_objective"
status = "complete_pending_human_review"

# Core task definition.
task_def_rows = [
    {
        "field": "selected_primary_formulation",
        "value": selected_formulation,
        "locked": "yes",
        "rationale": "Combines ordinal/regression preservation of rating magnitude with subject-relative semantics.",
    },
    {
        "field": "scientific_claim",
        "value": selected_claim,
        "locked": "yes",
        "rationale": "Avoids unsupported global binary LOSO claim.",
    },
    {
        "field": "raw_label_source",
        "value": "raw valence_score and arousal_score ratings from cache/index files",
        "locked": "yes",
        "rationale": "Uses existing labels only; no new annotation or model-derived labels.",
    },
    {
        "field": "target_transform",
        "value": "per_subject_average_rank_percentile: rank(raw_rating within subject and task, ties averaged, mapped to [0,1]",
        "locked": "yes",
        "rationale": "Removes between-subject scale offsets while preserving within-subject ordering.",
    },
    {
        "field": "secondary_target",
        "value": "per_subject_z_score_rating for audit only, not the primary target",
        "locked": "yes",
        "rationale": "Useful to check scale sensitivity without changing primary target.",
    },
    {
        "field": "primary_tasks",
        "value": "valence and arousal evaluated separately",
        "locked": "yes",
        "rationale": "Keeps task-specific interpretation.",
    },
    {
        "field": "primary_split",
        "value": "existing 6-fold subject-heldout protocol; no subject overlap between train and validation",
        "locked": "yes",
        "rationale": "Preserves the most important leakage guardrail.",
    },
    {
        "field": "allowed_modalities_first_pass",
        "value": "EEG summary features and EMG signed_log1p features only, separately",
        "locked": "yes",
        "rationale": "No fusion and no architecture jump before redesigned-task smoke review.",
    },
    {
        "field": "training_status",
        "value": "not authorized by this spec",
        "locked": "yes",
        "rationale": "This document only defines the task; future training requires review and a new objective.",
    },
]
task_def = pd.DataFrame(task_def_rows)
task_def.to_csv(task_def_csv_path, index=False)

metric_rows = [
    {
        "metric": "spearman_rho",
        "role": "primary",
        "definition": "Spearman rank correlation between predicted continuous score and target rank percentile within each fold/task/modality.",
        "direction": "higher_better",
        "pass_rule_for_future_minimal_training": "mean across folds must be positive and exceed mean-baseline/permutation controls by a pre-registered margin.",
        "reason": "Directly matches ordinal/relative affect claim.",
    },
    {
        "metric": "mae_rank_percentile",
        "role": "secondary",
        "definition": "Mean absolute error on [0,1] rank-percentile target.",
        "direction": "lower_better",
        "pass_rule_for_future_minimal_training": "must improve over train-mean predictor.",
        "reason": "Interpretable regression error.",
    },
    {
        "metric": "rmse_rank_percentile",
        "role": "secondary",
        "definition": "Root mean squared error on [0,1] rank-percentile target.",
        "direction": "lower_better",
        "pass_rule_for_future_minimal_training": "must improve over train-mean predictor.",
        "reason": "Penalizes large rank errors.",
    },
    {
        "metric": "top_bottom_q33_balanced_accuracy",
        "role": "audit_only",
        "definition": "Evaluate predicted score as top-vs-bottom third after excluding middle third, with thresholds locked from target rank percentiles.",
        "direction": "higher_better",
        "pass_rule_for_future_minimal_training": "used only as a secondary bridge to old binary results; cannot be sole success criterion.",
        "reason": "Connects to earlier q33 analysis while avoiding global threshold semantics.",
    },
    {
        "metric": "per_subject_error_dispersion",
        "role": "fairness_stability_audit",
        "definition": "Distribution of rank-percentile errors by held-out subject.",
        "direction": "lower_dispersion_better",
        "pass_rule_for_future_minimal_training": "must report hard-subject concentration; no fold hiding.",
        "reason": "Keeps subject-variability diagnosis visible.",
    },
    {
        "metric": "permutation_control_spearman",
        "role": "negative_control",
        "definition": "Same pipeline with train labels shuffled within fold.",
        "direction": "near_zero_expected",
        "pass_rule_for_future_minimal_training": "must stay near zero; if not, leakage or metric bug suspected.",
        "reason": "Protects against false positive redesigned task.",
    },
]
pd.DataFrame(metric_rows).to_csv(metric_csv_path, index=False)

guardrail_rows = [
    {
        "guardrail": "no_global_binary_threshold",
        "rule": "Do not use raw rating >= midpoint as the primary label.",
        "why": "The accepted diagnosis says the current global binary LOSO task is not defensible for more model search.",
        "blocking": "yes",
    },
    {
        "guardrail": "no_model_training_in_spec_step",
        "rule": "This spec does not authorize training.",
        "why": "Task definition must be reviewed before implementation.",
        "blocking": "yes",
    },
    {
        "guardrail": "no_direct_full_supcon_dg_training",
        "rule": "direct full SupCon/DG training remains blocked.",
        "why": "SupCon/DG and pair-sampler ablations were not sufficient.",
        "blocking": "yes",
    },
    {
        "guardrail": "no_broad_hyperparameter_search",
        "rule": "broad hyperparameter search remains blocked.",
        "why": "Would obscure whether the task redesign fixed the root issue.",
        "blocking": "yes",
    },
    {
        "guardrail": "heldout_subject_isolation",
        "rule": "No subject overlap between train and validation folds; scalers fit train only.",
        "why": "Keeps LOSO leakage controls intact.",
        "blocking": "yes",
    },
    {
        "guardrail": "target_transform_usage",
        "rule": "Held-out labels may be transformed only to define evaluation targets; target statistics must not enter feature preprocessing, training inputs, sampler state, or model selection.",
        "why": "Allows subject-relative ground truth without leaking into the predictor.",
        "blocking": "yes",
    },
    {
        "guardrail": "anti_cherry_picking",
        "rule": "No fold/task/modality exclusion after seeing results; all exclusions must be declared before any training.",
        "why": "Avoids converting redesign into outcome selection.",
        "blocking": "yes",
    },
    {
        "guardrail": "final_loso_claim_blocked",
        "rule": "final LOSO claim remains blocked until redesigned-task results pass review.",
        "why": "This spec changes the scientific target.",
        "blocking": "yes",
    },
]
pd.DataFrame(guardrail_rows).to_csv(guardrails_csv_path, index=False)

protocol_rows = [
    {
        "component": "label_construction",
        "locked_rule": "For each subject and task, compute average rank of raw rating and convert to percentile in [0,1].",
        "leakage_control": "Labels only; no feature or model input gets held-out label statistics.",
        "review_required": "yes",
    },
    {
        "component": "split",
        "locked_rule": "Use the existing 6 subject-heldout folds.",
        "leakage_control": "Validation subjects are completely held out from training.",
        "review_required": "yes",
    },
    {
        "component": "preprocessing",
        "locked_rule": "Feature scalers fit on train fold only; apply to held-out fold.",
        "leakage_control": "No validation statistics in scaler.",
        "review_required": "yes",
    },
    {
        "component": "baseline",
        "locked_rule": "Train-mean predictor and shuffled-label negative control must be reported.",
        "leakage_control": "Controls are generated within each fold.",
        "review_required": "yes",
    },
    {
        "component": "primary_model_family_if_later_authorized",
        "locked_rule": "Start with minimal ridge/linear regression or a single small MLP regression; no SupCon/DG first.",
        "leakage_control": "No tuning on validation beyond pre-registered run matrix.",
        "review_required": "yes",
    },
    {
        "component": "success_claim",
        "locked_rule": "Success means evidence for within-subject affect-order prediction, not global high/low classification.",
        "leakage_control": "Claim text must match target definition.",
        "review_required": "yes",
    },
]
pd.DataFrame(protocol_rows).to_csv(protocol_csv_path, index=False)

# Future minimal run matrix if later authorized after smoke tests.
future_rows = []
run_id = 0
for model in ["mean_baseline_no_training", "ridge_regression_summary_features"]:
    for modality in ["EEG", "EMG"]:
        for task in ["valence", "arousal"]:
            for fold in range(1, 7):
                run_id += 1
                future_rows.append({
                    "planned_run_id": run_id,
                    "model": model,
                    "modality": modality,
                    "task": task,
                    "fold": fold,
                    "target": selected_formulation,
                    "authorized_now": "no",
                    "requires_prior_objective": "label_semantics_redesigned_task_smoke_tests_objective",
                    "notes": "Minimal future run only; no SupCon/DG or broad search.",
                })
pd.DataFrame(future_rows).to_csv(future_run_csv_path, index=False)

stop_rows = [
    {
        "condition": "spec_rejected",
        "action": "stop_archive_current_global_binary_loso_branch",
        "reason": "No defensible target was accepted.",
    },
    {
        "condition": "smoke_tests_fail_label_construction_or_leakage",
        "action": "fix_spec_or_stop_archive",
        "reason": "Cannot train on a target that fails construction/leakage sanity checks.",
    },
    {
        "condition": "future_minimal_regression_not_above_controls",
        "action": "stop_or_reframe_as_negative_result",
        "reason": "Would indicate even redesigned target has weak physiological signal under current features.",
    },
    {
        "condition": "future_success_only_in_one_fold_or_one_subject_cluster",
        "action": "run failure analysis_before_any_claim",
        "reason": "Avoids false positives from subject/fold idiosyncrasy.",
    },
    {
        "condition": "request_to_resume_direct_full_supcon_dg_training",
        "action": "block_until_redesigned_task_review_and_smoke_tests_pass",
        "reason": "Model-side search is not the accepted next scientific step.",
    },
]
pd.DataFrame(stop_rows).to_csv(stop_csv_path, index=False)

# Key evidence summary.
key_indicators = {
    "decision_report_diagnosis": decision_report.get("diagnosis"),
    "decision_report_decision": decision_report.get("decision"),
    "failure_report_diagnosis": failure_report.get("diagnosis"),
    "best_pair_sampler_candidate_mean_macro_f1": key.get("best_pair_sampler_candidate_mean_macro_f1", prev_key.get("best_pair_sampler_candidate_mean_macro_f1")),
    "best_pair_sampler_candidate_folds_under_050": key.get("best_pair_sampler_candidate_folds_under_050", prev_key.get("best_pair_sampler_candidate_folds_under_050")),
    "mean_label_entropy": key.get("mean_label_entropy", prev_key.get("mean_label_entropy")),
    "high_subject_rating_shift": key.get("high_subject_rating_shift", prev_key.get("high_subject_rating_shift")),
    "objective_alignment_weak": key.get("objective_alignment_weak", prev_key.get("objective_alignment_weak")),
    "max_abs_loss_embedding_corr_with_macro_f1": key.get("max_abs_loss_embedding_corr_with_macro_f1", prev_key.get("max_abs_loss_embedding_corr_with_macro_f1")),
}

spec = {
    "status": status,
    "created_utc": now,
    "source_objective": "docs/idare_label_semantics_task_redesign_spec_objective.md",
    "source_decision_report": "docs/idare_label_semantics_task_redesign_or_stop_report.md",
    "selected_primary_formulation": selected_formulation,
    "scientific_claim": selected_claim,
    "diagnosis_context": diagnosis_context,
    "decision_context": decision_context,
    "recommended_next_objective": recommended_next_objective,
    "next_allowed_step": "human_review_closeout_then_redesigned_task_smoke_tests_objective",
    "training_authorized": False,
    "final_loso_claim_authorized": False,
    "direct_full_supcon_dg_training_authorized": False,
    "broad_hyperparameter_search_authorized": False,
    "key_indicators": key_indicators,
    "outputs": {
        "spec_md": str(spec_md_path),
        "spec_json": str(spec_json_path),
        "selected_task_definition_csv": str(task_def_csv_path),
        "guardrails_csv": str(guardrails_csv_path),
        "metric_plan_csv": str(metric_csv_path),
        "protocol_matrix_csv": str(protocol_csv_path),
        "future_run_matrix_csv": str(future_run_csv_path),
        "stop_criteria_csv": str(stop_csv_path),
    },
    "blocked": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
        "new training before redesigned-task smoke-test review",
    ],
}
spec_json_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Markdown spec.
md = []
md.append("# I-DARE Label-Semantics Task Redesign Spec\n")
md.append("## Status\n")
md.append("Status: complete; pending human review; no training is authorized.\n")
md.append(f"Created UTC: `{now}`\n")
md.append("## Selected Primary Formulation\n")
md.append(f"Selected formulation: `{selected_formulation}`\n")
md.append(f"Scientific claim: {selected_claim}\n")
md.append("This replaces the current global binary LOSO target as the next candidate task. It does not validate a final claim yet.\n")
md.append("## Why This Formulation Was Selected\n")
md.append(
    "The accepted diagnosis says the current global binary LOSO task is not defensible for more model search. "
    "The previous interventions did not fail because pair sampling was invalid; they failed because the target semantics and representation transfer are jointly weak. "
    "A subject-relative ordinal/regression target is selected because it attacks both problems: it avoids global absolute thresholds and avoids collapsing continuous ratings into a brittle binary label.\n"
)
md.append("Key evidence:\n")
for k, v in key_indicators.items():
    md.append(f"- `{k}`: `{v}`\n")
md.append("## Locked Task Definition\n")
md.append(md_table(task_def_rows, ["field", "value", "locked", "rationale"]))
md.append("\n## Metric Plan\n")
md.append(md_table(metric_rows, ["metric", "role", "definition", "direction", "pass_rule_for_future_minimal_training"]))
md.append("\n## Protocol Matrix\n")
md.append(md_table(protocol_rows, ["component", "locked_rule", "leakage_control", "review_required"]))
md.append("\n## Guardrails\n")
md.append(md_table(guardrail_rows, ["guardrail", "rule", "why", "blocking"]))
md.append("\n## Future Minimal Run Matrix If Later Authorized\n")
md.append(
    "The future matrix is intentionally minimal and is not authorized by this spec. "
    "It exists only so the next objective can be reviewed without inventing runs later.\n"
)
md.append(f"- Planned rows: `{len(future_rows)}`\n")
md.append("- Methods: `mean_baseline_no_training`, `ridge_regression_summary_features`\n")
md.append("- Modalities: `EEG`, `EMG`\n")
md.append("- Tasks: `valence`, `arousal`\n")
md.append("- Folds: existing 1..6 subject-heldout folds\n")
md.append("## Stop / Archive Criteria\n")
md.append(md_table(stop_rows, ["condition", "action", "reason"]))
md.append("\n## Next Allowed Step\n")
md.append("Human review / closeout, then create a redesigned-task smoke-test objective.\n")
md.append("\nThe smoke-test objective must validate label construction, fold leakage, metric computation, baseline controls, and target distribution before any training objective.\n")
md.append("\n## Still Blocked\n")
for item in spec["blocked"]:
    md.append(f"- {item}\n")
spec_md_path.write_text("\n".join(md), encoding="utf-8")

# Update roadmap/status.
status_json = load_json(status_json_path)
status_json["last_updated_utc"] = now
status_json["current_idare_next_allowed_step"] = "human_review_closeout_then_redesigned_task_smoke_tests_objective"
status_json["current_idare_blocked_steps"] = spec["blocked"]
events = status_json.get("idare_protocol_events")
if not isinstance(events, list):
    events = []
status_json["idare_protocol_events"] = events
events.append({
    "timestamp_utc": now,
    "type": "spec",
    "name": "I-DARE label-semantics task redesign spec",
    "status": f"complete pending human review; selected={selected_formulation}",
    "evidence": str(spec_md_path),
    "next_allowed_step": "human review / closeout before redesigned-task smoke tests",
    "blocked": spec["blocked"],
})
status_json_path.write_text(json.dumps(status_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Label-Semantics Task Redesign Spec

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE label-semantics task redesign spec | complete pending human review; selected=`{selected_formulation}` | `docs/idare_label_semantics_task_redesign_spec.md` | Human review / closeout before redesigned-task smoke tests. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Selected primary formulation: `{selected_formulation}`.
- Recommended next objective is `{recommended_next_objective}` only after human review/closeout.
- No training is authorized by this spec.
"""
if "I-DARE Label-Semantics Task Redesign Spec" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_LABEL_SEMANTICS_TASK_REDESIGN_SPEC_WRITTEN")
print(spec_md_path)
print(spec_json_path)
print(task_def_csv_path)
print(guardrails_csv_path)
print(metric_csv_path)
print(protocol_csv_path)
print(future_run_csv_path)
print(stop_csv_path)
print("selected_primary_formulation=", selected_formulation)
print("recommended_next_objective=", recommended_next_objective)
print("future_run_rows=", len(future_rows))
PY
echo

echo "===== 5) validate generated outputs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_paths = [
    Path("docs/idare_label_semantics_task_redesign_spec.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

csv_expect = {
    "docs/idare_label_semantics_selected_task_definition.csv": 9,
    "docs/idare_label_semantics_task_redesign_guardrails.csv": 8,
    "docs/idare_label_semantics_task_redesign_metric_plan.csv": 6,
    "docs/idare_label_semantics_task_redesign_protocol_matrix.csv": 6,
    "docs/idare_label_semantics_task_redesign_future_run_matrix.csv": 48,
    "docs/idare_label_semantics_task_redesign_stop_criteria.csv": 5,
}
for p, min_rows in csv_expect.items():
    df = pd.read_csv(p)
    print(Path(p).name, "rows=", len(df))
    if len(df) < min_rows:
        raise SystemExit(f"ERROR: {p} has too few rows")

spec = json.loads(Path("docs/idare_label_semantics_task_redesign_spec.json").read_text(encoding="utf-8"))
if spec.get("selected_primary_formulation") != "subject_relative_ordinal_affect_regression_v1":
    raise SystemExit("ERROR: wrong selected_primary_formulation")
if spec.get("training_authorized") is not False:
    raise SystemExit("ERROR: training_authorized must be false")
if spec.get("direct_full_supcon_dg_training_authorized") is not False:
    raise SystemExit("ERROR: direct_full_supcon_dg_training_authorized must be false")
if spec.get("broad_hyperparameter_search_authorized") is not False:
    raise SystemExit("ERROR: broad_hyperparameter_search_authorized must be false")

text = Path("docs/idare_label_semantics_task_redesign_spec.md").read_text(encoding="utf-8")
for term in [
    "Selected Primary Formulation",
    "subject_relative_ordinal_affect_regression_v1",
    "Metric Plan",
    "Guardrails",
    "Stop / Archive Criteria",
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "final LOSO claim",
]:
    if term not in text:
        raise SystemExit(f"ERROR: missing term {term!r} in spec markdown")

print("selected_primary_formulation=", spec["selected_primary_formulation"])
print("recommended_next_objective=", spec["recommended_next_objective"])
print("ALL_LABEL_SEMANTICS_TASK_REDESIGN_SPEC_OUTPUTS_VALID")
PY

grep -nE "Status|Selected Primary Formulation|Why This Formulation|Locked Task Definition|Metric Plan|Protocol Matrix|Guardrails|Future Minimal Run Matrix|Stop / Archive Criteria|Next Allowed Step" \
  docs/idare_label_semantics_task_redesign_spec.md
grep -nE "Label-Semantics Task Redesign Spec|Selected primary formulation|Recommended next objective" docs/project_status_current.md | tail -n 10
echo

echo "===== 6) file list ====="
ls -lh \
  docs/idare_label_semantics_task_redesign_spec.md \
  docs/idare_label_semantics_task_redesign_spec.json \
  docs/idare_label_semantics_selected_task_definition.csv \
  docs/idare_label_semantics_task_redesign_guardrails.csv \
  docs/idare_label_semantics_task_redesign_metric_plan.csv \
  docs/idare_label_semantics_task_redesign_protocol_matrix.csv \
  docs/idare_label_semantics_task_redesign_future_run_matrix.csv \
  docs/idare_label_semantics_task_redesign_stop_criteria.csv \
  docs/project_status_current.json \
  docs/project_status_current.md
echo

echo "===== 7) status before commit ====="
git status --short --branch
echo

echo "===== 8) commit and push task redesign spec ====="
git add \
  docs/idare_label_semantics_task_redesign_spec.md \
  docs/idare_label_semantics_task_redesign_spec.json \
  docs/idare_label_semantics_selected_task_definition.csv \
  docs/idare_label_semantics_task_redesign_guardrails.csv \
  docs/idare_label_semantics_task_redesign_metric_plan.csv \
  docs/idare_label_semantics_task_redesign_protocol_matrix.csv \
  docs/idare_label_semantics_task_redesign_future_run_matrix.csv \
  docs/idare_label_semantics_task_redesign_stop_criteria.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "docs: add I-DARE label semantics task redesign spec"
git push origin main
echo

echo "===== 9) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
