#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROCA_DIR = ROOT / "docs" / "roca"

PRED_CSV = ROCA_DIR / "emg_only_probe_predictions_current.csv"
SELECTED_CSV = ROCA_DIR / "fold_safe_selected_stimuli_current.csv"

OUT_MD = ROCA_DIR / "emg_only_probe_clipped_eval_current.md"
OUT_JSON = ROCA_DIR / "emg_only_probe_clipped_eval_current.json"
OUT_MAIN_CSV = ROCA_DIR / "emg_only_probe_clipped_main_metrics_current.csv"
OUT_SUBSET_CSV = ROCA_DIR / "emg_only_probe_clipped_subset_metrics_current.csv"

TARGETS = ["valence", "arousal"]
MODELS = ["stimulus_only", "emg_direct_ridge", "emg_residual_ridge"]


def safe_float(x):
    try:
        v = float(x)
    except Exception:
        return None
    return v if math.isfinite(v) else None


def pearson(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y, p = y[m], p[m]
    if len(y) < 2 or np.std(y) == 0 or np.std(p) == 0:
        return None
    return float(np.corrcoef(y, p)[0, 1])


def spearman(y, p):
    yr = pd.Series(y).rank(method="average").to_numpy()
    pr = pd.Series(p).rank(method="average").to_numpy()
    return pearson(yr, pr)


def ccc(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y, p = y[m], p[m]
    if len(y) < 2:
        return None
    my, mp = y.mean(), p.mean()
    vy, vp = y.var(), p.var()
    cov = np.mean((y - my) * (p - mp))
    den = vy + vp + (my - mp) ** 2
    if den == 0:
        return None
    return float(2 * cov / den)


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


def prediction_metrics(df):
    y = df["y_true_score"].to_numpy(dtype=float)
    pred = df["y_pred_score_clipped"].to_numpy(dtype=float)

    err = pred - y
    y_bin = (y > 5).astype(int)
    y_hat = (pred > 5).astype(int)

    recalls = []
    f1s = []
    for cls in [0, 1]:
        tp = int(((y_bin == cls) & (y_hat == cls)).sum())
        fp = int(((y_bin != cls) & (y_hat == cls)).sum())
        fn = int(((y_bin == cls) & (y_hat != cls)).sum())
        support = int((y_bin == cls).sum())
        if support > 0:
            recalls.append(tp / support)
        denom = 2 * tp + fp + fn
        f1s.append((2 * tp / denom) if denom > 0 else 0.0)

    return {
        "n": int(len(df)),
        "mae": safe_float(np.mean(np.abs(err))),
        "rmse": safe_float(np.sqrt(np.mean(err * err))),
        "pearson": pearson(y, pred),
        "spearman": spearman(y, pred),
        "ccc": ccc(y, pred),
        "balanced_accuracy": safe_float(np.mean(recalls)),
        "macro_f1": safe_float(np.mean(f1s)),
        "auroc": auroc(y_bin, pred),
    }


def deviation_metrics(df):
    true_dev = df["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
    pred_dev = df["y_pred_deviation_clipped"].to_numpy(dtype=float)

    err = pred_dev - true_dev
    sign_true = np.sign(true_dev)
    sign_pred = np.sign(pred_dev)
    nz = sign_true != 0

    return {
        "dev_rmse": safe_float(np.sqrt(np.mean(err * err))),
        "dev_mae": safe_float(np.mean(np.abs(err))),
        "dev_pearson": pearson(true_dev, pred_dev),
        "dev_spearman": spearman(true_dev, pred_dev),
        "dev_sign_acc": safe_float(np.mean(sign_true[nz] == sign_pred[nz])) if nz.sum() else None,
        "pred_dev_std": safe_float(np.std(pred_dev)),
    }


def md_table(rows, cols):
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


def add_lifts(df, group_cols):
    rows = []
    lower_is_better = {"mae", "rmse", "dev_mae", "dev_rmse"}
    metrics = [
        "mae", "rmse", "pearson", "spearman", "ccc",
        "balanced_accuracy", "macro_f1", "auroc",
        "dev_mae", "dev_rmse", "dev_pearson", "dev_spearman", "dev_sign_acc",
        "pred_dev_std",
    ]

    for keys, g in df.groupby(group_cols, dropna=False):
        base = g[g["model"] == "stimulus_only"]
        if base.empty:
            continue
        base = base.iloc[0]

        for _, row in g.iterrows():
            out = row.to_dict()
            for m in metrics:
                if m not in row or m not in base:
                    continue
                rv = row[m]
                bv = base[m]
                if pd.isna(rv) or pd.isna(bv):
                    out[f"lift_vs_stimulus_{m}"] = None
                elif m in lower_is_better:
                    out[f"lift_vs_stimulus_{m}"] = safe_float(float(bv) - float(rv))
                else:
                    out[f"lift_vs_stimulus_{m}"] = safe_float(float(rv) - float(bv))
            rows.append(out)

    return pd.DataFrame(rows)


def add_subset_flags(pred, selected):
    out = pred.copy()
    for subset in sorted(selected["subset"].unique()):
        key = selected[selected["subset"] == subset][
            ["target", "test_subject", "stimulus_id"]
        ].copy()
        key["selected"] = True

        merged = out.merge(
            key,
            on=["target", "test_subject", "stimulus_id"],
            how="left",
        )
        out[f"is_{subset}"] = merged["selected"].fillna(False).astype(bool).to_numpy()
    return out


def compute_main(pred):
    rows = []
    for target in TARGETS:
        for model in MODELS:
            sub = pred[(pred["target"] == target) & (pred["model"] == model)]
            row = {"target": target, "model": model}
            row.update(prediction_metrics(sub))
            row.update(deviation_metrics(sub))
            rows.append(row)
    return add_lifts(pd.DataFrame(rows), ["target"])


def compute_subsets(pred):
    subset_cols = [c for c in pred.columns if c.startswith("is_top25_train_")]
    rows = []

    for target in TARGETS:
        for subset_col in subset_cols:
            subset_name = subset_col.replace("is_", "")
            for model in MODELS:
                sub = pred[
                    (pred["target"] == target)
                    & (pred["model"] == model)
                    & (pred[subset_col])
                ]
                row = {
                    "target": target,
                    "subset": subset_name,
                    "model": model,
                }
                row.update(prediction_metrics(sub))
                row.update(deviation_metrics(sub))
                rows.append(row)

    return add_lifts(pd.DataFrame(rows), ["target", "subset"])


def main():
    if not PRED_CSV.exists():
        raise FileNotFoundError(PRED_CSV)
    if not SELECTED_CSV.exists():
        raise FileNotFoundError(SELECTED_CSV)

    pred = pd.read_csv(PRED_CSV)
    selected = pd.read_csv(SELECTED_CSV)

    pred["test_subject"] = pred["test_subject"].astype(int)
    pred["stimulus_id"] = pred["stimulus_id"].astype(str)
    selected["test_subject"] = selected["test_subject"].astype(int)
    selected["stimulus_id"] = selected["stimulus_id"].astype(str)

    pred["y_pred_score_raw"] = pred["y_pred_score"].astype(float)
    pred["y_pred_score_clipped"] = pred["y_pred_score_raw"].clip(1.0, 9.0)
    pred["y_pred_deviation_clipped"] = (
        pred["y_pred_score_clipped"] - pred["train_stimulus_mean"].astype(float)
    )

    pred = add_subset_flags(pred, selected)

    main_df = compute_main(pred)
    subset_df = compute_subsets(pred)

    main_df.to_csv(OUT_MAIN_CSV, index=False)
    subset_df.to_csv(OUT_SUBSET_CSV, index=False)

    summary = {
        "protocol": "post-hoc fixed clipping sanity check",
        "clip_range": [1.0, 9.0],
        "important_notes": [
            "No model is retrained.",
            "Clipping is a fixed SAM-scale constraint and does not use test labels.",
            "Deviation prediction is recomputed after clipping as clipped_score - train_stimulus_mean.",
            "This check evaluates whether raw Ridge outliers were responsible for poor RMSE.",
        ],
        "main_metrics": main_df.to_dict(orient="records"),
        "subset_metrics": subset_df.to_dict(orient="records"),
    }

    OUT_JSON.write_text(json.dumps(clean_json(summary), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("# ROCA-I-DARE EMG-only Clipped Evaluation\n")
    lines.append("No model was retrained. Predictions are clipped to SAM range `[1, 9]`.\n")

    main_cols = [
        "target", "model", "n",
        "mae", "rmse", "pearson", "balanced_accuracy", "macro_f1", "auroc",
        "dev_rmse", "dev_pearson", "dev_sign_acc", "pred_dev_std",
        "lift_vs_stimulus_rmse",
        "lift_vs_stimulus_balanced_accuracy",
        "lift_vs_stimulus_auroc",
        "lift_vs_stimulus_dev_rmse",
        "lift_vs_stimulus_dev_pearson",
    ]

    lines.append("## Main clipped metrics\n")
    lines.append(md_table(main_df.to_dict(orient="records"), main_cols))

    subset_cols = [
        "target", "subset", "model", "n",
        "mae", "rmse", "balanced_accuracy", "auroc",
        "dev_rmse", "dev_pearson", "dev_sign_acc", "pred_dev_std",
        "lift_vs_stimulus_rmse",
        "lift_vs_stimulus_balanced_accuracy",
        "lift_vs_stimulus_auroc",
        "lift_vs_stimulus_dev_rmse",
        "lift_vs_stimulus_dev_pearson",
    ]

    lines.append("\n## Fold-safe hard subset clipped metrics\n")
    lines.append(md_table(subset_df.to_dict(orient="records"), subset_cols))

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 04b completed.")
    print(f"wrote: {OUT_MD}")
    print(f"wrote: {OUT_JSON}")
    print(f"wrote: {OUT_MAIN_CSV}")
    print(f"wrote: {OUT_SUBSET_CSV}")
    print()
    print("Main clipped metrics:")
    print(main_df[
        [
            "target", "model", "mae", "rmse", "pearson",
            "balanced_accuracy", "auroc",
            "dev_rmse", "dev_pearson", "pred_dev_std",
            "lift_vs_stimulus_rmse",
            "lift_vs_stimulus_balanced_accuracy",
            "lift_vs_stimulus_auroc",
            "lift_vs_stimulus_dev_rmse",
            "lift_vs_stimulus_dev_pearson",
        ]
    ].to_string(index=False))
    print()
    print("Fold-safe subset clipped metrics:")
    print(subset_df[
        [
            "target", "subset", "model", "rmse",
            "balanced_accuracy", "auroc",
            "dev_rmse", "dev_pearson", "pred_dev_std",
            "lift_vs_stimulus_rmse",
            "lift_vs_stimulus_balanced_accuracy",
            "lift_vs_stimulus_auroc",
            "lift_vs_stimulus_dev_rmse",
            "lift_vs_stimulus_dev_pearson",
        ]
    ].to_string(index=False))


if __name__ == "__main__":
    main()
