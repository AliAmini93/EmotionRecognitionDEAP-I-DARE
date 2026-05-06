#!/usr/bin/env python3
"""Run a small I-DARE raw EMG-only training smoke.

Input cache:
- .cache/idare_raw_emg_windows_2x10000_float32.npy  [n, 2, 10000]
- .cache/idare_raw_emg_cache_index.csv

This is a smoke/stabilization script, not a final LOSO experiment.
It trains a tiny 1D CNN on cached raw EMG windows only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW_NPY = ROOT / ".cache" / "idare_raw_emg_windows_2x10000_float32.npy"
DEFAULT_RAW_INDEX = ROOT / ".cache" / "idare_raw_emg_cache_index.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "idare_raw_emg_training_smoke.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "idare_raw_emg_training_smoke.json"
DEFAULT_OUT_PRED = ROOT / "docs" / "idare_raw_emg_training_smoke_predictions.csv"


@dataclass(frozen=True)
class Fold:
    fold_id: int
    val_subjects: list[int]


class RawEMGDataset(Dataset):
    def __init__(self, raw: np.ndarray, row_indices: np.ndarray, labels: np.ndarray):
        self.raw = raw
        self.row_indices = np.asarray(row_indices, dtype=np.int64)
        self.labels = np.asarray(labels, dtype=np.int64)

    def __len__(self) -> int:
        return int(self.row_indices.shape[0])

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        row = int(self.row_indices[idx])
        x = np.asarray(self.raw[row], dtype=np.float32)
        y = int(self.labels[idx])
        return torch.from_numpy(x.copy()), torch.tensor(y, dtype=torch.long), torch.tensor(row, dtype=torch.long)


class TinyRawEMGCNN(nn.Module):
    def __init__(self, in_channels: int = 2, n_classes: int = 2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(in_channels, 16, kernel_size=51, stride=8, padding=25),
            nn.BatchNorm1d(16),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(kernel_size=4, stride=4),
            nn.Conv1d(16, 32, kernel_size=25, stride=4, padding=12),
            nn.BatchNorm1d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool1d(kernel_size=4, stride=4),
            nn.Conv1d(32, 64, kernel_size=9, stride=2, padding=4),
            nn.BatchNorm1d(64),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
            nn.Dropout(p=0.20),
            nn.Linear(64, n_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-npy", type=Path, default=DEFAULT_RAW_NPY)
    parser.add_argument("--raw-index", type=Path, default=DEFAULT_RAW_INDEX)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-predictions-csv", type=Path, default=DEFAULT_OUT_PRED)
    parser.add_argument("--tasks", nargs="+", default=["valence"])
    parser.add_argument("--label-policy", default="midpoint_as_high", choices=["midpoint_as_high", "midpoint_as_low", "discard_midpoint"])
    parser.add_argument("--recipes", nargs="+", default=["ce_class_weighted"], choices=["ce_class_weighted", "balanced_sampler_ce"])
    parser.add_argument("--folds", type=int, default=6)
    parser.add_argument("--seeds", nargs="+", type=int, default=[11])
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--max-runs", type=int, default=None)
    parser.add_argument("--cpu", action="store_true")
    return parser.parse_args()


def safe_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [safe_json(v) for v in obj]
    if isinstance(obj, tuple):
        return [safe_json(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        return None if math.isnan(v) else v
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def make_subject_folds(subjects: list[int], n_folds: int, seed: int) -> list[Fold]:
    rng = np.random.default_rng(seed)
    shuffled = np.asarray(sorted(subjects), dtype=np.int64)
    rng.shuffle(shuffled)
    splits = np.array_split(shuffled, n_folds)
    return [Fold(fold_id=i + 1, val_subjects=[int(x) for x in split.tolist()]) for i, split in enumerate(splits)]


def finite_summary(values: list[float]) -> dict[str, float | None]:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"mean": None, "std": None, "min": None, "max": None}
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=0)),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def confusion_binary(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, int]:
    y_true = y_true.astype(np.int64)
    y_pred = y_pred.astype(np.int64)
    return {
        "tn": int(((y_true == 0) & (y_pred == 0)).sum()),
        "fp": int(((y_true == 0) & (y_pred == 1)).sum()),
        "fn": int(((y_true == 1) & (y_pred == 0)).sum()),
        "tp": int(((y_true == 1) & (y_pred == 1)).sum()),
    }


def metrics_from_predictions(y_true: np.ndarray, y_pred: np.ndarray, loss_mean: float | None = None, batches: int | None = None) -> dict[str, Any]:
    y_true = y_true.astype(np.int64)
    y_pred = y_pred.astype(np.int64)
    n = int(y_true.size)
    conf = confusion_binary(y_true, y_pred)
    per_class: dict[str, Any] = {}
    recalls: list[float] = []
    f1s: list[float] = []
    for cls in [0, 1]:
        tp = int(((y_true == cls) & (y_pred == cls)).sum())
        fp = int(((y_true != cls) & (y_pred == cls)).sum())
        fn = int(((y_true == cls) & (y_pred != cls)).sum())
        support = int((y_true == cls).sum())
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        recalls.append(recall)
        f1s.append(f1)
        per_class[str(cls)] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "support": support,
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
        }
    pred_counts = {str(k): int((y_pred == k).sum()) for k in [0, 1]}
    true_counts = {str(k): int((y_true == k).sum()) for k in [0, 1]}
    pred_unique = sorted(set(int(x) for x in y_pred.tolist()))
    majority_label = 1 if true_counts["1"] >= true_counts["0"] else 0
    majority_pred = np.full_like(y_true, majority_label)
    majority_conf = confusion_binary(y_true, majority_pred)
    majority_acc = float((majority_pred == y_true).mean()) if n else 0.0
    maj_recalls = []
    maj_f1s = []
    for cls in [0, 1]:
        tp = int(((y_true == cls) & (majority_pred == cls)).sum())
        fp = int(((y_true != cls) & (majority_pred == cls)).sum())
        fn = int(((y_true == cls) & (majority_pred != cls)).sum())
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        maj_recalls.append(recall)
        maj_f1s.append(f1)
    out = {
        "n": n,
        "accuracy": float((y_true == y_pred).mean()) if n else 0.0,
        "balanced_accuracy": float(np.mean(recalls)),
        "macro_f1": float(np.mean(f1s)),
        "confusion": conf,
        "per_class": per_class,
        "pred_counts": pred_counts,
        "true_counts": true_counts,
        "pred_unique_labels": pred_unique,
        "one_class_pred": len(pred_unique) == 1,
        "collapsed_to_label": int(pred_unique[0]) if len(pred_unique) == 1 else None,
        "majority_baseline": {
            "label": int(majority_label),
            "accuracy": majority_acc,
            "balanced_accuracy": float(np.mean(maj_recalls)),
            "macro_f1": float(np.mean(maj_f1s)),
            "confusion": majority_conf,
        },
    }
    if loss_mean is not None:
        out["loss_mean"] = float(loss_mean)
    if batches is not None:
        out["batches"] = int(batches)
    return out


def threshold_sweep(y_true: np.ndarray, p1: np.ndarray) -> dict[str, Any]:
    thresholds = [round(x, 4) for x in np.arange(0.05, 0.951, 0.05)]
    records = []
    best = None
    for threshold in thresholds:
        pred = (p1 >= threshold).astype(np.int64)
        m = metrics_from_predictions(y_true, pred)
        row = {
            "threshold": float(threshold),
            "macro_f1": m["macro_f1"],
            "balanced_accuracy": m["balanced_accuracy"],
            "accuracy": m["accuracy"],
            "pred_counts": m["pred_counts"],
            "one_class_pred": m["one_class_pred"],
            "confusion": m["confusion"],
        }
        records.append(row)
        if best is None or (row["macro_f1"], row["balanced_accuracy"], row["accuracy"]) > (best["macro_f1"], best["balanced_accuracy"], best["accuracy"]):
            best = row
    assert best is not None
    return {"best": best, "records": records}


def probability_summary(p1: np.ndarray) -> dict[str, float]:
    p1 = np.asarray(p1, dtype=np.float64)
    return {
        "mean": float(p1.mean()),
        "median": float(np.median(p1)),
        "q05": float(np.quantile(p1, 0.05)),
        "q25": float(np.quantile(p1, 0.25)),
        "q75": float(np.quantile(p1, 0.75)),
        "q95": float(np.quantile(p1, 0.95)),
        "min": float(p1.min()),
        "max": float(p1.max()),
    }


def class_weights(labels: np.ndarray, device: torch.device) -> torch.Tensor:
    counts = np.bincount(labels.astype(np.int64), minlength=2).astype(np.float64)
    total = counts.sum()
    weights = total / (2.0 * np.maximum(counts, 1.0))
    return torch.tensor(weights, dtype=torch.float32, device=device)


def make_loader(dataset: RawEMGDataset, labels: np.ndarray, recipe: str, batch_size: int, num_workers: int, is_train: bool) -> DataLoader:
    if is_train and recipe == "balanced_sampler_ce":
        counts = np.bincount(labels.astype(np.int64), minlength=2).astype(np.float64)
        sample_weights = np.asarray([1.0 / max(counts[int(y)], 1.0) for y in labels], dtype=np.float64)
        sampler = WeightedRandomSampler(weights=torch.DoubleTensor(sample_weights), num_samples=len(sample_weights), replacement=True)
        return DataLoader(dataset, batch_size=batch_size, sampler=sampler, num_workers=num_workers, pin_memory=torch.cuda.is_available())
    return DataLoader(dataset, batch_size=batch_size, shuffle=is_train, num_workers=num_workers, pin_memory=torch.cuda.is_available())


def evaluate(model: nn.Module, loader: DataLoader, criterion: nn.Module, device: torch.device) -> dict[str, Any]:
    model.eval()
    losses = []
    y_true_parts = []
    y_pred_parts = []
    p1_parts = []
    row_parts = []
    with torch.no_grad():
        for x, y, row_ids in loader:
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            logits = model(x)
            loss = criterion(logits, y)
            probs = torch.softmax(logits, dim=1)
            pred = torch.argmax(probs, dim=1)
            losses.append(float(loss.detach().cpu().item()))
            y_true_parts.append(y.detach().cpu().numpy())
            y_pred_parts.append(pred.detach().cpu().numpy())
            p1_parts.append(probs[:, 1].detach().cpu().numpy())
            row_parts.append(row_ids.detach().cpu().numpy())
    y_true = np.concatenate(y_true_parts) if y_true_parts else np.asarray([], dtype=np.int64)
    y_pred = np.concatenate(y_pred_parts) if y_pred_parts else np.asarray([], dtype=np.int64)
    p1 = np.concatenate(p1_parts) if p1_parts else np.asarray([], dtype=np.float32)
    rows = np.concatenate(row_parts) if row_parts else np.asarray([], dtype=np.int64)
    out = metrics_from_predictions(y_true, y_pred, loss_mean=float(np.mean(losses)) if losses else None, batches=len(losses))
    out["probability"] = probability_summary(p1) if len(p1) else {}
    out["threshold_sweep"] = threshold_sweep(y_true, p1) if len(p1) else {"best": None, "records": []}
    out["rows"] = rows.astype(int).tolist()
    out["y_true"] = y_true.astype(int).tolist()
    out["y_pred"] = y_pred.astype(int).tolist()
    out["p1"] = [float(x) for x in p1.tolist()]
    return out


def train_one_run(
    *,
    raw: np.ndarray,
    index_df: pd.DataFrame,
    task: str,
    label_policy: str,
    recipe: str,
    fold: Fold,
    seed: int,
    epochs: int,
    lr: float,
    weight_decay: float,
    batch_size: int,
    num_workers: int,
    grad_clip: float,
    device: torch.device,
    run_id: int,
) -> dict[str, Any]:
    set_seed(seed)
    label_col = f"{task}_{label_policy}"
    if label_col not in index_df.columns:
        raise KeyError(f"Missing label column: {label_col}")

    eligible = index_df[label_col].notna().to_numpy()
    subject_ids = index_df["subject_id"].astype(int).to_numpy()
    val_mask = np.isin(subject_ids, np.asarray(fold.val_subjects, dtype=np.int64)) & eligible
    train_mask = (~np.isin(subject_ids, np.asarray(fold.val_subjects, dtype=np.int64))) & eligible

    train_rows = np.where(train_mask)[0]
    val_rows = np.where(val_mask)[0]
    train_labels = index_df.iloc[train_rows][label_col].astype(int).to_numpy()
    val_labels = index_df.iloc[val_rows][label_col].astype(int).to_numpy()

    train_ds = RawEMGDataset(raw, train_rows, train_labels)
    val_ds = RawEMGDataset(raw, val_rows, val_labels)

    train_loader = make_loader(train_ds, train_labels, recipe, batch_size, num_workers, is_train=True)
    eval_train_loader = make_loader(train_ds, train_labels, "ce_class_weighted", batch_size, num_workers, is_train=False)
    val_loader = make_loader(val_ds, val_labels, "ce_class_weighted", batch_size, num_workers, is_train=False)

    model = TinyRawEMGCNN().to(device)
    weights = class_weights(train_labels, device)
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    epoch_records: list[dict[str, Any]] = []
    best = None
    t0 = time.perf_counter()
    for epoch in range(1, epochs + 1):
        model.train()
        train_losses = []
        for x, y, _row_ids in train_loader:
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            if grad_clip and grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()
            train_losses.append(float(loss.detach().cpu().item()))
        val_eval = evaluate(model, val_loader, criterion, device)
        rec = {
            "epoch": epoch,
            "train_loss_mean": float(np.mean(train_losses)) if train_losses else None,
            "val": {k: v for k, v in val_eval.items() if k not in {"rows", "y_true", "y_pred", "p1"}},
        }
        epoch_records.append(rec)
        if best is None or (val_eval["macro_f1"], val_eval["balanced_accuracy"], val_eval["accuracy"]) > (best["macro_f1"], best["balanced_accuracy"], best["accuracy"]):
            best = {k: v for k, v in val_eval.items() if k not in {"rows", "y_true", "y_pred", "p1"}}
            best["epoch"] = epoch

    final = evaluate(model, val_loader, criterion, device)
    train_final = evaluate(model, eval_train_loader, criterion, device)
    duration = float(time.perf_counter() - t0)

    return {
        "run_id": int(run_id),
        "task": task,
        "policy": label_policy,
        "recipe": recipe,
        "fold_id": int(fold.fold_id),
        "seed": int(seed),
        "val_subjects": fold.val_subjects,
        "train_n": int(len(train_rows)),
        "val_n": int(len(val_rows)),
        "train_label_counts": {str(k): int(v) for k, v in Counter(train_labels.tolist()).items()},
        "val_label_counts": {str(k): int(v) for k, v in Counter(val_labels.tolist()).items()},
        "class_weights": [float(x) for x in weights.detach().cpu().numpy().tolist()],
        "batch_size": int(batch_size),
        "epochs": int(epochs),
        "duration_sec": duration,
        "epoch_records": epoch_records,
        "best": best,
        "final": {k: v for k, v in final.items() if k not in {"rows", "y_true", "y_pred", "p1"}},
        "train_final": {k: v for k, v in train_final.items() if k not in {"rows", "y_true", "y_pred", "p1"}},
        "prediction_rows": final["rows"],
        "prediction_y_true": final["y_true"],
        "prediction_y_pred": final["y_pred"],
        "prediction_p1": final["p1"],
    }


def aggregate_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[(run["task"], run["policy"], run["recipe"])].append(run)
    rows = []
    for (task, policy, recipe), group in sorted(grouped.items()):
        final_macro = [float(r["final"]["macro_f1"]) for r in group]
        final_bal = [float(r["final"]["balanced_accuracy"]) for r in group]
        final_acc = [float(r["final"]["accuracy"]) for r in group]
        best_macro = [float(r["best"]["macro_f1"]) for r in group]
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
            "best_macro_f1": finite_summary(best_macro),
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
        "run_id", "task", "policy", "recipe", "fold_id", "seed", "cache_row", "subject_id", "stimulus_id", "y_true", "y_pred", "p1",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator='\n')
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
    lines.append("# I-DARE Raw EMG-Only Training Smoke\n")
    lines.append("This report was generated by `scripts/32_run_idare_raw_emg_smoke.py`.\n")
    lines.append("No raw I-DARE EMG HDF5/MAT files were loaded inside training loops.\n")
    lines.append("## Inputs\n")
    lines.append(f"- raw_npy: `{cfg['raw_npy']}`")
    lines.append(f"- raw_index: `{cfg['raw_index']}`\n")
    lines.append("## Run Scope\n")
    lines.append(f"- label_policy: `{cfg['label_policy']}`")
    lines.append(f"- tasks: `{', '.join(cfg['tasks'])}`")
    lines.append(f"- recipes: `{', '.join(cfg['recipes'])}`")
    lines.append(f"- epochs: `{cfg['epochs']}`")
    lines.append(f"- max_runs: `{cfg['max_runs']}`")
    lines.append(f"- device: `{cfg['device']}`")
    lines.append("- model: `TinyRawEMGCNN(input_shape=[2,10000])`\n")
    lines.append("## Aggregate\n")
    lines.append("| Task | Policy | Recipe | Runs | Final macro F1 | Final bal acc | Final acc | Threshold macro F1 | Threshold bal acc | One-class final runs | Majority acc |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in report["aggregate"]:
        lines.append(
            "| {task} | {policy} | {recipe} | {runs} | {mf:.4f} | {ba:.4f} | {acc:.4f} | {tmf:.4f} | {tba:.4f} | {one} | {maj:.4f} |".format(
                task=row["task"], policy=row["policy"], recipe=row["recipe"], runs=row["runs"],
                mf=row["final_macro_f1"]["mean"], ba=row["final_balanced_accuracy"]["mean"], acc=row["final_accuracy"]["mean"],
                tmf=row["threshold_best_macro_f1"]["mean"], tba=row["threshold_best_balanced_accuracy"]["mean"],
                one=row["one_class_final_runs"], maj=row["majority_accuracy"]["mean"],
            )
        )
    lines.append("")
    lines.append("## Aggregate Threshold Diagnostics\n")
    lines.append("| Task | Policy | Recipe | Runs | Mean threshold | Macro F1 gain | Bal acc gain | Threshold one-class runs |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|")
    for row in report["aggregate"]:
        lines.append(
            "| {task} | {policy} | {recipe} | {runs} | {thr:.4f} | {mg:.4f} | {bg:.4f} | {one} |".format(
                task=row["task"], policy=row["policy"], recipe=row["recipe"], runs=row["runs"],
                thr=row["threshold_best_value"]["mean"], mg=row["threshold_gain_macro_f1"]["mean"],
                bg=row["threshold_gain_balanced_accuracy"]["mean"], one=row["threshold_one_class_final_runs"],
            )
        )
    lines.append("")
    lines.append("## Per-run Final Diagnostics\n")
    lines.append("| Run | Task | Recipe | Fold | Seed | Train n | Val n | Macro F1 | Bal acc | Acc | Pred 0 | Pred 1 | TN | FP | FN | TP | One-class | Majority acc |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|")
    for run in report["runs"]:
        f = run["final"]
        c = f["confusion"]
        lines.append(
            "| {run_id} | {task} | {recipe} | {fold} | {seed} | {train_n} | {val_n} | {mf:.4f} | {ba:.4f} | {acc:.4f} | {p0} | {p1} | {tn} | {fp} | {fn} | {tp} | {one} | {maj:.4f} |".format(
                run_id=run["run_id"], task=run["task"], recipe=run["recipe"], fold=run["fold_id"], seed=run["seed"],
                train_n=run["train_n"], val_n=run["val_n"], mf=f["macro_f1"], ba=f["balanced_accuracy"], acc=f["accuracy"],
                p0=f["pred_counts"].get("0", 0), p1=f["pred_counts"].get("1", 0), tn=c["tn"], fp=c["fp"], fn=c["fn"], tp=c["tp"],
                one=str(f["one_class_pred"]).lower(), maj=f["majority_baseline"]["accuracy"],
            )
        )
    lines.append("")
    lines.append("## Train vs Validation Probability Diagnostics\n")
    lines.append("| Run | Task | Recipe | Fold | Train P1 mean | Val P1 mean | Mean shift | Train pred 0 | Train pred 1 | Val pred 0 | Val pred 1 |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for run in report["runs"]:
        tr = run["train_final"]
        va = run["final"]
        train_mean = tr["probability"]["mean"]
        val_mean = va["probability"]["mean"]
        lines.append(
            "| {run_id} | {task} | {recipe} | {fold} | {trm:.4f} | {vam:.4f} | {shift:.4f} | {tr0} | {tr1} | {va0} | {va1} |".format(
                run_id=run["run_id"], task=run["task"], recipe=run["recipe"], fold=run["fold_id"],
                trm=train_mean, vam=val_mean, shift=val_mean - train_mean,
                tr0=tr["pred_counts"].get("0", 0), tr1=tr["pred_counts"].get("1", 0),
                va0=va["pred_counts"].get("0", 0), va1=va["pred_counts"].get("1", 0),
            )
        )
    lines.append("")
    lines.append("## Probability / Threshold Diagnostics\n")
    lines.append("| Run | Task | Recipe | P1 mean | P1 q05 | P1 median | P1 q95 | Best threshold | Best threshold macro F1 | Best threshold bal acc | Best threshold pred 0 | Best threshold pred 1 |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for run in report["runs"]:
        f = run["final"]
        prob = f["probability"]
        best = f["threshold_sweep"]["best"]
        lines.append(
            "| {run_id} | {task} | {recipe} | {mean:.4f} | {q05:.4f} | {med:.4f} | {q95:.4f} | {thr:.4f} | {mf:.4f} | {ba:.4f} | {p0} | {p1} |".format(
                run_id=run["run_id"], task=run["task"], recipe=run["recipe"], mean=prob["mean"], q05=prob["q05"],
                med=prob["median"], q95=prob["q95"], thr=best["threshold"], mf=best["macro_f1"], ba=best["balanced_accuracy"],
                p0=best["pred_counts"].get("0", 0), p1=best["pred_counts"].get("1", 0),
            )
        )
    lines.append("")
    lines.append("## Notes\n")
    lines.append("- This is a smoke/stabilization report, not a final LOSO result.")
    lines.append("- The raw EMG cache was already baseline-corrected and per-window globally z-scored before training.")
    lines.append("- Primary diagnostics are macro F1, balanced accuracy, one-class collapse, threshold behavior, and majority baseline.")
    lines.append("- This is the raw I-DARE EMG-only ablation path, intended to be compared against the feature-level EMG-only path.\n")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_predictions_csv.parent.mkdir(parents=True, exist_ok=True)

    device = torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")
    raw = np.load(args.raw_npy, mmap_mode="r")
    index_df = pd.read_csv(args.raw_index)

    print("[INFO] I-DARE raw EMG-only training smoke")
    print(f"[INFO] raw_npy={args.raw_npy}")
    print(f"[INFO] raw_index={args.raw_index}")
    print(f"[INFO] raw_shape={list(raw.shape)}")
    print(f"[INFO] label_policy={args.label_policy}")
    print(f"[INFO] tasks={args.tasks}")
    print(f"[INFO] recipes={args.recipes}")
    print(f"[INFO] epochs={args.epochs}")
    print(f"[INFO] max_runs={args.max_runs}")
    print(f"[INFO] device={device}")

    subjects = sorted(index_df["subject_id"].dropna().astype(int).unique().tolist())
    folds = make_subject_folds(subjects, args.folds, args.seeds[0])

    planned = []
    for task in args.tasks:
        for fold in folds:
            for seed in args.seeds:
                for recipe in args.recipes:
                    planned.append((task, fold, seed, recipe))
    if args.max_runs is not None:
        planned = planned[: args.max_runs]
    print(f"[INFO] planned_runs={len(planned)}")

    runs: list[dict[str, Any]] = []
    for i, (task, fold, seed, recipe) in enumerate(planned, start=1):
        print(f"[RUN] {i}/{len(planned)} task={task} policy={args.label_policy} recipe={recipe} fold={fold.fold_id} seed={seed} val_subjects={fold.val_subjects}")
        run = train_one_run(
            raw=raw,
            index_df=index_df,
            task=task,
            label_policy=args.label_policy,
            recipe=recipe,
            fold=fold,
            seed=seed,
            epochs=args.epochs,
            lr=args.lr,
            weight_decay=args.weight_decay,
            batch_size=args.batch_size,
            num_workers=args.num_workers,
            grad_clip=args.grad_clip,
            device=device,
            run_id=i,
        )
        runs.append(run)
        f = run["final"]
        print(json.dumps({
            "run_id": run["run_id"],
            "task": task,
            "recipe": recipe,
            "final_macro_f1": f["macro_f1"],
            "final_balanced_accuracy": f["balanced_accuracy"],
            "final_accuracy": f["accuracy"],
            "majority_accuracy": f["majority_baseline"]["accuracy"],
            "one_class_pred": f["one_class_pred"],
            "pred_counts": f["pred_counts"],
            "confusion": f["confusion"],
        }, sort_keys=True))

    aggregate = aggregate_runs(runs)
    report = {
        "generated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "config": {
            "raw_npy": str(args.raw_npy),
            "raw_index": str(args.raw_index),
            "raw_shape": list(raw.shape),
            "label_policy": args.label_policy,
            "tasks": args.tasks,
            "recipes": args.recipes,
            "folds": args.folds,
            "seeds": args.seeds,
            "epochs": args.epochs,
            "lr": args.lr,
            "weight_decay": args.weight_decay,
            "batch_size": args.batch_size,
            "num_workers": args.num_workers,
            "grad_clip": args.grad_clip,
            "max_runs": args.max_runs,
            "device": str(device),
            "model": "TinyRawEMGCNN(input_shape=[2,10000])",
        },
        "aggregate": aggregate,
        "runs": runs,
    }

    write_predictions_csv(args.out_predictions_csv, runs, index_df)
    args.out_json.write_text(json.dumps(safe_json(report), indent=2, ensure_ascii=False), encoding="utf-8")
    args.out_md.write_text(build_report_md(safe_json(report)), encoding="utf-8")

    print(f"[DONE] wrote {args.out_predictions_csv}")
    print(f"[DONE] wrote {args.out_md}")
    print(f"[DONE] wrote {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
