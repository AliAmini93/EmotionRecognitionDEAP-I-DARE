#!/usr/bin/env bash
# Create human-review closeout docs for the broader I-DARE single-modality evaluation.
# This does NOT run any experiment and does NOT push.
# It creates review status docs, updates project_status_current, validates JSON, and commits locally.

cd /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE || exit 1

LOG=/tmp/idare_broader_eval_review_closeout.log

{
  echo "===== 0) start status ====="
  git status --short --branch
  echo

  PY=".venv/bin/python"
  if [ ! -x "$PY" ]; then PY="python3"; fi
  echo "PY=$PY"
  echo

  echo "===== 1) create review closeout docs and update roadmap ====="
  "$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
REPORT_MD = DOCS / "idare_broader_standardized_single_modality_evaluation_report.md"
REPORT_JSON = DOCS / "idare_broader_standardized_single_modality_evaluation_report.json"

REVIEW_MD = DOCS / "idare_broader_standardized_single_modality_evaluation_review_status.md"
REVIEW_JSON = DOCS / "idare_broader_standardized_single_modality_evaluation_review_status.json"

PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()

report = json.loads(REPORT_JSON.read_text(encoding="utf-8"))

comparisons = report.get("comparisons", [])
validation = report.get("validation", {})
primary_matrix = report.get("primary_matrix", {})

def find_comparison(modality: str, task: str):
    for row in comparisons:
        if row.get("modality") == modality and row.get("task") == task:
            return row
    raise SystemExit(f"Missing comparison for {modality} {task}")

eeg_valence = find_comparison("EEG", "valence")
eeg_arousal = find_comparison("EEG", "arousal")
emg_valence = find_comparison("EMG", "valence")
emg_arousal = find_comparison("EMG", "arousal")

review = {
    "status": "frozen_human_review_closeout",
    "created_or_updated_utc": NOW,
    "reviewed_report": str(REPORT_MD),
    "reviewed_json": str(REPORT_JSON),
    "evidence_level": "broader standardized single-modality primary matrix; not final LOSO",
    "primary_matrix": primary_matrix,
    "validation_summary": validation,
    "human_review_decision": {
        "accepted": True,
        "primary_matrix_complete": True,
        "mainline_changed": False,
        "eeg_decision": "Keep baseline-corrected STIM-BSL-only as the practical I-DARE EEG mainline for now.",
        "emg_decision": "Keep feature-only EMG as the practical I-DARE EMG mainline for now.",
        "bsl_stats_decision": "Keep BSL-stats sidecars as controlled ablations; do not promote them to mainline from this evidence alone.",
        "fusion_decision": "Do not start EEG+EMG fusion from this report.",
        "full_paired_model_decision": "Do not start full model(BSL, STIM, STIM-BSL).",
        "label_policy_decision": "Do not lock midpoint_as_high as final label policy.",
        "final_claim_decision": "Do not claim final LOSO or final paper performance from this report."
    },
    "rationale": {
        "eeg_valence": eeg_valence,
        "eeg_arousal": eeg_arousal,
        "emg_valence": emg_valence,
        "emg_arousal": emg_arousal,
        "summary": [
            "EEG valence favors the STIM-BSL-only baseline.",
            "EEG arousal slightly favors BSL-stats on macro F1, but the report labels it roughly neutral or mixed.",
            "EMG valence and arousal are roughly neutral or mixed.",
            "Therefore there is no strong broader-evaluation basis to promote BSL-stats sidecars or start fusion."
        ]
    },
    "next_allowed_step": "Stop here, hand off, or create a separate explicit objective for a future controlled follow-up.",
    "not_authorized": [
        "EEG+EMG fusion",
        "full model(BSL, STIM, STIM-BSL)",
        "final LOSO / final paper claim",
        "locking midpoint_as_high",
        "raw EMG mainline",
        "architecture ablations",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "optional robustness seed 13 without explicit objective"
    ]
}

REVIEW_JSON.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def fmt(x):
    if x is None:
        return "NA"
    return f"{float(x):.4f}"

lines = []
lines.append("# I-DARE Broader Standardized Single-Modality Evaluation Review Status\n")
lines.append("## Status\n")
lines.append("Frozen human-review closeout.\n")
lines.append("The 96-run primary matrix is accepted as completed and valid broader single-modality evidence.\n")
lines.append("This is not final LOSO evidence and does not change any mainline automatically.\n")

lines.append("## Reviewed Evidence\n")
lines.append(f"- Report: `{REPORT_MD}`")
lines.append(f"- JSON: `{REPORT_JSON}`")
lines.append("- Evidence level: broader standardized single-modality primary matrix, not final LOSO.\n")

lines.append("## Review Decision\n")
lines.append("| Item | Decision |")
lines.append("|---|---|")
lines.append("| Accept primary matrix? | yes |")
lines.append("| Change EEG mainline? | no |")
lines.append("| Change EMG mainline? | no |")
lines.append("| Promote BSL-stats to mainline? | no |")
lines.append("| Start EEG+EMG fusion? | no |")
lines.append("| Start full BSL/STIM paired model? | no |")
lines.append("| Lock `midpoint_as_high`? | no |")
lines.append("| Claim final LOSO? | no |\n")

lines.append("## Result Summary\n")
lines.append("| Modality | Task | Baseline macro F1 | Sidecar macro F1 | Delta | Interpretation |")
lines.append("|---|---|---:|---:|---:|---|")
for row in [eeg_valence, eeg_arousal, emg_valence, emg_arousal]:
    lines.append(
        f"| {row['modality']} | {row['task']} | "
        f"{fmt(row.get('baseline_final_macro_f1_mean'))} | "
        f"{fmt(row.get('sidecar_final_macro_f1_mean'))} | "
        f"{fmt(row.get('delta_final_macro_f1'))} | "
        f"{row.get('interpretation')} |"
    )

lines.append("\n## Rationale\n")
lines.append("- EEG valence favors the `STIM-BSL`-only baseline.")
lines.append("- EEG arousal is a small BSL-stats gain, but the combined report labels it roughly neutral or mixed.")
lines.append("- EMG valence and EMG arousal are both roughly neutral or mixed.")
lines.append("- Because the evidence is mixed and still not final LOSO, keep mainlines unchanged.")
lines.append("- Keep BSL-stats sidecars as controlled ablations.\n")

lines.append("## Mainline After Review\n")
lines.append("- EEG practical mainline: baseline-corrected `STIM-BSL`-only.")
lines.append("- EMG practical mainline: feature-only EMG.")
lines.append("- BSL-stats: controlled ablation only.")
lines.append("- Fusion: not started.\n")

lines.append("## Not Authorized\n")
for item in review["not_authorized"]:
    lines.append(f"- {item}")

lines.append("\n## Next Allowed Step\n")
lines.append("Stop here, hand off, or create a separate explicit objective for a future controlled follow-up.\n")
lines.append("Do not start fusion automatically from this closeout.\n")

REVIEW_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

# Update central roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
row = "| I-DARE broader standardized single-modality evaluation review | human review accepted 96-run primary matrix; mainlines unchanged | yes | `docs/idare_broader_standardized_single_modality_evaluation_review_status.md` | Stop here, hand off, or create explicit future follow-up objective. | EEG+EMG fusion; full paired BSL/STIM neural model; final LOSO claim. |"
if "I-DARE broader standardized single-modality evaluation review" not in project_md:
    anchor = "| EEG+EMG fusion | not started intentionally | no | `docs/idare_eeg_bsl_stats_ablation_status.md`<br>`docs/idare_emg_bsl_stats_ablation_status.md` | Start only after current baseline/ablation status is indexed and compared cleanly. | All fusion experiments. |"
    project_md = project_md.replace(anchor, row + "\n" + anchor)

note = "- Human review of the broader standardized single-modality evaluation is frozen in `docs/idare_broader_standardized_single_modality_evaluation_review_status.md`; mainlines remain unchanged and fusion is not started."
if note not in project_md:
    project_md = project_md.replace(
        "- Do not claim final performance from the smoke reports.",
        "- Do not claim final performance from the smoke reports.\n" + note,
    )

PROJECT_MD.write_text(project_md, encoding="utf-8")

project = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
project.setdefault("sources", {})["idare_broader_standardized_single_modality_evaluation_review_status"] = str(REVIEW_MD)
project.setdefault("decisions", {})["idare_broader_standardized_single_modality_evaluation_review_status"] = {
    "status": "frozen_human_review_closeout",
    "evidence": str(REVIEW_MD),
    "reviewed_report": str(REPORT_MD),
    "mainline_changed": False,
    "eeg_mainline": "baseline-corrected STIM-BSL-only",
    "emg_mainline": "feature-only EMG",
    "bsl_stats": "controlled ablation only",
    "fusion_started": False,
    "final_loso_claim": False,
    "midpoint_as_high_locked": False,
    "next_allowed_step": review["next_allowed_step"],
    "not_authorized": review["not_authorized"]
}
project["last_updated_for_broader_standardized_single_modality_review_utc"] = NOW
PROJECT_JSON.write_text(json.dumps(project, indent=2, sort_keys=True) + "\n", encoding="utf-8")

print("OK_REVIEW_CLOSEOUT_WRITTEN")
print(str(REVIEW_MD))
print(str(REVIEW_JSON))
PY
  echo

  echo "===== 2) validate docs ====="
  "$PY" -m json.tool docs/idare_broader_standardized_single_modality_evaluation_review_status.json >/dev/null
  "$PY" -m json.tool docs/project_status_current.json >/dev/null
  echo "OK_JSON"

  grep -n "Status\|Review Decision\|Result Summary\|Mainline After Review\|Next Allowed Step" docs/idare_broader_standardized_single_modality_evaluation_review_status.md
  grep -n "broader standardized single-modality evaluation review\|Human review of the broader" docs/project_status_current.md
  echo

  echo "===== 3) status before commit ====="
  git status --short --branch
  echo

  echo "===== 4) commit review closeout ====="
  git add \
    docs/idare_broader_standardized_single_modality_evaluation_review_status.md \
    docs/idare_broader_standardized_single_modality_evaluation_review_status.json \
    docs/project_status_current.md \
    docs/project_status_current.json

  git commit -m "docs: review broader I-DARE single-modality evaluation"
  echo "COMMIT_EXIT=$?"
  echo

  echo "===== 5) final status ====="
  git status --short --branch
} > "$LOG" 2>&1

cat "$LOG"
echo "LOG_SAVED_TO=$LOG"
