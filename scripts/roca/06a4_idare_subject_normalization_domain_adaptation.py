#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler


ROCA = Path("docs/roca")
OUT_PREFIX = "idare_06a4_subject_normalization_domain_adaptation_current"


def read_csv_optional(path: Path) -> pd.DataFrame:
    try:
        if path.exists():
            return pd.read_csv(path)
    except Exception as exc:
        print(f"[WARN] failed to read {path}: {exc}")
    return pd.DataFrame()


def first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = list(df.columns)
    lower = {c.lower(): c for c in cols}
    for c in candidates:
        if c in cols:
            return c
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def rmse(y: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    y = y[np.isfinite(y)]
    if y.size == 0:
        return float("nan")
    return float(np.sqrt(np.mean(y * y)))


def corr(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    a = a[m]
    b = b[m]
    if a.size < 3:
        return float("nan")
    if float(np.std(a)) <= 1e-12 or float(np.std(b)) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def sign_acc(y: np.ndarray, p: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    if not np.any(m):
        return float("nan")
    return float(np.mean(np.sign(y[m]) == np.sign(p[m])))


def bootstrap_ci_mean(x: np.ndarray, rng: np.random.Generator, n_boot: int = 2000) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return float("nan"), float("nan")
    if x.size == 1:
        return float(x[0]), float(x[0])
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, x.size, size=x.size)
        vals.append(float(np.mean(x[idx])))
    return float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))


def signflip_p_one_sided_gt_zero(x: np.ndarray, rng: np.random.Generator, n_perm: int = 5000) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return float("nan")
    obs = float(np.mean(x))
    signs = rng.choice([-1.0, 1.0], size=(n_perm, x.size))
    sims = np.mean(signs * x[None, :], axis=1)
    return float((np.sum(sims >= obs) + 1) / (n_perm + 1))


def md_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df is None or df.empty:
        return "_empty_\n"
    x = df.copy()
    if max_rows is not None:
        x = x.head(max_rows)
    x = x.fillna("")
    cols = list(x.columns)
    rows = [[str(v) for v in row] for row in x.to_numpy().tolist()]
    widths = []
    for i, c in enumerate(cols):
        widths.append(max(len(str(c)), *(len(r[i]) for r in rows)))
    def fmt(row: list[str]) -> str:
        return "| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(cols))) + " |"
    out = [fmt([str(c) for c in cols]), "| " + " | ".join("-" * w for w in widths) + " |"]
    out.extend(fmt(r) for r in rows)
    return "\n".join(out) + "\n"


def git_short() -> str:
    try:
        return subprocess.check_output(["git", "status", "--short"], text=True, stderr=subprocess.STDOUT)
    except Exception as exc:
        return f"[git status failed: {exc}]"


def loso_stimulus_prior_residual(df: pd.DataFrame, y_col: str, stim_col: str) -> tuple[np.ndarray, np.ndarray]:
    y = df[y_col].astype(float).to_numpy()
    stim_sum = df.groupby(stim_col)[y_col].transform("sum").astype(float).to_numpy()
    stim_count = df.groupby(stim_col)[y_col].transform("count").astype(float).to_numpy()
    pred = np.where(stim_count > 1, (stim_sum - y) / np.maximum(stim_count - 1, 1), np.nan)
    pred = np.where(np.isfinite(pred), pred, float(np.nanmean(y)))
    return pred.astype(float), (y - pred).astype(float)


def get_threshold(target: str, residual: np.ndarray) -> tuple[float, str]:
    verdict = read_csv_optional(ROCA / "idare_high_disagreement_direct_deviation_confirmatory_stats_current_verdict.csv")
    if not verdict.empty and "target" in verdict.columns and "abs_residual_threshold" in verdict.columns:
        m = verdict[verdict["target"].astype(str) == target]
        if not m.empty:
            try:
                return float(m.iloc[0]["abs_residual_threshold"]), "05ajb_confirmatory_threshold"
            except Exception:
                pass
    return float(np.nanquantile(np.abs(residual), 0.75)), "q75_abs_residual_fallback"


def eeg_summary_features(X: np.ndarray, sample_rate: float = 128.0, trial_channel_zscore: bool = False) -> np.ndarray:
    X = X.astype(np.float32, copy=False)
    if trial_channel_zscore:
        mu = X.mean(axis=2, keepdims=True)
        sd = X.std(axis=2, keepdims=True) + 1e-6
        X = (X - mu) / sd

    n, c, t = X.shape
    feats = []

    mean = X.mean(axis=2)
    std = X.std(axis=2)
    rms = np.sqrt(np.mean(X * X, axis=2))
    absmean = np.mean(np.abs(X), axis=2)
    ptp = np.ptp(X, axis=2)
    q25 = np.quantile(X, 0.25, axis=2)
    q75 = np.quantile(X, 0.75, axis=2)
    feats.extend([mean, std, rms, absmean, ptp, q25, q75])

    # Simple linear slope per channel.
    tt = np.linspace(-1.0, 1.0, t, dtype=np.float32)
    denom = float(np.sum(tt * tt)) + 1e-12
    slope = np.sum(X * tt[None, None, :], axis=2) / denom
    feats.append(slope)

    # Bandpower summary per channel. Intended to anchor the neural/deep route against simple bandpower evidence.
    freqs = np.fft.rfftfreq(t, d=1.0 / sample_rate)
    fft = np.fft.rfft(X, axis=2)
    power = (np.abs(fft) ** 2).astype(np.float32) / float(t)
    bands = {
        "delta": (1.0, 4.0),
        "theta": (4.0, 8.0),
        "alpha": (8.0, 13.0),
        "beta": (13.0, 30.0),
        "gamma": (30.0, 45.0),
    }
    total = np.mean(power[:, :, (freqs >= 1.0) & (freqs <= 45.0)], axis=2) + 1e-8
    for _name, (lo, hi) in bands.items():
        mask = (freqs >= lo) & (freqs < hi)
        bp = np.mean(power[:, :, mask], axis=2) if np.any(mask) else np.zeros((n, c), dtype=np.float32)
        feats.append(np.log1p(bp))
        feats.append(bp / total)

    F = np.concatenate([f.reshape(n, -1) for f in feats], axis=1)
    F = np.nan_to_num(F, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    return F


def train_loso_ridge_predictions(
    F: np.ndarray,
    residual: np.ndarray,
    subjects: np.ndarray,
    alpha: float,
) -> np.ndarray:
    pred = np.zeros(len(residual), dtype=float)
    unique_subjects = np.array(sorted(pd.unique(subjects)))
    for i, s in enumerate(unique_subjects, 1):
        test = subjects == s
        train = ~test
        scaler = StandardScaler()
        Xtr = scaler.fit_transform(F[train])
        Xte = scaler.transform(F[test])
        model = Ridge(alpha=alpha)
        model.fit(Xtr, residual[train])
        pred[test] = model.predict(Xte)
        if i % 10 == 0 or i == len(unique_subjects):
            print(f"[train] alpha={alpha} LOSO fold {i}/{len(unique_subjects)}")
    return pred


def load_fixed_bandpower_predictions(df: pd.DataFrame, target: str, subj_col: str, stim_col: str) -> tuple[np.ndarray | None, str]:
    path = ROCA / "idare_residual_physiology_feature_audit_current_predictions.csv"
    pred_df = read_csv_optional(path)
    if pred_df.empty:
        return None, f"missing {path}"

    tcol = first_col(pred_df, ["target"])
    bcol = first_col(pred_df, ["feature_block", "block"])
    pcol = first_col(pred_df, ["y_pred_deviation", "pred_deviation", "y_pred_residual"])
    pscol = first_col(pred_df, ["test_subject", "subject_id", "subject"])
    stcol = first_col(pred_df, ["stimulus_id", "stimulus"])
    if any(x is None for x in [tcol, bcol, pcol, pscol, stcol]):
        return None, f"fixed prediction columns missing in {path}"

    f = pred_df[
        (pred_df[tcol].astype(str) == target)
        & (pred_df[bcol].astype(str) == "eeg_bandpower")
    ].copy()
    if f.empty:
        return None, "no eeg_bandpower fixed prediction rows"
    f = f.drop_duplicates(subset=[pscol, stcol], keep="first")

    base = pd.DataFrame({
        "row_id": np.arange(len(df)),
        "subject_key": df[subj_col].astype(str).to_numpy(),
        "stimulus_key": df[stim_col].astype(str).to_numpy(),
    })
    f["subject_key"] = f[pscol].astype(str)
    f["stimulus_key"] = f[stcol].astype(str)
    f = f[["subject_key", "stimulus_key", pcol]].rename(columns={pcol: "fixed_pred"})
    merged = base.merge(f, on=["subject_key", "stimulus_key"], how="left").sort_values("row_id")
    arr = merged["fixed_pred"].to_numpy(dtype=float)
    if np.mean(np.isfinite(arr)) < 0.95:
        return None, f"fixed prediction alignment incomplete finite_rate={np.mean(np.isfinite(arr)):.3f}"
    return arr, f"loaded {path} eeg_bandpower rows={len(f)}"


def per_group_metrics(
    residual: np.ndarray,
    pred: np.ndarray,
    mask: np.ndarray,
    subjects: np.ndarray,
    rng: np.random.Generator,
    fixed_pred: np.ndarray | None = None,
    n_perm: int = 3000,
) -> dict[str, Any]:
    idx = np.flatnonzero(mask)
    y = residual[idx]
    p = pred[idx]
    zero_rmse = rmse(y)
    model_rmse = rmse(y - p)
    out = {
        "n_eval": int(idx.size),
        "subjects_eval": int(len(pd.unique(subjects[idx]))) if idx.size else 0,
        "zero_rmse": zero_rmse,
        "model_rmse": model_rmse,
        "lift_vs_zero": zero_rmse - model_rmse,
        "pearson": corr(y, p),
        "sign_acc": sign_acc(y, p),
    }
    if fixed_pred is not None:
        fp = fixed_pred[idx]
        out["fixed_rmse_same_eval"] = rmse(y - fp)
        out["lift_vs_fixed_same_eval"] = out["fixed_rmse_same_eval"] - model_rmse
    else:
        out["fixed_rmse_same_eval"] = float("nan")
        out["lift_vs_fixed_same_eval"] = float("nan")

    subject_imps = []
    wins = 0
    losses = 0
    for s in pd.unique(subjects[idx]):
        m = idx[subjects[idx] == s]
        if m.size < 1:
            continue
        z = rmse(residual[m])
        mm = rmse(residual[m] - pred[m])
        imp = z - mm
        subject_imps.append(imp)
        if imp > 1e-12:
            wins += 1
        elif imp < -1e-12:
            losses += 1
    imps = np.asarray(subject_imps, dtype=float)
    ci_low, ci_high = bootstrap_ci_mean(imps, rng)
    out.update({
        "mean_subject_improvement_zero_minus_model": float(np.nanmean(imps)) if imps.size else float("nan"),
        "ci95_low_mean_subject_improvement": ci_low,
        "ci95_high_mean_subject_improvement": ci_high,
        "signflip_p_one_sided_mean_gt_zero": signflip_p_one_sided_gt_zero(imps, rng, n_perm=n_perm) if imps.size else float("nan"),
        "wins_vs_zero": int(wins),
        "losses_vs_zero": int(losses),
        "win_margin_vs_zero": int(wins - losses),
    })
    return out


def evaluate_kshot_bias(
    residual: np.ndarray,
    base_pred: np.ndarray,
    high_mask: np.ndarray,
    subjects: np.ndarray,
    k: int,
    n_repeats: int,
    rng: np.random.Generator,
    fixed_pred: np.ndarray | None = None,
    n_perm: int = 3000,
) -> dict[str, Any]:
    ys = []
    ps = []
    fs = []
    group_rows = []
    unique_subjects = np.array(sorted(pd.unique(subjects)))

    for rep in range(n_repeats):
        for s in unique_subjects:
            idx_s = np.flatnonzero(subjects == s)
            if idx_s.size <= k:
                continue
            cal = rng.choice(idx_s, size=k, replace=False)
            cal_set = set(cal.tolist())
            eval_idx = np.array([i for i in idx_s if i not in cal_set and high_mask[i]], dtype=int)
            if eval_idx.size == 0:
                continue

            bias = float(np.mean(residual[cal] - base_pred[cal]))
            p = base_pred[eval_idx] + bias

            ys.append(residual[eval_idx])
            ps.append(p)
            if fixed_pred is not None:
                fs.append(fixed_pred[eval_idx])

            z = rmse(residual[eval_idx])
            m = rmse(residual[eval_idx] - p)
            group_rows.append({
                "repeat": rep,
                "subject": s,
                "n_eval": int(eval_idx.size),
                "improvement": z - m,
            })

    if not ys:
        return {}

    y = np.concatenate(ys)
    p = np.concatenate(ps)
    zero = rmse(y)
    model = rmse(y - p)
    out = {
        "n_eval": int(y.size),
        "subjects_eval": int(len(unique_subjects)),
        "zero_rmse": zero,
        "model_rmse": model,
        "lift_vs_zero": zero - model,
        "pearson": corr(y, p),
        "sign_acc": sign_acc(y, p),
    }
    if fixed_pred is not None and fs:
        fcat = np.concatenate(fs)
        out["fixed_rmse_same_eval"] = rmse(y - fcat)
        out["lift_vs_fixed_same_eval"] = out["fixed_rmse_same_eval"] - model
    else:
        out["fixed_rmse_same_eval"] = float("nan")
        out["lift_vs_fixed_same_eval"] = float("nan")

    g = pd.DataFrame(group_rows)
    imps = g["improvement"].to_numpy(dtype=float)
    ci_low, ci_high = bootstrap_ci_mean(imps, rng)
    wins = int(np.sum(imps > 1e-12))
    losses = int(np.sum(imps < -1e-12))
    out.update({
        "mean_subject_repeat_improvement_zero_minus_model": float(np.mean(imps)),
        "ci95_low_subject_repeat_improvement": ci_low,
        "ci95_high_subject_repeat_improvement": ci_high,
        "signflip_p_subject_repeat_mean_gt_zero": signflip_p_one_sided_gt_zero(imps, rng, n_perm=n_perm),
        "wins_vs_zero_subject_repeats": wins,
        "losses_vs_zero_subject_repeats": losses,
        "win_margin_vs_zero_subject_repeats": wins - losses,
    })
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, default=Path(".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy"))
    parser.add_argument("--index", type=Path, default=Path(".cache/idare_eeg_cache_index_baseline_corrected.csv"))
    parser.add_argument("--target", type=str, default="arousal")
    parser.add_argument("--seed", type=int, default=20260530)
    parser.add_argument("--n-kshot-repeats", type=int, default=150)
    parser.add_argument("--alphas", type=str, default="100,1000")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    if not args.cache.exists():
        raise FileNotFoundError(args.cache)
    if not args.index.exists():
        raise FileNotFoundError(args.index)

    print(f"[INFO] loading EEG cache={args.cache}")
    X = np.load(args.cache, mmap_mode="r")
    df = pd.read_csv(args.index)
    if len(df) != X.shape[0]:
        raise SystemExit(f"cache/index row mismatch: X={X.shape[0]} index={len(df)}")

    subj_col = first_col(df, ["subject_id", "subject", "test_subject", "participant_id", "participant", "subj"])
    stim_col = first_col(df, ["stimulus_id", "stimulus", "trial_id", "trial"])
    y_col = first_col(df, [f"{args.target}_score", args.target, f"label_{args.target}", f"{args.target}_rating"])
    if subj_col is None or stim_col is None or y_col is None:
        raise SystemExit(f"required columns missing. columns={list(df.columns)}")

    subjects = df[subj_col].to_numpy()
    _stim_pred, residual = loso_stimulus_prior_residual(df, y_col, stim_col)
    threshold, threshold_source = get_threshold(args.target, residual)
    high_mask = np.abs(residual) >= threshold

    print(f"[INFO] target={args.target} high_threshold={threshold:.6f} source={threshold_source} high_n={int(np.sum(high_mask))}")

    fixed_pred, fixed_note = load_fixed_bandpower_predictions(df, args.target, subj_col, stim_col)
    print(f"[INFO] fixed bandpower: {fixed_note}")

    print("[INFO] building raw EEG summary features...")
    F_raw = eeg_summary_features(np.asarray(X), trial_channel_zscore=False)
    print(f"[INFO] raw summary shape={F_raw.shape}")

    print("[INFO] building per-trial channel-zscore EEG summary features...")
    F_trialz = eeg_summary_features(np.asarray(X), trial_channel_zscore=True)
    print(f"[INFO] trial-z summary shape={F_trialz.shape}")

    alphas = [float(a.strip()) for a in args.alphas.split(",") if a.strip()]
    base_predictions: dict[str, np.ndarray] = {
        "zero_residual": np.zeros(len(df), dtype=float),
    }
    if fixed_pred is not None:
        base_predictions["fixed_eeg_bandpower_ridge_from_05aj"] = fixed_pred

    for alpha in alphas:
        print(f"[INFO] training LOSO raw_summary_ridge alpha={alpha}")
        base_predictions[f"raw_summary_ridge_alpha{alpha:g}"] = train_loso_ridge_predictions(F_raw, residual, subjects, alpha=alpha)

        print(f"[INFO] training LOSO trialz_summary_ridge alpha={alpha}")
        base_predictions[f"trialz_summary_ridge_alpha{alpha:g}"] = train_loso_ridge_predictions(F_trialz, residual, subjects, alpha=alpha)

    metric_rows: list[dict[str, Any]] = []
    subject_rows: list[dict[str, Any]] = []

    # k=0 pure LOSO, no calibration.
    for method, pred in base_predictions.items():
        met = per_group_metrics(residual, pred, high_mask, subjects, rng, fixed_pred=fixed_pred)
        row = {
            "target": args.target,
            "method": method,
            "adaptation": "none_pure_loso",
            "k_calibration": 0,
            "n_repeats": 1,
            **met,
        }
        metric_rows.append(row)

        idx = np.flatnonzero(high_mask)
        for s in pd.unique(subjects[idx]):
            m = idx[subjects[idx] == s]
            subject_rows.append({
                "target": args.target,
                "method": method,
                "adaptation": "none_pure_loso",
                "k_calibration": 0,
                "subject": s,
                "n_eval": int(m.size),
                "zero_rmse": rmse(residual[m]),
                "model_rmse": rmse(residual[m] - pred[m]),
                "improvement_zero_minus_model": rmse(residual[m]) - rmse(residual[m] - pred[m]),
            })

    # k-shot bias correction: direct test of calibration-dominant diagnosis from 06a3.
    for k in [4, 8, 16]:
        for method, pred in base_predictions.items():
            if method == "zero_residual":
                k_method = "kshot_subject_mean_only"
            else:
                k_method = method + "_plus_kshot_bias"
            met = evaluate_kshot_bias(
                residual=residual,
                base_pred=pred,
                high_mask=high_mask,
                subjects=subjects,
                k=k,
                n_repeats=args.n_kshot_repeats,
                rng=rng,
                fixed_pred=fixed_pred,
            )
            row = {
                "target": args.target,
                "method": k_method,
                "adaptation": "labelled_kshot_bias_correction",
                "k_calibration": k,
                "n_repeats": args.n_kshot_repeats,
                **met,
            }
            metric_rows.append(row)

    metrics_df = pd.DataFrame(metric_rows)

    # Stable ranking: first require practical lift, then fixed comparison, then paired evidence.
    metrics_df["passes_zero_gate"] = (
        (metrics_df["lift_vs_zero"] > 0.02)
        & (metrics_df.get("ci95_low_mean_subject_improvement", metrics_df.get("ci95_low_subject_repeat_improvement", pd.Series(np.nan, index=metrics_df.index))).fillna(-999) > 0)
    )
    # More robust pass columns because k=0 and k-shot have different CI names.
    ci_low = metrics_df["ci95_low_mean_subject_improvement"] if "ci95_low_mean_subject_improvement" in metrics_df.columns else pd.Series(np.nan, index=metrics_df.index)
    ci_low = ci_low.fillna(metrics_df["ci95_low_subject_repeat_improvement"] if "ci95_low_subject_repeat_improvement" in metrics_df.columns else np.nan)
    win_margin = metrics_df["win_margin_vs_zero"] if "win_margin_vs_zero" in metrics_df.columns else pd.Series(np.nan, index=metrics_df.index)
    win_margin = win_margin.fillna(metrics_df["win_margin_vs_zero_subject_repeats"] if "win_margin_vs_zero_subject_repeats" in metrics_df.columns else np.nan)
    metrics_df["passes_practical_gate"] = (metrics_df["lift_vs_zero"] > 0.02) & (ci_low > 0) & (win_margin > 3)
    if "lift_vs_fixed_same_eval" in metrics_df.columns and fixed_pred is not None:
        metrics_df["passes_fixed_reference_gate"] = metrics_df["lift_vs_fixed_same_eval"] > 0.02
    else:
        metrics_df["passes_fixed_reference_gate"] = False

    ranked = metrics_df.sort_values(
        by=["passes_practical_gate", "passes_fixed_reference_gate", "lift_vs_zero", "lift_vs_fixed_same_eval", "pearson"],
        ascending=[False, False, False, False, False],
        na_position="last",
    ).reset_index(drop=True)

    best = ranked.iloc[0].to_dict() if not ranked.empty else {}
    best_pure = ranked[ranked["k_calibration"] == 0].head(1)
    best_kshot = ranked[ranked["k_calibration"] > 0].head(1)

    if not best:
        decision = "NO_RESULT"
        interpretation = "No metrics were produced."
        action = "Inspect inputs."
    elif bool(best.get("passes_fixed_reference_gate", False)) and bool(best.get("passes_practical_gate", False)):
        decision = "GO_SUBJECT_ADAPTATION_IMPROVES_RESIDUAL_GATE"
        interpretation = "A normalization/adaptation candidate beats zero and the fixed EEG-bandpower reference on the high-disagreement residual gate."
        action = "Promote this candidate to a confirmatory rerun with locked B2 bridge checks."
    elif bool(best.get("passes_practical_gate", False)):
        decision = "PARTIAL_GO_BEATS_ZERO_NOT_FIXED_REFERENCE"
        interpretation = "The best candidate beats zero residual but does not clearly beat the fixed EEG-bandpower reference."
        action = "Use as diagnostic evidence; do not claim physiology improvement beyond fixed features."
    else:
        decision = "NO_GO_SUBJECT_NORMALIZATION_DOMAIN_ADAPTATION"
        interpretation = "Subject normalization/adaptation did not produce stable improvement under the current high-disagreement residual gate."
        action = "Stop generic model search; only continue with target reformulation or a specifically anchored bandpower/neural reproduction test."

    decision_df = pd.DataFrame([{
        "target": args.target,
        "decision": decision,
        "high_threshold": threshold,
        "high_threshold_source": threshold_source,
        "fixed_prediction_note": fixed_note,
        "best_method": best.get("method"),
        "best_adaptation": best.get("adaptation"),
        "best_k_calibration": best.get("k_calibration"),
        "best_lift_vs_zero": best.get("lift_vs_zero"),
        "best_lift_vs_fixed_same_eval": best.get("lift_vs_fixed_same_eval"),
        "best_pearson": best.get("pearson"),
        "best_sign_acc": best.get("sign_acc"),
        "best_passes_practical_gate": best.get("passes_practical_gate"),
        "best_passes_fixed_reference_gate": best.get("passes_fixed_reference_gate"),
        "interpretation": interpretation,
        "recommended_next_action": action,
    }])

    subject_df = pd.DataFrame(subject_rows)
    next_steps_df = pd.DataFrame([
        {
            "priority": 1,
            "step": "06a4b",
            "title": "Confirm best 06a4 candidate only if it passes",
            "purpose": "Rerun the best adaptation with more seeds/repeats and locked B2 bridge if 06a4 passes.",
            "success_condition": "Stable paired subject improvement and no degradation against locked B2.",
        },
        {
            "priority": 2,
            "step": "06a5",
            "title": "Augmentation rerun under residual gates",
            "purpose": "Rerun old augmentation only if it can be evaluated against 05ajb/06a1y/06a4 metrics.",
            "success_condition": "Augmentation beats fixed EEG-bandpower under subject-held-out residual gates.",
        },
        {
            "priority": 3,
            "step": "06a6",
            "title": "Target reformulation or calibration-first paper conclusion",
            "purpose": "If adaptation fails, write the evidence-based stop condition: LOSO residual decoding is calibration-dominant.",
            "success_condition": "A clear project decision that avoids unbounded architecture search.",
        },
    ])

    ROCA.mkdir(parents=True, exist_ok=True)
    decision_df.to_csv(ROCA / f"{OUT_PREFIX}_decision_table.csv", index=False)
    metrics_df.to_csv(ROCA / f"{OUT_PREFIX}_method_metrics.csv", index=False)
    ranked.to_csv(ROCA / f"{OUT_PREFIX}_ranked_methods.csv", index=False)
    subject_df.to_csv(ROCA / f"{OUT_PREFIX}_subject_stats_pure_loso.csv", index=False)
    next_steps_df.to_csv(ROCA / f"{OUT_PREFIX}_next_steps.csv", index=False)

    payload = {
        "title": "I-DARE subject-normalization and domain-adaptation ablation",
        "inputs": {
            "cache": str(args.cache),
            "index": str(args.index),
            "target": args.target,
            "subject_column": subj_col,
            "stimulus_column": stim_col,
            "score_column": y_col,
            "seed": args.seed,
            "n_kshot_repeats": args.n_kshot_repeats,
            "alphas": alphas,
        },
        "decision_table": decision_df.to_dict(orient="records"),
        "method_metrics": metrics_df.to_dict(orient="records"),
        "ranked_methods_top20": ranked.head(20).to_dict(orient="records"),
        "next_steps": next_steps_df.to_dict(orient="records"),
    }
    with open(ROCA / f"{OUT_PREFIX}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

    report = []
    report.append("# I-DARE subject-normalization and domain-adaptation ablation\n")
    report.append("This step follows 06a3: arousal residuals looked calibration-dominant, so this tests whether subject normalization or k-shot bias/context can turn that structure into high-disagreement residual improvement.\n")
    report.append("\n## Decision table\n")
    report.append(md_table(decision_df))
    report.append("\n## Ranked methods, top 20\n")
    cols = [
        "method", "adaptation", "k_calibration", "n_eval", "zero_rmse", "model_rmse",
        "lift_vs_zero", "fixed_rmse_same_eval", "lift_vs_fixed_same_eval",
        "pearson", "sign_acc", "passes_practical_gate", "passes_fixed_reference_gate",
    ]
    report.append(md_table(ranked[[c for c in cols if c in ranked.columns]].head(20)))
    report.append("\n## Next steps\n")
    report.append(md_table(next_steps_df))
    report.append("\n## Notes\n")
    report.append("- `none_pure_loso` uses no held-out subject labels.\n")
    report.append("- `labelled_kshot_bias_correction` uses k calibration ratings from the held-out subject; it is a calibration/adaptation diagnostic, not zero-shot LOSO.\n")
    report.append("- The fixed EEG-bandpower predictions are loaded from prior ROCA prediction files when available, so comparisons are on the same evaluation rows.\n")
    (ROCA / f"{OUT_PREFIX}.md").write_text("\n".join(report), encoding="utf-8")

    print("ROCA step 06a4 completed.")
    for suffix in [
        ".md", ".json", "_decision_table.csv", "_method_metrics.csv",
        "_ranked_methods.csv", "_subject_stats_pure_loso.csv", "_next_steps.csv",
    ]:
        print(f"wrote: {ROCA / (OUT_PREFIX + suffix)}")

    print("\nDecision table:")
    print(decision_df.to_string(index=False))

    print("\nTop ranked methods:")
    print(ranked[[c for c in cols if c in ranked.columns]].head(20).to_string(index=False))

    print("\nNext steps:")
    print(next_steps_df.to_string(index=False))

    print("\n================== KEY OUTPUTS ==================")
    print(decision_df.to_csv(index=False).strip())
    print()
    print(ranked[[c for c in cols if c in ranked.columns]].head(20).to_csv(index=False).strip())
    print()
    print(next_steps_df.to_csv(index=False).strip())

    print("\n================== SIZE CHECK ==================")
    for p in sorted(ROCA.glob(f"{OUT_PREFIX}*")):
        print(f"{p.stat().st_size/1024:.1f}K\t{p}")

    print("\n================== GIT STATUS ==================")
    print(git_short())

    print("[INFO] If inspection is OK:")
    print(f"git add scripts/roca/06a4_idare_subject_normalization_domain_adaptation.py docs/roca/{OUT_PREFIX}*")
    print('git commit -m "Add I-DARE subject-normalization domain-adaptation ablation"')
    print("git push")


if __name__ == "__main__":
    main()
