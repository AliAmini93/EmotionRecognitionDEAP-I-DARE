# I-DARE Label/Task and Protocol Reconciliation Execution Authorization Package

## Status

`created`

## Package ID

`idare_label_task_protocol_reconciliation_execution_authorization_package`

## Execution Authorization

`NOT_AUTHORIZED`

Execution requires explicit human approval phrase:

`APPROVE_LABEL_TASK_PROTOCOL_RECONCILIATION_EXECUTION`

## Scope

Control Tower documentation/authorization package only.

Forbidden:
- no execution
- no runner creation
- no branch creation
- no worktree creation
- no Wave 2 execution
- no DG execution
- no model-capacity probe
- no augmentation
- no DEAP
- no fusion
- no preprocessing changes
- no threshold changes
- no main push

## Future Executable Branch

`idare/postwave1/label-task-protocol-reconciliation`

## Future Worktree

`/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-label-task-protocol`

## Future Allowed File Prefix

`idare_label_task_protocol_`

## Exact Future Audit Scope

This is a compact reconciliation audit only.

Allowed audit categories:

1. protocol alignment
2. label/task formulation
3. midpoint and threshold policy review
4. fold/subject label-bias review
5. prior-results interpretation
6. final label-task/protocol decision matrix

This is not model development.

## Future Required Questions

### Protocol Alignment

- Did the I-DARE paper/source use subject-dependent, within-subject, cross-subject, LOSO, or another protocol?
- Is the current held-out-subject protocol comparable to the original reported setting?
- Are current results being judged against a target the original protocol did not support?

### Label / Task Formulation

- Are arousal/valence labels too subject-dependent for direct cross-subject binary classification?
- Is midpoint-as-high creating instability?
- Should discard-midpoint, subject-relative labels, within-subject preference, or another target be reviewed?
- Should arousal or valence be deprioritized?

### Fold / Subject Bias

- Are certain held-out folds intrinsically harder because of label distributions or subject tendencies?
- Do failures cluster around specific subject groups?
- Are fold-level label distributions confounded with subject identity?

### Prior-Results Interpretation

- Did W1D's within-subject signal imply label signal exists mainly in subject-relative form?
- Did R3 fail confirmation because representation selection was unstable, or because the target is not stable cross-subject?
- Did strict NTD and W1B fail because normalization cannot fix task/protocol mismatch?

## Allowed Future Inputs

Future reconciliation may read existing committed artifacts from pushed branches/local worktrees, including:

- Wave 1 closeouts
- strict NTD smoke artifacts
- representation redesign smoke artifacts
- representation redesign confirmation artifacts
- root-cause triage artifacts
- project synthesis/final registry docs
- local I-DARE cache/index metadata for label/fold audit only
- I-DARE paper/source docs if present in repo or cited in existing project docs

No manual attachment should be required if files are already pushed or locally present.

## Future Required Outputs

If execution is later approved, the future branch must produce:

- objective doc/json
- guarded runner/script
- protocol comparison report
- label/task policy report
- midpoint/fold/subject-bias report
- prior-results interpretation report
- final reconciliation decision matrix
- closeout report/json
- artifact review bundle

## Required Closeout Decision Matrix

The closeout must classify:

- A: keep current held-out-subject binary arousal formulation
- B: redesign label/task policy before more modeling
- C: reconcile or change evaluation protocol target
- D: use subject-relative / within-subject formulation instead
- E: stop/pivot if current formulation is unsupported

## Stop / Blocker Rules

Stop and notify Control Tower if:

- required artifacts are missing and cannot be read from pushed branches/local worktrees
- I-DARE protocol evidence is unavailable or ambiguous enough to block conclusions
- audit requires new model-development experiments
- scope expands into Wave 2, DG, model-capacity, augmentation, fusion, DEAP, preprocessing, or threshold changes
- output paths escape the allowed prefix
- main push is requested

## Current Ruling

This package does not authorize execution.

## Next State

`AWAITING_APPROVE_LABEL_TASK_PROTOCOL_RECONCILIATION_EXECUTION`
