#!/usr/bin/env python3
"""
Download I-DARE files from docs/idare_download_manifest.csv.

Default mode is dry-run.

Examples:
    Dry-run first-stage files:
        python scripts/download_idare_from_manifest.py

    Actually download first-stage files:
        python scripts/download_idare_from_manifest.py --run

    Download only main-protocol files:
        python scripts/download_idare_from_manifest.py --run --main-protocol-only

    Verify already downloaded files:
        python scripts/download_idare_from_manifest.py --verify-only
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "idare_download_manifest.csv"
IDARE_ROOT = Path("/mnt/HDD/AliWorks/I-DARE")
LOG_PATH = ROOT / "docs" / "idare_download_report.md"


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def human_size(num_bytes: int) -> str:
    value = float(num_bytes)
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024
    return f"{num_bytes} B"


def read_manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with MANIFEST.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            row["size_bytes"] = int(row.get("size_bytes") or 0)
            row["include_in_first_stage"] = parse_bool(row.get("include_in_first_stage", "false"))
            row["include_in_main_protocol"] = parse_bool(row.get("include_in_main_protocol", "false"))
            rows.append(row)
    return rows


def file_md5(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.md5()
    with path.open("rb") as fp:
        while True:
            chunk = fp.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def verify_file(path: Path, expected_size: int, expected_md5: str) -> tuple[bool, list[str]]:
    problems: list[str] = []

    if not path.exists():
        return False, ["missing"]

    actual_size = path.stat().st_size
    if actual_size != expected_size:
        problems.append(f"size mismatch: actual={actual_size}, expected={expected_size}")

    if expected_md5:
        actual_md5 = file_md5(path)
        if actual_md5.lower() != expected_md5.lower():
            problems.append(f"md5 mismatch: actual={actual_md5}, expected={expected_md5}")

    return len(problems) == 0, problems


def download_file(url: str, dest: Path, expected_size: int, expected_md5: str) -> tuple[str, list[str]]:
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists():
        ok, problems = verify_file(dest, expected_size, expected_md5)
        if ok:
            return "already_ok", []
        dest.unlink()

    tmp = dest.with_suffix(dest.suffix + ".part")

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "EmotionRecognitionDEAP-IDARE/0.1",
        },
    )

    with urllib.request.urlopen(req, timeout=120) as response, tmp.open("wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)

    tmp.rename(dest)

    ok, problems = verify_file(dest, expected_size, expected_md5)
    if not ok:
        return "failed_verify", problems

    return "downloaded_ok", []


def select_rows(rows: list[dict[str, Any]], main_protocol_only: bool) -> list[dict[str, Any]]:
    if main_protocol_only:
        return [r for r in rows if r["include_in_main_protocol"]]
    return [r for r in rows if r["include_in_first_stage"]]


def write_report(lines: list[str]) -> None:
    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="Actually download files. Without this flag, only dry-run.")
    parser.add_argument("--verify-only", action="store_true", help="Only verify local files, do not download.")
    parser.add_argument("--main-protocol-only", action="store_true", help="Use include_in_main_protocol instead of include_in_first_stage.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of selected files for testing.")
    args = parser.parse_args()

    rows = read_manifest()
    selected = select_rows(rows, main_protocol_only=args.main_protocol_only)

    if args.limit is not None:
        selected = selected[: args.limit]

    total_size = sum(r["size_bytes"] for r in selected)

    print("I-DARE downloader")
    print("=================")
    print(f"manifest: {MANIFEST}")
    print(f"idare_root: {IDARE_ROOT}")
    print(f"mode: {'verify-only' if args.verify_only else 'run' if args.run else 'dry-run'}")
    print(f"main_protocol_only: {args.main_protocol_only}")
    print(f"selected_files: {len(selected)}")
    print(f"selected_total_size: {human_size(total_size)}")
    print()

    report: list[str] = []
    report.append("# I-DARE Download Report\n")
    report.append(f"- Mode: {'verify-only' if args.verify_only else 'run' if args.run else 'dry-run'}")
    report.append(f"- Main protocol only: {args.main_protocol_only}")
    report.append(f"- Selected files: {len(selected)}")
    report.append(f"- Selected total size: {human_size(total_size)}")
    report.append("")
    report.append("| Status | Category | File | Local path | Notes |")
    report.append("|---|---|---|---|---|")

    status_counts: dict[str, int] = {}

    for i, row in enumerate(selected, start=1):
        category = row["category"]
        file_name = row["file_name"]
        url = row["download_url"]
        expected_size = row["size_bytes"]
        expected_md5 = row.get("computed_md5") or ""
        rel = row["local_relative_path"]
        dest = IDARE_ROOT / rel

        if not url:
            status = "missing_url"
            problems = ["download_url missing"]
        elif args.verify_only:
            ok, problems = verify_file(dest, expected_size, expected_md5)
            status = "verified_ok" if ok else "verify_failed"
        elif not args.run:
            if dest.exists():
                ok, problems = verify_file(dest, expected_size, expected_md5)
                status = "already_ok" if ok else "existing_but_invalid"
            else:
                status = "would_download"
                problems = []
        else:
            print(f"[{i}/{len(selected)}] {category} {file_name} -> {dest}")
            status, problems = download_file(url, dest, expected_size, expected_md5)
            time.sleep(0.1)

        status_counts[status] = status_counts.get(status, 0) + 1
        notes = "; ".join(problems) if problems else ""
        report.append(f"| {status} | {category} | {file_name} | `{dest}` | {notes} |")

    report.append("")
    report.append("## Status Counts\n")
    for status, count in sorted(status_counts.items()):
        report.append(f"- {status}: {count}")

    write_report(report)

    print("Status counts:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    print()
    print(f"Wrote report: {LOG_PATH}")

    if not args.run and not args.verify_only:
        print()
        print("Dry-run only. No files were downloaded.")
        print("To download, run:")
        print("python scripts/download_idare_from_manifest.py --run")


if __name__ == "__main__":
    main()
