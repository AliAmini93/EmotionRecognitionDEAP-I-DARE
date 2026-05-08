#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start validation-only calibration protocol analysis ====="
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
import numpy
import pandas
print("OK_IMPORTS")
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repo is not clean; commit/stash current changes before running calibration protocol analysis."
  git status --short --branch
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required committed inputs ====="
ls -lh \
  docs/idare_calibration_protocol_objective.md \
  docs/idare_calibration_protocol_objective.json \
  docs/idare_calibration_subject_generalization_review_status.md \
  docs/idare_calibration_subject_generalization_report.md \
  docs/idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv \
  docs/idare_broader_eval_eeg_bsl_stats_primary_predictions.csv \
  docs/idare_broader_eval_emg_feature_only_primary_predictions.csv \
  docs/idare_broader_eval_emg_bsl_stats_primary_predictions.csv \
  docs/idare_label_policy_ablation_eeg_primary_predictions.csv \
  docs/idare_label_policy_ablation_emg_primary_predictions.csv
echo

echo "===== 3) generate validation-only calibration protocol report ====="
"$PY" - <<'PY'
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

OUT_MD = DOCS / "idare_calibration_protocol_report.md"
OUT_JSON = DOCS / "idare_calibration_protocol_report.json"
OUT_CSV = DOCS / "idare_calibration_protocol_summary.csv"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

SOURCES = [
    {
        "path": DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv",
        "source_group": "broader_eval_primary",
        "modality": "EEG",
        "variant": "stim_bsl_only",
        "default_label_policy": "midpoint_as_high",
    },
    {
        "path": DOCS / "idare_broader_eval_eeg_bsl_stats_primary_predictions.csv",
        "source_group": "broader_eval_primary",
        "modality": "EEG",
        "variant": "bsl_stats",
        "default_label_policy": "midpoint_as_high",
    },
    {
        "path": DOCS / "idare_broader_eval_emg_feature_only_primary_predictions.csv",
        "source_group": "broader_eval_primary",
        "modality": "EMG",
        "variant": "feature_only",
        "default_label_policy": "midpoint_as_high",
    },
    {
        "path": DOCS / "idare_broader_eval_emg_bsl_stats_primary_predictions.csv",
        "source_group": "broader_eval_primary",
        "modality": "EMG",
        "variant": "bsl_stats",
        "default_label_policy": "midpoint_as_high",
    },
    {
        "path": DOCS / "idare_label_policy_ablation_eeg_primary_predictions.csv",
        "source_group": "label_policy_ablation",
        "modality": "EEG",
        "variant": "mainline_label_policy_ablation",
        "default_label_policy": "unknown_from_file",
    },
    {
        "path": DOCS / "idare_label_policy_ablation_emg_primary_predictions.csv",
        "source_group": "label_policy_ablation",
        "modality": "EMG",
        "variant": "mainline_label_policy_ablation",
        "default_label_policy": "unknown_from_file",
    },
]

REQUIRED_CONTEXT = [
    DOCS / "idare_calibration_protocol_objective.md",
    DOCS / "idare_calibration_protocol_objective.json",
    DOCS / "idare_calibration_subject_generalization_review_status.md",
    DOCS / "idare_calibration_subject_generalization_report.md",
]

for p in REQUIRED_CONTEXT:
    if not p.exists():
        raise SystemExit(f"ERROR: missing required context file: {p}")

def pick_col(cols, candidates):
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None

def macro_f1_binary(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    vals = []
    for cls in [0, 1]:
        tp = int(((y_true == cls) & (y_pred == cls)).sum())
        fp = int(((y_true != cls) & (y_pred == cls)).sum())
        fn = int(((y_true == cls) & (y_pred != cls)).sum())
        denom = (2 * tp + fp + fn)
        vals.append(0.0 if denom == 0 else (2 * tp / denom))
    return float(np.mean(vals))

def balanced_accuracy_binary(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    vals = []
    for cls in [0, 1]:
        mask = y_true == cls
        denom = int(mask.sum())
        vals.append(0.0 if denom == 0 else float((y_pred[mask] == cls).mean()))
    return float(np.mean(vals))

def metrics_at_threshold(y_true, prob1, threshold):
    y_true = np.asarray(y_true, dtype=int)
    prob1 = np.asarray(prob1, dtype=float)
    y_pred = (prob1 >= float(threshold)).astype(int)
    pred0 = int((y_pred == 0).sum())
    pred1 = int((y_pred == 1).sum())
    return {
        "threshold": float(threshold),
        "n": int(len(y_true)),
        "macro_f1": macro_f1_binary(y_true, y_pred),
        "balanced_accuracy": balanced_accuracy_binary(y_true, y_pred),
        "accuracy": float((y_true == y_pred).mean()) if len(y_true) else 0.0,
        "pred_0": pred0,
        "pred_1": pred1,
        "one_class": bool(pred0 == 0 or pred1 == 0),
    }

def threshold_candidates(prob1):
    # A dense fixed grid is easier to compare across folds and avoids selecting a
    # threshold that exactly encodes one held-out sample.
    grid = np.round(np.linspace(0.05, 0.95, 91), 4)
    extras = np.array([0.1, 0.25, 0.33, 0.4, 0.45, 0.5, 0.55, 0.6, 0.67, 0.75, 0.9])
    return np.unique(np.concatenate([grid, extras]))

def best_threshold(y_true, prob1):
    best = None
    for th in threshold_candidates(prob1):
        m = metrics_at_threshold(y_true, prob1, th)
        candidate = (
            m["macro_f1"],
            m["balanced_accuracy"],
            -abs(float(th) - 0.5),
            -float(th),
        )
        if best is None or candidate > best[0]:
            best = (candidate, m)
    return best[1]

def normalize_predictions(meta):
    p = meta["path"]
    if not p.exists():
        raise SystemExit(f"ERROR: missing prediction file: {p}")
    df = pd.read_csv(p)
    print(f"LOADED {p} rows={len(df)}")
    cols = list(df.columns)

    y_col = pick_col(cols, ["y_true", "true_label", "label", "target", "truth"])
    prob_col = pick_col(cols, ["prob1", "prob_1", "p1", "probability_1", "y_prob", "y_prob1", "pred_prob_1", "prob_positive"])
    pred_col = pick_col(cols, ["y_pred", "pred", "prediction", "pred_label"])
    fold_col = pick_col(cols, ["fold_id", "fold"])
    task_col = pick_col(cols, ["task"])
    recipe_col = pick_col(cols, ["recipe"])
    policy_col = pick_col(cols, ["label_policy", "policy"])
    subject_col = pick_col(cols, ["subject_id", "subject", "subj", "participant_id"])
    seed_col = pick_col(cols, ["seed"])

    missing = []
    for name, col in [
        ("y_true", y_col),
        ("fold_id/fold", fold_col),
        ("task", task_col),
        ("recipe", recipe_col),
    ]:
        if col is None:
            missing.append(name)
    if prob_col is None and pred_col is None:
        missing.append("prob1/prob_1 or y_pred")
    if missing:
        raise SystemExit(f"ERROR: {p} missing required columns: {missing}; columns={cols}")

    out = pd.DataFrame()
    out["source_path"] = str(p)
    out["source_group"] = meta["source_group"]
    out["modality"] = meta["modality"]
    out["variant"] = meta["variant"]
    out["task"] = df[task_col].astype(str)
    out["recipe"] = df[recipe_col].astype(str)
    out["label_policy"] = df[policy_col].astype(str) if policy_col else meta["default_label_policy"]
    out["fold_id"] = pd.to_numeric(df[fold_col], errors="coerce").astype("Int64")
    out["seed"] = pd.to_numeric(df[seed_col], errors="coerce").astype("Int64") if seed_col else pd.Series([11] * len(df), dtype="Int64")
    out["y_true"] = pd.to_numeric(df[y_col], errors="coerce").astype("Int64")

    if prob_col:
        out["prob1"] = pd.to_numeric(df[prob_col], errors="coerce")
    else:
        # Last-resort fallback: only meaningful for default metrics, not true calibration.
        out["prob1"] = pd.to_numeric(df[pred_col], errors="coerce").astype(float)

    if pred_col:
        out["default_pred_file"] = pd.to_numeric(df[pred_col], errors="coerce").fillna(0).astype(int)
    else:
        out["default_pred_file"] = (out["prob1"] >= 0.5).astype(int)

    if subject_col:
        out["subject_id"] = pd.to_numeric(df[subject_col], errors="coerce").astype("Int64")
    else:
        out["subject_id"] = pd.Series([pd.NA] * len(out), dtype="Int64")

    out = out.dropna(subset=["fold_id", "y_true", "prob1"]).copy()
    out["fold_id"] = out["fold_id"].astype(int)
    out["y_true"] = out["y_true"].astype(int)
    out["prob1"] = out["prob1"].astype(float).clip(0.0, 1.0)
    return out

frames = [normalize_predictions(meta) for meta in SOURCES]
all_df = pd.concat(frames, ignore_index=True)

group_cols = ["source_group", "modality", "variant", "task", "label_policy", "recipe"]
summary_rows = []
fold_rows = []

for key, group in all_df.groupby(group_cols, dropna=False):
    g = group.copy()
    folds = sorted(int(f) for f in g["fold_id"].dropna().unique().tolist())
    if len(folds) < 2:
        continue

    y_all = g["y_true"].to_numpy(dtype=int)
    p_all = g["prob1"].to_numpy(dtype=float)

    default_all = metrics_at_threshold(y_all, p_all, 0.5)
    oracle_all = best_threshold(y_all, p_all)

    calibrated_pred = np.zeros(len(g), dtype=int)
    oracle_fold_pred = np.zeros(len(g), dtype=int)

    selected_thresholds = []
    oracle_thresholds = []
    fold_metric_rows = []
    for fold in folds:
        test_mask = (g["fold_id"].to_numpy(dtype=int) == fold)
        train_mask = ~test_mask
        train = g.loc[train_mask]
        test = g.loc[test_mask]
        train_best = best_threshold(train["y_true"].to_numpy(dtype=int), train["prob1"].to_numpy(dtype=float))
        test_default = metrics_at_threshold(test["y_true"].to_numpy(dtype=int), test["prob1"].to_numpy(dtype=float), 0.5)
        test_cal = metrics_at_threshold(test["y_true"].to_numpy(dtype=int), test["prob1"].to_numpy(dtype=float), train_best["threshold"])
        test_oracle = best_threshold(test["y_true"].to_numpy(dtype=int), test["prob1"].to_numpy(dtype=float))

        idx = np.where(test_mask)[0]
        calibrated_pred[idx] = (test["prob1"].to_numpy(dtype=float) >= train_best["threshold"]).astype(int)
        oracle_fold_pred[idx] = (test["prob1"].to_numpy(dtype=float) >= test_oracle["threshold"]).astype(int)

        selected_thresholds.append(float(train_best["threshold"]))
        oracle_thresholds.append(float(test_oracle["threshold"]))

        row = dict(zip(group_cols, key))
        row.update({
            "level": "fold_transfer",
            "fold_id": int(fold),
            "n": int(len(test)),
            "train_selected_threshold": float(train_best["threshold"]),
            "test_oracle_threshold": float(test_oracle["threshold"]),
            "default_macro_f1": test_default["macro_f1"],
            "calibrated_macro_f1": test_cal["macro_f1"],
            "oracle_fold_macro_f1": test_oracle["macro_f1"],
            "calibrated_gain": test_cal["macro_f1"] - test_default["macro_f1"],
            "oracle_gain": test_oracle["macro_f1"] - test_default["macro_f1"],
            "oracle_gap": test_oracle["macro_f1"] - test_cal["macro_f1"],
            "default_balanced_accuracy": test_default["balanced_accuracy"],
            "calibrated_balanced_accuracy": test_cal["balanced_accuracy"],
            "oracle_fold_balanced_accuracy": test_oracle["balanced_accuracy"],
            "default_accuracy": test_default["accuracy"],
            "calibrated_accuracy": test_cal["accuracy"],
            "oracle_fold_accuracy": test_oracle["accuracy"],
            "calibrated_one_class": test_cal["one_class"],
            "calibrated_pred_0": test_cal["pred_0"],
            "calibrated_pred_1": test_cal["pred_1"],
        })
        fold_metric_rows.append(row)
        fold_rows.append(row)

    cal_all = {
        "n": int(len(y_all)),
        "macro_f1": macro_f1_binary(y_all, calibrated_pred),
        "balanced_accuracy": balanced_accuracy_binary(y_all, calibrated_pred),
        "accuracy": float((y_all == calibrated_pred).mean()),
        "pred_0": int((calibrated_pred == 0).sum()),
        "pred_1": int((calibrated_pred == 1).sum()),
        "one_class": bool((calibrated_pred == 0).sum() == 0 or (calibrated_pred == 1).sum() == 0),
    }
    oracle_fold_all = {
        "n": int(len(y_all)),
        "macro_f1": macro_f1_binary(y_all, oracle_fold_pred),
        "balanced_accuracy": balanced_accuracy_binary(y_all, oracle_fold_pred),
        "accuracy": float((y_all == oracle_fold_pred).mean()),
        "pred_0": int((oracle_fold_pred == 0).sum()),
        "pred_1": int((oracle_fold_pred == 1).sum()),
        "one_class": bool((oracle_fold_pred == 0).sum() == 0 or (oracle_fold_pred == 1).sum() == 0),
    }

    selected_thresholds_arr = np.asarray(selected_thresholds, dtype=float)
    oracle_thresholds_arr = np.asarray(oracle_thresholds, dtype=float)
    nonoracle_gain = cal_all["macro_f1"] - default_all["macro_f1"]
    oracle_fold_gain = oracle_fold_all["macro_f1"] - default_all["macro_f1"]
    oracle_overall_gain = oracle_all["macro_f1"] - default_all["macro_f1"]
    oracle_gap = oracle_fold_gain - nonoracle_gain
    threshold_std = float(selected_thresholds_arr.std(ddof=0)) if len(selected_thresholds_arr) else 0.0
    threshold_range = float(selected_thresholds_arr.max() - selected_thresholds_arr.min()) if len(selected_thresholds_arr) else 0.0
    unstable = bool(threshold_std > 0.15 or threshold_range > 0.40)

    pass_like = bool(
        nonoracle_gain >= 0.005
        and oracle_gap <= 0.015
        and not cal_all["one_class"]
        and threshold_std <= 0.20
    )

    row = dict(zip(group_cols, key))
    row.update({
        "level": "overall_leave_one_fold_out",
        "n": int(len(g)),
        "n_folds": int(len(folds)),
        "default_macro_f1": default_all["macro_f1"],
        "calibrated_macro_f1": cal_all["macro_f1"],
        "oracle_fold_macro_f1": oracle_fold_all["macro_f1"],
        "oracle_overall_macro_f1": oracle_all["macro_f1"],
        "calibrated_gain": nonoracle_gain,
        "oracle_fold_gain": oracle_fold_gain,
        "oracle_overall_gain": oracle_overall_gain,
        "oracle_gap": oracle_gap,
        "default_balanced_accuracy": default_all["balanced_accuracy"],
        "calibrated_balanced_accuracy": cal_all["balanced_accuracy"],
        "oracle_fold_balanced_accuracy": oracle_fold_all["balanced_accuracy"],
        "default_accuracy": default_all["accuracy"],
        "calibrated_accuracy": cal_all["accuracy"],
        "oracle_fold_accuracy": oracle_fold_all["accuracy"],
        "calibrated_pred_0": cal_all["pred_0"],
        "calibrated_pred_1": cal_all["pred_1"],
        "calibrated_one_class": cal_all["one_class"],
        "selected_threshold_mean": float(selected_thresholds_arr.mean()),
        "selected_threshold_std": threshold_std,
        "selected_threshold_min": float(selected_thresholds_arr.min()),
        "selected_threshold_max": float(selected_thresholds_arr.max()),
        "selected_threshold_range": threshold_range,
        "oracle_threshold_mean": float(oracle_thresholds_arr.mean()),
        "oracle_threshold_std": float(oracle_thresholds_arr.std(ddof=0)),
        "threshold_unstable": unstable,
        "protocol_pass_like": pass_like,
    })
    summary_rows.append(row)

summary = pd.DataFrame(summary_rows)
fold_summary = pd.DataFrame(fold_rows)

if summary.empty:
    raise SystemExit("ERROR: no calibration protocol groups were generated")

summary = summary.sort_values(["calibrated_gain", "calibrated_macro_f1"], ascending=[False, False]).reset_index(drop=True)
summary.to_csv(OUT_CSV, index=False)

n_groups = int(len(summary))
positive_gain_count = int((summary["calibrated_gain"] > 0).sum())
material_gain_count = int((summary["calibrated_gain"] >= 0.01).sum())
negative_gain_count = int((summary["calibrated_gain"] < 0).sum())
pass_like_count = int(summary["protocol_pass_like"].sum())
unstable_count = int(summary["threshold_unstable"].sum())
collapse_count = int(summary["calibrated_one_class"].sum())

mean_gain = float(summary["calibrated_gain"].mean())
median_gain = float(summary["calibrated_gain"].median())
max_gain = float(summary["calibrated_gain"].max())
mean_oracle_gap = float(summary["oracle_gap"].mean())
mean_threshold_std = float(summary["selected_threshold_std"].mean())

if pass_like_count >= max(2, math.ceil(0.25 * n_groups)) and mean_gain >= 0.005 and mean_oracle_gap <= 0.02:
    diagnosis = "validation_calibration_partially_supported"
    recommended_next = "controlled_calibration_evaluation_objective"
    recommendation_reason = [
        "Several groups show validation-only calibration gains.",
        "Oracle-vs-non-oracle gap is not too large on average.",
        "A controlled calibration evaluation can be justified before model changes.",
    ]
elif unstable_count >= max(2, math.ceil(0.25 * n_groups)) or mean_oracle_gap > 0.02:
    diagnosis = "calibration_protocol_not_sufficient_due_to_instability"
    recommended_next = "subject_stratified_generalization_objective"
    recommendation_reason = [
        "Validation-only calibration does not reliably convert oracle gains into stable held-out gains.",
        "Thresholds remain unstable across folds/groups.",
        "Subject/fold generalization should be addressed before using calibration as a fix.",
    ]
else:
    diagnosis = "calibration_not_sufficient_as_primary_fix"
    recommended_next = "representation_label_task_redesign_objective"
    recommendation_reason = [
        "Validation-only calibration gains are too small or inconsistent.",
        "Calibration alone should not be treated as the main fix.",
        "A representation/label-task redesign objective is more appropriate after review.",
    ]

top_rows = summary.head(20).to_dict(orient="records")
bad_rows = summary.sort_values(["calibrated_gain", "calibrated_macro_f1"], ascending=[True, True]).head(12).to_dict(orient="records")
unstable_rows = summary.sort_values(["selected_threshold_std", "selected_threshold_range"], ascending=[False, False]).head(15).to_dict(orient="records")

report = {
    "status": "complete_pending_review",
    "created_or_updated_utc": NOW,
    "objective": "docs/idare_calibration_protocol_objective.md",
    "evidence_level": "read-only validation-only calibration protocol simulation from existing prediction outputs; no new model training; no final performance claim",
    "protocol_summary": {
        "n_prediction_rows": int(len(all_df)),
        "n_protocol_groups": n_groups,
        "positive_gain_count": positive_gain_count,
        "material_gain_count_ge_0p01": material_gain_count,
        "negative_gain_count": negative_gain_count,
        "pass_like_count": pass_like_count,
        "threshold_unstable_count": unstable_count,
        "calibrated_one_class_count": collapse_count,
        "mean_calibrated_macro_f1_gain": mean_gain,
        "median_calibrated_macro_f1_gain": median_gain,
        "max_calibrated_macro_f1_gain": max_gain,
        "mean_oracle_gap": mean_oracle_gap,
        "mean_selected_threshold_std": mean_threshold_std,
        "diagnosis": diagnosis,
        "recommended_next_objective": recommended_next,
        "recommendation_reason": recommendation_reason,
    },
    "protocol_definition": {
        "name": "leave_one_fold_out_threshold_transfer",
        "threshold_selection": "For each protocol group and target fold, choose the threshold that maximizes macro-F1 on all other folds only.",
        "threshold_application": "Apply that threshold to the target fold predictions.",
        "oracle_separation": "Oracle fold thresholds are computed only as diagnostic upper bounds and are not counted as valid calibrated performance.",
        "leakage_guard": "The target fold labels are not used to select the threshold applied to that target fold.",
    },
    "outputs": {
        "report_md": str(OUT_MD),
        "report_json": str(OUT_JSON),
        "summary_csv": str(OUT_CSV),
    },
    "top_validation_calibration_gains": top_rows,
    "worst_validation_calibration_gains": bad_rows,
    "threshold_instability_examples": unstable_rows,
    "not_authorized": [
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "final global label-policy lock",
        "new model training",
        "architecture ablation for improvement",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "broad hyperparameter search",
        "mainline change",
    ],
}
OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def fmt(x, digits=4):
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.{digits}f}"
    return str(x)

md = []
md.append("# I-DARE Validation-only Calibration Protocol Report")
md.append("")
md.append("## Status")
md.append("")
md.append("Calibration protocol analysis complete; pending human review.")
md.append("")
md.append(f"Generated UTC: `{NOW}`")
md.append("")
md.append("This report is read-only and uses existing prediction outputs only.")
md.append("")
md.append("No new model training was run.")
md.append("")
md.append("## Protocol Summary")
md.append("")
md.append("| Item | Value |")
md.append("|---|---:|")
for label, value in [
    ("Prediction rows loaded", len(all_df)),
    ("Protocol groups", n_groups),
    ("Positive validation-calibration gain groups", positive_gain_count),
    ("Material gain groups >= 0.01", material_gain_count),
    ("Negative gain groups", negative_gain_count),
    ("Pass-like groups", pass_like_count),
    ("Threshold-unstable groups", unstable_count),
    ("Calibrated one-class groups", collapse_count),
    ("Mean calibrated macro-F1 gain", mean_gain),
    ("Median calibrated macro-F1 gain", median_gain),
    ("Max calibrated macro-F1 gain", max_gain),
    ("Mean oracle gap", mean_oracle_gap),
    ("Mean selected-threshold std", mean_threshold_std),
]:
    md.append(f"| {label} | {fmt(value)} |")
md.append(f"| Diagnosis | `{diagnosis}` |")
md.append(f"| Recommended next objective | `{recommended_next}` |")
md.append("")
md.append("## Protocol Definition")
md.append("")
md.append("For each modality/variant/task/policy/recipe group and target fold:")
md.append("")
md.append("1. choose the threshold that maximizes macro-F1 on all **other** folds only;")
md.append("2. apply that threshold to the target fold;")
md.append("3. compute calibrated metrics on the target fold;")
md.append("4. compute oracle fold threshold only as a diagnostic upper bound.")
md.append("")
md.append("The target fold labels are not used to select the threshold applied to that same target fold.")
md.append("")
md.append("## Top Validation-calibration Gains")
md.append("")
cols = [
    "source_group", "modality", "variant", "task", "label_policy", "recipe",
    "default_macro_f1", "calibrated_macro_f1", "calibrated_gain",
    "oracle_fold_gain", "oracle_gap", "selected_threshold_mean", "selected_threshold_std",
    "protocol_pass_like",
]
md.append("| Source | Mod | Variant | Task | Policy | Recipe | Default F1 | Cal F1 | Gain | Oracle gain | Oracle gap | Th mean | Th std | Pass-like |")
md.append("|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
for _, r in summary.head(15).iterrows():
    md.append(
        f"| {r['source_group']} | {r['modality']} | {r['variant']} | {r['task']} | {r['label_policy']} | {r['recipe']} | "
        f"{fmt(r['default_macro_f1'])} | {fmt(r['calibrated_macro_f1'])} | {fmt(r['calibrated_gain'])} | "
        f"{fmt(r['oracle_fold_gain'])} | {fmt(r['oracle_gap'])} | {fmt(r['selected_threshold_mean'])} | {fmt(r['selected_threshold_std'])} | {r['protocol_pass_like']} |"
    )
md.append("")
md.append("## Worst Validation-calibration Gains")
md.append("")
md.append("| Source | Mod | Variant | Task | Policy | Recipe | Default F1 | Cal F1 | Gain | Oracle gap | Th std |")
md.append("|---|---|---|---|---|---|---:|---:|---:|---:|---:|")
for _, r in summary.sort_values(["calibrated_gain", "calibrated_macro_f1"], ascending=[True, True]).head(12).iterrows():
    md.append(
        f"| {r['source_group']} | {r['modality']} | {r['variant']} | {r['task']} | {r['label_policy']} | {r['recipe']} | "
        f"{fmt(r['default_macro_f1'])} | {fmt(r['calibrated_macro_f1'])} | {fmt(r['calibrated_gain'])} | "
        f"{fmt(r['oracle_gap'])} | {fmt(r['selected_threshold_std'])} |"
    )
md.append("")
md.append("## Threshold Instability Examples")
md.append("")
md.append("| Source | Mod | Variant | Task | Policy | Recipe | Th mean | Th std | Th min | Th max | Range |")
md.append("|---|---|---|---|---|---|---:|---:|---:|---:|---:|")
for _, r in summary.sort_values(["selected_threshold_std", "selected_threshold_range"], ascending=[False, False]).head(15).iterrows():
    md.append(
        f"| {r['source_group']} | {r['modality']} | {r['variant']} | {r['task']} | {r['label_policy']} | {r['recipe']} | "
        f"{fmt(r['selected_threshold_mean'])} | {fmt(r['selected_threshold_std'])} | {fmt(r['selected_threshold_min'])} | {fmt(r['selected_threshold_max'])} | {fmt(r['selected_threshold_range'])} |"
    )
md.append("")
md.append("## Recommendation")
md.append("")
for reason in recommendation_reason:
    md.append(f"- {reason}")
md.append("")
md.append(f"Recommended next objective: `{recommended_next}`")
md.append("")
md.append("## Not Authorized")
md.append("")
for item in report["not_authorized"]:
    md.append(f"- {item}")
md.append("")
md.append("## Next Allowed Step")
md.append("")
md.append("Human review / closeout of this calibration protocol report.")
md.append("")
md.append("Do not start fusion, architecture changes, augmentation, domain generalization, or final claims from this report alone.")
md.append("")
OUT_MD.write_text("\n".join(md), encoding="utf-8")

project_md = PROJECT_MD.read_text(encoding="utf-8")
row = "| I-DARE calibration protocol report | validation-only calibration protocol analysis complete; pending human review | yes | `docs/idare_calibration_protocol_report.md` | Human review / closeout before the next diagnostic or fix objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |"
if "I-DARE calibration protocol report" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE calibration protocol objective |"):
            out.append(row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert calibration protocol report row in project_status_current.md")
    project_md = "\n".join(out) + "\n"

bullet = f"- Validation-only calibration protocol analysis is complete in `docs/idare_calibration_protocol_report.md`; diagnosis is `{diagnosis}`, recommended next objective is `{recommended_next}`, and human review is required before any next step."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: project status marker not found")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)

PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_calibration_protocol_report"] = {
    "status": "complete_pending_review",
    "evidence": str(OUT_MD),
    "evidence_json": str(OUT_JSON),
    "summary_csv": str(OUT_CSV),
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next,
    "new_model_training_run": False,
    "protocol": report["protocol_definition"],
    "protocol_summary": report["protocol_summary"],
    "not_authorized": report["not_authorized"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_CALIBRATION_PROTOCOL_REPORT_WRITTEN")
print(OUT_MD)
print(OUT_JSON)
print(OUT_CSV)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next)
PY
echo

echo "===== 4) validate generated outputs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path
json.loads(Path("docs/idare_calibration_protocol_report.json").read_text(encoding="utf-8"))
print("OK_JSON")
with Path("docs/idare_calibration_protocol_summary.csv").open(newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
print("summary_rows=", len(rows))
if not rows:
    raise SystemExit("ERROR: empty calibration protocol summary")
PY

grep -n "## Status\|## Protocol Summary\|## Top Validation\|## Worst Validation\|## Threshold Instability\|## Recommendation\|## Next Allowed Step" docs/idare_calibration_protocol_report.md
grep -n "calibration protocol report" docs/project_status_current.md
echo

echo "===== 5) file list ====="
ls -lh \
  docs/idare_calibration_protocol_report.md \
  docs/idare_calibration_protocol_report.json \
  docs/idare_calibration_protocol_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push calibration protocol report ====="
git add \
  docs/idare_calibration_protocol_report.md \
  docs/idare_calibration_protocol_report.json \
  docs/idare_calibration_protocol_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "analysis: add I-DARE calibration protocol report"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_calibration_protocol_report.log"
