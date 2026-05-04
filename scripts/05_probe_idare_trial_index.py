#!/usr/bin/env python3
"""
Probe I-DARE trial/event indexing.

Goal:
- Confirm that Stimuli_Specifications.csv rows align with event_begin/event_end order.
- Extract STIM_* emotional stimulus events.
- Match STIM_* suffixes to Valence_SAM.csv and Arousal_SAM.csv.
- Produce a loader-design-ready trial index preview.

This script does not train models.
This script does not write processed datasets.
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
METADATA_DIR = IDARE_ROOT / "metadata"

OUT_MD = ROOT / "docs" / "idare_trial_index_probe.md"
OUT_JSON = ROOT / "docs" / "idare_trial_index_probe.json"

SAMPLE_SUBJECTS = [1, 2, 3]
COMMON_SUBJECTS = [
    1, 2, 3, 5, 6, 7, 8, 9, 10,
    11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
    31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
    41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
    52, 53, 54, 55, 56, 57, 58, 59, 60,
    61, 62, 63, 64, 65,
]


def subject_col(subject_id: int) -> str:
    return f"sbj_P_{subject_id:02d}"


def subject_name(subject_id: int) -> str:
    return f"sbj_P_{subject_id:02d}"


def read_csv_auto(path: Path) -> pd.DataFrame:
    first_line = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    sep = ";" if ";" in first_line else ","
    df = pd.read_csv(path, sep=sep)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def normalize_stimulus_id(value: Any) -> str:
    s = str(value).strip()
    for prefix in ["STIM_", "BSL_", "SAM_"]:
        if s.startswith(prefix):
            return s[len(prefix):]
    return s


def load_event_arrays(path: Path, group_name: str) -> dict[str, Any]:
    with h5py.File(path, "r") as f:
        g = f[group_name]
        fs = float(np.asarray(g["Fs"][()]).squeeze())
        data_shape = list(g["data"].shape)
        time_shape = list(g["time"].shape)
        begin = np.asarray(g["event_begin"][()]).astype(float).squeeze()
        end = np.asarray(g["event_end"][()]).astype(float).squeeze()
        durations = (end - begin) / fs

    return {
        "fs": fs,
        "data_shape": data_shape,
        "time_shape": time_shape,
        "event_begin": begin.tolist(),
        "event_end": end.tolist(),
        "duration_sec": durations.tolist(),
        "num_events": int(len(begin)),
    }


def build_label_maps() -> dict[str, dict[str, Any]]:
    valence = read_csv_auto(LABEL_DIR / "Valence_SAM.csv")
    arousal = read_csv_auto(LABEL_DIR / "Arousal_SAM.csv")
    quadrants = read_csv_auto(LABEL_DIR / "Quadrants_SAM.csv")

    maps: dict[str, dict[str, Any]] = {}

    for _, row in valence.iterrows():
        stim = normalize_stimulus_id(row["Stimulus"])
        maps.setdefault(stim, {})["stimulus_id"] = stim
        maps[stim]["valence"] = {}

        for col in valence.columns:
            if col == "Stimulus":
                continue
            maps[stim]["valence"][col.strip()] = row[col]

    for _, row in arousal.iterrows():
        stim = normalize_stimulus_id(row["Stimulus"])
        maps.setdefault(stim, {})["stimulus_id"] = stim
        maps[stim]["arousal"] = {}

        for col in arousal.columns:
            if col == "Stimulus":
                continue
            maps[stim]["arousal"][col.strip()] = row[col]

    for _, row in quadrants.iterrows():
        stim = normalize_stimulus_id(row["Stimulus"])
        maps.setdefault(stim, {})["stimulus_id"] = stim
        maps[stim]["quadrant_gs"] = row.get("Quadrant (GS)")
        maps[stim]["quadrant_subject"] = {}

        for col in quadrants.columns:
            if col in {"Stimulus", "Quadrant (GS)"}:
                continue
            maps[stim]["quadrant_subject"][col.strip()] = row[col]

    return maps


def score_to_binary(value: Any) -> int | None:
    try:
        x = float(value)
    except Exception:
        return None
    if x == 5:
        return None
    return 1 if x > 5 else 0


def build_subject_trial_preview(subject_id: int, specs: pd.DataFrame, label_maps: dict[str, dict[str, Any]]) -> dict[str, Any]:
    col = subject_col(subject_id)
    group = subject_name(subject_id)

    eeg_events = load_event_arrays(EEG_DIR / f"{group}.mat", group)
    emg_events = load_event_arrays(EMG_DIR / f"{group}.mat", group) if (EMG_DIR / f"{group}.mat").exists() else None

    stim_rows = []
    all_rows = []

    for i, row in specs.iterrows():
        event_index_1based = i + 1
        raw_event_name = str(row["Stimulus"]).strip()
        stimulus_id = normalize_stimulus_id(raw_event_name)
        desc = str(row.get("Description", "")).strip()
        is_stim_event = raw_event_name.startswith("STIM_")
        is_labeled = stimulus_id in label_maps

        eeg_duration = float(eeg_events["duration_sec"][i])
        emg_duration = float(emg_events["duration_sec"][i]) if emg_events else None

        item = {
            "subject_id": subject_id,
            "subject_col": col,
            "event_index_1based": event_index_1based,
            "raw_event_name": raw_event_name,
            "stimulus_id": stimulus_id,
            "description": desc,
            "is_stim_event": is_stim_event,
            "is_labeled": is_labeled,
            "metadata_duration_sec": row.get(col),
            "eeg_begin": eeg_events["event_begin"][i],
            "eeg_end": eeg_events["event_end"][i],
            "eeg_duration_sec": eeg_duration,
            "emg_begin": emg_events["event_begin"][i] if emg_events else None,
            "emg_end": emg_events["event_end"][i] if emg_events else None,
            "emg_duration_sec": emg_duration,
        }

        if is_labeled:
            labels = label_maps[stimulus_id]
            val = labels.get("valence", {}).get(col)
            aro = labels.get("arousal", {}).get(col)
            item["valence_score"] = val
            item["arousal_score"] = aro
            item["valence_binary_gt5_discard5"] = score_to_binary(val)
            item["arousal_binary_gt5_discard5"] = score_to_binary(aro)
            item["quadrant_gs"] = labels.get("quadrant_gs")
            item["quadrant_subject"] = labels.get("quadrant_subject", {}).get(col)

        all_rows.append(item)
        if is_stim_event:
            stim_rows.append(item)

    labeled_stim_rows = [x for x in stim_rows if x["is_labeled"]]

    return {
        "subject_id": subject_id,
        "eeg_event_summary": {
            "fs": eeg_events["fs"],
            "data_shape": eeg_events["data_shape"],
            "time_shape": eeg_events["time_shape"],
            "num_events": eeg_events["num_events"],
        },
        "emg_event_summary": {
            "fs": emg_events["fs"] if emg_events else None,
            "data_shape": emg_events["data_shape"] if emg_events else None,
            "time_shape": emg_events["time_shape"] if emg_events else None,
            "num_events": emg_events["num_events"] if emg_events else None,
        },
        "all_rows_count": len(all_rows),
        "stim_rows_count": len(stim_rows),
        "labeled_stim_rows_count": len(labeled_stim_rows),
        "stim_rows_preview": stim_rows[:12],
        "labeled_stim_rows_preview": labeled_stim_rows[:12],
        "all_stimulus_ids": [x["stimulus_id"] for x in labeled_stim_rows],
        "duration_checks": {
            "all_labeled_stim_eeg_4p5_to_5p5": all(4.5 <= float(x["eeg_duration_sec"]) <= 5.5 for x in labeled_stim_rows),
            "all_labeled_stim_emg_4p5_to_5p5": all(4.5 <= float(x["emg_duration_sec"]) <= 5.5 for x in labeled_stim_rows if x["emg_duration_sec"] is not None),
            "eeg_labeled_stim_min_duration": min(float(x["eeg_duration_sec"]) for x in labeled_stim_rows),
            "eeg_labeled_stim_max_duration": max(float(x["eeg_duration_sec"]) for x in labeled_stim_rows),
            "emg_labeled_stim_min_duration": min(float(x["emg_duration_sec"]) for x in labeled_stim_rows if x["emg_duration_sec"] is not None),
            "emg_labeled_stim_max_duration": max(float(x["emg_duration_sec"]) for x in labeled_stim_rows if x["emg_duration_sec"] is not None),
        },
    }


def main() -> None:
    specs = read_csv_auto(METADATA_DIR / "Stimuli_Specifications.csv")
    label_maps = build_label_maps()

    specs_stim_ids = [
        normalize_stimulus_id(x)
        for x in specs["Stimulus"].astype(str).tolist()
        if str(x).strip().startswith("STIM_")
    ]
    label_stim_ids = sorted(label_maps.keys())

    samples = {
        subject_name(s): build_subject_trial_preview(s, specs, label_maps)
        for s in SAMPLE_SUBJECTS
    }

    payload = {
        "summary": {
            "specs_rows": int(len(specs)),
            "specs_stim_rows": int(len(specs_stim_ids)),
            "label_stimuli": int(len(label_stim_ids)),
            "stim_rows_match_label_stimuli": set(specs_stim_ids) == set(label_stim_ids),
            "specs_stim_ids_sorted": sorted(specs_stim_ids),
            "label_stim_ids_sorted": label_stim_ids,
            "common_subject_count": len(COMMON_SUBJECTS),
            "sample_subjects": SAMPLE_SUBJECTS,
        },
        "samples": samples,
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    lines = []
    lines.append("# I-DARE Trial Index Probe\n")
    lines.append("This report was generated by `scripts/05_probe_idare_trial_index.py`.\n")
    lines.append("No training or preprocessing was performed.\n")

    lines.append("## Summary\n")
    lines.append("```json\n")
    lines.append(json.dumps(payload["summary"], indent=2, ensure_ascii=False, default=str))
    lines.append("\n```\n")

    lines.append("## Loader Interpretation\n")
    lines.append("- `Stimuli_Specifications.csv` has 100 rows.\n")
    lines.append("- Each subject `.mat` file has 100 event begin/end pairs.\n")
    lines.append("- Rows appear to align with event indices in order.\n")
    lines.append("- Main emotional trials should use `STIM_*` rows only.\n")
    lines.append("- Label CSV files store stimulus IDs without the `STIM_` prefix.\n")
    lines.append("- Therefore, loader should map `STIM_<id>` to label stimulus `<id>`.\n")

    for name, item in samples.items():
        lines.append(f"## Subject `{name}`\n")
        lines.append("### Event summaries\n")
        lines.append("```json\n")
        lines.append(json.dumps({
            "eeg": item["eeg_event_summary"],
            "emg": item["emg_event_summary"],
            "all_rows_count": item["all_rows_count"],
            "stim_rows_count": item["stim_rows_count"],
            "labeled_stim_rows_count": item["labeled_stim_rows_count"],
            "duration_checks": item["duration_checks"],
        }, indent=2, ensure_ascii=False, default=str))
        lines.append("\n```\n")

        lines.append("### Labeled STIM row preview\n")
        lines.append("```json\n")
        lines.append(json.dumps(item["labeled_stim_rows_preview"], indent=2, ensure_ascii=False, default=str))
        lines.append("\n```\n")

    lines.append("## Candidate Loader Decision\n")
    lines.append("Use the following candidate design unless later evidence contradicts it:\n")
    lines.append("1. Load I-DARE `.mat` files with `h5py`.\n")
    lines.append("2. Use data orientation as `time x channels`.\n")
    lines.append("3. Use `Stimuli_Specifications.csv` row order as the event order.\n")
    lines.append("4. Keep only rows whose `Stimulus` starts with `STIM_`.\n")
    lines.append("5. Strip `STIM_` to match label CSV stimulus IDs.\n")
    lines.append("6. Extract one natural stimulus window per STIM event.\n")
    lines.append("7. EEG: resample from 512Hz to 128Hz later for model input.\n")
    lines.append("8. EMG: extract window-level features from 2000Hz EMG.\n")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print("summary:")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False, default=str))
    for name, item in samples.items():
        print(name)
        print("  stim_rows_count:", item["stim_rows_count"])
        print("  labeled_stim_rows_count:", item["labeled_stim_rows_count"])
        print("  duration_checks:", item["duration_checks"])


if __name__ == "__main__":
    main()
