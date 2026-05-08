# I-DARE Label-Semantics Task-Redesign Spec Objective

## Status

Status: objective created; design/spec only; no training is authorized.

Created UTC: `2026-05-08T11:10:33+00:00`

## Scientific Question

Can we define one defensible label/task formulation that directly addresses the accepted label-semantics and representation-transfer bottleneck without cherry-picking or resuming broad model search?

## Diagnosis Context

Accepted diagnosis: `current_global_binary_loso_task_not_defensible_for_more_model_search`

Accepted decision: `pause_current_global_binary_loso_training_and_prepare_task_redesign_spec`

Stop condition: If a defensible redesign spec cannot be accepted, stop/archive the current binary LOSO branch.

## Core Principle

Do not improve the model until the target is scientifically defensible.

The current global binary LOSO branch is paused as a final-performance path. The next work must define the task first.

## Authorized Work

- Read the existing decision report, candidate matrix, evidence-gap audit, and representation/label-semantics failure analysis.
- Create an implementation-ready task-redesign specification.
- Lock label definition, inclusion/exclusion rules, split protocol, metrics, and anti-cherry-picking guardrails.
- Select exactly one primary next formulation, or select stop/archive.
- No model training.
- No broad hyperparameter search.

## Candidate Formulations to Evaluate

| Candidate | Role in the spec |
|---|---|
| `ordinal_or_regression_affect_rating_task` | Primary redesign candidate if rating magnitude should be preserved. |
| `subject_relative_binary_top_bottom_q33` | Candidate if subject-relative binary semantics remain preferred. |
| `restricted_high_confidence_label_task` | Secondary diagnostic candidate only if inclusion rules can be locked before training. |
| `personalization_or_few_shot_adaptation_task` | Alternative scientific claim if pure LOSO is not the right target. |
| `stop_archive_current_global_binary_loso_path` | Required fallback if no defensible redesign is accepted. |

## Required Spec Sections

1. Scientific claim.
2. Label definition.
3. Allowed samples and excluded samples.
4. Train/validation/test protocol.
5. Metrics and pass criteria.
6. Leakage controls.
7. Anti-cherry-picking rules.
8. Minimal future run matrix if training is later authorized.
9. Explicit stop/archive criteria.

## Evidence That Must Be Addressed

- Best targeted pair-sampler candidate remained weak and unstable.
- Pair sampler was judged valid but not the primary failure mode.
- Prior report diagnosed a joint label-semantics and representation-transfer bottleneck.
- Current global binary LOSO task is not defensible for more model search.
- Subject-relative labeling alone was not sufficient.
- direct full SupCon/DG training remains blocked.
- broad hyperparameter search remains blocked.
- final LOSO claim remains blocked.

## Pass Criteria

- The spec is complete enough to implement without guessing.
- Exactly one primary candidate is selected, or stop/archive is selected.
- All inclusion/exclusion rules are pre-registered before training.
- Metrics align with the scientific claim.
- The spec explicitly blocks direct full SupCon/DG training until reviewed.
- The spec explicitly blocks broad hyperparameter search.
- The spec explicitly blocks final LOSO claim.

## Next Allowed Step

Prepare a reviewed label-semantics task-redesign spec command/script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new training before redesign spec review
