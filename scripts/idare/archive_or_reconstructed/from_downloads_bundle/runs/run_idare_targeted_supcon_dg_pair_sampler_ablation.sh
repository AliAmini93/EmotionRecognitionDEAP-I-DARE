#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_targeted_supcon_dg_pair_sampler_ablation_run.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start targeted SupCon/DG pair-sampler ablation run ====="
date
git status --short --branch
echo

echo "===== 1) choose python and require clean repo ====="
PY="${PY:-.venv/bin/python}"
if [[ ! -x "$PY" ]]; then
  PY="$(command -v python3)"
fi
echo "PY=$PY"
"$PY" - <<'PY'
import json, csv, pathlib
import numpy as np
import pandas as pd
import torch
print("torch_cuda_available=", torch.cuda.is_available())
print("OK_IMPORTS")
PY

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: repo is not clean; commit/stash before running this ablation script." >&2
  git status --short
  exit 2
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required inputs ====="
required=(
  .cache/idare_eeg_cache_index_baseline_corrected.csv
  .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy
  .cache/idare_emg_feature_cache_index.csv
  .cache/idare_emg_features.npy
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_objective.md
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_objective.json
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_run_matrix.csv
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_guardrails.csv
  docs/idare_targeted_supcon_dg_pair_sampler_smoke_test_plan.csv
  docs/idare_targeted_supcon_dg_pair_sampler_decision_tree.csv
  docs/idare_minimal_supcon_dg_first_pass_report.json
  docs/idare_supcon_dg_failure_analysis_report.json
  docs/project_status_current.json
  docs/project_status_current.md
)
for f in "${required[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "ERROR: missing required input: $f" >&2
    exit 3
  fi
  ls -lh "$f"
done
echo

echo "===== 3) remove stale outputs ====="
rm -f \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv
echo "OK_CLEAN_OUTPUT_TARGETS"
echo

echo "===== 4) run guardrailed targeted pair/sampler ablation ====="
"$PY" - <<'PY'
import csv
import json
import math
import random
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn
import torch.nn.functional as F

DOCS = Path("docs")
TMP = Path("/tmp/idare_targeted_supcon_dg_pair_sampler_ablation")
TMP.mkdir(parents=True, exist_ok=True)

SEED = 11
EPOCHS_DEFAULT = 12
BATCH_SIZE = 128
LR = 1e-3
WEIGHT_DECAY = 1e-4
EMBED_DIM = 32
HIDDEN_DIM = 128

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("device=", device)

# Official authorized subject folds used throughout current I-DARE diagnostics.
FOLDS = {
    1: [6, 7, 8, 13, 28, 38, 43, 54, 58, 59, 65],
    2: [2, 5, 11, 17, 26, 31, 34, 44, 46, 49, 63],
    3: [9, 10, 20, 35, 39, 45, 47, 48, 52, 57, 62],
    4: [1, 3, 19, 25, 36, 40, 42, 53, 55, 61],
    5: [14, 23, 24, 27, 29, 30, 37, 56, 60, 64],
    6: [12, 15, 16, 18, 21, 22, 32, 33, 41, 50],
}

paths = {
    "run_matrix": DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_run_matrix.csv",
    "objective_json": DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_objective.json",
    "decision_tree": DOCS / "idare_targeted_supcon_dg_pair_sampler_decision_tree.csv",
    "first_pass_report": DOCS / "idare_minimal_supcon_dg_first_pass_report.json",
    "failure_report": DOCS / "idare_supcon_dg_failure_analysis_report.json",
    "eeg_index": Path(".cache/idare_eeg_cache_index_baseline_corrected.csv"),
    "eeg_npy": Path(".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy"),
    "emg_index": Path(".cache/idare_emg_feature_cache_index.csv"),
    "emg_npy": Path(".cache/idare_emg_features.npy"),
}

objective = json.loads(paths["objective_json"].read_text(encoding="utf-8"))
run_matrix = pd.read_csv(paths["run_matrix"])
if len(run_matrix) != 120:
    raise SystemExit(f"ERROR: expected 120 run matrix rows, got {len(run_matrix)}")

# ---- helpers ----
def safe_col(df, candidates, required=True):
    for c in candidates:
        if c in df.columns:
            return c
    if required:
        raise KeyError(f"none of columns found: {candidates}; available={list(df.columns)}")
    return None

def infer_score_col(df, task):
    return safe_col(df, [f"{task}_score", task, f"{task}_rating", f"{task}_label_raw"])

def labels_from_scores(scores):
    scores = np.asarray(scores, dtype=np.float32)
    # Continuity with previous I-DARE smoke/default policy: midpoint_as_high.
    return (scores >= 5.0).astype(np.int64)

def macro_f1_np(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=np.int64)
    y_pred = np.asarray(y_pred, dtype=np.int64)
    out = []
    for cls in [0, 1]:
        tp = int(((y_true == cls) & (y_pred == cls)).sum())
        fp = int(((y_true != cls) & (y_pred == cls)).sum())
        fn = int(((y_true == cls) & (y_pred != cls)).sum())
        denom = 2 * tp + fp + fn
        out.append((2 * tp / denom) if denom else 0.0)
    return float(np.mean(out))

def balanced_acc_np(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=np.int64)
    y_pred = np.asarray(y_pred, dtype=np.int64)
    vals = []
    for cls in [0, 1]:
        denom = int((y_true == cls).sum())
        vals.append(float(((y_true == cls) & (y_pred == cls)).sum() / denom) if denom else 0.0)
    return float(np.mean(vals))

def acc_np(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=np.int64)
    y_pred = np.asarray(y_pred, dtype=np.int64)
    return float((y_true == y_pred).mean()) if len(y_true) else 0.0

def md_table(rows, columns):
    if not rows:
        return "_No rows._"
    widths = {}
    for c in columns:
        widths[c] = max(len(str(c)), max(len(str(r.get(c, ""))) for r in rows))
    sep = "| " + " | ".join(str(c).ljust(widths[c]) for c in columns) + " |"
    bar = "| " + " | ".join("-" * widths[c] for c in columns) + " |"
    lines = [sep, bar]
    for r in rows:
        lines.append("| " + " | ".join(str(r.get(c, "")).ljust(widths[c]) for c in columns) + " |")
    return "\n".join(lines)

def confusion_counts(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=np.int64)
    y_pred = np.asarray(y_pred, dtype=np.int64)
    return {
        "tn": int(((y_true == 0) & (y_pred == 0)).sum()),
        "fp": int(((y_true == 0) & (y_pred == 1)).sum()),
        "fn": int(((y_true == 1) & (y_pred == 0)).sum()),
        "tp": int(((y_true == 1) & (y_pred == 1)).sum()),
    }

# ---- feature building ----
def build_eeg_summary_features():
    cache = TMP / "eeg_summary_features_float32.npy"
    if cache.exists():
        return np.load(cache, mmap_mode="r")
    print("BUILDING_EEG_SUMMARY_FEATURES")
    x = np.load(paths["eeg_npy"], mmap_mode="r")
    # robust, lightweight summary: channel mean/std/min/max/energy across time.
    mean = x.mean(axis=2)
    std = x.std(axis=2)
    mn = x.min(axis=2)
    mx = x.max(axis=2)
    energy = np.sqrt((x.astype(np.float32) ** 2).mean(axis=2))
    feat = np.concatenate([mean, std, mn, mx, energy], axis=1).astype(np.float32)
    np.save(cache, feat)
    return np.load(cache, mmap_mode="r")

def build_emg_features():
    cache = TMP / "emg_signed_log1p_float32.npy"
    if cache.exists():
        return np.load(cache, mmap_mode="r")
    print("BUILDING_EMG_SIGNED_LOG1P_FEATURES")
    x = np.load(paths["emg_npy"]).astype(np.float32)
    feat = np.sign(x) * np.log1p(np.abs(x))
    np.save(cache, feat.astype(np.float32))
    return np.load(cache, mmap_mode="r")

eeg_index = pd.read_csv(paths["eeg_index"])
emg_index = pd.read_csv(paths["emg_index"])
subject_col_eeg = safe_col(eeg_index, ["subject_id", "subject", "subj"])
subject_col_emg = safe_col(emg_index, ["subject_id", "subject", "subj"])

features = {
    "EEG": build_eeg_summary_features(),
    "EMG": build_emg_features(),
}
indices = {
    "EEG": eeg_index,
    "EMG": emg_index,
}
subject_cols = {
    "EEG": subject_col_eeg,
    "EMG": subject_col_emg,
}

# ---- model/loss ----
class MLP(nn.Module):
    def __init__(self, in_dim, hidden_dim=HIDDEN_DIM, embed_dim=EMBED_DIM):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.15),
            nn.Linear(hidden_dim, embed_dim),
            nn.ReLU(),
        )
        self.head = nn.Linear(embed_dim, 2)

    def forward(self, x):
        z = self.net(x)
        logits = self.head(z)
        return logits, z

def supcon_loss(z, y, subjects, ratings, candidate_id, temperature=0.10):
    # z: [B,D], y: [B], subjects: [B], ratings: [B]
    if z.shape[0] < 4:
        return z.new_tensor(0.0), 0.0, 0
    z = F.normalize(z, dim=1)
    sim = torch.matmul(z, z.t()) / temperature
    B = z.shape[0]
    eye = torch.eye(B, dtype=torch.bool, device=z.device)
    same_label = y[:, None].eq(y[None, :])
    diff_subject = subjects[:, None].ne(subjects[None, :])
    pos_mask = same_label & (~eye)

    if candidate_id in {"A2_cross_subject_positive_only", "A5_cross_subject_supcon_vrex"}:
        pos_mask = pos_mask & diff_subject
    elif candidate_id == "A4_rating_distance_guarded_supcon":
        rating_dist = torch.abs(ratings[:, None] - ratings[None, :])
        pos_mask = pos_mask & diff_subject & (rating_dist <= 1.5)
    elif candidate_id in {"A0_CE_control", "A6_vrex_only_recheck"}:
        return z.new_tensor(0.0), 0.0, 0
    else:
        # Conservative default: cross-subject same label.
        pos_mask = pos_mask & diff_subject

    pos_counts = pos_mask.sum(dim=1)
    usable = pos_counts > 0
    if usable.sum().item() == 0:
        return z.new_tensor(0.0), 0.0, 0

    logits = sim.masked_fill(eye, -1e9)
    log_prob = logits - torch.logsumexp(logits, dim=1, keepdim=True)
    pos_log_prob = (log_prob * pos_mask.float()).sum(dim=1) / pos_counts.clamp_min(1).float()
    loss = -pos_log_prob[usable].mean()
    coverage = float(usable.float().mean().detach().cpu().item())
    return loss, coverage, int(usable.sum().detach().cpu().item())

def vrex_penalty(ce_per_sample, subjects):
    uniq = torch.unique(subjects)
    group_losses = []
    for s in uniq:
        mask = subjects == s
        if mask.sum().item() >= 2:
            group_losses.append(ce_per_sample[mask].mean())
    if len(group_losses) < 2:
        return ce_per_sample.new_tensor(0.0), 0
    g = torch.stack(group_losses)
    return g.var(unbiased=False), len(group_losses)

def make_batches(train_idx, y_train, subj_train, ratings_train, candidate_id, batch_size=BATCH_SIZE):
    rng = np.random.default_rng(SEED)
    train_idx = np.asarray(train_idx, dtype=np.int64)
    y_train = np.asarray(y_train, dtype=np.int64)
    subj_train = np.asarray(subj_train, dtype=np.int64)
    ratings_train = np.asarray(ratings_train, dtype=np.float32)

    # Balanced-by-class batches. This is intentionally simple and auditable.
    by_class = {c: train_idx[y_train == c] for c in [0, 1]}
    n_batches = max(1, int(math.ceil(len(train_idx) / batch_size)))
    half = max(2, batch_size // 2)

    batches = []
    for _ in range(n_batches):
        parts = []
        for cls in [0, 1]:
            pool = by_class[cls]
            if len(pool) == 0:
                continue
            take = min(half, len(pool))
            replace = len(pool) < take
            parts.append(rng.choice(pool, size=take, replace=replace))
        if not parts:
            continue
        b = np.concatenate(parts)
        rng.shuffle(b)
        batches.append(b.astype(np.int64))
    return batches

def fit_predict_one(modality, task, fold, candidate):
    df = indices[modality].copy()
    x_all = np.asarray(features[modality], dtype=np.float32)
    subj_col = subject_cols[modality]
    score_col = infer_score_col(df, task)
    subjects = df[subj_col].astype(int).to_numpy()
    ratings = df[score_col].astype(float).to_numpy()
    labels = labels_from_scores(ratings)

    valid = np.isfinite(ratings)
    val_subjects = np.array(FOLDS[int(fold)], dtype=np.int64)
    val_mask = np.isin(subjects, val_subjects) & valid
    train_mask = (~np.isin(subjects, val_subjects)) & valid

    train_idx = np.where(train_mask)[0]
    val_idx = np.where(val_mask)[0]
    if len(train_idx) == 0 or len(val_idx) == 0:
        raise RuntimeError(f"empty split modality={modality} task={task} fold={fold}")

    # Train-fold-only standard scaling.
    mu = x_all[train_idx].mean(axis=0)
    sd = x_all[train_idx].std(axis=0)
    sd = np.where(sd < 1e-6, 1.0, sd)

    x_train = ((x_all[train_idx] - mu) / sd).astype(np.float32)
    x_val = ((x_all[val_idx] - mu) / sd).astype(np.float32)
    y_train = labels[train_idx].astype(np.int64)
    y_val = labels[val_idx].astype(np.int64)
    subj_train = subjects[train_idx].astype(np.int64)
    subj_val = subjects[val_idx].astype(np.int64)
    rating_train = ratings[train_idx].astype(np.float32)
    rating_val = ratings[val_idx].astype(np.float32)

    # Convert original row ids to local train array positions for batching.
    orig_to_local = {int(orig): i for i, orig in enumerate(train_idx)}
    batches_orig = make_batches(train_idx, y_train, subj_train, rating_train, candidate["candidate_id"])
    batches_local = [np.array([orig_to_local[int(o)] for o in b if int(o) in orig_to_local], dtype=np.int64) for b in batches_orig]
    batches_local = [b for b in batches_local if len(b) >= 4]

    model = MLP(x_train.shape[1]).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)

    method = candidate["candidate_id"]
    use_supcon = "SupCon" in str(candidate.get("loss", "")) or "supcon" in str(candidate.get("method_family", "")).lower()
    use_vrex = "VREx" in str(candidate.get("loss", "")) or "vrex" in str(candidate.get("dg_regularizer", "")).lower() or "vrex" in str(candidate.get("method_family", "")).lower()
    lam_supcon = float(candidate.get("lambda_supcon", 0.10)) if use_supcon else 0.0
    lam_vrex = float(candidate.get("lambda_vrex", 0.10)) if use_vrex else 0.0
    temp = float(candidate.get("temperature", 0.10))
    epochs = int(candidate.get("epochs", EPOCHS_DEFAULT))

    Xtr = torch.tensor(x_train, device=device)
    ytr = torch.tensor(y_train, device=device)
    strn = torch.tensor(subj_train, device=device)
    rtr = torch.tensor(rating_train, device=device)

    loss_rows = []
    for epoch in range(1, epochs + 1):
        model.train()
        rng = np.random.default_rng(SEED + epoch)
        rng.shuffle(batches_local)
        ce_vals, sup_vals, vrex_vals, cov_vals = [], [], [], []
        for b in batches_local:
            xb = Xtr[b]
            yb = ytr[b]
            sb = strn[b]
            rb = rtr[b]

            opt.zero_grad(set_to_none=True)
            logits, z = model(xb)
            ce_per = F.cross_entropy(logits, yb, reduction="none")
            ce = ce_per.mean()
            sup, cov, usable = supcon_loss(z, yb, sb, rb, method, temperature=temp)
            vr, n_groups = vrex_penalty(ce_per, sb)
            loss = ce + lam_supcon * sup + lam_vrex * vr
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()

            ce_vals.append(float(ce.detach().cpu()))
            sup_vals.append(float(sup.detach().cpu()))
            vrex_vals.append(float(vr.detach().cpu()))
            cov_vals.append(float(cov))

        loss_rows.append({
            "epoch": epoch,
            "ce_loss": float(np.mean(ce_vals)) if ce_vals else None,
            "supcon_loss": float(np.mean(sup_vals)) if sup_vals else None,
            "vrex_penalty": float(np.mean(vrex_vals)) if vrex_vals else None,
            "positive_pair_coverage": float(np.mean(cov_vals)) if cov_vals else 0.0,
        })

    model.eval()
    with torch.no_grad():
        Xv = torch.tensor(x_val, device=device)
        logits, emb = model(Xv)
        probs = F.softmax(logits, dim=1)[:, 1].detach().cpu().numpy()
        pred = (probs >= 0.5).astype(np.int64)
        emb_np = emb.detach().cpu().numpy()

    metrics = {
        "accuracy": acc_np(y_val, pred),
        "balanced_accuracy": balanced_acc_np(y_val, pred),
        "macro_f1": macro_f1_np(y_val, pred),
        "one_class_pred": bool(len(set(pred.tolist())) == 1),
        "confusion": confusion_counts(y_val, pred),
        "n_train": int(len(train_idx)),
        "n_val": int(len(val_idx)),
        "val_subjects": val_subjects.tolist(),
        "positive_pair_coverage_final_epoch": loss_rows[-1]["positive_pair_coverage"] if loss_rows else 0.0,
        "embedding_norm_mean": float(np.linalg.norm(emb_np, axis=1).mean()),
        "embedding_norm_std": float(np.linalg.norm(emb_np, axis=1).std()),
    }

    pred_rows = []
    for j, orig_idx in enumerate(val_idx):
        pred_rows.append({
            "modality": modality,
            "task": task,
            "fold": int(fold),
            "candidate_id": method,
            "row_index": int(orig_idx),
            "subject_id": int(subjects[orig_idx]),
            "rating": float(ratings[orig_idx]),
            "y_true": int(y_val[j]),
            "y_pred": int(pred[j]),
            "prob_high": float(probs[j]),
        })

    return metrics, pred_rows, loss_rows

def pair_audit_for(modality, task, fold, candidate):
    df = indices[modality]
    subj_col = subject_cols[modality]
    score_col = infer_score_col(df, task)
    subjects = df[subj_col].astype(int).to_numpy()
    ratings = df[score_col].astype(float).to_numpy()
    labels = labels_from_scores(ratings)
    valid = np.isfinite(ratings)
    val_subjects = np.array(FOLDS[int(fold)], dtype=np.int64)
    train_mask = (~np.isin(subjects, val_subjects)) & valid
    idx = np.where(train_mask)[0]
    rng = np.random.default_rng(SEED + int(fold))
    if len(idx) > 512:
        idx = rng.choice(idx, size=512, replace=False)
    y = labels[idx]
    s = subjects[idx]
    r = ratings[idx]
    same = y[:, None] == y[None, :]
    diff_s = s[:, None] != s[None, :]
    eye = np.eye(len(idx), dtype=bool)
    pos = same & (~eye)
    cid = candidate["candidate_id"]
    if cid in {"A2_cross_subject_positive_only", "A5_cross_subject_supcon_vrex"}:
        pos = pos & diff_s
    elif cid == "A4_rating_distance_guarded_supcon":
        pos = pos & diff_s & (np.abs(r[:, None] - r[None, :]) <= 1.5)
    elif cid in {"A0_CE_control", "A6_vrex_only_recheck"}:
        pos = np.zeros_like(pos, dtype=bool)

    anchors_with_pos = (pos.sum(axis=1) > 0)
    coverage = float(anchors_with_pos.mean()) if len(idx) else 0.0
    mean_pos = float(pos.sum(axis=1).mean()) if len(idx) else 0.0
    return {
        "modality": modality,
        "task": task,
        "fold": int(fold),
        "candidate_id": cid,
        "audit_n": int(len(idx)),
        "anchor_positive_coverage": coverage,
        "mean_positive_count": mean_pos,
        "train_subject_count": int(len(set(s.tolist()))),
        "class0_count": int((y == 0).sum()),
        "class1_count": int((y == 1).sum()),
        "passed": bool((cid in {"A0_CE_control", "A6_vrex_only_recheck"}) or coverage >= 0.95),
    }

# ---- pre-training smoke / guardrail ----
smoke_rows = []
pair_audit_rows = []

for _, row in run_matrix.iterrows():
    row = row.to_dict()
    fold = int(row["fold"])
    modality = str(row["modality"])
    task = str(row["task"])
    cid = str(row["candidate_id"])
    df = indices[modality]
    subjects = df[subject_cols[modality]].astype(int).to_numpy()
    val_subjects = set(FOLDS[fold])
    train_subjects = set(int(x) for x in subjects if int(x) not in val_subjects)
    subject_overlap = len(train_subjects.intersection(val_subjects))

    audit = pair_audit_for(modality, task, fold, row)
    pair_audit_rows.append(audit)

    smoke_rows.append({
        "smoke_id": "leakage_guard",
        "candidate_id": cid,
        "modality": modality,
        "task": task,
        "fold": fold,
        "metric": "subject_overlap",
        "value": subject_overlap,
        "passed": subject_overlap == 0,
    })
    smoke_rows.append({
        "smoke_id": "pair_coverage_guard",
        "candidate_id": cid,
        "modality": modality,
        "task": task,
        "fold": fold,
        "metric": "anchor_positive_coverage",
        "value": audit["anchor_positive_coverage"],
        "passed": audit["passed"],
    })

bad_smokes = [r for r in smoke_rows if not r["passed"]]
# Allow CE and VREx rows to have zero SupCon coverage; pair audit pass handles this.
if bad_smokes:
    pd.DataFrame(smoke_rows).to_csv(DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv", index=False)
    pd.DataFrame(pair_audit_rows).to_csv(DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv", index=False)
    print("FAILED_SMOKES=", len(bad_smokes))
    for r in bad_smokes[:10]:
        print(r)
    raise SystemExit("ERROR: smoke tests failed; training blocked")

print("OK_REQUIRED_SMOKES_PASSED", "rows=", len(smoke_rows))
pd.DataFrame(smoke_rows).to_csv(DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv", index=False)

# ---- training ----
run_records = []
prediction_rows = []
loss_embedding_rows = []
start = time.time()

for _, row in run_matrix.iterrows():
    candidate = row.to_dict()
    run_id = int(candidate["planned_run_id"])
    modality = str(candidate["modality"])
    task = str(candidate["task"])
    fold = int(candidate["fold"])
    cid = str(candidate["candidate_id"])
    metrics, pred_rows, loss_rows = fit_predict_one(modality, task, fold, candidate)

    rec = {
        "run_id": run_id,
        "candidate_id": cid,
        "method_family": candidate.get("method_family", ""),
        "modality": modality,
        "task": task,
        "fold": fold,
        "accuracy": metrics["accuracy"],
        "balanced_accuracy": metrics["balanced_accuracy"],
        "macro_f1": metrics["macro_f1"],
        "one_class_pred": metrics["one_class_pred"],
        "n_train": metrics["n_train"],
        "n_val": metrics["n_val"],
        "positive_pair_coverage_final_epoch": metrics["positive_pair_coverage_final_epoch"],
        "embedding_norm_mean": metrics["embedding_norm_mean"],
        "embedding_norm_std": metrics["embedding_norm_std"],
        "confusion_json": json.dumps(metrics["confusion"], sort_keys=True),
    }
    run_records.append(rec)
    prediction_rows.extend([{"run_id": run_id, **p} for p in pred_rows])

    for lr in loss_rows:
        loss_embedding_rows.append({
            "run_id": run_id,
            "candidate_id": cid,
            "modality": modality,
            "task": task,
            "fold": fold,
            **lr,
        })

    print(json.dumps({
        "run_id": run_id,
        "candidate_id": cid,
        "modality": modality,
        "task": task,
        "fold": fold,
        "macro_f1": round(metrics["macro_f1"], 4),
        "bal_acc": round(metrics["balanced_accuracy"], 4),
        "acc": round(metrics["accuracy"], 4),
        "one_class_pred": metrics["one_class_pred"],
        "pos_cov": round(metrics["positive_pair_coverage_final_epoch"], 4),
    }, sort_keys=True), flush=True)

runs_df = pd.DataFrame(run_records)
pred_df = pd.DataFrame(prediction_rows)
loss_df = pd.DataFrame(loss_embedding_rows)
pair_audit_df = pd.DataFrame(pair_audit_rows)

runs_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv"
pred_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv"
pair_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv"
loss_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv"
report_json_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_report.json"
report_md_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_report.md"

runs_df.to_csv(runs_path, index=False)
pred_df.to_csv(pred_path, index=False)
pair_audit_df.to_csv(pair_path, index=False)
loss_df.to_csv(loss_path, index=False)

summary = (
    runs_df.groupby(["candidate_id", "modality", "task"], dropna=False)
    .agg(
        n_runs=("run_id", "count"),
        mean_macro_f1=("macro_f1", "mean"),
        std_macro_f1=("macro_f1", "std"),
        mean_balanced_accuracy=("balanced_accuracy", "mean"),
        mean_accuracy=("accuracy", "mean"),
        folds_over_055_macro_f1=("macro_f1", lambda s: int((s >= 0.55).sum())),
        folds_under_050_macro_f1=("macro_f1", lambda s: int((s < 0.50).sum())),
        one_class_pred_count=("one_class_pred", "sum"),
        mean_positive_pair_coverage=("positive_pair_coverage_final_epoch", "mean"),
    )
    .reset_index()
)
summary_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv"
summary.to_csv(summary_path, index=False)

# Candidate-level aggregate.
candidate_summary = (
    runs_df.groupby(["candidate_id"], dropna=False)
    .agg(
        n_runs=("run_id", "count"),
        mean_macro_f1=("macro_f1", "mean"),
        mean_balanced_accuracy=("balanced_accuracy", "mean"),
        mean_accuracy=("accuracy", "mean"),
        folds_over_055_macro_f1=("macro_f1", lambda s: int((s >= 0.55).sum())),
        folds_under_050_macro_f1=("macro_f1", lambda s: int((s < 0.50).sum())),
        one_class_pred_count=("one_class_pred", "sum"),
        mean_positive_pair_coverage=("positive_pair_coverage_final_epoch", "mean"),
    )
    .reset_index()
    .sort_values(["mean_macro_f1", "mean_balanced_accuracy"], ascending=False)
)
candidate_summary_path = DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv"
candidate_summary.to_csv(candidate_summary_path, index=False)

best_cell = summary.sort_values(["mean_macro_f1", "mean_balanced_accuracy"], ascending=False).iloc[0].to_dict()
best_candidate = candidate_summary.iloc[0].to_dict()

# Simple decision.
ce_mean = float(candidate_summary.loc[candidate_summary["candidate_id"] == "A0_CE_control", "mean_macro_f1"].iloc[0])
best_mean = float(best_candidate["mean_macro_f1"])
gain_vs_ce = best_mean - ce_mean
if gain_vs_ce >= 0.03 and int(best_candidate["folds_under_050_macro_f1"]) <= 8:
    diagnosis = "targeted_pair_sampler_candidate_promising_but_requires_confirmation"
    recommended_next_objective = "targeted_pair_sampler_confirmation_objective"
elif gain_vs_ce >= 0.015:
    diagnosis = "targeted_pair_sampler_ablation_inconclusive_small_gain"
    recommended_next_objective = "targeted_pair_sampler_failure_analysis_or_confirmation"
else:
    diagnosis = "targeted_pair_sampler_ablation_not_sufficient"
    recommended_next_objective = "supcon_dg_pair_sampler_failure_analysis_objective"

report = {
    "status": "complete_pending_human_review",
    "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    "objective": str(paths["run_matrix"]),
    "n_runs": int(len(runs_df)),
    "n_predictions": int(len(pred_df)),
    "n_loss_rows": int(len(loss_df)),
    "n_pair_audit_rows": int(len(pair_audit_df)),
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next_objective,
    "best_cell": best_cell,
    "best_candidate": best_candidate,
    "gain_vs_ce_macro_f1": gain_vs_ce,
    "outputs": {
        "runs": str(runs_path),
        "predictions": str(pred_path),
        "pair_audit": str(pair_path),
        "loss_embedding_summary": str(loss_path),
        "method_task_summary": str(summary_path),
        "candidate_summary": str(candidate_summary_path),
        "smoke_summary": str(DOCS / "idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv"),
    },
    "blocked": [
        "direct full SupCon/DG training",
        "broad hyperparameter search",
        "EEG+EMG fusion",
        "final LOSO claim",
        "mainline change",
    ],
}
report_json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

top_rows = []
for _, r in summary.sort_values(["mean_macro_f1", "mean_balanced_accuracy"], ascending=False).head(12).iterrows():
    top_rows.append({
        "candidate": r["candidate_id"],
        "modality": r["modality"],
        "task": r["task"],
        "macro_f1": f"{r['mean_macro_f1']:.4f}",
        "bal_acc": f"{r['mean_balanced_accuracy']:.4f}",
        "acc": f"{r['mean_accuracy']:.4f}",
        "over_055": int(r["folds_over_055_macro_f1"]),
        "under_050": int(r["folds_under_050_macro_f1"]),
    })

cand_rows = []
for _, r in candidate_summary.iterrows():
    cand_rows.append({
        "candidate": r["candidate_id"],
        "n": int(r["n_runs"]),
        "macro_f1": f"{r['mean_macro_f1']:.4f}",
        "bal_acc": f"{r['mean_balanced_accuracy']:.4f}",
        "gain_vs_ce": f"{(float(r['mean_macro_f1']) - ce_mean):+.4f}",
        "over_055": int(r["folds_over_055_macro_f1"]),
        "under_050": int(r["folds_under_050_macro_f1"]),
    })

md = f"""# I-DARE Targeted SupCon/DG Pair-Sampler Ablation Report

## Status

Status: complete; pending human review.

Runs completed: `{len(runs_df)}`
Predictions written: `{len(pred_df)}`
Runtime seconds: `{time.time() - start:.1f}`

## Executive Diagnosis

Diagnosis: `{diagnosis}`

Recommended next objective: `{recommended_next_objective}`

Best candidate aggregate:

`{best_candidate['candidate_id']}` with mean macro-F1 `{float(best_candidate['mean_macro_f1']):.4f}` and mean balanced accuracy `{float(best_candidate['mean_balanced_accuracy']):.4f}`.

Gain vs CE control by candidate aggregate: `{gain_vs_ce:+.4f}` macro-F1.

## Candidate-level Summary

{md_table(cand_rows, ["candidate", "n", "macro_f1", "bal_acc", "gain_vs_ce", "over_055", "under_050"])}

## Top Method/Task Cells

{md_table(top_rows, ["candidate", "modality", "task", "macro_f1", "bal_acc", "acc", "over_055", "under_050"])}

## Outputs

- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv`

## Interpretation Rules

This is a diagnostic ablation only. It does not authorize direct full SupCon/DG training.

A promising candidate must show consistent gains across tasks/folds, not only a single lucky fold.

## Blocked Until Review

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change

## Next Allowed Step

Human review / closeout before confirmation or failure-analysis objective.
"""
report_md_path.write_text(md, encoding="utf-8")

# Update project status.
status_path = DOCS / "project_status_current.json"
status_md_path = DOCS / "project_status_current.md"
status = json.loads(status_path.read_text(encoding="utf-8"))
now = report["created_utc"]
event = {
    "timestamp_utc": now,
    "type": "analysis_report",
    "name": "I-DARE targeted SupCon/DG pair-sampler ablation report",
    "status": f"complete pending human review; diagnosis={diagnosis}",
    "evidence": str(report_md_path),
    "next_allowed_step": "human_review_closeout_before_confirmation_or_failure_analysis",
    "blocked": report["blocked"],
}
status["last_updated_utc"] = now
status.setdefault("idare_protocol_events", []).append(event)
status["current_idare_next_allowed_step"] = "human_review_closeout_before_confirmation_or_failure_analysis"
status["current_idare_blocked_steps"] = report["blocked"]
status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

status_md = status_md_path.read_text(encoding="utf-8")
append = f"""

## I-DARE Targeted SupCon/DG Pair-Sampler Ablation Report

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE targeted SupCon/DG pair-sampler ablation report | complete pending human review; diagnosis=`{diagnosis}` | `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md` | Human review / closeout before confirmation or failure-analysis objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Targeted pair/sampler ablation is complete in `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md`.
- Best aggregate candidate is `{best_candidate['candidate_id']}`; full training remains blocked pending review.
"""
if "I-DARE Targeted SupCon/DG Pair-Sampler Ablation Report" not in status_md:
    status_md_path.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")
else:
    status_md_path.write_text(status_md, encoding="utf-8")

print("OK_TARGETED_SUPCON_DG_PAIR_SAMPLER_ABLATION_REPORT_WRITTEN")
print(report_md_path)
print(report_json_path)
print("runs=", len(runs_df))
print("predictions=", len(pred_df))
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next_objective)
print("best_candidate=", json.dumps(best_candidate, sort_keys=True))
PY

echo

echo "===== 5) validate outputs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path

json_paths = [
    Path("docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

checks = [
    ("docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv", 120),
    ("docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv", 120),
    ("docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv", 120),
    ("docs/idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv", 20),
    ("docs/idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv", 5),
]
for path, min_rows in checks:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(Path(path).name, "rows=", len(rows))
    if len(rows) < min_rows:
        raise SystemExit(f"ERROR: {path} expected at least {min_rows} rows, got {len(rows)}")

with open("docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv", newline="", encoding="utf-8") as f:
    pred_rows = sum(1 for _ in f) - 1
print("idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv rows=", pred_rows)
if pred_rows <= 0:
    raise SystemExit("ERROR: no prediction rows")

report = json.loads(Path("docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json").read_text(encoding="utf-8"))
print("diagnosis=", report.get("diagnosis"))
print("recommended_next_objective=", report.get("recommended_next_objective"))
if report.get("n_runs") != 120:
    raise SystemExit(f"ERROR: expected n_runs=120, got {report.get('n_runs')}")

text = Path("docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md").read_text(encoding="utf-8")
for term in ["Executive Diagnosis", "Candidate-level Summary", "direct full SupCon/DG training", "Next Allowed Step"]:
    if term not in text:
        raise SystemExit(f"ERROR: missing term in report: {term}")

print("ALL_TARGETED_SUPCON_DG_PAIR_SAMPLER_ABLATION_OUTPUTS_VALID")
PY

grep -nE "Status|Executive Diagnosis|Candidate-level Summary|Top Method|Next Allowed Step" \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md
grep -nE "targeted SupCon/DG pair-sampler ablation report" docs/project_status_current.md | tail -n 10
echo

echo "===== 6) file list ====="
ls -lh \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv \
  docs/project_status_current.json \
  docs/project_status_current.md
echo

echo "===== 7) status before commit ====="
git status --short --branch
echo

echo "===== 8) commit and push targeted ablation outputs ====="
git add \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_method_task_summary.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv \
  docs/idare_targeted_supcon_dg_pair_sampler_ablation_smoke_summary.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "exp: run I-DARE targeted SupCon DG pair sampler ablation"
git push origin main
echo

echo "===== 9) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
