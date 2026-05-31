# I-DARE Prior Best Cell Confirmation Objective

## Status

Created for Control Tower validation only.

No confirmation execution is authorized in this objective.

## Authorized Scope

- Create objective document.
- Create guarded runner.
- Create validation artifacts.
- Validate branch/worktree/scope.
- Validate prior label-policy artifacts.
- Validate required I-DARE EEG/EMG cache/index inputs.
- Validate the exact four registered prior-best cells.
- Validate the planned matrix only as metadata: 4 cells x 6 folds = 24 planned confirmation runs.

## Registered Cells

| Cell | Dataset | Modality | Task | Label policy | Recipe |
|---|---|---|---|---|---|
| C0 | I-DARE | EEG | arousal | midpoint_as_high | ce_class_weighted |
| C1 | I-DARE | EEG | valence | discard_midpoint | balanced_sampler_ce |
| C2 | I-DARE | EMG | arousal | discard_midpoint | ce_class_weighted |
| C3 | I-DARE | EMG | valence | midpoint_as_high | ce_class_weighted |

## Planned Matrix Metadata

- Cells: 4
- Folds per cell: 6
- Planned confirmation runs: 24
- Metadata only: yes

## Required Inputs

### EEG

- `.cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy`
- `.cache/idare_eeg_cache_index_baseline_corrected.csv`

### EMG

- `.cache/idare_emg_features.npy`
- `.cache/idare_emg_feature_cache_index.csv`

## Forbidden

- No 24-run confirmation execution.
- No full 144-run label-policy rerun.
- No experiments.
- No model results.
- No Wave 2.
- No DG.
- No model-capacity probe.
- No augmentation.
- No representation redesign v2.
- No DEAP.
- No fusion.
- No preprocessing changes.
- No threshold changes.
- No main push.
- No final paper-level performance claim.

## Next Gate

Run `scripts/idare_prior_best_confirm_runner.py` in default validate mode and report validation output to Control Tower.
