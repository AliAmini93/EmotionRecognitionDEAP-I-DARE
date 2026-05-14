#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)


ROOT = Path(__file__).resolve().parents[2]
ROCA_DIR = ROOT / "docs" / "roca"

AROUSAL_PRED = ROCA_DIR / "eeg_gaussian10_full_loso_predictions_current.csv"
VALENCE_PRED = ROCA_DIR / "eeg_gaussian10_valence_full_loso_predictions_current.csv"

AROUSAL_EEG_MODEL = "eeg_bc_residual_huber_norm_gaussian10_full_loso"
VALENCE_EEG_MODEL = "eeg_bc_residual_huber_norm_gaussian10_valence_full_loso"
BASELINE_MODEL = "stimulus_only"

OUT_MD = ROCA_DIR / "joint_valence_arousal_subject_macro_report_current.md"
OUT_JSON = ROCA_DIR / "joint_valence_arousal_subject_macro_report_current.json"
OUT_PRED = ROCA_DIR / "joint_valence_arousal_subject_macro_predictions_current.csv"
OUT_POOLED = ROCA_DIR / "joint_valence_arousal_subject_macro_pooled_metrics_current.csv"
OUT_SUBJECT = ROCA_DIR / "joint_valence_arousal_subject_macro_subject_metrics_current.csv"
OUT_SUBJECT_SUMMARY = ROCA_DIR / "joint_valence_arousal_subject_macro_subject_summary_current.csv"
OUT_COMPARISON = ROCA_DIR / "joint_valence_arousal_subject_macro_eeg_vs_stimulus_current.csv"
OUT_FAILURE = ROCA_DIR / "joint_valence_arousal_subject_macro_failure_ranking_current.csv"
OUT_CONFUSION = ROCA_DIR / "joint_valence_arousal_subject_macro_confusion_current.csv"
OUT_CLASS_REPORT = ROCA_DIR / "joint_valence_arousal_subject_macro_classification_report_current.csv"

QUADRANT_NAMES = {
    0: "LV_LA",
    1: "LV_HA",
    2: "HV_LA",
    3: "HV_HA",
}

BINARY_NAMES = {
    0: "low",
    1: "high",
}


def safe_float(x: Any):
    try:
        v = float(x)
    except Exception:
        return None
    return v if math.isfinite(v) else None


def clean_json(x):
    if isinstance(x, dict):
        return {str(k): clean_json(v) for k, v in x.items()}
    if isinstance(x, list):
        return [clean_json(v) for v in x]
    if isinstance(x, tuple):
        return [clean_json(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        v = float(x)
        return v if math.isfinite(v) else None
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    return x


def md_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    if not rows:
        return "_No rows._\n"

    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")

    for row in rows:
        vals = []
        for col in cols:
            val = row.get(col, "")
            if isinstance(val, float):
                vals.append(f"{val:.4f}" if math.isfinite(val) else "")
            elif val is None:
                vals.append("")
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")

    return "\n".join(lines) + "\n"


def require_inputs():
    for path in [AROUSAL_PRED, VALENCE_PRED]:
        if not path.exists():
            raise FileNotFoundError(path)


def pearson(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y = y[m]
    p = p[m]
    if len(y) < 2 or np.std(y) == 0 or np.std(p) == 0:
        return None
    return safe_float(np.corrcoef(y, p)[0, 1])


def spearman(y, p):
    yr = pd.Series(y).rank(method="average").to_numpy(dtype=float)
    pr = pd.Series(p).rank(method="average").to_numpy(dtype=float)
    return pearson(yr, pr)


def safe_auroc(y_true, score):
    y_true = np.asarray(y_true, dtype=int)
    score = np.asarray(score, dtype=float)
    if len(np.unique(y_true)) < 2:
        return None
    try:
        return safe_float(roc_auc_score(y_true, score))
    except Exception:
        return None


def safe_average_precision(y_true, score):
    y_true = np.asarray(y_true, dtype=int)
    score = np.asarray(score, dtype=float)
    if len(np.unique(y_true)) < 2:
        return None
    try:
        return safe_float(average_precision_score(y_true, score))
    except Exception:
        return None


def present_balanced_accuracy(y_true, y_pred, labels):
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    recalls = []

    for label in labels:
        support = int(np.sum(y_true == label))
        if support > 0:
            recalls.append(float(np.sum((y_true == label) & (y_pred == label)) / support))

    return safe_float(np.mean(recalls)) if recalls else None


def load_target(path: Path, target: str, model: str, prefix: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    g = df[df["target"].astype(str).eq(target) & df["model"].astype(str).eq(model)].copy()

    if g.empty:
        raise ValueError(f"No rows found: path={path}, target={target}, model={model}")

    required = [
        "test_subject",
        "stimulus_id",
        "y_true_score",
        "y_pred_score_raw",
        "y_pred_score_clipped",
        "train_stimulus_mean",
        "true_deviation_from_train_stimulus_mean",
        "y_pred_deviation_clipped",
    ]

    for col in required:
        if col not in g.columns:
            raise ValueError(f"Missing column {col} in {path}")

    g = g[required].copy()
    g["test_subject"] = g["test_subject"].astype(int)
    g["stimulus_id"] = g["stimulus_id"].astype(str)

    return g.rename(
        columns={
            "y_true_score": f"{prefix}_true_score",
            "y_pred_score_raw": f"{prefix}_pred_score_raw",
            "y_pred_score_clipped": f"{prefix}_pred_score",
            "train_stimulus_mean": f"{prefix}_train_stimulus_mean",
            "true_deviation_from_train_stimulus_mean": f"{prefix}_true_deviation",
            "y_pred_deviation_clipped": f"{prefix}_pred_deviation",
        }
    )


def make_joint_predictions(group_name: str, valence_model: str, arousal_model: str) -> pd.DataFrame:
    v = load_target(VALENCE_PRED, "valence", valence_model, "valence")
    a = load_target(AROUSAL_PRED, "arousal", arousal_model, "arousal")

    merged = v.merge(a, on=["test_subject", "stimulus_id"], how="inner")

    if len(merged) != min(len(v), len(a)):
        raise ValueError(
            f"Merge row mismatch for {group_name}: valence={len(v)}, arousal={len(a)}, merged={len(merged)}"
        )

    merged["model_group"] = group_name

    merged["valence_true_bin"] = (merged["valence_true_score"] > 5).astype(int)
    merged["valence_pred_bin"] = (merged["valence_pred_score"] > 5).astype(int)

    merged["arousal_true_bin"] = (merged["arousal_true_score"] > 5).astype(int)
    merged["arousal_pred_bin"] = (merged["arousal_pred_score"] > 5).astype(int)

    # 0 = low valence + low arousal
    # 1 = low valence + high arousal
    # 2 = high valence + low arousal
    # 3 = high valence + high arousal
    merged["joint_true_class"] = merged["valence_true_bin"] * 2 + merged["arousal_true_bin"]
    merged["joint_pred_class"] = merged["valence_pred_bin"] * 2 + merged["arousal_pred_bin"]
    merged["joint_true_label"] = merged["joint_true_class"].map(QUADRANT_NAMES)
    merged["joint_pred_label"] = merged["joint_pred_class"].map(QUADRANT_NAMES)

    merged["valence_correct"] = merged["valence_true_bin"].eq(merged["valence_pred_bin"])
    merged["arousal_correct"] = merged["arousal_true_bin"].eq(merged["arousal_pred_bin"])
    merged["joint_correct"] = merged["joint_true_class"].eq(merged["joint_pred_class"])
    merged["dimension_hamming_score"] = (
        merged["valence_correct"].astype(float) + merged["arousal_correct"].astype(float)
    ) / 2.0

    merged["both_dimensions_correct"] = merged["valence_correct"] & merged["arousal_correct"]
    merged["only_valence_correct"] = merged["valence_correct"] & ~merged["arousal_correct"]
    merged["only_arousal_correct"] = ~merged["valence_correct"] & merged["arousal_correct"]
    merged["neither_dimension_correct"] = ~merged["valence_correct"] & ~merged["arousal_correct"]

    return merged


def regression_metrics(y_true, y_pred, prefix: str) -> dict[str, Any]:
    y = np.asarray(y_true, dtype=float)
    p = np.asarray(y_pred, dtype=float)
    err = p - y

    return {
        f"{prefix}_mae_score": safe_float(np.mean(np.abs(err))),
        f"{prefix}_rmse_score": safe_float(np.sqrt(np.mean(err * err))),
        f"{prefix}_pearson_score": pearson(y, p),
        f"{prefix}_spearman_score": spearman(y, p),
        f"{prefix}_true_score_std": safe_float(np.std(y)),
        f"{prefix}_pred_score_std": safe_float(np.std(p)),
        f"{prefix}_pred_over_true_std_ratio": safe_float(np.std(p) / (np.std(y) + 1e-12)),
    }


def deviation_metrics(true_dev, pred_dev, prefix: str) -> dict[str, Any]:
    y = np.asarray(true_dev, dtype=float)
    p = np.asarray(pred_dev, dtype=float)
    err = p - y

    sign_true = np.sign(y)
    sign_pred = np.sign(p)
    nz = sign_true != 0

    return {
        f"{prefix}_mae_deviation": safe_float(np.mean(np.abs(err))),
        f"{prefix}_rmse_deviation": safe_float(np.sqrt(np.mean(err * err))),
        f"{prefix}_pearson_deviation": pearson(y, p),
        f"{prefix}_spearman_deviation": spearman(y, p),
        f"{prefix}_sign_accuracy_deviation": safe_float(np.mean(sign_true[nz] == sign_pred[nz])) if int(nz.sum()) else None,
        f"{prefix}_true_deviation_std": safe_float(np.std(y)),
        f"{prefix}_pred_deviation_std": safe_float(np.std(p)),
        f"{prefix}_pred_over_true_deviation_std_ratio": safe_float(np.std(p) / (np.std(y) + 1e-12)),
        f"{prefix}_mean_abs_true_deviation": safe_float(np.mean(np.abs(y))),
        f"{prefix}_mean_abs_pred_deviation": safe_float(np.mean(np.abs(p))),
    }


def binary_task_metrics(df: pd.DataFrame, group: str, task: str, dim: str, scope: str) -> dict[str, Any]:
    y_true = df[f"{dim}_true_bin"].to_numpy(dtype=int)
    y_pred = df[f"{dim}_pred_bin"].to_numpy(dtype=int)
    score = df[f"{dim}_pred_score"].to_numpy(dtype=float)

    row = {
        "scope": scope,
        "model_group": group,
        "task": task,
        "n": int(len(df)),
        "subjects": int(df["test_subject"].nunique()),
        "accuracy": safe_float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": present_balanced_accuracy(y_true, y_pred, labels=[0, 1]),
        "macro_precision": safe_float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_recall": safe_float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_f1": safe_float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": safe_float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "mcc": safe_float(matthews_corrcoef(y_true, y_pred)) if len(np.unique(y_true)) > 1 else None,
        "cohen_kappa": safe_float(cohen_kappa_score(y_true, y_pred)) if len(np.unique(y_true)) > 1 else None,
        "auroc": safe_auroc(y_true, score),
        "average_precision": safe_average_precision(y_true, score),
        "true_high_rate": safe_float(np.mean(y_true)),
        "pred_high_rate": safe_float(np.mean(y_pred)),
        "majority_class_accuracy": safe_float(max(np.mean(y_true), 1.0 - np.mean(y_true))),
    }

    row["accuracy_lift_vs_majority"] = safe_float(row["accuracy"] - row["majority_class_accuracy"])

    row.update(regression_metrics(df[f"{dim}_true_score"], df[f"{dim}_pred_score"], prefix=dim))
    row.update(deviation_metrics(df[f"{dim}_true_deviation"], df[f"{dim}_pred_deviation"], prefix=dim))

    return row


def joint_task_metrics(df: pd.DataFrame, group: str, scope: str) -> dict[str, Any]:
    y_true = df["joint_true_class"].to_numpy(dtype=int)
    y_pred = df["joint_pred_class"].to_numpy(dtype=int)

    row = {
        "scope": scope,
        "model_group": group,
        "task": "joint_4class_valence_arousal",
        "n": int(len(df)),
        "subjects": int(df["test_subject"].nunique()),
        "accuracy": safe_float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": present_balanced_accuracy(y_true, y_pred, labels=[0, 1, 2, 3]),
        "macro_precision": safe_float(precision_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_recall": safe_float(recall_score(y_true, y_pred, average="macro", zero_division=0)),
        "macro_f1": safe_float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "weighted_f1": safe_float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
        "mcc": safe_float(matthews_corrcoef(y_true, y_pred)) if len(np.unique(y_true)) > 1 else None,
        "cohen_kappa": safe_float(cohen_kappa_score(y_true, y_pred)) if len(np.unique(y_true)) > 1 else None,
        "auroc": None,
        "average_precision": None,
        "true_high_rate": None,
        "pred_high_rate": None,
        "majority_class_accuracy": safe_float(pd.Series(y_true).value_counts(normalize=True).max()),
        "dimension_hamming_accuracy": safe_float(df["dimension_hamming_score"].mean()),
        "both_dimensions_correct_rate": safe_float(df["both_dimensions_correct"].mean()),
        "only_valence_correct_rate": safe_float(df["only_valence_correct"].mean()),
        "only_arousal_correct_rate": safe_float(df["only_arousal_correct"].mean()),
        "neither_dimension_correct_rate": safe_float(df["neither_dimension_correct"].mean()),
    }

    row["accuracy_lift_vs_majority"] = safe_float(row["accuracy"] - row["majority_class_accuracy"])

    for cls, name in QUADRANT_NAMES.items():
        row[f"true_rate_{name}"] = safe_float(np.mean(y_true == cls))
        row[f"pred_rate_{name}"] = safe_float(np.mean(y_pred == cls))

    return row


def build_pooled_metrics(all_pred: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for group, g in all_pred.groupby("model_group"):
        rows.append(binary_task_metrics(g, group, "valence_high_low", "valence", "pooled_trial"))
        rows.append(binary_task_metrics(g, group, "arousal_high_low", "arousal", "pooled_trial"))
        rows.append(joint_task_metrics(g, group, "pooled_trial"))

    return pd.DataFrame(rows)


def build_subject_metrics(all_pred: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for (group, sid), g in all_pred.groupby(["model_group", "test_subject"]):
        rows.append({
            "test_subject": int(sid),
            **binary_task_metrics(g, group, "valence_high_low", "valence", "subject"),
        })
        rows.append({
            "test_subject": int(sid),
            **binary_task_metrics(g, group, "arousal_high_low", "arousal", "subject"),
        })
        rows.append({
            "test_subject": int(sid),
            **joint_task_metrics(g, group, "subject"),
        })

    return pd.DataFrame(rows)


def summarize_subject_metrics(subject_metrics: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        "accuracy",
        "balanced_accuracy",
        "macro_precision",
        "macro_recall",
        "macro_f1",
        "weighted_f1",
        "mcc",
        "cohen_kappa",
        "auroc",
        "average_precision",
        "accuracy_lift_vs_majority",
        "dimension_hamming_accuracy",
        "both_dimensions_correct_rate",
        "only_valence_correct_rate",
        "only_arousal_correct_rate",
        "neither_dimension_correct_rate",
        "valence_pearson_deviation",
        "arousal_pearson_deviation",
        "valence_pred_over_true_deviation_std_ratio",
        "arousal_pred_over_true_deviation_std_ratio",
    ]

    rows = []
    for (group, task), g in subject_metrics.groupby(["model_group", "task"]):
        row = {
            "scope": "subject_macro_summary",
            "model_group": group,
            "task": task,
            "subjects": int(g["test_subject"].nunique()),
        }

        for col in metric_cols:
            if col not in g.columns:
                continue
            vals = pd.to_numeric(g[col], errors="coerce").dropna().to_numpy(dtype=float)
            if len(vals) == 0:
                continue

            row[f"{col}_mean"] = safe_float(np.mean(vals))
            row[f"{col}_median"] = safe_float(np.median(vals))
            row[f"{col}_std"] = safe_float(np.std(vals))
            row[f"{col}_min"] = safe_float(np.min(vals))
            row[f"{col}_max"] = safe_float(np.max(vals))

        rows.append(row)

    return pd.DataFrame(rows)


def build_comparison(subject_metrics: pd.DataFrame, pooled_metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []

    compare_cols = [
        "accuracy",
        "balanced_accuracy",
        "macro_f1",
        "weighted_f1",
        "mcc",
        "cohen_kappa",
        "auroc",
        "average_precision",
        "accuracy_lift_vs_majority",
        "dimension_hamming_accuracy",
        "both_dimensions_correct_rate",
        "neither_dimension_correct_rate",
    ]

    for task in subject_metrics["task"].unique():
        eeg = subject_metrics[
            subject_metrics["model_group"].eq("eeg_gaussian10") & subject_metrics["task"].eq(task)
        ].copy()
        stim = subject_metrics[
            subject_metrics["model_group"].eq("stimulus_only") & subject_metrics["task"].eq(task)
        ].copy()

        merged = eeg.merge(
            stim,
            on=["test_subject", "task"],
            how="inner",
            suffixes=("_eeg", "_stimulus"),
        )

        for _, r in merged.iterrows():
            row = {
                "scope": "subject",
                "test_subject": int(r["test_subject"]),
                "task": task,
            }

            for col in compare_cols:
                eeg_col = f"{col}_eeg"
                stim_col = f"{col}_stimulus"
                if eeg_col in merged.columns and stim_col in merged.columns:
                    ev = safe_float(r[eeg_col])
                    sv = safe_float(r[stim_col])
                    row[f"eeg_{col}"] = ev
                    row[f"stimulus_{col}"] = sv
                    row[f"delta_{col}_eeg_minus_stimulus"] = (
                        safe_float(ev - sv) if ev is not None and sv is not None else None
                    )

            rows.append(row)

    # Add pooled comparison rows.
    for task in pooled_metrics["task"].unique():
        eeg = pooled_metrics[
            pooled_metrics["model_group"].eq("eeg_gaussian10") & pooled_metrics["task"].eq(task)
        ]
        stim = pooled_metrics[
            pooled_metrics["model_group"].eq("stimulus_only") & pooled_metrics["task"].eq(task)
        ]
        if eeg.empty or stim.empty:
            continue

        er = eeg.iloc[0]
        sr = stim.iloc[0]
        row = {
            "scope": "pooled_trial",
            "test_subject": None,
            "task": task,
        }

        for col in compare_cols:
            ev = safe_float(er.get(col))
            sv = safe_float(sr.get(col))
            row[f"eeg_{col}"] = ev
            row[f"stimulus_{col}"] = sv
            row[f"delta_{col}_eeg_minus_stimulus"] = (
                safe_float(ev - sv) if ev is not None and sv is not None else None
            )

        rows.append(row)

    return pd.DataFrame(rows)


def build_failure_ranking(comparison: pd.DataFrame) -> pd.DataFrame:
    subj = comparison[comparison["scope"].eq("subject")].copy()
    rows = []

    for sid, g in subj.groupby("test_subject"):
        row = {"test_subject": int(sid)}

        failure_score = 0.0
        for task in ["valence_high_low", "arousal_high_low", "joint_4class_valence_arousal"]:
            t = g[g["task"].eq(task)]
            if t.empty:
                continue
            r = t.iloc[0]

            for metric in ["accuracy", "balanced_accuracy", "macro_f1", "mcc"]:
                col = f"delta_{metric}_eeg_minus_stimulus"
                val = safe_float(r.get(col))
                row[f"{task}_delta_{metric}"] = val
                if val is not None:
                    failure_score += max(0.0, -val)

        row["failure_score"] = safe_float(failure_score)
        rows.append(row)

    return pd.DataFrame(rows).sort_values("failure_score", ascending=False).reset_index(drop=True)


def build_confusion_and_reports(all_pred: pd.DataFrame):
    confusion_rows = []
    report_rows = []

    task_defs = [
        ("valence_high_low", "valence_true_bin", "valence_pred_bin", [0, 1], BINARY_NAMES),
        ("arousal_high_low", "arousal_true_bin", "arousal_pred_bin", [0, 1], BINARY_NAMES),
        ("joint_4class_valence_arousal", "joint_true_class", "joint_pred_class", [0, 1, 2, 3], QUADRANT_NAMES),
    ]

    for group, g in all_pred.groupby("model_group"):
        for task, y_col, p_col, labels, names in task_defs:
            y_true = g[y_col].to_numpy(dtype=int)
            y_pred = g[p_col].to_numpy(dtype=int)

            cm = confusion_matrix(y_true, y_pred, labels=labels)
            for i, actual in enumerate(labels):
                for j, predicted in enumerate(labels):
                    confusion_rows.append({
                        "model_group": group,
                        "task": task,
                        "actual_class": int(actual),
                        "actual_label": names.get(actual, str(actual)),
                        "predicted_class": int(predicted),
                        "predicted_label": names.get(predicted, str(predicted)),
                        "count": int(cm[i, j]),
                    })

            report = classification_report(
                y_true,
                y_pred,
                labels=labels,
                target_names=[names.get(x, str(x)) for x in labels],
                output_dict=True,
                zero_division=0,
            )

            for label, vals in report.items():
                if isinstance(vals, dict):
                    row = {
                        "model_group": group,
                        "task": task,
                        "label": label,
                    }
                    row.update({k: safe_float(v) for k, v in vals.items()})
                    report_rows.append(row)
                else:
                    report_rows.append({
                        "model_group": group,
                        "task": task,
                        "label": label,
                        "value": safe_float(vals),
                    })

    return pd.DataFrame(confusion_rows), pd.DataFrame(report_rows)


def write_report(
    all_pred: pd.DataFrame,
    pooled: pd.DataFrame,
    subject_metrics: pd.DataFrame,
    subject_summary: pd.DataFrame,
    comparison: pd.DataFrame,
    failure: pd.DataFrame,
    confusion: pd.DataFrame,
    class_report: pd.DataFrame,
):
    all_pred.to_csv(OUT_PRED, index=False)
    pooled.to_csv(OUT_POOLED, index=False)
    subject_metrics.to_csv(OUT_SUBJECT, index=False)
    subject_summary.to_csv(OUT_SUBJECT_SUMMARY, index=False)
    comparison.to_csv(OUT_COMPARISON, index=False)
    failure.to_csv(OUT_FAILURE, index=False)
    confusion.to_csv(OUT_CONFUSION, index=False)
    class_report.to_csv(OUT_CLASS_REPORT, index=False)

    main_cols = [
        "scope",
        "model_group",
        "task",
        "n",
        "subjects",
        "accuracy",
        "balanced_accuracy",
        "macro_f1",
        "weighted_f1",
        "mcc",
        "cohen_kappa",
        "auroc",
        "average_precision",
        "accuracy_lift_vs_majority",
        "dimension_hamming_accuracy",
        "both_dimensions_correct_rate",
        "neither_dimension_correct_rate",
    ]

    summary_cols = [
        "scope",
        "model_group",
        "task",
        "subjects",
        "accuracy_mean",
        "accuracy_median",
        "balanced_accuracy_mean",
        "balanced_accuracy_median",
        "macro_f1_mean",
        "macro_f1_median",
        "mcc_mean",
        "cohen_kappa_mean",
        "auroc_mean",
        "dimension_hamming_accuracy_mean",
        "both_dimensions_correct_rate_mean",
        "neither_dimension_correct_rate_mean",
    ]

    comparison_cols = [
        "scope",
        "test_subject",
        "task",
        "eeg_accuracy",
        "stimulus_accuracy",
        "delta_accuracy_eeg_minus_stimulus",
        "eeg_balanced_accuracy",
        "stimulus_balanced_accuracy",
        "delta_balanced_accuracy_eeg_minus_stimulus",
        "eeg_macro_f1",
        "stimulus_macro_f1",
        "delta_macro_f1_eeg_minus_stimulus",
        "eeg_mcc",
        "stimulus_mcc",
        "delta_mcc_eeg_minus_stimulus",
    ]

    failure_cols = [
        "test_subject",
        "failure_score",
        "valence_high_low_delta_accuracy",
        "valence_high_low_delta_macro_f1",
        "arousal_high_low_delta_accuracy",
        "arousal_high_low_delta_macro_f1",
        "joint_4class_valence_arousal_delta_accuracy",
        "joint_4class_valence_arousal_delta_macro_f1",
    ]

    existing_main_cols = [c for c in main_cols if c in pooled.columns]
    existing_summary_cols = [c for c in summary_cols if c in subject_summary.columns]
    existing_comparison_cols = [c for c in comparison_cols if c in comparison.columns]
    existing_failure_cols = [c for c in failure_cols if c in failure.columns]

    pooled_comparison = comparison[comparison["scope"].eq("pooled_trial")].copy()
    subject_comparison = comparison[comparison["scope"].eq("subject")].copy()

    lines = []
    lines.append("# ROCA-I-DARE Joint Valence/Arousal Subject-Macro Diagnostic Report\n")
    lines.append("No model training was performed here. This report merges full LOSO Valence and Arousal predictions.\n")

    lines.append("## Evaluation levels\n")
    lines.append("- `pooled_trial`: metrics over all 2016 trials pooled together.")
    lines.append("- `subject`: metrics computed separately for each held-out subject over that subject's 32 trials.")
    lines.append("- `subject_macro_summary`: mean/median/std/min/max of subject-level metrics across subjects.")
    lines.append("")

    lines.append("## Label definitions\n")
    lines.append("- Valence high: `valence_score > 5`")
    lines.append("- Arousal high: `arousal_score > 5`")
    lines.append("- Joint classes: `LV_LA`, `LV_HA`, `HV_LA`, `HV_HA`")
    lines.append("")

    lines.append("## Pooled trial-level metrics\n")
    lines.append(md_table(pooled.to_dict(orient="records"), existing_main_cols))

    lines.append("\n## Subject-macro summary\n")
    lines.append(md_table(subject_summary.to_dict(orient="records"), existing_summary_cols))

    lines.append("\n## Pooled EEG vs stimulus-only comparison\n")
    lines.append(md_table(pooled_comparison.to_dict(orient="records"), existing_comparison_cols))

    lines.append("\n## Worst subjects by diagnostic failure score\n")
    lines.append(md_table(failure.head(20).to_dict(orient="records"), existing_failure_cols))

    lines.append("\n## Confusion matrices\n")
    for (group, task), g in confusion.groupby(["model_group", "task"]):
        lines.append(f"\n### {group} / {task}\n")
        pivot = g.pivot(index="actual_label", columns="predicted_label", values="count").fillna(0).astype(int)
        pivot = pivot.reset_index()
        lines.append(md_table(pivot.to_dict(orient="records"), list(pivot.columns)))

    lines.append("\n## Diagnostic notes\n")
    lines.append(
        "- Accuracy shows exact correctness, but can be misleading under class imbalance.\n"
        "- Balanced accuracy is the mean recall over available classes and is safer when high/low are imbalanced.\n"
        "- Macro-F1 weights classes equally and helps detect one-class collapse.\n"
        "- MCC and Cohen's kappa are stricter agreement diagnostics; values near 0 mean weak practical classification agreement.\n"
        "- Joint 4-class accuracy equals both Valence and Arousal being correct for a trial.\n"
        "- Dimension hamming accuracy gives partial credit: one dimension correct = 0.5, both correct = 1.0.\n"
        "- Subject-macro metrics are crucial because the protocol is cross-subject LOSO.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "protocol": "Joint Valence/Arousal high-low subject-macro diagnostic report",
        "inputs": {
            "arousal_predictions": str(AROUSAL_PRED),
            "valence_predictions": str(VALENCE_PRED),
            "arousal_eeg_model": AROUSAL_EEG_MODEL,
            "valence_eeg_model": VALENCE_EEG_MODEL,
            "baseline_model": BASELINE_MODEL,
        },
        "outputs": {
            "predictions": str(OUT_PRED),
            "pooled_metrics": str(OUT_POOLED),
            "subject_metrics": str(OUT_SUBJECT),
            "subject_summary": str(OUT_SUBJECT_SUMMARY),
            "comparison": str(OUT_COMPARISON),
            "failure_ranking": str(OUT_FAILURE),
            "confusion": str(OUT_CONFUSION),
            "classification_report": str(OUT_CLASS_REPORT),
        },
        "pooled_metrics": pooled.to_dict(orient="records"),
        "subject_summary": subject_summary.to_dict(orient="records"),
        "pooled_comparison": pooled_comparison.to_dict(orient="records"),
        "worst_subjects": failure.head(30).to_dict(orient="records"),
        "notes": [
            "No training was run.",
            "Predictions are cross-subject because they come from full LOSO runs.",
            "Pooled metrics are trial-level pooled over 2016 rows.",
            "Subject-macro metrics compute per-subject performance first, then summarize over subjects.",
        ],
    }

    OUT_JSON.write_text(json.dumps(clean_json(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    print("ROCA step 05n completed.")
    print(f"wrote: {OUT_MD}")
    print(f"wrote: {OUT_JSON}")
    print(f"wrote: {OUT_PRED}")
    print(f"wrote: {OUT_POOLED}")
    print(f"wrote: {OUT_SUBJECT}")
    print(f"wrote: {OUT_SUBJECT_SUMMARY}")
    print(f"wrote: {OUT_COMPARISON}")
    print(f"wrote: {OUT_FAILURE}")
    print(f"wrote: {OUT_CONFUSION}")
    print(f"wrote: {OUT_CLASS_REPORT}")
    print()
    print("Pooled trial-level metrics:")
    print(pooled[existing_main_cols].to_string(index=False))
    print()
    print("Subject-macro summary:")
    print(subject_summary[existing_summary_cols].to_string(index=False))
    print()
    print("Pooled EEG vs stimulus-only comparison:")
    print(pooled_comparison[existing_comparison_cols].to_string(index=False))
    print()
    print("Worst subjects:")
    print(failure.head(20)[existing_failure_cols].to_string(index=False))


def main():
    require_inputs()

    eeg = make_joint_predictions(
        group_name="eeg_gaussian10",
        valence_model=VALENCE_EEG_MODEL,
        arousal_model=AROUSAL_EEG_MODEL,
    )

    stim = make_joint_predictions(
        group_name="stimulus_only",
        valence_model=BASELINE_MODEL,
        arousal_model=BASELINE_MODEL,
    )

    all_pred = pd.concat([eeg, stim], ignore_index=True)

    pooled = build_pooled_metrics(all_pred)
    subject_metrics = build_subject_metrics(all_pred)
    subject_summary = summarize_subject_metrics(subject_metrics)
    comparison = build_comparison(subject_metrics, pooled)
    failure = build_failure_ranking(comparison)
    confusion, class_report = build_confusion_and_reports(all_pred)

    write_report(
        all_pred=all_pred,
        pooled=pooled,
        subject_metrics=subject_metrics,
        subject_summary=subject_summary,
        comparison=comparison,
        failure=failure,
        confusion=confusion,
        class_report=class_report,
    )


if __name__ == "__main__":
    main()
