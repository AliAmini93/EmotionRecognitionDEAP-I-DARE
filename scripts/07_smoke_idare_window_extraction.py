#!/usr/bin/env python3
"""
Smoke-test I-DARE window extraction from the generated trial index.

Inputs:
- .cache/idare_trial_index.csv
- /mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/*.mat
- /mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/*.mat

Outputs:
- docs/idare_window_extraction_smoke_test.md
- docs/idare_window_extraction_smoke_test.json
- .cache/idare_window_smoke_sample.npz

This script does not train models.
This script does not create the final dataset cache.
It only validates real signal slicing from the downloaded I-DARE files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd
from scipy.signal import resample_poly


ROOT = Path(__file__).resolve().parents[1]
TRIAL_INDEX = ROOT / ".cache" / "idare_trial_index.csv"

OUT_MD = ROOT / "docs" / "idare_window_extraction_smoke_test.md"
OUT_JSON = ROOT / "docs" / "idare_window_extraction_smoke_test.json"
OUT_NPZ = ROOT / ".cache" / "idare_window_smoke_sample.npz"

N_ROWS = 8
EEG_MODEL_CHANNELS = 32
TARGET_EEG_FS = 128.0


def as_python_scalar(x: Any) -> Any:
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    return x


def read_h5_subject_group(path: Path) -> tuple[h5py.File, h5py.Group]:
    h5 = h5py.File(path, "r")
    groups = [k for k in h5.keys() if not k.startswith("#")]
    if len(groups) != 1:
        h5.close()
        raise RuntimeError(f"Expected exactly one subject group in {path}, found {groups}")
    return h5, h5[groups[0]]


def read_fs(group: h5py.Group) -> float:
    return float(np.array(group["Fs"]).squeeze())


def load_data_shape(path: Path) -> dict[str, Any]:
    with h5py.File(path, "r") as h5:
        groups = [k for k in h5.keys() if not k.startswith("#")]
        group = h5[groups[0]]
        data = group["data"]
        time = group["time"]
        fs = float(np.array(group["Fs"]).squeeze())
        return {
            "path": str(path),
            "group": groups[0],
            "fs": fs,
            "data_shape": list(data.shape),
            "time_shape": list(time.shape),
        }


def slice_half_open(data: h5py.Dataset, begin_raw: float, end_raw: float) -> np.ndarray:
    """
    Candidate convention selected for smoke testing:
    use raw begin/end as Python half-open slice boundaries.

    This yields sample_count = end_raw - begin_raw, matching the duration formula
    used in scripts/06_build_idare_trial_index.py.
    """
    start = int(round(begin_raw))
    stop = int(round(end_raw))
    return np.asarray(data[start:stop, :])


def slice_matlab_1based_inclusive(data: h5py.Dataset, begin_raw: float, end_raw: float) -> np.ndarray:
    """
    Alternative convention for comparison only:
    interpret raw begin/end as MATLAB 1-based inclusive indices.
    """
    start = int(round(begin_raw)) - 1
    stop = int(round(end_raw))
    return np.asarray(data[start:stop, :])


def summarize_window(row: pd.Series) -> dict[str, Any]:
    eeg_path = Path(str(row["eeg_file"]))
    emg_path = Path(str(row["emg_file"]))

    eeg_h5, eeg_group = read_h5_subject_group(eeg_path)
    emg_h5, emg_group = read_h5_subject_group(emg_path)

    try:
        eeg_data = eeg_group["data"]
        emg_data = emg_group["data"]

        eeg_fs = read_fs(eeg_group)
        emg_fs = read_fs(emg_group)

        eeg_half = slice_half_open(eeg_data, row["eeg_begin_raw"], row["eeg_end_raw"])
        emg_half = slice_half_open(emg_data, row["emg_begin_raw"], row["emg_end_raw"])

        eeg_1based = slice_matlab_1based_inclusive(eeg_data, row["eeg_begin_raw"], row["eeg_end_raw"])
        emg_1based = slice_matlab_1based_inclusive(emg_data, row["emg_begin_raw"], row["emg_end_raw"])

        # EEG data is time x channels in raw HDF5. Convert selected first 32 channels
        # to channels x time for the current EEGSegmentClassifier-style input.
        eeg_32_ch_time = eeg_half[:, :EEG_MODEL_CHANNELS].T

        if eeg_fs == TARGET_EEG_FS:
            eeg_32_resampled = eeg_32_ch_time
        else:
            # I-DARE EEG is 512Hz in probes. 512 -> 128 is exactly /4.
            # resample_poly keeps channel axis unchanged and resamples time axis.
            eeg_32_resampled = resample_poly(
                eeg_32_ch_time,
                up=int(TARGET_EEG_FS),
                down=int(eeg_fs),
                axis=1,
            )

        # Keep only a tiny preview to avoid large committed artifacts.
        return {
            "subject_id": int(row["subject_id"]),
            "stimulus_id": str(row["stimulus_id"]),
            "raw_event_name": str(row["raw_event_name"]),
            "event_index_1based": int(row["event_index_1based"]),
            "valence_score": as_python_scalar(row["valence_score"]),
            "arousal_score": as_python_scalar(row["arousal_score"]),
            "valence_label_gt5": None if pd.isna(row["valence_label_gt5"]) else int(row["valence_label_gt5"]),
            "arousal_label_gt5": None if pd.isna(row["arousal_label_gt5"]) else int(row["arousal_label_gt5"]),
            "valence_is_discard_score5": bool(row["valence_is_discard_score5"]),
            "arousal_is_discard_score5": bool(row["arousal_is_discard_score5"]),
            "eeg": {
                "file": str(eeg_path),
                "fs": eeg_fs,
                "raw_data_shape": list(eeg_data.shape),
                "begin_raw": float(row["eeg_begin_raw"]),
                "end_raw": float(row["eeg_end_raw"]),
                "trial_index_duration_samples": float(row["eeg_duration_samples"]),
                "trial_index_duration_sec": float(row["eeg_duration_sec"]),
                "half_open_shape_time_x_channels": list(eeg_half.shape),
                "half_open_duration_sec": eeg_half.shape[0] / eeg_fs,
                "matlab_1based_inclusive_shape_time_x_channels": list(eeg_1based.shape),
                "matlab_1based_inclusive_duration_sec": eeg_1based.shape[0] / eeg_fs,
                "model_candidate_first32_shape_channels_x_time": list(eeg_32_ch_time.shape),
                "model_candidate_first32_resampled_128hz_shape_channels_x_time": list(eeg_32_resampled.shape),
                "model_candidate_first32_resampled_128hz_duration_sec": eeg_32_resampled.shape[1] / TARGET_EEG_FS,
            },
            "emg": {
                "file": str(emg_path),
                "fs": emg_fs,
                "raw_data_shape": list(emg_data.shape),
                "begin_raw": float(row["emg_begin_raw"]),
                "end_raw": float(row["emg_end_raw"]),
                "trial_index_duration_samples": float(row["emg_duration_samples"]),
                "trial_index_duration_sec": float(row["emg_duration_sec"]),
                "half_open_shape_time_x_channels": list(emg_half.shape),
                "half_open_duration_sec": emg_half.shape[0] / emg_fs,
                "matlab_1based_inclusive_shape_time_x_channels": list(emg_1based.shape),
                "matlab_1based_inclusive_duration_sec": emg_1based.shape[0] / emg_fs,
            },
            "preview_values": {
                "eeg_first_channel_first_10": [float(x) for x in eeg_half[:10, 0]],
                "emg_first_channel_first_10": [float(x) for x in emg_half[:10, 0]],
            },
            "_arrays_for_npz": {
                "eeg_32_resampled": eeg_32_resampled.astype(np.float32),
                "emg_half": emg_half.astype(np.float32),
            },
        }
    finally:
        eeg_h5.close()
        emg_h5.close()


def main() -> None:
    if not TRIAL_INDEX.exists():
        raise SystemExit(
            f"Missing {TRIAL_INDEX}. Run: python scripts/06_build_idare_trial_index.py"
        )

    df = pd.read_csv(TRIAL_INDEX)

    # Choose subject 1 rows where possible, then take first N_ROWS.
    sample_df = df[df["subject_id"] == 1].head(N_ROWS).copy()
    if sample_df.empty:
        sample_df = df.head(N_ROWS).copy()

    windows = [summarize_window(row) for _, row in sample_df.iterrows()]

    issues: list[str] = []
    warnings: list[str] = []

    for item in windows:
        eeg = item["eeg"]
        emg = item["emg"]

        if eeg["half_open_shape_time_x_channels"][1] < EEG_MODEL_CHANNELS:
            issues.append(f"{item['subject_id']} {item['stimulus_id']}: EEG has fewer than {EEG_MODEL_CHANNELS} channels")

        if not (630 <= eeg["model_candidate_first32_resampled_128hz_shape_channels_x_time"][1] <= 650):
            issues.append(
                f"{item['subject_id']} {item['stimulus_id']}: resampled EEG length is not near 640 samples"
            )

        if emg["half_open_shape_time_x_channels"][1] != 2:
            warnings.append(f"{item['subject_id']} {item['stimulus_id']}: EMG channel count is not 2")

    chosen_slicing = {
        "candidate": "raw begin/end as Python half-open slices: data[int(begin):int(end), :]",
        "reason": (
            "This convention gives sample_count = end - begin, matching the duration "
            "stored in .cache/idare_trial_index.csv."
        ),
        "note": (
            "The MATLAB 1-based inclusive convention gives one extra sample. "
            "The final loader can revisit this, but the half-open convention is the clean "
            "working choice for the first extraction implementation."
        ),
    }

    payload = {
        "trial_index": str(TRIAL_INDEX),
        "output_npz": str(OUT_NPZ),
        "n_sample_rows": len(windows),
        "chosen_slicing": chosen_slicing,
        "target_eeg_fs": TARGET_EEG_FS,
        "eeg_model_channels": EEG_MODEL_CHANNELS,
        "issues": issues,
        "warnings": warnings,
        "windows": [
            {k: v for k, v in item.items() if k != "_arrays_for_npz"}
            for item in windows
        ],
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    # Save one small example array pair for manual inspection.
    if windows:
        first = windows[0]["_arrays_for_npz"]
        OUT_NPZ.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            OUT_NPZ,
            eeg_32ch_128hz=first["eeg_32_resampled"],
            emg_raw=first["emg_half"],
        )

    lines: list[str] = []
    lines.append("# I-DARE Window Extraction Smoke Test\n")
    lines.append("This report was generated by `scripts/07_smoke_idare_window_extraction.py`.\n")
    lines.append("No model training was performed.\n")
    lines.append("No final processed dataset was created.\n")

    status = "PASSED" if not issues else "FAILED"
    if warnings and not issues:
        status = "PASSED with warnings"

    lines.append("## Status\n")
    lines.append(f"Status: **{status}**\n")
    lines.append("## Inputs / Outputs\n")
    lines.append(f"- Trial index: `{TRIAL_INDEX}`\n")
    lines.append(f"- JSON report: `{OUT_JSON}`\n")
    lines.append(f"- Small sample NPZ: `{OUT_NPZ}`\n")
    lines.append("## Chosen Slicing Convention\n")
    lines.append("```json\n")
    lines.append(json.dumps(chosen_slicing, indent=2))
    lines.append("\n```\n")

    lines.append("## Summary\n")
    lines.append(f"- Sample rows tested: `{len(windows)}`\n")
    lines.append(f"- Target EEG model channels: `{EEG_MODEL_CHANNELS}`\n")
    lines.append(f"- Target EEG sampling rate after resampling: `{TARGET_EEG_FS}`\n")
    lines.append(f"- Issues: `{len(issues)}`\n")
    lines.append(f"- Warnings: `{len(warnings)}`\n")

    lines.append("## Window Summaries\n")
    for item in payload["windows"]:
        lines.append(f"### Subject {item['subject_id']} - `{item['stimulus_id']}`\n")
        lines.append(f"- Raw event: `{item['raw_event_name']}`\n")
        lines.append(f"- Event index 1-based: `{item['event_index_1based']}`\n")
        lines.append(f"- Valence score / label: `{item['valence_score']}` / `{item['valence_label_gt5']}`\n")
        lines.append(f"- Arousal score / label: `{item['arousal_score']}` / `{item['arousal_label_gt5']}`\n")

        lines.append("#### EEG\n")
        lines.append("```json\n")
        lines.append(json.dumps(item["eeg"], indent=2, default=str))
        lines.append("\n```\n")

        lines.append("#### EMG\n")
        lines.append("```json\n")
        lines.append(json.dumps(item["emg"], indent=2, default=str))
        lines.append("\n```\n")

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

    lines.append("## Next Step\n")
    lines.append(
        "- If this smoke test passes, implement reusable I-DARE window extraction / dataset loader code.\n"
    )
    lines.append(
        "- The first model-facing EEG input candidate is 32 channels × 640 samples after 512Hz to 128Hz resampling.\n"
    )
    lines.append(
        "- EMG should remain feature-level in the main protocol, so the next loader step should compute window-level EMG features rather than pass raw EMG to the main model.\n"
    )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_MD}")
    print(f"Wrote: {OUT_JSON}")
    print(f"Wrote: {OUT_NPZ}")
    print(f"Status: {status}")
    print(f"Sample rows tested: {len(windows)}")
    print(f"Issues: {len(issues)}")
    print(f"Warnings: {len(warnings)}")


if __name__ == "__main__":
    main()
