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
OUT_PREFIX = "idare_representation_learning_feasibility_gate_current"


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


def read_csv_optional(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def read_json_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


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


def first_value(df: pd.DataFrame, col: str, default=None):
    if df.empty or col not in df.columns:
        return default
    s = df[col].dropna()
    if s.empty:
        return default
    return s.iloc[0]


def best_by_target(df: pd.DataFrame, target: str) -> pd.Series | None:
    if df.empty or "target" not in df.columns:
        return None
    g = df[df["target"].astype(str) == target]
    if g.empty:
        return None
    return g.iloc[0]


def yesno(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)) and math.isfinite(float(v)):
        return bool(v)
    return str(v).strip().lower() in {"true", "1", "yes", "go", "pass"}


def main():
    # Core evidence files.
    direction = read_csv_optional(ROCA / "idare_scientific_direction_lock_current_decision_table.csv")
    baselines = read_csv_optional(ROCA / "idare_scientific_direction_lock_current_locked_baselines.csv")
    phys_synth = read_csv_optional(ROCA / "idare_physiology_challenge_synthesis_current_decision_table.csv")
    direct_dev = read_csv_optional(ROCA / "idare_direct_deviation_predictability_audit_current_decision_table.csv")
    high_disagree = read_csv_optional(ROCA / "idare_high_disagreement_direct_deviation_challenge_current_decision_table.csv")
    high_disagree_conf = read_csv_optional(ROCA / "idare_high_disagreement_direct_deviation_confirmatory_stats_current_verdict.csv")
    bridge = read_csv_optional(ROCA / "idare_high_disagreement_personalization_bridge_current_decision_table.csv")
    rescue = read_csv_optional(ROCA / "idare_failure_subject_physiology_rescue_audit_current_decision_table.csv")
    sample_reduction = read_csv_optional(ROCA / "idare_physiology_assisted_calibration_sample_reduction_current_decision_table.csv")
    model_family = read_csv_optional(ROCA / "idare_subject_calibration_model_family_confirmatory_stats_current_verdict.csv")

    targets = sorted(set(
        list(direction["target"].astype(str)) if "target" in direction.columns else []
    ) | set(
        list(sample_reduction["target"].astype(str)) if "target" in sample_reduction.columns else []
    ) | {"arousal", "valence"})

    evidence_rows = []
    decision_rows = []

    for target in targets:
        dir_r = best_by_target(direction, target)
        ps_r = best_by_target(phys_synth, target)
        dd_r = best_by_target(direct_dev, target)
        hd_r = best_by_target(high_disagree, target)
        hdc_r = best_by_target(high_disagree_conf, target)
        br_r = best_by_target(bridge, target)
        re_r = best_by_target(rescue, target)
        sr_r = best_by_target(sample_reduction, target)
        mf_r = best_by_target(model_family, target)

        # Locked baseline.
        b2_rmse = None
        if not baselines.empty:
            b2 = baselines[
                (baselines.get("target", pd.Series(dtype=str)).astype(str) == target)
                & (
                    baselines.get("baseline_level", pd.Series(dtype=str)).astype(str).str.contains("B2", na=False)
                    | baselines.get("baseline_name", pd.Series(dtype=str)).astype(str).str.contains("kernel_residual", na=False)
                )
            ]
            if not b2.empty and "rmse" in b2.columns:
                b2_rmse = safe_float(b2["rmse"].iloc[0])

        fixed_feature_incremental_pass = False
        if ps_r is not None and "passes_incremental_physiology_gate" in ps_r.index:
            fixed_feature_incremental_pass = fixed_feature_incremental_pass or yesno(ps_r["passes_incremental_physiology_gate"])
        if br_r is not None and "passes_bridge_gate" in br_r.index:
            fixed_feature_incremental_pass = fixed_feature_incremental_pass or yesno(br_r["passes_bridge_gate"])
        if re_r is not None and "passes_failure_rescue_gate" in re_r.index:
            fixed_feature_incremental_pass = fixed_feature_incremental_pass or yesno(re_r["passes_failure_rescue_gate"])
        if sr_r is not None and "passes_sample_reduction_gate" in sr_r.index:
            fixed_feature_incremental_pass = fixed_feature_incremental_pass or yesno(sr_r["passes_sample_reduction_gate"])

        high_disagreement_confirmed = False
        high_disagreement_block = None
        high_disagreement_model = None
        high_disagreement_lift = None
        if hdc_r is not None:
            high_disagreement_confirmed = yesno(hdc_r.get("passes_confirmatory_gate", False))
            high_disagreement_block = hdc_r.get("feature_block", None)
            high_disagreement_model = hdc_r.get("model", None)
            high_disagreement_lift = safe_float(hdc_r.get("pooled_lift_vs_zero_residual_rmse", None))

        # Fixed features are considered exhausted when all actionability gates are no-go.
        fixed_feature_actionability_status = (
            "ACTIONABLE_FIXED_FEATURE_ROUTE_EXISTS"
            if fixed_feature_incremental_pass
            else "FIXED_FEATURE_ROUTE_EXHAUSTED_FOR_ACTIONABLE_PERSONALIZATION"
        )

        if high_disagreement_confirmed and not fixed_feature_incremental_pass:
            physiology_signal_status = "DETECTION_SIGNAL_PRESENT_BUT_NOT_ACTIONABLE"
        elif fixed_feature_incremental_pass:
            physiology_signal_status = "ACTIONABLE_FIXED_FEATURE_SIGNAL_PRESENT"
        else:
            physiology_signal_status = "NO_ACTIONABLE_FIXED_FEATURE_SIGNAL"

        representation_gate_decision = (
            "GO_REPRESENTATION_LEARNING_REQUIRED"
            if not fixed_feature_incremental_pass
            else "DEFER_REPRESENTATION_LEARNING_FIXED_FEATURE_GATE_NOT_CLOSED"
        )

        if target == "arousal" and high_disagreement_confirmed and not fixed_feature_incremental_pass:
            recommended_first_experiment = "raw_or_time_frequency_EEG_arousal_high_disagreement_representation"
            rationale = (
                "Arousal has a confirmed high-disagreement EEG-bandpower residual signal, "
                "but direct correction/bridge/rescue/sample-reduction failed. "
                "The next route should learn a representation that can preserve the signal while correcting scale and direction."
            )
        elif not fixed_feature_incremental_pass:
            recommended_first_experiment = "multimodal_EEG_EMG_residual_representation_learning"
            rationale = (
                "Fixed features failed the actionable gates. "
                "The next route should test learned EEG/EMG representations rather than more linear correction on engineered features."
            )
        else:
            recommended_first_experiment = "continue_fixed_feature_refinement"
            rationale = "At least one fixed-feature physiology actionability gate passed."

        evidence_rows.append({
            "target": target,
            "locked_B2_kernel_residual_rmse": b2_rmse,
            "model_family_confirmatory_decision": None if mf_r is None else mf_r.get("decision", None),
            "physiology_vs_locked_status": None if ps_r is None else ps_r.get("final_status", None),
            "direct_deviation_status": None if dd_r is None else dd_r.get("decision", None),
            "high_disagreement_confirmatory_status": None if hdc_r is None else hdc_r.get("decision", None),
            "high_disagreement_confirmed": high_disagreement_confirmed,
            "high_disagreement_feature_block": high_disagreement_block,
            "high_disagreement_model": high_disagreement_model,
            "high_disagreement_lift": high_disagreement_lift,
            "bridge_status": None if br_r is None else br_r.get("decision", None),
            "failure_rescue_status": None if re_r is None else re_r.get("decision", None),
            "sample_reduction_status": None if sr_r is None else sr_r.get("decision", None),
            "sample_reduction_best_lower_k_rmse": None if sr_r is None else safe_float(sr_r.get("best_lower_k_rmse", None)),
            "sample_reduction_delta_vs_locked_B2": None if sr_r is None else safe_float(sr_r.get("pooled_delta_rmse_candidate_minus_locked_B2", None)),
        })

        decision_rows.append({
            "target": target,
            "representation_gate_decision": representation_gate_decision,
            "fixed_feature_actionability_status": fixed_feature_actionability_status,
            "physiology_signal_status": physiology_signal_status,
            "locked_challenge_baseline": "B2_LOCKED_kernel_residual_shrink4_k16",
            "locked_B2_rmse": b2_rmse,
            "positive_signal_to_preserve": (
                f"{high_disagreement_block}/{high_disagreement_model} on high-disagreement residuals"
                if high_disagreement_confirmed
                else "none_confirmed_with_current_fixed_features"
            ),
            "recommended_first_experiment": recommended_first_experiment,
            "interpretation": rationale,
        })

    evidence = pd.DataFrame(evidence_rows)
    decision = pd.DataFrame(decision_rows)

    route_matrix = pd.DataFrame([
        {
            "route": "A_fixed_engineered_features_plus_linear_or_kernel_correction",
            "status": "CLOSED_OR_DEPRIORITIZED",
            "why": "Zero-shot, after-fewshot, locked-baseline bridge, failure-subject rescue, and sample-reduction gates did not pass.",
            "keep": "Use as historical baseline and sanity-check only.",
        },
        {
            "route": "B_high_disagreement_arousal_detection",
            "status": "KEEP_AS_SIGNAL_SOURCE_NOT_DIRECT_CORRECTION",
            "why": "Arousal high-disagreement EEG-bandpower passed confirmatory residual gates, but failed bridge/rescue/sample-reduction actionability.",
            "keep": "Use for gating, uncertainty, curriculum, or targeted representation learning.",
        },
        {
            "route": "C_learned_EEG_or_EMG_representations",
            "status": "NEXT_PRIMARY_ROUTE",
            "why": "The fixed-feature bottleneck is now the most plausible blocker after repeated no-go actionability audits.",
            "keep": "Raw/time-frequency/self-supervised/contrastive subject-adaptive representation learning.",
        },
        {
            "route": "D_cross_dataset_or_pretraining",
            "status": "SECONDARY_SUPPORTING_ROUTE",
            "why": "DEAP has limited per-subject calibration data, so representation learning may need pretraining or external affective physiology data.",
            "keep": "Pretrain on available EEG/EMG datasets, then evaluate under locked I-DARE gates.",
        },
    ])

    success_gates = pd.DataFrame([
        {
            "gate": "G1_locked_personalization_incremental_value",
            "required_for_claim": "Any new EEG/EMG model must beat or complement B2_LOCKED kernel_residual_shrink4 k=16, not merely stimulus-only.",
            "metric": "pooled RMSE lift >= 0.02 plus paired subject CI/sign tests and stable win margin",
        },
        {
            "gate": "G2_high_disagreement_residual_signal",
            "required_for_claim": "If claiming targeted residual learning, evaluate high-disagreement residuals separately.",
            "metric": "positive residual RMSE lift, residual Pearson > 0.1, permutation p < 0.05, paired subject support",
        },
        {
            "gate": "G3_calibration_reduction",
            "required_for_claim": "If claiming practical calibration savings, lower-k model must match locked k=16.",
            "metric": "candidate RMSE within +0.02 of B2 plus subject-level stability",
        },
        {
            "gate": "G4_no_degradation",
            "required_for_claim": "Gating or targeted corrections must not improve one subset by harming pooled performance.",
            "metric": "pooled and paired subject metrics remain non-inferior to B2",
        },
    ])

    experiment_backlog = pd.DataFrame([
        {
            "priority": 1,
            "experiment_id": "06a",
            "title": "Arousal high-disagreement EEG representation prototype",
            "input_representation": "EEG time-frequency tensors or raw/preprocessed EEG segments",
            "model_family": "small CNN/TCN/Transformer encoder with residual head",
            "target": "arousal deviation on high-disagreement trials",
            "evaluation_gate": "G2 then G1",
            "success_condition": "beats fixed EEG-bandpower residual model on high-disagreement arousal and does not degrade locked personalization when used as gate/correction",
        },
        {
            "priority": 2,
            "experiment_id": "06b",
            "title": "Subject-adaptive residual representation",
            "input_representation": "EEG/EMG learned embeddings plus k-shot subject context",
            "model_family": "FiLM/adapters/prototypical or conditional residual head",
            "target": "rating minus stimulus mean / residual correction",
            "evaluation_gate": "G1 and G3",
            "success_condition": "beats B2 locked baseline or matches B2 with fewer calibration samples",
        },
        {
            "priority": 3,
            "experiment_id": "06c",
            "title": "Self-supervised physiology pretraining",
            "input_representation": "raw EEG/EMG or time-frequency windows",
            "model_family": "masked reconstruction, contrastive predictive coding, subject-invariant contrastive learning",
            "target": "pretrained representation for downstream residual/deviation prediction",
            "evaluation_gate": "G1/G2/G3",
            "success_condition": "pretrained representation beats fixed-feature models under locked ROCA gates",
        },
        {
            "priority": 4,
            "experiment_id": "06d",
            "title": "Arousal high-disagreement uncertainty/gating model",
            "input_representation": "confirmed EEG-bandpower signal plus locked model uncertainty/error features",
            "model_family": "risk classifier or mixture-of-experts gate",
            "target": "detect trials where locked personalization is likely wrong",
            "evaluation_gate": "G4",
            "success_condition": "improves high-disagreement arousal triage without worsening pooled RMSE",
        },
    ])

    artifact = {
        "step": "05an",
        "title": "I-DARE representation-learning feasibility gate",
        "summary_decision": clean_json(decision.to_dict(orient="records")),
        "evidence_rollup": clean_json(evidence.to_dict(orient="records")),
        "route_matrix": clean_json(route_matrix.to_dict(orient="records")),
        "success_gates": clean_json(success_gates.to_dict(orient="records")),
        "experiment_backlog": clean_json(experiment_backlog.to_dict(orient="records")),
        "interpretation": (
            "Fixed engineered EEG/EMG features have not produced actionable residual learning under locked personalization gates. "
            "The next scientifically justified route is learned physiology representation, with arousal high-disagreement EEG signal preserved as a targeted entry point."
        ),
    }

    out = ROCA / OUT_PREFIX
    paths = {
        "md": out.with_suffix(".md"),
        "json": out.with_suffix(".json"),
        "decision": Path(str(out) + "_decision_table.csv"),
        "evidence": Path(str(out) + "_evidence_rollup.csv"),
        "route_matrix": Path(str(out) + "_route_matrix.csv"),
        "success_gates": Path(str(out) + "_success_gates.csv"),
        "experiment_backlog": Path(str(out) + "_experiment_backlog.csv"),
    }

    decision.to_csv(paths["decision"], index=False)
    evidence.to_csv(paths["evidence"], index=False)
    route_matrix.to_csv(paths["route_matrix"], index=False)
    success_gates.to_csv(paths["success_gates"], index=False)
    experiment_backlog.to_csv(paths["experiment_backlog"], index=False)
    paths["json"].write_text(json.dumps(clean_json(artifact), indent=2), encoding="utf-8")

    lines = []
    lines.append("# I-DARE Representation-Learning Feasibility Gate\n\n")
    lines.append("This document closes the current fixed engineered EEG/EMG feature route for actionable personalization, while preserving the confirmed arousal high-disagreement EEG signal as a useful starting point for learned representations.\n\n")
    lines.append("## Decision table\n\n")
    lines.append(md_table(decision))
    lines.append("\n## Evidence rollup\n\n")
    lines.append(md_table(evidence))
    lines.append("\n## Route matrix\n\n")
    lines.append(md_table(route_matrix))
    lines.append("\n## Success gates for future EEG/EMG claims\n\n")
    lines.append(md_table(success_gates))
    lines.append("\n## Experiment backlog\n\n")
    lines.append(md_table(experiment_backlog))
    lines.append("\n## Bottom line\n\n")
    lines.append("The current fixed-feature EEG/EMG route should not be used for new success claims unless it beats the locked B2 personalization baseline. The next primary scientific route is representation learning: raw/time-frequency EEG/EMG encoders, self-supervised pretraining, subject-adaptive residual heads, and targeted arousal high-disagreement gating.\n")
    paths["md"].write_text("".join(lines), encoding="utf-8")

    print("ROCA step 05an completed.")
    for p in paths.values():
        print(f"wrote: {p}")

    print("\nDecision table:")
    print(decision.to_string(index=False))

    print("\nRoute matrix:")
    print(route_matrix.to_string(index=False))

    print("\nExperiment backlog:")
    print(experiment_backlog.to_string(index=False))

    print("\n================== KEY OUTPUTS ==================")
    print(paths["decision"].read_text(encoding="utf-8").strip())
    print()
    print(paths["experiment_backlog"].read_text(encoding="utf-8").strip())

    print("\n================== SIZE CHECK ==================")
    for p in sorted(paths.values(), key=lambda x: x.stat().st_size if x.exists() else 0):
        if p.exists():
            print(f"{p.stat().st_size/1024:.1f}K\t{p}")


if __name__ == "__main__":
    main()
