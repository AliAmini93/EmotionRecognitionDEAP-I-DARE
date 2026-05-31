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

OUT_MD = ROCA_DIR / "eeg_validation_calibrated_smoke_current.md"
OUT_JSON = ROCA_DIR / "eeg_validation_calibrated_smoke_current.json"
OUT_PRED_CSV = ROCA_DIR / "eeg_validation_calibrated_smoke_predictions_current.csv"
OUT_MAIN_CSV = ROCA_DIR / "eeg_validation_calibrated_smoke_main_metrics_current.csv"
OUT_SUBSET_CSV = ROCA_DIR / "eeg_validation_calibrated_smoke_subset_metrics_current.csv"
OUT_FOLD_CSV = ROCA_DIR / "eeg_validation_calibrated_smoke_fold_summary_current.csv"
OUT_HISTORY_CSV = ROCA_DIR / "eeg_validation_calibrated_smoke_history_current.csv"

BASELINE_MODEL = "stimulus_fit_only"
UNCAL_MODEL = "eeg_multitask_uncalibrated_inner"
CAL_MODEL = "eeg_multitask_val_affine_calibrated_inner"
EPS = 1e-12


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
    p.add_argument("--lambda-bce", type=float, default=0.25)
    p.add_argument("--val-subject-count", type=int, default=8)
    p.add_argument("--seed", type=int, default=20260513)
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--dropout", type=float, default=0.1)
    p.add_argument("--head-dropout", type=float, default=0.3)
    p.add_argument("--calibration-ridge", type=float, default=1e-6)
    p.add_argument("--max-abs-calibration-slope", type=float, default=20.0)
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


def rmse(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    if not m.any():
        return None
    e = p[m] - y[m]
    return float(np.sqrt(np.mean(e * e)))


def pearson(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y = y[m]
    p = p[m]
    if len(y) < 2 or np.std(y) == 0 or np.std(p) == 0:
        return None
    return float(np.corrcoef(y, p)[0, 1])


def fit_affine_calibrator(pred_dev_val, true_dev_val, ridge=1e-6, max_abs_slope=20.0):
    x = np.asarray(pred_dev_val, dtype=float)
    y = np.asarray(true_dev_val, dtype=float)
    m = np.isfinite(x) & np.isfinite(y)
    x = x[m]
    y = y[m]

    if len(x) < 2 or np.std(x) < EPS:
        return 0.0, float(np.mean(y)) if len(y) else 0.0

    xm = float(np.mean(x))
    ym = float(np.mean(y))
    xc = x - xm
    yc = y - ym

    den = float(np.sum(xc * xc) + float(ridge) * len(xc))
    if den <= EPS:
        a = 0.0
    else:
        a = float(np.sum(xc * yc) / den)

    max_abs_slope = abs(float(max_abs_slope))
    if math.isfinite(max_abs_slope) and max_abs_slope > 0:
        a = float(np.clip(a, -max_abs_slope, max_abs_slope))

    b = float(ym - a * xm)
    return a, b


def apply_affine(pred_dev, a, b):
    return np.asarray(pred_dev, dtype=float) * float(a) + float(b)


def make_prediction_rows(test_df, target, model_name, true_score, stim_mean, true_dev, pred_dev):
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

    return rows


def aggregate_main(pred):
    rows = []
    for model, g in pred.groupby("model"):
        row = {"target": g["target"].iloc[0], "model": model}
        row.update(base.prediction_metrics(g))
        row.update(base.deviation_metrics(g))
        rows.append(row)
    return pd.DataFrame(rows)


def aggregate_subsets(pred):
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
            rows.append(row)

    return pd.DataFrame(rows)


def add_lifts(df, group_cols, baseline_model=BASELINE_MODEL):
    rows = []
    lower_is_better = {"mae", "rmse", "dev_mae", "dev_rmse"}
    metrics = [
        "mae", "rmse", "pearson", "spearman",
        "balanced_accuracy", "macro_f1", "auroc",
        "dev_mae", "dev_rmse", "dev_pearson", "dev_spearman",
        "dev_sign_acc", "true_dev_std", "pred_dev_std",
    ]

    for _, g in df.groupby(group_cols, dropna=False):
        base_row = g[g["model"].eq(baseline_model)]
        if base_row.empty:
            continue
        base_row = base_row.iloc[0]

        for _, row in g.iterrows():
            out = row.to_dict()
            for metric in metrics:
                rv = row.get(metric, np.nan)
                bv = base_row.get(metric, np.nan)

                if pd.isna(rv) or pd.isna(bv):
                    out[f"lift_vs_{baseline_model}_{metric}"] = None
                elif metric in lower_is_better:
                    out[f"lift_vs_{baseline_model}_{metric}"] = safe_float(float(bv) - float(rv))
                else:
                    out[f"lift_vs_{baseline_model}_{metric}"] = safe_float(float(rv) - float(bv))
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
        f"lambda_bce={args.lambda_bce}"
    )
    print(
        f"calibration: affine ridge={args.calibration_ridge} "
        f"max_abs_slope={args.max_abs_calibration_slope}"
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
        test_df = idx[idx["subject_id"].eq(test_subject)].copy()

        fit_rows = fit_df["cache_row"].to_numpy(dtype=int)
        val_rows = val_df["cache_row"].to_numpy(dtype=int)
        test_rows = test_df["cache_row"].to_numpy(dtype=int)

        fit_mean, fit_std = base.fit_eeg_normalizer(x_mmap, fit_rows)
        x_fit = base.load_normed(x_mmap, fit_rows, fit_mean, fit_std)
        x_val = base.load_normed(x_mmap, val_rows, fit_mean, fit_std)
        x_test = base.load_normed(x_mmap, test_rows, fit_mean, fit_std)

        y_fit_raw = base.loo_train_deviation(fit_df, score_col).astype(float)
        y_fit_mean, y_fit_std = base.fit_target_scaler(y_fit_raw)
        y_fit_scaled = base.scale_target(y_fit_raw, y_fit_mean, y_fit_std)
        y_fit_bin = mt.true_binary_labels(fit_df, score_col)

        y_val_raw, val_stim_mean = base.heldout_deviation(val_df, fit_df, score_col)
        y_val_scaled = base.scale_target(y_val_raw, y_fit_mean, y_fit_std)
        y_val_bin = mt.true_binary_labels(val_df, score_col)

        model, best_epoch, best_val_rmse_scaled, best_val_bce, best_val_objective, hist = mt.train_with_early_stopping(
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
                "stage": "inner_fit_model",
                "test_subject": int(test_subject),
                "target": args.target,
                "y_fit_mean": safe_float(y_fit_mean),
                "y_fit_std": safe_float(y_fit_std),
            })
            history_rows.append(hh)

        pred_val_scaled, val_binary_logits = mt.predict_multitask(model, x_val, args.batch_size, device)
        pred_val_dev_uncal = base.unscale_target(pred_val_scaled, y_fit_mean, y_fit_std)

        cal_a, cal_b = fit_affine_calibrator(
            pred_val_dev_uncal,
            y_val_raw,
            ridge=args.calibration_ridge,
            max_abs_slope=args.max_abs_calibration_slope,
        )
        pred_val_dev_cal = apply_affine(pred_val_dev_uncal, cal_a, cal_b)

        val_uncal_rmse = rmse(y_val_raw, pred_val_dev_uncal)
        val_cal_rmse = rmse(y_val_raw, pred_val_dev_cal)
        val_uncal_corr = pearson(y_val_raw, pred_val_dev_uncal)
        val_cal_corr = pearson(y_val_raw, pred_val_dev_cal)

        print(
            f"best_epoch={best_epoch} "
            f"best_val_rmse_scaled={best_val_rmse_scaled} "
            f"cal_a={cal_a:.4f} cal_b={cal_b:.4f} "
            f"val_rmse_uncal={val_uncal_rmse:.4f} val_rmse_cal={val_cal_rmse:.4f}"
        )

        pred_test_scaled, test_binary_logits = mt.predict_multitask(model, x_test, args.batch_size, device)
        pred_test_dev_uncal = base.unscale_target(pred_test_scaled, y_fit_mean, y_fit_std)
        pred_test_dev_cal = apply_affine(pred_test_dev_uncal, cal_a, cal_b)

        true_dev_test, test_stim_mean = base.heldout_deviation(test_df, fit_df, score_col)
        true_score = test_df[score_col].to_numpy(dtype=float)

        baseline_rows = make_prediction_rows(
            test_df=test_df,
            target=args.target,
            model_name=BASELINE_MODEL,
            true_score=true_score,
            stim_mean=test_stim_mean,
            true_dev=true_dev_test,
            pred_dev=np.zeros_like(true_dev_test, dtype=float),
        )
        uncal_rows = make_prediction_rows(
            test_df=test_df,
            target=args.target,
            model_name=UNCAL_MODEL,
            true_score=true_score,
            stim_mean=test_stim_mean,
            true_dev=true_dev_test,
            pred_dev=pred_test_dev_uncal,
        )
        cal_rows = make_prediction_rows(
            test_df=test_df,
            target=args.target,
            model_name=CAL_MODEL,
            true_score=true_score,
            stim_mean=test_stim_mean,
            true_dev=true_dev_test,
            pred_dev=pred_test_dev_cal,
        )

        all_pred_rows.extend([baseline_rows, uncal_rows, cal_rows])

        for model_name, rows in [
            (BASELINE_MODEL, baseline_rows),
            (UNCAL_MODEL, uncal_rows),
            (CAL_MODEL, cal_rows),
        ]:
            fold_metric = {
                "target": args.target,
                "model": model_name,
                "test_subject": int(test_subject),
            }
            fold_metric.update(base.prediction_metrics(rows))
            fold_metric.update(base.deviation_metrics(rows))
            fold_metric.update({
                "best_epoch": int(best_epoch),
                "best_val_rmse_scaled": safe_float(best_val_rmse_scaled),
                "best_val_bce": safe_float(best_val_bce),
                "best_val_objective": safe_float(best_val_objective),
                "fit_subjects": int(len(fit_subjects)),
                "val_subjects": int(len(val_subjects)),
                "calibration_a": safe_float(cal_a),
                "calibration_b": safe_float(cal_b),
                "val_uncal_dev_rmse": safe_float(val_uncal_rmse),
                "val_cal_dev_rmse": safe_float(val_cal_rmse),
                "val_uncal_dev_pearson": safe_float(val_uncal_corr),
                "val_cal_dev_pearson": safe_float(val_cal_corr),
                "y_fit_mean": safe_float(y_fit_mean),
                "y_fit_std": safe_float(y_fit_std),
            })
            fold_rows.append(fold_metric)

        print(
            f"test uncal dev_pearson={base.deviation_metrics(uncal_rows)['dev_pearson']} "
            f"cal dev_pearson={base.deviation_metrics(cal_rows)['dev_pearson']} "
            f"uncal pred_std={base.deviation_metrics(uncal_rows)['pred_dev_std']} "
            f"cal pred_std={base.deviation_metrics(cal_rows)['pred_dev_std']}"
        )

    pred = pd.concat(all_pred_rows, ignore_index=True)
    pred = base.add_subset_flags(pred, selected)

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
        "protocol": "EEG validation-calibrated multitask residual smoke",
        "target": args.target,
        "cache": args.cache,
        "models": [BASELINE_MODEL, UNCAL_MODEL, CAL_MODEL],
        "baseline_note": "stimulus_fit_only uses fit-subject stimulus means only, because validation subjects are reserved for calibration.",
        "epochs_max": args.epochs,
        "patience": args.patience,
        "max_folds": args.max_folds,
        "test_subjects": test_subjects,
        "validation_subject_count": args.val_subject_count,
        "loss": {
            "residual": f"HuberLoss(delta={args.huber_delta}) on scaled residual",
            "auxiliary": "BCEWithLogitsLoss on raw high/low score label",
            "lambda_bce": args.lambda_bce,
        },
        "calibration": {
            "type": "validation affine residual calibration",
            "formula": "pred_dev_calibrated = a * pred_dev + b",
            "fit_scope": "validation subjects only, inside outer train fold",
            "ridge": args.calibration_ridge,
            "max_abs_slope": args.max_abs_calibration_slope,
        },
        "optimizer": {
            "name": "AdamW",
            "lr": args.lr,
            "weight_decay": args.weight_decay,
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
            "fold_safe_selected": str(base.FOLD_SAFE_SELECTED),
        },
        "main_metrics": main.to_dict(orient="records"),
        "subset_metrics": subset.to_dict(orient="records"),
        "fold_summary": fold_df.to_dict(orient="records"),
        "elapsed_sec": safe_float(time.perf_counter() - t0),
        "notes": [
            "This is a calibration diagnostic smoke run, not final full LOSO.",
            "The model is trained only on fit subjects.",
            "Validation subjects are used for epoch selection and affine calibration.",
            "The held-out test subject is used only for final evaluation.",
            "The baseline is fit-only stimulus mean, not the stronger outer-train stimulus-only baseline.",
            "If calibration helps, the next step is a full nested calibration protocol.",
        ],
    }

    OUT_JSON.write_text(json.dumps(clean_json(summary), indent=2, ensure_ascii=False), encoding="utf-8")

    main_cols = [
        "target", "model", "n",
        "mae", "rmse", "pearson", "balanced_accuracy", "auroc",
        "dev_rmse", "dev_pearson", "dev_sign_acc",
        "true_dev_std", "pred_dev_std",
        f"lift_vs_{BASELINE_MODEL}_rmse",
        f"lift_vs_{BASELINE_MODEL}_balanced_accuracy",
        f"lift_vs_{BASELINE_MODEL}_auroc",
        f"lift_vs_{BASELINE_MODEL}_dev_rmse",
    ]

    subset_cols = [
        "target", "subset", "model", "n",
        "rmse", "balanced_accuracy", "auroc",
        "dev_rmse", "dev_pearson",
        "true_dev_std", "pred_dev_std",
        f"lift_vs_{BASELINE_MODEL}_rmse",
        f"lift_vs_{BASELINE_MODEL}_balanced_accuracy",
        f"lift_vs_{BASELINE_MODEL}_auroc",
        f"lift_vs_{BASELINE_MODEL}_dev_rmse",
    ]

    fold_cols = [
        "test_subject", "model", "best_epoch",
        "rmse", "dev_rmse", "dev_pearson",
        "true_dev_std", "pred_dev_std",
        "calibration_a", "calibration_b",
        "val_uncal_dev_rmse", "val_cal_dev_rmse",
        "val_uncal_dev_pearson", "val_cal_dev_pearson",
    ]

    lines = []
    lines.append("# ROCA-I-DARE EEG Validation-Calibrated Smoke\n")
    lines.append("This is a calibration diagnostic smoke run, not final full LOSO.\n")

    lines.append("## Configuration\n")
    lines.append(f"- target: `{args.target}`")
    lines.append(f"- cache: `{args.cache}`")
    lines.append(f"- test_subjects: `{test_subjects}`")
    lines.append(f"- baseline: `{BASELINE_MODEL}`")
    lines.append(f"- uncalibrated model: `{UNCAL_MODEL}`")
    lines.append(f"- calibrated model: `{CAL_MODEL}`")
    lines.append(f"- affine calibration: `pred_dev_cal = a * pred_dev + b`")
    lines.append(f"- calibration ridge: `{args.calibration_ridge}`")
    lines.append(f"- max abs calibration slope: `{args.max_abs_calibration_slope}`")
    lines.append(f"- loss: `HuberResidual + {args.lambda_bce} * BCEHighLow`")
    lines.append("")

    lines.append("## Main metrics\n")
    lines.append(base.md_table(main.to_dict(orient="records"), main_cols))

    lines.append("\n## Fold-safe hard subset metrics\n")
    lines.append(base.md_table(subset.to_dict(orient="records"), subset_cols))

    lines.append("\n## Fold summary\n")
    lines.append(base.md_table(fold_df.to_dict(orient="records"), fold_cols))

    lines.append("\n## Interpretation guide\n")
    lines.append(
        f"- Positive `lift_vs_{BASELINE_MODEL}_rmse` means lower RMSE than the fit-only stimulus baseline.\n"
        "- This smoke uses fit-only stimulus means because validation subjects are reserved for calibration.\n"
        "- If calibrated rows improve RMSE/dev_pearson over uncalibrated rows, the issue is likely calibration/scale.\n"
        "- If calibration hurts, the next step should be residual-sign auxiliary or a different regression head/loss.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05f completed.")
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
