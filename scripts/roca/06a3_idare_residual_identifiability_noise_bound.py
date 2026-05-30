#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROCA = Path("docs/roca")
OUT_PREFIX = "idare_06a3_residual_identifiability_noise_bound_current"


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


def signflip_p_one_sided_gt_zero(x: np.ndarray, n_perm: int, rng: np.random.Generator) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return float("nan")
    obs = float(np.mean(x))
    if abs(obs) <= 1e-12:
        return 1.0
    signs = rng.choice([-1.0, 1.0], size=(n_perm, x.size))
    sims = np.mean(signs * x[None, :], axis=1)
    return float((np.sum(sims >= obs) + 1) / (n_perm + 1))


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


def loso_stimulus_prior_residual(
    df: pd.DataFrame,
    y_col: str,
    subj_col: str,
    stim_col: str,
) -> tuple[np.ndarray, np.ndarray]:
    y = df[y_col].astype(float).to_numpy()
    stim = df[stim_col].to_numpy()
    subj = df[subj_col].to_numpy()

    stim_sum = df.groupby(stim_col)[y_col].transform("sum").astype(float).to_numpy()
    stim_count = df.groupby(stim_col)[y_col].transform("count").astype(float).to_numpy()

    # In the normal I-DARE table there is one rating per subject per stimulus.
    # Exclude the held-out subject's own rating from the stimulus prior.
    pred = np.where(stim_count > 1, (stim_sum - y) / np.maximum(stim_count - 1, 1), np.nan)

    # Fallback only for pathological missing-stimulus cases.
    global_mean = float(np.nanmean(y))
    pred = np.where(np.isfinite(pred), pred, global_mean)
    residual = y - pred
    return pred.astype(float), residual.astype(float)


def leave_one_trial_subject_mean_pred(
    residual: np.ndarray,
    df: pd.DataFrame,
    subj_col: str,
) -> np.ndarray:
    tmp = pd.DataFrame({"subject": df[subj_col].to_numpy(), "r": residual})
    s_sum = tmp.groupby("subject")["r"].transform("sum").astype(float).to_numpy()
    s_cnt = tmp.groupby("subject")["r"].transform("count").astype(float).to_numpy()
    pred = np.where(s_cnt > 1, (s_sum - residual) / np.maximum(s_cnt - 1, 1), 0.0)
    return pred.astype(float)


def kshot_subject_mean_oracle(
    residual: np.ndarray,
    df: pd.DataFrame,
    subj_col: str,
    k_values: list[int],
    rng: np.random.Generator,
    n_repeats: int,
) -> pd.DataFrame:
    subjects = np.array(sorted(pd.unique(df[subj_col])))
    by_subject = {s: np.flatnonzero(df[subj_col].to_numpy() == s) for s in subjects}
    zero_rmse = rmse(residual)
    rows: list[dict[str, Any]] = []
    for k in k_values:
        pooled_rmses = []
        pooled_lifts = []
        per_subject_lifts_all = []
        for rep in range(n_repeats):
            errors = []
            subject_lifts = []
            for s in subjects:
                idx = by_subject[s]
                if idx.size <= k:
                    continue
                cal = rng.choice(idx, size=k, replace=False)
                eval_idx = np.setdiff1d(idx, cal, assume_unique=False)
                mu = float(np.mean(residual[cal]))
                e_zero = residual[eval_idx]
                e_model = residual[eval_idx] - mu
                errors.append(e_model)
                subject_lifts.append(rmse(e_zero) - rmse(e_model))
            if not errors:
                continue
            err = np.concatenate(errors)
            this_rmse = rmse(err)
            pooled_rmses.append(this_rmse)
            pooled_lifts.append(zero_rmse - this_rmse)
            per_subject_lifts_all.extend(subject_lifts)
        rows.append({
            "k_calibration_trials": k,
            "n_repeats": n_repeats,
            "pooled_rmse_mean": float(np.nanmean(pooled_rmses)) if pooled_rmses else float("nan"),
            "pooled_lift_vs_zero_mean": float(np.nanmean(pooled_lifts)) if pooled_lifts else float("nan"),
            "pooled_lift_vs_zero_p10": float(np.nanquantile(pooled_lifts, 0.10)) if pooled_lifts else float("nan"),
            "pooled_lift_vs_zero_p90": float(np.nanquantile(pooled_lifts, 0.90)) if pooled_lifts else float("nan"),
            "subject_lift_mean_over_repeats": float(np.nanmean(per_subject_lifts_all)) if per_subject_lifts_all else float("nan"),
        })
    return pd.DataFrame(rows)


def split_half_reliability(
    residual: np.ndarray,
    df: pd.DataFrame,
    subj_col: str,
    stim_col: str,
    rng: np.random.Generator,
    n_repeats: int,
    high_mask: np.ndarray | None = None,
) -> dict[str, float]:
    if high_mask is None:
        mask = np.ones(len(df), dtype=bool)
    else:
        mask = np.asarray(high_mask, dtype=bool)

    d = pd.DataFrame({
        "subject": df[subj_col].to_numpy(),
        "stimulus": df[stim_col].to_numpy(),
        "r": residual,
        "mask": mask,
    })
    d = d[d["mask"]].copy()

    subjects = np.array(sorted(pd.unique(d["subject"])))
    stimuli = np.array(sorted(pd.unique(d["stimulus"])))

    subj_rs = []
    for _ in range(n_repeats):
        a_vals = []
        b_vals = []
        for s in subjects:
            vals = d.loc[d["subject"] == s, "r"].to_numpy(dtype=float)
            if vals.size < 4:
                continue
            perm = rng.permutation(vals.size)
            half = vals.size // 2
            a_vals.append(float(np.mean(vals[perm[:half]])))
            b_vals.append(float(np.mean(vals[perm[half:]])))
        subj_rs.append(corr(np.array(a_vals), np.array(b_vals)))

    stim_rs = []
    for _ in range(n_repeats):
        if subjects.size < 4:
            stim_rs.append(float("nan"))
            continue
        perm_s = rng.permutation(subjects)
        half = subjects.size // 2
        s_a = set(perm_s[:half])
        s_b = set(perm_s[half:])
        a_vals = []
        b_vals = []
        for st in stimuli:
            da = d[(d["stimulus"] == st) & (d["subject"].isin(s_a))]["r"].to_numpy(dtype=float)
            db = d[(d["stimulus"] == st) & (d["subject"].isin(s_b))]["r"].to_numpy(dtype=float)
            if da.size >= 2 and db.size >= 2:
                a_vals.append(float(np.mean(da)))
                b_vals.append(float(np.mean(db)))
        stim_rs.append(corr(np.array(a_vals), np.array(b_vals)))

    def summarize(vals: list[float], prefix: str) -> dict[str, float]:
        arr = np.asarray(vals, dtype=float)
        arr = arr[np.isfinite(arr)]
        if arr.size == 0:
            return {
                f"{prefix}_mean_r": float("nan"),
                f"{prefix}_median_r": float("nan"),
                f"{prefix}_p10_r": float("nan"),
                f"{prefix}_p90_r": float("nan"),
                f"{prefix}_n_valid": 0,
            }
        return {
            f"{prefix}_mean_r": float(np.mean(arr)),
            f"{prefix}_median_r": float(np.median(arr)),
            f"{prefix}_p10_r": float(np.quantile(arr, 0.10)),
            f"{prefix}_p90_r": float(np.quantile(arr, 0.90)),
            f"{prefix}_n_valid": int(arr.size),
        }

    out = {}
    out.update(summarize(subj_rs, "subject_style_split_half"))
    out.update(summarize(stim_rs, "shared_stimulus_residual_split_half"))
    out["n_rows_used"] = int(len(d))
    out["n_subjects_used"] = int(d["subject"].nunique()) if len(d) else 0
    out["n_stimuli_used"] = int(d["stimulus"].nunique()) if len(d) else 0
    return out


def variance_decomposition(residual: np.ndarray, df: pd.DataFrame, subj_col: str, stim_col: str) -> dict[str, float]:
    d = pd.DataFrame({
        "subject": df[subj_col].to_numpy(),
        "stimulus": df[stim_col].to_numpy(),
        "r": residual,
    })
    total_var = float(np.nanvar(d["r"].to_numpy(dtype=float), ddof=0))
    subj_mean = d.groupby("subject")["r"].mean()
    stim_mean = d.groupby("stimulus")["r"].mean()
    subj_var = float(np.nanvar(subj_mean.to_numpy(dtype=float), ddof=0))
    stim_var = float(np.nanvar(stim_mean.to_numpy(dtype=float), ddof=0))
    return {
        "total_residual_variance": total_var,
        "subject_mean_variance": subj_var,
        "stimulus_mean_variance": stim_var,
        "subject_mean_variance_ratio_to_total": subj_var / total_var if total_var > 0 else float("nan"),
        "stimulus_mean_variance_ratio_to_total": stim_var / total_var if total_var > 0 else float("nan"),
    }


def subject_stats_from_predictions(
    residual: np.ndarray,
    pred_residual: np.ndarray,
    df: pd.DataFrame,
    subj_col: str,
) -> pd.DataFrame:
    rows = []
    for s, g in pd.DataFrame({
        "subject": df[subj_col].to_numpy(),
        "r": residual,
        "p": pred_residual,
    }).groupby("subject"):
        r = g["r"].to_numpy(dtype=float)
        p = g["p"].to_numpy(dtype=float)
        zero = rmse(r)
        model = rmse(r - p)
        rows.append({
            "subject": s,
            "n": int(len(g)),
            "zero_rmse": zero,
            "model_rmse": model,
            "improvement_zero_minus_model": zero - model,
        })
    return pd.DataFrame(rows)


def read_reference_tables() -> dict[str, Any]:
    refs: dict[str, Any] = {}

    v05ajb = read_csv_optional(ROCA / "idare_high_disagreement_direct_deviation_confirmatory_stats_current_verdict.csv")
    if not v05ajb.empty:
        refs["05ajb_confirmed_high_disagreement"] = v05ajb.to_dict(orient="records")

    s06a1y = read_csv_optional(ROCA / "idare_06a1y_split_control_deep_learning_probe_current_split_summary.csv")
    if not s06a1y.empty:
        refs["06a1y_split_summary"] = s06a1y.to_dict(orient="records")

    z06a1z = read_csv_optional(ROCA / "idare_06a1z_prior_experiment_map_and_root_cause_autopsy_current_root_cause_table.csv")
    if not z06a1z.empty:
        refs["06a1z_root_cause"] = z06a1z.to_dict(orient="records")

    return refs


def decide_target(row: dict[str, Any]) -> tuple[str, str, str]:
    target = row["target"]
    shared = row.get("shared_stimulus_residual_split_half_mean_r", float("nan"))
    subj = row.get("subject_style_split_half_mean_r", float("nan"))
    subj_lift = row.get("leave_one_trial_subject_mean_oracle_lift_vs_zero", float("nan"))
    k16 = row.get("k16_pooled_lift_vs_zero_mean", float("nan"))
    high_shared = row.get("high_disagreement_shared_stimulus_residual_split_half_mean_r", float("nan"))

    if target == "arousal":
        if (np.isfinite(subj) and subj >= 0.50) and (not np.isfinite(shared) or shared <= 0.10) and (np.isfinite(subj_lift) and subj_lift >= 0.10):
            return (
                "CALIBRATION_DOMINANT_NOT_GLOBAL_RESIDUAL_DECODING",
                "Subject-style residual structure is repeatable, but shared stimulus residual structure is weak/non-repeatable. The viable route is explicit calibration/subject adaptation, not larger generic CNN search.",
                "Run 06a4 subject-normalization/domain-adaptation and k-shot context ablations; require improvement over fixed EEG-bandpower and B2 locked gates.",
            )
        if np.isfinite(high_shared) and high_shared > 0.15:
            return (
                "HIGH_DISAGREEMENT_SIGNAL_MAY_BE_TARGETABLE",
                "The global residual is weak, but high-disagreement residual structure may still be targetable.",
                "Use high-disagreement arousal only; test gating/uncertainty or subject-adaptive residual head.",
            )

    if target == "valence":
        if (not np.isfinite(shared) or shared <= 0.10) and (not np.isfinite(subj_lift) or subj_lift < 0.05) and (not np.isfinite(k16) or k16 < 0.03):
            return (
                "NO_GO_VALENCE_CURRENT_RESIDUAL_IDENTIFIABILITY",
                "Valence residual has weak shared structure and weak calibration/oracle headroom under the current target.",
                "Do not run more valence physiology models until target/label formulation changes or a stronger representation source appears.",
            )

    if np.isfinite(shared) and shared >= 0.20:
        return (
            "SHARED_RESIDUAL_STRUCTURE_PRESENT",
            "There is repeatable residual structure across subject halves; a representation model may be justified.",
            "Proceed to a constrained representation test and compare against fixed-feature residual gates.",
        )

    return (
        "WEAK_OR_MIXED_RESIDUAL_IDENTIFIABILITY",
        "The measured residual structure is weak, mixed, or inconsistent. Extra model capacity is not yet justified as the next move.",
        "Prioritize normalization/adaptation audits and target reliability checks before new architecture search.",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=Path, default=Path(".cache/idare_eeg_cache_index_baseline_corrected.csv"))
    parser.add_argument("--targets", type=str, default="arousal,valence")
    parser.add_argument("--seed", type=int, default=20260530)
    parser.add_argument("--n-reliability-repeats", type=int, default=1000)
    parser.add_argument("--n-kshot-repeats", type=int, default=500)
    parser.add_argument("--n-perm", type=int, default=5000)
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    if not args.index.exists():
        raise FileNotFoundError(f"index file not found: {args.index}")

    df = pd.read_csv(args.index)
    subj_col = first_col(df, ["subject_id", "subject", "test_subject", "participant_id", "participant", "subj"])
    stim_col = first_col(df, ["stimulus_id", "stimulus", "video_id", "trial_id", "trial"])
    if subj_col is None or stim_col is None:
        raise SystemExit(f"Could not infer subject/stimulus columns from {list(df.columns)}")

    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    references = read_reference_tables()

    residual_rows = []
    reliability_rows = []
    kshot_rows = []
    decision_rows = []
    subject_stat_rows = []
    high_rows = []

    for target in targets:
        y_col = first_col(df, [f"{target}_score", target, f"label_{target}", f"{target}_rating"])
        if y_col is None:
            print(f"[WARN] skipping target={target}; no score column found")
            continue

        stim_pred, residual = loso_stimulus_prior_residual(df, y_col, subj_col, stim_col)
        zero = rmse(residual)

        subj_pred = leave_one_trial_subject_mean_pred(residual, df, subj_col)
        subj_err = residual - subj_pred
        subj_oracle_rmse = rmse(subj_err)
        subj_lift = zero - subj_oracle_rmse

        subj_stats = subject_stats_from_predictions(residual, subj_pred, df, subj_col)
        subj_ci_low, subj_ci_high = bootstrap_ci_mean(subj_stats["improvement_zero_minus_model"].to_numpy(), rng)
        subj_p = signflip_p_one_sided_gt_zero(subj_stats["improvement_zero_minus_model"].to_numpy(), args.n_perm, rng)

        var_info = variance_decomposition(residual, df, subj_col, stim_col)
        rel = split_half_reliability(
            residual=residual,
            df=df,
            subj_col=subj_col,
            stim_col=stim_col,
            rng=rng,
            n_repeats=args.n_reliability_repeats,
        )

        kshot = kshot_subject_mean_oracle(
            residual=residual,
            df=df,
            subj_col=subj_col,
            k_values=[1, 2, 4, 8, 16],
            rng=rng,
            n_repeats=args.n_kshot_repeats,
        )
        kshot.insert(0, "target", target)
        kshot_rows.extend(kshot.to_dict(orient="records"))
        kshot16_lift = float(kshot.loc[kshot["k_calibration_trials"] == 16, "pooled_lift_vs_zero_mean"].iloc[0]) if (kshot["k_calibration_trials"] == 16).any() else float("nan")

        # High-disagreement threshold: prefer 05ajb arousal threshold when available; otherwise use q75 abs residual.
        q75 = float(np.nanquantile(np.abs(residual), 0.75))
        ref_threshold = None
        for rec in references.get("05ajb_confirmed_high_disagreement", []):
            if str(rec.get("target")) == target and "abs_residual_threshold" in rec:
                try:
                    ref_threshold = float(rec["abs_residual_threshold"])
                except Exception:
                    ref_threshold = None
        high_thr = ref_threshold if ref_threshold is not None and np.isfinite(ref_threshold) else q75
        high_mask = np.abs(residual) >= high_thr
        high_zero = rmse(residual[high_mask])

        high_rel = split_half_reliability(
            residual=residual,
            df=df,
            subj_col=subj_col,
            stim_col=stim_col,
            rng=rng,
            n_repeats=max(200, args.n_reliability_repeats // 2),
            high_mask=high_mask,
        )

        row = {
            "target": target,
            "n_trials": int(len(df)),
            "n_subjects": int(df[subj_col].nunique()),
            "n_stimuli": int(df[stim_col].nunique()),
            "score_column": y_col,
            "zero_residual_rmse_after_loso_stimulus_prior": zero,
            "leave_one_trial_subject_mean_oracle_rmse": subj_oracle_rmse,
            "leave_one_trial_subject_mean_oracle_lift_vs_zero": subj_lift,
            "subject_oracle_ci95_low_mean_subject_improvement": subj_ci_low,
            "subject_oracle_ci95_high_mean_subject_improvement": subj_ci_high,
            "subject_oracle_signflip_p": subj_p,
            "k16_pooled_lift_vs_zero_mean": kshot16_lift,
        }
        row.update(var_info)
        row.update(rel)
        row.update({
            "high_disagreement_abs_residual_threshold": high_thr,
            "high_disagreement_n": int(np.sum(high_mask)),
            "high_disagreement_zero_rmse": high_zero,
            "high_disagreement_subject_style_split_half_mean_r": high_rel.get("subject_style_split_half_mean_r", float("nan")),
            "high_disagreement_shared_stimulus_residual_split_half_mean_r": high_rel.get("shared_stimulus_residual_split_half_mean_r", float("nan")),
            "high_disagreement_n_subjects_used": high_rel.get("n_subjects_used", 0),
            "high_disagreement_n_stimuli_used": high_rel.get("n_stimuli_used", 0),
        })
        residual_rows.append(row)

        reliability_rows.append({
            "target": target,
            "subset": "all_trials",
            **rel,
        })
        reliability_rows.append({
            "target": target,
            "subset": "high_disagreement_abs_residual_q75_or_05ajb",
            **high_rel,
        })

        high_rows.append({
            "target": target,
            "abs_residual_threshold": high_thr,
            "n_high": int(np.sum(high_mask)),
            "zero_rmse_high": high_zero,
            "subject_style_split_half_mean_r_high": high_rel.get("subject_style_split_half_mean_r", float("nan")),
            "shared_stimulus_residual_split_half_mean_r_high": high_rel.get("shared_stimulus_residual_split_half_mean_r", float("nan")),
            "interpretation": (
                "high-disagreement subset has enough rows for targeted analysis"
                if np.sum(high_mask) >= 100 else
                "high-disagreement subset is small; subject-level conclusions are fragile"
            ),
        })

        ss = subj_stats.copy()
        ss.insert(0, "target", target)
        subject_stat_rows.extend(ss.to_dict(orient="records"))

        decision, interpretation, action = decide_target(row)
        decision_rows.append({
            "target": target,
            "decision": decision,
            "zero_residual_rmse": zero,
            "subject_mean_oracle_lift": subj_lift,
            "k16_subject_mean_oracle_lift": kshot16_lift,
            "subject_style_reliability_mean_r": row["subject_style_split_half_mean_r"],
            "shared_stimulus_residual_reliability_mean_r": row["shared_stimulus_residual_split_half_mean_r"],
            "high_disagreement_shared_residual_reliability_mean_r": row["high_disagreement_shared_stimulus_residual_split_half_mean_r"],
            "interpretation": interpretation,
            "recommended_next_action": action,
        })

    residual_df = pd.DataFrame(residual_rows)
    reliability_df = pd.DataFrame(reliability_rows)
    kshot_df = pd.DataFrame(kshot_rows)
    decision_df = pd.DataFrame(decision_rows)
    subject_stats_df = pd.DataFrame(subject_stat_rows)
    high_df = pd.DataFrame(high_rows)

    next_steps_df = pd.DataFrame([
        {
            "priority": 1,
            "step": "06a4",
            "title": "Subject-normalization and domain-adaptation ablation",
            "purpose": "Test whether subject/domain normalization, CORAL-style alignment, and k-shot context can turn subject-style structure into LOSO improvement.",
            "success_condition": "Arousal high-disagreement LOSO improves beyond fixed EEG-bandpower and does not harm locked B2 gates.",
        },
        {
            "priority": 2,
            "step": "06a5",
            "title": "Augmentation rerun under current residual gates",
            "purpose": "Only rerun prior augmentation if it is evaluated under 05ajb/06a1y residual gates, not old binary/oracle metrics.",
            "success_condition": "Augmentation beats zero residual and fixed EEG-bandpower under subject-held-out residual gates.",
        },
        {
            "priority": 3,
            "step": "06a6",
            "title": "Neural pipeline anchor test against fixed EEG-bandpower",
            "purpose": "Before larger deep models, force the neural pipeline to reproduce the simple bandpower/summary signal.",
            "success_condition": "A neural or hybrid model matches/exceeds fixed EEG-bandpower on confirmed arousal high-disagreement residual prediction.",
        },
    ])

    outputs = {
        "decision_table": decision_df,
        "residual_identifiability": residual_df,
        "reliability_bootstrap": reliability_df,
        "kshot_subject_mean_oracle": kshot_df,
        "high_disagreement_bounds": high_df,
        "subject_mean_oracle_subject_stats": subject_stats_df,
        "next_steps": next_steps_df,
    }

    ROCA.mkdir(parents=True, exist_ok=True)
    for name, table in outputs.items():
        table.to_csv(ROCA / f"{OUT_PREFIX}_{name}.csv", index=False)

    payload = {
        "title": "I-DARE residual identifiability and label-noise bound",
        "inputs": {
            "index": str(args.index),
            "subject_column": subj_col,
            "stimulus_column": stim_col,
            "targets": targets,
            "seed": args.seed,
            "n_reliability_repeats": args.n_reliability_repeats,
            "n_kshot_repeats": args.n_kshot_repeats,
        },
        "references_loaded": references,
        "decision_table": decision_df.to_dict(orient="records"),
        "residual_identifiability": residual_df.to_dict(orient="records"),
        "reliability_bootstrap": reliability_df.to_dict(orient="records"),
        "kshot_subject_mean_oracle": kshot_df.to_dict(orient="records"),
        "high_disagreement_bounds": high_df.to_dict(orient="records"),
        "next_steps": next_steps_df.to_dict(orient="records"),
    }
    with open(ROCA / f"{OUT_PREFIX}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

    lines = []
    lines.append("# I-DARE residual identifiability and label-noise bound\n")
    lines.append("This report asks whether the residual target has repeatable structure strong enough to justify more physiology/deep modeling.\n")
    lines.append("Residual definition: rating minus LOSO stimulus prior. The zero-residual baseline predicts no subjective deviation beyond the stimulus prior.\n")
    lines.append("\n## Decision table\n")
    lines.append(md_table(decision_df))
    lines.append("\n## Residual identifiability\n")
    keep_cols = [
        "target",
        "zero_residual_rmse_after_loso_stimulus_prior",
        "leave_one_trial_subject_mean_oracle_lift_vs_zero",
        "k16_pooled_lift_vs_zero_mean",
        "subject_style_split_half_mean_r",
        "shared_stimulus_residual_split_half_mean_r",
        "high_disagreement_shared_stimulus_residual_split_half_mean_r",
    ]
    lines.append(md_table(residual_df[[c for c in keep_cols if c in residual_df.columns]]))
    lines.append("\n## Reliability bootstrap\n")
    lines.append(md_table(reliability_df))
    lines.append("\n## K-shot subject-mean oracle\n")
    lines.append(md_table(kshot_df))
    lines.append("\n## High-disagreement bounds\n")
    lines.append(md_table(high_df))
    lines.append("\n## Next steps\n")
    lines.append(md_table(next_steps_df))
    lines.append("\n## Git status note\n")
    lines.append("This script intentionally writes only 06a3 outputs. Existing unrelated untracked files are not touched.\n")

    md_path = ROCA / f"{OUT_PREFIX}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 06a3 completed.")
    for suffix in [
        ".md",
        ".json",
        "_decision_table.csv",
        "_residual_identifiability.csv",
        "_reliability_bootstrap.csv",
        "_kshot_subject_mean_oracle.csv",
        "_high_disagreement_bounds.csv",
        "_subject_mean_oracle_subject_stats.csv",
        "_next_steps.csv",
    ]:
        print(f"wrote: {ROCA / (OUT_PREFIX + suffix)}")

    print("\nDecision table:")
    print(decision_df.to_string(index=False))

    print("\nResidual identifiability:")
    display_cols = [c for c in keep_cols if c in residual_df.columns]
    print(residual_df[display_cols].to_string(index=False))

    print("\nK-shot subject-mean oracle:")
    print(kshot_df.to_string(index=False))

    print("\nNext steps:")
    print(next_steps_df.to_string(index=False))

    print("\n================== KEY OUTPUTS ==================")
    print(decision_df.to_csv(index=False).strip())
    print()
    print(residual_df[[c for c in keep_cols if c in residual_df.columns]].to_csv(index=False).strip())
    print()
    print(next_steps_df.to_csv(index=False).strip())

    print("\n================== SIZE CHECK ==================")
    for p in sorted(ROCA.glob(f"{OUT_PREFIX}*")):
        try:
            print(f"{p.stat().st_size/1024:.1f}K\t{p}")
        except Exception:
            pass

    print("\n================== GIT STATUS ==================")
    print(git_short())

    print("[INFO] If inspection is OK:")
    print(f"git add scripts/roca/06a3_idare_residual_identifiability_noise_bound.py docs/roca/{OUT_PREFIX}*")
    print('git commit -m "Add I-DARE residual identifiability noise bound"')
    print("git push")


if __name__ == "__main__":
    main()
