#!/usr/bin/env python3
"""
Audit whether I-DARE EEG per-stimulus baseline correction is feasible.

This script is diagnostic only.

It does not:
- train a model
- build a cache
- modify cache files
- load raw MATLAB/HDF5 `.mat` files

It reads:
- Stimuli_Specifications.csv
- .cache/idare_eeg_cache_index.csv

Main questions:
1. Does every cached/labeled STIM_<id> have a matching BSL_<id> row?
2. Is the matching BSL_<id> immediately before STIM_<id>?
3. Are BSL/STIM durations sane and close to ~5 seconds?
4. Does the current cache index contain explicit evidence of baseline correction?
5. Is a future baseline-corrected cache feasible without touching training loops?
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_INDEX = ROOT / ".cache" / "idare_eeg_cache_index.csv"
DEFAULT_OUT_MD = ROOT / "docs" / "idare_baseline_correction_audit.md"
DEFAULT_OUT_JSON = ROOT / "docs" / "idare_baseline_correction_audit.json"

STIMULI_SPECS_CANDIDATES = [
    ROOT / "data" / "idare" / "Stimuli_Specifications.csv",
    ROOT / "data" / "I-DARE" / "Stimuli_Specifications.csv",
    ROOT / "datasets" / "I-DARE" / "Stimuli_Specifications.csv",
    Path("/mnt/HDD/AliWorks/I-DARE/Stimuli_Specifications.csv"),
    Path("/mnt/HDD/AliWorks/I-DARE/metadata/Stimuli_Specifications.csv"),
    Path("/mnt/HDD/AliWorks/I-DARE/raw_downloads/Stimuli_Specifications.csv"),
    Path("/mnt/HDD/AliWorks/I-DARE/raw_downloads/Metadata/Stimuli_Specifications.csv"),
    Path("/mnt/HDD/AliWorks/I-DARE/raw_downloads/metadata/Stimuli_Specifications.csv"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stimuli-specs",
        type=Path,
        default=None,
        help="Optional explicit path to Stimuli_Specifications.csv.",
    )
    parser.add_argument(
        "--cache-index",
        type=Path,
        default=DEFAULT_CACHE_INDEX,
        help="Path to I-DARE EEG cache index CSV.",
    )
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument(
        "--search-root",
        type=Path,
        default=Path("/mnt/HDD/AliWorks/I-DARE"),
        help="Fallback root to search for Stimuli_Specifications.csv if candidates fail.",
    )
    return parser.parse_args()


def read_stimuli_specs_csv(path: Path) -> pd.DataFrame:
    """Read I-DARE Stimuli_Specifications.csv with delimiter auto-detection.

    Some metadata copies are semicolon-separated. If read with the default comma
    separator, pandas sees the whole header as one giant column. This helper
    prevents that silent schema mistake.
    """
    try:
        df = pd.read_csv(path, sep=None, engine="python")
    except Exception:
        df = pd.read_csv(path, sep=";")

    if len(df.columns) == 1 and ";" in str(df.columns[0]):
        df = pd.read_csv(path, sep=";")

    df.columns = [str(c).strip().lstrip("\ufeff") for c in df.columns]
    return df


def find_stimuli_specs(explicit: Path | None, search_root: Path) -> tuple[Path, list[str]]:
    notes: list[str] = []

    if explicit is not None:
        if explicit.exists():
            return explicit, [f"explicit path exists: {explicit}"]
        raise FileNotFoundError(f"--stimuli-specs does not exist: {explicit}")

    for candidate in STIMULI_SPECS_CANDIDATES:
        if candidate.exists():
            notes.append(f"found candidate: {candidate}")
            return candidate, notes

    if search_root.exists():
        matches = sorted(search_root.rglob("Stimuli_Specifications.csv"))
        notes.append(f"searched {search_root}, matches={len(matches)}")
        if matches:
            return matches[0], notes + [f"using first match: {matches[0]}"]

    raise FileNotFoundError(
        "Could not find Stimuli_Specifications.csv. Pass --stimuli-specs explicitly."
    )


def as_clean_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def looks_like_event_name(value: str) -> bool:
    return (
        value.startswith(("STIM_", "BSL_", "SAM_", "IST_"))
        or value in {"BSL", "EYC"}
    )


def find_stimulus_event_column(df: pd.DataFrame) -> str:
    """Find the column containing event names such as STIM_*, BSL_*, SAM_*."""
    preferred = [
        "Stimulus",
        "stimulus",
        "Stimuli",
        "stimuli",
        "Event",
        "event",
        "EventName",
        "event_name",
        "Name",
        "name",
        "label",
        "Label",
    ]

    for col in preferred:
        if col in df.columns:
            values = df[col].map(as_clean_str).tolist()
            hits = sum(1 for value in values if looks_like_event_name(value))
            if hits > 0:
                return str(col)

    best_col: str | None = None
    best_hits = -1

    for col in df.columns:
        values = df[col].map(as_clean_str).tolist()
        hits = sum(1 for value in values if looks_like_event_name(value))
        if hits > best_hits:
            best_hits = hits
            best_col = str(col)

    if best_col is not None and best_hits > 0:
        return best_col

    preview = {
        str(col): [as_clean_str(v) for v in df[col].head(5).tolist()]
        for col in df.columns[:12]
    }
    raise ValueError(
        "Could not identify event/stimulus column in Stimuli_Specifications.csv. "
        f"Columns={list(map(str, df.columns))}. Preview={preview}"
    )


def event_kind(name: str) -> str:
    if name.startswith("STIM_"):
        return "STIM"
    if name.startswith("BSL_"):
        return "BSL_STIM"
    if name == "BSL":
        return "BSL_GLOBAL"
    if name == "EYC":
        return "EYC"
    if name.startswith("SAM_"):
        return "SAM"
    if name.startswith("IST_"):
        return "INSTRUCTION"
    return "OTHER"


def stimulus_id_from_event(name: str) -> str | None:
    if name.startswith("STIM_"):
        return name[len("STIM_") :]
    if name.startswith("BSL_"):
        return name[len("BSL_") :]
    if name.startswith("SAM_"):
        return name[len("SAM_") :]
    return None


def find_subject_duration_cols(df: pd.DataFrame) -> list[str]:
    cols: list[str] = []
    for col in df.columns:
        c = str(col)
        if c.startswith("sbj_P_"):
            cols.append(c)
    return cols


def numeric_duration_summary(row: pd.Series | None, duration_cols: list[str]) -> dict[str, Any]:
    if row is None or not duration_cols:
        return {
            "n": 0,
            "missing": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
        }

    values = pd.to_numeric(row[duration_cols], errors="coerce")
    clean = values.dropna()
    if clean.empty:
        return {
            "n": 0,
            "missing": int(len(values)),
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
        }

    return {
        "n": int(clean.shape[0]),
        "missing": int(values.isna().sum()),
        "mean": float(clean.mean()),
        "median": float(clean.median()),
        "min": float(clean.min()),
        "max": float(clean.max()),
    }


def fmt_float(value: Any, digits: int = 4) -> str:
    if value is None:
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def summarize_bool(values: list[bool]) -> dict[str, Any]:
    return {
        "total": int(len(values)),
        "true": int(sum(1 for v in values if v)),
        "false": int(sum(1 for v in values if not v)),
        "all_true": bool(values and all(values)),
    }


def guess_cache_stimulus_col(cache_df: pd.DataFrame) -> str | None:
    candidates = [
        "stimulus_id",
        "stimulus",
        "stim_id",
        "trial_id",
        "raw_event_name",
        "event_name",
    ]
    for c in candidates:
        if c in cache_df.columns:
            return c

    for c in cache_df.columns:
        lc = str(c).lower()
        if "stim" in lc:
            return str(c)

    return None


def normalize_cache_stimulus(value: Any) -> str:
    text = as_clean_str(value)
    if text.startswith("STIM_"):
        return text[len("STIM_") :]
    if text.startswith("BSL_"):
        return text[len("BSL_") :]
    if text.startswith("SAM_"):
        return text[len("SAM_") :]
    return text


def cache_baseline_evidence(cache_df: pd.DataFrame) -> dict[str, Any]:
    cols = [str(c) for c in cache_df.columns]
    evidence_keywords = [
        "baseline",
        "bsl",
        "correct",
        "correction",
        "normalized",
        "normalised",
        "zscore",
        "z_score",
        "reference",
        "ref",
    ]

    matching_cols = [
        c
        for c in cols
        if any(k in c.lower() for k in evidence_keywords)
    ]

    return {
        "matching_columns": matching_cols,
        "has_explicit_metadata_evidence": bool(matching_cols),
        "interpretation": (
            "Cache index has columns that may indicate baseline/normalization metadata."
            if matching_cols
            else "No explicit cache-index columns indicate baseline correction. This is not proof of absence in the NPY values, but there is no metadata evidence."
        ),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    stimuli_specs_path, find_notes = find_stimuli_specs(args.stimuli_specs, args.search_root)

    specs = read_stimuli_specs_csv(stimuli_specs_path)
    stimulus_event_column = find_stimulus_event_column(specs)

    duration_cols = find_subject_duration_cols(specs)
    specs = specs.copy()
    specs["_event_index_1based"] = list(range(1, len(specs) + 1))
    specs["_event_name"] = specs[stimulus_event_column].map(as_clean_str)
    specs["_event_kind"] = specs["_event_name"].map(event_kind)
    specs["_stimulus_id"] = specs["_event_name"].map(stimulus_id_from_event)

    stim_rows = specs[specs["_event_kind"] == "STIM"].copy()
    bsl_rows = specs[specs["_event_kind"] == "BSL_STIM"].copy()

    bsl_by_id: dict[str, pd.Series] = {}
    duplicate_bsl_ids: set[str] = set()
    for _, row in bsl_rows.iterrows():
        sid = as_clean_str(row["_stimulus_id"])
        if sid in bsl_by_id:
            duplicate_bsl_ids.add(sid)
        else:
            bsl_by_id[sid] = row

    stim_by_id: dict[str, pd.Series] = {}
    duplicate_stim_ids: set[str] = set()
    for _, row in stim_rows.iterrows():
        sid = as_clean_str(row["_stimulus_id"])
        if sid in stim_by_id:
            duplicate_stim_ids.add(sid)
        else:
            stim_by_id[sid] = row

    cache_index_path = args.cache_index
    if not cache_index_path.exists():
        raise FileNotFoundError(f"cache index not found: {cache_index_path}")

    cache_df = pd.read_csv(cache_index_path)
    cache_stim_col = guess_cache_stimulus_col(cache_df)
    if cache_stim_col is None:
        cached_stimulus_ids: list[str] = []
    else:
        cached_stimulus_ids = sorted(
            {
                normalize_cache_stimulus(v)
                for v in cache_df[cache_stim_col].tolist()
                if as_clean_str(v)
            }
        )

    ids_to_audit = cached_stimulus_ids if cached_stimulus_ids else sorted(stim_by_id.keys())

    pair_rows: list[dict[str, Any]] = []
    for sid in ids_to_audit:
        stim_row = stim_by_id.get(sid)
        bsl_row = bsl_by_id.get(sid)

        stim_idx = int(stim_row["_event_index_1based"]) if stim_row is not None else None
        bsl_idx = int(bsl_row["_event_index_1based"]) if bsl_row is not None else None
        bsl_immediately_before = bool(
            stim_idx is not None and bsl_idx is not None and bsl_idx == stim_idx - 1
        )

        stim_dur = numeric_duration_summary(stim_row, duration_cols)
        bsl_dur = numeric_duration_summary(bsl_row, duration_cols)

        pair_rows.append(
            {
                "stimulus_id": sid,
                "has_stim_row": bool(stim_row is not None),
                "has_bsl_row": bool(bsl_row is not None),
                "stim_event_index_1based": stim_idx,
                "bsl_event_index_1based": bsl_idx,
                "bsl_immediately_before_stim": bsl_immediately_before,
                "stim_duration_summary": stim_dur,
                "bsl_duration_summary": bsl_dur,
            }
        )

    bsl_duration_close_to_5: list[bool] = []
    stim_duration_close_to_5: list[bool] = []
    for row in pair_rows:
        bsl_mean = row["bsl_duration_summary"].get("mean")
        stim_mean = row["stim_duration_summary"].get("mean")
        if bsl_mean is not None:
            bsl_duration_close_to_5.append(4.5 <= float(bsl_mean) <= 5.5)
        if stim_mean is not None:
            stim_duration_close_to_5.append(4.5 <= float(stim_mean) <= 5.5)

    feasibility = {
        "can_map_stim_to_bsl_for_all_audited_ids": bool(
            pair_rows and all(row["has_stim_row"] and row["has_bsl_row"] for row in pair_rows)
        ),
        "all_bsl_immediately_before_stim": bool(
            pair_rows and all(row["bsl_immediately_before_stim"] for row in pair_rows)
        ),
        "all_bsl_mean_durations_4p5_to_5p5": bool(
            bsl_duration_close_to_5 and all(bsl_duration_close_to_5)
        ),
        "all_stim_mean_durations_4p5_to_5p5": bool(
            stim_duration_close_to_5 and all(stim_duration_close_to_5)
        ),
    }

    feasible_for_future_cache = all(feasibility.values())
    baseline_evidence = cache_baseline_evidence(cache_df)

    report = {
        "config": {
            "stimuli_specs": str(stimuli_specs_path),
            "cache_index": str(cache_index_path),
            "out_md": str(args.out_md),
            "out_json": str(args.out_json),
        },
        "find_notes": find_notes,
        "stimuli_specs": {
            "rows": int(len(specs)),
            "stimulus_event_column": stimulus_event_column,
            "duration_subject_columns": duration_cols,
            "duration_subject_column_count": int(len(duration_cols)),
            "event_kind_counts": {
                str(k): int(v)
                for k, v in specs["_event_kind"].value_counts(dropna=False).to_dict().items()
            },
            "stim_rows": int(len(stim_rows)),
            "bsl_stim_rows": int(len(bsl_rows)),
            "duplicate_stimulus_ids_in_stim_rows": sorted(duplicate_stim_ids),
            "duplicate_stimulus_ids_in_bsl_rows": sorted(duplicate_bsl_ids),
        },
        "cache_index": {
            "path": str(cache_index_path),
            "rows": int(len(cache_df)),
            "columns": [str(c) for c in cache_df.columns],
            "stimulus_column": cache_stim_col,
            "cached_stimulus_count": int(len(cached_stimulus_ids)),
            "cached_stimulus_ids": cached_stimulus_ids,
            "baseline_metadata_evidence": baseline_evidence,
        },
        "pair_summary": {
            "audited_stimulus_count": int(len(pair_rows)),
            "has_stim_row": summarize_bool([row["has_stim_row"] for row in pair_rows]),
            "has_bsl_row": summarize_bool([row["has_bsl_row"] for row in pair_rows]),
            "bsl_immediately_before_stim": summarize_bool(
                [row["bsl_immediately_before_stim"] for row in pair_rows]
            ),
            "bsl_mean_duration_4p5_to_5p5": summarize_bool(bsl_duration_close_to_5),
            "stim_mean_duration_4p5_to_5p5": summarize_bool(stim_duration_close_to_5),
        },
        "pair_rows": pair_rows,
        "feasibility": {
            **feasibility,
            "feasible_for_future_baseline_corrected_cache": bool(feasible_for_future_cache),
            "recommendation": (
                "Feasible to build a separate baseline-corrected I-DARE EEG cache in a future step. Do not overwrite the current cache."
                if feasible_for_future_cache
                else "Do not build a baseline-corrected cache yet. Review missing/misaligned BSL/STIM pairs or duration issues first."
            ),
        },
        "interpretation": {
            "current_cache_baseline_corrected": (
                "unknown"
                if baseline_evidence["has_explicit_metadata_evidence"]
                else "no_explicit_metadata_evidence"
            ),
            "notes": [
                "This audit only checks metadata/index feasibility.",
                "It does not inspect NPY signal values and cannot prove whether numerical baseline correction was already applied.",
                "A future baseline-corrected cache should be written to a new filename and smoke-tested before any broader run.",
                "Training loops should continue reading cache files only; raw MATLAB/HDF5 access should stay outside training.",
            ],
        },
    }

    return report


def write_markdown(report: dict[str, Any], out_md: Path) -> None:
    cfg = report["config"]
    specs = report["stimuli_specs"]
    cache = report["cache_index"]
    pair_summary = report["pair_summary"]
    feasibility = report["feasibility"]

    lines: list[str] = []
    lines.append("# I-DARE Baseline-Correction Feasibility Audit")
    lines.append("")
    lines.append("This diagnostic is metadata/cache-index only.")
    lines.append("")
    lines.append("It does not train a model, build a cache, modify cache files, or load raw MATLAB/HDF5 files.")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    lines.append(f"- stimuli_specs: `{cfg['stimuli_specs']}`")
    lines.append(f"- cache_index: `{cfg['cache_index']}`")
    lines.append("")
    lines.append("## Stimuli Specifications Summary")
    lines.append("")
    lines.append(f"- rows: `{specs['rows']}`")
    lines.append(f"- event/stimulus column: `{specs['stimulus_event_column']}`")
    lines.append(f"- subject duration columns: `{specs['duration_subject_column_count']}`")
    lines.append(f"- STIM rows: `{specs['stim_rows']}`")
    lines.append(f"- BSL_<stimulus> rows: `{specs['bsl_stim_rows']}`")
    lines.append(f"- event kind counts: `{json.dumps(specs['event_kind_counts'], sort_keys=True)}`")
    lines.append("")
    lines.append("## Cache Index Summary")
    lines.append("")
    lines.append(f"- rows: `{cache['rows']}`")
    lines.append(f"- stimulus column: `{cache['stimulus_column']}`")
    lines.append(f"- cached stimulus count: `{cache['cached_stimulus_count']}`")
    lines.append(
        f"- baseline metadata evidence columns: `{cache['baseline_metadata_evidence']['matching_columns']}`"
    )
    lines.append(
        f"- baseline metadata interpretation: {cache['baseline_metadata_evidence']['interpretation']}"
    )
    lines.append("")
    lines.append("## Pair Feasibility Summary")
    lines.append("")
    lines.append("| Check | Total | Pass | Fail | All pass |")
    lines.append("|---|---:|---:|---:|---|")
    for key, label in [
        ("has_stim_row", "Has STIM row"),
        ("has_bsl_row", "Has matching BSL row"),
        ("bsl_immediately_before_stim", "BSL immediately before STIM"),
        ("bsl_mean_duration_4p5_to_5p5", "BSL mean duration 4.5-5.5s"),
        ("stim_mean_duration_4p5_to_5p5", "STIM mean duration 4.5-5.5s"),
    ]:
        row = pair_summary[key]
        lines.append(
            f"| {label} | {row['total']} | {row['true']} | {row['false']} | `{str(row['all_true']).lower()}` |"
        )
    lines.append("")
    lines.append("## Per-Stimulus Pair Preview")
    lines.append("")
    lines.append("| Stimulus | STIM idx | BSL idx | BSL before STIM | STIM mean sec | BSL mean sec |")
    lines.append("|---|---:|---:|---|---:|---:|")
    for row in report["pair_rows"][:40]:
        stim_mean = row["stim_duration_summary"].get("mean")
        bsl_mean = row["bsl_duration_summary"].get("mean")
        lines.append(
            "| {sid} | {stim_idx} | {bsl_idx} | `{before}` | {stim_mean} | {bsl_mean} |".format(
                sid=row["stimulus_id"],
                stim_idx="" if row["stim_event_index_1based"] is None else row["stim_event_index_1based"],
                bsl_idx="" if row["bsl_event_index_1based"] is None else row["bsl_event_index_1based"],
                before=str(row["bsl_immediately_before_stim"]).lower(),
                stim_mean=fmt_float(stim_mean),
                bsl_mean=fmt_float(bsl_mean),
            )
        )
    lines.append("")
    if len(report["pair_rows"]) > 40:
        lines.append(f"Only first 40 rows shown. Full table is in `{cfg['out_json']}`.")
        lines.append("")
    lines.append("## Feasibility Decision")
    lines.append("")
    lines.append(
        f"- can_map_stim_to_bsl_for_all_audited_ids: `{str(feasibility['can_map_stim_to_bsl_for_all_audited_ids']).lower()}`"
    )
    lines.append(
        f"- all_bsl_immediately_before_stim: `{str(feasibility['all_bsl_immediately_before_stim']).lower()}`"
    )
    lines.append(
        f"- all_bsl_mean_durations_4p5_to_5p5: `{str(feasibility['all_bsl_mean_durations_4p5_to_5p5']).lower()}`"
    )
    lines.append(
        f"- all_stim_mean_durations_4p5_to_5p5: `{str(feasibility['all_stim_mean_durations_4p5_to_5p5']).lower()}`"
    )
    lines.append(
        f"- feasible_for_future_baseline_corrected_cache: `{str(feasibility['feasible_for_future_baseline_corrected_cache']).lower()}`"
    )
    lines.append("")
    lines.append(f"Recommendation: {feasibility['recommendation']}")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    for note in report["interpretation"]["notes"]:
        lines.append(f"- {note}")

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    report = build_report(args)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, args.out_md)

    print(f"[DONE] wrote {args.out_md}")
    print(f"[DONE] wrote {args.out_json}")

    feasible = report["feasibility"]["feasible_for_future_baseline_corrected_cache"]
    print(f"[RESULT] feasible_for_future_baseline_corrected_cache={str(feasible).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
