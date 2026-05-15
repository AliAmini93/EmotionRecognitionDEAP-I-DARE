#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROCA = ROOT / "docs" / "roca"

DEFAULT_AUDIT_PREFIX = "idare_residual_physiology_feature_audit_current"
DEFAULT_OUT_PREFIX = "idare_residual_physiology_confirmatory_stats_current"

PRACTICAL_RMSE_LIFT = 0.02
MIN_WIN_MARGIN = 3


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--audit-prefix", type=str, default=DEFAULT_AUDIT_PREFIX)
    p.add_argument("--out-prefix", type=str, default=DEFAULT_OUT_PREFIX)
    p.add_argument("--n-bootstrap", type=int, default=20000)
    p.add_argument("--n-permutations", type=int, default=20000)
    p.add_argument("--seed", type=int, default=20260516)
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
        return None if math.isfinite(v) else None
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    return x


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "_No rows._\n"

    use_cols = [c for c in cols if c in df.columns]
    lines = []
    lines.append("| " + " | ".join(use_cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(use_cols)) + " |")

    for _, row in df[use_cols].iterrows():
        vals = []
        for c in use_cols:
            v = row[c]
            if pd.isna(v):
                vals.append("")
            elif isinstance(v, float):
                vals.append(f"{v:.6f}")
            else:
                vals.append(str(v).replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(vals) + " |")

    return "\n".join(lines) + "\n"


def find_subject_col(df: pd.DataFrame) -> str:
    for c in ["test_subject", "subject_id", "subject", "heldout_subject"]:
        if c in df.columns:
            return c
    raise KeyError(f"Could not find subject column. columns={list(df.columns)}")


def bootstrap_ci_mean(x: np.ndarray, n_boot: int, seed: int):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]

    if len(x) == 0:
        return None, None

    rng = np.random.default_rng(seed)
    n = len(x)
    vals = np.empty(n_boot, dtype=float)

    for i in range(n_boot):
        sample = x[rng.integers(0, n, size=n)]
        vals[i] = float(np.mean(sample))

    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def sign_flip_p_positive_mean(x: np.ndarray, n_perm: int, seed: int):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]

    if len(x) == 0:
        return None

    obs = float(np.mean(x))
    rng = np.random.default_rng(seed)
    n = len(x)

    count = 0
    done = 0
    chunk = 2000

    while done < n_perm:
        m = min(chunk, n_perm - done)
        signs = rng.choice(np.array([-1.0, 1.0]), size=(m, n))
        means = (signs * x[None, :]).mean(axis=1)
        count += int(np.sum(means >= obs))
        done += m

    return float((count + 1) / (n_perm + 1))


def binom_one_sided_p_wins(wins: int, losses: int):
    n = int(wins + losses)
    if n <= 0:
        return None

    # H1: wins > losses. If wins is not above half, evidence for improvement is absent.
    prob = 0.0
    for k in range(int(wins), n + 1):
        prob += math.comb(n, k) * (0.5 ** n)

    return float(prob)


def paired_stats_for_metric(
    paired: pd.DataFrame,
    metric: str,
    n_boot: int,
    n_perm: int,
    seed: int,
):
    stim_col = f"{metric}_stimulus"
    model_col = f"{metric}_model"

    if stim_col not in paired.columns or model_col not in paired.columns:
        return None

    improvement = paired[stim_col].to_numpy(dtype=float) - paired[model_col].to_numpy(dtype=float)
    improvement = improvement[np.isfinite(improvement)]

    if len(improvement) == 0:
        return None

    ci_low, ci_high = bootstrap_ci_mean(improvement, n_boot=n_boot, seed=seed)
    perm_p = sign_flip_p_positive_mean(improvement, n_perm=n_perm, seed=seed + 17)

    wins = int((improvement > 0).sum())
    losses = int((improvement < 0).sum())
    ties = int((improvement == 0).sum())
    sign_p = binom_one_sided_p_wins(wins, losses)

    mean_imp = float(np.mean(improvement))
    median_imp = float(np.median(improvement))

    passes = (
        mean_imp > 0
        and ci_low is not None
        and ci_low > 0
        and perm_p is not None
        and perm_p < 0.05
        and (wins - losses) > MIN_WIN_MARGIN
    )

    return {
        "metric": metric,
        "subjects": int(len(improvement)),
        "mean_improvement_stimulus_minus_model": mean_imp,
        "median_improvement_stimulus_minus_model": median_imp,
        "ci95_low_mean_improvement": ci_low,
        "ci95_high_mean_improvement": ci_high,
        "signflip_p_one_sided_mean_gt_zero": perm_p,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_margin": int(wins - losses),
        "sign_test_p_one_sided_wins_gt_losses": sign_p,
        "passes_confirmatory_metric": bool(passes),
    }


def main():
    args = parse_args()

    subject_path = ROCA / f"{args.audit_prefix}_subject_metrics.csv"
    main_path = ROCA / f"{args.audit_prefix}_main_metrics.csv"

    if not subject_path.exists():
        raise FileNotFoundError(subject_path)
    if not main_path.exists():
        raise FileNotFoundError(main_path)

    subject = pd.read_csv(subject_path)
    main_metrics = pd.read_csv(main_path)

    subject_col = find_subject_col(subject)

    needed = ["target", "model", subject_col, "rmse", "dev_rmse"]
    missing = [c for c in needed if c not in subject.columns]
    if missing:
        raise KeyError(f"Missing required columns in subject metrics: {missing}; columns={list(subject.columns)}")

    stim = subject[subject["model"].eq("stimulus_only")].copy()
    phys = subject[~subject["model"].eq("stimulus_only")].copy()

    if stim.empty:
        raise ValueError("No stimulus_only rows found in subject metrics.")

    stim_keep = stim[["target", subject_col, "rmse", "dev_rmse"]].rename(
        columns={
            "rmse": "rmse_stimulus",
            "dev_rmse": "dev_rmse_stimulus",
        }
    )

    rows = []

    for (target, model), g in phys.groupby(["target", "model"]):
        g_keep = g[["target", subject_col, "rmse", "dev_rmse"]].rename(
            columns={
                "rmse": "rmse_model",
                "dev_rmse": "dev_rmse_model",
            }
        )

        paired = g_keep.merge(stim_keep, on=["target", subject_col], how="inner")

        for metric in ["rmse", "dev_rmse"]:
            stats = paired_stats_for_metric(
                paired,
                metric=metric,
                n_boot=args.n_bootstrap,
                n_perm=args.n_permutations,
                seed=args.seed + abs(hash((target, model, metric))) % 100000,
            )
            if stats is None:
                continue

            pooled = main_metrics[
                main_metrics["target"].eq(target)
                & main_metrics["model"].eq(model)
            ]

            if not pooled.empty:
                pooled = pooled.iloc[0]
                stats["pooled_rmse"] = safe_float(pooled.get("rmse"))
                stats["pooled_dev_rmse"] = safe_float(pooled.get("dev_rmse"))
                stats["pooled_lift_vs_stimulus_rmse"] = safe_float(pooled.get("lift_vs_stimulus_rmse"))
                stats["pooled_lift_vs_stimulus_dev_rmse"] = safe_float(pooled.get("lift_vs_stimulus_dev_rmse"))
                stats["pooled_dev_pearson"] = safe_float(pooled.get("dev_pearson"))
            else:
                stats["pooled_rmse"] = None
                stats["pooled_dev_rmse"] = None
                stats["pooled_lift_vs_stimulus_rmse"] = None
                stats["pooled_lift_vs_stimulus_dev_rmse"] = None
                stats["pooled_dev_pearson"] = None

            stats["target"] = target
            stats["model"] = model
            rows.append(stats)

    paired_stats = pd.DataFrame(rows)

    verdict_rows = []
    for target, g in paired_stats.groupby("target"):
        models = sorted(g["model"].unique())

        target_pass = False
        best_reason_rows = []

        for model in models:
            mg = g[g["model"].eq(model)]

            rmse_row = mg[mg["metric"].eq("rmse")]
            dev_row = mg[mg["metric"].eq("dev_rmse")]

            rmse_pass = bool(rmse_row["passes_confirmatory_metric"].iloc[0]) if not rmse_row.empty else False
            dev_pass = bool(dev_row["passes_confirmatory_metric"].iloc[0]) if not dev_row.empty else False

            pooled_lift = None
            if not rmse_row.empty:
                pooled_lift = safe_float(rmse_row["pooled_lift_vs_stimulus_rmse"].iloc[0])

            model_pass = bool(
                rmse_pass
                and dev_pass
                and pooled_lift is not None
                and pooled_lift >= PRACTICAL_RMSE_LIFT
            )

            if model_pass:
                target_pass = True

            best_reason_rows.append({
                "target": target,
                "model": model,
                "rmse_pass": rmse_pass,
                "dev_rmse_pass": dev_pass,
                "pooled_lift_vs_stimulus_rmse": pooled_lift,
                "model_pass": model_pass,
            })

        reason_df = pd.DataFrame(best_reason_rows)
        if not reason_df.empty:
            reason_df = reason_df.sort_values(
                ["model_pass", "pooled_lift_vs_stimulus_rmse"],
                ascending=[False, False],
            )
            best = reason_df.iloc[0]
            best_model = best["model"]
            best_pooled_lift = safe_float(best["pooled_lift_vs_stimulus_rmse"])
        else:
            best_model = None
            best_pooled_lift = None

        verdict_rows.append({
            "target": target,
            "confirmatory_verdict": "GO_CONFIRMED_RESIDUAL_SIGNAL" if target_pass else "NO_GO_CONFIRMED_CURRENT_FEATURE_SET",
            "best_candidate_model": best_model,
            "best_candidate_pooled_lift_vs_stimulus_rmse": best_pooled_lift,
            "criterion": (
                "requires positive paired subject-level RMSE and dev-RMSE improvement, "
                "bootstrap CI lower bound > 0, sign-flip p < 0.05, win margin > 3, "
                f"and pooled RMSE lift >= {PRACTICAL_RMSE_LIFT}"
            ),
        })

    verdict = pd.DataFrame(verdict_rows)

    out_stats = ROCA / f"{args.out_prefix}_paired_subject_stats.csv"
    out_verdict = ROCA / f"{args.out_prefix}_verdict.csv"
    out_json = ROCA / f"{args.out_prefix}.json"
    out_md = ROCA / f"{args.out_prefix}.md"

    paired_stats.to_csv(out_stats, index=False)
    verdict.to_csv(out_verdict, index=False)

    report = {
        "objective": "Confirm whether any tested physiological feature block improves stimulus-only at the paired subject level.",
        "inputs": {
            "subject_metrics": str(subject_path),
            "main_metrics": str(main_path),
            "audit_prefix": args.audit_prefix,
        },
        "settings": {
            "n_bootstrap": args.n_bootstrap,
            "n_permutations": args.n_permutations,
            "seed": args.seed,
            "practical_rmse_lift": PRACTICAL_RMSE_LIFT,
            "min_win_margin": MIN_WIN_MARGIN,
        },
        "verdict": verdict.to_dict(orient="records"),
        "paired_subject_stats": paired_stats.to_dict(orient="records"),
    }
    out_json.write_text(json.dumps(clean_json(report), indent=2, ensure_ascii=False), encoding="utf-8")

    stat_cols = [
        "target", "model", "metric", "subjects",
        "mean_improvement_stimulus_minus_model",
        "median_improvement_stimulus_minus_model",
        "ci95_low_mean_improvement",
        "ci95_high_mean_improvement",
        "signflip_p_one_sided_mean_gt_zero",
        "wins", "losses", "ties", "win_margin",
        "sign_test_p_one_sided_wins_gt_losses",
        "pooled_lift_vs_stimulus_rmse",
        "pooled_lift_vs_stimulus_dev_rmse",
        "passes_confirmatory_metric",
    ]

    lines = []
    lines.append("# I-DARE Residual Physiology Confirmatory Statistics\n")
    lines.append("Positive improvement means `stimulus_only RMSE - physiology_model RMSE`; positive is good for physiology.\n")

    lines.append("## Confirmatory verdict\n")
    lines.append(md_table(verdict, [
        "target",
        "confirmatory_verdict",
        "best_candidate_model",
        "best_candidate_pooled_lift_vs_stimulus_rmse",
        "criterion",
    ]))

    lines.append("\n## Paired subject-level statistics\n")
    lines.append(md_table(paired_stats.sort_values(
        ["target", "metric", "mean_improvement_stimulus_minus_model"],
        ascending=[True, True, False],
    ), stat_cols))

    lines.append("\n## Interpretation\n")
    lines.append(
        "- A positive pooled correlation is not enough.\n"
        "- The model must beat stimulus-only per subject and in residual/dev RMSE.\n"
        "- If the verdict is `NO_GO_CONFIRMED_CURRENT_FEATURE_SET`, current engineered EEG/EMG feature blocks should not be used to claim cross-subject physiological decoding beyond stimulus prior.\n"
    )

    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 05y completed.")
    for p in [out_md, out_json, out_stats, out_verdict]:
        print(f"wrote: {p}")

    print("\nConfirmatory verdict:")
    print(verdict.to_string(index=False))

    print("\nTop paired subject stats:")
    top = paired_stats.sort_values(
        ["target", "metric", "mean_improvement_stimulus_minus_model"],
        ascending=[True, True, False],
    )
    print(top[stat_cols].groupby(["target", "metric"], as_index=False).head(5).to_string(index=False))


if __name__ == "__main__":
    main()
