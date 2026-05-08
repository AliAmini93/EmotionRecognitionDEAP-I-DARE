#!/usr/bin/env bash
# Build combined broader-evaluation report and commit validated primary outputs.
# This does NOT run training and does NOT push.

cd /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE || exit 1

LOG=/tmp/idare_build_broader_eval_report.log

{
  echo "===== 0) start status ====="
  git status --short --branch
  echo

  PY=".venv/bin/python"
  if [ ! -x "$PY" ]; then PY="python3"; fi
  echo "PY=$PY"
  echo

  echo "===== 1) build combined report and update roadmap ====="
  "$PY" - <<'PY'
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev

DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

REPORT_MD = DOCS / "idare_broader_standardized_single_modality_evaluation_report.md"
REPORT_JSON = DOCS / "idare_broader_standardized_single_modality_evaluation_report.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

FILES = {
    "EEG-B0": {
        "modality": "EEG",
        "condition": "baseline",
        "label": "EEG STIM-BSL-only",
        "json": DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary.json",
        "md": DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary.md",
        "pred": DOCS / "idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv",
    },
    "EEG-B1": {
        "modality": "EEG",
        "condition": "bsl_stats",
        "label": "EEG STIM-BSL + BSL-stats",
        "json": DOCS / "idare_broader_eval_eeg_bsl_stats_primary.json",
        "md": DOCS / "idare_broader_eval_eeg_bsl_stats_primary.md",
        "pred": DOCS / "idare_broader_eval_eeg_bsl_stats_primary_predictions.csv",
    },
    "EMG-B0": {
        "modality": "EMG",
        "condition": "baseline",
        "label": "EMG feature-only",
        "json": DOCS / "idare_broader_eval_emg_feature_only_primary.json",
        "md": DOCS / "idare_broader_eval_emg_feature_only_primary.md",
        "pred": DOCS / "idare_broader_eval_emg_feature_only_primary_predictions.csv",
    },
    "EMG-B1": {
        "modality": "EMG",
        "condition": "bsl_stats",
        "label": "EMG feature + BSL-stats",
        "json": DOCS / "idare_broader_eval_emg_bsl_stats_primary.json",
        "md": DOCS / "idare_broader_eval_emg_bsl_stats_primary.md",
        "pred": DOCS / "idare_broader_eval_emg_bsl_stats_primary_predictions.csv",
    },
}

EXPECTED_FOLD1 = [6, 7, 8, 13, 28, 38, 43, 54, 58, 59, 65]
EXPECTED_RUNS_PER_CONDITION = 24
EXPECTED_PRED_ROWS = 8064


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def as_float(x):
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None


def nested_get(obj, path):
    cur = obj
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def first_float(obj, paths):
    for path in paths:
        v = nested_get(obj, path)
        v = as_float(v)
        if v is not None:
            return v
    return None


def metric(run, name):
    paths = []
    if name == "macro_f1":
        paths = [
            ("final_macro_f1",),
            ("macro_f1",),
            ("final", "macro_f1"),
            ("metrics", "macro_f1"),
            ("final_metrics", "macro_f1"),
            ("eval", "macro_f1"),
        ]
    elif name == "balanced_accuracy":
        paths = [
            ("final_balanced_accuracy",),
            ("balanced_accuracy",),
            ("final", "balanced_accuracy"),
            ("metrics", "balanced_accuracy"),
            ("final_metrics", "balanced_accuracy"),
            ("eval", "balanced_accuracy"),
        ]
    elif name == "accuracy":
        paths = [
            ("final_accuracy",),
            ("accuracy",),
            ("final", "accuracy"),
            ("metrics", "accuracy"),
            ("final_metrics", "accuracy"),
            ("eval", "accuracy"),
        ]
    elif name == "majority_accuracy":
        paths = [
            ("majority_accuracy",),
            ("majority_baseline", "accuracy"),
            ("final", "majority_baseline", "accuracy"),
            ("metrics", "majority_baseline", "accuracy"),
        ]
    elif name == "threshold_macro_f1":
        paths = [
            ("threshold_best_macro_f1",),
            ("best_threshold_macro_f1",),
            ("threshold_sweep", "best", "macro_f1"),
            ("final", "threshold_sweep", "best", "macro_f1"),
            ("metrics", "threshold_sweep", "best", "macro_f1"),
        ]
    elif name == "threshold_balanced_accuracy":
        paths = [
            ("threshold_best_balanced_accuracy",),
            ("best_threshold_balanced_accuracy",),
            ("threshold_sweep", "best", "balanced_accuracy"),
            ("final", "threshold_sweep", "best", "balanced_accuracy"),
            ("metrics", "threshold_sweep", "best", "balanced_accuracy"),
        ]
    return first_float(run, paths)


def summarize(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return {"mean": None, "std": None, "min": None, "max": None}
    return {
        "mean": float(mean(vals)),
        "std": float(pstdev(vals)) if len(vals) > 1 else 0.0,
        "min": float(min(vals)),
        "max": float(max(vals)),
    }


def fmt(x):
    if x is None:
        return "NA"
    return f"{float(x):.4f}"


def pred_row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as f:
        return sum(1 for _ in f) - 1


def bool_one_class(run):
    for path in [("one_class_pred",), ("final", "one_class_pred"), ("metrics", "one_class_pred")]:
        cur = nested_get(run, path)
        if isinstance(cur, bool):
            return cur
    return False


# Validate and collect runs.
condition_data = {}
validation = {}
for cid, meta in FILES.items():
    for key in ["json", "md", "pred"]:
        if not meta[key].exists():
            raise SystemExit(f"ERROR: missing {cid} {key}: {meta[key]}")

    data = load_json(meta["json"])
    runs = data.get("runs", [])
    if len(runs) != EXPECTED_RUNS_PER_CONDITION:
        raise SystemExit(f"ERROR: {cid} expected {EXPECTED_RUNS_PER_CONDITION} runs, got {len(runs)}")

    first = runs[0]
    first_fold = first.get("val_subjects")
    if first_fold != EXPECTED_FOLD1:
        raise SystemExit(f"ERROR: {cid} fold1 mismatch: {first_fold}")

    rows = pred_row_count(meta["pred"])
    if rows != EXPECTED_PRED_ROWS:
        raise SystemExit(f"ERROR: {cid} expected {EXPECTED_PRED_ROWS} prediction rows, got {rows}")

    condition_data[cid] = {"meta": meta, "data": data, "runs": runs}
    validation[cid] = {
        "n_runs": len(runs),
        "prediction_rows": rows,
        "first_fold_val_subjects": first_fold,
        "json": str(meta["json"]),
        "md": str(meta["md"]),
        "predictions_csv": str(meta["pred"]),
    }

# Aggregate per condition/task/recipe.
aggregates = []
best_by_condition_task = {}

for cid, pack in condition_data.items():
    meta = pack["meta"]
    grouped = defaultdict(list)
    for run in pack["runs"]:
        task = run.get("task")
        recipe = run.get("recipe")
        if task not in {"valence", "arousal"}:
            raise SystemExit(f"ERROR: {cid} unexpected task: {task}")
        if recipe not in {"ce_class_weighted", "balanced_sampler_ce"}:
            raise SystemExit(f"ERROR: {cid} unexpected recipe: {recipe}")
        grouped[(task, recipe)].append(run)

    for (task, recipe), rows in sorted(grouped.items()):
        if len(rows) != 6:
            raise SystemExit(f"ERROR: {cid} {task} {recipe} expected 6 folds, got {len(rows)}")

        macro = [metric(r, "macro_f1") for r in rows]
        bal = [metric(r, "balanced_accuracy") for r in rows]
        acc = [metric(r, "accuracy") for r in rows]
        majority = [metric(r, "majority_accuracy") for r in rows]
        thr_macro = [metric(r, "threshold_macro_f1") for r in rows]
        thr_bal = [metric(r, "threshold_balanced_accuracy") for r in rows]
        one_class = sum(1 for r in rows if bool_one_class(r))

        if any(v is None for v in macro):
            raise SystemExit(f"ERROR: {cid} {task} {recipe} missing final macro F1")

        row = {
            "condition_id": cid,
            "modality": meta["modality"],
            "condition": meta["condition"],
            "label": meta["label"],
            "task": task,
            "recipe": recipe,
            "n_folds": len(rows),
            "final_macro_f1": summarize(macro),
            "final_balanced_accuracy": summarize(bal),
            "final_accuracy": summarize(acc),
            "majority_accuracy": summarize(majority),
            "threshold_best_macro_f1": summarize(thr_macro),
            "threshold_best_balanced_accuracy": summarize(thr_bal),
            "one_class_final_runs": int(one_class),
        }
        aggregates.append(row)

for row in aggregates:
    key = (row["condition_id"], row["task"])
    old = best_by_condition_task.get(key)
    if old is None or (row["final_macro_f1"]["mean"] or -1) > (old["final_macro_f1"]["mean"] or -1):
        best_by_condition_task[key] = row

# Build comparisons.
comparisons = []
for modality, b0, b1 in [("EEG", "EEG-B0", "EEG-B1"), ("EMG", "EMG-B0", "EMG-B1")]:
    for task in ["valence", "arousal"]:
        base = best_by_condition_task[(b0, task)]
        side = best_by_condition_task[(b1, task)]
        dm = (side["final_macro_f1"]["mean"] or 0) - (base["final_macro_f1"]["mean"] or 0)
        db = (side["final_balanced_accuracy"]["mean"] or 0) - (base["final_balanced_accuracy"]["mean"] or 0)

        if dm >= 0.02:
            interpretation = "sidecar_better_broader_eval"
        elif dm <= -0.02:
            interpretation = "baseline_better_broader_eval"
        else:
            interpretation = "roughly_neutral_or_mixed"

        comparisons.append({
            "modality": modality,
            "task": task,
            "baseline_condition": b0,
            "sidecar_condition": b1,
            "baseline_recipe": base["recipe"],
            "sidecar_recipe": side["recipe"],
            "baseline_final_macro_f1_mean": base["final_macro_f1"]["mean"],
            "sidecar_final_macro_f1_mean": side["final_macro_f1"]["mean"],
            "delta_final_macro_f1": dm,
            "baseline_final_balanced_accuracy_mean": base["final_balanced_accuracy"]["mean"],
            "sidecar_final_balanced_accuracy_mean": side["final_balanced_accuracy"]["mean"],
            "delta_final_balanced_accuracy": db,
            "baseline_one_class_final_runs": base["one_class_final_runs"],
            "sidecar_one_class_final_runs": side["one_class_final_runs"],
            "interpretation": interpretation,
        })

# Conservative decision.
decision = {
    "status": "primary_matrix_complete_pending_human_review",
    "mainline_changed": False,
    "evidence_level": "broader standardized single-modality primary matrix; not final LOSO",
    "summary": "All 96 authorized primary runs completed and validated. Interpret before changing any mainline.",
    "next_allowed_step": "Human review / closeout decision for the broader standardized single-modality evaluation.",
    "not_authorized_from_this_report": [
        "EEG+EMG fusion",
        "full model(BSL, STIM, STIM-BSL)",
        "final LOSO / final paper claim",
        "locking midpoint_as_high",
        "raw EMG mainline",
        "architecture ablations",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "optional robustness seed 13 without explicit objective",
    ],
}

# Write JSON.
out = {
    "status": "primary_matrix_complete",
    "created_or_updated_utc": NOW,
    "objective": "Broader standardized I-DARE single-modality primary matrix",
    "evidence_level": "broader standardized primary matrix, not final LOSO",
    "primary_matrix": {
        "conditions": 4,
        "tasks": 2,
        "recipes": 2,
        "folds": 6,
        "seeds": [11],
        "total_runs": 96,
    },
    "validation": validation,
    "aggregates": aggregates,
    "best_by_condition_task": {f"{k[0]}:{k[1]}": v for k, v in best_by_condition_task.items()},
    "comparisons": comparisons,
    "decision": decision,
}
REPORT_JSON.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

# Write MD.
lines = []
lines.append("# I-DARE Broader Standardized Single-Modality Evaluation Report\n")
lines.append("## Status\n")
lines.append("Primary matrix complete.\n")
lines.append("This is broader standardized single-modality evidence, not final LOSO evidence.\n")
lines.append("No mainline is changed automatically by this report.\n")
lines.append("## Run Matrix\n")
lines.append("| Item | Value |")
lines.append("|---|---:|")
lines.append("| Conditions | 4 |")
lines.append("| Tasks | 2 |")
lines.append("| Recipes | 2 |")
lines.append("| Folds | 6 |")
lines.append("| Seeds | 1 (`11`) |")
lines.append("| Total runs | 96 |")
lines.append("\n## Validation\n")
lines.append("| Condition | Runs | Prediction rows | Fold 1 aligned? |")
lines.append("|---|---:|---:|---|")
for cid in ["EEG-B0", "EEG-B1", "EMG-B0", "EMG-B1"]:
    v = validation[cid]
    aligned = "yes" if v["first_fold_val_subjects"] == EXPECTED_FOLD1 else "no"
    lines.append(f"| {cid} | {v['n_runs']} | {v['prediction_rows']} | {aligned} |")

lines.append("\n## Best Recipe Per Condition and Task\n")
lines.append("| Condition | Task | Best recipe | Macro F1 | Balanced acc | Accuracy | One-class runs |")
lines.append("|---|---|---|---:|---:|---:|---:|")
for cid in ["EEG-B0", "EEG-B1", "EMG-B0", "EMG-B1"]:
    for task in ["valence", "arousal"]:
        r = best_by_condition_task[(cid, task)]
        lines.append(
            f"| {cid} | {task} | {r['recipe']} | {fmt(r['final_macro_f1']['mean'])} | "
            f"{fmt(r['final_balanced_accuracy']['mean'])} | {fmt(r['final_accuracy']['mean'])} | "
            f"{r['one_class_final_runs']} |"
        )

lines.append("\n## Direct Baseline vs BSL-stats Comparison\n")
lines.append("| Modality | Task | Baseline recipe | Baseline macro F1 | Sidecar recipe | Sidecar macro F1 | Delta macro F1 | Baseline bal acc | Sidecar bal acc | Delta bal acc | Interpretation |")
lines.append("|---|---|---|---:|---|---:|---:|---:|---:|---:|---|")
for c in comparisons:
    lines.append(
        f"| {c['modality']} | {c['task']} | {c['baseline_recipe']} | "
        f"{fmt(c['baseline_final_macro_f1_mean'])} | {c['sidecar_recipe']} | "
        f"{fmt(c['sidecar_final_macro_f1_mean'])} | {fmt(c['delta_final_macro_f1'])} | "
        f"{fmt(c['baseline_final_balanced_accuracy_mean'])} | "
        f"{fmt(c['sidecar_final_balanced_accuracy_mean'])} | "
        f"{fmt(c['delta_final_balanced_accuracy'])} | {c['interpretation']} |"
    )

lines.append("\n## Interpretation\n")
lines.append("- All 96 authorized primary runs completed and produced valid JSON plus prediction CSVs.\n")
lines.append("- Fold 1 alignment was verified across all four conditions.\n")
lines.append("- This report does not automatically change the EEG or EMG mainline.\n")
lines.append("- This report does not authorize fusion or final LOSO claims.\n")
lines.append("- A human review / closeout decision is the next step.\n")

lines.append("\n## Not Authorized From This Report\n")
for item in decision["not_authorized_from_this_report"]:
    lines.append(f"- {item}")

lines.append("\n## Next Allowed Step\n")
lines.append("Human review / closeout decision for the broader standardized single-modality evaluation.\n")

REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

# Update project roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
row = "| I-DARE broader standardized single-modality evaluation primary report | 96-run primary matrix completed; combined report generated; pending human review | yes | `docs/idare_broader_standardized_single_modality_evaluation_report.md` | Human review / closeout decision before any mainline change or future objective. | EEG+EMG fusion; full paired BSL/STIM neural model; final LOSO claim. |"
if "I-DARE broader standardized single-modality evaluation primary report" not in project_md:
    anchor = "| EEG+EMG fusion | not started intentionally | no | `docs/idare_eeg_bsl_stats_ablation_status.md`<br>`docs/idare_emg_bsl_stats_ablation_status.md` | Start only after current baseline/ablation status is indexed and compared cleanly. | All fusion experiments. |"
    project_md = project_md.replace(anchor, row + "\n" + anchor)

note = "- The broader standardized single-modality primary matrix is complete in `docs/idare_broader_standardized_single_modality_evaluation_report.md`; next step is human review / closeout, not fusion."
if note not in project_md:
    project_md = project_md.replace(
        "- Do not claim final performance from the smoke reports.",
        "- Do not claim final performance from the smoke reports.\n" + note,
    )

PROJECT_MD.write_text(project_md, encoding="utf-8")

project = load_json(PROJECT_JSON)
project.setdefault("sources", {})["idare_broader_standardized_single_modality_evaluation_report"] = str(REPORT_MD)
project.setdefault("run_summaries", {})["idare_broader_standardized_single_modality_evaluation_primary_matrix"] = out
project.setdefault("decisions", {})["idare_broader_standardized_single_modality_evaluation_primary_matrix"] = decision
project["last_updated_for_broader_standardized_single_modality_primary_report_utc"] = NOW
PROJECT_JSON.write_text(json.dumps(project, indent=2, sort_keys=True) + "\n", encoding="utf-8")

print("OK_COMBINED_REPORT_WRITTEN")
print(str(REPORT_MD))
print(str(REPORT_JSON))
PY
  echo

  echo "===== 2) validate combined outputs ====="
  "$PY" -m json.tool docs/idare_broader_standardized_single_modality_evaluation_report.json >/dev/null
  "$PY" -m json.tool docs/project_status_current.json >/dev/null
  echo "OK_JSON"

  grep -n "Status\|Validation\|Direct Baseline vs BSL-stats Comparison\|Next Allowed Step" docs/idare_broader_standardized_single_modality_evaluation_report.md
  grep -n "broader standardized single-modality evaluation primary report\|primary matrix is complete" docs/project_status_current.md
  echo

  echo "===== 3) file list ====="
  ls -lh \
    docs/idare_broader_standardized_single_modality_evaluation_report.md \
    docs/idare_broader_standardized_single_modality_evaluation_report.json \
    docs/idare_broader_eval_*_primary*
  echo

  echo "===== 4) status before commit ====="
  git status --short --branch
  echo

  echo "===== 5) commit reports and outputs ====="
  git add \
    docs/idare_broader_eval_eeg_stim_bsl_only_primary.md \
    docs/idare_broader_eval_eeg_stim_bsl_only_primary.json \
    docs/idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv \
    docs/idare_broader_eval_eeg_bsl_stats_primary.md \
    docs/idare_broader_eval_eeg_bsl_stats_primary.json \
    docs/idare_broader_eval_eeg_bsl_stats_primary_predictions.csv \
    docs/idare_broader_eval_emg_feature_only_primary.md \
    docs/idare_broader_eval_emg_feature_only_primary.json \
    docs/idare_broader_eval_emg_feature_only_primary_predictions.csv \
    docs/idare_broader_eval_emg_bsl_stats_primary.md \
    docs/idare_broader_eval_emg_bsl_stats_primary.json \
    docs/idare_broader_eval_emg_bsl_stats_primary_predictions.csv \
    docs/idare_broader_standardized_single_modality_evaluation_report.md \
    docs/idare_broader_standardized_single_modality_evaluation_report.json \
    docs/project_status_current.md \
    docs/project_status_current.json

  git commit -m "exp: run broader I-DARE single-modality evaluation"
  echo "COMMIT_EXIT=$?"
  echo

  echo "===== 6) final status ====="
  git status --short --branch
} > "$LOG" 2>&1

cat "$LOG"
echo "LOG_SAVED_TO=$LOG"
