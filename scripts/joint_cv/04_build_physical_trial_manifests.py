#!/usr/bin/env python3
"""Build canonical physical-trial manifests for DEAP and I-DARE.

Scientific scope
----------------
- One row per physical trial, never one row per window/segment.
- DEAP stimulus identity and presentation order remain unresolved unless an
  independently verified official mapping exists. They are therefore left
  blank and explicitly flagged.
- I-DARE stimulus identity and chronology are taken from the verified local
  trial index.
- No model training and no Joint-CV fold construction are performed.
- Datasets and caches are read-only.
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
import subprocess
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE")
DEAP_DIR = Path("/mnt/HDD/AliWorks/DEAP/data_preprocessed_python")
IDARE_INDEX = REPO / ".cache" / "idare_trial_index.csv"
OUT_DIR = REPO / "docs" / "joint_cv"
EXPECTED_BRANCH = "joint-cv-capacity-audit"

REQUIRED_COLUMNS = [
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
    "eeg_path",
    "emg_path",
    "eeg_sampling_rate",
    "emg_sampling_rate",
    "trial_duration_sec",
    "chronology_verified",
    "quality_flag",
]

OUTPUTS = {
    "deap_csv": "deap_trial_manifest.csv",
    "idare_csv": "idare_trial_manifest.csv",
    "deap_md": "deap_trial_manifest_audit.md",
    "idare_md": "idare_trial_manifest_audit.md",
    "deap_json": "deap_trial_manifest_audit.json",
    "idare_json": "idare_trial_manifest_audit.json",
    "decision_md": "phase2_manifest_decision.md",
    "decision_json": "phase2_manifest_decision.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO)
    parser.add_argument("--deap-dir", type=Path, default=DEAP_DIR)
    parser.add_argument("--idare-index", type=Path, default=IDARE_INDEX)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite only this script's output files if they already exist.",
    )
    return parser.parse_args()


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed:\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def safe_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): safe_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
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


def prepare_output_paths(out_dir: Path, overwrite: bool) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: out_dir / name for key, name in OUTPUTS.items()}
    if not overwrite:
        existing = [path for path in paths.values() if path.exists()]
        if existing:
            raise FileExistsError(
                "Refusing to overwrite existing outputs. "
                "Use --overwrite only after reviewing them:\n"
                + "\n".join(f"- {path}" for path in existing)
            )
    return paths


def label_policy_values(score: float) -> tuple[Any, int, int]:
    if np.isclose(score, 5.0):
        discard = pd.NA
    else:
        discard = int(score > 5.0)
    midpoint_low = int(score > 5.0)
    midpoint_high = int(score >= 5.0)
    return discard, midpoint_low, midpoint_high


def load_deap_pickle(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"dtype\(\): align should be passed",
            )
            return pickle.load(handle, encoding="latin1")


def build_deap_manifest(deap_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    subject_files = sorted(deap_dir.glob("s??.dat"))

    if len(subject_files) != 32:
        raise ValueError(
            f"Expected 32 DEAP subject files, found {len(subject_files)}"
        )

    for path in subject_files:
        subject_id = int(path.stem[1:])
        obj = load_deap_pickle(path)

        data = np.asarray(obj.get("data"))
        labels = np.asarray(obj.get("labels"), dtype=float)

        if data.shape != (40, 40, 8064):
            raise ValueError(
                f"{path.name}: expected data shape (40, 40, 8064), "
                f"found {data.shape}"
            )
        if labels.shape != (40, 4):
            raise ValueError(
                f"{path.name}: expected labels shape (40, 4), "
                f"found {labels.shape}"
            )

        for trial_index_0based in range(40):
            valence = float(labels[trial_index_0based, 0])
            arousal = float(labels[trial_index_0based, 1])

            v_discard, v_low, v_high = label_policy_values(valence)
            a_discard, a_low, a_high = label_policy_values(arousal)

            source_trial_1based = trial_index_0based + 1
            rows.append(
                {
                    "dataset": "DEAP",
                    "subject_id": f"s{subject_id:02d}",
                    "session_id": "session_1",
                    "trial_id": (
                        f"deap_s{subject_id:02d}_row{source_trial_1based:02d}"
                    ),
                    "stimulus_id": pd.NA,
                    "presentation_order": pd.NA,
                    "valence_score": valence,
                    "arousal_score": arousal,
                    "valence_discard_midpoint": v_discard,
                    "valence_midpoint_as_low": v_low,
                    "valence_midpoint_as_high": v_high,
                    "arousal_discard_midpoint": a_discard,
                    "arousal_midpoint_as_low": a_low,
                    "arousal_midpoint_as_high": a_high,
                    "eeg_available": True,
                    "emg_available": True,
                    "eeg_path": str(path),
                    "emg_path": str(path),
                    "eeg_sampling_rate": 128.0,
                    "emg_sampling_rate": 128.0,
                    "trial_duration_sec": 60.0,
                    "chronology_verified": False,
                    "quality_flag": (
                        "stimulus_identity_unresolved;"
                        "presentation_order_unverified"
                    ),
                    "source_file": str(path),
                    "source_trial_index_0based": trial_index_0based,
                    "source_trial_index_1based": source_trial_1based,
                    "recorded_duration_sec": 63.0,
                    "baseline_duration_sec": 3.0,
                    "stimulus_duration_sec": 60.0,
                    "eeg_channel_indices_0based": "0-31",
                    "emg_channel_indices_0based": "34-35",
                    "stimulus_identity_verified": False,
                }
            )

    frame = pd.DataFrame(rows)
    return frame[REQUIRED_COLUMNS + [
        "source_file",
        "source_trial_index_0based",
        "source_trial_index_1based",
        "recorded_duration_sec",
        "baseline_duration_sec",
        "stimulus_duration_sec",
        "eeg_channel_indices_0based",
        "emg_channel_indices_0based",
        "stimulus_identity_verified",
    ]]


def build_idare_manifest(index_path: Path) -> pd.DataFrame:
    source = pd.read_csv(index_path)

    required = {
        "subject_id",
        "stimulus_id",
        "event_index_0based",
        "valence_score",
        "arousal_score",
        "eeg_file",
        "emg_file",
        "eeg_fs",
        "emg_fs",
        "eeg_duration_sec",
        "emg_duration_sec",
    }
    missing = sorted(required - set(source.columns))
    if missing:
        raise ValueError(f"I-DARE trial index missing columns: {missing}")

    source = source.copy()
    source["subject_id"] = source["subject_id"].astype(str)
    source["stimulus_id"] = source["stimulus_id"].astype(str)
    source["event_index_0based"] = pd.to_numeric(
        source["event_index_0based"], errors="raise"
    ).astype(int)

    order_map: dict[tuple[str, int], int] = {}
    for subject_id, group in source.groupby("subject_id", sort=True):
        ordered = group.sort_values(
            ["event_index_0based", "stimulus_id"],
            kind="stable",
        )
        if ordered["event_index_0based"].duplicated().any():
            raise ValueError(
                f"I-DARE subject {subject_id}: duplicate event indices"
            )
        for presentation_order, (_, row) in enumerate(
            ordered.iterrows(),
            start=1,
        ):
            order_map[
                (subject_id, int(row["event_index_0based"]))
            ] = presentation_order

    rows: list[dict[str, Any]] = []
    for _, row in source.iterrows():
        subject_id = str(row["subject_id"])
        stimulus_id = str(row["stimulus_id"])
        event_index = int(row["event_index_0based"])

        valence = float(row["valence_score"])
        arousal = float(row["arousal_score"])
        v_discard, v_low, v_high = label_policy_values(valence)
        a_discard, a_low, a_high = label_policy_values(arousal)

        eeg_path = Path(str(row["eeg_file"]))
        emg_path = Path(str(row["emg_file"]))

        eeg_available = eeg_path.exists()
        emg_available = emg_path.exists()

        flags: list[str] = []
        if not eeg_available:
            flags.append("missing_eeg")
        if not emg_available:
            flags.append("missing_emg")
        if not flags:
            flags.append("ok")

        presentation_order = order_map[(subject_id, event_index)]
        eeg_duration = float(row["eeg_duration_sec"])
        emg_duration = float(row["emg_duration_sec"])

        rows.append(
            {
                "dataset": "I-DARE",
                "subject_id": subject_id,
                "session_id": "session_1",
                "trial_id": (
                    f"idare_s{subject_id}_stim{stimulus_id}_"
                    f"event{event_index}"
                ),
                "stimulus_id": stimulus_id,
                "presentation_order": presentation_order,
                "valence_score": valence,
                "arousal_score": arousal,
                "valence_discard_midpoint": v_discard,
                "valence_midpoint_as_low": v_low,
                "valence_midpoint_as_high": v_high,
                "arousal_discard_midpoint": a_discard,
                "arousal_midpoint_as_low": a_low,
                "arousal_midpoint_as_high": a_high,
                "eeg_available": eeg_available,
                "emg_available": emg_available,
                "eeg_path": str(eeg_path),
                "emg_path": str(emg_path),
                "eeg_sampling_rate": float(row["eeg_fs"]),
                "emg_sampling_rate": float(row["emg_fs"]),
                "trial_duration_sec": eeg_duration,
                "chronology_verified": True,
                "quality_flag": ";".join(flags),
                "raw_event_name": row.get("raw_event_name", pd.NA),
                "event_index_0based": event_index,
                "event_index_1based": row.get(
                    "event_index_1based",
                    event_index + 1,
                ),
                "metadata_duration_sec": row.get(
                    "metadata_duration_sec",
                    pd.NA,
                ),
                "eeg_duration_sec": eeg_duration,
                "emg_duration_sec": emg_duration,
                "stimulus_identity_verified": True,
                "source_trial_index_path": str(index_path),
            }
        )

    frame = pd.DataFrame(rows)
    return frame[REQUIRED_COLUMNS + [
        "raw_event_name",
        "event_index_0based",
        "event_index_1based",
        "metadata_duration_sec",
        "eeg_duration_sec",
        "emg_duration_sec",
        "stimulus_identity_verified",
        "source_trial_index_path",
    ]]


def policy_counts(frame: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for task in ("valence", "arousal"):
        result[task] = {}
        for policy in (
            "discard_midpoint",
            "midpoint_as_low",
            "midpoint_as_high",
        ):
            column = f"{task}_{policy}"
            values = frame[column]
            result[task][policy] = {
                "low_0": int((values == 0).sum()),
                "high_1": int((values == 1).sum()),
                "discard_or_missing": int(values.isna().sum()),
            }
    return result


def audit_manifest(
    frame: pd.DataFrame,
    dataset: str,
) -> dict[str, Any]:
    subject_counts = frame.groupby("subject_id").size()
    issues: list[str] = []
    warnings_list: list[str] = []

    missing_required_columns = [
        column for column in REQUIRED_COLUMNS if column not in frame.columns
    ]
    if missing_required_columns:
        issues.append(
            f"Missing required columns: {missing_required_columns}"
        )

    duplicate_trial_ids = int(frame["trial_id"].duplicated(keep=False).sum())
    if duplicate_trial_ids:
        issues.append(f"Duplicated trial_id rows: {duplicate_trial_ids}")

    missing_subjects = int(frame["subject_id"].isna().sum())
    if missing_subjects:
        issues.append(f"Missing subject_id rows: {missing_subjects}")

    for score_column in ("valence_score", "arousal_score"):
        scores = pd.to_numeric(frame[score_column], errors="coerce")
        missing_scores = int(scores.isna().sum())
        if missing_scores:
            issues.append(
                f"{score_column}: {missing_scores} missing/non-numeric values"
            )
        if not scores.dropna().between(1.0, 9.0).all():
            issues.append(f"{score_column}: values outside [1, 9]")

    missing_eeg = int((~frame["eeg_available"].astype(bool)).sum())
    missing_emg = int((~frame["emg_available"].astype(bool)).sum())
    if missing_eeg:
        issues.append(f"Missing EEG rows: {missing_eeg}")
    if missing_emg:
        issues.append(f"Missing EMG rows: {missing_emg}")

    stimulus_missing = int(frame["stimulus_id"].isna().sum())
    chronology_unverified = int(
        (~frame["chronology_verified"].astype(bool)).sum()
    )

    if dataset == "DEAP":
        if len(frame) != 1280:
            issues.append(f"Expected 1280 rows, found {len(frame)}")
        if frame["subject_id"].nunique() != 32:
            issues.append(
                f"Expected 32 subjects, found "
                f"{frame['subject_id'].nunique()}"
            )
        if subject_counts.min() != 40 or subject_counts.max() != 40:
            issues.append(
                f"Expected 40 trials per subject, found "
                f"{subject_counts.min()}..{subject_counts.max()}"
            )
        if stimulus_missing != 1280:
            issues.append(
                "DEAP stimulus_id should remain unresolved for all rows "
                "until official mapping is verified"
            )
        if chronology_unverified != 1280:
            issues.append(
                "DEAP chronology should remain unverified for all rows"
            )
        warnings_list.append(
            "DEAP physical-trial manifest is valid for subject-held-out "
            "analyses only; stimulus-held-out and Strict Joint folds remain "
            "blocked."
        )

    if dataset == "I-DARE":
        if len(frame) != 2016:
            issues.append(f"Expected 2016 rows, found {len(frame)}")
        if frame["subject_id"].nunique() != 63:
            issues.append(
                f"Expected 63 subjects, found "
                f"{frame['subject_id'].nunique()}"
            )
        if frame["stimulus_id"].nunique() != 32:
            issues.append(
                f"Expected 32 stimuli, found "
                f"{frame['stimulus_id'].nunique()}"
            )
        if subject_counts.min() != 32 or subject_counts.max() != 32:
            issues.append(
                f"Expected 32 trials per subject, found "
                f"{subject_counts.min()}..{subject_counts.max()}"
            )

        duplicated_cells = int(
            frame.duplicated(
                ["subject_id", "stimulus_id"],
                keep=False,
            ).sum()
        )
        if duplicated_cells:
            issues.append(
                f"Duplicated subject-stimulus cells: {duplicated_cells}"
            )

        order_counts = frame.groupby("subject_id")[
            "presentation_order"
        ].nunique()
        if order_counts.min() != 32 or order_counts.max() != 32:
            issues.append(
                "Presentation order is not a 32-value permutation "
                "within every subject"
            )

        subject_sets = {
            subject_id: frozenset(group["stimulus_id"].astype(str))
            for subject_id, group in frame.groupby("subject_id")
        }
        unique_sets = set(subject_sets.values())
        if len(unique_sets) != 1:
            issues.append(
                "Subjects do not share one common 32-stimulus set"
            )

        if stimulus_missing:
            issues.append(f"Missing stimulus_id rows: {stimulus_missing}")
        if chronology_unverified:
            issues.append(
                f"Unverified chronology rows: {chronology_unverified}"
            )

    return {
        "dataset": dataset,
        "row_count": len(frame),
        "column_count": len(frame.columns),
        "columns": list(frame.columns),
        "subject_count": int(frame["subject_id"].nunique()),
        "stimulus_count_excluding_missing": int(
            frame["stimulus_id"].nunique(dropna=True)
        ),
        "trials_per_subject_min": int(subject_counts.min()),
        "trials_per_subject_max": int(subject_counts.max()),
        "duplicate_trial_id_rows": duplicate_trial_ids,
        "missing_stimulus_id_rows": stimulus_missing,
        "chronology_unverified_rows": chronology_unverified,
        "missing_eeg_rows": missing_eeg,
        "missing_emg_rows": missing_emg,
        "valence_score_min": float(frame["valence_score"].min()),
        "valence_score_max": float(frame["valence_score"].max()),
        "arousal_score_min": float(frame["arousal_score"].min()),
        "arousal_score_max": float(frame["arousal_score"].max()),
        "label_policy_counts": policy_counts(frame),
        "issues": issues,
        "warnings": warnings_list,
        "passed": not issues,
    }


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
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


def write_audit_markdown(
    path: Path,
    audit: dict[str, Any],
    manifest_path: Path,
) -> None:
    dataset = audit["dataset"]
    lines = [
        f"# {dataset} Canonical Physical-Trial Manifest Audit",
        "",
        "No model training or fold construction was performed.",
        "",
        "## Summary",
        "",
        f"- Manifest: `{manifest_path}`",
        f"- Audit passed: `{audit['passed']}`",
        f"- Rows: `{audit['row_count']}`",
        f"- Columns: `{audit['column_count']}`",
        f"- Subjects: `{audit['subject_count']}`",
        f"- Verified/non-missing stimuli: "
        f"`{audit['stimulus_count_excluding_missing']}`",
        f"- Trials per subject: "
        f"`{audit['trials_per_subject_min']}.."
        f"{audit['trials_per_subject_max']}`",
        f"- Duplicate trial IDs: `{audit['duplicate_trial_id_rows']}`",
        f"- Missing stimulus IDs: `{audit['missing_stimulus_id_rows']}`",
        f"- Chronology-unverified rows: "
        f"`{audit['chronology_unverified_rows']}`",
        f"- Missing EEG rows: `{audit['missing_eeg_rows']}`",
        f"- Missing EMG rows: `{audit['missing_emg_rows']}`",
        "",
        "## Label Policy Counts",
        "",
    ]

    count_rows = []
    for task, policies in audit["label_policy_counts"].items():
        for policy, counts in policies.items():
            count_rows.append(
                {
                    "task": task,
                    "policy": policy,
                    **counts,
                }
            )
    lines.append(
        markdown_table(
            count_rows,
            [
                "task",
                "policy",
                "low_0",
                "high_1",
                "discard_or_missing",
            ],
        )
    )

    lines.extend(["", "## Issues", ""])
    if audit["issues"]:
        lines.extend(f"- {item}" for item in audit["issues"])
    else:
        lines.append("- None.")

    lines.extend(["", "## Warnings", ""])
    if audit["warnings"]:
        lines.extend(f"- {item}" for item in audit["warnings"])
    else:
        lines.append("- None.")

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo = args.repo_root.resolve()
    deap_dir = args.deap_dir.resolve()
    idare_index = args.idare_index.resolve()
    out_dir = args.out_dir.resolve()
    output_paths = prepare_output_paths(out_dir, args.overwrite)

    branch = git(repo, "branch", "--show-current")
    head = git(repo, "rev-parse", "HEAD")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}"
        )

    if not deap_dir.exists():
        raise FileNotFoundError(deap_dir)
    if not idare_index.exists():
        raise FileNotFoundError(idare_index)

    deap_manifest = build_deap_manifest(deap_dir)
    idare_manifest = build_idare_manifest(idare_index)

    deap_audit = audit_manifest(deap_manifest, "DEAP")
    idare_audit = audit_manifest(idare_manifest, "I-DARE")

    deap_manifest.to_csv(output_paths["deap_csv"], index=False)
    idare_manifest.to_csv(output_paths["idare_csv"], index=False)

    output_paths["deap_json"].write_text(
        json.dumps(safe_json(deap_audit), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    output_paths["idare_json"].write_text(
        json.dumps(safe_json(idare_audit), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    write_audit_markdown(
        output_paths["deap_md"],
        deap_audit,
        output_paths["deap_csv"],
    )
    write_audit_markdown(
        output_paths["idare_md"],
        idare_audit,
        output_paths["idare_csv"],
    )

    decision = {
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "physical_trial_is_statistical_unit": True,
        "deap": {
            "manifest_built": True,
            "manifest_audit_passed": deap_audit["passed"],
            "row_count": len(deap_manifest),
            "subject_held_out_ready": deap_audit["passed"],
            "stimulus_held_out_ready": False,
            "strict_joint_ready": False,
            "blocking_reason": (
                "Official subject-specific trial-position to common "
                "stimulus identity mapping is unavailable."
            ),
        },
        "idare": {
            "manifest_built": True,
            "manifest_audit_passed": idare_audit["passed"],
            "row_count": len(idare_manifest),
            "subject_held_out_ready": idare_audit["passed"],
            "stimulus_held_out_ready": idare_audit["passed"],
            "strict_joint_ready": idare_audit["passed"],
            "blocking_reason": None,
        },
        "safe_next_step": (
            "Review the two manifests and audits. If accepted, construct "
            "Strict Joint folds for I-DARE only. Keep DEAP Strict Joint "
            "fold construction blocked."
        ),
    }

    output_paths["decision_json"].write_text(
        json.dumps(safe_json(decision), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    decision_lines = [
        "# Phase 2 Manifest Decision",
        "",
        "## Statistical Unit",
        "",
        "One row equals one physical trial. No 5-second window is treated "
        "as an independent trial.",
        "",
        "## DEAP",
        "",
        f"- Manifest rows: `{len(deap_manifest)}`",
        f"- Manifest audit passed: `{deap_audit['passed']}`",
        f"- Subject-held-out analyses ready: `{deap_audit['passed']}`",
        "- Stimulus-held-out analyses ready: `False`",
        "- Strict Joint subject–stimulus CV ready: `False`",
        "- Reason: official subject-specific trial-position to common "
        "stimulus identity mapping is unavailable.",
        "",
        "## I-DARE",
        "",
        f"- Manifest rows: `{len(idare_manifest)}`",
        f"- Manifest audit passed: `{idare_audit['passed']}`",
        f"- Subject-held-out analyses ready: `{idare_audit['passed']}`",
        f"- Stimulus-held-out analyses ready: `{idare_audit['passed']}`",
        f"- Strict Joint subject–stimulus CV ready: "
        f"`{idare_audit['passed']}`",
        "",
        "## Safe Next Step",
        "",
        "Review these manifests and reports. After review, build Strict "
        "Joint folds for I-DARE only. Keep DEAP Strict Joint folds blocked.",
        "",
    ]
    output_paths["decision_md"].write_text(
        "\n".join(decision_lines),
        encoding="utf-8",
    )

    print("Canonical physical-trial manifests completed.")
    print(f"Branch: {branch}")
    print(f"HEAD: {head}")
    print(
        f"DEAP manifest: {len(deap_manifest)} rows, "
        f"audit_passed={deap_audit['passed']}"
    )
    print(
        f"I-DARE manifest: {len(idare_manifest)} rows, "
        f"audit_passed={idare_audit['passed']}"
    )
    print("DEAP Strict Joint ready: False")
    print(f"I-DARE Strict Joint ready: {idare_audit['passed']}")
    print(f"Decision report: {output_paths['decision_md']}")


if __name__ == "__main__":
    main()

