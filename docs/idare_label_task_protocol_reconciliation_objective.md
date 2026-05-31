# I-DARE Label/Task + Protocol Reconciliation Objective

## Status

Creation authorized by Control Tower for objective and guarded runner artifacts only.

This objective does not authorize reconciliation/audit execution.

## Branch / Worktree

- Branch: `idare/postwave1/label-task-protocol-reconciliation`
- Worktree: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-label-task-protocol`

## Allowed Prefix

All produced artifacts for this phase must use:

```text
idare_label_task_protocol_
```

Allowed locations:

```text
docs/idare_label_task_protocol_*
scripts/idare_label_task_protocol_*
```

## Scope

Compact label/task + protocol reconciliation only.

This is not:

- Wave 2
- DG
- model-capacity probing
- augmentation
- representation redesign v2
- DEAP work
- fusion
- preprocessing work
- threshold changing
- main-branch work

## Audit Categories Encoded for Future Explicit Approval

The guarded runner may only encode these categories:

1. protocol alignment
2. label/task formulation
3. midpoint and threshold policy review
4. fold/subject label-bias review
5. prior-results interpretation
6. final label-task/protocol decision matrix

## Required Guardrails

The runner must:

- default to validate/preflight mode
- validate branch/worktree/scope
- validate required prior artifacts/docs
- validate required cache/index metadata
- validate output prefix
- stop with blocker output if required inputs are missing
- refuse reconciliation/audit execution unless Control Tower later issues explicit run approval

## Current Authorization Boundary

Authorized now:

- create this objective artifact
- create guarded runner artifact
- run validation/preflight mode only

Not authorized now:

- run reconciliation/audit
- create model results
- run experiments
- run Wave 2
- run DG
- run model-capacity probe
- run augmentation
- run representation redesign v2
- touch DEAP
- touch fusion
- make preprocessing changes
- change thresholds
- push to main
- edit W1-owned files

## Validation Outputs

The validation/preflight runner should produce:

- `docs/idare_label_task_protocol_reconciliation_runner_validation.md`
- `docs/idare_label_task_protocol_reconciliation_runner_validation.json`

These validation outputs are blocker/readiness reports only, not audit results.
