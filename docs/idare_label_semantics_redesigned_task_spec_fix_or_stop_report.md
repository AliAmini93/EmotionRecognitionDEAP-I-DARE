# I-DARE Label-Semantics Redesigned-Task Spec-Fix-or-Stop Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T11:42:58+00:00`

## Executive Decision

Selected formulation: `subject_relative_ordinal_affect_regression_v1`

Diagnosis: `redesigned_task_smoke_failure_not_yet_fixable`

Decision: `stop_or_archive_redesigned_branch_pending_manual_review`

Recommendation: `stop_archive_objective`

Recommended next objective: `label_semantics_redesigned_task_stop_archive_objective`

## Failed Smoke Diagnosis

| smoke_test | failure_classification | root_cause | actual_spec_problem | evidence | recommended_action |
| --- | --- | --- | --- | --- | --- |
| future_run_matrix_guard | unresolved_or_stop_trigger | not proven to be a narrow implementation false positive | unknown | requires manual review | stop/archive or create a more focused manual audit objective |

## Future Run Matrix Guard Audit

| check | value | expected | passed |
| --- | --- | --- | --- |
| future_rows | 48 | 48 | True |
| authorized_now_all_no | True | True | True |
| contains_ridge | True | allowed | True |
| contains_supcon | True | False | False |
| contains_fusion | False | False | True |
| contains_real_dg_token | False | False | True |

## Fix-or-Stop Decision Matrix

| decision_option | selected | rationale | next_step | training_authorized |
| --- | --- | --- | --- | --- |
| narrow_fix_objective | False | Only failed smoke is future_run_matrix_guard, and it is explained by a tokenization bug: 'dg' matched inside 'ridge'. | Create patch objective that fixes only the guard and reruns smoke tests. | no |
| stop_archive_objective | True | Use only if failure is a true spec/data degeneracy rather than a guard implementation bug. | Archive redesigned task branch. | no |
| minimal_regression_training | False | Not allowed until patched smoke tests pass and are reviewed. | blocked | no |
| direct_full_supcon_dg_training | False | Still blocked by the project guardrails and unrelated to this smoke failure. | blocked | no |

## Patch Plan

| patch_item | current_behavior | patched_behavior | why | training_authorized |
| --- | --- | --- | --- | --- |
| replace_substring_dg_check | checks whether 'dg' appears anywhere in future matrix text | check explicit forbidden method names/tokens only, e.g. SupCon, VREx, domain_generalization, fusion | prevents false positive on ridge_regression_summary_features | no |
| rerun_same_smokes | smoke test report is failed | rerun all six smoke tests after guard patch | confirm no other hidden failure emerges | no |
| preserve_future_matrix | 48-row matrix contains mean baseline and ridge regression only | do not change future matrix unless explicit forbidden row is found | the future matrix itself appears consistent with the spec | no |

## Interpretation

The smoke failure is not safely explained as a narrow implementation issue. The redesigned branch should be stopped/archived unless human review identifies a valid narrow fix.

## Next Allowed Step

Human review / closeout before creating the selected next objective.


Blocked:

- direct full SupCon/DG training

- broad hyperparameter search

- EEG+EMG fusion

- final LOSO claim

- mainline change

- minimal regression training before patched smoke-test review
