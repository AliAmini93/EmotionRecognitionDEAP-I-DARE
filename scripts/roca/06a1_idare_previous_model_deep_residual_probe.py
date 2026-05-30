#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import math
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from emotion_deap_idare.models.eeg_segment_encoder import EEGSegmentEncoder  # noqa: E402

ROCA = ROOT / "docs" / "roca"
OUT_PREFIX = "idare_06a1_previous_model_deep_residual_probe"

CACHE_BASELINE_CORRECTED = ROOT / ".cache" / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
INDEX_BASELINE_CORRECTED = ROOT / ".cache" / "idare_eeg_cache_index_baseline_corrected.csv"
CACHE_RAW = ROOT / ".cache" / "idare_eeg_windows_32x640_float32.npy"
INDEX_RAW = ROOT / ".cache" / "idare_eeg_cache_index.csv"

REFERENCE_05AJB = ROCA / "idare_high_disagreement_direct_deviation_confirmatory_stats_current_verdict.csv"


@dataclass(frozen=True)
class FoldSpec:
    seed: int
    test_subject: int
    train_subjects: list[int]
    val_subjects: list[int]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", default="arousal", choices=["arousal", "valence"])
    p.add_argument("--cache-policy", default="baseline_corrected", choices=["baseline_corrected", "raw"])
    p.add_argument("--seeds", nargs="+", type=int, default=[11])
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--patience", type=int, default=5)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--lr", type=float, default=1e-3)
    p.add_argument("--weight-decay", type=float, default=1e-3)
    p.add_argument("--grad-clip", type=float, default=1.0)
    p.add_argument("--dropout", type=float, default=0.10)
    p.add_argument("--head-dropout", type=float, default=0.25)
    p.add_argument("--high-weight", type=float, default=4.0)
    p.add_argument("--sign-loss-weight", type=float, default=0.20)
    p.add_argument("--val-subject-count", type=int, default=8)
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--max-test-subjects", type=int, default=0)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--cpu", action="store_true")
    p.add_argument("--threshold-source", default="confirmatory_or_train", choices=["confirmatory_or_train", "train"])
    p.add_argument("--bootstrap-iters", type=int, default=5000)
    p.add_argument("--signflip-iters", type=int, default=10000)
    p.add_argument("--beat-fixed-margin", type=float, default=0.005)
    return p.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def choose_cache(policy: str) -> tuple[Path, Path]:
    if policy == "baseline_corrected":
        if CACHE_BASELINE_CORRECTED.exists() and INDEX_BASELINE_CORRECTED.exists():
            return CACHE_BASELINE_CORRECTED, INDEX_BASELINE_CORRECTED
        print("[WARN] baseline-corrected cache/index not found; falling back to raw cache.", flush=True)
    return CACHE_RAW, INDEX_RAW


def normalize_stimulus_id(x: Any) -> str:
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s


def find_score_column(df: pd.DataFrame, target: str) -> str:
    candidates = [f"{target}_score", target, f"y_{target}", f"{target}_rating"]
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"Could not find score column for {target}. Available columns: {list(df.columns)}")


def load_index(index_path: Path, target: str) -> tuple[pd.DataFrame, str]:
    if not index_path.exists():
        raise FileNotFoundError(index_path)

    df = pd.read_csv(index_path)
    if "subject_id" not in df.columns:
        for c in ["subject", "participant_id", "participant", "test_subject"]:
            if c in df.columns:
                df["subject_id"] = df[c]
                break
    if "subject_id" not in df.columns:
        raise KeyError(f"Missing subject_id column. Available columns: {list(df.columns)}")

    if "stimulus_id" not in df.columns:
        for c in ["stimulus", "trial_id", "trial", "image_id", "video_id"]:
            if c in df.columns:
                df["stimulus_id"] = df[c]
                break
    if "stimulus_id" not in df.columns:
        raise KeyError(f"Missing stimulus_id column. Available columns: {list(df.columns)}")

    if "cache_row" not in df.columns:
        df["cache_row"] = np.arange(len(df), dtype=np.int64)

    score_col = find_score_column(df, target)

    out = df.copy()
    out["subject_id"] = out["subject_id"].astype(int)
    out["stimulus_key"] = out["stimulus_id"].map(normalize_stimulus_id)
    out["cache_row"] = out["cache_row"].astype(int)
    out[score_col] = pd.to_numeric(out[score_col], errors="coerce")
    out = out.dropna(subset=[score_col]).copy()
    out = out.sort_values(["subject_id", "stimulus_key", "cache_row"]).reset_index(drop=True)
    return out, score_col


def load_reference(target: str) -> dict[str, Any] | None:
    if not REFERENCE_05AJB.exists():
        return None
    try:
        df = pd.read_csv(REFERENCE_05AJB)
    except Exception:
        return None
    if "target" not in df.columns:
        return None
    rows = df[df["target"].astype(str) == target]
    if rows.empty:
        return None
    r = rows.iloc[0].to_dict()
    return {
        "source": str(REFERENCE_05AJB.relative_to(ROOT)),
        "feature_block": r.get("feature_block"),
        "model": r.get("model"),
        "quantile": float(r.get("quantile", 0.75)),
        "abs_residual_threshold": float(r.get("abs_residual_threshold", math.nan)),
        "baseline_residual_rmse": float(r.get("baseline_residual_rmse", math.nan)),
        "fixed_model_residual_rmse": float(r.get("model_residual_rmse", math.nan)),
        "fixed_pooled_lift_vs_zero": float(r.get("pooled_lift_vs_zero_residual_rmse", math.nan)),
        "fixed_residual_pearson": float(r.get("residual_pearson", math.nan)),
        "fixed_wins": int(r.get("wins", 0)),
        "fixed_losses": int(r.get("losses", 0)),
        "fixed_win_margin": int(r.get("win_margin", 0)),
        "fixed_decision": r.get("decision"),
    }


def make_folds(subjects: list[int], seeds: list[int], val_subject_count: int, max_test_subjects: int) -> list[FoldSpec]:
    subjects = sorted(int(s) for s in subjects)
    test_subjects = subjects[: max_test_subjects] if max_test_subjects and max_test_subjects > 0 else subjects
    folds: list[FoldSpec] = []

    for seed in seeds:
        for test_subject in test_subjects:
            remaining = [s for s in subjects if s != test_subject]
            rng = np.random.default_rng(seed * 100003 + test_subject)
            val_n = min(max(1, val_subject_count), max(1, len(remaining) // 3))
            val_subjects = sorted(int(s) for s in rng.choice(np.asarray(remaining), size=val_n, replace=False))
            val_set = set(val_subjects)
            train_subjects = [s for s in remaining if s not in val_set]
            folds.append(FoldSpec(seed=seed, test_subject=test_subject, train_subjects=train_subjects, val_subjects=val_subjects))

    return folds


def compute_stimulus_mean(df: pd.DataFrame, score_col: str, train_subjects: list[int]) -> dict[str, float]:
    train = df[df["subject_id"].isin(train_subjects)].copy()
    return train.groupby("stimulus_key")[score_col].mean().astype(float).to_dict()


def add_deviation(df: pd.DataFrame, score_col: str, stim_mean: dict[str, float]) -> pd.DataFrame:
    out = df.copy()
    out["train_stimulus_mean"] = out["stimulus_key"].map(stim_mean)
    out = out.dropna(subset=["train_stimulus_mean"]).copy()
    out["true_deviation"] = out[score_col].astype(float) - out["train_stimulus_mean"].astype(float)
    return out


def compute_eeg_norm(cache_path: Path, cache_rows: np.ndarray, chunk_size: int = 128) -> tuple[np.ndarray, np.ndarray]:
    cache = np.load(cache_path, mmap_mode="r")
    rows = np.asarray(cache_rows, dtype=np.int64)
    rows = np.unique(rows)
    rows.sort()

    if rows.size == 0:
        raise ValueError("No rows for EEG normalization.")

    sample = np.asarray(cache[int(rows[0])], dtype=np.float32)
    if sample.ndim != 2:
        raise ValueError(f"Expected EEG sample [C,T], got {sample.shape}")
    C, _ = sample.shape

    sums = np.zeros(C, dtype=np.float64)
    sumsqs = np.zeros(C, dtype=np.float64)
    count = 0

    for start in range(0, len(rows), chunk_size):
        chunk_rows = rows[start : start + chunk_size]
        arr = np.asarray(cache[chunk_rows], dtype=np.float64)
        sums += arr.sum(axis=(0, 2))
        sumsqs += np.square(arr).sum(axis=(0, 2))
        count += arr.shape[0] * arr.shape[2]

    mean = sums / max(count, 1)
    var = sumsqs / max(count, 1) - np.square(mean)
    std = np.sqrt(np.maximum(var, 1e-6))
    return mean.astype(np.float32), std.astype(np.float32)


class ResidualEEGDataset(Dataset):
    def __init__(
        self,
        rows: pd.DataFrame,
        cache_path: Path,
        eeg_mean: np.ndarray,
        eeg_std: np.ndarray,
        target_mean: float,
        target_std: float,
        high_threshold: float,
        high_weight: float,
    ) -> None:
        self.rows = rows.reset_index(drop=True).copy()
        self.cache = np.load(cache_path, mmap_mode="r")
        self.eeg_mean = eeg_mean.astype(np.float32)
        self.eeg_std = eeg_std.astype(np.float32)
        self.target_mean = float(target_mean)
        self.target_std = float(max(target_std, 1e-6))
        self.high_threshold = float(high_threshold)
        self.high_weight = float(high_weight)

        if len(self.rows) == 0:
            raise ValueError("Empty dataset.")

    def __len__(self) -> int:
        return int(len(self.rows))

    def __getitem__(self, idx: int) -> dict[str, Any]:
        r = self.rows.iloc[idx]
        cache_row = int(r["cache_row"])
        eeg = np.asarray(self.cache[cache_row], dtype=np.float32)
        eeg = (eeg - self.eeg_mean[:, None]) / self.eeg_std[:, None]

        dev = float(r["true_deviation"])
        y_z = (dev - self.target_mean) / self.target_std
        is_high = float(abs(dev) >= self.high_threshold)
        weight = 1.0 + self.high_weight * is_high

        return {
            "eeg": torch.from_numpy(eeg),
            "target_z": torch.tensor(y_z, dtype=torch.float32),
            "dev": torch.tensor(dev, dtype=torch.float32),
            "score": torch.tensor(float(r["score_value"]), dtype=torch.float32),
            "train_stimulus_mean": torch.tensor(float(r["train_stimulus_mean"]), dtype=torch.float32),
            "is_high": torch.tensor(is_high, dtype=torch.float32),
            "weight": torch.tensor(weight, dtype=torch.float32),
            "subject_id": torch.tensor(int(r["subject_id"]), dtype=torch.long),
            "stimulus_key": str(r["stimulus_key"]),
            "cache_row": torch.tensor(cache_row, dtype=torch.long),
        }


class PreviousModelResidualRegressor(nn.Module):
    def __init__(self, dropout: float = 0.10, head_dropout: float = 0.25) -> None:
        super().__init__()
        self.encoder = EEGSegmentEncoder(
            C=32,
            sampling_rate=128,
            window_sec=5.0,
            modelsize="lite",
            dropout=dropout,
            norm_kind="gn",
            stem_fusion="concat",
            channel_pos_mode="learnable",
            channel_mixer="mha",
            use_spectral_branch=False,
        )
        D = int(self.encoder.Dembed)

        self.reg_head = nn.Sequential(
            nn.LayerNorm(D),
            nn.Linear(D, 128),
            nn.GELU(),
            nn.Dropout(head_dropout),
            nn.Linear(128, 1),
        )
        self.sign_head = nn.Sequential(
            nn.LayerNorm(D),
            nn.Linear(D, 128),
            nn.GELU(),
            nn.Dropout(head_dropout),
            nn.Linear(128, 1),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        z, _ = self.encoder(x_eeg=x, return_attn=False)
        pred_z = self.reg_head(z).squeeze(-1)
        sign_logit = self.sign_head(z).squeeze(-1)
        return pred_z, sign_logit


def rmse(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if a.size == 0:
        return math.nan
    return float(np.sqrt(np.mean(np.square(a - b))))


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    ok = np.isfinite(a) & np.isfinite(b)
    a = a[ok]
    b = b[ok]
    if a.size < 3 or np.std(a) <= 1e-12 or np.std(b) <= 1e-12:
        return math.nan
    return float(np.corrcoef(a, b)[0, 1])


def bootstrap_ci(values: np.ndarray, iters: int, seed: int) -> tuple[float, float]:
    x = np.asarray(values, dtype=np.float64)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return math.nan, math.nan
    if x.size == 1:
        return float(x[0]), float(x[0])
    rng = np.random.default_rng(seed)
    means = np.empty(iters, dtype=np.float64)
    n = x.size
    for i in range(iters):
        means[i] = rng.choice(x, size=n, replace=True).mean()
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def signflip_p_one_sided_mean_gt_zero(values: np.ndarray, iters: int, seed: int) -> float:
    x = np.asarray(values, dtype=np.float64)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return math.nan
    obs = float(x.mean())
    if obs <= 0:
        return 1.0
    rng = np.random.default_rng(seed)
    absx = np.abs(x)
    count = 0
    for _ in range(iters):
        signs = rng.choice(np.asarray([-1.0, 1.0]), size=absx.size, replace=True)
        if float((signs * absx).mean()) >= obs:
            count += 1
    return float((count + 1) / (iters + 1))


def train_one_fold(
    args: argparse.Namespace,
    fold: FoldSpec,
    base_df: pd.DataFrame,
    score_col: str,
    cache_path: Path,
    device: torch.device,
    reference: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    set_seed(fold.seed)

    stim_mean = compute_stimulus_mean(base_df, score_col, fold.train_subjects)

    train_rows = add_deviation(base_df[base_df["subject_id"].isin(fold.train_subjects)], score_col, stim_mean)
    val_rows = add_deviation(base_df[base_df["subject_id"].isin(fold.val_subjects)], score_col, stim_mean)
    test_rows = add_deviation(base_df[base_df["subject_id"] == fold.test_subject], score_col, stim_mean)

    train_rows = train_rows.rename(columns={score_col: "score_value"})
    val_rows = val_rows.rename(columns={score_col: "score_value"})
    test_rows = test_rows.rename(columns={score_col: "score_value"})

    if len(train_rows) == 0 or len(val_rows) == 0 or len(test_rows) == 0:
        raise ValueError(f"Empty split for fold test_subject={fold.test_subject}")

    train_devs = train_rows["true_deviation"].to_numpy(dtype=np.float64)
    train_threshold = float(np.quantile(np.abs(train_devs), 0.75))
    ref_threshold = None
    if reference is not None:
        t = reference.get("abs_residual_threshold")
        if t is not None and np.isfinite(float(t)):
            ref_threshold = float(t)

    high_threshold = train_threshold
    threshold_source = "train_q75"
    if args.threshold_source == "confirmatory_or_train" and ref_threshold is not None:
        high_threshold = ref_threshold
        threshold_source = "05ajb_confirmatory"

    target_mean = float(train_devs.mean())
    target_std = float(train_devs.std(ddof=0))
    if target_std < 1e-6:
        target_std = 1.0

    eeg_mean, eeg_std = compute_eeg_norm(cache_path, train_rows["cache_row"].to_numpy(dtype=np.int64))

    train_ds = ResidualEEGDataset(train_rows, cache_path, eeg_mean, eeg_std, target_mean, target_std, high_threshold, args.high_weight)
    val_ds = ResidualEEGDataset(val_rows, cache_path, eeg_mean, eeg_std, target_mean, target_std, high_threshold, args.high_weight)
    test_ds = ResidualEEGDataset(test_rows, cache_path, eeg_mean, eeg_std, target_mean, target_std, high_threshold, args.high_weight)

    generator = torch.Generator()
    generator.manual_seed(fold.seed * 1009 + fold.test_subject)

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda"),
        generator=generator,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda"),
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda"),
    )

    model = PreviousModelResidualRegressor(dropout=args.dropout, head_dropout=args.head_dropout).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    best_state = None
    best_monitor = math.inf
    best_epoch = 0
    bad_epochs = 0
    history: list[dict[str, Any]] = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        for batch in train_loader:
            x = batch["eeg"].to(device=device, dtype=torch.float32)
            y_z = batch["target_z"].to(device=device, dtype=torch.float32)
            dev = batch["dev"].to(device=device, dtype=torch.float32)
            weight = batch["weight"].to(device=device, dtype=torch.float32)

            optimizer.zero_grad(set_to_none=True)
            pred_z, sign_logit = model(x)

            reg_loss = F.smooth_l1_loss(pred_z, y_z, reduction="none")
            sign_target = (dev > 0).float()
            sign_loss = F.binary_cross_entropy_with_logits(sign_logit, sign_target, reduction="none")
            loss = ((reg_loss + args.sign_loss_weight * sign_loss) * weight).mean()

            loss.backward()
            if args.grad_clip and args.grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=args.grad_clip)
            optimizer.step()
            losses.append(float(loss.detach().cpu().item()))

        val_pred = predict_rows(model, val_loader, device, target_mean, target_std, fold, split="val")
        val_metrics_all = metrics_from_predictions(pd.DataFrame(val_pred), high_only=False)
        val_metrics_high = metrics_from_predictions(pd.DataFrame(val_pred), high_only=True)
        monitor = val_metrics_high["model_residual_rmse"]
        if not np.isfinite(monitor):
            monitor = val_metrics_all["model_residual_rmse"]

        history.append({
            "epoch": epoch,
            "train_loss_mean": float(np.mean(losses)) if losses else math.nan,
            "val_model_residual_rmse_all": val_metrics_all["model_residual_rmse"],
            "val_model_residual_rmse_high": val_metrics_high["model_residual_rmse"],
            "val_lift_vs_zero_high": val_metrics_high["lift_vs_zero_residual_rmse"],
        })

        if monitor < best_monitor - 1e-5:
            best_monitor = float(monitor)
            best_epoch = int(epoch)
            best_state = copy.deepcopy(model.state_dict())
            bad_epochs = 0
        else:
            bad_epochs += 1

        print(
            f"[fold] seed={fold.seed} test_subject={fold.test_subject} epoch={epoch}/{args.epochs} "
            f"loss={np.mean(losses):.5f} val_high_rmse={val_metrics_high['model_residual_rmse']:.5f} "
            f"val_high_lift={val_metrics_high['lift_vs_zero_residual_rmse']:.5f}",
            flush=True,
        )

        if bad_epochs >= args.patience:
            break

    if best_state is not None:
        model.load_state_dict(best_state)

    test_pred = predict_rows(model, test_loader, device, target_mean, target_std, fold, split="test")

    fold_info = {
        "seed": fold.seed,
        "test_subject": fold.test_subject,
        "train_subjects": fold.train_subjects,
        "val_subjects": fold.val_subjects,
        "train_rows": int(len(train_rows)),
        "val_rows": int(len(val_rows)),
        "test_rows": int(len(test_rows)),
        "train_dev_mean": target_mean,
        "train_dev_std": target_std,
        "high_threshold": high_threshold,
        "threshold_source": threshold_source,
        "best_epoch": best_epoch,
        "best_monitor": best_monitor,
        "epoch_history": history,
    }
    return test_pred, fold_info


def predict_rows(
    model: nn.Module,
    loader: DataLoader,
    device: torch.device,
    target_mean: float,
    target_std: float,
    fold: FoldSpec,
    split: str,
) -> list[dict[str, Any]]:
    model.eval()
    rows: list[dict[str, Any]] = []
    with torch.no_grad():
        for batch in loader:
            x = batch["eeg"].to(device=device, dtype=torch.float32)
            pred_z, sign_logit = model(x)
            pred_dev = pred_z.detach().cpu().numpy().astype(np.float64) * target_std + target_mean
            sign_prob = torch.sigmoid(sign_logit).detach().cpu().numpy().astype(np.float64)

            dev = batch["dev"].detach().cpu().numpy().astype(np.float64)
            score = batch["score"].detach().cpu().numpy().astype(np.float64)
            stim_mean = batch["train_stimulus_mean"].detach().cpu().numpy().astype(np.float64)
            is_high = batch["is_high"].detach().cpu().numpy().astype(np.float64)
            subject_ids = batch["subject_id"].detach().cpu().numpy().astype(int)
            cache_rows = batch["cache_row"].detach().cpu().numpy().astype(int)
            stimuli = list(batch["stimulus_key"])

            for i in range(len(dev)):
                rows.append({
                    "seed": int(fold.seed),
                    "split": split,
                    "test_subject": int(fold.test_subject),
                    "subject_id": int(subject_ids[i]),
                    "stimulus_id": str(stimuli[i]),
                    "cache_row": int(cache_rows[i]),
                    "y_true_score": float(score[i]),
                    "train_stimulus_mean": float(stim_mean[i]),
                    "true_deviation": float(dev[i]),
                    "pred_deviation": float(pred_dev[i]),
                    "pred_score": float(stim_mean[i] + pred_dev[i]),
                    "pred_sign_prob_positive": float(sign_prob[i]),
                    "is_high_disagreement": bool(is_high[i] >= 0.5),
                })
    return rows


def metrics_from_predictions(pred: pd.DataFrame, high_only: bool) -> dict[str, Any]:
    if pred.empty:
        return {
            "n": 0,
            "zero_residual_rmse": math.nan,
            "model_residual_rmse": math.nan,
            "lift_vs_zero_residual_rmse": math.nan,
            "residual_pearson": math.nan,
            "residual_sign_acc": math.nan,
        }
    x = pred.copy()
    if high_only:
        x = x[x["is_high_disagreement"].astype(bool)].copy()
    if x.empty:
        return {
            "n": 0,
            "zero_residual_rmse": math.nan,
            "model_residual_rmse": math.nan,
            "lift_vs_zero_residual_rmse": math.nan,
            "residual_pearson": math.nan,
            "residual_sign_acc": math.nan,
        }

    true_dev = x["true_deviation"].to_numpy(dtype=np.float64)
    pred_dev = x["pred_deviation"].to_numpy(dtype=np.float64)
    zero = np.zeros_like(true_dev)

    zero_rmse = rmse(true_dev, zero)
    model_rmse = rmse(true_dev, pred_dev)
    sign_true = true_dev > 0
    sign_pred = pred_dev > 0

    return {
        "n": int(len(x)),
        "zero_residual_rmse": zero_rmse,
        "model_residual_rmse": model_rmse,
        "lift_vs_zero_residual_rmse": float(zero_rmse - model_rmse),
        "residual_pearson": pearson(true_dev, pred_dev),
        "residual_sign_acc": float(np.mean(sign_true == sign_pred)) if len(x) else math.nan,
    }


def subject_stats_from_predictions(pred: pd.DataFrame, high_only: bool) -> pd.DataFrame:
    x = pred.copy()
    if high_only:
        x = x[x["is_high_disagreement"].astype(bool)].copy()
    if x.empty:
        return pd.DataFrame()

    rows = []
    for (subject_id, seed), g in x.groupby(["subject_id", "seed"]):
        true_dev = g["true_deviation"].to_numpy(dtype=np.float64)
        pred_dev = g["pred_deviation"].to_numpy(dtype=np.float64)
        zero = np.zeros_like(true_dev)
        zero_rmse = rmse(true_dev, zero)
        model_rmse = rmse(true_dev, pred_dev)
        rows.append({
            "subject_id": int(subject_id),
            "seed": int(seed),
            "n": int(len(g)),
            "zero_residual_rmse": zero_rmse,
            "model_residual_rmse": model_rmse,
            "improvement_zero_minus_model_rmse": float(zero_rmse - model_rmse),
            "residual_pearson": pearson(true_dev, pred_dev),
        })

    per_seed = pd.DataFrame(rows)
    if per_seed.empty:
        return per_seed

    agg = (
        per_seed.groupby("subject_id", as_index=False)
        .agg(
            n=("n", "sum"),
            zero_residual_rmse=("zero_residual_rmse", "mean"),
            model_residual_rmse=("model_residual_rmse", "mean"),
            improvement_zero_minus_model_rmse=("improvement_zero_minus_model_rmse", "mean"),
            residual_pearson=("residual_pearson", "mean"),
        )
        .sort_values("improvement_zero_minus_model_rmse", ascending=False)
    )
    return agg


def summarize_decision(
    args: argparse.Namespace,
    pred: pd.DataFrame,
    fold_infos: list[dict[str, Any]],
    reference: dict[str, Any] | None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    all_metrics = metrics_from_predictions(pred, high_only=False)
    high_metrics = metrics_from_predictions(pred, high_only=True)
    subj = subject_stats_from_predictions(pred, high_only=True)

    if subj.empty:
        improvements = np.asarray([], dtype=np.float64)
        wins = losses = win_margin = 0
    else:
        improvements = subj["improvement_zero_minus_model_rmse"].to_numpy(dtype=np.float64)
        wins = int(np.sum(improvements > 1e-12))
        losses = int(np.sum(improvements < -1e-12))
        win_margin = int(wins - losses)

    ci_low, ci_high = bootstrap_ci(improvements, args.bootstrap_iters, seed=911)
    signflip_p = signflip_p_one_sided_mean_gt_zero(improvements, args.signflip_iters, seed=912)
    mean_improvement = float(np.mean(improvements)) if improvements.size else math.nan

    fixed_lift = math.nan
    fixed_rmse = math.nan
    fixed_pearson = math.nan
    fixed_name = None
    fixed_block = None
    if reference is not None:
        fixed_lift = float(reference.get("fixed_pooled_lift_vs_zero", math.nan))
        fixed_rmse = float(reference.get("fixed_model_residual_rmse", math.nan))
        fixed_pearson = float(reference.get("fixed_residual_pearson", math.nan))
        fixed_name = reference.get("model")
        fixed_block = reference.get("feature_block")

    deep_lift = float(high_metrics["lift_vs_zero_residual_rmse"])
    deep_rmse = float(high_metrics["model_residual_rmse"])
    deep_pearson = float(high_metrics["residual_pearson"])

    beats_zero = bool(np.isfinite(deep_lift) and deep_lift > 0.02)
    beats_fixed = False
    if np.isfinite(fixed_lift):
        beats_fixed = bool(deep_lift >= fixed_lift + args.beat_fixed_margin)
    elif np.isfinite(fixed_rmse):
        beats_fixed = bool(deep_rmse <= fixed_rmse - args.beat_fixed_margin)

    stable_subjects = bool(np.isfinite(ci_low) and ci_low > 0 and signflip_p < 0.05 and win_margin >= 3)
    pearson_ok = bool(np.isfinite(deep_pearson) and deep_pearson > 0.10)

    passes_gate = bool(beats_zero and beats_fixed and stable_subjects and pearson_ok)

    if passes_gate:
        decision = "GO_PREVIOUS_DEEP_MODEL_BEATS_FIXED_FEATURE_HIGH_DISAGREEMENT"
        reason = "previous EEGSegmentEncoder backbone beats zero-residual and fixed EEG-bandpower high-disagreement reference with subject-level support"
    else:
        failed = []
        if not beats_zero:
            failed.append("deep residual lift vs zero is <= 0.02")
        if not beats_fixed:
            failed.append("deep model does not beat fixed EEG-bandpower 05ajb reference")
        if not stable_subjects:
            failed.append("paired subject-level evidence is not stable")
        if not pearson_ok:
            failed.append("residual Pearson is <= 0.10")
        decision = "NO_GO_PREVIOUS_DEEP_MODEL_UNDER_LOSO_HIGH_DISAGREEMENT"
        reason = "; ".join(failed)

    decision_row = {
        "target": args.target,
        "decision": decision,
        "input_cache_policy": args.cache_policy,
        "architecture": "previous_EEGSegmentEncoder_lite_plus_residual_head",
        "evaluation_subset": "high_disagreement_q75",
        "n_predictions_high": high_metrics["n"],
        "n_subjects": int(subj["subject_id"].nunique()) if not subj.empty else 0,
        "zero_residual_rmse_high": high_metrics["zero_residual_rmse"],
        "deep_model_residual_rmse_high": high_metrics["model_residual_rmse"],
        "deep_lift_vs_zero_residual_rmse_high": high_metrics["lift_vs_zero_residual_rmse"],
        "deep_residual_pearson_high": high_metrics["residual_pearson"],
        "deep_residual_sign_acc_high": high_metrics["residual_sign_acc"],
        "fixed_reference_block": fixed_block,
        "fixed_reference_model": fixed_name,
        "fixed_reference_residual_rmse": fixed_rmse,
        "fixed_reference_lift_vs_zero": fixed_lift,
        "fixed_reference_residual_pearson": fixed_pearson,
        "deep_minus_fixed_lift": float(deep_lift - fixed_lift) if np.isfinite(fixed_lift) else math.nan,
        "mean_subject_improvement_zero_minus_deep": mean_improvement,
        "ci95_low_mean_subject_improvement": ci_low,
        "ci95_high_mean_subject_improvement": ci_high,
        "signflip_p_one_sided_mean_gt_zero": signflip_p,
        "wins_vs_zero": wins,
        "losses_vs_zero": losses,
        "win_margin_vs_zero": win_margin,
        "passes_06a1_gate": passes_gate,
        "reason": reason,
    }

    fold_metrics_rows = []
    for info in fold_infos:
        fold_pred = pred[(pred["seed"] == info["seed"]) & (pred["test_subject"] == info["test_subject"])]
        fm_all = metrics_from_predictions(fold_pred, high_only=False)
        fm_high = metrics_from_predictions(fold_pred, high_only=True)
        fold_metrics_rows.append({
            "seed": info["seed"],
            "test_subject": info["test_subject"],
            "train_rows": info["train_rows"],
            "val_rows": info["val_rows"],
            "test_rows": info["test_rows"],
            "high_threshold": info["high_threshold"],
            "threshold_source": info["threshold_source"],
            "best_epoch": info["best_epoch"],
            "best_monitor": info["best_monitor"],
            "test_high_n": fm_high["n"],
            "test_all_model_rmse": fm_all["model_residual_rmse"],
            "test_high_zero_rmse": fm_high["zero_residual_rmse"],
            "test_high_model_rmse": fm_high["model_residual_rmse"],
            "test_high_lift_vs_zero": fm_high["lift_vs_zero_residual_rmse"],
            "test_high_pearson": fm_high["residual_pearson"],
        })

    payload = {
        "args": vars(args),
        "reference_05ajb": reference,
        "decision": decision_row,
        "all_metrics": all_metrics,
        "high_metrics": high_metrics,
        "fold_count": len(fold_infos),
    }

    return pd.DataFrame([decision_row]), pd.DataFrame(fold_metrics_rows), payload


def md_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df is None or df.empty:
        return "_empty_\n"
    x = df.head(max_rows).copy()
    cols = list(x.columns)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in x.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                if math.isnan(v):
                    vals.append("")
                else:
                    vals.append(f"{v:.6g}")
            else:
                vals.append(str(v).replace("|", "/"))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def write_outputs(
    args: argparse.Namespace,
    decision: pd.DataFrame,
    fold_metrics: pd.DataFrame,
    subject_stats: pd.DataFrame,
    predictions: pd.DataFrame,
    payload: dict[str, Any],
) -> None:
    suffix = "_smoke_current" if args.smoke else "_current"
    prefix = ROCA / f"{OUT_PREFIX}{suffix}"

    decision_path = Path(str(prefix) + "_decision_table.csv")
    fold_path = Path(str(prefix) + "_fold_metrics.csv")
    subject_path = Path(str(prefix) + "_subject_stats.csv")
    pred_path = Path(str(prefix) + "_predictions.csv")
    json_path = Path(str(prefix) + ".json")
    md_path = Path(str(prefix) + ".md")

    decision.to_csv(decision_path, index=False)
    fold_metrics.to_csv(fold_path, index=False)
    subject_stats.to_csv(subject_path, index=False)
    predictions.to_csv(pred_path, index=False)

    payload2 = dict(payload)
    payload2["output_files"] = {
        "decision_table": str(decision_path.relative_to(ROOT)),
        "fold_metrics": str(fold_path.relative_to(ROOT)),
        "subject_stats": str(subject_path.relative_to(ROOT)),
        "predictions": str(pred_path.relative_to(ROOT)),
    }
    json_path.write_text(json.dumps(payload2, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    lines = []
    lines.append("# I-DARE 06a1 Previous-Model Deep Residual Probe\n\n")
    lines.append("This run reuses the previous `EEGSegmentEncoder` backbone and replaces the binary classification head with a residual/deviation regression head.\n\n")
    lines.append("## Decision\n\n")
    lines.append(md_table(decision))
    lines.append("\n## Fold metrics preview\n\n")
    lines.append(md_table(fold_metrics.sort_values("test_high_lift_vs_zero", ascending=False), max_rows=25))
    lines.append("\n## Subject stats preview\n\n")
    if not subject_stats.empty:
        lines.append(md_table(subject_stats.sort_values("improvement_zero_minus_deep_rmse", ascending=False), max_rows=25))
    else:
        lines.append("_empty_\n")
    lines.append("\n## Interpretation\n\n")
    row = decision.iloc[0].to_dict()
    if bool(row.get("passes_06a1_gate")):
        lines.append("The previous deep EEG backbone produced actionable high-disagreement arousal residual signal beyond the fixed-feature reference. Next step: bridge/gating against locked B2.\n")
    else:
        lines.append("The previous deep EEG backbone did not beat the fixed-feature high-disagreement reference under the current LOSO residual gate. This supports the hypothesis that the bottleneck is not merely architecture design.\n")

    md_path.write_text("".join(lines), encoding="utf-8")

    print("\nROCA step 06a1 completed.")
    for p in [md_path, json_path, decision_path, fold_path, subject_path, pred_path]:
        print(f"wrote: {p}")

    print("\nDecision table:")
    print(decision.to_string(index=False))


def main() -> None:
    args = parse_args()
    start = time.perf_counter()

    cache_path, index_path = choose_cache(args.cache_policy)
    if not cache_path.exists():
        raise FileNotFoundError(cache_path)
    if not index_path.exists():
        raise FileNotFoundError(index_path)

    device = torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda:0")
    print(f"[INFO] device={device}")
    if device.type == "cuda":
        print(f"[INFO] gpu={torch.cuda.get_device_name(0)}")
        torch.backends.cudnn.benchmark = True

    base_df, score_col = load_index(index_path, args.target)
    cache = np.load(cache_path, mmap_mode="r")
    print(f"[INFO] cache={cache_path} shape={cache.shape}")
    print(f"[INFO] index={index_path} rows={len(base_df)} score_col={score_col}")

    if len(cache) < int(base_df["cache_row"].max()) + 1:
        raise ValueError("Cache rows and index cache_row values are inconsistent.")

    subjects = sorted(int(s) for s in base_df["subject_id"].unique())
    reference = load_reference(args.target)
    if reference:
        print(f"[INFO] loaded 05ajb reference: {reference}")
    else:
        print("[WARN] no 05ajb reference found; using train q75 threshold and zero-residual comparator only.")

    folds = make_folds(
        subjects=subjects,
        seeds=args.seeds,
        val_subject_count=args.val_subject_count,
        max_test_subjects=args.max_test_subjects,
    )

    if args.smoke:
        folds = folds[: max(1, min(len(folds), args.max_test_subjects or 4))]
        print(f"[INFO] smoke mode folds={len(folds)}")

    all_predictions: list[dict[str, Any]] = []
    fold_infos: list[dict[str, Any]] = []

    for i, fold in enumerate(folds, start=1):
        print("\n" + "=" * 90)
        print(f"[FOLD {i}/{len(folds)}] seed={fold.seed} test_subject={fold.test_subject}")
        print("=" * 90)

        preds, info = train_one_fold(
            args=args,
            fold=fold,
            base_df=base_df,
            score_col=score_col,
            cache_path=cache_path,
            device=device,
            reference=reference,
        )
        all_predictions.extend(preds)
        fold_infos.append(info)

    pred_df = pd.DataFrame(all_predictions)
    subject_stats = subject_stats_from_predictions(pred_df, high_only=True)
    if not subject_stats.empty:
        subject_stats = subject_stats.rename(columns={
            "model_residual_rmse": "deep_model_residual_rmse",
            "improvement_zero_minus_model_rmse": "improvement_zero_minus_deep_rmse",
        })

    decision, fold_metrics, payload = summarize_decision(args, pred_df, fold_infos, reference)
    payload["elapsed_sec"] = float(time.perf_counter() - start)

    write_outputs(args, decision, fold_metrics, subject_stats, pred_df, payload)


if __name__ == "__main__":
    main()
