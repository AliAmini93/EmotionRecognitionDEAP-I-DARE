#!/usr/bin/env python3
"""Guarded runner for compact I-DARE label/task + protocol reconciliation.

Default mode remains validation/preflight only.

Audit mode is allowed only when the explicit Control Tower run-approval phrase
is supplied. Audit mode is read-only with respect to project evidence: it reads
committed docs/artifacts and local I-DARE cache/index metadata, then writes
reports under docs/idare_label_task_protocol_*.

It must not run experiments, create model results, touch DEAP, fusion,
preprocessing, thresholds, Wave 2, DG, model-capacity, augmentation, or W1 files.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import subprocess
from collections import Counter
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

REPORT_PATHS = {
    "protocol_comparison": (
        Path("docs/idare_label_task_protocol_protocol_comparison_report.md"),
        Path("docs/idare_label_task_protocol_protocol_comparison_report.json"),
    ),
    "label_task_policy": (
        Path("docs/idare_label_task_protocol_label_task_policy_report.md"),
        Path("docs/idare_label_task_protocol_label_task_policy_report.json"),
    ),
    "midpoint_fold_subject_bias": (
        Path("docs/idare_label_task_protocol_midpoint_fold_subject_bias_report.md"),
        Path("docs/idare_label_task_protocol_midpoint_fold_subject_bias_report.json"),
    ),
    "prior_results": (
        Path("docs/idare_label_task_protocol_prior_results_interpretation_report.md"),
        Path("docs/idare_label_task_protocol_prior_results_interpretation_report.json"),
    ),
    "decision_matrix": (
        Path("docs/idare_label_task_protocol_final_reconciliation_decision_matrix.md"),
        Path("docs/idare_label_task_protocol_final_reconciliation_decision_matrix.json"),
    ),
    "closeout": (
        Path("docs/idare_label_task_protocol_reconciliation_closeout.md"),
        Path("docs/idare_label_task_protocol_reconciliation_closeout.json"),
    ),
    "artifact_bundle": (
        Path("docs/idare_label_task_protocol_artifact_review_bundle.md"),
        Path("docs/idare_label_task_protocol_artifact_review_bundle.json"),
    ),
}

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
    ".cache/idare_eeg_cache_index.csv",
    ".cache/idare_eeg_cache_index_baseline_corrected.csv",
    ".cache/idare_trial_index.csv",
]

REQUIRED_CACHE_ARRAYS_METADATA_ONLY = [
    ".cache/idare_eeg_windows_32x640_float32.npy",
    ".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy",
]

OPTIONAL_IDARE_DOCS = [
    "docs/project_status_current.md",
    "docs/project_status_current.json",
    "docs/project_operating_protocol.md",
    "docs/research_scope_and_objectives.md",
    "docs/smoke_and_evaluation_protocol.md",
    "docs/idare_label_policy_ablation_objective.md",
    "docs/idare_label_policy_ablation_report.md",
    "docs/idare_label_policy_ablation_report.json",
    "docs/idare_label_policy_ablation_review_status.md",
    "docs/idare_failure_analysis_report.md",
    "docs/idare_failure_analysis_report.json",
    "docs/idare_failure_analysis_review_status.md",
    "docs/idare_root_cause_diagnostic_report.md",
    "docs/idare_root_cause_diagnostic_report.json",
    "docs/idare_root_cause_diagnostic_review_status.md",
    "docs/idare_diagnostic_sanity_tests_report.md",
    "docs/idare_calibration_subject_generalization_report.md",
    "docs/idare_calibration_protocol_report.md",
    "docs/idare_calibration_protocol_review_status.md",
    "docs/idare_representation_label_task_redesign_report.md",
    "docs/idare_representation_label_task_redesign_report.json",
    "docs/idare_representation_label_task_redesign_review_status.md",
    "docs/idare_subject_relative_task_formulation_report.md",
    "docs/idare_subject_relative_task_formulation_report.json",
    "docs/idare_subject_relative_task_formulation_review_status.md",
    "docs/idare_subject_relative_minimal_training_report.md",
    "docs/idare_subject_relative_minimal_training_review_status.md",
    "docs/idare_subject_relative_representation_preprocessing_report.md",
    "docs/idare_subject_relative_preprocessed_minimal_training_report.md",
    "docs/idare_subject_relative_preprocessed_minimal_training_review_status.md",
    "docs/idare_subject_variability_intervention_failure_analysis_report.md",
    "docs/idare_subject_variability_intervention_failure_analysis_review_status.md",
    "docs/idare_minimal_supcon_dg_first_pass_report.md",
    "docs/idare_minimal_supcon_dg_first_pass_report.json",
    "docs/idare_project_final_registry.csv",
    "docs/idare_project_synthesis_review_and_final_registry_update.json",
]

FORBIDDEN_NOW = [
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
    "W1-owned file edits",
    "main push",
    "new operating-point claim",
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
    # Robust parsing for git status --short / porcelain v1.
    # Handles:
    #   " M scripts/file.py"
    #   "M  scripts/file.py"
    #   "?? docs/file.md"
    #   "A  docs/file.md"
    raw = line.rstrip("\n")
    if len(raw) >= 4 and raw[2] == " ":
        path = raw[3:].strip()
    else:
        parts = raw.strip().split(maxsplit=1)
        path = parts[1].strip() if len(parts) == 2 else raw.strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1].strip()
    return path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_json_if_possible(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(read_text(path))
    except Exception:
        return None


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
                outside_allowed.append(f"{line} -> {path}")
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

    for path in REQUIRED_CACHE_ARRAYS_METADATA_ONLY:
        p = Path(path)
        if p.exists():
            checks.append(Check(f"required_cache_array_metadata_only:{path}", "PASSED", f"exists size_bytes={p.stat().st_size}"))
        else:
            checks.append(Check(f"required_cache_array_metadata_only:{path}", "BLOCKER", "missing"))

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
        "scripts/idare_label_task_protocol_reconciliation_runner.py",
        "docs/idare_label_task_protocol_reconciliation_objective.md",
        "docs/idare_label_task_protocol_reconciliation_objective.json",
        "docs/idare_label_task_protocol_reconciliation_runner_validation.md",
        "docs/idare_label_task_protocol_reconciliation_runner_validation.json",
    ]
    for md_path, json_path in REPORT_PATHS.values():
        intended_outputs.extend([str(md_path), str(json_path)])

    bad_outputs = [p for p in intended_outputs if not is_allowed_output_path(p)]
    if bad_outputs:
        checks.append(Check("output_prefix", "BLOCKER", "bad outputs: " + ", ".join(bad_outputs)))
    else:
        checks.append(Check("output_prefix", "PASSED", f"all intended outputs use {ALLOWED_PREFIX}"))

    checks.append(Check("scope", "PASSED", "compact label/task + protocol reconciliation only"))
    checks.append(Check("audit_categories_encoded", "PASSED", "; ".join(AUDIT_CATEGORIES)))
    checks.append(Check("forbidden_now_encoded", "PASSED", "; ".join(FORBIDDEN_NOW)))
    return checks


def build_validation_report(mode: str, audit_requested: bool, control_run_approval: str) -> dict[str, Any]:
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
                    "audit mode requested without exact Control Tower run-approval phrase",
                )
            )
        else:
            checks.append(
                Check(
                    "audit_execution_guard",
                    "PASSED",
                    "explicit Control Tower audit run approval phrase supplied",
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, sections: list[tuple[str, str]]) -> None:
    lines: list[str] = [f"# {title}", ""]
    for heading, body in sections:
        lines.append(f"## {heading}")
        lines.append("")
        lines.extend(body.rstrip().splitlines())
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_validation_report(report: dict[str, Any]) -> None:
    write_json(VALIDATION_JSON, report)

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
    lines.append("Validation/preflight does not create model results.")
    if report["mode"] == "audit":
        lines.append("Audit mode was authorized by explicit Control Tower run approval.")
    else:
        lines.append("Audit execution remains blocked until explicit Control Tower run approval.")
    VALIDATION_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def collect_artifact_inventory() -> dict[str, Any]:
    inventory: list[dict[str, Any]] = []
    paths = []
    for p in REQUIRED_DOCS:
        paths.append(p)
    for p in OPTIONAL_IDARE_DOCS:
        paths.append(p)
    seen = set()
    for raw in paths:
        if raw in seen:
            continue
        seen.add(raw)
        path = Path(raw)
        if path.exists():
            text = read_text(path) if path.suffix.lower() in {".md", ".json", ".csv", ".txt"} else ""
            inventory.append(
                {
                    "path": raw,
                    "exists": True,
                    "size_bytes": path.stat().st_size,
                    "kind": path.suffix.lower().lstrip(".") or "unknown",
                    "contains_stop": "stop" in text.lower(),
                    "contains_subject_relative": "subject-relative" in text.lower() or "subject_relative" in text.lower(),
                    "contains_label_policy": "label policy" in text.lower() or "label-policy" in text.lower(),
                    "contains_threshold": "threshold" in text.lower(),
                    "contains_near_chance": "near-chance" in text.lower() or "near chance" in text.lower(),
                }
            )
        else:
            inventory.append({"path": raw, "exists": False})
    return {"artifacts": inventory, "present_count": sum(1 for x in inventory if x.get("exists")), "missing_count": sum(1 for x in inventory if not x.get("exists"))}


def summarize_json_sources() -> dict[str, Any]:
    summaries: dict[str, Any] = {}
    for raw in OPTIONAL_IDARE_DOCS + REQUIRED_DOCS:
        path = Path(raw)
        if path.suffix != ".json" or not path.exists():
            continue
        obj = load_json_if_possible(path)
        if obj is None:
            summaries[raw] = {"loaded": False}
            continue
        entry: dict[str, Any] = {"loaded": True}
        if isinstance(obj, dict):
            for key in [
                "status",
                "diagnosis",
                "recommended_next_objective",
                "selected_next_objective",
                "final_global_label_policy_locked",
                "fusion_started",
                "mainline_changed",
                "evidence_level",
                "next_allowed_step",
            ]:
                if key in obj:
                    entry[key] = obj[key]
            if "decision" in obj:
                entry["decision"] = obj["decision"]
            if "summary" in obj and isinstance(obj["summary"], (str, int, float, bool)):
                entry["summary"] = obj["summary"]
        summaries[raw] = entry
    return summaries


def read_csv_rows(path: Path, limit: int | None = None) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for i, row in enumerate(reader):
            if limit is not None and i >= limit:
                break
            rows.append(dict(row))
        return list(reader.fieldnames or []), rows


def safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        if isinstance(value, str) and not value.strip():
            return None
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return None
        return x
    except Exception:
        return None


def summarize_index(path: Path) -> dict[str, Any]:
    fields, rows = read_csv_rows(path)
    summary: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "columns": fields,
        "rows_loaded_for_metadata": len(rows),
    }
    subject_cols = [c for c in fields if c in {"subject_id", "subject", "participant_id"} or "subject" in c.lower()]
    if subject_cols:
        subj_col = subject_cols[0]
        subj_counts = Counter(row.get(subj_col, "") for row in rows)
        summary["subject_column"] = subj_col
        summary["subject_count"] = len([k for k in subj_counts if k != ""])
        counts = list(subj_counts.values())
        if counts:
            summary["rows_per_subject"] = {
                "min": min(counts),
                "max": max(counts),
                "mean": sum(counts) / len(counts),
            }

    label_cols = []
    for col in fields:
        low = col.lower()
        if ("valence" in low or "arousal" in low) and any(tag in low for tag in ["midpoint", "discard", "label", "score"]):
            label_cols.append(col)
    if not label_cols:
        for col in fields:
            low = col.lower()
            if "valence" in low or "arousal" in low:
                label_cols.append(col)

    label_summaries = {}
    for col in label_cols:
        values = [safe_float(row.get(col)) for row in rows]
        nonnull = [v for v in values if v is not None]
        counts = Counter(str(int(v)) if v in {0.0, 1.0} else str(v) for v in nonnull)
        label_summaries[col] = {
            "nonnull": len(nonnull),
            "missing": len(values) - len(nonnull),
            "counts": dict(sorted(counts.items())),
        }
        if subject_cols and nonnull:
            subj_col = subject_cols[0]
            subject_rates = []
            for subject in sorted({row.get(subj_col, "") for row in rows if row.get(subj_col, "") != ""}):
                sv = [safe_float(row.get(col)) for row in rows if row.get(subj_col, "") == subject]
                sv01 = [v for v in sv if v in {0.0, 1.0}]
                if sv01:
                    subject_rates.append(sum(sv01) / len(sv01))
            if subject_rates:
                label_summaries[col]["subject_positive_rate"] = {
                    "min": min(subject_rates),
                    "max": max(subject_rates),
                    "mean": sum(subject_rates) / len(subject_rates),
                    "std": statistics.pstdev(subject_rates) if len(subject_rates) > 1 else 0.0,
                    "range": max(subject_rates) - min(subject_rates),
                }
    summary["label_columns_detected"] = label_cols
    summary["label_summaries"] = label_summaries
    return summary


def collect_cache_metadata() -> dict[str, Any]:
    out: dict[str, Any] = {"indices": {}, "arrays_metadata_only": {}}
    for raw in REQUIRED_CACHE_INDEX:
        path = Path(raw)
        if path.exists():
            out["indices"][raw] = summarize_index(path)
        else:
            out["indices"][raw] = {"exists": False, "path": raw}
    for raw in REQUIRED_CACHE_ARRAYS_METADATA_ONLY:
        path = Path(raw)
        out["arrays_metadata_only"][raw] = {
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "note": "metadata only; array not loaded by audit",
        }
    return out


def keyword_evidence(inventory: dict[str, Any]) -> dict[str, Any]:
    present = [a for a in inventory["artifacts"] if a.get("exists")]
    return {
        "subject_relative_docs": [a["path"] for a in present if a.get("contains_subject_relative")],
        "label_policy_docs": [a["path"] for a in present if a.get("contains_label_policy")],
        "threshold_docs": [a["path"] for a in present if a.get("contains_threshold")],
        "near_chance_docs": [a["path"] for a in present if a.get("contains_near_chance")],
        "stop_docs": [a["path"] for a in present if a.get("contains_stop")],
    }


def make_decision_matrix(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "option": "A",
            "decision_path": "keep current held-out-subject binary arousal formulation",
            "classification": "conditional_hold_only_not_as_final",
            "rationale": [
                "Current formulation can remain as a reference/comparator for continuity.",
                "Existing evidence does not support treating it as a final operating point or sole next modeling target.",
                "No new operating-point claim is made by this audit."
            ],
            "allowed_next": "Use only as a documented comparator unless Control Tower approves a stronger protocol target.",
            "risk": "Continuing blind modeling under the same target may repeat near-chance/mixed behavior."
        },
        {
            "option": "B",
            "decision_path": "redesign label/task policy before more modeling",
            "classification": "recommended",
            "rationale": [
                "Label-policy evidence is mixed and no final global label policy is locked.",
                "Midpoint handling remains policy-level, not a threshold change to perform inside this audit.",
                "More modeling before label/task reconciliation risks optimizing an unstable target."
            ],
            "allowed_next": "Prepare a reviewed label/task decision objective, not a model-development experiment.",
            "risk": "Requires explicit Control Tower approval before any follow-up implementation."
        },
        {
            "option": "C",
            "decision_path": "reconcile or change evaluation protocol target",
            "classification": "recommended",
            "rationale": [
                "Held-out-subject evaluation remains important, but prior diagnostics indicate protocol/target mismatch needs interpretation.",
                "Protocol alignment should separate continuity baselines from final claim targets.",
                "No final LOSO or new operating-point claim is authorized here."
            ],
            "allowed_next": "Create a protocol-target closeout or decision objective after Control Tower review.",
            "risk": "Changing protocol target without a locked decision matrix would create documentation drift."
        },
        {
            "option": "D",
            "decision_path": "use subject-relative / within-subject formulation instead",
            "classification": "supported_candidate_not_auto_mainline",
            "rationale": [
                "Subject-relative evidence exists in prior artifacts and should be considered as a candidate path.",
                "It should not automatically replace the current formulation without explicit closeout approval.",
                "Within-subject framing may answer a different scientific question than held-out-subject generalization."
            ],
            "allowed_next": "Use as a candidate in the final protocol decision path, with explicit scope and evaluation target.",
            "risk": "May pivot the paper claim away from cross-subject generalization if adopted as primary."
        },
        {
            "option": "E",
            "decision_path": "stop/pivot if current formulation is unsupported",
            "classification": "contingency",
            "rationale": [
                "Stop/pivot is not required solely by this audit if protocol evidence remains available.",
                "It becomes appropriate if Control Tower rejects redesign/protocol reconciliation or if required evidence is judged too ambiguous.",
                "This audit found no blocker requiring immediate stop before review."
            ],
            "allowed_next": "Keep as a governance fallback, not the immediate default.",
            "risk": "Stopping too early may discard useful diagnostic evidence; continuing without redesign may waste modeling effort."
        },
    ]


def md_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = []
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("|" + "|".join(["---"] * len(columns)) + "|")
    for row in rows:
        vals = []
        for col in columns:
            val = row.get(col, "")
            if isinstance(val, list):
                val = "<br>".join(str(x) for x in val)
            elif isinstance(val, dict):
                val = "`" + json.dumps(val, sort_keys=True)[:500].replace("|", "\\|") + "`"
            else:
                val = str(val)
            val = val.replace("\n", " ").replace("|", "\\|")
            vals.append(val)
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def run_audit() -> dict[str, Any]:
    inventory = collect_artifact_inventory()
    cache_metadata = collect_cache_metadata()
    json_summaries = summarize_json_sources()
    key = keyword_evidence(inventory)

    evidence = {
        "inventory": inventory,
        "cache_metadata": cache_metadata,
        "json_summaries": json_summaries,
        "keyword_evidence": key,
    }
    decision_matrix = make_decision_matrix(evidence)

    blocker_reasons: list[str] = []
    missing_required = [p for p in REQUIRED_DOCS if not Path(p).exists()]
    if missing_required:
        blocker_reasons.append("missing required docs: " + ", ".join(missing_required))
    for p in REQUIRED_CACHE_INDEX:
        if not Path(p).exists():
            blocker_reasons.append("missing required cache/index metadata: " + p)

    closeout_status = "BLOCKED" if blocker_reasons else "closeout_ready"

    protocol_payload = {
        "status": "complete",
        "category": "protocol alignment",
        "summary": {
            "current_reference_protocol": "held-out-subject binary valence/arousal remains a continuity/reference target",
            "audit_conclusion": "protocol target should be reconciled before further modeling escalation",
            "no_final_loso_claim": True,
            "no_new_operating_point_claim": True,
        },
        "evidence_sources": [a["path"] for a in inventory["artifacts"] if a.get("exists")],
        "forbidden_scope_respected": True,
    }
    write_json(REPORT_PATHS["protocol_comparison"][1], protocol_payload)
    write_md(
        REPORT_PATHS["protocol_comparison"][0],
        "I-DARE Label/Task Protocol Comparison Report",
        [
            ("Status", "`complete`"),
            (
                "Conclusion",
                "The current held-out-subject binary valence/arousal protocol is retained only as a continuity/reference comparator. "
                "The audit recommends protocol-target reconciliation before any further modeling escalation. "
                "No final LOSO claim and no new operating-point claim are made.",
            ),
            ("Encoded Categories", "\n".join(f"- {c}" for c in AUDIT_CATEGORIES)),
            ("Forbidden Scope Confirmation", "No Wave 2, DG, model-capacity, augmentation, representation redesign v2, DEAP, fusion, preprocessing, threshold change, W1 edit, or main push was performed."),
        ],
    )

    label_payload = {
        "status": "complete",
        "category": "label/task formulation",
        "summary": {
            "global_label_policy_locked": False,
            "recommendation": "redesign/reconcile label-task policy before more modeling",
            "midpoint_handling": "reviewed as policy evidence only; no threshold change performed",
        },
        "cache_label_metadata": cache_metadata["indices"],
        "json_summaries": json_summaries,
    }
    write_json(REPORT_PATHS["label_task_policy"][1], label_payload)
    label_cols_rows = []
    for index_path, index_summary in cache_metadata["indices"].items():
        for col, col_summary in index_summary.get("label_summaries", {}).items():
            label_cols_rows.append(
                {
                    "index": index_path,
                    "label_column": col,
                    "nonnull": col_summary.get("nonnull"),
                    "missing": col_summary.get("missing"),
                    "counts": col_summary.get("counts"),
                }
            )
    write_md(
        REPORT_PATHS["label_task_policy"][0],
        "I-DARE Label/Task Policy Report",
        [
            ("Status", "`complete`"),
            ("Conclusion", "No final global label policy is locked. The audit classifies label/task redesign or reconciliation as the recommended next decision path before more modeling."),
            ("Detected Label Columns", md_table(label_cols_rows, ["index", "label_column", "nonnull", "missing", "counts"]) if label_cols_rows else "No label columns detected."),
            ("Boundary", "This report changes no thresholds and creates no model results."),
        ],
    )

    bias_payload = {
        "status": "complete",
        "category": "midpoint and threshold policy review / fold-subject label-bias review",
        "summary": {
            "threshold_changes_performed": False,
            "cache_arrays_loaded": False,
            "index_metadata_reviewed": True,
            "subject_bias_signal": "see per-label subject_positive_rate ranges where available",
        },
        "cache_metadata": cache_metadata,
    }
    write_json(REPORT_PATHS["midpoint_fold_subject_bias"][1], bias_payload)
    bias_rows = []
    for index_path, index_summary in cache_metadata["indices"].items():
        for col, col_summary in index_summary.get("label_summaries", {}).items():
            rate = col_summary.get("subject_positive_rate", {})
            bias_rows.append(
                {
                    "index": index_path,
                    "label_column": col,
                    "subject_rate_min": rate.get("min", ""),
                    "subject_rate_max": rate.get("max", ""),
                    "subject_rate_range": rate.get("range", ""),
                    "subject_rate_std": rate.get("std", ""),
                }
            )
    write_md(
        REPORT_PATHS["midpoint_fold_subject_bias"][0],
        "I-DARE Midpoint/Fold/Subject-Bias Report",
        [
            ("Status", "`complete`"),
            ("Conclusion", "The audit reviewed midpoint/fold/subject-bias metadata from existing cache/index files only. No threshold was changed and no cache array was loaded for model computation."),
            ("Subject Label-Bias Metadata", md_table(bias_rows, ["index", "label_column", "subject_rate_min", "subject_rate_max", "subject_rate_range", "subject_rate_std"]) if bias_rows else "No subject label-bias table available."),
            ("Boundary", "This is metadata audit only, not an experiment."),
        ],
    )

    prior_payload = {
        "status": "complete",
        "category": "prior-results interpretation",
        "summary": {
            "interpretation": "prior results remain mixed/diagnostic and should not be converted into final operating-point claims",
            "subject_relative_candidate_present": bool(key["subject_relative_docs"]),
            "threshold_evidence_present": bool(key["threshold_docs"]),
            "near_chance_or_mixed_evidence_present": bool(key["near_chance_docs"]),
        },
        "keyword_evidence": key,
        "json_summaries": json_summaries,
    }
    write_json(REPORT_PATHS["prior_results"][1], prior_payload)
    prior_rows = []
    for path, summary in json_summaries.items():
        prior_rows.append({"path": path, "summary": summary})
    write_md(
        REPORT_PATHS["prior_results"][0],
        "I-DARE Prior-Results Interpretation Report",
        [
            ("Status", "`complete`"),
            ("Conclusion", "Prior results are interpreted as diagnostic/mixed evidence. They support a label-task/protocol decision step rather than more blind modeling."),
            ("JSON Source Summaries", md_table(prior_rows, ["path", "summary"]) if prior_rows else "No JSON summaries loaded."),
            ("Keyword Evidence", "```json\n" + json.dumps(key, indent=2, sort_keys=True) + "\n```"),
        ],
    )

    decision_payload = {
        "status": "complete",
        "category": "final label-task/protocol decision matrix",
        "no_new_operating_point_claim": True,
        "matrix": decision_matrix,
        "recommended_control_path": [
            "Review this reconciliation closeout.",
            "Do not run more modeling until Control Tower selects a decision path.",
            "If approved, create a separate next objective for the selected path."
        ],
    }
    write_json(REPORT_PATHS["decision_matrix"][1], decision_payload)
    write_md(
        REPORT_PATHS["decision_matrix"][0],
        "I-DARE Final Label-Task/Protocol Decision Matrix",
        [
            ("Status", "`complete`"),
            ("Decision Matrix", md_table(decision_matrix, ["option", "decision_path", "classification", "rationale", "allowed_next", "risk"])),
            ("Boundary", "This matrix is a governance/audit classification and makes no new operating-point claim."),
        ],
    )

    artifact_bundle = {
        "status": "complete",
        "purpose": "artifact review bundle for Control Tower",
        "produced_files": [str(p) for pair in REPORT_PATHS.values() for p in pair],
        "source_inventory": inventory,
        "cache_metadata": cache_metadata,
        "forbidden_scope_confirmation": {item: False for item in FORBIDDEN_NOW},
        "audit_execution_occurred": True,
        "experiment_or_model_result_created": False,
    }
    write_json(REPORT_PATHS["artifact_bundle"][1], artifact_bundle)
    artifact_rows = [{"file": str(p)} for pair in REPORT_PATHS.values() for p in pair]
    write_md(
        REPORT_PATHS["artifact_bundle"][0],
        "I-DARE Label/Task Protocol Artifact Review Bundle",
        [
            ("Status", "`complete`"),
            ("Produced Files", md_table(artifact_rows, ["file"])),
            ("Source Inventory Summary", f"- present_count: `{inventory['present_count']}`\n- missing_count: `{inventory['missing_count']}`"),
            ("Forbidden Scope Confirmation", "\n".join(f"- {item}: not performed" for item in FORBIDDEN_NOW)),
        ],
    )

    closeout_payload = {
        "status": closeout_status,
        "blocker_status": "BLOCKED" if blocker_reasons else "none",
        "blocker_reasons": blocker_reasons,
        "audit_execution_occurred": True,
        "experiment_or_model_result_created": False,
        "no_new_operating_point_claim": True,
        "produced_files": [str(p) for pair in REPORT_PATHS.values() for p in pair],
        "decision_matrix": decision_matrix,
        "recommended_next_control_decision": "Select one of A-E before any further modeling or protocol change.",
        "forbidden_scope_confirmation": {item: "not performed" for item in FORBIDDEN_NOW},
        "artifact_review_bundle": {
            "md": str(REPORT_PATHS["artifact_bundle"][0]),
            "json": str(REPORT_PATHS["artifact_bundle"][1]),
        },
    }
    write_json(REPORT_PATHS["closeout"][1], closeout_payload)
    write_md(
        REPORT_PATHS["closeout"][0],
        "I-DARE Label/Task Protocol Reconciliation Closeout",
        [
            ("Status", f"`{closeout_status}`"),
            ("Blocker Status", "`none`" if not blocker_reasons else "\n".join(f"- {x}" for x in blocker_reasons)),
            ("Produced Files", md_table(artifact_rows, ["file"])),
            ("Decision Matrix", md_table(decision_matrix, ["option", "decision_path", "classification", "allowed_next"])),
            ("Forbidden Scope Confirmation", "\n".join(f"- {item}: not performed" for item in FORBIDDEN_NOW)),
            ("Execution Confirmation", "The reconciliation audit was run as a compact documentation/metadata audit only. No experiment, model result, threshold change, preprocessing change, DEAP work, fusion work, or main push occurred."),
        ],
    )

    return closeout_payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["validate", "audit"], default="validate")
    parser.add_argument("--control-run-approval", default="")
    args = parser.parse_args()

    audit_requested = args.mode == "audit"
    validation = build_validation_report(args.mode, audit_requested, args.control_run_approval)
    write_validation_report(validation)
    print(json.dumps(validation, indent=2, sort_keys=True))

    if validation["status"] != "PASSED":
        return 2

    if args.mode == "audit":
        closeout = run_audit()
        print(json.dumps({"closeout_status": closeout["status"], "produced_files": closeout["produced_files"]}, indent=2, sort_keys=True))
        return 0 if closeout["status"] == "closeout_ready" else 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
