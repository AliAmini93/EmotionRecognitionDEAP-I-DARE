#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / ".cache"
ROCA_DIR = ROOT / "docs" / "roca"

DEFAULT_TRIAL_INDEX = CACHE_DIR / "idare_trial_index.csv"

OUT_MD = ROCA_DIR / "idare_label_variance_decomposition_current.md"
OUT_JSON = ROCA_DIR / "idare_label_variance_decomposition_current.json"
OUT_SUMMARY = ROCA_DIR / "idare_label_variance_decomposition_current.csv"
OUT_BINARY = ROCA_DIR / "idare_label_variance_decomposition_binary_current.csv"
OUT_SUBJECT = ROCA_DIR / "idare_label_variance_decomposition_subject_current.csv"
OUT_PRED = ROCA_DIR / "idare_label_variance_decomposition_predictions_current.csv"

TARGETS = {
    "valence": "valence_score",
    "arousal": "arousal_score",
}

LABEL_POLICIES = ["midpoint_as_low", "midpoint_as_high", "discard_midpoint"]
EPS = 1e-12


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--trial-index", type=Path, default=DEFAULT_TRIAL_INDEX)
    return p.parse_args()


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
    if len(y) < 2 or np.std(y) < EPS or np.std(p) < EPS:
        return None
    return float(np.corrcoef(y, p)[0, 1])


def spearman(y, p):
    y = pd.Series(y).rank(method="average").to_numpy(dtype=float)
    p = pd.Series(p).rank(method="average").to_numpy(dtype=float)
    return pearson(y, p)


def ccc(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y, p = y[m], p[m]
    if len(y) < 2:
        return None
    my = float(np.mean(y))
    mp = float(np.mean(p))
    vy = float(np.var(y))
    vp = float(np.var(p))
    cov = float(np.mean((y - my) * (p - mp)))
    denom = vy + vp + (my - mp) ** 2
    if denom < EPS:
        return None
    return float(2.0 * cov / denom)


def auroc(y_bin, score):
    y_bin = np.asarray(y_bin, dtype=int)
    score = np.asarray(score, dtype=float)
    m = np.isfinite(score)
    y_bin, score = y_bin[m], score[m]
    n_pos = int((y_bin == 1).sum())
    n_neg = int((y_bin == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return None
    ranks = pd.Series(score).rank(method="average").to_numpy(dtype=float)
    rank_sum_pos = float(ranks[y_bin == 1].sum())
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def regression_metrics(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    err = p - y
    return {
        "mae": safe_float(np.mean(np.abs(err))),
        "rmse": safe_float(np.sqrt(np.mean(err * err))),
        "pearson": pearson(y, p),
        "spearman": spearman(y, p),
        "ccc": ccc(y, p),
        "y_true_mean": safe_float(np.mean(y)),
        "y_true_std": safe_float(np.std(y)),
        "y_pred_mean": safe_float(np.mean(p)),
        "y_pred_std": safe_float(np.std(p)),
        "residual_mean": safe_float(np.mean(y - p)),
        "residual_std": safe_float(np.std(y - p)),
    }


def binary_arrays(y_score, pred_score, policy: str):
    y_score = np.asarray(y_score, dtype=float)
    pred_score = np.asarray(pred_score, dtype=float)

    m = np.isfinite(y_score) & np.isfinite(pred_score)
    if policy == "discard_midpoint":
        m &= y_score != 5.0
        y_bin = (y_score[m] > 5.0).astype(int)
        pred_bin = (pred_score[m] > 5.0).astype(int)
    elif policy == "midpoint_as_high":
        y_bin = (y_score[m] >= 5.0).astype(int)
        pred_bin = (pred_score[m] >= 5.0).astype(int)
    elif policy == "midpoint_as_low":
        y_bin = (y_score[m] > 5.0).astype(int)
        pred_bin = (pred_score[m] > 5.0).astype(int)
    else:
        raise ValueError(f"unknown label policy: {policy}")

    return y_bin, pred_bin, pred_score[m]


def binary_metrics(y_score, pred_score, policy: str):
    y_bin, pred_bin, score = binary_arrays(y_score, pred_score, policy)

    if len(y_bin) == 0:
        return {
            "binary_n": 0,
            "accuracy": None,
            "balanced_accuracy": None,
            "macro_f1": None,
            "auroc": None,
            "n_low": 0,
            "n_high": 0,
            "majority_accuracy": None,
            "true_high_rate": None,
            "pred_high_rate": None,
        }

    recalls = []
    f1s = []
    for cls in [0, 1]:
        tp = int(((y_bin == cls) & (pred_bin == cls)).sum())
        fp = int(((y_bin != cls) & (pred_bin == cls)).sum())
        fn = int(((y_bin == cls) & (pred_bin != cls)).sum())
        support = int((y_bin == cls).sum())

        if support > 0:
            recalls.append(tp / support)

        denom = 2 * tp + fp + fn
        f1s.append((2 * tp / denom) if denom > 0 else 0.0)

    n_low = int((y_bin == 0).sum())
    n_high = int((y_bin == 1).sum())

    return {
        "binary_n": int(len(y_bin)),
        "accuracy": safe_float(np.mean(y_bin == pred_bin)),
        "balanced_accuracy": safe_float(np.mean(recalls)) if recalls else None,
        "macro_f1": safe_float(np.mean(f1s)),
        "auroc": auroc(y_bin, score),
        "n_low": n_low,
        "n_high": n_high,
        "majority_accuracy": safe_float(max(n_low, n_high) / len(y_bin)),
        "true_high_rate": safe_float(np.mean(y_bin == 1)),
        "pred_high_rate": safe_float(np.mean(pred_bin == 1)),
    }


def r2_from_pred(y, pred):
    y = np.asarray(y, dtype=float)
    pred = np.asarray(pred, dtype=float)
    sse = float(np.sum((y - pred) ** 2))
    sst = float(np.sum((y - np.mean(y)) ** 2))
    if sst < EPS:
        return None
    return float(1.0 - sse / sst)


def additive_subject_stimulus_lstsq(df: pd.DataFrame, score_col: str):
    y = df[score_col].to_numpy(dtype=float)

    subj_codes, subj_levels = pd.factorize(df["subject_id"].astype(str), sort=True)
    stim_codes, stim_levels = pd.factorize(df["stimulus_id"].astype(str), sort=True)

    n = len(df)
    n_subj = len(subj_levels)
    n_stim = len(stim_levels)

    # Intercept + subject dummies excluding first + stimulus dummies excluding first.
    X = np.ones((n, 1 + (n_subj - 1) + (n_stim - 1)), dtype=float)

    col = 1
    for j in range(1, n_subj):
        X[:, col] = (subj_codes == j).astype(float)
        col += 1

    for j in range(1, n_stim):
        X[:, col] = (stim_codes == j).astype(float)
        col += 1

    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ beta

    return pred, {
        "additive_design_rank": int(np.linalg.matrix_rank(X)),
        "additive_design_cols": int(X.shape[1]),
    }


def load_trial_index(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    required = ["subject_id", "stimulus_id", "valence_score", "arousal_score"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"trial index missing columns: {missing}")

    df = df[required].copy()
    df["subject_id"] = df["subject_id"].astype(int)
    df["stimulus_id"] = df["stimulus_id"].astype(str)

    before = len(df)
    df = df.drop_duplicates(["subject_id", "stimulus_id"]).reset_index(drop=True)
    after = len(df)

    if after != before:
        print(f"[WARN] dropped duplicate subject/stimulus rows: before={before} after={after}")

    return df


def make_loso_predictions(df: pd.DataFrame, target: str, score_col: str):
    rows = []

    subjects = sorted(df["subject_id"].unique().tolist())

    for test_subject in subjects:
        train = df[df["subject_id"].ne(test_subject)].copy()
        test = df[df["subject_id"].eq(test_subject)].copy()

        global_mean = float(train[score_col].mean())
        stim_means = train.groupby("stimulus_id")[score_col].mean()

        pred_stim = test["stimulus_id"].map(stim_means).astype(float).fillna(global_mean).to_numpy(dtype=float)
        pred_global = np.full(len(test), global_mean, dtype=float)
        y = test[score_col].to_numpy(dtype=float)

        fold = test[["subject_id", "stimulus_id"]].copy()
        fold = fold.rename(columns={"subject_id": "test_subject"})
        fold["target"] = target
        fold["y_true_score"] = y
        fold["y_pred_global_train_mean"] = pred_global
        fold["y_pred_stimulus_train_mean"] = pred_stim
        fold["residual_vs_stimulus_train_mean"] = y - pred_stim
        fold["residual_vs_global_train_mean"] = y - pred_global
        rows.append(fold)

    return pd.concat(rows, ignore_index=True)


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


def main():
    args = parse_args()

    print("[INFO] I-DARE label variance decomposition")
    print(f"[INFO] trial_index={args.trial_index}")

    ROCA_DIR.mkdir(parents=True, exist_ok=True)

    df = load_trial_index(args.trial_index)
    subjects = sorted(df["subject_id"].unique().tolist())
    stimuli = sorted(df["stimulus_id"].unique().tolist())

    all_pred = []
    summary_rows = []
    binary_rows = []
    subject_rows = []

    for target, score_col in TARGETS.items():
        print(f"[TARGET] {target}")

        y = df[score_col].to_numpy(dtype=float)
        y_mean = float(np.mean(y))
        y_std = float(np.std(y))
        sst = float(np.sum((y - y_mean) ** 2))

        stim_pred_in = df["stimulus_id"].map(df.groupby("stimulus_id")[score_col].mean()).to_numpy(dtype=float)
        subj_pred_in = df["subject_id"].map(df.groupby("subject_id")[score_col].mean()).to_numpy(dtype=float)
        additive_pred_in, additive_diag = additive_subject_stimulus_lstsq(df, score_col)

        r2_stim_in = r2_from_pred(y, stim_pred_in)
        r2_subj_in = r2_from_pred(y, subj_pred_in)
        r2_add_in = r2_from_pred(y, additive_pred_in)

        pred = make_loso_predictions(df, target, score_col)
        all_pred.append(pred)

        y_loso = pred["y_true_score"].to_numpy(dtype=float)
        global_pred = pred["y_pred_global_train_mean"].to_numpy(dtype=float)
        stim_pred = pred["y_pred_stimulus_train_mean"].to_numpy(dtype=float)

        global_m = regression_metrics(y_loso, global_pred)
        stim_m = regression_metrics(y_loso, stim_pred)

        sse_global_loso = float(np.sum((y_loso - global_pred) ** 2))
        sse_stim_loso = float(np.sum((y_loso - stim_pred) ** 2))
        loso_stimulus_r2_vs_global = (
            float(1.0 - sse_stim_loso / sse_global_loso)
            if sse_global_loso > EPS else None
        )

        row = {
            "target": target,
            "n": int(len(df)),
            "subjects": int(len(subjects)),
            "stimuli": int(len(stimuli)),
            "y_mean": safe_float(y_mean),
            "y_std": safe_float(y_std),
            "sst_total": safe_float(sst),

            "r2_stimulus_in_sample": safe_float(r2_stim_in),
            "r2_subject_in_sample": safe_float(r2_subj_in),
            "r2_subject_plus_stimulus_in_sample": safe_float(r2_add_in),
            "unique_stimulus_r2_over_subject": safe_float(r2_add_in - r2_subj_in) if r2_add_in is not None and r2_subj_in is not None else None,
            "unique_subject_r2_over_stimulus": safe_float(r2_add_in - r2_stim_in) if r2_add_in is not None and r2_stim_in is not None else None,
            "overlap_r2_stimulus_subject": safe_float(r2_stim_in + r2_subj_in - r2_add_in) if r2_add_in is not None and r2_stim_in is not None and r2_subj_in is not None else None,

            "loso_global_mae": global_m["mae"],
            "loso_global_rmse": global_m["rmse"],
            "loso_global_pearson": global_m["pearson"],
            "loso_global_spearman": global_m["spearman"],
            "loso_global_ccc": global_m["ccc"],
            "loso_global_pred_std": global_m["y_pred_std"],

            "loso_stimulus_mae": stim_m["mae"],
            "loso_stimulus_rmse": stim_m["rmse"],
            "loso_stimulus_pearson": stim_m["pearson"],
            "loso_stimulus_spearman": stim_m["spearman"],
            "loso_stimulus_ccc": stim_m["ccc"],
            "loso_stimulus_pred_std": stim_m["y_pred_std"],

            "lift_stimulus_vs_global_mae": safe_float(global_m["mae"] - stim_m["mae"]),
            "lift_stimulus_vs_global_rmse": safe_float(global_m["rmse"] - stim_m["rmse"]),
            "lift_stimulus_vs_global_pearson": safe_float(stim_m["pearson"] - global_m["pearson"]) if stim_m["pearson"] is not None and global_m["pearson"] is not None else None,
            "lift_stimulus_vs_global_spearman": safe_float(stim_m["spearman"] - global_m["spearman"]) if stim_m["spearman"] is not None and global_m["spearman"] is not None else None,
            "lift_stimulus_vs_global_ccc": safe_float(stim_m["ccc"] - global_m["ccc"]) if stim_m["ccc"] is not None and global_m["ccc"] is not None else None,

            "loso_stimulus_r2_vs_loso_global": safe_float(loso_stimulus_r2_vs_global),
            "loso_stimulus_residual_mean": stim_m["residual_mean"],
            "loso_stimulus_residual_std": stim_m["residual_std"],
            "residual_std_ratio_after_loso_stimulus": safe_float(stim_m["residual_std"] / y_std) if y_std > EPS else None,
        }
        row.update(additive_diag)
        summary_rows.append(row)

        for test_subject, g in pred.groupby("test_subject"):
            ys = g["y_true_score"].to_numpy(dtype=float)
            pg = g["y_pred_global_train_mean"].to_numpy(dtype=float)
            ps = g["y_pred_stimulus_train_mean"].to_numpy(dtype=float)

            gm = regression_metrics(ys, pg)
            sm = regression_metrics(ys, ps)

            subject_rows.append({
                "target": target,
                "test_subject": int(test_subject),
                "n": int(len(g)),
                "global_rmse": gm["rmse"],
                "stimulus_rmse": sm["rmse"],
                "lift_stimulus_vs_global_rmse": safe_float(gm["rmse"] - sm["rmse"]),
                "global_mae": gm["mae"],
                "stimulus_mae": sm["mae"],
                "lift_stimulus_vs_global_mae": safe_float(gm["mae"] - sm["mae"]),
                "stimulus_pearson": sm["pearson"],
                "stimulus_spearman": sm["spearman"],
                "stimulus_residual_std": sm["residual_std"],
            })

        for policy in LABEL_POLICIES:
            for model_name, pred_col in [
                ("global_train_mean", "y_pred_global_train_mean"),
                ("stimulus_only", "y_pred_stimulus_train_mean"),
            ]:
                bm = binary_metrics(
                    pred["y_true_score"].to_numpy(dtype=float),
                    pred[pred_col].to_numpy(dtype=float),
                    policy=policy,
                )
                bm.update({
                    "target": target,
                    "label_policy": policy,
                    "model": model_name,
                })
                binary_rows.append(bm)

    pred_df = pd.concat(all_pred, ignore_index=True)
    summary = pd.DataFrame(summary_rows)
    binary = pd.DataFrame(binary_rows)
    subject = pd.DataFrame(subject_rows)

    for (target, policy), g in binary.groupby(["target", "label_policy"], dropna=False):
        base = g[g["model"].eq("global_train_mean")]
        if base.empty:
            continue
        base = base.iloc[0]
        idxs = g.index

        for metric in ["accuracy", "balanced_accuracy", "macro_f1", "auroc"]:
            base_val = base.get(metric)
            vals = []
            for idx in idxs:
                cur = binary.loc[idx, metric]
                if pd.isna(cur) or pd.isna(base_val):
                    vals.append(None)
                else:
                    vals.append(float(cur) - float(base_val))
            binary.loc[idxs, f"lift_vs_global_{metric}"] = vals

    summary.to_csv(OUT_SUMMARY, index=False)
    binary.to_csv(OUT_BINARY, index=False)
    subject.to_csv(OUT_SUBJECT, index=False)
    pred_df.to_csv(OUT_PRED, index=False)

    report = {
        "protocol": "I-DARE label variance decomposition",
        "trial_index": str(args.trial_index),
        "n": int(len(df)),
        "subjects": int(len(subjects)),
        "stimuli": int(len(stimuli)),
        "targets": TARGETS,
        "summary": summary.to_dict(orient="records"),
        "binary": binary.to_dict(orient="records"),
        "subject": subject.to_dict(orient="records"),
        "outputs": {
            "md": str(OUT_MD),
            "json": str(OUT_JSON),
            "summary_csv": str(OUT_SUMMARY),
            "binary_csv": str(OUT_BINARY),
            "subject_csv": str(OUT_SUBJECT),
            "predictions_csv": str(OUT_PRED),
        },
        "notes": [
            "In-sample stimulus/subject R2 is descriptive and not a deployable cross-subject result.",
            "LOSO stimulus-only predictions are computed using train subjects only.",
            "Subject in-sample effect can be large but is not available for unseen subjects.",
            "Residual physiological models should target the residual left after LOSO stimulus-only prediction.",
        ],
    }

    OUT_JSON.write_text(json.dumps(clean_json(report), indent=2, ensure_ascii=False), encoding="utf-8")

    summary_cols = [
        "target", "n", "subjects", "stimuli", "y_std",
        "r2_stimulus_in_sample", "r2_subject_in_sample", "r2_subject_plus_stimulus_in_sample",
        "unique_stimulus_r2_over_subject", "unique_subject_r2_over_stimulus",
        "loso_global_rmse", "loso_stimulus_rmse", "lift_stimulus_vs_global_rmse",
        "loso_stimulus_pearson", "loso_stimulus_ccc",
        "loso_stimulus_r2_vs_loso_global",
        "loso_stimulus_residual_std", "residual_std_ratio_after_loso_stimulus",
    ]

    binary_cols = [
        "target", "label_policy", "model", "binary_n",
        "accuracy", "balanced_accuracy", "macro_f1", "auroc",
        "n_low", "n_high", "true_high_rate", "pred_high_rate",
        "lift_vs_global_accuracy", "lift_vs_global_balanced_accuracy",
        "lift_vs_global_macro_f1", "lift_vs_global_auroc",
    ]

    lines = []
    lines.append("# I-DARE Label Variance Decomposition\n")
    lines.append("This report measures how much of I-DARE valence/arousal is explained by stimulus identity before adding EEG/EMG features.\n")

    lines.append("## Configuration\n")
    lines.append(f"- trial_index: `{args.trial_index}`")
    lines.append(f"- subjects: `{len(subjects)}`")
    lines.append(f"- stimuli: `{len(stimuli)}`")
    lines.append(f"- rows: `{len(df)}`")
    lines.append("- leakage control: LOSO stimulus-only predictions use train subjects only.\n")

    lines.append("## Continuous score decomposition\n")
    lines.append(md_table(summary.to_dict(orient="records"), summary_cols))

    lines.append("\n## Binary LOSO stimulus-only metrics\n")
    lines.append(md_table(binary.to_dict(orient="records"), binary_cols))

    lines.append("\n## Interpretation\n")
    lines.append(
        "- `r2_stimulus_in_sample` is descriptive: how much score variance is explainable by stimulus identity using all rows.\n"
        "- `r2_subject_in_sample` is also descriptive and is not available for an unseen subject.\n"
        "- `loso_stimulus_r2_vs_loso_global` is the more relevant cross-subject stimulus-prior number.\n"
        "- `residual_std_ratio_after_loso_stimulus` tells how much score variation remains after removing the train-subject stimulus mean.\n"
        "- A future EEG/EMG model must improve on `stimulus_only`, especially in residual metrics, not merely raw accuracy.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("\nI-DARE label variance decomposition completed.")
    print(f"wrote: {OUT_MD}")
    print(f"wrote: {OUT_JSON}")
    print(f"wrote: {OUT_SUMMARY}")
    print(f"wrote: {OUT_BINARY}")
    print(f"wrote: {OUT_SUBJECT}")
    print(f"wrote: {OUT_PRED}")

    print("\nContinuous summary:")
    print(summary[summary_cols].to_string(index=False))

    print("\nBinary summary:")
    print(binary[binary_cols].to_string(index=False))


if __name__ == "__main__":
    main()
