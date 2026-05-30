#!/usr/bin/env python3
"""
ROCA 06a1y: Split-control learning probe for I-DARE arousal high-disagreement residuals.

Purpose
-------
Use the same lightweight previous-model style EEG residual encoder under multiple split
protocols to isolate whether failure is mainly:
  (a) weak/no physiological residual signal, or
  (b) subject/domain shift under LOSO.

This script deliberately keeps the model small and the target narrow:
  - target: arousal residual/deviation from a training-only stimulus prior
  - input: baseline-corrected I-DARE EEG 5s stimulus cache [N, 32, 640]
  - evaluation: high-disagreement residual subset, threshold imported from 05ajb when available
  - split controls: random row split, within-subject trial split, leave-one-subject-out,
    leave-one-stimulus-out

It does not claim final performance. It is an autopsy/diagnostic probe.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset


ROOT = Path.cwd()
ROCA = ROOT / "docs" / "roca"
CACHE_DIR = ROOT / ".cache"
OUT_PREFIX_DEFAULT = "idare_06a1y_split_control_deep_learning_probe_current"
SMOKE_PREFIX_DEFAULT = "idare_06a1y_split_control_deep_learning_probe_smoke_current"

EEG_CACHE_DEFAULT = CACHE_DIR / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
EEG_INDEX_DEFAULT = CACHE_DIR / "idare_eeg_cache_index_baseline_corrected.csv"
REF_05AJB = ROCA / "idare_high_disagreement_direct_deviation_confirmatory_stats_current_verdict.csv"

SUBJECT_CANDIDATES = ["subject_id", "subject", "participant_id", "participant", "subj", "test_subject"]
STIMULUS_CANDIDATES = ["stimulus_id", "stimulus", "trial_id", "trial", "video_id", "picture_id"]
AROUSAL_CANDIDATES = ["arousal_score", "arousal", "y_arousal", "label_arousal"]


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = True


def find_col(df: pd.DataFrame, candidates: Sequence[str], what: str) -> str:
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    raise SystemExit(f"Could not find {what} column. Tried {candidates}. Available columns: {list(df.columns)}")


def normalize_id_series(s: pd.Series) -> pd.Series:
    """Convert numeric or string IDs like Dummy_1 / S01 into stable integer IDs."""
    raw = s.astype(str).str.strip()
    numeric = pd.to_numeric(raw, errors="coerce")
    if numeric.notna().all():
        return numeric.astype(int)

    extracted = raw.str.extract(r"(-?\d+)", expand=False)
    extracted_num = pd.to_numeric(extracted, errors="coerce")
    if extracted_num.notna().all():
        return extracted_num.astype(int)

    codes, _ = pd.factorize(raw, sort=True)
    return pd.Series(codes + 1, index=s.index, dtype=int)


def safe_float(x, default: Optional[float] = None) -> Optional[float]:
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def pearson(y: np.ndarray, p: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    if len(y) < 2 or np.std(y) <= 1e-12 or np.std(p) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(y, p)[0, 1])


def rmse(y: np.ndarray, p: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    if len(y) == 0:
        return float("nan")
    return float(np.sqrt(np.mean((y - p) ** 2)))


def sign_acc(y: np.ndarray, p: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    if len(y) == 0:
        return float("nan")
    return float(np.mean(np.sign(y) == np.sign(p)))


def bootstrap_ci_mean(values: np.ndarray, seed: int, n_boot: int = 2000) -> Tuple[float, float]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        sample = rng.choice(values, size=len(values), replace=True)
        boots.append(float(np.mean(sample)))
    return float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))


def signflip_p_one_sided_mean_gt_zero(values: np.ndarray, seed: int, n_perm: int = 20000) -> float:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return float("nan")
    obs = float(np.mean(values))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_perm, len(values)), replace=True)
    null = (signs * values[None, :]).mean(axis=1)
    return float((np.sum(null >= obs) + 1.0) / (n_perm + 1.0))


def md_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df is None or df.empty:
        return "\n"
    x = df.head(max_rows).copy()
    for c in x.columns:
        if pd.api.types.is_float_dtype(x[c]):
            x[c] = x[c].map(lambda v: "" if pd.isna(v) else f"{v:.6g}")
        else:
            x[c] = x[c].map(lambda v: "" if pd.isna(v) else str(v))
    cols = list(x.columns)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in x.iterrows():
        vals = [str(row[c]).replace("|", "\\|") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def load_reference_threshold() -> Dict[str, object]:
    ref = {
        "source": str(REF_05AJB.relative_to(ROOT)) if REF_05AJB.exists() else None,
        "abs_residual_threshold": 2.2096774193548385,
        "fixed_reference_residual_rmse": 3.1684144111057955,
        "fixed_reference_lift_vs_zero": 0.0717248010176145,
        "fixed_reference_residual_pearson": 0.2129723962280969,
        "fixed_reference_block": "eeg_bandpower",
        "fixed_reference_model": "physio_eeg_bandpower_ridge",
    }
    if not REF_05AJB.exists():
        return ref
    try:
        df = pd.read_csv(REF_05AJB)
        row = df[df["target"].astype(str).str.lower().eq("arousal")].iloc[0]
        ref.update({
            "abs_residual_threshold": safe_float(row.get("abs_residual_threshold"), ref["abs_residual_threshold"]),
            "fixed_reference_residual_rmse": safe_float(row.get("model_residual_rmse"), ref["fixed_reference_residual_rmse"]),
            "fixed_reference_lift_vs_zero": safe_float(row.get("pooled_lift_vs_zero_residual_rmse"), ref["fixed_reference_lift_vs_zero"]),
            "fixed_reference_residual_pearson": safe_float(row.get("residual_pearson"), ref["fixed_reference_residual_pearson"]),
            "fixed_reference_block": row.get("feature_block", ref["fixed_reference_block"]),
            "fixed_reference_model": row.get("model", ref["fixed_reference_model"]),
        })
    except Exception as e:
        ref["load_warning"] = repr(e)
    return ref


class EEGDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray):
        self.x = torch.from_numpy(x.astype(np.float32, copy=False))
        self.y = torch.from_numpy(y.astype(np.float32, copy=False)).view(-1, 1)

    def __len__(self) -> int:
        return int(self.x.shape[0])

    def __getitem__(self, idx: int):
        return self.x[idx], self.y[idx]


class EEGSegmentEncoderLite(nn.Module):
    """Previous-model-style lightweight EEG segment encoder plus residual head.

    The original project used temporal convolution / mixer / attention ideas. This probe keeps
    the same spirit but intentionally low capacity to make split behavior interpretable.
    """
    def __init__(self, channels: int = 32, width: int = 64, dropout: float = 0.20):
        super().__init__()
        self.stem = nn.Sequential(
            nn.Conv1d(channels, width, kernel_size=7, padding=3, bias=False),
            nn.GroupNorm(8, width),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.branch3 = nn.Sequential(
            nn.Conv1d(width, width, kernel_size=3, padding=1, groups=4, bias=False),
            nn.GroupNorm(8, width),
            nn.GELU(),
        )
        self.branch9 = nn.Sequential(
            nn.Conv1d(width, width, kernel_size=9, padding=4, groups=4, bias=False),
            nn.GroupNorm(8, width),
            nn.GELU(),
        )
        self.branch25 = nn.Sequential(
            nn.Conv1d(width, width, kernel_size=25, padding=12, groups=4, bias=False),
            nn.GroupNorm(8, width),
            nn.GELU(),
        )
        self.fuse = nn.Sequential(
            nn.Conv1d(width * 3, width, kernel_size=1, bias=False),
            nn.GroupNorm(8, width),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        enc = nn.TransformerEncoderLayer(
            d_model=width,
            nhead=4,
            dim_feedforward=width * 2,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )
        self.temporal_mixer = nn.TransformerEncoder(enc, num_layers=1)
        self.head = nn.Sequential(
            nn.LayerNorm(width),
            nn.Linear(width, width),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(width, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, C, T]
        z = self.stem(x)
        z = torch.cat([self.branch3(z), self.branch9(z), self.branch25(z)], dim=1)
        z = self.fuse(z)
        # downsample before transformer to keep smoke/full cheap
        z = nn.functional.avg_pool1d(z, kernel_size=8, stride=8)  # [B, W, 80]
        z = z.transpose(1, 2)  # [B, 80, W]
        z = self.temporal_mixer(z)
        z = z.mean(dim=1)
        return self.head(z).squeeze(1)


def compute_train_prior(meta: pd.DataFrame, train_idx: np.ndarray, stimulus_col: str, score_col: str) -> Tuple[Dict[int, float], float]:
    train = meta.iloc[train_idx]
    overall = float(train[score_col].mean())
    prior = train.groupby(stimulus_col)[score_col].mean().to_dict()
    return {int(k): float(v) for k, v in prior.items()}, overall


def residual_from_prior(meta: pd.DataFrame, idx: np.ndarray, stimulus_col: str, score_col: str, prior: Dict[int, float], fallback: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    stim = meta.iloc[idx][stimulus_col].astype(int).to_numpy()
    y = meta.iloc[idx][score_col].astype(float).to_numpy()
    pred = np.array([prior.get(int(s), fallback) for s in stim], dtype=float)
    missing = np.array([0 if int(s) in prior else 1 for s in stim], dtype=int)
    return y - pred, pred, missing


def train_val_split_indices(meta: pd.DataFrame, train_idx: np.ndarray, seed: int, subject_col: str, val_frac: float = 0.15) -> Tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_idx = np.array(train_idx, dtype=int)
    subjects = np.array(sorted(meta.iloc[train_idx][subject_col].unique()))
    if len(subjects) >= 8:
        n_val_subj = max(2, int(round(len(subjects) * val_frac)))
        val_subj = set(rng.choice(subjects, size=n_val_subj, replace=False).tolist())
        mask = meta.iloc[train_idx][subject_col].isin(val_subj).to_numpy()
        fit_idx = train_idx[~mask]
        val_idx = train_idx[mask]
        if len(fit_idx) > 10 and len(val_idx) > 5:
            return fit_idx, val_idx
    perm = rng.permutation(train_idx)
    n_val = max(16, int(round(len(perm) * val_frac)))
    n_val = min(n_val, max(1, len(perm) - 1))
    return perm[n_val:], perm[:n_val]


def zscore_by_fit(x: np.ndarray, fit_idx: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    # channel-wise normalization over fit samples and time
    mu = x[fit_idx].mean(axis=(0, 2), keepdims=True)
    sd = x[fit_idx].std(axis=(0, 2), keepdims=True) + 1e-6
    return (x - mu) / sd, mu, sd


def make_splits(meta: pd.DataFrame, split: str, seed: int, subject_col: str, stimulus_col: str, smoke: bool) -> List[Tuple[str, np.ndarray, np.ndarray]]:
    n = len(meta)
    rng = np.random.default_rng(seed)
    rows = np.arange(n)
    splits: List[Tuple[str, np.ndarray, np.ndarray]] = []

    if split == "random_trial_kfold_subjects_overlap":
        k = 3 if smoke else 5
        perm = rng.permutation(rows)
        folds = np.array_split(perm, k)
        for i, test_idx in enumerate(folds, start=1):
            train_idx = np.setdiff1d(rows, test_idx, assume_unique=False)
            splits.append((f"random_fold_{i}", train_idx, test_idx))
        return splits

    if split == "within_subject_trial_kfold_subjects_overlap":
        k = 3 if smoke else 5
        fold_test: List[List[int]] = [[] for _ in range(k)]
        for _, g in meta.groupby(subject_col):
            arr = rng.permutation(g.index.to_numpy())
            chunks = np.array_split(arr, k)
            for i, ch in enumerate(chunks):
                fold_test[i].extend(ch.tolist())
        for i, test_list in enumerate(fold_test, start=1):
            test_idx = np.array(sorted(test_list), dtype=int)
            train_idx = np.setdiff1d(rows, test_idx, assume_unique=False)
            splits.append((f"within_subject_fold_{i}", train_idx, test_idx))
        return splits

    if split == "loso_leave_one_subject_out":
        subjects = sorted(meta[subject_col].unique())
        if smoke:
            subjects = subjects[:4]
        for s in subjects:
            test_idx = meta.index[meta[subject_col].eq(s)].to_numpy()
            train_idx = np.setdiff1d(rows, test_idx, assume_unique=False)
            splits.append((f"loso_subject_{s}", train_idx, test_idx))
        return splits

    if split == "leave_one_stimulus_out":
        stims = sorted(meta[stimulus_col].unique())
        if smoke:
            stims = stims[:4]
        for st in stims:
            test_idx = meta.index[meta[stimulus_col].eq(st)].to_numpy()
            train_idx = np.setdiff1d(rows, test_idx, assume_unique=False)
            splits.append((f"losto_stimulus_{st}", train_idx, test_idx))
        return splits

    raise ValueError(f"Unknown split: {split}")


@dataclass
class FoldResult:
    split: str
    fold_id: str
    seed: int
    n_train: int
    n_fit: int
    n_val: int
    n_test: int
    n_high: int
    zero_rmse_high: float
    model_rmse_high: float
    lift_vs_zero_high: float
    pearson_high: float
    sign_acc_high: float
    missing_stimulus_prior_rate_test: float
    best_epoch: int
    best_val_loss: float
    test_subjects: str
    test_stimuli: str


def run_one_fold(
    x_raw: np.ndarray,
    meta: pd.DataFrame,
    split_name: str,
    fold_id: str,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    args,
    subject_col: str,
    stimulus_col: str,
    score_col: str,
    threshold: float,
    device: torch.device,
) -> Tuple[FoldResult, pd.DataFrame, pd.DataFrame]:
    set_seed(args.seed + (abs(hash((split_name, fold_id))) % 100000))
    fit_idx, val_idx = train_val_split_indices(meta, train_idx, args.seed, subject_col, args.val_frac)

    prior, fallback = compute_train_prior(meta, fit_idx, stimulus_col, score_col)
    y_fit_dev, _, _ = residual_from_prior(meta, fit_idx, stimulus_col, score_col, prior, fallback)
    y_val_dev, _, _ = residual_from_prior(meta, val_idx, stimulus_col, score_col, prior, fallback)
    y_test_dev, test_prior_score, missing_test = residual_from_prior(meta, test_idx, stimulus_col, score_col, prior, fallback)

    x_norm, _, _ = zscore_by_fit(x_raw, fit_idx)
    x_fit = x_norm[fit_idx]
    x_val = x_norm[val_idx]
    x_test = x_norm[test_idx]

    train_ds = EEGDataset(x_fit, y_fit_dev)
    val_ds = EEGDataset(x_val, y_val_dev)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0, drop_last=False)

    model = EEGSegmentEncoderLite(channels=x_raw.shape[1], width=args.width, dropout=args.dropout).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    loss_fn = nn.SmoothL1Loss(beta=1.0)

    best_state = None
    best_val = float("inf")
    best_epoch = 0
    patience_left = args.patience

    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        total_n = 0
        for xb, yb in train_loader:
            xb = xb.to(device, non_blocking=True)
            yb = yb.to(device, non_blocking=True).view(-1)
            opt.zero_grad(set_to_none=True)
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            opt.step()
            total_loss += float(loss.detach().cpu()) * len(xb)
            total_n += len(xb)

        model.eval()
        val_losses = []
        with torch.no_grad():
            for xb, yb in val_loader:
                xb = xb.to(device, non_blocking=True)
                yb = yb.to(device, non_blocking=True).view(-1)
                pred = model(xb)
                val_losses.append(float(loss_fn(pred, yb).detach().cpu()) * len(xb))
        val_loss = float(np.sum(val_losses) / max(1, len(val_ds)))

        if val_loss < best_val - 1e-5:
            best_val = val_loss
            best_epoch = epoch
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience_left = args.patience
        else:
            patience_left -= 1

        if args.verbose:
            print(f"[{split_name}/{fold_id}] epoch={epoch}/{args.epochs} train_loss={total_loss/max(1,total_n):.5f} val_loss={val_loss:.5f}")
        if patience_left <= 0:
            break

    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    preds = []
    test_loader = DataLoader(EEGDataset(x_test, np.zeros(len(x_test), dtype=np.float32)), batch_size=args.batch_size, shuffle=False, num_workers=0)
    with torch.no_grad():
        for xb, _ in test_loader:
            xb = xb.to(device, non_blocking=True)
            preds.append(model(xb).detach().cpu().numpy())
    y_pred_dev = np.concatenate(preds, axis=0).astype(float)

    high_mask = np.abs(y_test_dev) >= threshold
    if int(high_mask.sum()) == 0:
        # Preserve fold in output, but it contributes no high-disagreement metric.
        zero_high = float("nan")
        model_high = float("nan")
        lift = float("nan")
        r = float("nan")
        sacc = float("nan")
    else:
        zero_high = rmse(y_test_dev[high_mask], np.zeros(int(high_mask.sum())))
        model_high = rmse(y_test_dev[high_mask], y_pred_dev[high_mask])
        lift = zero_high - model_high
        r = pearson(y_test_dev[high_mask], y_pred_dev[high_mask])
        sacc = sign_acc(y_test_dev[high_mask], y_pred_dev[high_mask])

    pred_df = meta.iloc[test_idx].copy()
    pred_df["split"] = split_name
    pred_df["fold_id"] = fold_id
    pred_df["seed"] = args.seed
    pred_df["target"] = "arousal"
    pred_df["train_stimulus_or_fallback_mean"] = test_prior_score
    pred_df["true_deviation_from_train_prior"] = y_test_dev
    pred_df["y_pred_deviation"] = y_pred_dev
    pred_df["y_pred_score"] = test_prior_score + y_pred_dev
    pred_df["is_high_disagreement_q75"] = high_mask.astype(int)
    pred_df["missing_stimulus_prior"] = missing_test

    subj_rows = []
    for subj, g in pred_df[pred_df["is_high_disagreement_q75"].eq(1)].groupby(subject_col):
        yy = g["true_deviation_from_train_prior"].to_numpy(float)
        pp = g["y_pred_deviation"].to_numpy(float)
        zero_s = rmse(yy, np.zeros_like(yy))
        model_s = rmse(yy, pp)
        subj_rows.append({
            "split": split_name,
            "fold_id": fold_id,
            "test_subject": int(subj),
            "n_high": int(len(g)),
            "zero_rmse_high": zero_s,
            "model_rmse_high": model_s,
            "improvement_zero_minus_model": zero_s - model_s,
            "pearson_high": pearson(yy, pp),
            "sign_acc_high": sign_acc(yy, pp),
        })
    subj_df = pd.DataFrame(subj_rows)

    result = FoldResult(
        split=split_name,
        fold_id=fold_id,
        seed=args.seed,
        n_train=int(len(train_idx)),
        n_fit=int(len(fit_idx)),
        n_val=int(len(val_idx)),
        n_test=int(len(test_idx)),
        n_high=int(high_mask.sum()),
        zero_rmse_high=zero_high,
        model_rmse_high=model_high,
        lift_vs_zero_high=lift,
        pearson_high=r,
        sign_acc_high=sacc,
        missing_stimulus_prior_rate_test=float(np.mean(missing_test)) if len(missing_test) else float("nan"),
        best_epoch=int(best_epoch),
        best_val_loss=float(best_val),
        test_subjects=",".join(map(str, sorted(pred_df[subject_col].unique()))),
        test_stimuli=",".join(map(str, sorted(pred_df[stimulus_col].unique()))),
    )
    return result, pred_df, subj_df


def aggregate_split(pred: pd.DataFrame, subject_col: str) -> pd.DataFrame:
    rows = []
    for split, g0 in pred.groupby("split"):
        g = g0[g0["is_high_disagreement_q75"].eq(1)].copy()
        if g.empty:
            continue
        yy = g["true_deviation_from_train_prior"].to_numpy(float)
        pp = g["y_pred_deviation"].to_numpy(float)
        zero = rmse(yy, np.zeros_like(yy))
        model = rmse(yy, pp)
        subj_delta = []
        wins = losses = ties = 0
        for _, sg in g.groupby(subject_col):
            sy = sg["true_deviation_from_train_prior"].to_numpy(float)
            sp = sg["y_pred_deviation"].to_numpy(float)
            z = rmse(sy, np.zeros_like(sy))
            m = rmse(sy, sp)
            d = z - m
            subj_delta.append(d)
            if d > 1e-9:
                wins += 1
            elif d < -1e-9:
                losses += 1
            else:
                ties += 1
        subj_delta_arr = np.asarray(subj_delta, dtype=float)
        ci_low, ci_high = bootstrap_ci_mean(subj_delta_arr, seed=1234)
        p_sf = signflip_p_one_sided_mean_gt_zero(subj_delta_arr, seed=1234)
        rows.append({
            "split": split,
            "folds": int(g0["fold_id"].nunique()),
            "n_high": int(len(g)),
            "subjects_high": int(g[subject_col].nunique()),
            "zero_rmse_high": zero,
            "model_rmse_high": model,
            "lift_vs_zero_high": zero - model,
            "pearson_high": pearson(yy, pp),
            "sign_acc_high": sign_acc(yy, pp),
            "mean_subject_improvement_zero_minus_model": float(np.mean(subj_delta_arr)) if len(subj_delta_arr) else float("nan"),
            "ci95_low_mean_subject_improvement": ci_low,
            "ci95_high_mean_subject_improvement": ci_high,
            "signflip_p_one_sided_mean_gt_zero": p_sf,
            "wins_vs_zero": int(wins),
            "losses_vs_zero": int(losses),
            "ties_vs_zero": int(ties),
            "win_margin_vs_zero": int(wins - losses),
            "missing_stimulus_prior_rate": float(g["missing_stimulus_prior"].mean()),
        })
    return pd.DataFrame(rows).sort_values("split")


def build_decision(split_summary: pd.DataFrame, ref: Dict[str, object]) -> pd.DataFrame:
    def get_lift(name: str) -> float:
        if split_summary.empty or name not in set(split_summary["split"]):
            return float("nan")
        return float(split_summary.loc[split_summary["split"].eq(name), "lift_vs_zero_high"].iloc[0])

    random_lift = get_lift("random_trial_kfold_subjects_overlap")
    within_lift = get_lift("within_subject_trial_kfold_subjects_overlap")
    loso_lift = get_lift("loso_leave_one_subject_out")
    stim_lift = get_lift("leave_one_stimulus_out")
    best_overlap = float(np.nanmax([random_lift, within_lift, stim_lift]))
    gap = best_overlap - loso_lift if np.isfinite(best_overlap) and np.isfinite(loso_lift) else float("nan")

    fixed_lift = safe_float(ref.get("fixed_reference_lift_vs_zero"), float("nan"))
    loso_minus_fixed = loso_lift - fixed_lift if np.isfinite(loso_lift) and np.isfinite(fixed_lift) else float("nan")

    if np.isfinite(best_overlap) and best_overlap >= 0.15 and np.isfinite(loso_lift) and loso_lift < 0.08:
        decision = "SUBJECT_SHIFT_CONFIRMED_DEEP_LEARNS_WITH_SUBJECT_OVERLAP_BUT_FAILS_LOSO"
        interpretation = "The deep residual model can exploit EEG signal when subject/domain overlap exists, but the mapping does not transfer cleanly to unseen subjects. This points to domain adaptation / subject normalization rather than blind architecture scaling."
        next_action = "Move to subject-adaptive residual representation: subject normalization, adversarial subject-invariant encoder, FiLM/adapters, or k-shot context."
    elif np.isfinite(loso_lift) and np.isfinite(fixed_lift) and loso_lift > fixed_lift + 0.02:
        decision = "DEEP_LOSO_BEATS_FIXED_REFERENCE_ON_HIGH_DISAGREEMENT"
        interpretation = "The previous-model-style deep representation improves the confirmed arousal high-disagreement pocket under LOSO."
        next_action = "Run confirmatory statistics and then test bridge to locked B2 personalization."
    elif np.isfinite(best_overlap) and best_overlap <= 0.02 and np.isfinite(loso_lift) and loso_lift <= 0.02:
        decision = "NO_CLEAR_DEEP_PHYSIOLOGY_SIGNAL_EVEN_WITH_SUBJECT_OVERLAP"
        interpretation = "This would suggest the target/input representation is weak even before LOSO generalization."
        next_action = "Audit residual target identifiability and input window/feature quality before more modeling."
    else:
        decision = "MIXED_SPLIT_CONTROL_RESULT_REQUIRES_REVIEW"
        interpretation = "The split-control pattern is not clean enough for a single diagnosis. Inspect split summaries and subject outliers."
        next_action = "Review split-specific subject stats, then decide between subject-adaptation and target/input audit."

    return pd.DataFrame([{
        "target": "arousal",
        "decision": decision,
        "random_trial_lift": random_lift,
        "within_subject_lift": within_lift,
        "leave_one_stimulus_lift": stim_lift,
        "loso_lift": loso_lift,
        "best_subject_overlap_lift": best_overlap,
        "overlap_minus_loso_lift_gap": gap,
        "fixed_eeg_bandpower_reference_lift": fixed_lift,
        "loso_minus_fixed_reference_lift": loso_minus_fixed,
        "interpretation": interpretation,
        "recommended_next_action": next_action,
    }])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--cache", type=Path, default=EEG_CACHE_DEFAULT)
    p.add_argument("--index", type=Path, default=EEG_INDEX_DEFAULT)
    p.add_argument("--out-prefix", type=str, default=OUT_PREFIX_DEFAULT)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--seed", type=int, default=11)
    p.add_argument("--epochs", type=int, default=8)
    p.add_argument("--smoke-epochs", type=int, default=2)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--width", type=int, default=64)
    p.add_argument("--dropout", type=float, default=0.20)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--weight-decay", type=float, default=1e-3)
    p.add_argument("--grad-clip", type=float, default=2.0)
    p.add_argument("--patience", type=int, default=3)
    p.add_argument("--val-frac", type=float, default=0.15)
    p.add_argument("--write-predictions", action="store_true")
    p.add_argument("--max-splits", type=str, default="", help="Optional comma list of split names to run")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    if args.smoke:
        args.epochs = args.smoke_epochs
        if args.out_prefix == OUT_PREFIX_DEFAULT:
            args.out_prefix = SMOKE_PREFIX_DEFAULT

    set_seed(args.seed)
    ROCA.mkdir(parents=True, exist_ok=True)

    if not args.cache.exists():
        raise SystemExit(f"Missing EEG cache: {args.cache}")
    if not args.index.exists():
        raise SystemExit(f"Missing EEG index: {args.index}")

    x = np.load(args.cache, mmap_mode="r")
    meta = pd.read_csv(args.index)
    if len(meta) != x.shape[0]:
        raise SystemExit(f"Cache/index row mismatch: x={x.shape[0]} index={len(meta)}")
    meta = meta.copy().reset_index(drop=True)
    subject_col0 = find_col(meta, SUBJECT_CANDIDATES, "subject")
    stimulus_col0 = find_col(meta, STIMULUS_CANDIDATES, "stimulus")
    score_col = find_col(meta, AROUSAL_CANDIDATES, "arousal score")

    meta["_subject_id_norm"] = normalize_id_series(meta[subject_col0])
    meta["_stimulus_id_norm"] = normalize_id_series(meta[stimulus_col0])
    subject_col = "_subject_id_norm"
    stimulus_col = "_stimulus_id_norm"
    meta[score_col] = pd.to_numeric(meta[score_col], errors="coerce")
    keep = meta[score_col].notna().to_numpy()
    if not keep.all():
        x = x[keep]
        meta = meta.loc[keep].reset_index(drop=True)

    ref = load_reference_threshold()
    threshold = float(ref["abs_residual_threshold"])

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] device={device}")
    if torch.cuda.is_available():
        print(f"[INFO] gpu={torch.cuda.get_device_name(0)}")
    print(f"[INFO] cache={args.cache} shape={tuple(x.shape)}")
    print(f"[INFO] index={args.index} rows={len(meta)} subject_col={subject_col0} stimulus_col={stimulus_col0} score_col={score_col}")
    print(f"[INFO] high-disagreement threshold={threshold:.6f}")
    print(f"[INFO] epochs={args.epochs} smoke={args.smoke}")

    all_split_names = [
        "random_trial_kfold_subjects_overlap",
        "within_subject_trial_kfold_subjects_overlap",
        "loso_leave_one_subject_out",
        "leave_one_stimulus_out",
    ]
    split_names = all_split_names
    if args.max_splits.strip():
        requested = [s.strip() for s in args.max_splits.split(",") if s.strip()]
        split_names = [s for s in all_split_names if s in requested]
        if not split_names:
            raise SystemExit(f"No known split names in --max-splits={args.max_splits}")

    fold_rows: List[dict] = []
    pred_frames: List[pd.DataFrame] = []
    subj_frames: List[pd.DataFrame] = []

    start = time.time()
    for split_name in split_names:
        split_defs = make_splits(meta, split_name, args.seed, subject_col, stimulus_col, args.smoke)
        print("\n" + "=" * 96)
        print(f"[SPLIT] {split_name} folds={len(split_defs)}")
        print("=" * 96)
        for i, (fold_id, train_idx, test_idx) in enumerate(split_defs, start=1):
            print(f"[fold {i}/{len(split_defs)}] {fold_id} train={len(train_idx)} test={len(test_idx)}")
            res, pred_df, subj_df = run_one_fold(
                x, meta, split_name, fold_id, train_idx, test_idx, args,
                subject_col, stimulus_col, score_col, threshold, device,
            )
            fold_rows.append(res.__dict__)
            pred_frames.append(pred_df)
            if not subj_df.empty:
                subj_frames.append(subj_df)
            print(f"  n_high={res.n_high} zero_rmse={res.zero_rmse_high:.4f} model_rmse={res.model_rmse_high:.4f} lift={res.lift_vs_zero_high:.4f} r={res.pearson_high:.4f} sign_acc={res.sign_acc_high:.4f}")

    fold_df = pd.DataFrame(fold_rows)
    pred_df = pd.concat(pred_frames, ignore_index=True) if pred_frames else pd.DataFrame()
    subj_df = pd.concat(subj_frames, ignore_index=True) if subj_frames else pd.DataFrame()
    split_summary = aggregate_split(pred_df, subject_col) if not pred_df.empty else pd.DataFrame()
    decision = build_decision(split_summary, ref)

    next_steps = pd.DataFrame([
        {
            "priority": 1,
            "step": "06a2",
            "title": "Subject-adaptive residual representation",
            "purpose": "If subject-overlap works but LOSO fails, add explicit subject/domain adaptation instead of blindly scaling architecture.",
            "success_condition": "Improves high-disagreement arousal under LOSO and then improves/matches locked B2 with paired subject support.",
        },
        {
            "priority": 2,
            "step": "06a3",
            "title": "Residual identifiability and label-noise bound",
            "purpose": "Quantify whether single-trial subjective residuals have enough repeatable structure for physiology learning.",
            "success_condition": "Upper/lower bounds explain whether model capacity can realistically help under LOSO.",
        },
        {
            "priority": 3,
            "step": "06a4",
            "title": "Subject-normalization and calibration ablation",
            "purpose": "Test per-subject EEG normalization, CORAL/MMD alignment, and k-shot calibration context before larger deep models.",
            "success_condition": "Reduces overlap-vs-LOSO gap without worsening high-disagreement residual metrics.",
        },
    ])

    out_base = ROCA / args.out_prefix
    decision.to_csv(f"{out_base}_decision_table.csv", index=False)
    split_summary.to_csv(f"{out_base}_split_summary.csv", index=False)
    fold_df.to_csv(f"{out_base}_fold_metrics.csv", index=False)
    subj_df.to_csv(f"{out_base}_subject_stats.csv", index=False)
    next_steps.to_csv(f"{out_base}_next_steps.csv", index=False)
    if args.write_predictions or args.smoke:
        slim_cols = [
            subject_col, stimulus_col, "split", "fold_id", "target", score_col,
            "train_stimulus_or_fallback_mean", "true_deviation_from_train_prior",
            "y_pred_deviation", "y_pred_score", "is_high_disagreement_q75",
            "missing_stimulus_prior",
        ]
        slim_cols = [c for c in slim_cols if c in pred_df.columns]
        pred_df[slim_cols].to_csv(f"{out_base}_predictions.csv", index=False)

    payload = {
        "title": "I-DARE 06a1y split-control deep learning probe",
        "created_unix": time.time(),
        "elapsed_sec": time.time() - start,
        "input": {
            "cache": str(args.cache),
            "index": str(args.index),
            "cache_shape": list(x.shape),
            "subject_col_original": subject_col0,
            "stimulus_col_original": stimulus_col0,
            "score_col": score_col,
            "target": "arousal",
            "threshold": threshold,
        },
        "reference_05ajb": ref,
        "args": vars(args),
        "decision": decision.to_dict(orient="records"),
        "split_summary": split_summary.to_dict(orient="records"),
        "next_steps": next_steps.to_dict(orient="records"),
    }
    with open(f"{out_base}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

    lines = []
    lines.append("# I-DARE 06a1y Split-Control Deep Learning Probe\n")
    lines.append("\n## Purpose\n")
    lines.append("This diagnostic reruns a previous-model-style lightweight EEG residual encoder under split controls to separate weak physiology from subject/domain-shift failure.\n")
    lines.append("\n## Decision\n")
    lines.append(md_table(decision))
    lines.append("\n## Split summary\n")
    lines.append(md_table(split_summary))
    lines.append("\n## 05ajb fixed reference\n")
    lines.append(md_table(pd.DataFrame([ref])))
    lines.append("\n## Next steps\n")
    lines.append(md_table(next_steps))
    lines.append("\n## Notes\n")
    lines.append("- Target is arousal high-disagreement residual/deviation.\n")
    lines.append("- The zero baseline predicts zero residual around a training-only stimulus prior when available.\n")
    lines.append("- Leave-one-stimulus-out uses the training global mean as fallback for unseen stimulus IDs; inspect `missing_stimulus_prior_rate`.\n")
    lines.append("- This is a diagnostic probe, not a final claim model.\n")
    (out_base.with_suffix(".md")).write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 06a1y completed.")
    for suffix in [".md", ".json", "_decision_table.csv", "_split_summary.csv", "_fold_metrics.csv", "_subject_stats.csv", "_next_steps.csv"]:
        print(f"wrote: {out_base}{suffix}")
    if args.write_predictions or args.smoke:
        print(f"wrote: {out_base}_predictions.csv")
    print("\nDecision table:")
    print(decision.to_string(index=False))
    print("\nSplit summary:")
    print(split_summary.to_string(index=False))
    print("\nNext steps:")
    print(next_steps.to_string(index=False))


if __name__ == "__main__":
    main()
