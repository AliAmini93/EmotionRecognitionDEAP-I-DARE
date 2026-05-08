#!/usr/bin/env bash
set -euo pipefail

REPO="/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE"
LOG="/tmp/idare_label_policy_review_closeout.log"

cd "$REPO"

{
  echo "===== 0) start label-policy review closeout ====="
  date
  git status --short --branch
  echo

  echo "===== 1) choose python and require clean repo ====="
  if [ -x ".venv/bin/python" ]; then
    PY=".venv/bin/python"
  elif [ -x ".venv/bin/python3" ]; then
    PY=".venv/bin/python3"
  else
    PY="python3"
  fi
  echo "PY=$PY"
  "$PY" - <<'PY'
import sys, json
print(sys.executable)
print("OK_IMPORTS")
PY

  if [ -n "$(git status --short)" ]; then
    echo "ERROR: repo is not clean. Commit/stash/remove unrelated changes before closeout."
    git status --short --branch
    exit 1
  fi
  echo "OK_REPO_CLEAN"
  echo

  echo "===== 2) create review closeout docs and update roadmap ====="
  "$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
REPORT_MD = DOCS / "idare_label_policy_ablation_report.md"
REPORT_JSON = DOCS / "idare_label_policy_ablation_report.json"
REVIEW_MD = DOCS / "idare_label_policy_ablation_review_status.md"
REVIEW_JSON = DOCS / "idare_label_policy_ablation_review_status.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()

required = [REPORT_MD, REPORT_JSON, PROJECT_MD, PROJECT_JSON]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit("ERROR missing required files: " + ", ".join(missing))

report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))
comparisons = report.get("comparisons", [])
if len(comparisons) != 4:
    raise SystemExit(f"ERROR expected 4 modality/task comparisons, got {len(comparisons)}")

def fmt(x):
    return f"{float(x):.4f}"

winner_rows = []
policy_winners = set()
task_specific = {}
for row in comparisons:
    modality = row["modality"]
    task = row["task"]
    best_policy = row["best_policy"]
    best_recipe = row["best_recipe"]
    macro = float(row["best_macro_f1_mean"])
    bal = float(row["best_balanced_accuracy_mean"])
    policy_winners.add(best_policy)
    key = f"{modality.lower()}_{task}"
    task_specific[key] = {
        "modality": modality,
        "task": task,
        "best_policy": best_policy,
        "best_recipe": best_recipe,
        "macro_f1": macro,
        "balanced_accuracy": bal,
    }
    winner_rows.append(
        f"| {modality} | {task} | `{best_policy}` | `{best_recipe}` | {fmt(macro)} | {fmt(bal)} |"
    )

not_authorized = [
    "EEG+EMG fusion",
    "full model(BSL, STIM, STIM-BSL)",
    "final LOSO / final paper claim",
    "locking a final global label policy",
    "raw EMG mainline",
    "architecture ablations",
    "data augmentation",
    "SupCon / VREx / domain generalization",
    "optional extra seeds without explicit objective",
]

review = {
    "status": "frozen_human_review_closeout",
    "created_or_updated_utc": NOW,
    "reviewed_report": str(REPORT_MD),
    "reviewed_json": str(REPORT_JSON),
    "evidence_level": "human-reviewed controlled label-policy primary matrix; not final LOSO evidence",
    "matrix": report.get("matrix", {}),
    "human_review_decision": {
        "accepted": True,
        "result": "mixed_task_specific_winners",
        "final_global_label_policy_locked": False,
        "practical_default_policy": "midpoint_as_high remains the continuity/default smoke policy only, not a final paper policy.",
        "task_specific_winners": task_specific,
        "mainline_changed": False,
        "fusion_started": False,
        "final_loso_claim": False,
        "recommended_interpretation": (
            "The 144-run matrix does not support locking one global label policy. "
            "Keep midpoint_as_high as the practical default for continuity, and keep "
            "discard_midpoint as a serious task-specific contender for EEG valence and EMG arousal."
        ),
    },
    "not_authorized": not_authorized,
    "next_allowed_step": (
        "Stop here, hand off, or create a separate explicit follow-up objective for label-policy robustness "
        "before any final label-policy lock."
    ),
}

REVIEW_JSON.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")

md_lines = [
    "# I-DARE Label-Policy Ablation Review Status",
    "",
    "## Status",
    "",
    "Frozen human-review closeout.",
    "",
    "This closes the controlled 144-run I-DARE label-policy ablation at smoke/stabilization evidence level.",
    "",
    "It does **not** make a final LOSO claim.",
    "",
    "It does **not** lock a final global label policy.",
    "",
    "## Reviewed Inputs",
    "",
    f"- Primary report: `{REPORT_MD}`",
    f"- Primary JSON: `{REPORT_JSON}`",
    "- EEG combined output: `docs/idare_label_policy_ablation_eeg_primary.json`",
    "- EMG combined output: `docs/idare_label_policy_ablation_emg_primary.json`",
    "",
    "## Result Summary",
    "",
    "| Modality | Task | Best policy | Best recipe | Macro F1 | Balanced acc |",
    "|---|---|---|---|---:|---:|",
    *winner_rows,
    "",
    "## Review Decision",
    "",
    "- The 144-run label-policy matrix is accepted as a valid controlled smoke/stabilization ablation.",
    "- The result is mixed: no single label policy wins across EEG/EMG and valence/arousal.",
    "- Do **not** lock `midpoint_as_high`, `midpoint_as_low`, or `discard_midpoint` as the final global paper policy.",
    "- Keep `midpoint_as_high` only as the practical continuity/default smoke policy for now.",
    "- Keep `discard_midpoint` as a serious task-specific contender, especially for EEG valence and EMG arousal.",
    "",
    "## Mainline / Policy Status After Review",
    "",
    "- EEG practical mainline remains baseline-corrected `STIM-BSL`-only.",
    "- EMG practical mainline remains feature-level EMG.",
    "- Label policy remains unresolved for final claims.",
    "- Any future final-label decision needs an explicit follow-up objective, likely robustness-focused.",
    "",
    "## Not Authorized",
    "",
]
md_lines.extend(f"- {item}" for item in not_authorized)
md_lines.extend([
    "",
    "## Next Allowed Step",
    "",
    "Stop here, hand off, or create a separate explicit follow-up objective for label-policy robustness before locking any final policy.",
    "",
])
REVIEW_MD.write_text("\n".join(md_lines), encoding="utf-8")

# Update project_status_current.md
project_md = PROJECT_MD.read_text(encoding="utf-8")

old_label_block = """Label policy is now an explicit future ablation:

- `discard_midpoint`: score `> 5` is high, score `== 5` discarded.
- `midpoint_as_low`: score `> 5` is high, score `== 5` low.
- `midpoint_as_high`: score `>= 5` is high.

Final claims should not lock to `midpoint_as_high` until these policies are compared under fixed splits, seeds, recipes, and metrics."""
new_label_block = """Label policy has now been tested in a controlled 144-run I-DARE ablation and reviewed.

Best smoke-level policies were mixed by modality/task:

- EEG valence: `discard_midpoint`
- EEG arousal: `midpoint_as_high`
- EMG valence: `midpoint_as_high`
- EMG arousal: `discard_midpoint`

No final global label policy is locked. `midpoint_as_high` remains only the practical continuity/default smoke policy, not a final paper policy."""
if old_label_block in project_md:
    project_md = project_md.replace(old_label_block, new_label_block)
elif "No final global label policy is locked" not in project_md:
    project_md = project_md.replace("## Phase Roadmap", new_label_block + "\n\n## Phase Roadmap")

old_row_objective = "| I-DARE controlled label-policy ablation objective | short-term execution objective created for 144-run label-policy matrix | yes | `docs/idare_label_policy_ablation_objective.md` | Prepare execution commands or limited script patches; review before running. | EEG+EMG fusion; final LOSO claim; locking final label policy before review. |"
old_row_planned = "| Label-policy ablation | planned / not final | no | `README.md`<br>`training smoke JSON reports` | Run controlled comparison of discard_midpoint, midpoint_as_low, and midpoint_as_high using fixed splits/seeds. | Locking midpoint_as_high as the final paper policy. |"
new_rows = """| I-DARE controlled label-policy ablation objective | short-term objective created and executed for 144-run label-policy matrix | yes | `docs/idare_label_policy_ablation_objective.md` | Review status is frozen in `docs/idare_label_policy_ablation_review_status.md`. | EEG+EMG fusion; final LOSO claim; locking final label policy before review. |
| I-DARE label-policy ablation primary report | 144-run EEG/EMG mainline label-policy matrix completed; mixed task-specific winners | yes | `docs/idare_label_policy_ablation_report.md` | Reviewed in `docs/idare_label_policy_ablation_review_status.md`. | EEG+EMG fusion; final LOSO claim; locking final global label policy. |
| I-DARE label-policy ablation review | human review accepted 144-run matrix; no final global label policy locked | yes | `docs/idare_label_policy_ablation_review_status.md` | Stop here, hand off, or create explicit label-policy robustness objective. | EEG+EMG fusion; final LOSO claim; architecture/augmentation/DG work. |"""
if old_row_objective in project_md:
    project_md = project_md.replace(old_row_objective, new_rows)
else:
    anchor = "| EEG+EMG fusion | not started intentionally | no |"
    if new_rows not in project_md and anchor in project_md:
        project_md = project_md.replace(anchor, new_rows + "\n" + anchor)

if old_row_planned in project_md:
    project_md = project_md.replace(old_row_planned + "\n", "")

old_decision = "- A controlled I-DARE label-policy ablation objective is defined in `docs/idare_label_policy_ablation_objective.md`; only the 144-run EEG/EMG mainline label-policy matrix is authorized."
new_decision = "- Human review of the controlled I-DARE label-policy ablation is frozen in `docs/idare_label_policy_ablation_review_status.md`; winners are mixed, no final global label policy is locked, and `midpoint_as_high` remains only the practical continuity/default smoke policy."
if old_decision in project_md:
    project_md = project_md.replace(old_decision, new_decision)
elif new_decision not in project_md:
    project_md = project_md.replace("## Documentation Gap Closed by This File", new_decision + "\n\n## Documentation Gap Closed by This File")

PROJECT_MD.write_text(project_md, encoding="utf-8")

# Update project_status_current.json
project = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
project.setdefault("decisions", {})

project["decisions"]["idare_label_policy_ablation_primary_matrix"] = {
    "status": "primary_matrix_complete_reviewed",
    "evidence": str(REPORT_MD),
    "evidence_json": str(REPORT_JSON),
    "evidence_level": report.get("evidence_level", "controlled ablation primary matrix, not final LOSO"),
    "total_primary_runs": report.get("matrix", {}).get("total_runs", 144),
    "summary": "All 144 authorized label-policy runs completed and validated; winners are mixed by modality/task.",
    "final_global_label_policy_locked": False,
    "next_allowed_step": "See docs/idare_label_policy_ablation_review_status.md.",
    "not_authorized_from_this_report": not_authorized,
}

project["decisions"]["idare_label_policy_ablation_review_status"] = {
    "status": "frozen_human_review_closeout",
    "evidence": str(REVIEW_MD),
    "reviewed_report": str(REPORT_MD),
    "mainline_changed": False,
    "fusion_started": False,
    "final_loso_claim": False,
    "final_global_label_policy_locked": False,
    "practical_default_policy": "midpoint_as_high for continuity/default smoke use only",
    "task_specific_winners": task_specific,
    "next_allowed_step": review["next_allowed_step"],
    "not_authorized": not_authorized,
}

if "idare_label_policy_ablation_objective" in project["decisions"]:
    project["decisions"]["idare_label_policy_ablation_objective"]["status"] = "executed_and_reviewed"
    project["decisions"]["idare_label_policy_ablation_objective"]["next_allowed_step"] = "See docs/idare_label_policy_ablation_review_status.md."

project["label_policy_review"] = {
    "status": "mixed_task_specific_winners_no_global_lock",
    "evidence": str(REVIEW_MD),
    "best_policies": task_specific,
    "final_global_label_policy_locked": False,
    "practical_default_policy": "midpoint_as_high remains continuity/default smoke policy only",
}

PROJECT_JSON.write_text(json.dumps(project, indent=2, sort_keys=True) + "\n", encoding="utf-8")

print("OK_REVIEW_CLOSEOUT_WRITTEN")
print(REVIEW_MD)
print(REVIEW_JSON)
PY
  echo

  echo "===== 3) validate docs ====="
  "$PY" - <<'PY'
import json
from pathlib import Path
for p in [
    Path("docs/idare_label_policy_ablation_review_status.json"),
    Path("docs/project_status_current.json"),
]:
    json.loads(p.read_text(encoding="utf-8"))
print("OK_JSON")
PY

  grep -n "## Status\|## Result Summary\|## Review Decision\|## Next Allowed Step" docs/idare_label_policy_ablation_review_status.md
  grep -n "I-DARE label-policy ablation review\|No final global label policy\|Human review of the controlled I-DARE label-policy ablation" docs/project_status_current.md
  echo

  echo "===== 4) diff stat ====="
  git diff --stat
  echo

  echo "===== 5) status before commit ====="
  git status --short --branch
  echo

  echo "===== 6) commit and push review closeout ====="
  git add \
    docs/idare_label_policy_ablation_review_status.md \
    docs/idare_label_policy_ablation_review_status.json \
    docs/project_status_current.md \
    docs/project_status_current.json

  git commit -m "docs: review I-DARE label-policy ablation"
  git push origin main
  echo

  echo "===== 7) final status ====="
  git status --short --branch
  echo "LOG_SAVED_TO=$LOG"
} 2>&1 | tee "$LOG"
