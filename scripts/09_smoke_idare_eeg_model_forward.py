#!/usr/bin/env python3
"""
Smoke test I-DARE EEG-only model forward pass.

Goal:
- Validate that IDARETrialDataset can feed EEG batches into EEGSegmentClassifier-v1.
- Validate forward pass, CrossEntropyLoss, backward pass, and one optimizer step.
- Validate both tasks: valence and arousal.

This is NOT full training.
This script does not save model checkpoints.
This script does not run epochs.
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

from emotion_deap_idare.datasets.idare_loader import IDAREPaths, IDARETrialDataset  # noqa: E402
from emotion_deap_idare.models.eeg_segment_classifier import EEGSegmentClassifier  # noqa: E402


OUT_MD = ROOT / "docs" / "idare_eeg_forward_smoke_test.md"
OUT_JSON = ROOT / "docs" / "idare_eeg_forward_smoke_test.json"


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def tensor_shape(value: Any) -> list[int] | None:
    if isinstance(value, torch.Tensor):
        return list(value.shape)
    return None


def count_trainable_params(model: torch.nn.Module) -> int:
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))


def grad_global_norm(model: torch.nn.Module) -> float:
    total_sq = 0.0
    for param in model.parameters():
        if param.grad is None:
            continue
        grad = param.grad.detach()
        total_sq += float(torch.sum(grad * grad).item())
    return float(math.sqrt(total_sq))


def summarize_aux(aux: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key, value in aux.items():
        if isinstance(value, torch.Tensor):
            summary[key] = {
                "shape": list(value.shape),
                "dtype": str(value.dtype),
                "isfinite": bool(torch.isfinite(value).all().item()),
            }
    return summary


def run_one_task(task: str, *, batch_size: int, device: torch.device) -> dict[str, Any]:
    dataset = IDARETrialDataset(
        task=task,          # "valence" or "arousal"
        return_mode="eeg",  # EEG-only smoke test
        keep_score5=False,  # current main binary preset: discard midpoint score 5
        cache_files=True,
    )

    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=(device.type == "cuda"),
    )

    batch = next(iter(loader))
    x = batch["eeg"].to(device=device, dtype=torch.float32)
    y = batch["label"].to(device=device, dtype=torch.long)

    model = EEGSegmentClassifier(
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

    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = torch.nn.CrossEntropyLoss()

    optimizer.zero_grad(set_to_none=True)
    logits, aux = model(x, return_attn=True)
    loss = criterion(logits, y)

    loss.backward()
    grad_norm = grad_global_norm(model)
    optimizer.step()

    with torch.no_grad():
        logits_after, _ = model(x, return_attn=False)
        loss_after = criterion(logits_after, y)

    issues: list[str] = []
    warnings: list[str] = []

    expected_x_shape = [min(batch_size, len(dataset)), 32, 640]
    expected_logits_shape = [x.shape[0], 2]

    if list(x.shape) != expected_x_shape:
        issues.append(f"Unexpected EEG batch shape: expected {expected_x_shape}, got {list(x.shape)}")

    if list(logits.shape) != expected_logits_shape:
        issues.append(f"Unexpected logits shape: expected {expected_logits_shape}, got {list(logits.shape)}")

    if not torch.isfinite(x).all().item():
        issues.append("EEG batch contains non-finite values.")

    if not torch.isfinite(logits).all().item():
        issues.append("Logits contain non-finite values.")

    if not torch.isfinite(loss).item():
        issues.append("Loss is not finite.")

    if not math.isfinite(grad_norm) or grad_norm <= 0:
        issues.append(f"Gradient global norm is invalid: {grad_norm}")

    label_values = sorted({int(v) for v in y.detach().cpu().tolist()})
    if not set(label_values).issubset({0, 1}):
        issues.append(f"Labels are not binary: {label_values}")

    if float(loss_after.item()) == float(loss.item()):
        warnings.append("Loss after one optimizer step is exactly equal to initial loss; this can happen, but inspect if repeated.")

    return {
        "task": task,
        "status": "PASSED" if not issues else "FAILED",
        "device": str(device),
        "dataset_rows_after_score5_discard": len(dataset),
        "subjects": int(dataset.df["subject_id"].nunique()),
        "label_counts": {str(k): int(v) for k, v in dataset.df["label"].value_counts().sort_index().to_dict().items()},
        "batch": {
            "eeg_shape": list(x.shape),
            "label_shape": list(y.shape),
            "label_values": y.detach().cpu().tolist(),
            "subject_ids": [int(v) for v in batch["subject_id"]],
            "stimulus_ids": [str(v) for v in batch["stimulus_id"]],
            "eeg_isfinite": bool(torch.isfinite(x).all().item()),
            "eeg_mean": float(x.mean().item()),
            "eeg_std": float(x.std().item()),
        },
        "model": {
            "class": "EEGSegmentClassifier",
            "variant": "v1-lite",
            "trainable_parameters": count_trainable_params(model),
            "input_shape": list(x.shape),
            "logits_shape": list(logits.shape),
            "loss_before_step": float(loss.item()),
            "loss_after_one_step": float(loss_after.item()),
            "grad_global_norm": grad_norm,
            "aux_tensor_summary": summarize_aux(aux),
        },
        "issues": issues,
        "warnings": warnings,
    }


def write_reports(payload: dict[str, Any]) -> None:
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines: list[str] = []
    lines.append("# I-DARE EEG-only Model Forward Smoke Test\n")
    lines.append("This report was generated by `scripts/09_smoke_idare_eeg_model_forward.py`.\n")
    lines.append("No full training was performed.\n")
    lines.append("No checkpoint was saved.\n")
    lines.append("\n## Status\n")
    lines.append(f"Status: **{payload['status']}**\n")
    lines.append("\n## Purpose\n")
    lines.append("- Validate `IDARETrialDataset` → `EEGSegmentClassifier-v1` compatibility.\n")
    lines.append("- Validate EEG batch shape `[B, 32, 640]`.\n")
    lines.append("- Validate forward pass, loss computation, backward pass, and one optimizer step.\n")
    lines.append("- Run this for both `valence` and `arousal` using the current main binary preset: discard `score == 5`.\n")
    lines.append("\n## Environment\n")
    lines.append("```json\n")
    lines.append(json.dumps(payload["environment"], indent=2, ensure_ascii=False))
    lines.append("\n```\n")

    for task_result in payload["tasks"]:
        lines.append(f"\n## Task: `{task_result['task']}`\n")
        lines.append(f"- Status: **{task_result['status']}**\n")
        lines.append(f"- Dataset rows after score-5 discard: `{task_result['dataset_rows_after_score5_discard']}`\n")
        lines.append(f"- Subjects: `{task_result['subjects']}`\n")
        lines.append(f"- Label counts: `{task_result['label_counts']}`\n")

        lines.append("\n### Batch Summary\n")
        lines.append("```json\n")
        lines.append(json.dumps(task_result["batch"], indent=2, ensure_ascii=False))
        lines.append("\n```\n")

        lines.append("\n### Model / Optimization Summary\n")
        lines.append("```json\n")
        lines.append(json.dumps(task_result["model"], indent=2, ensure_ascii=False))
        lines.append("\n```\n")

        lines.append("\n### Issues\n")
        if task_result["issues"]:
            for issue in task_result["issues"]:
                lines.append(f"- {issue}\n")
        else:
            lines.append("- None.\n")

        lines.append("\n### Warnings\n")
        if task_result["warnings"]:
            for warning in task_result["warnings"]:
                lines.append(f"- {warning}\n")
        else:
            lines.append("- None.\n")

    lines.append("\n## Next Step\n")
    lines.append("If this smoke test passes, document the result and then decide the next controlled baseline step. Do not start full LOSO training until the baseline-smoke path is reviewed.\n")

    OUT_MD.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--tasks", nargs="+", choices=["valence", "arousal"], default=["valence", "arousal"])
    args = parser.parse_args()

    set_seed(args.seed)

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        if args.device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but torch.cuda.is_available() is False.")
        device = torch.device(args.device)

    results = [run_one_task(task, batch_size=args.batch_size, device=device) for task in args.tasks]
    all_issues = [issue for result in results for issue in result["issues"]]
    all_warnings = [warning for result in results for warning in result["warnings"]]

    payload = {
        "status": "PASSED" if not all_issues else "FAILED",
        "environment": {
            "device": str(device),
            "torch_version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "seed": args.seed,
            "batch_size": args.batch_size,
        },
        "tasks": results,
        "issues": all_issues,
        "warnings": all_warnings,
    }

    write_reports(payload)

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print(f"Status: {payload['status']}")
    print(f"Issues: {len(all_issues)}")
    print(f"Warnings: {len(all_warnings)}")
    for result in results:
        print(
            f"{result['task']}: rows={result['dataset_rows_after_score5_discard']} "
            f"batch={result['batch']['eeg_shape']} logits={result['model']['logits_shape']} "
            f"loss={result['model']['loss_before_step']:.6f} grad_norm={result['model']['grad_global_norm']:.6f}"
        )

    if all_issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
