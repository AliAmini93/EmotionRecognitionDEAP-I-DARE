#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeClassifier
from sklearn.metrics import balanced_accuracy_score, accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(".")
DOCS = ROOT / "docs"
SCRIPT_PATH = Path("scripts/idare_w1b_eeg_subj_norm_runner.py")

PREFIX = "idare_w1b_eeg_subj_norm_"

OBJECTIVE_JSON = DOCS / f"{PREFIX}objective.json"
REPORT_MD = DOCS / f"{PREFIX}report.md"
REPORT_JSON = DOCS / f"{PREFIX}report.json"
RUNS_CSV = DOCS / f"{PREFIX}runs.csv"
FOLD_CSV = DOCS / f"{PREFIX}fold_diagnostics.csv"
CLOSEOUT_MD = DOCS / f"{PREFIX}closeout.md"
CLOSEOUT_JSON = DOCS / f"{PREFIX}closeout.json"

CACHE_INDEX = ROOT / ".cache/idare_eeg_cache_index_baseline_corrected.csv"
WINDOWS_NPY = ROOT / ".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy"

REF_ID = "REF-PW-EEG-ARO-001"
REF_BAL_ACC = 0.5216709095

FS = 128.0
N_FOLDS = 6

@dataclass(frozen=True)
class Cell:
    cell_id: str
    name: str
    transductive: bool
    strict_nontransductive_allowed: bool

CELLS = [
    Cell("B0", "none_current", False, True),
    Cell("B1", "per_subject_zscore_transductive", True, False),
    Cell("B2", "train_fold_standard_scaler_nontransductive", False, True),
    Cell("B3", "per_subject_rank_transform_transductive", True, False),
]

def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()

def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise SystemExit(f"ERROR: no rows for {path}")
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def md_table(rows: list[dict[str, Any]], cols: list[str]) -> str:
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for row in rows:
        vals = []
        for col in cols:
            val = row.get(col, "")
            if isinstance(val, float):
                val = f"{val:.6f}"
            vals.append(str(val).replace("|", "\\|"))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)

def find_col(df: pd.DataFrame, exact: list[str], contains: str) -> str | None:
    lower = {str(c).lower(): str(c) for c in df.columns}
    for c in exact:
        if c.lower() in lower:
            return lower[c.lower()]
    candidates = []
    for c in df.columns:
        lc = str(c).lower()
        if contains.lower() in lc:
            candidates.append(str(c))
    numeric = [c for c in candidates if pd.api.types.is_numeric_dtype(df[c])]
    if numeric:
        def score(c: str) -> tuple[int, int]:
            lc = c.lower()
            bad = int(any(tok in lc for tok in ["pred", "prediction", "rank", "fold", "binary"]))
            good = int(any(tok in lc for tok in ["score", "rating", "raw", "mean", "sam", "arousal"]))
            return (bad, -good, len(lc))
        return sorted(numeric, key=score)[0]
    return candidates[0] if candidates else None

def current_stim_bsl_summary(windows_by_index_row: np.ndarray) -> np.ndarray:
    x = windows_by_index_row.astype(np.float32, copy=False)
    mean = x.mean(axis=-1)
    std = x.std(axis=-1)
    rms = np.sqrt(np.mean(np.square(x), axis=-1))
    line_length = np.mean(np.abs(np.diff(x, axis=-1)), axis=-1)
    return np.concatenate([mean, std, rms, line_length], axis=1).astype(np.float32, copy=False)

def derive_existing_6fold_subject_map(subjects: pd.Series) -> dict[str, int]:
    unique = sorted(subjects.astype(str).unique().tolist())
    return {s: (i % N_FOLDS) + 1 for i, s in enumerate(unique)}

def make_pairs(df: pd.DataFrame, subject_col: str, score_col: str, row_positions: np.ndarray) -> dict[str, np.ndarray]:
    left, right, y, subjects = [], [], [], []
    subset = df.iloc[row_positions]
    for subject, group in subset.groupby(subject_col, dropna=False):
        pos = group["_pos"].to_numpy(dtype=int)
        scores = pd.to_numeric(group[score_col], errors="coerce").to_numpy(dtype=float)
        n = len(pos)
        for i in range(n - 1):
            si = scores[i]
            if not np.isfinite(si):
                continue
            for j in range(i + 1, n):
                sj = scores[j]
                if not np.isfinite(sj) or si == sj:
                    continue
                left.append(int(pos[i]))
                right.append(int(pos[j]))
                y.append(1 if si > sj else 0)
                subjects.append(str(subject))
    return {
        "left": np.asarray(left, dtype=np.int32),
        "right": np.asarray(right, dtype=np.int32),
        "y": np.asarray(y, dtype=np.int8),
        "subject": np.asarray(subjects, dtype=object),
    }

def pair_features(sample_features: np.ndarray, left: np.ndarray, right: np.ndarray) -> np.ndarray:
    diff = sample_features[left] - sample_features[right]
    absdiff = np.abs(diff)
    return np.concatenate([diff, absdiff], axis=1).astype(np.float32, copy=False)

def per_subject_zscore(features: np.ndarray, subjects: np.ndarray) -> np.ndarray:
    out = np.empty_like(features, dtype=np.float32)
    for subject in sorted(set(subjects.astype(str))):
        mask = subjects.astype(str) == subject
        block = features[mask]
        mu = block.mean(axis=0, keepdims=True)
        sd = block.std(axis=0, keepdims=True)
        sd[sd < 1e-6] = 1.0
        out[mask] = (block - mu) / sd
    return out

def per_subject_rank_transform(features: np.ndarray, subjects: np.ndarray) -> np.ndarray:
    out = np.empty_like(features, dtype=np.float32)
    for subject in sorted(set(subjects.astype(str))):
        mask = subjects.astype(str) == subject
        block = features[mask]
        ranked = pd.DataFrame(block).rank(axis=0, method="average", pct=True).to_numpy(dtype=np.float32)
        out[mask] = ranked
    return out

def train_fold_standardize(features: np.ndarray, train_positions: np.ndarray) -> np.ndarray:
    scaler = StandardScaler()
    scaler.fit(features[train_positions])
    return scaler.transform(features).astype(np.float32, copy=False)

def metric_row(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "pred_positive_rate": float(np.mean(y_pred)),
        "true_positive_rate": float(np.mean(y_true)),
        "one_class_pred": bool(len(set(y_pred.tolist())) < 2),
        "n_pairs": int(len(y_true)),
    }

def top3_bottom3_gap(vals: list[float]) -> float:
    ordered = sorted(float(v) for v in vals)
    if len(ordered) < 6:
        return math.nan
    return float(np.mean(ordered[-3:]) - np.mean(ordered[:3]))

def main() -> None:
    branch = run_git(["branch", "--show-current"])
    if branch != "idare/wave1/eeg-subject-normalization":
        raise SystemExit(f"ERROR: wrong branch: {branch}")

    if not OBJECTIVE_JSON.exists():
        raise SystemExit(f"ERROR: missing objective JSON: {OBJECTIVE_JSON}")
    if not CACHE_INDEX.exists():
        raise SystemExit(f"ERROR: missing fixed cache index: {CACHE_INDEX}")
    if not WINDOWS_NPY.exists():
        raise SystemExit(f"ERROR: missing fixed STIM-BSL EEG cache: {WINDOWS_NPY}")

    objective = json.loads(OBJECTIVE_JSON.read_text(encoding="utf-8"))
    if objective["scope"]["dataset"] != "I-DARE only":
        raise SystemExit("ERROR: objective dataset scope mismatch")
    if objective["scope"]["modality"] != "EEG only":
        raise SystemExit("ERROR: objective modality scope mismatch")
    if objective["scope"]["task"] != "arousal only":
        raise SystemExit("ERROR: objective task scope mismatch")
    if int(objective["scope"]["max_registered_runs"]) != 24:
        raise SystemExit("ERROR: max_registered_runs must be 24")

    idx = pd.read_csv(CACHE_INDEX)
    idx.columns = [str(c).strip() for c in idx.columns]

    subject_col = find_col(
        idx,
        ["subject_id", "subject", "participant_id", "participant", "subj"],
        "subject",
    )
    score_col = find_col(
        idx,
        ["arousal_score", "arousal_rating", "arousal_raw", "arousal", "Arousal (M)", "arousal_mean"],
        "arousal",
    )

    if subject_col is None:
        raise SystemExit("ERROR: could not find subject column")
    if score_col is None:
        raise SystemExit("ERROR: could not find arousal score column")

    scores = pd.to_numeric(idx[score_col], errors="coerce")
    if scores.dropna().nunique() < 3:
        raise SystemExit(
            f"ERROR: arousal column {score_col} has fewer than 3 unique numeric values; "
            "pairwise affect preference ranking needs score-level arousal, not a binary label."
        )

    if "cache_row" in idx.columns:
        cache_rows = idx["cache_row"].astype(int).to_numpy()
    else:
        cache_rows = np.arange(len(idx), dtype=int)

    windows = np.load(WINDOWS_NPY, mmap_mode="r")
    if windows.ndim != 3 or tuple(windows.shape[1:]) != (32, 640):
        raise SystemExit(f"ERROR: unexpected windows shape: {windows.shape}")
    if int(cache_rows.max()) >= int(windows.shape[0]):
        raise SystemExit("ERROR: cache_row exceeds window cache size")

    idx = idx.copy()
    idx["_pos"] = np.arange(len(idx), dtype=int)
    idx["_subject_str"] = idx[subject_col].astype(str)
    fold_map = derive_existing_6fold_subject_map(idx["_subject_str"])
    idx["_fold"] = idx["_subject_str"].map(fold_map).astype(int)

    base_features_cache_order = current_stim_bsl_summary(np.asarray(windows[cache_rows], dtype=np.float32))
    subjects = idx["_subject_str"].to_numpy(dtype=str)

    b1_features = per_subject_zscore(base_features_cache_order, subjects)
    b3_features = per_subject_rank_transform(base_features_cache_order, subjects)

    run_rows: list[dict[str, Any]] = []
    fold_rows: list[dict[str, Any]] = []
    run_id = 1

    for cell in CELLS:
        for fold in range(1, N_FOLDS + 1):
            train_positions = idx.index[idx["_fold"] != fold].to_numpy(dtype=int)
            val_positions = idx.index[idx["_fold"] == fold].to_numpy(dtype=int)

            if cell.cell_id == "B0":
                sample_features = base_features_cache_order
                cell_norm = "none/current"
            elif cell.cell_id == "B1":
                sample_features = b1_features
                cell_norm = "per-subject z-score using unlabeled subject-level feature statistics"
            elif cell.cell_id == "B2":
                sample_features = train_fold_standardize(base_features_cache_order, train_positions)
                cell_norm = "train-fold StandardScaler fit on train subjects only"
            elif cell.cell_id == "B3":
                sample_features = b3_features
                cell_norm = "per-subject rank transform using unlabeled subject-level feature statistics"
            else:
                raise SystemExit(f"ERROR: unknown cell {cell}")

            train_pairs = make_pairs(idx, "_subject_str", score_col, train_positions)
            val_pairs = make_pairs(idx, "_subject_str", score_col, val_positions)

            if len(train_pairs["y"]) == 0 or len(val_pairs["y"]) == 0:
                raise SystemExit(f"ERROR: empty pair set for {cell.cell_id} fold={fold}")

            x_train_raw = pair_features(sample_features, train_pairs["left"], train_pairs["right"])
            x_val_raw = pair_features(sample_features, val_pairs["left"], val_pairs["right"])

            # Fixed model-side scaling for ridge numerical stability, fit on train pairs only.
            pair_scaler = StandardScaler()
            x_train = pair_scaler.fit_transform(x_train_raw).astype(np.float32, copy=False)
            x_val = pair_scaler.transform(x_val_raw).astype(np.float32, copy=False)

            if not np.isfinite(x_train).all() or not np.isfinite(x_val).all():
                raise SystemExit(f"ERROR: non-finite features for {cell.cell_id} fold={fold}")

            clf = RidgeClassifier(alpha=1.0)
            clf.fit(x_train, train_pairs["y"].astype(int))
            y_pred = clf.predict(x_val).astype(int)
            y_true = val_pairs["y"].astype(int)
            metrics = metric_row(y_true, y_pred)

            row = {
                "run_id": run_id,
                "cell_id": cell.cell_id,
                "cell_name": cell.name,
                "normalization": cell_norm,
                "transductive": cell.transductive,
                "strict_nontransductive_allowed": cell.strict_nontransductive_allowed,
                "dataset": "I-DARE",
                "modality": "EEG",
                "task": "arousal",
                "formulation": "within_subject_pairwise_affect_preference_ranking",
                "input": "current_STIM_BSL_summary",
                "model": "RidgeClassifier(alpha=1.0)",
                "fold": fold,
                "n_train_subjects": int(idx.loc[train_positions, "_subject_str"].nunique()),
                "n_val_subjects": int(idx.loc[val_positions, "_subject_str"].nunique()),
                "n_train_pairs": int(len(train_pairs["y"])),
                "n_val_pairs": int(len(val_pairs["y"])),
                "train_positive_rate": float(np.mean(train_pairs["y"])),
                "val_positive_rate": float(np.mean(y_true)),
                "accuracy": metrics["accuracy"],
                "balanced_accuracy": metrics["balanced_accuracy"],
                "macro_f1": metrics["macro_f1"],
                "pred_positive_rate": metrics["pred_positive_rate"],
                "true_positive_rate": metrics["true_positive_rate"],
                "one_class_pred": metrics["one_class_pred"],
                "delta_vs_ref_mean_bal_acc": float(metrics["balanced_accuracy"] - REF_BAL_ACC),
                "positive_fold_bal_acc_gt_0_5": bool(metrics["balanced_accuracy"] > 0.5),
                "leakage_or_transductive_labeling_issue": False,
            }
            run_rows.append(row)
            fold_rows.append({
                "cell_id": cell.cell_id,
                "cell_name": cell.name,
                "fold": fold,
                "balanced_accuracy": metrics["balanced_accuracy"],
                "macro_f1": metrics["macro_f1"],
                "accuracy": metrics["accuracy"],
                "n_val_pairs": int(len(y_true)),
                "val_subjects": ",".join(sorted(idx.loc[val_positions, "_subject_str"].unique().tolist())),
                "transductive": cell.transductive,
            })

            print(json.dumps({
                "run_id": run_id,
                "cell_id": cell.cell_id,
                "fold": fold,
                "balanced_accuracy": round(metrics["balanced_accuracy"], 6),
                "macro_f1": round(metrics["macro_f1"], 6),
                "transductive": cell.transductive,
            }, sort_keys=True))

            run_id += 1

    if len(run_rows) != 24:
        raise SystemExit(f"ERROR: expected 24 registered runs, got {len(run_rows)}")

    write_csv(RUNS_CSV, run_rows)
    write_csv(FOLD_CSV, fold_rows)

    runs_df = pd.DataFrame(run_rows)
    summary_rows: list[dict[str, Any]] = []

    b0_vals = runs_df[runs_df["cell_id"] == "B0"].sort_values("fold")["balanced_accuracy"].to_numpy(dtype=float)
    b0_std = float(np.std(b0_vals, ddof=0))
    b0_gap = top3_bottom3_gap(b0_vals.tolist())

    for cell in CELLS:
        g = runs_df[runs_df["cell_id"] == cell.cell_id].sort_values("fold").copy()
        vals = g["balanced_accuracy"].to_numpy(dtype=float)
        mean_bal = float(np.mean(vals))
        std_bal = float(np.std(vals, ddof=0))
        gap = top3_bottom3_gap(vals.tolist())
        delta_vs_b0 = vals - b0_vals if len(vals) == len(b0_vals) else np.full_like(vals, np.nan)
        summary_rows.append({
            "cell_id": cell.cell_id,
            "cell_name": cell.name,
            "transductive": cell.transductive,
            "strict_nontransductive_allowed": cell.strict_nontransductive_allowed,
            "mean_balanced_accuracy": mean_bal,
            "delta_vs_ref_mean_balanced_accuracy": float(mean_bal - REF_BAL_ACC),
            "fold_stdev_balanced_accuracy": std_bal,
            "fold_stdev_delta_vs_B0": float(std_bal - b0_std),
            "bimodal_gap_top3_minus_bottom3": gap,
            "bimodal_gap_delta_vs_B0": float(gap - b0_gap) if np.isfinite(gap) and np.isfinite(b0_gap) else math.nan,
            "positive_fold_count_bal_acc_gt_0_5": int((vals > 0.5).sum()),
            "positive_fold_count_vs_B0": int((delta_vs_b0 > 0).sum()) if cell.cell_id != "B0" else "",
            "moderate_pass_mean_bal_acc_ge_0_53": bool(mean_bal >= 0.53),
            "strong_pass_mean_bal_acc_ge_0_55": bool(mean_bal >= 0.55),
            "heterogeneity_pass_candidate": bool(cell.cell_id != "B0" and std_bal < b0_std and gap < b0_gap),
            "must_not_report_as_strict_nontransductive": bool(cell.transductive),
        })

    best_mean = max(summary_rows, key=lambda r: float(r["mean_balanced_accuracy"]))
    best_nontrans = max([r for r in summary_rows if not r["transductive"]], key=lambda r: float(r["mean_balanced_accuracy"]))
    hetero_cells = [r for r in summary_rows if r["heterogeneity_pass_candidate"]]
    moderate_cells = [r for r in summary_rows if r["moderate_pass_mean_bal_acc_ge_0_53"]]
    strong_cells = [r for r in summary_rows if r["strong_pass_mean_bal_acc_ge_0_55"]]

    if strong_cells:
        diagnosis = "strong_pass_observed"
    elif moderate_cells:
        diagnosis = "moderate_pass_observed"
    elif hetero_cells:
        diagnosis = "heterogeneity_pass_candidate_observed"
    else:
        diagnosis = "no_registered_pass_observed"

    leakage_issue = False
    transductive_labeling_issue = not all(
        (not r["transductive"]) or r["must_not_report_as_strict_nontransductive"]
        for r in summary_rows
    )

    report = {
        "status": "complete_pending_control_tower_review",
        "created_utc": now_utc(),
        "branch": branch,
        "docs_prefix": PREFIX,
        "script": str(SCRIPT_PATH),
        "reference": {
            "id": REF_ID,
            "mean_balanced_accuracy": REF_BAL_ACC,
        },
        "scope": {
            "dataset": "I-DARE only",
            "modality": "EEG only",
            "task": "arousal only",
            "input": "current STIM-BSL summary",
            "formulation": "within-subject pairwise affect preference ranking",
            "model": "RidgeClassifier(alpha=1.0)",
            "folds": 6,
            "registered_runs": len(run_rows),
        },
        "input_artifacts": {
            "cache_index": str(CACHE_INDEX),
            "windows_npy": str(WINDOWS_NPY),
            "windows_shape": [int(v) for v in windows.shape],
            "subject_column": subject_col,
            "arousal_score_column": score_col,
            "n_index_rows": int(len(idx)),
            "n_subjects": int(idx["_subject_str"].nunique()),
        },
        "methodology": {
            "B1_transductive": "per-subject z-score uses unlabeled held-out subject feature statistics",
            "B3_transductive": "per-subject rank transform uses unlabeled held-out subject feature statistics",
            "B2_non_transductive": "train-fold StandardScaler fit on train subjects only",
            "pairwise_feature": "diff plus absdiff of fixed current STIM-BSL summary features",
            "model_side_scaler": "StandardScaler fit on train pairs only for ridge numerical stability, constant across cells",
        },
        "summary": summary_rows,
        "best_overall": best_mean,
        "best_strict_nontransductive": best_nontrans,
        "diagnosis": diagnosis,
        "leakage_issue": leakage_issue,
        "transductive_labeling_issue": transductive_labeling_issue,
        "forbidden_scope_touched": False,
        "outputs": {
            "runs_csv": str(RUNS_CSV),
            "fold_diagnostics_csv": str(FOLD_CSV),
            "report_md": str(REPORT_MD),
            "report_json": str(REPORT_JSON),
            "closeout_md": str(CLOSEOUT_MD),
            "closeout_json": str(CLOSEOUT_JSON),
        },
        "next_allowed_step": "Control Tower review only; do not reopen input definition, Wave 2, neural training, DEAP, fusion, rereference/CAR, or downsampling from this branch.",
    }

    if transductive_labeling_issue:
        raise SystemExit("ERROR: transductive labeling issue detected")

    write_json(REPORT_JSON, report)

    report_md = []
    report_md.append("# W1B — EEG Subject Normalization Report")
    report_md.append("")
    report_md.append(f"- status: `{report['status']}`")
    report_md.append(f"- branch: `{branch}`")
    report_md.append(f"- reference: `{REF_ID}` mean balanced accuracy `{REF_BAL_ACC}`")
    report_md.append(f"- registered runs: `{len(run_rows)}`")
    report_md.append("")
    report_md.append("## Scope")
    report_md.append("")
    report_md.append("- I-DARE only.")
    report_md.append("- EEG only.")
    report_md.append("- Arousal only.")
    report_md.append("- Current STIM-BSL summary input fixed.")
    report_md.append("- Within-subject pairwise affect preference ranking.")
    report_md.append("- Ridge classifier fixed.")
    report_md.append("- No neural training, no DEAP, no fusion, no rereference/CAR, no downsampling rebuild, no cache overwrite.")
    report_md.append("")
    report_md.append("## Methodology Note")
    report_md.append("")
    report_md.append("B1 and B3 are explicitly transductive because they use unlabeled held-out subject feature statistics. They are diagnostic/calibration-style conditions only and must not be reported as strict non-transductive results.")
    report_md.append("")
    report_md.append("## Summary")
    report_md.append("")
    report_md.append(md_table(summary_rows, [
        "cell_id",
        "cell_name",
        "transductive",
        "mean_balanced_accuracy",
        "delta_vs_ref_mean_balanced_accuracy",
        "fold_stdev_balanced_accuracy",
        "fold_stdev_delta_vs_B0",
        "bimodal_gap_top3_minus_bottom3",
        "bimodal_gap_delta_vs_B0",
        "positive_fold_count_bal_acc_gt_0_5",
        "positive_fold_count_vs_B0",
        "moderate_pass_mean_bal_acc_ge_0_53",
        "strong_pass_mean_bal_acc_ge_0_55",
        "heterogeneity_pass_candidate",
    ]))
    report_md.append("")
    report_md.append("## Diagnosis")
    report_md.append("")
    report_md.append(f"`{diagnosis}`")
    report_md.append("")
    report_md.append("## Output Files")
    report_md.append("")
    for key, path in report["outputs"].items():
        report_md.append(f"- {key}: `{path}`")
    report_md.append("")
    REPORT_MD.write_text("\n".join(report_md) + "\n", encoding="utf-8")

    closeout = {
        "status": "closed_pending_control_tower_review",
        "created_utc": now_utc(),
        "source_report": str(REPORT_JSON),
        "diagnosis": diagnosis,
        "best_overall_cell": best_mean["cell_id"],
        "best_overall_mean_balanced_accuracy": best_mean["mean_balanced_accuracy"],
        "best_strict_nontransductive_cell": best_nontrans["cell_id"],
        "best_strict_nontransductive_mean_balanced_accuracy": best_nontrans["mean_balanced_accuracy"],
        "transductive_cells": ["B1", "B3"],
        "strict_nontransductive_cells": ["B0", "B2"],
        "control_tower_handoff": {
            "review_needed": True,
            "do_not_push_to_main": True,
            "do_not_start_wave2_from_w1b": True,
            "do_not_reopen_pairwise_or_input_definition_from_w1b": True
        }
    }
    write_json(CLOSEOUT_JSON, closeout)

    closeout_md = []
    closeout_md.append("# W1B — EEG Subject Normalization Closeout")
    closeout_md.append("")
    closeout_md.append(f"- status: `{closeout['status']}`")
    closeout_md.append(f"- diagnosis: `{diagnosis}`")
    closeout_md.append(f"- best overall cell: `{closeout['best_overall_cell']}`")
    closeout_md.append(f"- best strict non-transductive cell: `{closeout['best_strict_nontransductive_cell']}`")
    closeout_md.append("")
    closeout_md.append("B1 and B3 remain transductive diagnostics only. They must not be promoted as strict non-transductive evidence.")
    closeout_md.append("")
    closeout_md.append("No DEAP, fusion, neural training, rereference/CAR, downsampling rebuild, input-definition ablation, or cache overwrite was performed.")
    closeout_md.append("")
    closeout_md.append("Next step: Control Tower review.")
    closeout_md.append("")
    CLOSEOUT_MD.write_text("\n".join(closeout_md), encoding="utf-8")

    print("===== W1B COMPLETE =====")
    print(json.dumps({
        "diagnosis": diagnosis,
        "best_overall_cell": best_mean["cell_id"],
        "best_overall_mean_balanced_accuracy": round(float(best_mean["mean_balanced_accuracy"]), 6),
        "best_strict_nontransductive_cell": best_nontrans["cell_id"],
        "best_strict_nontransductive_mean_balanced_accuracy": round(float(best_nontrans["mean_balanced_accuracy"]), 6),
        "registered_runs": len(run_rows),
        "report": str(REPORT_MD),
    }, indent=2))

if __name__ == "__main__":
    main()
