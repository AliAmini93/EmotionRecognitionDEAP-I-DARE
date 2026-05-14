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

PRED_CSV = ROCA_DIR / "eeg_gaussian10_full_loso_predictions_current.csv"
MAIN_CSV = ROCA_DIR / "eeg_gaussian10_full_loso_main_metrics_current.csv"
SUBSET_CSV = ROCA_DIR / "eeg_gaussian10_full_loso_subset_metrics_current.csv"
FOLD_CSV = ROCA_DIR / "eeg_gaussian10_full_loso_fold_summary_current.csv"

OUT_MD = ROCA_DIR / "eeg_gaussian10_full_loso_diagnostic_current.md"
OUT_JSON = ROCA_DIR / "eeg_gaussian10_full_loso_diagnostic_current.json"
OUT_FOLD_METRICS = ROCA_DIR / "eeg_gaussian10_full_loso_diagnostic_fold_metrics_current.csv"
OUT_SUBJECT_COMPARISON = ROCA_DIR / "eeg_gaussian10_full_loso_diagnostic_subject_comparison_current.csv"
OUT_SUBSET_DIAGNOSTIC = ROCA_DIR / "eeg_gaussian10_full_loso_diagnostic_subset_current.csv"
OUT_FAILURE_RANKING = ROCA_DIR / "eeg_gaussian10_full_loso_diagnostic_failure_ranking_current.csv"

TARGET_CONFIG = "gaussian_0p10"
EEG_MODEL = "eeg_bc_residual_huber_norm_gaussian10_full_loso"
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
        "mean_abs_true_dev": safe_float(np.mean(np.abs(y))),
        "mean_abs_pred_dev": safe_float(np.mean(np.abs(p))),
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
    for path in [PRED_CSV, MAIN_CSV, SUBSET_CSV, FOLD_CSV]:
        if not path.exists():
            raise FileNotFoundError(path)


def compute_fold_metrics(pred: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for (cfg, target, model, sid), g in pred.groupby(
        ["augmentation_config", "target", "model", "test_subject"],
        dropna=False,
    ):
        row = {
            "augmentation_config": str(cfg),
            "target": str(target),
            "model": str(model),
            "test_subject": int(sid),
        }
        row.update(score_metrics(g))
        row.update(deviation_metrics(g))
        rows.append(row)

    fold_metrics = pd.DataFrame(rows)

    # Add per-subject lift versus stimulus_only.
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
                "pearson",
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


def make_subject_comparison(fold_metrics: pd.DataFrame) -> pd.DataFrame:
    eeg = fold_metrics[fold_metrics["model"].eq(EEG_MODEL)].copy()
    base = fold_metrics[fold_metrics["model"].eq(BASELINE_MODEL)].copy()

    eeg_cols = [
        "test_subject",
        "rmse",
        "mae",
        "balanced_accuracy",
        "auroc",
        "dev_rmse",
        "dev_pearson",
        "dev_sign_acc",
        "true_dev_std",
        "pred_dev_std",
        "std_ratio_pred_over_true",
        "mean_abs_true_dev",
        "mean_abs_pred_dev",
        "lift_vs_stimulus_rmse",
        "lift_vs_stimulus_mae",
        "lift_vs_stimulus_balanced_accuracy",
        "lift_vs_stimulus_auroc",
        "lift_vs_stimulus_dev_rmse",
    ]
    base_cols = ["test_subject", "rmse", "mae", "balanced_accuracy", "auroc"]

    eeg = eeg[eeg_cols].rename(columns={c: f"eeg_{c}" for c in eeg_cols if c != "test_subject"})
    base = base[base_cols].rename(columns={c: f"stimulus_{c}" for c in base_cols if c != "test_subject"})

    out = eeg.merge(base, on="test_subject", how="left")

    out["eeg_better_rmse_than_stimulus"] = out["eeg_lift_vs_stimulus_rmse"] > 0
    out["eeg_better_mae_than_stimulus"] = out["eeg_lift_vs_stimulus_mae"] > 0
    out["eeg_better_auroc_than_stimulus"] = out["eeg_lift_vs_stimulus_auroc"] > 0
    out["eeg_better_ba_than_stimulus"] = out["eeg_lift_vs_stimulus_balanced_accuracy"] > 0
    out["eeg_positive_dev_pearson"] = out["eeg_dev_pearson"] > 0

    # A simple failure severity score: worse RMSE plus negative residual correlation.
    out["failure_score"] = (
        -out["eeg_lift_vs_stimulus_rmse"].fillna(0.0)
        + np.maximum(0.0, -out["eeg_dev_pearson"].fillna(0.0))
    )

    return out.sort_values("test_subject").reset_index(drop=True)


def summarize_subjects(subject_cmp: pd.DataFrame, main_metrics: pd.DataFrame) -> dict[str, Any]:
    n = int(len(subject_cmp))

    main_eeg = main_metrics[
        main_metrics["model"].astype(str).eq(EEG_MODEL)
    ].copy()
    main_stim = main_metrics[
        main_metrics["model"].astype(str).eq(BASELINE_MODEL)
    ].copy()

    main_eeg_row = main_eeg.iloc[0].to_dict() if len(main_eeg) else {}
    main_stim_row = main_stim.iloc[0].to_dict() if len(main_stim) else {}

    def count_true(col):
        return int(subject_cmp[col].fillna(False).astype(bool).sum())

    rmse_lift = subject_cmp["eeg_lift_vs_stimulus_rmse"].dropna().to_numpy(dtype=float)
    dev_corr = subject_cmp["eeg_dev_pearson"].dropna().to_numpy(dtype=float)
    pred_std = subject_cmp["eeg_pred_dev_std"].dropna().to_numpy(dtype=float)
    true_std = subject_cmp["eeg_true_dev_std"].dropna().to_numpy(dtype=float)

    return {
        "subjects": n,
        "aggregate": {
            "eeg_rmse": safe_float(main_eeg_row.get("rmse")),
            "stimulus_rmse": safe_float(main_stim_row.get("rmse")),
            "eeg_lift_vs_stimulus_rmse": safe_float(main_eeg_row.get("lift_vs_stimulus_rmse")),
            "eeg_mae": safe_float(main_eeg_row.get("mae")),
            "stimulus_mae": safe_float(main_stim_row.get("mae")),
            "eeg_auroc": safe_float(main_eeg_row.get("auroc")),
            "stimulus_auroc": safe_float(main_stim_row.get("auroc")),
            "eeg_lift_vs_stimulus_auroc": safe_float(main_eeg_row.get("lift_vs_stimulus_auroc")),
            "eeg_balanced_accuracy": safe_float(main_eeg_row.get("balanced_accuracy")),
            "stimulus_balanced_accuracy": safe_float(main_stim_row.get("balanced_accuracy")),
            "eeg_lift_vs_stimulus_balanced_accuracy": safe_float(main_eeg_row.get("lift_vs_stimulus_balanced_accuracy")),
            "eeg_dev_pearson": safe_float(main_eeg_row.get("dev_pearson")),
            "eeg_pred_dev_std": safe_float(main_eeg_row.get("pred_dev_std")),
            "true_dev_std": safe_float(main_eeg_row.get("true_dev_std")),
        },
        "fold_counts": {
            "rmse_better_than_stimulus": count_true("eeg_better_rmse_than_stimulus"),
            "rmse_worse_than_stimulus": n - count_true("eeg_better_rmse_than_stimulus"),
            "mae_better_than_stimulus": count_true("eeg_better_mae_than_stimulus"),
            "auroc_better_than_stimulus": count_true("eeg_better_auroc_than_stimulus"),
            "ba_better_than_stimulus": count_true("eeg_better_ba_than_stimulus"),
            "positive_dev_pearson": count_true("eeg_positive_dev_pearson"),
            "negative_dev_pearson": n - count_true("eeg_positive_dev_pearson"),
        },
        "fold_distribution": {
            "mean_rmse_lift": safe_float(np.mean(rmse_lift)) if len(rmse_lift) else None,
            "median_rmse_lift": safe_float(np.median(rmse_lift)) if len(rmse_lift) else None,
            "min_rmse_lift": safe_float(np.min(rmse_lift)) if len(rmse_lift) else None,
            "max_rmse_lift": safe_float(np.max(rmse_lift)) if len(rmse_lift) else None,
            "mean_dev_pearson": safe_float(np.mean(dev_corr)) if len(dev_corr) else None,
            "median_dev_pearson": safe_float(np.median(dev_corr)) if len(dev_corr) else None,
            "min_dev_pearson": safe_float(np.min(dev_corr)) if len(dev_corr) else None,
            "max_dev_pearson": safe_float(np.max(dev_corr)) if len(dev_corr) else None,
            "mean_pred_dev_std": safe_float(np.mean(pred_std)) if len(pred_std) else None,
            "mean_true_dev_std": safe_float(np.mean(true_std)) if len(true_std) else None,
            "mean_std_ratio_pred_over_true": safe_float(np.mean(pred_std / (true_std + 1e-12))) if len(pred_std) and len(true_std) else None,
        },
    }


def make_subset_diagnostic(subset_metrics: pd.DataFrame) -> pd.DataFrame:
    if subset_metrics.empty:
        return pd.DataFrame()

    out = subset_metrics.copy()
    out["model"] = out["model"].astype(str)

    # Keep only useful rows and make sure fields exist.
    wanted_cols = [
        "target",
        "subset",
        "model",
        "n",
        "rmse",
        "lift_vs_stimulus_rmse",
        "balanced_accuracy",
        "lift_vs_stimulus_balanced_accuracy",
        "auroc",
        "lift_vs_stimulus_auroc",
        "dev_rmse",
        "dev_pearson",
        "dev_sign_acc",
        "true_dev_std",
        "pred_dev_std",
    ]

    for col in wanted_cols:
        if col not in out.columns:
            out[col] = np.nan

    return out[wanted_cols].sort_values(["subset", "model"]).reset_index(drop=True)


def choose_verdict(summary: dict[str, Any]) -> dict[str, Any]:
    agg = summary["aggregate"]
    counts = summary["fold_counts"]

    rmse_lift = agg.get("eeg_lift_vs_stimulus_rmse")
    auroc_lift = agg.get("eeg_lift_vs_stimulus_auroc")
    ba_lift = agg.get("eeg_lift_vs_stimulus_balanced_accuracy")
    dev_corr = agg.get("eeg_dev_pearson")

    rmse_good = rmse_lift is not None and rmse_lift > 0
    auc_good = auroc_lift is not None and auroc_lift > 0
    ba_good = ba_lift is not None and ba_lift > 0
    dev_good = dev_corr is not None and dev_corr > 0

    if rmse_good and auc_good and ba_good and dev_good:
        verdict = "go"
        reason = "Full LOSO EEG beats stimulus-only on aggregate RMSE, AUROC/BA, and residual correlation."
    elif (not rmse_good) and (not auc_good) and (not ba_good) and (not dev_good):
        verdict = "no_go_current_path"
        reason = "Full LOSO EEG is worse than stimulus-only on aggregate RMSE/AUROC/BA and has non-positive residual correlation."
    elif counts.get("rmse_better_than_stimulus", 0) >= max(1, summary["subjects"] // 2):
        verdict = "mixed_fold_level"
        reason = "Aggregate is not clearly positive, but EEG improves RMSE in many folds."
    else:
        verdict = "no_go_or_redesign"
        reason = "Full LOSO evidence is mixed or negative; current head/objective should not be treated as primary result."

    return {
        "verdict": verdict,
        "reason": reason,
        "key_aggregate": agg,
        "key_fold_counts": counts,
    }


def write_outputs(
    fold_metrics: pd.DataFrame,
    subject_cmp: pd.DataFrame,
    subset_diag: pd.DataFrame,
    failure_ranking: pd.DataFrame,
    summary: dict[str, Any],
    verdict: dict[str, Any],
):
    fold_metrics.to_csv(OUT_FOLD_METRICS, index=False)
    subject_cmp.to_csv(OUT_SUBJECT_COMPARISON, index=False)
    subset_diag.to_csv(OUT_SUBSET_DIAGNOSTIC, index=False)
    failure_ranking.to_csv(OUT_FAILURE_RANKING, index=False)

    subject_cols = [
        "test_subject",
        "eeg_rmse",
        "stimulus_rmse",
        "eeg_lift_vs_stimulus_rmse",
        "eeg_auroc",
        "stimulus_auroc",
        "eeg_lift_vs_stimulus_auroc",
        "eeg_balanced_accuracy",
        "stimulus_balanced_accuracy",
        "eeg_lift_vs_stimulus_balanced_accuracy",
        "eeg_dev_pearson",
        "eeg_dev_sign_acc",
        "eeg_pred_dev_std",
        "eeg_true_dev_std",
        "eeg_std_ratio_pred_over_true",
    ]

    failure_cols = [
        "test_subject",
        "failure_score",
        "eeg_lift_vs_stimulus_rmse",
        "eeg_dev_pearson",
        "eeg_rmse",
        "stimulus_rmse",
        "eeg_pred_dev_std",
        "eeg_true_dev_std",
        "eeg_std_ratio_pred_over_true",
    ]

    subset_cols = [
        "subset",
        "model",
        "n",
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

    best_rmse = subject_cmp.sort_values("eeg_lift_vs_stimulus_rmse", ascending=False).head(12)
    worst_rmse = subject_cmp.sort_values("eeg_lift_vs_stimulus_rmse", ascending=True).head(12)
    best_dev = subject_cmp.sort_values("eeg_dev_pearson", ascending=False).head(12)
    worst_dev = subject_cmp.sort_values("eeg_dev_pearson", ascending=True).head(12)

    lines = []
    lines.append("# ROCA-I-DARE EEG Gaussian 0.10 Full LOSO Diagnostic\n")
    lines.append("No model training was performed in this step. This report analyzes the full LOSO Gaussian 0.10 run.\n")

    lines.append("## Decision verdict\n")
    lines.append(f"- verdict: `{verdict['verdict']}`")
    lines.append(f"- reason: {verdict['reason']}")
    lines.append("")

    lines.append("## Aggregate summary\n")
    lines.append("```json")
    lines.append(json.dumps(clean_json(summary["aggregate"]), indent=2, ensure_ascii=False))
    lines.append("```\n")

    lines.append("## Fold count summary\n")
    lines.append("```json")
    lines.append(json.dumps(clean_json(summary["fold_counts"]), indent=2, ensure_ascii=False))
    lines.append("```\n")

    lines.append("## Fold distribution summary\n")
    lines.append("```json")
    lines.append(json.dumps(clean_json(summary["fold_distribution"]), indent=2, ensure_ascii=False))
    lines.append("```\n")

    lines.append("## Best subjects by RMSE lift\n")
    lines.append(md_table(best_rmse.to_dict(orient="records"), subject_cols))

    lines.append("\n## Worst subjects by RMSE lift\n")
    lines.append(md_table(worst_rmse.to_dict(orient="records"), subject_cols))

    lines.append("\n## Best subjects by residual correlation\n")
    lines.append(md_table(best_dev.to_dict(orient="records"), subject_cols))

    lines.append("\n## Worst subjects by residual correlation\n")
    lines.append(md_table(worst_dev.to_dict(orient="records"), subject_cols))

    lines.append("\n## Failure ranking\n")
    lines.append(md_table(failure_ranking.head(20).to_dict(orient="records"), failure_cols))

    lines.append("\n## Hard subset diagnostic\n")
    lines.append(md_table(subset_diag.to_dict(orient="records"), subset_cols))

    lines.append("\n## Interpretation\n")
    lines.append(
        "- Positive `eeg_lift_vs_stimulus_rmse` means EEG beat stimulus-only for that subject.\n"
        "- `eeg_dev_pearson` measures whether EEG residual predictions track subject-specific deviations.\n"
        "- `eeg_std_ratio_pred_over_true` shows how much of the true residual amplitude the model expresses.\n"
        "- If aggregate and most fold-level metrics are negative, this model/objective path should be redesigned.\n"
        "- If hard subsets improve despite aggregate failure, a restricted task formulation may still be worth exploring.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    payload = {
        "protocol": "EEG Gaussian 0.10 full LOSO diagnostic",
        "inputs": {
            "pred_csv": str(PRED_CSV),
            "main_csv": str(MAIN_CSV),
            "subset_csv": str(SUBSET_CSV),
            "fold_csv": str(FOLD_CSV),
        },
        "target_config": TARGET_CONFIG,
        "eeg_model": EEG_MODEL,
        "baseline_model": BASELINE_MODEL,
        "verdict": verdict,
        "summary": summary,
        "best_rmse_subjects": best_rmse.to_dict(orient="records"),
        "worst_rmse_subjects": worst_rmse.to_dict(orient="records"),
        "best_dev_pearson_subjects": best_dev.to_dict(orient="records"),
        "worst_dev_pearson_subjects": worst_dev.to_dict(orient="records"),
        "failure_ranking": failure_ranking.to_dict(orient="records"),
        "subset_diagnostic": subset_diag.to_dict(orient="records"),
        "notes": [
            "No training was run in this diagnostic.",
            "This analyzes the full 63-subject LOSO Gaussian 0.10 run.",
            "A no-go verdict applies to the current EEG residual regression path, not necessarily all EEG modeling.",
        ],
    }

    OUT_JSON.write_text(json.dumps(clean_json(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    print("ROCA step 05l completed.")
    print(f"wrote: {OUT_MD}")
    print(f"wrote: {OUT_JSON}")
    print(f"wrote: {OUT_FOLD_METRICS}")
    print(f"wrote: {OUT_SUBJECT_COMPARISON}")
    print(f"wrote: {OUT_SUBSET_DIAGNOSTIC}")
    print(f"wrote: {OUT_FAILURE_RANKING}")
    print()
    print("Decision verdict:")
    print(json.dumps(clean_json(verdict), indent=2, ensure_ascii=False))
    print()
    print("Fold counts:")
    print(json.dumps(clean_json(summary["fold_counts"]), indent=2, ensure_ascii=False))
    print()
    print("Fold distribution:")
    print(json.dumps(clean_json(summary["fold_distribution"]), indent=2, ensure_ascii=False))
    print()
    print("Worst subjects by failure score:")
    print(failure_ranking.head(15)[failure_cols].to_string(index=False))


def main():
    require_inputs()

    pred = pd.read_csv(PRED_CSV)
    main_metrics = pd.read_csv(MAIN_CSV)
    subset_metrics = pd.read_csv(SUBSET_CSV)

    pred["test_subject"] = pred["test_subject"].astype(int)
    pred["augmentation_config"] = pred["augmentation_config"].astype(str)
    pred["model"] = pred["model"].astype(str)

    fold_metrics = compute_fold_metrics(pred)
    subject_cmp = make_subject_comparison(fold_metrics)
    subset_diag = make_subset_diagnostic(subset_metrics)

    failure_ranking = subject_cmp.sort_values("failure_score", ascending=False).reset_index(drop=True)

    summary = summarize_subjects(subject_cmp, main_metrics)
    verdict = choose_verdict(summary)

    write_outputs(
        fold_metrics=fold_metrics,
        subject_cmp=subject_cmp,
        subset_diag=subset_diag,
        failure_ranking=failure_ranking,
        summary=summary,
        verdict=verdict,
    )


if __name__ == "__main__":
    main()
