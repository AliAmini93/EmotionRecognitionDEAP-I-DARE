# Strict NTD Normalization Smoke Execution Authorization Package

## Status

`created`

## Execution Authorization

`NOT_AUTHORIZED`

Execution requires explicit human approval phrase:

`APPROVE_STRICT_NTD_NORM_SMOKE_EXECUTION`

## Future Executable Branch

`idare/postwave1/strict-ntd-norm-smoke`

## Future Worktree

`/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-strict-ntd-smoke`

## Exact Executable Scope

- I-DARE only
- EEG-only
- arousal-only
- pairwise formulation
- ridge fixed
- strict non-transductive normalization only

## Future Cells

| Cell | Definition |
|---|---|
| S0 | current / no normalization |
| S1 | train-fold StandardScaler |
| S2 | train-fold RobustScaler |
| S3 | train-fold frozen quantile/rank mapper |

Run count: `4 cells x 6 folds = 24 runs`

## Leakage Assertions

- all fitted statistics must use training subjects only
- no held-out/test-subject feature statistics
- no test labels in transform/model selection
- no global scaler
- no per-test-subject normalization
- no threshold tuning on test folds

## Future Allowed Files

Only docs/scripts with prefix:

`idare_strict_ntd_norm_smoke_`

## Forbidden

- DEAP
- fusion
- preprocessing changes
- threshold changes
- model-capacity probe
- augmentation
- SupCon/DG execution
- main push

## Current Ruling

This package does not create a runner, does not run experiments, and does not authorize execution.

Next required state:

`AWAITING_APPROVE_STRICT_NTD_NORM_SMOKE_EXECUTION`
