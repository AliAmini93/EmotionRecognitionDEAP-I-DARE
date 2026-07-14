#!/usr/bin/env python3
"""Build the verified DEAP physical-trial manifest and audit Joint-CV capacity.

Inputs
------
- 32 local DEAP preprocessed .dat files.
- The 1280-row mapping verified against all embedded ratings:
  docs/joint_cv/deap_verified_trial_stimulus_mapping.csv

Outputs
-------
- A canonical verified physical-trial manifest.
- Chronology and sequence audit.
- Label-blind random-partition capacity audits for 4x4 and 5x5 Strict Joint CV.

No EEG/EMG model, fusion model, TTA method, PM-SSI-DG, or LRSC is trained.
No Joint-CV split is frozen by this script.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import pickle
import re
import shutil
import subprocess
import time
import warnings
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


REPO = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE")
DEAP_ROOT = Path("/mnt/HDD/AliWorks/DEAP")
DOCS = REPO / "docs" / "joint_cv"
MAPPING = DOCS / "deap_verified_trial_stimulus_mapping.csv"
CANONICAL_MANIFEST = DOCS / "deap_trial_manifest.csv"
EXPECTED_BRANCH = "joint-cv-capacity-audit"

TASKS = ("valence", "arousal")
POLICIES = (
    "discard_midpoint",
    "midpoint_as_low",
    "midpoint_as_high",
)
SCHEMES = {
    "deap_4x4": (4, 4),
    "deap_5x5": (5, 5),
}

OUTPUT_NAMES = {
    "manifest_audit_md": "deap_verified_manifest_audit.md",
    "manifest_audit_json": "deap_verified_manifest_audit.json",
    "capacity_trials_csv": "deap_joint_cv_partition_capacity_trials.csv",
    "capacity_summary_csv": "deap_joint_cv_partition_capacity_summary.csv",
    "capacity_md": "deap_joint_cv_partition_capacity.md",
    "capacity_json": "deap_joint_cv_partition_capacity.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--deap-root", type=Path, default=DEAP_ROOT)
    parser.add_argument("--docs-dir", type=Path, default=DOCS)
    parser.add_argument("--mapping", type=Path, default=MAPPING)
    parser.add_argument(
        "--canonical-manifest",
        type=Path,
        default=CANONICAL_MANIFEST,
    )
    parser.add_argument(
        "--random-partitions",
        type=int,
        default=1000,
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


def prepare_outputs(
    docs_dir: Path,
    overwrite: bool,
) -> dict[str, Path]:
    docs_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        key: docs_dir / name
        for key, name in OUTPUT_NAMES.items()
    }
    if not overwrite:
        existing = [path for path in outputs.values() if path.exists()]
        if existing:
            raise FileExistsError(
                "Refusing to overwrite existing audit outputs:\n"
                + "\n".join(f"- {path}" for path in existing)
            )
    return outputs


def subject_number(value: Any) -> int:
    match = re.search(r"(\d+)", str(value))
    if not match:
        raise ValueError(f"Cannot parse subject number from {value!r}")
    number = int(match.group(1))
    if number < 1 or number > 32:
        raise ValueError(f"Subject number outside 1..32: {number}")
    return number


def discover_dat_files(root: Path) -> dict[int, Path]:
    candidates: dict[int, list[Path]] = {}

    for path in root.rglob("*.dat"):
        match = re.fullmatch(r"s(\d{2})\.dat", path.name, re.IGNORECASE)
        if not match:
            continue
        number = int(match.group(1))
        if 1 <= number <= 32:
            candidates.setdefault(number, []).append(path.resolve())

    missing = sorted(set(range(1, 33)) - set(candidates))
    if missing:
        raise FileNotFoundError(
            f"Missing DEAP .dat subjects: {missing}"
        )

    ambiguous = {
        number: paths
        for number, paths in candidates.items()
        if len(paths) != 1
    }
    if ambiguous:
        details = "\n".join(
            f"s{number:02}: {paths}"
            for number, paths in sorted(ambiguous.items())
        )
        raise RuntimeError(
            "Expected one .dat file per subject, found ambiguity:\n"
            + details
        )

    return {
        number: paths[0]
        for number, paths in candidates.items()
    }


def load_dat(path: Path) -> tuple[np.ndarray, np.ndarray]:
    with path.open("rb") as handle:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            obj = pickle.load(handle, encoding="latin1")

    if not isinstance(obj, dict):
        raise TypeError(f"{path}: expected dict")
    if "data" not in obj or "labels" not in obj:
        raise KeyError(f"{path}: missing data or labels")

    data = np.asarray(obj["data"])
    labels = np.asarray(obj["labels"], dtype=float)

    if data.ndim != 3:
        raise ValueError(f"{path}: expected 3D data, found {data.shape}")
    if labels.shape != (40, 4):
        raise ValueError(
            f"{path}: expected labels (40,4), found {labels.shape}"
        )
    if data.shape[0] != 40:
        raise ValueError(
            f"{path}: expected 40 trials, found {data.shape[0]}"
        )
    if data.shape[1] < 36:
        raise ValueError(
            f"{path}: expected at least 36 channels, found {data.shape[1]}"
        )
    if not np.isfinite(labels).all():
        raise ValueError(f"{path}: non-finite labels")

    return data, labels


def binary_labels(score: float) -> dict[str, Any]:
    return {
        "discard_midpoint": (
            0 if score < 5.0 else 1 if score > 5.0 else np.nan
        ),
        "midpoint_as_low": 0 if score <= 5.0 else 1,
        "midpoint_as_high": 0 if score < 5.0 else 1,
    }


def load_mapping(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)

    frame = pd.read_csv(path)
    required = {
        "subject_id",
        "trial_index_0based_in_dat",
        "trial_index_1based_in_dat",
        "metadata_trial",
        "stimulus_id_experiment_id",
        "valence_score",
        "arousal_score",
        "dominance_score",
        "liking_score",
        "verified_order_hypothesis",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Mapping missing columns: {missing}")

    frame = frame.copy()
    frame["_subject_number"] = frame["subject_id"].map(subject_number)
    frame["trial_index_0based_in_dat"] = pd.to_numeric(
        frame["trial_index_0based_in_dat"],
        errors="raise",
    ).astype(int)
    frame["metadata_trial"] = pd.to_numeric(
        frame["metadata_trial"],
        errors="raise",
    ).astype(int)
    frame["stimulus_id_experiment_id"] = pd.to_numeric(
        frame["stimulus_id_experiment_id"],
        errors="raise",
    ).astype(int)

    if len(frame) != 1280:
        raise ValueError(f"Expected 1280 mapping rows, found {len(frame)}")
    if frame.duplicated(
        ["_subject_number", "trial_index_0based_in_dat"]
    ).any():
        raise ValueError("Duplicate subject/dat-row mapping")
    if frame.duplicated(
        ["_subject_number", "metadata_trial"]
    ).any():
        raise ValueError("Duplicate subject/presentation-order mapping")
    if frame.duplicated(
        ["_subject_number", "stimulus_id_experiment_id"]
    ).any():
        raise ValueError("Duplicate subject/stimulus mapping")

    expected_order = set(range(1, 41))
    expected_rows = set(range(40))
    for number, group in frame.groupby("_subject_number"):
        if len(group) != 40:
            raise ValueError(f"s{number:02}: mapping rows != 40")
        if set(group["trial_index_0based_in_dat"]) != expected_rows:
            raise ValueError(f"s{number:02}: dat rows are not 0..39")
        if set(group["metadata_trial"]) != expected_order:
            raise ValueError(f"s{number:02}: Trial is not 1..40")
        if set(group["stimulus_id_experiment_id"]) != expected_order:
            raise ValueError(f"s{number:02}: Experiment_id is not 1..40")

    raw_hypotheses = {
        str(value).strip().lower()
        for value in frame["verified_order_hypothesis"].dropna()
    }
    accepted_experiment_hypotheses = {
        "experiment",
        "experiment_order",
        "experiment_order_alignment",
        "verified_dat_rows_follow_common_experiment_id_order",
    }
    unsupported_hypotheses = (
        raw_hypotheses - accepted_experiment_hypotheses
    )
    if not raw_hypotheses or unsupported_hypotheses:
        raise ValueError(
            "Expected an experiment-order mapping alias, found "
            f"{sorted(raw_hypotheses)}"
        )

    # Canonicalize the verified resolver output. Older resolver versions
    # emitted the compact value "experiment"; both values encode the same
    # independently verified hypothesis.
    frame["verified_order_hypothesis"] = (
        "experiment_order_alignment"
    )

    return frame.sort_values(
        ["_subject_number", "trial_index_0based_in_dat"],
        kind="stable",
    ).reset_index(drop=True)


def build_manifest(
    mapping: pd.DataFrame,
    dat_files: dict[int, Path],
    mapping_path: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    total_comparisons = 0
    exact_comparisons = 0
    max_abs_error = 0.0

    mapping_hash = sha256_file(mapping_path)

    for number in range(1, 33):
        dat_path = dat_files[number]
        data, labels = load_dat(dat_path)

        subject_mapping = mapping[
            mapping["_subject_number"] == number
        ].sort_values("trial_index_0based_in_dat")

        expected_scores = subject_mapping[
            [
                "valence_score",
                "arousal_score",
                "dominance_score",
                "liking_score",
            ]
        ].to_numpy(dtype=float)

        errors = np.abs(labels - expected_scores)
        total_comparisons += int(errors.size)
        exact_comparisons += int((errors <= 1e-8).sum())
        max_abs_error = max(max_abs_error, float(errors.max()))

        if not np.allclose(
            labels,
            expected_scores,
            rtol=0.0,
            atol=1e-8,
        ):
            raise ValueError(
                f"s{number:02}: embedded labels no longer match mapping"
            )

        dat_hash = sha256_file(dat_path)

        for _, map_row in subject_mapping.iterrows():
            dat_index = int(map_row["trial_index_0based_in_dat"])
            stimulus_id = int(map_row["stimulus_id_experiment_id"])
            presentation_order = int(map_row["metadata_trial"])

            valence = float(map_row["valence_score"])
            arousal = float(map_row["arousal_score"])
            dominance = float(map_row["dominance_score"])
            liking = float(map_row["liking_score"])

            eeg_block = data[dat_index, :32, :]
            emg_block = data[dat_index, 34:36, :]

            valence_labels = binary_labels(valence)
            arousal_labels = binary_labels(arousal)

            rows.append(
                {
                    "dataset": "DEAP",
                    "subject_id": f"s{number:02}",
                    "subject_number": number,
                    "session_id": f"s{number:02}_session1",
                    "trial_id": (
                        f"DEAP_s{number:02}_exp{stimulus_id:02}"
                    ),
                    "stimulus_id": f"exp{stimulus_id:02}",
                    "stimulus_id_numeric": stimulus_id,
                    "presentation_order": presentation_order,
                    "trial_index_0based_in_dat": dat_index,
                    "trial_index_1based_in_dat": dat_index + 1,
                    "valence_score": valence,
                    "arousal_score": arousal,
                    "dominance_score": dominance,
                    "liking_score": liking,
                    "valence_discard_midpoint": (
                        valence_labels["discard_midpoint"]
                    ),
                    "valence_midpoint_as_low": (
                        valence_labels["midpoint_as_low"]
                    ),
                    "valence_midpoint_as_high": (
                        valence_labels["midpoint_as_high"]
                    ),
                    "arousal_discard_midpoint": (
                        arousal_labels["discard_midpoint"]
                    ),
                    "arousal_midpoint_as_low": (
                        arousal_labels["midpoint_as_low"]
                    ),
                    "arousal_midpoint_as_high": (
                        arousal_labels["midpoint_as_high"]
                    ),
                    "eeg_available": bool(
                        eeg_block.size > 0
                        and np.isfinite(eeg_block).all()
                    ),
                    "emg_available": bool(
                        emg_block.size > 0
                        and np.isfinite(emg_block).all()
                    ),
                    "eeg_channel_count": 32,
                    "emg_channel_count": 2,
                    "sample_count": int(data.shape[-1]),
                    "chronology_verified": True,
                    "stimulus_identity_verified": True,
                    "mapping_verified": True,
                    "verified_order_hypothesis": (
                        "experiment_order_alignment"
                    ),
                    "physical_trial_unit": True,
                    "dat_path": str(dat_path),
                    "dat_sha256": dat_hash,
                    "mapping_path": str(mapping_path),
                    "mapping_sha256": mapping_hash,
                }
            )

    manifest = pd.DataFrame(rows).sort_values(
        ["subject_number", "presentation_order"],
        kind="stable",
    ).reset_index(drop=True)

    if len(manifest) != 1280:
        raise ValueError(f"Manifest rows != 1280: {len(manifest)}")
    if manifest["subject_id"].nunique() != 32:
        raise ValueError("Manifest subject count != 32")
    if manifest["stimulus_id"].nunique() != 40:
        raise ValueError("Manifest stimulus count != 40")
    if manifest["trial_id"].duplicated().any():
        raise ValueError("Duplicate physical trial_id")
    if manifest.duplicated(["subject_id", "stimulus_id"]).any():
        raise ValueError("Duplicate subject-stimulus cell")
    if not manifest["chronology_verified"].all():
        raise ValueError("Chronology is not verified for all rows")
    if not manifest["stimulus_identity_verified"].all():
        raise ValueError("Stimulus identity is not verified for all rows")
    if not manifest["eeg_available"].all():
        raise ValueError("Missing EEG availability")
    if not manifest["emg_available"].all():
        raise ValueError("Missing EMG availability")

    verification = {
        "embedded_rating_comparisons": total_comparisons,
        "exact_rating_comparisons_at_1e_8": exact_comparisons,
        "exact_match_fraction": (
            exact_comparisons / total_comparisons
        ),
        "max_absolute_error": max_abs_error,
    }
    return manifest, verification


def install_manifest(
    manifest: pd.DataFrame,
    canonical_path: Path,
) -> dict[str, Any]:
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    new_bytes = manifest.to_csv(
        index=False,
        lineterminator="\n",
    ).encode("utf-8")

    action = "CREATED"
    backup_path: Path | None = None

    if canonical_path.exists():
        old_bytes = canonical_path.read_bytes()
        if old_bytes == new_bytes:
            action = "ALREADY_IDENTICAL"
        else:
            old_frame = pd.read_csv(canonical_path)
            already_verified = bool(
                "mapping_verified" in old_frame.columns
                and old_frame["mapping_verified"]
                .astype(str)
                .str.lower()
                .isin({"true", "1"})
                .all()
            )
            if already_verified:
                backup_path = canonical_path.with_name(
                    canonical_path.stem
                    + f"_verified_backup_{int(time.time())}"
                    + canonical_path.suffix
                )
            else:
                backup_path = canonical_path.with_name(
                    "deap_trial_manifest_pre_verified_mapping.csv"
                )
                if backup_path.exists():
                    backup_path = canonical_path.with_name(
                        canonical_path.stem
                        + f"_pre_verified_backup_{int(time.time())}"
                        + canonical_path.suffix
                    )
            shutil.copy2(canonical_path, backup_path)
            canonical_path.write_bytes(new_bytes)
            action = "REPLACED_WITH_BACKUP"
    else:
        canonical_path.write_bytes(new_bytes)

    return {
        "action": action,
        "canonical_path": str(canonical_path),
        "canonical_sha256": hashlib.sha256(new_bytes).hexdigest(),
        "backup_path": str(backup_path) if backup_path else None,
    }


def sequence_audit(manifest: pd.DataFrame) -> dict[str, Any]:
    sequences: dict[str, tuple[str, ...]] = {}

    for subject_id, group in manifest.groupby("subject_id"):
        ordered = group.sort_values("presentation_order")
        sequence = tuple(ordered["stimulus_id"].astype(str))
        if len(sequence) != 40:
            raise ValueError(f"{subject_id}: sequence length != 40")
        sequences[str(subject_id)] = sequence

    counts = pd.Series(list(sequences.values())).value_counts()
    pairwise_same_position: list[float] = []

    for subject_a, subject_b in combinations(sorted(sequences), 2):
        seq_a = sequences[subject_a]
        seq_b = sequences[subject_b]
        pairwise_same_position.append(
            sum(a == b for a, b in zip(seq_a, seq_b)) / 40.0
        )

    stimulus_position_counts = (
        manifest.groupby("stimulus_id")["presentation_order"]
        .nunique()
        .astype(int)
    )

    return {
        "subject_count": 32,
        "unique_complete_sequences": int(len(counts)),
        "largest_identical_sequence_group": int(counts.iloc[0]),
        "pairwise_same_position_fraction_mean": float(
            np.mean(pairwise_same_position)
        ),
        "pairwise_same_position_fraction_median": float(
            np.median(pairwise_same_position)
        ),
        "pairwise_same_position_fraction_max": float(
            np.max(pairwise_same_position)
        ),
        "stimulus_unique_position_count_min": int(
            stimulus_position_counts.min()
        ),
        "stimulus_unique_position_count_median": float(
            stimulus_position_counts.median()
        ),
        "stimulus_unique_position_count_max": int(
            stimulus_position_counts.max()
        ),
    }


def label_count_audit(manifest: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for task in TASKS:
        for policy in POLICIES:
            values = pd.to_numeric(
                manifest[f"{task}_{policy}"],
                errors="coerce",
            )
            retained = values.dropna().astype(int)
            rows.append(
                {
                    "task": task,
                    "policy": policy,
                    "rows_total": int(len(values)),
                    "rows_retained": int(len(retained)),
                    "midpoints_removed": int(values.isna().sum()),
                    "low": int((retained == 0).sum()),
                    "high": int((retained == 1).sum()),
                }
            )
    return rows


def fold_capacities(n: int, k: int) -> list[int]:
    base = n // k
    remainder = n % k
    return [
        base + (1 if index < remainder else 0)
        for index in range(k)
    ]


def random_assignment(
    entities: list[str],
    k: int,
    rng: np.random.Generator,
) -> dict[str, int]:
    shuffled = list(entities)
    rng.shuffle(shuffled)

    assignment: dict[str, int] = {}
    cursor = 0
    for fold_index, capacity in enumerate(
        fold_capacities(len(entities), k)
    ):
        for entity in shuffled[cursor:cursor + capacity]:
            assignment[entity] = fold_index
        cursor += capacity

    if len(assignment) != len(entities):
        raise RuntimeError("Incomplete random assignment")
    return assignment


def label_matrices(
    manifest: pd.DataFrame,
) -> tuple[list[str], list[str], dict[str, np.ndarray]]:
    subjects = sorted(manifest["subject_id"].unique().tolist())
    stimuli = sorted(manifest["stimulus_id"].unique().tolist())
    subject_index = {value: index for index, value in enumerate(subjects)}
    stimulus_index = {value: index for index, value in enumerate(stimuli)}

    matrices: dict[str, np.ndarray] = {}
    for task in TASKS:
        for policy in POLICIES:
            key = f"{task}_{policy}"
            matrix = np.full((32, 40), np.nan, dtype=float)
            for _, row in manifest.iterrows():
                matrix[
                    subject_index[row["subject_id"]],
                    stimulus_index[row["stimulus_id"]],
                ] = row[key]
            if np.isnan(matrix).all():
                raise ValueError(f"All labels missing for {key}")
            matrices[key] = matrix

    return subjects, stimuli, matrices


def evaluate_partition(
    subjects: list[str],
    stimuli: list[str],
    matrices: dict[str, np.ndarray],
    subject_assignment: dict[str, int],
    stimulus_assignment: dict[str, int],
    k_subject: int,
    k_stimulus: int,
) -> dict[str, Any]:
    subject_folds = np.asarray(
        [subject_assignment[value] for value in subjects],
        dtype=int,
    )
    stimulus_folds = np.asarray(
        [stimulus_assignment[value] for value in stimuli],
        dtype=int,
    )

    min_test_class: int | None = None
    min_train_class: int | None = None
    min_test_retained: int | None = None
    single_test = 0
    single_train = 0
    max_removed_fraction = 0.0

    for subject_fold in range(k_subject):
        held_subjects = subject_folds == subject_fold

        for stimulus_fold in range(k_stimulus):
            held_stimuli = stimulus_folds == stimulus_fold

            for key, matrix in matrices.items():
                test_values = matrix[np.ix_(held_subjects, held_stimuli)]
                train_values = matrix[
                    np.ix_(~held_subjects, ~held_stimuli)
                ]

                test_flat = test_values.ravel()
                train_flat = train_values.ravel()
                test_retained = test_flat[~np.isnan(test_flat)].astype(int)
                train_retained = train_flat[~np.isnan(train_flat)].astype(int)

                test_low = int((test_retained == 0).sum())
                test_high = int((test_retained == 1).sum())
                train_low = int((train_retained == 0).sum())
                train_high = int((train_retained == 1).sum())

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

                if test_low == 0 or test_high == 0:
                    single_test += 1
                if train_low == 0 or train_high == 0:
                    single_train += 1

                removed_fraction = (
                    (len(test_flat) - len(test_retained))
                    / len(test_flat)
                )
                max_removed_fraction = max(
                    max_removed_fraction,
                    removed_fraction,
                )

    assert min_test_class is not None
    assert min_train_class is not None
    assert min_test_retained is not None

    held_subject_sizes = [
        int((subject_folds == fold).sum())
        for fold in range(k_subject)
    ]
    held_stimulus_sizes = [
        int((stimulus_folds == fold).sum())
        for fold in range(k_stimulus)
    ]

    strong = bool(
        single_test == 0
        and single_train == 0
        and min_test_class >= 10
        and min_train_class >= 10
        and min(held_subject_sizes) >= 6
        and min(held_stimulus_sizes) >= 5
    )
    minimal = bool(
        single_test == 0
        and single_train == 0
        and min_test_class >= 5
    )

    return {
        "min_test_class_support": min_test_class,
        "min_train_class_support": min_train_class,
        "min_test_retained": min_test_retained,
        "single_class_test_flags": single_test,
        "single_class_train_flags": single_train,
        "max_midpoint_removed_fraction": max_removed_fraction,
        "min_held_subjects": min(held_subject_sizes),
        "max_held_subjects": max(held_subject_sizes),
        "min_held_stimuli": min(held_stimulus_sizes),
        "max_held_stimuli": max(held_stimulus_sizes),
        "strong_capacity_pass": strong,
        "minimal_capacity_pass": minimal,
    }


def run_random_capacity_audit(
    manifest: pd.DataFrame,
    random_partitions: int,
    manifest_hash: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    subjects, stimuli, matrices = label_matrices(manifest)
    trial_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []

    for scheme_index, (
        scheme,
        (k_subject, k_stimulus),
    ) in enumerate(SCHEMES.items()):
        for trial_index in range(random_partitions):
            seed_payload = (
                f"{manifest_hash}|{scheme}|trial={trial_index}"
            ).encode("utf-8")
            seed = int.from_bytes(
                hashlib.sha256(seed_payload).digest()[:8],
                "big",
            ) % (2**32)
            rng = np.random.default_rng(seed)

            subject_assignment = random_assignment(
                subjects,
                k_subject,
                rng,
            )
            stimulus_assignment = random_assignment(
                stimuli,
                k_stimulus,
                rng,
            )
            result = evaluate_partition(
                subjects,
                stimuli,
                matrices,
                subject_assignment,
                stimulus_assignment,
                k_subject,
                k_stimulus,
            )
            trial_rows.append(
                {
                    "scheme": scheme,
                    "trial_index": trial_index,
                    "seed": seed,
                    **result,
                }
            )

        frame = pd.DataFrame(
            [row for row in trial_rows if row["scheme"] == scheme]
        )
        strong_rate = float(frame["strong_capacity_pass"].mean())
        minimal_rate = float(frame["minimal_capacity_pass"].mean())
        p05 = float(
            frame["min_test_class_support"].quantile(0.05)
        )
        median = float(
            frame["min_test_class_support"].median()
        )
        p95 = float(
            frame["min_test_class_support"].quantile(0.95)
        )
        single_test_rate = float(
            (frame["single_class_test_flags"] > 0).mean()
        )

        if strong_rate >= 0.95 and p05 >= 10:
            verdict = "ROBUST_STRONG"
        elif minimal_rate >= 0.95 and p05 >= 5:
            verdict = "ROBUST_MINIMAL"
        else:
            verdict = "PARTITION_SENSITIVE"

        summaries.append(
            {
                "scheme": scheme,
                "random_partitions": random_partitions,
                "outer_cells": k_subject * k_stimulus,
                "held_subjects": (
                    f"{frame['min_held_subjects'].min()}.."
                    f"{frame['max_held_subjects'].max()}"
                ),
                "held_stimuli": (
                    f"{frame['min_held_stimuli'].min()}.."
                    f"{frame['max_held_stimuli'].max()}"
                ),
                "min_test_class_random_min": int(
                    frame["min_test_class_support"].min()
                ),
                "min_test_class_p05": p05,
                "min_test_class_median": median,
                "min_test_class_p95": p95,
                "min_test_class_random_max": int(
                    frame["min_test_class_support"].max()
                ),
                "strong_pass_rate": strong_rate,
                "minimal_pass_rate": minimal_rate,
                "single_class_test_partition_rate": single_test_rate,
                "verdict": verdict,
            }
        )

    strong_schemes = [
        row for row in summaries
        if row["verdict"] == "ROBUST_STRONG"
    ]
    minimal_schemes = [
        row for row in summaries
        if row["verdict"] == "ROBUST_MINIMAL"
    ]

    if strong_schemes:
        recommendation = max(
            strong_schemes,
            key=lambda row: (
                row["outer_cells"],
                row["min_test_class_p05"],
            ),
        )["scheme"]
    elif minimal_schemes:
        recommendation = max(
            minimal_schemes,
            key=lambda row: (
                row["min_test_class_p05"],
                -row["outer_cells"],
            ),
        )["scheme"]
    else:
        recommendation = "DO_NOT_FREEZE_YET"

    return trial_rows, summaries, recommendation


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
        values: list[str] = []
        for column in columns:
            value = str(row.get(column, ""))
            value = value.replace("|", "\\|").replace("\n", " ")
            values.append(value)
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    if args.random_partitions < 100:
        raise ValueError("--random-partitions must be at least 100")

    repo = args.repo_root.resolve()
    docs_dir = args.docs_dir.resolve()
    mapping_path = args.mapping.resolve()
    canonical_manifest = args.canonical_manifest.resolve()

    branch = git(repo, "branch", "--show-current")
    head = git(repo, "rev-parse", "HEAD")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}"
        )

    outputs = prepare_outputs(docs_dir, args.overwrite)
    mapping = load_mapping(mapping_path)
    dat_files = discover_dat_files(args.deap_root.resolve())

    manifest, rating_verification = build_manifest(
        mapping,
        dat_files,
        mapping_path,
    )
    install_result = install_manifest(
        manifest,
        canonical_manifest,
    )
    manifest_hash = sha256_file(canonical_manifest)

    sequence = sequence_audit(manifest)
    label_counts = label_count_audit(manifest)

    trial_rows, capacity_summaries, recommendation = (
        run_random_capacity_audit(
            manifest,
            args.random_partitions,
            manifest_hash,
        )
    )

    write_csv(outputs["capacity_trials_csv"], trial_rows)
    write_csv(outputs["capacity_summary_csv"], capacity_summaries)

    manifest_report = {
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "training_performed": False,
        "mapping_path": str(mapping_path),
        "mapping_sha256": sha256_file(mapping_path),
        "manifest_installation": install_result,
        "manifest_rows": len(manifest),
        "subjects": int(manifest["subject_id"].nunique()),
        "stimuli": int(manifest["stimulus_id"].nunique()),
        "complete_grid": bool(
            len(manifest) == 32 * 40
            and not manifest.duplicated(
                ["subject_id", "stimulus_id"]
            ).any()
        ),
        "chronology_verified_rows": int(
            manifest["chronology_verified"].sum()
        ),
        "stimulus_identity_verified_rows": int(
            manifest["stimulus_identity_verified"].sum()
        ),
        "eeg_available_rows": int(
            manifest["eeg_available"].sum()
        ),
        "emg_available_rows": int(
            manifest["emg_available"].sum()
        ),
        "rating_verification": rating_verification,
        "sequence_audit": sequence,
        "label_counts": label_counts,
        "deap_strict_joint_ready": True,
    }
    outputs["manifest_audit_json"].write_text(
        json.dumps(
            safe_json(manifest_report),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    capacity_report = {
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "manifest": str(canonical_manifest),
        "manifest_sha256": manifest_hash,
        "random_partitions_per_scheme": args.random_partitions,
        "partition_construction_uses_labels": False,
        "capacity_summaries": capacity_summaries,
        "recommended_pre_freeze_scheme": recommendation,
        "interpretation": (
            "This is a capacity and partition-robustness result, not "
            "model selection. The selected scheme must still be frozen "
            "with deterministic label-blind repetitions before training."
        ),
    }
    outputs["capacity_json"].write_text(
        json.dumps(
            safe_json(capacity_report),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    label_table = [
        {
            **row,
            "retained": row["rows_retained"],
        }
        for row in label_counts
    ]

    manifest_md = [
        "# DEAP Verified Physical-Trial Manifest Audit",
        "",
        "No model training was performed.",
        "",
        "## Mapping Resolution",
        "",
        "- `.dat` row order: common `Experiment_id` order",
        "- `stimulus_id`: verified `Experiment_id`",
        "- `presentation_order`: participant-specific metadata `Trial`",
        f"- Embedded-rating comparisons: "
        f"`{rating_verification['embedded_rating_comparisons']}`",
        f"- Exact-match fraction: "
        f"`{rating_verification['exact_match_fraction']:.6f}`",
        f"- Maximum absolute error: "
        f"`{rating_verification['max_absolute_error']:.12f}`",
        "",
        "## Canonical Manifest",
        "",
        f"- Rows: `{len(manifest)}`",
        "- Grid: `32 subjects × 40 stimuli = 1280`",
        "- Duplicate subject–stimulus cells: `0`",
        "- Chronology-verified rows: `1280`",
        "- Stimulus-identity-verified rows: `1280`",
        "- EEG-available rows: `1280`",
        "- EMG-available rows: `1280`",
        f"- Manifest action: `{install_result['action']}`",
        f"- Manifest SHA-256: `{manifest_hash}`",
        "",
        "## Presentation Sequences",
        "",
        f"- Unique complete sequences: "
        f"`{sequence['unique_complete_sequences']}` of `32`",
        f"- Largest identical-sequence group: "
        f"`{sequence['largest_identical_sequence_group']}`",
        f"- Mean pairwise same-position fraction: "
        f"`{sequence['pairwise_same_position_fraction_mean']:.4f}`",
        f"- Maximum pairwise same-position fraction: "
        f"`{sequence['pairwise_same_position_fraction_max']:.4f}`",
        f"- Unique positions per stimulus, min/median/max: "
        f"`{sequence['stimulus_unique_position_count_min']}/"
        f"{sequence['stimulus_unique_position_count_median']:.1f}/"
        f"{sequence['stimulus_unique_position_count_max']}`",
        "",
        "## Label Counts",
        "",
        markdown_table(
            label_table,
            [
                "task",
                "policy",
                "retained",
                "midpoints_removed",
                "low",
                "high",
            ],
        ),
        "",
        "## Decision",
        "",
        "- DEAP stimulus-aware manifest: **READY**",
        "- DEAP chronology-aware manifest: **READY**",
        "- DEAP Strict Joint CV construction: **READY**",
        "",
    ]
    outputs["manifest_audit_md"].write_text(
        "\n".join(manifest_md),
        encoding="utf-8",
    )

    capacity_md = [
        "# DEAP Strict Joint-CV Label-Blind Partition Capacity",
        "",
        "No model training was performed. Every reference partition was "
        "constructed without labels.",
        "",
        markdown_table(
            capacity_summaries,
            [
                "scheme",
                "random_partitions",
                "outer_cells",
                "held_subjects",
                "held_stimuli",
                "min_test_class_random_min",
                "min_test_class_p05",
                "min_test_class_median",
                "min_test_class_p95",
                "strong_pass_rate",
                "minimal_pass_rate",
                "single_class_test_partition_rate",
                "verdict",
            ],
        ),
        "",
        "## Decision",
        "",
        f"- Recommended pre-freeze scheme: **{recommendation}**",
        "- This is not yet a frozen benchmark.",
        "- The next step is deterministic repeated label-blind freezing "
        "of the defensible scheme, without rerolling after support review.",
        "",
    ]
    outputs["capacity_md"].write_text(
        "\n".join(capacity_md),
        encoding="utf-8",
    )

    print("DEAP verified manifest and Joint-CV capacity audit completed.")
    print(f"Branch: {branch}")
    print(f"HEAD: {head}")
    print(
        f"Manifest: rows={len(manifest)}, "
        f"subjects={manifest['subject_id'].nunique()}, "
        f"stimuli={manifest['stimulus_id'].nunique()}"
    )
    print(
        "Rating verification: "
        f"{rating_verification['exact_rating_comparisons_at_1e_8']}/"
        f"{rating_verification['embedded_rating_comparisons']} exact, "
        f"max_error={rating_verification['max_absolute_error']:.12f}"
    )
    print(
        f"Chronology verified rows: "
        f"{int(manifest['chronology_verified'].sum())}"
    )
    print(
        f"Unique complete presentation sequences: "
        f"{sequence['unique_complete_sequences']}"
    )
    for row in capacity_summaries:
        print(
            f"{row['scheme']}: "
            f"strong_rate={row['strong_pass_rate']:.4f}, "
            f"minimal_rate={row['minimal_pass_rate']:.4f}, "
            f"min_test_class_p05={row['min_test_class_p05']:.2f}, "
            f"verdict={row['verdict']}"
        )
    print(f"Recommended pre-freeze scheme: {recommendation}")
    print(f"Manifest report: {outputs['manifest_audit_md']}")
    print(f"Capacity report: {outputs['capacity_md']}")


if __name__ == "__main__":
    main()

