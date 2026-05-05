#!/usr/bin/env python3
"""
Tiny I-DARE EEG-only label-policy comparison.

Goal:
- Compare three score-5 policies in a small controlled pilot:
  1. discard_midpoint
  2. midpoint_as_low
  3. midpoint_as_high
- Run both valence and arousal.
- Use a tiny subject-held-out split, not full LOSO.
- Report accuracy, balanced accuracy, macro F1, and class counts.

Important:
This is NOT a final experiment.
This is NOT full LOSO.
This is only a directional policy pilot before committing to full baseline runs.

Outputs:
- docs/idare_label_policy_comparison.md
- docs/idare_label_policy_comparison.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
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


OUT_MD = ROOT / "docs" / "idare_label_policy_comparison.md"
OUT_JSON = ROOT / "docs" / "idare_label_policy_comparison.json"

LABEL_POLICIES = ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]
TASKS = ["valence", "arousal"]


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


def count_trainable_params(model: torch.nn.Module) -> int:
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def binary_metrics(y_true: list[int], y_pred: list[int]) -> dict[str, Any]:
    labels = [0, 1]
    total = len(y_true)
    correct = sum(int(t == p) for t, p in zip(y_true, y_pred))

    per_class: dict[str, Any] = {}
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
        per_class[str(label)] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": sum(1 for t in y_true if t == label),
        }

    return {
        "n": total,
        "accuracy": safe_div(correct, total),
        "balanced_accuracy": float(sum(recalls) / len(recalls)),
        "macro_f1": float(sum(f1s) / len(f1s)),
        "true_counts": {str(label): int(sum(1 for t in y_true if t == label)) for label in labels},
        "pred_counts": {str(label): int(sum(1 for p in y_pred if p == label)) for label in labels},
        "per_class": per_class,
    }


def collect_eval_metrics(
    model: torch.nn.Module,
    loader: DataLoader,
    *,
    device: torch.device,
    max_eval_batches: int,
) -> dict[str, Any]:
    model.eval()
    criterion = torch.nn.CrossEntropyLoss()

    all_true: list[int] = []
    all_pred: list[int] = []
    losses: list[float] = []

    with torch.no_grad():
        for batch_idx, batch in enumerate(loader):
            if batch_idx >= max_eval_batches:
                break

            x = batch["eeg"].to(device=device, dtype=torch.float32)
            y = batch["label"].to(device=device, dtype=torch.long)

            logits, _ = model(x, return_attn=False)
            loss = criterion(logits, y)
            pred = logits.argmax(dim=1)

            losses.append(float(loss.item()))
            all_true.extend(int(v) for v in y.detach().cpu().tolist())
            all_pred.extend(int(v) for v in pred.detach().cpu().tolist())

    metrics = binary_metrics(all_true, all_pred)
    metrics["loss_mean"] = float(np.mean(losses)) if losses else math.nan
    metrics["batches"] = len(losses)
    return metrics


def train_tiny(
    *,
    task: str,
    label_policy: str,
    train_subjects: list[int],
    test_subjects: list[int],
    device: torch.device,
    batch_size: int,
    epochs: int,
    max_train_batches: int,
    max_eval_batches: int,
    seed: int,
) -> dict[str, Any]:
    # Reset seed per run to make policies comparable.
    set_seed(seed)

    train_ds = IDARETrialDataset(
        task=task,
        label_policy=label_policy,
        return_mode="eeg",
        include_subjects=train_subjects,
        cache_files=True,
    )
    test_ds = IDARETrialDataset(
        task=task,
        label_policy=label_policy,
        return_mode="eeg",
        include_subjects=test_subjects,
        cache_files=True,
    )

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
    test_loader = DataLoader(
        test_ds,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )

    model = make_model(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = torch.nn.CrossEntropyLoss()

    train_history: list[dict[str, Any]] = []

    for epoch in range(epochs):
        model.train()
        batch_losses: list[float] = []
        batch_accs: list[float] = []

        for batch_idx, batch in enumerate(train_loader):
            if batch_idx >= max_train_batches:
                break

            x = batch["eeg"].to(device=device, dtype=torch.float32)
            y = batch["label"].to(device=device, dtype=torch.long)

            optimizer.zero_grad(set_to_none=True)
            logits, _ = model(x, return_attn=False)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()

            pred = logits.argmax(dim=1)
            acc = float((pred == y).float().mean().item())
            batch_losses.append(float(loss.item()))
            batch_accs.append(acc)

        train_history.append(
            {
                "epoch": epoch + 1,
                "batches": len(batch_losses),
                "loss_mean": float(np.mean(batch_losses)) if batch_losses else math.nan,
                "accuracy_mean": float(np.mean(batch_accs)) if batch_accs else math.nan,
            }
        )

    eval_metrics = collect_eval_metrics(
        model,
        test_loader,
        device=device,
        max_eval_batches=max_eval_batches,
    )

    return {
        "task": task,
        "label_policy": label_policy,
        "train_subjects": train_subjects,
        "test_subjects": test_subjects,
        "train_rows": len(train_ds),
        "test_rows": len(test_ds),
        "train_label_counts": {str(k): int(v) for k, v in train_ds.df["label"].value_counts().sort_index().to_dict().items()},
        "test_label_counts": {str(k): int(v) for k, v in test_ds.df["label"].value_counts().sort_index().to_dict().items()},
        "model_trainable_parameters": count_trainable_params(model),
        "train_history": train_history,
        "eval": eval_metrics,
    }


def dataset_summary(task: str, label_policy: str) -> dict[str, Any]:
    ds = IDARETrialDataset(task=task, label_policy=label_policy, return_mode="eeg", cache_files=True)
    return {
        "task": task,
        "label_policy": label_policy,
        "rows": len(ds),
        "subjects": int(ds.df["subject_id"].nunique()),
        "label_counts": {str(k): int(v) for k, v in ds.df["label"].value_counts().sort_index().to_dict().items()},
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# I-DARE Score-5 Label Policy Comparison\n")
    lines.append("This report was generated by `scripts/10_compare_idare_label_policies.py`.\n")
    lines.append("\n**Important:** this is a tiny EEG-only policy pilot, not a final LOSO experiment.\n")
    lines.append("No checkpoint was saved.\n")

    lines.append("\n## Status\n")
    lines.append(f"Status: **{payload['status']}**\n")

    lines.append("\n## Compared Policies\n")
    lines.append("- `discard_midpoint`: score < 5 -> 0, score > 5 -> 1, score == 5 dropped.\n")
    lines.append("- `midpoint_as_low`: score <= 5 -> 0, score > 5 -> 1.\n")
    lines.append("- `midpoint_as_high`: score < 5 -> 0, score >= 5 -> 1.\n")

    lines.append("\n## Pilot Configuration\n")
    lines.append("```json\n")
    lines.append(json.dumps(payload["config"], indent=2, ensure_ascii=False))
    lines.append("\n```\n")

    lines.append("\n## Dataset Counts by Policy\n")
    lines.append("| Task | Policy | Rows | Subjects | Label counts |\n")
    lines.append("|---|---|---:|---:|---|\n")
    for row in payload["dataset_summaries"]:
        lines.append(
            f"| {row['task']} | {row['label_policy']} | {row['rows']} | "
            f"{row['subjects']} | `{row['label_counts']}` |\n"
        )

    if payload.get("pilot_results"):
        lines.append("\n## Tiny EEG-only Pilot Results\n")
        lines.append("| Task | Policy | Train rows | Test rows | Test acc | Test bal acc | Test macro F1 | Test counts |\n")
        lines.append("|---|---|---:|---:|---:|---:|---:|---|\n")
        for row in payload["pilot_results"]:
            ev = row["eval"]
            lines.append(
                f"| {row['task']} | {row['label_policy']} | {row['train_rows']} | {row['test_rows']} | "
                f"{ev['accuracy']:.4f} | {ev['balanced_accuracy']:.4f} | {ev['macro_f1']:.4f} | "
                f"`{row['test_label_counts']}` |\n"
            )

        lines.append("\n### Full Pilot Result JSON\n")
        lines.append("```json\n")
        lines.append(json.dumps(payload["pilot_results"], indent=2, ensure_ascii=False))
        lines.append("\n```\n")
    else:
        lines.append("\n## Tiny EEG-only Pilot Results\n")
        lines.append("Pilot training was not run. Re-run with `--run-pilot` to produce directional metrics.\n")

    lines.append("\n## Interpretation Notes\n")
    lines.append("- The pilot is deliberately tiny and should not be treated as publishable evidence.\n")
    lines.append("- If one policy improves accuracy but hurts balanced accuracy or macro F1, it may be exploiting class imbalance.\n")
    lines.append("- Full decision should wait for LOSO baseline, but this pilot can decide whether all three policies deserve full testing.\n")

    lines.append("\n## Issues\n")
    if payload["issues"]:
        for issue in payload["issues"]:
            lines.append(f"- {issue}\n")
    else:
        lines.append("- None.\n")

    lines.append("\n## Warnings\n")
    if payload["warnings"]:
        for warning in payload["warnings"]:
            lines.append(f"- {warning}\n")
    else:
        lines.append("- None.\n")

    OUT_MD.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-pilot", action="store_true", help="Run the tiny EEG-only train/eval policy pilot.")
    parser.add_argument("--tasks", nargs="+", choices=TASKS, default=TASKS)
    parser.add_argument("--policies", nargs="+", choices=LABEL_POLICIES, default=LABEL_POLICIES)
    parser.add_argument("--train-subjects", nargs="+", type=int, default=[5, 6, 7, 8])
    parser.add_argument("--test-subjects", nargs="+", type=int, default=[1, 2])
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--max-train-batches", type=int, default=8)
    parser.add_argument("--max-eval-batches", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    args = parser.parse_args()

    set_seed(args.seed)

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        if args.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but torch.cuda.is_available() is False.")
        device = torch.device(args.device)

    issues: list[str] = []
    warnings: list[str] = []
    dataset_summaries: list[dict[str, Any]] = []

    for task in args.tasks:
        for policy in args.policies:
            dataset_summaries.append(dataset_summary(task, policy))

    pilot_results: list[dict[str, Any]] = []
    if args.run_pilot:
        for task in args.tasks:
            for policy in args.policies:
                print(f"Running tiny pilot: task={task}, policy={policy}")
                result = train_tiny(
                    task=task,
                    label_policy=policy,
                    train_subjects=args.train_subjects,
                    test_subjects=args.test_subjects,
                    device=device,
                    batch_size=args.batch_size,
                    epochs=args.epochs,
                    max_train_batches=args.max_train_batches,
                    max_eval_batches=args.max_eval_batches,
                    seed=args.seed,
                )
                pilot_results.append(result)

                # Directional warning: one-class prediction is a common tiny-pilot failure mode.
                pred_counts = result["eval"].get("pred_counts", {})
                if 0 in [int(v) for v in pred_counts.values()]:
                    warnings.append(f"{task}/{policy}: tiny pilot predicted only one class on evaluated batches.")

    payload = {
        "status": "PASSED" if not issues else "FAILED",
        "config": {
            "run_pilot": args.run_pilot,
            "tasks": args.tasks,
            "policies": args.policies,
            "train_subjects": args.train_subjects,
            "test_subjects": args.test_subjects,
            "epochs": args.epochs,
            "max_train_batches": args.max_train_batches,
            "max_eval_batches": args.max_eval_batches,
            "batch_size": args.batch_size,
            "seed": args.seed,
            "device": str(device),
            "torch_version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        "dataset_summaries": dataset_summaries,
        "pilot_results": pilot_results,
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

    for row in dataset_summaries:
        print(f"{row['task']}/{row['label_policy']}: rows={row['rows']} labels={row['label_counts']}")

    if pilot_results:
        print("\nPilot results:")
        for row in pilot_results:
            ev = row["eval"]
            print(
                f"{row['task']}/{row['label_policy']}: "
                f"acc={ev['accuracy']:.4f} bal_acc={ev['balanced_accuracy']:.4f} "
                f"macro_f1={ev['macro_f1']:.4f} test_counts={row['test_label_counts']}"
            )

    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
