# I-DARE Broader Standardized Single-Modality Evaluation Execution Spec

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
