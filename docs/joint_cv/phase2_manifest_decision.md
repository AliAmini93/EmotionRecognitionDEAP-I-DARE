# Phase 2 Manifest Decision

## Statistical Unit

One row equals one physical trial. No 5-second window is treated as an independent trial.

## DEAP

- Manifest rows: `1280`
- Manifest audit passed: `True`
- Subject-held-out analyses ready: `True`
- Stimulus-held-out analyses ready: `False`
- Strict Joint subject–stimulus CV ready: `False`
- Reason: official subject-specific trial-position to common stimulus identity mapping is unavailable.

## I-DARE

- Manifest rows: `2016`
- Manifest audit passed: `True`
- Subject-held-out analyses ready: `True`
- Stimulus-held-out analyses ready: `True`
- Strict Joint subject–stimulus CV ready: `True`

## Safe Next Step

Review these manifests and reports. After review, build Strict Joint folds for I-DARE only. Keep DEAP Strict Joint folds blocked.
