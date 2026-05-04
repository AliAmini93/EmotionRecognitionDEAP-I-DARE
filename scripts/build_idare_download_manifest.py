#!/usr/bin/env python3
"""
Build I-DARE download manifest from docs/data_sources_idare.json.

Input:
- docs/data_sources_idare.json

Outputs:
- docs/idare_download_manifest.csv
- docs/idare_download_manifest_summary.md

This script does not download files.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_JSON = ROOT / "docs" / "data_sources_idare.json"
OUT_CSV = ROOT / "docs" / "idare_download_manifest.csv"
OUT_MD = ROOT / "docs" / "idare_download_manifest_summary.md"


COMMON_EEG_EMG_SUBJECTS = {
    1, 2, 3, 5, 6, 7, 8, 9, 10,
    11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
    31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
    41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
    52, 53, 54, 55, 56, 57, 58, 59, 60,
    61, 62, 63, 64, 65,
}


def subject_id_from_name(name: str | None) -> int | None:
    if not name:
        return None
    m = re.search(r"sbj_P_(\d+)\.mat$", name)
    return int(m.group(1)) if m else None


def local_path_for(category: str, file_name: str, subject_id: int | None) -> str:
    if category == "EEG":
        return f"raw_downloads/EEG/{file_name}"
    if category == "EMG":
        return f"raw_downloads/EMG/{file_name}"
    if category == "labels":
        return f"labels/{file_name}"
    if category == "metadata":
        return f"metadata/{file_name}"
    return f"unused/{category}/{file_name}"


def is_required_first_stage(category: str, file_name: str) -> bool:
    if category in {"EEG", "EMG"}:
        return True

    required_label_metadata = {
        "Valence_SAM.csv",
        "Arousal_SAM.csv",
        "Quadrants_SAM.csv",
        "Sample.csv",
        "Stimuli_Specifications.csv",
        "Agreement_Raters.csv",
    }

    return file_name in required_label_metadata


def include_in_main_protocol(category: str, subject_id: int | None, file_name: str) -> bool:
    if category in {"EEG", "EMG"}:
        return subject_id in COMMON_EEG_EMG_SUBJECTS

    required_label_metadata = {
        "Valence_SAM.csv",
        "Arousal_SAM.csv",
        "Quadrants_SAM.csv",
        "Sample.csv",
        "Stimuli_Specifications.csv",
        "Agreement_Raters.csv",
    }

    return file_name in required_label_metadata


def note_for(category: str, subject_id: int | None, file_name: str) -> str:
    if category == "EMG" and subject_id == 4:
        return "EMG-only subject. Exclude from main EEG+EMG protocol; optional EMG-only secondary analysis."
    if category in {"SC/PPG", "ET"}:
        return "Not required for first-stage EEG-EMG project."
    if file_name == "Stimuli_Selection.pdf":
        return "Documentation only; not required for first-stage download."
    return ""


def main() -> None:
    payload: dict[str, Any] = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    files = payload["files"]

    rows: list[dict[str, Any]] = []

    for f in files:
        category = f.get("category_guess") or "unknown"
        file_name = f.get("file_name") or ""
        subject_id = subject_id_from_name(file_name)

        first_stage = is_required_first_stage(category, file_name)
        main_protocol = include_in_main_protocol(category, subject_id, file_name)

        rows.append(
            {
                "category": category,
                "article_id": f.get("article_id"),
                "article_title": f.get("article_title"),
                "file_id": f.get("file_id"),
                "file_name": file_name,
                "subject_id": "" if subject_id is None else subject_id,
                "size_bytes": f.get("size_bytes") or 0,
                "size_human": f.get("size_human") or "",
                "download_url": f.get("download_url") or "",
                "local_relative_path": local_path_for(category, file_name, subject_id),
                "include_in_first_stage": str(first_stage).lower(),
                "include_in_main_protocol": str(main_protocol).lower(),
                "notes": note_for(category, subject_id, file_name),
            }
        )

    rows.sort(
        key=lambda r: (
            not (r["include_in_first_stage"] == "true"),
            r["category"],
            int(r["subject_id"]) if str(r["subject_id"]).isdigit() else 9999,
            r["file_name"],
        )
    )

    fieldnames = [
        "category",
        "article_id",
        "article_title",
        "file_id",
        "file_name",
        "subject_id",
        "size_bytes",
        "size_human",
        "download_url",
        "local_relative_path",
        "include_in_first_stage",
        "include_in_main_protocol",
        "notes",
    ]

    with OUT_CSV.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total_files = len(rows)
    first_stage_rows = [r for r in rows if r["include_in_first_stage"] == "true"]
    main_rows = [r for r in rows if r["include_in_main_protocol"] == "true"]

    def total_size(selected_rows: list[dict[str, Any]]) -> int:
        return sum(int(r["size_bytes"]) for r in selected_rows)

    def gb(n: int) -> str:
        return f"{n / (1024 ** 3):.2f} GB"

    by_category: dict[str, int] = {}
    by_category_size: dict[str, int] = {}

    for r in first_stage_rows:
        c = r["category"]
        by_category[c] = by_category.get(c, 0) + 1
        by_category_size[c] = by_category_size.get(c, 0) + int(r["size_bytes"])

    lines: list[str] = []
    lines.append("# I-DARE Download Manifest Summary\n")
    lines.append("This file was generated by `scripts/build_idare_download_manifest.py`.\n")
    lines.append("No dataset files were downloaded by this script.\n")
    lines.append("## Manifest Outputs\n")
    lines.append("- `docs/idare_download_manifest.csv`\n")
    lines.append("- `docs/idare_download_manifest_summary.md`\n")
    lines.append("## Counts\n")
    lines.append(f"- Total listed files: {total_files}\n")
    lines.append(f"- First-stage files: {len(first_stage_rows)}\n")
    lines.append(f"- Main-protocol files: {len(main_rows)}\n")
    lines.append(f"- First-stage total size: {gb(total_size(first_stage_rows))}\n")
    lines.append(f"- Main-protocol total size: {gb(total_size(main_rows))}\n")
    lines.append("## First-Stage Files by Category\n")
    lines.append("| Category | Count | Size |\n")
    lines.append("|---|---:|---:|\n")
    for c in sorted(by_category):
        lines.append(f"| {c} | {by_category[c]} | {gb(by_category_size[c])} |\n")
    lines.append("\n## Main Protocol Subject Decision\n")
    lines.append("- Use the 63 common EEG+EMG subjects for main I-DARE experiments.\n")
    lines.append("- Subject 4 has EMG but no EEG.\n")
    lines.append("- Subject 4 is included in the manifest but excluded from `include_in_main_protocol`.\n")
    lines.append("- Subject 4 may be used only for optional EMG-only secondary analysis.\n")
    lines.append("\n## Next Step\n")
    lines.append("Review `docs/idare_download_manifest.csv` before downloading files.\n")

    OUT_MD.write_text("".join(lines), encoding="utf-8")

    print(f"Wrote: {OUT_CSV}")
    print(f"Wrote: {OUT_MD}")
    print(f"Total listed files: {total_files}")
    print(f"First-stage files: {len(first_stage_rows)}")
    print(f"Main-protocol files: {len(main_rows)}")
    print(f"First-stage total size: {gb(total_size(first_stage_rows))}")
    print(f"Main-protocol total size: {gb(total_size(main_rows))}")


if __name__ == "__main__":
    main()
