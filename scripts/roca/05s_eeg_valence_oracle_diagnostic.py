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
    balanced_accuracy_score,
    f1_score,
    matthews_corrcoef,
    roc_auc_score,
    confusion_matrix,
)


ROOT = Path(__file__).resolve().parents[2]
ROCA_DIR = ROOT / "docs" / "roca"

ORACLE_PRED = ROCA_DIR / "eeg_gaussian10_valence_test_oracle_predictions_current.csv"
CLEAN_PRED = ROCA_DIR / "eeg_gaussian10_valence_full_loso_predictions_current.csv"
ORACLE_FOLD = ROCA_DIR / "eeg_gaussian10_valence_test_oracle_fold_summary_current.csv"

OUT_MD = ROCA_DIR / "eeg_valence_oracle_diagnostic_current.md"
OUT_JSON = ROCA_DIR / "eeg_valence_oracle_diagnostic_current.json"
OUT_POOLED = ROCA_DIR / "eeg_valence_oracle_diagnostic_pooled_current.csv"
OUT_SUBJECT = ROCA_DIR / "eeg_valence_oracle_diagnostic_subject_current.csv"
OUT_COMPARISON = ROCA_DIR / "eeg_valence_oracle_diagnostic_comparison_current.csv"
OUT_FAILURE = ROCA_DIR / "eeg_valence_oracle_diagnostic_failure_current.csv"
OUT_EPOCH = ROCA_DIR / "eeg_valence_oracle_diagnostic_epoch_current.csv"


ORACLE_MODEL = "eeg_bc_residual_huber_norm_gaussian10_valence_test_oracle"
CLEAN_MODEL = "eeg_bc_residual_huber_norm_gaussian10_valence_full_loso"
BASELINE_MODEL = "stimulus_only"


def safe_float(x: Any):
    try:
        v = float(x)
    except Exception:
        return None
    return v if math.isfinite(v) else None


def table_block(df: pd.DataFrame, max_rows: int | None = None) -> str:
    d = df.copy()
    if max_rows is not None:
        d = d.head(max_rows)
    return "```\n" + d.to_string(index=False) + "\n```"


def ensure_prediction_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "y_true_score" not in df.columns:
        for candidate in ["true_score", "y_true", "score_true"]:
            if candidate in df.columns:
                df["y_true_score"] = df[candidate]
                break

    if "y_pred_score" not in df.columns:
        for candidate in [
            "y_pred_score_clipped",
            "y_pred_score_raw",
            "pred_score",
            "predicted_score",
            "y_prediction_score",
            "score_pred",
        ]:
            if candidate in df.columns:
                df["y_pred_score"] = df[candidate]
                break

    if "predicted_deviation_from_train_stimulus_mean" not in df.columns:
        for candidate in [
            "y_pred_deviation_clipped",
            "y_pred_deviation_raw",
            "predicted_deviation",
            "pred_dev",
        ]:
            if candidate in df.columns:
                df["predicted_deviation_from_train_stimulus_mean"] = df[candidate]
                break

    if "y_pred_score" not in df.columns:
        needed = ["train_stimulus_mean", "predicted_deviation_from_train_stimulus_mean"]
        if all(c in df.columns for c in needed):
            df["y_pred_score"] = (
                df["train_stimulus_mean"].astype(float)
                + df["predicted_deviation_from_train_stimulus_mean"].astype(float)
            )

    if "predicted_deviation_from_train_stimulus_mean" not in df.columns:
        needed = ["y_pred_score", "train_stimulus_mean"]
        if all(c in df.columns for c in needed):
            df["predicted_deviation_from_train_stimulus_mean"] = (
                df["y_pred_score"].astype(float)
                - df["train_stimulus_mean"].astype(float)
            )

    required = [
        "y_true_score",
        "y_pred_score",
        "true_deviation_from_train_stimulus_mean",
        "predicted_deviation_from_train_stimulus_mean",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(
            "Missing required prediction columns after normalization: "
            + ", ".join(missing)
            + "\nAvailable columns: "
            + ", ".join(map(str, df.columns))
        )

    return df


def binary_metrics(df: pd.DataFrame) -> dict[str, Any]:
    df = ensure_prediction_columns(df)
    y = (df["y_true_score"].to_numpy(dtype=float) > 5.0).astype(int)
    score = df["y_pred_score"].to_numpy(dtype=float)
    pred = (score > 5.0).astype(int)

    out = {
        "n": int(len(df)),
        "subjects": int(df["test_subject"].nunique()),
        "mae": safe_float(np.mean(np.abs(df["y_true_score"] - df["y_pred_score"]))),
        "rmse": safe_float(np.sqrt(np.mean((df["y_true_score"] - df["y_pred_score"]) ** 2))),
        "accuracy": safe_float(accuracy_score(y, pred)),
        "balanced_accuracy": safe_float(balanced_accuracy_score(y, pred)),
        "macro_f1": safe_float(f1_score(y, pred, average="macro", zero_division=0)),
        "mcc": safe_float(matthews_corrcoef(y, pred)),
        "pred_dev_std": safe_float(df["predicted_deviation_from_train_stimulus_mean"].std(ddof=0)),
        "true_dev_std": safe_float(df["true_deviation_from_train_stimulus_mean"].std(ddof=0)),
        "dev_pearson": None,
    }

    true_dev = df["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
    pred_dev = df["predicted_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
    if len(df) >= 2 and np.std(true_dev) > 0 and np.std(pred_dev) > 0:
        out["dev_pearson"] = safe_float(np.corrcoef(true_dev, pred_dev)[0, 1])

    try:
        if len(np.unique(y)) == 2:
            out["auroc"] = safe_float(roc_auc_score(y, score))
        else:
            out["auroc"] = None
    except Exception:
        out["auroc"] = None

    cm = confusion_matrix(y, pred, labels=[0, 1])
    out.update({
        "tn": int(cm[0, 0]),
        "fp": int(cm[0, 1]),
        "fn": int(cm[1, 0]),
        "tp": int(cm[1, 1]),
    })

    return out


def load_predictions() -> pd.DataFrame:
    oracle = ensure_prediction_columns(pd.read_csv(ORACLE_PRED))
    clean = ensure_prediction_columns(pd.read_csv(CLEAN_PRED))

    oracle = oracle[oracle["model"].isin([ORACLE_MODEL, BASELINE_MODEL])].copy()
    oracle["run_group"] = oracle["model"].map({
        ORACLE_MODEL: "oracle_test_checkpoint",
        BASELINE_MODEL: "stimulus_only_oracle_file",
    })

    clean = clean[clean["model"].isin([CLEAN_MODEL, BASELINE_MODEL])].copy()
    clean["run_group"] = clean["model"].map({
        CLEAN_MODEL: "clean_gaussian10",
        BASELINE_MODEL: "stimulus_only_clean_file",
    })

    df = pd.concat([oracle, clean], ignore_index=True)
    return df


def main():
    df = load_predictions()

    pooled_rows = []
    for group, g in df.groupby("run_group", sort=False):
        row = {"scope": "pooled_trial", "run_group": group}
        row.update(binary_metrics(g))
        pooled_rows.append(row)

    pooled = pd.DataFrame(pooled_rows)

    subject_rows = []
    for (group, sid), g in df.groupby(["run_group", "test_subject"], sort=False):
        row = {"scope": "subject", "run_group": group, "test_subject": int(sid)}
        row.update(binary_metrics(g))
        subject_rows.append(row)

    subject = pd.DataFrame(subject_rows)

    comp_rows = []
    pivot = subject.pivot(index="test_subject", columns="run_group")
    metric_cols = ["rmse", "mae", "accuracy", "balanced_accuracy", "macro_f1", "mcc", "auroc", "dev_pearson", "pred_dev_std"]
    for sid in sorted(subject["test_subject"].unique()):
        row = {"test_subject": int(sid)}
        for metric in metric_cols:
            for group in ["oracle_test_checkpoint", "clean_gaussian10", "stimulus_only_oracle_file"]:
                try:
                    row[f"{group}_{metric}"] = safe_float(pivot.loc[sid, (metric, group)])
                except Exception:
                    row[f"{group}_{metric}"] = None

            if row.get(f"oracle_test_checkpoint_{metric}") is not None and row.get(f"clean_gaussian10_{metric}") is not None:
                row[f"delta_oracle_minus_clean_{metric}"] = safe_float(
                    row[f"oracle_test_checkpoint_{metric}"] - row[f"clean_gaussian10_{metric}"]
                )
            if row.get(f"oracle_test_checkpoint_{metric}") is not None and row.get(f"stimulus_only_oracle_file_{metric}") is not None:
                row[f"delta_oracle_minus_stimulus_{metric}"] = safe_float(
                    row[f"oracle_test_checkpoint_{metric}"] - row[f"stimulus_only_oracle_file_{metric}"]
                )
        comp_rows.append(row)

    comparison = pd.DataFrame(comp_rows)

    failure = comparison.copy()
    # For RMSE, positive delta means oracle is worse. For macro-F1, negative delta means oracle is worse.
    failure["failure_score"] = (
        failure["delta_oracle_minus_stimulus_rmse"].fillna(0).clip(lower=0)
        + (-failure["delta_oracle_minus_stimulus_macro_f1"].fillna(0)).clip(lower=0)
        + failure["delta_oracle_minus_clean_rmse"].fillna(0).clip(lower=0)
    )
    failure = failure.sort_values("failure_score", ascending=False).reset_index(drop=True)

    fold = pd.read_csv(ORACLE_FOLD)
    epoch = fold[["test_subject", "best_epoch", "best_val_rmse_scaled", "rmse", "dev_pearson", "pred_dev_std", "true_dev_std"]].copy()
    epoch["std_ratio_pred_over_true"] = epoch["pred_dev_std"] / epoch["true_dev_std"].replace(0, np.nan)

    payload = {
        "pooled": pooled.to_dict(orient="records"),
        "subject_macro": subject.groupby("run_group").agg({
            "accuracy": ["mean", "median"],
            "balanced_accuracy": ["mean", "median"],
            "macro_f1": ["mean", "median"],
            "mcc": ["mean", "median"],
            "auroc": ["mean", "median"],
            "rmse": ["mean", "median"],
            "dev_pearson": ["mean", "median"],
            "pred_dev_std": ["mean", "median"],
        }).to_json(),
        "best_epoch_summary": {
            "min": int(epoch["best_epoch"].min()),
            "median": safe_float(epoch["best_epoch"].median()),
            "mean": safe_float(epoch["best_epoch"].mean()),
            "max": int(epoch["best_epoch"].max()),
        },
    }

    pooled.to_csv(OUT_POOLED, index=False)
    subject.to_csv(OUT_SUBJECT, index=False)
    comparison.to_csv(OUT_COMPARISON, index=False)
    failure.to_csv(OUT_FAILURE, index=False)
    epoch.to_csv(OUT_EPOCH, index=False)
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("# EEG Valence Oracle Diagnostic")
    lines.append("")
    lines.append("This is a deliberately leaky diagnostic. The held-out test subject is used for checkpoint selection.")
    lines.append("")
    lines.append("## Pooled trial-level metrics")
    lines.append("")
    lines.append(table_block(pooled))
    lines.append("")
    lines.append("## Best epoch summary")
    lines.append("")
    lines.append(table_block(pd.DataFrame([payload["best_epoch_summary"]])))
    lines.append("")
    lines.append("## Worst subjects")
    lines.append("")
    keep = [
        "test_subject",
        "failure_score",
        "delta_oracle_minus_stimulus_rmse",
        "delta_oracle_minus_stimulus_macro_f1",
        "delta_oracle_minus_clean_rmse",
        "delta_oracle_minus_clean_macro_f1",
        "oracle_test_checkpoint_rmse",
        "clean_gaussian10_rmse",
        "stimulus_only_oracle_file_rmse",
    ]
    lines.append(table_block(failure[keep], max_rows=20))
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- If oracle beats clean by a lot, checkpoint selection / subject-specific validation is a major bottleneck.")
    lines.append("- If oracle beats stimulus-only, EEG contains usable subject-specific residual signal under leaky selection.")
    lines.append("- This result is not valid as clean cross-subject performance.")
    lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 05s completed.")
    for p in [OUT_MD, OUT_JSON, OUT_POOLED, OUT_SUBJECT, OUT_COMPARISON, OUT_FAILURE, OUT_EPOCH]:
        print(f"wrote: {p}")

    print("\nPooled metrics:")
    print(pooled.to_string(index=False))
    print("\nBest epoch summary:")
    print(pd.DataFrame([payload["best_epoch_summary"]]).to_string(index=False))


if __name__ == "__main__":
    main()
