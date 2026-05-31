#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROCA = ROOT / "docs" / "roca"

OUT_PREFIX = "idare_physiology_challenge_synthesis_current"

SCIENTIFIC_LOCK_DECISION = ROCA / "idare_scientific_direction_lock_current_decision_table.csv"
SCIENTIFIC_LOCK_BASELINES = ROCA / "idare_scientific_direction_lock_current_locked_baselines.csv"
MODEL_FAMILY_CONFIRM = ROCA / "idare_subject_calibration_model_family_confirmatory_stats_current_verdict.csv"
PHYS_GPU_VERDICT = ROCA / "idare_physiology_informed_personalization_challenge_gpu_current_verdict.csv"
PHYS_GPU_RANKING = ROCA / "idare_physiology_informed_personalization_challenge_gpu_current_best_ranking.csv"

OUT_MD = ROCA / f"{OUT_PREFIX}.md"
OUT_JSON = ROCA / f"{OUT_PREFIX}.json"
OUT_DECISION = ROCA / f"{OUT_PREFIX}_decision_table.csv"
OUT_EVIDENCE = ROCA / f"{OUT_PREFIX}_evidence_table.csv"
OUT_NEXT = ROCA / f"{OUT_PREFIX}_next_questions.csv"

PRACTICAL_INCREMENTAL_RMSE_LIFT = 0.02
MIN_WIN_MARGIN = 3


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required input not found: {path}")
    return pd.read_csv(path)


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
    if hasattr(x, "item"):
        return clean_json(x.item())
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    return x


def md_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    """Render a simple GitHub-flavored markdown table without optional tabulate."""
    if df.empty:
        return "_No rows._\n"
    x = df.copy()
    if max_rows is not None:
        x = x.head(max_rows)

    def fmt(v: Any) -> str:
        if pd.isna(v):
            return ""
        if isinstance(v, float):
            return f"{v:.6f}"
        text = str(v)
        return text.replace("|", "\\|").replace("\n", " ")

    cols = [str(c) for c in x.columns]
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in x.iterrows():
        lines.append("| " + " | ".join(fmt(row[c]) for c in x.columns) + " |")
    return "\n".join(lines) + "\n"


def as_target_map(df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    out = {}
    for _, row in df.iterrows():
        if "target" in row and pd.notna(row["target"]):
            out[str(row["target"])] = row.to_dict()
    return out


def main() -> None:
    lock_decision = read_csv(SCIENTIFIC_LOCK_DECISION)
    locked_baselines = read_csv(SCIENTIFIC_LOCK_BASELINES)
    model_family = read_csv(MODEL_FAMILY_CONFIRM)
    phys_gpu = read_csv(PHYS_GPU_VERDICT)
    phys_ranking = read_csv(PHYS_GPU_RANKING)

    lock_by_target = as_target_map(lock_decision)
    mf_by_target = as_target_map(model_family)
    phys_by_target = as_target_map(phys_gpu)

    evidence_rows = []
    decision_rows = []

    for target in sorted(set(lock_by_target) | set(mf_by_target) | set(phys_by_target)):
        mf = mf_by_target.get(target, {})
        phys = phys_by_target.get(target, {})

        b0 = locked_baselines[
            (locked_baselines["target"].astype(str) == target)
            & (locked_baselines["baseline_level"].astype(str) == "B0")
        ]
        b1 = locked_baselines[
            (locked_baselines["target"].astype(str) == target)
            & (locked_baselines["baseline_level"].astype(str) == "B1")
        ]
        b2 = locked_baselines[
            (locked_baselines["target"].astype(str) == target)
            & (locked_baselines["baseline_level"].astype(str) == "B2_LOCKED")
        ]

        stimulus_rmse = safe_float(b0.iloc[0]["rmse"]) if not b0.empty else None
        fewshot_rmse = safe_float(b1.iloc[0]["rmse"]) if not b1.empty else None
        locked_rmse = safe_float(b2.iloc[0]["rmse"]) if not b2.empty else safe_float(mf.get("best_rmse"))

        phys_best_rmse = safe_float(phys.get("best_rmse"))
        phys_locked_rmse = safe_float(phys.get("locked_reference_rmse"))
        phys_lift = safe_float(phys.get("best_lift_vs_locked_rmse"))
        phys_win_margin = safe_float(phys.get("rmse_win_margin_vs_locked"))
        phys_mean_delta = safe_float(phys.get("mean_delta_rmse_model_minus_locked"))

        passes_incremental = (
            phys_lift is not None
            and phys_win_margin is not None
            and phys_mean_delta is not None
            and phys_lift >= PRACTICAL_INCREMENTAL_RMSE_LIFT
            and phys_win_margin >= MIN_WIN_MARGIN
            and phys_mean_delta < 0
        )

        if passes_incremental:
            final_status = "PHYSIOLOGY_ADDS_VALUE_OVER_LOCKED_PERSONALIZATION"
            interpretation = (
                "EEG/EMG adds incremental value beyond the locked personalized baseline "
                "under the current challenge criteria."
            )
        else:
            final_status = "CURRENT_PHYSIOLOGY_NO_GO_AGAINST_LOCKED_PERSONALIZATION"
            interpretation = (
                "Current fixed EEG/EMG feature blocks and the tested physiology-informed models "
                "do not add incremental value over the locked personalized kernel residual baseline. "
                "This does not prove physiology is useless; it says the current representation/modeling "
                "route is not sufficient."
            )

        evidence_rows.append({
            "target": target,
            "stimulus_only_rmse_B0": stimulus_rmse,
            "fewshot_bias_shrink4_rmse_B1": fewshot_rmse,
            "locked_kernel_residual_rmse_B2": locked_rmse,
            "model_family_confirmatory_decision": mf.get("decision"),
            "physiology_gpu_decision": phys.get("decision"),
            "physiology_best_block": phys.get("best_block"),
            "physiology_best_model": phys.get("best_model"),
            "physiology_best_k": safe_float(phys.get("best_k_calibration")),
            "physiology_best_rmse": phys_best_rmse,
            "physiology_locked_reference_rmse": phys_locked_rmse,
            "physiology_lift_vs_locked_rmse": phys_lift,
            "physiology_win_margin_vs_locked": phys_win_margin,
            "physiology_mean_delta_model_minus_locked": phys_mean_delta,
        })

        decision_rows.append({
            "target": target,
            "final_status": final_status,
            "locked_baseline": "B2_LOCKED_kernel_residual_shrink4",
            "locked_baseline_rmse": locked_rmse,
            "best_physiology_model": phys.get("best_model"),
            "best_physiology_block": phys.get("best_block"),
            "best_physiology_k": safe_float(phys.get("best_k_calibration")),
            "best_physiology_rmse": phys_best_rmse,
            "lift_vs_locked_rmse": phys_lift,
            "win_margin_vs_locked": phys_win_margin,
            "mean_delta_rmse_model_minus_locked": phys_mean_delta,
            "passes_incremental_physiology_gate": bool(passes_incremental),
            "interpretation": interpretation,
        })

    decision = pd.DataFrame(decision_rows)
    evidence = pd.DataFrame(evidence_rows)

    ranking_cols = [
        "target", "block", "k_calibration", "model", "rmse",
        "locked_reference_rmse", "lift_vs_locked_rmse",
        "rmse_win_margin_vs_locked", "mean_delta_rmse_model_minus_locked",
        "pearson", "ccc",
    ]
    ranking_preview = phys_ranking[[c for c in ranking_cols if c in phys_ranking.columns]].copy()
    if not ranking_preview.empty:
        ranking_preview = ranking_preview.sort_values(
            ["target", "lift_vs_locked_rmse", "rmse"],
            ascending=[True, False, True],
        ).groupby("target", as_index=False).head(10)

    next_questions = pd.DataFrame([
        {
            "priority": 1,
            "question": "Can physiology predict individual deviation directly?",
            "audit": "direct_deviation_predictability_audit",
            "purpose": "Model rating - stimulus_mean directly, especially on high-disagreement stimuli.",
            "success_condition": "EEG/EMG or EEG+EMG predicts deviation above locked non-physiology baselines with paired subject-level support.",
        },
        {
            "priority": 2,
            "question": "Can physiology reduce calibration burden?",
            "audit": "calibration_sample_reduction_challenge",
            "purpose": "Test whether physiology-assisted k=4 or k=8 can match locked k=16 personalization.",
            "success_condition": "Lower-k physiology-assisted model matches or beats B2 locked k=16 without subject-level instability.",
        },
        {
            "priority": 3,
            "question": "Can physiology rescue failure subjects?",
            "audit": "failure_subject_physiology_rescue",
            "purpose": "Focus on subjects where locked personalization still regresses.",
            "success_condition": "Physiology improves failure-subject RMSE while preserving pooled metrics.",
        },
        {
            "priority": 4,
            "question": "Are current hand-crafted EEG/EMG features the bottleneck?",
            "audit": "representation_learning_plan",
            "purpose": "If direct deviation remains no-go, move from fixed features to learned representations.",
            "success_condition": "Feature-learning method beats fixed-feature physiology against the locked challenge baseline.",
        },
    ])

    OUT_DECISION.parent.mkdir(parents=True, exist_ok=True)
    decision.to_csv(OUT_DECISION, index=False)
    evidence.to_csv(OUT_EVIDENCE, index=False)
    next_questions.to_csv(OUT_NEXT, index=False)

    payload = {
        "inputs": {
            "scientific_lock_decision": str(SCIENTIFIC_LOCK_DECISION),
            "scientific_lock_baselines": str(SCIENTIFIC_LOCK_BASELINES),
            "model_family_confirmatory": str(MODEL_FAMILY_CONFIRM),
            "physiology_gpu_verdict": str(PHYS_GPU_VERDICT),
            "physiology_gpu_ranking": str(PHYS_GPU_RANKING),
        },
        "criteria": {
            "practical_incremental_rmse_lift": PRACTICAL_INCREMENTAL_RMSE_LIFT,
            "min_win_margin": MIN_WIN_MARGIN,
            "mean_delta_rmse_model_minus_locked_must_be_negative": True,
        },
        "decision": decision.to_dict(orient="records"),
        "evidence": evidence.to_dict(orient="records"),
        "next_questions": next_questions.to_dict(orient="records"),
    }
    OUT_JSON.write_text(json.dumps(clean_json(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("# I-DARE Physiology Challenge Synthesis\n")
    lines.append(
        "This synthesis closes the previous 05ah GPU physiology-informed personalization challenge. "
        "The locked comparison is no longer `stimulus_only`; it is the personalized `kernel_residual_shrink4` baseline.\n"
    )

    lines.append("## Final decision\n")
    lines.append(md_table(decision))

    lines.append("\n## Evidence table\n")
    lines.append(md_table(evidence))

    lines.append("\n## Closest physiology-informed rows from 05ah GPU\n")
    lines.append(md_table(ranking_preview, max_rows=20))

    lines.append("\n## Interpretation\n")
    lines.append(
        "- The strongest confirmed non-physiology baseline is `B2_LOCKED = kernel_residual_shrink4`.\n"
        "- Current EEG/EMG feature blocks did not beat this locked personalized baseline.\n"
        "- Therefore, physiology is still scientifically central, but the next claim must be stricter: "
        "EEG/EMG must predict subject-specific deviation or reduce calibration burden beyond B2.\n"
        "- This result points to two likely bottlenecks: either the current fixed EEG/EMG features are insufficient, "
        "or the current adaptation/calibration formulation is not extracting the right subject-specific signal.\n"
    )

    lines.append("\n## Next questions\n")
    lines.append(md_table(next_questions))

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 05ahx completed.")
    for p in [OUT_MD, OUT_JSON, OUT_DECISION, OUT_EVIDENCE, OUT_NEXT]:
        print(f"wrote: {p}")

    print("\nDecision table:")
    print(decision.to_string(index=False))

    print("\nEvidence table:")
    print(evidence.to_string(index=False))

    print("\nNext questions:")
    print(next_questions.to_string(index=False))


if __name__ == "__main__":
    main()
