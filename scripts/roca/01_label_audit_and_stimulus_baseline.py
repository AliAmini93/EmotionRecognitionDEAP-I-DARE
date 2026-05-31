#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
TRIAL_INDEX = ROOT / ".cache" / "idare_trial_index.csv"
OUT_DIR = ROOT / "docs" / "roca"

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


def ccc(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y, p = y[m], p[m]
    if len(y) < 2:
        return None
    my, mp = y.mean(), p.mean()
    vy, vp = y.var(), p.var()
    cov = np.mean((y - my) * (p - mp))
    den = vy + vp + (my - mp) ** 2
    if den == 0:
        return None
    return float(2 * cov / den)


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
    rank_sum_pos = ranks[y_bin == 1].sum()
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def metrics(y, pred, p_high):
    y = np.asarray(y, dtype=float)
    pred = np.asarray(pred, dtype=float)
    p_high = np.asarray(p_high, dtype=float)
    m = np.isfinite(y) & np.isfinite(pred) & np.isfinite(p_high)
    y, pred, p_high = y[m], pred[m], p_high[m]

    err = pred - y
    y_bin = (y > 5).astype(int)
    y_hat = (p_high >= 0.5).astype(int)

    acc = float((y_bin == y_hat).mean())

    recalls = []
    f1s = []
    for cls in [0, 1]:
        tp = int(((y_bin == cls) & (y_hat == cls)).sum())
        fp = int(((y_bin != cls) & (y_hat == cls)).sum())
        fn = int(((y_bin == cls) & (y_hat != cls)).sum())
        support = int((y_bin == cls).sum())
        if support > 0:
            recalls.append(tp / support)
        den = 2 * tp + fp + fn
        f1s.append((2 * tp / den) if den > 0 else 0.0)

    return {
        "n": int(len(y)),
        "mae": safe_float(np.mean(np.abs(err))),
        "rmse": safe_float(np.sqrt(np.mean(err * err))),
        "pearson": pearson(y, pred),
        "spearman": spearman(y, pred),
        "ccc": ccc(y, pred),
        "accuracy": acc,
        "balanced_accuracy": safe_float(np.mean(recalls)),
        "macro_f1": safe_float(np.mean(f1s)),
        "auroc": auroc(y_bin, p_high),
    }


def entropy_binary(p):
    p = float(p)
    if p <= 0 or p >= 1:
        return 0.0
    return float(-(p * math.log(p) + (1 - p) * math.log(1 - p)))


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
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for r in rows:
        vals = []
        for c in cols:
            v = r.get(c, "")
            if isinstance(v, float):
                vals.append(f"{v:.4f}" if math.isfinite(v) else "")
            elif v is None:
                vals.append("")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def load_df():
    if not TRIAL_INDEX.exists():
        raise FileNotFoundError(TRIAL_INDEX)

    df = pd.read_csv(TRIAL_INDEX)
    required = ["subject_id", "stimulus_id", "valence_score", "arousal_score"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing columns: {missing}")

    df = df.copy()
    df["subject_id"] = df["subject_id"].astype(int)
    df["stimulus_id"] = df["stimulus_id"].astype(str)
    for col in TARGETS.values():
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=list(TARGETS.values())).reset_index(drop=True)
    return df


def label_audit(df):
    out = {
        "trial_index": str(TRIAL_INDEX),
        "n_rows": int(len(df)),
        "n_subjects": int(df["subject_id"].nunique()),
        "n_stimuli": int(df["stimulus_id"].nunique()),
        "targets": {},
    }

    for target, col in TARGETS.items():
        s = df[col]
        counts = s.astype(int).value_counts().sort_index()
        counts = {str(i): int(counts.get(i, 0)) for i in range(1, 10)}

        stim = df.groupby("stimulus_id")[col].agg(["count", "mean", "std", "min", "max"]).reset_index()
        stim["high_rate"] = df.groupby("stimulus_id")[col].apply(lambda x: float((x > 5).mean())).values
        stim["entropy_high_low"] = stim["high_rate"].apply(entropy_binary)

        subj = df.groupby("subject_id")[col].agg(["count", "mean", "std", "min", "max"]).reset_index()
        subj["high_rate"] = df.groupby("subject_id")[col].apply(lambda x: float((x > 5).mean())).values

        n_low = int((s <= 5).sum())
        n_high = int((s > 5).sum())
        n = int(len(s))

        out["targets"][target] = {
            "n": n,
            "mean": safe_float(s.mean()),
            "std": safe_float(s.std()),
            "min": safe_float(s.min()),
            "max": safe_float(s.max()),
            "score_counts_1_to_9": counts,
            "low_y_le_5": n_low,
            "high_y_gt_5": n_high,
            "minority_rate": safe_float(min(n_low, n_high) / n),
            "near_midpoint_4_5_6": int(s.between(4, 6, inclusive="both").sum()),
            "near_midpoint_rate": safe_float(s.between(4, 6, inclusive="both").mean()),
            "subject_mean_min": safe_float(subj["mean"].min()),
            "subject_mean_max": safe_float(subj["mean"].max()),
            "subject_mean_std": safe_float(subj["mean"].std()),
            "stimulus_mean_std": safe_float(stim["mean"].std()),
            "mean_stimulus_std": safe_float(stim["std"].mean()),
            "top10_disagreement_by_std": stim.sort_values("std", ascending=False)
                [["stimulus_id", "count", "mean", "std", "high_rate", "entropy_high_low"]]
                .head(10).to_dict(orient="records"),
            "top10_disagreement_by_entropy": stim.sort_values("entropy_high_low", ascending=False)
                [["stimulus_id", "count", "mean", "std", "high_rate", "entropy_high_low"]]
                .head(10).to_dict(orient="records"),
        }

    return out


def run_loso_baselines(df):
    pred_rows = []

    for test_subject in sorted(df["subject_id"].unique()):
        train = df[df["subject_id"] != test_subject]
        test = df[df["subject_id"] == test_subject]

        for target, col in TARGETS.items():
            global_mean = float(train[col].mean())
            global_p_high = float((train[col] > 5).mean())

            stim_mean = train.groupby("stimulus_id")[col].mean()
            stim_p_high = train.groupby("stimulus_id")[col].apply(lambda x: float((x > 5).mean()))

            base = test[["subject_id", "stimulus_id", col]].rename(
                columns={"subject_id": "test_subject", col: "y_true_score"}
            )
            base["target"] = target

            g = base.copy()
            g["model"] = "global_mean"
            g["y_pred_score"] = global_mean
            g["p_high"] = global_p_high
            g["train_stimulus_mean"] = np.nan
            g["true_deviation_from_train_stimulus_mean"] = np.nan
            pred_rows.append(g)

            st = base.copy()
            st["model"] = "stimulus_only"
            st["train_stimulus_mean"] = st["stimulus_id"].map(stim_mean).astype(float)
            st["y_pred_score"] = st["train_stimulus_mean"]
            st["p_high"] = st["stimulus_id"].map(stim_p_high).astype(float)
            st["true_deviation_from_train_stimulus_mean"] = (
                st["y_true_score"] - st["train_stimulus_mean"]
            )
            pred_rows.append(st)

    pred = pd.concat(pred_rows, ignore_index=True)

    main = []
    per_subject = []

    for target in TARGETS:
        for model in ["global_mean", "stimulus_only"]:
            sub = pred[(pred["target"] == target) & (pred["model"] == model)]
            row = {"target": target, "model": model}
            row.update(metrics(sub["y_true_score"], sub["y_pred_score"], sub["p_high"]))
            main.append(row)

            for sid, g in sub.groupby("test_subject"):
                ps = {"target": target, "model": model, "test_subject": int(sid)}
                ps.update(metrics(g["y_true_score"], g["y_pred_score"], g["p_high"]))
                per_subject.append(ps)

    main_df = pd.DataFrame(main)
    per_subject_df = pd.DataFrame(per_subject)
    return pred, main_df, per_subject_df


def write_reports(label, pred, main_df, per_subject_df):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    (OUT_DIR / "label_audit_current.json").write_text(
        json.dumps(clean_json(label), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    label_lines = ["# ROCA-I-DARE Label Audit\n"]
    label_lines.append("No EEG/EMG model was trained.\n")
    label_lines.append("## Dataset Summary\n")
    label_lines.append(md_table([
        {"item": "rows", "value": label["n_rows"]},
        {"item": "subjects", "value": label["n_subjects"]},
        {"item": "stimuli", "value": label["n_stimuli"]},
    ], ["item", "value"]))

    for target, info in label["targets"].items():
        label_lines.append(f"\n## {target}\n")
        label_lines.append(md_table([
            {"metric": "n", "value": info["n"]},
            {"metric": "mean", "value": info["mean"]},
            {"metric": "std", "value": info["std"]},
            {"metric": "low_y_le_5", "value": info["low_y_le_5"]},
            {"metric": "high_y_gt_5", "value": info["high_y_gt_5"]},
            {"metric": "minority_rate", "value": info["minority_rate"]},
            {"metric": "near_midpoint_rate", "value": info["near_midpoint_rate"]},
            {"metric": "stimulus_mean_std", "value": info["stimulus_mean_std"]},
            {"metric": "mean_stimulus_std", "value": info["mean_stimulus_std"]},
        ], ["metric", "value"]))

        label_lines.append("\n### Score counts\n")
        label_lines.append(md_table(
            [{"score": k, "count": v} for k, v in info["score_counts_1_to_9"].items()],
            ["score", "count"],
        ))

        label_lines.append("\n### Top disagreement by STD\n")
        label_lines.append(md_table(
            info["top10_disagreement_by_std"],
            ["stimulus_id", "count", "mean", "std", "high_rate", "entropy_high_low"],
        ))

    (OUT_DIR / "label_audit_current.md").write_text("\n".join(label_lines), encoding="utf-8")

    pred.to_csv(OUT_DIR / "stimulus_only_predictions_current.csv", index=False)
    per_subject_df.to_csv(OUT_DIR / "stimulus_only_per_subject_metrics_current.csv", index=False)

    baseline_summary = {
        "protocol": "strict_loso",
        "notes": [
            "Each test subject is excluded from global and stimulus means.",
            "High/low is derived as score > 5.",
            "Later EEG/EMG probes must beat stimulus-only.",
        ],
        "main_metrics": main_df.to_dict(orient="records"),
    }
    (OUT_DIR / "stimulus_only_baseline_current.json").write_text(
        json.dumps(clean_json(baseline_summary), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    cols = [
        "target", "model", "n", "mae", "rmse", "pearson", "spearman",
        "ccc", "accuracy", "balanced_accuracy", "macro_f1", "auroc",
    ]
    baseline_lines = ["# ROCA-I-DARE Stimulus-Only Baseline\n"]
    baseline_lines.append("Protocol: strict LOSO. No EEG/EMG model was trained.\n")
    baseline_lines.append("## Main metrics\n")
    baseline_lines.append(md_table(main_df.to_dict(orient="records"), cols))

    (OUT_DIR / "stimulus_only_baseline_current.md").write_text(
        "\n".join(baseline_lines),
        encoding="utf-8",
    )


def main():
    df = load_df()
    label = label_audit(df)
    pred, main_df, per_subject_df = run_loso_baselines(df)
    write_reports(label, pred, main_df, per_subject_df)

    print("ROCA step 01 completed.")
    print(f"rows: {len(df)}")
    print(f"subjects: {df['subject_id'].nunique()}")
    print(f"stimuli: {df['stimulus_id'].nunique()}")
    print()
    print(main_df[[
        "target", "model", "mae", "rmse", "pearson",
        "balanced_accuracy", "macro_f1", "auroc"
    ]].to_string(index=False))


if __name__ == "__main__":
    main()
