#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(".")
OUT_PREFIX = ROOT / "docs/roca/idare_06a5_augmentation_locked_gate_probe_current"

AUG_MAIN = ROOT / "docs/roca/eeg_augmentation_matrix_smoke_main_metrics_current.csv"
AUG_SUBSET = ROOT / "docs/roca/eeg_augmentation_matrix_smoke_subset_metrics_current.csv"
GAUSS_AROUSAL = ROOT / "docs/roca/eeg_gaussian10_arousal_test_oracle_main_metrics_current.csv"
GAUSS_VALENCE = ROOT / "docs/roca/eeg_gaussian10_valence_test_oracle_main_metrics_current.csv"

LOCKED_06A4B = ROOT / "docs/roca/idare_06a4b_kshot_calibration_locked_bridge_confirm_current_decision_table.csv"
FIXED_05AJ = ROOT / "docs/roca/idare_residual_physiology_feature_audit_current_predictions.csv"
PRIOR_MAP = ROOT / "docs/roca/idare_06a1z_prior_experiment_map_and_root_cause_autopsy_current_augmentation_evidence.csv"


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as exc:
        return pd.DataFrame({"_read_error": [str(exc)], "_path": [str(path)]})


def finite_float(x, default=np.nan):
    try:
        v = float(x)
        if math.isfinite(v):
            return v
    except Exception:
        pass
    return default


def best_aug_from_matrix(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    d = df.copy()
    if "model" in d.columns:
        d = d[d["model"].astype(str).str.contains("eeg_", case=False, na=False)]
    if "augmentation_config" not in d.columns:
        return pd.DataFrame()
    keep_cols = [
        "augmentation_config", "target", "model", "n", "rmse", "pearson",
        "balanced_accuracy", "auroc", "dev_rmse", "dev_pearson", "dev_sign_acc",
        "pred_dev_std", "lift_vs_stimulus_rmse", "lift_vs_stimulus_balanced_accuracy",
        "lift_vs_stimulus_auroc", "lift_vs_stimulus_dev_rmse",
    ]
    keep_cols = [c for c in keep_cols if c in d.columns]
    d = d[keep_cols].copy()
    sort_cols = [c for c in ["lift_vs_stimulus_rmse", "dev_pearson", "lift_vs_stimulus_auroc"] if c in d.columns]
    if sort_cols:
        d = d.sort_values(sort_cols, ascending=[False] * len(sort_cols))
    return d


def extract_gaussian10_oracle(path: Path, target: str) -> dict:
    df = safe_read_csv(path)
    out = {"target": target, "path": str(path), "available": bool(not df.empty)}
    if df.empty:
        return out

    model_rows = df[df.get("model", "").astype(str).str.contains("gaussian10", case=False, na=False)].copy()
    stim_rows = df[df.get("model", "").astype(str).str.fullmatch("stimulus_only", case=False, na=False)].copy()

    if not model_rows.empty:
        r = model_rows.iloc[0]
        for c in [
            "augmentation_config", "n", "mae", "rmse", "pearson", "balanced_accuracy",
            "macro_f1", "auroc", "dev_rmse", "dev_pearson", "dev_sign_acc",
            "pred_dev_std", "lift_vs_stimulus_rmse", "lift_vs_stimulus_balanced_accuracy",
            "lift_vs_stimulus_auroc", "lift_vs_stimulus_dev_rmse",
        ]:
            if c in r.index:
                out[f"model_{c}"] = r[c]
    if not stim_rows.empty:
        r = stim_rows.iloc[0]
        for c in ["mae", "rmse", "pearson", "balanced_accuracy", "macro_f1", "auroc", "dev_rmse"]:
            if c in r.index:
                out[f"stimulus_{c}"] = r[c]
    return out


def load_locked_bridge() -> dict:
    df = safe_read_csv(LOCKED_06A4B)
    out = {"path": str(LOCKED_06A4B), "available": bool(not df.empty)}
    if df.empty:
        return out
    r = df.iloc[0]
    for c in [
        "target", "decision", "locked_bridge_rmse_05ak", "best_candidate_rmse",
        "best_lift_vs_zero", "best_lift_vs_fixed_same_eval",
        "best_lift_vs_locked_bridge_rmse", "best_passes_locked_bridge_gate",
        "recommended_next_action",
    ]:
        if c in r.index:
            out[c] = r[c]
    return out


def summarize_prior_aug_evidence() -> pd.DataFrame:
    df = safe_read_csv(PRIOR_MAP)
    if df.empty:
        return pd.DataFrame()
    cols = list(df.columns)
    text_cols = [c for c in cols if df[c].dtype == object]
    mask = pd.Series(False, index=df.index)
    for c in text_cols:
        mask |= df[c].astype(str).str.contains("gaussian|augment|noise|jitter|shift|gain|oracle", case=False, regex=True, na=False)
    d = df[mask].copy()
    if d.empty:
        return pd.DataFrame()
    preferred = [c for c in [
        "file", "path", "source_file", "metric_file", "target", "model", "augmentation_config",
        "metric", "metric_name", "value", "computed_rmse", "rmse", "lift_vs_stimulus_rmse",
        "balanced_accuracy", "auroc", "notes"
    ] if c in d.columns]
    if preferred:
        d = d[preferred]
    return d.head(80)


def decision_logic(gauss_arousal: dict, locked: dict) -> dict:
    aug_rmse = finite_float(gauss_arousal.get("model_rmse"))
    stim_rmse = finite_float(gauss_arousal.get("stimulus_rmse"))
    lift_stim = finite_float(gauss_arousal.get("model_lift_vs_stimulus_rmse"))
    locked_rmse = finite_float(locked.get("locked_bridge_rmse_05ak"))
    best_kshot_rmse = finite_float(locked.get("best_candidate_rmse"))

    pass_stim = math.isfinite(lift_stim) and lift_stim > 0
    pass_locked = math.isfinite(aug_rmse) and math.isfinite(locked_rmse) and aug_rmse < locked_rmse
    pass_kshot = math.isfinite(aug_rmse) and math.isfinite(best_kshot_rmse) and aug_rmse < best_kshot_rmse

    if pass_stim and pass_locked:
        decision = "GO_RERUN_GAUSSIAN10_UNDER_LOCKED_CURRENT_GATE"
        interpretation = (
            "Prior gaussian_0p10 evidence beats stimulus-only and appears better than the locked B2 bridge. "
            "This is strong enough to justify a real 06a5 rerun under the current residual locked gate."
        )
        next_action = (
            "Run a proper locked-gate gaussian_0p10 residual experiment with no test-label checkpointing, "
            "subject-level validation, fixed zero/fixed/B2 references, and paired subject bootstrap."
        )
    elif pass_stim and not pass_locked:
        decision = "PARTIAL_GO_PRIOR_AUG_BEATS_STIMULUS_NOT_LOCKED_B2"
        interpretation = (
            "Prior gaussian_0p10 evidence improved over stimulus-only, but it does not establish improvement over the locked B2 bridge. "
            "Treat it as promising historical evidence, not a solved current-gate result."
        )
        next_action = (
            "Only run 06a5 if we can compare against locked B2 in the same current residual protocol. "
            "Do not claim augmentation solved LOSO unless it beats locked B2 and fixed EEG-bandpower."
        )
    elif pass_stim:
        decision = "WEAK_GO_PRIOR_AUG_BEATS_STIMULUS_ONLY_BUT_LOCKED_REFERENCE_MISSING"
        interpretation = (
            "Prior gaussian_0p10 beats stimulus-only, but locked bridge reference is unavailable or incomparable."
        )
        next_action = (
            "Create a compact locked-gate augmentation rerun or load the locked bridge decision table before claiming anything."
        )
    else:
        decision = "NO_GO_PRIOR_AUG_NOT_ENOUGH_FOR_CURRENT_GATE"
        interpretation = (
            "Prior augmentation evidence is not strong enough under the criteria. It may have helped old/oracle/smoke settings, "
            "but not enough to justify more deep search as the next step."
        )
        next_action = (
            "Skip augmentation rerun and move to 06a6 neural pipeline anchor or final calibration-dominant conclusion."
        )

    return {
        "target": "arousal",
        "decision": decision,
        "gaussian10_rmse": aug_rmse,
        "stimulus_only_rmse": stim_rmse,
        "lift_vs_stimulus_rmse": lift_stim,
        "locked_bridge_rmse_05ak": locked_rmse,
        "kshot_06a4b_best_rmse": best_kshot_rmse,
        "passes_stimulus_gate": bool(pass_stim),
        "passes_locked_bridge_gate": bool(pass_locked),
        "passes_kshot_06a4b_gate": bool(pass_kshot),
        "interpretation": interpretation,
        "recommended_next_action": next_action,
    }



def df_to_md(df: pd.DataFrame) -> str:
    """Tiny markdown-table writer; avoids optional pandas dependency: tabulate."""
    if df is None or df.empty:
        return "_No rows._"
    d = df.copy()

    def fmt(x):
        if pd.isna(x):
            return ""
        if isinstance(x, float):
            return f"{x:.6g}"
        txt = str(x)
        txt = txt.replace("\n", " ").replace("|", "\\|")
        return txt

    cols = [str(c).replace("|", "\\|") for c in d.columns]
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in d.iterrows():
        lines.append("| " + " | ".join(fmt(row[c]) for c in d.columns) + " |")
    return "\n".join(lines)

def write_md(payload: dict, ranked_aug: pd.DataFrame, prior_evidence: pd.DataFrame) -> None:
    lines = []
    lines.append("# ROCA 06a5 - Augmentation locked-gate probe")
    lines.append("")
    lines.append("Purpose: inspect prior augmentation evidence and decide whether `gaussian_0p10` deserves a current locked-gate rerun.")
    lines.append("")
    lines.append("## Decision")
    dt = pd.DataFrame([payload["decision"]])
    lines.append(df_to_md(dt))
    lines.append("")
    lines.append("## Prior gaussian_0p10 oracle/smoke evidence")
    ga = pd.DataFrame(payload["gaussian10_evidence"])
    lines.append(df_to_md(ga))
    lines.append("")
    lines.append("## Locked bridge reference")
    lines.append(df_to_md(pd.DataFrame([payload["locked_bridge"]])))
    lines.append("")
    lines.append("## Ranked augmentation matrix evidence")
    if ranked_aug.empty:
        lines.append("_No augmentation matrix found._")
    else:
        lines.append(df_to_md(ranked_aug.head(20)))
    lines.append("")
    lines.append("## Prior augmentation evidence rows")
    if prior_evidence.empty:
        lines.append("_No prior augmentation evidence rows found._")
    else:
        lines.append(df_to_md(prior_evidence.head(40)))
    lines.append("")
    lines.append("## Interpretation")
    lines.append(payload["decision"]["interpretation"])
    lines.append("")
    lines.append("## Recommended next action")
    lines.append(payload["decision"]["recommended_next_action"])
    lines.append("")
    (OUT_PREFIX.with_suffix(".md")).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    aug_main = safe_read_csv(AUG_MAIN)
    ranked_aug = best_aug_from_matrix(aug_main)
    prior_evidence = summarize_prior_aug_evidence()

    gauss_arousal = extract_gaussian10_oracle(GAUSS_AROUSAL, "arousal")
    gauss_valence = extract_gaussian10_oracle(GAUSS_VALENCE, "valence")
    locked = load_locked_bridge()
    decision = decision_logic(gauss_arousal, locked)

    payload = {
        "inputs": {
            "augmentation_matrix": str(AUG_MAIN),
            "augmentation_subset": str(AUG_SUBSET),
            "gaussian10_arousal": str(GAUSS_AROUSAL),
            "gaussian10_valence": str(GAUSS_VALENCE),
            "locked_bridge_06a4b": str(LOCKED_06A4B),
            "prior_map": str(PRIOR_MAP),
        },
        "decision": decision,
        "gaussian10_evidence": [gauss_arousal, gauss_valence],
        "locked_bridge": locked,
    }

    OUT_PREFIX.with_suffix(".json").write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    pd.DataFrame([decision]).to_csv(str(OUT_PREFIX) + "_decision_table.csv", index=False)
    pd.DataFrame(payload["gaussian10_evidence"]).to_csv(str(OUT_PREFIX) + "_gaussian10_evidence.csv", index=False)
    if not ranked_aug.empty:
        ranked_aug.to_csv(str(OUT_PREFIX) + "_ranked_augmentation_matrix.csv", index=False)
    else:
        pd.DataFrame().to_csv(str(OUT_PREFIX) + "_ranked_augmentation_matrix.csv", index=False)
    if not prior_evidence.empty:
        prior_evidence.to_csv(str(OUT_PREFIX) + "_prior_augmentation_evidence_rows.csv", index=False)
    else:
        pd.DataFrame().to_csv(str(OUT_PREFIX) + "_prior_augmentation_evidence_rows.csv", index=False)

    write_md(payload, ranked_aug, prior_evidence)

    print("ROCA step 06a5 completed.")
    for p in [
        OUT_PREFIX.with_suffix(".md"),
        OUT_PREFIX.with_suffix(".json"),
        Path(str(OUT_PREFIX) + "_decision_table.csv"),
        Path(str(OUT_PREFIX) + "_gaussian10_evidence.csv"),
        Path(str(OUT_PREFIX) + "_ranked_augmentation_matrix.csv"),
        Path(str(OUT_PREFIX) + "_prior_augmentation_evidence_rows.csv"),
    ]:
        print(f"wrote: {p}")

    print("\nDecision:")
    print(pd.DataFrame([decision]).to_string(index=False))
    print("\nGaussian10 evidence:")
    print(pd.DataFrame(payload["gaussian10_evidence"]).to_string(index=False))
    print("\n================== GIT STATUS ==================")
    import subprocess
    print(subprocess.check_output(["git", "status", "--short"], text=True))



def patch_noncomparable_decision_outputs() -> None:
    """Correct 06a5 interpretation: old gaussian10 evidence is promising but not locked-gate comparable."""
    import json
    from pathlib import Path
    import pandas as pd

    prefix = Path("docs/roca/idare_06a5_augmentation_locked_gate_probe_current")
    decision = "RERUN_REQUIRED_GAUSSIAN10_PRIOR_EVIDENCE_NOT_LOCKED_COMPARABLE"
    interp = (
        "Prior gaussian_0p10 evidence beats stimulus-only in the old score/oracle report, "
        "but it is not directly comparable to locked B2 or the current high-disagreement residual gate. "
        "It justifies a clean rerun under the current locked residual protocol, not a final physiology/deep gain claim."
    )
    action = (
        "Run a proper locked-gate gaussian_0p10 residual experiment with no test-label checkpointing, "
        "subject-level validation, fixed zero/fixed/B2 references, and paired subject bootstrap."
    )

    csv_path = Path(str(prefix) + "_decision_table.csv")
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        if "decision" in df.columns:
            df.loc[df["target"].astype(str).eq("arousal"), "decision"] = decision
        if "interpretation" in df.columns:
            df.loc[df["target"].astype(str).eq("arousal"), "interpretation"] = interp
        if "recommended_next_action" in df.columns:
            df.loc[df["target"].astype(str).eq("arousal"), "recommended_next_action"] = action
        for col in ["passes_locked_bridge_gate", "passes_kshot_06a4b_gate"]:
            if col in df.columns:
                df.loc[df["target"].astype(str).eq("arousal"), col] = False
        df.to_csv(csv_path, index=False)

    json_path = Path(str(prefix) + ".json")
    if json_path.exists():
        payload = json.loads(json_path.read_text(encoding="utf-8"))

        def walk(x):
            if isinstance(x, dict):
                if x.get("target") == "arousal":
                    if "decision" in x:
                        x["decision"] = decision
                    if "interpretation" in x:
                        x["interpretation"] = interp
                    if "recommended_next_action" in x:
                        x["recommended_next_action"] = action
                    if "passes_locked_bridge_gate" in x:
                        x["passes_locked_bridge_gate"] = False
                    if "passes_kshot_06a4b_gate" in x:
                        x["passes_kshot_06a4b_gate"] = False
                return {k: walk(v) for k, v in x.items()}
            if isinstance(x, list):
                return [walk(v) for v in x]
            if isinstance(x, str):
                x = x.replace(
                    "GO_RERUN_GAUSSIAN10_UNDER_LOCKED_CURRENT_GATE",
                    decision,
                )
                x = x.replace(
                    "Prior gaussian_0p10 evidence beats stimulus-only and appears better than the locked B2 bridge. This is strong enough to justify a real 06a5 rerun under the current residual locked gate.",
                    interp,
                )
                return x
            return x

        payload = walk(payload)
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    md_path = Path(str(prefix) + ".md")
    if md_path.exists():
        txt = md_path.read_text(encoding="utf-8")
        txt = txt.replace("GO_RERUN_GAUSSIAN10_UNDER_LOCKED_CURRENT_GATE", decision)
        note = (
            "\n\n## Critical comparability correction\n\n"
            "The prior `gaussian_0p10` result is promising, but it came from the old score/oracle report "
            "and is not directly comparable to locked B2 or the current high-disagreement residual gate. "
            "For decision-making, the locked-B2/k-shot pass flags are treated as **not passed** until a clean locked-gate rerun is completed.\n"
        )
        if "## Critical comparability correction" not in txt:
            txt += note
        md_path.write_text(txt, encoding="utf-8")

    if csv_path.exists():
        print("\\nCorrected 06a5 decision:")
        print(pd.read_csv(csv_path).to_string(index=False))

if __name__ == "__main__":
    main()
    patch_noncomparable_decision_outputs()
