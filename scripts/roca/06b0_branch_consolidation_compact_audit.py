#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(".")
PREFIX = ROOT / "docs/roca/idare_06b0_branch_consolidation_compact_audit_current"
TARGET = "origin/roca-idare-killtest"
MAIN = "origin/main"


def run(args: list[str], check: bool = False) -> str:
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(args)}\nSTDERR:\n{p.stderr}")
    return p.stdout.strip()


def rc(args: list[str]) -> int:
    return subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode


def safe_count_rev(expr: str) -> int:
    out = run(["git", "rev-list", "--count", expr])
    try:
        return int(out)
    except Exception:
        return -1


def shortstat(base: str, branch: str) -> str:
    return run(["git", "diff", "--shortstat", f"{base}...{branch}"])


def changed_files(base: str, branch: str) -> list[str]:
    out = run(["git", "diff", "--name-only", f"{base}...{branch}"])
    return [x for x in out.splitlines() if x.strip()]


def last_commit(branch: str) -> dict:
    fmt = "%(committerdate:iso-strict)|%(objectname:short)|%(subject)"
    out = run(["git", "for-each-ref", f"refs/remotes/{branch}", f"--format={fmt}"])
    if not out:
        # branch is already like origin/x; fallback to log
        out = run(["git", "log", "-1", "--format=%cI|%h|%s", branch])
    parts = out.split("|", 2)
    return {
        "last_commit_date": parts[0] if len(parts) > 0 else "",
        "last_commit_hash": parts[1] if len(parts) > 1 else "",
        "last_commit_subject": parts[2] if len(parts) > 2 else "",
    }


def classify(branch: str, files: list[str]) -> tuple[str, str, str]:
    joined = (branch + " " + " ".join(files)).lower()

    if "data-augmentation" in joined or "augmentation" in joined:
        return (
            "KEEP_EVIDENCE_CHERRY_PICK_ONLY",
            "contains prior augmentation evidence; do not merge whole branch because current locked-gate tests supersede it",
            "Use as historical evidence only; gaussian_0p10 was promising in old reports but failed current locked-gate rerun.",
        )

    if "prior-best" in joined or "prior_best" in joined:
        return (
            "KEEP_EVIDENCE_CHERRY_PICK_ONLY",
            "contains prior-best confirmation reports; useful for history, not enough to override current ROCA conclusion",
            "Cherry-pick only summary docs if missing from current branch.",
        )

    if "strict-ntd" in joined or "nontransductive" in joined or "strict_ntd" in joined:
        return (
            "KEEP_METHOD_NOTES_CHERRY_PICK_ONLY",
            "contains strict non-transductive normalization / DG design notes",
            "Useful for methods section and future work; do not merge wholesale.",
        )

    if "subject-normalization" in joined or "subject_normalization" in joined:
        return (
            "KEEP_METHOD_NOTES_CHERRY_PICK_ONLY",
            "contains EEG subject-normalization audit/design evidence",
            "Use to support calibration/domain-shift framing; do not claim it solves locked LOSO.",
        )

    if "representation-redesign" in joined or "representation_redesign" in joined:
        return (
            "ARCHIVE_REFERENCE_ONLY",
            "contains representation redesign smoke/confirmation material",
            "Reference only if writing the project chronology.",
        )

    if "label-task" in joined or "label_task" in joined or "target-protocol" in joined:
        return (
            "KEEP_PROTOCOL_REFERENCE_ONLY",
            "contains label/task protocol decisions",
            "Useful to document target formulation, not a model-fix branch.",
        )

    if "root-cause" in joined or "root_cause" in joined or "triage" in joined:
        return (
            "KEEP_ROOT_CAUSE_REFERENCE_ONLY",
            "contains older root-cause triage reports",
            "Compare against 06a7/06a7b; do not merge wholesale.",
        )

    if "control-tower" in branch:
        return (
            "ARCHIVE_CONTROL_DOCS_ONLY",
            "mostly planning/authorization/control documents",
            "Do not merge wholesale; cherry-pick only missing decision summaries.",
        )

    return (
        "REVIEW_BEFORE_ACTION",
        "branch category not recognized automatically",
        "Inspect top files before merge/delete.",
    )


def top_relevant_files(files: list[str], limit: int = 18) -> list[str]:
    keys = [
        "augmentation", "gaussian", "prior", "best", "strict", "ntd",
        "subject", "normalization", "representation", "label", "target",
        "root", "triage", "emg", "eeg", "fusion", "calibration",
        "report", "summary", "decision",
    ]

    def score(path: str) -> tuple[int, str]:
        p = path.lower()
        s = sum(1 for k in keys if k in p)
        if p.endswith(".md"):
            s += 3
        if p.endswith(".csv") or p.endswith(".json"):
            s += 1
        if p.startswith("docs/"):
            s += 2
        if p.startswith("scripts/"):
            s += 1
        return (-s, path)

    return sorted(files, key=score)[:limit]


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    cols = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def md_table(rows: list[dict], cols: list[str]) -> str:
    if not rows:
        return "_No rows._"

    def fmt(x):
        txt = "" if x is None else str(x)
        txt = txt.replace("\n", " ").replace("|", "\\|")
        if len(txt) > 160:
            txt = txt[:157] + "..."
        return txt

    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for r in rows:
        lines.append("| " + " | ".join(fmt(r.get(c, "")) for c in cols) + " |")
    return "\n".join(lines)


def main() -> None:
    run(["git", "fetch", "--all", "--prune"], check=True)

    current_branch = run(["git", "branch", "--show-current"])

    branches = run([
        "git", "for-each-ref", "refs/remotes/origin",
        "--sort=-committerdate",
        "--format=%(refname:short)",
    ]).splitlines()

    branches = [
        b for b in branches
        if b not in {"origin/HEAD", "origin/main", "origin/roca-idare-killtest"}
    ]

    summary_rows = []
    file_rows = []

    for b in branches:
        files = changed_files(TARGET, b)
        lc = last_commit(b)
        action, reason, note = classify(b, files)

        docs_count = sum(1 for f in files if f.startswith("docs/"))
        scripts_count = sum(1 for f in files if f.startswith("scripts/"))
        md_count = sum(1 for f in files if f.endswith(".md"))
        csv_count = sum(1 for f in files if f.endswith(".csv"))
        json_count = sum(1 for f in files if f.endswith(".json"))

        row = {
            "branch": b,
            "last_commit_date": lc["last_commit_date"],
            "last_commit_hash": lc["last_commit_hash"],
            "last_commit_subject": lc["last_commit_subject"],
            "commits_ahead_of_roca": safe_count_rev(f"{TARGET}..{b}"),
            "commits_behind_roca": safe_count_rev(f"{b}..{TARGET}"),
            "files_changed_vs_roca": len(files),
            "docs_files": docs_count,
            "scripts_files": scripts_count,
            "md_files": md_count,
            "csv_files": csv_count,
            "json_files": json_count,
            "shortstat_vs_roca": shortstat(TARGET, b),
            "recommended_action": action,
            "reason": reason,
            "note": note,
        }
        summary_rows.append(row)

        for rank, f in enumerate(top_relevant_files(files), start=1):
            file_rows.append({
                "branch": b,
                "rank": rank,
                "file": f,
                "recommended_action": action,
            })

    decision_rows = [
        {
            "decision": "DO_NOT_MERGE_OLD_BRANCHES_WHOLESALE",
            "why": "old wave/postwave branches contain useful evidence but also outdated objectives, old protocols, and non-current claims",
            "action": "cherry-pick only missing evidence docs; keep 06a7/06a7b as current root-cause conclusion",
        },
        {
            "decision": "KEEP_ROCA_IDARE_KILLTEST_AS_CURRENT_TRUTH_BRANCH",
            "why": "it contains locked-gate reruns: 06a5b augmentation no-go, 06a6 neural anchor no-go, 06a7/06a7b final conclusion",
            "action": "merge this branch to main when ready, then archive/delete old experimental branches after confirming evidence is preserved",
        },
        {
            "decision": "DATA_AUGMENTATION_TRACK_IS_HISTORICAL_EVIDENCE_ONLY",
            "why": "old augmentation helped in older/non-current setups, but gaussian10 failed the current locked LOSO residual gate",
            "action": "cite as prior attempt; do not use it as proof that augmentation solves current LOSO crisis",
        },
    ]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "current_branch": current_branch,
        "target_branch": TARGET,
        "main_branch": MAIN,
        "n_old_remote_branches_audited": len(branches),
        "decision_table": decision_rows,
        "branch_summary": summary_rows,
        "top_relevant_files": file_rows,
    }

    write_csv(Path(str(PREFIX) + "_branch_summary.csv"), summary_rows)
    write_csv(Path(str(PREFIX) + "_top_relevant_files.csv"), file_rows)
    write_csv(Path(str(PREFIX) + "_decision_table.csv"), decision_rows)

    Path(str(PREFIX) + ".json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    md = []
    md.append("# I-DARE 06b0 Branch Consolidation Compact Audit")
    md.append("")
    md.append(f"- generated_at: `{payload['generated_at']}`")
    md.append(f"- current_branch: `{current_branch}`")
    md.append(f"- target_branch: `{TARGET}`")
    md.append(f"- old_remote_branches_audited: `{len(branches)}`")
    md.append("")
    md.append("## Decision table")
    md.append(md_table(decision_rows, ["decision", "why", "action"]))
    md.append("")
    md.append("## Branch summary")
    md.append(md_table(summary_rows, [
        "branch",
        "last_commit_date",
        "last_commit_hash",
        "commits_ahead_of_roca",
        "files_changed_vs_roca",
        "recommended_action",
        "reason",
    ]))
    md.append("")
    md.append("## Top relevant files by branch")
    md.append(md_table(file_rows, ["branch", "rank", "file", "recommended_action"]))
    md.append("")
    md.append("## Interpretation")
    md.append("")
    md.append(
        "The extra branches are not a GitHub connection error. They are old Wave/PostWave experimental branches. "
        "They should not be merged wholesale into the current ROCA branch because they contain older objectives, "
        "older protocols, and historical claims. The safe route is to preserve them as evidence, cherry-pick only "
        "missing reports if needed, and keep the current locked-gate ROCA conclusion as the project truth."
    )

    Path(str(PREFIX) + ".md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("ROCA step 06b0 completed.")
    for suffix in [".md", ".json", "_decision_table.csv", "_branch_summary.csv", "_top_relevant_files.csv"]:
        print("wrote:", str(PREFIX) + suffix)

    print()
    print("Decision table:")
    for r in decision_rows:
        print("-", r["decision"], "=>", r["action"])

    print()
    print("Branch actions:")
    for r in summary_rows:
        print(f"- {r['branch']}: {r['recommended_action']} | files={r['files_changed_vs_roca']} | commits_ahead={r['commits_ahead_of_roca']}")


if __name__ == "__main__":
    main()
