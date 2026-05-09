# I-DARE Alternative Pairwise Feature-Representation Patch First-Pass Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-09T01:08:56+00:00`

## Executive Result

Diagnosis: `feature_representation_patch_first_pass_no_actionable_signal`

Recommended next objective: `label_semantics_alternative_pairwise_feature_patch_archive_or_rethink_objective`

Runs executed: `96`

## Best Cell

| Metric | Value |
|---|---|
| feature_set_id | `bandpower_temporal_stats_v1` |
| model | `ridge_classifier_pairwise_feature_patch` |
| mean_balanced_accuracy | `0.516756` |
| delta_vs_majority_baseline_bal_acc | `0.016756` |
| delta_vs_random_baseline_bal_acc | `0.016160` |
| folds_over_055_bal_acc | `0` |
| folds_under_045_bal_acc | `0` |
| subject_positive_lift_fraction | `0.396825` |

## Top Cells

| feature_set_id | model | mean_balanced_accuracy | delta_vs_majority_baseline_bal_acc | folds_over_055_bal_acc | folds_under_045_bal_acc |
| --- | --- | --- | --- | --- | --- |
| bandpower_temporal_stats_v1 | ridge_classifier_pairwise_feature_patch | 0.5167558046828528 | 0.01675580468285276 | 0 | 0 |
| bandpower_temporal_stats_v1 | logistic_regression_pairwise_feature_patch | 0.5158489540815604 | 0.015848954081560396 | 0 | 0 |
| robust_scaled_current_summary_diff_control | ridge_classifier_pairwise_feature_patch | 0.514970469561589 | 0.014970469561588984 | 0 | 0 |
| robust_scaled_current_summary_diff_control | logistic_regression_pairwise_feature_patch | 0.5149498431018388 | 0.014949843101838778 | 0 | 0 |
| current_summary_diff_control | ridge_classifier_pairwise_feature_patch | 0.5149461011353417 | 0.014946101135341672 | 0 | 0 |
| current_summary_diff_control | logistic_regression_pairwise_feature_patch | 0.5146624836671729 | 0.014662483667172932 | 0 | 0 |
| current_summary_diff_control | random_balanced_no_training | 0.5021168971822413 | 0.002116897182241284 | 0 | 0 |
| bandpower_only_control_v1 | random_balanced_no_training | 0.5020190965141068 | 0.0020190965141068107 | 0 | 0 |

## Decision Matrix

| threshold_id | metric | observed | pass | decision |
| --- | --- | --- | --- | --- |
| T1_actionable_patch_signal | mean_balanced_accuracy | 0.5167558046828528 | False | candidate for narrow confirmation objective if also fold stability passes |
| T2_fold_stability | folds_over_055_bal_acc_and_no_folds_under_045 | folds_over_055=0; folds_under_045=0 | False | supports non-spurious patch signal |
| T3_control_lift | delta_vs_majority_baseline_bal_acc | 0.01675580468285276 | False | practical improvement over majority control |
| T4_subject_lift | subject_positive_lift_fraction | 0.3968253968253968 | False | supports broader subject-level lift |
| T5_archive_floor | mean_balanced_accuracy_below_053_or_no_improvement | mean_bal=0.5167558046828528; delta=0.01675580468285276 | False | archive patch branch or redesign representation if floor fails |

## Pair Audit

| fold | n_train_pairs | n_val_pairs | train_positive_rate | val_positive_rate | n_val_subjects |
| --- | --- | --- | --- | --- | --- |
| 1 | 21694 | 4402 | 0.561076795427307 | 0.5365742844161745 | 11 |
| 2 | 21418 | 4678 | 0.5564011579045662 | 0.5594271056006841 | 11 |
| 3 | 21478 | 4618 | 0.5567091907998882 | 0.5580337808575141 | 11 |
| 4 | 21925 | 4171 | 0.5601368301026226 | 0.5401582354351474 | 10 |
| 5 | 22008 | 4088 | 0.5522082878953108 | 0.5824363992172211 | 10 |
| 6 | 21957 | 4139 | 0.5551760258687435 | 0.5663203672384634 | 10 |

## Interpretation

This was a limited first-pass run of the frozen 96-row feature patch matrix.

It does not authorize broad search, SupCon/DG, fusion, or a final LOSO claim.

## Next Allowed Step

`human_review_closeout_then_archive_or_rethink_feature_patch`
