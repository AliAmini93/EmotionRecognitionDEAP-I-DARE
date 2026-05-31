#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import os
import pickle
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
ROCA = ROOT / "docs" / "roca"
OUT_PREFIX = "idare_06a0_deep_data_and_prior_model_inventory_current"

EXCLUDED_DIR_NAMES = {
    ".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache",
    "node_modules", ".idea", ".vscode", "wandb", "runs", "lightning_logs",
}

TEXT_EXTS = {".md", ".txt", ".py", ".json", ".yaml", ".yml", ".toml", ".sh", ".csv"}
DATA_EXTS = {".npy", ".npz", ".pkl", ".pickle", ".dat", ".mat", ".h5", ".hdf5", ".pt", ".pth", ".ckpt", ".csv", ".json"}

DEEP_TERMS = [
    "deep", "cnn", "lstm", "gru", "transformer", "attention", "eegnet", "torch",
    "pytorch", "tensorflow", "keras", "conv", "tcn", "temporal", "raw eeg",
    "time-frequency", "spectrogram", "wavelet", "representation", "embedding",
    "domain adaptation", "few-shot", "loso", "cross-subject", "proposed model",
    "neural", "gpu",
]

RESULT_TERMS = [
    "accuracy", "acc", "rmse", "mae", "f1", "auc", "ccc", "pearson", "loss",
    "valence", "arousal", "subject", "fold", "test", "validation", "baseline",
]

DATA_HINT_TERMS = [
    "deap", "eeg", "emg", "data", "dataset", "preprocessed", "raw", "physio",
    "feature", "cache", "subject", "trial", "s01", "s1",
]


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)


def safe_stat(p: Path) -> dict[str, Any]:
    try:
        st = p.stat()
        return {"size_bytes": int(st.st_size), "size_mb": round(st.st_size / (1024 * 1024), 4)}
    except Exception:
        return {"size_bytes": None, "size_mb": None}


def is_interesting_path(p: Path, terms: list[str]) -> bool:
    s = rel(p).lower()
    return any(t.lower() in s for t in terms)


def iter_files():
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIR_NAMES]
        r = Path(root)
        for f in files:
            p = r / f
            if p.is_file():
                yield p


def inspect_npy(p: Path) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        arr = np.load(p, mmap_mode="r", allow_pickle=False)
        out["shape"] = tuple(int(x) for x in arr.shape)
        out["dtype"] = str(arr.dtype)
        out["kind"] = "npy"
    except Exception as e:
        out["inspect_error"] = repr(e)
    return out


def inspect_npz(p: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"kind": "npz"}
    try:
        with np.load(p, allow_pickle=False) as z:
            keys = list(z.keys())
            out["npz_keys"] = keys[:50]
            shapes = {}
            dtypes = {}
            for k in keys[:50]:
                try:
                    shapes[k] = tuple(int(x) for x in z[k].shape)
                    dtypes[k] = str(z[k].dtype)
                except Exception:
                    pass
            out["npz_shapes"] = shapes
            out["npz_dtypes"] = dtypes
    except Exception as e:
        out["inspect_error"] = repr(e)
    return out


def inspect_pickle_like(p: Path, max_mb: float = 150.0) -> dict[str, Any]:
    out: dict[str, Any] = {"kind": "pickle_like"}
    st = safe_stat(p)
    if st.get("size_mb") is not None and st["size_mb"] > max_mb:
        out["inspect_skipped"] = f"file larger than {max_mb} MB"
        return out
    try:
        with p.open("rb") as f:
            obj = pickle.load(f, encoding="latin1")
        out["object_type"] = type(obj).__name__
        if isinstance(obj, dict):
            out["dict_keys"] = list(map(str, obj.keys()))[:50]
            shapes = {}
            dtypes = {}
            for k, v in obj.items():
                if hasattr(v, "shape"):
                    shapes[str(k)] = tuple(int(x) for x in v.shape)
                    dtypes[str(k)] = str(getattr(v, "dtype", ""))
                elif isinstance(v, (list, tuple)):
                    shapes[str(k)] = [len(v)]
            out["dict_shapes"] = shapes
            out["dict_dtypes"] = dtypes
        elif hasattr(obj, "shape"):
            out["shape"] = tuple(int(x) for x in obj.shape)
            out["dtype"] = str(getattr(obj, "dtype", ""))
    except Exception as e:
        out["inspect_error"] = repr(e)
    return out


def inspect_csv_header(p: Path, max_mb: float = 200.0) -> dict[str, Any]:
    out: dict[str, Any] = {"kind": "csv"}
    st = safe_stat(p)
    if st.get("size_mb") is not None and st["size_mb"] > max_mb:
        out["inspect_skipped"] = f"file larger than {max_mb} MB"
        return out
    try:
        df = pd.read_csv(p, nrows=20)
        out["columns"] = list(df.columns)
        out["sample_rows"] = int(len(df))
        try:
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                row_count = sum(1 for _ in f) - 1
            out["estimated_rows"] = max(row_count, 0)
        except Exception:
            pass
    except Exception as e:
        out["inspect_error"] = repr(e)
    return out


def inspect_json(p: Path, max_mb: float = 50.0) -> dict[str, Any]:
    out: dict[str, Any] = {"kind": "json"}
    st = safe_stat(p)
    if st.get("size_mb") is not None and st["size_mb"] > max_mb:
        out["inspect_skipped"] = f"file larger than {max_mb} MB"
        return out
    try:
        obj = json.loads(p.read_text(encoding="utf-8", errors="ignore"))
        out["object_type"] = type(obj).__name__
        if isinstance(obj, dict):
            out["dict_keys"] = list(map(str, obj.keys()))[:50]
        elif isinstance(obj, list):
            out["list_len"] = len(obj)
            out["first_type"] = type(obj[0]).__name__ if obj else None
    except Exception as e:
        out["inspect_error"] = repr(e)
    return out


def find_text_hits(p: Path, max_mb: float = 2.0) -> dict[str, Any] | None:
    st = safe_stat(p)
    if st.get("size_mb") is not None and st["size_mb"] > max_mb:
        return None
    try:
        txt = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    low = txt.lower()
    deep_hits = [t for t in DEEP_TERMS if t in low]
    result_hits = [t for t in RESULT_TERMS if t in low]
    if not deep_hits and not result_hits and not is_interesting_path(p, DEEP_TERMS):
        return None
    snippets = []
    lines = txt.splitlines()
    pattern = re.compile("|".join(re.escape(t) for t in DEEP_TERMS + RESULT_TERMS), re.I)
    for i, line in enumerate(lines):
        if pattern.search(line):
            s = line.strip()
            if len(s) > 220:
                s = s[:217] + "..."
            snippets.append(f"L{i+1}: {s}")
            if len(snippets) >= 8:
                break
    return {
        "path": rel(p),
        **st,
        "deep_terms": ",".join(deep_hits[:20]),
        "result_terms": ",".join(result_hits[:20]),
        "snippets": " || ".join(snippets),
    }


def normalize_for_json(x: Any):
    if isinstance(x, dict):
        return {str(k): normalize_for_json(v) for k, v in x.items()}
    if isinstance(x, list):
        return [normalize_for_json(v) for v in x]
    if isinstance(x, tuple):
        return [normalize_for_json(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        v = float(x)
        return None if not math.isfinite(v) else v
    if isinstance(x, float):
        return None if not math.isfinite(x) else x
    return x


def md_table(df: pd.DataFrame, max_rows: int = 25) -> str:
    if df.empty:
        return "_empty_\n"
    x = df.head(max_rows).copy()
    for c in x.columns:
        x[c] = x[c].map(lambda v: "" if pd.isna(v) else str(v).replace("\n", " "))
    cols = list(x.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, r in x.iterrows():
        vals = [str(r[c]).replace("|", "/") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_Showing {max_rows} of {len(df)} rows._")
    return "\n".join(lines) + "\n"


def load_existing_decision_csv(name: str) -> pd.DataFrame:
    p = ROCA / name
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p)
    except Exception:
        return pd.DataFrame()


def summarize_existing_roca() -> pd.DataFrame:
    rows = []
    files = [
        ("05an_representation_gate", "idare_representation_learning_feasibility_gate_current_decision_table.csv"),
        ("05am_sample_reduction", "idare_physiology_assisted_calibration_sample_reduction_current_decision_table.csv"),
        ("05al_failure_rescue", "idare_failure_subject_physiology_rescue_audit_current_decision_table.csv"),
        ("05ak_bridge", "idare_high_disagreement_personalization_bridge_current_decision_table.csv"),
        ("05ajb_high_disagreement_confirmatory", "idare_high_disagreement_direct_deviation_confirmatory_stats_current_verdict.csv"),
        ("05ai_direct_deviation", "idare_direct_deviation_predictability_audit_current_decision_table.csv"),
        ("05ahx_physiology_challenge_synthesis", "idare_physiology_challenge_synthesis_current_decision_table.csv"),
        ("05ag_scientific_direction", "idare_scientific_direction_lock_current_decision_table.csv"),
        ("05af_model_family_confirmatory", "idare_subject_calibration_model_family_confirmatory_stats_current_verdict.csv"),
    ]
    for step, fname in files:
        df = load_existing_decision_csv(fname)
        if df.empty:
            rows.append({"step": step, "file": fname, "status": "missing_or_unreadable"})
            continue
        for _, r in df.iterrows():
            target = r.get("target", "")
            decision_cols = [c for c in df.columns if "decision" in c or "status" in c or "final" in c]
            metric_cols = [c for c in df.columns if any(k in c for k in ["rmse", "lift", "win_margin", "pearson", "ci95"])]
            summary = []
            for c in decision_cols[:4]:
                summary.append(f"{c}={r.get(c)}")
            metrics = []
            for c in metric_cols[:6]:
                metrics.append(f"{c}={r.get(c)}")
            rows.append({
                "step": step,
                "file": fname,
                "target": target,
                "decision_summary": "; ".join(summary),
                "metric_summary": "; ".join(metrics),
                "status": "read",
            })
    return pd.DataFrame(rows)


def main():
    data_rows = []
    shape_rows = []
    text_rows = []

    for p in iter_files():
        ext = p.suffix.lower()
        rp = rel(p)
        st = safe_stat(p)
        if ext in DATA_EXTS and is_interesting_path(p, DATA_HINT_TERMS):
            row = {"path": rp, "extension": ext, **st}
            info: dict[str, Any] = {}
            if ext == ".npy":
                info = inspect_npy(p)
            elif ext == ".npz":
                info = inspect_npz(p)
            elif ext in {".pkl", ".pickle", ".dat"}:
                if is_interesting_path(p, ["deap", "data_preprocessed", "s01", "s1", "subject", "eeg"]):
                    info = inspect_pickle_like(p)
                else:
                    info = {"inspect_skipped": "pickle-like file without clear DEAP/EEG hint"}
            elif ext == ".csv":
                info = inspect_csv_header(p)
            elif ext == ".json":
                info = inspect_json(p)
            else:
                info = {"kind": ext.lstrip("."), "inspect_skipped": "metadata only"}
            row.update({k: json.dumps(normalize_for_json(v)) if isinstance(v, (dict, list, tuple)) else v for k, v in info.items()})
            data_rows.append(row)
            if "shape" in info:
                shape_rows.append({"path": rp, "key": "", "shape": str(info["shape"]), "dtype": info.get("dtype", ""), "kind": info.get("kind", ext)})
            if "dict_shapes" in info and isinstance(info["dict_shapes"], dict):
                dtypes = info.get("dict_dtypes", {}) if isinstance(info.get("dict_dtypes"), dict) else {}
                for k, shp in info["dict_shapes"].items():
                    shape_rows.append({"path": rp, "key": k, "shape": str(shp), "dtype": dtypes.get(k, ""), "kind": info.get("kind", ext)})
            if "npz_shapes" in info and isinstance(info["npz_shapes"], dict):
                dtypes = info.get("npz_dtypes", {}) if isinstance(info.get("npz_dtypes"), dict) else {}
                for k, shp in info["npz_shapes"].items():
                    shape_rows.append({"path": rp, "key": k, "shape": str(shp), "dtype": dtypes.get(k, ""), "kind": info.get("kind", ext)})

        if ext in TEXT_EXTS and (is_interesting_path(p, DEEP_TERMS + RESULT_TERMS) or "docs" in rp or "scripts" in rp):
            hit = find_text_hits(p)
            if hit is not None:
                text_rows.append(hit)

    data_df = pd.DataFrame(data_rows).sort_values(["size_bytes", "path"], ascending=[False, True]) if data_rows else pd.DataFrame()
    shape_df = pd.DataFrame(shape_rows).sort_values(["path", "key"]) if shape_rows else pd.DataFrame()
    text_df = pd.DataFrame(text_rows).sort_values(["size_bytes", "path"], ascending=[False, True]) if text_rows else pd.DataFrame()
    roca_df = summarize_existing_roca()

    expected_spec = pd.DataFrame([
        {"item": "DEAP original participants", "expected": "32", "why_it_matters": "Original DEAP has 32 participants; project outputs may have more rows/subjects if merged or using derived pseudo-subject IDs, so inventory must separate DEAP raw from project-derived tables."},
        {"item": "DEAP trials per participant", "expected": "40 music-video trials", "why_it_matters": "Representation learning should preserve trial identity and avoid stimulus leakage in cross-subject evaluation."},
        {"item": "DEAP preprocessed signal shape", "expected": "usually 40 trials x 40 channels x 8064 samples per subject file", "why_it_matters": "8064 samples at 128 Hz equals 63 seconds: 3 s baseline + 60 s stimulus."},
        {"item": "EEG channels", "expected": "32 EEG channels in the 40-channel preprocessed array", "why_it_matters": "Deep EEG models should use EEG channels separately from peripheral channels unless multimodal design is explicit."},
        {"item": "Peripheral channels", "expected": "8 non-EEG peripheral channels in the 40-channel preprocessed array", "why_it_matters": "EMG/EOG/GSR/resp/etc. should be handled as separate modalities, not silently mixed as EEG."},
        {"item": "Labels", "expected": "valence, arousal, dominance, liking", "why_it_matters": "Current ROCA target focus is valence/arousal; dominance/liking can be auxiliary only if leakage-safe."},
        {"item": "Baseline/stimulus split", "expected": "3 s baseline = 384 samples; 60 s stimulus = 7680 samples at 128 Hz", "why_it_matters": "Model inputs must document whether baseline is removed, concatenated, used as context, or excluded."},
    ])

    requirements = pd.DataFrame([
        {"requirement": "R1_raw_or_preprocessed_trial_tensor", "must_have": "Per-trial EEG/EMG time series aligned as subject_id, stimulus_id, trial_id, channel, time.", "failure_if_missing": "If only engineered feature tables exist, this is not true representation learning."},
        {"requirement": "R2_baseline_policy", "must_have": "Explicit handling of 3 s baseline: subtract, encode as separate context, or drop.", "failure_if_missing": "Baseline leakage or inconsistent residual target definition."},
        {"requirement": "R3_loso_and_stimulus_prior_lock", "must_have": "Evaluation must keep subject out of training and compare against B2_LOCKED kernel_residual_shrink4 k=16.", "failure_if_missing": "Model can look good while only rediscovering stimulus priors or subject leakage."},
        {"requirement": "R4_high_disagreement_arousal_entry_point", "must_have": "First representation experiment should test arousal high-disagreement EEG, where fixed EEG-bandpower had confirmed residual signal.", "failure_if_missing": "Deep model search becomes an unbounded architecture fishing exercise."},
        {"requirement": "R5_prior_deep_model_forensics", "must_have": "Find prior proposed deep model scripts/logs/metrics and compare exact protocol, split, targets, and leakage controls.", "failure_if_missing": "We may repeat the same failed deep-learning experiment without understanding why."},
    ])

    next_steps = pd.DataFrame([
        {"priority": 1, "step": "06a0b", "title": "Prior deep-learning run forensic review", "purpose": "Open the candidate scripts/logs found by this inventory and extract model architecture, input tensor, split protocol, and exact metrics.", "success_condition": "A short table says whether the old model failed because of input representation, split/generalization, target definition, or training instability."},
        {"priority": 2, "step": "06a1", "title": "Minimal arousal high-disagreement EEG representation prototype", "purpose": "Only after data readiness is confirmed, test a small GPU model on raw/time-frequency EEG for the one confirmed signal pocket.", "success_condition": "Beats fixed EEG-bandpower high-disagreement residual model and does not degrade locked B2 evaluation."},
        {"priority": 3, "step": "06a2", "title": "Subject-adaptive residual representation", "purpose": "Learn EEG/EMG embeddings with k-shot subject context instead of linear correction on fixed features.", "success_condition": "Beats B2 locked baseline or matches B2 with fewer calibration samples under paired subject-level gates."},
    ])

    prioritized = text_df.copy()
    if not prioritized.empty:
        prioritized["priority_score"] = (
            prioritized.get("deep_terms", "").fillna("").map(lambda s: len([x for x in str(s).split(",") if x])) * 2
            + prioritized.get("result_terms", "").fillna("").map(lambda s: len([x for x in str(s).split(",") if x]))
            + prioritized.get("path", "").fillna("").str.lower().map(lambda s: 5 if any(k in s for k in ["deep", "cnn", "lstm", "transformer", "torch", "model"]) else 0)
        )
        prioritized = prioritized.sort_values(["priority_score", "size_bytes"], ascending=[False, False])

    outputs = {
        "data_inventory": ROCA / f"{OUT_PREFIX}_data_inventory.csv",
        "shape_inventory": ROCA / f"{OUT_PREFIX}_shape_inventory.csv",
        "prior_dl_candidates": ROCA / f"{OUT_PREFIX}_prior_dl_candidates.csv",
        "roca_evidence_rollup": ROCA / f"{OUT_PREFIX}_roca_evidence_rollup.csv",
        "expected_deap_spec": ROCA / f"{OUT_PREFIX}_expected_deap_spec.csv",
        "representation_requirements": ROCA / f"{OUT_PREFIX}_representation_requirements.csv",
        "next_steps": ROCA / f"{OUT_PREFIX}_next_steps.csv",
        "json": ROCA / f"{OUT_PREFIX}.json",
        "md": ROCA / f"{OUT_PREFIX}.md",
    }

    data_df.to_csv(outputs["data_inventory"], index=False)
    shape_df.to_csv(outputs["shape_inventory"], index=False)
    prioritized.to_csv(outputs["prior_dl_candidates"], index=False)
    roca_df.to_csv(outputs["roca_evidence_rollup"], index=False)
    expected_spec.to_csv(outputs["expected_deap_spec"], index=False)
    requirements.to_csv(outputs["representation_requirements"], index=False)
    next_steps.to_csv(outputs["next_steps"], index=False)

    artifact = {
        "step": "06a0",
        "title": "I-DARE deep data and prior model inventory",
        "expected_deap_spec": expected_spec.to_dict(orient="records"),
        "representation_requirements": requirements.to_dict(orient="records"),
        "next_steps": next_steps.to_dict(orient="records"),
        "counts": {
            "data_inventory_rows": int(len(data_df)),
            "shape_inventory_rows": int(len(shape_df)),
            "prior_deep_candidate_rows": int(len(prioritized)),
            "roca_evidence_rows": int(len(roca_df)),
        },
        "top_prior_deep_candidates": prioritized.head(30).to_dict(orient="records") if not prioritized.empty else [],
        "top_shape_inventory": shape_df.head(50).to_dict(orient="records") if not shape_df.empty else [],
    }
    outputs["json"].write_text(json.dumps(normalize_for_json(artifact), indent=2), encoding="utf-8")

    lines = []
    lines.append("# I-DARE 06a0 Deep Data and Prior Model Inventory\n\n")
    lines.append("This audit checks whether the project has the raw/preprocessed physiology tensors needed for real representation learning, and searches the repository for prior deep-learning scripts/results so we do not repeat old failures blindly.\n\n")
    lines.append("## Expected DEAP experiment/data facts to verify locally\n\n")
    lines.append(md_table(expected_spec, max_rows=20))
    lines.append("\n## Actual data inventory: largest/most relevant files\n\n")
    show_cols = [c for c in ["path", "extension", "size_mb", "kind", "shape", "dict_keys", "dict_shapes", "columns", "estimated_rows", "inspect_error", "inspect_skipped"] if c in data_df.columns]
    lines.append(md_table(data_df[show_cols] if show_cols else data_df, max_rows=30))
    lines.append("\n## Shape inventory\n\n")
    lines.append(md_table(shape_df, max_rows=40))
    lines.append("\n## Prior deep-learning candidates discovered in repo\n\n")
    cand_cols = [c for c in ["path", "size_mb", "priority_score", "deep_terms", "result_terms", "snippets"] if c in prioritized.columns]
    lines.append(md_table(prioritized[cand_cols] if cand_cols else prioritized, max_rows=40))
    lines.append("\n## ROCA evidence rollup\n\n")
    lines.append(md_table(roca_df, max_rows=60))
    lines.append("\n## Representation-learning requirements\n\n")
    lines.append(md_table(requirements, max_rows=20))
    lines.append("\n## Next steps\n\n")
    lines.append(md_table(next_steps, max_rows=20))
    lines.append("\n## Interpretation\n\n")
    lines.append("If the inventory shows only fixed feature tables, then deep representation learning is not yet possible in a scientifically meaningful sense. If DEAP-like trial tensors are present, the first non-open-ended experiment should be arousal high-disagreement EEG representation learning, because that is the only fixed-feature physiology pocket that already passed confirmatory residual-signal gates.\n")
    outputs["md"].write_text("".join(lines), encoding="utf-8")

    print("ROCA step 06a0 completed.")
    for p in outputs.values():
        print(f"wrote: {p}")

    print("\nExpected DEAP spec:")
    print(expected_spec.to_string(index=False))

    print("\nTop data inventory rows:")
    if data_df.empty:
        print("No relevant data-like files found by inventory rules.")
    else:
        print((data_df[show_cols] if show_cols else data_df).head(20).to_string(index=False))

    print("\nTop prior deep-learning candidates:")
    if prioritized.empty:
        print("No prior deep-learning candidates found by text search.")
    else:
        print((prioritized[cand_cols] if cand_cols else prioritized).head(20).to_string(index=False))

    print("\nNext steps:")
    print(next_steps.to_string(index=False))

    print("\n================== KEY OUTPUTS ==================")
    print(outputs["expected_deap_spec"].read_text(encoding="utf-8").strip())
    print()
    print(outputs["representation_requirements"].read_text(encoding="utf-8").strip())
    print()
    print(outputs["next_steps"].read_text(encoding="utf-8").strip())

    print("\n================== SIZE CHECK ==================")
    for p in sorted(outputs.values(), key=lambda x: x.stat().st_size if x.exists() else 0):
        if p.exists():
            print(f"{p.stat().st_size/1024:.1f}K\t{p}")


if __name__ == "__main__":
    main()
