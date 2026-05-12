#!/usr/bin/env python3
"""Guarded runner for I-DARE label/task + protocol reconciliation.

Default mode is validation/preflight only.

This script must not run reconciliation/audit unless a future Control Tower
message explicitly approves audit execution and the operator passes the exact
run-approval phrase.

Current creation authorization allows only:
- objective artifact creation
- guarded runner artifact creation
- validation/preflight mode
"""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_BRANCH = "idare/postwave1/label-task-protocol-reconciliation"
EXPECTED_WORKTREE = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-label-task-protocol")
ALLOWED_PREFIX = "idare_label_task_protocol_"
AUDIT_RUN_APPROVAL_PHRASE = "APPROVE_LABEL_TASK_PROTOCOL_RECONCILIATION_AUDIT_RUN"

VALIDATION_MD = Path("docs/idare_label_task_protocol_reconciliation_runner_validation.md")
VALIDATION_JSON = Path("docs/idare_label_task_protocol_reconciliation_runner_validation.json")

AUDIT_CATEGORIES = [
    "protocol alignment",
    "label/task formulation",
    "midpoint and threshold policy review",
    "fold/subject label-bias review",
    "prior-results interpretation",
    "final label-task/protocol decision matrix",
]

REQUIRED_DOCS = [
    "docs/idare_label_task_protocol_reconciliation_execution_authorization_package.md",
    "docs/idare_label_task_protocol_reconciliation_execution_authorization_package.json",
    "docs/idare_label_task_protocol_reconciliation_design_objective.md",
    "docs/idare_label_task_protocol_reconciliation_design_objective.json",
    "docs/idare_label_task_protocol_reconciliation_objective.md",
    "docs/idare_label_task_protocol_reconciliation_objective.json",
    "docs/idare_root_cause_triage_execution_authorization_package.md",
    "docs/idare_cross_subject_failure_root_cause_triage_objective.md",
    "docs/idare_project_final_registry.csv",
    "docs/idare_project_synthesis_review_and_final_registry_update.json",
]

REQUIRED_CACHE_INDEX = [
    ".cache/idare_eeg_windows_32x640_float32.npy",
    ".cache/idare_eeg_cache_index.csv",
    ".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy",
    ".cache/idare_eeg_cache_index_baseline_corrected.csv",
    ".cache/idare_trial_index.csv",
]

FORBIDDEN_NOW = [
    "reconciliation audit execution",
    "experiments",
    "model results",
    "Wave 2",
    "DG",
    "model-capacity probe",
    "augmentation",
    "representation redesign v2",
    "DEAP",
    "fusion",
    "preprocessing changes",
    "threshold changes",
    "main push",
    "W1-owned file edits",
]


@dataclass
class Check:
    name: str
    status: str
    detail: str


def run_git(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def is_allowed_output_path(path: str) -> bool:
    p = Path(path)
    if len(p.parts) < 2:
        return False
    if p.parts[0] not in {"docs", "scripts"}:
        return False
    return p.name.startswith(ALLOWED_PREFIX)


def normalize_status_path(line: str) -> str:
    # Handles porcelain-ish lines like "?? docs/file", " M docs/file", "A  docs/file".
    path = line[3:].strip() if len(line) >= 4 else line.strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1].strip()
    return path


def validate_git_state() -> list[Check]:
    checks: list[Check] = []

    rc, branch, err = run_git(["branch", "--show-current"])
    if rc == 0 and branch == EXPECTED_BRANCH:
        checks.append(Check("branch", "PASSED", branch))
    else:
        checks.append(Check("branch", "BLOCKER", f"expected={EXPECTED_BRANCH}; got={branch!r}; err={err!r}"))

    rc, root, err = run_git(["rev-parse", "--show-toplevel"])
    if rc == 0:
        root_path = Path(root).resolve()
        if root_path == EXPECTED_WORKTREE.resolve():
            checks.append(Check("worktree", "PASSED", str(root_path)))
        else:
            checks.append(Check("worktree", "BLOCKER", f"expected={EXPECTED_WORKTREE}; got={root_path}"))
    else:
        checks.append(Check("worktree", "BLOCKER", err or "git rev-parse failed"))

    rc, status, err = run_git(["status", "--short"])
    if rc != 0:
        checks.append(Check("git_status", "BLOCKER", err or "git status failed"))
    else:
        lines = [line for line in status.splitlines() if line.strip()]
        outside_allowed = []
        for line in lines:
            path = normalize_status_path(line)
            if not is_allowed_output_path(path):
                outside_allowed.append(line)
        if outside_allowed:
            checks.append(Check("git_status_allowed_prefix", "BLOCKER", "outside allowed prefix: " + " | ".join(outside_allowed)))
        else:
            detail = "clean" if not lines else "only allowed-prefix changes: " + " | ".join(lines)
            checks.append(Check("git_status_allowed_prefix", "PASSED", detail))

    rc, staged, err = run_git(["diff", "--cached", "--name-only"])
    if rc != 0:
        checks.append(Check("staged_changes", "BLOCKER", err or "git diff --cached failed"))
    elif staged.strip():
        bad = [p for p in staged.splitlines() if not is_allowed_output_path(p)]
        if bad:
            checks.append(Check("staged_changes", "BLOCKER", "staged outside allowed prefix: " + ", ".join(bad)))
        else:
            checks.append(Check("staged_changes", "PASSED", "staged files are within allowed prefix"))
    else:
        checks.append(Check("staged_changes", "PASSED", "no staged changes"))

    return checks


def validate_required_paths() -> list[Check]:
    checks: list[Check] = []

    for path in REQUIRED_DOCS:
        p = Path(path)
        checks.append(Check(f"required_doc:{path}", "PASSED" if p.exists() else "BLOCKER", "exists" if p.exists() else "missing"))

    for path in REQUIRED_CACHE_INDEX:
        p = Path(path)
        checks.append(Check(f"required_cache_or_index:{path}", "PASSED" if p.exists() else "BLOCKER", "exists" if p.exists() else "missing"))

    for path in [".cache", ".venv"]:
        p = Path(path)
        if p.exists():
            checks.append(Check(f"local_link_or_dir:{path}", "PASSED", str(p.resolve())))
        else:
            checks.append(Check(f"local_link_or_dir:{path}", "BLOCKER", "missing"))

    return checks


def validate_prefix_and_scope() -> list[Check]:
    checks: list[Check] = []
    intended_outputs = [
        "docs/idare_label_task_protocol_reconciliation_objective.md",
        "docs/idare_label_task_protocol_reconciliation_objective.json",
        "scripts/idare_label_task_protocol_reconciliation_runner.py",
        str(VALIDATION_MD),
        str(VALIDATION_JSON),
    ]

    bad_outputs = [p for p in intended_outputs if not is_allowed_output_path(p)]
    if bad_outputs:
        checks.append(Check("output_prefix", "BLOCKER", "bad outputs: " + ", ".join(bad_outputs)))
    else:
        checks.append(Check("output_prefix", "PASSED", f"all intended outputs use {ALLOWED_PREFIX}"))

    checks.append(Check("scope", "PASSED", "compact label/task + protocol reconciliation only"))
    checks.append(Check("audit_categories_encoded", "PASSED", "; ".join(AUDIT_CATEGORIES)))
    checks.append(Check("forbidden_now_encoded", "PASSED", "; ".join(FORBIDDEN_NOW)))
    return checks


def build_report(mode: str, audit_requested: bool, control_run_approval: str) -> dict[str, Any]:
    checks: list[Check] = []
    checks.extend(validate_git_state())
    checks.extend(validate_required_paths())
    checks.extend(validate_prefix_and_scope())

    if audit_requested:
        if control_run_approval != AUDIT_RUN_APPROVAL_PHRASE:
            checks.append(
                Check(
                    "audit_execution_guard",
                    "BLOCKER",
                    "audit mode requested without exact future Control Tower run-approval phrase",
                )
            )
        else:
            checks.append(
                Check(
                    "audit_execution_guard",
                    "BLOCKER",
                    "Audit execution is intentionally blocked in artifact-creation phase even with phrase.",
                )
            )
    else:
        checks.append(Check("audit_execution_guard", "PASSED", "validate/preflight mode only; no audit execution requested"))

    blocker_count = sum(1 for c in checks if c.status == "BLOCKER")
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runner": "scripts/idare_label_task_protocol_reconciliation_runner.py",
        "mode": mode,
        "status": "BLOCKED" if blocker_count else "PASSED",
        "blocker_count": blocker_count,
        "audit_execution_occurred": False,
        "experiment_or_model_result_created": False,
        "allowed_prefix": ALLOWED_PREFIX,
        "expected_branch": EXPECTED_BRANCH,
        "expected_worktree": str(EXPECTED_WORKTREE),
        "audit_categories_encoded": AUDIT_CATEGORIES,
        "forbidden_now": FORBIDDEN_NOW,
        "checks": [asdict(c) for c in checks],
    }


def write_validation_report(report: dict[str, Any]) -> None:
    VALIDATION_JSON.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines: list[str] = []
    lines.append("# I-DARE Label/Task Protocol Reconciliation Runner Validation")
    lines.append("")
    lines.append(f"- status: `{report['status']}`")
    lines.append(f"- mode: `{report['mode']}`")
    lines.append(f"- blocker_count: `{report['blocker_count']}`")
    lines.append(f"- audit_execution_occurred: `{str(report['audit_execution_occurred']).lower()}`")
    lines.append(f"- experiment_or_model_result_created: `{str(report['experiment_or_model_result_created']).lower()}`")
    lines.append(f"- allowed_prefix: `{report['allowed_prefix']}`")
    lines.append("")
    lines.append("## Checks")
    lines.append("")
    lines.append("| Check | Status | Detail |")
    lines.append("|---|---|---|")
    for check in report["checks"]:
        detail = str(check["detail"]).replace("\n", " ")
        lines.append(f"| `{check['name']}` | `{check['status']}` | {detail} |")
    lines.append("")
    lines.append("## Encoded Audit Categories")
    lines.append("")
    for item in report["audit_categories_encoded"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Current Boundary")
    lines.append("")
    lines.append("This validation did not execute reconciliation/audit and did not create experiment/model results.")
    lines.append("Audit execution remains blocked until a future explicit Control Tower run approval.")
    VALIDATION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["validate", "audit"], default="validate")
    parser.add_argument("--control-run-approval", default="")
    args = parser.parse_args()

    audit_requested = args.mode == "audit"
    report = build_report(args.mode, audit_requested, args.control_run_approval)
    write_validation_report(report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "PASSED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
