#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start root-cause diagnostic report generation ====="
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
try:
    import numpy as np
    import pandas as pd
except Exception as e:
    print("IMPORT_ERROR:", repr(e))
    raise
print("OK_IMPORTS")
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repo is not clean; commit/stash current changes before root-cause diagnostic report."
  git status --short --branch
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) generate read-only root-cause diagnostic report from existing committed outputs ====="
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

OUT_MD = DOCS / "idare_root_cause_diagnostic_report.md"
OUT_JSON = DOCS / "idare_root_cause_diagnostic_report.json"
OUT_SUBJECT = DOCS / "idare_root_cause_subject_summary.csv"
OUT_CAL = DOCS / "idare_root_cause_calibration_summary.csv"
OUT_OVERLAP = DOCS / "idare_root_cause_error_overlap_summary.csv"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

SOURCES = [
    {
        "source_id": "label_eeg_mainline",
        "modality": "EEG",
        "representation": "STIM-BSL-only",
        "family": "label_policy_ablation",
        "pred_csv": DOCS / "idare_label_policy_ablation_eeg_primary_predictions.csv",
        "json": DOCS / "idare_label_policy_ablation_eeg_primary.json",
    },
    {
        "source_id": "label_emg_mainline",
        "modality": "EMG",
        "representation": "feature-only",
        "family": "label_policy_ablation",
        "pred_csv": DOCS / "idare_label_policy_ablation_emg_primary_predictions.csv",
        "json": DOCS / "idare_label_policy_ablation_emg_primary.json",
    },
    {
        "source_id": "broader_eeg_stim_bsl_only",
        "modality": "EEG",
        "representation": "STIM-BSL-only",
        "family": "broader_primary",
        "pred_csv": DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv",
        "json": DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary.json",
    },
    {
        "source_id": "broader_eeg_bsl_stats",
        "modality": "EEG",
        "representation": "STIM-BSL-plus-BSL-stats",
        "family": "broader_primary",
        "pred_csv": DOCS / "idare_broader_eval_eeg_bsl_stats_primary_predictions.csv",
        "json": DOCS / "idare_broader_eval_eeg_bsl_stats_primary.json",
    },
    {
        "source_id": "broader_emg_feature_only",
        "modality": "EMG",
        "representation": "feature-only",
        "family": "broader_primary",
        "pred_csv": DOCS / "idare_broader_eval_emg_feature_only_primary_predictions.csv",
        "json": DOCS / "idare_broader_eval_emg_feature_only_primary.json",
    },
    {
        "source_id": "broader_emg_bsl_stats",
        "modality": "EMG",
        "representation": "feature-plus-BSL-stats",
        "family": "broader_primary",
        "pred_csv": DOCS / "idare_broader_eval_emg_bsl_stats_primary_predictions.csv",
        "json": DOCS / "idare_broader_eval_emg_bsl_stats_primary.json",
    },
]

required = [
    DOCS / "idare_root_cause_diagnostic_objective.md",
    DOCS / "idare_root_cause_diagnostic_objective.json",
    DOCS / "idare_failure_analysis_review_status.md",
    DOCS / "idare_failure_analysis_report.md",
    DOCS / "idare_failure_analysis_report.json",
    DOCS / "idare_failure_analysis_fold_summary.csv",
] + [s["pred_csv"] for s in SOURCES] + [s["json"] for s in SOURCES]

missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("ERROR: missing required files:\n" + "\n".join(missing))


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def binary_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    n = int(len(y_true))
    if n == 0:
        return {
            "n": 0,
            "accuracy": math.nan,
            "balanced_accuracy": math.nan,
            "macro_f1": math.nan,
            "majority_accuracy": math.nan,
            "true_0": 0,
            "true_1": 0,
            "pred_0": 0,
            "pred_1": 0,
            "tn": 0,
            "fp": 0,
            "fn": 0,
            "tp": 0,
            "one_class_pred": False,
        }

    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tp = int(((y_true == 1) & (y_pred == 1)).sum())

    true_0 = int((y_true == 0).sum())
    true_1 = int((y_true == 1).sum())
    pred_0 = int((y_pred == 0).sum())
    pred_1 = int((y_pred == 1).sum())

    f1s = []
    recalls = []
    for label in [0, 1]:
        ltp = int(((y_true == label) & (y_pred == label)).sum())
        lfp = int(((y_true != label) & (y_pred == label)).sum())
        lfn = int(((y_true == label) & (y_pred != label)).sum())
        prec = safe_div(ltp, ltp + lfp)
        rec = safe_div(ltp, ltp + lfn)
        f1 = safe_div(2.0 * prec * rec, prec + rec)
        f1s.append(f1)
        recalls.append(rec)

    majority_accuracy = max(true_0, true_1) / n
    return {
        "n": n,
        "accuracy": float((y_true == y_pred).mean()),
        "balanced_accuracy": float(np.mean(recalls)),
        "macro_f1": float(np.mean(f1s)),
        "majority_accuracy": float(majority_accuracy),
        "true_0": true_0,
        "true_1": true_1,
        "pred_0": pred_0,
        "pred_1": pred_1,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "one_class_pred": bool(len(set(y_pred.tolist())) == 1),
    }


def expected_calibration_error(y_true: np.ndarray, prob1: np.ndarray, bins: int = 10) -> float:
    y_true = np.asarray(y_true, dtype=int)
    prob1 = np.asarray(prob1, dtype=float)
    mask = np.isfinite(prob1)
    y_true = y_true[mask]
    prob1 = prob1[mask]
    if len(prob1) == 0:
        return math.nan

    pred = (prob1 >= 0.5).astype(int)
    conf = np.where(pred == 1, prob1, 1.0 - prob1)
    correct = (pred == y_true).astype(float)

    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    n = len(prob1)
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        if i == bins - 1:
            m = (conf >= lo) & (conf <= hi)
        else:
            m = (conf >= lo) & (conf < hi)
        if not m.any():
            continue
        ece += float(m.mean()) * abs(float(correct[m].mean()) - float(conf[m].mean()))
    return float(ece)


def threshold_sweep(y_true: np.ndarray, prob1: np.ndarray) -> dict[str, Any]:
    y_true = np.asarray(y_true, dtype=int)
    prob1 = np.asarray(prob1, dtype=float)
    mask = np.isfinite(prob1)
    y_true = y_true[mask]
    prob1 = prob1[mask]
    if len(prob1) == 0:
        return {
            "best_threshold": math.nan,
            "best_threshold_macro_f1": math.nan,
            "best_threshold_balanced_accuracy": math.nan,
            "best_threshold_accuracy": math.nan,
            "best_threshold_pred_0": 0,
            "best_threshold_pred_1": 0,
        }
    thresholds = np.unique(np.concatenate([np.linspace(0.05, 0.95, 181), [0.5], prob1]))
    best: dict[str, Any] | None = None
    for th in thresholds:
        pred = (prob1 >= th).astype(int)
        m = binary_metrics(y_true, pred)
        row = {
            "best_threshold": float(th),
            "best_threshold_macro_f1": m["macro_f1"],
            "best_threshold_balanced_accuracy": m["balanced_accuracy"],
            "best_threshold_accuracy": m["accuracy"],
            "best_threshold_pred_0": m["pred_0"],
            "best_threshold_pred_1": m["pred_1"],
        }
        if best is None or row["best_threshold_macro_f1"] > best["best_threshold_macro_f1"]:
            best = row
    assert best is not None
    return best


def group_metrics(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby(group_cols, dropna=False, sort=True):
        if not isinstance(key, tuple):
            key = (key,)
        row = {col: val for col, val in zip(group_cols, key)}
        met = binary_metrics(g["y_true"].to_numpy(), g["y_pred"].to_numpy())
        row.update(met)

        if "prob1" in g.columns:
            prob = pd.to_numeric(g["prob1"], errors="coerce").to_numpy(dtype=float)
            true = g["y_true"].to_numpy(dtype=int)
            finite = np.isfinite(prob)
            if finite.any():
                row.update({
                    "prob1_mean": float(np.mean(prob[finite])),
                    "prob1_std": float(np.std(prob[finite])),
                    "prob1_q05": float(np.quantile(prob[finite], 0.05)),
                    "prob1_median": float(np.median(prob[finite])),
                    "prob1_q95": float(np.quantile(prob[finite], 0.95)),
                    "brier": float(np.mean((prob[finite] - true[finite]) ** 2)),
                    "ece_10": expected_calibration_error(true[finite], prob[finite], bins=10),
                })
                sweep = threshold_sweep(true[finite], prob[finite])
                row.update(sweep)
                row["threshold_macro_f1_gain"] = float(sweep["best_threshold_macro_f1"] - met["macro_f1"])
                row["threshold_balanced_accuracy_gain"] = float(sweep["best_threshold_balanced_accuracy"] - met["balanced_accuracy"])
                row["prediction_skew_abs"] = abs(safe_div(met["pred_1"], met["n"]) - 0.5)
            else:
                row.update({
                    "prob1_mean": math.nan,
                    "prob1_std": math.nan,
                    "prob1_q05": math.nan,
                    "prob1_median": math.nan,
                    "prob1_q95": math.nan,
                    "brier": math.nan,
                    "ece_10": math.nan,
                    "best_threshold": math.nan,
                    "best_threshold_macro_f1": math.nan,
                    "best_threshold_balanced_accuracy": math.nan,
                    "best_threshold_accuracy": math.nan,
                    "best_threshold_pred_0": 0,
                    "best_threshold_pred_1": 0,
                    "threshold_macro_f1_gain": math.nan,
                    "threshold_balanced_accuracy_gain": math.nan,
                    "prediction_skew_abs": abs(safe_div(met["pred_1"], met["n"]) - 0.5),
                })
        rows.append(row)
    return pd.DataFrame(rows)


loaded = {}
metadata = []
for src in SOURCES:
    df = pd.read_csv(src["pred_csv"])
    if "fold" in df.columns and "fold_id" not in df.columns:
        df = df.rename(columns={"fold": "fold_id"})
    if "policy" not in df.columns:
        df["policy"] = "midpoint_as_high"
    for col in ["y_true", "y_pred", "fold_id", "subject_id"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="raise").astype(int)
    if "stimulus_id" in df.columns:
        df["stimulus_id"] = pd.to_numeric(df["stimulus_id"], errors="coerce").astype("Int64")
    else:
        df["stimulus_id"] = df["cache_row"].astype("Int64")
    if "prob1" in df.columns:
        df["prob1"] = pd.to_numeric(df["prob1"], errors="coerce")
    df["source_id"] = src["source_id"]
    df["modality"] = src["modality"]
    df["representation"] = src["representation"]
    df["family"] = src["family"]
    loaded[src["source_id"]] = df
    metadata.append({
        "source_id": src["source_id"],
        "path": str(src["pred_csv"]),
        "json": str(src["json"]),
        "rows": int(len(df)),
        "runs": int(df[["task", "policy", "recipe", "fold_id", "seed"]].drop_duplicates().shape[0]),
        "modalities": sorted(df["modality"].unique().tolist()),
        "tasks": sorted(df["task"].unique().tolist()),
        "policies": sorted(df["policy"].unique().tolist()),
        "recipes": sorted(df["recipe"].unique().tolist()),
        "folds": sorted(int(x) for x in df["fold_id"].unique().tolist()),
        "subjects": int(df["subject_id"].nunique()),
    })

all_df = pd.concat(loaded.values(), ignore_index=True)

subject_summary = group_metrics(
    all_df,
    ["source_id", "family", "modality", "representation", "task", "policy", "recipe", "subject_id"],
)
subject_summary = subject_summary.sort_values(
    ["macro_f1", "balanced_accuracy", "n"],
    ascending=[True, True, False],
).reset_index(drop=True)
subject_summary.to_csv(OUT_SUBJECT, index=False)

calibration_summary = group_metrics(
    all_df,
    ["source_id", "family", "modality", "representation", "task", "policy", "recipe", "fold_id"],
)
calibration_summary = calibration_summary.sort_values(
    ["source_id", "task", "policy", "recipe", "fold_id"],
).reset_index(drop=True)
calibration_summary.to_csv(OUT_CAL, index=False)

aggregate_summary = group_metrics(
    all_df,
    ["source_id", "family", "modality", "representation", "task", "policy", "recipe"],
)
fold_ranges = (
    calibration_summary
    .groupby(["source_id", "family", "modality", "representation", "task", "policy", "recipe"], dropna=False)
    .agg(
        fold_macro_f1_min=("macro_f1", "min"),
        fold_macro_f1_max=("macro_f1", "max"),
        fold_macro_f1_std=("macro_f1", "std"),
        fold_bal_acc_min=("balanced_accuracy", "min"),
        fold_bal_acc_max=("balanced_accuracy", "max"),
        fold_bal_acc_std=("balanced_accuracy", "std"),
    )
    .reset_index()
)
fold_ranges["fold_macro_f1_range"] = fold_ranges["fold_macro_f1_max"] - fold_ranges["fold_macro_f1_min"]
fold_ranges["fold_bal_acc_range"] = fold_ranges["fold_bal_acc_max"] - fold_ranges["fold_bal_acc_min"]
aggregate_summary = aggregate_summary.merge(
    fold_ranges,
    on=["source_id", "family", "modality", "representation", "task", "policy", "recipe"],
    how="left",
)
aggregate_summary["macro_f1_vs_majority_acc"] = aggregate_summary["macro_f1"] - aggregate_summary["majority_accuracy"]
aggregate_summary = aggregate_summary.sort_values(
    ["macro_f1", "balanced_accuracy"],
    ascending=[False, False],
).reset_index(drop=True)


def overlap_pair(a: pd.DataFrame, b: pd.DataFrame, pair_name: str, pair_type: str, left_label: str, right_label: str) -> list[dict[str, Any]]:
    key_cols = ["task", "policy", "recipe", "fold_id", "subject_id", "stimulus_id"]
    keep = key_cols + ["y_true", "y_pred"]
    aa = a[keep].copy().rename(columns={"y_true": "y_true_a", "y_pred": "y_pred_a"})
    bb = b[keep].copy().rename(columns={"y_true": "y_true_b", "y_pred": "y_pred_b"})
    merged = aa.merge(bb, on=key_cols, how="inner")
    if merged.empty:
        return [{
            "pair_name": pair_name,
            "pair_type": pair_type,
            "left": left_label,
            "right": right_label,
            "task": "NA",
            "policy": "NA",
            "recipe": "NA",
            "n_aligned": 0,
            "y_true_mismatch": 0,
            "left_error_rate": math.nan,
            "right_error_rate": math.nan,
            "both_error_rate": math.nan,
            "either_error_rate": math.nan,
            "error_jaccard": math.nan,
        }]
    merged["err_a"] = (merged["y_true_a"].astype(int) != merged["y_pred_a"].astype(int))
    merged["err_b"] = (merged["y_true_b"].astype(int) != merged["y_pred_b"].astype(int))
    merged["both_err"] = merged["err_a"] & merged["err_b"]
    merged["either_err"] = merged["err_a"] | merged["err_b"]
    merged["y_true_mismatch_bool"] = merged["y_true_a"].astype(int) != merged["y_true_b"].astype(int)
    rows = []
    for key, g in merged.groupby(["task", "policy", "recipe"], dropna=False, sort=True):
        task, policy, recipe = key
        either = int(g["either_err"].sum())
        both = int(g["both_err"].sum())
        rows.append({
            "pair_name": pair_name,
            "pair_type": pair_type,
            "left": left_label,
            "right": right_label,
            "task": task,
            "policy": policy,
            "recipe": recipe,
            "n_aligned": int(len(g)),
            "y_true_mismatch": int(g["y_true_mismatch_bool"].sum()),
            "left_error_rate": float(g["err_a"].mean()),
            "right_error_rate": float(g["err_b"].mean()),
            "both_error_rate": float(g["both_err"].mean()),
            "either_error_rate": float(g["either_err"].mean()),
            "error_jaccard": safe_div(both, either),
        })
    return rows


def task_overlap(df: pd.DataFrame, source_id: str) -> list[dict[str, Any]]:
    rows = []
    key_cols = ["policy", "recipe", "fold_id", "subject_id", "stimulus_id"]
    val = df[df["task"] == "valence"][key_cols + ["y_true", "y_pred"]].rename(columns={"y_true": "y_true_valence", "y_pred": "y_pred_valence"})
    aro = df[df["task"] == "arousal"][key_cols + ["y_true", "y_pred"]].rename(columns={"y_true": "y_true_arousal", "y_pred": "y_pred_arousal"})
    merged = val.merge(aro, on=key_cols, how="inner")
    if merged.empty:
        return []
    merged["err_valence"] = merged["y_true_valence"].astype(int) != merged["y_pred_valence"].astype(int)
    merged["err_arousal"] = merged["y_true_arousal"].astype(int) != merged["y_pred_arousal"].astype(int)
    merged["both_err"] = merged["err_valence"] & merged["err_arousal"]
    merged["either_err"] = merged["err_valence"] | merged["err_arousal"]
    for key, g in merged.groupby(["policy", "recipe"], dropna=False, sort=True):
        policy, recipe = key
        either = int(g["either_err"].sum())
        both = int(g["both_err"].sum())
        rows.append({
            "pair_name": f"{source_id}:valence_vs_arousal",
            "pair_type": "task_overlap",
            "left": "valence",
            "right": "arousal",
            "task": "valence_vs_arousal",
            "policy": policy,
            "recipe": recipe,
            "n_aligned": int(len(g)),
            "y_true_mismatch": 0,
            "left_error_rate": float(g["err_valence"].mean()),
            "right_error_rate": float(g["err_arousal"].mean()),
            "both_error_rate": float(g["both_err"].mean()),
            "either_error_rate": float(g["either_err"].mean()),
            "error_jaccard": safe_div(both, either),
        })
    return rows


overlap_rows: list[dict[str, Any]] = []
overlap_rows += overlap_pair(
    loaded["label_eeg_mainline"],
    loaded["label_emg_mainline"],
    "label_policy_mainline:EEG_vs_EMG",
    "modality_overlap",
    "EEG STIM-BSL-only",
    "EMG feature-only",
)
overlap_rows += overlap_pair(
    loaded["broader_eeg_stim_bsl_only"],
    loaded["broader_emg_feature_only"],
    "broader_mainline:EEG_vs_EMG",
    "modality_overlap",
    "EEG STIM-BSL-only",
    "EMG feature-only",
)
overlap_rows += overlap_pair(
    loaded["broader_eeg_stim_bsl_only"],
    loaded["broader_eeg_bsl_stats"],
    "broader_EEG:baseline_vs_BSL-stats",
    "representation_overlap",
    "EEG STIM-BSL-only",
    "EEG STIM-BSL-plus-BSL-stats",
)
overlap_rows += overlap_pair(
    loaded["broader_emg_feature_only"],
    loaded["broader_emg_bsl_stats"],
    "broader_EMG:baseline_vs_BSL-stats",
    "representation_overlap",
    "EMG feature-only",
    "EMG feature-plus-BSL-stats",
)
for sid, df in loaded.items():
    overlap_rows += task_overlap(df, sid)

overlap_summary = pd.DataFrame(overlap_rows)
overlap_summary.to_csv(OUT_OVERLAP, index=False)

# Diagnostic evidence summaries.
weak_subject_threshold = 0.45
weak_fold_threshold = 0.47
near_chance_threshold = 0.53
strong_threshold = 0.58

weak_subject_counts = (
    subject_summary[subject_summary["macro_f1"] <= weak_subject_threshold]
    .groupby(["subject_id"], dropna=False)
    .agg(
        weak_rows=("macro_f1", "size"),
        worst_macro_f1=("macro_f1", "min"),
        mean_macro_f1=("macro_f1", "mean"),
        worst_bal_acc=("balanced_accuracy", "min"),
    )
    .reset_index()
    .sort_values(["weak_rows", "worst_macro_f1"], ascending=[False, True])
)

weak_fold_counts = (
    calibration_summary[calibration_summary["macro_f1"] <= weak_fold_threshold]
    .groupby(["source_id", "modality", "representation", "task", "policy", "fold_id"], dropna=False)
    .agg(
        weak_recipe_rows=("macro_f1", "size"),
        worst_macro_f1=("macro_f1", "min"),
        mean_macro_f1=("macro_f1", "mean"),
        worst_bal_acc=("balanced_accuracy", "min"),
    )
    .reset_index()
    .sort_values(["weak_recipe_rows", "worst_macro_f1"], ascending=[False, True])
)

label_source = aggregate_summary[aggregate_summary["family"] == "label_policy_ablation"].copy()
policy_winners = []
for key, g in label_source.groupby(["modality", "task"], dropna=False, sort=True):
    modality, task = key
    best = g.sort_values(["macro_f1", "balanced_accuracy"], ascending=[False, False]).iloc[0]
    by_policy = g.groupby("policy")["macro_f1"].max()
    policy_winners.append({
        "modality": modality,
        "task": task,
        "best_policy": str(best["policy"]),
        "best_recipe": str(best["recipe"]),
        "best_macro_f1": float(best["macro_f1"]),
        "best_balanced_accuracy": float(best["balanced_accuracy"]),
        "policy_macro_f1_range": float(by_policy.max() - by_policy.min()) if len(by_policy) else math.nan,
    })

policy_winner_df = pd.DataFrame(policy_winners)

label_subject = subject_summary[subject_summary["family"] == "label_policy_ablation"].copy()
label_subject_policy = (
    label_subject
    .groupby(["modality", "task", "subject_id", "policy"], dropna=False)
    .agg(mean_macro_f1=("macro_f1", "mean"), mean_bal_acc=("balanced_accuracy", "mean"))
    .reset_index()
)
policy_spread_subject = []
for key, g in label_subject_policy.groupby(["modality", "task", "subject_id"], dropna=False, sort=True):
    if g["policy"].nunique() < 2:
        continue
    policy_spread_subject.append({
        "modality": key[0],
        "task": key[1],
        "subject_id": int(key[2]),
        "policy_macro_f1_range": float(g["mean_macro_f1"].max() - g["mean_macro_f1"].min()),
        "best_policy": str(g.sort_values("mean_macro_f1", ascending=False).iloc[0]["policy"]),
        "worst_policy": str(g.sort_values("mean_macro_f1", ascending=True).iloc[0]["policy"]),
    })
policy_spread_subject_df = pd.DataFrame(policy_spread_subject).sort_values("policy_macro_f1_range", ascending=False)

broad = aggregate_summary[aggregate_summary["family"] == "broader_primary"].copy()
rep_deltas = []
for modality in ["EEG", "EMG"]:
    if modality == "EEG":
        a = broad[broad["source_id"] == "broader_eeg_stim_bsl_only"]
        b = broad[broad["source_id"] == "broader_eeg_bsl_stats"]
        base_name = "STIM-BSL-only"
        alt_name = "STIM-BSL-plus-BSL-stats"
    else:
        a = broad[broad["source_id"] == "broader_emg_feature_only"]
        b = broad[broad["source_id"] == "broader_emg_bsl_stats"]
        base_name = "feature-only"
        alt_name = "feature-plus-BSL-stats"
    join = a.merge(
        b,
        on=["modality", "task", "policy", "recipe"],
        suffixes=("_base", "_alt"),
        how="inner",
    )
    for _, r in join.iterrows():
        rep_deltas.append({
            "modality": modality,
            "task": r["task"],
            "policy": r["policy"],
            "recipe": r["recipe"],
            "baseline": base_name,
            "alternative": alt_name,
            "delta_macro_f1": float(r["macro_f1_alt"] - r["macro_f1_base"]),
            "delta_balanced_accuracy": float(r["balanced_accuracy_alt"] - r["balanced_accuracy_base"]),
        })

rep_delta_df = pd.DataFrame(rep_deltas)

# Root-cause ranking heuristics. These are diagnostic scores, not statistical proof.
weak_group_ratio = float((aggregate_summary["macro_f1"] <= near_chance_threshold).mean())
strong_group_ratio = float((aggregate_summary["macro_f1"] >= strong_threshold).mean())
mean_fold_spread = float(aggregate_summary["fold_macro_f1_range"].fillna(0).mean())
max_fold_spread = float(aggregate_summary["fold_macro_f1_range"].fillna(0).max())
mean_threshold_gain = float(calibration_summary["threshold_macro_f1_gain"].fillna(0).mean())
max_threshold_gain = float(calibration_summary["threshold_macro_f1_gain"].fillna(0).max())
mean_ece = float(calibration_summary["ece_10"].replace([np.inf, -np.inf], np.nan).dropna().mean())
repeated_weak_subjects = int((weak_subject_counts["weak_rows"] >= 8).sum()) if not weak_subject_counts.empty else 0
subject_count = int(all_df["subject_id"].nunique())
repeated_weak_subject_ratio = safe_div(repeated_weak_subjects, subject_count)
policy_mixed = len(set(policy_winner_df["best_policy"].tolist())) > 1 if not policy_winner_df.empty else False
mean_policy_range = float(policy_winner_df["policy_macro_f1_range"].fillna(0).mean()) if not policy_winner_df.empty else 0.0
rep_delta_abs_mean = float(rep_delta_df["delta_macro_f1"].abs().mean()) if not rep_delta_df.empty else 0.0
modality_overlap_mean = float(
    overlap_summary[overlap_summary["pair_type"] == "modality_overlap"]["error_jaccard"]
    .replace([np.inf, -np.inf], np.nan)
    .dropna()
    .mean()
)
if math.isnan(modality_overlap_mean):
    modality_overlap_mean = 0.0

scores = [
    {
        "rank_candidate": "subject/fold generalization issue",
        "score": min(1.0, 0.45 * safe_div(mean_fold_spread, 0.12) + 0.35 * safe_div(repeated_weak_subject_ratio, 0.30) + 0.20 * safe_div(modality_overlap_mean, 0.60)),
        "confidence": "medium-high" if mean_fold_spread >= 0.08 or repeated_weak_subjects >= 10 else "medium",
        "support": [
            f"mean fold macro-F1 range = {mean_fold_spread:.4f}",
            f"max fold macro-F1 range = {max_fold_spread:.4f}",
            f"subjects weak in at least 8 diagnostic rows = {repeated_weak_subjects}/{subject_count}",
            f"mean EEG/EMG error-overlap Jaccard = {modality_overlap_mean:.4f}",
        ],
    },
    {
        "rank_candidate": "calibration/threshold issue",
        "score": min(1.0, 0.70 * safe_div(mean_threshold_gain, 0.04) + 0.30 * safe_div(mean_ece, 0.18)),
        "confidence": "medium-high" if mean_threshold_gain >= 0.02 or mean_ece >= 0.10 else "medium",
        "support": [
            f"mean threshold macro-F1 gain = {mean_threshold_gain:.4f}",
            f"max threshold macro-F1 gain = {max_threshold_gain:.4f}",
            f"mean ECE-10 = {mean_ece:.4f}",
        ],
    },
    {
        "rank_candidate": "label/task definition issue",
        "score": min(1.0, (0.45 if policy_mixed else 0.10) + 0.55 * safe_div(mean_policy_range, 0.06)),
        "confidence": "medium-high" if policy_mixed and mean_policy_range >= 0.03 else "medium",
        "support": [
            f"mixed best policies across modality/task = {policy_mixed}",
            f"mean best-policy macro-F1 range by modality/task = {mean_policy_range:.4f}",
            "best policies: " + "; ".join(
                f"{r['modality']} {r['task']}={r['best_policy']} ({r['best_macro_f1']:.4f})"
                for r in policy_winners
            ),
        ],
    },
    {
        "rank_candidate": "representation weakness",
        "score": min(1.0, 0.55 * weak_group_ratio + 0.25 * (1.0 if rep_delta_abs_mean <= 0.025 else 0.4) + 0.20 * (1.0 - min(1.0, strong_group_ratio / 0.10))),
        "confidence": "medium" if weak_group_ratio >= 0.50 else "low-medium",
        "support": [
            f"aggregate groups at or below macro-F1 {near_chance_threshold:.2f} = {weak_group_ratio:.2%}",
            f"aggregate groups at or above macro-F1 {strong_threshold:.2f} = {strong_group_ratio:.2%}",
            f"mean absolute BSL-stats representation delta = {rep_delta_abs_mean:.4f}",
        ],
    },
    {
        "rank_candidate": "model/pipeline learning issue",
        "score": min(1.0, 0.55 * weak_group_ratio + 0.25 * (1.0 - min(1.0, strong_group_ratio / 0.08)) + 0.20 * safe_div(mean_threshold_gain, 0.05)),
        "confidence": "low-medium",
        "support": [
            "Read-only outputs cannot prove pipeline failure.",
            f"weak aggregate ratio = {weak_group_ratio:.2%}",
            f"strong aggregate ratio = {strong_group_ratio:.2%}",
            "A micro-overfit / shuffled-label / within-subject diagnostic objective is needed if this remains plausible after review.",
        ],
    },
]

scores = sorted(scores, key=lambda x: x["score"], reverse=True)

# Recommended next objective: keep it one objective and diagnostic-only, because read-only evidence cannot conclusively
# separate representation weakness from model/pipeline inability to learn.
top = scores[0]["rank_candidate"]
if top == "calibration/threshold issue" and scores[0]["score"] >= scores[1]["score"] + 0.15:
    recommended_next = "calibration_and_fold_difficulty_intervention_objective"
    recommended_rationale = [
        "Calibration/threshold evidence is clearly dominant in this read-only report.",
        "Next work should test threshold/calibration/fold-aware decision rules without fusion or architecture escalation.",
    ]
else:
    recommended_next = "diagnostic_sanity_tests_objective"
    recommended_rationale = [
        "Read-only evidence points to subject/fold, label, calibration, and representation issues, but it cannot conclusively rule out model/pipeline learning failure.",
        "Before proposing fixes, run diagnostic-only sanity tests: micro-overfit, shuffled-label negative control, within-subject contrast, and a simple classical baseline.",
        "This is not a performance-training objective; it is the fastest way to localize whether the pipeline can learn signal at all.",
    ]

top_subjects = weak_subject_counts.head(20).to_dict(orient="records")
top_weak_folds = weak_fold_counts.head(20).to_dict(orient="records")
top_policy_sensitive_subjects = policy_spread_subject_df.head(20).to_dict(orient="records") if not policy_spread_subject_df.empty else []
top_aggregate = aggregate_summary.head(12).to_dict(orient="records")
bottom_aggregate = aggregate_summary.tail(12).sort_values(["macro_f1", "balanced_accuracy"]).to_dict(orient="records")
top_overlap = overlap_summary.sort_values("error_jaccard", ascending=False).head(20).to_dict(orient="records")

report_json = {
    "status": "complete_pending_review",
    "created_or_updated_utc": NOW,
    "objective": "docs/idare_root_cause_diagnostic_objective.md",
    "evidence_level": "read-only diagnostic analysis from existing committed outputs; no new training",
    "source_validation": metadata,
    "outputs": {
        "markdown_report": str(OUT_MD),
        "json_report": str(OUT_JSON),
        "subject_summary_csv": str(OUT_SUBJECT),
        "calibration_summary_csv": str(OUT_CAL),
        "error_overlap_summary_csv": str(OUT_OVERLAP),
    },
    "summary_stats": {
        "aggregate_rows": int(len(aggregate_summary)),
        "subject_summary_rows": int(len(subject_summary)),
        "calibration_fold_rows": int(len(calibration_summary)),
        "error_overlap_rows": int(len(overlap_summary)),
        "weak_group_ratio_macro_f1_le_0p53": weak_group_ratio,
        "strong_group_ratio_macro_f1_ge_0p58": strong_group_ratio,
        "mean_fold_macro_f1_range": mean_fold_spread,
        "max_fold_macro_f1_range": max_fold_spread,
        "mean_threshold_macro_f1_gain": mean_threshold_gain,
        "max_threshold_macro_f1_gain": max_threshold_gain,
        "mean_ece_10": mean_ece,
        "repeated_weak_subjects_count": repeated_weak_subjects,
        "subject_count": subject_count,
        "mean_modality_error_overlap_jaccard": modality_overlap_mean,
        "mean_abs_representation_delta_macro_f1": rep_delta_abs_mean,
    },
    "root_cause_ranking": scores,
    "policy_winners": policy_winners,
    "representation_deltas": rep_deltas,
    "top_repeated_weak_subjects": top_subjects,
    "top_weak_folds": top_weak_folds,
    "top_policy_sensitive_subjects": top_policy_sensitive_subjects,
    "top_error_overlap_rows": top_overlap,
    "best_aggregate_rows": top_aggregate,
    "worst_aggregate_rows": bottom_aggregate,
    "recommended_next_objective": recommended_next,
    "recommended_rationale": recommended_rationale,
    "not_authorized_from_this_report": [
        "new performance training without a reviewed follow-up objective",
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "final global label-policy lock",
        "architecture ablation",
        "data augmentation",
        "SupCon / VREx / domain generalization",
    ],
}

OUT_JSON.write_text(json.dumps(report_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "NA"
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if math.isnan(f):
        return "NA"
    return f"{f:.{digits}f}"


def md_table(rows: list[dict[str, Any]], headers: list[tuple[str, str]], limit: int | None = None) -> str:
    if limit is not None:
        rows = rows[:limit]
    lines = []
    lines.append("| " + " | ".join(h[0] for h in headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for r in rows:
        vals = []
        for _, key in headers:
            val = r.get(key, "")
            if isinstance(val, float):
                vals.append(fmt(val))
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


ranking_rows = [
    {
        "rank": i + 1,
        "candidate": r["rank_candidate"],
        "score": r["score"],
        "confidence": r["confidence"],
        "support": "; ".join(r["support"][:3]),
    }
    for i, r in enumerate(scores)
]

policy_rows = policy_winners
rep_rows = rep_deltas
subject_rows = top_subjects[:10]
fold_rows = top_weak_folds[:10]
overlap_rows_md = top_overlap[:10]

md = f"""# I-DARE Root-Cause Diagnostic Report

## Status

Read-only root-cause diagnostic report complete; pending human review.

No new training was run.

Generated UTC: `{NOW}`

## Source Validation

| Source | Rows | Runs | Tasks | Policies | Recipes | Subjects |
|---|---:|---:|---|---|---|---:|
"""
for m in metadata:
    md += f"| `{m['source_id']}` | {m['rows']} | {m['runs']} | {', '.join(m['tasks'])} | {', '.join(m['policies'])} | {', '.join(m['recipes'])} | {m['subjects']} |\n"

md += f"""
## Diagnostic Summary

| Diagnostic | Value |
|---|---:|
| Aggregate rows analyzed | {len(aggregate_summary)} |
| Subject-summary rows | {len(subject_summary)} |
| Fold/calibration rows | {len(calibration_summary)} |
| Error-overlap rows | {len(overlap_summary)} |
| Weak aggregate ratio, macro-F1 <= 0.53 | {weak_group_ratio:.2%} |
| Strong aggregate ratio, macro-F1 >= 0.58 | {strong_group_ratio:.2%} |
| Mean fold macro-F1 range | {mean_fold_spread:.4f} |
| Max fold macro-F1 range | {max_fold_spread:.4f} |
| Mean threshold macro-F1 gain | {mean_threshold_gain:.4f} |
| Max threshold macro-F1 gain | {max_threshold_gain:.4f} |
| Mean ECE-10 | {mean_ece:.4f} |
| Subjects weak in at least 8 diagnostic rows | {repeated_weak_subjects}/{subject_count} |
| Mean EEG/EMG error-overlap Jaccard | {modality_overlap_mean:.4f} |
| Mean absolute BSL-stats representation delta | {rep_delta_abs_mean:.4f} |

## Root-Cause Ranking

{md_table(ranking_rows, [
    ("Rank", "rank"),
    ("Candidate cause", "candidate"),
    ("Score", "score"),
    ("Confidence", "confidence"),
    ("Main support", "support"),
])}

## Label-Policy Sensitivity

{md_table(policy_rows, [
    ("Modality", "modality"),
    ("Task", "task"),
    ("Best policy", "best_policy"),
    ("Best recipe", "best_recipe"),
    ("Best macro F1", "best_macro_f1"),
    ("Best bal acc", "best_balanced_accuracy"),
    ("Policy macro-F1 range", "policy_macro_f1_range"),
])}

## Representation Delta Snapshot

Positive delta means the BSL-stats representation beat the corresponding baseline.

{md_table(rep_rows, [
    ("Modality", "modality"),
    ("Task", "task"),
    ("Policy", "policy"),
    ("Recipe", "recipe"),
    ("Delta macro F1", "delta_macro_f1"),
    ("Delta bal acc", "delta_balanced_accuracy"),
])}

## Repeated Weak Subjects

{md_table(subject_rows, [
    ("Subject", "subject_id"),
    ("Weak rows", "weak_rows"),
    ("Worst macro F1", "worst_macro_f1"),
    ("Mean macro F1", "mean_macro_f1"),
    ("Worst bal acc", "worst_bal_acc"),
])}

## Weak Fold Hotspots

{md_table(fold_rows, [
    ("Source", "source_id"),
    ("Modality", "modality"),
    ("Task", "task"),
    ("Policy", "policy"),
    ("Fold", "fold_id"),
    ("Weak recipe rows", "weak_recipe_rows"),
    ("Worst macro F1", "worst_macro_f1"),
    ("Mean macro F1", "mean_macro_f1"),
])}

## Error-Overlap Snapshot

{md_table(overlap_rows_md, [
    ("Pair", "pair_name"),
    ("Type", "pair_type"),
    ("Task", "task"),
    ("Policy", "policy"),
    ("Recipe", "recipe"),
    ("N aligned", "n_aligned"),
    ("Left err", "left_error_rate"),
    ("Right err", "right_error_rate"),
    ("Both err", "both_error_rate"),
    ("Error Jaccard", "error_jaccard"),
])}

## Interpretation

The read-only evidence does not support another blind training sweep.

The strongest current explanation is a combination of subject/fold generalization difficulty, calibration/threshold weakness, and label/task sensitivity. Representation weakness is also plausible because BSL-stats does not produce a consistent large gain. A model/pipeline learning issue cannot be proven from read-only outputs, but it also cannot be ruled out.

## Recommended Next Objective

`{recommended_next}`

Rationale:

"""
for item in recommended_rationale:
    md += f"- {item}\n"

md += """
## Not Authorized From This Report

- new performance training without a reviewed follow-up objective
- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation
- data augmentation
- SupCon / VREx / domain generalization

## Output Files

- `docs/idare_root_cause_diagnostic_report.md`
- `docs/idare_root_cause_diagnostic_report.json`
- `docs/idare_root_cause_subject_summary.csv`
- `docs/idare_root_cause_calibration_summary.csv`
- `docs/idare_root_cause_error_overlap_summary.csv`

## Next Allowed Step

Human review / closeout of this root-cause diagnostic report.

Only after review should we create the next objective.
"""

OUT_MD.write_text(md, encoding="utf-8")

# Update central roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
report_row = "| I-DARE root-cause diagnostic report | read-only diagnostic report complete from existing predictions; pending human review | yes | `docs/idare_root_cause_diagnostic_report.md` | Human review / closeout before diagnostic sanity tests or any fix objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; new performance training. |"

if "I-DARE root-cause diagnostic report" not in project_md:
    lines = project_md.splitlines()
    out_lines = []
    inserted = False
    for line in lines:
        out_lines.append(line)
        if line.startswith("| I-DARE root-cause diagnostic objective |"):
            out_lines.append(report_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert root-cause report row")
    project_md = "\n".join(out_lines) + "\n"

report_bullet = "- Controlled I-DARE root-cause diagnostic report is complete in `docs/idare_root_cause_diagnostic_report.md`; next work is human review/closeout, not new training or fusion."
if report_bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: project status marker not found")
    project_md = project_md.replace(marker, "\n" + report_bullet + "\n" + marker)

PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_root_cause_diagnostic_report"] = {
    "status": "complete_pending_review",
    "evidence": "docs/idare_root_cause_diagnostic_report.md",
    "evidence_json": "docs/idare_root_cause_diagnostic_report.json",
    "subject_summary_csv": "docs/idare_root_cause_subject_summary.csv",
    "calibration_summary_csv": "docs/idare_root_cause_calibration_summary.csv",
    "error_overlap_summary_csv": "docs/idare_root_cause_error_overlap_summary.csv",
    "evidence_level": "read-only diagnostic analysis from existing committed outputs; no new training",
    "root_cause_ranking": scores,
    "recommended_next_objective": recommended_next,
    "next_allowed_step": "Human review / closeout of root-cause diagnostic report.",
    "not_authorized": report_json["not_authorized_from_this_report"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_ROOT_CAUSE_DIAGNOSTIC_REPORT_WRITTEN")
print(OUT_MD)
print(OUT_JSON)
print(OUT_SUBJECT)
print(OUT_CAL)
print(OUT_OVERLAP)
print("recommended_next_objective=", recommended_next)
PY
echo

echo "===== 3) validate generated docs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
for p in [
    Path("docs/idare_root_cause_diagnostic_report.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")
for p in [
    Path("docs/idare_root_cause_subject_summary.csv"),
    Path("docs/idare_root_cause_calibration_summary.csv"),
    Path("docs/idare_root_cause_error_overlap_summary.csv"),
]:
    with p.open("r", encoding="utf-8") as f:
        rows = sum(1 for _ in f) - 1
    print(p.name, "rows=", rows)
PY

grep -n "## Status\|## Diagnostic Summary\|## Root-Cause Ranking\|## Recommended Next Objective\|## Next Allowed Step" docs/idare_root_cause_diagnostic_report.md
grep -n "root-cause diagnostic report" docs/project_status_current.md
echo

echo "===== 4) file list ====="
ls -lh \
  docs/idare_root_cause_diagnostic_report.md \
  docs/idare_root_cause_diagnostic_report.json \
  docs/idare_root_cause_subject_summary.csv \
  docs/idare_root_cause_calibration_summary.csv \
  docs/idare_root_cause_error_overlap_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 5) status before commit ====="
git status --short --branch
echo

echo "===== 6) commit and push root-cause diagnostic report ====="
git add \
  docs/idare_root_cause_diagnostic_report.md \
  docs/idare_root_cause_diagnostic_report.json \
  docs/idare_root_cause_subject_summary.csv \
  docs/idare_root_cause_calibration_summary.csv \
  docs/idare_root_cause_error_overlap_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "analysis: add I-DARE root-cause diagnostic report"

git push origin main
echo

echo "===== 7) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_root_cause_diagnostic_report.log"
