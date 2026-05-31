#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / ".cache"
ROCA_DIR = ROOT / "docs" / "roca"
DEFAULT_TRIAL_INDEX = CACHE_DIR / "idare_trial_index.csv"
DEFAULT_OUT_PREFIX = "idare_physiology_informed_personalization_challenge_gpu_current"

TARGETS = {
    "valence": "valence_score",
    "arousal": "arousal_score",
}
LABEL_POLICIES = ["midpoint_as_low", "midpoint_as_high", "discard_midpoint"]
EPS = 1e-8
LOCKED_REFERENCE_MODEL = "locked_kernel_residual_shrink4"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--trial-index", type=Path, default=DEFAULT_TRIAL_INDEX)
    p.add_argument("--targets", type=str, default="valence,arousal")
    p.add_argument("--blocks", type=str, default="emg_existing_22,emg_bsl_stats_22,eeg_entropy_complexity,eeg_bandpower,emg_lagged_interaction_experimental")
    p.add_argument("--k-values", type=str, default="4,8,16")
    p.add_argument("--n-repeats", type=int, default=50)
    p.add_argument("--max-subjects", type=int, default=None)
    p.add_argument("--seed", type=int, default=20260530)
    p.add_argument("--alphas", type=str, default="100,1000")
    p.add_argument("--device", type=str, default="cuda")
    p.add_argument("--out-prefix", type=str, default=DEFAULT_OUT_PREFIX)
    p.add_argument("--practical-lift", type=float, default=0.02)
    p.add_argument("--min-win-margin", type=int, default=3)
    p.add_argument("--no-knn", action="store_true")
    p.add_argument("--write-predictions", action="store_true", help="Debug only. Can create large files; off by default.")
    return p.parse_args()


def stable_seed(*parts: Any) -> int:
    payload = "|".join(str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "little") % (2**32)


def safe_float(x: Any):
    try:
        v = float(x)
    except Exception:
        return None
    return v if math.isfinite(v) else None


def clean_json(x: Any):
    if isinstance(x, dict):
        return {str(k): clean_json(v) for k, v in x.items()}
    if isinstance(x, list):
        return [clean_json(v) for v in x]
    if isinstance(x, tuple):
        return [clean_json(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        v = float(x)
        return v if math.isfinite(v) else None
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    try:
        if bool(pd.isna(x)):
            return None
    except Exception:
        pass
    return x


def md_cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6f}" if math.isfinite(v) else ""
    try:
        if bool(pd.isna(v)):
            return ""
    except Exception:
        pass
    return str(v).replace("|", "\\|").replace("\n", " ")


def md_table(df: pd.DataFrame, cols: list[str], max_rows: int | None = None) -> str:
    if df is None or df.empty:
        return "_No rows._\n"
    view = df.copy()
    if max_rows is not None:
        view = view.head(max_rows)
    cols = [c for c in cols if c in view.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(md_cell(row.get(c)) for c in cols) + " |")
    return "\n".join(lines) + "\n"


def pearson_from_sums(n, sy, sp, sy2, sp2, syp):
    if n < 2:
        return None
    cov = syp - sy * sp / n
    vy = sy2 - sy * sy / n
    vp = sp2 - sp * sp / n
    if vy <= EPS or vp <= EPS:
        return None
    return safe_float(cov / math.sqrt(vy * vp))


def ccc_from_sums(n, sy, sp, sy2, sp2, syp):
    if n < 2:
        return None
    my, mp = sy / n, sp / n
    vy = sy2 / n - my * my
    vp = sp2 / n - mp * mp
    cov = syp / n - my * mp
    denom = vy + vp + (my - mp) ** 2
    if denom <= EPS:
        return None
    return safe_float(2.0 * cov / denom)


class RegAccum:
    __slots__ = ("n", "sae", "sse", "sy", "sp", "sy2", "sp2", "syp")
    def __init__(self):
        self.n = 0
        self.sae = 0.0
        self.sse = 0.0
        self.sy = 0.0
        self.sp = 0.0
        self.sy2 = 0.0
        self.sp2 = 0.0
        self.syp = 0.0

    def add(self, y, p):
        y = np.asarray(y, dtype=np.float64)
        p = np.asarray(p, dtype=np.float64)
        m = np.isfinite(y) & np.isfinite(p)
        if not np.any(m):
            return
        y = y[m]
        p = p[m]
        e = p - y
        self.n += int(len(y))
        self.sae += float(np.abs(e).sum())
        self.sse += float((e * e).sum())
        self.sy += float(y.sum())
        self.sp += float(p.sum())
        self.sy2 += float((y * y).sum())
        self.sp2 += float((p * p).sum())
        self.syp += float((y * p).sum())

    def row(self):
        if self.n == 0:
            return {"n": 0, "mae": None, "rmse": None, "pearson": None, "ccc": None, "y_true_std": None, "y_pred_std": None}
        my = self.sy / self.n
        mp = self.sp / self.n
        vy = max(0.0, self.sy2 / self.n - my * my)
        vp = max(0.0, self.sp2 / self.n - mp * mp)
        return {
            "n": int(self.n),
            "mae": safe_float(self.sae / self.n),
            "rmse": safe_float(math.sqrt(self.sse / self.n)),
            "pearson": pearson_from_sums(self.n, self.sy, self.sp, self.sy2, self.sp2, self.syp),
            "ccc": ccc_from_sums(self.n, self.sy, self.sp, self.sy2, self.sp2, self.syp),
            "y_true_std": safe_float(math.sqrt(vy)),
            "y_pred_std": safe_float(math.sqrt(vp)),
        }


class BinaryAccum:
    def __init__(self):
        self.n = 0
        self.correct = 0
        self.tp = {0: 0, 1: 0}
        self.fp = {0: 0, 1: 0}
        self.fn = {0: 0, 1: 0}
        self.support = {0: 0, 1: 0}

    def add(self, y_score, pred_score, policy: str):
        y = np.asarray(y_score, dtype=float)
        p = np.asarray(pred_score, dtype=float)
        m = np.isfinite(y) & np.isfinite(p)
        if policy == "midpoint_as_low":
            yb = (y[m] > 5.0).astype(int)
            pb = (p[m] > 5.0).astype(int)
        elif policy == "midpoint_as_high":
            yb = (y[m] >= 5.0).astype(int)
            pb = (p[m] >= 5.0).astype(int)
        elif policy == "discard_midpoint":
            m = m & (y != 5.0)
            yb = (y[m] > 5.0).astype(int)
            pb = (p[m] > 5.0).astype(int)
        else:
            raise ValueError(policy)
        self.n += int(len(yb))
        self.correct += int((yb == pb).sum())
        for cls in [0, 1]:
            self.support[cls] += int((yb == cls).sum())
            self.tp[cls] += int(((yb == cls) & (pb == cls)).sum())
            self.fp[cls] += int(((yb != cls) & (pb == cls)).sum())
            self.fn[cls] += int(((yb == cls) & (pb != cls)).sum())

    def row(self):
        if self.n == 0:
            return {"binary_n": 0, "accuracy": None, "balanced_accuracy": None, "macro_f1": None, "n_low": 0, "n_high": 0}
        recalls, f1s = [], []
        for cls in [0, 1]:
            if self.support[cls] > 0:
                recalls.append(self.tp[cls] / self.support[cls])
            denom = 2 * self.tp[cls] + self.fp[cls] + self.fn[cls]
            f1s.append((2 * self.tp[cls] / denom) if denom > 0 else 0.0)
        return {
            "binary_n": int(self.n),
            "accuracy": safe_float(self.correct / self.n),
            "balanced_accuracy": safe_float(np.mean(recalls)) if recalls else None,
            "macro_f1": safe_float(np.mean(f1s)),
            "n_low": int(self.support[0]),
            "n_high": int(self.support[1]),
        }


def load_05w_module():
    path = ROOT / "scripts" / "roca" / "05w_idare_residual_physiology_feature_audit.py"
    if not path.exists():
        raise FileNotFoundError(f"Missing feature helper script: {path}")
    spec = importlib.util.spec_from_file_location("roca05w_feature_helpers", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def load_base(path: Path, max_subjects: int | None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    needed = ["subject_id", "stimulus_id", "valence_score", "arousal_score"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"trial index missing columns: {missing}")
    df = df[needed].drop_duplicates(["subject_id", "stimulus_id"]).copy()
    df["subject_id"] = df["subject_id"].astype(int)
    df["stimulus_id"] = df["stimulus_id"].astype(str)
    df = df.sort_values(["subject_id", "stimulus_id"]).reset_index(drop=True)
    df["audit_row"] = np.arange(len(df), dtype=int)
    if max_subjects is not None:
        keep = sorted(df["subject_id"].unique())[: int(max_subjects)]
        df = df[df["subject_id"].isin(keep)].copy().reset_index(drop=True)
    return df


def stimulus_prior_excluding_subject(df: pd.DataFrame, score_col: str, test_subject: int):
    train = df[df["subject_id"].ne(test_subject)]
    stim_mean = train.groupby("stimulus_id")[score_col].mean()
    global_mean = float(train[score_col].mean())
    return stim_mean, global_mean


def map_stimulus_prior(g: pd.DataFrame, score_col: str, stim_mean: pd.Series, global_mean: float):
    return g["stimulus_id"].map(stim_mean).astype(float).fillna(global_mean).to_numpy(dtype=np.float32)


def kernel_residual_predict_np(y_cal, p_cal, p_eval, bandwidth=0.75, shrink_lambda=4.0):
    y_cal = np.asarray(y_cal, dtype=np.float32)
    p_cal = np.asarray(p_cal, dtype=np.float32)
    p_eval = np.asarray(p_eval, dtype=np.float32)
    if len(y_cal) == 0:
        return p_eval.copy()
    r = y_cal - p_cal
    out = np.empty_like(p_eval, dtype=np.float32)
    bw = float(bandwidth) if bandwidth > 0 else 0.75
    for i, pe in enumerate(p_eval):
        d = np.abs(p_cal - pe)
        w = np.exp(-0.5 * (d / bw) ** 2)
        sw = float(w.sum())
        if sw <= EPS:
            loc = float(r.mean())
            eff_n = len(r)
        else:
            loc = float((w * r).sum() / sw)
            eff_n = (sw * sw) / float((w * w).sum() + EPS)
        shrink = eff_n / (eff_n + shrink_lambda)
        out[i] = pe + shrink * loc
    return out


def standardize_np(x_train: np.ndarray, x_test: np.ndarray):
    mu = x_train.mean(axis=0, keepdims=True)
    sd = x_train.std(axis=0, keepdims=True)
    sd = np.where(sd < EPS, 1.0, sd)
    return ((x_train - mu) / sd).astype(np.float32), ((x_test - mu) / sd).astype(np.float32)


def torch_ridge_predict(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, alpha: float, device: torch.device):
    if x_train.shape[0] < 2 or x_test.shape[0] == 0:
        return np.zeros((x_test.shape[0],), dtype=np.float32)
    xt_np, xv_np = standardize_np(x_train, x_test)
    xt = torch.as_tensor(xt_np, dtype=torch.float32, device=device)
    xv = torch.as_tensor(xv_np, dtype=torch.float32, device=device)
    y = torch.as_tensor(y_train.astype(np.float32), dtype=torch.float32, device=device).view(-1, 1)
    ones = torch.ones((xt.shape[0], 1), dtype=torch.float32, device=device)
    xtb = torch.cat([ones, xt], dim=1)
    reg = torch.eye(xtb.shape[1], dtype=torch.float32, device=device) * float(alpha)
    reg[0, 0] = 0.0
    a = xtb.T @ xtb + reg
    b = xtb.T @ y
    try:
        w = torch.linalg.solve(a, b)
    except RuntimeError:
        w = torch.linalg.lstsq(a, b).solution
    xvb = torch.cat([torch.ones((xv.shape[0], 1), dtype=torch.float32, device=device), xv], dim=1)
    pred = (xvb @ w).squeeze(1)
    return pred.detach().cpu().numpy().astype(np.float32)


def torch_knn_residual_predict(x_train: np.ndarray, r_train: np.ndarray, x_test: np.ndarray, device: torch.device, k=64, temperature=1.0, chunk=512):
    if x_train.shape[0] == 0 or x_test.shape[0] == 0:
        return np.zeros((x_test.shape[0],), dtype=np.float32)
    xt_np, xv_np = standardize_np(x_train, x_test)
    xt = torch.as_tensor(xt_np, dtype=torch.float32, device=device)
    xv = torch.as_tensor(xv_np, dtype=torch.float32, device=device)
    r = torch.as_tensor(r_train.astype(np.float32), dtype=torch.float32, device=device)
    kk = int(min(k, xt.shape[0]))
    outs = []
    for start in range(0, xv.shape[0], chunk):
        xb = xv[start:start + chunk]
        d = torch.cdist(xb, xt)
        vals, idx = torch.topk(d, k=kk, dim=1, largest=False)
        scale = torch.median(vals.detach()).clamp_min(1e-6) * float(temperature)
        w = torch.softmax(-vals / scale, dim=1)
        pred = (w * r[idx]).sum(dim=1)
        outs.append(pred.detach().cpu().numpy())
    return np.concatenate(outs, axis=0).astype(np.float32)


def make_calibration_indices(n: int, k: int, seed: int, target: str, block: str, subject_id: int, repeat: int):
    if k <= 0:
        return np.array([], dtype=int)
    rng = np.random.default_rng(stable_seed(seed, target, block, subject_id, k, repeat))
    return np.sort(rng.choice(n, size=int(k), replace=False))


def add_predictions(global_acc, subject_acc, binary_acc, key, subject_id, y, p):
    global_acc[key].add(y, p)
    subject_acc[key + (int(subject_id),)].add(y, p)
    for policy in LABEL_POLICIES:
        binary_acc[key + (policy,)].add(y, p, policy)


def build_rows_from_acc(global_acc, subject_acc, binary_acc):
    main_rows = []
    for key, acc in global_acc.items():
        target, block, k, model = key
        row = {"target": target, "block": block, "k_calibration": int(k), "model": model}
        row.update(acc.row())
        main_rows.append(row)
    main = pd.DataFrame(main_rows)

    subject_rows = []
    for key, acc in subject_acc.items():
        target, block, k, model, subject_id = key
        row = {"target": target, "block": block, "k_calibration": int(k), "model": model, "subject_id": int(subject_id)}
        row.update(acc.row())
        subject_rows.append(row)
    subject = pd.DataFrame(subject_rows)

    binary_rows = []
    for key, acc in binary_acc.items():
        target, block, k, model, policy = key
        row = {"target": target, "block": block, "k_calibration": int(k), "model": model, "label_policy": policy}
        row.update(acc.row())
        binary_rows.append(row)
    binary = pd.DataFrame(binary_rows)
    return main, subject, binary


def add_locked_lifts(main: pd.DataFrame, subject: pd.DataFrame):
    if main.empty:
        return main, subject, pd.DataFrame()
    ref = main[main["model"].eq(LOCKED_REFERENCE_MODEL)][["target", "block", "k_calibration", "rmse"]].rename(columns={"rmse": "locked_reference_rmse"})
    main = main.merge(ref, on=["target", "block", "k_calibration"], how="left")
    main["locked_reference_model"] = LOCKED_REFERENCE_MODEL
    main["lift_vs_locked_rmse"] = main["locked_reference_rmse"] - main["rmse"]

    sub_ref = subject[subject["model"].eq(LOCKED_REFERENCE_MODEL)][["target", "block", "k_calibration", "subject_id", "rmse"]].rename(columns={"rmse": "locked_subject_rmse"})
    subject = subject.merge(sub_ref, on=["target", "block", "k_calibration", "subject_id"], how="left")
    subject["delta_rmse_model_minus_locked"] = subject["rmse"] - subject["locked_subject_rmse"]

    win_rows = []
    for keys, g in subject[~subject["model"].eq(LOCKED_REFERENCE_MODEL)].groupby(["target", "block", "k_calibration", "model"], dropna=False):
        target, block, k, model = keys
        delta = g["delta_rmse_model_minus_locked"].to_numpy(dtype=float)
        delta = delta[np.isfinite(delta)]
        if len(delta) == 0:
            continue
        wins = int((delta < -1e-12).sum())
        losses = int((delta > 1e-12).sum())
        ties = int(len(delta) - wins - losses)
        win_rows.append({
            "target": target,
            "block": block,
            "k_calibration": int(k),
            "model": model,
            "subjects": int(len(delta)),
            "rmse_wins_vs_locked": wins,
            "rmse_losses_vs_locked": losses,
            "rmse_ties_vs_locked": ties,
            "rmse_win_margin_vs_locked": wins - losses,
            "mean_delta_rmse_model_minus_locked": safe_float(np.mean(delta)),
            "median_delta_rmse_model_minus_locked": safe_float(np.median(delta)),
            "worst_regression_delta_rmse": safe_float(np.max(delta)),
            "best_gain_delta_rmse": safe_float(np.min(delta)),
        })
    wins = pd.DataFrame(win_rows)
    if not wins.empty:
        main = main.merge(wins, on=["target", "block", "k_calibration", "model"], how="left")
    return main, subject, wins


def build_verdict(main: pd.DataFrame, practical_lift: float, min_win_margin: int):
    rows = []
    cand = main[~main["model"].eq(LOCKED_REFERENCE_MODEL)].copy()
    for target, tg in cand.groupby("target", dropna=False):
        tgc = tg.copy()
        if tgc.empty:
            rows.append({"target": target, "decision": "NO_CANDIDATES", "reason": "no physiology-informed candidates"})
            continue
        tgc = tgc.sort_values(["lift_vs_locked_rmse", "rmse"], ascending=[False, True])
        best = tgc.iloc[0]
        lift = safe_float(best.get("lift_vs_locked_rmse"))
        margin = safe_float(best.get("rmse_win_margin_vs_locked"))
        mean_delta = safe_float(best.get("mean_delta_rmse_model_minus_locked"))
        reasons = []
        if lift is None or lift <= 0:
            reasons.append("physiology-informed models do not improve over locked B2 personalization baseline")
        if lift is None or lift < practical_lift:
            reasons.append(f"pooled lift < {practical_lift}")
        if margin is None or margin < min_win_margin:
            reasons.append(f"subject win margin < {min_win_margin}")
        if mean_delta is None or mean_delta >= 0:
            reasons.append("mean subject RMSE delta is not better than locked baseline")
        if not reasons:
            decision = "GO_PHYSIOLOGY_BEATS_LOCKED_PERSONALIZATION_GPU"
            reason = "physiology-informed model beats locked B2 personalization baseline in pooled and subject-level metrics"
        elif lift is not None and lift > 0:
            decision = "WEAK_GO_PHYSIOLOGY_VS_LOCKED_NEEDS_CONFIRMATION_GPU"
            reason = "; ".join(reasons)
        else:
            decision = "NO_GO_PHYSIOLOGY_VS_LOCKED_PERSONALIZATION_GPU"
            reason = "; ".join(reasons)
        rows.append({
            "target": target,
            "decision": decision,
            "best_block": best.get("block"),
            "best_model": best.get("model"),
            "best_k_calibration": int(best.get("k_calibration")),
            "best_rmse": safe_float(best.get("rmse")),
            "locked_reference_model": LOCKED_REFERENCE_MODEL,
            "locked_reference_rmse": safe_float(best.get("locked_reference_rmse")),
            "best_lift_vs_locked_rmse": lift,
            "rmse_win_margin_vs_locked": margin,
            "mean_delta_rmse_model_minus_locked": mean_delta,
            "reason": reason,
        })
    return pd.DataFrame(rows)


def main():
    args = parse_args()
    ROCA_DIR.mkdir(parents=True, exist_ok=True)
    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    blocks = [b.strip() for b in args.blocks.split(",") if b.strip()]
    k_values = [int(x.strip()) for x in args.k_values.split(",") if x.strip()]
    alphas = [float(x.strip()) for x in args.alphas.split(",") if x.strip()]

    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but torch.cuda.is_available() is False")
    device = torch.device(args.device if args.device != "cuda" else "cuda:0")
    torch.manual_seed(int(args.seed))
    if device.type == "cuda":
        torch.cuda.set_device(device)

    feature_helpers = load_05w_module()
    base = load_base(args.trial_index, args.max_subjects)
    subjects = sorted(base["subject_id"].unique())

    print("[INFO] I-DARE GPU physiology-informed personalization challenge")
    print(f"[INFO] device={device} torch={torch.__version__}")
    if device.type == "cuda":
        print(f"[INFO] gpu={torch.cuda.get_device_name(device)}")
    print(f"[INFO] rows={len(base)} subjects={len(subjects)} stimuli={base['stimulus_id'].nunique()}")
    print(f"[INFO] targets={targets}")
    print(f"[INFO] blocks={blocks}")
    print(f"[INFO] k_values={k_values} n_repeats={args.n_repeats} alphas={alphas}")

    global_acc: dict[tuple, RegAccum] = defaultdict(RegAccum)
    subject_acc: dict[tuple, RegAccum] = defaultdict(RegAccum)
    binary_acc: dict[tuple, BinaryAccum] = defaultdict(BinaryAccum)
    prediction_rows = []

    for block in blocks:
        print("\n" + "=" * 88)
        print(f"[BLOCK] {block}")
        print("=" * 88)
        X, names = feature_helpers.build_feature_block(base, block)
        X = np.asarray(X, dtype=np.float32)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
        print(f"[BLOCK] feature_shape={X.shape}")

        for target in targets:
            if target not in TARGETS:
                raise ValueError(f"Unknown target: {target}")
            score_col = TARGETS[target]
            print(f"  [TARGET] {target}")

            for test_subject in subjects:
                stim_mean, global_mean = stimulus_prior_excluding_subject(base, score_col, int(test_subject))
                train_mask = base["subject_id"].ne(test_subject).to_numpy()
                test_mask = base["subject_id"].eq(test_subject).to_numpy()

                train_df = base.loc[train_mask].copy().reset_index(drop=True)
                test_df = base.loc[test_mask].copy().reset_index(drop=True)
                train_rows = np.where(train_mask)[0]
                test_rows = np.where(test_mask)[0]

                y_train = train_df[score_col].to_numpy(dtype=np.float32)
                p_train = map_stimulus_prior(train_df, score_col, stim_mean, global_mean)
                r_train = y_train - p_train
                x_train = X[train_rows]

                y_test_all = test_df[score_col].to_numpy(dtype=np.float32)
                p_test_all = map_stimulus_prior(test_df, score_col, stim_mean, global_mean)
                x_test_all = X[test_rows]

                physio_pred_by_model = {}
                for alpha in alphas:
                    alpha_name = f"{int(alpha) if float(alpha).is_integer() else alpha:g}"
                    r_pred = torch_ridge_predict(x_train, r_train, x_test_all, alpha=alpha, device=device)
                    physio_pred_by_model[f"physio_residual_ridge{alpha_name}"] = p_test_all + r_pred

                    x_train_ctx = np.concatenate([x_train, p_train[:, None]], axis=1).astype(np.float32)
                    x_test_ctx = np.concatenate([x_test_all, p_test_all[:, None]], axis=1).astype(np.float32)
                    y_pred = torch_ridge_predict(x_train_ctx, y_train, x_test_ctx, alpha=alpha, device=device)
                    physio_pred_by_model[f"physio_context_ridge{alpha_name}"] = y_pred

                if not args.no_knn:
                    r_knn = torch_knn_residual_predict(x_train, r_train, x_test_all, device=device, k=64)
                    physio_pred_by_model["physio_similarity_knn64"] = p_test_all + r_knn

                n_test = len(test_df)
                for k in k_values:
                    if k >= n_test:
                        continue
                    repeats = [0] if k <= 0 else list(range(args.n_repeats))
                    for rep in repeats:
                        cal_idx = make_calibration_indices(n_test, k, args.seed, target, block, int(test_subject), int(rep))
                        eval_mask = np.ones(n_test, dtype=bool)
                        eval_mask[cal_idx] = False
                        eval_idx = np.where(eval_mask)[0]
                        if len(eval_idx) == 0:
                            continue
                        y_eval = y_test_all[eval_idx]
                        p_eval = p_test_all[eval_idx]
                        y_cal = y_test_all[cal_idx]
                        p_cal = p_test_all[cal_idx]
                        locked_pred = kernel_residual_predict_np(y_cal, p_cal, p_eval, bandwidth=0.75, shrink_lambda=4.0)

                        locked_key = (target, block, int(k), LOCKED_REFERENCE_MODEL)
                        add_predictions(global_acc, subject_acc, binary_acc, locked_key, int(test_subject), y_eval, locked_pred)

                        for model, pred_all in physio_pred_by_model.items():
                            pred_eval = pred_all[eval_idx]
                            key = (target, block, int(k), model)
                            add_predictions(global_acc, subject_acc, binary_acc, key, int(test_subject), y_eval, pred_eval)

                            if args.write_predictions:
                                for loc, idx in enumerate(eval_idx):
                                    prediction_rows.append({
                                        "target": target,
                                        "block": block,
                                        "subject_id": int(test_subject),
                                        "stimulus_id": str(test_df.iloc[idx]["stimulus_id"]),
                                        "k_calibration": int(k),
                                        "repeat": int(rep),
                                        "model": model,
                                        "y_true_score": float(y_eval[loc]),
                                        "locked_reference_score": float(locked_pred[loc]),
                                        "y_pred_score": float(pred_eval[loc]),
                                    })

        if device.type == "cuda":
            torch.cuda.empty_cache()

    main_df, subject_df, binary_df = build_rows_from_acc(global_acc, subject_acc, binary_acc)
    main_df, subject_df, wins_df = add_locked_lifts(main_df, subject_df)
    verdict_df = build_verdict(main_df, args.practical_lift, args.min_win_margin)
    best_df = main_df[~main_df["model"].eq(LOCKED_REFERENCE_MODEL)].copy()
    best_df = best_df.sort_values(["target", "lift_vs_locked_rmse", "rmse"], ascending=[True, False, True])

    out_prefix = args.out_prefix
    out_md = ROCA_DIR / f"{out_prefix}.md"
    out_json = ROCA_DIR / f"{out_prefix}.json"
    out_main = ROCA_DIR / f"{out_prefix}_main_metrics.csv"
    out_binary = ROCA_DIR / f"{out_prefix}_binary_metrics.csv"
    out_subject = ROCA_DIR / f"{out_prefix}_subject_metrics.csv"
    out_wins = ROCA_DIR / f"{out_prefix}_subject_winloss.csv"
    out_verdict = ROCA_DIR / f"{out_prefix}_verdict.csv"
    out_best = ROCA_DIR / f"{out_prefix}_best_ranking.csv"
    out_pred = ROCA_DIR / f"{out_prefix}_predictions.csv"

    main_df.to_csv(out_main, index=False)
    binary_df.to_csv(out_binary, index=False)
    subject_df.to_csv(out_subject, index=False)
    wins_df.to_csv(out_wins, index=False)
    verdict_df.to_csv(out_verdict, index=False)
    best_df.to_csv(out_best, index=False)

    prediction_path = None
    if args.write_predictions:
        pd.DataFrame(prediction_rows).to_csv(out_pred, index=False)
        prediction_path = str(out_pred)
    else:
        if out_pred.exists():
            out_pred.unlink()

    verdict_cols = [
        "target", "decision", "best_block", "best_model", "best_k_calibration", "best_rmse",
        "locked_reference_rmse", "best_lift_vs_locked_rmse", "rmse_win_margin_vs_locked",
        "mean_delta_rmse_model_minus_locked", "reason",
    ]
    best_cols = [
        "target", "block", "k_calibration", "model", "n", "rmse", "locked_reference_rmse",
        "lift_vs_locked_rmse", "pearson", "ccc", "rmse_wins_vs_locked", "rmse_losses_vs_locked",
        "rmse_win_margin_vs_locked", "mean_delta_rmse_model_minus_locked",
    ]

    report = {
        "step": "05ah_gpu",
        "title": "I-DARE GPU physiology-informed personalization challenge",
        "purpose": "Test whether EEG/EMG feature blocks beat the locked kernel_residual_shrink4 personalization baseline using a PyTorch/CUDA backend.",
        "inputs": {
            "trial_index": str(args.trial_index),
            "targets": targets,
            "blocks": blocks,
            "k_values": k_values,
            "n_repeats": args.n_repeats,
            "max_subjects": args.max_subjects,
            "alphas": alphas,
            "seed": args.seed,
            "device": str(device),
            "torch": torch.__version__,
            "gpu": torch.cuda.get_device_name(device) if device.type == "cuda" else None,
        },
        "locked_reference_model": LOCKED_REFERENCE_MODEL,
        "candidate_models": sorted([m for m in main_df["model"].unique().tolist() if m != LOCKED_REFERENCE_MODEL]),
        "outputs": {
            "md": str(out_md),
            "json": str(out_json),
            "main_metrics": str(out_main),
            "binary_metrics": str(out_binary),
            "subject_metrics": str(out_subject),
            "subject_winloss": str(out_wins),
            "verdict": str(out_verdict),
            "best_ranking": str(out_best),
            "predictions": prediction_path,
        },
        "verdict": verdict_df.to_dict(orient="records"),
        "best_top30": best_df.head(30).to_dict(orient="records"),
    }
    out_json.write_text(json.dumps(clean_json(report), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("# I-DARE GPU Physiology-Informed Personalization Challenge\n")
    lines.append("This is the CUDA/PyTorch version of the 05ah challenge. It keeps the scientific target locked: EEG/EMG must beat the B2 `kernel_residual_shrink4` personalization baseline, not merely `stimulus_only`.\n")
    lines.append(f"Backend: `{device}`; PyTorch `{torch.__version__}`.\n")
    if device.type == "cuda":
        lines.append(f"GPU: `{torch.cuda.get_device_name(device)}`.\n")
    lines.append("\n## Verdict\n")
    lines.append(md_table(verdict_df, verdict_cols))
    lines.append("\n## Best physiology-informed rows by lift over locked B2\n")
    lines.append(md_table(best_df, best_cols, max_rows=40))
    lines.append("\n## Interpretation\n")
    lines.append("- `GO_PHYSIOLOGY_BEATS_LOCKED_PERSONALIZATION_GPU` means EEG/EMG adds incremental value over the locked personalized B2 baseline.\n")
    lines.append("- `NO_GO_PHYSIOLOGY_VS_LOCKED_PERSONALIZATION_GPU` means the tested physiology features do not yet improve over the locked personalization baseline.\n")
    lines.append("- This GPU step is intentionally documented separately from CPU 05ah to preserve reproducibility and backend comparability.\n")
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05ah_gpu completed.")
    for p in [out_md, out_json, out_main, out_binary, out_subject, out_wins, out_verdict, out_best]:
        print(f"wrote: {p}")
    if prediction_path:
        print(f"wrote: {prediction_path}")
    else:
        print("[INFO] skipped predictions CSV by default")

    print("\nVerdict:")
    print(verdict_df[verdict_cols].to_string(index=False))
    print("\nBest rows:")
    print(best_df[best_cols].head(30).to_string(index=False))


if __name__ == "__main__":
    main()
