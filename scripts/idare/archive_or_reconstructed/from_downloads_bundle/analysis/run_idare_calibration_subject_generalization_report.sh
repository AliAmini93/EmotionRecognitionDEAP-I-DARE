#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start calibration + subject-generalization diagnostic report ====="
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
try:
    import json
    import numpy as np
    import pandas as pd
except Exception as e:
    print("IMPORT_ERROR:", repr(e))
    raise
print("OK_IMPORTS")
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repo is not clean; commit/stash current changes before running this read-only diagnostic."
  git status --short --branch
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required committed inputs ====="
ls -lh \
  docs/idare_calibration_and_subject_generalization_objective.md \
  docs/idare_calibration_and_subject_generalization_objective.json \
  docs/idare_diagnostic_sanity_tests_review_status.md \
  docs/idare_diagnostic_sanity_tests_report.md \
  docs/idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv \
  docs/idare_broader_eval_emg_feature_only_primary_predictions.csv \
  docs/idare_label_policy_ablation_eeg_primary_predictions.csv \
  docs/idare_label_policy_ablation_emg_primary_predictions.csv
echo

echo "===== 3) generate calibration + subject-generalization report ====="
"$PY" - <<'PY'
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

OUT_MD = DOCS / "idare_calibration_subject_generalization_report.md"
OUT_JSON = DOCS / "idare_calibration_subject_generalization_report.json"
OUT_THRESH = DOCS / "idare_calibration_subject_threshold_summary.csv"
OUT_SUBJECT = DOCS / "idare_subject_difficulty_ranking.csv"
OUT_OVERLAP = DOCS / "idare_cross_modality_error_overlap.csv"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

required = [
    DOCS / "idare_calibration_and_subject_generalization_objective.md",
    DOCS / "idare_calibration_and_subject_generalization_objective.json",
    DOCS / "idare_diagnostic_sanity_tests_review_status.md",
    DOCS / "idare_diagnostic_sanity_tests_report.md",
    DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv",
    DOCS / "idare_broader_eval_emg_feature_only_primary_predictions.csv",
    DOCS / "idare_label_policy_ablation_eeg_primary_predictions.csv",
    DOCS / "idare_label_policy_ablation_emg_primary_predictions.csv",
    PROJECT_MD,
    PROJECT_JSON,
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("ERROR: missing required files:\n" + "\n".join(missing))

objective = json.loads((DOCS / "idare_calibration_and_subject_generalization_objective.json").read_text(encoding="utf-8"))

candidate_files = [
    DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv",
    DOCS / "idare_broader_eval_eeg_bsl_stats_primary_predictions.csv",
    DOCS / "idare_broader_eval_emg_feature_only_primary_predictions.csv",
    DOCS / "idare_broader_eval_emg_bsl_stats_primary_predictions.csv",
    DOCS / "idare_label_policy_ablation_eeg_primary_predictions.csv",
    DOCS / "idare_label_policy_ablation_emg_primary_predictions.csv",
]
input_files = [p for p in candidate_files if p.exists()]

TRUE_COLS = [
    "y_true", "true_label", "label", "target", "target_label", "truth",
    "valence_label", "arousal_label", "class_label",
]
PRED_COLS = [
    "y_pred", "pred", "prediction", "pred_label", "predicted_label",
    "final_pred", "class_pred",
]
PROB1_COLS = [
    "prob_1", "p_1", "p1", "prob1", "prob_class_1", "probability_1",
    "p_class_1", "score_1", "class1_prob", "positive_prob",
]
SUBJECT_COLS = ["subject_id", "subject", "subject_idx", "sid"]
TASK_COLS = ["task", "target_task"]
RECIPE_COLS = ["recipe", "model_recipe", "training_recipe"]
POLICY_COLS = ["label_policy", "policy"]
FOLD_COLS = ["fold_id", "fold", "cv_fold"]
RUN_COLS = ["run_id", "run"]
SEED_COLS = ["seed", "random_seed"]


def first_col(df: pd.DataFrame, candidates: list[str], required: bool = True) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    if required:
        raise ValueError(f"Missing required column from candidates={candidates}; columns={list(df.columns)}")
    return None


def infer_metadata(path: Path) -> dict[str, str]:
    name = path.name.lower()
    if "_eeg_" in name or name.startswith("idare_label_policy_ablation_eeg"):
        modality = "EEG"
    elif "_emg_" in name or name.startswith("idare_label_policy_ablation_emg"):
        modality = "EMG"
    else:
        modality = "unknown"

    if "stim_bsl_only" in name:
        variant = "stim_bsl_only"
    elif "bsl_stats" in name:
        variant = "bsl_stats"
    elif "feature_only" in name:
        variant = "feature_only"
    elif "label_policy_ablation" in name:
        variant = "mainline_label_policy_ablation"
    else:
        variant = "unknown"

    if "label_policy_ablation" in name:
        source_group = "label_policy_ablation"
    elif "broader_eval" in name:
        source_group = "broader_eval_primary"
    else:
        source_group = "other"

    return {
        "source_file": str(path),
        "source_name": path.name,
        "source_group": source_group,
        "modality": modality,
        "variant": variant,
    }


def normalize_predictions(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    meta = infer_metadata(path)

    true_col = first_col(raw, TRUE_COLS, required=True)
    pred_col = first_col(raw, PRED_COLS, required=False)
    prob_col = first_col(raw, PROB1_COLS, required=False)
    subject_col = first_col(raw, SUBJECT_COLS, required=True)
    task_col = first_col(raw, TASK_COLS, required=False)
    recipe_col = first_col(raw, RECIPE_COLS, required=False)
    policy_col = first_col(raw, POLICY_COLS, required=False)
    fold_col = first_col(raw, FOLD_COLS, required=False)
    run_col = first_col(raw, RUN_COLS, required=False)
    seed_col = first_col(raw, SEED_COLS, required=False)

    df = pd.DataFrame()
    for k, v in meta.items():
        df[k] = [v] * len(raw)

    df["subject_id"] = pd.to_numeric(raw[subject_col], errors="coerce").astype("Int64")
    df["task"] = raw[task_col].astype(str) if task_col else "unknown"
    df["recipe"] = raw[recipe_col].astype(str) if recipe_col else "unknown"
    if policy_col:
        df["label_policy"] = raw[policy_col].astype(str)
    else:
        df["label_policy"] = "midpoint_as_high"

    if fold_col:
        df["fold_id"] = pd.to_numeric(raw[fold_col], errors="coerce").astype("Int64")
    else:
        df["fold_id"] = pd.Series([pd.NA] * len(raw), dtype="Int64")

    if run_col:
        df["run_id"] = pd.to_numeric(raw[run_col], errors="coerce").astype("Int64")
    else:
        df["run_id"] = pd.Series([pd.NA] * len(raw), dtype="Int64")

    if seed_col:
        df["seed"] = pd.to_numeric(raw[seed_col], errors="coerce").astype("Int64")
    else:
        df["seed"] = pd.Series([pd.NA] * len(raw), dtype="Int64")

    df["y_true"] = pd.to_numeric(raw[true_col], errors="coerce").astype("Int64")

    if prob_col:
        df["prob_1"] = pd.to_numeric(raw[prob_col], errors="coerce")
    else:
        df["prob_1"] = np.nan

    if pred_col:
        df["y_pred"] = pd.to_numeric(raw[pred_col], errors="coerce").astype("Int64")
    elif prob_col:
        df["y_pred"] = (df["prob_1"] >= 0.5).astype("Int64")
    else:
        raise ValueError(f"Missing prediction/probability column for {path}")

    df = df.dropna(subset=["subject_id", "y_true", "y_pred"])
    df["subject_id"] = df["subject_id"].astype(int)
    df["y_true"] = df["y_true"].astype(int)
    df["y_pred"] = df["y_pred"].astype(int)
    df["correct"] = (df["y_true"] == df["y_pred"]).astype(int)

    return df


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def metrics(y_true: Any, y_pred: Any) -> dict[str, Any]:
    yt = np.asarray(y_true, dtype=int)
    yp = np.asarray(y_pred, dtype=int)
    n = int(len(yt))
    if n == 0:
        return {
            "n": 0,
            "accuracy": math.nan,
            "balanced_accuracy": math.nan,
            "macro_f1": math.nan,
            "true_0": 0,
            "true_1": 0,
            "pred_0": 0,
            "pred_1": 0,
            "one_class_pred": False,
        }

    true_0 = int((yt == 0).sum())
    true_1 = int((yt == 1).sum())
    pred_0 = int((yp == 0).sum())
    pred_1 = int((yp == 1).sum())

    recalls = []
    f1s = []
    for label in [0, 1]:
        tp = int(((yt == label) & (yp == label)).sum())
        fp = int(((yt != label) & (yp == label)).sum())
        fn = int(((yt == label) & (yp != label)).sum())
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2.0 * precision * recall, precision + recall)
        recalls.append(recall)
        f1s.append(f1)

    return {
        "n": n,
        "accuracy": float((yt == yp).mean()),
        "balanced_accuracy": float(np.mean(recalls)),
        "macro_f1": float(np.mean(f1s)),
        "true_0": true_0,
        "true_1": true_1,
        "pred_0": pred_0,
        "pred_1": pred_1,
        "one_class_pred": bool(len(set(yp.tolist())) == 1),
    }


def best_threshold(y_true: Any, prob: Any) -> dict[str, Any]:
    yt = np.asarray(y_true, dtype=int)
    pr = np.asarray(prob, dtype=float)
    mask = np.isfinite(pr)
    yt = yt[mask]
    pr = pr[mask]
    if len(yt) == 0:
        return {
            "best_threshold": math.nan,
            "best_macro_f1": math.nan,
            "best_balanced_accuracy": math.nan,
            "best_accuracy": math.nan,
            "best_pred_0": 0,
            "best_pred_1": 0,
            "threshold_one_class": False,
        }

    grid = np.unique(np.concatenate([
        np.linspace(0.01, 0.99, 99),
        np.quantile(pr, np.linspace(0.05, 0.95, 19)),
        np.array([0.5]),
    ]))
    best = None
    for th in grid:
        yp = (pr >= th).astype(int)
        m = metrics(yt, yp)
        item = {
            "best_threshold": float(th),
            "best_macro_f1": m["macro_f1"],
            "best_balanced_accuracy": m["balanced_accuracy"],
            "best_accuracy": m["accuracy"],
            "best_pred_0": m["pred_0"],
            "best_pred_1": m["pred_1"],
            "threshold_one_class": m["one_class_pred"],
        }
        if best is None or (item["best_macro_f1"], item["best_balanced_accuracy"], item["best_accuracy"]) > (
            best["best_macro_f1"], best["best_balanced_accuracy"], best["best_accuracy"]
        ):
            best = item
    return best


frames = []
errors = []
for path in input_files:
    try:
        df = normalize_predictions(path)
        frames.append(df)
        print(f"LOADED {path} rows={len(df)}")
    except Exception as e:
        errors.append({"path": str(path), "error": repr(e)})
        print(f"SKIP {path}: {e}")

if not frames:
    raise SystemExit("ERROR: no prediction files could be loaded")

all_pred = pd.concat(frames, ignore_index=True)
all_pred = all_pred[all_pred["task"].isin(["valence", "arousal"])].copy()

# Primary threshold summaries.
threshold_rows: list[dict[str, Any]] = []
group_cols = ["source_group", "source_name", "modality", "variant", "task", "label_policy", "recipe"]
for keys, g in all_pred.groupby(group_cols, dropna=False):
    row = dict(zip(group_cols, keys))
    default = metrics(g["y_true"], g["y_pred"])
    if g["prob_1"].notna().any():
        best = best_threshold(g["y_true"], g["prob_1"])
    else:
        best = {
            "best_threshold": math.nan,
            "best_macro_f1": math.nan,
            "best_balanced_accuracy": math.nan,
            "best_accuracy": math.nan,
            "best_pred_0": 0,
            "best_pred_1": 0,
            "threshold_one_class": False,
        }
    row.update({
        "level": "overall",
        "fold_id": "",
        "n": default["n"],
        "default_macro_f1": default["macro_f1"],
        "default_balanced_accuracy": default["balanced_accuracy"],
        "default_accuracy": default["accuracy"],
        "default_pred_0": default["pred_0"],
        "default_pred_1": default["pred_1"],
        **best,
        "macro_f1_gain": best["best_macro_f1"] - default["macro_f1"] if math.isfinite(best["best_macro_f1"]) else math.nan,
        "balanced_accuracy_gain": best["best_balanced_accuracy"] - default["balanced_accuracy"] if math.isfinite(best["best_balanced_accuracy"]) else math.nan,
    })
    threshold_rows.append(row)

# Fold-specific threshold summaries.
fold_group_cols = ["source_group", "source_name", "modality", "variant", "task", "label_policy", "recipe", "fold_id"]
for keys, g in all_pred.dropna(subset=["fold_id"]).groupby(fold_group_cols, dropna=False):
    row = dict(zip(fold_group_cols, keys))
    default = metrics(g["y_true"], g["y_pred"])
    if g["prob_1"].notna().any():
        best = best_threshold(g["y_true"], g["prob_1"])
    else:
        best = {
            "best_threshold": math.nan,
            "best_macro_f1": math.nan,
            "best_balanced_accuracy": math.nan,
            "best_accuracy": math.nan,
            "best_pred_0": 0,
            "best_pred_1": 0,
            "threshold_one_class": False,
        }
    row.update({
        "level": "fold",
        "n": default["n"],
        "default_macro_f1": default["macro_f1"],
        "default_balanced_accuracy": default["balanced_accuracy"],
        "default_accuracy": default["accuracy"],
        "default_pred_0": default["pred_0"],
        "default_pred_1": default["pred_1"],
        **best,
        "macro_f1_gain": best["best_macro_f1"] - default["macro_f1"] if math.isfinite(best["best_macro_f1"]) else math.nan,
        "balanced_accuracy_gain": best["best_balanced_accuracy"] - default["balanced_accuracy"] if math.isfinite(best["best_balanced_accuracy"]) else math.nan,
    })
    threshold_rows.append(row)

threshold_df = pd.DataFrame(threshold_rows)
threshold_df.to_csv(OUT_THRESH, index=False)

overall = threshold_df[threshold_df["level"] == "overall"].copy()
fold_level = threshold_df[threshold_df["level"] == "fold"].copy()

# Subject difficulty.
subject_group_cols = ["subject_id", "modality", "task", "label_policy"]
subject_rows = []
for keys, g in all_pred.groupby(subject_group_cols, dropna=False):
    row = dict(zip(subject_group_cols, keys))
    n = int(len(g))
    correct = int(g["correct"].sum())
    row.update({
        "n": n,
        "correct": correct,
        "errors": int(n - correct),
        "accuracy": float(correct / n) if n else math.nan,
        "error_rate": float(1.0 - correct / n) if n else math.nan,
        "n_sources": int(g["source_name"].nunique()),
        "n_recipes": int(g["recipe"].nunique()),
        "n_folds": int(g["fold_id"].nunique(dropna=True)),
        "variants": ",".join(sorted(str(v) for v in g["variant"].dropna().unique())),
        "recipes": ",".join(sorted(str(v) for v in g["recipe"].dropna().unique())),
    })
    subject_rows.append(row)

subject_df = pd.DataFrame(subject_rows)
if not subject_df.empty:
    subject_df["hard_subject_flag"] = subject_df["error_rate"] >= 0.55
    subject_df = subject_df.sort_values(["error_rate", "n"], ascending=[False, False])
subject_df.to_csv(OUT_SUBJECT, index=False)

# Cross-modality error overlap based on subject/task/policy for comparable rows.
overlap_rows = []
if not subject_df.empty:
    agg = subject_df.groupby(["subject_id", "task", "label_policy", "modality"], dropna=False).agg(
        n=("n", "sum"),
        errors=("errors", "sum"),
        correct=("correct", "sum"),
    ).reset_index()
    agg["accuracy"] = agg["correct"] / agg["n"]
    agg["error_rate"] = agg["errors"] / agg["n"]
    pivot = agg.pivot_table(
        index=["subject_id", "task", "label_policy"],
        columns="modality",
        values=["n", "accuracy", "error_rate"],
        aggfunc="first",
    )
    pivot.columns = [f"{a}_{b}" for a, b in pivot.columns]
    pivot = pivot.reset_index()
    if "error_rate_EEG" in pivot.columns and "error_rate_EMG" in pivot.columns:
        both = pivot.dropna(subset=["error_rate_EEG", "error_rate_EMG"]).copy()
        both["common_failure_score"] = both["error_rate_EEG"] * both["error_rate_EMG"]
        both["both_hard_flag"] = (both["error_rate_EEG"] >= 0.55) & (both["error_rate_EMG"] >= 0.55)
        both["eeg_specific_hard_flag"] = (both["error_rate_EEG"] >= 0.55) & (both["error_rate_EMG"] < 0.45)
        both["emg_specific_hard_flag"] = (both["error_rate_EMG"] >= 0.55) & (both["error_rate_EEG"] < 0.45)
        overlap_rows = both.to_dict(orient="records")
        overlap_df = both.sort_values(["common_failure_score"], ascending=False)
    else:
        overlap_df = pd.DataFrame()
else:
    overlap_df = pd.DataFrame()

overlap_df.to_csv(OUT_OVERLAP, index=False)

# Stability map.
stability_rows = []
for keys, g in fold_level.groupby(["source_group", "modality", "variant", "task", "label_policy", "recipe"], dropna=False):
    row = dict(zip(["source_group", "modality", "variant", "task", "label_policy", "recipe"], keys))
    th = pd.to_numeric(g["best_threshold"], errors="coerce")
    gains = pd.to_numeric(g["macro_f1_gain"], errors="coerce")
    defaults = pd.to_numeric(g["default_macro_f1"], errors="coerce")
    bests = pd.to_numeric(g["best_macro_f1"], errors="coerce")
    row.update({
        "folds": int(len(g)),
        "default_macro_f1_mean": float(defaults.mean()) if len(defaults) else math.nan,
        "default_macro_f1_std": float(defaults.std(ddof=0)) if len(defaults) else math.nan,
        "best_macro_f1_mean": float(bests.mean()) if len(bests) else math.nan,
        "best_macro_f1_std": float(bests.std(ddof=0)) if len(bests) else math.nan,
        "macro_f1_gain_mean": float(gains.mean()) if len(gains) else math.nan,
        "macro_f1_gain_max": float(gains.max()) if len(gains) else math.nan,
        "threshold_mean": float(th.mean()) if len(th.dropna()) else math.nan,
        "threshold_std": float(th.std(ddof=0)) if len(th.dropna()) else math.nan,
        "threshold_min": float(th.min()) if len(th.dropna()) else math.nan,
        "threshold_max": float(th.max()) if len(th.dropna()) else math.nan,
        "one_class_threshold_folds": int(pd.Series(g["threshold_one_class"]).astype(bool).sum()),
    })
    row["calibration_instability_flag"] = bool(row["threshold_std"] >= 0.15 or row["one_class_threshold_folds"] > 0)
    row["large_threshold_gain_flag"] = bool(row["macro_f1_gain_mean"] >= 0.03 or row["macro_f1_gain_max"] >= 0.06)
    row["stable_recipe_flag"] = bool(row["default_macro_f1_std"] <= 0.03 and row["default_macro_f1_mean"] >= 0.53)
    stability_rows.append(row)

stability_df = pd.DataFrame(stability_rows)

# Diagnosis.
overall_gain_mean = float(pd.to_numeric(overall["macro_f1_gain"], errors="coerce").mean()) if not overall.empty else math.nan
overall_gain_max = float(pd.to_numeric(overall["macro_f1_gain"], errors="coerce").max()) if not overall.empty else math.nan
fold_gain_mean = float(pd.to_numeric(fold_level["macro_f1_gain"], errors="coerce").mean()) if not fold_level.empty else math.nan
threshold_std_mean = float(stability_df["threshold_std"].mean()) if not stability_df.empty else math.nan
threshold_instability_count = int(stability_df["calibration_instability_flag"].sum()) if not stability_df.empty else 0
large_gain_count = int(stability_df["large_threshold_gain_flag"].sum()) if not stability_df.empty else 0
hard_subject_count = int((subject_df["hard_subject_flag"] == True).sum()) if not subject_df.empty else 0
both_hard_count = int((overlap_df["both_hard_flag"] == True).sum()) if not overlap_df.empty and "both_hard_flag" in overlap_df.columns else 0
mean_common_failure_score = float(overlap_df["common_failure_score"].mean()) if not overlap_df.empty and "common_failure_score" in overlap_df.columns else math.nan

if large_gain_count >= 4 and threshold_instability_count >= 4:
    diagnosis = "calibration_instability_supported"
    recommended_next = "calibration_protocol_objective"
    recommendation_reason = [
        "Threshold sweeps show repeated macro-F1 gains.",
        "Best thresholds vary substantially across folds/conditions, so calibration needs a protocol before model changes.",
    ]
elif hard_subject_count >= 12 or both_hard_count >= 4:
    diagnosis = "subject_difficulty_supported"
    recommended_next = "subject_stratified_generalization_objective"
    recommendation_reason = [
        "Subject-level error rates show repeated hard subjects.",
        "Cross-modality overlap suggests at least part of the failure is subject-level rather than modality-specific.",
    ]
elif overall_gain_mean >= 0.02 or overall_gain_max >= 0.05:
    diagnosis = "global_threshold_calibration_possible"
    recommended_next = "calibration_protocol_objective"
    recommendation_reason = [
        "Threshold tuning gives non-trivial improvement in at least some conditions.",
        "Next step should define a validation-only calibration protocol rather than changing architecture.",
    ]
else:
    diagnosis = "representation_or_label_task_issue_still_likely"
    recommended_next = "representation_label_task_redesign_objective"
    recommendation_reason = [
        "Calibration gains and subject-overlap effects are not strong enough to explain the weak results.",
        "Next step should revisit representation, task formulation, label policy, or dataset assumptions before architecture escalation.",
    ]

diagnostic_summary = {
    "loaded_prediction_files": [str(p) for p in input_files],
    "load_errors": errors,
    "n_prediction_rows": int(len(all_pred)),
    "n_threshold_rows": int(len(threshold_df)),
    "n_subject_rows": int(len(subject_df)),
    "n_overlap_rows": int(len(overlap_df)),
    "overall_macro_f1_gain_mean": overall_gain_mean,
    "overall_macro_f1_gain_max": overall_gain_max,
    "fold_macro_f1_gain_mean": fold_gain_mean,
    "threshold_std_mean": threshold_std_mean,
    "threshold_instability_count": threshold_instability_count,
    "large_threshold_gain_count": large_gain_count,
    "hard_subject_count": hard_subject_count,
    "cross_modality_both_hard_count": both_hard_count,
    "cross_modality_mean_common_failure_score": mean_common_failure_score,
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next,
    "recommendation_reason": recommendation_reason,
}

# Compact report tables.
def clean_records(df: pd.DataFrame, max_rows: int | None = None) -> list[dict[str, Any]]:
    if max_rows is not None:
        df = df.head(max_rows)
    records = df.replace({np.nan: None}).to_dict(orient="records")
    return records


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


def md_table(rows: list[dict[str, Any]], headers: list[tuple[str, str]]) -> str:
    lines = ["| " + " | ".join(h[0] for h in headers) + " |"]
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


top_threshold = overall.sort_values(["macro_f1_gain", "best_macro_f1"], ascending=[False, False]).head(16)
top_instability = stability_df.sort_values(["threshold_std", "macro_f1_gain_mean"], ascending=[False, False]).head(16) if not stability_df.empty else pd.DataFrame()
top_subjects = subject_df.sort_values(["error_rate", "n"], ascending=[False, False]).head(20) if not subject_df.empty else pd.DataFrame()
top_overlap = overlap_df.sort_values(["common_failure_score"], ascending=False).head(20) if not overlap_df.empty and "common_failure_score" in overlap_df.columns else pd.DataFrame()
top_stability = stability_df.sort_values(["default_macro_f1_mean", "default_macro_f1_std"], ascending=[False, True]).head(16) if not stability_df.empty else pd.DataFrame()

report = {
    "status": "complete_pending_review",
    "created_or_updated_utc": NOW,
    "objective": "docs/idare_calibration_and_subject_generalization_objective.md",
    "evidence_level": "read-only diagnostic from existing prediction outputs; no final performance claim",
    "diagnostic_summary": diagnostic_summary,
    "outputs": {
        "report_md": str(OUT_MD),
        "report_json": str(OUT_JSON),
        "threshold_summary_csv": str(OUT_THRESH),
        "subject_difficulty_csv": str(OUT_SUBJECT),
        "cross_modality_error_overlap_csv": str(OUT_OVERLAP),
    },
    "top_threshold_gains": clean_records(top_threshold, 30),
    "threshold_instability": clean_records(top_instability, 30),
    "subject_difficulty_top": clean_records(top_subjects, 50),
    "cross_modality_overlap_top": clean_records(top_overlap, 50),
    "recipe_policy_stability_top": clean_records(top_stability, 30),
    "not_authorized": objective.get("not_authorized", []),
}
OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = f"""# I-DARE Calibration and Subject-Generalization Report

## Status

Calibration and subject-generalization diagnostic complete; pending human review.

Generated UTC: `{NOW}`

This report is read-only and uses existing prediction outputs only.

No new performance training was run.

## Diagnostic Summary

| Item | Value |
|---|---|
| Prediction rows loaded | {diagnostic_summary["n_prediction_rows"]} |
| Threshold summary rows | {diagnostic_summary["n_threshold_rows"]} |
| Subject difficulty rows | {diagnostic_summary["n_subject_rows"]} |
| Cross-modality overlap rows | {diagnostic_summary["n_overlap_rows"]} |
| Overall macro-F1 gain mean | {fmt(overall_gain_mean)} |
| Overall macro-F1 gain max | {fmt(overall_gain_max)} |
| Fold macro-F1 gain mean | {fmt(fold_gain_mean)} |
| Mean threshold std | {fmt(threshold_std_mean)} |
| Threshold instability count | {threshold_instability_count} |
| Large threshold-gain count | {large_gain_count} |
| Hard subject count | {hard_subject_count} |
| Cross-modality both-hard count | {both_hard_count} |
| Cross-modality mean common-failure score | {fmt(mean_common_failure_score)} |
| Diagnosis | `{diagnosis}` |
| Recommended next objective | `{recommended_next}` |

## Top Threshold Gains

{md_table(clean_records(top_threshold, 16), [
    ("Source", "source_group"),
    ("Modality", "modality"),
    ("Variant", "variant"),
    ("Task", "task"),
    ("Policy", "label_policy"),
    ("Recipe", "recipe"),
    ("Default F1", "default_macro_f1"),
    ("Best F1", "best_macro_f1"),
    ("F1 gain", "macro_f1_gain"),
    ("Best th", "best_threshold"),
    ("One-class", "threshold_one_class"),
])}

## Fold Threshold Instability

{md_table(clean_records(top_instability, 16), [
    ("Source", "source_group"),
    ("Modality", "modality"),
    ("Variant", "variant"),
    ("Task", "task"),
    ("Policy", "label_policy"),
    ("Recipe", "recipe"),
    ("Folds", "folds"),
    ("Mean gain", "macro_f1_gain_mean"),
    ("Th std", "threshold_std"),
    ("Th min", "threshold_min"),
    ("Th max", "threshold_max"),
    ("Instability", "calibration_instability_flag"),
])}

## Hard Subject Ranking

{md_table(clean_records(top_subjects, 20), [
    ("Subject", "subject_id"),
    ("Modality", "modality"),
    ("Task", "task"),
    ("Policy", "label_policy"),
    ("N", "n"),
    ("Errors", "errors"),
    ("Error rate", "error_rate"),
    ("Sources", "n_sources"),
    ("Recipes", "n_recipes"),
    ("Hard", "hard_subject_flag"),
])}

## Cross-modality Error Overlap

{md_table(clean_records(top_overlap, 20), [
    ("Subject", "subject_id"),
    ("Task", "task"),
    ("Policy", "label_policy"),
    ("EEG err", "error_rate_EEG"),
    ("EMG err", "error_rate_EMG"),
    ("Common score", "common_failure_score"),
    ("Both hard", "both_hard_flag"),
    ("EEG-specific", "eeg_specific_hard_flag"),
    ("EMG-specific", "emg_specific_hard_flag"),
])}

## Recipe / Policy Stability Map

{md_table(clean_records(top_stability, 16), [
    ("Source", "source_group"),
    ("Modality", "modality"),
    ("Variant", "variant"),
    ("Task", "task"),
    ("Policy", "label_policy"),
    ("Recipe", "recipe"),
    ("Default F1 mean", "default_macro_f1_mean"),
    ("Default F1 std", "default_macro_f1_std"),
    ("Gain mean", "macro_f1_gain_mean"),
    ("Stable", "stable_recipe_flag"),
])}

## Recommendation

Recommended next objective:

`{recommended_next}`

Reason:

"""
for reason in recommendation_reason:
    md += f"- {reason}\n"

md += """
## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- new performance training
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Output Files

- `docs/idare_calibration_subject_generalization_report.md`
- `docs/idare_calibration_subject_generalization_report.json`
- `docs/idare_calibration_subject_threshold_summary.csv`
- `docs/idare_subject_difficulty_ranking.csv`
- `docs/idare_cross_modality_error_overlap.csv`

## Next Allowed Step

Human review / closeout of this calibration and subject-generalization report.

Only after review should the next objective be created.
"""
OUT_MD.write_text(md, encoding="utf-8")

# Update roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
report_row = "| I-DARE calibration and subject-generalization report | read-only diagnostic report complete; pending human review | yes | `docs/idare_calibration_subject_generalization_report.md` | Human review / closeout before the next diagnostic or fix objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |"

if "I-DARE calibration and subject-generalization report" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE calibration and subject-generalization objective |"):
            out.append(report_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert calibration report row")
    project_md = "\n".join(out) + "\n"

bullet = "- Calibration and subject-generalization diagnostics are complete in `docs/idare_calibration_subject_generalization_report.md`; next work is human review/closeout before creating a fix objective."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: project status marker not found")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)

PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_calibration_subject_generalization_report"] = {
    "status": "complete_pending_review",
    "evidence": str(OUT_MD),
    "evidence_json": str(OUT_JSON),
    "threshold_summary_csv": str(OUT_THRESH),
    "subject_difficulty_csv": str(OUT_SUBJECT),
    "cross_modality_error_overlap_csv": str(OUT_OVERLAP),
    "evidence_level": "read-only diagnostic from existing prediction outputs; no final performance claim",
    "diagnostic_summary": diagnostic_summary,
    "next_allowed_step": "Human review / closeout of calibration and subject-generalization report.",
    "not_authorized": objective.get("not_authorized", []),
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_CALIBRATION_SUBJECT_REPORT_WRITTEN")
print(OUT_MD)
print(OUT_JSON)
print(OUT_THRESH)
print(OUT_SUBJECT)
print(OUT_OVERLAP)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next)
PY
echo

echo "===== 4) validate generated outputs ====="
"$PY" - <<'PY'
import json
import pandas as pd
from pathlib import Path

for p in [
    Path("docs/idare_calibration_subject_generalization_report.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")

for p in [
    Path("docs/idare_calibration_subject_threshold_summary.csv"),
    Path("docs/idare_subject_difficulty_ranking.csv"),
    Path("docs/idare_cross_modality_error_overlap.csv"),
]:
    df = pd.read_csv(p)
    print(f"{p.name} rows=", len(df))
PY

grep -n "## Status\|## Diagnostic Summary\|## Top Threshold Gains\|## Fold Threshold Instability\|## Hard Subject Ranking\|## Cross-modality Error Overlap\|## Recommendation\|## Next Allowed Step" docs/idare_calibration_subject_generalization_report.md
grep -n "calibration and subject-generalization report" docs/project_status_current.md
echo

echo "===== 5) file list ====="
ls -lh \
  docs/idare_calibration_subject_generalization_report.md \
  docs/idare_calibration_subject_generalization_report.json \
  docs/idare_calibration_subject_threshold_summary.csv \
  docs/idare_subject_difficulty_ranking.csv \
  docs/idare_cross_modality_error_overlap.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push calibration + subject-generalization report ====="
git add \
  docs/idare_calibration_subject_generalization_report.md \
  docs/idare_calibration_subject_generalization_report.json \
  docs/idare_calibration_subject_threshold_summary.csv \
  docs/idare_subject_difficulty_ranking.csv \
  docs/idare_cross_modality_error_overlap.csv \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "analysis: add I-DARE calibration subject diagnostics"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_calibration_subject_report.log"
