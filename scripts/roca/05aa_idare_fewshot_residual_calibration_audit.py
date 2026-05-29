#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ROCA = ROOT / "docs" / "roca"
CACHE = ROOT / ".cache"
DEFAULT_TRIAL_INDEX = CACHE / "idare_trial_index.csv"
DEFAULT_OUT_PREFIX = "idare_fewshot_residual_calibration_audit_current"
TARGETS = {"valence": "valence_score", "arousal": "arousal_score"}
LABEL_POLICIES = ["midpoint_as_low", "midpoint_as_high", "discard_midpoint"]
EPS = 1e-12


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--trial-index", type=Path, default=DEFAULT_TRIAL_INDEX)
    p.add_argument("--out-prefix", type=str, default=DEFAULT_OUT_PREFIX)
    p.add_argument("--k-values", type=str, default="0,1,2,4,8,16")
    p.add_argument("--n-repeats", type=int, default=200)
    p.add_argument("--seed", type=int, default=20260517)
    p.add_argument("--max-subjects", type=int, default=None)
    return p.parse_args()


def stable_seed(*parts: Any) -> int:
    payload = "|".join(str(p) for p in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little") % (2**32)


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
        return None if not math.isfinite(v) else v
    if isinstance(x, float):
        return None if not math.isfinite(x) else x
    return x


def pearson(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y, p = y[m], p[m]
    if len(y) < 2 or np.std(y) < EPS or np.std(p) < EPS:
        return None
    return float(np.corrcoef(y, p)[0, 1])


def spearman(y, p):
    return pearson(pd.Series(y).rank(method="average"), pd.Series(p).rank(method="average"))


def ccc(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y, p = y[m], p[m]
    if len(y) < 2:
        return None
    my, mp = float(np.mean(y)), float(np.mean(p))
    vy, vp = float(np.var(y)), float(np.var(p))
    cov = float(np.mean((y - my) * (p - mp)))
    denom = vy + vp + (my - mp) ** 2
    if denom < EPS:
        return None
    return float(2.0 * cov / denom)


def auroc(y_bin, score):
    y_bin = np.asarray(y_bin, dtype=int)
    score = np.asarray(score, dtype=float)
    m = np.isfinite(score)
    y_bin, score = y_bin[m], score[m]
    n_pos = int((y_bin == 1).sum())
    n_neg = int((y_bin == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return None
    ranks = pd.Series(score).rank(method="average").to_numpy(dtype=float)
    rank_sum_pos = float(ranks[y_bin == 1].sum())
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def regression_metrics(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    err = p - y
    return {
        "n": int(len(y)),
        "mae": safe_float(np.mean(np.abs(err))),
        "rmse": safe_float(np.sqrt(np.mean(err * err))),
        "pearson": pearson(y, p),
        "spearman": spearman(y, p),
        "ccc": ccc(y, p),
        "y_true_mean": safe_float(np.mean(y)),
        "y_true_std": safe_float(np.std(y)),
        "y_pred_mean": safe_float(np.mean(p)),
        "y_pred_std": safe_float(np.std(p)),
        "residual_mean": safe_float(np.mean(y - p)),
        "residual_std": safe_float(np.std(y - p)),
    }


def binary_arrays(y_score, pred_score, policy):
    y_score = np.asarray(y_score, dtype=float)
    pred_score = np.asarray(pred_score, dtype=float)
    m = np.isfinite(y_score) & np.isfinite(pred_score)
    if policy == "midpoint_as_low":
        y_bin = (y_score[m] > 5.0).astype(int)
        pred_bin = (pred_score[m] > 5.0).astype(int)
    elif policy == "midpoint_as_high":
        y_bin = (y_score[m] >= 5.0).astype(int)
        pred_bin = (pred_score[m] >= 5.0).astype(int)
    elif policy == "discard_midpoint":
        m = m & (y_score != 5.0)
        y_bin = (y_score[m] > 5.0).astype(int)
        pred_bin = (pred_score[m] > 5.0).astype(int)
    else:
        raise ValueError(policy)
    return y_bin, pred_bin, pred_score[m]


def binary_metrics(y_score, pred_score, policy):
    y_bin, pred_bin, score = binary_arrays(y_score, pred_score, policy)
    if len(y_bin) == 0:
        return {"binary_n": 0, "accuracy": None, "balanced_accuracy": None, "macro_f1": None, "auroc": None, "n_low": 0, "n_high": 0, "true_high_rate": None, "pred_high_rate": None}
    recalls, f1s = [], []
    for cls in [0, 1]:
        tp = int(((y_bin == cls) & (pred_bin == cls)).sum())
        fp = int(((y_bin != cls) & (pred_bin == cls)).sum())
        fn = int(((y_bin == cls) & (pred_bin != cls)).sum())
        support = int((y_bin == cls).sum())
        if support > 0:
            recalls.append(tp / support)
        denom = 2 * tp + fp + fn
        f1s.append((2 * tp / denom) if denom > 0 else 0.0)
    return {
        "binary_n": int(len(y_bin)),
        "accuracy": safe_float(np.mean(y_bin == pred_bin)),
        "balanced_accuracy": safe_float(np.mean(recalls)),
        "macro_f1": safe_float(np.mean(f1s)),
        "auroc": auroc(y_bin, score),
        "n_low": int((y_bin == 0).sum()),
        "n_high": int((y_bin == 1).sum()),
        "true_high_rate": safe_float(np.mean(y_bin == 1)),
        "pred_high_rate": safe_float(np.mean(pred_bin == 1)),
    }


def md_cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6f}" if math.isfinite(v) else ""
    try:
        if bool(pd.isna(v)):
            return ""
    except (TypeError, ValueError):
        pass
    return str(v).replace("|", "\\|").replace("\n", " ")


def md_table(df: pd.DataFrame, cols):
    if df.empty:
        return "_No rows._\n"
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in df[cols].to_dict(orient="records"):
        lines.append("| " + " | ".join(md_cell(row.get(c)) for c in cols) + " |")
    return "\n".join(lines) + "\n"


def load_idare(path: Path):
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    required = ["subject_id", "stimulus_id", "valence_score", "arousal_score"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"trial index missing columns: {missing}")
    df = df[required].copy()
    df["subject_id"] = df["subject_id"].astype(int)
    df["stimulus_id"] = df["stimulus_id"].astype(str)
    return df.drop_duplicates(["subject_id", "stimulus_id"]).reset_index(drop=True)


def build_loso_stimulus_prior(df: pd.DataFrame, target: str, score_col: str):
    rows = []
    for test_subject in sorted(df["subject_id"].unique()):
        train = df[df["subject_id"].ne(test_subject)]
        test = df[df["subject_id"].eq(test_subject)].copy()
        global_mean = float(train[score_col].mean())
        stim_mean = train.groupby("stimulus_id")[score_col].mean()
        pred_stim = test["stimulus_id"].map(stim_mean).astype(float).fillna(global_mean).to_numpy(dtype=float)
        out = test[["subject_id", "stimulus_id"]].copy()
        out["target"] = target
        out["y_true_score"] = test[score_col].to_numpy(dtype=float)
        out["stimulus_pred_score"] = pred_stim
        out["stimulus_residual"] = out["y_true_score"] - out["stimulus_pred_score"]
        rows.append(out)
    return pd.concat(rows, ignore_index=True)


def run_fewshot_for_target(base: pd.DataFrame, target: str, k_values, n_repeats: int, seed: int):
    pred_rows = []
    for subject_id in sorted(base["subject_id"].unique()):
        subj = base[base["subject_id"].eq(subject_id)].copy().reset_index(drop=True)
        n_trials = len(subj)
        for k in k_values:
            repeats = 1 if k <= 0 else n_repeats
            for rep in range(repeats):
                if k <= 0:
                    cal_idx = np.array([], dtype=int)
                else:
                    rng = np.random.default_rng(stable_seed(seed, target, subject_id, k, rep))
                    kk = min(k, max(0, n_trials - 1))
                    cal_idx = np.sort(rng.choice(np.arange(n_trials), size=kk, replace=False))
                is_cal = np.zeros(n_trials, dtype=bool)
                is_cal[cal_idx] = True
                test_mask = ~is_cal
                if cal_idx.size == 0:
                    bias_hat = 0.0
                    shrink_bias_hat = 0.0
                else:
                    cal_res = subj.loc[is_cal, "stimulus_residual"].to_numpy(dtype=float)
                    bias_hat = float(np.mean(cal_res))
                    tau = 4.0
                    shrink_bias_hat = float((cal_idx.size / (cal_idx.size + tau)) * bias_hat)
                for model, bias in [("stimulus_only", 0.0), ("stimulus_plus_fewshot_bias", bias_hat), ("stimulus_plus_fewshot_bias_shrink4", shrink_bias_hat)]:
                    tmp = subj.loc[test_mask, ["subject_id", "stimulus_id", "target", "y_true_score", "stimulus_pred_score", "stimulus_residual"]].copy()
                    tmp["k_calibration"] = int(k)
                    tmp["repeat"] = int(rep)
                    tmp["model"] = model
                    tmp["calibration_n"] = int(cal_idx.size)
                    tmp["estimated_subject_bias"] = float(bias)
                    tmp["y_pred_score"] = tmp["stimulus_pred_score"] + float(bias)
                    tmp["predicted_residual"] = float(bias)
                    pred_rows.append(tmp)
    return pd.concat(pred_rows, ignore_index=True)


def aggregate(pred: pd.DataFrame):
    main_rows, binary_rows, subject_rows = [], [], []
    for (target, k, model), g in pred.groupby(["target", "k_calibration", "model"], dropna=False):
        row = {"target": target, "k_calibration": int(k), "model": model}
        row.update(regression_metrics(g["y_true_score"], g["y_pred_score"]))
        dev = regression_metrics(g["stimulus_residual"], g["predicted_residual"])
        for name, val in dev.items():
            if name != "n":
                row[f"residual_{name}"] = val
        main_rows.append(row)
        for policy in LABEL_POLICIES:
            brow = {"target": target, "k_calibration": int(k), "model": model, "label_policy": policy}
            brow.update(binary_metrics(g["y_true_score"], g["y_pred_score"], policy))
            binary_rows.append(brow)

    main = pd.DataFrame(main_rows)
    binary = pd.DataFrame(binary_rows)

    for (target, k, model, subject_id), g in pred.groupby(["target", "k_calibration", "model", "subject_id"], dropna=False):
        row = {"target": target, "k_calibration": int(k), "model": model, "subject_id": int(subject_id)}
        row.update(regression_metrics(g["y_true_score"], g["y_pred_score"]))
        dev = regression_metrics(g["stimulus_residual"], g["predicted_residual"])
        row["residual_rmse"] = dev["rmse"]
        row["residual_mae"] = dev["mae"]
        subject_rows.append(row)
    subject = pd.DataFrame(subject_rows)

    for (target, k), g in main.groupby(["target", "k_calibration"]):
        base = g[g["model"].eq("stimulus_only")]
        if base.empty:
            continue
        base = base.iloc[0]
        for idx in g.index:
            for m in ["mae", "rmse", "residual_mae", "residual_rmse"]:
                main.loc[idx, f"lift_vs_stimulus_{m}"] = float(base[m]) - float(main.loc[idx, m])
            for m in ["pearson", "spearman", "ccc"]:
                bv, rv = base.get(m), main.loc[idx, m]
                main.loc[idx, f"lift_vs_stimulus_{m}"] = np.nan if pd.isna(bv) or pd.isna(rv) else float(rv) - float(bv)

    for (target, k, policy), g in binary.groupby(["target", "k_calibration", "label_policy"]):
        base = g[g["model"].eq("stimulus_only")]
        if base.empty:
            continue
        base = base.iloc[0]
        for idx in g.index:
            for m in ["accuracy", "balanced_accuracy", "macro_f1", "auroc"]:
                bv, rv = base.get(m), binary.loc[idx, m]
                binary.loc[idx, f"lift_vs_stimulus_{m}"] = np.nan if pd.isna(bv) or pd.isna(rv) else float(rv) - float(bv)

    win_rows = []
    for (target, k), g in subject.groupby(["target", "k_calibration"]):
        base = g[g["model"].eq("stimulus_only")][["subject_id", "rmse", "residual_rmse"]].rename(columns={"rmse": "stimulus_rmse", "residual_rmse": "stimulus_residual_rmse"})
        for model, gm in g[g["model"].ne("stimulus_only")].groupby("model"):
            merged = gm.merge(base, on="subject_id", how="inner")
            delta = merged["rmse"].to_numpy(dtype=float) - merged["stimulus_rmse"].to_numpy(dtype=float)
            dev_delta = merged["residual_rmse"].to_numpy(dtype=float) - merged["stimulus_residual_rmse"].to_numpy(dtype=float)
            win_rows.append({
                "target": target,
                "k_calibration": int(k),
                "model": model,
                "subjects": int(len(merged)),
                "rmse_wins": int((delta < 0).sum()),
                "rmse_losses": int((delta > 0).sum()),
                "rmse_ties": int((delta == 0).sum()),
                "rmse_win_margin": int((delta < 0).sum() - (delta > 0).sum()),
                "mean_delta_rmse_model_minus_stimulus": safe_float(np.mean(delta)),
                "median_delta_rmse_model_minus_stimulus": safe_float(np.median(delta)),
                "worst_regression_delta_rmse": safe_float(np.max(delta)),
                "best_gain_delta_rmse": safe_float(np.min(delta)),
                "residual_rmse_wins": int((dev_delta < 0).sum()),
                "residual_rmse_losses": int((dev_delta > 0).sum()),
                "residual_rmse_win_margin": int((dev_delta < 0).sum() - (dev_delta > 0).sum()),
            })
    wins = pd.DataFrame(win_rows)
    return main, binary, subject, wins


def make_verdict(main: pd.DataFrame, wins: pd.DataFrame):
    rows = []
    for target, g in main[main["model"].ne("stimulus_only")].groupby("target"):
        best = g.sort_values(["lift_vs_stimulus_rmse", "k_calibration"], ascending=[False, True]).iloc[0]
        w = wins[wins["target"].eq(target) & wins["k_calibration"].eq(int(best["k_calibration"])) & wins["model"].eq(best["model"])]
        w = w.iloc[0] if not w.empty else pd.Series(dtype=object)
        lift = safe_float(best.get("lift_vs_stimulus_rmse"))
        residual_lift = safe_float(best.get("lift_vs_stimulus_residual_rmse"))
        win_margin = safe_float(w.get("rmse_win_margin"))
        if lift is not None and lift > 0.02 and residual_lift is not None and residual_lift > 0.02 and win_margin is not None and win_margin > 3:
            decision = "GO_FEWSHOT_SUBJECT_CALIBRATION"
            reason = "few-shot subject bias beats stimulus-only in pooled and subject-level residual metrics"
        elif lift is not None and lift > 0.0:
            decision = "WEAK_GO_FEWSHOT_CALIBRATION_NEEDS_CONFIRMATION"
            reason = "few-shot calibration has positive pooled lift but does not meet practical margin"
        else:
            decision = "NO_GO_FEWSHOT_CURRENT_SIMPLE_BIAS"
            reason = "simple few-shot subject-bias calibration does not beat stimulus-only enough"
        rows.append({
            "target": target,
            "decision": decision,
            "best_model": best["model"],
            "best_k_calibration": int(best["k_calibration"]),
            "best_lift_vs_stimulus_rmse": lift,
            "best_lift_vs_stimulus_residual_rmse": residual_lift,
            "best_rmse": safe_float(best["rmse"]),
            "best_residual_rmse": safe_float(best["residual_rmse"]),
            "rmse_win_margin": win_margin,
            "reason": reason,
        })
    return pd.DataFrame(rows)


def main():
    args = parse_args()
    ROCA.mkdir(parents=True, exist_ok=True)
    k_values = [int(x.strip()) for x in args.k_values.split(",") if x.strip()]
    df = load_idare(args.trial_index)
    if args.max_subjects is not None:
        keep = sorted(df["subject_id"].unique())[: int(args.max_subjects)]
        df = df[df["subject_id"].isin(keep)].copy()
    pred_parts = []
    for target, score_col in TARGETS.items():
        print(f"[TARGET] {target}")
        base = build_loso_stimulus_prior(df, target, score_col)
        pred_parts.append(run_fewshot_for_target(base, target, k_values, args.n_repeats, args.seed))
    pred = pd.concat(pred_parts, ignore_index=True)
    main_metrics, binary_metrics, subject_metrics, winloss = aggregate(pred)
    verdict = make_verdict(main_metrics, winloss)

    out_prefix = args.out_prefix
    out_md = ROCA / f"{out_prefix}.md"
    out_json = ROCA / f"{out_prefix}.json"
    out_pred = ROCA / f"{out_prefix}_predictions.csv"
    out_main = ROCA / f"{out_prefix}_main_metrics.csv"
    out_binary = ROCA / f"{out_prefix}_binary_metrics.csv"
    out_subject = ROCA / f"{out_prefix}_subject_metrics.csv"
    out_winloss = ROCA / f"{out_prefix}_subject_winloss.csv"
    out_verdict = ROCA / f"{out_prefix}_verdict.csv"

    pred.to_csv(out_pred, index=False)
    main_metrics.to_csv(out_main, index=False)
    binary_metrics.to_csv(out_binary, index=False)
    subject_metrics.to_csv(out_subject, index=False)
    winloss.to_csv(out_winloss, index=False)
    verdict.to_csv(out_verdict, index=False)

    report = {
        "step": "05aa I-DARE few-shot residual subject calibration audit",
        "question": "Can subject-specific residual structure be exploited with a few calibration labels from the held-out subject?",
        "method": {
            "baseline": "LOSO stimulus-only",
            "model_1": "stimulus_only",
            "model_2": "stimulus_plus_fewshot_bias = stimulus prior + mean residual of k calibration trials",
            "model_3": "stimulus_plus_fewshot_bias_shrink4 = empirical-Bayes shrinkage with tau=4",
            "k_values": k_values,
            "n_repeats": args.n_repeats,
            "seed": args.seed,
            "max_subjects": args.max_subjects,
        },
        "outputs": {"md": str(out_md), "json": str(out_json), "predictions": str(out_pred), "main_metrics": str(out_main), "binary_metrics": str(out_binary), "subject_metrics": str(out_subject), "subject_winloss": str(out_winloss), "verdict": str(out_verdict)},
        "verdict": verdict.to_dict(orient="records"),
        "main_metrics": main_metrics.to_dict(orient="records"),
    }
    out_json.write_text(json.dumps(clean_json(report), indent=2, ensure_ascii=False), encoding="utf-8")

    main_cols = ["target", "k_calibration", "model", "n", "rmse", "lift_vs_stimulus_rmse", "residual_rmse", "lift_vs_stimulus_residual_rmse", "pearson", "ccc"]
    binary_cols = ["target", "k_calibration", "model", "label_policy", "accuracy", "balanced_accuracy", "macro_f1", "auroc", "lift_vs_stimulus_accuracy", "lift_vs_stimulus_balanced_accuracy"]
    win_cols = ["target", "k_calibration", "model", "subjects", "rmse_wins", "rmse_losses", "rmse_win_margin", "mean_delta_rmse_model_minus_stimulus", "worst_regression_delta_rmse", "best_gain_delta_rmse"]

    lines = []
    lines.append("# I-DARE Few-Shot Residual Subject Calibration Audit\n")
    lines.append("This audit tests whether the subject-structured residual found in 05z can be exploited by a few calibration labels from the held-out subject.\n")
    lines.append("## Models\n")
    lines.append("- `stimulus_only`: LOSO stimulus prior.")
    lines.append("- `stimulus_plus_fewshot_bias`: stimulus prior plus the mean residual estimated from k calibration trials of the same held-out subject.")
    lines.append("- `stimulus_plus_fewshot_bias_shrink4`: conservative shrinkage version of the same subject-bias estimate.\n")
    lines.append("## Verdict\n")
    lines.append(md_table(verdict, list(verdict.columns)))
    lines.append("\n## Main metrics\n")
    show_main = main_metrics.sort_values(["target", "k_calibration", "model"])
    lines.append(md_table(show_main, [c for c in main_cols if c in show_main.columns]))
    lines.append("\n## Binary metrics\n")
    show_bin = binary_metrics[binary_metrics["label_policy"].isin(["midpoint_as_low", "midpoint_as_high"])].copy()
    show_bin = show_bin.sort_values(["target", "k_calibration", "label_policy", "model"])
    lines.append(md_table(show_bin, [c for c in binary_cols if c in show_bin.columns]))
    lines.append("\n## Subject win/loss\n")
    show_wins = winloss.sort_values(["target", "k_calibration", "model"])
    lines.append(md_table(show_wins, [c for c in win_cols if c in show_wins.columns]))
    lines.append("\n## Interpretation\n")
    lines.append("- If few-shot subject-bias calibration beats stimulus-only, the residual is practically usable through subject adaptation.\n- This still does not prove EEG/EMG value. It creates the next baseline that physiology must beat.\n- The next audit after this should test physiology on top of the few-shot calibrated baseline, not only on top of stimulus-only.\n")
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05aa completed.")
    for p in [out_md, out_json, out_pred, out_main, out_binary, out_subject, out_winloss, out_verdict]:
        print(f"wrote: {p}")
    print("\nVerdict:")
    print(verdict.to_string(index=False))
    print("\nBest rows by target:")
    best_rows = main_metrics[main_metrics["model"].ne("stimulus_only")].sort_values(["target", "lift_vs_stimulus_rmse"], ascending=[True, False]).groupby("target", as_index=False).head(5)
    print(best_rows[main_cols].to_string(index=False))


if __name__ == "__main__":
    main()
