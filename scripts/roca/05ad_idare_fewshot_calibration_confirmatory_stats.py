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

DEFAULT_FEWSHOT_PREFIX = "idare_fewshot_residual_calibration_audit_current"
DEFAULT_OUT_PREFIX = "idare_fewshot_calibration_confirmatory_stats_current"

PRACTICAL_RMSE_LIFT = 0.02
MIN_WIN_MARGIN = 3
EPS = 1e-12


def stable_seed(*parts: Any) -> int:
    payload = "|".join(str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "little") % (2**32)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--fewshot-prefix", type=str, default=DEFAULT_FEWSHOT_PREFIX)
    p.add_argument("--out-prefix", type=str, default=DEFAULT_OUT_PREFIX)
    p.add_argument("--n-bootstrap", type=int, default=20000)
    p.add_argument("--n-permutations", type=int, default=20000)
    p.add_argument("--seed", type=int, default=20260529)
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
    try:
        if not isinstance(x, (list, tuple, dict, np.ndarray)) and bool(pd.isna(x)):
            return None
    except (TypeError, ValueError):
        pass
    return x


def md_cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (np.integer, int)):
        return str(int(v))
    if isinstance(v, (np.floating, float)):
        return f"{float(v):.6f}" if math.isfinite(float(v)) else ""
    try:
        if bool(pd.isna(v)):
            return ""
    except (TypeError, ValueError):
        pass
    return str(v).replace("|", "\\|").replace("\n", " ")


def md_table(df: pd.DataFrame, cols: list[str] | None = None, max_rows: int | None = None) -> str:
    if df is None or df.empty:
        return "_No rows._\n"
    if cols is None:
        cols = list(df.columns)
    cols = [c for c in cols if c in df.columns]
    show = df[cols].copy()
    if max_rows is not None:
        show = show.head(max_rows)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in show.iterrows():
        lines.append("| " + " | ".join(md_cell(row.get(c)) for c in cols) + " |")
    return "\n".join(lines) + "\n"


def read_csv(path: Path, name: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing {name}: {path}")
    return pd.read_csv(path)


def normalize_k(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "k_calibration" in df.columns:
        df["k_calibration"] = pd.to_numeric(df["k_calibration"], errors="coerce").fillna(-1).astype(int)
    return df


def find_subject_col(df: pd.DataFrame) -> str:
    for c in ["subject_id", "subject", "test_subject", "participant_id", "subj"]:
        if c in df.columns:
            return c
    raise KeyError(f"Could not find a subject column in subject_metrics. Columns={list(df.columns)}")


def metric_col(df: pd.DataFrame, primary: str, fallback: str = "rmse") -> str:
    if primary in df.columns:
        return primary
    if fallback in df.columns:
        return fallback
    raise KeyError(f"Missing metric column {primary!r} and fallback {fallback!r}")


def get_reference_subject_rows(subject: pd.DataFrame, subject_col: str) -> pd.DataFrame:
    candidates = [
        "stimulus_plus_fewshot_bias_shrink4",
        "stimulus_plus_fewshot_bias",
        "stimulus_only",
    ]

    refs = []
    for target, g in subject.groupby("target", dropna=False):
        g0 = g[g["k_calibration"].eq(0)].copy()
        chosen = None
        for model in candidates:
            gm = g0[g0["model"].eq(model)]
            if not gm.empty:
                chosen = gm
                break
        if chosen is None or chosen.empty:
            if g0.empty:
                raise ValueError(f"No k=0 reference rows found for target={target}")
            first_model = str(g0["model"].iloc[0])
            chosen = g0[g0["model"].eq(first_model)].copy()

        residual_metric = metric_col(chosen, "residual_rmse", "rmse")
        agg = chosen.groupby(["target", subject_col], as_index=False).agg(
            ref_rmse=("rmse", "mean"),
            ref_residual_rmse=(residual_metric, "mean"),
        )
        agg["reference_model"] = str(chosen["model"].iloc[0])
        refs.append(agg)

    return pd.concat(refs, ignore_index=True)


def get_reference_main_rows(main: pd.DataFrame) -> pd.DataFrame:
    candidates = [
        "stimulus_plus_fewshot_bias_shrink4",
        "stimulus_plus_fewshot_bias",
        "stimulus_only",
    ]
    refs = []
    for target, g in main.groupby("target", dropna=False):
        g0 = g[g["k_calibration"].eq(0)].copy()
        chosen = None
        for model in candidates:
            gm = g0[g0["model"].eq(model)]
            if not gm.empty:
                chosen = gm
                break
        if chosen is None or chosen.empty:
            if g0.empty:
                raise ValueError(f"No k=0 main reference row found for target={target}")
            chosen = g0.iloc[[0]].copy()
        row = chosen.iloc[0]
        refs.append({
            "target": target,
            "reference_model": str(row["model"]),
            "ref_pooled_rmse": safe_float(row["rmse"]),
            "ref_pooled_residual_rmse": safe_float(row["residual_rmse"] if "residual_rmse" in chosen.columns else row["rmse"]),
        })
    return pd.DataFrame(refs)


def bootstrap_mean_ci(values: np.ndarray, n_bootstrap: int, rng: np.random.Generator):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return None, None, None
    if n_bootstrap <= 0:
        mean = float(np.mean(values))
        return mean, None, None
    idx = rng.integers(0, len(values), size=(n_bootstrap, len(values)))
    means = values[idx].mean(axis=1)
    return float(np.mean(values)), float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def signflip_p_one_sided(values: np.ndarray, n_perm: int, rng: np.random.Generator):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return None
    obs = float(np.mean(values))
    if n_perm <= 0:
        return None
    signs = rng.choice(np.array([-1.0, 1.0], dtype=float), size=(n_perm, len(values)))
    perm_means = (signs * values[None, :]).mean(axis=1)
    return float((np.sum(perm_means >= obs) + 1.0) / (n_perm + 1.0))


def binom_one_sided_p_wins_gt_losses(wins: int, losses: int) -> float | None:
    n = int(wins + losses)
    if n <= 0:
        return None
    s = 0
    for k in range(int(wins), n + 1):
        s += math.comb(n, k)
    return float(s / (2 ** n))


def paired_stats_for_values(
    values: np.ndarray,
    n_bootstrap: int,
    n_perm: int,
    seed_parts: tuple[Any, ...],
):
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    wins = int(np.sum(values > EPS))
    losses = int(np.sum(values < -EPS))
    ties = int(len(values) - wins - losses)
    rng = np.random.default_rng(stable_seed(*seed_parts, "bootstrap"))
    mean, ci_low, ci_high = bootstrap_mean_ci(values, n_bootstrap, rng)
    rng = np.random.default_rng(stable_seed(*seed_parts, "signflip"))
    p_sf = signflip_p_one_sided(values, n_perm, rng)
    p_sign = binom_one_sided_p_wins_gt_losses(wins, losses)
    return {
        "subjects": int(len(values)),
        "mean_improvement_stimulus_minus_model": safe_float(mean),
        "median_improvement_stimulus_minus_model": safe_float(np.median(values)) if len(values) else None,
        "ci95_low_mean_improvement": safe_float(ci_low),
        "ci95_high_mean_improvement": safe_float(ci_high),
        "signflip_p_one_sided_mean_gt_zero": safe_float(p_sf),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_margin": int(wins - losses),
        "sign_test_p_one_sided_wins_gt_losses": safe_float(p_sign),
    }


def add_pooled_lifts(cand: pd.DataFrame, ref_main: pd.DataFrame) -> pd.DataFrame:
    out = cand.merge(ref_main, on="target", how="left")
    if "lift_vs_stimulus_rmse" not in out.columns:
        out["lift_vs_stimulus_rmse"] = out["ref_pooled_rmse"] - out["rmse"]
    if "lift_vs_stimulus_residual_rmse" not in out.columns:
        residual_col = "residual_rmse" if "residual_rmse" in out.columns else "rmse"
        out["lift_vs_stimulus_residual_rmse"] = out["ref_pooled_residual_rmse"] - out[residual_col]
    return out


def build_paired_stats(
    main: pd.DataFrame,
    subject: pd.DataFrame,
    n_bootstrap: int,
    n_perm: int,
    seed: int,
):
    subject_col = find_subject_col(subject)
    residual_col = metric_col(subject, "residual_rmse", "rmse")
    ref_subject = get_reference_subject_rows(subject, subject_col)
    ref_main = get_reference_main_rows(main)

    main_with_lifts = add_pooled_lifts(main.copy(), ref_main)
    stat_rows = []
    failure_rows = []

    group_cols = ["target", "k_calibration", "model"]

    for keys, gsub in subject.groupby(group_cols, dropna=False):
        target, k_calibration, model = keys
        if int(k_calibration) == 0 and str(model) in {"stimulus_plus_fewshot_bias", "stimulus_plus_fewshot_bias_shrink4", "stimulus_only"}:
            continue

        gsub = gsub.copy()
        gsub_agg = gsub.groupby(["target", subject_col], as_index=False).agg(
            model_rmse=("rmse", "mean"),
            model_residual_rmse=(residual_col, "mean"),
        )

        merged = gsub_agg.merge(ref_subject, on=["target", subject_col], how="inner")
        if merged.empty:
            continue

        merged["rmse_improvement"] = merged["ref_rmse"] - merged["model_rmse"]
        merged["residual_rmse_improvement"] = merged["ref_residual_rmse"] - merged["model_residual_rmse"]

        main_match = main_with_lifts[
            main_with_lifts["target"].eq(target)
            & main_with_lifts["k_calibration"].eq(int(k_calibration))
            & main_with_lifts["model"].eq(model)
        ]
        if main_match.empty:
            pooled_lift = None
            pooled_residual_lift = None
            pooled_rmse = None
            pooled_residual_rmse = None
            pearson = None
            ccc = None
        else:
            mr = main_match.iloc[0]
            pooled_lift = safe_float(mr.get("lift_vs_stimulus_rmse"))
            pooled_residual_lift = safe_float(mr.get("lift_vs_stimulus_residual_rmse"))
            pooled_rmse = safe_float(mr.get("rmse"))
            pooled_residual_rmse = safe_float(mr.get("residual_rmse", mr.get("rmse")))
            pearson = safe_float(mr.get("pearson"))
            ccc = safe_float(mr.get("ccc"))

        for metric_name, values_col in [
            ("rmse", "rmse_improvement"),
            ("residual_rmse", "residual_rmse_improvement"),
        ]:
            vals = merged[values_col].to_numpy(dtype=float)
            stats = paired_stats_for_values(
                vals,
                n_bootstrap,
                n_perm,
                (seed, target, k_calibration, model, metric_name),
            )
            row = {
                "target": target,
                "k_calibration": int(k_calibration),
                "model": model,
                "metric": metric_name,
                "pooled_rmse": pooled_rmse,
                "pooled_residual_rmse": pooled_residual_rmse,
                "pooled_lift_vs_stimulus_rmse": pooled_lift,
                "pooled_lift_vs_stimulus_residual_rmse": pooled_residual_lift,
                "pearson": pearson,
                "ccc": ccc,
            }
            row.update(stats)
            row["passes_confirmatory_metric"] = bool(
                row["mean_improvement_stimulus_minus_model"] is not None
                and row["mean_improvement_stimulus_minus_model"] > 0
                and row["ci95_low_mean_improvement"] is not None
                and row["ci95_low_mean_improvement"] > 0
                and row["signflip_p_one_sided_mean_gt_zero"] is not None
                and row["signflip_p_one_sided_mean_gt_zero"] < 0.05
                and row["win_margin"] >= MIN_WIN_MARGIN
                and pooled_lift is not None
                and pooled_lift >= PRACTICAL_RMSE_LIFT
            )
            stat_rows.append(row)

        fail = merged.copy()
        fail["target"] = target
        fail["k_calibration"] = int(k_calibration)
        fail["model"] = model
        fail["rmse_worse_than_stimulus"] = fail["rmse_improvement"] < -EPS
        fail["residual_worse_than_stimulus"] = fail["residual_rmse_improvement"] < -EPS
        fail = fail.rename(columns={subject_col: "subject_id"})
        failure_rows.append(fail[[
            "target", "k_calibration", "model", "subject_id",
            "ref_rmse", "model_rmse", "rmse_improvement", "rmse_worse_than_stimulus",
            "ref_residual_rmse", "model_residual_rmse", "residual_rmse_improvement", "residual_worse_than_stimulus",
        ]])

    paired = pd.DataFrame(stat_rows)
    failures = pd.concat(failure_rows, ignore_index=True) if failure_rows else pd.DataFrame()

    return paired, failures, main_with_lifts, ref_main


def choose_best_candidates(main_with_lifts: pd.DataFrame) -> pd.DataFrame:
    cand = main_with_lifts[main_with_lifts["k_calibration"].gt(0)].copy()
    if cand.empty:
        return cand
    cand = cand.sort_values(
        ["target", "lift_vs_stimulus_rmse", "rmse"],
        ascending=[True, False, True],
    )
    return cand.groupby("target", as_index=False).head(1).reset_index(drop=True)


def build_verdict(best: pd.DataFrame, paired: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, b in best.iterrows():
        target = b["target"]
        model = b["model"]
        k = int(b["k_calibration"])
        sp = paired[
            paired["target"].eq(target)
            & paired["model"].eq(model)
            & paired["k_calibration"].eq(k)
        ]
        rmse_row = sp[sp["metric"].eq("rmse")]
        res_row = sp[sp["metric"].eq("residual_rmse")]

        rmse_pass = bool(not rmse_row.empty and bool(rmse_row.iloc[0]["passes_confirmatory_metric"]))
        res_pass = bool(not res_row.empty and bool(res_row.iloc[0]["passes_confirmatory_metric"]))

        pooled_lift = safe_float(b.get("lift_vs_stimulus_rmse"))
        mean_imp = safe_float(rmse_row.iloc[0]["mean_improvement_stimulus_minus_model"]) if not rmse_row.empty else None
        ci_low = safe_float(rmse_row.iloc[0]["ci95_low_mean_improvement"]) if not rmse_row.empty else None
        p_sf = safe_float(rmse_row.iloc[0]["signflip_p_one_sided_mean_gt_zero"]) if not rmse_row.empty else None
        wins = int(rmse_row.iloc[0]["wins"]) if not rmse_row.empty else 0
        losses = int(rmse_row.iloc[0]["losses"]) if not rmse_row.empty else 0
        win_margin = int(rmse_row.iloc[0]["win_margin"]) if not rmse_row.empty else 0

        if rmse_pass and res_pass:
            decision = "GO_CONFIRMED_FEWSHOT_SUBJECT_CALIBRATION"
            reason = "pooled lift, paired subject improvement, bootstrap CI, sign-flip test, and win margin all pass"
        elif pooled_lift is not None and pooled_lift > 0 and mean_imp is not None and mean_imp > 0:
            decision = "WEAK_GO_FEWSHOT_NEEDS_CAUTION"
            reasons = []
            if pooled_lift < PRACTICAL_RMSE_LIFT:
                reasons.append(f"pooled lift < {PRACTICAL_RMSE_LIFT}")
            if ci_low is None or ci_low <= 0:
                reasons.append("bootstrap CI lower bound is not > 0")
            if p_sf is None or p_sf >= 0.05:
                reasons.append("sign-flip p is not < 0.05")
            if win_margin < MIN_WIN_MARGIN:
                reasons.append(f"win margin < {MIN_WIN_MARGIN}")
            reason = "; ".join(reasons) if reasons else "positive but not all confirmatory criteria passed"
        elif pooled_lift is not None and pooled_lift > 0:
            decision = "WEAK_POOLED_ONLY_FEWSHOT"
            reason = "pooled lift is positive but paired subject-level evidence is not positive"
        else:
            decision = "NO_GO_FEWSHOT_CALIBRATION"
            reason = "few-shot calibration does not improve over stimulus-only under confirmatory criteria"

        rows.append({
            "target": target,
            "decision": decision,
            "best_model": model,
            "best_k_calibration": k,
            "best_rmse": safe_float(b.get("rmse")),
            "best_lift_vs_stimulus_rmse": pooled_lift,
            "mean_subject_rmse_improvement": mean_imp,
            "ci95_low_mean_subject_rmse_improvement": ci_low,
            "signflip_p_one_sided_mean_gt_zero": p_sf,
            "rmse_wins": wins,
            "rmse_losses": losses,
            "rmse_win_margin": win_margin,
            "reason": reason,
        })
    return pd.DataFrame(rows)


def build_calibration_curve(main_with_lifts: pd.DataFrame, paired: pd.DataFrame) -> pd.DataFrame:
    rmse_stats = paired[paired["metric"].eq("rmse")].copy()
    cols = [
        "target", "k_calibration", "model",
        "rmse", "residual_rmse", "lift_vs_stimulus_rmse", "lift_vs_stimulus_residual_rmse",
        "pearson", "ccc",
    ]
    main_cols = [c for c in cols if c in main_with_lifts.columns]
    curve = main_with_lifts[main_cols].copy()
    if not rmse_stats.empty:
        curve = curve.merge(
            rmse_stats[[
                "target", "k_calibration", "model",
                "subjects",
                "mean_improvement_stimulus_minus_model",
                "median_improvement_stimulus_minus_model",
                "ci95_low_mean_improvement",
                "ci95_high_mean_improvement",
                "signflip_p_one_sided_mean_gt_zero",
                "wins", "losses", "ties", "win_margin",
                "sign_test_p_one_sided_wins_gt_losses",
                "passes_confirmatory_metric",
            ]],
            on=["target", "k_calibration", "model"],
            how="left",
        )
    else:
        curve["subjects"] = np.nan
    return curve.sort_values(["target", "k_calibration", "model"]).reset_index(drop=True)


def main():
    args = parse_args()

    main_csv = ROCA / f"{args.fewshot_prefix}_main_metrics.csv"
    subject_csv = ROCA / f"{args.fewshot_prefix}_subject_metrics.csv"
    verdict_csv = ROCA / f"{args.fewshot_prefix}_verdict.csv"

    main_df = normalize_k(read_csv(main_csv, "few-shot main metrics"))
    subject_df = normalize_k(read_csv(subject_csv, "few-shot subject metrics"))
    input_verdict = read_csv(verdict_csv, "few-shot verdict") if verdict_csv.exists() else pd.DataFrame()

    required_main = {"target", "k_calibration", "model", "rmse"}
    required_subject = {"target", "k_calibration", "model", "rmse"}
    missing_main = sorted(required_main - set(main_df.columns))
    missing_subject = sorted(required_subject - set(subject_df.columns))
    if missing_main:
        raise KeyError(f"Main metrics missing columns: {missing_main}")
    if missing_subject:
        raise KeyError(f"Subject metrics missing columns: {missing_subject}")

    if "residual_rmse" not in main_df.columns:
        main_df["residual_rmse"] = main_df["rmse"]
    if "residual_rmse" not in subject_df.columns:
        subject_df["residual_rmse"] = subject_df["rmse"]

    paired, failures, main_with_lifts, ref_main = build_paired_stats(
        main_df,
        subject_df,
        args.n_bootstrap,
        args.n_permutations,
        args.seed,
    )
    best = choose_best_candidates(main_with_lifts)
    verdict = build_verdict(best, paired)
    curve = build_calibration_curve(main_with_lifts, paired)

    if not failures.empty:
        best_keys = set((r["target"], int(r["best_k_calibration"]), r["best_model"]) for _, r in verdict.iterrows())
        failures["is_best_candidate"] = [
            (r["target"], int(r["k_calibration"]), r["model"]) in best_keys for _, r in failures.iterrows()
        ]
        failures = failures.sort_values(
            ["is_best_candidate", "target", "rmse_improvement"],
            ascending=[False, True, True],
        )

    out_md = ROCA / f"{args.out_prefix}.md"
    out_json = ROCA / f"{args.out_prefix}.json"
    out_verdict = ROCA / f"{args.out_prefix}_verdict.csv"
    out_paired = ROCA / f"{args.out_prefix}_paired_subject_stats.csv"
    out_curve = ROCA / f"{args.out_prefix}_calibration_curve.csv"
    out_failures = ROCA / f"{args.out_prefix}_failure_subjects.csv"

    verdict.to_csv(out_verdict, index=False)
    paired.to_csv(out_paired, index=False)
    curve.to_csv(out_curve, index=False)
    failures.to_csv(out_failures, index=False)

    report = {
        "step": "05ad",
        "purpose": "Confirm few-shot subject calibration with paired subject-level statistics.",
        "inputs": {
            "fewshot_prefix": args.fewshot_prefix,
            "main_metrics": str(main_csv),
            "subject_metrics": str(subject_csv),
            "verdict": str(verdict_csv),
        },
        "parameters": {
            "n_bootstrap": args.n_bootstrap,
            "n_permutations": args.n_permutations,
            "seed": args.seed,
            "practical_rmse_lift": PRACTICAL_RMSE_LIFT,
            "min_win_margin": MIN_WIN_MARGIN,
        },
        "reference_main": ref_main.to_dict(orient="records"),
        "input_fewshot_verdict": input_verdict.to_dict(orient="records"),
        "verdict": verdict.to_dict(orient="records"),
        "top_paired_rows": paired.sort_values(
            ["target", "pooled_lift_vs_stimulus_rmse", "metric"],
            ascending=[True, False, True],
        ).head(30).to_dict(orient="records") if not paired.empty else [],
        "outputs": {
            "md": str(out_md),
            "json": str(out_json),
            "verdict": str(out_verdict),
            "paired_subject_stats": str(out_paired),
            "calibration_curve": str(out_curve),
            "failure_subjects": str(out_failures),
        },
    }
    out_json.write_text(json.dumps(clean_json(report), indent=2, ensure_ascii=False), encoding="utf-8")

    paired_show = paired.sort_values(
        ["target", "pooled_lift_vs_stimulus_rmse", "metric"],
        ascending=[True, False, True],
    ).copy() if not paired.empty else paired

    curve_show = curve.sort_values(
        ["target", "lift_vs_stimulus_rmse", "k_calibration"],
        ascending=[True, False, True],
    ).copy() if not curve.empty else curve

    failure_show = failures[failures["is_best_candidate"].eq(True)].copy() if not failures.empty and "is_best_candidate" in failures.columns else failures
    if not failure_show.empty:
        failure_show = failure_show.sort_values(["target", "rmse_improvement"], ascending=[True, True])

    lines = []
    lines.append("# I-DARE Few-shot Calibration Confirmatory Statistics\n")
    lines.append(
        "This report validates whether the few-shot subject-calibration result from 05aa is reliable at subject level, not only in pooled repeated predictions.\n"
    )
    lines.append("Positive improvement means `stimulus_only RMSE - fewshot_model RMSE`; positive is good for few-shot calibration.\n")
    lines.append("## Decision rule\n")
    lines.append(
        f"`GO_CONFIRMED_FEWSHOT_SUBJECT_CALIBRATION` requires pooled RMSE lift >= {PRACTICAL_RMSE_LIFT}, "
        "positive paired mean subject improvement, bootstrap CI lower bound > 0, one-sided sign-flip p < 0.05, "
        f"and subject win margin >= {MIN_WIN_MARGIN}.\n"
    )

    lines.append("## Verdict\n")
    lines.append(md_table(verdict, [
        "target", "decision", "best_model", "best_k_calibration",
        "best_rmse", "best_lift_vs_stimulus_rmse",
        "mean_subject_rmse_improvement", "ci95_low_mean_subject_rmse_improvement",
        "signflip_p_one_sided_mean_gt_zero", "rmse_wins", "rmse_losses", "rmse_win_margin", "reason",
    ]))

    lines.append("\n## Calibration curve summary\n")
    lines.append(md_table(curve_show, [
        "target", "k_calibration", "model", "rmse", "lift_vs_stimulus_rmse",
        "mean_improvement_stimulus_minus_model", "ci95_low_mean_improvement",
        "signflip_p_one_sided_mean_gt_zero", "wins", "losses", "win_margin",
        "passes_confirmatory_metric",
    ], max_rows=40))

    lines.append("\n## Paired subject-level statistics\n")
    lines.append(md_table(paired_show, [
        "target", "k_calibration", "model", "metric", "subjects",
        "mean_improvement_stimulus_minus_model", "median_improvement_stimulus_minus_model",
        "ci95_low_mean_improvement", "ci95_high_mean_improvement",
        "signflip_p_one_sided_mean_gt_zero", "wins", "losses", "ties", "win_margin",
        "sign_test_p_one_sided_wins_gt_losses", "pooled_lift_vs_stimulus_rmse",
        "passes_confirmatory_metric",
    ], max_rows=60))

    lines.append("\n## Worst failure subjects for the selected candidates\n")
    lines.append(md_table(failure_show, [
        "target", "k_calibration", "model", "subject_id",
        "ref_rmse", "model_rmse", "rmse_improvement", "rmse_worse_than_stimulus",
        "ref_residual_rmse", "model_residual_rmse", "residual_rmse_improvement",
    ], max_rows=80))

    lines.append("\n## Interpretation\n")
    lines.append("- Arousal should only stay in the GO path if the subject-paired tests confirm the 05aa win margin and CI evidence.\n")
    lines.append("- Valence should remain weak/unstable unless paired subject evidence turns positive; a tiny pooled lift alone is not enough.\n")
    lines.append("- Any future calibration model family in 05ae must beat the locked few-shot baseline confirmed here, not merely beat stimulus-only.\n")

    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05ad completed.")
    for p in [out_md, out_json, out_verdict, out_paired, out_curve, out_failures]:
        print(f"wrote: {p}")

    print("\nVerdict:")
    print(verdict.to_string(index=False))

    print("\nCalibration curve top rows:")
    show_cols = [
        "target", "k_calibration", "model", "rmse", "lift_vs_stimulus_rmse",
        "mean_improvement_stimulus_minus_model", "ci95_low_mean_improvement",
        "signflip_p_one_sided_mean_gt_zero", "wins", "losses", "win_margin",
        "passes_confirmatory_metric",
    ]
    print(curve_show[[c for c in show_cols if c in curve_show.columns]].head(30).to_string(index=False))


if __name__ == "__main__":
    main()
