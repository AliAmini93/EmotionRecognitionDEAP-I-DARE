#!/usr/bin/env python3
"""
Analyze valence fold/class-bias diagnostics from existing cache index and smoke JSON.

This script does not train a model.
It does not load raw MATLAB/HDF5 files.
It only reads:
- .cache/idare_eeg_cache_index.csv
- docs/idare_eeg_cache_recipe_stabilization_valence_threshold_aggregate_compare_smoke.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_INDEX = ROOT / ".cache" / "idare_eeg_cache_index.csv"
DEFAULT_SMOKE_JSON = ROOT / "docs" / "idare_eeg_cache_recipe_stabilization_valence_threshold_aggregate_compare_smoke.json"
DEFAULT_OUT_MD = ROOT / "docs" / "idare_valence_fold_bias_diagnostics.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "idare_valence_fold_bias_diagnostics.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-index", type=Path, default=DEFAULT_CACHE_INDEX)
    parser.add_argument("--smoke-json", type=Path, default=DEFAULT_SMOKE_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--label-col", default="valence_midpoint_as_high")
    return parser.parse_args()


def count_labels(values: list[int]) -> dict[str, int]:
    return {
        "0": int(sum(1 for v in values if int(v) == 0)),
        "1": int(sum(1 for v in values if int(v) == 1)),
    }


def ratio(counts: dict[str, int]) -> dict[str, float]:
    total = counts["0"] + counts["1"]
    if total == 0:
        return {"0": 0.0, "1": 0.0}
    return {
        "0": counts["0"] / total,
        "1": counts["1"] / total,
    }


def subject_label_table(df: pd.DataFrame, subjects: list[int], label_col: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for subject in sorted(int(s) for s in subjects):
        sdf = df[df["subject_id"].astype(int) == int(subject)].copy()
        labels = [int(v) for v in sdf[label_col].tolist()]
        counts = count_labels(labels)
        ratios = ratio(counts)
        rows.append(
            {
                "subject_id": int(subject),
                "n": int(len(sdf)),
                "label_counts": counts,
                "label_ratio": ratios,
            }
        )
    return rows


def main() -> None:
    args = parse_args()

    if not args.cache_index.exists():
        raise FileNotFoundError(args.cache_index)
    if not args.smoke_json.exists():
        raise FileNotFoundError(args.smoke_json)

    df = pd.read_csv(args.cache_index)
    if args.label_col not in df.columns:
        raise KeyError(f"Missing label column: {args.label_col}")

    df = df[df[args.label_col].isin([0, 1, 0.0, 1.0])].copy()
    df[args.label_col] = df[args.label_col].astype(int)
    df["subject_id"] = df["subject_id"].astype(int)

    smoke = json.loads(args.smoke_json.read_text(encoding="utf-8"))

    fold_rows: list[dict[str, Any]] = []
    for run in smoke["runs"]:
        fold_id = int(run["fold_id"])
        val_subjects = [int(s) for s in run["val_subjects"]]
        all_subjects = sorted(int(s) for s in df["subject_id"].unique().tolist())
        train_subjects = [s for s in all_subjects if s not in set(val_subjects)]

        train_df = df[df["subject_id"].isin(train_subjects)].copy()
        val_df = df[df["subject_id"].isin(val_subjects)].copy()

        train_labels = [int(v) for v in train_df[args.label_col].tolist()]
        val_labels = [int(v) for v in val_df[args.label_col].tolist()]

        final = run["final"]
        prob = final["prob1_summary"]
        best = final["threshold_sweep"]["best"]

        fold_rows.append(
            {
                "run_id": int(run["run_id"]),
                "recipe": run["recipe"],
                "sampler": run.get("sampler"),
                "fold_id": fold_id,
                "val_subjects": val_subjects,
                "train_counts_from_cache_index": count_labels(train_labels),
                "train_ratio_from_cache_index": ratio(count_labels(train_labels)),
                "val_counts_from_cache_index": count_labels(val_labels),
                "val_ratio_from_cache_index": ratio(count_labels(val_labels)),
                "run_train_counts": run.get("train_counts"),
                "run_val_counts": run.get("val_counts"),
                "argmax_pred_counts": final["pred_counts"],
                "confusion": final["confusion"],
                "argmax_macro_f1": final["macro_f1"],
                "argmax_balanced_accuracy": final["balanced_accuracy"],
                "prob1_summary": {
                    "mean": prob["mean"],
                    "q05": prob["q05"],
                    "median": prob["median"],
                    "q95": prob["q95"],
                },
                "threshold_best": {
                    "threshold": best["threshold"],
                    "macro_f1": best["macro_f1"],
                    "balanced_accuracy": best["balanced_accuracy"],
                    "pred_counts": best["pred_counts"],
                },
                "val_subject_label_table": subject_label_table(df, val_subjects, args.label_col),
            }
        )

    report = {
        "status": "valence_fold_bias_diagnostics",
        "inputs": {
            "cache_index": str(args.cache_index),
            "smoke_json": str(args.smoke_json),
            "label_col": args.label_col,
        },
        "fold_rows": fold_rows,
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines: list[str] = []
    lines.append("# I-DARE Valence Fold-Bias Diagnostics")
    lines.append("")
    lines.append("This diagnostic reads the cache index and existing smoke JSON only.")
    lines.append("")
    lines.append("It does not train a model and does not load raw MATLAB/HDF5 files.")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- cache_index: `{args.cache_index}`")
    lines.append(f"- smoke_json: `{args.smoke_json}`")
    lines.append(f"- label_col: `{args.label_col}`")
    lines.append("")
    lines.append("## Run-Level Diagnostics")
    lines.append("")
    lines.append("| Run | Recipe | Fold | Train 0 | Train 1 | Val 0 | Val 1 | Pred 0 | Pred 1 | Macro F1 | Bal acc | P1 mean | P1 median | Best threshold |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for row in fold_rows:
        tc = row["train_counts_from_cache_index"]
        vc = row["val_counts_from_cache_index"]
        pc = row["argmax_pred_counts"]
        prob = row["prob1_summary"]
        best = row["threshold_best"]
        lines.append(
            "| {run_id} | {recipe} | {fold} | {t0} | {t1} | {v0} | {v1} | {p0} | {p1} | {mf1:.4f} | {ba:.4f} | {pm:.4f} | {pmed:.4f} | {thr:.2f} |".format(
                run_id=row["run_id"],
                recipe=row["recipe"],
                fold=row["fold_id"],
                t0=tc["0"],
                t1=tc["1"],
                v0=vc["0"],
                v1=vc["1"],
                p0=pc["0"],
                p1=pc["1"],
                mf1=float(row["argmax_macro_f1"]),
                ba=float(row["argmax_balanced_accuracy"]),
                pm=float(prob["mean"]),
                pmed=float(prob["median"]),
                thr=float(best["threshold"]),
            )
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- This file is diagnostic only.")
    lines.append("- It is intended to explain fold/class-bias behavior before any broader run.")
    lines.append("- If fold 2 has near-collapse despite similar validation label counts, the issue is more likely model/probability bias than a trivial validation-label imbalance.")
    lines.append("- Any follow-up should remain smoke-first.")

    args.out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[DONE] wrote {args.out_md}")
    print(f"[DONE] wrote {args.out_json}")


if __name__ == "__main__":
    main()
