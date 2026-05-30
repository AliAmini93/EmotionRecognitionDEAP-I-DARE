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
DEFAULT_OUT_PREFIX = "idare_physiology_assisted_calibration_sample_reduction_current"
MATCH_TOLERANCE_RMSE = 0.02
MIN_WIN_MARGIN_FOR_MATCH = -3


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--out-prefix", type=str, default=DEFAULT_OUT_PREFIX)
    p.add_argument("--n-bootstrap", type=int, default=20000)
    p.add_argument("--seed", type=int, default=20260530)
    p.add_argument("--match-tolerance-rmse", type=float, default=MATCH_TOLERANCE_RMSE)
    p.add_argument("--min-win-margin-for-match", type=int, default=MIN_WIN_MARGIN_FOR_MATCH)
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
        return None if not math.isfinite(v) else v
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, float):
        return None if not math.isfinite(x) else x
    return x


def md_table(df: pd.DataFrame, floatfmt: int = 6) -> str:
    if df is None or df.empty:
        return "_empty_\n"
    x = df.copy()
    for c in x.columns:
        if pd.api.types.is_float_dtype(x[c]):
            x[c] = x[c].map(lambda v: "" if pd.isna(v) else f"{float(v):.{floatfmt}f}")
        else:
            x[c] = x[c].map(lambda v: "" if pd.isna(v) else str(v))
    cols = list(x.columns)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, r in x.iterrows():
        vals = [str(r[c]).replace("\n", " ") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def read_csv_required(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)


def first_existing(paths: list[Path]) -> Path:
    for p in paths:
        if p.exists():
            return p
    raise FileNotFoundError("None of these files exists:\n" + "\n".join(str(p) for p in paths))


def find_col(df: pd.DataFrame, candidates: list[str], *, required: bool = True, label: str = "") -> str | None:
    cols = list(df.columns)
    lower = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand in cols:
            return cand
        if cand.lower() in lower:
            return lower[cand.lower()]
    if required:
        raise SystemExit(
            f"Could not find column {label or candidates}. Candidates={candidates}. Available columns={cols}"
        )
    return None


def normalize_subject_col(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    c = find_col(df, ["subject_id", "subject", "participant_id", "participant", "subj", "test_subject"], required=True, label="subject id")
    out = df.copy()
    out["__subject_id__"] = out[c].astype(str)
    return out, "__subject_id__"


def normalize_target_col(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    c = find_col(df, ["target", "label_target", "emotion_target"], required=True, label="target")
    out = df.copy()
    out["__target__"] = out[c].astype(str)
    return out, "__target__"


def normalize_model_col(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    c = find_col(df, ["model", "candidate_model", "best_model"], required=True, label="model")
    out = df.copy()
    out["__model__"] = out[c].astype(str)
    return out, "__model__"


def normalize_block_col(df: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
    c = find_col(df, ["block", "feature_block", "best_block"], required=False, label="feature block")
    out = df.copy()
    out["__block__"] = "" if c is None else out[c].astype(str)
    return out, "__block__"


def normalize_k_col(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    c = find_col(df, ["k_calibration", "k", "best_k_calibration"], required=True, label="k calibration")
    out = df.copy()
    out["__k__"] = pd.to_numeric(out[c], errors="coerce")
    return out, "__k__"


def pick_rmse_col(df: pd.DataFrame, *, purpose: str) -> str:
    return find_col(df, ["rmse", "candidate_rmse", "subject_rmse", "model_rmse", "best_rmse", "residual_rmse"], required=True, label=f"RMSE for {purpose}") or ""


def bootstrap_mean_ci(values: np.ndarray, n_bootstrap: int, seed: int) -> tuple[float | None, float | None]:
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return None, None
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(values), size=(n_bootstrap, len(values)))
    means = values[idx].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def subject_delta_stats(delta_candidate_minus_locked: np.ndarray, args, seed_parts: tuple[Any, ...]) -> dict[str, Any]:
    d = np.asarray(delta_candidate_minus_locked, dtype=float)
    d = d[np.isfinite(d)]
    if len(d) == 0:
        return {
            "subjects_with_pair": 0,
            "mean_delta_rmse_candidate_minus_locked_B2": None,
            "median_delta_rmse_candidate_minus_locked_B2": None,
            "ci95_low_mean_delta_candidate_minus_locked_B2": None,
            "ci95_high_mean_delta_candidate_minus_locked_B2": None,
            "wins_vs_locked_B2": 0,
            "losses_vs_locked_B2": 0,
            "ties_vs_locked_B2": 0,
            "win_margin_vs_locked_B2": 0,
        }
    ci_lo, ci_hi = bootstrap_mean_ci(
        d,
        args.n_bootstrap,
        stable_seed(args.seed, "sample_reduction_subject_delta", *seed_parts),
    )
    wins = int(np.sum(d < 0))
    losses = int(np.sum(d > 0))
    ties = int(np.sum(d == 0))
    return {
        "subjects_with_pair": int(len(d)),
        "mean_delta_rmse_candidate_minus_locked_B2": float(np.mean(d)),
        "median_delta_rmse_candidate_minus_locked_B2": float(np.median(d)),
        "ci95_low_mean_delta_candidate_minus_locked_B2": ci_lo,
        "ci95_high_mean_delta_candidate_minus_locked_B2": ci_hi,
        "wins_vs_locked_B2": wins,
        "losses_vs_locked_B2": losses,
        "ties_vs_locked_B2": ties,
        "win_margin_vs_locked_B2": wins - losses,
    }


def load_locked_b2_rmse() -> pd.DataFrame:
    p = ROCA / "idare_scientific_direction_lock_current_locked_baselines.csv"
    df = read_csv_required(p)
    target_col = find_col(df, ["target"], required=True)
    name_col = find_col(df, ["baseline_name"], required=True)
    level_col = find_col(df, ["baseline_level"], required=False)
    rmse_col = find_col(df, ["rmse"], required=True)
    mask = df[name_col].astype(str).str.contains("kernel_residual_shrink4", regex=False, na=False)
    if level_col is not None:
        mask |= df[level_col].astype(str).str.contains("B2_LOCKED", regex=False, na=False)
    out = df.loc[mask, [target_col, rmse_col]].copy()
    out.columns = ["target", "locked_B2_k16_rmse"]
    out["locked_B2_k16_rmse"] = pd.to_numeric(out["locked_B2_k16_rmse"], errors="coerce")
    out = out.dropna(subset=["locked_B2_k16_rmse"])
    if out.empty:
        raise SystemExit(f"Could not find B2 locked kernel residual baselines in {p}")
    return out.drop_duplicates("target")


def load_physiology_candidate_main() -> tuple[pd.DataFrame, Path]:
    p = first_existing([
        ROCA / "idare_physiology_informed_personalization_challenge_gpu_current_main_metrics.csv",
        ROCA / "idare_physiology_informed_personalization_challenge_current_main_metrics.csv",
    ])
    df = read_csv_required(p)
    df, _ = normalize_target_col(df)
    df, _ = normalize_model_col(df)
    df, _ = normalize_block_col(df)
    df, _ = normalize_k_col(df)
    rmse_col = pick_rmse_col(df, purpose="physiology candidate main metrics")
    out = df.copy()
    out["candidate_rmse"] = pd.to_numeric(out[rmse_col], errors="coerce")
    out = out[out["__model__"].str.contains("physio", case=False, na=False)].copy()
    out = out[out["__k__"].isin([4, 8, 16])].copy()
    out = out.dropna(subset=["candidate_rmse", "__k__"])
    return out, p


def load_physiology_candidate_subject_metrics() -> tuple[pd.DataFrame | None, Path | None]:
    paths = [
        ROCA / "idare_physiology_informed_personalization_challenge_gpu_current_subject_metrics.csv",
        ROCA / "idare_physiology_informed_personalization_challenge_current_subject_metrics.csv",
    ]
    try:
        p = first_existing(paths)
    except FileNotFoundError:
        return None, None
    df = read_csv_required(p)
    try:
        df, _ = normalize_target_col(df)
        df, _ = normalize_model_col(df)
        df, _ = normalize_block_col(df)
        df, _ = normalize_k_col(df)
        df, _ = normalize_subject_col(df)
        rmse_col = pick_rmse_col(df, purpose="physiology candidate subject metrics")
    except SystemExit:
        return None, p
    out = df.copy()
    out["candidate_subject_rmse"] = pd.to_numeric(out[rmse_col], errors="coerce")
    out = out[out["__model__"].str.contains("physio", case=False, na=False)].copy()
    out = out[out["__k__"].isin([4, 8, 16])].copy()
    out = out.dropna(subset=["candidate_subject_rmse", "__k__"])
    return out, p


def load_locked_b2_subject_metrics() -> tuple[pd.DataFrame | None, Path | None]:
    paths = [
        ROCA / "idare_subject_calibration_model_family_comparison_current_subject_metrics.csv",
        ROCA / "idare_subject_calibration_model_family_confirmatory_stats_current_paired_subject_stats.csv",
    ]
    try:
        p = first_existing(paths)
    except FileNotFoundError:
        return None, None
    df = read_csv_required(p)
    try:
        df, _ = normalize_target_col(df)
        df, _ = normalize_model_col(df)
        df, _ = normalize_k_col(df)
        df, _ = normalize_subject_col(df)
        rmse_col = pick_rmse_col(df, purpose="locked B2 subject metrics")
    except SystemExit:
        return None, p
    out = df.copy()
    out["locked_B2_subject_rmse"] = pd.to_numeric(out[rmse_col], errors="coerce")
    out = out[(out["__model__"].astype(str) == "kernel_residual_shrink4") & (out["__k__"] == 16)].copy()
    if out.empty:
        out = df[df["__model__"].astype(str).str.contains("kernel_residual", case=False, na=False) & (df["__k__"] == 16)].copy()
        out["locked_B2_subject_rmse"] = pd.to_numeric(out[rmse_col], errors="coerce")
    out = out.dropna(subset=["locked_B2_subject_rmse"])
    if out.empty:
        return None, p
    return out[["__target__", "__subject_id__", "locked_B2_subject_rmse"]].drop_duplicates(["__target__", "__subject_id__"]), p


def build_subject_stats_for_candidate(candidate_sub: pd.DataFrame | None, locked_sub: pd.DataFrame | None, row: pd.Series, args) -> tuple[dict[str, Any], pd.DataFrame]:
    if candidate_sub is None or locked_sub is None:
        return {"subject_evidence_status": "UNAVAILABLE", **subject_delta_stats(np.array([]), args, (row.get("target"),))}, pd.DataFrame()
    m = candidate_sub[(candidate_sub["__target__"] == str(row["target"])) & (candidate_sub["__model__"] == str(row["model"])) & (candidate_sub["__block__"] == str(row["feature_block"])) & (candidate_sub["__k__"] == float(row["k_calibration"]))].copy()
    if m.empty:
        m = candidate_sub[(candidate_sub["__target__"] == str(row["target"])) & (candidate_sub["__model__"] == str(row["model"])) & (candidate_sub["__k__"] == float(row["k_calibration"]))].copy()
    if m.empty:
        return {"subject_evidence_status": "CANDIDATE_SUBJECT_ROWS_NOT_FOUND", **subject_delta_stats(np.array([]), args, (row.get("target"),))}, pd.DataFrame()
    lock = locked_sub[locked_sub["__target__"] == str(row["target"])].copy()
    merged = m[["__target__", "__subject_id__", "candidate_subject_rmse"]].merge(lock, on=["__target__", "__subject_id__"], how="inner")
    if merged.empty:
        return {"subject_evidence_status": "NO_OVERLAP_WITH_LOCKED_B2_SUBJECTS", **subject_delta_stats(np.array([]), args, (row.get("target"),))}, pd.DataFrame()
    merged["delta_rmse_candidate_minus_locked_B2"] = merged["candidate_subject_rmse"] - merged["locked_B2_subject_rmse"]
    stats = subject_delta_stats(merged["delta_rmse_candidate_minus_locked_B2"].to_numpy(), args, (row["target"], row["feature_block"], row["model"], row["k_calibration"]))
    stats["subject_evidence_status"] = "AVAILABLE"
    merged.insert(0, "target", row["target"])
    merged.insert(1, "feature_block", row["feature_block"])
    merged.insert(2, "model", row["model"])
    merged.insert(3, "k_calibration", row["k_calibration"])
    merged = merged.rename(columns={"__subject_id__": "subject_id"})
    return stats, merged


def reason_for_sample_reduction(row: pd.Series, args) -> tuple[str, bool]:
    reasons = []
    pooled_delta = safe_float(row.get("pooled_delta_rmse_candidate_minus_locked_B2"))
    ci_hi = safe_float(row.get("ci95_high_mean_delta_candidate_minus_locked_B2"))
    win_margin = safe_float(row.get("win_margin_vs_locked_B2"))
    subject_status = str(row.get("subject_evidence_status", ""))
    if pooled_delta is None or pooled_delta > args.match_tolerance_rmse:
        reasons.append(f"pooled candidate RMSE is not within +{args.match_tolerance_rmse:.3f} of locked k=16 B2")
    if subject_status != "AVAILABLE":
        reasons.append(f"paired subject evidence unavailable: {subject_status}")
    else:
        if ci_hi is None or ci_hi > args.match_tolerance_rmse:
            reasons.append(f"bootstrap upper CI for subject delta is not <= +{args.match_tolerance_rmse:.3f}")
        if win_margin is None or win_margin < args.min_win_margin_for_match:
            reasons.append(f"win margin vs locked B2 is below {args.min_win_margin_for_match}")
    if len(reasons) == 0:
        return "lower-k physiology-assisted model matches locked k=16 personalization within practical tolerance and subject-level stability", True
    return "; ".join(reasons), False


def main():
    args = parse_args()
    locked_b2 = load_locked_b2_rmse()
    main_df, main_path = load_physiology_candidate_main()
    candidate_sub, candidate_sub_path = load_physiology_candidate_subject_metrics()
    locked_sub, locked_sub_path = load_locked_b2_subject_metrics()

    base = main_df.copy()
    base["target"] = base["__target__"]
    base["feature_block"] = base["__block__"]
    base["model"] = base["__model__"]
    base["k_calibration"] = base["__k__"].astype(int)
    base = base.merge(locked_b2, on="target", how="left")
    base["pooled_delta_rmse_candidate_minus_locked_B2"] = base["candidate_rmse"] - base["locked_B2_k16_rmse"]
    base["pooled_lift_vs_locked_B2_rmse"] = base["locked_B2_k16_rmse"] - base["candidate_rmse"]

    rows = []
    subject_rows = []
    for _, r in base.iterrows():
        if not np.isfinite(r.get("candidate_rmse", np.nan)) or not np.isfinite(r.get("locked_B2_k16_rmse", np.nan)):
            continue
        stat, subj = build_subject_stats_for_candidate(candidate_sub, locked_sub, r, args)
        out = {
            "target": r["target"],
            "feature_block": r["feature_block"],
            "model": r["model"],
            "k_calibration": int(r["k_calibration"]),
            "candidate_rmse": float(r["candidate_rmse"]),
            "locked_B2_k16_rmse": float(r["locked_B2_k16_rmse"]),
            "pooled_delta_rmse_candidate_minus_locked_B2": float(r["pooled_delta_rmse_candidate_minus_locked_B2"]),
            "pooled_lift_vs_locked_B2_rmse": float(r["pooled_lift_vs_locked_B2_rmse"]),
        }
        out.update(stat)
        reason, passes = reason_for_sample_reduction(pd.Series(out), args)
        out["passes_sample_reduction_gate"] = bool(passes and int(r["k_calibration"]) < 16)
        if int(r["k_calibration"]) >= 16 and passes:
            out["passes_sample_reduction_gate"] = False
            reason = "k=16 diagnostic row; not a calibration-sample reduction candidate"
        out["reason"] = reason
        rows.append(out)
        if subj is not None and not subj.empty:
            subject_rows.append(subj)

    metrics = pd.DataFrame(rows)
    if metrics.empty:
        raise SystemExit("No physiology candidate metrics could be constructed.")
    metrics = metrics.sort_values(["target", "pooled_delta_rmse_candidate_minus_locked_B2", "k_calibration"], ascending=[True, True, True]).reset_index(drop=True)

    decision_rows = []
    for target, g in metrics.groupby("target", sort=True):
        eligible = g[g["k_calibration"].isin([4, 8])].copy()
        passing = eligible[eligible["passes_sample_reduction_gate"] == True].copy()
        if not passing.empty:
            best = passing.sort_values(["k_calibration", "pooled_delta_rmse_candidate_minus_locked_B2"], ascending=[True, True]).iloc[0]
            decision = "GO_PHYSIOLOGY_ASSISTED_SAMPLE_REDUCTION"
        else:
            best = eligible.sort_values("pooled_delta_rmse_candidate_minus_locked_B2", ascending=True).iloc[0]
            if safe_float(best.get("pooled_delta_rmse_candidate_minus_locked_B2")) is not None and best["pooled_delta_rmse_candidate_minus_locked_B2"] <= 0.05:
                decision = "WEAK_OR_NEAR_MATCH_NEEDS_CONFIRMATION"
            else:
                decision = "NO_GO_PHYSIOLOGY_ASSISTED_SAMPLE_REDUCTION"
        decision_rows.append({
            "target": target,
            "decision": decision,
            "best_lower_k_feature_block": best["feature_block"],
            "best_lower_k_model": best["model"],
            "best_lower_k": int(best["k_calibration"]),
            "best_lower_k_rmse": safe_float(best["candidate_rmse"]),
            "locked_B2_k16_rmse": safe_float(best["locked_B2_k16_rmse"]),
            "pooled_delta_rmse_candidate_minus_locked_B2": safe_float(best["pooled_delta_rmse_candidate_minus_locked_B2"]),
            "pooled_lift_vs_locked_B2_rmse": safe_float(best["pooled_lift_vs_locked_B2_rmse"]),
            "subjects_with_pair": int(best.get("subjects_with_pair", 0) or 0),
            "ci95_high_mean_delta_candidate_minus_locked_B2": safe_float(best.get("ci95_high_mean_delta_candidate_minus_locked_B2")),
            "wins_vs_locked_B2": int(best.get("wins_vs_locked_B2", 0) or 0),
            "losses_vs_locked_B2": int(best.get("losses_vs_locked_B2", 0) or 0),
            "win_margin_vs_locked_B2": int(best.get("win_margin_vs_locked_B2", 0) or 0),
            "passes_sample_reduction_gate": bool(best.get("passes_sample_reduction_gate", False)),
            "reason": best.get("reason", ""),
        })
    decision = pd.DataFrame(decision_rows)
    subject_stats = pd.concat(subject_rows, ignore_index=True) if subject_rows else pd.DataFrame()

    next_steps = pd.DataFrame([
        {"priority": 1, "step": "05an", "title": "Representation-learning feasibility gate", "purpose": "Decide whether fixed engineered EEG/EMG features are exhausted and define raw/learned representation experiments.", "success_condition": "A learned EEG/EMG representation beats fixed-feature physiology under the same locked gates."},
        {"priority": 2, "step": "05ao", "title": "Targeted arousal high-disagreement gating refinement", "purpose": "Use the confirmed arousal EEG-bandpower high-disagreement signal as a risk/gating signal rather than direct additive correction.", "success_condition": "A gating or uncertainty-aware model improves high-disagreement arousal without degrading locked personalization."},
        {"priority": 3, "step": "05ap", "title": "Cross-dataset physiology representation sanity check", "purpose": "Check whether current DEAP fixed-feature bottleneck is dataset/representation-specific by using another affective physiology dataset if available.", "success_condition": "Physiology representation transfers or pretrains into an improved residual/deviation predictor."},
    ])

    artifact = {
        "step": "05am",
        "title": "I-DARE physiology-assisted calibration sample reduction audit",
        "inputs": {
            "physiology_candidate_main_metrics": str(main_path),
            "physiology_candidate_subject_metrics": str(candidate_sub_path) if candidate_sub_path else None,
            "locked_B2_subject_metrics": str(locked_sub_path) if locked_sub_path else None,
            "locked_B2_baselines": str(ROCA / "idare_scientific_direction_lock_current_locked_baselines.csv"),
        },
        "criteria": {
            "eligible_k_values": [4, 8],
            "reference": "locked B2 kernel_residual_shrink4 at k=16",
            "match_tolerance_rmse": args.match_tolerance_rmse,
            "min_win_margin_for_match": args.min_win_margin_for_match,
        },
        "decision_table": clean_json(decision.to_dict(orient="records")),
        "sample_reduction_metrics": clean_json(metrics.to_dict(orient="records")),
        "next_steps": clean_json(next_steps.to_dict(orient="records")),
    }

    out_prefix = ROCA / args.out_prefix
    paths = {
        "md": out_prefix.with_suffix(".md"),
        "json": out_prefix.with_suffix(".json"),
        "decision": Path(str(out_prefix) + "_decision_table.csv"),
        "metrics": Path(str(out_prefix) + "_sample_reduction_metrics.csv"),
        "subject_stats": Path(str(out_prefix) + "_subject_stats.csv"),
        "next_steps": Path(str(out_prefix) + "_next_steps.csv"),
    }
    decision.to_csv(paths["decision"], index=False)
    metrics.to_csv(paths["metrics"], index=False)
    if not subject_stats.empty:
        subject_stats.to_csv(paths["subject_stats"], index=False)
    else:
        pd.DataFrame([{"note": "subject-level candidate/locked rows were not available or could not be matched"}]).to_csv(paths["subject_stats"], index=False)
    next_steps.to_csv(paths["next_steps"], index=False)
    paths["json"].write_text(json.dumps(clean_json(artifact), indent=2), encoding="utf-8")

    lines = []
    lines.append("# I-DARE Physiology-Assisted Calibration Sample Reduction Audit\n")
    lines.append("Question: can EEG/EMG reduce the number of subject calibration samples needed to approach the locked k=16 personalization baseline?\n")
    lines.append("\n## Decision table\n")
    lines.append(md_table(decision))
    lines.append("\n## Criteria\n")
    lines.append(f"- Reference: locked B2 `kernel_residual_shrink4` at k=16.\n")
    lines.append(f"- Candidate lower-k physiology-assisted models are accepted only if pooled RMSE is within +{args.match_tolerance_rmse:.3f} of B2 and paired subject evidence is stable.\n")
    lines.append("- This is a sample-reduction test, not a global physiology-beats-personalization test.\n")
    lines.append("\n## Top sample-reduction metrics\n")
    top_cols = ["target", "k_calibration", "feature_block", "model", "candidate_rmse", "locked_B2_k16_rmse", "pooled_delta_rmse_candidate_minus_locked_B2", "ci95_high_mean_delta_candidate_minus_locked_B2", "wins_vs_locked_B2", "losses_vs_locked_B2", "win_margin_vs_locked_B2", "passes_sample_reduction_gate"]
    lines.append(md_table(metrics[top_cols].head(30)))
    lines.append("\n## Interpretation\n")
    for _, r in decision.iterrows():
        if r["passes_sample_reduction_gate"]:
            lines.append(f"- **{r['target']}**: GO. A lower-k physiology-assisted model matched the locked k=16 baseline under the practical and paired-subject gates.\n")
        else:
            lines.append(f"- **{r['target']}**: {r['decision']}. Best lower-k candidate did not satisfy the sample-reduction gate: {r['reason']}.\n")
    lines.append("\n## Next steps\n")
    lines.append(md_table(next_steps))
    paths["md"].write_text("".join(lines), encoding="utf-8")

    print("ROCA step 05am completed.")
    for p in paths.values():
        print(f"wrote: {p}")
    print("\nDecision table:")
    print(decision.to_string(index=False))
    print("\nTop sample-reduction metrics:")
    print(metrics[top_cols].head(20).to_string(index=False))
    print("\n================== KEY OUTPUTS ==================")
    print(paths["decision"].read_text(encoding="utf-8").strip())
    print()
    print(paths["next_steps"].read_text(encoding="utf-8").strip())
    print("\n================== SIZE CHECK ==================")
    for p in sorted(paths.values(), key=lambda x: x.stat().st_size if x.exists() else 0):
        if p.exists():
            print(f"{p.stat().st_size/1024:.1f}K\t{p}")
    print("\n================== GIT STATUS ==================")


if __name__ == "__main__":
    main()
