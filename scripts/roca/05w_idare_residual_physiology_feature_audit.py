#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / ".cache"
ROCA_DIR = ROOT / "docs" / "roca"

TRIAL_INDEX = CACHE_DIR / "idare_trial_index.csv"

EEG_BC_NPY = CACHE_DIR / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
EEG_BC_INDEX = CACHE_DIR / "idare_eeg_cache_index_baseline_corrected.csv"

EMG_FEATURE_NPY = CACHE_DIR / "idare_emg_features.npy"
EMG_FEATURE_INDEX = CACHE_DIR / "idare_emg_feature_cache_index.csv"

EMG_BSL_NPY = CACHE_DIR / "idare_emg_bsl_stats.npy"
EMG_BSL_INDEX = CACHE_DIR / "idare_emg_bsl_stats_index.csv"

EMG_EXPANDED_NPY = CACHE_DIR / "roca_idare_emg_expanded_features.npy"
EMG_EXPANDED_INDEX = CACHE_DIR / "roca_idare_emg_expanded_feature_index.csv"

RAW_EMG_NPY = CACHE_DIR / "idare_raw_emg_windows_2x10000_float32.npy"
RAW_EMG_INDEX = CACHE_DIR / "idare_raw_emg_cache_index.csv"

TARGETS = {
    "valence": "valence_score",
    "arousal": "arousal_score",
}

LABEL_POLICIES = ["midpoint_as_low", "midpoint_as_high", "discard_midpoint"]
EPS = 1e-8


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--targets", default="valence,arousal")
    p.add_argument("--blocks", default="emg_existing_22,emg_bsl_stats_22,emg_expanded_812,eeg_bandpower,eeg_entropy_complexity,eeg_cov_riemannian,eeg_directed_connectivity_experimental,emg_lagged_interaction_experimental")
    p.add_argument("--max-subjects", type=int, default=0)
    p.add_argument("--alphas", default="0.1,1,10,100,1000")
    p.add_argument("--inner-val-subject-count", type=int, default=8)
    p.add_argument("--seed", type=int, default=20260515)
    p.add_argument("--out-prefix", default="idare_residual_physiology_feature_audit_current")
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
        return None if math.isfinite(v) else None
    if isinstance(x, float):
        return x if math.isfinite(x) else None
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
    return pearson(pd.Series(y).rank(method="average"), pd.Series(p).rank(method="average"))


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


def regression_metrics(df):
    y = df["y_true_score"].to_numpy(dtype=float)
    p = df["y_pred_score"].to_numpy(dtype=float)
    err = p - y
    return {
        "n": int(len(df)),
        "mae": safe_float(np.mean(np.abs(err))),
        "rmse": safe_float(np.sqrt(np.mean(err * err))),
        "pearson": pearson(y, p),
        "spearman": spearman(y, p),
        "ccc": ccc(y, p),
        "y_true_std": safe_float(np.std(y)),
        "y_pred_std": safe_float(np.std(p)),
    }


def deviation_metrics(df):
    y = df["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
    p = df["y_pred_deviation"].to_numpy(dtype=float)
    err = p - y

    sign_true = np.sign(y)
    sign_pred = np.sign(p)
    nz = sign_true != 0

    return {
        "dev_mae": safe_float(np.mean(np.abs(err))),
        "dev_rmse": safe_float(np.sqrt(np.mean(err * err))),
        "dev_pearson": pearson(y, p),
        "dev_spearman": spearman(y, p),
        "dev_sign_acc": safe_float(np.mean(sign_true[nz] == sign_pred[nz])) if int(nz.sum()) else None,
        "true_dev_std": safe_float(np.std(y)),
        "pred_dev_std": safe_float(np.std(p)),
    }


def binary_metrics(df, policy):
    y = df["y_true_score"].to_numpy(dtype=float)
    p = df["y_pred_score"].to_numpy(dtype=float)
    m = np.isfinite(y) & np.isfinite(p)

    if policy == "midpoint_as_low":
        yb = (y[m] > 5.0).astype(int)
        pb = (p[m] > 5.0).astype(int)
        score = p[m]
    elif policy == "midpoint_as_high":
        yb = (y[m] >= 5.0).astype(int)
        pb = (p[m] >= 5.0).astype(int)
        score = p[m]
    elif policy == "discard_midpoint":
        m = m & (y != 5.0)
        yb = (y[m] > 5.0).astype(int)
        pb = (p[m] > 5.0).astype(int)
        score = p[m]
    else:
        raise ValueError(policy)

    if len(yb) == 0:
        return {
            "binary_n": 0,
            "accuracy": None,
            "balanced_accuracy": None,
            "macro_f1": None,
            "auroc": None,
            "n_low": 0,
            "n_high": 0,
        }

    recalls = []
    f1s = []
    for cls in [0, 1]:
        tp = int(((yb == cls) & (pb == cls)).sum())
        fp = int(((yb != cls) & (pb == cls)).sum())
        fn = int(((yb == cls) & (pb != cls)).sum())
        support = int((yb == cls).sum())
        if support > 0:
            recalls.append(tp / support)
        denom = 2 * tp + fp + fn
        f1s.append((2 * tp / denom) if denom > 0 else 0.0)

    return {
        "binary_n": int(len(yb)),
        "accuracy": safe_float(np.mean(yb == pb)),
        "balanced_accuracy": safe_float(np.mean(recalls)),
        "macro_f1": safe_float(np.mean(f1s)),
        "auroc": auroc(yb, score),
        "n_low": int((yb == 0).sum()),
        "n_high": int((yb == 1).sum()),
    }


def md_cell(v):
    if v is None:
        return ""

    if isinstance(v, float):
        return f"{v:.4f}" if math.isfinite(v) else ""

    if isinstance(v, np.ndarray):
        v = v.tolist()

    if isinstance(v, (list, tuple)):
        items = list(v)
        if len(items) > 8:
            items = items[:8] + ["..."]
        return ("[" + ", ".join(str(x) for x in items) + "]").replace("|", "\\|").replace("\n", " ")

    try:
        if bool(pd.isna(v)):
            return ""
    except (TypeError, ValueError):
        pass

    return str(v).replace("|", "\\|").replace("\n", " ")


def md_table(rows, cols):
    if not rows:
        return "_No rows._\n"

    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")

    for row in rows:
        vals = [md_cell(row.get(col, "")) for col in cols]
        lines.append("| " + " | ".join(vals) + " |")

    return "\n".join(lines) + "\n"

def load_base():
    if not TRIAL_INDEX.exists():
        raise FileNotFoundError(TRIAL_INDEX)
    df = pd.read_csv(TRIAL_INDEX)
    needed = ["subject_id", "stimulus_id", "valence_score", "arousal_score"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"trial index missing columns: {missing}")

    df = df[needed].drop_duplicates(["subject_id", "stimulus_id"]).copy()
    df["subject_id"] = df["subject_id"].astype(int)
    df["stimulus_id"] = df["stimulus_id"].astype(str)
    df = df.sort_values(["subject_id", "stimulus_id"]).reset_index(drop=True)
    df["audit_row"] = np.arange(len(df), dtype=int)
    return df


def align_feature_cache(base, npy_path, index_path, name):
    if not npy_path.exists():
        raise FileNotFoundError(npy_path)
    if not index_path.exists():
        raise FileNotFoundError(index_path)

    x = np.load(npy_path, mmap_mode="r")
    idx = pd.read_csv(index_path)

    needed = ["cache_row", "subject_id", "stimulus_id"]
    missing = [c for c in needed if c not in idx.columns]
    if missing:
        raise KeyError(f"{name} index missing columns: {missing}")

    idx = idx[needed].copy()
    idx["cache_row"] = idx["cache_row"].astype(int)
    idx["subject_id"] = idx["subject_id"].astype(int)
    idx["stimulus_id"] = idx["stimulus_id"].astype(str)

    merged = base[["subject_id", "stimulus_id"]].merge(
        idx,
        on=["subject_id", "stimulus_id"],
        how="left",
        validate="one_to_one",
    )

    if merged["cache_row"].isna().any():
        n = int(merged["cache_row"].isna().sum())
        raise ValueError(f"{name}: failed to align {n} rows")

    rows = merged["cache_row"].to_numpy(dtype=int)
    arr = np.asarray(x[rows], dtype=np.float32)
    return arr


def sanitize_features(x):
    x = np.asarray(x, dtype=np.float32)
    if x.ndim == 1:
        x = x[:, None]
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    return x.astype(np.float32, copy=False)


def spectral_entropy_from_power(power):
    power = np.asarray(power, dtype=float)
    s = power.sum(axis=-1, keepdims=True)
    p = power / np.maximum(s, EPS)
    h = -(p * np.log(np.maximum(p, EPS))).sum(axis=-1)
    h = h / np.log(max(power.shape[-1], 2))
    return h


def hjorth_features(x, axis=-1):
    x = np.asarray(x, dtype=np.float32)
    dx = np.diff(x, axis=axis)
    ddx = np.diff(dx, axis=axis)

    var0 = np.var(x, axis=axis) + EPS
    var1 = np.var(dx, axis=axis) + EPS
    var2 = np.var(ddx, axis=axis) + EPS

    mobility = np.sqrt(var1 / var0)
    complexity = np.sqrt(var2 / var1) / np.maximum(mobility, EPS)
    return var0, mobility, complexity


def build_eeg_bandpower(base):
    x = align_feature_cache(base, EEG_BC_NPY, EEG_BC_INDEX, "eeg_bc")
    fs = 128.0
    freqs = np.fft.rfftfreq(x.shape[-1], d=1.0 / fs)
    fft = np.fft.rfft(x, axis=-1)
    psd = (np.abs(fft) ** 2).astype(np.float32)

    bands = {
        "delta": (1.0, 4.0),
        "theta": (4.0, 8.0),
        "alpha": (8.0, 13.0),
        "beta": (13.0, 30.0),
        "gamma": (30.0, 45.0),
    }

    feats = []
    names = []
    total = psd[:, :, (freqs >= 1.0) & (freqs <= 45.0)].sum(axis=-1) + EPS

    for bname, (lo, hi) in bands.items():
        m = (freqs >= lo) & (freqs < hi)
        bp = psd[:, :, m].sum(axis=-1)
        log_bp = np.log(bp + EPS)
        rel_bp = bp / total

        feats.append(log_bp)
        names.extend([f"eeg_{bname}_logpower_ch{c:02d}" for c in range(x.shape[1])])

        feats.append(rel_bp)
        names.extend([f"eeg_{bname}_relpower_ch{c:02d}" for c in range(x.shape[1])])

        feats.append(log_bp.mean(axis=1, keepdims=True))
        names.append(f"eeg_{bname}_logpower_channel_mean")

        feats.append(log_bp.std(axis=1, keepdims=True))
        names.append(f"eeg_{bname}_logpower_channel_std")

    out = np.concatenate(feats, axis=1)
    return sanitize_features(out), names


def build_eeg_entropy_complexity(base):
    x = align_feature_cache(base, EEG_BC_NPY, EEG_BC_INDEX, "eeg_bc")
    fs = 128.0
    freqs = np.fft.rfftfreq(x.shape[-1], d=1.0 / fs)
    fft = np.fft.rfft(x, axis=-1)
    psd = np.abs(fft) ** 2
    m = (freqs >= 1.0) & (freqs <= 45.0)

    var0, mobility, complexity = hjorth_features(x, axis=-1)
    line_length = np.mean(np.abs(np.diff(x, axis=-1)), axis=-1)
    zc = np.mean(np.diff(np.signbit(x), axis=-1) != 0, axis=-1)
    sent = spectral_entropy_from_power(psd[:, :, m])

    feats = [np.log(var0 + EPS), mobility, complexity, line_length, zc, sent]
    names = []
    base_names = ["log_activity", "hjorth_mobility", "hjorth_complexity", "line_length", "zero_cross_rate", "spectral_entropy"]
    for bn in base_names:
        names.extend([f"eeg_{bn}_ch{c:02d}" for c in range(x.shape[1])])

    out = np.concatenate(feats, axis=1)
    return sanitize_features(out), names


def build_eeg_cov_riemannian(base):
    x = align_feature_cache(base, EEG_BC_NPY, EEG_BC_INDEX, "eeg_bc")
    n, c, _ = x.shape
    iu = np.triu_indices(c)
    feats = []

    for i in range(n):
        xi = x[i].astype(np.float64)
        xi = xi - xi.mean(axis=1, keepdims=True)
        xi = xi / (xi.std(axis=1, keepdims=True) + EPS)
        cov = np.cov(xi)
        cov = cov + np.eye(c) * 1e-4
        vals = np.linalg.eigvalsh(cov)
        feats.append(np.concatenate([cov[iu], np.log(np.maximum(vals, EPS))]))

    names = [f"eeg_cov_ch{i:02d}_ch{j:02d}" for i, j in zip(iu[0], iu[1])]
    names += [f"eeg_cov_logeig_{i:02d}" for i in range(c)]

    return sanitize_features(np.asarray(feats, dtype=np.float32)), names


def build_eeg_directed_connectivity_experimental(base):
    x = align_feature_cache(base, EEG_BC_NPY, EEG_BC_INDEX, "eeg_bc")
    # Experimental only: contiguous pseudo-ROI groups because montage labels are not enforced here.
    n, c, t = x.shape
    roi_count = 8
    group_size = c // roi_count
    roi = []
    for r in range(roi_count):
        roi.append(x[:, r * group_size:(r + 1) * group_size, :].mean(axis=1))
    r = np.stack(roi, axis=1)  # [N, R, T]

    r = r - r.mean(axis=-1, keepdims=True)
    r = r / (r.std(axis=-1, keepdims=True) + EPS)

    lags = [1, 2, 4, 8, 16]
    feats = []
    names = []

    for lag in lags:
        block = []
        for i in range(roi_count):
            for j in range(roi_count):
                if i == j:
                    continue
                src = r[:, i, :-lag]
                dst = r[:, j, lag:]
                val = np.mean(src * dst, axis=-1)
                block.append(val[:, None])
                names.append(f"eeg_directed_lagcorr_roi{i}_to_roi{j}_lag{lag}")
        feats.append(np.concatenate(block, axis=1))

    out = np.concatenate(feats, axis=1)
    return sanitize_features(out), names


def build_emg_lagged_interaction_experimental(base):
    x = align_feature_cache(base, RAW_EMG_NPY, RAW_EMG_INDEX, "raw_emg")
    if x.ndim != 3 or x.shape[1] != 2:
        raise ValueError(f"expected raw EMG [N,2,T], got {x.shape}")

    n, _, t = x.shape
    # downsample envelope into 200 bins for robust lag summaries
    bins = 200
    step = t // bins
    xs = x[:, :, :bins * step].reshape(n, 2, bins, step)
    env = np.mean(np.abs(xs), axis=-1)
    env = env - env.mean(axis=-1, keepdims=True)
    env = env / (env.std(axis=-1, keepdims=True) + EPS)

    ch0 = env[:, 0, :]
    ch1 = env[:, 1, :]

    lags = np.arange(-25, 26)
    corr_by_lag = []
    for lag in lags:
        if lag < 0:
            a = ch0[:, -lag:]
            b = ch1[:, :lag]
        elif lag > 0:
            a = ch0[:, :-lag]
            b = ch1[:, lag:]
        else:
            a = ch0
            b = ch1
        corr_by_lag.append(np.mean(a * b, axis=1))
    corr_by_lag = np.stack(corr_by_lag, axis=1)

    max_idx = np.argmax(corr_by_lag, axis=1)
    max_corr = corr_by_lag[np.arange(n), max_idx]
    lag_at_max = lags[max_idx].astype(float) / 25.0
    zero_corr = corr_by_lag[:, np.where(lags == 0)[0][0]]

    pos_max = corr_by_lag[:, lags > 0].max(axis=1)
    neg_max = corr_by_lag[:, lags < 0].max(axis=1)
    lead_lag_asym = pos_max - neg_max

    raw0 = x[:, 0, :]
    raw1 = x[:, 1, :]
    thr0 = np.quantile(np.abs(raw0), 0.75, axis=1, keepdims=True)
    thr1 = np.quantile(np.abs(raw1), 0.75, axis=1, keepdims=True)
    burst0 = np.abs(raw0) > thr0
    burst1 = np.abs(raw1) > thr1
    coact = np.mean(burst0 & burst1, axis=1)
    xoract = np.mean(burst0 ^ burst1, axis=1)

    out = np.stack([zero_corr, max_corr, lag_at_max, lead_lag_asym, coact, xoract], axis=1)
    names = [
        "emg_env_corr_lag0",
        "emg_env_corr_max",
        "emg_env_corr_lag_at_max_scaled",
        "emg_env_lead_lag_asym",
        "emg_burst_coactivation_fraction",
        "emg_burst_xor_fraction",
    ]
    return sanitize_features(out), names


def build_simple_cache_block(base, npy, index, name):
    x = align_feature_cache(base, npy, index, name)
    if x.ndim > 2:
        x = x.reshape(x.shape[0], -1)
    names = [f"{name}_f{i:04d}" for i in range(x.shape[1])]
    return sanitize_features(x), names


def build_feature_block(base, block):
    if block == "emg_existing_22":
        return build_simple_cache_block(base, EMG_FEATURE_NPY, EMG_FEATURE_INDEX, block)
    if block == "emg_bsl_stats_22":
        return build_simple_cache_block(base, EMG_BSL_NPY, EMG_BSL_INDEX, block)
    if block == "emg_expanded_812":
        return build_simple_cache_block(base, EMG_EXPANDED_NPY, EMG_EXPANDED_INDEX, block)
    if block == "eeg_bandpower":
        return build_eeg_bandpower(base)
    if block == "eeg_entropy_complexity":
        return build_eeg_entropy_complexity(base)
    if block == "eeg_cov_riemannian":
        return build_eeg_cov_riemannian(base)
    if block == "eeg_directed_connectivity_experimental":
        return build_eeg_directed_connectivity_experimental(base)
    if block == "emg_lagged_interaction_experimental":
        return build_emg_lagged_interaction_experimental(base)
    raise ValueError(f"Unknown block: {block}")


def loo_train_deviation(df, score_col):
    g = df.groupby("stimulus_id")[score_col].agg(["sum", "count"])
    sums = df["stimulus_id"].map(g["sum"]).to_numpy(dtype=float)
    counts = df["stimulus_id"].map(g["count"]).to_numpy(dtype=float)
    y = df[score_col].to_numpy(dtype=float)
    means = (sums - y) / np.maximum(counts - 1.0, 1.0)
    return y - means


def heldout_deviation(eval_df, train_df, score_col):
    means = train_df.groupby("stimulus_id")[score_col].mean()
    baseline = eval_df["stimulus_id"].map(means).astype(float).to_numpy(dtype=float)
    y = eval_df[score_col].to_numpy(dtype=float)
    return y - baseline, baseline


def standardize_train_apply(x_train, x_other):
    mu = x_train.mean(axis=0, keepdims=True)
    sd = x_train.std(axis=0, keepdims=True)
    sd = np.where(sd < EPS, 1.0, sd)
    xt = (x_train - mu) / sd
    xo = (x_other - mu) / sd
    return sanitize_features(xt), sanitize_features(xo), mu, sd


def fit_ridge(x, y, alpha):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    xb = np.concatenate([np.ones((x.shape[0], 1)), x], axis=1)
    reg = np.eye(xb.shape[1]) * float(alpha)
    reg[0, 0] = 0.0
    w = np.linalg.solve(xb.T @ xb + reg, xb.T @ y)
    return w


def predict_ridge(x, w):
    x = np.asarray(x, dtype=np.float64)
    xb = np.concatenate([np.ones((x.shape[0], 1)), x], axis=1)
    return xb @ w


def split_inner_subjects(train_subjects, test_subject, val_count, seed):
    train_subjects = np.asarray(sorted([int(s) for s in train_subjects]), dtype=int)
    rng = np.random.default_rng(seed + int(test_subject) * 17)
    shuffled = train_subjects.copy()
    rng.shuffle(shuffled)
    val_count = int(min(max(1, val_count), max(1, len(shuffled) - 1)))
    val = set(shuffled[:val_count].tolist())
    fit = [s for s in train_subjects.tolist() if s not in val]
    return sorted(fit), sorted(val)


def select_alpha(x, df, target, score_col, outer_train_subjects, test_subject, alphas, val_count, seed):
    fit_subjects, val_subjects = split_inner_subjects(outer_train_subjects, test_subject, val_count, seed)

    fit_df = df[df["subject_id"].isin(fit_subjects)].copy()
    val_df = df[df["subject_id"].isin(val_subjects)].copy()

    fit_rows = fit_df["audit_row"].to_numpy(dtype=int)
    val_rows = val_df["audit_row"].to_numpy(dtype=int)

    x_fit, x_val, _, _ = standardize_train_apply(x[fit_rows], x[val_rows])
    y_fit = loo_train_deviation(fit_df, score_col)
    y_val, _ = heldout_deviation(val_df, fit_df, score_col)

    best_alpha = None
    best_rmse = None

    for alpha in alphas:
        try:
            w = fit_ridge(x_fit, y_fit, alpha)
            pred = predict_ridge(x_val, w)
            rmse = float(np.sqrt(np.mean((pred - y_val) ** 2)))
        except Exception:
            continue

        if best_rmse is None or rmse < best_rmse:
            best_rmse = rmse
            best_alpha = float(alpha)

    if best_alpha is None:
        best_alpha = float(alphas[0])
        best_rmse = None

    return best_alpha, safe_float(best_rmse)


def add_lifts(main):
    out_rows = []
    lower = {"mae", "rmse", "dev_mae", "dev_rmse"}
    metrics = [
        "mae", "rmse", "pearson", "spearman", "ccc",
        "dev_mae", "dev_rmse", "dev_pearson", "dev_spearman", "dev_sign_acc",
        "pred_dev_std",
    ]

    for _, g in main.groupby(["target"], dropna=False):
        base = g[g["model"].eq("stimulus_only")]
        if base.empty:
            continue
        base = base.iloc[0]

        for _, row in g.iterrows():
            r = row.to_dict()
            for m in metrics:
                rv = row.get(m)
                bv = base.get(m)
                if pd.isna(rv) or pd.isna(bv):
                    r[f"lift_vs_stimulus_{m}"] = None
                elif m in lower:
                    r[f"lift_vs_stimulus_{m}"] = safe_float(float(bv) - float(rv))
                else:
                    r[f"lift_vs_stimulus_{m}"] = safe_float(float(rv) - float(bv))
            out_rows.append(r)

    return pd.DataFrame(out_rows)


def aggregate(pred):
    main_rows = []
    binary_rows = []
    subject_rows = []

    for (target, model), g in pred.groupby(["target", "model"]):
        row = {"target": target, "model": model}
        row.update(regression_metrics(g))
        row.update(deviation_metrics(g))
        main_rows.append(row)

        for policy in LABEL_POLICIES:
            brow = {"target": target, "model": model, "label_policy": policy}
            brow.update(binary_metrics(g, policy))
            binary_rows.append(brow)

    for (target, model, sid), g in pred.groupby(["target", "model", "test_subject"]):
        row = {"target": target, "model": model, "test_subject": int(sid)}
        row.update(regression_metrics(g))
        row.update(deviation_metrics(g))
        subject_rows.append(row)

    main = add_lifts(pd.DataFrame(main_rows))
    binary = pd.DataFrame(binary_rows)
    subject = pd.DataFrame(subject_rows)

    # subject-level win/loss against stimulus-only
    win_rows = []
    for (target, model), g in subject.groupby(["target", "model"]):
        if model == "stimulus_only":
            continue
        base = subject[(subject["target"].eq(target)) & (subject["model"].eq("stimulus_only"))]
        merged = g.merge(base[["test_subject", "rmse", "dev_rmse"]], on="test_subject", suffixes=("", "_stimulus"))
        if merged.empty:
            continue
        delta = merged["rmse"] - merged["rmse_stimulus"]
        dev_delta = merged["dev_rmse"] - merged["dev_rmse_stimulus"]
        win_rows.append({
            "target": target,
            "model": model,
            "subjects": int(len(merged)),
            "rmse_wins": int((delta < 0).sum()),
            "rmse_losses": int((delta > 0).sum()),
            "rmse_ties": int((delta == 0).sum()),
            "mean_delta_rmse_model_minus_stimulus": safe_float(delta.mean()),
            "median_delta_rmse_model_minus_stimulus": safe_float(delta.median()),
            "worst_regression_delta_rmse": safe_float(delta.max()),
            "best_gain_delta_rmse": safe_float(delta.min()),
            "dev_rmse_wins": int((dev_delta < 0).sum()),
            "dev_rmse_losses": int((dev_delta > 0).sum()),
        })

    wins = pd.DataFrame(win_rows)
    return main, binary, subject, wins


def run_block(base, x, block, targets, subjects, alphas, args):
    pred_rows = []
    fold_rows = []

    for target in targets:
        score_col = TARGETS[target]
        print(f"  [TARGET] {target}")

        for fold_i, test_subject in enumerate(subjects, start=1):
            outer_train_subjects = [s for s in subjects if s != test_subject]
            train_df = base[base["subject_id"].isin(outer_train_subjects)].copy()
            test_df = base[base["subject_id"].eq(test_subject)].copy()

            train_rows = train_df["audit_row"].to_numpy(dtype=int)
            test_rows = test_df["audit_row"].to_numpy(dtype=int)

            true_dev, train_stim_mean = heldout_deviation(test_df, train_df, score_col)
            true_score = test_df[score_col].to_numpy(dtype=float)

            stim_pred = test_df[["subject_id", "stimulus_id"]].rename(columns={"subject_id": "test_subject"}).copy()
            stim_pred["target"] = target
            stim_pred["feature_block"] = "none"
            stim_pred["model"] = "stimulus_only"
            stim_pred["y_true_score"] = true_score
            stim_pred["train_stimulus_mean"] = train_stim_mean
            stim_pred["true_deviation_from_train_stimulus_mean"] = true_dev
            stim_pred["y_pred_deviation"] = 0.0
            stim_pred["y_pred_score"] = train_stim_mean
            pred_rows.append(stim_pred)

            best_alpha, inner_rmse = select_alpha(
                x=x,
                df=base,
                target=target,
                score_col=score_col,
                outer_train_subjects=outer_train_subjects,
                test_subject=test_subject,
                alphas=alphas,
                val_count=args.inner_val_subject_count,
                seed=args.seed,
            )

            x_train, x_test, _, _ = standardize_train_apply(x[train_rows], x[test_rows])
            y_train = loo_train_deviation(train_df, score_col)

            w = fit_ridge(x_train, y_train, best_alpha)
            pred_dev = predict_ridge(x_test, w)
            pred_score = train_stim_mean + pred_dev

            model_name = f"physio_{block}_ridge"

            fpred = test_df[["subject_id", "stimulus_id"]].rename(columns={"subject_id": "test_subject"}).copy()
            fpred["target"] = target
            fpred["feature_block"] = block
            fpred["model"] = model_name
            fpred["y_true_score"] = true_score
            fpred["train_stimulus_mean"] = train_stim_mean
            fpred["true_deviation_from_train_stimulus_mean"] = true_dev
            fpred["y_pred_deviation"] = pred_dev
            fpred["y_pred_score"] = np.clip(pred_score, 1.0, 9.0)
            pred_rows.append(fpred)

            frow = {
                "target": target,
                "feature_block": block,
                "test_subject": int(test_subject),
                "selected_alpha": best_alpha,
                "inner_val_dev_rmse": inner_rmse,
                "train_n": int(len(train_df)),
                "test_n": int(len(test_df)),
            }
            fold_rows.append(frow)

    return pd.concat(pred_rows, ignore_index=True), pd.DataFrame(fold_rows)


def main():
    args = parse_args()
    t0 = time.perf_counter()
    ROCA_DIR.mkdir(parents=True, exist_ok=True)

    requested_targets = [x.strip() for x in args.targets.split(",") if x.strip()]
    requested_blocks = [x.strip() for x in args.blocks.split(",") if x.strip()]
    alphas = [float(x.strip()) for x in args.alphas.split(",") if x.strip()]

    base = load_base()
    subjects = sorted(base["subject_id"].unique().tolist())
    if args.max_subjects and args.max_subjects > 0:
        subjects = subjects[:args.max_subjects]
        base = base[base["subject_id"].isin(subjects)].copy().reset_index(drop=True)
        base["audit_row"] = np.arange(len(base), dtype=int)

    print("[INFO] I-DARE residual physiology feature audit")
    print(f"[INFO] rows={len(base)} subjects={len(subjects)}")
    print(f"[INFO] targets={requested_targets}")
    print(f"[INFO] blocks={requested_blocks}")
    print(f"[INFO] alphas={alphas}")

    all_pred = []
    all_fold = []
    feature_manifest = []

    for block in requested_blocks:
        print("\n" + "=" * 88)
        print(f"[BLOCK] {block}")
        print("=" * 88)

        x, names = build_feature_block(base, block)
        print(f"[BLOCK] feature_shape={x.shape}")

        feature_manifest.append({
            "block": block,
            "shape": list(x.shape),
            "feature_dim": int(x.shape[1]),
            "feature_names_preview": names[:20],
        })

        pred, fold = run_block(base, x, block, requested_targets, subjects, alphas, args)
        all_pred.append(pred)
        all_fold.append(fold)

    pred = pd.concat(all_pred, ignore_index=True)
    fold = pd.concat(all_fold, ignore_index=True)

    # Remove duplicated stimulus-only rows across blocks.
    stim = pred[pred["model"].eq("stimulus_only")].drop_duplicates(
        ["target", "test_subject", "stimulus_id", "model"]
    )
    models = pred[~pred["model"].eq("stimulus_only")]
    pred = pd.concat([stim, models], ignore_index=True)

    main, binary, subject, wins = aggregate(pred)

    out_prefix = args.out_prefix
    out_md = ROCA_DIR / f"{out_prefix}.md"
    out_json = ROCA_DIR / f"{out_prefix}.json"
    out_pred = ROCA_DIR / f"{out_prefix}_predictions.csv"
    out_main = ROCA_DIR / f"{out_prefix}_main_metrics.csv"
    out_binary = ROCA_DIR / f"{out_prefix}_binary_metrics.csv"
    out_subject = ROCA_DIR / f"{out_prefix}_subject_metrics.csv"
    out_wins = ROCA_DIR / f"{out_prefix}_subject_winloss.csv"
    out_fold = ROCA_DIR / f"{out_prefix}_fold_summary.csv"

    pred.to_csv(out_pred, index=False)
    main.to_csv(out_main, index=False)
    binary.to_csv(out_binary, index=False)
    subject.to_csv(out_subject, index=False)
    wins.to_csv(out_wins, index=False)
    fold.to_csv(out_fold, index=False)

    report = {
        "protocol": "I-DARE residual physiology feature audit",
        "targets": requested_targets,
        "blocks": requested_blocks,
        "alphas": alphas,
        "max_subjects": args.max_subjects,
        "subjects": subjects,
        "feature_manifest": feature_manifest,
        "leakage_control": [
            "Outer evaluation is leave-one-subject-out.",
            "Stimulus-only baseline for test subject uses train-subject mean of same stimulus.",
            "Physiology models predict residual over train-subject stimulus mean.",
            "Training residuals use leave-one-row-out same-stimulus means inside outer train.",
            "Alpha is selected by inner validation subjects only; held-out subject is not used for tuning.",
        ],
        "outputs": {
            "md": str(out_md),
            "json": str(out_json),
            "predictions": str(out_pred),
            "main_metrics": str(out_main),
            "binary_metrics": str(out_binary),
            "subject_metrics": str(out_subject),
            "subject_winloss": str(out_wins),
            "fold_summary": str(out_fold),
        },
        "elapsed_sec": safe_float(time.perf_counter() - t0),
        "main_metrics": main.to_dict(orient="records"),
        "subject_winloss": wins.to_dict(orient="records"),
    }

    out_json.write_text(json.dumps(clean_json(report), indent=2, ensure_ascii=False), encoding="utf-8")

    main_cols = [
        "target", "model", "n",
        "mae", "rmse", "pearson", "spearman", "ccc",
        "dev_rmse", "dev_pearson", "dev_sign_acc",
        "true_dev_std", "pred_dev_std",
        "lift_vs_stimulus_rmse",
        "lift_vs_stimulus_dev_rmse",
        "lift_vs_stimulus_dev_pearson",
        "lift_vs_stimulus_pred_dev_std",
    ]

    win_cols = [
        "target", "model", "subjects",
        "rmse_wins", "rmse_losses",
        "mean_delta_rmse_model_minus_stimulus",
        "median_delta_rmse_model_minus_stimulus",
        "worst_regression_delta_rmse",
        "best_gain_delta_rmse",
        "dev_rmse_wins", "dev_rmse_losses",
    ]

    lines = []
    lines.append("# I-DARE Residual Physiology Feature Audit\n")
    lines.append("This audit asks whether EEG/EMG feature blocks add cross-subject residual value beyond stimulus-only prior.\n")
    lines.append("## Leakage control\n")
    lines.append("- Outer protocol: leave-one-subject-out.")
    lines.append("- Test-subject stimulus prior is computed from train subjects only.")
    lines.append("- Physiological models predict residual/deviation over train-subject stimulus mean.")
    lines.append("- Ridge alpha is selected using inner validation subjects only.\n")

    lines.append("## Feature blocks\n")
    lines.append(md_table(feature_manifest, ["block", "shape", "feature_dim", "feature_names_preview"]))

    lines.append("\n## Main metrics\n")
    lines.append(md_table(main.to_dict(orient="records"), main_cols))

    lines.append("\n## Subject win/loss vs stimulus-only\n")
    lines.append(md_table(wins.to_dict(orient="records"), win_cols))

    lines.append("\n## Interpretation\n")
    lines.append(
        "- Positive `lift_vs_stimulus_rmse` means the physiological block reduced score RMSE beyond stimulus-only.\n"
        "- Positive `lift_vs_stimulus_dev_rmse` means the block improved residual/deviation RMSE.\n"
        "- `dev_pearson` is central: it tests whether the block tracks subject-specific residual variation.\n"
        "- Experimental directed/lagged features are not causal claims; they are exploratory directed-dynamics summaries.\n"
    )

    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05w completed.")
    for p in [out_md, out_json, out_main, out_binary, out_subject, out_wins, out_fold, out_pred]:
        print(f"wrote: {p}")

    print("\nMain metrics:")
    print(main[main_cols].to_string(index=False))

    print("\nSubject win/loss:")
    print(wins[win_cols].to_string(index=False))


if __name__ == "__main__":
    main()
