# I-DARE Representation Redesign Smoke Objective

## Status

`created_pending_validation`

## Objective ID

`idare_repr_redesign_smoke_objective`

## Authorization

Control Tower approved guarded objective and runner creation only with:

`AUTHORIZE_REPRESENTATION_REDESIGN_SMOKE_GUARDED_OBJECTIVE_AND_RUNNER_CREATION`

This approval does **not** authorize the 24-run smoke execution.

## Allowed Branch / Worktree

- branch: `idare/postwave1/representation-redesign-smoke`
- worktree: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-repr-redesign-smoke`

## Allowed File Prefix

- `docs/idare_repr_redesign_smoke_*`
- `scripts/idare_repr_redesign_smoke_*`

## Scope Lock

- I-DARE only
- EEG-only first
- arousal-only first
- cross-subject / held-out-subject evaluation
- pairwise reference comparison required
- Ridge/classical model only unless explicitly justified
- representation redesign cells only

## Representation Cells

| Cell | Definition | Guarded fitting rule |
|---|---|---|
| R0 | current representation anchor | train-fold scaler + RidgeClassifier only |
| R1 | train-only subject-residualized features | subject residualization fit from training subjects only; held-out subject never residualized using its own statistics |
| R2 | train-only subject-invariant feature selection | feature selection fit from training fold only |
| R3 | diagnostics-first stable-feature subset | stable feature subset fit from training fold only |

## Later Planned Matrix

`4 cells x 6 folds = 24 runs`

This matrix is planned only. The runner must remain in validate/preflight mode by default and must block smoke execution unless Control Tower later issues explicit run approval.

## Required Inputs

- `.cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy`
- `.cache/idare_eeg_cache_index_baseline_corrected.csv`

## Hard Leakage Rules

- all fitted statistics must use training subjects only
- no held-out/test-subject feature statistics
- no test labels
- no global all-subject feature selection
- no per-test-subject normalization
- no target adaptation
- no threshold tuning on held-out subjects
- feature selection, residualization, and stability filters must be fit on training folds only

## Runner Requirements

The guarded runner must:

- default to validate/preflight mode
- validate branch/worktree/scope
- validate required EEG cache/index files
- validate output prefix
- validate leakage constraints
- stop with blocker output if any required input is missing
- stop with blocker output if leakage checks fail
- avoid the 24-run smoke unless Control Tower later issues explicit run approval

## Forbidden

- DEAP
- fusion
- preprocessing changes
- threshold changes
- DG execution
- model-capacity probe
- augmentation
- W1 branch-owned file edits
- main push
- experiment execution before Control Tower run approval

## Validation Output

Validation mode may write only:

- `docs/idare_repr_redesign_smoke_validation_report.md`
- `docs/idare_repr_redesign_smoke_validation_report.json`

## Execution Output, Future Only

Future smoke execution, if later approved, may write only allowed-prefix files such as:

- `docs/idare_repr_redesign_smoke_runs.csv`
- `docs/idare_repr_redesign_smoke_metric_summary.csv`
- `docs/idare_repr_redesign_smoke_leakage_audit.md`
- `docs/idare_repr_redesign_smoke_leakage_audit.json`
- `docs/idare_repr_redesign_smoke_closeout_report.md`
- `docs/idare_repr_redesign_smoke_closeout_report.json`

## Current Next Step

Run only local runner validation/preflight in the authorized worktree. Then report validation result to Control Tower. Do not run the 24-run smoke.
