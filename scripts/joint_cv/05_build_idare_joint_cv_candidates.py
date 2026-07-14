#!/usr/bin/env python3
"""Build and audit candidate Strict Joint Subject–Stimulus CV schemes for I-DARE.

The script operates only on the canonical physical-trial manifest and creates
candidate fold assignments plus exhaustive outer-cell support diagnostics.

Primary protocol for every outer cell
-------------------------------------
Train:
    source subjects × source stimuli

Primary test:
    held-out subjects × held-out stimuli

Diagnostic regions:
    source subjects × held-out stimuli
    held-out subjects × source stimuli

All subject-fold × stimulus-fold combinations are evaluated. Diagonal-only
pairing is explicitly forbidden.

No model training is performed. Fold construction uses only identity and label
support profiles, never model outputs, predictions, or target EEG/EMG features.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    normalized_mutual_info_score,
)


REPO = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE")
MANIFEST = REPO / "docs" / "joint_cv" / "idare_trial_manifest.csv"
OUT_DOCS = REPO / "docs" / "joint_cv"
OUT_FOLDS = REPO / "folds"
EXPECTED_BRANCH = "joint-cv-capacity-audit"

SCHEMES = {
    "idare_4x4": (4, 4),
    "idare_5x5": (5, 5),
}

TASKS = ("valence", "arousal")
POLICIES = (
    "discard_midpoint",
    "midpoint_as_low",
    "midpoint_as_high",
)

OUTPUTS = {
    "candidates_json": "idare_joint_cv_candidates.json",
    "assignments_csv": "idare_joint_cv_fold_assignments.csv",
    "cell_support_csv": "idare_joint_cv_cell_support.csv",
    "feasibility_md": "idare_joint_cv_feasibility.md",
    "feasibility_json": "idare_joint_cv_feasibility.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--docs-dir", type=Path, default=OUT_DOCS)
    parser.add_argument("--folds-dir", type=Path, default=OUT_FOLDS)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite only this script's own existing output files.",
    )
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

    paths = {
        "candidates_json": folds_dir / OUTPUTS["candidates_json"],
        "assignments_csv": docs_dir / OUTPUTS["assignments_csv"],
        "cell_support_csv": docs_dir / OUTPUTS["cell_support_csv"],
        "feasibility_md": docs_dir / OUTPUTS["feasibility_md"],
        "feasibility_json": docs_dir / OUTPUTS["feasibility_json"],
    }

    for scheme_name in SCHEMES:
        paths[f"{scheme_name}_subject_csv"] = (
            folds_dir / f"{scheme_name}_subject_folds.csv"
        )
        paths[f"{scheme_name}_stimulus_csv"] = (
            folds_dir / f"{scheme_name}_stimulus_folds.csv"
        )

    if not overwrite:
        existing = [path for path in paths.values() if path.exists()]
        if existing:
            raise FileExistsError(
                "Refusing to overwrite existing outputs. "
                "Use --overwrite only after reviewing them:\n"
                + "\n".join(f"- {path}" for path in existing)
            )

    return paths


def load_and_validate_manifest(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path)

    required = {
        "dataset",
        "subject_id",
        "session_id",
        "trial_id",
        "stimulus_id",
        "presentation_order",
        "valence_score",
        "arousal_score",
        "valence_discard_midpoint",
        "valence_midpoint_as_low",
        "valence_midpoint_as_high",
        "arousal_discard_midpoint",
        "arousal_midpoint_as_low",
        "arousal_midpoint_as_high",
        "eeg_available",
        "emg_available",
        "chronology_verified",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Manifest missing required columns: {missing}")

    if len(df) != 2016:
        raise ValueError(f"Expected 2016 physical trials, found {len(df)}")

    df = df.copy()
    df["subject_id"] = df["subject_id"].astype(str)
    df["stimulus_id"] = df["stimulus_id"].astype(str)
    df["presentation_order"] = pd.to_numeric(
        df["presentation_order"],
        errors="raise",
    ).astype(int)

    if df["subject_id"].nunique() != 63:
        raise ValueError(
            f"Expected 63 subjects, found {df['subject_id'].nunique()}"
        )
    if df["stimulus_id"].nunique() != 32:
        raise ValueError(
            f"Expected 32 stimuli, found {df['stimulus_id'].nunique()}"
        )
    if df.duplicated(["subject_id", "stimulus_id"]).any():
        raise ValueError("Duplicate subject–stimulus physical cells found")

    expected_trials = 63 * 32
    if len(df) != expected_trials:
        raise ValueError(
            f"Manifest is not a complete 63×32 grid: {len(df)} rows"
        )

    subject_counts = df.groupby("subject_id").size()
    stimulus_counts = df.groupby("stimulus_id").size()
    if not (subject_counts == 32).all():
        raise ValueError("Not every subject has exactly 32 trials")
    if not (stimulus_counts == 63).all():
        raise ValueError("Not every stimulus appears for exactly 63 subjects")

    if not df["chronology_verified"].astype(bool).all():
        raise ValueError("I-DARE chronology is not verified for every row")

    return df.sort_values(
        ["subject_id", "presentation_order", "stimulus_id"],
        kind="stable",
    ).reset_index(drop=True)


def score_category(series: pd.Series) -> np.ndarray:
    values = pd.to_numeric(series, errors="raise").to_numpy(dtype=float)
    return np.where(values < 5.0, 0, np.where(values > 5.0, 2, 1))


def build_entity_profiles(
    df: pd.DataFrame,
    entity_column: str,
) -> tuple[list[str], np.ndarray, list[str]]:
    work = df.copy()
    work["_valence_category"] = score_category(work["valence_score"])
    work["_arousal_category"] = score_category(work["arousal_score"])

    entities = sorted(work[entity_column].astype(str).unique().tolist())
    feature_names = [
        "n_trials",
        "valence_low",
        "valence_mid",
        "valence_high",
        "arousal_low",
        "arousal_mid",
        "arousal_high",
        "valence_score_sum",
        "arousal_score_sum",
    ]

    matrix: list[list[float]] = []
    for entity in entities:
        group = work[work[entity_column].astype(str) == entity]
        valence_cat = group["_valence_category"].to_numpy()
        arousal_cat = group["_arousal_category"].to_numpy()

        matrix.append(
            [
                float(len(group)),
                float((valence_cat == 0).sum()),
                float((valence_cat == 1).sum()),
                float((valence_cat == 2).sum()),
                float((arousal_cat == 0).sum()),
                float((arousal_cat == 1).sum()),
                float((arousal_cat == 2).sum()),
                float(group["valence_score"].sum()),
                float(group["arousal_score"].sum()),
            ]
        )

    return entities, np.asarray(matrix, dtype=float), feature_names


def fold_capacities(n_entities: int, k: int) -> list[int]:
    base = n_entities // k
    remainder = n_entities % k
    return [base + (1 if fold < remainder else 0) for fold in range(k)]


def stable_tie_key(entity: str, scheme: str, axis: str) -> str:
    payload = f"{scheme}|{axis}|{entity}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def assignment_objective(
    fold_members: list[list[int]],
    features: np.ndarray,
    capacities: list[int],
) -> float:
    total = features.sum(axis=0)
    scales = np.where(np.abs(total) > 1e-12, np.abs(total), 1.0)

    objective = 0.0
    n_entities = len(features)

    for fold_index, members in enumerate(fold_members):
        fold_sum = (
            features[members].sum(axis=0)
            if members
            else np.zeros(features.shape[1], dtype=float)
        )
        target = total * (capacities[fold_index] / n_entities)
        deviation = (fold_sum - target) / scales
        objective += float(np.dot(deviation, deviation))

    return objective


def balanced_partition(
    entities: list[str],
    features: np.ndarray,
    k: int,
    scheme: str,
    axis: str,
) -> tuple[dict[str, int], dict[str, Any]]:
    capacities = fold_capacities(len(entities), k)

    total = features.sum(axis=0)
    scales = np.where(np.abs(total) > 1e-12, np.abs(total), 1.0)
    normalized = features / scales

    rarity = np.linalg.norm(
        normalized - normalized.mean(axis=0, keepdims=True),
        axis=1,
    )
    order = sorted(
        range(len(entities)),
        key=lambda index: (
            -float(rarity[index]),
            stable_tie_key(entities[index], scheme, axis),
            entities[index],
        ),
    )

    fold_members: list[list[int]] = [[] for _ in range(k)]

    for entity_index in order:
        candidate_folds = [
            fold
            for fold in range(k)
            if len(fold_members[fold]) < capacities[fold]
        ]

        best_fold = None
        best_score = None
        for fold in candidate_folds:
            fold_members[fold].append(entity_index)
            score = assignment_objective(
                fold_members,
                features,
                capacities,
            )
            fold_members[fold].pop()

            key = (score, len(fold_members[fold]), fold)
            if best_score is None or key < best_score:
                best_score = key
                best_fold = fold

        assert best_fold is not None
        fold_members[best_fold].append(entity_index)

    # Deterministic pairwise-swap refinement while preserving exact sizes.
    improved = True
    refinement_passes = 0
    current_objective = assignment_objective(
        fold_members,
        features,
        capacities,
    )

    while improved and refinement_passes < 50:
        improved = False
        refinement_passes += 1

        for fold_a in range(k):
            for fold_b in range(fold_a + 1, k):
                members_a = sorted(
                    fold_members[fold_a],
                    key=lambda i: entities[i],
                )
                members_b = sorted(
                    fold_members[fold_b],
                    key=lambda i: entities[i],
                )

                accepted = False
                for entity_a in members_a:
                    for entity_b in members_b:
                        index_a = fold_members[fold_a].index(entity_a)
                        index_b = fold_members[fold_b].index(entity_b)

                        fold_members[fold_a][index_a] = entity_b
                        fold_members[fold_b][index_b] = entity_a

                        new_objective = assignment_objective(
                            fold_members,
                            features,
                            capacities,
                        )

                        if new_objective + 1e-15 < current_objective:
                            current_objective = new_objective
                            improved = True
                            accepted = True
                            break

                        fold_members[fold_a][index_a] = entity_a
                        fold_members[fold_b][index_b] = entity_b

                    if accepted:
                        break

                if accepted:
                    break
            if improved:
                break

    assignment: dict[str, int] = {}
    for fold_index, members in enumerate(fold_members):
        for entity_index in members:
            assignment[entities[entity_index]] = fold_index

    metadata = {
        "k": k,
        "capacities": capacities,
        "objective": current_objective,
        "refinement_passes": refinement_passes,
        "construction": (
            "deterministic greedy label-support balancing plus "
            "pairwise-swap refinement; no model outputs used"
        ),
    }
    return assignment, metadata


def mask_for_policy(
    frame: pd.DataFrame,
    task: str,
    policy: str,
) -> tuple[np.ndarray, np.ndarray]:
    column = f"{task}_{policy}"
    values = pd.to_numeric(frame[column], errors="coerce")
    retained = values.notna().to_numpy()
    labels = values.fillna(-1).astype(int).to_numpy()
    return retained, labels


def class_counts(labels: np.ndarray) -> tuple[int, int]:
    return int((labels == 0).sum()), int((labels == 1).sum())


def constant_prediction_metrics(
    y_true: np.ndarray,
    predicted_class: int,
) -> dict[str, Any]:
    if len(y_true) == 0:
        return {
            "accuracy": None,
            "balanced_accuracy": None,
            "macro_f1": None,
        }

    y_pred = np.full(len(y_true), predicted_class, dtype=int)
    both_classes = len(np.unique(y_true)) == 2

    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": (
            float(balanced_accuracy_score(y_true, y_pred))
            if both_classes
            else None
        ),
        "macro_f1": float(
            f1_score(
                y_true,
                y_pred,
                average="macro",
                labels=[0, 1],
                zero_division=0,
            )
        ),
    }


def categorical_nmi(
    identities: pd.Series,
    labels: np.ndarray,
) -> float | None:
    if len(labels) == 0 or len(np.unique(labels)) < 2:
        return None
    return float(
        normalized_mutual_info_score(
            identities.astype(str).to_numpy(),
            labels,
        )
    )


def sequence_js_divergence(
    region: pd.DataFrame,
    global_distribution: np.ndarray,
) -> float | None:
    if len(region) == 0:
        return None

    counts = (
        region["presentation_order"]
        .value_counts()
        .reindex(range(1, 33), fill_value=0)
        .to_numpy(dtype=float)
    )
    if counts.sum() == 0:
        return None

    local = counts / counts.sum()
    return float(jensenshannon(local, global_distribution, base=2.0) ** 2)


def majority_class_from_train(y_train: np.ndarray) -> int | None:
    if len(y_train) == 0:
        return None
    low, high = class_counts(y_train)
    # Deterministic tie rule: class 0.
    return 1 if high > low else 0


def evaluate_cell_policy(
    frame: pd.DataFrame,
    masks: dict[str, np.ndarray],
    task: str,
    policy: str,
    global_order_distribution: np.ndarray,
) -> dict[str, Any]:
    retained, all_labels = mask_for_policy(frame, task, policy)

    region_data: dict[str, dict[str, Any]] = {}
    for region_name, region_mask in masks.items():
        mask = region_mask & retained
        labels = all_labels[mask]
        region_frame = frame.loc[mask]
        low, high = class_counts(labels)
        valid_modality = (
            region_frame["eeg_available"].astype(bool).to_numpy()
            & region_frame["emg_available"].astype(bool).to_numpy()
        )
        labels_after_qc = labels[valid_modality]
        qc_low, qc_high = class_counts(labels_after_qc)

        region_data[region_name] = {
            "rows_total_before_policy": int(region_mask.sum()),
            "rows_retained": int(mask.sum()),
            "rows_removed_midpoint": int(
                region_mask.sum() - mask.sum()
            ),
            "low_count": low,
            "high_count": high,
            "single_class": bool(
                len(labels) > 0 and len(np.unique(labels)) < 2
            ),
            "rows_after_eeg_emg_availability": int(
                valid_modality.sum()
            ),
            "low_after_eeg_emg_availability": qc_low,
            "high_after_eeg_emg_availability": qc_high,
            "stimulus_label_nmi": categorical_nmi(
                region_frame["stimulus_id"],
                labels,
            ),
            "subject_label_nmi": categorical_nmi(
                region_frame["subject_id"],
                labels,
            ),
            "presentation_order_js_divergence": (
                sequence_js_divergence(
                    region_frame,
                    global_order_distribution,
                )
            ),
        }

    train_labels = all_labels[masks["train"] & retained]
    test_labels = all_labels[masks["unseen_subject_unseen_stimulus"] & retained]

    train_majority = majority_class_from_train(train_labels)
    if train_majority is None:
        legal_metrics = {
            "accuracy": None,
            "balanced_accuracy": None,
            "macro_f1": None,
        }
    else:
        legal_metrics = constant_prediction_metrics(
            test_labels,
            train_majority,
        )

    test_low, test_high = class_counts(test_labels)
    test_oracle_majority = 1 if test_high > test_low else 0
    oracle_metrics = constant_prediction_metrics(
        test_labels,
        test_oracle_majority,
    )

    return {
        "regions": region_data,
        "train_majority_class": train_majority,
        "train_majority_test_accuracy": legal_metrics["accuracy"],
        "train_majority_test_balanced_accuracy": (
            legal_metrics["balanced_accuracy"]
        ),
        "train_majority_test_macro_f1": legal_metrics["macro_f1"],
        "oracle_test_majority_class_diagnostic_only": (
            test_oracle_majority
        ),
        "oracle_test_majority_accuracy_diagnostic_only": (
            oracle_metrics["accuracy"]
        ),
        "theoretical_balanced_accuracy_chance": (
            0.5 if len(np.unique(test_labels)) == 2 else None
        ),
    }


def build_outer_cells(
    frame: pd.DataFrame,
    scheme_name: str,
    subject_assignment: dict[str, int],
    stimulus_assignment: dict[str, int],
    k_subject: int,
    k_stimulus: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    subject_series = frame["subject_id"].astype(str)
    stimulus_series = frame["stimulus_id"].astype(str)

    global_order_counts = (
        frame["presentation_order"]
        .value_counts()
        .reindex(range(1, 33), fill_value=0)
        .to_numpy(dtype=float)
    )
    global_order_distribution = (
        global_order_counts / global_order_counts.sum()
    )

    nested_rows: list[dict[str, Any]] = []
    flat_rows: list[dict[str, Any]] = []

    for subject_fold in range(k_subject):
        held_subjects = sorted(
            entity
            for entity, fold in subject_assignment.items()
            if fold == subject_fold
        )
        source_subjects = sorted(
            entity
            for entity, fold in subject_assignment.items()
            if fold != subject_fold
        )

        held_subject_mask = subject_series.isin(held_subjects).to_numpy()
        source_subject_mask = ~held_subject_mask

        for stimulus_fold in range(k_stimulus):
            held_stimuli = sorted(
                entity
                for entity, fold in stimulus_assignment.items()
                if fold == stimulus_fold
            )
            source_stimuli = sorted(
                entity
                for entity, fold in stimulus_assignment.items()
                if fold != stimulus_fold
            )

            held_stimulus_mask = stimulus_series.isin(
                held_stimuli
            ).to_numpy()
            source_stimulus_mask = ~held_stimulus_mask

            masks = {
                "train": source_subject_mask & source_stimulus_mask,
                "seen_subject_unseen_stimulus": (
                    source_subject_mask & held_stimulus_mask
                ),
                "unseen_subject_seen_stimulus": (
                    held_subject_mask & source_stimulus_mask
                ),
                "unseen_subject_unseen_stimulus": (
                    held_subject_mask & held_stimulus_mask
                ),
            }

            cell_id = (
                f"{scheme_name}_S{subject_fold + 1:02d}_"
                f"T{stimulus_fold + 1:02d}"
            )

            subject_leakage = bool(
                set(held_subjects).intersection(source_subjects)
            )
            stimulus_leakage = bool(
                set(held_stimuli).intersection(source_stimuli)
            )

            cell_record = {
                "scheme": scheme_name,
                "cell_id": cell_id,
                "subject_fold_index_0based": subject_fold,
                "stimulus_fold_index_0based": stimulus_fold,
                "held_subjects": held_subjects,
                "source_subjects": source_subjects,
                "held_stimuli": held_stimuli,
                "source_stimuli": source_stimuli,
                "n_held_subjects": len(held_subjects),
                "n_source_subjects": len(source_subjects),
                "n_held_stimuli": len(held_stimuli),
                "n_source_stimuli": len(source_stimuli),
                "subject_leakage": subject_leakage,
                "stimulus_leakage": stimulus_leakage,
                "region_rows": {
                    name: int(mask.sum())
                    for name, mask in masks.items()
                },
                "task_policy_support": {},
            }

            for task in TASKS:
                cell_record["task_policy_support"][task] = {}
                for policy in POLICIES:
                    evaluation = evaluate_cell_policy(
                        frame,
                        masks,
                        task,
                        policy,
                        global_order_distribution,
                    )
                    cell_record["task_policy_support"][task][
                        policy
                    ] = evaluation

                    train = evaluation["regions"]["train"]
                    test = evaluation["regions"][
                        "unseen_subject_unseen_stimulus"
                    ]
                    seen_unseen = evaluation["regions"][
                        "seen_subject_unseen_stimulus"
                    ]
                    unseen_seen = evaluation["regions"][
                        "unseen_subject_seen_stimulus"
                    ]

                    flat_rows.append(
                        {
                            "scheme": scheme_name,
                            "cell_id": cell_id,
                            "subject_fold": subject_fold + 1,
                            "stimulus_fold": stimulus_fold + 1,
                            "task": task,
                            "label_policy": policy,
                            "held_subject_count": len(held_subjects),
                            "held_stimulus_count": len(held_stimuli),
                            "source_subject_count": len(source_subjects),
                            "source_stimulus_count": len(source_stimuli),
                            "train_physical_trials_before_policy": (
                                train["rows_total_before_policy"]
                            ),
                            "test_physical_trials_before_policy": (
                                test["rows_total_before_policy"]
                            ),
                            "train_retained": train["rows_retained"],
                            "test_retained": test["rows_retained"],
                            "test_midpoints_removed": (
                                test["rows_removed_midpoint"]
                            ),
                            "test_midpoint_removed_fraction": (
                                test["rows_removed_midpoint"]
                                / test["rows_total_before_policy"]
                                if test["rows_total_before_policy"]
                                else None
                            ),
                            "train_low": train["low_count"],
                            "train_high": train["high_count"],
                            "test_low": test["low_count"],
                            "test_high": test["high_count"],
                            "train_single_class": train[
                                "single_class"
                            ],
                            "test_single_class": test[
                                "single_class"
                            ],
                            "test_rows_after_eeg_emg_availability": (
                                test[
                                    "rows_after_eeg_emg_availability"
                                ]
                            ),
                            "test_low_after_eeg_emg_availability": (
                                test[
                                    "low_after_eeg_emg_availability"
                                ]
                            ),
                            "test_high_after_eeg_emg_availability": (
                                test[
                                    "high_after_eeg_emg_availability"
                                ]
                            ),
                            "seen_subject_unseen_stimulus_retained": (
                                seen_unseen["rows_retained"]
                            ),
                            "seen_subject_unseen_stimulus_low": (
                                seen_unseen["low_count"]
                            ),
                            "seen_subject_unseen_stimulus_high": (
                                seen_unseen["high_count"]
                            ),
                            "unseen_subject_seen_stimulus_retained": (
                                unseen_seen["rows_retained"]
                            ),
                            "unseen_subject_seen_stimulus_low": (
                                unseen_seen["low_count"]
                            ),
                            "unseen_subject_seen_stimulus_high": (
                                unseen_seen["high_count"]
                            ),
                            "train_majority_class": evaluation[
                                "train_majority_class"
                            ],
                            "train_majority_test_accuracy": evaluation[
                                "train_majority_test_accuracy"
                            ],
                            "train_majority_test_balanced_accuracy": (
                                evaluation[
                                    "train_majority_test_balanced_accuracy"
                                ]
                            ),
                            "train_majority_test_macro_f1": evaluation[
                                "train_majority_test_macro_f1"
                            ],
                            "oracle_test_majority_accuracy_"
                            "diagnostic_only": evaluation[
                                "oracle_test_majority_accuracy_"
                                "diagnostic_only"
                            ],
                            "theoretical_balanced_accuracy_chance": (
                                evaluation[
                                    "theoretical_balanced_accuracy_chance"
                                ]
                            ),
                            "train_stimulus_label_nmi": train[
                                "stimulus_label_nmi"
                            ],
                            "test_stimulus_label_nmi": test[
                                "stimulus_label_nmi"
                            ],
                            "train_subject_label_nmi": train[
                                "subject_label_nmi"
                            ],
                            "test_subject_label_nmi": test[
                                "subject_label_nmi"
                            ],
                            "test_presentation_order_js_divergence": (
                                test[
                                    "presentation_order_js_divergence"
                                ]
                            ),
                            "subject_leakage": subject_leakage,
                            "stimulus_leakage": stimulus_leakage,
                            "test_independent_subjects": (
                                len(held_subjects)
                            ),
                            "test_independent_stimuli": (
                                len(held_stimuli)
                            ),
                            "test_min_axis_units_capacity_proxy": min(
                                len(held_subjects),
                                len(held_stimuli),
                            ),
                            "exact_statistical_ess_identifiable_"
                            "pre_model": False,
                            "session_split_leakage": False,
                        }
                    )

            nested_rows.append(cell_record)

    return nested_rows, flat_rows


def summarize_scheme(
    scheme_name: str,
    flat: pd.DataFrame,
    k_subject: int,
    k_stimulus: int,
) -> dict[str, Any]:
    subset = flat[flat["scheme"] == scheme_name].copy()

    per_policy: dict[str, Any] = {}
    overall_single_class = 0
    global_min_test_class = None
    global_min_train_class = None

    for task in TASKS:
        per_policy[task] = {}
        for policy in POLICIES:
            rows = subset[
                (subset["task"] == task)
                & (subset["label_policy"] == policy)
            ]
            min_test_class = int(
                rows[["test_low", "test_high"]].min(axis=1).min()
            )
            min_train_class = int(
                rows[["train_low", "train_high"]].min(axis=1).min()
            )
            single_test = int(rows["test_single_class"].sum())
            single_train = int(rows["train_single_class"].sum())

            overall_single_class += single_test + single_train
            global_min_test_class = (
                min_test_class
                if global_min_test_class is None
                else min(global_min_test_class, min_test_class)
            )
            global_min_train_class = (
                min_train_class
                if global_min_train_class is None
                else min(global_min_train_class, min_train_class)
            )

            per_policy[task][policy] = {
                "outer_cells": len(rows),
                "min_test_low": int(rows["test_low"].min()),
                "min_test_high": int(rows["test_high"].min()),
                "min_test_class_support": min_test_class,
                "min_train_class_support": min_train_class,
                "single_class_test_cells": single_test,
                "single_class_train_cells": single_train,
                "min_test_retained": int(rows["test_retained"].min()),
                "max_test_retained": int(rows["test_retained"].max()),
                "max_midpoint_removed_fraction": float(
                    rows["test_midpoint_removed_fraction"].max()
                ),
                "min_majority_test_accuracy": float(
                    rows["train_majority_test_accuracy"].min()
                ),
                "max_majority_test_accuracy": float(
                    rows["train_majority_test_accuracy"].max()
                ),
                "max_test_stimulus_label_nmi": (
                    float(rows["test_stimulus_label_nmi"].max())
                    if rows["test_stimulus_label_nmi"].notna().any()
                    else None
                ),
                "max_test_presentation_order_js_divergence": (
                    float(
                        rows[
                            "test_presentation_order_js_divergence"
                        ].max()
                    )
                    if rows[
                        "test_presentation_order_js_divergence"
                    ].notna().any()
                    else None
                ),
            }

    min_held_subjects = int(subset["held_subject_count"].min())
    min_held_stimuli = int(subset["held_stimulus_count"].min())
    leakage_free = bool(
        not subset["subject_leakage"].any()
        and not subset["stimulus_leakage"].any()
        and not subset["session_split_leakage"].any()
    )
    complete_outer_grid = len(
        subset[["cell_id"]].drop_duplicates()
    ) == k_subject * k_stimulus

    if (
        overall_single_class == 0
        and global_min_test_class is not None
        and global_min_test_class >= 10
        and min_held_subjects >= 10
        and min_held_stimuli >= 5
        and leakage_free
        and complete_outer_grid
    ):
        verdict = "PASS_STRONG_CAPACITY"
    elif (
        overall_single_class == 0
        and global_min_test_class is not None
        and global_min_test_class >= 5
        and leakage_free
        and complete_outer_grid
    ):
        verdict = "PASS_MINIMAL_CAPACITY"
    else:
        verdict = "FAIL_CAPACITY"

    return {
        "scheme": scheme_name,
        "k_subject": k_subject,
        "k_stimulus": k_stimulus,
        "outer_cells_expected": k_subject * k_stimulus,
        "outer_cells_observed": int(
            subset["cell_id"].nunique()
        ),
        "all_combinations_evaluated": complete_outer_grid,
        "min_held_subjects": min_held_subjects,
        "max_held_subjects": int(
            subset["held_subject_count"].max()
        ),
        "min_held_stimuli": min_held_stimuli,
        "max_held_stimuli": int(
            subset["held_stimulus_count"].max()
        ),
        "min_test_physical_trials_before_policy": int(
            subset["test_physical_trials_before_policy"].min()
        ),
        "max_test_physical_trials_before_policy": int(
            subset["test_physical_trials_before_policy"].max()
        ),
        "global_min_test_class_support": global_min_test_class,
        "global_min_train_class_support": global_min_train_class,
        "total_single_class_train_or_test_flags": overall_single_class,
        "leakage_free": leakage_free,
        "verdict": verdict,
        "threshold_note": (
            "PASS_STRONG_CAPACITY is a pre-training audit heuristic: "
            "zero single-class train/test cells across all six task-policy "
            "combinations, minimum test class support >=10, >=10 held "
            "subjects, >=5 held stimuli, zero leakage, and exhaustive cells."
        ),
        "task_policy": per_policy,
    }


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


def write_feasibility_markdown(
    path: Path,
    manifest: Path,
    scheme_summaries: list[dict[str, Any]],
    flat: pd.DataFrame,
    assignment_metadata: dict[str, Any],
) -> None:
    summary_rows = [
        {
            "scheme": item["scheme"],
            "outer_cells": item["outer_cells_observed"],
            "held_subjects": (
                f"{item['min_held_subjects']}.."
                f"{item['max_held_subjects']}"
            ),
            "held_stimuli": (
                f"{item['min_held_stimuli']}.."
                f"{item['max_held_stimuli']}"
            ),
            "test_trials_before_policy": (
                f"{item['min_test_physical_trials_before_policy']}.."
                f"{item['max_test_physical_trials_before_policy']}"
            ),
            "min_test_class": item[
                "global_min_test_class_support"
            ],
            "min_train_class": item[
                "global_min_train_class_support"
            ],
            "single_class_flags": item[
                "total_single_class_train_or_test_flags"
            ],
            "leakage_free": item["leakage_free"],
            "verdict": item["verdict"],
        }
        for item in scheme_summaries
    ]

    policy_rows: list[dict[str, Any]] = []
    for scheme in scheme_summaries:
        for task, policy_map in scheme["task_policy"].items():
            for policy, values in policy_map.items():
                policy_rows.append(
                    {
                        "scheme": scheme["scheme"],
                        "task": task,
                        "policy": policy,
                        "min_test_class": values[
                            "min_test_class_support"
                        ],
                        "min_train_class": values[
                            "min_train_class_support"
                        ],
                        "single_class_test_cells": values[
                            "single_class_test_cells"
                        ],
                        "single_class_train_cells": values[
                            "single_class_train_cells"
                        ],
                        "test_retained": (
                            f"{values['min_test_retained']}.."
                            f"{values['max_test_retained']}"
                        ),
                        "max_midpoint_removed_fraction": round(
                            values[
                                "max_midpoint_removed_fraction"
                            ],
                            6,
                        ),
                        "majority_accuracy_range": (
                            f"{values['min_majority_test_accuracy']:.4f}.."
                            f"{values['max_majority_test_accuracy']:.4f}"
                        ),
                        "max_test_stimulus_label_nmi": (
                            round(
                                values[
                                    "max_test_stimulus_label_nmi"
                                ],
                                6,
                            )
                            if values[
                                "max_test_stimulus_label_nmi"
                            ]
                            is not None
                            else None
                        ),
                    }
                )

    passing = [
        item for item in scheme_summaries
        if item["verdict"] != "FAIL_CAPACITY"
    ]
    if passing:
        recommended = sorted(
            passing,
            key=lambda item: (
                item["verdict"] != "PASS_STRONG_CAPACITY",
                -item["outer_cells_observed"],
                -int(item["global_min_test_class_support"]),
            ),
        )[0]["scheme"]
        recommendation = (
            f"`{recommended}` is the leading candidate under the current "
            "pre-training support heuristic. This is not a model-selection "
            "result and must be locked before training."
        )
    else:
        recommended = None
        recommendation = (
            "Neither candidate scheme satisfies the minimum capacity gate. "
            "Strict Joint CV is not statistically defensible under these "
            "candidate partitions."
        )

    emg_removed = int(
        (
            flat["test_retained"]
            - flat["test_rows_after_eeg_emg_availability"]
        ).max()
    )

    lines = [
        "# I-DARE Strict Joint Subject–Stimulus CV Feasibility",
        "",
        "No model training was performed.",
        "",
        "## Protocol",
        "",
        "For every outer cell:",
        "",
        "- Train = source subjects × source stimuli",
        "- Primary test = held-out subjects × held-out stimuli",
        "- Diagnostic A = source subjects × held-out stimuli",
        "- Diagnostic B = held-out subjects × source stimuli",
        "",
        "All subject-fold × stimulus-fold combinations are evaluated. "
        "Diagonal-only fold pairing is not used.",
        "",
        "## Manifest",
        "",
        f"- Source manifest: `{manifest}`",
        "- Statistical unit: one physical trial",
        "- Physical grid: 63 subjects × 32 stimuli = 2016 trials",
        "- Repeated-session nesting: absent in the current manifest "
        "(one session per subject)",
        "",
        "## Construction Method",
        "",
        "Entity folds are constructed deterministically using label-support "
        "profiles and exact fold capacities, followed by deterministic "
        "pairwise-swap refinement. No EEG/EMG features, model outputs, "
        "predictions, or trained metrics are used.",
        "",
        "## Scheme Summary",
        "",
        markdown_table(
            summary_rows,
            [
                "scheme",
                "outer_cells",
                "held_subjects",
                "held_stimuli",
                "test_trials_before_policy",
                "min_test_class",
                "min_train_class",
                "single_class_flags",
                "leakage_free",
                "verdict",
            ],
        ),
        "",
        "## Task and Label-Policy Support",
        "",
        markdown_table(
            policy_rows,
            [
                "scheme",
                "task",
                "policy",
                "min_test_class",
                "min_train_class",
                "single_class_test_cells",
                "single_class_train_cells",
                "test_retained",
                "max_midpoint_removed_fraction",
                "majority_accuracy_range",
                "max_test_stimulus_label_nmi",
            ],
        ),
        "",
        "## Leakage and Modality Availability",
        "",
        "- Subject leakage: zero if all scheme rows report leakage-free.",
        "- Stimulus leakage: zero if all scheme rows report leakage-free.",
        f"- Maximum rows removed by EEG+EMG availability filtering in any "
        f"cell-policy combination: `{emg_removed}`",
        "- This is an availability-level check, not a signal-quality "
        "artifact rejection analysis.",
        "",
        "## Effective Independent Support",
        "",
        "An exact statistical effective sample size cannot be identified "
        "before a fitted model because two-way residual dependence and ICC "
        "are unknown. The audit therefore reports physical-trial count, "
        "independent held-out subject count, independent held-out stimulus "
        "count, and the conservative minimum-axis capacity proxy separately.",
        "",
        "## Decision",
        "",
        recommendation,
        "",
        f"- Recommended candidate: `{recommended}`",
        "- Fold assignments must be committed and frozen before any model "
        "training or hyperparameter comparison.",
        "- Chance distributions, shortcut baselines, donor availability, "
        "and stream/TTA capacity remain separate next-stage audits.",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()

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
    frame = load_and_validate_manifest(manifest_path)

    subject_entities, subject_features, subject_feature_names = (
        build_entity_profiles(frame, "subject_id")
    )
    stimulus_entities, stimulus_features, stimulus_feature_names = (
        build_entity_profiles(frame, "stimulus_id")
    )

    candidates: dict[str, Any] = {
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "manifest": str(manifest_path),
        "construction_uses_model_outputs": False,
        "construction_uses_eeg_or_emg_features": False,
        "physical_trial_is_statistical_unit": True,
        "schemes": {},
    }

    all_assignment_rows: list[dict[str, Any]] = []
    all_nested_cells: list[dict[str, Any]] = []
    all_flat_rows: list[dict[str, Any]] = []
    assignment_metadata: dict[str, Any] = {}

    for scheme_name, (k_subject, k_stimulus) in SCHEMES.items():
        subject_assignment, subject_meta = balanced_partition(
            subject_entities,
            subject_features,
            k_subject,
            scheme_name,
            "subject",
        )
        stimulus_assignment, stimulus_meta = balanced_partition(
            stimulus_entities,
            stimulus_features,
            k_stimulus,
            scheme_name,
            "stimulus",
        )

        assignment_metadata[scheme_name] = {
            "subject": subject_meta,
            "stimulus": stimulus_meta,
        }

        subject_rows = [
            {
                "scheme": scheme_name,
                "axis": "subject",
                "entity_id": entity,
                "fold_index_0based": fold,
                "fold_index_1based": fold + 1,
            }
            for entity, fold in sorted(subject_assignment.items())
        ]
        stimulus_rows = [
            {
                "scheme": scheme_name,
                "axis": "stimulus",
                "entity_id": entity,
                "fold_index_0based": fold,
                "fold_index_1based": fold + 1,
            }
            for entity, fold in sorted(stimulus_assignment.items())
        ]
        all_assignment_rows.extend(subject_rows)
        all_assignment_rows.extend(stimulus_rows)

        write_csv(
            outputs[f"{scheme_name}_subject_csv"],
            subject_rows,
        )
        write_csv(
            outputs[f"{scheme_name}_stimulus_csv"],
            stimulus_rows,
        )

        nested_cells, flat_rows = build_outer_cells(
            frame,
            scheme_name,
            subject_assignment,
            stimulus_assignment,
            k_subject,
            k_stimulus,
        )
        all_nested_cells.extend(nested_cells)
        all_flat_rows.extend(flat_rows)

        candidates["schemes"][scheme_name] = {
            "k_subject": k_subject,
            "k_stimulus": k_stimulus,
            "outer_cell_count": k_subject * k_stimulus,
            "subject_feature_names": subject_feature_names,
            "stimulus_feature_names": stimulus_feature_names,
            "subject_assignment": subject_assignment,
            "stimulus_assignment": stimulus_assignment,
            "subject_partition_metadata": subject_meta,
            "stimulus_partition_metadata": stimulus_meta,
            "outer_cells": nested_cells,
        }

    flat = pd.DataFrame(all_flat_rows)

    scheme_summaries = [
        summarize_scheme(
            scheme_name,
            flat,
            k_subject,
            k_stimulus,
        )
        for scheme_name, (k_subject, k_stimulus) in SCHEMES.items()
    ]

    candidates["scheme_summaries"] = scheme_summaries

    passing = [
        item for item in scheme_summaries
        if item["verdict"] != "FAIL_CAPACITY"
    ]
    if passing:
        recommended = sorted(
            passing,
            key=lambda item: (
                item["verdict"] != "PASS_STRONG_CAPACITY",
                -item["outer_cells_observed"],
                -int(item["global_min_test_class_support"]),
            ),
        )[0]["scheme"]
    else:
        recommended = None

    candidates["recommended_candidate_pretraining"] = recommended
    candidates["recommendation_is_model_selection"] = False

    outputs["candidates_json"].write_text(
        json.dumps(
            safe_json(candidates),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    write_csv(outputs["assignments_csv"], all_assignment_rows)
    flat.to_csv(outputs["cell_support_csv"], index=False)

    feasibility = {
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "manifest": str(manifest_path),
        "scheme_summaries": scheme_summaries,
        "recommended_candidate_pretraining": recommended,
        "assignment_metadata": assignment_metadata,
        "outputs": {
            key: str(path) for key, path in outputs.items()
        },
    }
    outputs["feasibility_json"].write_text(
        json.dumps(
            safe_json(feasibility),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    write_feasibility_markdown(
        outputs["feasibility_md"],
        manifest_path,
        scheme_summaries,
        flat,
        assignment_metadata,
    )

    print("I-DARE Joint-CV candidate audit completed.")
    print(f"Branch: {branch}")
    print(f"HEAD: {head}")
    print(f"Manifest rows: {len(frame)}")
    for summary in scheme_summaries:
        print(
            f"{summary['scheme']}: "
            f"cells={summary['outer_cells_observed']}, "
            f"held_subjects="
            f"{summary['min_held_subjects']}.."
            f"{summary['max_held_subjects']}, "
            f"held_stimuli="
            f"{summary['min_held_stimuli']}.."
            f"{summary['max_held_stimuli']}, "
            f"min_test_class="
            f"{summary['global_min_test_class_support']}, "
            f"single_class_flags="
            f"{summary['total_single_class_train_or_test_flags']}, "
            f"verdict={summary['verdict']}"
        )
    print(f"Recommended pre-training candidate: {recommended}")
    print(f"Report: {outputs['feasibility_md']}")
    print(f"Cell support CSV: {outputs['cell_support_csv']}")
    print(f"Folds JSON: {outputs['candidates_json']}")


if __name__ == "__main__":
    main()

