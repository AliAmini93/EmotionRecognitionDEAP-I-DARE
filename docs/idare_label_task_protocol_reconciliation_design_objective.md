# I-DARE Label/Task and Protocol Reconciliation Design Objective

## Status

`created`

## Objective ID

`idare_label_task_protocol_reconciliation_design_objective`

## Scope

Control Tower documentation/design only.

Forbidden:
- no execution
- no runner creation
- no Wave 2 execution
- no DG execution
- no model-capacity probe
- no augmentation
- no DEAP
- no fusion
- no preprocessing changes
- no threshold changes
- no main push

## Current Root-Cause Context

Root-cause triage accepted this primary diagnosis:

`LABEL_TASK_AND_PROTOCOL_UNCERTAINTY_INTERACTING_WITH_STRONG_SUBJECT_DOMAIN_SHIFT`

Formal root-cause triage decision:

| Direction | Decision |
|---|---|
| A. label/task redesign | PRIMARY_RECOMMENDED |
| B. evaluation/protocol reconciliation | PRIMARY_RECOMMENDED |
| C. representation redesign v2 | NOT_PRIMARY_NOW |
| D. subject/domain-generalization | MECHANISM_PRIMARY_BUT_EXECUTION_DEFERRED |
| E. stop/pivot away from current formulation | CONTINGENT_FALLBACK |

## Purpose

Define a compact reconciliation objective to determine whether the current I-DARE cross-subject formulation is scientifically aligned with:

1. the dataset label structure,
2. the original I-DARE evaluation protocol,
3. the current held-out-subject target,
4. the observed subject-domain shift,
5. the failed/fragile operating-point attempts.

This objective does not authorize execution.

## Reconciliation Questions

### 1. Protocol Alignment

Questions:
- Did the I-DARE paper use subject-dependent, within-subject, cross-subject, LOSO, or another protocol?
- Is the current held-out-subject protocol comparable to the paper's reported setting?
- Are current results being judged against a target the original protocol did not support?

Required future evidence:
- documented protocol extraction from paper/source docs
- table comparing current protocol vs original protocol
- decision on whether current cross-subject target is valid, strict, or misaligned

### 2. Label / Task Formulation

Questions:
- Are arousal/valence labels too subject-dependent for direct cross-subject binary classification?
- Is midpoint-as-high creating instability?
- Would discard-midpoint, subject-relative labels, within-subject preference, or another target better match I-DARE?
- Are arousal and valence equally defensible, or should one be deprioritized?

Required future evidence:
- label policy inventory
- midpoint policy comparison plan
- task-formulation decision matrix
- subject-label bias summary

### 3. Fold / Subject Bias

Questions:
- Are certain held-out folds intrinsically harder because of label distributions or subject bias?
- Do failures cluster around specific subject groups?
- Are fold-level label distributions confounded with subject identity?

Required future evidence:
- fold label distribution summary
- subject label tendency summary
- fold difficulty table based on existing artifacts
- mapping of failed folds across W1, strict NTD, representation smoke, and confirmation

### 4. Interpretation of Prior Results

Questions:
- Did W1D's within-subject signal imply label signal exists only in subject-relative form?
- Did R3 fail confirmation because representation redesign was unstable, or because the target is not stable cross-subject?
- Did strict NTD and W1B fail because normalization cannot fix task/protocol mismatch?

Required future evidence:
- synthesis table connecting W1D, W1B, strict NTD, representation smoke, and confirmation
- explicit ruling on whether more feature engineering is premature

## Candidate Next Directions

| Direction | Status before reconciliation | What would make it valid |
|---|---|---|
| Keep current cross-subject binary formulation | not supported yet | protocol and labels are shown to support it |
| Label/task redesign | primary candidate | labels show subject-dependence or midpoint instability |
| Protocol target redesign | primary candidate | paper/current protocol mismatch is confirmed |
| Representation redesign v2 | deferred | label/protocol reconciliation supports current target |
| DG execution | deferred | protocol/label target is validated first |
| Stop/pivot | fallback | current formulation is unsupported or not scientifically defensible |

## Minimum Future Reconciliation Audit

If later authorized, the audit should be compact and produce:

- protocol comparison report
- label/task policy report
- fold/subject label-bias report
- prior-results interpretation report
- final reconciliation decision matrix
- closeout report/json
- artifact review bundle

No model training is required for this design.

## Decision Gates

The reconciliation should answer:

1. Is the current held-out-subject binary arousal task valid as the main target?
2. Does the original I-DARE protocol support the target being pursued?
3. Should midpoint policy be changed or explicitly treated as unstable?
4. Should the next scientific direction be label/task redesign, protocol redesign, representation v2, DG design, or stop/pivot?
5. Is any future execution justified?

## Current Ruling

This objective does not authorize execution or runner creation.

## Next State

`REQUEST_LABEL_TASK_PROTOCOL_RECONCILIATION_EXECUTION_AUTHORIZATION_PACKAGE`
