# I-DARE Label-Semantics Alternative-Formulation Design Spec Objective

## Status

Status: objective created; design/spec only; no training is authorized.

Created UTC: `2026-05-08T15:46:10+00:00`

## Scientific Question

Can we define a materially different label-semantics task formulation that avoids the archived branch failure mode before any new training is considered?

## Accepted Archive Context

Archived formulation: `subject_relative_ordinal_affect_regression_v1`

Accepted archive diagnosis: `redesigned_task_branch_archived_as_negative_result`

Accepted archive decision: `archive_closeout_complete_for_subject_relative_ordinal_affect_regression_v1`

## Core Principle

The next step is not to rescue the archived formulation. The next step is to decide whether a materially different formulation can be specified, audited, and smoke-tested.

## Authorized Work

- Read archived-branch evidence.
- Compare alternative task formulation candidates.
- Select zero or one primary alternative candidate for a future smoke-test objective.
- Define metric alignment, target-construction guardrails, and stop/archive criteria.
- Produce an implementation-ready design/spec only.

## Not Authorized

- training
- model search
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- implementation of any alternative before design/spec review
- reopening archived `subject_relative_ordinal_affect_regression_v1` without new evidence

## Candidate Matrix

See: `docs/idare_label_semantics_alternative_formulation_candidate_matrix.csv`

## Design Constraints

See: `docs/idare_label_semantics_alternative_formulation_design_constraints.csv`

## Spec Requirements

See: `docs/idare_label_semantics_alternative_formulation_spec_requirements.csv`

## Decision Tree

See: `docs/idare_label_semantics_alternative_formulation_design_decision_tree.csv`

## Smoke Plan Seed

See: `docs/idare_label_semantics_alternative_formulation_smoke_plan_seed.csv`

## Expected Outputs

- `docs/idare_label_semantics_alternative_formulation_design_spec.md`
- `docs/idare_label_semantics_alternative_formulation_design_spec.json`
- `docs/idare_label_semantics_alternative_formulation_candidate_decision_matrix.csv`
- `docs/idare_label_semantics_alternative_formulation_selected_task_definition.csv`
- `docs/idare_label_semantics_alternative_formulation_metric_plan.csv`
- `docs/idare_label_semantics_alternative_formulation_smoke_test_plan.csv`
- `docs/idare_label_semantics_alternative_formulation_stop_criteria.csv`

## Pass Criteria

- No training is run or authorized.
- The archived formulation is not reused unchanged.
- The spec explains why the selected candidate is materially different.
- The spec defines smoke tests before any future training.
- The spec defines stop/archive criteria before any future training.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_formulation_design_spec_command`
