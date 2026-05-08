#!/usr/bin/env bash
# Create the I-DARE controlled label-policy ablation objective.
# This does NOT run the 144-run matrix.
# It creates objective docs, updates project_status_current, validates JSON, and commits locally.
# Push is manual.

cd /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE || exit 1

LOG=/tmp/idare_label_policy_ablation_objective.log

{
  echo "===== 0) start status ====="
  git status --short --branch
  echo

  PY=".venv/bin/python"
  if [ ! -x "$PY" ]; then PY="python3"; fi
  echo "PY=$PY"
  echo

  echo "===== 1) create label-policy ablation objective docs ====="
  "$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
OBJ_MD = DOCS / "idare_label_policy_ablation_objective.md"
OBJ_JSON = DOCS / "idare_label_policy_ablation_objective.json"
PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

NOW = datetime.now(timezone.utc).isoformat()

objective = {
    "status": "short_term_execution_objective",
    "authorized_execution": True,
    "authorized_scope": "I-DARE controlled label-policy ablation primary matrix only",
    "evidence_level": "controlled ablation objective; not final LOSO",
    "objective": "Evaluate whether label-policy choice is limiting I-DARE EEG/EMG single-modality results.",
    "scientific_questions": [
        "Does discarding midpoint score-5 labels improve EEG and/or EMG cross-subject validation stability?",
        "Does assigning midpoint labels to low or high materially change macro-F1 and balanced accuracy?",
        "Is midpoint_as_high still acceptable as a controlled comparison policy, or should later evaluations use a different label policy?"
    ],
    "context": {
        "reason": "Broader EEG/EMG single-modality and BSL-stats evaluations did not produce a clear improvement; label definition is the next controlled target before model complexity.",
        "current_mainlines": {
            "eeg": "baseline-corrected STIM-BSL-only",
            "emg": "feature-only EMG"
        }
    },
    "modalities": {
        "EEG-LP": "baseline-corrected STIM-BSL-only EEG response cache",
        "EMG-LP": "feature-only EMG cache"
    },
    "tasks": [
        "valence",
        "arousal"
    ],
    "label_policies": [
        "discard_midpoint",
        "midpoint_as_low",
        "midpoint_as_high"
    ],
    "recipes": [
        "ce_class_weighted",
        "balanced_sampler_ce"
    ],
    "folds": 6,
    "seeds": [
        11
    ],
    "total_primary_runs": 144,
    "run_matrix_formula": "2 modalities * 2 tasks * 3 label policies * 2 recipes * 6 folds * 1 seed = 144 runs",
    "hyperparameters": {
        "eeg": {
            "epochs": 12,
            "lr": 0.001,
            "batch_size": 64,
            "weight_decay": 0.001,
            "grad_clip": 1.0
        },
        "emg": {
            "epochs": 20,
            "lr": 0.001,
            "batch_size": 128,
            "hidden_dim": 64,
            "weight_decay": 0.001,
            "grad_clip": 1.0
        }
    },
    "required_outputs": [
        "EEG label-policy markdown report",
        "EEG label-policy JSON report",
        "EEG label-policy predictions CSV",
        "EMG label-policy markdown report",
        "EMG label-policy JSON report",
        "EMG label-policy predictions CSV",
        "combined label-policy comparison report markdown",
        "combined label-policy comparison report JSON",
        "central roadmap update",
        "human-review closeout decision"
    ],
    "pass_criteria": [
        "all 144 primary runs finish",
        "all JSON reports validate",
        "prediction CSVs exist and are non-empty",
        "fold/seed/task/recipe/policy alignment is documented",
        "no one-class collapse is hidden in aggregates",
        "results are interpreted as controlled ablation evidence, not final LOSO"
    ],
    "failure_handling": {
        "engineering_fail": "Fix script/output and rerun the same objective.",
        "data_or_protocol_fail": "Stop and audit; do not interpret results.",
        "scientific_weak_result": "Document weak result without changing mainline.",
        "inconclusive": "Do not lock label policy.",
        "repeated_scientific_failure": "Stop blind tuning and review dataset/label strategy."
    },
    "not_authorized": [
        "EEG+EMG fusion",
        "full model(BSL, STIM, STIM-BSL)",
        "final LOSO / final paper claim",
        "locking a final label policy before review",
        "raw EMG mainline",
        "architecture ablations",
        "data augmentation",
        "SupCon / VREx / domain generalization",
        "optional extra seeds without explicit objective"
    ],
    "next_step": "Prepare execution commands or limited script patches for the 144-run primary matrix; review before running."
}

OBJ_JSON.write_text(json.dumps(objective, indent=2, sort_keys=True) + "\n", encoding="utf-8")

md = """# I-DARE Controlled Label-Policy Ablation Objective

## Status

Short-term execution objective.

This document authorizes the controlled I-DARE label-policy ablation primary matrix only.

It does not authorize fusion, full paired BSL/STIM modeling, final LOSO claims, or locking a final label policy before review.

## Why this objective exists

The broader standardized single-modality evaluation did not produce a clear EEG or EMG improvement.

Therefore, before adding model complexity, the next controlled question is whether the current label definition is limiting the task.

Current practical mainlines:

- EEG: baseline-corrected `STIM-BSL`-only.
- EMG: feature-only EMG.

BSL-stats sidecars remain controlled ablations and are not part of this label-policy objective.

## Scientific question

Does label-policy choice materially change I-DARE EEG/EMG cross-subject performance?

Specifically:

1. Does `discard_midpoint` reduce label noise and improve stability?
2. Does `midpoint_as_low` outperform `midpoint_as_high`?
3. Is `midpoint_as_high` acceptable for later controlled evaluations, or should it be replaced?

## Authorized scope

Authorized:

- I-DARE EEG mainline: baseline-corrected `STIM-BSL`-only.
- I-DARE EMG mainline: feature-only EMG.
- Tasks: `valence`, `arousal`.
- Label policies:
  - `discard_midpoint`
  - `midpoint_as_low`
  - `midpoint_as_high`
- Recipes:
  - `ce_class_weighted`
  - `balanced_sampler_ce`
- All 6 subject-held-out folds.
- Seed: `11`.

Not authorized:

- EEG+EMG fusion.
- Full `model(BSL, STIM, STIM-BSL)`.
- Final LOSO / final paper claim.
- Locking a final label policy before review.
- Raw EMG mainline.
- Architecture ablations.
- Data augmentation.
- SupCon / VREx / domain generalization.
- Optional extra seeds without explicit objective.

## Primary run matrix

Use:

- modalities: 2
- tasks: 2
- label policies: 3
- recipes: 2
- folds: 6
- seeds: 1

Total:

```text
2 * 2 * 3 * 2 * 6 * 1 = 144 runs
```

## Conditions

| ID | Modality | Input |
|---|---|---|
| EEG-LP | EEG | baseline-corrected `STIM-BSL` response cache |
| EMG-LP | EMG | feature-only EMG cache |

## Label policies

| Policy | Meaning |
|---|---|
| `discard_midpoint` | score 5 is discarded |
| `midpoint_as_low` | score 5 is assigned to low |
| `midpoint_as_high` | score 5 is assigned to high |

## Hyperparameters

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
- weight decay: `1e-3`
- grad clip: `1.0`

## Required outputs

If executed, produce:

- `docs/idare_label_policy_ablation_eeg_primary.md`
- `docs/idare_label_policy_ablation_eeg_primary.json`
- `docs/idare_label_policy_ablation_eeg_primary_predictions.csv`
- `docs/idare_label_policy_ablation_emg_primary.md`
- `docs/idare_label_policy_ablation_emg_primary.json`
- `docs/idare_label_policy_ablation_emg_primary_predictions.csv`
- `docs/idare_label_policy_ablation_report.md`
- `docs/idare_label_policy_ablation_report.json`

Also update the central roadmap and create a human-review closeout after the report is reviewed.

## Metrics

Report at minimum:

- final macro F1
- final balanced accuracy
- final accuracy
- majority baseline
- one-class final runs
- threshold-best macro F1
- threshold-best balanced accuracy where available
- per-fold results
- per-recipe results
- per-policy results

## Pass criteria

The objective can be interpreted if:

- all 144 primary runs finish
- all JSON reports validate
- prediction CSVs exist and are non-empty
- fold/seed/task/recipe/policy alignment is documented
- no hidden one-class collapse exists
- results are interpreted as controlled label-policy evidence, not final LOSO

## Failure handling

| Failure | Meaning | Action |
|---|---|---|
| engineering fail | script crash, missing output, bad JSON | fix script/output and rerun same objective |
| data/protocol fail | fold mismatch, policy mismatch, cache mismatch | stop and audit |
| scientific weak result | all policies weak but protocol valid | document result |
| inconclusive | no stable winner | do not lock final label policy |
| repeated scientific failure | repeated collapse or unstable behavior | stop blind tuning and review label strategy |

## Closeout decision

At closeout, decide one of:

1. keep `midpoint_as_high` as a temporary comparison policy only
2. select a better candidate policy for later evaluation
3. declare label policy inconclusive and avoid final label lock
4. create a separate final label-policy objective if stronger evidence is needed

Do not jump directly to fusion.

## Next step after this objective

Prepare execution commands or limited script patches needed to run the 144-run primary matrix.

Do not execute until commands/scripts are reviewed.
"""
OBJ_MD.write_text(md, encoding="utf-8")

# Update central roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
row = "| I-DARE controlled label-policy ablation objective | short-term execution objective created for 144-run label-policy matrix | yes | `docs/idare_label_policy_ablation_objective.md` | Prepare execution commands or limited script patches; review before running. | EEG+EMG fusion; final LOSO claim; locking final label policy before review. |"
if "I-DARE controlled label-policy ablation objective" not in project_md:
    anchor = "| Label-policy ablation | planned / not final | no | `README.md`<br>`training smoke JSON reports` | Run controlled comparison of discard_midpoint, midpoint_as_low, and midpoint_as_high using fixed splits/seeds. | Locking midpoint_as_high as the final paper policy. |"
    project_md = project_md.replace(anchor, row + "\n" + anchor)

note = "- A controlled I-DARE label-policy ablation objective is defined in `docs/idare_label_policy_ablation_objective.md`; only the 144-run EEG/EMG mainline label-policy matrix is authorized."
if note not in project_md:
    project_md = project_md.replace(
        "- Do not claim final performance from the smoke reports.",
        "- Do not claim final performance from the smoke reports.\n" + note,
    )

PROJECT_MD.write_text(project_md, encoding="utf-8")

project = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
project.setdefault("sources", {})["idare_label_policy_ablation_objective"] = str(OBJ_MD)
project.setdefault("decisions", {})["idare_label_policy_ablation_objective"] = {
    "status": "short_term_execution_objective",
    "authorized_execution": True,
    "authorized_scope": "144-run I-DARE EEG/EMG mainline label-policy primary matrix only",
    "evidence": str(OBJ_MD),
    "modalities": ["EEG STIM-BSL-only", "EMG feature-only"],
    "tasks": ["valence", "arousal"],
    "label_policies": ["discard_midpoint", "midpoint_as_low", "midpoint_as_high"],
    "recipes": ["ce_class_weighted", "balanced_sampler_ce"],
    "folds": 6,
    "seeds": [11],
    "total_primary_runs": 144,
    "next_allowed_step": "Prepare execution commands or limited script patches; review before running.",
    "not_authorized": objective["not_authorized"]
}
project["last_updated_for_idare_label_policy_ablation_objective_utc"] = NOW
PROJECT_JSON.write_text(json.dumps(project, indent=2, sort_keys=True) + "\n", encoding="utf-8")

print("OK_OBJECTIVE_WRITTEN")
print(str(OBJ_MD))
print(str(OBJ_JSON))
PY
  echo

  echo "===== 2) validate objective docs ====="
  "$PY" -m json.tool docs/idare_label_policy_ablation_objective.json >/dev/null
  "$PY" -m json.tool docs/project_status_current.json >/dev/null
  echo "OK_JSON"

  grep -n "Status\|Scientific question\|Primary run matrix\|Pass criteria\|Next step" docs/idare_label_policy_ablation_objective.md
  grep -n "controlled label-policy ablation objective\|144-run EEG/EMG" docs/project_status_current.md
  echo

  echo "===== 3) status before commit ====="
  git status --short --branch
  echo

  echo "===== 4) commit objective ====="
  git add \
    docs/idare_label_policy_ablation_objective.md \
    docs/idare_label_policy_ablation_objective.json \
    docs/project_status_current.md \
    docs/project_status_current.json

  git commit -m "docs: add I-DARE label-policy ablation objective"
  echo "COMMIT_EXIT=$?"
  echo

  echo "===== 5) final status ====="
  git status --short --branch
} > "$LOG" 2>&1

cat "$LOG"
echo "LOG_SAVED_TO=$LOG"
