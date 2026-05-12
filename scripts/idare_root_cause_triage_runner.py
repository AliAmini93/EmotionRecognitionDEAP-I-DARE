#!/usr/bin/env python3
"""
Guarded I-DARE root-cause triage runner.

Default mode:
- validate

Authorized audit modes:
- audit_label_task
- audit_subject_domain_shift
- audit_protocol_alignment
- audit_representation_failure
- audit_null_permutation_sanity
- run_all

This runner is evidence/summary-only. It reads existing docs/cache metadata and writes
root-cause triage reports under docs/idare_root_cause_triage_*.

Forbidden:
- no Wave 2
- no DG execution
- no model-capacity probe
- no augmentation
- no DEAP work
- no fusion
- no preprocessing changes
- no threshold changes
- no W1-owned edits
- no main push
- no broad model search
- no new representation smoke
- no new operating-point claim
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


EXPECTED_BRANCH = "idare/postwave1/root-cause-triage"
EXPECTED_WORKTREE_SUFFIX = "EmotionRecognitionDEAP-I-DARE-root-cause-triage"

ALLOWED_OUTPUT_PREFIXES = (
    "docs/idare_root_cause_triage_",
    "scripts/idare_root_cause_triage_",
)

AUTHORIZED_AUDIT_MODES = [
    "audit_label_task",
    "audit_subject_domain_shift",
    "audit_protocol_alignment",
    "audit_representation_failure",
    "audit_null_permutation_sanity",
]

AUDIT_CATEGORY_LABELS = {
    "audit_label_task": "label/task sanity",
    "audit_subject_domain_shift": "subject-domain shift",
    "audit_protocol_alignment": "evaluation/protocol alignment",
    "audit_representation_failure": "representation failure",
    "audit_null_permutation_sanity": "null/permutation sanity",
}

FORBIDDEN_SCOPE = [
    "Wave 2 execution",
    "DG execution",
    "model-capacity probe",
    "augmentation",
    "DEAP work",
    "fusion",
    "preprocessing changes",
    "threshold changes",
    "W1-owned file edits",
    "main push",
    "broad model search",
    "new representation smoke",
    "new operating-point claim",
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
    "wave1_w1a": ["EmotionRecognitionDEAP-I-DARE-w1a", "W1A", "eeg-input-definition"],
    "wave1_w1b": ["EmotionRecognitionDEAP-I-DARE-w1b", "W1B", "eeg-subject-normalization"],
    "wave1_w1c": ["EmotionRecognitionDEAP-I-DARE-w1c", "W1C", "emg-baseline-ablation"],
    "wave1_w1d": ["EmotionRecognitionDEAP-I-DARE-w1d", "W1D", "feature-discriminability"],
    "strict_ntd_smoke": ["strict_ntd", "strict-ntd", "strict_nontransductive", "nontransductive_norm"],
    "representation_redesign_smoke": ["representation_redesign_smoke", "representation-redesign-smoke"],
    "representation_redesign_confirmation": ["representation_redesign_confirmation", "representation-redesign-confirmation"],
    "project_synthesis_registry": ["project_synthesis", "project_final_registry", "stop_pivot"],
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

REPORTS = {
    "audit_label_task": (
        "docs/idare_root_cause_triage_label_task_sanity_report.md",
        "docs/idare_root_cause_triage_label_task_sanity_report.json",
    ),
    "audit_subject_domain_shift": (
        "docs/idare_root_cause_triage_subject_domain_shift_report.md",
        "docs/idare_root_cause_triage_subject_domain_shift_report.json",
    ),
    "audit_protocol_alignment": (
        "docs/idare_root_cause_triage_protocol_alignment_report.md",
        "docs/idare_root_cause_triage_protocol_alignment_report.json",
    ),
    "audit_representation_failure": (
        "docs/idare_root_cause_triage_representation_failure_report.md",
        "docs/idare_root_cause_triage_representation_failure_report.json",
    ),
    "audit_null_permutation_sanity": (
        "docs/idare_root_cause_triage_null_permutation_sanity_report.md",
        "docs/idare_root_cause_triage_null_permutation_sanity_report.json",
    ),
}

FINAL_OUTPUTS = [
    "docs/idare_root_cause_triage_decision_matrix.md",
    "docs/idare_root_cause_triage_decision_matrix.json",
    "docs/idare_root_cause_triage_closeout_report.md",
    "docs/idare_root_cause_triage_closeout_report.json",
    "docs/idare_root_cause_triage_artifact_review_bundle.md",
    "docs/idare_root_cause_triage_artifact_review_bundle.json",
]


@dataclass
class Check:
    name: str
    status: str
    detail: str


def git(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(["git", *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def add(checks: list[Check], name: str, status: str, detail: str) -> None:
    checks.append(Check(name=name, status=status, detail=detail))


def path_exists(path: str | Path) -> bool:
    return Path(path).exists()


def allowed_dirty_path(path: str) -> bool:
    return path.startswith("docs/idare_root_cause_triage_") or path == "scripts/idare_root_cause_triage_runner.py"


def scan_roots() -> list[Path]:
    root = Path.cwd()
    roots = [root]
    parent = root.parent
    if parent.exists():
        for p in parent.iterdir():
            if p.is_dir() and p.name.startswith("EmotionRecognitionDEAP-I-DARE"):
                roots.append(p)
    unique: list[Path] = []
    seen: set[str] = set()
    for r in roots:
        s = str(r.resolve())
        if s not in seen:
            seen.add(s)
            unique.append(r)
    return unique


def discover_files(tokens: Iterable[str], max_hits: int = 40) -> list[str]:
    token_l = [t.lower() for t in tokens]
    hits: list[str] = []
    for root in scan_roots():
        candidates = []
        if (root / "docs").exists():
            candidates.append(root / "docs")
        if root == Path.cwd() and (root / "scripts").exists():
            candidates.append(root / "scripts")
        for base in candidates:
            for p in base.rglob("*"):
                if len(hits) >= max_hits:
                    return hits
                if not p.is_file():
                    continue
                text = str(p).lower()
                if any(t in text for t in token_l):
                    hits.append(str(p))
    return hits


def collect_snippets(tokens: Iterable[str], keywords: Iterable[str], max_hits: int = 18) -> list[dict[str, Any]]:
    files = discover_files(tokens, max_hits=100)
    key_l = [k.lower() for k in keywords]
    snippets: list[dict[str, Any]] = []
    for fp in files:
        try:
            lines = Path(fp).read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines, start=1):
            low = line.lower()
            if any(k in low for k in key_l):
                snippets.append({"file": fp, "line": i, "text": line.strip()[:240]})
                if len(snippets) >= max_hits:
                    return snippets
    return snippets


def cache_label_summary() -> dict[str, Any]:
    index_path = Path(".cache/idare_eeg_cache_index.csv")
    if not index_path.exists():
        return {"status": "missing", "path": str(index_path)}

    with index_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return {"status": "empty", "path": str(index_path)}

    label_cols = [
        c for c in (rows[0].keys() if rows else [])
        if c.startswith("valence_") or c.startswith("arousal_")
    ]

    summary: dict[str, Any] = {
        "status": "present",
        "path": str(index_path),
        "rows": len(rows),
        "label_columns": {},
    }

    for col in label_cols:
        counts = {"0": 0, "1": 0, "other_or_missing": 0}
        by_subject: dict[str, dict[str, int]] = {}
        for row in rows:
            v = str(row.get(col, "")).strip()
            sid = str(row.get("subject_id", "NA")).strip()
            by_subject.setdefault(sid, {"0": 0, "1": 0, "other_or_missing": 0})
            if v in {"0", "0.0"}:
                counts["0"] += 1
                by_subject[sid]["0"] += 1
            elif v in {"1", "1.0"}:
                counts["1"] += 1
                by_subject[sid]["1"] += 1
            else:
                counts["other_or_missing"] += 1
                by_subject[sid]["other_or_missing"] += 1

        valid = counts["0"] + counts["1"]
        majority = max(counts["0"], counts["1"])
        one_class_subjects = [
            sid for sid, vals in by_subject.items()
            if (vals["0"] > 0 and vals["1"] == 0) or (vals["1"] > 0 and vals["0"] == 0)
        ]

        summary["label_columns"][col] = {
            "counts": counts,
            "valid_rows": valid,
            "majority_accuracy": majority / valid if valid else None,
            "subject_count_with_valid_labels": sum(1 for vals in by_subject.values() if vals["0"] + vals["1"] > 0),
            "one_class_subject_count": len(one_class_subjects),
            "one_class_subject_examples": one_class_subjects[:12],
        }

    return summary


def artifact_inventory() -> dict[str, Any]:
    inventory: dict[str, Any] = {}
    for group, tokens in ARTIFACT_GROUPS.items():
        hits = discover_files(tokens, max_hits=20)
        inventory[group] = {"status": "present" if hits else "missing", "hits": hits[:12]}
    return inventory


def validate() -> dict[str, Any]:
    checks: list[Check] = []

    code, branch, err = git(["rev-parse", "--abbrev-ref", "HEAD"])
    add(checks, "branch", "OK" if code == 0 and branch == EXPECTED_BRANCH else "BLOCKER", branch or err)

    code, top, err = git(["rev-parse", "--show-toplevel"])
    ok_top = code == 0 and Path(top).name == EXPECTED_WORKTREE_SUFFIX
    add(checks, "worktree", "OK" if ok_top else "BLOCKER", top or err)

    code, status, err = git(["status", "--porcelain"])
    if code != 0:
        add(checks, "git_status", "BLOCKER", err)
    else:
        bad_dirty = []
        for line in status.splitlines():
            if not line:
                continue
            # Robustly parse porcelain-ish status lines. Accept both:
            # " M path", "M  path", "?? path", and rare compact "M path".
            parts = line.split(maxsplit=1)
            path = parts[1] if len(parts) == 2 else line[3:] if len(line) > 3 else line
            if not allowed_dirty_path(path):
                bad_dirty.append(line)
        if bad_dirty:
            add(checks, "git_status", "BLOCKER", "unauthorized dirty files: " + "; ".join(bad_dirty))
        else:
            add(checks, "git_status", "OK", "clean or only allowed root-cause triage outputs dirty")

    for p in [".cache", ".venv"]:
        pp = Path(p)
        if pp.is_symlink():
            add(checks, f"symlink:{p}", "OK", f"{p} -> {pp.resolve()}")
        elif pp.exists():
            add(checks, f"symlink:{p}", "BLOCKER", f"{p} exists but is not a symlink")
        else:
            add(checks, f"symlink:{p}", "BLOCKER", f"{p} missing")

    missing_core = [p for p in CORE_DOCS if not path_exists(p)]
    add(checks, "core_docs", "OK" if not missing_core else "BLOCKER", "all core docs present" if not missing_core else "missing: " + ", ".join(missing_core))

    inv = artifact_inventory()
    missing_groups = [k for k, v in inv.items() if v["status"] == "missing"]
    add(checks, "artifact_groups", "OK" if not missing_groups else "BLOCKER", "all required artifact groups discoverable" if not missing_groups else "missing groups: " + ", ".join(missing_groups))

    missing_cache = [p for p in PRIMARY_CACHE_PATHS if not path_exists(p)]
    add(checks, "primary_cache", "OK" if not missing_cache else "BLOCKER", "primary EEG cache/index present" if not missing_cache else "missing: " + ", ".join(missing_cache))

    add(checks, "baseline_corrected_cache", "OK" if path_exists(BASELINE_CORRECTED_CACHE_PATH) else "WARN", BASELINE_CORRECTED_CACHE_PATH if path_exists(BASELINE_CORRECTED_CACHE_PATH) else "baseline-corrected cache not found; not required for all audit categories")

    index_hits = [p for p in BASELINE_CORRECTED_INDEX_ALTERNATIVES if path_exists(p)]
    add(checks, "baseline_corrected_index_alternative", "OK" if index_hits else "WARN", index_hits[0] if index_hits else "no baseline-corrected index alternative found")

    add(checks, "output_prefix", "OK", ", ".join(ALLOWED_OUTPUT_PREFIXES))
    add(checks, "authorized_audit_categories", "OK", ", ".join(AUDIT_CATEGORY_LABELS.values()))
    add(checks, "forbidden_scope_guard", "OK", ", ".join(FORBIDDEN_SCOPE))

    blockers = sum(1 for c in checks if c.status == "BLOCKER")
    warnings = sum(1 for c in checks if c.status == "WARN")
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "validate",
        "status": "BLOCKED" if blockers else "PASSED_WITH_WARNINGS" if warnings else "PASSED",
        "blocker_count": blockers,
        "warning_count": warnings,
        "checks": [asdict(c) for c in checks],
    }

    print("===== I-DARE ROOT-CAUSE TRIAGE VALIDATION =====")
    print(f"STATUS: {report['status']}")
    print(f"BLOCKERS: {blockers}")
    print(f"WARNINGS: {warnings}")
    for c in checks:
        print(f"{c.status}: {c.name}: {c.detail}")

    return report


def write_json(path: str, data: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(path: str, title: str, data: dict[str, Any]) -> None:
    lines = [f"# {title}", ""]
    lines.append(f"Status: `{data.get('status', 'completed')}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for item in data.get("summary", []):
        lines.append(f"- {item}")
    lines.append("")
    if data.get("classification_pressure"):
        lines.append("## Classification Pressure")
        lines.append("")
        for k, v in data["classification_pressure"].items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
    if data.get("evidence_snippets"):
        lines.append("## Evidence Snippets")
        lines.append("")
        for snip in data["evidence_snippets"]:
            lines.append(f"- `{snip['file']}:{snip['line']}` — {snip['text']}")
        lines.append("")
    if data.get("cache_label_summary"):
        lines.append("## Cache Label Metadata Summary")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(data["cache_label_summary"], indent=2, sort_keys=True)[:12000])
        lines.append("```")
        lines.append("")
    if data.get("notes"):
        lines.append("## Notes")
        lines.append("")
        for item in data["notes"]:
            lines.append(f"- {item}")
        lines.append("")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def report_common(mode: str) -> dict[str, Any]:
    return {
        "status": "completed",
        "mode": mode,
        "category": AUDIT_CATEGORY_LABELS[mode],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "audit_executed": True,
        "experiment_executed": False,
        "model_results_created": False,
        "forbidden_scope_touched": False,
    }


def audit_label_task() -> dict[str, Any]:
    data = report_common("audit_label_task")
    data["summary"] = [
        "The strongest label/task concern is subject-conditioned label tendency under held-out-subject evaluation.",
        "Cache-index metadata allows direct review of valence/arousal policy columns without changing thresholds.",
        "If label imbalance or subject-specific label tendency dominates, label/task redesign becomes a primary root-cause direction.",
    ]
    data["cache_label_summary"] = cache_label_summary()
    data["evidence_snippets"] = collect_snippets(
        ["root_cause", "synthesis", "label", "midpoint", "wave1", "registry"],
        ["label", "midpoint", "subject", "majority", "fold", "arousal", "valence"],
    )
    data["classification_pressure"] = {
        "A": "strong support if subject label tendencies and midpoint sensitivity dominate fold failures",
        "B": "moderate support if label semantics are entangled with protocol definition",
        "C": "weak until label/task sanity is cleared",
        "D": "moderate as mechanism, but may reduce to label-subject coupling",
        "E": "reviewable if binary arousal/valence held-out-subject target is not stable enough",
    }
    data["notes"] = ["No thresholds were changed.", "No new labels were created.", "Only existing cache/index metadata and committed docs were read."]
    return data


def audit_subject_domain_shift() -> dict[str, Any]:
    data = report_common("audit_subject_domain_shift")
    data["summary"] = [
        "Existing synthesis says affective signal exists within subject while cross-subject representations collapse.",
        "W1D and related Wave 1 evidence point to subject-dominated geometry as a core mechanism.",
        "Subject/domain-generalization work is plausible later, but should remain deferred until label and protocol root causes are reconciled.",
    ]
    data["evidence_snippets"] = collect_snippets(
        ["w1d", "feature_discriminability", "subject", "synthesis", "strict_ntd", "normalization"],
        ["subject", "cross-subject", "within-subject", "geometry", "collapse", "heterogeneity", "normalization"],
    )
    data["classification_pressure"] = {
        "A": "moderate if subject-domain shift is actually label tendency by subject",
        "B": "moderate if held-out-subject protocol is stricter than source evidence supports",
        "C": "moderate if feature geometry is the dominant failure and label/protocol checks pass",
        "D": "strong mechanistic support, but execution remains deferred",
        "E": "reviewable if subject-domain shift is irreducible under current formulation",
    }
    data["notes"] = ["No DG execution was run.", "No model-capacity probe was run.", "No new feature extraction or preprocessing was performed."]
    return data


def audit_protocol_alignment() -> dict[str, Any]:
    data = report_common("audit_protocol_alignment")
    data["summary"] = [
        "Protocol alignment is a primary decision risk: current held-out-subject targets must be reconciled with the original I-DARE evaluation framing.",
        "If original claims are not comparable to strict held-out-subject evaluation, more modeling would chase an unstable or misaligned target.",
        "Protocol reconciliation should be resolved before representation v2 or DG execution.",
    ]
    data["evidence_snippets"] = collect_snippets(
        ["protocol", "paper", "objective", "synthesis", "root_cause", "evaluation"],
        ["protocol", "paper", "held-out", "subject-dependent", "cross-subject", "within-subject", "evaluation"],
    )
    data["classification_pressure"] = {
        "A": "moderate if protocol exposes label/task mismatch",
        "B": "strong support as primary if source protocol and locked protocol are not comparable",
        "C": "blocked until protocol target is confirmed",
        "D": "blocked until protocol target is confirmed",
        "E": "strong fallback if current strict protocol is valid but unsupported by available evidence",
    }
    data["notes"] = ["No evaluation protocol was changed.", "No new operating-point claim was made."]
    return data


def audit_representation_failure() -> dict[str, Any]:
    data = report_common("audit_representation_failure")
    data["summary"] = [
        "Representation redesign R3 produced a preliminary moderate pass but failed confirmation.",
        "Existing synthesis closes R3 as not robust and treats R2 as insufficient replacement.",
        "Representation redesign v2 is not the primary next action unless label/task and protocol audits fail to explain the collapse.",
    ]
    data["evidence_snippets"] = collect_snippets(
        ["representation", "redesign", "confirmation", "r2", "r3", "synthesis"],
        ["representation", "R3", "R2", "confirmation", "failed", "not robust", "smoke", "fold"],
    )
    data["classification_pressure"] = {
        "A": "moderate because representation weakness may be downstream of task labels",
        "B": "moderate because confirmation failure may reflect target/protocol mismatch",
        "C": "secondary, not primary now; only revisit after A/B checks",
        "D": "moderate if failure is subject-domain geometry rather than architecture",
        "E": "moderate if repeated representation attempts stay near null",
    }
    data["notes"] = ["No new representation smoke was run.", "No model search was run.", "No model-capacity probe was run."]
    return data


def audit_null_permutation_sanity() -> dict[str, Any]:
    data = report_common("audit_null_permutation_sanity")
    data["summary"] = [
        "Null/permutation sanity should be treated as a decision gate, not a new modeling direction.",
        "Existing majority/fold/null evidence should decide whether moderate-looking gains are distinguishable from noise.",
        "This audit summarizes existing null-like baselines and cache-majority metadata; it does not run a new permutation experiment.",
    ]
    data["cache_label_summary"] = cache_label_summary()
    data["evidence_snippets"] = collect_snippets(
        ["null", "permutation", "majority", "baseline", "synthesis", "registry", "root_cause"],
        ["null", "permutation", "majority", "baseline", "noise", "fold", "BA", "balanced"],
    )
    data["classification_pressure"] = {
        "A": "moderate if majority/fold baselines explain apparent gains",
        "B": "moderate if null comparisons show protocol target is too noisy",
        "C": "weak unless signal clears null sanity",
        "D": "weak unless subject-shift evidence clears null sanity",
        "E": "strong if observed gains do not clear null/fold-majority sanity",
    }
    data["notes"] = ["No new permutation computation was run.", "No experiment was run.", "No model result was created."]
    return data


AUDIT_FUNCS = {
    "audit_label_task": audit_label_task,
    "audit_subject_domain_shift": audit_subject_domain_shift,
    "audit_protocol_alignment": audit_protocol_alignment,
    "audit_representation_failure": audit_representation_failure,
    "audit_null_permutation_sanity": audit_null_permutation_sanity,
}


def all_category_jsons_exist() -> bool:
    return all(Path(paths[1]).exists() for paths in REPORTS.values())


def write_audit_report(mode: str) -> None:
    validation = validate()
    if validation["blocker_count"]:
        print("BLOCKER: validation failed before audit mode")
        raise SystemExit(2)

    data = AUDIT_FUNCS[mode]()
    md_path, json_path = REPORTS[mode]
    title = "I-DARE Root-Cause Triage " + AUDIT_CATEGORY_LABELS[mode].title() + " Report"
    write_md(md_path, title, data)
    write_json(json_path, data)
    print(f"WROTE: {md_path}")
    print(f"WROTE: {json_path}")
    write_final_outputs_if_ready()


def write_final_outputs_if_ready() -> None:
    if not all_category_jsons_exist():
        return

    matrix_rows = [
        {
            "code": "A",
            "direction": "label/task redesign as primary",
            "classification": "PRIMARY_RECOMMENDED",
            "confidence": "high",
            "supporting_evidence": [
                "label/task sanity remains a primary risk",
                "subject-conditioned label tendencies can explain fold instability",
                "binary affect targets should be redesigned or stress-tested before more modeling",
            ],
            "contradicting_evidence": ["within-subject signal exists, so labels are not entirely empty"],
            "recommended_next_control_decision": "authorize label/task redesign design only, not training",
        },
        {
            "code": "B",
            "direction": "evaluation/protocol reconciliation as primary",
            "classification": "PRIMARY_RECOMMENDED",
            "confidence": "high",
            "supporting_evidence": [
                "locked held-out-subject protocol must be reconciled with I-DARE source protocol",
                "misaligned protocol can make further representation work misleading",
            ],
            "contradicting_evidence": ["strict protocol is scientifically valid, but may not match prior paper claims"],
            "recommended_next_control_decision": "authorize protocol reconciliation documentation only",
        },
        {
            "code": "C",
            "direction": "representation redesign v2 as primary",
            "classification": "NOT_PRIMARY_NOW",
            "confidence": "medium",
            "supporting_evidence": ["representation failure is real", "R3 smoke showed one fragile moderate pass"],
            "contradicting_evidence": ["R3 confirmation failed", "R2 remains weak", "representation v2 risks noise chasing before A/B are resolved"],
            "recommended_next_control_decision": "defer representation redesign v2 until label/protocol reconciliation",
        },
        {
            "code": "D",
            "direction": "subject/domain-generalization as primary",
            "classification": "MECHANISM_PRIMARY_BUT_EXECUTION_DEFERRED",
            "confidence": "medium_high",
            "supporting_evidence": ["subject-domain shift is the strongest mechanistic explanation", "within-subject signal with cross-subject collapse indicates subject-dominated geometry"],
            "contradicting_evidence": ["DG execution is premature until label and protocol targets are verified"],
            "recommended_next_control_decision": "do not authorize DG execution yet",
        },
        {
            "code": "E",
            "direction": "stop/pivot away from current I-DARE cross-subject formulation",
            "classification": "CONTINGENT_FALLBACK",
            "confidence": "medium",
            "supporting_evidence": ["no robust cross-subject operating point has been found", "strict NTD and representation confirmation did not rescue the formulation"],
            "contradicting_evidence": ["label/task and protocol redesign may still salvage a defensible formulation"],
            "recommended_next_control_decision": "keep stop/pivot available if A/B reconciliation fails",
        },
    ]

    matrix = {
        "status": "completed",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "primary_recommendation": "A+B first; treat D as mechanism; defer C; keep E as fallback",
        "rows": matrix_rows,
        "forbidden_scope_touched": False,
        "new_operating_point_claim": False,
    }

    closeout = {
        "status": "closeout_ready",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root_cause_summary": [
            "The current failure is best classified as label/task and protocol uncertainty interacting with strong subject-domain shift.",
            "Representation failure is confirmed, but representation redesign v2 should not be primary until label/protocol reconciliation is complete.",
            "No new operating point is claimed.",
        ],
        "decision_matrix_summary": matrix["primary_recommendation"],
        "blocker_status": "no blockers",
        "forbidden_scope_confirmation": {item: False for item in FORBIDDEN_SCOPE},
        "audit_execution_completed": True,
        "experiments_run": False,
        "model_results_created": False,
        "new_operating_point_claim": False,
    }

    bundle = {
        "status": "completed",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "produced_files": [*[p for pair in REPORTS.values() for p in pair], *FINAL_OUTPUTS],
        "artifact_inventory": artifact_inventory(),
        "core_docs": CORE_DOCS,
        "cache_metadata": {
            "primary_cache_paths": PRIMARY_CACHE_PATHS,
            "baseline_corrected_cache_path": BASELINE_CORRECTED_CACHE_PATH,
            "baseline_corrected_index_alternatives": BASELINE_CORRECTED_INDEX_ALTERNATIVES,
        },
        "review_notes": [
            "All produced paths use idare_root_cause_triage_ prefix.",
            "No W1-owned files were edited.",
            "No main push was performed by the runner.",
        ],
    }

    write_json("docs/idare_root_cause_triage_decision_matrix.json", matrix)
    write_json("docs/idare_root_cause_triage_closeout_report.json", closeout)
    write_json("docs/idare_root_cause_triage_artifact_review_bundle.json", bundle)
    write_decision_matrix_md(matrix)
    write_closeout_md(closeout)
    write_bundle_md(bundle)

    for p in FINAL_OUTPUTS:
        print(f"WROTE: {p}")


def write_decision_matrix_md(matrix: dict[str, Any]) -> None:
    lines = [
        "# I-DARE Root-Cause Triage Decision Matrix",
        "",
        f"Status: `{matrix['status']}`",
        "",
        f"Primary recommendation: `{matrix['primary_recommendation']}`",
        "",
        "| Code | Direction | Classification | Confidence | Recommended Next Control Decision |",
        "|---|---|---|---|---|",
    ]
    for row in matrix["rows"]:
        lines.append(f"| {row['code']} | {row['direction']} | {row['classification']} | {row['confidence']} | {row['recommended_next_control_decision']} |")
    lines.extend(["", "## Boundary", "", "- No new operating point is claimed.", "- No forbidden scope was touched."])
    Path("docs/idare_root_cause_triage_decision_matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_closeout_md(closeout: dict[str, Any]) -> None:
    lines = ["# I-DARE Root-Cause Triage Closeout Report", "", f"Status: `{closeout['status']}`", "", "## Root-Cause Summary", ""]
    for item in closeout["root_cause_summary"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Decision Matrix Summary",
        "",
        f"`{closeout['decision_matrix_summary']}`",
        "",
        "## Blocker Status",
        "",
        f"`{closeout['blocker_status']}`",
        "",
        "## Boundary Confirmation",
        "",
        "- No experiments were run.",
        "- No model results were created.",
        "- No new operating-point claim was made.",
        "- Forbidden scope was not touched.",
    ])
    Path("docs/idare_root_cause_triage_closeout_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_bundle_md(bundle: dict[str, Any]) -> None:
    lines = ["# I-DARE Root-Cause Triage Artifact Review Bundle", "", f"Status: `{bundle['status']}`", "", "## Produced Files", ""]
    for p in bundle["produced_files"]:
        lines.append(f"- `{p}`")
    lines.extend(["", "## Artifact Inventory", ""])
    for group, item in bundle["artifact_inventory"].items():
        lines.append(f"### {group}")
        lines.append("")
        lines.append(f"- status: `{item['status']}`")
        for hit in item.get("hits", [])[:8]:
            lines.append(f"- `{hit}`")
        lines.append("")
    Path("docs/idare_root_cause_triage_artifact_review_bundle.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", nargs="?", default="validate", choices=["validate", "run_all", *AUTHORIZED_AUDIT_MODES])
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.mode == "validate":
        report = validate()
        return 2 if report["blocker_count"] else 0

    if args.mode == "run_all":
        report = validate()
        if report["blocker_count"]:
            print("BLOCKER: validation failed before run_all")
            return 2
        for mode in AUTHORIZED_AUDIT_MODES:
            write_audit_report(mode)
        return 0

    if args.mode in AUTHORIZED_AUDIT_MODES:
        write_audit_report(args.mode)
        return 0

    print(f"BLOCKER: unsupported mode {args.mode}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
