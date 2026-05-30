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
OUT_PREFIX = "idare_scientific_direction_lock_current"

FILES = {
    "residual_reliability_verdict": ROCA / "idare_residual_signal_reliability_audit_current_verdict.csv",
    "zero_shot_physio_verdict": ROCA / "idare_residual_physiology_confirmatory_stats_current_verdict.csv",
    "fewshot_verdict": ROCA / "idare_fewshot_calibration_confirmatory_stats_current_verdict.csv",
    "physio_after_fewshot_verdict": ROCA / "idare_physiology_after_fewshot_audit_current_verdict.csv",
    "model_family_confirmatory_verdict": ROCA / "idare_subject_calibration_model_family_confirmatory_stats_current_verdict.csv",
    "personalization_decision": ROCA / "idare_personalization_decision_synthesis_current_decision_table.csv",
    "personalization_evidence": ROCA / "idare_personalization_decision_synthesis_current_evidence_table.csv",
}

OUT_MD = ROCA / f"{OUT_PREFIX}.md"
OUT_JSON = ROCA / f"{OUT_PREFIX}.json"
OUT_DECISION = ROCA / f"{OUT_PREFIX}_decision_table.csv"
OUT_BASELINES = ROCA / f"{OUT_PREFIX}_locked_baselines.csv"
OUT_CHALLENGE = ROCA / f"{OUT_PREFIX}_physiology_challenge_matrix.csv"
OUT_NEXT = ROCA / f"{OUT_PREFIX}_next_steps.csv"
OUT_EVIDENCE = ROCA / f"{OUT_PREFIX}_evidence_rollup.csv"


def read_csv(path: Path, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Missing required input: {path}")
        return pd.DataFrame()
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
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        v = float(x)
        return v if math.isfinite(v) else None
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    try:
        if bool(pd.isna(x)):
            return None
    except Exception:
        pass
    return x


def md_cell(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6f}" if math.isfinite(v) else ""
    try:
        if bool(pd.isna(v)):
            return ""
    except Exception:
        pass
    return str(v).replace("|", "\\|").replace("\n", " ")


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_No rows._\n"
    cols = list(df.columns)
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(md_cell(row[c]) for c in cols) + " |")
    return "\n".join(lines) + "\n"


def first_row(df: pd.DataFrame, target: str) -> dict[str, Any]:
    if df.empty or "target" not in df.columns:
        return {}
    hit = df[df["target"].astype(str).eq(target)]
    if hit.empty:
        return {}
    return hit.iloc[0].to_dict()


def main() -> None:
    residual = read_csv(FILES["residual_reliability_verdict"])
    zero = read_csv(FILES["zero_shot_physio_verdict"])
    fewshot = read_csv(FILES["fewshot_verdict"])
    phys_after = read_csv(FILES["physio_after_fewshot_verdict"])
    mf_conf = read_csv(FILES["model_family_confirmatory_verdict"])
    personal_decision = read_csv(FILES["personalization_decision"], required=False)
    personal_evidence = read_csv(FILES["personalization_evidence"], required=False)

    targets = sorted(set(residual["target"].astype(str)) | set(fewshot["target"].astype(str)) | set(mf_conf["target"].astype(str)))

    decision_rows: list[dict[str, Any]] = []
    baseline_rows: list[dict[str, Any]] = []
    challenge_rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []

    for target in targets:
        r = first_row(residual, target)
        z = first_row(zero, target)
        f = first_row(fewshot, target)
        p = first_row(phys_after, target)
        c = first_row(mf_conf, target)
        pd_row = first_row(personal_decision, target)
        pe = first_row(personal_evidence, target)

        best_model = str(c.get("best_candidate_model", "") or "")
        best_k = safe_float(c.get("best_k_calibration"))
        locked_ref = str(c.get("locked_reference_model", "") or "")
        best_rmse = safe_float(c.get("best_rmse"))
        locked_rmse = safe_float(c.get("locked_reference_rmse"))
        lift_locked = safe_float(c.get("best_lift_vs_locked_reference_rmse"))
        lift_stimulus = safe_float(c.get("best_lift_vs_stimulus_rmse"))
        ci_low = safe_float(c.get("ci95_low_mean_subject_improvement"))
        pval = safe_float(c.get("signflip_p_one_sided_mean_gt_zero"))
        wins = safe_float(c.get("wins"))
        losses = safe_float(c.get("losses"))
        margin = safe_float(c.get("win_margin"))
        pass_raw = c.get("confirmatory_pass", False)
        confirmed = str(pass_raw).lower() == "true" or str(c.get("decision", "")).startswith("GO_")

        residual_verdict = str(r.get("residual_signal_verdict", ""))
        zero_verdict = str(z.get("confirmatory_verdict", ""))
        fewshot_decision = str(f.get("decision", ""))
        phys_after_decision = str(p.get("decision", ""))
        mf_decision = str(c.get("decision", ""))

        if confirmed and best_model:
            final_direction = "LOCK_PERSONALIZED_KERNEL_RESIDUAL_BASELINE"
            physiology_claim_status = "PHYSIOLOGY_MUST_BEAT_LOCKED_PERSONALIZATION_BASELINE"
            next_focus = "05ah physiology-informed personalization challenge against locked kernel baseline"
            interpretation = (
                "A personalized residual model is now the strongest confirmed baseline. "
                "EEG/EMG is still central to the project, but future physiology claims must show incremental value "
                "over this locked subject-calibration baseline, not merely over stimulus_only."
            )
        else:
            final_direction = "PERSONALIZATION_PROMISING_BUT_NOT_LOCKED"
            physiology_claim_status = "DO_NOT_CLAIM_PHYSIOLOGY_INCREMENT_YET"
            next_focus = "Repeat model-family confirmation or inspect instability before physiology challenge."
            interpretation = (
                "The personalization route is promising but not sufficiently locked. "
                "Do not start new physiology claims until the baseline is stable."
            )

        decision_rows.append({
            "target": target,
            "final_direction": final_direction,
            "residual_signal_verdict": residual_verdict,
            "zero_shot_physiology_verdict": zero_verdict,
            "fewshot_decision": fewshot_decision,
            "physiology_after_fewshot_decision": phys_after_decision,
            "model_family_confirmatory_decision": mf_decision,
            "locked_best_model": best_model,
            "locked_k_calibration": best_k,
            "locked_reference_model": locked_ref,
            "locked_best_rmse": best_rmse,
            "locked_reference_rmse": locked_rmse,
            "locked_lift_vs_reference_rmse": lift_locked,
            "locked_lift_vs_stimulus_rmse": lift_stimulus,
            "paired_ci95_low": ci_low,
            "paired_signflip_p": pval,
            "wins": wins,
            "losses": losses,
            "win_margin": margin,
            "physiology_claim_status": physiology_claim_status,
            "recommended_next_focus": next_focus,
            "interpretation": interpretation,
        })

        stimulus_historical_rmse = safe_float(r.get("residual_std"))

        baseline_rows.extend([
            {
                "target": target,
                "baseline_level": "B0",
                "baseline_name": "stimulus_only",
                "status": "historical_reference_only",
                "rmse": stimulus_historical_rmse,
                "how_to_use": "Do not claim physiology success by beating this alone.",
            },
            {
                "target": target,
                "baseline_level": "B1",
                "baseline_name": str(f.get("best_model", "")),
                "status": str(f.get("decision", "")),
                "rmse": safe_float(f.get("best_rmse")),
                "how_to_use": "Few-shot subject calibration reference.",
            },
            {
                "target": target,
                "baseline_level": "B2_LOCKED",
                "baseline_name": best_model,
                "status": str(c.get("decision", "")),
                "rmse": best_rmse,
                "how_to_use": "Locked challenge baseline for future EEG/EMG or multimodal personalization claims.",
            },
        ])

        challenge_rows.extend([
            {
                "target": target,
                "challenge": "C1_physio_moderator_over_locked_baseline",
                "required_comparator": best_model,
                "required_k": best_k,
                "minimum_evidence": "positive pooled RMSE lift + positive paired subject mean + CI low > 0 + signflip p < 0.05 + win margin > 3",
                "success_interpretation": "EEG/EMG provides incremental personalization value beyond subject residual calibration.",
                "failure_interpretation": "EEG/EMG does not add measurable value beyond the locked personalized baseline under this protocol.",
            },
            {
                "target": target,
                "challenge": "C2_reduce_calibration_samples",
                "required_comparator": f"{best_model} at k=16",
                "required_k": "1,2,4,8",
                "minimum_evidence": "physiology-assisted model at smaller k matches or beats locked k=16 baseline with paired evidence",
                "success_interpretation": "EEG/EMG is useful by lowering calibration burden.",
                "failure_interpretation": "Personalization still depends mainly on explicit subject calibration samples.",
            },
            {
                "target": target,
                "challenge": "C3_rescue_failure_subjects",
                "required_comparator": best_model,
                "required_k": best_k,
                "minimum_evidence": "improvement concentrated in locked-baseline failure subjects without pooled regression",
                "success_interpretation": "EEG/EMG helps specific subjects even if global average lift is modest.",
                "failure_interpretation": "Physiology features are not explaining current failure modes.",
            },
        ])

        evidence_rows.append({
            "target": target,
            "subject_r2_on_residual": safe_float(r.get("subject_r2_on_residual")),
            "stimulus_r2_on_residual": safe_float(r.get("stimulus_r2_on_residual")),
            "subject_split_half_pearson_median": safe_float(r.get("subject_split_half_pearson_median")),
            "zero_shot_best_candidate_pooled_lift": safe_float(z.get("best_candidate_pooled_lift_vs_stimulus_rmse")),
            "fewshot_best_lift_vs_stimulus": safe_float(f.get("best_lift_vs_stimulus_rmse")),
            "fewshot_mean_subject_improvement": safe_float(f.get("mean_subject_rmse_improvement")),
            "phys_after_fewshot_best_lift": safe_float(p.get("best_lift_vs_fewshot_rmse")),
            "model_family_lift_vs_locked": lift_locked,
            "model_family_ci95_low": ci_low,
            "model_family_signflip_p": pval,
            "model_family_win_margin": margin,
            "personalization_prior_decision": str(pd_row.get("final_decision", "")),
            "personalization_prior_fewshot_best_k": safe_float(pe.get("fewshot_best_k")),
        })

    decision = pd.DataFrame(decision_rows)
    baselines = pd.DataFrame(baseline_rows)
    challenge = pd.DataFrame(challenge_rows)
    evidence = pd.DataFrame(evidence_rows)

    next_steps = pd.DataFrame([
        {
            "step": "05ah",
            "title": "Physiology-informed personalization challenge",
            "purpose": "Test whether EEG/EMG improves over the locked kernel_residual_shrink4 personalization baseline.",
            "why_now": "05af confirms the personalization baseline; the next physiology test must be stricter and targeted.",
            "success_condition": "EEG/EMG model beats locked B2 baseline with paired subject-level confirmatory evidence.",
        },
        {
            "step": "05ai",
            "title": "Calibration-sample reduction audit",
            "purpose": "Test whether EEG/EMG reduces required calibration samples, e.g. k=4 or k=8 matching k=16 personalization.",
            "why_now": "Even if EEG/EMG does not improve final RMSE, it may be valuable if it reduces subject calibration burden.",
            "success_condition": "Physiology-assisted lower-k model matches or beats locked k=16 baseline without subject-level instability.",
        },
        {
            "step": "05aj",
            "title": "Failure-subject physiology rescue audit",
            "purpose": "Focus on subjects where locked personalization still regresses and test whether physiology explains those failures.",
            "why_now": "05af failure subjects define the most scientifically useful error surface.",
            "success_condition": "Physiology improves failure-subject RMSE while preserving pooled and paired metrics.",
        },
    ])

    decision.to_csv(OUT_DECISION, index=False)
    baselines.to_csv(OUT_BASELINES, index=False)
    challenge.to_csv(OUT_CHALLENGE, index=False)
    next_steps.to_csv(OUT_NEXT, index=False)
    evidence.to_csv(OUT_EVIDENCE, index=False)

    payload = {
        "out_prefix": OUT_PREFIX,
        "inputs": {k: str(v) for k, v in FILES.items()},
        "outputs": {
            "md": str(OUT_MD),
            "json": str(OUT_JSON),
            "decision": str(OUT_DECISION),
            "locked_baselines": str(OUT_BASELINES),
            "physiology_challenge_matrix": str(OUT_CHALLENGE),
            "next_steps": str(OUT_NEXT),
            "evidence_rollup": str(OUT_EVIDENCE),
        },
        "decision_table": decision.to_dict(orient="records"),
        "locked_baselines": baselines.to_dict(orient="records"),
        "physiology_challenge_matrix": challenge.to_dict(orient="records"),
        "next_steps": next_steps.to_dict(orient="records"),
        "evidence_rollup": evidence.to_dict(orient="records"),
        "claim_lock": {
            "current_scientific_direction": "Personalization-first emotion recognition with physiology as an incremental moderator/challenge, not as an unconstrained zero-shot decoder.",
            "locked_baseline_for_future_physio_claims": "kernel_residual_shrink4 at k=16.",
            "forbidden_claim": "Do not claim EEG/EMG success merely because it beats stimulus_only.",
            "required_claim": "EEG/EMG must beat the locked personalized baseline or reduce calibration burden with paired subject-level evidence.",
        },
    }
    OUT_JSON.write_text(json.dumps(clean_json(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines: list[str] = []
    lines.append("# I-DARE Scientific Direction Lock")
    lines.append("")
    lines.append("This report locks the current scientific direction after the residual reliability, physiology, few-shot, and model-family audits.")
    lines.append("")
    lines.append("## Current claim lock")
    lines.append("")
    lines.append("- The project is still aiming for EEG/EMG value, but EEG/EMG must now beat a stronger personalized baseline, not just `stimulus_only`.")
    lines.append("- `stimulus_only` is now a historical reference, not the final comparator for physiology claims.")
    lines.append("- The currently locked baseline is `kernel_residual_shrink4` with `k=16` calibration trials.")
    lines.append("- Future physiology work should test EEG/EMG as a personalization moderator, calibration-sample reducer, or failure-subject rescue signal.")
    lines.append("")
    lines.append("## Decision table")
    lines.append("")
    lines.append(md_table(decision))
    lines.append("")
    lines.append("## Locked baselines")
    lines.append("")
    lines.append(md_table(baselines))
    lines.append("")
    lines.append("## Evidence rollup")
    lines.append("")
    lines.append(md_table(evidence))
    lines.append("")
    lines.append("## Physiology challenge matrix")
    lines.append("")
    lines.append(md_table(challenge))
    lines.append("")
    lines.append("## Recommended next steps")
    lines.append("")
    lines.append(md_table(next_steps))
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The result is not a retreat from EEG/EMG. It is a stricter scientific framing: EEG/EMG should be evaluated only after locking the strongest non-physiology personalization baseline. If physiology can beat this baseline, reduce the calibration burden, or rescue failure subjects, the project has a stronger and more defensible claim.")
    lines.append("")
    lines.append("## Practical next action")
    lines.append("")
    lines.append("Build `05ah`: a physiology-informed personalization challenge against the locked `kernel_residual_shrink4, k=16` baseline, with paired subject-level confirmatory statistics and no huge prediction dumps committed.")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 05ag completed.")
    for pth in [OUT_MD, OUT_JSON, OUT_DECISION, OUT_BASELINES, OUT_CHALLENGE, OUT_NEXT, OUT_EVIDENCE]:
        print(f"wrote: {pth}")

    print("\nDecision table:")
    print(decision.to_string(index=False))

    print("\nLocked baselines:")
    print(baselines.to_string(index=False))

    print("\nNext steps:")
    print(next_steps.to_string(index=False))


if __name__ == "__main__":
    main()
