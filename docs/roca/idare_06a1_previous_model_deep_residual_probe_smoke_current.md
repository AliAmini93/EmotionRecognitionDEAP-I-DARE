# I-DARE 06a1 Previous-Model Deep Residual Probe

This run reuses the previous `EEGSegmentEncoder` backbone and replaces the binary classification head with a residual/deviation regression head.

## Decision

| target | decision | input_cache_policy | architecture | evaluation_subset | n_predictions_high | n_subjects | zero_residual_rmse_high | deep_model_residual_rmse_high | deep_lift_vs_zero_residual_rmse_high | deep_residual_pearson_high | deep_residual_sign_acc_high | fixed_reference_block | fixed_reference_model | fixed_reference_residual_rmse | fixed_reference_lift_vs_zero | fixed_reference_residual_pearson | deep_minus_fixed_lift | mean_subject_improvement_zero_minus_deep | ci95_low_mean_subject_improvement | ci95_high_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | wins_vs_zero | losses_vs_zero | win_margin_vs_zero | passes_06a1_gate | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_GO_PREVIOUS_DEEP_MODEL_UNDER_LOSO_HIGH_DISAGREEMENT | baseline_corrected | previous_EEGSegmentEncoder_lite_plus_residual_head | high_disagreement_q75 | 39 | 4 | 3.26683 | 3.27864 | -0.0118038 | 0.171155 | 0.410256 | eeg_bandpower | physio_eeg_bandpower_ridge | 3.16841 | 0.0717248 | 0.212972 | -0.0835286 | 0.0665258 | -0.161588 | 0.386707 | 0.430057 | 2 | 2 | 0 | False | deep residual lift vs zero is <= 0.02; deep model does not beat fixed EEG-bandpower 05ajb reference; paired subject-level evidence is not stable |

## Fold metrics preview

| seed | test_subject | train_rows | val_rows | test_rows | high_threshold | threshold_source | best_epoch | best_monitor | test_high_n | test_all_model_rmse | test_high_zero_rmse | test_high_model_rmse | test_high_lift_vs_zero | test_high_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | 5 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 1 | 3.27439 | 9 | 1.60414 | 2.8916 | 2.35437 | 0.537231 | -0.150903 |
| 11 | 3 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 1 | 3.33989 | 5 | 1.81595 | 3.20181 | 3.18802 | 0.0137846 | 0.884909 |
| 11 | 1 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 1 | 3.07939 | 10 | 1.87647 | 2.9691 | 3.03396 | -0.0648668 | 0.751933 |
| 11 | 2 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 1 | 3.27243 | 15 | 2.91733 | 3.66561 | 3.88565 | -0.220046 | -0.581539 |

## Subject stats preview

| subject_id | n | zero_residual_rmse | deep_model_residual_rmse | improvement_zero_minus_deep_rmse | residual_pearson |
| --- | --- | --- | --- | --- | --- |
| 5 | 9 | 2.8916 | 2.35437 | 0.537231 | -0.150903 |
| 3 | 5 | 3.20181 | 3.18802 | 0.0137846 | 0.884909 |
| 1 | 10 | 2.9691 | 3.03396 | -0.0648668 | 0.751933 |
| 2 | 15 | 3.66561 | 3.88565 | -0.220046 | -0.581539 |

## Interpretation

The previous deep EEG backbone did not beat the fixed-feature high-disagreement reference under the current LOSO residual gate. This supports the hypothesis that the bottleneck is not merely architecture design.
