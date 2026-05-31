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

DEFAULT_PRED_CSV = ROCA / "idare_residual_physiology_feature_audit_current_predictions.csv"
DEFAULT_05AJ_DECISION_CSV = ROCA / "idare_high_disagreement_direct_deviation_challenge_current_decision_table.csv"
DEFAULT_OUT_PREFIX = "idare_high_disagreement_direct_deviation_confirmatory_stats_current"

PRACTICAL_RMSE_LIFT = 0.02
MIN_WIN_MARGIN = 3
MIN_RESIDUAL_PEARSON = 0.10


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Confirmatory paired-subject statistics for the 05aj high-disagreement "
            "direct-deviation physiology signal."
        )
    )
    p.add_argument("--predictions-csv", type=Path, default=DEFAULT_PRED_CSV)
    p.add_argument("--decision-csv", type=Path, default=DEFAULT_05AJ_DECISION_CSV)
    p.add_argument("--out-prefix", type=str, default=DEFAULT_OUT_PREFIX)
    p.add_argument("--q-values", type=str, default="0.50,0.75,0.90")
    p.add_argument("--n-bootstrap", type=int, default=20000)
    p.add_argument("--n-signflips", type=int, default=20000)
    p.add_argument("--n-permutations", type=int, default=20000)
    p.add_argument("--seed", type=int, default=20260530)
    p.add_argument(
        "--primary-target",
        type=str,
        default="arousal",
        help="Target whose 05aj exploratory GO is treated as the primary confirmatory candidate.",
    )
    p.add_argument(
        "--primary-quantile",
        type=float,
        default=0.75,
        help="High-disagreement quantile for the primary confirmatory candidate.",
    )
    return p.parse_args()


def stable_seed(*parts: Any) -> int:
    payload = "|".join(str(p) for p in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "little") % (2**32)


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
    if isinstance(x, tuple):
        return [clean_json(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        v = float(x)
        return v if math.isfinite(v) else None
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if pd.isna(x):
        return None
    return x


def md_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df is None or df.empty:
        return "_No rows._\n"
    x = df.copy()
    if max_rows is not None:
        x = x.head(max_rows).copy()

    def fmt(v: Any) -> str:
        if pd.isna(v):
            return ""
        if isinstance(v, float):
            if abs(v) >= 10000 or (abs(v) > 0 and abs(v) < 1e-4):
                return f"{v:.6e}"
            return f"{v:.6f}"
        return str(v)

    cols = list(x.columns)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in x.iterrows():
        vals = [fmt(row[c]).replace("|", "\\|") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def find_col(df: pd.DataFrame, candidates: list[str], required: bool = True) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    if required:
        raise SystemExit(
            f"Could not find any of columns {candidates}. Available columns: {list(df.columns)}"
        )
    return None


def normalize_predictions(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"Missing predictions CSV: {path}")

    df = pd.read_csv(path)
    subject_col = find_col(df, ["test_subject", "subject_id", "subject", "participant_id", "participant", "subj"])
    stimulus_col = find_col(df, ["stimulus_id", "stimulus", "video_id", "clip_id"])
    target_col = find_col(df, ["target"])
    block_col = find_col(df, ["feature_block", "block"], required=False)
    model_col = find_col(df, ["model"])
    y_col = find_col(df, ["y_true_score", "y_true", "true_score", "score"])
    stim_mean_col = find_col(df, ["train_stimulus_mean", "stimulus_mean", "stimulus_only_pred"])
    true_dev_col = find_col(df, ["true_deviation_from_train_stimulus_mean", "true_deviation", "true_dev"], required=False)
    pred_dev_col = find_col(df, ["y_pred_deviation", "pred_deviation", "pred_dev"], required=False)
    pred_score_col = find_col(df, ["y_pred_score", "y_pred", "pred_score"], required=False)

    out = pd.DataFrame()
    out["subject_id"] = df[subject_col].astype(str)
    out["stimulus_id"] = df[stimulus_col].astype(str)
    out["target"] = df[target_col].astype(str)
    out["feature_block"] = df[block_col].astype(str) if block_col else ""
    out["model"] = df[model_col].astype(str)
    out["y_true"] = pd.to_numeric(df[y_col], errors="coerce")
    out["stimulus_mean"] = pd.to_numeric(df[stim_mean_col], errors="coerce")

    if true_dev_col:
        out["true_dev"] = pd.to_numeric(df[true_dev_col], errors="coerce")
    else:
        out["true_dev"] = out["y_true"] - out["stimulus_mean"]

    if pred_dev_col:
        out["pred_dev"] = pd.to_numeric(df[pred_dev_col], errors="coerce")
    elif pred_score_col:
        out["pred_dev"] = pd.to_numeric(df[pred_score_col], errors="coerce") - out["stimulus_mean"]
    else:
        raise SystemExit("Could not find predicted deviation or predicted score column.")

    out["pred_score"] = out["stimulus_mean"] + out["pred_dev"]
    out = out.replace([np.inf, -np.inf], np.nan)
    out = out.dropna(subset=["y_true", "stimulus_mean", "true_dev", "pred_dev"])
    return out


def load_candidates(decision_csv: Path, primary_target: str, primary_quantile: float) -> list[dict[str, Any]]:
    if decision_csv.exists():
        d = pd.read_csv(decision_csv)
        needed = ["target", "quantile", "best_block", "best_model"]
        missing = [c for c in needed if c not in d.columns]
        if missing:
            raise SystemExit(f"Decision CSV is missing columns {missing}: {decision_csv}")

        rows: list[dict[str, Any]] = []
        # Put primary candidate first.
        d["_primary_order"] = d.apply(
            lambda r: 0
            if str(r["target"]) == primary_target and abs(float(r["quantile"]) - primary_quantile) < 1e-9
            else 1,
            axis=1,
        )
        d = d.sort_values(["_primary_order", "target"]).drop(columns=["_primary_order"])
        for _, r in d.iterrows():
            rows.append(
                {
                    "target": str(r["target"]),
                    "quantile": float(r["quantile"]),
                    "block": str(r["best_block"]),
                    "model": str(r["best_model"]),
                    "source": "05aj_decision_table",
                }
            )
        return rows

    return [
        {
            "target": primary_target,
            "quantile": primary_quantile,
            "block": "eeg_bandpower",
            "model": "physio_eeg_bandpower_ridge",
            "source": "hardcoded_primary_default",
        }
    ]


def pearsonr_np(a: np.ndarray, b: np.ndarray) -> float | None:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    a = a[mask]
    b = b[mask]
    if len(a) < 3:
        return None
    if float(np.std(a)) == 0.0 or float(np.std(b)) == 0.0:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def rmse_np(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return float(np.sqrt(np.mean((a - b) ** 2)))


def subject_rmse_arrays(y: np.ndarray, pred: np.ndarray, subject_codes: np.ndarray, n_subjects: int) -> np.ndarray:
    err2 = (y - pred) ** 2
    sums = np.bincount(subject_codes, weights=err2, minlength=n_subjects)
    counts = np.bincount(subject_codes, minlength=n_subjects)
    out = np.full(n_subjects, np.nan, dtype=float)
    ok = counts > 0
    out[ok] = np.sqrt(sums[ok] / counts[ok])
    return out


def bootstrap_ci_mean(values: np.ndarray, n_bootstrap: int, seed: int) -> tuple[float, float]:
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return math.nan, math.nan
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), size=(n_bootstrap, len(v)))
    means = v[idx].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def signflip_p_mean_gt_zero(values: np.ndarray, n_signflips: int, seed: int) -> float:
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return math.nan
    obs = float(np.mean(v))
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_signflips, len(v)))
    null = (signs * v).mean(axis=1)
    return float((np.sum(null >= obs) + 1) / (n_signflips + 1))


def binomial_sign_test_p_wins_gt_losses(wins: int, losses: int) -> float | None:
    n = int(wins + losses)
    if n <= 0:
        return None
    # One-sided P[X >= wins], X ~ Binomial(n, 0.5)
    total = 0
    for k in range(int(wins), n + 1):
        total += math.comb(n, k)
    return float(total / (2 ** n))


def permutation_p_alignment(
    y: np.ndarray,
    pred_dev: np.ndarray,
    subject_codes: np.ndarray,
    baseline_subject_rmse: np.ndarray,
    observed_mean_improvement: float,
    n_permutations: int,
    seed: int,
) -> float:
    y = np.asarray(y, dtype=float)
    pred_dev = np.asarray(pred_dev, dtype=float)
    subject_codes = np.asarray(subject_codes, dtype=int)
    n_subjects = len(baseline_subject_rmse)
    rng = np.random.default_rng(seed)

    null = np.empty(n_permutations, dtype=float)
    for i in range(n_permutations):
        shuffled = pred_dev[rng.permutation(len(pred_dev))]
        model_rmse = subject_rmse_arrays(y, shuffled, subject_codes, n_subjects)
        imp = baseline_subject_rmse - model_rmse
        null[i] = np.nanmean(imp)

    return float((np.sum(null >= observed_mean_improvement) + 1) / (n_permutations + 1))


def evaluate_candidate(
    pred: pd.DataFrame,
    target: str,
    quantile: float,
    block: str,
    model: str,
    n_bootstrap: int,
    n_signflips: int,
    n_permutations: int,
    seed: int,
    source: str,
) -> tuple[dict[str, Any], pd.DataFrame]:
    target_df = pred[pred["target"] == target].copy()
    if target_df.empty:
        raise SystemExit(f"No predictions for target={target}")

    unique_truth = target_df.drop_duplicates(["subject_id", "stimulus_id", "target"]).copy()
    threshold = float(unique_truth["true_dev"].abs().quantile(quantile))

    model_df = target_df[
        (target_df["feature_block"] == block)
        & (target_df["model"] == model)
        & (target_df["true_dev"].abs() >= threshold)
    ].copy()

    if model_df.empty:
        raise SystemExit(
            f"No rows for target={target}, quantile={quantile}, block={block}, model={model}."
        )

    y = model_df["true_dev"].to_numpy(dtype=float)
    pred_dev = model_df["pred_dev"].to_numpy(dtype=float)
    baseline_pred = np.zeros_like(y)

    subjects = sorted(model_df["subject_id"].unique())
    subject_to_code = {s: i for i, s in enumerate(subjects)}
    subject_codes = model_df["subject_id"].map(subject_to_code).to_numpy(dtype=int)
    n_subjects = len(subjects)

    baseline_subject_rmse = subject_rmse_arrays(y, baseline_pred, subject_codes, n_subjects)
    model_subject_rmse = subject_rmse_arrays(y, pred_dev, subject_codes, n_subjects)
    improvements = baseline_subject_rmse - model_subject_rmse
    deltas = model_subject_rmse - baseline_subject_rmse

    pooled_baseline_rmse = rmse_np(y, baseline_pred)
    pooled_model_rmse = rmse_np(y, pred_dev)
    pooled_lift = pooled_baseline_rmse - pooled_model_rmse

    wins = int(np.sum(improvements > 0))
    losses = int(np.sum(improvements < 0))
    ties = int(np.sum(improvements == 0))
    win_margin = wins - losses

    mean_imp = float(np.nanmean(improvements))
    median_imp = float(np.nanmedian(improvements))
    ci_low, ci_high = bootstrap_ci_mean(
        improvements,
        n_bootstrap,
        stable_seed(seed, target, quantile, block, model, "bootstrap"),
    )
    signflip_p = signflip_p_mean_gt_zero(
        improvements,
        n_signflips,
        stable_seed(seed, target, quantile, block, model, "signflip"),
    )
    sign_test_p = binomial_sign_test_p_wins_gt_losses(wins, losses)

    perm_p = permutation_p_alignment(
        y=y,
        pred_dev=pred_dev,
        subject_codes=subject_codes,
        baseline_subject_rmse=baseline_subject_rmse,
        observed_mean_improvement=mean_imp,
        n_permutations=n_permutations,
        seed=stable_seed(seed, target, quantile, block, model, "permutation"),
    )

    residual_pearson = pearsonr_np(y, pred_dev)
    sign_acc = float(np.mean(np.sign(y) == np.sign(pred_dev)))

    passes = (
        pooled_lift > PRACTICAL_RMSE_LIFT
        and mean_imp > 0
        and ci_low > 0
        and signflip_p < 0.05
        and perm_p < 0.05
        and win_margin >= MIN_WIN_MARGIN
        and (residual_pearson is not None and residual_pearson > MIN_RESIDUAL_PEARSON)
    )

    reasons: list[str] = []
    if pooled_lift <= PRACTICAL_RMSE_LIFT:
        reasons.append(f"pooled residual RMSE lift <= {PRACTICAL_RMSE_LIFT}")
    if mean_imp <= 0:
        reasons.append("mean subject improvement <= 0")
    if not (ci_low > 0):
        reasons.append("bootstrap CI lower bound is not > 0")
    if not (signflip_p < 0.05):
        reasons.append("sign-flip p is not < 0.05")
    if not (perm_p < 0.05):
        reasons.append("permutation p is not < 0.05")
    if win_margin < MIN_WIN_MARGIN:
        reasons.append(f"win margin < {MIN_WIN_MARGIN}")
    if residual_pearson is None or residual_pearson <= MIN_RESIDUAL_PEARSON:
        reasons.append(f"residual Pearson <= {MIN_RESIDUAL_PEARSON}")

    if passes:
        decision = "GO_CONFIRMED_HIGH_DISAGREEMENT_PHYSIOLOGY"
        reason = "candidate passes pooled, paired subject-level, sign-flip, permutation, and correlation gates"
    else:
        decision = "WEAK_OR_NO_GO_HIGH_DISAGREEMENT_PHYSIOLOGY"
        reason = "; ".join(reasons)

    subject_rows = []
    for subj, base_rmse, mod_rmse, imp, delta in zip(
        subjects, baseline_subject_rmse, model_subject_rmse, improvements, deltas
    ):
        subject_rows.append(
            {
                "target": target,
                "quantile": quantile,
                "feature_block": block,
                "model": model,
                "subject_id": subj,
                "baseline_residual_rmse": base_rmse,
                "model_residual_rmse": mod_rmse,
                "improvement_baseline_minus_model": imp,
                "delta_rmse_model_minus_baseline": delta,
            }
        )

    row = {
        "target": target,
        "quantile": quantile,
        "candidate_source": source,
        "feature_block": block,
        "model": model,
        "n": int(len(model_df)),
        "subjects": int(n_subjects),
        "abs_residual_threshold": threshold,
        "baseline_residual_rmse": pooled_baseline_rmse,
        "model_residual_rmse": pooled_model_rmse,
        "pooled_lift_vs_zero_residual_rmse": pooled_lift,
        "residual_pearson": residual_pearson,
        "residual_sign_acc": sign_acc,
        "mean_subject_improvement_baseline_minus_model": mean_imp,
        "median_subject_improvement_baseline_minus_model": median_imp,
        "ci95_low_mean_subject_improvement": ci_low,
        "ci95_high_mean_subject_improvement": ci_high,
        "signflip_p_one_sided_mean_gt_zero": signflip_p,
        "permutation_p_alignment": perm_p,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_margin": win_margin,
        "sign_test_p_one_sided_wins_gt_losses": sign_test_p,
        "passes_confirmatory_gate": bool(passes),
        "decision": decision,
        "reason": reason,
    }
    return row, pd.DataFrame(subject_rows)


def build_report(
    out_md: Path,
    verdict: pd.DataFrame,
    sensitivity: pd.DataFrame,
    permutation: pd.DataFrame,
    failures: pd.DataFrame,
    args: argparse.Namespace,
) -> None:
    lines: list[str] = []
    lines.append("# I-DARE High-Disagreement Direct-Deviation Confirmatory Statistics\n")
    lines.append(
        "This report locks the exploratory 05aj high-disagreement physiology signal and tests it "
        "with paired subject-level bootstrap, sign-flip, sign-test, and residual-prediction permutation checks.\n"
    )
    lines.append("Positive improvement means `zero residual baseline RMSE - physiology residual-model RMSE`; positive is good for physiology.\n")

    lines.append("## Confirmatory verdict\n")
    show_cols = [
        "target",
        "decision",
        "quantile",
        "feature_block",
        "model",
        "n",
        "subjects",
        "baseline_residual_rmse",
        "model_residual_rmse",
        "pooled_lift_vs_zero_residual_rmse",
        "residual_pearson",
        "residual_sign_acc",
        "mean_subject_improvement_baseline_minus_model",
        "ci95_low_mean_subject_improvement",
        "signflip_p_one_sided_mean_gt_zero",
        "permutation_p_alignment",
        "wins",
        "losses",
        "win_margin",
        "passes_confirmatory_gate",
        "reason",
    ]
    lines.append(md_table(verdict[show_cols]))

    lines.append("\n## Sensitivity curve for locked candidates\n")
    sens_cols = [
        "target",
        "quantile",
        "feature_block",
        "model",
        "n",
        "baseline_residual_rmse",
        "model_residual_rmse",
        "pooled_lift_vs_zero_residual_rmse",
        "residual_pearson",
        "residual_sign_acc",
        "ci95_low_mean_subject_improvement",
        "signflip_p_one_sided_mean_gt_zero",
        "permutation_p_alignment",
        "wins",
        "losses",
        "win_margin",
        "passes_confirmatory_gate",
    ]
    lines.append(md_table(sensitivity[sens_cols], max_rows=30))

    lines.append("\n## Permutation summary\n")
    lines.append(md_table(permutation, max_rows=30))

    lines.append("\n## Worst failure subjects for primary candidate\n")
    lines.append(md_table(failures, max_rows=30))

    lines.append("\n## Interpretation\n")
    lines.append(
        "- If arousal/q75/eeg_bandpower passes here, the claim is still scoped: EEG bandpower contains "
        "a confirmed high-disagreement arousal residual signal under the current fixed-feature audit.\n"
    )
    lines.append(
        "- This does not yet mean EEG beats the locked personalized kernel baseline; it means the residual "
        "signal is real enough to justify representation-learning or physiology-assisted calibration follow-up.\n"
    )
    lines.append(
        "- If it fails, 05aj should be treated as exploratory only and not used as a scientific claim.\n"
    )
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    q_values = [float(x.strip()) for x in args.q_values.split(",") if x.strip()]

    out_prefix = args.out_prefix
    out_md = ROCA / f"{out_prefix}.md"
    out_json = ROCA / f"{out_prefix}.json"
    out_verdict = ROCA / f"{out_prefix}_verdict.csv"
    out_sensitivity = ROCA / f"{out_prefix}_sensitivity_curve.csv"
    out_subject = ROCA / f"{out_prefix}_paired_subject_stats.csv"
    out_perm = ROCA / f"{out_prefix}_permutation_stats.csv"
    out_fail = ROCA / f"{out_prefix}_failure_subjects.csv"

    pred = normalize_predictions(args.predictions_csv)
    candidates = load_candidates(args.decision_csv, args.primary_target, args.primary_quantile)

    # Confirm only the 05aj-selected candidate rows, with primary first.
    verdict_rows: list[dict[str, Any]] = []
    subject_frames: list[pd.DataFrame] = []
    sensitivity_rows: list[dict[str, Any]] = []

    for cand in candidates:
        row, subj = evaluate_candidate(
            pred=pred,
            target=cand["target"],
            quantile=float(cand["quantile"]),
            block=cand["block"],
            model=cand["model"],
            n_bootstrap=args.n_bootstrap,
            n_signflips=args.n_signflips,
            n_permutations=args.n_permutations,
            seed=args.seed,
            source=cand.get("source", "candidate"),
        )
        verdict_rows.append(row)
        subject_frames.append(subj)

        for q in q_values:
            srow, _ = evaluate_candidate(
                pred=pred,
                target=cand["target"],
                quantile=q,
                block=cand["block"],
                model=cand["model"],
                n_bootstrap=args.n_bootstrap,
                n_signflips=args.n_signflips,
                n_permutations=args.n_permutations,
                seed=args.seed,
                source=f"sensitivity_for_{cand.get('source', 'candidate')}",
            )
            sensitivity_rows.append(srow)

    verdict = pd.DataFrame(verdict_rows)
    sensitivity = pd.DataFrame(sensitivity_rows)
    subject_stats = pd.concat(subject_frames, ignore_index=True) if subject_frames else pd.DataFrame()

    # Primary failure subjects: first verdict row is primary candidate.
    primary = verdict.iloc[0]
    failures = subject_stats[
        (subject_stats["target"] == primary["target"])
        & (subject_stats["quantile"] == primary["quantile"])
        & (subject_stats["feature_block"] == primary["feature_block"])
        & (subject_stats["model"] == primary["model"])
    ].copy()
    failures = failures.sort_values("delta_rmse_model_minus_baseline", ascending=False)

    perm_cols = [
        "target",
        "quantile",
        "feature_block",
        "model",
        "permutation_p_alignment",
        "signflip_p_one_sided_mean_gt_zero",
        "sign_test_p_one_sided_wins_gt_losses",
        "pooled_lift_vs_zero_residual_rmse",
        "mean_subject_improvement_baseline_minus_model",
        "ci95_low_mean_subject_improvement",
        "wins",
        "losses",
        "win_margin",
        "passes_confirmatory_gate",
    ]
    permutation = sensitivity[perm_cols].copy()

    verdict.to_csv(out_verdict, index=False)
    sensitivity.to_csv(out_sensitivity, index=False)
    subject_stats.to_csv(out_subject, index=False)
    permutation.to_csv(out_perm, index=False)
    failures.to_csv(out_fail, index=False)

    payload = {
        "inputs": {
            "predictions_csv": str(args.predictions_csv),
            "decision_csv": str(args.decision_csv),
            "q_values": q_values,
            "n_bootstrap": args.n_bootstrap,
            "n_signflips": args.n_signflips,
            "n_permutations": args.n_permutations,
            "seed": args.seed,
        },
        "candidates": candidates,
        "verdict": clean_json(verdict.to_dict(orient="records")),
        "sensitivity_curve": clean_json(sensitivity.to_dict(orient="records")),
        "permutation_stats": clean_json(permutation.to_dict(orient="records")),
        "failure_subjects_preview": clean_json(failures.head(50).to_dict(orient="records")),
    }
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    build_report(out_md, verdict, sensitivity, permutation, failures, args)

    print("ROCA step 05ajb completed.")
    for p in [out_md, out_json, out_verdict, out_sensitivity, out_subject, out_perm, out_fail]:
        print(f"wrote: {p}")

    print("\nConfirmatory verdict:")
    print(
        verdict[
            [
                "target",
                "decision",
                "quantile",
                "feature_block",
                "model",
                "pooled_lift_vs_zero_residual_rmse",
                "residual_pearson",
                "ci95_low_mean_subject_improvement",
                "signflip_p_one_sided_mean_gt_zero",
                "permutation_p_alignment",
                "wins",
                "losses",
                "win_margin",
                "passes_confirmatory_gate",
                "reason",
            ]
        ].to_string(index=False)
    )

    print("\nSensitivity top rows:")
    print(
        sensitivity.sort_values(
            ["target", "pooled_lift_vs_zero_residual_rmse"],
            ascending=[True, False],
        )[
            [
                "target",
                "quantile",
                "feature_block",
                "model",
                "n",
                "pooled_lift_vs_zero_residual_rmse",
                "residual_pearson",
                "ci95_low_mean_subject_improvement",
                "permutation_p_alignment",
                "wins",
                "losses",
                "win_margin",
                "passes_confirmatory_gate",
            ]
        ].head(20).to_string(index=False)
    )


if __name__ == "__main__":
    main()
