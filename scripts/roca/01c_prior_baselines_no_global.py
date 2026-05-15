#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / ".cache"
ROCA_DIR = ROOT / "docs" / "roca"

DEFAULT_IDARE_TRIAL_INDEX = CACHE_DIR / "idare_trial_index.csv"
DEFAULT_DEAP_DIR = Path("/mnt/HDD/AliWorks/DEAP/data_preprocessed_python")

TARGETS = {
    "valence": "valence_score",
    "arousal": "arousal_score",
}

LABEL_POLICIES = ["midpoint_as_low", "midpoint_as_high", "discard_midpoint"]
EPS = 1e-12


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", choices=["idare", "deap", "both"], default="both")
    p.add_argument("--idare-trial-index", type=Path, default=DEFAULT_IDARE_TRIAL_INDEX)
    p.add_argument("--deap-dir", type=Path, default=DEFAULT_DEAP_DIR)
    p.add_argument("--out-prefix", type=str, default="prior_baselines_no_global_current")
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
    return x


def pearson(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y, p = y[m], p[m]
    if len(y) < 2 or np.std(y) < EPS or np.std(p) < EPS:
        return None
    return float(np.corrcoef(y, p)[0, 1])


def spearman(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    if m.sum() < 2:
        return None
    yr = pd.Series(y[m]).rank(method="average").to_numpy()
    pr = pd.Series(p[m]).rank(method="average").to_numpy()
    return pearson(yr, pr)


def ccc(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    y, p = y[m], p[m]
    if len(y) < 2:
        return None
    vy = float(np.var(y))
    vp = float(np.var(p))
    denom = vy + vp + (float(np.mean(y)) - float(np.mean(p))) ** 2
    if denom < EPS:
        return None
    return float(2.0 * np.cov(y, p, bias=True)[0, 1] / denom)


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


def continuous_metrics(y, pred):
    y = np.asarray(y, dtype=float)
    pred = np.asarray(pred, dtype=float)
    m = np.isfinite(y) & np.isfinite(pred)
    y, pred = y[m], pred[m]
    err = pred - y
    return {
        "n": int(len(y)),
        "mae": safe_float(np.mean(np.abs(err))),
        "rmse": safe_float(np.sqrt(np.mean(err * err))),
        "pearson": pearson(y, pred),
        "spearman": spearman(y, pred),
        "ccc": ccc(y, pred),
        "y_true_mean": safe_float(np.mean(y)),
        "y_true_std": safe_float(np.std(y)),
        "y_pred_mean": safe_float(np.mean(pred)),
        "y_pred_std": safe_float(np.std(pred)),
        "residual_mean": safe_float(np.mean(y - pred)),
        "residual_std": safe_float(np.std(y - pred)),
        "rmse_over_y_std": safe_float(np.sqrt(np.mean(err * err)) / (np.std(y) + EPS)),
    }


def label_array(y, policy: str):
    y = np.asarray(y, dtype=float)
    out = np.full(len(y), np.nan, dtype=float)
    if policy == "midpoint_as_low":
        out[:] = (y > 5.0).astype(float)
    elif policy == "midpoint_as_high":
        out[:] = (y >= 5.0).astype(float)
    elif policy == "discard_midpoint":
        m = y != 5.0
        out[m] = (y[m] > 5.0).astype(float)
    else:
        raise ValueError(policy)
    return out


def binary_metrics_from_score(y, score, policy: str):
    y = np.asarray(y, dtype=float)
    score = np.asarray(score, dtype=float)
    labels = label_array(y, policy)
    m = np.isfinite(labels) & np.isfinite(score)
    labels = labels[m].astype(int)
    score = score[m]

    if policy == "midpoint_as_high":
        pred = (score >= 5.0).astype(int)
    else:
        pred = (score > 5.0).astype(int)

    return binary_metrics(labels, pred, score)


def binary_metrics_from_probability(y, p_high, policy: str):
    labels = label_array(y, policy)
    p_high = np.asarray(p_high, dtype=float)
    m = np.isfinite(labels) & np.isfinite(p_high)
    labels = labels[m].astype(int)
    p_high = p_high[m]
    pred = (p_high >= 0.5).astype(int)
    return binary_metrics(labels, pred, p_high)


def binary_metrics(labels, pred, score):
    labels = np.asarray(labels, dtype=int)
    pred = np.asarray(pred, dtype=int)
    score = np.asarray(score, dtype=float)

    if len(labels) == 0:
        return {
            "binary_n": 0,
            "accuracy": None,
            "balanced_accuracy": None,
            "macro_f1": None,
            "auroc": None,
            "n_low": 0,
            "n_high": 0,
            "true_high_rate": None,
            "pred_high_rate": None,
        }

    recalls = []
    f1s = []
    for cls in [0, 1]:
        tp = int(((labels == cls) & (pred == cls)).sum())
        fp = int(((labels != cls) & (pred == cls)).sum())
        fn = int(((labels == cls) & (pred != cls)).sum())
        support = int((labels == cls).sum())
        if support > 0:
            recalls.append(tp / support)
        denom = 2 * tp + fp + fn
        f1s.append((2 * tp / denom) if denom > 0 else 0.0)

    return {
        "binary_n": int(len(labels)),
        "accuracy": safe_float(np.mean(labels == pred)),
        "balanced_accuracy": safe_float(np.mean(recalls)) if recalls else None,
        "macro_f1": safe_float(np.mean(f1s)),
        "auroc": auroc(labels, score),
        "n_low": int((labels == 0).sum()),
        "n_high": int((labels == 1).sum()),
        "true_high_rate": safe_float(np.mean(labels == 1)),
        "pred_high_rate": safe_float(np.mean(pred == 1)),
    }


def load_idare(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)
    needed = ["subject_id", "stimulus_id", "valence_score", "arousal_score"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise KeyError(f"I-DARE trial index missing columns: {missing}")

    out = df[needed].copy()
    out["dataset"] = "I-DARE"
    out["subject_id"] = out["subject_id"].astype(int)
    out["stimulus_id"] = out["stimulus_id"].astype(str)
    out = out.drop_duplicates(["subject_id", "stimulus_id"]).reset_index(drop=True)
    return out[["dataset", "subject_id", "stimulus_id", "valence_score", "arousal_score"]]


def load_deap(deap_dir: Path) -> pd.DataFrame:
    if not deap_dir.exists():
        raise FileNotFoundError(deap_dir)

    files = sorted(deap_dir.glob("s*.dat"))
    if not files:
        raise FileNotFoundError(f"No DEAP s*.dat files found in {deap_dir}")

    rows = []
    for sid, path in enumerate(files, start=1):
        with path.open("rb") as f:
            obj = pickle.load(f, encoding="latin1")
        labels = np.asarray(obj["labels"], dtype=float)
        if labels.ndim != 2 or labels.shape[1] < 2:
            raise ValueError(f"Unexpected labels shape for {path}: {labels.shape}")

        for trial_i in range(labels.shape[0]):
            rows.append({
                "dataset": "DEAP",
                "subject_id": int(sid),
                "stimulus_id": str(trial_i + 1),
                "valence_score": float(labels[trial_i, 0]),
                "arousal_score": float(labels[trial_i, 1]),
            })

    return pd.DataFrame(rows)


def check_grid(df: pd.DataFrame, dataset: str):
    n_subjects = int(df["subject_id"].nunique())
    n_stimuli = int(df["stimulus_id"].nunique())
    expected = n_subjects * n_stimuli
    duplicated = int(df.duplicated(["subject_id", "stimulus_id"]).sum())

    if duplicated:
        raise ValueError(f"{dataset}: duplicated subject/stimulus cells={duplicated}")

    if len(df) != expected:
        print(
            f"[WARN] {dataset}: incomplete grid rows={len(df)} "
            f"subjects*stimuli={expected}. Results still computed, but inspect carefully."
        )


def marginal_loo_mean(df: pd.DataFrame, y_col: str, key_col: str) -> np.ndarray:
    y = df[y_col].to_numpy(dtype=float)
    sums = df.groupby(key_col)[y_col].transform("sum").to_numpy(dtype=float)
    counts = df.groupby(key_col)[y_col].transform("count").to_numpy(dtype=float)
    denom = counts - 1.0
    pred = np.full(len(df), np.nan, dtype=float)
    m = denom > 0
    pred[m] = (sums[m] - y[m]) / denom[m]
    return pred


def additive_design(df: pd.DataFrame) -> np.ndarray:
    subjects = sorted(df["subject_id"].astype(int).unique().tolist())
    stimuli = sorted(df["stimulus_id"].astype(str).unique().tolist())

    subj_code = pd.Categorical(df["subject_id"].astype(int), categories=subjects).codes
    stim_code = pd.Categorical(df["stimulus_id"].astype(str), categories=stimuli).codes

    n = len(df)
    p = 1 + max(0, len(subjects) - 1) + max(0, len(stimuli) - 1)
    x = np.zeros((n, p), dtype=float)
    x[:, 0] = 1.0

    for i, c in enumerate(subj_code):
        if c > 0:
            x[i, c] = 1.0

    stim_offset = 1 + max(0, len(subjects) - 1)
    for i, c in enumerate(stim_code):
        if c > 0:
            x[i, stim_offset + c - 1] = 1.0

    return x


def ols_leave_one_out_prediction(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    xtx_inv = np.linalg.pinv(x.T @ x)
    beta = xtx_inv @ (x.T @ y)
    fitted = x @ beta
    h = np.einsum("ij,jk,ik->i", x, xtx_inv, x)
    denom = 1.0 - h
    denom = np.where(np.abs(denom) < EPS, np.nan, denom)
    return (fitted - h * y) / denom


def additive_loo_score(df: pd.DataFrame, y_col: str) -> np.ndarray:
    x = additive_design(df)
    y = df[y_col].to_numpy(dtype=float)
    return ols_leave_one_out_prediction(x, y)


def class_marginal_loo_prob(df: pd.DataFrame, y_col: str, policy: str, key_col: str) -> np.ndarray:
    labels = label_array(df[y_col].to_numpy(dtype=float), policy)
    tmp = df[[key_col]].copy()
    tmp["_valid"] = np.isfinite(labels).astype(float)
    tmp["_label"] = np.nan_to_num(labels, nan=0.0)

    sums = tmp.groupby(key_col)["_label"].transform("sum").to_numpy(dtype=float)
    counts = tmp.groupby(key_col)["_valid"].transform("sum").to_numpy(dtype=float)

    valid = np.isfinite(labels)
    denom = counts - valid.astype(float)
    numer = sums - np.nan_to_num(labels, nan=0.0)

    p = np.full(len(df), np.nan, dtype=float)
    m = denom > 0
    p[m] = numer[m] / denom[m]
    return p


def class_additive_loo_prob(df: pd.DataFrame, y_col: str, policy: str) -> np.ndarray:
    labels = label_array(df[y_col].to_numpy(dtype=float), policy)
    valid = np.isfinite(labels)

    out = np.full(len(df), np.nan, dtype=float)
    if valid.sum() < 4:
        return out

    dsub = df.loc[valid].reset_index(drop=True)
    x = additive_design(dsub)
    y = labels[valid].astype(float)
    pred = ols_leave_one_out_prediction(x, y)
    pred = np.clip(pred, 0.0, 1.0)

    out[np.where(valid)[0]] = pred
    return out


def run_dataset(df: pd.DataFrame, dataset: str):
    check_grid(df, dataset)

    main_rows = []
    binary_rows = []
    pred_rows = []

    n_subjects = int(df["subject_id"].nunique())
    n_stimuli = int(df["stimulus_id"].nunique())

    print(f"[DATASET] {dataset}: rows={len(df)} subjects={n_subjects} stimuli={n_stimuli}")

    for target, y_col in TARGETS.items():
        print(f"  [TARGET] {target}")

        y = df[y_col].to_numpy(dtype=float)

        score_protocols = [
            (
                "leave_one_subject_out",
                "stimulus_only",
                marginal_loo_mean(df, y_col, "stimulus_id"),
                "For each held-out subject, predict each stimulus by train-subject mean of the same stimulus.",
            ),
            (
                "leave_one_stimulus_out",
                "subject_only",
                marginal_loo_mean(df, y_col, "subject_id"),
                "For each held-out stimulus, predict each subject by train-stimulus mean of the same subject.",
            ),
            (
                "leave_one_subject_stimulus_pair_out",
                "subject_stimulus_additive_loo_cell",
                additive_loo_score(df, y_col),
                "Exact leave-one-cell-out additive subject+stimulus prior using OLS LOO hat formula.",
            ),
        ]

        for protocol, model, pred, desc in score_protocols:
            row = {
                "dataset": dataset,
                "target": target,
                "protocol": protocol,
                "model": model,
                "description": desc,
            }
            row.update(continuous_metrics(y, pred))
            main_rows.append(row)

            p_df = df[["subject_id", "stimulus_id"]].copy()
            p_df.insert(0, "dataset", dataset)
            p_df["target"] = target
            p_df["protocol"] = protocol
            p_df["model"] = model
            p_df["y_true_score"] = y
            p_df["y_pred_score"] = pred
            pred_rows.extend(p_df.to_dict(orient="records"))

            for policy in LABEL_POLICIES:
                brow = {
                    "dataset": dataset,
                    "target": target,
                    "protocol": protocol,
                    "model": model,
                    "label_policy": policy,
                    "binary_source": "score_threshold",
                }
                brow.update(binary_metrics_from_score(y, pred, policy))
                binary_rows.append(brow)

        prob_protocols_by_policy = {}
        for policy in LABEL_POLICIES:
            prob_protocols_by_policy[policy] = [
                (
                    "leave_one_subject_out",
                    "stimulus_only",
                    class_marginal_loo_prob(df, y_col, policy, "stimulus_id"),
                ),
                (
                    "leave_one_stimulus_out",
                    "subject_only",
                    class_marginal_loo_prob(df, y_col, policy, "subject_id"),
                ),
                (
                    "leave_one_subject_stimulus_pair_out",
                    "subject_stimulus_additive_loo_cell",
                    class_additive_loo_prob(df, y_col, policy),
                ),
            ]

        for policy, prob_protocols in prob_protocols_by_policy.items():
            for protocol, model, p_high in prob_protocols:
                brow = {
                    "dataset": dataset,
                    "target": target,
                    "protocol": protocol,
                    "model": model,
                    "label_policy": policy,
                    "binary_source": "class_prior_probability",
                }
                brow.update(binary_metrics_from_probability(y, p_high, policy))
                binary_rows.append(brow)

    return main_rows, binary_rows, pred_rows


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    if df.empty:
        return "_No rows._\n"
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in df.iterrows():
        vals = []
        for col in cols:
            val = row.get(col, "")
            if isinstance(val, float):
                vals.append(f"{val:.6f}" if math.isfinite(val) else "")
            elif pd.isna(val):
                vals.append("")
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines) + "\n"


def maybe_sanity_checks(main: pd.DataFrame):
    checks = []

    def pick(dataset, target, protocol, model, metric):
        g = main[
            main["dataset"].eq(dataset)
            & main["target"].eq(target)
            & main["protocol"].eq(protocol)
            & main["model"].eq(model)
        ]
        if g.empty:
            return None
        return safe_float(g.iloc[0][metric])

    checks.append({
        "name": "I-DARE LOSO stimulus-only valence RMSE should match previous variance decomposition",
        "value": pick("I-DARE", "valence", "leave_one_subject_out", "stimulus_only", "rmse"),
        "expected_near": 1.257773694673858,
    })
    checks.append({
        "name": "I-DARE LOSO stimulus-only arousal RMSE should match previous variance decomposition",
        "value": pick("I-DARE", "arousal", "leave_one_subject_out", "stimulus_only", "rmse"),
        "expected_near": 1.9442049821165959,
    })
    checks.append({
        "name": "DEAP LOSO stimulus-only valence RMSE should match previous DEAP stimulus-only run",
        "value": pick("DEAP", "valence", "leave_one_subject_out", "stimulus_only", "rmse"),
        "expected_near": 1.5637460592350514,
    })
    checks.append({
        "name": "DEAP LOSO stimulus-only arousal RMSE should match previous DEAP stimulus-only run",
        "value": pick("DEAP", "arousal", "leave_one_subject_out", "stimulus_only", "rmse"),
        "expected_near": 1.9038635597684934,
    })

    for c in checks:
        v = c["value"]
        e = c["expected_near"]
        c["abs_diff"] = None if v is None else abs(v - e)
        c["pass_1e_minus_6"] = bool(c["abs_diff"] is not None and c["abs_diff"] < 1e-6)

    return checks


def main():
    args = parse_args()
    ROCA_DIR.mkdir(parents=True, exist_ok=True)

    all_main = []
    all_binary = []
    all_pred = []
    datasets = {}

    if args.dataset in {"deap", "both"}:
        datasets["DEAP"] = load_deap(args.deap_dir)

    if args.dataset in {"idare", "both"}:
        datasets["I-DARE"] = load_idare(args.idare_trial_index)

    for dataset, df in datasets.items():
        m, b, p = run_dataset(df, dataset)
        all_main.extend(m)
        all_binary.extend(b)
        all_pred.extend(p)

    main_df = pd.DataFrame(all_main)
    binary_df = pd.DataFrame(all_binary)
    pred_df = pd.DataFrame(all_pred)

    main_df = main_df.sort_values(["dataset", "target", "protocol", "model"]).reset_index(drop=True)
    binary_df = binary_df.sort_values(
        ["dataset", "target", "protocol", "model", "label_policy", "binary_source"]
    ).reset_index(drop=True)

    out_main = ROCA_DIR / f"{args.out_prefix}_main_metrics.csv"
    out_binary = ROCA_DIR / f"{args.out_prefix}_binary_metrics.csv"
    out_pred = ROCA_DIR / f"{args.out_prefix}_predictions.csv"
    out_json = ROCA_DIR / f"{args.out_prefix}.json"
    out_md = ROCA_DIR / f"{args.out_prefix}.md"

    main_df.to_csv(out_main, index=False)
    binary_df.to_csv(out_binary, index=False)
    pred_df.to_csv(out_pred, index=False)

    sanity = maybe_sanity_checks(main_df)

    summary = {
        "protocol_definitions": {
            "leave_one_subject_out": {
                "baseline": "stimulus_only",
                "definition": "For test cell (subject=s, stimulus=v), train excludes subject s; prediction is mean label of stimulus v over all other subjects.",
            },
            "leave_one_stimulus_out": {
                "baseline": "subject_only",
                "definition": "For test cell (subject=s, stimulus=v), train excludes stimulus v; prediction is mean label of subject s over all other stimuli.",
            },
            "leave_one_subject_stimulus_pair_out": {
                "baseline": "subject_stimulus_additive_loo_cell",
                "definition": "For test cell (s,v), only that cell is held out. Prediction is exact OLS leave-one-out additive prior with subject and stimulus main effects.",
                "warning": "If strict unseen-subject plus unseen-stimulus is intended, no non-global subject/stimulus prior exists.",
            },
        },
        "binary_sources": {
            "score_threshold": "Threshold the continuous prior score at 5 according to label policy.",
            "class_prior_probability": "Compute train-only P(high) under the same protocol and threshold probability at 0.5.",
        },
        "outputs": {
            "main_metrics": str(out_main),
            "binary_metrics": str(out_binary),
            "predictions": str(out_pred),
            "json": str(out_json),
            "md": str(out_md),
        },
        "sanity_checks": sanity,
        "main_metrics": main_df.to_dict(orient="records"),
        "binary_metrics": binary_df.to_dict(orient="records"),
    }

    out_json.write_text(json.dumps(clean_json(summary), indent=2, ensure_ascii=False), encoding="utf-8")

    main_cols = [
        "dataset", "target", "protocol", "model", "n",
        "mae", "rmse", "pearson", "spearman", "ccc",
        "y_true_std", "y_pred_std", "residual_std", "rmse_over_y_std",
    ]
    bin_cols = [
        "dataset", "target", "protocol", "model", "label_policy", "binary_source",
        "binary_n", "accuracy", "balanced_accuracy", "macro_f1", "auroc",
        "n_low", "n_high", "true_high_rate", "pred_high_rate",
    ]

    lines = []
    lines.append("# Prior baselines without global baseline\n")
    lines.append("This report computes non-global prior baselines for DEAP and I-DARE.\n")
    lines.append("## Protocols\n")
    lines.append("- `leave_one_subject_out`: stimulus-only prior, train excludes the test subject.")
    lines.append("- `leave_one_stimulus_out`: subject-only prior, train excludes the test stimulus.")
    lines.append("- `leave_one_subject_stimulus_pair_out`: exact leave-one-cell-out additive subject+stimulus prior.")
    lines.append("")
    lines.append("Important: strict unseen-subject plus unseen-stimulus has no legal non-global subject/stimulus prior; it collapses to global, which is intentionally excluded here.\n")
    lines.append("## Continuous score metrics\n")
    lines.append(md_table(main_df, main_cols))
    lines.append("\n## Binary metrics\n")
    lines.append(md_table(binary_df, bin_cols))
    lines.append("\n## Sanity checks\n")
    lines.append(md_table(pd.DataFrame(sanity), ["name", "value", "expected_near", "abs_diff", "pass_1e_minus_6"]))

    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("\nPrior baselines without global completed.")
    print("wrote:", out_md)
    print("wrote:", out_json)
    print("wrote:", out_main)
    print("wrote:", out_binary)
    print("wrote:", out_pred)

    print("\nContinuous metrics:")
    print(main_df[main_cols].to_string(index=False))

    print("\nSanity checks:")
    print(pd.DataFrame(sanity).to_string(index=False))


if __name__ == "__main__":
    main()
