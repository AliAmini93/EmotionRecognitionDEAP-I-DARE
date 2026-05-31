# I-DARE Root-Cause Triage Execution Authorization Package

## Status

`created`

## Package ID

`idare_root_cause_triage_execution_authorization_package`

## Execution Authorization

`NOT_AUTHORIZED`

Execution requires explicit human approval phrase:

`APPROVE_ROOT_CAUSE_TRIAGE_EXECUTION`

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

`idare/postwave1/root-cause-triage`

## Future Worktree

`/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage`

## Future Allowed File Prefix

`idare_root_cause_triage_`

## Exact Future Triage Scope

Allowed future audit categories:

1. label/task sanity
2. subject-domain shift
3. evaluation/protocol alignment
4. representation failure
5. null/permutation sanity

This is an audit/triage objective, not a new model-development wave.

## Future Required Questions

### Label / Task Sanity

- Are arousal/valence labels too subject-dependent?
- Are midpoint policies causing instability?
- Are fold-level label distributions or subject label biases dominating performance?

### Subject-Domain Shift

- How much of feature geometry is subject identity vs affect?
- Which folds/subjects consistently break generalization?
- Are failures concentrated in specific held-out subject groups?

### Evaluation / Protocol Alignment

- Is the current held-out-subject protocol comparable to the I-DARE paper?
- Did the paper use subject-dependent, cross-subject, within-subject, or another protocol?
- Are we chasing a target the original protocol does not support?

### Representation Failure

- Do current EEG/EMG features preserve affect signal only within subject?
- Did R2/R3 fail confirmation because selection was unstable, fold-sensitive, or genuinely weak?
- Should representation redesign continue, or should label/task redesign take priority?

### Null / Permutation Sanity

- Compare observed BA against majority/fold/null/permutation baselines.
- Decide whether current gains are above noise enough to justify further modeling.

## Allowed Future Inputs

Future triage may read existing committed artifacts from pushed branches, including:

- Wave 1 closeouts
- Strict NTD smoke artifacts
- representation redesign smoke artifacts
- representation redesign confirmation artifacts
- Control Tower registry/docs
- local I-DARE cache/index metadata, if needed for audit only

No manual artifact attachment should be required if files are already pushed.

## Future Required Outputs

If execution is later approved, the future branch must produce:

- objective doc/json
- guarded runner/script
- label/task sanity report
- subject-domain shift report
- protocol alignment report
- representation failure report
- null/permutation sanity report
- final root-cause decision matrix
- closeout report/json
- artifact review bundle

## Decision Matrix Required In Closeout

The triage closeout must classify:

- A: label/task redesign as primary
- B: evaluation/protocol reconciliation as primary
- C: representation redesign v2 as primary
- D: subject/domain-generalization as primary
- E: stop/pivot away from current I-DARE cross-subject formulation

## Stop / Blocker Rules

Stop and notify Control Tower if:

- required artifacts are missing and cannot be read from GitHub/local branch
- the audit requires new model-development experiments
- scope expands into Wave 2, DG, model-capacity, augmentation, fusion, DEAP, preprocessing, or threshold changes
- output paths escape the allowed prefix
- main push is requested

## Current Ruling

This package does not authorize execution.

## Next State

`AWAITING_APPROVE_ROOT_CAUSE_TRIAGE_EXECUTION`
