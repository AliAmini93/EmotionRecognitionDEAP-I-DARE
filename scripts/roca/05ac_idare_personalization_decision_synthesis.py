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
OUT_PREFIX = "idare_personalization_decision_synthesis_current"

INPUTS = {
    "residual_signal_verdict": ROCA / "idare_residual_signal_reliability_audit_current_verdict.csv",
    "residual_signal_effects": ROCA / "idare_residual_signal_reliability_audit_current_residual_effects.csv",
    "confirmatory_physio_verdict": ROCA / "idare_residual_physiology_confirmatory_stats_current_verdict.csv",
    "fewshot_verdict": ROCA / "idare_fewshot_residual_calibration_audit_current_verdict.csv",
    "fewshot_main": ROCA / "idare_fewshot_residual_calibration_audit_current_main_metrics.csv",
    "fewshot_winloss": ROCA / "idare_fewshot_residual_calibration_audit_current_subject_winloss.csv",
    "phys_after_fewshot_verdict": ROCA / "idare_physiology_after_fewshot_audit_current_verdict.csv",
    "phys_after_fewshot_best": ROCA / "idare_physiology_after_fewshot_audit_current_best_ranking.csv",
    "prior_baselines": ROCA / "prior_baselines_no_global_current_main_metrics.csv",
    "audit_main": ROCA / "idare_residual_physiology_feature_audit_current_main_metrics.csv",
}

OUT_MD = ROCA / f"{OUT_PREFIX}.md"
OUT_JSON = ROCA / f"{OUT_PREFIX}.json"
OUT_DECISION = ROCA / f"{OUT_PREFIX}_decision_table.csv"
OUT_EVIDENCE = ROCA / f"{OUT_PREFIX}_evidence_table.csv"
OUT_NEXT = ROCA / f"{OUT_PREFIX}_next_steps.csv"


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


def read_csv(path: Path, required: bool = True) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return pd.DataFrame()
    return pd.read_csv(path)


def fmt(x: Any, nd: int = 4) -> str:
    if x is None:
        return ""
    try:
        if pd.isna(x):
            return ""
    except Exception:
        pass
    if isinstance(x, (float, np.floating)):
        return f"{float(x):.{nd}f}"
    return str(x)


def md_table(df: pd.DataFrame, cols: list[str] | None = None, max_rows: int | None = None) -> str:
    if df is None or df.empty:
        return "_No rows._\n"
    if cols is not None:
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
    if max_rows is not None:
        df = df.head(max_rows)
    lines = []
    lines.append("| " + " | ".join(df.columns) + " |")
    lines.append("| " + " | ".join(["---"] * len(df.columns)) + " |")
    for _, row in df.iterrows():
        vals = []
        for c in df.columns:
            vals.append(fmt(row[c]).replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def first_row(df: pd.DataFrame, target: str) -> pd.Series:
    g = df[df["target"].eq(target)] if "target" in df.columns else pd.DataFrame()
    return g.iloc[0] if not g.empty else pd.Series(dtype=object)


def main():
    ROCA.mkdir(parents=True, exist_ok=True)

    residual = read_csv(INPUTS["residual_signal_verdict"])
    effects = read_csv(INPUTS["residual_signal_effects"])
    phys0 = read_csv(INPUTS["confirmatory_physio_verdict"])
    fewshot_v = read_csv(INPUTS["fewshot_verdict"])
    fewshot_main = read_csv(INPUTS["fewshot_main"])
    fewshot_wins = read_csv(INPUTS["fewshot_winloss"])
    after_v = read_csv(INPUTS["phys_after_fewshot_verdict"])
    after_best = read_csv(INPUTS["phys_after_fewshot_best"])
    prior = read_csv(INPUTS["prior_baselines"], required=False)
    audit_main = read_csv(INPUTS["audit_main"], required=False)

    targets = sorted(set(residual["target"]).union(set(fewshot_v["target"])).union(set(after_v["target"])))

    decision_rows = []
    evidence_rows = []
    for target in targets:
        r = first_row(residual, target)
        eff = first_row(effects, target)
        p0 = first_row(phys0, target)
        fs = first_row(fewshot_v, target)
        pa = first_row(after_v, target)

        residual_structured = bool(r.get("few_shot_or_subject_calibration_plausible", False))
        zero_shot_no_go = "NO_GO" in str(p0.get("confirmatory_verdict", ""))
        fewshot_decision = str(fs.get("decision", ""))
        fewshot_go = fewshot_decision.startswith("GO") or fewshot_decision.startswith("WEAK_GO")
        phys_after_no_go = "NO_GO" in str(pa.get("decision", ""))

        if residual_structured and zero_shot_no_go and fewshot_go and phys_after_no_go:
            final = "PIVOT_TO_PERSONALIZATION_FEWSHOT"
            next_action = "Build 05ad few-shot calibration confirmatory/stability audit before any new physiology or architecture search."
        elif residual_structured and zero_shot_no_go and not fewshot_go:
            final = "RESIDUAL_STRUCTURED_BUT_NO_WORKING_MODEL_YET"
            next_action = "Explore stronger subject calibration/domain adaptation."
        elif not residual_structured:
            final = "NO_RELIABLE_RESIDUAL_STRUCTURE"
            next_action = "Stop residual modeling and write up the stimulus-prior finding."
        else:
            final = "REVIEW_MANUALLY"
            next_action = "Inspect inconsistent evidence."

        interpretation = (
            "Residual structure appears mainly subject-specific. Current zero-shot physiology features do not beat stimulus-only, "
            "and physiology does not add value after few-shot calibration. Future claims should compare against a locked few-shot baseline."
        )

        decision_rows.append({
            "target": target,
            "final_decision": final,
            "residual_signal_verdict": r.get("residual_signal_verdict"),
            "zero_shot_physiology_verdict": p0.get("confirmatory_verdict"),
            "fewshot_decision": fewshot_decision,
            "physiology_after_fewshot_decision": pa.get("decision"),
            "recommended_next_action": next_action,
            "interpretation": interpretation,
        })

        evidence_rows.append({
            "target": target,
            "subject_r2_on_residual": safe_float(eff.get("subject_r2_on_residual")),
            "stimulus_r2_on_residual": safe_float(eff.get("stimulus_r2_on_residual")),
            "subject_split_half_pearson_median": safe_float(r.get("subject_split_half_pearson_median")),
            "subject_split_half_pearson_q025": safe_float(r.get("subject_split_half_pearson_q025")),
            "fewshot_best_model": fs.get("best_model"),
            "fewshot_best_k": safe_float(fs.get("best_k_calibration")),
            "fewshot_lift_vs_stimulus_rmse": safe_float(fs.get("best_lift_vs_stimulus_rmse")),
            "fewshot_rmse_win_margin": safe_float(fs.get("rmse_win_margin")),
            "phys_after_fewshot_best_block": pa.get("best_block"),
            "phys_after_fewshot_best_k": safe_float(pa.get("best_k_calibration")),
            "phys_after_fewshot_lift_vs_fewshot_rmse": safe_float(pa.get("best_lift_vs_fewshot_rmse")),
            "phys_after_fewshot_win_margin": safe_float(pa.get("rmse_win_margin_vs_fewshot")),
        })

    decision = pd.DataFrame(decision_rows)
    evidence = pd.DataFrame(evidence_rows)
    next_steps = pd.DataFrame([
        {
            "step": "05ad",
            "title": "Few-shot calibration confirmatory stability audit",
            "purpose": "Validate 05aa with paired subject statistics, calibration-size curves, bootstrap/sign tests, and subject-level failure analysis.",
            "why_now": "05aa is the only route that clearly moves beyond stimulus-only; 05ab says physiology does not add after few-shot.",
            "success_condition": "Arousal remains positive with subject-level win margin and CI/p-value support; valence is classified honestly as weak/unstable or recoverable.",
        },
        {
            "step": "05ae",
            "title": "Subject calibration model-family comparison",
            "purpose": "Compare mean-bias, shrinkage, ridge residual calibration, hierarchical/mixed-effect calibration, and small adapter models.",
            "why_now": "05z says residual is subject-profile structured, so the math should target subject calibration directly.",
            "success_condition": "A method beats the simple few-shot bias baseline, not just stimulus-only.",
        },
        {
            "step": "05af",
            "title": "Physiology as moderator of personalization",
            "purpose": "Use physiology only as a moderator/adapter after 05ad/05ae, not as standalone zero-shot decoder.",
            "why_now": "05ab says current physiology does not improve after few-shot, so future physiology claims need a stricter target.",
            "success_condition": "Physiology improves over the locked few-shot baseline with paired subject-level evidence.",
        },
    ])

    decision.to_csv(OUT_DECISION, index=False)
    evidence.to_csv(OUT_EVIDENCE, index=False)
    next_steps.to_csv(OUT_NEXT, index=False)

    report = {
        "title": "I-DARE personalization decision synthesis",
        "inputs": {k: str(v) for k, v in INPUTS.items()},
        "decision_table": decision.to_dict(orient="records"),
        "evidence_table": evidence.to_dict(orient="records"),
        "next_steps": next_steps.to_dict(orient="records"),
        "best_fewshot_rows": fewshot_main.sort_values(["target", "lift_vs_stimulus_rmse", "rmse"], ascending=[True, False, True]).groupby("target", as_index=False).head(5).to_dict(orient="records") if not fewshot_main.empty else [],
        "physiology_after_fewshot_best_rows": after_best.head(20).to_dict(orient="records") if not after_best.empty else [],
        "fewshot_subject_winloss_preview": fewshot_wins.head(20).to_dict(orient="records") if not fewshot_wins.empty else [],
        "prior_baseline_rows": prior.to_dict(orient="records") if not prior.empty else [],
        "zero_shot_audit_main_rows": audit_main.to_dict(orient="records") if not audit_main.empty else [],
    }
    OUT_JSON.write_text(json.dumps(clean_json(report), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("# I-DARE Personalization Decision Synthesis\n")
    lines.append("This checkpoint synthesizes 05z, 05aa, and 05ab after the residual reliability and few-shot audits.\n")
    lines.append("## Final decision\n")
    lines.append(md_table(decision, ["target", "final_decision", "residual_signal_verdict", "zero_shot_physiology_verdict", "fewshot_decision", "physiology_after_fewshot_decision", "recommended_next_action"]))
    lines.append("\n## Evidence table\n")
    lines.append(md_table(evidence, ["target", "subject_r2_on_residual", "stimulus_r2_on_residual", "subject_split_half_pearson_median", "subject_split_half_pearson_q025", "fewshot_best_model", "fewshot_best_k", "fewshot_lift_vs_stimulus_rmse", "fewshot_rmse_win_margin", "phys_after_fewshot_best_block", "phys_after_fewshot_best_k", "phys_after_fewshot_lift_vs_fewshot_rmse", "phys_after_fewshot_win_margin"]))
    lines.append("\n## Interpretation lock\n")
    lines.append("- The residual is not being treated as random noise: 05z shows reliable subject-structured residual bias/profile.\n")
    lines.append("- The current zero-shot EEG/EMG feature blocks remain no-go against stimulus-only.\n")
    lines.append("- Few-shot subject calibration is the first path that clearly changes the decision, especially for arousal.\n")
    lines.append("- Adding the tested physiology blocks after few-shot calibration does not improve the few-shot baseline.\n")
    lines.append("- Therefore, future claims must compare against a locked few-shot baseline, not just stimulus-only.\n")
    lines.append("\n## Recommended next steps\n")
    lines.append(md_table(next_steps, ["step", "title", "purpose", "why_now", "success_condition"]))
    lines.append("\n## Practical note\n")
    lines.append("Do not start a large deep architecture search yet. The next high-value step is 05ad: a confirmatory few-shot calibration stability audit with paired subject-level uncertainty. Only after that should we test adapter/domain-adaptation models.\n")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05ac completed.")
    for p in [OUT_MD, OUT_JSON, OUT_DECISION, OUT_EVIDENCE, OUT_NEXT]:
        print(f"wrote: {p}")
    print("\nDecision table:")
    print(decision.to_string(index=False))
    print("\nEvidence table:")
    print(evidence.to_string(index=False))
    print("\nNext steps:")
    print(next_steps.to_string(index=False))


if __name__ == "__main__":
    main()
