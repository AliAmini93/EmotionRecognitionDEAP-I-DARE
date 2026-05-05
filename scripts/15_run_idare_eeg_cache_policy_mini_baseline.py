#!/usr/bin/env python3
"""
Run a cache-based I-DARE EEG-only score-5 policy mini-baseline.

Reads:
- .cache/idare_eeg_windows_32x640_float32.npy
- .cache/idare_eeg_cache_index.csv

Does NOT read I-DARE .mat/HDF5 files during training.

Goal:
- Replace the earlier HDF5-on-the-fly mini-baseline with a fast cache-based version.
- Compare three score-5 policies for valence and arousal:
  discard_midpoint, midpoint_as_low, midpoint_as_high.
- Use a subject-held-out validation split.
- Use class-weighted CrossEntropyLoss by default.
- Report accuracy, balanced accuracy, macro F1, confusion matrix, majority baseline, and runtime.

Important:
This is NOT full LOSO.
This is NOT a final experiment.
This script does not save model checkpoints.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from collections import defaultdict
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

OUT_MD = ROOT / "docs" / "idare_eeg_cache_policy_mini_baseline.md"
OUT_JSON = ROOT / "docs" / "idare_eeg_cache_policy_mini_baseline.json"

TASKS = ["valence", "arousal"]
POLICIES = ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]

DEFAULT_TRAIN_SUBJECTS = [5, 6, 7, 8, 9, 10, 11, 12]
DEFAULT_VAL_SUBJECTS = [1, 2, 3, 13]
DEFAULT_SEEDS = [11, 13]


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def label_column(task: str, policy: str) -> str:
    valid_tasks = {"valence", "arousal"}
    valid_policies = {"discard_midpoint", "midpoint_as_low", "midpoint_as_high"}

    if task not in valid_tasks:
        raise ValueError(f"Unknown task: {task}")
    if policy not in valid_policies:
        raise ValueError(f"Unknown policy: {policy}")

    return f"{task}_{policy}"


class IDARECachedEEGDataset(Dataset):
    def __init__(
        self,
        *,
        task: str,
        policy: str,
        subjects: list[int],
        cache_npy: Path = CACHE_NPY,
        cache_index: Path = CACHE_INDEX,
    ) -> None:
        self.task = task
        self.policy = policy
        self.cache_npy = Path(cache_npy)
        self.cache_index = Path(cache_index)

        if not self.cache_npy.exists():
            raise FileNotFoundError(f"Missing EEG cache: {self.cache_npy}")
        if not self.cache_index.exists():
            raise FileNotFoundError(f"Missing EEG cache index: {self.cache_index}")

        df = pd.read_csv(self.cache_index)
        col = label_column(task, policy)
        if col not in df.columns:
            raise KeyError(f"Missing label column {col}. Columns: {list(df.columns)}")

        df = df[df["subject_id"].astype(int).isin([int(s) for s in subjects])].copy()
        df = df[df[col].notna()].copy()
        df[col] = df[col].astype(int)
        df["cache_row"] = df["cache_row"].astype(int)
        df["subject_id"] = df["subject_id"].astype(int)
        df = df.sort_values(["subject_id", "cache_row"]).reset_index(drop=True)

        if df.empty:
            raise ValueError(f"Empty dataset for task={task}, policy={policy}, subjects={subjects}")

        self.df = df
        self.label_col = col
        self.x = np.load(self.cache_npy, mmap_mode="r")

    def __len__(self) -> int:
        return int(len(self.df))

    def __getitem__(self, idx: int) -> dict[str, Any]:
        row = self.df.iloc[int(idx)]
        cache_row = int(row["cache_row"])
        eeg = np.asarray(self.x[cache_row], dtype=np.float32)

        return {
            "eeg": torch.from_numpy(eeg.copy()),
            "label": torch.tensor(int(row[self.label_col]), dtype=torch.long),
            "subject_id": int(row["subject_id"]),
            "stimulus_id": str(row["stimulus_id"]),
            "cache_row": cache_row,
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


def class_weights_from_counts(label_counts: dict[int, int], *, device: torch.device) -> torch.Tensor:
    total = sum(label_counts.values())
    weights = []
    for label in [0, 1]:
        count = label_counts.get(label, 0)
        if count <= 0:
            weights.append(0.0)
        else:
            weights.append(total / (2.0 * count))
    return torch.tensor(weights, dtype=torch.float32, device=device)


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def binary_metrics_no_majority(y_true: list[int], y_pred: list[int]) -> dict[str, Any]:
    labels = [0, 1]
    recalls = []
    f1s = []

    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)

        precision = safe_div(tp, tp + fp)
        recall = safe_div(tp, tp + fn)
        f1 = safe_div(2 * precision * recall, precision + recall)

        recalls.append(recall)
        f1s.append(f1)

    total = len(y_true)
    correct = sum(int(t == p) for t, p in zip(y_true, y_pred))
    return {
        "accuracy": safe_div(correct, total),
        "balanced_accuracy": float(sum(recalls) / len(recalls)),
        "macro_f1": float(sum(f1s) / len(f1s)),
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
        f1 = safe_div(2 * precision * recall, precision + recall)

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
    majority_raw = {
        "label": int(majority_label),
        "accuracy": safe_div(true_counts[str(majority_label)], total),
        "balanced_accuracy": binary_metrics_no_majority(y_true, majority_pred)["balanced_accuracy"],
        "macro_f1": binary_metrics_no_majority(y_true, majority_pred)["macro_f1"],
    }

    return {
        "n": int(total),
        "accuracy": safe_div(correct, total),
        "balanced_accuracy": float(sum(recalls) / len(recalls)),
        "macro_f1": float(sum(f1s) / len(f1s)),
        "true_counts": true_counts,
        "pred_counts": pred_counts,
        "confusion": confusion,
        "per_class": per_class,
        "majority_baseline": majority_raw,
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


def run_one(
    *,
    task: str,
    policy: str,
    seed: int,
    train_subjects: list[int],
    val_subjects: list[int],
    device: torch.device,
    batch_size: int,
    epochs: int,
    use_class_weights: bool,
) -> dict[str, Any]:
    set_seed(seed)

    train_ds = IDARECachedEEGDataset(task=task, policy=policy, subjects=train_subjects)
    val_ds = IDARECachedEEGDataset(task=task, policy=policy, subjects=val_subjects)

    train_counts = {int(k): int(v) for k, v in train_ds.df[train_ds.label_col].value_counts().sort_index().to_dict().items()}
    val_counts = {int(k): int(v) for k, v in val_ds.df[val_ds.label_col].value_counts().sort_index().to_dict().items()}

    generator = torch.Generator()
    generator.manual_seed(seed)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
        generator=generator,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )

    model = make_model(device)

    if use_class_weights:
        weight = class_weights_from_counts(train_counts, device=device)
        criterion = torch.nn.CrossEntropyLoss(weight=weight)
    else:
        weight = None
        criterion = torch.nn.CrossEntropyLoss()

    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    history = []
    best = None

    run_start = time.perf_counter()

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_start = time.perf_counter()
        losses: list[float] = []
        y_true_train: list[int] = []
        y_pred_train: list[int] = []

        for batch_idx, batch in enumerate(train_loader, start=1):
            x = batch["eeg"].to(device=device, dtype=torch.float32)
            y = batch["label"].to(device=device, dtype=torch.long)

            optimizer.zero_grad(set_to_none=True)
            logits, _ = model(x, return_attn=False)
            loss = criterion(logits, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()

            pred = logits.argmax(dim=1)
            losses.append(float(loss.item()))
            y_true_train.extend(int(v) for v in y.detach().cpu().tolist())
            y_pred_train.extend(int(v) for v in pred.detach().cpu().tolist())

        train_metrics = binary_metrics(y_true_train, y_pred_train)
        val_metrics = eval_model(model, val_loader, device=device, criterion=criterion)

        epoch_info = {
            "epoch": int(epoch),
            "elapsed_sec": float(time.perf_counter() - epoch_start),
            "train_loss_mean": float(np.mean(losses)) if losses else math.nan,
            "train_accuracy": train_metrics["accuracy"],
            "train_balanced_accuracy": train_metrics["balanced_accuracy"],
            "train_macro_f1": train_metrics["macro_f1"],
            "val": val_metrics,
        }
        history.append(epoch_info)

        if best is None or val_metrics["macro_f1"] > best["val"]["macro_f1"]:
            best = epoch_info

        print(
            f"{task}/{policy}/seed{seed} epoch {epoch}/{epochs} "
            f"sec={epoch_info['elapsed_sec']:.2f} "
            f"train_f1={train_metrics['macro_f1']:.4f} "
            f"val_f1={val_metrics['macro_f1']:.4f} "
            f"val_bal={val_metrics['balanced_accuracy']:.4f}",
            flush=True,
        )

    final = history[-1]["val"]
    result = {
        "task": task,
        "policy": policy,
        "seed": int(seed),
        "train_subjects": train_subjects,
        "val_subjects": val_subjects,
        "train_rows": int(len(train_ds)),
        "val_rows": int(len(val_ds)),
        "train_label_counts": {str(k): int(v) for k, v in train_counts.items()},
        "val_label_counts": {str(k): int(v) for k, v in val_counts.items()},
        "class_weights": [float(v) for v in weight.detach().cpu().tolist()] if weight is not None else None,
        "model_trainable_parameters": int(sum(p.numel() for p in model.parameters() if p.requires_grad)),
        "elapsed_sec": float(time.perf_counter() - run_start),
        "history": history,
        "best_epoch_by_macro_f1": best,
        "final": final,
        "warnings": [],
    }

    pred_counts = final["pred_counts"]
    if pred_counts.get("0", 0) == 0 or pred_counts.get("1", 0) == 0:
        result["warnings"].append("Final epoch predicted only one class on the validation split.")
    if abs(final["balanced_accuracy"] - 0.5) <= 0.02:
        result["warnings"].append("Final balanced accuracy is near chance.")

    return result


def aggregate_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in results:
        grouped[(r["task"], r["policy"])].append(r)

    rows = []
    for (task, policy), items in sorted(grouped.items()):
        final_acc = [float(x["final"]["accuracy"]) for x in items]
        final_bal = [float(x["final"]["balanced_accuracy"]) for x in items]
        final_f1 = [float(x["final"]["macro_f1"]) for x in items]
        best_f1 = [float(x["best_epoch_by_macro_f1"]["val"]["macro_f1"]) for x in items]
        best_bal = [float(x["best_epoch_by_macro_f1"]["val"]["balanced_accuracy"]) for x in items]
        majority_acc = [float(x["final"]["majority_baseline"]["accuracy"]) for x in items]
        elapsed = [float(x["elapsed_sec"]) for x in items]

        rows.append(
            {
                "task": task,
                "policy": policy,
                "n_seeds": int(len(items)),
                "final_accuracy_mean": float(np.mean(final_acc)),
                "final_accuracy_std": float(np.std(final_acc)),
                "final_balanced_accuracy_mean": float(np.mean(final_bal)),
                "final_balanced_accuracy_std": float(np.std(final_bal)),
                "final_macro_f1_mean": float(np.mean(final_f1)),
                "final_macro_f1_std": float(np.std(final_f1)),
                "best_macro_f1_mean": float(np.mean(best_f1)),
                "best_macro_f1_std": float(np.std(best_f1)),
                "best_balanced_accuracy_mean": float(np.mean(best_bal)),
                "best_balanced_accuracy_std": float(np.std(best_bal)),
                "majority_accuracy_mean": float(np.mean(majority_acc)),
                "elapsed_sec_mean": float(np.mean(elapsed)),
            }
        )

    return rows


def write_report(payload: dict[str, Any]) -> None:
    lines = []
    lines.append("# I-DARE EEG Cache-Based Score-5 Policy Mini-Baseline\n")
    lines.append("This report was generated by `scripts/15_run_idare_eeg_cache_policy_mini_baseline.py`.\n")
    lines.append("\n")
    lines.append("**Important:** this is still not full LOSO and not a final experiment.\n")
    lines.append("No checkpoint was saved.\n")
    lines.append("\n")
    lines.append("## Status\n")
    lines.append(f"Status: **{payload['status']}**\n")
    lines.append("\n")
    lines.append("## Why This Exists\n")
    lines.append("- The earlier baseline attempt was too slow because it read MATLAB/HDF5 files during training.\n")
    lines.append("- This script trains from the EEG cache instead of raw `.mat` files.\n")
    lines.append("- The goal is to re-check the three score-5 policies quickly before deciding whether any should become the temporary main preset.\n")
    lines.append("\n")
    lines.append("## Configuration\n")
    lines.append("```json\n")
    lines.append(json.dumps(payload["config"], indent=2, ensure_ascii=False))
    lines.append("\n```\n")
    lines.append("\n")
    lines.append("## Aggregate Results\n")
    lines.append("| Task | Policy | Seeds | Acc mean | Bal acc mean | Macro F1 mean | Best F1 mean | Majority acc | Mean sec |\n")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|\n")
    for row in payload["aggregate"]:
        lines.append(
            f"| {row['task']} | {row['policy']} | {row['n_seeds']} | "
            f"{row['final_accuracy_mean']:.4f} | "
            f"{row['final_balanced_accuracy_mean']:.4f} | "
            f"{row['final_macro_f1_mean']:.4f} | "
            f"{row['best_macro_f1_mean']:.4f} | "
            f"{row['majority_accuracy_mean']:.4f} | "
            f"{row['elapsed_sec_mean']:.2f} |\n"
        )

    lines.append("\n")
    lines.append("## Run Details\n")
    for r in payload["results"]:
        lines.append(f"\n### {r['task']} / {r['policy']} / seed {r['seed']}\n")
        lines.append(f"- Train rows: `{r['train_rows']}`; validation rows: `{r['val_rows']}`\n")
        lines.append(f"- Train label counts: `{r['train_label_counts']}`\n")
        lines.append(f"- Validation label counts: `{r['val_label_counts']}`\n")
        lines.append(f"- Class weights: `{r['class_weights']}`\n")
        lines.append(f"- Elapsed seconds: `{r['elapsed_sec']:.2f}`\n")
        lines.append(
            f"- Final: acc `{r['final']['accuracy']:.4f}`, "
            f"balanced acc `{r['final']['balanced_accuracy']:.4f}`, "
            f"macro F1 `{r['final']['macro_f1']:.4f}`\n"
        )
        lines.append(
            f"- Best epoch by macro F1: epoch `{r['best_epoch_by_macro_f1']['epoch']}`, "
            f"balanced acc `{r['best_epoch_by_macro_f1']['val']['balanced_accuracy']:.4f}`, "
            f"macro F1 `{r['best_epoch_by_macro_f1']['val']['macro_f1']:.4f}`\n"
        )
        lines.append(f"- Final pred counts: `{r['final']['pred_counts']}`\n")
        lines.append(f"- Final confusion: `{r['final']['confusion']}`\n")
        if r["warnings"]:
            lines.append("- Warnings:\n")
            for w in r["warnings"]:
                lines.append(f"  - {w}\n")

    lines.append("\n")
    lines.append("## Global Issues\n")
    if payload["issues"]:
        for issue in payload["issues"]:
            lines.append(f"- {issue}\n")
    else:
        lines.append("- None.\n")

    lines.append("\n")
    lines.append("## Global Warnings\n")
    if payload["warnings"]:
        for warning in payload["warnings"]:
            lines.append(f"- {warning}\n")
    else:
        lines.append("- None.\n")

    lines.append("\n")
    lines.append("## Interpretation Rule\n")
    lines.append("- Prefer balanced accuracy and macro F1 over raw accuracy for policy comparison.\n")
    lines.append("- Compare against the majority baseline; raw accuracy below majority baseline is not automatically bad if balanced accuracy/F1 are better.\n")
    lines.append("- If no policy clearly improves balanced accuracy or macro F1, keep all three label presets but do not expand ablations yet.\n")
    lines.append("- If one policy is clearly better across both seeds and both tasks, promote it as the temporary main I-DARE binary preset.\n")

    OUT_MD.write_text("".join(lines), encoding="utf-8")
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_SEEDS)
    parser.add_argument("--train-subjects", type=int, nargs="+", default=DEFAULT_TRAIN_SUBJECTS)
    parser.add_argument("--val-subjects", type=int, nargs="+", default=DEFAULT_VAL_SUBJECTS)
    parser.add_argument("--no-class-weights", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not CACHE_NPY.exists() or not CACHE_INDEX.exists():
        print("Missing cache files. Run these first:", file=sys.stderr)
        print("python scripts/12_build_idare_eeg_cache.py --force", file=sys.stderr)
        print("python scripts/13_validate_idare_eeg_cache.py", file=sys.stderr)
        return 2

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    issues: list[str] = []
    warnings: list[str] = []

    config = {
        "tasks": TASKS,
        "policies": POLICIES,
        "seeds": args.seeds,
        "train_subjects": args.train_subjects,
        "val_subjects": args.val_subjects,
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "use_class_weights": not args.no_class_weights,
        "cache_npy": str(CACHE_NPY),
        "cache_index": str(CACHE_INDEX),
        "device": str(device),
        "torch_version": torch.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }

    started = time.perf_counter()
    results = []

    for task in TASKS:
        for policy in POLICIES:
            for seed in args.seeds:
                print(f"Running cache mini-baseline: task={task}, policy={policy}, seed={seed}", flush=True)
                try:
                    result = run_one(
                        task=task,
                        policy=policy,
                        seed=int(seed),
                        train_subjects=[int(s) for s in args.train_subjects],
                        val_subjects=[int(s) for s in args.val_subjects],
                        device=device,
                        batch_size=int(args.batch_size),
                        epochs=int(args.epochs),
                        use_class_weights=not args.no_class_weights,
                    )
                    results.append(result)
                    for w in result["warnings"]:
                        warnings.append(f"{task}/{policy}/seed{seed}: {w}")
                except Exception as exc:
                    issues.append(f"{task}/{policy}/seed{seed}: {exc!r}")

    aggregate = aggregate_results(results)

    payload = {
        "status": "PASSED" if not issues else "FAILED",
        "config": config,
        "elapsed_sec": float(time.perf_counter() - started),
        "aggregate": aggregate,
        "results": results,
        "issues": issues,
        "warnings": warnings,
    }

    write_report(payload)

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print(f"Status: {payload['status']}")
    print(f"Elapsed: {payload['elapsed_sec']:.2f}s")
    print(f"Issues: {len(issues)}")
    print(f"Warnings: {len(warnings)}")
    print()
    print("Aggregate:")
    for row in aggregate:
        print(
            f"{row['task']}/{row['policy']}: "
            f"acc={row['final_accuracy_mean']:.4f} "
            f"bal_acc={row['final_balanced_accuracy_mean']:.4f} "
            f"macro_f1={row['final_macro_f1_mean']:.4f} "
            f"best_f1={row['best_macro_f1_mean']:.4f} "
            f"maj_acc={row['majority_accuracy_mean']:.4f} "
            f"sec={row['elapsed_sec_mean']:.2f}",
            flush=True,
        )

    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
