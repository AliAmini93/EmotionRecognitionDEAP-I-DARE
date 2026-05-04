#!/usr/bin/env python3
"""
Probe I-DARE MATLAB v7.3 / HDF5 file structure.

This script inspects selected EEG/EMG subject files and generates:
- docs/idare_hdf5_structure_probe.md
- docs/idare_hdf5_structure_probe.json

It does not train models.
It does not write processed datasets.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
IDARE_ROOT = Path("/mnt/HDD/AliWorks/I-DARE")
EEG_DIR = IDARE_ROOT / "raw_downloads" / "EEG"
EMG_DIR = IDARE_ROOT / "raw_downloads" / "EMG"
LABEL_DIR = IDARE_ROOT / "labels"
OUT_MD = ROOT / "docs" / "idare_hdf5_structure_probe.md"
OUT_JSON = ROOT / "docs" / "idare_hdf5_structure_probe.json"


SAMPLE_SUBJECTS = [1, 2, 3]


def subject_name(subject_id: int) -> str:
    return f"sbj_P_{subject_id:02d}"


def subject_file(folder: Path, subject_id: int) -> Path:
    return folder / f"{subject_name(subject_id)}.mat"


def safe_scalar(x: Any) -> Any:
    arr = np.array(x)
    arr = np.squeeze(arr)
    if arr.size == 1:
        value = arr.item()
        if isinstance(value, np.generic):
            value = value.item()
        return value
    return arr.tolist()


def decode_uint16_chars(arr: np.ndarray) -> str:
    arr = np.array(arr).squeeze()
    chars = []
    for x in arr.flatten():
        try:
            code = int(x)
            if code != 0:
                chars.append(chr(code))
        except Exception:
            pass
    return "".join(chars)


def decode_hdf5_value(f: h5py.File, obj: Any, max_items: int = 200) -> Any:
    """
    Best-effort decoder for MATLAB v7.3 strings/cell arrays/numeric arrays.
    """
    if isinstance(obj, h5py.Reference):
        if not obj:
            return None
        return decode_hdf5_value(f, f[obj], max_items=max_items)

    if isinstance(obj, h5py.Dataset):
        data = obj[()]
        arr = np.array(data)

        if arr.dtype.kind in {"U", "S"}:
            return arr.astype(str).tolist()

        if arr.dtype == object:
            out = []
            for ref in arr.flatten()[:max_items]:
                out.append(decode_hdf5_value(f, ref, max_items=max_items))
            return out

        # MATLAB char arrays are often uint16.
        if arr.dtype.kind in {"u", "i"} and arr.ndim >= 1:
            if arr.size > 0 and arr.size < 500:
                decoded = decode_uint16_chars(arr)
                # Return string only when it looks textual.
                if decoded and sum(ch.isprintable() for ch in decoded) / max(len(decoded), 1) > 0.8:
                    return decoded

        if arr.size <= max_items:
            return arr.squeeze().tolist()

        return {
            "shape": list(arr.shape),
            "dtype": str(arr.dtype),
            "preview": arr.flatten()[:10].tolist(),
        }

    if isinstance(obj, h5py.Group):
        return {
            "group_keys": list(obj.keys())
        }

    return str(obj)


def dataset_info(ds: h5py.Dataset) -> dict[str, Any]:
    info = {
        "shape": list(ds.shape),
        "dtype": str(ds.dtype),
    }
    try:
        if np.prod(ds.shape) <= 20:
            info["values"] = np.array(ds[()]).squeeze().tolist()
        else:
            sample = np.array(ds[()])
            info["min"] = float(np.nanmin(sample)) if np.issubdtype(sample.dtype, np.number) else None
            info["max"] = float(np.nanmax(sample)) if np.issubdtype(sample.dtype, np.number) else None
    except Exception as exc:
        info["read_error"] = repr(exc)
    return info


def extract_group_probe(path: Path, subject_id: int) -> dict[str, Any]:
    sbj = subject_name(subject_id)

    result: dict[str, Any] = {
        "path": str(path),
        "subject": sbj,
        "exists": path.exists(),
    }

    if not path.exists():
        result["error"] = "file missing"
        return result

    with h5py.File(path, "r") as f:
        if sbj not in f:
            result["error"] = f"group {sbj} not found"
            result["top_keys"] = list(f.keys())
            return result

        g = f[sbj]
        result["group_keys"] = list(g.keys())

        for key in ["Fs", "data", "time", "event_begin", "event_end", "event_id", "channels", "channels_type", "channels_unit", "subject"]:
            if key not in g:
                result[key] = {"missing": True}
                continue

            obj = g[key]
            if isinstance(obj, h5py.Dataset):
                result[key] = dataset_info(obj)
                if key in {"Fs", "event_begin", "event_end", "event_id", "channels", "channels_type", "channels_unit", "subject"}:
                    try:
                        result[key]["decoded"] = decode_hdf5_value(f, obj)
                    except Exception as exc:
                        result[key]["decode_error"] = repr(exc)
            else:
                result[key] = {"type": type(obj).__name__, "keys": list(obj.keys())}

        # Derived event info.
        try:
            fs = float(np.array(g["Fs"][()]).squeeze())
            event_begin = np.array(decode_hdf5_value(f, g["event_begin"])).astype(float).flatten()
            event_end = np.array(decode_hdf5_value(f, g["event_end"])).astype(float).flatten()
            event_id = np.array(decode_hdf5_value(f, g["event_id"])).flatten()

            durations_samples = event_end - event_begin
            durations_sec = durations_samples / fs

            result["derived"] = {
                "fs": fs,
                "num_events": int(len(event_id)),
                "event_id_preview": event_id[:10].astype(str).tolist(),
                "event_begin_preview": event_begin[:10].tolist(),
                "event_end_preview": event_end[:10].tolist(),
                "duration_samples_preview": durations_samples[:10].tolist(),
                "duration_sec_preview": durations_sec[:10].tolist(),
                "duration_sec_unique_rounded": sorted(set(np.round(durations_sec, 6).tolist())),
                "min_duration_sec": float(np.min(durations_sec)),
                "max_duration_sec": float(np.max(durations_sec)),
            }
        except Exception as exc:
            result["derived_error"] = repr(exc)

        # Data orientation guess.
        try:
            data_shape = tuple(g["data"].shape)
            time_shape = tuple(g["time"].shape)
            channels_decoded = decode_hdf5_value(f, g["channels"])
            n_channels = len(channels_decoded) if isinstance(channels_decoded, list) else None

            result["data_orientation_guess"] = {
                "data_shape": list(data_shape),
                "time_shape": list(time_shape),
                "n_decoded_channels": n_channels,
                "guess": None,
            }

            if n_channels is not None:
                if len(data_shape) == 2 and data_shape[0] == n_channels:
                    result["data_orientation_guess"]["guess"] = "channels x time"
                elif len(data_shape) == 2 and data_shape[1] == n_channels:
                    result["data_orientation_guess"]["guess"] = "time x channels"
                else:
                    result["data_orientation_guess"]["guess"] = "unknown"
        except Exception as exc:
            result["data_orientation_error"] = repr(exc)

    return result


def read_label_stimuli() -> dict[str, Any]:
    out = {}
    for name in ["Arousal_SAM.csv", "Valence_SAM.csv", "Quadrants_SAM.csv"]:
        path = LABEL_DIR / name
        if not path.exists():
            out[name] = {"exists": False}
            continue
        df = pd.read_csv(path)
        df.columns = [str(c).strip() for c in df.columns]
        out[name] = {
            "exists": True,
            "shape": list(df.shape),
            "columns_preview": list(df.columns[:10]),
            "stimulus_values": df["Stimulus"].astype(str).tolist() if "Stimulus" in df.columns else [],
            "stimulus_count": int(df["Stimulus"].nunique()) if "Stimulus" in df.columns else None,
        }
    return out


def main() -> None:
    payload = {
        "samples": {
            "EEG": [],
            "EMG": [],
        },
        "labels": read_label_stimuli(),
    }

    for subject_id in SAMPLE_SUBJECTS:
        payload["samples"]["EEG"].append(extract_group_probe(subject_file(EEG_DIR, subject_id), subject_id))
        payload["samples"]["EMG"].append(extract_group_probe(subject_file(EMG_DIR, subject_id), subject_id))

    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("# I-DARE HDF5 Structure Probe\n")
    lines.append("This report was generated by `scripts/02_probe_idare_hdf5_structure.py`.\n")
    lines.append("No training or preprocessing was performed.\n")

    lines.append("## Label Stimulus Summary\n")
    for name, item in payload["labels"].items():
        lines.append(f"### `{name}`\n")
        lines.append(f"- Exists: `{item.get('exists')}`\n")
        if item.get("exists"):
            lines.append(f"- Shape: `{item.get('shape')}`\n")
            lines.append(f"- Stimulus count: `{item.get('stimulus_count')}`\n")
            lines.append(f"- First 10 stimulus values: `{item.get('stimulus_values', [])[:10]}`\n")

    for modality, items in payload["samples"].items():
        lines.append(f"## {modality} Sample Files\n")
        for item in items:
            lines.append(f"### `{Path(item['path']).name}`\n")
            lines.append(f"- Subject: `{item.get('subject')}`\n")
            lines.append(f"- Exists: `{item.get('exists')}`\n")
            if item.get("error"):
                lines.append(f"- Error: `{item.get('error')}`\n")
                continue

            lines.append(f"- Group keys: `{item.get('group_keys')}`\n")

            for key in ["Fs", "data", "time", "event_begin", "event_end", "event_id", "channels", "channels_type", "channels_unit", "subject"]:
                value = item.get(key, {})
                lines.append(f"- `{key}`: shape={value.get('shape')}, dtype={value.get('dtype')}\n")
                if "decoded" in value:
                    decoded = value["decoded"]
                    if isinstance(decoded, list):
                        preview = decoded[:20]
                    else:
                        preview = decoded
                    lines.append(f"  - decoded preview: `{preview}`\n")

            if item.get("data_orientation_guess"):
                lines.append("- Data orientation guess:\n")
                lines.append("```json\n")
                lines.append(json.dumps(item["data_orientation_guess"], indent=2, ensure_ascii=False))
                lines.append("\n```\n")

            if item.get("derived"):
                lines.append("- Derived event summary:\n")
                lines.append("```json\n")
                lines.append(json.dumps(item["derived"], indent=2, ensure_ascii=False))
                lines.append("\n```\n")
            elif item.get("derived_error"):
                lines.append(f"- Derived event error: `{item.get('derived_error')}`\n")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")

    for modality, items in payload["samples"].items():
        print(modality)
        for item in items:
            print(
                Path(item["path"]).name,
                "data=",
                item.get("data", {}).get("shape"),
                "Fs=",
                item.get("Fs", {}).get("decoded"),
                "events=",
                item.get("derived", {}).get("num_events"),
                "duration_unique=",
                item.get("derived", {}).get("duration_sec_unique_rounded"),
                "orientation=",
                item.get("data_orientation_guess", {}).get("guess"),
            )


if __name__ == "__main__":
    main()
