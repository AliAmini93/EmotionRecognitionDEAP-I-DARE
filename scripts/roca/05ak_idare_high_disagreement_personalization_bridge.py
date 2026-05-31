#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROCA = ROOT / "docs" / "roca"

PRED_CSV = ROCA / "idare_residual_physiology_feature_audit_current_predictions.csv"
AJB_VERDICT_CSV = ROCA / "idare_high_disagreement_direct_deviation_confirmatory_stats_current_verdict.csv"
B2_LOCK_CSV = ROCA / "idare_scientific_direction_lock_current_locked_baselines.csv"

OUT_PREFIX = "idare_high_disagreement_personalization_bridge_current"
OUT_MD = ROCA / f"{OUT_PREFIX}.md"
OUT_JSON = ROCA / f"{OUT_PREFIX}.json"
OUT_DECISION = ROCA / f"{OUT_PREFIX}_decision_table.csv"
OUT_BRIDGE = ROCA / f"{OUT_PREFIX}_bridge_metrics.csv"
OUT_SUBJECT = ROCA / f"{OUT_PREFIX}_subject_stats.csv"
OUT_FAILURE = ROCA / f"{OUT_PREFIX}_failure_subjects.csv"
OUT_VALIDATION = ROCA / f"{OUT_PREFIX}_locked_baseline_validation.csv"
OUT_NEXT = ROCA / f"{OUT_PREFIX}_next_steps.csv"

K_LOCKED = 16
KERNEL_SHRINK = 4.0
N_REPEATS = 100
SEED = 20260530
PRACTICAL_RMSE_LIFT = 0.02
MIN_WIN_MARGIN = 3
GAMMAS = [0.0, 0.05, 0.10, 0.20, 0.35, 0.50, 0.75, 1.0]


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
    if pd.isna(x) if not isinstance(x, (list, dict, tuple, np.ndarray)) else False:
        return None
    return x


def md_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df is None or len(df) == 0:
        return "\n"
    x = df.copy()
    if max_rows is not None:
        x = x.head(max_rows)
    x = x.replace([np.inf, -np.inf], np.nan)
    x = x.where(pd.notna(x), "")
    cols = list(x.columns)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in x.iterrows():
        vals = []
        for c in cols:
            v = row[c]
            if isinstance(v, float):
                vals.append(f"{v:.6f}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    m = np.isfinite(y_true) & np.isfinite(y_pred)
    if m.sum() == 0:
        return float("nan")
    return float(np.sqrt(np.mean((y_true[m] - y_pred[m]) ** 2)))


def pearson(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    m = np.isfinite(y_true) & np.isfinite(y_pred)
    if m.sum() < 3:
        return float("nan")
    a = y_true[m]
    b = y_pred[m]
    if np.std(a) == 0 or np.std(b) == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def bootstrap_ci(vals: np.ndarray, n_boot: int = 20000, seed: int = SEED):
    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, vals.size, size=(n_boot, vals.size))
    means = vals[idx].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def signflip_p(vals: np.ndarray, n_perm: int = 20000, seed: int = SEED):
    vals = np.asarray(vals, dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return float("nan")
    observed = float(np.mean(vals))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_perm, vals.size))
    null_means = (signs * vals[None, :]).mean(axis=1)
    # one-sided: mean improvement > 0
    return float((np.sum(null_means >= observed) + 1) / (n_perm + 1))


def find_subject_col(df: pd.DataFrame) -> str:
    for c in ["subject_id", "subject", "participant_id", "participant", "subj", "test_subject"]:
        if c in df.columns:
            return c
    raise SystemExit(f"Could not find subject column. Available columns: {list(df.columns)}")


def normalize_stimulus_id(x: Any) -> str:
    s = str(x)
    # keep Dummy_1 and 1 separate only if truly different; otherwise normalize common labels.
    if s.lower().startswith("dummy_"):
        tail = s.split("_", 1)[1]
        if tail.isdigit():
            return str(int(tail))
    try:
        f = float(s)
        if math.isfinite(f) and f.is_integer():
            return str(int(f))
    except Exception:
        pass
    return s


def load_predictions() -> pd.DataFrame:
    if not PRED_CSV.exists():
        raise SystemExit(f"Missing input predictions: {PRED_CSV}")
    df = pd.read_csv(PRED_CSV)
    subj_col = find_subject_col(df)
    required = ["stimulus_id", "target", "model", "y_true_score", "train_stimulus_mean", "y_pred_deviation"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing required columns in {PRED_CSV}: {missing}. Available columns: {list(df.columns)}")
    if "feature_block" not in df.columns:
        df["feature_block"] = "unknown"
    out = df.copy()
    out["subject_id"] = out[subj_col].astype(str)
    out["stimulus_key"] = out["stimulus_id"].map(normalize_stimulus_id)
    for c in ["y_true_score", "train_stimulus_mean", "y_pred_deviation"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    out["true_residual"] = out["y_true_score"] - out["train_stimulus_mean"]
    out["physio_pred_score"] = out["train_stimulus_mean"] + out["y_pred_deviation"]
    return out


def load_ajb_candidates() -> pd.DataFrame:
    if not AJB_VERDICT_CSV.exists():
        raise SystemExit(f"Missing 05ajb verdict: {AJB_VERDICT_CSV}")
    v = pd.read_csv(AJB_VERDICT_CSV)
    needed = ["target", "quantile", "feature_block", "model", "passes_confirmatory_gate"]
    missing = [c for c in needed if c not in v.columns]
    if missing:
        raise SystemExit(f"Missing required columns in {AJB_VERDICT_CSV}: {missing}")
    # Keep confirmed candidates, but retain no-go valence in a separate negative-control row.
    v["passes_confirmatory_gate"] = v["passes_confirmatory_gate"].astype(str).str.lower().isin(["true", "1", "yes"])
    return v


def load_locked_rmse() -> dict[tuple[str, str], float]:
    d: dict[tuple[str, str], float] = {}
    if B2_LOCK_CSV.exists():
        b = pd.read_csv(B2_LOCK_CSV)
        for _, r in b.iterrows():
            target = str(r.get("target"))
            level = str(r.get("baseline_level"))
            name = str(r.get("baseline_name"))
            val = safe_float(r.get("rmse"))
            if val is not None:
                d[(target, level)] = val
                d[(target, name)] = val
    return d


def prepare_trial_table(all_pred: pd.DataFrame, target: str) -> pd.DataFrame:
    x = all_pred[all_pred["target"].astype(str) == str(target)].copy()
    base_cols = ["subject_id", "stimulus_key", "target", "y_true_score", "train_stimulus_mean", "true_residual"]
    trial = x[base_cols].drop_duplicates(subset=["subject_id", "stimulus_key", "target"]).copy()
    trial = trial.dropna(subset=["y_true_score", "train_stimulus_mean", "true_residual"])
    return trial


def build_similarity_maps(trial: pd.DataFrame) -> dict[str, dict[str, dict[str, float]]]:
    """Return target-subject-specific stimulus similarity maps using other subjects only."""
    subjects = sorted(trial["subject_id"].unique())
    stimuli = sorted(trial["stimulus_key"].unique(), key=lambda z: (len(str(z)), str(z)))
    maps: dict[str, dict[str, dict[str, float]]] = {}
    for held in subjects:
        train = trial[trial["subject_id"] != held]
        mat = train.pivot_table(index="subject_id", columns="stimulus_key", values="true_residual", aggfunc="mean")
        # Ensure full columns for consistent pair vectors.
        mat = mat.reindex(columns=stimuli)
        sim_by_test: dict[str, dict[str, float]] = {}
        for a in stimuli:
            sims = {}
            va = mat[a].to_numpy(dtype=float)
            for b in stimuli:
                vb = mat[b].to_numpy(dtype=float)
                mask = np.isfinite(va) & np.isfinite(vb)
                if mask.sum() < 4 or np.std(va[mask]) == 0 or np.std(vb[mask]) == 0:
                    sim = 0.0
                else:
                    sim = float(np.corrcoef(va[mask], vb[mask])[0, 1])
                # Positive-only kernel; negative correlation should not borrow residual sign blindly.
                sims[b] = max(0.0, sim)
            sim_by_test[a] = sims
        maps[held] = sim_by_test
    return maps


def predict_locked_for_subject(
    subj_df: pd.DataFrame,
    sim_map: dict[str, dict[str, float]],
    k: int,
    repeat: int,
    target: str,
    subject_id: str,
) -> pd.DataFrame:
    subj_df = subj_df.sort_values("stimulus_key").reset_index(drop=True)
    stimuli = subj_df["stimulus_key"].to_numpy()
    if len(stimuli) <= k:
        return pd.DataFrame()
    rng = np.random.default_rng(stable_seed(SEED, "05ak", target, subject_id, k, repeat))
    calib_idx = np.sort(rng.choice(np.arange(len(stimuli)), size=k, replace=False))
    test_mask = np.ones(len(stimuli), dtype=bool)
    test_mask[calib_idx] = False
    calib = subj_df.iloc[calib_idx].copy()
    test = subj_df.loc[test_mask].copy()
    calib_stim = calib["stimulus_key"].to_numpy()
    calib_resid = calib["true_residual"].to_numpy(dtype=float)
    bias_resid = float(np.mean(calib_resid)) * (k / (k + KERNEL_SHRINK))
    pred_resids = []
    for stim in test["stimulus_key"].to_numpy():
        sims = np.array([sim_map.get(stim, {}).get(cs, 0.0) for cs in calib_stim], dtype=float)
        if not np.isfinite(sims).all() or sims.sum() <= 1e-12:
            weights = np.ones_like(sims) / max(1, len(sims))
        else:
            # mild temperature keeps weights stable with small k
            weights = sims / sims.sum()
        kr = float(np.sum(weights * calib_resid)) * (k / (k + KERNEL_SHRINK))
        # Conservative blend with simple bias stabilizes noisy kernel estimates.
        pred_resids.append(0.75 * kr + 0.25 * bias_resid)
    out = test.copy()
    out["repeat"] = repeat
    out["locked_pred_residual"] = np.asarray(pred_resids, dtype=float)
    out["locked_pred_score"] = out["train_stimulus_mean"] + out["locked_pred_residual"]
    return out


def make_locked_predictions(trial: pd.DataFrame, target: str) -> pd.DataFrame:
    sim_maps = build_similarity_maps(trial)
    rows = []
    for subject_id, subj_df in trial.groupby("subject_id"):
        for rep in range(N_REPEATS):
            pred = predict_locked_for_subject(
                subj_df=subj_df,
                sim_map=sim_maps[str(subject_id)],
                k=K_LOCKED,
                repeat=rep,
                target=target,
                subject_id=str(subject_id),
            )
            if len(pred):
                rows.append(pred)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def evaluate_bridge(merged: pd.DataFrame, target: str, feature_block: str, model: str, quantile: float):
    metric_rows = []
    subject_rows = []
    failure_rows = []

    for gamma in GAMMAS:
        x = merged.copy()
        x["candidate_pred_residual"] = (1.0 - gamma) * x["locked_pred_residual"] + gamma * x["y_pred_deviation"]
        x["candidate_pred_score"] = x["train_stimulus_mean"] + x["candidate_pred_residual"]

        locked_rmse = rmse(x["y_true_score"].to_numpy(), x["locked_pred_score"].to_numpy())
        cand_rmse = rmse(x["y_true_score"].to_numpy(), x["candidate_pred_score"].to_numpy())
        locked_resid_rmse = rmse(x["true_residual"].to_numpy(), x["locked_pred_residual"].to_numpy())
        cand_resid_rmse = rmse(x["true_residual"].to_numpy(), x["candidate_pred_residual"].to_numpy())
        lift = locked_rmse - cand_rmse
        resid_lift = locked_resid_rmse - cand_resid_rmse
        corr = pearson(x["true_residual"].to_numpy(), x["candidate_pred_residual"].to_numpy())

        subj_stats = []
        for sid, g in x.groupby("subject_id"):
            lrmse = rmse(g["y_true_score"].to_numpy(), g["locked_pred_score"].to_numpy())
            crmse = rmse(g["y_true_score"].to_numpy(), g["candidate_pred_score"].to_numpy())
            subj_stats.append({
                "target": target,
                "quantile": quantile,
                "feature_block": feature_block,
                "model": model,
                "gamma": gamma,
                "subject_id": sid,
                "n": len(g),
                "locked_rmse": lrmse,
                "candidate_rmse": crmse,
                "improvement_locked_minus_candidate": lrmse - crmse,
                "delta_candidate_minus_locked": crmse - lrmse,
            })
        sdf = pd.DataFrame(subj_stats)
        vals = sdf["improvement_locked_minus_candidate"].to_numpy(dtype=float)
        ci_low, ci_high = bootstrap_ci(vals, seed=stable_seed(SEED, target, feature_block, model, quantile, gamma, "boot"))
        sp = signflip_p(vals, seed=stable_seed(SEED, target, feature_block, model, quantile, gamma, "sign"))
        wins = int(np.sum(vals > 0))
        losses = int(np.sum(vals < 0))
        ties = int(np.sum(vals == 0))
        win_margin = wins - losses
        passes = bool(
            lift >= PRACTICAL_RMSE_LIFT
            and resid_lift >= PRACTICAL_RMSE_LIFT
            and ci_low > 0
            and sp < 0.05
            and win_margin > MIN_WIN_MARGIN
        )

        metric_rows.append({
            "target": target,
            "quantile": quantile,
            "feature_block": feature_block,
            "model": model,
            "gamma_physio_blend": gamma,
            "n": len(x),
            "subjects": x["subject_id"].nunique(),
            "locked_rmse": locked_rmse,
            "candidate_rmse": cand_rmse,
            "lift_vs_locked_rmse": lift,
            "locked_residual_rmse": locked_resid_rmse,
            "candidate_residual_rmse": cand_resid_rmse,
            "lift_vs_locked_residual_rmse": resid_lift,
            "residual_pearson": corr,
            "mean_subject_improvement_locked_minus_candidate": float(np.mean(vals)),
            "median_subject_improvement_locked_minus_candidate": float(np.median(vals)),
            "ci95_low_mean_subject_improvement": ci_low,
            "ci95_high_mean_subject_improvement": ci_high,
            "signflip_p_one_sided_mean_gt_zero": sp,
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "win_margin": win_margin,
            "passes_bridge_gate": passes,
        })
        subject_rows.extend(subj_stats)
        ff = sdf.sort_values("delta_candidate_minus_locked", ascending=False).head(20).copy()
        failure_rows.extend(ff.to_dict(orient="records"))

    return pd.DataFrame(metric_rows), pd.DataFrame(subject_rows), pd.DataFrame(failure_rows)


def main() -> None:
    pred = load_predictions()
    ajb = load_ajb_candidates()
    locked_rmse_map = load_locked_rmse()

    candidate_rows = []
    # Keep all verdict rows so valence remains documented as negative control.
    for _, r in ajb.iterrows():
        candidate_rows.append({
            "target": str(r["target"]),
            "quantile": float(r["quantile"]),
            "feature_block": str(r["feature_block"]),
            "model": str(r["model"]),
            "source_05ajb_passed": bool(r["passes_confirmatory_gate"]),
        })

    all_metrics = []
    all_subject = []
    all_failure = []
    validation_rows = []

    for c in candidate_rows:
        target = c["target"]
        q = c["quantile"]
        block = c["feature_block"]
        model = c["model"]
        print(f"[TARGET] {target} q={q} block={block} model={model}")

        trial = prepare_trial_table(pred, target)
        if trial.empty:
            print(f"[WARN] no trial rows for {target}")
            continue

        locked = make_locked_predictions(trial, target)
        if locked.empty:
            print(f"[WARN] no locked predictions for {target}")
            continue

        # Validate reimplementation against locked full B2 RMSE only as a sanity check.
        locked_full_rmse = rmse(locked["y_true_score"].to_numpy(), locked["locked_pred_score"].to_numpy())
        b2_reported = locked_rmse_map.get((target, "B2_LOCKED")) or locked_rmse_map.get((target, "kernel_residual_shrink4"))
        validation_rows.append({
            "target": target,
            "reimplemented_locked_model": "kernel_residual_shrink4_bridge_reimplementation",
            "k_calibration": K_LOCKED,
            "n_repeats": N_REPEATS,
            "reimplemented_locked_full_rmse": locked_full_rmse,
            "reported_B2_locked_rmse": b2_reported,
            "abs_difference_vs_reported_B2": abs(locked_full_rmse - b2_reported) if b2_reported is not None else None,
            "note": "This bridge script reimplements locked-style kernel residual predictions to obtain per-trial predictions for conditional physiology tests.",
        })

        phys = pred[(pred["target"].astype(str) == target) & (pred["feature_block"].astype(str) == block) & (pred["model"].astype(str) == model)].copy()
        keep_cols = ["subject_id", "stimulus_key", "target", "y_pred_deviation", "physio_pred_score"]
        phys = phys[keep_cols].drop_duplicates(subset=["subject_id", "stimulus_key", "target"])

        merged = locked.merge(phys, on=["subject_id", "stimulus_key", "target"], how="inner")
        threshold = float(np.quantile(np.abs(trial["true_residual"].to_numpy(dtype=float)), q))
        merged = merged[np.abs(merged["true_residual"].to_numpy(dtype=float)) >= threshold].copy()
        if merged.empty:
            print(f"[WARN] no high-disagreement rows for {target} q={q}")
            continue
        merged["abs_residual_threshold"] = threshold
        merged["source_05ajb_passed"] = c["source_05ajb_passed"]

        mdf, sdf, fdf = evaluate_bridge(merged, target, block, model, q)
        mdf["abs_residual_threshold"] = threshold
        mdf["source_05ajb_passed"] = c["source_05ajb_passed"]
        all_metrics.append(mdf)
        all_subject.append(sdf)
        all_failure.append(fdf)

    bridge = pd.concat(all_metrics, ignore_index=True) if all_metrics else pd.DataFrame()
    subj = pd.concat(all_subject, ignore_index=True) if all_subject else pd.DataFrame()
    fail = pd.concat(all_failure, ignore_index=True) if all_failure else pd.DataFrame()
    validation = pd.DataFrame(validation_rows)

    decision_rows = []
    if len(bridge):
        for target, g in bridge.groupby("target"):
            best = g.sort_values(["passes_bridge_gate", "lift_vs_locked_rmse", "ci95_low_mean_subject_improvement", "win_margin"], ascending=[False, False, False, False]).iloc[0]
            reasons = []
            if best["lift_vs_locked_rmse"] < PRACTICAL_RMSE_LIFT:
                reasons.append(f"pooled RMSE lift vs locked < {PRACTICAL_RMSE_LIFT}")
            if best["lift_vs_locked_residual_rmse"] < PRACTICAL_RMSE_LIFT:
                reasons.append(f"residual RMSE lift vs locked < {PRACTICAL_RMSE_LIFT}")
            if best["ci95_low_mean_subject_improvement"] <= 0:
                reasons.append("bootstrap CI lower bound is not > 0")
            if best["signflip_p_one_sided_mean_gt_zero"] >= 0.05:
                reasons.append("sign-flip p is not < 0.05")
            if best["win_margin"] <= MIN_WIN_MARGIN:
                reasons.append(f"win margin <= {MIN_WIN_MARGIN}")
            decision = "GO_PHYSIOLOGY_BRIDGES_TO_LOCKED_PERSONALIZATION" if bool(best["passes_bridge_gate"]) else "NO_GO_PHYSIOLOGY_BRIDGE_TO_LOCKED_PERSONALIZATION"
            decision_rows.append({
                "target": target,
                "decision": decision,
                "quantile": best["quantile"],
                "feature_block": best["feature_block"],
                "model": best["model"],
                "gamma_physio_blend": best["gamma_physio_blend"],
                "locked_rmse": best["locked_rmse"],
                "candidate_rmse": best["candidate_rmse"],
                "lift_vs_locked_rmse": best["lift_vs_locked_rmse"],
                "lift_vs_locked_residual_rmse": best["lift_vs_locked_residual_rmse"],
                "residual_pearson": best["residual_pearson"],
                "ci95_low_mean_subject_improvement": best["ci95_low_mean_subject_improvement"],
                "signflip_p_one_sided_mean_gt_zero": best["signflip_p_one_sided_mean_gt_zero"],
                "wins": int(best["wins"]),
                "losses": int(best["losses"]),
                "win_margin": int(best["win_margin"]),
                "passes_bridge_gate": bool(best["passes_bridge_gate"]),
                "reason": "candidate improves locked personalization in the high-disagreement region" if bool(best["passes_bridge_gate"]) else "; ".join(reasons),
            })
    decision = pd.DataFrame(decision_rows)

    next_steps = pd.DataFrame([
        {
            "priority": 1,
            "step": "05al",
            "title": "Failure-subject physiology rescue audit",
            "purpose": "Test confirmed arousal EEG-bandpower residual signal specifically on subjects where personalization still fails.",
            "success_condition": "Physiology improves failure-subject RMSE without worsening pooled or paired metrics.",
        },
        {
            "priority": 2,
            "step": "05am",
            "title": "Physiology-assisted calibration sample reduction",
            "purpose": "Test whether physiology can reduce calibration samples, e.g. k=4/k=8 approaching locked k=16.",
            "success_condition": "Lower-k physiology-assisted model matches locked k=16 with stable subject-level evidence.",
        },
        {
            "priority": 3,
            "step": "05an",
            "title": "Representation-learning feasibility gate",
            "purpose": "If fixed-feature physiology cannot bridge to personalization, define raw/learned EEG representation experiments.",
            "success_condition": "Learned representation beats fixed-feature high-disagreement physiology under the same gates.",
        },
    ])

    OUT_DECISION.parent.mkdir(parents=True, exist_ok=True)
    decision.to_csv(OUT_DECISION, index=False)
    bridge.to_csv(OUT_BRIDGE, index=False)
    subj.to_csv(OUT_SUBJECT, index=False)
    fail.to_csv(OUT_FAILURE, index=False)
    validation.to_csv(OUT_VALIDATION, index=False)
    next_steps.to_csv(OUT_NEXT, index=False)

    payload = {
        "out_prefix": OUT_PREFIX,
        "inputs": {
            "predictions": str(PRED_CSV),
            "ajb_verdict": str(AJB_VERDICT_CSV),
            "locked_baselines": str(B2_LOCK_CSV),
        },
        "parameters": {
            "k_locked": K_LOCKED,
            "kernel_shrink": KERNEL_SHRINK,
            "n_repeats": N_REPEATS,
            "gammas": GAMMAS,
            "practical_rmse_lift": PRACTICAL_RMSE_LIFT,
            "min_win_margin": MIN_WIN_MARGIN,
            "seed": SEED,
        },
        "decision": clean_json(decision.to_dict(orient="records")),
        "locked_validation": clean_json(validation.to_dict(orient="records")),
        "next_steps": clean_json(next_steps.to_dict(orient="records")),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("# I-DARE High-Disagreement Physiology-to-Personalization Bridge\n")
    lines.append("This audit asks whether the confirmed high-disagreement physiology residual signal can improve a locked-style personalized residual baseline, rather than only improving stimulus-only residual prediction.\n")
    lines.append("## Decision\n")
    lines.append(md_table(decision))
    lines.append("\n## Bridge metrics, top rows\n")
    if len(bridge):
        top = bridge.sort_values(["target", "lift_vs_locked_rmse"], ascending=[True, False]).head(30)
        lines.append(md_table(top))
    lines.append("\n## Locked baseline validation\n")
    lines.append(md_table(validation))
    lines.append("\n## Interpretation\n")
    lines.append("- A pass here would mean physiology is not merely detectable in high-disagreement residuals, but can be used as a conditional correction on top of personalization.\n")
    lines.append("- A no-go here does not erase the 05ajb arousal signal; it means the current fixed-feature physiology signal is not yet strong enough to improve the locked personalized predictor.\n")
    lines.append("- The locked model is reimplemented here to obtain per-trial predictions for conditional testing; compare the validation table against the reported B2 RMSE before treating this as a final locked-baseline replacement.\n")
    lines.append("\n## Next steps\n")
    lines.append(md_table(next_steps))
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 05ak completed.")
    for p in [OUT_MD, OUT_JSON, OUT_DECISION, OUT_BRIDGE, OUT_SUBJECT, OUT_FAILURE, OUT_VALIDATION, OUT_NEXT]:
        print(f"wrote: {p}")
    print("\nDecision table:")
    print(decision.to_string(index=False) if len(decision) else "<empty>")
    print("\nLocked validation:")
    print(validation.to_string(index=False) if len(validation) else "<empty>")
    print("\nTop bridge metrics:")
    if len(bridge):
        cols = ["target", "quantile", "feature_block", "model", "gamma_physio_blend", "locked_rmse", "candidate_rmse", "lift_vs_locked_rmse", "ci95_low_mean_subject_improvement", "signflip_p_one_sided_mean_gt_zero", "wins", "losses", "win_margin", "passes_bridge_gate"]
        print(bridge.sort_values(["target", "lift_vs_locked_rmse"], ascending=[True, False])[cols].head(30).to_string(index=False))
    else:
        print("<empty>")


if __name__ == "__main__":
    main()
