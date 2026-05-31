#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROCA = ROOT / "docs" / "roca"

OUT_PREFIX = "idare_residual_physiology_synthesis_current"

VARIANCE_CSV = ROCA / "idare_label_variance_decomposition_current.csv"
PRIOR_MAIN_CSV = ROCA / "prior_baselines_no_global_current_main_metrics.csv"
PRIOR_BINARY_CSV = ROCA / "prior_baselines_no_global_current_binary_metrics.csv"

AUDIT_PREFIX = "idare_residual_physiology_feature_audit_current"
AUDIT_MAIN_CSV = ROCA / f"{AUDIT_PREFIX}_main_metrics.csv"
AUDIT_BINARY_CSV = ROCA / f"{AUDIT_PREFIX}_binary_metrics.csv"
AUDIT_WINLOSS_CSV = ROCA / f"{AUDIT_PREFIX}_subject_winloss.csv"
AUDIT_BEST_CSV = ROCA / f"{AUDIT_PREFIX}_best_ranking.csv"
AUDIT_TOP3_CSV = ROCA / f"{AUDIT_PREFIX}_top3_summary.csv"

OUT_MD = ROCA / f"{OUT_PREFIX}.md"
OUT_JSON = ROCA / f"{OUT_PREFIX}.json"
OUT_GO_NOGO = ROCA / f"{OUT_PREFIX}_go_nogo.csv"
OUT_TOP_MODELS = ROCA / f"{OUT_PREFIX}_top_models.csv"
OUT_PRIOR_SUMMARY = ROCA / f"{OUT_PREFIX}_prior_summary.csv"


PRACTICAL_RMSE_LIFT = 0.02
MIN_WIN_MARGIN = 3


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


def read_csv_required(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def read_csv_optional(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def pct(x):
    if x is None or pd.isna(x):
        return ""
    return f"{100.0 * float(x):.2f}%"


def num(x, nd=4):
    if x is None or pd.isna(x):
        return ""
    return f"{float(x):.{nd}f}"


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "_No rows._\n"

    use_cols = [c for c in cols if c in df.columns]
    rows = []
    rows.append("| " + " | ".join(use_cols) + " |")
    rows.append("| " + " | ".join(["---"] * len(use_cols)) + " |")

    for _, r in df[use_cols].iterrows():
        vals = []
        for c in use_cols:
            v = r[c]
            if pd.isna(v):
                vals.append("")
            elif isinstance(v, float):
                vals.append(f"{v:.6f}")
            else:
                vals.append(str(v).replace("|", "\\|").replace("\n", " "))
        rows.append("| " + " | ".join(vals) + " |")

    return "\n".join(rows) + "\n"


def build_prior_summary(prior_main: pd.DataFrame, prior_binary: pd.DataFrame) -> pd.DataFrame:
    rows = []

    pm = prior_main[prior_main["dataset"].eq("I-DARE")].copy()

    for _, r in pm.iterrows():
        rows.append({
            "dataset": r["dataset"],
            "target": r["target"],
            "protocol": r["protocol"],
            "model": r["model"],
            "n": int(r["n"]),
            "rmse": safe_float(r["rmse"]),
            "mae": safe_float(r["mae"]),
            "pearson": safe_float(r["pearson"]),
            "spearman": safe_float(r["spearman"]),
            "ccc": safe_float(r["ccc"]),
            "y_pred_std": safe_float(r.get("y_pred_std")),
            "residual_std": safe_float(r.get("residual_std")),
        })

    out = pd.DataFrame(rows)

    if not prior_binary.empty:
        pb = prior_binary[
            prior_binary["dataset"].eq("I-DARE")
            & prior_binary["label_policy"].isin(["midpoint_as_low", "midpoint_as_high", "discard_midpoint"])
        ].copy()

        # Keep the main score-threshold rows if binary_source exists.
        if "binary_source" in pb.columns:
            pb = pb[pb["binary_source"].eq("score_threshold")].copy()

        bin_keep = [
            "dataset", "target", "protocol", "model", "label_policy",
            "accuracy", "balanced_accuracy", "macro_f1", "auroc",
        ]
        pb = pb[[c for c in bin_keep if c in pb.columns]].copy()

        out = out.merge(
            pb,
            on=["dataset", "target", "protocol", "model"],
            how="left",
        )

    return out


def build_top_models(audit_main: pd.DataFrame, winloss: pd.DataFrame) -> pd.DataFrame:
    phys = audit_main[audit_main["model"].ne("stimulus_only")].copy()

    if phys.empty:
        return phys

    phys = phys.sort_values(
        ["target", "lift_vs_stimulus_rmse", "rmse"],
        ascending=[True, False, True],
    )

    merge_cols = [
        "target", "model", "rmse_wins", "rmse_losses",
        "mean_delta_rmse_model_minus_stimulus",
        "median_delta_rmse_model_minus_stimulus",
        "worst_regression_delta_rmse",
        "best_gain_delta_rmse",
    ]

    if not winloss.empty:
        phys = phys.merge(
            winloss[[c for c in merge_cols if c in winloss.columns]],
            on=["target", "model"],
            how="left",
        )

    return phys


def build_go_nogo(top_models: pd.DataFrame, variance: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for target, g in top_models.groupby("target"):
        g = g.sort_values(["lift_vs_stimulus_rmse", "rmse"], ascending=[False, True])
        best = g.iloc[0]

        lift_rmse = safe_float(best.get("lift_vs_stimulus_rmse"))
        lift_dev_rmse = safe_float(best.get("lift_vs_stimulus_dev_rmse"))
        rmse_wins = safe_float(best.get("rmse_wins"))
        rmse_losses = safe_float(best.get("rmse_losses"))

        win_margin = None
        if rmse_wins is not None and rmse_losses is not None:
            win_margin = rmse_wins - rmse_losses

        vrow = variance[variance["target"].eq(target)]
        if not vrow.empty:
            vrow = vrow.iloc[0]
            r2_stim = safe_float(vrow.get("r2_stimulus_in_sample"))
            r2_subject = safe_float(vrow.get("r2_subject_in_sample"))
            residual_ratio = safe_float(vrow.get("residual_std_ratio_after_loso_stimulus"))
            loso_stim_rmse = safe_float(vrow.get("loso_stimulus_rmse"))
        else:
            r2_stim = r2_subject = residual_ratio = loso_stim_rmse = None

        reasons = []

        if lift_rmse is None or lift_rmse <= 0:
            reasons.append("best physiologic block does not beat stimulus-only RMSE")
        elif lift_rmse < PRACTICAL_RMSE_LIFT:
            reasons.append(f"RMSE lift is positive but below practical threshold {PRACTICAL_RMSE_LIFT}")

        if lift_dev_rmse is None or lift_dev_rmse <= 0:
            reasons.append("residual/dev RMSE does not improve over stimulus-only")

        if win_margin is None or win_margin <= MIN_WIN_MARGIN:
            reasons.append(f"subject-level win margin is not meaningfully positive; required > {MIN_WIN_MARGIN}")

        if reasons:
            decision = "NO_GO_CURRENT_FEATURE_SET"
        else:
            decision = "GO_WEAK_RESIDUAL_SIGNAL"

        rows.append({
            "target": target,
            "decision": decision,
            "best_model": best["model"],
            "best_rmse": safe_float(best.get("rmse")),
            "stimulus_rmse_reference": loso_stim_rmse,
            "best_lift_vs_stimulus_rmse": lift_rmse,
            "best_dev_rmse": safe_float(best.get("dev_rmse")),
            "best_lift_vs_stimulus_dev_rmse": lift_dev_rmse,
            "best_dev_pearson": safe_float(best.get("dev_pearson")),
            "rmse_wins": rmse_wins,
            "rmse_losses": rmse_losses,
            "win_margin": win_margin,
            "worst_regression_delta_rmse": safe_float(best.get("worst_regression_delta_rmse")),
            "best_gain_delta_rmse": safe_float(best.get("best_gain_delta_rmse")),
            "stimulus_r2_in_sample": r2_stim,
            "subject_r2_in_sample": r2_subject,
            "residual_std_ratio_after_loso_stimulus": residual_ratio,
            "reason": "; ".join(reasons) if reasons else "passes current practical go criteria",
        })

    return pd.DataFrame(rows)


def main():
    variance = read_csv_required(VARIANCE_CSV)
    prior_main = read_csv_required(PRIOR_MAIN_CSV)
    prior_binary = read_csv_optional(PRIOR_BINARY_CSV)

    audit_main = read_csv_required(AUDIT_MAIN_CSV)
    audit_binary = read_csv_optional(AUDIT_BINARY_CSV)
    winloss = read_csv_required(AUDIT_WINLOSS_CSV)
    audit_best = read_csv_optional(AUDIT_BEST_CSV)
    audit_top3 = read_csv_optional(AUDIT_TOP3_CSV)

    prior_summary = build_prior_summary(prior_main, prior_binary)
    top_models = build_top_models(audit_main, winloss)
    go_nogo = build_go_nogo(top_models, variance)

    prior_summary.to_csv(OUT_PRIOR_SUMMARY, index=False)
    top_models.to_csv(OUT_TOP_MODELS, index=False)
    go_nogo.to_csv(OUT_GO_NOGO, index=False)

    report = {
        "objective": "Synthesize I-DARE residual physiology audit and provide go/no-go verdict.",
        "inputs": {
            "variance": str(VARIANCE_CSV),
            "prior_main": str(PRIOR_MAIN_CSV),
            "prior_binary": str(PRIOR_BINARY_CSV),
            "audit_main": str(AUDIT_MAIN_CSV),
            "audit_binary": str(AUDIT_BINARY_CSV),
            "audit_winloss": str(AUDIT_WINLOSS_CSV),
            "audit_best": str(AUDIT_BEST_CSV),
            "audit_top3": str(AUDIT_TOP3_CSV),
        },
        "criteria": {
            "practical_rmse_lift": PRACTICAL_RMSE_LIFT,
            "min_win_margin": MIN_WIN_MARGIN,
            "requires_positive_residual_dev_rmse_lift": True,
        },
        "go_nogo": go_nogo.to_dict(orient="records"),
        "top_models": top_models.to_dict(orient="records"),
        "prior_summary": prior_summary.to_dict(orient="records"),
    }

    OUT_JSON.write_text(json.dumps(clean_json(report), indent=2, ensure_ascii=False), encoding="utf-8")

    top_display_cols = [
        "target", "model", "n",
        "rmse", "lift_vs_stimulus_rmse",
        "dev_rmse", "lift_vs_stimulus_dev_rmse",
        "dev_pearson", "dev_sign_acc",
        "rmse_wins", "rmse_losses",
        "mean_delta_rmse_model_minus_stimulus",
        "median_delta_rmse_model_minus_stimulus",
        "worst_regression_delta_rmse",
        "best_gain_delta_rmse",
    ]

    prior_display_cols = [
        "dataset", "target", "protocol", "model",
        "rmse", "pearson", "ccc",
        "label_policy", "accuracy", "balanced_accuracy", "macro_f1", "auroc",
    ]

    go_cols = [
        "target", "decision", "best_model",
        "best_rmse", "stimulus_rmse_reference",
        "best_lift_vs_stimulus_rmse",
        "best_lift_vs_stimulus_dev_rmse",
        "best_dev_pearson",
        "rmse_wins", "rmse_losses", "win_margin",
        "stimulus_r2_in_sample",
        "subject_r2_in_sample",
        "residual_std_ratio_after_loso_stimulus",
        "reason",
    ]

    lines = []
    lines.append("# I-DARE Residual Physiology Synthesis\n")
    lines.append("This report synthesizes prior baselines, label variance decomposition, and the 05w residual physiology feature audit.\n")

    lines.append("## Go / No-Go verdict\n")
    lines.append(md_table(go_nogo, go_cols))

    lines.append("\n## Interpretation\n")
    lines.append(
        "- `NO_GO_CURRENT_FEATURE_SET` means the current EEG/EMG engineered feature blocks do not provide reliable residual improvement beyond stimulus-only under the current LOSO audit.\n"
        "- This does not prove physiology contains no signal; it means the tested feature blocks and Ridge audit did not extract a cross-subject residual signal strong enough to justify architecture optimization as a scientific claim.\n"
        "- A model is only interesting here if it improves stimulus-only in pooled RMSE, residual/dev RMSE, and subject-level win/loss stability.\n"
    )

    lines.append("\n## Top physiology models by RMSE lift vs stimulus-only\n")
    lines.append(md_table(top_models.groupby("target", as_index=False).head(8), top_display_cols))

    lines.append("\n## I-DARE prior baseline summary\n")
    lines.append(md_table(prior_summary, prior_display_cols))

    lines.append("\n## Recommended next action\n")
    lines.append(
        "Do not start another architecture search yet. First, treat this as a negative/near-null feature audit and decide whether to: "
        "(1) write up the stimulus-prior finding, or "
        "(2) run one stricter confirmatory residual test with permutation/bootstrap and a small number of neuroscience-motivated features.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 05x completed.")
    for p in [OUT_MD, OUT_JSON, OUT_GO_NOGO, OUT_TOP_MODELS, OUT_PRIOR_SUMMARY]:
        print(f"wrote: {p}")

    print("\nGo / No-Go:")
    print(go_nogo[go_cols].to_string(index=False))

    print("\nTop models:")
    print(top_models[top_display_cols].groupby("target", as_index=False).head(5).to_string(index=False))


if __name__ == "__main__":
    main()
