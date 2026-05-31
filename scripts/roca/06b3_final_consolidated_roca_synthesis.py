#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(".")
PREFIX = ROOT / "docs/roca/idare_06b3_final_consolidated_roca_synthesis_current"

CONSOLIDATED_BRANCH = "roca-consolidate-branches"
ROCA_BRANCH = "origin/roca-idare-killtest"
MAIN_BRANCH = "origin/main"

MERGED_BRANCHES = [
    ("origin/idare/postwave1/data-augmentation-track", "historical augmentation evidence"),
    ("origin/idare/postwave1/idare-prior-best-cell-confirmation", "prior-best confirmation evidence"),
    ("origin/idare/postwave1/label-task-protocol-reconciliation", "label/task protocol evidence"),
    ("origin/idare/postwave1/root-cause-triage", "root-cause triage evidence"),
    ("origin/idare/postwave1/representation-redesign-confirmation", "representation redesign confirmation evidence"),
    ("origin/idare/postwave1/representation-redesign-smoke", "representation redesign smoke evidence"),
    ("origin/idare/postwave1/strict-ntd-norm-smoke", "strict non-transductive normalization evidence"),
    ("origin/idare/wave1/eeg-input-definition", "early EEG input definition evidence"),
    ("origin/idare/wave1/eeg-subject-normalization", "early EEG subject-normalization evidence"),
    ("origin/idare/wave1/emg-baseline-ablation", "early EMG baseline evidence"),
    ("origin/idare/wave1/feature-discriminability", "early feature discriminability evidence"),
]

KEY_FILES = {
    "final_roca_decision": ROOT / "docs/roca/idare_06a7_final_loso_root_cause_report_current_decision_table.csv",
    "calibration_conclusion": ROOT / "docs/roca/idare_06a7b_calibration_dominant_conclusion_current_conclusion_table.csv",
    "branch_merge_plan": ROOT / "docs/roca/idare_06b2_branch_merge_plan_current_branch_plan.csv",
    "branch_policy": ROOT / "docs/roca/idare_06b1_branch_consolidation_merge_policy_current.md",
    "compact_audit": ROOT / "docs/roca/idare_06b0_branch_consolidation_compact_audit_current_branch_summary.csv",
}

def run(args: list[str], check: bool = True) -> str:
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(args)}\nSTDERR:\n{p.stderr}")
    return p.stdout.strip()

def read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def branch_tip(branch: str) -> str:
    return run(["git", "rev-parse", "--short", branch], check=False)

def ahead_count(base: str, head: str) -> int:
    out = run(["git", "rev-list", "--count", f"{base}..{head}"], check=False)
    try:
        return int(out)
    except Exception:
        return -1

def changed_files(base: str, head: str) -> int:
    out = run(["git", "diff", "--name-only", f"{base}...{head}"], check=False)
    if not out:
        return 0
    return len([x for x in out.splitlines() if x.strip()])

def main() -> None:
    run(["git", "fetch", "--all", "--prune"], check=False)

    current_branch = run(["git", "branch", "--show-current"], check=False)
    working_tree_status = run(["git", "status", "--short"], check=False)

    final_rows = read_csv_rows(KEY_FILES["final_roca_decision"])
    conclusion_rows = read_csv_rows(KEY_FILES["calibration_conclusion"])
    merge_plan_rows = read_csv_rows(KEY_FILES["branch_merge_plan"])
    compact_rows = read_csv_rows(KEY_FILES["compact_audit"])

    branch_rows = []
    for branch, role in MERGED_BRANCHES:
        branch_rows.append({
            "branch": branch,
            "role": role,
            "tip": branch_tip(branch),
            "commits_ahead_of_roca_before_consolidation": ahead_count(ROCA_BRANCH, branch),
            "changed_files_vs_roca_before_consolidation": changed_files(ROCA_BRANCH, branch),
            "status_after_06b3": "merged_into_roca_consolidate_branches_as_historical_evidence",
            "scientific_use": "preserve/cite as evidence; do not override locked-gate ROCA conclusion",
        })

    decision = {
        "target": "I-DARE EEG/EMG emotion recognition under LOSO",
        "current_branch": current_branch,
        "consolidated_branch_tip": branch_tip("HEAD"),
        "origin_consolidated_tip": branch_tip("origin/roca-consolidate-branches"),
        "origin_roca_tip": branch_tip(ROCA_BRANCH),
        "origin_main_tip": branch_tip(MAIN_BRANCH),
        "final_decision": "CONSOLIDATION_READY_FOR_REVIEW_NOT_MAIN",
        "scientific_conclusion_changed_by_historical_merges": "NO",
        "current_scientific_conclusion": (
            "Strict LOSO global raw EEG/EMG residual decoding remains unsupported by locked gates. "
            "The dominant issue is subject calibration/domain shift plus weak transferable residual identifiability. "
            "Historical branches are useful evidence, but they do not overturn the final ROCA locked-gate conclusion."
        ),
        "recommended_action": (
            "Review this 06b3 synthesis. If acceptable, merge roca-consolidate-branches into "
            "roca-idare-killtest only; do not merge into main."
        ),
    }

    next_steps = [
        {
            "priority": 1,
            "step": "review_06b3",
            "action": "Review final consolidated ROCA synthesis.",
            "success_condition": "No historical branch is misrepresented as final proof.",
        },
        {
            "priority": 2,
            "step": "merge_to_roca",
            "action": "Merge roca-consolidate-branches into roca-idare-killtest.",
            "success_condition": "origin/roca-idare-killtest points to a commit containing 06b1, 06b2, 06b3 and historical evidence merges.",
        },
        {
            "priority": 3,
            "step": "archive_old_branches",
            "action": "After verification, optionally delete/archive old idare/* remote branches.",
            "success_condition": "GitHub branch list is reduced without losing evidence.",
        },
        {
            "priority": 4,
            "step": "scientific_next_track",
            "action": "Start next research track only after deciding whether the claim is calibrated/personalized or strict zero-calibration LOSO.",
            "success_condition": "No more blind EEG/EMG architecture search without a success gate.",
        },
    ]

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "decision": decision,
        "merged_branch_summary": branch_rows,
        "final_roca_decision_rows": final_rows,
        "calibration_conclusion_rows": conclusion_rows,
        "merge_plan_rows": merge_plan_rows,
        "compact_audit_rows": compact_rows,
        "key_files": {k: str(v) for k, v in KEY_FILES.items()},
        "working_tree_status": working_tree_status,
        "next_steps": next_steps,
    }

    PREFIX.parent.mkdir(parents=True, exist_ok=True)

    (Path(str(PREFIX) + ".json")).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    write_csv(Path(str(PREFIX) + "_decision_table.csv"), [decision])
    write_csv(Path(str(PREFIX) + "_merged_branch_summary.csv"), branch_rows)
    write_csv(Path(str(PREFIX) + "_next_steps.csv"), next_steps)

    md = []
    md.append("# I-DARE 06b3 Final Consolidated ROCA Synthesis")
    md.append("")
    md.append(f"Generated at: `{payload['generated_at']}`")
    md.append("")
    md.append("## Final decision")
    md.append("")
    md.append(f"- **Decision:** `{decision['final_decision']}`")
    md.append(f"- **Scientific conclusion changed by historical merges:** `{decision['scientific_conclusion_changed_by_historical_merges']}`")
    md.append(f"- **Current branch:** `{current_branch}`")
    md.append(f"- **Consolidated branch tip:** `{decision['consolidated_branch_tip']}`")
    md.append(f"- **ROCA truth branch tip:** `{decision['origin_roca_tip']}`")
    md.append(f"- **Main branch tip:** `{decision['origin_main_tip']}`")
    md.append("")
    md.append("## Current scientific conclusion")
    md.append("")
    md.append(decision["current_scientific_conclusion"])
    md.append("")
    md.append("## Merged historical branches")
    md.append("")
    md.append("| Branch | Role | Status | Scientific use |")
    md.append("|---|---|---|---|")
    for r in branch_rows:
        md.append(f"| `{r['branch']}` | {r['role']} | {r['status_after_06b3']} | {r['scientific_use']} |")
    md.append("")
    md.append("## What this means")
    md.append("")
    md.append(
        "The historical branches are now preserved in the consolidation branch. "
        "They provide useful evidence about augmentation, protocol choices, representation redesign, "
        "normalization, EMG baselines, and feature discriminability. However, they do not replace the "
        "newer locked-gate ROCA conclusion."
    )
    md.append("")
    md.append("The current conclusion remains calibration-dominant: EEG/EMG signals under strict LOSO are not enough, "
              "under the tested formulations, to support a strong global residual emotion-recognition claim. "
              "Future positive claims should be framed around calibration, personalization, adaptation, or a redesigned target.")
    md.append("")
    md.append("## Recommended next steps")
    md.append("")
    md.append("| Priority | Step | Action | Success condition |")
    md.append("|---:|---|---|---|")
    for s in next_steps:
        md.append(f"| {s['priority']} | `{s['step']}` | {s['action']} | {s['success_condition']} |")
    md.append("")
    md.append("## Merge instruction")
    md.append("")
    md.append("If this synthesis is accepted, merge `roca-consolidate-branches` into `roca-idare-killtest`. Do **not** merge it into `main`.")
    md.append("")

    (Path(str(PREFIX) + ".md")).write_text("\n".join(md), encoding="utf-8")

    print("ROCA step 06b3 completed.")
    for suffix in [".md", ".json", "_decision_table.csv", "_merged_branch_summary.csv", "_next_steps.csv"]:
        print("wrote:", str(PREFIX) + suffix)

    print()
    print("Decision:")
    print(decision["final_decision"])
    print(decision["current_scientific_conclusion"])

if __name__ == "__main__":
    main()
