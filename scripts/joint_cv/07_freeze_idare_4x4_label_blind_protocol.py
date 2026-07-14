#!/usr/bin/env python3
"""Freeze a label-blind repeated 4x4 Strict Joint CV protocol for I-DARE.

The partition seeds are derived deterministically from the manifest SHA-256,
protocol name, repetition index, and axis. Labels are not used to construct or
select any partition, and no repetition is rerolled after inspecting support.

Protocol
--------
For each repetition and every one of the 16 subject-fold × stimulus-fold cells:

Train:
    source subjects × source stimuli

Primary test:
    held-out subjects × held-out stimuli

Diagnostics:
    source subjects × held-out stimuli
    held-out subjects × source stimuli

No model training is performed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


REPO = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE")
MANIFEST = REPO / "docs" / "joint_cv" / "idare_trial_manifest.csv"
DOCS = REPO / "docs" / "joint_cv"
FOLDS = REPO / "folds"
EXPECTED_BRANCH = "joint-cv-capacity-audit"

K_SUBJECT = 4
K_STIMULUS = 4
DEFAULT_REPETITIONS = 5

TASKS = ("valence", "arousal")
POLICIES = (
    "discard_midpoint",
    "midpoint_as_low",
    "midpoint_as_high",
)

OUTPUT_NAMES = {
    "protocol_json": "idare_4x4_label_blind_repeated_protocol.json",
    "assignments_csv": "idare_4x4_label_blind_repeated_assignments.csv",
    "primary_subject_csv": "idare_4x4_label_blind_primary_subject_folds.csv",
    "primary_stimulus_csv": "idare_4x4_label_blind_primary_stimulus_folds.csv",
    "support_csv": "idare_4x4_label_blind_repeated_support.csv",
    "decision_md": "idare_4x4_label_blind_protocol_decision.md",
    "decision_json": "idare_4x4_label_blind_protocol_decision.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--docs-dir", type=Path, default=DOCS)
    parser.add_argument("--folds-dir", type=Path, default=FOLDS)
    parser.add_argument(
        "--repetitions",
        type=int,
        default=DEFAULT_REPETITIONS,
        help="Number of pre-registered label-blind 4x4 repetitions.",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed:\n{proc.stderr.strip()}"
        )
    return proc.stdout.strip()


def safe_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): safe_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [safe_json(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        value = float(value)
        return value if math.isfinite(value) else None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


def prepare_outputs(
    docs_dir: Path,
    folds_dir: Path,
    overwrite: bool,
) -> dict[str, Path]:
    docs_dir.mkdir(parents=True, exist_ok=True)
    folds_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "protocol_json": folds_dir / OUTPUT_NAMES["protocol_json"],
        "assignments_csv": folds_dir / OUTPUT_NAMES["assignments_csv"],
        "primary_subject_csv": (
            folds_dir / OUTPUT_NAMES["primary_subject_csv"]
        ),
        "primary_stimulus_csv": (
            folds_dir / OUTPUT_NAMES["primary_stimulus_csv"]
        ),
        "support_csv": docs_dir / OUTPUT_NAMES["support_csv"],
        "decision_md": docs_dir / OUTPUT_NAMES["decision_md"],
        "decision_json": docs_dir / OUTPUT_NAMES["decision_json"],
    }

    if not overwrite:
        existing = [path for path in outputs.values() if path.exists()]
        if existing:
            raise FileExistsError(
                "Refusing to overwrite existing outputs:\n"
                + "\n".join(f"- {path}" for path in existing)
            )

    return outputs


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def deterministic_seed(
    manifest_hash: str,
    repetition: int,
    axis: str,
) -> int:
    payload = (
        f"{manifest_hash}|I-DARE|strict-joint|4x4|"
        f"repetition={repetition}|axis={axis}"
    ).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:8], "big") % (2**32)


def fold_capacities(n_entities: int, k: int) -> list[int]:
    base = n_entities // k
    remainder = n_entities % k
    return [
        base + (1 if fold_index < remainder else 0)
        for fold_index in range(k)
    ]


def label_blind_assignment(
    entities: list[str],
    k: int,
    seed: int,
) -> dict[str, int]:
    rng = np.random.default_rng(seed)
    shuffled = list(entities)
    rng.shuffle(shuffled)

    capacities = fold_capacities(len(entities), k)
    assignment: dict[str, int] = {}
    cursor = 0

    for fold_index, capacity in enumerate(capacities):
        for entity in shuffled[cursor:cursor + capacity]:
            assignment[entity] = fold_index
        cursor += capacity

    if cursor != len(entities):
        raise RuntimeError("Partition cursor mismatch")
    if len(assignment) != len(entities):
        raise RuntimeError("Duplicate entity in partition")

    return assignment


def load_manifest(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    required = {
        "subject_id",
        "stimulus_id",
        "trial_id",
        "valence_discard_midpoint",
        "valence_midpoint_as_low",
        "valence_midpoint_as_high",
        "arousal_discard_midpoint",
        "arousal_midpoint_as_low",
        "arousal_midpoint_as_high",
        "eeg_available",
        "emg_available",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Manifest missing columns: {missing}")

    df = df.copy()
    df["subject_id"] = df["subject_id"].astype(str)
    df["stimulus_id"] = df["stimulus_id"].astype(str)

    if len(df) != 2016:
        raise ValueError(f"Expected 2016 rows, found {len(df)}")
    if df["subject_id"].nunique() != 63:
        raise ValueError("Expected 63 subjects")
    if df["stimulus_id"].nunique() != 32:
        raise ValueError("Expected 32 stimuli")
    if df["trial_id"].duplicated().any():
        raise ValueError("Duplicate trial_id")
    if df.duplicated(["subject_id", "stimulus_id"]).any():
        raise ValueError("Duplicate subject-stimulus physical cells")

    return df


def class_counts(values: np.ndarray) -> tuple[int, int]:
    return int((values == 0).sum()), int((values == 1).sum())


def evaluate_repetition(
    df: pd.DataFrame,
    repetition: int,
    subject_assignment: dict[str, int],
    stimulus_assignment: dict[str, int],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    subject_fold = df["subject_id"].map(subject_assignment)
    stimulus_fold = df["stimulus_id"].map(stimulus_assignment)

    if subject_fold.isna().any() or stimulus_fold.isna().any():
        raise ValueError("Incomplete fold assignment")

    support_rows: list[dict[str, Any]] = []
    single_class_test_total = 0
    single_class_train_total = 0
    min_test_class_global: int | None = None
    min_train_class_global: int | None = None
    min_test_retained_global: int | None = None
    max_midpoint_removed_fraction = 0.0

    for subject_fold_index in range(K_SUBJECT):
        held_subject = subject_fold == subject_fold_index
        held_subject_ids = sorted(
            entity
            for entity, fold in subject_assignment.items()
            if fold == subject_fold_index
        )

        for stimulus_fold_index in range(K_STIMULUS):
            held_stimulus = stimulus_fold == stimulus_fold_index
            held_stimulus_ids = sorted(
                entity
                for entity, fold in stimulus_assignment.items()
                if fold == stimulus_fold_index
            )

            masks = {
                "train": (~held_subject) & (~held_stimulus),
                "seen_subject_unseen_stimulus": (
                    (~held_subject) & held_stimulus
                ),
                "unseen_subject_seen_stimulus": (
                    held_subject & (~held_stimulus)
                ),
                "unseen_subject_unseen_stimulus": (
                    held_subject & held_stimulus
                ),
            }

            cell_id = (
                f"rep{repetition:02d}_S{subject_fold_index + 1:02d}_"
                f"T{stimulus_fold_index + 1:02d}"
            )

            for task in TASKS:
                for policy in POLICIES:
                    label_column = f"{task}_{policy}"
                    labels = pd.to_numeric(
                        df[label_column],
                        errors="coerce",
                    )
                    retained = labels.notna()

                    region_stats: dict[str, dict[str, Any]] = {}
                    for region_name, region_mask in masks.items():
                        region_values = (
                            labels[region_mask & retained]
                            .astype(int)
                            .to_numpy()
                        )
                        low, high = class_counts(region_values)

                        available_mask = (
                            region_mask
                            & retained
                            & df["eeg_available"].astype(bool)
                            & df["emg_available"].astype(bool)
                        )

                        region_stats[region_name] = {
                            "rows_before_policy": int(region_mask.sum()),
                            "rows_retained": int(
                                (region_mask & retained).sum()
                            ),
                            "midpoints_removed": int(
                                region_mask.sum()
                                - (region_mask & retained).sum()
                            ),
                            "low": low,
                            "high": high,
                            "single_class": bool(
                                len(region_values) > 0
                                and len(np.unique(region_values)) < 2
                            ),
                            "rows_after_eeg_emg_availability": int(
                                available_mask.sum()
                            ),
                        }

                    train = region_stats["train"]
                    test = region_stats[
                        "unseen_subject_unseen_stimulus"
                    ]
                    diag_a = region_stats[
                        "seen_subject_unseen_stimulus"
                    ]
                    diag_b = region_stats[
                        "unseen_subject_seen_stimulus"
                    ]

                    test_min_class = min(
                        test["low"],
                        test["high"],
                    )
                    train_min_class = min(
                        train["low"],
                        train["high"],
                    )
                    removed_fraction = (
                        test["midpoints_removed"]
                        / test["rows_before_policy"]
                        if test["rows_before_policy"]
                        else 0.0
                    )

                    if test["single_class"]:
                        single_class_test_total += 1
                    if train["single_class"]:
                        single_class_train_total += 1

                    min_test_class_global = (
                        test_min_class
                        if min_test_class_global is None
                        else min(
                            min_test_class_global,
                            test_min_class,
                        )
                    )
                    min_train_class_global = (
                        train_min_class
                        if min_train_class_global is None
                        else min(
                            min_train_class_global,
                            train_min_class,
                        )
                    )
                    min_test_retained_global = (
                        test["rows_retained"]
                        if min_test_retained_global is None
                        else min(
                            min_test_retained_global,
                            test["rows_retained"],
                        )
                    )
                    max_midpoint_removed_fraction = max(
                        max_midpoint_removed_fraction,
                        removed_fraction,
                    )

                    support_rows.append(
                        {
                            "repetition": repetition,
                            "role": (
                                "primary"
                                if repetition == 0
                                else "sensitivity"
                            ),
                            "cell_id": cell_id,
                            "subject_fold": subject_fold_index + 1,
                            "stimulus_fold": stimulus_fold_index + 1,
                            "task": task,
                            "label_policy": policy,
                            "held_subject_count": len(
                                held_subject_ids
                            ),
                            "held_stimulus_count": len(
                                held_stimulus_ids
                            ),
                            "train_rows_before_policy": train[
                                "rows_before_policy"
                            ],
                            "train_rows_retained": train[
                                "rows_retained"
                            ],
                            "train_low": train["low"],
                            "train_high": train["high"],
                            "train_single_class": train[
                                "single_class"
                            ],
                            "test_rows_before_policy": test[
                                "rows_before_policy"
                            ],
                            "test_rows_retained": test[
                                "rows_retained"
                            ],
                            "test_midpoints_removed": test[
                                "midpoints_removed"
                            ],
                            "test_midpoint_removed_fraction": (
                                removed_fraction
                            ),
                            "test_low": test["low"],
                            "test_high": test["high"],
                            "test_min_class_support": (
                                test_min_class
                            ),
                            "test_single_class": test[
                                "single_class"
                            ],
                            "test_rows_after_eeg_emg_availability": (
                                test[
                                    "rows_after_eeg_emg_availability"
                                ]
                            ),
                            "seen_subject_unseen_stimulus_"
                            "rows_retained": diag_a[
                                "rows_retained"
                            ],
                            "unseen_subject_seen_stimulus_"
                            "rows_retained": diag_b[
                                "rows_retained"
                            ],
                            "subject_leakage": False,
                            "stimulus_leakage": False,
                        }
                    )

    assert min_test_class_global is not None
    assert min_train_class_global is not None
    assert min_test_retained_global is not None

    held_subject_sizes = [
        sum(fold == fold_index for fold in subject_assignment.values())
        for fold_index in range(K_SUBJECT)
    ]
    held_stimulus_sizes = [
        sum(fold == fold_index for fold in stimulus_assignment.values())
        for fold_index in range(K_STIMULUS)
    ]

    strong_pass = bool(
        single_class_test_total == 0
        and single_class_train_total == 0
        and min_test_class_global >= 10
        and min_train_class_global >= 10
        and min(held_subject_sizes) >= 10
        and min(held_stimulus_sizes) >= 5
    )
    minimal_pass = bool(
        single_class_test_total == 0
        and single_class_train_total == 0
        and min_test_class_global >= 5
    )

    summary = {
        "repetition": repetition,
        "role": "primary" if repetition == 0 else "sensitivity",
        "outer_cells": K_SUBJECT * K_STIMULUS,
        "min_held_subjects": min(held_subject_sizes),
        "max_held_subjects": max(held_subject_sizes),
        "min_held_stimuli": min(held_stimulus_sizes),
        "max_held_stimuli": max(held_stimulus_sizes),
        "min_test_class_support": min_test_class_global,
        "min_train_class_support": min_train_class_global,
        "min_test_retained": min_test_retained_global,
        "max_midpoint_removed_fraction": (
            max_midpoint_removed_fraction
        ),
        "single_class_test_flags": single_class_test_total,
        "single_class_train_flags": single_class_train_total,
        "strong_capacity_pass": strong_pass,
        "minimal_capacity_pass": minimal_pass,
    }

    return support_rows, summary


def write_csv(
    path: Path,
    rows: Iterable[dict[str, Any]],
) -> None:
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    columns: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=columns,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(
    rows: list[dict[str, Any]],
    columns: list[str],
) -> str:
    if not rows:
        return "_No rows._"

    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]

    for row in rows:
        values = []
        for column in columns:
            value = str(row.get(column, ""))
            value = value.replace("|", "\\|").replace("\n", " ")
            values.append(value)
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def main() -> None:
    args = parse_args()

    if args.repetitions < 2:
        raise ValueError("--repetitions must be at least 2")

    repo = args.repo_root.resolve()
    manifest_path = args.manifest.resolve()
    docs_dir = args.docs_dir.resolve()
    folds_dir = args.folds_dir.resolve()

    branch = git(repo, "branch", "--show-current")
    head = git(repo, "rev-parse", "HEAD")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}"
        )

    outputs = prepare_outputs(
        docs_dir,
        folds_dir,
        args.overwrite,
    )
    df = load_manifest(manifest_path)
    manifest_hash = sha256_file(manifest_path)

    subjects = sorted(df["subject_id"].unique().tolist())
    stimuli = sorted(df["stimulus_id"].unique().tolist())

    assignment_rows: list[dict[str, Any]] = []
    support_rows: list[dict[str, Any]] = []
    repetition_summaries: list[dict[str, Any]] = []
    protocol_repetitions: list[dict[str, Any]] = []

    for repetition in range(args.repetitions):
        subject_seed = deterministic_seed(
            manifest_hash,
            repetition,
            "subject",
        )
        stimulus_seed = deterministic_seed(
            manifest_hash,
            repetition,
            "stimulus",
        )

        subject_assignment = label_blind_assignment(
            subjects,
            K_SUBJECT,
            subject_seed,
        )
        stimulus_assignment = label_blind_assignment(
            stimuli,
            K_STIMULUS,
            stimulus_seed,
        )

        repetition_assignment_rows: list[dict[str, Any]] = []

        for axis, assignment, seed in (
            ("subject", subject_assignment, subject_seed),
            ("stimulus", stimulus_assignment, stimulus_seed),
        ):
            for entity, fold_index in sorted(assignment.items()):
                row = {
                    "repetition": repetition,
                    "role": (
                        "primary"
                        if repetition == 0
                        else "sensitivity"
                    ),
                    "axis": axis,
                    "entity_id": entity,
                    "fold_index_0based": fold_index,
                    "fold_index_1based": fold_index + 1,
                    "seed": seed,
                    "manifest_sha256": manifest_hash,
                    "partition_uses_labels": False,
                }
                assignment_rows.append(row)
                repetition_assignment_rows.append(row)

        rep_support, rep_summary = evaluate_repetition(
            df,
            repetition,
            subject_assignment,
            stimulus_assignment,
        )
        support_rows.extend(rep_support)
        repetition_summaries.append(rep_summary)

        protocol_repetitions.append(
            {
                "repetition": repetition,
                "role": (
                    "primary"
                    if repetition == 0
                    else "sensitivity"
                ),
                "subject_seed": subject_seed,
                "stimulus_seed": stimulus_seed,
                "subject_assignment": subject_assignment,
                "stimulus_assignment": stimulus_assignment,
                "capacity_summary": rep_summary,
            }
        )

        if repetition == 0:
            write_csv(
                outputs["primary_subject_csv"],
                [
                    row
                    for row in repetition_assignment_rows
                    if row["axis"] == "subject"
                ],
            )
            write_csv(
                outputs["primary_stimulus_csv"],
                [
                    row
                    for row in repetition_assignment_rows
                    if row["axis"] == "stimulus"
                ],
            )

    write_csv(outputs["assignments_csv"], assignment_rows)
    write_csv(outputs["support_csv"], support_rows)

    primary = repetition_summaries[0]
    sensitivity = repetition_summaries[1:]

    all_repetitions_minimal = all(
        item["minimal_capacity_pass"]
        for item in repetition_summaries
    )
    all_repetitions_strong = all(
        item["strong_capacity_pass"]
        for item in repetition_summaries
    )
    sensitivity_strong_rate = (
        sum(item["strong_capacity_pass"] for item in sensitivity)
        / len(sensitivity)
    )

    if (
        primary["strong_capacity_pass"]
        and all_repetitions_minimal
    ):
        decision = "LOCK_LABEL_BLIND_4X4_PROTOCOL"
        reason = (
            "The pre-registered primary repetition passes the strong "
            "capacity gate, and every pre-registered sensitivity "
            "repetition passes the minimum capacity gate."
        )
    elif (
        primary["minimal_capacity_pass"]
        and all_repetitions_minimal
    ):
        decision = "LOCK_4X4_WITH_CAPACITY_CAUTION"
        reason = (
            "All pre-registered repetitions pass the minimum capacity "
            "gate, but the primary repetition does not pass the stronger "
            "support threshold."
        )
    else:
        decision = "DO_NOT_LOCK_PROTOCOL"
        reason = (
            "At least one pre-registered label-blind repetition fails "
            "the minimum capacity gate. No rerolling or seed replacement "
            "is permitted."
        )

    protocol = {
        "protocol_name": (
            "I-DARE repeated label-blind 4x4 Strict Joint CV"
        ),
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "manifest": str(manifest_path),
        "manifest_sha256": manifest_hash,
        "statistical_unit": "physical_trial",
        "partition_uses_labels": False,
        "partition_seed_derivation": (
            "SHA256(manifest_sha256 | dataset | protocol | "
            "repetition | axis), first 8 bytes modulo 2**32"
        ),
        "repetitions": args.repetitions,
        "primary_repetition": 0,
        "sensitivity_repetitions": list(
            range(1, args.repetitions)
        ),
        "subject_folds": K_SUBJECT,
        "stimulus_folds": K_STIMULUS,
        "outer_cells_per_repetition": (
            K_SUBJECT * K_STIMULUS
        ),
        "all_subject_stimulus_fold_combinations": True,
        "diagonal_only_pairing": False,
        "train_region": "source subjects x source stimuli",
        "primary_test_region": (
            "held-out subjects x held-out stimuli"
        ),
        "diagnostic_regions": [
            "source subjects x held-out stimuli",
            "held-out subjects x source stimuli",
        ],
        "no_reroll_after_support_audit": True,
        "repetition_details": protocol_repetitions,
        "decision": decision,
        "decision_reason": reason,
    }

    outputs["protocol_json"].write_text(
        json.dumps(
            safe_json(protocol),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    decision_payload = {
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "manifest_sha256": manifest_hash,
        "decision": decision,
        "reason": reason,
        "primary_summary": primary,
        "repetition_summaries": repetition_summaries,
        "all_repetitions_minimal": all_repetitions_minimal,
        "all_repetitions_strong": all_repetitions_strong,
        "sensitivity_strong_rate": sensitivity_strong_rate,
        "balanced_5x5_status": (
            "rejected as primary due partition sensitivity"
        ),
        "previous_label_balanced_4x4_status": (
            "retained only as a diagnostic capacity-upper-bound split; "
            "not the headline benchmark"
        ),
    }
    outputs["decision_json"].write_text(
        json.dumps(
            safe_json(decision_payload),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    table_rows = [
        {
            "repetition": item["repetition"],
            "role": item["role"],
            "held_subjects": (
                f"{item['min_held_subjects']}.."
                f"{item['max_held_subjects']}"
            ),
            "held_stimuli": (
                f"{item['min_held_stimuli']}.."
                f"{item['max_held_stimuli']}"
            ),
            "min_test_class": item[
                "min_test_class_support"
            ],
            "min_train_class": item[
                "min_train_class_support"
            ],
            "min_test_retained": item[
                "min_test_retained"
            ],
            "max_midpoint_removed_fraction": round(
                item[
                    "max_midpoint_removed_fraction"
                ],
                6,
            ),
            "single_class_test_flags": item[
                "single_class_test_flags"
            ],
            "single_class_train_flags": item[
                "single_class_train_flags"
            ],
            "strong_pass": item[
                "strong_capacity_pass"
            ],
            "minimal_pass": item[
                "minimal_capacity_pass"
            ],
        }
        for item in repetition_summaries
    ]

    md_lines = [
        "# I-DARE Label-Blind Repeated 4x4 Protocol Decision",
        "",
        "No model training was performed.",
        "",
        "## Why 5x5 Was Not Selected",
        "",
        "The 5x5 scheme was partition-sensitive under label-blind "
        "randomization. Its earlier balanced split was more balanced than "
        "over 99% of random partitions and therefore is not suitable as "
        "the sole headline benchmark.",
        "",
        "## Frozen Construction Rule",
        "",
        f"- Manifest SHA-256: `{manifest_hash}`",
        f"- Repetitions: `{args.repetitions}`",
        "- Repetition 0: primary benchmark",
        f"- Repetitions 1–{args.repetitions - 1}: sensitivity analysis",
        "- Subject folds: `4`",
        "- Stimulus folds: `4`",
        "- Outer cells per repetition: `16`",
        "- All subject-fold × stimulus-fold combinations are evaluated",
        "- Partition construction uses no labels",
        "- Seeds are derived deterministically from the manifest hash",
        "- No rerolling or replacement of unfavorable repetitions",
        "",
        "## Capacity Audit",
        "",
        markdown_table(
            table_rows,
            [
                "repetition",
                "role",
                "held_subjects",
                "held_stimuli",
                "min_test_class",
                "min_train_class",
                "min_test_retained",
                "max_midpoint_removed_fraction",
                "single_class_test_flags",
                "single_class_train_flags",
                "strong_pass",
                "minimal_pass",
            ],
        ),
        "",
        "## Decision",
        "",
        f"- Decision: **{decision}**",
        f"- Reason: {reason}",
        f"- All repetitions pass minimum capacity: "
        f"`{all_repetitions_minimal}`",
        f"- All repetitions pass strong capacity: "
        f"`{all_repetitions_strong}`",
        f"- Sensitivity strong-pass rate: "
        f"`{sensitivity_strong_rate:.4f}`",
        "",
        "## Status of Earlier Candidate Splits",
        "",
        "- Label-balanced 5x5: rejected as primary due partition "
        "sensitivity.",
        "- Label-balanced 4x4: retained only as a diagnostic "
        "capacity-upper-bound split; it is not the headline benchmark.",
        "",
        "## Next Audit Before Model Training",
        "",
        "Run leakage-safe shortcut baselines and null/permutation analyses "
        "on the frozen primary and sensitivity partitions. Do not tune "
        "architectures on sensitivity repetitions.",
        "",
    ]

    outputs["decision_md"].write_text(
        "\n".join(md_lines),
        encoding="utf-8",
    )

    print("I-DARE label-blind repeated 4x4 protocol audit completed.")
    print(f"Branch: {branch}")
    print(f"HEAD: {head}")
    print(f"Manifest SHA-256: {manifest_hash}")
    print(f"Repetitions: {args.repetitions}")
    for item in repetition_summaries:
        print(
            f"rep{item['repetition']:02d} "
            f"({item['role']}): "
            f"min_test_class="
            f"{item['min_test_class_support']}, "
            f"single_class_test="
            f"{item['single_class_test_flags']}, "
            f"strong={item['strong_capacity_pass']}, "
            f"minimal={item['minimal_capacity_pass']}"
        )
    print(f"Decision: {decision}")
    print(f"Report: {outputs['decision_md']}")
    print(f"Protocol JSON: {outputs['protocol_json']}")


if __name__ == "__main__":
    main()

