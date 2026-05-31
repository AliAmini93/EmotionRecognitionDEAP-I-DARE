#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(".")
PREFIX = ROOT / "docs/roca/idare_06b2_branch_merge_plan_current"

TARGET = "origin/roca-idare-killtest"

CANDIDATES = [
    "origin/idare/control-tower",
    "origin/idare/postwave1/data-augmentation-track",
    "origin/idare/postwave1/idare-prior-best-cell-confirmation",
    "origin/idare/postwave1/label-task-protocol-reconciliation",
    "origin/idare/postwave1/root-cause-triage",
    "origin/idare/postwave1/representation-redesign-confirmation",
    "origin/idare/postwave1/representation-redesign-smoke",
    "origin/idare/postwave1/strict-ntd-norm-smoke",
    "origin/idare/wave1/eeg-input-definition",
    "origin/idare/wave1/eeg-subject-normalization",
    "origin/idare/wave1/emg-baseline-ablation",
    "origin/idare/wave1/feature-discriminability",
]


def run(args: list[str], check: bool = True) -> str:
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(args)}\nSTDERR:\n{p.stderr}")
    return p.stdout.strip()


def ok(args: list[str]) -> bool:
    return subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def rev_count(expr: str) -> int:
    out = run(["git", "rev-list", "--count", expr])
    return int(out or 0)


def changed_files(branch: str) -> list[str]:
    out = run(["git", "diff", "--name-only", f"{TARGET}...{branch}"], check=False)
    return [x for x in out.splitlines() if x.strip()]


def classify(branch: str, files: list[str], commits_ahead: int) -> str:
    b = branch.lower()
    joined = "\n".join(files).lower()

    if commits_ahead == 0:
        return "SKIP_ALREADY_COVERED"

    if "data-augmentation-track" in b:
        return "MERGE_AS_HISTORICAL_AUGMENTATION_EVIDENCE"

    if "control-tower" in b:
        return "MERGE_AS_PLANNING_AND_AUTHORIZATION_EVIDENCE"

    if "prior-best-cell-confirmation" in b:
        return "MERGE_AS_PRIOR_BEST_CONFIRMATION_EVIDENCE"

    if "root-cause-triage" in b:
        return "MERGE_AS_ROOT_CAUSE_TRIAGE_EVIDENCE"

    if "label-task-protocol" in b:
        return "MERGE_AS_PROTOCOL_LABEL_POLICY_EVIDENCE"

    if "representation-redesign" in b:
        return "MERGE_AS_REPRESENTATION_REDESIGN_EVIDENCE"

    if "strict-ntd-norm" in b:
        return "MERGE_AS_STRICT_NORMALIZATION_DG_EVIDENCE"

    if "wave1" in b:
        return "MERGE_AS_EARLY_WAVE1_DIAGNOSTIC_EVIDENCE"

    if "docs/" in joined:
        return "MERGE_AS_DOCUMENTATION_EVIDENCE"

    return "REVIEW_BEFORE_MERGE"


def main() -> None:
    run(["git", "fetch", "--all", "--prune"], check=False)

    current = run(["git", "branch", "--show-current"], check=False)
    target_head = run(["git", "rev-parse", "--short", TARGET])
    local_head = run(["git", "rev-parse", "--short", "HEAD"])

    existing = []
    missing = []
    for b in CANDIDATES:
        if ok(["git", "rev-parse", "--verify", b]):
            existing.append(b)
        else:
            missing.append(b)

    rows = []
    for b in existing:
        commits_ahead = rev_count(f"{TARGET}..{b}")
        files = changed_files(b)

        covered_by = []
        covers = []
        for other in existing:
            if other == b:
                continue
            if ok(["git", "merge-base", "--is-ancestor", b, other]):
                covered_by.append(other)
            if ok(["git", "merge-base", "--is-ancestor", other, b]):
                covers.append(other)

        is_redundant = bool(covered_by)
        recommended_action = "SKIP_COVERED_BY_LARGER_BRANCH" if is_redundant else "MERGE_BRANCH_TIP"

        rows.append({
            "branch": b,
            "commits_ahead_target": commits_ahead,
            "changed_file_count": len(files),
            "is_ancestor_of_other_candidate": is_redundant,
            "covered_by": "; ".join(covered_by),
            "covers": "; ".join(covers),
            "classification": classify(b, files, commits_ahead),
            "recommended_action": recommended_action,
            "last_commit": run(["git", "log", "-1", "--oneline", b], check=False),
        })

    merge_tips = [r for r in rows if r["recommended_action"] == "MERGE_BRANCH_TIP"]
    redundant = [r for r in rows if r["recommended_action"] != "MERGE_BRANCH_TIP"]

    decision = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "current_branch": current,
        "target": TARGET,
        "target_head": target_head,
        "local_head": local_head,
        "candidate_count": len(CANDIDATES),
        "existing_candidate_count": len(existing),
        "missing": missing,
        "merge_tip_count": len(merge_tips),
        "redundant_count": len(redundant),
        "policy": "Merge only non-redundant branch tips into roca-consolidate-branches. Preserve current ROCA locked-gate conclusion as truth.",
        "merge_order": [r["branch"] for r in merge_tips],
    }

    PREFIX.parent.mkdir(parents=True, exist_ok=True)

    with open(str(PREFIX) + ".json", "w", encoding="utf-8") as f:
        json.dump({"decision": decision, "branches": rows}, f, indent=2, ensure_ascii=False)

    with open(str(PREFIX) + "_branch_plan.csv", "w", newline="", encoding="utf-8") as f:
        cols = [
            "branch",
            "recommended_action",
            "classification",
            "commits_ahead_target",
            "changed_file_count",
            "is_ancestor_of_other_candidate",
            "covered_by",
            "covers",
            "last_commit",
        ]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})

    md = []
    md.append("# I-DARE Branch Merge Plan")
    md.append("")
    md.append(f"- generated_at: `{decision['generated_at']}`")
    md.append(f"- current_branch: `{current}`")
    md.append(f"- target: `{TARGET}` @ `{target_head}`")
    md.append(f"- local_head: `{local_head}`")
    md.append("")
    md.append("## Decision")
    md.append("")
    md.append("Merge only non-redundant branch tips into `roca-consolidate-branches` first.")
    md.append("Branches that are ancestors of another candidate should not be merged separately unless manual review shows missing artifacts.")
    md.append("")
    md.append("Current ROCA locked-gate conclusion remains the scientific truth; old branches are imported as historical evidence, not as replacement conclusions.")
    md.append("")
    md.append("## Recommended merge tips")
    md.append("")
    if merge_tips:
        md.append("| branch | classification | commits ahead | files | last commit |")
        md.append("|---|---:|---:|---:|---|")
        for r in merge_tips:
            md.append(
                f"| `{r['branch']}` | {r['classification']} | {r['commits_ahead_target']} | {r['changed_file_count']} | {r['last_commit'].replace('|', '/')} |"
            )
    else:
        md.append("_No merge tips found._")
    md.append("")
    md.append("## Covered / redundant branches")
    md.append("")
    if redundant:
        md.append("| branch | covered by | commits ahead | files |")
        md.append("|---|---|---:|---:|")
        for r in redundant:
            md.append(f"| `{r['branch']}` | {r['covered_by']} | {r['commits_ahead_target']} | {r['changed_file_count']} |")
    else:
        md.append("_No redundant branches detected._")
    md.append("")
    md.append("## Concrete merge order")
    md.append("")
    md.append("```bash")
    for r in merge_tips:
        md.append(f"git merge --no-ff {r['branch']} -m \"Merge historical I-DARE evidence from {r['branch']}\"")
    md.append("```")
    md.append("")
    md.append("After each merge, run:")
    md.append("")
    md.append("```bash")
    md.append("git status --short")
    md.append("```")

    Path(str(PREFIX) + ".md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("ROCA step 06b2 completed.")
    print(f"wrote: {PREFIX}.md")
    print(f"wrote: {PREFIX}.json")
    print(f"wrote: {PREFIX}_branch_plan.csv")
    print()
    print("Recommended merge tips:")
    for r in merge_tips:
        print(f"- {r['branch']} | {r['classification']} | commits={r['commits_ahead_target']} files={r['changed_file_count']}")
    print()
    print("Covered/redundant branches:")
    for r in redundant:
        print(f"- {r['branch']} covered_by={r['covered_by']}")


if __name__ == "__main__":
    main()
