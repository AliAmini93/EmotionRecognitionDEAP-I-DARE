#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset


ROOT = Path(".")
EEG_CACHE = ROOT / ".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy"
INDEX_CSV = ROOT / ".cache/idare_eeg_cache_index_baseline_corrected.csv"
FIXED_PRED = ROOT / "docs/roca/idare_residual_physiology_feature_audit_current_predictions.csv"
LOCKED_06A4B = ROOT / "docs/roca/idare_06a4b_kshot_calibration_locked_bridge_confirm_current_decision_table.csv"
DEFAULT_HIGH_THRESHOLD = 2.2096774193548385


def seed_all(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = True


def first_existing_col(df: pd.DataFrame, names: list[str]) -> str | None:
    lower_to_real = {str(c).lower(): str(c) for c in df.columns}
    for name in names:
        if name.lower() in lower_to_real:
            return lower_to_real[name.lower()]
    return None


def pick_col_contains(df: pd.DataFrame, must: list[str], avoid: list[str] | None = None) -> str | None:
    avoid = avoid or []
    for col in df.columns:
        s = str(col).lower()
        if all(m.lower() in s for m in must) and not any(a.lower() in s for a in avoid):
            return str(col)
    return None


def to_float_array(x: pd.Series, n: int | None = None) -> np.ndarray:
    arr = pd.to_numeric(x, errors="coerce").to_numpy(dtype=np.float32)
    if n is not None and len(arr) != n:
        out = np.full(n, np.nan, dtype=np.float32)
        m = min(n, len(arr))
        out[:m] = arr[:m]
        return out
    return arr


def find_subject_col(df: pd.DataFrame) -> str:
    col = first_existing_col(df, ["subject_id", "subject", "sub", "participant", "participant_id"])
    if col is None:
        raise ValueError(f"Could not find subject column. columns={list(df.columns)}")
    return col


def find_stimulus_col(df: pd.DataFrame) -> str:
    col = first_existing_col(df, ["stimulus_id", "stimulus", "trial", "video_id", "clip_id"])
    if col is None:
        raise ValueError(f"Could not find stimulus column. columns={list(df.columns)}")
    return col


def find_score_col(df: pd.DataFrame, target: str) -> str:
    candidates = [
        f"{target}_score",
        target,
        f"score_{target}",
        f"rating_{target}",
        "score",
        "label",
        "y",
    ]
    col = first_existing_col(df, candidates)
    if col is None:
        col = pick_col_contains(df, [target, "score"])
    if col is None:
        raise ValueError(f"Could not find score column for target={target}. columns={list(df.columns)}")
    return col


def loso_stimulus_prior(index: pd.DataFrame, y: np.ndarray, subject_col: str, stimulus_col: str) -> np.ndarray:
    subjects = np.array(index[subject_col])
    stimuli = np.array(index[stimulus_col])
    prior = np.full(len(y), np.nan, dtype=np.float32)
    global_mean = float(np.nanmean(y))
    for subj in sorted(pd.unique(index[subject_col])):
        train = subjects != subj
        test = subjects == subj
        means = pd.DataFrame({"stim": stimuli[train], "y": y[train]}).groupby("stim")["y"].mean().to_dict()
        vals = [float(means.get(s, global_mean)) for s in stimuli[test]]
        prior[test] = np.asarray(vals, dtype=np.float32)
    return prior


def high_mask_from_residual(residual: np.ndarray, threshold: float) -> np.ndarray:
    return np.isfinite(residual) & (np.abs(residual) >= float(threshold))


def rmse(y: np.ndarray, p: np.ndarray) -> float:
    m = np.isfinite(y) & np.isfinite(p)
    if not np.any(m):
        return float("nan")
    return float(np.sqrt(np.mean((y[m] - p[m]) ** 2)))


def pearson(y: np.ndarray, p: np.ndarray) -> float:
    m = np.isfinite(y) & np.isfinite(p)
    if int(np.sum(m)) < 3:
        return float("nan")
    yy = y[m]
    pp = p[m]
    if float(np.std(yy)) <= 1e-12 or float(np.std(pp)) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(yy, pp)[0, 1])


def sign_acc(y: np.ndarray, p: np.ndarray) -> float:
    m = np.isfinite(y) & np.isfinite(p) & (y != 0)
    if not np.any(m):
        return float("nan")
    return float(np.mean(np.sign(y[m]) == np.sign(p[m])))


def get_locked_b2_rmse() -> float:
    if not LOCKED_06A4B.exists():
        return float("nan")
    try:
        df = pd.read_csv(LOCKED_06A4B)
        for col in ["locked_bridge_rmse_05ak", "best_candidate_rmse", "locked_bridge_rmse"]:
            if col in df.columns:
                vals = pd.to_numeric(df[col], errors="coerce").dropna()
                if len(vals):
                    return float(vals.iloc[0])
    except Exception:
        return float("nan")
    return float("nan")


def load_fixed_bandpower_prediction(index: pd.DataFrame, target: str, n: int) -> tuple[np.ndarray, dict[str, Any]]:
    info: dict[str, Any] = {
        "path": str(FIXED_PRED),
        "exists": FIXED_PRED.exists(),
        "loaded": False,
        "finite_rate": 0.0,
        "prediction_column": None,
        "model_filter": None,
        "merge_strategy": None,
        "columns": [],
        "error": None,
    }
    out = np.full(n, np.nan, dtype=np.float32)
    if not FIXED_PRED.exists():
        info["error"] = "missing fixed prediction file"
        return out, info

    try:
        df = pd.read_csv(FIXED_PRED)
        info["columns"] = [str(c) for c in df.columns]

        work = df.copy()
        if "target" in work.columns:
            cand = work[work["target"].astype(str).str.lower().eq(target.lower())]
            if len(cand):
                work = cand

        if "model" in work.columns:
            model_s = work["model"].astype(str).str.lower()
            masks = [
                model_s.str.contains("eeg", na=False) & model_s.str.contains("bandpower", na=False),
                model_s.str.contains("band", na=False),
                model_s.str.contains("fixed", na=False),
            ]
            for mask in masks:
                cand = work[mask]
                if len(cand) >= min(10, n):
                    work = cand.copy()
                    info["model_filter"] = str(cand["model"].iloc[0])
                    break

        pred_candidates = [
            "pred_residual", "residual_pred", "predicted_residual", "y_pred_residual",
            "dev_pred", "pred_dev", "prediction", "pred", "y_pred", "yhat", "model_pred",
            "pred_score", "score_pred", "prediction_score",
        ]
        pred_col = first_existing_col(work, pred_candidates)
        if pred_col is None:
            # Heuristic: choose a numeric column that looks like prediction, not truth/id/metric.
            numeric_cols = []
            for col in work.columns:
                s = str(col).lower()
                if any(bad in s for bad in ["true", "score", "label", "subject", "stim", "fold", "row", "index", "target", "model", "rmse", "mae", "acc", "auroc"]):
                    continue
                vals = pd.to_numeric(work[col], errors="coerce")
                finite = vals.notna().mean()
                if finite > 0.8:
                    numeric_cols.append(str(col))
            if numeric_cols:
                pred_col = numeric_cols[0]

        if pred_col is None:
            info["error"] = "could not infer prediction column"
            return out, info

        info["prediction_column"] = pred_col
        vals = pd.to_numeric(work[pred_col], errors="coerce").to_numpy(dtype=np.float32)

        # Direct row-order path, most ROCA prediction files use dataset order after filtering by model/target.
        if len(vals) == n:
            out = vals.astype(np.float32)
            info["merge_strategy"] = "row_order_after_filter"
        else:
            # Try merging by row-like keys.
            row_keys = ["row_id", "cache_row", "cache_index", "sample_id", "trial_index", "index"]
            left_key = first_existing_col(index, row_keys)
            right_key = first_existing_col(work, row_keys)
            if left_key and right_key:
                tmp = index[[left_key]].copy()
                tmp["__order"] = np.arange(n)
                rhs = work[[right_key, pred_col]].copy()
                merged = tmp.merge(rhs, left_on=left_key, right_on=right_key, how="left")
                out = pd.to_numeric(merged[pred_col], errors="coerce").to_numpy(dtype=np.float32)
                info["merge_strategy"] = f"key:{left_key}->{right_key}"
            else:
                out[: min(n, len(vals))] = vals[: min(n, len(vals))]
                info["merge_strategy"] = f"truncated_or_padded_len_{len(vals)}"

        finite_rate = float(np.isfinite(out).mean())
        info["finite_rate"] = finite_rate
        info["loaded"] = finite_rate > 0.8
        if not info["loaded"]:
            info["error"] = f"finite_rate too low: {finite_rate:.3f}"
        return out, info
    except Exception as exc:
        info["error"] = repr(exc)
        return out, info


class EEGResidualDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray, indices: np.ndarray, mean: np.ndarray, std: np.ndarray, gaussian_std: float, train: bool) -> None:
        self.x = x
        self.y = y.astype(np.float32)
        self.indices = np.asarray(indices, dtype=np.int64)
        self.mean = mean.astype(np.float32)
        self.std = std.astype(np.float32)
        self.gaussian_std = float(gaussian_std)
        self.train = bool(train)

    def __len__(self) -> int:
        return int(len(self.indices))

    def __getitem__(self, i: int):
        idx = int(self.indices[i])
        xx = (self.x[idx].astype(np.float32) - self.mean) / self.std
        if xx.ndim == 3 and xx.shape[0] == 1:
            xx = xx[0]
        if xx.ndim != 2:
            raise RuntimeError(f"Expected one EEG sample shaped [channels,time], got {xx.shape}")
        if self.train and self.gaussian_std > 0:
            xx = xx + np.random.normal(0.0, self.gaussian_std, size=xx.shape).astype(np.float32)
        xx = np.ascontiguousarray(xx, dtype=np.float32)
        yy = np.float32(self.y[idx])
        return torch.from_numpy(xx), torch.tensor(yy, dtype=torch.float32), idx


class TinyEEGAnchorNet(nn.Module):
    def __init__(self, n_channels: int = 32) -> None:
        super().__init__()
        self.spatial = nn.Sequential(
            nn.Conv1d(n_channels, 48, kernel_size=1, bias=False),
            nn.BatchNorm1d(48),
            nn.SiLU(),
        )
        self.temporal = nn.Sequential(
            nn.Conv1d(48, 64, kernel_size=9, padding=4, groups=1, bias=False),
            nn.BatchNorm1d(64),
            nn.SiLU(),
            nn.AvgPool1d(4),
            nn.Conv1d(64, 64, kernel_size=9, padding=4, groups=1, bias=False),
            nn.BatchNorm1d(64),
            nn.SiLU(),
            nn.AvgPool1d(4),
            nn.Conv1d(64, 96, kernel_size=7, padding=3, bias=False),
            nn.BatchNorm1d(96),
            nn.SiLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(96, 64),
            nn.SiLU(),
            nn.Dropout(0.10),
            nn.Linear(64, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if x.ndim == 4 and x.shape[1] == 1:
            x = x.squeeze(1)
        if x.ndim != 3:
            raise RuntimeError(f"Expected Conv1d input [batch,channels,time], got {tuple(x.shape)}")
        x = self.spatial(x)
        x = self.temporal(x)
        return self.head(x).squeeze(-1)


def choose_val_indices(train_idx: np.ndarray, subjects: np.ndarray, y: np.ndarray, seed: int, max_val_subjects: int = 8) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_subjects = sorted(pd.unique(subjects[train_idx]))
    rng.shuffle(train_subjects)
    n_val_subj = max(2, min(max_val_subjects, max(2, len(train_subjects) // 8)))
    val_subjects = set(train_subjects[:n_val_subj])
    val_idx = train_idx[np.isin(subjects[train_idx], list(val_subjects))]
    fit_idx = train_idx[~np.isin(subjects[train_idx], list(val_subjects))]
    if len(fit_idx) < 100 or len(val_idx) < 32:
        shuffled = train_idx.copy()
        rng.shuffle(shuffled)
        n_val = max(32, int(0.15 * len(shuffled)))
        val_idx = shuffled[:n_val]
        fit_idx = shuffled[n_val:]
    return fit_idx, val_idx


def train_one_fold(
    x: np.ndarray,
    y_resid: np.ndarray,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    subjects: np.ndarray,
    args: argparse.Namespace,
    method: str,
    gaussian_std: float,
    fold_seed: int,
    device: torch.device,
) -> tuple[np.ndarray, dict[str, Any]]:
    fit_idx, val_idx = choose_val_indices(train_idx, subjects, y_resid, seed=fold_seed)
    mean = np.nanmean(x[fit_idx], axis=(0, 2), keepdims=False).astype(np.float32)[:, None]
    std = np.nanstd(x[fit_idx], axis=(0, 2), keepdims=False).astype(np.float32)[:, None]
    std = np.where(std < 1e-6, 1.0, std).astype(np.float32)

    train_ds = EEGResidualDataset(x, y_resid, fit_idx, mean, std, gaussian_std=gaussian_std, train=True)
    val_ds = EEGResidualDataset(x, y_resid, val_idx, mean, std, gaussian_std=0.0, train=False)
    test_ds = EEGResidualDataset(x, y_resid, test_idx, mean, std, gaussian_std=0.0, train=False)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0, pin_memory=(device.type == "cuda"))
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0, pin_memory=(device.type == "cuda"))
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False, num_workers=0, pin_memory=(device.type == "cuda"))

    model = TinyEEGAnchorNet(n_channels=x.shape[1]).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    loss_fn = nn.HuberLoss(delta=1.0)

    best_state = None
    best_val = float("inf")
    best_epoch = -1
    history = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        train_losses = []
        for xb, yb, _ in train_loader:
            xb = xb.to(device, non_blocking=True)
            yb = yb.to(device, non_blocking=True)
            opt.zero_grad(set_to_none=True)
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            train_losses.append(float(loss.detach().cpu()))
        model.eval()
        val_losses = []
        with torch.no_grad():
            for xb, yb, _ in val_loader:
                xb = xb.to(device, non_blocking=True)
                yb = yb.to(device, non_blocking=True)
                pred = model(xb)
                val_losses.append(float(loss_fn(pred, yb).detach().cpu()))
        tr = float(np.mean(train_losses)) if train_losses else float("nan")
        va = float(np.mean(val_losses)) if val_losses else float("nan")
        history.append({"epoch": epoch, "train_loss": tr, "val_loss": va})
        if va < best_val:
            best_val = va
            best_epoch = epoch
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    pred_out = np.full(len(test_idx), np.nan, dtype=np.float32)
    pos = 0
    with torch.no_grad():
        for xb, _, idxb in test_loader:
            xb = xb.to(device, non_blocking=True)
            pp = model(xb).detach().cpu().numpy().astype(np.float32)
            pred_out[pos: pos + len(pp)] = pp
            pos += len(pp)

    meta = {
        "method": method,
        "gaussian_std": gaussian_std,
        "best_epoch": best_epoch,
        "best_val_loss": best_val,
        "fit_n": int(len(fit_idx)),
        "val_n": int(len(val_idx)),
        "test_n": int(len(test_idx)),
        "final_train_loss": history[-1]["train_loss"] if history else float("nan"),
        "final_val_loss": history[-1]["val_loss"] if history else float("nan"),
    }
    return pred_out, meta


def aggregate_metrics(df: pd.DataFrame, fixed_available: bool, locked_b2: float) -> pd.DataFrame:
    rows = []
    for method, g in df.groupby("method", sort=False):
        y = g["true_residual"].to_numpy(dtype=np.float32)
        p = g["pred_residual"].to_numpy(dtype=np.float32)
        fixed = g["fixed_bandpower_pred_residual"].to_numpy(dtype=np.float32) if "fixed_bandpower_pred_residual" in g.columns else np.full(len(g), np.nan)
        high = g["high_disagreement"].to_numpy(dtype=bool)
        yh = y[high]
        ph = p[high]
        fh = fixed[high]
        zero = np.zeros_like(yh)
        zero_rmse = rmse(yh, zero)
        model_rmse = rmse(yh, ph)
        fixed_rmse = rmse(yh, fh) if fixed_available else float("nan")
        rows.append({
            "method": method,
            "n_eval": int(len(g)),
            "n_high": int(np.sum(high)),
            "zero_rmse_high": zero_rmse,
            "model_rmse_high": model_rmse,
            "lift_vs_zero_high": zero_rmse - model_rmse if np.isfinite(zero_rmse) and np.isfinite(model_rmse) else float("nan"),
            "fixed_rmse_same_eval_high": fixed_rmse,
            "lift_vs_fixed_same_eval_high": fixed_rmse - model_rmse if np.isfinite(fixed_rmse) and np.isfinite(model_rmse) else float("nan"),
            "locked_bridge_rmse_05ak": locked_b2,
            "lift_vs_locked_bridge_rmse": locked_b2 - model_rmse if np.isfinite(locked_b2) and np.isfinite(model_rmse) else float("nan"),
            "pearson_high": pearson(yh, ph),
            "sign_acc_high": sign_acc(yh, ph),
        })
    return pd.DataFrame(rows).sort_values("model_rmse_high", ascending=True)


def subject_stats(pred_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (method, subj), g in pred_df.groupby(["method", "subject_id"], sort=False):
        high = g["high_disagreement"].to_numpy(dtype=bool)
        if not np.any(high):
            continue
        y = g.loc[high, "true_residual"].to_numpy(dtype=np.float32)
        p = g.loc[high, "pred_residual"].to_numpy(dtype=np.float32)
        rows.append({
            "method": method,
            "subject_id": subj,
            "n_high": int(len(y)),
            "zero_rmse_high": rmse(y, np.zeros_like(y)),
            "model_rmse_high": rmse(y, p),
            "improvement_zero_minus_model": rmse(y, np.zeros_like(y)) - rmse(y, p),
            "pearson_high": pearson(y, p),
            "sign_acc_high": sign_acc(y, p),
        })
    return pd.DataFrame(rows)


def df_to_md(df: pd.DataFrame) -> str:
    """Safe markdown-table writer; avoids tabulate and handles arrays/lists/dicts."""
    if df is None or df.empty:
        return "_No rows._"

    d = df.copy()

    def fmt(x):
        try:
            if hasattr(x, "tolist") and not isinstance(x, (str, bytes)):
                x = x.tolist()
        except Exception:
            pass

        if isinstance(x, (list, tuple, dict)):
            try:
                txt = json.dumps(x, ensure_ascii=False, default=str)
            except Exception:
                txt = str(x)
            txt = txt.replace("\n", " ").replace("|", "\\|")
            return txt[:237] + "..." if len(txt) > 240 else txt

        try:
            missing = pd.isna(x)
            if isinstance(missing, bool) and missing:
                return ""
            if hasattr(missing, "item"):
                try:
                    if bool(missing.item()):
                        return ""
                except Exception:
                    pass
        except Exception:
            pass

        if isinstance(x, float):
            return f"{x:.6g}"

        txt = str(x).replace("\n", " ").replace("|", "\\|")
        return txt[:237] + "..." if len(txt) > 240 else txt

    cols = [str(c).replace("|", "\\|") for c in d.columns]
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in d.iterrows():
        lines.append("| " + " | ".join(fmt(row[c]) for c in d.columns) + " |")
    return "\n".join(lines)


def write_outputs(prefix: Path, payload: dict[str, Any], decision: pd.DataFrame, method_metrics: pd.DataFrame, fold_metrics: pd.DataFrame, subj_stats: pd.DataFrame, pred_df: pd.DataFrame) -> None:
    prefix.parent.mkdir(parents=True, exist_ok=True)
    decision.to_csv(str(prefix) + "_decision_table.csv", index=False)
    method_metrics.to_csv(str(prefix) + "_method_metrics.csv", index=False)
    fold_metrics.to_csv(str(prefix) + "_fold_metrics.csv", index=False)
    subj_stats.to_csv(str(prefix) + "_subject_stats.csv", index=False)
    pred_df.to_csv(str(prefix) + "_predictions.csv", index=False)
    with open(str(prefix) + ".json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

    lines = []
    lines.append("# ROCA-I-DARE 06a6 Neural Anchor Against Fixed EEG-Bandpower")
    lines.append("")
    lines.append("Purpose: check whether the raw-EEG neural pipeline can recover the simple fixed EEG-bandpower residual signal under LOSO.")
    lines.append("")
    lines.append("## Decision")
    lines.append(df_to_md(decision))
    lines.append("")
    lines.append("## Method metrics")
    lines.append(df_to_md(method_metrics))
    lines.append("")
    lines.append("## Fixed bandpower loading audit")
    lines.append(df_to_md(pd.DataFrame([payload.get("fixed_bandpower_info", {})])))
    lines.append("")
    lines.append("## Fold metrics preview")
    lines.append(df_to_md(fold_metrics.head(20)))
    lines.append("")
    lines.append("## Interpretation guide")
    lines.append("- If neural LOSO is worse than fixed EEG-bandpower, the neural pipeline is not anchored and larger CNN search is unsafe.")
    lines.append("- If neural matches fixed EEG-bandpower but still loses to locked B2, the problem is calibration/subject-style dominance, not architecture size.")
    lines.append("- If neural beats fixed and locked B2, promote it to a confirmatory multi-seed run.")
    Path(str(prefix) + ".md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="arousal")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--smoke-subjects", type=int, default=6)
    ap.add_argument("--batch-size", type=int, default=96)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--weight-decay", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=7066)
    ap.add_argument("--high-threshold", type=float, default=DEFAULT_HIGH_THRESHOLD)
    ap.add_argument("--out-prefix", default=None)
    args = ap.parse_args()

    seed_all(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] device={device}")
    if device.type == "cuda":
        print(f"[INFO] gpu={torch.cuda.get_device_name(0)}")

    x = np.load(EEG_CACHE, mmap_mode="r")
    index = pd.read_csv(INDEX_CSV)
    n = len(index)
    print(f"[INFO] cache={EEG_CACHE} shape={x.shape}")
    print(f"[INFO] index={INDEX_CSV} rows={n}")
    if x.shape[0] != n:
        raise ValueError(f"cache rows {x.shape[0]} != index rows {n}")

    subject_col = find_subject_col(index)
    stimulus_col = find_stimulus_col(index)
    score_col = find_score_col(index, args.target)
    y_score = pd.to_numeric(index[score_col], errors="coerce").to_numpy(dtype=np.float32)
    subjects = np.asarray(index[subject_col])
    stimuli = np.asarray(index[stimulus_col])

    stim_prior = loso_stimulus_prior(index, y_score, subject_col, stimulus_col)
    y_resid = (y_score - stim_prior).astype(np.float32)
    high = high_mask_from_residual(y_resid, args.high_threshold)
    print(f"[INFO] target={args.target} score_col={score_col} high_threshold={args.high_threshold:.6f} high_n={int(high.sum())}")

    fixed_pred, fixed_info = load_fixed_bandpower_prediction(index, args.target, n)
    fixed_available = bool(fixed_info.get("loaded", False))
    print(f"[INFO] fixed_bandpower_loaded={fixed_available} finite_rate={fixed_info.get('finite_rate')}")
    print(f"[INFO] fixed_bandpower_prediction_column={fixed_info.get('prediction_column')} strategy={fixed_info.get('merge_strategy')}")
    if fixed_info.get("error"):
        print(f"[WARN] fixed bandpower load issue: {fixed_info.get('error')}")

    locked_b2 = get_locked_b2_rmse()
    print(f"[INFO] locked_bridge_rmse_05ak={locked_b2}")

    all_subjects = sorted(pd.unique(index[subject_col]))
    if args.smoke:
        all_subjects = all_subjects[: args.smoke_subjects]
    methods = [
        ("neural_noaug_anchor", 0.0),
        ("neural_gaussian_0p10_anchor", 0.10),
    ]

    pred_rows = []
    fold_rows = []
    for method, gaussian_std in methods:
        print("\n" + "=" * 90)
        print(f"[METHOD] {method} gaussian_std={gaussian_std}")
        print("=" * 90)
        for fold_i, subj in enumerate(all_subjects, start=1):
            test_idx = np.where(subjects == subj)[0]
            train_idx = np.where(subjects != subj)[0]
            print(f"[fold {fold_i}/{len(all_subjects)}] method={method} test_subject={subj} train={len(train_idx)} test={len(test_idx)}")
            pred, meta = train_one_fold(
                x=x,
                y_resid=y_resid,
                train_idx=train_idx,
                test_idx=test_idx,
                subjects=subjects,
                args=args,
                method=method,
                gaussian_std=gaussian_std,
                fold_seed=args.seed + fold_i * 100 + int(abs(hash(method)) % 97),
                device=device,
            )
            test_high = high[test_idx]
            yy = y_resid[test_idx]
            fixed_test = fixed_pred[test_idx]
            fold_rows.append({
                **meta,
                "fold": fold_i,
                "subject_id": subj,
                "n_high": int(test_high.sum()),
                "zero_rmse_high": rmse(yy[test_high], np.zeros(int(test_high.sum()), dtype=np.float32)),
                "model_rmse_high": rmse(yy[test_high], pred[test_high]),
                "fixed_rmse_high": rmse(yy[test_high], fixed_test[test_high]) if fixed_available else float("nan"),
                "pearson_high": pearson(yy[test_high], pred[test_high]),
                "sign_acc_high": sign_acc(yy[test_high], pred[test_high]),
            })
            for local_pos, row_idx in enumerate(test_idx):
                pred_rows.append({
                    "method": method,
                    "row_index": int(row_idx),
                    "subject_id": subjects[row_idx],
                    "stimulus_id": stimuli[row_idx],
                    "score": float(y_score[row_idx]),
                    "stimulus_prior_loso": float(stim_prior[row_idx]),
                    "true_residual": float(y_resid[row_idx]),
                    "pred_residual": float(pred[local_pos]),
                    "fixed_bandpower_pred_residual": float(fixed_pred[row_idx]) if np.isfinite(fixed_pred[row_idx]) else float("nan"),
                    "high_disagreement": bool(high[row_idx]),
                })

    pred_df = pd.DataFrame(pred_rows)
    fold_metrics = pd.DataFrame(fold_rows)
    method_metrics = aggregate_metrics(pred_df, fixed_available=fixed_available, locked_b2=locked_b2)
    subj = subject_stats(pred_df)

    # Method deltas.
    noaug_rmse = method_metrics.loc[method_metrics["method"].eq("neural_noaug_anchor"), "model_rmse_high"]
    gauss_rmse = method_metrics.loc[method_metrics["method"].eq("neural_gaussian_0p10_anchor"), "model_rmse_high"]
    noaug_val = float(noaug_rmse.iloc[0]) if len(noaug_rmse) else float("nan")
    gauss_val = float(gauss_rmse.iloc[0]) if len(gauss_rmse) else float("nan")
    gaussian_delta = noaug_val - gauss_val if np.isfinite(noaug_val) and np.isfinite(gauss_val) else float("nan")

    best = method_metrics.iloc[0].to_dict() if len(method_metrics) else {}
    best_method = best.get("method", "")
    best_lift_zero = float(best.get("lift_vs_zero_high", float("nan")))
    best_lift_fixed = float(best.get("lift_vs_fixed_same_eval_high", float("nan")))
    best_lift_b2 = float(best.get("lift_vs_locked_bridge_rmse", float("nan")))

    practical_zero = bool(np.isfinite(best_lift_zero) and best_lift_zero > 0.05)
    fixed_gate = bool(fixed_available and np.isfinite(best_lift_fixed) and best_lift_fixed > 0.02)
    b2_gate = bool(np.isfinite(best_lift_b2) and best_lift_b2 > 0.02)
    anchor_gate = bool(fixed_available and np.isfinite(best_lift_fixed) and best_lift_fixed >= -0.05)

    if b2_gate:
        decision_code = "GO_NEURAL_ANCHOR_BEATS_LOCKED_B2_CONFIRM_MULTI_SEED"
        interp = "Neural raw-EEG anchor beats locked B2 on the high-disagreement residual gate. This requires a stricter multi-seed confirmatory rerun."
        action = "Run multi-seed confirmation with paired bootstrap, fixed reference checks, and locked reporting."
    elif anchor_gate:
        decision_code = "ANCHOR_OK_BUT_RESIDUAL_GATE_REMAINS_CALIBRATION_DOMINANT"
        interp = "The neural pipeline is close to the fixed EEG-bandpower reference, but still does not beat locked B2. Architecture alone is not the main bottleneck."
        action = "Stop blind CNN/augmentation search; frame the result as calibration-dominant and only pursue explicitly calibrated/personalized models."
    elif practical_zero:
        decision_code = "WEAK_NEURAL_SIGNAL_BUT_NOT_ANCHORED_TO_FIXED_REFERENCE"
        interp = "The neural model beats zero slightly, but it does not reproduce the fixed EEG-bandpower reference. This suggests a neural pipeline/training representation issue."
        action = "Debug the neural input/target pipeline before any larger model: loss scale, target construction, validation split, and feature anchor distillation."
    else:
        decision_code = "NO_GO_NEURAL_PIPELINE_NOT_ANCHORED"
        interp = "The neural raw-EEG pipeline does not beat the practical gates under LOSO. This supports the diagnosis: weak residual identifiability plus subject calibration/domain shift."
        action = "Finalize the calibration-dominant negative result, unless a separate distillation/feature-anchor test is intentionally added."

    decision = pd.DataFrame([{
        "target": args.target,
        "decision": decision_code,
        "best_method": best_method,
        "best_model_rmse_high": best.get("model_rmse_high", float("nan")),
        "best_lift_vs_zero_high": best_lift_zero,
        "fixed_bandpower_loaded": fixed_available,
        "best_lift_vs_fixed_same_eval_high": best_lift_fixed,
        "best_lift_vs_locked_bridge_rmse": best_lift_b2,
        "gaussian_delta_rmse_vs_noaug_positive_means_help": gaussian_delta,
        "passes_zero_gate": practical_zero,
        "passes_fixed_reference_gate": fixed_gate,
        "passes_locked_bridge_gate": b2_gate,
        "anchor_close_to_fixed_reference_gate": anchor_gate,
        "interpretation": interp,
        "recommended_next_action": action,
    }])

    prefix = Path(args.out_prefix) if args.out_prefix else ROOT / f"docs/roca/idare_06a6_neural_anchor_fixed_bandpower_{'smoke_' if args.smoke else ''}current"
    payload = {
        "args": vars(args),
        "cache": {"path": str(EEG_CACHE), "shape": list(x.shape)},
        "index": {"path": str(INDEX_CSV), "rows": n, "subject_col": subject_col, "stimulus_col": stimulus_col, "score_col": score_col},
        "high_threshold": args.high_threshold,
        "high_n": int(high.sum()),
        "fixed_bandpower_info": fixed_info,
        "locked_bridge_rmse_05ak": locked_b2,
        "decision": decision.to_dict(orient="records"),
        "method_metrics": method_metrics.to_dict(orient="records"),
    }
    write_outputs(prefix, payload, decision, method_metrics, fold_metrics, subj, pred_df)

    print("\nROCA step 06a6 completed.")
    for suffix in [".md", ".json", "_decision_table.csv", "_method_metrics.csv", "_fold_metrics.csv", "_subject_stats.csv", "_predictions.csv"]:
        print(f"wrote: {prefix}{suffix}")
    print("\nDecision table:")
    print(decision.to_string(index=False))
    print("\nMethod metrics:")
    print(method_metrics.to_string(index=False))
    print("\nFixed bandpower audit:")
    print(pd.DataFrame([fixed_info]).to_string(index=False))


if __name__ == "__main__":
    main()
