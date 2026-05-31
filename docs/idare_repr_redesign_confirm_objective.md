# I-DARE Representation Redesign Confirmation Objective

## Status

`guarded_objective_created`

## Authorization State

Control Tower has authorized guarded objective documentation and guarded runner creation only.

Execution is not authorized.

The 18-run confirmation is not authorized.

Commit and push are not authorized.

## Objective ID

`idare_repr_redesign_confirm_objective`

## Scope

This objective is limited to:

- I-DARE only
- EEG-only
- arousal-only
- cross-subject / held-out-subject setting
- same held-out-subject folds unless Control Tower explicitly changes this
- Ridge/classical model family only
- strict train-fold-only feature selection and fitting

## Cells

| Cell | Name | Role |
|---|---|---|
| R0 | current representation anchor | anchor/control |
| R2 | train-only subject-invariant feature selection | near-miss/stability comparator |
| R3 | diagnostics-first stable-feature subset | primary confirmation candidate |

Planned matrix, if later approved:

`3 cells x 6 folds = 18 runs`

## Current Permission Boundary

Allowed now:

- create `docs/idare_repr_redesign_confirm_*`
- create `scripts/idare_repr_redesign_confirm_*`
- validate guarded runner preflight behavior

Not allowed now:

- no confirmation execution
- no 18-run confirmation
- no experiments
- no commit
- no push

## Hard Leakage Rules

All future executable confirmation logic must obey:

- all fitted statistics must use training subjects only
- no held-out/test-subject feature statistics
- no test labels for fitting or selection
- no global all-subject feature selection
- no per-test-subject normalization
- no target adaptation
- no threshold tuning on held-out subjects
- feature selection and stability filters must be fit on training folds only

## Forbidden Scope

The confirmation objective and runner must not touch or initiate:

- DEAP
- fusion
- preprocessing changes
- threshold changes
- DG execution
- model-capacity probe
- augmentation
- main push
- W1 branch-owned file edits
- direct GitHub write/commit

## Guarded Runner Requirements

The guarded runner must:

- default to validate/preflight mode
- validate branch/worktree/scope
- validate required EEG cache/index files
- validate output prefix
- validate leakage constraints
- stop with blocker output if required inputs are missing
- stop with blocker output if leakage checks fail
- not execute the 18-run confirmation unless Control Tower later issues explicit run approval

## Required Validation Before Any Future Execution

Before any future execution request, the runner must report:

- branch
- HEAD
- worktree path
- dirty-file scope
- cache/index presence
- allowed output prefixes
- planned cells
- planned fold count
- planned matrix size
- leakage guard status
- blocker status

## Future Outputs If Execution Is Later Authorized

Future outputs, only if Control Tower later authorizes execution, must use:

- `docs/idare_repr_redesign_confirm_*`
- `scripts/idare_repr_redesign_confirm_*`

Expected future result artifacts may include:

- run manifest
- fold-level metrics
- leakage audit
- R2 vs R3 stability comparison
- closeout report/json

## Current Next State

`AWAITING_CONTROL_TOWER_EXECUTION_AUTHORIZATION`

This document does not authorize execution.
