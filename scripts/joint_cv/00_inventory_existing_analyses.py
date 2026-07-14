#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "docs" / "joint_cv"
CSV_PATH = OUT_DIR / "existing_analysis_inventory.csv"
MD_PATH = OUT_DIR / "existing_analysis_inventory.md"

KEYWORDS = (
    "roca",
    "prior",
    "baseline",
    "stimulus_only",
    "stimulus-only",
    "subject_only",
    "subject-only",
    "leave_one_subject",
    "leave-one-subject",
    "leave_one_stimulus",
    "leave-one-stimulus",
    "loso",
    "pair_out",
    "pair-out",
    "label_audit",
    "label audit",
    "variance_decomposition",
    "variance decomposition",
    "content-held",
    "content_held",
    "subject-held",
    "subject_held",
    "joint_cv",
    "joint-cv",
    "strict_joint",
    "strict joint",
    "subject-stimulus",
    "subject_stimulus",
    "chance",
    "majority",
    "null",
    "permutation",
    "crossed",
    "bicrossed",
)

ALLOWED_PREFIXES = (
    "docs/",
    "scripts/",
    "src/",
    "experiments/",
)

ALLOWED_SUFFIXES = {
    ".md",
    ".json",
    ".csv",
    ".txt",
    ".py",
    ".sh",
    ".yaml",
    ".yml",
    ".toml",
}

REQUIRED_COLUMNS = [
    "dataset",
    "artifact_path",
    "commit_sha",
    "analysis_type",
    "protocol",
    "task",
    "label_policy",
    "uses_target_subject",
    "uses_target_stimulus",
    "strict_joint",
    "reproducible",
    "usable_for_current_audit",
    "notes",
]

EXTRA_COLUMNS = [
    "commit_date",
    "commit_message",
    "git_status_at_commit",
    "current_path_exists",
    "deleted_later_in_history",
]


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout


def matches_candidate(path: str, commit_message: str) -> bool:
    lower = f"{path} {commit_message}".lower()

    if not path.startswith(ALLOWED_PREFIXES):
        return False

    suffix = Path(path).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        return False

    return any(keyword in lower for keyword in KEYWORDS)


def read_git_blob_prefix(commit_sha: str, path: str, limit: int = 60000) -> str:
    process = subprocess.Popen(
        ["git", "show", f"{commit_sha}:{path}"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )

    assert process.stdout is not None
    data = process.stdout.read(limit)

    try:
        process.terminate()
        process.wait(timeout=1)
    except Exception:
        process.kill()
        process.wait()

    return data.decode("utf-8", errors="ignore")


def detect_dataset(blob: str) -> str:
    has_deap = bool(re.search(r"\bdeap\b", blob))
    has_idare = "i-dare" in blob or "idare" in blob

    if has_deap and has_idare:
        return "DEAP+I-DARE"
    if has_deap:
        return "DEAP"
    if has_idare:
        return "I-DARE"
    return "unspecified"


def detect_task(blob: str) -> str:
    has_valence = "valence" in blob
    has_arousal = "arousal" in blob

    if has_valence and has_arousal:
        return "valence+arousal"
    if has_valence:
        return "valence"
    if has_arousal:
        return "arousal"
    return "unspecified"


def detect_label_policy(blob: str) -> str:
    policies: list[str] = []

    if "discard_midpoint" in blob or "discard midpoint" in blob:
        policies.append("discard_midpoint")

    if "midpoint_as_low" in blob or "midpoint as low" in blob:
        policies.append("midpoint_as_low")

    if "midpoint_as_high" in blob or "midpoint as high" in blob:
        policies.append("midpoint_as_high")

    if (
        "score > 5" in blob
        or "score>5" in blob
        or "label_gt5" in blob
        or "y > 5" in blob
    ):
        policies.append("threshold_gt5")

    if not policies:
        return "unspecified"

    return "+".join(sorted(set(policies)))


def detect_protocol(blob: str) -> str:
    pair_patterns = (
        "leave_one_subject_stimulus_pair_out",
        "leave-one-subject-stimulus-pair-out",
        "leave one subject stimulus pair out",
        "leave-one-cell-out",
        "pair-out",
        "pair_out",
    )

    strict_joint_patterns = (
        "strict joint",
        "strict_joint",
        "strict-joint",
        "joint subject-stimulus",
        "joint subject stimulus",
        "joint_cv",
        "joint-cv",
        "bicrossed",
        "bi-crossed",
        "subject-held-out and stimulus-held-out",
        "subject held out and stimulus held out",
        "unseen subjects and unseen stimuli",
    )

    loso_patterns = (
        "strict_loso",
        "strict loso",
        "leave_one_subject_out",
        "leave-one-subject-out",
        "leave one subject out",
        "loso",
        "subject-held-out",
        "subject held out",
    )

    stimulus_out_patterns = (
        "leave_one_stimulus_out",
        "leave-one-stimulus-out",
        "leave one stimulus out",
        "content-held-out",
        "content held out",
        "stimulus-held-out",
        "stimulus held out",
    )

    if any(pattern in blob for pattern in pair_patterns):
        return "leave-one-subject-stimulus-pair-out"

    if any(pattern in blob for pattern in strict_joint_patterns):
        return "strict-joint-subject-and-stimulus-held-out"

    if any(pattern in blob for pattern in loso_patterns):
        return "leave-one-subject-out"

    if any(pattern in blob for pattern in stimulus_out_patterns):
        return "leave-one-stimulus-out"

    if "random split" in blob or "random_split" in blob:
        return "random-split"

    if "smoke" in blob:
        return "smoke-or-partial"

    return "unspecified"


def detect_analysis_type(blob: str) -> str:
    if (
        "label audit" in blob
        or "label_audit" in blob
        or "label variance" in blob
        or "label_variance" in blob
    ):
        return "label-audit"

    if "variance decomposition" in blob or "variance_decomposition" in blob:
        return "variance-decomposition"

    if (
        "chance" in blob
        or "permutation" in blob
        or "random null" in blob
        or "null distribution" in blob
    ):
        return "chance-or-null-analysis"

    if (
        "stimulus-only" in blob
        or "stimulus_only" in blob
        or "subject-only" in blob
        or "subject_only" in blob
        or "prior baseline" in blob
        or "prior_baseline" in blob
        or "majority baseline" in blob
    ):
        return "prior-or-baseline"

    if (
        "trial index" in blob
        or "trial_index" in blob
        or "cache audit" in blob
        or "data audit" in blob
        or "manifest" in blob
    ):
        return "data-or-cache-audit"

    if (
        "training" in blob
        or "model" in blob
        or "neural" in blob
        or "eeg_" in blob
        or "emg_" in blob
    ):
        return "model-or-training-result"

    return "other"


def protocol_visibility(protocol: str) -> tuple[str, str, str]:
    if protocol == "strict-joint-subject-and-stimulus-held-out":
        return "no", "no", "yes"

    if protocol == "leave-one-subject-out":
        return "no", "yes", "no"

    if protocol == "leave-one-stimulus-out":
        return "yes", "no", "no"

    if protocol == "leave-one-subject-stimulus-pair-out":
        return "yes", "yes", "no"

    return "unknown", "unknown", "no"


def detect_reproducibility(path: str, blob: str) -> str:
    if path.startswith("scripts/"):
        return "yes"

    if (
        "this report was generated by" in blob
        or "generated by `scripts/" in blob
        or "generated from" in blob
    ):
        return "likely"

    return "unknown"


def detect_usability(
    analysis_type: str,
    protocol: str,
) -> str:
    if protocol == "strict-joint-subject-and-stimulus-held-out":
        return "requires-manual-verification"

    if analysis_type in {
        "label-audit",
        "variance-decomposition",
        "prior-or-baseline",
        "chance-or-null-analysis",
        "data-or-cache-audit",
    }:
        return "yes-or-context"

    if analysis_type == "model-or-training-result":
        return "context-only"

    return "manual-review"


def parse_history() -> list[dict[str, Any]]:
    raw = run_git(
        [
            "log",
            "--all",
            "--date=iso-strict",
            "--pretty=format:@@@%H\t%aI\t%s",
            "--name-status",
        ]
    )

    events: list[dict[str, str]] = []
    current_sha = ""
    current_date = ""
    current_message = ""

    for raw_line in raw.splitlines():
        line = raw_line.rstrip("\n")

        if line.startswith("@@@"):
            payload = line[3:]
            parts = payload.split("\t", 2)

            if len(parts) == 3:
                current_sha, current_date, current_message = parts

            continue

        if not line.strip() or not current_sha:
            continue

        parts = line.split("\t")
        if len(parts) < 2:
            continue

        status = parts[0]

        if status.startswith("R") and len(parts) >= 3:
            path = parts[2]
        else:
            path = parts[-1]

        if not matches_candidate(path, current_message):
            continue

        events.append(
            {
                "commit_sha": current_sha,
                "commit_date": current_date,
                "commit_message": current_message,
                "git_status_at_commit": status,
                "artifact_path": path,
            }
        )

    return events


def select_latest_content_versions(
    events: list[dict[str, str]],
) -> list[dict[str, str]]:
    deleted_later: set[str] = set()
    selected: dict[str, dict[str, str]] = {}

    # git log is newest first.
    for event in events:
        path = event["artifact_path"]
        status = event["git_status_at_commit"]

        if status.startswith("D"):
            deleted_later.add(path)
            continue

        if path in selected:
            continue

        row = dict(event)
        row["deleted_later_in_history"] = (
            "yes" if path in deleted_later else "no"
        )
        selected[path] = row

    return sorted(
        selected.values(),
        key=lambda row: (
            row["artifact_path"].lower(),
            row["commit_date"],
        ),
    )


def build_inventory(
    selected: list[dict[str, str]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    for item in selected:
        path = item["artifact_path"]
        commit_sha = item["commit_sha"]

        snippet = read_git_blob_prefix(commit_sha, path)
        blob = (
            path
            + "\n"
            + item["commit_message"]
            + "\n"
            + snippet
        ).lower()

        dataset = detect_dataset(blob)
        task = detect_task(blob)
        label_policy = detect_label_policy(blob)
        protocol = detect_protocol(blob)
        analysis_type = detect_analysis_type(blob)

        uses_target_subject, uses_target_stimulus, strict_joint = (
            protocol_visibility(protocol)
        )

        reproducible = detect_reproducibility(path, blob)
        usability = detect_usability(analysis_type, protocol)

        notes_parts = [
            "Automated historical inventory; scientific classification "
            "must be manually reviewed before reuse."
        ]

        if item["deleted_later_in_history"] == "yes":
            notes_parts.append(
                "Artifact was later deleted or reverted from a newer history state."
            )

        if not (ROOT / path).exists():
            notes_parts.append(
                "Artifact is not present in the current working tree "
                "but remains recoverable from Git history."
            )

        if protocol == "leave-one-subject-stimulus-pair-out":
            notes_parts.append(
                "Pair-out is not Strict Joint CV because the target subject "
                "and target stimulus remain represented in other training cells."
            )

        row = {
            "dataset": dataset,
            "artifact_path": path,
            "commit_sha": commit_sha,
            "analysis_type": analysis_type,
            "protocol": protocol,
            "task": task,
            "label_policy": label_policy,
            "uses_target_subject": uses_target_subject,
            "uses_target_stimulus": uses_target_stimulus,
            "strict_joint": strict_joint,
            "reproducible": reproducible,
            "usable_for_current_audit": usability,
            "notes": " ".join(notes_parts),
            "commit_date": item["commit_date"],
            "commit_message": item["commit_message"],
            "git_status_at_commit": item["git_status_at_commit"],
            "current_path_exists": (
                "yes" if (ROOT / path).exists() else "no"
            ),
            "deleted_later_in_history": item[
                "deleted_later_in_history"
            ],
        }
        rows.append(row)

    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    fieldnames = REQUIRED_COLUMNS + EXTRA_COLUMNS

    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(
    rows: list[dict[str, str]],
    columns: list[str],
) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]

    for row in rows:
        values: list[str] = []

        for column in columns:
            value = str(row.get(column, ""))
            value = value.replace("|", "\\|").replace("\n", " ")
            values.append(value)

        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def counter_rows(counter: Counter[str], key_name: str) -> list[dict[str, str]]:
    return [
        {
            key_name: key,
            "count": str(value),
        }
        for key, value in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]


def write_markdown(rows: list[dict[str, str]]) -> None:
    dataset_counts = Counter(row["dataset"] for row in rows)
    protocol_counts = Counter(row["protocol"] for row in rows)
    type_counts = Counter(row["analysis_type"] for row in rows)

    strict_candidates = [
        row
        for row in rows
        if row["strict_joint"] == "yes"
    ]

    pair_out_rows = [
        row
        for row in rows
        if row["protocol"]
        == "leave-one-subject-stimulus-pair-out"
    ]

    historical_only = [
        row
        for row in rows
        if row["current_path_exists"] == "no"
    ]

    lines: list[str] = [
        "# Existing Analysis Inventory",
        "",
        "This inventory was generated from the complete local Git history, "
        "including historical and later-reverted artifacts.",
        "",
        "No model training was performed.",
        "",
        "## Summary",
        "",
        f"- Unique candidate artifacts: `{len(rows)}`",
        f"- Current-tree artifacts: "
        f"`{sum(row['current_path_exists'] == 'yes' for row in rows)}`",
        f"- Historical-only artifacts: `{len(historical_only)}`",
        f"- Automatically detected Strict Joint candidates: "
        f"`{len(strict_candidates)}`",
        f"- Explicit pair-out artifacts: `{len(pair_out_rows)}`",
        "",
        "## Dataset Counts",
        "",
        markdown_table(
            counter_rows(dataset_counts, "dataset"),
            ["dataset", "count"],
        ),
        "",
        "## Protocol Counts",
        "",
        markdown_table(
            counter_rows(protocol_counts, "protocol"),
            ["protocol", "count"],
        ),
        "",
        "## Analysis-Type Counts",
        "",
        markdown_table(
            counter_rows(type_counts, "analysis_type"),
            ["analysis_type", "count"],
        ),
        "",
        "## Automatically Detected Strict Joint Candidates",
        "",
    ]

    if strict_candidates:
        lines.append(
            markdown_table(
                strict_candidates,
                [
                    "dataset",
                    "artifact_path",
                    "commit_sha",
                    "protocol",
                    "task",
                    "current_path_exists",
                ],
            )
        )
    else:
        lines.append(
            "No artifact was automatically confirmed as Strict Joint CV."
        )

    lines.extend(
        [
            "",
            "## Pair-Out Warning",
            "",
            "Every leave-one-subject-stimulus-pair-out artifact is classified "
            "as non-Strict-Joint because the target subject and target stimulus "
            "remain observable through other training cells.",
            "",
        ]
    )

    if pair_out_rows:
        lines.append(
            markdown_table(
                pair_out_rows[:50],
                [
                    "dataset",
                    "artifact_path",
                    "commit_sha",
                    "task",
                    "current_path_exists",
                ],
            )
        )
    else:
        lines.append("No explicit pair-out artifact was detected.")

    lines.extend(
        [
            "",
            "## Manual Review Requirement",
            "",
            "This file is an automated first-pass inventory. "
            "The full row-level evidence is stored in:",
            "",
            f"- `{CSV_PATH.relative_to(ROOT)}`",
            "",
            "Before reusing any result, inspect the exact script/report content, "
            "split construction, target-data visibility, and statistical unit.",
            "",
        ]
    )

    MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    events = parse_history()
    selected = select_latest_content_versions(events)
    inventory = build_inventory(selected)

    write_csv(inventory)
    write_markdown(inventory)

    print("Existing-analysis inventory completed.")
    print(f"Candidate history events: {len(events)}")
    print(f"Unique artifact paths: {len(inventory)}")
    print(f"CSV: {CSV_PATH}")
    print(f"Markdown: {MD_PATH}")
    print(
        "Strict Joint candidates:",
        sum(row["strict_joint"] == "yes" for row in inventory),
    )
    print(
        "Pair-out artifacts:",
        sum(
            row["protocol"]
            == "leave-one-subject-stimulus-pair-out"
            for row in inventory
        ),
    )


if __name__ == "__main__":
    main()
