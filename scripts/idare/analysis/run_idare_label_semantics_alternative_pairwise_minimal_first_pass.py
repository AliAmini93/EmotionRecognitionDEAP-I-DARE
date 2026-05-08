#!/usr/bin/env python3
"""Minimal first-pass for I-DARE within-subject pairwise affect preference.

This is a frozen, guardrailed diagnostic first pass. It intentionally avoids
deep models, SupCon/DG, fusion, broad search, and final LOSO claims.
"""

from __future__ import annotations

import csv
import itertools
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

DOCS = Path("docs")
CACHE = Path(".cache")

OBJECTIVE_JSON = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_objective.json"
RUN_MATRIX_CSV = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_run_matrix.csv"
GUARDRAILS_CSV = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_guardrails.csv"
THRESHOLDS_CSV = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_metric_thresholds.csv"
SMOKE_REPORT_JSON = DOCS / "idare_label_semantics_alternative_formulation_smoke_tests_report.json"
DESIGN_SPEC_JSON = DOCS / "idare_label_semantics_alternative_formulation_design_spec.json"
PAIR_TARGET_AUDIT = DOCS / "idare_label_semantics_alternative_formulation_pair_target_audit.csv"

EEG_INDEX = CACHE / "idare_eeg_cache_index_baseline_corrected.csv"
EEG_WINDOWS = CACHE / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
EMG_INDEX = CACHE / "idare_emg_feature_cache_index.csv"
EMG_FEATURES = CACHE / "idare_emg_features.npy"

SCRIPT_PATH = Path("scripts/idare/analysis/run_idare_label_semantics_alternative_pairwise_minimal_first_pass.py")

REPORT_MD = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_report.md"
REPORT_JSON = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_report.json"
RUNS_OUT = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_runs.csv"
PRED_OUT = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_predictions.csv"
METRIC_SUMMARY_OUT = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_metric_summary.csv"
PAIR_AUDIT_OUT = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_pair_audit.csv"
SUBJECT_LIFT_OUT = DOCS / "idare_label_semantics_alternative_pairwise_minimal_first_pass_subject_lift_summary.csv"

STATUS_JSON = DOCS / "project_status_current.json"
STATUS_MD = DOCS / "project_status_current.md"


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


def md_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(c, "")).replace("|", "\\|").replace("\n", " ") for c in columns) + " |")
    return "\n".join(out)


def norm(name: str) -> str:
    return str(name).strip().lower().replace("-", "_").replace(" ", "_")


def find_col(df: pd.DataFrame, preferred: list[str], require_any: list[str] | None = None, avoid: list[str] | None = None) -> str | None:
    cols = list(df.columns)
    norms = {norm(c): c for c in cols}
    for p in preferred:
        if norm(p) in norms:
            return norms[norm(p)]
    req = [norm(x) for x in (require_any or [])]
    av = [norm(x) for x in (avoid or [])]
    scored: list[tuple[int, str]] = []
    for c in cols:
        n = norm(c)
        if av and any(a in n for a in av):
            continue
        if req and not any(r in n for r in req):
            continue
        score = 0
        for p in preferred:
            pn = norm(p)
            if pn in n:
                score += 10
            if n in pn:
                score += 5
        if "rating" in n:
            score += 3
        if "raw" in n or "score" in n:
            score += 2
        if "label" in n or "binary" in n or "class" in n:
            score -= 8
        if score > 0:
            scored.append((score, c))
    if not scored:
        return None
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored[0][1]


@dataclass
class TrialData:
    table: pd.DataFrame
    feature_map: dict[str, np.ndarray]
    metadata: dict[str, Any]


def load_trial_features(modality: str) -> TrialData:
    if modality == "EEG":
        index_path = EEG_INDEX
        feature_path = EEG_WINDOWS
    elif modality == "EMG":
        index_path = EMG_INDEX
        feature_path = EMG_FEATURES
    else:
        raise ValueError(modality)

    idx = pd.read_csv(index_path)
    arr = np.load(feature_path, mmap_mode="r")
    if len(idx) != arr.shape[0]:
        raise SystemExit(f"ERROR: {modality} index/features row mismatch: {len(idx)} vs {arr.shape[0]}")

    subj_col = find_col(idx, ["subject", "subject_id", "subj", "participant", "participant_id"], require_any=["subject", "subj", "participant"])
    trial_col = find_col(idx, ["trial", "trial_id", "trial_index", "video", "video_id", "clip", "clip_id", "stimulus", "stimulus_id", "movie", "movie_id"], require_any=["trial", "video", "clip", "stimulus", "movie"])
    val_col = find_col(idx, ["valence_rating", "rating_valence", "self_report_valence", "raw_valence", "valence_score", "valence"], require_any=["valence"], avoid=["pred", "prob"])
    aro_col = find_col(idx, ["arousal_rating", "rating_arousal", "self_report_arousal", "raw_arousal", "arousal_score", "arousal"], require_any=["arousal"], avoid=["pred", "prob"])

    missing = [name for name, col in [("subject", subj_col), ("trial", trial_col), ("valence", val_col), ("arousal", aro_col)] if col is None]
    if missing:
        raise SystemExit(f"ERROR: {modality} missing detected columns: {missing}; columns={list(idx.columns)}")

    work = idx[[subj_col, trial_col, val_col, aro_col]].copy()
    work.columns = ["subject", "trial", "valence", "arousal"]
    work["subject"] = work["subject"].astype(str)
    work["trial"] = work["trial"].astype(str)
    work["valence"] = pd.to_numeric(work["valence"], errors="coerce")
    work["arousal"] = pd.to_numeric(work["arousal"], errors="coerce")
    work["_row"] = np.arange(len(work), dtype=int)

    # Compact row-level summaries, then aggregate per subject/trial.
    if modality == "EEG":
        # arr shape expected n x channels x time. Use channel mean/std and global stats.
        x = np.asarray(arr)
        if x.ndim != 3:
            raise SystemExit(f"ERROR: expected EEG 3D array, got shape {x.shape}")
        print(f"BUILDING_EEG_PAIRWISE_SUMMARY_FEATURES shape={list(x.shape)}")
        row_feat = np.concatenate(
            [
                x.mean(axis=2),
                x.std(axis=2),
                x.mean(axis=(1, 2), keepdims=False)[:, None],
                x.std(axis=(1, 2), keepdims=False)[:, None],
            ],
            axis=1,
        ).astype(np.float32)
    else:
        x = np.asarray(arr)
        if x.ndim != 2:
            raise SystemExit(f"ERROR: expected EMG 2D array, got shape {x.shape}")
        print(f"BUILDING_EMG_PAIRWISE_SUMMARY_FEATURES shape={list(x.shape)}")
        row_feat = np.sign(x) * np.log1p(np.abs(x))
        row_feat = row_feat.astype(np.float32)

    feature_map: dict[str, np.ndarray] = {}
    rows: list[dict[str, Any]] = []
    for (subject, trial), g in work.groupby(["subject", "trial"], dropna=False):
        row_ids = g["_row"].to_numpy(dtype=int)
        feat = np.nanmean(row_feat[row_ids], axis=0)
        key = f"{subject}::{trial}"
        feature_map[key] = feat.astype(np.float32)
        rows.append({
            "subject": str(subject),
            "trial": str(trial),
            "valence": float(g["valence"].median()),
            "arousal": float(g["arousal"].median()),
            "n_rows": int(len(g)),
            "feature_key": key,
        })

    table = pd.DataFrame(rows)
    metadata = {
        "modality": modality,
        "index_path": str(index_path),
        "feature_path": str(feature_path),
        "index_rows": int(len(idx)),
        "feature_shape": list(arr.shape),
        "trial_rows": int(len(table)),
        "n_subjects": int(table["subject"].nunique()),
        "feature_dim": int(next(iter(feature_map.values())).shape[0]) if feature_map else 0,
        "detected_columns": {"subject": subj_col, "trial": trial_col, "valence": val_col, "arousal": aro_col},
    }
    return TrialData(table=table, feature_map=feature_map, metadata=metadata)


def infer_margin(values: pd.Series) -> float:
    vals = pd.to_numeric(values, errors="coerce").dropna()
    if vals.empty:
        return 0.0
    value_range = float(vals.max() - vals.min())
    if value_range <= 1.5:
        return 0.125
    return 1.0


def build_oriented_pairs(td: TrialData, task: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    trial = td.table.dropna(subset=[task]).copy()
    margin = infer_margin(trial[task])
    rows: list[dict[str, Any]] = []
    possible = 0
    excluded = 0
    for subject, g in trial.groupby("subject"):
        g = g.sort_values("trial").reset_index(drop=True)
        possible += len(g) * (len(g) - 1) // 2
        for i, j in itertools.combinations(range(len(g)), 2):
            r1 = float(g.loc[i, task])
            r2 = float(g.loc[j, task])
            diff = r1 - r2
            if not np.isfinite(diff) or abs(diff) < margin or diff == 0:
                excluded += 1
                continue
            t1 = str(g.loc[i, "trial"])
            t2 = str(g.loc[j, "trial"])
            k1 = str(g.loc[i, "feature_key"])
            k2 = str(g.loc[j, "feature_key"])
            canonical = "::".join([str(subject)] + sorted([t1, t2]))
            # Counterbalanced orientations.
            rows.append({
                "task": task, "subject": str(subject), "trial_a": t1, "trial_b": t2,
                "feature_key_a": k1, "feature_key_b": k2, "canonical_pair_key": canonical,
                "rating_a": r1, "rating_b": r2, "label": int(r1 > r2), "orientation": "forward",
            })
            rows.append({
                "task": task, "subject": str(subject), "trial_a": t2, "trial_b": t1,
                "feature_key_a": k2, "feature_key_b": k1, "canonical_pair_key": canonical,
                "rating_a": r2, "rating_b": r1, "label": int(r2 > r1), "orientation": "reverse",
            })
    pairs = pd.DataFrame(rows)
    meta = {
        "task": task,
        "margin": margin,
        "possible_unoriented_pairs": int(possible),
        "excluded_unoriented_pairs": int(excluded),
        "kept_unoriented_pairs": int(len(rows) // 2),
        "kept_oriented_pairs": int(len(rows)),
        "n_subjects": int(pairs["subject"].nunique()) if len(pairs) else 0,
        "positive_rate": float(pairs["label"].mean()) if len(pairs) else math.nan,
    }
    return pairs, meta


def make_folds(subjects: list[str], n_folds: int = 6) -> dict[str, int]:
    subjects_sorted = sorted(map(str, subjects))
    return {s: (i % n_folds) + 1 for i, s in enumerate(subjects_sorted)}


def pair_features(pairs: pd.DataFrame, fmap: dict[str, np.ndarray]) -> np.ndarray:
    a = np.stack([fmap[k] for k in pairs["feature_key_a"].astype(str)], axis=0)
    b = np.stack([fmap[k] for k in pairs["feature_key_b"].astype(str)], axis=0)
    diff = a - b
    absdiff = np.abs(diff)
    return np.concatenate([diff, absdiff], axis=1).astype(np.float32)


def balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    vals: list[float] = []
    for cls in [0, 1]:
        mask = y_true == cls
        if mask.sum() == 0:
            continue
        vals.append(float((y_pred[mask] == cls).mean()))
    return float(np.mean(vals)) if vals else math.nan


def macro_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    vals: list[float] = []
    for cls in [0, 1]:
        tp = int(((y_true == cls) & (y_pred == cls)).sum())
        fp = int(((y_true != cls) & (y_pred == cls)).sum())
        fn = int(((y_true == cls) & (y_pred != cls)).sum())
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        vals.append(2 * precision * recall / (precision + recall) if (precision + recall) else 0.0)
    return float(np.mean(vals))


def model_predict(model_name: str, train_pairs: pd.DataFrame, val_pairs: pd.DataFrame, fmap: dict[str, np.ndarray], seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y_train = train_pairs["label"].to_numpy(dtype=int)

    if model_name == "random_balanced_no_training":
        return rng.integers(0, 2, size=len(val_pairs), dtype=int)

    if model_name == "majority_train_label_no_training":
        if len(y_train) == 0:
            return np.zeros(len(val_pairs), dtype=int)
        majority = int(np.mean(y_train) >= 0.5)
        return np.full(len(val_pairs), majority, dtype=int)

    x_train = pair_features(train_pairs, fmap)
    y_val_len = len(val_pairs)
    x_val = pair_features(val_pairs, fmap)

    if len(np.unique(y_train)) < 2:
        return np.full(y_val_len, int(np.mean(y_train) >= 0.5), dtype=int)

    if model_name == "logistic_regression_pairwise_summary_diff":
        clf = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, class_weight="balanced", solver="liblinear", random_state=seed),
        )
    elif model_name == "ridge_classifier_pairwise_summary_diff":
        clf = make_pipeline(StandardScaler(), RidgeClassifier(class_weight="balanced"))
    else:
        raise ValueError(f"Unknown model: {model_name}")

    clf.fit(x_train, y_train)
    return clf.predict(x_val).astype(int)


def main() -> None:
    created = now_utc()
    objective = read_json(OBJECTIVE_JSON)
    smoke = read_json(SMOKE_REPORT_JSON)
    design = read_json(DESIGN_SPEC_JSON)
    status = read_json(STATUS_JSON)

    if objective.get("status") != "objective_created":
        raise SystemExit("ERROR: objective status mismatch")
    if objective.get("training_authorized") is not True:
        raise SystemExit("ERROR: objective must authorize frozen minimal first-pass matrix")
    if objective.get("planned_rows") != 96:
        raise SystemExit(f"ERROR: planned rows mismatch: {objective.get('planned_rows')}")
    if smoke.get("diagnosis") != "alternative_pairwise_formulation_smoke_tests_passed":
        raise SystemExit("ERROR: smoke report was not passed")
    if design.get("selected_primary_formulation") != "within_subject_pairwise_affect_preference_ranking_v1":
        raise SystemExit("ERROR: design selected formulation mismatch")

    matrix = pd.read_csv(RUN_MATRIX_CSV)
    if len(matrix) != 96:
        raise SystemExit(f"ERROR: run matrix expected 96 rows, found {len(matrix)}")
    allowed_models = set(objective["authorized_models"])
    if set(matrix["model"]) != allowed_models:
        raise SystemExit("ERROR: run matrix models do not match objective")

    # Build trial features per modality once.
    modality_data = {m: load_trial_features(m) for m in ["EEG", "EMG"]}

    pair_cache: dict[tuple[str, str], tuple[pd.DataFrame, dict[str, Any], dict[str, int]]] = {}
    pair_audit_rows: list[dict[str, Any]] = []
    for modality, td in modality_data.items():
        for task in ["valence", "arousal"]:
            pairs, meta = build_oriented_pairs(td, task)
            fold_map = make_folds(list(pairs["subject"].unique()), n_folds=6) if len(pairs) else {}
            pairs["fold"] = pairs["subject"].map(fold_map).astype(int) if len(pairs) else []
            pair_cache[(modality, task)] = (pairs, meta, fold_map)
            counts = pairs.groupby("fold").size().to_dict() if len(pairs) else {}
            pair_audit_rows.append({
                "modality": modality,
                "task": task,
                **meta,
                "min_oriented_pairs_per_fold": int(min(counts.values())) if counts else 0,
                "max_oriented_pairs_per_fold": int(max(counts.values())) if counts else 0,
                "fold_count": int(len(counts)),
                "feature_dim": int(td.metadata["feature_dim"]),
                "leakage_guard_pass": True,
            })
    write_csv(PAIR_AUDIT_OUT, pair_audit_rows)

    run_rows: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    subject_rows: list[dict[str, Any]] = []

    for row in matrix.to_dict("records"):
        run_id = int(row["objective_run_id"])
        model_name = str(row["model"])
        modality = str(row["modality"])
        task = str(row["task"])
        fold_id = int(row["fold"])
        td = modality_data[modality]
        pairs, meta, fold_map = pair_cache[(modality, task)]

        train = pairs[pairs["fold"] != fold_id].reset_index(drop=True)
        val = pairs[pairs["fold"] == fold_id].reset_index(drop=True)
        if train.empty or val.empty:
            raise SystemExit(f"ERROR: empty train/val for run {run_id}")

        y_true = val["label"].to_numpy(dtype=int)
        y_pred = model_predict(model_name, train, val, td.feature_map, seed=20260508 + run_id)

        acc = float((y_true == y_pred).mean())
        bal_acc = balanced_accuracy(y_true, y_pred)
        f1 = macro_f1(y_true, y_pred)
        pos_rate_pred = float(np.mean(y_pred))
        one_class = bool(len(np.unique(y_pred)) < 2)

        train_subjects = set(train["subject"].astype(str))
        val_subjects = set(val["subject"].astype(str))
        train_pairs = set(train["canonical_pair_key"].astype(str))
        val_pairs = set(val["canonical_pair_key"].astype(str))
        subject_overlap = len(train_subjects & val_subjects)
        pair_overlap = len(train_pairs & val_pairs)

        run_rows.append({
            "objective_run_id": run_id,
            "model": model_name,
            "training_category": str(row["training_category"]),
            "modality": modality,
            "task": task,
            "fold": fold_id,
            "n_train_pairs": int(len(train)),
            "n_val_pairs": int(len(val)),
            "accuracy": acc,
            "balanced_accuracy": bal_acc,
            "macro_f1": f1,
            "pred_positive_rate": pos_rate_pred,
            "one_class_pred": one_class,
            "subject_overlap": int(subject_overlap),
            "pair_overlap": int(pair_overlap),
            "leakage_guard_pass": bool(subject_overlap == 0 and pair_overlap == 0),
        })

        # Compact predictions for traceability.
        for idx, (yt, yp) in enumerate(zip(y_true, y_pred)):
            if idx < 250 or model_name in {"logistic_regression_pairwise_summary_diff", "ridge_classifier_pairwise_summary_diff"}:
                prediction_rows.append({
                    "objective_run_id": run_id,
                    "model": model_name,
                    "modality": modality,
                    "task": task,
                    "fold": fold_id,
                    "subject": str(val.loc[idx, "subject"]),
                    "trial_a": str(val.loc[idx, "trial_a"]),
                    "trial_b": str(val.loc[idx, "trial_b"]),
                    "y_true": int(yt),
                    "y_pred": int(yp),
                    "correct": bool(yt == yp),
                })

        for subject, g in val.assign(y_true=y_true, y_pred=y_pred).groupby("subject"):
            y_s = g["y_true"].to_numpy(dtype=int)
            p_s = g["y_pred"].to_numpy(dtype=int)
            subject_rows.append({
                "objective_run_id": run_id,
                "model": model_name,
                "modality": modality,
                "task": task,
                "fold": fold_id,
                "subject": str(subject),
                "n_val_pairs": int(len(g)),
                "balanced_accuracy": balanced_accuracy(y_s, p_s),
                "accuracy": float((y_s == p_s).mean()),
            })

        print(json.dumps({
            "objective_run_id": run_id,
            "model": model_name,
            "modality": modality,
            "task": task,
            "fold": fold_id,
            "bal_acc": round(bal_acc, 4),
            "macro_f1": round(f1, 4),
            "n_val_pairs": int(len(val)),
        }, sort_keys=True))

    write_csv(RUNS_OUT, run_rows)
    write_csv(PRED_OUT, prediction_rows)
    write_csv(SUBJECT_LIFT_OUT, subject_rows)

    runs = pd.DataFrame(run_rows)
    summary_rows: list[dict[str, Any]] = []
    for (model, category, modality, task), g in runs.groupby(["model", "training_category", "modality", "task"]):
        # Control baselines by cell.
        baseline_g = runs[
            (runs["model"] == "majority_train_label_no_training")
            & (runs["modality"] == modality)
            & (runs["task"] == task)
        ]
        rand_g = runs[
            (runs["model"] == "random_balanced_no_training")
            & (runs["modality"] == modality)
            & (runs["task"] == task)
        ]
        mean_bal = float(g["balanced_accuracy"].mean())
        mean_f1 = float(g["macro_f1"].mean())
        maj_bal = float(baseline_g["balanced_accuracy"].mean()) if len(baseline_g) else math.nan
        rnd_bal = float(rand_g["balanced_accuracy"].mean()) if len(rand_g) else math.nan
        summary_rows.append({
            "model": model,
            "training_category": category,
            "modality": modality,
            "task": task,
            "n_runs": int(len(g)),
            "mean_balanced_accuracy": mean_bal,
            "std_balanced_accuracy": float(g["balanced_accuracy"].std(ddof=0)),
            "min_balanced_accuracy": float(g["balanced_accuracy"].min()),
            "max_balanced_accuracy": float(g["balanced_accuracy"].max()),
            "mean_macro_f1": mean_f1,
            "mean_accuracy": float(g["accuracy"].mean()),
            "mean_pred_positive_rate": float(g["pred_positive_rate"].mean()),
            "one_class_pred_count": int(g["one_class_pred"].sum()),
            "folds_over_055_bal_acc": int((g["balanced_accuracy"] >= 0.55).sum()),
            "folds_under_045_bal_acc": int((g["balanced_accuracy"] < 0.45).sum()),
            "mean_majority_baseline_bal_acc": maj_bal,
            "delta_vs_majority_baseline_bal_acc": mean_bal - maj_bal if np.isfinite(maj_bal) else math.nan,
            "mean_random_baseline_bal_acc": rnd_bal,
            "delta_vs_random_baseline_bal_acc": mean_bal - rnd_bal if np.isfinite(rnd_bal) else math.nan,
        })
    write_csv(METRIC_SUMMARY_OUT, summary_rows)

    summary = pd.DataFrame(summary_rows)
    learned = summary[summary["training_category"] == "minimal_classical_pairwise_baseline"].copy()
    learned = learned.sort_values(
        ["mean_balanced_accuracy", "mean_macro_f1", "delta_vs_majority_baseline_bal_acc"],
        ascending=[False, False, False],
    )
    best = learned.iloc[0].to_dict() if len(learned) else {}
    best_bal = float(best.get("mean_balanced_accuracy", math.nan)) if best else math.nan
    best_delta_majority = float(best.get("delta_vs_majority_baseline_bal_acc", math.nan)) if best else math.nan
    best_folds_over = int(best.get("folds_over_055_bal_acc", 0)) if best else 0

    if np.isfinite(best_bal) and best_bal >= 0.55 and best_delta_majority > 0.02 and best_folds_over >= 3:
        diagnosis = "alternative_pairwise_minimal_first_pass_actionable_signal"
        recommended_next = "label_semantics_alternative_pairwise_confirmation_or_failure_analysis_objective"
    elif np.isfinite(best_bal) and best_bal > 0.52 and best_delta_majority > 0.0:
        diagnosis = "alternative_pairwise_minimal_first_pass_weak_mixed_signal"
        recommended_next = "label_semantics_alternative_pairwise_failure_or_metric_debug_objective"
    else:
        diagnosis = "alternative_pairwise_minimal_first_pass_no_actionable_signal"
        recommended_next = "label_semantics_alternative_pairwise_archive_or_patch_objective"

    report = {
        "status": "complete_pending_human_review",
        "created_utc": created,
        "source_objective": str(OBJECTIVE_JSON),
        "diagnosis": diagnosis,
        "recommended_next_objective": recommended_next,
        "training_authorized_was_limited_to_frozen_matrix": True,
        "broad_search_authorized": False,
        "final_loso_claim_authorized": False,
        "n_runs": int(len(runs)),
        "n_predictions_written": int(len(prediction_rows)),
        "best_learned_cell": best,
        "outputs": {
            "runs": str(RUNS_OUT),
            "predictions": str(PRED_OUT),
            "metric_summary": str(METRIC_SUMMARY_OUT),
            "pair_audit": str(PAIR_AUDIT_OUT),
            "subject_lift": str(SUBJECT_LIFT_OUT),
        },
    }
    write_json(REPORT_JSON, report)

    blocked = [
        "broad hyperparameter search",
        "direct full SupCon/DG training",
        "EEG+EMG fusion",
        "final LOSO claim",
        "training outside reviewed next objective",
    ]
    status["last_updated_utc"] = created
    status["current_idare_next_allowed_step"] = "human_review_closeout_before_next_pairwise_decision"
    status["current_idare_blocked_steps"] = blocked
    status["current_idare_alternative_pairwise_first_pass_diagnosis"] = diagnosis
    events = status.get("idare_protocol_events")
    if not isinstance(events, list):
        events = []
    status["idare_protocol_events"] = events
    events.append({
        "timestamp_utc": created,
        "type": "training_report",
        "name": "I-DARE alternative pairwise minimal first pass",
        "status": f"complete pending human review; diagnosis={diagnosis}",
        "evidence": str(REPORT_MD),
        "recommended_next_objective": recommended_next,
        "blocked": blocked,
    })
    write_json(STATUS_JSON, status)

    top_rows = summary.sort_values("mean_balanced_accuracy", ascending=False).head(8).to_dict("records")
    report_md = f"""# I-DARE Alternative Pairwise Minimal First-Pass Report

## Status

Status: complete; pending human review.

Created UTC: `{created}`

## Executive Result

Diagnosis: `{diagnosis}`

Recommended next objective: `{recommended_next}`

Runs executed: `{len(runs)}`

Predictions written: `{len(prediction_rows)}`

## Best Learned Cell

```json
{json.dumps(best, indent=2)}
```

## Top Cells

{md_table(top_rows, ["model", "modality", "task", "n_runs", "mean_balanced_accuracy", "mean_macro_f1", "delta_vs_majority_baseline_bal_acc", "folds_over_055_bal_acc", "folds_under_045_bal_acc"])}

## Pair Audit

{md_table(pair_audit_rows, ["modality", "task", "kept_oriented_pairs", "n_subjects", "positive_rate", "min_oriented_pairs_per_fold", "feature_dim", "leakage_guard_pass"])}

## Interpretation

This run used only the frozen 96-row minimal first-pass matrix. It does not authorize broad model search, SupCon/DG, EEG+EMG fusion, or final LOSO claims.

The next step must be human review and a separate objective for confirmation, metric-debug, patch, or archive.

## Next Allowed Step

`human_review_closeout_before_next_pairwise_decision`
"""
    REPORT_MD.write_text(report_md, encoding="utf-8")

    status_md = STATUS_MD.read_text(encoding="utf-8")
    append = f"""

## I-DARE Alternative Pairwise Minimal First-Pass Report

Updated: `{created}`

| Item | Status | Evidence | Next allowed step | Blocked |
|---|---|---|---|---|
| I-DARE alternative pairwise minimal first pass | complete pending human review; diagnosis=`{diagnosis}` | `docs/idare_label_semantics_alternative_pairwise_minimal_first_pass_report.md` | Human review / closeout before next pairwise decision. | broad search; SupCon/DG; fusion; final claim; training outside reviewed objective |

- Frozen 96-row matrix was executed.
- Recommended next objective: `{recommended_next}` only after human review.
"""
    if "I-DARE Alternative Pairwise Minimal First-Pass Report" not in status_md:
        STATUS_MD.write_text(status_md.rstrip() + append + "\n", encoding="utf-8")

    print("OK_ALTERNATIVE_PAIRWISE_MINIMAL_FIRST_PASS_REPORT_WRITTEN")
    print(REPORT_MD)
    print(REPORT_JSON)
    print(RUNS_OUT)
    print(PRED_OUT)
    print(METRIC_SUMMARY_OUT)
    print(PAIR_AUDIT_OUT)
    print(SUBJECT_LIFT_OUT)
    print("runs=", len(runs))
    print("predictions_written=", len(prediction_rows))
    print("diagnosis=", diagnosis)
    print("recommended_next_objective=", recommended_next)
    print("best_learned_cell=", json.dumps(best, sort_keys=True))


if __name__ == "__main__":
    main()
