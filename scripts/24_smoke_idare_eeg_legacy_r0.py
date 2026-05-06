#!/usr/bin/env python3
"""
Smoke-test the adapted legacy MAHNOB EEG encoder as an R0 baseline.

This script is intentionally cache-only:
- it reads .cache/idare_eeg_windows_32x640_float32.npy
- it reads .cache/idare_eeg_cache_index.csv
- it does not read raw MATLAB/HDF5 files during training

Default smoke:
- task: valence
- policy: midpoint_as_high
- models: legacy_r0 and eeg_segment_v1
- recipes: ce_class_weighted
- max-runs: 2
- epochs: 1

The point is not to claim a result. The point is to verify that the adapted
legacy encoder can be used fairly as an R0 baseline against EEGSegmentClassifier-v1.
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
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from emotion_deap_idare.models.eeg_segment_classifier import EEGSegmentClassifier  # noqa: E402
from emotion_deap_idare.models.legacy_mahnob_eeg_encoder import LegacyMAHNOBEEGEncoder  # noqa: E402
from emotion_deap_idare.models.old_style_eeg_classifier import OldStyleEEGClassifier  # noqa: E402

DEFAULT_CACHE_NPY = ROOT / ".cache" / "idare_eeg_windows_32x640_float32.npy"
DEFAULT_CACHE_INDEX = ROOT / ".cache" / "idare_eeg_cache_index.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "idare_eeg_legacy_r0_smoke.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "idare_eeg_legacy_r0_smoke.json"

VALID_TASKS = {"valence", "arousal"}
VALID_POLICIES = {"discard_midpoint", "midpoint_as_low", "midpoint_as_high"}
VALID_MODELS = {"legacy_r0", "eeg_segment_v1"}
VALID_RECIPES = {"ce_class_weighted", "ce_no_class_weight"}


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
    model_name: str
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
    parser.add_argument("--models", nargs="+", default=["legacy_r0", "eeg_segment_v1"], choices=sorted(VALID_MODELS))
    parser.add_argument("--recipes", nargs="+", default=["ce_class_weighted"], choices=sorted(VALID_RECIPES))
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
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": int(sum(1 for t in y_true if t == label)),
            "tp": int(tp),
            "fp": int(fp),
            "fn": int(fn),
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

        self.df = df
        self.cache = cache

    def __len__(self) -> int:
        return int(len(self.df))

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.df.iloc[index]
        cache_row = int(row["cache_row"])
        eeg = np.array(self.cache[cache_row], dtype=np.float32, copy=True)
        return {
            "eeg": torch.from_numpy(eeg),
            "label": torch.tensor(int(row["label"]), dtype=torch.long),
            "cache_row": cache_row,
            "subject_id": int(row["subject_id"]),
        }


def make_model(model_name: str, device: torch.device) -> torch.nn.Module:
    if model_name == "legacy_r0":
        old_encoder = LegacyMAHNOBEEGEncoder(
            C=32,
            timelen=640,
            dropout=0.1,
            modelsize="lite",
            norm_kind="gn",
            use_temp_pools=False,
        )
        return OldStyleEEGClassifier(
            old_encoder=old_encoder,
            d_embed=old_encoder.Dembed,
            n_classes=2,
            head_dropout=0.3,
        ).to(device)

    if model_name == "eeg_segment_v1":
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

    raise ValueError(f"Unknown model_name: {model_name}")


def run_model_forward(model: torch.nn.Module, model_name: str, x: torch.Tensor) -> tuple[torch.Tensor, dict[str, Any]]:
    if model_name == "eeg_segment_v1":
        logits, aux = model(x, return_attn=False)
        return logits, aux
    logits, aux = model(x)
    return logits, aux


def class_weights_from_labels(labels: list[int], device: torch.device) -> torch.Tensor:
    counts = {0: int(sum(1 for y in labels if y == 0)), 1: int(sum(1 for y in labels if y == 1))}
    total = sum(counts.values())
    weights = []
    for label in [0, 1]:
        count = counts[label]
        weights.append(total / (2.0 * count) if count > 0 else 0.0)
    return torch.tensor(weights, dtype=torch.float32, device=device)


def eval_model(
    model: torch.nn.Module,
    model_name: str,
    loader: DataLoader,
    *,
    device: torch.device,
    criterion: torch.nn.Module,
) -> dict[str, Any]:
    model.eval()
    y_true: list[int] = []
    y_pred: list[int] = []
    loss_sum = 0.0
    n_seen = 0

    with torch.no_grad():
        for batch in loader:
            x = batch["eeg"].to(device=device, dtype=torch.float32)
            y = batch["label"].to(device=device, dtype=torch.long)

            logits, _ = run_model_forward(model, model_name, x)
            loss = criterion(logits, y)
            pred = logits.argmax(dim=1)

            batch_n = int(y.numel())
            loss_sum += float(loss.item()) * batch_n
            n_seen += batch_n
            y_true.extend(int(v) for v in y.detach().cpu().tolist())
            y_pred.extend(int(v) for v in pred.detach().cpu().tolist())

    metrics = binary_metrics(y_true, y_pred)
    metrics["loss_mean"] = safe_div(loss_sum, n_seen)
    metrics["batches"] = int(len(loader))
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
    train_counts = count_ints(train_labels)
    val_counts = count_ints([int(v) for v in val_ds.df["label"].tolist()])

    generator = torch.Generator()
    generator.manual_seed(spec.seed)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        generator=generator,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
    )

    model = make_model(spec.model_name, device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    if spec.recipe == "ce_class_weighted":
        class_weights = class_weights_from_labels(train_labels, device)
        train_criterion = torch.nn.CrossEntropyLoss(weight=class_weights)
        class_weights_out: list[float] | None = [float(v) for v in class_weights.detach().cpu().tolist()]
    elif spec.recipe == "ce_no_class_weight":
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
            logits, _ = run_model_forward(model, spec.model_name, x)
            loss = train_criterion(logits, y)
            loss.backward()

            if grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)

            optimizer.step()

            batch_n = int(y.numel())
            train_loss_sum += float(loss.item()) * batch_n
            train_n += batch_n

        val_metrics = eval_model(model, spec.model_name, val_loader, device=device, criterion=eval_criterion)
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
        "model_name": spec.model_name,
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
                for model_name in args.models:
                    for recipe in args.recipes:
                        specs.append(
                            RunSpec(
                                run_id=run_id,
                                task=task,
                                policy=args.label_policy,
                                model_name=model_name,
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
                model_name=s.model_name,
                recipe=s.recipe,
                fold=s.fold,
                seed=s.seed,
            )
            for i, s in enumerate(specs)
        ]

    return specs


def aggregate_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for run in runs:
        key = (str(run["task"]), str(run["policy"]), str(run["model_name"]), str(run["recipe"]))
        groups.setdefault(key, []).append(run)

    rows: list[dict[str, Any]] = []
    for (task, policy, model_name, recipe), group in sorted(groups.items()):
        final_macro_f1 = [float(r["final"]["macro_f1"]) for r in group]
        final_bal_acc = [float(r["final"]["balanced_accuracy"]) for r in group]
        final_acc = [float(r["final"]["accuracy"]) for r in group]
        best_macro_f1 = [float(r["best"]["macro_f1"]) for r in group]
        majority_acc = [float(r["final"]["majority_baseline"]["accuracy"]) for r in group]
        one_class = [bool(r["final"]["one_class_pred"]) for r in group]

        rows.append(
            {
                "task": task,
                "policy": policy,
                "model_name": model_name,
                "recipe": recipe,
                "runs": int(len(group)),
                "final_macro_f1": summarize(final_macro_f1),
                "final_balanced_accuracy": summarize(final_bal_acc),
                "final_accuracy": summarize(final_acc),
                "best_macro_f1": summarize(best_macro_f1),
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
    lines.append("# I-DARE EEG Legacy R0 Smoke Test")
    lines.append("")
    lines.append("This report was generated by `scripts/24_smoke_idare_eeg_legacy_r0.py`.")
    lines.append("")
    lines.append("No raw MATLAB/HDF5 files were loaded inside training loops.")
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("- This is a smoke test, not a full run and not a final LOSO result.")
    lines.append("- `legacy_r0` means adapted MAHNOB encoder wrapped by `OldStyleEEGClassifier`.")
    lines.append("- `eeg_segment_v1` means the current EEGSegmentClassifier-v1 lite baseline.")
    lines.append("")
    lines.append("## Configuration")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(report["config"], indent=2, sort_keys=True))
    lines.append("```")
    lines.append("")
    lines.append("## Aggregate")
    lines.append("")
    lines.append(
        "| Task | Policy | Model | Recipe | Runs | Final macro F1 | Final bal acc | Final acc | "
        "Best macro F1 | One-class final runs | Majority acc |"
    )
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in report["aggregate"]:
        lines.append(
            "| {task} | {policy} | {model_name} | {recipe} | {runs} | {fmf1} | {fba} | {facc} | {bmf1} | {one} | {maj} |".format(
                task=row["task"],
                policy=row["policy"],
                model_name=row["model_name"],
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
        "| Run | Task | Model | Recipe | Fold | Seed | Train n | Val n | Macro F1 | Bal acc | Acc | "
        "Pred 0 | Pred 1 | TN | FP | FN | TP | One-class |"
    )
    lines.append("|---:|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    for run in report["runs"]:
        final = run["final"]
        pred = final["pred_counts"]
        conf = final["confusion"]
        lines.append(
            "| {run_id} | {task} | {model_name} | {recipe} | {fold} | {seed} | {train_n} | {val_n} | "
            "{mf1} | {ba} | {acc} | {p0} | {p1} | {tn} | {fp} | {fn} | {tp} | {one} |".format(
                run_id=run["run_id"],
                task=run["task"],
                model_name=run["model_name"],
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
            )
        )

    lines.append("")
    lines.append("## Interpretation Guardrail")
    lines.append("")
    lines.append("- If this smoke passes, commit only after reviewing the report.")
    lines.append("- A fuller model comparison should still be proposed separately and smoke-tested first.")
    lines.append("- Do not claim legacy superiority/inferiority from a two-run smoke test.")

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
    if cache_preview.ndim != 3 or tuple(cache_preview.shape[1:]) != (32, 640):
        raise ValueError(f"Unexpected cache shape: {cache_preview.shape}")

    device = torch.device("cpu" if args.cpu or not torch.cuda.is_available() else "cuda")
    specs = build_run_specs(args)
    if not specs:
        raise ValueError("No run specs were built")

    print("[INFO] I-DARE EEG legacy R0 smoke")
    print(f"[INFO] cache_npy={args.cache_npy}")
    print(f"[INFO] cache_index={args.cache_index}")
    print(f"[INFO] cache_shape={cache_shape}")
    print(f"[INFO] label_policy={args.label_policy}")
    print(f"[INFO] tasks={args.tasks}")
    print(f"[INFO] models={args.models}")
    print(f"[INFO] recipes={args.recipes}")
    print(f"[INFO] epochs={args.epochs}")
    print(f"[INFO] max_runs={args.max_runs}")
    print(f"[INFO] planned_runs={len(specs)}")
    print(f"[INFO] device={device}")

    runs: list[dict[str, Any]] = []
    for spec in specs:
        print(
            "[RUN] {}/{} task={} policy={} model={} recipe={} fold={} seed={} val_subjects={}".format(
                spec.run_id,
                len(specs),
                spec.task,
                spec.policy,
                spec.model_name,
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
                    "model_name": run["model_name"],
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

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "smoke_complete",
        "config": {
            "cache_npy": str(args.cache_npy),
            "cache_index": str(args.cache_index),
            "cache_shape": cache_shape,
            "label_policy": args.label_policy,
            "tasks": list(args.tasks),
            "models": list(args.models),
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
        "aggregate": aggregate_runs(runs),
        "runs": runs,
    }

    write_reports(report, args.out_md, args.out_json)
    print(f"[DONE] wrote {args.out_md}")
    print(f"[DONE] wrote {args.out_json}")


if __name__ == "__main__":
    main()
