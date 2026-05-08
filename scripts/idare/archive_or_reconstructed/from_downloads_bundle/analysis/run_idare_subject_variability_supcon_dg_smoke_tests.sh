#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start SupCon/DG smoke tests ====="
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
import numpy as np
import pandas as pd
import torch
print("torch_cuda_available=", torch.cuda.is_available())
print("OK_IMPORTS")
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repository is not clean. Commit/stash changes before running smoke tests." >&2
  git status --short --branch >&2
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required inputs ====="
ls -lh \
  .cache/idare_eeg_cache_index_baseline_corrected.csv \
  .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy \
  .cache/idare_emg_feature_cache_index.csv \
  .cache/idare_emg_features.npy \
  docs/idare_subject_variability_supcon_dg_design_spec.md \
  docs/idare_subject_variability_supcon_dg_design_spec.json \
  docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv \
  docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv \
  docs/idare_subject_variability_supcon_dg_smoke_test_plan.csv \
  docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md \
  docs/idare_subject_variability_supcon_dg_smoke_tests_objective.json \
  docs/idare_subject_variability_supcon_dg_design_spec_review_status.md \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 3) remove stale outputs and run smoke tests ====="
rm -f \
  docs/idare_subject_variability_supcon_dg_smoke_tests_report.md \
  docs/idare_subject_variability_supcon_dg_smoke_tests_report.json \
  docs/idare_subject_variability_supcon_dg_pair_sampler_audit.csv \
  docs/idare_subject_variability_supcon_dg_loss_trace_summary.csv \
  docs/idare_subject_variability_supcon_dg_embedding_diagnostic_summary.csv

"$PY" - <<'PY'
import csv
import json
import math
import os
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn
import torch.nn.functional as F

DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

OBJECTIVE_JSON = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_objective.json"
OBJECTIVE_MD = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_objective.md"
DESIGN_MD = DOCS / "idare_subject_variability_supcon_dg_design_spec.md"
DESIGN_JSON = DOCS / "idare_subject_variability_supcon_dg_design_spec.json"
DESIGN_REVIEW_MD = DOCS / "idare_subject_variability_supcon_dg_design_spec_review_status.md"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

REPORT_MD = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_report.md"
REPORT_JSON = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_report.json"
PAIR_AUDIT_CSV = DOCS / "idare_subject_variability_supcon_dg_pair_sampler_audit.csv"
LOSS_CSV = DOCS / "idare_subject_variability_supcon_dg_loss_trace_summary.csv"
EMBED_CSV = DOCS / "idare_subject_variability_supcon_dg_embedding_diagnostic_summary.csv"

EEG_INDEX = Path(".cache/idare_eeg_cache_index_baseline_corrected.csv")
EEG_NPY = Path(".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy")
EMG_INDEX = Path(".cache/idare_emg_feature_cache_index.csv")
EMG_NPY = Path(".cache/idare_emg_features.npy")

for p in [
    OBJECTIVE_JSON, OBJECTIVE_MD, DESIGN_MD, DESIGN_JSON, DESIGN_REVIEW_MD,
    PROJECT_MD, PROJECT_JSON, EEG_INDEX, EEG_NPY, EMG_INDEX, EMG_NPY
]:
    if not p.exists():
        raise SystemExit(f"ERROR: missing required input: {p}")

objective = json.loads(OBJECTIVE_JSON.read_text(encoding="utf-8"))
if objective.get("authorized_scope", {}).get("training_authorized") is not False:
    raise SystemExit("ERROR: objective unexpectedly authorizes training")
if objective.get("authorized_scope", {}).get("smoke_tests_authorized") is not True:
    raise SystemExit("ERROR: smoke tests not authorized in objective")

SEED = 11
rng_global = np.random.default_rng(SEED)
random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TASKS = ["valence", "arousal"]
MODALITIES = ["EEG", "EMG"]
FOLDS = 6

def find_col(df: pd.DataFrame, task: str) -> str:
    candidates = [
        f"{task}_score",
        task,
        f"{task}_rating",
        f"{task}_label_source",
        f"{task}_raw",
    ]
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in df.columns:
            return cand
        if cand.lower() in lower:
            return lower[cand.lower()]
    contains = [c for c in df.columns if task.lower() in c.lower() and ("score" in c.lower() or "rating" in c.lower())]
    if contains:
        return contains[0]
    raise SystemExit(f"ERROR: could not find rating column for task={task}; columns={list(df.columns)[:40]}")

def find_subject_col(df: pd.DataFrame) -> str:
    for c in ["subject_id", "subject", "participant_id", "participant"]:
        if c in df.columns:
            return c
    contains = [c for c in df.columns if "subject" in c.lower()]
    if contains:
        return contains[0]
    raise SystemExit("ERROR: could not find subject column")

def add_subject_relative_q33_labels(df_in: pd.DataFrame, task: str) -> pd.DataFrame:
    df = df_in.copy()
    subj_col = find_subject_col(df)
    rating_col = find_col(df, task)
    label_col = f"{task}_subject_q33_label"
    df[label_col] = np.nan
    for sid, group in df.groupby(subj_col, sort=True):
        vals = pd.to_numeric(group[rating_col], errors="coerce")
        vals = vals.dropna()
        if len(vals) < 6:
            continue
        low_thr = float(vals.quantile(1.0 / 3.0))
        high_thr = float(vals.quantile(2.0 / 3.0))
        if not np.isfinite(low_thr) or not np.isfinite(high_thr) or low_thr >= high_thr:
            continue
        idx = group.index
        raw = pd.to_numeric(df.loc[idx, rating_col], errors="coerce")
        low_idx = idx[raw <= low_thr]
        high_idx = idx[raw >= high_thr]
        df.loc[low_idx, label_col] = 0
        df.loc[high_idx, label_col] = 1
    df[label_col] = df[label_col].astype("float")
    df["_subject_id_int"] = pd.to_numeric(df[subj_col], errors="coerce").astype("Int64")
    df["_row_id"] = np.arange(len(df), dtype=int)
    return df

def make_fold_subjects(subjects: list[int], fold_id: int = 1, seed: int = 11) -> list[int]:
    arr = np.asarray(sorted(set(int(s) for s in subjects)), dtype=int)
    rng = np.random.default_rng(int(seed))
    rng.shuffle(arr)
    chunks = np.array_split(arr, FOLDS)
    return sorted(int(x) for x in chunks[fold_id - 1].tolist())

def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    acc = float((y_true == y_pred).mean()) if len(y_true) else float("nan")
    f1s = []
    recalls = []
    for cls in [0, 1]:
        tp = int(((y_true == cls) & (y_pred == cls)).sum())
        fp = int(((y_true != cls) & (y_pred == cls)).sum())
        fn = int(((y_true == cls) & (y_pred != cls)).sum())
        denom_p = tp + fp
        denom_r = tp + fn
        precision = tp / denom_p if denom_p else 0.0
        recall = tp / denom_r if denom_r else 0.0
        recalls.append(recall)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        f1s.append(f1)
    return {
        "accuracy": acc,
        "balanced_accuracy": float(np.mean(recalls)),
        "macro_f1": float(np.mean(f1s)),
    }

def class_counts(y: np.ndarray) -> dict[str, int]:
    values, counts = np.unique(np.asarray(y).astype(int), return_counts=True)
    return {str(int(v)): int(c) for v, c in zip(values, counts)}

def safe_float(x: Any) -> float:
    try:
        y = float(x)
        if math.isfinite(y):
            return y
    except Exception:
        pass
    return float("nan")

class TinySupConNet(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64, embed_dim: int = 24):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.projector = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, embed_dim),
        )
        self.classifier = nn.Linear(hidden_dim, 2)

    def forward(self, x):
        h = self.encoder(x)
        z = F.normalize(self.projector(h), dim=1)
        logits = self.classifier(h)
        return h, z, logits

def supervised_contrastive_loss(z: torch.Tensor, y: torch.Tensor, temperature: float = 0.2) -> torch.Tensor:
    n = z.shape[0]
    if n < 2:
        return z.new_tensor(0.0)
    y = y.view(-1, 1)
    mask = torch.eq(y, y.T).float().to(z.device)
    logits = torch.matmul(z, z.T) / temperature
    logits = logits - torch.max(logits, dim=1, keepdim=True)[0].detach()
    logits_mask = torch.ones_like(mask) - torch.eye(n, device=z.device)
    mask = mask * logits_mask
    exp_logits = torch.exp(logits) * logits_mask
    log_prob = logits - torch.log(exp_logits.sum(dim=1, keepdim=True).clamp_min(1e-12))
    positives = mask.sum(dim=1)
    valid = positives > 0
    if valid.sum() == 0:
        return z.new_tensor(0.0)
    mean_log_prob_pos = (mask * log_prob).sum(dim=1)[valid] / positives[valid].clamp_min(1.0)
    return -mean_log_prob_pos.mean()

def balanced_batch_indices(y: np.ndarray, batch_size: int, rng: np.random.Generator) -> np.ndarray:
    y = np.asarray(y).astype(int)
    idx0 = np.flatnonzero(y == 0)
    idx1 = np.flatnonzero(y == 1)
    if len(idx0) == 0 or len(idx1) == 0:
        return rng.choice(np.arange(len(y)), size=min(batch_size, len(y)), replace=len(y) < batch_size)
    half = batch_size // 2
    a = rng.choice(idx0, size=half, replace=len(idx0) < half)
    b = rng.choice(idx1, size=batch_size - half, replace=len(idx1) < (batch_size - half))
    out = np.concatenate([a, b])
    rng.shuffle(out)
    return out

def select_balanced_subset(y: np.ndarray, max_per_class: int, rng: np.random.Generator) -> np.ndarray:
    y = np.asarray(y).astype(int)
    parts = []
    for cls in [0, 1]:
        idx = np.flatnonzero(y == cls)
        if len(idx) == 0:
            continue
        take = min(max_per_class, len(idx))
        parts.append(rng.choice(idx, size=take, replace=False))
    if not parts:
        return np.arange(min(len(y), max_per_class * 2))
    out = np.concatenate(parts)
    rng.shuffle(out)
    return out

def standardize_train_only(X_train: np.ndarray, X_val: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mu = X_train.mean(axis=0, keepdims=True)
    sig = X_train.std(axis=0, keepdims=True)
    sig[sig < 1e-6] = 1.0
    return ((X_train - mu) / sig).astype(np.float32), ((X_val - mu) / sig).astype(np.float32)

def build_modality_task_data(modality: str, task: str) -> dict[str, Any]:
    if modality == "EEG":
        index_path = EEG_INDEX
        data_path = EEG_NPY
    else:
        index_path = EMG_INDEX
        data_path = EMG_NPY

    df0 = pd.read_csv(index_path)
    df = add_subject_relative_q33_labels(df0, task)
    label_col = f"{task}_subject_q33_label"
    valid = df[label_col].notna() & df["_subject_id_int"].notna()
    dfv = df.loc[valid].copy()
    dfv[label_col] = dfv[label_col].astype(int)
    subjects = sorted(int(x) for x in dfv["_subject_id_int"].dropna().unique().tolist())
    val_subjects = make_fold_subjects(subjects, fold_id=1, seed=SEED)
    train_mask = ~dfv["_subject_id_int"].astype(int).isin(val_subjects)
    val_mask = dfv["_subject_id_int"].astype(int).isin(val_subjects)
    train_rows = dfv.loc[train_mask, "_row_id"].astype(int).to_numpy()
    val_rows = dfv.loc[val_mask, "_row_id"].astype(int).to_numpy()
    y_train = dfv.loc[train_mask, label_col].astype(int).to_numpy()
    y_val = dfv.loc[val_mask, label_col].astype(int).to_numpy()
    train_subjects = dfv.loc[train_mask, "_subject_id_int"].astype(int).to_numpy()
    val_subjects_arr = dfv.loc[val_mask, "_subject_id_int"].astype(int).to_numpy()

    if modality == "EEG":
        arr = np.load(data_path, mmap_mode="r")
        Xtr_raw = np.asarray(arr[train_rows], dtype=np.float32)
        Xva_raw = np.asarray(arr[val_rows], dtype=np.float32)
        X_train = np.concatenate(
            [
                Xtr_raw.mean(axis=2),
                Xtr_raw.std(axis=2),
                np.log1p(np.var(Xtr_raw, axis=2)),
            ],
            axis=1,
        ).astype(np.float32)
        X_val = np.concatenate(
            [
                Xva_raw.mean(axis=2),
                Xva_raw.std(axis=2),
                np.log1p(np.var(Xva_raw, axis=2)),
            ],
            axis=1,
        ).astype(np.float32)
        feature_kind = "eeg_channel_mean_std_logvar"
    else:
        arr = np.load(data_path, mmap_mode="r")
        X_train = np.asarray(arr[train_rows], dtype=np.float32)
        X_val = np.asarray(arr[val_rows], dtype=np.float32)
        X_train = np.sign(X_train) * np.log1p(np.abs(X_train))
        X_val = np.sign(X_val) * np.log1p(np.abs(X_val))
        feature_kind = "emg_signed_log1p"

    X_train, X_val = standardize_train_only(X_train, X_val)
    return {
        "modality": modality,
        "task": task,
        "feature_kind": feature_kind,
        "train_rows": train_rows,
        "val_rows": val_rows,
        "X_train": X_train,
        "X_val": X_val,
        "y_train": y_train,
        "y_val": y_val,
        "train_subjects": train_subjects,
        "val_subjects": val_subjects_arr,
        "val_subject_list": sorted(set(int(x) for x in val_subjects_arr.tolist())),
        "train_class_counts": class_counts(y_train),
        "val_class_counts": class_counts(y_val),
    }

def audit_pair_sampler(data: dict[str, Any], n_batches: int = 20, batch_size: int = 64) -> dict[str, Any]:
    y = data["y_train"]
    s = data["train_subjects"]
    rng = np.random.default_rng(SEED + 101)
    rows = []
    bad_batches = 0
    coverage_values = []
    subject_counts = []
    for b in range(n_batches):
        idx = balanced_batch_indices(y, batch_size=batch_size, rng=rng)
        by = y[idx]
        bs = s[idx]
        positive_available = []
        for i in range(len(idx)):
            same_class = by == by[i]
            different_subject = bs != bs[i]
            positive_available.append(bool(np.any(same_class & different_subject)))
        coverage = float(np.mean(positive_available)) if positive_available else 0.0
        n_subjects = int(len(set(int(x) for x in bs.tolist())))
        n_classes = int(len(set(int(x) for x in by.tolist())))
        coverage_values.append(coverage)
        subject_counts.append(n_subjects)
        if n_classes < 2 or n_subjects < 4 or coverage < 0.95:
            bad_batches += 1
    avg_cov = float(np.mean(coverage_values)) if coverage_values else 0.0
    min_cov = float(np.min(coverage_values)) if coverage_values else 0.0
    min_subjects = int(np.min(subject_counts)) if subject_counts else 0
    passed = bad_batches == 0 and avg_cov >= 0.95 and min_subjects >= 4
    return {
        "test": "pair_sampler_integrity_smoke",
        "modality": data["modality"],
        "task": data["task"],
        "feature_kind": data["feature_kind"],
        "n_batches": n_batches,
        "batch_size": batch_size,
        "avg_positive_pair_coverage": avg_cov,
        "min_positive_pair_coverage": min_cov,
        "min_subjects_per_batch": min_subjects,
        "bad_batches": bad_batches,
        "passed": bool(passed),
    }

def leakage_guard(data: dict[str, Any]) -> dict[str, Any]:
    train_rows = set(int(x) for x in data["train_rows"].tolist())
    val_rows = set(int(x) for x in data["val_rows"].tolist())
    train_subjects = set(int(x) for x in data["train_subjects"].tolist())
    val_subjects = set(int(x) for x in data["val_subjects"].tolist())
    row_overlap = len(train_rows & val_rows)
    subject_overlap = len(train_subjects & val_subjects)
    train_has_two_classes = len(set(int(x) for x in data["y_train"].tolist())) == 2
    val_has_two_classes = len(set(int(x) for x in data["y_val"].tolist())) == 2
    passed = row_overlap == 0 and subject_overlap == 0 and train_has_two_classes and val_has_two_classes
    return {
        "test": "leakage_guard_smoke",
        "modality": data["modality"],
        "task": data["task"],
        "row_overlap": row_overlap,
        "subject_overlap": subject_overlap,
        "train_has_two_classes": bool(train_has_two_classes),
        "val_has_two_classes": bool(val_has_two_classes),
        "n_train": int(len(data["y_train"])),
        "n_val": int(len(data["y_val"])),
        "train_class_counts": data["train_class_counts"],
        "val_class_counts": data["val_class_counts"],
        "passed": bool(passed),
    }

@dataclass
class TrainResult:
    metrics: dict[str, float]
    loss: dict[str, float]
    embedding: dict[str, float]
    pred_counts: dict[str, int]
    one_class_pred: bool

def train_eval_smoke(
    data: dict[str, Any],
    test_name: str,
    train_mode: str,
    epochs: int,
    batch_size: int = 64,
    supcon_weight: float = 0.10,
    temperature: float = 0.20,
    shuffle_labels: bool = False,
) -> TrainResult:
    rng = np.random.default_rng(SEED + hash((data["modality"], data["task"], test_name)) % 10000)

    X_train = data["X_train"]
    y_train = data["y_train"].copy()
    X_val = data["X_val"]
    y_val = data["y_val"]

    eval_on_train = False
    if train_mode == "micro_overfit":
        subset = select_balanced_subset(y_train, max_per_class=48, rng=rng)
        X_train = X_train[subset]
        y_train = y_train[subset]
        X_val = X_train
        y_val = y_train
        eval_on_train = True

    if shuffle_labels:
        y_train = y_train.copy()
        rng.shuffle(y_train)

    model = TinySupConNet(X_train.shape[1]).to(DEVICE)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

    Xtr = torch.tensor(X_train, dtype=torch.float32, device=DEVICE)
    ytr = torch.tensor(y_train, dtype=torch.long, device=DEVICE)
    Xev = torch.tensor(X_val, dtype=torch.float32, device=DEVICE)

    ce_losses = []
    sc_losses = []
    total_losses = []
    steps_per_epoch = max(4, min(16, int(math.ceil(len(y_train) / max(batch_size, 1)))))
    for ep in range(epochs):
        model.train()
        for _ in range(steps_per_epoch):
            idx_np = balanced_batch_indices(y_train, batch_size=min(batch_size, len(y_train)), rng=rng)
            idx = torch.tensor(idx_np, dtype=torch.long, device=DEVICE)
            xb = Xtr[idx]
            yb = ytr[idx]
            _, z, logits = model(xb)
            ce = F.cross_entropy(logits, yb)
            sc = supervised_contrastive_loss(z, yb, temperature=temperature)
            loss = ce + supcon_weight * sc
            if not torch.isfinite(loss):
                raise RuntimeError(f"non-finite loss in {test_name} {data['modality']} {data['task']}")
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            ce_losses.append(float(ce.detach().cpu()))
            sc_losses.append(float(sc.detach().cpu()))
            total_losses.append(float(loss.detach().cpu()))

    model.eval()
    with torch.no_grad():
        h, z, logits = model(Xev)
        probs = torch.softmax(logits, dim=1)[:, 1].detach().cpu().numpy()
        pred = (probs >= 0.5).astype(int)
        z_np = z.detach().cpu().numpy()
        h_np = h.detach().cpu().numpy()

    m = metrics(y_val, pred)
    pc = class_counts(pred)
    one_class = len(set(int(x) for x in pred.tolist())) < 2

    emb_var = float(np.var(z_np, axis=0).mean()) if z_np.size else 0.0
    norm_mean = float(np.linalg.norm(z_np, axis=1).mean()) if z_np.size else 0.0
    centroids = []
    for cls in [0, 1]:
        if np.any(y_val == cls):
            centroids.append(z_np[y_val == cls].mean(axis=0))
    centroid_distance = float(np.linalg.norm(centroids[0] - centroids[1])) if len(centroids) == 2 else float("nan")

    loss_dict = {
        "ce_first": float(np.mean(ce_losses[:max(1, min(5, len(ce_losses)))])),
        "ce_last": float(np.mean(ce_losses[-max(1, min(5, len(ce_losses))):])),
        "supcon_first": float(np.mean(sc_losses[:max(1, min(5, len(sc_losses)))])),
        "supcon_last": float(np.mean(sc_losses[-max(1, min(5, len(sc_losses))):])),
        "total_first": float(np.mean(total_losses[:max(1, min(5, len(total_losses)))])),
        "total_last": float(np.mean(total_losses[-max(1, min(5, len(total_losses))):])),
        "epochs": int(epochs),
        "steps_per_epoch": int(steps_per_epoch),
        "train_mode": train_mode,
        "shuffle_labels": bool(shuffle_labels),
        "eval_on_train": bool(eval_on_train),
    }
    emb_dict = {
        "embedding_variance_mean": emb_var,
        "embedding_norm_mean": norm_mean,
        "embedding_centroid_distance": centroid_distance,
        "embedding_collapse_flag": bool(emb_var < 1e-5),
    }
    return TrainResult(metrics=m, loss=loss_dict, embedding=emb_dict, pred_counts=pc, one_class_pred=one_class)

datasets = {}
for modality in MODALITIES:
    for task in TASKS:
        print(f"BUILDING_DATA modality={modality} task={task}")
        datasets[(modality, task)] = build_modality_task_data(modality, task)

test_records = []
pair_rows = []
loss_rows = []
embed_rows = []

# Pair sampler and leakage guard for all modality/task combinations.
for (modality, task), data in datasets.items():
    pair = audit_pair_sampler(data)
    pair_rows.append(pair)
    test_records.append({
        "test": pair["test"],
        "modality": modality,
        "task": task,
        "passed": bool(pair["passed"]),
        "summary": f"avg_positive_pair_coverage={pair['avg_positive_pair_coverage']:.3f}; min_subjects_per_batch={pair['min_subjects_per_batch']}",
    })
    print(f"[pair_sampler_integrity_smoke] {modality} {task} coverage={pair['avg_positive_pair_coverage']:.3f} passed={pair['passed']}")

    leak = leakage_guard(data)
    test_records.append({
        "test": leak["test"],
        "modality": modality,
        "task": task,
        "passed": bool(leak["passed"]),
        "summary": f"row_overlap={leak['row_overlap']}; subject_overlap={leak['subject_overlap']}; n_train={leak['n_train']}; n_val={leak['n_val']}",
    })
    print(f"[leakage_guard_smoke] {modality} {task} row_overlap={leak['row_overlap']} subject_overlap={leak['subject_overlap']} passed={leak['passed']}")

# SupCon micro-overfit, shuffled-label control, and one-fold minimal smoke.
for (modality, task), data in datasets.items():
    res = train_eval_smoke(
        data,
        test_name="supcon_micro_overfit_smoke",
        train_mode="micro_overfit",
        epochs=90,
        batch_size=64,
        supcon_weight=0.10,
        temperature=0.20,
        shuffle_labels=False,
    )
    passed = (
        res.metrics["macro_f1"] >= 0.90
        and res.metrics["balanced_accuracy"] >= 0.90
        and res.loss["total_last"] <= res.loss["total_first"]
        and not res.embedding["embedding_collapse_flag"]
    )
    test_records.append({
        "test": "supcon_micro_overfit_smoke",
        "modality": modality,
        "task": task,
        "passed": bool(passed),
        "summary": f"macro_f1={res.metrics['macro_f1']:.3f}; bal_acc={res.metrics['balanced_accuracy']:.3f}; total_loss_first={res.loss['total_first']:.4f}; total_loss_last={res.loss['total_last']:.4f}",
    })
    loss_rows.append({"test": "supcon_micro_overfit_smoke", "modality": modality, "task": task, **res.loss, **res.metrics, "one_class_pred": res.one_class_pred})
    embed_rows.append({"test": "supcon_micro_overfit_smoke", "modality": modality, "task": task, **res.embedding, "one_class_pred": res.one_class_pred, "pred_counts": json.dumps(res.pred_counts, sort_keys=True)})
    print(f"[supcon_micro_overfit_smoke] {modality} {task} macro_f1={res.metrics['macro_f1']:.3f} bal_acc={res.metrics['balanced_accuracy']:.3f} passed={passed}")

    res = train_eval_smoke(
        data,
        test_name="shuffled_label_negative_control",
        train_mode="subject_heldout_fold1",
        epochs=25,
        batch_size=64,
        supcon_weight=0.10,
        temperature=0.20,
        shuffle_labels=True,
    )
    passed = (
        res.metrics["macro_f1"] <= 0.65
        and res.metrics["balanced_accuracy"] <= 0.65
        and not res.embedding["embedding_collapse_flag"]
    )
    test_records.append({
        "test": "shuffled_label_negative_control",
        "modality": modality,
        "task": task,
        "passed": bool(passed),
        "summary": f"macro_f1={res.metrics['macro_f1']:.3f}; bal_acc={res.metrics['balanced_accuracy']:.3f}; one_class={res.one_class_pred}",
    })
    loss_rows.append({"test": "shuffled_label_negative_control", "modality": modality, "task": task, **res.loss, **res.metrics, "one_class_pred": res.one_class_pred})
    embed_rows.append({"test": "shuffled_label_negative_control", "modality": modality, "task": task, **res.embedding, "one_class_pred": res.one_class_pred, "pred_counts": json.dumps(res.pred_counts, sort_keys=True)})
    print(f"[shuffled_label_negative_control] {modality} {task} macro_f1={res.metrics['macro_f1']:.3f} bal_acc={res.metrics['balanced_accuracy']:.3f} passed={passed}")

    res = train_eval_smoke(
        data,
        test_name="one_fold_one_task_minimal_smoke",
        train_mode="subject_heldout_fold1",
        epochs=35,
        batch_size=64,
        supcon_weight=0.10,
        temperature=0.20,
        shuffle_labels=False,
    )
    passed = (
        math.isfinite(res.metrics["macro_f1"])
        and math.isfinite(res.metrics["balanced_accuracy"])
        and not res.one_class_pred
        and not res.embedding["embedding_collapse_flag"]
        and math.isfinite(res.loss["total_last"])
    )
    test_records.append({
        "test": "one_fold_one_task_minimal_smoke",
        "modality": modality,
        "task": task,
        "passed": bool(passed),
        "summary": f"macro_f1={res.metrics['macro_f1']:.3f}; bal_acc={res.metrics['balanced_accuracy']:.3f}; one_class={res.one_class_pred}; emb_var={res.embedding['embedding_variance_mean']:.6f}",
    })
    loss_rows.append({"test": "one_fold_one_task_minimal_smoke", "modality": modality, "task": task, **res.loss, **res.metrics, "one_class_pred": res.one_class_pred})
    embed_rows.append({"test": "one_fold_one_task_minimal_smoke", "modality": modality, "task": task, **res.embedding, "one_class_pred": res.one_class_pred, "pred_counts": json.dumps(res.pred_counts, sort_keys=True)})
    print(f"[one_fold_one_task_minimal_smoke] {modality} {task} macro_f1={res.metrics['macro_f1']:.3f} bal_acc={res.metrics['balanced_accuracy']:.3f} passed={passed}")

pair_df = pd.DataFrame(pair_rows)
loss_df = pd.DataFrame(loss_rows)
embed_df = pd.DataFrame(embed_rows)
pair_df.to_csv(PAIR_AUDIT_CSV, index=False)
loss_df.to_csv(LOSS_CSV, index=False)
embed_df.to_csv(EMBED_CSV, index=False)

all_passed = all(bool(r["passed"]) for r in test_records)
failed = [r for r in test_records if not bool(r["passed"])]

if all_passed:
    diagnosis = "supcon_dg_smoke_tests_passed_ready_for_minimal_first_pass_objective"
    recommended_next = "minimal_supcon_dg_first_pass_training_objective"
else:
    diagnosis = "supcon_dg_smoke_tests_failed_fix_before_training"
    recommended_next = "supcon_dg_smoke_failure_fix_objective"

by_test = {}
for r in test_records:
    by_test.setdefault(r["test"], {"passed": 0, "failed": 0})
    if r["passed"]:
        by_test[r["test"]]["passed"] += 1
    else:
        by_test[r["test"]]["failed"] += 1

report = {
    "status": "smoke_tests_complete",
    "created_or_updated_utc": NOW,
    "objective": str(OBJECTIVE_MD),
    "design_spec": str(DESIGN_MD),
    "design_review": str(DESIGN_REVIEW_MD),
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next,
    "device": str(DEVICE),
    "seed": SEED,
    "smoke_test_count": len(test_records),
    "all_passed": bool(all_passed),
    "by_test": by_test,
    "failed_tests": failed,
    "outputs": {
        "pair_sampler_audit_csv": str(PAIR_AUDIT_CSV),
        "loss_trace_summary_csv": str(LOSS_CSV),
        "embedding_diagnostic_summary_csv": str(EMBED_CSV),
    },
    "test_records": test_records,
    "interpretation": {
        "if_all_passed": "Implementation is smoke-test valid enough to consider a minimal first-pass training objective after human review.",
        "if_failed": "Do not expand to training. Fix the failing sampler/protocol/loss/negative-control issue first.",
        "training_authorized_by_this_report": False,
    },
}
REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

def md_bool(x: bool) -> str:
    return "PASS" if x else "FAIL"

summary_lines = []
for test, counts in sorted(by_test.items()):
    summary_lines.append(f"- `{test}`: {counts['passed']} passed, {counts['failed']} failed")

failed_md = "\n".join(
    f"- `{r['test']}` / {r['modality']} / {r['task']}: {r['summary']}"
    for r in failed
) if failed else "- none"

minimal_rows = loss_df[loss_df["test"] == "one_fold_one_task_minimal_smoke"].copy()
if not minimal_rows.empty:
    metric_lines = []
    for _, row in minimal_rows.iterrows():
        metric_lines.append(
            f"- {row['modality']} {row['task']}: macro-F1={safe_float(row['macro_f1']):.3f}, "
            f"balanced-accuracy={safe_float(row['balanced_accuracy']):.3f}, one-class={row['one_class_pred']}"
        )
else:
    metric_lines = ["- no minimal smoke rows"]
metric_md = "\n".join(metric_lines)

report_md = f"""# I-DARE Subject-variability SupCon/DG Smoke Tests Report

## Status

Smoke tests complete.

Generated UTC: `{NOW}`

Objective: `{OBJECTIVE_MD}`

Design spec: `{DESIGN_MD}`

## Executive Result

Diagnosis: `{diagnosis}`

Recommended next objective: `{recommended_next}`

All smoke tests passed: `{all_passed}`

Device: `{DEVICE}`

## Smoke-test Summary

{chr(10).join(summary_lines)}

## Failed Smoke Tests

{failed_md}

## Pair/Sampler Audit

Detailed CSV:

- `{PAIR_AUDIT_CSV}`

The pair/sampler audit checks that balanced batches contain both classes, multiple subjects, and cross-subject positive-pair availability.

## Loss Trace Summary

Detailed CSV:

- `{LOSS_CSV}`

The loss trace summary records CE, SupCon, and total loss movement for micro-overfit, shuffled-label negative control, and one-fold minimal smoke tests.

## Embedding Diagnostic Summary

Detailed CSV:

- `{EMBED_CSV}`

The embedding diagnostic summary records embedding variance, norm, centroid distance, collapse flag, prediction counts, and one-class prediction status.

## One-fold Minimal Smoke Metrics

{metric_md}

## Interpretation

This report still does **not** authorize full SupCon/DG training.

If all smoke tests passed, the next scientific step is a human review/closeout and then a minimal first-pass training objective.

If any smoke test failed, the next step must be a targeted fix objective, not broader training.

Failure interpretation:

- sampler failure -> fix positive/negative pair construction;
- leakage failure -> fix protocol and data split;
- micro-overfit failure -> fix implementation or optimization;
- negative-control failure -> audit leakage/evaluation;
- one-fold smoke failure -> inspect pair coverage, loss traces, embedding diagnostics, and prediction collapse.

## Next Allowed Step

Human review / closeout before any minimal SupCon/DG first-pass training objective.
"""
REPORT_MD.write_text(report_md, encoding="utf-8")

# Update project status docs.
project_md = PROJECT_MD.read_text(encoding="utf-8")
report_row = "| I-DARE subject-variability SupCon/DG smoke-tests report | smoke tests complete; pending human review | yes | `docs/idare_subject_variability_supcon_dg_smoke_tests_report.md` | Human review / closeout before minimal first-pass training or smoke-fix objective. | EEG+EMG fusion; final LOSO claim; direct full SupCon/DG training; broad hyperparameter search; mainline change. |"
if report_row not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE subject-variability SupCon/DG smoke-tests objective |"):
            out.append(report_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not find smoke-tests objective row in project_status_current.md")
    project_md = "\n".join(out) + "\n"

bullet = f"- SupCon/DG smoke tests are complete in `docs/idare_subject_variability_supcon_dg_smoke_tests_report.md`; diagnosis is `{diagnosis}`, and full training remains blocked until human review."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: marker not found in project_status_current.md")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_subject_variability_supcon_dg_smoke_tests_report"] = {
    "status": "smoke_tests_complete",
    "evidence": str(REPORT_MD),
    "evidence_json": str(REPORT_JSON),
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next,
    "all_passed": bool(all_passed),
    "training_authorized": False,
    "outputs": report["outputs"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_SUPCON_DG_SMOKE_TESTS_REPORT_WRITTEN")
print(REPORT_MD)
print(REPORT_JSON)
print(PAIR_AUDIT_CSV)
print(LOSS_CSV)
print(EMBED_CSV)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next)
print("all_passed=", all_passed)
PY
echo

echo "===== 4) validate generated outputs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

paths = [
    Path("docs/idare_subject_variability_supcon_dg_smoke_tests_report.json"),
    Path("docs/project_status_current.json"),
]
for p in paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

csvs = [
    Path("docs/idare_subject_variability_supcon_dg_pair_sampler_audit.csv"),
    Path("docs/idare_subject_variability_supcon_dg_loss_trace_summary.csv"),
    Path("docs/idare_subject_variability_supcon_dg_embedding_diagnostic_summary.csv"),
]
for p in csvs:
    df = pd.read_csv(p)
    print(p.name, "rows=", len(df))
    if len(df) == 0:
        raise SystemExit(f"ERROR: empty CSV: {p}")

report = json.loads(Path("docs/idare_subject_variability_supcon_dg_smoke_tests_report.json").read_text(encoding="utf-8"))
required_tests = [
    "pair_sampler_integrity_smoke",
    "leakage_guard_smoke",
    "supcon_micro_overfit_smoke",
    "shuffled_label_negative_control",
    "one_fold_one_task_minimal_smoke",
]
for t in required_tests:
    if t not in report.get("by_test", {}):
        raise SystemExit(f"ERROR: missing test in report: {t}")

text = Path("docs/idare_subject_variability_supcon_dg_smoke_tests_report.md").read_text(encoding="utf-8")
for term in ["Smoke Tests Report", "Failed Smoke Tests", "Pair/Sampler Audit", "does **not** authorize full SupCon/DG training"]:
    if term not in text:
        raise SystemExit(f"ERROR: missing term in report md: {term}")

print("diagnosis=", report.get("diagnosis"))
print("recommended_next_objective=", report.get("recommended_next_objective"))
print("all_passed=", report.get("all_passed"))
print("ALL_SUPCON_DG_SMOKE_OUTPUTS_VALID")
PY

grep -n "## Status\|## Executive Result\|## Smoke-test Summary\|## Failed Smoke Tests\|## Next Allowed Step" docs/idare_subject_variability_supcon_dg_smoke_tests_report.md
grep -n "SupCon/DG smoke-tests report\|SupCon/DG smoke tests are complete" docs/project_status_current.md
echo

echo "===== 5) file list ====="
ls -lh \
  docs/idare_subject_variability_supcon_dg_smoke_tests_report.md \
  docs/idare_subject_variability_supcon_dg_smoke_tests_report.json \
  docs/idare_subject_variability_supcon_dg_pair_sampler_audit.csv \
  docs/idare_subject_variability_supcon_dg_loss_trace_summary.csv \
  docs/idare_subject_variability_supcon_dg_embedding_diagnostic_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push smoke-test report ====="
git add \
  docs/idare_subject_variability_supcon_dg_smoke_tests_report.md \
  docs/idare_subject_variability_supcon_dg_smoke_tests_report.json \
  docs/idare_subject_variability_supcon_dg_pair_sampler_audit.csv \
  docs/idare_subject_variability_supcon_dg_loss_trace_summary.csv \
  docs/idare_subject_variability_supcon_dg_embedding_diagnostic_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "analysis: add I-DARE SupCon DG smoke tests report"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_supcon_dg_smoke_tests_run.log"
