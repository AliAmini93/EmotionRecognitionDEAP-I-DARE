#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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
DEFAULT_OUT_PREFIX = "idare_subject_calibration_model_family_comparison_current"

TARGETS = {
    "valence": "valence_score",
    "arousal": "arousal_score",
}

LABEL_POLICIES = ["midpoint_as_low", "midpoint_as_high", "discard_midpoint"]
EPS = 1e-12


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--trial-index", type=Path, default=DEFAULT_TRIAL_INDEX)
    p.add_argument("--targets", type=str, default="valence,arousal")
    p.add_argument("--k-values", type=str, default="0,1,2,4,8,16")
    p.add_argument("--n-repeats", type=int, default=100)
    p.add_argument("--max-subjects", type=int, default=None)
    p.add_argument("--seed", type=int, default=20260529)
    p.add_argument("--out-prefix", type=str, default=DEFAULT_OUT_PREFIX)
    p.add_argument("--write-predictions", action="store_true")
    p.add_argument("--practical-lift", type=float, default=0.02)
    p.add_argument("--min-win-margin", type=int, default=3)
    return p.parse_args()


def stable_seed(*parts: Any) -> int:
    payload = "|".join(str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "little") % (2**32)


def safe_float(x: Any):
    try:
        v = float(x)
    except Exception:
        return None
    return v if math.isfinite(v) else None


def clean_json(x: Any):
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
    if pd.isna(x) if not isinstance(x, (list, tuple, dict, np.ndarray)) else False:
        return None
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
    return pearson(
        pd.Series(y).rank(method="average").to_numpy(dtype=float),
        pd.Series(p).rank(method="average").to_numpy(dtype=float),
    )


def ccc(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y, p = y[m], p[m]
    if len(y) < 2:
        return None
    my, mp = float(np.mean(y)), float(np.mean(p))
    vy, vp = float(np.var(y)), float(np.var(p))
    cov = float(np.mean((y - my) * (p - mp)))
    denom = vy + vp + (my - mp) ** 2
    if denom < EPS:
        return None
    return float(2 * cov / denom)


def regression_metrics(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    err = p - y
    return {
        "n": int(len(y)),
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


def binary_arrays(y_score, pred_score, policy):
    y_score = np.asarray(y_score, dtype=float)
    pred_score = np.asarray(pred_score, dtype=float)
    m = np.isfinite(y_score) & np.isfinite(pred_score)

    if policy == "midpoint_as_low":
        y_bin = (y_score[m] > 5.0).astype(int)
        pred_bin = (pred_score[m] > 5.0).astype(int)
    elif policy == "midpoint_as_high":
        y_bin = (y_score[m] >= 5.0).astype(int)
        pred_bin = (pred_score[m] >= 5.0).astype(int)
    elif policy == "discard_midpoint":
        m = m & (y_score != 5.0)
        y_bin = (y_score[m] > 5.0).astype(int)
        pred_bin = (pred_score[m] > 5.0).astype(int)
    else:
        raise ValueError(policy)

    return y_bin, pred_bin, pred_score[m]


def binary_metrics(y_score, pred_score, policy):
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

    return {
        "binary_n": int(len(y_bin)),
        "accuracy": safe_float(np.mean(y_bin == pred_bin)),
        "balanced_accuracy": safe_float(np.mean(recalls)),
        "macro_f1": safe_float(np.mean(f1s)),
        "auroc": auroc(y_bin, score),
        "n_low": int((y_bin == 0).sum()),
        "n_high": int((y_bin == 1).sum()),
        "true_high_rate": safe_float(np.mean(y_bin == 1)),
        "pred_high_rate": safe_float(np.mean(pred_bin == 1)),
    }


def md_cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6f}" if math.isfinite(v) else ""
    try:
        if bool(pd.isna(v)):
            return ""
    except Exception:
        pass
    return str(v).replace("|", "\\|").replace("\n", " ")


def md_table(df: pd.DataFrame, cols: list[str], max_rows: int | None = None):
    if df is None or len(df) == 0:
        return "_No rows._\n"
    view = df.copy()
    if max_rows is not None:
        view = view.head(max_rows)
    cols = [c for c in cols if c in view.columns]
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(md_cell(row.get(c)) for c in cols) + " |")
    return "\n".join(lines) + "\n"


def load_base(path: Path, max_subjects: int | None):
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
    df = df.drop_duplicates(["subject_id", "stimulus_id"]).reset_index(drop=True)

    if max_subjects is not None:
        keep = sorted(df["subject_id"].unique())[:max_subjects]
        df = df[df["subject_id"].isin(keep)].copy().reset_index(drop=True)

    return df


def train_stimulus_prior_for_subject(df: pd.DataFrame, score_col: str, test_subject: int):
    train = df[df["subject_id"].ne(test_subject)].copy()
    stim_mean = train.groupby("stimulus_id")[score_col].mean()
    global_mean = float(train[score_col].mean())

    # Training-subject residuals relative to train-subject stimulus means.
    train_res_rows = []
    for sub, sg in train.groupby("subject_id"):
        other = train[train["subject_id"].ne(sub)]
        other_stim = other.groupby("stimulus_id")[score_col].mean()
        other_global = float(other[score_col].mean())
        sp = sg["stimulus_id"].map(other_stim).astype(float).fillna(other_global).to_numpy(dtype=float)
        yy = sg[score_col].to_numpy(dtype=float)
        rr = yy - sp
        train_res_rows.append(pd.DataFrame({
            "subject_id": int(sub),
            "stimulus_id": sg["stimulus_id"].astype(str).to_numpy(),
            "residual": rr,
            "stimulus_pred": sp,
            "y_true": yy,
        }))
    train_res = pd.concat(train_res_rows, ignore_index=True)

    subject_means = train_res.groupby("subject_id")["residual"].mean()
    tau2 = float(np.var(subject_means.to_numpy(dtype=float), ddof=1)) if len(subject_means) > 1 else 0.0

    centered = train_res.merge(subject_means.rename("subject_resid_mean"), on="subject_id", how="left")
    within = centered["residual"].to_numpy(dtype=float) - centered["subject_resid_mean"].to_numpy(dtype=float)
    sigma2 = float(np.var(within, ddof=1)) if len(within) > 1 else 1.0

    return stim_mean, global_mean, tau2, sigma2


def calibrate_constant_bias(y_cal, p_cal):
    return float(np.mean(y_cal - p_cal))


def trimmed_mean(x, trim_frac=0.2):
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n == 0:
        return 0.0
    k = int(np.floor(n * trim_frac))
    if 2 * k >= n:
        return float(np.mean(x))
    return float(np.mean(x[k:n-k]))


def huber_location(x, c=1.345, max_iter=50):
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return 0.0
    mu = float(np.median(x))
    mad = float(np.median(np.abs(x - mu)))
    scale = 1.4826 * mad if mad > EPS else float(np.std(x))
    if scale < EPS:
        return mu
    for _ in range(max_iter):
        r = (x - mu) / scale
        w = np.ones_like(r)
        big = np.abs(r) > c
        w[big] = c / np.abs(r[big])
        denom = float(np.sum(w))
        if denom < EPS:
            break
        new_mu = float(np.sum(w * x) / denom)
        if abs(new_mu - mu) < 1e-10:
            mu = new_mu
            break
        mu = new_mu
    return mu


def affine_ridge_predict(y_cal, p_cal, p_eval, ridge=1.0, shrink_to_identity=True):
    y_cal = np.asarray(y_cal, dtype=float)
    p_cal = np.asarray(p_cal, dtype=float)
    p_eval = np.asarray(p_eval, dtype=float)

    if len(y_cal) < 2 or np.std(p_cal) < EPS:
        return p_eval + calibrate_constant_bias(y_cal, p_cal)

    # Fit y = a + b * p. Penalize b around 1 and a around 0 if shrink_to_identity.
    x = p_cal - float(np.mean(p_cal))
    y_center = y_cal - float(np.mean(p_cal))
    if shrink_to_identity:
        # residual formulation: y - p = a + beta * (p - mean_p)
        r = y_cal - p_cal
        beta_num = float(np.sum(x * (r - np.mean(r))))
        beta_den = float(np.sum(x * x) + ridge)
        beta = beta_num / beta_den if beta_den > EPS else 0.0
        a = float(np.mean(r))
        return p_eval + a + beta * (p_eval - float(np.mean(p_cal)))
    else:
        X = np.column_stack([np.ones(len(p_cal)), p_cal])
        A = X.T @ X + ridge * np.eye(2)
        b = X.T @ y_cal
        coef = np.linalg.solve(A, b)
        return coef[0] + coef[1] * p_eval


def kernel_residual_predict(y_cal, p_cal, p_eval, bandwidth=0.75, shrink_lambda=4.0):
    r = np.asarray(y_cal, dtype=float) - np.asarray(p_cal, dtype=float)
    p_cal = np.asarray(p_cal, dtype=float)
    p_eval = np.asarray(p_eval, dtype=float)
    if len(r) == 0:
        return p_eval
    bw = float(bandwidth)
    if bw <= 0:
        bw = 0.75
    out = []
    for pe in p_eval:
        dist = np.abs(p_cal - pe)
        w = np.exp(-0.5 * (dist / bw) ** 2)
        sw = float(np.sum(w))
        if sw < EPS:
            loc = float(np.mean(r))
            eff_n = len(r)
        else:
            loc = float(np.sum(w * r) / sw)
            eff_n = (sw * sw) / float(np.sum(w * w) + EPS)
        shrink = eff_n / (eff_n + shrink_lambda)
        out.append(pe + shrink * loc)
    return np.asarray(out, dtype=float)


def empirical_bayes_shrink_factor(k, tau2, sigma2):
    k = int(k)
    if k <= 0:
        return 0.0
    denom = tau2 + sigma2 / max(k, 1)
    if denom <= EPS:
        return 0.0
    return float(tau2 / denom)


def make_model_predictions(model: str, y_cal, p_cal, p_eval, tau2, sigma2):
    y_cal = np.asarray(y_cal, dtype=float)
    p_cal = np.asarray(p_cal, dtype=float)
    p_eval = np.asarray(p_eval, dtype=float)
    k = len(y_cal)

    if model == "stimulus_only":
        return p_eval

    residual = y_cal - p_cal
    mean_bias = float(np.mean(residual)) if k > 0 else 0.0

    if model == "bias_mean":
        return p_eval + mean_bias

    if model.startswith("bias_shrink"):
        lam = float(model.replace("bias_shrink", ""))
        shrink = k / (k + lam) if k > 0 else 0.0
        return p_eval + shrink * mean_bias

    if model == "bias_empirical_bayes":
        shrink = empirical_bayes_shrink_factor(k, tau2, sigma2)
        return p_eval + shrink * mean_bias

    if model == "bias_median":
        return p_eval + float(np.median(residual))

    if model == "bias_huber":
        return p_eval + huber_location(residual)

    if model == "bias_trimmed_mean":
        return p_eval + trimmed_mean(residual, trim_frac=0.2)

    if model == "affine_residual_ridge1":
        return affine_ridge_predict(y_cal, p_cal, p_eval, ridge=1.0, shrink_to_identity=True)

    if model == "affine_residual_ridge4":
        return affine_ridge_predict(y_cal, p_cal, p_eval, ridge=4.0, shrink_to_identity=True)

    if model == "kernel_residual_shrink4":
        return kernel_residual_predict(y_cal, p_cal, p_eval, bandwidth=0.75, shrink_lambda=4.0)

    raise ValueError(model)


MODEL_FAMILY = [
    "stimulus_only",
    "bias_mean",
    "bias_shrink1",
    "bias_shrink2",
    "bias_shrink4",
    "bias_shrink8",
    "bias_empirical_bayes",
    "bias_median",
    "bias_huber",
    "bias_trimmed_mean",
    "affine_residual_ridge1",
    "affine_residual_ridge4",
    "kernel_residual_shrink4",
]

LOCKED_BASELINE = "bias_shrink4"


def run_target(df: pd.DataFrame, target: str, score_col: str, k_values: list[int], n_repeats: int, seed: int):
    subjects = sorted(df["subject_id"].unique())
    rows = []
    fold_rows = []

    for test_subject in subjects:
        stim_mean, global_mean, tau2, sigma2 = train_stimulus_prior_for_subject(df, score_col, test_subject)
        test = df[df["subject_id"].eq(test_subject)].copy().reset_index(drop=True)
        all_stims = test["stimulus_id"].astype(str).to_numpy()
        y_all = test[score_col].to_numpy(dtype=float)
        p_all = test["stimulus_id"].map(stim_mean).astype(float).fillna(global_mean).to_numpy(dtype=float)

        for k in k_values:
            if k == 0:
                repeat_ids = [0]
            else:
                repeat_ids = list(range(n_repeats))

            if k >= len(test):
                continue

            for rep in repeat_ids:
                if k == 0:
                    cal_idx = np.array([], dtype=int)
                else:
                    rng = np.random.default_rng(stable_seed(seed, target, test_subject, k, rep))
                    cal_idx = np.sort(rng.choice(len(test), size=k, replace=False))

                eval_mask = np.ones(len(test), dtype=bool)
                eval_mask[cal_idx] = False
                eval_idx = np.where(eval_mask)[0]

                y_cal = y_all[cal_idx]
                p_cal = p_all[cal_idx]
                y_eval = y_all[eval_idx]
                p_eval = p_all[eval_idx]
                stim_eval = all_stims[eval_idx]

                for model in MODEL_FAMILY:
                    # Some models are not meaningful for k=0; keep them as stimulus_only equivalent
                    # only if model is stimulus_only, otherwise skip to avoid duplicated zero-calibration rows.
                    if k == 0 and model != "stimulus_only":
                        continue

                    pred = make_model_predictions(model, y_cal, p_cal, p_eval, tau2, sigma2)

                    fold_met = regression_metrics(y_eval, pred)
                    fold_rows.append({
                        "target": target,
                        "subject_id": int(test_subject),
                        "k_calibration": int(k),
                        "repeat": int(rep),
                        "model": model,
                        "eval_n": int(len(eval_idx)),
                        "calibration_n": int(len(cal_idx)),
                        "calibration_stimuli": ",".join(all_stims[cal_idx].tolist()),
                        "tau2_train_subject_residual": safe_float(tau2),
                        "sigma2_train_within_residual": safe_float(sigma2),
                        "fold_rmse": fold_met["rmse"],
                        "fold_mae": fold_met["mae"],
                        "fold_pearson": fold_met["pearson"],
                    })

                    for loc, idx in enumerate(eval_idx):
                        rows.append({
                            "target": target,
                            "subject_id": int(test_subject),
                            "stimulus_id": str(stim_eval[loc]),
                            "k_calibration": int(k),
                            "repeat": int(rep),
                            "model": model,
                            "y_true_score": float(y_eval[loc]),
                            "stimulus_pred_score": float(p_eval[loc]),
                            "y_pred_score": float(pred[loc]),
                            "residual_true": float(y_eval[loc] - p_eval[loc]),
                            "residual_pred": float(pred[loc] - p_eval[loc]),
                        })

    return pd.DataFrame(rows), pd.DataFrame(fold_rows)


def aggregate(pred: pd.DataFrame):
    main_rows = []
    binary_rows = []
    subject_rows = []

    group_cols = ["target", "k_calibration", "model"]
    for keys, g in pred.groupby(group_cols, dropna=False):
        target, k, model = keys
        y = g["y_true_score"].to_numpy(dtype=float)
        p = g["y_pred_score"].to_numpy(dtype=float)
        stim = g["stimulus_pred_score"].to_numpy(dtype=float)

        row = {"target": target, "k_calibration": int(k), "model": model}
        row.update(regression_metrics(y, p))
        stim_m = regression_metrics(y, stim)
        row["stimulus_rmse_reference"] = stim_m["rmse"]
        row["lift_vs_stimulus_rmse"] = safe_float(stim_m["rmse"] - row["rmse"]) if row["rmse"] is not None else None
        main_rows.append(row)

        for policy in LABEL_POLICIES:
            brow = {"target": target, "k_calibration": int(k), "model": model, "label_policy": policy}
            brow.update(binary_metrics(y, p, policy))
            binary_rows.append(brow)

    main = pd.DataFrame(main_rows)
    binary = pd.DataFrame(binary_rows)

    # locked reference per target/k = bias_shrink4 if k>0, stimulus_only if k=0
    locked_rows = []
    for _, row in main.iterrows():
        target = row["target"]
        k = int(row["k_calibration"])
        ref_model = "stimulus_only" if k == 0 else LOCKED_BASELINE
        ref = main[(main["target"].eq(target)) & (main["k_calibration"].eq(k)) & (main["model"].eq(ref_model))]
        if not ref.empty:
            ref_rmse = float(ref.iloc[0]["rmse"])
            locked_rows.append((row.name, ref_model, ref_rmse))
    for idx, ref_model, ref_rmse in locked_rows:
        main.loc[idx, "locked_reference_model"] = ref_model
        main.loc[idx, "locked_reference_rmse"] = ref_rmse
        main.loc[idx, "lift_vs_locked_reference_rmse"] = ref_rmse - float(main.loc[idx, "rmse"])

    # Subject-level metrics per target/k/model, averaged across repeats per subject.
    for keys, g in pred.groupby(["target", "k_calibration", "model", "subject_id"], dropna=False):
        target, k, model, subject_id = keys
        y = g["y_true_score"].to_numpy(dtype=float)
        p = g["y_pred_score"].to_numpy(dtype=float)
        stim = g["stimulus_pred_score"].to_numpy(dtype=float)
        met = regression_metrics(y, p)
        stim_met = regression_metrics(y, stim)
        subject_rows.append({
            "target": target,
            "k_calibration": int(k),
            "model": model,
            "subject_id": int(subject_id),
            "n": met["n"],
            "rmse": met["rmse"],
            "mae": met["mae"],
            "pearson": met["pearson"],
            "stimulus_rmse_reference": stim_met["rmse"],
            "lift_vs_stimulus_rmse": safe_float(stim_met["rmse"] - met["rmse"]),
        })

    subject = pd.DataFrame(subject_rows)

    # Subject win/loss vs locked reference at same target/k.
    win_rows = []
    if not subject.empty:
        for (target, k, model), g in subject.groupby(["target", "k_calibration", "model"], dropna=False):
            k = int(k)
            ref_model = "stimulus_only" if k == 0 else LOCKED_BASELINE
            ref = subject[
                subject["target"].eq(target)
                & subject["k_calibration"].eq(k)
                & subject["model"].eq(ref_model)
            ][["subject_id", "rmse"]].rename(columns={"rmse": "ref_rmse"})
            merged = g.merge(ref, on="subject_id", how="inner")
            if merged.empty:
                continue
            delta = merged["rmse"].to_numpy(dtype=float) - merged["ref_rmse"].to_numpy(dtype=float)
            wins = int((delta < -EPS).sum())
            losses = int((delta > EPS).sum())
            ties = int((np.abs(delta) <= EPS).sum())
            win_rows.append({
                "target": target,
                "k_calibration": k,
                "model": model,
                "locked_reference_model": ref_model,
                "subjects": int(len(merged)),
                "rmse_wins_vs_locked": wins,
                "rmse_losses_vs_locked": losses,
                "rmse_ties_vs_locked": ties,
                "rmse_win_margin_vs_locked": wins - losses,
                "mean_delta_rmse_model_minus_locked": safe_float(np.mean(delta)),
                "median_delta_rmse_model_minus_locked": safe_float(np.median(delta)),
                "worst_regression_delta_rmse": safe_float(np.max(delta)),
                "best_gain_delta_rmse": safe_float(np.min(delta)),
            })
    wins = pd.DataFrame(win_rows)

    main = main.merge(
        wins[[
            "target", "k_calibration", "model", "rmse_wins_vs_locked", "rmse_losses_vs_locked",
            "rmse_win_margin_vs_locked", "mean_delta_rmse_model_minus_locked",
            "median_delta_rmse_model_minus_locked", "worst_regression_delta_rmse", "best_gain_delta_rmse",
        ]] if not wins.empty else pd.DataFrame(columns=[
            "target", "k_calibration", "model", "rmse_wins_vs_locked", "rmse_losses_vs_locked",
            "rmse_win_margin_vs_locked", "mean_delta_rmse_model_minus_locked",
            "median_delta_rmse_model_minus_locked", "worst_regression_delta_rmse", "best_gain_delta_rmse",
        ]),
        on=["target", "k_calibration", "model"],
        how="left",
    )

    return main, binary, subject, wins


def build_verdict(main: pd.DataFrame, practical_lift: float, min_win_margin: int):
    rows = []
    candidate_models = [m for m in MODEL_FAMILY if m not in {"stimulus_only", LOCKED_BASELINE}]
    for target, tg in main.groupby("target"):
        cand = tg[tg["model"].isin(candidate_models)].copy()
        cand = cand[cand["k_calibration"].gt(0)].copy()
        if cand.empty:
            rows.append({
                "target": target,
                "decision": "NO_CANDIDATES",
                "reason": "no model-family candidates were available",
            })
            continue

        cand = cand.sort_values(["lift_vs_locked_reference_rmse", "rmse"], ascending=[False, True])
        best = cand.iloc[0]
        pooled_lift = safe_float(best["lift_vs_locked_reference_rmse"])
        win_margin = safe_float(best.get("rmse_win_margin_vs_locked"))
        mean_delta = safe_float(best.get("mean_delta_rmse_model_minus_locked"))

        reasons = []
        if pooled_lift is None or pooled_lift <= 0:
            reasons.append("no pooled RMSE lift over locked few-shot baseline")
        if pooled_lift is None or pooled_lift < practical_lift:
            reasons.append(f"pooled lift < {practical_lift}")
        if win_margin is None or win_margin < min_win_margin:
            reasons.append(f"subject win margin < {min_win_margin}")
        if mean_delta is None or mean_delta >= 0:
            reasons.append("mean subject RMSE delta is not better than locked baseline")

        if not reasons:
            decision = "GO_MODEL_FAMILY_BEATS_LOCKED_FEWSHOT"
            reason = "candidate beats locked few-shot baseline in pooled and subject-level metrics"
        elif pooled_lift is not None and pooled_lift > 0:
            decision = "WEAK_GO_MODEL_FAMILY_NEEDS_CONFIRMATION"
            reason = "; ".join(reasons)
        else:
            decision = "NO_GO_MODEL_FAMILY_OVER_LOCKED_FEWSHOT"
            reason = "; ".join(reasons)

        rows.append({
            "target": target,
            "decision": decision,
            "best_candidate_model": best["model"],
            "best_k_calibration": int(best["k_calibration"]),
            "best_rmse": safe_float(best["rmse"]),
            "locked_reference_model": best["locked_reference_model"],
            "locked_reference_rmse": safe_float(best["locked_reference_rmse"]),
            "best_lift_vs_locked_reference_rmse": pooled_lift,
            "rmse_win_margin_vs_locked": win_margin,
            "mean_delta_rmse_model_minus_locked": mean_delta,
            "reason": reason,
        })

    return pd.DataFrame(rows)


def build_failure_subjects(subject: pd.DataFrame, verdict: pd.DataFrame):
    rows = []
    for _, v in verdict.iterrows():
        target = v["target"]
        model = v.get("best_candidate_model")
        k = int(v.get("best_k_calibration", 0)) if pd.notna(v.get("best_k_calibration", np.nan)) else 0
        if not isinstance(model, str) or not model:
            continue
        ref_model = "stimulus_only" if k == 0 else LOCKED_BASELINE
        cand = subject[
            subject["target"].eq(target)
            & subject["k_calibration"].eq(k)
            & subject["model"].eq(model)
        ][["subject_id", "rmse", "lift_vs_stimulus_rmse"]].rename(columns={
            "rmse": "candidate_rmse",
            "lift_vs_stimulus_rmse": "candidate_lift_vs_stimulus_rmse",
        })
        ref = subject[
            subject["target"].eq(target)
            & subject["k_calibration"].eq(k)
            & subject["model"].eq(ref_model)
        ][["subject_id", "rmse", "lift_vs_stimulus_rmse"]].rename(columns={
            "rmse": "locked_rmse",
            "lift_vs_stimulus_rmse": "locked_lift_vs_stimulus_rmse",
        })
        merged = cand.merge(ref, on="subject_id", how="inner")
        if merged.empty:
            continue
        merged["delta_rmse_candidate_minus_locked"] = merged["candidate_rmse"] - merged["locked_rmse"]
        merged["target"] = target
        merged["best_candidate_model"] = model
        merged["k_calibration"] = k
        merged["locked_reference_model"] = ref_model
        rows.append(merged)

    if not rows:
        return pd.DataFrame()
    out = pd.concat(rows, ignore_index=True)
    return out.sort_values(["target", "delta_rmse_candidate_minus_locked"], ascending=[True, False])


def main():
    args = parse_args()
    ROCA_DIR.mkdir(parents=True, exist_ok=True)

    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    k_values = [int(x.strip()) for x in args.k_values.split(",") if x.strip()]

    df = load_base(args.trial_index, args.max_subjects)
    print("[INFO] I-DARE subject calibration model-family comparison")
    print(f"[INFO] rows={len(df)} subjects={df['subject_id'].nunique()} stimuli={df['stimulus_id'].nunique()}")
    print(f"[INFO] targets={targets}")
    print(f"[INFO] k_values={k_values} n_repeats={args.n_repeats}")

    pred_parts = []
    fold_parts = []
    for target in targets:
        if target not in TARGETS:
            raise ValueError(f"Unknown target {target}")
        print(f"[TARGET] {target}")
        pred_t, fold_t = run_target(
            df=df,
            target=target,
            score_col=TARGETS[target],
            k_values=k_values,
            n_repeats=args.n_repeats,
            seed=args.seed,
        )
        pred_parts.append(pred_t)
        fold_parts.append(fold_t)

    pred = pd.concat(pred_parts, ignore_index=True)
    fold = pd.concat(fold_parts, ignore_index=True)
    main_df, binary_df, subject_df, wins_df = aggregate(pred)
    verdict_df = build_verdict(main_df, args.practical_lift, args.min_win_margin)
    failure_df = build_failure_subjects(subject_df, verdict_df)

    best = main_df.sort_values(["target", "lift_vs_locked_reference_rmse", "rmse"], ascending=[True, False, True]).copy()

    out_prefix = args.out_prefix
    out_md = ROCA_DIR / f"{out_prefix}.md"
    out_json = ROCA_DIR / f"{out_prefix}.json"
    out_main = ROCA_DIR / f"{out_prefix}_main_metrics.csv"
    out_binary = ROCA_DIR / f"{out_prefix}_binary_metrics.csv"
    out_subject = ROCA_DIR / f"{out_prefix}_subject_metrics.csv"
    out_wins = ROCA_DIR / f"{out_prefix}_subject_winloss.csv"
    out_fold = ROCA_DIR / f"{out_prefix}_fold_summary.csv"
    out_verdict = ROCA_DIR / f"{out_prefix}_verdict.csv"
    out_best = ROCA_DIR / f"{out_prefix}_best_ranking.csv"
    out_failure = ROCA_DIR / f"{out_prefix}_failure_subjects.csv"
    out_pred = ROCA_DIR / f"{out_prefix}_predictions.csv"

    main_df.to_csv(out_main, index=False)
    binary_df.to_csv(out_binary, index=False)
    subject_df.to_csv(out_subject, index=False)
    wins_df.to_csv(out_wins, index=False)
    fold.to_csv(out_fold, index=False)
    verdict_df.to_csv(out_verdict, index=False)
    best.to_csv(out_best, index=False)
    failure_df.to_csv(out_failure, index=False)

    prediction_path = None
    if args.write_predictions:
        pred.to_csv(out_pred, index=False)
        prediction_path = str(out_pred)
    else:
        if out_pred.exists():
            out_pred.unlink()

    report = {
        "step": "05ae",
        "title": "I-DARE subject calibration model-family comparison",
        "purpose": "Compare subject personalization families against the locked 05ad few-shot baseline, not merely against stimulus-only.",
        "inputs": {
            "trial_index": str(args.trial_index),
            "targets": targets,
            "k_values": k_values,
            "n_repeats": args.n_repeats,
            "max_subjects": args.max_subjects,
            "seed": args.seed,
        },
        "locked_reference": {
            "k_0": "stimulus_only",
            "k_positive": LOCKED_BASELINE,
            "note": "Candidate model families must beat the locked shrinkage few-shot baseline at the same k.",
        },
        "model_family": MODEL_FAMILY,
        "outputs": {
            "md": str(out_md),
            "json": str(out_json),
            "main_metrics": str(out_main),
            "binary_metrics": str(out_binary),
            "subject_metrics": str(out_subject),
            "subject_winloss": str(out_wins),
            "fold_summary": str(out_fold),
            "verdict": str(out_verdict),
            "best_ranking": str(out_best),
            "failure_subjects": str(out_failure),
            "predictions": prediction_path,
        },
        "verdict": verdict_df.to_dict(orient="records"),
        "best_top20": best.head(20).to_dict(orient="records"),
    }
    out_json.write_text(json.dumps(clean_json(report), indent=2, ensure_ascii=False), encoding="utf-8")

    main_cols = [
        "target", "k_calibration", "model", "n", "rmse", "lift_vs_stimulus_rmse",
        "locked_reference_model", "locked_reference_rmse", "lift_vs_locked_reference_rmse",
        "pearson", "spearman", "ccc",
        "rmse_wins_vs_locked", "rmse_losses_vs_locked", "rmse_win_margin_vs_locked",
        "mean_delta_rmse_model_minus_locked", "worst_regression_delta_rmse", "best_gain_delta_rmse",
    ]

    verdict_cols = [
        "target", "decision", "best_candidate_model", "best_k_calibration", "best_rmse",
        "locked_reference_model", "locked_reference_rmse", "best_lift_vs_locked_reference_rmse",
        "rmse_win_margin_vs_locked", "mean_delta_rmse_model_minus_locked", "reason",
    ]

    failure_cols = [
        "target", "subject_id", "best_candidate_model", "k_calibration", "locked_reference_model",
        "candidate_rmse", "locked_rmse", "delta_rmse_candidate_minus_locked",
        "candidate_lift_vs_stimulus_rmse", "locked_lift_vs_stimulus_rmse",
    ]

    lines = []
    lines.append("# I-DARE Subject Calibration Model-Family Comparison\n")
    lines.append("This report tests whether any subject-calibration family improves over the locked 05ad few-shot baseline.\n")
    lines.append("The locked reference is `bias_shrink4` for k>0 and `stimulus_only` for k=0.\n")
    lines.append("A new model is only interesting if it beats the locked few-shot baseline at the same calibration size.\n")

    lines.append("## Verdict\n")
    lines.append(md_table(verdict_df, verdict_cols))

    lines.append("\n## Best ranking by lift over locked reference\n")
    lines.append(md_table(best, main_cols, max_rows=40))

    lines.append("\n## Worst failure subjects for best candidate\n")
    lines.append(md_table(failure_df, failure_cols, max_rows=30))

    lines.append("\n## Model family\n")
    lines.append("\n".join([f"- `{m}`" for m in MODEL_FAMILY]))
    lines.append("\n")

    lines.append("\n## Interpretation\n")
    lines.append(
        "- If `GO_MODEL_FAMILY_BEATS_LOCKED_FEWSHOT` appears, we have a calibration method worth confirming in the next step.\n"
        "- If only `WEAK_GO` appears, it means pooled gain exists but subject-level stability is not yet enough.\n"
        "- If `NO_GO` appears, the simple locked shrinkage few-shot baseline is still the strongest honest baseline.\n"
    )

    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05ae completed.")
    for p in [out_md, out_json, out_main, out_binary, out_subject, out_wins, out_fold, out_verdict, out_best, out_failure]:
        print(f"wrote: {p}")
    if prediction_path:
        print(f"wrote: {prediction_path}")
    else:
        print("[INFO] skipped predictions CSV unless --write-predictions is passed")

    print("\nVerdict:")
    print(verdict_df[verdict_cols].to_string(index=False))

    print("\nBest model-family rows:")
    print(best[main_cols].head(30).to_string(index=False))

    print("\nFailure subjects:")
    if not failure_df.empty:
        print(failure_df[failure_cols].head(20).to_string(index=False))
    else:
        print("(none)")


if __name__ == "__main__":
    main()
