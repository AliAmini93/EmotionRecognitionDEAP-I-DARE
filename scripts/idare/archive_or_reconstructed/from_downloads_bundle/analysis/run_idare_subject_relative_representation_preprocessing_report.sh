#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start subject-relative representation/preprocessing diagnostic report ====="
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
import csv
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
  docs/idare_subject_relative_representation_preprocessing_objective.md \
  docs/idare_subject_relative_representation_preprocessing_objective.json \
  docs/idare_subject_relative_minimal_training_review_status.md \
  docs/idare_subject_relative_minimal_training_report.md \
  docs/idare_subject_relative_minimal_training_report.json \
  docs/idare_subject_relative_task_formulation_report.md \
  docs/idare_subject_relative_candidate_matrix.csv \
  .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy \
  .cache/idare_eeg_cache_index_baseline_corrected.csv \
  .cache/idare_emg_features.npy \
  .cache/idare_emg_feature_cache_index.csv
echo

echo "===== 3) remove stale outputs and generate read-only diagnostic report ====="
rm -f \
  docs/idare_subject_relative_representation_preprocessing_report.md \
  docs/idare_subject_relative_representation_preprocessing_report.json \
  docs/idare_subject_relative_preprocessing_candidate_matrix.csv \
  docs/idare_subject_relative_distribution_shift_summary.csv

"$PY" - <<'PY'
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

REPORT_MD = DOCS / "idare_subject_relative_representation_preprocessing_report.md"
REPORT_JSON = DOCS / "idare_subject_relative_representation_preprocessing_report.json"
CANDIDATE_CSV = DOCS / "idare_subject_relative_preprocessing_candidate_matrix.csv"
SHIFT_CSV = DOCS / "idare_subject_relative_distribution_shift_summary.csv"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

OBJECTIVE_MD = DOCS / "idare_subject_relative_representation_preprocessing_objective.md"
OBJECTIVE_JSON = DOCS / "idare_subject_relative_representation_preprocessing_objective.json"
PREV_REPORT = DOCS / "idare_subject_relative_minimal_training_report.md"
PREV_REPORT_JSON = DOCS / "idare_subject_relative_minimal_training_report.json"

EEG_NPY = Path(".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy")
EEG_INDEX = Path(".cache/idare_eeg_cache_index_baseline_corrected.csv")
EMG_NPY = Path(".cache/idare_emg_features.npy")
EMG_INDEX = Path(".cache/idare_emg_feature_cache_index.csv")

TASKS = ["valence", "arousal"]
FORMULATION = "subject_top_bottom_quantile_q33"
SEED = 11
FOLDS = 6

def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def infer_rating_col(df, task):
    lower = {str(c).lower(): c for c in df.columns}
    preferred = [
        task, f"{task}_score", f"{task}_rating", f"rating_{task}",
        f"{task}_raw", f"raw_{task}", f"deap_{task}",
        f"{task}_self_report", f"self_report_{task}",
    ]
    forbidden = ["midpoint", "discard", "binary", "label", "pred", "prob", "class"]
    candidates = []
    for name in preferred:
        if name.lower() in lower:
            candidates.append(lower[name.lower()])
    for c in df.columns:
        cl = str(c).lower()
        if task in cl and not any(bad in cl for bad in forbidden):
            candidates.append(c)
    seen = []
    for c in candidates:
        if c not in seen:
            seen.append(c)
    scored = []
    for c in seen:
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(s) == 0:
            continue
        unique = int(s.nunique())
        vmin = float(s.min())
        vmax = float(s.max())
        raw_like = (unique > 2) or (vmax > 1.5) or (vmin < 0.0)
        if not raw_like:
            continue
        exact_bonus = 10 if str(c).lower() == task else 0
        score = exact_bonus + min(unique, 20) + (5 if vmax > 2 else 0)
        scored.append((score, str(c)))
    if not scored:
        raise SystemExit(f"ERROR: could not infer raw rating column for task={task}")
    scored.sort(reverse=True)
    return scored[0][1]

def subject_q33_labels(df, task, rating_col):
    subjects = pd.to_numeric(df["subject_id"], errors="coerce").astype("Int64")
    raw = pd.to_numeric(df[rating_col], errors="coerce")
    labels = pd.Series(np.nan, index=df.index, dtype="float64")
    detail_rows = []
    for subject_id, idx in df.groupby(subjects, dropna=True).groups.items():
        idx = list(idx)
        x = raw.loc[idx].dropna()
        n = int(len(x))
        if n == 0:
            detail_rows.append({"subject_id": int(subject_id), "n_valid": 0, "n_low": 0, "n_high": 0, "n_mid": 0})
            continue
        q_low = float(x.quantile(1.0 / 3.0))
        q_high = float(x.quantile(2.0 / 3.0))
        n_low = n_high = 0
        if q_high > q_low:
            vals = raw.loc[idx]
            low = vals <= q_low
            high = vals >= q_high
            labels.loc[vals[low].index] = 0.0
            labels.loc[vals[high].index] = 1.0
            n_low = int(low.fillna(False).sum())
            n_high = int(high.fillna(False).sum())
        detail_rows.append({
            "subject_id": int(subject_id),
            "q_low": q_low,
            "q_high": q_high,
            "n_valid": int(n_low + n_high),
            "n_low": n_low,
            "n_high": n_high,
            "n_mid": int(n - n_low - n_high),
        })
    return labels.to_numpy(), detail_rows

def make_folds(subjects, n_folds=6, seed=11):
    subjects = np.asarray(sorted(set(int(s) for s in subjects)), dtype=int)
    rng = np.random.default_rng(int(seed))
    shuffled = subjects.copy()
    rng.shuffle(shuffled)
    chunks = np.array_split(shuffled, n_folds)
    return {i: sorted(int(x) for x in chunk.tolist()) for i, chunk in enumerate(chunks, start=1)}

def build_eeg_summary(eeg_path):
    print("BUILDING_EEG_SUMMARY_FEATURES")
    x = np.load(eeg_path, mmap_mode="r")
    # Shape expected [n, channels, time].
    mean = np.asarray(x.mean(axis=2), dtype=np.float32)
    std = np.asarray(x.std(axis=2), dtype=np.float32)
    absmean = np.asarray(np.abs(x).mean(axis=2), dtype=np.float32)
    ptp = np.asarray(x.max(axis=2) - x.min(axis=2), dtype=np.float32)
    # temporal roughness: std of first differences
    diffstd = np.asarray(np.diff(x, axis=2).std(axis=2), dtype=np.float32)
    raw_summary = np.concatenate([mean, std, absmean, ptp, diffstd], axis=1)

    # Per-window, per-channel zscore summary. This is leakage-safe because it uses only each trial waveform.
    eps = 1e-6
    z_absmean_parts = []
    z_ptp_parts = []
    z_diffstd_parts = []
    n = x.shape[0]
    chunk = 256
    for start in range(0, n, chunk):
        stop = min(n, start + chunk)
        xb = np.asarray(x[start:stop], dtype=np.float32)
        mu = xb.mean(axis=2, keepdims=True)
        sd = xb.std(axis=2, keepdims=True) + eps
        z = (xb - mu) / sd
        z_absmean_parts.append(np.asarray(np.abs(z).mean(axis=2), dtype=np.float32))
        z_ptp_parts.append(np.asarray(z.max(axis=2) - z.min(axis=2), dtype=np.float32))
        z_diffstd_parts.append(np.asarray(np.diff(z, axis=2).std(axis=2), dtype=np.float32))
    z_summary = np.concatenate([
        np.concatenate(z_absmean_parts, axis=0),
        np.concatenate(z_ptp_parts, axis=0),
        np.concatenate(z_diffstd_parts, axis=0),
    ], axis=1)
    return {
        "eeg_summary_raw": raw_summary,
        "eeg_window_channel_zscore_summary": z_summary,
    }

def build_emg_features(emg_path):
    print("BUILDING_EMG_FEATURES")
    x = np.asarray(np.load(emg_path, mmap_mode="r"), dtype=np.float32)
    eps = 1e-6
    l2 = x / (np.linalg.norm(x, axis=1, keepdims=True) + eps)
    log_abs = np.sign(x) * np.log1p(np.abs(x))
    return {
        "emg_raw_features": x,
        "emg_record_l2_normalized": l2,
        "emg_signed_log1p_features": log_abs,
    }

def fit_transform_candidate(candidate, base_train, base_val):
    eps = 1e-6
    if candidate.endswith("_train_standard_scaled"):
        mu = base_train.mean(axis=0, keepdims=True)
        sd = base_train.std(axis=0, keepdims=True) + eps
        return (base_train - mu) / sd, (base_val - mu) / sd, "low", "train-only standard scaling"
    if candidate.endswith("_train_robust_scaled"):
        med = np.median(base_train, axis=0, keepdims=True)
        q25 = np.quantile(base_train, 0.25, axis=0, keepdims=True)
        q75 = np.quantile(base_train, 0.75, axis=0, keepdims=True)
        iqr = (q75 - q25) + eps
        return (base_train - med) / iqr, (base_val - med) / iqr, "low", "train-only robust scaling"
    return base_train, base_val, "low", "deterministic record-level or raw feature transform"

def compute_metrics(train_x, val_x, train_y, val_y):
    eps = 1e-6
    train_x = np.asarray(train_x, dtype=np.float32)
    val_x = np.asarray(val_x, dtype=np.float32)
    train_y = np.asarray(train_y, dtype=int)
    val_y = np.asarray(val_y, dtype=int)

    train_std = train_x.std(axis=0) + eps
    train_mean = train_x.mean(axis=0)
    val_mean = val_x.mean(axis=0)
    domain_shift = float(np.mean(np.abs((val_mean - train_mean) / train_std)))
    centroid_l2 = float(np.linalg.norm((val_mean - train_mean) / train_std) / math.sqrt(train_x.shape[1]))

    def class_sep(x, y):
        if len(np.unique(y)) < 2:
            return 0.0
        a = x[y == 0]
        b = x[y == 1]
        if len(a) == 0 or len(b) == 0:
            return 0.0
        pooled = x.std(axis=0) + eps
        return float(np.linalg.norm((b.mean(axis=0) - a.mean(axis=0)) / pooled) / math.sqrt(x.shape[1]))

    train_sep = class_sep(train_x, train_y)
    val_sep = class_sep(val_x, val_y)
    pos_train = float(np.mean(train_y == 1)) if len(train_y) else None
    pos_val = float(np.mean(val_y == 1)) if len(val_y) else None

    return {
        "domain_shift_mean_abs_z": domain_shift,
        "domain_shift_centroid_l2": centroid_l2,
        "train_class_separation": train_sep,
        "val_class_separation": val_sep,
        "val_train_separation_ratio": float(val_sep / (train_sep + eps)),
        "train_pos_rate": pos_train,
        "val_pos_rate": pos_val,
        "val_balance_gap": None if pos_val is None else float(abs(pos_val - 0.5)),
    }

def valid_rows_for_task(index_df, task):
    rating_col = infer_rating_col(index_df, task)
    labels, details = subject_q33_labels(index_df, task, rating_col)
    valid = np.isin(labels, [0.0, 1.0])
    subjects = pd.to_numeric(index_df["subject_id"], errors="coerce").to_numpy()
    return labels, valid, subjects, rating_col, details

def create_candidate_features(modality, feature_blocks):
    candidates = {}
    if modality == "EEG":
        base = feature_blocks["eeg_summary_raw"]
        zbase = feature_blocks["eeg_window_channel_zscore_summary"]
        candidates["eeg_summary_raw"] = ("eeg_summary_raw", base)
        candidates["eeg_summary_train_standard_scaled"] = ("eeg_summary_raw", base)
        candidates["eeg_summary_train_robust_scaled"] = ("eeg_summary_raw", base)
        candidates["eeg_window_channel_zscore_summary"] = ("eeg_window_channel_zscore_summary", zbase)
        candidates["eeg_window_channel_zscore_train_standard_scaled"] = ("eeg_window_channel_zscore_summary", zbase)
    else:
        raw = feature_blocks["emg_raw_features"]
        l2 = feature_blocks["emg_record_l2_normalized"]
        log_abs = feature_blocks["emg_signed_log1p_features"]
        candidates["emg_raw_features"] = ("emg_raw_features", raw)
        candidates["emg_train_standard_scaled"] = ("emg_raw_features", raw)
        candidates["emg_train_robust_scaled"] = ("emg_raw_features", raw)
        candidates["emg_record_l2_normalized"] = ("emg_record_l2_normalized", l2)
        candidates["emg_signed_log1p_train_standard_scaled"] = ("emg_signed_log1p_features", log_abs)
    return candidates

def short_candidate_description(name):
    descriptions = {
        "eeg_summary_raw": "raw EEG summary features",
        "eeg_summary_train_standard_scaled": "train-only standard scaling on EEG summary features",
        "eeg_summary_train_robust_scaled": "train-only robust scaling on EEG summary features",
        "eeg_window_channel_zscore_summary": "per-trial channel zscore then EEG summary features",
        "eeg_window_channel_zscore_train_standard_scaled": "per-trial channel zscore summary plus train-only standard scaling",
        "emg_raw_features": "raw EMG features",
        "emg_train_standard_scaled": "train-only standard scaling on EMG features",
        "emg_train_robust_scaled": "train-only robust scaling on EMG features",
        "emg_record_l2_normalized": "per-record L2 normalization on EMG features",
        "emg_signed_log1p_train_standard_scaled": "signed log1p EMG features plus train-only standard scaling",
    }
    return descriptions.get(name, name)

objective = load_json(OBJECTIVE_JSON)
previous = load_json(PREV_REPORT_JSON)

eeg_index = pd.read_csv(EEG_INDEX)
emg_index = pd.read_csv(EMG_INDEX)
eeg_blocks = build_eeg_summary(EEG_NPY)
emg_blocks = build_emg_features(EMG_NPY)

modalities = {
    "EEG": {"index": eeg_index, "blocks": eeg_blocks},
    "EMG": {"index": emg_index, "blocks": emg_blocks},
}

shift_rows = []
label_audit = {}
for modality, info in modalities.items():
    index_df = info["index"]
    blocks = info["blocks"]
    candidate_features = create_candidate_features(modality, blocks)
    label_audit[modality] = {}
    for task in TASKS:
        labels, valid_mask, subjects, rating_col, details = valid_rows_for_task(index_df, task)
        valid_subjects = sorted(set(int(s) for s, ok in zip(subjects, valid_mask) if ok and not pd.isna(s)))
        folds = make_folds(valid_subjects, FOLDS, SEED)
        label_audit[modality][task] = {
            "rating_col": rating_col,
            "valid_subjects": len(valid_subjects),
            "valid_samples": int(valid_mask.sum()),
            "class0": int(np.sum(labels[valid_mask] == 0)),
            "class1": int(np.sum(labels[valid_mask] == 1)),
        }
        for fold_id, val_subjects in folds.items():
            val_set = set(val_subjects)
            is_val = np.array([int(s) in val_set if not pd.isna(s) else False for s in subjects], dtype=bool)
            train_mask = valid_mask & (~is_val)
            val_mask = valid_mask & is_val
            train_y = labels[train_mask].astype(int)
            val_y = labels[val_mask].astype(int)
            if train_mask.sum() == 0 or val_mask.sum() == 0:
                continue
            for candidate_name, (base_name, feature_matrix) in candidate_features.items():
                train_base = feature_matrix[train_mask]
                val_base = feature_matrix[val_mask]
                train_x, val_x, leakage_risk, transform_note = fit_transform_candidate(candidate_name, train_base, val_base)
                metrics = compute_metrics(train_x, val_x, train_y, val_y)
                shift_rows.append({
                    "modality": modality,
                    "task": task,
                    "fold": fold_id,
                    "seed": SEED,
                    "candidate": candidate_name,
                    "base_feature_block": base_name,
                    "description": short_candidate_description(candidate_name),
                    "leakage_risk": leakage_risk,
                    "transform_note": transform_note,
                    "feature_dim": int(train_x.shape[1]),
                    "n_train": int(len(train_y)),
                    "n_val": int(len(val_y)),
                    "train_class0": int(np.sum(train_y == 0)),
                    "train_class1": int(np.sum(train_y == 1)),
                    "val_class0": int(np.sum(val_y == 0)),
                    "val_class1": int(np.sum(val_y == 1)),
                    **metrics,
                })

shift_df = pd.DataFrame(shift_rows)
if shift_df.empty:
    raise SystemExit("ERROR: no shift rows generated")

SHIFT_CSV.write_text(shift_df.to_csv(index=False), encoding="utf-8")

# Aggregate candidates and score relative to raw baselines.
candidate_rows = []
for (modality, candidate), g in shift_df.groupby(["modality", "candidate"]):
    raw_candidate = "eeg_summary_raw" if modality == "EEG" else "emg_raw_features"
    raw_g = shift_df[(shift_df["modality"] == modality) & (shift_df["candidate"] == raw_candidate)]
    merged = g.merge(
        raw_g[["task", "fold", "domain_shift_mean_abs_z", "val_class_separation"]],
        on=["task", "fold"],
        suffixes=("", "_raw"),
        how="left",
    )
    shift_reduction = (merged["domain_shift_mean_abs_z_raw"] - merged["domain_shift_mean_abs_z"]).mean()
    sep_gain = (merged["val_class_separation"] - merged["val_class_separation_raw"]).mean()
    mean_domain_shift = float(g["domain_shift_mean_abs_z"].mean())
    mean_val_sep = float(g["val_class_separation"].mean())
    mean_sep_ratio = float(g["val_train_separation_ratio"].mean())
    mean_balance_gap = float(g["val_balance_gap"].mean())
    low_leakage = bool((g["leakage_risk"] == "low").all())
    implementation_risk = "low" if ("standard" in candidate or "robust" in candidate or "raw" in candidate) else "medium"
    # Diagnostic score: prefer shift reduction, validation separation gain, low balance gap, and low implementation risk.
    score = 0.0
    score += max(0.0, float(shift_reduction)) * 2.0
    score += max(0.0, float(sep_gain)) * 1.5
    score += max(0.0, mean_val_sep) * 0.5
    score += max(0.0, 0.10 - mean_balance_gap) * 0.5
    if not low_leakage:
        score -= 2.0
    if implementation_risk == "medium":
        score -= 0.05
    is_baseline = candidate == raw_candidate
    candidate_rows.append({
        "modality": modality,
        "candidate": candidate,
        "description": short_candidate_description(candidate),
        "is_raw_baseline": is_baseline,
        "leakage_risk": "low" if low_leakage else "review_required",
        "implementation_risk": implementation_risk,
        "mean_domain_shift_mean_abs_z": mean_domain_shift,
        "mean_val_class_separation": mean_val_sep,
        "mean_val_train_separation_ratio": mean_sep_ratio,
        "mean_val_balance_gap": mean_balance_gap,
        "mean_shift_reduction_vs_raw": float(shift_reduction),
        "mean_val_sep_gain_vs_raw": float(sep_gain),
        "diagnostic_score": float(score),
    })

cand_df = pd.DataFrame(candidate_rows)
cand_df = cand_df.sort_values(["diagnostic_score", "mean_shift_reduction_vs_raw"], ascending=[False, False])
cand_df.to_csv(CANDIDATE_CSV, index=False)

non_raw = cand_df[cand_df["is_raw_baseline"] == False].copy()
if non_raw.empty:
    raise SystemExit("ERROR: no non-raw candidates")
best = non_raw.iloc[0].to_dict()
best_candidate = str(best["candidate"])
best_modality = str(best["modality"])
best_score = float(best["diagnostic_score"])
best_shift_reduction = float(best["mean_shift_reduction_vs_raw"])
best_sep_gain = float(best["mean_val_sep_gain_vs_raw"])

if best_score > 0.10 and best_shift_reduction >= -0.02:
    recommended_next = "minimal_subject_relative_preprocessed_training_objective"
    diagnosis = "preprocessing_candidate_worth_testing"
else:
    recommended_next = "subject_relative_feature_engineering_objective"
    diagnosis = "preprocessing_diagnostic_not_enough"

report = {
    "status": "complete_pending_review",
    "created_or_updated_utc": NOW,
    "objective": str(OBJECTIVE_MD),
    "objective_json": str(OBJECTIVE_JSON),
    "prior_report": str(PREV_REPORT),
    "evidence_level": "read-only representation/preprocessing diagnostic; no new performance training",
    "formulation": FORMULATION,
    "label_audit": label_audit,
    "diagnosis": diagnosis,
    "best_candidate": {
        "modality": best_modality,
        "candidate": best_candidate,
        "description": short_candidate_description(best_candidate),
        "diagnostic_score": best_score,
        "mean_shift_reduction_vs_raw": best_shift_reduction,
        "mean_val_sep_gain_vs_raw": best_sep_gain,
        "leakage_risk": best.get("leakage_risk"),
        "implementation_risk": best.get("implementation_risk"),
    },
    "candidate_matrix_csv": str(CANDIDATE_CSV),
    "distribution_shift_summary_csv": str(SHIFT_CSV),
    "candidate_count": int(len(cand_df)),
    "shift_summary_rows": int(len(shift_df)),
    "recommended_next_objective": recommended_next,
    "not_authorized": objective.get("not_authorized", []),
    "next_allowed_step": "Human review / closeout before any minimal preprocessed training objective or feature-engineering objective.",
}
REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def fmt(x, d=4):
    try:
        if x is None or pd.isna(x):
            return "NA"
        return f"{float(x):.{d}f}"
    except Exception:
        return str(x)

md = []
md.append("# I-DARE Subject-relative Representation/Preprocessing Report")
md.append("")
md.append("## Status")
md.append("")
md.append("Read-only representation/preprocessing diagnostic complete; pending human review.")
md.append("")
md.append(f"Generated UTC: `{NOW}`")
md.append("")
md.append("No new performance training was run.")
md.append("")
md.append("## Diagnostic Summary")
md.append("")
md.append(f"- Diagnosis: `{diagnosis}`")
md.append(f"- Recommended next objective: `{recommended_next}`")
md.append(f"- Best candidate: `{best_candidate}`")
md.append(f"- Best candidate modality: `{best_modality}`")
md.append(f"- Diagnostic score: `{fmt(best_score)}`")
md.append(f"- Mean shift reduction vs raw: `{fmt(best_shift_reduction)}`")
md.append(f"- Mean validation-separation gain vs raw: `{fmt(best_sep_gain)}`")
md.append("")
md.append("## Candidate Ranking")
md.append("")
md.append("| Rank | Modality | Candidate | Raw baseline | Shift reduction vs raw | Val sep gain vs raw | Domain shift | Val class sep | Leakage risk | Implementation risk | Score |")
md.append("|---:|---|---|---:|---:|---:|---:|---:|---|---|---:|")
for i, row in enumerate(cand_df.head(12).to_dict(orient="records"), start=1):
    md.append(
        f"| {i} | {row['modality']} | `{row['candidate']}` | {row['is_raw_baseline']} | "
        f"{fmt(row['mean_shift_reduction_vs_raw'])} | {fmt(row['mean_val_sep_gain_vs_raw'])} | "
        f"{fmt(row['mean_domain_shift_mean_abs_z'])} | {fmt(row['mean_val_class_separation'])} | "
        f"{row['leakage_risk']} | {row['implementation_risk']} | {fmt(row['diagnostic_score'])} |"
    )
md.append("")
md.append("## Label Audit")
md.append("")
md.append("| Modality | Task | Rating column | Valid subjects | Valid samples | Class 0 | Class 1 |")
md.append("|---|---|---|---:|---:|---:|---:|")
for modality, task_map in label_audit.items():
    for task, row in task_map.items():
        md.append(
            f"| {modality} | {task} | `{row['rating_col']}` | {row['valid_subjects']} | "
            f"{row['valid_samples']} | {row['class0']} | {row['class1']} |"
        )
md.append("")
md.append("## Output Files")
md.append("")
md.append(f"- `{CANDIDATE_CSV}`")
md.append(f"- `{SHIFT_CSV}`")
md.append(f"- `{REPORT_JSON}`")
md.append("")
md.append("## Interpretation")
md.append("")
if recommended_next == "minimal_subject_relative_preprocessed_training_objective":
    md.append("At least one low-leakage preprocessing candidate has enough diagnostic support to justify a small separately authorized training test.")
else:
    md.append("The preprocessing-only diagnostic is not strong enough to justify another training pass; the next objective should focus on feature engineering/design.")
md.append("")
md.append("## Not Authorized")
md.append("")
for item in report["not_authorized"]:
    md.append(f"- {item}")
md.append("")
md.append("## Next Allowed Step")
md.append("")
md.append(report["next_allowed_step"])
md.append("")
REPORT_MD.write_text("\n".join(md), encoding="utf-8")

# Update central roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
row = "| I-DARE subject-relative representation/preprocessing report | read-only representation/preprocessing diagnostic complete; pending human review | yes | `docs/idare_subject_relative_representation_preprocessing_report.md` | Human review / closeout before selected preprocessing training or feature-engineering objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search; mainline change. |"
if "I-DARE subject-relative representation/preprocessing report" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE subject-relative representation/preprocessing objective |"):
            out.append(row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert roadmap row")
    project_md = "\n".join(out) + "\n"

bullet = f"- Subject-relative representation/preprocessing diagnosis is complete in `docs/idare_subject_relative_representation_preprocessing_report.md`; recommended next objective is `{recommended_next}` after human review."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: project status marker not found")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = load_json(PROJECT_JSON)
decisions = project_json.setdefault("decisions", {})
decisions["idare_subject_relative_representation_preprocessing_report"] = {
    "status": "complete_pending_review",
    "evidence": str(REPORT_MD),
    "evidence_json": str(REPORT_JSON),
    "diagnosis": diagnosis,
    "best_candidate": report["best_candidate"],
    "recommended_next_objective": recommended_next,
    "not_authorized": report["not_authorized"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_REPRESENTATION_PREPROCESSING_REPORT_WRITTEN")
print(REPORT_MD)
print(REPORT_JSON)
print(CANDIDATE_CSV)
print(SHIFT_CSV)
print("diagnosis=", diagnosis)
print("best_candidate=", best_candidate)
print("recommended_next_objective=", recommended_next)
PY
echo

echo "===== 4) validate generated outputs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path

for p in [
    Path("docs/idare_subject_relative_representation_preprocessing_report.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

for p in [
    Path("docs/idare_subject_relative_preprocessing_candidate_matrix.csv"),
    Path("docs/idare_subject_relative_distribution_shift_summary.csv"),
]:
    with p.open(newline="", encoding="utf-8") as f:
        n = sum(1 for _ in csv.DictReader(f))
    print(p.name, "rows=", n)
    if n <= 0:
        raise SystemExit(f"ERROR: empty CSV {p}")

report = json.loads(Path("docs/idare_subject_relative_representation_preprocessing_report.json").read_text(encoding="utf-8"))
if report.get("recommended_next_objective") not in {
    "minimal_subject_relative_preprocessed_training_objective",
    "subject_relative_feature_engineering_objective",
}:
    raise SystemExit("ERROR: invalid recommended_next_objective")
print("recommended_next_objective=", report.get("recommended_next_objective"))
print("best_candidate=", report.get("best_candidate", {}).get("candidate"))
PY

grep -n "## Status\|## Diagnostic Summary\|## Candidate Ranking\|## Label Audit\|## Interpretation\|## Next Allowed Step" docs/idare_subject_relative_representation_preprocessing_report.md
grep -n "subject-relative representation/preprocessing report" docs/project_status_current.md
echo

echo "===== 5) file list ====="
ls -lh \
  docs/idare_subject_relative_representation_preprocessing_report.md \
  docs/idare_subject_relative_representation_preprocessing_report.json \
  docs/idare_subject_relative_preprocessing_candidate_matrix.csv \
  docs/idare_subject_relative_distribution_shift_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push report ====="
git add \
  docs/idare_subject_relative_representation_preprocessing_report.md \
  docs/idare_subject_relative_representation_preprocessing_report.json \
  docs/idare_subject_relative_preprocessing_candidate_matrix.csv \
  docs/idare_subject_relative_distribution_shift_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "analysis: add I-DARE subject-relative preprocessing diagnostic"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_subject_relative_preprocessing_report.log"
