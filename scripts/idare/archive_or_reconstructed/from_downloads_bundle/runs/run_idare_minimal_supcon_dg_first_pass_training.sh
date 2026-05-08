#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start minimal SupCon/DG first-pass training ====="
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
print("torch_cuda_available=", torch.cuda.is_available())
print("OK_IMPORTS")
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repository is not clean. Commit/stash changes before running first-pass training." >&2
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
  docs/idare_minimal_supcon_dg_first_pass_training_objective.md \
  docs/idare_minimal_supcon_dg_first_pass_training_objective.json \
  docs/idare_subject_variability_supcon_dg_smoke_tests_review_status.md \
  docs/idare_subject_variability_supcon_dg_smoke_tests_report.json \
  docs/idare_subject_variability_supcon_dg_design_spec.md \
  docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv \
  docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 3) remove stale outputs ====="
rm -f \
  docs/idare_minimal_supcon_dg_first_pass_report.md \
  docs/idare_minimal_supcon_dg_first_pass_report.json \
  docs/idare_minimal_supcon_dg_first_pass_runs.csv \
  docs/idare_minimal_supcon_dg_first_pass_predictions.csv \
  docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv \
  docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv
echo "OK_CLEAN_OUTPUT_TARGETS"
echo

echo "===== 4) run minimal SupCon/DG first-pass matrix ====="
"$PY" - <<'PY'
import csv
import json
import math
import os
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
import torch.nn.functional as F

DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

OUT_REPORT_MD = DOCS / "idare_minimal_supcon_dg_first_pass_report.md"
OUT_REPORT_JSON = DOCS / "idare_minimal_supcon_dg_first_pass_report.json"
OUT_RUNS_CSV = DOCS / "idare_minimal_supcon_dg_first_pass_runs.csv"
OUT_PRED_CSV = DOCS / "idare_minimal_supcon_dg_first_pass_predictions.csv"
OUT_EMBED_CSV = DOCS / "idare_minimal_supcon_dg_first_pass_embedding_summary.csv"
OUT_LOSS_CSV = DOCS / "idare_minimal_supcon_dg_first_pass_loss_summary.csv"

PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

OBJECTIVE_JSON = DOCS / "idare_minimal_supcon_dg_first_pass_training_objective.json"
SMOKE_REPORT_JSON = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_report.json"
SMOKE_REVIEW_MD = DOCS / "idare_subject_variability_supcon_dg_smoke_tests_review_status.md"
DESIGN_MATRIX = DOCS / "idare_subject_variability_supcon_dg_first_pass_run_matrix.csv"
HP_REGISTRY = DOCS / "idare_subject_variability_supcon_dg_hyperparameter_registry.csv"

EEG_INDEX = Path(".cache/idare_eeg_cache_index_baseline_corrected.csv")
EEG_NPY = Path(".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy")
EMG_INDEX = Path(".cache/idare_emg_feature_cache_index.csv")
EMG_NPY = Path(".cache/idare_emg_features.npy")

SEED = int(os.environ.get("IDARE_SUPCON_DG_SEED", "11"))
EPOCHS = int(os.environ.get("IDARE_SUPCON_DG_EPOCHS", "12"))
LR = float(os.environ.get("IDARE_SUPCON_DG_LR", "0.001"))
WEIGHT_DECAY = float(os.environ.get("IDARE_SUPCON_DG_WEIGHT_DECAY", "0.0001"))
HIDDEN_DIM = int(os.environ.get("IDARE_SUPCON_DG_HIDDEN_DIM", "64"))
PROJ_DIM = int(os.environ.get("IDARE_SUPCON_DG_PROJ_DIM", "64"))
TAU = float(os.environ.get("IDARE_SUPCON_DG_TAU", "0.10"))
LAMBDA_SUPCON = float(os.environ.get("IDARE_SUPCON_DG_LAMBDA_SUPCON", "0.10"))
LAMBDA_VREX = float(os.environ.get("IDARE_SUPCON_DG_LAMBDA_VREX", "0.05"))
WARMUP_EPOCHS = int(os.environ.get("IDARE_SUPCON_DG_WARMUP_EPOCHS", "3"))
N_FOLDS = 6

torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device=", device)
print("epochs=", EPOCHS, "lr=", LR, "seed=", SEED)

for p in [OBJECTIVE_JSON, SMOKE_REPORT_JSON, SMOKE_REVIEW_MD, DESIGN_MATRIX, HP_REGISTRY, EEG_INDEX, EEG_NPY, EMG_INDEX, EMG_NPY]:
    if not p.exists():
        raise SystemExit(f"ERROR: missing required file: {p}")

objective = json.loads(OBJECTIVE_JSON.read_text(encoding="utf-8"))
if objective["authorized_scope"]["minimal_first_pass_training_authorized"] is not True:
    raise SystemExit("ERROR: objective does not authorize minimal first-pass training")
if objective["authorized_scope"]["direct_full_training_authorized"] is not False:
    raise SystemExit("ERROR: direct full training must remain blocked")

smoke = json.loads(SMOKE_REPORT_JSON.read_text(encoding="utf-8"))
if smoke.get("all_passed") is not True:
    raise SystemExit("ERROR: smoke tests are not all passed")
if smoke.get("diagnosis") != "supcon_dg_smoke_tests_passed_ready_for_minimal_first_pass_objective":
    raise SystemExit(f"ERROR: unexpected smoke diagnosis: {smoke.get('diagnosis')}")

matrix_df = pd.read_csv(DESIGN_MATRIX)
if matrix_df.empty:
    raise SystemExit("ERROR: empty first-pass run matrix")
first_pass_rows = matrix_df[matrix_df["stage"].astype(str).str.startswith("first_pass")].copy()
if first_pass_rows.empty:
    raise SystemExit("ERROR: no first-pass rows found in run matrix")
print("design_rows=", len(matrix_df), "first_pass_design_rows=", len(first_pass_rows))

def read_index(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "subject_id" not in df.columns:
        raise SystemExit(f"ERROR: {path} lacks subject_id")
    df = df.copy()
    df["subject_id"] = df["subject_id"].astype(int)
    df["_row_id"] = np.arange(len(df), dtype=int)
    return df

def pick_rating_column(df: pd.DataFrame, task: str) -> str:
    candidates = [
        f"{task}_score",
        task,
        f"{task}_rating",
        f"rating_{task}",
        f"{task}_label_raw",
    ]
    for c in candidates:
        if c in df.columns:
            return c
    raise SystemExit(f"ERROR: could not find raw rating column for task={task}; candidates={candidates}")

def add_subject_relative_label(df: pd.DataFrame, task: str) -> pd.DataFrame:
    col = pick_rating_column(df, task)
    out = df.copy()
    y = np.full(len(out), np.nan, dtype=float)
    for sid, sub in out.groupby("subject_id", sort=True):
        vals = pd.to_numeric(sub[col], errors="coerce")
        valid = vals.dropna()
        if len(valid) < 3:
            continue
        q_low = float(valid.quantile(1.0 / 3.0))
        q_high = float(valid.quantile(2.0 / 3.0))
        idx = sub.index
        low_mask = vals <= q_low
        high_mask = vals >= q_high
        y[idx[low_mask.to_numpy()]] = 0.0
        y[idx[high_mask.to_numpy()]] = 1.0
        # If all values are identical, avoid assigning the same rows to both classes.
        if q_low == q_high:
            y[idx] = np.nan
    label_col = f"subject_relative_{task}_q33_label"
    out[label_col] = y
    return out

def make_folds(subjects, n_folds=6, seed=11):
    subjects = sorted({int(s) for s in subjects})
    rng = np.random.default_rng(int(seed))
    arr = np.asarray(subjects, dtype=int)
    rng.shuffle(arr)
    chunks = np.array_split(arr, n_folds)
    folds = []
    all_set = set(subjects)
    for i, chunk in enumerate(chunks, start=1):
        val_subjects = sorted(int(x) for x in chunk.tolist())
        train_subjects = sorted(all_set - set(val_subjects))
        folds.append({"fold": i, "val_subjects": val_subjects, "train_subjects": train_subjects})
    return folds

def build_eeg_features() -> np.ndarray:
    print("BUILDING_EEG_SUMMARY_FEATURES")
    x = np.load(EEG_NPY, mmap_mode="r")
    # Compact but information-preserving enough for a diagnostic first pass.
    mean = np.asarray(x.mean(axis=2), dtype=np.float32)
    std = np.asarray(x.std(axis=2), dtype=np.float32)
    amin = np.asarray(x.min(axis=2), dtype=np.float32)
    amax = np.asarray(x.max(axis=2), dtype=np.float32)
    feat = np.concatenate([mean, std, amin, amax], axis=1).astype(np.float32)
    return feat

def build_emg_features() -> np.ndarray:
    print("BUILDING_EMG_SIGNED_LOG1P_FEATURES")
    x = np.asarray(np.load(EMG_NPY), dtype=np.float32)
    feat = np.sign(x) * np.log1p(np.abs(x))
    return feat.astype(np.float32)

class SmallMLP(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, projection_dim: int):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.05),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.projection = nn.Linear(hidden_dim, projection_dim)
        self.classifier = nn.Linear(hidden_dim, 2)

    def forward(self, x):
        h = self.encoder(x)
        z = F.normalize(self.projection(h), dim=1)
        logits = self.classifier(h)
        return logits, z, h

def supcon_loss(z, y, subjects, tau: float):
    n = z.shape[0]
    if n < 2:
        return z.new_tensor(0.0), {"positive_pair_coverage": 0.0, "anchors_without_positive": 1.0}

    y_col = y.view(-1, 1)
    s_col = subjects.view(-1, 1)
    eye = torch.eye(n, device=z.device, dtype=torch.bool)
    pos = (y_col == y_col.T) & (s_col != s_col.T) & (~eye)
    logits = torch.matmul(z, z.T) / tau
    logits = logits - logits.max(dim=1, keepdim=True).values.detach()
    logits_mask = (~eye).float()
    exp_logits = torch.exp(logits) * logits_mask
    denom = exp_logits.sum(dim=1, keepdim=True).clamp_min(1e-12)
    log_prob = logits - torch.log(denom)
    pos_count = pos.sum(dim=1)
    valid = pos_count > 0
    if valid.sum() == 0:
        return z.new_tensor(0.0), {"positive_pair_coverage": 0.0, "anchors_without_positive": 1.0}
    loss_per_anchor = -(log_prob * pos.float()).sum(dim=1)[valid] / pos_count[valid].float()
    coverage = float(valid.float().mean().detach().cpu())
    return loss_per_anchor.mean(), {
        "positive_pair_coverage": coverage,
        "anchors_without_positive": 1.0 - coverage,
    }

def vrex_loss(logits, y, subjects, class_weights):
    losses = []
    unique_subjects = torch.unique(subjects)
    for sid in unique_subjects:
        mask = subjects == sid
        if int(mask.sum().item()) == 0:
            continue
        losses.append(F.cross_entropy(logits[mask], y[mask], weight=class_weights, reduction="mean"))
    if len(losses) < 2:
        return logits.new_tensor(0.0), 0
    stacked = torch.stack(losses)
    return torch.var(stacked, unbiased=False), len(losses)

def compute_metrics(y_true, prob1):
    y_true = np.asarray(y_true, dtype=int)
    prob1 = np.asarray(prob1, dtype=float)
    y_pred = (prob1 >= 0.5).astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())

    acc = float((tp + tn) / max(1, len(y_true)))
    rec0 = tn / max(1, tn + fp)
    rec1 = tp / max(1, tp + fn)
    bal_acc = float((rec0 + rec1) / 2.0)

    def f1_for(cls):
        if cls == 1:
            precision = tp / max(1, tp + fp)
            recall = tp / max(1, tp + fn)
        else:
            precision = tn / max(1, tn + fn)
            recall = tn / max(1, tn + fp)
        if precision + recall == 0:
            return 0.0
        return 2 * precision * recall / (precision + recall)

    macro_f1 = float((f1_for(0) + f1_for(1)) / 2.0)
    counts = Counter(int(x) for x in y_pred.tolist())
    majority = max(np.bincount(y_true, minlength=2)) / max(1, len(y_true))
    return {
        "final_accuracy": acc,
        "final_balanced_accuracy": bal_acc,
        "final_macro_f1": macro_f1,
        "majority_accuracy": float(majority),
        "one_class_pred": len(counts) == 1,
        "pred_count_0": int(counts.get(0, 0)),
        "pred_count_1": int(counts.get(1, 0)),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }, y_pred

def embedding_diagnostics(z_np, y_np, subj_np):
    z_np = np.asarray(z_np, dtype=np.float32)
    y_np = np.asarray(y_np, dtype=int)
    subj_np = np.asarray(subj_np, dtype=int)
    n = len(y_np)
    if n < 2:
        return {
            "same_class_cross_subject_distance_mean": math.nan,
            "diff_class_cross_subject_distance_mean": math.nan,
            "distance_margin_diff_minus_same": math.nan,
        }

    # Keep diagnostics bounded.
    if n > 320:
        rng = np.random.default_rng(SEED)
        take = rng.choice(np.arange(n), size=320, replace=False)
        z_np = z_np[take]
        y_np = y_np[take]
        subj_np = subj_np[take]
        n = len(y_np)

    diff = z_np[:, None, :] - z_np[None, :, :]
    dist = np.sqrt(np.maximum((diff * diff).sum(axis=2), 0.0))
    eye = np.eye(n, dtype=bool)
    cross_subject = subj_np[:, None] != subj_np[None, :]
    same_class = y_np[:, None] == y_np[None, :]
    diff_class = y_np[:, None] != y_np[None, :]
    same_mask = (~eye) & cross_subject & same_class
    diff_mask = (~eye) & cross_subject & diff_class
    same_val = float(np.nanmean(dist[same_mask])) if same_mask.any() else math.nan
    diff_val = float(np.nanmean(dist[diff_mask])) if diff_mask.any() else math.nan
    return {
        "same_class_cross_subject_distance_mean": same_val,
        "diff_class_cross_subject_distance_mean": diff_val,
        "distance_margin_diff_minus_same": float(diff_val - same_val) if np.isfinite(same_val) and np.isfinite(diff_val) else math.nan,
    }

def write_csv(path: Path, rows):
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = []
    seen = set()
    for row in rows:
        for k in row.keys():
            if k not in seen:
                seen.add(k)
                fieldnames.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow(row)

def method_params(method: str):
    use_supcon = method in {"CE_plus_SupCon", "CE_plus_SupCon_plus_VREx"}
    use_vrex = method in {"CE_plus_VREx", "CE_plus_SupCon_plus_VREx"}
    return use_supcon, use_vrex

def train_one_run(global_run_id, design_row, modality, task, fold_id, fold, X_all, index_df):
    label_col = f"subject_relative_{task}_q33_label"
    valid = index_df[label_col].notna().to_numpy()
    subjects = index_df["subject_id"].astype(int).to_numpy()
    y_all = index_df[label_col].to_numpy()
    row_ids = index_df["_row_id"].to_numpy()

    val_subjects = set(fold["val_subjects"])
    val_mask = valid & np.isin(subjects, list(val_subjects))
    train_mask = valid & (~np.isin(subjects, list(val_subjects)))

    train_idx = np.where(train_mask)[0]
    val_idx = np.where(val_mask)[0]
    if len(train_idx) == 0 or len(val_idx) == 0:
        raise RuntimeError(f"empty split modality={modality} task={task} fold={fold_id}")

    train_subjects = set(int(x) for x in subjects[train_idx])
    val_subjects_found = set(int(x) for x in subjects[val_idx])
    if train_subjects & val_subjects_found:
        raise RuntimeError("subject leakage detected")
    if set(row_ids[train_idx]) & set(row_ids[val_idx]):
        raise RuntimeError("row leakage detected")

    X_train_raw = np.asarray(X_all[train_idx], dtype=np.float32)
    X_val_raw = np.asarray(X_all[val_idx], dtype=np.float32)
    mu = X_train_raw.mean(axis=0, keepdims=True)
    sigma = X_train_raw.std(axis=0, keepdims=True)
    sigma = np.where(sigma < 1e-6, 1.0, sigma)
    X_train = (X_train_raw - mu) / sigma
    X_val = (X_val_raw - mu) / sigma

    y_train = y_all[train_idx].astype(int)
    y_val = y_all[val_idx].astype(int)
    s_train = subjects[train_idx].astype(int)
    s_val = subjects[val_idx].astype(int)

    # Fail early if no contrastive positives are possible.
    pos_possible = []
    for i in range(len(y_train)):
        pos_possible.append(np.any((y_train == y_train[i]) & (s_train != s_train[i])))
    pos_coverage = float(np.mean(pos_possible))
    if pos_coverage < 0.95:
        raise RuntimeError(f"positive pair coverage below gate: {pos_coverage}")

    cls_counts = np.bincount(y_train, minlength=2).astype(np.float32)
    cls_counts = np.where(cls_counts <= 0, 1.0, cls_counts)
    class_weights_np = cls_counts.sum() / (2.0 * cls_counts)

    xt = torch.tensor(X_train, dtype=torch.float32, device=device)
    yt = torch.tensor(y_train, dtype=torch.long, device=device)
    st = torch.tensor(s_train, dtype=torch.long, device=device)
    xv = torch.tensor(X_val, dtype=torch.float32, device=device)
    class_weights = torch.tensor(class_weights_np, dtype=torch.float32, device=device)

    model = SmallMLP(X_train.shape[1], HIDDEN_DIM, PROJ_DIM).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)

    use_supcon, use_vrex = method_params(str(design_row["method"]))
    loss_trace = []
    for epoch in range(1, EPOCHS + 1):
        model.train()
        opt.zero_grad(set_to_none=True)
        logits, z, _ = model(xt)
        ce = F.cross_entropy(logits, yt, weight=class_weights)
        sup = xt.new_tensor(0.0)
        sup_stats = {"positive_pair_coverage": pos_coverage, "anchors_without_positive": 1.0 - pos_coverage}
        if use_supcon:
            sup, sup_stats = supcon_loss(z, yt, st, TAU)
        vr, env_count = vrex_loss(logits, yt, st, class_weights) if use_vrex else (xt.new_tensor(0.0), 0)

        active_supcon = LAMBDA_SUPCON if (use_supcon and epoch > WARMUP_EPOCHS) else 0.0
        active_vrex = LAMBDA_VREX if (use_vrex and epoch > WARMUP_EPOCHS) else 0.0
        loss = ce + active_supcon * sup + active_vrex * vr
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite loss in run {global_run_id}")
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        opt.step()

        loss_trace.append({
            "global_run_id": global_run_id,
            "epoch": epoch,
            "ce_loss": float(ce.detach().cpu()),
            "supcon_loss": float(sup.detach().cpu()),
            "vrex_loss": float(vr.detach().cpu()),
            "total_loss": float(loss.detach().cpu()),
            "active_lambda_supcon": active_supcon,
            "active_lambda_vrex": active_vrex,
            "positive_pair_coverage": sup_stats["positive_pair_coverage"],
            "anchors_without_positive": sup_stats["anchors_without_positive"],
            "vrex_environment_count": int(env_count),
        })

    model.eval()
    with torch.no_grad():
        logits_val, z_val, _ = model(xv)
        prob = torch.softmax(logits_val, dim=1)[:, 1].detach().cpu().numpy()
        z_np = z_val.detach().cpu().numpy()

    metrics, y_pred = compute_metrics(y_val, prob)
    emb = embedding_diagnostics(z_np, y_val, s_val)

    run_row = {
        "global_run_id": global_run_id,
        "design_run_id": int(design_row["run_id"]),
        "stage": str(design_row["stage"]),
        "method": str(design_row["method"]),
        "modality": modality,
        "task": task,
        "fold": fold_id,
        "seed": SEED,
        "label_formulation": str(design_row["label_formulation"]),
        "recipe": str(design_row["recipe"]),
        "hyperparameter_tag": str(design_row["hyperparameter_tag"]),
        "n_train": int(len(train_idx)),
        "n_val": int(len(val_idx)),
        "train_subject_count": int(len(train_subjects)),
        "val_subject_count": int(len(val_subjects_found)),
        "val_subjects": " ".join(str(x) for x in sorted(val_subjects_found)),
        "epochs": EPOCHS,
        "lr": LR,
        "hidden_dim": HIDDEN_DIM,
        "projection_dim": PROJ_DIM,
        "tau": TAU,
        "lambda_supcon": LAMBDA_SUPCON if use_supcon else 0.0,
        "lambda_vrex": LAMBDA_VREX if use_vrex else 0.0,
        "warmup_epochs": WARMUP_EPOCHS,
        "positive_pair_coverage_train": pos_coverage,
        "row_overlap": 0,
        "subject_overlap": 0,
        **metrics,
    }

    pred_rows = []
    for local_i, idx in enumerate(val_idx.tolist()):
        pred_rows.append({
            "global_run_id": global_run_id,
            "design_run_id": int(design_row["run_id"]),
            "stage": str(design_row["stage"]),
            "method": str(design_row["method"]),
            "modality": modality,
            "task": task,
            "fold": fold_id,
            "seed": SEED,
            "subject_id": int(subjects[idx]),
            "source_row_id": int(row_ids[idx]),
            "y_true": int(y_val[local_i]),
            "prob1": float(prob[local_i]),
            "y_pred": int(y_pred[local_i]),
        })

    emb_row = {
        "global_run_id": global_run_id,
        "design_run_id": int(design_row["run_id"]),
        "stage": str(design_row["stage"]),
        "method": str(design_row["method"]),
        "modality": modality,
        "task": task,
        "fold": fold_id,
        "seed": SEED,
        **emb,
    }

    print(json.dumps({
        "global_run_id": global_run_id,
        "method": str(design_row["method"]),
        "modality": modality,
        "task": task,
        "fold": fold_id,
        "macro_f1": round(run_row["final_macro_f1"], 4),
        "bal_acc": round(run_row["final_balanced_accuracy"], 4),
        "acc": round(run_row["final_accuracy"], 4),
        "one_class_pred": run_row["one_class_pred"],
    }, sort_keys=True))

    return run_row, pred_rows, emb_row, loss_trace

# Load data.
eeg_index = read_index(EEG_INDEX)
emg_index = read_index(EMG_INDEX)
for task in ["valence", "arousal"]:
    eeg_index = add_subject_relative_label(eeg_index, task)
    emg_index = add_subject_relative_label(emg_index, task)

eeg_features = build_eeg_features()
emg_features = build_emg_features()
if len(eeg_features) != len(eeg_index):
    raise SystemExit("ERROR: EEG feature/index row mismatch")
if len(emg_features) != len(emg_index):
    raise SystemExit("ERROR: EMG feature/index row mismatch")

features_by_modality = {"EEG": eeg_features, "EMG": emg_features}
index_by_modality = {"EEG": eeg_index, "EMG": emg_index}

run_rows = []
pred_rows_all = []
embed_rows = []
loss_rows = []
expanded_specs = []
global_run_id = 0

for _, design_row in first_pass_rows.iterrows():
    modality = str(design_row["modality"])
    task = str(design_row["task"])
    index_df = index_by_modality[modality]
    label_col = f"subject_relative_{task}_q33_label"
    valid_subjects = sorted(index_df.loc[index_df[label_col].notna(), "subject_id"].astype(int).unique().tolist())
    folds = make_folds(valid_subjects, N_FOLDS, SEED)

    if str(design_row["fold_scope"]) != "folds_1_to_6":
        raise SystemExit(f"ERROR: unsupported first-pass fold_scope={design_row['fold_scope']}")

    for fold in folds:
        global_run_id += 1
        expanded_specs.append({
            "global_run_id": global_run_id,
            "design_run_id": int(design_row["run_id"]),
            "method": str(design_row["method"]),
            "modality": modality,
            "task": task,
            "fold": int(fold["fold"]),
        })
        rr, pr, er, lr_rows = train_one_run(
            global_run_id=global_run_id,
            design_row=design_row,
            modality=modality,
            task=task,
            fold_id=int(fold["fold"]),
            fold=fold,
            X_all=features_by_modality[modality],
            index_df=index_df,
        )
        run_rows.append(rr)
        pred_rows_all.extend(pr)
        embed_rows.append(er)
        loss_rows.extend(lr_rows)

if not run_rows:
    raise SystemExit("ERROR: no runs completed")

write_csv(OUT_RUNS_CSV, run_rows)
write_csv(OUT_PRED_CSV, pred_rows_all)
write_csv(OUT_EMBED_CSV, embed_rows)
write_csv(OUT_LOSS_CSV, loss_rows)

runs_df = pd.DataFrame(run_rows)
agg = (
    runs_df.groupby(["method", "modality", "task"], dropna=False)
    .agg(
        n_runs=("global_run_id", "count"),
        mean_macro_f1=("final_macro_f1", "mean"),
        mean_balanced_accuracy=("final_balanced_accuracy", "mean"),
        mean_accuracy=("final_accuracy", "mean"),
        one_class_pred_count=("one_class_pred", "sum"),
        mean_positive_pair_coverage=("positive_pair_coverage_train", "mean"),
    )
    .reset_index()
)
agg_records = agg.to_dict(orient="records")

best_row = agg.sort_values(["mean_macro_f1", "mean_balanced_accuracy"], ascending=False).iloc[0].to_dict()
ce_supcon = agg[agg["method"] == "CE_plus_SupCon"]
combo = agg[agg["method"] == "CE_plus_SupCon_plus_VREx"]
vrex = agg[agg["method"] == "CE_plus_VREx"]

# Conservative diagnosis: require all modality/task cells of a method to exceed 0.54 macro-F1
# and no one-class collapse to call it a strong positive. Otherwise keep it diagnostic.
def method_status(method_df):
    if method_df.empty:
        return "not_run"
    min_f1 = float(method_df["mean_macro_f1"].min())
    mean_f1 = float(method_df["mean_macro_f1"].mean())
    collapse = int(method_df["one_class_pred_count"].sum())
    if collapse > 0:
        return "invalid_or_collapse"
    if min_f1 >= 0.54 and mean_f1 >= 0.56:
        return "consistent_positive_signal"
    if mean_f1 >= 0.52:
        return "mixed_or_weak_positive_signal"
    return "not_sufficient"

status_by_method = {
    "CE_plus_SupCon": method_status(ce_supcon),
    "CE_plus_VREx": method_status(vrex),
    "CE_plus_SupCon_plus_VREx": method_status(combo),
}
if "consistent_positive_signal" in status_by_method.values():
    diagnosis = "minimal_supcon_dg_first_pass_consistent_positive_signal"
    recommended_next = "supcon_dg_second_pass_confirmation_objective"
elif "mixed_or_weak_positive_signal" in status_by_method.values():
    diagnosis = "minimal_supcon_dg_first_pass_mixed_weak_signal"
    recommended_next = "supcon_dg_targeted_ablation_objective"
else:
    diagnosis = "minimal_supcon_dg_first_pass_not_sufficient"
    recommended_next = "supcon_dg_failure_analysis_objective"

payload = {
    "status": "first_pass_training_complete_pending_human_review",
    "created_or_updated_utc": NOW,
    "objective": str(OBJECTIVE_JSON.with_suffix(".md")),
    "objective_json": str(OBJECTIVE_JSON),
    "smoke_report_json": str(SMOKE_REPORT_JSON),
    "smoke_review": str(SMOKE_REVIEW_MD),
    "design_matrix": str(DESIGN_MATRIX),
    "hyperparameter_registry": str(HP_REGISTRY),
    "device": str(device),
    "seed": SEED,
    "epochs": EPOCHS,
    "expanded_run_count": int(len(run_rows)),
    "design_first_pass_rows": int(len(first_pass_rows)),
    "prediction_rows": int(len(pred_rows_all)),
    "aggregate_by_method_modality_task": agg_records,
    "best_aggregate_row": best_row,
    "status_by_method": status_by_method,
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next,
    "outputs": {
        "runs_csv": str(OUT_RUNS_CSV),
        "predictions_csv": str(OUT_PRED_CSV),
        "embedding_summary_csv": str(OUT_EMBED_CSV),
        "loss_summary_csv": str(OUT_LOSS_CSV),
        "report_md": str(OUT_REPORT_MD),
        "report_json": str(OUT_REPORT_JSON),
    },
    "blocked": objective.get("blocked", []),
}
OUT_REPORT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

def md_table(df, max_rows=20):
    if df.empty:
        return "_No rows._"
    d = df.copy().head(max_rows)
    for c in d.columns:
        if pd.api.types.is_float_dtype(d[c]):
            d[c] = d[c].map(lambda x: f"{x:.4f}")
    return d.to_markdown(index=False)

report = f"""# I-DARE Minimal SupCon/DG First-pass Training Report

## Status

Minimal first-pass SupCon/DG diagnostic training complete, pending human review.

Generated UTC: `{NOW}`

## Run Matrix

- Design first-pass rows executed: `{len(first_pass_rows)}`
- Expanded subject-heldout runs completed: `{len(run_rows)}`
- Prediction rows: `{len(pred_rows_all)}`
- Epochs: `{EPOCHS}`
- Device: `{device}`

## Aggregate Results

{md_table(agg)}

## Best Aggregate Cell

- method: `{best_row.get('method')}`
- modality: `{best_row.get('modality')}`
- task: `{best_row.get('task')}`
- mean macro-F1: `{float(best_row.get('mean_macro_f1')):.4f}`
- mean balanced accuracy: `{float(best_row.get('mean_balanced_accuracy')):.4f}`

## Method-level Interpretation

```json
{json.dumps(status_by_method, indent=2, sort_keys=True)}
```

## Diagnosis

`{diagnosis}`

## Recommended Next Objective

`{recommended_next}`

## Required Caution

This report does not authorize final claims, fusion, broad search, or mainline replacement.

The result must be reviewed before any second-pass confirmation or ablation objective.

## Outputs

- `{OUT_RUNS_CSV}`
- `{OUT_PRED_CSV}`
- `{OUT_EMBED_CSV}`
- `{OUT_LOSS_CSV}`
- `{OUT_REPORT_JSON}`

## Next Allowed Step

Human review / closeout before the recommended next objective.
"""
OUT_REPORT_MD.write_text(report, encoding="utf-8")

# Update roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
report_row = "| I-DARE minimal SupCon/DG first-pass training report | minimal first-pass SupCon/DG diagnostic training complete; pending human review | yes | `docs/idare_minimal_supcon_dg_first_pass_report.md` | Human review / closeout before second-pass confirmation, targeted ablation, or failure analysis. | EEG+EMG fusion; final LOSO claim; direct full SupCon/DG training; broad hyperparameter search; mainline change. |"
if report_row not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE minimal SupCon/DG first-pass training objective |"):
            out.append(report_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not find objective row in project_status_current.md")
    project_md = "\n".join(out) + "\n"

bullet = f"- Minimal SupCon/DG first-pass diagnostic training is complete in `docs/idare_minimal_supcon_dg_first_pass_report.md`; diagnosis is `{diagnosis}`, and full SupCon/DG training remains blocked pending review."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: marker not found in project_status_current.md")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_minimal_supcon_dg_first_pass_training_report"] = {
    "status": "first_pass_training_complete_pending_human_review",
    "evidence": str(OUT_REPORT_MD),
    "evidence_json": str(OUT_REPORT_JSON),
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next,
    "expanded_run_count": int(len(run_rows)),
    "full_training_authorized": False,
    "broad_hyperparameter_search_authorized": False,
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_MINIMAL_SUPCON_DG_FIRST_PASS_REPORT_WRITTEN")
print(OUT_REPORT_MD)
print(OUT_REPORT_JSON)
print(OUT_RUNS_CSV)
print(OUT_PRED_CSV)
print(OUT_EMBED_CSV)
print(OUT_LOSS_CSV)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next)
print("expanded_run_count=", len(run_rows))
print("prediction_rows=", len(pred_rows_all))
PY
echo

echo "===== 5) validate outputs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path

required_json = [
    Path("docs/idare_minimal_supcon_dg_first_pass_report.json"),
    Path("docs/project_status_current.json"),
]
for p in required_json:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

for p in [
    Path("docs/idare_minimal_supcon_dg_first_pass_runs.csv"),
    Path("docs/idare_minimal_supcon_dg_first_pass_predictions.csv"),
    Path("docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv"),
    Path("docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv"),
]:
    with p.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(p.name, "rows=", len(rows))
    if len(rows) <= 0:
        raise SystemExit(f"ERROR: empty output {p}")

report = json.loads(Path("docs/idare_minimal_supcon_dg_first_pass_report.json").read_text(encoding="utf-8"))
if report.get("expanded_run_count", 0) <= 0:
    raise SystemExit("ERROR: missing expanded_run_count")
if not report.get("diagnosis"):
    raise SystemExit("ERROR: missing diagnosis")
if not report.get("recommended_next_objective"):
    raise SystemExit("ERROR: missing recommended_next_objective")
print("diagnosis=", report["diagnosis"])
print("recommended_next_objective=", report["recommended_next_objective"])
print("ALL_MINIMAL_SUPCON_DG_FIRST_PASS_OUTPUTS_VALID")
PY

grep -n "## Status\|## Run Matrix\|## Aggregate Results\|## Diagnosis\|## Recommended Next Objective\|## Next Allowed Step" docs/idare_minimal_supcon_dg_first_pass_report.md
grep -n "minimal SupCon/DG first-pass training report\|Minimal SupCon/DG first-pass diagnostic training" docs/project_status_current.md
echo

echo "===== 6) file list ====="
ls -lh \
  docs/idare_minimal_supcon_dg_first_pass_report.md \
  docs/idare_minimal_supcon_dg_first_pass_report.json \
  docs/idare_minimal_supcon_dg_first_pass_runs.csv \
  docs/idare_minimal_supcon_dg_first_pass_predictions.csv \
  docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv \
  docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 7) status before commit ====="
git status --short --branch
echo

echo "===== 8) commit and push first-pass outputs ====="
git add \
  docs/idare_minimal_supcon_dg_first_pass_report.md \
  docs/idare_minimal_supcon_dg_first_pass_report.json \
  docs/idare_minimal_supcon_dg_first_pass_runs.csv \
  docs/idare_minimal_supcon_dg_first_pass_predictions.csv \
  docs/idare_minimal_supcon_dg_first_pass_embedding_summary.csv \
  docs/idare_minimal_supcon_dg_first_pass_loss_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "exp: run I-DARE minimal SupCon DG first pass"

git push origin main
echo

echo "===== 9) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_minimal_supcon_dg_first_pass_run.log"
