#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROCA = ROOT / "docs" / "roca"

DEFAULT_BRIDGE_PREFIX = "idare_high_disagreement_personalization_bridge_current"
DEFAULT_FAILURE_PREFIX = "idare_subject_calibration_model_family_confirmatory_stats_current"
DEFAULT_OUT_PREFIX = "idare_failure_subject_physiology_rescue_audit_current"

PRACTICAL_RMSE_LIFT = 0.02
MIN_WIN_MARGIN = 3


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--bridge-prefix", default=DEFAULT_BRIDGE_PREFIX)
    p.add_argument("--failure-prefix", default=DEFAULT_FAILURE_PREFIX)
    p.add_argument("--out-prefix", default=DEFAULT_OUT_PREFIX)
    p.add_argument("--n-bootstrap", type=int, default=20000)
    p.add_argument("--n-permutations", type=int, default=20000)
    p.add_argument("--seed", type=int, default=20260530)
    return p.parse_args()


def safe_float(x: Any) -> float | None:
    try:
        v = float(x)
    except Exception:
        return None
    return v if math.isfinite(v) else None


def clean_json(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): clean_json(v) for k, v in x.items()}
    if isinstance(x, list):
        return [clean_json(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        v = float(x)
        return None if not math.isfinite(v) else v
    if isinstance(x, float):
        return None if not math.isfinite(x) else x
    if pd.isna(x) if not isinstance(x, (list, dict, tuple, set)) else False:
        return None
    return x


def read_csv_required(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"Missing required file: {path}")
    return pd.read_csv(path)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out


def find_col(df: pd.DataFrame, candidates: Iterable[str], required: bool = True) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    if required:
        raise SystemExit(f"Could not find any of columns {list(candidates)}. Available columns: {list(df.columns)}")
    return None


def format_float(v: Any, digits: int = 6) -> str:
    fv = safe_float(v)
    if fv is None:
        return ""
    return f"{fv:.{digits}f}"


def md_table(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df is None or len(df) == 0:
        return "\n_No rows._\n"
    x = df.head(max_rows).copy()
    cols = list(x.columns)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in x.iterrows():
        vals = []
        for c in cols:
            val = row[c]
            if isinstance(val, float):
                vals.append(format_float(val))
            else:
                vals.append(str(val).replace("|", "/") if not pd.isna(val) else "")
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def bootstrap_mean_ci(values: np.ndarray, n_bootstrap: int, rng: np.random.Generator) -> tuple[float | None, float | None]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return None, None
    if values.size == 1:
        return float(values[0]), float(values[0])
    idx = rng.integers(0, values.size, size=(n_bootstrap, values.size))
    means = values[idx].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def signflip_p_mean_gt_zero(values: np.ndarray, n_permutations: int, rng: np.random.Generator) -> float | None:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return None
    obs = float(values.mean())
    if values.size == 1:
        return 0.5 if obs > 0 else 1.0
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_permutations, values.size))
    null_means = (signs * np.abs(values)[None, :]).mean(axis=1)
    return float((np.sum(null_means >= obs) + 1.0) / (n_permutations + 1.0))


def sign_test_p_wins_gt_losses(wins: int, losses: int) -> float | None:
    n = int(wins) + int(losses)
    if n <= 0:
        return None
    # P[X >= wins] under Binomial(n, 0.5)
    total = 0.0
    for k in range(int(wins), n + 1):
        total += math.comb(n, k) * (0.5 ** n)
    return float(total)


def pooled_rmse_from_subject_rows(df: pd.DataFrame, rmse_col: str, n_col: str | None) -> float | None:
    r = pd.to_numeric(df[rmse_col], errors="coerce")
    ok = np.isfinite(r.to_numpy(dtype=float))
    if not ok.any():
        return None
    if n_col is not None:
        n = pd.to_numeric(df[n_col], errors="coerce").fillna(0.0)
        weights = n.to_numpy(dtype=float)
        weights = np.where(np.isfinite(weights) & (weights > 0), weights, 1.0)
    else:
        weights = np.ones(len(df), dtype=float)
    r2 = (r.to_numpy(dtype=float) ** 2) * weights
    return float(np.sqrt(np.nansum(r2[ok]) / np.nansum(weights[ok])))


def infer_failure_subjects(failures: pd.DataFrame) -> pd.DataFrame:
    failures = normalize_columns(failures)
    target_col = find_col(failures, ["target"])
    subj_col = find_col(failures, ["subject_id", "test_subject", "subject", "participant_id", "participant", "subj"])

    x = failures.copy()
    x = x.rename(columns={target_col: "target", subj_col: "subject_id"})
    x["target"] = x["target"].astype(str)
    x["subject_id"] = pd.to_numeric(x["subject_id"], errors="coerce")
    x = x.dropna(subset=["subject_id"])
    x["subject_id"] = x["subject_id"].astype(int)

    # Prefer explicit failure rows where the locked personalized/kernel model regressed versus its locked reference.
    delta_col = find_col(x, ["delta_rmse_candidate_minus_locked", "delta_rmse_model_minus_locked"], required=False)
    improvement_col = find_col(x, ["improvement_locked_minus_candidate", "mean_subject_improvement_locked_minus_model"], required=False)
    if delta_col is not None:
        mask = pd.to_numeric(x[delta_col], errors="coerce") > 0
        if mask.any():
            x = x.loc[mask].copy()
    elif improvement_col is not None:
        mask = pd.to_numeric(x[improvement_col], errors="coerce") < 0
        if mask.any():
            x = x.loc[mask].copy()

    cols = ["target", "subject_id"]
    keep = x[cols].drop_duplicates().sort_values(cols).reset_index(drop=True)
    return keep


def summarize_group(
    group: pd.DataFrame,
    target: str,
    feature_block: str,
    model: str,
    gamma: float,
    quantile: float | None,
    locked_col: str,
    cand_col: str,
    n_col: str | None,
    args: argparse.Namespace,
    seed_offset: int,
) -> dict[str, Any]:
    locked = pd.to_numeric(group[locked_col], errors="coerce")
    cand = pd.to_numeric(group[cand_col], errors="coerce")
    improvement = locked - cand
    improvement_np = improvement.to_numpy(dtype=float)
    improvement_np = improvement_np[np.isfinite(improvement_np)]

    rng = np.random.default_rng(args.seed + seed_offset)
    ci_low, ci_high = bootstrap_mean_ci(improvement_np, args.n_bootstrap, rng)
    rng = np.random.default_rng(args.seed + 100000 + seed_offset)
    p_signflip = signflip_p_mean_gt_zero(improvement_np, args.n_permutations, rng)

    wins = int(np.sum(improvement_np > 1e-12))
    losses = int(np.sum(improvement_np < -1e-12))
    ties = int(improvement_np.size - wins - losses)
    win_margin = wins - losses
    sign_test_p = sign_test_p_wins_gt_losses(wins, losses)

    locked_rmse = pooled_rmse_from_subject_rows(group, locked_col, n_col)
    candidate_rmse = pooled_rmse_from_subject_rows(group, cand_col, n_col)
    lift = None if locked_rmse is None or candidate_rmse is None else locked_rmse - candidate_rmse

    passes = bool(
        lift is not None and lift >= PRACTICAL_RMSE_LIFT
        and ci_low is not None and ci_low > 0
        and p_signflip is not None and p_signflip < 0.05
        and win_margin >= MIN_WIN_MARGIN
    )

    return {
        "target": target,
        "feature_block": feature_block,
        "model": model,
        "quantile": quantile,
        "gamma_physio_blend": gamma,
        "failure_subjects": int(group["subject_id"].nunique()),
        "rows": int(len(group)),
        "locked_failure_rmse": locked_rmse,
        "candidate_failure_rmse": candidate_rmse,
        "lift_vs_locked_failure_rmse": lift,
        "mean_subject_improvement_locked_minus_candidate": float(np.nanmean(improvement_np)) if improvement_np.size else None,
        "median_subject_improvement_locked_minus_candidate": float(np.nanmedian(improvement_np)) if improvement_np.size else None,
        "ci95_low_mean_subject_improvement": ci_low,
        "ci95_high_mean_subject_improvement": ci_high,
        "signflip_p_one_sided_mean_gt_zero": p_signflip,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_margin": win_margin,
        "sign_test_p_one_sided_wins_gt_losses": sign_test_p,
        "passes_failure_rescue_gate": passes,
    }


def reason_for(row: pd.Series) -> str:
    if bool(row.get("passes_failure_rescue_gate", False)):
        return "physiology improves locked-personalization failure subjects with pooled, paired, CI, sign-flip, and win-margin support"
    reasons = []
    if safe_float(row.get("lift_vs_locked_failure_rmse")) is None or safe_float(row.get("lift_vs_locked_failure_rmse")) < PRACTICAL_RMSE_LIFT:
        reasons.append("failure-subject pooled RMSE lift < 0.02")
    if safe_float(row.get("ci95_low_mean_subject_improvement")) is None or safe_float(row.get("ci95_low_mean_subject_improvement")) <= 0:
        reasons.append("bootstrap CI lower bound is not > 0")
    if safe_float(row.get("signflip_p_one_sided_mean_gt_zero")) is None or safe_float(row.get("signflip_p_one_sided_mean_gt_zero")) >= 0.05:
        reasons.append("sign-flip p is not < 0.05")
    if safe_float(row.get("win_margin")) is None or int(row.get("win_margin", 0)) < MIN_WIN_MARGIN:
        reasons.append("win margin < 3")
    return "; ".join(reasons)


def main() -> None:
    args = parse_args()

    subject_stats_path = ROCA / f"{args.bridge_prefix}_subject_stats.csv"
    bridge_decision_path = ROCA / f"{args.bridge_prefix}_decision_table.csv"
    failure_subjects_path = ROCA / f"{args.failure_prefix}_failure_subjects.csv"

    subject_stats = normalize_columns(read_csv_required(subject_stats_path))
    bridge_decision = normalize_columns(read_csv_required(bridge_decision_path)) if bridge_decision_path.exists() else pd.DataFrame()
    failure_raw = normalize_columns(read_csv_required(failure_subjects_path))
    failure_subjects = infer_failure_subjects(failure_raw)

    target_col = find_col(subject_stats, ["target"])
    subj_col = find_col(subject_stats, ["subject_id", "test_subject", "subject", "participant_id", "participant", "subj"])
    block_col = find_col(subject_stats, ["feature_block", "block", "best_block", "physiology_block"])
    model_col = find_col(subject_stats, ["model", "best_model", "candidate_model"])
    gamma_col = find_col(subject_stats, ["gamma_physio_blend", "gamma", "blend", "physio_blend"], required=False)
    quantile_col = find_col(subject_stats, ["quantile", "q"], required=False)
    locked_col = find_col(subject_stats, ["locked_rmse", "locked_subject_rmse", "baseline_rmse", "locked_reference_rmse"])
    cand_col = find_col(subject_stats, ["candidate_rmse", "candidate_subject_rmse", "model_rmse", "physio_rmse"])
    n_col = find_col(subject_stats, ["n", "rows", "samples", "n_samples"], required=False)

    ss = subject_stats.rename(
        columns={
            target_col: "target",
            subj_col: "subject_id",
            block_col: "feature_block",
            model_col: "model",
            locked_col: "locked_rmse",
            cand_col: "candidate_rmse",
        }
    ).copy()
    if gamma_col and gamma_col != "gamma_physio_blend":
        ss = ss.rename(columns={gamma_col: "gamma_physio_blend"})
    elif "gamma_physio_blend" not in ss.columns:
        ss["gamma_physio_blend"] = np.nan
    if quantile_col and quantile_col != "quantile":
        ss = ss.rename(columns={quantile_col: "quantile"})
    elif "quantile" not in ss.columns:
        ss["quantile"] = np.nan
    if n_col and n_col != "n_samples_for_pooling":
        ss = ss.rename(columns={n_col: "n_samples_for_pooling"})
        n_col2 = "n_samples_for_pooling"
    else:
        n_col2 = None

    ss["target"] = ss["target"].astype(str)
    ss["subject_id"] = pd.to_numeric(ss["subject_id"], errors="coerce")
    ss = ss.dropna(subset=["subject_id"])
    ss["subject_id"] = ss["subject_id"].astype(int)
    ss["gamma_physio_blend"] = pd.to_numeric(ss["gamma_physio_blend"], errors="coerce")
    ss["quantile"] = pd.to_numeric(ss["quantile"], errors="coerce")

    merged = ss.merge(failure_subjects, on=["target", "subject_id"], how="inner")
    if merged.empty:
        raise SystemExit("No overlap between 05ak subject stats and 05af failure subjects. Check subject/target naming.")

    group_cols = ["target", "feature_block", "model", "quantile", "gamma_physio_blend"]
    metrics = []
    for i, (keys, group) in enumerate(merged.groupby(group_cols, dropna=False)):
        target, block, model, quantile, gamma = keys
        metrics.append(
            summarize_group(
                group=group,
                target=str(target),
                feature_block=str(block),
                model=str(model),
                gamma=float(gamma) if safe_float(gamma) is not None else None,
                quantile=float(quantile) if safe_float(quantile) is not None else None,
                locked_col="locked_rmse",
                cand_col="candidate_rmse",
                n_col=n_col2,
                args=args,
                seed_offset=i + 1,
            )
        )

    metrics_df = pd.DataFrame(metrics)
    metrics_df["gamma_is_positive"] = pd.to_numeric(metrics_df["gamma_physio_blend"], errors="coerce").fillna(0) > 0

    # Rank positive physiology blends first; gamma=0 is retained only as a sanity baseline.
    rank_df = metrics_df.copy()
    positive = rank_df[rank_df["gamma_is_positive"]].copy()
    candidate_space = positive if len(positive) else rank_df
    candidate_space = candidate_space.sort_values(
        ["target", "passes_failure_rescue_gate", "lift_vs_locked_failure_rmse", "mean_subject_improvement_locked_minus_candidate", "win_margin"],
        ascending=[True, False, False, False, False],
    )

    decisions = []
    for target, tg in candidate_space.groupby("target"):
        best = tg.iloc[0].copy()
        if bool(best["passes_failure_rescue_gate"]):
            decision = "GO_FAILURE_SUBJECT_PHYSIOLOGY_RESCUE"
        elif safe_float(best.get("lift_vs_locked_failure_rmse")) is not None and best.get("lift_vs_locked_failure_rmse") > 0:
            decision = "WEAK_FAILURE_SUBJECT_RESCUE_NEEDS_CONFIRMATION"
        else:
            decision = "NO_GO_FAILURE_SUBJECT_PHYSIOLOGY_RESCUE"
        d = best.to_dict()
        d["decision"] = decision
        d["reason"] = reason_for(best)
        decisions.append(d)

    decision_df = pd.DataFrame(decisions)
    decision_cols = [
        "target", "decision", "feature_block", "model", "quantile", "gamma_physio_blend",
        "failure_subjects", "locked_failure_rmse", "candidate_failure_rmse", "lift_vs_locked_failure_rmse",
        "mean_subject_improvement_locked_minus_candidate", "ci95_low_mean_subject_improvement",
        "signflip_p_one_sided_mean_gt_zero", "wins", "losses", "win_margin", "passes_failure_rescue_gate", "reason",
    ]
    decision_df = decision_df[[c for c in decision_cols if c in decision_df.columns]]

    next_steps = pd.DataFrame([
        {
            "priority": 1,
            "step": "05am",
            "title": "Physiology-assisted calibration sample reduction",
            "purpose": "Test whether physiology can reduce calibration samples even if it cannot beat the locked k=16 personalization model.",
            "success_condition": "A lower-k physiology-assisted model matches locked k=16 RMSE with stable paired subject evidence.",
        },
        {
            "priority": 2,
            "step": "05an",
            "title": "Representation-learning feasibility gate",
            "purpose": "Move beyond fixed engineered EEG/EMG features if failure-subject rescue remains no-go.",
            "success_condition": "Learned EEG/EMG representations beat fixed-feature physiology under the same locked gates.",
        },
        {
            "priority": 3,
            "step": "05ao",
            "title": "Targeted arousal high-disagreement model refinement",
            "purpose": "Use the confirmed arousal high-disagreement EEG-bandpower signal as a detection/triage signal rather than a direct additive correction.",
            "success_condition": "A gating or uncertainty-aware model improves high-disagreement arousal without degrading locked personalization.",
        },
    ])

    out = {
        "inputs": {
            "bridge_subject_stats": str(subject_stats_path),
            "bridge_decision_table": str(bridge_decision_path) if bridge_decision_path.exists() else None,
            "failure_subjects": str(failure_subjects_path),
        },
        "parameters": {
            "practical_rmse_lift": PRACTICAL_RMSE_LIFT,
            "min_win_margin": MIN_WIN_MARGIN,
            "n_bootstrap": args.n_bootstrap,
            "n_permutations": args.n_permutations,
            "seed": args.seed,
        },
        "decision_table": decision_df.to_dict(orient="records"),
        "failure_subject_count": failure_subjects.groupby("target")["subject_id"].nunique().to_dict(),
        "bridge_decision_table": bridge_decision.to_dict(orient="records") if len(bridge_decision) else [],
        "next_steps": next_steps.to_dict(orient="records"),
    }

    out_json = ROCA / f"{args.out_prefix}.json"
    out_md = ROCA / f"{args.out_prefix}.md"
    out_decision = ROCA / f"{args.out_prefix}_decision_table.csv"
    out_metrics = ROCA / f"{args.out_prefix}_failure_rescue_metrics.csv"
    out_subjects = ROCA / f"{args.out_prefix}_failure_subject_stats.csv"
    out_failure_set = ROCA / f"{args.out_prefix}_locked_failure_subject_set.csv"
    out_next = ROCA / f"{args.out_prefix}_next_steps.csv"

    out_json.write_text(json.dumps(clean_json(out), indent=2, ensure_ascii=False), encoding="utf-8")
    decision_df.to_csv(out_decision, index=False)
    metrics_df.sort_values(["target", "lift_vs_locked_failure_rmse", "mean_subject_improvement_locked_minus_candidate"], ascending=[True, False, False]).to_csv(out_metrics, index=False)
    merged.sort_values(["target", "subject_id", "feature_block", "model", "gamma_physio_blend"]).to_csv(out_subjects, index=False)
    failure_subjects.to_csv(out_failure_set, index=False)
    next_steps.to_csv(out_next, index=False)

    lines = []
    lines.append("# I-DARE Failure-Subject Physiology Rescue Audit")
    lines.append("")
    lines.append("This audit asks whether the physiology signal can rescue the subjects where the locked personalized kernel-residual model still regresses relative to its locked few-shot reference.")
    lines.append("")
    lines.append("## Decision table")
    lines.append("")
    lines.append(md_table(decision_df))
    lines.append("")
    lines.append("## Top failure-rescue metrics")
    lines.append("")
    lines.append(md_table(metrics_df.sort_values(["target", "lift_vs_locked_failure_rmse"], ascending=[True, False]), max_rows=40))
    lines.append("")
    lines.append("## Locked failure-subject set")
    lines.append("")
    lines.append(md_table(failure_subjects.groupby("target").agg(failure_subjects=("subject_id", "nunique")).reset_index()))
    lines.append("")
    lines.append("## Next steps")
    lines.append("")
    lines.append(md_table(next_steps))
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 05al completed.")
    for p in [out_md, out_json, out_decision, out_metrics, out_subjects, out_failure_set, out_next]:
        print(f"wrote: {p}")
    print("\nDecision table:")
    print(decision_df.to_string(index=False))
    print("\nTop failure rescue metrics:")
    cols = [
        "target", "feature_block", "model", "gamma_physio_blend", "failure_subjects", "locked_failure_rmse",
        "candidate_failure_rmse", "lift_vs_locked_failure_rmse", "ci95_low_mean_subject_improvement",
        "signflip_p_one_sided_mean_gt_zero", "wins", "losses", "win_margin", "passes_failure_rescue_gate",
    ]
    print(metrics_df[[c for c in cols if c in metrics_df.columns]].sort_values(["target", "lift_vs_locked_failure_rmse"], ascending=[True, False]).head(30).to_string(index=False))


if __name__ == "__main__":
    main()
