#!/usr/bin/env python3
"""Guarded I-DARE representation-redesign smoke runner.

Default behavior is validation/preflight only. This script must not execute the
24-run smoke unless a later Control Tower approval token is explicitly supplied.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

EXPECTED_BRANCH = "idare/postwave1/representation-redesign-smoke"
EXPECTED_WORKTREE = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-repr-redesign-smoke")
OBJECTIVE_JSON = Path("docs/idare_repr_redesign_smoke_objective.json")
VALIDATION_MD = Path("docs/idare_repr_redesign_smoke_validation_report.md")
VALIDATION_JSON = Path("docs/idare_repr_redesign_smoke_validation_report.json")

CACHE_NPY = Path(".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy")
CACHE_INDEX = Path(".cache/idare_eeg_cache_index_baseline_corrected.csv")

ALLOWED_PREFIXES = (
    "docs/idare_repr_redesign_smoke_",
    "scripts/idare_repr_redesign_smoke_",
)

RUN_APPROVAL_TOKEN = "APPROVE_REPRESENTATION_REDESIGN_SMOKE_EXECUTION"

PLANNED_OUTPUTS = [
    "docs/idare_repr_redesign_smoke_validation_report.md",
    "docs/idare_repr_redesign_smoke_validation_report.json",
    "docs/idare_repr_redesign_smoke_runs.csv",
    "docs/idare_repr_redesign_smoke_metric_summary.csv",
    "docs/idare_repr_redesign_smoke_fold_level_report.md",
    "docs/idare_repr_redesign_smoke_fold_level_report.json",
    "docs/idare_repr_redesign_smoke_leakage_audit.md",
    "docs/idare_repr_redesign_smoke_leakage_audit.json",
    "docs/idare_repr_redesign_smoke_representation_diagnostic_report.md",
    "docs/idare_repr_redesign_smoke_representation_diagnostic_report.json",
    "docs/idare_repr_redesign_smoke_closeout_report.md",
    "docs/idare_repr_redesign_smoke_closeout_report.json",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def blocker(message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "level": "BLOCKER",
        "message": message,
        "details": details or {},
    }


def ok(message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "level": "OK",
        "message": message,
        "details": details or {},
    }


def is_allowed_path(path: str) -> bool:
    return path.startswith(ALLOWED_PREFIXES)


def parse_porcelain_paths(text: str) -> list[str]:
    paths: list[str] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        # Porcelain v1 format: XY path, or XY old -> new for renames.
        path = line[3:].strip()
        if " -> " in path:
            old, new = path.split(" -> ", 1)
            paths.append(old.strip())
            paths.append(new.strip())
        else:
            paths.append(path)
    return paths


def validate_git_scope(checks: list[dict[str, Any]]) -> None:
    cwd = Path.cwd().resolve()
    top = Path(run_git(["rev-parse", "--show-toplevel"])).resolve()
    branch = run_git(["branch", "--show-current"])
    head = run_git(["rev-parse", "HEAD"])
    porcelain = run_git(["status", "--porcelain"])

    checks.append(ok("git metadata read", {"cwd": str(cwd), "top": str(top), "branch": branch, "head": head}))

    if branch != EXPECTED_BRANCH:
        checks.append(blocker("wrong branch", {"expected": EXPECTED_BRANCH, "actual": branch}))
    else:
        checks.append(ok("branch matches expected branch"))

    if top != EXPECTED_WORKTREE:
        checks.append(blocker("wrong worktree", {"expected": str(EXPECTED_WORKTREE), "actual": str(top)}))
    else:
        checks.append(ok("worktree matches expected worktree"))

    changed = parse_porcelain_paths(porcelain)
    disallowed = [p for p in changed if not is_allowed_path(p)]
    if disallowed:
        checks.append(blocker("non-allowed dirty paths present", {"paths": disallowed}))
    else:
        checks.append(ok("dirty paths are empty or restricted to allowed idare_repr_redesign_smoke_* prefixes", {"paths": changed}))


def validate_objective(checks: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not OBJECTIVE_JSON.exists():
        checks.append(blocker("objective JSON missing", {"path": str(OBJECTIVE_JSON)}))
        return None

    data = json.loads(OBJECTIVE_JSON.read_text(encoding="utf-8"))
    checks.append(ok("objective JSON loaded", {"path": str(OBJECTIVE_JSON)}))

    expected = {
        "objective_id": "idare_repr_redesign_smoke_objective",
        "allowed_branch": EXPECTED_BRANCH,
        "allowed_worktree": str(EXPECTED_WORKTREE),
    }
    for key, value in expected.items():
        if data.get(key) != value:
            checks.append(blocker(f"objective field mismatch: {key}", {"expected": value, "actual": data.get(key)}))
        else:
            checks.append(ok(f"objective field validated: {key}"))

    auth = data.get("authorization", {})
    if auth.get("smoke_execution_authorized") is not False:
        checks.append(blocker("objective must not authorize smoke execution", {"authorization": auth}))
    else:
        checks.append(ok("objective correctly keeps smoke execution unauthorized"))

    return data


def validate_inputs(checks: list[dict[str, Any]]) -> None:
    missing = []
    for path in [CACHE_NPY, CACHE_INDEX]:
        if not path.exists():
            missing.append(str(path))

    if missing:
        checks.append(blocker("required EEG input files missing", {"missing": missing}))
        return

    checks.append(ok("required EEG cache/index files exist", {"cache_npy": str(CACHE_NPY), "cache_index": str(CACHE_INDEX)}))

    try:
        arr = np.load(CACHE_NPY, mmap_mode="r")
        shape = list(arr.shape)
        if len(shape) != 3 or shape[1:] != [32, 640]:
            checks.append(blocker("unexpected EEG cache shape", {"shape": shape, "expected_suffix": [32, 640]}))
        else:
            checks.append(ok("EEG cache shape is compatible", {"shape": shape, "dtype": str(arr.dtype)}))
    except Exception as exc:
        checks.append(blocker("failed to inspect EEG cache npy", {"error": repr(exc)}))
        return

    try:
        df = pd.read_csv(CACHE_INDEX, nrows=5)
        columns = list(df.columns)
        required_cols = [
            "cache_row",
            "subject_id",
            "arousal_midpoint_as_high",
            "arousal_discard_midpoint",
            "arousal_midpoint_as_low",
        ]
        missing_cols = [c for c in required_cols if c not in columns]
        if missing_cols:
            checks.append(blocker("required cache-index columns missing", {"missing": missing_cols, "columns": columns}))
        else:
            checks.append(ok("cache-index required arousal/subject/cache columns exist", {"columns": columns}))
    except Exception as exc:
        checks.append(blocker("failed to inspect EEG cache index CSV", {"error": repr(exc)}))


def validate_output_prefix(checks: list[dict[str, Any]]) -> None:
    disallowed = [p for p in PLANNED_OUTPUTS if not is_allowed_path(p)]
    if disallowed:
        checks.append(blocker("planned outputs escape allowed prefix", {"disallowed": disallowed}))
    else:
        checks.append(ok("planned outputs are restricted to allowed prefixes", {"planned_outputs": PLANNED_OUTPUTS}))


def validate_scope_and_leakage_design(checks: list[dict[str, Any]], objective: dict[str, Any] | None) -> None:
    if objective is None:
        checks.append(blocker("cannot validate scope/leakage without objective JSON"))
        return

    scope = objective.get("scope", {})
    expected_scope = {
        "dataset": "I-DARE only",
        "modality": "EEG-only first",
        "task": "arousal-only first",
        "evaluation": "cross-subject / held-out-subject",
        "comparison": "pairwise reference comparison required",
        "model_family": "Ridge/classical model only",
        "cells_only": True,
    }
    for key, expected in expected_scope.items():
        actual = scope.get(key)
        if actual != expected:
            checks.append(blocker(f"scope mismatch: {key}", {"expected": expected, "actual": actual}))
        else:
            checks.append(ok(f"scope validated: {key}"))

    matrix = objective.get("planned_matrix", {})
    if matrix.get("planned_runs") != 24 or matrix.get("cells") != 4 or matrix.get("folds") != 6:
        checks.append(blocker("planned matrix mismatch", {"planned_matrix": matrix}))
    else:
        checks.append(ok("planned 4 x 6 = 24 run matrix is declared but not executed", {"planned_matrix": matrix}))

    if matrix.get("execution_authorized") is not False:
        checks.append(blocker("planned matrix must remain execution_authorized=false", {"planned_matrix": matrix}))
    else:
        checks.append(ok("planned matrix correctly remains unauthorized for execution"))

    cells = {row.get("cell"): row for row in objective.get("cells", [])}
    required_cells = {"R0", "R1", "R2", "R3"}
    if set(cells) != required_cells:
        checks.append(blocker("cell set mismatch", {"expected": sorted(required_cells), "actual": sorted(cells)}))
    else:
        checks.append(ok("representation cell set validated", {"cells": sorted(cells)}))

    rules = objective.get("hard_leakage_rules", {})
    required_true = [
        "all_fitted_statistics_training_subjects_only",
        "no_heldout_feature_statistics",
        "no_test_labels_for_fit",
        "no_global_all_subject_feature_selection",
        "no_per_test_subject_normalization",
        "no_target_adaptation",
        "no_threshold_tuning_on_heldout",
        "feature_selection_residualization_stability_train_fold_only",
    ]
    failed = [name for name in required_true if rules.get(name) is not True]
    if failed:
        checks.append(blocker("hard leakage rules not fully asserted", {"failed": failed, "rules": rules}))
    else:
        checks.append(ok("hard leakage constraints asserted in objective"))

    r1 = cells.get("R1", {})
    r2 = cells.get("R2", {})
    r3 = cells.get("R3", {})
    if r1.get("held_out_subject_statistics_allowed") is not False:
        checks.append(blocker("R1 must disallow held-out subject statistics", {"R1": r1}))
    else:
        checks.append(ok("R1 leakage guard validated"))

    if r2.get("global_all_subject_feature_selection_allowed") is not False:
        checks.append(blocker("R2 must disallow global all-subject feature selection", {"R2": r2}))
    else:
        checks.append(ok("R2 leakage guard validated"))

    if r3.get("global_all_subject_stability_filter_allowed") is not False:
        checks.append(blocker("R3 must disallow global all-subject stability filtering", {"R3": r3}))
    else:
        checks.append(ok("R3 leakage guard validated"))


def write_validation_report(report: dict[str, Any]) -> None:
    VALIDATION_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    checks = report["checks"]
    blocker_count = report["blocker_count"]
    status = report["status"]

    lines = [
        "# I-DARE Representation Redesign Smoke Validation Report",
        "",
        f"- status: `{status}`",
        f"- generated_at_utc: `{report['generated_at_utc']}`",
        f"- blocker_count: `{blocker_count}`",
        f"- smoke_execution_occurred: `{report['smoke_execution_occurred']}`",
        f"- experiment_execution_occurred: `{report['experiment_execution_occurred']}`",
        "",
        "## Checks",
        "",
        "| Level | Message | Details |",
        "|---|---|---|",
    ]

    for item in checks:
        details = json.dumps(item.get("details", {}), ensure_ascii=False, sort_keys=True)
        lines.append(f"| {item['level']} | {item['message']} | `{details}` |")

    if blocker_count:
        lines.extend(["", "## Blocker Status", "", "`BLOCKED`"])
    else:
        lines.extend(["", "## Blocker Status", "", "`NO_BLOCKERS`"])

    lines.extend([
        "",
        "## Execution Boundary",
        "",
        "No 24-run smoke execution occurred.",
        "No experiment execution occurred.",
        "Runner creation/validation only.",
        "",
    ])

    VALIDATION_MD.write_text("\n".join(lines), encoding="utf-8")


def validate_all() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    validate_git_scope(checks)
    objective = validate_objective(checks)
    validate_inputs(checks)
    validate_output_prefix(checks)
    validate_scope_and_leakage_design(checks, objective)

    blocker_count = sum(1 for item in checks if item["level"] == "BLOCKER")
    status = "validation_passed" if blocker_count == 0 else "validation_blocked"

    report = {
        "status": status,
        "generated_at_utc": now_utc(),
        "mode": "validate",
        "blocker_count": blocker_count,
        "smoke_execution_occurred": False,
        "experiment_execution_occurred": False,
        "checks": checks,
        "required_next_control_notification": True,
    }
    write_validation_report(report)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["validate", "run"], default="validate")
    parser.add_argument("--control-run-approval", default="")
    parser.add_argument("--confirm-24-run-smoke", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.mode == "validate":
        report = validate_all()
        print(json.dumps({
            "status": report["status"],
            "blocker_count": report["blocker_count"],
            "validation_report_md": str(VALIDATION_MD),
            "validation_report_json": str(VALIDATION_JSON),
            "smoke_execution_occurred": False,
            "experiment_execution_occurred": False,
        }, indent=2))
        return 0 if report["blocker_count"] == 0 else 2

    # Run mode is deliberately guarded. This branch must not execute the smoke
    # unless Control Tower later gives explicit run approval.
    report = validate_all()
    if report["blocker_count"] != 0:
        print("BLOCKER: validation failed; refusing run mode")
        return 2

    if args.control_run_approval != RUN_APPROVAL_TOKEN or not args.confirm_24_run_smoke:
        print("BLOCKER: 24-run smoke execution is not authorized")
        print("Required later token:", RUN_APPROVAL_TOKEN)
        print("Required later flag: --confirm-24-run-smoke")
        print("No smoke execution occurred.")
        return 2

    print("BLOCKER: run approval token detected, but this creation step did not execute the 24-run smoke.")
    print("Control Tower must issue a separate run-execution instruction before any experiment command is run.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
