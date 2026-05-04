#!/usr/bin/env python3
"""
Probe I-DARE .mat files using mat73.

Goal:
- Check whether mat73 can decode MATLAB v7.3 structures better than raw h5py.
- Inspect fields needed for loader design:
  Fs, data, time, channels, channels_type, channels_unit,
  event_begin, event_end, event_id, subject.

This script does not train or preprocess data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mat73
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
IDARE_ROOT = Path("/mnt/HDD/AliWorks/I-DARE")
EEG_DIR = IDARE_ROOT / "raw_downloads" / "EEG"
EMG_DIR = IDARE_ROOT / "raw_downloads" / "EMG"
LABEL_DIR = IDARE_ROOT / "labels"

OUT_MD = ROOT / "docs" / "idare_mat73_probe.md"
OUT_JSON = ROOT / "docs" / "idare_mat73_probe.json"

SAMPLE_SUBJECTS = [1, 2, 3]


def subject_name(subject_id: int) -> str:
    return f"sbj_P_{subject_id:02d}"


def subject_file(folder: Path, subject_id: int) -> Path:
    return folder / f"{subject_name(subject_id)}.mat"


def safe_shape(x: Any) -> list[int] | None:
    try:
        return list(np.asarray(x).shape)
    except Exception:
        return None


def safe_dtype(x: Any) -> str | None:
    try:
        return str(np.asarray(x).dtype)
    except Exception:
        return None


def compact_preview(x: Any, n: int = 10) -> Any:
    try:
        arr = np.asarray(x)
        if arr.dtype == object:
            flat = arr.flatten().tolist()
            return [str(v) for v in flat[:n]]
        flat = arr.flatten()
        return flat[:n].tolist()
    except Exception:
        if isinstance(x, (list, tuple)):
            return [str(v) for v in x[:n]]
        return str(x)[:300]


def read_csv_auto(path: Path) -> pd.DataFrame:
    first_line = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    sep = ";" if ";" in first_line else ","
    df = pd.read_csv(path, sep=sep)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def summarize_csvs() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name in ["Arousal_SAM.csv", "Valence_SAM.csv", "Quadrants_SAM.csv", "Sample.csv"]:
        path = LABEL_DIR / name
        if not path.exists():
            out[name] = {"exists": False}
            continue

        df = read_csv_auto(path)
        item: dict[str, Any] = {
            "exists": True,
            "shape": list(df.shape),
            "columns": list(df.columns),
            "preview": df.head(3).astype(str).to_dict(orient="records"),
        }
        if "Stimulus" in df.columns:
            item["stimulus_count"] = int(df["Stimulus"].nunique())
            item["stimulus_values"] = df["Stimulus"].astype(str).tolist()
        out[name] = item
    return out


def normalize_loaded_subject(obj: Any, sbj: str) -> Any:
    """
    mat73 usually returns a dict with top-level key sbj_P_XX.
    Sometimes it may return the subject dict directly.
    """
    if isinstance(obj, dict) and sbj in obj:
        return obj[sbj]
    return obj


def summarize_subject_file(path: Path, subject_id: int) -> dict[str, Any]:
    sbj = subject_name(subject_id)
    result: dict[str, Any] = {
        "path": str(path),
        "subject": sbj,
        "exists": path.exists(),
    }

    if not path.exists():
        result["error"] = "missing file"
        return result

    try:
        loaded = mat73.loadmat(str(path))
        result["top_level_type"] = type(loaded).__name__
        result["top_level_keys"] = list(loaded.keys()) if isinstance(loaded, dict) else None
        data_obj = normalize_loaded_subject(loaded, sbj)
        result["subject_obj_type"] = type(data_obj).__name__
    except Exception as exc:
        result["error"] = f"mat73.loadmat failed: {exc!r}"
        return result

    if not isinstance(data_obj, dict):
        result["error"] = f"subject object is not dict: {type(data_obj).__name__}"
        result["subject_preview"] = str(data_obj)[:500]
        return result

    result["field_names"] = list(data_obj.keys())
    fields: dict[str, Any] = {}

    for key in [
        "Fs",
        "data",
        "time",
        "channels",
        "channels_type",
        "channels_unit",
        "event_begin",
        "event_end",
        "event_id",
        "subject",
    ]:
        value = data_obj.get(key)
        fields[key] = {
            "present": key in data_obj,
            "type": type(value).__name__,
            "shape": safe_shape(value),
            "dtype": safe_dtype(value),
            "preview": compact_preview(value, n=20),
        }

    result["fields"] = fields

    try:
        fs = float(np.asarray(data_obj["Fs"]).squeeze())
        event_begin = np.asarray(data_obj["event_begin"]).astype(float).squeeze()
        event_end = np.asarray(data_obj["event_end"]).astype(float).squeeze()
        durations_samples = event_end - event_begin
        durations_sec = durations_samples / fs

        event_id = np.asarray(data_obj.get("event_id", [])).squeeze()

        result["derived"] = {
            "fs": fs,
            "data_shape": safe_shape(data_obj.get("data")),
            "time_shape": safe_shape(data_obj.get("time")),
            "event_begin_shape": safe_shape(event_begin),
            "event_end_shape": safe_shape(event_end),
            "event_id_shape": safe_shape(event_id),
            "num_event_begin": int(event_begin.size),
            "num_event_end": int(event_end.size),
            "num_event_id": int(event_id.size),
            "event_id_preview": compact_preview(event_id, n=20),
            "duration_sec_preview": np.round(durations_sec.flatten()[:20], 6).tolist(),
            "duration_sec_unique_rounded": sorted(set(np.round(durations_sec.flatten(), 6).tolist())),
            "num_around_5s_events_4p5_to_5p5": int(((durations_sec >= 4.5) & (durations_sec <= 5.5)).sum()),
            "min_duration_sec": float(np.min(durations_sec)),
            "max_duration_sec": float(np.max(durations_sec)),
        }

        data_arr = np.asarray(data_obj.get("data"))
        time_arr = np.asarray(data_obj.get("time"))
        channels = data_obj.get("channels")
        n_channels = len(channels) if isinstance(channels, (list, tuple)) else None

        guess = "unknown"
        if data_arr.ndim == 2:
            if time_arr.shape[0] == data_arr.shape[0]:
                guess = "time x channels"
            elif time_arr.shape[0] == data_arr.shape[1]:
                guess = "channels x time"
            elif n_channels is not None and data_arr.shape[0] == n_channels:
                guess = "channels x time"
            elif n_channels is not None and data_arr.shape[1] == n_channels:
                guess = "time x channels"

        result["derived"]["data_orientation_guess"] = guess
        result["derived"]["n_channels_from_data"] = int(data_arr.shape[1]) if guess == "time x channels" else None

    except Exception as exc:
        result["derived_error"] = repr(exc)

    return result


def main() -> None:
    payload: dict[str, Any] = {
        "labels": summarize_csvs(),
        "samples": {"EEG": [], "EMG": []},
    }

    for sid in SAMPLE_SUBJECTS:
        payload["samples"]["EEG"].append(summarize_subject_file(subject_file(EEG_DIR, sid), sid))
        payload["samples"]["EMG"].append(summarize_subject_file(subject_file(EMG_DIR, sid), sid))

    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines: list[str] = []
    lines.append("# I-DARE mat73 Loader Probe\n")
    lines.append("This report was generated by `scripts/03_probe_idare_mat73_loader.py`.\n")
    lines.append("No training or preprocessing was performed.\n")

    lines.append("## CSV Label Summary\n")
    for name, item in payload["labels"].items():
        lines.append(f"### `{name}`\n")
        lines.append(f"- Exists: `{item.get('exists')}`\n")
        if item.get("exists"):
            lines.append(f"- Shape: `{item.get('shape')}`\n")
            lines.append(f"- Columns preview: `{item.get('columns', [])[:12]}`\n")
            if "stimulus_count" in item:
                lines.append(f"- Stimulus count: `{item.get('stimulus_count')}`\n")
                lines.append(f"- First 10 stimulus values: `{item.get('stimulus_values', [])[:10]}`\n")

    for modality, items in payload["samples"].items():
        lines.append(f"## {modality} Sample Files\n")
        for item in items:
            lines.append(f"### `{Path(item['path']).name}`\n")
            lines.append(f"- Exists: `{item.get('exists')}`\n")
            if item.get("error"):
                lines.append(f"- Error: `{item['error']}`\n")
                continue

            lines.append(f"- Top-level keys: `{item.get('top_level_keys')}`\n")
            lines.append(f"- Field names: `{item.get('field_names')}`\n")

            lines.append("### Field summaries\n")
            for key, field in item.get("fields", {}).items():
                lines.append(
                    f"- `{key}`: present={field.get('present')}, "
                    f"type={field.get('type')}, shape={field.get('shape')}, "
                    f"dtype={field.get('dtype')}\n"
                )
                lines.append(f"  - preview: `{field.get('preview')}`\n")

            if item.get("derived"):
                lines.append("### Derived summary\n")
                lines.append("```json\n")
                lines.append(json.dumps(item["derived"], indent=2, ensure_ascii=False))
                lines.append("\n```\n")
            if item.get("derived_error"):
                lines.append(f"- Derived error: `{item['derived_error']}`\n")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")

    for modality, items in payload["samples"].items():
        print(modality)
        for item in items:
            d = item.get("derived", {})
            print(
                Path(item["path"]).name,
                "fs=", d.get("fs"),
                "data_shape=", d.get("data_shape"),
                "orientation=", d.get("data_orientation_guess"),
                "num_event_begin=", d.get("num_event_begin"),
                "num_event_id=", d.get("num_event_id"),
                "around_5s=", d.get("num_around_5s_events_4p5_to_5p5"),
                "event_id_preview=", d.get("event_id_preview"),
            )


if __name__ == "__main__":
    main()
