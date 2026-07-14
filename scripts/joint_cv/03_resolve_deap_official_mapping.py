#!/usr/bin/env python3
"""Resolve DEAP trial-position versus stimulus identity using official metadata.

Read-only with respect to datasets, caches, and Git. The script searches for
official DEAP metadata files, inspects the actual project baseline code, and,
when participant_ratings.csv is found, tests which metadata ordering exactly
matches the labels embedded in s01.dat ... s32.dat.

No model training and no Joint-CV fold construction are performed.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import pickle
import re
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


REPO = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE")
DEAP_DIR = Path("/mnt/HDD/AliWorks/DEAP/data_preprocessed_python")
EXPECTED_BRANCH = "joint-cv-capacity-audit"

EXACT_METADATA_NAMES = {
    "participant_ratings.csv",
    "participant_questionnaire.csv",
    "online_ratings.csv",
    "video_list.csv",
}

SEARCH_ROOTS = [
    Path("/mnt/HDD/AliWorks"),
    Path.home() / "Downloads",
    Path.home() / "Documents",
]

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "node_modules",
    ".cache", "Trash", ".Trash-1000",
}

OUTPUT_NAMES = {
    "md": "deap_official_mapping_resolution.md",
    "json": "deap_official_mapping_resolution.json",
    "mapping": "deap_verified_trial_stimulus_mapping.csv",
    "code": "deap_project_code_assignment_evidence.csv",
    "candidates": "deap_official_metadata_candidates.csv",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, default=REPO)
    p.add_argument("--deap-dir", type=Path, default=DEAP_DIR)
    p.add_argument("--out-dir", type=Path, default=None)
    p.add_argument("--overwrite", action="store_true")
    return p.parse_args()


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


def ensure_outputs(out_dir: Path, overwrite: bool) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {key: out_dir / name for key, name in OUTPUT_NAMES.items()}
    if not overwrite:
        existing = [p for p in paths.values() if p.exists()]
        if existing:
            raise FileExistsError(
                "Refusing to overwrite existing outputs:\n"
                + "\n".join(f"- {p}" for p in existing)
            )
    return paths


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
        v = float(value)
        return v if math.isfinite(v) else None
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


def discover_metadata() -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[Path] = set()

    for root in SEARCH_ROOTS:
        if not root.exists():
            continue

        for current, dirs, files in os.walk(root):
            dirs[:] = [
                d for d in dirs
                if d not in EXCLUDED_DIRS and not d.startswith(".")
            ]
            current_path = Path(current)

            for filename in files:
                lower = filename.lower()
                path = current_path / filename

                exact = lower in EXACT_METADATA_NAMES
                archive_candidate = (
                    path.suffix.lower() in {".zip", ".rar", ".7z", ".tar", ".gz"}
                    and "deap" in lower
                    and any(term in lower for term in ("meta", "rating", "data"))
                )

                if not exact and not archive_candidate:
                    continue

                try:
                    resolved = path.resolve()
                except OSError:
                    resolved = path

                if resolved in seen:
                    continue
                seen.add(resolved)

                found.append(
                    {
                        "path": str(path),
                        "filename": filename,
                        "exact_expected_name": exact,
                        "archive_candidate": archive_candidate,
                        "size_bytes": path.stat().st_size,
                        "search_root": str(root),
                    }
                )

    return sorted(found, key=lambda row: row["path"].lower())


def normalize_columns(df: pd.DataFrame) -> dict[str, str]:
    return {
        str(column).strip().lower().replace(" ", "_"): str(column)
        for column in df.columns
    }


def find_column(mapping: dict[str, str], aliases: list[str]) -> str | None:
    for alias in aliases:
        normalized = alias.strip().lower().replace(" ", "_")
        if normalized in mapping:
            return mapping[normalized]
    return None


def load_deap_labels(deap_dir: Path) -> dict[int, np.ndarray]:
    labels: dict[int, np.ndarray] = {}
    files = sorted(deap_dir.glob("s??.dat"))
    for path in files:
        subject_id = int(path.stem[1:])
        with path.open("rb") as handle:
            obj = pickle.load(handle, encoding="latin1")
        arr = np.asarray(obj["labels"], dtype=float)
        if arr.shape != (40, 4):
            raise ValueError(f"{path}: expected labels (40, 4), got {arr.shape}")
        labels[subject_id] = arr
    return labels


def evaluate_alignment(
    ratings: pd.DataFrame,
    labels_by_subject: dict[int, np.ndarray],
    participant_col: str,
    trial_col: str,
    experiment_col: str,
    rating_cols: list[str],
    order_by: str,
) -> dict[str, Any]:
    absolute_errors: list[np.ndarray] = []
    per_subject: list[dict[str, Any]] = []
    mapped_rows: list[dict[str, Any]] = []
    issues: list[str] = []

    for subject_id in sorted(labels_by_subject):
        group = ratings[
            pd.to_numeric(ratings[participant_col], errors="coerce")
            == subject_id
        ].copy()

        if len(group) != 40:
            issues.append(
                f"subject {subject_id}: expected 40 metadata rows, found {len(group)}"
            )
            continue

        group[trial_col] = pd.to_numeric(group[trial_col], errors="coerce")
        group[experiment_col] = pd.to_numeric(
            group[experiment_col], errors="coerce"
        )
        for column in rating_cols:
            group[column] = pd.to_numeric(group[column], errors="coerce")

        sort_col = trial_col if order_by == "trial" else experiment_col
        group = group.sort_values(sort_col, kind="stable").reset_index(drop=True)

        metadata_labels = group[rating_cols].to_numpy(dtype=float)
        embedded_labels = labels_by_subject[subject_id]

        if metadata_labels.shape != embedded_labels.shape:
            issues.append(
                f"subject {subject_id}: metadata label shape "
                f"{metadata_labels.shape} != {embedded_labels.shape}"
            )
            continue

        errors = np.abs(metadata_labels - embedded_labels)
        absolute_errors.append(errors)

        per_subject.append(
            {
                "subject_id": subject_id,
                "order_by": order_by,
                "mean_abs_error": float(errors.mean()),
                "max_abs_error": float(errors.max()),
                "exact_match_fraction_1e-8": float(
                    np.isclose(
                        metadata_labels,
                        embedded_labels,
                        atol=1e-8,
                        rtol=0.0,
                    ).mean()
                ),
            }
        )

        for row_index, row in group.iterrows():
            mapped_rows.append(
                {
                    "subject_id": subject_id,
                    "trial_index_0based_in_dat": int(row_index),
                    "trial_index_1based_in_dat": int(row_index + 1),
                    "metadata_trial": int(row[trial_col]),
                    "stimulus_id_experiment_id": int(row[experiment_col]),
                    "valence_score": float(row[rating_cols[0]]),
                    "arousal_score": float(row[rating_cols[1]]),
                    "dominance_score": float(row[rating_cols[2]]),
                    "liking_score": float(row[rating_cols[3]]),
                    "verified_order_hypothesis": order_by,
                }
            )

    if absolute_errors:
        all_errors = np.concatenate(
            [arr.reshape(-1) for arr in absolute_errors]
        )
        mae = float(all_errors.mean())
        max_error = float(all_errors.max())
        exact_fraction = float(np.isclose(all_errors, 0.0, atol=1e-8).mean())
    else:
        mae = None
        max_error = None
        exact_fraction = None

    return {
        "order_by": order_by,
        "subjects_compared": len(per_subject),
        "mean_abs_error": mae,
        "max_abs_error": max_error,
        "exact_match_fraction_1e-8": exact_fraction,
        "issues": issues,
        "per_subject": per_subject,
        "mapped_rows": mapped_rows,
    }


def inspect_participant_ratings(
    path: Path,
    labels_by_subject: dict[int, np.ndarray],
) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path)}
    try:
        df = pd.read_csv(path)
    except Exception as exc:
        result["read_error"] = repr(exc)
        return result

    columns = normalize_columns(df)
    result["row_count"] = len(df)
    result["columns"] = list(df.columns)

    participant_col = find_column(
        columns,
        ["Participant_id", "participant", "subject_id", "subject"],
    )
    trial_col = find_column(
        columns,
        ["Trial", "trial_id", "trial_index", "presentation_order"],
    )
    experiment_col = find_column(
        columns,
        ["Experiment_id", "experiment", "video_id", "stimulus_id"],
    )

    rating_aliases = {
        "valence": ["Valence", "valence_score"],
        "arousal": ["Arousal", "arousal_score"],
        "dominance": ["Dominance", "dominance_score"],
        "liking": ["Liking", "liking_score"],
    }
    rating_cols: list[str] = []
    missing: list[str] = []

    for name, aliases in rating_aliases.items():
        found = find_column(columns, aliases)
        if found is None:
            missing.append(name)
        else:
            rating_cols.append(found)

    required_missing = []
    if participant_col is None:
        required_missing.append("participant")
    if trial_col is None:
        required_missing.append("trial")
    if experiment_col is None:
        required_missing.append("experiment/stimulus")
    required_missing.extend(missing)

    result["resolved_columns"] = {
        "participant": participant_col,
        "trial": trial_col,
        "experiment": experiment_col,
        "ratings": rating_cols,
    }
    result["missing_required_columns"] = required_missing

    if required_missing:
        return result

    participant_numeric = pd.to_numeric(df[participant_col], errors="coerce")
    trial_numeric = pd.to_numeric(df[trial_col], errors="coerce")
    experiment_numeric = pd.to_numeric(df[experiment_col], errors="coerce")

    result["participant_count"] = int(participant_numeric.nunique())
    result["trial_unique_count"] = int(trial_numeric.nunique())
    result["experiment_unique_count"] = int(experiment_numeric.nunique())
    result["duplicate_participant_trial_rows"] = int(
        df.assign(_participant=participant_numeric, _trial=trial_numeric)
        .duplicated(["_participant", "_trial"], keep=False)
        .sum()
    )
    result["duplicate_participant_experiment_rows"] = int(
        df.assign(
            _participant=participant_numeric,
            _experiment=experiment_numeric,
        )
        .duplicated(["_participant", "_experiment"], keep=False)
        .sum()
    )

    result["trial_order_alignment"] = evaluate_alignment(
        df,
        labels_by_subject,
        participant_col,
        trial_col,
        experiment_col,
        rating_cols,
        order_by="trial",
    )
    result["experiment_order_alignment"] = evaluate_alignment(
        df,
        labels_by_subject,
        participant_col,
        trial_col,
        experiment_col,
        rating_cols,
        order_by="experiment",
    )

    return result


def inspect_project_code(repo: Path) -> list[dict[str, Any]]:
    targets = [
        repo / "scripts" / "roca" / "01_deap_stimulus_only_loso.py",
        repo / "scripts" / "roca" / "01c_prior_baselines_no_global.py",
    ]
    evidence: list[dict[str, Any]] = []

    patterns = [
        ("stimulus_assignment", re.compile(r"\bstimulus_id\b.*=", re.I)),
        ("trial_assignment", re.compile(r"\btrial_id\b.*=", re.I)),
        ("explicit_assumption", re.compile(
            r"trial_id.*stimulus|stimulus.*trial_id", re.I
        )),
        ("enumerated_trial_loop", re.compile(
            r"for\s+.*trial.*enumerate|enumerate\(.*trial", re.I
        )),
    ]

    for path in targets:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()

        for line_number, line in enumerate(lines, start=1):
            for category, pattern in patterns:
                if not pattern.search(line):
                    continue
                start = max(0, line_number - 4)
                end = min(len(lines), line_number + 3)
                excerpt = "\n".join(
                    f"{i + 1}: {lines[i]}" for i in range(start, end)
                )
                evidence.append(
                    {
                        "artifact_path": str(path.relative_to(repo)),
                        "line_number": line_number,
                        "category": category,
                        "line": line.strip(),
                        "excerpt": excerpt,
                    }
                )
    return evidence


def choose_resolution(
    analyses: list[dict[str, Any]],
) -> tuple[str, dict[str, Any] | None, str]:
    valid: list[tuple[str, dict[str, Any], dict[str, Any]]] = []

    for analysis in analyses:
        if analysis.get("missing_required_columns") or analysis.get("read_error"):
            continue

        for key in ("trial_order_alignment", "experiment_order_alignment"):
            alignment = analysis.get(key, {})
            if (
                alignment.get("subjects_compared") == 32
                and alignment.get("max_abs_error") is not None
                and alignment["max_abs_error"] <= 1e-8
            ):
                valid.append((key, analysis, alignment))

    if len(valid) == 1:
        key, analysis, alignment = valid[0]
        if key == "trial_order_alignment":
            return (
                "VERIFIED_DAT_ROWS_FOLLOW_PRESENTATION_TRIAL_ORDER",
                {
                    "participant_ratings_path": analysis["path"],
                    "alignment_key": key,
                    "mapped_rows": alignment["mapped_rows"],
                },
                (
                    "Embedded .dat labels exactly match participant_ratings rows "
                    "sorted by Trial. Therefore each subject's .dat row is a "
                    "presentation-order trial, and Experiment_id must be used as "
                    "the common stimulus identity."
                ),
            )
        return (
            "VERIFIED_DAT_ROWS_FOLLOW_COMMON_EXPERIMENT_ID_ORDER",
            {
                "participant_ratings_path": analysis["path"],
                "alignment_key": key,
                "mapped_rows": alignment["mapped_rows"],
            },
            (
                "Embedded .dat labels exactly match participant_ratings rows "
                "sorted by Experiment_id. Therefore .dat row position is already "
                "aligned to common stimulus identity."
            ),
        )

    if len(valid) > 1:
        return (
            "AMBIGUOUS_BOTH_ORDERINGS_MATCH",
            None,
            (
                "Both Trial and Experiment_id orderings exactly match. This can "
                "occur only if their order is identical; inspect the mapping "
                "before declaring chronology."
            ),
        )

    if analyses:
        return (
            "METADATA_FOUND_BUT_NOT_VERIFIED_AGAINST_DAT_LABELS",
            None,
            (
                "participant_ratings.csv candidate(s) were found, but no ordering "
                "matched all embedded .dat labels exactly."
            ),
        )

    return (
        "OFFICIAL_PARTICIPANT_RATINGS_NOT_FOUND",
        None,
        (
            "No participant_ratings.csv was found in the searched local roots. "
            "DEAP common stimulus identity remains unresolved."
        ),
    )


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
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def md_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    output = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        values = []
        for col in columns:
            value = str(row.get(col, ""))
            value = value.replace("|", "\\|").replace("\n", "<br>")
            values.append(value)
        output.append("| " + " | ".join(values) + " |")
    return "\n".join(output)


def main() -> None:
    args = parse_args()
    repo = args.repo_root.resolve()
    deap_dir = args.deap_dir.resolve()
    out_dir = (args.out_dir or repo / "docs" / "joint_cv").resolve()
    outputs = ensure_outputs(out_dir, args.overwrite)

    branch = git(repo, "branch", "--show-current")
    head = git(repo, "rev-parse", "HEAD")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}."
        )

    candidates = discover_metadata()
    labels_by_subject = load_deap_labels(deap_dir)
    code_evidence = inspect_project_code(repo)

    participant_ratings_paths = [
        Path(row["path"])
        for row in candidates
        if row["filename"].lower() == "participant_ratings.csv"
    ]
    analyses = [
        inspect_participant_ratings(path, labels_by_subject)
        for path in participant_ratings_paths
    ]

    status, verified, reason = choose_resolution(analyses)
    mapping_rows: list[dict[str, Any]] = []
    if verified is not None:
        mapping_rows = verified["mapped_rows"]

    write_csv(outputs["candidates"], candidates)
    write_csv(outputs["code"], code_evidence)
    write_csv(outputs["mapping"], mapping_rows)

    report = {
        "audit_type": "deap_official_mapping_resolution",
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "search_roots": [str(p) for p in SEARCH_ROOTS],
        "metadata_candidates": candidates,
        "project_code_evidence": code_evidence,
        "participant_ratings_analyses": analyses,
        "resolution": {
            "status": status,
            "reason": reason,
            "verified_mapping_row_count": len(mapping_rows),
            "deap_stimulus_aware_manifest_ready": bool(mapping_rows),
            "deap_joint_cv_ready": bool(mapping_rows),
        },
    }
    outputs["json"].write_text(
        json.dumps(safe_json(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    alignment_rows: list[dict[str, Any]] = []
    for analysis in analyses:
        for key in ("trial_order_alignment", "experiment_order_alignment"):
            a = analysis.get(key, {})
            alignment_rows.append(
                {
                    "participant_ratings_path": analysis.get("path"),
                    "hypothesis": key,
                    "subjects_compared": a.get("subjects_compared"),
                    "mean_abs_error": a.get("mean_abs_error"),
                    "max_abs_error": a.get("max_abs_error"),
                    "exact_match_fraction_1e-8": a.get(
                        "exact_match_fraction_1e-8"
                    ),
                }
            )

    md = [
        "# DEAP Official Mapping Resolution",
        "",
        "Read-only audit. No model training or Joint-CV folds were created.",
        "",
        "## Decision",
        "",
        f"- Status: **{status}**",
        f"- DEAP stimulus-aware manifest ready: `{bool(mapping_rows)}`",
        f"- DEAP Joint-CV ready: `{bool(mapping_rows)}`",
        f"- Verified mapping rows: `{len(mapping_rows)}`",
        "",
        reason,
        "",
        "## Metadata Search",
        "",
        f"- Search roots: `{[str(p) for p in SEARCH_ROOTS]}`",
        f"- Candidates found: `{len(candidates)}`",
        f"- participant_ratings.csv files found: "
        f"`{len(participant_ratings_paths)}`",
        "",
        md_table(
            candidates,
            [
                "filename", "path", "exact_expected_name",
                "archive_candidate", "size_bytes",
            ],
        ),
        "",
        "## Alignment Tests Against Embedded DEAP Labels",
        "",
        md_table(
            alignment_rows,
            [
                "participant_ratings_path", "hypothesis",
                "subjects_compared", "mean_abs_error", "max_abs_error",
                "exact_match_fraction_1e-8",
            ],
        ),
        "",
        "## Actual Project-Code Evidence",
        "",
        md_table(
            code_evidence,
            [
                "artifact_path", "line_number", "category", "line",
            ],
        ),
        "",
        "## Interpretation",
        "",
    ]

    if mapping_rows:
        md.extend(
            [
                "The official metadata candidate has been verified by exact "
                "agreement with all four embedded DEAP ratings for all 32 subjects. "
                "The generated mapping may now be used to build the DEAP canonical "
                "physical-trial manifest.",
                "",
                f"- Mapping file: `{outputs['mapping'].relative_to(repo)}`",
            ]
        )
    else:
        md.extend(
            [
                "Do not construct DEAP stimulus-held-out or Strict Joint folds. "
                "I-DARE may proceed independently because its stimulus identities "
                "are already explicit and verified.",
                "",
            ]
        )

    outputs["md"].write_text("\n".join(md), encoding="utf-8")

    print("DEAP official-mapping resolution completed.")
    print(f"Branch: {branch}")
    print(f"HEAD: {head}")
    print(f"Metadata candidates found: {len(candidates)}")
    print(
        "participant_ratings.csv files found:",
        len(participant_ratings_paths),
    )
    print(f"Resolution status: {status}")
    print(f"Verified mapping rows: {len(mapping_rows)}")
    print(f"DEAP Joint-CV ready: {bool(mapping_rows)}")
    print(f"Report: {outputs['md']}")


if __name__ == "__main__":
    main()

