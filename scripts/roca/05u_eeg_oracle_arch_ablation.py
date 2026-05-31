#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
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
SRC = ROOT / "src"
ROCA_DIR = ROOT / "docs" / "roca"
ORACLE_SCRIPT = ROOT / "scripts" / "roca" / "05o_eeg_oracle_checkpoint_base.py"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from emotion_deap_idare.models.eeg_segment_classifier import EEGSegmentClassifier


def load_oracle_module():
    if not ORACLE_SCRIPT.exists():
        raise FileNotFoundError(ORACLE_SCRIPT)
    spec = importlib.util.spec_from_file_location("roca_05o_oracle_arch", ORACLE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module spec for {ORACLE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["roca_05o_oracle_arch"] = module
    spec.loader.exec_module(module)
    return module


oracle = load_oracle_module()


ARCH_CONFIGS: dict[str, dict[str, Any]] = {
    "A0_current": {
        "description": "Current model config: lite + GN + concat stem + learnable channel position + MHA mixer.",
        "modelsize": "lite",
        "norm_kind": "gn",
        "stem_fusion": "concat",
        "channel_pos_mode": "learnable",
        "channel_mixer": "mha",
        "dropout": 0.10,
        "head_dropout": 0.30,
    },
    "A1_low_dropout": {
        "description": "Same as current, but lower regularization. Tests underfitting.",
        "modelsize": "lite",
        "norm_kind": "gn",
        "stem_fusion": "concat",
        "channel_pos_mode": "learnable",
        "channel_mixer": "mha",
        "dropout": 0.05,
        "head_dropout": 0.10,
    },
    "A2_high_dropout": {
        "description": "Same as current, but higher regularization. Tests overfitting/noisy checkpointing.",
        "modelsize": "lite",
        "norm_kind": "gn",
        "stem_fusion": "concat",
        "channel_pos_mode": "learnable",
        "channel_mixer": "mha",
        "dropout": 0.20,
        "head_dropout": 0.40,
    },
    "A3_batchnorm": {
        "description": "Swap GroupNorm to BatchNorm inside temporal blocks/stem.",
        "modelsize": "lite",
        "norm_kind": "bn",
        "stem_fusion": "concat",
        "channel_pos_mode": "learnable",
        "channel_mixer": "mha",
        "dropout": 0.10,
        "head_dropout": 0.30,
    },
    "A4_stem_sum": {
        "description": "Use sum fusion for temporal branches instead of concat projection.",
        "modelsize": "lite",
        "norm_kind": "gn",
        "stem_fusion": "sum",
        "channel_pos_mode": "learnable",
        "channel_mixer": "mha",
        "dropout": 0.10,
        "head_dropout": 0.30,
    },
    "A5_stem_attn": {
        "description": "Use learned attention over temporal branches.",
        "modelsize": "lite",
        "norm_kind": "gn",
        "stem_fusion": "attn",
        "channel_pos_mode": "learnable",
        "channel_mixer": "mha",
        "dropout": 0.10,
        "head_dropout": 0.30,
    },
    "A6_stem_moe": {
        "description": "Use lightweight MoE-style gate over temporal branches.",
        "modelsize": "lite",
        "norm_kind": "gn",
        "stem_fusion": "moe",
        "channel_pos_mode": "learnable",
        "channel_mixer": "mha",
        "dropout": 0.10,
        "head_dropout": 0.30,
    },
    "A7_no_channel_mha": {
        "description": "Disable channel self-attention mixer. Tests whether MHA is noisy/overfitting.",
        "modelsize": "lite",
        "norm_kind": "gn",
        "stem_fusion": "concat",
        "channel_pos_mode": "learnable",
        "channel_mixer": "none",
        "dropout": 0.10,
        "head_dropout": 0.30,
    },
    "A8_no_channel_pos": {
        "description": "Disable learned channel identity embedding.",
        "modelsize": "lite",
        "norm_kind": "gn",
        "stem_fusion": "concat",
        "channel_pos_mode": "none",
        "channel_mixer": "mha",
        "dropout": 0.10,
        "head_dropout": 0.30,
    },
    "A9_base_capacity": {
        "description": "Use base encoder capacity instead of lite. Tests undercapacity vs overfitting.",
        "modelsize": "base",
        "norm_kind": "gn",
        "stem_fusion": "concat",
        "channel_pos_mode": "learnable",
        "channel_mixer": "mha",
        "dropout": 0.10,
        "head_dropout": 0.30,
    },
    "A10_lr_low": {
        "description": "Current architecture with lower LR=3e-5.",
        "modelsize": "lite",
        "norm_kind": "gn",
        "stem_fusion": "concat",
        "channel_pos_mode": "learnable",
        "channel_mixer": "mha",
        "dropout": 0.10,
        "head_dropout": 0.30,
        "lr": 3e-5,
    },
    "A11_lr_high": {
        "description": "Current architecture with higher LR=3e-4.",
        "modelsize": "lite",
        "norm_kind": "gn",
        "stem_fusion": "concat",
        "channel_pos_mode": "learnable",
        "channel_mixer": "mha",
        "dropout": 0.10,
        "head_dropout": 0.30,
        "lr": 3e-4,
    },
}


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


def parse_config_names(config_arg: str) -> list[str]:
    if config_arg.strip().lower() == "all":
        return list(ARCH_CONFIGS.keys())
    names = [x.strip() for x in config_arg.split(",") if x.strip()]
    bad = [x for x in names if x not in ARCH_CONFIGS]
    if bad:
        raise KeyError(f"Unknown arch configs: {bad}. Available: {list(ARCH_CONFIGS)}")
    return names


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--target", choices=["valence", "arousal"], default="arousal")
    p.add_argument("--cache", choices=["baseline_corrected", "raw"], default="baseline_corrected")
    p.add_argument("--max-folds", type=int, default=63)
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--patience", type=int, default=8)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--weight-decay", type=float, default=1e-3)
    p.add_argument("--huber-delta", type=float, default=1.0)
    p.add_argument("--val-subject-count", type=int, default=8)
    p.add_argument("--seed", type=int, default=20260513)
    p.add_argument("--num-workers", type=int, default=0)
    p.add_argument("--dropout", type=float, default=0.10)
    p.add_argument("--head-dropout", type=float, default=0.30)
    p.add_argument("--arch-configs", type=str, default="all")
    p.add_argument("--augment-config", type=str, default="gaussian_0p10")
    p.add_argument(
        "--clean-inner-validation",
        action="store_true",
        help="Use clean inner validation instead of oracle test checkpoint selection. Default is oracle/leaky diagnostic.",
    )
    p.add_argument("--out-prefix", type=str, default=None)
    return p.parse_args()


def make_model_factory(arch_cfg: dict[str, Any]):
    def make_model(args, device):
        model = EEGSegmentClassifier(
            C=32,
            sampling_rate=128,
            window_sec=5.0,
            n_classes=1,
            modelsize=str(arch_cfg.get("modelsize", "lite")),
            dropout=float(arch_cfg.get("dropout", args.dropout)),
            head_dropout=float(arch_cfg.get("head_dropout", args.head_dropout)),
            norm_kind=str(arch_cfg.get("norm_kind", "gn")),
            stem_fusion=str(arch_cfg.get("stem_fusion", "concat")),
            channel_pos_mode=str(arch_cfg.get("channel_pos_mode", "learnable")),
            channel_mixer=str(arch_cfg.get("channel_mixer", "mha")),
            use_spectral_branch=False,
            use_projection_head=True,
            projection_dim=64,
        )
        return model.to(device)

    return make_model


def args_for_arch(args, arch_cfg: dict[str, Any]):
    out = copy.copy(args)
    for key in ["lr", "dropout", "head_dropout", "weight_decay", "huber_delta"]:
        if key in arch_cfg:
            setattr(out, key.replace("-", "_"), arch_cfg[key])
    out.oracle_test_checkpoint_selection = not bool(args.clean_inner_validation)
    return out


def aggregate_main(pred: pd.DataFrame) -> pd.DataFrame:
    rows = []
    group_cols = ["arch_config", "augmentation_config", "target", "model"]

    for keys, g in pred.groupby(group_cols, dropna=False):
        arch_config, aug, target, model = keys
        row = {
            "arch_config": arch_config,
            "augmentation_config": aug,
            "target": target,
            "model": model,
        }
        row.update(oracle.base.prediction_metrics(g))
        row.update(oracle.base.deviation_metrics(g))
        rows.append(row)

    return pd.DataFrame(rows)


def add_lifts(main: pd.DataFrame) -> pd.DataFrame:
    lower_is_better = {"mae", "rmse", "dev_mae", "dev_rmse"}
    metrics = [
        "mae", "rmse", "pearson", "spearman",
        "balanced_accuracy", "macro_f1", "auroc",
        "dev_mae", "dev_rmse", "dev_pearson", "dev_spearman",
        "dev_sign_acc", "true_dev_std", "pred_dev_std",
    ]

    rows = []
    for _, g in main.groupby(["arch_config", "augmentation_config", "target"], dropna=False):
        base = g[g["model"].eq("stimulus_only")]
        if base.empty:
            continue
        base = base.iloc[0]

        for _, row in g.iterrows():
            out = row.to_dict()
            for metric in metrics:
                rv = row.get(metric, np.nan)
                bv = base.get(metric, np.nan)
                if pd.isna(rv) or pd.isna(bv):
                    out[f"lift_vs_stimulus_{metric}"] = None
                elif metric in lower_is_better:
                    out[f"lift_vs_stimulus_{metric}"] = safe_float(float(bv) - float(rv))
                else:
                    out[f"lift_vs_stimulus_{metric}"] = safe_float(float(rv) - float(bv))
            rows.append(out)

    return pd.DataFrame(rows)


def summarize_best(main: pd.DataFrame) -> pd.DataFrame:
    eeg = main[~main["model"].eq("stimulus_only")].copy()
    if eeg.empty:
        return pd.DataFrame()

    sort_cols = [
        "lift_vs_stimulus_rmse",
        "dev_pearson",
        "lift_vs_stimulus_auroc",
        "balanced_accuracy",
        "pred_dev_std",
    ]
    for col in sort_cols:
        if col not in eeg.columns:
            eeg[col] = np.nan

    return eeg.sort_values(
        by=["lift_vs_stimulus_rmse", "dev_pearson", "lift_vs_stimulus_auroc"],
        ascending=[False, False, False],
        na_position="last",
    ).reset_index(drop=True)


def md_table(df: pd.DataFrame, cols: list[str], max_rows: int | None = None) -> str:
    if df.empty:
        return "_No rows._\n"
    show = df.copy()
    if max_rows is not None:
        show = show.head(max_rows)
    existing = [c for c in cols if c in show.columns]
    lines = []
    lines.append("| " + " | ".join(existing) + " |")
    lines.append("| " + " | ".join(["---"] * len(existing)) + " |")
    for _, row in show.iterrows():
        vals = []
        for col in existing:
            val = row.get(col, "")
            if isinstance(val, float):
                vals.append(f"{val:.6f}" if math.isfinite(val) else "")
            elif pd.isna(val):
                vals.append("")
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def write_outputs(args, cfg_names, pred, main, best, fold_df, history_df, elapsed_sec, eeg_npy, eeg_index):
    prefix = args.out_prefix
    if prefix is None:
        mode = "oracle" if not args.clean_inner_validation else "clean"
        prefix = f"eeg_{mode}_arch_ablation_{args.target}_current"

    out_pred = ROCA_DIR / f"{prefix}_predictions.csv"
    out_main = ROCA_DIR / f"{prefix}_main_metrics.csv"
    out_best = ROCA_DIR / f"{prefix}_best_ranking.csv"
    out_fold = ROCA_DIR / f"{prefix}_fold_summary.csv"
    out_hist = ROCA_DIR / f"{prefix}_history.csv"
    out_json = ROCA_DIR / f"{prefix}.json"
    out_md = ROCA_DIR / f"{prefix}.md"

    pred.to_csv(out_pred, index=False)
    main.to_csv(out_main, index=False)
    best.to_csv(out_best, index=False)
    fold_df.to_csv(out_fold, index=False)
    history_df.to_csv(out_hist, index=False)

    summary = {
        "protocol": "EEG oracle architecture ablation over existing modular EEGSegmentClassifier",
        "target": args.target,
        "cache": args.cache,
        "augmentation_config": args.augment_config,
        "arch_configs": {name: ARCH_CONFIGS[name] for name in cfg_names},
        "oracle_test_checkpoint_selection": not bool(args.clean_inner_validation),
        "max_folds": args.max_folds,
        "epochs": args.epochs,
        "patience": args.patience,
        "batch_size": args.batch_size,
        "base_lr": args.lr,
        "weight_decay": args.weight_decay,
        "huber_delta": args.huber_delta,
        "seed": args.seed,
        "inputs": {
            "oracle_script": str(ORACLE_SCRIPT),
            "eeg_npy": str(eeg_npy),
            "eeg_index": str(eeg_index),
        },
        "outputs": {
            "predictions": str(out_pred),
            "main_metrics": str(out_main),
            "best_ranking": str(out_best),
            "fold_summary": str(out_fold),
            "history": str(out_hist),
            "markdown": str(out_md),
            "json": str(out_json),
        },
        "best_ranking": best.to_dict(orient="records"),
        "elapsed_sec": safe_float(elapsed_sec),
        "notes": [
            "This is an oracle/leaky upper-bound diagnostic unless --clean-inner-validation is used.",
            "It does not introduce a new model family; it changes only existing modular EEGSegmentClassifier/EEGSegmentEncoder options.",
            "Primary decision metrics: lift_vs_stimulus_rmse, dev_pearson, pred_dev_std, AUROC lift, balanced accuracy.",
            "A config is promising only if it improves residual prediction without merely inflating prediction variance.",
        ],
    }
    out_json.write_text(json.dumps(clean_json(summary), indent=2, ensure_ascii=False), encoding="utf-8")

    main_cols = [
        "arch_config", "augmentation_config", "target", "model", "n",
        "rmse", "lift_vs_stimulus_rmse",
        "balanced_accuracy", "lift_vs_stimulus_balanced_accuracy",
        "macro_f1", "auroc", "lift_vs_stimulus_auroc",
        "dev_rmse", "dev_pearson", "pred_dev_std", "true_dev_std",
    ]
    fold_cols = [
        "arch_config", "test_subject", "best_epoch", "best_val_rmse_scaled",
        "rmse", "balanced_accuracy", "auroc", "dev_rmse", "dev_pearson",
        "pred_dev_std", "true_dev_std", "final_train_last_loss",
    ]

    lines = []
    lines.append(f"# ROCA EEG {'Oracle' if not args.clean_inner_validation else 'Clean'} Architecture Ablation - {args.target}\n")
    lines.append("This report tests architecture-internal ablations of the existing EEGSegmentClassifier/EEGSegmentEncoder.\n")
    lines.append("## Configuration\n")
    lines.append(f"- target: `{args.target}`")
    lines.append(f"- cache: `{args.cache}`")
    lines.append(f"- augmentation_config: `{args.augment_config}`")
    lines.append(f"- oracle_test_checkpoint_selection: `{str(not args.clean_inner_validation).lower()}`")
    lines.append(f"- arch_configs: `{', '.join(cfg_names)}`")
    lines.append(f"- max_folds: `{args.max_folds}`")
    lines.append(f"- epochs/patience: `{args.epochs}` / `{args.patience}`")
    lines.append(f"- base optimizer: `AdamW(lr={args.lr}, weight_decay={args.weight_decay})`")
    lines.append("")
    lines.append("## Best EEG configs by RMSE lift, then dev_pearson\n")
    lines.append(md_table(best, main_cols, max_rows=20))
    lines.append("\n## All pooled/main metrics\n")
    lines.append(md_table(main, main_cols, max_rows=None))
    lines.append("\n## Fold summary\n")
    lines.append(md_table(fold_df, fold_cols, max_rows=80))
    lines.append("\n## Interpretation\n")
    lines.append(
        "- Positive `lift_vs_stimulus_rmse` means the EEG residual model beats stimulus-only RMSE.\n"
        "- `dev_pearson` measures whether predicted residuals track true subject-specific deviations.\n"
        "- `pred_dev_std` must be read against `true_dev_std`; variance inflation alone is not success.\n"
        "- Because oracle mode uses the test subject for checkpoint selection, this is an upper-bound diagnostic, not a clean result.\n"
    )
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05u completed.")
    for p in [out_md, out_json, out_main, out_best, out_fold, out_hist, out_pred]:
        print(f"wrote: {p}")

    print("\nBest ranking:")
    print(best[[c for c in main_cols if c in best.columns]].head(20).to_string(index=False))


def main():
    args = parse_args()
    cfg_names = parse_config_names(args.arch_configs)

    if args.augment_config not in oracle.AUGMENTATION_CONFIGS:
        raise KeyError(
            f"Unknown augment config: {args.augment_config}. "
            f"Available: {list(oracle.AUGMENTATION_CONFIGS)}"
        )

    args.oracle_test_checkpoint_selection = not bool(args.clean_inner_validation)

    t0 = time.perf_counter()
    ROCA_DIR.mkdir(parents=True, exist_ok=True)

    x_mmap, idx, stim_pred, selected, eeg_npy, eeg_index = oracle.base.load_inputs(args)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("[INFO] ROCA step 05u EEG architecture ablation")
    print(f"[INFO] device={device}")
    print(f"[INFO] target={args.target}")
    print(f"[INFO] cache={args.cache}")
    print(f"[INFO] augment_config={args.augment_config}")
    print(f"[INFO] oracle_test_checkpoint_selection={args.oracle_test_checkpoint_selection}")
    print(f"[INFO] configs={cfg_names}")

    all_pred = []
    all_folds = []
    all_history = []

    original_make_model = oracle.base.make_model
    original_model_name = oracle.MODEL_NAME

    try:
        for arch_name in cfg_names:
            arch_cfg = ARCH_CONFIGS[arch_name]
            arch_args = args_for_arch(args, arch_cfg)

            oracle.base.set_seed(int(args.seed))
            oracle.base.make_model = make_model_factory(arch_cfg)
            oracle.MODEL_NAME = f"eeg_oracle_arch_{arch_name}"

            print("\n" + "=" * 88)
            print(f"[ARCH] {arch_name}: {arch_cfg['description']}")
            print(json.dumps(clean_json(arch_cfg), indent=2, ensure_ascii=False))
            print("=" * 88)

            pred, fold_df, history_df = oracle.run_one_config(
                args=arch_args,
                aug_name=args.augment_config,
                aug_cfg=oracle.AUGMENTATION_CONFIGS[args.augment_config],
                x_mmap=x_mmap,
                idx=idx,
                stim_pred=stim_pred,
                selected=selected,
                device=device,
            )

            pred["arch_config"] = arch_name
            pred["arch_description"] = arch_cfg["description"]
            fold_df["arch_config"] = arch_name
            fold_df["arch_description"] = arch_cfg["description"]
            history_df["arch_config"] = arch_name
            history_df["arch_description"] = arch_cfg["description"]

            all_pred.append(pred)
            all_folds.append(fold_df)
            all_history.append(history_df)

    finally:
        oracle.base.make_model = original_make_model
        oracle.MODEL_NAME = original_model_name

    pred_df = pd.concat(all_pred, ignore_index=True)
    fold_df = pd.concat(all_folds, ignore_index=True)
    history_df = pd.concat(all_history, ignore_index=True)

    main_df = add_lifts(aggregate_main(pred_df))
    best_df = summarize_best(main_df)

    write_outputs(
        args=args,
        cfg_names=cfg_names,
        pred=pred_df,
        main=main_df,
        best=best_df,
        fold_df=fold_df,
        history_df=history_df,
        elapsed_sec=time.perf_counter() - t0,
        eeg_npy=eeg_npy,
        eeg_index=eeg_index,
    )


if __name__ == "__main__":
    main()
