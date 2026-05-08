# I-DARE Alternative Pairwise Minimal First-Pass Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T17:05:28+00:00`

## Executive Result

Diagnosis: `alternative_pairwise_minimal_first_pass_weak_mixed_signal`

Recommended next objective: `label_semantics_alternative_pairwise_failure_or_metric_debug_objective`

Runs executed: `96`

Predictions written: `434800`

## Best Learned Cell

```json
{
  "model": "ridge_classifier_pairwise_summary_diff",
  "training_category": "minimal_classical_pairwise_baseline",
  "modality": "EEG",
  "task": "arousal",
  "n_runs": 6,
  "mean_balanced_accuracy": 0.5216709095350218,
  "std_balanced_accuracy": 0.018748839652001463,
  "min_balanced_accuracy": 0.5053943898345721,
  "max_balanced_accuracy": 0.5497501135847342,
  "mean_macro_f1": 0.5216709095350218,
  "mean_accuracy": 0.5216709095350218,
  "mean_pred_positive_rate": 0.5,
  "one_class_pred_count": 0,
  "folds_over_055_bal_acc": 0,
  "folds_under_045_bal_acc": 0,
  "mean_majority_baseline_bal_acc": 0.5,
  "delta_vs_majority_baseline_bal_acc": 0.02167090953502182,
  "mean_random_baseline_bal_acc": 0.501244141659629,
  "delta_vs_random_baseline_bal_acc": 0.02042676787539277
}
```

## Top Cells

| model | modality | task | n_runs | mean_balanced_accuracy | mean_macro_f1 | delta_vs_majority_baseline_bal_acc | folds_over_055_bal_acc | folds_under_045_bal_acc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ridge_classifier_pairwise_summary_diff | EEG | arousal | 6 | 0.5216709095350218 | 0.5216709095350218 | 0.02167090953502182 | 0 | 0 |
| logistic_regression_pairwise_summary_diff | EEG | arousal | 6 | 0.5212300585899118 | 0.5212300585899118 | 0.021230058589911782 | 0 | 0 |
| logistic_regression_pairwise_summary_diff | EEG | valence | 6 | 0.5144921704153708 | 0.5144921704153708 | 0.014492170415370764 | 0 | 0 |
| ridge_classifier_pairwise_summary_diff | EEG | valence | 6 | 0.514171467706751 | 0.514171467706751 | 0.01417146770675104 | 0 | 0 |
| ridge_classifier_pairwise_summary_diff | EMG | valence | 6 | 0.511954974495675 | 0.511954974495675 | 0.011954974495674953 | 0 | 0 |
| logistic_regression_pairwise_summary_diff | EMG | valence | 6 | 0.5110322609499353 | 0.5110322577557423 | 0.011032260949935258 | 0 | 0 |
| logistic_regression_pairwise_summary_diff | EMG | arousal | 6 | 0.5078025298608785 | 0.5078025298608785 | 0.007802529860878482 | 0 | 0 |
| ridge_classifier_pairwise_summary_diff | EMG | arousal | 6 | 0.5070697458002597 | 0.5070697458002597 | 0.0070697458002596525 | 0 | 0 |

## Pair Audit

| modality | task | kept_oriented_pairs | n_subjects | positive_rate | min_oriented_pairs_per_fold | feature_dim | leakage_guard_pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EEG | valence | 53508 | 63 | 0.5 | 8368 | 66 | True |
| EEG | arousal | 52192 | 63 | 0.5 | 8176 | 66 | True |
| EMG | valence | 53508 | 63 | 0.5 | 8368 | 22 | True |
| EMG | arousal | 52192 | 63 | 0.5 | 8176 | 22 | True |

## Interpretation

This run used only the frozen 96-row minimal first-pass matrix. It does not authorize broad model search, SupCon/DG, EEG+EMG fusion, or final LOSO claims.

The next step must be human review and a separate objective for confirmation, metric-debug, patch, or archive.

## Next Allowed Step

`human_review_closeout_before_next_pairwise_decision`
