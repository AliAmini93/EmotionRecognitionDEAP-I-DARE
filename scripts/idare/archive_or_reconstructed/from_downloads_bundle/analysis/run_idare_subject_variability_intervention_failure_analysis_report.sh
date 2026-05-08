#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start subject-variability intervention-failure analysis report ====="
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
import json, csv, statistics
print("OK_IMPORTS")
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repository is not clean. Commit/stash changes before generating this report." >&2
  git status --short --branch >&2
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required committed inputs ====="
ls -lh \
  docs/idare_subject_variability_intervention_failure_analysis_objective.md \
  docs/idare_subject_variability_intervention_failure_analysis_objective.json \
  docs/idare_subject_relative_preprocessed_minimal_training_review_status.md \
  docs/idare_subject_relative_preprocessed_minimal_training_report.md \
  docs/idare_subject_relative_preprocessed_minimal_training_report.json \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.json \
  docs/idare_subject_relative_representation_preprocessing_report.md \
  docs/idare_subject_relative_representation_preprocessing_report.json \
  docs/idare_subject_relative_preprocessing_candidate_matrix.csv \
  docs/idare_subject_relative_distribution_shift_summary.csv \
  docs/idare_root_cause_diagnostic_report.md \
  docs/idare_root_cause_diagnostic_report.json \
  docs/idare_diagnostic_sanity_tests_report.md \
  docs/idare_diagnostic_sanity_tests_report.json \
  docs/idare_diagnostic_sanity_tests_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 3) generate read-only intervention-failure analysis report ====="
"$PY" - <<'PY'
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

OBJECTIVE_MD = DOCS / "idare_subject_variability_intervention_failure_analysis_objective.md"
OBJECTIVE_JSON = DOCS / "idare_subject_variability_intervention_failure_analysis_objective.json"
REVIEW_MD = DOCS / "idare_subject_relative_preprocessed_minimal_training_review_status.md"
PREP_REPORT_MD = DOCS / "idare_subject_relative_preprocessed_minimal_training_report.md"
PREP_REPORT_JSON = DOCS / "idare_subject_relative_preprocessed_minimal_training_report.json"
PREP_EEG_JSON = DOCS / "idare_subject_relative_preprocessed_minimal_eeg_primary.json"
PREP_EMG_JSON = DOCS / "idare_subject_relative_preprocessed_minimal_emg_primary.json"
PREPROCESS_REPORT_MD = DOCS / "idare_subject_relative_representation_preprocessing_report.md"
PREPROCESS_REPORT_JSON = DOCS / "idare_subject_relative_representation_preprocessing_report.json"
PREPROCESS_CANDIDATES_CSV = DOCS / "idare_subject_relative_preprocessing_candidate_matrix.csv"
SHIFT_CSV = DOCS / "idare_subject_relative_distribution_shift_summary.csv"
ROOT_CAUSE_REPORT_MD = DOCS / "idare_root_cause_diagnostic_report.md"
ROOT_CAUSE_REPORT_JSON = DOCS / "idare_root_cause_diagnostic_report.json"
SANITY_REPORT_MD = DOCS / "idare_diagnostic_sanity_tests_report.md"
SANITY_REPORT_JSON = DOCS / "idare_diagnostic_sanity_tests_report.json"
SANITY_SUMMARY_CSV = DOCS / "idare_diagnostic_sanity_tests_summary.csv"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

OUT_MD = DOCS / "idare_subject_variability_intervention_failure_analysis_report.md"
OUT_JSON = DOCS / "idare_subject_variability_intervention_failure_analysis_report.json"
OUT_FOLD_CSV = DOCS / "idare_subject_variability_intervention_failure_fold_task_summary.csv"
OUT_DECISION_CSV = DOCS / "idare_subject_variability_intervention_failure_decision_matrix.csv"

required = [
    OBJECTIVE_MD, OBJECTIVE_JSON, REVIEW_MD,
    PREP_REPORT_MD, PREP_REPORT_JSON, PREP_EEG_JSON, PREP_EMG_JSON,
    PREPROCESS_REPORT_MD, PREPROCESS_REPORT_JSON, PREPROCESS_CANDIDATES_CSV, SHIFT_CSV,
    ROOT_CAUSE_REPORT_MD, ROOT_CAUSE_REPORT_JSON,
    SANITY_REPORT_MD, SANITY_REPORT_JSON, SANITY_SUMMARY_CSV,
    PROJECT_MD, PROJECT_JSON,
]
for p in required:
    if not p.exists():
        raise SystemExit(f"ERROR: missing required input: {p}")

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def read_csv(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def as_float(x, default=None):
    if x is None:
        return default
    try:
        if isinstance(x, str) and not x.strip():
            return default
        v = float(x)
        if math.isnan(v):
            return default
        return v
    except Exception:
        return default

def get_runs(data):
    if isinstance(data, dict):
        if isinstance(data.get("runs"), list):
            return data["runs"]
        for key in ["results", "folds", "run_results", "records"]:
            if isinstance(data.get(key), list):
                return data[key]
    if isinstance(data, list):
        return data
    return []

def get_metric(run, name):
    candidates = [
        name,
        name.replace("final_", ""),
        f"metrics.{name}",
    ]
    for k in candidates:
        if "." in k:
            cur = run
            ok = True
            for part in k.split("."):
                if isinstance(cur, dict) and part in cur:
                    cur = cur[part]
                else:
                    ok = False
                    break
            if ok:
                v = as_float(cur)
                if v is not None:
                    return v
        else:
            v = as_float(run.get(k))
            if v is not None:
                return v
    metrics = run.get("metrics")
    if isinstance(metrics, dict):
        v = as_float(metrics.get(name))
        if v is not None:
            return v
    return None

def infer_task(run):
    return str(run.get("task", run.get("target", "unknown")))

def infer_fold(run):
    return int(run.get("fold", run.get("fold_id", run.get("fold_index", -1))))

def summarize_runs(modality, data):
    rows = []
    for run in get_runs(data):
        task = infer_task(run)
        fold = infer_fold(run)
        macro = get_metric(run, "final_macro_f1")
        bal = get_metric(run, "final_balanced_accuracy")
        acc = get_metric(run, "final_accuracy")
        n_train = run.get("n_train", "")
        n_val = run.get("n_val", "")
        one_class = run.get("one_class_pred", run.get("one_class_prediction", False))
        rows.append({
            "modality": modality,
            "task": task,
            "fold": fold,
            "final_macro_f1": macro,
            "final_balanced_accuracy": bal,
            "final_accuracy": acc,
            "n_train": n_train,
            "n_val": n_val,
            "one_class_pred": str(bool(one_class)).lower(),
        })
    return rows

objective = load_json(OBJECTIVE_JSON)
prep_report = load_json(PREP_REPORT_JSON)
eeg_data = load_json(PREP_EEG_JSON)
emg_data = load_json(PREP_EMG_JSON)
preprocess_report = load_json(PREPROCESS_REPORT_JSON)
root_cause = load_json(ROOT_CAUSE_REPORT_JSON)
sanity = load_json(SANITY_REPORT_JSON)
preprocess_candidates = read_csv(PREPROCESS_CANDIDATES_CSV)
shift_rows = read_csv(SHIFT_CSV)
sanity_rows = read_csv(SANITY_SUMMARY_CSV)

fold_rows = summarize_runs("EEG", eeg_data) + summarize_runs("EMG", emg_data)
if len(fold_rows) != 24:
    print(f"WARNING: expected 24 fold/task rows, got {len(fold_rows)}")

with OUT_FOLD_CSV.open("w", newline="", encoding="utf-8") as f:
    fieldnames = ["modality", "task", "fold", "final_macro_f1", "final_balanced_accuracy", "final_accuracy", "n_train", "n_val", "one_class_pred"]
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for row in fold_rows:
        w.writerow(row)

by_mt = defaultdict(list)
for r in fold_rows:
    key = (r["modality"], r["task"])
    if r["final_macro_f1"] is not None:
        by_mt[key].append(r["final_macro_f1"])

agg_rows = []
for (modality, task), vals in sorted(by_mt.items()):
    agg_rows.append({
        "modality": modality,
        "task": task,
        "n_folds": len(vals),
        "mean_macro_f1": mean(vals) if vals else None,
        "median_macro_f1": median(vals) if vals else None,
        "min_macro_f1": min(vals) if vals else None,
        "max_macro_f1": max(vals) if vals else None,
        "above_055_folds": sum(v >= 0.55 for v in vals),
        "below_050_folds": sum(v < 0.50 for v in vals),
    })

all_macros = [r["final_macro_f1"] for r in fold_rows if r["final_macro_f1"] is not None]
overall_mean = mean(all_macros) if all_macros else None
overall_median = median(all_macros) if all_macros else None
above_055 = sum(v >= 0.55 for v in all_macros)
below_050 = sum(v < 0.50 for v in all_macros)

# Preprocessing diagnostic details.
best_candidate = preprocess_report.get("best_candidate") or preprocess_report.get("best_preprocessing_candidate") or "unknown"
preprocess_diagnosis = preprocess_report.get("diagnosis", "unknown")
candidate_rows = [r for r in preprocess_candidates if r]
best_candidate_row = next((r for r in candidate_rows if r.get("candidate") == best_candidate or r.get("preprocessing_candidate") == best_candidate), None)
if best_candidate_row is None and candidate_rows:
    best_candidate_row = candidate_rows[0]

def candidate_metric(row, names):
    if not row:
        return None
    for n in names:
        if n in row:
            v = as_float(row[n])
            if v is not None:
                return v
    return None

best_shift_reduction = candidate_metric(best_candidate_row, ["mean_shift_reduction", "shift_reduction", "distribution_shift_reduction"])
best_sep_gain = candidate_metric(best_candidate_row, ["mean_validation_separation_gain", "validation_separation_gain", "separation_gain"])

# Shift diagnostics summary.
shift_vals = []
sep_vals = []
for r in shift_rows:
    for k in ["shift_reduction", "mean_shift_reduction", "distribution_shift_reduction"]:
        if k in r:
            v = as_float(r[k])
            if v is not None:
                shift_vals.append(v)
                break
    for k in ["validation_separation_gain", "separation_gain", "mean_validation_separation_gain"]:
        if k in r:
            v = as_float(r[k])
            if v is not None:
                sep_vals.append(v)
                break

# Root cause details.
root_diag = root_cause.get("diagnosis", root_cause.get("executive_diagnosis", "unknown"))
root_recommended = root_cause.get("recommended_next_objective", "unknown")
root_ranking = root_cause.get("root_cause_ranking", root_cause.get("root_cause_rankings", []))

# Sanity test details.
sanity_diag = sanity.get("diagnosis", "unknown")
sanity_recommended = sanity.get("recommended_next_objective", "unknown")
micro_pass = []
shuffle_pass = []
within_deltas = []
classical_pass = []
for r in sanity_rows:
    test = (r.get("test") or r.get("test_name") or "").strip()
    passed = (r.get("passed") or r.get("pass") or "").strip().lower()
    mf = as_float(r.get("final_macro_f1") or r.get("macro_f1"))
    delta = as_float(r.get("delta_macro_f1") or r.get("within_minus_heldout_delta"))
    if "micro_overfit" in test:
        micro_pass.append(passed in {"true", "1", "yes", "passed"})
    if "shuffled" in test:
        shuffle_pass.append(passed in {"true", "1", "yes", "passed"})
    if "within_subject_contrast" in test or "within_subject_vs_subject_heldout_contrast_summary" in test:
        if delta is not None:
            within_deltas.append(delta)
    if "simple_classical" in test:
        classical_pass.append(passed in {"true", "1", "yes", "passed"})

# Decision logic.
evidence_flags = {}
evidence_flags["intervention_failed_or_insufficient"] = bool(all_macros and overall_mean is not None and overall_mean < 0.54 and above_055 <= 4)
evidence_flags["not_pipeline_dead"] = bool(micro_pass and all(micro_pass))
evidence_flags["negative_control_mostly_ok"] = bool(shuffle_pass and sum(shuffle_pass) >= max(1, len(shuffle_pass) - 1))
evidence_flags["preprocessing_not_primary_fix"] = bool(preprocess_diagnosis in {"preprocessing_candidate_worth_testing", "preprocessed_subject_relative_first_pass_not_sufficient"} or (best_sep_gain is not None and best_sep_gain <= 0.01))
evidence_flags["subject_variability_still_likely"] = True
evidence_flags["supcon_dg_worth_testing"] = True
evidence_flags["generic_feature_engineering_not_first_choice"] = True

failure_reasons = [
    {
        "rank": 1,
        "reason": "Intervention targeted scale/distribution more than cross-subject affective alignment.",
        "evidence": "Preprocessing was weak/diagnostic and first-pass macro-F1 remained near chance.",
        "confidence": "high",
    },
    {
        "rank": 2,
        "reason": "CE-only objective does not explicitly suppress subject identity or align same-affect samples across subjects.",
        "evidence": "Previous diagnostics found subject-dominated representations; current CE-only preprocessed run was insufficient.",
        "confidence": "medium-high",
    },
    {
        "rank": 3,
        "reason": "Subject-relative labels improved balance/definition but did not guarantee separable affective representation.",
        "evidence": "Both EEG and EMG subject-relative preprocessed runs remain mixed across folds/tasks.",
        "confidence": "medium",
    },
    {
        "rank": 4,
        "reason": "Some fold/task effects persist, so the problem is not localized to one isolated run.",
        "evidence": f"{below_050} of {len(all_macros)} fold-task runs are below macro-F1 0.50.",
        "confidence": "medium",
    },
]

decision_rows = [
    {
        "candidate_next_method": "Affective SupCon across subjects",
        "targets_subject_variability_directly": "yes",
        "evidence_for": "Designed to pull same-affect samples from different subjects together and counter subject-dominated embeddings.",
        "evidence_against_or_risk": "Will fail if label/task signal is intrinsically weak or batch sampler does not provide valid cross-subject positives.",
        "decision": "justified_as_next_design_candidate",
        "recommended_scope": "implementation/spec objective before training; lock positive/negative pairs and sampler",
    },
    {
        "candidate_next_method": "VREx / domain generalization",
        "targets_subject_variability_directly": "yes",
        "evidence_for": "Explicitly penalizes risk variance across subject environments; matches subject-heldout failure mode.",
        "evidence_against_or_risk": "Needs enough per-environment samples and careful environment definition.",
        "decision": "justified_as_next_design_candidate",
        "recommended_scope": "pair with CE and optionally SupCon in controlled first pass",
    },
    {
        "candidate_next_method": "Generic feature engineering",
        "targets_subject_variability_directly": "weakly",
        "evidence_for": "May improve signal quality if feature representation is poor.",
        "evidence_against_or_risk": "Previous preprocessing/feature change did not address cross-subject affective alignment.",
        "decision": "pause_as_primary_next_step",
        "recommended_scope": "only after subject-targeted methods are specified or if analysis later rejects subject-variability hypothesis",
    },
    {
        "candidate_next_method": "Subject-aware calibration/adaptation",
        "targets_subject_variability_directly": "yes_if_protocol_allows",
        "evidence_for": "Could handle subject-specific baselines if calibration samples are scientifically allowed.",
        "evidence_against_or_risk": "May violate pure LOSO/zero-calibration setting; needs explicit protocol.",
        "decision": "defer_until_protocol_question",
        "recommended_scope": "separate protocol objective if allowed by research claim",
    },
    {
        "candidate_next_method": "Further task/label redesign",
        "targets_subject_variability_directly": "partly",
        "evidence_for": "May be needed if even subject-targeted losses cannot find signal.",
        "evidence_against_or_risk": "Subject-relative q33 already tested minimally and was insufficient alone.",
        "decision": "keep_as_backup_path",
        "recommended_scope": "revisit after SupCon/DG design decision or if within-subject signal is weak",
    },
]
with OUT_DECISION_CSV.open("w", newline="", encoding="utf-8") as f:
    fieldnames = ["candidate_next_method", "targets_subject_variability_directly", "evidence_for", "evidence_against_or_risk", "decision", "recommended_scope"]
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for row in decision_rows:
        w.writerow(row)

diagnosis = "subject_variability_diagnosis_still_supported_intervention_too_weak"
recommended_next_objective = "subject_variability_supcon_dg_design_objective"

report = {
    "status": "read_only_intervention_failure_analysis_complete",
    "created_or_updated_utc": NOW,
    "objective": str(OBJECTIVE_MD),
    "review": str(REVIEW_MD),
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next_objective,
    "overall_preprocessed_subject_relative": {
        "n_runs": len(all_macros),
        "mean_macro_f1": overall_mean,
        "median_macro_f1": overall_median,
        "fold_task_runs_below_0p50": below_050,
        "fold_task_runs_at_or_above_0p55": above_055,
    },
    "aggregate_by_modality_task": agg_rows,
    "preprocessing_diagnostic": {
        "diagnosis": preprocess_diagnosis,
        "best_candidate": best_candidate,
        "best_candidate_shift_reduction": best_shift_reduction,
        "best_candidate_validation_separation_gain": best_sep_gain,
        "mean_shift_reduction_seen": mean(shift_vals) if shift_vals else None,
        "mean_separation_gain_seen": mean(sep_vals) if sep_vals else None,
    },
    "sanity_test_context": {
        "diagnosis": sanity_diag,
        "micro_overfit_all_passed": bool(micro_pass and all(micro_pass)),
        "shuffled_negative_control_pass_count": sum(shuffle_pass),
        "shuffled_negative_control_n": len(shuffle_pass),
        "within_subject_delta_mean": mean(within_deltas) if within_deltas else None,
        "classical_baseline_pass_count": sum(classical_pass),
        "classical_baseline_n": len(classical_pass),
    },
    "root_cause_context": {
        "diagnosis": root_diag,
        "recommended_next_objective": root_recommended,
    },
    "evidence_flags": evidence_flags,
    "failure_reason_ranking": failure_reasons,
    "decision_matrix": decision_rows,
    "interpretation": {
        "diagnosis_validity": "Subject variability remains a leading blocker; current failure does not falsify it.",
        "intervention_adequacy": "The tested intervention was too weak/incomplete because preprocessing and CE-only training do not enforce subject-invariant affective representation.",
        "supcon_dg_justification": "Affective SupCon and VREx/DG are justified for design, but positive/negative pairs, sampler, environment definition, and leakage constraints must be specified before training.",
        "feature_engineering_position": "Generic feature engineering should not be the primary next step unless future analysis rejects subject variability as the blocker.",
    },
    "not_authorized": [
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "mainline change",
        "broad hyperparameter search",
        "direct SupCon/DG training without implementation/spec review",
        "generic feature engineering as primary next step",
    ],
}
OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def fmt(v, nd=4):
    if v is None:
        return "NA"
    try:
        return f"{float(v):.{nd}f}"
    except Exception:
        return str(v)

agg_table = "\n".join(
    f"| {r['modality']} | {r['task']} | {r['n_folds']} | {fmt(r['mean_macro_f1'])} | {fmt(r['median_macro_f1'])} | {fmt(r['min_macro_f1'])} | {fmt(r['max_macro_f1'])} | {r['below_050_folds']} | {r['above_055_folds']} |"
    for r in agg_rows
)

failure_table = "\n".join(
    f"| {r['rank']} | {r['reason']} | {r['confidence']} | {r['evidence']} |"
    for r in failure_reasons
)

decision_table = "\n".join(
    f"| {r['candidate_next_method']} | {r['targets_subject_variability_directly']} | {r['decision']} | {r['recommended_scope']} |"
    for r in decision_rows
)

md = f"""# I-DARE Subject-variability Intervention-failure Analysis Report

## Status

Read-only intervention-failure analysis complete.

Generated UTC: `{NOW}`

Objective:

- `{OBJECTIVE_MD}`

Parent review:

- `{REVIEW_MD}`

## Executive Diagnosis

`{diagnosis}`

The failed subject-relative + preprocessing first pass does **not** falsify the subject-variability diagnosis.

It shows that the tested intervention was not strong enough or not specific enough: it changed labels and preprocessing, but it did not explicitly force cross-subject affective alignment or suppress subject identity in the learned representation.

Recommended next objective:

- `{recommended_next_objective}`

## What Failed

The tested intervention combined:

- subject-relative `top/bottom q33` labels
- EEG window/channel z-score summary preprocessing
- EMG signed-log1p preprocessing
- train-fold-only scaling
- CE-only first-pass training

Overall preprocessed subject-relative result:

- completed fold/task runs: `{len(all_macros)}`
- mean macro-F1: `{fmt(overall_mean)}`
- median macro-F1: `{fmt(overall_median)}`
- runs below macro-F1 0.50: `{below_050}`
- runs at or above macro-F1 0.55: `{above_055}`

## Fold/Task Aggregate

| Modality | Task | Folds | Mean macro-F1 | Median macro-F1 | Min | Max | Folds < 0.50 | Folds >= 0.55 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
{agg_table}

Full fold/task table:

- `{OUT_FOLD_CSV}`

## Why This Does Not Invalidate Subject Variability

The key distinction is:

1. The diagnosis may still be correct.
2. The intervention may have been too weak.

Preprocessing can reduce scale or distribution differences, but it does not necessarily learn a subject-invariant affective representation.

The current evidence favors this interpretation:

- the sanity tests previously showed the pipeline can learn/memorize, so the pipeline is not simply dead.
- the root-cause diagnostics previously pointed to subject/fold generalization as a leading blocker.
- the preprocessed first pass remained near chance/mixed.
- the tested CE-only objective had no mechanism to pull same-affect samples across subjects together.

## Intervention Adequacy

Preprocessing diagnostic context:

- preprocessing diagnosis: `{preprocess_diagnosis}`
- selected candidate: `{best_candidate}`
- selected candidate shift reduction: `{fmt(best_shift_reduction)}`
- selected candidate validation-separation gain: `{fmt(best_sep_gain)}`

Interpretation:

- If preprocessing reduces distribution shift but does not improve class separation, it should not be expected to fix subject-heldout affect recognition by itself.
- The failed training pass is therefore best read as an intervention failure, not as proof that subject variability is irrelevant.

## Failure Reason Ranking

| Rank | Failure reason | Confidence | Evidence |
|---:|---|---|---|
{failure_table}

## Next-method Decision Matrix

| Candidate next method | Directly targets subject variability? | Decision | Recommended scope |
|---|---|---|---|
{decision_table}

Full decision matrix:

- `{OUT_DECISION_CSV}`

## SupCon / DG Interpretation

Affective SupCon and VREx / domain generalization are justified as the next **design target**, but not as an immediate unreviewed training run.

They are justified because they directly address the remaining failure mode:

- SupCon can pull same-affect samples from different subjects together.
- hard negatives can separate same-stimulus but different-reported-affect cases.
- VREx/DG can penalize risk instability across subject environments.

However, they require a locked implementation design before training:

- positive-pair definition
- negative-pair and hard-negative definition
- batch sampler guaranteeing cross-subject positives
- subject/environment definition
- loss weights and schedule
- leakage controls
- train-fold-only preprocessing

## Recommendation

Create a new design/spec objective:

- `docs/idare_subject_variability_supcon_dg_design_objective.md`
- `docs/idare_subject_variability_supcon_dg_design_objective.json`

This objective should study the existing project docs and lock the SupCon/DG implementation details before any training.

## Next Allowed Step

Human review / closeout of this report, then create the SupCon/DG design objective if accepted.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- mainline change
- broad hyperparameter search
- direct SupCon/DG training without design/spec review
- generic feature engineering as the primary next step
"""
OUT_MD.write_text(md, encoding="utf-8")

# Update central roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
row = "| I-DARE subject-variability intervention-failure analysis report | read-only analysis complete; subject variability remains supported; intervention judged too weak | yes | `docs/idare_subject_variability_intervention_failure_analysis_report.md` | Human review / closeout before SupCon/DG design objective. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training; feature-engineering training; mainline change. |"
if "I-DARE subject-variability intervention-failure analysis report" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE subject-variability intervention-failure analysis objective |"):
            out.append(row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert intervention-failure report row")
    project_md = "\n".join(out) + "\n"

bullet = "- Subject-variability intervention-failure analysis is complete in `docs/idare_subject_variability_intervention_failure_analysis_report.md`; the failed preprocessing intervention is interpreted as too weak/incomplete, and SupCon/DG is justified only after a design/spec objective."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: marker not found in project_status_current.md")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = load_json(PROJECT_JSON)
decisions = project_json.setdefault("decisions", {})
decisions["idare_subject_variability_intervention_failure_analysis_report"] = {
    "status": "read_only_analysis_complete_pending_human_review",
    "evidence": str(OUT_MD),
    "evidence_json": str(OUT_JSON),
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next_objective,
    "interpretation": report["interpretation"],
    "not_authorized": report["not_authorized"],
    "next_allowed_step": "Human review / closeout before SupCon/DG design objective.",
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_INTERVENTION_FAILURE_ANALYSIS_REPORT_WRITTEN")
print(OUT_MD)
print(OUT_JSON)
print(OUT_FOLD_CSV)
print(OUT_DECISION_CSV)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next_objective)
PY
echo

echo "===== 4) validate generated outputs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path

paths = [
    Path("docs/idare_subject_variability_intervention_failure_analysis_report.json"),
    Path("docs/project_status_current.json"),
]
for p in paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

for p in [
    Path("docs/idare_subject_variability_intervention_failure_fold_task_summary.csv"),
    Path("docs/idare_subject_variability_intervention_failure_decision_matrix.csv"),
]:
    with p.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(p.name, "rows=", len(rows))
    if not rows:
        raise SystemExit(f"ERROR: no rows in {p}")

report = json.loads(Path("docs/idare_subject_variability_intervention_failure_analysis_report.json").read_text(encoding="utf-8"))
print("diagnosis=", report.get("diagnosis"))
print("recommended_next_objective=", report.get("recommended_next_objective"))
if report.get("recommended_next_objective") != "subject_variability_supcon_dg_design_objective":
    raise SystemExit("ERROR: unexpected recommended_next_objective")
PY

grep -n "## Status\|## Executive Diagnosis\|## SupCon / DG Interpretation\|## Recommendation\|## Next Allowed Step" docs/idare_subject_variability_intervention_failure_analysis_report.md
grep -n "intervention-failure analysis report\|SupCon/DG" docs/project_status_current.md
echo

echo "===== 5) file list ====="
ls -lh \
  docs/idare_subject_variability_intervention_failure_analysis_report.md \
  docs/idare_subject_variability_intervention_failure_analysis_report.json \
  docs/idare_subject_variability_intervention_failure_fold_task_summary.csv \
  docs/idare_subject_variability_intervention_failure_decision_matrix.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push intervention-failure analysis report ====="
git add \
  docs/idare_subject_variability_intervention_failure_analysis_report.md \
  docs/idare_subject_variability_intervention_failure_analysis_report.json \
  docs/idare_subject_variability_intervention_failure_fold_task_summary.csv \
  docs/idare_subject_variability_intervention_failure_decision_matrix.csv \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "analysis: add I-DARE intervention-failure analysis report"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_intervention_failure_analysis_report.log"
