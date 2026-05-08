# I-DARE Label-Semantics Redesigned-Task Archive-or-Alternative-Formulation Objective

## Status

Status: objective created; read-only decision analysis only; no training is authorized.

Created UTC: `2026-05-08T15:14:36+00:00`

## Scientific Question

Should the current redesigned task branch be archived, and under what constraints may an alternative formulation be designed?

## Triggering Evidence

- Accepted metric-debug diagnosis: `redesigned_task_metric_debug_no_actionable_signal`
- Accepted recommendation: `archive_or_alternative_formulation_after_review`
- Decision reason: The best rank signal is far below a practical threshold, q33 separation remains near chance, and no cell improves MAE/RMSE over the mean baseline.
- Current formulation: `subject_relative_ordinal_affect_regression_v1`
- Max mean Spearman rho: `0.019171068580299766`
- Max q33 balanced accuracy: `0.5070515450953589`
- Cells improving MAE vs baseline: `0`
- Cells improving RMSE vs baseline: `0`

## Authorized Work

- Read existing metric-debug and redesigned-task evidence.
- Define the precise archive scope for the current task branch.
- Define requirements for any future alternative formulation.
- Produce a decision matrix selecting archive, alternative-spec, or no-action.

## Archive Scope Seed

See: `docs/idare_label_semantics_redesigned_task_archive_scope.csv`

## Alternative Formulation Requirements

See: `docs/idare_label_semantics_alternative_formulation_requirements.csv`

## Decision Tree

See: `docs/idare_label_semantics_archive_or_alternative_formulation_decision_tree.csv`

## Expected Outputs

- `docs/idare_label_semantics_redesigned_task_archive_or_alternative_formulation_report.md`
- `docs/idare_label_semantics_redesigned_task_archive_or_alternative_formulation_report.json`
- `docs/idare_label_semantics_redesigned_task_archive_scope_decision.csv`
- `docs/idare_label_semantics_alternative_formulation_candidate_constraints.csv`
- `docs/idare_label_semantics_archive_or_alternative_formulation_final_decision_matrix.csv`

## Pass Criteria

- No training is run.
- No archive implementation is performed inside this objective creation step.
- The archive scope clearly states what is and is not archived.
- Any alternative path is design/spec-only and gated by a separate review.
- Exactly one recommended next objective is produced.

## Next Allowed Step

`prepare_reviewed_label_semantics_redesigned_task_archive_or_alternative_formulation_command`

## Blocked

- new training
- model search
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- implementation of archive before this objective is reported/reviewed
- implementation of alternative formulation before a separate design/spec is reviewed
