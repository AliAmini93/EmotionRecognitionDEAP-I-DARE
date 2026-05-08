# I-DARE Label-Semantics Redesigned-Task Smoke-Guard Patch Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T12:05:24+00:00`

## Executive Result

| item | value |
| --- | --- |
| selected_primary_formulation | subject_relative_ordinal_affect_regression_v1 |
| future_guard_passed | True |
| actual_forbidden_model_rows | 0 |
| all_passed | True |
| diagnosis | redesigned_task_smoke_tests_passed_after_guard_patch |
| recommended_next_objective | label_semantics_minimal_redesigned_task_first_pass_training_objective |

## Patched Guard Logic

- Scan explicit `model` / `method` columns only.

- Do not scan `notes` as authorized-method declarations.

- Use token-aware DG matching, so `ridge` is not interpreted as `DG`.

- Keep actual SupCon, VREx, DG/domain-generalization, fusion, or contrastive model rows blocked.


## Guard Audit

| check | value | passed | details |
| --- | --- | --- | --- |
| explicit_method_columns_present | model | True | Patched guard scans only explicit model/method columns. |
| future_rows | 48 | True | Expected future matrix size is 48. |
| authorized_now_all_no | True | True | Future matrix must not authorize immediate training. |
| forbidden_explicit_model_rows | 0 | True | Explicit model/method columns must not contain SupCon, VREx, DG, domain-generalization, fusion, or contrastive rows. |
| notes_mentions_supcon_dg_ignored | 48 | True | Notes are explanatory metadata; negated guardrail text is not an authorized method. |
| notes_negative_guardrail_mentions | 48 | True | SupCon/DG appears only as negative guardrail prose in current matrix. |
| ridge_not_dg | 24 | True | Token-aware DG check must not match letters inside ridge. |

## Smoke-Test Decision Matrix

| smoke_test | passed | evidence | action_if_failed |
| --- | --- | --- | --- |
| target_construction_integrity | True | 8064 targets; min=0.0000; max=1.0000 | fix target construction or stop/archive |
| fold_leakage_guard | True | max_subject_overlap=0; max_row_overlap=0 | fix split protocol before any training |
| metric_computation_sanity | True | perfect_spearman=1.0000; reversed_spearman=-1.0000 | fix metric code |
| baseline_no_training_control | True | 48 no-training control rows; mean_null_spearman=0.0021 | fix controls before training |
| target_distribution_audit | True | min_val_target_std=0.2884 | revise target or flag degenerate cells |
| future_run_matrix_guard | True | patched token-aware guard; explicit model/method columns only; notes ignored as metadata | fix future matrix before training objective |

## Interpretation

The previous smoke failure is corrected by a narrow guard patch. The future run matrix contains no actual forbidden model rows; the previous failure came from over-broad scanning of explanatory notes and/or non-token-aware matching. Training is still not authorized until this patched smoke report is reviewed and a separate minimal first-pass objective is created.

## Next Allowed Step

`human_review_closeout_then_create_minimal_redesigned_task_first_pass_objective`


Blocked:

- direct full SupCon/DG training

- broad hyperparameter search

- EEG+EMG fusion

- final LOSO claim

- mainline change

- minimal regression training until patched smoke-test report is reviewed
