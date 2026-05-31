#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import os
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path.cwd()
DOCS = ROOT / "docs"
ROCA = DOCS / "roca"
OUT_PREFIX = "idare_06a1z_prior_experiment_map_and_root_cause_autopsy_current"

TEXT_EXTS = {".md", ".py", ".sh", ".txt"}
TABLE_EXTS = {".csv", ".tsv"}
JSON_EXTS = {".json"}

SEARCH_ROOTS = [DOCS, ROOT / "scripts"]
SKIP_PARTS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", ".ipynb_checkpoints",
}

EXPERIMENT_TERMS = [
    "augmentation", "augment", "aug", "augmentation_config",
    "oracle", "ablation", "arch_ablation", "architecture", "a8_vs_a0",
    "deep", "cnn", "tcn", "transformer", "attention", "mha", "moe",
    "eegnet", "gru", "lstm", "temporal", "representation", "embedding",
    "residual", "deviation", "high_disagreement", "subject", "loso",
    "domain", "adaptation", "calibration", "fewshot", "few-shot",
    "macro_f1", "f1", "accuracy", "acc", "auc", "rmse", "pearson", "ccc",
    "label_policy", "pairwise", "stimulus_only", "emg_only", "bandpower",
]

METRIC_PATTERNS = [
    "rmse", "mae", "mse", "lift", "pearson", "spearman", "ccc",
    "auc", "accuracy", "acc", "macro_f1", "f1", "loss",
    "win_margin", "wins", "losses", "delta", "improvement",
]


def safe_float(x: Any) -> float | None:
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None


def jsonable(obj: Any) -> Any:
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        return None if math.isnan(v) or math.isinf(v) else v
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    if isinstance(obj, pd.Series):
        return obj.to_dict()
    if isinstance(obj, dict):
        return {str(k): jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    return obj


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        seen: list[str] = []
        for r in rows:
            for k in r.keys():
                if k not in seen:
                    seen.append(k)
        columns = seen
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: jsonable(r.get(k)) for k in columns})


def md_table(rows: list[dict[str, Any]], max_rows: int = 30) -> str:
    if not rows:
        return "_No rows._\n"
    rows = rows[:max_rows]
    cols: list[str] = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    def fmt(v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, float):
            if math.isnan(v) or math.isinf(v):
                return ""
            return f"{v:.6g}"
        s = str(v).replace("|", "\\|").replace("\n", " ")
        return s[:240] + ("..." if len(s) > 240 else "")
    out = []
    out.append("| " + " | ".join(cols) + " |")
    out.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for r in rows:
        out.append("| " + " | ".join(fmt(r.get(c)) for c in cols) + " |")
    return "\n".join(out) + "\n"


def text_snippets(path: Path, terms: list[str], max_lines: int = 8, max_bytes: int = 1_500_000) -> list[str]:
    try:
        raw = path.read_bytes()
    except Exception:
        return []
    if len(raw) > max_bytes and path.suffix.lower() not in {".csv", ".tsv"}:
        raw = raw[:max_bytes]
    try:
        text = raw.decode("utf-8", errors="ignore")
    except Exception:
        return []
    lines = text.splitlines()
    hits: list[str] = []
    low_terms = [t.lower() for t in terms]
    for i, line in enumerate(lines, start=1):
        ll = line.lower()
        if any(t in ll for t in low_terms):
            clean = re.sub(r"\s+", " ", line).strip()
            hits.append(f"L{i}: {clean[:260]}")
            if len(hits) >= max_lines:
                break
    return hits


def estimate_rows_csv(path: Path) -> int | None:
    try:
        with path.open("rb") as f:
            return max(0, sum(1 for _ in f) - 1)
    except Exception:
        return None


def iter_candidate_files() -> list[Path]:
    files: list[Path] = []
    for base in SEARCH_ROOTS:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if any(part in SKIP_PARTS for part in p.parts):
                continue
            ext = p.suffix.lower()
            if ext not in TEXT_EXTS | TABLE_EXTS | JSON_EXTS:
                continue
            # Keep metric/provenance files, but avoid huge prediction tables unless they are named as known prior candidates.
            files.append(p)
    return sorted(files)


def score_file(path: Path) -> dict[str, Any]:
    rel = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    name_low = rel.lower()
    score = 0
    matched: list[str] = []
    for term in EXPERIMENT_TERMS:
        if term.lower() in name_low:
            score += 3
            matched.append(term)
    snippets = text_snippets(path, EXPERIMENT_TERMS)
    for snip in snippets:
        low = snip.lower()
        for term in EXPERIMENT_TERMS:
            if term.lower() in low and term not in matched:
                score += 1
                matched.append(term)
    size_mb = path.stat().st_size / (1024 * 1024)
    kind = path.suffix.lower().lstrip(".")
    rows = estimate_rows_csv(path) if path.suffix.lower() in TABLE_EXTS else None
    return {
        "path": rel,
        "extension": path.suffix.lower(),
        "size_mb": round(size_mb, 4),
        "kind": kind,
        "score": score,
        "matched_terms": ",".join(sorted(set(matched))),
        "estimated_rows": rows,
        "snippets": " || ".join(snippets),
    }


def metric_columns(cols: list[str]) -> list[str]:
    out = []
    for c in cols:
        low = c.lower()
        if any(p in low for p in METRIC_PATTERNS) or low in {"decision", "status", "target", "task", "model", "block", "feature_block", "augmentation_config", "arch_config"}:
            out.append(c)
    return out


def summarize_csv(path: Path, rel: str, max_size_mb: float = 80.0) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        rows.append({
            "path": rel,
            "summary_type": "csv_skipped_large",
            "size_mb": size_mb,
            "note": f"Skipped full read because size_mb>{max_size_mb}",
        })
        return rows
    try:
        df = pd.read_csv(path, low_memory=False)
    except Exception as e:
        return [{"path": rel, "summary_type": "csv_read_failed", "error": repr(e), "size_mb": size_mb}]
    mcols = metric_columns(list(df.columns))
    base = {
        "path": rel,
        "summary_type": "csv_overview",
        "rows": int(len(df)),
        "cols": int(len(df.columns)),
        "metric_like_columns": ",".join(mcols[:50]),
        "size_mb": size_mb,
    }
    # Decisions/statuses.
    decision_bits = []
    for c in df.columns:
        if c.lower() in {"decision", "status", "final_status", "representation_gate_decision"} or "decision" in c.lower():
            vals = [str(v) for v in df[c].dropna().unique()[:8]]
            if vals:
                decision_bits.append(f"{c}={';'.join(vals)}")
    base["decision_values"] = " | ".join(decision_bits[:8])
    rows.append(base)

    # Numeric metric ranges.
    numeric_summary: dict[str, Any] = {"path": rel, "summary_type": "numeric_metric_ranges"}
    any_num = False
    for c in mcols:
        if c not in df.columns:
            continue
        vals = pd.to_numeric(df[c], errors="coerce")
        if vals.notna().sum() == 0:
            continue
        any_num = True
        numeric_summary[f"{c}_min"] = float(vals.min())
        numeric_summary[f"{c}_max"] = float(vals.max())
        numeric_summary[f"{c}_mean"] = float(vals.mean())
    if any_num:
        rows.append(numeric_summary)

    # Prediction table metric computation.
    lower_cols = {c.lower(): c for c in df.columns}
    y_true_candidates = ["y_true_score", "y_true", "label", "arousal_score", "valence_score"]
    pred_candidates = ["y_pred_score_clipped", "y_pred_score", "y_pred", "prediction", "prob1"]
    true_col = next((lower_cols[c] for c in y_true_candidates if c in lower_cols), None)
    pred_col = next((lower_cols[c] for c in pred_candidates if c in lower_cols), None)
    if true_col and pred_col:
        y = pd.to_numeric(df[true_col], errors="coerce")
        p = pd.to_numeric(df[pred_col], errors="coerce")
        mask = y.notna() & p.notna()
        if mask.sum() > 0:
            rmse = float(np.sqrt(np.mean((y[mask].to_numpy() - p[mask].to_numpy()) ** 2)))
            corr = np.corrcoef(y[mask].to_numpy(), p[mask].to_numpy())[0, 1] if mask.sum() > 2 else np.nan
            rows.append({
                "path": rel,
                "summary_type": "computed_prediction_metric",
                "target_column": true_col,
                "prediction_column": pred_col,
                "n": int(mask.sum()),
                "computed_rmse": rmse,
                "computed_pearson": None if np.isnan(corr) else float(corr),
            })

    # Residual prediction table metric computation.
    resid_true_candidates = ["true_deviation_from_train_stimulus_mean", "true_deviation", "residual", "y_true_deviation"]
    resid_pred_candidates = ["y_pred_deviation_clipped", "y_pred_deviation", "physio_residual_pred", "y_pred_residual"]
    rt_col = next((lower_cols[c] for c in resid_true_candidates if c in lower_cols), None)
    rp_col = next((lower_cols[c] for c in resid_pred_candidates if c in lower_cols), None)
    if rt_col and rp_col:
        rt = pd.to_numeric(df[rt_col], errors="coerce")
        rp = pd.to_numeric(df[rp_col], errors="coerce")
        mask = rt.notna() & rp.notna()
        if mask.sum() > 0:
            rmse_model = float(np.sqrt(np.mean((rt[mask].to_numpy() - rp[mask].to_numpy()) ** 2)))
            rmse_zero = float(np.sqrt(np.mean((rt[mask].to_numpy()) ** 2)))
            corr = np.corrcoef(rt[mask].to_numpy(), rp[mask].to_numpy())[0, 1] if mask.sum() > 2 else np.nan
            rows.append({
                "path": rel,
                "summary_type": "computed_residual_metric",
                "residual_true_column": rt_col,
                "residual_pred_column": rp_col,
                "n": int(mask.sum()),
                "zero_residual_rmse": rmse_zero,
                "model_residual_rmse": rmse_model,
                "lift_vs_zero_residual_rmse": rmse_zero - rmse_model,
                "residual_pearson": None if np.isnan(corr) else float(corr),
            })

    # Augmentation/architecture group summaries for oracle/deep prediction files.
    group_cols = [c for c in ["target", "task", "augmentation_config", "arch_config", "model", "feature_block", "block"] if c in df.columns]
    if group_cols and (("augmentation_config" in df.columns) or ("arch_config" in df.columns)):
        if rt_col and rp_col:
            sub = df.copy()
            sub["_rt"] = pd.to_numeric(sub[rt_col], errors="coerce")
            sub["_rp"] = pd.to_numeric(sub[rp_col], errors="coerce")
            sub = sub[sub["_rt"].notna() & sub["_rp"].notna()]
            if len(sub):
                grouped = []
                for keys, g in sub.groupby(group_cols, dropna=False):
                    if not isinstance(keys, tuple):
                        keys = (keys,)
                    rt = g["_rt"].to_numpy()
                    rp = g["_rp"].to_numpy()
                    rmse_model = float(np.sqrt(np.mean((rt - rp) ** 2)))
                    rmse_zero = float(np.sqrt(np.mean(rt ** 2)))
                    rec = {
                        "path": rel,
                        "summary_type": "augmentation_or_arch_group_residual_metric",
                        "n": int(len(g)),
                        "zero_residual_rmse": rmse_zero,
                        "model_residual_rmse": rmse_model,
                        "lift_vs_zero_residual_rmse": rmse_zero - rmse_model,
                    }
                    for col, val in zip(group_cols, keys):
                        rec[col] = val
                    grouped.append(rec)
                grouped = sorted(grouped, key=lambda r: r.get("lift_vs_zero_residual_rmse", -999), reverse=True)
                rows.extend(grouped[:25])
        elif true_col and pred_col:
            sub = df.copy()
            sub["_y"] = pd.to_numeric(sub[true_col], errors="coerce")
            sub["_p"] = pd.to_numeric(sub[pred_col], errors="coerce")
            sub = sub[sub["_y"].notna() & sub["_p"].notna()]
            if len(sub):
                grouped = []
                for keys, g in sub.groupby(group_cols, dropna=False):
                    if not isinstance(keys, tuple):
                        keys = (keys,)
                    y = g["_y"].to_numpy()
                    p = g["_p"].to_numpy()
                    rec = {
                        "path": rel,
                        "summary_type": "augmentation_or_arch_group_score_metric",
                        "n": int(len(g)),
                        "score_rmse": float(np.sqrt(np.mean((y - p) ** 2))),
                    }
                    for col, val in zip(group_cols, keys):
                        rec[col] = val
                    grouped.append(rec)
                grouped = sorted(grouped, key=lambda r: r.get("score_rmse", 999))
                rows.extend(grouped[:25])
    return rows


def flatten_json_metrics(obj: Any, prefix: str = "", out: list[tuple[str, Any]] | None = None, limit: int = 4000) -> list[tuple[str, Any]]:
    if out is None:
        out = []
    if len(out) >= limit:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten_json_metrics(v, f"{prefix}.{k}" if prefix else str(k), out, limit)
            if len(out) >= limit:
                break
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:200]):
            flatten_json_metrics(v, f"{prefix}[{i}]", out, limit)
            if len(out) >= limit:
                break
    else:
        low = prefix.lower()
        if any(p in low for p in METRIC_PATTERNS) or any(p in low for p in ["decision", "status", "target", "model", "augmentation", "architecture"]):
            out.append((prefix, obj))
    return out


def summarize_json(path: Path, rel: str, max_size_mb: float = 30.0) -> list[dict[str, Any]]:
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        return [{"path": rel, "summary_type": "json_skipped_large", "size_mb": size_mb}]
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [{"path": rel, "summary_type": "json_read_failed", "error": repr(e), "size_mb": size_mb}]
    flat = flatten_json_metrics(obj)
    rows = [{
        "path": rel,
        "summary_type": "json_overview",
        "size_mb": size_mb,
        "metric_like_entries": len(flat),
        "top_metric_paths": " | ".join([f"{k}={str(v)[:80]}" for k, v in flat[:20]]),
    }]
    return rows


def load_csv_optional(path: Path) -> pd.DataFrame:
    try:
        if path.exists():
            return pd.read_csv(path)
    except Exception:
        pass
    return pd.DataFrame()


def corr_safe(a: np.ndarray, b: np.ndarray) -> float | None:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 3:
        return None
    if np.nanstd(a[m]) <= 1e-12 or np.nanstd(b[m]) <= 1e-12:
        return None
    return float(np.corrcoef(a[m], b[m])[0, 1])


def residual_identifiability() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    index_candidates = [
        ROOT / ".cache" / "idare_eeg_cache_index_baseline_corrected.csv",
        ROOT / ".cache" / "idare_eeg_cache_index.csv",
    ]
    index_path = next((p for p in index_candidates if p.exists()), None)
    if index_path is None:
        return ([{
            "target": "NA",
            "diagnostic": "missing_index",
            "finding": "No I-DARE EEG cache index found under .cache.",
        }], [], [])

    df = pd.read_csv(index_path)
    lower = {c.lower(): c for c in df.columns}
    subj_col = next((lower[c] for c in ["subject_id", "subject", "participant_id", "test_subject"] if c in lower), None)
    stim_col = next((lower[c] for c in ["stimulus_id", "stimulus", "trial_id"] if c in lower), None)
    if not subj_col or not stim_col:
        return ([{
            "target": "NA",
            "diagnostic": "missing_columns",
            "finding": f"Index exists but subject/stimulus columns were not found. columns={list(df.columns)}",
        }], [], [])

    target_cols = [c for c in ["arousal_score", "valence_score"] if c in df.columns]
    if not target_cols:
        target_cols = [c for c in df.columns if c.lower() in {"arousal", "valence"}]

    ident_rows: list[dict[str, Any]] = []
    calib_rows: list[dict[str, Any]] = []
    reliability_rows: list[dict[str, Any]] = []

    rng = np.random.default_rng(20260530)

    for target_col in target_cols:
        work = df[[subj_col, stim_col, target_col]].copy()
        work = work.dropna()
        work[subj_col] = work[subj_col].astype(str)
        work[stim_col] = work[stim_col].astype(str)
        work[target_col] = pd.to_numeric(work[target_col], errors="coerce")
        work = work.dropna()
        if work.empty:
            continue

        y = work[target_col].to_numpy(dtype=float)
        stim_sum = work.groupby(stim_col)[target_col].transform("sum").to_numpy(dtype=float)
        stim_count = work.groupby(stim_col)[target_col].transform("count").to_numpy(dtype=float)
        stim_prior_loso = np.where(stim_count > 1, (stim_sum - y) / (stim_count - 1), np.nan)
        valid = np.isfinite(stim_prior_loso)
        w = work.loc[valid].copy()
        yv = y[valid]
        prior = stim_prior_loso[valid]
        resid = yv - prior
        w["_resid"] = resid

        zero_rmse = float(np.sqrt(np.mean(resid ** 2)))
        subj_sum = w.groupby(subj_col)["_resid"].transform("sum").to_numpy(dtype=float)
        subj_count = w.groupby(subj_col)["_resid"].transform("count").to_numpy(dtype=float)
        subj_mean_loo = np.where(subj_count > 1, (subj_sum - resid) / (subj_count - 1), 0.0)
        subj_loo_rmse = float(np.sqrt(np.mean((resid - subj_mean_loo) ** 2)))
        subj_lift = zero_rmse - subj_loo_rmse

        # One-hot oracle for subject + stimulus effects on residual.
        subjects = sorted(w[subj_col].unique())
        stimuli = sorted(w[stim_col].unique())
        s_map = {v: i for i, v in enumerate(subjects)}
        t_map = {v: i for i, v in enumerate(stimuli)}
        n = len(w)
        # Drop first subject/stimulus dummy to avoid singular intercept duplication.
        X = np.ones((n, 1 + max(0, len(subjects) - 1) + max(0, len(stimuli) - 1)), dtype=float)
        for i, v in enumerate(w[subj_col].to_numpy()):
            j = s_map[v]
            if j > 0:
                X[i, j] = 1.0
        offset = 1 + max(0, len(subjects) - 1)
        for i, v in enumerate(w[stim_col].to_numpy()):
            j = t_map[v]
            if j > 0:
                X[i, offset + j - 1] = 1.0
        try:
            beta, *_ = np.linalg.lstsq(X, resid, rcond=None)
            pred_add = X @ beta
            add_rmse = float(np.sqrt(np.mean((resid - pred_add) ** 2)))
            add_lift = zero_rmse - add_rmse
        except Exception:
            add_rmse = np.nan
            add_lift = np.nan

        # Split-half reliability: stimulus residual pattern shared across subjects.
        mat = w.pivot_table(index=subj_col, columns=stim_col, values="_resid", aggfunc="mean")
        subj_values = np.array(mat.index)
        stim_values = np.array(mat.columns)
        stim_corrs = []
        subj_corrs = []
        for _ in range(300):
            if len(subj_values) >= 4:
                perm = rng.permutation(len(subj_values))
                a_idx = perm[: len(perm)//2]
                b_idx = perm[len(perm)//2 :]
                a = mat.iloc[a_idx].mean(axis=0).to_numpy()
                b = mat.iloc[b_idx].mean(axis=0).to_numpy()
                c = corr_safe(a, b)
                if c is not None:
                    stim_corrs.append(c)
            if len(stim_values) >= 6:
                perm = rng.permutation(len(stim_values))
                a_cols = perm[: len(perm)//2]
                b_cols = perm[len(perm)//2 :]
                a = mat.iloc[:, a_cols].mean(axis=1).to_numpy()
                b = mat.iloc[:, b_cols].mean(axis=1).to_numpy()
                c = corr_safe(a, b)
                if c is not None:
                    subj_corrs.append(c)

        stim_reliab = float(np.nanmean(stim_corrs)) if stim_corrs else np.nan
        subj_reliab = float(np.nanmean(subj_corrs)) if subj_corrs else np.nan

        ident_rows.append({
            "target": target_col.replace("_score", ""),
            "n_trials": int(len(w)),
            "n_subjects": int(len(subjects)),
            "n_stimuli": int(len(stimuli)),
            "zero_residual_rmse_after_loso_stimulus_prior": zero_rmse,
            "leave_one_trial_subject_mean_oracle_rmse": subj_loo_rmse,
            "subject_mean_oracle_lift_vs_zero": subj_lift,
            "subject_plus_stimulus_additive_oracle_rmse": add_rmse,
            "subject_plus_stimulus_additive_oracle_lift_vs_zero": add_lift,
            "split_half_shared_stimulus_residual_reliability_mean_r": stim_reliab,
            "split_half_subject_style_reliability_mean_r": subj_reliab,
            "interpretation": (
                "subject_style_dominant_or_calibration_needed"
                if (np.isfinite(subj_reliab) and subj_reliab > 0.25 and subj_lift > 0.03)
                else "weak_or_mixed_identifiability"
            ),
        })

        # k-shot subject-mean calibration oracle.
        for k in [1, 2, 4, 8, 16]:
            rmses = []
            lifts = []
            eval_counts = []
            for rep in range(300):
                pred_rows = []
                true_rows = []
                for subj, g in w.groupby(subj_col):
                    if len(g) <= k:
                        continue
                    idx = np.array(g.index)
                    cal = rng.choice(idx, size=k, replace=False)
                    eval_idx = np.array([ii for ii in idx if ii not in set(cal)])
                    if len(eval_idx) == 0:
                        continue
                    cal_mean = float(w.loc[cal, "_resid"].mean())
                    true = w.loc[eval_idx, "_resid"].to_numpy(dtype=float)
                    pred = np.full_like(true, cal_mean)
                    true_rows.append(true)
                    pred_rows.append(pred)
                if true_rows:
                    true_all = np.concatenate(true_rows)
                    pred_all = np.concatenate(pred_rows)
                    rmse = float(np.sqrt(np.mean((true_all - pred_all) ** 2)))
                    zero = float(np.sqrt(np.mean(true_all ** 2)))
                    rmses.append(rmse)
                    lifts.append(zero - rmse)
                    eval_counts.append(len(true_all))
            calib_rows.append({
                "target": target_col.replace("_score", ""),
                "k_calibration_trials": k,
                "mean_eval_n": float(np.mean(eval_counts)) if eval_counts else None,
                "oracle_kshot_subject_mean_rmse_mean": float(np.mean(rmses)) if rmses else None,
                "oracle_kshot_subject_mean_lift_vs_zero_mean": float(np.mean(lifts)) if lifts else None,
                "oracle_kshot_subject_mean_lift_p10": float(np.percentile(lifts, 10)) if lifts else None,
                "oracle_kshot_subject_mean_lift_p90": float(np.percentile(lifts, 90)) if lifts else None,
            })

        reliability_rows.append({
            "target": target_col.replace("_score", ""),
            "reliability_item": "shared_stimulus_residual_pattern_across_subjects",
            "mean_split_half_r": stim_reliab,
            "n_repeats": len(stim_corrs),
            "interpretation": "high means residual has cross-subject stimulus structure; low means residual is mostly idiosyncratic/noisy",
        })
        reliability_rows.append({
            "target": target_col.replace("_score", ""),
            "reliability_item": "subject_style_pattern_across_stimulus_halves",
            "mean_split_half_r": subj_reliab,
            "n_repeats": len(subj_corrs),
            "interpretation": "high means subject calibration can be structurally useful",
        })

    return ident_rows, calib_rows, reliability_rows


def collect_prior_and_metric_summaries() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    candidates = [score_file(p) for p in iter_candidate_files()]
    candidates = [r for r in candidates if r["score"] > 0]
    candidates = sorted(candidates, key=lambda r: (r["score"], r["size_mb"]), reverse=True)

    metric_rows: list[dict[str, Any]] = []
    augmentation_rows: list[dict[str, Any]] = []
    for r in candidates[:220]:
        p = ROOT / r["path"]
        ext = p.suffix.lower()
        if ext in TABLE_EXTS:
            summaries = summarize_csv(p, r["path"])
            metric_rows.extend(summaries)
            for s in summaries:
                blob = json.dumps(jsonable(s), ensure_ascii=False).lower()
                if "augmentation" in blob or "aug" in blob or "arch_config" in blob or "oracle" in blob:
                    augmentation_rows.append(s)
        elif ext in JSON_EXTS:
            summaries = summarize_json(p, r["path"])
            metric_rows.extend(summaries)
            for s in summaries:
                blob = json.dumps(jsonable(s), ensure_ascii=False).lower()
                if "augmentation" in blob or "aug" in blob or "arch" in blob or "oracle" in blob:
                    augmentation_rows.append(s)
    return candidates, metric_rows, augmentation_rows


def value_from_csv(path: Path, col: str, target: str | None = None) -> float | None:
    df = load_csv_optional(path)
    if df.empty or col not in df.columns:
        return None
    if target is not None and "target" in df.columns:
        sub = df[df["target"].astype(str).str.lower() == target.lower()]
        if not sub.empty:
            return safe_float(sub.iloc[0][col])
    return safe_float(df.iloc[0][col])


def build_root_cause_table(
    candidates: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    augmentation_rows: list[dict[str, Any]],
    ident_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    split_x = load_csv_optional(ROCA / "idare_06a1x_loso_generalization_failure_autopsy_current_split_control_metrics.csv")
    split_y = load_csv_optional(ROCA / "idare_06a1y_split_control_deep_learning_probe_current_split_summary.csv")
    prev_deep = load_csv_optional(ROCA / "idare_06a1_previous_model_deep_residual_probe_current_decision_table.csv")
    conf = load_csv_optional(ROCA / "idare_high_disagreement_direct_deviation_confirmatory_stats_current_verdict.csv")

    def split_lift(df: pd.DataFrame, split_name: str) -> float | None:
        if df.empty or "split" not in df.columns:
            return None
        sub = df[df["split"].astype(str) == split_name]
        if sub.empty:
            return None
        col = "lift_vs_zero_high" if "lift_vs_zero_high" in sub.columns else "pooled_lift_vs_zero_residual_rmse"
        if col not in sub.columns:
            return None
        return safe_float(sub.iloc[0][col])

    x_random = split_lift(split_x, "random_trial_kfold_subjects_overlap")
    x_loso = split_lift(split_x, "loso_leave_one_subject_out")
    y_random = split_lift(split_y, "random_trial_kfold_subjects_overlap")
    y_within = split_lift(split_y, "within_subject_trial_kfold_subjects_overlap")
    y_loso = split_lift(split_y, "loso_leave_one_subject_out")
    y_losto = split_lift(split_y, "leave_one_stimulus_out")

    fixed_lift = None
    if not conf.empty and "pooled_lift_vs_zero_residual_rmse" in conf.columns:
        sub = conf[conf.get("target", "").astype(str).str.lower() == "arousal"] if "target" in conf.columns else conf
        if not sub.empty:
            fixed_lift = safe_float(sub.iloc[0]["pooled_lift_vs_zero_residual_rmse"])

    prev_deep_lift = None
    if not prev_deep.empty and "deep_lift_vs_zero_residual_rmse_high" in prev_deep.columns:
        prev_deep_lift = safe_float(prev_deep.iloc[0]["deep_lift_vs_zero_residual_rmse_high"])

    rows.append({
        "root_cause_hypothesis": "H1_subject_domain_shift_is_real_for_EEG_summary_features",
        "evidence": f"06a1x summary-feature split control: random_overlap_lift={x_random}, loso_lift={x_loso}.",
        "current_weight": (
            "strong" if x_random is not None and x_loso is not None and x_random > 0.15 and x_loso < 0.08
            else "mixed_or_missing"
        ),
        "interpretation": "Some EEG summary information can predict residuals when subject/stimulus distributions are easier, but much of that signal does not transfer cleanly to held-out subjects.",
        "next_action": "Run subject-normalization/domain-adaptation ablations only after checking residual identifiability; avoid generic larger CNN search.",
    })

    rows.append({
        "root_cause_hypothesis": "H2_previous_deep_encoder_training_or_capacity_did_not_recover_even_easy_signal",
        "evidence": f"06a1 previous deep lift={prev_deep_lift}; 06a1y deep random={y_random}, within={y_within}, LOSO={y_loso}, LOSTO={y_losto}; fixed EEG-bandpower reference={fixed_lift}.",
        "current_weight": (
            "strong" if y_random is not None and y_within is not None and max(y_random, y_within) < 0.03
            else "mixed"
        ),
        "interpretation": "The earlier deep route is not only blocked by LOSO; under this residual target it barely beats zero even with subject overlap.",
        "next_action": "If continuing deep learning, first reproduce simple EEG-bandpower/summary gains inside the neural pipeline; otherwise deep architecture search is unanchored.",
    })

    aug_count = len(augmentation_rows)
    aug_best = None
    for r in augmentation_rows:
        for key in ["lift_vs_zero_residual_rmse", "computed_rmse", "score_rmse"]:
            if key in r and safe_float(r.get(key)) is not None:
                v = safe_float(r.get(key))
                if aug_best is None:
                    aug_best = (key, v, r.get("path"))
                elif key == "lift_vs_zero_residual_rmse" and v is not None and v > aug_best[1]:
                    aug_best = (key, v, r.get("path"))
    rows.append({
        "root_cause_hypothesis": "H3_prior_augmentation_helped_some_old_tasks_but_may_not_solve_current_residual_LOSO_gate",
        "evidence": f"Found {aug_count} augmentation/oracle/architecture-related summary rows. Best detected metric={aug_best}.",
        "current_weight": "needs_manual_review" if aug_count else "missing_evidence",
        "interpretation": "Prior augmentation may have improved earlier binary/oracle/architecture tasks, but this script separates those from the current high-disagreement residual LOSO gate.",
        "next_action": "Inspect augmentation_evidence table; if a prior augmentation truly improved residual LOSO, rerun it under 05ajb/06a1y gates.",
    })

    ar_ident = next((r for r in ident_rows if str(r.get("target")).lower() == "arousal"), None)
    if ar_ident:
        rows.append({
            "root_cause_hypothesis": "H4_residual_identifiability_or_subject_style_bound",
            "evidence": (
                f"arousal zero_residual_rmse={ar_ident.get('zero_residual_rmse_after_loso_stimulus_prior')}, "
                f"subject_mean_lift={ar_ident.get('subject_mean_oracle_lift_vs_zero')}, "
                f"stimulus_residual_reliability={ar_ident.get('split_half_shared_stimulus_residual_reliability_mean_r')}, "
                f"subject_style_reliability={ar_ident.get('split_half_subject_style_reliability_mean_r')}."
            ),
            "current_weight": "computed",
            "interpretation": "This tells us whether more model capacity can realistically help or whether calibration/label noise dominates.",
            "next_action": "Use the identifiability table as the gate for 06a3/06a4: if shared residual reliability is low, stop global residual decoding and focus on calibration or task reformulation.",
        })

    rows.append({
        "root_cause_hypothesis": "current_best_working_summary",
        "evidence": "Fixed EEG-bandpower has a confirmed but weak arousal high-disagreement residual signal; previous deep model and split-control deep model do not beat it.",
        "current_weight": "high",
        "interpretation": "The main problem is probably not one missing fancy architecture. It is a combination of weak residual identifiability, subject style/domain shift, and a deep pipeline that has not yet reproduced the simple fixed-feature signal.",
        "next_action": "Commit this map, then run a focused 06a3 identifiability/noise-bound report and a 06a4 normalization/domain-adaptation ablation, not another unconstrained model.",
    })

    return rows


def main() -> None:
    ROCA.mkdir(parents=True, exist_ok=True)

    print("[INFO] Scanning prior experiment files, metrics, augmentation evidence...")
    candidates, metric_rows, augmentation_rows = collect_prior_and_metric_summaries()

    print("[INFO] Running residual identifiability / label-noise bound autopsy...")
    ident_rows, calib_rows, reliability_rows = residual_identifiability()

    root_rows = build_root_cause_table(candidates, metric_rows, augmentation_rows, ident_rows)

    next_steps = [
        {
            "priority": 1,
            "step": "06a3",
            "title": "Residual identifiability and label-noise bound",
            "purpose": "Formalize whether arousal/valence residuals have repeatable structure strong enough for physiology learning.",
            "success_condition": "Shared residual reliability and oracle bounds justify another modeling step; otherwise stop blind deep search.",
        },
        {
            "priority": 2,
            "step": "06a4",
            "title": "Subject-normalization and domain-adaptation ablation",
            "purpose": "Test whether per-subject EEG normalization, CORAL/MMD-style alignment, or k-shot context closes the 06a1x overlap-vs-LOSO gap.",
            "success_condition": "LOSO high-disagreement arousal improves beyond fixed EEG-bandpower or cleanly explains why it cannot.",
        },
        {
            "priority": 3,
            "step": "06a5",
            "title": "Augmentation rerun under current residual gates",
            "purpose": "Only if prior augmentation evidence looks real, rerun the best old augmentation under 05ajb/06a1y residual gates.",
            "success_condition": "Augmentation beats zero residual and fixed EEG-bandpower under subject-held-out gates.",
        },
    ]

    # Write tables.
    write_csv(ROCA / f"{OUT_PREFIX}_candidate_experiment_files.csv", candidates)
    write_csv(ROCA / f"{OUT_PREFIX}_metric_summaries.csv", metric_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_augmentation_evidence.csv", augmentation_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_residual_identifiability.csv", ident_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_kshot_subject_mean_oracle.csv", calib_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_split_half_reliability.csv", reliability_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_root_cause_table.csv", root_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_next_steps.csv", next_steps)

    payload = {
        "title": "I-DARE prior experiment map and root-cause autopsy",
        "candidate_experiment_files": candidates[:80],
        "metric_summaries": metric_rows[:120],
        "augmentation_evidence": augmentation_rows[:80],
        "residual_identifiability": ident_rows,
        "kshot_subject_mean_oracle": calib_rows,
        "split_half_reliability": reliability_rows,
        "root_cause_table": root_rows,
        "next_steps": next_steps,
    }
    (ROCA / f"{OUT_PREFIX}.json").write_text(json.dumps(jsonable(payload), indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("# I-DARE 06a1z Prior Experiment Map and Root-Cause Autopsy\n")
    lines.append("## What this step does\n")
    lines.append("- Scans committed/local docs and scripts for prior deep-learning, augmentation, oracle, ablation, residual, LOSO, and calibration experiments.\n")
    lines.append("- Extracts comparable metric summaries where possible, including augmentation/architecture grouped metrics.\n")
    lines.append("- Runs a residual identifiability / label-noise bound audit from the current I-DARE EEG cache index.\n")
    lines.append("- Combines 06a1x, 06a1y, 06a1, and 05ajb evidence into a root-cause table.\n")

    lines.append("\n## Root-cause table\n")
    lines.append(md_table(root_rows, max_rows=20))

    lines.append("\n## Residual identifiability\n")
    lines.append(md_table(ident_rows, max_rows=20))

    lines.append("\n## K-shot subject-mean oracle\n")
    lines.append(md_table(calib_rows, max_rows=20))

    lines.append("\n## Split-half reliability\n")
    lines.append(md_table(reliability_rows, max_rows=20))

    lines.append("\n## Top prior experiment candidates\n")
    lines.append(md_table(candidates[:25], max_rows=25))

    lines.append("\n## Augmentation / oracle / architecture evidence preview\n")
    lines.append(md_table(augmentation_rows[:25], max_rows=25))

    lines.append("\n## Next steps\n")
    lines.append(md_table(next_steps, max_rows=10))

    (ROCA / f"{OUT_PREFIX}.md").write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 06a1z completed.")
    for suffix in [
        "candidate_experiment_files.csv",
        "metric_summaries.csv",
        "augmentation_evidence.csv",
        "residual_identifiability.csv",
        "kshot_subject_mean_oracle.csv",
        "split_half_reliability.csv",
        "root_cause_table.csv",
        "next_steps.csv",
        "json",
        "md",
    ]:
        if suffix in {"json", "md"}:
            p = ROCA / f"{OUT_PREFIX}.{suffix}"
        else:
            p = ROCA / f"{OUT_PREFIX}_{suffix}"
        print(f"wrote: {p}")

    print("\nRoot-cause table:")
    print(pd.DataFrame(root_rows).to_string(index=False))

    print("\nResidual identifiability:")
    print(pd.DataFrame(ident_rows).to_string(index=False))

    print("\nK-shot oracle:")
    print(pd.DataFrame(calib_rows).to_string(index=False))

    print("\nNext steps:")
    print(pd.DataFrame(next_steps).to_string(index=False))


if __name__ == "__main__":
    main()
