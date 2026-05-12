#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPECTED_BRANCH = "idare/postwave1/idare-prior-best-cell-confirmation"
EXPECTED_WORKTREE = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-idare-prior-best-confirm")
ALLOWED_PREFIX = "idare_prior_best_confirm_"

ROOT = Path(__file__).resolve().parents[1]

OBJECTIVE_JSON = ROOT / "docs" / "idare_prior_best_confirm_objective.json"
OUT_JSON = ROOT / "docs" / "idare_prior_best_confirm_validation_report.json"
OUT_MD = ROOT / "docs" / "idare_prior_best_confirm_validation_report.md"

EXPECTED_CELLS = [
    {
        "cell_id": "C0",
        "dataset": "I-DARE",
        "modality": "EEG",
        "task": "arousal",
        "label_policy": "midpoint_as_high",
        "recipe": "ce_class_weighted",
    },
    {
        "cell_id": "C1",
        "dataset": "I-DARE",
        "modality": "EEG",
        "task": "valence",
        "label_policy": "discard_midpoint",
        "recipe": "balanced_sampler_ce",
    },
    {
        "cell_id": "C2",
        "dataset": "I-DARE",
        "modality": "EMG",
        "task": "arousal",
        "label_policy": "discard_midpoint",
        "recipe": "ce_class_weighted",
    },
    {
        "cell_id": "C3",
        "dataset": "I-DARE",
        "modality": "EMG",
        "task": "valence",
        "label_policy": "midpoint_as_high",
        "recipe": "ce_class_weighted",
    },
]

REQUIRED_DOC_ARTIFACTS = [
    "docs/project_status_current.md",
    "docs/project_operating_protocol.md",
    "docs/research_scope_and_objectives.md",
    "docs/smoke_and_evaluation_protocol.md",
    "docs/idare_label_policy_ablation_objective.md",
    "docs/idare_label_policy_ablation_objective.json",
    "docs/idare_label_policy_ablation_report.md",
    "docs/idare_label_policy_ablation_report.json",
    "docs/idare_label_policy_ablation_eeg_primary.json",
    "docs/idare_label_policy_ablation_emg_primary.json",
    "docs/idare_label_policy_ablation_review_status.md",
    "docs/idare_label_policy_ablation_review_status.json",
]

REQUIRED_INPUTS = {
    "eeg_cache_npy": {
        "path": ".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy",
        "expected_shape": [2016, 32, 640],
    },
    "eeg_cache_index_csv": {
        "path": ".cache/idare_eeg_cache_index_baseline_corrected.csv",
        "required_columns": [
            "cache_row",
            "subject_id",
            "arousal_midpoint_as_high",
            "valence_discard_midpoint",
        ],
    },
    "emg_cache_npy": {
        "path": ".cache/idare_emg_features.npy",
        "expected_shape": [2016, 22],
    },
    "emg_cache_index_csv": {
        "path": ".cache/idare_emg_feature_cache_index.csv",
        "required_columns": [
            "cache_row",
            "subject_id",
            "arousal_discard_midpoint",
            "valence_midpoint_as_high",
        ],
    },
}

ALLOWED_PREFIX_PATHS = (
    "docs/idare_prior_best_confirm_",
    "scripts/idare_prior_best_confirm_",
)

ALLOWED_EXISTING_PREFIX_FILES = {
    "docs/idare_prior_best_confirm_objective.md",
    "docs/idare_prior_best_confirm_objective.json",
    "docs/idare_prior_best_confirm_validation_report.md",
    "docs/idare_prior_best_confirm_validation_report.json",
    "docs/idare_prior_best_confirm_validation_terminal_recovery.log",
    "scripts/idare_prior_best_confirm_runner.py",
}

FORBIDDEN_ACTIONS = [
    "confirmation_execution",
    "144_run_label_policy_rerun",
    "experiment",
    "model_result_creation",
    "wave2",
    "domain_generalization",
    "model_capacity_probe",
    "augmentation",
    "representation_redesign_v2",
    "deap",
    "fusion",
    "preprocessing_change",
    "threshold_change",
    "main_push",
    "final_paper_level_performance_claim",
]


def git(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def add_check(checks: list[dict[str, Any]], name: str, ok: bool, details: Any = None) -> None:
    checks.append({"name": name, "ok": bool(ok), "details": details})


def read_csv_header_and_count(path: Path) -> tuple[list[str], int]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return [], 0
        count = sum(1 for _ in reader)
    return header, count


def npy_shape(path: Path) -> list[int] | None:
    try:
        import numpy as np
    except Exception:
        return None
    arr = np.load(path, mmap_mode="r")
    return [int(v) for v in arr.shape]


def parse_porcelain_paths(porcelain: str) -> list[str]:
    paths = []
    for line in porcelain.splitlines():
        if not line:
            continue

        # Porcelain v1 is normally: XY SP PATH.
        # Some intent-to-add lines may appear as "A  PATH" or " A PATH".
        # Avoid blindly slicing off the first 3 chars unless the separator is present.
        if line.startswith("?? "):
            raw = line[3:]
        elif len(line) >= 4 and line[2] == " ":
            raw = line[3:]
        elif len(line) >= 3:
            raw = line[2:].strip()
        else:
            raw = line.strip()

        if " -> " in raw:
            raw = raw.rsplit(" -> ", 1)[1]
        paths.append(raw.strip())
    return paths


def is_allowed_prefix_path(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in ALLOWED_PREFIX_PATHS)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="validate", choices=["validate", "execute"])
    parser.add_argument("--folds", type=int, default=6)
    parser.add_argument("--planned-runs", type=int, default=24)
    args = parser.parse_args()

    checks: list[dict[str, Any]] = []
    blockers: list[str] = []

    if args.mode != "validate":
        blockers.append("confirmation execution is not authorized; runner is currently validation-only")

    code, git_root, git_root_err = git(["rev-parse", "--show-toplevel"])
    git_root_ok = code == 0 and Path(git_root).resolve() == ROOT.resolve()
    add_check(checks, "git_root_matches_script_root", git_root_ok, {"git_root": git_root, "script_root": str(ROOT)})
    if not git_root_ok:
        blockers.append("git root does not match runner root")

    add_check(
        checks,
        "expected_worktree_path",
        ROOT.resolve() == EXPECTED_WORKTREE.resolve(),
        {"expected": str(EXPECTED_WORKTREE), "actual": str(ROOT.resolve())},
    )
    if ROOT.resolve() != EXPECTED_WORKTREE.resolve():
        blockers.append("runner is not executing from the approved worktree path")

    code, branch, branch_err = git(["rev-parse", "--abbrev-ref", "HEAD"])
    branch_ok = code == 0 and branch == EXPECTED_BRANCH
    add_check(checks, "expected_branch", branch_ok, {"expected": EXPECTED_BRANCH, "actual": branch, "stderr": branch_err})
    if not branch_ok:
        blockers.append("current branch is not the approved confirmation branch")

    code, status_short, status_err = git(["status", "--short", "--branch"])
    add_check(checks, "git_status_readable", code == 0, {"status": status_short, "stderr": status_err})
    if code != 0:
        blockers.append("git status is not readable")

    code, porcelain, porcelain_err = git(["status", "--porcelain"])
    changed_paths = parse_porcelain_paths(porcelain) if code == 0 else []
    disallowed_changes = [p for p in changed_paths if not is_allowed_prefix_path(p)]
    add_check(
        checks,
        "git_changes_limited_to_allowed_prefix",
        code == 0 and not disallowed_changes,
        {"changed_paths": changed_paths, "disallowed_changes": disallowed_changes},
    )
    if disallowed_changes:
        blockers.append("working tree has changes outside allowed idare_prior_best_confirm_ prefix")

    prefix_files = []
    for base in [ROOT / "docs", ROOT / "scripts"]:
        if base.exists():
            prefix_files.extend(str(p.relative_to(ROOT)) for p in base.glob(f"{ALLOWED_PREFIX}*"))
    unexpected_prefix_files = sorted(set(prefix_files) - ALLOWED_EXISTING_PREFIX_FILES)
    add_check(
        checks,
        "only_expected_prefix_files_present",
        not unexpected_prefix_files,
        {"prefix_files": sorted(prefix_files), "unexpected_prefix_files": unexpected_prefix_files},
    )
    if unexpected_prefix_files:
        blockers.append("unexpected idare_prior_best_confirm_ files already exist")

    objective_ok = OBJECTIVE_JSON.exists()
    add_check(checks, "objective_json_exists", objective_ok, str(OBJECTIVE_JSON.relative_to(ROOT)))
    if not objective_ok:
        blockers.append("objective JSON is missing")
        objective = {}
    else:
        objective = json.loads(OBJECTIVE_JSON.read_text(encoding="utf-8"))

    cells_ok = objective.get("registered_cells") == EXPECTED_CELLS
    add_check(checks, "exact_four_registered_cells", cells_ok, objective.get("registered_cells"))
    if not cells_ok:
        blockers.append("registered cells do not exactly match the Control Tower matrix")

    matrix = objective.get("planned_matrix_metadata", {})
    matrix_ok = (
        matrix.get("cells") == 4
        and args.folds == 6
        and matrix.get("folds_per_cell") == 6
        and matrix.get("planned_confirmation_runs") == args.planned_runs == 24
        and matrix.get("metadata_only") is True
    )
    add_check(checks, "planned_matrix_metadata_only_4x6_24", matrix_ok, matrix)
    if not matrix_ok:
        blockers.append("planned matrix metadata does not validate as 4 cells x 6 folds = 24")

    for rel in REQUIRED_DOC_ARTIFACTS:
        exists = (ROOT / rel).exists()
        add_check(checks, f"required_doc_exists:{rel}", exists, rel)
        if not exists:
            blockers.append(f"missing required prior/governance artifact: {rel}")

    for key, spec in REQUIRED_INPUTS.items():
        path = ROOT / spec["path"]
        exists = path.exists()
        add_check(checks, f"required_input_exists:{key}", exists, spec["path"])
        if not exists:
            blockers.append(f"missing required input: {spec['path']}")
            continue

        if path.suffix == ".npy":
            shape = npy_shape(path)
            expected = spec.get("expected_shape")
            shape_ok = shape == expected
            add_check(checks, f"npy_shape:{key}", shape_ok, {"expected": expected, "actual": shape})
            if not shape_ok:
                blockers.append(f"unexpected npy shape for {spec['path']}: expected {expected}, got {shape}")

        if path.suffix == ".csv":
            header, rows = read_csv_header_and_count(path)
            required_columns = spec.get("required_columns", [])
            missing_cols = [c for c in required_columns if c not in header]
            add_check(
                checks,
                f"csv_columns:{key}",
                not missing_cols,
                {"required": required_columns, "missing": missing_cols, "rows": rows},
            )
            if missing_cols:
                blockers.append(f"missing required columns in {spec['path']}: {missing_cols}")
            rows_ok = rows > 0
            add_check(checks, f"csv_nonempty:{key}", rows_ok, {"rows": rows})
            if not rows_ok:
                blockers.append(f"empty input index: {spec['path']}")

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BLOCKED" if blockers else "PASSED",
        "mode": args.mode,
        "expected_branch": EXPECTED_BRANCH,
        "expected_worktree": str(EXPECTED_WORKTREE),
        "actual_root": str(ROOT.resolve()),
        "allowed_prefix": ALLOWED_PREFIX,
        "registered_cells": EXPECTED_CELLS,
        "planned_matrix_metadata": {
            "cells": 4,
            "folds_per_cell": args.folds,
            "planned_confirmation_runs": args.planned_runs,
            "metadata_only": True,
        },
        "checks": checks,
        "blockers": blockers,
        "git_status_short_branch": status_short,
        "forbidden_actions": FORBIDDEN_ACTIONS,
        "confirmation_execution_occurred": False,
        "experiment_or_model_result_created": False,
        "model_results_created": False,
        "final_paper_level_claim_made": False,
    }

    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# I-DARE Prior Best Confirmation Validation Report",
        "",
        f"- status: `{report['status']}`",
        f"- mode: `{args.mode}`",
        f"- expected_branch: `{EXPECTED_BRANCH}`",
        f"- expected_worktree: `{EXPECTED_WORKTREE}`",
        f"- actual_root: `{ROOT.resolve()}`",
        "- confirmation_execution_occurred: `false`",
        "- experiment_or_model_result_created: `false`",
        "- model_results_created: `false`",
        "- final_paper_level_claim_made: `false`",
        "",
        "## Registered Cells",
        "",
        "| Cell | Dataset | Modality | Task | Label policy | Recipe |",
        "|---|---|---|---|---|---|",
    ]
    for cell in EXPECTED_CELLS:
        lines.append(
            f"| {cell['cell_id']} | {cell['dataset']} | {cell['modality']} | {cell['task']} | "
            f"{cell['label_policy']} | {cell['recipe']} |"
        )
    lines.extend([
        "",
        "## Planned Matrix Metadata",
        "",
        "- 4 cells x 6 folds = 24 planned confirmation runs.",
        "- Metadata only.",
        "- No confirmation run executed.",
        "",
        "## Blockers",
        "",
    ])
    if blockers:
        for blocker in blockers:
            lines.append(f"- BLOCKER: {blocker}")
    else:
        lines.append("- None.")
    lines.extend([
        "",
        "## Check Summary",
        "",
        "| Check | OK | Details |",
        "|---|---:|---|",
    ])
    for check in checks:
        details = json.dumps(check.get("details"), sort_keys=True)
        if len(details) > 180:
            details = details[:177] + "..."
        lines.append(f"| {check['name']} | {str(check['ok']).lower()} | `{details}` |")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": report["status"],
        "blocker_count": len(blockers),
        "out_md": str(OUT_MD.relative_to(ROOT)),
        "out_json": str(OUT_JSON.relative_to(ROOT)),
        "confirmation_execution_occurred": False,
        "experiment_or_model_result_created": False,
    }, indent=2))

    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
