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

DEFAULT_INPUT_PREFIX = "idare_subject_calibration_model_family_comparison_current"
DEFAULT_OUT_PREFIX = "idare_subject_calibration_model_family_confirmatory_stats_current"

PRACTICAL_RMSE_LIFT = 0.02
MIN_WIN_MARGIN = 3
EPS = 1e-12


def stable_seed(*parts: Any) -> int:
    payload = "|".join(str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "little") % (2**32)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input-prefix", type=str, default=DEFAULT_INPUT_PREFIX)
    p.add_argument("--out-prefix", type=str, default=DEFAULT_OUT_PREFIX)
    p.add_argument("--n-bootstrap", type=int, default=20000)
    p.add_argument("--n-permutations", type=int, default=20000)
    p.add_argument("--seed", type=int, default=20260529)
    p.add_argument("--practical-rmse-lift", type=float, default=PRACTICAL_RMSE_LIFT)
    p.add_argument("--min-win-margin", type=int, default=MIN_WIN_MARGIN)
    return p.parse_args()


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
    if pd.isna(x) if not isinstance(x, (list, tuple, dict, np.ndarray)) else False:
        return None
    return x


def md_cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6f}" if math.isfinite(v) else ""
    if isinstance(v, (np.floating,)):
        v = float(v)
        return f"{v:.6f}" if math.isfinite(v) else ""
    if isinstance(v, (np.integer,)):
        return str(int(v))
    try:
        if bool(pd.isna(v)):
            return ""
    except (TypeError, ValueError):
        pass
    return str(v).replace("|", "\\|").replace("\n", " ")


def md_table(df: pd.DataFrame, cols: list[str], max_rows: int | None = None) -> str:
    if df is None or df.empty:
        return "_No rows._\n"
    use = df.copy()
    if max_rows is not None:
        use = use.head(max_rows)
    existing = [c for c in cols if c in use.columns]
    lines = []
    lines.append("| " + " | ".join(existing) + " |")
    lines.append("| " + " | ".join(["---"] * len(existing)) + " |")
    for _, row in use.iterrows():
        lines.append("| " + " | ".join(md_cell(row.get(c)) for c in existing) + " |")
    return "\n".join(lines) + "\n"


def load_csv(path: Path, required: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"{path} missing columns: {missing}")
    return df


def normalize_k(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "k_calibration" in df.columns:
        df["k_calibration"] = pd.to_numeric(df["k_calibration"], errors="coerce").fillna(0).astype(int)
    return df


def bootstrap_mean_ci(x: np.ndarray, n_bootstrap: int, seed: int) -> tuple[float | None, float | None]:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n == 0:
        return None, None
    if n_bootstrap <= 0:
        return None, None
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_bootstrap, n))
    means = x[idx].mean(axis=1)
    return safe_float(np.quantile(means, 0.025)), safe_float(np.quantile(means, 0.975))


def signflip_p_mean_gt_zero(x: np.ndarray, n_permutations: int, seed: int) -> float | None:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n == 0 or n_permutations <= 0:
        return None
    observed = float(np.mean(x))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_permutations, n))
    sim = (signs * x).mean(axis=1)
    return safe_float((np.sum(sim >= observed) + 1.0) / (n_permutations + 1.0))


def sign_test_p_wins_gt_losses(wins: int, losses: int) -> float | None:
    n = int(wins) + int(losses)
    if n <= 0:
        return None
    # exact one-sided binomial tail P[X >= wins], X~Binom(n, 0.5)
    tail = 0.0
    for k in range(int(wins), n + 1):
        tail += math.comb(n, k)
    return safe_float(tail / (2.0 ** n))


def subject_table_for(subject: pd.DataFrame, target: str, k: int, model: str) -> pd.DataFrame:
    g = subject[
        subject["target"].astype(str).eq(str(target))
        & subject["k_calibration"].eq(int(k))
        & subject["model"].astype(str).eq(str(model))
    ].copy()
    if g.empty:
        return g
    if "subject_id" not in g.columns:
        raise KeyError("subject_metrics must contain subject_id")
    return (
        g.groupby(["target", "k_calibration", "model", "subject_id"], as_index=False)["rmse"]
        .mean()
        .sort_values("subject_id")
    )


def compute_paired_stats_for_row(
    row: pd.Series,
    subject: pd.DataFrame,
    n_bootstrap: int,
    n_permutations: int,
    seed_base: int,
    practical_lift: float,
    min_win_margin: int,
) -> tuple[dict[str, Any] | None, pd.DataFrame]:
    target = str(row["target"])
    model = str(row["model"])
    k = int(row.get("k_calibration", 0))
    locked_model = row.get("locked_reference_model")
    if locked_model is None or pd.isna(locked_model) or str(locked_model).strip() == "":
        locked_model = "stimulus_only" if k == 0 else "bias_shrink4"
    locked_model = str(locked_model)

    candidate = subject_table_for(subject, target, k, model)
    locked = subject_table_for(subject, target, k, locked_model)

    if candidate.empty or locked.empty:
        return None, pd.DataFrame()

    merged = candidate[["subject_id", "rmse"]].rename(columns={"rmse": "candidate_rmse"}).merge(
        locked[["subject_id", "rmse"]].rename(columns={"rmse": "locked_rmse"}),
        on="subject_id",
        how="inner",
    )
    if merged.empty:
        return None, pd.DataFrame()

    merged["improvement_locked_minus_candidate"] = merged["locked_rmse"] - merged["candidate_rmse"]
    merged["delta_rmse_candidate_minus_locked"] = merged["candidate_rmse"] - merged["locked_rmse"]

    x = merged["improvement_locked_minus_candidate"].to_numpy(dtype=float)
    wins = int((x > EPS).sum())
    losses = int((x < -EPS).sum())
    ties = int(len(x) - wins - losses)
    win_margin = wins - losses
    ci_low, ci_high = bootstrap_mean_ci(x, n_bootstrap, stable_seed(seed_base, target, model, k, "bootstrap"))
    p_signflip = signflip_p_mean_gt_zero(x, n_permutations, stable_seed(seed_base, target, model, k, "signflip"))
    p_signtest = sign_test_p_wins_gt_losses(wins, losses)

    pooled_lift = safe_float(row.get("lift_vs_locked_reference_rmse"))
    if pooled_lift is None and "locked_reference_rmse" in row and not pd.isna(row.get("locked_reference_rmse")):
        pooled_lift = safe_float(float(row.get("locked_reference_rmse")) - float(row.get("rmse")))

    passes = (
        pooled_lift is not None
        and pooled_lift >= practical_lift
        and safe_float(np.mean(x)) is not None
        and float(np.mean(x)) > 0
        and ci_low is not None
        and ci_low > 0
        and p_signflip is not None
        and p_signflip < 0.05
        and win_margin >= min_win_margin
    )

    stats = {
        "target": target,
        "k_calibration": k,
        "model": model,
        "locked_reference_model": locked_model,
        "subjects": int(len(merged)),
        "candidate_rmse_pooled": safe_float(row.get("rmse")),
        "locked_reference_rmse_pooled": safe_float(row.get("locked_reference_rmse")),
        "pooled_lift_vs_locked_reference_rmse": pooled_lift,
        "lift_vs_stimulus_rmse": safe_float(row.get("lift_vs_stimulus_rmse")),
        "mean_subject_improvement_locked_minus_model": safe_float(np.mean(x)),
        "median_subject_improvement_locked_minus_model": safe_float(np.median(x)),
        "ci95_low_mean_subject_improvement": ci_low,
        "ci95_high_mean_subject_improvement": ci_high,
        "signflip_p_one_sided_mean_gt_zero": p_signflip,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_margin": int(win_margin),
        "sign_test_p_one_sided_wins_gt_losses": p_signtest,
        "passes_confirmatory_metric": bool(passes),
        "pearson": safe_float(row.get("pearson")),
        "spearman": safe_float(row.get("spearman")),
        "ccc": safe_float(row.get("ccc")),
    }

    merged["target"] = target
    merged["k_calibration"] = k
    merged["model"] = model
    merged["locked_reference_model"] = locked_model
    merged["candidate_lift_vs_locked"] = merged["locked_rmse"] - merged["candidate_rmse"]
    return stats, merged


def build_stats(main: pd.DataFrame, subject: pd.DataFrame, args) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    failure_parts = []

    main = normalize_k(main)
    subject = normalize_k(subject)

    # We do not need to test the locked model against itself, but keeping zero rows in
    # the calibration curve can be useful. Here we test every row with a valid reference.
    for _, row in main.iterrows():
        if "rmse" not in row or pd.isna(row.get("rmse")):
            continue
        stats, failures = compute_paired_stats_for_row(
            row=row,
            subject=subject,
            n_bootstrap=args.n_bootstrap,
            n_permutations=args.n_permutations,
            seed_base=args.seed,
            practical_lift=args.practical_rmse_lift,
            min_win_margin=args.min_win_margin,
        )
        if stats is None:
            continue
        rows.append(stats)
        if failures is not None and not failures.empty:
            failure_parts.append(failures)

    stats_df = pd.DataFrame(rows)
    failure_df = pd.concat(failure_parts, ignore_index=True) if failure_parts else pd.DataFrame()
    if not stats_df.empty:
        stats_df = stats_df.sort_values(
            ["target", "passes_confirmatory_metric", "pooled_lift_vs_locked_reference_rmse", "win_margin", "candidate_rmse_pooled"],
            ascending=[True, False, False, False, True],
        ).reset_index(drop=True)
    return stats_df, failure_df


def choose_verdict(stats_df: pd.DataFrame, args) -> pd.DataFrame:
    rows = []
    if stats_df.empty:
        return pd.DataFrame(rows)

    candidate_stats = stats_df.copy()
    candidate_stats = candidate_stats[candidate_stats["model"].ne(candidate_stats["locked_reference_model"])]
    if candidate_stats.empty:
        candidate_stats = stats_df.copy()

    for target, g in candidate_stats.groupby("target", sort=True):
        g = g.copy()
        g = g.sort_values(
            ["passes_confirmatory_metric", "pooled_lift_vs_locked_reference_rmse", "win_margin", "candidate_rmse_pooled"],
            ascending=[False, False, False, True],
        )
        best = g.iloc[0]

        reasons = []
        if not bool(best.get("passes_confirmatory_metric")):
            if safe_float(best.get("pooled_lift_vs_locked_reference_rmse")) is None or float(best.get("pooled_lift_vs_locked_reference_rmse")) < args.practical_rmse_lift:
                reasons.append(f"pooled lift vs locked reference < {args.practical_rmse_lift}")
            if safe_float(best.get("mean_subject_improvement_locked_minus_model")) is None or float(best.get("mean_subject_improvement_locked_minus_model")) <= 0:
                reasons.append("mean paired subject improvement is not positive")
            if safe_float(best.get("ci95_low_mean_subject_improvement")) is None or float(best.get("ci95_low_mean_subject_improvement")) <= 0:
                reasons.append("bootstrap CI lower bound is not > 0")
            if safe_float(best.get("signflip_p_one_sided_mean_gt_zero")) is None or float(best.get("signflip_p_one_sided_mean_gt_zero")) >= 0.05:
                reasons.append("sign-flip p is not < 0.05")
            if int(best.get("win_margin", 0)) < args.min_win_margin:
                reasons.append(f"win margin < {args.min_win_margin}")

        if bool(best.get("passes_confirmatory_metric")):
            decision = "GO_CONFIRMED_MODEL_FAMILY_CALIBRATION"
            reason = "candidate beats locked few-shot reference in pooled RMSE and paired subject-level confirmatory statistics"
        elif safe_float(best.get("pooled_lift_vs_locked_reference_rmse")) is not None and float(best.get("pooled_lift_vs_locked_reference_rmse")) > 0:
            decision = "WEAK_GO_MODEL_FAMILY_NEEDS_CAUTION"
            reason = "; ".join(reasons) if reasons else "positive pooled lift but confirmatory criteria are incomplete"
        else:
            decision = "NO_GO_MODEL_FAMILY_OVER_LOCKED_FEWSHOT"
            reason = "; ".join(reasons) if reasons else "candidate does not improve locked few-shot reference"

        rows.append({
            "target": target,
            "decision": decision,
            "best_candidate_model": best.get("model"),
            "best_k_calibration": int(best.get("k_calibration")),
            "locked_reference_model": best.get("locked_reference_model"),
            "best_rmse": safe_float(best.get("candidate_rmse_pooled")),
            "locked_reference_rmse": safe_float(best.get("locked_reference_rmse_pooled")),
            "best_lift_vs_locked_reference_rmse": safe_float(best.get("pooled_lift_vs_locked_reference_rmse")),
            "best_lift_vs_stimulus_rmse": safe_float(best.get("lift_vs_stimulus_rmse")),
            "mean_subject_improvement_locked_minus_model": safe_float(best.get("mean_subject_improvement_locked_minus_model")),
            "ci95_low_mean_subject_improvement": safe_float(best.get("ci95_low_mean_subject_improvement")),
            "ci95_high_mean_subject_improvement": safe_float(best.get("ci95_high_mean_subject_improvement")),
            "signflip_p_one_sided_mean_gt_zero": safe_float(best.get("signflip_p_one_sided_mean_gt_zero")),
            "wins": int(best.get("wins")),
            "losses": int(best.get("losses")),
            "win_margin": int(best.get("win_margin")),
            "confirmatory_pass": bool(best.get("passes_confirmatory_metric")),
            "reason": reason,
        })
    return pd.DataFrame(rows)


def select_failure_subjects(failure_df: pd.DataFrame, verdict: pd.DataFrame) -> pd.DataFrame:
    if failure_df.empty or verdict.empty:
        return pd.DataFrame()
    parts = []
    for _, row in verdict.iterrows():
        g = failure_df[
            failure_df["target"].astype(str).eq(str(row["target"]))
            & failure_df["model"].astype(str).eq(str(row["best_candidate_model"]))
            & failure_df["k_calibration"].eq(int(row["best_k_calibration"]))
        ].copy()
        if g.empty:
            continue
        g = g.sort_values("delta_rmse_candidate_minus_locked", ascending=False)
        parts.append(g.head(20))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def main():
    args = parse_args()
    ROCA.mkdir(parents=True, exist_ok=True)

    main_path = ROCA / f"{args.input_prefix}_main_metrics.csv"
    subject_path = ROCA / f"{args.input_prefix}_subject_metrics.csv"
    verdict_input_path = ROCA / f"{args.input_prefix}_verdict.csv"
    best_input_path = ROCA / f"{args.input_prefix}_best_ranking.csv"

    main_df = load_csv(main_path, ["target", "k_calibration", "model", "rmse"])
    subject_df = load_csv(subject_path, ["target", "k_calibration", "model", "subject_id", "rmse"])

    stats_df, all_failures = build_stats(main_df, subject_df, args)
    verdict_df = choose_verdict(stats_df, args)
    failure_df = select_failure_subjects(all_failures, verdict_df)

    out_md = ROCA / f"{args.out_prefix}.md"
    out_json = ROCA / f"{args.out_prefix}.json"
    out_verdict = ROCA / f"{args.out_prefix}_verdict.csv"
    out_stats = ROCA / f"{args.out_prefix}_paired_subject_stats.csv"
    out_curve = ROCA / f"{args.out_prefix}_model_family_curve.csv"
    out_fail = ROCA / f"{args.out_prefix}_failure_subjects.csv"

    verdict_df.to_csv(out_verdict, index=False)
    stats_df.to_csv(out_stats, index=False)
    stats_df.to_csv(out_curve, index=False)
    failure_df.to_csv(out_fail, index=False)

    report = {
        "title": "I-DARE subject-calibration model-family confirmatory statistics",
        "inputs": {
            "main_metrics": str(main_path),
            "subject_metrics": str(subject_path),
            "input_verdict": str(verdict_input_path) if verdict_input_path.exists() else None,
            "input_best_ranking": str(best_input_path) if best_input_path.exists() else None,
        },
        "outputs": {
            "md": str(out_md),
            "json": str(out_json),
            "verdict": str(out_verdict),
            "paired_subject_stats": str(out_stats),
            "model_family_curve": str(out_curve),
            "failure_subjects": str(out_fail),
        },
        "criteria": {
            "positive_improvement_definition": "locked_reference_RMSE - candidate_RMSE; positive favors candidate",
            "practical_rmse_lift": args.practical_rmse_lift,
            "min_win_margin": args.min_win_margin,
            "bootstrap_ci": "95% bootstrap CI over subjects for mean paired RMSE improvement",
            "signflip_test": "one-sided sign-flip test for mean paired improvement > 0",
        },
        "verdict": verdict_df.to_dict(orient="records"),
        "paired_subject_stats": stats_df.to_dict(orient="records"),
        "failure_subjects": failure_df.to_dict(orient="records"),
    }
    out_json.write_text(json.dumps(clean_json(report), ensure_ascii=False, indent=2), encoding="utf-8")

    verdict_cols = [
        "target", "decision", "best_candidate_model", "best_k_calibration",
        "locked_reference_model", "best_rmse", "locked_reference_rmse",
        "best_lift_vs_locked_reference_rmse", "mean_subject_improvement_locked_minus_model",
        "ci95_low_mean_subject_improvement", "signflip_p_one_sided_mean_gt_zero",
        "wins", "losses", "win_margin", "confirmatory_pass", "reason",
    ]
    curve_cols = [
        "target", "k_calibration", "model", "locked_reference_model",
        "candidate_rmse_pooled", "locked_reference_rmse_pooled",
        "pooled_lift_vs_locked_reference_rmse", "lift_vs_stimulus_rmse",
        "mean_subject_improvement_locked_minus_model", "ci95_low_mean_subject_improvement",
        "signflip_p_one_sided_mean_gt_zero", "wins", "losses", "win_margin",
        "passes_confirmatory_metric",
    ]
    fail_cols = [
        "target", "subject_id", "k_calibration", "model", "locked_reference_model",
        "candidate_rmse", "locked_rmse", "delta_rmse_candidate_minus_locked",
        "improvement_locked_minus_candidate",
    ]

    lines = []
    lines.append("# I-DARE Subject-Calibration Model-Family Confirmatory Statistics\n")
    lines.append("This report validates whether the 05ae model-family winner beats the locked few-shot reference at paired subject level.\n")
    lines.append("Positive improvement means `locked_reference_RMSE - candidate_RMSE`; positive is good for the candidate.\n")
    lines.append("## Confirmatory verdict\n")
    lines.append(md_table(verdict_df, verdict_cols))
    lines.append("\n## Model-family calibration curve / paired subject statistics\n")
    lines.append(md_table(stats_df, curve_cols, max_rows=80))
    lines.append("\n## Worst failure subjects for selected candidates\n")
    lines.append(md_table(failure_df, fail_cols, max_rows=60))
    lines.append("\n## Interpretation\n")
    lines.append("- `GO_CONFIRMED_MODEL_FAMILY_CALIBRATION` means the model-family candidate beats the locked few-shot reference in pooled RMSE and paired subject-level tests.\n")
    lines.append("- If confirmed, this should become the next locked personalization baseline. Future physiology, adapters, or deep models should be compared against this baseline, not only against stimulus-only.\n")
    lines.append("- Failure subjects are preserved so we can inspect where the personalization model still regresses.\n")
    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05af completed.")
    for p in [out_md, out_json, out_verdict, out_stats, out_curve, out_fail]:
        print(f"wrote: {p}")

    print("\nVerdict:")
    print(verdict_df[verdict_cols].to_string(index=False))

    print("\nTop model-family confirmatory rows:")
    top = stats_df[stats_df["model"].ne(stats_df["locked_reference_model"])].copy()
    if not top.empty:
        top = top.sort_values(
            ["target", "passes_confirmatory_metric", "pooled_lift_vs_locked_reference_rmse", "win_margin"],
            ascending=[True, False, False, False],
        )
        print(top[curve_cols].head(30).to_string(index=False))

    print("\nFailure subjects preview:")
    if not failure_df.empty:
        print(failure_df[fail_cols].head(30).to_string(index=False))
    else:
        print("No failure subject rows generated.")


if __name__ == "__main__":
    main()
