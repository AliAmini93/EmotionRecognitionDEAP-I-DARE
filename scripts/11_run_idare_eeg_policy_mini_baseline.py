#!/usr/bin/env python3
"""
Run a small I-DARE EEG-only score-5 policy mini-baseline.

Goal:
- Go beyond the one-batch/tiny policy pilot.
- Compare three score-5 policies with a subject-held-out validation split.
- Use class-weighted CrossEntropyLoss by default to reduce majority-class collapse.
- Report accuracy, balanced accuracy, macro F1, confusion matrix, and majority baseline.

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
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from emotion_deap_idare.datasets.idare_loader import IDARETrialDataset  # noqa: E402
from emotion_deap_idare.models.eeg_segment_classifier import EEGSegmentClassifier  # noqa: E402


OUT_MD = ROOT / "docs" / "idare_eeg_policy_mini_baseline.md"
OUT_JSON = ROOT / "docs" / "idare_eeg_policy_mini_baseline.json"

TASKS = ["valence", "arousal"]
POLICIES = ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]


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
    majority_correct = true_counts[str(majority_label)]
    majority_pred = [majority_label for _ in y_true]
    majority_raw = {
        "label": int(majority_label),
        "accuracy": safe_div(majority_correct, total),
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

    train_ds = IDARETrialDataset(
        task=task,
        label_policy=policy,
        return_mode="eeg",
        include_subjects=train_subjects,
        cache_files=True,
    )
    val_ds = IDARETrialDataset(
        task=task,
        label_policy=policy,
        return_mode="eeg",
        include_subjects=val_subjects,
        cache_files=True,
    )

    train_counts = {int(k): int(v) for k, v in train_ds.df["label"].value_counts().sort_index().to_dict().items()}
    val_counts = {int(k): int(v) for k, v in val_ds.df["label"].value_counts().sort_index().to_dict().items()}

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
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    class_weights = class_weights_from_counts(train_counts, device=device) if use_class_weights else None
    criterion = torch.nn.CrossEntropyLoss(weight=class_weights)

    history: list[dict[str, Any]] = []
    best_epoch: dict[str, Any] | None = None

    for epoch in range(1, epochs + 1):
        model.train()
        losses: list[float] = []
        accuracies: list[float] = []

        for batch in train_loader:
            x = batch["eeg"].to(device=device, dtype=torch.float32)
            y = batch["label"].to(device=device, dtype=torch.long)

            optimizer.zero_grad(set_to_none=True)
            logits, _ = model(x, return_attn=False)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            pred = logits.argmax(dim=1)
            acc = float((pred == y).float().mean().item())
            losses.append(float(loss.item()))
            accuracies.append(acc)

        val_metrics = eval_model(model, val_loader, device=device, criterion=criterion)

        row = {
            "epoch": int(epoch),
            "train_loss_mean": float(np.mean(losses)) if losses else math.nan,
            "train_accuracy_mean": float(np.mean(accuracies)) if accuracies else math.nan,
            "train_batches": int(len(losses)),
            "val": val_metrics,
        }
        history.append(row)

        if best_epoch is None or val_metrics["macro_f1"] > best_epoch["val"]["macro_f1"]:
            best_epoch = row

    assert best_epoch is not None

    final_val = history[-1]["val"]
    warnings: list[str] = []
    if 0 in [int(v) for v in final_val["pred_counts"].values()]:
        warnings.append("Final epoch predicted only one class on the validation split.")
    if final_val["balanced_accuracy"] <= 0.5001:
        warnings.append("Final balanced accuracy is near chance.")

    return {
        "task": task,
        "policy": policy,
        "seed": int(seed),
        "train_subjects": train_subjects,
        "val_subjects": val_subjects,
        "train_rows": int(len(train_ds)),
        "val_rows": int(len(val_ds)),
        "train_label_counts": {str(k): int(v) for k, v in train_counts.items()},
        "val_label_counts": {str(k): int(v) for k, v in val_counts.items()},
        "use_class_weights": bool(use_class_weights),
        "class_weights": [float(v) for v in class_weights.detach().cpu().tolist()] if class_weights is not None else None,
        "epochs": int(epochs),
        "batch_size": int(batch_size),
        "history": history,
        "best_epoch": best_epoch,
        "final_val": final_val,
        "warnings": warnings,
    }


def aggregate_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        groups[(row["task"], row["policy"])].append(row)

    summary = []
    for (task, policy), rows in sorted(groups.items()):
        final_acc = [r["final_val"]["accuracy"] for r in rows]
        final_bal = [r["final_val"]["balanced_accuracy"] for r in rows]
        final_f1 = [r["final_val"]["macro_f1"] for r in rows]
        best_f1 = [r["best_epoch"]["val"]["macro_f1"] for r in rows]
        maj_acc = [r["final_val"]["majority_baseline"]["accuracy"] for r in rows]

        summary.append(
            {
                "task": task,
                "policy": policy,
                "n_seeds": len(rows),
                "final_accuracy_mean": float(np.mean(final_acc)),
                "final_accuracy_std": float(np.std(final_acc)),
                "final_balanced_accuracy_mean": float(np.mean(final_bal)),
                "final_balanced_accuracy_std": float(np.std(final_bal)),
                "final_macro_f1_mean": float(np.mean(final_f1)),
                "final_macro_f1_std": float(np.std(final_f1)),
                "best_macro_f1_mean": float(np.mean(best_f1)),
                "majority_accuracy_mean": float(np.mean(maj_acc)),
            }
        )

    return summary


def write_markdown(payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# I-DARE EEG-only Score-5 Policy Mini-Baseline\n")
    lines.append("This report was generated by `scripts/11_run_idare_eeg_policy_mini_baseline.py`.\n")
    lines.append("\n**Important:** this is still not full LOSO and not a final experiment.\n")
    lines.append("No checkpoint was saved.\n")

    lines.append("\n## Status\n")
    lines.append(f"Status: **{payload['status']}**\n")

    lines.append("\n## Why This Exists\n")
    lines.append("- The earlier tiny pilot often collapsed to one-class predictions.\n")
    lines.append("- This mini-baseline uses a larger subject-held-out split and class-weighted loss by default.\n")
    lines.append("- The goal is to decide whether all three score-5 policies deserve full LOSO baseline runs.\n")

    lines.append("\n## Configuration\n")
    lines.append("```json\n")
    lines.append(json.dumps(payload["config"], indent=2, ensure_ascii=False))
    lines.append("\n```\n")

    lines.append("\n## Aggregate Results\n")
    lines.append("| Task | Policy | Seeds | Acc mean | Bal acc mean | Macro F1 mean | Best F1 mean | Majority acc |\n")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|\n")
    for row in payload["aggregate"]:
        lines.append(
            f"| {row['task']} | {row['policy']} | {row['n_seeds']} | "
            f"{row['final_accuracy_mean']:.4f} | {row['final_balanced_accuracy_mean']:.4f} | "
            f"{row['final_macro_f1_mean']:.4f} | {row['best_macro_f1_mean']:.4f} | "
            f"{row['majority_accuracy_mean']:.4f} |\n"
        )

    lines.append("\n## Run Details\n")
    for row in payload["results"]:
        fv = row["final_val"]
        bv = row["best_epoch"]["val"]
        lines.append(f"\n### {row['task']} / {row['policy']} / seed {row['seed']}\n")
        lines.append(f"- Train rows: `{row['train_rows']}`; validation rows: `{row['val_rows']}`\n")
        lines.append(f"- Train label counts: `{row['train_label_counts']}`\n")
        lines.append(f"- Validation label counts: `{row['val_label_counts']}`\n")
        lines.append(f"- Class weights: `{row['class_weights']}`\n")
        lines.append(
            f"- Final: acc `{fv['accuracy']:.4f}`, balanced acc `{fv['balanced_accuracy']:.4f}`, "
            f"macro F1 `{fv['macro_f1']:.4f}`\n"
        )
        lines.append(
            f"- Best epoch by macro F1: epoch `{row['best_epoch']['epoch']}`, "
            f"balanced acc `{bv['balanced_accuracy']:.4f}`, macro F1 `{bv['macro_f1']:.4f}`\n"
        )
        lines.append(f"- Final pred counts: `{fv['pred_counts']}`\n")
        lines.append(f"- Final confusion: `{fv['confusion']}`\n")
        if row["warnings"]:
            lines.append("- Warnings:\n")
            for warning in row["warnings"]:
                lines.append(f"  - {warning}\n")

    lines.append("\n## Global Issues\n")
    if payload["issues"]:
        for issue in payload["issues"]:
            lines.append(f"- {issue}\n")
    else:
        lines.append("- None.\n")

    lines.append("\n## Global Warnings\n")
    if payload["warnings"]:
        for warning in payload["warnings"]:
            lines.append(f"- {warning}\n")
    else:
        lines.append("- None.\n")

    lines.append("\n## Interpretation Rule\n")
    lines.append("- Prefer balanced accuracy and macro F1 over raw accuracy for policy comparison.\n")
    lines.append("- If all policies remain near chance, keep all three as label presets but do not expand ablations yet.\n")
    lines.append("- If one policy is clearly better across both seeds and both tasks, promote it as the temporary main I-DARE binary preset.\n")

    OUT_MD.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", nargs="+", choices=TASKS, default=TASKS)
    parser.add_argument("--policies", nargs="+", choices=POLICIES, default=POLICIES)
    parser.add_argument("--seeds", nargs="+", type=int, default=[11, 13])
    parser.add_argument("--train-subjects", nargs="+", type=int, default=[5, 6, 7, 8, 9, 10, 11, 12])
    parser.add_argument("--val-subjects", nargs="+", type=int, default=[1, 2, 3, 13])
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--no-class-weights", action="store_true")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        if args.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but torch.cuda.is_available() is False.")
        device = torch.device(args.device)

    issues: list[str] = []
    warnings: list[str] = []
    results: list[dict[str, Any]] = []

    for task in args.tasks:
        for policy in args.policies:
            for seed in args.seeds:
                print(f"Running mini-baseline: task={task}, policy={policy}, seed={seed}")
                result = run_one(
                    task=task,
                    policy=policy,
                    seed=seed,
                    train_subjects=args.train_subjects,
                    val_subjects=args.val_subjects,
                    device=device,
                    batch_size=args.batch_size,
                    epochs=args.epochs,
                    use_class_weights=not args.no_class_weights,
                )
                results.append(result)
                for warning in result["warnings"]:
                    warnings.append(f"{task}/{policy}/seed{seed}: {warning}")

    aggregate = aggregate_results(results)

    payload = {
        "status": "PASSED" if not issues else "FAILED",
        "config": {
            "tasks": args.tasks,
            "policies": args.policies,
            "seeds": args.seeds,
            "train_subjects": args.train_subjects,
            "val_subjects": args.val_subjects,
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "use_class_weights": not args.no_class_weights,
            "device": str(device),
            "torch_version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        "aggregate": aggregate,
        "results": results,
        "issues": issues,
        "warnings": warnings,
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(payload)

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print(f"Status: {payload['status']}")
    print(f"Issues: {len(issues)}")
    print(f"Warnings: {len(warnings)}")

    print("\nAggregate:")
    for row in aggregate:
        print(
            f"{row['task']}/{row['policy']}: "
            f"acc={row['final_accuracy_mean']:.4f} "
            f"bal_acc={row['final_balanced_accuracy_mean']:.4f} "
            f"macro_f1={row['final_macro_f1_mean']:.4f} "
            f"best_f1={row['best_macro_f1_mean']:.4f} "
            f"maj_acc={row['majority_accuracy_mean']:.4f}"
        )

    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
