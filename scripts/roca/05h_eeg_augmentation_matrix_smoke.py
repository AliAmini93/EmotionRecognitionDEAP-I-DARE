#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import importlib.util


ROOT = Path(__file__).resolve().parents[2]
ROCA_DIR = ROOT / "docs" / "roca"
BASE_SCRIPT_05C = ROOT / "scripts" / "roca" / "05c_eeg_residual_training_stabilized_smoke.py"

OUT_MD = ROCA_DIR / "eeg_augmentation_matrix_smoke_current.md"
OUT_JSON = ROCA_DIR / "eeg_augmentation_matrix_smoke_current.json"
OUT_PRED_CSV = ROCA_DIR / "eeg_augmentation_matrix_smoke_predictions_current.csv"
OUT_MAIN_CSV = ROCA_DIR / "eeg_augmentation_matrix_smoke_main_metrics_current.csv"
OUT_SUBSET_CSV = ROCA_DIR / "eeg_augmentation_matrix_smoke_subset_metrics_current.csv"
OUT_FOLD_CSV = ROCA_DIR / "eeg_augmentation_matrix_smoke_fold_summary_current.csv"
OUT_HISTORY_CSV = ROCA_DIR / "eeg_augmentation_matrix_smoke_history_current.csv"

MODEL_NAME = "eeg_bc_residual_huber_norm_augmented_smoke"


def load_base_module():
    if not BASE_SCRIPT_05C.exists():
        raise FileNotFoundError(BASE_SCRIPT_05C)
    spec = importlib.util.spec_from_file_location("roca_05c_base_aug", BASE_SCRIPT_05C)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec for {BASE_SCRIPT_05C}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["roca_05c_base_aug"] = module
    spec.loader.exec_module(module)
    return module


base = load_base_module()


AUGMENTATION_CONFIGS = {
    "none": {
        "description": "No augmentation control",
        "gaussian_std": 0.0,
        "gain_jitter": 0.0,
        "time_shift_max": 0,
        "time_mask_frac": 0.0,
        "channel_drop_prob": 0.0,
    },
    "gaussian_0p05": {
        "description": "Additive Gaussian noise, std=0.05 in normalized EEG units",
        "gaussian_std": 0.05,
        "gain_jitter": 0.0,
        "time_shift_max": 0,
        "time_mask_frac": 0.0,
        "channel_drop_prob": 0.0,
    },
    "gaussian_0p10": {
        "description": "Additive Gaussian noise, std=0.10 in normalized EEG units",
        "gaussian_std": 0.10,
        "gain_jitter": 0.0,
        "time_shift_max": 0,
        "time_mask_frac": 0.0,
        "channel_drop_prob": 0.0,
    },
    "gain_0p10": {
        "description": "Global amplitude gain jitter, gain in [0.90, 1.10]",
        "gaussian_std": 0.0,
        "gain_jitter": 0.10,
        "time_shift_max": 0,
        "time_mask_frac": 0.0,
        "channel_drop_prob": 0.0,
    },
    "gaussian_0p05_gain_0p10": {
        "description": "Gaussian noise std=0.05 plus global gain jitter 0.10",
        "gaussian_std": 0.05,
        "gain_jitter": 0.10,
        "time_shift_max": 0,
        "time_mask_frac": 0.0,
        "channel_drop_prob": 0.0,
    },
    "gaussian_0p05_shift16": {
        "description": "Gaussian noise std=0.05 plus random time shift up to 16 samples",
        "gaussian_std": 0.05,
        "gain_jitter": 0.0,
        "time_shift_max": 16,
        "time_mask_frac": 0.0,
        "channel_drop_prob": 0.0,
    },
}


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
    p.add_argument(
        "--configs",
        type=str,
        default="all",
        help="Comma-separated augmentation configs or 'all'.",
    )
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


def selected_configs(config_arg: str) -> list[str]:
    if config_arg.strip().lower() == "all":
        return list(AUGMENTATION_CONFIGS.keys())

    names = [x.strip() for x in config_arg.split(",") if x.strip()]
    bad = [x for x in names if x not in AUGMENTATION_CONFIGS]
    if bad:
        raise KeyError(f"Unknown augmentation config(s): {bad}. Available: {sorted(AUGMENTATION_CONFIGS)}")
    return names


class AugmentedEEGResidualDataset(Dataset):
    def __init__(self, x: np.ndarray, y_scaled: np.ndarray, aug_cfg: dict[str, Any] | None, train: bool):
        self.x = np.asarray(x, dtype=np.float32)
        self.y = np.asarray(y_scaled, dtype=np.float32)
        self.aug_cfg = aug_cfg or {}
        self.train = bool(train)

    def __len__(self):
        return int(len(self.y))

    def _augment(self, x: torch.Tensor) -> torch.Tensor:
        if not self.train:
            return x

        cfg = self.aug_cfg

        gain_jitter = float(cfg.get("gain_jitter", 0.0) or 0.0)
        if gain_jitter > 0:
            gain = 1.0 + (torch.rand((), dtype=x.dtype) * 2.0 - 1.0) * gain_jitter
            x = x * gain

        time_shift_max = int(cfg.get("time_shift_max", 0) or 0)
        if time_shift_max > 0:
            shift = int(torch.randint(-time_shift_max, time_shift_max + 1, (1,)).item())
            if shift != 0:
                x = torch.roll(x, shifts=shift, dims=-1)

        gaussian_std = float(cfg.get("gaussian_std", 0.0) or 0.0)
        if gaussian_std > 0:
            x = x + torch.randn_like(x) * gaussian_std

        time_mask_frac = float(cfg.get("time_mask_frac", 0.0) or 0.0)
        if time_mask_frac > 0:
            t = int(x.shape[-1])
            width = max(1, int(round(t * time_mask_frac)))
            if width < t:
                start = int(torch.randint(0, t - width + 1, (1,)).item())
                x = x.clone()
                x[:, start:start + width] = 0.0

        channel_drop_prob = float(cfg.get("channel_drop_prob", 0.0) or 0.0)
        if channel_drop_prob > 0:
            c = int(x.shape[0])
            keep = (torch.rand(c, dtype=x.dtype) > channel_drop_prob).to(x.dtype)
            if keep.sum() < 1:
                keep[int(torch.randint(0, c, (1,)).item())] = 1.0
            x = x * keep[:, None]

        return x

    def __getitem__(self, idx):
        x = torch.from_numpy(self.x[idx].copy())
        x = self._augment(x)
        y = torch.tensor(self.y[idx], dtype=torch.float32)
        return x, y


def predict_dev_scaled(model, x_np, batch_size, device):
    model.eval()
    preds = []
    with torch.no_grad():
        for start in range(0, len(x_np), batch_size):
            xb = torch.from_numpy(x_np[start:start + batch_size]).to(device)
            logits, _ = model(xb, return_attn=False)
            preds.append(logits.squeeze(-1).detach().cpu().numpy())
    return np.concatenate(preds).astype(float)


def evaluate_scaled_rmse(model, x_val, y_val_scaled, batch_size, device):
    pred = predict_dev_scaled(model, x_val, batch_size, device)
    err = pred - np.asarray(y_val_scaled, dtype=float)
    return float(np.sqrt(np.mean(err * err)))


def train_aug_with_early_stopping(x_train, y_train_scaled, x_val, y_val_scaled, args, device, aug_cfg):
    model = base.make_model(args, device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    loss_fn = nn.HuberLoss(delta=args.huber_delta)

    ds = AugmentedEEGResidualDataset(x_train, y_train_scaled, aug_cfg=aug_cfg, train=True)
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

        val_rmse_scaled = evaluate_scaled_rmse(model, x_val, y_val_scaled, args.batch_size, device)

        row = {
            "epoch": int(epoch),
            "train_loss": safe_float(np.mean(losses)),
            "val_rmse_scaled": safe_float(val_rmse_scaled),
        }

        if best_val is None or val_rmse_scaled < best_val - 1e-6:
            best_val = val_rmse_scaled
            best_epoch = epoch
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
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


def train_aug_for_fixed_epochs(x_train, y_train_scaled, args, device, aug_cfg, epochs):
    model = base.make_model(args, device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    loss_fn = nn.HuberLoss(delta=args.huber_delta)

    ds = AugmentedEEGResidualDataset(x_train, y_train_scaled, aug_cfg=aug_cfg, train=True)
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


def make_prediction_rows(
    test_df: pd.DataFrame,
    target: str,
    augmentation_config: str,
    model_name: str,
    true_score: np.ndarray,
    stim_mean: np.ndarray,
    true_dev: np.ndarray,
    pred_dev: np.ndarray,
) -> pd.DataFrame:
    pred_score = np.asarray(stim_mean, dtype=float) + np.asarray(pred_dev, dtype=float)

    rows = test_df[["subject_id", "stimulus_id"]].rename(
        columns={"subject_id": "test_subject"}
    ).copy()

    rows["target"] = target
    rows["augmentation_config"] = augmentation_config
    rows["model"] = model_name
    rows["y_true_score"] = true_score
    rows["train_stimulus_mean"] = stim_mean
    rows["true_deviation_from_train_stimulus_mean"] = true_dev
    rows["y_pred_deviation_raw"] = pred_dev
    rows["y_pred_score_raw"] = pred_score
    rows["y_pred_score_clipped"] = np.clip(pred_score, 1.0, 9.0)
    rows["y_pred_deviation_clipped"] = rows["y_pred_score_clipped"] - rows["train_stimulus_mean"]

    return rows


def add_subset_flags(pred: pd.DataFrame, selected: pd.DataFrame) -> pd.DataFrame:
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


def aggregate_main(pred: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for (aug_name, target, model), g in pred.groupby(["augmentation_config", "target", "model"]):
        row = {
            "augmentation_config": aug_name,
            "target": target,
            "model": model,
        }
        row.update(base.prediction_metrics(g))
        row.update(base.deviation_metrics(g))
        rows.append(row)

    return pd.DataFrame(rows)


def aggregate_subsets(pred: pd.DataFrame) -> pd.DataFrame:
    subset_cols = [c for c in pred.columns if c.startswith("is_top25_train_")]
    rows = []

    for subset_col in subset_cols:
        subset_name = subset_col.replace("is_", "")
        for (aug_name, target, model), g0 in pred.groupby(["augmentation_config", "target", "model"]):
            g = g0[g0[subset_col]].copy()
            if g.empty:
                continue
            row = {
                "augmentation_config": aug_name,
                "target": target,
                "subset": subset_name,
                "model": model,
            }
            row.update(base.prediction_metrics(g))
            row.update(base.deviation_metrics(g))
            rows.append(row)

    return pd.DataFrame(rows)


def add_lifts(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    rows = []
    lower_is_better = {"mae", "rmse", "dev_mae", "dev_rmse"}
    metrics = [
        "mae", "rmse", "pearson", "spearman",
        "balanced_accuracy", "macro_f1", "auroc",
        "dev_mae", "dev_rmse", "dev_pearson", "dev_spearman",
        "dev_sign_acc", "true_dev_std", "pred_dev_std",
    ]

    for _, g in df.groupby(group_cols, dropna=False):
        base_row = g[g["model"].eq("stimulus_only")]
        if base_row.empty:
            continue
        base_row = base_row.iloc[0]

        for _, row in g.iterrows():
            out = row.to_dict()
            for metric in metrics:
                rv = row.get(metric, np.nan)
                bv = base_row.get(metric, np.nan)

                if pd.isna(rv) or pd.isna(bv):
                    out[f"lift_vs_stimulus_{metric}"] = None
                elif metric in lower_is_better:
                    out[f"lift_vs_stimulus_{metric}"] = safe_float(float(bv) - float(rv))
                else:
                    out[f"lift_vs_stimulus_{metric}"] = safe_float(float(rv) - float(bv))
            rows.append(out)

    return pd.DataFrame(rows)


def run_one_config(args, aug_name: str, aug_cfg: dict[str, Any], x_mmap, idx, stim_pred, selected, device):
    score_col = base.TARGET_COLUMNS[args.target]
    subjects = sorted(idx["subject_id"].unique().tolist())
    test_subjects = subjects[: args.max_folds]

    pred_rows_all = []
    fold_rows = []
    history_rows = []

    print(f"\n\n######## Augmentation config: {aug_name} ########")
    print(json.dumps(aug_cfg, indent=2))

    for fold_i, test_subject in enumerate(test_subjects, start=1):
        print(f"\n=== Config {aug_name} | Fold {fold_i}/{len(test_subjects)} | test_subject={test_subject} ===")

        outer_train_subjects = [s for s in subjects if s != test_subject]
        fit_subjects, val_subjects = base.split_inner_subjects(
            outer_train_subjects,
            test_subject=test_subject,
            val_count=args.val_subject_count,
            seed=args.seed,
        )

        fit_df = idx[idx["subject_id"].isin(fit_subjects)].copy()
        val_df = idx[idx["subject_id"].isin(val_subjects)].copy()
        outer_train_df = idx[idx["subject_id"].isin(outer_train_subjects)].copy()
        test_df = idx[idx["subject_id"].eq(test_subject)].copy()

        fit_rows = fit_df["cache_row"].to_numpy(dtype=int)
        val_rows = val_df["cache_row"].to_numpy(dtype=int)

        fit_mean, fit_std = base.fit_eeg_normalizer(x_mmap, fit_rows)
        x_fit = base.load_normed(x_mmap, fit_rows, fit_mean, fit_std)
        x_val = base.load_normed(x_mmap, val_rows, fit_mean, fit_std)

        y_fit_raw = base.loo_train_deviation(fit_df, score_col).astype(float)
        y_fit_mean, y_fit_std = base.fit_target_scaler(y_fit_raw)
        y_fit_scaled = base.scale_target(y_fit_raw, y_fit_mean, y_fit_std)

        y_val_raw, _ = base.heldout_deviation(val_df, fit_df, score_col)
        y_val_scaled = base.scale_target(y_val_raw, y_fit_mean, y_fit_std)

        _, best_epoch, best_val_scaled, hist = train_aug_with_early_stopping(
            x_train=x_fit,
            y_train_scaled=y_fit_scaled,
            x_val=x_val,
            y_val_scaled=y_val_scaled,
            args=args,
            device=device,
            aug_cfg=aug_cfg,
        )

        for h in hist:
            hh = dict(h)
            hh.update({
                "augmentation_config": aug_name,
                "stage": "inner",
                "test_subject": int(test_subject),
                "target": args.target,
                "y_fit_mean": safe_float(y_fit_mean),
                "y_fit_std": safe_float(y_fit_std),
            })
            history_rows.append(hh)

        print(f"best_epoch={best_epoch} best_val_rmse_scaled={best_val_scaled}")

        outer_rows = outer_train_df["cache_row"].to_numpy(dtype=int)
        test_rows = test_df["cache_row"].to_numpy(dtype=int)

        outer_mean, outer_std = base.fit_eeg_normalizer(x_mmap, outer_rows)
        x_outer = base.load_normed(x_mmap, outer_rows, outer_mean, outer_std)
        x_test = base.load_normed(x_mmap, test_rows, outer_mean, outer_std)

        y_outer_raw = base.loo_train_deviation(outer_train_df, score_col).astype(float)
        y_outer_mean, y_outer_std = base.fit_target_scaler(y_outer_raw)
        y_outer_scaled = base.scale_target(y_outer_raw, y_outer_mean, y_outer_std)

        final_model, final_hist = train_aug_for_fixed_epochs(
            x_train=x_outer,
            y_train_scaled=y_outer_scaled,
            args=args,
            device=device,
            aug_cfg=aug_cfg,
            epochs=best_epoch,
        )

        for h in final_hist:
            hh = dict(h)
            hh.update({
                "augmentation_config": aug_name,
                "stage": "final",
                "test_subject": int(test_subject),
                "target": args.target,
                "y_outer_mean": safe_float(y_outer_mean),
                "y_outer_std": safe_float(y_outer_std),
            })
            history_rows.append(hh)

        pred_scaled = predict_dev_scaled(final_model, x_test, args.batch_size, device)
        pred_dev = base.unscale_target(pred_scaled, y_outer_mean, y_outer_std)

        true_dev, train_stim_mean = base.heldout_deviation(test_df, outer_train_df, score_col)
        true_score = test_df[score_col].to_numpy(dtype=float)

        eeg_rows = make_prediction_rows(
            test_df=test_df,
            target=args.target,
            augmentation_config=aug_name,
            model_name=MODEL_NAME,
            true_score=true_score,
            stim_mean=train_stim_mean,
            true_dev=true_dev,
            pred_dev=pred_dev,
        )

        pred_rows_all.append(eeg_rows)

        fold_metric = {
            "augmentation_config": aug_name,
            "target": args.target,
            "model": MODEL_NAME,
            "test_subject": int(test_subject),
        }
        fold_metric.update(base.prediction_metrics(eeg_rows))
        fold_metric.update(base.deviation_metrics(eeg_rows))
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

    eeg_pred = pd.concat(pred_rows_all, ignore_index=True)

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
            "augmentation_config": aug_name,
            "model": "stimulus_only",
            "y_true_score": float(row["y_true_score"]),
            "train_stimulus_mean": pred_score,
            "true_deviation_from_train_stimulus_mean": float(row["true_deviation_from_train_stimulus_mean"]),
            "y_pred_deviation_raw": 0.0,
            "y_pred_score_raw": pred_score,
            "y_pred_score_clipped": np.clip(pred_score, 1.0, 9.0),
            "y_pred_deviation_clipped": 0.0,
        })

    all_pred = pd.concat([pd.DataFrame(stim_rows), eeg_pred], ignore_index=True)
    return all_pred, pd.DataFrame(fold_rows), pd.DataFrame(history_rows)


def summarize_best(main: pd.DataFrame) -> pd.DataFrame:
    rows = []
    eeg = main[main["model"].eq(MODEL_NAME)].copy()
    if eeg.empty:
        return pd.DataFrame()

    for metric, maximize in [
        ("lift_vs_stimulus_rmse", True),
        ("dev_pearson", True),
        ("lift_vs_stimulus_auroc", True),
        ("pred_dev_std", True),
        ("rmse", False),
    ]:
        valid = eeg[pd.notna(eeg[metric])].copy()
        if valid.empty:
            continue
        idx = valid[metric].idxmax() if maximize else valid[metric].idxmin()
        row = valid.loc[idx].to_dict()
        row["best_metric"] = metric
        row["best_metric_value"] = safe_float(row.get(metric))
        rows.append(row)

    return pd.DataFrame(rows)


def write_report(args, cfg_names, cfgs, pred, main, subset, fold_df, history_df, eeg_npy, eeg_index, elapsed_sec):
    pred.to_csv(OUT_PRED_CSV, index=False)
    main.to_csv(OUT_MAIN_CSV, index=False)
    subset.to_csv(OUT_SUBSET_CSV, index=False)
    fold_df.to_csv(OUT_FOLD_CSV, index=False)
    history_df.to_csv(OUT_HISTORY_CSV, index=False)

    best_df = summarize_best(main)

    summary = {
        "protocol": "EEG train-only augmentation matrix smoke",
        "target": args.target,
        "cache": args.cache,
        "model": MODEL_NAME,
        "augmentation_configs": {name: cfgs[name] for name in cfg_names},
        "epochs_max": args.epochs,
        "patience": args.patience,
        "max_folds": args.max_folds,
        "validation_subject_count": args.val_subject_count,
        "target_normalization": "fit residual mean/std on train subjects only; predict scaled residual; de-scale using outer train stats",
        "augmentation_scope": "train batches only; validation and test are never augmented",
        "loss": f"HuberLoss(delta={args.huber_delta}) on scaled residual",
        "optimizer": {
            "name": "AdamW",
            "lr": args.lr,
            "weight_decay": args.weight_decay,
        },
        "device": {
            "torch": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "device": "cuda" if torch.cuda.is_available() else "cpu",
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        "inputs": {
            "base_script_05c": str(BASE_SCRIPT_05C),
            "eeg_npy": str(eeg_npy),
            "eeg_index": str(eeg_index),
            "trial_index": str(base.TRIAL_INDEX),
            "stimulus_only_predictions": str(base.STIMULUS_ONLY_PRED),
            "fold_safe_selected": str(base.FOLD_SAFE_SELECTED),
        },
        "main_metrics": main.to_dict(orient="records"),
        "subset_metrics": subset.to_dict(orient="records"),
        "fold_summary": fold_df.to_dict(orient="records"),
        "best_rows": best_df.to_dict(orient="records"),
        "elapsed_sec": safe_float(elapsed_sec),
        "notes": [
            "This is exploratory and should not be treated as final model selection.",
            "All augmentation is applied only to training batches.",
            "Validation and test signals remain untouched.",
            "The no_aug config is included as a within-script control.",
            "If a config looks promising, validate it with a broader smoke before full LOSO.",
        ],
    }

    OUT_JSON.write_text(json.dumps(clean_json(summary), indent=2, ensure_ascii=False), encoding="utf-8")

    main_cols = [
        "augmentation_config", "target", "model", "n",
        "mae", "rmse", "pearson", "balanced_accuracy", "auroc",
        "dev_rmse", "dev_pearson", "dev_sign_acc",
        "true_dev_std", "pred_dev_std",
        "lift_vs_stimulus_rmse",
        "lift_vs_stimulus_balanced_accuracy",
        "lift_vs_stimulus_auroc",
        "lift_vs_stimulus_dev_rmse",
    ]

    fold_cols = [
        "augmentation_config",
        "test_subject",
        "best_epoch",
        "best_val_rmse_scaled",
        "rmse",
        "dev_rmse",
        "dev_pearson",
        "true_dev_std",
        "pred_dev_std",
        "final_train_last_loss",
    ]

    best_cols = [
        "best_metric",
        "best_metric_value",
        "augmentation_config",
        "rmse",
        "lift_vs_stimulus_rmse",
        "balanced_accuracy",
        "lift_vs_stimulus_balanced_accuracy",
        "auroc",
        "lift_vs_stimulus_auroc",
        "dev_pearson",
        "pred_dev_std",
    ]

    lines = []
    lines.append("# ROCA-I-DARE EEG Augmentation Matrix Smoke\n")
    lines.append("This is an exploratory train-only augmentation matrix. It is not final model selection.\n")

    lines.append("## Configuration\n")
    lines.append(f"- target: `{args.target}`")
    lines.append(f"- cache: `{args.cache}`")
    lines.append(f"- model: `{MODEL_NAME}`")
    lines.append(f"- max_folds: `{args.max_folds}`")
    lines.append(f"- epochs_max: `{args.epochs}`")
    lines.append(f"- patience: `{args.patience}`")
    lines.append(f"- batch_size: `{args.batch_size}`")
    lines.append(f"- optimizer: `AdamW(lr={args.lr}, weight_decay={args.weight_decay})`")
    lines.append(f"- loss: `HuberLoss(delta={args.huber_delta}) on scaled residual`")
    lines.append(f"- configs: `{cfg_names}`")
    lines.append("")

    lines.append("## Augmentation configs\n")
    lines.append("```json")
    lines.append(json.dumps({name: cfgs[name] for name in cfg_names}, indent=2))
    lines.append("```\n")

    lines.append("## Main metrics\n")
    lines.append(base.md_table(main.to_dict(orient="records"), main_cols))

    lines.append("\n## Best rows\n")
    lines.append(base.md_table(best_df.to_dict(orient="records"), best_cols))

    lines.append("\n## Fold summary\n")
    lines.append(base.md_table(fold_df.to_dict(orient="records"), fold_cols))

    lines.append("\n## Interpretation guide\n")
    lines.append(
        "- Positive `lift_vs_stimulus_rmse` means lower score RMSE than stimulus-only.\n"
        "- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.\n"
        "- `pred_dev_std` tracks whether the model escapes near-zero residual collapse.\n"
        "- A config is only interesting if it improves RMSE/deviation metrics without simply inflating noise.\n"
        "- Any promising config should be re-tested on broader smoke folds before full LOSO.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05h completed.")
    print(f"wrote: {OUT_MD}")
    print(f"wrote: {OUT_JSON}")
    print(f"wrote: {OUT_PRED_CSV}")
    print(f"wrote: {OUT_MAIN_CSV}")
    print(f"wrote: {OUT_SUBSET_CSV}")
    print(f"wrote: {OUT_FOLD_CSV}")
    print(f"wrote: {OUT_HISTORY_CSV}")
    print("\nMain metrics:")
    print(main[main_cols].to_string(index=False))
    print("\nBest rows:")
    if best_df.empty:
        print("No best rows.")
    else:
        print(best_df[best_cols].to_string(index=False))


def main():
    args = parse_args()
    base.set_seed(args.seed)
    t0 = time.perf_counter()

    cfg_names = selected_configs(args.configs)
    cfgs = AUGMENTATION_CONFIGS

    x_mmap, idx, stim_pred, selected, eeg_npy, eeg_index = base.load_inputs(args)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"device: {device}")
    print(f"target: {args.target}")
    print(f"cache: {args.cache}")
    print(f"configs: {cfg_names}")
    print(f"epochs={args.epochs} patience={args.patience} lr={args.lr}")

    pred_frames = []
    fold_frames = []
    history_frames = []

    for cfg_i, cfg_name in enumerate(cfg_names, start=1):
        print(f"\n\n==============================")
        print(f"Config {cfg_i}/{len(cfg_names)}: {cfg_name}")
        print(f"==============================")

        pred_cfg, fold_cfg, hist_cfg = run_one_config(
            args=args,
            aug_name=cfg_name,
            aug_cfg=cfgs[cfg_name],
            x_mmap=x_mmap,
            idx=idx,
            stim_pred=stim_pred,
            selected=selected,
            device=device,
        )

        pred_frames.append(pred_cfg)
        fold_frames.append(fold_cfg)
        history_frames.append(hist_cfg)

    pred = pd.concat(pred_frames, ignore_index=True, sort=False)
    pred = add_subset_flags(pred, selected)

    main_df = add_lifts(aggregate_main(pred), ["augmentation_config", "target"])
    subset_df = add_lifts(aggregate_subsets(pred), ["augmentation_config", "target", "subset"])
    fold_df = pd.concat(fold_frames, ignore_index=True, sort=False)
    history_df = pd.concat(history_frames, ignore_index=True, sort=False)

    write_report(
        args=args,
        cfg_names=cfg_names,
        cfgs=cfgs,
        pred=pred,
        main=main_df,
        subset=subset_df,
        fold_df=fold_df,
        history_df=history_df,
        eeg_npy=eeg_npy,
        eeg_index=eeg_index,
        elapsed_sec=time.perf_counter() - t0,
    )


if __name__ == "__main__":
    main()
