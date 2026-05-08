#!/usr/bin/env bash
# Refine the I-DARE broader standardized single-modality evaluation plan.
# Creates a planning-only execution spec, updates central roadmap docs,
# validates JSON, commits locally, and does NOT push.

set -u

REPO_DIR="${1:-/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE}"
LOG_FILE="/tmp/idare_refined_single_modality_spec.log"

cd "$REPO_DIR" || {
  echo "ERROR: repo path not found: $REPO_DIR"
  exit 1
}

{
  echo "===== 0) start status ====="
  git status --short --branch
  echo

  echo "===== 1) create refined execution spec ====="
  PY=".venv/bin/python"
  if [ ! -x "$PY" ]; then
    PY="python3"
  fi
  echo "PY=$PY"

  "$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
DOCS.mkdir(exist_ok=True)

SPEC_MD = DOCS / "idare_broader_standardized_single_modality_evaluation_execution_spec.md"
SPEC_JSON = DOCS / "idare_broader_standardized_single_modality_evaluation_execution_spec.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

spec_md = """# I-DARE Broader Standardized Single-Modality Evaluation Execution Spec

## Status

Planning only.

This document does not authorize execution.

## Purpose

This spec refines the broader standardized single-modality evaluation plan.

It says exactly what should be run later if a new short-term objective explicitly authorizes execution.

## Evaluation scope

Include only I-DARE single-modality models.

Include:

- EEG `STIM-BSL`-only.
- EEG `STIM-BSL + BSL-stats`.
- EMG feature-only.
- EMG feature + BSL-stats.

Do not include:

- EEG+EMG fusion.
- Full `model(BSL, STIM, STIM-BSL)`.
- Raw EMG mainline.
- Architecture ablations.
- Data augmentation.
- SupCon / VREx / domain generalization.

## Tasks

Run both:

- `valence`
- `arousal`

## Label policy

Use:

- `midpoint_as_high`

But do not lock it as final.

A separate label-policy ablation is still needed before final claims.

## Conditions

| ID | Modality | Input | Sidecar? | Purpose |
|---|---|---|---|---|
| EEG-B0 | EEG | baseline-corrected `STIM-BSL` response cache | no | EEG baseline |
| EEG-B1 | EEG | baseline-corrected `STIM-BSL` response cache | yes, EEG BSL-stats | EEG BSL-stats ablation |
| EMG-B0 | EMG | feature-level EMG cache | no | EMG baseline |
| EMG-B1 | EMG | feature-level EMG cache | yes, EMG BSL-stats | EMG BSL-stats ablation |

## Primary run matrix

Primary evaluation should use:

- folds: all 6 subject-held-out folds
- seed: `11`
- recipes:
  - `ce_class_weighted`
  - `balanced_sampler_ce`
- tasks:
  - `valence`
  - `arousal`

This gives:

- 4 conditions
- 2 tasks
- 2 recipes
- 6 folds
- 1 seed

Total primary runs:

```text
4 * 2 * 2 * 6 * 1 = 96 runs
```

## Optional robustness pass

Only if the primary run is clean:

- add seed `13`
- keep the same folds, tasks, recipes, and conditions

This adds another 96 runs.

Do not run optional robustness automatically.

## Hyperparameters

Use the current stable smoke settings unless an explicit objective changes them.

### EEG

- epochs: `12`
- learning rate: `1e-3`
- batch size: `64`
- weight decay: `1e-3`
- grad clip: `1.0`

### EMG

- epochs: `20`
- learning rate: `1e-3`
- batch size: `128`
- hidden dim: `64`
- zclip: `8.0`

## Required outputs if executed later

For each condition and task:

- markdown report
- JSON report
- predictions CSV

Also create one combined comparison report:

- `docs/idare_broader_standardized_single_modality_evaluation_report.md`
- `docs/idare_broader_standardized_single_modality_evaluation_report.json`

## Metrics

Report at minimum:

- final macro F1
- final balanced accuracy
- final accuracy
- majority baseline
- one-class final runs
- threshold-best macro F1
- threshold-best balanced accuracy
- threshold one-class runs
- per-fold results
- per-recipe results

## Pass criteria

The evaluation can be interpreted if:

- all planned primary runs finish
- all reports are created
- no cache/index mismatch occurs
- no sidecar leakage occurs
- no hidden one-class collapse exists
- fold/seed/task/recipe alignment is documented
- prediction CSVs are available

## Fail handling

| Failure | Meaning | Action |
|---|---|---|
| engineering fail | script crashes, output missing, bad JSON | fix script/output and rerun same objective |
| data/protocol fail | folds mismatch, cache mismatch, sidecar leakage | stop and audit |
| scientific weak result | model is weak but protocol is valid | document result |
| inconclusive | outputs incomplete or unstable | do not promote any mainline |
| repeated scientific failure | repeated collapse or unstable behavior | stop blind tuning and review method |

## What this still does not prove

Even if executed, this is not automatically final paper evidence.

Final LOSO or final claims require a separate final-evaluation objective.

## Next allowed step

After this spec:

1. Stop here.
2. Review/refine this spec.
3. Create a new short-term objective to execute the primary run matrix.

Do not execute the matrix automatically.
"""

spec_json = {
    "status": "planning_only",
    "authorized_execution": False,
    "purpose": "Refine the broader I-DARE standardized single-modality evaluation plan into a concrete run matrix.",
    "scope": {
        "include": [
            "EEG STIM-BSL-only",
            "EEG STIM-BSL plus BSL-stats",
            "EMG feature-only",
            "EMG feature plus BSL-stats",
        ],
        "exclude": [
            "EEG+EMG fusion",
            "full model(BSL, STIM, STIM-BSL)",
            "raw EMG mainline",
            "architecture ablations",
            "data augmentation",
            "SupCon / VREx / domain generalization",
        ],
    },
    "tasks": ["valence", "arousal"],
    "label_policy": {
        "use_for_controlled_eval": "midpoint_as_high",
        "final_locked": False,
    },
    "conditions": {
        "EEG-B0": "baseline-corrected STIM-BSL EEG response cache only",
        "EEG-B1": "baseline-corrected STIM-BSL EEG response cache plus EEG BSL-stats sidecar",
        "EMG-B0": "feature-level EMG cache only",
        "EMG-B1": "feature-level EMG cache plus EMG BSL-stats sidecar",
    },
    "primary_run_matrix": {
        "conditions": 4,
        "tasks": 2,
        "recipes": ["ce_class_weighted", "balanced_sampler_ce"],
        "folds": 6,
        "seeds": [11],
        "total_runs": 96,
    },
    "optional_robustness_pass": {
        "run_automatically": False,
        "additional_seed": 13,
        "additional_runs": 96,
    },
    "hyperparameters": {
        "eeg": {
            "epochs": 12,
            "lr": 0.001,
            "batch_size": 64,
            "weight_decay": 0.001,
            "grad_clip": 1.0,
        },
        "emg": {
            "epochs": 20,
            "lr": 0.001,
            "batch_size": 128,
            "hidden_dim": 64,
            "zclip": 8.0,
        },
    },
    "required_outputs_if_executed": [
        "markdown reports",
        "JSON reports",
        "prediction CSV files",
        "combined comparison report",
        "central roadmap update",
    ],
    "pass_criteria": [
        "all primary runs finish",
        "all reports are created",
        "no cache/index mismatch",
        "no sidecar leakage",
        "no hidden one-class collapse",
        "fold/seed/task/recipe alignment documented",
        "prediction CSVs available",
    ],
    "next_allowed_step": "Stop, refine this spec, or create a new explicit short-term objective to execute the primary run matrix.",
}

SPEC_MD.write_text(spec_md, encoding="utf-8")
SPEC_JSON.write_text(json.dumps(spec_json, indent=2, sort_keys=True) + "\n", encoding="utf-8")

md = PROJECT_MD.read_text(encoding="utf-8")
row = "| I-DARE broader standardized single-modality evaluation execution spec | run matrix specified; planning only; no experiment authorized | yes | `docs/idare_broader_standardized_single_modality_evaluation_execution_spec.md` | Review spec before creating an execution objective. | EEG+EMG fusion; full paired BSL/STIM neural model; final LOSO claim. |"

if "I-DARE broader standardized single-modality evaluation execution spec" not in md:
    anchor = "| EEG+EMG fusion | not started intentionally | no | `docs/idare_eeg_bsl_stats_ablation_status.md`<br>`docs/idare_emg_bsl_stats_ablation_status.md` | Start only after current baseline/ablation status is indexed and compared cleanly. | All fusion experiments. |"
    md = md.replace(anchor, row + "\n" + anchor)

note = "- Broader standardized single-modality evaluation now has a planning-only execution spec in `docs/idare_broader_standardized_single_modality_evaluation_execution_spec.md`; no run matrix is authorized yet."
if note not in md:
    md = md.replace(
        "- Do not claim final performance from the smoke reports.",
        "- Do not claim final performance from the smoke reports.\n" + note,
    )

PROJECT_MD.write_text(md, encoding="utf-8")

data = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
data.setdefault("sources", {})["idare_broader_standardized_single_modality_evaluation_execution_spec"] = str(SPEC_MD)
data.setdefault("decisions", {})["idare_broader_standardized_single_modality_evaluation_execution_spec"] = {
    "status": "planning_only",
    "authorized_execution": False,
    "evidence": str(SPEC_MD),
    "primary_run_matrix": {
        "conditions": 4,
        "tasks": 2,
        "recipes": 2,
        "folds": 6,
        "seeds": 1,
        "total_runs": 96,
    },
    "next_allowed_step": "Review spec before creating an execution objective.",
    "not_allowed_yet": [
        "EEG+EMG fusion",
        "full model(BSL, STIM, STIM-BSL)",
        "final LOSO / final performance claim",
        "locking midpoint_as_high",
        "raw EMG mainline",
        "architecture ablations",
        "data augmentation",
        "SupCon / VREx / domain generalization",
    ],
}
data["last_updated_for_broader_standardized_single_modality_execution_spec_utc"] = datetime.now(timezone.utc).isoformat()
PROJECT_JSON.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

print("OK files written")
PY

  PY_EXIT=$?
  echo "python_exit=$PY_EXIT"
  echo

  echo "===== 2) validate ====="
  if [ "$PY_EXIT" -eq 0 ]; then
    "$PY" -m json.tool docs/idare_broader_standardized_single_modality_evaluation_execution_spec.json >/dev/null
    "$PY" -m json.tool docs/project_status_current.json >/dev/null
    echo "OK JSON"

    grep -n "Status\|Primary run matrix\|Optional robustness pass\|Pass criteria\|Next allowed step" docs/idare_broader_standardized_single_modality_evaluation_execution_spec.md
    grep -n "execution spec\|no run matrix is authorized" docs/project_status_current.md
  fi
  echo

  echo "===== 3) status before commit ====="
  git status --short --branch
  echo

  if [ "$PY_EXIT" -eq 0 ]; then
    echo "===== 4) commit ====="
    git add \
      docs/idare_broader_standardized_single_modality_evaluation_execution_spec.md \
      docs/idare_broader_standardized_single_modality_evaluation_execution_spec.json \
      docs/project_status_current.md \
      docs/project_status_current.json

    git commit -m "docs: refine I-DARE single-modality evaluation spec"
    echo "commit_exit=$?"
  else
    echo "SKIP_COMMIT because generation failed"
  fi
  echo

  echo "===== 5) final status ====="
  git status --short --branch
} > "$LOG_FILE" 2>&1

cat "$LOG_FILE"
echo "LOG_SAVED_TO=$LOG_FILE"
