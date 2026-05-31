#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROCA_DIR = ROOT / "docs" / "roca"

EXPERIMENTS = [
    {
        "experiment": "05b_residual_smoke",
        "description": "Baseline EEG residual smoke: Huber residual, no target normalization",
        "pred": ROCA_DIR / "eeg_residual_training_smoke_predictions_current.csv",
        "main": ROCA_DIR / "eeg_residual_training_smoke_main_metrics_current.csv",
        "fold": ROCA_DIR / "eeg_residual_training_smoke_fold_summary_current.csv",
    },
    {
        "experiment": "05c_stabilized_residual_smoke",
        "description": "Stabilized EEG residual smoke: target-normalized residual, lower LR, early stopping",
        "pred": ROCA_DIR / "eeg_residual_training_stabilized_smoke_predictions_current.csv",
        "main": ROCA_DIR / "eeg_residual_training_stabilized_smoke_main_metrics_current.csv",
        "fold": ROCA_DIR / "eeg_residual_training_stabilized_smoke_fold_summary_current.csv",
    },
    {
        "experiment": "05d_multitask_highlow_smoke",
        "description": "Multitask EEG smoke: residual regression plus auxiliary raw high/low BCE",
        "pred": ROCA_DIR / "eeg_multitask_residual_training_smoke_predictions_current.csv",
        "main": ROCA_DIR / "eeg_multitask_residual_training_smoke_main_metrics_current.csv",
        "fold": ROCA_DIR / "eeg_multitask_residual_training_smoke_fold_summary_current.csv",
    },
]

OUT_MD = ROCA_DIR / "eeg_smoke_diagnostic_current.md"
OUT_JSON = ROCA_DIR / "eeg_smoke_diagnostic_current.json"
OUT_EXPERIMENT_SUMMARY = ROCA_DIR / "eeg_smoke_diagnostic_experiment_summary_current.csv"
OUT_FOLD_DIAGNOSTIC = ROCA_DIR / "eeg_smoke_diagnostic_fold_current.csv"
OUT_MODEL_COMPARISON = ROCA_DIR / "eeg_smoke_diagnostic_model_comparison_current.csv"


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
        return None if not math.isfinite(v) else v
    if isinstance(x, float):
        return None if not math.isfinite(x) else x
    return x


def pearson(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y, p = y[m], p[m]
    if len(y) < 2 or np.std(y) == 0 or np.std(p) == 0:
        return None
    return float(np.corrcoef(y, p)[0, 1])


def rmse(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    if not m.any():
        return None
    e = p[m] - y[m]
    return float(np.sqrt(np.mean(e * e)))


def mae(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    if not m.any():
        return None
    return float(np.mean(np.abs(p[m] - y[m])))


def auroc(y_bin, score):
    y_bin = np.asarray(y_bin, dtype=int)
    score = np.asarray(score, dtype=float)
    m = np.isfinite(score)
    y_bin, score = y_bin[m], score[m]

    n_pos = int((y_bin == 1).sum())
    n_neg = int((y_bin == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return None

    ranks = pd.Series(score).rank(method="average").to_numpy()
    rank_sum_pos = float(ranks[y_bin == 1].sum())
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def balanced_accuracy(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y = y[m]
    p = p[m]
    if len(y) == 0:
        return None

    y_bin = (y > 5).astype(int)
    p_bin = (p > 5).astype(int)

    recalls = []
    for cls in [0, 1]:
        support = int((y_bin == cls).sum())
        if support > 0:
            recalls.append(float(((y_bin == cls) & (p_bin == cls)).sum() / support))

    if not recalls:
        return None
    return float(np.mean(recalls))


def md_table(rows, cols):
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


def require_columns(df: pd.DataFrame, cols: list[str], label: str):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"{label} missing columns: {missing}")


def load_experiment(spec: dict[str, Any]):
    for key in ["pred", "main", "fold"]:
        if not spec[key].exists():
            raise FileNotFoundError(spec[key])

    pred = pd.read_csv(spec["pred"])
    main = pd.read_csv(spec["main"])
    fold = pd.read_csv(spec["fold"])

    require_columns(
        pred,
        [
            "test_subject",
            "target",
            "model",
            "y_true_score",
            "y_pred_score_clipped",
            "true_deviation_from_train_stimulus_mean",
            "y_pred_deviation_clipped",
        ],
        f"{spec['experiment']} predictions",
    )

    pred["experiment"] = spec["experiment"]
    pred["experiment_description"] = spec["description"]

    main["experiment"] = spec["experiment"]
    main["experiment_description"] = spec["description"]

    fold["experiment"] = spec["experiment"]
    fold["experiment_description"] = spec["description"]

    pred["test_subject"] = pred["test_subject"].astype(int)

    return pred, main, fold


def subject_centered_corr(df: pd.DataFrame):
    sub = df.copy()
    sub["true_dev_centered"] = sub["true_deviation_from_train_stimulus_mean"] - sub.groupby("test_subject")[
        "true_deviation_from_train_stimulus_mean"
    ].transform("mean")
    sub["pred_dev_centered"] = sub["y_pred_deviation_clipped"] - sub.groupby("test_subject")[
        "y_pred_deviation_clipped"
    ].transform("mean")
    return pearson(sub["true_dev_centered"], sub["pred_dev_centered"])


def fold_level_diagnostics(pred: pd.DataFrame):
    rows = []

    eeg_models = sorted([m for m in pred["model"].unique().tolist() if m != "stimulus_only"])

    for experiment in sorted(pred["experiment"].unique()):
        exp = pred[pred["experiment"].eq(experiment)].copy()
        for target in sorted(exp["target"].unique()):
            target_df = exp[exp["target"].eq(target)].copy()

            stim = target_df[target_df["model"].eq("stimulus_only")].copy()
            stim_by_subject = {
                int(sid): g.copy()
                for sid, g in stim.groupby("test_subject")
            }

            for model in eeg_models:
                model_df = target_df[target_df["model"].eq(model)].copy()
                if model_df.empty:
                    continue

                for sid, g in model_df.groupby("test_subject"):
                    sid = int(sid)
                    stim_g = stim_by_subject.get(sid)

                    true_dev = g["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
                    pred_dev = g["y_pred_deviation_clipped"].to_numpy(dtype=float)
                    y = g["y_true_score"].to_numpy(dtype=float)
                    p = g["y_pred_score_clipped"].to_numpy(dtype=float)

                    row = {
                        "experiment": experiment,
                        "target": target,
                        "model": model,
                        "test_subject": sid,
                        "n": int(len(g)),
                        "rmse": rmse(y, p),
                        "mae": mae(y, p),
                        "dev_rmse": rmse(true_dev, pred_dev),
                        "dev_mae": mae(true_dev, pred_dev),
                        "dev_pearson": pearson(true_dev, pred_dev),
                        "score_pearson": pearson(y, p),
                        "balanced_accuracy": balanced_accuracy(y, p),
                        "auroc": auroc((y > 5).astype(int), p),
                        "true_dev_mean": safe_float(np.mean(true_dev)),
                        "pred_dev_mean": safe_float(np.mean(pred_dev)),
                        "dev_mean_bias_pred_minus_true": safe_float(np.mean(pred_dev) - np.mean(true_dev)),
                        "true_dev_std": safe_float(np.std(true_dev)),
                        "pred_dev_std": safe_float(np.std(pred_dev)),
                        "std_ratio_pred_over_true": safe_float(np.std(pred_dev) / (np.std(true_dev) + 1e-12)),
                    }

                    if stim_g is not None and len(stim_g):
                        sy = stim_g["y_true_score"].to_numpy(dtype=float)
                        sp = stim_g["y_pred_score_clipped"].to_numpy(dtype=float)
                        sdev_true = stim_g["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
                        sdev_pred = stim_g["y_pred_deviation_clipped"].to_numpy(dtype=float)

                        row["stimulus_rmse"] = rmse(sy, sp)
                        row["stimulus_dev_rmse"] = rmse(sdev_true, sdev_pred)
                        row["lift_vs_stimulus_rmse"] = safe_float(row["stimulus_rmse"] - row["rmse"])
                        row["lift_vs_stimulus_dev_rmse"] = safe_float(row["stimulus_dev_rmse"] - row["dev_rmse"])
                    else:
                        row["stimulus_rmse"] = None
                        row["stimulus_dev_rmse"] = None
                        row["lift_vs_stimulus_rmse"] = None
                        row["lift_vs_stimulus_dev_rmse"] = None

                    rows.append(row)

    return pd.DataFrame(rows)


def aggregate_model_comparison(pred: pd.DataFrame, fold_diag: pd.DataFrame):
    rows = []

    eeg_models = sorted([m for m in pred["model"].unique().tolist() if m != "stimulus_only"])

    for experiment in sorted(pred["experiment"].unique()):
        exp = pred[pred["experiment"].eq(experiment)].copy()
        for target in sorted(exp["target"].unique()):
            target_df = exp[exp["target"].eq(target)].copy()

            stim = target_df[target_df["model"].eq("stimulus_only")].copy()
            stim_rmse = rmse(stim["y_true_score"], stim["y_pred_score_clipped"])
            stim_auroc = auroc(
                (stim["y_true_score"].to_numpy(dtype=float) > 5).astype(int),
                stim["y_pred_score_clipped"].to_numpy(dtype=float),
            )
            stim_ba = balanced_accuracy(stim["y_true_score"], stim["y_pred_score_clipped"])

            for model in eeg_models:
                g = target_df[target_df["model"].eq(model)].copy()
                if g.empty:
                    continue

                true_dev = g["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
                pred_dev = g["y_pred_deviation_clipped"].to_numpy(dtype=float)
                y = g["y_true_score"].to_numpy(dtype=float)
                p = g["y_pred_score_clipped"].to_numpy(dtype=float)

                fd = fold_diag[
                    fold_diag["experiment"].eq(experiment)
                    & fold_diag["target"].eq(target)
                    & fold_diag["model"].eq(model)
                ].copy()

                dev_corrs = fd["dev_pearson"].dropna().to_numpy(dtype=float)
                rmse_lifts = fd["lift_vs_stimulus_rmse"].dropna().to_numpy(dtype=float)

                row = {
                    "experiment": experiment,
                    "target": target,
                    "model": model,
                    "n": int(len(g)),
                    "aggregate_rmse": rmse(y, p),
                    "stimulus_rmse": stim_rmse,
                    "aggregate_lift_vs_stimulus_rmse": safe_float(stim_rmse - rmse(y, p)),
                    "aggregate_auroc": auroc((y > 5).astype(int), p),
                    "stimulus_auroc": stim_auroc,
                    "aggregate_lift_vs_stimulus_auroc": safe_float(auroc((y > 5).astype(int), p) - stim_auroc)
                    if stim_auroc is not None and auroc((y > 5).astype(int), p) is not None else None,
                    "aggregate_balanced_accuracy": balanced_accuracy(y, p),
                    "stimulus_balanced_accuracy": stim_ba,
                    "aggregate_dev_pearson": pearson(true_dev, pred_dev),
                    "subject_centered_dev_pearson": subject_centered_corr(g),
                    "macro_mean_fold_dev_pearson": safe_float(np.mean(dev_corrs)) if len(dev_corrs) else None,
                    "macro_median_fold_dev_pearson": safe_float(np.median(dev_corrs)) if len(dev_corrs) else None,
                    "positive_fold_dev_pearson_count": int(np.sum(dev_corrs > 0)) if len(dev_corrs) else 0,
                    "negative_fold_dev_pearson_count": int(np.sum(dev_corrs < 0)) if len(dev_corrs) else 0,
                    "mean_fold_rmse_lift": safe_float(np.mean(rmse_lifts)) if len(rmse_lifts) else None,
                    "positive_fold_rmse_lift_count": int(np.sum(rmse_lifts > 0)) if len(rmse_lifts) else 0,
                    "negative_fold_rmse_lift_count": int(np.sum(rmse_lifts < 0)) if len(rmse_lifts) else 0,
                    "true_dev_std": safe_float(np.std(true_dev)),
                    "pred_dev_std": safe_float(np.std(pred_dev)),
                    "std_ratio_pred_over_true": safe_float(np.std(pred_dev) / (np.std(true_dev) + 1e-12)),
                    "true_dev_mean": safe_float(np.mean(true_dev)),
                    "pred_dev_mean": safe_float(np.mean(pred_dev)),
                    "mean_bias_pred_minus_true": safe_float(np.mean(pred_dev) - np.mean(true_dev)),
                }
                rows.append(row)

    return pd.DataFrame(rows)


def choose_verdict(row: dict[str, Any]):
    rmse_lift = row.get("aggregate_lift_vs_stimulus_rmse")
    agg_dev = row.get("aggregate_dev_pearson")
    centered_dev = row.get("subject_centered_dev_pearson")
    macro_dev = row.get("macro_mean_fold_dev_pearson")
    std_ratio = row.get("std_ratio_pred_over_true")

    rmse_ok = rmse_lift is not None and rmse_lift > 0
    agg_ok = agg_dev is not None and agg_dev >= 0.10
    centered_ok = centered_dev is not None and centered_dev >= 0.10
    macro_ok = macro_dev is not None and macro_dev >= 0.10
    scale_bad = std_ratio is not None and std_ratio < 0.25

    if rmse_ok and agg_ok:
        return "promising"
    if centered_ok and macro_ok and not rmse_ok:
        return "ranking_signal_but_calibration_problem"
    if centered_ok or macro_ok:
        return "weak_within_subject_signal"
    if scale_bad:
        return "collapsed_or_under_scaled"
    return "not_promising"


def experiment_summary(model_cmp: pd.DataFrame):
    rows = []
    for _, row in model_cmp.iterrows():
        d = row.to_dict()
        d["diagnostic_verdict"] = choose_verdict(d)
        rows.append(d)
    return pd.DataFrame(rows)


def write_outputs(pred: pd.DataFrame, fold_diag: pd.DataFrame, model_cmp: pd.DataFrame, exp_summary: pd.DataFrame, missing: list[str]):
    fold_diag.to_csv(OUT_FOLD_DIAGNOSTIC, index=False)
    model_cmp.to_csv(OUT_MODEL_COMPARISON, index=False)
    exp_summary.to_csv(OUT_EXPERIMENT_SUMMARY, index=False)

    summary = {
        "protocol": "EEG smoke diagnostic report",
        "inputs": [
            {
                "experiment": e["experiment"],
                "description": e["description"],
                "pred": str(e["pred"]),
                "main": str(e["main"]),
                "fold": str(e["fold"]),
            }
            for e in EXPERIMENTS
        ],
        "missing_inputs": missing,
        "experiment_summary": exp_summary.to_dict(orient="records"),
        "fold_diagnostics": fold_diag.to_dict(orient="records"),
        "notes": [
            "No model was trained in this diagnostic step.",
            "Aggregate dev_pearson can disagree with mean fold dev_pearson if calibration differs by subject.",
            "subject_centered_dev_pearson removes per-subject mean bias before correlation.",
            "std_ratio_pred_over_true below 0.25 indicates severely under-scaled residual predictions.",
            "This report is intended to choose the next EEG training formulation.",
        ],
    }

    OUT_JSON.write_text(json.dumps(clean_json(summary), indent=2, ensure_ascii=False), encoding="utf-8")

    key_cols = [
        "experiment",
        "target",
        "model",
        "aggregate_rmse",
        "stimulus_rmse",
        "aggregate_lift_vs_stimulus_rmse",
        "aggregate_dev_pearson",
        "subject_centered_dev_pearson",
        "macro_mean_fold_dev_pearson",
        "positive_fold_dev_pearson_count",
        "negative_fold_dev_pearson_count",
        "pred_dev_std",
        "true_dev_std",
        "std_ratio_pred_over_true",
        "diagnostic_verdict",
    ]

    fold_cols = [
        "experiment",
        "test_subject",
        "model",
        "rmse",
        "stimulus_rmse",
        "lift_vs_stimulus_rmse",
        "dev_pearson",
        "true_dev_mean",
        "pred_dev_mean",
        "dev_mean_bias_pred_minus_true",
        "true_dev_std",
        "pred_dev_std",
        "std_ratio_pred_over_true",
    ]

    lines = []
    lines.append("# ROCA-I-DARE EEG Smoke Diagnostic Report\n")
    lines.append("No model training was performed in this step.\n")

    lines.append("## Experiment-level summary\n")
    lines.append(md_table(exp_summary.to_dict(orient="records"), key_cols))

    lines.append("\n## Fold-level diagnostics\n")
    lines.append(md_table(fold_diag.to_dict(orient="records"), fold_cols))

    lines.append("\n## Interpretation\n")
    lines.append(
        "- `aggregate_dev_pearson` is computed after pooling all smoke subjects.\n"
        "- `macro_mean_fold_dev_pearson` averages per-subject correlations.\n"
        "- `subject_centered_dev_pearson` removes subject-level mean bias before correlation.\n"
        "- If macro/centered correlations are positive while aggregate correlation is poor, the model has a calibration problem rather than no signal.\n"
        "- If `std_ratio_pred_over_true` is very small, residual predictions are under-scaled.\n"
    )

    lines.append("\n## Suggested next decision rule\n")
    lines.append(
        "- If the best experiment is `collapsed_or_under_scaled`, adjust model/head/loss before full LOSO.\n"
        "- If the best experiment is `weak_within_subject_signal`, try residual-sign auxiliary instead of raw high/low auxiliary.\n"
        "- If the best experiment is `ranking_signal_but_calibration_problem`, test fold-safe calibration of predicted residual scale.\n"
        "- Only run full LOSO when RMSE lift or robust residual correlation is at least directionally promising.\n"
    )

    lines.append("\n## Missing inputs\n")
    if missing:
        for m in missing:
            lines.append(f"- `{m}`")
    else:
        lines.append("- None.")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 05e completed.")
    print(f"wrote: {OUT_MD}")
    print(f"wrote: {OUT_JSON}")
    print(f"wrote: {OUT_EXPERIMENT_SUMMARY}")
    print(f"wrote: {OUT_FOLD_DIAGNOSTIC}")
    print(f"wrote: {OUT_MODEL_COMPARISON}")
    print()
    print("Experiment summary:")
    print(exp_summary[key_cols].to_string(index=False))


def main():
    ROCA_DIR.mkdir(parents=True, exist_ok=True)

    pred_frames = []
    main_frames = []
    fold_frames = []
    missing = []

    for spec in EXPERIMENTS:
        try:
            pred, main, fold = load_experiment(spec)
            pred_frames.append(pred)
            main_frames.append(main)
            fold_frames.append(fold)
        except FileNotFoundError as exc:
            missing.append(str(exc))

    if not pred_frames:
        raise FileNotFoundError("No EEG smoke prediction files were found.")

    pred_all = pd.concat(pred_frames, ignore_index=True, sort=False)

    fold_diag = fold_level_diagnostics(pred_all)
    model_cmp = aggregate_model_comparison(pred_all, fold_diag)
    exp_summary = experiment_summary(model_cmp)

    write_outputs(pred_all, fold_diag, model_cmp, exp_summary, missing)


if __name__ == "__main__":
    main()
