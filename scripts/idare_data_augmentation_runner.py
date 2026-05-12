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

EXPECTED_BRANCH = "idare/postwave1/data-augmentation-track"
EXPECTED_WORKTREE = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-data-augmentation")
ALLOWED_PREFIX = "idare_data_augmentation_"

OBJECTIVE_JSON = Path("docs/idare_data_augmentation_objective.json")
VALIDATION_JSON = Path("docs/idare_data_augmentation_validation_report.json")
VALIDATION_MD = Path("docs/idare_data_augmentation_validation_report.md")
OPTION_A_MATRIX_CSV = Path("docs/idare_data_augmentation_option_a_run_matrix.csv")
IMPLEMENTATION_JSON = Path("docs/idare_data_augmentation_option_a_implementation_report.json")
IMPLEMENTATION_MD = Path("docs/idare_data_augmentation_option_a_implementation_report.md")

CONTROL_DOCS = [
    "docs/idare_deap_cross_subject_data_augmentation_objective.md",
    "docs/idare_deap_cross_subject_data_augmentation_objective.json",
    "docs/idare_data_augmentation_track_execution_authorization_package.md",
    "docs/idare_data_augmentation_track_execution_authorization_package.json",
    "docs/project_status_current.md",
    "docs/project_status_current.json",
    "docs/project_operating_protocol.md",
    "docs/research_scope_and_objectives.md",
    "docs/smoke_and_evaluation_protocol.md",
    "docs/idare_prior_best_confirmation_status_update.md",
    "docs/idare_prior_best_confirmation_status_update.json",
]

REQUIRED_INPUTS = {
    "eeg_bsl_npy": ".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy",
    "eeg_bsl_index": ".cache/idare_eeg_cache_index_baseline_corrected.csv",
    "eeg_raw_npy": ".cache/idare_eeg_windows_32x640_float32.npy",
    "eeg_raw_index": ".cache/idare_eeg_cache_index.csv",
    "eeg_bsl_stats": ".cache/idare_eeg_bsl_stats.npy",
    "eeg_bsl_stats_index": ".cache/idare_eeg_bsl_stats_index.csv",
    "emg_features_npy": ".cache/idare_emg_features.npy",
    "emg_features_index": ".cache/idare_emg_feature_cache_index.csv",
    "emg_bsl_stats": ".cache/idare_emg_bsl_stats.npy",
    "emg_bsl_stats_index": ".cache/idare_emg_bsl_stats_index.csv",
    "raw_emg_npy": ".cache/idare_raw_emg_windows_2x10000_float32.npy",
    "raw_emg_index": ".cache/idare_raw_emg_cache_index.csv",
}

TASKS = ["valence", "arousal"]
MODALITIES = ["EEG", "EMG"]
FOLDS = [1, 2, 3, 4, 5, 6]

EEG_POLICIES = [
    "E0_none_baseline",
    "E1_additive_gaussian_noise_weak",
    "E2_additive_gaussian_noise_medium",
    "E3_amplitude_scaling",
    "E4_time_channel_masking_or_dropout",
]

EMG_POLICIES = [
    "M0_none_baseline",
    "M1_feature_gaussian_jitter_weak",
    "M2_feature_gaussian_jitter_medium",
    "M3_feature_scaling",
    "M4_feature_dropout",
]

LABEL_COLUMNS = {
    "valence": "valence_midpoint_as_high",
    "arousal": "arousal_midpoint_as_high",
}

OPTION_A_EXPECTED_RUNS = 120


def run_cmd(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def check(ok: bool, name: str, details: Any = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "details": details}


def repo_root() -> Path:
    rc, out, err = run_cmd(["git", "rev-parse", "--show-toplevel"])
    if rc != 0:
        raise RuntimeError(f"not a git worktree: {err}")
    return Path(out)


def current_branch() -> str:
    rc, out, err = run_cmd(["git", "branch", "--show-current"])
    if rc != 0:
        return f"ERROR: {err}"
    return out


def git_status_short_branch() -> str:
    rc, out, err = run_cmd(["git", "status", "--short", "--branch"])
    if rc != 0:
        return f"ERROR: {err}"
    return out


def changed_paths() -> list[str]:
    rc, out, _ = run_cmd(["git", "status", "--porcelain=v1"])
    if rc != 0 or not out:
        return []
    paths: list[str] = []
    for line in out.splitlines():
        # Porcelain v1 format is "XY PATH" for tracked changes and
        # "?? PATH" for untracked files. Split instead of slicing so
        # paths like "scripts/..." and "docs/..." are never truncated.
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            paths.append(parts[1])
    return paths


def path_allowed(path: str) -> bool:
    p = str(Path(path))
    return p.startswith(f"docs/{ALLOWED_PREFIX}") or p.startswith(f"scripts/{ALLOWED_PREFIX}")


def load_numpy_shape(path: Path) -> dict[str, Any]:
    import numpy as np
    arr = np.load(path, mmap_mode="r")
    return {"shape": list(arr.shape), "dtype": str(arr.dtype)}


def csv_columns(path: Path, required: list[str]) -> dict[str, Any]:
    import pandas as pd
    df = pd.read_csv(path, nrows=5)
    cols = list(df.columns)
    missing = [c for c in required if c not in cols]
    return {"columns": cols, "required": required, "missing": missing, "preview_rows": len(df)}


def option_a_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    run_id = 1
    for target in TASKS:
        for modality in MODALITIES:
            policies = EEG_POLICIES if modality == "EEG" else EMG_POLICIES
            for policy in policies:
                for fold_id in FOLDS:
                    rows.append(
                        {
                            "run_id": run_id,
                            "matrix_option": "A",
                            "dataset": "I-DARE",
                            "target": target,
                            "label_column": LABEL_COLUMNS[target],
                            "modality": modality,
                            "da_policy": policy,
                            "fold_id": fold_id,
                            "execution_authorized": False,
                            "status": "planned_metadata_only",
                        }
                    )
                    run_id += 1
    return rows


def write_option_a_matrix() -> None:
    rows = option_a_rows()
    if len(rows) != OPTION_A_EXPECTED_RUNS:
        raise RuntimeError(f"Option A matrix row count mismatch: {len(rows)} != {OPTION_A_EXPECTED_RUNS}")

    OPTION_A_MATRIX_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OPTION_A_MATRIX_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_report(mode: str) -> dict[str, Any]:
    root = repo_root()
    branch = current_branch()
    status = git_status_short_branch()
    changes = changed_paths()

    checks: list[dict[str, Any]] = []

    checks.append(check(root == EXPECTED_WORKTREE, "expected_worktree", {"actual": str(root), "expected": str(EXPECTED_WORKTREE)}))
    checks.append(check(branch == EXPECTED_BRANCH, "expected_branch", {"actual": branch, "expected": EXPECTED_BRANCH}))
    checks.append(check(Path(".cache").exists(), "cache_symlink_or_dir_exists", ".cache"))
    checks.append(check(Path(".venv").exists(), "venv_symlink_or_dir_exists", ".venv"))

    disallowed_changes = [p for p in changes if not path_allowed(p)]
    checks.append(check(len(disallowed_changes) == 0, "dirty_paths_limited_to_allowed_prefix", {"changed_paths": changes, "disallowed": disallowed_changes}))

    for doc in CONTROL_DOCS:
        checks.append(check(Path(doc).exists(), f"control_doc_exists:{doc}", doc))

    checks.append(check(OBJECTIVE_JSON.exists(), "branch_objective_json_exists", str(OBJECTIVE_JSON)))

    for name, raw_path in REQUIRED_INPUTS.items():
        p = Path(raw_path)
        checks.append(check(p.exists(), f"required_input_exists:{name}", raw_path))

    if Path(REQUIRED_INPUTS["eeg_bsl_npy"]).exists():
        checks.append(check(True, "eeg_bsl_npy_shape", load_numpy_shape(Path(REQUIRED_INPUTS["eeg_bsl_npy"]))))
    if Path(REQUIRED_INPUTS["eeg_raw_npy"]).exists():
        checks.append(check(True, "eeg_raw_npy_shape", load_numpy_shape(Path(REQUIRED_INPUTS["eeg_raw_npy"]))))
    if Path(REQUIRED_INPUTS["emg_features_npy"]).exists():
        checks.append(check(True, "emg_features_npy_shape", load_numpy_shape(Path(REQUIRED_INPUTS["emg_features_npy"]))))
    if Path(REQUIRED_INPUTS["raw_emg_npy"]).exists():
        checks.append(check(True, "raw_emg_npy_shape", load_numpy_shape(Path(REQUIRED_INPUTS["raw_emg_npy"]))))

    required_label_cols = [
        "cache_row",
        "subject_id",
        "valence_midpoint_as_high",
        "arousal_midpoint_as_high",
    ]

    if Path(REQUIRED_INPUTS["eeg_bsl_index"]).exists():
        c = csv_columns(Path(REQUIRED_INPUTS["eeg_bsl_index"]), required_label_cols)
        checks.append(check(len(c["missing"]) == 0, "eeg_bsl_index_required_columns", c))
    if Path(REQUIRED_INPUTS["emg_features_index"]).exists():
        c = csv_columns(Path(REQUIRED_INPUTS["emg_features_index"]), required_label_cols)
        checks.append(check(len(c["missing"]) == 0, "emg_features_index_required_columns", c))

    rows = option_a_rows()
    checks.append(check(len(rows) == OPTION_A_EXPECTED_RUNS, "option_A_matrix_has_120_rows", {"rows": len(rows)}))

    unique_targets = sorted({r["target"] for r in rows})
    unique_modalities = sorted({r["modality"] for r in rows})
    unique_folds = sorted({r["fold_id"] for r in rows})
    checks.append(check(unique_targets == ["arousal", "valence"], "option_A_targets_exact", unique_targets))
    checks.append(check(unique_modalities == ["EEG", "EMG"], "option_A_modalities_exact", unique_modalities))
    checks.append(check(unique_folds == FOLDS, "option_A_folds_exact", unique_folds))

    forbidden_scope = {
        "DEAP_stage_1": False,
        "fusion": False,
        "DG": False,
        "SupCon": False,
        "model_capacity_probe": False,
        "augmentation_plus_model_search": False,
        "preprocessing_change": False,
        "threshold_change": False,
        "main_push": False,
    }

    blockers = [c for c in checks if not c["ok"]]

    return {
        "status": "PASSED" if not blockers else "BLOCKED",
        "mode": mode,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_branch": EXPECTED_BRANCH,
        "actual_branch": branch,
        "expected_worktree": str(EXPECTED_WORKTREE),
        "actual_worktree": str(root),
        "git_status_short_branch": status,
        "execution_authorized": False,
        "da_execution_occurred": False,
        "experiment_or_model_result_created": False,
        "model_results_created": False,
        "option_A": {
            "selected": True,
            "dataset": "I-DARE",
            "targets": TASKS,
            "modalities": MODALITIES,
            "folds": FOLDS,
            "expected_runs": OPTION_A_EXPECTED_RUNS,
            "execution_authorized": False,
            "run_matrix_csv": str(OPTION_A_MATRIX_CSV),
        },
        "label_columns": LABEL_COLUMNS,
        "eeg_da_policies": EEG_POLICIES,
        "emg_da_policies": EMG_POLICIES,
        "forbidden_scope": forbidden_scope,
        "checks": checks,
        "blocker_count": len(blockers),
        "blockers": blockers,
    }


def write_validation_reports(report: dict[str, Any]) -> None:
    VALIDATION_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# I-DARE Data Augmentation Validation Report",
        "",
        f"- status: `{report['status']}`",
        f"- mode: `{report['mode']}`",
        f"- expected_branch: `{report['expected_branch']}`",
        f"- actual_branch: `{report['actual_branch']}`",
        f"- expected_worktree: `{report['expected_worktree']}`",
        f"- actual_worktree: `{report['actual_worktree']}`",
        f"- execution_authorized: `{str(report['execution_authorized']).lower()}`",
        f"- da_execution_occurred: `{str(report['da_execution_occurred']).lower()}`",
        f"- experiment_or_model_result_created: `{str(report['experiment_or_model_result_created']).lower()}`",
        f"- model_results_created: `{str(report['model_results_created']).lower()}`",
        f"- blocker_count: `{report['blocker_count']}`",
        "",
        "## Option A Matrix Metadata",
        "",
        "- Option A selected: `true`",
        "- Matrix: `2 targets x 2 modalities x 5 DA policies x 6 folds = 120 runs`",
        "- Execution authorized: `false`",
        "- Metadata/plan only; no DA run executed.",
        "",
        "## Blockers",
        "",
    ]

    if report["blockers"]:
        for b in report["blockers"]:
            lines.append(f"- `{b['name']}`: `{json.dumps(b['details'], sort_keys=True)}`")
    else:
        lines.append("- None.")

    lines += [
        "",
        "## Check Summary",
        "",
        "| Check | OK | Details |",
        "|---|---:|---|",
    ]

    for c in report["checks"]:
        details = json.dumps(c["details"], sort_keys=True)
        if len(details) > 240:
            details = details[:237] + "..."
        lines.append(f"| {c['name']} | {str(c['ok']).lower()} | `{details}` |")

    VALIDATION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_implementation_report(report: dict[str, Any]) -> None:
    impl = {
        "status": report["status"],
        "implementation_stage": "option_A_run_implementation_plan_only",
        "execution_authorized": False,
        "da_execution_occurred": False,
        "model_results_created": False,
        "option_A_run_matrix_csv": str(OPTION_A_MATRIX_CSV),
        "option_A_expected_runs": OPTION_A_EXPECTED_RUNS,
        "label_columns": LABEL_COLUMNS,
        "eeg_da_policies": EEG_POLICIES,
        "emg_da_policies": EMG_POLICIES,
        "blocker_count": report["blocker_count"],
        "blockers": report["blockers"],
    }
    IMPLEMENTATION_JSON.write_text(json.dumps(impl, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "# I-DARE Data Augmentation Option A Implementation Report",
        "",
        f"- status: `{impl['status']}`",
        "- implementation_stage: `option_A_run_implementation_plan_only`",
        "- execution_authorized: `false`",
        "- da_execution_occurred: `false`",
        "- model_results_created: `false`",
        f"- option_A_expected_runs: `{OPTION_A_EXPECTED_RUNS}`",
        f"- option_A_run_matrix_csv: `{OPTION_A_MATRIX_CSV}`",
        "",
        "## Option A",
        "",
        "`2 targets x 2 modalities x 5 DA policies x 6 folds = 120 runs`",
        "",
        "## Current Boundary",
        "",
        "`RUN_IMPLEMENTATION_ONLY_NO_EXECUTION`",
    ]
    IMPLEMENTATION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Guarded I-DARE data augmentation runner")
    parser.add_argument("--mode", choices=["status", "validate", "plan", "run", "closeout"], default="status")
    parser.add_argument("--matrix-option", choices=["A"], default="A")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    if args.mode in {"run", "closeout"}:
        print("BLOCKER: DA run/closeout is not authorized yet. Runner is implementation/validation-only at this gate.")
        print("DA_EXECUTION_OCCURRED: false")
        print("EXPERIMENT_OR_MODEL_RESULT_CREATED: false")
        print("MODEL_RESULTS_CREATED: false")
        return 2

    report = build_report(args.mode)

    if args.mode == "plan":
        write_option_a_matrix()
        report = build_report(args.mode)

    if args.write_report:
        write_validation_reports(report)
        if args.mode == "plan":
            write_implementation_report(report)

    print(f"STATUS: {report['status']}")
    print(f"MODE: {report['mode']}")
    print(f"BLOCKERS: {report['blocker_count']}")
    print(f"OPTION_A_EXPECTED_RUNS: {OPTION_A_EXPECTED_RUNS}")
    print("DA_EXECUTION_OCCURRED: false")
    print("EXPERIMENT_OR_MODEL_RESULT_CREATED: false")
    print("MODEL_RESULTS_CREATED: false")

    if report["blockers"]:
        for b in report["blockers"]:
            print(f"BLOCKER: {b['name']} :: {json.dumps(b['details'], sort_keys=True)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
