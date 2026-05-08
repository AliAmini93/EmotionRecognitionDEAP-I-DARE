#!/usr/bin/env bash
set -euo pipefail

LOG_PATH="${LOG_PATH:-/tmp/idare_label_semantics_minimal_redesigned_task_first_pass_run.log}"
exec > >(tee "$LOG_PATH") 2>&1

echo "===== 0) start minimal redesigned-task first-pass run ====="
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
try:
    import json
    from pathlib import Path
    import numpy as np
    import pandas as pd
except Exception as e:
    raise SystemExit(f"ERROR_IMPORTS: {e}")
print("OK_IMPORTS")
PY

if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: repo is not clean; commit/stash before running first pass." >&2
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
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.md
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.json
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_run_matrix.csv
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_guardrails.csv
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_review_status.md
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_review_status.json
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.md
  docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.json
  docs/idare_label_semantics_task_redesign_spec.md
  docs/idare_label_semantics_task_redesign_spec.json
  docs/idare_label_semantics_selected_task_definition.csv
  docs/idare_label_semantics_task_redesign_metric_plan.csv
  docs/idare_label_semantics_task_redesign_protocol_matrix.csv
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

echo "===== 3) remove stale first-pass outputs ====="
rm -f \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.md \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.json \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_runs.csv \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_predictions.csv \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_metric_summary.csv \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_subject_error_summary.csv
echo "OK_CLEAN_OUTPUT_TARGETS"
echo

echo "===== 4) run frozen 48-row minimal first-pass matrix ====="
"$PY" - <<'PY'
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

DOCS = Path("docs")
CACHE = Path(".cache")
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

RUN_MATRIX_PATH = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_run_matrix.csv"
OBJ_JSON_PATH = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_training_objective.json"
REVIEW_JSON_PATH = DOCS / "idare_label_semantics_redesigned_task_smoke_guard_patch_review_status.json"
SPEC_JSON_PATH = DOCS / "idare_label_semantics_task_redesign_spec.json"
METRIC_PLAN_PATH = DOCS / "idare_label_semantics_task_redesign_metric_plan.csv"
PROTOCOL_PATH = DOCS / "idare_label_semantics_task_redesign_protocol_matrix.csv"

EEG_INDEX_PATH = CACHE / "idare_eeg_cache_index_baseline_corrected.csv"
EEG_NPY_PATH = CACHE / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
EMG_INDEX_PATH = CACHE / "idare_emg_feature_cache_index.csv"
EMG_NPY_PATH = CACHE / "idare_emg_features.npy"

REPORT_MD_PATH = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_report.md"
REPORT_JSON_PATH = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_report.json"
RUNS_CSV_PATH = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_runs.csv"
PRED_CSV_PATH = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_predictions.csv"
METRIC_CSV_PATH = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_metric_summary.csv"
SUBJECT_CSV_PATH = DOCS / "idare_label_semantics_minimal_redesigned_task_first_pass_subject_error_summary.csv"

STATUS_JSON_PATH = DOCS / "project_status_current.json"
STATUS_MD_PATH = DOCS / "project_status_current.md"

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def md_table(rows, columns):
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        vals = []
        for c in columns:
            v = row.get(c, "")
            if isinstance(v, float):
                v = f"{v:.4f}" if np.isfinite(v) else "nan"
            vals.append(str(v).replace("\n", " ").replace("|", "\\|"))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)

def pick_col(df, candidates, required=True, what="column"):
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    for c in df.columns:
        lc = c.lower()
        for cand in candidates:
            if cand.lower() in lc:
                return c
    if required:
        raise SystemExit(f"ERROR: could not find {what}; candidates={candidates}; columns={list(df.columns)}")
    return None

def subject_numeric(series):
    def conv(x):
        if pd.isna(x):
            return np.nan
        if isinstance(x, (int, np.integer)):
            return int(x)
        if isinstance(x, float) and np.isfinite(x):
            return int(x)
        m = re.search(r"\d+", str(x))
        if not m:
            return np.nan
        return int(m.group(0))
    return series.map(conv).astype("Int64")

def ensure_common_columns(idx, modality):
    idx = idx.copy()
    subj_col = pick_col(idx, ["subject_id", "subject", "participant_id", "participant", "subj"], True, f"{modality} subject column")
    idx["_subject_id"] = subject_numeric(idx[subj_col])
    if idx["_subject_id"].isna().any():
        bad = idx.loc[idx["_subject_id"].isna(), subj_col].head(5).tolist()
        raise SystemExit(f"ERROR: {modality} subject_id conversion failed; examples={bad}")
    idx["_subject_id"] = idx["_subject_id"].astype(int)

    trial_col = pick_col(idx, ["trial_id", "trial", "video_id", "stimulus_id", "clip_id"], False, f"{modality} trial column")
    idx["_trial_id"] = idx[trial_col].astype(str) if trial_col else idx.index.astype(str)

    val_col = pick_col(idx, ["valence_score", "valence_rating", "valence"], True, f"{modality} valence score")
    aro_col = pick_col(idx, ["arousal_score", "arousal_rating", "arousal"], True, f"{modality} arousal score")
    idx["_valence_raw"] = pd.to_numeric(idx[val_col], errors="coerce")
    idx["_arousal_raw"] = pd.to_numeric(idx[aro_col], errors="coerce")
    if idx[["_valence_raw", "_arousal_raw"]].isna().any().any():
        raise SystemExit(f"ERROR: {modality} has missing/non-numeric valence/arousal ratings after conversion")

    if "row_id" in idx.columns:
        idx["_row_id"] = idx["row_id"]
    elif "sample_id" in idx.columns:
        idx["_row_id"] = idx["sample_id"]
    else:
        idx["_row_id"] = np.arange(len(idx))
    return idx

def add_rank_targets(idx):
    idx = idx.copy()
    for task, raw_col in [("valence", "_valence_raw"), ("arousal", "_arousal_raw")]:
        ranks = idx.groupby("_subject_id", sort=False)[raw_col].rank(method="average", ascending=True)
        counts = idx.groupby("_subject_id", sort=False)[raw_col].transform("count").astype(float)
        target = (ranks - 1.0) / np.maximum(counts - 1.0, 1.0)
        target = target.where(counts > 1.0, 0.5)
        idx[f"_target_{task}"] = target.astype(float)
        z = idx.groupby("_subject_id", sort=False)[raw_col].transform(lambda s: (s - s.mean()) / (s.std(ddof=0) if s.std(ddof=0) > 0 else 1.0))
        idx[f"_z_{task}"] = z.astype(float)
    return idx

# Existing six held-out subject folds used throughout the I-DARE diagnostics.
FOLDS = {
    1: [6, 7, 8, 13, 28, 38, 43, 54, 58, 59, 65],
    2: [2, 5, 11, 17, 26, 31, 34, 44, 46, 49, 63],
    3: [9, 10, 20, 35, 39, 45, 47, 48, 52, 57, 62],
    4: [1, 3, 19, 25, 36, 40, 42, 53, 55, 61],
    5: [14, 23, 24, 27, 29, 30, 37, 56, 60, 64],
    6: [12, 15, 16, 18, 21, 22, 32, 33, 41, 50],
}
ALL_FOLD_SUBJECTS = sorted([s for vals in FOLDS.values() for s in vals])

def validate_subjects(idx, modality):
    subjects = sorted(idx["_subject_id"].unique().tolist())
    missing = sorted(set(subjects) - set(ALL_FOLD_SUBJECTS))
    extra = sorted(set(ALL_FOLD_SUBJECTS) - set(subjects))
    if missing or extra:
        raise SystemExit(
            f"ERROR: {modality} subjects do not match frozen folds; "
            f"subjects_not_in_folds={missing}; fold_subjects_not_in_data={extra}"
        )

def build_eeg_summary_features(npy_path):
    x = np.load(npy_path, mmap_mode="r")
    if x.ndim != 3:
        raise SystemExit(f"ERROR: EEG array must be 3D [rows, channels, time], got shape={x.shape}")
    print("BUILDING_EEG_SUMMARY_FEATURES shape=", list(x.shape))
    # Summary features per channel. Keep deterministic and lightweight.
    mean = np.asarray(x.mean(axis=2), dtype=np.float32)
    std = np.asarray(x.std(axis=2), dtype=np.float32)
    rms = np.asarray(np.sqrt((np.asarray(x, dtype=np.float32) ** 2).mean(axis=2)), dtype=np.float32)
    mn = np.asarray(x.min(axis=2), dtype=np.float32)
    mx = np.asarray(x.max(axis=2), dtype=np.float32)
    feats = np.concatenate([mean, std, rms, mn, mx], axis=1).astype(np.float32)
    return feats

def build_emg_features(npy_path):
    x = np.load(npy_path)
    if x.ndim != 2:
        raise SystemExit(f"ERROR: EMG array must be 2D [rows, features], got shape={x.shape}")
    print("BUILDING_EMG_SIGNED_LOG1P_FEATURES shape=", list(x.shape))
    x = np.asarray(x, dtype=np.float32)
    return (np.sign(x) * np.log1p(np.abs(x))).astype(np.float32)

def standardize_train_val(X_train, X_val):
    mu = X_train.mean(axis=0)
    sd = X_train.std(axis=0)
    sd = np.where(sd > 1e-8, sd, 1.0)
    return (X_train - mu) / sd, (X_val - mu) / sd

def ridge_predict(X_train, y_train, X_val, alpha=1.0):
    Xtr, Xva = standardize_train_val(X_train.astype(float), X_val.astype(float))
    # Add intercept without regularizing intercept.
    Xtr_i = np.column_stack([np.ones(len(Xtr)), Xtr])
    Xva_i = np.column_stack([np.ones(len(Xva)), Xva])
    reg = np.eye(Xtr_i.shape[1]) * alpha
    reg[0, 0] = 0.0
    try:
        beta = np.linalg.solve(Xtr_i.T @ Xtr_i + reg, Xtr_i.T @ y_train)
    except np.linalg.LinAlgError:
        beta = np.linalg.pinv(Xtr_i.T @ Xtr_i + reg) @ Xtr_i.T @ y_train
    return Xva_i @ beta

def spearmanr_simple(y, p):
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    if len(y) < 3 or np.nanstd(y) <= 1e-12 or np.nanstd(p) <= 1e-12:
        return 0.0
    yr = pd.Series(y).rank(method="average").to_numpy(dtype=float)
    pr = pd.Series(p).rank(method="average").to_numpy(dtype=float)
    c = np.corrcoef(yr, pr)[0, 1]
    if not np.isfinite(c):
        return 0.0
    return float(c)

def mae(y, p):
    return float(np.mean(np.abs(np.asarray(y) - np.asarray(p))))

def rmse(y, p):
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(p)) ** 2)))

def balanced_acc_binary(y_true, y_score):
    y_true = np.asarray(y_true, dtype=float)
    y_score = np.asarray(y_score, dtype=float)
    mask = (y_true <= (1.0/3.0)) | (y_true >= (2.0/3.0))
    if mask.sum() == 0:
        return float("nan")
    yt = (y_true[mask] >= (2.0/3.0)).astype(int)
    yp = (y_score[mask] >= 0.5).astype(int)
    out = []
    for cls in [0, 1]:
        m = yt == cls
        if m.sum() == 0:
            continue
        out.append(float((yp[m] == cls).mean()))
    if not out:
        return float("nan")
    return float(np.mean(out))

def safe_float(x):
    try:
        if x is None:
            return None
        v = float(x)
        if not np.isfinite(v):
            return None
        return v
    except Exception:
        return None

def run_cell(row, idx, features):
    modality = row["modality"]
    task = row["task"]
    fold = int(row["fold"])
    model = row["model"]
    target_col = f"_target_{task}"
    val_subjects = set(FOLDS[fold])

    is_val = idx["_subject_id"].isin(val_subjects).to_numpy()
    is_train = ~is_val
    if is_val.sum() == 0 or is_train.sum() == 0:
        raise SystemExit(f"ERROR: empty split for {modality} {task} fold={fold}")

    y_train = idx.loc[is_train, target_col].to_numpy(dtype=float)
    y_val = idx.loc[is_val, target_col].to_numpy(dtype=float)

    if model == "mean_baseline_no_training":
        pred = np.full_like(y_val, fill_value=float(np.mean(y_train)), dtype=float)
        permutation_spearman = None
    elif model == "ridge_regression_summary_features":
        X_train = features[is_train]
        X_val = features[is_val]
        pred = ridge_predict(X_train, y_train, X_val, alpha=1.0)
        # Negative-control metric, not an additional registered model row.
        rng = np.random.default_rng(20260508 + int(row["objective_run_id"]))
        y_perm = y_train.copy()
        rng.shuffle(y_perm)
        perm_pred = ridge_predict(X_train, y_perm, X_val, alpha=1.0)
        permutation_spearman = spearmanr_simple(y_val, perm_pred)
    else:
        raise SystemExit(f"ERROR: unauthorized model in run matrix: {model}")

    run_metrics = {
        "objective_run_id": int(row["objective_run_id"]),
        "planned_run_id": int(row["planned_run_id"]),
        "model": model,
        "training_category": row.get("training_category", ""),
        "modality": modality,
        "task": task,
        "fold": fold,
        "target": row["target"],
        "n_train": int(is_train.sum()),
        "n_val": int(is_val.sum()),
        "n_train_subjects": int(idx.loc[is_train, "_subject_id"].nunique()),
        "n_val_subjects": int(idx.loc[is_val, "_subject_id"].nunique()),
        "train_target_mean": float(np.mean(y_train)),
        "val_target_mean": float(np.mean(y_val)),
        "val_target_std": float(np.std(y_val)),
        "spearman_rho": spearmanr_simple(y_val, pred),
        "mae_rank_percentile": mae(y_val, pred),
        "rmse_rank_percentile": rmse(y_val, pred),
        "top_bottom_q33_balanced_accuracy": balanced_acc_binary(y_val, pred),
        "permutation_control_spearman": safe_float(permutation_spearman),
        "pred_min": float(np.min(pred)),
        "pred_max": float(np.max(pred)),
        "pred_mean": float(np.mean(pred)),
    }

    pred_df = idx.loc[is_val, ["_row_id", "_subject_id", "_trial_id", f"_target_{task}", f"_z_{task}", f"_{task}_raw"]].copy()
    pred_df = pred_df.rename(columns={
        "_row_id": "source_row_id",
        "_subject_id": "subject_id",
        "_trial_id": "trial_id",
        f"_target_{task}": "target_rank_percentile",
        f"_z_{task}": "target_subject_z",
        f"_{task}_raw": "raw_rating",
    })
    pred_df.insert(0, "objective_run_id", int(row["objective_run_id"]))
    pred_df.insert(1, "model", model)
    pred_df.insert(2, "modality", modality)
    pred_df.insert(3, "task", task)
    pred_df.insert(4, "fold", fold)
    pred_df["prediction"] = pred
    pred_df["abs_error"] = np.abs(pred_df["target_rank_percentile"].to_numpy(dtype=float) - pred)
    pred_df["squared_error"] = (pred_df["target_rank_percentile"].to_numpy(dtype=float) - pred) ** 2
    pred_df["true_top_bottom_q33"] = np.where(
        pred_df["target_rank_percentile"] <= (1.0/3.0),
        "bottom",
        np.where(pred_df["target_rank_percentile"] >= (2.0/3.0), "top", "middle"),
    )
    pred_df["pred_top_bottom_by_0p5"] = np.where(pred_df["prediction"] >= 0.5, "top", "bottom")
    return run_metrics, pred_df

objective = read_json(OBJ_JSON_PATH)
review = read_json(REVIEW_JSON_PATH)
spec = read_json(SPEC_JSON_PATH)
run_matrix = pd.read_csv(RUN_MATRIX_PATH)
metric_plan = pd.read_csv(METRIC_PLAN_PATH)
protocol = pd.read_csv(PROTOCOL_PATH)

if len(run_matrix) != 48:
    raise SystemExit(f"ERROR: frozen run matrix must contain 48 rows; got {len(run_matrix)}")
allowed_models = {"mean_baseline_no_training", "ridge_regression_summary_features"}
models = set(run_matrix["model"].astype(str).unique())
if not models.issubset(allowed_models):
    raise SystemExit(f"ERROR: unregistered model(s): {sorted(models - allowed_models)}")
if review.get("accepted_diagnosis") != "redesigned_task_smoke_tests_passed_after_guard_patch":
    raise SystemExit("ERROR: patched smoke review does not authorize this objective")
selected_primary_formulation = objective.get("selected_primary_formulation", "subject_relative_ordinal_affect_regression_v1")

eeg_idx = add_rank_targets(ensure_common_columns(pd.read_csv(EEG_INDEX_PATH), "EEG"))
emg_idx = add_rank_targets(ensure_common_columns(pd.read_csv(EMG_INDEX_PATH), "EMG"))
validate_subjects(eeg_idx, "EEG")
validate_subjects(emg_idx, "EMG")

eeg_features = build_eeg_summary_features(EEG_NPY_PATH)
emg_features = build_emg_features(EMG_NPY_PATH)
if len(eeg_features) != len(eeg_idx):
    raise SystemExit(f"ERROR: EEG feature/index row mismatch: {len(eeg_features)} vs {len(eeg_idx)}")
if len(emg_features) != len(emg_idx):
    raise SystemExit(f"ERROR: EMG feature/index row mismatch: {len(emg_features)} vs {len(emg_idx)}")

runs = []
pred_chunks = []
for _, row in run_matrix.sort_values("objective_run_id").iterrows():
    if row["modality"] == "EEG":
        idx, feats = eeg_idx, eeg_features
    elif row["modality"] == "EMG":
        idx, feats = emg_idx, emg_features
    else:
        raise SystemExit(f"ERROR: unknown modality: {row['modality']}")
    m, p = run_cell(row, idx, feats)
    runs.append(m)
    pred_chunks.append(p)
    print(json.dumps({
        "objective_run_id": m["objective_run_id"],
        "model": m["model"],
        "modality": m["modality"],
        "task": m["task"],
        "fold": m["fold"],
        "spearman_rho": round(m["spearman_rho"], 4),
        "mae": round(m["mae_rank_percentile"], 4),
        "rmse": round(m["rmse_rank_percentile"], 4),
        "q33_bal_acc": None if m["top_bottom_q33_balanced_accuracy"] is None else round(m["top_bottom_q33_balanced_accuracy"], 4),
    }))

runs_df = pd.DataFrame(runs)
pred_df = pd.concat(pred_chunks, ignore_index=True)

# Subject-level error audit.
subject_df = (
    pred_df.groupby(["model", "modality", "task", "fold", "subject_id"], dropna=False)
    .agg(
        n=("abs_error", "size"),
        mean_abs_error=("abs_error", "mean"),
        rmse=("squared_error", lambda s: float(np.sqrt(np.mean(s)))),
        target_mean=("target_rank_percentile", "mean"),
        pred_mean=("prediction", "mean"),
    )
    .reset_index()
)

summary = (
    runs_df.groupby(["model", "training_category", "modality", "task"], dropna=False)
    .agg(
        n_runs=("objective_run_id", "count"),
        mean_spearman_rho=("spearman_rho", "mean"),
        std_spearman_rho=("spearman_rho", "std"),
        min_spearman_rho=("spearman_rho", "min"),
        max_spearman_rho=("spearman_rho", "max"),
        mean_mae_rank_percentile=("mae_rank_percentile", "mean"),
        mean_rmse_rank_percentile=("rmse_rank_percentile", "mean"),
        mean_top_bottom_q33_balanced_accuracy=("top_bottom_q33_balanced_accuracy", "mean"),
        mean_permutation_control_spearman=("permutation_control_spearman", "mean"),
        folds_positive_spearman=("spearman_rho", lambda s: int((s > 0).sum())),
        folds_over_010_spearman=("spearman_rho", lambda s: int((s > 0.10).sum())),
        folds_under_000_spearman=("spearman_rho", lambda s: int((s < 0).sum())),
    )
    .reset_index()
)

# Join ridge against mean baseline by modality/task.
mean_base = summary.loc[summary["model"] == "mean_baseline_no_training", ["modality", "task", "mean_spearman_rho", "mean_mae_rank_percentile", "mean_rmse_rank_percentile"]].rename(columns={
    "mean_spearman_rho": "mean_baseline_spearman_rho",
    "mean_mae_rank_percentile": "mean_baseline_mae",
    "mean_rmse_rank_percentile": "mean_baseline_rmse",
})
summary = summary.merge(mean_base, on=["modality", "task"], how="left")
summary["delta_vs_mean_baseline_spearman"] = summary["mean_spearman_rho"] - summary["mean_baseline_spearman_rho"]
summary["delta_vs_mean_baseline_mae"] = summary["mean_baseline_mae"] - summary["mean_mae_rank_percentile"]
summary["delta_vs_mean_baseline_rmse"] = summary["mean_baseline_rmse"] - summary["mean_rmse_rank_percentile"]

ridge_summary = summary[summary["model"] == "ridge_regression_summary_features"].copy()
best = ridge_summary.sort_values(
    ["mean_spearman_rho", "delta_vs_mean_baseline_mae"],
    ascending=[False, False],
).head(1).to_dict("records")
best = best[0] if best else {}

# Cautious pre-registered interpretation. Spearman must be positive and beat controls, not just MAE.
ridge_mean_spearman = float(ridge_summary["mean_spearman_rho"].mean()) if len(ridge_summary) else 0.0
ridge_best_spearman = float(ridge_summary["mean_spearman_rho"].max()) if len(ridge_summary) else 0.0
ridge_cells_over_010 = int((ridge_summary["mean_spearman_rho"] > 0.10).sum()) if len(ridge_summary) else 0
ridge_cells_positive = int((ridge_summary["mean_spearman_rho"] > 0.0).sum()) if len(ridge_summary) else 0
perm_abs_max = float(np.nanmax(np.abs(ridge_summary["mean_permutation_control_spearman"].fillna(0).to_numpy()))) if len(ridge_summary) else 0.0
mae_improved_cells = int((ridge_summary["delta_vs_mean_baseline_mae"] > 0).sum()) if len(ridge_summary) else 0

if ridge_cells_over_010 >= 2 and ridge_mean_spearman > 0.05 and perm_abs_max < 0.10:
    diagnosis = "minimal_redesigned_task_first_pass_signal_supported"
    recommended_next_objective = "label_semantics_redesigned_task_confirmation_objective"
elif ridge_cells_positive >= 2 or mae_improved_cells >= 2:
    diagnosis = "minimal_redesigned_task_first_pass_mixed_signal"
    recommended_next_objective = "label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective"
else:
    diagnosis = "minimal_redesigned_task_first_pass_not_sufficient"
    recommended_next_objective = "label_semantics_minimal_redesigned_task_failure_analysis_objective"

blocked = [
    "direct full SupCon/DG training",
    "broad hyperparameter search",
    "EEG+EMG fusion",
    "final LOSO claim",
    "mainline change",
    "deep neural training for redesigned task",
    "unregistered feature engineering",
]

runs_df.to_csv(RUNS_CSV_PATH, index=False)
pred_df.to_csv(PRED_CSV_PATH, index=False)
summary.to_csv(METRIC_CSV_PATH, index=False)
subject_df.to_csv(SUBJECT_CSV_PATH, index=False)

report = {
    "status": "complete_pending_human_review",
    "created_utc": now,
    "selected_primary_formulation": selected_primary_formulation,
    "source_objective": str(OBJ_JSON_PATH),
    "source_run_matrix": str(RUN_MATRIX_PATH),
    "n_runs": int(len(runs_df)),
    "n_predictions": int(len(pred_df)),
    "n_metric_summary_rows": int(len(summary)),
    "n_subject_error_rows": int(len(subject_df)),
    "models": sorted(runs_df["model"].unique().tolist()),
    "modalities": sorted(runs_df["modality"].unique().tolist()),
    "tasks": sorted(runs_df["task"].unique().tolist()),
    "folds": sorted([int(x) for x in runs_df["fold"].unique().tolist()]),
    "best_ridge_cell": {k: (safe_float(v) if isinstance(v, (float, np.floating)) else v) for k, v in best.items()},
    "key_indicators": {
        "ridge_mean_spearman": safe_float(ridge_mean_spearman),
        "ridge_best_spearman": safe_float(ridge_best_spearman),
        "ridge_cells_over_010_spearman": ridge_cells_over_010,
        "ridge_cells_positive_spearman": ridge_cells_positive,
        "ridge_cells_mae_improved_vs_mean_baseline": mae_improved_cells,
        "permutation_abs_max_mean_spearman": safe_float(perm_abs_max),
    },
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next_objective,
    "training_authorized": False,
    "blocked": blocked,
}
write_json(REPORT_JSON_PATH, report)

# Markdown report.
summary_rows = summary.sort_values(["model", "modality", "task"]).to_dict("records")
top_rows = ridge_summary.sort_values("mean_spearman_rho", ascending=False).head(8).to_dict("records")
key_rows = [{"item": k, "value": v} for k, v in report["key_indicators"].items()]
run_matrix_rows = [
    {"item": "n_runs", "value": len(runs_df)},
    {"item": "n_predictions", "value": len(pred_df)},
    {"item": "selected_primary_formulation", "value": selected_primary_formulation},
    {"item": "diagnosis", "value": diagnosis},
    {"item": "recommended_next_objective", "value": recommended_next_objective},
]

md = []
md.append("# I-DARE Label-Semantics Minimal Redesigned-Task First-Pass Report\n")
md.append("## Status\n")
md.append("Status: complete; pending human review.\n")
md.append(f"Created UTC: `{now}`\n")
md.append("## Run Matrix\n")
md.append(md_table(run_matrix_rows, ["item", "value"]))
md.append("\n## Key Indicators\n")
md.append(md_table(key_rows, ["item", "value"]))
md.append("\n## Metric Summary\n")
metric_cols = [
    "model", "modality", "task", "n_runs", "mean_spearman_rho", "std_spearman_rho",
    "mean_mae_rank_percentile", "mean_rmse_rank_percentile",
    "mean_top_bottom_q33_balanced_accuracy", "mean_permutation_control_spearman",
    "delta_vs_mean_baseline_spearman", "delta_vs_mean_baseline_mae",
    "folds_positive_spearman", "folds_over_010_spearman",
]
md.append(md_table(summary_rows, metric_cols))
md.append("\n## Top Ridge Cells\n")
top_cols = [
    "modality", "task", "n_runs", "mean_spearman_rho", "std_spearman_rho",
    "mean_mae_rank_percentile", "delta_vs_mean_baseline_mae",
    "mean_permutation_control_spearman", "folds_over_010_spearman",
]
md.append(md_table(top_rows, top_cols))
md.append("\n## Interpretation\n")
if diagnosis == "minimal_redesigned_task_first_pass_signal_supported":
    md.append("The minimal redesigned-task first pass shows a cautious positive signal. This is not a final claim; it only justifies a reviewed confirmation objective.\n")
elif diagnosis == "minimal_redesigned_task_first_pass_mixed_signal":
    md.append("The minimal redesigned-task first pass shows mixed evidence. The next step should analyze whether the signal is robust enough for confirmation or whether it reflects fold/task instability.\n")
else:
    md.append("The minimal redesigned-task first pass is not sufficient as a fix. The next step should be a read-only failure analysis before any additional model work.\n")
md.append("\n## Next Allowed Step\n")
md.append("Human review / closeout before any confirmation or failure-analysis objective.\n")
md.append(f"\nRecommended next objective: `{recommended_next_objective}`\n")
md.append("\n## Blocked\n")
for b in blocked:
    md.append(f"- {b}\n")
REPORT_MD_PATH.write_text("\n".join(md), encoding="utf-8")

# Update roadmap.
status = read_json(STATUS_JSON_PATH)
status["last_updated_utc"] = now
status["current_idare_next_allowed_step"] = "human_review_closeout_before_next_redesigned_task_objective"
status["current_idare_blocked_steps"] = blocked
events = status.get("idare_protocol_events")
if not isinstance(events, list):
    events = []
status["idare_protocol_events"] = events
events.append({
    "timestamp_utc": now,
    "type": "analysis",
    "name": "I-DARE minimal redesigned-task first-pass report",
    "status": f"complete pending human review; diagnosis={diagnosis}",
    "evidence": str(REPORT_MD_PATH),
    "next_allowed_step": "human review / closeout before next objective",
    "blocked": blocked,
})
write_json(STATUS_JSON_PATH, status)

status_md = STATUS_MD_PATH.read_text(encoding="utf-8")
append = f"""

## I-DARE Minimal Redesigned-Task First-Pass Report

Updated: `{now}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE minimal redesigned-task first-pass report | complete pending human review; diagnosis=`{diagnosis}` | `docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.md` | Human review / closeout before next objective. | direct full SupCon/DG training; broad hyperparameter search; EEG+EMG fusion; final LOSO claim; mainline change |

- Frozen 48-row minimal first-pass matrix was executed.
- Recommended next objective is `{recommended_next_objective}` only after human review.
"""
if "I-DARE Minimal Redesigned-Task First-Pass Report" not in status_md:
    STATUS_MD_PATH.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

print("OK_MINIMAL_REDESIGNED_TASK_FIRST_PASS_REPORT_WRITTEN")
print(REPORT_MD_PATH)
print(REPORT_JSON_PATH)
print(RUNS_CSV_PATH)
print(PRED_CSV_PATH)
print(METRIC_CSV_PATH)
print(SUBJECT_CSV_PATH)
print("runs=", len(runs_df))
print("predictions=", len(pred_df))
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next_objective)
print("best_ridge_cell=", json.dumps(report["best_ridge_cell"], ensure_ascii=False))
PY
echo

echo "===== 5) validate first-pass outputs ====="
"$PY" - <<'PY'
import json
from pathlib import Path
import pandas as pd

json_paths = [
    Path("docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

runs = pd.read_csv("docs/idare_label_semantics_minimal_redesigned_task_first_pass_runs.csv")
pred = pd.read_csv("docs/idare_label_semantics_minimal_redesigned_task_first_pass_predictions.csv")
metric = pd.read_csv("docs/idare_label_semantics_minimal_redesigned_task_first_pass_metric_summary.csv")
subj = pd.read_csv("docs/idare_label_semantics_minimal_redesigned_task_first_pass_subject_error_summary.csv")
print("runs_rows=", len(runs))
print("predictions_rows=", len(pred))
print("metric_summary_rows=", len(metric))
print("subject_error_rows=", len(subj))
if len(runs) != 48:
    raise SystemExit(f"ERROR: expected 48 runs, got {len(runs)}")
allowed_models = {"mean_baseline_no_training", "ridge_regression_summary_features"}
if not set(runs["model"].astype(str).unique()).issubset(allowed_models):
    raise SystemExit("ERROR: unregistered model in runs")
required_metrics = ["spearman_rho", "mae_rank_percentile", "rmse_rank_percentile", "top_bottom_q33_balanced_accuracy"]
for c in required_metrics:
    if c not in runs.columns:
        raise SystemExit(f"ERROR: missing metric column {c}")
if pred.empty:
    raise SystemExit("ERROR: empty predictions")

report = json.loads(Path("docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.json").read_text(encoding="utf-8"))
if report["n_runs"] != 48:
    raise SystemExit("ERROR: report n_runs != 48")
if "direct full SupCon/DG training" not in report.get("blocked", []):
    raise SystemExit("ERROR: missing blocked direct full SupCon/DG training")
print("diagnosis=", report["diagnosis"])
print("recommended_next_objective=", report["recommended_next_objective"])
print("ALL_MINIMAL_REDESIGNED_TASK_FIRST_PASS_OUTPUTS_VALID")
PY

grep -nE "Status|Run Matrix|Key Indicators|Metric Summary|Top Ridge Cells|Interpretation|Next Allowed Step" \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.md
grep -nE "Minimal Redesigned-Task First-Pass Report|Frozen 48-row|minimal first-pass report|Recommended next objective" docs/project_status_current.md | tail -n 10
echo

echo "===== 6) file list ====="
ls -lh \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.md \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.json \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_runs.csv \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_predictions.csv \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_metric_summary.csv \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_subject_error_summary.csv \
  docs/project_status_current.json \
  docs/project_status_current.md
echo

echo "===== 7) status before commit ====="
git status --short --branch
echo

echo "===== 8) commit and push minimal redesigned-task first-pass outputs ====="
git add \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.md \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.json \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_runs.csv \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_predictions.csv \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_metric_summary.csv \
  docs/idare_label_semantics_minimal_redesigned_task_first_pass_subject_error_summary.csv \
  docs/project_status_current.json \
  docs/project_status_current.md

git commit -m "analysis: run I-DARE minimal redesigned task first pass"
git push origin main
echo

echo "===== 9) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=$LOG_PATH"
