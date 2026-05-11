# I-DARE Representation Redesign Confirmation Objective

## Status

`created`

## Objective ID

`idare_representation_redesign_confirmation_objective`

## Execution Authorization

`NOT_AUTHORIZED`

Execution requires explicit human approval phrase:

`APPROVE_REPRESENTATION_REDESIGN_CONFIRMATION_EXECUTION`

## Scope

Control Tower documentation/design/authorization package only.

Forbidden:
- no execution
- no runner creation yet
- no Wave 2 execution
- no DG execution
- no model-capacity probe
- no augmentation
- no DEAP
- no fusion
- no preprocessing changes
- no threshold changes
- no main push

## Purpose

Confirm whether the moderate-pass R3 representation redesign smoke result is robust enough to become the next operating point, while retaining R2 as a near-miss comparator and R0 as the anchor.

## Prior Evidence

Representation redesign smoke result:

- best cell: R3 diagnostics-first stable-feature subset
- R3 mean balanced accuracy: 0.532721790019799
- moderate gate >= 0.53: PASS
- strong gate >= 0.55: NOT MET
- leakage audit: passed
- one-class collapse: 0
- forbidden scope touched: false

Important stability note:

- R2 mean BA: 0.5284867731698891
- R2 fold wins vs R0: 5/6
- R3 mean BA: 0.532721790019799
- R3 fold wins vs R0: 3/6

Therefore confirmation must not simply celebrate R3. It must test whether R3 is robust and whether R2 is more fold-stable.

## Confirmation Cells

| Cell | Role | Include? |
|---|---|---|
| R0 | current representation anchor | yes |
| R2 | train-only subject-invariant feature selection | yes, near-miss comparator |
| R3 | diagnostics-first stable-feature subset | yes, primary confirmation candidate |
| R1 | train-only subject-residualized features | no, excluded from confirmation |

Future intended run count if separately authorized:

`3 cells x 6 folds = 18 runs`

## Future Executable Scope

If later authorized:

- I-DARE only
- EEG-only
- arousal-only
- cross-subject / held-out-subject setting
- same held-out-subject folds unless Control explicitly changes this
- Ridge/classical model family only
- strict train-fold-only feature selection and fitting
- no held-out/test-subject statistics
- no test labels
- no global all-subject feature selection
- no threshold tuning

## Required Future Outputs

Allowed future file prefix:

`idare_repr_redesign_confirm_`

Required outputs if later authorized:

- objective doc/json
- guarded runner/script
- runs CSV
- metric summary
- fold-level report
- leakage audit
- R2 vs R3 stability comparison
- closeout report/json
- artifact review bundle

## Confirmation Gates

For confirmation to pass:

- R3 mean balanced accuracy must remain >= 0.53
- leakage audit must pass
- one-class collapse must be 0
- forbidden scope touched must be false
- R3 must show positive mean delta vs R0
- R2 must remain reported as near-miss/stability comparator
- thresholds remain unchanged

Strong gate remains:

- mean balanced accuracy >= 0.55

No threshold changes are authorized.

## Stop Criteria

Archive or downgrade the representation redesign path if:

- R3 falls below 0.53
- R3 improvement is driven by one unstable fold only
- R2 is more stable than R3 without clear R3 advantage
- leakage audit fails
- one-class collapse occurs
- any test-subject statistics are used
- any forbidden scope is touched

Consider future model-capacity or DG design only if confirmation supports a stable operating point. Do not authorize those here.

## Current Ruling

This document does not authorize execution.

## Next State

`AWAITING_APPROVE_REPRESENTATION_REDESIGN_CONFIRMATION_EXECUTION`
