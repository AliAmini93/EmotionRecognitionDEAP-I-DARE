#!/usr/bin/env python3
"""Run leakage-safe shortcut baselines and null tests for frozen I-DARE 4x4 CV.

Scope
-----
- Uses the frozen label-blind repeated 4x4 Strict Joint protocol.
- Fits only simple label/metadata shortcut baselines.
- Does not train EEG, EMG, fusion, PM-SSI-DG, LRSC-TTA, or any deep model.
- Uses train-region labels only for every outer cell.
- Never uses target-subject or target-stimulus labels during fitting.

Primary-test legal baselines
----------------------------
1. Global train prior / majority.
2. Presentation-order-bin prior learned from train only.
3. Fixed quadratic logistic regression on presentation order learned from
   train only, with no tuning.

Diagnostic baselines
--------------------
- Subject prior on source-subject × held-stimulus diagnostic cells.
- Stimulus prior on held-subject × source-stimulus diagnostic cells.

Null test
---------
For the main discard-midpoint policy, train labels are permuted within each
source subject inside each outer cell. This preserves subject prevalence while
breaking order association. The order-bin baseline is then refit and evaluated
on the untouched primary test labels.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    roc_auc_score,
)


REPO = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE")
MANIFEST = REPO / "docs" / "joint_cv" / "idare_trial_manifest.csv"
ASSIGNMENTS = (
    REPO / "folds" / "idare_4x4_label_blind_repeated_assignments.csv"
)
PROTOCOL = (
    REPO / "folds" / "idare_4x4_label_blind_repeated_protocol.json"
)
DOCS = REPO / "docs" / "joint_cv"
EXPECTED_BRANCH = "joint-cv-capacity-audit"

TASKS = ("valence", "arousal")
POLICIES = (
    "discard_midpoint",
    "midpoint_as_low",
    "midpoint_as_high",
)
PRIMARY_BASELINES = (
    "global_train_prior",
    "order_bin_prior",
    "order_quadratic_logistic",
)

OUTPUT_NAMES = {
    "cell_csv": "idare_4x4_shortcut_baseline_cell_metrics.csv",
    "summary_csv": "idare_4x4_shortcut_baseline_summary.csv",
    "null_csv": "idare_4x4_shortcut_null_tests.csv",
    "md": "idare_4x4_shortcut_baseline_audit.md",
    "json": "idare_4x4_shortcut_baseline_audit.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--assignments", type=Path, default=ASSIGNMENTS)
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    parser.add_argument("--docs-dir", type=Path, default=DOCS)
    parser.add_argument(
        "--permutations",
        type=int,
        default=500,
        help="Within-source-subject permutations per repetition and task.",
    )
    parser.add_argument(
        "--smoothing-strength",
        type=float,
        default=8.0,
        help="Empirical-Bayes shrinkage toward the global train prior.",
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


def deterministic_seed(
    manifest_hash: str,
    repetition: int,
    task: str,
    permutation: int,
) -> int:
    payload = (
        f"{manifest_hash}|shortcut-null|rep={repetition}|"
        f"task={task}|perm={permutation}"
    ).encode("utf-8")
    return int.from_bytes(
        hashlib.sha256(payload).digest()[:8],
        "big",
    ) % (2**32)


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
                "Refusing to overwrite existing outputs:\n"
                + "\n".join(f"- {path}" for path in existing)
            )
    return outputs


def load_inputs(
    manifest_path: Path,
    assignments_path: Path,
    protocol_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    if not assignments_path.exists():
        raise FileNotFoundError(assignments_path)
    if not protocol_path.exists():
        raise FileNotFoundError(protocol_path)

    manifest = pd.read_csv(manifest_path)
    assignments = pd.read_csv(assignments_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))

    manifest_required = {
        "trial_id",
        "subject_id",
        "stimulus_id",
        "presentation_order",
        "eeg_available",
        "emg_available",
        *{
            f"{task}_{policy}"
            for task in TASKS
            for policy in POLICIES
        },
    }
    missing_manifest = sorted(
        manifest_required - set(manifest.columns)
    )
    if missing_manifest:
        raise ValueError(
            f"Manifest missing columns: {missing_manifest}"
        )

    assignment_required = {
        "repetition",
        "role",
        "axis",
        "entity_id",
        "fold_index_0based",
        "partition_uses_labels",
        "manifest_sha256",
    }
    missing_assignments = sorted(
        assignment_required - set(assignments.columns)
    )
    if missing_assignments:
        raise ValueError(
            f"Assignments missing columns: {missing_assignments}"
        )

    manifest = manifest.copy()
    manifest["trial_id"] = manifest["trial_id"].astype(str)
    manifest["subject_id"] = manifest["subject_id"].astype(str)
    manifest["stimulus_id"] = manifest["stimulus_id"].astype(str)
    manifest["presentation_order"] = pd.to_numeric(
        manifest["presentation_order"],
        errors="raise",
    ).astype(int)

    assignments = assignments.copy()
    assignments["entity_id"] = assignments["entity_id"].astype(str)
    assignments["repetition"] = pd.to_numeric(
        assignments["repetition"],
        errors="raise",
    ).astype(int)
    assignments["fold_index_0based"] = pd.to_numeric(
        assignments["fold_index_0based"],
        errors="raise",
    ).astype(int)

    if len(manifest) != 2016:
        raise ValueError(f"Expected 2016 trials, found {len(manifest)}")
    if manifest["trial_id"].duplicated().any():
        raise ValueError("Duplicate trial_id in manifest")
    if manifest.duplicated(
        ["subject_id", "stimulus_id"]
    ).any():
        raise ValueError("Duplicate subject-stimulus cells")

    if assignments["partition_uses_labels"].astype(bool).any():
        raise ValueError(
            "Frozen protocol unexpectedly reports label-using partitions"
        )

    manifest_hash = sha256_file(manifest_path)
    assignment_hashes = set(
        assignments["manifest_sha256"].astype(str)
    )
    if assignment_hashes != {manifest_hash}:
        raise ValueError(
            "Assignment manifest hash does not match current manifest"
        )
    if protocol.get("manifest_sha256") != manifest_hash:
        raise ValueError(
            "Protocol manifest hash does not match current manifest"
        )

    return manifest, assignments, protocol


def assignments_for_repetition(
    assignments: pd.DataFrame,
    repetition: int,
) -> tuple[dict[str, int], dict[str, int]]:
    subset = assignments[
        assignments["repetition"] == repetition
    ]
    subject_rows = subset[subset["axis"] == "subject"]
    stimulus_rows = subset[subset["axis"] == "stimulus"]

    subject_assignment = {
        str(row["entity_id"]): int(row["fold_index_0based"])
        for _, row in subject_rows.iterrows()
    }
    stimulus_assignment = {
        str(row["entity_id"]): int(row["fold_index_0based"])
        for _, row in stimulus_rows.iterrows()
    }

    if len(subject_assignment) != 63:
        raise ValueError(
            f"rep {repetition}: expected 63 subject assignments"
        )
    if len(stimulus_assignment) != 32:
        raise ValueError(
            f"rep {repetition}: expected 32 stimulus assignments"
        )
    if set(subject_assignment.values()) != {0, 1, 2, 3}:
        raise ValueError(
            f"rep {repetition}: invalid subject fold set"
        )
    if set(stimulus_assignment.values()) != {0, 1, 2, 3}:
        raise ValueError(
            f"rep {repetition}: invalid stimulus fold set"
        )

    return subject_assignment, stimulus_assignment


def label_view(
    frame: pd.DataFrame,
    task: str,
    policy: str,
) -> tuple[pd.DataFrame, np.ndarray]:
    column = f"{task}_{policy}"
    values = pd.to_numeric(frame[column], errors="coerce")
    retained = values.notna()

    result = frame.loc[retained].copy()
    labels = values.loc[retained].astype(int).to_numpy()
    return result, labels


def clipped_probabilities(probabilities: np.ndarray) -> np.ndarray:
    return np.clip(
        np.asarray(probabilities, dtype=float),
        1e-6,
        1.0 - 1e-6,
    )


def metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> dict[str, Any]:
    y_true = np.asarray(y_true, dtype=int)
    probabilities = clipped_probabilities(probabilities)
    predictions = (probabilities >= 0.5).astype(int)

    if len(y_true) == 0:
        return {
            "n": 0,
            "low": 0,
            "high": 0,
            "accuracy": None,
            "balanced_accuracy": None,
            "macro_f1": None,
            "roc_auc": None,
            "brier": None,
            "log_loss": None,
        }

    both_classes = len(np.unique(y_true)) == 2

    return {
        "n": int(len(y_true)),
        "low": int((y_true == 0).sum()),
        "high": int((y_true == 1).sum()),
        "accuracy": float(
            accuracy_score(y_true, predictions)
        ),
        "balanced_accuracy": (
            float(
                balanced_accuracy_score(
                    y_true,
                    predictions,
                )
            )
            if both_classes
            else None
        ),
        "macro_f1": float(
            f1_score(
                y_true,
                predictions,
                average="macro",
                labels=[0, 1],
                zero_division=0,
            )
        ),
        "roc_auc": (
            float(roc_auc_score(y_true, probabilities))
            if both_classes
            else None
        ),
        "brier": float(
            brier_score_loss(y_true, probabilities)
        ),
        "log_loss": float(
            log_loss(
                y_true,
                probabilities,
                labels=[0, 1],
            )
        ),
    }


def global_probability(y_train: np.ndarray) -> float:
    if len(y_train) == 0:
        raise ValueError("Empty training labels")
    return float(np.mean(y_train))


def smoothed_group_probabilities(
    train_groups: pd.Series,
    y_train: np.ndarray,
    test_groups: pd.Series,
    alpha: float,
) -> np.ndarray:
    global_p = global_probability(y_train)

    train_table = pd.DataFrame(
        {
            "group": train_groups.astype(str).to_numpy(),
            "label": np.asarray(y_train, dtype=int),
        }
    )
    grouped = train_table.groupby("group")["label"].agg(
        ["sum", "count"]
    )
    group_probability = (
        grouped["sum"] + alpha * global_p
    ) / (grouped["count"] + alpha)

    return (
        test_groups.astype(str)
        .map(group_probability)
        .fillna(global_p)
        .to_numpy(dtype=float)
    )


def order_bins(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="raise").astype(int)
    if not values.between(1, 32).all():
        raise ValueError("presentation_order outside 1..32")
    return ((values - 1) // 4 + 1).astype(str)


def order_quadratic_probabilities(
    train_order: pd.Series,
    y_train: np.ndarray,
    test_order: pd.Series,
) -> np.ndarray:
    global_p = global_probability(y_train)
    if len(np.unique(y_train)) < 2:
        return np.full(len(test_order), global_p, dtype=float)

    train_x = (
        pd.to_numeric(train_order, errors="raise")
        .to_numpy(dtype=float)
    )
    test_x = (
        pd.to_numeric(test_order, errors="raise")
        .to_numpy(dtype=float)
    )

    train_z = (train_x - 16.5) / 16.0
    test_z = (test_x - 16.5) / 16.0

    train_features = np.column_stack(
        [train_z, train_z * train_z]
    )
    test_features = np.column_stack(
        [test_z, test_z * test_z]
    )

    model = LogisticRegression(
        C=1.0,
        solver="lbfgs",
        max_iter=1000,
        random_state=0,
    )
    model.fit(train_features, y_train)
    return model.predict_proba(test_features)[:, 1]


def make_masks(
    frame: pd.DataFrame,
    subject_assignment: dict[str, int],
    stimulus_assignment: dict[str, int],
    subject_fold_index: int,
    stimulus_fold_index: int,
) -> dict[str, np.ndarray]:
    subject_fold = frame["subject_id"].map(subject_assignment)
    stimulus_fold = frame["stimulus_id"].map(stimulus_assignment)

    if subject_fold.isna().any() or stimulus_fold.isna().any():
        raise ValueError("Incomplete assignment mapping")

    held_subject = (
        subject_fold.to_numpy() == subject_fold_index
    )
    held_stimulus = (
        stimulus_fold.to_numpy() == stimulus_fold_index
    )

    return {
        "train": (~held_subject) & (~held_stimulus),
        "primary_test": held_subject & held_stimulus,
        "seen_subject_unseen_stimulus": (
            (~held_subject) & held_stimulus
        ),
        "unseen_subject_seen_stimulus": (
            held_subject & (~held_stimulus)
        ),
    }


def fit_predict_baseline(
    baseline: str,
    train_frame: pd.DataFrame,
    y_train: np.ndarray,
    test_frame: pd.DataFrame,
    alpha: float,
) -> np.ndarray:
    global_p = global_probability(y_train)

    if baseline == "global_train_prior":
        return np.full(len(test_frame), global_p, dtype=float)

    if baseline == "order_bin_prior":
        return smoothed_group_probabilities(
            order_bins(train_frame["presentation_order"]),
            y_train,
            order_bins(test_frame["presentation_order"]),
            alpha,
        )

    if baseline == "order_quadratic_logistic":
        return order_quadratic_probabilities(
            train_frame["presentation_order"],
            y_train,
            test_frame["presentation_order"],
        )

    if baseline == "subject_prior":
        return smoothed_group_probabilities(
            train_frame["subject_id"],
            y_train,
            test_frame["subject_id"],
            alpha,
        )

    if baseline == "stimulus_prior":
        return smoothed_group_probabilities(
            train_frame["stimulus_id"],
            y_train,
            test_frame["stimulus_id"],
            alpha,
        )

    raise ValueError(f"Unknown baseline: {baseline}")


def evaluate_all_baselines(
    manifest: pd.DataFrame,
    assignments: pd.DataFrame,
    repetitions: list[int],
    alpha: float,
) -> tuple[
    list[dict[str, Any]],
    dict[tuple[int, str, str, str], dict[str, list[Any]]],
]:
    cell_rows: list[dict[str, Any]] = []
    pooled: dict[
        tuple[int, str, str, str],
        dict[str, list[Any]],
    ] = defaultdict(
        lambda: {
            "trial_id": [],
            "y_true": [],
            "probability": [],
        }
    )

    for repetition in repetitions:
        subject_assignment, stimulus_assignment = (
            assignments_for_repetition(
                assignments,
                repetition,
            )
        )
        role = "primary" if repetition == 0 else "sensitivity"

        for subject_fold_index in range(4):
            for stimulus_fold_index in range(4):
                masks = make_masks(
                    manifest,
                    subject_assignment,
                    stimulus_assignment,
                    subject_fold_index,
                    stimulus_fold_index,
                )
                cell_id = (
                    f"rep{repetition:02d}_"
                    f"S{subject_fold_index + 1:02d}_"
                    f"T{stimulus_fold_index + 1:02d}"
                )

                for task in TASKS:
                    for policy in POLICIES:
                        train_frame, y_train = label_view(
                            manifest.loc[masks["train"]],
                            task,
                            policy,
                        )
                        primary_frame, y_primary = label_view(
                            manifest.loc[masks["primary_test"]],
                            task,
                            policy,
                        )
                        diag_subject_frame, y_diag_subject = label_view(
                            manifest.loc[
                                masks[
                                    "seen_subject_unseen_stimulus"
                                ]
                            ],
                            task,
                            policy,
                        )
                        diag_stimulus_frame, y_diag_stimulus = label_view(
                            manifest.loc[
                                masks[
                                    "unseen_subject_seen_stimulus"
                                ]
                            ],
                            task,
                            policy,
                        )

                        if len(np.unique(y_train)) < 2:
                            raise ValueError(
                                f"{cell_id} {task} {policy}: "
                                "single-class training labels"
                            )

                        for baseline in PRIMARY_BASELINES:
                            probabilities = fit_predict_baseline(
                                baseline,
                                train_frame,
                                y_train,
                                primary_frame,
                                alpha,
                            )
                            result = metrics(
                                y_primary,
                                probabilities,
                            )

                            row = {
                                "repetition": repetition,
                                "role": role,
                                "cell_id": cell_id,
                                "subject_fold": (
                                    subject_fold_index + 1
                                ),
                                "stimulus_fold": (
                                    stimulus_fold_index + 1
                                ),
                                "task": task,
                                "label_policy": policy,
                                "region": "primary_test",
                                "baseline": baseline,
                                **result,
                                "fit_uses_target_subject_labels": False,
                                "fit_uses_target_stimulus_labels": False,
                                "fit_uses_eeg_or_emg": False,
                            }
                            cell_rows.append(row)

                            key = (
                                repetition,
                                task,
                                policy,
                                baseline,
                            )
                            pooled[key]["trial_id"].extend(
                                primary_frame[
                                    "trial_id"
                                ].astype(str).tolist()
                            )
                            pooled[key]["y_true"].extend(
                                y_primary.tolist()
                            )
                            pooled[key]["probability"].extend(
                                probabilities.tolist()
                            )

                        for (
                            region_name,
                            baseline,
                            test_frame,
                            y_test,
                        ) in (
                            (
                                "seen_subject_unseen_stimulus",
                                "subject_prior",
                                diag_subject_frame,
                                y_diag_subject,
                            ),
                            (
                                "unseen_subject_seen_stimulus",
                                "stimulus_prior",
                                diag_stimulus_frame,
                                y_diag_stimulus,
                            ),
                        ):
                            for diagnostic_baseline in (
                                "global_train_prior",
                                baseline,
                            ):
                                probabilities = fit_predict_baseline(
                                    diagnostic_baseline,
                                    train_frame,
                                    y_train,
                                    test_frame,
                                    alpha,
                                )
                                result = metrics(
                                    y_test,
                                    probabilities,
                                )
                                cell_rows.append(
                                    {
                                        "repetition": repetition,
                                        "role": role,
                                        "cell_id": cell_id,
                                        "subject_fold": (
                                            subject_fold_index + 1
                                        ),
                                        "stimulus_fold": (
                                            stimulus_fold_index + 1
                                        ),
                                        "task": task,
                                        "label_policy": policy,
                                        "region": region_name,
                                        "baseline": (
                                            diagnostic_baseline
                                        ),
                                        **result,
                                        "fit_uses_target_subject_labels": False,
                                        "fit_uses_target_stimulus_labels": False,
                                        "fit_uses_eeg_or_emg": False,
                                    }
                                )

    return cell_rows, pooled


def summarize_results(
    cell_frame: pd.DataFrame,
    pooled: dict[
        tuple[int, str, str, str],
        dict[str, list[Any]],
    ],
) -> list[dict[str, Any]]:
    summary_rows: list[dict[str, Any]] = []

    for (
        repetition,
        task,
        policy,
        baseline,
    ), values in sorted(pooled.items()):
        trial_ids = values["trial_id"]
        if len(trial_ids) != len(set(trial_ids)):
            raise ValueError(
                f"Duplicate primary test trial in pooled predictions: "
                f"rep={repetition}, task={task}, policy={policy}, "
                f"baseline={baseline}"
            )

        result = metrics(
            np.asarray(values["y_true"], dtype=int),
            np.asarray(values["probability"], dtype=float),
        )
        summary_rows.append(
            {
                "repetition": repetition,
                "role": (
                    "primary"
                    if repetition == 0
                    else "sensitivity"
                ),
                "task": task,
                "label_policy": policy,
                "region": "primary_test",
                "aggregation": "pooled_unique_physical_trials",
                "baseline": baseline,
                **result,
                "cell_balanced_accuracy_mean": float(
                    cell_frame[
                        (cell_frame["repetition"] == repetition)
                        & (cell_frame["task"] == task)
                        & (cell_frame["label_policy"] == policy)
                        & (cell_frame["region"] == "primary_test")
                        & (cell_frame["baseline"] == baseline)
                    ]["balanced_accuracy"].mean()
                ),
                "cell_balanced_accuracy_std": float(
                    cell_frame[
                        (cell_frame["repetition"] == repetition)
                        & (cell_frame["task"] == task)
                        & (cell_frame["label_policy"] == policy)
                        & (cell_frame["region"] == "primary_test")
                        & (cell_frame["baseline"] == baseline)
                    ]["balanced_accuracy"].std(ddof=1)
                ),
            }
        )

    diagnostics = cell_frame[
        cell_frame["region"] != "primary_test"
    ].copy()
    group_columns = [
        "repetition",
        "role",
        "task",
        "label_policy",
        "region",
        "baseline",
    ]
    for keys, group in diagnostics.groupby(
        group_columns,
        sort=True,
    ):
        (
            repetition,
            role,
            task,
            policy,
            region,
            baseline,
        ) = keys
        summary_rows.append(
            {
                "repetition": int(repetition),
                "role": role,
                "task": task,
                "label_policy": policy,
                "region": region,
                "aggregation": "macro_mean_across_overlapping_cells",
                "baseline": baseline,
                "n": int(group["n"].sum()),
                "low": int(group["low"].sum()),
                "high": int(group["high"].sum()),
                "accuracy": float(group["accuracy"].mean()),
                "balanced_accuracy": float(
                    group["balanced_accuracy"].mean()
                ),
                "macro_f1": float(group["macro_f1"].mean()),
                "roc_auc": float(group["roc_auc"].mean()),
                "brier": float(group["brier"].mean()),
                "log_loss": float(group["log_loss"].mean()),
                "cell_balanced_accuracy_mean": float(
                    group["balanced_accuracy"].mean()
                ),
                "cell_balanced_accuracy_std": float(
                    group["balanced_accuracy"].std(ddof=1)
                ),
            }
        )

    return summary_rows


def permute_labels_within_subject(
    train_frame: pd.DataFrame,
    y_train: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    permuted = np.asarray(y_train, dtype=int).copy()
    subject_values = train_frame[
        "subject_id"
    ].astype(str).to_numpy()

    for subject_id in np.unique(subject_values):
        indices = np.flatnonzero(
            subject_values == subject_id
        )
        shuffled_values = permuted[indices].copy()
        rng.shuffle(shuffled_values)
        permuted[indices] = shuffled_values

    return permuted


def pooled_observed_ba(
    summary_frame: pd.DataFrame,
    repetition: int,
    task: str,
) -> float:
    row = summary_frame[
        (summary_frame["repetition"] == repetition)
        & (summary_frame["task"] == task)
        & (
            summary_frame["label_policy"]
            == "discard_midpoint"
        )
        & (summary_frame["region"] == "primary_test")
        & (summary_frame["baseline"] == "order_bin_prior")
    ]
    if len(row) != 1:
        raise ValueError(
            f"Expected one observed row, found {len(row)}"
        )
    return float(row.iloc[0]["balanced_accuracy"])


def run_null_tests(
    manifest: pd.DataFrame,
    assignments: pd.DataFrame,
    repetitions: list[int],
    summary_frame: pd.DataFrame,
    permutations: int,
    alpha: float,
    manifest_hash: str,
) -> list[dict[str, Any]]:
    null_rows: list[dict[str, Any]] = []

    for repetition in repetitions:
        subject_assignment, stimulus_assignment = (
            assignments_for_repetition(
                assignments,
                repetition,
            )
        )

        for task in TASKS:
            observed = pooled_observed_ba(
                summary_frame,
                repetition,
                task,
            )
            null_values: list[float] = []

            for permutation in range(permutations):
                rng = np.random.default_rng(
                    deterministic_seed(
                        manifest_hash,
                        repetition,
                        task,
                        permutation,
                    )
                )
                pooled_y: list[int] = []
                pooled_probability: list[float] = []
                pooled_trial_ids: list[str] = []

                for subject_fold_index in range(4):
                    for stimulus_fold_index in range(4):
                        masks = make_masks(
                            manifest,
                            subject_assignment,
                            stimulus_assignment,
                            subject_fold_index,
                            stimulus_fold_index,
                        )

                        train_frame, y_train = label_view(
                            manifest.loc[masks["train"]],
                            task,
                            "discard_midpoint",
                        )
                        test_frame, y_test = label_view(
                            manifest.loc[
                                masks["primary_test"]
                            ],
                            task,
                            "discard_midpoint",
                        )

                        permuted_train = (
                            permute_labels_within_subject(
                                train_frame,
                                y_train,
                                rng,
                            )
                        )
                        probabilities = (
                            fit_predict_baseline(
                                "order_bin_prior",
                                train_frame,
                                permuted_train,
                                test_frame,
                                alpha,
                            )
                        )

                        pooled_trial_ids.extend(
                            test_frame[
                                "trial_id"
                            ].astype(str).tolist()
                        )
                        pooled_y.extend(y_test.tolist())
                        pooled_probability.extend(
                            probabilities.tolist()
                        )

                if len(pooled_trial_ids) != len(
                    set(pooled_trial_ids)
                ):
                    raise ValueError(
                        "Duplicate pooled primary test trial "
                        "during null test"
                    )

                null_metric = metrics(
                    np.asarray(pooled_y, dtype=int),
                    np.asarray(
                        pooled_probability,
                        dtype=float,
                    ),
                )["balanced_accuracy"]
                assert null_metric is not None
                null_values.append(float(null_metric))

            null_array = np.asarray(
                null_values,
                dtype=float,
            )
            p_value = float(
                (
                    1
                    + np.sum(null_array >= observed)
                )
                / (permutations + 1)
            )

            null_rows.append(
                {
                    "repetition": repetition,
                    "role": (
                        "primary"
                        if repetition == 0
                        else "sensitivity"
                    ),
                    "task": task,
                    "label_policy": "discard_midpoint",
                    "baseline": "order_bin_prior",
                    "permutations": permutations,
                    "permutation_scheme": (
                        "shuffle train labels within each "
                        "source subject inside each outer cell"
                    ),
                    "observed_balanced_accuracy": observed,
                    "null_mean": float(null_array.mean()),
                    "null_median": float(
                        np.median(null_array)
                    ),
                    "null_std": float(
                        null_array.std(ddof=1)
                    ),
                    "null_p05": float(
                        np.quantile(null_array, 0.05)
                    ),
                    "null_p95": float(
                        np.quantile(null_array, 0.95)
                    ),
                    "effect_over_null_median": float(
                        observed
                        - np.median(null_array)
                    ),
                    "p_value_upper_tail": p_value,
                }
            )

    p_values = np.asarray(
        [row["p_value_upper_tail"] for row in null_rows],
        dtype=float,
    )
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values), dtype=float)
    running = 1.0

    for reverse_rank, index in enumerate(
        order[::-1],
        start=1,
    ):
        rank = len(p_values) - reverse_rank + 1
        value = p_values[index] * len(p_values) / rank
        running = min(running, value)
        adjusted[index] = min(running, 1.0)

    for row, q_value in zip(null_rows, adjusted):
        row["bh_fdr_q_value"] = float(q_value)
        row["significant_at_fdr_0_05"] = bool(
            q_value < 0.05
        )

    return null_rows


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

    if args.permutations < 100:
        raise ValueError("--permutations must be at least 100")
    if args.smoothing_strength <= 0:
        raise ValueError(
            "--smoothing-strength must be positive"
        )

    repo = args.repo_root.resolve()
    manifest_path = args.manifest.resolve()
    assignments_path = args.assignments.resolve()
    protocol_path = args.protocol.resolve()
    docs_dir = args.docs_dir.resolve()

    branch = git(repo, "branch", "--show-current")
    head = git(repo, "rev-parse", "HEAD")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}"
        )

    outputs = prepare_outputs(
        docs_dir,
        args.overwrite,
    )
    manifest, assignments, protocol = load_inputs(
        manifest_path,
        assignments_path,
        protocol_path,
    )
    manifest_hash = sha256_file(manifest_path)

    repetitions = sorted(
        assignments["repetition"].unique().tolist()
    )
    expected_repetitions = list(
        range(int(protocol["repetitions"]))
    )
    if repetitions != expected_repetitions:
        raise ValueError(
            f"Expected repetitions {expected_repetitions}, "
            f"found {repetitions}"
        )

    cell_rows, pooled = evaluate_all_baselines(
        manifest,
        assignments,
        repetitions,
        args.smoothing_strength,
    )
    cell_frame = pd.DataFrame(cell_rows)
    summary_rows = summarize_results(
        cell_frame,
        pooled,
    )
    summary_frame = pd.DataFrame(summary_rows)

    null_rows = run_null_tests(
        manifest,
        assignments,
        repetitions,
        summary_frame,
        args.permutations,
        args.smoothing_strength,
        manifest_hash,
    )

    cell_frame.to_csv(outputs["cell_csv"], index=False)
    pd.DataFrame(summary_rows).to_csv(
        outputs["summary_csv"],
        index=False,
    )
    pd.DataFrame(null_rows).to_csv(
        outputs["null_csv"],
        index=False,
    )

    primary_rows = summary_frame[
        (summary_frame["repetition"] == 0)
        & (summary_frame["region"] == "primary_test")
    ].copy()

    primary_table: list[dict[str, Any]] = []
    for _, row in primary_rows.iterrows():
        primary_table.append(
            {
                "task": row["task"],
                "policy": row["label_policy"],
                "baseline": row["baseline"],
                "n": int(row["n"]),
                "balanced_accuracy": round(
                    float(row["balanced_accuracy"]),
                    4,
                ),
                "macro_f1": round(
                    float(row["macro_f1"]),
                    4,
                ),
                "roc_auc": round(
                    float(row["roc_auc"]),
                    4,
                ),
                "brier": round(
                    float(row["brier"]),
                    4,
                ),
            }
        )

    diagnostic_table: list[dict[str, Any]] = []
    diagnostic_subset = summary_frame[
        (summary_frame["repetition"] == 0)
        & (summary_frame["region"] != "primary_test")
        & (
            summary_frame["label_policy"]
            == "discard_midpoint"
        )
    ]
    for _, row in diagnostic_subset.iterrows():
        diagnostic_table.append(
            {
                "task": row["task"],
                "region": row["region"],
                "baseline": row["baseline"],
                "balanced_accuracy_macro": round(
                    float(row["balanced_accuracy"]),
                    4,
                ),
                "roc_auc_macro": round(
                    float(row["roc_auc"]),
                    4,
                ),
            }
        )

    null_table: list[dict[str, Any]] = []
    for row in null_rows:
        null_table.append(
            {
                "repetition": row["repetition"],
                "role": row["role"],
                "task": row["task"],
                "observed_ba": round(
                    row["observed_balanced_accuracy"],
                    4,
                ),
                "null_median": round(
                    row["null_median"],
                    4,
                ),
                "effect": round(
                    row["effect_over_null_median"],
                    4,
                ),
                "p_value": round(
                    row["p_value_upper_tail"],
                    6,
                ),
                "fdr_q": round(
                    row["bh_fdr_q_value"],
                    6,
                ),
                "significant": row[
                    "significant_at_fdr_0_05"
                ],
            }
        )

    primary_null = [
        row for row in null_rows
        if row["repetition"] == 0
    ]
    material_order_shortcut = any(
        row["significant_at_fdr_0_05"]
        and row["effect_over_null_median"] >= 0.05
        for row in primary_null
    )

    decision = (
        "PROCEED_WITH_MATERIAL_ORDER_SHORTCUT_GATE"
        if material_order_shortcut
        else "PROCEED_WITH_STANDARD_SHORTCUT_GATE"
    )
    decision_reason = (
        "The primary repetition shows a statistically material "
        "presentation-order shortcut under the main label policy."
        if material_order_shortcut
        else
        "No primary-repetition order shortcut exceeded the "
        "predefined materiality rule of FDR q<0.05 and "
        "balanced-accuracy effect >=0.05."
    )

    report = {
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "manifest": str(manifest_path),
        "manifest_sha256": manifest_hash,
        "assignments": str(assignments_path),
        "protocol": str(protocol_path),
        "permutations": args.permutations,
        "smoothing_strength": args.smoothing_strength,
        "fit_uses_target_subject_labels": False,
        "fit_uses_target_stimulus_labels": False,
        "fit_uses_eeg_or_emg": False,
        "cell_metrics_rows": len(cell_frame),
        "summary_rows": len(summary_frame),
        "null_tests": null_rows,
        "decision": decision,
        "decision_reason": decision_reason,
        "future_model_gate": {
            "primary_test": (
                "Compare every EEG/EMG model against the best legal "
                "primary-test shortcut among global prior, order-bin "
                "prior, and fixed order-only logistic baseline."
            ),
            "diagnostic_seen_subject_unseen_stimulus": (
                "Compare against train-only subject prior."
            ),
            "diagnostic_unseen_subject_seen_stimulus": (
                "Compare against train-only stimulus prior."
            ),
            "no_architecture_tuning_on_sensitivity_repetitions": True,
        },
    }
    outputs["json"].write_text(
        json.dumps(
            safe_json(report),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    md_lines = [
        "# I-DARE 4x4 Leakage-Safe Shortcut Baseline Audit",
        "",
        "No EEG/EMG or deep model was trained. Only fixed, simple "
        "label/metadata baselines were fitted inside each legal train "
        "region.",
        "",
        "## Leakage Contract",
        "",
        "- No target-subject labels were used for fitting.",
        "- No target-stimulus labels were used for fitting.",
        "- No EEG or EMG features were used.",
        "- Primary-test stimulus-only and subject-only priors are "
        "intentionally absent because both identities are unseen.",
        "",
        "## Primary Repetition: Legal Primary-Test Baselines",
        "",
        markdown_table(
            primary_table,
            [
                "task",
                "policy",
                "baseline",
                "n",
                "balanced_accuracy",
                "macro_f1",
                "roc_auc",
                "brier",
            ],
        ),
        "",
        "## Primary Repetition: Diagnostic Identity Shortcuts",
        "",
        markdown_table(
            diagnostic_table,
            [
                "task",
                "region",
                "baseline",
                "balanced_accuracy_macro",
                "roc_auc_macro",
            ],
        ),
        "",
        "The subject-prior and stimulus-prior results are diagnostic "
        "only. Their cells overlap across the 16 outer combinations, so "
        "the report uses macro cell averages rather than pretending they "
        "are one independent pooled test set.",
        "",
        "## Presentation-Order Null Tests",
        "",
        "Main policy: discard midpoint. Train labels were shuffled within "
        "each source subject inside each outer cell, preserving subject "
        "prevalence while breaking order association.",
        "",
        markdown_table(
            null_table,
            [
                "repetition",
                "role",
                "task",
                "observed_ba",
                "null_median",
                "effect",
                "p_value",
                "fdr_q",
                "significant",
            ],
        ),
        "",
        "## Decision",
        "",
        f"- Decision: **{decision}**",
        f"- Reason: {decision_reason}",
        "",
        "## Mandatory Gates for Future Models",
        "",
        "1. On the primary unseen-subject × unseen-stimulus test, report "
        "improvement over the best legal shortcut baseline, not only over "
        "0.5 chance.",
        "2. On source-subject × unseen-stimulus diagnostics, compare "
        "against the train-only subject prior.",
        "3. On unseen-subject × source-stimulus diagnostics, compare "
        "against the train-only stimulus prior.",
        "4. Keep repetitions 1–4 as sensitivity analyses; do not tune "
        "architectures or hyperparameters on them.",
        "5. Use paired uncertainty analysis over physical trials and "
        "outer cells when comparing a future model with these baselines.",
        "",
    ]
    outputs["md"].write_text(
        "\n".join(md_lines),
        encoding="utf-8",
    )

    print("I-DARE shortcut baseline and null audit completed.")
    print(f"Branch: {branch}")
    print(f"HEAD: {head}")
    print(f"Manifest SHA-256: {manifest_hash}")
    print(f"Cell metric rows: {len(cell_frame)}")
    print(f"Summary rows: {len(summary_frame)}")
    print(f"Null tests: {len(null_rows)}")
    print(f"Decision: {decision}")
    for row in primary_null:
        print(
            f"primary {row['task']}: "
            f"observed_ba="
            f"{row['observed_balanced_accuracy']:.4f}, "
            f"null_median={row['null_median']:.4f}, "
            f"effect={row['effect_over_null_median']:.4f}, "
            f"q={row['bh_fdr_q_value']:.6f}"
        )
    print(f"Report: {outputs['md']}")
    print(f"Cell metrics: {outputs['cell_csv']}")
    print(f"Null tests: {outputs['null_csv']}")


if __name__ == "__main__":
    main()

