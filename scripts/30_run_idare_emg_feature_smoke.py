#!/usr/bin/env python3
"""Run DEAP EMG-feature-only training smokes.

Cache-only smoke script:
- reads .cache/deap_emg_features.npy
- reads .cache/deap_emg_feature_cache_index.csv
- uses subject-wise folds
- fits feature standardization on train rows only
- trains a tiny MLP
- reports macro F1, balanced accuracy, threshold diagnostics, and one-class collapse

No raw DEAP .dat files are loaded inside training loops.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_FEATURE_NPY = ROOT / ".cache" / "deap_emg_features.npy"
DEFAULT_FEATURE_INDEX = ROOT / ".cache" / "deap_emg_feature_cache_index.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "deap_emg_feature_training_smoke.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "deap_emg_feature_training_smoke.json"

VALID_TASKS = {"valence", "arousal", "dominance", "liking"}
VALID_POLICIES = {"discard_midpoint", "midpoint_as_low", "midpoint_as_high"}
VALID_RECIPES = {"ce_class_weighted", "ce_no_class_weight", "balanced_sampler_ce"}


@dataclass(frozen=True)
class Fold:
    fold_id: int
    val_subjects: list[int]
    train_subjects: list[int]


@dataclass(frozen=True)
class RunSpec:
    run_id: int
    task: str
    policy: str
    recipe: str
    fold: Fold
    seed: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-npy", type=Path, default=DEFAULT_FEATURE_NPY)
    parser.add_argument("--feature-index", type=Path, default=DEFAULT_FEATURE_INDEX)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-predictions-csv", type=Path, default=None)
    parser.add_argument("--tasks", nargs="+", default=["valence", "arousal"], choices=sorted(VALID_TASKS))
    parser.add_argument("--label-policy", default="midpoint_as_high", choices=sorted(VALID_POLICIES))
    parser.add_argument("--recipes", nargs="+", default=["ce_class_weighted", "balanced_sampler_ce"], choices=sorted(VALID_RECIPES))
    parser.add_argument("--folds", type=int, default=6)
    parser.add_argument("--seeds", nargs="+", type=int, default=[11])
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--dropout", type=float, default=0.20)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--max-runs", type=int, default=4, help="0 means run all planned specs.")
    parser.add_argument("--cpu", action="store_true")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def safe_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def label_column(task: str, policy: str) -> str:
    return f"{task}_{policy}"


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def count_ints(values: list[int]) -> dict[str, int]:
    return {
        "0": int(sum(1 for v in values if int(v) == 0)),
        "1": int(sum(1 for v in values if int(v) == 1)),
    }


def binary_metrics_no_majority(y_true: list[int], y_pred: list[int]) -> dict[str, float]:
    f1s: list[float] = []
    recalls: list[float] = []
    for label in [0, 1]:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2.0 * precision * recall, precision + recall)
        f1s.append(f1)
        recalls.append(recall)
    correct = sum(int(t == p) for t, p in zip(y_true, y_pred))
    return {
        "accuracy": safe_div(correct, len(y_true)),
        "balanced_accuracy": float(sum(recalls) / len(recalls)),
        "macro_f1": float(sum(f1s) / len(f1s)),
    }


def binary_metrics(y_true: list[int], y_pred: list[int]) -> dict[str, Any]:
    confusion = {
        "tn": int(sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)),
        "fp": int(sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)),
        "fn": int(sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)),
        "tp": int(sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)),
    }

    f1s: list[float] = []
    recalls: list[float] = []
    per_class: dict[str, Any] = {}
    for label in [0, 1]:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2.0 * precision * recall, precision + recall)
        f1s.append(f1)
        recalls.append(recall)
        per_class[str(label)] = {
            "tp": int(tp),
            "fp": int(fp),
            "fn": int(fn),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": int(sum(1 for t in y_true if t == label)),
        }

    true_counts = count_ints(y_true)
    pred_counts = count_ints(y_pred)
    majority_label = max([0, 1], key=lambda label: true_counts[str(label)])
    majority_pred = [majority_label for _ in y_true]
    pred_unique = sorted({int(p) for p in y_pred})
    correct = sum(int(t == p) for t, p in zip(y_true, y_pred))

    return {
        "n": int(len(y_true)),
        "accuracy": safe_div(correct, len(y_true)),
        "balanced_accuracy": float(sum(recalls) / len(recalls)),
        "macro_f1": float(sum(f1s) / len(f1s)),
        "true_counts": true_counts,
        "pred_counts": pred_counts,
        "confusion": confusion,
        "per_class": per_class,
        "one_class_pred": bool(len(pred_unique) == 1),
        "pred_unique_labels": pred_unique,
        "collapsed_to_label": int(pred_unique[0]) if len(pred_unique) == 1 else None,
        "majority_baseline": {
            "label": int(majority_label),
            **binary_metrics_no_majority(y_true, majority_pred),
        },
    }


def summarize(values: list[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return {"mean": math.nan, "std": math.nan, "min": math.nan, "max": math.nan}
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=0)),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def quantile_summary(values: list[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return {k: math.nan for k in ["mean", "std", "min", "q05", "q25", "median", "q75", "q95", "max"]}
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=0)),
        "min": float(arr.min()),
        "q05": float(np.quantile(arr, 0.05)),
        "q25": float(np.quantile(arr, 0.25)),
        "median": float(np.quantile(arr, 0.50)),
        "q75": float(np.quantile(arr, 0.75)),
        "q95": float(np.quantile(arr, 0.95)),
        "max": float(arr.max()),
    }


def threshold_sweep(y_true: list[int], prob1: list[float]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    for threshold in [round(float(x), 2) for x in np.arange(0.05, 0.951, 0.05)]:
        y_pred = [1 if p >= threshold else 0 for p in prob1]
        metrics = binary_metrics(y_true, y_pred)
        record = {
            "threshold": threshold,
            "accuracy": metrics["accuracy"],
            "balanced_accuracy": metrics["balanced_accuracy"],
            "macro_f1": metrics["macro_f1"],
            "pred_counts": metrics["pred_counts"],
            "one_class_pred": metrics["one_class_pred"],
            "confusion": metrics["confusion"],
        }
        records.append(record)
        if best is None:
            best = record
        else:
            key = (record["macro_f1"], record["balanced_accuracy"], -abs(threshold - 0.5))
            best_key = (best["macro_f1"], best["balanced_accuracy"], -abs(best["threshold"] - 0.5))
            if key > best_key:
                best = record
    assert best is not None
    return {"best": best, "records": records}


def make_subject_folds(subjects: list[int], n_folds: int, seed: int) -> list[Fold]:
    """Build sidecar-compatible numpy.default_rng subject folds.

    This keeps I-DARE EMG feature-only broader-eval folds aligned with
    scripts/36_run_idare_emg_bsl_stats_ablation_smoke.py.
    """
    subjects = sorted({int(s) for s in subjects})
    if n_folds < 2:
        raise ValueError("--folds must be >= 2")
    if n_folds > len(subjects):
        raise ValueError(f"--folds={n_folds} exceeds subject count={len(subjects)}")
    rng = np.random.default_rng(int(seed))
    shuffled = np.asarray(subjects, dtype=int)
    rng.shuffle(shuffled)
    chunks = [list(chunk) for chunk in np.array_split(shuffled, n_folds)]
    all_subjects = set(subjects)
    folds: list[Fold] = []
    for i, chunk in enumerate(chunks, start=1):
        val_subjects = sorted(int(x) for x in chunk)
        train_subjects = sorted(all_subjects - set(val_subjects))
        folds.append(Fold(fold_id=i, val_subjects=val_subjects, train_subjects=train_subjects))
    return folds

class DEAPEMGFeatureDataset(Dataset):
    def __init__(
        self,
        *,
        feature_npy: Path,
        feature_index: Path,
        task: str,
        policy: str,
        subjects: list[int],
        mean: np.ndarray | None = None,
        std: np.ndarray | None = None,
    ) -> None:
        if not feature_npy.exists():
            raise FileNotFoundError(f"Missing feature cache: {feature_npy}")
        if not feature_index.exists():
            raise FileNotFoundError(f"Missing feature cache index: {feature_index}")

        col = label_column(task, policy)
        df = pd.read_csv(feature_index)
        missing = sorted({"cache_row", "subject_id", col} - set(df.columns))
        if missing:
            raise KeyError(f"Missing required cache-index columns: {missing}")

        df = df[df["subject_id"].astype(int).isin([int(s) for s in subjects])].copy()
        df[col] = df[col].map(safe_float)
        df = df[df[col].isin([0.0, 1.0])].copy()
        df["label"] = df[col].astype(int)
        df["cache_row"] = df["cache_row"].astype(int)
        df["subject_id"] = df["subject_id"].astype(int)
        sort_cols = [c for c in ["subject_id", "trial_id", "window_id", "cache_row"] if c in df.columns]
        df = df.sort_values(sort_cols).reset_index(drop=True)

        if len(df) == 0:
            raise ValueError(f"No rows for task={task}, policy={policy}, subjects={subjects}")

        cache = np.load(feature_npy, mmap_mode="r")
        if cache.ndim != 2:
            raise ValueError(f"Unexpected feature cache shape: {cache.shape}; expected [N, F]")
        if int(df["cache_row"].max()) >= int(cache.shape[0]):
            raise ValueError("cache_row exceeds cache first dimension")

        if mean is None or std is None:
            rows = df["cache_row"].to_numpy(dtype=int)
            x = np.asarray(cache[rows], dtype=np.float32)
            mean = x.mean(axis=0).astype(np.float32)
            std = x.std(axis=0).astype(np.float32)
            std = np.where(std < 1e-6, 1.0, std).astype(np.float32)

        self.df = df
        self.cache = cache
        self.mean = np.asarray(mean, dtype=np.float32)
        self.std = np.asarray(std, dtype=np.float32)
        self.feature_dim = int(cache.shape[1])

    def __len__(self) -> int:
        return int(len(self.df))

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.df.iloc[index]
        cache_row = int(row["cache_row"])
        x = np.asarray(self.cache[cache_row], dtype=np.float32)
        x = (x - self.mean) / self.std
        return {
            "features": torch.from_numpy(x.astype(np.float32, copy=False)),
            "label": torch.tensor(int(row["label"]), dtype=torch.long),
            "cache_row": cache_row,
            "subject_id": int(row["subject_id"]),
            "trial_id": int(row["trial_id"]) if "trial_id" in row.index and not pd.isna(row["trial_id"]) else -1,
            "window_id": int(row["window_id"]) if "window_id" in row.index and not pd.isna(row["window_id"]) else -1,
        }


class TinyEMGMLP(nn.Module):
    def __init__(self, feature_dim: int, hidden_dim: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(feature_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 2),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def class_weights_from_labels(labels: list[int], device: torch.device) -> torch.Tensor:
    counts = {0: int(sum(1 for y in labels if y == 0)), 1: int(sum(1 for y in labels if y == 1))}
    total = sum(counts.values())
    return torch.tensor([total / (2.0 * max(counts[label], 1)) for label in [0, 1]], dtype=torch.float32, device=device)


def sampler_from_labels(labels: list[int]) -> WeightedRandomSampler:
    counts = {0: int(sum(1 for y in labels if y == 0)), 1: int(sum(1 for y in labels if y == 1))}
    sample_weights = [1.0 / max(counts[int(y)], 1) for y in labels]
    return WeightedRandomSampler(
        weights=torch.tensor(sample_weights, dtype=torch.double),
        num_samples=len(sample_weights),
        replacement=True,
    )


def collate_batch(batch: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "features": torch.stack([x["features"] for x in batch], dim=0),
        "label": torch.stack([x["label"] for x in batch], dim=0),
        "cache_row": [int(x["cache_row"]) for x in batch],
        "subject_id": [int(x["subject_id"]) for x in batch],
        "trial_id": [int(x["trial_id"]) for x in batch],
        "window_id": [int(x["window_id"]) for x in batch],
    }


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, device: torch.device, criterion: nn.Module) -> dict[str, Any]:
    model.eval()
    losses: list[float] = []
    y_true: list[int] = []
    y_pred: list[int] = []
    prob1: list[float] = []
    cache_rows: list[int] = []
    subject_ids: list[int] = []
    trial_ids: list[int] = []
    window_ids: list[int] = []

    for batch in loader:
        x = batch["features"].to(device=device, dtype=torch.float32)
        y = batch["label"].to(device=device)
        logits = model(x)
        loss = criterion(logits, y)
        probs = torch.softmax(logits, dim=1)
        pred = torch.argmax(probs, dim=1)

        losses.append(float(loss.detach().cpu().item()))
        y_true.extend(int(v) for v in y.detach().cpu().numpy().tolist())
        y_pred.extend(int(v) for v in pred.detach().cpu().numpy().tolist())
        prob1.extend(float(v) for v in probs[:, 1].detach().cpu().numpy().tolist())
        cache_rows.extend(int(v) for v in batch["cache_row"])
        subject_ids.extend(int(v) for v in batch["subject_id"])
        trial_ids.extend(int(v) for v in batch["trial_id"])
        window_ids.extend(int(v) for v in batch["window_id"])

    metrics = binary_metrics(y_true, y_pred)
    metrics.update(
        {
            "loss_mean": float(np.mean(losses)) if losses else math.nan,
            "batches": int(len(losses)),
            "prob1_summary": quantile_summary(prob1),
            "margin_summary": quantile_summary([2.0 * p - 1.0 for p in prob1]),
            "threshold_sweep": threshold_sweep(y_true, prob1),
            "prob1": prob1,
            "y_true": y_true,
            "y_pred": y_pred,
            "cache_row": cache_rows,
            "subject_id": subject_ids,
            "trial_id": trial_ids,
            "window_id": window_ids,
        }
    )
    return metrics


def compact_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    drop = {"prob1", "y_true", "y_pred", "cache_row", "subject_id", "trial_id", "window_id"}
    return {k: v for k, v in metrics.items() if k not in drop}


def prediction_rows(spec: RunSpec, final_full: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for i, y_true in enumerate(final_full["y_true"]):
        rows.append(
            {
                "run_id": spec.run_id,
                "task": spec.task,
                "policy": spec.policy,
                "recipe": spec.recipe,
                "fold_id": spec.fold.fold_id,
                "seed": spec.seed,
                "cache_row": int(final_full["cache_row"][i]),
                "subject_id": int(final_full["subject_id"][i]),
                "trial_id": int(final_full["trial_id"][i]),
                "window_id": int(final_full["window_id"][i]),
                "y_true": int(y_true),
                "y_pred": int(final_full["y_pred"][i]),
                "prob1": float(final_full["prob1"][i]),
            }
        )
    return rows


def train_one_run(args: argparse.Namespace, spec: RunSpec, device: torch.device) -> dict[str, Any]:
    set_seed(spec.seed)

    train_ds = DEAPEMGFeatureDataset(
        feature_npy=args.feature_npy,
        feature_index=args.feature_index,
        task=spec.task,
        policy=spec.policy,
        subjects=spec.fold.train_subjects,
    )
    val_ds = DEAPEMGFeatureDataset(
        feature_npy=args.feature_npy,
        feature_index=args.feature_index,
        task=spec.task,
        policy=spec.policy,
        subjects=spec.fold.val_subjects,
        mean=train_ds.mean,
        std=train_ds.std,
    )

    train_labels = train_ds.df["label"].astype(int).tolist()
    val_labels = val_ds.df["label"].astype(int).tolist()

    if spec.recipe == "balanced_sampler_ce":
        sampler = sampler_from_labels(train_labels)
        shuffle = False
    else:
        sampler = None
        shuffle = True

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        sampler=sampler,
        shuffle=shuffle if sampler is None else False,
        num_workers=args.num_workers,
        collate_fn=collate_batch,
        drop_last=False,
    )
    train_eval_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, collate_fn=collate_batch)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers, collate_fn=collate_batch)

    model = TinyEMGMLP(feature_dim=train_ds.feature_dim, hidden_dim=args.hidden_dim, dropout=args.dropout).to(device)
    if spec.recipe == "ce_class_weighted":
        criterion = nn.CrossEntropyLoss(weight=class_weights_from_labels(train_labels, device))
    else:
        criterion = nn.CrossEntropyLoss()

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    epoch_records: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    start = time.perf_counter()

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_losses: list[float] = []
        for batch in train_loader:
            x = batch["features"].to(device=device, dtype=torch.float32)
            y = batch["label"].to(device=device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            if args.grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            optimizer.step()
            train_losses.append(float(loss.detach().cpu().item()))

        val_metrics = evaluate(model, val_loader, device, criterion)
        epoch_record = {
            "epoch": epoch,
            "train_loss_mean": float(np.mean(train_losses)) if train_losses else math.nan,
            "val": compact_metrics(val_metrics),
        }
        epoch_records.append(epoch_record)
        if best is None or (
            val_metrics["macro_f1"],
            val_metrics["balanced_accuracy"],
            val_metrics["accuracy"],
        ) > (
            best["macro_f1"],
            best["balanced_accuracy"],
            best["accuracy"],
        ):
            best = compact_metrics(val_metrics)
            best["epoch"] = epoch

    final_full = evaluate(model, val_loader, device, criterion)
    train_final_full = evaluate(model, train_eval_loader, device, criterion)
    duration = time.perf_counter() - start

    prediction = prediction_rows(spec, final_full)

    return {
        "run_id": spec.run_id,
        "task": spec.task,
        "policy": spec.policy,
        "recipe": spec.recipe,
        "fold_id": spec.fold.fold_id,
        "seed": spec.seed,
        "train_subjects": spec.fold.train_subjects,
        "val_subjects": spec.fold.val_subjects,
        "train_n": int(len(train_ds)),
        "val_n": int(len(val_ds)),
        "feature_dim": int(train_ds.feature_dim),
        "train_label_counts": count_ints(train_labels),
        "val_label_counts": count_ints(val_labels),
        "sampler": "weighted_random_sampler" if spec.recipe == "balanced_sampler_ce" else "shuffle",
        "class_weights": class_weights_from_labels(train_labels, torch.device("cpu")).numpy().tolist() if spec.recipe == "ce_class_weighted" else None,
        "feature_scaler": {
            "mean_mean": float(np.asarray(train_ds.mean).mean()),
            "mean_std": float(np.asarray(train_ds.mean).std()),
            "std_mean": float(np.asarray(train_ds.std).mean()),
            "std_min": float(np.asarray(train_ds.std).min()),
            "std_max": float(np.asarray(train_ds.std).max()),
        },
        "epochs": args.epochs,
        "lr": args.lr,
        "weight_decay": args.weight_decay,
        "batch_size": args.batch_size,
        "hidden_dim": args.hidden_dim,
        "dropout": args.dropout,
        "duration_sec": duration,
        "epoch_records": epoch_records,
        "best": best,
        "final": compact_metrics(final_full),
        "train_final": compact_metrics(train_final_full),
        "prediction_rows": prediction,
    }


def build_run_specs(tasks: list[str], policy: str, recipes: list[str], folds: list[Fold], seeds: list[int], max_runs: int) -> list[RunSpec]:
    specs: list[RunSpec] = []
    run_id = 1
    for task in tasks:
        for seed in seeds:
            for fold in folds:
                for recipe in recipes:
                    specs.append(RunSpec(run_id=run_id, task=task, policy=policy, recipe=recipe, fold=fold, seed=seed))
                    run_id += 1
    if max_runs and max_runs > 0:
        specs = specs[:max_runs]
        specs = [
            RunSpec(run_id=i, task=s.task, policy=s.policy, recipe=s.recipe, fold=s.fold, seed=s.seed)
            for i, s in enumerate(specs, start=1)
        ]
    return specs


def aggregate_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for run in runs:
        grouped.setdefault((run["task"], run["policy"], run["recipe"]), []).append(run)

    rows: list[dict[str, Any]] = []
    for (task, policy, recipe), group in sorted(grouped.items()):
        final_macro = [float(g["final"]["macro_f1"]) for g in group]
        final_bal = [float(g["final"]["balanced_accuracy"]) for g in group]
        final_acc = [float(g["final"]["accuracy"]) for g in group]
        majority_acc = [float(g["final"]["majority_baseline"]["accuracy"]) for g in group]
        threshold_macro = [float(g["final"]["threshold_sweep"]["best"]["macro_f1"]) for g in group]
        threshold_bal = [float(g["final"]["threshold_sweep"]["best"]["balanced_accuracy"]) for g in group]
        threshold_values = [float(g["final"]["threshold_sweep"]["best"]["threshold"]) for g in group]
        rows.append(
            {
                "task": task,
                "policy": policy,
                "recipe": recipe,
                "runs": len(group),
                "final_macro_f1": summarize(final_macro),
                "final_balanced_accuracy": summarize(final_bal),
                "final_accuracy": summarize(final_acc),
                "majority_accuracy": summarize(majority_acc),
                "threshold_best_macro_f1": summarize(threshold_macro),
                "threshold_best_balanced_accuracy": summarize(threshold_bal),
                "threshold_best_value": summarize(threshold_values),
                "threshold_gain_macro_f1": summarize([t - f for t, f in zip(threshold_macro, final_macro)]),
                "threshold_gain_balanced_accuracy": summarize([t - f for t, f in zip(threshold_bal, final_bal)]),
                "one_class_final_runs": int(sum(1 for g in group if g["final"]["one_class_pred"])),
                "threshold_one_class_final_runs": int(sum(1 for g in group if g["final"]["threshold_sweep"]["best"]["one_class_pred"])),
            }
        )
    return rows


def fmt(value: float) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    return f"{float(value):.4f}"


def write_markdown(report: dict[str, Any], path: Path) -> None:
    config = report["config"]
    lines: list[str] = []
    lines.append("# I-DARE EMG Feature-Only Training Smoke")
    lines.append("")
    lines.append("This report was generated by `scripts/30_run_idare_emg_feature_smoke.py`.")
    lines.append("")
    lines.append("No raw I-DARE EMG HDF5/MAT files were loaded inside training loops.")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- feature_npy: `{config['feature_npy']}`")
    lines.append(f"- feature_index: `{config['feature_index']}`")
    lines.append("")
    lines.append("## Run Scope")
    lines.append("")
    lines.append(f"- label_policy: `{config['label_policy']}`")
    lines.append(f"- tasks: `{', '.join(config['tasks'])}`")
    lines.append(f"- recipes: `{', '.join(config['recipes'])}`")
    lines.append(f"- epochs: `{config['epochs']}`")
    lines.append(f"- max_runs: `{config['max_runs']}`")
    lines.append(f"- device: `{config['device']}`")
    lines.append(f"- model: `TinyEMGMLP(feature_dim={config['feature_dim']}, hidden_dim={config['hidden_dim']})`")
    lines.append("")
    lines.append("## Aggregate")
    lines.append("")
    lines.append("| Task | Policy | Recipe | Runs | Final macro F1 | Final bal acc | Final acc | Threshold macro F1 | Threshold bal acc | One-class final runs | Majority acc |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in report["aggregate"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["task"],
                    row["policy"],
                    row["recipe"],
                    str(row["runs"]),
                    fmt(row["final_macro_f1"]["mean"]),
                    fmt(row["final_balanced_accuracy"]["mean"]),
                    fmt(row["final_accuracy"]["mean"]),
                    fmt(row["threshold_best_macro_f1"]["mean"]),
                    fmt(row["threshold_best_balanced_accuracy"]["mean"]),
                    str(row["one_class_final_runs"]),
                    fmt(row["majority_accuracy"]["mean"]),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## Aggregate Threshold Diagnostics")
    lines.append("")
    lines.append("| Task | Policy | Recipe | Runs | Mean threshold | Macro F1 gain | Bal acc gain | Threshold one-class runs |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|")
    for row in report["aggregate"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["task"],
                    row["policy"],
                    row["recipe"],
                    str(row["runs"]),
                    fmt(row["threshold_best_value"]["mean"]),
                    fmt(row["threshold_gain_macro_f1"]["mean"]),
                    fmt(row["threshold_gain_balanced_accuracy"]["mean"]),
                    str(row["threshold_one_class_final_runs"]),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## Per-run Final Diagnostics")
    lines.append("")
    lines.append("| Run | Task | Recipe | Fold | Seed | Train n | Val n | Macro F1 | Bal acc | Acc | Pred 0 | Pred 1 | TN | FP | FN | TP | One-class | Majority acc |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|")
    for run in report["runs"]:
        final = run["final"]
        confusion = final["confusion"]
        pred_counts = final["pred_counts"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(run["run_id"]),
                    run["task"],
                    run["recipe"],
                    str(run["fold_id"]),
                    str(run["seed"]),
                    str(run["train_n"]),
                    str(run["val_n"]),
                    fmt(final["macro_f1"]),
                    fmt(final["balanced_accuracy"]),
                    fmt(final["accuracy"]),
                    str(pred_counts["0"]),
                    str(pred_counts["1"]),
                    str(confusion["tn"]),
                    str(confusion["fp"]),
                    str(confusion["fn"]),
                    str(confusion["tp"]),
                    str(final["one_class_pred"]).lower(),
                    fmt(final["majority_baseline"]["accuracy"]),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## Train vs Validation Probability Diagnostics")
    lines.append("")
    lines.append("| Run | Task | Recipe | Fold | Train P1 mean | Val P1 mean | Mean shift | Train pred 0 | Train pred 1 | Val pred 0 | Val pred 1 |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for run in report["runs"]:
        train = run["train_final"]
        final = run["final"]
        train_p = train["prob1_summary"]
        val_p = final["prob1_summary"]
        train_counts = train["pred_counts"]
        val_counts = final["pred_counts"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(run["run_id"]),
                    run["task"],
                    run["recipe"],
                    str(run["fold_id"]),
                    fmt(train_p["mean"]),
                    fmt(val_p["mean"]),
                    fmt(val_p["mean"] - train_p["mean"]),
                    str(train_counts["0"]),
                    str(train_counts["1"]),
                    str(val_counts["0"]),
                    str(val_counts["1"]),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## Probability / Threshold Diagnostics")
    lines.append("")
    lines.append("| Run | Task | Recipe | P1 mean | P1 q05 | P1 median | P1 q95 | Best threshold | Best threshold macro F1 | Best threshold bal acc | Best threshold pred 0 | Best threshold pred 1 |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for run in report["runs"]:
        final = run["final"]
        prob = final["prob1_summary"]
        best = final["threshold_sweep"]["best"]
        lines.append(
            "| "
            + " | ".join(
                [
                    str(run["run_id"]),
                    run["task"],
                    run["recipe"],
                    fmt(prob["mean"]),
                    fmt(prob["q05"]),
                    fmt(prob["median"]),
                    fmt(prob["q95"]),
                    fmt(best["threshold"]),
                    fmt(best["macro_f1"]),
                    fmt(best["balanced_accuracy"]),
                    str(best["pred_counts"]["0"]),
                    str(best["pred_counts"]["1"]),
                ]
            )
            + " |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This is a smoke/stabilization report, not a final LOSO result.")
    lines.append("- Features are standardized using train-fold statistics only.")
    lines.append("- Primary diagnostics are macro F1, balanced accuracy, one-class collapse, threshold behavior, and majority baseline.")
    lines.append("- This is the feature-level I-DARE EMG-only path. Raw EMG-only should be a separate ablation after this path is stable.")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()

    feature_index = pd.read_csv(args.feature_index)
    if "subject_id" not in feature_index.columns:
        raise KeyError("feature index must contain subject_id")

    feature_cache = np.load(args.feature_npy, mmap_mode="r")
    if feature_cache.ndim != 2:
        raise ValueError(f"feature cache must be 2D, got shape={feature_cache.shape}")

    subjects = sorted(int(s) for s in feature_index["subject_id"].dropna().astype(int).unique().tolist())
    folds = make_subject_folds(subjects, args.folds, seed=20240506)
    specs = build_run_specs(
        tasks=args.tasks,
        policy=args.label_policy,
        recipes=args.recipes,
        folds=folds,
        seeds=args.seeds,
        max_runs=args.max_runs,
    )

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")

    print("[INFO] I-DARE EMG feature-only training smoke")
    print(f"[INFO] feature_npy={args.feature_npy}")
    print(f"[INFO] feature_index={args.feature_index}")
    print(f"[INFO] feature_shape={list(feature_cache.shape)}")
    print(f"[INFO] label_policy={args.label_policy}")
    print(f"[INFO] tasks={args.tasks}")
    print(f"[INFO] recipes={args.recipes}")
    print(f"[INFO] epochs={args.epochs}")
    print(f"[INFO] max_runs={args.max_runs}")
    print(f"[INFO] planned_runs={len(specs)}")
    print(f"[INFO] device={device}")

    runs: list[dict[str, Any]] = []
    prediction_rows_all: list[dict[str, Any]] = []
    start = time.perf_counter()

    for i, spec in enumerate(specs, start=1):
        print(
            f"[RUN] {i}/{len(specs)} task={spec.task} policy={spec.policy} "
            f"recipe={spec.recipe} fold={spec.fold.fold_id} seed={spec.seed} "
            f"val_subjects={spec.fold.val_subjects}"
        )
        run = train_one_run(args, spec, device)
        prediction_rows_all.extend(run.pop("prediction_rows"))
        runs.append(run)

        final = run["final"]
        print(
            json.dumps(
                {
                    "run_id": run["run_id"],
                    "task": run["task"],
                    "recipe": run["recipe"],
                    "final_macro_f1": final["macro_f1"],
                    "final_balanced_accuracy": final["balanced_accuracy"],
                    "final_accuracy": final["accuracy"],
                    "majority_accuracy": final["majority_baseline"]["accuracy"],
                    "one_class_pred": final["one_class_pred"],
                    "pred_counts": final["pred_counts"],
                    "confusion": final["confusion"],
                },
                sort_keys=True,
            )
        )

    elapsed = time.perf_counter() - start

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": {
            "feature_npy": str(args.feature_npy),
            "feature_index": str(args.feature_index),
            "feature_shape": list(feature_cache.shape),
            "feature_dim": int(feature_cache.shape[1]),
            "label_policy": args.label_policy,
            "tasks": args.tasks,
            "recipes": args.recipes,
            "folds": args.folds,
            "seeds": args.seeds,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "lr": args.lr,
            "weight_decay": args.weight_decay,
            "grad_clip": args.grad_clip,
            "hidden_dim": args.hidden_dim,
            "dropout": args.dropout,
            "num_workers": args.num_workers,
            "max_runs": args.max_runs,
            "device": str(device),
            "train_normalization": "feature standardization fit on train rows only",
            "model": "TinyEMGMLP",
            "raw_files_loaded_inside_training_loop": False,
        },
        "aggregate": aggregate_runs(runs),
        "runs": runs,
        "elapsed_sec": elapsed,
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, args.out_md)

    if args.out_predictions_csv is not None:
        args.out_predictions_csv.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(prediction_rows_all).to_csv(args.out_predictions_csv, index=False)
        print(f"[DONE] wrote {args.out_predictions_csv}")

    print(f"[DONE] wrote {args.out_md}")
    print(f"[DONE] wrote {args.out_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
