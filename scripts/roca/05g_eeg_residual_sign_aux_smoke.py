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


ROOT = Path(__file__).resolve().parents[2]
ROCA_DIR = ROOT / "docs" / "roca"
BASE_SCRIPT_05D = ROOT / "scripts" / "roca" / "05d_eeg_multitask_residual_training_smoke.py"

OUT_MD = ROCA_DIR / "eeg_residual_sign_aux_smoke_current.md"
OUT_JSON = ROCA_DIR / "eeg_residual_sign_aux_smoke_current.json"
OUT_PRED_CSV = ROCA_DIR / "eeg_residual_sign_aux_smoke_predictions_current.csv"
OUT_MAIN_CSV = ROCA_DIR / "eeg_residual_sign_aux_smoke_main_metrics_current.csv"
OUT_SUBSET_CSV = ROCA_DIR / "eeg_residual_sign_aux_smoke_subset_metrics_current.csv"
OUT_FOLD_CSV = ROCA_DIR / "eeg_residual_sign_aux_smoke_fold_summary_current.csv"
OUT_HISTORY_CSV = ROCA_DIR / "eeg_residual_sign_aux_smoke_history_current.csv"

MODEL_NAME = "eeg_bc_residual_huber_norm_residual_sign_aux_smoke"


def load_module(path: Path, name: str):
    if not path.exists():
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


mt = load_module(BASE_SCRIPT_05D, "roca_05d_multitask")
base = mt.base


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

    # 05d train helpers expect args.lambda_bce, but here it means residual-sign auxiliary weight.
    p.add_argument("--lambda-sign", dest="lambda_bce", type=float, default=0.25)

    p.add_argument("--val-subject-count", type=int, default=8)
    p.add_argument("--seed", type=int, default=20260513)
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--dropout", type=float, default=0.1)
    p.add_argument("--head-dropout", type=float, default=0.3)
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


def residual_sign_labels(residual: np.ndarray) -> np.ndarray:
    return (np.asarray(residual, dtype=float) > 0.0).astype(np.float32)


def residual_sign_accuracy(true_dev: np.ndarray, sign_prob: np.ndarray) -> float | None:
    true = np.asarray(true_dev, dtype=float)
    prob = np.asarray(sign_prob, dtype=float)
    m = np.isfinite(true) & np.isfinite(prob)
    true = true[m]
    prob = prob[m]
    if len(true) == 0:
        return None
    y = (true > 0.0).astype(int)
    p = (prob >= 0.5).astype(int)
    return float(np.mean(y == p))


def residual_sign_auroc(true_dev: np.ndarray, sign_prob: np.ndarray) -> float | None:
    true = np.asarray(true_dev, dtype=float)
    prob = np.asarray(sign_prob, dtype=float)
    m = np.isfinite(true) & np.isfinite(prob)
    true = true[m]
    prob = prob[m]
    if len(true) == 0:
        return None
    y = (true > 0.0).astype(int)
    return base.auroc(y, prob)


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


def make_prediction_rows(
    test_df: pd.DataFrame,
    target: str,
    model_name: str,
    true_score: np.ndarray,
    stim_mean: np.ndarray,
    true_dev: np.ndarray,
    pred_dev: np.ndarray,
    aux_logit: np.ndarray | None,
    aux_prob: np.ndarray | None,
) -> pd.DataFrame:
    pred_score = np.asarray(stim_mean, dtype=float) + np.asarray(pred_dev, dtype=float)

    rows = test_df[["subject_id", "stimulus_id"]].rename(
        columns={"subject_id": "test_subject"}
    ).copy()

    rows["target"] = target
    rows["model"] = model_name
    rows["y_true_score"] = true_score
    rows["train_stimulus_mean"] = stim_mean
    rows["true_deviation_from_train_stimulus_mean"] = true_dev
    rows["y_pred_deviation_raw"] = pred_dev
    rows["y_pred_score_raw"] = pred_score
    rows["y_pred_score_clipped"] = np.clip(pred_score, 1.0, 9.0)
    rows["y_pred_deviation_clipped"] = rows["y_pred_score_clipped"] - rows["train_stimulus_mean"]

    rows["aux_residual_sign_logit"] = aux_logit if aux_logit is not None else np.nan
    rows["aux_residual_sign_prob"] = aux_prob if aux_prob is not None else np.nan

    return rows


def aggregate_main(pred: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for model, g in pred.groupby("model"):
        row = {"target": g["target"].iloc[0], "model": model}
        row.update(base.prediction_metrics(g))
        row.update(base.deviation_metrics(g))

        if "aux_residual_sign_prob" in g.columns and g["aux_residual_sign_prob"].notna().any():
            true_dev = g["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
            prob = g["aux_residual_sign_prob"].to_numpy(dtype=float)
            row["aux_residual_sign_acc"] = residual_sign_accuracy(true_dev, prob)
            row["aux_residual_sign_auroc"] = residual_sign_auroc(true_dev, prob)
            row["aux_residual_sign_prob_mean"] = safe_float(np.nanmean(prob))
            row["aux_residual_sign_prob_std"] = safe_float(np.nanstd(prob))
        else:
            row["aux_residual_sign_acc"] = None
            row["aux_residual_sign_auroc"] = None
            row["aux_residual_sign_prob_mean"] = None
            row["aux_residual_sign_prob_std"] = None

        rows.append(row)

    return pd.DataFrame(rows)


def aggregate_subsets(pred: pd.DataFrame) -> pd.DataFrame:
    subset_cols = [c for c in pred.columns if c.startswith("is_top25_train_")]
    rows = []

    for subset_col in subset_cols:
        subset_name = subset_col.replace("is_", "")
        for model, g0 in pred.groupby("model"):
            g = g0[g0[subset_col]].copy()
            if g.empty:
                continue

            row = {
                "target": g0["target"].iloc[0],
                "subset": subset_name,
                "model": model,
            }
            row.update(base.prediction_metrics(g))
            row.update(base.deviation_metrics(g))

            if "aux_residual_sign_prob" in g.columns and g["aux_residual_sign_prob"].notna().any():
                true_dev = g["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
                prob = g["aux_residual_sign_prob"].to_numpy(dtype=float)
                row["aux_residual_sign_acc"] = residual_sign_accuracy(true_dev, prob)
                row["aux_residual_sign_auroc"] = residual_sign_auroc(true_dev, prob)
            else:
                row["aux_residual_sign_acc"] = None
                row["aux_residual_sign_auroc"] = None

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
        "aux_residual_sign_acc", "aux_residual_sign_auroc",
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
    print(
        f"epochs={args.epochs} patience={args.patience} lr={args.lr} "
        f"lambda_sign={args.lambda_bce}"
    )

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
        y_fit_bin = residual_sign_labels(y_fit_raw)

        y_val_raw, _ = base.heldout_deviation(val_df, fit_df, score_col)
        y_val_scaled = base.scale_target(y_val_raw, y_fit_mean, y_fit_std)
        y_val_bin = residual_sign_labels(y_val_raw)

        _, best_epoch, best_val_rmse_scaled, best_val_bce, best_val_objective, hist = mt.train_with_early_stopping(
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
                "auxiliary": "residual_sign",
                "y_fit_mean": safe_float(y_fit_mean),
                "y_fit_std": safe_float(y_fit_std),
            })
            history_rows.append(hh)

        print(
            f"best_epoch={best_epoch} "
            f"best_val_rmse_scaled={best_val_rmse_scaled} "
            f"best_val_sign_bce={best_val_bce} "
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
        y_outer_bin = residual_sign_labels(y_outer_raw)

        final_model, final_hist = mt.train_for_fixed_epochs(
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
                "auxiliary": "residual_sign",
                "y_outer_mean": safe_float(y_outer_mean),
                "y_outer_std": safe_float(y_outer_std),
            })
            history_rows.append(hh)

        pred_scaled, sign_logits = mt.predict_multitask(final_model, x_test, args.batch_size, device)
        pred_dev = base.unscale_target(pred_scaled, y_outer_mean, y_outer_std)
        sign_prob = 1.0 / (1.0 + np.exp(-sign_logits))

        true_dev, train_stim_mean = base.heldout_deviation(test_df, outer_train_df, score_col)
        true_score = test_df[score_col].to_numpy(dtype=float)

        eeg_rows = make_prediction_rows(
            test_df=test_df,
            target=args.target,
            model_name=MODEL_NAME,
            true_score=true_score,
            stim_mean=train_stim_mean,
            true_dev=true_dev,
            pred_dev=pred_dev,
            aux_logit=sign_logits,
            aux_prob=sign_prob,
        )

        all_pred_rows.append(eeg_rows)

        fold_metric = {
            "target": args.target,
            "model": MODEL_NAME,
            "test_subject": int(test_subject),
        }
        fold_metric.update(base.prediction_metrics(eeg_rows))
        fold_metric.update(base.deviation_metrics(eeg_rows))
        fold_metric.update({
            "best_epoch": int(best_epoch),
            "best_val_rmse_scaled": safe_float(best_val_rmse_scaled),
            "best_val_sign_bce": safe_float(best_val_bce),
            "best_val_objective": safe_float(best_val_objective),
            "fit_subjects": int(len(fit_subjects)),
            "val_subjects": int(len(val_subjects)),
            "outer_train_subjects": int(len(outer_train_subjects)),
            "y_outer_mean": safe_float(y_outer_mean),
            "y_outer_std": safe_float(y_outer_std),
            "final_train_last_loss": safe_float(final_hist[-1]["train_loss"]) if final_hist else None,
            "final_train_last_huber": safe_float(final_hist[-1].get("train_huber")) if final_hist else None,
            "final_train_last_bce": safe_float(final_hist[-1].get("train_bce")) if final_hist else None,
            "aux_residual_sign_acc": residual_sign_accuracy(true_dev, sign_prob),
            "aux_residual_sign_auroc": residual_sign_auroc(true_dev, sign_prob),
            "aux_residual_sign_prob_mean": safe_float(np.mean(sign_prob)),
            "aux_residual_sign_prob_std": safe_float(np.std(sign_prob)),
        })
        fold_rows.append(fold_metric)

        print(
            f"test rmse={fold_metric['rmse']:.4f} "
            f"dev_rmse={fold_metric['dev_rmse']:.4f} "
            f"dev_pearson={fold_metric['dev_pearson']} "
            f"pred_dev_std={fold_metric['pred_dev_std']} "
            f"sign_acc={fold_metric['aux_residual_sign_acc']} "
            f"sign_auc={fold_metric['aux_residual_sign_auroc']}"
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
        test_subject = int(row["test_subject"])
        true_dev = float(row["true_deviation_from_train_stimulus_mean"])
        stim_rows.append({
            "test_subject": test_subject,
            "stimulus_id": str(row["stimulus_id"]),
            "target": args.target,
            "model": "stimulus_only",
            "y_true_score": float(row["y_true_score"]),
            "train_stimulus_mean": pred_score,
            "true_deviation_from_train_stimulus_mean": true_dev,
            "y_pred_deviation_raw": 0.0,
            "y_pred_score_raw": pred_score,
            "y_pred_score_clipped": np.clip(pred_score, 1.0, 9.0),
            "y_pred_deviation_clipped": 0.0,
            "aux_residual_sign_logit": np.nan,
            "aux_residual_sign_prob": np.nan,
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
        "protocol": "EEG residual-sign auxiliary smoke",
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
            "auxiliary": "BCEWithLogitsLoss on residual sign label: residual > 0",
            "lambda_sign": args.lambda_bce,
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
            "aux_residual_sign_head": True,
            "modelsize": "lite",
        },
        "device": {
            "torch": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "device": str(device),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        "inputs": {
            "base_script_05d": str(BASE_SCRIPT_05D),
            "eeg_npy": str(eeg_npy),
            "eeg_index": str(eeg_index),
            "trial_index": str(base.TRIAL_INDEX),
            "stimulus_only_predictions": str(base.STIMULUS_ONLY_PRED),
            "fold_safe_selected": str(base.FOLD_SAFE_SELECTED),
        },
        "main_metrics": main.to_dict(orient="records"),
        "subset_metrics": subset.to_dict(orient="records"),
        "fold_summary": fold_df.to_dict(orient="records"),
        "elapsed_sec": safe_float(time.perf_counter() - t0),
        "notes": [
            "This is a residual-sign auxiliary smoke run, not final full LOSO.",
            "Residual targets are normalized using train-only residual mean/std.",
            "Auxiliary BCE is aligned with ROCA: residual > 0, not raw score > 5.",
            "The auxiliary residual-sign head is not the main ROCA output; final score still uses predicted residual.",
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
        "aux_residual_sign_acc", "aux_residual_sign_auroc",
        "aux_residual_sign_prob_std",
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
        "aux_residual_sign_acc", "aux_residual_sign_auroc",
        "lift_vs_stimulus_rmse",
        "lift_vs_stimulus_balanced_accuracy",
        "lift_vs_stimulus_auroc",
        "lift_vs_stimulus_dev_rmse",
    ]

    fold_cols = [
        "test_subject",
        "best_epoch",
        "best_val_rmse_scaled",
        "best_val_sign_bce",
        "best_val_objective",
        "rmse",
        "dev_rmse",
        "dev_pearson",
        "true_dev_std",
        "pred_dev_std",
        "aux_residual_sign_acc",
        "aux_residual_sign_auroc",
        "aux_residual_sign_prob_std",
        "final_train_last_loss",
    ]

    lines = []
    lines.append("# ROCA-I-DARE EEG Residual-Sign Auxiliary Smoke\n")
    lines.append("This is a strict-LOSO residual-sign auxiliary smoke run, not final full training.\n")

    lines.append("## Configuration\n")
    lines.append(f"- target: `{args.target}`")
    lines.append(f"- cache: `{args.cache}`")
    lines.append(f"- model: `{MODEL_NAME}`")
    lines.append(f"- test_subjects: `{test_subjects}`")
    lines.append(f"- epochs_max: `{args.epochs}`")
    lines.append(f"- patience: `{args.patience}`")
    lines.append(f"- batch_size: `{args.batch_size}`")
    lines.append(f"- optimizer: `AdamW(lr={args.lr}, weight_decay={args.weight_decay})`")
    lines.append(f"- loss: `HuberResidual + {args.lambda_bce} * BCEResidualSign`")
    lines.append(f"- residual-sign label: `residual > 0`")
    lines.append(f"- dropout/head_dropout: `{args.dropout}` / `{args.head_dropout}`")
    lines.append("")

    lines.append("## Main metrics\n")
    lines.append(base.md_table(main.to_dict(orient="records"), main_cols))

    lines.append("\n## Fold-safe hard subset metrics\n")
    lines.append(base.md_table(subset.to_dict(orient="records"), subset_cols))

    lines.append("\n## Fold summary\n")
    lines.append(base.md_table(fold_df.to_dict(orient="records"), fold_cols))

    lines.append("\n## Interpretation guide\n")
    lines.append(
        "- Positive `lift_vs_stimulus_rmse` means lower score RMSE than stimulus-only.\n"
        "- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.\n"
        "- `aux_residual_sign_acc` checks whether the auxiliary head predicts residual direction.\n"
        "- `pred_dev_std` should not collapse near zero if the model is learning residual variation.\n"
        "- If this improves over 05c/05d, the next step is full LOSO or a broader smoke over more folds.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05g completed.")
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
    print(fold_df[fold_cols].to_string(index=False))


def main():
    args = parse_args()
    run_training(args)


if __name__ == "__main__":
    main()
