#!/usr/bin/env python3
"""
Guarded I-DARE representation redesign confirmation runner.

Default behavior is validation/preflight only.

This script must not execute the 18-run confirmation unless Control Tower later
issues explicit run approval. In the current authorization state, execution is
blocked by design.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


EXPECTED_BRANCH = "idare/postwave1/representation-redesign-confirmation"
EXPECTED_WORKTREE = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-repr-redesign-confirmation")
ALLOWED_DOC_PREFIX = "docs/idare_repr_redesign_confirm_"
ALLOWED_SCRIPT_PREFIX = "scripts/idare_repr_redesign_confirm_"
REQUIRED_CACHE_FILES = [
    ".cache/idare_eeg_windows_32x640_float32.npy",
    ".cache/idare_eeg_cache_index.csv",
]
REQUIRED_CONTROL_DOCS = [
    "docs/project_status_current.md",
    "docs/project_status_current.json",
    "docs/project_operating_protocol.md",
    "docs/research_scope_and_objectives.md",
    "docs/research_scope_and_objectives.json",
    "docs/smoke_and_evaluation_protocol.md",
    "docs/smoke_and_evaluation_protocol.json",
    "docs/idare_repr_redesign_confirm_objective.md",
    "docs/idare_repr_redesign_confirm_objective.json",
]
CELLS = [
    "R0_current_representation_anchor",
    "R2_train_only_subject_invariant_feature_selection",
    "R3_diagnostics_first_stable_feature_subset",
]
FOLDS = [1, 2, 3, 4, 5, 6]


@dataclass(frozen=True)
class ScopeConfig:
    dataset: str = "I-DARE"
    modality: str = "EEG-only"
    task: str = "arousal-only"
    setting: str = "cross-subject / held-out-subject"
    model_family: str = "Ridge/classical"
    folds: str = "same held-out-subject folds unless Control Tower changes this"


@dataclass(frozen=True)
class LeakageConfig:
    fitted_statistics_scope: str = "training_subjects_only"
    held_out_subject_feature_statistics: bool = False
    test_labels_for_fitting_or_selection: bool = False
    global_all_subject_feature_selection: bool = False
    per_test_subject_normalization: bool = False
    target_adaptation: bool = False
    threshold_tuning_on_held_out_subjects: bool = False
    feature_selection_fit_scope: str = "training_folds_only"
    stability_filter_fit_scope: str = "training_folds_only"


def run_git(args: list[str], root: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(root) if root is not None else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def build_run_manifest() -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    run_id = 1
    for cell in CELLS:
        for fold_id in FOLDS:
            manifest.append(
                {
                    "run_id": run_id,
                    "cell": cell,
                    "fold_id": fold_id,
                    "dataset": "I-DARE",
                    "modality": "EEG-only",
                    "task": "arousal",
                    "model_family": "Ridge/classical",
                    "execution_authorized": False,
                }
            )
            run_id += 1
    return manifest


def validate_leakage_config(config: LeakageConfig) -> list[str]:
    blockers: list[str] = []
    if config.fitted_statistics_scope != "training_subjects_only":
        blockers.append("fitted statistics are not restricted to training subjects only")
    if config.held_out_subject_feature_statistics:
        blockers.append("held-out/test-subject feature statistics are enabled")
    if config.test_labels_for_fitting_or_selection:
        blockers.append("test labels for fitting/selection are enabled")
    if config.global_all_subject_feature_selection:
        blockers.append("global all-subject feature selection is enabled")
    if config.per_test_subject_normalization:
        blockers.append("per-test-subject normalization is enabled")
    if config.target_adaptation:
        blockers.append("target adaptation is enabled")
    if config.threshold_tuning_on_held_out_subjects:
        blockers.append("threshold tuning on held-out subjects is enabled")
    if config.feature_selection_fit_scope != "training_folds_only":
        blockers.append("feature selection is not fit on training folds only")
    if config.stability_filter_fit_scope != "training_folds_only":
        blockers.append("stability filters are not fit on training folds only")
    return blockers


def validate_dirty_scope(root: Path) -> dict[str, Any]:
    status = run_git(["status", "--porcelain"], root=root)
    dirty_lines = [line for line in status.splitlines() if line.strip()]
    blockers: list[str] = []
    allowed_dirty: list[str] = []
    forbidden_dirty: list[str] = []

    for line in dirty_lines:
        path = line[3:].strip()
        if path.startswith(ALLOWED_DOC_PREFIX) or path.startswith(ALLOWED_SCRIPT_PREFIX):
            allowed_dirty.append(line)
        else:
            forbidden_dirty.append(line)
            blockers.append(f"dirty file outside allowed prefixes: {line}")

    return {
        "dirty_lines": dirty_lines,
        "allowed_dirty": allowed_dirty,
        "forbidden_dirty": forbidden_dirty,
        "blockers": blockers,
    }


def validate_output_prefixes() -> dict[str, Any]:
    planned_outputs = [
        "docs/idare_repr_redesign_confirm_objective.md",
        "docs/idare_repr_redesign_confirm_objective.json",
        "scripts/idare_repr_redesign_confirm_runner.py",
        "docs/idare_repr_redesign_confirm_run_manifest.csv",
        "docs/idare_repr_redesign_confirm_metrics_summary.csv",
        "docs/idare_repr_redesign_confirm_leakage_audit.json",
        "docs/idare_repr_redesign_confirm_closeout.md",
        "docs/idare_repr_redesign_confirm_closeout.json",
    ]
    blockers = [
        p for p in planned_outputs
        if not (p.startswith(ALLOWED_DOC_PREFIX) or p.startswith(ALLOWED_SCRIPT_PREFIX))
    ]
    return {
        "planned_outputs": planned_outputs,
        "invalid_outputs": blockers,
        "blockers": [f"planned output violates prefix: {p}" for p in blockers],
    }


def validate(mode: str) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []

    root = Path(run_git(["rev-parse", "--show-toplevel"]))
    branch = run_git(["branch", "--show-current"], root=root)
    head = run_git(["rev-parse", "HEAD"], root=root)

    if branch != EXPECTED_BRANCH:
        blockers.append(f"unexpected branch: {branch}; expected {EXPECTED_BRANCH}")

    if root.resolve() != EXPECTED_WORKTREE.resolve():
        blockers.append(f"unexpected worktree: {root}; expected {EXPECTED_WORKTREE}")

    script_path = Path(__file__).resolve()
    try:
        script_rel = rel(script_path, root)
        if not script_rel.startswith(ALLOWED_SCRIPT_PREFIX):
            blockers.append(f"runner path violates allowed prefix: {script_rel}")
    except ValueError:
        blockers.append(f"runner is outside git worktree: {script_path}")

    missing_cache = [p for p in REQUIRED_CACHE_FILES if not (root / p).exists()]
    for p in missing_cache:
        blockers.append(f"missing required EEG cache/index file: {p}")

    missing_docs = [p for p in REQUIRED_CONTROL_DOCS if not (root / p).exists()]
    for p in missing_docs:
        blockers.append(f"missing required control/objective doc: {p}")

    dirty_scope = validate_dirty_scope(root)
    blockers.extend(dirty_scope["blockers"])

    prefix_check = validate_output_prefixes()
    blockers.extend(prefix_check["blockers"])

    scope = ScopeConfig()
    leakage = LeakageConfig()
    blockers.extend(validate_leakage_config(leakage))

    manifest = build_run_manifest()
    if len(manifest) != 18:
        blockers.append(f"planned matrix size is {len(manifest)}; expected 18")

    if sorted({row["cell"] for row in manifest}) != sorted(CELLS):
        blockers.append("planned manifest cells do not match required R0/R2/R3 cells")

    if sorted({row["fold_id"] for row in manifest}) != FOLDS:
        blockers.append("planned manifest folds do not match required 1..6 folds")

    execution_authorized = False
    if mode != "validate":
        blockers.append("execution/planning modes are blocked in current authorization state")

    return {
        "status": "BLOCKED" if blockers else "VALIDATION_PASSED",
        "mode": mode,
        "branch": branch,
        "head": head,
        "worktree": str(root),
        "scope": asdict(scope),
        "cells": CELLS,
        "folds": FOLDS,
        "planned_runs": len(manifest),
        "execution_authorized": execution_authorized,
        "required_cache_files": REQUIRED_CACHE_FILES,
        "missing_cache_files": missing_cache,
        "required_control_docs": REQUIRED_CONTROL_DOCS,
        "missing_control_docs": missing_docs,
        "dirty_scope": dirty_scope,
        "output_prefix_check": prefix_check,
        "leakage_config": asdict(leakage),
        "blockers": blockers,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["validate", "plan", "execute"],
        default="validate",
        help="Default is validate. plan/execute are blocked until future Control Tower authorization.",
    )
    args = parser.parse_args()

    result = validate(args.mode)
    print(json.dumps(result, indent=2, sort_keys=True))

    if result["blockers"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
