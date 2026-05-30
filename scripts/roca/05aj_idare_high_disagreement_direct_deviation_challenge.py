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

AUDIT_PREFIX = "idare_residual_physiology_feature_audit_current"
PRED_CSV = ROCA / f"{AUDIT_PREFIX}_predictions.csv"

OUT_PREFIX = "idare_high_disagreement_direct_deviation_challenge_current"
OUT_MD = ROCA / f"{OUT_PREFIX}.md"
OUT_JSON = ROCA / f"{OUT_PREFIX}.json"
OUT_DECISION = ROCA / f"{OUT_PREFIX}_decision_table.csv"
OUT_METRICS = ROCA / f"{OUT_PREFIX}_high_disagreement_metrics.csv"
OUT_WINLOSS = ROCA / f"{OUT_PREFIX}_subject_winloss.csv"
OUT_THRESH = ROCA / f"{OUT_PREFIX}_thresholds.csv"
OUT_NEXT = ROCA / f"{OUT_PREFIX}_next_steps.csv"

PRACTICAL_RMSE_LIFT = 0.02
MIN_WIN_MARGIN = 3
MIN_DEV_PEARSON = 0.10
PRIMARY_QUANTILE = 0.75


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
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return safe_float(x)
    if isinstance(x, (np.bool_,)):
        return bool(x)
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    return x


def rmse(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if len(a) == 0:
        return np.nan
    return float(np.sqrt(np.mean((a - b) ** 2)))


def corr(a, b, method: str = "pearson"):
    a = pd.Series(a, dtype="float64")
    b = pd.Series(b, dtype="float64")
    mask = a.notna() & b.notna()
    if int(mask.sum()) < 3:
        return np.nan
    if float(a[mask].std(ddof=0)) == 0.0 or float(b[mask].std(ddof=0)) == 0.0:
        return np.nan
    return float(a[mask].corr(b[mask], method=method))


def sign_acc(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b) & (a != 0)
    if int(mask.sum()) == 0:
        return np.nan
    return float(np.mean(np.sign(a[mask]) == np.sign(b[mask])))


def md_table(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "_empty_\n"
    d = df.copy()
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda x: "" if pd.isna(x) else f"{float(x):.6f}")
        else:
            d[c] = d[c].map(lambda x: "" if pd.isna(x) else str(x))
    cols = list(d.columns)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, r in d.iterrows():
        vals = [str(r[c]).replace("|", "\\|") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def find_col(df: pd.DataFrame, candidates: list[str], required: bool = True) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    if required:
        raise SystemExit(f"Could not find any of columns {candidates}. Available columns: {list(df.columns)}")
    return None


def normalize_key_series(s: pd.Series) -> pd.Series:
    out = s.astype(str)
    out = out.str.replace(r"^S0*", "", regex=True)
    out = out.str.replace(r"^subj[_-]?", "", regex=True, case=False)
    out = out.str.replace(r"^subject[_-]?", "", regex=True, case=False)
    out = out.str.replace(r"^video[_-]?", "", regex=True, case=False)
    out = out.str.replace(r"^stimulus[_-]?", "", regex=True, case=False)
    return out


def prepare_predictions(pred: pd.DataFrame) -> pd.DataFrame:
    """Normalize 05w prediction schema.

    Current 05w columns are:
      test_subject, stimulus_id, target, feature_block, model,
      y_true_score, train_stimulus_mean,
      true_deviation_from_train_stimulus_mean, y_pred_deviation, y_pred_score.

    Older scripts expected explicit stimulus_only rows; this version uses
    train_stimulus_mean as the zero-residual/stimulus baseline.
    """
    target_col = find_col(pred, ["target"])
    model_col = find_col(pred, ["model"])
    block_col = find_col(pred, ["feature_block", "block"], required=False)
    subject_col = find_col(pred, ["test_subject", "subject_id", "subject", "participant_id", "participant", "subj"])
    stimulus_col = find_col(pred, ["stimulus_id", "stimulus", "video_id", "video", "clip_id", "movie_id"])

    true_col = find_col(pred, ["y_true_score", "y_true", "true", "label", "rating", "target_value", "y"])
    score_pred_col = find_col(pred, ["y_pred_score", "y_pred", "pred", "prediction", "y_hat"])
    stim_pred_col = find_col(pred, ["train_stimulus_mean", "stimulus_prediction", "stimulus_only_prediction"], required=False)
    true_dev_col = find_col(pred, ["true_deviation_from_train_stimulus_mean", "true_residual", "residual"], required=False)
    pred_dev_col = find_col(pred, ["y_pred_deviation", "predicted_deviation", "pred_residual"], required=False)

    if stim_pred_col is None:
        raise SystemExit(
            "05aj needs train_stimulus_mean/stimulus_prediction in the 05w predictions file. "
            f"Available columns: {list(pred.columns)}"
        )

    out = pd.DataFrame()
    out["target"] = pred[target_col]
    out["model"] = pred[model_col].astype(str)
    out["block"] = pred[block_col].astype(str) if block_col else pred[model_col].astype(str)
    out["subject_key"] = normalize_key_series(pred[subject_col])
    out["stimulus_key"] = normalize_key_series(pred[stimulus_col])
    out["y_true"] = pd.to_numeric(pred[true_col], errors="coerce")
    out["stimulus_pred"] = pd.to_numeric(pred[stim_pred_col], errors="coerce")
    out["model_pred"] = pd.to_numeric(pred[score_pred_col], errors="coerce")

    if true_dev_col:
        out["true_residual"] = pd.to_numeric(pred[true_dev_col], errors="coerce")
    else:
        out["true_residual"] = out["y_true"] - out["stimulus_pred"]

    if pred_dev_col:
        out["model_residual_pred"] = pd.to_numeric(pred[pred_dev_col], errors="coerce")
    else:
        out["model_residual_pred"] = out["model_pred"] - out["stimulus_pred"]

    before = len(out)
    out = out.dropna(subset=["target", "model", "block", "subject_key", "stimulus_key", "y_true", "stimulus_pred", "model_pred", "true_residual", "model_residual_pred"])
    dropped = before - len(out)
    if dropped:
        print(f"[WARN] dropped {dropped} rows with missing required values")

    # If repeats/duplicates exist, average predictions at the same target-model-subject-stimulus identity.
    out = (
        out.groupby(["target", "model", "block", "subject_key", "stimulus_key"], as_index=False)
        .agg({
            "y_true": "mean",
            "stimulus_pred": "mean",
            "model_pred": "mean",
            "true_residual": "mean",
            "model_residual_pred": "mean",
        })
    )
    return out


def main():
    if not PRED_CSV.exists():
        raise SystemExit(f"Missing predictions CSV: {PRED_CSV}")

    raw = pd.read_csv(PRED_CSV)
    pred = prepare_predictions(raw)

    print("[INFO] I-DARE high-disagreement direct deviation challenge")
    print(f"[INFO] input={PRED_CSV}")
    print(f"[INFO] normalized rows={len(pred)} targets={sorted(pred['target'].unique())}")
    print(f"[INFO] models={pred['model'].nunique()} subjects={pred['subject_key'].nunique()} stimuli={pred['stimulus_key'].nunique()}")

    rows_metrics = []
    rows_winloss = []
    rows_thresholds = []
    decision_rows = []

    for target in sorted(pred["target"].dropna().unique()):
        sub = pred[pred["target"].eq(target)].copy()

        # One residual target per subject/stimulus, independent of model.
        base = (
            sub.groupby(["target", "subject_key", "stimulus_key"], as_index=False)
            .agg({
                "y_true": "mean",
                "stimulus_pred": "mean",
                "true_residual": "mean",
            })
        )
        base["abs_true_residual"] = base["true_residual"].abs()

        thresholds = {}
        for q in [0.50, 0.75, 0.90]:
            thresholds[q] = float(base["abs_true_residual"].quantile(q))
            keep = base["abs_true_residual"].ge(thresholds[q])
            rows_thresholds.append({
                "target": target,
                "quantile": q,
                "abs_residual_threshold": thresholds[q],
                "n_samples": int(keep.sum()),
                "n_subjects": int(base.loc[keep, "subject_key"].nunique()),
                "stimulus_residual_rmse_on_subset": rmse(base.loc[keep, "true_residual"], np.zeros(int(keep.sum()))),
                "mean_abs_residual_on_subset": float(base.loc[keep, "abs_true_residual"].mean()),
            })

        for (model, block), mdf in sub.groupby(["model", "block"]):
            merged = mdf.merge(
                base[["target", "subject_key", "stimulus_key", "abs_true_residual"]],
                on=["target", "subject_key", "stimulus_key"],
                how="inner",
            )
            if merged.empty:
                continue

            for q, threshold in thresholds.items():
                cur = merged[merged["abs_true_residual"].ge(threshold)].copy()
                if cur.empty:
                    continue

                stim_res_rmse = rmse(cur["true_residual"], np.zeros(len(cur)))
                model_score_rmse = rmse(cur["y_true"], cur["model_pred"])
                model_res_rmse = rmse(cur["true_residual"], cur["model_residual_pred"])
                lift = stim_res_rmse - model_res_rmse

                pear = corr(cur["true_residual"], cur["model_residual_pred"], "pearson")
                spear = corr(cur["true_residual"], cur["model_residual_pred"], "spearman")
                sacc = sign_acc(cur["true_residual"], cur["model_residual_pred"])

                subj_rows = []
                for subj, g in cur.groupby("subject_key"):
                    sr = rmse(g["true_residual"], np.zeros(len(g)))
                    mr = rmse(g["true_residual"], g["model_residual_pred"])
                    subj_rows.append({
                        "subject_key": subj,
                        "stimulus_residual_rmse": sr,
                        "model_residual_rmse": mr,
                        "delta_model_minus_stimulus": mr - sr,
                    })
                subj_df = pd.DataFrame(subj_rows)
                if subj_df.empty:
                    wins = losses = ties = 0
                    win_margin = 0
                    mean_delta = np.nan
                    median_delta = np.nan
                    worst = np.nan
                    best = np.nan
                else:
                    eps = 1e-12
                    wins = int((subj_df["delta_model_minus_stimulus"] < -eps).sum())
                    losses = int((subj_df["delta_model_minus_stimulus"] > eps).sum())
                    ties = int((subj_df["delta_model_minus_stimulus"].abs() <= eps).sum())
                    win_margin = wins - losses
                    mean_delta = float(subj_df["delta_model_minus_stimulus"].mean())
                    median_delta = float(subj_df["delta_model_minus_stimulus"].median())
                    worst = float(subj_df["delta_model_minus_stimulus"].max())
                    best = float(subj_df["delta_model_minus_stimulus"].min())

                passes = (
                    lift >= PRACTICAL_RMSE_LIFT
                    and win_margin >= MIN_WIN_MARGIN
                    and (not pd.isna(mean_delta) and mean_delta < 0)
                    and (not pd.isna(pear) and pear >= MIN_DEV_PEARSON)
                )

                rows_metrics.append({
                    "target": target,
                    "quantile": q,
                    "abs_residual_threshold": threshold,
                    "block": block,
                    "model": model,
                    "n": int(len(cur)),
                    "subjects": int(cur["subject_key"].nunique()),
                    "stimulus_residual_rmse_on_subset": stim_res_rmse,
                    "model_score_rmse_on_subset": model_score_rmse,
                    "model_residual_rmse_on_subset": model_res_rmse,
                    "lift_vs_zero_residual_rmse": lift,
                    "residual_pearson": pear,
                    "residual_spearman": spear,
                    "residual_sign_acc": sacc,
                    "pred_residual_std": float(cur["model_residual_pred"].std(ddof=0)),
                    "true_residual_std": float(cur["true_residual"].std(ddof=0)),
                    "rmse_wins": wins,
                    "rmse_losses": losses,
                    "rmse_ties": ties,
                    "rmse_win_margin": win_margin,
                    "mean_delta_rmse_model_minus_stimulus": mean_delta,
                    "median_delta_rmse_model_minus_stimulus": median_delta,
                    "worst_regression_delta_rmse": worst,
                    "best_gain_delta_rmse": best,
                    "passes_high_disagreement_gate": bool(passes),
                })
                rows_winloss.append({
                    "target": target,
                    "quantile": q,
                    "block": block,
                    "model": model,
                    "subjects": int(len(subj_df)),
                    "rmse_wins": wins,
                    "rmse_losses": losses,
                    "rmse_ties": ties,
                    "rmse_win_margin": win_margin,
                    "mean_delta_rmse_model_minus_stimulus": mean_delta,
                    "median_delta_rmse_model_minus_stimulus": median_delta,
                    "worst_regression_delta_rmse": worst,
                    "best_gain_delta_rmse": best,
                })

    metrics = pd.DataFrame(rows_metrics)
    winloss = pd.DataFrame(rows_winloss)
    thresholds_df = pd.DataFrame(rows_thresholds)

    if metrics.empty:
        raise SystemExit("No metrics generated.")

    metrics = metrics.sort_values(
        ["target", "quantile", "lift_vs_zero_residual_rmse", "residual_pearson", "rmse_win_margin"],
        ascending=[True, True, False, False, False],
    )
    winloss = winloss.sort_values(["target", "quantile", "rmse_win_margin"], ascending=[True, True, False])

    for target in sorted(metrics["target"].dropna().unique()):
        primary = metrics[(metrics["target"].eq(target)) & (metrics["quantile"].eq(PRIMARY_QUANTILE))].copy()
        if primary.empty:
            primary = metrics[metrics["target"].eq(target)].copy()
        primary = primary.sort_values(
            ["lift_vs_zero_residual_rmse", "residual_pearson", "rmse_win_margin"],
            ascending=[False, False, False],
        )
        best = primary.iloc[0].to_dict()

        reasons = []
        if safe_float(best.get("lift_vs_zero_residual_rmse")) is None or best["lift_vs_zero_residual_rmse"] < PRACTICAL_RMSE_LIFT:
            reasons.append("residual RMSE lift on high-disagreement subset is below practical threshold")
        if safe_float(best.get("residual_pearson")) is None or best["residual_pearson"] < MIN_DEV_PEARSON:
            reasons.append("residual correlation is weak")
        if safe_float(best.get("rmse_win_margin")) is None or best["rmse_win_margin"] < MIN_WIN_MARGIN:
            reasons.append("subject-level win margin is not stable")
        if safe_float(best.get("mean_delta_rmse_model_minus_stimulus")) is None or best["mean_delta_rmse_model_minus_stimulus"] >= 0:
            reasons.append("mean subject RMSE delta does not beat zero-residual/stimulus baseline")

        if bool(best.get("passes_high_disagreement_gate")):
            decision = "GO_HIGH_DISAGREEMENT_DIRECT_DEVIATION_PHYSIOLOGY"
            reason = "physiology predicts high-disagreement residuals with practical RMSE lift and paired subject stability"
        elif (
            (safe_float(best.get("lift_vs_zero_residual_rmse")) is not None and best["lift_vs_zero_residual_rmse"] > 0)
            or (safe_float(best.get("residual_pearson")) is not None and best["residual_pearson"] >= MIN_DEV_PEARSON)
        ):
            decision = "WEAK_HIGH_DISAGREEMENT_SIGNAL_NEEDS_CONFIRMATION"
            reason = "; ".join(reasons) if reasons else "weak signal but confirmatory gate failed"
        else:
            decision = "NO_GO_HIGH_DISAGREEMENT_CURRENT_FIXED_FEATURES"
            reason = "; ".join(reasons) if reasons else "high-disagreement gate failed"

        decision_rows.append({
            "target": target,
            "decision": decision,
            "quantile": best.get("quantile"),
            "best_block": best.get("block"),
            "best_model": best.get("model"),
            "n": best.get("n"),
            "subjects": best.get("subjects"),
            "abs_residual_threshold": best.get("abs_residual_threshold"),
            "stimulus_residual_rmse_on_subset": best.get("stimulus_residual_rmse_on_subset"),
            "best_model_residual_rmse_on_subset": best.get("model_residual_rmse_on_subset"),
            "best_lift_vs_zero_residual_rmse": best.get("lift_vs_zero_residual_rmse"),
            "best_residual_pearson": best.get("residual_pearson"),
            "best_residual_sign_acc": best.get("residual_sign_acc"),
            "rmse_wins": best.get("rmse_wins"),
            "rmse_losses": best.get("rmse_losses"),
            "rmse_win_margin": best.get("rmse_win_margin"),
            "mean_delta_rmse_model_minus_stimulus": best.get("mean_delta_rmse_model_minus_stimulus"),
            "passes_high_disagreement_gate": best.get("passes_high_disagreement_gate"),
            "reason": reason,
        })

    decision = pd.DataFrame(decision_rows)

    next_steps = pd.DataFrame([
        {
            "priority": 1,
            "step": "05ak",
            "title": "Representation-learning feasibility plan",
            "purpose": "If high-disagreement residuals still do not pass, move beyond fixed engineered EEG/EMG features.",
            "success_condition": "Learned EEG/EMG representations beat fixed-feature residual models under the locked evaluation.",
        },
        {
            "priority": 2,
            "step": "05al",
            "title": "Failure-subject physiology rescue",
            "purpose": "Test whether physiology helps only for subjects where locked personalization still regresses.",
            "success_condition": "Improves failure-subject RMSE without harming pooled or paired metrics.",
        },
        {
            "priority": 3,
            "step": "05am",
            "title": "Physiology-assisted calibration sample reduction",
            "purpose": "Test if physiology can reduce k even when it cannot beat the k=16 locked model.",
            "success_condition": "Physiology-assisted lower-k model matches the locked k=16 baseline with subject-level stability.",
        },
    ])

    decision.to_csv(OUT_DECISION, index=False)
    metrics.to_csv(OUT_METRICS, index=False)
    winloss.to_csv(OUT_WINLOSS, index=False)
    thresholds_df.to_csv(OUT_THRESH, index=False)
    next_steps.to_csv(OUT_NEXT, index=False)

    report = {
        "inputs": {"predictions": str(PRED_CSV)},
        "parameters": {
            "primary_quantile": PRIMARY_QUANTILE,
            "practical_rmse_lift": PRACTICAL_RMSE_LIFT,
            "min_win_margin": MIN_WIN_MARGIN,
            "min_dev_pearson": MIN_DEV_PEARSON,
        },
        "decision": decision.to_dict(orient="records"),
        "thresholds": thresholds_df.to_dict(orient="records"),
        "top_metrics": metrics.groupby("target", group_keys=False).head(20).to_dict(orient="records"),
        "next_steps": next_steps.to_dict(orient="records"),
    }
    OUT_JSON.write_text(json.dumps(clean_json(report), indent=2), encoding="utf-8")

    lines = []
    lines.append("# I-DARE High-Disagreement Direct Deviation Challenge\n")
    lines.append("This audit asks whether fixed EEG/EMG feature blocks predict residuals specifically where the subject rating deviates strongly from the stimulus prior.\n")
    lines.append("Residual target: `rating - train_stimulus_mean`. The zero-residual baseline is the stimulus-only prediction.\n")
    lines.append("## Decision table\n")
    lines.append(md_table(decision))
    lines.append("\n## High-disagreement thresholds\n")
    lines.append(md_table(thresholds_df))
    lines.append("\n## Top high-disagreement physiology metrics\n")
    lines.append(md_table(metrics.groupby("target", group_keys=False).head(15)))
    lines.append("\n## Interpretation\n")
    lines.append("- `GO` means EEG/EMG predicts subjective deviation where stimulus-only is weakest.\n")
    lines.append("- `WEAK` means some correlation or small lift appears, but it is not stable enough for a scientific claim.\n")
    lines.append("- `NO_GO` means current fixed EEG/EMG features remain insufficient even on high-disagreement samples.\n")
    lines.append("\n## Next steps\n")
    lines.append(md_table(next_steps))
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 05aj completed.")
    for p in [OUT_MD, OUT_JSON, OUT_DECISION, OUT_METRICS, OUT_WINLOSS, OUT_THRESH, OUT_NEXT]:
        print(f"wrote: {p}")

    print("\nDecision table:")
    print(decision.to_string(index=False))
    print("\nTop metrics:")
    cols = [
        "target", "quantile", "block", "model", "n",
        "stimulus_residual_rmse_on_subset", "model_residual_rmse_on_subset",
        "lift_vs_zero_residual_rmse", "residual_pearson", "residual_sign_acc",
        "rmse_win_margin", "mean_delta_rmse_model_minus_stimulus",
        "passes_high_disagreement_gate",
    ]
    print(metrics[[c for c in cols if c in metrics.columns]].groupby("target", group_keys=False).head(12).to_string(index=False))


if __name__ == "__main__":
    main()
