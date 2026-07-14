#!/usr/bin/env python3
"""Freeze a repeated label-blind 4x4 Strict Joint protocol for DEAP.

No EEG/EMG or deep model training is performed.

Construction
------------
- 5 deterministic label-blind repetitions.
- 4 subject folds × 4 stimulus folds.
- All 16 subject-fold × stimulus-fold outer cells are evaluated.
- Train = source subjects × source stimuli.
- Primary test = held-out subjects × held-out stimuli.
- Repetition 0 is primary; repetitions 1-4 are sensitivity analyses.
- Seeds are derived from the verified manifest SHA-256.
- No rerolling after support inspection.
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
MANIFEST = REPO / "docs" / "joint_cv" / "deap_trial_manifest.csv"
FOLDS = REPO / "folds"
DOCS = REPO / "docs" / "joint_cv"
EXPECTED_BRANCH = "joint-cv-capacity-audit"

TASKS = ("valence", "arousal")
POLICIES = (
    "discard_midpoint",
    "midpoint_as_low",
    "midpoint_as_high",
)

OUTPUT_NAMES = {
    "protocol_json": "deap_4x4_label_blind_repeated_protocol.json",
    "assignments_csv": "deap_4x4_label_blind_repeated_assignments.csv",
    "primary_subject_csv": "deap_4x4_label_blind_primary_subject_folds.csv",
    "primary_stimulus_csv": "deap_4x4_label_blind_primary_stimulus_folds.csv",
    "support_csv": "deap_4x4_label_blind_repeated_support.csv",
    "decision_md": "deap_4x4_label_blind_protocol_decision.md",
    "decision_json": "deap_4x4_label_blind_protocol_decision.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--folds-dir", type=Path, default=FOLDS)
    parser.add_argument("--docs-dir", type=Path, default=DOCS)
    parser.add_argument("--repetitions", type=int, default=5)
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
        raise RuntimeError(proc.stderr.strip())
    return proc.stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


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


def deterministic_seed(
    manifest_hash: str,
    repetition: int,
    axis: str,
) -> int:
    payload = (
        f"{manifest_hash}|DEAP|strict-joint|4x4|"
        f"repetition={repetition}|axis={axis}"
    ).encode("utf-8")
    return int.from_bytes(
        hashlib.sha256(payload).digest()[:8],
        "big",
    ) % (2**32)


def fold_capacities(n: int, k: int) -> list[int]:
    base = n // k
    remainder = n % k
    return [
        base + (1 if index < remainder else 0)
        for index in range(k)
    ]


def assign_entities(
    entities: list[str],
    k: int,
    seed: int,
) -> dict[str, int]:
    rng = np.random.default_rng(seed)
    shuffled = list(entities)
    rng.shuffle(shuffled)

    assignment: dict[str, int] = {}
    cursor = 0
    for fold_index, capacity in enumerate(fold_capacities(len(entities), k)):
        for entity in shuffled[cursor:cursor + capacity]:
            assignment[entity] = fold_index
        cursor += capacity

    if len(assignment) != len(entities):
        raise RuntimeError("Incomplete fold assignment")
    return assignment


def prepare_outputs(
    folds_dir: Path,
    docs_dir: Path,
    overwrite: bool,
) -> dict[str, Path]:
    folds_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "protocol_json": folds_dir / OUTPUT_NAMES["protocol_json"],
        "assignments_csv": folds_dir / OUTPUT_NAMES["assignments_csv"],
        "primary_subject_csv": folds_dir / OUTPUT_NAMES["primary_subject_csv"],
        "primary_stimulus_csv": folds_dir / OUTPUT_NAMES["primary_stimulus_csv"],
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


def load_manifest(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)

    frame = pd.read_csv(path)
    required = {
        "trial_id",
        "subject_id",
        "stimulus_id",
        "chronology_verified",
        "stimulus_identity_verified",
        "mapping_verified",
        "eeg_available",
        "emg_available",
        *{
            f"{task}_{policy}"
            for task in TASKS
            for policy in POLICIES
        },
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Manifest missing columns: {missing}")

    frame = frame.copy()
    frame["trial_id"] = frame["trial_id"].astype(str)
    frame["subject_id"] = frame["subject_id"].astype(str)
    frame["stimulus_id"] = frame["stimulus_id"].astype(str)

    for column in (
        "chronology_verified",
        "stimulus_identity_verified",
        "mapping_verified",
        "eeg_available",
        "emg_available",
    ):
        values = frame[column].astype(str).str.lower()
        frame[column] = values.isin({"true", "1", "yes"})

    if len(frame) != 1280:
        raise ValueError(f"Expected 1280 rows, found {len(frame)}")
    if frame["subject_id"].nunique() != 32:
        raise ValueError("Expected 32 subjects")
    if frame["stimulus_id"].nunique() != 40:
        raise ValueError("Expected 40 stimuli")
    if frame["trial_id"].duplicated().any():
        raise ValueError("Duplicate trial_id")
    if frame.duplicated(["subject_id", "stimulus_id"]).any():
        raise ValueError("Duplicate subject-stimulus cells")

    for column in (
        "chronology_verified",
        "stimulus_identity_verified",
        "mapping_verified",
        "eeg_available",
        "emg_available",
    ):
        if not frame[column].all():
            raise ValueError(f"Not all rows pass {column}")

    return frame


def evaluate_repetition(
    manifest: pd.DataFrame,
    repetition: int,
    role: str,
    subject_assignment: dict[str, int],
    stimulus_assignment: dict[str, int],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    subject_fold = manifest["subject_id"].map(subject_assignment)
    stimulus_fold = manifest["stimulus_id"].map(stimulus_assignment)

    if subject_fold.isna().any() or stimulus_fold.isna().any():
        raise ValueError("Incomplete assignment mapping")

    support_rows: list[dict[str, Any]] = []
    min_test_class = None
    min_train_class = None
    min_test_retained = None
    max_removed_fraction = 0.0
    single_test_flags = 0
    single_train_flags = 0

    held_subject_counts = [
        int(sum(fold == index for fold in subject_assignment.values()))
        for index in range(4)
    ]
    held_stimulus_counts = [
        int(sum(fold == index for fold in stimulus_assignment.values()))
        for index in range(4)
    ]

    for subject_fold_index in range(4):
        held_subject = subject_fold.to_numpy() == subject_fold_index

        for stimulus_fold_index in range(4):
            held_stimulus = stimulus_fold.to_numpy() == stimulus_fold_index

            train_mask = (~held_subject) & (~held_stimulus)
            test_mask = held_subject & held_stimulus

            for task in TASKS:
                for policy in POLICIES:
                    column = f"{task}_{policy}"

                    train_values = pd.to_numeric(
                        manifest.loc[train_mask, column],
                        errors="coerce",
                    )
                    test_values = pd.to_numeric(
                        manifest.loc[test_mask, column],
                        errors="coerce",
                    )

                    train_retained = train_values.dropna().astype(int)
                    test_retained = test_values.dropna().astype(int)

                    train_low = int((train_retained == 0).sum())
                    train_high = int((train_retained == 1).sum())
                    test_low = int((test_retained == 0).sum())
                    test_high = int((test_retained == 1).sum())

                    train_single = train_low == 0 or train_high == 0
                    test_single = test_low == 0 or test_high == 0

                    single_train_flags += int(train_single)
                    single_test_flags += int(test_single)

                    current_test_min = min(test_low, test_high)
                    current_train_min = min(train_low, train_high)

                    min_test_class = (
                        current_test_min
                        if min_test_class is None
                        else min(min_test_class, current_test_min)
                    )
                    min_train_class = (
                        current_train_min
                        if min_train_class is None
                        else min(min_train_class, current_train_min)
                    )
                    min_test_retained = (
                        len(test_retained)
                        if min_test_retained is None
                        else min(min_test_retained, len(test_retained))
                    )

                    removed_fraction = float(
                        test_values.isna().mean()
                    )
                    max_removed_fraction = max(
                        max_removed_fraction,
                        removed_fraction,
                    )

                    support_rows.append(
                        {
                            "repetition": repetition,
                            "role": role,
                            "subject_fold": subject_fold_index,
                            "stimulus_fold": stimulus_fold_index,
                            "task": task,
                            "label_policy": policy,
                            "held_subjects": held_subject_counts[
                                subject_fold_index
                            ],
                            "held_stimuli": held_stimulus_counts[
                                stimulus_fold_index
                            ],
                            "train_rows_total": int(train_mask.sum()),
                            "train_rows_retained": int(len(train_retained)),
                            "train_low": train_low,
                            "train_high": train_high,
                            "train_min_class": current_train_min,
                            "train_single_class": train_single,
                            "test_rows_total": int(test_mask.sum()),
                            "test_rows_retained": int(len(test_retained)),
                            "test_low": test_low,
                            "test_high": test_high,
                            "test_min_class": current_test_min,
                            "test_single_class": test_single,
                            "midpoint_removed_fraction": removed_fraction,
                            "subject_leakage": False,
                            "stimulus_leakage": False,
                            "partition_uses_labels": False,
                        }
                    )

    assert min_test_class is not None
    assert min_train_class is not None
    assert min_test_retained is not None

    strong = bool(
        single_test_flags == 0
        and single_train_flags == 0
        and min_test_class >= 10
        and min_train_class >= 10
        and min(held_subject_counts) >= 6
        and min(held_stimulus_counts) >= 5
    )
    minimal = bool(
        single_test_flags == 0
        and single_train_flags == 0
        and min_test_class >= 5
    )

    summary = {
        "repetition": repetition,
        "role": role,
        "held_subjects_min": min(held_subject_counts),
        "held_subjects_max": max(held_subject_counts),
        "held_stimuli_min": min(held_stimulus_counts),
        "held_stimuli_max": max(held_stimulus_counts),
        "min_test_class": min_test_class,
        "min_train_class": min_train_class,
        "min_test_retained": min_test_retained,
        "max_midpoint_removed_fraction": max_removed_fraction,
        "single_class_test_flags": single_test_flags,
        "single_class_train_flags": single_train_flags,
        "strong_pass": strong,
        "minimal_pass": minimal,
    }
    return support_rows, summary


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
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


def main() -> None:
    args = parse_args()
    if args.repetitions != 5:
        raise ValueError("This protocol must use exactly 5 repetitions")

    repo = args.repo_root.resolve()
    manifest_path = args.manifest.resolve()
    branch = git(repo, "branch", "--show-current")
    head = git(repo, "rev-parse", "HEAD")

    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}"
        )

    outputs = prepare_outputs(
        args.folds_dir.resolve(),
        args.docs_dir.resolve(),
        args.overwrite,
    )
    manifest = load_manifest(manifest_path)
    manifest_hash = sha256_file(manifest_path)

    subjects = sorted(manifest["subject_id"].unique().tolist())
    stimuli = sorted(manifest["stimulus_id"].unique().tolist())

    assignments_rows: list[dict[str, Any]] = []
    support_rows: list[dict[str, Any]] = []
    repetition_summaries: list[dict[str, Any]] = []

    primary_subject_rows: list[dict[str, Any]] = []
    primary_stimulus_rows: list[dict[str, Any]] = []

    for repetition in range(args.repetitions):
        role = "primary" if repetition == 0 else "sensitivity"
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

        subject_assignment = assign_entities(
            subjects,
            4,
            subject_seed,
        )
        stimulus_assignment = assign_entities(
            stimuli,
            4,
            stimulus_seed,
        )

        for entity_id, fold_index in sorted(subject_assignment.items()):
            row = {
                "dataset": "DEAP",
                "repetition": repetition,
                "role": role,
                "axis": "subject",
                "entity_id": entity_id,
                "fold_index_0based": fold_index,
                "fold_index_1based": fold_index + 1,
                "seed": subject_seed,
                "partition_uses_labels": False,
                "manifest_sha256": manifest_hash,
            }
            assignments_rows.append(row)
            if repetition == 0:
                primary_subject_rows.append(row.copy())

        for entity_id, fold_index in sorted(stimulus_assignment.items()):
            row = {
                "dataset": "DEAP",
                "repetition": repetition,
                "role": role,
                "axis": "stimulus",
                "entity_id": entity_id,
                "fold_index_0based": fold_index,
                "fold_index_1based": fold_index + 1,
                "seed": stimulus_seed,
                "partition_uses_labels": False,
                "manifest_sha256": manifest_hash,
            }
            assignments_rows.append(row)
            if repetition == 0:
                primary_stimulus_rows.append(row.copy())

        rep_support, rep_summary = evaluate_repetition(
            manifest,
            repetition,
            role,
            subject_assignment,
            stimulus_assignment,
        )
        support_rows.extend(rep_support)
        repetition_summaries.append(rep_summary)

    primary = repetition_summaries[0]
    all_minimal = all(
        row["minimal_pass"] for row in repetition_summaries
    )
    all_strong = all(
        row["strong_pass"] for row in repetition_summaries
    )
    sensitivity_strong_rate = float(
        np.mean(
            [
                row["strong_pass"]
                for row in repetition_summaries[1:]
            ]
        )
    )

    if primary["strong_pass"] and all_minimal:
        decision = "LOCK_LABEL_BLIND_4X4_PROTOCOL"
        reason = (
            "The pre-registered primary repetition passes the strong "
            "capacity gate, and every pre-registered sensitivity "
            "repetition passes the minimum capacity gate."
        )
    elif primary["minimal_pass"] and all_minimal:
        decision = "LOCK_4X4_WITH_CAPACITY_CAUTION"
        reason = (
            "The primary repetition and all sensitivity repetitions pass "
            "minimum capacity, but the primary repetition does not pass "
            "the strong capacity gate."
        )
    else:
        decision = "DO_NOT_LOCK_PROTOCOL"
        reason = (
            "At least one pre-registered repetition fails the minimum "
            "capacity gate. Do not reroll seeds."
        )

    protocol = {
        "dataset": "DEAP",
        "decision": decision,
        "reason": reason,
        "branch": branch,
        "head": head,
        "manifest": str(manifest_path),
        "manifest_sha256": manifest_hash,
        "repetitions": args.repetitions,
        "primary_repetition": 0,
        "sensitivity_repetitions": [1, 2, 3, 4],
        "subject_folds": 4,
        "stimulus_folds": 4,
        "outer_cells_per_repetition": 16,
        "all_subject_by_stimulus_fold_combinations": True,
        "partition_uses_labels": False,
        "rerolling_allowed": False,
        "train_region": "source_subjects_x_source_stimuli",
        "primary_test_region": "held_subjects_x_held_stimuli",
        "strong_gate": {
            "single_class_test_flags": 0,
            "single_class_train_flags": 0,
            "min_test_class": 10,
            "min_train_class": 10,
            "min_held_subjects": 6,
            "min_held_stimuli": 5,
        },
        "minimal_gate": {
            "single_class_test_flags": 0,
            "single_class_train_flags": 0,
            "min_test_class": 5,
        },
        "repetition_summaries": repetition_summaries,
    }

    outputs["protocol_json"].write_text(
        json.dumps(safe_json(protocol), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_csv(outputs["assignments_csv"], assignments_rows)
    write_csv(outputs["primary_subject_csv"], primary_subject_rows)
    write_csv(outputs["primary_stimulus_csv"], primary_stimulus_rows)
    write_csv(outputs["support_csv"], support_rows)

    decision_payload = {
        **protocol,
        "all_repetitions_pass_minimum_capacity": all_minimal,
        "all_repetitions_pass_strong_capacity": all_strong,
        "sensitivity_strong_pass_rate": sensitivity_strong_rate,
    }
    outputs["decision_json"].write_text(
        json.dumps(
            safe_json(decision_payload),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    table_rows = []
    for row in repetition_summaries:
        table_rows.append(
            {
                "repetition": row["repetition"],
                "role": row["role"],
                "held_subjects": (
                    f"{row['held_subjects_min']}.."
                    f"{row['held_subjects_max']}"
                ),
                "held_stimuli": (
                    f"{row['held_stimuli_min']}.."
                    f"{row['held_stimuli_max']}"
                ),
                "min_test_class": row["min_test_class"],
                "min_train_class": row["min_train_class"],
                "min_test_retained": row["min_test_retained"],
                "max_midpoint_removed_fraction": round(
                    row["max_midpoint_removed_fraction"],
                    6,
                ),
                "single_class_test_flags": row[
                    "single_class_test_flags"
                ],
                "single_class_train_flags": row[
                    "single_class_train_flags"
                ],
                "strong_pass": row["strong_pass"],
                "minimal_pass": row["minimal_pass"],
            }
        )

    md_lines = [
        "# DEAP Label-Blind Repeated 4x4 Protocol Decision",
        "",
        "No model training was performed.",
        "",
        "## Frozen Construction Rule",
        "",
        f"- Manifest SHA-256: `{manifest_hash}`",
        "- Repetitions: `5`",
        "- Repetition 0: primary benchmark",
        "- Repetitions 1–4: sensitivity analysis",
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
        f"- All repetitions pass minimum capacity: `{all_minimal}`",
        f"- All repetitions pass strong capacity: `{all_strong}`",
        f"- Sensitivity strong-pass rate: `{sensitivity_strong_rate:.4f}`",
        "",
        "## Status of 5x5",
        "",
        "- The 5x5 scheme remains non-primary because its strong-pass rate "
        "was only 0.644 under label-blind random partitions.",
        "- Do not substitute or reroll the 4x4 repetitions after seeing "
        "their support.",
        "",
        "## Next Audit Before Model Training",
        "",
        "Run leakage-safe shortcut baselines, presentation-order "
        "confounding analysis, and null/permutation tests on the frozen "
        "DEAP partitions.",
        "",
    ]
    outputs["decision_md"].write_text(
        "\n".join(md_lines),
        encoding="utf-8",
    )

    print("DEAP label-blind repeated 4x4 protocol audit completed.")
    print(f"Branch: {branch}")
    print(f"HEAD: {head}")
    print(f"Manifest SHA-256: {manifest_hash}")
    print(f"Repetitions: {args.repetitions}")
    for row in repetition_summaries:
        print(
            f"rep{row['repetition']:02d} ({row['role']}): "
            f"min_test_class={row['min_test_class']}, "
            f"single_class_test={row['single_class_test_flags']}, "
            f"strong={row['strong_pass']}, "
            f"minimal={row['minimal_pass']}"
        )
    print(f"Decision: {decision}")
    print(f"Report: {outputs['decision_md']}")
    print(f"Protocol JSON: {outputs['protocol_json']}")


if __name__ == "__main__":
    main()

