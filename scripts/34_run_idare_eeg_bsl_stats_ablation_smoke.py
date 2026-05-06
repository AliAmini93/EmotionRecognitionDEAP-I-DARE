#!/usr/bin/env python3
"""Run I-DARE EEG response + BSL stats sidecar training smoke.

Inputs:
- baseline-corrected EEG response cache: [n_trials, 32, 640]
- compact BSL stats sidecar: [n_trials, 229]
- aligned cache/index CSV files

Policy:
- The EEG cache is the main STIM-BSL response representation.
- The sidecar contains compact BSL summary statistics only.
- BSL stats are standardized with train-fold statistics only.
- No raw I-DARE EEG HDF5/MAT files are loaded inside training loops.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_EEG_NPY = ROOT / ".cache" / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
DEFAULT_EEG_INDEX = ROOT / ".cache" / "idare_eeg_cache_index_baseline_corrected.csv"
DEFAULT_BSL_NPY = ROOT / ".cache" / "idare_eeg_bsl_stats.npy"
DEFAULT_BSL_INDEX = ROOT / ".cache" / "idare_eeg_bsl_stats_index.csv"

DEFAULT_OUT_MD = ROOT / "docs" / "idare_eeg_bsl_stats_ablation_smoke.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "idare_eeg_bsl_stats_ablation_smoke.json"
DEFAULT_OUT_PRED = ROOT / "docs" / "idare_eeg_bsl_stats_ablation_smoke_predictions.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eeg-npy", type=Path, default=DEFAULT_EEG_NPY)
    parser.add_argument("--eeg-index", type=Path, default=DEFAULT_EEG_INDEX)
    parser.add_argument("--bsl-stats-npy", type=Path, default=DEFAULT_BSL_NPY)
    parser.add_argument("--bsl-stats-index", type=Path, default=DEFAULT_BSL_INDEX)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-predictions-csv", type=Path, default=DEFAULT_OUT_PRED)
    parser.add_argument("--tasks", nargs="+", default=["valence", "arousal"], choices=["valence", "arousal"])
    parser.add_argument(
        "--label-policy",
        default="midpoint_as_high",
        choices=["midpoint_as_high", "midpoint_as_low", "discard_midpoint"],
    )
    parser.add_argument("--recipes", nargs="+", default=["ce_class_weighted", "balanced_sampler_ce"])
    parser.add_argument("--folds", type=int, default=6)
    parser.add_argument("--seeds", nargs="+", type=int, default=[11])
    parser.add_argument("--epochs", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--max-runs", type=int, default=4)
    parser.add_argument("--stats-hidden-dim", type=int, default=32)
    parser.add_argument("--eeg-hidden-dim", type=int, default=64)
    parser.add_argument("--stats-zclip", type=float, default=8.0)
    return parser.parse_args()


def safe_json(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [safe_json(v) for v in obj]
    if isinstance(obj, tuple):
        return [safe_json(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        value = float(obj)
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def label_value(score: Any, policy: str) -> float:
    if pd.isna(score):
        return float("nan")
    x = float(score)
    if policy == "midpoint_as_high":
        return 1.0 if x >= 5.0 else 0.0
    if policy == "midpoint_as_low":
        return 1.0 if x > 5.0 else 0.0
    if policy == "discard_midpoint":
        if x == 5.0:
            return float("nan")
        return 1.0 if x > 5.0 else 0.0
    raise ValueError(policy)


def finite_summary(values: list[float]) -> dict[str, float | None]:
    arr = np.asarray(values, dtype=np.float64)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {"mean": None, "std": None, "min": None, "max": None}
    return {
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def confusion_counts(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, int]:
    y_true = y_true.astype(int)
    y_pred = y_pred.astype(int)
    return {
        "tn": int(((y_true == 0) & (y_pred == 0)).sum()),
        "fp": int(((y_true == 0) & (y_pred == 1)).sum()),
        "fn": int(((y_true == 1) & (y_pred == 0)).sum()),
        "tp": int(((y_true == 1) & (y_pred == 1)).sum()),
    }


def metrics_from_preds_basic(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    c = confusion_counts(y_true, y_pred)
    tn, fp, fn, tp = c["tn"], c["fp"], c["fn"], c["tp"]
    rec0 = tn / (tn + fp) if (tn + fp) else 0.0
    rec1 = tp / (tp + fn) if (tp + fn) else 0.0
    prec0 = tn / (tn + fn) if (tn + fn) else 0.0
    prec1 = tp / (tp + fp) if (tp + fp) else 0.0
    f1_0 = 2 * prec0 * rec0 / (prec0 + rec0) if (prec0 + rec0) else 0.0
    f1_1 = 2 * prec1 * rec1 / (prec1 + rec1) if (prec1 + rec1) else 0.0
    return {
        "accuracy": float((y_true == y_pred).mean()) if y_true.size else 0.0,
        "balanced_accuracy": float(0.5 * (rec0 + rec1)),
        "macro_f1": float(0.5 * (f1_0 + f1_1)),
    }


def threshold_sweep(y_true: np.ndarray, p1: np.ndarray) -> dict[str, Any]:
    rows = []
    best = None
    for t in np.round(np.arange(0.05, 0.951, 0.05), 2):
        pred = (p1 >= t).astype(int)
        m = metrics_from_preds_basic(y_true, pred)
        row = {
            "threshold": float(t),
            "macro_f1": m["macro_f1"],
            "balanced_accuracy": m["balanced_accuracy"],
            "accuracy": m["accuracy"],
            "pred_counts": {"0": int((pred == 0).sum()), "1": int((pred == 1).sum())},
            "one_class_pred": int((pred == 0).sum()) == 0 or int((pred == 1).sum()) == 0,
        }
        rows.append(row)
        key = (row["macro_f1"], row["balanced_accuracy"], -abs(t - 0.5))
        if best is None or key > best[0]:
            best = (key, row)
    return {"rows": rows, "best": best[1] if best else None}


def metrics_from_preds(y_true: np.ndarray, y_pred: np.ndarray, p1: np.ndarray | None = None) -> dict[str, Any]:
    y_true = y_true.astype(int)
    y_pred = y_pred.astype(int)
    c = confusion_counts(y_true, y_pred)
    basic = metrics_from_preds_basic(y_true, y_pred)
    counts = {str(k): int((y_pred == k).sum()) for k in [0, 1]}
    majority_label = int(np.bincount(y_true, minlength=2).argmax()) if y_true.size else 0
    majority_pred = np.full_like(y_true, majority_label)
    majority_basic = metrics_from_preds_basic(y_true, majority_pred)
    out = {
        **basic,
        "confusion": c,
        "pred_counts": counts,
        "one_class_pred": int((y_pred == 0).sum()) == 0 or int((y_pred == 1).sum()) == 0,
        "majority_baseline": {
            "label": majority_label,
            "accuracy": majority_basic["accuracy"],
            "macro_f1": majority_basic["macro_f1"],
        },
    }
    if p1 is not None:
        out["p1_summary"] = {
            "mean": float(np.mean(p1)),
            "std": float(np.std(p1)),
            "q05": float(np.quantile(p1, 0.05)),
            "median": float(np.quantile(p1, 0.50)),
            "q95": float(np.quantile(p1, 0.95)),
        }
        out["threshold_sweep"] = threshold_sweep(y_true, p1)
    return out


def make_folds(subjects: np.ndarray, n_folds: int, seed: int) -> list[np.ndarray]:
    subjects = np.asarray(sorted(set(int(s) for s in subjects)))
    rng = np.random.default_rng(seed)
    perm = rng.permutation(subjects)
    chunks = np.array_split(perm, n_folds)
    return [np.asarray(sorted(chunk.tolist()), dtype=int) for chunk in chunks if len(chunk)]


def label_column_or_scores(index_df: pd.DataFrame, task: str, policy: str) -> pd.Series:
    col = f"{task}_{policy}"
    if col in index_df.columns:
        return index_df[col].astype(float)
    score_col = f"{task}_score"
    if score_col not in index_df.columns:
        raise ValueError(f"Missing label source for {task}/{policy}")
    return index_df[score_col].map(lambda x: label_value(x, policy)).astype(float)


def align_indices(eeg_df: pd.DataFrame, bsl_df: pd.DataFrame) -> pd.DataFrame:
    if len(eeg_df) != len(bsl_df):
        raise ValueError(f"EEG index rows={len(eeg_df)} != BSL stats rows={len(bsl_df)}")
    checks = ["subject_id", "stimulus_id", "valence_score", "arousal_score"]
    mismatches = []
    for c in checks:
        if c in eeg_df.columns and c in bsl_df.columns:
            a = eeg_df[c].astype(str).fillna("NA").tolist()
            b = bsl_df[c].astype(str).fillna("NA").tolist()
            if a != b:
                mismatches.append(c)
    if mismatches:
        raise ValueError(f"EEG and BSL sidecar indices are not row-aligned for columns: {mismatches}")
    return eeg_df.copy()


class EEGWithBSLStatsDataset(Dataset):
    def __init__(
        self,
        eeg: np.ndarray,
        stats: np.ndarray,
        row_ids: np.ndarray,
        y: np.ndarray,
        stats_mean: np.ndarray,
        stats_std: np.ndarray,
        *,
        stats_zclip: float,
    ) -> None:
        self.eeg = eeg
        self.stats = stats
        self.row_ids = row_ids.astype(np.int64)
        self.y = y.astype(np.int64)
        self.stats_mean = stats_mean.astype(np.float32)
        self.stats_std = stats_std.astype(np.float32)
        self.stats_zclip = float(stats_zclip)

    def __len__(self) -> int:
        return int(len(self.row_ids))

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        row = int(self.row_ids[idx])
        x_eeg = np.asarray(self.eeg[row], dtype=np.float32)
        x_stats = np.asarray(self.stats[row], dtype=np.float32)
        x_stats = (x_stats - self.stats_mean) / self.stats_std
        if self.stats_zclip > 0:
            x_stats = np.clip(x_stats, -self.stats_zclip, self.stats_zclip)
        y = int(self.y[idx])
        return (
            torch.from_numpy(x_eeg.copy()),
            torch.from_numpy(x_stats.astype(np.float32, copy=True)),
            torch.tensor(y, dtype=torch.long),
            torch.tensor(row, dtype=torch.long),
        )


class TinyEEGBSLStatsNet(nn.Module):
    def __init__(self, n_stats: int, eeg_hidden_dim: int = 64, stats_hidden_dim: int = 32) -> None:
        super().__init__()
        self.eeg_encoder = nn.Sequential(
            nn.Conv1d(32, 32, kernel_size=9, padding=4),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(4),
            nn.Conv1d(32, 64, kernel_size=7, padding=3),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(4),
            nn.Conv1d(64, eeg_hidden_dim, kernel_size=5, padding=2),
            nn.BatchNorm1d(eeg_hidden_dim),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1),
            nn.Flatten(),
        )
        self.stats_encoder = nn.Sequential(
            nn.Linear(n_stats, stats_hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.10),
            nn.Linear(stats_hidden_dim, stats_hidden_dim),
            nn.ReLU(),
        )
        self.classifier = nn.Sequential(
            nn.Dropout(0.20),
            nn.Linear(eeg_hidden_dim + stats_hidden_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.20),
            nn.Linear(64, 2),
        )

    def forward(self, eeg: torch.Tensor, stats: torch.Tensor) -> torch.Tensor:
        h_eeg = self.eeg_encoder(eeg)
        h_stats = self.stats_encoder(stats)
        return self.classifier(torch.cat([h_eeg, h_stats], dim=1))


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def make_loader(
    dataset: Dataset,
    *,
    batch_size: int,
    shuffle: bool,
    y_for_sampler: np.ndarray | None = None,
) -> DataLoader:
    if y_for_sampler is not None:
        counts = np.bincount(y_for_sampler.astype(int), minlength=2).astype(np.float64)
        weights_per_class = np.where(counts > 0, 1.0 / counts, 0.0)
        sample_weights = weights_per_class[y_for_sampler.astype(int)]
        sampler = WeightedRandomSampler(sample_weights.tolist(), num_samples=len(sample_weights), replacement=True)
        return DataLoader(dataset, batch_size=batch_size, sampler=sampler, num_workers=0)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=0)


@torch.no_grad()
def evaluate(model: nn.Module, loader: DataLoader, device: torch.device) -> dict[str, Any]:
    model.eval()
    y_true_batches = []
    p1_batches = []
    row_batches = []
    for eeg, stats, y, rows in loader:
        eeg = eeg.to(device)
        stats = stats.to(device)
        logits = model(eeg, stats)
        prob = torch.softmax(logits, dim=1)[:, 1].detach().cpu().numpy()
        y_true_batches.append(y.numpy())
        p1_batches.append(prob)
        row_batches.append(rows.numpy())
    y_true = np.concatenate(y_true_batches) if y_true_batches else np.array([], dtype=int)
    p1 = np.concatenate(p1_batches) if p1_batches else np.array([], dtype=float)
    rows = np.concatenate(row_batches) if row_batches else np.array([], dtype=int)
    y_pred = (p1 >= 0.5).astype(int)
    out = metrics_from_preds(y_true, y_pred, p1)
    out["rows"] = rows.astype(int).tolist()
    out["y_true"] = y_true.astype(int).tolist()
    out["y_pred"] = y_pred.astype(int).tolist()
    out["p1"] = p1.astype(float).tolist()
    return out


def class_weights(y: np.ndarray, device: torch.device) -> torch.Tensor:
    counts = np.bincount(y.astype(int), minlength=2).astype(np.float32)
    total = float(counts.sum())
    weights = np.where(counts > 0, total / (2.0 * counts), 0.0)
    return torch.tensor(weights, dtype=torch.float32, device=device)


def strip_prediction_payload(metrics: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in metrics.items() if k not in {"rows", "y_true", "y_pred", "p1"}}


def run_one(
    *,
    run_id: int,
    task: str,
    policy: str,
    recipe: str,
    fold_id: int,
    seed: int,
    train_rows: np.ndarray,
    val_rows: np.ndarray,
    y_all: np.ndarray,
    eeg: np.ndarray,
    stats: np.ndarray,
    index_df: pd.DataFrame,
    args: argparse.Namespace,
    device: torch.device,
) -> dict[str, Any]:
    set_seed(seed)

    stats_train = np.asarray(stats[train_rows], dtype=np.float32)
    stats_mean = stats_train.mean(axis=0).astype(np.float32)
    stats_std = stats_train.std(axis=0).astype(np.float32)
    stats_std = np.where(stats_std < 1e-6, 1.0, stats_std).astype(np.float32)

    train_y = y_all[train_rows].astype(int)
    val_y = y_all[val_rows].astype(int)

    train_ds = EEGWithBSLStatsDataset(
        eeg, stats, train_rows, train_y, stats_mean, stats_std, stats_zclip=args.stats_zclip
    )
    val_ds = EEGWithBSLStatsDataset(
        eeg, stats, val_rows, val_y, stats_mean, stats_std, stats_zclip=args.stats_zclip
    )

    train_loader = make_loader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=(recipe != "balanced_sampler_ce"),
        y_for_sampler=train_y if recipe == "balanced_sampler_ce" else None,
    )
    eval_train_loader = make_loader(train_ds, batch_size=args.batch_size, shuffle=False)
    val_loader = make_loader(val_ds, batch_size=args.batch_size, shuffle=False)

    model = TinyEEGBSLStatsNet(
        n_stats=stats.shape[1],
        eeg_hidden_dim=args.eeg_hidden_dim,
        stats_hidden_dim=args.stats_hidden_dim,
    ).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    if recipe == "ce_class_weighted":
        criterion = nn.CrossEntropyLoss(weight=class_weights(train_y, device))
    else:
        criterion = nn.CrossEntropyLoss()

    history: list[dict[str, Any]] = []
    for epoch in range(1, args.epochs + 1):
        model.train()
        losses = []
        for eeg_batch, stats_batch, y_batch, _rows in train_loader:
            eeg_batch = eeg_batch.to(device)
            stats_batch = stats_batch.to(device)
            y_batch = y_batch.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(eeg_batch, stats_batch)
            loss = criterion(logits, y_batch)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach().cpu().item()))
        history.append({"epoch": epoch, "loss": float(np.mean(losses)) if losses else None})

    train_final = evaluate(model, eval_train_loader, device)
    final = evaluate(model, val_loader, device)

    run = {
        "run_id": run_id,
        "task": task,
        "policy": policy,
        "recipe": recipe,
        "fold_id": fold_id,
        "seed": seed,
        "val_subjects": sorted(index_df.iloc[val_rows]["subject_id"].astype(int).unique().tolist()),
        "train_n": int(len(train_rows)),
        "val_n": int(len(val_rows)),
        "train_label_counts": {str(k): int((train_y == k).sum()) for k in [0, 1]},
        "val_label_counts": {str(k): int((val_y == k).sum()) for k in [0, 1]},
        "stats_standardization": {
            "train_only": True,
            "std_floor": 1e-6,
            "zclip": args.stats_zclip,
            "train_stats_mean_global": float(stats_mean.mean()),
            "train_stats_std_global": float(stats_std.mean()),
        },
        "history": history,
        "train_final": strip_prediction_payload(train_final),
        "final": strip_prediction_payload(final),
        "prediction_rows": final["rows"],
        "prediction_y_true": final["y_true"],
        "prediction_y_pred": final["y_pred"],
        "prediction_p1": final["p1"],
    }

    print(json.dumps({
        "run_id": run_id,
        "task": task,
        "recipe": recipe,
        "fold": fold_id,
        "final_macro_f1": final["macro_f1"],
        "final_balanced_accuracy": final["balanced_accuracy"],
        "final_accuracy": final["accuracy"],
        "majority_accuracy": final["majority_baseline"]["accuracy"],
        "one_class_pred": final["one_class_pred"],
        "pred_counts": final["pred_counts"],
        "confusion": final["confusion"],
    }, sort_keys=True))

    return run


def aggregate_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        groups[(run["task"], run["policy"], run["recipe"])].append(run)

    rows = []
    for (task, policy, recipe), group in sorted(groups.items()):
        final_macro = [float(r["final"]["macro_f1"]) for r in group]
        final_bal = [float(r["final"]["balanced_accuracy"]) for r in group]
        final_acc = [float(r["final"]["accuracy"]) for r in group]
        majority_acc = [float(r["final"]["majority_baseline"]["accuracy"]) for r in group]
        threshold_macro = [float(r["final"]["threshold_sweep"]["best"]["macro_f1"]) for r in group]
        threshold_bal = [float(r["final"]["threshold_sweep"]["best"]["balanced_accuracy"]) for r in group]
        threshold_values = [float(r["final"]["threshold_sweep"]["best"]["threshold"]) for r in group]
        rows.append({
            "task": task,
            "policy": policy,
            "recipe": recipe,
            "runs": int(len(group)),
            "final_macro_f1": finite_summary(final_macro),
            "final_balanced_accuracy": finite_summary(final_bal),
            "final_accuracy": finite_summary(final_acc),
            "majority_accuracy": finite_summary(majority_acc),
            "threshold_best_macro_f1": finite_summary(threshold_macro),
            "threshold_best_balanced_accuracy": finite_summary(threshold_bal),
            "threshold_best_value": finite_summary(threshold_values),
            "threshold_gain_macro_f1": finite_summary([b - a for a, b in zip(final_macro, threshold_macro)]),
            "threshold_gain_balanced_accuracy": finite_summary([b - a for a, b in zip(final_bal, threshold_bal)]),
            "one_class_final_runs": int(sum(1 for r in group if r["final"]["one_class_pred"])),
            "threshold_one_class_final_runs": int(sum(1 for r in group if r["final"]["threshold_sweep"]["best"]["one_class_pred"])),
        })
    return rows


def write_predictions_csv(path: Path, runs: list[dict[str, Any]], index_df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run_id", "task", "policy", "recipe", "fold_id", "seed",
        "cache_row", "subject_id", "stimulus_id", "y_true", "y_pred", "p1",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for run in runs:
            for row_id, yt, yp, prob in zip(
                run["prediction_rows"],
                run["prediction_y_true"],
                run["prediction_y_pred"],
                run["prediction_p1"],
            ):
                meta = index_df.iloc[int(row_id)]
                writer.writerow({
                    "run_id": run["run_id"],
                    "task": run["task"],
                    "policy": run["policy"],
                    "recipe": run["recipe"],
                    "fold_id": run["fold_id"],
                    "seed": run["seed"],
                    "cache_row": int(row_id),
                    "subject_id": int(meta["subject_id"]),
                    "stimulus_id": meta.get("stimulus_id"),
                    "y_true": int(yt),
                    "y_pred": int(yp),
                    "p1": float(prob),
                })


def fmt(x: Any, digits: int = 4) -> str:
    if x is None:
        return "NA"
    try:
        value = float(x)
    except Exception:
        return str(x)
    if not math.isfinite(value):
        return "NA"
    return f"{value:.{digits}f}"


def build_report_md(report: dict[str, Any]) -> str:
    cfg = report["config"]
    lines: list[str] = []
    lines.append("# I-DARE EEG Response + BSL Stats Ablation Smoke\n")
    lines.append("This report was generated by `scripts/34_run_idare_eeg_bsl_stats_ablation_smoke.py`.\n")
    lines.append("No raw I-DARE EEG HDF5/MAT files were loaded inside training loops.\n")
    lines.append("## Inputs\n")
    lines.append(f"- eeg_npy: `{cfg['eeg_npy']}`")
    lines.append(f"- eeg_index: `{cfg['eeg_index']}`")
    lines.append(f"- bsl_stats_npy: `{cfg['bsl_stats_npy']}`")
    lines.append(f"- bsl_stats_index: `{cfg['bsl_stats_index']}`\n")
    lines.append("## Run Scope\n")
    lines.append(f"- label_policy: `{cfg['label_policy']}`")
    lines.append(f"- tasks: `{', '.join(cfg['tasks'])}`")
    lines.append(f"- recipes: `{', '.join(cfg['recipes'])}`")
    lines.append(f"- epochs: `{cfg['epochs']}`")
    lines.append(f"- max_runs: `{cfg['max_runs']}`")
    lines.append(f"- device: `{cfg['device']}`")
    lines.append(f"- model: `TinyEEGBSLStatsNet(eeg=[32,640], bsl_stats_dim={cfg['bsl_stats_dim']})`")
    lines.append(f"- BSL stats standardization: train-fold mean/std only, zclip `{cfg['stats_zclip']}`\n")
    lines.append("## Aggregate\n")
    lines.append("| Task | Policy | Recipe | Runs | Final macro F1 | Final bal acc | Final acc | Threshold macro F1 | Threshold bal acc | One-class final runs | Majority acc |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in report["aggregate"]:
        lines.append(
            f"| {row['task']} | {row['policy']} | {row['recipe']} | {row['runs']} | "
            f"{fmt(row['final_macro_f1']['mean'])} | {fmt(row['final_balanced_accuracy']['mean'])} | "
            f"{fmt(row['final_accuracy']['mean'])} | {fmt(row['threshold_best_macro_f1']['mean'])} | "
            f"{fmt(row['threshold_best_balanced_accuracy']['mean'])} | {row['one_class_final_runs']} | "
            f"{fmt(row['majority_accuracy']['mean'])} |"
        )
    lines.append("")
    lines.append("## Aggregate Threshold Diagnostics\n")
    lines.append("| Task | Policy | Recipe | Runs | Mean threshold | Macro F1 gain | Bal acc gain | Threshold one-class runs |")
    lines.append("|---|---|---|---:|---:|---:|---:|---:|")
    for row in report["aggregate"]:
        lines.append(
            f"| {row['task']} | {row['policy']} | {row['recipe']} | {row['runs']} | "
            f"{fmt(row['threshold_best_value']['mean'])} | {fmt(row['threshold_gain_macro_f1']['mean'])} | "
            f"{fmt(row['threshold_gain_balanced_accuracy']['mean'])} | {row['threshold_one_class_final_runs']} |"
        )
    lines.append("")
    lines.append("## Per-run Final Diagnostics\n")
    lines.append("| Run | Task | Recipe | Fold | Seed | Train n | Val n | Macro F1 | Bal acc | Acc | Pred 0 | Pred 1 | TN | FP | FN | TP | One-class | Majority acc |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|")
    for run in report["runs"]:
        f = run["final"]
        c = f["confusion"]
        pc = f["pred_counts"]
        lines.append(
            f"| {run['run_id']} | {run['task']} | {run['recipe']} | {run['fold_id']} | {run['seed']} | "
            f"{run['train_n']} | {run['val_n']} | {fmt(f['macro_f1'])} | {fmt(f['balanced_accuracy'])} | "
            f"{fmt(f['accuracy'])} | {pc.get('0', 0)} | {pc.get('1', 0)} | "
            f"{c['tn']} | {c['fp']} | {c['fn']} | {c['tp']} | {str(f['one_class_pred']).lower()} | "
            f"{fmt(f['majority_baseline']['accuracy'])} |"
        )
    lines.append("")
    lines.append("## Probability / Threshold Diagnostics\n")
    lines.append("| Run | Task | Recipe | P1 mean | P1 q05 | P1 median | P1 q95 | Best threshold | Best threshold macro F1 | Best threshold bal acc |")
    lines.append("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for run in report["runs"]:
        f = run["final"]
        p = f["p1_summary"]
        b = f["threshold_sweep"]["best"]
        lines.append(
            f"| {run['run_id']} | {run['task']} | {run['recipe']} | {fmt(p['mean'])} | "
            f"{fmt(p['q05'])} | {fmt(p['median'])} | {fmt(p['q95'])} | "
            f"{fmt(b['threshold'])} | {fmt(b['macro_f1'])} | {fmt(b['balanced_accuracy'])} |"
        )
    lines.append("")
    lines.append("## Notes\n")
    lines.append("- This is a smoke/stabilization report, not a final LOSO result.")
    lines.append("- Main EEG input is the existing baseline-corrected STIM-BSL response cache.")
    lines.append("- BSL stats are compact sidecar features, standardized with train-fold statistics only.")
    lines.append("- This is the first low-capacity baseline-aware I-DARE ablation before any full paired BSL/STIM neural model.\n")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    start_time = time.perf_counter()

    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_predictions_csv.parent.mkdir(parents=True, exist_ok=True)

    eeg = np.load(args.eeg_npy, mmap_mode="r")
    stats = np.load(args.bsl_stats_npy, mmap_mode="r")
    eeg_index = pd.read_csv(args.eeg_index)
    bsl_index = pd.read_csv(args.bsl_stats_index)
    index_df = align_indices(eeg_index, bsl_index)

    if tuple(eeg.shape[:2]) != (len(index_df), 32):
        raise ValueError(f"Unexpected EEG shape={eeg.shape} for index rows={len(index_df)}")
    if len(stats) != len(index_df):
        raise ValueError(f"Unexpected BSL stats shape={stats.shape} for index rows={len(index_df)}")
    if stats.shape[1] != 229:
        print(f"[WARN] expected BSL stats dim 229, got {stats.shape[1]}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    planned = []
    run_id = 0
    for seed in args.seeds:
        folds = make_folds(index_df["subject_id"].astype(int).unique(), args.folds, seed)
        for task in args.tasks:
            y_series = label_column_or_scores(index_df, task, args.label_policy)
            valid_mask = y_series.notna().to_numpy()
            y_all = y_series.fillna(-1).to_numpy(dtype=int)
            for fold_id, val_subjects in enumerate(folds, 1):
                val_mask = index_df["subject_id"].astype(int).isin(val_subjects).to_numpy()
                train_rows = np.where(valid_mask & ~val_mask)[0]
                val_rows = np.where(valid_mask & val_mask)[0]
                if len(train_rows) == 0 or len(val_rows) == 0:
                    continue
                for recipe in args.recipes:
                    run_id += 1
                    planned.append((run_id, task, args.label_policy, recipe, fold_id, seed, train_rows, val_rows, y_all))
                    if args.max_runs and len(planned) >= args.max_runs:
                        break
                if args.max_runs and len(planned) >= args.max_runs:
                    break
            if args.max_runs and len(planned) >= args.max_runs:
                break
        if args.max_runs and len(planned) >= args.max_runs:
            break

    print("[INFO] I-DARE EEG response + BSL stats ablation smoke")
    print(f"[INFO] eeg_npy={args.eeg_npy}")
    print(f"[INFO] eeg_index={args.eeg_index}")
    print(f"[INFO] bsl_stats_npy={args.bsl_stats_npy}")
    print(f"[INFO] bsl_stats_index={args.bsl_stats_index}")
    print(f"[INFO] eeg_shape={list(eeg.shape)}")
    print(f"[INFO] bsl_stats_shape={list(stats.shape)}")
    print(f"[INFO] label_policy={args.label_policy}")
    print(f"[INFO] tasks={args.tasks}")
    print(f"[INFO] recipes={args.recipes}")
    print(f"[INFO] epochs={args.epochs}")
    print(f"[INFO] max_runs={args.max_runs}")
    print(f"[INFO] device={device}")
    print(f"[INFO] planned_runs={len(planned)}")

    runs = []
    for i, item in enumerate(planned, 1):
        rid, task, policy, recipe, fold_id, seed, train_rows, val_rows, y_all = item
        val_subjects = sorted(index_df.iloc[val_rows]["subject_id"].astype(int).unique().tolist())
        print(
            f"[RUN] {i}/{len(planned)} task={task} policy={policy} recipe={recipe} "
            f"fold={fold_id} seed={seed} val_subjects={val_subjects}"
        )
        runs.append(run_one(
            run_id=rid,
            task=task,
            policy=policy,
            recipe=recipe,
            fold_id=fold_id,
            seed=seed,
            train_rows=train_rows,
            val_rows=val_rows,
            y_all=y_all,
            eeg=eeg,
            stats=stats,
            index_df=index_df,
            args=args,
            device=device,
        ))

    aggregate = aggregate_runs(runs)
    report = {
        "status": "PASSED",
        "generated_at_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "config": {
            "eeg_npy": args.eeg_npy,
            "eeg_index": args.eeg_index,
            "bsl_stats_npy": args.bsl_stats_npy,
            "bsl_stats_index": args.bsl_stats_index,
            "eeg_shape": list(eeg.shape),
            "bsl_stats_shape": list(stats.shape),
            "bsl_stats_dim": int(stats.shape[1]),
            "label_policy": args.label_policy,
            "tasks": args.tasks,
            "recipes": args.recipes,
            "folds": args.folds,
            "seeds": args.seeds,
            "epochs": args.epochs,
            "lr": args.lr,
            "batch_size": args.batch_size,
            "max_runs": args.max_runs,
            "device": str(device),
            "stats_zclip": args.stats_zclip,
            "representation": "baseline-corrected STIM-BSL EEG response cache + compact BSL stats sidecar",
            "raw_hdf5_loaded_in_training_loop": False,
        },
        "aggregate": aggregate,
        "runs": runs,
        "elapsed_sec": float(time.perf_counter() - start_time),
    }

    write_predictions_csv(args.out_predictions_csv, runs, index_df)
    args.out_json.write_text(json.dumps(safe_json(report), indent=2, ensure_ascii=False), encoding="utf-8")
    args.out_md.write_text(build_report_md(safe_json(report)), encoding="utf-8")

    print(f"[DONE] wrote {args.out_predictions_csv}")
    print(f"[DONE] wrote {args.out_md}")
    print(f"[DONE] wrote {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
