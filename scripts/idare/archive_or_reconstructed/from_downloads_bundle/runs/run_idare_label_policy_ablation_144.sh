#!/usr/bin/env bash
# Run the authorized I-DARE controlled label-policy ablation primary matrix.
# This RUNS TRAINING: 144 runs total.
# It builds the required combined EEG/EMG/report outputs.
# It does NOT commit and does NOT push.
#
# Log:
#   /tmp/idare_label_policy_ablation_run.log
#
# If the terminal closes:
#   cat /tmp/idare_label_policy_ablation_run.log

cd /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE || exit 1

LOG=/tmp/idare_label_policy_ablation_run.log
TMP_DIR=/tmp/idare_label_policy_ablation_parts

{
  echo "===== 0) start I-DARE label-policy ablation ====="
  date -u
  git status --short --branch
  echo

  PY=".venv/bin/python"
  if [ ! -x "$PY" ]; then PY="python3"; fi
  echo "PY=$PY"
  "$PY" - <<'PY'
import sys
print(sys.executable)
import numpy, pandas, torch
print("OK_IMPORTS")
print("cuda_available=", torch.cuda.is_available())
PY
  echo

  echo "===== 1) require clean repo before running ====="
  if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: repo is not clean. Stop before running label-policy ablation."
    git status --short --branch
    exit 1
  fi
  echo "OK_REPO_CLEAN"
  echo

  echo "===== 2) check required cache artifacts ====="
  missing=0
  for f in \
    .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy \
    .cache/idare_eeg_cache_index_baseline_corrected.csv \
    .cache/idare_emg_features.npy \
    .cache/idare_emg_feature_cache_index.csv
  do
    if [ -f "$f" ]; then
      ls -lh "$f"
    else
      echo "MISSING: $f"
      missing=1
    fi
  done
  if [ "$missing" -ne 0 ]; then
    echo "ERROR: required cache missing"
    exit 1
  fi
  echo

  echo "===== 3) compile scripts ====="
  for s in \
    scripts/20_run_idare_eeg_cache_recipe_stabilization.py \
    scripts/30_run_idare_emg_feature_smoke.py
  do
    "$PY" -B -m py_compile "$s"
    echo "OK_COMPILE: $s"
  done
  echo

  echo "===== 4) prepare temp and remove stale final outputs ====="
  rm -rf "$TMP_DIR"
  mkdir -p "$TMP_DIR"

  rm -f \
    docs/idare_label_policy_ablation_eeg_primary.md \
    docs/idare_label_policy_ablation_eeg_primary.json \
    docs/idare_label_policy_ablation_eeg_primary_predictions.csv \
    docs/idare_label_policy_ablation_emg_primary.md \
    docs/idare_label_policy_ablation_emg_primary.json \
    docs/idare_label_policy_ablation_emg_primary_predictions.csv \
    docs/idare_label_policy_ablation_report.md \
    docs/idare_label_policy_ablation_report.json

  echo "OK_CLEAN_OUTPUT_TARGETS"
  echo

  run_cmd() {
    name="$1"
    shift
    echo
    echo "===== RUN: $name ====="
    date -u
    "$@"
    code=$?
    echo "EXIT_$name=$code"
    date -u
    if [ "$code" -ne 0 ]; then
      echo "ERROR: $name failed. Stop label-policy matrix."
      exit "$code"
    fi
  }

  POLICIES=(discard_midpoint midpoint_as_low midpoint_as_high)

  echo "===== 5) run EEG label-policy ablation: 72 runs ====="
  for policy in "${POLICIES[@]}"; do
    run_cmd "EEG_LABEL_POLICY_${policy}" \
      "$PY" scripts/20_run_idare_eeg_cache_recipe_stabilization.py \
        --cache-npy .cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy \
        --cache-index .cache/idare_eeg_cache_index_baseline_corrected.csv \
        --tasks valence arousal \
        --label-policy "$policy" \
        --recipes ce_class_weighted balanced_sampler_ce \
        --folds 6 \
        --seeds 11 \
        --epochs 12 \
        --lr 1e-3 \
        --batch-size 64 \
        --weight-decay 1e-3 \
        --grad-clip 1.0 \
        --max-runs 0 \
        --out-md "$TMP_DIR/eeg_${policy}.md" \
        --out-json "$TMP_DIR/eeg_${policy}.json" \
        --out-predictions-csv "$TMP_DIR/eeg_${policy}_predictions.csv"
  done

  echo
  echo "===== 6) run EMG label-policy ablation: 72 runs ====="
  for policy in "${POLICIES[@]}"; do
    run_cmd "EMG_LABEL_POLICY_${policy}" \
      "$PY" scripts/30_run_idare_emg_feature_smoke.py \
        --feature-npy .cache/idare_emg_features.npy \
        --feature-index .cache/idare_emg_feature_cache_index.csv \
        --tasks valence arousal \
        --label-policy "$policy" \
        --recipes ce_class_weighted balanced_sampler_ce \
        --folds 6 \
        --seeds 11 \
        --epochs 20 \
        --lr 1e-3 \
        --batch-size 128 \
        --weight-decay 1e-3 \
        --grad-clip 1.0 \
        --hidden-dim 64 \
        --max-runs 0 \
        --out-md "$TMP_DIR/emg_${policy}.md" \
        --out-json "$TMP_DIR/emg_${policy}.json" \
        --out-predictions-csv "$TMP_DIR/emg_${policy}_predictions.csv"
  done

  echo
  echo "===== 7) combine reports ====="
  "$PY" - <<'PY'
import csv
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev

TMP = Path("/tmp/idare_label_policy_ablation_parts")
DOCS = Path("docs")
NOW = datetime.now(timezone.utc).isoformat()

POLICIES = ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"]
MODS = {
    "eeg": {
        "label": "EEG STIM-BSL-only",
        "condition": "EEG-LP",
        "prefix": "eeg",
        "out_md": DOCS / "idare_label_policy_ablation_eeg_primary.md",
        "out_json": DOCS / "idare_label_policy_ablation_eeg_primary.json",
        "out_csv": DOCS / "idare_label_policy_ablation_eeg_primary_predictions.csv",
    },
    "emg": {
        "label": "EMG feature-only",
        "condition": "EMG-LP",
        "prefix": "emg",
        "out_md": DOCS / "idare_label_policy_ablation_emg_primary.md",
        "out_json": DOCS / "idare_label_policy_ablation_emg_primary.json",
        "out_csv": DOCS / "idare_label_policy_ablation_emg_primary_predictions.csv",
    },
}

REPORT_MD = DOCS / "idare_label_policy_ablation_report.md"
REPORT_JSON = DOCS / "idare_label_policy_ablation_report.json"

EXPECTED_FOLD1 = [6, 7, 8, 13, 28, 38, 43, 54, 58, 59, 65]


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
        v = as_float(nested_get(obj, path))
        if v is not None:
            return v
    return None


def metric(run, name):
    if name == "macro_f1":
        paths = [("final_macro_f1",), ("macro_f1",), ("final", "macro_f1"), ("metrics", "macro_f1"), ("final_metrics", "macro_f1")]
    elif name == "balanced_accuracy":
        paths = [("final_balanced_accuracy",), ("balanced_accuracy",), ("final", "balanced_accuracy"), ("metrics", "balanced_accuracy"), ("final_metrics", "balanced_accuracy")]
    elif name == "accuracy":
        paths = [("final_accuracy",), ("accuracy",), ("final", "accuracy"), ("metrics", "accuracy"), ("final_metrics", "accuracy")]
    elif name == "majority_accuracy":
        paths = [("majority_accuracy",), ("majority_baseline", "accuracy"), ("metrics", "majority_baseline", "accuracy")]
    elif name == "threshold_macro_f1":
        paths = [("threshold_best_macro_f1",), ("best_threshold_macro_f1",), ("threshold_sweep", "best", "macro_f1")]
    elif name == "threshold_balanced_accuracy":
        paths = [("threshold_best_balanced_accuracy",), ("best_threshold_balanced_accuracy",), ("threshold_sweep", "best", "balanced_accuracy")]
    else:
        return None
    return first_float(run, paths)


def summarize(values):
    vals = [v for v in values if v is not None]
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


def one_class(run):
    v = run.get("one_class_pred")
    if isinstance(v, bool):
        return v
    v = nested_get(run, ("metrics", "one_class_pred"))
    return bool(v) if isinstance(v, bool) else False


def get_fold_id(run):
    return run.get("fold_id", run.get("fold"))


def csv_row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as f:
        return sum(1 for _ in f) - 1


def combine_csv(input_paths, out_path: Path, modality: str):
    fieldnames = []
    rows = []
    for path in input_paths:
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            local_fields = list(reader.fieldnames or [])
            for field in ["modality", "source_file"]:
                if field not in local_fields:
                    local_fields = [field] + local_fields
            for field in local_fields:
                if field not in fieldnames:
                    fieldnames.append(field)
            for row in reader:
                row = dict(row)
                row["modality"] = modality.upper()
                row["source_file"] = str(path)
                rows.append(row)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def build_modality(mod_key, meta):
    all_runs = []
    sources = {}
    validation = {}
    csv_paths = []

    for policy in POLICIES:
        json_path = TMP / f"{mod_key}_{policy}.json"
        md_path = TMP / f"{mod_key}_{policy}.md"
        csv_path = TMP / f"{mod_key}_{policy}_predictions.csv"
        for path in [json_path, md_path, csv_path]:
            if not path.exists():
                raise SystemExit(f"ERROR: missing {path}")

        data = load_json(json_path)
        runs = data.get("runs", [])
        if len(runs) != 24:
            raise SystemExit(f"ERROR: {mod_key} {policy} expected 24 runs, got {len(runs)}")

        first = runs[0]
        if first.get("val_subjects") != EXPECTED_FOLD1:
            raise SystemExit(f"ERROR: {mod_key} {policy} fold1 mismatch: {first.get('val_subjects')}")

        pred_rows = csv_row_count(csv_path)
        if pred_rows <= 0:
            raise SystemExit(f"ERROR: empty predictions CSV for {mod_key} {policy}")

        for run in runs:
            run = dict(run)
            run.setdefault("label_policy", run.get("policy", policy))
            run.setdefault("policy", run.get("label_policy", policy))
            run["source_policy"] = policy
            run["modality"] = mod_key.upper()
            all_runs.append(run)

        sources[policy] = {
            "json": str(json_path),
            "md": str(md_path),
            "predictions_csv": str(csv_path),
        }
        validation[policy] = {
            "n_runs": len(runs),
            "prediction_rows": pred_rows,
            "first_fold_val_subjects": first.get("val_subjects"),
        }
        csv_paths.append(csv_path)

    # Aggregate by task/policy/recipe.
    grouped = defaultdict(list)
    for run in all_runs:
        task = run.get("task")
        policy = run.get("policy") or run.get("label_policy") or run.get("source_policy")
        recipe = run.get("recipe")
        if task not in {"valence", "arousal"}:
            raise SystemExit(f"ERROR: unexpected task in {mod_key}: {task}")
        if policy not in set(POLICIES):
            raise SystemExit(f"ERROR: unexpected policy in {mod_key}: {policy}")
        if recipe not in {"ce_class_weighted", "balanced_sampler_ce"}:
            raise SystemExit(f"ERROR: unexpected recipe in {mod_key}: {recipe}")
        grouped[(task, policy, recipe)].append(run)

    aggregates = []
    for (task, policy, recipe), rows in sorted(grouped.items()):
        if len(rows) != 6:
            raise SystemExit(f"ERROR: {mod_key} {task} {policy} {recipe} expected 6 folds, got {len(rows)}")
        row = {
            "modality": mod_key.upper(),
            "condition": meta["condition"],
            "task": task,
            "policy": policy,
            "recipe": recipe,
            "n_folds": len(rows),
            "fold_ids": sorted(int(get_fold_id(r)) for r in rows),
            "final_macro_f1": summarize([metric(r, "macro_f1") for r in rows]),
            "final_balanced_accuracy": summarize([metric(r, "balanced_accuracy") for r in rows]),
            "final_accuracy": summarize([metric(r, "accuracy") for r in rows]),
            "majority_accuracy": summarize([metric(r, "majority_accuracy") for r in rows]),
            "threshold_best_macro_f1": summarize([metric(r, "threshold_macro_f1") for r in rows]),
            "threshold_best_balanced_accuracy": summarize([metric(r, "threshold_balanced_accuracy") for r in rows]),
            "one_class_final_runs": int(sum(1 for r in rows if one_class(r))),
        }
        if row["final_macro_f1"]["mean"] is None:
            raise SystemExit(f"ERROR: missing macro_f1 for {mod_key} {task} {policy} {recipe}")
        aggregates.append(row)

    # Best recipe by task/policy.
    best = {}
    for row in aggregates:
        key = (row["task"], row["policy"])
        old = best.get(key)
        if old is None or (row["final_macro_f1"]["mean"] or -1) > (old["final_macro_f1"]["mean"] or -1):
            best[key] = row

    # Best policy by task.
    best_policy_by_task = {}
    for task in ["valence", "arousal"]:
        candidates = [row for (t, p), row in best.items() if t == task]
        best_policy_by_task[task] = max(candidates, key=lambda r: r["final_macro_f1"]["mean"] or -1)

    pred_rows_total = combine_csv(csv_paths, meta["out_csv"], mod_key)

    out = {
        "status": "primary_matrix_complete",
        "created_or_updated_utc": NOW,
        "modality": mod_key.upper(),
        "label": meta["label"],
        "condition": meta["condition"],
        "matrix": {
            "tasks": 2,
            "policies": POLICIES,
            "recipes": ["ce_class_weighted", "balanced_sampler_ce"],
            "folds": 6,
            "seeds": [11],
            "total_runs": len(all_runs),
        },
        "sources": sources,
        "validation": validation,
        "prediction_rows_total": pred_rows_total,
        "runs": all_runs,
        "aggregates": aggregates,
        "best_by_task_policy": {f"{k[0]}:{k[1]}": v for k, v in best.items()},
        "best_policy_by_task": best_policy_by_task,
    }
    meta["out_json"].write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = []
    lines.append(f"# I-DARE Label-Policy Ablation: {meta['label']}\n")
    lines.append("## Status\n")
    lines.append("Primary label-policy matrix complete.\n")
    lines.append("This is controlled ablation evidence, not final LOSO evidence.\n")
    lines.append("## Validation\n")
    lines.append("| Policy | Runs | Prediction rows | Fold 1 aligned? |")
    lines.append("|---|---:|---:|---|")
    for policy in POLICIES:
        v = validation[policy]
        aligned = "yes" if v["first_fold_val_subjects"] == EXPECTED_FOLD1 else "no"
        lines.append(f"| {policy} | {v['n_runs']} | {v['prediction_rows']} | {aligned} |")

    lines.append("\n## Best Recipe Per Task and Policy\n")
    lines.append("| Task | Policy | Best recipe | Macro F1 | Balanced acc | Accuracy | One-class runs |")
    lines.append("|---|---|---|---:|---:|---:|---:|")
    for task in ["valence", "arousal"]:
        for policy in POLICIES:
            r = best[(task, policy)]
            lines.append(
                f"| {task} | {policy} | {r['recipe']} | {fmt(r['final_macro_f1']['mean'])} | "
                f"{fmt(r['final_balanced_accuracy']['mean'])} | {fmt(r['final_accuracy']['mean'])} | "
                f"{r['one_class_final_runs']} |"
            )

    lines.append("\n## Best Policy Per Task\n")
    lines.append("| Task | Best policy | Recipe | Macro F1 | Balanced acc | Interpretation |")
    lines.append("|---|---|---|---:|---:|---|")
    for task in ["valence", "arousal"]:
        r = best_policy_by_task[task]
        lines.append(
            f"| {task} | {r['policy']} | {r['recipe']} | {fmt(r['final_macro_f1']['mean'])} | "
            f"{fmt(r['final_balanced_accuracy']['mean'])} | pending human review |"
        )

    lines.append("\n## Next Step\n")
    lines.append("Use the combined label-policy report for human review before locking any final policy.\n")
    meta["out_md"].write_text("\n".join(lines) + "\n", encoding="utf-8")

    return out


modality_outputs = {mod_key: build_modality(mod_key, meta) for mod_key, meta in MODS.items()}

# Combined report.
comparisons = []
for mod_key, out in modality_outputs.items():
    for task, best_row in out["best_policy_by_task"].items():
        by_policy = []
        for policy in POLICIES:
            row = out["best_by_task_policy"][f"{task}:{policy}"]
            by_policy.append({
                "policy": policy,
                "recipe": row["recipe"],
                "final_macro_f1_mean": row["final_macro_f1"]["mean"],
                "final_balanced_accuracy_mean": row["final_balanced_accuracy"]["mean"],
                "one_class_final_runs": row["one_class_final_runs"],
            })
        comparisons.append({
            "modality": mod_key.upper(),
            "task": task,
            "best_policy": best_row["policy"],
            "best_recipe": best_row["recipe"],
            "best_macro_f1_mean": best_row["final_macro_f1"]["mean"],
            "best_balanced_accuracy_mean": best_row["final_balanced_accuracy"]["mean"],
            "policies": by_policy,
        })

decision = {
    "status": "primary_matrix_complete_pending_human_review",
    "final_label_policy_locked": False,
    "evidence_level": "controlled label-policy primary matrix, not final LOSO",
    "next_allowed_step": "Human review / closeout decision for label-policy ablation.",
    "not_authorized_from_this_report": [
        "EEG+EMG fusion",
        "full model(BSL, STIM, STIM-BSL)",
        "final LOSO / final paper claim",
        "locking a final label policy without review",
        "raw EMG mainline",
        "architecture ablations",
        "data augmentation",
        "SupCon / VREx / domain generalization",
    ],
}

report = {
    "status": "primary_matrix_complete",
    "created_or_updated_utc": NOW,
    "objective": "I-DARE controlled label-policy ablation",
    "evidence_level": "controlled ablation primary matrix, not final LOSO",
    "matrix": {
        "modalities": 2,
        "tasks": 2,
        "policies": 3,
        "recipes": 2,
        "folds": 6,
        "seeds": [11],
        "total_runs": 144,
    },
    "modality_reports": {
        "eeg": str(MODS["eeg"]["out_json"]),
        "emg": str(MODS["emg"]["out_json"]),
    },
    "comparisons": comparisons,
    "decision": decision,
}
REPORT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

lines = []
lines.append("# I-DARE Controlled Label-Policy Ablation Report\n")
lines.append("## Status\n")
lines.append("Primary matrix complete.\n")
lines.append("This is controlled label-policy ablation evidence, not final LOSO evidence.\n")
lines.append("No final label policy is locked automatically by this report.\n")
lines.append("## Run Matrix\n")
lines.append("| Item | Value |")
lines.append("|---|---:|")
lines.append("| Modalities | 2 |")
lines.append("| Tasks | 2 |")
lines.append("| Label policies | 3 |")
lines.append("| Recipes | 2 |")
lines.append("| Folds | 6 |")
lines.append("| Seeds | 1 (`11`) |")
lines.append("| Total runs | 144 |")
lines.append("\n## Best Policy Summary\n")
lines.append("| Modality | Task | Best policy | Best recipe | Macro F1 | Balanced acc |")
lines.append("|---|---|---|---|---:|---:|")
for c in comparisons:
    lines.append(
        f"| {c['modality']} | {c['task']} | {c['best_policy']} | {c['best_recipe']} | "
        f"{fmt(c['best_macro_f1_mean'])} | {fmt(c['best_balanced_accuracy_mean'])} |"
    )

lines.append("\n## Policy Detail\n")
lines.append("| Modality | Task | Policy | Recipe | Macro F1 | Balanced acc | One-class runs |")
lines.append("|---|---|---|---|---:|---:|---:|")
for c in comparisons:
    for p in c["policies"]:
        lines.append(
            f"| {c['modality']} | {c['task']} | {p['policy']} | {p['recipe']} | "
            f"{fmt(p['final_macro_f1_mean'])} | {fmt(p['final_balanced_accuracy_mean'])} | "
            f"{p['one_class_final_runs']} |"
        )

lines.append("\n## Interpretation\n")
lines.append("- All 144 authorized primary runs completed and produced valid combined outputs.\n")
lines.append("- This report does not lock a final label policy.")
lines.append("- This report does not authorize fusion or final LOSO claims.")
lines.append("- A human review / closeout decision is the next step.\n")
lines.append("## Not Authorized\n")
for item in decision["not_authorized_from_this_report"]:
    lines.append(f"- {item}")
lines.append("\n## Next Allowed Step\n")
lines.append("Human review / closeout decision for the label-policy ablation.\n")
REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

print("OK_COMBINED_LABEL_POLICY_REPORTS_WRITTEN")
for path in [
    MODS["eeg"]["out_md"],
    MODS["eeg"]["out_json"],
    MODS["eeg"]["out_csv"],
    MODS["emg"]["out_md"],
    MODS["emg"]["out_json"],
    MODS["emg"]["out_csv"],
    REPORT_MD,
    REPORT_JSON,
]:
    print(path)
PY

  echo
  echo "===== 8) validate final outputs ====="
  "$PY" - <<'PY'
import csv
import json
from pathlib import Path

files = [
    ("EEG", Path("docs/idare_label_policy_ablation_eeg_primary.json"), 72),
    ("EMG", Path("docs/idare_label_policy_ablation_emg_primary.json"), 72),
]
for name, path, expected in files:
    data = json.loads(path.read_text(encoding="utf-8"))
    runs = data.get("runs", [])
    print(name, "runs=", len(runs), "status=", data.get("status"))
    if len(runs) != expected:
        raise SystemExit(f"ERROR: {name} expected {expected} runs, got {len(runs)}")
    for policy, val in data.get("validation", {}).items():
        if val.get("n_runs") != 24:
            raise SystemExit(f"ERROR: {name} {policy} expected 24 runs")
        if val.get("prediction_rows", 0) <= 0:
            raise SystemExit(f"ERROR: {name} {policy} empty predictions")
    print("  OK")

for path in [
    Path("docs/idare_label_policy_ablation_eeg_primary_predictions.csv"),
    Path("docs/idare_label_policy_ablation_emg_primary_predictions.csv"),
]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = sum(1 for _ in f) - 1
    print(path.name, "rows=", rows)
    if rows <= 0:
        raise SystemExit(f"ERROR: empty combined CSV: {path}")

json.loads(Path("docs/idare_label_policy_ablation_report.json").read_text(encoding="utf-8"))
print("ALL_LABEL_POLICY_OUTPUTS_VALID")
PY

  "$PY" -m json.tool docs/idare_label_policy_ablation_eeg_primary.json >/dev/null
  "$PY" -m json.tool docs/idare_label_policy_ablation_emg_primary.json >/dev/null
  "$PY" -m json.tool docs/idare_label_policy_ablation_report.json >/dev/null

  echo
  echo "===== 9) output files ====="
  ls -lh \
    docs/idare_label_policy_ablation_eeg_primary.md \
    docs/idare_label_policy_ablation_eeg_primary.json \
    docs/idare_label_policy_ablation_eeg_primary_predictions.csv \
    docs/idare_label_policy_ablation_emg_primary.md \
    docs/idare_label_policy_ablation_emg_primary.json \
    docs/idare_label_policy_ablation_emg_primary_predictions.csv \
    docs/idare_label_policy_ablation_report.md \
    docs/idare_label_policy_ablation_report.json

  echo
  echo "===== 10) final status ====="
  git status --short --branch

  echo
  echo "LABEL_POLICY_ABLATION_DONE"
  date -u
} > "$LOG" 2>&1

cat "$LOG"
echo "LOG_SAVED_TO=$LOG"
