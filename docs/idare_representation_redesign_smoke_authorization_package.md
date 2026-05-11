# I-DARE Representation Redesign Smoke Authorization Package

## Status

`created`

## Package ID

`idare_representation_redesign_smoke_authorization_package`

## Execution Authorization

`NOT_AUTHORIZED`

Execution requires explicit human approval phrase:

`APPROVE_REPRESENTATION_REDESIGN_SMOKE_EXECUTION`

Even after branch/worktree setup, the future execution chat must request Control approval before running the 24-run smoke.

## Scope

Control Tower documentation/authorization package only.

Forbidden:
- no experiments
- no runner creation
- no branch creation
- no worktree creation
- no smoke run
- no Wave 2 execution
- no DG execution
- no model-capacity probe
- no augmentation
- no DEAP
- no fusion
- no preprocessing changes
- no threshold changes
- no main push
- no W1 branch-owned file modifications

## Future Executable Branch

`idare/postwave1/representation-redesign-smoke`

## Future Worktree

`/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-repr-redesign-smoke`

## Future Allowed File Prefix

`idare_repr_redesign_smoke_`

## Exact Future Executable Scope

- I-DARE only
- EEG-only first
- arousal-only first
- cross-subject / held-out-subject evaluation
- pairwise reference comparison required
- ridge/classical model only unless explicitly justified
- representation redesign cells only

## Future Cell Matrix

| Cell | Definition |
|---|---|
| R0 | current representation anchor |
| R1 | train-only subject-residualized features |
| R2 | train-only subject-invariant feature selection |
| R3 | diagnostics-first stable-feature subset |

Run count:

`4 representation cells x 6 folds = 24 runs`

## Leakage Assertions

- all fitted statistics must use training subjects only
- no held-out/test-subject feature statistics
- no test labels
- no global all-subject feature selection
- no per-test-subject normalization
- no target adaptation
- no threshold tuning on held-out subjects
- feature selection, residualization, and stability filters must be fit on training folds only

## Required Outputs For Future Executable Branch

- objective doc/json
- runner/script
- runs CSV
- metric summary
- fold-level report
- leakage audit
- representation diagnostic report
- closeout report/json
- artifact review bundle

## Gate Thresholds

Thresholds are unchanged:

- moderate gate: mean balanced accuracy >= 0.53
- strong gate: mean balanced accuracy >= 0.55

No threshold changes are authorized.

## Stop / Blocker Rules

Stop and notify Control Tower if:

- leakage audit fails
- any transform uses test-subject statistics
- required cache/index files are missing
- file outputs escape the allowed prefix
- scope expansion is needed
- DEAP, fusion, preprocessing changes, threshold changes, DG execution, model-capacity probe, or augmentation are requested

Archive if:

- no R cell improves meaningfully over R0

Consider DG design only if:

- representation redesign shows some signal but insufficient transfer

## Required Control Sequence After Human Approval

1. create branch/worktree only
2. future chat performs preflight only
3. Control reviews preflight
4. future chat may create objective/runner only if Control approves
5. future chat must request Control run approval before any 24-run smoke execution
6. after execution, future chat submits closeout/artifact review bundle
7. Control performs formal artifact review

## Current Ruling

This package does not authorize execution.

## Next State

`AWAITING_APPROVE_REPRESENTATION_REDESIGN_SMOKE_EXECUTION`
