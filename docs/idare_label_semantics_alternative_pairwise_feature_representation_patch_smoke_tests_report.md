# I-DARE Alternative Pairwise Feature-Representation Patch Smoke Tests Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-09T00:58:08+00:00`

## Executive Result

Diagnosis: `feature_representation_patch_smoke_tests_passed`

All smoke tests passed: `True`

Recommended next objective: `label_semantics_alternative_pairwise_feature_representation_patch_first_pass_objective`

## Detected Columns and Cache Shape

- Subject column: `subject_id`
- Trial/window column: `__row_id__`
- Arousal label column: `arousal_score`
- Index rows: `2016`
- Windows shape: `[2016, 32, 640]`

## Feature Shape Audit

| feature_set_id | window_rows | n_features | finite_fraction | pass |
| --- | --- | --- | --- | --- |
| current_summary_diff_control | 2016 | 128 | 1.0 | True |
| robust_scaled_current_summary_diff_control | 2016 | 128 | 1.0 | True |
| bandpower_only_control_v1 | 2016 | 128 | 1.0 | True |
| bandpower_temporal_stats_v1 | 2016 | 256 | 1.0 | True |

## Pair Target Audit

| task | n_subjects | non_tie_within_subject_pairs | canonical_positive_rate | subjects_with_non_tie_pairs | same_subject_only_by_construction | pass |
| --- | --- | --- | --- | --- | --- | --- |
| arousal | 63 | 26096 | 0.5569435928877989 | 63 | True | True |

## Fold-Locality Audit

| fold | n_train_rows | n_val_rows | n_train_subjects | n_val_subjects | subject_overlap_count | pass |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1664 | 352 | 52 | 11 | 0 | True |
| 2 | 1664 | 352 | 52 | 11 | 0 | True |
| 3 | 1664 | 352 | 52 | 11 | 0 | True |
| 4 | 1696 | 320 | 53 | 10 | 0 | True |
| 5 | 1696 | 320 | 53 | 10 | 0 | True |
| 6 | 1696 | 320 | 53 | 10 | 0 | True |

## Matrix Guard Audit

| guard | expected | observed | pass |
| --- | --- | --- | --- |
| row_count | 96 | 96 | True |
| feature_set_scope | bandpower_only_control_v1,bandpower_temporal_stats_v1,current_summary_diff_control,robust_scaled_current_summary_diff_control | bandpower_only_control_v1,bandpower_temporal_stats_v1,current_summary_diff_control,robust_scaled_current_summary_diff_control | True |
| model_scope | logistic_regression_pairwise_feature_patch,majority_train_label_no_training,random_balanced_no_training,ridge_classifier_pairwise_feature_patch | logistic_regression_pairwise_feature_patch,majority_train_label_no_training,random_balanced_no_training,ridge_classifier_pairwise_feature_patch | True |
| modality_scope | EEG | EEG | True |
| task_scope | arousal | arousal | True |
| fold_scope | 1,2,3,4,5,6 | 1,2,3,4,5,6 | True |
| authorized_status | matrix_defined_not_yet_authorized_for_training | matrix_defined_not_yet_authorized_for_training | True |

## Smoke Decision Matrix

| requirement_id | check | status | evidence |
| --- | --- | --- | --- |
| SMOKE_001 | cache_index_window_alignment | pass | index_rows=2016 windows_shape=[2016, 32, 640] |
| SMOKE_002 | feature_matrices_finite_and_shaped | pass | docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_feature_shape_audit.csv |
| SMOKE_003 | pairwise_target_construction | pass | docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_pair_target_audit.csv |
| SMOKE_004 | fold_locality_subject_disjointness | pass | docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_fold_locality_audit.csv |
| SMOKE_005 | frozen_matrix_scope_guard | pass | docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_matrix_guard_audit.csv |
| SMOKE_006 | no_training_metrics_produced | pass | script performs no model fit/predict; smoke audits only |

## Interpretation

The smoke tests validate feature extraction, same-subject pair construction, fold-locality, and frozen matrix scope only.

No patch model training was run. No broad search, SupCon/DG, fusion, or final LOSO claim is authorized by this report.

## Next Allowed Step

`human_review_closeout_then_create_feature_patch_first_pass_objective`
