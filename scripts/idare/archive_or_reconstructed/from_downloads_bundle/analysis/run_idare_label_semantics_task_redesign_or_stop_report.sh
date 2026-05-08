#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_task_redesign_or_stop_report.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start label-semantics task-redesign-or-stop report ====="
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
    import csv
    import math
    from pathlib import Path
    import pandas as pd
except Exception as e:
    raise SystemExit(f"ERROR_IMPORTS: {e}")
print("OK_IMPORTS")
PY

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: repo is not clean; commit/stash before generating report." >&2
  git status --short
  exit 2
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required committed inputs ====="
required=(
  docs/idare_label_semantics_task_redesign_or_stop_objective.md
  docs/idare_label_semantics_task_redesign_or_stop_objective.json
  docs/idare_representation_or_label_semantics_failure_analysis_review_status.md
  docs/idare_representation_or_label_semantics_failure_analysis_review_status.json
  docs/idare_representation_or_label_semantics_failure_analysis_report.md
  docs/idare_representation_or_label_semantics_failure_analysis_report.json
  docs/idare_label_semantics_cross_subject_audit.csv
  docs/idare_representation_transfer_failure_summary.csv
  docs/idare_task_formulation_failure_decision_matrix.csv
  docs/idare_objective_metric_alignment_summary.csv
  docs/idare_supcon_dg_pair_sampler_failure_analysis_report.json
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv
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
  docs/idare_label_semantics_task_redesign_or_stop_report.md \
  docs/idare_label_semantics_task_redesign_or_stop_report.json \
  docs/idare_label_semantics_task_redesign_or_stop_decision_matrix.csv \
  docs/idare_label_semantics_task_candidate_matrix.csv \
  docs/idare_label_semantics_evidence_gap_audit.csv
echo "OK_CLEAN_TARGET_OUTPUTS"
echo

echo "===== 4) generate read-only task-redesign-or-stop report ====="
"$PY" - <<'PY'
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DOCS = Path("docs")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

report_json_path = DOCS / "idare_label_semantics_task_redesign_or_stop_report.json"
report_md_path = DOCS / "idare_label_semantics_task_redesign_or_stop_report.md"
decision_csv_path = DOCS / "idare_label_semantics_task_redesign_or_stop_decision_matrix.csv"
candidate_csv_path = DOCS / "idare_label_semantics_task_candidate_matrix.csv"
gap_csv_path = DOCS / "idare_label_semantics_evidence_gap_audit.csv"
status_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def safe_read_csv(path):
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p)
    except Exception as e:
        raise SystemExit(f"ERROR_READ_CSV {path}: {e}")

def col(df, name, default=None):
    if name in df.columns:
        return df[name]
    return pd.Series([default] * len(df))

def mean_numeric(df, column):
    if df.empty or column not in df.columns:
        return None
    s = pd.to_numeric(df[column], errors="coerce")
    if s.notna().sum() == 0:
        return None
    return float(s.mean())

def max_numeric(df, column):
    if df.empty or column not in df.columns:
        return None
    s = pd.to_numeric(df[column], errors="coerce")
    if s.notna().sum() == 0:
        return None
    return float(s.max())

def min_numeric(df, column):
    if df.empty or column not in df.columns:
        return None
    s = pd.to_numeric(df[column], errors="coerce")
    if s.notna().sum() == 0:
        return None
    return float(s.min())

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
            v = row.get(c, "")
            s = str(v).replace("\n", " ").replace("|", "\\|")
            vals.append(s)
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)

objective = load_json(DOCS / "idare_label_semantics_task_redesign_or_stop_objective.json")
prev_report = load_json(DOCS / "idare_representation_or_label_semantics_failure_analysis_report.json")
pair_report = load_json(DOCS / "idare_supcon_dg_pair_sampler_failure_analysis_report.json")

label_audit = safe_read_csv(DOCS / "idare_label_semantics_cross_subject_audit.csv")
repr_summary = safe_read_csv(DOCS / "idare_representation_transfer_failure_summary.csv")
task_matrix_prev = safe_read_csv(DOCS / "idare_task_formulation_failure_decision_matrix.csv")
metric_alignment = safe_read_csv(DOCS / "idare_objective_metric_alignment_summary.csv")
pair_candidate = safe_read_csv(DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv")
pair_method_task = safe_read_csv(DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv")
subject_rel_candidates = safe_read_csv(DOCS / "idare_subject_relative_candidate_matrix.csv")
subject_rel_balance = safe_read_csv(DOCS / "idare_subject_relative_label_balance_summary.csv")

key = prev_report.get("key_indicators", {})
diagnosis_prev = prev_report.get("diagnosis", "label_semantics_and_representation_transfer_joint_bottleneck")

# Evidence signals.
best_pair_macro = key.get("best_pair_sampler_candidate_mean_macro_f1")
best_pair_under_050 = key.get("best_pair_sampler_candidate_folds_under_050")
mean_label_entropy = key.get("mean_label_entropy")
high_subject_rating_shift = bool(key.get("high_subject_rating_shift", False))
low_entropy_problem = bool(key.get("low_entropy_problem", False))
objective_alignment_weak = bool(key.get("objective_alignment_weak", False))
max_abs_corr = key.get("max_abs_loss_embedding_corr_with_macro_f1")

# Backfill from CSVs if JSON does not include values.
if best_pair_macro is None and not pair_candidate.empty and "mean_macro_f1" in pair_candidate.columns:
    best_pair_macro = max_numeric(pair_candidate, "mean_macro_f1")
if best_pair_under_050 is None and not pair_candidate.empty and "folds_under_050_macro_f1" in pair_candidate.columns:
    best_pair_under_050 = max_numeric(pair_candidate, "folds_under_050_macro_f1")
if mean_label_entropy is None:
    for c in ["label_entropy", "entropy", "mean_label_entropy"]:
        if c in label_audit.columns:
            mean_label_entropy = mean_numeric(label_audit, c)
            break
if max_abs_corr is None:
    for c in ["abs_corr_with_macro_f1", "abs_loss_embedding_corr_with_macro_f1", "correlation_abs"]:
        if c in metric_alignment.columns:
            max_abs_corr = max_numeric(metric_alignment, c)
            break

# More robust audit features.
n_label_rows = len(label_audit)
n_low_entropy = 0
if "label_entropy" in label_audit.columns:
    n_low_entropy = int((pd.to_numeric(label_audit["label_entropy"], errors="coerce") < 0.50).sum())
elif "entropy" in label_audit.columns:
    n_low_entropy = int((pd.to_numeric(label_audit["entropy"], errors="coerce") < 0.50).sum())

shift_cols = [c for c in label_audit.columns if "shift" in c.lower()]
max_subject_shift = None
for c in shift_cols:
    v = max_numeric(label_audit, c)
    if v is not None:
        max_subject_shift = v if max_subject_shift is None else max(max_subject_shift, abs(v))

repr_best = None
for c in ["mean_macro_f1", "macro_f1", "best_macro_f1"]:
    if c in repr_summary.columns:
        repr_best = max_numeric(repr_summary, c)
        break

subject_rel_retention = None
for c in ["retention_fraction", "retention", "valid_fraction"]:
    if c in subject_rel_balance.columns:
        subject_rel_retention = mean_numeric(subject_rel_balance, c)
        break

# Candidate matrix: score task-level options, not model methods.
candidate_rows = [
    {
        "candidate": "stop_archive_current_global_binary_loso_path",
        "decision_type": "stop",
        "scientific_value": "high if documented honestly; prevents chasing non-defensible task",
        "evidence_for": "Repeated CE/SupCon/DG/preprocessing/pair-sampler attempts stayed near chance.",
        "evidence_against": "Some folds/cells exceed 0.55, so the data is not pure noise.",
        "main_risk": "Could stop too early before testing a better task semantics.",
        "training_authorized": "no",
        "recommended_role": "fallback if task redesign is not accepted",
    },
    {
        "candidate": "pause_global_binary_loso_claim_and_redesign_task_semantics",
        "decision_type": "pause_redesign",
        "scientific_value": "highest; directly targets label semantics before new modeling",
        "evidence_for": "Joint label-semantics and representation-transfer bottleneck; pair sampler not primary failure mode.",
        "evidence_against": "Requires a new spec and careful anti-cherry-picking constraints.",
        "main_risk": "May delay training, but avoids uncontrolled model search.",
        "training_authorized": "no",
        "recommended_role": "selected",
    },
    {
        "candidate": "subject_relative_binary_top_bottom_q33",
        "decision_type": "redesign_variant",
        "scientific_value": "moderate; addresses subject rating scale differences",
        "evidence_for": "Retains within-subject semantics and reduces global-threshold mismatch.",
        "evidence_against": "First-pass subject-relative training was not sufficient alone.",
        "main_risk": "Could still be representation-limited or too narrow for LOSO claim.",
        "training_authorized": "no",
        "recommended_role": "candidate for future spec only",
    },
    {
        "candidate": "ordinal_or_regression_affect_rating_task",
        "decision_type": "redesign_variant",
        "scientific_value": "high; preserves rating magnitude instead of binary thresholding",
        "evidence_for": "Binary discretization likely collapses subject-specific semantics and confidence.",
        "evidence_against": "Needs new metrics and baselines; not directly comparable to old binary results.",
        "main_risk": "May be harder, but more scientifically faithful.",
        "training_authorized": "no",
        "recommended_role": "primary redesign candidate",
    },
    {
        "candidate": "restricted_high_confidence_label_task",
        "decision_type": "narrow_validation",
        "scientific_value": "moderate if pre-registered; useful as sanity validation",
        "evidence_for": "Can test whether low-confidence/mid ratings are diluting supervision.",
        "evidence_against": "High cherry-picking risk unless locked before training.",
        "main_risk": "Inflated result if cohort/item selection is unconstrained.",
        "training_authorized": "no",
        "recommended_role": "secondary diagnostic candidate",
    },
    {
        "candidate": "personalization_or_few_shot_adaptation_task",
        "decision_type": "redesign_variant",
        "scientific_value": "high if subject variability is central scientific target",
        "evidence_for": "Subject variability remains supported across many diagnostics.",
        "evidence_against": "Changes final claim away from pure LOSO generalization.",
        "main_risk": "Requires a new claim and protocol.",
        "training_authorized": "no",
        "recommended_role": "alternative mainline candidate",
    },
]

candidate_df = pd.DataFrame(candidate_rows)
candidate_df.to_csv(candidate_csv_path, index=False)

decision_rows = [
    {
        "decision": "continue_current_global_binary_loso_training",
        "verdict": "reject",
        "reason": "Model-side and pair/sampler interventions did not produce robust gains; label/task semantics remain unresolved.",
        "next_step_allowed": "none",
    },
    {
        "decision": "direct_full_supcon_dg_training",
        "verdict": "reject_block",
        "reason": "Smoke tests passed but first-pass and targeted ablations were not sufficient.",
        "next_step_allowed": "none",
    },
    {
        "decision": "broad_hyperparameter_search",
        "verdict": "reject_block",
        "reason": "Would obscure root cause and violate the current diagnosis workflow.",
        "next_step_allowed": "none",
    },
    {
        "decision": "task_semantics_redesign_spec",
        "verdict": "select",
        "reason": "Directly addresses the accepted joint label-semantics and representation-transfer bottleneck.",
        "next_step_allowed": "create reviewed task redesign spec with no training",
    },
    {
        "decision": "stop_archive_if_redesign_not_accepted",
        "verdict": "conditional",
        "reason": "If no defensible task redesign is accepted, the current branch should be stopped rather than patched with more models.",
        "next_step_allowed": "create stop/archive closeout",
    },
]
decision_df = pd.DataFrame(decision_rows)
decision_df.to_csv(decision_csv_path, index=False)

gap_rows = [
    {
        "evidence_gap": "task_semantic_validity",
        "current_state": "global binary labels show subject-semantics risk",
        "required_before_training": "pre-register a redesigned target and justify label semantics",
        "blocking": "yes",
    },
    {
        "evidence_gap": "metric_alignment",
        "current_state": f"weak objective alignment; max_abs_corr={fmt(max_abs_corr)}",
        "required_before_training": "define metric expected to improve and how it maps to scientific claim",
        "blocking": "yes",
    },
    {
        "evidence_gap": "representation_transfer",
        "current_state": f"best observed transfer summary remains low; repr_best={fmt(repr_best)}",
        "required_before_training": "specify whether the task is LOSO, personalization, or few-shot adaptation",
        "blocking": "yes",
    },
    {
        "evidence_gap": "subject_relative_interpretation",
        "current_state": f"subject-relative retention estimate={fmt(subject_rel_retention)}; first-pass not sufficient",
        "required_before_training": "decide if subject-relative labels are the claim or only a diagnostic",
        "blocking": "yes",
    },
    {
        "evidence_gap": "anti_cherry_picking_guardrails",
        "current_state": "restricted/high-confidence task not yet pre-registered",
        "required_before_training": "lock inclusion criteria before any new training",
        "blocking": "yes",
    },
]
gap_df = pd.DataFrame(gap_rows)
gap_df.to_csv(gap_csv_path, index=False)

recommended_next_objective = "label_semantics_task_redesign_spec_objective"
diagnosis = "current_global_binary_loso_task_not_defensible_for_more_model_search"
decision = "pause_current_global_binary_loso_training_and_prepare_task_redesign_spec"
stop_condition = "If a defensible redesign spec cannot be accepted, stop/archive the current binary LOSO branch."

summary = {
    "status": "complete_pending_human_review",
    "created_utc": now,
    "source_objective": "docs/idare_label_semantics_task_redesign_or_stop_objective.md",
    "diagnosis": diagnosis,
    "decision": decision,
    "recommended_next_objective": recommended_next_objective,
    "stop_condition": stop_condition,
    "key_indicators": {
        "previous_diagnosis": diagnosis_prev,
        "best_pair_sampler_candidate_mean_macro_f1": best_pair_macro,
        "best_pair_sampler_candidate_folds_under_050": best_pair_under_050,
        "mean_label_entropy": mean_label_entropy,
        "n_label_audit_rows": n_label_rows,
        "n_low_entropy_rows": n_low_entropy,
        "high_subject_rating_shift": high_subject_rating_shift,
        "low_entropy_problem": low_entropy_problem,
        "objective_alignment_weak": objective_alignment_weak,
        "max_abs_loss_embedding_corr_with_macro_f1": max_abs_corr,
        "representation_best_macro_f1": repr_best,
        "subject_relative_mean_retention": subject_rel_retention,
    },
    "outputs": {
        "report_md": str(report_md_path),
        "report_json": str(report_json_path),
        "decision_matrix_csv": str(decision_csv_path),
        "task_candidate_matrix_csv": str(candidate_csv_path),
        "evidence_gap_audit_csv": str(gap_csv_path),
    },
    "blocked": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
        "new model training before task redesign spec review",
    ],
    "next_allowed_step": "human_review_closeout_then_task_redesign_spec_or_stop_archive",
}
report_json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Build markdown report.
md = []
md.append("# I-DARE Label-Semantics Task-Redesign-or-Stop Report\n")
md.append("## Status\n")
md.append("Status: complete; pending human review.\n")
md.append(f"Created UTC: `{now}`\n")
md.append("## Executive Decision\n")
md.append(f"Diagnosis: `{diagnosis}`\n")
md.append(f"Decision: `{decision}`\n")
md.append(f"Recommended next objective: `{recommended_next_objective}`\n")
md.append(f"Stop condition: {stop_condition}\n")
md.append("## Why More Model Search Is Blocked\n")
md.append(
    "The current evidence says the bottleneck is not primarily a missing optimizer trick, pair sampler, or SupCon/DG toggle. "
    "The best targeted pair-sampler cell remained weak and unstable, and the previous report diagnosed a joint label-semantics and representation-transfer bottleneck.\n"
)
md.append("Key indicators:\n")
md.append(f"- best pair-sampler candidate mean macro-F1: `{fmt(best_pair_macro)}`\n")
md.append(f"- best pair-sampler candidate folds under 0.50 macro-F1: `{best_pair_under_050}`\n")
md.append(f"- mean label entropy: `{fmt(mean_label_entropy)}`\n")
md.append(f"- high subject rating shift: `{high_subject_rating_shift}`\n")
md.append(f"- low entropy problem: `{low_entropy_problem}`\n")
md.append(f"- objective alignment weak: `{objective_alignment_weak}`\n")
md.append(f"- max absolute loss/embedding correlation with macro-F1: `{fmt(max_abs_corr)}`\n")
md.append("## Candidate Task Decisions\n")
md.append(md_table(candidate_rows, [
    "candidate", "decision_type", "scientific_value", "evidence_for", "evidence_against", "main_risk", "recommended_role"
]))
md.append("\n## Decision Matrix\n")
md.append(md_table(decision_rows, ["decision", "verdict", "reason", "next_step_allowed"]))
md.append("\n## Evidence Gap Audit\n")
md.append(md_table(gap_rows, ["evidence_gap", "current_state", "required_before_training", "blocking"]))
md.append("\n## Interpretation\n")
md.append(
    "The current global binary LOSO task should be paused as a final-performance target. "
    "Continuing with direct full SupCon/DG training or broad hyperparameter search would not answer the accepted failure mode. "
    "The scientifically cleaner path is to write a task redesign spec first, with the main candidates being ordinal/regression affect modeling, a pre-registered restricted high-confidence task, or a personalization/few-shot formulation. "
    "If none of these can be justified without cherry-picking, the current binary global-label branch should be stopped/archived.\n"
)
md.append("## Next Allowed Step\n")
md.append("Human review / closeout before one of the following:\n")
md.append("- create a label-semantics task-redesign specification objective;\n")
md.append("- create a stop/archive closeout objective.\n")
md.append("\nBlocked until review:\n")
for b in summary["blocked"]:
    md.append(f"- {b}\n")
report_md_path.write_text("\n".join(md), encoding="utf-8")

# Update roadmap/status.
status = load_json(status_path)
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "human_review_closeout_then_task_redesign_spec_or_stop_archive"
status["current_idare_blocked_steps"] = summary["blocked"]
status.setdefault("idare_protocol_events", []).append({
    "timestamp_utc": now,
    "type": "report",
    "name": "I-DARE label-semantics task-redesign-or-stop report",
    "status": f"complete pending human review; diagnosis={diagnosis}",
    "evidence": str(report_md_path),
    "next_allowed_step": "human review / closeout before task redesign spec or stop/archive",
    "blocked": summary["blocked"],
})
status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Label-Semantics Task-Redesign-or-Stop Report

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE label-semantics task-redesign-or-stop report | complete pending human review; diagnosis=`{diagnosis}` | `docs/idare_label_semantics_task_redesign_or_stop_report.md` | Human review / closeout before task redesign spec or stop/archive. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Recommended next objective is `{recommended_next_objective}` only after human review/closeout.
- Stop/archive is explicitly allowed if no defensible task redesign spec is accepted.
"""
if "I-DARE Label-Semantics Task-Redesign-or-Stop Report" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_LABEL_SEMANTICS_TASK_REDESIGN_OR_STOP_REPORT_WRITTEN")
print(report_md_path)
print(report_json_path)
print(decision_csv_path)
print(candidate_csv_path)
print(gap_csv_path)
print("diagnosis=", diagnosis)
print("decision=", decision)
print("recommended_next_objective=", recommended_next_objective)
print("stop_condition=", stop_condition)
print("key_indicators=", json.dumps(summary["key_indicators"], ensure_ascii=False))
PY
echo

echo "===== 5) validate generated outputs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_paths = [
    Path("docs/idare_label_semantics_task_redesign_or_stop_report.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

csv_expect = {
    "docs/idare_label_semantics_task_redesign_or_stop_decision_matrix.csv": 5,
    "docs/idare_label_semantics_task_candidate_matrix.csv": 6,
    "docs/idare_label_semantics_evidence_gap_audit.csv": 5,
}
for p, min_rows in csv_expect.items():
    df = pd.read_csv(p)
    print(Path(p).name, "rows=", len(df))
    if len(df) < min_rows:
        raise SystemExit(f"ERROR: {p} has too few rows")

report = json.loads(Path("docs/idare_label_semantics_task_redesign_or_stop_report.json").read_text(encoding="utf-8"))
required = [
    "diagnosis",
    "decision",
    "recommended_next_objective",
    "stop_condition",
    "key_indicators",
]
for k in required:
    if k not in report:
        raise SystemExit(f"ERROR: report missing {k}")

text = Path("docs/idare_label_semantics_task_redesign_or_stop_report.md").read_text(encoding="utf-8")
for term in [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "final LOSO claim",
    "stop/archive",
    "task redesign",
]:
    if term not in text:
        raise SystemExit(f"ERROR: missing term {term!r} in report markdown")

print("diagnosis=", report["diagnosis"])
print("decision=", report["decision"])
print("recommended_next_objective=", report["recommended_next_objective"])
print("ALL_LABEL_SEMANTICS_TASK_REDESIGN_OR_STOP_REPORT_OUTPUTS_VALID")
PY

grep -nE "Status|Executive Decision|Why More Model Search|Candidate Task Decisions|Decision Matrix|Evidence Gap Audit|Interpretation|Next Allowed Step" \
  docs/idare_label_semantics_task_redesign_or_stop_report.md
grep -nE "Label-Semantics Task-Redesign-or-Stop Report|Recommended next objective" docs/project_status_current.md | tail -n 8
echo

echo "===== 6) file list ====="
ls -lh \
  docs/idare_label_semantics_task_redesign_or_stop_report.md \
  docs/idare_label_semantics_task_redesign_or_stop_report.json \
  docs/idare_label_semantics_task_redesign_or_stop_decision_matrix.csv \
  docs/idare_label_semantics_task_candidate_matrix.csv \
  docs/idare_label_semantics_evidence_gap_audit.csv \
  docs/project_status_current.json \
  docs/project_status_current.md
echo

echo "===== 7) status before commit ====="
git status --short --branch
echo

echo "===== 8) commit and push label-semantics task-redesign/stop report ====="
git add \
  docs/idare_label_semantics_task_redesign_or_stop_report.md \
  docs/idare_label_semantics_task_redesign_or_stop_report.json \
  docs/idare_label_semantics_task_redesign_or_stop_decision_matrix.csv \
  docs/idare_label_semantics_task_candidate_matrix.csv \
  docs/idare_label_semantics_evidence_gap_audit.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "analysis: add I-DARE label semantics task decision report"
git push origin main
echo

echo "===== 9) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
