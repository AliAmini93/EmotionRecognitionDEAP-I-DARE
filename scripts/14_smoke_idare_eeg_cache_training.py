#!/usr/bin/env python3
"""
Smoke-test cache-based I-DARE EEG training.

This script reads:
- .cache/idare_eeg_windows_32x640_float32.npy
- .cache/idare_eeg_cache_index.csv

It does NOT read I-DARE .mat/HDF5 files during training.
It runs only one small task/policy/seed to verify that cache-based training is fast and does not hang.
"""

from __future__ import annotations

import json
import math
import random
import sys
import time
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

OUT_MD = ROOT / "docs" / "idare_eeg_cache_training_smoke_test.md"
OUT_JSON = ROOT / "docs" / "idare_eeg_cache_training_smoke_test.json"

TASK = "valence"
POLICY = "discard_midpoint"
SEED = 11
TRAIN_SUBJECTS = [5, 6, 7, 8, 9, 10, 11, 12]
VAL_SUBJECTS = [1, 2, 3, 13]
EPOCHS = 3
BATCH_SIZE = 16


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def label_column(task: str, policy: str) -> str:
    """Return the label column name used by .cache/idare_eeg_cache_index.csv."""
    valid_tasks = {"valence", "arousal"}
    valid_policies = {"discard_midpoint", "midpoint_as_low", "midpoint_as_high"}

    if task not in valid_tasks:
        raise ValueError(f"Unknown task: {task}")
    if policy not in valid_policies:
        raise ValueError(f"Unknown policy: {policy}")

    return f"{task}_{policy}"


class IDARECachedEEGDataset(Dataset):
    def __init__(self, *, task: str, policy: str, subjects: list[int]) -> None:
        if not CACHE_NPY.exists():
            raise FileNotFoundError(CACHE_NPY)
        if not CACHE_INDEX.exists():
            raise FileNotFoundError(CACHE_INDEX)

        self.x = np.load(CACHE_NPY, mmap_mode="r")
        df = pd.read_csv(CACHE_INDEX)

        col = label_column(task, policy)
        if col not in df.columns:
            raise KeyError(f"Missing label column {col}. Columns: {list(df.columns)}")

        df = df[df["subject_id"].isin(subjects)].copy()
        df = df[~df[col].isna()].copy()
        df["label"] = df[col].astype(int)

        if len(df) == 0:
            raise RuntimeError("Empty dataset after filtering.")

        self.df = df.reset_index(drop=True)
        self.cache_rows = self.df["cache_row"].astype(int).to_numpy()
        self.labels = self.df["label"].astype(int).to_numpy()

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        row = int(self.cache_rows[idx])
        eeg = np.asarray(self.x[row], dtype=np.float32)
        label = int(self.labels[idx])
        return {
            "eeg": torch.from_numpy(eeg.copy()),
            "label": torch.tensor(label, dtype=torch.long),
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


def class_weights(ds: IDARECachedEEGDataset, device: torch.device) -> torch.Tensor:
    counts = ds.df["label"].value_counts().sort_index().to_dict()
    total = sum(counts.values())
    weights = []
    for label in [0, 1]:
        count = int(counts.get(label, 0))
        weights.append(total / (2.0 * count) if count else 0.0)
    return torch.tensor(weights, dtype=torch.float32, device=device)


def metrics(y_true: list[int], y_pred: list[int]) -> dict[str, Any]:
    total = len(y_true)
    correct = sum(int(a == b) for a, b in zip(y_true, y_pred))

    recalls = []
    f1s = []
    for label in [0, 1]:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

        recalls.append(recall)
        f1s.append(f1)

    return {
        "accuracy": correct / total if total else math.nan,
        "balanced_accuracy": float(sum(recalls) / 2),
        "macro_f1": float(sum(f1s) / 2),
        "true_counts": {str(k): int(v) for k, v in pd.Series(y_true).value_counts().sort_index().to_dict().items()},
        "pred_counts": {str(k): int(v) for k, v in pd.Series(y_pred).value_counts().sort_index().to_dict().items()},
    }


def evaluate(model: torch.nn.Module, loader: DataLoader, criterion: torch.nn.Module, device: torch.device) -> dict[str, Any]:
    model.eval()
    losses = []
    y_true = []
    y_pred = []

    with torch.no_grad():
        for batch in loader:
            x = batch["eeg"].to(device=device, dtype=torch.float32)
            y = batch["label"].to(device=device, dtype=torch.long)

            logits, _ = model(x, return_attn=False)
            loss = criterion(logits, y)

            losses.append(float(loss.item()))
            y_true.extend(int(v) for v in y.detach().cpu().tolist())
            y_pred.extend(int(v) for v in logits.argmax(dim=1).detach().cpu().tolist())

    out = metrics(y_true, y_pred)
    out["loss_mean"] = float(np.mean(losses)) if losses else math.nan
    out["batches"] = int(len(losses))
    return out


def main() -> None:
    set_seed(SEED)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_ds = IDARECachedEEGDataset(task=TASK, policy=POLICY, subjects=TRAIN_SUBJECTS)
    val_ds = IDARECachedEEGDataset(task=TASK, policy=POLICY, subjects=VAL_SUBJECTS)

    train_loader = DataLoader(
        train_ds,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )

    model = make_model(device)
    criterion = torch.nn.CrossEntropyLoss(weight=class_weights(train_ds, device))
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    started = time.perf_counter()
    history = []

    for epoch in range(1, EPOCHS + 1):
        epoch_start = time.perf_counter()
        model.train()

        train_losses = []
        train_true = []
        train_pred = []

        for batch_idx, batch in enumerate(train_loader, start=1):
            x = batch["eeg"].to(device=device, dtype=torch.float32)
            y = batch["label"].to(device=device, dtype=torch.long)

            optimizer.zero_grad(set_to_none=True)
            logits, _ = model(x, return_attn=False)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            train_losses.append(float(loss.item()))
            train_true.extend(int(v) for v in y.detach().cpu().tolist())
            train_pred.extend(int(v) for v in logits.argmax(dim=1).detach().cpu().tolist())

            if batch_idx == 1 or batch_idx == len(train_loader):
                print(f"epoch {epoch}/{EPOCHS} batch {batch_idx}/{len(train_loader)} loss={loss.item():.4f}", flush=True)

        train_metrics = metrics(train_true, train_pred)
        train_metrics["loss_mean"] = float(np.mean(train_losses))
        val_metrics = evaluate(model, val_loader, criterion, device)

        elapsed_epoch = time.perf_counter() - epoch_start
        row = {
            "epoch": epoch,
            "elapsed_sec": elapsed_epoch,
            "train": train_metrics,
            "val": val_metrics,
        }
        history.append(row)

        print(
            f"epoch {epoch} done in {elapsed_epoch:.2f}s | "
            f"train_f1={train_metrics['macro_f1']:.4f} | "
            f"val_f1={val_metrics['macro_f1']:.4f} | "
            f"val_bal_acc={val_metrics['balanced_accuracy']:.4f}",
            flush=True,
        )

    elapsed = time.perf_counter() - started

    payload = {
        "status": "PASSED",
        "task": TASK,
        "policy": POLICY,
        "seed": SEED,
        "device": str(device),
        "cache_npy": str(CACHE_NPY),
        "cache_index": str(CACHE_INDEX),
        "train_subjects": TRAIN_SUBJECTS,
        "val_subjects": VAL_SUBJECTS,
        "train_rows": len(train_ds),
        "val_rows": len(val_ds),
        "batch_size": BATCH_SIZE,
        "epochs": EPOCHS,
        "elapsed_sec": elapsed,
        "history": history,
        "issues": [],
        "warnings": [],
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = []
    lines.append("# I-DARE EEG Cache Training Smoke Test\n")
    lines.append("This report was generated by `scripts/14_smoke_idare_eeg_cache_training.py`.\n")
    lines.append("No full baseline was run and no checkpoint was saved.\n")
    lines.append("## Status\n")
    lines.append("Status: **PASSED**\n")
    lines.append("## Configuration\n")
    lines.append("```json\n")
    lines.append(json.dumps({k: payload[k] for k in [
        "task", "policy", "seed", "device", "train_subjects", "val_subjects",
        "train_rows", "val_rows", "batch_size", "epochs", "elapsed_sec"
    ]}, indent=2))
    lines.append("\n```\n")
    lines.append("## Epoch History\n")
    lines.append("| Epoch | sec | Train macro F1 | Val macro F1 | Val bal acc | Val acc |\n")
    lines.append("|---:|---:|---:|---:|---:|---:|\n")
    for row in history:
        lines.append(
            f"| {row['epoch']} | {row['elapsed_sec']:.2f} | "
            f"{row['train']['macro_f1']:.4f} | "
            f"{row['val']['macro_f1']:.4f} | "
            f"{row['val']['balanced_accuracy']:.4f} | "
            f"{row['val']['accuracy']:.4f} |\n"
        )
    lines.append("\n## Final Validation Metrics\n")
    lines.append("```json\n")
    lines.append(json.dumps(history[-1]["val"], indent=2))
    lines.append("\n```\n")
    OUT_MD.write_text("".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print(f"Status: PASSED")
    print(f"Elapsed: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
