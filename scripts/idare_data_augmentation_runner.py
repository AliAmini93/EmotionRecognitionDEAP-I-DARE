#!/usr/bin/env python3
from __future__ import annotations

import argparse
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

EEG_REQUIRED_COLUMNS = [
    "cache_row",
    "subject_id",
    "valence_discard_midpoint",
    "valence_midpoint_as_high",
    "arousal_discard_midpoint",
    "arousal_midpoint_as_high",
]

EMG_REQUIRED_COLUMNS = [
    "cache_row",
    "subject_id",
    "valence_discard_midpoint",
    "valence_midpoint_as_high",
    "arousal_discard_midpoint",
    "arousal_midpoint_as_high",
]

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

PLANNED_OPTIONS = {
    "A_preferred": {
        "targets": ["valence", "arousal"],
        "modalities": ["EEG", "EMG"],
        "policies_per_modality": 5,
        "folds": 6,
        "total_runs": 120,
        "execution_authorized": False,
    },
    "B_runtime_fallback": {
        "targets": ["valence", "arousal"],
        "modalities": ["EEG"],
        "policies_per_modality": 5,
        "folds": 6,
        "total_runs": 60,
        "execution_authorized": False,
    },
}


def run_cmd(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        args,
        cwd=cwd,
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
    paths = []
    for line in out.splitlines():
        if len(line) >= 4:
            paths.append(line[3:])
    return paths


def path_allowed(path: str) -> bool:
    p = Path(path)
    return (
        str(p).startswith(f"docs/{ALLOWED_PREFIX}")
        or str(p).startswith(f"scripts/{ALLOWED_PREFIX}")
    )


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

    if Path(REQUIRED_INPUTS["eeg_bsl_index"]).exists():
        c = csv_columns(Path(REQUIRED_INPUTS["eeg_bsl_index"]), EEG_REQUIRED_COLUMNS)
        checks.append(check(len(c["missing"]) == 0, "eeg_bsl_index_required_columns", c))
    if Path(REQUIRED_INPUTS["emg_features_index"]).exists():
        c = csv_columns(Path(REQUIRED_INPUTS["emg_features_index"]), EMG_REQUIRED_COLUMNS)
        checks.append(check(len(c["missing"]) == 0, "emg_features_index_required_columns", c))

    checks.append(check(EEG_POLICIES == [
        "E0_none_baseline",
        "E1_additive_gaussian_noise_weak",
        "E2_additive_gaussian_noise_medium",
        "E3_amplitude_scaling",
        "E4_time_channel_masking_or_dropout",
    ], "eeg_policy_registry_exact", EEG_POLICIES))

    checks.append(check(EMG_POLICIES == [
        "M0_none_baseline",
        "M1_feature_gaussian_jitter_weak",
        "M2_feature_gaussian_jitter_medium",
        "M3_feature_scaling",
        "M4_feature_dropout",
    ], "emg_policy_registry_exact", EMG_POLICIES))

    checks.append(check(PLANNED_OPTIONS["A_preferred"]["total_runs"] == 120, "option_A_metadata_120_runs", PLANNED_OPTIONS["A_preferred"]))
    checks.append(check(PLANNED_OPTIONS["B_runtime_fallback"]["total_runs"] == 60, "option_B_metadata_60_runs", PLANNED_OPTIONS["B_runtime_fallback"]))

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
        "planned_matrix_metadata": PLANNED_OPTIONS,
        "eeg_da_policies": EEG_POLICIES,
        "emg_da_policies": EMG_POLICIES,
        "forbidden_scope": forbidden_scope,
        "checks": checks,
        "blocker_count": len(blockers),
        "blockers": blockers,
    }


def write_reports(report: dict[str, Any]) -> None:
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
        f"- blocker_count: `{report['blocker_count']}`",
        "",
        "## Planned Matrix Metadata",
        "",
        "- Option A: `2 targets x 2 modalities x 5 DA policies x 6 folds = 120 runs`",
        "- Option B: `2 targets x 1 modality x 5 DA policies x 6 folds = 60 EEG-first runs`",
        "- Metadata only; no DA run executed.",
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Guarded I-DARE data augmentation runner")
    parser.add_argument("--mode", choices=["status", "validate", "run", "closeout"], default="status")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    if args.mode in {"run", "closeout"}:
        print("BLOCKER: DA execution/closeout is not authorized yet. Runner is validation-only at this gate.")
        print("da_execution_occurred=false")
        print("experiment_or_model_result_created=false")
        return 2

    report = build_report(args.mode)

    if args.write_report:
        write_reports(report)

    print(f"STATUS: {report['status']}")
    print(f"MODE: {report['mode']}")
    print(f"BLOCKERS: {report['blocker_count']}")
    print("DA_EXECUTION_OCCURRED: false")
    print("EXPERIMENT_OR_MODEL_RESULT_CREATED: false")

    if report["blockers"]:
        for b in report["blockers"]:
            print(f"BLOCKER: {b['name']} :: {json.dumps(b['details'], sort_keys=True)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
