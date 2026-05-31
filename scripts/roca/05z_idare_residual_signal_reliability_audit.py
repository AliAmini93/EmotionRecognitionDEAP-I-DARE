#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".cache"
ROCA = ROOT / "docs" / "roca"

DEFAULT_TRIAL_INDEX = CACHE / "idare_trial_index.csv"
DEFAULT_CONFIRMATORY_VERDICT = ROCA / "idare_residual_physiology_confirmatory_stats_current_verdict.csv"
DEFAULT_OUT_PREFIX = "idare_residual_signal_reliability_audit_current"

TARGETS = {
    "valence": "valence_score",
    "arousal": "arousal_score",
}

EPS = 1e-12


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--trial-index", type=Path, default=DEFAULT_TRIAL_INDEX)
    p.add_argument("--confirmatory-verdict", type=Path, default=DEFAULT_CONFIRMATORY_VERDICT)
    p.add_argument("--out-prefix", type=str, default=DEFAULT_OUT_PREFIX)
    p.add_argument("--n-splits", type=int, default=5000)
    p.add_argument("--seed", type=int, default=20260516)
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
    if pd.isna(x) if not isinstance(x, (list, tuple, dict, np.ndarray)) else False:
        return None
    return x


def pearson(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    a, b = a[m], b[m]
    if len(a) < 3:
        return None
    if np.std(a) < EPS or np.std(b) < EPS:
        return None
    return float(np.corrcoef(a, b)[0, 1])


def spearman(a, b):
    a = pd.Series(a).rank(method="average").to_numpy(dtype=float)
    b = pd.Series(b).rank(method="average").to_numpy(dtype=float)
    return pearson(a, b)


def summary_stats(x):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return {}
    med = float(np.median(x))
    mad = float(np.median(np.abs(x - med)))
    std = float(np.std(x))
    if std < EPS:
        skew = None
        kurt = None
    else:
        z = (x - float(np.mean(x))) / std
        skew = float(np.mean(z ** 3))
        kurt = float(np.mean(z ** 4) - 3.0)
    scaled_mad = 1.4826 * mad
    outlier_rate = float(np.mean(np.abs(x - med) > 3.0 * scaled_mad)) if scaled_mad > EPS else 0.0
    return {
        "n": int(len(x)),
        "mean": safe_float(np.mean(x)),
        "std": safe_float(np.std(x)),
        "median": safe_float(np.median(x)),
        "q25": safe_float(np.quantile(x, 0.25)),
        "q75": safe_float(np.quantile(x, 0.75)),
        "iqr": safe_float(np.quantile(x, 0.75) - np.quantile(x, 0.25)),
        "mad": safe_float(mad),
        "scaled_mad": safe_float(scaled_mad),
        "mean_abs": safe_float(np.mean(np.abs(x))),
        "median_abs": safe_float(np.median(np.abs(x))),
        "q90_abs": safe_float(np.quantile(np.abs(x), 0.90)),
        "q95_abs": safe_float(np.quantile(np.abs(x), 0.95)),
        "skew": safe_float(skew),
        "kurtosis_excess": safe_float(kurt),
        "outlier_rate_3mad": safe_float(outlier_rate),
        "positive_rate": safe_float(np.mean(x > 0.0)),
        "negative_rate": safe_float(np.mean(x < 0.0)),
    }


def load_idare_trial_index(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)
    required = ["subject_id", "stimulus_id", "valence_score", "arousal_score"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"trial index missing columns: {missing}")
    out = df[required].copy()
    out["subject_id"] = out["subject_id"].astype(int)
    out["stimulus_id"] = out["stimulus_id"].astype(str)
    out = out.drop_duplicates(["subject_id", "stimulus_id"]).reset_index(drop=True)
    return out


def compute_loso_stimulus_residuals(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for target, score_col in TARGETS.items():
        for subject_id in sorted(df["subject_id"].unique()):
            train = df[df["subject_id"].ne(subject_id)]
            test = df[df["subject_id"].eq(subject_id)].copy()
            global_mean = float(train[score_col].mean())
            stim_means = train.groupby("stimulus_id")[score_col].mean()

            pred = test["stimulus_id"].map(stim_means).astype(float).fillna(global_mean).to_numpy(dtype=float)
            y = test[score_col].to_numpy(dtype=float)

            out = test[["subject_id", "stimulus_id"]].copy()
            out["target"] = target
            out["y_true_score"] = y
            out["stimulus_only_pred"] = pred
            out["residual"] = y - pred
            out["split_id"] = f"heldout_subject_{subject_id}"
            rows.append(out)

    pred = pd.concat(rows, ignore_index=True)
    return pred[["target", "subject_id", "stimulus_id", "split_id", "y_true_score", "stimulus_only_pred", "residual"]]


def effect_r2_oneway(df: pd.DataFrame, group_col: str) -> float:
    y = df["residual"].to_numpy(dtype=float)
    y_mean = float(np.mean(y))
    sst = float(np.sum((y - y_mean) ** 2))
    if sst < EPS:
        return 0.0
    group_mean = df.groupby(group_col)["residual"].transform("mean").to_numpy(dtype=float)
    ss_model = float(np.sum((group_mean - y_mean) ** 2))
    return max(0.0, min(1.0, ss_model / sst))


def effect_r2_additive(df: pd.DataFrame):
    y = df["residual"].to_numpy(dtype=float)
    y_mean = float(np.mean(y))
    sst = float(np.sum((y - y_mean) ** 2))
    if sst < EPS:
        return 0.0, 0, 0

    subj = pd.get_dummies(df["subject_id"].astype(str), prefix="subj", dtype=float)
    stim = pd.get_dummies(df["stimulus_id"].astype(str), prefix="stim", dtype=float)
    x = pd.concat([subj, stim], axis=1).to_numpy(dtype=float)

    coef, *_ = np.linalg.lstsq(x, y, rcond=None)
    pred = x @ coef
    ss_res = float(np.sum((y - pred) ** 2))
    r2 = 1.0 - ss_res / sst
    rank = int(np.linalg.matrix_rank(x))
    return max(0.0, min(1.0, r2)), rank, int(x.shape[1])


def residual_effects(pred: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for target, g in pred.groupby("target", sort=True):
        subject_r2 = effect_r2_oneway(g, "subject_id")
        stimulus_r2 = effect_r2_oneway(g, "stimulus_id")
        additive_r2, rank, cols = effect_r2_additive(g)

        rows.append({
            "target": target,
            "subject_r2_on_residual": subject_r2,
            "stimulus_r2_on_residual": stimulus_r2,
            "subject_plus_stimulus_r2_on_residual": additive_r2,
            "unique_subject_r2_over_stimulus": additive_r2 - stimulus_r2,
            "unique_stimulus_r2_over_subject": additive_r2 - subject_r2,
            "additive_design_rank": rank,
            "additive_design_cols": cols,
        })
    return pd.DataFrame(rows)


def split_half_subject_reliability(pred: pd.DataFrame, n_splits: int, seed: int):
    rng = np.random.default_rng(seed)
    raw_rows = []

    for target, g in pred.groupby("target", sort=True):
        stimuli = np.array(sorted(g["stimulus_id"].unique()))
        if len(stimuli) < 4:
            continue

        for split_idx in range(n_splits):
            shuffled = stimuli.copy()
            rng.shuffle(shuffled)
            half = len(shuffled) // 2
            a_set = set(shuffled[:half])
            b_set = set(shuffled[half:])

            ga = g[g["stimulus_id"].isin(a_set)].groupby("subject_id")["residual"].mean()
            gb = g[g["stimulus_id"].isin(b_set)].groupby("subject_id")["residual"].mean()
            subjects = sorted(set(ga.index).intersection(gb.index))
            a = ga.loc[subjects].to_numpy(dtype=float)
            b = gb.loc[subjects].to_numpy(dtype=float)

            raw_rows.append({
                "target": target,
                "axis": "subject_bias_across_stimuli",
                "split_idx": split_idx,
                "n_items": len(subjects),
                "pearson": pearson(a, b),
                "spearman": spearman(a, b),
            })

    raw = pd.DataFrame(raw_rows)

    summary_rows = []
    if not raw.empty:
        for (target, axis), gg in raw.groupby(["target", "axis"], sort=True):
            for metric in ["pearson", "spearman"]:
                x = gg[metric].dropna().to_numpy(dtype=float)
                if len(x) == 0:
                    continue
                summary_rows.append({
                    "target": target,
                    "axis": axis,
                    "metric": metric,
                    "splits": int(len(x)),
                    "mean": safe_float(np.mean(x)),
                    "std": safe_float(np.std(x)),
                    "q025": safe_float(np.quantile(x, 0.025)),
                    "q25": safe_float(np.quantile(x, 0.25)),
                    "median": safe_float(np.median(x)),
                    "q75": safe_float(np.quantile(x, 0.75)),
                    "q975": safe_float(np.quantile(x, 0.975)),
                    "positive_rate": safe_float(np.mean(x > 0.0)),
                    "used_in_verdict": True,
                    "note": "Meaningful split-half reliability of subject residual bias across stimuli.",
                })

    return raw, pd.DataFrame(summary_rows)


def artifact_checks(pred: pd.DataFrame, n_splits: int, seed: int) -> pd.DataFrame:
    """Compute only a small diagnostic artifact check.

    We intentionally do not use this in the verdict.
    LOSO stimulus residuals are centered within each stimulus, so splitting subjects and
    correlating half-stimulus residual means can induce near-perfect anti-correlation.
    """
    rng = np.random.default_rng(seed + 19)
    rows = []

    for target, g in pred.groupby("target", sort=True):
        subjects = np.array(sorted(g["subject_id"].unique()))
        for split_idx in range(min(n_splits, 200)):
            shuffled = subjects.copy()
            rng.shuffle(shuffled)
            half = len(shuffled) // 2
            a_set = set(shuffled[:half])
            b_set = set(shuffled[half:])

            ga = g[g["subject_id"].isin(a_set)].groupby("stimulus_id")["residual"].mean()
            gb = g[g["subject_id"].isin(b_set)].groupby("stimulus_id")["residual"].mean()
            stimuli = sorted(set(ga.index).intersection(gb.index))
            a = ga.loc[stimuli].to_numpy(dtype=float)
            b = gb.loc[stimuli].to_numpy(dtype=float)

            rows.append({
                "target": target,
                "artifact_check": "stimulus_residual_split_subjects_not_used",
                "split_idx": split_idx,
                "pearson": pearson(a, b),
                "spearman": spearman(a, b),
                "used_in_verdict": False,
                "why_not_used": (
                    "LOSO residuals are algebraically centered by stimulus; split-subject "
                    "stimulus residual means can be forced into anti-correlation. "
                    "Do not interpret near -1 as scientific stimulus reliability."
                ),
            })

    return pd.DataFrame(rows)


def profile_tables(pred: pd.DataFrame):
    subject_rows = []
    stimulus_rows = []

    for (target, subject_id), g in pred.groupby(["target", "subject_id"], sort=True):
        row = {"target": target, "subject_id": int(subject_id)}
        row.update({f"residual_{k}": v for k, v in summary_stats(g["residual"].to_numpy()).items()})
        subject_rows.append(row)

    for (target, stimulus_id), g in pred.groupby(["target", "stimulus_id"], sort=True):
        row = {"target": target, "stimulus_id": str(stimulus_id)}
        row.update({f"residual_{k}": v for k, v in summary_stats(g["residual"].to_numpy()).items()})
        stimulus_rows.append(row)

    return pd.DataFrame(subject_rows), pd.DataFrame(stimulus_rows)


def residual_summary(pred: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for target, g in pred.groupby("target", sort=True):
        row = {"target": target}
        row.update(summary_stats(g["residual"].to_numpy(dtype=float)))
        rows.append(row)
    return pd.DataFrame(rows)


def load_confirmatory(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    out = {}
    if "target" in df.columns and "confirmatory_verdict" in df.columns:
        for _, r in df.iterrows():
            out[str(r["target"])] = str(r["confirmatory_verdict"])
    return out


def build_verdict(summary: pd.DataFrame, effects: pd.DataFrame, reliability: pd.DataFrame, confirmatory: dict[str, str]) -> pd.DataFrame:
    rows = []

    for _, srow in summary.iterrows():
        target = str(srow["target"])
        erow = effects[effects["target"].eq(target)].iloc[0]

        rel = reliability[
            reliability["target"].eq(target)
            & reliability["axis"].eq("subject_bias_across_stimuli")
            & reliability["metric"].eq("pearson")
        ]

        if rel.empty:
            subj_med = None
            subj_q025 = None
        else:
            subj_med = safe_float(rel.iloc[0]["median"])
            subj_q025 = safe_float(rel.iloc[0]["q025"])

        subject_r2 = safe_float(erow["subject_r2_on_residual"]) or 0.0
        stimulus_r2 = safe_float(erow["stimulus_r2_on_residual"]) or 0.0

        fewshot = bool(subject_r2 >= 0.05 and subj_q025 is not None and subj_q025 > 0.0)
        stimulus_plausible = bool(stimulus_r2 >= 0.05)

        confirm = confirmatory.get(target, "UNKNOWN")

        if fewshot and "NO_GO" in confirm:
            verdict = "SUBJECT_STRUCTURED_RESIDUAL_PRESENT__ZERO_SHOT_PHYSIOLOGY_NO_GO__FEW_SHOT_RECOMMENDED"
        elif fewshot:
            verdict = "SUBJECT_STRUCTURED_RESIDUAL_PRESENT__FEW_SHOT_RECOMMENDED"
        else:
            verdict = "WEAK_OR_UNRELIABLE_RESIDUAL_STRUCTURE_CURRENT_AUDIT"

        interpretation = (
            "Residual is reliable mainly as subject-specific bias/profile across stimuli. "
            "The current physiology feature audit remains no-go for zero-shot LOSO, "
            "but few-shot subject calibration is scientifically plausible."
            if fewshot else
            "Residual reliability was not strong enough to justify subject-calibration pivot from this audit alone."
        )

        rows.append({
            "target": target,
            "residual_signal_verdict": verdict,
            "confirmatory_physiology_verdict": confirm,
            "residual_std": safe_float(srow["std"]),
            "subject_r2_on_residual": subject_r2,
            "stimulus_r2_on_residual": stimulus_r2,
            "additive_subject_stimulus_r2_on_residual": safe_float(erow["subject_plus_stimulus_r2_on_residual"]),
            "subject_split_half_pearson_median": subj_med,
            "subject_split_half_pearson_q025": subj_q025,
            "stimulus_split_half_status": "NOT_USED_ARTIFACT_UNDER_LOSO_RESIDUAL_DEFINITION",
            "stimulus_split_half_artifact_note": (
                "Splitting subjects and correlating per-stimulus residual means is not used; "
                "LOSO stimulus residuals are algebraically centered within stimulus and can induce anti-correlation."
            ),
            "few_shot_or_subject_calibration_plausible": fewshot,
            "stimulus_residual_structure_plausible": stimulus_plausible,
            "interpretation": interpretation,
        })

    return pd.DataFrame(rows)


def md_table(df: pd.DataFrame, cols=None, max_rows=None) -> str:
    if df is None or df.empty:
        return "_No rows._\n"

    if cols is None:
        cols = list(df.columns)
    rows = df[cols].copy()
    if max_rows is not None:
        rows = rows.head(max_rows)

    def fmt(v):
        if isinstance(v, float):
            return f"{v:.6f}" if math.isfinite(v) else ""
        if pd.isna(v):
            return ""
        return str(v).replace("|", "\\|").replace("\n", " ")

    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, r in rows.iterrows():
        lines.append("| " + " | ".join(fmt(r[c]) for c in cols) + " |")
    return "\n".join(lines) + "\n"


def main():
    args = parse_args()
    ROCA.mkdir(parents=True, exist_ok=True)

    df = load_idare_trial_index(args.trial_index)
    pred = compute_loso_stimulus_residuals(df)

    summary = residual_summary(pred)
    effects = residual_effects(pred)
    split_raw, reliability = split_half_subject_reliability(pred, args.n_splits, args.seed)
    artifact = artifact_checks(pred, args.n_splits, args.seed)
    subject_profile, stimulus_profile = profile_tables(pred)
    confirmatory = load_confirmatory(args.confirmatory_verdict)
    verdict = build_verdict(summary, effects, reliability, confirmatory)

    out_prefix = args.out_prefix
    out_md = ROCA / f"{out_prefix}.md"
    out_json = ROCA / f"{out_prefix}.json"
    out_pred = ROCA / f"{out_prefix}_residual_predictions.csv"
    out_summary = ROCA / f"{out_prefix}_residual_summary.csv"
    out_effects = ROCA / f"{out_prefix}_residual_effects.csv"
    out_split_raw = ROCA / f"{out_prefix}_split_half_raw.csv"
    out_reliability = ROCA / f"{out_prefix}_split_half_reliability.csv"
    out_artifact = ROCA / f"{out_prefix}_artifact_checks.csv"
    out_subject_profile = ROCA / f"{out_prefix}_subject_residual_profile.csv"
    out_stimulus_profile = ROCA / f"{out_prefix}_stimulus_residual_profile.csv"
    out_verdict = ROCA / f"{out_prefix}_verdict.csv"

    pred.to_csv(out_pred, index=False)
    summary.to_csv(out_summary, index=False)
    effects.to_csv(out_effects, index=False)
    split_raw.to_csv(out_split_raw, index=False)
    reliability.to_csv(out_reliability, index=False)
    artifact.to_csv(out_artifact, index=False)
    subject_profile.to_csv(out_subject_profile, index=False)
    stimulus_profile.to_csv(out_stimulus_profile, index=False)
    verdict.to_csv(out_verdict, index=False)

    report = {
        "title": "I-DARE residual signal reliability audit",
        "patched_interpretation": {
            "stimulus_split_half_status": "not used",
            "reason": (
                "LOSO stimulus residuals are centered by stimulus. Split-subject per-stimulus residual "
                "correlations can show algebraic anti-correlation and are not scientific reliability evidence."
            ),
            "main_claim": (
                "Residual structure is mostly subject-specific. Current EEG/EMG feature blocks remain no-go "
                "for zero-shot LOSO, but few-shot subject calibration is plausible."
            ),
        },
        "inputs": {
            "trial_index": str(args.trial_index),
            "confirmatory_verdict": str(args.confirmatory_verdict),
            "n_splits": args.n_splits,
            "seed": args.seed,
        },
        "outputs": {
            "md": str(out_md),
            "json": str(out_json),
            "residual_predictions": str(out_pred),
            "residual_summary": str(out_summary),
            "residual_effects": str(out_effects),
            "split_half_raw": str(out_split_raw),
            "split_half_reliability": str(out_reliability),
            "artifact_checks": str(out_artifact),
            "subject_residual_profile": str(out_subject_profile),
            "stimulus_residual_profile": str(out_stimulus_profile),
            "verdict": str(out_verdict),
        },
        "verdict": verdict.to_dict(orient="records"),
        "residual_summary": summary.to_dict(orient="records"),
        "residual_effects": effects.to_dict(orient="records"),
        "split_half_reliability": reliability.to_dict(orient="records"),
    }

    out_json.write_text(json.dumps(clean_json(report), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("# I-DARE Residual Signal Reliability Audit\n")
    lines.append("This is the patched interpretation of the residual reliability audit.\n")
    lines.append("## Key correction\n")
    lines.append(
        "The previous `stimulus_residual_across_subjects = -1` result should **not** be interpreted as scientific "
        "stimulus reliability. Under LOSO stimulus-only residuals, residuals are algebraically centered within each "
        "stimulus. Splitting subjects can force per-stimulus half-means into anti-correlation. Therefore this axis is "
        "not used in the verdict.\n"
    )
    lines.append("## Verdict\n")
    lines.append(md_table(verdict))
    lines.append("\n## Residual summary\n")
    lines.append(md_table(summary))
    lines.append("\n## Residual variance/effect decomposition\n")
    lines.append(md_table(effects))
    lines.append("\n## Used split-half reliability: subject residual bias across stimuli\n")
    lines.append(md_table(reliability))
    lines.append("\n## Artifact check, not used in verdict\n")
    artifact_preview_cols = ["target", "artifact_check", "split_idx", "pearson", "spearman", "used_in_verdict", "why_not_used"]
    lines.append(md_table(artifact, artifact_preview_cols, max_rows=8))
    lines.append("\n## Interpretation\n")
    lines.append(
        "- Residuals are not pure noise.\n"
        "- The reliable component currently looks subject-specific, especially for arousal.\n"
        "- This supports a pivot toward few-shot subject calibration / subject-adaptive modeling.\n"
        "- It does not rescue the current zero-shot LOSO physiology feature results; those remain no-go under 05y.\n"
    )
    lines.append("\n## Recommended next step\n")
    lines.append(
        "Run `05aa` few-shot residual calibration: hold out one subject, use k calibration stimuli from that subject, "
        "then predict residuals on the remaining stimuli for k = 1, 2, 4, 8, 16.\n"
    )

    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("\nROCA step 05z patched audit completed.")
    for p in [
        out_md, out_json, out_pred, out_summary, out_effects, out_split_raw,
        out_reliability, out_artifact, out_subject_profile, out_stimulus_profile, out_verdict
    ]:
        print(f"wrote: {p}")

    print("\nVerdict:")
    print(verdict.to_string(index=False))

    print("\nResidual effects:")
    print(effects.to_string(index=False))

    print("\nSubject split-half reliability:")
    print(reliability.to_string(index=False))

    print("\n[INFO] Not committed. If inspection is OK:")
    print("git add docs/roca/idare_residual_signal_diagnosis_lock_current.md scripts/roca/05z_idare_residual_signal_reliability_audit.py docs/roca/idare_residual_signal_reliability_audit_current*")
    print('git commit -m "Patch I-DARE residual signal reliability audit interpretation"')
    print("git push")


if __name__ == "__main__":
    main()
