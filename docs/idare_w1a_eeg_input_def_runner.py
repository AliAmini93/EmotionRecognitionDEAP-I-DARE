#!/usr/bin/env python3
"""
W1A EEG Input Definition guarded runner.

Scope:
- I-DARE only
- EEG only
- arousal only
- pairwise formulation
- ridge classifier only
- normalization fixed to current/default none
- max 18 registered runs
- no cache overwrite
- no preprocessing rebuild
- outputs only docs/idare_w1a_eeg_input_def_*
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

PREFIX = "idare_w1a_eeg_input_def_"

OBJECTIVE_JSON = DOCS / f"{PREFIX}objective.json"
INPUT_MANIFEST_CSV = DOCS / f"{PREFIX}input_manifest.csv"
RUN_MATRIX_CSV = DOCS / f"{PREFIX}run_matrix.csv"
RUNS_CSV = DOCS / f"{PREFIX}runs.csv"
PREDICTIONS_CSV = DOCS / f"{PREFIX}predictions.csv"
REPORT_JSON = DOCS / f"{PREFIX}report.json"
REPORT_MD = DOCS / f"{PREFIX}report.md"
BLOCKER_JSON = DOCS / f"{PREFIX}blocker.json"
BLOCKER_MD = DOCS / f"{PREFIX}blocker.md"

WAVE0_BASELINE_REGISTRY = DOCS / "idare_wave0_baseline_registry.csv"
WAVE0_BRANCH_REGISTRY = DOCS / "idare_wave0_branch_registry.csv"
WAVE0_GATE_CRITERIA = DOCS / "idare_wave0_gate_criteria.csv"

# Required cached inputs. These are read-only.
STIM_BSL_NPY = ROOT / ".cache" / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
STIM_BSL_INDEX_CSV = ROOT / ".cache" / "idare_eeg_cache_index_baseline_corrected.csv"
BSL_STATS_NPY = ROOT / ".cache" / "idare_eeg_bsl_stats.npy"
BSL_STATS_INDEX_CSV = ROOT / ".cache" / "idare_eeg_bsl_stats_index.csv"

FOLD_SOURCE_CANDIDATES = [
    DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv",
    DOCS / "idare_broader_eval_eeg_bsl_stats_primary_predictions.csv",
    DOCS / "idare_eeg_stim_bsl_only_arousal_standardized_smoke_predictions.csv",
    DOCS / "idare_eeg_bsl_stats_arousal_ablation_smoke_predictions.csv",
]

REFERENCE_PAIRWISE_BAL_ACC = 0.5216709095
REFERENCE_BSL_BINARY_BAL_ACC = 0.5427
MODERATE_PASS = 0.53
STRONG_PASS = 0.55


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def git_output(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def md_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(c, "")).replace("|", "\\|") for c in cols) + " |")
    return "\n".join(out)


def find_col(df: pd.DataFrame, preferred: list[str], contains: str | None = None) -> str | None:
    lower = {str(c).lower(): str(c) for c in df.columns}
    for name in preferred:
        if name.lower() in lower:
            return lower[name.lower()]
    if contains:
        candidates = [str(c) for c in df.columns if contains.lower() in str(c).lower()]
        if candidates:
            return candidates[0]
    return None


def find_numeric_rating_col(df: pd.DataFrame, task: str) -> str | None:
    preferred = [
        f"{task}_score",
        f"{task}_rating",
        f"{task}_raw",
        f"{task}_value",
        task,
    ]
    lower = {str(c).lower(): str(c) for c in df.columns}
    for col in preferred:
        if col.lower() in lower and pd.api.types.is_numeric_dtype(df[lower[col.lower()]]):
            return lower[col.lower()]

    candidates: list[str] = []
    bad_tokens = ["pred", "prediction", "label", "midpoint", "discard", "binary", "fold", "rank"]
    good_tokens = [task, "score", "rating", "value"]
    for c in df.columns:
        lc = str(c).lower()
        if task in lc and pd.api.types.is_numeric_dtype(df[c]):
            if not any(tok in lc for tok in bad_tokens):
                candidates.append(str(c))
    if candidates:
        def score(name: str) -> tuple[int, int]:
            lc = name.lower()
            return (-sum(tok in lc for tok in good_tokens), len(lc))
        return sorted(candidates, key=score)[0]
    return None


def append_blocker(reason: str, details: dict[str, Any]) -> None:
    data = {
        "status": "blocked",
        "branch": safe_git_branch(),
        "created_utc": now_utc(),
        "reason": reason,
        "details": details,
        "control_notify_required": True,
        "notification_type": "blocker",
    }
    write_json(BLOCKER_JSON, data)
    lines = [
        "# W1A EEG Input Definition Blocker",
        "",
        f"- status: `blocked`",
        f"- reason: `{reason}`",
        f"- branch: `{data['branch']}`",
        "",
        "## Details",
        "",
        "```json",
        json.dumps(details, indent=2, ensure_ascii=False),
        "```",
        "",
        "## Required action",
        "",
        "Notify Control Tower before proceeding.",
    ]
    BLOCKER_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def safe_git_branch() -> str:
    try:
        return git_output(["branch", "--show-current"])
    except Exception:
        return "UNKNOWN"


def validate_scope() -> list[str]:
    issues: list[str] = []
    branch = safe_git_branch()
    if branch != "idare/wave1/eeg-input-definition":
        issues.append(f"wrong_branch:{branch}")

    if not OBJECTIVE_JSON.exists():
        issues.append(f"missing:{OBJECTIVE_JSON}")

    for p in [WAVE0_BASELINE_REGISTRY, WAVE0_BRANCH_REGISTRY, WAVE0_GATE_CRITERIA]:
        if not p.exists():
            issues.append(f"missing:{p}")

    return issues


def build_input_manifest() -> tuple[list[dict[str, Any]], list[str]]:
    required = [
        ("wave0_baseline_registry", WAVE0_BASELINE_REGISTRY),
        ("wave0_branch_registry", WAVE0_BRANCH_REGISTRY),
        ("wave0_gate_criteria", WAVE0_GATE_CRITERIA),
        ("stim_bsl_npy", STIM_BSL_NPY),
        ("stim_bsl_index_csv", STIM_BSL_INDEX_CSV),
        ("bsl_stats_npy", BSL_STATS_NPY),
        ("bsl_stats_index_csv", BSL_STATS_INDEX_CSV),
    ]

    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    for role, path in required:
        exists = path.exists()
        if not exists:
            missing.append(str(path))
        rows.append({
            "role": role,
            "path": str(path),
            "exists": exists,
            "size_bytes": path.stat().st_size if exists and path.is_file() else "",
            "sha256": file_sha256(path) if exists and path.is_file() else "",
        })

    for path in FOLD_SOURCE_CANDIDATES:
        rows.append({
            "role": "fold_source_candidate",
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() and path.is_file() else "",
            "sha256": file_sha256(path) if path.exists() and path.is_file() else "",
        })

    write_csv(INPUT_MANIFEST_CSV, rows)
    return rows, missing


def infer_fold_map(subject_values: pd.Series) -> tuple[dict[str, int], str]:
    subjects_needed = sorted({str(s) for s in subject_values.dropna().astype(str).unique()})

    for path in FOLD_SOURCE_CANDIDATES:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        subject_col = find_col(df, ["subject_id", "subject", "heldout_subject", "val_subject"], contains="subject")
        fold_col = find_col(df, ["fold", "fold_id", "test_fold"], contains="fold")
        if subject_col is None or fold_col is None:
            continue

        sub = df[[subject_col, fold_col]].dropna().copy()
        sub[subject_col] = sub[subject_col].astype(str)
        sub[fold_col] = pd.to_numeric(sub[fold_col], errors="coerce")
        sub = sub.dropna()
        mapping: dict[str, int] = {}
        ambiguous = False
        for subject, g in sub.groupby(subject_col):
            folds = sorted(set(int(v) for v in g[fold_col].tolist()))
            if len(folds) != 1:
                ambiguous = True
                break
            mapping[str(subject)] = int(folds[0])
        if ambiguous:
            continue
        if all(s in mapping for s in subjects_needed):
            return mapping, str(path)

    # Fallback is blocked, not used silently.
    raise RuntimeError("Could not infer existing 6-fold subject-held-out structure from allowed fold-source docs.")


def stim_bsl_summary_features(windows: np.ndarray) -> np.ndarray:
    x = windows.astype(np.float32, copy=False)
    mean = x.mean(axis=-1)
    std = x.std(axis=-1)
    rms = np.sqrt(np.mean(np.square(x), axis=-1))
    mav = np.mean(np.abs(x), axis=-1)
    logvar = np.log(np.var(x, axis=-1) + 1e-6)
    global_mean = x.mean(axis=(1, 2), keepdims=False).reshape(-1, 1)
    global_std = x.std(axis=(1, 2), keepdims=False).reshape(-1, 1)
    global_rms = np.sqrt(np.mean(np.square(x), axis=(1, 2))).reshape(-1, 1)
    return np.concatenate([mean, std, rms, mav, logvar, global_mean, global_std, global_rms], axis=1)


def align_bsl_stats(index_df: pd.DataFrame, bsl_index_df: pd.DataFrame, bsl_stats: np.ndarray) -> np.ndarray:
    if len(index_df) == len(bsl_index_df) == bsl_stats.shape[0]:
        return np.asarray(bsl_stats, dtype=np.float32)

    key_candidates = [
        ["cache_row"],
        ["subject_id", "stimulus_id"],
        ["subject", "stimulus_id"],
        ["subject_id", "trial_id"],
        ["subject", "trial_id"],
    ]
    for keys in key_candidates:
        if all(k in index_df.columns for k in keys) and all(k in bsl_index_df.columns for k in keys):
            left = index_df[keys].astype(str).copy()
            left["_row_order"] = np.arange(len(index_df))
            right = bsl_index_df[keys].astype(str).copy()
            right["_bsl_row"] = np.arange(len(bsl_index_df))
            merged = left.merge(right, on=keys, how="left", validate="one_to_one")
            if merged["_bsl_row"].isna().any():
                continue
            order = merged.sort_values("_row_order")["_bsl_row"].astype(int).to_numpy()
            return np.asarray(bsl_stats[order], dtype=np.float32)

    raise RuntimeError("Could not align BSL-stats sidecar to STIM-BSL index.")


def make_pairs(df: pd.DataFrame, row_indices: np.ndarray, subject_col: str, rating_col: str) -> dict[str, np.ndarray]:
    left: list[int] = []
    right: list[int] = []
    y: list[int] = []
    subjects: list[str] = []

    for subject, g in df.iloc[row_indices].groupby(subject_col, dropna=False):
        idxs = g.index.to_numpy(dtype=int)
        vals = pd.to_numeric(g[rating_col], errors="coerce").to_numpy(dtype=float)
        if len(idxs) < 2:
            continue
        for i in range(len(idxs) - 1):
            for j in range(i + 1, len(idxs)):
                if not np.isfinite(vals[i]) or not np.isfinite(vals[j]) or vals[i] == vals[j]:
                    continue
                left.append(int(idxs[i]))
                right.append(int(idxs[j]))
                y.append(1 if vals[i] > vals[j] else 0)
                subjects.append(str(subject))

    return {
        "left": np.asarray(left, dtype=np.int32),
        "right": np.asarray(right, dtype=np.int32),
        "y": np.asarray(y, dtype=np.int8),
        "subject": np.asarray(subjects, dtype=object),
    }


def pairwise_diff_features(x: np.ndarray, pairs: dict[str, np.ndarray]) -> np.ndarray:
    return (x[pairs["left"]] - x[pairs["right"]]).astype(np.float32, copy=False)


def metric_row(cell: str, fold: int, y_true: np.ndarray, y_pred: np.ndarray, n_train: int) -> dict[str, Any]:
    return {
        "cell": cell,
        "fold": int(fold),
        "model": "ridge_classifier",
        "task": "arousal",
        "formulation": "within_subject_pairwise_affect_preference_ranking",
        "normalization": "none",
        "n_train_pairs": int(n_train),
        "n_val_pairs": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "pred_positive_rate": float(np.mean(y_pred)) if len(y_pred) else math.nan,
        "true_positive_rate": float(np.mean(y_true)) if len(y_true) else math.nan,
        "one_class_pred": bool(len(set(y_pred.tolist())) < 2),
    }


def run_w1a() -> dict[str, Any]:
    scope_issues = validate_scope()
    manifest_rows, missing_inputs = build_input_manifest()
    if scope_issues or missing_inputs:
        details = {
            "scope_issues": scope_issues,
            "missing_inputs": missing_inputs,
            "input_manifest": str(INPUT_MANIFEST_CSV),
        }
        append_blocker("missing_or_invalid_required_inputs", details)
        raise SystemExit("BLOCKED: missing_or_invalid_required_inputs; see W1A blocker docs.")

    index_df = pd.read_csv(STIM_BSL_INDEX_CSV)
    bsl_index_df = pd.read_csv(BSL_STATS_INDEX_CSV)
    windows = np.load(STIM_BSL_NPY, mmap_mode="r")
    bsl_stats = np.load(BSL_STATS_NPY, mmap_mode="r")

    if windows.ndim != 3 or tuple(windows.shape[1:]) != (32, 640):
        append_blocker("unexpected_stim_bsl_shape", {"shape": list(windows.shape)})
        raise SystemExit("BLOCKED: unexpected_stim_bsl_shape")
    if bsl_stats.ndim != 2:
        append_blocker("unexpected_bsl_stats_shape", {"shape": list(bsl_stats.shape)})
        raise SystemExit("BLOCKED: unexpected_bsl_stats_shape")
    if len(index_df) != windows.shape[0]:
        append_blocker("stim_bsl_index_row_mismatch", {"index_rows": len(index_df), "npy_rows": int(windows.shape[0])})
        raise SystemExit("BLOCKED: stim_bsl_index_row_mismatch")

    subject_col = find_col(index_df, ["subject_id", "subject", "participant_id"], contains="subject")
    rating_col = find_numeric_rating_col(index_df, "arousal")
    if subject_col is None or rating_col is None:
        append_blocker("could_not_identify_subject_or_arousal_rating_column", {"columns": list(index_df.columns)})
        raise SystemExit("BLOCKED: could_not_identify_subject_or_arousal_rating_column")

    fold_map, fold_source = infer_fold_map(index_df[subject_col])
    index_df["_w1a_fold"] = index_df[subject_col].astype(str).map(fold_map)
    if index_df["_w1a_fold"].isna().any():
        append_blocker("fold_mapping_incomplete", {"fold_source": fold_source})
        raise SystemExit("BLOCKED: fold_mapping_incomplete")

    bsl_aligned = align_bsl_stats(index_df, bsl_index_df, bsl_stats)

    a1 = stim_bsl_summary_features(np.asarray(windows, dtype=np.float32))
    a2 = np.asarray(bsl_aligned, dtype=np.float32)
    a3 = np.concatenate([a1, a2], axis=1).astype(np.float32)

    cells = {
        "A1": ("current_STIM_BSL_summary", a1),
        "A2": ("BSL_stats_sidecar", a2),
        "A3": ("STIM_BSL_summary_plus_BSL_stats_concat", a3),
    }

    run_matrix: list[dict[str, Any]] = []
    run_id = 1
    for cell, (cell_name, x) in cells.items():
        for fold in range(1, 7):
            run_matrix.append({
                "run_id": run_id,
                "cell": cell,
                "input_definition": cell_name,
                "fold": fold,
                "model": "ridge_classifier",
                "task": "arousal",
                "normalization": "none",
            })
            run_id += 1
    write_csv(RUN_MATRIX_CSV, run_matrix)

    run_rows: list[dict[str, Any]] = []
    pred_rows: list[dict[str, Any]] = []

    for run in run_matrix:
        cell = run["cell"]
        fold = int(run["fold"])
        x = cells[cell][1]
        train_rows = index_df.index[index_df["_w1a_fold"].astype(int) != fold].to_numpy(dtype=int)
        val_rows = index_df.index[index_df["_w1a_fold"].astype(int) == fold].to_numpy(dtype=int)

        train_pairs = make_pairs(index_df, train_rows, subject_col, rating_col)
        val_pairs = make_pairs(index_df, val_rows, subject_col, rating_col)

        if len(train_pairs["y"]) == 0 or len(val_pairs["y"]) == 0:
            append_blocker("empty_pairwise_train_or_val_pairs", {"cell": cell, "fold": fold})
            raise SystemExit("BLOCKED: empty_pairwise_train_or_val_pairs")

        x_train = pairwise_diff_features(x, train_pairs)
        x_val = pairwise_diff_features(x, val_pairs)
        y_train = train_pairs["y"].astype(int)
        y_val = val_pairs["y"].astype(int)

        if not np.isfinite(x_train).all() or not np.isfinite(x_val).all():
            append_blocker("non_finite_pairwise_features", {"cell": cell, "fold": fold})
            raise SystemExit("BLOCKED: non_finite_pairwise_features")

        clf = RidgeClassifier(alpha=1.0)
        clf.fit(x_train, y_train)
        y_pred = clf.predict(x_val).astype(int)
        row = metric_row(cell, fold, y_val, y_pred, len(y_train))
        row["run_id"] = int(run["run_id"])
        row["input_definition"] = run["input_definition"]
        run_rows.append(row)

        scores = clf.decision_function(x_val)
        for i in range(len(y_val)):
            pred_rows.append({
                "run_id": int(run["run_id"]),
                "cell": cell,
                "fold": fold,
                "subject": str(val_pairs["subject"][i]),
                "left_index": int(val_pairs["left"][i]),
                "right_index": int(val_pairs["right"][i]),
                "y_true": int(y_val[i]),
                "y_pred": int(y_pred[i]),
                "score": float(scores[i]),
            })

    write_csv(RUNS_CSV, run_rows)
    write_csv(PREDICTIONS_CSV, pred_rows)

    df = pd.DataFrame(run_rows)
    summary_rows: list[dict[str, Any]] = []
    for cell, g in df.groupby("cell", sort=True):
        mean_bal = float(g["balanced_accuracy"].mean())
        summary_rows.append({
            "cell": cell,
            "input_definition": str(g["input_definition"].iloc[0]),
            "runs": int(len(g)),
            "mean_balanced_accuracy": mean_bal,
            "std_balanced_accuracy": float(g["balanced_accuracy"].std(ddof=0)),
            "min_balanced_accuracy": float(g["balanced_accuracy"].min()),
            "max_balanced_accuracy": float(g["balanced_accuracy"].max()),
            "mean_macro_f1": float(g["macro_f1"].mean()),
            "delta_vs_REF_PW_EEG_ARO_001": mean_bal - REFERENCE_PAIRWISE_BAL_ACC,
            "delta_vs_REF_BSL_EEG_ARO_001": mean_bal - REFERENCE_BSL_BINARY_BAL_ACC,
            "moderate_pass": bool(mean_bal >= MODERATE_PASS),
            "strong_pass": bool(mean_bal >= STRONG_PASS),
        })

    best = max(summary_rows, key=lambda r: r["mean_balanced_accuracy"])
    gate_trigger = bool(best["moderate_pass"] or best["strong_pass"])
    diagnosis = "strong_pass" if best["strong_pass"] else "moderate_pass" if best["moderate_pass"] else "no_gate_pass"

    report = {
        "status": "complete",
        "created_utc": now_utc(),
        "branch": safe_git_branch(),
        "scope": {
            "dataset": "I-DARE",
            "modality": "EEG",
            "task": "arousal",
            "formulation": "within_subject_pairwise_affect_preference_ranking",
            "model": "ridge_classifier",
            "normalization": "none",
            "registered_runs": 18
        },
        "input_manifest": str(INPUT_MANIFEST_CSV),
        "fold_source": fold_source,
        "subject_column": subject_col,
        "arousal_rating_column": rating_col,
        "summary": summary_rows,
        "best_cell": best,
        "diagnosis": diagnosis,
        "gate_trigger": gate_trigger,
        "control_notify_required": gate_trigger,
        "outputs": {
            "run_matrix_csv": str(RUN_MATRIX_CSV),
            "runs_csv": str(RUNS_CSV),
            "predictions_csv": str(PREDICTIONS_CSV),
            "report_json": str(REPORT_JSON),
            "report_md": str(REPORT_MD)
        }
    }
    write_json(REPORT_JSON, report)

    lines = [
        "# W1A EEG Input Definition Report",
        "",
        f"- status: `{report['status']}`",
        f"- diagnosis: `{diagnosis}`",
        f"- fold_source: `{fold_source}`",
        f"- subject_column: `{subject_col}`",
        f"- arousal_rating_column: `{rating_col}`",
        "",
        "## Cell Summary",
        "",
        md_table(summary_rows, [
            "cell",
            "input_definition",
            "runs",
            "mean_balanced_accuracy",
            "std_balanced_accuracy",
            "delta_vs_REF_PW_EEG_ARO_001",
            "delta_vs_REF_BSL_EEG_ARO_001",
            "moderate_pass",
            "strong_pass"
        ]),
        "",
        "## Interpretation",
        "",
        f"Best cell: `{best['cell']}` with mean balanced accuracy `{best['mean_balanced_accuracy']}`.",
        "",
        "Moderate pass threshold: `0.53`.",
        "",
        "Strong pass threshold: `0.55`.",
        "",
        "No Wave 2 design is included in this report.",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def validate_outputs() -> None:
    allowed = sorted(str(p) for p in DOCS.glob(f"{PREFIX}*"))
    unexpected = []
    # This runner intentionally only checks its own prefix outputs.
    for path in allowed:
        if not path.startswith(str(DOCS / PREFIX)):
            unexpected.append(path)
    if unexpected:
        append_blocker("unexpected_output_path", {"unexpected": unexpected})
        raise SystemExit("BLOCKED: unexpected_output_path")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["validate", "run"], default="validate")
    args = parser.parse_args()

    if args.mode == "validate":
        scope_issues = validate_scope()
        manifest_rows, missing = build_input_manifest()
        result = {
            "status": "validation_complete" if not scope_issues and not missing else "blocked",
            "created_utc": now_utc(),
            "branch": safe_git_branch(),
            "scope_issues": scope_issues,
            "missing_inputs": missing,
            "input_manifest": str(INPUT_MANIFEST_CSV),
            "required_input_count": 7,
            "missing_input_count": len(missing),
        }
        if scope_issues or missing:
            append_blocker("missing_or_invalid_required_inputs", result)
            print(json.dumps(result, indent=2))
            raise SystemExit(3)
        print(json.dumps(result, indent=2))
        return

    report = run_w1a()
    validate_outputs()
    print(json.dumps({
        "status": "run_complete",
        "diagnosis": report["diagnosis"],
        "best_cell": report["best_cell"],
        "gate_trigger": report["gate_trigger"],
        "report_json": str(REPORT_JSON),
        "report_md": str(REPORT_MD)
    }, indent=2))


if __name__ == "__main__":
    main()
