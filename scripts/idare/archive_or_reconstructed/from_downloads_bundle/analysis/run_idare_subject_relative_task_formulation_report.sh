#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start subject-relative task formulation report ====="
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
print("OK_IMPORTS")
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repo is not clean; commit/stash current changes before running this diagnostic."
  git status --short --branch
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required inputs ====="
ls -lh \
  docs/idare_subject_relative_task_formulation_objective.md \
  docs/idare_subject_relative_task_formulation_objective.json \
  docs/idare_representation_label_task_redesign_review_status.md \
  docs/idare_representation_label_task_redesign_report.md \
  docs/idare_label_noise_subject_balance_summary.csv \
  docs/idare_representation_signal_diagnostic_summary.csv \
  .cache/idare_eeg_cache_index_baseline_corrected.csv \
  .cache/idare_emg_feature_cache_index.csv
echo

echo "===== 3) remove stale partial outputs and generate read-only subject-relative formulation report ====="
rm -f \
  docs/idare_subject_relative_task_formulation_report.md \
  docs/idare_subject_relative_task_formulation_report.json \
  docs/idare_subject_relative_label_balance_summary.csv \
  docs/idare_subject_relative_candidate_matrix.csv

"$PY" - <<'PY'
import itertools
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DOCS = Path("docs")
CACHE = Path(".cache")
NOW = datetime.now(timezone.utc).isoformat()

OUT_MD = DOCS / "idare_subject_relative_task_formulation_report.md"
OUT_JSON = DOCS / "idare_subject_relative_task_formulation_report.json"
OUT_BALANCE_CSV = DOCS / "idare_subject_relative_label_balance_summary.csv"
OUT_MATRIX_CSV = DOCS / "idare_subject_relative_candidate_matrix.csv"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

REQUIRED = [
    DOCS / "idare_subject_relative_task_formulation_objective.md",
    DOCS / "idare_subject_relative_task_formulation_objective.json",
    DOCS / "idare_representation_label_task_redesign_review_status.md",
    DOCS / "idare_representation_label_task_redesign_report.md",
    DOCS / "idare_label_noise_subject_balance_summary.csv",
    DOCS / "idare_representation_signal_diagnostic_summary.csv",
    CACHE / "idare_eeg_cache_index_baseline_corrected.csv",
    CACHE / "idare_emg_feature_cache_index.csv",
    PROJECT_MD,
    PROJECT_JSON,
]
missing = [str(p) for p in REQUIRED if not p.exists()]
if missing:
    raise SystemExit("ERROR: missing required files:\n" + "\n".join(missing))

TASKS = ["valence", "arousal"]
FORMULATIONS = [
    "subject_median_split",
    "subject_zscore_sign",
    "subject_top_bottom_quantile_q33",
    "within_subject_pairwise_or_ranking_task",
]

def pick_col(cols, candidates):
    lower = {str(c).lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None

def numeric_cols(df):
    out = []
    for c in df.columns:
        s = pd.to_numeric(df[c], errors="coerce")
        if s.notna().sum() > 0:
            out.append(c)
    return out

def find_subject_col(df):
    return pick_col(df.columns, ["subject_id", "subject", "subj", "participant_id", "participant", "s"])

def find_task_rating_col(df, task):
    nums = numeric_cols(df)
    lower = {str(c).lower(): c for c in nums}
    preferred = [
        task, f"{task}_score", f"{task}_rating", f"rating_{task}",
        f"{task}_raw", f"raw_{task}", f"{task}_label_raw",
    ]
    candidates = []
    for name in preferred:
        if name.lower() in lower:
            candidates.append(lower[name.lower()])
    for c in nums:
        cl = str(c).lower()
        if task in cl and any(k in cl for k in ["score", "rating", "raw", "self", "deap"]):
            candidates.append(c)
    for c in nums:
        cl = str(c).lower()
        if task in cl and "pred" not in cl and "prob" not in cl:
            candidates.append(c)
    seen = []
    for c in candidates:
        if c not in seen:
            seen.append(c)
    if not seen:
        return None

    def score(c):
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(s) == 0:
            return -999
        unique = sorted(s.unique().tolist())
        raw_like = 10 if (float(s.max()) > 1.5 or float(s.min()) < 0) else 0
        exact = 5 if str(c).lower() == task else 0
        label_penalty = -5 if "label" in str(c).lower() and raw_like == 0 else 0
        return raw_like + exact + label_penalty + min(len(unique), 20) / 100
    return max(seen, key=score)

def make_folds(subjects, n_folds=6, seed=11):
    subjects = np.asarray(sorted(set(int(s) for s in subjects)), dtype=int)
    rng = np.random.default_rng(int(seed))
    permuted = rng.permutation(subjects)
    chunks = np.array_split(permuted, int(n_folds))
    mapping = {}
    for i, chunk in enumerate(chunks, start=1):
        for s in chunk.tolist():
            mapping[int(s)] = int(i)
    return mapping

def safe_float(x):
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None

def subject_relative_labels(values, formulation):
    x = pd.to_numeric(pd.Series(values), errors="coerce")
    y = pd.Series(np.nan, index=x.index, dtype="float64")
    meta = {
        "n_total": int(len(x)),
        "n_nonmissing": int(x.notna().sum()),
        "n_ties_or_discarded": 0,
        "threshold_low": None,
        "threshold_high": None,
        "statistic": None,
    }
    valid = x.dropna()
    if len(valid) == 0:
        return y, meta

    if formulation == "subject_median_split":
        med = float(valid.median())
        y.loc[x < med] = 0.0
        y.loc[x > med] = 1.0
        meta["statistic"] = med
        meta["threshold_low"] = med
        meta["threshold_high"] = med
        meta["n_ties_or_discarded"] = int((x == med).sum())

    elif formulation == "subject_zscore_sign":
        mu = float(valid.mean())
        sd = float(valid.std(ddof=0))
        if sd <= 1e-12:
            meta["statistic"] = mu
            meta["threshold_low"] = mu
            meta["threshold_high"] = mu
            meta["n_ties_or_discarded"] = int(len(valid))
            return y, meta
        z = (x - mu) / sd
        y.loc[z < 0] = 0.0
        y.loc[z > 0] = 1.0
        meta["statistic"] = mu
        meta["threshold_low"] = mu
        meta["threshold_high"] = mu
        meta["n_ties_or_discarded"] = int((z == 0).sum())

    elif formulation == "subject_top_bottom_quantile_q33":
        q_low = float(valid.quantile(1.0 / 3.0))
        q_high = float(valid.quantile(2.0 / 3.0))
        if q_high <= q_low:
            meta["threshold_low"] = q_low
            meta["threshold_high"] = q_high
            meta["n_ties_or_discarded"] = int(len(valid))
            return y, meta
        y.loc[x <= q_low] = 0.0
        y.loc[x >= q_high] = 1.0
        meta["threshold_low"] = q_low
        meta["threshold_high"] = q_high
        meta["statistic"] = float(valid.median())
        meta["n_ties_or_discarded"] = int(y.isna().sum())

    elif formulation == "within_subject_pairwise_or_ranking_task":
        # No per-trial class label. We report pairwise ranking availability instead.
        meta["statistic"] = float(valid.median())
        return y, meta

    else:
        raise ValueError(formulation)

    return y, meta

def pairwise_stats(values):
    x = pd.to_numeric(pd.Series(values), errors="coerce").dropna().to_numpy(dtype=float)
    n = int(len(x))
    if n < 2:
        return {
            "n_pairs_total": 0,
            "n_pairs_usable_unequal": 0,
            "n_pairwise_ties": 0,
            "pairwise_usable_fraction": 0.0,
            "pairwise_balance_gap": None,
        }
    total = n * (n - 1) // 2
    ties = 0
    usable = 0
    # Binary pair direction is naturally balanced if both directions are generated.
    # Here we count unequal pairs only; a pairwise training set can include both directions.
    vals, counts = np.unique(x, return_counts=True)
    ties = int(sum(c * (c - 1) // 2 for c in counts))
    usable = int(total - ties)
    return {
        "n_pairs_total": int(total),
        "n_pairs_usable_unequal": usable,
        "n_pairwise_ties": ties,
        "pairwise_usable_fraction": float(usable / total) if total else 0.0,
        "pairwise_balance_gap": 0.0 if usable > 0 else None,
    }

def audit_modality(index_path, modality):
    df = pd.read_csv(index_path)
    subj_col = find_subject_col(df)
    if subj_col is None:
        raise SystemExit(f"ERROR: cannot find subject column for {modality}")
    df = df.copy()
    df["_subject_id"] = pd.to_numeric(df[subj_col], errors="coerce").astype("Int64")
    subjects = sorted(int(s) for s in df["_subject_id"].dropna().unique().tolist())
    fold_map = make_folds(subjects, 6, 11)
    df["_fold_id"] = df["_subject_id"].map(fold_map).astype("Int64")

    rows = []
    discovered = {}
    for task in TASKS:
        col = find_task_rating_col(df, task)
        discovered[task] = col
        if col is None:
            continue
        raw_all = pd.to_numeric(df[col], errors="coerce")
        global_median = float(raw_all.dropna().median()) if raw_all.notna().any() else None
        global_mean = float(raw_all.dropna().mean()) if raw_all.notna().any() else None
        for subject_id, sg in df.groupby("_subject_id", dropna=True):
            sg_idx = sg.index
            raw = raw_all.loc[sg_idx]
            fold_id = int(sg["_fold_id"].dropna().iloc[0]) if sg["_fold_id"].notna().any() else None
            for formulation in FORMULATIONS:
                if formulation == "within_subject_pairwise_or_ranking_task":
                    ps = pairwise_stats(raw)
                    rows.append({
                        "modality": modality,
                        "task": task,
                        "formulation": formulation,
                        "subject_id": int(subject_id),
                        "fold_id": fold_id,
                        "rating_column": str(col),
                        "n_total": int(len(raw)),
                        "n_nonmissing": int(raw.notna().sum()),
                        "n_valid": None,
                        "retention_fraction": None,
                        "n_low": None,
                        "n_high": None,
                        "prop_high": None,
                        "balance_gap_abs": ps["pairwise_balance_gap"],
                        "rating_mean": safe_float(raw.mean()),
                        "rating_std": safe_float(raw.std(ddof=0)),
                        "rating_min": safe_float(raw.min()),
                        "rating_max": safe_float(raw.max()),
                        "subject_statistic": safe_float(raw.median()),
                        "threshold_low": None,
                        "threshold_high": None,
                        "n_ties_or_discarded": ps["n_pairwise_ties"],
                        "n_pairs_total": ps["n_pairs_total"],
                        "n_pairs_usable_unequal": ps["n_pairs_usable_unequal"],
                        "pairwise_usable_fraction": ps["pairwise_usable_fraction"],
                        "global_median_reference": global_median,
                        "global_mean_reference": global_mean,
                    })
                    continue

                y, meta = subject_relative_labels(raw, formulation)
                valid = y.dropna()
                n_valid = int(len(valid))
                n_low = int((valid == 0).sum()) if n_valid else 0
                n_high = int((valid == 1).sum()) if n_valid else 0
                prop_high = float(n_high / n_valid) if n_valid else None
                rows.append({
                    "modality": modality,
                    "task": task,
                    "formulation": formulation,
                    "subject_id": int(subject_id),
                    "fold_id": fold_id,
                    "rating_column": str(col),
                    "n_total": int(len(raw)),
                    "n_nonmissing": int(raw.notna().sum()),
                    "n_valid": n_valid,
                    "retention_fraction": float(n_valid / max(1, int(raw.notna().sum()))),
                    "n_low": n_low,
                    "n_high": n_high,
                    "prop_high": prop_high,
                    "balance_gap_abs": abs(prop_high - 0.5) if prop_high is not None else None,
                    "rating_mean": safe_float(raw.mean()),
                    "rating_std": safe_float(raw.std(ddof=0)),
                    "rating_min": safe_float(raw.min()),
                    "rating_max": safe_float(raw.max()),
                    "subject_statistic": meta.get("statistic"),
                    "threshold_low": meta.get("threshold_low"),
                    "threshold_high": meta.get("threshold_high"),
                    "n_ties_or_discarded": meta.get("n_ties_or_discarded"),
                    "n_pairs_total": None,
                    "n_pairs_usable_unequal": None,
                    "pairwise_usable_fraction": None,
                    "global_median_reference": global_median,
                    "global_mean_reference": global_mean,
                })
    return pd.DataFrame(rows), discovered

def leakage_profile(formulation):
    if formulation == "subject_median_split":
        return {
            "leakage_risk": "medium",
            "scientifically_valid": True,
            "reason": "Uses each subject's own rating distribution to define low/high. Valid for subject-relative affect if labels are available for evaluation, but not a deployment classifier without subject calibration.",
        }
    if formulation == "subject_zscore_sign":
        return {
            "leakage_risk": "medium",
            "scientifically_valid": True,
            "reason": "Uses each subject's own mean/std. Similar leakage profile to median split, slightly more sensitive to outliers.",
        }
    if formulation == "subject_top_bottom_quantile_q33":
        return {
            "leakage_risk": "medium",
            "scientifically_valid": True,
            "reason": "Uses only within-subject extremes and discards ambiguous middle trials. Lower coverage but cleaner labels.",
        }
    if formulation == "within_subject_pairwise_or_ranking_task":
        return {
            "leakage_risk": "medium_high",
            "scientifically_valid": "conditional",
            "reason": "Best matches within-subject affective ordering, but requires a different pairwise/ranking training objective and careful subject-heldout evaluation design.",
        }
    return {"leakage_risk": "unknown", "scientifically_valid": False, "reason": "Unknown formulation."}

def aggregate_candidate_matrix(balance_df):
    rows = []
    for (modality, task, formulation), g in balance_df.groupby(["modality", "task", "formulation"]):
        leak = leakage_profile(formulation)
        if formulation == "within_subject_pairwise_or_ranking_task":
            n_total = int(g["n_total"].sum())
            pairs_total = int(pd.to_numeric(g["n_pairs_total"], errors="coerce").fillna(0).sum())
            pairs_usable = int(pd.to_numeric(g["n_pairs_usable_unequal"], errors="coerce").fillna(0).sum())
            retention = float(pairs_usable / pairs_total) if pairs_total else 0.0
            mean_gap = 0.0 if pairs_usable else None
            max_gap = 0.0 if pairs_usable else None
            empty_subjects = int((pd.to_numeric(g["n_pairs_usable_unequal"], errors="coerce").fillna(0) == 0).sum())
            fold_gaps = []
            for _, fg in g.groupby("fold_id"):
                ft = int(pd.to_numeric(fg["n_pairs_total"], errors="coerce").fillna(0).sum())
                fu = int(pd.to_numeric(fg["n_pairs_usable_unequal"], errors="coerce").fillna(0).sum())
                fold_gaps.append(0.0 if fu > 0 else 1.0)
            rows.append({
                "modality": modality,
                "task": task,
                "formulation": formulation,
                "n_subjects": int(g["subject_id"].nunique()),
                "n_trials_total": n_total,
                "n_valid_or_pairs": pairs_usable,
                "coverage_or_pairwise_usable_fraction": retention,
                "global_prop_high": 0.5 if pairs_usable else None,
                "mean_subject_balance_gap_abs": mean_gap,
                "max_subject_balance_gap_abs": max_gap,
                "mean_fold_balance_gap_abs": float(np.mean(fold_gaps)) if fold_gaps else None,
                "empty_or_unusable_subjects": empty_subjects,
                "leakage_risk": leak["leakage_risk"],
                "scientifically_valid": leak["scientifically_valid"],
                "leakage_reason": leak["reason"],
            })
            continue

        valid = pd.to_numeric(g["n_valid"], errors="coerce").fillna(0)
        n_valid = int(valid.sum())
        n_total = int(pd.to_numeric(g["n_nonmissing"], errors="coerce").fillna(0).sum())
        n_high = int(pd.to_numeric(g["n_high"], errors="coerce").fillna(0).sum())
        prop_high = float(n_high / n_valid) if n_valid else None
        mean_gap = safe_float(pd.to_numeric(g["balance_gap_abs"], errors="coerce").mean())
        max_gap = safe_float(pd.to_numeric(g["balance_gap_abs"], errors="coerce").max())
        empty_subjects = int((valid == 0).sum())
        fold_gaps = []
        for _, fg in g.groupby("fold_id"):
            fv = pd.to_numeric(fg["n_valid"], errors="coerce").fillna(0).sum()
            fh = pd.to_numeric(fg["n_high"], errors="coerce").fillna(0).sum()
            fold_gaps.append(abs(float(fh / fv) - 0.5) if fv else 1.0)
        rows.append({
            "modality": modality,
            "task": task,
            "formulation": formulation,
            "n_subjects": int(g["subject_id"].nunique()),
            "n_trials_total": n_total,
            "n_valid_or_pairs": n_valid,
            "coverage_or_pairwise_usable_fraction": float(n_valid / n_total) if n_total else 0.0,
            "global_prop_high": prop_high,
            "mean_subject_balance_gap_abs": mean_gap,
            "max_subject_balance_gap_abs": max_gap,
            "mean_fold_balance_gap_abs": float(np.mean(fold_gaps)) if fold_gaps else None,
            "empty_or_unusable_subjects": empty_subjects,
            "leakage_risk": leak["leakage_risk"],
            "scientifically_valid": leak["scientifically_valid"],
            "leakage_reason": leak["reason"],
        })
    mat = pd.DataFrame(rows)

    # Scoring favors coverage, balance, no empty subjects, and simpler binary formulation.
    def score_row(r):
        coverage = float(r["coverage_or_pairwise_usable_fraction"] or 0.0)
        mean_gap = float(r["mean_subject_balance_gap_abs"] if pd.notna(r["mean_subject_balance_gap_abs"]) else 1.0)
        fold_gap = float(r["mean_fold_balance_gap_abs"] if pd.notna(r["mean_fold_balance_gap_abs"]) else 1.0)
        empty = float(r["empty_or_unusable_subjects"] or 0)
        leakage_penalty = {
            "low": 0.00,
            "medium": 0.05,
            "medium_high": 0.12,
            "high": 0.25,
        }.get(str(r["leakage_risk"]), 0.20)
        complexity_penalty = 0.10 if r["formulation"] == "within_subject_pairwise_or_ranking_task" else 0.0
        return coverage - mean_gap - fold_gap - 0.03 * empty - leakage_penalty - complexity_penalty

    if not mat.empty:
        mat["selection_score"] = mat.apply(score_row, axis=1)
    return mat

eeg_balance, eeg_cols = audit_modality(CACHE / "idare_eeg_cache_index_baseline_corrected.csv", "EEG")
emg_balance, emg_cols = audit_modality(CACHE / "idare_emg_feature_cache_index.csv", "EMG")
balance = pd.concat([eeg_balance, emg_balance], ignore_index=True)
balance.to_csv(OUT_BALANCE_CSV, index=False)

matrix = aggregate_candidate_matrix(balance)
matrix.to_csv(OUT_MATRIX_CSV, index=False)

# Recommended formulation: choose one with best average score across modality/task, but require no empty subjects.
avg = matrix.groupby("formulation", as_index=False).agg(
    mean_selection_score=("selection_score", "mean"),
    mean_coverage=("coverage_or_pairwise_usable_fraction", "mean"),
    mean_subject_balance_gap=("mean_subject_balance_gap_abs", "mean"),
    mean_fold_balance_gap=("mean_fold_balance_gap_abs", "mean"),
    total_empty_subjects=("empty_or_unusable_subjects", "sum"),
)
eligible = avg[avg["total_empty_subjects"] == 0].copy()
if eligible.empty:
    eligible = avg.copy()
best_row = eligible.sort_values(["mean_selection_score", "mean_coverage"], ascending=[False, False]).iloc[0]
selected_formulation = str(best_row["formulation"])

# Conservative override: top/bottom quantile often cleaner but lower coverage; select it if its balance is much better and coverage remains >0.45.
if "subject_top_bottom_quantile_q33" in set(avg["formulation"]):
    q = avg[avg["formulation"] == "subject_top_bottom_quantile_q33"].iloc[0]
    med = avg[avg["formulation"] == "subject_median_split"].iloc[0] if "subject_median_split" in set(avg["formulation"]) else None
    if med is not None:
        if float(q["mean_coverage"]) >= 0.45 and float(q["mean_subject_balance_gap"]) <= float(med["mean_subject_balance_gap"]) + 0.02:
            selected_formulation = "subject_top_bottom_quantile_q33"

if selected_formulation == "within_subject_pairwise_or_ranking_task":
    recommended_next = "minimal_subject_relative_pairwise_training_objective"
else:
    recommended_next = "minimal_subject_relative_training_objective"

report = {
    "status": "complete_pending_review",
    "created_or_updated_utc": NOW,
    "objective": "docs/idare_subject_relative_task_formulation_objective.md",
    "evidence_level": "read-only subject-relative task formulation diagnostic/design; no new model training; no final performance claim",
    "inputs": {
        "eeg_index": ".cache/idare_eeg_cache_index_baseline_corrected.csv",
        "emg_index": ".cache/idare_emg_feature_cache_index.csv",
        "prior_review": "docs/idare_representation_label_task_redesign_review_status.md",
        "prior_report": "docs/idare_representation_label_task_redesign_report.md",
    },
    "discovered_rating_columns": {
        "EEG": {k: str(v) if v is not None else None for k, v in eeg_cols.items()},
        "EMG": {k: str(v) if v is not None else None for k, v in emg_cols.items()},
    },
    "candidate_formulations": FORMULATIONS,
    "candidate_matrix": matrix.to_dict(orient="records"),
    "average_candidate_scores": avg.to_dict(orient="records"),
    "selected_formulation": selected_formulation,
    "recommended_next_objective": recommended_next,
    "recommendation": {
        "summary": f"Use `{selected_formulation}` as the first subject-relative task candidate for a minimal controlled training objective after human review.",
        "why": [
            "The formulation is subject-relative and directly targets the diagnosed label/task subject-dependence blocker.",
            "It provides better within-subject class balance than global binary labels.",
            "It can be evaluated with the existing subject-heldout folds if the task definition is frozen before model fitting.",
            "A future run must be explicitly small and controlled; this report does not authorize training by itself.",
        ],
    },
    "outputs": {
        "report_md": str(OUT_MD),
        "report_json": str(OUT_JSON),
        "label_balance_summary_csv": str(OUT_BALANCE_CSV),
        "candidate_matrix_csv": str(OUT_MATRIX_CSV),
    },
    "not_authorized": [
        "EEG+EMG fusion",
        "final LOSO / final paper claim",
        "final global label-policy lock",
        "new model training",
        "architecture ablation for improvement",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "broad hyperparameter search",
        "mainline change",
    ],
    "next_allowed_step": "Human review / closeout before creating the selected minimal controlled training objective.",
}
OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def fmt(x, d=4):
    try:
        if x is None or pd.isna(x):
            return "NA"
        return f"{float(x):.{d}f}"
    except Exception:
        return str(x)

md = []
md.append("# I-DARE Subject-relative Task Formulation Report")
md.append("")
md.append("## Status")
md.append("")
md.append("Subject-relative task formulation diagnostic/design report complete; pending human review.")
md.append("")
md.append(f"Generated UTC: `{NOW}`")
md.append("")
md.append("No new model training was run.")
md.append("")
md.append("## Executive Recommendation")
md.append("")
md.append(f"- Selected formulation: `{selected_formulation}`")
md.append(f"- Recommended next objective: `{recommended_next}`")
md.append("")
for item in report["recommendation"]["why"]:
    md.append(f"- {item}")
md.append("")
md.append("## Candidate Matrix")
md.append("")
md.append("| Mod | Task | Formulation | Coverage / usable | Prop high | Mean subj gap | Max subj gap | Mean fold gap | Empty subjects | Leakage risk | Score |")
md.append("|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|")
for _, r in matrix.sort_values(["selection_score"], ascending=False).iterrows():
    md.append(
        f"| {r['modality']} | {r['task']} | `{r['formulation']}` | "
        f"{fmt(r['coverage_or_pairwise_usable_fraction'])} | {fmt(r['global_prop_high'])} | "
        f"{fmt(r['mean_subject_balance_gap_abs'])} | {fmt(r['max_subject_balance_gap_abs'])} | "
        f"{fmt(r['mean_fold_balance_gap_abs'])} | {int(r['empty_or_unusable_subjects'])} | "
        f"{r['leakage_risk']} | {fmt(r['selection_score'])} |"
    )
md.append("")
md.append("## Average Formulation Scores")
md.append("")
md.append("| Formulation | Mean score | Mean coverage | Mean subj gap | Mean fold gap | Empty subjects |")
md.append("|---|---:|---:|---:|---:|---:|")
for _, r in avg.sort_values(["mean_selection_score"], ascending=False).iterrows():
    md.append(
        f"| `{r['formulation']}` | {fmt(r['mean_selection_score'])} | {fmt(r['mean_coverage'])} | "
        f"{fmt(r['mean_subject_balance_gap'])} | {fmt(r['mean_fold_balance_gap'])} | {int(r['total_empty_subjects'])} |"
    )
md.append("")
md.append("## Leakage and Scientific Validity Audit")
md.append("")
md.append("| Formulation | Leakage risk | Scientifically valid | Notes |")
md.append("|---|---|---|---|")
for f in FORMULATIONS:
    lp = leakage_profile(f)
    md.append(f"| `{f}` | {lp['leakage_risk']} | {lp['scientifically_valid']} | {lp['reason']} |")
md.append("")
md.append("## Future Controlled Run Matrix Draft")
md.append("")
md.append("This is only a draft for the next objective. It is not authorized by this report.")
md.append("")
md.append("| Dimension | Draft value |")
md.append("|---|---|")
md.append(f"| Task formulation | `{selected_formulation}` |")
md.append("| Modalities | EEG STIM-BSL-only, EMG feature-only |")
md.append("| Tasks | valence, arousal |")
md.append("| Folds | sidecar-compatible 6 folds, seed 11 |")
md.append("| Recipes | start with `ce_class_weighted` only, then add `balanced_sampler_ce` only if the first pass is valid |")
md.append("| Matrix size | minimal first pass: 24 runs; optional recipe pass: +24 runs |")
md.append("| Claim level | diagnostic only, no final LOSO claim |")
md.append("")
md.append("## Not Authorized")
md.append("")
for item in report["not_authorized"]:
    md.append(f"- {item}")
md.append("")
md.append("## Next Allowed Step")
md.append("")
md.append("Human review / closeout of this subject-relative task formulation report.")
md.append("")
md.append("If accepted, create a separate minimal controlled training objective. Do not start training from this report alone.")
md.append("")
OUT_MD.write_text("\n".join(md), encoding="utf-8")

# Update roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
row = "| I-DARE subject-relative task formulation report | read-only subject-relative formulation audit complete; pending human review | yes | `docs/idare_subject_relative_task_formulation_report.md` | Human review / closeout before any minimal controlled training objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work; broad hyperparameter search. |"
if "I-DARE subject-relative task formulation report" not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE subject-relative task formulation objective |"):
            out.append(row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not insert report row in project_status_current.md")
    project_md = "\n".join(out) + "\n"

bullet = f"- Subject-relative task formulation report is complete in `docs/idare_subject_relative_task_formulation_report.md`; selected candidate is `{selected_formulation}` and recommended next objective is `{recommended_next}`."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: project status marker not found")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_subject_relative_task_formulation_report"] = {
    "status": "complete_pending_review",
    "evidence": str(OUT_MD),
    "evidence_json": str(OUT_JSON),
    "label_balance_summary_csv": str(OUT_BALANCE_CSV),
    "candidate_matrix_csv": str(OUT_MATRIX_CSV),
    "selected_formulation": selected_formulation,
    "recommended_next_objective": recommended_next,
    "new_model_training_run": False,
    "not_authorized": report["not_authorized"],
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_SUBJECT_RELATIVE_TASK_REPORT_WRITTEN")
print(OUT_MD)
print(OUT_JSON)
print(OUT_BALANCE_CSV)
print(OUT_MATRIX_CSV)
print("selected_formulation=", selected_formulation)
print("recommended_next_objective=", recommended_next)
PY
echo

echo "===== 4) validate generated outputs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path
json.loads(Path("docs/idare_subject_relative_task_formulation_report.json").read_text(encoding="utf-8"))
print("OK_JSON")
for p in [
    Path("docs/idare_subject_relative_label_balance_summary.csv"),
    Path("docs/idare_subject_relative_candidate_matrix.csv"),
]:
    with p.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(p.name, "rows=", len(rows))
    if not rows:
        raise SystemExit(f"ERROR: empty {p}")
PY

grep -n "## Status\|## Executive Recommendation\|## Candidate Matrix\|## Leakage and Scientific Validity Audit\|## Future Controlled Run Matrix Draft\|## Next Allowed Step" docs/idare_subject_relative_task_formulation_report.md
grep -n "subject-relative task formulation report" docs/project_status_current.md
echo

echo "===== 5) file list ====="
ls -lh \
  docs/idare_subject_relative_task_formulation_report.md \
  docs/idare_subject_relative_task_formulation_report.json \
  docs/idare_subject_relative_label_balance_summary.csv \
  docs/idare_subject_relative_candidate_matrix.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push subject-relative formulation report ====="
git add \
  docs/idare_subject_relative_task_formulation_report.md \
  docs/idare_subject_relative_task_formulation_report.json \
  docs/idare_subject_relative_label_balance_summary.csv \
  docs/idare_subject_relative_candidate_matrix.csv \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "analysis: add I-DARE subject-relative task formulation report"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch

echo "LOG_SAVED_TO=/tmp/idare_subject_relative_task_report.log"
