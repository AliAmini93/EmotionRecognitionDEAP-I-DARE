#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import numpy as np
import pandas as pd

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader


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


def pearson(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3:
        return float("nan")
    a = a[m]
    b = b[m]
    if np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def rmse(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() == 0:
        return float("nan")
    return float(np.sqrt(np.mean((a[m] - b[m]) ** 2)))


def sign_acc(y, p) -> float:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p) & (np.abs(y) > 1e-12)
    if m.sum() == 0:
        return float("nan")
    return float(np.mean(np.sign(y[m]) == np.sign(p[m])))


def df_to_md(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_No rows._"
    d = df.copy()
    def fmt(x):
        if pd.isna(x):
            return ""
        if isinstance(x, float):
            return f"{x:.6g}"
        return str(x).replace("\n", " ").replace("|", "\\|")
    cols = [str(c).replace("|", "\\|") for c in d.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in d.iterrows():
        lines.append("| " + " | ".join(fmt(row[c]) for c in d.columns) + " |")
    return "\n".join(lines)


def load_high_threshold() -> float:
    for p in [
        LOCKED_06A4B,
        ROOT / "docs/roca/idare_06a4_subject_normalization_domain_adaptation_current_decision_table.csv",
    ]:
        if p.exists():
            try:
                df = pd.read_csv(p)
                if "high_threshold" in df.columns and len(df):
                    v = float(df["high_threshold"].dropna().iloc[0])
                    return v
            except Exception:
                pass
    return DEFAULT_HIGH_THRESHOLD


def load_locked_bridge_rmse() -> float:
    if LOCKED_06A4B.exists():
        try:
            df = pd.read_csv(LOCKED_06A4B)
            if "locked_bridge_rmse_05ak" in df.columns and len(df):
                return float(df["locked_bridge_rmse_05ak"].dropna().iloc[0])
        except Exception:
            pass
    return float("nan")


def find_col(cols, candidates):
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    for c in cols:
        cl = c.lower()
        for cand in candidates:
            if cand.lower() in cl:
                return c
    return None


def load_fixed_residual_predictions(n: int) -> np.ndarray:
    arr = np.full(n, np.nan, dtype=np.float32)
    if not FIXED_PRED.exists():
        return arr
    try:
        df = pd.read_csv(FIXED_PRED)
    except Exception:
        return arr

    if "target" in df.columns:
        df = df[df["target"].astype(str).str.lower().eq("arousal")].copy()
    if "model" in df.columns:
        hit = df[df["model"].astype(str).str.lower().str.contains("eeg_bandpower", na=False)].copy()
        if len(hit) >= n:
            df = hit

    pred_col = find_col(
        df.columns,
        [
            "pred_residual", "residual_pred", "y_residual_pred", "resid_pred",
            "dev_pred", "prediction_residual", "y_pred_residual", "residual_prediction"
        ],
    )
    if pred_col is None:
        return arr

    idx_col = find_col(df.columns, ["row_id", "sample_index", "trial_index", "cache_row", "index"])
    vals = pd.to_numeric(df[pred_col], errors="coerce").to_numpy(dtype=np.float32)

    if idx_col is not None:
        idx = pd.to_numeric(df[idx_col], errors="coerce").to_numpy()
        ok = np.isfinite(idx) & (idx >= 0) & (idx < n)
        arr[idx[ok].astype(int)] = vals[ok]
    elif len(vals) == n:
        arr[:] = vals
    elif len(vals) > n:
        arr[:] = vals[:n]
    return arr


class EEGDataset(Dataset):
    def __init__(self, x, indices, y_scaled, ch_mean, ch_std, gaussian_std: float = 0.0):
        self.x = x
        self.indices = np.asarray(indices, dtype=np.int64)
        self.y = np.asarray(y_scaled, dtype=np.float32)
        self.ch_mean = ch_mean.astype(np.float32)
        self.ch_std = ch_std.astype(np.float32)
        self.gaussian_std = float(gaussian_std)

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, j):
        i = int(self.indices[j])
        xx = np.array(self.x[i], dtype=np.float32, copy=True)
        xx = (xx - self.ch_mean[:, None]) / self.ch_std[:, None]
        xt = torch.from_numpy(xx)
        if self.gaussian_std > 0:
            xt = xt + torch.randn_like(xt) * self.gaussian_std
        return xt, torch.tensor(self.y[j], dtype=torch.float32)


class EEGSmallCNN(nn.Module):
    def __init__(self, in_ch=32):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv1d(in_ch, 64, kernel_size=15, padding=7),
            nn.BatchNorm1d(64),
            nn.SiLU(),
            nn.Conv1d(64, 64, kernel_size=9, padding=4, groups=8),
            nn.BatchNorm1d(64),
            nn.SiLU(),
            nn.Conv1d(64, 96, kernel_size=9, padding=4),
            nn.BatchNorm1d(96),
            nn.SiLU(),
            nn.AdaptiveAvgPool1d(1),
        )
        self.head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(96, 64),
            nn.SiLU(),
            nn.Dropout(0.15),
            nn.Linear(64, 1),
        )

    def forward(self, x):
        return self.head(self.net(x)).squeeze(-1)


def stimulus_prior_from_fit(stim, y, fit_idx):
    fit_idx = np.asarray(fit_idx, dtype=np.int64)
    global_mean = float(np.mean(y[fit_idx]))
    pri = {}
    for s in np.unique(stim[fit_idx]):
        m = fit_idx[stim[fit_idx] == s]
        pri[s] = float(np.mean(y[m])) if len(m) else global_mean
    return pri, global_mean


def apply_prior(stim, pri, global_mean):
    return np.array([pri.get(s, global_mean) for s in stim], dtype=np.float32)


def train_one_fold(
    x,
    df,
    subjects,
    stim,
    y,
    test_subject,
    fold_i,
    method,
    gaussian_std,
    epochs,
    batch_size,
    device,
    seed,
):
    seed_all(seed + fold_i)

    test_idx = np.flatnonzero(subjects == test_subject)
    train_subjects = sorted([s for s in np.unique(subjects) if s != test_subject])
    val_subject = train_subjects[(fold_i * 13) % len(train_subjects)]

    val_idx = np.flatnonzero(subjects == val_subject)
    fit_idx = np.flatnonzero((subjects != test_subject) & (subjects != val_subject))

    pri, global_mean = stimulus_prior_from_fit(stim, y, fit_idx)
    prior_all = apply_prior(stim, pri, global_mean)
    resid_all = y - prior_all

    fit_resid = resid_all[fit_idx]
    resid_mean = float(np.mean(fit_resid))
    resid_std = float(np.std(fit_resid) + 1e-6)

    y_fit_scaled = (resid_all[fit_idx] - resid_mean) / resid_std
    y_val_scaled = (resid_all[val_idx] - resid_mean) / resid_std

    fit_x = np.asarray(x[fit_idx], dtype=np.float32)
    ch_mean = fit_x.mean(axis=(0, 2))
    ch_std = fit_x.std(axis=(0, 2)) + 1e-6

    train_ds = EEGDataset(x, fit_idx, y_fit_scaled, ch_mean, ch_std, gaussian_std=gaussian_std)
    val_ds = EEGDataset(x, val_idx, y_val_scaled, ch_mean, ch_std, gaussian_std=0.0)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0, drop_last=False)

    model = EEGSmallCNN(in_ch=x.shape[1]).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-3)
    loss_fn = nn.HuberLoss(delta=1.0)

    best_loss = float("inf")
    best_state = None
    patience = 3
    bad = 0

    for ep in range(1, epochs + 1):
        model.train()
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            opt.zero_grad(set_to_none=True)
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()

        model.eval()
        vals = []
        with torch.no_grad():
            for xb, yb in val_loader:
                xb = xb.to(device)
                yb = yb.to(device)
                vals.append(float(loss_fn(model(xb), yb).detach().cpu()))
        val_loss = float(np.mean(vals)) if vals else float("inf")

        if val_loss < best_loss - 1e-5:
            best_loss = val_loss
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            bad = 0
        else:
            bad += 1
        if bad >= patience:
            break

    if best_state is not None:
        model.load_state_dict(best_state)

    test_ds = EEGDataset(
        x,
        test_idx,
        (resid_all[test_idx] - resid_mean) / resid_std,
        ch_mean,
        ch_std,
        gaussian_std=0.0,
    )
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    pred_scaled = []
    model.eval()
    with torch.no_grad():
        for xb, _ in test_loader:
            xb = xb.to(device)
            pred_scaled.append(model(xb).detach().cpu().numpy())
    pred_scaled = np.concatenate(pred_scaled).astype(np.float32)
    pred_resid = pred_scaled * resid_std + resid_mean

    out = pd.DataFrame(
        {
            "row_id": test_idx,
            "subject_id": subjects[test_idx],
            "stimulus_id": stim[test_idx],
            "target": "arousal",
            "method": method,
            "fold": fold_i,
            "test_subject": test_subject,
            "val_subject": val_subject,
            "score_true": y[test_idx],
            "stimulus_prior": prior_all[test_idx],
            "residual_true": resid_all[test_idx],
            "residual_pred": pred_resid,
            "best_val_loss": best_loss,
        }
    )
    return out


def summarize_predictions(preds, fixed_pred, high_threshold, locked_rmse):
    rows = []
    subject_rows = []
    for method, g in preds.groupby("method"):
        resid_true = g["residual_true"].to_numpy(float)
        pred = g["residual_pred"].to_numpy(float)
        row_ids = g["row_id"].to_numpy(int)
        high = np.abs(resid_true) >= high_threshold

        fixed = fixed_pred[row_ids]
        fixed_ok = np.isfinite(fixed)

        zero_rmse = rmse(resid_true[high], np.zeros(high.sum()))
        model_rmse = rmse(resid_true[high], pred[high])
        fixed_rmse = rmse(resid_true[high & fixed_ok], fixed[high & fixed_ok]) if np.any(high & fixed_ok) else float("nan")

        rows.append(
            {
                "method": method,
                "n_eval": int(len(g)),
                "n_high": int(high.sum()),
                "high_threshold": high_threshold,
                "zero_rmse_high": zero_rmse,
                "model_rmse_high": model_rmse,
                "lift_vs_zero_high": zero_rmse - model_rmse,
                "fixed_rmse_same_eval_high": fixed_rmse,
                "lift_vs_fixed_same_eval_high": fixed_rmse - model_rmse if np.isfinite(fixed_rmse) else float("nan"),
                "locked_bridge_rmse_05ak": locked_rmse,
                "lift_vs_locked_bridge_rmse": locked_rmse - model_rmse if np.isfinite(locked_rmse) else float("nan"),
                "pearson_high": pearson(resid_true[high], pred[high]),
                "sign_acc_high": sign_acc(resid_true[high], pred[high]),
            }
        )

        for sid, sg in g.groupby("subject_id"):
            rt = sg["residual_true"].to_numpy(float)
            pp = sg["residual_pred"].to_numpy(float)
            h = np.abs(rt) >= high_threshold
            if h.sum() == 0:
                continue
            subject_rows.append(
                {
                    "method": method,
                    "subject_id": sid,
                    "n_high": int(h.sum()),
                    "zero_rmse_high": rmse(rt[h], np.zeros(h.sum())),
                    "model_rmse_high": rmse(rt[h], pp[h]),
                    "improvement_zero_minus_model": rmse(rt[h], np.zeros(h.sum())) - rmse(rt[h], pp[h]),
                    "pearson_high": pearson(rt[h], pp[h]),
                    "sign_acc_high": sign_acc(rt[h], pp[h]),
                }
            )

    metrics = pd.DataFrame(rows).sort_values("model_rmse_high")
    subj = pd.DataFrame(subject_rows)
    return metrics, subj


def make_decision(metrics):
    if metrics.empty:
        return pd.DataFrame([{"target": "arousal", "decision": "NO_METRICS"}])

    best = metrics.iloc[0].to_dict()
    gaussian = metrics[metrics["method"].eq("gaussian_0p10")]
    noaug = metrics[metrics["method"].eq("none_noaug_control")]

    gaussian_delta_vs_noaug = float("nan")
    if len(gaussian) and len(noaug):
        gaussian_delta_vs_noaug = float(noaug.iloc[0]["model_rmse_high"] - gaussian.iloc[0]["model_rmse_high"])

    passes_zero = bool(best.get("lift_vs_zero_high", float("nan")) > 0.03)
    passes_fixed = bool(best.get("lift_vs_fixed_same_eval_high", float("nan")) > 0.03)
    passes_locked = bool(best.get("lift_vs_locked_bridge_rmse", float("nan")) > 0.03)

    if passes_locked and passes_fixed:
        decision = "GO_AUGMENTATION_BEATS_FIXED_AND_LOCKED_GATE"
        interpretation = "Train-only gaussian augmentation produced a clean locked-gate improvement beyond fixed EEG-bandpower and locked B2."
        action = "Promote gaussian_0p10 to confirmatory multi-seed paired bootstrap and locked B2 bridge report."
    elif passes_fixed:
        decision = "PARTIAL_GO_AUGMENTATION_BEATS_FIXED_NOT_LOCKED_B2"
        interpretation = "Augmentation improves the physiology residual model beyond fixed EEG-bandpower but still does not beat locked B2."
        action = "Do not claim final improvement over personalization; run multi-seed confirmation or frame as calibration-dominant."
    elif passes_zero:
        decision = "WEAK_AUGMENTATION_BEATS_ZERO_ONLY"
        interpretation = "Augmentation gives some residual signal but not enough to beat the fixed reference or locked B2."
        action = "Stop deep augmentation search unless the neural anchor can reproduce fixed bandpower robustly."
    else:
        decision = "NO_GO_AUGMENTATION_DOES_NOT_FIX_LOSO"
        interpretation = "Clean locked-gate gaussian augmentation does not solve the LOSO residual problem."
        action = "Finalize diagnosis: weak residual identifiability plus subject calibration/domain shift; avoid further blind architecture search."

    return pd.DataFrame(
        [
            {
                "target": "arousal",
                "decision": decision,
                "best_method": best.get("method"),
                "best_model_rmse_high": best.get("model_rmse_high"),
                "best_lift_vs_zero_high": best.get("lift_vs_zero_high"),
                "best_lift_vs_fixed_same_eval_high": best.get("lift_vs_fixed_same_eval_high"),
                "best_lift_vs_locked_bridge_rmse": best.get("lift_vs_locked_bridge_rmse"),
                "gaussian_delta_rmse_vs_noaug": gaussian_delta_vs_noaug,
                "passes_zero_gate": passes_zero,
                "passes_fixed_reference_gate": passes_fixed,
                "passes_locked_bridge_gate": passes_locked,
                "interpretation": interpretation,
                "recommended_next_action": action,
            }
        ]
    )


def write_report(prefix, decision, metrics, folds, subj, preds, args, device, locked_rmse):
    payload = {
        "args": vars(args),
        "device": str(device),
        "locked_bridge_rmse_05ak": locked_rmse,
        "decision": decision.to_dict(orient="records"),
        "method_metrics": metrics.to_dict(orient="records"),
        "fold_metrics": folds.to_dict(orient="records"),
        "subject_stats": subj.to_dict(orient="records"),
    }
    Path(str(prefix) + ".json").write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    decision.to_csv(str(prefix) + "_decision_table.csv", index=False)
    metrics.to_csv(str(prefix) + "_method_metrics.csv", index=False)
    folds.to_csv(str(prefix) + "_fold_metrics.csv", index=False)
    subj.to_csv(str(prefix) + "_subject_stats.csv", index=False)
    preds.to_csv(str(prefix) + "_predictions.csv", index=False)

    lines = []
    lines.append("# ROCA 06a5b Gaussian10 locked-gate rerun")
    lines.append("")
    lines.append("Clean rerun of prior `gaussian_0p10` evidence under the current residual high-disagreement gate.")
    lines.append("")
    lines.append("- no test-label checkpointing")
    lines.append("- subject-level validation inside each LOSO fold")
    lines.append("- train-only Gaussian noise augmentation")
    lines.append("- compared against zero residual, fixed EEG-bandpower, and locked B2 scalar")
    lines.append("")
    lines.append("## Decision")
    lines.append(df_to_md(decision))
    lines.append("")
    lines.append("## Method metrics")
    lines.append(df_to_md(metrics))
    lines.append("")
    lines.append("## Fold metrics preview")
    lines.append(df_to_md(folds.head(30)))
    lines.append("")
    lines.append("## Subject stats preview")
    lines.append(df_to_md(subj.head(40)))
    Path(str(prefix) + ".md").write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--seed", type=int, default=2605)
    args = ap.parse_args()

    seed_all(args.seed)

    if not EEG_CACHE.exists():
        raise FileNotFoundError(EEG_CACHE)
    if not INDEX_CSV.exists():
        raise FileNotFoundError(INDEX_CSV)

    x = np.load(EEG_CACHE, mmap_mode="r")
    df = pd.read_csv(INDEX_CSV)

    subject_col = "subject_id"
    stimulus_col = "stimulus_id"
    score_col = "arousal_score"

    subjects = df[subject_col].to_numpy()
    stim = df[stimulus_col].to_numpy()
    y = pd.to_numeric(df[score_col], errors="coerce").to_numpy(np.float32)

    high_threshold = load_high_threshold()
    locked_rmse = load_locked_bridge_rmse()
    fixed_pred = load_fixed_residual_predictions(len(df))

    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] device={device}")
    if torch.cuda.is_available():
        print(f"[INFO] gpu={torch.cuda.get_device_name(0)}")
    print(f"[INFO] cache={EEG_CACHE} shape={x.shape}")
    print(f"[INFO] high_threshold={high_threshold:.6f}")
    print(f"[INFO] locked_bridge_rmse_05ak={locked_rmse}")
    print(f"[INFO] fixed_pred_finite_rate={np.isfinite(fixed_pred).mean():.3f}")

    unique_subjects = sorted(pd.unique(subjects))
    if args.smoke:
        unique_subjects = unique_subjects[:6]
        prefix = ROOT / "docs/roca/idare_06a5b_gaussian10_locked_gate_rerun_smoke_current"
    else:
        prefix = ROOT / "docs/roca/idare_06a5b_gaussian10_locked_gate_rerun_current"

    methods = [
        ("none_noaug_control", 0.0),
        ("gaussian_0p10", 0.10),
    ]

    all_preds = []
    fold_rows = []

    for method, gstd in methods:
        print(f"\n{'='*90}\n[_METHOD] {method} gaussian_std={gstd}\n{'='*90}")
        for fi, test_subject in enumerate(unique_subjects, start=1):
            print(f"[fold {fi}/{len(unique_subjects)}] method={method} test_subject={test_subject}")
            pred_df = train_one_fold(
                x=x,
                df=df,
                subjects=subjects,
                stim=stim,
                y=y,
                test_subject=test_subject,
                fold_i=fi,
                method=method,
                gaussian_std=gstd,
                epochs=args.epochs,
                batch_size=args.batch_size,
                device=device,
                seed=args.seed,
            )
            rt = pred_df["residual_true"].to_numpy(float)
            pp = pred_df["residual_pred"].to_numpy(float)
            high = np.abs(rt) >= high_threshold
            fold_rows.append(
                {
                    "method": method,
                    "fold": fi,
                    "test_subject": test_subject,
                    "n": len(pred_df),
                    "n_high": int(high.sum()),
                    "zero_rmse_high": rmse(rt[high], np.zeros(high.sum())) if high.sum() else float("nan"),
                    "model_rmse_high": rmse(rt[high], pp[high]) if high.sum() else float("nan"),
                    "lift_vs_zero_high": (
                        rmse(rt[high], np.zeros(high.sum())) - rmse(rt[high], pp[high])
                        if high.sum()
                        else float("nan")
                    ),
                    "pearson_high": pearson(rt[high], pp[high]) if high.sum() else float("nan"),
                    "sign_acc_high": sign_acc(rt[high], pp[high]) if high.sum() else float("nan"),
                }
            )
            all_preds.append(pred_df)

    preds = pd.concat(all_preds, ignore_index=True)
    folds = pd.DataFrame(fold_rows)
    metrics, subj = summarize_predictions(preds, fixed_pred, high_threshold, locked_rmse)
    decision = make_decision(metrics)

    write_report(prefix, decision, metrics, folds, subj, preds, args, device, locked_rmse)

    print("\nROCA step 06a5b completed.")
    for suffix in [
        ".md", ".json", "_decision_table.csv", "_method_metrics.csv",
        "_fold_metrics.csv", "_subject_stats.csv", "_predictions.csv"
    ]:
        print("wrote:", str(prefix) + suffix)

    print("\nDecision table:")
    print(decision.to_string(index=False))
    print("\nMethod metrics:")
    print(metrics.to_string(index=False))


if __name__ == "__main__":
    main()
