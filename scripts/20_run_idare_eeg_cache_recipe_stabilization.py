#!/usr/bin/env python3
"""
Run tiny cache-based I-DARE EEG training-recipe stabilization checks.

Hard constraints:
- Use the validated EEG cache only.
- Do not load raw MATLAB/HDF5 files inside training loops.
- Start with smoke tests before any fuller run.
- Default label policy is midpoint_as_high.

Inputs:
- .cache/idare_eeg_windows_32x640_float32.npy
- .cache/idare_eeg_cache_index.csv

Outputs:
- docs/idare_eeg_cache_recipe_stabilization.md
- docs/idare_eeg_cache_recipe_stabilization.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from emotion_deap_idare.models.eeg_segment_classifier import EEGSegmentClassifier  # noqa: E402

DEFAULT_CACHE_NPY = ROOT / ".cache" / "idare_eeg_windows_32x640_float32.npy"
DEFAULT_CACHE_INDEX = ROOT / ".cache" / "idare_eeg_cache_index.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "idare_eeg_cache_recipe_stabilization.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "idare_eeg_cache_recipe_stabilization.json"

VALID_TASKS = {"valence", "arousal"}
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
    parser.add_argument("--cache-npy", type=Path, default=DEFAULT_CACHE_NPY)
    parser.add_argument("--cache-index", type=Path, default=DEFAULT_CACHE_INDEX)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--tasks", nargs="+", default=["valence"], choices=sorted(VALID_TASKS))
    parser.add_argument("--label-policy", default="midpoint_as_high", choices=sorted(VALID_POLICIES))
    parser.add_argument(
        "--recipes",
        nargs="+",
        default=["ce_class_weighted", "ce_no_class_weight"],
        choices=sorted(VALID_RECIPES),
    )
    parser.add_argument("--folds", type=int, default=6)
    parser.add_argument("--seeds", nargs="+", type=int, default=[11])
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--max-runs", type=int, default=2, help="0 means run all planned specs.")
    parser.add_argument("--cpu", action="store_true")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def label_column(task: str, policy: str) -> str:
    if task not in VALID_TASKS:
        raise ValueError(f"Unknown task: {task}")
    if policy not in VALID_POLICIES:
        raise ValueError(f"Unknown policy: {policy}")
    return f"{task}_{policy}"


def safe_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def count_ints(values: list[int]) -> dict[str, int]:
    return {
        "0": int(sum(1 for v in values if int(v) == 0)),
        "1": int(sum(1 for v in values if int(v) == 1)),
    }


def binary_metrics_no_majority(y_true: list[int], y_pred: list[int]) -> dict[str, float]:
    labels = [0, 1]
    recalls: list[float] = []
    f1s: list[float] = []

    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)

        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2.0 * precision * recall, precision + recall)

        recalls.append(recall)
        f1s.append(f1)

    total = len(y_true)
    correct = sum(int(t == p) for t, p in zip(y_true, y_pred))
    return {
        "accuracy": safe_div(correct, total),
        "balanced_accuracy": float(sum(recalls) / len(recalls)) if recalls else math.nan,
        "macro_f1": float(sum(f1s) / len(f1s)) if f1s else math.nan,
    }


def binary_metrics(y_true: list[int], y_pred: list[int]) -> dict[str, Any]:
    labels = [0, 1]
    total = len(y_true)
    correct = sum(int(t == p) for t, p in zip(y_true, y_pred))

    confusion = {
        "tn": int(sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)),
        "fp": int(sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)),
        "fn": int(sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)),
        "tp": int(sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)),
    }

    per_class: dict[str, Any] = {}
    recalls: list[float] = []
    f1s: list[float] = []

    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)

        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2.0 * precision * recall, precision + recall)

        recalls.append(recall)
        f1s.append(f1)

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
    majority_label = max(labels, key=lambda label: true_counts[str(label)])
    majority_pred = [majority_label for _ in y_true]
    majority_metrics = binary_metrics_no_majority(y_true, majority_pred)

    pred_unique = sorted({int(p) for p in y_pred})

    return {
        "n": int(total),
        "accuracy": safe_div(correct, total),
        "balanced_accuracy": float(sum(recalls) / len(recalls)) if recalls else math.nan,
        "macro_f1": float(sum(f1s) / len(f1s)) if f1s else math.nan,
        "true_counts": true_counts,
        "pred_counts": pred_counts,
        "confusion": confusion,
        "per_class": per_class,
        "one_class_pred": bool(len(pred_unique) == 1),
        "pred_unique_labels": pred_unique,
        "collapsed_to_label": int(pred_unique[0]) if len(pred_unique) == 1 else None,
        "majority_baseline": {
            "label": int(majority_label),
            **majority_metrics,
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


class IDARECachedEEGDataset(Dataset):
    def __init__(
        self,
        *,
        cache_npy: Path,
        cache_index: Path,
        task: str,
        policy: str,
        subjects: list[int],
    ) -> None:
        if not cache_npy.exists():
            raise FileNotFoundError(f"Missing EEG cache: {cache_npy}")
        if not cache_index.exists():
            raise FileNotFoundError(f"Missing EEG cache index: {cache_index}")

        col = label_column(task, policy)
        df = pd.read_csv(cache_index)

        required = {"cache_row", "subject_id", col}
        missing = sorted(required - set(df.columns))
        if missing:
            raise KeyError(f"Missing required cache-index columns: {missing}")

        df = df[df["subject_id"].astype(int).isin([int(s) for s in subjects])].copy()
        df[col] = df[col].map(safe_float)
        df = df[df[col].isin([0.0, 1.0])].copy()
        df["label"] = df[col].astype(int)
        df["cache_row"] = df["cache_row"].astype(int)
        df["subject_id"] = df["subject_id"].astype(int)
        df = df.sort_values(["subject_id", "cache_row"]).reset_index(drop=True)

        if len(df) == 0:
            raise ValueError(f"No rows for task={task}, policy={policy}, subjects={subjects}")

        cache = np.load(cache_npy, mmap_mode="r")
        if cache.ndim != 3 or tuple(cache.shape[1:]) != (32, 640):
            raise ValueError(f"Unexpected cache shape: {cache.shape}; expected [N, 32, 640]")
        if int(df["cache_row"].max()) >= int(cache.shape[0]):
            raise ValueError("cache_row exceeds cache first dimension")

        self.cache_npy = cache_npy
        self.cache_index = cache_index
        self.task = task
        self.policy = policy
        self.subjects = [int(s) for s in subjects]
        self.label_col = col
        self.df = df
        self.cache = cache

    def __len__(self) -> int:
        return int(len(self.df))

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.df.iloc[index]
        cache_row = int(row["cache_row"])
        eeg = np.array(self.cache[cache_row], dtype=np.float32, copy=True)
        stimulus_id = str(row["stimulus_id"]) if "stimulus_id" in row.index else ""
        return {
            "eeg": torch.from_numpy(eeg),
            "label": torch.tensor(int(row["label"]), dtype=torch.long),
            "cache_row": cache_row,
            "subject_id": int(row["subject_id"]),
            "stimulus_id": stimulus_id,
        }


def make_model(device: torch.device) -> EEGSegmentClassifier:
    return EEGSegmentClassifier(
        C=32,
        sampling_rate=128,
        window_sec=5.0,
        n_classes=2,
        modelsize="lite",
        stem_fusion="concat",
        channel_pos_mode="learnable",
        channel_mixer="mha",
        norm_kind="gn",
        use_spectral_branch=False,
    ).to(device)


def class_weights_from_labels(labels: list[int], device: torch.device) -> torch.Tensor:
    counts = {
        0: int(sum(1 for y in labels if y == 0)),
        1: int(sum(1 for y in labels if y == 1)),
    }
    total = sum(counts.values())
    weights = []
    for label in [0, 1]:
        count = counts[label]
        weights.append(total / (2.0 * count) if count > 0 else 0.0)
    return torch.tensor(weights, dtype=torch.float32, device=device)


def numeric_summary(values: list[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=np.float64)
    if arr.size == 0:
        return {
            "n": 0,
            "mean": math.nan,
            "std": math.nan,
            "min": math.nan,
            "q05": math.nan,
            "q25": math.nan,
            "median": math.nan,
            "q75": math.nan,
            "q95": math.nan,
            "max": math.nan,
        }
    return {
        "n": int(arr.size),
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


def threshold_sweep_from_probs(
    y_true: list[int],
    prob1: list[float],
    *,
    thresholds: list[float] | None = None,
) -> dict[str, Any]:
    if thresholds is None:
        thresholds = [round(v / 100.0, 2) for v in range(5, 100, 5)]

    rows: list[dict[str, Any]] = []
    for threshold in thresholds:
        y_pred = [1 if float(p) >= threshold else 0 for p in prob1]
        metrics = binary_metrics(y_true, y_pred)
        rows.append(
            {
                "threshold": float(threshold),
                "macro_f1": float(metrics["macro_f1"]),
                "balanced_accuracy": float(metrics["balanced_accuracy"]),
                "accuracy": float(metrics["accuracy"]),
                "pred_counts": metrics["pred_counts"],
                "confusion": metrics["confusion"],
                "one_class_pred": bool(metrics["one_class_pred"]),
            }
        )

    best = max(
        rows,
        key=lambda row: (
            float(row["macro_f1"]),
            float(row["balanced_accuracy"]),
            float(row["accuracy"]),
            -abs(float(row["threshold"]) - 0.5),
        ),
    )

    return {
        "best": best,
        "rows": rows,
    }


def eval_model(
    model: torch.nn.Module,
    loader: DataLoader,
    *,
    device: torch.device,
    criterion: torch.nn.Module,
) -> dict[str, Any]:
    model.eval()
    y_true: list[int] = []
    y_pred: list[int] = []
    prob1_values: list[float] = []
    logit_margin_values: list[float] = []
    loss_sum = 0.0
    n_seen = 0

    with torch.no_grad():
        for batch in loader:
            x = batch["eeg"].to(device=device, dtype=torch.float32)
            y = batch["label"].to(device=device, dtype=torch.long)

            logits, _ = model(x, return_attn=False)
            loss = criterion(logits, y)
            probs = torch.softmax(logits, dim=1)
            prob1 = probs[:, 1]
            margin = logits[:, 1] - logits[:, 0]
            pred = logits.argmax(dim=1)

            batch_n = int(y.numel())
            loss_sum += float(loss.item()) * batch_n
            n_seen += batch_n

            y_true.extend(int(v) for v in y.detach().cpu().tolist())
            y_pred.extend(int(v) for v in pred.detach().cpu().tolist())
            prob1_values.extend(float(v) for v in prob1.detach().cpu().tolist())
            logit_margin_values.extend(float(v) for v in margin.detach().cpu().tolist())

    metrics = binary_metrics(y_true, y_pred)
    metrics["loss_mean"] = safe_div(loss_sum, n_seen)
    metrics["batches"] = int(len(loader))
    metrics["prob1_summary"] = numeric_summary(prob1_values)
    metrics["logit_margin_summary"] = numeric_summary(logit_margin_values)
    metrics["threshold_sweep"] = threshold_sweep_from_probs(y_true, prob1_values)
    return metrics


def train_one(
    *,
    spec: RunSpec,
    cache_npy: Path,
    cache_index: Path,
    device: torch.device,
    batch_size: int,
    epochs: int,
    lr: float,
    weight_decay: float,
    grad_clip: float,
    num_workers: int,
) -> dict[str, Any]:
    set_seed(spec.seed)
    start = time.perf_counter()

    train_ds = IDARECachedEEGDataset(
        cache_npy=cache_npy,
        cache_index=cache_index,
        task=spec.task,
        policy=spec.policy,
        subjects=spec.fold.train_subjects,
    )
    val_ds = IDARECachedEEGDataset(
        cache_npy=cache_npy,
        cache_index=cache_index,
        task=spec.task,
        policy=spec.policy,
        subjects=spec.fold.val_subjects,
    )

    train_labels = [int(v) for v in train_ds.df["label"].tolist()]
    val_labels = [int(v) for v in val_ds.df["label"].tolist()]
    train_counts = count_ints(train_labels)
    val_counts = count_ints(val_labels)

    generator = torch.Generator()
    generator.manual_seed(spec.seed)

    train_sampler = None
    sampler_name = "shuffle"

    if spec.recipe == "balanced_sampler_ce":
        count_lookup = {
            0: int(train_counts["0"]),
            1: int(train_counts["1"]),
        }
        sample_weights = [
            1.0 / float(count_lookup[int(label)]) if count_lookup[int(label)] > 0 else 0.0
            for label in train_labels
        ]
        train_sampler = WeightedRandomSampler(
            weights=torch.as_tensor(sample_weights, dtype=torch.double),
            num_samples=len(sample_weights),
            replacement=True,
            generator=generator,
        )
        sampler_name = "weighted_random_sampler"

    train_loader_kwargs: dict[str, Any] = {
        "batch_size": batch_size,
        "num_workers": num_workers,
    }

    if train_sampler is None:
        train_loader_kwargs["shuffle"] = True
        train_loader_kwargs["generator"] = generator
    else:
        train_loader_kwargs["shuffle"] = False
        train_loader_kwargs["sampler"] = train_sampler

    train_loader = DataLoader(train_ds, **train_loader_kwargs)
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
    )

    model = make_model(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    if spec.recipe == "ce_class_weighted":
        class_weights = class_weights_from_labels(train_labels, device)
        train_criterion = torch.nn.CrossEntropyLoss(weight=class_weights)
        class_weights_out: list[float] | None = [
            float(v) for v in class_weights.detach().cpu().tolist()
        ]
    elif spec.recipe in {"ce_no_class_weight", "balanced_sampler_ce"}:
        train_criterion = torch.nn.CrossEntropyLoss()
        class_weights_out = None
    else:
        raise ValueError(f"Unsupported recipe: {spec.recipe}")

    eval_criterion = torch.nn.CrossEntropyLoss()

    epoch_records: list[dict[str, Any]] = []
    best_metrics: dict[str, Any] | None = None
    best_epoch = 0

    for epoch in range(1, epochs + 1):
        model.train()
        train_loss_sum = 0.0
        train_n = 0

        for batch in train_loader:
            x = batch["eeg"].to(device=device, dtype=torch.float32)
            y = batch["label"].to(device=device, dtype=torch.long)

            optimizer.zero_grad(set_to_none=True)
            logits, _ = model(x, return_attn=False)
            loss = train_criterion(logits, y)
            loss.backward()

            if grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)

            optimizer.step()

            batch_n = int(y.numel())
            train_loss_sum += float(loss.item()) * batch_n
            train_n += batch_n

        val_metrics = eval_model(model, val_loader, device=device, criterion=eval_criterion)
        train_loss_mean = safe_div(train_loss_sum, train_n)

        epoch_record = {
            "epoch": int(epoch),
            "train_loss_mean": train_loss_mean,
            "val": val_metrics,
        }
        epoch_records.append(epoch_record)

        if best_metrics is None:
            best_metrics = val_metrics
            best_epoch = epoch
        else:
            old_score = (float(best_metrics["macro_f1"]), float(best_metrics["balanced_accuracy"]))
            new_score = (float(val_metrics["macro_f1"]), float(val_metrics["balanced_accuracy"]))
            if new_score > old_score:
                best_metrics = val_metrics
                best_epoch = epoch

    final_metrics = epoch_records[-1]["val"]
    assert best_metrics is not None

    duration_sec = time.perf_counter() - start

    return {
        "run_id": int(spec.run_id),
        "task": spec.task,
        "policy": spec.policy,
        "recipe": spec.recipe,
        "fold_id": int(spec.fold.fold_id),
        "val_subjects": [int(s) for s in spec.fold.val_subjects],
        "train_subject_count": int(len(spec.fold.train_subjects)),
        "val_subject_count": int(len(spec.fold.val_subjects)),
        "seed": int(spec.seed),
        "epochs": int(epochs),
        "batch_size": int(batch_size),
        "lr": float(lr),
        "weight_decay": float(weight_decay),
        "grad_clip": float(grad_clip),
        "train_n": int(len(train_ds)),
        "val_n": int(len(val_ds)),
        "train_counts": train_counts,
        "val_counts": val_counts,
        "class_weights": class_weights_out,
        "sampler": sampler_name,
        "final": final_metrics,
        "best": {
            "epoch": int(best_epoch),
            **best_metrics,
        },
        "epoch_records": epoch_records,
        "duration_sec": float(duration_sec),
    }


def subjects_for_task(cache_index: Path, task: str, policy: str) -> list[int]:
    col = label_column(task, policy)
    df = pd.read_csv(cache_index)
    if col not in df.columns:
        raise KeyError(f"Missing label column {col}. Columns: {list(df.columns)}")
    df[col] = df[col].map(safe_float)
    df = df[df[col].isin([0.0, 1.0])].copy()
    return sorted(int(s) for s in df["subject_id"].astype(int).unique().tolist())


def make_subject_folds(subjects: list[int], n_folds: int) -> list[Fold]:
    subjects = sorted({int(s) for s in subjects})
    if not subjects:
        raise ValueError("No subjects available for folds")
    n_folds = max(1, min(int(n_folds), len(subjects)))

    shuffled = list(subjects)
    rng = random.Random(20260505)
    rng.shuffle(shuffled)

    chunks = np.array_split(np.asarray(shuffled, dtype=int), n_folds)
    folds: list[Fold] = []
    for i, chunk in enumerate(chunks, start=1):
        val_subjects = sorted(int(s) for s in chunk.tolist())
        val_set = set(val_subjects)
        train_subjects = sorted(int(s) for s in subjects if int(s) not in val_set)
        folds.append(Fold(fold_id=i, val_subjects=val_subjects, train_subjects=train_subjects))
    return folds


def build_run_specs(args: argparse.Namespace) -> list[RunSpec]:
    specs: list[RunSpec] = []
    run_id = 1

    for task in args.tasks:
        subjects = subjects_for_task(args.cache_index, task, args.label_policy)
        folds = make_subject_folds(subjects, args.folds)

        for fold in folds:
            for seed in args.seeds:
                for recipe in args.recipes:
                    specs.append(
                        RunSpec(
                            run_id=run_id,
                            task=task,
                            policy=args.label_policy,
                            recipe=recipe,
                            fold=fold,
                            seed=int(seed),
                        )
                    )
                    run_id += 1

    if args.max_runs and args.max_runs > 0:
        specs = specs[: int(args.max_runs)]
        specs = [
            RunSpec(
                run_id=i + 1,
                task=s.task,
                policy=s.policy,
                recipe=s.recipe,
                fold=s.fold,
                seed=s.seed,
            )
            for i, s in enumerate(specs)
        ]

    return specs


def aggregate_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for run in runs:
        key = (str(run["task"]), str(run["policy"]), str(run["recipe"]))
        groups.setdefault(key, []).append(run)

    rows: list[dict[str, Any]] = []
    for (task, policy, recipe), group in sorted(groups.items()):
        final_macro_f1 = [float(r["final"]["macro_f1"]) for r in group]
        final_bal_acc = [float(r["final"]["balanced_accuracy"]) for r in group]
        final_acc = [float(r["final"]["accuracy"]) for r in group]
        best_macro_f1 = [float(r["best"]["macro_f1"]) for r in group]
        best_bal_acc = [float(r["best"]["balanced_accuracy"]) for r in group]
        majority_acc = [float(r["final"]["majority_baseline"]["accuracy"]) for r in group]
        one_class = [bool(r["final"]["one_class_pred"]) for r in group]

        rows.append(
            {
                "task": task,
                "policy": policy,
                "recipe": recipe,
                "runs": int(len(group)),
                "final_macro_f1": summarize(final_macro_f1),
                "final_balanced_accuracy": summarize(final_bal_acc),
                "final_accuracy": summarize(final_acc),
                "best_macro_f1": summarize(best_macro_f1),
                "best_balanced_accuracy": summarize(best_bal_acc),
                "majority_accuracy": summarize(majority_acc),
                "one_class_final_runs": int(sum(1 for v in one_class if v)),
            }
        )

    return rows


def fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        return f"{value:.4f}"
    return str(value)


def write_reports(report: dict[str, Any], out_md: Path, out_json: Path) -> None:
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)

    out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines: list[str] = []
    lines.append("# I-DARE EEG Cache Recipe Stabilization")
    lines.append("")
    lines.append("This report was generated by `scripts/20_run_idare_eeg_cache_recipe_stabilization.py`.")
    lines.append("")
    lines.append("No raw MATLAB/HDF5 files were loaded inside training loops.")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- cache_npy: `{report['config']['cache_npy']}`")
    lines.append(f"- cache_index: `{report['config']['cache_index']}`")
    lines.append("")
    lines.append("## Run Scope")
    lines.append("")
    lines.append(f"- label_policy: `{report['config']['label_policy']}`")
    lines.append(f"- tasks: `{', '.join(report['config']['tasks'])}`")
    lines.append(f"- recipes: `{', '.join(report['config']['recipes'])}`")
    lines.append(f"- epochs: `{report['config']['epochs']}`")
    lines.append(f"- max_runs: `{report['config']['max_runs']}`")
    lines.append(f"- device: `{report['config']['device']}`")
    lines.append("")
    lines.append("## Aggregate")
    lines.append("")
    lines.append(
        "| Task | Policy | Recipe | Runs | Final macro F1 | Final bal acc | Final acc | "
        "Best macro F1 | One-class final runs | Majority acc |"
    )
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in report["aggregate"]:
        lines.append(
            "| {task} | {policy} | {recipe} | {runs} | {fmf1} | {fba} | {facc} | {bmf1} | {one} | {maj} |".format(
                task=row["task"],
                policy=row["policy"],
                recipe=row["recipe"],
                runs=row["runs"],
                fmf1=fmt(row["final_macro_f1"]["mean"]),
                fba=fmt(row["final_balanced_accuracy"]["mean"]),
                facc=fmt(row["final_accuracy"]["mean"]),
                bmf1=fmt(row["best_macro_f1"]["mean"]),
                one=row["one_class_final_runs"],
                maj=fmt(row["majority_accuracy"]["mean"]),
            )
        )

    lines.append("")
    lines.append("## Per-run Final Diagnostics")
    lines.append("")
    lines.append(
        "| Run | Task | Recipe | Fold | Seed | Train n | Val n | Macro F1 | Bal acc | Acc | "
        "Pred 0 | Pred 1 | TN | FP | FN | TP | One-class | Majority acc |"
    )
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|")
    for run in report["runs"]:
        final = run["final"]
        pred = final["pred_counts"]
        conf = final["confusion"]
        lines.append(
            "| {run_id} | {task} | {recipe} | {fold} | {seed} | {train_n} | {val_n} | "
            "{mf1} | {ba} | {acc} | {p0} | {p1} | {tn} | {fp} | {fn} | {tp} | {one} | {maj} |".format(
                run_id=run["run_id"],
                task=run["task"],
                recipe=run["recipe"],
                fold=run["fold_id"],
                seed=run["seed"],
                train_n=run["train_n"],
                val_n=run["val_n"],
                mf1=fmt(final["macro_f1"]),
                ba=fmt(final["balanced_accuracy"]),
                acc=fmt(final["accuracy"]),
                p0=pred["0"],
                p1=pred["1"],
                tn=conf["tn"],
                fp=conf["fp"],
                fn=conf["fn"],
                tp=conf["tp"],
                one=str(final["one_class_pred"]).lower(),
                maj=fmt(final["majority_baseline"]["accuracy"]),
            )
        )

    lines.append("")
    lines.append("## Probability / Threshold Diagnostics")
    lines.append("")
    lines.append(
        "| Run | Task | Recipe | P1 mean | P1 q05 | P1 median | P1 q95 | Margin mean | Best threshold | Best threshold macro F1 | Best threshold bal acc | Best threshold pred 0 | Best threshold pred 1 |"
    )
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for run in report["runs"]:
        final = run["final"]
        prob = final.get("prob1_summary", {})
        margin = final.get("logit_margin_summary", {})
        best_thr = final.get("threshold_sweep", {}).get("best", {})
        best_pred = best_thr.get("pred_counts", {"0": "", "1": ""})
        lines.append(
            "| {run_id} | {task} | {recipe} | {pmean} | {pq05} | {pmed} | {pq95} | {mmean} | {thr} | {tmf1} | {tba} | {tp0} | {tp1} |".format(
                run_id=run["run_id"],
                task=run["task"],
                recipe=run["recipe"],
                pmean=fmt(prob.get("mean")),
                pq05=fmt(prob.get("q05")),
                pmed=fmt(prob.get("median")),
                pq95=fmt(prob.get("q95")),
                mmean=fmt(margin.get("mean")),
                thr=fmt(best_thr.get("threshold")),
                tmf1=fmt(best_thr.get("macro_f1")),
                tba=fmt(best_thr.get("balanced_accuracy")),
                tp0=best_pred.get("0", ""),
                tp1=best_pred.get("1", ""),
            )
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- This is a smoke/stabilization report, not a final LOSO result.")
    lines.append("- Fuller commands should only be considered after reviewing this smoke output.")
    lines.append("- Primary diagnostics are one-class collapse, macro F1, balanced accuracy, accuracy, confusion counts, prediction counts, and majority baseline.")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()

    if args.epochs < 1:
        raise ValueError("--epochs must be >= 1")
    if args.folds < 1:
        raise ValueError("--folds must be >= 1")
    if args.batch_size < 1:
        raise ValueError("--batch-size must be >= 1")

    if not args.cache_npy.exists():
        raise FileNotFoundError(f"Missing cache npy: {args.cache_npy}")
    if not args.cache_index.exists():
        raise FileNotFoundError(f"Missing cache index: {args.cache_index}")

    cache_preview = np.load(args.cache_npy, mmap_mode="r")
    cache_shape = [int(v) for v in cache_preview.shape]
    if cache_shape != [2016, 32, 640]:
        print(f"[WARN] Cache shape is {cache_shape}, expected [2016, 32, 640]. Continuing only if compatible.")
    if cache_preview.ndim != 3 or tuple(cache_preview.shape[1:]) != (32, 640):
        raise ValueError(f"Unexpected cache shape: {cache_preview.shape}")

    device = torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")
    specs = build_run_specs(args)

    if not specs:
        raise ValueError("No run specs were built")

    print("[INFO] I-DARE EEG cache recipe stabilization")
    print(f"[INFO] cache_npy={args.cache_npy}")
    print(f"[INFO] cache_index={args.cache_index}")
    print(f"[INFO] cache_shape={cache_shape}")
    print(f"[INFO] label_policy={args.label_policy}")
    print(f"[INFO] tasks={args.tasks}")
    print(f"[INFO] recipes={args.recipes}")
    print(f"[INFO] epochs={args.epochs}")
    print(f"[INFO] max_runs={args.max_runs}")
    print(f"[INFO] planned_runs={len(specs)}")
    print(f"[INFO] device={device}")

    runs: list[dict[str, Any]] = []

    for spec in specs:
        print(
            "[RUN] {}/{} task={} policy={} recipe={} fold={} seed={} val_subjects={}".format(
                spec.run_id,
                len(specs),
                spec.task,
                spec.policy,
                spec.recipe,
                spec.fold.fold_id,
                spec.seed,
                spec.fold.val_subjects,
            ),
            flush=True,
        )

        run = train_one(
            spec=spec,
            cache_npy=args.cache_npy,
            cache_index=args.cache_index,
            device=device,
            batch_size=args.batch_size,
            epochs=args.epochs,
            lr=args.lr,
            weight_decay=args.weight_decay,
            grad_clip=args.grad_clip,
            num_workers=args.num_workers,
        )
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
                    "pred_counts": final["pred_counts"],
                    "confusion": final["confusion"],
                    "one_class_pred": final["one_class_pred"],
                    "majority_accuracy": final["majority_baseline"]["accuracy"],
                },
                sort_keys=True,
            ),
            flush=True,
        )

    aggregate = aggregate_runs(runs)

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "smoke_or_stabilization_complete",
        "config": {
            "cache_npy": str(args.cache_npy),
            "cache_index": str(args.cache_index),
            "cache_shape": cache_shape,
            "label_policy": args.label_policy,
            "tasks": list(args.tasks),
            "recipes": list(args.recipes),
            "folds": int(args.folds),
            "seeds": [int(s) for s in args.seeds],
            "epochs": int(args.epochs),
            "batch_size": int(args.batch_size),
            "lr": float(args.lr),
            "weight_decay": float(args.weight_decay),
            "grad_clip": float(args.grad_clip),
            "num_workers": int(args.num_workers),
            "max_runs": int(args.max_runs),
            "device": str(device),
        },
        "aggregate": aggregate,
        "runs": runs,
    }

    write_reports(report, args.out_md, args.out_json)

    print(f"[DONE] wrote {args.out_md}")
    print(f"[DONE] wrote {args.out_json}")


if __name__ == "__main__":
    main()
