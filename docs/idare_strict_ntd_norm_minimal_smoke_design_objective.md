# I-DARE Strict NTD Normalization Minimal Smoke Design Objective

## Status

`created`

## Objective ID

`idare_strict_ntd_norm_minimal_smoke_design_objective`

## Scope

Control Tower documentation/design only.

Forbidden:
- no experiments
- no runner creation
- no Wave 2 execution
- no W2E execution
- no DEAP
- no fusion
- no preprocessing changes
- no threshold changes
- no main push
- no W1A/W1B/W1C/W1D branch-owned file modifications

## Purpose

Design a minimal future smoke-test objective for strict non-transductive normalization.

This document does not authorize execution. A separate future executable objective and explicit human approval are required before any run.

## Candidate Cells

| Cell | Candidate | Strict NTD rule |
|---|---|---|
| S0 | current / no normalization anchor | no fitted transform |
| S1 | train-fold StandardScaler | fit mean/std on training subjects only |
| S2 | train-fold RobustScaler | fit median/IQR on training subjects only |
| S3 | train-fold frozen quantile/rank mapper | fit mapping on training subjects only and apply frozen |

## Train-Only Fitting Rules

- all normalization statistics must be fit only on training subjects within each fold
- held-out/test subject features may only be transformed using frozen train-derived transforms
- no held-out/test subject unlabeled statistics may be used
- no per-test-subject centering, scaling, ranking, quantile mapping, or adaptation is allowed
- no transform may be fit globally across all subjects

## Leakage Validation Checklist

Before any future execution, a proposed runner/objective must prove:

- no test-subject rows in fit statistics
- no test labels in transform or model selection
- no global scaler across all subjects
- no per-test-subject normalization
- no target-domain adaptation
- no threshold tuning on held-out subjects
- fold splits are explicit and immutable
- train-only transform parameters are recorded
- held-out subjects are transformed using frozen train-derived transforms only

## Future Output Schema

A future executable objective, if separately authorized, must produce:

- runs CSV
- metric summary
- fold-level report
- leakage audit
- closeout report
- decision matrix

## Comparison References

Future results must be compared against:

- W1A pairwise input-definition results
- W1B normalization results
- W1D subject-dominance diagnosis
- REF-PW-EEG-ARO-001 pairwise reference baseline

## Gate Thresholds

Thresholds are unchanged.

- moderate gate: mean balanced accuracy >= 0.53
- strong gate: mean balanced accuracy >= 0.55

This design does not modify thresholds.

## Stop Conditions

- if no strict NTD cell improves meaningfully over S0 anchor, archive strict NTD smoke
- if a strict NTD cell reaches mean balanced accuracy >= 0.53, future executable confirmation may be considered
- if strict NTD fails but W1D diagnosis remains strong, consider representation redesign or DG design, not direct execution

## Human Approval Requirement

This design does not authorize execution.

A separate future executable objective is required before any run.

## Next State

After this objective is committed, the next state is:

`REQUEST_STRICT_NTD_NORM_MINIMAL_SMOKE_DESIGN_REVIEW`
