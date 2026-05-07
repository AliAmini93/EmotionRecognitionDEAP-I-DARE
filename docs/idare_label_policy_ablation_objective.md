# I-DARE Controlled Label-Policy Ablation Objective

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
