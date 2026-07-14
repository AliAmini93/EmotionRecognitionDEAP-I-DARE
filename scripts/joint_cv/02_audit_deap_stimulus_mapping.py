#!/usr/bin/env python3
"""Audit the provenance of DEAP stimulus identity and trial order.

This is a read-only scientific audit. It does not train models, construct
Joint-CV folds, modify datasets/caches, or alter Git state.

The key question is whether the local evidence contains a verified mapping:
    (subject_id, physical_trial_index) -> stimulus_id / video_id
rather than merely treating the row position 0..39 as a shared stimulus ID.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_REPO = Path("/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE")
DEFAULT_DEAP = Path("/mnt/HDD/AliWorks/DEAP")
EXPECTED_BRANCH = "joint-cv-capacity-audit"

TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".csv", ".sh", ".yaml", ".yml"}
MAPPING_NAME_TERMS = (
    "participant_ratings", "video_list", "video_order", "stimulus_order",
    "trial_order", "experiment_id", "playlist", "sequence", "metadata",
)
AUTHORITATIVE_COLUMN_SETS = (
    {"subject_id", "trial_id", "stimulus_id"},
    {"participant_id", "trial", "experiment_id"},
    {"participant", "trial", "video_id"},
)
SUSPICIOUS_ASSIGNMENT_PATTERNS = (
    re.compile(
        r'["\']stimulus_id["\']\s*:\s*'
        r'(?:int\()?(?:trial|trial_i|trial_idx|trial_index|i|j)'
        r'(?:\s*\+\s*1)?(?:\))?',
        re.I,
    ),
    re.compile(
        r'\bstimulus_id\s*=\s*'
        r'(?:int\()?(?:trial|trial_i|trial_idx|trial_index|i|j)'
        r'(?:\s*\+\s*1)?(?:\))?',
        re.I,
    ),
)
MAPPING_EVIDENCE_PATTERNS = (
    re.compile(r"participant_ratings", re.I),
    re.compile(r"experiment_id", re.I),
    re.compile(r"video[_ -]?id", re.I),
    re.compile(r"stimulus[_ -]?mapping", re.I),
    re.compile(r"trial[_ -]?to[_ -]?(?:video|stimulus)", re.I),
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, default=DEFAULT_REPO)
    p.add_argument("--deap-root", type=Path, default=DEFAULT_DEAP)
    p.add_argument("--out-dir", type=Path, default=None)
    p.add_argument("--overwrite", action="store_true")
    return p.parse_args()


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git(repo: Path, *args: str) -> str:
    result = run(["git", *args], repo)
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed:\n{result.stderr.strip()}"
        )
    return result.stdout


def safe_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): safe_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [safe_json(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


def ensure_outputs(out_dir: Path, overwrite: bool) -> dict[str, Path]:
    paths = {
        "md": out_dir / "deap_stimulus_mapping_provenance_audit.md",
        "json": out_dir / "deap_stimulus_mapping_provenance_audit.json",
        "evidence": out_dir / "deap_stimulus_mapping_code_evidence.csv",
        "correction_md": out_dir / "manifest_prerequisites_audit_correction.md",
        "correction_json": out_dir / "manifest_prerequisites_audit_correction.json",
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    if not overwrite:
        existing = [p for p in paths.values() if p.exists()]
        if existing:
            raise FileExistsError(
                "Refusing to overwrite existing outputs:\n"
                + "\n".join(f"- {p}" for p in existing)
            )
    return paths


def inspect_csv_header(path: Path) -> list[str]:
    try:
        return [str(c).strip().lower() for c in pd.read_csv(path, nrows=0).columns]
    except Exception:
        return []


def scan_local_mapping_files(deap_root: Path, repo: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    roots = [
        ("deap_dataset_root", deap_root),
        ("repository", repo),
    ]

    for root_kind, root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if any(part in {".git", ".venv", "__pycache__"} for part in path.parts):
                continue
            if path.suffix.lower() == ".dat":
                continue

            name_lower = path.name.lower()
            name_hits = [term for term in MAPPING_NAME_TERMS if term in name_lower]
            columns: list[str] = []
            column_match = False

            if path.suffix.lower() in {".csv", ".tsv"}:
                columns = inspect_csv_header(path)
                colset = set(columns)
                column_match = any(req <= colset for req in AUTHORITATIVE_COLUMN_SETS)

            if not name_hits and not column_match:
                continue

            authoritative_location = root_kind == "deap_dataset_root"
            rows.append(
                {
                    "root_kind": root_kind,
                    "path": str(path),
                    "relative_path": str(path.relative_to(root)),
                    "size_bytes": path.stat().st_size,
                    "name_hits": ";".join(name_hits),
                    "columns": ";".join(columns[:50]),
                    "authoritative_column_match": column_match,
                    "outside_project_derived_outputs": authoritative_location,
                    "candidate_strength": (
                        "strong"
                        if authoritative_location and column_match
                        else "medium"
                        if authoritative_location and name_hits
                        else "project-derived-or-weak"
                    ),
                }
            )
    return rows


def current_candidate_paths(repo: Path) -> list[Path]:
    candidates: set[Path] = set()
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", ".venv", ".cache", "__pycache__"} for part in path.parts):
            continue
        lower = str(path.relative_to(repo)).lower()
        if "deap" not in lower:
            continue
        if "stimulus" in lower or "prior_baseline" in lower:
            if path.suffix.lower() in TEXT_SUFFIXES:
                candidates.add(path)
    return sorted(candidates)


def historical_candidate_paths(repo: Path) -> list[str]:
    raw = git(
        repo,
        "log",
        "--all",
        "--pretty=format:",
        "--name-only",
        "--",
        "*deap*stimulus*",
        "*prior_baselines_no_global*",
    )
    return sorted(
        {
            line.strip()
            for line in raw.splitlines()
            if line.strip() and Path(line.strip()).suffix.lower() in TEXT_SUFFIXES
        }
    )


def latest_blob_for_path(repo: Path, path: str) -> tuple[str | None, str | None]:
    sha = git(repo, "log", "--all", "-1", "--format=%H", "--", path).strip()
    if not sha:
        return None, None
    result = run(["git", "show", f"{sha}:{path}"], repo)
    if result.returncode != 0:
        return sha, None
    return sha, result.stdout


def line_excerpt(text: str, line_no: int, radius: int = 4) -> str:
    lines = text.splitlines()
    start = max(0, line_no - 1 - radius)
    end = min(len(lines), line_no + radius)
    return "\n".join(
        f"{i + 1}: {lines[i]}" for i in range(start, end)
    )


def analyze_text(
    artifact_path: str,
    text: str,
    source_kind: str,
    commit_sha: str | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str]] = set()

    for line_no, line in enumerate(text.splitlines(), start=1):
        line_lower = line.lower()
        categories: list[str] = []

        if "stimulus_id" in line_lower:
            categories.append("stimulus_id_reference")
        if "trial_id" in line_lower or "trial_idx" in line_lower or "trial_index" in line_lower:
            categories.append("trial_index_reference")
        if any(p.search(line) for p in MAPPING_EVIDENCE_PATTERNS):
            categories.append("mapping_source_reference")
        if any(p.search(line) for p in SUSPICIOUS_ASSIGNMENT_PATTERNS):
            categories.append("trial_position_used_as_stimulus_id")

        for category in categories:
            key = (artifact_path, line_no, category)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "artifact_path": artifact_path,
                    "source_kind": source_kind,
                    "commit_sha": commit_sha or "",
                    "line_number": line_no,
                    "category": category,
                    "line": line.strip(),
                    "excerpt": line_excerpt(text, line_no),
                }
            )

    return rows


def inspect_candidate_code(repo: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    evidence: list[dict[str, Any]] = []
    artifact_summary: list[dict[str, Any]] = []

    current_paths = current_candidate_paths(repo)
    current_rel = {str(p.relative_to(repo)) for p in current_paths}
    historical_paths = historical_candidate_paths(repo)

    all_paths = sorted(current_rel | set(historical_paths))

    for rel in all_paths:
        current_path = repo / rel
        text: str | None = None
        source_kind = ""
        sha: str | None = None

        if current_path.exists():
            try:
                text = current_path.read_text(encoding="utf-8", errors="ignore")
                source_kind = "current_worktree"
            except Exception:
                text = None

        if text is None:
            sha, text = latest_blob_for_path(repo, rel)
            source_kind = "git_history"

        if text is None:
            continue

        rows = analyze_text(rel, text, source_kind, sha)
        evidence.extend(rows)

        categories = sorted({r["category"] for r in rows})
        artifact_summary.append(
            {
                "artifact_path": rel,
                "source_kind": source_kind,
                "commit_sha": sha or "",
                "categories": categories,
                "suspicious_trial_position_assignment": (
                    "trial_position_used_as_stimulus_id" in categories
                ),
                "mapping_source_reference": (
                    "mapping_source_reference" in categories
                ),
            }
        )

    return evidence, artifact_summary


def read_previous_audit(repo: Path) -> dict[str, Any]:
    path = repo / "docs" / "joint_cv" / "manifest_prerequisites_audit.json"
    if not path.exists():
        return {"path": str(path), "exists": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {"path": str(path), "exists": True, "data": data}
    except Exception as exc:
        return {"path": str(path), "exists": True, "error": repr(exc)}


def classify(
    local_candidates: list[dict[str, Any]],
    code_evidence: list[dict[str, Any]],
    artifact_summary: list[dict[str, Any]],
) -> dict[str, Any]:
    strong_authoritative = [
        r
        for r in local_candidates
        if r["root_kind"] == "deap_dataset_root"
        and r["authoritative_column_match"]
    ]
    medium_authoritative = [
        r
        for r in local_candidates
        if r["root_kind"] == "deap_dataset_root"
        and r["candidate_strength"] == "medium"
    ]
    position_assumptions = [
        r
        for r in code_evidence
        if r["category"] == "trial_position_used_as_stimulus_id"
    ]
    mapping_refs = [
        r
        for r in code_evidence
        if r["category"] == "mapping_source_reference"
    ]

    if strong_authoritative:
        verdict = "POTENTIALLY_VERIFIABLE_MAPPING_FOUND"
        deap_ready = False
        reason = (
            "At least one local dataset-level file has a plausible subject/trial/"
            "stimulus mapping schema. Its completeness and semantics must still be "
            "validated before DEAP Joint-CV folds are built."
        )
    elif medium_authoritative:
        verdict = "POTENTIAL_METADATA_FOUND_NEEDS_SCHEMA_REVIEW"
        deap_ready = False
        reason = (
            "Dataset-level files with mapping-related names were found, but no "
            "verified mapping schema was established."
        )
    elif position_assumptions:
        verdict = "UNVERIFIED_TRIAL_POSITION_AS_STIMULUS_ID"
        deap_ready = False
        reason = (
            "Project code appears to use the DEAP row/trial position as stimulus_id, "
            "while no authoritative local mapping from participant trial position to "
            "video/stimulus identity was found. Previous DEAP stimulus-only results "
            "must therefore be treated as relying on an unverified alignment assumption."
        )
    elif mapping_refs:
        verdict = "MAPPING_REFERENCED_BUT_SOURCE_NOT_VERIFIED"
        deap_ready = False
        reason = (
            "Project text/code refers to a mapping source, but the authoritative mapping "
            "file was not verified locally."
        )
    else:
        verdict = "NO_VERIFIED_DEAP_STIMULUS_MAPPING"
        deap_ready = False
        reason = (
            "No authoritative local mapping from DEAP subject/trial position to "
            "stimulus identity was found."
        )

    return {
        "verdict": verdict,
        "deap_stimulus_aware_manifest_ready": deap_ready,
        "reason": reason,
        "strong_authoritative_candidates": len(strong_authoritative),
        "medium_authoritative_candidates": len(medium_authoritative),
        "trial_position_assignment_evidence_count": len(position_assumptions),
        "mapping_source_reference_count": len(mapping_refs),
        "artifacts_reviewed": len(artifact_summary),
    }


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
    deap = args.deap_root.resolve()
    out_dir = (args.out_dir or repo / "docs" / "joint_cv").resolve()
    outputs = ensure_outputs(out_dir, args.overwrite)

    branch = git(repo, "branch", "--show-current").strip()
    head = git(repo, "rev-parse", "HEAD").strip()
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Expected branch {EXPECTED_BRANCH!r}, found {branch!r}. "
            "No output was written."
        )

    local_candidates = scan_local_mapping_files(deap, repo)
    code_evidence, artifact_summary = inspect_candidate_code(repo)
    previous = read_previous_audit(repo)
    assessment = classify(local_candidates, code_evidence, artifact_summary)

    previous_idare_ready = False
    previous_deap_status = None
    previous_joint_ready = None
    if previous.get("exists") and isinstance(previous.get("data"), dict):
        data = previous["data"]
        previous_idare_ready = bool(
            data.get("decision", {}).get("idare_manifest_ready")
        )
        previous_joint_ready = data.get("decision", {}).get(
            "joint_cv_fold_construction_ready"
        )
        previous_deap_status = (
            data.get("deap", {})
            .get("stimulus_mapping_assessment", {})
            .get("status")
        )

    corrected = {
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "previous_audit_path": previous.get("path"),
        "previous_deap_mapping_status": previous_deap_status,
        "previous_joint_cv_ready": previous_joint_ready,
        "correction_reason": (
            "A status of needs_manual_review is not equivalent to verified. "
            "The previous Boolean decision used a too-permissive condition."
        ),
        "idare_manifest_ready": previous_idare_ready,
        "deap_stimulus_aware_manifest_ready": assessment[
            "deap_stimulus_aware_manifest_ready"
        ],
        "deap_joint_cv_fold_construction_ready": False,
        "idare_joint_cv_fold_construction_ready": previous_idare_ready,
        "combined_deap_idare_joint_cv_ready": (
            previous_idare_ready
            and assessment["deap_stimulus_aware_manifest_ready"]
        ),
        "deap_verdict": assessment["verdict"],
        "remaining_critical_uncertainty": (
            "Verified DEAP mapping from subject-specific trial position to "
            "common video/stimulus identity and presentation order."
        ),
    }

    report = {
        "audit_type": "deap_stimulus_mapping_provenance",
        "read_only": True,
        "repository": str(repo),
        "branch": branch,
        "head": head,
        "local_mapping_candidates": local_candidates,
        "artifact_summary": artifact_summary,
        "code_evidence": code_evidence,
        "assessment": assessment,
        "correction": corrected,
    }

    outputs["json"].write_text(
        json.dumps(safe_json(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    outputs["correction_json"].write_text(
        json.dumps(safe_json(corrected), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    write_csv(outputs["evidence"], code_evidence)

    suspicious = [
        row
        for row in code_evidence
        if row["category"] == "trial_position_used_as_stimulus_id"
    ]
    mapping_refs = [
        row
        for row in code_evidence
        if row["category"] == "mapping_source_reference"
    ]

    md = [
        "# DEAP Stimulus-Mapping Provenance Audit",
        "",
        "Read-only audit. No training or fold construction was performed.",
        "",
        "## Result",
        "",
        f"- Verdict: **{assessment['verdict']}**",
        f"- DEAP stimulus-aware manifest ready: "
        f"`{assessment['deap_stimulus_aware_manifest_ready']}`",
        f"- Strong authoritative local candidates: "
        f"`{assessment['strong_authoritative_candidates']}`",
        f"- Trial-position-as-stimulus assignment evidence: "
        f"`{assessment['trial_position_assignment_evidence_count']}`",
        "",
        assessment["reason"],
        "",
        "## Scientific Interpretation",
        "",
        "A DEAP physical-trial row can be identified as `(subject_id, row_index)`, "
        "but Strict Joint subject–stimulus CV additionally requires a verified "
        "common stimulus identity across subjects. A project script assigning "
        "`stimulus_id = trial_index` is not by itself evidence that row positions "
        "represent the same video for every participant.",
        "",
        "## Dataset-Level Mapping Candidates",
        "",
        md_table(
            local_candidates,
            [
                "root_kind", "relative_path", "candidate_strength",
                "authoritative_column_match", "name_hits", "columns",
            ],
        ),
        "",
        "## Trial-Position Assignment Evidence",
        "",
        md_table(
            suspicious[:100],
            [
                "artifact_path", "source_kind", "commit_sha",
                "line_number", "line",
            ],
        ),
        "",
        "## Mapping-Source References",
        "",
        md_table(
            mapping_refs[:100],
            [
                "artifact_path", "source_kind", "commit_sha",
                "line_number", "line",
            ],
        ),
        "",
        "## Corrected Readiness",
        "",
        f"- I-DARE manifest ready: `{corrected['idare_manifest_ready']}`",
        f"- I-DARE Joint-CV fold construction ready: "
        f"`{corrected['idare_joint_cv_fold_construction_ready']}`",
        f"- DEAP stimulus-aware manifest ready: "
        f"`{corrected['deap_stimulus_aware_manifest_ready']}`",
        f"- DEAP Joint-CV fold construction ready: "
        f"`{corrected['deap_joint_cv_fold_construction_ready']}`",
        f"- Combined DEAP+I-DARE Joint-CV ready: "
        f"`{corrected['combined_deap_idare_joint_cv_ready']}`",
        "",
        "## Required Next Evidence",
        "",
        "Locate and verify an authoritative DEAP mapping such as participant ratings "
        "or experiment metadata containing participant/subject ID, trial or "
        "presentation order, and experiment/video/stimulus ID. Until then, DEAP "
        "stimulus-held-out and Strict Joint results must remain blocked.",
        "",
    ]
    outputs["md"].write_text("\n".join(md), encoding="utf-8")

    correction_md = [
        "# Correction to Manifest Prerequisites Audit",
        "",
        "The earlier readiness decision was too permissive.",
        "",
        f"- Earlier DEAP mapping status: `{previous_deap_status}`",
        f"- Earlier combined Joint-CV ready value: `{previous_joint_ready}`",
        "- Correct rule: only a **verified** DEAP mapping may set DEAP "
        "stimulus-aware readiness to true.",
        f"- Corrected DEAP verdict: **{assessment['verdict']}**",
        f"- Corrected DEAP Joint-CV readiness: `False`",
        f"- I-DARE readiness remains: `{previous_idare_ready}`",
        "",
        "The earlier 38 repository hits were mostly generic mentions of DEAP "
        "trials/windowing and do not constitute a verified subject-trial-to-video "
        "mapping.",
        "",
    ]
    outputs["correction_md"].write_text(
        "\n".join(correction_md),
        encoding="utf-8",
    )

    print("DEAP stimulus-mapping provenance audit completed.")
    print(f"Branch: {branch}")
    print(f"HEAD: {head}")
    print(f"Local mapping candidates: {len(local_candidates)}")
    print(f"Artifacts reviewed: {assessment['artifacts_reviewed']}")
    print(
        "Trial-position assignment evidence:",
        assessment["trial_position_assignment_evidence_count"],
    )
    print(f"DEAP verdict: {assessment['verdict']}")
    print(
        "DEAP Joint-CV fold construction ready:",
        corrected["deap_joint_cv_fold_construction_ready"],
    )
    print(
        "I-DARE Joint-CV fold construction ready:",
        corrected["idare_joint_cv_fold_construction_ready"],
    )
    print(
        "Combined DEAP+I-DARE Joint-CV ready:",
        corrected["combined_deap_idare_joint_cv_ready"],
    )
    print(f"Report: {outputs['md']}")
    print(f"Correction: {outputs['correction_md']}")


if __name__ == "__main__":
    main()

