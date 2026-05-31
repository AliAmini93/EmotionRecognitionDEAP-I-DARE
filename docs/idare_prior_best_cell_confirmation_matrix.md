# I-DARE Prior Best Cell Confirmation Matrix

## Status

`created`

## Matrix

| Cell | Dataset | Modality | Task | Policy | Recipe | Prior BA | Future status |
|---|---|---|---|---|---|---:|---|
| C0 | I-DARE | EEG | arousal | midpoint_as_high | ce_class_weighted | 0.5416327026 | confirmation candidate |
| C1 | I-DARE | EEG | valence | discard_midpoint | balanced_sampler_ce | 0.5218687144 | confirmation candidate |
| C2 | I-DARE | EMG | arousal | discard_midpoint | ce_class_weighted | 0.5364967332 | confirmation candidate |
| C3 | I-DARE | EMG | valence | midpoint_as_high | ce_class_weighted | 0.5201507594 | confirmation candidate |

## Run Count If Later Approved

`4 cells x 6 folds = 24 runs`

## Explicit Non-Goals

- do not rerun the full 144-run label-policy matrix
- do not run DEAP
- do not run fusion
- do not run DG
- do not run model-capacity probe
- do not run augmentation
- do not change thresholds
- do not claim final paper-level performance

## Current Decision

`CONFIRMATION_PACKAGE_CREATED_EXECUTION_BLOCKED`
