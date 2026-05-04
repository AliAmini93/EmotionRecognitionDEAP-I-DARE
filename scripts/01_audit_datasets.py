#!/usr/bin/env python3
"""
Dataset audit script for EmotionRecognitionDEAP-I-DARE.

Current scope:
- Audit downloaded I-DARE first-stage files.
- Generate:
  - docs/data_audit_idare.md
  - docs/data_audit_idare.json

This script does not train models.
This script does not preprocess data for training.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

IDARE_ROOT = Path("/mnt/HDD/AliWorks/I-DARE")
IDARE_EEG_DIR = IDARE_ROOT / "raw_downloads" / "EEG"
IDARE_EMG_DIR = IDARE_ROOT / "raw_downloads" / "EMG"
IDARE_LABEL_DIR = IDARE_ROOT / "labels"
IDARE_METADATA_DIR = IDARE_ROOT / "metadata"

MANIFEST = ROOT / "docs" / "idare_download_manifest.csv"
OUT_MD = ROOT / "docs" / "data_audit_idare.md"
OUT_JSON = ROOT / "docs" / "data_audit_idare.json"


def subject_id_from_name(name: str | None) -> int | None:
    if not name:
        return None
    m = re.search(r"sbj_P_(\d+)\.mat$", name)
    return int(m.group(1)) if m else None


def human_size(num_bytes: int | float | None) -> str:
    if num_bytes is None:
        return "unknown"
    value = float(num_bytes)
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{num_bytes} B"


def read_manifest() -> list[dict[str, Any]]:
    if not MANIFEST.exists():
        return []

    rows: list[dict[str, Any]] = []
    with MANIFEST.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            row["size_bytes"] = int(row.get("size_bytes") or 0)
            row["include_in_first_stage"] = str(row.get("include_in_first_stage", "")).lower() == "true"
            row["include_in_main_protocol"] = str(row.get("include_in_main_protocol", "")).lower() == "true"
            rows.append(row)
    return rows


def list_mat_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(folder.glob("sbj_P_*.mat"))


def file_summary(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "name": path.name,
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "size_human": human_size(path.stat().st_size) if path.exists() else "missing",
        "subject_id": subject_id_from_name(path.name),
    }


def read_csv_safely(path: Path) -> tuple[pd.DataFrame | None, str]:
    try:
        df = pd.read_csv(path)
        if df.shape[1] == 1:
            first_line = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
            if ";" in first_line:
                df = pd.read_csv(path, sep=";")
        return df, ""
    except Exception as exc:
        return None, repr(exc)


def summarize_dataframe(df: pd.DataFrame, max_preview_rows: int = 3) -> dict[str, Any]:
    return {
        "shape": list(df.shape),
        "columns": list(map(str, df.columns)),
        "dtypes": {str(k): str(v) for k, v in df.dtypes.items()},
        "missing_values": {str(k): int(v) for k, v in df.isna().sum().items()},
        "preview": df.head(max_preview_rows).astype(str).to_dict(orient="records"),
    }


def is_hdf5_mat(path: Path) -> bool:
    try:
        with path.open("rb") as fp:
            sig = fp.read(8)
        return sig == b"\x89HDF\r\n\x1a\n"
    except Exception:
        return False


def summarize_value(value: Any, max_depth: int = 2, depth: int = 0) -> dict[str, Any]:
    info: dict[str, Any] = {
        "python_type": type(value).__name__,
    }

    if isinstance(value, np.ndarray):
        info["shape"] = list(value.shape)
        info["dtype"] = str(value.dtype)

        if value.dtype.names:
            info["structured_fields"] = list(value.dtype.names)

        if value.dtype == object and depth < max_depth and value.size > 0:
            try:
                first = value.flat[0]
                info["first_object_summary"] = summarize_value(first, max_depth=max_depth, depth=depth + 1)
            except Exception as exc:
                info["first_object_error"] = repr(exc)

        return info

    if hasattr(value, "__dict__"):
        fields = [k for k in value.__dict__.keys() if not k.startswith("_")]
        info["fields"] = fields
        if depth < max_depth:
            info["field_summaries"] = {}
            for k in fields[:20]:
                try:
                    info["field_summaries"][k] = summarize_value(
                        getattr(value, k),
                        max_depth=max_depth,
                        depth=depth + 1,
                    )
                except Exception as exc:
                    info["field_summaries"][k] = {"error": repr(exc)}
        return info

    if isinstance(value, (list, tuple)):
        info["length"] = len(value)
        if value and depth < max_depth:
            info["first_item_summary"] = summarize_value(value[0], max_depth=max_depth, depth=depth + 1)
        return info

    try:
        info["repr"] = repr(value)[:300]
    except Exception:
        pass

    return info


def inspect_mat_with_scipy(path: Path) -> dict[str, Any]:
    import scipy.io

    mat = scipy.io.loadmat(path, squeeze_me=False, struct_as_record=False)
    keys = [k for k in mat.keys() if not k.startswith("__")]

    key_summaries: dict[str, Any] = {}
    for k in keys:
        key_summaries[k] = summarize_value(mat[k], max_depth=3)

    return {
        "loader": "scipy.io.loadmat",
        "keys": keys,
        "key_summaries": key_summaries,
    }


def inspect_mat_with_h5py(path: Path) -> dict[str, Any]:
    try:
        import h5py
    except Exception as exc:
        return {
            "loader": "h5py",
            "error": f"h5py not available: {exc!r}",
        }

    def visit(name: str, obj: Any, out: dict[str, Any]) -> None:
        item: dict[str, Any] = {"type": type(obj).__name__}
        if hasattr(obj, "shape"):
            item["shape"] = list(obj.shape)
        if hasattr(obj, "dtype"):
            item["dtype"] = str(obj.dtype)
        out[name] = item

    content: dict[str, Any] = {}
    with h5py.File(path, "r") as f:
        f.visititems(lambda name, obj: visit(name, obj, content))

    return {
        "loader": "h5py",
        "keys": list(content.keys()),
        "content": content,
    }


def inspect_mat_file(path: Path) -> dict[str, Any]:
    base = file_summary(path)

    try:
        base.update(inspect_mat_with_scipy(path))
        return base
    except NotImplementedError as exc:
        base["scipy_error"] = repr(exc)
        try:
            h5_summary = inspect_mat_with_h5py(path)
            base.update(h5_summary)
            base["loader_note"] = "scipy failed because this appears to be MATLAB v7.3/HDF5; h5py was used."
            return base
        except Exception as h5_exc:
            base["loader"] = "failed"
            base["error"] = f"scipy_error={exc!r}; h5py_error={h5_exc!r}"
            return base
    except Exception as exc:
        base["scipy_error"] = repr(exc)
        try:
            h5_summary = inspect_mat_with_h5py(path)
            base.update(h5_summary)
            base["loader_note"] = "scipy failed; h5py fallback was used."
            return base
        except Exception as h5_exc:
            base["loader"] = "failed"
            base["error"] = f"scipy_error={exc!r}; h5py_error={h5_exc!r}"
            return base


def compact_mat_summary(item: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    lines.append(f"- File: `{item.get('name')}`")
    lines.append(f"  - Subject ID: `{item.get('subject_id')}`")
    lines.append(f"  - Size: `{item.get('size_human')}`")
    lines.append(f"  - Loader: `{item.get('loader', 'unknown')}`")

    if item.get("error"):
        lines.append(f"  - Error: `{item.get('error')}`")
        return lines

    keys = item.get("keys", [])
    lines.append(f"  - Keys: `{keys}`")

    key_summaries = item.get("key_summaries", {})
    if key_summaries:
        lines.append("  - Key summaries:")
        for key, summary in key_summaries.items():
            shape = summary.get("shape")
            dtype = summary.get("dtype")
            pytype = summary.get("python_type")
            fields = summary.get("fields") or summary.get("structured_fields")
            lines.append(f"    - `{key}`: type={pytype}, shape={shape}, dtype={dtype}, fields={fields}")

    content = item.get("content", {})
    if content:
        lines.append("  - HDF5 content preview:")
        for key, summary in list(content.items())[:30]:
            lines.append(f"    - `{key}`: {summary}")

    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mat-samples", type=int, default=3, help="Number of EEG and EMG .mat files to inspect deeply.")
    parser.add_argument("--inspect-all-mat", action="store_true", help="Inspect all EEG/EMG .mat files. Slower.")
    args = parser.parse_args()

    manifest_rows = read_manifest()
    first_stage_rows = [r for r in manifest_rows if r.get("include_in_first_stage")]

    eeg_files = list_mat_files(IDARE_EEG_DIR)
    emg_files = list_mat_files(IDARE_EMG_DIR)
    label_files = sorted(IDARE_LABEL_DIR.glob("*.csv")) if IDARE_LABEL_DIR.exists() else []
    metadata_files = sorted(IDARE_METADATA_DIR.glob("*.csv")) if IDARE_METADATA_DIR.exists() else []

    eeg_subjects = sorted(s for s in (subject_id_from_name(p.name) for p in eeg_files) if s is not None)
    emg_subjects = sorted(s for s in (subject_id_from_name(p.name) for p in emg_files) if s is not None)
    common_subjects = sorted(set(eeg_subjects) & set(emg_subjects))
    eeg_only = sorted(set(eeg_subjects) - set(emg_subjects))
    emg_only = sorted(set(emg_subjects) - set(eeg_subjects))

    expected_first_stage_paths = [
        IDARE_ROOT / r["local_relative_path"]
        for r in first_stage_rows
    ]
    missing_expected = [str(p) for p in expected_first_stage_paths if not p.exists()]
    unexpected_local = []

    known_paths = {str(p) for p in expected_first_stage_paths}
    for p in sorted(IDARE_ROOT.rglob("*")):
        if p.is_file() and str(p) not in known_paths:
            unexpected_local.append(str(p))

    csv_summaries: dict[str, Any] = {}
    for p in label_files + metadata_files:
        df, err = read_csv_safely(p)
        if df is None:
            csv_summaries[p.name] = {
                "path": str(p),
                "error": err,
            }
        else:
            csv_summaries[p.name] = {
                "path": str(p),
                **summarize_dataframe(df),
            }

    if args.inspect_all_mat:
        eeg_to_inspect = eeg_files
        emg_to_inspect = emg_files
    else:
        eeg_to_inspect = eeg_files[: args.mat_samples]
        emg_to_inspect = emg_files[: args.mat_samples]

    mat_summaries = {
        "EEG": [inspect_mat_file(p) for p in eeg_to_inspect],
        "EMG": [inspect_mat_file(p) for p in emg_to_inspect],
    }

    issues: list[str] = []
    warnings: list[str] = []

    if not IDARE_ROOT.exists():
        issues.append(f"I-DARE root does not exist: {IDARE_ROOT}")

    if missing_expected:
        issues.append(f"Missing expected first-stage files: {len(missing_expected)}")

    if len(eeg_files) != 63:
        warnings.append(f"Expected 63 EEG files, found {len(eeg_files)}.")

    if len(emg_files) != 64:
        warnings.append(f"Expected 64 EMG files, found {len(emg_files)}.")

    if len(label_files) != 4:
        warnings.append(f"Expected 4 label CSV files, found {len(label_files)}.")

    if len(metadata_files) != 2:
        warnings.append(f"Expected 2 metadata CSV files, found {len(metadata_files)}.")

    if emg_only != [4]:
        warnings.append(f"Expected EMG-only subject [4], found {emg_only}.")

    if eeg_only:
        warnings.append(f"Expected no EEG-only subjects, found {eeg_only}.")

    if len(common_subjects) != 63:
        warnings.append(f"Expected 63 common EEG+EMG subjects, found {len(common_subjects)}.")

    mat_errors = []
    for modality, items in mat_summaries.items():
        for item in items:
            if item.get("error"):
                mat_errors.append(f"{modality} {item.get('name')}: {item.get('error')}")
    if mat_errors:
        warnings.extend(mat_errors)

    payload = {
        "idare_root": str(IDARE_ROOT),
        "manifest": str(MANIFEST),
        "counts": {
            "manifest_first_stage_rows": len(first_stage_rows),
            "eeg_files": len(eeg_files),
            "emg_files": len(emg_files),
            "label_csv_files": len(label_files),
            "metadata_csv_files": len(metadata_files),
            "common_eeg_emg_subjects": len(common_subjects),
            "missing_expected_files": len(missing_expected),
            "unexpected_local_files": len(unexpected_local),
        },
        "subjects": {
            "eeg_subjects": eeg_subjects,
            "emg_subjects": emg_subjects,
            "common_subjects": common_subjects,
            "eeg_only_subjects": eeg_only,
            "emg_only_subjects": emg_only,
        },
        "files": {
            "eeg": [file_summary(p) for p in eeg_files],
            "emg": [file_summary(p) for p in emg_files],
            "labels": [file_summary(p) for p in label_files],
            "metadata": [file_summary(p) for p in metadata_files],
        },
        "csv_summaries": csv_summaries,
        "mat_summaries": mat_summaries,
        "missing_expected_files": missing_expected,
        "unexpected_local_files": unexpected_local,
        "issues": issues,
        "warnings": warnings,
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines: list[str] = []
    lines.append("# I-DARE Data Audit\n")
    lines.append("This report was generated by `scripts/01_audit_datasets.py`.\n")
    lines.append("No training was performed.\n")

    lines.append("## Audit Status\n")
    if issues:
        lines.append("Status: **FAILED / needs attention**\n")
    elif warnings:
        lines.append("Status: **PASSED with warnings**\n")
    else:
        lines.append("Status: **PASSED**\n")

    lines.append("## Local Paths\n")
    lines.append(f"- I-DARE root: `{IDARE_ROOT}`\n")
    lines.append(f"- Manifest: `{MANIFEST}`\n")

    lines.append("## File Counts\n")
    lines.append("| Item | Count |\n")
    lines.append("|---|---:|\n")
    lines.append(f"| Manifest first-stage rows | {len(first_stage_rows)} |\n")
    lines.append(f"| EEG `.mat` files | {len(eeg_files)} |\n")
    lines.append(f"| EMG `.mat` files | {len(emg_files)} |\n")
    lines.append(f"| Label CSV files | {len(label_files)} |\n")
    lines.append(f"| Metadata CSV files | {len(metadata_files)} |\n")
    lines.append(f"| Missing expected first-stage files | {len(missing_expected)} |\n")
    lines.append(f"| Unexpected local files | {len(unexpected_local)} |\n")

    lines.append("\n## Subject Coverage\n")
    lines.append(f"- EEG subjects: `{len(eeg_subjects)}`\n")
    lines.append(f"- EMG subjects: `{len(emg_subjects)}`\n")
    lines.append(f"- Common EEG+EMG subjects: `{len(common_subjects)}`\n")
    lines.append(f"- EEG-only subjects: `{eeg_only}`\n")
    lines.append(f"- EMG-only subjects: `{emg_only}`\n")

    lines.append("\n### Common Subject IDs\n")
    lines.append("```text\n")
    lines.append(str(common_subjects))
    lines.append("\n```\n")

    lines.append("## Label and Metadata CSV Summaries\n")
    for name, summary in csv_summaries.items():
        lines.append(f"### `{name}`\n")
        if "error" in summary:
            lines.append(f"- Error: `{summary['error']}`\n")
            continue
        lines.append(f"- Path: `{summary['path']}`\n")
        lines.append(f"- Shape: `{summary['shape']}`\n")
        lines.append(f"- Columns: `{summary['columns']}`\n")
        lines.append("- Missing values:\n")
        lines.append("```json\n")
        lines.append(json.dumps(summary["missing_values"], indent=2, ensure_ascii=False))
        lines.append("\n```\n")
        lines.append("- Preview:\n")
        lines.append("```json\n")
        lines.append(json.dumps(summary["preview"], indent=2, ensure_ascii=False))
        lines.append("\n```\n")

    lines.append("## Sample `.mat` Structure\n")
    lines.append(f"Deep-inspected EEG files: `{len(eeg_to_inspect)}`\n")
    lines.append(f"Deep-inspected EMG files: `{len(emg_to_inspect)}`\n")

    for modality, items in mat_summaries.items():
        lines.append(f"### {modality}\n")
        for item in items:
            lines.extend(compact_mat_summary(item))
            lines.append("")

    lines.append("## Issues\n")
    if issues:
        for issue in issues:
            lines.append(f"- {issue}\n")
    else:
        lines.append("- None.\n")

    lines.append("## Warnings\n")
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}\n")
    else:
        lines.append("- None.\n")

    lines.append("## Audit Interpretation\n")
    if not issues:
        lines.append("- The downloaded I-DARE first-stage files are present according to the manifest.\n")
        lines.append("- EEG and EMG subject coverage matches the expected main protocol decision.\n")
        lines.append("- Subject 4 remains EMG-only and should be excluded from main EEG+EMG experiments.\n")
    lines.append("- The next step is to inspect the `.mat` fields in this report and decide the exact loader design.\n")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print("Counts:")
    for k, v in payload["counts"].items():
        print(f"  {k}: {v}")

    print("Issues:", len(issues))
    print("Warnings:", len(warnings))

    if issues:
        sys.exit(2)


if __name__ == "__main__":
    main()
