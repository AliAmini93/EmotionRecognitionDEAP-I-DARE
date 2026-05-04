#!/usr/bin/env python3
"""
Build I-DARE trial index.

Goal:
- Create one clean row per subject × emotional STIM trial.
- Use only the 63 common EEG+EMG subjects.
- Use only STIM_* events from Stimuli_Specifications.csv.
- Map STIM_<id> to label stimulus <id>.
- Attach EEG/EMG event boundaries and valence/arousal labels.

Outputs:
- .cache/idare_trial_index.csv
- docs/idare_trial_index_summary.md
- docs/idare_trial_index_summary.json

This script does not train models.
This script does not extract signal windows.
"""

from __future__ import annotations

import json
from collections import Counter
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

OUT_DIR = ROOT / ".cache"
OUT_CSV = OUT_DIR / "idare_trial_index.csv"
OUT_SUMMARY_MD = ROOT / "docs" / "idare_trial_index_summary.md"
OUT_SUMMARY_JSON = ROOT / "docs" / "idare_trial_index_summary.json"

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


def subject_file(folder: Path, subject_id: int) -> Path:
    return folder / f"{subject_col(subject_id)}.mat"


def read_csv_normalized(path: Path) -> pd.DataFrame:
    """Read I-DARE CSV files robustly and normalize column names/cell strings."""
    read_attempts = [
        {"sep": ",", "engine": "python"},
        {"sep": ";", "engine": "python"},
        {"sep": None, "engine": "python"},
    ]

    last_error: Exception | None = None
    df: pd.DataFrame | None = None

    for kwargs in read_attempts:
        try:
            candidate = pd.read_csv(path, dtype=str, encoding="utf-8-sig", **kwargs)
            candidate.columns = [
                str(c).replace("\ufeff", "").replace("\xa0", " ").strip()
                for c in candidate.columns
            ]

            # Accept the first parse that exposes a usable Stimulus column.
            if "Stimulus" in candidate.columns:
                df = candidate
                break

            # If pandas parsed the whole header as one column, try the next separator.
            if candidate.shape[1] > 1 and df is None:
                df = candidate

        except Exception as exc:
            last_error = exc

    if df is None:
        raise RuntimeError(f"Could not read CSV file {path}. Last error: {last_error!r}")

    # Final normalization.
    df.columns = [
        str(c).replace("\ufeff", "").replace("\xa0", " ").strip()
        for c in df.columns
    ]

    # Some files may contain accidental trailing spaces in subject columns.
    normalized_columns = {}
    for col in df.columns:
        normalized_columns[col] = str(col).strip()
    df = df.rename(columns=normalized_columns)

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].map(
                lambda x: x.replace("\ufeff", "").replace("\xa0", " ").strip()
                if isinstance(x, str)
                else x
            )

    if "Stimulus" not in df.columns:
        raise KeyError(
            f"Column 'Stimulus' not found in {path}. "
            f"Parsed columns are: {list(df.columns)}"
        )

    return df


def parse_int(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if text == "":
        return None
    return int(float(text))


def parse_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    if text == "":
        return None
    return float(text)


def binary_gt5(score: int | None) -> int | None:
    if score is None:
        return None
    if score == 5:
        return None
    return 1 if score > 5 else 0


def mat_info(path: Path, subject_id: int) -> dict[str, Any]:
    key = subject_col(subject_id)

    with h5py.File(path, "r") as h:
        if key not in h:
            raise KeyError(f"{key} not found in {path}")

        group = h[key]
        fs = float(np.asarray(group["Fs"]).squeeze())
        data_shape = list(group["data"].shape)
        time_shape = list(group["time"].shape)
        event_begin = np.asarray(group["event_begin"]).reshape(-1).astype(float)
        event_end = np.asarray(group["event_end"]).reshape(-1).astype(float)

    return {
        "path": str(path),
        "fs": fs,
        "data_shape": data_shape,
        "time_shape": time_shape,
        "event_begin": event_begin,
        "event_end": event_end,
        "num_events": int(len(event_begin)),
    }


def score_counts(rows: list[dict[str, Any]], score_field: str, label_field: str) -> dict[str, Any]:
    scores = [r[score_field] for r in rows if r[score_field] is not None]
    labels = [r[label_field] for r in rows if r[label_field] is not None]

    return {
        "n_total_rows": len(rows),
        "n_scores_present": len(scores),
        "score_counts": {str(k): int(v) for k, v in sorted(Counter(scores).items())},
        "n_score_eq_5_discard": int(sum(1 for x in scores if x == 5)),
        "binary_label_counts_after_discard": {str(k): int(v) for k, v in sorted(Counter(labels).items())},
        "n_rows_after_discard": int(len(labels)),
    }


def duration_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    vals = [float(r[field]) for r in rows if r[field] is not None]
    return {
        "min": min(vals) if vals else None,
        "max": max(vals) if vals else None,
        "mean": sum(vals) / len(vals) if vals else None,
        "all_4p5_to_5p5": all(4.5 <= v <= 5.5 for v in vals) if vals else False,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    specs = read_csv_normalized(METADATA_DIR / "Stimuli_Specifications.csv")
    valence = read_csv_normalized(LABEL_DIR / "Valence_SAM.csv")
    arousal = read_csv_normalized(LABEL_DIR / "Arousal_SAM.csv")
    quadrants = read_csv_normalized(LABEL_DIR / "Quadrants_SAM.csv")

    valence_by_stim = valence.set_index("Stimulus")
    arousal_by_stim = arousal.set_index("Stimulus")
    quadrants_by_stim = quadrants.set_index("Stimulus")

    stim_rows = specs[specs["Stimulus"].str.startswith("STIM_", na=False)].copy()
    label_stimuli = set(valence["Stimulus"].astype(str))
    stim_ids = [x.replace("STIM_", "", 1) for x in stim_rows["Stimulus"].astype(str)]

    issues: list[str] = []
    warnings: list[str] = []

    if len(stim_rows) != 32:
        issues.append(f"Expected 32 STIM rows, found {len(stim_rows)}.")

    if set(stim_ids) != label_stimuli:
        issues.append("STIM stimulus IDs do not exactly match Valence_SAM stimulus IDs.")

    rows: list[dict[str, Any]] = []

    for subject_id in COMMON_SUBJECTS:
        col = subject_col(subject_id)

        eeg_file = subject_file(EEG_DIR, subject_id)
        emg_file = subject_file(EMG_DIR, subject_id)

        if not eeg_file.exists():
            issues.append(f"Missing EEG file for subject {subject_id}: {eeg_file}")
            continue

        if not emg_file.exists():
            issues.append(f"Missing EMG file for subject {subject_id}: {emg_file}")
            continue

        eeg = mat_info(eeg_file, subject_id)
        emg = mat_info(emg_file, subject_id)

        if eeg["num_events"] != len(specs):
            issues.append(f"Subject {subject_id}: EEG event count {eeg['num_events']} != specs rows {len(specs)}.")

        if emg["num_events"] != len(specs):
            issues.append(f"Subject {subject_id}: EMG event count {emg['num_events']} != specs rows {len(specs)}.")

        for event_index_0based, spec_row in stim_rows.iterrows():
            raw_event_name = str(spec_row["Stimulus"])
            stimulus_id = raw_event_name.replace("STIM_", "", 1)

            if stimulus_id not in valence_by_stim.index:
                issues.append(f"Missing valence label for stimulus {stimulus_id}.")
                continue

            if stimulus_id not in arousal_by_stim.index:
                issues.append(f"Missing arousal label for stimulus {stimulus_id}.")
                continue

            valence_score = parse_int(valence_by_stim.loc[stimulus_id, col])
            arousal_score = parse_int(arousal_by_stim.loc[stimulus_id, col])

            quadrant_gs = None
            quadrant_subject = None
            if stimulus_id in quadrants_by_stim.index:
                if "Quadrant (GS)" in quadrants_by_stim.columns:
                    quadrant_gs = quadrants_by_stim.loc[stimulus_id, "Quadrant (GS)"]
                if col in quadrants_by_stim.columns:
                    quadrant_subject = quadrants_by_stim.loc[stimulus_id, col]

            eeg_begin = float(eeg["event_begin"][event_index_0based])
            eeg_end = float(eeg["event_end"][event_index_0based])
            emg_begin = float(emg["event_begin"][event_index_0based])
            emg_end = float(emg["event_end"][event_index_0based])

            eeg_duration_sec = (eeg_end - eeg_begin) / eeg["fs"]
            emg_duration_sec = (emg_end - emg_begin) / emg["fs"]

            rows.append({
                "subject_id": subject_id,
                "subject_col": col,
                "stimulus_id": stimulus_id,
                "raw_event_name": raw_event_name,
                "event_index_0based": int(event_index_0based),
                "event_index_1based": int(event_index_0based + 1),
                "description": spec_row.get("Description"),
                "metadata_duration_sec": parse_float(spec_row.get(col)),
                "eeg_file": str(eeg_file),
                "emg_file": str(emg_file),
                "eeg_fs": eeg["fs"],
                "emg_fs": emg["fs"],
                "eeg_data_shape": json.dumps(eeg["data_shape"]),
                "emg_data_shape": json.dumps(emg["data_shape"]),
                "eeg_begin_raw": eeg_begin,
                "eeg_end_raw": eeg_end,
                "eeg_duration_samples": eeg_end - eeg_begin,
                "eeg_duration_sec": eeg_duration_sec,
                "emg_begin_raw": emg_begin,
                "emg_end_raw": emg_end,
                "emg_duration_samples": emg_end - emg_begin,
                "emg_duration_sec": emg_duration_sec,
                "valence_score": valence_score,
                "arousal_score": arousal_score,
                "valence_label_gt5": binary_gt5(valence_score),
                "arousal_label_gt5": binary_gt5(arousal_score),
                "valence_is_discard_score5": valence_score == 5,
                "arousal_is_discard_score5": arousal_score == 5,
                "quadrant_gs": quadrant_gs,
                "quadrant_subject": quadrant_subject,
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    trials_per_subject = df.groupby("subject_id").size().to_dict() if not df.empty else {}

    summary = {
        "output_csv": str(OUT_CSV),
        "n_rows": int(len(df)),
        "n_subjects": int(df["subject_id"].nunique()) if not df.empty else 0,
        "expected_subjects": len(COMMON_SUBJECTS),
        "expected_rows": len(COMMON_SUBJECTS) * 32,
        "trials_per_subject_min": int(min(trials_per_subject.values())) if trials_per_subject else None,
        "trials_per_subject_max": int(max(trials_per_subject.values())) if trials_per_subject else None,
        "unique_stimuli": int(df["stimulus_id"].nunique()) if not df.empty else 0,
        "valence": score_counts(rows, "valence_score", "valence_label_gt5"),
        "arousal": score_counts(rows, "arousal_score", "arousal_label_gt5"),
        "eeg_duration_sec": duration_summary(rows, "eeg_duration_sec"),
        "emg_duration_sec": duration_summary(rows, "emg_duration_sec"),
        "issues": issues,
        "warnings": warnings,
    }

    if summary["n_rows"] != summary["expected_rows"]:
        summary["issues"].append(
            f"Expected {summary['expected_rows']} rows, got {summary['n_rows']}."
        )

    if summary["trials_per_subject_min"] != 32 or summary["trials_per_subject_max"] != 32:
        summary["issues"].append("Not every subject has exactly 32 STIM trials.")

    OUT_SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    md: list[str] = []
    md.append("# I-DARE Trial Index Summary\n")
    md.append("This report was generated by `scripts/06_build_idare_trial_index.py`.\n")
    md.append("No model training was performed.\n")
    md.append("No signal windows were extracted.\n")

    md.append("## Outputs\n")
    md.append(f"- Trial index CSV: `{OUT_CSV}`\n")
    md.append(f"- Summary JSON: `{OUT_SUMMARY_JSON}`\n")
    md.append(f"- Summary Markdown: `{OUT_SUMMARY_MD}`\n")

    md.append("## Core Counts\n")
    md.append("| Item | Value |\n")
    md.append("|---|---:|\n")
    for key in [
        "n_rows",
        "n_subjects",
        "expected_subjects",
        "expected_rows",
        "trials_per_subject_min",
        "trials_per_subject_max",
        "unique_stimuli",
    ]:
        md.append(f"| {key} | {summary[key]} |\n")

    md.append("\n## Valence Label Summary\n")
    md.append("```json\n")
    md.append(json.dumps(summary["valence"], indent=2, ensure_ascii=False))
    md.append("\n```\n")

    md.append("\n## Arousal Label Summary\n")
    md.append("```json\n")
    md.append(json.dumps(summary["arousal"], indent=2, ensure_ascii=False))
    md.append("\n```\n")

    md.append("\n## Duration Checks\n")
    md.append("```json\n")
    md.append(json.dumps({
        "eeg_duration_sec": summary["eeg_duration_sec"],
        "emg_duration_sec": summary["emg_duration_sec"],
    }, indent=2, ensure_ascii=False))
    md.append("\n```\n")

    md.append("\n## Issues\n")
    if summary["issues"]:
        for issue in summary["issues"]:
            md.append(f"- {issue}\n")
    else:
        md.append("- None.\n")

    md.append("\n## Warnings\n")
    if summary["warnings"]:
        for warning in summary["warnings"]:
            md.append(f"- {warning}\n")
    else:
        md.append("- None.\n")

    md.append("\n## Loader Notes\n")
    md.append("- Use only `STIM_*` rows as emotional trials.\n")
    md.append("- Strip the `STIM_` prefix to match label CSV stimulus IDs.\n")
    md.append("- Use the 63 common EEG+EMG subjects for the main I-DARE protocol.\n")
    md.append("- `score == 5` is marked as discard separately for valence and arousal.\n")
    md.append("- Raw event begin/end values are preserved. The exact Python slicing convention should be finalized during window extraction.\n")

    OUT_SUMMARY_MD.write_text("".join(md), encoding="utf-8")

    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_SUMMARY_MD}")
    print(f"Wrote: {OUT_SUMMARY_JSON}")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
