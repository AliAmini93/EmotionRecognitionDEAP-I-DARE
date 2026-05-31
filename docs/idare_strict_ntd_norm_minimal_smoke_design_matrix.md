# I-DARE Strict NTD Normalization Minimal Smoke Design Matrix

## Status

`created`

## Purpose

Define the minimum defensible future smoke matrix for strict non-transductive normalization, without authorizing execution.

## Cell Matrix

| Cell | Candidate | Fit rule | Held-out/test usage | Status |
|---|---|---|---|---|
| S0 | current / no normalization anchor | no transform fit | no held-out stats used | design candidate |
| S1 | train-fold StandardScaler | fit mean/std on training subjects only | apply frozen transform only | design candidate |
| S2 | train-fold RobustScaler | fit median/IQR on training subjects only | apply frozen transform only | design candidate |
| S3 | train-fold frozen quantile/rank mapper | fit quantile/rank mapping on training subjects only | apply frozen mapping only | design candidate |

## Excluded From Minimal Smoke

| Candidate | Reason |
|---|---|
| per-test-subject z-score | transductive |
| per-test-subject rank transform | transductive / W1B B3 diagnostic-only |
| test-time adaptation | transductive |
| target distribution alignment | transductive |
| DG smoke | deferred until strict NTD design review is complete |
| W2E interaction grid | design subsection only, not execution |
| model capacity probe | deferred |
| augmentation | deferred |
| representation redesign | fallback if strict NTD path is weak |

## Required Future Decision Points

Before execution, Control Tower must review:

1. exact input files
2. exact fold protocol
3. exact train-only transform fitting implementation
4. exact leakage audit
5. exact output schema
6. exact comparison references
7. unchanged thresholds
8. explicit human approval

## Current Ruling

No execution is authorized by this matrix.
