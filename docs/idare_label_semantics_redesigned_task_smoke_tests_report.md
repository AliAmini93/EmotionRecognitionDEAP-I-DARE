# I-DARE Label-Semantics Redesigned-Task Smoke Tests Report

## Status

Status: complete; patched guard result pending human review.

Patched UTC: `2026-05-08T12:05:24+00:00`

## Executive Result

- Selected formulation: `subject_relative_ordinal_affect_regression_v1`

- Diagnosis: `redesigned_task_smoke_tests_passed_after_guard_patch`

- all_passed: `True`

- recommended_next_objective: `label_semantics_minimal_redesigned_task_first_pass_training_objective`

## Patched Future-Run Matrix Guard

- Actual forbidden model rows: `0`

- Future guard passed: `True`

- Notes were not treated as authorized method declarations.

- Token-aware DG check prevented `ridge` from being treated as `DG`.

## Smoke-Test Decision Matrix

| smoke_test | passed | evidence | action_if_failed |
| --- | --- | --- | --- |
| target_construction_integrity | True | 8064 targets; min=0.0000; max=1.0000 | fix target construction or stop/archive |
| fold_leakage_guard | True | max_subject_overlap=0; max_row_overlap=0 | fix split protocol before any training |
| metric_computation_sanity | True | perfect_spearman=1.0000; reversed_spearman=-1.0000 | fix metric code |
| baseline_no_training_control | True | 48 no-training control rows; mean_null_spearman=0.0021 | fix controls before training |
| target_distribution_audit | True | min_val_target_std=0.2884 | revise target or flag degenerate cells |
| future_run_matrix_guard | True | patched token-aware guard; explicit model/method columns only; notes ignored as metadata | fix future matrix before training objective |

## Next Allowed Step

`human_review_closeout_then_create_minimal_redesigned_task_first_pass_objective`


Training remains blocked until human review/closeout.
