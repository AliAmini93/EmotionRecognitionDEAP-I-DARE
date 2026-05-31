# I-DARE Strict NTD Normalization Smoke Objective

## Status

`guarded_objective_created_not_executed`

## Human Authorization State

The human approval phrase has been issued in chat:

`APPROVE_STRICT_NTD_NORM_SMOKE_EXECUTION`

This document and the runner creation do not execute the smoke. Execution still requires a separate explicit run command after this guarded creation step is reviewed.

## Scope

Allowed scope:

- I-DARE only
- EEG-only
- arousal-only
- within-subject pairwise affect-preference ranking formulation
- fixed ridge readout
- strict non-transductive normalization only

Forbidden in this branch:

- DEAP
- fusion
- preprocessing changes
- threshold changes
- model-capacity probe
- augmentation
- SupCon/DG execution
- main push
- edits to W1A/W1B/W1C/W1D-owned files

## Fixed Inputs

The smoke runner uses the existing baseline-corrected I-DARE EEG cache as the fixed input artifact:

- `.cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy`
- `.cache/idare_eeg_cache_index_baseline_corrected.csv`

The original non-baseline-corrected EEG cache remains available for audit/reference but is not the default input for this strict NTD smoke runner:

- `.cache/idare_eeg_windows_32x640_float32.npy`
- `.cache/idare_eeg_cache_index.csv`

No raw MATLAB/HDF5 files are loaded by the runner.

## Cell Matrix

| Cell | Candidate | Fit rule | Held-out/test usage |
|---|---|---|---|
| S0 | current / no additional normalization | no fitted transform | no held-out statistics used |
| S1 | train-fold StandardScaler | fit mean/std on training subjects only | apply frozen transform only |
| S2 | train-fold RobustScaler | fit median/IQR on training subjects only | apply frozen transform only |
| S3 | train-fold frozen quantile/rank mapper | fit empirical per-feature rank map on training subjects only | apply frozen rank map only |

## Run Count

`4 cells x 6 folds = 24 runs`

## Pairwise Formulation

For each fold and cell:

1. Build compact EEG window features from the fixed cache.
2. Fit the cell-specific normalization transform using training-subject rows only.
3. Transform train and held-out subject rows with the frozen fold transform.
4. Build within-subject arousal-preference pairs.
5. Train a fixed ridge readout on training-subject pairs only.
6. Evaluate on held-out subject pairs only.

Pair label:

- `1` if the first window has higher `arousal_score` than the second.
- `0` otherwise.
- Equal-score pairs are skipped.
- Both pair directions are included for non-tied pairs to keep the formulation symmetric.

## Leakage Rules

Required leakage guards:

- all fitted statistics use training subjects only
- no held-out/test-subject feature statistics
- no test labels in transform/model selection
- no global scaler
- no per-test-subject normalization
- no target-domain adaptation
- no threshold tuning on test folds

## Runner

Created runner:

- `scripts/idare_strict_ntd_norm_smoke_runner.py`

Runner behavior:

- default mode is dry-run / plan-only
- actual execution requires:
  - `--execute`
  - `--approval-phrase APPROVE_STRICT_NTD_NORM_SMOKE_EXECUTION`
- outputs are restricted to files with prefix `idare_strict_ntd_norm_smoke_`

## Expected Execution Outputs

When separately authorized and executed later, the runner writes:

- `docs/idare_strict_ntd_norm_smoke_report.md`
- `docs/idare_strict_ntd_norm_smoke_report.json`
- `docs/idare_strict_ntd_norm_smoke_runs.csv`

## Current Step Boundary

This step creates the guarded objective and runner only.

No smoke experiment is executed by this file-creation step.
