#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start minimal subject-relative training first pass ====="
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
import csv
import json
import numpy
import pandas
import torch
print("OK_IMPORTS")
print("cuda_available=", torch.cuda.is_available())
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repo is not clean; commit/stash current changes before running this first pass."
  git status --short --branch
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required inputs ====="
ls -lh \
  docs/idare_minimal_subject_relative_training_objective.md \
  docs/idare_minimal_subject_relative_training_objective.json \
  docs/idare_subject_relative_task_formulation_review_status.md \
  docs/idare_subject_relative_task_formulation_report.md \
  docs/idare_subject_relative_candidate_matrix.csv \
  docs/idare_subject_relative_label_balance_summary.csv \
  docs/idare_broader_eval_eeg_stim_bsl_only_primary.json \
  docs/idare_broader_eval_emg_feature_only_primary.json \
  scripts/20_run_idare_eeg_cache_recipe_stabilization.py \
  scripts/30_run_idare_emg_feature_smoke.py \
  .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy \
  .cache/idare_eeg_cache_index_baseline_corrected.csv \
  .cache/idare_emg_features.npy \
  .cache/idare_emg_feature_cache_index.csv
echo

echo "===== 3) compile scripts ====="
"$PY" -B -m py_compile \
  scripts/20_run_idare_eeg_cache_recipe_stabilization.py \
  scripts/30_run_idare_emg_feature_smoke.py
echo "OK_COMPILE"
echo

echo "===== 4) prepare subject-relative temporary cache indices ====="
TMP_DIR="/tmp/idare_subject_relative_minimal_training"
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"

"$PY" - <<'PY'
import json
from pathlib import Path

import numpy as np
import pandas as pd

TMP = Path("/tmp/idare_subject_relative_minimal_training")
DOCS = Path("docs")
FORMULATION = "subject_top_bottom_quantile_q33"
TASKS = ["valence", "arousal"]

INPUTS = {
    "EEG": Path(".cache/idare_eeg_cache_index_baseline_corrected.csv"),
    "EMG": Path(".cache/idare_emg_feature_cache_index.csv"),
}
OUTPUTS = {
    "EEG": TMP / "eeg_subject_relative_q33_index.csv",
    "EMG": TMP / "emg_subject_relative_q33_index.csv",
}
SUMMARY = TMP / "subject_relative_q33_label_summary.json"

def numeric_series(df, col):
    return pd.to_numeric(df[col], errors="coerce")

def infer_rating_col(df: pd.DataFrame, task: str) -> str:
    lower_to_col = {str(c).lower(): c for c in df.columns}
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
        c = lower_to_col.get(name.lower())
        if c is not None:
            candidates.append(c)
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
        s = numeric_series(df, c).dropna()
        if len(s) == 0:
            continue
        unique = int(s.nunique())
        vmin = float(s.min())
        vmax = float(s.max())
        # Raw DEAP ratings are usually broader than binary labels.
        raw_like = (unique > 2) or (vmax > 1.5) or (vmin < 0.0)
        if not raw_like:
            continue
        exact_bonus = 10 if str(c).lower() == task else 0
        score = exact_bonus + min(unique, 20) + (5 if vmax > 2 else 0)
        scored.append((score, c, unique, vmin, vmax))
    if not scored:
        raise SystemExit(
            f"ERROR: could not infer raw rating column for task={task}. "
            f"Available columns containing task: {[c for c in df.columns if task in str(c).lower()]}"
        )
    scored.sort(reverse=True, key=lambda x: x[0])
    return str(scored[0][1])

def apply_subject_q33(df: pd.DataFrame, task: str, rating_col: str) -> dict:
    label_col = f"{task}_midpoint_as_high"
    if "subject_id" not in df.columns:
        raise SystemExit("ERROR: missing subject_id column")
    if label_col not in df.columns:
        df[label_col] = np.nan

    out = df.copy()
    out["subject_id"] = pd.to_numeric(out["subject_id"], errors="coerce").astype("Int64")
    raw = pd.to_numeric(out[rating_col], errors="coerce")
    labels = pd.Series(np.nan, index=out.index, dtype="float64")
    rows = []

    for subject_id, idx in out.groupby("subject_id", dropna=True).groups.items():
        x = raw.loc[list(idx)].dropna()
        n_nonmissing = int(len(x))
        q_low = None
        q_high = None
        n_low = 0
        n_high = 0
        n_middle = n_nonmissing
        n_valid = 0
        if n_nonmissing > 0:
            q_low = float(x.quantile(1.0 / 3.0))
            q_high = float(x.quantile(2.0 / 3.0))
            if q_high > q_low:
                subject_values = raw.loc[list(idx)]
                low_mask = subject_values <= q_low
                high_mask = subject_values >= q_high
                labels.loc[subject_values[low_mask].index] = 0.0
                labels.loc[subject_values[high_mask].index] = 1.0
                n_low = int(low_mask.fillna(False).sum())
                n_high = int(high_mask.fillna(False).sum())
                n_valid = n_low + n_high
                n_middle = int(n_nonmissing - n_valid)

        rows.append({
            "task": task,
            "subject_id": int(subject_id),
            "rating_col": rating_col,
            "n_nonmissing": n_nonmissing,
            "q_low": q_low,
            "q_high": q_high,
            "n_low": n_low,
            "n_high": n_high,
            "n_middle_discarded": n_middle,
            "n_valid": n_valid,
            "prop_high": float(n_high / n_valid) if n_valid else None,
            "retention_fraction": float(n_valid / n_nonmissing) if n_nonmissing else 0.0,
        })

    out[label_col] = labels
    # Clear alternative policy columns so the temp index is obviously subject-relative only for the chosen policy.
    # Existing scripts will read only *_midpoint_as_high.
    return {"df": out, "rows": rows, "label_col": label_col}

summary = {
    "formulation": FORMULATION,
    "definition": {
        "class_0": "per-subject bottom third of raw rating",
        "class_1": "per-subject top third of raw rating",
        "discard": "per-subject middle third",
    },
    "modalities": {},
}
for modality, input_path in INPUTS.items():
    df = pd.read_csv(input_path)
    modality_rows = []
    rating_cols = {}
    for task in TASKS:
        rating_col = infer_rating_col(df, task)
        rating_cols[task] = rating_col
        result = apply_subject_q33(df, task, rating_col)
        df = result["df"]
        for row in result["rows"]:
            row["modality"] = modality
            modality_rows.append(row)

    output_path = OUTPUTS[modality]
    df.to_csv(output_path, index=False)
    out_rows = pd.DataFrame(modality_rows)
    summary["modalities"][modality] = {
        "input_index": str(input_path),
        "output_index": str(output_path),
        "rating_columns": rating_cols,
        "n_rows": int(len(df)),
        "per_task": {},
    }
    for task, tg in out_rows.groupby("task"):
        summary["modalities"][modality]["per_task"][task] = {
            "subjects": int(tg["subject_id"].nunique()),
            "n_nonmissing": int(tg["n_nonmissing"].sum()),
            "n_valid": int(tg["n_valid"].sum()),
            "n_low": int(tg["n_low"].sum()),
            "n_high": int(tg["n_high"].sum()),
            "n_middle_discarded": int(tg["n_middle_discarded"].sum()),
            "retention_fraction": float(tg["n_valid"].sum() / max(1, tg["n_nonmissing"].sum())),
            "prop_high": float(tg["n_high"].sum() / max(1, tg["n_valid"].sum())),
            "empty_subjects": int((tg["n_valid"] == 0).sum()),
        }

SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("OK_TEMP_INDICES")
print(json.dumps(summary, indent=2))
PY

ls -lh "$TMP_DIR"/*
echo

echo "===== 5) remove stale final outputs ====="
rm -f \
  docs/idare_subject_relative_minimal_eeg_primary.md \
  docs/idare_subject_relative_minimal_eeg_primary.json \
  docs/idare_subject_relative_minimal_eeg_primary_predictions.csv \
  docs/idare_subject_relative_minimal_emg_primary.md \
  docs/idare_subject_relative_minimal_emg_primary.json \
  docs/idare_subject_relative_minimal_emg_primary_predictions.csv \
  docs/idare_subject_relative_minimal_training_report.md \
  docs/idare_subject_relative_minimal_training_report.json
echo "OK_CLEAN_OUTPUT_TARGETS"
echo

echo "===== 6) run EEG minimal subject-relative first pass: 12 runs ====="
"$PY" scripts/20_run_idare_eeg_cache_recipe_stabilization.py \
  --cache-npy .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy \
  --cache-index "$TMP_DIR/eeg_subject_relative_q33_index.csv" \
  --out-md docs/idare_subject_relative_minimal_eeg_primary.md \
  --out-json docs/idare_subject_relative_minimal_eeg_primary.json \
  --out-predictions-csv docs/idare_subject_relative_minimal_eeg_primary_predictions.csv \
  --tasks valence arousal \
  --label-policy midpoint_as_high \
  --recipes ce_class_weighted \
  --folds 6 \
  --seeds 11 \
  --epochs 12 \
  --batch-size 64 \
  --max-runs 0
EEG_EXIT=$?
echo "EEG_EXIT=$EEG_EXIT"
echo

echo "===== 7) run EMG minimal subject-relative first pass: 12 runs ====="
"$PY" scripts/30_run_idare_emg_feature_smoke.py \
  --feature-npy .cache/idare_emg_features.npy \
  --feature-index "$TMP_DIR/emg_subject_relative_q33_index.csv" \
  --out-md docs/idare_subject_relative_minimal_emg_primary.md \
  --out-json docs/idare_subject_relative_minimal_emg_primary.json \
  --out-predictions-csv docs/idare_subject_relative_minimal_emg_primary_predictions.csv \
  --tasks valence arousal \
  --label-policy midpoint_as_high \
  --recipes ce_class_weighted \
  --folds 6 \
  --seeds 11 \
  --epochs 20 \
  --batch-size 128 \
  --max-runs 0
EMG_EXIT=$?
echo "EMG_EXIT=$EMG_EXIT"
echo

echo "===== 8) annotate outputs, validate, and build combined report ====="
"$PY" - <<'PY'
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DOCS = Path("docs")
TMP = Path("/tmp/idare_subject_relative_minimal_training")
NOW = datetime.now(timezone.utc).isoformat()
FORMULATION = "subject_top_bottom_quantile_q33"

EEG_JSON = DOCS / "idare_subject_relative_minimal_eeg_primary.json"
EMG_JSON = DOCS / "idare_subject_relative_minimal_emg_primary.json"
EEG_PRED = DOCS / "idare_subject_relative_minimal_eeg_primary_predictions.csv"
EMG_PRED = DOCS / "idare_subject_relative_minimal_emg_primary_predictions.csv"
REPORT_MD = DOCS / "idare_subject_relative_minimal_training_report.md"
REPORT_JSON = DOCS / "idare_subject_relative_minimal_training_report.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

GLOBAL_BASELINES = {
    "EEG": DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary.json",
    "EMG": DOCS / "idare_broader_eval_emg_feature_only_primary.json",
}
TEMP_INDEX = {
    "EEG": TMP / "eeg_subject_relative_q33_index.csv",
    "EMG": TMP / "emg_subject_relative_q33_index.csv",
}
OUTPUT_JSON = {
    "EEG": EEG_JSON,
    "EMG": EMG_JSON,
}
OUTPUT_PRED = {
    "EEG": EEG_PRED,
    "EMG": EMG_PRED,
}

def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def count_prediction_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))

def metric_from_row(row: dict[str, Any], metric: str) -> float | None:
    names = [
        metric,
        f"{metric}_mean",
        f"final_{metric}",
        f"final_{metric}_mean",
    ]
    # metric aliases
    aliases = {
        "macro_f1": ["macro_f1", "final_macro_f1", "final_macro_f1_mean"],
        "balanced_accuracy": ["balanced_accuracy", "final_balanced_accuracy", "final_balanced_accuracy_mean", "final_bal_acc", "final_bal_acc_mean"],
        "accuracy": ["accuracy", "final_accuracy", "final_accuracy_mean", "final_acc", "final_acc_mean"],
    }
    for name in aliases.get(metric, names):
        if name in row:
            v = row[name]
            if isinstance(v, dict):
                if "mean" in v:
                    return float(v["mean"])
            try:
                return float(v)
            except Exception:
                pass
    return None

def aggregate_row(data: dict[str, Any], task: str, recipe: str) -> dict[str, Any]:
    rows = data.get("aggregate") or data.get("aggregates") or []
    if isinstance(rows, dict):
        rows = list(rows.values())
    for r in rows:
        if str(r.get("task")) == task and str(r.get("recipe")) == recipe:
            return r
    # Fallback from runs.
    runs = [
        r for r in data.get("runs", [])
        if str(r.get("task")) == task and str(r.get("recipe")) == recipe
    ]
    if not runs:
        return {}
    def mean_key(*keys):
        vals = []
        for r in runs:
            for k in keys:
                if k in r:
                    try:
                        vals.append(float(r[k]))
                        break
                    except Exception:
                        pass
        return float(np.mean(vals)) if vals else None
    return {
        "task": task,
        "recipe": recipe,
        "runs": len(runs),
        "final_macro_f1_mean": mean_key("final_macro_f1", "macro_f1"),
        "final_balanced_accuracy_mean": mean_key("final_balanced_accuracy", "balanced_accuracy"),
        "final_accuracy_mean": mean_key("final_accuracy", "accuracy"),
        "one_class_final_runs": sum(1 for r in runs if bool(r.get("one_class_pred"))),
    }

def make_folds(subjects, n_folds=6, seed=11):
    subjects = np.asarray(sorted(set(int(s) for s in subjects)), dtype=int)
    rng = np.random.default_rng(int(seed))
    permuted = rng.permutation(subjects)
    chunks = np.array_split(permuted, n_folds)
    folds = {}
    for i, chunk in enumerate(chunks, start=1):
        val = sorted(int(x) for x in chunk.tolist())
        folds[i] = val
    return folds

def retained_counts(temp_index: Path, task: str, val_subjects: list[int]) -> dict[str, int]:
    df = pd.read_csv(temp_index)
    col = f"{task}_midpoint_as_high"
    if col not in df.columns:
        raise SystemExit(f"ERROR missing label column {col} in {temp_index}")
    df["subject_id"] = pd.to_numeric(df["subject_id"], errors="coerce").astype("Int64")
    labels = pd.to_numeric(df[col], errors="coerce")
    valid = df[labels.isin([0.0, 1.0])].copy()
    val_set = {int(s) for s in val_subjects}
    val = valid[valid["subject_id"].astype(int).isin(val_set)]
    train = valid[~valid["subject_id"].astype(int).isin(val_set)]
    return {
        "retained_train_n": int(len(train)),
        "retained_val_n": int(len(val)),
        "retained_train_class0": int((pd.to_numeric(train[col], errors="coerce") == 0).sum()),
        "retained_train_class1": int((pd.to_numeric(train[col], errors="coerce") == 1).sum()),
        "retained_val_class0": int((pd.to_numeric(val[col], errors="coerce") == 0).sum()),
        "retained_val_class1": int((pd.to_numeric(val[col], errors="coerce") == 1).sum()),
    }

def annotate_json(modality: str, path: Path) -> dict[str, Any]:
    data = load_json(path)
    runs = data.get("runs", [])
    if len(runs) != 12:
        raise SystemExit(f"ERROR: {modality} expected 12 runs, got {len(runs)}")

    subjects = sorted(pd.read_csv(TEMP_INDEX[modality])["subject_id"].dropna().astype(int).unique().tolist())
    folds = make_folds(subjects, 6, 11)

    for run in runs:
        fold_id = run.get("fold_id", run.get("fold"))
        if fold_id is None:
            fold_id = run.get("run_spec", {}).get("fold_id")
        fold_id = int(fold_id)
        val_subjects = run.get("val_subjects")
        if val_subjects is None:
            val_subjects = folds[fold_id]
            run["val_subjects"] = val_subjects
        task = str(run.get("task"))
        counts = retained_counts(TEMP_INDEX[modality], task, [int(s) for s in val_subjects])
        run["subject_relative_formulation"] = FORMULATION
        run["subject_relative_label_policy_alias"] = "midpoint_as_high"
        run["subject_relative_definition"] = "per-subject bottom third=0, top third=1, middle third discarded"
        run.update(counts)
        if counts["retained_val_n"] <= 0:
            raise SystemExit(f"ERROR: {modality} run {run.get('run_id')} has empty retained val set")

    data["subject_relative_formulation"] = FORMULATION
    data["subject_relative_definition"] = {
        "class_0": "per-subject bottom third of raw rating",
        "class_1": "per-subject top third of raw rating",
        "discard": "per-subject middle third",
    }
    data["subject_relative_temp_index_used"] = str(TEMP_INDEX[modality])
    data["status"] = data.get("status") or "subject_relative_minimal_first_pass_complete"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return data

annotated = {modality: annotate_json(modality, path) for modality, path in OUTPUT_JSON.items()}

for modality, pred in OUTPUT_PRED.items():
    rows = count_prediction_rows(pred)
    if rows <= 0:
        raise SystemExit(f"ERROR: empty prediction CSV {pred}")
    print(f"{modality} prediction rows={rows}")

comparison_rows = []
for modality in ["EEG", "EMG"]:
    new_data = annotated[modality]
    base_data = load_json(GLOBAL_BASELINES[modality])
    for task in ["valence", "arousal"]:
        new_row = aggregate_row(new_data, task, "ce_class_weighted")
        base_row = aggregate_row(base_data, task, "ce_class_weighted")
        new_macro = metric_from_row(new_row, "macro_f1")
        base_macro = metric_from_row(base_row, "macro_f1")
        new_bal = metric_from_row(new_row, "balanced_accuracy")
        base_bal = metric_from_row(base_row, "balanced_accuracy")
        runs = [r for r in new_data.get("runs", []) if r.get("task") == task and r.get("recipe") == "ce_class_weighted"]
        comparison_rows.append({
            "modality": modality,
            "task": task,
            "recipe": "ce_class_weighted",
            "subject_relative_macro_f1": new_macro,
            "global_label_macro_f1": base_macro,
            "delta_macro_f1": None if new_macro is None or base_macro is None else float(new_macro - base_macro),
            "subject_relative_balanced_accuracy": new_bal,
            "global_label_balanced_accuracy": base_bal,
            "delta_balanced_accuracy": None if new_bal is None or base_bal is None else float(new_bal - base_bal),
            "subject_relative_runs": len(runs),
            "one_class_runs": int(sum(1 for r in runs if bool(r.get("one_class_pred")))),
            "retained_val_n_total": int(sum(int(r.get("retained_val_n", 0)) for r in runs)),
            "retained_val_n_mean": float(np.mean([int(r.get("retained_val_n", 0)) for r in runs])) if runs else None,
        })

deltas = [r["delta_macro_f1"] for r in comparison_rows if r["delta_macro_f1"] is not None]
mean_delta = float(np.mean(deltas)) if deltas else None
min_delta = float(np.min(deltas)) if deltas else None
positive = sum(1 for d in deltas if d > 0.0)

if deltas and positive == len(deltas) and mean_delta is not None and mean_delta >= 0.02:
    recommended_next = "minimal_subject_relative_balanced_sampler_pass_objective"
    diagnosis = "subject_relative_first_pass_promising"
elif deltas and positive >= 2 and mean_delta is not None and mean_delta > 0.0:
    recommended_next = "subject_relative_training_review_closeout_objective"
    diagnosis = "subject_relative_first_pass_mixed_promising"
else:
    recommended_next = "subject_relative_representation_preprocessing_objective"
    diagnosis = "subject_relative_first_pass_not_sufficient_alone"

report = {
    "status": "complete_pending_review",
    "created_or_updated_utc": NOW,
    "objective": "docs/idare_minimal_subject_relative_training_objective.md",
    "evidence_level": "minimal controlled diagnostic training first pass; no final LOSO claim; no mainline change",
    "subject_relative_formulation": FORMULATION,
    "matrix": {
        "planned_runs": 24,
        "completed_runs": int(sum(len(d.get("runs", [])) for d in annotated.values())),
        "modalities": ["EEG", "EMG"],
        "tasks": ["valence", "arousal"],
        "recipe": "ce_class_weighted",
        "folds": 6,
        "seed": 11,
    },
    "validation": {
        "all_json_valid": True,
        "prediction_csv_rows": {
            "EEG": count_prediction_rows(EEG_PRED),
            "EMG": count_prediction_rows(EMG_PRED),
        },
        "all_runs_annotated_with_formulation_and_retained_val_n": all(
            "subject_relative_formulation" in r and int(r.get("retained_val_n", 0)) > 0
            for data in annotated.values()
            for r in data.get("runs", [])
        ),
    },
    "comparison_against_global_label_mainline": comparison_rows,
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next,
    "not_authorized": [
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "final global label-policy lock",
        "architecture ablation for improvement",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "broad hyperparameter search",
        "mainline change",
        "BSL-stats sidecars in first pass",
    ],
    "outputs": {
        "eeg_md": "docs/idare_subject_relative_minimal_eeg_primary.md",
        "eeg_json": "docs/idare_subject_relative_minimal_eeg_primary.json",
        "eeg_predictions": "docs/idare_subject_relative_minimal_eeg_primary_predictions.csv",
        "emg_md": "docs/idare_subject_relative_minimal_emg_primary.md",
        "emg_json": "docs/idare_subject_relative_minimal_emg_primary.json",
        "emg_predictions": "docs/idare_subject_relative_minimal_emg_primary_predictions.csv",
        "report_md": str(REPORT_MD),
        "report_json": str(REPORT_JSON),
    },
    "next_allowed_step": "Human review / closeout before any optional balanced-sampler pass, preprocessing objective, BSL-stats sidecar, or stop/handoff decision.",
}
REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def fmt(x, d=4):
    if x is None:
        return "NA"
    try:
        if math.isnan(float(x)):
            return "NA"
        return f"{float(x):.{d}f}"
    except Exception:
        return str(x)

md = []
md.append("# I-DARE Minimal Subject-relative Training Report")
md.append("")
md.append("## Status")
md.append("")
md.append("Minimal subject-relative first-pass diagnostic training complete; pending human review.")
md.append("")
md.append(f"Generated UTC: `{NOW}`")
md.append("")
md.append("No final LOSO claim or mainline change is made.")
md.append("")
md.append("## Run Matrix")
md.append("")
md.append("| Dimension | Value |")
md.append("|---|---|")
md.append("| Formulation | `subject_top_bottom_quantile_q33` |")
md.append("| Definition | per-subject bottom third = 0, top third = 1, middle third discarded |")
md.append("| Modalities | EEG `STIM-BSL`-only; EMG feature-only |")
md.append("| Tasks | valence; arousal |")
md.append("| Recipe | `ce_class_weighted` |")
md.append("| Folds / seed | 6 folds, seed 11 |")
md.append("| Completed runs | 24 |")
md.append("")
md.append("## Validation")
md.append("")
md.append(f"- EEG prediction rows: `{report['validation']['prediction_csv_rows']['EEG']}`")
md.append(f"- EMG prediction rows: `{report['validation']['prediction_csv_rows']['EMG']}`")
md.append(f"- All runs annotated with formulation and retained validation count: `{report['validation']['all_runs_annotated_with_formulation_and_retained_val_n']}`")
md.append("")
md.append("## Comparison Against Previous Global-label Mainline")
md.append("")
md.append("| Modality | Task | Subject-relative macro F1 | Global-label macro F1 | Delta macro F1 | Subject-relative bal acc | Global-label bal acc | Delta bal acc | Retained val n total | One-class runs |")
md.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for r in comparison_rows:
    md.append(
        f"| {r['modality']} | {r['task']} | {fmt(r['subject_relative_macro_f1'])} | "
        f"{fmt(r['global_label_macro_f1'])} | {fmt(r['delta_macro_f1'])} | "
        f"{fmt(r['subject_relative_balanced_accuracy'])} | {fmt(r['global_label_balanced_accuracy'])} | "
        f"{fmt(r['delta_balanced_accuracy'])} | {r['retained_val_n_total']} | {r['one_class_runs']} |"
    )
md.append("")
md.append("## Diagnosis")
md.append("")
md.append(f"`{diagnosis}`")
md.append("")
md.append(f"Mean delta macro F1 across modality/task cells: `{fmt(mean_delta)}`")
md.append("")
md.append(f"Positive delta cells: `{positive}/{len(deltas)}`")
md.append("")
md.append("## Recommendation")
md.append("")
md.append(f"Recommended next objective after human review: `{recommended_next}`")
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

# Update central roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
row = "| I-DARE minimal subject-relative training report | 24-run first-pass subject-relative diagnostic training complete; pending human review | yes | `docs/idare_subject_relative_minimal_training_report.md` | Human review / closeout before optional second pass or next fix objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search; mainline change. |"
if "I-DARE minimal subject-relative training report" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE minimal subject-relative training objective |"):
            out.append(row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert report row")
    project_md = "\n".join(out) + "\n"
bullet = f"- Minimal subject-relative first-pass training is complete in `docs/idare_subject_relative_minimal_training_report.md`; recommended next objective is `{recommended_next}` after human review."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: project status marker not found")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = load_json(PROJECT_JSON)
decisions = project_json.setdefault("decisions", {})
decisions["idare_subject_relative_minimal_training_report"] = {
    "status": "complete_pending_review",
    "evidence": str(REPORT_MD),
    "evidence_json": str(REPORT_JSON),
    "subject_relative_formulation": FORMULATION,
    "completed_runs": report["matrix"]["completed_runs"],
    "diagnosis": diagnosis,
    "recommended_next_objective": recommended_next,
    "claim_level": report["evidence_level"],
    "not_authorized": report["not_authorized"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_SUBJECT_RELATIVE_MINIMAL_REPORT_WRITTEN")
print(REPORT_MD)
print(REPORT_JSON)
print("diagnosis=", diagnosis)
print("recommended_next_objective=", recommended_next)
PY
echo

echo "===== 9) validate final outputs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path

files = [
    Path("docs/idare_subject_relative_minimal_eeg_primary.json"),
    Path("docs/idare_subject_relative_minimal_emg_primary.json"),
    Path("docs/idare_subject_relative_minimal_training_report.json"),
    Path("docs/project_status_current.json"),
]
for p in files:
    json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)

for p, expected_runs in [
    (Path("docs/idare_subject_relative_minimal_eeg_primary.json"), 12),
    (Path("docs/idare_subject_relative_minimal_emg_primary.json"), 12),
]:
    data = json.loads(p.read_text(encoding="utf-8"))
    runs = data.get("runs", [])
    print(p.name, "runs=", len(runs), "formulation=", data.get("subject_relative_formulation"))
    if len(runs) != expected_runs:
        raise SystemExit(f"ERROR: {p} expected {expected_runs} runs")
    if any(r.get("subject_relative_formulation") != "subject_top_bottom_quantile_q33" for r in runs):
        raise SystemExit(f"ERROR: {p} missing run formulation annotation")
    if any(int(r.get("retained_val_n", 0)) <= 0 for r in runs):
        raise SystemExit(f"ERROR: {p} has nonpositive retained_val_n")

for p in [
    Path("docs/idare_subject_relative_minimal_eeg_primary_predictions.csv"),
    Path("docs/idare_subject_relative_minimal_emg_primary_predictions.csv"),
]:
    with p.open(newline="", encoding="utf-8") as f:
        n = sum(1 for _ in csv.DictReader(f))
    print(p.name, "rows=", n)
    if n <= 0:
        raise SystemExit(f"ERROR: empty predictions {p}")

print("ALL_SUBJECT_RELATIVE_MINIMAL_OUTPUTS_VALID")
PY

grep -n "## Status\|## Run Matrix\|## Comparison Against Previous Global-label Mainline\|## Diagnosis\|## Recommendation\|## Next Allowed Step" docs/idare_subject_relative_minimal_training_report.md
grep -n "minimal subject-relative training report" docs/project_status_current.md
echo

echo "===== 10) file list ====="
ls -lh \
  docs/idare_subject_relative_minimal_eeg_primary.md \
  docs/idare_subject_relative_minimal_eeg_primary.json \
  docs/idare_subject_relative_minimal_eeg_primary_predictions.csv \
  docs/idare_subject_relative_minimal_emg_primary.md \
  docs/idare_subject_relative_minimal_emg_primary.json \
  docs/idare_subject_relative_minimal_emg_primary_predictions.csv \
  docs/idare_subject_relative_minimal_training_report.md \
  docs/idare_subject_relative_minimal_training_report.json
echo

echo "===== 11) status before commit ====="
git status --short --branch
echo

echo "===== 12) commit and push first-pass outputs ====="
git add \
  docs/idare_subject_relative_minimal_eeg_primary.md \
  docs/idare_subject_relative_minimal_eeg_primary.json \
  docs/idare_subject_relative_minimal_eeg_primary_predictions.csv \
  docs/idare_subject_relative_minimal_emg_primary.md \
  docs/idare_subject_relative_minimal_emg_primary.json \
  docs/idare_subject_relative_minimal_emg_primary_predictions.csv \
  docs/idare_subject_relative_minimal_training_report.md \
  docs/idare_subject_relative_minimal_training_report.json \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "exp: run I-DARE minimal subject-relative training"

git push origin main
echo

echo "===== 13) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_minimal_subject_relative_training_run.log"
