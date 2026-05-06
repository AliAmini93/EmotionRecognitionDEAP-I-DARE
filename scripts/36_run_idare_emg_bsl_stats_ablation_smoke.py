#!/usr/bin/env python3
"""Run I-DARE EMG response + BSL stats ablation smoke.

The main EMG input is the existing baseline-corrected EMG feature cache.
The sidecar input is compact preceding-BSL EMG summary stats.
No raw I-DARE EMG HDF5/MAT files are loaded inside training loops.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_FEATURE_NPY = ROOT / ".cache" / "idare_emg_features.npy"
DEFAULT_FEATURE_INDEX = ROOT / ".cache" / "idare_emg_feature_cache_index.csv"
DEFAULT_BSL_STATS_NPY = ROOT / ".cache" / "idare_emg_bsl_stats.npy"
DEFAULT_BSL_STATS_INDEX = ROOT / ".cache" / "idare_emg_bsl_stats_index.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "idare_emg_bsl_stats_ablation_smoke.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "idare_emg_bsl_stats_ablation_smoke.json"
DEFAULT_OUT_PRED = ROOT / "docs" / "idare_emg_bsl_stats_ablation_smoke_predictions.csv"

EPS = 1e-8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-npy", type=Path, default=DEFAULT_FEATURE_NPY)
    parser.add_argument("--feature-index", type=Path, default=DEFAULT_FEATURE_INDEX)
    parser.add_argument("--bsl-stats-npy", type=Path, default=DEFAULT_BSL_STATS_NPY)
    parser.add_argument("--bsl-stats-index", type=Path, default=DEFAULT_BSL_STATS_INDEX)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-predictions-csv", type=Path, default=DEFAULT_OUT_PRED)
    parser.add_argument("--tasks", nargs="+", default=["valence"], choices=["valence", "arousal"])
    parser.add_argument("--label-policy", default="midpoint_as_high", choices=["midpoint_as_high", "midpoint_as_low", "discard_midpoint"])
    parser.add_argument("--recipes", nargs="+", default=["ce_class_weighted"], choices=["ce_class_weighted", "balanced_sampler_ce"])
    parser.add_argument("--folds", type=int, default=6)
    parser.add_argument("--seeds", nargs="+", type=int, default=[11])
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--max-runs", type=int, default=4)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--zclip", type=float, default=8.0)
    return parser.parse_args()


def safe_json(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [safe_json(v) for v in obj]
    if isinstance(obj, tuple):
        return [safe_json(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        value = float(obj)
        return None if math.isnan(value) else value
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def finite_summary(values: list[float]) -> dict[str, float | None]:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"mean": None, "std": None, "median": None, "min": None, "max": None}
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "median": float(np.median(arr)),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def label_column(task: str, policy: str) -> str:
    return f"{task}_{policy}"


def make_subject_folds(subjects: list[int], folds: int, seed: int) -> list[list[int]]:
    rng = np.random.default_rng(seed)
    shuffled = np.asarray(subjects, dtype=int)
    rng.shuffle(shuffled)
    chunks = np.array_split(shuffled, folds)
    return [sorted([int(x) for x in chunk.tolist()]) for chunk in chunks if len(chunk) > 0]


def confusion_counts(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, int]:
    yt = y_true.astype(int)
    yp = y_pred.astype(int)
    return {
        "tn": int(((yt == 0) & (yp == 0)).sum()),
        "fp": int(((yt == 0) & (yp == 1)).sum()),
        "fn": int(((yt == 1) & (yp == 0)).sum()),
        "tp": int(((yt == 1) & (yp == 1)).sum()),
    }


def metrics_from_predictions(y_true: np.ndarray, y_pred: np.ndarray, p1: np.ndarray | None = None) -> dict[str, Any]:
    cm = confusion_counts(y_true, y_pred)
    tn, fp, fn, tp = cm["tn"], cm["fp"], cm["fn"], cm["tp"]
    n = max(1, len(y_true))
    acc = float((y_true == y_pred).sum() / n)

    recall0 = tn / max(1, tn + fp)
    recall1 = tp / max(1, tp + fn)
    bal_acc = float((recall0 + recall1) / 2.0)

    f1s = []
    for cls in [0, 1]:
        pred_pos = y_pred == cls
        true_pos = y_true == cls
        tp_cls = int((pred_pos & true_pos).sum())
        fp_cls = int((pred_pos & ~true_pos).sum())
        fn_cls = int((~pred_pos & true_pos).sum())
        precision = tp_cls / max(1, tp_cls + fp_cls)
        recall = tp_cls / max(1, tp_cls + fn_cls)
        f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
        f1s.append(f1)

    values, counts = np.unique(y_pred.astype(int), return_counts=True)
    pred_counts = {str(int(v)): int(c) for v, c in zip(values, counts)}
    pred_counts.setdefault("0", 0)
    pred_counts.setdefault("1", 0)

    y_counts = {0: int((y_true == 0).sum()), 1: int((y_true == 1).sum())}
    majority_class = 1 if y_counts[1] >= y_counts[0] else 0
    majority_pred = np.full_like(y_true, majority_class)
    majority_acc = float((majority_pred == y_true).sum() / n)

    out = {
        "accuracy": acc,
        "balanced_accuracy": bal_acc,
        "macro_f1": float(np.mean(f1s)),
        "confusion": cm,
        "pred_counts": pred_counts,
        "one_class_pred": bool(len(np.unique(y_pred)) == 1),
        "majority_baseline": {
            "class": int(majority_class),
            "accuracy": majority_acc,
            "label_counts": {"0": y_counts[0], "1": y_counts[1]},
        },
    }
    if p1 is not None:
        p1 = np.asarray(p1, dtype=np.float64)
        out["p1_summary"] = {
            "mean": float(p1.mean()),
            "q05": float(np.quantile(p1, 0.05)),
            "median": float(np.median(p1)),
            "q95": float(np.quantile(p1, 0.95)),
        }
    return out


def threshold_sweep(y_true: np.ndarray, p1: np.ndarray) -> dict[str, Any]:
    rows = []
    for thr in np.arange(0.05, 0.951, 0.05):
        pred = (p1 >= thr).astype(int)
        m = metrics_from_predictions(y_true, pred)
        rows.append({
            "threshold": float(round(float(thr), 4)),
            "macro_f1": m["macro_f1"],
            "balanced_accuracy": m["balanced_accuracy"],
            "accuracy": m["accuracy"],
            "pred_counts": m["pred_counts"],
            "one_class_pred": m["one_class_pred"],
        })
    best = max(rows, key=lambda r: (r["macro_f1"], r["balanced_accuracy"], -abs(r["threshold"] - 0.5)))
    return {"best": best, "rows": rows}


class EMGBSLStatsDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray, rows: np.ndarray) -> None:
        self.x = x.astype(np.float32, copy=False)
        self.y = y.astype(np.int64, copy=False)
        self.rows = rows.astype(np.int64, copy=False)

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, idx: int):
        return (
            torch.from_numpy(self.x[idx].copy()),
            torch.tensor(int(self.y[idx]), dtype=torch.long),
            torch.tensor(int(self.rows[idx]), dtype=torch.long),
        )


class TinyEMGBSLStatsMLP(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(hidden_dim, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


@torch.no_grad()
def evaluate_model(model: nn.Module, loader: DataLoader, device: torch.device) -> dict[str, Any]:
    model.eval()
    ys: list[int] = []
    preds: list[int] = []
    p1s: list[float] = []
    rows: list[int] = []
    for x, y, row in loader:
        x = x.to(device)
        logits = model(x)
        prob = torch.softmax(logits, dim=1)[:, 1].detach().cpu().numpy()
        pred = (prob >= 0.5).astype(int)
        ys.extend(y.numpy().astype(int).tolist())
        preds.extend(pred.astype(int).tolist())
        p1s.extend(prob.astype(float).tolist())
        rows.extend(row.numpy().astype(int).tolist())

    y_arr = np.asarray(ys, dtype=int)
    p_arr = np.asarray(p1s, dtype=float)
    pred_arr = np.asarray(preds, dtype=int)
    final = metrics_from_predictions(y_arr, pred_arr, p_arr)
    final["threshold_sweep"] = threshold_sweep(y_arr, p_arr)
    final["prediction_rows"] = rows
    final["prediction_y_true"] = y_arr.astype(int).tolist()
    final["prediction_y_pred"] = pred_arr.astype(int).tolist()
    final["prediction_p1"] = p_arr.astype(float).tolist()
    return final


def train_one_run(
    x_all: np.ndarray,
    labels: np.ndarray,
    index_df: pd.DataFrame,
    *,
    task: str,
    policy: str,
    recipe: str,
    fold_id: int,
    seed: int,
    val_subjects: list[int],
    epochs: int,
    lr: float,
    batch_size: int,
    hidden_dim: int,
    zclip: float,
    device: torch.device,
    run_id: int,
) -> dict[str, Any]:
    set_seed(seed)

    subject_ids = index_df["subject_id"].astype(int).to_numpy()
    valid = np.isfinite(labels)
    val_mask = np.isin(subject_ids, np.asarray(val_subjects, dtype=int)) & valid
    train_mask = (~np.isin(subject_ids, np.asarray(val_subjects, dtype=int))) & valid

    train_rows = np.where(train_mask)[0]
    val_rows = np.where(val_mask)[0]
    if len(train_rows) == 0 or len(val_rows) == 0:
        raise ValueError(f"empty split for fold={fold_id}")

    x_train_raw = x_all[train_rows].astype(np.float32, copy=False)
    x_val_raw = x_all[val_rows].astype(np.float32, copy=False)

    mu = x_train_raw.mean(axis=0, keepdims=True)
    sigma = x_train_raw.std(axis=0, keepdims=True)
    sigma = np.where(sigma < EPS, 1.0, sigma)
    x_train = np.clip((x_train_raw - mu) / sigma, -zclip, zclip).astype(np.float32)
    x_val = np.clip((x_val_raw - mu) / sigma, -zclip, zclip).astype(np.float32)

    y_train = labels[train_rows].astype(int)
    y_val = labels[val_rows].astype(int)

    train_ds = EMGBSLStatsDataset(x_train, y_train, train_rows)
    val_ds = EMGBSLStatsDataset(x_val, y_val, val_rows)

    class_counts = np.bincount(y_train, minlength=2).astype(np.float64)
    class_weights = class_counts.sum() / np.maximum(class_counts, 1.0)
    class_weights = class_weights / class_weights.mean()

    if recipe == "balanced_sampler_ce":
        sample_weights = class_weights[y_train]
        generator = torch.Generator()
        generator.manual_seed(seed)
        sampler = WeightedRandomSampler(
            weights=torch.as_tensor(sample_weights, dtype=torch.double),
            num_samples=len(sample_weights),
            replacement=True,
            generator=generator,
        )
        train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler)
        criterion = nn.CrossEntropyLoss()
    elif recipe == "ce_class_weighted":
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
        criterion = nn.CrossEntropyLoss(weight=torch.as_tensor(class_weights, dtype=torch.float32, device=device))
    else:
        raise ValueError(recipe)

    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    train_eval_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=False)

    model = TinyEMGBSLStatsMLP(input_dim=x_train.shape[1], hidden_dim=hidden_dim).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    history = []
    for epoch in range(1, epochs + 1):
        model.train()
        losses: list[float] = []
        for x, y, _ in train_loader:
            x = x.to(device)
            y = y.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu().item()))
        history.append({"epoch": epoch, "train_loss": float(np.mean(losses)) if losses else None})

    final = evaluate_model(model, val_loader, device)
    train_final = evaluate_model(model, train_eval_loader, device)

    run = {
        "run_id": run_id,
        "task": task,
        "policy": policy,
        "recipe": recipe,
        "fold_id": fold_id,
        "seed": seed,
        "val_subjects": val_subjects,
        "train_n": int(len(train_rows)),
        "val_n": int(len(val_rows)),
        "input_dim": int(x_train.shape[1]),
        "train_label_counts": {"0": int((y_train == 0).sum()), "1": int((y_train == 1).sum())},
        "val_label_counts": {"0": int((y_val == 0).sum()), "1": int((y_val == 1).sum())},
        "standardization": {
            "train_fold_mean_std_only": True,
            "zclip": float(zclip),
            "zero_std_features": int((sigma <= EPS).sum()),
        },
        "history": history,
        "train_final": {k: v for k, v in train_final.items() if not k.startswith("prediction_")},
        "final": {k: v for k, v in final.items() if not k.startswith("prediction_")},
        "prediction_rows": final["prediction_rows"],
        "prediction_y_true": final["prediction_y_true"],
        "prediction_y_pred": final["prediction_y_pred"],
        "prediction_p1": final["prediction_p1"],
    }
    print(json.dumps({
        "run_id": run_id,
        "task": task,
        "recipe": recipe,
        "fold": fold_id,
        "final_macro_f1": run["final"]["macro_f1"],
        "final_balanced_accuracy": run["final"]["balanced_accuracy"],
        "final_accuracy": run["final"]["accuracy"],
        "majority_accuracy": run["final"]["majority_baseline"]["accuracy"],
        "one_class_pred": run["final"]["one_class_pred"],
        "pred_counts": run["final"]["pred_counts"],
        "confusion": run["final"]["confusion"],
    }, sort_keys=True))
    return run


def aggregate_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        groups[(run["task"], run["policy"], run["recipe"])].append(run)

    rows = []
    for (task, policy, recipe), group in sorted(groups.items()):
        final_macro = [float(r["final"]["macro_f1"]) for r in group]
        final_bal = [float(r["final"]["balanced_accuracy"]) for r in group]
        final_acc = [float(r["final"]["accuracy"]) for r in group]
        majority_acc = [float(r["final"]["majority_baseline"]["accuracy"]) for r in group]
        threshold_macro = [float(r["final"]["threshold_sweep"]["best"]["macro_f1"]) for r in group]
        threshold_bal = [float(r["final"]["threshold_sweep"]["best"]["balanced_accuracy"]) for r in group]
        threshold_values = [float(r["final"]["threshold_sweep"]["best"]["threshold"]) for r in group]
        rows.append({
            "task": task,
            "policy": policy,
            "recipe": recipe,
            "runs": int(len(group)),
            "final_macro_f1": finite_summary(final_macro),
            "final_balanced_accuracy": finite_summary(final_bal),
            "final_accuracy": finite_summary(final_acc),
            "majority_accuracy": finite_summary(majority_acc),
            "threshold_best_macro_f1": finite_summary(threshold_macro),
            "threshold_best_balanced_accuracy": finite_summary(threshold_bal),
            "threshold_best_value": finite_summary(threshold_values),
            "threshold_gain_macro_f1": finite_summary([b - a for a, b in zip(final_macro, threshold_macro)]),
            "threshold_gain_balanced_accuracy": finite_summary([b - a for a, b in zip(final_bal, threshold_bal)]),
            "one_class_final_runs": int(sum(1 for r in group if r["final"]["one_class_pred"])),
            "threshold_one_class_final_runs": int(sum(1 for r in group if r["final"]["threshold_sweep"]["best"]["one_class_pred"])),
        })
    return rows


def write_predictions_csv(path: Path, runs: list[dict[str, Any]], index_df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run_id", "task", "policy", "recipe", "fold_id", "seed",
        "cache_row", "subject_id", "stimulus_id", "y_true", "y_pred", "p1",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for run in runs:
            rows = run["prediction_rows"]
            y_true = run["prediction_y_true"]
            y_pred = run["prediction_y_pred"]
            p1 = run["prediction_p1"]
            for row_id, yt, yp, prob in zip(rows, y_true, y_pred, p1):
                meta = index_df.iloc[int(row_id)]
                writer.writerow({
                    "run_id": run["run_id"],
                    "task": run["task"],
                    "policy": run["policy"],
                    "recipe": run["recipe"],
                    "fold_id": run["fold_id"],
                    "seed": run["seed"],
                    "cache_row": int(row_id),
                    "subject_id": int(meta["subject_id"]),
                    "stimulus_id": meta.get("stimulus_id"),
                    "y_true": int(yt),
                    "y_pred": int(yp),
                    "p1": float(prob),
                })


def build_report_md(report: dict[str, Any]) -> str:
    cfg = report["config"]
    lines: list[str] = []
    lines.append("# I-DARE EMG Response + BSL Stats Ablation Smoke\n")
    lines.append("This report was generated by `scripts/36_run_idare_emg_bsl_stats_ablation_smoke.py`.\n")
    lines.append("No raw I-DARE EMG HDF5/MAT files were loaded inside training loops.\n")
    lines.append("## Inputs\n")
    lines.append(f"- feature_npy: `{cfg['feature_npy']}`")
    lines.append(f"- feature_index: `{cfg['feature_index']}`")
    lines.append(f"- bsl_stats_npy: `{cfg['bsl_stats_npy']}`")
    lines.append(f"- bsl_stats_index: `{cfg['bsl_stats_index']}`\n")
    lines.append("## Run Scope\n")
    lines.append(f"- label_policy: `{cfg['label_policy']}`")
    lines.append(f"- tasks: `{', '.join(cfg['tasks'])}`")
    lines.append(f"- recipes: `{', '.join(cfg['recipes'])}`")
    lines.append(f"- epochs: `{cfg['epochs']}`")
    lines.append(f"- max_runs: `{cfg['max_runs']}`")
    lines.append(f"- device: `{cfg['device']}`")
    lines.append(f"- model: `TinyEMGBSLStatsMLP(input_dim={cfg['input_dim']}, hidden_dim={cfg['hidden_dim']})`")
    lines.append(f"- BSL stats standardization: train-fold mean/std only, zclip `{cfg['zclip']}`\n")

    lines.append("## Aggregate\n")
    lines.append("| Task | Policy | Recipe | Runs | Final macro F1 | Final bal acc | Final acc | Threshold macro F1 | Threshold bal acc | One-class final runs | Majority acc |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in report["aggregate"]:
        lines.append(
            f"| {row['task']} | {row['policy']} | {row['recipe']} | {row['runs']} | "
            f"{row['final_macro_f1']['mean']:.4f} | {row['final_balanced_accuracy']['mean']:.4f} | "
            f"{row['final_accuracy']['mean']:.4f} | {row['threshold_best_macro_f1']['mean']:.4f} | "
            f"{row['threshold_best_balanced_accuracy']['mean']:.4f} | {row['one_class_final_runs']} | "
            f"{row['majority_accuracy']['mean']:.4f} |"
        )
    lines.append("")

    lines.append("## Aggregate Threshold Diagnostics\n")
    lines.append("| Task | Policy | Recipe | Runs | Mean threshold | Macro F1 gain | Bal acc gain | Threshold one-class runs |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|")
    for row in report["aggregate"]:
        lines.append(
            f"| {row['task']} | {row['policy']} | {row['recipe']} | {row['runs']} | "
            f"{row['threshold_best_value']['mean']:.4f} | {row['threshold_gain_macro_f1']['mean']:.4f} | "
            f"{row['threshold_gain_balanced_accuracy']['mean']:.4f} | {row['threshold_one_class_final_runs']} |"
        )
    lines.append("")

    lines.append("## Per-run Final Diagnostics\n")
    lines.append("| Run | Task | Recipe | Fold | Seed | Train n | Val n | Macro F1 | Bal acc | Acc | Pred 0 | Pred 1 | TN | FP | FN | TP | One-class | Majority acc |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|")
    for run in report["runs"]:
        f = run["final"]
        cm = f["confusion"]
        pc = f["pred_counts"]
        lines.append(
            f"| {run['run_id']} | {run['task']} | {run['recipe']} | {run['fold_id']} | {run['seed']} | "
            f"{run['train_n']} | {run['val_n']} | {f['macro_f1']:.4f} | {f['balanced_accuracy']:.4f} | "
            f"{f['accuracy']:.4f} | {pc.get('0', 0)} | {pc.get('1', 0)} | "
            f"{cm['tn']} | {cm['fp']} | {cm['fn']} | {cm['tp']} | "
            f"{str(f['one_class_pred']).lower()} | {f['majority_baseline']['accuracy']:.4f} |"
        )
    lines.append("")

    lines.append("## Probability / Threshold Diagnostics\n")
    lines.append("| Run | Task | Recipe | P1 mean | P1 q05 | P1 median | P1 q95 | Best threshold | Best threshold macro F1 | Best threshold bal acc |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for run in report["runs"]:
        f = run["final"]
        ps = f["p1_summary"]
        best = f["threshold_sweep"]["best"]
        lines.append(
            f"| {run['run_id']} | {run['task']} | {run['recipe']} | "
            f"{ps['mean']:.4f} | {ps['q05']:.4f} | {ps['median']:.4f} | {ps['q95']:.4f} | "
            f"{best['threshold']:.4f} | {best['macro_f1']:.4f} | {best['balanced_accuracy']:.4f} |"
        )
    lines.append("")

    lines.append("## Notes\n")
    lines.append("- This is a smoke/stabilization report, not a final LOSO result.")
    lines.append("- Main EMG input is the existing baseline-corrected STIM-BSL EMG feature cache.")
    lines.append("- BSL stats are compact sidecar features, standardized with train-fold statistics only.")
    lines.append("- This is the EMG counterpart of the EEG BSL-stats sidecar ablation.\n")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    start = time.perf_counter()

    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_predictions_csv.parent.mkdir(parents=True, exist_ok=True)

    feature_arr = np.load(args.feature_npy, mmap_mode="r")
    bsl_arr = np.load(args.bsl_stats_npy, mmap_mode="r")
    feature_df = pd.read_csv(args.feature_index)
    bsl_df = pd.read_csv(args.bsl_stats_index)

    if feature_arr.shape[0] != bsl_arr.shape[0]:
        raise ValueError(f"row mismatch: feature={feature_arr.shape}, bsl={bsl_arr.shape}")
    if len(feature_df) != len(bsl_df) or len(feature_df) != feature_arr.shape[0]:
        raise ValueError("index/cache row mismatch")

    for col in ["cache_row", "subject_id"]:
        if col in feature_df.columns and col in bsl_df.columns:
            if not np.array_equal(feature_df[col].to_numpy(), bsl_df[col].to_numpy()):
                raise ValueError(f"index alignment mismatch on {col}")
    if "stimulus_id" in feature_df.columns and "stimulus_id" in bsl_df.columns:
        if not feature_df["stimulus_id"].astype(str).equals(bsl_df["stimulus_id"].astype(str)):
            raise ValueError("index alignment mismatch on stimulus_id")

    x_all = np.concatenate([
        np.asarray(feature_arr[:], dtype=np.float32),
        np.asarray(bsl_arr[:], dtype=np.float32),
    ], axis=1)

    subjects = sorted(feature_df["subject_id"].dropna().astype(int).unique().tolist())
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("[INFO] I-DARE EMG response + BSL stats ablation smoke")
    print(f"[INFO] feature_npy={args.feature_npy}")
    print(f"[INFO] feature_index={args.feature_index}")
    print(f"[INFO] bsl_stats_npy={args.bsl_stats_npy}")
    print(f"[INFO] bsl_stats_index={args.bsl_stats_index}")
    print(f"[INFO] feature_shape={list(feature_arr.shape)}")
    print(f"[INFO] bsl_stats_shape={list(bsl_arr.shape)}")
    print(f"[INFO] input_dim={x_all.shape[1]}")
    print(f"[INFO] label_policy={args.label_policy}")
    print(f"[INFO] tasks={args.tasks}")
    print(f"[INFO] recipes={args.recipes}")
    print(f"[INFO] epochs={args.epochs}")
    print(f"[INFO] max_runs={args.max_runs}")
    print(f"[INFO] device={device}")

    planned = []
    for task in args.tasks:
        col = label_column(task, args.label_policy)
        if col not in feature_df.columns:
            raise KeyError(f"missing label column in feature index: {col}")
        for seed in args.seeds:
            folds = make_subject_folds(subjects, args.folds, seed)
            for fold_id, val_subjects in enumerate(folds, start=1):
                for recipe in args.recipes:
                    planned.append((task, seed, fold_id, val_subjects, recipe))
    if args.max_runs is not None:
        planned = planned[:args.max_runs]
    print(f"[INFO] planned_runs={len(planned)}")

    runs: list[dict[str, Any]] = []
    for i, (task, seed, fold_id, val_subjects, recipe) in enumerate(planned, start=1):
        col = label_column(task, args.label_policy)
        labels = feature_df[col].to_numpy(dtype=np.float64)
        print(
            f"[RUN] {i}/{len(planned)} task={task} policy={args.label_policy} "
            f"recipe={recipe} fold={fold_id} seed={seed} val_subjects={val_subjects}"
        )
        run = train_one_run(
            x_all,
            labels,
            feature_df,
            task=task,
            policy=args.label_policy,
            recipe=recipe,
            fold_id=fold_id,
            seed=seed,
            val_subjects=val_subjects,
            epochs=args.epochs,
            lr=args.lr,
            batch_size=args.batch_size,
            hidden_dim=args.hidden_dim,
            zclip=args.zclip,
            device=device,
            run_id=i,
        )
        runs.append(run)

    aggregate = aggregate_runs(runs)
    report = {
        "status": "PASSED",
        "generated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "config": {
            "feature_npy": str(args.feature_npy),
            "feature_index": str(args.feature_index),
            "bsl_stats_npy": str(args.bsl_stats_npy),
            "bsl_stats_index": str(args.bsl_stats_index),
            "feature_shape": list(feature_arr.shape),
            "bsl_stats_shape": list(bsl_arr.shape),
            "input_dim": int(x_all.shape[1]),
            "label_policy": args.label_policy,
            "tasks": args.tasks,
            "recipes": args.recipes,
            "folds": args.folds,
            "seeds": args.seeds,
            "epochs": args.epochs,
            "lr": args.lr,
            "batch_size": args.batch_size,
            "max_runs": args.max_runs,
            "hidden_dim": args.hidden_dim,
            "zclip": args.zclip,
            "device": str(device),
            "model": "TinyEMGBSLStatsMLP",
            "main_input": "baseline-corrected STIM-BSL EMG feature cache",
            "sidecar_input": "compact preceding-BSL EMG summary stats",
        },
        "aggregate": aggregate,
        "runs": runs,
        "elapsed_sec": float(time.perf_counter() - start),
    }

    write_predictions_csv(args.out_predictions_csv, runs, feature_df)
    args.out_json.write_text(json.dumps(safe_json(report), indent=2, ensure_ascii=False), encoding="utf-8")
    args.out_md.write_text(build_report_md(safe_json(report)), encoding="utf-8")

    print(f"[DONE] wrote {args.out_predictions_csv}")
    print(f"[DONE] wrote {args.out_md}")
    print(f"[DONE] wrote {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
