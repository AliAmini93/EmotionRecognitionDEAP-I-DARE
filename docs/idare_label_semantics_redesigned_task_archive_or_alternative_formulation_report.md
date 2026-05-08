# I-DARE Label-Semantics Redesigned-Task Archive-or-Alternative-Formulation Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T15:19:19+00:00`

## Executive Decision

Diagnosis: `current_redesigned_task_branch_should_be_archived`

Decision: `archive_current_subject_relative_ordinal_affect_regression_v1_branch`

Recommendation: `archive_closeout_first_then_optional_alternative_formulation_spec`

Recommended next objective: `label_semantics_redesigned_task_archive_closeout_objective`

Decision reason: The current redesigned task has no actionable rank, threshold, or absolute-error signal; therefore the branch should be archived before any alternative formulation is designed.

## Evidence Summary

| Indicator | Value |
|---|---:|
| Current formulation | `subject_relative_ordinal_affect_regression_v1` |
| Max mean Spearman rho | 0.0192 |
| Max q33 balanced accuracy | 0.5071 |
| Cells with mean Spearman >= 0.10 | 0 |
| Cells with q33 >= 0.55 | 0 |
| Cells improving MAE vs mean baseline | 0 |
| Cells improving RMSE vs mean baseline | 0 |

## Archive Scope Decision

| scope_id | archived_item | decision | archive_status_after_review | reason |
| --- | --- | --- | --- | --- |
| ARCHIVE_DECISION_001 | subject_relative_ordinal_affect_regression_v1 | archive_current_redesigned_task_branch | recommended_pending_closeout | Metric-debug found no actionable signal; current formulation is not defensible for more model search. |
| ARCHIVE_DECISION_002 | minimal first-pass evidence for current redesigned task | freeze_as_negative_evidence | recommended_pending_closeout | Evidence is valuable as negative/stop evidence and must remain queryable. |
| ARCHIVE_DECISION_003 | additional training on current redesigned task | block_further_training | recommended_pending_closeout | No metric supports continuing training: Spearman near zero, q33 near chance, no MAE/RMSE improvement. |

## What Is Not Archived

The archive decision does **not** archive raw data, EEG/EMG caches, historical scripts, diagnostic documents, the overall repository, or future alternative formulations that are justified by a separate reviewed spec.

## Alternative Formulation Constraints

| constraint_id | constraint | why_required | forbidden_in_next_step |
| --- | --- | --- | --- |
| ALT_CONSTRAINT_001 | Alternative formulation must be design/spec-only first. | The current branch failed after smoke tests, first pass, failure/confirmation analysis, and metric debug. | training; model search; fusion; final claims |
| ALT_CONSTRAINT_002 | Alternative must explicitly address the failure mechanism. | The observed failure is not a model-capacity issue; it is task/label/metric semantics. | reusing the same subject_relative_ordinal_affect_regression_v1 target unchanged |
| ALT_CONSTRAINT_003 | Alternative must define no-training smoke tests and baseline controls before any first-pass model. | A prior false-positive guard required patching, and weak signals must be caught before training. | jumping directly to neural/SupCon/DG training |
| ALT_CONSTRAINT_004 | Alternative must define stop/archive criteria before execution. | The project must avoid broad search on an ill-posed task. | open-ended exploration without predeclared stop criteria |
| ALT_CONSTRAINT_005 | Alternative must preserve reproducibility-layer discipline. | Historical scripts have been backfilled and active scripts must remain committed. | uncommitted ad-hoc scripts as the sole reproduction path |

## Final Decision Matrix

| decision_option | decision | rationale | next_objective_if_selected | allowed_after_human_review |
| --- | --- | --- | --- | --- |
| archive_current_redesigned_task_branch | selected | No actionable signal after read-only metric debug. | label_semantics_redesigned_task_archive_closeout_objective | yes |
| prepare_alternative_formulation_spec | allowed_after_archive_closeout | A future alternative may be justified, but only as a separate design/spec objective after the current branch is archived. | label_semantics_alternative_formulation_design_spec_objective | conditional |
| continue_current_redesigned_task_training | rejected | No cell improves MAE/RMSE; q33 remains near chance; Spearman is near zero. | not_allowed | no |
| patch_metrics_to_rescue_current_branch | rejected | The problem is not only metric wording; the signal is too weak to rescue the branch. | not_allowed_without_new_evidence | no |
| return_to_SupCon_DG_or_broad_search | rejected | The bottleneck is label/task semantics, not model capacity. | not_allowed | no |

## Interpretation

The current `subject_relative_ordinal_affect_regression_v1` branch should be archived as a negative result. The evidence no longer supports metric patching, further classical model tests, SupCon/DG, or broad model search on this branch.

An alternative formulation can still be scientifically valid, but only after the current branch is closed out and only as a separate design/spec objective with no training initially.

## Next Allowed Step

Human review / closeout before creating the archive closeout objective.

## Blocked

- new training
- model search
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- archive implementation before human review/closeout
- alternative formulation spec before archive closeout review
- alternative formulation training
