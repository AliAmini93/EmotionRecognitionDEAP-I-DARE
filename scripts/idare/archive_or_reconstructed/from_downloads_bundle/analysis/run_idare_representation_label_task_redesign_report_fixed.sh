#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start representation/label-task diagnostic report ====="
date
git status --short --branch
echo

echo "===== 1) choose python and require clean repo ====="
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif [ -x ".venv/bin/python3" ]; then
  PY=".venv/bin/python3"
else
  PY="python3"
fi
echo "PY=$PY"
"$PY" - <<'PY'
import sys
print(sys.executable)
import json
import numpy
import pandas
print("OK_IMPORTS")
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repo is not clean; commit/stash current changes before running this diagnostic."
  git status --short --branch
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required inputs ====="
ls -lh \
  docs/idare_representation_label_task_redesign_objective.md \
  docs/idare_representation_label_task_redesign_objective.json \
  docs/idare_calibration_protocol_review_status.md \
  docs/idare_calibration_protocol_report.md \
  docs/idare_root_cause_diagnostic_report.md \
  docs/idare_diagnostic_sanity_tests_report.md \
  docs/idare_failure_analysis_report.md \
  .cache/idare_eeg_cache_index_baseline_corrected.csv \
  .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy \
  .cache/idare_emg_feature_cache_index.csv \
  .cache/idare_emg_features.npy
echo

echo "===== 3) remove stale partial outputs and generate representation/label-task diagnostic report ====="
rm -f \
  docs/idare_representation_label_task_redesign_report.md \
  docs/idare_representation_label_task_redesign_report.json \
  docs/idare_label_noise_subject_balance_summary.csv \
  docs/idare_representation_signal_diagnostic_summary.csv
"$PY" - <<'PY'
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DOCS = Path("docs")
CACHE = Path(".cache")
NOW = datetime.now(timezone.utc).isoformat()

OUT_MD = DOCS / "idare_representation_label_task_redesign_report.md"
OUT_JSON = DOCS / "idare_representation_label_task_redesign_report.json"
OUT_LABEL_CSV = DOCS / "idare_label_noise_subject_balance_summary.csv"
OUT_REPR_CSV = DOCS / "idare_representation_signal_diagnostic_summary.csv"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

REQUIRED = [
    DOCS / "idare_representation_label_task_redesign_objective.md",
    DOCS / "idare_representation_label_task_redesign_objective.json",
    DOCS / "idare_calibration_protocol_review_status.md",
    DOCS / "idare_calibration_protocol_report.md",
    DOCS / "idare_root_cause_diagnostic_report.md",
    DOCS / "idare_diagnostic_sanity_tests_report.md",
    DOCS / "idare_failure_analysis_report.md",
    CACHE / "idare_eeg_cache_index_baseline_corrected.csv",
    CACHE / "idare_eeg_windows_32x640_float32_baseline_corrected.npy",
    CACHE / "idare_emg_feature_cache_index.csv",
    CACHE / "idare_emg_features.npy",
]
missing = [str(p) for p in REQUIRED if not p.exists()]
if missing:
    raise SystemExit("ERROR: missing required files:\n" + "\n".join(missing))

PRED_SOURCES = [
    (DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv", "EEG", "stim_bsl_only", "broader_eval_primary"),
    (DOCS / "idare_broader_eval_emg_feature_only_primary_predictions.csv", "EMG", "feature_only", "broader_eval_primary"),
    (DOCS / "idare_label_policy_ablation_eeg_primary_predictions.csv", "EEG", "label_policy_ablation", "label_policy_ablation"),
    (DOCS / "idare_label_policy_ablation_emg_primary_predictions.csv", "EMG", "label_policy_ablation", "label_policy_ablation"),
]

TASKS = ["valence", "arousal"]
POLICIES = ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]

def pick_col(cols, candidates):
    lower = {str(c).lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None

def numeric_cols(df):
    out = []
    for c in df.columns:
        try:
            s = pd.to_numeric(df[c], errors="coerce")
            if s.notna().sum() > 0:
                out.append(c)
        except Exception:
            pass
    return out

def find_subject_col(df):
    return pick_col(df.columns, ["subject_id", "subject", "subj", "participant_id", "participant", "s"])

def find_task_rating_col(df, task):
    nums = numeric_cols(df)
    lower = {str(c).lower(): c for c in nums}

    # Prefer raw-like non-binary columns.
    preferred = [
        task,
        f"{task}_rating",
        f"rating_{task}",
        f"{task}_score",
        f"score_{task}",
        f"{task}_raw",
        f"raw_{task}",
        f"deap_{task}",
    ]
    candidates = []
    for name in preferred:
        if name.lower() in lower:
            candidates.append(lower[name.lower()])
    for c in nums:
        cl = str(c).lower()
        if task in cl and any(k in cl for k in ["rating", "score", "raw", "self", "deap"]):
            candidates.append(c)
    for c in nums:
        cl = str(c).lower()
        if task in cl and "pred" not in cl and "prob" not in cl:
            candidates.append(c)

    seen = []
    for c in candidates:
        if c not in seen:
            seen.append(c)

    if not seen:
        return None

    def score_col(c):
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(s) == 0:
            return -999
        unique = sorted(s.unique().tolist())
        mx = float(s.max())
        mn = float(s.min())
        non_binary = not set(unique).issubset({0, 1})
        raw_like = 10 if non_binary and mx > 1.5 else 0
        exact = 5 if str(c).lower() == task else 0
        contains_label_penalty = -3 if "label" in str(c).lower() else 0
        return raw_like + exact + contains_label_penalty + min(len(unique), 20) / 100.0

    return max(seen, key=score_col)

def make_folds(subjects, n_folds=6, seed=11):
    subjects = np.asarray(sorted(set(int(s) for s in subjects)), dtype=int)
    rng = np.random.default_rng(int(seed))
    permuted = rng.permutation(subjects)
    chunks = np.array_split(permuted, int(n_folds))
    mapping = {}
    for i, chunk in enumerate(chunks, start=1):
        for s in chunk.tolist():
            mapping[int(s)] = int(i)
    return mapping

def labels_from_values(values, policy):
    x = pd.to_numeric(pd.Series(values), errors="coerce")
    if x.dropna().empty:
        return pd.Series([pd.NA] * len(x), dtype="Int64"), pd.Series([False] * len(x))
    vals = set(float(v) for v in x.dropna().unique().tolist())
    raw_like = (max(vals) > 1.5) or (min(vals) < 0)
    if raw_like:
        midpoint = np.isclose(x.astype(float), 5.0, atol=1e-8)
        if policy == "discard_midpoint":
            y = pd.Series(np.where(x > 5.0, 1, np.where(x < 5.0, 0, np.nan)), index=x.index)
        elif policy == "midpoint_as_low":
            y = pd.Series(np.where(x > 5.0, 1, 0), index=x.index)
        elif policy == "midpoint_as_high":
            y = pd.Series(np.where(x >= 5.0, 1, 0), index=x.index)
        else:
            raise ValueError(policy)
        return y.astype("Float64").astype("Int64"), pd.Series(midpoint, index=x.index)
    else:
        y = x.round().astype("Float64").astype("Int64")
        return y, pd.Series([False] * len(x), index=x.index)

def prop_or_nan(mask):
    if len(mask) == 0:
        return float("nan")
    return float(np.asarray(mask, dtype=bool).mean())

def eta_squared_factor(X, factor):
    X = np.asarray(X, dtype=np.float64)
    factor = np.asarray(factor)
    ok = pd.notna(factor)
    X = X[ok]
    factor = factor[ok]
    if X.shape[0] < 3 or len(np.unique(factor)) < 2:
        return {"eta_mean": float("nan"), "eta_median": float("nan"), "eta_max": float("nan")}
    mu = X.mean(axis=0)
    total = ((X - mu) ** 2).sum(axis=0)
    between = np.zeros(X.shape[1], dtype=np.float64)
    for g in np.unique(factor):
        mask = factor == g
        if mask.sum() == 0:
            continue
        gm = X[mask].mean(axis=0)
        between += mask.sum() * ((gm - mu) ** 2)
    eta = np.divide(between, total, out=np.zeros_like(between), where=total > 1e-12)
    return {
        "eta_mean": float(np.nanmean(eta)),
        "eta_median": float(np.nanmedian(eta)),
        "eta_max": float(np.nanmax(eta)),
    }

def abs_corr_summary(X, y):
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    ok = np.isfinite(y)
    X = X[ok]
    y = y[ok]
    if X.shape[0] < 3 or len(np.unique(y)) < 2:
        return {"abs_corr_mean": float("nan"), "abs_corr_max": float("nan")}
    Xz = X - X.mean(axis=0)
    yz = y - y.mean()
    denom = np.sqrt((Xz ** 2).sum(axis=0) * (yz ** 2).sum())
    corr = np.divide((Xz * yz[:, None]).sum(axis=0), denom, out=np.zeros(X.shape[1]), where=denom > 1e-12)
    ac = np.abs(corr)
    return {"abs_corr_mean": float(np.nanmean(ac)), "abs_corr_max": float(np.nanmax(ac))}

def centroid_separation(X, y):
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y)
    ok = pd.notna(y)
    X = X[ok]
    y = y[ok]
    vals = np.unique(y)
    if X.shape[0] < 3 or len(vals) != 2:
        return float("nan")
    X0 = X[y == vals[0]]
    X1 = X[y == vals[1]]
    if len(X0) < 2 or len(X1) < 2:
        return float("nan")
    d = float(np.linalg.norm(X1.mean(axis=0) - X0.mean(axis=0)))
    scatter = float((np.mean(np.linalg.norm(X0 - X0.mean(axis=0), axis=1)) + np.mean(np.linalg.norm(X1 - X1.mean(axis=0), axis=1))) / 2.0)
    return float(d / (scatter + 1e-12))

def safe_float(x):
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None

def label_audit_for_index(df, modality):
    subj_col = find_subject_col(df)
    if subj_col is None:
        raise SystemExit(f"ERROR: cannot find subject column for {modality}; columns={list(df.columns)}")
    df = df.copy()
    df["_subject_id"] = pd.to_numeric(df[subj_col], errors="coerce").astype("Int64")
    subjects = sorted(int(s) for s in df["_subject_id"].dropna().unique().tolist())
    fold_map = make_folds(subjects, 6, 11)
    df["_fold_id"] = df["_subject_id"].map(fold_map).astype("Int64")

    rows = []
    discovered = {}
    for task in TASKS:
        col = find_task_rating_col(df, task)
        discovered[task] = col
        if col is None:
            continue
        raw = pd.to_numeric(df[col], errors="coerce")
        raw_like = bool(raw.dropna().max() > 1.5) if raw.dropna().size else False
        near_mid = (raw.astype(float).sub(5.0).abs() <= 0.5) if raw_like else pd.Series([False] * len(raw), index=raw.index)
        if raw_like:
            exact_mid = pd.Series(np.isclose(raw.astype(float), 5.0, atol=1e-8), index=raw.index)
        else:
            exact_mid = pd.Series([False] * len(raw), index=raw.index)

        for subject_id, sg in df.groupby("_subject_id", dropna=True):
            sg_idx = sg.index
            base = {
                "modality": modality,
                "task": task,
                "subject_id": int(subject_id),
                "fold_id": int(sg["_fold_id"].dropna().iloc[0]) if sg["_fold_id"].notna().any() else None,
                "rating_column": str(col),
                "n": int(len(sg)),
                "rating_mean": safe_float(raw.loc[sg_idx].mean()),
                "rating_std": safe_float(raw.loc[sg_idx].std(ddof=0)),
                "rating_min": safe_float(raw.loc[sg_idx].min()),
                "rating_max": safe_float(raw.loc[sg_idx].max()),
                "exact_midpoint_fraction": float(np.asarray(exact_mid.loc[sg_idx], dtype=bool).mean()) if raw_like else 0.0,
                "near_midpoint_fraction": float(np.asarray(near_mid.loc[sg_idx], dtype=bool).mean()) if raw_like else 0.0,
            }
            for policy in POLICIES:
                y, _ = labels_from_values(raw.loc[sg_idx], policy)
                valid = y.dropna()
                base[f"{policy}_n_valid"] = int(len(valid))
                base[f"{policy}_prop_high"] = safe_float(valid.mean()) if len(valid) else None
                base[f"{policy}_n_high"] = int((valid == 1).sum()) if len(valid) else 0
                base[f"{policy}_n_low"] = int((valid == 0).sum()) if len(valid) else 0
            rows.append(base)

    out = pd.DataFrame(rows)
    if not out.empty:
        # Add global prop and skew.
        for policy in POLICIES:
            colp = f"{policy}_prop_high"
            global_by = out.groupby(["modality", "task"])[colp].transform("mean")
            out[f"{policy}_abs_subject_prop_skew"] = (out[colp] - global_by).abs()
    return out, discovered

def load_prediction_subject_errors():
    frames = []
    for path, modality, variant, source_group in PRED_SOURCES:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        cols = list(df.columns)
        subj_col = find_subject_col(df)
        y_col = pick_col(cols, ["y_true", "true_label", "label", "target"])
        pred_col = pick_col(cols, ["y_pred", "pred", "prediction", "pred_label"])
        task_col = pick_col(cols, ["task"])
        recipe_col = pick_col(cols, ["recipe"])
        policy_col = pick_col(cols, ["label_policy", "policy"])
        if subj_col is None or y_col is None or pred_col is None or task_col is None:
            continue
        tmp = pd.DataFrame({
            "source_path": str(path),
            "source_group": source_group,
            "modality": modality,
            "variant": variant,
            "subject_id": pd.to_numeric(df[subj_col], errors="coerce"),
            "task": df[task_col].astype(str),
            "recipe": df[recipe_col].astype(str) if recipe_col else "unknown",
            "label_policy": df[policy_col].astype(str) if policy_col else "unknown",
            "y_true": pd.to_numeric(df[y_col], errors="coerce"),
            "y_pred": pd.to_numeric(df[pred_col], errors="coerce"),
        })
        tmp = tmp.dropna(subset=["subject_id", "y_true", "y_pred"])
        tmp["subject_id"] = tmp["subject_id"].astype(int)
        tmp["correct"] = (tmp["y_true"].astype(int) == tmp["y_pred"].astype(int)).astype(int)
        frames.append(tmp)
    if not frames:
        return pd.DataFrame()
    pred = pd.concat(frames, ignore_index=True)
    rows = []
    for key, g in pred.groupby(["modality", "variant", "task", "label_policy", "subject_id"]):
        rows.append({
            "modality": key[0],
            "variant": key[1],
            "task": key[2],
            "label_policy": key[3],
            "subject_id": int(key[4]),
            "n_predictions": int(len(g)),
            "error_rate": float(1.0 - g["correct"].mean()),
            "prop_high_true": float(g["y_true"].mean()),
            "prop_high_pred": float(g["y_pred"].mean()),
        })
    return pd.DataFrame(rows)

def build_eeg_summary_features(path):
    X = np.load(path, mmap_mode="r")
    if X.ndim != 3:
        raise SystemExit(f"ERROR: expected EEG cache 3D, got shape={X.shape}")
    # Read-only summaries: no model training.
    means = np.asarray(X.mean(axis=2), dtype=np.float32)
    stds = np.asarray(X.std(axis=2), dtype=np.float32)
    absmeans = np.asarray(np.mean(np.abs(X), axis=2), dtype=np.float32)
    F = np.concatenate([means, stds, absmeans], axis=1)
    return F

def build_emg_summary_features(path):
    X = np.load(path, mmap_mode="r")
    if X.ndim != 2:
        raise SystemExit(f"ERROR: expected EMG feature cache 2D, got shape={X.shape}")
    return np.asarray(X, dtype=np.float32)

def zscore(X):
    X = np.asarray(X, dtype=np.float64)
    mu = np.nanmean(X, axis=0)
    sd = np.nanstd(X, axis=0)
    sd[sd < 1e-8] = 1.0
    Z = (X - mu) / sd
    Z = np.nan_to_num(Z, nan=0.0, posinf=0.0, neginf=0.0)
    return Z

def representation_diagnostics(index_df, feature_matrix, modality, discovered_cols):
    subj_col = find_subject_col(index_df)
    if subj_col is None:
        raise SystemExit(f"ERROR: no subject column for {modality}")
    n = min(len(index_df), int(feature_matrix.shape[0]))
    df = index_df.iloc[:n].copy()
    F = zscore(feature_matrix[:n])
    subjects = pd.to_numeric(df[subj_col], errors="coerce").to_numpy()
    subject_eta = eta_squared_factor(F, subjects)

    rows = []
    for task in TASKS:
        col = discovered_cols.get(task)
        if col is None:
            continue
        raw = pd.to_numeric(df[col], errors="coerce")
        for policy in POLICIES:
            y, _ = labels_from_values(raw, policy)
            y_np = y.astype("Float64").to_numpy(dtype=float, na_value=np.nan)
            label_eta = eta_squared_factor(F, y_np)
            corr = abs_corr_summary(F, y_np)
            sep = centroid_separation(F, y_np)
            ratio = float(subject_eta["eta_mean"] / max(label_eta["eta_mean"], 1e-12)) if not math.isnan(label_eta["eta_mean"]) else float("nan")
            rows.append({
                "modality": modality,
                "task": task,
                "label_policy": policy,
                "n": int(np.isfinite(y_np).sum()),
                "n_features": int(F.shape[1]),
                "subject_eta_mean": subject_eta["eta_mean"],
                "subject_eta_median": subject_eta["eta_median"],
                "subject_eta_max": subject_eta["eta_max"],
                "label_eta_mean": label_eta["eta_mean"],
                "label_eta_median": label_eta["eta_median"],
                "label_eta_max": label_eta["eta_max"],
                "subject_to_label_eta_ratio": ratio,
                "label_abs_corr_mean": corr["abs_corr_mean"],
                "label_abs_corr_max": corr["abs_corr_max"],
                "label_centroid_separation": sep,
                "subject_dominance_flag": bool((ratio > 5.0 and label_eta["eta_mean"] < 0.02) or (ratio > 10.0)),
            })
    return pd.DataFrame(rows)

# Load indices.
eeg_idx = pd.read_csv(CACHE / "idare_eeg_cache_index_baseline_corrected.csv")
emg_idx = pd.read_csv(CACHE / "idare_emg_feature_cache_index.csv")

label_eeg, eeg_cols = label_audit_for_index(eeg_idx, "EEG")
label_emg, emg_cols = label_audit_for_index(emg_idx, "EMG")
label_summary = pd.concat([label_eeg, label_emg], ignore_index=True)
pred_subject = load_prediction_subject_errors()
if not pred_subject.empty and not label_summary.empty:
    # Add broad subject error summaries where possible.
    err = pred_subject.groupby(["modality", "task", "subject_id"], as_index=False).agg(
        mean_prediction_error_rate=("error_rate", "mean"),
        max_prediction_error_rate=("error_rate", "max"),
        mean_true_prop_high=("prop_high_true", "mean"),
    )
    label_summary = label_summary.merge(err, on=["modality", "task", "subject_id"], how="left")

label_summary.to_csv(OUT_LABEL_CSV, index=False)

print("BUILDING_EEG_SUMMARY_FEATURES")
eeg_F = build_eeg_summary_features(CACHE / "idare_eeg_windows_32x640_float32_baseline_corrected.npy")
print("BUILDING_EMG_SUMMARY_FEATURES")
emg_F = build_emg_summary_features(CACHE / "idare_emg_features.npy")

repr_eeg = representation_diagnostics(eeg_idx, eeg_F, "EEG", eeg_cols)
repr_emg = representation_diagnostics(emg_idx, emg_F, "EMG", emg_cols)
repr_summary = pd.concat([repr_eeg, repr_emg], ignore_index=True)
repr_summary.to_csv(OUT_REPR_CSV, index=False)

# Aggregate diagnosis signals.
label_metrics = {}
if not label_summary.empty:
    label_metrics = {
        "mean_exact_midpoint_fraction": float(label_summary["exact_midpoint_fraction"].mean()),
        "mean_near_midpoint_fraction": float(label_summary["near_midpoint_fraction"].mean()),
        "max_subject_prop_skew_midpoint_as_high": float(label_summary["midpoint_as_high_abs_subject_prop_skew"].max()),
        "mean_subject_prop_skew_midpoint_as_high": float(label_summary["midpoint_as_high_abs_subject_prop_skew"].mean()),
        "high_skew_subject_rows_ge_0p20": int((label_summary["midpoint_as_high_abs_subject_prop_skew"] >= 0.20).sum()),
        "n_subject_balance_rows": int(len(label_summary)),
    }

repr_metrics = {}
if not repr_summary.empty:
    repr_metrics = {
        "mean_subject_eta": float(repr_summary["subject_eta_mean"].mean()),
        "mean_label_eta": float(repr_summary["label_eta_mean"].mean()),
        "median_subject_to_label_eta_ratio": float(repr_summary["subject_to_label_eta_ratio"].median()),
        "max_subject_to_label_eta_ratio": float(repr_summary["subject_to_label_eta_ratio"].max()),
        "subject_dominance_rows": int(repr_summary["subject_dominance_flag"].sum()),
        "n_representation_rows": int(len(repr_summary)),
    }

subject_skew = label_metrics.get("mean_subject_prop_skew_midpoint_as_high", 0.0) or 0.0
max_subject_skew = label_metrics.get("max_subject_prop_skew_midpoint_as_high", 0.0) or 0.0
near_mid = label_metrics.get("mean_near_midpoint_fraction", 0.0) or 0.0
subj_ratio = repr_metrics.get("median_subject_to_label_eta_ratio", 0.0) or 0.0
subj_dom_rows = repr_metrics.get("subject_dominance_rows", 0) or 0

# Decision rule: choose exactly one next objective.
if subject_skew >= 0.15 or max_subject_skew >= 0.35:
    leading_blocker = "label_task_subject_dependence"
    diagnosis = "subject_relative_label_task_problem_supported"
    recommended_next = "subject_relative_task_formulation_objective"
    reason = [
        "Per-subject label balance/skew is large enough that global binary labels are likely unstable under subject-heldout evaluation.",
        "A subject-relative task formulation should be tested before architecture, fusion, or augmentation.",
    ]
elif subj_dom_rows >= max(2, math.ceil(0.35 * max(1, len(repr_summary)))) or subj_ratio >= 5.0:
    leading_blocker = "representation_subject_nuisance_dominance"
    diagnosis = "representation_subject_nuisance_problem_supported"
    recommended_next = "representation_preprocessing_redesign_objective"
    reason = [
        "Read-only representation summaries show stronger subject separability than label separability.",
        "Representation/preprocessing should be redesigned before more complex models are added.",
    ]
elif near_mid >= 0.15:
    leading_blocker = "label_noise_midpoint_burden"
    diagnosis = "label_noise_or_midpoint_burden_supported"
    recommended_next = "data_quality_or_label_noise_audit_objective"
    reason = [
        "Midpoint or near-midpoint burden is high enough to justify a dedicated label-quality audit.",
        "A label-quality objective should precede any new model training.",
    ]
else:
    leading_blocker = "mixed_label_representation_subject_issue"
    diagnosis = "mixed_issue_requires_subject_relative_task_redesign"
    recommended_next = "subject_relative_task_formulation_objective"
    reason = [
        "No single representation or midpoint signal fully explains the failures.",
        "The safest next fix objective is still subject-relative task formulation because it directly addresses subject-heldout instability without changing model capacity.",
    ]

top_skew = []
if not label_summary.empty:
    cols = [
        "modality", "task", "subject_id", "fold_id", "n", "rating_mean",
        "exact_midpoint_fraction", "near_midpoint_fraction",
        "midpoint_as_high_prop_high", "midpoint_as_high_abs_subject_prop_skew",
        "mean_prediction_error_rate",
    ]
    available = [c for c in cols if c in label_summary.columns]
    top_skew = label_summary.sort_values(
        ["midpoint_as_high_abs_subject_prop_skew", "mean_prediction_error_rate"],
        ascending=[False, False],
        na_position="last",
    )[available].head(20).to_dict(orient="records")

repr_top = []
if not repr_summary.empty:
    repr_top = repr_summary.sort_values(
        ["subject_to_label_eta_ratio", "subject_eta_mean"],
        ascending=[False, False],
        na_position="last",
    ).head(20).to_dict(orient="records")

report = {
    "status": "complete_pending_review",
    "created_or_updated_utc": NOW,
    "objective": "docs/idare_representation_label_task_redesign_objective.md",
    "evidence_level": "read-only representation/label-task diagnostic; no new model training; no final performance claim",
    "inputs": {
        "eeg_index": ".cache/idare_eeg_cache_index_baseline_corrected.csv",
        "eeg_cache": ".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy",
        "emg_index": ".cache/idare_emg_feature_cache_index.csv",
        "emg_cache": ".cache/idare_emg_features.npy",
        "prior_reports": [
            "docs/idare_failure_analysis_report.md",
            "docs/idare_root_cause_diagnostic_report.md",
            "docs/idare_diagnostic_sanity_tests_report.md",
            "docs/idare_calibration_protocol_report.md",
        ],
    },
    "discovered_rating_columns": {
        "EEG": {k: str(v) if v is not None else None for k, v in eeg_cols.items()},
        "EMG": {k: str(v) if v is not None else None for k, v in emg_cols.items()},
    },
    "label_task_metrics": label_metrics,
    "representation_metrics": repr_metrics,
    "leading_blocker": leading_blocker,
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next,
    "recommendation_reason": reason,
    "top_subject_label_skew_rows": top_skew,
    "top_representation_subject_dominance_rows": repr_top,
    "outputs": {
        "report_md": str(OUT_MD),
        "report_json": str(OUT_JSON),
        "label_noise_subject_balance_summary_csv": str(OUT_LABEL_CSV),
        "representation_signal_diagnostic_summary_csv": str(OUT_REPR_CSV),
    },
    "not_authorized": [
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "final global label-policy lock",
        "new model training",
        "architecture ablation for improvement",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "broad hyperparameter search",
        "mainline change",
    ],
    "next_allowed_step": "Human review / closeout before creating the selected next objective.",
}
OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def fmt(x, d=4):
    try:
        if x is None or pd.isna(x):
            return "NA"
        return f"{float(x):.{d}f}"
    except Exception:
        return str(x)

md = []
md.append("# I-DARE Representation and Label-task Redesign Diagnostic Report")
md.append("")
md.append("## Status")
md.append("")
md.append("Representation/label-task diagnostic complete; pending human review.")
md.append("")
md.append(f"Generated UTC: `{NOW}`")
md.append("")
md.append("This report is read-only. No new model training was run.")
md.append("")
md.append("## Executive Diagnosis")
md.append("")
md.append(f"- Leading blocker: `{leading_blocker}`")
md.append(f"- Diagnosis: `{diagnosis}`")
md.append(f"- Recommended next objective: `{recommended_next}`")
md.append("")
for r in reason:
    md.append(f"- {r}")
md.append("")
md.append("## Label and Task Evidence")
md.append("")
md.append("| Metric | Value |")
md.append("|---|---:|")
for k, v in label_metrics.items():
    md.append(f"| {k} | {fmt(v)} |")
md.append("")
md.append("Discovered rating/label columns:")
md.append("")
md.append("| Modality | Valence column | Arousal column |")
md.append("|---|---|---|")
md.append(f"| EEG | `{eeg_cols.get('valence')}` | `{eeg_cols.get('arousal')}` |")
md.append(f"| EMG | `{emg_cols.get('valence')}` | `{emg_cols.get('arousal')}` |")
md.append("")
md.append("### Highest Subject Label-skew Rows")
md.append("")
md.append("| Mod | Task | Subject | Fold | N | Rating mean | Midpoint frac | Near-mid frac | Prop high | Abs skew | Error rate |")
md.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for r in top_skew[:15]:
    md.append(
        f"| {r.get('modality')} | {r.get('task')} | {r.get('subject_id')} | {r.get('fold_id')} | {r.get('n')} | "
        f"{fmt(r.get('rating_mean'))} | {fmt(r.get('exact_midpoint_fraction'))} | {fmt(r.get('near_midpoint_fraction'))} | "
        f"{fmt(r.get('midpoint_as_high_prop_high'))} | {fmt(r.get('midpoint_as_high_abs_subject_prop_skew'))} | {fmt(r.get('mean_prediction_error_rate'))} |"
    )
md.append("")
md.append("## Representation-signal Evidence")
md.append("")
md.append("| Metric | Value |")
md.append("|---|---:|")
for k, v in repr_metrics.items():
    md.append(f"| {k} | {fmt(v)} |")
md.append("")
md.append("### Strongest Subject-vs-label Dominance Rows")
md.append("")
md.append("| Mod | Task | Policy | N | Features | Subject eta | Label eta | Ratio | Max label corr | Centroid sep | Subject dominated |")
md.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
for r in repr_top[:15]:
    md.append(
        f"| {r.get('modality')} | {r.get('task')} | {r.get('label_policy')} | {r.get('n')} | {r.get('n_features')} | "
        f"{fmt(r.get('subject_eta_mean'))} | {fmt(r.get('label_eta_mean'))} | {fmt(r.get('subject_to_label_eta_ratio'))} | "
        f"{fmt(r.get('label_abs_corr_max'))} | {fmt(r.get('label_centroid_separation'))} | {r.get('subject_dominance_flag')} |"
    )
md.append("")
md.append("## Recommendation")
md.append("")
md.append(f"Recommended next objective: `{recommended_next}`")
md.append("")
md.append("Reasoning:")
md.append("")
for r in reason:
    md.append(f"- {r}")
md.append("")
md.append("## Expected Review Decision")
md.append("")
md.append("Human review should decide whether to accept this blocker diagnosis and create the recommended next objective.")
md.append("")
md.append("## Not Authorized")
md.append("")
for item in report["not_authorized"]:
    md.append(f"- {item}")
md.append("")
md.append("## Next Allowed Step")
md.append("")
md.append("Human review / closeout of this representation and label-task diagnostic report.")
md.append("")
md.append("Do not start fusion, architecture changes, augmentation, DG, broad hyperparameter search, or final claims from this report alone.")
md.append("")
OUT_MD.write_text("\n".join(md), encoding="utf-8")

# Update roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
row = "| I-DARE representation and label-task redesign report | read-only representation/label-task diagnostic complete; pending human review | yes | `docs/idare_representation_label_task_redesign_report.md` | Human review / closeout before the selected next objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |"
if "I-DARE representation and label-task redesign report" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE representation and label-task redesign objective |"):
            out.append(row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert report row in project_status_current.md")
    project_md = "\n".join(out) + "\n"

bullet = f"- Representation/label-task diagnostic report is complete in `docs/idare_representation_label_task_redesign_report.md`; diagnosis is `{diagnosis}` and recommended next objective is `{recommended_next}`."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: project status marker not found")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_representation_label_task_redesign_report"] = {
    "status": "complete_pending_review",
    "evidence": str(OUT_MD),
    "evidence_json": str(OUT_JSON),
    "label_summary_csv": str(OUT_LABEL_CSV),
    "representation_summary_csv": str(OUT_REPR_CSV),
    "leading_blocker": leading_blocker,
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next,
    "new_model_training_run": False,
    "not_authorized": report["not_authorized"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_REPRESENTATION_LABEL_TASK_REPORT_WRITTEN")
print(OUT_MD)
print(OUT_JSON)
print(OUT_LABEL_CSV)
print(OUT_REPR_CSV)
print("leading_blocker=", leading_blocker)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next)
PY
echo

echo "===== 4) validate generated outputs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path
json.loads(Path("docs/idare_representation_label_task_redesign_report.json").read_text(encoding="utf-8"))
print("OK_JSON")
for p in [
    Path("docs/idare_label_noise_subject_balance_summary.csv"),
    Path("docs/idare_representation_signal_diagnostic_summary.csv"),
]:
    with p.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(p.name, "rows=", len(rows))
    if not rows:
        raise SystemExit(f"ERROR: empty {p}")
PY

grep -n "## Status\|## Executive Diagnosis\|## Label and Task Evidence\|## Representation-signal Evidence\|## Recommendation\|## Next Allowed Step" docs/idare_representation_label_task_redesign_report.md
grep -n "representation and label-task redesign report" docs/project_status_current.md
echo

echo "===== 5) file list ====="
ls -lh \
  docs/idare_representation_label_task_redesign_report.md \
  docs/idare_representation_label_task_redesign_report.json \
  docs/idare_label_noise_subject_balance_summary.csv \
  docs/idare_representation_signal_diagnostic_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push representation/label-task diagnostic report ====="
git add \
  docs/idare_representation_label_task_redesign_report.md \
  docs/idare_representation_label_task_redesign_report.json \
  docs/idare_label_noise_subject_balance_summary.csv \
  docs/idare_representation_signal_diagnostic_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "analysis: add I-DARE representation label-task diagnostic"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_representation_label_task_report.log"
