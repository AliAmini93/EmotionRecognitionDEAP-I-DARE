#!/usr/bin/env python3
"""
Run focused cache-based I-DARE EEG baseline.

Purpose:
- Use the validated EEG cache, not raw MATLAB/HDF5 files.
- Compare the two remaining score-5 policies:
  - midpoint_as_low
  - midpoint_as_high
- Run both valence and arousal.
- Use subject-held-out folds over all cached subjects.
- Keep this as a short baseline, not full LOSO and not a final experiment.

Inputs:
- .cache/idare_eeg_windows_32x640_float32.npy
- .cache/idare_eeg_cache_index.csv

Outputs:
- docs/idare_eeg_cache_main_baseline.md
- docs/idare_eeg_cache_main_baseline.json

No checkpoint is saved by default.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from dataclasses import dataclass
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

CACHE_NPY = ROOT / ".cache" / "idare_eeg_windows_32x640_float32.npy"
CACHE_INDEX = ROOT / ".cache" / "idare_eeg_cache_index.csv"

OUT_MD = ROOT / "docs" / "idare_eeg_cache_main_baseline.md"
OUT_JSON = ROOT / "docs" / "idare_eeg_cache_main_baseline.json"

DEFAULT_TASKS = ["valence", "arousal"]
DEFAULT_POLICIES = ["midpoint_as_high"]
DEFAULT_SEEDS = [11, 13]
VALID_TASKS = {"valence", "arousal"}
VALID_POLICIES = {"discard_midpoint", "midpoint_as_low", "midpoint_as_high"}


@dataclass(frozen=True)
class Fold:
    fold_id: int
    val_subjects: list[int]
    train_subjects: list[int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", nargs="+", default=DEFAULT_TASKS, choices=sorted(VALID_TASKS))
    parser.add_argument("--policies", nargs="+", default=DEFAULT_POLICIES, choices=sorted(VALID_POLICIES))
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--folds", type=int, default=6)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--no-class-weights", action="store_true")
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--max-runs", type=int, default=0, help="Optional cap for debugging; 0 means run all.")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


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


def label_column(task: str, policy: str) -> str:
    if task not in VALID_TASKS:
        raise ValueError(f"Unknown task: {task}")
    if policy not in VALID_POLICIES:
        raise ValueError(f"Unknown policy: {policy}")
    return f"{task}_{policy}"


def safe_float(v: Any) -> float | None:
    if pd.isna(v):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def binary_metrics_no_majority(y_true: list[int], y_pred: list[int]) -> dict[str, Any]:
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

    per_class: dict[str, Any] = {}
    recalls: list[float] = []
    f1s: list[float] = []

    confusion = {
        "tn": sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0),
        "fp": sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1),
        "fn": sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0),
        "tp": sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1),
    }

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

    true_counts = {str(label): int(sum(1 for t in y_true if t == label)) for label in labels}
    pred_counts = {str(label): int(sum(1 for p in y_pred if p == label)) for label in labels}

    majority_label = max(labels, key=lambda label: true_counts[str(label)])
    majority_pred = [majority_label for _ in y_true]
    majority_metrics = binary_metrics_no_majority(y_true, majority_pred)

    return {
        "n": int(total),
        "accuracy": safe_div(correct, total),
        "balanced_accuracy": float(sum(recalls) / len(recalls)) if recalls else math.nan,
        "macro_f1": float(sum(f1s) / len(f1s)) if f1s else math.nan,
        "true_counts": true_counts,
        "pred_counts": pred_counts,
        "confusion": confusion,
        "per_class": per_class,
        "majority_baseline": {
            "label": int(majority_label),
            **majority_metrics,
        },
    }


def summarize_metric(values: list[float]) -> dict[str, float]:
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
    def __init__(self, *, task: str, policy: str, subjects: list[int]) -> None:
        if not CACHE_NPY.exists():
            raise FileNotFoundError(f"Missing EEG cache: {CACHE_NPY}")
        if not CACHE_INDEX.exists():
            raise FileNotFoundError(f"Missing EEG cache index: {CACHE_INDEX}")

        col = label_column(task, policy)
        df = pd.read_csv(CACHE_INDEX)
        if col not in df.columns:
            raise KeyError(f"Missing label column {col}. Columns: {list(df.columns)}")
        if "cache_row" not in df.columns:
            raise KeyError("Missing cache_row column in cache index")

        df = df[df["subject_id"].astype(int).isin([int(s) for s in subjects])].copy()
        df[col] = df[col].map(safe_float)
        df = df[df[col].isin([0.0, 1.0])].copy()
        df["label"] = df[col].astype(int)
        df = df.sort_values(["subject_id", "cache_row"]).reset_index(drop=True)

        self.task = task
        self.policy = policy
        self.subjects = [int(s) for s in subjects]
        self.label_col = col
        self.df = df
        self.cache = np.load(CACHE_NPY, mmap_mode="r")

        if len(self.df) == 0:
            raise ValueError(f"No rows for task={task}, policy={policy}, subjects={subjects}")

    def __len__(self) -> int:
        return int(len(self.df))

    def __getitem__(self, index: int) -> dict[str, Any]:
        row = self.df.iloc[index]
        cache_row = int(row["cache_row"])
        eeg = np.asarray(self.cache[cache_row], dtype=np.float32)
        return {
            "eeg": torch.from_numpy(eeg),
            "label": torch.tensor(int(row["label"]), dtype=torch.long),
            "cache_row": cache_row,
            "subject_id": int(row["subject_id"]),
            "stimulus_id": str(row["stimulus_id"]),
        }


def class_weights_from_counts(label_counts: dict[int, int], *, device: torch.device) -> torch.Tensor:
    total = sum(label_counts.values())
    weights = []
    for label in [0, 1]:
        count = label_counts.get(label, 0)
        weights.append(total / (2.0 * count) if count > 0 else 0.0)
    return torch.tensor(weights, dtype=torch.float32, device=device)


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
    losses: list[float] = []

    with torch.no_grad():
        for batch in loader:
            x = batch["eeg"].to(device=device, dtype=torch.float32)
            y = batch["label"].to(device=device, dtype=torch.long)

            logits, _ = model(x, return_attn=False)
            loss = criterion(logits, y)
            pred = logits.argmax(dim=1)

            losses.append(float(loss.item()))
            y_true.extend(int(v) for v in y.detach().cpu().tolist())
            y_pred.extend(int(v) for v in pred.detach().cpu().tolist())

    metrics = binary_metrics(y_true, y_pred)
    metrics["loss_mean"] = float(np.mean(losses)) if losses else math.nan
    metrics["batches"] = int(len(losses))
    return metrics


def train_one(
    *,
    task: str,
    policy: str,
    fold: Fold,
    seed: int,
    device: torch.device,
    batch_size: int,
    epochs: int,
    lr: float,
    weight_decay: float,
    grad_clip: float,
    num_workers: int,
    use_class_weights: bool,
) -> dict[str, Any]:
    set_seed(seed)

    train_ds = IDARECachedEEGDataset(task=task, policy=policy, subjects=fold.train_subjects)
    val_ds = IDARECachedEEGDataset(task=task, policy=policy, subjects=fold.val_subjects)

    train_counts = {
        int(k): int(v)
        for k, v in train_ds.df["label"].value_counts().sort_index().to_dict().items()
    }
    val_counts = {
        int(k): int(v)
        for k, v in val_ds.df["label"].value_counts().sort_index().to_dict().items()
    }

    generator = torch.Generator()
    generator.manual_seed(seed)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=(device.type == "cuda"),
        generator=generator,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=(device.type == "cuda"),
    )

    model = make_model(device)

    if use_class_weights:
        weights = class_weights_from_counts(train_counts, device=device)
        criterion = torch.nn.CrossEntropyLoss(weight=weights)
        class_weights = [float(v) for v in weights.detach().cpu().tolist()]
    else:
        criterion = torch.nn.CrossEntropyLoss()
        class_weights = None

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    epoch_history: list[dict[str, Any]] = []
    best_eval: dict[str, Any] | None = None
    start = time.perf_counter()

    for epoch in range(1, epochs + 1):
        epoch_start = time.perf_counter()
        model.train()

        y_true: list[int] = []
        y_pred: list[int] = []
        losses: list[float] = []

        for batch_idx, batch in enumerate(train_loader, start=1):
            x = batch["eeg"].to(device=device, dtype=torch.float32)
            y = batch["label"].to(device=device, dtype=torch.long)

            optimizer.zero_grad(set_to_none=True)
            logits, _ = model(x, return_attn=False)
            loss = criterion(logits, y)
            loss.backward()

            if grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=grad_clip)

            optimizer.step()

            pred = logits.argmax(dim=1)
            losses.append(float(loss.item()))
            y_true.extend(int(v) for v in y.detach().cpu().tolist())
            y_pred.extend(int(v) for v in pred.detach().cpu().tolist())

        train_metrics = binary_metrics(y_true, y_pred)
        val_metrics = eval_model(model, val_loader, device=device, criterion=criterion)

        epoch_record = {
            "epoch": epoch,
            "elapsed_sec": float(time.perf_counter() - epoch_start),
            "train_loss_mean": float(np.mean(losses)) if losses else math.nan,
            "train_accuracy": train_metrics["accuracy"],
            "train_balanced_accuracy": train_metrics["balanced_accuracy"],
            "train_macro_f1": train_metrics["macro_f1"],
            "val_loss_mean": val_metrics["loss_mean"],
            "val_accuracy": val_metrics["accuracy"],
            "val_balanced_accuracy": val_metrics["balanced_accuracy"],
            "val_macro_f1": val_metrics["macro_f1"],
            "val_pred_counts": val_metrics["pred_counts"],
            "val_confusion": val_metrics["confusion"],
        }
        epoch_history.append(epoch_record)

        if best_eval is None or val_metrics["macro_f1"] > best_eval["macro_f1"]:
            best_eval = {
                "epoch": epoch,
                "accuracy": val_metrics["accuracy"],
                "balanced_accuracy": val_metrics["balanced_accuracy"],
                "macro_f1": val_metrics["macro_f1"],
                "pred_counts": val_metrics["pred_counts"],
                "confusion": val_metrics["confusion"],
                "loss_mean": val_metrics["loss_mean"],
            }

        print(
            f"{task}/{policy}/fold{fold.fold_id}/seed{seed} "
            f"epoch {epoch}/{epochs} "
            f"sec={epoch_record['elapsed_sec']:.2f} "
            f"train_f1={epoch_record['train_macro_f1']:.4f} "
            f"val_f1={epoch_record['val_macro_f1']:.4f} "
            f"val_bal={epoch_record['val_balanced_accuracy']:.4f}",
            flush=True,
        )

    final_eval = eval_model(model, val_loader, device=device, criterion=criterion)
    elapsed = float(time.perf_counter() - start)

    warnings: list[str] = []
    if 0 in final_eval["pred_counts"].values():
        warnings.append("Final epoch predicted only one class on the validation split.")
    if abs(final_eval["balanced_accuracy"] - 0.5) <= 0.02:
        warnings.append("Final balanced accuracy is near chance.")
    if final_eval["macro_f1"] <= final_eval["majority_baseline"]["macro_f1"]:
        warnings.append("Final macro F1 does not beat majority-class baseline macro F1.")

    return {
        "task": task,
        "policy": policy,
        "fold_id": fold.fold_id,
        "seed": seed,
        "train_subjects": fold.train_subjects,
        "val_subjects": fold.val_subjects,
        "train_rows": int(len(train_ds)),
        "val_rows": int(len(val_ds)),
        "train_label_counts": {str(k): int(v) for k, v in train_counts.items()},
        "val_label_counts": {str(k): int(v) for k, v in val_counts.items()},
        "class_weights": class_weights,
        "elapsed_sec": elapsed,
        "epoch_history": epoch_history,
        "final_eval": final_eval,
        "best_eval": best_eval,
        "warnings": warnings,
    }


def make_subject_folds(subjects: list[int], *, n_folds: int) -> list[Fold]:
    if n_folds < 2:
        raise ValueError("n_folds must be >= 2")
    subjects = sorted(int(s) for s in subjects)
    chunks = [list(map(int, chunk.tolist())) for chunk in np.array_split(np.asarray(subjects), n_folds)]
    folds: list[Fold] = []
    for idx, val_subjects in enumerate(chunks, start=1):
        val_set = set(val_subjects)
        train_subjects = [s for s in subjects if s not in val_set]
        folds.append(Fold(fold_id=idx, val_subjects=val_subjects, train_subjects=train_subjects))
    return folds


def aggregate_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in results:
        grouped.setdefault((row["task"], row["policy"]), []).append(row)

    out: list[dict[str, Any]] = []
    for (task, policy), rows in grouped.items():
        out.append(
            {
                "task": task,
                "policy": policy,
                "runs": len(rows),
                "final_accuracy": summarize_metric([r["final_eval"]["accuracy"] for r in rows]),
                "final_balanced_accuracy": summarize_metric([r["final_eval"]["balanced_accuracy"] for r in rows]),
                "final_macro_f1": summarize_metric([r["final_eval"]["macro_f1"] for r in rows]),
                "best_macro_f1": summarize_metric([r["best_eval"]["macro_f1"] for r in rows if r["best_eval"]]),
                "majority_accuracy": summarize_metric(
                    [r["final_eval"]["majority_baseline"]["accuracy"] for r in rows]
                ),
                "majority_macro_f1": summarize_metric(
                    [r["final_eval"]["majority_baseline"]["macro_f1"] for r in rows]
                ),
                "one_class_final_runs": int(
                    sum(1 for r in rows if 0 in r["final_eval"]["pred_counts"].values())
                ),
                "near_chance_bal_acc_runs": int(
                    sum(1 for r in rows if abs(r["final_eval"]["balanced_accuracy"] - 0.5) <= 0.02)
                ),
                "elapsed_sec": summarize_metric([r["elapsed_sec"] for r in rows]),
            }
        )

    out.sort(
        key=lambda r: (
            r["task"],
            -r["final_macro_f1"]["mean"],
            -r["final_balanced_accuracy"]["mean"],
            r["one_class_final_runs"],
        )
    )
    return out


def make_recommendations(aggregate: list[dict[str, Any]]) -> dict[str, Any]:
    recommendations: dict[str, Any] = {}

    for task in sorted({row["task"] for row in aggregate}):
        rows = [row for row in aggregate if row["task"] == task]
        rows = sorted(
            rows,
            key=lambda r: (
                r["final_macro_f1"]["mean"],
                r["final_balanced_accuracy"]["mean"],
                -r["one_class_final_runs"],
            ),
            reverse=True,
        )

        top = rows[0]
        second = rows[1] if len(rows) > 1 else None
        margin_f1 = (
            top["final_macro_f1"]["mean"] - second["final_macro_f1"]["mean"]
            if second is not None
            else math.nan
        )
        margin_bal = (
            top["final_balanced_accuracy"]["mean"] - second["final_balanced_accuracy"]["mean"]
            if second is not None
            else math.nan
        )
        clear = (
            second is not None
            and margin_f1 >= 0.03
            and margin_bal >= -0.02
            and top["one_class_final_runs"] <= second["one_class_final_runs"]
        )

        recommendations[task] = {
            "top_policy": top["policy"],
            "second_policy": second["policy"] if second is not None else None,
            "margin_final_macro_f1_vs_second": margin_f1,
            "margin_final_balanced_accuracy_vs_second": margin_bal,
            "top_one_class_final_runs": top["one_class_final_runs"],
            "is_clear_temporary_winner": bool(clear),
            "recommendation": (
                f"Promote {top['policy']} as the temporary task-specific policy."
                if clear
                else "This run evaluates the temporary main policy; do not treat it as a final LOSO result."
            ),
        }

    return recommendations


def write_reports(payload: dict[str, Any]) -> None:
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    lines: list[str] = []
    lines.append("# I-DARE EEG Cache-Based Main Baseline\n")
    lines.append("This report was generated by `scripts/18_run_idare_eeg_cache_main_baseline.py`.\n\n")
    lines.append("**Important:** this is still not full LOSO and not a final experiment.\n")
    lines.append("No checkpoint was saved.\n\n")

    lines.append("## Status\n\n")
    lines.append(f"Status: **{payload['status']}**\n\n")

    lines.append("## Why This Exists\n\n")
    lines.append("- The raw HDF5 training path was too slow.\n")
    lines.append("- The cache-based path is fast and validated.\n")
    lines.append("- The previous focused policy baseline selected a temporary main score-5 policy.\n")
    lines.append("- This main baseline evaluates the temporary main score-5 policy: `midpoint_as_high` for both valence and arousal.\n\n")

    lines.append("## Configuration\n\n")
    lines.append("```json\n")
    lines.append(json.dumps(payload["config"], indent=2, ensure_ascii=False, default=str))
    lines.append("\n```\n\n")

    lines.append("## Aggregate Results\n\n")
    lines.append(
        "| Task | Policy | Runs | Final macro F1 mean | Final bal acc mean | Best F1 mean | "
        "One-class final runs | Majority macro F1 | Mean sec |\n"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|\n")
    for row in payload["aggregate"]:
        lines.append(
            f"| {row['task']} | {row['policy']} | {row['runs']} | "
            f"{row['final_macro_f1']['mean']:.4f} | "
            f"{row['final_balanced_accuracy']['mean']:.4f} | "
            f"{row['best_macro_f1']['mean']:.4f} | "
            f"{row['one_class_final_runs']} | "
            f"{row['majority_macro_f1']['mean']:.4f} | "
            f"{row['elapsed_sec']['mean']:.2f} |\n"
        )
    lines.append("\n")

    lines.append("## Recommendations\n\n")
    lines.append("```json\n")
    lines.append(json.dumps(payload["recommendations"], indent=2, ensure_ascii=False, default=str))
    lines.append("\n```\n\n")

    lines.append("## Fold Definitions\n\n")
    for fold in payload["config"]["folds"]:
        lines.append(
            f"- Fold {fold['fold_id']}: validation subjects `{fold['val_subjects']}`, "
            f"train subjects count `{len(fold['train_subjects'])}`\n"
        )
    lines.append("\n")

    lines.append("## Run Details\n\n")
    for row in payload["runs"]:
        lines.append(f"### {row['task']} / {row['policy']} / fold {row['fold_id']} / seed {row['seed']}\n")
        lines.append(f"- Train rows: `{row['train_rows']}`; validation rows: `{row['val_rows']}`\n")
        lines.append(f"- Train label counts: `{row['train_label_counts']}`\n")
        lines.append(f"- Validation label counts: `{row['val_label_counts']}`\n")
        lines.append(f"- Elapsed seconds: `{row['elapsed_sec']:.2f}`\n")
        final_eval = row["final_eval"]
        best_eval = row["best_eval"]
        lines.append(
            f"- Final: acc `{final_eval['accuracy']:.4f}`, "
            f"balanced acc `{final_eval['balanced_accuracy']:.4f}`, "
            f"macro F1 `{final_eval['macro_f1']:.4f}`\n"
        )
        lines.append(
            f"- Best epoch by macro F1: epoch `{best_eval['epoch']}`, "
            f"balanced acc `{best_eval['balanced_accuracy']:.4f}`, "
            f"macro F1 `{best_eval['macro_f1']:.4f}`\n"
        )
        lines.append(f"- Final pred counts: `{final_eval['pred_counts']}`\n")
        lines.append(f"- Final confusion: `{final_eval['confusion']}`\n")
        if row["warnings"]:
            lines.append("- Warnings:\n")
            for warning in row["warnings"]:
                lines.append(f"  - {warning}\n")
        lines.append("\n")

    lines.append("## Global Issues\n\n")
    if payload["issues"]:
        for issue in payload["issues"]:
            lines.append(f"- {issue}\n")
    else:
        lines.append("- None.\n")
    lines.append("\n")

    lines.append("## Global Warnings\n\n")
    if payload["warnings"]:
        for warning in payload["warnings"]:
            lines.append(f"- {warning}\n")
    else:
        lines.append("- None.\n")
    lines.append("\n")

    lines.append("## Interpretation Rule\n\n")
    lines.append("- Prefer macro F1 and balanced accuracy over raw accuracy.\n")
    lines.append("- Check one-class collapse before trusting a policy.\n")
    lines.append("- If a policy is consistently better across both tasks, it can become the temporary primary policy.\n")
    lines.append("- If results remain near chance, do not expand model complexity yet; inspect splits, labels, and normalization first.\n")

    OUT_MD.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    start = time.perf_counter()

    issues: list[str] = []
    warnings: list[str] = []

    if not CACHE_NPY.exists():
        issues.append(f"Missing cache NPY: {CACHE_NPY}")
    if not CACHE_INDEX.exists():
        issues.append(f"Missing cache index: {CACHE_INDEX}")
    if issues:
        payload = {
            "status": "FAILED",
            "issues": issues,
            "warnings": warnings,
            "config": vars(args),
            "runs": [],
            "aggregate": [],
            "recommendations": {},
            "elapsed_sec": 0.0,
        }
        write_reports(payload)
        print(f"Status: {payload['status']}")
        for issue in issues:
            print(f"Issue: {issue}")
        raise SystemExit(1)

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True

    cache_index = pd.read_csv(CACHE_INDEX)
    subjects = sorted(int(s) for s in cache_index["subject_id"].dropna().unique().tolist())
    folds = make_subject_folds(subjects, n_folds=args.folds)

    config = {
        "tasks": args.tasks,
        "policies": args.policies,
        "seeds": args.seeds,
        "fold_count": args.folds,
        "folds": [
            {
                "fold_id": fold.fold_id,
                "val_subjects": fold.val_subjects,
                "train_subjects": fold.train_subjects,
            }
            for fold in folds
        ],
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "use_class_weights": not args.no_class_weights,
        "lr": args.lr,
        "weight_decay": args.weight_decay,
        "grad_clip": args.grad_clip,
        "num_workers": args.num_workers,
        "cache_npy": str(CACHE_NPY),
        "cache_index": str(CACHE_INDEX),
        "device": str(device),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "max_runs": args.max_runs,
    }

    results: list[dict[str, Any]] = []
    run_count = 0

    for task in args.tasks:
        for policy in args.policies:
            for fold in folds:
                for seed in args.seeds:
                    run_count += 1
                    if args.max_runs and run_count > args.max_runs:
                        break
                    print(
                        f"Running main baseline: task={task}, policy={policy}, fold={fold.fold_id}, seed={seed}",
                        flush=True,
                    )
                    result = train_one(
                        task=task,
                        policy=policy,
                        fold=fold,
                        seed=seed,
                        device=device,
                        batch_size=args.batch_size,
                        epochs=args.epochs,
                        lr=args.lr,
                        weight_decay=args.weight_decay,
                        grad_clip=args.grad_clip,
                        num_workers=args.num_workers,
                        use_class_weights=not args.no_class_weights,
                    )
                    results.append(result)

                    for warning in result["warnings"]:
                        warnings.append(
                            f"{task}/{policy}/fold{fold.fold_id}/seed{seed}: {warning}"
                        )
                if args.max_runs and run_count >= args.max_runs:
                    break
            if args.max_runs and run_count >= args.max_runs:
                break
        if args.max_runs and run_count >= args.max_runs:
            break

    aggregate = aggregate_results(results)
    recommendations = make_recommendations(aggregate)

    status = "PASSED" if not issues else "FAILED"
    payload = {
        "status": status,
        "config": config,
        "runs": results,
        "aggregate": aggregate,
        "recommendations": recommendations,
        "issues": issues,
        "warnings": warnings,
        "elapsed_sec": float(time.perf_counter() - start),
    }

    write_reports(payload)

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print(f"Status: {status}")
    print(f"Elapsed: {payload['elapsed_sec']:.2f}s")
    print(f"Issues: {len(issues)}")
    print(f"Warnings: {len(warnings)}")

    print("\nRecommendations:")
    print(json.dumps(recommendations, indent=2, ensure_ascii=False, default=str))

    print("\nAggregate:")
    for row in aggregate:
        print(
            f"{row['task']}/{row['policy']}: "
            f"macro_f1={row['final_macro_f1']['mean']:.4f} "
            f"bal_acc={row['final_balanced_accuracy']['mean']:.4f} "
            f"best_f1={row['best_macro_f1']['mean']:.4f} "
            f"one_class={row['one_class_final_runs']}/{row['runs']} "
            f"sec={row['elapsed_sec']['mean']:.2f}",
            flush=True,
        )

    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
