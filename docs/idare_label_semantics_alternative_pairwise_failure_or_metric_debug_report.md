# I-DARE Alternative Pairwise Failure-or-Metric-Debug Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-09T00:37:12+00:00`

## Executive Diagnosis

Diagnosis: `alternative_pairwise_metric_debug_weak_but_consistent_signal`

Recommendation: `create_narrow_feature_representation_patch_or_confirmation_design_after_review`

Recommended next objective: `label_semantics_alternative_pairwise_feature_representation_patch_objective`

Decision reason: Best cell is consistently weak-positive but below confirmation threshold; summary features may be limiting.

## Best Cell Debug

Best cell: `ridge_classifier_pairwise_summary_diff` / `EEG` / `arousal`

- Mean balanced accuracy: `0.521671`
- Delta vs majority baseline: `0.021671`
- Folds over 0.55: `0`
- Positive-delta folds vs majority: `6` / `6`
- Subject positive-lift fraction: `0.603175`

## Top Cell Audit

| model | modality | task | mean_balanced_accuracy | delta_vs_majority_baseline_bal_acc | folds_over_055_bal_acc | weak_positive_signal | cell_decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ridge_classifier_pairwise_summary_diff | EEG | arousal | 0.5216709095350218 | 0.0216709095350218 | 0 | True | weak_positive_below_confirmation_threshold |
| logistic_regression_pairwise_summary_diff | EEG | arousal | 0.5212300585899118 | 0.0212300585899117 | 0 | True | weak_positive_below_confirmation_threshold |
| logistic_regression_pairwise_summary_diff | EEG | valence | 0.5144921704153708 | 0.0144921704153707 | 0 | False | near_chance |
| ridge_classifier_pairwise_summary_diff | EEG | valence | 0.514171467706751 | 0.014171467706751 | 0 | False | near_chance |
| ridge_classifier_pairwise_summary_diff | EMG | valence | 0.511954974495675 | 0.0119549744956749 | 0 | False | near_chance |
| logistic_regression_pairwise_summary_diff | EMG | valence | 0.5110322609499353 | 0.0110322609499352 | 0 | False | near_chance |
| logistic_regression_pairwise_summary_diff | EMG | arousal | 0.5078025298608785 | 0.0078025298608784 | 0 | False | near_chance |
| ridge_classifier_pairwise_summary_diff | EMG | arousal | 0.5070697458002597 | 0.0070697458002596 | 0 | False | near_chance |

## Best-Cell Fold Audit

| fold | balanced_accuracy | macro_f1 | delta_vs_majority_bal_acc | delta_vs_random_bal_acc |
| --- | --- | --- | --- | --- |
| 1 | 0.5497501135847342 | 0.5497501135847342 | 0.049750113584734246 | 0.039300318037255866 |
| 2 | 0.5451047456177853 | 0.5451047456177853 | 0.045104745617785325 | 0.04948696023941851 |
| 3 | 0.505413598960589 | 0.505413598960589 | 0.005413598960589017 | 0.010827197921178033 |
| 4 | 0.5053943898345721 | 0.5053943898345721 | 0.0053943898345720775 | -0.0015583792855429213 |
| 5 | 0.5066046966731899 | 0.5066046966731899 | 0.006604696673189858 | 0.008317025440313153 |
| 6 | 0.5177579125392607 | 0.5177579125392607 | 0.017757912539260734 | 0.016187484899734206 |

## Metric Alignment

| metric | value | threshold_or_context | status |
| --- | --- | --- | --- |
| mean_balanced_accuracy | 0.5216709095350218 | actionable >= 0.55 | below_actionable_threshold |
| delta_vs_majority_baseline_bal_acc | 0.02167090953502182 | positive but should be practically meaningful | positive_but_small |
| folds_over_055_bal_acc | 0 | confirmation candidate requires >= 3 | not_met |
| fold_positive_delta_count | 6 | majority of folds positive supports weak signal | weak_support |
| subject_positive_lift_fraction | 0.6031746031746031 | broad subject lift would support generality | to_review_below_or_near_mixed |

## Decision Matrix

| decision_id | option | status | rationale |
| --- | --- | --- | --- |
| D1 | narrow confirmation | not_selected | Requires mean balanced accuracy >= 0.55 and at least 3 folds over 0.55. |
| D2 | narrow feature/representation patch | selected | Weak-positive signal is present but below confirmation threshold; avoid broad search. |
| D3 | archive or patch | not_selected | Marginal signal without enough stability. |
| D4 | archive closeout | not_selected | No actionable signal beyond controls. |
| D5 | broad training / SupCon / fusion | blocked | Not authorized by evidence; would be premature. |

## Interpretation

The pairwise label formulation remains healthier than the archived global/ordinal branch, but the first-pass signal is not strong enough for a final claim or broad model search.

The best cell is weak-positive, with small lift over controls and no fold reaching the predeclared actionable threshold. This points more toward a narrow feature/representation patch or patch-vs-archive decision than toward immediate confirmation.

## Next Allowed Step

`human_review_closeout_before_pairwise_patch_or_archive`
