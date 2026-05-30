# I-DARE 06a1 Previous-Model Deep Residual Probe

This run reuses the previous `EEGSegmentEncoder` backbone and replaces the binary classification head with a residual/deviation regression head.

## Decision

| target | decision | input_cache_policy | architecture | evaluation_subset | n_predictions_high | n_subjects | zero_residual_rmse_high | deep_model_residual_rmse_high | deep_lift_vs_zero_residual_rmse_high | deep_residual_pearson_high | deep_residual_sign_acc_high | fixed_reference_block | fixed_reference_model | fixed_reference_residual_rmse | fixed_reference_lift_vs_zero | fixed_reference_residual_pearson | deep_minus_fixed_lift | mean_subject_improvement_zero_minus_deep | ci95_low_mean_subject_improvement | ci95_high_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | wins_vs_zero | losses_vs_zero | win_margin_vs_zero | passes_06a1_gate | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_GO_PREVIOUS_DEEP_MODEL_UNDER_LOSO_HIGH_DISAGREEMENT | baseline_corrected | previous_EEGSegmentEncoder_lite_plus_residual_head | high_disagreement_q75 | 492 | 63 | 3.27531 | 3.33167 | -0.0563594 | 0.101419 | 0.563008 | eeg_bandpower | physio_eeg_bandpower_ridge | 3.16841 | 0.0717248 | 0.212972 | -0.128084 | 0.0421239 | -0.142597 | 0.219818 | 0.328067 | 35 | 28 | 7 | False | deep residual lift vs zero is <= 0.02; deep model does not beat fixed EEG-bandpower 05ajb reference; paired subject-level evidence is not stable |

## Fold metrics preview

| seed | test_subject | train_rows | val_rows | test_rows | high_threshold | threshold_source | best_epoch | best_monitor | test_high_n | test_all_model_rmse | test_high_zero_rmse | test_high_model_rmse | test_high_lift_vs_zero | test_high_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | 23 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 9 | 2.91308 | 4 | 1.95664 | 2.70056 | 0.792349 | 1.90821 | 0.60487 |
| 11 | 32 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 2 | 3.2896 | 2 | 1.53957 | 2.53183 | 1.00723 | 1.5246 |  |
| 11 | 33 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 9 | 2.98536 | 4 | 1.83308 | 3.07944 | 1.6389 | 1.44054 | -0.0144892 |
| 11 | 58 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 7 | 2.91831 | 5 | 1.27265 | 2.94421 | 1.68646 | 1.25775 | -0.583645 |
| 11 | 49 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 6 | 3.07338 | 14 | 1.86938 | 3.31445 | 2.35618 | 0.958274 | -0.0242548 |
| 11 | 3 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 5 | 3.28363 | 5 | 1.63758 | 3.20181 | 2.29417 | 0.907638 | -0.990736 |
| 11 | 18 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 2 | 3.15081 | 11 | 2.07993 | 3.30331 | 2.61643 | 0.68688 | 0.431523 |
| 11 | 27 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 6 | 3.17758 | 6 | 1.69124 | 2.86458 | 2.23368 | 0.630903 | 0.591821 |
| 11 | 30 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 5 | 2.31607 | 1 | 1.14146 | 2.48148 | 1.87958 | 0.601906 |  |
| 11 | 26 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 8 | 2.9675 | 11 | 2.25786 | 2.97804 | 2.38963 | 0.588412 | -0.0397178 |
| 11 | 65 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 2 | 3.23428 | 10 | 2.16786 | 2.8681 | 2.29129 | 0.576805 | 0.134447 |
| 11 | 5 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 1 | 3.27439 | 9 | 1.60414 | 2.8916 | 2.35438 | 0.537228 | -0.150923 |
| 11 | 37 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 5 | 2.90197 | 5 | 1.98505 | 2.99839 | 2.50431 | 0.494074 | 0.549736 |
| 11 | 21 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 3 | 3.27627 | 4 | 1.84029 | 3.18802 | 2.7167 | 0.47132 | 0.839216 |
| 11 | 31 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 1 | 2.97187 | 13 | 2.19472 | 3.33613 | 2.94307 | 0.39306 | -0.386057 |
| 11 | 17 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 2 | 2.91549 | 5 | 1.3887 | 2.74545 | 2.36191 | 0.38354 | 0.348663 |
| 11 | 35 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 3 | 2.32945 | 4 | 2.00557 | 3.27639 | 2.8996 | 0.376788 | -0.616634 |
| 11 | 24 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 2 | 2.97368 | 4 | 1.61833 | 2.36309 | 1.99145 | 0.371635 | 0.492688 |
| 11 | 6 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 3 | 2.73758 | 23 | 3.48928 | 4.3937 | 4.04528 | 0.348416 | -0.289999 |
| 11 | 45 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 2 | 3.48121 | 4 | 1.46743 | 3.28833 | 2.95937 | 0.328953 | 0.0098255 |
| 11 | 36 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 1 | 3.30657 | 5 | 1.54244 | 2.75151 | 2.45047 | 0.30103 | 0.302117 |
| 11 | 19 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 2 | 2.851 | 9 | 1.68101 | 3.1271 | 2.84395 | 0.283146 | -0.158661 |
| 11 | 60 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 5 | 2.9609 | 14 | 2.51838 | 3.33433 | 3.05712 | 0.277216 | -0.0777133 |
| 11 | 59 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 1 | 3.15871 | 9 | 1.9576 | 3.55817 | 3.32443 | 0.233741 | 0.258197 |
| 11 | 44 | 1728 | 256 | 32 | 2.20968 | 05ajb_confirmatory | 1 | 3.05418 | 11 | 2.36 | 3.77853 | 3.56108 | 0.217445 | 0.421272 |

## Subject stats preview

| subject_id | n | zero_residual_rmse | deep_model_residual_rmse | improvement_zero_minus_deep_rmse | residual_pearson |
| --- | --- | --- | --- | --- | --- |
| 23 | 4 | 2.70056 | 0.792349 | 1.90821 | 0.60487 |
| 32 | 2 | 2.53183 | 1.00723 | 1.5246 |  |
| 33 | 4 | 3.07944 | 1.6389 | 1.44054 | -0.0144892 |
| 58 | 5 | 2.94421 | 1.68646 | 1.25775 | -0.583645 |
| 49 | 14 | 3.31445 | 2.35618 | 0.958274 | -0.0242548 |
| 3 | 5 | 3.20181 | 2.29417 | 0.907638 | -0.990736 |
| 18 | 11 | 3.30331 | 2.61643 | 0.68688 | 0.431523 |
| 27 | 6 | 2.86458 | 2.23368 | 0.630903 | 0.591821 |
| 30 | 1 | 2.48148 | 1.87958 | 0.601906 |  |
| 26 | 11 | 2.97804 | 2.38963 | 0.588412 | -0.0397178 |
| 65 | 10 | 2.8681 | 2.29129 | 0.576805 | 0.134447 |
| 5 | 9 | 2.8916 | 2.35438 | 0.537228 | -0.150923 |
| 37 | 5 | 2.99839 | 2.50431 | 0.494074 | 0.549736 |
| 21 | 4 | 3.18802 | 2.7167 | 0.47132 | 0.839216 |
| 31 | 13 | 3.33613 | 2.94307 | 0.39306 | -0.386057 |
| 17 | 5 | 2.74545 | 2.36191 | 0.38354 | 0.348663 |
| 35 | 4 | 3.27639 | 2.8996 | 0.376788 | -0.616634 |
| 24 | 4 | 2.36309 | 1.99145 | 0.371635 | 0.492688 |
| 6 | 23 | 4.3937 | 4.04528 | 0.348416 | -0.289999 |
| 45 | 4 | 3.28833 | 2.95937 | 0.328953 | 0.0098255 |
| 36 | 5 | 2.75151 | 2.45047 | 0.30103 | 0.302117 |
| 19 | 9 | 3.1271 | 2.84395 | 0.283146 | -0.158661 |
| 60 | 14 | 3.33433 | 3.05712 | 0.277216 | -0.0777133 |
| 59 | 9 | 3.55817 | 3.32443 | 0.233741 | 0.258197 |
| 44 | 11 | 3.77853 | 3.56108 | 0.217445 | 0.421272 |

## Interpretation

The previous deep EEG backbone did not beat the fixed-feature high-disagreement reference under the current LOSO residual gate. This supports the hypothesis that the bottleneck is not merely architecture design.
