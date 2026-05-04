#!/usr/bin/env python3
"""
Probe I-DARE MATLAB/HDF5 references and event timing.

Goal:
- Inspect MATLAB v7.3 string/object references stored in #refs#.
- Decode or at least identify mappings for:
  channels, channels_type, channels_unit, event_id, subject.
- Inspect Stimuli_Specifications.csv and label CSV alignment.
- Summarize event durations and candidate 5-second events.

This script does not train models.
This script does not preprocess data for training.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
IDARE_ROOT = Path("/mnt/HDD/AliWorks/I-DARE")

EEG_FILE = IDARE_ROOT / "raw_downloads" / "EEG" / "sbj_P_01.mat"
EMG_FILE = IDARE_ROOT / "raw_downloads" / "EMG" / "sbj_P_01.mat"

LABEL_DIR = IDARE_ROOT / "labels"
METADATA_DIR = IDARE_ROOT / "metadata"

OUT_MD = ROOT / "docs" / "idare_refs_and_events_probe.md"
OUT_JSON = ROOT / "docs" / "idare_refs_and_events_probe.json"


REF_MAGIC = 3707764736


def to_python(x: Any) -> Any:
    if isinstance(x, bytes):
        return x.decode("utf-8", errors="replace")
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, np.ndarray):
        if x.size <= 50:
            return x.squeeze().tolist()
        return {
            "shape": list(x.shape),
            "dtype": str(x.dtype),
            "preview": x.flatten()[:20].tolist(),
        }
    return x


def attrs_to_dict(obj: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        for k, v in obj.attrs.items():
            out[str(k)] = to_python(np.array(v) if not isinstance(v, bytes) else v)
    except Exception as exc:
        out["attrs_error"] = repr(exc)
    return out


def decode_uint_chars(arr: np.ndarray) -> str:
    arr = np.asarray(arr).squeeze()
    chars = []
    for x in arr.flatten(order="F"):
        try:
            code = int(x)
            if code != 0:
                chars.append(chr(code))
        except Exception:
            pass
    return "".join(chars)


def dataset_preview(ds: h5py.Dataset, max_items: int = 40) -> dict[str, Any]:
    info: dict[str, Any] = {
        "type": "Dataset",
        "shape": list(ds.shape),
        "dtype": str(ds.dtype),
        "attrs": attrs_to_dict(ds),
    }

    try:
        arr = np.asarray(ds[()])
        if arr.size <= max_items:
            info["values"] = arr.squeeze().tolist()
        else:
            info["preview"] = arr.flatten()[:max_items].tolist()

        if arr.dtype.kind in {"u", "i"}:
            decoded = decode_uint_chars(arr)
            if decoded:
                info["uint_char_decode"] = decoded[:1000]
    except Exception as exc:
        info["read_error"] = repr(exc)

    return info


def object_preview(obj: Any, max_items: int = 40) -> dict[str, Any]:
    if isinstance(obj, h5py.Dataset):
        return dataset_preview(obj, max_items=max_items)

    if isinstance(obj, h5py.Group):
        return {
            "type": "Group",
            "keys": list(obj.keys()),
            "attrs": attrs_to_dict(obj),
        }

    return {"type": type(obj).__name__, "repr": repr(obj)[:500]}


def matlab_object_ref_candidate(raw: np.ndarray) -> dict[str, Any]:
    arr = np.asarray(raw).astype("uint64").flatten()
    out = {
        "raw": arr.tolist(),
        "is_candidate": False,
        "ref_index_guess": None,
        "ref_name_guess": None,
    }

    if arr.size >= 5 and int(arr[0]) == REF_MAGIC:
        ref_index = int(arr[4])
        out["is_candidate"] = True
        out["ref_index_guess"] = ref_index
        if 1 <= ref_index <= 26:
            out["ref_name_guess"] = chr(ord("a") + ref_index - 1)

    return out


def inspect_file(path: Path, group_name: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "group_name": group_name,
        "exists": path.exists(),
    }

    if not path.exists():
        result["error"] = "missing file"
        return result

    with h5py.File(path, "r") as f:
        result["top_keys"] = list(f.keys())
        result["top_attrs"] = attrs_to_dict(f)

        refs = f.get("#refs#")
        if refs is not None:
            result["refs_keys"] = list(refs.keys())
            result["refs"] = {}
            for key in refs.keys():
                result["refs"][key] = object_preview(refs[key], max_items=80)

        if group_name not in f:
            result["error"] = f"group not found: {group_name}"
            return result

        g = f[group_name]
        result["group_keys"] = list(g.keys())
        result["fields"] = {}

        for field in ["Fs", "data", "time", "channels", "channels_type", "channels_unit", "event_begin", "event_end", "event_id", "subject"]:
            if field not in g:
                result["fields"][field] = {"missing": True}
                continue

            obj = g[field]
            item = object_preview(obj, max_items=80)

            if isinstance(obj, h5py.Dataset):
                try:
                    raw = np.asarray(obj[()])
                    if raw.size <= 20 and raw.dtype.kind in {"u", "i"}:
                        item["matlab_object_ref_candidate"] = matlab_object_ref_candidate(raw)
                        ref_name = item["matlab_object_ref_candidate"].get("ref_name_guess")
                        if ref_name and refs is not None and ref_name in refs:
                            item["referenced_object_preview"] = object_preview(refs[ref_name], max_items=120)
                except Exception as exc:
                    item["candidate_error"] = repr(exc)

            result["fields"][field] = item

        # Event timing summary.
        try:
            fs = float(np.asarray(g["Fs"][()]).squeeze())
            event_begin = np.asarray(g["event_begin"][()]).astype(float).squeeze()
            event_end = np.asarray(g["event_end"][()]).astype(float).squeeze()
            durations = (event_end - event_begin) / fs

            table = []
            for idx, (b, e, d) in enumerate(zip(event_begin, event_end, durations), start=1):
                table.append({
                    "event_index_1based": idx,
                    "event_begin": float(b),
                    "event_end": float(e),
                    "duration_sec": float(d),
                    "is_around_5s_4p5_to_5p5": bool(4.5 <= d <= 5.5),
                })

            result["event_timing"] = {
                "fs": fs,
                "num_events": int(len(table)),
                "num_around_5s_4p5_to_5p5": int(sum(x["is_around_5s_4p5_to_5p5"] for x in table)),
                "duration_unique_rounded": sorted(set(np.round(durations, 6).tolist())),
                "events_first_40": table[:40],
                "around_5s_event_indices_1based": [x["event_index_1based"] for x in table if x["is_around_5s_4p5_to_5p5"]],
            }

            data_shape = list(g["data"].shape)
            time_shape = list(g["time"].shape)
            result["data_orientation_raw_h5py"] = {
                "data_shape": data_shape,
                "time_shape": time_shape,
                "guess": "time x channels" if len(data_shape) == 2 and data_shape[0] == time_shape[0] else "unknown",
            }

        except Exception as exc:
            result["event_timing_error"] = repr(exc)

    return result


def read_csv_auto(path: Path) -> pd.DataFrame:
    first_line = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    sep = ";" if ";" in first_line else ","
    df = pd.read_csv(path, sep=sep)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def csv_probe() -> dict[str, Any]:
    out: dict[str, Any] = {}

    for rel in [
        LABEL_DIR / "Arousal_SAM.csv",
        LABEL_DIR / "Valence_SAM.csv",
        LABEL_DIR / "Quadrants_SAM.csv",
        LABEL_DIR / "Sample.csv",
        METADATA_DIR / "Stimuli_Specifications.csv",
        METADATA_DIR / "Agreement_Raters.csv",
    ]:
        item: dict[str, Any] = {"path": str(rel), "exists": rel.exists()}
        if rel.exists():
            df = read_csv_auto(rel)
            item["shape"] = list(df.shape)
            item["columns"] = list(df.columns)
            item["preview"] = df.head(10).astype(str).to_dict(orient="records")

            if "Stimulus" in df.columns:
                item["stimulus_values"] = df["Stimulus"].astype(str).tolist()
                item["stimulus_count"] = int(df["Stimulus"].nunique())

            if rel.name == "Stimuli_Specifications.csv":
                for subj_col in ["sbj_P_01", "sbj_P_02", "sbj_P_03"]:
                    if subj_col in df.columns:
                        s = df[subj_col].astype(str).str.strip()
                        non_empty = df.loc[(s != "") & (s.str.lower() != "nan"), ["Stimulus", "Description", subj_col]]
                        item[f"{subj_col}_non_empty_count"] = int(len(non_empty))
                        item[f"{subj_col}_non_empty_preview"] = non_empty.head(40).astype(str).to_dict(orient="records")

        out[rel.name] = item

    # Cross-check label stimuli.
    try:
        arousal = read_csv_auto(LABEL_DIR / "Arousal_SAM.csv")
        valence = read_csv_auto(LABEL_DIR / "Valence_SAM.csv")
        specs = read_csv_auto(METADATA_DIR / "Stimuli_Specifications.csv")

        label_stimuli = set(arousal["Stimulus"].astype(str))
        valence_stimuli = set(valence["Stimulus"].astype(str))
        specs_stimuli = set(specs["Stimulus"].astype(str))

        out["stimulus_crosscheck"] = {
            "arousal_count": len(label_stimuli),
            "valence_count": len(valence_stimuli),
            "specs_count": len(specs_stimuli),
            "arousal_equals_valence": label_stimuli == valence_stimuli,
            "labels_subset_of_specs": label_stimuli.issubset(specs_stimuli),
            "label_stimuli_not_in_specs": sorted(label_stimuli - specs_stimuli),
            "specs_stimuli_not_in_labels_count": len(specs_stimuli - label_stimuli),
            "label_stimuli_sorted": sorted(label_stimuli),
        }
    except Exception as exc:
        out["stimulus_crosscheck_error"] = repr(exc)

    return out


def main() -> None:
    payload = {
        "files": {
            "EEG_sbj_P_01": inspect_file(EEG_FILE, "sbj_P_01"),
            "EMG_sbj_P_01": inspect_file(EMG_FILE, "sbj_P_01"),
        },
        "csvs": csv_probe(),
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    lines = []
    lines.append("# I-DARE MATLAB References and Event Probe\n")
    lines.append("This report was generated by `scripts/04_probe_idare_refs_and_events.py`.\n")
    lines.append("No training or preprocessing was performed.\n")

    lines.append("## CSV / Stimulus Cross-check\n")
    cross = payload["csvs"].get("stimulus_crosscheck", {})
    lines.append("```json\n")
    lines.append(json.dumps(cross, indent=2, ensure_ascii=False, default=str))
    lines.append("\n```\n")

    for name in ["Stimuli_Specifications.csv", "Arousal_SAM.csv", "Valence_SAM.csv", "Quadrants_SAM.csv", "Agreement_Raters.csv"]:
        item = payload["csvs"].get(name, {})
        lines.append(f"### `{name}`\n")
        lines.append(f"- Exists: `{item.get('exists')}`\n")
        if item.get("exists"):
            lines.append(f"- Shape: `{item.get('shape')}`\n")
            lines.append(f"- Columns preview: `{item.get('columns', [])[:15]}`\n")
            if item.get("stimulus_count") is not None:
                lines.append(f"- Stimulus count: `{item.get('stimulus_count')}`\n")
                lines.append(f"- First 10 stimulus values: `{item.get('stimulus_values', [])[:10]}`\n")
            if name == "Stimuli_Specifications.csv":
                for subj_col in ["sbj_P_01", "sbj_P_02", "sbj_P_03"]:
                    lines.append(f"- `{subj_col}` non-empty count: `{item.get(subj_col + '_non_empty_count')}`\n")
                    lines.append(f"- `{subj_col}` non-empty preview:\n")
                    lines.append("```json\n")
                    lines.append(json.dumps(item.get(subj_col + "_non_empty_preview", [])[:10], indent=2, ensure_ascii=False, default=str))
                    lines.append("\n```\n")

    for file_key, info in payload["files"].items():
        lines.append(f"## HDF5 File: `{file_key}`\n")
        lines.append(f"- Path: `{info.get('path')}`\n")
        lines.append(f"- Top keys: `{info.get('top_keys')}`\n")
        lines.append(f"- Group keys: `{info.get('group_keys')}`\n")
        lines.append(f"- Refs keys: `{info.get('refs_keys')}`\n")

        lines.append("### Raw data orientation\n")
        lines.append("```json\n")
        lines.append(json.dumps(info.get("data_orientation_raw_h5py"), indent=2, ensure_ascii=False, default=str))
        lines.append("\n```\n")

        lines.append("### Event timing summary\n")
        lines.append("```json\n")
        lines.append(json.dumps(info.get("event_timing"), indent=2, ensure_ascii=False, default=str))
        lines.append("\n```\n")

        lines.append("### Field reference candidates\n")
        for field in ["subject", "channels", "channels_type", "channels_unit", "event_id"]:
            field_info = info.get("fields", {}).get(field, {})
            candidate = field_info.get("matlab_object_ref_candidate")
            lines.append(f"#### `{field}`\n")
            lines.append("```json\n")
            lines.append(json.dumps({
                "field": field,
                "shape": field_info.get("shape"),
                "dtype": field_info.get("dtype"),
                "attrs": field_info.get("attrs"),
                "values": field_info.get("values"),
                "candidate": candidate,
                "referenced_object_preview": field_info.get("referenced_object_preview"),
            }, indent=2, ensure_ascii=False, default=str))
            lines.append("\n```\n")

        lines.append("### `#refs#` object previews\n")
        refs = info.get("refs", {})
        for ref_name, ref_info in refs.items():
            lines.append(f"#### `#refs#/{ref_name}`\n")
            lines.append("```json\n")
            lines.append(json.dumps(ref_info, indent=2, ensure_ascii=False, default=str))
            lines.append("\n```\n")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")

    for file_key, info in payload["files"].items():
        print(file_key)
        print("  raw orientation:", info.get("data_orientation_raw_h5py"))
        et = info.get("event_timing", {})
        print("  num_events:", et.get("num_events"))
        print("  around_5s:", et.get("num_around_5s_4p5_to_5p5"))
        print("  refs:", info.get("refs_keys"))
        for field in ["subject", "channels", "channels_type", "channels_unit", "event_id"]:
            candidate = info.get("fields", {}).get(field, {}).get("matlab_object_ref_candidate")
            print(" ", field, candidate)

    print("stimulus crosscheck:", payload["csvs"].get("stimulus_crosscheck"))


if __name__ == "__main__":
    main()
