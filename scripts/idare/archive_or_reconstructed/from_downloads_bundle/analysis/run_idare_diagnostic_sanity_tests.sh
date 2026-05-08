#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start I-DARE diagnostic sanity tests ====="
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
from pathlib import Path
try:
    import numpy as np
    import pandas as pd
    import torch
except Exception as e:
    print("IMPORT_ERROR:", repr(e))
    raise
print("OK_IMPORTS")
print("cuda_available=", torch.cuda.is_available())
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repo is not clean; commit/stash current changes before running diagnostic sanity tests."
  git status --short --branch
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required artifacts ====="
ls -lh \
  .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy \
  .cache/idare_eeg_cache_index_baseline_corrected.csv \
  .cache/idare_emg_features.npy \
  .cache/idare_emg_feature_cache_index.csv \
  docs/idare_diagnostic_sanity_tests_objective.md \
  docs/idare_diagnostic_sanity_tests_objective.json \
  docs/idare_root_cause_diagnostic_review_status.md \
  docs/idare_root_cause_diagnostic_report.md
echo

echo "===== 3) run diagnostic sanity tests and write report ====="
"$PY" - <<'PY'
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

ROOT = Path(".")
DOCS = ROOT / "docs"
CACHE = ROOT / ".cache"

OUT_MD = DOCS / "idare_diagnostic_sanity_tests_report.md"
OUT_JSON = DOCS / "idare_diagnostic_sanity_tests_report.json"
OUT_SUMMARY = DOCS / "idare_diagnostic_sanity_tests_summary.csv"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()
SEED = 11
POLICY = "midpoint_as_high"
TASKS = ["valence", "arousal"]
MODALITIES = ["EEG", "EMG"]

required = [
    CACHE / "idare_eeg_windows_32x640_float32_baseline_corrected.npy",
    CACHE / "idare_eeg_cache_index_baseline_corrected.csv",
    CACHE / "idare_emg_features.npy",
    CACHE / "idare_emg_feature_cache_index.csv",
    DOCS / "idare_diagnostic_sanity_tests_objective.md",
    DOCS / "idare_diagnostic_sanity_tests_objective.json",
    DOCS / "idare_root_cause_diagnostic_review_status.md",
    DOCS / "idare_root_cause_diagnostic_report.md",
    PROJECT_MD,
    PROJECT_JSON,
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("ERROR: missing required files:\n" + "\n".join(missing))

np.random.seed(SEED)
random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def safe_div(num: float, den: float) -> float:
    return float(num / den) if den else 0.0


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    n = int(len(y_true))
    if n == 0:
        return {
            "n": 0,
            "accuracy": math.nan,
            "balanced_accuracy": math.nan,
            "macro_f1": math.nan,
            "majority_accuracy": math.nan,
            "true_0": 0,
            "true_1": 0,
            "pred_0": 0,
            "pred_1": 0,
            "tn": 0,
            "fp": 0,
            "fn": 0,
            "tp": 0,
            "one_class_pred": False,
        }

    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tp = int(((y_true == 1) & (y_pred == 1)).sum())

    true_0 = int((y_true == 0).sum())
    true_1 = int((y_true == 1).sum())
    pred_0 = int((y_pred == 0).sum())
    pred_1 = int((y_pred == 1).sum())

    f1s = []
    recalls = []
    for label in [0, 1]:
        ltp = int(((y_true == label) & (y_pred == label)).sum())
        lfp = int(((y_true != label) & (y_pred == label)).sum())
        lfn = int(((y_true == label) & (y_pred != label)).sum())
        prec = safe_div(ltp, ltp + lfp)
        rec = safe_div(ltp, ltp + lfn)
        f1 = safe_div(2.0 * prec * rec, prec + rec)
        f1s.append(f1)
        recalls.append(rec)

    return {
        "n": n,
        "accuracy": float((y_true == y_pred).mean()),
        "balanced_accuracy": float(np.mean(recalls)),
        "macro_f1": float(np.mean(f1s)),
        "majority_accuracy": float(max(true_0, true_1) / n),
        "true_0": true_0,
        "true_1": true_1,
        "pred_0": pred_0,
        "pred_1": pred_1,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "one_class_pred": bool(len(set(y_pred.tolist())) == 1),
    }


def make_subject_folds(subjects: list[int], n_folds: int = 6, seed: int = 11) -> list[list[int]]:
    subjects_arr = np.asarray(sorted(set(int(s) for s in subjects)))
    rng = np.random.default_rng(seed)
    permuted = rng.permutation(subjects_arr)
    return [sorted(int(s) for s in chunk.tolist()) for chunk in np.array_split(permuted, n_folds)]


def standardize(train_x: np.ndarray, *arrays: np.ndarray) -> tuple[np.ndarray, ...]:
    mu = train_x.mean(axis=0, keepdims=True)
    sd = train_x.std(axis=0, keepdims=True)
    sd[sd < 1e-6] = 1.0
    out = [(arr - mu) / sd for arr in (train_x,) + arrays]
    return tuple(np.asarray(x, dtype=np.float32) for x in out)


class SmallMLP(torch.nn.Module):
    def __init__(self, input_dim: int, hidden: int = 64):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(input_dim, hidden),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden, 2),
        )

    def forward(self, x):
        return self.net(x)


def train_torch_classifier(
    train_x: np.ndarray,
    train_y: np.ndarray,
    eval_x: np.ndarray,
    epochs: int,
    lr: float,
    hidden: int = 64,
    shuffle_labels: bool = False,
) -> tuple[np.ndarray, dict[str, float]]:
    train_x = np.asarray(train_x, dtype=np.float32)
    eval_x = np.asarray(eval_x, dtype=np.float32)
    train_y = np.asarray(train_y, dtype=np.int64).copy()

    if shuffle_labels:
        rng = np.random.default_rng(SEED + 404)
        train_y = rng.permutation(train_y)

    model = SmallMLP(train_x.shape[1], hidden=hidden).to(DEVICE)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    x = torch.from_numpy(train_x).to(DEVICE)
    y = torch.from_numpy(train_y).to(DEVICE)

    class_counts = np.bincount(train_y, minlength=2).astype(np.float32)
    weights = class_counts.sum() / np.maximum(class_counts, 1.0)
    weights = weights / weights.mean()
    loss_fn = torch.nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=DEVICE))

    last_loss = math.nan
    for _ in range(epochs):
        model.train()
        opt.zero_grad(set_to_none=True)
        logits = model(x)
        loss = loss_fn(logits, y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
        opt.step()
        last_loss = float(loss.detach().cpu())

    model.eval()
    with torch.no_grad():
        ex = torch.from_numpy(eval_x).to(DEVICE)
        pred = model(ex).argmax(dim=1).detach().cpu().numpy().astype(int)
    return pred, {"final_train_loss": last_loss}


def ridge_classifier_predict(train_x: np.ndarray, train_y: np.ndarray, eval_x: np.ndarray, alpha: float = 10.0) -> np.ndarray:
    train_x = np.asarray(train_x, dtype=np.float64)
    eval_x = np.asarray(eval_x, dtype=np.float64)
    y = np.where(np.asarray(train_y, dtype=int) == 1, 1.0, -1.0)
    xb = np.concatenate([train_x, np.ones((train_x.shape[0], 1))], axis=1)
    eb = np.concatenate([eval_x, np.ones((eval_x.shape[0], 1))], axis=1)
    eye = np.eye(xb.shape[1], dtype=np.float64)
    eye[-1, -1] = 0.0
    try:
        w = np.linalg.solve(xb.T @ xb + alpha * eye, xb.T @ y)
    except np.linalg.LinAlgError:
        w = np.linalg.pinv(xb.T @ xb + alpha * eye) @ xb.T @ y
    score = eb @ w
    return (score >= 0.0).astype(int)


def centroid_predict(train_x: np.ndarray, train_y: np.ndarray, eval_x: np.ndarray) -> np.ndarray:
    train_x = np.asarray(train_x, dtype=np.float64)
    eval_x = np.asarray(eval_x, dtype=np.float64)
    train_y = np.asarray(train_y, dtype=int)
    centroids = {}
    global_mean = train_x.mean(axis=0)
    for label in [0, 1]:
        if (train_y == label).any():
            centroids[label] = train_x[train_y == label].mean(axis=0)
        else:
            centroids[label] = global_mean
    d0 = ((eval_x - centroids[0]) ** 2).sum(axis=1)
    d1 = ((eval_x - centroids[1]) ** 2).sum(axis=1)
    return (d1 < d0).astype(int)


def balanced_subset_indices(y: np.ndarray, per_class: int = 48) -> np.ndarray:
    y = np.asarray(y, dtype=int)
    rng = np.random.default_rng(SEED)
    idxs = []
    for label in [0, 1]:
        cand = np.where(y == label)[0]
        if len(cand) == 0:
            continue
        take = min(per_class, len(cand))
        idxs.extend(rng.choice(cand, size=take, replace=False).tolist())
    idxs = np.asarray(sorted(idxs), dtype=int)
    return idxs


def within_subject_split(index_df: pd.DataFrame, label_col: str, val_frac: float = 0.30) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(SEED)
    train_rows = []
    val_rows = []
    for _, sub in index_df.groupby("subject_id", sort=True):
        rows = sub.index.to_numpy()
        rng.shuffle(rows)
        if len(rows) <= 2:
            train_rows.extend(rows.tolist())
            continue
        n_val = max(1, int(round(len(rows) * val_frac)))
        n_val = min(n_val, len(rows) - 1)
        val_rows.extend(rows[:n_val].tolist())
        train_rows.extend(rows[n_val:].tolist())
    return np.asarray(sorted(train_rows), dtype=int), np.asarray(sorted(val_rows), dtype=int)


def subject_heldout_split(index_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[int]]:
    subjects = sorted(int(s) for s in index_df["subject_id"].dropna().astype(int).unique().tolist())
    fold1 = make_subject_folds(subjects, n_folds=6, seed=SEED)[0]
    val_set = set(fold1)
    is_val = index_df["subject_id"].astype(int).isin(val_set).to_numpy()
    train_rows = index_df.index.to_numpy()[~is_val]
    val_rows = index_df.index.to_numpy()[is_val]
    return np.asarray(sorted(train_rows), dtype=int), np.asarray(sorted(val_rows), dtype=int), fold1


def load_eeg_summary_features(eeg_npy: Path) -> np.ndarray:
    arr = np.load(eeg_npy, mmap_mode="r")
    chunks = []
    chunk_size = 128
    for start in range(0, arr.shape[0], chunk_size):
        x = np.asarray(arr[start:start + chunk_size], dtype=np.float32)
        feats = [
            x.mean(axis=2),
            x.std(axis=2),
            np.sqrt((x ** 2).mean(axis=2)),
            np.abs(x).mean(axis=2),
            x.min(axis=2),
            x.max(axis=2),
        ]
        chunks.append(np.concatenate(feats, axis=1).astype(np.float32))
    return np.concatenate(chunks, axis=0)


def modality_data(modality: str) -> tuple[np.ndarray, np.ndarray | None, pd.DataFrame, str]:
    if modality == "EEG":
        summary = load_eeg_summary_features(CACHE / "idare_eeg_windows_32x640_float32_baseline_corrected.npy")
        raw = np.load(CACHE / "idare_eeg_windows_32x640_float32_baseline_corrected.npy", mmap_mode="r")
        idx = pd.read_csv(CACHE / "idare_eeg_cache_index_baseline_corrected.csv")
        return summary, raw, idx, "STIM-BSL-only"
    if modality == "EMG":
        feats = np.load(CACHE / "idare_emg_features.npy")
        idx = pd.read_csv(CACHE / "idare_emg_feature_cache_index.csv")
        return np.asarray(feats, dtype=np.float32), None, idx, "feature-only"
    raise ValueError(modality)


def label_column(task: str) -> str:
    return f"{task}_{POLICY}"


summary_rows: list[dict[str, Any]] = []
details: dict[str, Any] = {
    "micro_overfit_subset": [],
    "shuffled_label_negative_control": [],
    "within_subject_vs_subject_heldout_contrast": [],
    "simple_classical_baseline": [],
}

cached_modality = {m: modality_data(m) for m in MODALITIES}


def append_row(
    test_id: str,
    modality: str,
    task: str,
    split: str,
    model: str,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    passed: bool,
    interpretation: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    met = metrics(y_true, y_pred)
    row: dict[str, Any] = {
        "test_id": test_id,
        "modality": modality,
        "task": task,
        "policy": POLICY,
        "split": split,
        "model": model,
        "passed": bool(passed),
        "interpretation": interpretation,
        **met,
    }
    if extra:
        row.update(extra)
    summary_rows.append(row)
    details.setdefault(test_id, []).append(row)
    print(
        f"[{test_id}] {modality} {task} {split} {model} "
        f"macro_f1={met['macro_f1']:.4f} bal_acc={met['balanced_accuracy']:.4f} "
        f"acc={met['accuracy']:.4f} passed={passed}"
    )
    return row


for modality in MODALITIES:
    features, raw, idx, representation = cached_modality[modality]
    idx = idx.copy()
    idx["__row_id__"] = np.arange(len(idx))
    for task in TASKS:
        lcol = label_column(task)
        if lcol not in idx.columns:
            raise SystemExit(f"ERROR: missing label column {lcol} for {modality}")
        valid = idx[lcol].notna().to_numpy()
        task_idx = idx.loc[valid].copy().reset_index(drop=True)
        row_ids = task_idx["__row_id__"].to_numpy(dtype=int)
        y = task_idx[lcol].astype(int).to_numpy()

        # 1) Micro-overfit. Raw EEG for EEG; native EMG for EMG.
        subset_local = balanced_subset_indices(y, per_class=48)
        subset_global = row_ids[subset_local]
        y_sub = y[subset_local]
        if modality == "EEG":
            x_sub_raw = np.asarray(raw[subset_global], dtype=np.float32).reshape(len(subset_global), -1)
            x_train, x_eval = standardize(x_sub_raw, x_sub_raw)
            hidden = 96
            epochs = 260
            lr = 5e-3
        else:
            x_sub_raw = np.asarray(features[subset_global], dtype=np.float32)
            x_train, x_eval = standardize(x_sub_raw, x_sub_raw)
            hidden = 64
            epochs = 220
            lr = 8e-3
        pred, train_info = train_torch_classifier(x_train, y_sub, x_eval, epochs=epochs, lr=lr, hidden=hidden)
        met = metrics(y_sub, pred)
        pass_micro = bool(met["accuracy"] >= 0.95 and met["macro_f1"] >= 0.95)
        append_row(
            "micro_overfit_subset",
            modality,
            task,
            "same_subset_train_eval",
            "small_mlp_raw" if modality == "EEG" else "small_mlp_features",
            y_sub,
            pred,
            pass_micro,
            "pass: model/data path can memorize a small subset" if pass_micro else "fail: possible pipeline/model/loss/data-feeding issue",
            {
                "representation": representation,
                "train_n": int(len(y_sub)),
                "eval_n": int(len(y_sub)),
                "final_train_loss": train_info["final_train_loss"],
            },
        )

        # Common split/features for remaining tests.
        x_all = np.asarray(features[row_ids], dtype=np.float32)

        train_rows, val_rows, fold1 = subject_heldout_split(task_idx)
        x_train_raw = x_all[train_rows]
        y_train = y[train_rows]
        x_val_raw = x_all[val_rows]
        y_val = y[val_rows]
        x_train, x_val = standardize(x_train_raw, x_val_raw)

        # 2) Shuffled-label negative control.
        pred, info = train_torch_classifier(
            x_train,
            y_train,
            x_val,
            epochs=90,
            lr=5e-3,
            hidden=64,
            shuffle_labels=True,
        )
        met = metrics(y_val, pred)
        pass_shuffle = bool(met["macro_f1"] <= 0.62 and met["balanced_accuracy"] <= 0.62)
        append_row(
            "shuffled_label_negative_control",
            modality,
            task,
            "subject_heldout_fold1_train_labels_shuffled",
            "small_mlp_summary_features" if modality == "EEG" else "small_mlp_features",
            y_val,
            pred,
            pass_shuffle,
            "pass: shuffled-label validation remains near chance" if pass_shuffle else "fail: possible leakage/split/metric issue",
            {
                "representation": representation,
                "train_n": int(len(y_train)),
                "eval_n": int(len(y_val)),
                "fold1_subjects": ",".join(str(s) for s in fold1),
                "final_train_loss": info["final_train_loss"],
            },
        )

        # 3) Within-subject vs subject-heldout contrast with same MLP on summary/native features.
        # Subject-heldout normal labels.
        pred_sh, info_sh = train_torch_classifier(
            x_train,
            y_train,
            x_val,
            epochs=120,
            lr=5e-3,
            hidden=64,
            shuffle_labels=False,
        )
        row_sh = append_row(
            "within_subject_vs_subject_heldout_contrast",
            modality,
            task,
            "subject_heldout_fold1",
            "small_mlp_summary_features" if modality == "EEG" else "small_mlp_features",
            y_val,
            pred_sh,
            True,
            "reference subject-heldout diagnostic score",
            {
                "representation": representation,
                "train_n": int(len(y_train)),
                "eval_n": int(len(y_val)),
                "fold1_subjects": ",".join(str(s) for s in fold1),
                "final_train_loss": info_sh["final_train_loss"],
            },
        )

        ws_train_rows, ws_val_rows = within_subject_split(task_idx, lcol, val_frac=0.30)
        wx_train_raw = x_all[ws_train_rows]
        wy_train = y[ws_train_rows]
        wx_val_raw = x_all[ws_val_rows]
        wy_val = y[ws_val_rows]
        wx_train, wx_val = standardize(wx_train_raw, wx_val_raw)
        pred_ws, info_ws = train_torch_classifier(
            wx_train,
            wy_train,
            wx_val,
            epochs=120,
            lr=5e-3,
            hidden=64,
            shuffle_labels=False,
        )
        row_ws = append_row(
            "within_subject_vs_subject_heldout_contrast",
            modality,
            task,
            "within_subject_random_70_30",
            "small_mlp_summary_features" if modality == "EEG" else "small_mlp_features",
            wy_val,
            pred_ws,
            True,
            "reference within-subject diagnostic score",
            {
                "representation": representation,
                "train_n": int(len(wy_train)),
                "eval_n": int(len(wy_val)),
                "final_train_loss": info_ws["final_train_loss"],
            },
        )

        contrast = float(row_ws["macro_f1"] - row_sh["macro_f1"])
        subject_generalization_signal = bool(row_ws["macro_f1"] >= 0.56 and contrast >= 0.05)
        contrast_row = {
            "test_id": "within_subject_vs_subject_heldout_contrast_summary",
            "modality": modality,
            "task": task,
            "policy": POLICY,
            "split": "contrast",
            "model": "small_mlp_summary_features" if modality == "EEG" else "small_mlp_features",
            "within_subject_macro_f1": row_ws["macro_f1"],
            "subject_heldout_macro_f1": row_sh["macro_f1"],
            "macro_f1_delta": contrast,
            "passed": True,
            "interpretation": (
                "subject/domain generalization likely"
                if subject_generalization_signal
                else "subject/domain generalization not isolated by this contrast"
            ),
        }
        summary_rows.append(contrast_row)
        details["within_subject_vs_subject_heldout_contrast"].append(contrast_row)
        print(
            f"[within_subject_contrast] {modality} {task} "
            f"within={row_ws['macro_f1']:.4f} heldout={row_sh['macro_f1']:.4f} delta={contrast:.4f}"
        )

        # 4) Simple classical baselines on subject-heldout fold1.
        pred_ridge = ridge_classifier_predict(x_train, y_train, x_val, alpha=10.0)
        met_ridge = metrics(y_val, pred_ridge)
        pass_classical = bool(met_ridge["macro_f1"] >= 0.53 or met_ridge["balanced_accuracy"] >= 0.53)
        append_row(
            "simple_classical_baseline",
            modality,
            task,
            "subject_heldout_fold1",
            "ridge_classifier_summary_features" if modality == "EEG" else "ridge_classifier_features",
            y_val,
            pred_ridge,
            pass_classical,
            "classical baseline finds some signal" if pass_classical else "classical baseline also near chance",
            {
                "representation": representation,
                "train_n": int(len(y_train)),
                "eval_n": int(len(y_val)),
                "fold1_subjects": ",".join(str(s) for s in fold1),
            },
        )

        pred_cent = centroid_predict(x_train, y_train, x_val)
        met_cent = metrics(y_val, pred_cent)
        pass_centroid = bool(met_cent["macro_f1"] >= 0.53 or met_cent["balanced_accuracy"] >= 0.53)
        append_row(
            "simple_classical_baseline",
            modality,
            task,
            "subject_heldout_fold1",
            "nearest_centroid_summary_features" if modality == "EEG" else "nearest_centroid_features",
            y_val,
            pred_cent,
            pass_centroid,
            "centroid baseline finds some signal" if pass_centroid else "centroid baseline also near chance",
            {
                "representation": representation,
                "train_n": int(len(y_train)),
                "eval_n": int(len(y_val)),
                "fold1_subjects": ",".join(str(s) for s in fold1),
            },
        )

summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv(OUT_SUMMARY, index=False)

micro = summary_df[summary_df["test_id"] == "micro_overfit_subset"]
shuffle = summary_df[summary_df["test_id"] == "shuffled_label_negative_control"]
contrast = summary_df[summary_df["test_id"] == "within_subject_vs_subject_heldout_contrast_summary"]
classical = summary_df[summary_df["test_id"] == "simple_classical_baseline"]

micro_fail = bool((micro["passed"] == False).any()) if not micro.empty else True
shuffle_fail = bool((shuffle["passed"] == False).any()) if not shuffle.empty else True

mean_within_delta = float(contrast["macro_f1_delta"].mean()) if not contrast.empty else math.nan
max_within_delta = float(contrast["macro_f1_delta"].max()) if not contrast.empty else math.nan
within_generalization_hits = int((contrast["interpretation"] == "subject/domain generalization likely").sum()) if not contrast.empty else 0

best_classical_macro = float(classical["macro_f1"].max()) if not classical.empty and "macro_f1" in classical else math.nan
mean_classical_macro = float(classical["macro_f1"].mean()) if not classical.empty and "macro_f1" in classical else math.nan

all_near_chance = bool(
    (micro["macro_f1"].max() < 0.90 if not micro.empty else True)
    and (classical["macro_f1"].max() < 0.56 if not classical.empty else True)
    and (summary_df[summary_df["test_id"] == "within_subject_vs_subject_heldout_contrast"]["macro_f1"].max() < 0.56)
)

if micro_fail:
    recommended_next = "pipeline_data_feeding_loss_audit_objective"
    recommendation_reason = [
        "At least one micro-overfit subset test failed.",
        "A model that cannot memorize a tiny diagnostic subset suggests a pipeline/model/loss/data-feeding problem.",
    ]
    diagnosis = "model_pipeline_learning_issue_supported"
elif shuffle_fail:
    recommended_next = "leakage_split_metric_audit_objective"
    recommendation_reason = [
        "At least one shuffled-label negative-control test performed suspiciously above the allowed threshold.",
        "This suggests possible leakage, split mismatch, or metric/reporting bug.",
    ]
    diagnosis = "leakage_or_split_issue_supported"
elif within_generalization_hits >= 2 or mean_within_delta >= 0.05:
    recommended_next = "subject_generalization_diagnostic_objective"
    recommendation_reason = [
        "Micro-overfit passed and shuffled-label control passed.",
        "Within-subject scores are better than subject-heldout scores, pointing toward subject/domain generalization difficulty.",
    ]
    diagnosis = "subject_generalization_issue_supported"
elif all_near_chance:
    recommended_next = "representation_label_task_redesign_objective"
    recommendation_reason = [
        "Micro-overfit and simple baselines do not show enough learnability.",
        "This points toward representation/label/task redesign before any heavier model work.",
    ]
    diagnosis = "representation_or_label_task_issue_supported"
elif best_classical_macro >= 0.56:
    recommended_next = "neural_training_baseline_audit_objective"
    recommendation_reason = [
        "A simple classical baseline finds some signal.",
        "If classical is stronger than the current neural setup, audit neural training before architecture escalation.",
    ]
    diagnosis = "neural_training_setup_issue_possible"
else:
    recommended_next = "calibration_and_subject_generalization_objective"
    recommendation_reason = [
        "Core sanity checks passed, but results remain weak/mixed.",
        "Next diagnostic work should focus on calibration and subject-generalization without fusion or architecture escalation.",
    ]
    diagnosis = "mixed_issue_unresolved"

report = {
    "status": "complete_pending_review",
    "created_or_updated_utc": NOW,
    "objective": "docs/idare_diagnostic_sanity_tests_objective.md",
    "evidence_level": "diagnostic-only sanity tests; no final performance claim",
    "device": str(DEVICE),
    "policy": POLICY,
    "tests_run": [
        "micro_overfit_subset",
        "shuffled_label_negative_control",
        "within_subject_vs_subject_heldout_contrast",
        "simple_classical_baseline",
    ],
    "summary_csv": str(OUT_SUMMARY),
    "diagnostic_summary": {
        "micro_overfit_all_passed": not micro_fail,
        "shuffled_label_control_all_passed": not shuffle_fail,
        "mean_within_subject_minus_subject_heldout_macro_f1": mean_within_delta,
        "max_within_subject_minus_subject_heldout_macro_f1": max_within_delta,
        "within_subject_generalization_hits": within_generalization_hits,
        "best_classical_macro_f1": best_classical_macro,
        "mean_classical_macro_f1": mean_classical_macro,
        "diagnosis": diagnosis,
        "recommended_next_objective": recommended_next,
        "recommendation_reason": recommendation_reason,
    },
    "rows": summary_df.replace({np.nan: None}).to_dict(orient="records"),
    "not_authorized": [
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "final global label-policy lock",
        "architecture ablation for improvement",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "broad hyperparameter search",
        "mainline change",
    ],
}
OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fmt(v: Any, digits: int = 4) -> str:
    if v is None:
        return "NA"
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    if math.isnan(f):
        return "NA"
    return f"{f:.{digits}f}"


def md_table(rows: list[dict[str, Any]], headers: list[tuple[str, str]]) -> str:
    lines = []
    lines.append("| " + " | ".join(h[0] for h in headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for r in rows:
        vals = []
        for _, key in headers:
            val = r.get(key, "")
            if isinstance(val, float):
                vals.append(fmt(val))
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def compact_rows(test_id: str) -> list[dict[str, Any]]:
    cols = [
        "test_id", "modality", "task", "split", "model", "n",
        "macro_f1", "balanced_accuracy", "accuracy", "majority_accuracy", "passed", "interpretation",
    ]
    rows = []
    for r in summary_df[summary_df["test_id"] == test_id].to_dict(orient="records"):
        rows.append({c: r.get(c, "") for c in cols})
    return rows


contrast_rows = []
for r in summary_df[summary_df["test_id"] == "within_subject_vs_subject_heldout_contrast_summary"].to_dict(orient="records"):
    contrast_rows.append({
        "modality": r.get("modality"),
        "task": r.get("task"),
        "within_subject_macro_f1": r.get("within_subject_macro_f1"),
        "subject_heldout_macro_f1": r.get("subject_heldout_macro_f1"),
        "macro_f1_delta": r.get("macro_f1_delta"),
        "interpretation": r.get("interpretation"),
    })

md = f"""# I-DARE Diagnostic Sanity Tests Report

## Status

Diagnostic sanity tests complete; pending human review.

Generated UTC: `{NOW}`

Device: `{DEVICE}`

Policy: `{POLICY}`

This report is diagnostic-only. It does not make a final performance claim.

## Diagnostic Summary

| Item | Value |
|---|---|
| Micro-overfit all passed | {not micro_fail} |
| Shuffled-label negative control all passed | {not shuffle_fail} |
| Mean within-subject minus subject-heldout macro-F1 | {fmt(mean_within_delta)} |
| Max within-subject minus subject-heldout macro-F1 | {fmt(max_within_delta)} |
| Subject-generalization contrast hits | {within_generalization_hits} |
| Best classical macro-F1 | {fmt(best_classical_macro)} |
| Mean classical macro-F1 | {fmt(mean_classical_macro)} |
| Diagnosis | `{diagnosis}` |
| Recommended next objective | `{recommended_next}` |

## Micro-overfit Subset Test

{md_table(compact_rows("micro_overfit_subset"), [
    ("Modality", "modality"),
    ("Task", "task"),
    ("N", "n"),
    ("Macro F1", "macro_f1"),
    ("Bal acc", "balanced_accuracy"),
    ("Acc", "accuracy"),
    ("Passed", "passed"),
    ("Interpretation", "interpretation"),
])}

## Shuffled-label Negative Control

{md_table(compact_rows("shuffled_label_negative_control"), [
    ("Modality", "modality"),
    ("Task", "task"),
    ("N", "n"),
    ("Macro F1", "macro_f1"),
    ("Bal acc", "balanced_accuracy"),
    ("Acc", "accuracy"),
    ("Passed", "passed"),
    ("Interpretation", "interpretation"),
])}

## Within-subject vs Subject-heldout Contrast

{md_table(contrast_rows, [
    ("Modality", "modality"),
    ("Task", "task"),
    ("Within macro F1", "within_subject_macro_f1"),
    ("Heldout macro F1", "subject_heldout_macro_f1"),
    ("Delta", "macro_f1_delta"),
    ("Interpretation", "interpretation"),
])}

## Simple Classical Baseline

{md_table(compact_rows("simple_classical_baseline"), [
    ("Modality", "modality"),
    ("Task", "task"),
    ("Model", "model"),
    ("N", "n"),
    ("Macro F1", "macro_f1"),
    ("Bal acc", "balanced_accuracy"),
    ("Acc", "accuracy"),
    ("Passed", "passed"),
    ("Interpretation", "interpretation"),
])}

## Recommendation

Recommended next objective:

`{recommended_next}`

Reason:

"""
for item in recommendation_reason:
    md += f"- {item}\n"

md += """
## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Output Files

- `docs/idare_diagnostic_sanity_tests_report.md`
- `docs/idare_diagnostic_sanity_tests_report.json`
- `docs/idare_diagnostic_sanity_tests_summary.csv`

## Next Allowed Step

Human review / closeout of this diagnostic sanity report.

Only after review should the next objective be created.
"""

OUT_MD.write_text(md, encoding="utf-8")

# Update roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
report_row = "| I-DARE diagnostic sanity tests report | diagnostic sanity tests complete; pending human review | yes | `docs/idare_diagnostic_sanity_tests_report.md` | Human review / closeout before the next diagnostic or fix objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |"

if "I-DARE diagnostic sanity tests report" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE diagnostic sanity tests objective |"):
            out.append(report_row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert diagnostic sanity report row")
    project_md = "\n".join(out) + "\n"

bullet = "- Diagnostic-only I-DARE sanity tests are complete in `docs/idare_diagnostic_sanity_tests_report.md`; next work is human review/closeout before creating the next objective."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: project status marker not found")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)

PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_diagnostic_sanity_tests_report"] = {
    "status": "complete_pending_review",
    "evidence": "docs/idare_diagnostic_sanity_tests_report.md",
    "evidence_json": "docs/idare_diagnostic_sanity_tests_report.json",
    "summary_csv": "docs/idare_diagnostic_sanity_tests_summary.csv",
    "evidence_level": "diagnostic-only sanity tests; no final performance claim",
    "diagnostic_summary": report["diagnostic_summary"],
    "next_allowed_step": "Human review / closeout of diagnostic sanity report.",
    "not_authorized": report["not_authorized"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_DIAGNOSTIC_SANITY_TESTS_REPORT_WRITTEN")
print(OUT_MD)
print(OUT_JSON)
print(OUT_SUMMARY)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next)
PY
echo

echo "===== 4) validate generated outputs ====="
"$PY" - <<'PY'
import json
import pandas as pd
from pathlib import Path

for p in [
    Path("docs/idare_diagnostic_sanity_tests_report.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")

df = pd.read_csv("docs/idare_diagnostic_sanity_tests_summary.csv")
print("summary_rows=", len(df))
print("tests=", sorted(df["test_id"].unique().tolist()))
PY

grep -n "## Status\|## Diagnostic Summary\|## Micro-overfit\|## Shuffled-label\|## Within-subject\|## Simple Classical\|## Recommendation\|## Next Allowed Step" docs/idare_diagnostic_sanity_tests_report.md
grep -n "diagnostic sanity tests report" docs/project_status_current.md
echo

echo "===== 5) file list ====="
ls -lh \
  docs/idare_diagnostic_sanity_tests_report.md \
  docs/idare_diagnostic_sanity_tests_report.json \
  docs/idare_diagnostic_sanity_tests_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push diagnostic sanity report ====="
git add \
  docs/idare_diagnostic_sanity_tests_report.md \
  docs/idare_diagnostic_sanity_tests_report.json \
  docs/idare_diagnostic_sanity_tests_summary.csv \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "analysis: add I-DARE diagnostic sanity tests report"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_diagnostic_sanity_tests_run.log"
