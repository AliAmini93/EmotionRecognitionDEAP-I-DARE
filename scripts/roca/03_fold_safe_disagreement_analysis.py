#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROCA_DIR = ROOT / "docs" / "roca"
TRIAL_INDEX = ROOT / ".cache" / "idare_trial_index.csv"
PRED_CSV = ROCA_DIR / "stimulus_only_predictions_current.csv"

OUT_MD = ROCA_DIR / "fold_safe_disagreement_current.md"
OUT_JSON = ROCA_DIR / "fold_safe_disagreement_current.json"
OUT_ROWS_CSV = ROCA_DIR / "fold_safe_disagreement_rows_current.csv"
OUT_SUBSET_CSV = ROCA_DIR / "fold_safe_high_disagreement_subset_metrics_current.csv"
OUT_SELECTED_STIM_CSV = ROCA_DIR / "fold_safe_selected_stimuli_current.csv"

TARGETS = {
    "valence": "valence_score",
    "arousal": "arousal_score",
}


def safe_float(x):
    try:
        v = float(x)
    except Exception:
        return None
    return v if math.isfinite(v) else None


def entropy_binary(p):
    p = float(p)
    if p <= 0 or p >= 1:
        return 0.0
    return float(-(p * math.log(p) + (1.0 - p) * math.log(1.0 - p)))


def pearson(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y, p = y[m], p[m]
    if len(y) < 2 or np.std(y) == 0 or np.std(p) == 0:
        return None
    return float(np.corrcoef(y, p)[0, 1])


def spearman(y, p):
    yr = pd.Series(y).rank(method="average").to_numpy()
    pr = pd.Series(p).rank(method="average").to_numpy()
    return pearson(yr, pr)


def auroc(y_bin, score):
    y_bin = np.asarray(y_bin, dtype=int)
    score = np.asarray(score, dtype=float)
    m = np.isfinite(score)
    y_bin, score = y_bin[m], score[m]
    n_pos = int((y_bin == 1).sum())
    n_neg = int((y_bin == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return None
    ranks = pd.Series(score).rank(method="average").to_numpy()
    rank_sum_pos = float(ranks[y_bin == 1].sum())
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def prediction_metrics(df):
    y = df["y_true_score"].to_numpy(dtype=float)
    pred = df["y_pred_score"].to_numpy(dtype=float)
    p_high = df["p_high"].to_numpy(dtype=float)

    err = pred - y
    y_bin = (y > 5).astype(int)
    y_hat = (p_high >= 0.5).astype(int)

    recalls = []
    f1s = []
    for cls in [0, 1]:
        tp = int(((y_bin == cls) & (y_hat == cls)).sum())
        fp = int(((y_bin != cls) & (y_hat == cls)).sum())
        fn = int(((y_bin == cls) & (y_hat != cls)).sum())
        support = int((y_bin == cls).sum())
        if support > 0:
            recalls.append(tp / support)
        denom = 2 * tp + fp + fn
        f1s.append((2 * tp / denom) if denom > 0 else 0.0)

    return {
        "n": int(len(df)),
        "mae": safe_float(np.mean(np.abs(err))),
        "rmse": safe_float(np.sqrt(np.mean(err * err))),
        "pearson": pearson(y, pred),
        "spearman": spearman(y, pred),
        "accuracy": safe_float(np.mean(y_bin == y_hat)),
        "balanced_accuracy": safe_float(np.mean(recalls)),
        "macro_f1": safe_float(np.mean(f1s)),
        "auroc": auroc(y_bin, p_high),
    }


def deviation_metrics(df):
    d = df["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
    abs_d = np.abs(d)
    return {
        "deviation_std": safe_float(np.std(d)),
        "mean_abs_deviation": safe_float(np.mean(abs_d)),
        "rmse_zero_deviation": safe_float(np.sqrt(np.mean(d * d))),
        "prop_abs_dev_ge_1p0": safe_float(np.mean(abs_d >= 1.0)),
        "prop_abs_dev_ge_2p0": safe_float(np.mean(abs_d >= 2.0)),
        "positive_deviation_rate": safe_float(np.mean(d > 0)),
    }


def md_table(rows, cols):
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


def load_inputs():
    if not TRIAL_INDEX.exists():
        raise FileNotFoundError(f"Missing trial index: {TRIAL_INDEX}")
    if not PRED_CSV.exists():
        raise FileNotFoundError(f"Missing stimulus-only predictions: {PRED_CSV}")

    trial = pd.read_csv(TRIAL_INDEX)
    pred = pd.read_csv(PRED_CSV)

    trial_required = ["subject_id", "stimulus_id", "valence_score", "arousal_score"]
    pred_required = [
        "target",
        "test_subject",
        "stimulus_id",
        "model",
        "y_true_score",
        "y_pred_score",
        "p_high",
        "true_deviation_from_train_stimulus_mean",
    ]

    missing_trial = [c for c in trial_required if c not in trial.columns]
    missing_pred = [c for c in pred_required if c not in pred.columns]
    if missing_trial:
        raise KeyError(f"Trial index missing columns: {missing_trial}")
    if missing_pred:
        raise KeyError(f"Prediction CSV missing columns: {missing_pred}")

    trial = trial.copy()
    trial["subject_id"] = trial["subject_id"].astype(int)
    trial["stimulus_id"] = trial["stimulus_id"].astype(str)

    for col in TARGETS.values():
        trial[col] = pd.to_numeric(trial[col], errors="coerce")

    trial = trial.dropna(subset=list(TARGETS.values())).reset_index(drop=True)

    pred = pred[pred["model"] == "stimulus_only"].copy()
    pred["test_subject"] = pred["test_subject"].astype(int)
    pred["stimulus_id"] = pred["stimulus_id"].astype(str)

    return trial, pred


def fold_train_disagreement_stats(train_df, score_col):
    rows = []
    for stim, g in train_df.groupby("stimulus_id"):
        scores = g[score_col].to_numpy(dtype=float)
        high_rate = float(np.mean(scores > 5))
        rows.append({
            "stimulus_id": str(stim),
            "train_n_subjects": int(len(g)),
            "train_score_mean": safe_float(np.mean(scores)),
            "train_score_std": safe_float(np.std(scores)),
            "train_high_rate": safe_float(high_rate),
            "train_high_low_entropy": safe_float(entropy_binary(high_rate)),
        })
    return pd.DataFrame(rows)


def main():
    trial, pred = load_inputs()

    subjects = sorted(trial["subject_id"].unique().tolist())
    expected_subjects = sorted(pred["test_subject"].unique().tolist())
    if subjects != expected_subjects:
        raise ValueError("Mismatch between trial subjects and prediction test subjects.")

    row_records = []
    selected_records = []
    subset_records = []

    subset_specs = [
        ("top25_train_score_std", "train_score_std"),
        ("top25_train_entropy", "train_high_low_entropy"),
    ]

    for target, score_col in TARGETS.items():
        for test_subject in subjects:
            train = trial[trial["subject_id"] != test_subject].copy()
            fold_pred = pred[
                (pred["target"] == target) &
                (pred["test_subject"] == test_subject)
            ].copy()

            if len(fold_pred) != 32:
                raise ValueError(
                    f"Expected 32 prediction rows for target={target}, "
                    f"subject={test_subject}, got {len(fold_pred)}"
                )

            stats = fold_train_disagreement_stats(train, score_col)
            fold_rows = fold_pred.merge(stats, on="stimulus_id", how="left")

            if fold_rows[["train_score_std", "train_high_low_entropy"]].isna().any().any():
                raise ValueError(f"Missing train-only disagreement stats for subject={test_subject}, target={target}")

            row_records.extend(fold_rows.to_dict(orient="records"))

            for subset_name, rank_col in subset_specs:
                selected = (
                    stats.sort_values(rank_col, ascending=False)
                    .head(8)
                    .copy()
                )
                selected["target"] = target
                selected["test_subject"] = int(test_subject)
                selected["subset"] = subset_name
                selected["rank_col"] = rank_col
                selected["rank_within_fold"] = list(range(1, len(selected) + 1))
                selected_records.extend(selected.to_dict(orient="records"))

                stim_ids = set(selected["stimulus_id"].astype(str).tolist())
                sub = fold_rows[fold_rows["stimulus_id"].astype(str).isin(stim_ids)].copy()
                if len(sub) != 8:
                    raise ValueError(
                        f"Expected 8 rows for subset={subset_name}, target={target}, "
                        f"subject={test_subject}, got {len(sub)}"
                    )

                sub_row = {
                    "target": target,
                    "test_subject": int(test_subject),
                    "subset": subset_name,
                    "n_stimuli": int(len(stim_ids)),
                    "n_trials": int(len(sub)),
                }
                sub_row.update(prediction_metrics(sub))
                sub_row.update(deviation_metrics(sub))
                subset_records.append(sub_row)

    rows_df = pd.DataFrame(row_records)
    selected_df = pd.DataFrame(selected_records)
    subset_fold_df = pd.DataFrame(subset_records)

    # Aggregate subset metrics over all held-out rows.
    aggregate_rows = []
    for target in TARGETS:
        for subset_name, _ in subset_specs:
            keys = subset_fold_df[
                (subset_fold_df["target"] == target) &
                (subset_fold_df["subset"] == subset_name)
            ][["test_subject", "target", "subset"]]

            # Easier and safer: rebuild from row-level file using selected table.
            selected_key = selected_df[
                (selected_df["target"] == target) &
                (selected_df["subset"] == subset_name)
            ][["test_subject", "stimulus_id"]].copy()

            selected_key["is_selected"] = True
            selected_key["test_subject"] = selected_key["test_subject"].astype(int)
            selected_key["stimulus_id"] = selected_key["stimulus_id"].astype(str)

            target_rows = rows_df[rows_df["target"] == target].copy()
            merged = target_rows.merge(
                selected_key,
                on=["test_subject", "stimulus_id"],
                how="left",
            )
            agg_df = merged[merged["is_selected"] == True].copy()

            agg_row = {
                "target": target,
                "subset": subset_name,
                "n_subjects": int(agg_df["test_subject"].nunique()),
                "n_stimuli_per_subject": 8,
                "n_trials": int(len(agg_df)),
            }
            agg_row.update(prediction_metrics(agg_df))
            agg_row.update(deviation_metrics(agg_df))
            aggregate_rows.append(agg_row)

    aggregate_df = pd.DataFrame(aggregate_rows)

    rows_df.to_csv(OUT_ROWS_CSV, index=False)
    selected_df.to_csv(OUT_SELECTED_STIM_CSV, index=False)
    aggregate_df.to_csv(OUT_SUBSET_CSV, index=False)

    summary = {
        "protocol": "fold-safe LOSO disagreement analysis",
        "description": (
            "For each held-out subject, high-disagreement stimuli are selected using "
            "train subjects only. The held-out subject label is never used to define "
            "the subset."
        ),
        "inputs": {
            "trial_index": str(TRIAL_INDEX),
            "stimulus_only_predictions": str(PRED_CSV),
        },
        "counts": {
            "subjects": int(len(subjects)),
            "targets": list(TARGETS.keys()),
            "row_level_records": int(len(rows_df)),
            "selected_stimulus_records": int(len(selected_df)),
            "aggregate_subset_rows": int(len(aggregate_df)),
        },
        "aggregate_subset_metrics": aggregate_df.to_dict(orient="records"),
        "official_subsets": [
            "top25_train_score_std",
            "top25_train_entropy",
        ],
        "not_official": [
            "Any subset selected using held-out/test subject labels.",
            "Any subset selected using true deviation from test labels.",
        ],
    }

    OUT_JSON.write_text(
        json.dumps(clean_json(summary), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = []
    lines.append("# ROCA-I-DARE Fold-safe High-disagreement Analysis\n")
    lines.append("No EEG/EMG model was trained.\n")
    lines.append(
        "For each LOSO fold, high-disagreement stimuli are selected using train subjects only.\n"
    )

    lines.append("## Aggregate official subset metrics\n")
    cols = [
        "target",
        "subset",
        "n_subjects",
        "n_stimuli_per_subject",
        "n_trials",
        "mae",
        "rmse",
        "pearson",
        "spearman",
        "balanced_accuracy",
        "macro_f1",
        "auroc",
        "mean_abs_deviation",
        "prop_abs_dev_ge_1p0",
        "prop_abs_dev_ge_2p0",
    ]
    lines.append(md_table(aggregate_df.to_dict(orient="records"), cols))

    lines.append("\n## Interpretation\n")
    lines.append(
        "- These subsets are official/evaluation-safe because they are selected train-only inside each fold.\n"
        "- Later EEG/EMG probes should report both full-test performance and these fold-safe high-disagreement subsets.\n"
        "- Subsets selected using test deviation or all-subject disagreement remain exploratory only.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 03 completed.")
    print(f"wrote: {OUT_MD}")
    print(f"wrote: {OUT_JSON}")
    print(f"wrote: {OUT_ROWS_CSV}")
    print(f"wrote: {OUT_SELECTED_STIM_CSV}")
    print(f"wrote: {OUT_SUBSET_CSV}")
    print()
    print("Fold-safe aggregate subset metrics:")
    print(
        aggregate_df[
            [
                "target",
                "subset",
                "n_trials",
                "mae",
                "rmse",
                "balanced_accuracy",
                "macro_f1",
                "auroc",
                "mean_abs_deviation",
                "prop_abs_dev_ge_1p0",
                "prop_abs_dev_ge_2p0",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
