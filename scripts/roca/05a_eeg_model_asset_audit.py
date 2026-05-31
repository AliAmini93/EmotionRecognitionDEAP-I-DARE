#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
CACHE_DIR = ROOT / ".cache"
ROCA_DIR = ROOT / "docs" / "roca"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

RAW_EEG_NPY = CACHE_DIR / "idare_eeg_windows_32x640_float32.npy"
RAW_EEG_INDEX = CACHE_DIR / "idare_eeg_cache_index.csv"

BC_EEG_NPY = CACHE_DIR / "idare_eeg_windows_32x640_float32_baseline_corrected.npy"
BC_EEG_INDEX = CACHE_DIR / "idare_eeg_cache_index_baseline_corrected.csv"

TRIAL_INDEX = CACHE_DIR / "idare_trial_index.csv"
STIMULUS_ONLY_PRED = ROCA_DIR / "stimulus_only_predictions_current.csv"
FOLD_SAFE_SELECTED = ROCA_DIR / "fold_safe_selected_stimuli_current.csv"

OUT_MD = ROCA_DIR / "eeg_model_asset_audit_current.md"
OUT_JSON = ROCA_DIR / "eeg_model_asset_audit_current.json"

EXPECTED_SHAPE_TAIL = (32, 640)
BATCH_SIZE = 8


def safe_float(x: Any):
    try:
        v = float(x)
    except Exception:
        return None
    return v if math.isfinite(v) else None


def clean_json(x):
    if isinstance(x, dict):
        return {str(k): clean_json(v) for k, v in x.items()}
    if isinstance(x, list):
        return [clean_json(v) for v in x]
    if isinstance(x, tuple):
        return [clean_json(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        v = float(x)
        return None if not math.isfinite(v) else v
    if isinstance(x, float):
        return None if not math.isfinite(x) else x
    return x


def file_size_human(path: Path) -> str:
    if not path.exists():
        return "missing"
    value = float(path.stat().st_size)
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024 or unit == "GB":
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{value:.2f} GB"


def shape_to_list(x):
    return [int(v) for v in tuple(x)]


def require_columns(df: pd.DataFrame, cols: list[str], label: str):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"{label} missing columns: {missing}")


def load_index(path: Path, label: str) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)
    require_columns(df, ["cache_row", "subject_id", "stimulus_id"], label)

    df = df.copy()
    df["cache_row"] = df["cache_row"].astype(int)
    df["subject_id"] = df["subject_id"].astype(int)
    df["stimulus_id"] = df["stimulus_id"].astype(str)

    return df.sort_values("cache_row").reset_index(drop=True)


def audit_cache(npy_path: Path, index_path: Path, label: str) -> dict[str, Any]:
    if not npy_path.exists():
        raise FileNotFoundError(npy_path)

    idx = load_index(index_path, f"{label}_index")
    x = np.load(npy_path, mmap_mode="r")

    issues = []

    if x.ndim != 3:
        issues.append(f"Expected 3D EEG cache, got ndim={x.ndim}")

    if tuple(x.shape[1:]) != EXPECTED_SHAPE_TAIL:
        issues.append(f"Expected shape tail {EXPECTED_SHAPE_TAIL}, got {tuple(x.shape[1:])}")

    if x.shape[0] != len(idx):
        issues.append(f"Feature/index row mismatch: npy={x.shape[0]}, index={len(idx)}")

    if not np.array_equal(idx["cache_row"].to_numpy(), np.arange(len(idx))):
        issues.append("cache_row is not contiguous 0..N-1 after sorting")

    sample = np.asarray(x[: min(BATCH_SIZE, x.shape[0])], dtype=np.float32)

    return {
        "label": label,
        "npy_path": str(npy_path),
        "index_path": str(index_path),
        "file_size": file_size_human(npy_path),
        "shape": shape_to_list(x.shape),
        "dtype": str(x.dtype),
        "index_rows": int(len(idx)),
        "subjects": int(idx["subject_id"].nunique()),
        "stimuli": int(idx["stimulus_id"].nunique()),
        "sample_mean": safe_float(np.mean(sample)),
        "sample_std": safe_float(np.std(sample)),
        "sample_min": safe_float(np.min(sample)),
        "sample_max": safe_float(np.max(sample)),
        "issues": issues,
    }


def check_alignment(cache_index_path: Path, label: str) -> dict[str, Any]:
    idx = load_index(cache_index_path, f"{label}_index")

    out: dict[str, Any] = {
        "label": label,
        "trial_index_merge": None,
        "stimulus_only_prediction_merge": None,
        "fold_safe_selected_merge": None,
        "issues": [],
    }

    if TRIAL_INDEX.exists():
        trial = pd.read_csv(TRIAL_INDEX)
        require_columns(trial, ["subject_id", "stimulus_id"], "trial_index")
        trial = trial.copy()
        trial["subject_id"] = trial["subject_id"].astype(int)
        trial["stimulus_id"] = trial["stimulus_id"].astype(str)

        merged = idx.merge(
            trial[["subject_id", "stimulus_id"]].drop_duplicates(),
            on=["subject_id", "stimulus_id"],
            how="left",
            indicator=True,
        )
        matched = int((merged["_merge"] == "both").sum())
        out["trial_index_merge"] = {
            "cache_rows": int(len(idx)),
            "matched_rows": matched,
            "unmatched_rows": int(len(idx) - matched),
        }
        if matched != len(idx):
            out["issues"].append(f"{label}: trial_index unmatched rows={len(idx) - matched}")
    else:
        out["issues"].append(f"Missing trial index: {TRIAL_INDEX}")

    if STIMULUS_ONLY_PRED.exists():
        pred = pd.read_csv(STIMULUS_ONLY_PRED)
        require_columns(pred, ["test_subject", "stimulus_id", "target"], "stimulus_only_predictions")
        pred = pred[pred["model"].eq("stimulus_only")].copy() if "model" in pred.columns else pred.copy()
        pred["test_subject"] = pred["test_subject"].astype(int)
        pred["stimulus_id"] = pred["stimulus_id"].astype(str)

        keys = pred[["test_subject", "stimulus_id"]].drop_duplicates().rename(
            columns={"test_subject": "subject_id"}
        )
        merged = idx.merge(keys, on=["subject_id", "stimulus_id"], how="left", indicator=True)
        matched = int((merged["_merge"] == "both").sum())
        out["stimulus_only_prediction_merge"] = {
            "cache_rows": int(len(idx)),
            "matched_rows": matched,
            "unmatched_rows": int(len(idx) - matched),
        }
        if matched != len(idx):
            out["issues"].append(f"{label}: stimulus_only prediction unmatched rows={len(idx) - matched}")
    else:
        out["issues"].append(f"Missing stimulus-only predictions: {STIMULUS_ONLY_PRED}")

    if FOLD_SAFE_SELECTED.exists():
        selected = pd.read_csv(FOLD_SAFE_SELECTED)
        require_columns(selected, ["test_subject", "stimulus_id", "target", "subset"], "fold_safe_selected")
        selected["test_subject"] = selected["test_subject"].astype(int)
        selected["stimulus_id"] = selected["stimulus_id"].astype(str)

        out["fold_safe_selected_merge"] = {
            "rows": int(len(selected)),
            "subjects": int(selected["test_subject"].nunique()),
            "stimuli": int(selected["stimulus_id"].nunique()),
            "subsets": sorted(selected["subset"].astype(str).unique().tolist()),
            "targets": sorted(selected["target"].astype(str).unique().tolist()),
        }
    else:
        out["issues"].append(f"Missing fold-safe selected stimuli: {FOLD_SAFE_SELECTED}")

    return out


def import_models():
    from emotion_deap_idare.models.eeg_segment_encoder import EEGSegmentEncoder
    from emotion_deap_idare.models.eeg_segment_classifier import EEGSegmentClassifier

    return EEGSegmentEncoder, EEGSegmentClassifier


def count_params(model: torch.nn.Module) -> dict[str, int]:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {
        "total_params": int(total),
        "trainable_params": int(trainable),
    }


def forward_smoke(npy_path: Path, label: str, device: torch.device) -> dict[str, Any]:
    _, EEGSegmentClassifier = import_models()

    x_np = np.load(npy_path, mmap_mode="r")
    batch_np = np.asarray(x_np[:BATCH_SIZE], dtype=np.float32)
    batch = torch.from_numpy(batch_np).to(device)

    model = EEGSegmentClassifier(
        C=32,
        sampling_rate=128,
        window_sec=5.0,
        n_classes=2,
        modelsize="lite",
        dropout=0.1,
        head_dropout=0.3,
        norm_kind="gn",
        stem_fusion="concat",
        channel_pos_mode="learnable",
        channel_mixer="mha",
        use_spectral_branch=False,
        use_projection_head=True,
        projection_dim=64,
    ).to(device)

    model.eval()

    with torch.no_grad():
        logits, aux = model(batch, return_attn=True)

    result = {
        "label": label,
        "device": str(device),
        "input_shape": shape_to_list(batch.shape),
        "logits_shape": shape_to_list(logits.shape),
        "z_shape": shape_to_list(aux["z"].shape) if "z" in aux else None,
        "z_proj_shape": shape_to_list(aux["z_proj"].shape) if "z_proj" in aux else None,
        "temporal_attn_shape": shape_to_list(aux["temporal_attn"].shape) if "temporal_attn" in aux else None,
        "channel_pool_attn_shape": shape_to_list(aux["channel_pool_attn"].shape) if "channel_pool_attn" in aux else None,
        "logits_mean": safe_float(logits.detach().cpu().float().mean().item()),
        "logits_std": safe_float(logits.detach().cpu().float().std().item()),
    }
    result.update(count_params(model))
    return result


def write_md(report: dict[str, Any]):
    lines = []
    lines.append("# ROCA-I-DARE EEG Model Asset Audit\n")
    lines.append("No model training was performed.\n")

    lines.append("## Status\n")
    lines.append(f"Status: **{report['status']}**\n")

    lines.append("## Cache audit\n")
    lines.append("| Cache | Shape | Dtype | Rows | Subjects | Stimuli | Size | Issues |")
    lines.append("|---|---:|---|---:|---:|---:|---:|---|")
    for c in report["cache_audit"]:
        issues = "; ".join(c["issues"]) if c["issues"] else "None"
        lines.append(
            f"| {c['label']} | {c['shape']} | {c['dtype']} | {c['index_rows']} | "
            f"{c['subjects']} | {c['stimuli']} | {c['file_size']} | {issues} |"
        )
    lines.append("")

    lines.append("## Alignment checks\n")
    lines.append("```json")
    lines.append(json.dumps(report["alignment"], indent=2, ensure_ascii=False))
    lines.append("```\n")

    lines.append("## Forward smoke tests\n")
    lines.append("| Cache | Device | Input | Logits | z | z_proj | Temporal attn | Channel pool attn | Params |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for f in report["forward_smoke"]:
        lines.append(
            f"| {f['label']} | {f['device']} | {f['input_shape']} | {f['logits_shape']} | "
            f"{f['z_shape']} | {f['z_proj_shape']} | {f['temporal_attn_shape']} | "
            f"{f['channel_pool_attn_shape']} | {f['total_params']} |"
        )
    lines.append("")

    lines.append("## Model import\n")
    lines.append("```json")
    lines.append(json.dumps(report["model_import"], indent=2, ensure_ascii=False))
    lines.append("```\n")

    lines.append("## Issues\n")
    if report["issues"]:
        for issue in report["issues"]:
            lines.append(f"- {issue}")
    else:
        lines.append("- None.")
    lines.append("")

    lines.append("## Next step\n")
    lines.append(
        "If this audit passes, design the EEG training protocol before writing the training script: "
        "target, loss, fold split, validation policy, cache choice, model head, and metrics.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    ROCA_DIR.mkdir(parents=True, exist_ok=True)

    issues = []
    cache_audit = []
    alignment = []
    forward = []
    model_import = {}

    required_paths = [
        RAW_EEG_NPY,
        RAW_EEG_INDEX,
        BC_EEG_NPY,
        BC_EEG_INDEX,
        TRIAL_INDEX,
        STIMULUS_ONLY_PRED,
        FOLD_SAFE_SELECTED,
    ]

    for path in required_paths:
        if not path.exists():
            issues.append(f"Missing required path: {path}")

    try:
        EEGSegmentEncoder, EEGSegmentClassifier = import_models()
        model_import = {
            "EEGSegmentEncoder": str(EEGSegmentEncoder),
            "EEGSegmentClassifier": str(EEGSegmentClassifier),
            "status": "OK",
        }
    except Exception as exc:
        issues.append(f"Model import failed: {exc}")
        model_import = {
            "status": "FAILED",
            "error": str(exc),
        }

    cache_specs = [
        ("raw", RAW_EEG_NPY, RAW_EEG_INDEX),
        ("baseline_corrected", BC_EEG_NPY, BC_EEG_INDEX),
    ]

    for label, npy, idx in cache_specs:
        if npy.exists() and idx.exists():
            try:
                cache_audit.append(audit_cache(npy, idx, label))
                alignment.append(check_alignment(idx, label))
            except Exception as exc:
                issues.append(f"{label} cache audit failed: {exc}")
        else:
            issues.append(f"{label} cache/index missing")

    if model_import.get("status") == "OK":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        for label, npy, _ in cache_specs:
            if npy.exists():
                try:
                    forward.append(forward_smoke(npy, label, device))
                except Exception as exc:
                    issues.append(f"{label} forward smoke failed: {exc}")

    for item in cache_audit:
        issues.extend([f"{item['label']}: {issue}" for issue in item["issues"]])

    for item in alignment:
        issues.extend(item.get("issues", []))

    status = "PASSED" if not issues else "FAILED"

    report = {
        "status": status,
        "root": str(ROOT),
        "device": {
            "torch": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        },
        "paths": {
            "raw_eeg_npy": str(RAW_EEG_NPY),
            "raw_eeg_index": str(RAW_EEG_INDEX),
            "baseline_corrected_eeg_npy": str(BC_EEG_NPY),
            "baseline_corrected_eeg_index": str(BC_EEG_INDEX),
            "trial_index": str(TRIAL_INDEX),
            "stimulus_only_predictions": str(STIMULUS_ONLY_PRED),
            "fold_safe_selected": str(FOLD_SAFE_SELECTED),
        },
        "model_import": model_import,
        "cache_audit": cache_audit,
        "alignment": alignment,
        "forward_smoke": forward,
        "issues": issues,
    }

    OUT_JSON.write_text(json.dumps(clean_json(report), indent=2, ensure_ascii=False), encoding="utf-8")
    write_md(report)

    print("ROCA step 05a completed.")
    print(f"status: {status}")
    print(f"wrote: {OUT_MD}")
    print(f"wrote: {OUT_JSON}")
    print()
    print("Cache audit:")
    for item in cache_audit:
        print(
            f"  {item['label']}: shape={item['shape']} rows={item['index_rows']} "
            f"subjects={item['subjects']} stimuli={item['stimuli']} issues={len(item['issues'])}"
        )
    print()
    print("Forward smoke:")
    for item in forward:
        print(
            f"  {item['label']}: input={item['input_shape']} logits={item['logits_shape']} "
            f"z={item['z_shape']} z_proj={item['z_proj_shape']} params={item['total_params']}"
        )
    print()
    print("Issues:")
    if issues:
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("  None")

    return 0 if status == "PASSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
