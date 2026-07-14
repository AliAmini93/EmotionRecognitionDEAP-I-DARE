#!/usr/bin/env python3
"""Audit robustness of I-DARE Strict Joint CV partition capacity.

This audit compares the current deterministic label-support-balanced 4x4 and
5x5 assignments against many label-blind random partitions with identical fold
sizes. It answers whether the apparent capacity depends on a specially balanced
partition.

No model training is performed. No existing fold files are modified.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE")
MANIFEST = REPO / "docs" / "joint_cv" / "idare_trial_manifest.csv"
DOCS = REPO / "docs" / "joint_cv"
FOLDS = REPO / "folds"
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

OUTPUT_NAMES = {
    "md": "idare_joint_cv_partition_robustness.md",
    "json": "idare_joint_cv_partition_robustness.json",
    "trials_csv": "idare_joint_cv_random_partition_trials.csv",
    "summary_csv": "idare_joint_cv_partition_robustness_summary.csv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--docs-dir", type=Path, default=DOCS)
    parser.add_argument("--folds-dir", type=Path, default=FOLDS)
    parser.add_argument(
        "--random-partitions",
        type=int,
        default=1000,
        help="Number of label-blind random partitions per scheme.",
    )
    parser.add_argument(
        "--base-seed",
        type=int,
        default=260713,
        help="Fixed audit seed; not selected from results.",
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


def fold_capacities(n: int, k: int) -> list[int]:
    base = n // k
    remainder = n % k
    return [base + (1 if i < remainder else 0) for i in range(k)]


def random_assignment(
    entities: list[str],
    k: int,
    rng: np.random.Generator,
) -> dict[str, int]:
    shuffled = list(entities)
    rng.shuffle(shuffled)
    capacities = fold_capacities(len(shuffled), k)

    assignment: dict[str, int] = {}
    cursor = 0
    for fold, capacity in enumerate(capacities):
        for entity in shuffled[cursor:cursor + capacity]:
            assignment[entity] = fold
        cursor += capacity

    if cursor != len(shuffled):
        raise RuntimeError("Assignment cursor mismatch")
    return assignment


def load_current_assignment(
    path: Path,
    expected_axis: str,
) -> dict[str, int]:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)

    required = {
        "axis",
        "entity_id",
        "fold_index_0based",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")

    if set(df["axis"].astype(str)) != {expected_axis}:
        raise ValueError(
            f"{path}: expected only axis={expected_axis!r}"
        )

    assignment = {
        str(row["entity_id"]): int(row["fold_index_0based"])
        for _, row in df.iterrows()
    }
    if len(assignment) != len(df):
        raise ValueError(f"{path}: duplicated entity_id")
    return assignment


def load_manifest(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_csv(path)

    required = {
        "subject_id",
        "stimulus_id",
        "valence_discard_midpoint",
        "valence_midpoint_as_low",
        "valence_midpoint_as_high",
        "arousal_discard_midpoint",
        "arousal_midpoint_as_low",
        "arousal_midpoint_as_high",
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
    if df.duplicated(["subject_id", "stimulus_id"]).any():
        raise ValueError("Duplicate subject-stimulus cells")

    return df


def evaluate_partition(
    df: pd.DataFrame,
    scheme: str,
    subject_assignment: dict[str, int],
    stimulus_assignment: dict[str, int],
    k_subject: int,
    k_stimulus: int,
) -> dict[str, Any]:
    subject_fold = df["subject_id"].map(subject_assignment)
    stimulus_fold = df["stimulus_id"].map(stimulus_assignment)

    if subject_fold.isna().any() or stimulus_fold.isna().any():
        raise ValueError(f"{scheme}: incomplete assignment")

    min_test_class = None
    min_train_class = None
    min_test_retained = None
    max_midpoint_removed_fraction = 0.0
    single_class_test_cells = 0
    single_class_train_cells = 0
    test_rows_before_policy: list[int] = []

    task_policy_details: dict[str, Any] = {}

    for task in TASKS:
        task_policy_details[task] = {}
        for policy in POLICIES:
            column = f"{task}_{policy}"
            labels = pd.to_numeric(df[column], errors="coerce")
            retained = labels.notna()

            policy_min_test_class = None
            policy_min_train_class = None
            policy_min_test_retained = None
            policy_max_removed = 0.0
            policy_single_test = 0
            policy_single_train = 0

            for subject_fold_index in range(k_subject):
                held_subject = subject_fold == subject_fold_index

                for stimulus_fold_index in range(k_stimulus):
                    held_stimulus = stimulus_fold == stimulus_fold_index

                    test_mask = held_subject & held_stimulus
                    train_mask = (~held_subject) & (~held_stimulus)

                    test_rows_before_policy.append(int(test_mask.sum()))

                    test_values = (
                        labels[test_mask & retained]
                        .astype(int)
                        .to_numpy()
                    )
                    train_values = (
                        labels[train_mask & retained]
                        .astype(int)
                        .to_numpy()
                    )

                    test_low = int((test_values == 0).sum())
                    test_high = int((test_values == 1).sum())
                    train_low = int((train_values == 0).sum())
                    train_high = int((train_values == 1).sum())

                    test_class_min = min(test_low, test_high)
                    train_class_min = min(train_low, train_high)

                    if len(np.unique(test_values)) < 2:
                        single_class_test_cells += 1
                        policy_single_test += 1
                    if len(np.unique(train_values)) < 2:
                        single_class_train_cells += 1
                        policy_single_train += 1

                    removed_fraction = (
                        (int(test_mask.sum()) - len(test_values))
                        / int(test_mask.sum())
                        if int(test_mask.sum())
                        else 0.0
                    )

                    min_test_class = (
                        test_class_min
                        if min_test_class is None
                        else min(min_test_class, test_class_min)
                    )
                    min_train_class = (
                        train_class_min
                        if min_train_class is None
                        else min(min_train_class, train_class_min)
                    )
                    min_test_retained = (
                        len(test_values)
                        if min_test_retained is None
                        else min(min_test_retained, len(test_values))
                    )
                    max_midpoint_removed_fraction = max(
                        max_midpoint_removed_fraction,
                        removed_fraction,
                    )

                    policy_min_test_class = (
                        test_class_min
                        if policy_min_test_class is None
                        else min(policy_min_test_class, test_class_min)
                    )
                    policy_min_train_class = (
                        train_class_min
                        if policy_min_train_class is None
                        else min(policy_min_train_class, train_class_min)
                    )
                    policy_min_test_retained = (
                        len(test_values)
                        if policy_min_test_retained is None
                        else min(
                            policy_min_test_retained,
                            len(test_values),
                        )
                    )
                    policy_max_removed = max(
                        policy_max_removed,
                        removed_fraction,
                    )

            task_policy_details[task][policy] = {
                "min_test_class_support": policy_min_test_class,
                "min_train_class_support": policy_min_train_class,
                "min_test_retained": policy_min_test_retained,
                "max_midpoint_removed_fraction": policy_max_removed,
                "single_class_test_cells": policy_single_test,
                "single_class_train_cells": policy_single_train,
            }

    held_subject_sizes = [
        sum(fold == i for fold in subject_assignment.values())
        for i in range(k_subject)
    ]
    held_stimulus_sizes = [
        sum(fold == i for fold in stimulus_assignment.values())
        for i in range(k_stimulus)
    ]

    strong_pass = bool(
        single_class_test_cells == 0
        and single_class_train_cells == 0
        and min_test_class is not None
        and min_test_class >= 10
        and min_train_class is not None
        and min_train_class >= 10
        and min(held_subject_sizes) >= 10
        and min(held_stimulus_sizes) >= 5
    )

    minimal_pass = bool(
        single_class_test_cells == 0
        and single_class_train_cells == 0
        and min_test_class is not None
        and min_test_class >= 5
    )

    return {
        "scheme": scheme,
        "min_test_class_support": int(min_test_class),
        "min_train_class_support": int(min_train_class),
        "min_test_retained": int(min_test_retained),
        "max_midpoint_removed_fraction": float(
            max_midpoint_removed_fraction
        ),
        "single_class_test_cells": int(single_class_test_cells),
        "single_class_train_cells": int(single_class_train_cells),
        "min_held_subjects": int(min(held_subject_sizes)),
        "max_held_subjects": int(max(held_subject_sizes)),
        "min_held_stimuli": int(min(held_stimulus_sizes)),
        "max_held_stimuli": int(max(held_stimulus_sizes)),
        "min_test_rows_before_policy": int(
            min(test_rows_before_policy)
        ),
        "max_test_rows_before_policy": int(
            max(test_rows_before_policy)
        ),
        "strong_capacity_pass": strong_pass,
        "minimal_capacity_pass": minimal_pass,
        "task_policy": task_policy_details,
    }


def percentile_leq(
    random_values: pd.Series,
    current_value: float,
) -> float:
    return float((random_values <= current_value).mean())


def summarize_scheme(
    scheme: str,
    current: dict[str, Any],
    trials: pd.DataFrame,
) -> dict[str, Any]:
    subset = trials[trials["scheme"] == scheme].copy()

    metrics = [
        "min_test_class_support",
        "min_train_class_support",
        "min_test_retained",
        "max_midpoint_removed_fraction",
        "single_class_test_cells",
        "single_class_train_cells",
    ]

    summary: dict[str, Any] = {
        "scheme": scheme,
        "random_partition_count": len(subset),
        "current_assignment": current,
        "random_strong_pass_rate": float(
            subset["strong_capacity_pass"].mean()
        ),
        "random_minimal_pass_rate": float(
            subset["minimal_capacity_pass"].mean()
        ),
    }

    for metric in metrics:
        series = pd.to_numeric(subset[metric], errors="coerce")
        current_value = current[metric]
        summary[f"{metric}_random_min"] = float(series.min())
        summary[f"{metric}_random_p05"] = float(
            series.quantile(0.05)
        )
        summary[f"{metric}_random_median"] = float(
            series.quantile(0.50)
        )
        summary[f"{metric}_random_p95"] = float(
            series.quantile(0.95)
        )
        summary[f"{metric}_random_max"] = float(series.max())
        summary[f"{metric}_current_percentile_leq"] = (
            percentile_leq(series, float(current_value))
        )

    if (
        summary["random_strong_pass_rate"] >= 0.95
        and summary["min_test_class_support_random_p05"] >= 10
    ):
        robustness = "ROBUST_STRONG"
    elif (
        summary["random_minimal_pass_rate"] >= 0.95
        and summary["min_test_class_support_random_p05"] >= 5
    ):
        robustness = "ROBUST_MINIMAL"
    else:
        robustness = "PARTITION_SENSITIVE"

    current_percentile = summary[
        "min_test_class_support_current_percentile_leq"
    ]
    if current_percentile > 0.99:
        balance_note = (
            "Current split is more label-balanced than over 99% of "
            "label-blind random partitions."
        )
    elif current_percentile > 0.95:
        balance_note = (
            "Current split is unusually label-balanced relative to "
            "label-blind random partitions."
        )
    else:
        balance_note = (
            "Current split is not an extreme outlier in minimum "
            "test-class support."
        )

    summary["robustness_verdict"] = robustness
    summary["balance_extremeness_note"] = balance_note
    return summary


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
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

    if args.random_partitions < 100:
        raise ValueError(
            "--random-partitions must be at least 100"
        )

    outputs = prepare_outputs(docs_dir, args.overwrite)
    df = load_manifest(manifest_path)

    subjects = sorted(df["subject_id"].unique().tolist())
    stimuli = sorted(df["stimulus_id"].unique().tolist())

    current_results: dict[str, Any] = {}
    random_rows: list[dict[str, Any]] = []

    for scheme_index, (
        scheme,
        (k_subject, k_stimulus),
    ) in enumerate(SCHEMES.items()):
        subject_path = (
            folds_dir / f"{scheme}_subject_folds.csv"
        )
        stimulus_path = (
            folds_dir / f"{scheme}_stimulus_folds.csv"
        )

        current_subject_assignment = load_current_assignment(
            subject_path,
            "subject",
        )
        current_stimulus_assignment = load_current_assignment(
            stimulus_path,
            "stimulus",
        )

        current_results[scheme] = evaluate_partition(
            df,
            scheme,
            current_subject_assignment,
            current_stimulus_assignment,
            k_subject,
            k_stimulus,
        )

        for trial_index in range(args.random_partitions):
            seed = (
                args.base_seed
                + scheme_index * 1_000_003
                + trial_index
            )
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
                df,
                scheme,
                subject_assignment,
                stimulus_assignment,
                k_subject,
                k_stimulus,
            )

            random_rows.append(
                {
                    "scheme": scheme,
                    "trial_index": trial_index,
                    "seed": seed,
                    "min_test_class_support": result[
                        "min_test_class_support"
                    ],
                    "min_train_class_support": result[
                        "min_train_class_support"
                    ],
                    "min_test_retained": result[
                        "min_test_retained"
                    ],
                    "max_midpoint_removed_fraction": result[
                        "max_midpoint_removed_fraction"
                    ],
                    "single_class_test_cells": result[
                        "single_class_test_cells"
                    ],
                    "single_class_train_cells": result[
                        "single_class_train_cells"
                    ],
                    "min_held_subjects": result[
                        "min_held_subjects"
                    ],
                    "max_held_subjects": result[
                        "max_held_subjects"
                    ],
                    "min_held_stimuli": result[
                        "min_held_stimuli"
                    ],
                    "max_held_stimuli": result[
                        "max_held_stimuli"
                    ],
                    "strong_capacity_pass": result[
                        "strong_capacity_pass"
                    ],
                    "minimal_capacity_pass": result[
                        "minimal_capacity_pass"
                    ],
                }
            )

    trials = pd.DataFrame(random_rows)
    trials.to_csv(outputs["trials_csv"], index=False)

    summaries = [
        summarize_scheme(
            scheme,
            current_results[scheme],
            trials,
        )
        for scheme in SCHEMES
    ]

    summary_rows = []
    for item in summaries:
        summary_rows.append(
            {
                "scheme": item["scheme"],
                "random_partitions": item[
                    "random_partition_count"
                ],
                "current_min_test_class": item[
                    "current_assignment"
                ]["min_test_class_support"],
                "random_min_test_class_p05": round(
                    item[
                        "min_test_class_support_random_p05"
                    ],
                    3,
                ),
                "random_min_test_class_median": round(
                    item[
                        "min_test_class_support_random_median"
                    ],
                    3,
                ),
                "random_min_test_class_p95": round(
                    item[
                        "min_test_class_support_random_p95"
                    ],
                    3,
                ),
                "current_min_test_class_percentile": round(
                    item[
                        "min_test_class_support_"
                        "current_percentile_leq"
                    ],
                    4,
                ),
                "random_strong_pass_rate": round(
                    item["random_strong_pass_rate"],
                    4,
                ),
                "random_minimal_pass_rate": round(
                    item["random_minimal_pass_rate"],
                    4,
                ),
                "robustness_verdict": item[
                    "robustness_verdict"
                ],
                "balance_note": item[
                    "balance_extremeness_note"
                ],
            }
        )

    write_csv(outputs["summary_csv"], summary_rows)

    robust_5x5 = next(
        item for item in summaries
        if item["scheme"] == "idare_5x5"
    )
    robust_4x4 = next(
        item for item in summaries
        if item["scheme"] == "idare_4x4"
    )

    if robust_5x5["robustness_verdict"] == "ROBUST_STRONG":
        recommendation = "LOCK_5X5_AFTER_FINAL_BASELINE_AUDITS"
        reason = (
            "5x5 retains strong capacity across label-blind random "
            "partitions; the current result is not dependent on one "
            "specially optimized partition."
        )
    elif robust_4x4["robustness_verdict"] == "ROBUST_STRONG":
        recommendation = "PREFER_4X4_FOR_CAPACITY_STABILITY"
        reason = (
            "5x5 is partition-sensitive, while 4x4 remains strongly "
            "robust across label-blind random partitions."
        )
    else:
        recommendation = "DO_NOT_LOCK_STRICT_JOINT_SCHEME"
        reason = (
            "Neither candidate demonstrates strong partition-robust "
            "capacity."
        )

    report = {
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "manifest": str(manifest_path),
        "random_partitions_per_scheme": args.random_partitions,
        "base_seed": args.base_seed,
        "current_fold_construction_used_label_support": True,
        "random_reference_partitions_are_label_blind": True,
        "summaries": summaries,
        "recommendation": recommendation,
        "recommendation_reason": reason,
        "interpretation": (
            "Label-based stratification may be defensible for a frozen "
            "benchmark split, but robustness to label-blind partitions "
            "must be reported to avoid a cherry-picked-capacity concern."
        ),
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
        "# I-DARE Joint-CV Partition Robustness Audit",
        "",
        "No model training was performed.",
        "",
        "## Why This Audit Was Necessary",
        "",
        "The current candidate folds were constructed using label-support "
        "profiles. Stratification can be acceptable for a benchmark, but "
        "the apparent feasibility must not depend on a specially balanced "
        "partition. Therefore the same capacity gates were evaluated over "
        f"`{args.random_partitions}` label-blind random partitions for "
        "each scheme, with identical fold sizes.",
        "",
        "## Summary",
        "",
        markdown_table(
            summary_rows,
            [
                "scheme",
                "random_partitions",
                "current_min_test_class",
                "random_min_test_class_p05",
                "random_min_test_class_median",
                "random_min_test_class_p95",
                "current_min_test_class_percentile",
                "random_strong_pass_rate",
                "random_minimal_pass_rate",
                "robustness_verdict",
            ],
        ),
        "",
        "## Balance Extremeness",
        "",
    ]

    for row in summary_rows:
        md_lines.append(
            f"- `{row['scheme']}`: {row['balance_note']}"
        )

    md_lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Recommendation: **{recommendation}**",
            f"- Reason: {reason}",
            "",
            "## Interpretation Boundary",
            "",
            "- This audit addresses partition-capacity robustness only.",
            "- It does not establish model performance.",
            "- It does not replace shortcut baselines, permutation/null "
            "tests, donor-support audits, or TTA stream audits.",
            "- If a label-balanced benchmark split is retained, it must "
            "be frozen before training and its construction must be "
            "reported transparently.",
            "",
        ]
    )

    outputs["md"].write_text(
        "\n".join(md_lines),
        encoding="utf-8",
    )

    print("I-DARE Joint-CV partition robustness audit completed.")
    print(f"Branch: {branch}")
    print(f"HEAD: {head}")
    print(
        f"Random partitions per scheme: "
        f"{args.random_partitions}"
    )
    for item in summaries:
        print(
            f"{item['scheme']}: "
            f"strong_pass_rate="
            f"{item['random_strong_pass_rate']:.4f}, "
            f"min_test_class_p05="
            f"{item['min_test_class_support_random_p05']:.2f}, "
            f"current_percentile="
            f"{item['min_test_class_support_current_percentile_leq']:.4f}, "
            f"verdict={item['robustness_verdict']}"
        )
    print(f"Recommendation: {recommendation}")
    print(f"Report: {outputs['md']}")
    print(f"Random trials CSV: {outputs['trials_csv']}")


if __name__ == "__main__":
    main()

