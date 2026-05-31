#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import hashlib
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

EMG_FEATURE_NPY = CACHE_DIR / "idare_emg_features.npy"
EMG_FEATURE_INDEX = CACHE_DIR / "idare_emg_feature_cache_index.csv"

EMG_BSL_NPY = CACHE_DIR / "idare_emg_bsl_stats.npy"
EMG_BSL_INDEX = CACHE_DIR / "idare_emg_bsl_stats_index.csv"

EEG_BC_NPY = CACHE_DIR / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
EEG_BC_INDEX = CACHE_DIR / "idare_eeg_cache_index_baseline_corrected.csv"

TARGETS = {
    "valence": "valence_score",
    "arousal": "arousal_score",
}

DEFAULT_BLOCKS = [
    "emg_existing_22",
    "emg_bsl_stats_22",
    "eeg_entropy_complexity",
    "eeg_bandpower",
    "emg_lagged_interaction_experimental",
]

EPS = 1e-8



def stable_seed(*parts: Any) -> int:
    payload = "|".join(str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "little") % (2**32)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--targets", type=str, default="valence,arousal")
    p.add_argument("--blocks", type=str, default=",".join(DEFAULT_BLOCKS))
    p.add_argument("--k-values", type=str, default="0,1,2,4,8,16")
    p.add_argument("--n-repeats", type=int, default=100)
    p.add_argument("--seed", type=int, default=20260529)
    p.add_argument("--max-subjects", type=int, default=None)
    p.add_argument("--alphas", type=str, default="0.1,1,10,100,1000")
    p.add_argument("--shrink-lambda", type=float, default=4.0)
    p.add_argument("--out-prefix", type=str, default="idare_physiology_after_fewshot_audit_current")
    return p.parse_args()


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
    yr = pd.Series(y).rank(method="average").to_numpy(dtype=float)
    pr = pd.Series(p).rank(method="average").to_numpy(dtype=float)
    return pearson(yr, pr)


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
        "y_true_std": safe_float(np.std(y)),
        "y_pred_std": safe_float(np.std(p)),
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


def binary_metrics(y_score, pred_score, policy):
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
        "auroc": auroc(y_bin, pred_score[m]),
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
    except (TypeError, ValueError):
        pass
    return str(v).replace("|", "\\|").replace("\n", " ")


def md_table(df, cols):
    if df is None or len(df) == 0:
        return "_No rows._\n"
    rows = df[cols].to_dict(orient="records")
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(md_cell(row.get(c)) for c in cols) + " |")
    return "\n".join(lines) + "\n"


def load_base(max_subjects=None):
    if not TRIAL_INDEX.exists():
        raise FileNotFoundError(TRIAL_INDEX)

    df = pd.read_csv(TRIAL_INDEX)
    required = ["subject_id", "stimulus_id", "valence_score", "arousal_score"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"missing trial index columns: {missing}")

    df = df[required].copy()
    df["subject_id"] = df["subject_id"].astype(int)
    df["stimulus_id"] = df["stimulus_id"].astype(str)
    df = df.drop_duplicates(["subject_id", "stimulus_id"]).sort_values(
        ["subject_id", "stimulus_id"]
    ).reset_index(drop=True)

    if max_subjects is not None:
        subjects = sorted(df["subject_id"].unique())[: int(max_subjects)]
        df = df[df["subject_id"].isin(subjects)].reset_index(drop=True)

    df["base_row"] = np.arange(len(df), dtype=int)
    return df


def align_feature_index(base, index_path):
    idx = pd.read_csv(index_path)
    required = ["subject_id", "stimulus_id"]
    missing = [c for c in required if c not in idx.columns]
    if missing:
        raise KeyError(f"{index_path} missing columns: {missing}")

    idx = idx.copy()
    idx["subject_id"] = idx["subject_id"].astype(int)
    idx["stimulus_id"] = idx["stimulus_id"].astype(str)

    if "cache_row" not in idx.columns:
        idx["cache_row"] = np.arange(len(idx), dtype=int)

    merge = base[["base_row", "subject_id", "stimulus_id"]].merge(
        idx[["subject_id", "stimulus_id", "cache_row"]],
        on=["subject_id", "stimulus_id"],
        how="left",
        validate="one_to_one",
    )

    if merge["cache_row"].isna().any():
        bad = merge[merge["cache_row"].isna()].head()
        raise ValueError(f"feature index missing rows for {index_path}: {bad}")

    return merge["cache_row"].to_numpy(dtype=int)


def standardize_train_apply(x_train, x_test):
    mu = np.nanmean(x_train, axis=0)
    sigma = np.nanstd(x_train, axis=0)
    sigma = np.where(sigma < EPS, 1.0, sigma)

    x_train_z = (x_train - mu) / sigma
    x_test_z = (x_test - mu) / sigma

    x_train_z = np.nan_to_num(x_train_z, nan=0.0, posinf=0.0, neginf=0.0)
    x_test_z = np.nan_to_num(x_test_z, nan=0.0, posinf=0.0, neginf=0.0)

    return x_train_z.astype(np.float64), x_test_z.astype(np.float64)


def ridge_fit_predict(x_train, y_train, x_test, alpha):
    x_train = np.asarray(x_train, dtype=np.float64)
    x_test = np.asarray(x_test, dtype=np.float64)
    y_train = np.asarray(y_train, dtype=np.float64)

    x_train_aug = np.column_stack([np.ones(len(x_train)), x_train])
    x_test_aug = np.column_stack([np.ones(len(x_test)), x_test])

    reg = np.eye(x_train_aug.shape[1], dtype=np.float64) * float(alpha)
    reg[0, 0] = 0.0

    beta = np.linalg.solve(x_train_aug.T @ x_train_aug + reg, x_train_aug.T @ y_train)
    return x_test_aug @ beta


def load_emg_existing(base):
    x = np.load(EMG_FEATURE_NPY, mmap_mode="r")
    rows = align_feature_index(base, EMG_FEATURE_INDEX)
    return np.asarray(x[rows], dtype=np.float32), [f"emg_existing_{i:02d}" for i in range(x.shape[1])]


def load_emg_bsl(base):
    x = np.load(EMG_BSL_NPY, mmap_mode="r")
    rows = align_feature_index(base, EMG_BSL_INDEX)
    return np.asarray(x[rows], dtype=np.float32), [f"emg_bsl_{i:02d}" for i in range(x.shape[1])]


def _mean_abs_diff(x):
    return np.mean(np.abs(np.diff(x, axis=-1)), axis=-1)


def build_emg_lagged(base):
    raw_path = CACHE_DIR / "idare_raw_emg_windows_2x10000_float32.npy"
    raw_index = CACHE_DIR / "idare_raw_emg_cache_index.csv"
    if not raw_path.exists():
        raise FileNotFoundError(raw_path)
    x = np.load(raw_path, mmap_mode="r")
    rows = align_feature_index(base, raw_index)
    w = np.asarray(x[rows], dtype=np.float32)

    # 2-channel lightweight directed/lagged summaries.
    a = w[:, 0, :]
    b = w[:, 1, :]
    feats = []
    names = []
    max_lag = 50
    for lag in [1, 5, 10, 25, 50]:
        a0 = a[:, :-lag]
        b1 = b[:, lag:]
        b0 = b[:, :-lag]
        a1 = a[:, lag:]
        c_ab = np.mean(a0 * b1, axis=1)
        c_ba = np.mean(b0 * a1, axis=1)
        feats.append(c_ab - c_ba)
        names.append(f"emg_lag_direction_diff_{lag}")
    feats.append(_mean_abs_diff(a) - _mean_abs_diff(b))
    names.append("emg_madiff_channel0_minus_channel1")
    return np.column_stack(feats).astype(np.float32), names


def _bandpower_from_windows(w, fs=128.0):
    bands = [
        ("delta", 1.0, 4.0),
        ("theta", 4.0, 8.0),
        ("alpha", 8.0, 13.0),
        ("beta", 13.0, 30.0),
        ("gamma", 30.0, 45.0),
    ]
    freqs = np.fft.rfftfreq(w.shape[-1], d=1.0 / fs)
    spec = np.abs(np.fft.rfft(w, axis=-1)) ** 2
    total = np.sum(spec[:, :, (freqs >= 1.0) & (freqs <= 45.0)], axis=-1) + EPS
    feats = []
    names = []
    for name, lo, hi in bands:
        mask = (freqs >= lo) & (freqs < hi)
        bp = np.sum(spec[:, :, mask], axis=-1)
        feats.append(np.log(bp + EPS))
        feats.append(bp / total)
        names += [f"eeg_logbp_{name}_ch{i:02d}" for i in range(w.shape[1])]
        names += [f"eeg_relbp_{name}_ch{i:02d}" for i in range(w.shape[1])]

    out = np.concatenate(feats, axis=1)

    # Basic hemispheric asymmetry pairs for first 16 vs second 16 channels.
    if w.shape[1] >= 32:
        log_alpha = feats[2 * 2]  # log alpha block: delta log, delta rel, theta log, theta rel, alpha log
        log_beta = feats[3 * 2]
        asym = []
        asym_names = []
        for i in range(16):
            asym.append(log_alpha[:, i] - log_alpha[:, i + 16])
            asym_names.append(f"eeg_alpha_asym_{i:02d}_{i+16:02d}")
            asym.append(log_beta[:, i] - log_beta[:, i + 16])
            asym_names.append(f"eeg_beta_asym_{i:02d}_{i+16:02d}")
        out = np.column_stack([out, np.column_stack(asym)])
        names += asym_names

    return out.astype(np.float32), names


def _entropy_complexity_from_windows(w):
    mean = np.mean(w, axis=-1)
    std = np.std(w, axis=-1)
    diff_std = np.std(np.diff(w, axis=-1), axis=-1)
    mobility = diff_std / (std + EPS)

    centered = w - np.mean(w, axis=-1, keepdims=True)
    z = centered / (np.std(centered, axis=-1, keepdims=True) + EPS)
    p = np.mean(z > 0, axis=-1)
    binary_entropy = -(p * np.log2(p + EPS) + (1.0 - p) * np.log2(1.0 - p + EPS))

    line_length = np.mean(np.abs(np.diff(w, axis=-1)), axis=-1)

    feats = np.concatenate([mean, std, mobility, binary_entropy, line_length], axis=1)
    names = []
    for block in ["mean", "std", "hjorth_mobility", "binary_entropy", "line_length"]:
        names += [f"eeg_{block}_ch{i:02d}" for i in range(w.shape[1])]
    return feats.astype(np.float32), names


def load_eeg_windows(base):
    if not EEG_BC_NPY.exists():
        raise FileNotFoundError(EEG_BC_NPY)
    x = np.load(EEG_BC_NPY, mmap_mode="r")
    rows = align_feature_index(base, EEG_BC_INDEX)
    return np.asarray(x[rows], dtype=np.float32)


def load_block(base, block):
    if block == "emg_existing_22":
        return load_emg_existing(base)
    if block == "emg_bsl_stats_22":
        return load_emg_bsl(base)
    if block == "emg_lagged_interaction_experimental":
        return build_emg_lagged(base)
    if block == "eeg_bandpower":
        w = load_eeg_windows(base)
        return _bandpower_from_windows(w)
    if block == "eeg_entropy_complexity":
        w = load_eeg_windows(base)
        return _entropy_complexity_from_windows(w)
    raise ValueError(f"unknown block: {block}")


def stimulus_means_train(train_df, score_col):
    return train_df.groupby("stimulus_id")[score_col].mean()


def map_stimulus_pred(df, stim_mean, fallback):
    return df["stimulus_id"].map(stim_mean).astype(float).fillna(float(fallback)).to_numpy(dtype=float)


def fit_physio_for_fold(x, base, train_mask, train_base_pred, score_col, alphas):
    train_df = base.loc[train_mask].copy()
    y_train = train_df[score_col].to_numpy(dtype=float)

    # Remove train-subject residual bias, so physiology is asked to model within-subject residual after stimulus + subject calibration.
    raw_resid = y_train - train_base_pred
    subject_bias = pd.Series(raw_resid, index=train_df.index).groupby(train_df["subject_id"]).transform("mean").to_numpy(dtype=float)
    y_resid_centered = raw_resid - subject_bias

    x_train_raw = np.asarray(x[train_mask], dtype=np.float32)

    # Inner subject-level CV on training subjects for alpha.
    subjects = sorted(train_df["subject_id"].unique())
    best_alpha = float(alphas[0])
    best_score = np.inf

    for alpha in alphas:
        fold_err = []
        for val_subject in subjects:
            tr = train_df["subject_id"].ne(val_subject).to_numpy()
            va = train_df["subject_id"].eq(val_subject).to_numpy()
            if tr.sum() < 2 or va.sum() == 0:
                continue
            xtr, xva = standardize_train_apply(x_train_raw[tr], x_train_raw[va])
            pred = ridge_fit_predict(xtr, y_resid_centered[tr], xva, alpha)
            err = pred - y_resid_centered[va]
            fold_err.append(np.mean(err * err))
        if fold_err:
            rmse = float(np.sqrt(np.mean(fold_err)))
            if rmse < best_score:
                best_score = rmse
                best_alpha = float(alpha)

    x_train_z, _ = standardize_train_apply(x_train_raw, x_train_raw)
    pred_train = ridge_fit_predict(x_train_z, y_resid_centered, x_train_z, best_alpha)

    # Recompute exact standardizer for external application.
    mu = np.nanmean(x_train_raw, axis=0)
    sigma = np.nanstd(x_train_raw, axis=0)
    sigma = np.where(sigma < EPS, 1.0, sigma)

    x_train_z = np.nan_to_num((x_train_raw - mu) / sigma, nan=0.0, posinf=0.0, neginf=0.0)
    x_aug = np.column_stack([np.ones(len(x_train_z)), x_train_z])
    reg = np.eye(x_aug.shape[1], dtype=np.float64) * best_alpha
    reg[0, 0] = 0.0
    beta = np.linalg.solve(x_aug.T @ x_aug + reg, x_aug.T @ y_resid_centered)

    return {
        "alpha": best_alpha,
        "mu": mu,
        "sigma": sigma,
        "beta": beta,
    }


def apply_physio_model(model, x_raw):
    z = (np.asarray(x_raw, dtype=np.float64) - model["mu"]) / model["sigma"]
    z = np.nan_to_num(z, nan=0.0, posinf=0.0, neginf=0.0)
    aug = np.column_stack([np.ones(len(z)), z])
    return aug @ model["beta"]


def run_target_block(base, x, target, score_col, block, k_values, n_repeats, seed, alphas, shrink_lambda):
    rng_master = np.random.default_rng(seed)
    rows = []
    fold_rows = []

    subjects = sorted(base["subject_id"].unique())

    for test_subject in subjects:
        test_mask = base["subject_id"].eq(test_subject).to_numpy()
        train_mask = ~test_mask
        train_df = base.loc[train_mask].copy()
        test_df = base.loc[test_mask].copy()

        stim_mean = stimulus_means_train(train_df, score_col)
        global_mean = float(train_df[score_col].mean())

        train_stim_pred = map_stimulus_pred(train_df, stim_mean, global_mean)
        test_stim_pred = map_stimulus_pred(test_df, stim_mean, global_mean)

        physio_model = fit_physio_for_fold(x, base, train_mask, train_stim_pred, score_col, alphas)
        physio_all_test = apply_physio_model(physio_model, x[test_mask])

        y_test = test_df[score_col].to_numpy(dtype=float)
        resid_test = y_test - test_stim_pred
        n_trials = len(test_df)

        for k in k_values:
            k = int(k)
            if k <= 0:
                repeats = 1
            else:
                repeats = int(n_repeats)

            if k >= n_trials:
                continue

            for repeat in range(repeats):
                if k <= 0:
                    cal_idx = np.array([], dtype=int)
                else:
                    local_rng = np.random.default_rng(int(rng_master.integers(0, 2**32 - 1)))
                    cal_idx = np.sort(local_rng.choice(n_trials, size=k, replace=False))

                eval_mask = np.ones(n_trials, dtype=bool)
                eval_mask[cal_idx] = False
                eval_idx = np.where(eval_mask)[0]

                if len(eval_idx) == 0:
                    continue

                if k <= 0:
                    bias_raw = 0.0
                    bias_shrink = 0.0
                else:
                    bias_raw = float(np.mean(resid_test[cal_idx]))
                    bias_shrink = float(k / (k + shrink_lambda) * bias_raw)

                candidates = {
                    "stimulus_only": test_stim_pred,
                    "stimulus_plus_fewshot_bias": test_stim_pred + bias_raw,
                    f"stimulus_plus_fewshot_bias_shrink{int(shrink_lambda)}": test_stim_pred + bias_shrink,
                    "stimulus_plus_physio": test_stim_pred + physio_all_test,
                    "stimulus_plus_fewshot_bias_plus_physio": test_stim_pred + bias_raw + physio_all_test,
                    f"stimulus_plus_fewshot_bias_shrink{int(shrink_lambda)}_plus_physio": test_stim_pred + bias_shrink + physio_all_test,
                }

                for model_name, pred_all in candidates.items():
                    y_eval = y_test[eval_idx]
                    p_eval = pred_all[eval_idx]
                    base_eval = candidates["stimulus_plus_fewshot_bias_shrink4"][eval_idx] if "shrink4" in candidates else test_stim_pred[eval_idx]

                    for idx_local, yv, pv, sv, physv in zip(
                        eval_idx,
                        y_eval,
                        p_eval,
                        test_stim_pred[eval_idx],
                        physio_all_test[eval_idx],
                    ):
                        rows.append({
                            "target": target,
                            "block": block,
                            "test_subject": int(test_subject),
                            "stimulus_id": str(test_df.iloc[int(idx_local)]["stimulus_id"]),
                            "k_calibration": int(k),
                            "repeat": int(repeat),
                            "model": model_name,
                            "alpha": float(physio_model["alpha"]),
                            "y_true": float(yv),
                            "y_pred": float(pv),
                            "stimulus_pred": float(sv),
                            "physio_residual_pred": float(physv),
                            "is_physio_model": bool("physio" in model_name),
                        })

                fold_rows.append({
                    "target": target,
                    "block": block,
                    "test_subject": int(test_subject),
                    "k_calibration": int(k),
                    "repeat": int(repeat),
                    "alpha": float(physio_model["alpha"]),
                    "calibration_n": int(k),
                    "eval_n": int(len(eval_idx)),
                    "bias_raw": safe_float(bias_raw),
                    "bias_shrink": safe_float(bias_shrink),
                    "physio_pred_std_eval": safe_float(np.std(physio_all_test[eval_idx])),
                })

    return pd.DataFrame(rows), pd.DataFrame(fold_rows)


def aggregate(pred):
    main_rows = []
    binary_rows = []
    subject_rows = []
    win_rows = []

    group_cols = ["target", "block", "k_calibration", "model"]

    for keys, g in pred.groupby(group_cols, dropna=False):
        target, block, k, model = keys
        y = g["y_true"].to_numpy(dtype=float)
        p = g["y_pred"].to_numpy(dtype=float)

        row = {"target": target, "block": block, "k_calibration": int(k), "model": model}
        row.update(regression_metrics(y, p))
        main_rows.append(row)

        for policy in ["midpoint_as_low", "midpoint_as_high", "discard_midpoint"]:
            brow = {"target": target, "block": block, "k_calibration": int(k), "model": model, "label_policy": policy}
            brow.update(binary_metrics(y, p, policy))
            binary_rows.append(brow)

        # subject metrics
        for subject, sg in g.groupby("test_subject"):
            sm = {"target": target, "block": block, "k_calibration": int(k), "model": model, "test_subject": int(subject)}
            sm.update(regression_metrics(sg["y_true"].to_numpy(float), sg["y_pred"].to_numpy(float)))
            subject_rows.append(sm)

    main = pd.DataFrame(main_rows)
    binary = pd.DataFrame(binary_rows)
    subject = pd.DataFrame(subject_rows)

    # Add lifts vs fewshot shrink baseline within target/block/k.
    baseline_model = "stimulus_plus_fewshot_bias_shrink4"
    for _, mg in main.groupby(["target", "block", "k_calibration"], dropna=False):
        base = mg[mg["model"].eq(baseline_model)]
        if base.empty:
            base = mg[mg["model"].eq("stimulus_only")]
        if base.empty:
            continue
        base = base.iloc[0]
        for idx, row in mg.iterrows():
            main.loc[idx, "lift_vs_fewshot_rmse"] = safe_float(float(base["rmse"]) - float(row["rmse"]))
            main.loc[idx, "lift_vs_fewshot_mae"] = safe_float(float(base["mae"]) - float(row["mae"]))
            main.loc[idx, "lift_vs_fewshot_pearson"] = safe_float(float(row["pearson"]) - float(base["pearson"])) if pd.notna(row["pearson"]) and pd.notna(base["pearson"]) else np.nan
            main.loc[idx, "fewshot_reference_model"] = base["model"]

    for _, bg in binary.groupby(["target", "block", "k_calibration", "label_policy"], dropna=False):
        base = bg[bg["model"].eq(baseline_model)]
        if base.empty:
            base = bg[bg["model"].eq("stimulus_only")]
        if base.empty:
            continue
        base = base.iloc[0]
        for idx, row in bg.iterrows():
            for m in ["accuracy", "balanced_accuracy", "macro_f1", "auroc"]:
                if pd.notna(row[m]) and pd.notna(base[m]):
                    binary.loc[idx, f"lift_vs_fewshot_{m}"] = float(row[m]) - float(base[m])
            binary.loc[idx, "fewshot_reference_model"] = base["model"]

    # Win/loss against fewshot shrink baseline at subject level.
    for keys, sg in subject.groupby(["target", "block", "k_calibration"], dropna=False):
        target, block, k = keys
        base = sg[sg["model"].eq(baseline_model)][["test_subject", "rmse"]].rename(columns={"rmse": "base_rmse"})
        if base.empty:
            continue
        for model, mg in sg.groupby("model"):
            if model == baseline_model:
                continue
            comp = mg.merge(base, on="test_subject", how="inner")
            if comp.empty:
                continue
            delta = comp["rmse"].to_numpy(float) - comp["base_rmse"].to_numpy(float)
            win_rows.append({
                "target": target,
                "block": block,
                "k_calibration": int(k),
                "model": model,
                "subjects": int(len(delta)),
                "rmse_wins_vs_fewshot": int((delta < -EPS).sum()),
                "rmse_losses_vs_fewshot": int((delta > EPS).sum()),
                "rmse_ties_vs_fewshot": int((np.abs(delta) <= EPS).sum()),
                "rmse_win_margin_vs_fewshot": int((delta < -EPS).sum() - (delta > EPS).sum()),
                "mean_delta_rmse_model_minus_fewshot": safe_float(np.mean(delta)),
                "median_delta_rmse_model_minus_fewshot": safe_float(np.median(delta)),
                "worst_regression_delta_rmse": safe_float(np.max(delta)),
                "best_gain_delta_rmse": safe_float(np.min(delta)),
            })

    return main, binary, subject, pd.DataFrame(win_rows)


def make_verdict(main, wins):
    rows = []
    phys = main[main["model"].str.contains("physio", regex=False)].copy()
    phys = phys[phys["model"].str.contains("plus_fewshot", regex=False)].copy()

    for target, tg in phys.groupby("target"):
        candidates = tg.sort_values(["lift_vs_fewshot_rmse", "rmse"], ascending=[False, True])
        best = candidates.iloc[0] if len(candidates) else None
        if best is None:
            continue

        w = wins[
            (wins["target"].eq(best["target"])) &
            (wins["block"].eq(best["block"])) &
            (wins["k_calibration"].eq(best["k_calibration"])) &
            (wins["model"].eq(best["model"]))
        ]
        win_margin = None
        if not w.empty:
            win_margin = float(w.iloc[0]["rmse_win_margin_vs_fewshot"])

        lift = float(best.get("lift_vs_fewshot_rmse", np.nan))
        if lift >= 0.02 and win_margin is not None and win_margin > 3:
            decision = "GO_PHYSIOLOGY_ADDS_AFTER_FEWSHOT"
            reason = "physiology improves few-shot calibrated baseline in pooled and subject-level RMSE"
        elif lift > 0:
            decision = "WEAK_GO_PHYSIOLOGY_AFTER_FEWSHOT_NEEDS_CONFIRMATION"
            reason = "physiology has positive pooled lift beyond few-shot but subject-level margin or practical lift is weak"
        else:
            decision = "NO_GO_PHYSIOLOGY_AFTER_FEWSHOT"
            reason = "physiology does not improve the few-shot calibrated baseline"

        rows.append({
            "target": target,
            "decision": decision,
            "best_block": best["block"],
            "best_model": best["model"],
            "best_k_calibration": int(best["k_calibration"]),
            "best_rmse": float(best["rmse"]),
            "best_lift_vs_fewshot_rmse": lift,
            "rmse_win_margin_vs_fewshot": win_margin,
            "reason": reason,
        })

    return pd.DataFrame(rows)


def main():
    args = parse_args()
    t0 = time.time()

    ROCA_DIR.mkdir(parents=True, exist_ok=True)

    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    blocks = [b.strip() for b in args.blocks.split(",") if b.strip()]
    k_values = [int(x) for x in args.k_values.split(",") if x.strip()]
    alphas = [float(x) for x in args.alphas.split(",") if x.strip()]

    base = load_base(args.max_subjects)
    print("[INFO] I-DARE physiology-after-fewshot audit")
    print(f"[INFO] rows={len(base)} subjects={base['subject_id'].nunique()}")
    print(f"[INFO] targets={targets}")
    print(f"[INFO] blocks={blocks}")
    print(f"[INFO] k_values={k_values} n_repeats={args.n_repeats}")

    pred_parts = []
    fold_parts = []
    manifest = []

    for block in blocks:
        print("\n" + "=" * 88)
        print(f"[BLOCK] {block}")
        print("=" * 88)
        x, names = load_block(base, block)
        print(f"[BLOCK] feature_shape={x.shape}")

        manifest.append({
            "block": block,
            "shape": list(x.shape),
            "feature_dim": int(x.shape[1]),
            "feature_names_preview": names[:10],
        })

        for target in targets:
            score_col = TARGETS[target]
            print(f"  [TARGET] {target}")
            pred, fold = run_target_block(
                base=base,
                x=x,
                target=target,
                score_col=score_col,
                block=block,
                k_values=k_values,
                n_repeats=args.n_repeats,
                seed=stable_seed(args.seed, block, target),
                alphas=alphas,
                shrink_lambda=args.shrink_lambda,
            )
            pred_parts.append(pred)
            fold_parts.append(fold)

    pred = pd.concat(pred_parts, ignore_index=True)
    fold = pd.concat(fold_parts, ignore_index=True)
    main_metrics, binary, subject, wins = aggregate(pred)
    verdict = make_verdict(main_metrics, wins)

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

    # Do NOT write full predictions for full run; it can become huge.
    write_predictions = args.max_subjects is not None
    out_pred = ROCA_DIR / f"{out_prefix}_predictions.csv"

    main_metrics.to_csv(out_main, index=False)
    binary.to_csv(out_binary, index=False)
    subject.to_csv(out_subject, index=False)
    wins.to_csv(out_wins, index=False)
    fold.to_csv(out_fold, index=False)
    verdict.to_csv(out_verdict, index=False)

    if write_predictions:
        pred.to_csv(out_pred, index=False)

    phys = main_metrics[main_metrics["model"].str.contains("physio", regex=False)].copy()
    best = phys.sort_values(["target", "lift_vs_fewshot_rmse", "rmse"], ascending=[True, False, True])
    best.to_csv(out_best, index=False)

    report = {
        "purpose": "Test whether physiology adds predictive value after stimulus-only plus few-shot subject residual calibration.",
        "baseline": "stimulus_plus_fewshot_bias_shrink4",
        "no_full_predictions_written_for_full_run": not write_predictions,
        "args": vars(args),
        "feature_manifest": manifest,
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
            "predictions": str(out_pred) if write_predictions else None,
        },
        "verdict": verdict.to_dict(orient="records"),
        "runtime_seconds": time.time() - t0,
    }
    out_json.write_text(json.dumps(clean_json(report), indent=2, ensure_ascii=False), encoding="utf-8")

    cols_verdict = [
        "target", "decision", "best_block", "best_model", "best_k_calibration",
        "best_rmse", "best_lift_vs_fewshot_rmse", "rmse_win_margin_vs_fewshot", "reason",
    ]

    top_cols = [
        "target", "block", "k_calibration", "model", "n", "rmse", "lift_vs_fewshot_rmse",
        "pearson", "ccc", "fewshot_reference_model",
    ]

    lines = []
    lines.append("# I-DARE Physiology After Few-Shot Calibration Audit\n")
    lines.append("This audit tests whether EEG/EMG features add value after the subject has already been calibrated with a few labeled trials.\n")
    lines.append("Baseline reference inside each `(target, block, k)` group is `stimulus_plus_fewshot_bias_shrink4` when available.\n")
    lines.append("The full run intentionally does not write the giant predictions CSV; smoke runs with `--max-subjects` do.\n")

    lines.append("## Verdict\n")
    lines.append(md_table(verdict, cols_verdict))

    lines.append("\n## Best physiology rows by lift vs few-shot baseline\n")
    lines.append(md_table(best.head(30), [c for c in top_cols if c in best.columns]))

    lines.append("\n## Feature manifest\n")
    lines.append(md_table(pd.DataFrame(manifest), ["block", "shape", "feature_dim", "feature_names_preview"]))

    lines.append("\n## Interpretation\n")
    lines.append("- If `GO_PHYSIOLOGY_ADDS_AFTER_FEWSHOT`, physiology helps beyond subject calibration.\n")
    lines.append("- If `NO_GO_PHYSIOLOGY_AFTER_FEWSHOT`, then the useful route is personalization/calibration, not the current physiology feature set.\n")
    lines.append("- A positive pooled lift alone is not sufficient; subject-level win margin is also required.\n")

    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05ab completed.")
    for p in [out_md, out_json, out_main, out_binary, out_subject, out_wins, out_fold, out_verdict, out_best]:
        print(f"wrote: {p}")
    if write_predictions:
        print(f"wrote: {out_pred}")
    else:
        print("[INFO] skipped full predictions CSV to avoid huge file")

    print("\nVerdict:")
    print(verdict[cols_verdict].to_string(index=False))

    print("\nBest physiology rows:")
    print(best[[c for c in top_cols if c in best.columns]].head(16).to_string(index=False))


if __name__ == "__main__":
    main()
