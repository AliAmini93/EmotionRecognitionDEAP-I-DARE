# I-DARE Strict Non-Transductive Normalization / DG Leakage Review

## Status

`created`

## Scope

Control Tower leakage review only. No execution is authorized.

## Leakage Principle

Held-out/test subject statistics are not allowed for strict non-transductive evidence.

This includes unlabeled statistics.

## Required Leakage Checklist Before Any Future Execution

A future executable objective must pass all checks below.

### Split and Subject Checks

- held-out subjects are excluded from all transform fitting.
- train/validation/test subject IDs are explicit.
- no row from a held-out subject is used in scaler/ranker/mapper fitting.
- fold definitions are immutable and recorded.

### Transform-Fitting Checks

- scaler parameters are fit on training subjects only.
- robust statistics are fit on training subjects only.
- quantile/rank mappings are fit on training subjects only.
- PCA/whitening/covariance transforms are fit on training subjects only.
- no target-subject batch statistics are used.

### DG Checks

- subject/domain labels used for DG are training-subject labels only.
- no held-out subject domain information is used for fitting.
- no target adaptation, entropy minimization, or test-time updates are used.
- DG losses are computed only on training data.

### Calibration Checks

- thresholds are unchanged.
- no threshold is tuned on held-out subjects.
- no post-hoc calibration uses test labels or test scores.
- no fold-global calibration includes held-out rows.

### File and Scope Checks

- no DEAP files.
- no fusion files.
- no preprocessing/cache rebuild.
- no rereference/CAR.
- no downsampling rebuild.
- no W1 branch-owned files modified.
- no push to main.

## Candidate Validity Ruling

| Candidate family | Leakage status |
|---|---|
| train-fold StandardScaler | allowed if train-only |
| train-fold RobustScaler | allowed if train-only |
| train-fold quantile/rank mapper | allowed if train-only and frozen |
| per-test-subject z-score | blocked |
| per-test-subject rank transform | blocked as strict evidence |
| test-time adaptation | blocked |
| target distribution alignment | blocked |
| DG using training subjects only | design-reviewable |
| DG using target/held-out stats | blocked |

## Evidence Needed Before Execution

Before any future run, Control Tower must receive a documentation-only execution proposal containing:

1. exact cells,
2. exact input files,
3. exact train-only transform fitting rules,
4. leakage validation plan,
5. output file list,
6. closeout schema,
7. comparison references,
8. unchanged gate thresholds,
9. freeze enforcement statement.

## Current Ruling

No future executable objective is authorized by this leakage review.
