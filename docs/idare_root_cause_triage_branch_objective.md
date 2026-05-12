# I-DARE Root-Cause Triage Branch Objective

## Status

`created`

## Objective ID

`idare_root_cause_triage_branch_objective`

## Authorization State

Documentation/design only.

Allowed now:
- read existing artifacts/docs/scripts from local worktrees and pushed branches
- create compact root-cause triage objective/spec docs
- create a guarded runner/script plan as documentation only

Not authorized:
- no scripts yet
- no triage/audit execution
- no experiments
- no commit
- no push

## Current Official State

`EXECUTION_PAUSED_PENDING_ROOT_CAUSE_TRIAGE`

Wave 1 is closed and accepted, but no robust cross-subject operating point was found.

## Scope

Compact root-cause triage only across:

1. label/task sanity
2. subject-domain shift
3. evaluation/protocol alignment
4. representation failure
5. null/permutation sanity

## Required Decision Outcomes

The future triage closeout must classify the primary next direction as:

- A: label/task redesign as primary
- B: evaluation/protocol reconciliation as primary
- C: representation redesign v2 as primary
- D: subject/domain-generalization as primary
- E: stop/pivot away from current I-DARE cross-subject formulation

## Hard Boundaries

Forbidden:
- no Wave 2
- no DG execution
- no model-capacity probe
- no augmentation
- no DEAP
- no fusion
- no preprocessing changes
- no threshold changes
- no W1 branch-owned file edits
- no main push
- no scripts yet
- no audit execution

## Stop Rules

Stop and notify Control Tower if required artifacts are missing, if the design requires execution, or if scope expands beyond compact root-cause triage.

## Next State

`CONTROL_NOTIFY_REQUIRED_AFTER_DOCS_CREATED_AND_SELF_VALIDATED`
