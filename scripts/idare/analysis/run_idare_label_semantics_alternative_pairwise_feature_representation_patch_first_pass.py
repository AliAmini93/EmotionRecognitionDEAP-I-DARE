#!/usr/bin/env python3
"""Run the frozen I-DARE pairwise feature-representation patch first-pass matrix.

This is intentionally narrow:
- EEG/arousal only
- fixed within-subject pairwise preference formulation
- fixed 96-row matrix
- classical controls and two classical learned baselines only
- no broad search, no SupCon/DG, no fusion, no final claim
"""

from __future__ import annotations

import csv
import json
import math
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.preprocessing import RobustScaler, StandardScaler

warnings.filterwarnings("ignore", category=ConvergenceWarning)

DOCS = Path("docs")
CACHE_INDEX = Path(".cache/idare_eeg_cache_index_baseline_corrected.csv")
WINDOWS_NPY = Path(".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy")

OBJECTIVE_JSON = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_objective.json"
REVIEW_JSON = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_tests_review_status.json"
SMOKE_REPORT_JSON = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_tests_report.json"
SPEC_JSON = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_spec.json"
RUN_MATRIX_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_run_matrix.csv"
FEATURE_DEF_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_feature_set_definition.csv"
THRESHOLDS_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_metric_thresholds.csv"
GUARDRAILS_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_guardrails.csv"

REPORT_MD = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_report.md"
REPORT_JSON = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_report.json"
RUNS_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_runs.csv"
PREDICTIONS_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_predictions.csv"
METRIC_SUMMARY_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_metric_summary.csv"
SUBJECT_LIFT_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_subject_lift_summary.csv"
DECISION_MATRIX_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_decision_matrix.csv"
PAIR_AUDIT_CSV = DOCS / "idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_pair_audit.csv"

STATUS_JSON = DOCS / "project_status_current.json"
STATUS_MD = DOCS / "project_status_current.md"

FS = 128.0
BANDS = [
    ("theta_4_8", 4.0, 8.0),
    ("alpha_8_13", 8.0, 13.0),
    ("beta_13_30", 13.0, 30.0),
    ("gamma_30_45", 30.0, 45.0),
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise SystemExit(f"ERROR: no rows for {path}")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def append_csv_rows(path: Path, rows: list[dict[str, Any]], header_written: bool) -> bool:
    if not rows:
        return header_written
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        if not header_written:
            writer.writeheader()
            header_written = True
        writer.writerows(rows)
    return header_written


def md_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(r.get(c, "")).replace("|", "\\|").replace("\n", " ") for c in cols) + " |")
    return "\n".join(out)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out


def find_col(df: pd.DataFrame, preferred: list[str], contains: str | None = None) -> str | None:
    lower = {str(c).lower(): str(c) for c in df.columns}
    for name in preferred:
        if name.lower() in lower:
            return lower[name.lower()]
    if contains:
        candidates = []
        for c in df.columns:
            lc = str(c).lower()
            if contains.lower() in lc:
                candidates.append(str(c))
        numeric = [c for c in candidates if pd.api.types.is_numeric_dtype(df[c])]
        if numeric:
            def score(c: str) -> tuple[int, int]:
                lc = c.lower()
                good = int(any(tok in lc for tok in ["rating", "label", "score", contains.lower()]))
                bad = int(any(tok in lc for tok in ["pred", "prediction", "rank", "fold"]))
                return (bad, -good)
            return sorted(numeric, key=score)[0]
        if candidates:
            return candidates[0]
    return None


def derive_subject_fold(subject_values: pd.Series, n_folds: int = 6) -> pd.Series:
    unique_subjects = sorted(subject_values.astype(str).unique())
    mapping = {s: (i % n_folds) + 1 for i, s in enumerate(unique_subjects)}
    return subject_values.astype(str).map(mapping).astype(int)


def temporal_features(windows: np.ndarray) -> np.ndarray:
    x = windows.astype(np.float32, copy=False)
    mean = x.mean(axis=-1)
    std = x.std(axis=-1)
    rms = np.sqrt(np.mean(np.square(x), axis=-1))
    line_length = np.mean(np.abs(np.diff(x, axis=-1)), axis=-1)
    return np.concatenate([mean, std, rms, line_length], axis=1).astype(np.float32, copy=False)


def bandpower_features(windows: np.ndarray) -> np.ndarray:
    x = windows.astype(np.float32, copy=False)
    freqs = np.fft.rfftfreq(x.shape[-1], d=1.0 / FS)
    spectrum = np.fft.rfft(x, axis=-1)
    power = (np.abs(spectrum) ** 2).astype(np.float32, copy=False)
    outputs = []
    for _, lo, hi in BANDS:
        mask = (freqs >= lo) & (freqs < hi)
        if not np.any(mask):
            outputs.append(np.zeros(x.shape[:2], dtype=np.float32))
        else:
            outputs.append(power[:, :, mask].mean(axis=-1))
    return np.concatenate(outputs, axis=1).astype(np.float32, copy=False)


def make_pair_index(df: pd.DataFrame, subject_col: str, label_col: str, row_indices: np.ndarray) -> dict[str, np.ndarray]:
    left: list[int] = []
    right: list[int] = []
    y: list[int] = []
    subjects: list[str] = []
    for subject, g in df.loc[row_indices].groupby(subject_col, dropna=False):
        inds = g.index.to_numpy(dtype=int)
        labels = pd.to_numeric(g[label_col], errors="coerce").to_numpy(dtype=float)
        n = len(inds)
        if n < 2:
            continue
        for a_pos in range(n - 1):
            la = labels[a_pos]
            if not np.isfinite(la):
                continue
            for b_pos in range(a_pos + 1, n):
                lb = labels[b_pos]
                if not np.isfinite(lb) or la == lb:
                    continue
                left.append(int(inds[a_pos]))
                right.append(int(inds[b_pos]))
                y.append(1 if la > lb else 0)
                subjects.append(str(subject))
    return {
        "left": np.asarray(left, dtype=np.int32),
        "right": np.asarray(right, dtype=np.int32),
        "y": np.asarray(y, dtype=np.int8),
        "subject": np.asarray(subjects, dtype=object),
    }


def pair_features(base: np.ndarray, left: np.ndarray, right: np.ndarray) -> np.ndarray:
    diff = base[left] - base[right]
    absdiff = np.abs(diff)
    return np.concatenate([diff, absdiff], axis=1).astype(np.float32, copy=False)


def scale_pair_features(feature_set_id: str, x_train: np.ndarray, x_val: np.ndarray) -> tuple[np.ndarray, np.ndarray, str]:
    if feature_set_id == "robust_scaled_current_summary_diff_control":
        scaler = RobustScaler(with_centering=True, with_scaling=True, quantile_range=(25, 75))
        scaler_name = "RobustScaler_train_fold_only"
    else:
        scaler = StandardScaler(with_mean=True, with_std=True)
        scaler_name = "StandardScaler_train_fold_only"
    xtr = scaler.fit_transform(x_train)
    xva = scaler.transform(x_val)
    return xtr.astype(np.float32, copy=False), xva.astype(np.float32, copy=False), scaler_name


def safe_bal_acc(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if y_true.size == 0:
        return math.nan
    return float(balanced_accuracy_score(y_true, y_pred))


def safe_macro_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    if y_true.size == 0:
        return math.nan
    return float(f1_score(y_true, y_pred, average="macro", zero_division=0))


def prediction_rows_for_run(
    objective_run_id: int,
    feature_set_id: str,
    model: str,
    fold: int,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    subject: np.ndarray,
    left: np.ndarray,
    right: np.ndarray,
    score: np.ndarray | None,
) -> list[dict[str, Any]]:
    rows = []
    if score is None:
        score = np.full_like(y_true, np.nan, dtype=float)
    for i in range(len(y_true)):
        rows.append({
            "objective_run_id": objective_run_id,
            "feature_set_id": feature_set_id,
            "model": model,
            "fold": fold,
            "subject": str(subject[i]),
            "left_index": int(left[i]),
            "right_index": int(right[i]),
            "y_true": int(y_true[i]),
            "y_pred": int(y_pred[i]),
            "score": "" if not np.isfinite(score[i]) else float(score[i]),
        })
    return rows


def summarize_metrics(runs: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    for (feature_set_id, model), g in runs.groupby(["feature_set_id", "model"], dropna=False):
        g = g.copy()
        majority = runs[
            (runs["feature_set_id"].astype(str) == str(feature_set_id))
            & (runs["model"].astype(str) == "majority_train_label_no_training")
        ]
        random_base = runs[
            (runs["feature_set_id"].astype(str) == str(feature_set_id))
            & (runs["model"].astype(str) == "random_balanced_no_training")
        ]
        mean_majority = float(majority["balanced_accuracy"].mean()) if len(majority) else math.nan
        mean_random = float(random_base["balanced_accuracy"].mean()) if len(random_base) else math.nan
        rows.append({
            "feature_set_id": feature_set_id,
            "model": model,
            "training_category": str(g["training_category"].iloc[0]),
            "n_runs": int(len(g)),
            "mean_accuracy": float(g["accuracy"].mean()),
            "mean_balanced_accuracy": float(g["balanced_accuracy"].mean()),
            "std_balanced_accuracy": float(g["balanced_accuracy"].std(ddof=0)),
            "min_balanced_accuracy": float(g["balanced_accuracy"].min()),
            "max_balanced_accuracy": float(g["balanced_accuracy"].max()),
            "mean_macro_f1": float(g["macro_f1"].mean()),
            "mean_pred_positive_rate": float(g["pred_positive_rate"].mean()),
            "mean_majority_baseline_bal_acc": mean_majority,
            "mean_random_baseline_bal_acc": mean_random,
            "delta_vs_majority_baseline_bal_acc": float(g["balanced_accuracy"].mean() - mean_majority) if np.isfinite(mean_majority) else math.nan,
            "delta_vs_random_baseline_bal_acc": float(g["balanced_accuracy"].mean() - mean_random) if np.isfinite(mean_random) else math.nan,
            "folds_over_055_bal_acc": int((g["balanced_accuracy"] >= 0.55).sum()),
            "folds_under_045_bal_acc": int((g["balanced_accuracy"] < 0.45).sum()),
            "positive_delta_folds_vs_majority": int((g["balanced_accuracy"].to_numpy() - majority.sort_values("fold")["balanced_accuracy"].to_numpy() > 0).sum()) if len(majority) == len(g) else -1,
        })
    return rows


def subject_lift_summary(preds: pd.DataFrame, best_feature_set: str, best_model: str) -> list[dict[str, Any]]:
    best = preds[
        (preds["feature_set_id"].astype(str) == str(best_feature_set))
        & (preds["model"].astype(str) == str(best_model))
    ].copy()
    base = preds[
        (preds["feature_set_id"].astype(str) == str(best_feature_set))
        & (preds["model"].astype(str) == "majority_train_label_no_training")
    ].copy()
    rows = []
    if best.empty or base.empty:
        return rows

    best["correct"] = (best["y_true"].astype(int) == best["y_pred"].astype(int)).astype(float)
    base["correct"] = (base["y_true"].astype(int) == base["y_pred"].astype(int)).astype(float)

    best_sub = best.groupby("subject")["correct"].agg(["count", "mean"]).reset_index().rename(columns={"count": "n_pairs", "mean": "best_accuracy"})
    base_sub = base.groupby("subject")["correct"].agg(["mean"]).reset_index().rename(columns={"mean": "majority_accuracy"})
    merged = best_sub.merge(base_sub, on="subject", how="left")
    for _, r in merged.iterrows():
        delta = float(r["best_accuracy"] - r["majority_accuracy"])
        rows.append({
            "feature_set_id": best_feature_set,
            "model": best_model,
            "subject": str(r["subject"]),
            "n_pairs": int(r["n_pairs"]),
            "best_accuracy": float(r["best_accuracy"]),
            "majority_accuracy": float(r["majority_accuracy"]),
            "subject_delta_vs_majority_accuracy": delta,
            "positive_lift": bool(delta > 0),
        })
    return rows


def main() -> None:
    created = now_utc()
    objective = read_json(OBJECTIVE_JSON)
    review = read_json(REVIEW_JSON)
    smoke = read_json(SMOKE_REPORT_JSON)
    spec = read_json(SPEC_JSON)

    if objective.get("status") != "objective_created":
        raise SystemExit("ERROR: objective status mismatch")
    if objective.get("limited_first_pass_authorized") is not True:
        raise SystemExit("ERROR: objective must authorize limited first pass")
    if objective.get("training_authorized_scope") != "limited_to_frozen_96_row_matrix":
        raise SystemExit("ERROR: objective training scope must be limited_to_frozen_96_row_matrix")
    if objective.get("model_search_authorized") is not False:
        raise SystemExit("ERROR: objective must not authorize model search")
    if objective.get("supcon_dg_authorized") is not False:
        raise SystemExit("ERROR: objective must not authorize SupCon/DG")
    if objective.get("fusion_authorized") is not False:
        raise SystemExit("ERROR: objective must not authorize fusion")
    if objective.get("final_loso_claim_authorized") is not False:
        raise SystemExit("ERROR: objective must not authorize final claim")
    if review.get("accepted_diagnosis") != "feature_representation_patch_smoke_tests_passed":
        raise SystemExit("ERROR: smoke review diagnosis mismatch")
    if smoke.get("diagnosis") != "feature_representation_patch_smoke_tests_passed" or smoke.get("all_passed") is not True:
        raise SystemExit("ERROR: smoke report did not pass")

    run_matrix = normalize_columns(pd.read_csv(RUN_MATRIX_CSV))
    feature_def = normalize_columns(pd.read_csv(FEATURE_DEF_CSV))
    thresholds = normalize_columns(pd.read_csv(THRESHOLDS_CSV))
    guardrails = normalize_columns(pd.read_csv(GUARDRAILS_CSV))
    idx = normalize_columns(pd.read_csv(CACHE_INDEX))
    windows = np.load(WINDOWS_NPY, mmap_mode="r")

    if len(run_matrix) != 96:
        raise SystemExit(f"ERROR: frozen matrix must have 96 rows, got {len(run_matrix)}")
    if set(run_matrix["modality"].astype(str)) != {"EEG"}:
        raise SystemExit("ERROR: matrix modality scope must be EEG only")
    if set(run_matrix["task"].astype(str)) != {"arousal"}:
        raise SystemExit("ERROR: matrix task scope must be arousal only")
    expected_models = {
        "random_balanced_no_training",
        "majority_train_label_no_training",
        "ridge_classifier_pairwise_feature_patch",
        "logistic_regression_pairwise_feature_patch",
    }
    if set(run_matrix["model"].astype(str)) != expected_models:
        raise SystemExit("ERROR: model scope mismatch")
    expected_features = {
        "current_summary_diff_control",
        "robust_scaled_current_summary_diff_control",
        "bandpower_only_control_v1",
        "bandpower_temporal_stats_v1",
    }
    if set(run_matrix["feature_set_id"].astype(str)) != expected_features:
        raise SystemExit("ERROR: feature-set scope mismatch")

    subject_col = find_col(idx, ["subject", "subject_id", "participant", "participant_id", "subj", "s"], contains="subject")
    arousal_col = find_col(idx, ["arousal", "arousal_rating", "rating_arousal", "arousal_label", "label_arousal"], contains="arousal")
    if subject_col is None or arousal_col is None:
        raise SystemExit("ERROR: could not identify subject/arousal columns")
    idx["_patch_fold"] = derive_subject_fold(idx[subject_col], n_folds=6)

    print(f"BUILDING_FEATURE_PATCH_SAMPLE_FEATURES shape={list(windows.shape)}")
    x = np.asarray(windows, dtype=np.float32)
    temporal = temporal_features(x)
    bandpower = bandpower_features(x)
    features = {
        "current_summary_diff_control": temporal,
        "robust_scaled_current_summary_diff_control": temporal,
        "bandpower_only_control_v1": bandpower,
        "bandpower_temporal_stats_v1": np.concatenate([bandpower, temporal], axis=1).astype(np.float32, copy=False),
    }

    pair_by_fold: dict[int, dict[str, dict[str, np.ndarray]]] = {}
    pair_audit_rows = []
    for fold in range(1, 7):
        train_idx = idx.index[idx["_patch_fold"] != fold].to_numpy(dtype=int)
        val_idx = idx.index[idx["_patch_fold"] == fold].to_numpy(dtype=int)
        train_pairs = make_pair_index(idx, subject_col, arousal_col, train_idx)
        val_pairs = make_pair_index(idx, subject_col, arousal_col, val_idx)
        pair_by_fold[fold] = {"train": train_pairs, "val": val_pairs}
        pair_audit_rows.append({
            "fold": fold,
            "n_train_pairs": int(len(train_pairs["y"])),
            "n_val_pairs": int(len(val_pairs["y"])),
            "train_positive_rate": float(train_pairs["y"].mean()) if len(train_pairs["y"]) else math.nan,
            "val_positive_rate": float(val_pairs["y"].mean()) if len(val_pairs["y"]) else math.nan,
            "n_val_subjects": int(len(set(val_pairs["subject"].astype(str)))),
            "same_subject_only_by_construction": True,
        })
    write_csv(PAIR_AUDIT_CSV, pair_audit_rows)

    run_rows: list[dict[str, Any]] = []
    pred_header_written = False
    if PREDICTIONS_CSV.exists():
        PREDICTIONS_CSV.unlink()

    # Cache transformed pair features per (feature_set_id, fold).
    pair_feature_cache: dict[tuple[str, int], tuple[np.ndarray, np.ndarray, str]] = {}

    for _, row in run_matrix.sort_values("objective_run_id").iterrows():
        run_id = int(row["objective_run_id"])
        feature_set_id = str(row["feature_set_id"])
        model_name = str(row["model"])
        training_category = str(row["training_category"])
        fold = int(row["fold"])
        pairs = pair_by_fold[fold]
        train_pairs = pairs["train"]
        val_pairs = pairs["val"]
        y_train = train_pairs["y"].astype(int)
        y_val = val_pairs["y"].astype(int)

        if len(y_val) == 0 or len(y_train) == 0:
            raise SystemExit(f"ERROR: empty train/val pairs for run {run_id}")

        score = None
        if model_name == "random_balanced_no_training":
            rng = np.random.default_rng(100000 + run_id)
            y_pred = rng.integers(0, 2, size=len(y_val)).astype(int)
            fit_status = "no_training_random_balanced"
            scaler_name = "none"
        elif model_name == "majority_train_label_no_training":
            counts = np.bincount(y_train, minlength=2)
            maj = int(np.argmax(counts))
            y_pred = np.full(len(y_val), maj, dtype=int)
            fit_status = "no_training_majority_train_label"
            scaler_name = "none"
        else:
            cache_key = (feature_set_id, fold)
            if cache_key not in pair_feature_cache:
                base = features[feature_set_id]
                x_train_raw = pair_features(base, train_pairs["left"], train_pairs["right"])
                x_val_raw = pair_features(base, val_pairs["left"], val_pairs["right"])
                x_train, x_val, scaler_name = scale_pair_features(feature_set_id, x_train_raw, x_val_raw)
                if not np.isfinite(x_train).all() or not np.isfinite(x_val).all():
                    raise SystemExit(f"ERROR: non-finite pair features for {feature_set_id} fold={fold}")
                pair_feature_cache[cache_key] = (x_train, x_val, scaler_name)
            x_train, x_val, scaler_name = pair_feature_cache[cache_key]

            if model_name == "ridge_classifier_pairwise_feature_patch":
                clf = RidgeClassifier(alpha=1.0)
            elif model_name == "logistic_regression_pairwise_feature_patch":
                clf = LogisticRegression(
                    penalty="l2",
                    C=1.0,
                    solver="liblinear",
                    max_iter=1000,
                    random_state=1729 + run_id,
                )
            else:
                raise SystemExit(f"ERROR: unsupported model {model_name}")

            clf.fit(x_train, y_train)
            y_pred = clf.predict(x_val).astype(int)
            if hasattr(clf, "decision_function"):
                score = np.asarray(clf.decision_function(x_val), dtype=float)
            elif hasattr(clf, "predict_proba"):
                score = np.asarray(clf.predict_proba(x_val)[:, 1], dtype=float)
            fit_status = "fit_train_fold_only"

        acc = float(accuracy_score(y_val, y_pred))
        bal = safe_bal_acc(y_val, y_pred)
        macro = safe_macro_f1(y_val, y_pred)
        pred_pos = float(np.mean(y_pred)) if len(y_pred) else math.nan

        run_row = {
            "objective_run_id": run_id,
            "feature_set_id": feature_set_id,
            "patch_candidate_id": str(row["patch_candidate_id"]),
            "model": model_name,
            "training_category": training_category,
            "modality": str(row["modality"]),
            "task": str(row["task"]),
            "fold": fold,
            "n_train_pairs": int(len(y_train)),
            "n_val_pairs": int(len(y_val)),
            "train_positive_rate": float(y_train.mean()),
            "val_positive_rate": float(y_val.mean()),
            "accuracy": acc,
            "balanced_accuracy": bal,
            "macro_f1": macro,
            "pred_positive_rate": pred_pos,
            "one_class_pred": bool(len(set(y_pred.tolist())) < 2),
            "scaler": scaler_name,
            "fit_status": fit_status,
        }
        run_rows.append(run_row)
        pred_rows = prediction_rows_for_run(
            run_id,
            feature_set_id,
            model_name,
            fold,
            y_val,
            y_pred,
            val_pairs["subject"],
            val_pairs["left"],
            val_pairs["right"],
            score,
        )
        pred_header_written = append_csv_rows(PREDICTIONS_CSV, pred_rows, pred_header_written)

        print(json.dumps({
            "objective_run_id": run_id,
            "feature_set_id": feature_set_id,
            "model": model_name,
            "fold": fold,
            "balanced_accuracy": round(bal, 4),
            "macro_f1": round(macro, 4),
            "n_val_pairs": int(len(y_val)),
        }, sort_keys=True))

    write_csv(RUNS_CSV, run_rows)
    runs_df = pd.DataFrame(run_rows)
    summary_rows = summarize_metrics(runs_df)
    write_csv(METRIC_SUMMARY_CSV, summary_rows)
    summary_df = pd.DataFrame(summary_rows)

    learned = summary_df[summary_df["training_category"].astype(str).eq("minimal_classical_pairwise_patch")].copy()
    if learned.empty:
        raise SystemExit("ERROR: no learned cells in summary")
    learned = learned.sort_values(
        ["mean_balanced_accuracy", "delta_vs_majority_baseline_bal_acc", "folds_over_055_bal_acc"],
        ascending=[False, False, False],
    )
    best = learned.iloc[0].to_dict()

    preds_df = pd.read_csv(PREDICTIONS_CSV)
    subject_rows = subject_lift_summary(preds_df, str(best["feature_set_id"]), str(best["model"]))
    write_csv(SUBJECT_LIFT_CSV, subject_rows)
    subject_positive_fraction = float(np.mean([r["positive_lift"] for r in subject_rows])) if subject_rows else math.nan

    mean_bal = float(best["mean_balanced_accuracy"])
    delta_majority = float(best["delta_vs_majority_baseline_bal_acc"])
    folds_over_055 = int(best["folds_over_055_bal_acc"])
    folds_under_045 = int(best["folds_under_045_bal_acc"])

    threshold_rows = [
        {
            "threshold_id": "T1_actionable_patch_signal",
            "metric": "mean_balanced_accuracy",
            "observed": mean_bal,
            "pass": bool(mean_bal >= 0.55),
            "decision": "candidate for narrow confirmation objective if also fold stability passes",
        },
        {
            "threshold_id": "T2_fold_stability",
            "metric": "folds_over_055_bal_acc_and_no_folds_under_045",
            "observed": f"folds_over_055={folds_over_055}; folds_under_045={folds_under_045}",
            "pass": bool(folds_over_055 >= 3 and folds_under_045 == 0),
            "decision": "supports non-spurious patch signal",
        },
        {
            "threshold_id": "T3_control_lift",
            "metric": "delta_vs_majority_baseline_bal_acc",
            "observed": delta_majority,
            "pass": bool(delta_majority >= 0.03),
            "decision": "practical improvement over majority control",
        },
        {
            "threshold_id": "T4_subject_lift",
            "metric": "subject_positive_lift_fraction",
            "observed": subject_positive_fraction,
            "pass": bool(subject_positive_fraction >= 0.65),
            "decision": "supports broader subject-level lift",
        },
        {
            "threshold_id": "T5_archive_floor",
            "metric": "mean_balanced_accuracy_below_053_or_no_improvement",
            "observed": f"mean_bal={mean_bal}; delta={delta_majority}",
            "pass": bool(not (mean_bal < 0.53 or delta_majority <= 0.0)),
            "decision": "archive patch branch or redesign representation if floor fails",
        },
    ]
    write_csv(DECISION_MATRIX_CSV, threshold_rows)

    if all(r["pass"] for r in threshold_rows[:4]):
        diagnosis = "feature_representation_patch_first_pass_actionable_signal"
        recommended_next = "label_semantics_alternative_pairwise_feature_representation_patch_confirmation_objective"
        next_allowed_step = "human_review_closeout_then_create_feature_patch_confirmation_objective"
    elif mean_bal >= 0.53 and delta_majority > 0.0:
        diagnosis = "feature_representation_patch_first_pass_weak_mixed_signal"
        recommended_next = "label_semantics_alternative_pairwise_feature_patch_failure_or_metric_debug_objective"
        next_allowed_step = "human_review_closeout_then_create_feature_patch_failure_or_metric_debug_objective"
    else:
        diagnosis = "feature_representation_patch_first_pass_no_actionable_signal"
        recommended_next = "label_semantics_alternative_pairwise_feature_patch_archive_or_rethink_objective"
        next_allowed_step = "human_review_closeout_then_archive_or_rethink_feature_patch"

    blocked = [
        "broad hyperparameter search",
        "direct full SupCon/DG training",
        "EEG+EMG fusion",
        "final LOSO claim",
        "changing label formulation during this patch branch",
        "confirmation training before review",
    ]

    report = {
        "status": "complete_pending_human_review",
        "created_utc": created,
        "source_objective": str(OBJECTIVE_JSON),
        "source_run_matrix": str(RUN_MATRIX_CSV),
        "diagnosis": diagnosis,
        "recommended_next_objective": recommended_next,
        "next_allowed_step": next_allowed_step,
        "selected_primary_patch": spec.get("selected_primary_patch"),
        "selected_formulation": spec.get("selected_formulation"),
        "runs": len(run_rows),
        "predictions": int(sum(1 for _ in open(PREDICTIONS_CSV, "r", encoding="utf-8")) - 1),
        "best_cell": best,
        "subject_positive_lift_fraction": subject_positive_fraction,
        "limited_first_pass_completed": True,
        "broad_model_search_authorized": False,
        "model_search_authorized": False,
        "supcon_dg_authorized": False,
        "fusion_authorized": False,
        "final_loso_claim_authorized": False,
        "outputs": {
            "runs": str(RUNS_CSV),
            "predictions": str(PREDICTIONS_CSV),
            "metric_summary": str(METRIC_SUMMARY_CSV),
            "subject_lift_summary": str(SUBJECT_LIFT_CSV),
            "decision_matrix": str(DECISION_MATRIX_CSV),
            "pair_audit": str(PAIR_AUDIT_CSV),
        },
        "blocked": blocked,
    }
    write_json(REPORT_JSON, report)

    status = read_json(STATUS_JSON)
    status["last_updated_utc"] = created
    status["current_idare_next_allowed_step"] = next_allowed_step
    status["current_idare_blocked_steps"] = blocked
    status["current_idare_pairwise_feature_patch_first_pass_status"] = f"complete_pending_human_review; diagnosis={diagnosis}"
    events = status.get("idare_protocol_events")
    if not isinstance(events, list):
        events = []
    status["idare_protocol_events"] = events
    events.append({
        "timestamp_utc": created,
        "type": "first_pass_report",
        "name": "I-DARE alternative pairwise feature patch first pass",
        "status": f"complete pending human review; diagnosis={diagnosis}",
        "evidence": str(REPORT_MD),
        "recommended_next_objective": recommended_next,
        "blocked": blocked,
    })
    write_json(STATUS_JSON, status)

    top_rows = summary_df.sort_values("mean_balanced_accuracy", ascending=False).head(8).to_dict("records")
    report_md = f"""# I-DARE Alternative Pairwise Feature-Representation Patch First-Pass Report

## Status

Status: complete; pending human review.

Created UTC: `{created}`

## Executive Result

Diagnosis: `{diagnosis}`

Recommended next objective: `{recommended_next}`

Runs executed: `{len(run_rows)}`

## Best Cell

| Metric | Value |
|---|---|
| feature_set_id | `{best["feature_set_id"]}` |
| model | `{best["model"]}` |
| mean_balanced_accuracy | `{float(best["mean_balanced_accuracy"]):.6f}` |
| delta_vs_majority_baseline_bal_acc | `{float(best["delta_vs_majority_baseline_bal_acc"]):.6f}` |
| delta_vs_random_baseline_bal_acc | `{float(best["delta_vs_random_baseline_bal_acc"]):.6f}` |
| folds_over_055_bal_acc | `{int(best["folds_over_055_bal_acc"])}` |
| folds_under_045_bal_acc | `{int(best["folds_under_045_bal_acc"])}` |
| subject_positive_lift_fraction | `{subject_positive_fraction:.6f}` |

## Top Cells

{md_table(top_rows, ["feature_set_id", "model", "mean_balanced_accuracy", "delta_vs_majority_baseline_bal_acc", "folds_over_055_bal_acc", "folds_under_045_bal_acc"])}

## Decision Matrix

{md_table(threshold_rows, ["threshold_id", "metric", "observed", "pass", "decision"])}

## Pair Audit

{md_table(pair_audit_rows, ["fold", "n_train_pairs", "n_val_pairs", "train_positive_rate", "val_positive_rate", "n_val_subjects"])}

## Interpretation

This was a limited first-pass run of the frozen 96-row feature patch matrix.

It does not authorize broad search, SupCon/DG, fusion, or a final LOSO claim.

## Next Allowed Step

`{next_allowed_step}`
"""
    REPORT_MD.write_text(report_md, encoding="utf-8")

    status_text = STATUS_MD.read_text(encoding="utf-8")
    append = f"""

## I-DARE Alternative Pairwise Feature-Representation Patch First-Pass Report

Updated: `{created}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE alternative pairwise feature patch first pass | complete pending human review; diagnosis=`{diagnosis}` | `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_report.md` | `{next_allowed_step}` | broad search; SupCon/DG; fusion; final claim; confirmation before review |

- Frozen 96-row matrix was executed.
- Best cell: `{best["feature_set_id"]}` / `{best["model"]}`.
- Mean balanced accuracy: `{float(best["mean_balanced_accuracy"]):.6f}`.
- Recommended next objective: `{recommended_next}` only after human review.
"""
    if "I-DARE Alternative Pairwise Feature-Representation Patch First-Pass Report" not in status_text:
        STATUS_MD.write_text(status_text.rstrip() + append + "\n", encoding="utf-8")

    print("OK_FEATURE_REPRESENTATION_PATCH_FIRST_PASS_REPORT_WRITTEN")
    print(REPORT_MD)
    print(REPORT_JSON)
    print(RUNS_CSV)
    print(PREDICTIONS_CSV)
    print(METRIC_SUMMARY_CSV)
    print(SUBJECT_LIFT_CSV)
    print(DECISION_MATRIX_CSV)
    print(PAIR_AUDIT_CSV)
    print("runs=", len(run_rows))
    print("predictions=", report["predictions"])
    print("diagnosis=", diagnosis)
    print("recommended_next_objective=", recommended_next)
    print("best_cell=", json.dumps(best, sort_keys=True))


if __name__ == "__main__":
    main()
