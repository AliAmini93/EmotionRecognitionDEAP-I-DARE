#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROCA_DIR = ROOT / "docs" / "roca"
PRED_CSV = ROCA_DIR / "stimulus_only_predictions_current.csv"

OUT_JSON = ROCA_DIR / "deviation_and_disagreement_current.json"
OUT_MD = ROCA_DIR / "deviation_and_disagreement_current.md"
OUT_PER_STIM_CSV = ROCA_DIR / "deviation_per_stimulus_current.csv"
OUT_PER_SUBJECT_CSV = ROCA_DIR / "deviation_per_subject_current.csv"
OUT_SUBSET_CSV = ROCA_DIR / "high_disagreement_subset_metrics_current.csv"

TARGETS = ["valence", "arousal"]


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
    return pearson(
        pd.Series(y).rank(method="average").to_numpy(),
        pd.Series(p).rank(method="average").to_numpy(),
    )


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
    rank_sum_pos = ranks[y_bin == 1].sum()
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def entropy_binary(p):
    p = float(p)
    if p <= 0 or p >= 1:
        return 0.0
    return float(-(p * math.log(p) + (1 - p) * math.log(1 - p)))


def prediction_metrics(df):
    y = df["y_true_score"].to_numpy(dtype=float)
    pred = df["y_pred_score"].to_numpy(dtype=float)
    p_high = df["p_high"].to_numpy(dtype=float)

    err = pred - y
    y_bin = (y > 5).astype(int)
    y_hat = (p_high >= 0.5).astype(int)

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
        "accuracy": safe_float(np.mean(y_bin == y_hat)),
        "balanced_accuracy": safe_float(np.mean(recalls)),
        "macro_f1": safe_float(np.mean(f1s)),
        "auroc": auroc(y_bin, p_high),
    }


def deviation_summary(dev):
    dev = np.asarray(dev, dtype=float)
    dev = dev[np.isfinite(dev)]
    abs_dev = np.abs(dev)

    return {
        "n": int(len(dev)),
        "mean_deviation": safe_float(np.mean(dev)),
        "std_deviation": safe_float(np.std(dev)),
        "mean_abs_deviation": safe_float(np.mean(abs_dev)),
        "median_abs_deviation": safe_float(np.median(abs_dev)),
        "rmse_if_predict_zero_deviation": safe_float(np.sqrt(np.mean(dev * dev))),
        "q75_abs_deviation": safe_float(np.quantile(abs_dev, 0.75)),
        "q90_abs_deviation": safe_float(np.quantile(abs_dev, 0.90)),
        "q95_abs_deviation": safe_float(np.quantile(abs_dev, 0.95)),
        "prop_abs_dev_ge_0p5": safe_float(np.mean(abs_dev >= 0.5)),
        "prop_abs_dev_ge_1p0": safe_float(np.mean(abs_dev >= 1.0)),
        "prop_abs_dev_ge_1p5": safe_float(np.mean(abs_dev >= 1.5)),
        "prop_abs_dev_ge_2p0": safe_float(np.mean(abs_dev >= 2.0)),
        "prop_abs_dev_ge_3p0": safe_float(np.mean(abs_dev >= 3.0)),
        "positive_deviation_rate": safe_float(np.mean(dev > 0)),
        "negative_deviation_rate": safe_float(np.mean(dev < 0)),
        "near_zero_abs_lt_0p5_rate": safe_float(np.mean(abs_dev < 0.5)),
    }


def md_table(rows, cols):
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for row in rows:
        vals = []
        for c in cols:
            v = row.get(c, "")
            if isinstance(v, float):
                vals.append(f"{v:.4f}" if math.isfinite(v) else "")
            elif v is None:
                vals.append("")
            else:
                vals.append(str(v))
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


def main():
    if not PRED_CSV.exists():
        raise FileNotFoundError(f"Missing predictions CSV: {PRED_CSV}")

    pred = pd.read_csv(PRED_CSV)
    stim_only = pred[pred["model"] == "stimulus_only"].copy()

    required = [
        "target",
        "test_subject",
        "stimulus_id",
        "y_true_score",
        "y_pred_score",
        "p_high",
        "true_deviation_from_train_stimulus_mean",
    ]
    missing = [c for c in required if c not in stim_only.columns]
    if missing:
        raise KeyError(f"Missing columns in stimulus-only predictions: {missing}")

    per_stim_rows = []
    per_subject_rows = []
    subset_rows = []
    summary = {
        "input": str(PRED_CSV),
        "protocol": "strict LOSO stimulus-only residual analysis",
        "note": (
            "true_deviation_from_train_stimulus_mean is y_true minus train-subject "
            "stimulus mean for the same stimulus. It is the residual that physiology "
            "models should try to predict."
        ),
        "targets": {},
    }

    for target in TARGETS:
        df = stim_only[stim_only["target"] == target].copy()
        dev = df["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)

        target_summary = {
            "stimulus_only_metrics": prediction_metrics(df),
            "deviation_summary": deviation_summary(dev),
        }

        # Per subject residual landscape
        for sid, g in df.groupby("test_subject"):
            d = g["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
            per_subject_rows.append({
                "target": target,
                "test_subject": int(sid),
                "n": int(len(g)),
                "mean_deviation": safe_float(np.mean(d)),
                "std_deviation": safe_float(np.std(d)),
                "mean_abs_deviation": safe_float(np.mean(np.abs(d))),
                "rmse_deviation": safe_float(np.sqrt(np.mean(d * d))),
                "positive_deviation_rate": safe_float(np.mean(d > 0)),
            })

        # Per stimulus residual and disagreement landscape
        for stim, g in df.groupby("stimulus_id"):
            y = g["y_true_score"].to_numpy(dtype=float)
            d = g["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
            high_rate = float(np.mean(y > 5))
            per_stim_rows.append({
                "target": target,
                "stimulus_id": str(stim),
                "n": int(len(g)),
                "score_mean": safe_float(np.mean(y)),
                "score_std": safe_float(np.std(y)),
                "score_min": safe_float(np.min(y)),
                "score_max": safe_float(np.max(y)),
                "high_rate": safe_float(high_rate),
                "high_low_entropy": safe_float(entropy_binary(high_rate)),
                "mean_deviation": safe_float(np.mean(d)),
                "std_deviation": safe_float(np.std(d)),
                "mean_abs_deviation": safe_float(np.mean(np.abs(d))),
                "rmse_deviation": safe_float(np.sqrt(np.mean(d * d))),
            })

        per_stim_target = pd.DataFrame([r for r in per_stim_rows if r["target"] == target])

        # High-disagreement subsets. Descriptive subsets; final model selection must not use test labels.
        subset_defs = {
            "top25_score_std": per_stim_target.sort_values("score_std", ascending=False).head(8),
            "top25_entropy": per_stim_target.sort_values("high_low_entropy", ascending=False).head(8),
            "top25_deviation_rmse": per_stim_target.sort_values("rmse_deviation", ascending=False).head(8),
        }

        target_summary["top_stimuli"] = {}
        for subset_name, stim_table in subset_defs.items():
            stim_ids = set(stim_table["stimulus_id"].astype(str).tolist())
            sub = df[df["stimulus_id"].astype(str).isin(stim_ids)].copy()
            row = {
                "target": target,
                "subset": subset_name,
                "n_stimuli": int(len(stim_ids)),
                "n_trials": int(len(sub)),
            }
            row.update(prediction_metrics(sub))
            subset_rows.append(row)

            target_summary["top_stimuli"][subset_name] = stim_table[
                [
                    "stimulus_id",
                    "score_mean",
                    "score_std",
                    "high_rate",
                    "high_low_entropy",
                    "mean_abs_deviation",
                    "rmse_deviation",
                ]
            ].to_dict(orient="records")

        summary["targets"][target] = target_summary

    per_stim_df = pd.DataFrame(per_stim_rows)
    per_subject_df = pd.DataFrame(per_subject_rows)
    subset_df = pd.DataFrame(subset_rows)

    per_stim_df.to_csv(OUT_PER_STIM_CSV, index=False)
    per_subject_df.to_csv(OUT_PER_SUBJECT_CSV, index=False)
    subset_df.to_csv(OUT_SUBSET_CSV, index=False)
    OUT_JSON.write_text(json.dumps(clean_json(summary), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("# ROCA-I-DARE Deviation and High-disagreement Analysis\n")
    lines.append("No EEG/EMG model was trained.\n")
    lines.append("This report analyzes the residual left by strict LOSO stimulus-only baseline.\n")

    for target in TARGETS:
        info = summary["targets"][target]
        lines.append(f"\n## Target: {target}\n")

        lines.append("### Stimulus-only metrics\n")
        lines.append(md_table([info["stimulus_only_metrics"]], [
            "n", "mae", "rmse", "pearson", "spearman",
            "accuracy", "balanced_accuracy", "macro_f1", "auroc",
        ]))

        lines.append("\n### Deviation summary\n")
        lines.append(md_table([info["deviation_summary"]], [
            "n",
            "mean_deviation",
            "std_deviation",
            "mean_abs_deviation",
            "median_abs_deviation",
            "rmse_if_predict_zero_deviation",
            "q75_abs_deviation",
            "q90_abs_deviation",
            "q95_abs_deviation",
            "prop_abs_dev_ge_1p0",
            "prop_abs_dev_ge_2p0",
            "positive_deviation_rate",
        ]))

        lines.append("\n### High-disagreement subset metrics\n")
        rows = subset_df[subset_df["target"] == target].to_dict(orient="records")
        lines.append(md_table(rows, [
            "subset", "n_stimuli", "n_trials", "mae", "rmse",
            "pearson", "balanced_accuracy", "macro_f1", "auroc",
        ]))

        for subset_name in ["top25_score_std", "top25_entropy", "top25_deviation_rmse"]:
            lines.append(f"\n### {subset_name}: top stimuli\n")
            lines.append(md_table(info["top_stimuli"][subset_name], [
                "stimulus_id",
                "score_mean",
                "score_std",
                "high_rate",
                "high_low_entropy",
                "mean_abs_deviation",
                "rmse_deviation",
            ]))

    lines.append("\n## Interpretation\n")
    lines.append(
        "- The deviation is the remaining error after train-subject stimulus mean is used.\n"
        "- EEG/EMG probes should try to predict this deviation, not merely reproduce stimulus prior.\n"
        "- High-disagreement stimuli are where physiology has the clearest chance to add value.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 02 completed.")
    print(f"wrote: {OUT_MD}")
    print(f"wrote: {OUT_JSON}")
    print(f"wrote: {OUT_PER_STIM_CSV}")
    print(f"wrote: {OUT_PER_SUBJECT_CSV}")
    print(f"wrote: {OUT_SUBSET_CSV}")
    print()

    for target in TARGETS:
        d = summary["targets"][target]["deviation_summary"]
        m = summary["targets"][target]["stimulus_only_metrics"]
        print(f"{target}:")
        print(f"  stimulus_only_rmse: {m['rmse']:.4f}")
        print(f"  stimulus_only_mae: {m['mae']:.4f}")
        print(f"  deviation_std: {d['std_deviation']:.4f}")
        print(f"  mean_abs_deviation: {d['mean_abs_deviation']:.4f}")
        print(f"  prop_abs_dev_ge_1p0: {d['prop_abs_dev_ge_1p0']:.4f}")
        print(f"  prop_abs_dev_ge_2p0: {d['prop_abs_dev_ge_2p0']:.4f}")
        print()

    print("High-disagreement subset metrics:")
    print(subset_df[
        ["target", "subset", "n_stimuli", "n_trials", "mae", "rmse", "balanced_accuracy", "auroc"]
    ].to_string(index=False))


if __name__ == "__main__":
    main()
