#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
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


ROOT = Path(__file__).resolve().parents[2]
ROCA_DIR = ROOT / "docs" / "roca"
BASE_SCRIPT = ROOT / "scripts" / "roca" / "05c_eeg_residual_training_stabilized_smoke.py"

OUT_MD = ROCA_DIR / "eeg_multitask_residual_training_smoke_current.md"
OUT_JSON = ROCA_DIR / "eeg_multitask_residual_training_smoke_current.json"
OUT_PRED_CSV = ROCA_DIR / "eeg_multitask_residual_training_smoke_predictions_current.csv"
OUT_MAIN_CSV = ROCA_DIR / "eeg_multitask_residual_training_smoke_main_metrics_current.csv"
OUT_SUBSET_CSV = ROCA_DIR / "eeg_multitask_residual_training_smoke_subset_metrics_current.csv"
OUT_FOLD_CSV = ROCA_DIR / "eeg_multitask_residual_training_smoke_fold_summary_current.csv"
OUT_HISTORY_CSV = ROCA_DIR / "eeg_multitask_residual_training_smoke_history_current.csv"

MODEL_NAME = "eeg_bc_residual_huber_norm_multitask_smoke"


def load_base_module():
    if not BASE_SCRIPT.exists():
        raise FileNotFoundError(BASE_SCRIPT)
    spec = importlib.util.spec_from_file_location("roca_05c_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec for {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["roca_05c_base"] = module
    spec.loader.exec_module(module)
    return module


base = load_base_module()


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
    p.add_argument("--lambda-bce", type=float, default=0.25)
    p.add_argument("--val-subject-count", type=int, default=8)
    p.add_argument("--seed", type=int, default=20260513)
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--dropout", type=float, default=0.1)
    p.add_argument("--head-dropout", type=float, default=0.3)
    return p.parse_args()


class EEGMultiTaskDataset(Dataset):
    def __init__(self, x: np.ndarray, y_scaled: np.ndarray, y_bin: np.ndarray):
        self.x = np.asarray(x, dtype=np.float32)
        self.y_scaled = np.asarray(y_scaled, dtype=np.float32)
        self.y_bin = np.asarray(y_bin, dtype=np.float32)

    def __len__(self):
        return int(len(self.y_scaled))

    def __getitem__(self, idx):
        return (
            torch.from_numpy(self.x[idx]),
            torch.tensor(self.y_scaled[idx], dtype=torch.float32),
            torch.tensor(self.y_bin[idx], dtype=torch.float32),
        )


class EEGResidualMultiTaskModel(nn.Module):
    def __init__(self, args):
        super().__init__()
        self.base = base.EEGSegmentClassifier(
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
        self.binary_head = nn.Sequential(
            nn.LayerNorm(128),
            nn.Linear(128, 64),
            nn.ELU(),
            nn.Dropout(args.head_dropout),
            nn.Linear(64, 1),
        )

    def forward(self, x):
        residual_logits, aux = self.base(x, return_attn=True)
        z = aux["z"]
        binary_logit = self.binary_head(z).squeeze(-1)
        residual_pred = residual_logits.squeeze(-1)
        return residual_pred, binary_logit


def make_model(args, device):
    return EEGResidualMultiTaskModel(args).to(device)


def true_binary_labels(df: pd.DataFrame, score_col: str) -> np.ndarray:
    return (df[score_col].to_numpy(dtype=float) > 5.0).astype(np.float32)


def predict_multitask(model, x_np, batch_size, device):
    model.eval()
    residual_preds = []
    binary_logits = []
    with torch.no_grad():
        for start in range(0, len(x_np), batch_size):
            xb = torch.from_numpy(x_np[start:start + batch_size]).to(device)
            pred_scaled, bin_logit = model(xb)
            residual_preds.append(pred_scaled.detach().cpu().numpy())
            binary_logits.append(bin_logit.detach().cpu().numpy())
    residual_preds = np.concatenate(residual_preds).astype(float)
    binary_logits = np.concatenate(binary_logits).astype(float)
    return residual_preds, binary_logits


def evaluate_validation(model, x_val, y_val_scaled, y_val_bin, args, device):
    pred_scaled, bin_logits = predict_multitask(model, x_val, args.batch_size, device)
    rmse_scaled = float(np.sqrt(np.mean((pred_scaled - y_val_scaled) ** 2)))

    logits = torch.tensor(bin_logits, dtype=torch.float32)
    labels = torch.tensor(y_val_bin, dtype=torch.float32)
    bce = float(nn.BCEWithLogitsLoss()(logits, labels).detach().cpu().item())

    objective = rmse_scaled + float(args.lambda_bce) * bce
    return rmse_scaled, bce, objective


def train_with_early_stopping(x_train, y_train_scaled, y_train_bin, args, device, x_val, y_val_scaled, y_val_bin):
    model = make_model(args, device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    huber = nn.HuberLoss(delta=args.huber_delta)
    bce = nn.BCEWithLogitsLoss()

    ds = EEGMultiTaskDataset(x_train, y_train_scaled, y_train_bin)
    loader = DataLoader(
        ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        drop_last=False,
    )

    best_epoch = 0
    best_objective = None
    best_rmse_scaled = None
    best_bce = None
    best_state = None
    bad_epochs = 0
    history = []

    for epoch in range(1, int(args.epochs) + 1):
        model.train()
        losses = []
        huber_losses = []
        bce_losses = []

        for xb, yb_scaled, yb_bin in loader:
            xb = xb.to(device)
            yb_scaled = yb_scaled.to(device)
            yb_bin = yb_bin.to(device)

            opt.zero_grad(set_to_none=True)
            pred_scaled, bin_logit = model(xb)

            loss_huber = huber(pred_scaled, yb_scaled)
            loss_bce = bce(bin_logit, yb_bin)
            loss = loss_huber + float(args.lambda_bce) * loss_bce

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            opt.step()

            losses.append(float(loss.detach().cpu().item()))
            huber_losses.append(float(loss_huber.detach().cpu().item()))
            bce_losses.append(float(loss_bce.detach().cpu().item()))

        val_rmse_scaled, val_bce, val_objective = evaluate_validation(
            model, x_val, y_val_scaled, y_val_bin, args, device
        )

        row = {
            "epoch": int(epoch),
            "train_loss": base.safe_float(np.mean(losses)),
            "train_huber": base.safe_float(np.mean(huber_losses)),
            "train_bce": base.safe_float(np.mean(bce_losses)),
            "val_rmse_scaled": base.safe_float(val_rmse_scaled),
            "val_bce": base.safe_float(val_bce),
            "val_objective": base.safe_float(val_objective),
        }

        if best_objective is None or val_objective < best_objective - 1e-6:
            best_objective = val_objective
            best_rmse_scaled = val_rmse_scaled
            best_bce = val_bce
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

    return model, int(best_epoch), base.safe_float(best_rmse_scaled), base.safe_float(best_bce), base.safe_float(best_objective), history


def train_for_fixed_epochs(x_train, y_train_scaled, y_train_bin, args, device, epochs):
    model = make_model(args, device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    huber = nn.HuberLoss(delta=args.huber_delta)
    bce = nn.BCEWithLogitsLoss()

    ds = EEGMultiTaskDataset(x_train, y_train_scaled, y_train_bin)
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
        huber_losses = []
        bce_losses = []

        for xb, yb_scaled, yb_bin in loader:
            xb = xb.to(device)
            yb_scaled = yb_scaled.to(device)
            yb_bin = yb_bin.to(device)

            opt.zero_grad(set_to_none=True)
            pred_scaled, bin_logit = model(xb)

            loss_huber = huber(pred_scaled, yb_scaled)
            loss_bce = bce(bin_logit, yb_bin)
            loss = loss_huber + float(args.lambda_bce) * loss_bce

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            opt.step()

            losses.append(float(loss.detach().cpu().item()))
            huber_losses.append(float(loss_huber.detach().cpu().item()))
            bce_losses.append(float(loss_bce.detach().cpu().item()))

        history.append({
            "epoch": int(epoch),
            "train_loss": base.safe_float(np.mean(losses)),
            "train_huber": base.safe_float(np.mean(huber_losses)),
            "train_bce": base.safe_float(np.mean(bce_losses)),
        })

    return model, history


def run_training(args):
    base.set_seed(args.seed)
    t0 = time.perf_counter()

    x_mmap, idx, stim_pred, selected, eeg_npy, eeg_index = base.load_inputs(args)
    score_col = base.TARGET_COLUMNS[args.target]

    subjects = sorted(idx["subject_id"].unique().tolist())
    test_subjects = subjects[: args.max_folds]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device: {device}")
    print(f"target: {args.target}")
    print(f"cache: {args.cache}")
    print(f"test_subjects: {test_subjects}")
    print(f"epochs={args.epochs} patience={args.patience} lr={args.lr} lambda_bce={args.lambda_bce}")

    all_pred_rows = []
    fold_rows = []
    history_rows = []

    for fold_i, test_subject in enumerate(test_subjects, start=1):
        print(f"\n=== Fold {fold_i}/{len(test_subjects)} | test_subject={test_subject} ===")

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
        y_fit_bin = true_binary_labels(fit_df, score_col)

        y_val_raw, _ = base.heldout_deviation(val_df, fit_df, score_col)
        y_val_scaled = base.scale_target(y_val_raw, y_fit_mean, y_fit_std)
        y_val_bin = true_binary_labels(val_df, score_col)

        _, best_epoch, best_val_rmse_scaled, best_val_bce, best_val_objective, hist = train_with_early_stopping(
            x_fit,
            y_fit_scaled,
            y_fit_bin,
            args,
            device,
            x_val,
            y_val_scaled,
            y_val_bin,
        )

        for h in hist:
            hh = dict(h)
            hh.update({
                "stage": "inner",
                "test_subject": int(test_subject),
                "target": args.target,
                "y_fit_mean": base.safe_float(y_fit_mean),
                "y_fit_std": base.safe_float(y_fit_std),
            })
            history_rows.append(hh)

        print(
            f"best_epoch={best_epoch} "
            f"best_val_rmse_scaled={best_val_rmse_scaled} "
            f"best_val_bce={best_val_bce} "
            f"best_val_objective={best_val_objective}"
        )

        outer_rows = outer_train_df["cache_row"].to_numpy(dtype=int)
        test_rows = test_df["cache_row"].to_numpy(dtype=int)

        outer_mean, outer_std = base.fit_eeg_normalizer(x_mmap, outer_rows)
        x_outer = base.load_normed(x_mmap, outer_rows, outer_mean, outer_std)
        x_test = base.load_normed(x_mmap, test_rows, outer_mean, outer_std)

        y_outer_raw = base.loo_train_deviation(outer_train_df, score_col).astype(float)
        y_outer_mean, y_outer_std = base.fit_target_scaler(y_outer_raw)
        y_outer_scaled = base.scale_target(y_outer_raw, y_outer_mean, y_outer_std)
        y_outer_bin = true_binary_labels(outer_train_df, score_col)

        final_model, final_hist = train_for_fixed_epochs(
            x_outer,
            y_outer_scaled,
            y_outer_bin,
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
                "y_outer_mean": base.safe_float(y_outer_mean),
                "y_outer_std": base.safe_float(y_outer_std),
            })
            history_rows.append(hh)

        pred_scaled, binary_logits = predict_multitask(final_model, x_test, args.batch_size, device)
        pred_dev = base.unscale_target(pred_scaled, y_outer_mean, y_outer_std)
        binary_prob = 1.0 / (1.0 + np.exp(-binary_logits))

        true_dev, train_stim_mean = base.heldout_deviation(test_df, outer_train_df, score_col)
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
        eeg_rows["aux_binary_logit"] = binary_logits
        eeg_rows["aux_binary_prob"] = binary_prob

        all_pred_rows.append(eeg_rows)

        fold_metric = {"target": args.target, "model": MODEL_NAME, "test_subject": int(test_subject)}
        fold_metric.update(base.prediction_metrics(eeg_rows))
        fold_metric.update(base.deviation_metrics(eeg_rows))
        fold_metric.update({
            "best_epoch": int(best_epoch),
            "best_val_rmse_scaled": base.safe_float(best_val_rmse_scaled),
            "best_val_bce": base.safe_float(best_val_bce),
            "best_val_objective": base.safe_float(best_val_objective),
            "fit_subjects": int(len(fit_subjects)),
            "val_subjects": int(len(val_subjects)),
            "outer_train_subjects": int(len(outer_train_subjects)),
            "y_outer_mean": base.safe_float(y_outer_mean),
            "y_outer_std": base.safe_float(y_outer_std),
            "final_train_last_loss": base.safe_float(final_hist[-1]["train_loss"]) if final_hist else None,
            "final_train_last_huber": base.safe_float(final_hist[-1].get("train_huber")) if final_hist else None,
            "final_train_last_bce": base.safe_float(final_hist[-1].get("train_bce")) if final_hist else None,
            "aux_binary_prob_mean": base.safe_float(np.mean(binary_prob)),
            "aux_binary_prob_std": base.safe_float(np.std(binary_prob)),
        })
        fold_rows.append(fold_metric)

        print(
            f"test rmse={fold_metric['rmse']:.4f} "
            f"dev_rmse={fold_metric['dev_rmse']:.4f} "
            f"dev_pearson={fold_metric['dev_pearson']} "
            f"pred_dev_std={fold_metric['pred_dev_std']} "
            f"aux_prob_std={fold_metric['aux_binary_prob_std']}"
        )

    eeg_pred = pd.concat(all_pred_rows, ignore_index=True)

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
            "aux_binary_logit": np.nan,
            "aux_binary_prob": np.nan,
        })

    pred = pd.concat([pd.DataFrame(stim_rows), eeg_pred], ignore_index=True)
    pred = base.add_subset_flags(pred, selected)

    main = base.add_lifts(base.aggregate_main(pred), ["target"])
    subset = base.add_lifts(base.aggregate_subsets(pred), ["target", "subset"])
    fold_df = pd.DataFrame(fold_rows)
    history_df = pd.DataFrame(history_rows)

    pred.to_csv(OUT_PRED_CSV, index=False)
    main.to_csv(OUT_MAIN_CSV, index=False)
    subset.to_csv(OUT_SUBSET_CSV, index=False)
    fold_df.to_csv(OUT_FOLD_CSV, index=False)
    history_df.to_csv(OUT_HISTORY_CSV, index=False)

    summary = {
        "protocol": "EEG multitask residual training smoke",
        "target": args.target,
        "cache": args.cache,
        "model": MODEL_NAME,
        "epochs_max": args.epochs,
        "patience": args.patience,
        "max_folds": args.max_folds,
        "test_subjects": test_subjects,
        "validation_subject_count": args.val_subject_count,
        "target_normalization": "fit residual mean/std on train subjects only; predict scaled residual; de-scale using outer train stats",
        "loss": {
            "residual": f"HuberLoss(delta={args.huber_delta}) on scaled residual",
            "auxiliary": "BCEWithLogitsLoss on high/low score label",
            "lambda_bce": args.lambda_bce,
        },
        "optimizer": {
            "name": "AdamW",
            "lr": args.lr,
            "weight_decay": args.weight_decay,
        },
        "model_config": {
            "dropout": args.dropout,
            "head_dropout": args.head_dropout,
            "n_classes_residual": 1,
            "aux_binary_head": True,
            "modelsize": "lite",
        },
        "device": {
            "torch": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "device": str(device),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        "inputs": {
            "base_script": str(BASE_SCRIPT),
            "eeg_npy": str(eeg_npy),
            "eeg_index": str(eeg_index),
            "trial_index": str(base.TRIAL_INDEX),
            "stimulus_only_predictions": str(base.STIMULUS_ONLY_PRED),
            "fold_safe_selected": str(base.FOLD_SAFE_SELECTED),
        },
        "main_metrics": main.to_dict(orient="records"),
        "subset_metrics": subset.to_dict(orient="records"),
        "fold_summary": fold_df.to_dict(orient="records"),
        "elapsed_sec": base.safe_float(time.perf_counter() - t0),
        "notes": [
            "This is a multitask smoke run, not the final full LOSO training.",
            "Residual targets are normalized using train-only residual mean/std.",
            "Auxiliary BCE is used only to shape the encoder; final ROCA evaluation uses residual-derived scores.",
            "Epoch is selected using validation subjects from outer-train subjects only.",
            "After epoch selection, the model is retrained on all outer-train subjects.",
            "The held-out test subject is only used for final evaluation.",
            "Final score is train-stimulus mean plus EEG-predicted residual.",
        ],
    }

    OUT_JSON.write_text(json.dumps(base.clean_json(summary), indent=2, ensure_ascii=False), encoding="utf-8")

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
    lines.append("# ROCA-I-DARE EEG Multitask Residual Training Smoke\n")
    lines.append("This is a strict-LOSO multitask smoke run, not final full training.\n")
    lines.append("## Configuration\n")
    lines.append(f"- target: `{args.target}`")
    lines.append(f"- cache: `{args.cache}`")
    lines.append(f"- model: `{MODEL_NAME}`")
    lines.append(f"- test_subjects: `{test_subjects}`")
    lines.append(f"- epochs_max: `{args.epochs}`")
    lines.append(f"- patience: `{args.patience}`")
    lines.append(f"- batch_size: `{args.batch_size}`")
    lines.append(f"- optimizer: `AdamW(lr={args.lr}, weight_decay={args.weight_decay})`")
    lines.append(f"- loss: `HuberResidual + {args.lambda_bce} * BCEHighLow`")
    lines.append(f"- dropout/head_dropout: `{args.dropout}` / `{args.head_dropout}`")
    lines.append("")
    lines.append("## Main metrics\n")
    lines.append(base.md_table(main.to_dict(orient="records"), main_cols))
    lines.append("\n## Fold-safe hard subset metrics\n")
    lines.append(base.md_table(subset.to_dict(orient="records"), subset_cols))
    lines.append("\n## Fold summary\n")
    lines.append(base.md_table(fold_df.to_dict(orient="records"), [
        "test_subject",
        "best_epoch",
        "best_val_rmse_scaled",
        "best_val_bce",
        "best_val_objective",
        "rmse",
        "dev_rmse",
        "dev_pearson",
        "true_dev_std",
        "pred_dev_std",
        "aux_binary_prob_std",
        "final_train_last_loss",
    ]))
    lines.append("\n## Interpretation guide\n")
    lines.append(
        "- Positive `lift_vs_stimulus_rmse` means lower score RMSE than stimulus-only.\n"
        "- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.\n"
        "- `pred_dev_std` should not collapse near zero if the model is learning residual variation.\n"
        "- The auxiliary binary head is not the main output; it is only a training signal.\n"
        "- If this smoke run is stable and promising, the next step is full 63-subject LOSO.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05d completed.")
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
        "test_subject", "best_epoch", "best_val_rmse_scaled", "best_val_bce", "best_val_objective",
        "rmse", "dev_rmse", "dev_pearson",
        "true_dev_std", "pred_dev_std", "aux_binary_prob_std",
        "final_train_last_loss"
    ]].to_string(index=False))


def main():
    args = parse_args()
    run_training(args)


if __name__ == "__main__":
    main()
