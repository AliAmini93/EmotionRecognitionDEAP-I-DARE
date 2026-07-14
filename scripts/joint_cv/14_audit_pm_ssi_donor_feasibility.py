#!/usr/bin/env python3
"""Audit PM-SSI donor-pool feasibility on frozen DEAP and I-DARE Joint-CV.

No EEG/EMG feature extraction, augmentation, representation learning, fusion,
TTA, PM-SSI-DG training, or LRSC training is performed.

For every source-training physical-trial anchor, an eligible PM-SSI donor must:
1. be inside the same outer-cell source train region;
2. have the same binary class as the anchor;
3. belong to a different subject;
4. belong to a different stimulus;
5. have paired EEG and EMG available;
6. be a different physical trial.

The audit is repeated for:
- DEAP frozen repeated label-blind 4x4 protocol;
- I-DARE frozen repeated label-blind 4x4 protocol;
- five repetitions;
- all 16 outer cells;
- valence and arousal;
- discard-midpoint, midpoint-as-low, and midpoint-as-high policies.

This script does not choose donors and does not freeze augmentation randomness.
It only measures the legal donor support available before model training.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE")
DOCS = REPO / "docs" / "joint_cv"
FOLDS = REPO / "folds"
EXPECTED_BRANCH = "joint-cv-capacity-audit"

DATASETS = {
    "DEAP": {
        "manifest": DOCS / "deap_trial_manifest.csv",
        "assignments": FOLDS / "deap_4x4_label_blind_repeated_assignments.csv",
        "protocol": FOLDS / "deap_4x4_label_blind_repeated_protocol.json",
        "expected_subjects": 32,
        "expected_stimuli": 40,
        "expected_trials": 1280,
        "expected_assignment_rows": 360,
    },
    "I-DARE": {
        "manifest": DOCS / "idare_trial_manifest.csv",
        "assignments": FOLDS / "idare_4x4_label_blind_repeated_assignments.csv",
        "protocol": FOLDS / "idare_4x4_label_blind_repeated_protocol.json",
        "expected_subjects": 63,
        "expected_stimuli": 32,
        "expected_trials": 2016,
        "expected_assignment_rows": 475,
    },
}

TASKS = ("valence", "arousal")
POLICIES = (
    "discard_midpoint",
    "midpoint_as_low",
    "midpoint_as_high",
)

OUTPUTS = {
    "anchor_csv_gz": DOCS / "pm_ssi_donor_anchor_support.csv.gz",
    "cell_csv": DOCS / "pm_ssi_donor_cell_support.csv",
    "summary_csv": DOCS / "pm_ssi_donor_protocol_summary.csv",
    "report_md": DOCS / "pm_ssi_donor_feasibility_audit.md",
    "report_json": DOCS / "pm_ssi_donor_feasibility_audit.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--docs-dir", type=Path, default=DOCS)
    parser.add_argument("--folds-dir", type=Path, default=FOLDS)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def git(repo: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip())
    return process.stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def bool_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .isin({"true", "1", "yes", "y"})
    )


def safe_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): safe_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [safe_json(item) for item in value]
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


def prepare_outputs(overwrite: bool) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    if overwrite:
        return
    existing = [path for path in OUTPUTS.values() if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing outputs:\n"
            + "\n".join(f"- {path}" for path in existing)
        )


def load_dataset(
    dataset: str,
    config: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], str]:
    manifest_path = Path(config["manifest"])
    assignment_path = Path(config["assignments"])
    protocol_path = Path(config["protocol"])

    for path in (manifest_path, assignment_path, protocol_path):
        if not path.exists():
            raise FileNotFoundError(path)

    manifest = pd.read_csv(manifest_path)
    assignments = pd.read_csv(assignment_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    manifest_hash = sha256_file(manifest_path)

    required_manifest = {
        "trial_id",
        "subject_id",
        "stimulus_id",
        "eeg_available",
        "emg_available",
        *{
            f"{task}_{policy}"
            for task in TASKS
            for policy in POLICIES
        },
    }
    missing = sorted(required_manifest - set(manifest.columns))
    if missing:
        raise ValueError(f"{dataset} manifest missing columns: {missing}")

    manifest = manifest.copy()
    manifest["trial_id"] = manifest["trial_id"].astype(str)
    manifest["subject_id"] = manifest["subject_id"].astype(str)
    manifest["stimulus_id"] = manifest["stimulus_id"].astype(str)
    manifest["eeg_available"] = bool_series(manifest["eeg_available"])
    manifest["emg_available"] = bool_series(manifest["emg_available"])
    manifest["paired_modalities_available"] = (
        manifest["eeg_available"] & manifest["emg_available"]
    )

    if len(manifest) != config["expected_trials"]:
        raise ValueError(
            f"{dataset}: expected {config['expected_trials']} trials, "
            f"found {len(manifest)}"
        )
    if manifest["subject_id"].nunique() != config["expected_subjects"]:
        raise ValueError(f"{dataset}: unexpected subject count")
    if manifest["stimulus_id"].nunique() != config["expected_stimuli"]:
        raise ValueError(f"{dataset}: unexpected stimulus count")
    if manifest["trial_id"].duplicated().any():
        raise ValueError(f"{dataset}: duplicate trial_id")
    if manifest.duplicated(["subject_id", "stimulus_id"]).any():
        raise ValueError(f"{dataset}: duplicate subject-stimulus cell")

    required_assignments = {
        "repetition",
        "role",
        "axis",
        "entity_id",
        "fold_index_0based",
        "partition_uses_labels",
        "manifest_sha256",
    }
    missing_assignments = sorted(
        required_assignments - set(assignments.columns)
    )
    if missing_assignments:
        raise ValueError(
            f"{dataset} assignments missing columns: {missing_assignments}"
        )

    assignments = assignments.copy()
    assignments["repetition"] = pd.to_numeric(
        assignments["repetition"],
        errors="raise",
    ).astype(int)
    assignments["entity_id"] = assignments["entity_id"].astype(str)
    assignments["fold_index_0based"] = pd.to_numeric(
        assignments["fold_index_0based"],
        errors="raise",
    ).astype(int)

    if len(assignments) != config["expected_assignment_rows"]:
        raise ValueError(
            f"{dataset}: expected {config['expected_assignment_rows']} "
            f"assignment rows, found {len(assignments)}"
        )
    if sorted(assignments["repetition"].unique().tolist()) != [0, 1, 2, 3, 4]:
        raise ValueError(f"{dataset}: repetitions are not 0..4")
    if bool_series(assignments["partition_uses_labels"]).any():
        raise ValueError(f"{dataset}: assignments unexpectedly use labels")
    if set(assignments["manifest_sha256"].astype(str)) != {manifest_hash}:
        raise ValueError(f"{dataset}: assignment manifest hash mismatch")

    if protocol.get("decision") != "LOCK_LABEL_BLIND_4X4_PROTOCOL":
        raise ValueError(f"{dataset}: protocol is not locked")
    if protocol.get("manifest_sha256") != manifest_hash:
        raise ValueError(f"{dataset}: protocol manifest hash mismatch")
    if protocol.get("partition_uses_labels") is not False:
        raise ValueError(f"{dataset}: protocol unexpectedly uses labels")
    if protocol.get("subject_folds") != 4:
        raise ValueError(f"{dataset}: expected four subject folds")
    if protocol.get("stimulus_folds") != 4:
        raise ValueError(f"{dataset}: expected four stimulus folds")

    return manifest, assignments, protocol, manifest_hash


def assignments_for_repetition(
    assignments: pd.DataFrame,
    repetition: int,
    expected_subjects: int,
    expected_stimuli: int,
) -> tuple[dict[str, int], dict[str, int]]:
    subset = assignments[assignments["repetition"] == repetition]
    subject_assignment = {
        str(row["entity_id"]): int(row["fold_index_0based"])
        for _, row in subset[subset["axis"] == "subject"].iterrows()
    }
    stimulus_assignment = {
        str(row["entity_id"]): int(row["fold_index_0based"])
        for _, row in subset[subset["axis"] == "stimulus"].iterrows()
    }

    if len(subject_assignment) != expected_subjects:
        raise ValueError(
            f"rep {repetition}: expected {expected_subjects} subject assignments"
        )
    if len(stimulus_assignment) != expected_stimuli:
        raise ValueError(
            f"rep {repetition}: expected {expected_stimuli} stimulus assignments"
        )
    return subject_assignment, stimulus_assignment


def quantile(values: np.ndarray, q: float) -> float:
    if len(values) == 0:
        return float("nan")
    return float(np.quantile(values, q))


def operational_verdict(
    zero_rate: float,
    below_5_rate: float,
    below_20_rate: float,
    minimum: int,
) -> str:
    if zero_rate > 0:
        return "FAIL_ZERO_DONOR_ANCHORS"
    if minimum >= 20:
        return "PASS_STRONG"
    if below_5_rate == 0:
        return "PASS_MINIMAL"
    if below_20_rate < 0.05:
        return "PASS_WITH_RARE_LOW_SUPPORT"
    return "LIMITED_DONOR_SUPPORT"


def audit_cell(
    train: pd.DataFrame,
    *,
    dataset: str,
    repetition: int,
    role: str,
    subject_fold: int,
    stimulus_fold: int,
    task: str,
    policy: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    label_column = f"{task}_{policy}"
    labels = pd.to_numeric(train[label_column], errors="coerce")
    usable = train[
        labels.notna() & train["paired_modalities_available"]
    ].copy()
    usable["_label"] = labels.loc[usable.index].astype(int)

    if len(usable) == 0:
        raise ValueError(
            f"{dataset} rep={repetition} cell={subject_fold},{stimulus_fold} "
            f"{task}/{policy}: no usable source anchors"
        )

    class_counts = usable["_label"].value_counts().to_dict()
    subject_class_counts = (
        usable.groupby(["subject_id", "_label"]).size().to_dict()
    )
    stimulus_class_counts = (
        usable.groupby(["stimulus_id", "_label"]).size().to_dict()
    )

    class_groups = {
        int(label): group.copy()
        for label, group in usable.groupby("_label", sort=True)
    }

    anchor_rows: list[dict[str, Any]] = []

    for _, anchor in usable.iterrows():
        label = int(anchor["_label"])
        subject_id = str(anchor["subject_id"])
        stimulus_id = str(anchor["stimulus_id"])

        total_same_class = int(class_counts[label])
        same_subject_same_class = int(
            subject_class_counts[(subject_id, label)]
        )
        same_stimulus_same_class = int(
            stimulus_class_counts[(stimulus_id, label)]
        )

        eligible_count = (
            total_same_class
            - same_subject_same_class
            - same_stimulus_same_class
            + 1
        )

        candidates = class_groups[label]
        legal = candidates[
            (candidates["subject_id"] != subject_id)
            & (candidates["stimulus_id"] != stimulus_id)
            & (candidates["trial_id"] != str(anchor["trial_id"]))
        ]

        if len(legal) != eligible_count:
            raise AssertionError(
                f"Eligibility formula mismatch for {dataset} "
                f"{anchor['trial_id']}: formula={eligible_count}, "
                f"explicit={len(legal)}"
            )
        if eligible_count < 0:
            raise AssertionError("Negative donor count")

        unique_donor_subjects = int(legal["subject_id"].nunique())
        unique_donor_stimuli = int(legal["stimulus_id"].nunique())

        anchor_rows.append(
            {
                "dataset": dataset,
                "repetition": repetition,
                "role": role,
                "subject_fold": subject_fold,
                "stimulus_fold": stimulus_fold,
                "task": task,
                "label_policy": policy,
                "anchor_trial_id": str(anchor["trial_id"]),
                "anchor_subject_id": subject_id,
                "anchor_stimulus_id": stimulus_id,
                "anchor_class": label,
                "source_train_rows_total": int(len(train)),
                "source_train_scored_paired_rows": int(len(usable)),
                "same_class_source_pool": total_same_class,
                "same_subject_same_class_excluded": same_subject_same_class,
                "same_stimulus_same_class_excluded": same_stimulus_same_class,
                "eligible_donor_count": int(eligible_count),
                "unique_eligible_donor_subjects": unique_donor_subjects,
                "unique_eligible_donor_stimuli": unique_donor_stimuli,
                "zero_donor": bool(eligible_count == 0),
                "below_5_donors": bool(eligible_count < 5),
                "below_10_donors": bool(eligible_count < 10),
                "below_20_donors": bool(eligible_count < 20),
                "anchor_paired_eeg_emg": True,
                "donors_restricted_to_source_train": True,
                "same_subject_donors_excluded": True,
                "same_stimulus_donors_excluded": True,
                "test_donors_excluded": True,
            }
        )

    anchor_frame = pd.DataFrame(anchor_rows)
    counts = anchor_frame["eligible_donor_count"].to_numpy(dtype=int)
    donor_subject_counts = anchor_frame[
        "unique_eligible_donor_subjects"
    ].to_numpy(dtype=int)
    donor_stimulus_counts = anchor_frame[
        "unique_eligible_donor_stimuli"
    ].to_numpy(dtype=int)

    zero_rate = float(np.mean(counts == 0))
    below_5_rate = float(np.mean(counts < 5))
    below_10_rate = float(np.mean(counts < 10))
    below_20_rate = float(np.mean(counts < 20))

    cell_row = {
        "dataset": dataset,
        "repetition": repetition,
        "role": role,
        "subject_fold": subject_fold,
        "stimulus_fold": stimulus_fold,
        "task": task,
        "label_policy": policy,
        "source_train_rows_total": int(len(train)),
        "source_train_scored_paired_rows": int(len(anchor_frame)),
        "class_0_anchors": int((anchor_frame["anchor_class"] == 0).sum()),
        "class_1_anchors": int((anchor_frame["anchor_class"] == 1).sum()),
        "eligible_donors_min": int(counts.min()),
        "eligible_donors_p01": quantile(counts, 0.01),
        "eligible_donors_p10": quantile(counts, 0.10),
        "eligible_donors_median": float(np.median(counts)),
        "eligible_donors_p90": quantile(counts, 0.90),
        "eligible_donors_max": int(counts.max()),
        "zero_donor_rate": zero_rate,
        "below_5_donor_rate": below_5_rate,
        "below_10_donor_rate": below_10_rate,
        "below_20_donor_rate": below_20_rate,
        "unique_donor_subjects_min": int(donor_subject_counts.min()),
        "unique_donor_subjects_median": float(
            np.median(donor_subject_counts)
        ),
        "unique_donor_stimuli_min": int(donor_stimulus_counts.min()),
        "unique_donor_stimuli_median": float(
            np.median(donor_stimulus_counts)
        ),
        "paired_modality_anchor_rate": 1.0,
        "operational_verdict": operational_verdict(
            zero_rate,
            below_5_rate,
            below_20_rate,
            int(counts.min()),
        ),
    }
    return anchor_rows, cell_row


def run_dataset(
    dataset: str,
    config: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    manifest, assignments, protocol, manifest_hash = load_dataset(
        dataset,
        config,
    )

    all_anchor_rows: list[dict[str, Any]] = []
    all_cell_rows: list[dict[str, Any]] = []

    for repetition in range(5):
        role = "primary" if repetition == 0 else "sensitivity"
        subject_assignment, stimulus_assignment = (
            assignments_for_repetition(
                assignments,
                repetition,
                config["expected_subjects"],
                config["expected_stimuli"],
            )
        )

        subject_folds = manifest["subject_id"].map(subject_assignment)
        stimulus_folds = manifest["stimulus_id"].map(
            stimulus_assignment
        )
        if subject_folds.isna().any() or stimulus_folds.isna().any():
            raise ValueError(f"{dataset}: incomplete fold mapping")

        for subject_fold in range(4):
            held_subject = subject_folds.to_numpy(dtype=int) == subject_fold

            for stimulus_fold in range(4):
                held_stimulus = (
                    stimulus_folds.to_numpy(dtype=int) == stimulus_fold
                )
                train_mask = (~held_subject) & (~held_stimulus)
                train = manifest.loc[train_mask].copy()

                held_subject_ids = set(
                    manifest.loc[held_subject, "subject_id"].astype(str)
                )
                held_stimulus_ids = set(
                    manifest.loc[held_stimulus, "stimulus_id"].astype(str)
                )

                if set(train["subject_id"].astype(str)) & held_subject_ids:
                    raise AssertionError("Subject leakage into source train")
                if set(train["stimulus_id"].astype(str)) & held_stimulus_ids:
                    raise AssertionError("Stimulus leakage into source train")

                for task in TASKS:
                    for policy in POLICIES:
                        anchor_rows, cell_row = audit_cell(
                            train,
                            dataset=dataset,
                            repetition=repetition,
                            role=role,
                            subject_fold=subject_fold,
                            stimulus_fold=stimulus_fold,
                            task=task,
                            policy=policy,
                        )
                        all_anchor_rows.extend(anchor_rows)
                        all_cell_rows.append(cell_row)

    metadata = {
        "dataset": dataset,
        "manifest": str(config["manifest"]),
        "manifest_sha256": manifest_hash,
        "protocol": str(config["protocol"]),
        "protocol_decision": protocol.get("decision"),
        "anchor_rows": len(all_anchor_rows),
        "cell_rows": len(all_cell_rows),
    }
    return all_anchor_rows, all_cell_rows, metadata


def summarize_protocol(
    anchor_frame: pd.DataFrame,
    cell_frame: pd.DataFrame,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    group_columns = [
        "dataset",
        "repetition",
        "role",
        "task",
        "label_policy",
    ]

    for keys, group in anchor_frame.groupby(
        group_columns,
        sort=True,
    ):
        dataset, repetition, role, task, policy = keys
        counts = group["eligible_donor_count"].to_numpy(dtype=int)
        subject_diversity = group[
            "unique_eligible_donor_subjects"
        ].to_numpy(dtype=int)
        stimulus_diversity = group[
            "unique_eligible_donor_stimuli"
        ].to_numpy(dtype=int)

        matching_cells = cell_frame[
            (cell_frame["dataset"] == dataset)
            & (cell_frame["repetition"] == repetition)
            & (cell_frame["task"] == task)
            & (cell_frame["label_policy"] == policy)
        ]

        zero_rate = float(np.mean(counts == 0))
        below_5_rate = float(np.mean(counts < 5))
        below_10_rate = float(np.mean(counts < 10))
        below_20_rate = float(np.mean(counts < 20))

        rows.append(
            {
                "dataset": dataset,
                "repetition": int(repetition),
                "role": role,
                "task": task,
                "label_policy": policy,
                "anchor_occurrences": int(len(group)),
                "outer_cells": int(len(matching_cells)),
                "eligible_donors_min": int(counts.min()),
                "eligible_donors_p01": quantile(counts, 0.01),
                "eligible_donors_p10": quantile(counts, 0.10),
                "eligible_donors_median": float(np.median(counts)),
                "eligible_donors_p90": quantile(counts, 0.90),
                "eligible_donors_max": int(counts.max()),
                "zero_donor_rate": zero_rate,
                "below_5_donor_rate": below_5_rate,
                "below_10_donor_rate": below_10_rate,
                "below_20_donor_rate": below_20_rate,
                "unique_donor_subjects_min": int(
                    subject_diversity.min()
                ),
                "unique_donor_subjects_median": float(
                    np.median(subject_diversity)
                ),
                "unique_donor_stimuli_min": int(
                    stimulus_diversity.min()
                ),
                "unique_donor_stimuli_median": float(
                    np.median(stimulus_diversity)
                ),
                "worst_cell_min_donors": int(
                    matching_cells["eligible_donors_min"].min()
                ),
                "cells_with_zero_donor_anchors": int(
                    (
                        matching_cells["zero_donor_rate"] > 0
                    ).sum()
                ),
                "operational_verdict": operational_verdict(
                    zero_rate,
                    below_5_rate,
                    below_20_rate,
                    int(counts.min()),
                ),
            }
        )

    return rows


def dataset_decision(
    summary_frame: pd.DataFrame,
    dataset: str,
) -> dict[str, Any]:
    primary_main = summary_frame[
        (summary_frame["dataset"] == dataset)
        & (summary_frame["repetition"] == 0)
        & (summary_frame["label_policy"] == "discard_midpoint")
    ].copy()
    all_rows = summary_frame[summary_frame["dataset"] == dataset].copy()

    if len(primary_main) != 2:
        raise ValueError(
            f"{dataset}: expected two primary main-policy task rows"
        )

    primary_zero = float(primary_main["zero_donor_rate"].max())
    primary_min = int(primary_main["eligible_donors_min"].min())
    primary_below_20 = float(
        primary_main["below_20_donor_rate"].max()
    )
    all_zero = float(all_rows["zero_donor_rate"].max())
    all_min = int(all_rows["eligible_donors_min"].min())

    if primary_zero == 0 and primary_min >= 20:
        verdict = "PM_SSI_DONOR_SUPPORT_STRONG"
    elif primary_zero == 0 and primary_min >= 5:
        verdict = "PM_SSI_DONOR_SUPPORT_MINIMAL"
    elif primary_zero == 0:
        verdict = "PM_SSI_DONOR_SUPPORT_LIMITED"
    else:
        verdict = "PM_SSI_DONOR_SUPPORT_INSUFFICIENT"

    return {
        "dataset": dataset,
        "verdict": verdict,
        "primary_discard_midpoint_zero_donor_rate_max": primary_zero,
        "primary_discard_midpoint_min_donors": primary_min,
        "primary_discard_midpoint_below_20_rate_max": primary_below_20,
        "all_repetitions_policies_zero_donor_rate_max": all_zero,
        "all_repetitions_policies_min_donors": all_min,
        "interpretation": (
            "Strong means every primary main-policy source anchor has at "
            "least 20 legal same-class donors from different subjects and "
            "different stimuli. This is an operational audit threshold, "
            "not a guarantee of model benefit."
        ),
    }


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
    repo = args.repo_root.resolve()
    branch = git(repo, "branch", "--show-current")
    head = git(repo, "rev-parse", "HEAD")

    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}"
        )

    prepare_outputs(args.overwrite)

    all_anchor_rows: list[dict[str, Any]] = []
    all_cell_rows: list[dict[str, Any]] = []
    dataset_metadata: list[dict[str, Any]] = []

    for dataset, config in DATASETS.items():
        anchor_rows, cell_rows, metadata = run_dataset(
            dataset,
            config,
        )
        all_anchor_rows.extend(anchor_rows)
        all_cell_rows.extend(cell_rows)
        dataset_metadata.append(metadata)

    anchor_frame = pd.DataFrame(all_anchor_rows)
    cell_frame = pd.DataFrame(all_cell_rows)
    summary_rows = summarize_protocol(anchor_frame, cell_frame)
    summary_frame = pd.DataFrame(summary_rows)

    with gzip.open(
        OUTPUTS["anchor_csv_gz"],
        mode="wt",
        encoding="utf-8",
        newline="",
        compresslevel=6,
    ) as handle:
        anchor_frame.to_csv(handle, index=False)

    cell_frame.to_csv(OUTPUTS["cell_csv"], index=False)
    summary_frame.to_csv(OUTPUTS["summary_csv"], index=False)

    decisions = {
        dataset: dataset_decision(summary_frame, dataset)
        for dataset in DATASETS
    }

    primary_rows = summary_frame[
        (summary_frame["repetition"] == 0)
        & (
            summary_frame["label_policy"]
            == "discard_midpoint"
        )
    ].copy()

    table_rows: list[dict[str, Any]] = []
    for _, row in primary_rows.sort_values(
        ["dataset", "task"]
    ).iterrows():
        table_rows.append(
            {
                "dataset": row["dataset"],
                "task": row["task"],
                "anchors": int(row["anchor_occurrences"]),
                "min": int(row["eligible_donors_min"]),
                "p10": round(float(row["eligible_donors_p10"]), 1),
                "median": round(
                    float(row["eligible_donors_median"]),
                    1,
                ),
                "p90": round(float(row["eligible_donors_p90"]), 1),
                "max": int(row["eligible_donors_max"]),
                "zero_rate": round(
                    float(row["zero_donor_rate"]),
                    6,
                ),
                "below_5_rate": round(
                    float(row["below_5_donor_rate"]),
                    6,
                ),
                "below_20_rate": round(
                    float(row["below_20_donor_rate"]),
                    6,
                ),
                "min_unique_subjects": int(
                    row["unique_donor_subjects_min"]
                ),
                "min_unique_stimuli": int(
                    row["unique_donor_stimuli_min"]
                ),
                "verdict": row["operational_verdict"],
            }
        )

    report_payload = {
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "training_performed": False,
        "eligibility_rule": {
            "same_outer_cell_source_train": True,
            "same_binary_class": True,
            "different_subject": True,
            "different_stimulus": True,
            "paired_eeg_emg": True,
            "different_physical_trial": True,
            "test_trials_allowed_as_donors": False,
        },
        "operational_gates": {
            "strong": (
                "zero donor rate = 0 and minimum eligible donors >= 20"
            ),
            "minimal": (
                "zero donor rate = 0 and no anchor has fewer than 5 donors"
            ),
            "note": (
                "These thresholds measure source-pool capacity and are not "
                "a theorem about augmentation quality."
            ),
        },
        "dataset_metadata": dataset_metadata,
        "dataset_decisions": decisions,
        "primary_discard_midpoint_summary": table_rows,
        "output_shapes": {
            "anchor_rows": len(anchor_frame),
            "cell_rows": len(cell_frame),
            "summary_rows": len(summary_frame),
        },
        "outputs": {
            key: str(path) for key, path in OUTPUTS.items()
        },
    }

    OUTPUTS["report_json"].write_text(
        json.dumps(
            safe_json(report_payload),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    md_lines = [
        "# PM-SSI Legal Donor-Pool Feasibility Audit",
        "",
        "No EEG/EMG representation or model was trained.",
        "",
        "## Legal Donor Rule",
        "",
        "For every source-training physical-trial anchor, the donor must "
        "be in the same source-train region, have the same binary class, "
        "come from a different subject and a different stimulus, have "
        "paired EEG+EMG, and be a different physical trial.",
        "",
        "No primary-test or diagnostic-test trial is allowed to act as a donor.",
        "",
        "## Primary Repetition, Discard-Midpoint Policy",
        "",
        markdown_table(
            table_rows,
            [
                "dataset",
                "task",
                "anchors",
                "min",
                "p10",
                "median",
                "p90",
                "max",
                "zero_rate",
                "below_5_rate",
                "below_20_rate",
                "min_unique_subjects",
                "min_unique_stimuli",
                "verdict",
            ],
        ),
        "",
        "## Dataset Decisions",
        "",
    ]

    for dataset in DATASETS:
        decision = decisions[dataset]
        md_lines.extend(
            [
                f"### {dataset}",
                "",
                f"- Verdict: **{decision['verdict']}**",
                "- Primary discard-midpoint maximum zero-donor rate: "
                f"`{decision['primary_discard_midpoint_zero_donor_rate_max']:.6f}`",
                "- Primary discard-midpoint minimum legal donors: "
                f"`{decision['primary_discard_midpoint_min_donors']}`",
                "- Worst minimum over all policies and repetitions: "
                f"`{decision['all_repetitions_policies_min_donors']}`",
                "",
            ]
        )

    md_lines.extend(
        [
            "## Interpretation Boundary",
            "",
            "- This audit establishes availability, not usefulness.",
            "- Donor labels are used only inside source training.",
            "- The donor cannot share the anchor subject or stimulus.",
            "- A later implementation must sample donors only after the "
            "outer split is fixed.",
            "- Hyperparameters must not be tuned on repetitions 1–4.",
            "",
            "## Next Step",
            "",
            "After reviewing this donor-capacity result, audit LRSC-TTA "
            "chronological stream feasibility for both datasets using the "
            "verified presentation order and frozen folds.",
            "",
        ]
    )

    OUTPUTS["report_md"].write_text(
        "\n".join(md_lines),
        encoding="utf-8",
    )

    print("PM-SSI donor-pool feasibility audit completed.")
    print(f"Branch: {branch}")
    print(f"HEAD: {head}")
    print(f"Anchor support rows: {len(anchor_frame)}")
    print(f"Cell support rows: {len(cell_frame)}")
    print(f"Protocol summary rows: {len(summary_frame)}")
    for dataset in DATASETS:
        decision = decisions[dataset]
        print(
            f"{dataset}: {decision['verdict']}, "
            f"primary_min={decision['primary_discard_midpoint_min_donors']}, "
            f"primary_zero_rate_max="
            f"{decision['primary_discard_midpoint_zero_donor_rate_max']:.6f}"
        )
    print(f"Report: {OUTPUTS['report_md']}")


if __name__ == "__main__":
    main()

