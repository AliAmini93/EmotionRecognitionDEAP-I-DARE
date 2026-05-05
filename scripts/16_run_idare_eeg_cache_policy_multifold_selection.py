#!/usr/bin/env python3
"""
Run cache-based multi-fold I-DARE EEG score-5 policy selection.

Goal:
- Re-check score==5 policies across multiple small subject-held-out folds.
- Use the EEG cache, not MATLAB/HDF5 files.
- Keep runtime short enough for interactive iteration.
- Produce:
  - docs/idare_eeg_cache_policy_multifold_selection.md
  - docs/idare_eeg_cache_policy_multifold_selection.json

Important:
This is not full LOSO.
This is still a policy-selection pilot.
No checkpoint is saved.
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

OUT_MD = ROOT / "docs" / "idare_eeg_cache_policy_multifold_selection.md"
OUT_JSON = ROOT / "docs" / "idare_eeg_cache_policy_multifold_selection.json"

TASKS = ["valence", "arousal"]
POLICIES = ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]

DEFAULT_FOLDS = [
    [1, 2, 3, 13],
    [14, 15, 16, 17],
    [18, 19, 20, 21],
    [22, 23, 24, 25],
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--seeds", type=int, nargs="+", default=[11, 13])
    parser.add_argument(
        "--max-train-subjects",
        type=int,
        default=24,
        help=(
            "Cap number of train subjects per fold to keep the pilot quick. "
            "Use 0 for all non-validation subjects."
        ),
    )
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-3)
    parser.add_argument("--no-class-weights", action="store_true")
    parser.add_argument(
        "--folds-json",
        type=str,
        default="",
        help='Optional JSON list of validation folds, e.g. "[[1,2,3,13],[14,15,16,17]]".',
    )
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def label_column(task: str, policy: str) -> str:
    col = f"{task}_{policy}"
    if task not in TASKS:
        raise ValueError(f"Unknown task: {task}")
    if policy not in POLICIES:
        raise ValueError(f"Unknown policy: {policy}")
    return col


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
    majority_metrics = binary_metrics_no_majority(y_true, majority_pred)

    return {
        "n": int(total),
        "accuracy": safe_div(correct, total),
        "balanced_accuracy": float(sum(recalls) / len(recalls)),
        "macro_f1": float(sum(f1s) / len(f1s)),
        "true_counts": true_counts,
        "pred_counts": pred_counts,
        "confusion": confusion,
        "per_class": per_class,
        "majority_baseline": {
            "label": int(majority_label),
            "accuracy": majority_metrics["accuracy"],
            "balanced_accuracy": majority_metrics["balanced_accuracy"],
            "macro_f1": majority_metrics["macro_f1"],
        },
    }


class CachedEEGDataset(Dataset):
    def __init__(
        self,
        *,
        task: str,
        policy: str,
        subjects: list[int],
        cache_npy: Path = CACHE_NPY,
        cache_index: Path = CACHE_INDEX,
    ) -> None:
        if not cache_npy.exists():
            raise FileNotFoundError(f"Missing cache npy: {cache_npy}")
        if not cache_index.exists():
            raise FileNotFoundError(f"Missing cache index: {cache_index}")

        df = pd.read_csv(cache_index)
        col = label_column(task, policy)
        if col not in df.columns:
            raise KeyError(f"Missing label column {col}. Columns: {list(df.columns)}")

        df = df[df["subject_id"].astype(int).isin(subjects)].copy()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df[df[col].notna()].copy()
        df["label"] = df[col].astype(int)
        df = df.sort_values(["subject_id", "stimulus_id"]).reset_index(drop=True)

        self.task = task
        self.policy = policy
        self.df = df
        self.cache = np.load(cache_npy, mmap_mode="r")

        if len(self.df) == 0:
            raise ValueError(f"Empty dataset for task={task}, policy={policy}, subjects={subjects}")

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        row = self.df.iloc[idx]
        cache_row = int(row["cache_row"])
        eeg = np.asarray(self.cache[cache_row], dtype=np.float32)
        label = int(row["label"])
        return {
            "eeg": torch.from_numpy(eeg.copy()),
            "label": torch.tensor(label, dtype=torch.long),
            "subject_id": int(row["subject_id"]),
            "stimulus_id": str(row["stimulus_id"]),
            "cache_row": cache_row,
        }


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
    fold_id: int,
    train_subjects: list[int],
    val_subjects: list[int],
    device: torch.device,
    batch_size: int,
    epochs: int,
    lr: float,
    weight_decay: float,
    use_class_weights: bool,
) -> dict[str, Any]:
    set_seed(seed)

    train_ds = CachedEEGDataset(task=task, policy=policy, subjects=train_subjects)
    val_ds = CachedEEGDataset(task=task, policy=policy, subjects=val_subjects)

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

    if use_class_weights:
        weights = class_weights_from_counts(train_counts, device=device)
        criterion = torch.nn.CrossEntropyLoss(weight=weights)
        weights_list: list[float] | None = [float(x) for x in weights.detach().cpu().tolist()]
    else:
        criterion = torch.nn.CrossEntropyLoss()
        weights_list = None

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    history: list[dict[str, Any]] = []
    run_start = time.perf_counter()

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_losses: list[float] = []
        train_true: list[int] = []
        train_pred: list[int] = []
        epoch_start = time.perf_counter()

        for batch in train_loader:
            x = batch["eeg"].to(device=device, dtype=torch.float32)
            y = batch["label"].to(device=device, dtype=torch.long)

            optimizer.zero_grad(set_to_none=True)
            logits, _ = model(x, return_attn=False)
            loss = criterion(logits, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()

            epoch_losses.append(float(loss.item()))
            pred = logits.argmax(dim=1)
            train_true.extend(int(v) for v in y.detach().cpu().tolist())
            train_pred.extend(int(v) for v in pred.detach().cpu().tolist())

        train_metrics = binary_metrics(train_true, train_pred)
        val_metrics = eval_model(model, val_loader, device=device, criterion=criterion)
        epoch_sec = time.perf_counter() - epoch_start

        history.append(
            {
                "epoch": epoch,
                "elapsed_sec": epoch_sec,
                "train_loss_mean": float(np.mean(epoch_losses)) if epoch_losses else math.nan,
                "train": train_metrics,
                "val": val_metrics,
            }
        )

        print(
            (
                f"{task}/{policy}/fold{fold_id}/seed{seed} "
                f"epoch {epoch}/{epochs} sec={epoch_sec:.2f} "
                f"train_f1={train_metrics['macro_f1']:.4f} "
                f"val_f1={val_metrics['macro_f1']:.4f} "
                f"val_bal={val_metrics['balanced_accuracy']:.4f}"
            ),
            flush=True,
        )

    elapsed_sec = time.perf_counter() - run_start
    final = history[-1]["val"]
    best = max(history, key=lambda x: (x["val"]["macro_f1"], x["val"]["balanced_accuracy"]))

    warnings: list[str] = []
    if len([k for k, v in final["pred_counts"].items() if v > 0]) < 2:
        warnings.append("Final epoch predicted only one class on the validation split.")
    if abs(final["balanced_accuracy"] - 0.5) < 0.025:
        warnings.append("Final balanced accuracy is near chance.")
    if final["macro_f1"] <= final["majority_baseline"]["macro_f1"]:
        warnings.append("Final macro F1 does not beat majority-class baseline macro F1.")

    return {
        "task": task,
        "policy": policy,
        "seed": seed,
        "fold_id": fold_id,
        "train_subjects": train_subjects,
        "val_subjects": val_subjects,
        "train_rows": len(train_ds),
        "val_rows": len(val_ds),
        "train_label_counts": {str(k): v for k, v in train_counts.items()},
        "val_label_counts": {str(k): v for k, v in val_counts.items()},
        "class_weights": weights_list,
        "model_trainable_parameters": int(sum(p.numel() for p in model.parameters() if p.requires_grad)),
        "elapsed_sec": elapsed_sec,
        "history": history,
        "final": final,
        "best_epoch_by_macro_f1": {
            "epoch": best["epoch"],
            "val": best["val"],
        },
        "warnings": warnings,
    }


def mean_std(values: list[float]) -> dict[str, float]:
    arr = np.asarray(values, dtype=float)
    return {
        "mean": float(np.mean(arr)) if len(arr) else math.nan,
        "std": float(np.std(arr, ddof=0)) if len(arr) else math.nan,
    }


def aggregate_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[(run["task"], run["policy"])].append(run)

    rows: list[dict[str, Any]] = []
    for (task, policy), items in sorted(grouped.items()):
        final_acc = [float(x["final"]["accuracy"]) for x in items]
        final_bal = [float(x["final"]["balanced_accuracy"]) for x in items]
        final_f1 = [float(x["final"]["macro_f1"]) for x in items]
        best_f1 = [float(x["best_epoch_by_macro_f1"]["val"]["macro_f1"]) for x in items]
        best_bal = [float(x["best_epoch_by_macro_f1"]["val"]["balanced_accuracy"]) for x in items]
        majority_acc = [float(x["final"]["majority_baseline"]["accuracy"]) for x in items]
        elapsed = [float(x["elapsed_sec"]) for x in items]
        one_class = sum(
            1
            for x in items
            if len([k for k, v in x["final"]["pred_counts"].items() if v > 0]) < 2
        )

        rows.append(
            {
                "task": task,
                "policy": policy,
                "runs": len(items),
                "final_accuracy": mean_std(final_acc),
                "final_balanced_accuracy": mean_std(final_bal),
                "final_macro_f1": mean_std(final_f1),
                "best_macro_f1": mean_std(best_f1),
                "best_balanced_accuracy": mean_std(best_bal),
                "majority_accuracy": mean_std(majority_acc),
                "elapsed_sec": mean_std(elapsed),
                "one_class_final_runs": int(one_class),
            }
        )

    rows.sort(key=lambda r: (r["task"], -r["final_macro_f1"]["mean"], -r["final_balanced_accuracy"]["mean"]))
    return rows


def make_recommendations(aggregate: list[dict[str, Any]]) -> dict[str, Any]:
    recs: dict[str, Any] = {}

    for task in TASKS:
        task_rows = [r for r in aggregate if r["task"] == task]
        task_rows_sorted = sorted(
            task_rows,
            key=lambda r: (
                r["final_macro_f1"]["mean"],
                r["final_balanced_accuracy"]["mean"],
                r["best_macro_f1"]["mean"],
            ),
            reverse=True,
        )

        top = task_rows_sorted[0]
        second = task_rows_sorted[1] if len(task_rows_sorted) > 1 else None

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
            margin_f1 >= 0.03
            and top["final_balanced_accuracy"]["mean"] >= 0.52
            and top["one_class_final_runs"] <= max(1, top["runs"] // 4)
        )

        recs[task] = {
            "top_policy": top["policy"],
            "second_policy": second["policy"] if second else None,
            "margin_final_macro_f1_vs_second": margin_f1,
            "margin_final_balanced_accuracy_vs_second": margin_bal,
            "is_clear_temporary_winner": bool(clear),
            "recommendation": (
                f"Promote {top['policy']} as temporary main preset for {task}."
                if clear
                else "Do not promote a single policy yet; keep candidate policies for the next baseline."
            ),
        }

    return recs


def write_reports(payload: dict[str, Any]) -> None:
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    md: list[str] = []
    md.append("# I-DARE EEG Cache-Based Multi-Fold Score-5 Policy Selection\n")
    md.append("This report was generated by `scripts/16_run_idare_eeg_cache_policy_multifold_selection.py`.\n")
    md.append("\n**Important:** this is still a policy-selection pilot, not full LOSO and not a final experiment.\n")
    md.append("No checkpoint was saved.\n")

    md.append("\n## Status\n")
    md.append(f"Status: **{payload['status']}**\n")

    md.append("\n## Configuration\n")
    md.append("```json\n")
    md.append(json.dumps(payload["config"], indent=2, ensure_ascii=False))
    md.append("\n```\n")

    md.append("\n## Aggregate Results\n")
    md.append(
        "| Task | Policy | Runs | Final macro F1 mean | Final bal acc mean | Best F1 mean | One-class final runs | Majority acc mean | Mean sec |\n"
    )
    md.append("|---|---|---:|---:|---:|---:|---:|---:|---:|\n")
    for row in payload["aggregate"]:
        md.append(
            "| {task} | {policy} | {runs} | {f1:.4f} | {bal:.4f} | {best:.4f} | {one} | {maj:.4f} | {sec:.2f} |\n".format(
                task=row["task"],
                policy=row["policy"],
                runs=row["runs"],
                f1=row["final_macro_f1"]["mean"],
                bal=row["final_balanced_accuracy"]["mean"],
                best=row["best_macro_f1"]["mean"],
                one=row["one_class_final_runs"],
                maj=row["majority_accuracy"]["mean"],
                sec=row["elapsed_sec"]["mean"],
            )
        )

    md.append("\n## Recommendations\n")
    md.append("```json\n")
    md.append(json.dumps(payload["recommendations"], indent=2, ensure_ascii=False))
    md.append("\n```\n")

    md.append("\n## Fold Definitions\n")
    for fold in payload["folds"]:
        md.append(
            f"- Fold {fold['fold_id']}: validation subjects `{fold['val_subjects']}`, train subjects `{fold['train_subjects']}`\n"
        )

    md.append("\n## Run Details\n")
    for run in payload["runs"]:
        md.append(f"\n### {run['task']} / {run['policy']} / fold {run['fold_id']} / seed {run['seed']}\n")
        md.append(f"- Train rows: `{run['train_rows']}`; validation rows: `{run['val_rows']}`\n")
        md.append(f"- Train label counts: `{run['train_label_counts']}`\n")
        md.append(f"- Validation label counts: `{run['val_label_counts']}`\n")
        md.append(f"- Elapsed seconds: `{run['elapsed_sec']:.2f}`\n")
        final = run["final"]
        best = run["best_epoch_by_macro_f1"]
        md.append(
            f"- Final: acc `{final['accuracy']:.4f}`, balanced acc `{final['balanced_accuracy']:.4f}`, macro F1 `{final['macro_f1']:.4f}`\n"
        )
        md.append(
            f"- Best epoch by macro F1: epoch `{best['epoch']}`, balanced acc `{best['val']['balanced_accuracy']:.4f}`, macro F1 `{best['val']['macro_f1']:.4f}`\n"
        )
        md.append(f"- Final pred counts: `{final['pred_counts']}`\n")
        md.append(f"- Final confusion: `{final['confusion']}`\n")
        if run["warnings"]:
            md.append("- Warnings:\n")
            for warning in run["warnings"]:
                md.append(f"  - {warning}\n")

    md.append("\n## Global Issues\n")
    if payload["issues"]:
        for issue in payload["issues"]:
            md.append(f"- {issue}\n")
    else:
        md.append("- None.\n")

    md.append("\n## Global Warnings\n")
    if payload["warnings"]:
        for warning in payload["warnings"]:
            md.append(f"- {warning}\n")
    else:
        md.append("- None.\n")

    md.append("\n## Interpretation Rule\n")
    md.append("- Prefer macro F1 and balanced accuracy over raw accuracy.\n")
    md.append("- Penalize policies that frequently collapse to one-class validation predictions.\n")
    md.append("- Promote a policy only if it is clearly better across folds/seeds for that task.\n")
    md.append("- If no policy is clearly better, keep all three as label presets but narrow full baselines to the most promising candidates.\n")

    OUT_MD.write_text("".join(md), encoding="utf-8")


def main() -> None:
    args = parse_args()
    start = time.perf_counter()

    if args.folds_json:
        val_folds = json.loads(args.folds_json)
    else:
        val_folds = DEFAULT_FOLDS

    if not CACHE_INDEX.exists():
        raise FileNotFoundError(f"Missing cache index: {CACHE_INDEX}")
    if not CACHE_NPY.exists():
        raise FileNotFoundError(f"Missing cache NPY: {CACHE_NPY}")

    index_df = pd.read_csv(CACHE_INDEX)
    all_subjects = sorted(int(x) for x in index_df["subject_id"].dropna().unique())

    folds: list[dict[str, Any]] = []
    for i, val_subjects_raw in enumerate(val_folds, start=1):
        val_subjects = sorted(int(x) for x in val_subjects_raw)
        train_candidates = [s for s in all_subjects if s not in set(val_subjects)]

        if args.max_train_subjects and args.max_train_subjects > 0:
            train_subjects = train_candidates[: args.max_train_subjects]
        else:
            train_subjects = train_candidates

        folds.append(
            {
                "fold_id": i,
                "val_subjects": val_subjects,
                "train_subjects": train_subjects,
            }
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True

    config = {
        "tasks": TASKS,
        "policies": POLICIES,
        "seeds": args.seeds,
        "folds": folds,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "use_class_weights": not args.no_class_weights,
        "lr": args.lr,
        "weight_decay": args.weight_decay,
        "cache_npy": str(CACHE_NPY),
        "cache_index": str(CACHE_INDEX),
        "device": str(device),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }

    runs: list[dict[str, Any]] = []
    issues: list[str] = []
    warnings: list[str] = []

    for task in TASKS:
        for policy in POLICIES:
            for fold in folds:
                for seed in args.seeds:
                    print(
                        f"Running multifold policy pilot: task={task}, policy={policy}, fold={fold['fold_id']}, seed={seed}",
                        flush=True,
                    )
                    try:
                        run = run_one(
                            task=task,
                            policy=policy,
                            seed=int(seed),
                            fold_id=int(fold["fold_id"]),
                            train_subjects=list(fold["train_subjects"]),
                            val_subjects=list(fold["val_subjects"]),
                            device=device,
                            batch_size=args.batch_size,
                            epochs=args.epochs,
                            lr=args.lr,
                            weight_decay=args.weight_decay,
                            use_class_weights=not args.no_class_weights,
                        )
                        runs.append(run)
                        for warning in run["warnings"]:
                            warnings.append(
                                f"{task}/{policy}/fold{fold['fold_id']}/seed{seed}: {warning}"
                            )
                    except Exception as exc:
                        issue = f"{task}/{policy}/fold{fold['fold_id']}/seed{seed}: {exc!r}"
                        print(f"ERROR: {issue}", flush=True)
                        issues.append(issue)

    aggregate = aggregate_runs(runs)
    recommendations = make_recommendations(aggregate) if aggregate else {}

    elapsed_sec = time.perf_counter() - start
    status = "PASSED" if not issues else "FAILED"

    payload = {
        "status": status,
        "elapsed_sec": elapsed_sec,
        "config": config,
        "folds": folds,
        "runs": runs,
        "aggregate": aggregate,
        "recommendations": recommendations,
        "issues": issues,
        "warnings": warnings,
    }

    write_reports(payload)

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print(f"Status: {status}")
    print(f"Elapsed: {elapsed_sec:.2f}s")
    print(f"Issues: {len(issues)}")
    print(f"Warnings: {len(warnings)}")
    print("\nRecommendations:")
    print(json.dumps(recommendations, indent=2, ensure_ascii=False))
    print("\nAggregate:")
    for row in aggregate:
        print(
            (
                f"{row['task']}/{row['policy']}: "
                f"macro_f1={row['final_macro_f1']['mean']:.4f} "
                f"bal_acc={row['final_balanced_accuracy']['mean']:.4f} "
                f"best_f1={row['best_macro_f1']['mean']:.4f} "
                f"one_class={row['one_class_final_runs']}/{row['runs']} "
                f"sec={row['elapsed_sec']['mean']:.2f}"
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
