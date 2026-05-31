#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROCA_DIR = ROOT / "docs" / "roca"

INPUT_SPECS = [
    {
        "experiment": "04b_clipped_ridge",
        "main": ROCA_DIR / "emg_only_probe_clipped_main_metrics_current.csv",
        "subset": ROCA_DIR / "emg_only_probe_clipped_subset_metrics_current.csv",
        "description": "22-feature EMG Ridge predictions clipped to SAM range",
    },
    {
        "experiment": "04c_nonlinear_22feat",
        "main": ROCA_DIR / "emg_nonlinear_probe_main_metrics_current.csv",
        "subset": ROCA_DIR / "emg_nonlinear_probe_subset_metrics_current.csv",
        "description": "22-feature EMG ExtraTrees nonlinear probe",
    },
    {
        "experiment": "04e_expanded_812feat",
        "main": ROCA_DIR / "emg_expanded_probe_main_metrics_current.csv",
        "subset": ROCA_DIR / "emg_expanded_probe_subset_metrics_current.csv",
        "description": "812-feature expanded EMG Ridge and ExtraTrees probe",
    },
    {
        "experiment": "04f_augmented_812feat",
        "main": ROCA_DIR / "emg_augmented_probe_main_metrics_current.csv",
        "subset": ROCA_DIR / "emg_augmented_probe_subset_metrics_current.csv",
        "description": "812-feature expanded EMG train-only augmentation probe",
    },
]

OUT_MD = ROCA_DIR / "emg_only_closeout_current.md"
OUT_JSON = ROCA_DIR / "emg_only_closeout_current.json"
OUT_ALL = ROCA_DIR / "emg_only_closeout_all_metrics_current.csv"
OUT_BEST_MAIN = ROCA_DIR / "emg_only_closeout_best_main_current.csv"
OUT_BEST_SUBSET = ROCA_DIR / "emg_only_closeout_best_subset_current.csv"

NUMERIC_COLUMNS = [
    "n",
    "mae",
    "rmse",
    "pearson",
    "spearman",
    "ccc",
    "balanced_accuracy",
    "macro_f1",
    "auroc",
    "dev_mae",
    "dev_rmse",
    "dev_pearson",
    "dev_spearman",
    "dev_sign_acc",
    "pred_dev_std",
    "lift_vs_stimulus_mae",
    "lift_vs_stimulus_rmse",
    "lift_vs_stimulus_pearson",
    "lift_vs_stimulus_spearman",
    "lift_vs_stimulus_ccc",
    "lift_vs_stimulus_balanced_accuracy",
    "lift_vs_stimulus_macro_f1",
    "lift_vs_stimulus_auroc",
    "lift_vs_stimulus_dev_mae",
    "lift_vs_stimulus_dev_rmse",
    "lift_vs_stimulus_dev_pearson",
    "lift_vs_stimulus_dev_spearman",
    "lift_vs_stimulus_dev_sign_acc",
]


def safe_float(x):
    try:
        v = float(x)
    except Exception:
        return None
    return v if math.isfinite(v) else None


def clean_json(x):
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


def md_table(rows, cols):
    if not rows:
        return "_No rows._\n"

    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")

    for row in rows:
        vals = []
        for col in cols:
            val = row.get(col, "")
            if isinstance(val, float):
                vals.append(f"{val:.4f}" if math.isfinite(val) else "")
            elif val is None:
                vals.append("")
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")

    return "\n".join(lines) + "\n"


def read_metric_file(path: Path, experiment: str, table: str, description: str):
    if not path.exists():
        return None

    df = pd.read_csv(path)
    df["experiment"] = experiment
    df["table"] = table
    df["experiment_description"] = description

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "model" in df.columns:
        df["is_stimulus_only"] = df["model"].eq("stimulus_only")
        df["is_residual_model"] = df["model"].astype(str).str.contains("residual", regex=False)
        df["is_direct_model"] = df["model"].astype(str).str.contains("direct", regex=False)
        df["is_augmented"] = df["model"].astype(str).str.endswith("_aug")
    else:
        df["is_stimulus_only"] = False
        df["is_residual_model"] = False
        df["is_direct_model"] = False
        df["is_augmented"] = False

    return df


def load_all_metrics():
    frames = []
    missing = []

    for spec in INPUT_SPECS:
        for table in ["main", "subset"]:
            path = spec[table]
            df = read_metric_file(
                path=path,
                experiment=spec["experiment"],
                table=table,
                description=spec["description"],
            )
            if df is None:
                missing.append(str(path))
            else:
                frames.append(df)

    if not frames:
        raise FileNotFoundError("No EMG metric files found.")

    all_df = pd.concat(frames, ignore_index=True, sort=False)
    return all_df, missing


def best_row(df, metric, maximize=True):
    if metric not in df.columns:
        return None

    valid = df[pd.notna(df[metric])].copy()
    if valid.empty:
        return None

    idx = valid[metric].idxmax() if maximize else valid[metric].idxmin()
    row = valid.loc[idx].to_dict()
    row["best_metric"] = metric
    row["best_metric_value"] = safe_float(row.get(metric))
    return row


def summarize_best_main(all_df):
    main = all_df[
        (all_df["table"] == "main")
        & (~all_df["is_stimulus_only"])
        & (all_df["is_residual_model"])
    ].copy()

    rows = []
    for target, g in main.groupby("target"):
        for metric, maximize in [
            ("lift_vs_stimulus_rmse", True),
            ("lift_vs_stimulus_auroc", True),
            ("lift_vs_stimulus_balanced_accuracy", True),
            ("dev_pearson", True),
            ("rmse", False),
        ]:
            r = best_row(g, metric, maximize=maximize)
            if r is None:
                continue
            rows.append(project_best_row(r, target=target, subset=None, scope="main"))

    return pd.DataFrame(rows)


def summarize_best_subset(all_df):
    subset = all_df[
        (all_df["table"] == "subset")
        & (~all_df["is_stimulus_only"])
        & (all_df["is_residual_model"])
    ].copy()

    rows = []
    for (target, subset_name), g in subset.groupby(["target", "subset"]):
        for metric, maximize in [
            ("lift_vs_stimulus_rmse", True),
            ("lift_vs_stimulus_auroc", True),
            ("lift_vs_stimulus_balanced_accuracy", True),
            ("dev_pearson", True),
            ("rmse", False),
        ]:
            r = best_row(g, metric, maximize=maximize)
            if r is None:
                continue
            rows.append(project_best_row(r, target=target, subset=subset_name, scope="subset"))

    return pd.DataFrame(rows)


def project_best_row(row, target, subset, scope):
    return {
        "scope": scope,
        "target": target,
        "subset": subset,
        "best_metric": row.get("best_metric"),
        "best_metric_value": safe_float(row.get("best_metric_value")),
        "experiment": row.get("experiment"),
        "model": row.get("model"),
        "rmse": safe_float(row.get("rmse")),
        "lift_vs_stimulus_rmse": safe_float(row.get("lift_vs_stimulus_rmse")),
        "balanced_accuracy": safe_float(row.get("balanced_accuracy")),
        "lift_vs_stimulus_balanced_accuracy": safe_float(row.get("lift_vs_stimulus_balanced_accuracy")),
        "auroc": safe_float(row.get("auroc")),
        "lift_vs_stimulus_auroc": safe_float(row.get("lift_vs_stimulus_auroc")),
        "dev_rmse": safe_float(row.get("dev_rmse")),
        "dev_pearson": safe_float(row.get("dev_pearson")),
        "pred_dev_std": safe_float(row.get("pred_dev_std")),
    }


def verdict_for_target(best_main_df, target):
    rows = best_main_df[best_main_df["target"] == target].copy()

    best_rmse_lift = rows.loc[
        rows["best_metric"].eq("lift_vs_stimulus_rmse"),
        "best_metric_value",
    ]
    best_dev = rows.loc[
        rows["best_metric"].eq("dev_pearson"),
        "best_metric_value",
    ]
    best_auroc_lift = rows.loc[
        rows["best_metric"].eq("lift_vs_stimulus_auroc"),
        "best_metric_value",
    ]

    rmse_lift = safe_float(best_rmse_lift.iloc[0]) if len(best_rmse_lift) else None
    dev = safe_float(best_dev.iloc[0]) if len(best_dev) else None
    auroc_lift = safe_float(best_auroc_lift.iloc[0]) if len(best_auroc_lift) else None

    rmse_positive = rmse_lift is not None and rmse_lift > 0
    dev_weak = dev is not None and dev >= 0.05
    dev_strong = dev is not None and dev >= 0.15
    auroc_positive = auroc_lift is not None and auroc_lift > 0

    if rmse_positive and dev_strong:
        verdict = "GO"
        reason = "Residual EMG improves RMSE and has strong deviation correlation."
    elif rmse_positive and dev_weak:
        verdict = "Conditional weak"
        reason = "Residual EMG improves RMSE and has weak positive deviation correlation."
    elif auroc_positive and not rmse_positive and not dev_weak:
        verdict = "Weak AUROC-only hint"
        reason = "Some AUROC lift exists, but no RMSE lift and no meaningful deviation correlation."
    else:
        verdict = "No robust value-add"
        reason = "No reliable RMSE lift and no meaningful deviation correlation."

    return {
        "target": target,
        "best_rmse_lift": rmse_lift,
        "best_dev_pearson": dev,
        "best_auroc_lift": auroc_lift,
        "verdict": verdict,
        "reason": reason,
    }


def overall_verdict(target_verdicts):
    statuses = {v["target"]: v["verdict"] for v in target_verdicts}

    if any(v == "GO" for v in statuses.values()):
        return {
            "verdict": "Conditional continue",
            "decision": "Continue EMG-only only if validated with nested train-subject tuning.",
            "reason": "At least one target shows a GO-level sign.",
        }

    if any(v == "Conditional weak" for v in statuses.values()):
        return {
            "verdict": "Conditional weak",
            "decision": "Do not treat EMG-only as primary; keep only as secondary/fusion candidate.",
            "reason": "Only weak target-level evidence exists.",
        }

    return {
        "verdict": "Conditional No-Go for EMG-only",
        "decision": "Close EMG-only as primary path for now; proceed to EEG-only residual probe.",
        "reason": "Across feature sets, nonlinear models, and train-only augmentation, EMG-only did not robustly beat stimulus-only.",
    }


def write_report(all_df, best_main, best_subset, missing):
    targets = sorted([t for t in all_df["target"].dropna().unique().tolist()])
    target_verdicts = [verdict_for_target(best_main, target) for target in targets]
    overall = overall_verdict(target_verdicts)

    all_df.to_csv(OUT_ALL, index=False)
    best_main.to_csv(OUT_BEST_MAIN, index=False)
    best_subset.to_csv(OUT_BEST_SUBSET, index=False)

    summary = {
        "protocol": "EMG-only closeout aggregation",
        "inputs": [
            {
                "experiment": spec["experiment"],
                "description": spec["description"],
                "main": str(spec["main"]),
                "subset": str(spec["subset"]),
            }
            for spec in INPUT_SPECS
        ],
        "missing_inputs": missing,
        "overall_verdict": overall,
        "target_verdicts": target_verdicts,
        "best_main": best_main.to_dict(orient="records"),
        "best_subset": best_subset.to_dict(orient="records"),
        "notes": [
            "This script performs no training and no new evaluation.",
            "It aggregates prior strict-LOSO EMG probes.",
            "EMG-only decision is based mainly on RMSE lift and deviation correlation.",
            "AUROC-only gains without RMSE/deviation support are treated as weak hints, not proof of physiological value-add.",
            "EMG may still be useful later in EEG+EMG fusion or uncertainty/QC analysis.",
        ],
    }

    OUT_JSON.write_text(
        json.dumps(clean_json(summary), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = []
    lines.append("# ROCA-I-DARE EMG-only Closeout Report\n")
    lines.append("This report aggregates prior EMG-only probes. No new model was trained.\n")

    lines.append("## Overall verdict\n")
    lines.append(f"**{overall['verdict']}**\n")
    lines.append(f"- Decision: {overall['decision']}")
    lines.append(f"- Reason: {overall['reason']}\n")

    lines.append("## Target verdicts\n")
    lines.append(md_table(target_verdicts, [
        "target",
        "best_rmse_lift",
        "best_dev_pearson",
        "best_auroc_lift",
        "verdict",
        "reason",
    ]))

    lines.append("\n## Best full-set residual EMG results\n")
    lines.append(md_table(best_main.to_dict(orient="records"), [
        "target",
        "best_metric",
        "best_metric_value",
        "experiment",
        "model",
        "rmse",
        "lift_vs_stimulus_rmse",
        "balanced_accuracy",
        "lift_vs_stimulus_balanced_accuracy",
        "auroc",
        "lift_vs_stimulus_auroc",
        "dev_pearson",
        "pred_dev_std",
    ]))

    lines.append("\n## Best fold-safe hard-subset residual EMG results\n")
    lines.append(md_table(best_subset.to_dict(orient="records"), [
        "target",
        "subset",
        "best_metric",
        "best_metric_value",
        "experiment",
        "model",
        "rmse",
        "lift_vs_stimulus_rmse",
        "balanced_accuracy",
        "lift_vs_stimulus_balanced_accuracy",
        "auroc",
        "lift_vs_stimulus_auroc",
        "dev_pearson",
        "pred_dev_std",
    ]))

    lines.append("\n## Interpretation\n")
    lines.append(
        "- EMG-only is closed as a primary path for now because it did not show robust RMSE improvement or meaningful deviation correlation.\n"
        "- Small AUROC gains appeared in some hard subsets, especially Valence, but they were not supported by RMSE/deviation metrics.\n"
        "- EMG should remain available for later multimodal fusion, calibration, uncertainty, or QC experiments.\n"
        "- Next recommended step: EEG-only residual probe under the same strict LOSO protocol.\n"
    )

    if missing:
        lines.append("\n## Missing inputs\n")
        for path in missing:
            lines.append(f"- `{path}`")
    else:
        lines.append("\n## Missing inputs\n")
        lines.append("- None.")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 04g completed.")
    print(f"wrote: {OUT_MD}")
    print(f"wrote: {OUT_JSON}")
    print(f"wrote: {OUT_ALL}")
    print(f"wrote: {OUT_BEST_MAIN}")
    print(f"wrote: {OUT_BEST_SUBSET}")
    print()
    print("Overall verdict:")
    print(f"  {overall['verdict']}")
    print(f"  {overall['decision']}")
    print()
    print("Target verdicts:")
    print(pd.DataFrame(target_verdicts).to_string(index=False))
    print()
    print("Best full-set rows:")
    print(best_main[
        [
            "target",
            "best_metric",
            "best_metric_value",
            "experiment",
            "model",
            "lift_vs_stimulus_rmse",
            "lift_vs_stimulus_auroc",
            "dev_pearson",
        ]
    ].to_string(index=False))


def main():
    all_df, missing = load_all_metrics()
    best_main = summarize_best_main(all_df)
    best_subset = summarize_best_subset(all_df)

    write_report(all_df, best_main, best_subset, missing)


if __name__ == "__main__":
    main()
