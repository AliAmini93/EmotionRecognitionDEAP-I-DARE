#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start minimal subject-relative preprocessed training first pass ====="
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
import torch
print("torch_cuda_available=", bool(torch.cuda.is_available()))
print("OK_IMPORTS")
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repo is not clean; commit/stash current changes before running."
  git status --short --branch
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required inputs ====="
ls -lh \
  docs/idare_minimal_subject_relative_preprocessed_training_objective.md \
  docs/idare_minimal_subject_relative_preprocessed_training_objective.json \
  docs/idare_subject_relative_representation_preprocessing_review_status.md \
  docs/idare_subject_relative_representation_preprocessing_report.md \
  docs/idare_subject_relative_preprocessing_candidate_matrix.csv \
  docs/idare_subject_relative_minimal_training_report.json \
  docs/idare_subject_relative_minimal_eeg_primary.json \
  docs/idare_subject_relative_minimal_emg_primary.json \
  docs/idare_broader_eval_eeg_stim_bsl_only_primary.json \
  docs/idare_broader_eval_emg_feature_only_primary.json \
  .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy \
  .cache/idare_eeg_cache_index_baseline_corrected.csv \
  .cache/idare_emg_features.npy \
  .cache/idare_emg_feature_cache_index.csv
echo

echo "===== 3) remove stale outputs and run 24-run first pass ====="
rm -f \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.md \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.md \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv \
  docs/idare_subject_relative_preprocessed_minimal_training_report.md \
  docs/idare_subject_relative_preprocessed_minimal_training_report.json

"$PY" - <<'PY'
import csv
import json
import math
import os
import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

OBJECTIVE_MD = DOCS / "idare_minimal_subject_relative_preprocessed_training_objective.md"
OBJECTIVE_JSON = DOCS / "idare_minimal_subject_relative_preprocessed_training_objective.json"
REVIEW_MD = DOCS / "idare_subject_relative_representation_preprocessing_review_status.md"
PREPROCESSING_REPORT_MD = DOCS / "idare_subject_relative_representation_preprocessing_report.md"
PREPROCESSING_REPORT_JSON = DOCS / "idare_subject_relative_representation_preprocessing_report.json"

PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

EEG_NPY = Path(".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy")
EEG_INDEX = Path(".cache/idare_eeg_cache_index_baseline_corrected.csv")
EMG_NPY = Path(".cache/idare_emg_features.npy")
EMG_INDEX = Path(".cache/idare_emg_feature_cache_index.csv")

OUTS = {
    "EEG": {
        "md": DOCS / "idare_subject_relative_preprocessed_minimal_eeg_primary.md",
        "json": DOCS / "idare_subject_relative_preprocessed_minimal_eeg_primary.json",
        "pred": DOCS / "idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv",
        "candidate": "eeg_window_channel_zscore_train_standard_scaled",
        "description": "per-trial channel zscore summary features plus train-only standard scaling",
    },
    "EMG": {
        "md": DOCS / "idare_subject_relative_preprocessed_minimal_emg_primary.md",
        "json": DOCS / "idare_subject_relative_preprocessed_minimal_emg_primary.json",
        "pred": DOCS / "idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv",
        "candidate": "emg_signed_log1p_train_standard_scaled",
        "description": "signed log1p EMG features plus train-only standard scaling",
    },
}
REPORT_MD = DOCS / "idare_subject_relative_preprocessed_minimal_training_report.md"
REPORT_JSON = DOCS / "idare_subject_relative_preprocessed_minimal_training_report.json"

TASKS = ["valence", "arousal"]
FOLDS = 6
SEED = 11
RECIPE = "ce_class_weighted"
FORMULATION = "subject_top_bottom_quantile_q33"
EPOCHS = {"EEG": 12, "EMG": 20}
BATCH_SIZE = 64
LR = 1e-3
WEIGHT_DECAY = 1e-4

def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def infer_rating_col(df, task):
    lower = {str(c).lower(): c for c in df.columns}
    preferred = [
        task,
        f"{task}_score",
        f"{task}_rating",
        f"rating_{task}",
        f"{task}_raw",
        f"raw_{task}",
        f"deap_{task}",
        f"{task}_self_report",
        f"self_report_{task}",
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

def subject_q33_labels(index_df, task):
    rating_col = infer_rating_col(index_df, task)
    subjects = pd.to_numeric(index_df["subject_id"], errors="coerce").astype("Int64")
    raw = pd.to_numeric(index_df[rating_col], errors="coerce")
    labels = pd.Series(np.nan, index=index_df.index, dtype="float64")
    subject_details = []
    for subject_id, idx in index_df.groupby(subjects, dropna=True).groups.items():
        idx = list(idx)
        vals = raw.loc[idx].dropna()
        if len(vals) == 0:
            subject_details.append({
                "subject_id": int(subject_id),
                "n_valid": 0,
                "n_low": 0,
                "n_high": 0,
                "n_middle_discarded": 0,
            })
            continue
        q_low = float(vals.quantile(1.0 / 3.0))
        q_high = float(vals.quantile(2.0 / 3.0))
        n_low = n_high = 0
        if q_high > q_low:
            all_vals = raw.loc[idx]
            low = all_vals <= q_low
            high = all_vals >= q_high
            labels.loc[all_vals[low].index] = 0.0
            labels.loc[all_vals[high].index] = 1.0
            n_low = int(low.fillna(False).sum())
            n_high = int(high.fillna(False).sum())
        subject_details.append({
            "subject_id": int(subject_id),
            "q_low": q_low,
            "q_high": q_high,
            "n_valid": int(n_low + n_high),
            "n_low": n_low,
            "n_high": n_high,
            "n_middle_discarded": int(len(vals) - n_low - n_high),
        })
    labels_arr = labels.to_numpy()
    valid_mask = np.isin(labels_arr, [0.0, 1.0])
    return labels_arr, valid_mask, rating_col, subject_details

def make_folds(subjects, n_folds=6, seed=11):
    arr = np.asarray(sorted(set(int(s) for s in subjects)), dtype=int)
    rng = np.random.default_rng(int(seed))
    shuffled = arr.copy()
    rng.shuffle(shuffled)
    chunks = np.array_split(shuffled, n_folds)
    return {i: sorted(int(x) for x in chunk.tolist()) for i, chunk in enumerate(chunks, start=1)}

def compute_metrics(y_true, prob1, threshold=0.5):
    y_true = np.asarray(y_true, dtype=int)
    prob1 = np.asarray(prob1, dtype=float)
    y_pred = (prob1 >= threshold).astype(int)
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    n = int(len(y_true))
    acc = float((tp + tn) / n) if n else 0.0
    tpr = float(tp / (tp + fn)) if (tp + fn) else 0.0
    tnr = float(tn / (tn + fp)) if (tn + fp) else 0.0
    bal = float((tpr + tnr) / 2.0)
    f1_pos = float((2 * tp) / (2 * tp + fp + fn)) if (2 * tp + fp + fn) else 0.0
    f1_neg = float((2 * tn) / (2 * tn + fp + fn)) if (2 * tn + fp + fn) else 0.0
    macro_f1 = float((f1_pos + f1_neg) / 2.0)
    majority = float(max(np.mean(y_true == 0), np.mean(y_true == 1))) if n else 0.0
    pred_counts = {"0": int(np.sum(y_pred == 0)), "1": int(np.sum(y_pred == 1))}
    one_class_pred = bool(pred_counts["0"] == 0 or pred_counts["1"] == 0)
    return {
        "confusion": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        "final_accuracy": acc,
        "final_balanced_accuracy": bal,
        "final_macro_f1": macro_f1,
        "majority_accuracy": majority,
        "pred_counts": pred_counts,
        "one_class_pred": one_class_pred,
        "threshold": threshold,
    }, y_pred

def set_all_seeds(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

class SmallMLP(nn.Module):
    def __init__(self, input_dim, hidden=64, dropout=0.10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, 2),
        )

    def forward(self, x):
        return self.net(x)

def train_predict(train_x, train_y, val_x, epochs, seed, modality, task, fold_id):
    run_seed = int(seed + fold_id * 101 + (0 if task == "valence" else 17) + (0 if modality == "EEG" else 31))
    set_all_seeds(run_seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_x = np.asarray(train_x, dtype=np.float32)
    val_x = np.asarray(val_x, dtype=np.float32)
    train_y = np.asarray(train_y, dtype=np.int64)

    model = SmallMLP(train_x.shape[1]).to(device)
    counts = np.bincount(train_y, minlength=2).astype(np.float32)
    weights = float(len(train_y)) / (2.0 * np.maximum(counts, 1.0))
    weight_t = torch.tensor(weights, dtype=torch.float32, device=device)
    loss_fn = nn.CrossEntropyLoss(weight=weight_t)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)

    ds = TensorDataset(torch.from_numpy(train_x), torch.from_numpy(train_y))
    gen = torch.Generator()
    gen.manual_seed(run_seed)
    loader = DataLoader(ds, batch_size=BATCH_SIZE, shuffle=True, generator=gen)

    model.train()
    for _ in range(int(epochs)):
        for xb, yb in loader:
            xb = xb.to(device)
            yb = yb.to(device)
            opt.zero_grad(set_to_none=True)
            loss = loss_fn(model(xb), yb)
            loss.backward()
            opt.step()

    model.eval()
    probs = []
    with torch.no_grad():
        for start in range(0, len(val_x), 512):
            xb = torch.from_numpy(val_x[start:start+512]).to(device)
            p = torch.softmax(model(xb), dim=1).detach().cpu().numpy()
            probs.append(p)
    probs = np.concatenate(probs, axis=0)
    return probs

def standardize_train_val(train_x, val_x):
    eps = 1e-6
    train_x = np.asarray(train_x, dtype=np.float32)
    val_x = np.asarray(val_x, dtype=np.float32)
    mu = train_x.mean(axis=0, keepdims=True)
    sd = train_x.std(axis=0, keepdims=True) + eps
    return (train_x - mu) / sd, (val_x - mu) / sd

def build_eeg_preprocessed_features(path):
    print("BUILDING_EEG_WINDOW_CHANNEL_ZSCORE_SUMMARY_FEATURES")
    x = np.load(path, mmap_mode="r")
    n = x.shape[0]
    eps = 1e-6
    abs_parts = []
    ptp_parts = []
    diffstd_parts = []
    chunk = 256
    for start in range(0, n, chunk):
        stop = min(n, start + chunk)
        xb = np.asarray(x[start:stop], dtype=np.float32)
        mu = xb.mean(axis=2, keepdims=True)
        sd = xb.std(axis=2, keepdims=True) + eps
        z = (xb - mu) / sd
        abs_parts.append(np.asarray(np.abs(z).mean(axis=2), dtype=np.float32))
        ptp_parts.append(np.asarray(z.max(axis=2) - z.min(axis=2), dtype=np.float32))
        diffstd_parts.append(np.asarray(np.diff(z, axis=2).std(axis=2), dtype=np.float32))
    return np.concatenate([
        np.concatenate(abs_parts, axis=0),
        np.concatenate(ptp_parts, axis=0),
        np.concatenate(diffstd_parts, axis=0),
    ], axis=1).astype(np.float32)

def build_emg_preprocessed_features(path):
    print("BUILDING_EMG_SIGNED_LOG1P_FEATURES")
    x = np.asarray(np.load(path, mmap_mode="r"), dtype=np.float32)
    return (np.sign(x) * np.log1p(np.abs(x))).astype(np.float32)

def summarize_aggregate(runs):
    out = []
    keys = ["final_macro_f1", "final_balanced_accuracy", "final_accuracy", "majority_accuracy"]
    for task in TASKS:
        rows = [r for r in runs if r["task"] == task]
        if not rows:
            continue
        item = {"task": task, "recipe": RECIPE, "n_runs": len(rows)}
        for key in keys:
            vals = [float(r[key]) for r in rows if key in r and r[key] is not None]
            item[key] = {
                "mean": float(np.mean(vals)) if vals else None,
                "std": float(np.std(vals)) if vals else None,
                "min": float(np.min(vals)) if vals else None,
                "max": float(np.max(vals)) if vals else None,
            }
        item["one_class_pred_runs"] = int(sum(1 for r in rows if r.get("one_class_pred")))
        out.append(item)
    if runs:
        for key in keys:
            vals = [float(r[key]) for r in runs if key in r and r[key] is not None]
            if vals:
                out.append({
                    "task": "ALL",
                    "recipe": RECIPE,
                    "n_runs": len(runs),
                    key: {
                        "mean": float(np.mean(vals)),
                        "std": float(np.std(vals)),
                        "min": float(np.min(vals)),
                        "max": float(np.max(vals)),
                    },
                })
    return out

def aggregate_by_task(runs):
    out = {}
    for task in TASKS:
        rows = [r for r in runs if r.get("task") == task and r.get("recipe") == RECIPE]
        if not rows:
            rows = [r for r in runs if r.get("task") == task]
        if rows:
            out[task] = {
                "n_runs": len(rows),
                "macro_f1_mean": float(np.mean([float(r["final_macro_f1"]) for r in rows])),
                "bal_acc_mean": float(np.mean([float(r["final_balanced_accuracy"]) for r in rows])),
            }
    if out:
        out["ALL"] = {
            "n_runs": sum(v["n_runs"] for k, v in out.items() if k != "ALL"),
            "macro_f1_mean": float(np.mean([v["macro_f1_mean"] for k, v in out.items() if k != "ALL"])),
            "bal_acc_mean": float(np.mean([v["bal_acc_mean"] for k, v in out.items() if k != "ALL"])),
        }
    return out

def extract_runs(path):
    data = load_json(path)
    if isinstance(data.get("runs"), list):
        return data["runs"]
    if isinstance(data.get("results"), list):
        return data["results"]
    return []

def fmt(x, digits=4):
    try:
        if x is None or (isinstance(x, float) and math.isnan(x)):
            return "NA"
        return f"{float(x):.{digits}f}"
    except Exception:
        return str(x)

def run_modality(modality, features, index_df):
    out = OUTS[modality]
    subjects_all = pd.to_numeric(index_df["subject_id"], errors="coerce").to_numpy()
    prediction_rows = []
    run_rows = []
    label_audit = {}
    run_id = 0

    for task in TASKS:
        labels, valid_mask, rating_col, subject_details = subject_q33_labels(index_df, task)
        valid_subjects = sorted(set(int(s) for s, ok in zip(subjects_all, valid_mask) if ok and not pd.isna(s)))
        folds = make_folds(valid_subjects, FOLDS, SEED)
        label_audit[task] = {
            "rating_col": rating_col,
            "valid_subjects": len(valid_subjects),
            "valid_samples": int(valid_mask.sum()),
            "class0": int(np.sum(labels[valid_mask] == 0)),
            "class1": int(np.sum(labels[valid_mask] == 1)),
            "empty_or_excluded_subjects": int(len(set(int(s) for s in subjects_all if not pd.isna(s))) - len(valid_subjects)),
        }

        for fold_id, val_subjects in folds.items():
            run_id += 1
            val_set = set(val_subjects)
            is_val = np.array([int(s) in val_set if not pd.isna(s) else False for s in subjects_all], dtype=bool)
            train_mask = valid_mask & (~is_val)
            val_mask = valid_mask & is_val

            train_x_raw = features[train_mask]
            val_x_raw = features[val_mask]
            train_x, val_x = standardize_train_val(train_x_raw, val_x_raw)

            train_y = labels[train_mask].astype(int)
            val_y = labels[val_mask].astype(int)
            val_indices = np.where(val_mask)[0]

            probs = train_predict(train_x, train_y, val_x, EPOCHS[modality], SEED, modality, task, fold_id)
            prob1 = probs[:, 1]
            metrics, y_pred = compute_metrics(val_y, prob1)

            run = {
                "run_id": run_id,
                "modality": modality,
                "task": task,
                "recipe": RECIPE,
                "fold_id": fold_id,
                "seed": SEED,
                "formulation": FORMULATION,
                "preprocessing_candidate": out["candidate"],
                "preprocessing_description": out["description"],
                "epochs": EPOCHS[modality],
                "feature_dim": int(train_x.shape[1]),
                "train_subjects": sorted(int(s) for s in set(valid_subjects) - val_set),
                "val_subjects": sorted(int(s) for s in val_subjects),
                "n_train": int(len(train_y)),
                "n_val": int(len(val_y)),
                "train_class0": int(np.sum(train_y == 0)),
                "train_class1": int(np.sum(train_y == 1)),
                "val_class0": int(np.sum(val_y == 0)),
                "val_class1": int(np.sum(val_y == 1)),
                "scaling_policy": "fit standard scaler on train fold only; apply to validation fold",
                **metrics,
            }
            run_rows.append(run)

            for idx, yt, yp, p0, p1 in zip(val_indices, val_y, y_pred, probs[:, 0], probs[:, 1]):
                row = {
                    "modality": modality,
                    "task": task,
                    "recipe": RECIPE,
                    "fold_id": fold_id,
                    "seed": SEED,
                    "run_id": run_id,
                    "row_index": int(idx),
                    "subject_id": int(subjects_all[idx]),
                    "formulation": FORMULATION,
                    "preprocessing_candidate": out["candidate"],
                    "y_true": int(yt),
                    "y_pred": int(yp),
                    "prob0": float(p0),
                    "prob1": float(p1),
                    "is_correct": int(int(yt) == int(yp)),
                }
                prediction_rows.append(row)

            print(
                json.dumps({
                    "run_id": run_id,
                    "modality": modality,
                    "task": task,
                    "fold": fold_id,
                    "final_macro_f1": metrics["final_macro_f1"],
                    "final_balanced_accuracy": metrics["final_balanced_accuracy"],
                    "final_accuracy": metrics["final_accuracy"],
                    "one_class_pred": metrics["one_class_pred"],
                    "n_train": int(len(train_y)),
                    "n_val": int(len(val_y)),
                }, sort_keys=True)
            )

    fieldnames = [
        "modality", "task", "recipe", "fold_id", "seed", "run_id", "row_index",
        "subject_id", "formulation", "preprocessing_candidate",
        "y_true", "y_pred", "prob0", "prob1", "is_correct",
    ]
    with out["pred"].open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(prediction_rows)

    data = {
        "status": "primary_matrix_complete",
        "created_or_updated_utc": NOW,
        "objective": str(OBJECTIVE_MD),
        "objective_json": str(OBJECTIVE_JSON),
        "review": str(REVIEW_MD),
        "modality": modality,
        "formulation": FORMULATION,
        "preprocessing_candidate": out["candidate"],
        "preprocessing_description": out["description"],
        "recipe": RECIPE,
        "tasks": TASKS,
        "folds": FOLDS,
        "seed": SEED,
        "planned_runs": 12,
        "completed_runs": len(run_rows),
        "label_audit": label_audit,
        "runs": run_rows,
        "aggregate": summarize_aggregate(run_rows),
        "predictions_csv": str(out["pred"]),
    }
    out["json"].write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    agg = aggregate_by_task(run_rows)
    md = []
    md.append(f"# I-DARE Subject-relative Preprocessed Minimal {modality} Primary")
    md.append("")
    md.append("## Status")
    md.append("")
    md.append("Primary first-pass matrix complete.")
    md.append("")
    md.append(f"Generated UTC: `{NOW}`")
    md.append("")
    md.append("## Setup")
    md.append("")
    md.append(f"- Formulation: `{FORMULATION}`")
    md.append(f"- Preprocessing: `{out['candidate']}`")
    md.append(f"- Recipe: `{RECIPE}`")
    md.append(f"- Runs: `{len(run_rows)}`")
    md.append("")
    md.append("## Aggregate Results")
    md.append("")
    md.append("| Task | Runs | Mean macro F1 | Mean balanced accuracy |")
    md.append("|---|---:|---:|---:|")
    for task in ["valence", "arousal", "ALL"]:
        if task in agg:
            md.append(f"| {task} | {agg[task]['n_runs']} | {fmt(agg[task]['macro_f1_mean'])} | {fmt(agg[task]['bal_acc_mean'])} |")
    md.append("")
    md.append("## Output Files")
    md.append("")
    md.append(f"- `{out['json']}`")
    md.append(f"- `{out['pred']}`")
    md.append("")
    out["md"].write_text("\n".join(md), encoding="utf-8")

    return run_rows, prediction_rows, agg, label_audit

objective = load_json(OBJECTIVE_JSON)
pre_report = load_json(PREPROCESSING_REPORT_JSON)

eeg_index = pd.read_csv(EEG_INDEX)
emg_index = pd.read_csv(EMG_INDEX)

eeg_features = build_eeg_preprocessed_features(EEG_NPY)
emg_features = build_emg_preprocessed_features(EMG_NPY)

print("===== RUN: EEG preprocessed minimal =====")
eeg_runs, eeg_preds, eeg_agg, eeg_label_audit = run_modality("EEG", eeg_features, eeg_index)
print("===== RUN: EMG preprocessed minimal =====")
emg_runs, emg_preds, emg_agg, emg_label_audit = run_modality("EMG", emg_features, emg_index)

all_runs = eeg_runs + emg_runs
if len(all_runs) != 24:
    raise SystemExit(f"ERROR: expected 24 runs, got {len(all_runs)}")

one_class_by_modality_task = {}
for modality in ["EEG", "EMG"]:
    for task in TASKS:
        rows = [r for r in all_runs if r["modality"] == modality and r["task"] == task]
        one_class_by_modality_task[f"{modality}_{task}"] = int(sum(1 for r in rows if r.get("one_class_pred")))

previous_eeg_runs = extract_runs(DOCS / "idare_subject_relative_minimal_eeg_primary.json")
previous_emg_runs = extract_runs(DOCS / "idare_subject_relative_minimal_emg_primary.json")
global_eeg_runs = extract_runs(DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary.json")
global_emg_runs = extract_runs(DOCS / "idare_broader_eval_emg_feature_only_primary.json")

previous_agg = {
    "EEG": aggregate_by_task(previous_eeg_runs),
    "EMG": aggregate_by_task(previous_emg_runs),
}
global_agg = {
    "EEG": aggregate_by_task([r for r in global_eeg_runs if r.get("recipe") == RECIPE]),
    "EMG": aggregate_by_task([r for r in global_emg_runs if r.get("recipe") == RECIPE]),
}
current_agg = {
    "EEG": aggregate_by_task(eeg_runs),
    "EMG": aggregate_by_task(emg_runs),
}

comparison_rows = []
for modality in ["EEG", "EMG"]:
    for task in ["valence", "arousal", "ALL"]:
        cur = current_agg.get(modality, {}).get(task)
        prev = previous_agg.get(modality, {}).get(task)
        glob = global_agg.get(modality, {}).get(task)
        if not cur:
            continue
        comparison_rows.append({
            "modality": modality,
            "task": task,
            "current_macro_f1": cur.get("macro_f1_mean"),
            "previous_subject_relative_macro_f1": None if not prev else prev.get("macro_f1_mean"),
            "delta_vs_previous_subject_relative": None if not prev else cur.get("macro_f1_mean") - prev.get("macro_f1_mean"),
            "global_label_macro_f1_reference": None if not glob else glob.get("macro_f1_mean"),
            "delta_vs_global_label_reference": None if not glob else cur.get("macro_f1_mean") - glob.get("macro_f1_mean"),
            "current_balanced_accuracy": cur.get("bal_acc_mean"),
            "previous_subject_relative_bal_acc": None if not prev else prev.get("bal_acc_mean"),
            "delta_bal_acc_vs_previous_subject_relative": None if not prev else cur.get("bal_acc_mean") - prev.get("bal_acc_mean"),
            "global_label_bal_acc_reference": None if not glob else glob.get("bal_acc_mean"),
            "delta_bal_acc_vs_global_label_reference": None if not glob else cur.get("bal_acc_mean") - glob.get("bal_acc_mean"),
        })

all_current_macro = [row["current_macro_f1"] for row in comparison_rows if row["task"] == "ALL"]
all_prev_delta = [row["delta_vs_previous_subject_relative"] for row in comparison_rows if row["task"] == "ALL" and row["delta_vs_previous_subject_relative"] is not None]
mean_macro_all = float(np.mean(all_current_macro)) if all_current_macro else None
mean_delta_prev_all = float(np.mean(all_prev_delta)) if all_prev_delta else None
max_one_class = max(one_class_by_modality_task.values()) if one_class_by_modality_task else 0

if mean_delta_prev_all is not None and mean_delta_prev_all >= 0.015 and max_one_class <= 1:
    diagnosis = "preprocessed_subject_relative_first_pass_promising"
    recommended_next_objective = "preprocessed_balanced_sampler_second_pass_objective"
elif mean_delta_prev_all is not None and mean_delta_prev_all >= 0.0 and max_one_class <= 1:
    diagnosis = "preprocessed_subject_relative_first_pass_mixed"
    recommended_next_objective = "subject_relative_preprocessed_training_review_closeout"
else:
    diagnosis = "preprocessed_subject_relative_first_pass_not_sufficient"
    recommended_next_objective = "subject_relative_feature_engineering_objective"

report = {
    "status": "complete_pending_review",
    "created_or_updated_utc": NOW,
    "objective": str(OBJECTIVE_MD),
    "objective_json": str(OBJECTIVE_JSON),
    "review": str(REVIEW_MD),
    "evidence_level": "24-run minimal diagnostic training; not final LOSO performance",
    "formulation": FORMULATION,
    "planned_runs": 24,
    "completed_runs": len(all_runs),
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next_objective,
    "mean_macro_f1_all_modalities": mean_macro_all,
    "mean_delta_macro_f1_vs_previous_subject_relative_all_modalities": mean_delta_prev_all,
    "one_class_prediction_counts_by_modality_task": one_class_by_modality_task,
    "current_aggregate": current_agg,
    "previous_subject_relative_aggregate": previous_agg,
    "global_label_reference_aggregate": global_agg,
    "comparison_rows": comparison_rows,
    "outputs": {
        "eeg_json": str(OUTS["EEG"]["json"]),
        "eeg_md": str(OUTS["EEG"]["md"]),
        "eeg_predictions_csv": str(OUTS["EEG"]["pred"]),
        "emg_json": str(OUTS["EMG"]["json"]),
        "emg_md": str(OUTS["EMG"]["md"]),
        "emg_predictions_csv": str(OUTS["EMG"]["pred"]),
    },
    "not_authorized": objective.get("not_authorized", []),
    "next_allowed_step": "Human review / closeout before optional second pass, feature engineering, or stopping.",
}
REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = []
md.append("# I-DARE Subject-relative Preprocessed Minimal Training Report")
md.append("")
md.append("## Status")
md.append("")
md.append("24-run minimal subject-relative preprocessed first pass complete; pending human review.")
md.append("")
md.append(f"Generated UTC: `{NOW}`")
md.append("")
md.append("## Run Matrix")
md.append("")
md.append("- Modalities: `EEG`, `EMG`")
md.append("- Tasks: `valence`, `arousal`")
md.append("- Folds: `6`")
md.append("- Seed: `11`")
md.append("- Recipe: `ce_class_weighted`")
md.append("- Formulation: `subject_top_bottom_quantile_q33`")
md.append("- EEG preprocessing: `eeg_window_channel_zscore_train_standard_scaled`")
md.append("- EMG preprocessing: `emg_signed_log1p_train_standard_scaled`")
md.append("")
md.append("## Aggregate Comparison")
md.append("")
md.append("| Modality | Task | Current macro F1 | Previous subject-relative macro F1 | Delta vs previous | Global-label reference macro F1 | Delta vs global ref | Current balanced acc |")
md.append("|---|---|---:|---:|---:|---:|---:|---:|")
for row in comparison_rows:
    md.append(
        f"| {row['modality']} | {row['task']} | {fmt(row['current_macro_f1'])} | "
        f"{fmt(row['previous_subject_relative_macro_f1'])} | {fmt(row['delta_vs_previous_subject_relative'])} | "
        f"{fmt(row['global_label_macro_f1_reference'])} | {fmt(row['delta_vs_global_label_reference'])} | "
        f"{fmt(row['current_balanced_accuracy'])} |"
    )
md.append("")
md.append("## Diagnosis")
md.append("")
md.append(f"- Diagnosis: `{diagnosis}`")
md.append(f"- Recommended next objective: `{recommended_next_objective}`")
md.append(f"- Mean macro-F1 across modality-level ALL rows: `{fmt(mean_macro_all)}`")
md.append(f"- Mean delta macro-F1 vs previous subject-relative minimal run: `{fmt(mean_delta_prev_all)}`")
md.append(f"- Max one-class prediction count per modality/task: `{max_one_class}`")
md.append("")
md.append("## Output Files")
md.append("")
for item in report["outputs"].values():
    md.append(f"- `{item}`")
md.append(f"- `{REPORT_JSON}`")
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

project_md = PROJECT_MD.read_text(encoding="utf-8")
row = "| I-DARE minimal subject-relative preprocessed training report | 24-run preprocessed subject-relative diagnostic training complete; pending human review | yes | `docs/idare_subject_relative_preprocessed_minimal_training_report.md` | Human review / closeout before optional second pass or next fix objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search; mainline change. |"
if "I-DARE minimal subject-relative preprocessed training report" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE minimal subject-relative preprocessed training objective |"):
            out.append(row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert roadmap row")
    project_md = "\n".join(out) + "\n"

bullet = f"- Minimal subject-relative preprocessed training is complete in `docs/idare_subject_relative_preprocessed_minimal_training_report.md`; diagnosis is `{diagnosis}` and next work is human review/closeout."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: project status marker not found")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = load_json(PROJECT_JSON)
decisions = project_json.setdefault("decisions", {})
decisions["idare_minimal_subject_relative_preprocessed_training_report"] = {
    "status": "complete_pending_review",
    "evidence": str(REPORT_MD),
    "evidence_json": str(REPORT_JSON),
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next_objective,
    "planned_runs": 24,
    "completed_runs": len(all_runs),
    "not_authorized": report["not_authorized"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_PREPROCESSED_MINIMAL_TRAINING_REPORT_WRITTEN")
print(REPORT_MD)
print(REPORT_JSON)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next_objective)
PY
echo

echo "===== 4) validate outputs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path

paths = [
    Path("docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json"),
    Path("docs/idare_subject_relative_preprocessed_minimal_emg_primary.json"),
    Path("docs/idare_subject_relative_preprocessed_minimal_training_report.json"),
    Path("docs/project_status_current.json"),
]
for p in paths:
    data = json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)
    if p.name.endswith("_primary.json") and len(data.get("runs", [])) != 12:
        raise SystemExit(f"ERROR: {p} expected 12 runs")

for p in [
    Path("docs/idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv"),
    Path("docs/idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv"),
]:
    with p.open(newline="", encoding="utf-8") as f:
        n = sum(1 for _ in csv.DictReader(f))
    print(p.name, "rows=", n)
    if n <= 0:
        raise SystemExit(f"ERROR: empty predictions {p}")

report = json.loads(Path("docs/idare_subject_relative_preprocessed_minimal_training_report.json").read_text(encoding="utf-8"))
if report.get("completed_runs") != 24:
    raise SystemExit("ERROR: completed_runs is not 24")
if not report.get("recommended_next_objective"):
    raise SystemExit("ERROR: missing recommended_next_objective")
print("diagnosis=", report.get("diagnosis"))
print("recommended_next_objective=", report.get("recommended_next_objective"))
PY

grep -n "## Status\|## Run Matrix\|## Aggregate Comparison\|## Diagnosis\|## Next Allowed Step" docs/idare_subject_relative_preprocessed_minimal_training_report.md
grep -n "minimal subject-relative preprocessed training report" docs/project_status_current.md
echo

echo "===== 5) file list ====="
ls -lh \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.md \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.md \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv \
  docs/idare_subject_relative_preprocessed_minimal_training_report.md \
  docs/idare_subject_relative_preprocessed_minimal_training_report.json \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push first-pass outputs ====="
git add \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.md \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.md \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary.json \
  docs/idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv \
  docs/idare_subject_relative_preprocessed_minimal_training_report.md \
  docs/idare_subject_relative_preprocessed_minimal_training_report.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "exp: run I-DARE minimal subject-relative preprocessed training"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_minimal_subject_relative_preprocessed_training_run.log"
