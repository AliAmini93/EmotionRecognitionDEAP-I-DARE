#!/usr/bin/env python3
"""Audit presentation-order and stimulus confounding in frozen I-DARE 4x4 CV.

This is a metadata/label audit only. It does not use EEG, EMG, or train a
physiological model.

It quantifies:
- whether subjects received identical or similar stimulus sequences;
- association between stimulus identity and presentation order;
- per-stimulus order concentration;
- label prevalence by order bin;
- leakage-safe quadratic order-only baseline null distributions.

The frozen protocol and manifest are verified by SHA-256 before analysis.
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
from typing import Any, Iterable

import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    balanced_accuracy_score,
    normalized_mutual_info_score,
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

OUTPUTS = {
    "md": "idare_order_stimulus_confound_audit.md",
    "json": "idare_order_stimulus_confound_audit.json",
    "stimulus_csv": "idare_stimulus_order_concentration.csv",
    "order_bin_csv": "idare_order_bin_label_prevalence.csv",
    "null_csv": "idare_order_quadratic_null_tests.csv",
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
        default=250,
        help="Within-source-subject permutations per repetition and task.",
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


def deterministic_seed(
    manifest_hash: str,
    repetition: int,
    task: str,
    permutation: int,
) -> int:
    payload = (
        f"{manifest_hash}|order-quadratic-null|rep={repetition}|"
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
    paths = {
        key: docs_dir / name
        for key, name in OUTPUTS.items()
    }
    if not overwrite:
        existing = [path for path in paths.values() if path.exists()]
        if existing:
            raise FileExistsError(
                "Refusing to overwrite existing outputs:\n"
                + "\n".join(f"- {path}" for path in existing)
            )
    return paths


def load_inputs(
    manifest_path: Path,
    assignments_path: Path,
    protocol_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], str]:
    manifest = pd.read_csv(manifest_path)
    assignments = pd.read_csv(assignments_path)
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))

    required = {
        "trial_id",
        "subject_id",
        "stimulus_id",
        "presentation_order",
        "valence_discard_midpoint",
        "arousal_discard_midpoint",
        "valence_score",
        "arousal_score",
    }
    missing = sorted(required - set(manifest.columns))
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

    if len(manifest) != 2016:
        raise ValueError(f"Expected 2016 rows, found {len(manifest)}")
    if manifest.duplicated(["subject_id", "stimulus_id"]).any():
        raise ValueError("Duplicate subject-stimulus cells")

    assignments = assignments.copy()
    assignments["entity_id"] = assignments["entity_id"].astype(str)
    assignments["repetition"] = assignments["repetition"].astype(int)
    assignments["fold_index_0based"] = (
        assignments["fold_index_0based"].astype(int)
    )

    manifest_hash = sha256_file(manifest_path)
    if protocol.get("manifest_sha256") != manifest_hash:
        raise ValueError("Protocol hash does not match current manifest")
    if set(assignments["manifest_sha256"].astype(str)) != {manifest_hash}:
        raise ValueError("Assignment hash does not match current manifest")

    return manifest, assignments, protocol, manifest_hash


def assignments_for_rep(
    assignments: pd.DataFrame,
    repetition: int,
) -> tuple[dict[str, int], dict[str, int]]:
    subset = assignments[assignments["repetition"] == repetition]
    subject = {
        str(row["entity_id"]): int(row["fold_index_0based"])
        for _, row in subset[subset["axis"] == "subject"].iterrows()
    }
    stimulus = {
        str(row["entity_id"]): int(row["fold_index_0based"])
        for _, row in subset[subset["axis"] == "stimulus"].iterrows()
    }
    if len(subject) != 63 or len(stimulus) != 32:
        raise ValueError(f"Incomplete assignment for repetition {repetition}")
    return subject, stimulus


def sequence_summary(manifest: pd.DataFrame) -> dict[str, Any]:
    sequences: dict[str, tuple[str, ...]] = {}
    for subject_id, group in manifest.groupby("subject_id"):
        ordered = group.sort_values("presentation_order")
        sequence = tuple(ordered["stimulus_id"].astype(str))
        if len(sequence) != 32:
            raise ValueError(f"Subject {subject_id}: sequence length != 32")
        sequences[str(subject_id)] = sequence

    sequence_counts = pd.Series(list(sequences.values())).value_counts()
    pairwise_matches = []
    for subject_a, subject_b in combinations(sorted(sequences), 2):
        seq_a = sequences[subject_a]
        seq_b = sequences[subject_b]
        pairwise_matches.append(
            sum(a == b for a, b in zip(seq_a, seq_b)) / 32.0
        )

    return {
        "subject_count": len(sequences),
        "unique_complete_sequences": int(len(sequence_counts)),
        "largest_identical_sequence_group": int(sequence_counts.iloc[0]),
        "largest_identical_sequence_fraction": float(
            sequence_counts.iloc[0] / len(sequences)
        ),
        "pairwise_same_position_fraction_mean": float(
            np.mean(pairwise_matches)
        ),
        "pairwise_same_position_fraction_median": float(
            np.median(pairwise_matches)
        ),
        "pairwise_same_position_fraction_max": float(
            np.max(pairwise_matches)
        ),
    }


def stimulus_order_concentration(
    manifest: pd.DataFrame,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    max_entropy = math.log(32)

    for stimulus_id, group in manifest.groupby("stimulus_id"):
        counts = (
            group["presentation_order"]
            .value_counts()
            .reindex(range(1, 33), fill_value=0)
            .to_numpy(dtype=float)
        )
        probabilities = counts / counts.sum()
        nonzero = probabilities[probabilities > 0]
        normalized_entropy = (
            float(entropy(nonzero) / max_entropy)
            if len(nonzero)
            else None
        )
        modal_position = int(np.argmax(counts) + 1)
        modal_count = int(counts.max())

        rows.append(
            {
                "stimulus_id": str(stimulus_id),
                "mean_position": float(
                    group["presentation_order"].mean()
                ),
                "std_position": float(
                    group["presentation_order"].std(ddof=1)
                ),
                "min_position": int(
                    group["presentation_order"].min()
                ),
                "max_position": int(
                    group["presentation_order"].max()
                ),
                "unique_positions": int(
                    group["presentation_order"].nunique()
                ),
                "modal_position": modal_position,
                "modal_position_count": modal_count,
                "modal_position_fraction": float(
                    modal_count / len(group)
                ),
                "normalized_order_entropy": normalized_entropy,
            }
        )

    return sorted(rows, key=lambda row: row["stimulus_id"])


def order_bin_prevalence(
    manifest: pd.DataFrame,
) -> list[dict[str, Any]]:
    work = manifest.copy()
    work["order_bin"] = (
        (work["presentation_order"] - 1) // 4 + 1
    ).astype(int)

    rows: list[dict[str, Any]] = []
    for task in ("valence", "arousal"):
        label_column = f"{task}_discard_midpoint"
        for order_bin, group in work.groupby("order_bin"):
            labels = pd.to_numeric(
                group[label_column],
                errors="coerce",
            )
            retained = labels.dropna().astype(int)
            rows.append(
                {
                    "task": task,
                    "order_bin": int(order_bin),
                    "position_start": int((order_bin - 1) * 4 + 1),
                    "position_end": int(order_bin * 4),
                    "rows_total": int(len(group)),
                    "rows_retained": int(len(retained)),
                    "low_count": int((retained == 0).sum()),
                    "high_count": int((retained == 1).sum()),
                    "high_prevalence": float(retained.mean()),
                    "mean_continuous_score": float(
                        group[f"{task}_score"].mean()
                    ),
                }
            )
    return rows


def quadratic_probabilities(
    train_order: pd.Series,
    y_train: np.ndarray,
    test_order: pd.Series,
) -> np.ndarray:
    if len(np.unique(y_train)) < 2:
        return np.full(len(test_order), float(np.mean(y_train)))

    train_x = pd.to_numeric(train_order).to_numpy(dtype=float)
    test_x = pd.to_numeric(test_order).to_numpy(dtype=float)
    train_z = (train_x - 16.5) / 16.0
    test_z = (test_x - 16.5) / 16.0

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


def within_subject_permutation(
    train_frame: pd.DataFrame,
    y_train: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    result = np.asarray(y_train, dtype=int).copy()
    subjects = train_frame["subject_id"].astype(str).to_numpy()
    for subject_id in np.unique(subjects):
        indices = np.flatnonzero(subjects == subject_id)
        values = result[indices].copy()
        rng.shuffle(values)
        result[indices] = values
    return result


def masks_for_cell(
    frame: pd.DataFrame,
    subject_assignment: dict[str, int],
    stimulus_assignment: dict[str, int],
    subject_fold: int,
    stimulus_fold: int,
) -> tuple[np.ndarray, np.ndarray]:
    sf = frame["subject_id"].map(subject_assignment).to_numpy()
    tf = frame["stimulus_id"].map(stimulus_assignment).to_numpy()
    held_subject = sf == subject_fold
    held_stimulus = tf == stimulus_fold
    return (
        (~held_subject) & (~held_stimulus),
        held_subject & held_stimulus,
    )


def observed_quadratic_ba(
    manifest: pd.DataFrame,
    subject_assignment: dict[str, int],
    stimulus_assignment: dict[str, int],
    task: str,
) -> float:
    pooled_y: list[int] = []
    pooled_p: list[float] = []
    pooled_ids: list[str] = []

    label_column = f"{task}_discard_midpoint"

    for subject_fold in range(4):
        for stimulus_fold in range(4):
            train_mask, test_mask = masks_for_cell(
                manifest,
                subject_assignment,
                stimulus_assignment,
                subject_fold,
                stimulus_fold,
            )

            train = manifest.loc[train_mask].copy()
            test = manifest.loc[test_mask].copy()

            train_labels = pd.to_numeric(
                train[label_column], errors="coerce"
            )
            test_labels = pd.to_numeric(
                test[label_column], errors="coerce"
            )

            train = train.loc[train_labels.notna()].copy()
            y_train = train_labels.dropna().astype(int).to_numpy()
            test = test.loc[test_labels.notna()].copy()
            y_test = test_labels.dropna().astype(int).to_numpy()

            probabilities = quadratic_probabilities(
                train["presentation_order"],
                y_train,
                test["presentation_order"],
            )

            pooled_ids.extend(test["trial_id"].astype(str).tolist())
            pooled_y.extend(y_test.tolist())
            pooled_p.extend(probabilities.tolist())

    if len(pooled_ids) != len(set(pooled_ids)):
        raise ValueError("Duplicate primary-test trial in pooled predictions")

    predictions = (np.asarray(pooled_p) >= 0.5).astype(int)
    return float(
        balanced_accuracy_score(
            np.asarray(pooled_y, dtype=int),
            predictions,
        )
    )


def quadratic_null_tests(
    manifest: pd.DataFrame,
    assignments: pd.DataFrame,
    repetitions: list[int],
    manifest_hash: str,
    permutations: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for repetition in repetitions:
        subject_assignment, stimulus_assignment = assignments_for_rep(
            assignments,
            repetition,
        )

        for task in ("valence", "arousal"):
            observed = observed_quadratic_ba(
                manifest,
                subject_assignment,
                stimulus_assignment,
                task,
            )
            label_column = f"{task}_discard_midpoint"
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
                pooled_p: list[float] = []
                pooled_ids: list[str] = []

                for subject_fold in range(4):
                    for stimulus_fold in range(4):
                        train_mask, test_mask = masks_for_cell(
                            manifest,
                            subject_assignment,
                            stimulus_assignment,
                            subject_fold,
                            stimulus_fold,
                        )

                        train = manifest.loc[train_mask].copy()
                        test = manifest.loc[test_mask].copy()

                        train_labels = pd.to_numeric(
                            train[label_column],
                            errors="coerce",
                        )
                        test_labels = pd.to_numeric(
                            test[label_column],
                            errors="coerce",
                        )

                        train = train.loc[train_labels.notna()].copy()
                        y_train = (
                            train_labels.dropna().astype(int).to_numpy()
                        )
                        test = test.loc[test_labels.notna()].copy()
                        y_test = (
                            test_labels.dropna().astype(int).to_numpy()
                        )

                        permuted = within_subject_permutation(
                            train,
                            y_train,
                            rng,
                        )
                        probabilities = quadratic_probabilities(
                            train["presentation_order"],
                            permuted,
                            test["presentation_order"],
                        )

                        pooled_ids.extend(
                            test["trial_id"].astype(str).tolist()
                        )
                        pooled_y.extend(y_test.tolist())
                        pooled_p.extend(probabilities.tolist())

                if len(pooled_ids) != len(set(pooled_ids)):
                    raise ValueError(
                        "Duplicate primary-test trial in null predictions"
                    )

                predictions = (
                    np.asarray(pooled_p) >= 0.5
                ).astype(int)
                null_values.append(
                    float(
                        balanced_accuracy_score(
                            np.asarray(pooled_y, dtype=int),
                            predictions,
                        )
                    )
                )

            null_array = np.asarray(null_values, dtype=float)
            p_value = float(
                (1 + np.sum(null_array >= observed))
                / (permutations + 1)
            )
            rows.append(
                {
                    "repetition": repetition,
                    "role": (
                        "primary"
                        if repetition == 0
                        else "sensitivity"
                    ),
                    "task": task,
                    "baseline": "order_quadratic_logistic",
                    "permutations": permutations,
                    "observed_balanced_accuracy": observed,
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

    p_values = np.asarray(
        [row["p_value_upper_tail"] for row in rows]
    )
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
        row["bh_fdr_q_value"] = float(q_value)
        row["significant_at_fdr_0_05"] = bool(q_value < 0.05)

    return rows


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
    if args.permutations < 100:
        raise ValueError("--permutations must be at least 100")

    repo = args.repo_root.resolve()
    branch = git(repo, "branch", "--show-current")
    head = git(repo, "rev-parse", "HEAD")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}"
        )

    outputs = prepare_outputs(args.docs_dir.resolve(), args.overwrite)
    manifest, assignments, protocol, manifest_hash = load_inputs(
        args.manifest.resolve(),
        args.assignments.resolve(),
        args.protocol.resolve(),
    )

    seq = sequence_summary(manifest)
    stimulus_rows = stimulus_order_concentration(manifest)
    order_rows = order_bin_prevalence(manifest)

    stimulus_nmi_exact_order = float(
        normalized_mutual_info_score(
            manifest["stimulus_id"].astype(str),
            manifest["presentation_order"].astype(str),
        )
    )
    order_bin = (
        (manifest["presentation_order"] - 1) // 4 + 1
    ).astype(str)
    stimulus_nmi_order_bin = float(
        normalized_mutual_info_score(
            manifest["stimulus_id"].astype(str),
            order_bin,
        )
    )

    repetitions = sorted(
        assignments["repetition"].unique().tolist()
    )
    null_rows = quadratic_null_tests(
        manifest,
        assignments,
        repetitions,
        manifest_hash,
        args.permutations,
    )

    write_csv(outputs["stimulus_csv"], stimulus_rows)
    write_csv(outputs["order_bin_csv"], order_rows)
    write_csv(outputs["null_csv"], null_rows)

    stimulus_frame = pd.DataFrame(stimulus_rows)
    primary_null = [
        row for row in null_rows if row["repetition"] == 0
    ]

    material_primary = any(
        row["significant_at_fdr_0_05"]
        and row["effect_over_null_median"] >= 0.05
        for row in primary_null
    )
    concentrated_stimulus_order = bool(
        stimulus_frame["modal_position_fraction"].median() >= 0.25
        or stimulus_nmi_order_bin >= 0.10
    )

    if material_primary and concentrated_stimulus_order:
        decision = "ORDER_IS_A_MATERIAL_STIMULUS_COFOUNDER"
    elif material_primary:
        decision = "ORDER_IS_A_MATERIAL_SHORTCUT"
    else:
        decision = "NO_MATERIAL_PRIMARY_ORDER_EFFECT"

    report = {
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "manifest_sha256": manifest_hash,
        "protocol_repetitions": protocol["repetitions"],
        "sequence_summary": seq,
        "stimulus_order_nmi_exact_position": stimulus_nmi_exact_order,
        "stimulus_order_nmi_4_trial_bin": stimulus_nmi_order_bin,
        "stimulus_order_summary": {
            "median_unique_positions_per_stimulus": float(
                stimulus_frame["unique_positions"].median()
            ),
            "median_modal_position_fraction": float(
                stimulus_frame["modal_position_fraction"].median()
            ),
            "median_normalized_order_entropy": float(
                stimulus_frame["normalized_order_entropy"].median()
            ),
        },
        "quadratic_order_null_tests": null_rows,
        "decision": decision,
        "future_model_requirements": [
            "Do not provide presentation_order as a model input.",
            "Report the order-only quadratic baseline beside every model.",
            "Use order-stratified or order-adjusted uncertainty analysis.",
            "Demonstrate improvement beyond the order-only shortcut.",
        ],
    }
    outputs["json"].write_text(
        json.dumps(safe_json(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    null_table = [
        {
            "rep": row["repetition"],
            "role": row["role"],
            "task": row["task"],
            "observed_ba": round(
                row["observed_balanced_accuracy"], 4
            ),
            "null_median": round(row["null_median"], 4),
            "effect": round(
                row["effect_over_null_median"], 4
            ),
            "p": round(row["p_value_upper_tail"], 6),
            "q": round(row["bh_fdr_q_value"], 6),
            "significant": row["significant_at_fdr_0_05"],
        }
        for row in null_rows
    ]

    order_table = [
        {
            "task": row["task"],
            "order_bin": row["order_bin"],
            "positions": (
                f"{row['position_start']}-{row['position_end']}"
            ),
            "retained": row["rows_retained"],
            "high_prevalence": round(
                row["high_prevalence"], 4
            ),
            "mean_score": round(
                row["mean_continuous_score"], 4
            ),
        }
        for row in order_rows
    ]

    md = [
        "# I-DARE Presentation-Order and Stimulus Confounding Audit",
        "",
        "No EEG/EMG or physiological model was trained.",
        "",
        "## Sequence Structure",
        "",
        f"- Unique complete stimulus sequences: "
        f"`{seq['unique_complete_sequences']}` of "
        f"`{seq['subject_count']}` subjects",
        f"- Largest identical-sequence group: "
        f"`{seq['largest_identical_sequence_group']}`",
        f"- Mean pairwise same-position fraction: "
        f"`{seq['pairwise_same_position_fraction_mean']:.4f}`",
        f"- Maximum pairwise same-position fraction: "
        f"`{seq['pairwise_same_position_fraction_max']:.4f}`",
        "",
        "## Stimulus–Order Association",
        "",
        f"- NMI(stimulus, exact presentation position): "
        f"`{stimulus_nmi_exact_order:.4f}`",
        f"- NMI(stimulus, 4-trial order bin): "
        f"`{stimulus_nmi_order_bin:.4f}`",
        f"- Median unique positions per stimulus: "
        f"`{stimulus_frame['unique_positions'].median():.1f}`",
        f"- Median modal-position fraction: "
        f"`{stimulus_frame['modal_position_fraction'].median():.4f}`",
        f"- Median normalized order entropy: "
        f"`{stimulus_frame['normalized_order_entropy'].median():.4f}`",
        "",
        "## Label Prevalence by Order Bin",
        "",
        markdown_table(
            order_table,
            [
                "task",
                "order_bin",
                "positions",
                "retained",
                "high_prevalence",
                "mean_score",
            ],
        ),
        "",
        "## Quadratic Order-Only Null Tests",
        "",
        "Train labels are permuted within source subject inside every "
        "outer cell. Primary test labels remain untouched.",
        "",
        markdown_table(
            null_table,
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
        "",
        "## Consequences for Future Models",
        "",
        "- Do not provide presentation order as an input feature.",
        "- Treat order-only quadratic performance as a mandatory legal "
        "shortcut baseline.",
        "- Report order-stratified or order-adjusted uncertainty.",
        "- A physiological model must improve beyond this shortcut, not "
        "merely beyond 0.5 balanced accuracy.",
        "",
    ]
    outputs["md"].write_text("\n".join(md), encoding="utf-8")

    print("I-DARE order/stimulus confounding audit completed.")
    print(f"Branch: {branch}")
    print(f"HEAD: {head}")
    print(
        f"Unique complete sequences: "
        f"{seq['unique_complete_sequences']}"
    )
    print(
        f"Stimulus-order NMI exact/bin: "
        f"{stimulus_nmi_exact_order:.4f}/"
        f"{stimulus_nmi_order_bin:.4f}"
    )
    for row in primary_null:
        print(
            f"primary {row['task']}: "
            f"observed={row['observed_balanced_accuracy']:.4f}, "
            f"null_median={row['null_median']:.4f}, "
            f"effect={row['effect_over_null_median']:.4f}, "
            f"q={row['bh_fdr_q_value']:.6f}"
        )
    print(f"Decision: {decision}")
    print(f"Report: {outputs['md']}")


if __name__ == "__main__":
    main()

