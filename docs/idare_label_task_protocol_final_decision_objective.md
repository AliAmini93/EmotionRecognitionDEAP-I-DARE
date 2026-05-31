# I-DARE Label/Task Protocol Final Decision Objective

## Status

`created`

## Objective ID

`idare_label_task_protocol_final_decision_objective`

## Scope

Control Tower documentation/final decision only.

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

This decision is based on:

- Project final registry: `NO_ROBUST_CROSS_SUBJECT_OPERATING_POINT_FOUND`
- Root-cause triage: label/task + protocol uncertainty interacting with strong subject-domain shift
- Label/task + protocol reconciliation audit:
  - latest branch commit: `19188db`
  - status: `closeout_ready`
  - blocker status: none
  - no experiments or model results created
  - no new operating-point claim

## Final Decision Purpose

Choose the next scientific governance target before any future modeling.

The project should not continue blind model/feature searches until the target formulation is locked.

## Final Decision Summary

| Decision area | Final ruling |
|---|---|
| Current held-out-subject binary arousal | Keep only as documented comparator / continuity reference |
| Label/task policy | Redesign/review before more modeling |
| Evaluation protocol target | Reconcile or change before more modeling |
| Subject-relative / within-subject formulation | Supported candidate, not automatic mainline |
| Stop/pivot | Keep as contingency fallback |
| DG / model-capacity / representation v2 | Deferred until label/protocol target is locked |

## Final Ruling

`CURRENT_HELD_OUT_BINARY_AROUSAL = COMPARATOR_ONLY_NOT_FINAL_TARGET`

`LABEL_TASK_POLICY_REDESIGN = PRIMARY_NEXT_DESIGN_PATH`

`PROTOCOL_TARGET_RECONCILIATION = PRIMARY_NEXT_DESIGN_PATH`

`SUBJECT_RELATIVE_WITHIN_SUBJECT = SUPPORTED_CANDIDATE_NOT_AUTO_MAINLINE`

`STOP_PIVOT = CONTINGENCY_NOT_IMMEDIATE_DEFAULT`

## Implication

The next valid project step is not another model run.

The next valid step is a documentation-only decision package defining the future target policy:

1. whether to redesign labels,
2. whether to change or reconcile the evaluation protocol,
3. whether subject-relative / within-subject formulation becomes a scoped candidate,
4. whether the current held-out-subject binary arousal formulation remains only as comparator,
5. whether to stop/pivot if no defensible target can be locked.

## Next State

`REQUEST_LABEL_TASK_PROTOCOL_TARGET_POLICY_DECISION_PACKAGE`
