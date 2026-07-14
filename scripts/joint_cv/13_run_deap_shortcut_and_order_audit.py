#!/usr/bin/env python3
"""Run leakage-safe shortcut and order-confounding audits for frozen DEAP 4x4.

This is a trial-level audit only. It does not use EEG/EMG features and does not
train any physiological, fusion, TTA, PM-SSI-DG, or LRSC model.

Primary strict-joint baselines
------------------------------
- global_train_prior
- order_bin_prior: 8 fixed bins of five presentation positions
- order_quadratic_logistic: fixed quadratic logistic model using order only

Diagnostic identity baselines
-----------------------------
- subject_prior on seen-subject x unseen-stimulus cells
- stimulus_prior on unseen-subject x seen-stimulus cells

Null tests
----------
- Quadratic order-only labels are shuffled within each source subject.
- Stimulus/order NMI is compared with within-subject random permutations.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from itertools import combinations
from pathlib import Path
from typing import Any, Callable, Iterable

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    f1_score,
    log_loss,
    normalized_mutual_info_score,
    roc_auc_score,
)


REPO = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE")
DOCS = REPO / "docs" / "joint_cv"
FOLDS = REPO / "folds"

MANIFEST = DOCS / "deap_trial_manifest.csv"
ASSIGNMENTS = FOLDS / "deap_4x4_label_blind_repeated_assignments.csv"
PROTOCOL = FOLDS / "deap_4x4_label_blind_repeated_protocol.json"

EXPECTED_BRANCH = "joint-cv-capacity-audit"

TASKS = ("valence", "arousal")
POLICIES = (
    "discard_midpoint",
    "midpoint_as_low",
    "midpoint_as_high",
)

OUTPUT_NAMES = {
    "cell_metrics_csv": "deap_4x4_shortcut_baseline_cell_metrics.csv",
    "summary_csv": "deap_4x4_shortcut_baseline_summary.csv",
    "order_null_csv": "deap_4x4_order_quadratic_null_tests.csv",
    "nmi_null_csv": "deap_order_stimulus_nmi_null.csv",
    "report_md": "deap_4x4_shortcut_and_order_audit.md",
    "report_json": "deap_4x4_shortcut_and_order_audit.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--assignments", type=Path, default=ASSIGNMENTS)
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    parser.add_argument("--docs-dir", type=Path, default=DOCS)
    parser.add_argument("--order-permutations", type=int, default=250)
    parser.add_argument("--nmi-permutations", type=int, default=500)
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


def bool_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return (
        series.astype(str)
        .str.strip()
        .str.lower()
        .isin({"true", "1", "yes", "y"})
    )


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
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], str]:
    manifest = pd.read_csv(manifest_path)
    assignments = pd.read_csv(assignments_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))

    required_manifest = {
        "trial_id",
        "subject_id",
        "stimulus_id",
        "presentation_order",
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
    missing = sorted(required_manifest - set(manifest.columns))
    if missing:
        raise ValueError(f"Manifest missing columns: {missing}")

    manifest = manifest.copy()
    manifest["trial_id"] = manifest["trial_id"].astype(str)
    manifest["subject_id"] = manifest["subject_id"].astype(str)
    manifest["stimulus_id"] = manifest["stimulus_id"].astype(str)
    manifest["presentation_order"] = pd.to_numeric(
        manifest["presentation_order"],
        errors="raise",
    ).astype(int)

    for column in (
        "chronology_verified",
        "stimulus_identity_verified",
        "mapping_verified",
        "eeg_available",
        "emg_available",
    ):
        manifest[column] = bool_series(manifest[column])

    if len(manifest) != 1280:
        raise ValueError(f"Expected 1280 trials, found {len(manifest)}")
    if manifest["subject_id"].nunique() != 32:
        raise ValueError("Expected 32 subjects")
    if manifest["stimulus_id"].nunique() != 40:
        raise ValueError("Expected 40 stimuli")
    if manifest["trial_id"].duplicated().any():
        raise ValueError("Duplicate trial_id")
    if manifest.duplicated(["subject_id", "stimulus_id"]).any():
        raise ValueError("Duplicate subject-stimulus cell")
    if not manifest["presentation_order"].between(1, 40).all():
        raise ValueError("Presentation order outside 1..40")

    for column in (
        "chronology_verified",
        "stimulus_identity_verified",
        "mapping_verified",
        "eeg_available",
        "emg_available",
    ):
        if not manifest[column].all():
            raise ValueError(f"Not all manifest rows pass {column}")

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
            f"Assignments missing columns: {missing_assignments}"
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

    if bool_series(assignments["partition_uses_labels"]).any():
        raise ValueError("Frozen assignments unexpectedly use labels")
    if sorted(assignments["repetition"].unique().tolist()) != [0, 1, 2, 3, 4]:
        raise ValueError("Expected repetitions 0..4")
    if len(assignments) != 360:
        raise ValueError(f"Expected 360 assignment rows, found {len(assignments)}")

    manifest_hash = sha256_file(manifest_path)
    if set(assignments["manifest_sha256"].astype(str)) != {manifest_hash}:
        raise ValueError("Assignment manifest hash mismatch")
    if protocol.get("manifest_sha256") != manifest_hash:
        raise ValueError("Protocol manifest hash mismatch")
    if protocol.get("decision") != "LOCK_LABEL_BLIND_4X4_PROTOCOL":
        raise ValueError("DEAP protocol is not locked")
    if protocol.get("partition_uses_labels") is not False:
        raise ValueError("Protocol unexpectedly uses labels")

    return manifest, assignments, protocol, manifest_hash


def assignments_for_rep(
    assignments: pd.DataFrame,
    repetition: int,
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

    if len(subject_assignment) != 32:
        raise ValueError(
            f"rep {repetition}: expected 32 subject assignments"
        )
    if len(stimulus_assignment) != 40:
        raise ValueError(
            f"rep {repetition}: expected 40 stimulus assignments"
        )
    return subject_assignment, stimulus_assignment


def masks_for_cell(
    frame: pd.DataFrame,
    subject_assignment: dict[str, int],
    stimulus_assignment: dict[str, int],
    subject_fold: int,
    stimulus_fold: int,
) -> dict[str, np.ndarray]:
    subject_folds = (
        frame["subject_id"]
        .map(subject_assignment)
        .to_numpy(dtype=int)
    )
    stimulus_folds = (
        frame["stimulus_id"]
        .map(stimulus_assignment)
        .to_numpy(dtype=int)
    )

    held_subject = subject_folds == subject_fold
    held_stimulus = stimulus_folds == stimulus_fold

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


def metrics(
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> dict[str, Any]:
    y_true = np.asarray(y_true, dtype=int)
    probabilities = np.clip(
        np.asarray(probabilities, dtype=float),
        1e-6,
        1.0 - 1e-6,
    )
    predictions = (probabilities >= 0.5).astype(int)

    auc = None
    if len(np.unique(y_true)) == 2:
        auc = float(roc_auc_score(y_true, probabilities))

    return {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, predictions)),
        "balanced_accuracy": float(
            balanced_accuracy_score(y_true, predictions)
        ),
        "macro_f1": float(
            f1_score(
                y_true,
                predictions,
                average="macro",
                zero_division=0,
            )
        ),
        "roc_auc": auc,
        "brier": float(brier_score_loss(y_true, probabilities)),
        "log_loss": float(
            log_loss(y_true, probabilities, labels=[0, 1])
        ),
    }


def global_probabilities(
    train: pd.DataFrame,
    y_train: np.ndarray,
    test: pd.DataFrame,
) -> np.ndarray:
    del train
    prior = float(np.mean(y_train))
    return np.full(len(test), prior, dtype=float)


def order_bin_probabilities(
    train: pd.DataFrame,
    y_train: np.ndarray,
    test: pd.DataFrame,
    alpha: float = 8.0,
) -> np.ndarray:
    global_prior = float(np.mean(y_train))
    train_bins = (
        (train["presentation_order"].to_numpy(dtype=int) - 1) // 5
    )
    test_bins = (
        (test["presentation_order"].to_numpy(dtype=int) - 1) // 5
    )

    bin_prior: dict[int, float] = {}
    for bin_index in range(8):
        selected = train_bins == bin_index
        n = int(selected.sum())
        positives = float(y_train[selected].sum())
        bin_prior[bin_index] = (
            positives + alpha * global_prior
        ) / (n + alpha)

    return np.asarray(
        [bin_prior.get(int(value), global_prior) for value in test_bins],
        dtype=float,
    )


def quadratic_order_probabilities(
    train: pd.DataFrame,
    y_train: np.ndarray,
    test: pd.DataFrame,
) -> np.ndarray:
    if len(np.unique(y_train)) < 2:
        return np.full(len(test), float(np.mean(y_train)))

    train_order = train["presentation_order"].to_numpy(dtype=float)
    test_order = test["presentation_order"].to_numpy(dtype=float)

    train_z = (train_order - 20.5) / 20.0
    test_z = (test_order - 20.5) / 20.0

    x_train = np.column_stack([train_z, train_z**2])
    x_test = np.column_stack([test_z, test_z**2])

    model = LogisticRegression(
        C=1.0,
        solver="lbfgs",
        max_iter=1000,
        random_state=0,
    )
    model.fit(x_train, y_train)
    return model.predict_proba(x_test)[:, 1]


def grouped_prior_probabilities(
    train: pd.DataFrame,
    y_train: np.ndarray,
    test: pd.DataFrame,
    group_column: str,
    alpha: float = 8.0,
) -> np.ndarray:
    global_prior = float(np.mean(y_train))
    temp = train[[group_column]].copy()
    temp["_label"] = y_train

    stats = temp.groupby(group_column)["_label"].agg(["sum", "count"])
    probabilities = {
        str(index): float(
            (row["sum"] + alpha * global_prior)
            / (row["count"] + alpha)
        )
        for index, row in stats.iterrows()
    }

    return np.asarray(
        [
            probabilities.get(str(value), global_prior)
            for value in test[group_column].astype(str)
        ],
        dtype=float,
    )


def extract_scored(
    frame: pd.DataFrame,
    label_column: str,
) -> tuple[pd.DataFrame, np.ndarray]:
    labels = pd.to_numeric(frame[label_column], errors="coerce")
    retained = labels.notna()
    scored = frame.loc[retained].copy()
    y = labels.loc[retained].astype(int).to_numpy()
    return scored, y


def add_prediction_records(
    records: list[dict[str, Any]],
    *,
    repetition: int,
    role: str,
    task: str,
    policy: str,
    region: str,
    baseline: str,
    subject_fold: int,
    stimulus_fold: int,
    test: pd.DataFrame,
    y_true: np.ndarray,
    probabilities: np.ndarray,
) -> None:
    for trial_id, subject_id, stimulus_id, y_value, probability in zip(
        test["trial_id"].astype(str),
        test["subject_id"].astype(str),
        test["stimulus_id"].astype(str),
        y_true,
        probabilities,
    ):
        records.append(
            {
                "repetition": repetition,
                "role": role,
                "task": task,
                "policy": policy,
                "region": region,
                "baseline": baseline,
                "subject_fold": subject_fold,
                "stimulus_fold": stimulus_fold,
                "trial_id": trial_id,
                "subject_id": subject_id,
                "stimulus_id": stimulus_id,
                "y_true": int(y_value),
                "probability": float(probability),
            }
        )


def run_baselines(
    manifest: pd.DataFrame,
    assignments: pd.DataFrame,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    cell_rows: list[dict[str, Any]] = []
    prediction_records: list[dict[str, Any]] = []

    primary_baselines: dict[
        str,
        Callable[[pd.DataFrame, np.ndarray, pd.DataFrame], np.ndarray],
    ] = {
        "global_train_prior": global_probabilities,
        "order_bin_prior": order_bin_probabilities,
        "order_quadratic_logistic": quadratic_order_probabilities,
    }

    for repetition in range(5):
        role = "primary" if repetition == 0 else "sensitivity"
        subject_assignment, stimulus_assignment = assignments_for_rep(
            assignments,
            repetition,
        )

        for subject_fold in range(4):
            for stimulus_fold in range(4):
                masks = masks_for_cell(
                    manifest,
                    subject_assignment,
                    stimulus_assignment,
                    subject_fold,
                    stimulus_fold,
                )

                for task in TASKS:
                    for policy in POLICIES:
                        label_column = f"{task}_{policy}"
                        train, y_train = extract_scored(
                            manifest.loc[masks["train"]],
                            label_column,
                        )
                        if len(np.unique(y_train)) != 2:
                            raise ValueError(
                                f"Single-class train: rep={repetition}, "
                                f"subject_fold={subject_fold}, "
                                f"stimulus_fold={stimulus_fold}, "
                                f"task={task}, policy={policy}"
                            )

                        primary_test, y_primary = extract_scored(
                            manifest.loc[masks["primary_test"]],
                            label_column,
                        )

                        for baseline_name, baseline_function in (
                            primary_baselines.items()
                        ):
                            probabilities = baseline_function(
                                train,
                                y_train,
                                primary_test,
                            )
                            result = metrics(y_primary, probabilities)
                            cell_rows.append(
                                {
                                    "repetition": repetition,
                                    "role": role,
                                    "task": task,
                                    "policy": policy,
                                    "region": "primary_test",
                                    "baseline": baseline_name,
                                    "subject_fold": subject_fold,
                                    "stimulus_fold": stimulus_fold,
                                    "train_n": int(len(train)),
                                    **result,
                                }
                            )
                            add_prediction_records(
                                prediction_records,
                                repetition=repetition,
                                role=role,
                                task=task,
                                policy=policy,
                                region="primary_test",
                                baseline=baseline_name,
                                subject_fold=subject_fold,
                                stimulus_fold=stimulus_fold,
                                test=primary_test,
                                y_true=y_primary,
                                probabilities=probabilities,
                            )

                        subject_diag, y_subject_diag = extract_scored(
                            manifest.loc[
                                masks[
                                    "seen_subject_unseen_stimulus"
                                ]
                            ],
                            label_column,
                        )
                        subject_diag_baselines = {
                            "global_train_prior": global_probabilities(
                                train,
                                y_train,
                                subject_diag,
                            ),
                            "subject_prior": grouped_prior_probabilities(
                                train,
                                y_train,
                                subject_diag,
                                "subject_id",
                            ),
                        }

                        for baseline_name, probabilities in (
                            subject_diag_baselines.items()
                        ):
                            result = metrics(
                                y_subject_diag,
                                probabilities,
                            )
                            cell_rows.append(
                                {
                                    "repetition": repetition,
                                    "role": role,
                                    "task": task,
                                    "policy": policy,
                                    "region": (
                                        "seen_subject_unseen_stimulus"
                                    ),
                                    "baseline": baseline_name,
                                    "subject_fold": subject_fold,
                                    "stimulus_fold": stimulus_fold,
                                    "train_n": int(len(train)),
                                    **result,
                                }
                            )

                        stimulus_diag, y_stimulus_diag = extract_scored(
                            manifest.loc[
                                masks[
                                    "unseen_subject_seen_stimulus"
                                ]
                            ],
                            label_column,
                        )
                        stimulus_diag_baselines = {
                            "global_train_prior": global_probabilities(
                                train,
                                y_train,
                                stimulus_diag,
                            ),
                            "stimulus_prior": grouped_prior_probabilities(
                                train,
                                y_train,
                                stimulus_diag,
                                "stimulus_id",
                            ),
                        }

                        for baseline_name, probabilities in (
                            stimulus_diag_baselines.items()
                        ):
                            result = metrics(
                                y_stimulus_diag,
                                probabilities,
                            )
                            cell_rows.append(
                                {
                                    "repetition": repetition,
                                    "role": role,
                                    "task": task,
                                    "policy": policy,
                                    "region": (
                                        "unseen_subject_seen_stimulus"
                                    ),
                                    "baseline": baseline_name,
                                    "subject_fold": subject_fold,
                                    "stimulus_fold": stimulus_fold,
                                    "train_n": int(len(train)),
                                    **result,
                                }
                            )

    cell_frame = pd.DataFrame(cell_rows)
    predictions = pd.DataFrame(prediction_records)
    summary_rows: list[dict[str, Any]] = []

    primary = predictions[predictions["region"] == "primary_test"]
    primary_group_columns = [
        "repetition",
        "role",
        "task",
        "policy",
        "region",
        "baseline",
    ]

    for keys, group in primary.groupby(
        primary_group_columns,
        sort=True,
    ):
        if group["trial_id"].duplicated().any():
            raise ValueError(
                f"Duplicate pooled primary trial for {keys}"
            )

        result = metrics(
            group["y_true"].to_numpy(dtype=int),
            group["probability"].to_numpy(dtype=float),
        )
        (
            repetition,
            role,
            task,
            policy,
            region,
            baseline,
        ) = keys

        matching_cells = cell_frame[
            (cell_frame["repetition"] == repetition)
            & (cell_frame["task"] == task)
            & (cell_frame["policy"] == policy)
            & (cell_frame["region"] == region)
            & (cell_frame["baseline"] == baseline)
        ]

        summary_rows.append(
            {
                "summary_type": "pooled_physical_trials",
                "repetition": repetition,
                "role": role,
                "task": task,
                "policy": policy,
                "region": region,
                "baseline": baseline,
                **result,
                "cell_balanced_accuracy_mean": float(
                    matching_cells["balanced_accuracy"].mean()
                ),
                "cell_balanced_accuracy_std": float(
                    matching_cells["balanced_accuracy"].std(ddof=1)
                ),
                "cell_roc_auc_mean": float(
                    matching_cells["roc_auc"].dropna().mean()
                ),
                "cell_count": int(len(matching_cells)),
            }
        )

    diagnostics = cell_frame[cell_frame["region"] != "primary_test"]
    diagnostic_group_columns = [
        "repetition",
        "role",
        "task",
        "policy",
        "region",
        "baseline",
    ]

    for keys, group in diagnostics.groupby(
        diagnostic_group_columns,
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
                "summary_type": "macro_outer_cells_overlapping_regions",
                "repetition": repetition,
                "role": role,
                "task": task,
                "policy": policy,
                "region": region,
                "baseline": baseline,
                "n": int(group["n"].sum()),
                "accuracy": float(group["accuracy"].mean()),
                "balanced_accuracy": float(
                    group["balanced_accuracy"].mean()
                ),
                "macro_f1": float(group["macro_f1"].mean()),
                "roc_auc": float(group["roc_auc"].dropna().mean()),
                "brier": float(group["brier"].mean()),
                "log_loss": float(group["log_loss"].mean()),
                "cell_balanced_accuracy_mean": float(
                    group["balanced_accuracy"].mean()
                ),
                "cell_balanced_accuracy_std": float(
                    group["balanced_accuracy"].std(ddof=1)
                ),
                "cell_roc_auc_mean": float(
                    group["roc_auc"].dropna().mean()
                ),
                "cell_count": int(len(group)),
            }
        )

    return cell_rows, summary_rows, prediction_records


def deterministic_seed(
    manifest_hash: str,
    *parts: Any,
) -> int:
    payload = (
        manifest_hash
        + "|DEAP|"
        + "|".join(str(part) for part in parts)
    ).encode("utf-8")
    return int.from_bytes(
        hashlib.sha256(payload).digest()[:8],
        "big",
    ) % (2**32)


def shuffle_labels_within_subject(
    train: pd.DataFrame,
    y_train: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    result = np.asarray(y_train, dtype=int).copy()
    subjects = train["subject_id"].astype(str).to_numpy()

    for subject_id in np.unique(subjects):
        indices = np.flatnonzero(subjects == subject_id)
        values = result[indices].copy()
        rng.shuffle(values)
        result[indices] = values

    return result


def bh_adjust(rows: list[dict[str, Any]], p_key: str, q_key: str) -> None:
    p_values = np.asarray([float(row[p_key]) for row in rows])
    order = np.argsort(p_values)
    adjusted = np.empty(len(rows), dtype=float)
    running = 1.0
    m = len(rows)

    for reverse_rank, index in enumerate(order[::-1], start=1):
        rank = m - reverse_rank + 1
        candidate = p_values[index] * m / rank
        running = min(running, candidate)
        adjusted[index] = min(running, 1.0)

    for row, q_value in zip(rows, adjusted):
        row[q_key] = float(q_value)
        row["significant_at_fdr_0_05"] = bool(q_value < 0.05)


def run_order_null_tests(
    manifest: pd.DataFrame,
    assignments: pd.DataFrame,
    manifest_hash: str,
    permutations: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for repetition in range(5):
        role = "primary" if repetition == 0 else "sensitivity"
        subject_assignment, stimulus_assignment = assignments_for_rep(
            assignments,
            repetition,
        )

        for task in TASKS:
            label_column = f"{task}_discard_midpoint"

            observed_y: list[int] = []
            observed_p: list[float] = []
            observed_ids: list[str] = []

            for subject_fold in range(4):
                for stimulus_fold in range(4):
                    masks = masks_for_cell(
                        manifest,
                        subject_assignment,
                        stimulus_assignment,
                        subject_fold,
                        stimulus_fold,
                    )
                    train, y_train = extract_scored(
                        manifest.loc[masks["train"]],
                        label_column,
                    )
                    test, y_test = extract_scored(
                        manifest.loc[masks["primary_test"]],
                        label_column,
                    )
                    probabilities = quadratic_order_probabilities(
                        train,
                        y_train,
                        test,
                    )
                    observed_ids.extend(test["trial_id"].astype(str))
                    observed_y.extend(y_test.tolist())
                    observed_p.extend(probabilities.tolist())

            if len(observed_ids) != len(set(observed_ids)):
                raise ValueError("Duplicate primary trial in observed null audit")

            observed_ba = float(
                balanced_accuracy_score(
                    np.asarray(observed_y, dtype=int),
                    (np.asarray(observed_p) >= 0.5).astype(int),
                )
            )

            null_values: list[float] = []
            for permutation in range(permutations):
                pooled_y: list[int] = []
                pooled_p: list[float] = []
                pooled_ids: list[str] = []

                for subject_fold in range(4):
                    for stimulus_fold in range(4):
                        masks = masks_for_cell(
                            manifest,
                            subject_assignment,
                            stimulus_assignment,
                            subject_fold,
                            stimulus_fold,
                        )
                        train, y_train = extract_scored(
                            manifest.loc[masks["train"]],
                            label_column,
                        )
                        test, y_test = extract_scored(
                            manifest.loc[masks["primary_test"]],
                            label_column,
                        )
                        rng = np.random.default_rng(
                            deterministic_seed(
                                manifest_hash,
                                "order-null",
                                repetition,
                                task,
                                permutation,
                                subject_fold,
                                stimulus_fold,
                            )
                        )
                        shuffled = shuffle_labels_within_subject(
                            train,
                            y_train,
                            rng,
                        )
                        probabilities = quadratic_order_probabilities(
                            train,
                            shuffled,
                            test,
                        )

                        pooled_ids.extend(test["trial_id"].astype(str))
                        pooled_y.extend(y_test.tolist())
                        pooled_p.extend(probabilities.tolist())

                if len(pooled_ids) != len(set(pooled_ids)):
                    raise ValueError(
                        "Duplicate primary trial in permuted null audit"
                    )
                null_values.append(
                    float(
                        balanced_accuracy_score(
                            np.asarray(pooled_y, dtype=int),
                            (
                                np.asarray(pooled_p) >= 0.5
                            ).astype(int),
                        )
                    )
                )

            null_array = np.asarray(null_values, dtype=float)
            p_value = float(
                (1 + np.sum(null_array >= observed_ba))
                / (permutations + 1)
            )

            rows.append(
                {
                    "repetition": repetition,
                    "role": role,
                    "task": task,
                    "policy": "discard_midpoint",
                    "baseline": "order_quadratic_logistic",
                    "permutations": permutations,
                    "observed_ba": observed_ba,
                    "null_mean": float(null_array.mean()),
                    "null_median": float(np.median(null_array)),
                    "null_std": float(null_array.std(ddof=1)),
                    "null_p05": float(np.quantile(null_array, 0.05)),
                    "null_p95": float(np.quantile(null_array, 0.95)),
                    "effect_over_null_median": float(
                        observed_ba - np.median(null_array)
                    ),
                    "p_value_upper_tail": p_value,
                }
            )

    bh_adjust(rows, "p_value_upper_tail", "fdr_q")
    return rows


def sequence_summary(manifest: pd.DataFrame) -> dict[str, Any]:
    sequences: dict[str, tuple[str, ...]] = {}
    for subject_id, group in manifest.groupby("subject_id"):
        ordered = group.sort_values("presentation_order")
        sequences[str(subject_id)] = tuple(
            ordered["stimulus_id"].astype(str)
        )

    sequence_counts = pd.Series(list(sequences.values())).value_counts()
    pairwise = []
    for subject_a, subject_b in combinations(sorted(sequences), 2):
        sequence_a = sequences[subject_a]
        sequence_b = sequences[subject_b]
        pairwise.append(
            sum(
                value_a == value_b
                for value_a, value_b in zip(sequence_a, sequence_b)
            )
            / 40.0
        )

    unique_positions = (
        manifest.groupby("stimulus_id")["presentation_order"]
        .nunique()
        .astype(int)
    )

    return {
        "subject_count": len(sequences),
        "unique_complete_sequences": int(len(sequence_counts)),
        "largest_identical_sequence_group": int(sequence_counts.iloc[0]),
        "pairwise_same_position_fraction_mean": float(np.mean(pairwise)),
        "pairwise_same_position_fraction_median": float(
            np.median(pairwise)
        ),
        "pairwise_same_position_fraction_max": float(np.max(pairwise)),
        "stimulus_unique_positions_min": int(unique_positions.min()),
        "stimulus_unique_positions_median": float(
            unique_positions.median()
        ),
        "stimulus_unique_positions_max": int(unique_positions.max()),
    }


def run_nmi_null(
    manifest: pd.DataFrame,
    manifest_hash: str,
    permutations: int,
) -> list[dict[str, Any]]:
    stimulus = manifest["stimulus_id"].astype(str).to_numpy()
    exact_order = manifest["presentation_order"].astype(str).to_numpy()
    order_bin = (
        (manifest["presentation_order"].to_numpy(dtype=int) - 1) // 5
    ).astype(str)

    definitions = {
        "exact_position": (
            float(
                normalized_mutual_info_score(
                    stimulus,
                    exact_order,
                )
            ),
            "exact",
        ),
        "five_trial_bin": (
            float(
                normalized_mutual_info_score(
                    stimulus,
                    order_bin,
                )
            ),
            "bin",
        ),
    }

    subject_groups = [
        group.index.to_numpy()
        for _, group in manifest.groupby("subject_id", sort=True)
    ]
    original_orders = manifest["presentation_order"].to_numpy(dtype=int)

    null_distributions = {
        "exact_position": [],
        "five_trial_bin": [],
    }

    for permutation in range(permutations):
        permuted_orders = original_orders.copy()
        rng = np.random.default_rng(
            deterministic_seed(
                manifest_hash,
                "stimulus-order-nmi",
                permutation,
            )
        )
        for indices in subject_groups:
            values = permuted_orders[indices].copy()
            rng.shuffle(values)
            permuted_orders[indices] = values

        permuted_exact = permuted_orders.astype(str)
        permuted_bin = ((permuted_orders - 1) // 5).astype(str)

        null_distributions["exact_position"].append(
            float(
                normalized_mutual_info_score(
                    stimulus,
                    permuted_exact,
                )
            )
        )
        null_distributions["five_trial_bin"].append(
            float(
                normalized_mutual_info_score(
                    stimulus,
                    permuted_bin,
                )
            )
        )

    rows = []
    for definition, (observed, _) in definitions.items():
        null_array = np.asarray(
            null_distributions[definition],
            dtype=float,
        )
        p_value = float(
            (1 + np.sum(null_array >= observed))
            / (permutations + 1)
        )
        rows.append(
            {
                "association": definition,
                "permutations": permutations,
                "observed_nmi": observed,
                "null_mean": float(null_array.mean()),
                "null_median": float(np.median(null_array)),
                "null_std": float(null_array.std(ddof=1)),
                "null_p05": float(np.quantile(null_array, 0.05)),
                "null_p95": float(np.quantile(null_array, 0.95)),
                "effect_over_null_median": float(
                    observed - np.median(null_array)
                ),
                "p_value_upper_tail": p_value,
            }
        )

    bh_adjust(rows, "p_value_upper_tail", "fdr_q")
    return rows


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
        values = []
        for column in columns:
            value = str(row.get(column, ""))
            value = value.replace("|", "\\|").replace("\n", " ")
            values.append(value)
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    if args.order_permutations < 100:
        raise ValueError("--order-permutations must be at least 100")
    if args.nmi_permutations < 100:
        raise ValueError("--nmi-permutations must be at least 100")

    repo = args.repo_root.resolve()
    branch = git(repo, "branch", "--show-current")
    head = git(repo, "rev-parse", "HEAD")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}"
        )

    outputs = prepare_outputs(
        args.docs_dir.resolve(),
        args.overwrite,
    )
    manifest, assignments, protocol, manifest_hash = load_inputs(
        args.manifest.resolve(),
        args.assignments.resolve(),
        args.protocol.resolve(),
    )

    sequence = sequence_summary(manifest)
    cell_rows, summary_rows, _ = run_baselines(
        manifest,
        assignments,
    )
    order_null_rows = run_order_null_tests(
        manifest,
        assignments,
        manifest_hash,
        args.order_permutations,
    )
    nmi_null_rows = run_nmi_null(
        manifest,
        manifest_hash,
        args.nmi_permutations,
    )

    write_csv(outputs["cell_metrics_csv"], cell_rows)
    write_csv(outputs["summary_csv"], summary_rows)
    write_csv(outputs["order_null_csv"], order_null_rows)
    write_csv(outputs["nmi_null_csv"], nmi_null_rows)

    summary_frame = pd.DataFrame(summary_rows)
    primary_main = summary_frame[
        (summary_frame["repetition"] == 0)
        & (summary_frame["role"] == "primary")
        & (summary_frame["policy"] == "discard_midpoint")
        & (summary_frame["region"] == "primary_test")
    ].copy()

    best_legal: dict[str, dict[str, Any]] = {}
    for task in TASKS:
        task_rows = primary_main[primary_main["task"] == task]
        best_row = task_rows.sort_values(
            "balanced_accuracy",
            ascending=False,
        ).iloc[0]
        best_legal[task] = {
            "baseline": str(best_row["baseline"]),
            "balanced_accuracy": float(
                best_row["balanced_accuracy"]
            ),
            "macro_f1": float(best_row["macro_f1"]),
            "roc_auc": float(best_row["roc_auc"]),
        }

    primary_order_null = [
        row for row in order_null_rows
        if row["repetition"] == 0
    ]
    material_order = any(
        row["significant_at_fdr_0_05"]
        and row["effect_over_null_median"] >= 0.05
        for row in primary_order_null
    )

    material_stimulus_order = any(
        row["significant_at_fdr_0_05"]
        and row["effect_over_null_median"] >= 0.05
        for row in nmi_null_rows
    )

    if material_order and material_stimulus_order:
        decision = "ORDER_IS_A_MATERIAL_STIMULUS_COFOUNDER"
    elif material_order:
        decision = "ORDER_IS_A_MATERIAL_NONIDENTITY_SHORTCUT"
    else:
        decision = "NO_MATERIAL_PRIMARY_ORDER_SHORTCUT"

    primary_table_rows = []
    for _, row in summary_frame[
        (summary_frame["repetition"] == 0)
        & (summary_frame["region"] == "primary_test")
    ].sort_values(["task", "policy", "baseline"]).iterrows():
        primary_table_rows.append(
            {
                "task": row["task"],
                "policy": row["policy"],
                "baseline": row["baseline"],
                "n": int(row["n"]),
                "balanced_accuracy": round(
                    float(row["balanced_accuracy"]),
                    4,
                ),
                "macro_f1": round(float(row["macro_f1"]), 4),
                "roc_auc": round(float(row["roc_auc"]), 4),
                "brier": round(float(row["brier"]), 4),
            }
        )

    diagnostic_table_rows = []
    for _, row in summary_frame[
        (summary_frame["repetition"] == 0)
        & (summary_frame["policy"] == "discard_midpoint")
        & (summary_frame["region"] != "primary_test")
    ].sort_values(["task", "region", "baseline"]).iterrows():
        diagnostic_table_rows.append(
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

    order_null_table = []
    for row in order_null_rows:
        order_null_table.append(
            {
                "rep": row["repetition"],
                "role": row["role"],
                "task": row["task"],
                "observed_ba": round(row["observed_ba"], 4),
                "null_median": round(row["null_median"], 4),
                "effect": round(
                    row["effect_over_null_median"],
                    4,
                ),
                "p": round(row["p_value_upper_tail"], 6),
                "q": round(row["fdr_q"], 6),
                "significant": row["significant_at_fdr_0_05"],
            }
        )

    nmi_table = []
    for row in nmi_null_rows:
        nmi_table.append(
            {
                "association": row["association"],
                "observed_nmi": round(row["observed_nmi"], 4),
                "null_median": round(row["null_median"], 4),
                "effect": round(
                    row["effect_over_null_median"],
                    4,
                ),
                "p": round(row["p_value_upper_tail"], 6),
                "q": round(row["fdr_q"], 6),
                "significant": row["significant_at_fdr_0_05"],
            }
        )

    report_payload = {
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "manifest_sha256": manifest_hash,
        "protocol_decision": protocol.get("decision"),
        "training_performed": False,
        "sequence_structure": sequence,
        "best_legal_primary_shortcut_discard_midpoint": best_legal,
        "primary_order_null_tests": primary_order_null,
        "stimulus_order_nmi_null_tests": nmi_null_rows,
        "decision": decision,
        "mandatory_future_model_gates": [
            "Do not provide presentation_order as a physiological-model input.",
            "Report improvement over the best legal primary shortcut baseline.",
            "Report subject-prior and stimulus-prior diagnostics in their legal regions.",
            "Use repetition 0 as primary and repetitions 1-4 only as sensitivity analyses.",
            "Use paired uncertainty respecting crossed subject and stimulus structure.",
        ],
        "output_shapes": {
            "cell_metrics_rows": len(cell_rows),
            "summary_rows": len(summary_rows),
            "order_null_rows": len(order_null_rows),
            "nmi_null_rows": len(nmi_null_rows),
        },
    }
    outputs["report_json"].write_text(
        json.dumps(
            safe_json(report_payload),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    md_lines = [
        "# DEAP 4x4 Leakage-Safe Shortcut and Order Audit",
        "",
        "No EEG/EMG feature or physiological model was trained.",
        "",
        "## Verified Sequence Structure",
        "",
        f"- Unique complete sequences: "
        f"`{sequence['unique_complete_sequences']}` of "
        f"`{sequence['subject_count']}`",
        f"- Largest identical-sequence group: "
        f"`{sequence['largest_identical_sequence_group']}`",
        f"- Mean pairwise same-position fraction: "
        f"`{sequence['pairwise_same_position_fraction_mean']:.4f}`",
        f"- Maximum pairwise same-position fraction: "
        f"`{sequence['pairwise_same_position_fraction_max']:.4f}`",
        f"- Unique positions per stimulus, min/median/max: "
        f"`{sequence['stimulus_unique_positions_min']}/"
        f"{sequence['stimulus_unique_positions_median']:.1f}/"
        f"{sequence['stimulus_unique_positions_max']}`",
        "",
        "## Stimulus–Order Association Against Randomized Sequences",
        "",
        markdown_table(
            nmi_table,
            [
                "association",
                "observed_nmi",
                "null_median",
                "effect",
                "p",
                "q",
                "significant",
            ],
        ),
        "",
        "## Primary Repetition: Legal Strict-Joint Baselines",
        "",
        markdown_table(
            primary_table_rows,
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
        "## Primary Repetition: Diagnostic Identity Priors",
        "",
        "Identity priors are diagnostic only and are not legal in the "
        "primary unseen-subject × unseen-stimulus test.",
        "",
        markdown_table(
            diagnostic_table_rows,
            [
                "task",
                "region",
                "baseline",
                "balanced_accuracy_macro",
                "roc_auc_macro",
            ],
        ),
        "",
        "## Quadratic Order-Only Null Tests",
        "",
        "Train labels were shuffled within each source subject inside every "
        "outer cell. Primary test labels remained untouched.",
        "",
        markdown_table(
            order_null_table,
            [
                "rep",
                "role",
                "task",
                "observed_ba",
                "null_median",
                "effect",
                "p",
                "q",
                "significant",
            ],
        ),
        "",
        "## Decision",
        "",
        f"- Decision: **{decision}**",
        f"- Best legal Valence shortcut under discard-midpoint: "
        f"`{best_legal['valence']['baseline']}`, "
        f"BA=`{best_legal['valence']['balanced_accuracy']:.4f}`",
        f"- Best legal Arousal shortcut under discard-midpoint: "
        f"`{best_legal['arousal']['baseline']}`, "
        f"BA=`{best_legal['arousal']['balanced_accuracy']:.4f}`",
        "",
        "## Mandatory Gates for Future Models",
        "",
        "- Do not provide presentation order as a model input.",
        "- Compare the physiological model with the best legal shortcut, "
        "not only with 0.5 balanced chance.",
        "- Report legal subject-prior and stimulus-prior diagnostics.",
        "- Keep repetitions 1–4 as sensitivity analyses and do not tune on them.",
        "- Use paired uncertainty that respects crossed subjects and stimuli.",
        "",
    ]
    outputs["report_md"].write_text(
        "\n".join(md_lines),
        encoding="utf-8",
    )

    print("DEAP shortcut and order audit completed.")
    print(f"Branch: {branch}")
    print(f"HEAD: {head}")
    print(f"Manifest SHA-256: {manifest_hash}")
    print(f"Cell metric rows: {len(cell_rows)}")
    print(f"Summary rows: {len(summary_rows)}")
    print(f"Order null tests: {len(order_null_rows)}")
    print(f"NMI null tests: {len(nmi_null_rows)}")
    print(f"Decision: {decision}")
    for task in TASKS:
        print(
            f"primary {task}: best={best_legal[task]['baseline']}, "
            f"BA={best_legal[task]['balanced_accuracy']:.4f}"
        )
    print(f"Report: {outputs['report_md']}")


if __name__ == "__main__":
    main()

