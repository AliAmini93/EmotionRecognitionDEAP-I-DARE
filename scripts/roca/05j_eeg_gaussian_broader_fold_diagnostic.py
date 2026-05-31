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

PRED_CSV = ROCA_DIR / "eeg_gaussian_broader_smoke_predictions_current.csv"
MAIN_CSV = ROCA_DIR / "eeg_gaussian_broader_smoke_main_metrics_current.csv"
FOLD_CSV = ROCA_DIR / "eeg_gaussian_broader_smoke_fold_summary_current.csv"

OUT_MD = ROCA_DIR / "eeg_gaussian_broader_fold_diagnostic_current.md"
OUT_JSON = ROCA_DIR / "eeg_gaussian_broader_fold_diagnostic_current.json"
OUT_FOLD_METRICS = ROCA_DIR / "eeg_gaussian_broader_fold_diagnostic_metrics_current.csv"
OUT_CONFIG_SUMMARY = ROCA_DIR / "eeg_gaussian_broader_fold_diagnostic_config_summary_current.csv"
OUT_GAUSS10_VS_NONE = ROCA_DIR / "eeg_gaussian_broader_gaussian10_vs_none_current.csv"

TARGET_CONFIG = "gaussian_0p10"
CONTROL_CONFIG = "none"
EEG_MODEL = "eeg_bc_residual_huber_norm_gaussian_broader_smoke"
BASELINE_MODEL = "stimulus_only"


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
    y = y[m]
    p = p[m]
    if len(y) < 2 or np.std(y) == 0 or np.std(p) == 0:
        return None
    return float(np.corrcoef(y, p)[0, 1])


def auroc(y_bin, score):
    y_bin = np.asarray(y_bin, dtype=int)
    score = np.asarray(score, dtype=float)
    m = np.isfinite(score)
    y_bin = y_bin[m]
    score = score[m]

    n_pos = int((y_bin == 1).sum())
    n_neg = int((y_bin == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return None

    ranks = pd.Series(score).rank(method="average").to_numpy()
    rank_sum_pos = float(ranks[y_bin == 1].sum())
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def score_metrics(df: pd.DataFrame) -> dict[str, Any]:
    y = df["y_true_score"].to_numpy(dtype=float)
    p = df["y_pred_score_clipped"].to_numpy(dtype=float)
    err = p - y

    y_bin = (y > 5).astype(int)
    p_bin = (p > 5).astype(int)

    recalls = []
    for cls in [0, 1]:
        support = int((y_bin == cls).sum())
        if support > 0:
            recalls.append(float(((y_bin == cls) & (p_bin == cls)).sum() / support))

    return {
        "n": int(len(df)),
        "mae": safe_float(np.mean(np.abs(err))),
        "rmse": safe_float(np.sqrt(np.mean(err * err))),
        "pearson": pearson(y, p),
        "balanced_accuracy": safe_float(np.mean(recalls)) if recalls else None,
        "auroc": auroc(y_bin, p),
    }


def deviation_metrics(df: pd.DataFrame) -> dict[str, Any]:
    y = df["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
    p = df["y_pred_deviation_clipped"].to_numpy(dtype=float)
    err = p - y

    sign_true = np.sign(y)
    sign_pred = np.sign(p)
    nz = sign_true != 0

    return {
        "dev_mae": safe_float(np.mean(np.abs(err))),
        "dev_rmse": safe_float(np.sqrt(np.mean(err * err))),
        "dev_pearson": pearson(y, p),
        "dev_sign_acc": safe_float(np.mean(sign_true[nz] == sign_pred[nz])) if int(nz.sum()) else None,
        "true_dev_mean": safe_float(np.mean(y)),
        "pred_dev_mean": safe_float(np.mean(p)),
        "true_dev_std": safe_float(np.std(y)),
        "pred_dev_std": safe_float(np.std(p)),
        "std_ratio_pred_over_true": safe_float(np.std(p) / (np.std(y) + 1e-12)),
    }


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
    for path in [PRED_CSV, MAIN_CSV, FOLD_CSV]:
        if not path.exists():
            raise FileNotFoundError(path)


def compute_fold_metrics(pred: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for (cfg, target, model, sid), g in pred.groupby(
        ["augmentation_config", "target", "model", "test_subject"],
        dropna=False,
    ):
        row = {
            "augmentation_config": cfg,
            "target": target,
            "model": model,
            "test_subject": int(sid),
        }
        row.update(score_metrics(g))
        row.update(deviation_metrics(g))
        rows.append(row)

    fold_metrics = pd.DataFrame(rows)

    # Add per-config fold lift versus stimulus_only.
    out_rows = []
    for (cfg, target, sid), g in fold_metrics.groupby(
        ["augmentation_config", "target", "test_subject"],
        dropna=False,
    ):
        baseline = g[g["model"].eq(BASELINE_MODEL)]
        if baseline.empty:
            continue

        baseline = baseline.iloc[0]
        for _, row in g.iterrows():
            d = row.to_dict()
            for metric in [
                "mae",
                "rmse",
                "balanced_accuracy",
                "auroc",
                "dev_mae",
                "dev_rmse",
                "dev_sign_acc",
                "pred_dev_std",
            ]:
                rv = row.get(metric)
                bv = baseline.get(metric)

                if pd.isna(rv) or pd.isna(bv):
                    d[f"lift_vs_stimulus_{metric}"] = None
                elif metric in ["mae", "rmse", "dev_mae", "dev_rmse"]:
                    d[f"lift_vs_stimulus_{metric}"] = safe_float(float(bv) - float(rv))
                else:
                    d[f"lift_vs_stimulus_{metric}"] = safe_float(float(rv) - float(bv))

            out_rows.append(d)

    return pd.DataFrame(out_rows)


def summarize_configs(fold_metrics: pd.DataFrame, main: pd.DataFrame) -> pd.DataFrame:
    rows = []
    eeg = fold_metrics[fold_metrics["model"].eq(EEG_MODEL)].copy()

    for cfg, g in eeg.groupby("augmentation_config"):
        rmse_lift = g["lift_vs_stimulus_rmse"].dropna().to_numpy(dtype=float)
        auroc_lift = g["lift_vs_stimulus_auroc"].dropna().to_numpy(dtype=float)
        ba_lift = g["lift_vs_stimulus_balanced_accuracy"].dropna().to_numpy(dtype=float)
        dev_corr = g["dev_pearson"].dropna().to_numpy(dtype=float)

        main_row = main[
            main["augmentation_config"].eq(cfg)
            & main["model"].eq(EEG_MODEL)
        ].copy()

        main_row_dict = main_row.iloc[0].to_dict() if len(main_row) else {}

        rows.append({
            "augmentation_config": cfg,
            "folds": int(g["test_subject"].nunique()),
            "aggregate_rmse": safe_float(main_row_dict.get("rmse")),
            "aggregate_rmse_lift": safe_float(main_row_dict.get("lift_vs_stimulus_rmse")),
            "aggregate_auroc": safe_float(main_row_dict.get("auroc")),
            "aggregate_auroc_lift": safe_float(main_row_dict.get("lift_vs_stimulus_auroc")),
            "aggregate_balanced_accuracy": safe_float(main_row_dict.get("balanced_accuracy")),
            "aggregate_ba_lift": safe_float(main_row_dict.get("lift_vs_stimulus_balanced_accuracy")),
            "aggregate_dev_pearson": safe_float(main_row_dict.get("dev_pearson")),
            "aggregate_pred_dev_std": safe_float(main_row_dict.get("pred_dev_std")),
            "mean_fold_rmse_lift": safe_float(np.mean(rmse_lift)) if len(rmse_lift) else None,
            "median_fold_rmse_lift": safe_float(np.median(rmse_lift)) if len(rmse_lift) else None,
            "positive_rmse_lift_folds": int(np.sum(rmse_lift > 0)) if len(rmse_lift) else 0,
            "negative_rmse_lift_folds": int(np.sum(rmse_lift < 0)) if len(rmse_lift) else 0,
            "mean_fold_auroc_lift": safe_float(np.mean(auroc_lift)) if len(auroc_lift) else None,
            "positive_auroc_lift_folds": int(np.sum(auroc_lift > 0)) if len(auroc_lift) else 0,
            "mean_fold_ba_lift": safe_float(np.mean(ba_lift)) if len(ba_lift) else None,
            "positive_ba_lift_folds": int(np.sum(ba_lift > 0)) if len(ba_lift) else 0,
            "mean_fold_dev_pearson": safe_float(np.mean(dev_corr)) if len(dev_corr) else None,
            "median_fold_dev_pearson": safe_float(np.median(dev_corr)) if len(dev_corr) else None,
            "positive_dev_pearson_folds": int(np.sum(dev_corr > 0)) if len(dev_corr) else 0,
            "negative_dev_pearson_folds": int(np.sum(dev_corr < 0)) if len(dev_corr) else 0,
            "mean_pred_dev_std": safe_float(np.mean(g["pred_dev_std"].dropna().to_numpy(dtype=float))),
            "mean_true_dev_std": safe_float(np.mean(g["true_dev_std"].dropna().to_numpy(dtype=float))),
        })

    return pd.DataFrame(rows)


def compare_gaussian10_vs_none(fold_metrics: pd.DataFrame) -> pd.DataFrame:
    eeg = fold_metrics[fold_metrics["model"].eq(EEG_MODEL)].copy()

    keep_cols = [
        "augmentation_config",
        "test_subject",
        "rmse",
        "lift_vs_stimulus_rmse",
        "balanced_accuracy",
        "lift_vs_stimulus_balanced_accuracy",
        "auroc",
        "lift_vs_stimulus_auroc",
        "dev_pearson",
        "dev_sign_acc",
        "pred_dev_std",
        "true_dev_std",
    ]

    a = eeg[eeg["augmentation_config"].eq(TARGET_CONFIG)][keep_cols].copy()
    b = eeg[eeg["augmentation_config"].eq(CONTROL_CONFIG)][keep_cols].copy()

    if a.empty or b.empty:
        return pd.DataFrame()

    a = a.rename(columns={c: f"{TARGET_CONFIG}_{c}" for c in keep_cols if c not in ["test_subject"]})
    b = b.rename(columns={c: f"{CONTROL_CONFIG}_{c}" for c in keep_cols if c not in ["test_subject"]})

    merged = a.merge(b, on="test_subject", how="inner")

    merged["delta_rmse_gauss10_minus_none"] = merged[f"{TARGET_CONFIG}_rmse"] - merged[f"{CONTROL_CONFIG}_rmse"]
    merged["delta_rmse_lift_gauss10_minus_none"] = (
        merged[f"{TARGET_CONFIG}_lift_vs_stimulus_rmse"]
        - merged[f"{CONTROL_CONFIG}_lift_vs_stimulus_rmse"]
    )
    merged["delta_auroc_gauss10_minus_none"] = merged[f"{TARGET_CONFIG}_auroc"] - merged[f"{CONTROL_CONFIG}_auroc"]
    merged["delta_ba_gauss10_minus_none"] = (
        merged[f"{TARGET_CONFIG}_balanced_accuracy"] - merged[f"{CONTROL_CONFIG}_balanced_accuracy"]
    )
    merged["delta_dev_pearson_gauss10_minus_none"] = (
        merged[f"{TARGET_CONFIG}_dev_pearson"] - merged[f"{CONTROL_CONFIG}_dev_pearson"]
    )
    merged["gauss10_better_rmse_than_none"] = merged["delta_rmse_gauss10_minus_none"] < 0
    merged["gauss10_better_rmse_than_stimulus"] = merged[f"{TARGET_CONFIG}_lift_vs_stimulus_rmse"] > 0
    merged["gauss10_positive_dev_pearson"] = merged[f"{TARGET_CONFIG}_dev_pearson"] > 0

    return merged


def choose_verdict(config_summary: pd.DataFrame) -> dict[str, Any]:
    g = config_summary[config_summary["augmentation_config"].eq(TARGET_CONFIG)].copy()
    if g.empty:
        return {
            "verdict": "missing_target_config",
            "reason": f"{TARGET_CONFIG} was not found.",
        }

    row = g.iloc[0].to_dict()
    rmse_lift = row.get("aggregate_rmse_lift")
    auroc_lift = row.get("aggregate_auroc_lift")
    ba_lift = row.get("aggregate_ba_lift")
    dev_pearson = row.get("aggregate_dev_pearson")
    pos_rmse = row.get("positive_rmse_lift_folds")
    folds = row.get("folds")

    if rmse_lift is not None and rmse_lift > 0.02 and dev_pearson is not None and dev_pearson > 0.10:
        verdict = "strong_candidate_for_full_loso"
        reason = "Gaussian 0.10 improves aggregate RMSE and has positive residual correlation."
    elif abs(float(rmse_lift or 0.0)) <= 0.02 and auroc_lift is not None and auroc_lift > 0 and dev_pearson is not None and dev_pearson > 0.05:
        verdict = "borderline_candidate_for_full_loso"
        reason = "Gaussian 0.10 is near-tied on RMSE but improves AUROC/BA and residual correlation."
    elif pos_rmse is not None and folds is not None and int(pos_rmse) >= max(1, int(folds) // 2):
        verdict = "fold_mixed_candidate"
        reason = "Gaussian 0.10 helps many folds but aggregate evidence is not clearly positive."
    else:
        verdict = "not_ready_for_full_loso"
        reason = "Gaussian 0.10 does not show enough fold-level or aggregate evidence."

    return {
        "verdict": verdict,
        "reason": reason,
        "gaussian_0p10_summary": row,
    }


def write_outputs(
    pred: pd.DataFrame,
    main: pd.DataFrame,
    fold_metrics: pd.DataFrame,
    config_summary: pd.DataFrame,
    gauss10_vs_none: pd.DataFrame,
    verdict: dict[str, Any],
):
    fold_metrics.to_csv(OUT_FOLD_METRICS, index=False)
    config_summary.to_csv(OUT_CONFIG_SUMMARY, index=False)
    gauss10_vs_none.to_csv(OUT_GAUSS10_VS_NONE, index=False)

    config_cols = [
        "augmentation_config",
        "folds",
        "aggregate_rmse",
        "aggregate_rmse_lift",
        "aggregate_auroc",
        "aggregate_auroc_lift",
        "aggregate_balanced_accuracy",
        "aggregate_ba_lift",
        "aggregate_dev_pearson",
        "positive_rmse_lift_folds",
        "negative_rmse_lift_folds",
        "positive_auroc_lift_folds",
        "positive_ba_lift_folds",
        "positive_dev_pearson_folds",
        "negative_dev_pearson_folds",
        "aggregate_pred_dev_std",
        "mean_fold_dev_pearson",
    ]

    compare_cols = [
        "test_subject",
        "gaussian_0p10_rmse",
        "none_rmse",
        "delta_rmse_gauss10_minus_none",
        "gaussian_0p10_lift_vs_stimulus_rmse",
        "gauss10_better_rmse_than_stimulus",
        "gauss10_better_rmse_than_none",
        "gaussian_0p10_auroc",
        "none_auroc",
        "delta_auroc_gauss10_minus_none",
        "gaussian_0p10_dev_pearson",
        "none_dev_pearson",
        "delta_dev_pearson_gauss10_minus_none",
        "gauss10_positive_dev_pearson",
    ]

    # Worst and best fold lists for gaussian_0p10.
    g10_folds = fold_metrics[
        fold_metrics["augmentation_config"].eq(TARGET_CONFIG)
        & fold_metrics["model"].eq(EEG_MODEL)
    ].copy()

    worst_by_rmse_lift = g10_folds.sort_values("lift_vs_stimulus_rmse", ascending=True).head(8)
    best_by_rmse_lift = g10_folds.sort_values("lift_vs_stimulus_rmse", ascending=False).head(8)
    worst_by_dev_corr = g10_folds.sort_values("dev_pearson", ascending=True).head(8)
    best_by_dev_corr = g10_folds.sort_values("dev_pearson", ascending=False).head(8)

    fold_rank_cols = [
        "test_subject",
        "rmse",
        "lift_vs_stimulus_rmse",
        "auroc",
        "lift_vs_stimulus_auroc",
        "balanced_accuracy",
        "lift_vs_stimulus_balanced_accuracy",
        "dev_pearson",
        "dev_sign_acc",
        "pred_dev_std",
        "true_dev_std",
    ]

    lines = []
    lines.append("# ROCA-I-DARE EEG Gaussian Broader Fold Diagnostic\n")
    lines.append("No model training was performed in this step. This report analyzes the 20-fold Gaussian broader smoke outputs.\n")

    lines.append("## Decision verdict\n")
    lines.append(f"- verdict: `{verdict['verdict']}`")
    lines.append(f"- reason: {verdict['reason']}")
    lines.append("")

    lines.append("## Config-level fold summary\n")
    lines.append(md_table(config_summary.to_dict(orient="records"), config_cols))

    lines.append("\n## Gaussian 0.10 vs no augmentation by fold\n")
    if gauss10_vs_none.empty:
        lines.append("_No comparison rows._\n")
    else:
        lines.append(md_table(gauss10_vs_none.to_dict(orient="records"), compare_cols))

    lines.append("\n## Gaussian 0.10 best folds by RMSE lift\n")
    lines.append(md_table(best_by_rmse_lift.to_dict(orient="records"), fold_rank_cols))

    lines.append("\n## Gaussian 0.10 worst folds by RMSE lift\n")
    lines.append(md_table(worst_by_rmse_lift.to_dict(orient="records"), fold_rank_cols))

    lines.append("\n## Gaussian 0.10 best folds by dev_pearson\n")
    lines.append(md_table(best_by_dev_corr.to_dict(orient="records"), fold_rank_cols))

    lines.append("\n## Gaussian 0.10 worst folds by dev_pearson\n")
    lines.append(md_table(worst_by_dev_corr.to_dict(orient="records"), fold_rank_cols))

    lines.append("\n## Interpretation guide\n")
    lines.append(
        "- `aggregate_rmse_lift > 0` means the EEG model beats stimulus-only on pooled RMSE.\n"
        "- `positive_rmse_lift_folds` counts subjects where EEG beats stimulus-only on RMSE.\n"
        "- `gauss10_better_rmse_than_none` checks whether Gaussian 0.10 improves over no augmentation for the same subject.\n"
        "- If Gaussian 0.10 is near-tied on RMSE but improves AUROC/BA/dev_pearson, it is a borderline but real candidate.\n"
        "- Any full LOSO after this point should use Gaussian 0.10 as a locked candidate, not continue tuning noise levels on the same folds.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "protocol": "EEG Gaussian broader fold diagnostic",
        "inputs": {
            "pred_csv": str(PRED_CSV),
            "main_csv": str(MAIN_CSV),
            "fold_csv": str(FOLD_CSV),
        },
        "target_config": TARGET_CONFIG,
        "control_config": CONTROL_CONFIG,
        "eeg_model": EEG_MODEL,
        "baseline_model": BASELINE_MODEL,
        "verdict": verdict,
        "config_summary": config_summary.to_dict(orient="records"),
        "gaussian_0p10_vs_none": gauss10_vs_none.to_dict(orient="records"),
        "gaussian_0p10_best_rmse_lift": best_by_rmse_lift.to_dict(orient="records"),
        "gaussian_0p10_worst_rmse_lift": worst_by_rmse_lift.to_dict(orient="records"),
        "gaussian_0p10_best_dev_pearson": best_by_dev_corr.to_dict(orient="records"),
        "gaussian_0p10_worst_dev_pearson": worst_by_dev_corr.to_dict(orient="records"),
        "notes": [
            "This diagnostic performs no training.",
            "It analyzes the 20-fold broader Gaussian smoke.",
            "The main question is whether Gaussian 0.10 is stable enough to justify full LOSO.",
            "Full LOSO should lock Gaussian 0.10 and avoid further tuning on the same folds.",
        ],
    }
    OUT_JSON.write_text(json.dumps(clean_json(summary), indent=2, ensure_ascii=False), encoding="utf-8")

    print("ROCA step 05j completed.")
    print(f"wrote: {OUT_MD}")
    print(f"wrote: {OUT_JSON}")
    print(f"wrote: {OUT_FOLD_METRICS}")
    print(f"wrote: {OUT_CONFIG_SUMMARY}")
    print(f"wrote: {OUT_GAUSS10_VS_NONE}")
    print()
    print("Decision verdict:")
    print(json.dumps(clean_json(verdict), indent=2, ensure_ascii=False))
    print()
    print("Config summary:")
    print(config_summary[config_cols].to_string(index=False))
    print()
    print("Gaussian 0.10 vs none:")
    if gauss10_vs_none.empty:
        print("No rows.")
    else:
        print(gauss10_vs_none[compare_cols].to_string(index=False))


def main():
    require_inputs()

    pred = pd.read_csv(PRED_CSV)
    main_metrics = pd.read_csv(MAIN_CSV)

    pred["test_subject"] = pred["test_subject"].astype(int)
    pred["augmentation_config"] = pred["augmentation_config"].astype(str)
    pred["model"] = pred["model"].astype(str)

    fold_metrics = compute_fold_metrics(pred)
    config_summary = summarize_configs(fold_metrics, main_metrics)
    gauss10_vs_none = compare_gaussian10_vs_none(fold_metrics)
    verdict = choose_verdict(config_summary)

    write_outputs(
        pred=pred,
        main=main_metrics,
        fold_metrics=fold_metrics,
        config_summary=config_summary,
        gauss10_vs_none=gauss10_vs_none,
        verdict=verdict,
    )


if __name__ == "__main__":
    main()
