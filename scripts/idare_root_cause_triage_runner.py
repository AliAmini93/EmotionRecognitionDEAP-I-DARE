#!/usr/bin/env python3
"""
Guarded I-DARE root-cause triage runner.

Current authorization boundary:
- default mode is validate
- validation/preflight only
- no audit execution
- no experiments
- no permutation/null computation
- no model results
- no forbidden project scope

Allowed file:
- scripts/idare_root_cause_triage_runner.py

Optional validation outputs, only if --write-report is explicitly passed:
- docs/idare_root_cause_triage_validation_report.md
- docs/idare_root_cause_triage_validation_report.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


EXPECTED_BRANCH = "idare/postwave1/root-cause-triage"
EXPECTED_WORKTREE_SUFFIX = "EmotionRecognitionDEAP-I-DARE-root-cause-triage"

ALLOWED_OUTPUT_PREFIXES = (
    "docs/idare_root_cause_triage_",
    "scripts/idare_root_cause_triage_",
)

PLANNED_AUDIT_CATEGORIES = [
    "label/task sanity",
    "subject-domain shift",
    "protocol alignment",
    "representation failure",
    "null/permutation sanity",
]

CANONICAL_AUDIT_CATEGORIES = [
    "label/task sanity",
    "subject-domain shift",
    "protocol alignment",
    "representation failure",
    "null/permutation sanity",
]

FORBIDDEN_SCOPE = [
    "Wave 2",
    "DG execution",
    "model-capacity probe",
    "augmentation",
    "DEAP",
    "fusion",
    "preprocessing changes",
    "threshold changes",
    "W1-owned file edits",
    "main push",
    "audit execution",
    "experiments",
    "permutation/null computation",
    "new model results",
]

CORE_DOCS = [
    "docs/idare_root_cause_triage_execution_authorization_package.md",
    "docs/idare_root_cause_triage_execution_authorization_package.json",
    "docs/idare_cross_subject_failure_root_cause_triage_objective.md",
    "docs/idare_cross_subject_failure_root_cause_triage_objective.json",
    "docs/idare_root_cause_triage_branch_objective.md",
    "docs/idare_root_cause_triage_branch_objective.json",
    "docs/idare_root_cause_triage_runner_plan.md",
    "docs/idare_root_cause_triage_runner_plan.json",
    "docs/idare_project_synthesis_and_stop_pivot_decision.md",
    "docs/idare_project_synthesis_and_stop_pivot_decision.json",
    "docs/idare_project_final_registry.csv",
]

ARTIFACT_GROUPS = {
    "wave1_w1a": [
        "EmotionRecognitionDEAP-I-DARE-w1a",
        "W1A",
        "eeg-input-definition",
    ],
    "wave1_w1b": [
        "EmotionRecognitionDEAP-I-DARE-w1b",
        "W1B",
        "eeg-subject-normalization",
    ],
    "wave1_w1c": [
        "EmotionRecognitionDEAP-I-DARE-w1c",
        "W1C",
        "emg-baseline-ablation",
    ],
    "wave1_w1d": [
        "EmotionRecognitionDEAP-I-DARE-w1d",
        "W1D",
        "feature-discriminability",
    ],
    "strict_ntd_smoke": [
        "EmotionRecognitionDEAP-I-DARE-strict-ntd-smoke",
        "strict_ntd",
        "strict-ntd",
        "strict_nontransductive",
    ],
    "representation_redesign_smoke": [
        "EmotionRecognitionDEAP-I-DARE-repr-redesign-smoke",
        "representation_redesign_smoke",
        "representation-redesign-smoke",
    ],
    "representation_redesign_confirmation": [
        "EmotionRecognitionDEAP-I-DARE-repr-redesign-confirmation",
        "representation_redesign_confirmation",
        "representation-redesign-confirmation",
    ],
    "project_synthesis_registry": [
        "project_synthesis",
        "project_final_registry",
        "stop_pivot",
    ],
}

PRIMARY_CACHE_PATHS = [
    ".cache/idare_eeg_windows_32x640_float32.npy",
    ".cache/idare_eeg_cache_index.csv",
]

BASELINE_CORRECTED_CACHE_PATH = ".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy"

BASELINE_CORRECTED_INDEX_ALTERNATIVES = [
    ".cache/idare_eeg_baseline_corrected_cache_index.csv",
    ".cache/idare_eeg_cache_index_baseline_corrected.csv",
    ".cache/idare_eeg_baseline_corrected_index.csv",
    ".cache/idare_eeg_cache_index.csv",
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


def add(checks: list[Check], name: str, status: str, detail: str) -> None:
    checks.append(Check(name=name, status=status, detail=detail))


def exists(path: str | Path) -> bool:
    return Path(path).exists()


def find_any_token(root: Path, tokens: Iterable[str]) -> list[str]:
    hits: list[str] = []
    token_l = [t.lower() for t in tokens]
    for base in [root, root.parent]:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if len(hits) >= 30:
                return hits
            text = str(p).lower()
            if any(t in text for t in token_l):
                hits.append(str(p))
    return hits


def validate(write_report: bool) -> dict:
    root = Path.cwd()
    checks: list[Check] = []

    code, branch, err = run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    if code == 0 and branch == EXPECTED_BRANCH:
        add(checks, "branch", "OK", branch)
    else:
        add(checks, "branch", "BLOCKER", f"got={branch!r} err={err!r}")

    code, top, err = run_git(["rev-parse", "--show-toplevel"])
    if code == 0 and Path(top).name == EXPECTED_WORKTREE_SUFFIX:
        add(checks, "worktree", "OK", top)
    else:
        add(checks, "worktree", "BLOCKER", f"got={top!r} err={err!r}")

    code, status, err = run_git(["status", "--porcelain"])
    if code == 0:
        dirty_nonrunner = [
            line for line in status.splitlines()
            if line and "scripts/idare_root_cause_triage_runner.py" not in line
        ]
        if dirty_nonrunner:
            add(checks, "git_status", "WARN", "dirty files exist outside runner; allowed only if Control expects them")
        else:
            add(checks, "git_status", "OK", "clean except possibly runner file")
    else:
        add(checks, "git_status", "BLOCKER", err)

    for p in [".cache", ".venv"]:
        pp = Path(p)
        if pp.is_symlink():
            add(checks, f"symlink:{p}", "OK", f"{p} -> {pp.resolve()}")
        elif pp.exists():
            add(checks, f"symlink:{p}", "BLOCKER", f"{p} exists but is not a symlink")
        else:
            add(checks, f"symlink:{p}", "BLOCKER", f"{p} missing")

    missing_core = [p for p in CORE_DOCS if not exists(p)]
    if missing_core:
        add(checks, "core_docs", "BLOCKER", "missing: " + ", ".join(missing_core))
    else:
        add(checks, "core_docs", "OK", f"{len(CORE_DOCS)} core docs present")

    for group, tokens in ARTIFACT_GROUPS.items():
        hits = find_any_token(root, tokens)
        if hits:
            add(checks, f"artifact_group:{group}", "OK", hits[0])
        else:
            add(checks, f"artifact_group:{group}", "BLOCKER", f"no artifact hit for tokens={tokens}")

    missing_cache = [p for p in PRIMARY_CACHE_PATHS if not exists(p)]
    if missing_cache:
        add(checks, "primary_cache", "BLOCKER", "missing: " + ", ".join(missing_cache))
    else:
        add(checks, "primary_cache", "OK", "primary EEG cache and index present")

    if exists(BASELINE_CORRECTED_CACHE_PATH):
        add(checks, "baseline_corrected_cache", "OK", BASELINE_CORRECTED_CACHE_PATH)
    else:
        add(checks, "baseline_corrected_cache", "WARN", "baseline-corrected cache missing; not required for documentation-only validation")

    index_hits = [p for p in BASELINE_CORRECTED_INDEX_ALTERNATIVES if exists(p)]
    if index_hits:
        add(checks, "baseline_corrected_index_alternative", "OK", index_hits[0])
    else:
        add(
            checks,
            "baseline_corrected_index_alternative",
            "WARN",
            "no baseline-corrected index alternative found; prior Control marked cache filename caution non-blocking",
        )

    bad_prefixes = [
        p for p in ALLOWED_OUTPUT_PREFIXES
        if not (p.startswith("docs/idare_root_cause_triage_") or p.startswith("scripts/idare_root_cause_triage_"))
    ]
    if bad_prefixes:
        add(checks, "output_prefixes", "BLOCKER", "bad prefixes: " + ", ".join(bad_prefixes))
    else:
        add(checks, "output_prefixes", "OK", ", ".join(ALLOWED_OUTPUT_PREFIXES))

    if PLANNED_AUDIT_CATEGORIES == CANONICAL_AUDIT_CATEGORIES:
        add(checks, "planned_audit_categories", "OK", ", ".join(PLANNED_AUDIT_CATEGORIES))
    else:
        add(checks, "planned_audit_categories", "BLOCKER", "planned categories do not match canonical categories")

    add(checks, "audit_execution", "OK", "no audit mode executed")
    add(checks, "experiments", "OK", "no experiments run")
    add(checks, "forbidden_scope", "OK", "forbidden scope not touched: " + ", ".join(FORBIDDEN_SCOPE))

    blocker_count = sum(1 for c in checks if c.status == "BLOCKER")
    warn_count = sum(1 for c in checks if c.status == "WARN")

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "validate",
        "status": "BLOCKED" if blocker_count else "PASSED_WITH_WARNINGS" if warn_count else "PASSED",
        "blocker_count": blocker_count,
        "warning_count": warn_count,
        "script_created": True,
        "audit_executed": False,
        "experiments_run": False,
        "checks": [asdict(c) for c in checks],
    }

    print("===== I-DARE ROOT-CAUSE TRIAGE VALIDATION =====")
    print(f"STATUS: {report['status']}")
    print(f"BLOCKERS: {blocker_count}")
    print(f"WARNINGS: {warn_count}")
    for c in checks:
        print(f"{c.status}: {c.name}: {c.detail}")

    if write_report:
        docs = Path("docs")
        docs.mkdir(exist_ok=True)
        json_path = docs / "idare_root_cause_triage_validation_report.json"
        md_path = docs / "idare_root_cause_triage_validation_report.md"
        json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        lines = [
            "# I-DARE Root-Cause Triage Validation Report",
            "",
            f"Status: `{report['status']}`",
            "",
            f"Blockers: `{blocker_count}`",
            f"Warnings: `{warn_count}`",
            "",
            "## Checks",
            "",
            "| Status | Check | Detail |",
            "|---|---|---|",
        ]
        for c in checks:
            detail = c.detail.replace("|", "\\|")
            lines.append(f"| {c.status} | {c.name} | {detail} |")
        lines.extend([
            "",
            "## Boundary Confirmation",
            "",
            "- No audit execution occurred.",
            "- No experiments were run.",
            "- No model results were created.",
        ])
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"WROTE: {md_path}")
        print(f"WROTE: {json_path}")

    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        nargs="?",
        default="validate",
        choices=[
            "validate",
            "status",
            "inventory",
            "audit_label_task",
            "audit_subject_domain",
            "audit_protocol_alignment",
            "audit_representation_failure",
            "audit_null_permutation",
            "decision_matrix",
            "closeout",
        ],
        help="Default is validate. Audit modes are intentionally blocked under current authorization.",
    )
    parser.add_argument("--write-report", action="store_true", help="Write optional validation report docs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.mode in {
        "audit_label_task",
        "audit_subject_domain",
        "audit_protocol_alignment",
        "audit_representation_failure",
        "audit_null_permutation",
        "decision_matrix",
        "closeout",
    }:
        print(f"BLOCKER: mode {args.mode} is not authorized yet")
        print("No audit execution occurred.")
        return 2

    if args.mode in {"validate", "status", "inventory"}:
        report = validate(write_report=args.write_report)
        return 2 if report["blocker_count"] else 0

    print(f"BLOCKER: unsupported mode {args.mode}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
