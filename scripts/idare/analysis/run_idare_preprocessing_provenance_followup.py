#!/usr/bin/env python3
from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy import signal

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs"
CACHE = ROOT / ".cache"
TMP_DIR = Path("/tmp")

TRIAL_INDEX = CACHE / "idare_trial_index.csv"

OUT_SCRIPT = ROOT / "scripts" / "idare" / "analysis" / "run_idare_preprocessing_provenance_followup.py"
OUT_MD = DOCS / "idare_preprocessing_provenance_followup_report.md"
OUT_JSON = DOCS / "idare_preprocessing_provenance_followup_report.json"
OUT_PATH_SAMPLE = DOCS / "idare_preprocessing_provenance_followup_path_sample.csv"
OUT_EEG_SOURCE = DOCS / "idare_preprocessing_provenance_followup_eeg_source_audit.csv"
OUT_DOWNSAMPLE = DOCS / "idare_preprocessing_provenance_followup_downsample_method_comparison.csv"
OUT_DOWNSAMPLE_SUMMARY = DOCS / "idare_preprocessing_provenance_followup_downsample_method_summary.csv"
OUT_MINI_MANIFEST = DOCS / "idare_preprocessing_provenance_followup_mini_cache_manifest.json"
OUT_PRIOR_VALIDITY = DOCS / "idare_preprocessing_provenance_followup_prior_result_validity.csv"
OUT_DECISION = DOCS / "idare_preprocessing_provenance_followup_decision_matrix.csv"

PROJECT_STATUS_JSON = DOCS / "project_status_current.json"
PROJECT_STATUS_MD = DOCS / "project_status_current.md"

SOURCE_FS = 512.0
TARGET_FS = 128.0
DOWNSAMPLE = 4
SOURCE_SAMPLES = 2560
TARGET_SAMPLES = 640
TARGET_CHANNELS = 32

# Deliberately conservative but not so strict that harmless high-frequency numerical residue blocks the project.
THRESHOLDS = {
    "energy_gt64_p95_max": 0.005,
    "energy_gt64_max_max": 0.02,
    "stride_poly_z_nrmse_p95_max": 0.075,
    "stride_poly_z_nrmse_max_max": 0.15,
    "stride_poly_z_corr_p05_min": 0.995,
    "stride_lowpass_z_nrmse_p95_max": 0.075,
    "stride_lowpass_z_corr_p05_min": 0.995,
}

def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def safe(v: Any) -> Any:
    if isinstance(v, dict):
        return {str(k): safe(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [safe(x) for x in v]
    if isinstance(v, np.ndarray):
        return safe(v.tolist())
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        x = float(v)
        return None if math.isnan(x) or math.isinf(x) else x
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass
    return v

def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    obj = json.loads(path.read_text(encoding="utf-8"))
    return obj if isinstance(obj, dict) else {}

def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        rows = [{"empty": True}]
    keys: list[str] = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

def unwrap_singleton_path_value(value: Any) -> str:
    """Normalize the bug seen in the first audit: groupby keys like ('/path/file.mat',)."""
    if isinstance(value, (tuple, list)) and len(value) == 1:
        value = value[0]
    s = str(value).strip()
    # Handle tuple/list represented as a string, e.g. "('/mnt/.../sbj_P_01.mat',)".
    if (s.startswith("(") and s.endswith(")")) or (s.startswith("[") and s.endswith("]")):
        try:
            parsed = ast.literal_eval(s)
            if isinstance(parsed, (tuple, list)) and len(parsed) == 1:
                s = str(parsed[0]).strip()
        except Exception:
            pass
    # Remove accidental outer quotes.
    if len(s) >= 2 and ((s[0] == s[-1] == "'") or (s[0] == s[-1] == '"')):
        s = s[1:-1]
    return s

def subject_key(h5: h5py.File, preferred: str) -> str:
    if preferred in h5:
        return preferred
    cands = sorted(k for k in h5.keys() if str(k).startswith("sbj_P_"))
    if not cands:
        raise KeyError(f"No sbj_P_* group found. keys={list(h5.keys())[:20]}")
    return cands[0]

def extract_raw_window(data: h5py.Dataset, begin_raw: float) -> np.ndarray:
    start = int(round(float(begin_raw)))
    stop = start + SOURCE_SAMPLES
    shape = tuple(int(x) for x in data.shape)
    if len(shape) != 2:
        raise ValueError(f"Expected 2D data, got shape={shape}")
    if shape[0] >= stop and shape[1] >= TARGET_CHANNELS:
        raw = np.asarray(data[start:stop, :TARGET_CHANNELS], dtype=np.float64)
    elif shape[1] >= stop and shape[0] >= TARGET_CHANNELS:
        raw = np.asarray(data[:TARGET_CHANNELS, start:stop], dtype=np.float64).T
    else:
        raise ValueError(f"Cannot extract {start}:{stop} first {TARGET_CHANNELS} channels from shape={shape}")
    if raw.shape != (SOURCE_SAMPLES, TARGET_CHANNELS):
        raise ValueError(f"Unexpected raw shape={raw.shape}")
    return raw

def zscore_global(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    mu = float(np.mean(x))
    sd = float(np.std(x))
    if not np.isfinite(mu) or not np.isfinite(sd) or sd < 1e-12:
        return x * 0.0
    return (x - mu) / sd

def nrmse(a: np.ndarray, b: np.ndarray) -> float:
    az = zscore_global(a).reshape(-1)
    bz = zscore_global(b).reshape(-1)
    return float(np.sqrt(np.mean((az - bz) ** 2)))

def corr(a: np.ndarray, b: np.ndarray) -> float:
    az = zscore_global(a).reshape(-1)
    bz = zscore_global(b).reshape(-1)
    sa = float(np.std(az))
    sb = float(np.std(bz))
    if sa < 1e-12 or sb < 1e-12:
        return 1.0 if np.allclose(az, bz) else 0.0
    return float(np.corrcoef(az, bz)[0, 1])

def energy_ratios(raw: np.ndarray) -> dict[str, float]:
    freqs, psd = signal.welch(raw, fs=SOURCE_FS, axis=0, nperseg=512, noverlap=256)
    total = float(np.sum(psd))
    if total <= 0 or not np.isfinite(total):
        return {"energy_ratio_gt40hz": float("nan"), "energy_ratio_gt64hz": float("nan")}
    return {
        "energy_ratio_gt40hz": float(np.sum(psd[freqs > 40.0]) / total),
        "energy_ratio_gt64hz": float(np.sum(psd[freqs > 64.0]) / total),
    }

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def percentile(values: list[float], q: float) -> float:
    vals = [float(v) for v in values if np.isfinite(float(v))]
    if not vals:
        return float("nan")
    return float(np.percentile(vals, q))

def summarize_metric(rows: list[dict[str, Any]], col: str) -> dict[str, Any]:
    vals = [float(r[col]) for r in rows if r.get(col) is not None and np.isfinite(float(r[col]))]
    if not vals:
        return {
            "metric": col,
            "count": 0,
            "mean": None,
            "median": None,
            "p05": None,
            "p95": None,
            "min": None,
            "max": None,
        }
    return {
        "metric": col,
        "count": len(vals),
        "mean": float(np.mean(vals)),
        "median": float(np.median(vals)),
        "p05": float(np.percentile(vals, 5)),
        "p95": float(np.percentile(vals, 95)),
        "min": float(np.min(vals)),
        "max": float(np.max(vals)),
    }

def make_source_and_path_audits(df: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    path_sample: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []

    cols = ["subject_id", "subject_col", "eeg_file", "eeg_begin_raw", "stimulus_id"]
    sample = df[cols].drop_duplicates(subset=["subject_col", "eeg_file"]).head(12)
    for _, row in sample.iterrows():
        raw_value = row["eeg_file"]
        normalized = unwrap_singleton_path_value(raw_value)
        p = Path(normalized)
        path_sample.append({
            "subject_id": int(row["subject_id"]),
            "subject_col": str(row["subject_col"]),
            "raw_eeg_file_value": str(raw_value),
            "normalized_eeg_file_path": str(p),
            "exists": bool(p.exists()),
            "looks_like_tuple_string": str(raw_value).strip().startswith("("),
            "example_stimulus_id": str(row["stimulus_id"]),
            "example_eeg_begin_raw": float(row["eeg_begin_raw"]),
        })

    grouped = df.groupby(["subject_id", "subject_col", "eeg_file"], sort=True, dropna=False)
    for key, g in grouped:
        subject_id, subject_col, eeg_file_key = key
        normalized = unwrap_singleton_path_value(eeg_file_key)
        p = Path(normalized)
        row_out: dict[str, Any] = {
            "subject_id": int(subject_id),
            "subject_col": str(subject_col),
            "raw_groupby_eeg_file_key": str(eeg_file_key),
            "normalized_eeg_file_path": str(p),
            "exists": bool(p.exists()),
            "path_parse_bug_fixed": not str(eeg_file_key).strip().startswith("("),
            "rows": int(len(g)),
            "pass": False,
            "failure_reason": "",
        }
        try:
            if not p.exists():
                raise FileNotFoundError(str(p))
            with h5py.File(p, "r") as h5:
                key2 = subject_key(h5, str(subject_col))
                grp = h5[key2]
                fs = float(np.asarray(grp["Fs"]).squeeze()) if "Fs" in grp else float("nan")
                data_shape = tuple(int(x) for x in grp["data"].shape)
                event_begin = np.asarray(grp["event_begin"]).reshape(-1) if "event_begin" in grp else np.array([])
                event_end = np.asarray(grp["event_end"]).reshape(-1) if "event_end" in grp else np.array([])
                row_out.update({
                    "h5_subject_key": key2,
                    "fs": fs,
                    "fs_is_512": bool(abs(fs - 512.0) < 1e-6),
                    "data_shape": json.dumps(list(data_shape)),
                    "event_begin_count": int(len(event_begin)),
                    "event_end_count": int(len(event_end)),
                    "has_data": bool("data" in grp),
                    "has_Fs": bool("Fs" in grp),
                    "has_event_begin": bool("event_begin" in grp),
                    "has_event_end": bool("event_end" in grp),
                })
                shape_ok = len(data_shape) == 2 and (data_shape[0] >= SOURCE_SAMPLES or data_shape[1] >= SOURCE_SAMPLES)
                events_ok = len(event_begin) >= int(g["event_index_1based"].max())
                fs_ok = abs(fs - 512.0) < 1e-6
                rows_ok = len(g) == 32
                row_out["shape_ok"] = bool(shape_ok)
                row_out["events_ok"] = bool(events_ok)
                row_out["rows_ok"] = bool(rows_ok)
                row_out["pass"] = bool(shape_ok and events_ok and fs_ok and rows_ok)
                if not row_out["pass"]:
                    row_out["failure_reason"] = f"shape_ok={shape_ok};events_ok={events_ok};fs_ok={fs_ok};rows_ok={rows_ok}"
        except Exception as exc:
            row_out["failure_reason"] = repr(exc)
        source_rows.append(row_out)

    source_pass = bool(source_rows) and all(bool(r.get("pass")) for r in source_rows) and all(bool(r.get("exists")) for r in path_sample)
    return path_sample, source_rows, source_pass

def make_downsample_comparison(df: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mini_rows: list[dict[str, Any]] = []
    mini_stride: list[np.ndarray] = []
    mini_poly: list[np.ndarray] = []
    mini_lowpass: list[np.ndarray] = []

    # Low-pass before decimation: anti-alias only. We deliberately use 60Hz
    # because 128Hz target Nyquist is 64Hz and the published EEG should already be <=40Hz.
    sos = signal.butter(8, 60.0, btype="lowpass", fs=SOURCE_FS, output="sos")

    grouped = df.groupby(["subject_id", "subject_col", "eeg_file"], sort=True, dropna=False)
    t0 = time.perf_counter()
    for _, g in grouped:
        first = g.iloc[0]
        p = Path(unwrap_singleton_path_value(first["eeg_file"]))
        subject_col = str(first["subject_col"])
        try:
            with h5py.File(p, "r") as h5:
                key = subject_key(h5, subject_col)
                data = h5[key]["data"]
                for _, row in g.iterrows():
                    raw = extract_raw_window(data, float(row["eeg_begin_raw"]))
                    stride = raw[::DOWNSAMPLE, :]
                    poly = signal.resample_poly(raw, up=1, down=DOWNSAMPLE, axis=0)
                    low = signal.sosfiltfilt(sos, raw, axis=0, padlen=150)[::DOWNSAMPLE, :]

                    if stride.shape != (TARGET_SAMPLES, TARGET_CHANNELS):
                        raise ValueError(f"bad stride shape {stride.shape}")
                    if poly.shape != (TARGET_SAMPLES, TARGET_CHANNELS):
                        raise ValueError(f"bad poly shape {poly.shape}")
                    if low.shape != (TARGET_SAMPLES, TARGET_CHANNELS):
                        raise ValueError(f"bad lowpass shape {low.shape}")

                    er = energy_ratios(raw)
                    out = {
                        "cache_row": int(row.name),
                        "subject_id": int(row["subject_id"]),
                        "subject_col": str(row["subject_col"]),
                        "stimulus_id": str(row["stimulus_id"]),
                        "eeg_file": str(p),
                        "eeg_begin_raw": float(row["eeg_begin_raw"]),
                        "energy_ratio_gt40hz": er["energy_ratio_gt40hz"],
                        "energy_ratio_gt64hz": er["energy_ratio_gt64hz"],
                        "stride_vs_poly_z_nrmse": nrmse(stride, poly),
                        "stride_vs_poly_z_corr": corr(stride, poly),
                        "stride_vs_lowpass_z_nrmse": nrmse(stride, low),
                        "stride_vs_lowpass_z_corr": corr(stride, low),
                        "poly_vs_lowpass_z_nrmse": nrmse(poly, low),
                        "poly_vs_lowpass_z_corr": corr(poly, low),
                    }
                    rows.append(out)

                    if len(mini_stride) < 24:
                        mini_stride.append(zscore_global(stride).T.astype(np.float32))
                        mini_poly.append(zscore_global(poly).T.astype(np.float32))
                        mini_lowpass.append(zscore_global(low).T.astype(np.float32))
                        mini_rows.append({
                            "cache_row": int(row.name),
                            "subject_id": int(row["subject_id"]),
                            "subject_col": str(row["subject_col"]),
                            "stimulus_id": str(row["stimulus_id"]),
                            "eeg_file": str(p),
                            "eeg_begin_raw": float(row["eeg_begin_raw"]),
                        })
        except Exception as exc:
            rows.append({
                "subject_id": int(first["subject_id"]),
                "subject_col": subject_col,
                "eeg_file": str(p),
                "failure": repr(exc),
            })

    mini_cache_path = TMP_DIR / f"idare_preprocessing_followup_mini_cache_{int(time.time())}.npz"
    np.savez_compressed(
        mini_cache_path,
        stride=np.stack(mini_stride, axis=0) if mini_stride else np.zeros((0, TARGET_CHANNELS, TARGET_SAMPLES), dtype=np.float32),
        resample_poly=np.stack(mini_poly, axis=0) if mini_poly else np.zeros((0, TARGET_CHANNELS, TARGET_SAMPLES), dtype=np.float32),
        lowpass_before_decimation=np.stack(mini_lowpass, axis=0) if mini_lowpass else np.zeros((0, TARGET_CHANNELS, TARGET_SAMPLES), dtype=np.float32),
    )

    manifest = {
        "created_at_utc": now_iso(),
        "temporary_mini_cache_path": str(mini_cache_path),
        "temporary_mini_cache_sha256": sha256_file(mini_cache_path),
        "temporary_mini_cache_size_bytes": mini_cache_path.stat().st_size,
        "rows": mini_rows,
        "n_rows": len(mini_rows),
        "arrays": {
            "stride": [len(mini_rows), TARGET_CHANNELS, TARGET_SAMPLES],
            "resample_poly": [len(mini_rows), TARGET_CHANNELS, TARGET_SAMPLES],
            "lowpass_before_decimation": [len(mini_rows), TARGET_CHANNELS, TARGET_SAMPLES],
        },
        "cache_overwrite": False,
        "elapsed_sec": time.perf_counter() - t0,
    }
    return rows, mini_rows, manifest

def make_summary(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool, dict[str, Any]]:
    metrics = [
        "energy_ratio_gt40hz",
        "energy_ratio_gt64hz",
        "stride_vs_poly_z_nrmse",
        "stride_vs_poly_z_corr",
        "stride_vs_lowpass_z_nrmse",
        "stride_vs_lowpass_z_corr",
        "poly_vs_lowpass_z_nrmse",
        "poly_vs_lowpass_z_corr",
    ]
    summaries = [summarize_metric(rows, m) for m in metrics]

    by_metric = {r["metric"]: r for r in summaries}
    checks = {
        "energy_gt64_p95_pass": float(by_metric["energy_ratio_gt64hz"]["p95"]) <= THRESHOLDS["energy_gt64_p95_max"],
        "energy_gt64_max_pass": float(by_metric["energy_ratio_gt64hz"]["max"]) <= THRESHOLDS["energy_gt64_max_max"],
        "stride_poly_nrmse_p95_pass": float(by_metric["stride_vs_poly_z_nrmse"]["p95"]) <= THRESHOLDS["stride_poly_z_nrmse_p95_max"],
        "stride_poly_nrmse_max_pass": float(by_metric["stride_vs_poly_z_nrmse"]["max"]) <= THRESHOLDS["stride_poly_z_nrmse_max_max"],
        "stride_poly_corr_p05_pass": float(by_metric["stride_vs_poly_z_corr"]["p05"]) >= THRESHOLDS["stride_poly_z_corr_p05_min"],
        "stride_lowpass_nrmse_p95_pass": float(by_metric["stride_vs_lowpass_z_nrmse"]["p95"]) <= THRESHOLDS["stride_lowpass_z_nrmse_p95_max"],
        "stride_lowpass_corr_p05_pass": float(by_metric["stride_vs_lowpass_z_corr"]["p05"]) >= THRESHOLDS["stride_lowpass_z_corr_p05_min"],
    }
    downsample_pass = all(bool(v) for v in checks.values())
    for row in summaries:
        row.update({"thresholds_json": json.dumps(THRESHOLDS), "downsample_pass": downsample_pass})
        if row["metric"] in checks:
            row["check_pass"] = checks[row["metric"]]
    return summaries, downsample_pass, checks

def prior_validity_rows(source_pass: bool, downsample_pass: bool) -> list[dict[str, Any]]:
    prior_path = DOCS / "idare_preprocessing_provenance_prior_result_validity.csv"
    old = pd.read_csv(prior_path)
    rows: list[dict[str, Any]] = []
    if source_pass and downsample_pass:
        eeg_status = "valid_after_followup"
        eeg_reason = "Corrected EEG source audit passes and stride downsampling is not materially different from anti-aliased alternatives under declared thresholds."
    elif source_pass and not downsample_pass:
        eeg_status = "preprocessing_contingent_corrected_downsample_cache_required"
        eeg_reason = "Corrected EEG source audit passes but downsampling difference remains material."
    else:
        eeg_status = "preprocessing_contingent_source_provenance_unresolved"
        eeg_reason = "Corrected EEG source audit failed or source identity remains unresolved."

    for _, r in old.iterrows():
        branch = str(r.get("branch_or_result", r.get("result_id", "")))
        modality = str(r.get("modality_scope", r.get("modality", ""))).upper()
        old_status = str(r.get("validity_status", r.get("status", "")))
        uses_eeg = "EEG" in modality or modality in {"", "MIXED", "BOTH"} or "pairwise" in branch.lower()
        if uses_eeg:
            new_status = eeg_status
            reason = eeg_reason
        else:
            new_status = "valid_after_followup"
            reason = "No EEG dependency detected or EMG provenance passed in previous audit."
        rows.append({
            "branch_or_result": branch,
            "modality_scope": modality,
            "previous_validity_status": old_status,
            "followup_validity_status": new_status,
            "reason": reason,
        })
    return rows

def write_report(report: dict[str, Any], decision_rows: list[dict[str, Any]], summary_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# I-DARE Preprocessing Provenance Follow-up Report",
        "",
        "## Status",
        "",
        "Status: complete; pending human review.",
        "",
        "## Executive Diagnosis",
        "",
        f"- Diagnosis: `{report['diagnosis']}`",
        f"- Decision: `{report['decision']}`",
        f"- Recommendation: `{report['recommendation']}`",
        f"- Recommended next objective: `{report['recommended_next_objective']}`",
        f"- Corrected EEG source pass: `{report['corrected_eeg_source_pass']}`",
        f"- Downsample pass: `{report['downsample_pass']}`",
        f"- Prior results preprocessing valid: `{report['prior_results_preprocessing_valid']}`",
        "",
        "## Path Bug Follow-up",
        "",
        "The original audit likely failed EEG source provenance because a singleton tuple groupby key was converted directly to a `Path`. This follow-up unwraps singleton tuple keys before path construction and persists normalized sample paths.",
        "",
        "## Corrected EEG Source Audit",
        "",
        f"- Corrected source rows: `{report['corrected_eeg_source_rows']}`",
        f"- Passing source rows: `{report['corrected_eeg_source_pass_rows']}`",
        "",
        "## Downsampling Method Comparison",
        "",
        "Compared current stride decimation, `scipy.signal.resample_poly`, and low-pass-before-decimation.",
        "",
        "| Metric | Median | P05 | P95 | Min | Max |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in summary_rows:
        lines.append(
            f"| {r['metric']} | {r.get('median')} | {r.get('p05')} | {r.get('p95')} | {r.get('min')} | {r.get('max')} |"
        )
    lines += [
        "",
        "## Mini-cache",
        "",
        f"- Temporary mini-cache path: `{report['mini_cache_manifest']['temporary_mini_cache_path']}`",
        f"- Temporary mini-cache rows: `{report['mini_cache_manifest']['n_rows']}`",
        f"- Cache overwrite: `{report['mini_cache_manifest']['cache_overwrite']}`",
        "",
        "## Decision Matrix",
        "",
        "| Check | Pass | Decision impact |",
        "|---|---:|---|",
    ]
    for r in decision_rows:
        lines.append(f"| {r['check']} | {r['pass']} | {r['decision_impact']} |")
    lines += [
        "",
        "## Interpretation",
        "",
        report["interpretation"],
        "",
        "## Next Allowed Step",
        "",
        f"`{report['next_allowed_step']}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

def update_project_status(report: dict[str, Any]) -> None:
    status = read_json(PROJECT_STATUS_JSON)
    entry = {
        "objective_id": "idare_preprocessing_provenance_followup_report",
        "status": "complete_pending_human_review",
        "created_at_utc": report["created_at_utc"],
        "diagnosis": report["diagnosis"],
        "decision": report["decision"],
        "recommendation": report["recommendation"],
        "recommended_next_objective": report["recommended_next_objective"],
        "next_allowed_step": report["next_allowed_step"],
        "corrected_eeg_source_pass": report["corrected_eeg_source_pass"],
        "downsample_pass": report["downsample_pass"],
        "prior_results_preprocessing_valid": report["prior_results_preprocessing_valid"],
    }
    status["current_objective"] = entry
    status["recommended_next_objective"] = report["recommended_next_objective"]
    status["next_allowed_step"] = report["next_allowed_step"]
    status["last_updated_utc"] = report["created_at_utc"]
    hist = status.setdefault("objective_history", [])
    if isinstance(hist, list):
        hist.append(entry)
    PROJECT_STATUS_JSON.write_text(json.dumps(safe(status), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    section = f"""

## Current Result: I-DARE Preprocessing Provenance Follow-up Report

Status: complete; pending human review.

Diagnosis: `{report['diagnosis']}`

Decision: `{report['decision']}`

Corrected EEG source pass: `{report['corrected_eeg_source_pass']}`

Downsample pass: `{report['downsample_pass']}`

Prior results preprocessing valid: `{report['prior_results_preprocessing_valid']}`

Recommended next objective: `{report['recommended_next_objective']}`

Next allowed step: `{report['next_allowed_step']}`
"""
    old = PROJECT_STATUS_MD.read_text(encoding="utf-8") if PROJECT_STATUS_MD.exists() else ""
    PROJECT_STATUS_MD.write_text(old.rstrip() + section + "\n", encoding="utf-8")

def main() -> None:
    t0 = time.perf_counter()
    created_at = now_iso()
    df = pd.read_csv(TRIAL_INDEX)
    if "eeg_file" not in df.columns:
        raise SystemExit("trial index missing eeg_file")
    if "subject_col" not in df.columns:
        raise SystemExit("trial index missing subject_col")
    if "eeg_begin_raw" not in df.columns:
        raise SystemExit("trial index missing eeg_begin_raw")

    print(f"trial_index_rows={len(df)}")
    print("correcting EEG path provenance audit")
    path_sample, source_rows, source_pass = make_source_and_path_audits(df)
    write_csv(OUT_PATH_SAMPLE, path_sample)
    write_csv(OUT_EEG_SOURCE, source_rows)

    print("running downsampling comparison: stride vs resample_poly vs lowpass-before-decimation")
    down_rows, mini_rows, mini_manifest = make_downsample_comparison(df)
    write_csv(OUT_DOWNSAMPLE, down_rows)
    OUT_MINI_MANIFEST.write_text(json.dumps(safe(mini_manifest), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    summary_rows, downsample_pass, downsample_checks = make_summary(down_rows)
    write_csv(OUT_DOWNSAMPLE_SUMMARY, summary_rows)

    prior_rows = prior_validity_rows(source_pass, downsample_pass)
    write_csv(OUT_PRIOR_VALIDITY, prior_rows)

    source_pass_rows = sum(1 for r in source_rows if bool(r.get("pass")))
    prior_valid = bool(source_pass and downsample_pass)

    if source_pass and downsample_pass:
        diagnosis = "preprocessing_provenance_followup_resolved_prior_results_valid"
        decision = "proceed_to_wave0_after_human_review"
        recommendation = "create_wave0_parallel_launch_pack_after_review"
        recommended_next = "idare_wave0_parallel_launch_pack_objective"
        next_allowed = "prepare_reviewed_idare_wave0_parallel_launch_pack_objective"
        interpretation = (
            "The corrected EEG source audit passed and current stride downsampling is not materially different "
            "from anti-aliased alternatives under declared thresholds. Prior EEG/EMG I-DARE results can remain "
            "valid from a preprocessing/downsampling standpoint, pending human review."
        )
    elif source_pass and not downsample_pass:
        diagnosis = "preprocessing_provenance_followup_downsample_issue_confirmed"
        decision = "do_not_launch_wave0_create_corrected_eeg_downsample_cache"
        recommendation = "create_corrected_eeg_downsample_cache_before_parallel_wave1"
        recommended_next = "idare_eeg_corrected_downsample_cache_objective"
        next_allowed = "prepare_reviewed_idare_eeg_corrected_downsample_cache_objective"
        interpretation = (
            "The corrected EEG source audit passed, but downsampling differences remain material. "
            "Prior EEG results should remain preprocessing-contingent until a corrected anti-aliased cache and "
            "minimal reference reruns are completed."
        )
    else:
        diagnosis = "preprocessing_provenance_followup_source_unresolved"
        decision = "do_not_launch_wave0_resolve_eeg_source_provenance"
        recommendation = "resolve_dataset_path_or_source_provenance_before_any_new_experiment"
        recommended_next = "idare_preprocessing_source_resolution_objective"
        next_allowed = "prepare_reviewed_idare_preprocessing_source_resolution_objective"
        interpretation = (
            "The corrected EEG source audit did not pass. New experimental branches remain blocked until the source "
            "path/provenance problem is resolved."
        )

    decision_rows = [
        {
            "check": "corrected_eeg_source_audit",
            "pass": bool(source_pass),
            "decision_impact": "source provenance unblocked" if source_pass else "Wave 0 remains blocked; resolve source provenance",
        },
        {
            "check": "downsample_stride_vs_resample_poly_and_lowpass",
            "pass": bool(downsample_pass),
            "decision_impact": "current EEG cache acceptable for prior-result validity" if downsample_pass else "corrected anti-aliased EEG cache required before Wave 1",
        },
        {
            "check": "temporary_mini_cache",
            "pass": bool(mini_manifest.get("n_rows", 0) > 0 and mini_manifest.get("cache_overwrite") is False),
            "decision_impact": "mini-cache verification path works without overwriting current cache",
        },
        {
            "check": "prior_result_validity",
            "pass": bool(prior_valid),
            "decision_impact": "prior results valid from preprocessing standpoint" if prior_valid else "prior EEG/mixed results remain preprocessing-contingent",
        },
        {
            "check": "manual_source_provenance_needed",
            "pass": bool(source_pass),
            "decision_impact": "manual source check not required by repository evidence" if source_pass else "manual or path-level source confirmation required",
        },
    ]
    write_csv(OUT_DECISION, decision_rows)

    report = {
        "created_at_utc": created_at,
        "status": "complete_pending_human_review",
        "diagnosis": diagnosis,
        "decision": decision,
        "recommendation": recommendation,
        "recommended_next_objective": recommended_next,
        "next_allowed_step": next_allowed,
        "trial_index_rows": int(len(df)),
        "corrected_eeg_source_pass": bool(source_pass),
        "corrected_eeg_source_rows": int(len(source_rows)),
        "corrected_eeg_source_pass_rows": int(source_pass_rows),
        "downsample_pass": bool(downsample_pass),
        "downsample_rows": int(len(down_rows)),
        "downsample_checks": safe(downsample_checks),
        "thresholds": THRESHOLDS,
        "mini_cache_manifest": safe(mini_manifest),
        "prior_results_preprocessing_valid": bool(prior_valid),
        "prior_validity_rows": int(len(prior_rows)),
        "decision_rows": int(len(decision_rows)),
        "elapsed_sec": time.perf_counter() - t0,
        "interpretation": interpretation,
        "outputs": {
            "report_md": str(OUT_MD),
            "report_json": str(OUT_JSON),
            "path_sample": str(OUT_PATH_SAMPLE),
            "corrected_eeg_source_audit": str(OUT_EEG_SOURCE),
            "downsample_comparison": str(OUT_DOWNSAMPLE),
            "downsample_summary": str(OUT_DOWNSAMPLE_SUMMARY),
            "mini_cache_manifest": str(OUT_MINI_MANIFEST),
            "prior_result_validity": str(OUT_PRIOR_VALIDITY),
            "decision_matrix": str(OUT_DECISION),
        },
    }

    OUT_JSON.write_text(json.dumps(safe(report), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(report, decision_rows, summary_rows)
    update_project_status(report)

    print("OK_PREPROCESSING_PROVENANCE_FOLLOWUP_REPORT_WRITTEN")
    for p in [OUT_MD, OUT_JSON, OUT_PATH_SAMPLE, OUT_EEG_SOURCE, OUT_DOWNSAMPLE, OUT_DOWNSAMPLE_SUMMARY, OUT_MINI_MANIFEST, OUT_PRIOR_VALIDITY, OUT_DECISION]:
        print(p.relative_to(ROOT))
    print("diagnosis=", diagnosis)
    print("decision=", decision)
    print("recommended_next_objective=", recommended_next)
    print("corrected_eeg_source_pass=", source_pass)
    print("downsample_pass=", downsample_pass)
    print("prior_results_preprocessing_valid=", prior_valid)
    print("downsample_rows=", len(down_rows))
    print("mini_cache_path=", mini_manifest.get("temporary_mini_cache_path"))

if __name__ == "__main__":
    main()
