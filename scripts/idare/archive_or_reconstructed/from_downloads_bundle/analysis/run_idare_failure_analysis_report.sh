#!/usr/bin/env bash
set -euo pipefail

REPO="/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE"
LOG="/tmp/idare_failure_analysis_report.log"

cd "$REPO"

{
  echo "===== 0) start failure-analysis report generation ====="
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
import sys, json, csv
print(sys.executable)
print("OK_IMPORTS")
PY

  if [ -n "$(git status --short)" ]; then
    echo "ERROR: repo is not clean. Commit/stash/remove unrelated changes before failure analysis."
    git status --short --branch
    exit 1
  fi
  echo "OK_REPO_CLEAN"
  echo

  echo "===== 2) generate read-only failure analysis report from committed outputs ====="
  "$PY" - <<'PY'
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
OUT_MD = DOCS / "idare_failure_analysis_report.md"
OUT_JSON = DOCS / "idare_failure_analysis_report.json"
OUT_CSV = DOCS / "idare_failure_analysis_fold_summary.csv"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()

SOURCES = [
    {
        "matrix": "label_policy_ablation",
        "modality": "EEG",
        "representation": "STIM-BSL-only",
        "path": DOCS / "idare_label_policy_ablation_eeg_primary_predictions.csv",
        "json": DOCS / "idare_label_policy_ablation_eeg_primary.json",
    },
    {
        "matrix": "label_policy_ablation",
        "modality": "EMG",
        "representation": "feature-only",
        "path": DOCS / "idare_label_policy_ablation_emg_primary_predictions.csv",
        "json": DOCS / "idare_label_policy_ablation_emg_primary.json",
    },
    {
        "matrix": "broader_single_modality",
        "modality": "EEG",
        "representation": "STIM-BSL-only",
        "path": DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv",
        "json": DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary.json",
    },
    {
        "matrix": "broader_single_modality",
        "modality": "EEG",
        "representation": "STIM-BSL+BSL-stats",
        "path": DOCS / "idare_broader_eval_eeg_bsl_stats_primary_predictions.csv",
        "json": DOCS / "idare_broader_eval_eeg_bsl_stats_primary.json",
    },
    {
        "matrix": "broader_single_modality",
        "modality": "EMG",
        "representation": "feature-only",
        "path": DOCS / "idare_broader_eval_emg_feature_only_primary_predictions.csv",
        "json": DOCS / "idare_broader_eval_emg_feature_only_primary.json",
    },
    {
        "matrix": "broader_single_modality",
        "modality": "EMG",
        "representation": "feature+BSL-stats",
        "path": DOCS / "idare_broader_eval_emg_bsl_stats_primary_predictions.csv",
        "json": DOCS / "idare_broader_eval_emg_bsl_stats_primary.json",
    },
]

REQUIRED_CONTEXT = [
    DOCS / "idare_failure_analysis_objective.md",
    DOCS / "idare_label_policy_ablation_report.json",
    DOCS / "idare_label_policy_ablation_review_status.md",
    DOCS / "idare_broader_standardized_single_modality_evaluation_report.json",
    DOCS / "idare_broader_standardized_single_modality_evaluation_review_status.md",
    PROJECT_MD,
    PROJECT_JSON,
]

missing = [str(p) for p in REQUIRED_CONTEXT if not p.exists()]
for src in SOURCES:
    if not src["path"].exists():
        missing.append(str(src["path"]))
    if not src["json"].exists():
        missing.append(str(src["json"]))
if missing:
    raise SystemExit("ERROR missing required files: " + ", ".join(missing))

def to_int(v):
    if v is None or v == "":
        return None
    return int(float(v))

def safe_div(a, b):
    return float(a / b) if b else 0.0

def mean(vals):
    vals = [v for v in vals if v is not None and not math.isnan(v)]
    return float(sum(vals) / len(vals)) if vals else math.nan

def std(vals):
    vals = [v for v in vals if v is not None and not math.isnan(v)]
    if not vals:
        return math.nan
    m = mean(vals)
    return float((sum((v - m) ** 2 for v in vals) / len(vals)) ** 0.5)

def fmt(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "NA"
    return f"{float(v):.4f}"

def binary_metrics(y_true, y_pred):
    labels = [0, 1]
    n = len(y_true)
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    recalls = []
    f1s = []
    per_class = {}
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2 * precision * recall, precision + recall)
        recalls.append(recall)
        f1s.append(f1)
        per_class[str(label)] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(1 for t in y_true if t == label),
        }

    true_counts = {str(label): sum(1 for t in y_true if t == label) for label in labels}
    pred_counts = {str(label): sum(1 for p in y_pred if p == label) for label in labels}
    majority_label = max(labels, key=lambda label: true_counts[str(label)])
    majority_pred = [majority_label] * n
    majority = None
    if y_pred != majority_pred:
        majority = binary_metrics_no_majority(y_true, majority_pred)
    else:
        majority = {
            "accuracy": safe_div(sum(1 for t in y_true if t == majority_label), n),
            "balanced_accuracy": 0.5 if n else math.nan,
            "macro_f1": safe_div(
                2 * safe_div(true_counts[str(majority_label)], n) * 1.0,
                safe_div(true_counts[str(majority_label)], n) + 1.0,
            ) / 2,
        }

    pred_unique = sorted(set(y_pred))
    max_pred = max(pred_counts.values()) if pred_counts else 0
    max_true = max(true_counts.values()) if true_counts else 0

    return {
        "n": n,
        "accuracy": safe_div(correct, n),
        "balanced_accuracy": mean(recalls),
        "macro_f1": mean(f1s),
        "per_class": per_class,
        "true_counts": true_counts,
        "pred_counts": pred_counts,
        "majority_label": majority_label,
        "majority_accuracy": majority["accuracy"],
        "majority_balanced_accuracy": majority["balanced_accuracy"],
        "majority_macro_f1": majority["macro_f1"],
        "one_class_pred": len(pred_unique) == 1,
        "pred_skew": safe_div(max_pred, n),
        "true_skew": safe_div(max_true, n),
    }

def binary_metrics_no_majority(y_true, y_pred):
    labels = [0, 1]
    n = len(y_true)
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    recalls = []
    f1s = []
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2 * precision * recall, precision + recall)
        recalls.append(recall)
        f1s.append(f1)
    return {
        "accuracy": safe_div(correct, n),
        "balanced_accuracy": mean(recalls),
        "macro_f1": mean(f1s),
    }

def load_runs_from_csv(src):
    rows_by_run = defaultdict(list)
    with src["path"].open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            task = row.get("task") or "unknown"
            policy = row.get("policy") or row.get("label_policy") or "unknown"
            recipe = row.get("recipe") or "unknown"
            fold_id = row.get("fold_id") or row.get("fold") or "unknown"
            seed = row.get("seed") or "unknown"
            run_id = row.get("run_id") or f"{task}-{policy}-{recipe}-{fold_id}-{seed}"
            key = (str(run_id), task, policy, recipe, str(fold_id), str(seed))
            rows_by_run[key].append(row)

    runs = []
    for (run_id, task, policy, recipe, fold_id, seed), rows in sorted(
        rows_by_run.items(),
        key=lambda item: (
            item[0][1],
            item[0][2],
            item[0][3],
            int(float(item[0][4])) if str(item[0][4]).replace(".", "", 1).isdigit() else 999,
            int(float(item[0][0])) if str(item[0][0]).replace(".", "", 1).isdigit() else 9999,
        ),
    ):
        y_true = [to_int(r.get("y_true")) for r in rows]
        y_pred = [to_int(r.get("y_pred")) for r in rows]
        if any(v is None for v in y_true + y_pred):
            raise SystemExit(f"ERROR missing y_true/y_pred in {src['path']}")
        metrics = binary_metrics(y_true, y_pred)
        runs.append({
            "matrix": src["matrix"],
            "modality": src["modality"],
            "representation": src["representation"],
            "source_csv": str(src["path"]),
            "source_json": str(src["json"]),
            "run_id": int(float(run_id)) if str(run_id).replace(".", "", 1).isdigit() else run_id,
            "task": task,
            "policy": policy,
            "recipe": recipe,
            "fold_id": int(float(fold_id)) if str(fold_id).replace(".", "", 1).isdigit() else fold_id,
            "seed": int(float(seed)) if str(seed).replace(".", "", 1).isdigit() else seed,
            **metrics,
        })
    return runs

all_runs = []
source_counts = {}
for src in SOURCES:
    runs = load_runs_from_csv(src)
    all_runs.extend(runs)
    source_counts[str(src["path"])] = {
        "runs": len(runs),
        "rows": sum(r["n"] for r in runs),
    }

def group_runs(runs, fields):
    grouped = defaultdict(list)
    for run in runs:
        key = tuple(run[f] for f in fields)
        grouped[key].append(run)
    out = []
    for key, items in grouped.items():
        macro_vals = [r["macro_f1"] for r in items]
        bal_vals = [r["balanced_accuracy"] for r in items]
        acc_vals = [r["accuracy"] for r in items]
        majority_macro_vals = [r["majority_macro_f1"] for r in items]
        majority_bal_vals = [r["majority_balanced_accuracy"] for r in items]
        pred_skew_vals = [r["pred_skew"] for r in items]
        true_skew_vals = [r["true_skew"] for r in items]
        fold_macro_means = defaultdict(list)
        for r in items:
            fold_macro_means[r["fold_id"]].append(r["macro_f1"])
        fold_means = [mean(v) for v in fold_macro_means.values()]
        row = {field: value for field, value in zip(fields, key)}
        row.update({
            "runs": len(items),
            "n_samples": sum(r["n"] for r in items),
            "macro_f1_mean": mean(macro_vals),
            "macro_f1_std": std(macro_vals),
            "macro_f1_min": min(macro_vals),
            "macro_f1_max": max(macro_vals),
            "balanced_accuracy_mean": mean(bal_vals),
            "balanced_accuracy_std": std(bal_vals),
            "accuracy_mean": mean(acc_vals),
            "majority_macro_f1_mean": mean(majority_macro_vals),
            "majority_balanced_accuracy_mean": mean(majority_bal_vals),
            "delta_macro_f1_vs_majority": mean(macro_vals) - mean(majority_macro_vals),
            "delta_bal_acc_vs_majority": mean(bal_vals) - mean(majority_bal_vals),
            "beat_majority_macro_runs": sum(1 for r in items if r["macro_f1"] > r["majority_macro_f1"]),
            "beat_majority_bal_acc_runs": sum(1 for r in items if r["balanced_accuracy"] > r["majority_balanced_accuracy"]),
            "one_class_runs": sum(1 for r in items if r["one_class_pred"]),
            "pred_skew_mean": mean(pred_skew_vals),
            "true_skew_mean": mean(true_skew_vals),
            "fold_macro_range": (max(fold_means) - min(fold_means)) if fold_means else math.nan,
            "weakest_fold_id": min(fold_macro_means, key=lambda f: mean(fold_macro_means[f])) if fold_macro_means else None,
            "weakest_fold_macro_f1": min(fold_means) if fold_means else math.nan,
        })
        labels = []
        if row["delta_macro_f1_vs_majority"] <= 0.01:
            labels.append("majority_not_clearly_beaten")
        if row["balanced_accuracy_mean"] < 0.52:
            labels.append("weak_signal_near_chance")
        if row["one_class_runs"] > 0:
            labels.append("prediction_collapse")
        if row["pred_skew_mean"] >= 0.70:
            labels.append("prediction_skew")
        if row["fold_macro_range"] >= 0.08:
            labels.append("fold_specific_instability")
        if not labels:
            labels.append("no_major_failure_flag")
        row["failure_labels"] = labels
        out.append(row)
    return sorted(out, key=lambda r: tuple(str(r.get(f, "")) for f in fields))

aggregate_fields = ["matrix", "modality", "representation", "task", "policy", "recipe"]
aggregate = group_runs(all_runs, aggregate_fields)
fold_summary = group_runs(all_runs, aggregate_fields + ["fold_id"])

# Best policy summary from label-policy matrix.
label_rows = [r for r in aggregate if r["matrix"] == "label_policy_ablation"]
best_policy_by_modality_task = []
for key in sorted({(r["modality"], r["task"]) for r in label_rows}):
    rows = [r for r in label_rows if (r["modality"], r["task"]) == key]
    best = max(rows, key=lambda r: r["macro_f1_mean"])
    best_policy_by_modality_task.append({
        "modality": key[0],
        "task": key[1],
        "best_policy": best["policy"],
        "best_recipe": best["recipe"],
        "macro_f1_mean": best["macro_f1_mean"],
        "balanced_accuracy_mean": best["balanced_accuracy_mean"],
    })

# Best representation summary for broader matrix.
broad_rows = [r for r in aggregate if r["matrix"] == "broader_single_modality"]
best_representation_by_modality_task = []
for key in sorted({(r["modality"], r["task"]) for r in broad_rows}):
    rows = [r for r in broad_rows if (r["modality"], r["task"]) == key]
    best = max(rows, key=lambda r: r["macro_f1_mean"])
    best_representation_by_modality_task.append({
        "modality": key[0],
        "task": key[1],
        "best_representation": best["representation"],
        "best_policy": best["policy"],
        "best_recipe": best["recipe"],
        "macro_f1_mean": best["macro_f1_mean"],
        "balanced_accuracy_mean": best["balanced_accuracy_mean"],
    })

# Cross-modality overlap for weak folds in label-policy mainline.
weak_fold_overlap = []
for task in sorted({r["task"] for r in label_rows}):
    eeg_folds = [
        r for r in fold_summary
        if r["matrix"] == "label_policy_ablation" and r["modality"] == "EEG" and r["task"] == task
    ]
    emg_folds = [
        r for r in fold_summary
        if r["matrix"] == "label_policy_ablation" and r["modality"] == "EMG" and r["task"] == task
    ]
    # Consider bottom 2 fold-policy-recipe rows as weak indicators.
    eeg_bottom = sorted(eeg_folds, key=lambda r: r["macro_f1_mean"])[:2]
    emg_bottom = sorted(emg_folds, key=lambda r: r["macro_f1_mean"])[:2]
    eeg_set = {r["fold_id"] for r in eeg_bottom}
    emg_set = {r["fold_id"] for r in emg_bottom}
    weak_fold_overlap.append({
        "task": task,
        "eeg_bottom_fold_ids": sorted(eeg_set),
        "emg_bottom_fold_ids": sorted(emg_set),
        "shared_bottom_fold_ids": sorted(eeg_set & emg_set),
        "interpretation": "shared_failure_signal" if eeg_set & emg_set else "complementary_or_policy_specific_failure_signal",
    })

# Failure-label counts.
failure_label_counts = defaultdict(int)
for row in aggregate:
    for label in row["failure_labels"]:
        failure_label_counts[label] += 1

policy_set = {x["best_policy"] for x in best_policy_by_modality_task}
policy_instability = len(policy_set) > 1
broad_rep_set = {(x["modality"], x["best_representation"]) for x in best_representation_by_modality_task}

recommendation = {
    "recommended_next_objective": "calibration_and_fold_difficulty_analysis",
    "rationale": [
        "Most aggregate rows remain close to chance/majority baselines.",
        "Best label policies are mixed by modality/task, so no global label policy should be locked.",
        "Before architecture, augmentation, DG, or fusion, inspect fold difficulty and calibration/threshold behavior on existing predictions.",
    ],
}
if any(row["failure_labels"] == ["no_major_failure_flag"] for row in aggregate):
    recommendation["rationale"].append("Some rows are not hard failures, but gains are still smoke-level and need robustness evidence.")
if policy_instability:
    recommendation["rationale"].append("Policy instability is present across modality/task winners.")
if any(x["shared_bottom_fold_ids"] for x in weak_fold_overlap):
    recommendation["rationale"].append("Some weak-fold overlap exists across modalities, suggesting split/subject difficulty should be inspected.")
else:
    recommendation["rationale"].append("Weak-fold overlap is not dominant, so complementary errors may be worth analyzing later, but fusion remains unauthorized.")

report = {
    "status": "failure_analysis_complete_pending_review",
    "created_or_updated_utc": NOW,
    "objective": "I-DARE controlled failure analysis",
    "evidence_level": "post-hoc analysis of existing smoke/stabilization outputs; no new training",
    "source_counts": source_counts,
    "aggregate": aggregate,
    "fold_summary_csv": str(OUT_CSV),
    "best_policy_by_modality_task": best_policy_by_modality_task,
    "best_representation_by_modality_task": best_representation_by_modality_task,
    "weak_fold_overlap": weak_fold_overlap,
    "failure_label_counts": dict(sorted(failure_label_counts.items())),
    "recommendation": recommendation,
    "not_authorized": [
        "new training from this report",
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "locking final global label policy",
        "architecture ablation",
        "augmentation",
        "SupCon / VREx / domain generalization",
    ],
}

OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

csv_fields = [
    "matrix", "modality", "representation", "task", "policy", "recipe", "fold_id",
    "runs", "n_samples", "macro_f1_mean", "balanced_accuracy_mean", "accuracy_mean",
    "majority_macro_f1_mean", "majority_balanced_accuracy_mean",
    "delta_macro_f1_vs_majority", "delta_bal_acc_vs_majority",
    "pred_skew_mean", "true_skew_mean", "one_class_runs", "failure_labels",
]
with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=csv_fields)
    writer.writeheader()
    for row in fold_summary:
        out = {k: row.get(k) for k in csv_fields}
        out["failure_labels"] = ";".join(row["failure_labels"])
        writer.writerow(out)

def md_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join(str(v) for v in row) + " |" for row in rows)
    return lines

md = [
    "# I-DARE Failure Analysis Report",
    "",
    "## Status",
    "",
    "Failure analysis complete; pending human review.",
    "",
    "No new training was run for this report.",
    "",
    "Evidence level: post-hoc analysis of existing smoke/stabilization outputs, not final LOSO performance.",
    "",
    "## Validation",
    "",
    f"- Total prediction sources analyzed: {len(SOURCES)}",
    f"- Total reconstructed runs: {len(all_runs)}",
    f"- Fold summary CSV: `{OUT_CSV}`",
    "",
    "## Failure-label counts",
    "",
]
md.extend(md_table(["Failure label", "Aggregate rows"], [[k, v] for k, v in sorted(failure_label_counts.items())]))
md.extend([
    "",
    "## Best label policy by modality/task",
    "",
])
md.extend(md_table(
    ["Modality", "Task", "Best policy", "Recipe", "Macro F1", "Balanced acc"],
    [
        [r["modality"], r["task"], f"`{r['best_policy']}`", f"`{r['best_recipe']}`", fmt(r["macro_f1_mean"]), fmt(r["balanced_accuracy_mean"])]
        for r in best_policy_by_modality_task
    ],
))
md.extend([
    "",
    "## Best representation by modality/task in broader single-modality matrix",
    "",
])
md.extend(md_table(
    ["Modality", "Task", "Best representation", "Policy", "Recipe", "Macro F1", "Balanced acc"],
    [
        [r["modality"], r["task"], r["best_representation"], f"`{r['best_policy']}`", f"`{r['best_recipe']}`", fmt(r["macro_f1_mean"]), fmt(r["balanced_accuracy_mean"])]
        for r in best_representation_by_modality_task
    ],
))
md.extend([
    "",
    "## Aggregate failure map",
    "",
])
display_rows = sorted(aggregate, key=lambda r: (r["matrix"], r["modality"], r["task"], r["representation"], r["policy"], r["recipe"]))
md.extend(md_table(
    ["Matrix", "Modality", "Representation", "Task", "Policy", "Recipe", "Macro F1", "Bal acc", "Delta macro vs majority", "Pred skew", "Weakest fold", "Labels"],
    [
        [
            r["matrix"],
            r["modality"],
            r["representation"],
            r["task"],
            f"`{r['policy']}`",
            f"`{r['recipe']}`",
            fmt(r["macro_f1_mean"]),
            fmt(r["balanced_accuracy_mean"]),
            fmt(r["delta_macro_f1_vs_majority"]),
            fmt(r["pred_skew_mean"]),
            r["weakest_fold_id"],
            ", ".join(f"`{x}`" for x in r["failure_labels"]),
        ]
        for r in display_rows
    ],
))
md.extend([
    "",
    "## Cross-modality weak-fold overlap",
    "",
])
md.extend(md_table(
    ["Task", "EEG bottom folds", "EMG bottom folds", "Shared", "Interpretation"],
    [
        [r["task"], r["eeg_bottom_fold_ids"], r["emg_bottom_fold_ids"], r["shared_bottom_fold_ids"], r["interpretation"]]
        for r in weak_fold_overlap
    ],
))
md.extend([
    "",
    "## Interpretation",
    "",
    "- Current evidence remains smoke/stabilization-level and close to majority/chance behavior in many aggregates.",
    "- Label-policy winners remain mixed by modality/task; no final global label policy should be locked.",
    "- BSL-stats and label-policy changes do not yet justify fusion, architecture escalation, or final claims.",
    "- The next useful improvement step should focus on calibration and fold/subject difficulty, using existing predictions first.",
    "",
    "## Recommended next objective",
    "",
    f"`{recommendation['recommended_next_objective']}`",
    "",
])
md.extend(f"- {item}" for item in recommendation["rationale"])
md.extend([
    "",
    "## Not authorized from this report",
    "",
])
md.extend(f"- {item}" for item in report["not_authorized"])
md.extend([
    "",
    "## Next allowed step",
    "",
    "Human review / closeout of this failure-analysis report. After review, create one explicit follow-up objective if needed.",
    "",
])
OUT_MD.write_text("\n".join(md), encoding="utf-8")

# Update roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
new_row = "| I-DARE controlled failure analysis report | post-hoc failure analysis complete from existing outputs; pending human review | yes | `docs/idare_failure_analysis_report.md` | Human review / closeout before choosing calibration, fold-difficulty, robustness, or model-change objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work. |"
if new_row not in project_md:
    anchor = "| EEG+EMG fusion | not started intentionally | no |"
    if anchor in project_md:
        project_md = project_md.replace(anchor, new_row + "\n" + anchor)
    else:
        project_md += "\n" + new_row + "\n"

decision_bullet = "- Controlled I-DARE failure analysis is complete in `docs/idare_failure_analysis_report.md`; next work is human review/closeout, not new training or fusion."
if decision_bullet not in project_md:
    marker = "## Documentation Gap Closed by This File"
    if marker in project_md:
        project_md = project_md.replace(marker, decision_bullet + "\n\n" + marker)
    else:
        project_md += "\n" + decision_bullet + "\n"
PROJECT_MD.write_text(project_md, encoding="utf-8")

project = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
project.setdefault("decisions", {})
project["decisions"]["idare_failure_analysis_report"] = {
    "status": "complete_pending_review",
    "evidence": str(OUT_MD),
    "evidence_json": str(OUT_JSON),
    "fold_summary_csv": str(OUT_CSV),
    "evidence_level": report["evidence_level"],
    "recommendation": recommendation,
    "next_allowed_step": "Human review / closeout of failure-analysis report.",
    "not_authorized": report["not_authorized"],
}
project["failure_analysis_report"] = {
    "status": "complete_pending_review",
    "evidence": str(OUT_MD),
    "evidence_json": str(OUT_JSON),
    "next_allowed_step": "Human review / closeout before any follow-up objective.",
}
PROJECT_JSON.write_text(json.dumps(project, indent=2, sort_keys=True) + "\n", encoding="utf-8")

print("OK_FAILURE_ANALYSIS_REPORT_WRITTEN")
print(OUT_MD)
print(OUT_JSON)
print(OUT_CSV)
PY
  echo

  echo "===== 3) validate generated docs ====="
  "$PY" - <<'PY'
import json, csv
from pathlib import Path

for p in [
    Path("docs/idare_failure_analysis_report.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")

with Path("docs/idare_failure_analysis_fold_summary.csv").open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
print("fold_summary_rows=", len(rows))
if not rows:
    raise SystemExit("ERROR empty fold summary")
PY

  grep -n "## Status\|## Failure-label counts\|## Aggregate failure map\|## Recommended next objective\|## Next allowed step" docs/idare_failure_analysis_report.md
  grep -n "I-DARE controlled failure analysis report\|failure analysis is complete" docs/project_status_current.md
  echo

  echo "===== 4) file list ====="
  ls -lh \
    docs/idare_failure_analysis_report.md \
    docs/idare_failure_analysis_report.json \
    docs/idare_failure_analysis_fold_summary.csv \
    docs/project_status_current.md \
    docs/project_status_current.json
  echo

  echo "===== 5) status before commit ====="
  git status --short --branch
  echo

  echo "===== 6) commit and push failure analysis report ====="
  git add \
    docs/idare_failure_analysis_report.md \
    docs/idare_failure_analysis_report.json \
    docs/idare_failure_analysis_fold_summary.csv \
    docs/project_status_current.md \
    docs/project_status_current.json

  git commit -m "analysis: add I-DARE failure analysis report"
  git push origin main
  echo

  echo "===== 7) final status ====="
  git status --short --branch
  echo "LOG_SAVED_TO=$LOG"
} 2>&1 | tee "$LOG"
