#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesRegressor


ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / ".cache"
ROCA_DIR = ROOT / "docs" / "roca"

FEATURE_NPY = CACHE_DIR / "roca_idare_emg_expanded_features.npy"
FEATURE_INDEX = CACHE_DIR / "roca_idare_emg_expanded_feature_index.csv"
FEATURE_COLUMNS = CACHE_DIR / "roca_idare_emg_expanded_feature_columns.json"

STIM_BASELINE_PRED = ROCA_DIR / "stimulus_only_predictions_current.csv"
FOLD_SAFE_SELECTED = ROCA_DIR / "fold_safe_selected_stimuli_current.csv"

OUT_MD = ROCA_DIR / "emg_expanded_probe_current.md"
OUT_JSON = ROCA_DIR / "emg_expanded_probe_current.json"
OUT_PRED_CSV = ROCA_DIR / "emg_expanded_probe_predictions_current.csv"
OUT_MAIN_CSV = ROCA_DIR / "emg_expanded_probe_main_metrics_current.csv"
OUT_SUBSET_CSV = ROCA_DIR / "emg_expanded_probe_subset_metrics_current.csv"
OUT_PER_SUBJECT_CSV = ROCA_DIR / "emg_expanded_probe_per_subject_metrics_current.csv"

TARGETS = {
    "valence": "valence_score",
    "arousal": "arousal_score",
}

MODELS = [
    "stimulus_only",
    "emg_expanded_ridge_direct",
    "emg_expanded_ridge_residual",
    "emg_expanded_extratrees_direct",
    "emg_expanded_extratrees_residual",
]

RIDGE_ALPHA = 100.0
EPS = 1e-8

ET_PARAMS = {
    "n_estimators": 300,
    "max_depth": 6,
    "min_samples_leaf": 8,
    "max_features": 0.5,
    "random_state": 11,
    "n_jobs": -1,
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
    rank_sum_pos = float(ranks[y_bin == 1].sum())
    return float((rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def prediction_metrics(df):
    y = df["y_true_score"].to_numpy(dtype=float)
    pred = df["y_pred_score_clipped"].to_numpy(dtype=float)

    err = pred - y
    y_bin = (y > 5).astype(int)
    y_hat = (pred > 5).astype(int)

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
        "ccc": ccc(y, pred),
        "balanced_accuracy": safe_float(np.mean(recalls)),
        "macro_f1": safe_float(np.mean(f1s)),
        "auroc": auroc(y_bin, pred),
    }


def deviation_metrics(df):
    true_dev = df["true_deviation_from_train_stimulus_mean"].to_numpy(dtype=float)
    pred_dev = df["y_pred_deviation_clipped"].to_numpy(dtype=float)

    err = pred_dev - true_dev
    sign_true = np.sign(true_dev)
    sign_pred = np.sign(pred_dev)
    nz = sign_true != 0

    return {
        "dev_rmse": safe_float(np.sqrt(np.mean(err * err))),
        "dev_mae": safe_float(np.mean(np.abs(err))),
        "dev_pearson": pearson(true_dev, pred_dev),
        "dev_spearman": spearman(true_dev, pred_dev),
        "dev_sign_acc": safe_float(np.mean(sign_true[nz] == sign_pred[nz])) if nz.sum() else None,
        "pred_dev_std": safe_float(np.std(pred_dev)),
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


def fit_preprocessor(x_train):
    x_train = np.asarray(x_train, dtype=float)
    x_train = np.nan_to_num(x_train, nan=0.0, posinf=0.0, neginf=0.0)

    lo = np.quantile(x_train, 0.01, axis=0)
    hi = np.quantile(x_train, 0.99, axis=0)

    lo = np.nan_to_num(lo, nan=0.0, posinf=0.0, neginf=0.0)
    hi = np.nan_to_num(hi, nan=0.0, posinf=0.0, neginf=0.0)

    bad = hi <= lo
    hi[bad] = lo[bad] + 1.0

    x_clip = np.clip(x_train, lo, hi)
    mean = x_clip.mean(axis=0)
    std = x_clip.std(axis=0)

    keep = np.isfinite(mean) & np.isfinite(std) & (std > EPS)

    if int(keep.sum()) == 0:
        raise ValueError("No usable features after train-only preprocessing.")

    mean = mean[keep]
    std = std[keep]
    lo = lo[keep]
    hi = hi[keep]

    return {
        "lo": lo,
        "hi": hi,
        "mean": mean,
        "std": std,
        "keep": keep,
        "n_features_kept": int(keep.sum()),
    }


def apply_preprocessor(x, prep):
    x = np.asarray(x, dtype=float)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    x = x[:, prep["keep"]]
    x_clip = np.clip(x, prep["lo"], prep["hi"])
    x_scaled = (x_clip - prep["mean"]) / prep["std"]
    x_scaled = np.nan_to_num(x_scaled, nan=0.0, posinf=0.0, neginf=0.0)
    return x_clip, x_scaled


def fit_ridge(x_train, y_train, alpha=RIDGE_ALPHA):
    x = np.asarray(x_train, dtype=float)
    y = np.asarray(y_train, dtype=float)

    if x.ndim != 2:
        raise ValueError(f"Expected 2D x_train, got shape={x.shape}")
    if len(x) == 0:
        raise ValueError("Cannot fit ridge with zero rows.")
    if len(y) != len(x):
        raise ValueError(f"x/y length mismatch: x={len(x)}, y={len(y)}")

    x_aug = np.concatenate([np.ones((x.shape[0], 1)), x], axis=1)

    reg = np.eye(x_aug.shape[1]) * float(alpha)
    reg[0, 0] = 0.0

    lhs = x_aug.T @ x_aug + reg
    rhs = x_aug.T @ y

    try:
        beta = np.linalg.solve(lhs, rhs)
    except np.linalg.LinAlgError:
        beta = np.linalg.pinv(lhs) @ rhs

    return beta


def predict_ridge(x, beta):
    x = np.asarray(x, dtype=float)
    x_aug = np.concatenate([np.ones((x.shape[0], 1)), x], axis=1)
    return x_aug @ beta


def make_extratrees(seed_offset=0):
    params = dict(ET_PARAMS)
    params["random_state"] = int(params["random_state"]) + int(seed_offset)
    return ExtraTreesRegressor(**params)


def train_deviation_target(train_df, score_col):
    means = []
    for _, row in train_df.iterrows():
        stim = row["stimulus_id"]
        sid = int(row["subject_id"])
        other = train_df[
            (train_df["stimulus_id"] == stim)
            & (train_df["subject_id"] != sid)
        ][score_col]
        means.append(float(other.mean()) if len(other) else np.nan)

    means = np.asarray(means, dtype=float)
    y = train_df[score_col].to_numpy(dtype=float)
    return y - means


def load_inputs():
    missing = []
    for path in [FEATURE_NPY, FEATURE_INDEX, FEATURE_COLUMNS, STIM_BASELINE_PRED, FOLD_SAFE_SELECTED]:
        if not path.exists():
            missing.append(str(path))
    if missing:
        raise FileNotFoundError("Missing required files:\n" + "\n".join(missing))

    x = np.load(FEATURE_NPY)
    idx = pd.read_csv(FEATURE_INDEX)
    feature_columns = json.loads(FEATURE_COLUMNS.read_text(encoding="utf-8"))
    stim = pd.read_csv(STIM_BASELINE_PRED)
    selected = pd.read_csv(FOLD_SAFE_SELECTED)

    idx = idx.copy()
    idx["cache_row"] = idx["cache_row"].astype(int)
    idx["subject_id"] = idx["subject_id"].astype(int)
    idx["stimulus_id"] = idx["stimulus_id"].astype(str)

    for col in TARGETS.values():
        idx[col] = pd.to_numeric(idx[col], errors="coerce")

    idx = idx.sort_values("cache_row").reset_index(drop=True)

    if x.shape[0] != len(idx):
        raise ValueError(f"Feature/index mismatch: x={x.shape}, idx={len(idx)}")

    if x.shape[1] != len(feature_columns):
        raise ValueError(f"Feature column mismatch: x_dim={x.shape[1]}, columns={len(feature_columns)}")

    if not np.array_equal(idx["cache_row"].to_numpy(), np.arange(len(idx))):
        raise ValueError("cache_row is not contiguous 0..n-1.")

    x = np.asarray(x[idx["cache_row"].to_numpy()], dtype=float)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)

    stim = stim[stim["model"] == "stimulus_only"].copy()
    stim["test_subject"] = stim["test_subject"].astype(int)
    stim["stimulus_id"] = stim["stimulus_id"].astype(str)

    selected = selected.copy()
    selected["test_subject"] = selected["test_subject"].astype(int)
    selected["stimulus_id"] = selected["stimulus_id"].astype(str)

    return x, idx, feature_columns, stim, selected


def run_loso(x, idx, stim_pred):
    subjects = sorted(idx["subject_id"].unique().tolist())
    rows = []
    preprocessing_rows = []

    for target, score_col in TARGETS.items():
        for test_subject in subjects:
            train_mask = idx["subject_id"].to_numpy() != test_subject
            test_mask = idx["subject_id"].to_numpy() == test_subject

            train_df = idx.loc[train_mask].copy()
            test_df = idx.loc[test_mask].copy()

            x_train_raw = x[train_mask]
            x_test_raw = x[test_mask]

            prep = fit_preprocessor(x_train_raw)
            x_train_tree, x_train_scaled = apply_preprocessor(x_train_raw, prep)
            x_test_tree, x_test_scaled = apply_preprocessor(x_test_raw, prep)

            preprocessing_rows.append({
                "target": target,
                "test_subject": int(test_subject),
                "n_features_input": int(x.shape[1]),
                "n_features_kept": int(prep["n_features_kept"]),
            })

            y_train_score = train_df[score_col].to_numpy(dtype=float)
            y_train_dev = train_deviation_target(train_df, score_col)
            valid_dev = np.isfinite(y_train_dev)

            # Ridge direct
            beta_direct = fit_ridge(x_train_scaled, y_train_score, alpha=RIDGE_ALPHA)
            pred_ridge_direct = predict_ridge(x_test_scaled, beta_direct)

            # Ridge residual
            beta_resid = fit_ridge(x_train_scaled[valid_dev], y_train_dev[valid_dev], alpha=RIDGE_ALPHA)
            pred_ridge_dev = predict_ridge(x_test_scaled, beta_resid)

            # ExtraTrees direct
            et_direct = make_extratrees(seed_offset=0)
            et_direct.fit(x_train_tree, y_train_score)
            pred_et_direct = et_direct.predict(x_test_tree)

            # ExtraTrees residual
            et_resid = make_extratrees(seed_offset=1000)
            et_resid.fit(x_train_tree[valid_dev], y_train_dev[valid_dev])
            pred_et_dev = et_resid.predict(x_test_tree)

            stim_mean = train_df.groupby("stimulus_id")[score_col].mean()
            test_stim_mean = test_df["stimulus_id"].map(stim_mean).astype(float).to_numpy()
            true_score = test_df[score_col].to_numpy(dtype=float)
            true_dev = true_score - test_stim_mean

            common = test_df[["subject_id", "stimulus_id"]].copy()
            common = common.rename(columns={"subject_id": "test_subject"})
            common["target"] = target
            common["y_true_score"] = true_score
            common["train_stimulus_mean"] = test_stim_mean
            common["true_deviation_from_train_stimulus_mean"] = true_dev

            model_specs = [
                ("emg_expanded_ridge_direct", pred_ridge_direct, None),
                ("emg_expanded_ridge_residual", test_stim_mean + pred_ridge_dev, pred_ridge_dev),
                ("emg_expanded_extratrees_direct", pred_et_direct, None),
                ("emg_expanded_extratrees_residual", test_stim_mean + pred_et_dev, pred_et_dev),
            ]

            for model_name, pred_score_raw, pred_dev_raw in model_specs:
                r = common.copy()
                r["model"] = model_name
                r["y_pred_score_raw"] = pred_score_raw
                r["y_pred_score_clipped"] = np.clip(pred_score_raw, 1.0, 9.0)
                r["y_pred_deviation_clipped"] = r["y_pred_score_clipped"] - r["train_stimulus_mean"]
                if pred_dev_raw is None:
                    r["y_pred_deviation_raw"] = pred_score_raw - test_stim_mean
                else:
                    r["y_pred_deviation_raw"] = pred_dev_raw
                rows.append(r)

    emg = pd.concat(rows, ignore_index=True)
    prep_df = pd.DataFrame(preprocessing_rows)

    stim_rows = []
    for _, row in stim_pred.iterrows():
        pred_score = float(row["y_pred_score"])
        stim_rows.append({
            "test_subject": int(row["test_subject"]),
            "stimulus_id": str(row["stimulus_id"]),
            "target": row["target"],
            "y_true_score": float(row["y_true_score"]),
            "train_stimulus_mean": pred_score,
            "true_deviation_from_train_stimulus_mean": float(row["true_deviation_from_train_stimulus_mean"]),
            "model": "stimulus_only",
            "y_pred_score_raw": pred_score,
            "y_pred_score_clipped": np.clip(pred_score, 1.0, 9.0),
            "y_pred_deviation_clipped": 0.0,
            "y_pred_deviation_raw": 0.0,
        })

    return pd.concat([pd.DataFrame(stim_rows), emg], ignore_index=True), prep_df


def add_subset_flags(pred, selected):
    out = pred.copy()
    for subset in sorted(selected["subset"].unique()):
        key = selected[selected["subset"] == subset][
            ["target", "test_subject", "stimulus_id"]
        ].copy()
        key["selected"] = True
        merged = out.merge(
            key,
            on=["target", "test_subject", "stimulus_id"],
            how="left",
        )
        out[f"is_{subset}"] = merged["selected"].fillna(False).astype(bool).to_numpy()
    return out


def aggregate_main(pred):
    rows = []
    for target in TARGETS:
        for model in MODELS:
            sub = pred[(pred["target"] == target) & (pred["model"] == model)]
            row = {"target": target, "model": model}
            row.update(prediction_metrics(sub))
            row.update(deviation_metrics(sub))
            rows.append(row)
    return pd.DataFrame(rows)


def aggregate_per_subject(pred):
    rows = []
    for target in TARGETS:
        for model in MODELS:
            sub = pred[(pred["target"] == target) & (pred["model"] == model)]
            for sid, g in sub.groupby("test_subject"):
                row = {"target": target, "model": model, "test_subject": int(sid)}
                row.update(prediction_metrics(g))
                row.update(deviation_metrics(g))
                rows.append(row)
    return pd.DataFrame(rows)


def aggregate_subsets(pred):
    subset_cols = [c for c in pred.columns if c.startswith("is_top25_train_")]
    rows = []
    for target in TARGETS:
        for subset_col in subset_cols:
            subset_name = subset_col.replace("is_", "")
            for model in MODELS:
                sub = pred[
                    (pred["target"] == target)
                    & (pred["model"] == model)
                    & (pred[subset_col])
                ]
                row = {"target": target, "subset": subset_name, "model": model}
                row.update(prediction_metrics(sub))
                row.update(deviation_metrics(sub))
                rows.append(row)
    return pd.DataFrame(rows)


def add_lifts(df, group_cols):
    rows = []
    lower_is_better = {"mae", "rmse", "dev_mae", "dev_rmse"}
    metrics = [
        "mae", "rmse", "pearson", "spearman", "ccc",
        "balanced_accuracy", "macro_f1", "auroc",
        "dev_mae", "dev_rmse", "dev_pearson", "dev_spearman", "dev_sign_acc",
        "pred_dev_std",
    ]

    for _, g in df.groupby(group_cols, dropna=False):
        base = g[g["model"] == "stimulus_only"]
        if base.empty:
            continue
        base = base.iloc[0]

        for _, row in g.iterrows():
            out = row.to_dict()
            for m in metrics:
                rv = row.get(m, np.nan)
                bv = base.get(m, np.nan)
                if pd.isna(rv) or pd.isna(bv):
                    out[f"lift_vs_stimulus_{m}"] = None
                elif m in lower_is_better:
                    out[f"lift_vs_stimulus_{m}"] = safe_float(float(bv) - float(rv))
                else:
                    out[f"lift_vs_stimulus_{m}"] = safe_float(float(rv) - float(bv))
            rows.append(out)

    return pd.DataFrame(rows)


def write_outputs(pred, main_df, subset_df, per_subject_df, prep_df, feature_dim):
    main_lift = add_lifts(main_df, ["target"])
    subset_lift = add_lifts(subset_df, ["target", "subset"])

    pred.to_csv(OUT_PRED_CSV, index=False)
    main_lift.to_csv(OUT_MAIN_CSV, index=False)
    subset_lift.to_csv(OUT_SUBSET_CSV, index=False)
    per_subject_df.to_csv(OUT_PER_SUBJECT_CSV, index=False)

    summary = {
        "protocol": "strict LOSO expanded EMG probe",
        "feature_cache": {
            "feature_npy": str(FEATURE_NPY),
            "feature_index": str(FEATURE_INDEX),
            "feature_columns": str(FEATURE_COLUMNS),
            "feature_dim": int(feature_dim),
        },
        "ridge_alpha": RIDGE_ALPHA,
        "extratrees_params": ET_PARAMS,
        "preprocessing": {
            "fit_scope": "train subjects only inside each LOSO fold",
            "quantile_clip": [0.01, 0.99],
            "standardization": "train mean/std for Ridge only",
            "feature_filter": "drop near-constant train-only features",
            "mean_features_kept": safe_float(prep_df["n_features_kept"].mean()),
            "min_features_kept": int(prep_df["n_features_kept"].min()),
            "max_features_kept": int(prep_df["n_features_kept"].max()),
        },
        "important_notes": [
            "No test subject is used for preprocessing, fitting, or subset selection.",
            "No hyperparameter tuning is performed in this probe.",
            "Hard subsets come from fold-safe Step 03.",
            "Predictions are clipped to SAM range [1, 9].",
            "Residual models are the ROCA-relevant models.",
        ],
        "main_metrics": main_lift.to_dict(orient="records"),
        "subset_metrics": subset_lift.to_dict(orient="records"),
    }

    OUT_JSON.write_text(json.dumps(clean_json(summary), indent=2, ensure_ascii=False), encoding="utf-8")

    main_cols = [
        "target", "model", "n",
        "mae", "rmse", "pearson", "balanced_accuracy", "auroc",
        "dev_rmse", "dev_pearson", "dev_sign_acc", "pred_dev_std",
        "lift_vs_stimulus_rmse",
        "lift_vs_stimulus_balanced_accuracy",
        "lift_vs_stimulus_auroc",
        "lift_vs_stimulus_dev_rmse",
        "lift_vs_stimulus_dev_pearson",
    ]

    subset_cols = [
        "target", "subset", "model", "n",
        "rmse", "balanced_accuracy", "auroc",
        "dev_rmse", "dev_pearson", "dev_sign_acc", "pred_dev_std",
        "lift_vs_stimulus_rmse",
        "lift_vs_stimulus_balanced_accuracy",
        "lift_vs_stimulus_auroc",
        "lift_vs_stimulus_dev_rmse",
        "lift_vs_stimulus_dev_pearson",
    ]

    lines = []
    lines.append("# ROCA-I-DARE Expanded EMG Probe\n")
    lines.append("Strict LOSO. Expanded EMG features. Fixed hyperparameters. No test tuning.\n")

    lines.append("## Configuration\n")
    lines.append(f"- feature_dim: `{feature_dim}`")
    lines.append(f"- ridge_alpha: `{RIDGE_ALPHA}`")
    lines.append(f"- ExtraTrees: `{json.dumps(ET_PARAMS)}`")
    lines.append(f"- mean_features_kept_per_fold: `{prep_df['n_features_kept'].mean():.2f}`")
    lines.append("")

    lines.append("## Main metrics\n")
    lines.append(md_table(main_lift.to_dict(orient="records"), main_cols))

    lines.append("\n## Fold-safe hard subset metrics\n")
    lines.append(md_table(subset_lift.to_dict(orient="records"), subset_cols))

    lines.append("\n## Interpretation guide\n")
    lines.append(
        "- Positive `lift_vs_stimulus_rmse` means lower RMSE than stimulus-only.\n"
        "- Positive `lift_vs_stimulus_auroc` means better high/low ranking than stimulus-only.\n"
        "- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.\n"
        "- Residual models are more important than direct models for ROCA.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    return main_lift, subset_lift


def main():
    x, idx, feature_columns, stim, selected = load_inputs()

    print("Running strict LOSO expanded EMG probe...")
    print(f"features shape: {x.shape}")
    print(f"feature columns: {len(feature_columns)}")
    print(f"subjects: {idx['subject_id'].nunique()}")
    print(f"stimuli: {idx['stimulus_id'].nunique()}")
    print(f"Ridge alpha: {RIDGE_ALPHA}")
    print(f"ExtraTrees params: {ET_PARAMS}")

    pred, prep_df = run_loso(x, idx, stim)
    pred = add_subset_flags(pred, selected)

    main_df = aggregate_main(pred)
    subset_df = aggregate_subsets(pred)
    per_subject_df = aggregate_per_subject(pred)

    main_lift, subset_lift = write_outputs(
        pred,
        main_df,
        subset_df,
        per_subject_df,
        prep_df,
        feature_dim=x.shape[1],
    )

    print()
    print("ROCA step 04e completed.")
    print(f"wrote: {OUT_MD}")
    print(f"wrote: {OUT_JSON}")
    print(f"wrote: {OUT_PRED_CSV}")
    print(f"wrote: {OUT_MAIN_CSV}")
    print(f"wrote: {OUT_SUBSET_CSV}")
    print(f"wrote: {OUT_PER_SUBJECT_CSV}")

    print()
    print("Main expanded EMG metrics:")
    print(main_lift[
        [
            "target", "model", "mae", "rmse", "pearson",
            "balanced_accuracy", "auroc",
            "dev_rmse", "dev_pearson", "pred_dev_std",
            "lift_vs_stimulus_rmse",
            "lift_vs_stimulus_balanced_accuracy",
            "lift_vs_stimulus_auroc",
            "lift_vs_stimulus_dev_rmse",
            "lift_vs_stimulus_dev_pearson",
        ]
    ].to_string(index=False))

    print()
    print("Fold-safe hard subset expanded EMG metrics:")
    print(subset_lift[
        [
            "target", "subset", "model", "rmse",
            "balanced_accuracy", "auroc",
            "dev_rmse", "dev_pearson", "pred_dev_std",
            "lift_vs_stimulus_rmse",
            "lift_vs_stimulus_balanced_accuracy",
            "lift_vs_stimulus_auroc",
            "lift_vs_stimulus_dev_rmse",
            "lift_vs_stimulus_dev_pearson",
        ]
    ].to_string(index=False))


if __name__ == "__main__":
    main()
