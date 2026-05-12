# I-DARE Label/Task Protocol Target Policy Decision Package

## Status

`created`

## Package ID

`idare_label_task_protocol_target_policy_decision_package`

## Scope

Control Tower documentation/target-policy decision only.

Forbidden:
- no execution
- no runner creation
- no new audit
- no experiments
- no model results
- no Wave 2 execution
- no DG execution
- no model-capacity probe
- no augmentation
- no representation redesign v2
- no DEAP
- no fusion
- no preprocessing changes
- no threshold changes
- no main push

## Evidence Base

This package follows:

- `NO_ROBUST_CROSS_SUBJECT_OPERATING_POINT_FOUND`
- Root-cause triage accepted A+B first.
- Label/task + protocol reconciliation accepted B+C as recommended.
- Final decision objective ruled current held-out-subject binary arousal as comparator only, not final target.

## Target Policy Decision

The current target policy is not locked for new modeling.

Final current ruling:

`CURRENT_HELD_OUT_BINARY_AROUSAL = COMPARATOR_ONLY_NOT_FINAL_TARGET`

Primary target-policy path:

`LABEL_TASK_POLICY_REDESIGN + PROTOCOL_TARGET_RECONCILIATION`

## Policy Options

| Option | Policy | Decision |
|---|---|---|
| P0 | Keep current held-out-subject binary arousal | comparator only |
| P1 | Redesign label/task policy | primary |
| P2 | Reconcile/change evaluation protocol target | primary |
| P3 | Subject-relative / within-subject formulation | candidate, requires explicit scope |
| P4 | Stop/pivot if no defensible target can be locked | fallback |

## Locked Governance Rules

Before any future run:

1. A target policy must be selected.
2. Comparator must be defined.
3. Evaluation protocol must be defined.
4. Label policy must be defined.
5. Subject-relative / within-subject status must be explicit.
6. Metrics and gates must remain unchanged unless a separate human review approves changes.
7. No operating-point claim may be made from prior fragile results.

## Recommended Target Policy

Recommended next scientific policy:

- Keep current held-out-subject binary arousal as comparator only.
- Do not treat it as final target.
- Prioritize a label/task redesign decision.
- Prioritize protocol target reconciliation.
- Include subject-relative / within-subject formulation as a scoped candidate, not automatic mainline.
- Keep stop/pivot as fallback if no defensible target can be locked.

## What This Package Does Not Authorize

This package does not authorize:

- model training,
- new ablation,
- runner creation,
- protocol change implementation,
- label-policy implementation,
- threshold change,
- final LOSO claim,
- fusion,
- DEAP,
- DG,
- representation redesign v2.

## Required Human Decision Before Execution

Before any future executable objective, Control Tower needs an explicit human decision choosing one:

- `LOCK_TARGET_POLICY_LABEL_TASK_REDESIGN`
- `LOCK_TARGET_POLICY_PROTOCOL_RECONCILIATION`
- `LOCK_TARGET_POLICY_SUBJECT_RELATIVE_CANDIDATE`
- `LOCK_TARGET_POLICY_STOP_PIVOT`
- `REQUEST_TARGET_POLICY_REVISION`

## Current State

`TARGET_POLICY_DECISION_PACKAGE_CREATED_EXECUTION_BLOCKED`

## Next State

`AWAITING_HUMAN_TARGET_POLICY_DECISION`
