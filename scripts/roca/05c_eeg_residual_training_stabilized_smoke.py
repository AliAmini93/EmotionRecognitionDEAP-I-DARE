#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
CACHE_DIR = ROOT / ".cache"
ROCA_DIR = ROOT / "docs" / "roca"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from emotion_deap_idare.models.eeg_segment_classifier import EEGSegmentClassifier


BC_EEG_NPY = CACHE_DIR / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
BC_EEG_INDEX = CACHE_DIR / "idare_eeg_cache_index_baseline_corrected.csv"
RAW_EEG_NPY = CACHE_DIR / "idare_eeg_windows_32x640_float32.npy"
RAW_EEG_INDEX = CACHE_DIR / "idare_eeg_cache_index.csv"

TRIAL_INDEX = CACHE_DIR / "idare_trial_index.csv"
STIMULUS_ONLY_PRED = ROCA_DIR / "stimulus_only_predictions_current.csv"
FOLD_SAFE_SELECTED = ROCA_DIR / "fold_safe_selected_stimuli_current.csv"

OUT_MD = ROCA_DIR / "eeg_residual_training_stabilized_smoke_current.md"
OUT_JSON = ROCA_DIR / "eeg_residual_training_stabilized_smoke_current.json"
OUT_PRED_CSV = ROCA_DIR / "eeg_residual_training_stabilized_smoke_predictions_current.csv"
OUT_MAIN_CSV = ROCA_DIR / "eeg_residual_training_stabilized_smoke_main_metrics_current.csv"
OUT_SUBSET_CSV = ROCA_DIR / "eeg_residual_training_stabilized_smoke_subset_metrics_current.csv"
OUT_FOLD_CSV = ROCA_DIR / "eeg_residual_training_stabilized_smoke_fold_summary_current.csv"
OUT_HISTORY_CSV = ROCA_DIR / "eeg_residual_training_stabilized_smoke_history_current.csv"

TARGET_COLUMNS = {
    "valence": "valence_score",
    "arousal": "arousal_score",
}

MODEL_NAME = "eeg_bc_residual_huber_norm_stabilized_smoke"
EPS = 1e-8


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--target", choices=["valence", "arousal"], default="arousal")
    p.add_argument("--cache", choices=["baseline_corrected", "raw"], default="baseline_corrected")
    p.add_argument("--max-folds", type=int, default=6)
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--patience", type=int, default=8)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--weight-decay", type=float, default=1e-3)
    p.add_argument("--huber-delta", type=float, default=1.0)
    p.add_argument("--val-subject-count", type=int, default=8)
    p.add_argument("--seed", type=int, default=20260513)
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--dropout", type=float, default=0.1)
    p.add_argument("--head-dropout", type=float, default=0.3)
    return p.parse_args()


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


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


def spearman(y, p):
    yr = pd.Series(y).rank(method="average").to_numpy()
    pr = pd.Series(p).rank(method="average").to_numpy()
    return pearson(yr, pr)


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
        "dev_mae": safe_float(np.mean(np.abs(err))),
        "dev_rmse": safe_float(np.sqrt(np.mean(err * err))),
        "dev_pearson": pearson(true_dev, pred_dev),
        "dev_spearman": spearman(true_dev, pred_dev),
        "dev_sign_acc": safe_float(np.mean(sign_true[nz] == sign_pred[nz])) if nz.sum() else None,
        "true_dev_mean": safe_float(np.mean(true_dev)),
        "true_dev_std": safe_float(np.std(true_dev)),
        "pred_dev_mean": safe_float(np.mean(pred_dev)),
        "pred_dev_std": safe_float(np.std(pred_dev)),
    }


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


class EEGResidualDataset(Dataset):
    def __init__(self, x: np.ndarray, y_scaled: np.ndarray):
        self.x = np.asarray(x, dtype=np.float32)
        self.y = np.asarray(y_scaled, dtype=np.float32)

    def __len__(self):
        return int(len(self.y))

    def __getitem__(self, idx):
        return torch.from_numpy(self.x[idx]), torch.tensor(self.y[idx], dtype=torch.float32)


def choose_cache(cache_name: str):
    if cache_name == "baseline_corrected":
        return BC_EEG_NPY, BC_EEG_INDEX
    return RAW_EEG_NPY, RAW_EEG_INDEX


def load_inputs(args):
    eeg_npy, eeg_index = choose_cache(args.cache)

    for path in [eeg_npy, eeg_index, TRIAL_INDEX, STIMULUS_ONLY_PRED, FOLD_SAFE_SELECTED]:
        if not path.exists():
            raise FileNotFoundError(path)

    x = np.load(eeg_npy, mmap_mode="r")
    idx = pd.read_csv(eeg_index)
    trial = pd.read_csv(TRIAL_INDEX)
    stim = pd.read_csv(STIMULUS_ONLY_PRED)
    selected = pd.read_csv(FOLD_SAFE_SELECTED)

    idx = idx.copy()
    idx["cache_row"] = idx["cache_row"].astype(int)
    idx["subject_id"] = idx["subject_id"].astype(int)
    idx["stimulus_id"] = idx["stimulus_id"].astype(str)
    idx = idx.sort_values("cache_row").reset_index(drop=True)

    if x.ndim != 3 or tuple(x.shape[1:]) != (32, 640):
        raise ValueError(f"Unexpected EEG cache shape: {x.shape}")
    if len(idx) != x.shape[0]:
        raise ValueError(f"EEG/index mismatch: x={x.shape[0]}, index={len(idx)}")
    if not np.array_equal(idx["cache_row"].to_numpy(), np.arange(len(idx))):
        raise ValueError("cache_row is not contiguous 0..N-1")

    trial = trial.copy()
    trial["subject_id"] = trial["subject_id"].astype(int)
    trial["stimulus_id"] = trial["stimulus_id"].astype(str)

    needed = ["subject_id", "stimulus_id", "valence_score", "arousal_score"]
    missing = [c for c in needed if c not in trial.columns]
    if missing:
        raise KeyError(f"trial index missing: {missing}")

    for label_col in ["valence_score", "arousal_score"]:
        if label_col in idx.columns:
            idx = idx.drop(columns=[label_col])

    labels = trial[needed].drop_duplicates(["subject_id", "stimulus_id"])
    idx = idx.merge(labels, on=["subject_id", "stimulus_id"], how="left")

    if idx[["valence_score", "arousal_score"]].isna().any().any():
        missing_n = int(idx[["valence_score", "arousal_score"]].isna().any(axis=1).sum())
        raise ValueError(f"Some EEG cache rows did not receive labels from trial index: missing_rows={missing_n}")

    stim = stim[stim["model"].eq("stimulus_only")].copy()
    stim["test_subject"] = stim["test_subject"].astype(int)
    stim["stimulus_id"] = stim["stimulus_id"].astype(str)

    selected = selected.copy()
    selected["test_subject"] = selected["test_subject"].astype(int)
    selected["stimulus_id"] = selected["stimulus_id"].astype(str)

    return x, idx, stim, selected, eeg_npy, eeg_index


def fit_eeg_normalizer(x_mmap, rows):
    arr = np.asarray(x_mmap[rows], dtype=np.float32).copy()
    mean = arr.mean(axis=(0, 2), keepdims=True)
    std = arr.std(axis=(0, 2), keepdims=True)
    std = np.where(std < EPS, 1.0, std)
    return mean.astype(np.float32), std.astype(np.float32)


def load_normed(x_mmap, rows, mean, std):
    arr = np.asarray(x_mmap[rows], dtype=np.float32).copy()
    arr = (arr - mean) / std
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    return arr.astype(np.float32)


def loo_train_deviation(df: pd.DataFrame, score_col: str) -> np.ndarray:
    g = df.groupby("stimulus_id")[score_col].agg(["sum", "count"])
    sums = df["stimulus_id"].map(g["sum"]).to_numpy(dtype=float)
    counts = df["stimulus_id"].map(g["count"]).to_numpy(dtype=float)
    y = df[score_col].to_numpy(dtype=float)
    means = (sums - y) / np.maximum(counts - 1.0, 1.0)
    return y - means


def heldout_deviation(eval_df: pd.DataFrame, train_df: pd.DataFrame, score_col: str):
    means = train_df.groupby("stimulus_id")[score_col].mean()
    baseline = eval_df["stimulus_id"].map(means).astype(float).to_numpy()
    y = eval_df[score_col].to_numpy(dtype=float)
    return y - baseline, baseline


def fit_target_scaler(y: np.ndarray):
    y = np.asarray(y, dtype=float)
    mean = float(np.mean(y))
    std = float(np.std(y))
    if not math.isfinite(std) or std < EPS:
        std = 1.0
    return mean, std


def scale_target(y: np.ndarray, mean: float, std: float):
    return ((np.asarray(y, dtype=float) - mean) / std).astype(np.float32)


def unscale_target(y_scaled: np.ndarray, mean: float, std: float):
    return np.asarray(y_scaled, dtype=float) * float(std) + float(mean)


def make_model(args, device):
    model = EEGSegmentClassifier(
        C=32,
        sampling_rate=128,
        window_sec=5.0,
        n_classes=1,
        modelsize="lite",
        dropout=args.dropout,
        head_dropout=args.head_dropout,
        norm_kind="gn",
        stem_fusion="concat",
        channel_pos_mode="learnable",
        channel_mixer="mha",
        use_spectral_branch=False,
        use_projection_head=True,
        projection_dim=64,
    )
    return model.to(device)


def predict_scaled(model, x_np, batch_size, device):
    model.eval()
    preds = []
    with torch.no_grad():
        for start in range(0, len(x_np), batch_size):
            xb = torch.from_numpy(x_np[start:start + batch_size]).to(device)
            logits, _ = model(xb, return_attn=False)
            pred = logits.squeeze(-1).detach().cpu().numpy()
            preds.append(pred)
    return np.concatenate(preds).astype(float)


def evaluate_scaled_rmse(model, x_val, y_val_scaled, batch_size, device):
    pred = predict_scaled(model, x_val, batch_size, device)
    err = pred - y_val_scaled
    return float(np.sqrt(np.mean(err * err)))


def train_with_early_stopping(x_train, y_train_scaled, args, device, x_val=None, y_val_scaled=None):
    model = make_model(args, device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    loss_fn = nn.HuberLoss(delta=args.huber_delta)

    ds = EEGResidualDataset(x_train, y_train_scaled)
    loader = DataLoader(
        ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        drop_last=False,
    )

    best_epoch = 0
    best_val = None
    best_state = None
    bad_epochs = 0
    history = []

    for epoch in range(1, int(args.epochs) + 1):
        model.train()
        losses = []

        for xb, yb in loader:
            xb = xb.to(device)
            yb = yb.to(device)

            opt.zero_grad(set_to_none=True)
            logits, _ = model(xb, return_attn=False)
            pred = logits.squeeze(-1)
            loss = loss_fn(pred, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            opt.step()

            losses.append(float(loss.detach().cpu().item()))

        row = {
            "epoch": int(epoch),
            "train_loss": safe_float(np.mean(losses)),
        }

        if x_val is not None and y_val_scaled is not None and len(x_val):
            val_rmse_scaled = evaluate_scaled_rmse(model, x_val, y_val_scaled, args.batch_size, device)
            row["val_rmse_scaled"] = safe_float(val_rmse_scaled)

            if best_val is None or val_rmse_scaled < best_val - 1e-6:
                best_val = val_rmse_scaled
                best_epoch = epoch
                best_state = copy.deepcopy(model.state_dict())
                bad_epochs = 0
            else:
                bad_epochs += 1

            if bad_epochs >= args.patience:
                row["early_stop"] = True
                history.append(row)
                break

        history.append(row)

    if best_state is not None:
        model.load_state_dict(best_state)
    else:
        best_epoch = int(args.epochs)
        best_val = None

    return model, int(best_epoch), safe_float(best_val), history


def train_for_fixed_epochs(x_train, y_train_scaled, args, device, epochs):
    model = make_model(args, device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    loss_fn = nn.HuberLoss(delta=args.huber_delta)

    ds = EEGResidualDataset(x_train, y_train_scaled)
    loader = DataLoader(
        ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        drop_last=False,
    )

    history = []
    for epoch in range(1, int(max(1, epochs)) + 1):
        model.train()
        losses = []

        for xb, yb in loader:
            xb = xb.to(device)
            yb = yb.to(device)

            opt.zero_grad(set_to_none=True)
            logits, _ = model(xb, return_attn=False)
            pred = logits.squeeze(-1)
            loss = loss_fn(pred, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            opt.step()

            losses.append(float(loss.detach().cpu().item()))

        history.append({
            "epoch": int(epoch),
            "train_loss": safe_float(np.mean(losses)),
        })

    return model, history


def split_inner_subjects(train_subjects, test_subject, val_count, seed):
    train_subjects = sorted([int(s) for s in train_subjects])
    rng = np.random.default_rng(seed + int(test_subject) * 17)
    shuffled = np.asarray(train_subjects, dtype=int).copy()
    rng.shuffle(shuffled)

    val_count = int(min(max(1, val_count), max(1, len(shuffled) - 1)))
    val_subjects = sorted(shuffled[:val_count].tolist())
    fit_subjects = sorted([s for s in train_subjects if s not in set(val_subjects)])
    return fit_subjects, val_subjects


def add_subset_flags(pred, selected):
    out = pred.copy()
    for subset in sorted(selected["subset"].astype(str).unique()):
        key = selected[selected["subset"].astype(str).eq(subset)][
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


def aggregate_main(pred):
    rows = []
    for model, g in pred.groupby("model"):
        row = {"target": g["target"].iloc[0], "model": model}
        row.update(prediction_metrics(g))
        row.update(deviation_metrics(g))
        rows.append(row)
    return pd.DataFrame(rows)


def aggregate_subsets(pred):
    subset_cols = [c for c in pred.columns if c.startswith("is_top25_train_")]
    rows = []

    for subset_col in subset_cols:
        subset_name = subset_col.replace("is_", "")
        for model, g0 in pred.groupby("model"):
            g = g0[g0[subset_col]].copy()
            row = {
                "target": g0["target"].iloc[0],
                "subset": subset_name,
                "model": model,
            }
            row.update(prediction_metrics(g))
            row.update(deviation_metrics(g))
            rows.append(row)

    return pd.DataFrame(rows)


def add_lifts(df, group_cols):
    rows = []
    lower_is_better = {"mae", "rmse", "dev_mae", "dev_rmse"}
    metrics = [
        "mae", "rmse", "pearson", "spearman",
        "balanced_accuracy", "macro_f1", "auroc",
        "dev_mae", "dev_rmse", "dev_pearson", "dev_spearman",
        "dev_sign_acc", "true_dev_std", "pred_dev_std",
    ]

    for _, g in df.groupby(group_cols, dropna=False):
        base = g[g["model"].eq("stimulus_only")]
        if base.empty:
            continue
        base = base.iloc[0]

        for _, row in g.iterrows():
            out = row.to_dict()
            for m in metrics:
                rv = row.get(m, np.nan)
                bv = base.get(m, np.nan)
                if pd.isna(rv) or pd.isna(bv):
                    out[f"lift_vs_stimulus_{m}"] = None
                elif m in lower_is_better:
                    out[f"lift_vs_stimulus_{m}"] = safe_float(float(bv) - float(rv))
                else:
                    out[f"lift_vs_stimulus_{m}"] = safe_float(float(rv) - float(bv))
            rows.append(out)

    return pd.DataFrame(rows)


def run_training(args):
    set_seed(args.seed)
    t0 = time.perf_counter()

    x_mmap, idx, stim_pred, selected, eeg_npy, eeg_index = load_inputs(args)
    score_col = TARGET_COLUMNS[args.target]

    subjects = sorted(idx["subject_id"].unique().tolist())
    test_subjects = subjects[: args.max_folds]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device: {device}")
    print(f"target: {args.target}")
    print(f"cache: {args.cache}")
    print(f"test_subjects: {test_subjects}")
    print(f"epochs={args.epochs} patience={args.patience} lr={args.lr}")

    all_pred_rows = []
    fold_rows = []
    history_rows = []

    for fold_i, test_subject in enumerate(test_subjects, start=1):
        print(f"\n=== Fold {fold_i}/{len(test_subjects)} | test_subject={test_subject} ===")

        outer_train_subjects = [s for s in subjects if s != test_subject]
        fit_subjects, val_subjects = split_inner_subjects(
            outer_train_subjects,
            test_subject=test_subject,
            val_count=args.val_subject_count,
            seed=args.seed,
        )

        fit_df = idx[idx["subject_id"].isin(fit_subjects)].copy()
        val_df = idx[idx["subject_id"].isin(val_subjects)].copy()
        outer_train_df = idx[idx["subject_id"].isin(outer_train_subjects)].copy()
        test_df = idx[idx["subject_id"].eq(test_subject)].copy()

        # Inner fit/validation stage for epoch selection.
        fit_rows = fit_df["cache_row"].to_numpy(dtype=int)
        val_rows = val_df["cache_row"].to_numpy(dtype=int)

        fit_mean, fit_std = fit_eeg_normalizer(x_mmap, fit_rows)
        x_fit = load_normed(x_mmap, fit_rows, fit_mean, fit_std)
        x_val = load_normed(x_mmap, val_rows, fit_mean, fit_std)

        y_fit_raw = loo_train_deviation(fit_df, score_col).astype(float)
        y_fit_mean, y_fit_std = fit_target_scaler(y_fit_raw)
        y_fit_scaled = scale_target(y_fit_raw, y_fit_mean, y_fit_std)

        y_val_raw, _ = heldout_deviation(val_df, fit_df, score_col)
        y_val_scaled = scale_target(y_val_raw, y_fit_mean, y_fit_std)

        _, best_epoch, best_val_scaled, hist = train_with_early_stopping(
            x_fit,
            y_fit_scaled,
            args,
            device,
            x_val=x_val,
            y_val_scaled=y_val_scaled,
        )

        for h in hist:
            hh = dict(h)
            hh.update({
                "stage": "inner",
                "test_subject": int(test_subject),
                "target": args.target,
                "y_fit_mean": safe_float(y_fit_mean),
                "y_fit_std": safe_float(y_fit_std),
            })
            history_rows.append(hh)

        print(f"best_epoch={best_epoch} best_val_rmse_scaled={best_val_scaled}")

        # Final model: retrain on all outer train subjects for selected epoch.
        outer_rows = outer_train_df["cache_row"].to_numpy(dtype=int)
        test_rows = test_df["cache_row"].to_numpy(dtype=int)

        outer_mean, outer_std = fit_eeg_normalizer(x_mmap, outer_rows)
        x_outer = load_normed(x_mmap, outer_rows, outer_mean, outer_std)
        x_test = load_normed(x_mmap, test_rows, outer_mean, outer_std)

        y_outer_raw = loo_train_deviation(outer_train_df, score_col).astype(float)
        y_outer_mean, y_outer_std = fit_target_scaler(y_outer_raw)
        y_outer_scaled = scale_target(y_outer_raw, y_outer_mean, y_outer_std)

        final_model, final_hist = train_for_fixed_epochs(
            x_outer,
            y_outer_scaled,
            args,
            device,
            epochs=best_epoch,
        )

        for h in final_hist:
            hh = dict(h)
            hh.update({
                "stage": "final",
                "test_subject": int(test_subject),
                "target": args.target,
                "y_outer_mean": safe_float(y_outer_mean),
                "y_outer_std": safe_float(y_outer_std),
            })
            history_rows.append(hh)

        pred_scaled = predict_scaled(final_model, x_test, args.batch_size, device)
        pred_dev = unscale_target(pred_scaled, y_outer_mean, y_outer_std)

        true_dev, train_stim_mean = heldout_deviation(test_df, outer_train_df, score_col)
        true_score = test_df[score_col].to_numpy(dtype=float)
        pred_score = train_stim_mean + pred_dev

        eeg_rows = test_df[["subject_id", "stimulus_id"]].rename(
            columns={"subject_id": "test_subject"}
        ).copy()
        eeg_rows["target"] = args.target
        eeg_rows["model"] = MODEL_NAME
        eeg_rows["y_true_score"] = true_score
        eeg_rows["train_stimulus_mean"] = train_stim_mean
        eeg_rows["true_deviation_from_train_stimulus_mean"] = true_dev
        eeg_rows["y_pred_deviation_raw"] = pred_dev
        eeg_rows["y_pred_score_raw"] = pred_score
        eeg_rows["y_pred_score_clipped"] = np.clip(pred_score, 1.0, 9.0)
        eeg_rows["y_pred_deviation_clipped"] = eeg_rows["y_pred_score_clipped"] - eeg_rows["train_stimulus_mean"]

        all_pred_rows.append(eeg_rows)

        fold_metric = {"target": args.target, "model": MODEL_NAME, "test_subject": int(test_subject)}
        fold_metric.update(prediction_metrics(eeg_rows))
        fold_metric.update(deviation_metrics(eeg_rows))
        fold_metric.update({
            "best_epoch": int(best_epoch),
            "best_val_rmse_scaled": safe_float(best_val_scaled),
            "fit_subjects": int(len(fit_subjects)),
            "val_subjects": int(len(val_subjects)),
            "outer_train_subjects": int(len(outer_train_subjects)),
            "y_outer_mean": safe_float(y_outer_mean),
            "y_outer_std": safe_float(y_outer_std),
            "final_train_last_loss": safe_float(final_hist[-1]["train_loss"]) if final_hist else None,
        })
        fold_rows.append(fold_metric)

        print(
            f"test rmse={fold_metric['rmse']:.4f} "
            f"dev_rmse={fold_metric['dev_rmse']:.4f} "
            f"dev_pearson={fold_metric['dev_pearson']} "
            f"pred_dev_std={fold_metric['pred_dev_std']}"
        )

    eeg_pred = pd.concat(all_pred_rows, ignore_index=True)

    # Add matching official stimulus-only rows for the same smoke folds.
    stim = stim_pred[
        (stim_pred["target"].eq(args.target))
        & (stim_pred["test_subject"].isin(test_subjects))
        & (stim_pred["model"].eq("stimulus_only"))
    ].copy()

    stim_rows = []
    for _, row in stim.iterrows():
        pred_score = float(row["y_pred_score"])
        stim_rows.append({
            "test_subject": int(row["test_subject"]),
            "stimulus_id": str(row["stimulus_id"]),
            "target": args.target,
            "model": "stimulus_only",
            "y_true_score": float(row["y_true_score"]),
            "train_stimulus_mean": pred_score,
            "true_deviation_from_train_stimulus_mean": float(row["true_deviation_from_train_stimulus_mean"]),
            "y_pred_deviation_raw": 0.0,
            "y_pred_score_raw": pred_score,
            "y_pred_score_clipped": np.clip(pred_score, 1.0, 9.0),
            "y_pred_deviation_clipped": 0.0,
        })

    pred = pd.concat([pd.DataFrame(stim_rows), eeg_pred], ignore_index=True)
    pred = add_subset_flags(pred, selected)

    main = add_lifts(aggregate_main(pred), ["target"])
    subset = add_lifts(aggregate_subsets(pred), ["target", "subset"])
    fold_df = pd.DataFrame(fold_rows)
    history_df = pd.DataFrame(history_rows)

    pred.to_csv(OUT_PRED_CSV, index=False)
    main.to_csv(OUT_MAIN_CSV, index=False)
    subset.to_csv(OUT_SUBSET_CSV, index=False)
    fold_df.to_csv(OUT_FOLD_CSV, index=False)
    history_df.to_csv(OUT_HISTORY_CSV, index=False)

    summary = {
        "protocol": "EEG residual training stabilized smoke",
        "target": args.target,
        "cache": args.cache,
        "model": MODEL_NAME,
        "epochs_max": args.epochs,
        "patience": args.patience,
        "max_folds": args.max_folds,
        "test_subjects": test_subjects,
        "validation_subject_count": args.val_subject_count,
        "target_normalization": "fit residual mean/std on train subjects only; predict scaled residual; de-scale using outer train stats",
        "loss": f"HuberLoss(delta={args.huber_delta}) on scaled residual",
        "optimizer": {
            "name": "AdamW",
            "lr": args.lr,
            "weight_decay": args.weight_decay,
        },
        "model_config": {
            "dropout": args.dropout,
            "head_dropout": args.head_dropout,
            "n_classes": 1,
            "modelsize": "lite",
        },
        "device": {
            "torch": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "device": str(device),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        "inputs": {
            "eeg_npy": str(eeg_npy),
            "eeg_index": str(eeg_index),
            "trial_index": str(TRIAL_INDEX),
            "stimulus_only_predictions": str(STIMULUS_ONLY_PRED),
            "fold_safe_selected": str(FOLD_SAFE_SELECTED),
        },
        "main_metrics": main.to_dict(orient="records"),
        "subset_metrics": subset.to_dict(orient="records"),
        "fold_summary": fold_df.to_dict(orient="records"),
        "elapsed_sec": safe_float(time.perf_counter() - t0),
        "notes": [
            "This is a stabilized smoke run, not the final full LOSO training.",
            "Residual targets are normalized using train-only residual mean/std.",
            "Epoch is selected using validation subjects from outer-train subjects only.",
            "After epoch selection, the model is retrained on all outer-train subjects.",
            "The held-out test subject is only used for final evaluation.",
            "Final score is train-stimulus mean plus EEG-predicted residual.",
        ],
    }

    OUT_JSON.write_text(json.dumps(clean_json(summary), indent=2, ensure_ascii=False), encoding="utf-8")

    main_cols = [
        "target", "model", "n",
        "mae", "rmse", "pearson", "balanced_accuracy", "auroc",
        "dev_rmse", "dev_pearson", "dev_sign_acc",
        "true_dev_std", "pred_dev_std",
        "lift_vs_stimulus_rmse",
        "lift_vs_stimulus_balanced_accuracy",
        "lift_vs_stimulus_auroc",
        "lift_vs_stimulus_dev_rmse",
    ]

    subset_cols = [
        "target", "subset", "model", "n",
        "rmse", "balanced_accuracy", "auroc",
        "dev_rmse", "dev_pearson",
        "true_dev_std", "pred_dev_std",
        "lift_vs_stimulus_rmse",
        "lift_vs_stimulus_balanced_accuracy",
        "lift_vs_stimulus_auroc",
        "lift_vs_stimulus_dev_rmse",
    ]

    lines = []
    lines.append("# ROCA-I-DARE EEG Residual Training Stabilized Smoke\n")
    lines.append("This is a strict-LOSO stabilized smoke run, not final full training.\n")
    lines.append("## Configuration\n")
    lines.append(f"- target: `{args.target}`")
    lines.append(f"- cache: `{args.cache}`")
    lines.append(f"- model: `{MODEL_NAME}`")
    lines.append(f"- test_subjects: `{test_subjects}`")
    lines.append(f"- epochs_max: `{args.epochs}`")
    lines.append(f"- patience: `{args.patience}`")
    lines.append(f"- batch_size: `{args.batch_size}`")
    lines.append(f"- optimizer: `AdamW(lr={args.lr}, weight_decay={args.weight_decay})`")
    lines.append(f"- loss: `HuberLoss(delta={args.huber_delta}) on scaled residual`")
    lines.append(f"- dropout/head_dropout: `{args.dropout}` / `{args.head_dropout}`")
    lines.append("")
    lines.append("## Main metrics\n")
    lines.append(md_table(main.to_dict(orient="records"), main_cols))
    lines.append("\n## Fold-safe hard subset metrics\n")
    lines.append(md_table(subset.to_dict(orient="records"), subset_cols))
    lines.append("\n## Fold summary\n")
    lines.append(md_table(fold_df.to_dict(orient="records"), [
        "test_subject",
        "best_epoch",
        "best_val_rmse_scaled",
        "rmse",
        "dev_rmse",
        "dev_pearson",
        "true_dev_std",
        "pred_dev_std",
        "y_outer_std",
        "final_train_last_loss",
    ]))
    lines.append("\n## Interpretation guide\n")
    lines.append(
        "- Positive `lift_vs_stimulus_rmse` means lower score RMSE than stimulus-only.\n"
        "- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.\n"
        "- `pred_dev_std` should not collapse near zero if the model is learning residual variation.\n"
        "- If this smoke run is stable and promising, the next step is full 63-subject LOSO.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05c completed.")
    print(f"wrote: {OUT_MD}")
    print(f"wrote: {OUT_JSON}")
    print(f"wrote: {OUT_PRED_CSV}")
    print(f"wrote: {OUT_MAIN_CSV}")
    print(f"wrote: {OUT_SUBSET_CSV}")
    print(f"wrote: {OUT_FOLD_CSV}")
    print(f"wrote: {OUT_HISTORY_CSV}")
    print("\nMain metrics:")
    print(main[main_cols].to_string(index=False))
    print("\nFold summary:")
    print(fold_df[[
        "test_subject", "best_epoch", "best_val_rmse_scaled",
        "rmse", "dev_rmse", "dev_pearson",
        "true_dev_std", "pred_dev_std", "y_outer_std",
        "final_train_last_loss"
    ]].to_string(index=False))


def main():
    args = parse_args()
    run_training(args)


if __name__ == "__main__":
    main()
