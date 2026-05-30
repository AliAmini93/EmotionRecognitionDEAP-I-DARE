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

OUT_PREFIX = "idare_direct_deviation_predictability_audit_current"

AUDIT_PREFIX = "idare_residual_physiology_feature_audit_current"
AUDIT_MAIN = ROCA / f"{AUDIT_PREFIX}_main_metrics.csv"
AUDIT_WINLOSS = ROCA / f"{AUDIT_PREFIX}_subject_winloss.csv"
AUDIT_PRED = ROCA / f"{AUDIT_PREFIX}_predictions.csv"

PHYS_CHALLENGE_SYNTHESIS = ROCA / "idare_physiology_challenge_synthesis_current_decision_table.csv"
SCIENTIFIC_LOCK = ROCA / "idare_scientific_direction_lock_current_locked_baselines.csv"

OUT_MD = ROCA / f"{OUT_PREFIX}.md"
OUT_JSON = ROCA / f"{OUT_PREFIX}.json"
OUT_DECISION = ROCA / f"{OUT_PREFIX}_decision_table.csv"
OUT_MODEL_METRICS = ROCA / f"{OUT_PREFIX}_direct_model_metrics.csv"
OUT_HIGH_RESIDUAL = ROCA / f"{OUT_PREFIX}_high_residual_metrics.csv"
OUT_FEATURE_BOTTLENECK = ROCA / f"{OUT_PREFIX}_feature_bottleneck_matrix.csv"
OUT_NEXT_STEPS = ROCA / f"{OUT_PREFIX}_next_steps.csv"

PRACTICAL_DEV_RMSE_LIFT = 0.02
MIN_WIN_MARGIN = 3
MIN_DEV_PEARSON = 0.05


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
        v = float(x)
        return None if not math.isfinite(v) else v
    if isinstance(x, float):
        return None if not math.isfinite(x) else x
    if pd.isna(x):
        return None
    return x


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def md_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df is None or df.empty:
        return "_No rows._\n"
    x = df.copy()
    if max_rows is not None:
        x = x.head(max_rows)
    for col in x.columns:
        if pd.api.types.is_float_dtype(x[col]):
            x[col] = x[col].map(lambda v: "" if pd.isna(v) else f"{float(v):.6g}")
        else:
            x[col] = x[col].map(lambda v: "" if pd.isna(v) else str(v))
    cols = list(x.columns)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in x.iterrows():
        vals = [str(row[c]).replace("\n", " ") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def first_existing(cols: list[str], candidates: list[str]) -> str | None:
    lower = {c.lower(): c for c in cols}
    for c in candidates:
        if c in cols:
            return c
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def corr(a: np.ndarray, b: np.ndarray) -> float | None:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    a = a[mask]
    b = b[mask]
    if len(a) < 3:
        return None
    if float(np.std(a)) <= 1e-12 or float(np.std(b)) <= 1e-12:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def rmse(a: np.ndarray, b: np.ndarray) -> float | None:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b)
    if not np.any(mask):
        return None
    return float(np.sqrt(np.mean((a[mask] - b[mask]) ** 2)))


def sign_acc(a: np.ndarray, b: np.ndarray) -> float | None:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mask = np.isfinite(a) & np.isfinite(b) & (np.abs(a) > 1e-12) & (np.abs(b) > 1e-12)
    if not np.any(mask):
        return None
    return float(np.mean(np.sign(a[mask]) == np.sign(b[mask])))


def model_to_block(model: str) -> str:
    m = str(model)
    if m.startswith("physio_"):
        m = m[len("physio_"):]
    if m.endswith("_ridge"):
        m = m[:-len("_ridge")]
    return m


def attach_winloss(model_metrics: pd.DataFrame, winloss: pd.DataFrame) -> pd.DataFrame:
    if model_metrics.empty:
        return model_metrics
    out = model_metrics.copy()
    if winloss.empty:
        out["rmse_wins"] = np.nan
        out["rmse_losses"] = np.nan
        out["rmse_win_margin"] = np.nan
        return out
    keep = [c for c in [
        "target", "model", "rmse_wins", "rmse_losses",
        "mean_delta_rmse_model_minus_stimulus",
        "median_delta_rmse_model_minus_stimulus",
        "worst_regression_delta_rmse",
        "best_gain_delta_rmse",
    ] if c in winloss.columns]
    if "target" in keep and "model" in keep:
        out = out.merge(winloss[keep], on=["target", "model"], how="left")
    if "rmse_wins" in out.columns and "rmse_losses" in out.columns:
        out["rmse_win_margin"] = out["rmse_wins"] - out["rmse_losses"]
    else:
        out["rmse_win_margin"] = np.nan
    return out


def build_model_metric_table(main: pd.DataFrame, winloss: pd.DataFrame) -> pd.DataFrame:
    if main.empty:
        return pd.DataFrame()
    phys = main[main["model"].astype(str).ne("stimulus_only")].copy()
    if phys.empty:
        return pd.DataFrame()
    phys["block"] = phys["model"].map(model_to_block)
    phys = attach_winloss(phys, winloss)

    for c in [
        "rmse", "dev_rmse", "lift_vs_stimulus_rmse", "lift_vs_stimulus_dev_rmse",
        "dev_pearson", "dev_sign_acc", "pred_dev_std", "true_dev_std",
        "rmse_win_margin", "rmse_wins", "rmse_losses",
    ]:
        if c not in phys.columns:
            phys[c] = np.nan
        phys[c] = pd.to_numeric(phys[c], errors="coerce")

    phys["direct_gate_dev_rmse"] = phys["lift_vs_stimulus_dev_rmse"] >= PRACTICAL_DEV_RMSE_LIFT
    phys["direct_gate_dev_corr"] = phys["dev_pearson"] >= MIN_DEV_PEARSON
    phys["direct_gate_subject_margin"] = phys["rmse_win_margin"] >= MIN_WIN_MARGIN
    phys["passes_direct_deviation_gate"] = (
        phys["direct_gate_dev_rmse"]
        & phys["direct_gate_dev_corr"]
        & phys["direct_gate_subject_margin"]
    )

    cols = [
        "target", "block", "model", "n",
        "rmse", "lift_vs_stimulus_rmse",
        "dev_rmse", "lift_vs_stimulus_dev_rmse",
        "dev_pearson", "dev_sign_acc",
        "pred_dev_std", "true_dev_std",
        "rmse_wins", "rmse_losses", "rmse_win_margin",
        "mean_delta_rmse_model_minus_stimulus",
        "worst_regression_delta_rmse", "best_gain_delta_rmse",
        "passes_direct_deviation_gate",
    ]
    cols = [c for c in cols if c in phys.columns]
    sort_cols = [c for c in ["target", "lift_vs_stimulus_dev_rmse", "dev_pearson", "rmse_win_margin"] if c in phys.columns]
    ascending = [True, False, False, False][: len(sort_cols)]
    return phys[cols].sort_values(sort_cols, ascending=ascending, na_position="last")


def compute_prediction_residuals(pred: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    if pred.empty:
        return pd.DataFrame(), "prediction file not available"

    df = pred.copy()
    cols = list(df.columns)
    model_col = first_existing(cols, ["model"])
    target_col = first_existing(cols, ["target"])
    y_true_col = first_existing(cols, ["y_true", "true", "true_score", "rating", "label", "y"])
    y_pred_col = first_existing(cols, ["y_pred", "pred", "prediction", "pred_score", "y_hat"])
    true_dev_col = first_existing(cols, ["true_dev", "dev_true", "residual_true", "target_dev", "deviation_true"])
    pred_dev_col = first_existing(cols, ["pred_dev", "dev_pred", "residual_pred", "deviation_pred"])
    baseline_col = first_existing(cols, ["stimulus_pred", "stimulus_only_pred", "baseline_pred", "stimulus_mean", "stimulus_only"])

    if model_col is None or target_col is None:
        return pd.DataFrame(), "prediction file lacks target/model columns"

    if true_dev_col is not None and pred_dev_col is not None:
        out = df.copy()
        out["true_dev_for_audit"] = pd.to_numeric(out[true_dev_col], errors="coerce")
        out["pred_dev_for_audit"] = pd.to_numeric(out[pred_dev_col], errors="coerce")
        out["audit_model"] = out[model_col].astype(str)
        out["audit_target"] = out[target_col].astype(str)
        return out, "used existing true_dev/pred_dev columns"

    if y_true_col is None or y_pred_col is None:
        return pd.DataFrame(), "prediction file lacks usable y_true/y_pred columns"

    out = df.copy()
    out["audit_model"] = out[model_col].astype(str)
    out["audit_target"] = out[target_col].astype(str)
    out["y_true_for_audit"] = pd.to_numeric(out[y_true_col], errors="coerce")
    out["y_pred_for_audit"] = pd.to_numeric(out[y_pred_col], errors="coerce")

    if baseline_col is not None:
        out["baseline_for_audit"] = pd.to_numeric(out[baseline_col], errors="coerce")
        out["true_dev_for_audit"] = out["y_true_for_audit"] - out["baseline_for_audit"]
        out["pred_dev_for_audit"] = out["y_pred_for_audit"] - out["baseline_for_audit"]
        return out, f"computed residuals from baseline column {baseline_col}"

    baseline_rows = out[out["audit_model"].eq("stimulus_only")].copy()
    if baseline_rows.empty:
        return pd.DataFrame(), "could not infer stimulus baseline rows"

    candidate_keys = [
        "target", "subject", "subject_id", "participant", "participant_id",
        "stimulus", "stimulus_id", "video", "video_id", "clip", "clip_id",
        "trial", "trial_id", "sample_id", "row_id",
    ]
    keys = [first_existing(cols, [c]) for c in candidate_keys]
    keys = [k for k in keys if k is not None]
    if target_col not in keys:
        keys.insert(0, target_col)
    # Keep only keys that uniquely-ish identify rows. If too many are missing, try target+subject+stimulus.
    keys = list(dict.fromkeys(keys))
    merge_keys = [k for k in keys if k in baseline_rows.columns and k in out.columns]

    if len(merge_keys) < 2:
        return pd.DataFrame(), "could not infer merge keys for stimulus baseline"

    base = baseline_rows[merge_keys + ["y_pred_for_audit"]].rename(columns={"y_pred_for_audit": "baseline_for_audit"})
    base = base.drop_duplicates(merge_keys)
    merged = out.merge(base, on=merge_keys, how="left")
    merged["true_dev_for_audit"] = merged["y_true_for_audit"] - merged["baseline_for_audit"]
    merged["pred_dev_for_audit"] = merged["y_pred_for_audit"] - merged["baseline_for_audit"]
    return merged, "computed residuals by joining stimulus_only predictions"


def high_residual_metrics(resid: pd.DataFrame) -> pd.DataFrame:
    if resid.empty:
        return pd.DataFrame()

    rows = []
    phys = resid[~resid["audit_model"].eq("stimulus_only")].copy()
    if phys.empty:
        return pd.DataFrame()

    for (target, model), g in phys.groupby(["audit_target", "audit_model"], dropna=False):
        g = g.copy()
        t = pd.to_numeric(g["true_dev_for_audit"], errors="coerce").to_numpy(float)
        p = pd.to_numeric(g["pred_dev_for_audit"], errors="coerce").to_numpy(float)
        valid = np.isfinite(t) & np.isfinite(p)
        if valid.sum() < 8:
            continue
        abs_t = np.abs(t[valid])
        thresholds = {
            "all_residuals": -np.inf,
            "abs_residual_q75": float(np.quantile(abs_t, 0.75)),
            "abs_residual_q90": float(np.quantile(abs_t, 0.90)),
        }
        for subset_name, th in thresholds.items():
            if np.isneginf(th):
                m = valid
            else:
                m = valid & (np.abs(t) >= th)
            if m.sum() < 8:
                continue
            r_model = rmse(t[m], p[m])
            r_zero = rmse(t[m], np.zeros(int(m.sum())))
            rows.append({
                "target": target,
                "block": model_to_block(model),
                "model": model,
                "subset": subset_name,
                "n": int(m.sum()),
                "zero_residual_rmse": r_zero,
                "physiology_residual_rmse": r_model,
                "lift_vs_zero_residual_rmse": None if r_model is None or r_zero is None else r_zero - r_model,
                "residual_pearson": corr(t[m], p[m]),
                "residual_sign_acc": sign_acc(t[m], p[m]),
                "true_residual_std": float(np.std(t[m])),
                "pred_residual_std": float(np.std(p[m])),
            })

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(
        ["target", "subset", "lift_vs_zero_residual_rmse", "residual_pearson"],
        ascending=[True, True, False, False],
        na_position="last",
    )


def build_decision(model_metrics: pd.DataFrame, high: pd.DataFrame, context: pd.DataFrame) -> pd.DataFrame:
    rows = []
    targets = sorted(model_metrics["target"].dropna().astype(str).unique().tolist()) if not model_metrics.empty else []
    for target in targets:
        m = model_metrics[model_metrics["target"].astype(str).eq(target)].copy()
        m = m.sort_values(
            ["lift_vs_stimulus_dev_rmse", "dev_pearson", "rmse_win_margin"],
            ascending=[False, False, False],
            na_position="last",
        )
        if m.empty:
            continue
        best = m.iloc[0].to_dict()

        hi_best = {}
        if not high.empty:
            h = high[
                (high["target"].astype(str) == target)
                & (high["subset"].astype(str) == "abs_residual_q75")
            ].copy()
            if not h.empty:
                h = h.sort_values(["lift_vs_zero_residual_rmse", "residual_pearson"], ascending=[False, False], na_position="last")
                hi_best = h.iloc[0].to_dict()

        dev_lift = safe_float(best.get("lift_vs_stimulus_dev_rmse"))
        dev_corr = safe_float(best.get("dev_pearson"))
        win_margin = safe_float(best.get("rmse_win_margin"))
        high_lift = safe_float(hi_best.get("lift_vs_zero_residual_rmse"))

        pass_direct = bool(best.get("passes_direct_deviation_gate", False))
        high_pass = high_lift is not None and high_lift >= PRACTICAL_DEV_RMSE_LIFT

        reasons = []
        if dev_lift is None or dev_lift < PRACTICAL_DEV_RMSE_LIFT:
            reasons.append("direct residual/dev RMSE lift is below practical threshold")
        if dev_corr is None or dev_corr < MIN_DEV_PEARSON:
            reasons.append("direct residual correlation is weak")
        if win_margin is None or win_margin < MIN_WIN_MARGIN:
            reasons.append("subject-level win margin is not stable")
        if high_lift is not None and high_lift < PRACTICAL_DEV_RMSE_LIFT:
            reasons.append("high-residual subset does not show practical physiology lift")
        if not reasons:
            reasons.append("direct residual signal is learnable by current fixed physiology features")

        if pass_direct and (high_lift is None or high_pass):
            decision = "GO_CURRENT_PHYSIOLOGY_CAN_MODEL_DIRECT_DEVIATION"
        elif (dev_corr is not None and dev_corr > 0.10) or (high_lift is not None and high_lift > 0):
            decision = "WEAK_SIGNAL_BUT_NOT_ACTIONABLE_WITH_CURRENT_FEATURES"
        else:
            decision = "NO_GO_CURRENT_FIXED_FEATURES_FOR_DIRECT_DEVIATION"

        rows.append({
            "target": target,
            "decision": decision,
            "best_block_by_direct_dev": best.get("block"),
            "best_model_by_direct_dev": best.get("model"),
            "best_dev_rmse": safe_float(best.get("dev_rmse")),
            "best_lift_vs_stimulus_dev_rmse": dev_lift,
            "best_dev_pearson": dev_corr,
            "best_dev_sign_acc": safe_float(best.get("dev_sign_acc")),
            "rmse_win_margin": win_margin,
            "high_residual_q75_best_block": hi_best.get("block"),
            "high_residual_q75_lift_vs_zero": high_lift,
            "passes_direct_deviation_gate": pass_direct,
            "reason": "; ".join(reasons),
        })
    return pd.DataFrame(rows)


def main():
    main_metrics = read_csv(AUDIT_MAIN)
    winloss = read_csv(AUDIT_WINLOSS)
    pred = read_csv(AUDIT_PRED)

    if main_metrics.empty:
        raise SystemExit(f"Missing required input: {AUDIT_MAIN}")

    model_metrics = build_model_metric_table(main_metrics, winloss)
    resid, residual_note = compute_prediction_residuals(pred)
    high = high_residual_metrics(resid)

    context = read_csv(PHYS_CHALLENGE_SYNTHESIS)
    locked = read_csv(SCIENTIFIC_LOCK)

    decision = build_decision(model_metrics, high, context)

    feature_bottleneck = pd.DataFrame([
        {
            "hypothesis": "H1_current_fixed_EEG_EMG_features_are_insufficient",
            "status": "SUPPORTED_BY_CURRENT_AUDITS" if not decision.empty and not decision["passes_direct_deviation_gate"].any() else "NOT_REJECTED",
            "evidence": "05w direct residual/dev metrics and 05ah/05ahx locked-baseline challenge do not show incremental physiology value.",
            "next_test": "representation_learning_or_raw_signal_modeling",
        },
        {
            "hypothesis": "H2_current_adaptation_method_is_insufficient",
            "status": "PARTLY_SUPPORTED",
            "evidence": "Calibration/personalization works without physiology, but fixed-feature physiology does not improve it.",
            "next_test": "physiology_as_gating_or_reliability_weighting_after_direct_deviation_test",
        },
        {
            "hypothesis": "H3_no_learnable_physiology_signal_exists",
            "status": "NOT_TESTED_AS_FINAL_CLAIM",
            "evidence": "Current audits only reject current feature/model route; they do not prove raw EEG/EMG lacks usable signal.",
            "next_test": "deep_representation_learning_and_high_disagreement_protocol",
        },
    ])

    next_steps = pd.DataFrame([
        {
            "priority": 1,
            "step": "05aj",
            "title": "High-disagreement direct deviation challenge",
            "purpose": "Restrict or weight samples where subjects disagree most with stimulus mean, then test EEG/EMG residual prediction.",
            "success_condition": "Positive residual RMSE lift, positive paired subject statistics, and stable win margin.",
        },
        {
            "priority": 2,
            "step": "05ak",
            "title": "Representation-learning feasibility plan",
            "purpose": "Move beyond fixed engineered EEG/EMG features if direct deviation remains no-go.",
            "success_condition": "Learned EEG/EMG representation beats fixed-feature residual models under locked evaluation.",
        },
        {
            "priority": 3,
            "step": "05al",
            "title": "Failure-subject physiology rescue",
            "purpose": "Test whether physiology helps only where locked personalization fails.",
            "success_condition": "Improves failure-subject RMSE without harming pooled or paired metrics.",
        },
    ])

    decision.to_csv(OUT_DECISION, index=False)
    model_metrics.to_csv(OUT_MODEL_METRICS, index=False)
    high.to_csv(OUT_HIGH_RESIDUAL, index=False)
    feature_bottleneck.to_csv(OUT_FEATURE_BOTTLENECK, index=False)
    next_steps.to_csv(OUT_NEXT_STEPS, index=False)

    payload = {
        "inputs": {
            "audit_main": str(AUDIT_MAIN),
            "audit_winloss": str(AUDIT_WINLOSS),
            "audit_predictions": str(AUDIT_PRED),
            "physiology_challenge_synthesis": str(PHYS_CHALLENGE_SYNTHESIS) if PHYS_CHALLENGE_SYNTHESIS.exists() else None,
            "scientific_lock": str(SCIENTIFIC_LOCK) if SCIENTIFIC_LOCK.exists() else None,
        },
        "residual_prediction_handling": residual_note,
        "thresholds": {
            "practical_dev_rmse_lift": PRACTICAL_DEV_RMSE_LIFT,
            "min_win_margin": MIN_WIN_MARGIN,
            "min_dev_pearson": MIN_DEV_PEARSON,
        },
        "decision": decision.to_dict(orient="records"),
        "model_metrics_top": model_metrics.head(50).to_dict(orient="records"),
        "high_residual_top": high.head(50).to_dict(orient="records") if not high.empty else [],
        "feature_bottleneck": feature_bottleneck.to_dict(orient="records"),
        "next_steps": next_steps.to_dict(orient="records"),
    }
    OUT_JSON.write_text(json.dumps(clean_json(payload), indent=2), encoding="utf-8")

    lines = []
    lines.append("# I-DARE Direct Deviation Predictability Audit")
    lines.append("")
    lines.append("This audit asks the core mathematical question directly:")
    lines.append("")
    lines.append("`rating = stimulus_prior + subjective_deviation`")
    lines.append("")
    lines.append("and tests whether the current fixed EEG/EMG feature blocks can predict the subjective deviation/residual.")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(md_table(decision))
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- A successful physiology model must predict the residual/deviation itself, not merely correlate with the original rating.")
    lines.append("- `NO_GO_CURRENT_FIXED_FEATURES_FOR_DIRECT_DEVIATION` means the current engineered EEG/EMG features do not provide a stable, practically useful residual predictor under the current audit.")
    lines.append("- This does **not** prove that EEG/EMG has no usable signal. It says the current fixed-feature route is not sufficient.")
    lines.append("- The next scientific move is either a high-disagreement residual challenge or representation learning from richer EEG/EMG signals.")
    lines.append("")
    lines.append(f"Residual prediction handling: `{residual_note}`")
    lines.append("")
    lines.append("## Direct model metrics")
    lines.append("")
    lines.append(md_table(model_metrics.head(30)))
    lines.append("")
    lines.append("## High-residual subset metrics")
    lines.append("")
    if high.empty:
        lines.append("_High-residual metrics could not be computed from the available prediction schema._\n")
    else:
        lines.append(md_table(high.head(30)))
    lines.append("")
    lines.append("## Feature bottleneck matrix")
    lines.append("")
    lines.append(md_table(feature_bottleneck))
    lines.append("")
    lines.append("## Recommended next steps")
    lines.append("")
    lines.append(md_table(next_steps))
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 05ai completed.")
    for p in [OUT_MD, OUT_JSON, OUT_DECISION, OUT_MODEL_METRICS, OUT_HIGH_RESIDUAL, OUT_FEATURE_BOTTLENECK, OUT_NEXT_STEPS]:
        print(f"wrote: {p}")

    print("\nDecision table:")
    print(decision.to_string(index=False))
    print("\nTop direct model metrics:")
    print(model_metrics.head(20).to_string(index=False))
    if not high.empty:
        print("\nTop high-residual metrics:")
        print(high.head(20).to_string(index=False))
    print("\nNext steps:")
    print(next_steps.to_string(index=False))


if __name__ == "__main__":
    main()
