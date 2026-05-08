#!/usr/bin/env bash
# Create a short-term objective for executing the broader standardized
# I-DARE single-modality evaluation. This does NOT run the evaluation.
# It creates docs and commits them locally. Push is manual.

cd /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE || exit 1

{
  echo "===== 0) start status ====="
  git status --short --branch
  echo

  echo "===== 1) create execution objective docs ====="

  cat > docs/idare_broader_standardized_single_modality_evaluation_objective.md <<'MD'
# I-DARE Broader Standardized Single-Modality Evaluation Objective

## Status

Short-term execution objective.

This document authorizes execution of the **primary run matrix only** from:

- `docs/idare_broader_standardized_single_modality_evaluation_execution_spec.md`

It does not authorize optional robustness runs, fusion, full paired BSL/STIM modeling, final LOSO claims, or label-policy finalization.

## Why this objective exists

The project has already completed:

- standardized EEG `STIM-BSL`-only baseline smoke
- EEG/EMG BSL-stats vs baseline comparison
- human review of that comparison
- broader single-modality evaluation plan
- broader single-modality execution spec

The current smoke-level conclusion is:

- EEG mainline remains baseline-corrected `STIM-BSL`-only.
- EMG mainline remains feature-level EMG.
- BSL-stats sidecars remain controlled ablations.
- Fusion is not started.

This objective allows the next controlled step: run a broader standardized single-modality evaluation to test whether those smoke-level conclusions are stable.

## Scientific question

Do the current I-DARE single-modality conclusions remain stable under the broader standardized primary run matrix?

Specifically:

1. Does EEG `STIM-BSL`-only remain stronger than EEG `STIM-BSL + BSL-stats`?
2. Does EMG feature-level remain the practical EMG mainline?
3. Are the small EMG BSL-stats gains stable or smoke-level noise?

## Authorized scope

Authorized:

- I-DARE EEG `STIM-BSL`-only.
- I-DARE EEG `STIM-BSL + BSL-stats`.
- I-DARE EMG feature-only.
- I-DARE EMG feature + BSL-stats.
- `valence` and `arousal`.
- `midpoint_as_high` as the controlled comparison label policy.
- Primary matrix only: 96 runs.

Not authorized:

- optional robustness seed `13`
- EEG+EMG fusion
- full `model(BSL, STIM, STIM-BSL)`
- final LOSO / final paper claim
- locking `midpoint_as_high`
- raw EMG mainline
- architecture ablations
- data augmentation
- SupCon / VREx / domain generalization

## Primary run matrix

Use:

- conditions: 4
- tasks: 2
- recipes: 2
- folds: 6
- seeds: 1

Total:

```text
4 * 2 * 2 * 6 * 1 = 96 runs
```

Conditions:

| ID | Condition |
|---|---|
| EEG-B0 | baseline-corrected `STIM-BSL` EEG response cache only |
| EEG-B1 | baseline-corrected `STIM-BSL` EEG response cache + EEG BSL-stats sidecar |
| EMG-B0 | feature-level EMG cache only |
| EMG-B1 | feature-level EMG cache + EMG BSL-stats sidecar |

Tasks:

- `valence`
- `arousal`

Recipes:

- `ce_class_weighted`
- `balanced_sampler_ce`

Seed:

- `11`

Folds:

- all 6 subject-held-out folds

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
- zclip: `8.0`

## Required outputs

At minimum, execution should produce:

- per-condition markdown reports
- per-condition JSON reports
- prediction CSV files
- combined comparison report:
  - `docs/idare_broader_standardized_single_modality_evaluation_report.md`
  - `docs/idare_broader_standardized_single_modality_evaluation_report.json`
- central roadmap update
- clear pass/fail/freeze decision

## Metrics

Report:

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

## Execution gates

Before running:

- repo must be clean
- required caches must exist locally
- scripts must be checked for whether they can generate the required output schema
- fold/task/seed/recipe alignment must be confirmed
- no sidecar leakage should be possible

During running:

- log terminal output
- stop on data/protocol failure
- do not silently change hyperparameters
- do not add optional robustness seed
- do not start fusion

After running:

- inspect all reports
- verify JSON validity
- verify prediction CSV existence
- summarize pass/fail
- update central roadmap
- commit outputs only after review

## Pass criteria

The objective can be closed if:

- all 96 primary runs finish
- all required reports are created
- all JSON reports validate
- prediction CSVs exist
- no cache/index mismatch occurs
- no sidecar leakage occurs
- no hidden one-class collapse exists
- fold/seed/task/recipe alignment is documented
- results are interpreted as smoke-to-broader-evaluation evidence, not final LOSO

## Failure handling

| Failure | Meaning | Action |
|---|---|---|
| engineering fail | script crash, missing output, bad JSON | fix script/output and rerun same objective |
| data/protocol fail | fold mismatch, cache mismatch, sidecar leakage | stop and audit |
| scientific weak result | model weak but protocol valid | document result |
| inconclusive | outputs incomplete or unstable | do not promote any mainline |
| repeated scientific failure | repeated collapse or unstable behavior | stop blind tuning and review method |

## Closeout decision

At closeout, decide one of:

1. keep current mainlines unchanged
2. promote no sidecar but document broader evidence
3. identify a controlled follow-up objective
4. stop and hand off

Do not jump directly to fusion.

## Next step after this objective

Prepare execution commands or limited script patches needed to run the 96-run primary matrix.

Do not execute until commands/scripts are reviewed.
MD

  cat > docs/idare_broader_standardized_single_modality_evaluation_objective.json <<'JSON'
{
  "status": "short_term_execution_objective",
  "authorized_execution": true,
  "authorized_scope": "primary run matrix only",
  "source_spec": "docs/idare_broader_standardized_single_modality_evaluation_execution_spec.md",
  "objective": "Execute the broader standardized I-DARE single-modality primary run matrix.",
  "scientific_questions": [
    "Does EEG STIM-BSL-only remain stronger than EEG STIM-BSL plus BSL-stats?",
    "Does EMG feature-level remain the practical EMG mainline?",
    "Are small EMG BSL-stats gains stable or smoke-level noise?"
  ],
  "conditions": {
    "EEG-B0": "baseline-corrected STIM-BSL EEG response cache only",
    "EEG-B1": "baseline-corrected STIM-BSL EEG response cache plus EEG BSL-stats sidecar",
    "EMG-B0": "feature-level EMG cache only",
    "EMG-B1": "feature-level EMG cache plus EMG BSL-stats sidecar"
  },
  "tasks": [
    "valence",
    "arousal"
  ],
  "recipes": [
    "ce_class_weighted",
    "balanced_sampler_ce"
  ],
  "folds": 6,
  "seeds": [
    11
  ],
  "total_primary_runs": 96,
  "label_policy": {
    "controlled_policy": "midpoint_as_high",
    "final_locked": false
  },
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
      "zclip": 8.0
    }
  },
  "required_outputs": [
    "per-condition markdown reports",
    "per-condition JSON reports",
    "prediction CSV files",
    "combined comparison report",
    "central roadmap update",
    "clear pass/fail/freeze decision"
  ],
  "not_authorized": [
    "optional robustness seed 13",
    "EEG+EMG fusion",
    "full model(BSL, STIM, STIM-BSL)",
    "final LOSO / final paper claim",
    "locking midpoint_as_high",
    "raw EMG mainline",
    "architecture ablations",
    "data augmentation",
    "SupCon / VREx / domain generalization"
  ],
  "next_step": "Prepare execution commands or limited script patches needed to run the 96-run primary matrix; do not execute until reviewed."
}
JSON

  echo "===== 2) update central roadmap ====="
  PY=".venv/bin/python"
  if [ ! -x "$PY" ]; then PY="python3"; fi

  "$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

md_path = Path("docs/project_status_current.md")
json_path = Path("docs/project_status_current.json")

objective_md = "docs/idare_broader_standardized_single_modality_evaluation_objective.md"

md = md_path.read_text(encoding="utf-8")

row = "| I-DARE broader standardized single-modality evaluation objective | short-term execution objective created for 96-run primary matrix | yes | `docs/idare_broader_standardized_single_modality_evaluation_objective.md` | Prepare execution commands or limited script patches; review before running. | EEG+EMG fusion; full paired BSL/STIM neural model; final LOSO claim. |"

if "I-DARE broader standardized single-modality evaluation objective" not in md:
    anchor = "| EEG+EMG fusion | not started intentionally | no | `docs/idare_eeg_bsl_stats_ablation_status.md`<br>`docs/idare_emg_bsl_stats_ablation_status.md` | Start only after current baseline/ablation status is indexed and compared cleanly. | All fusion experiments. |"
    md = md.replace(anchor, row + "\n" + anchor)

note = "- Broader standardized single-modality evaluation now has an execution objective in `docs/idare_broader_standardized_single_modality_evaluation_objective.md`; only the 96-run primary matrix is in scope, and commands/scripts must be reviewed before running."
if note not in md:
    md = md.replace(
        "- Do not claim final performance from the smoke reports.",
        "- Do not claim final performance from the smoke reports.\n" + note,
    )

md_path.write_text(md, encoding="utf-8")

data = json.loads(json_path.read_text(encoding="utf-8"))
data.setdefault("sources", {})["idare_broader_standardized_single_modality_evaluation_objective"] = objective_md
data.setdefault("decisions", {})["idare_broader_standardized_single_modality_evaluation_objective"] = {
    "status": "short_term_execution_objective",
    "authorized_execution": True,
    "authorized_scope": "primary run matrix only",
    "evidence": objective_md,
    "total_primary_runs": 96,
    "next_allowed_step": "Prepare execution commands or limited script patches; review before running.",
    "not_allowed_yet": [
        "optional robustness seed 13",
        "EEG+EMG fusion",
        "full model(BSL, STIM, STIM-BSL)",
        "final LOSO / final paper claim",
        "locking midpoint_as_high",
        "raw EMG mainline",
        "architecture ablations",
        "data augmentation",
        "SupCon / VREx / domain generalization"
    ]
}
data["last_updated_for_broader_standardized_single_modality_objective_utc"] = datetime.now(timezone.utc).isoformat()

json_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("OK roadmap updated")
PY

  echo "===== 3) validate ====="
  "$PY" -m json.tool docs/idare_broader_standardized_single_modality_evaluation_objective.json >/dev/null
  "$PY" -m json.tool docs/project_status_current.json >/dev/null
  echo "OK JSON"

  grep -n "Status\|Authorized scope\|Primary run matrix\|Pass criteria\|Next step" docs/idare_broader_standardized_single_modality_evaluation_objective.md || true
  grep -n "broader standardized single-modality evaluation objective\|96-run primary matrix" docs/project_status_current.md || true
  echo

  echo "===== 4) status before commit ====="
  git status --short --branch
  echo

  echo "===== 5) commit ====="
  git add \
    docs/idare_broader_standardized_single_modality_evaluation_objective.md \
    docs/idare_broader_standardized_single_modality_evaluation_objective.json \
    docs/project_status_current.md \
    docs/project_status_current.json

  git commit -m "docs: add objective for broader I-DARE evaluation"
  echo "commit_exit=$?"
  echo

  echo "===== 6) final status ====="
  git status --short --branch
} > /tmp/idare_broader_eval_objective.log 2>&1

cat /tmp/idare_broader_eval_objective.log
echo "LOG_SAVED_TO=/tmp/idare_broader_eval_objective.log"
