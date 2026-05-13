# ROCA-I-DARE EEG Validation-Calibrated Smoke

This is a calibration diagnostic smoke run, not final full LOSO.

## Configuration

- target: `arousal`
- cache: `baseline_corrected`
- test_subjects: `[1, 2, 3, 5, 6, 7]`
- baseline: `stimulus_fit_only`
- uncalibrated model: `eeg_multitask_uncalibrated_inner`
- calibrated model: `eeg_multitask_val_affine_calibrated_inner`
- affine calibration: `pred_dev_cal = a * pred_dev + b`
- calibration ridge: `1e-06`
- max abs calibration slope: `20.0`
- loss: `HuberResidual + 0.25 * BCEHighLow`

## Main metrics

| target | model | n | mae | rmse | pearson | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | true_dev_std | pred_dev_std | lift_vs_stimulus_fit_only_rmse | lift_vs_stimulus_fit_only_balanced_accuracy | lift_vs_stimulus_fit_only_auroc | lift_vs_stimulus_fit_only_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | eeg_multitask_uncalibrated_inner | 192 | 1.9704 | 2.4496 | 0.4188 | 0.6234 | 0.6515 | 2.4496 | -0.0770 | 0.4688 | 2.2734 | 0.3493 | -0.0782 | -0.0046 | -0.0054 | -0.0782 |
| arousal | eeg_multitask_val_affine_calibrated_inner | 192 | 1.9946 | 2.4919 | 0.4146 | 0.6174 | 0.6441 | 2.4919 | -0.0846 | 0.4583 | 2.2734 | 0.3768 | -0.1205 | -0.0106 | -0.0128 | -0.1205 |
| arousal | stimulus_fit_only | 192 | 1.9303 | 2.3714 | 0.4445 | 0.6280 | 0.6568 | 2.3714 |  | 0.0000 | 2.2734 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Fold-safe hard subset metrics

| target | subset | model | n | rmse | balanced_accuracy | auroc | dev_rmse | dev_pearson | true_dev_std | pred_dev_std | lift_vs_stimulus_fit_only_rmse | lift_vs_stimulus_fit_only_balanced_accuracy | lift_vs_stimulus_fit_only_auroc | lift_vs_stimulus_fit_only_dev_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | top25_train_entropy | eeg_multitask_uncalibrated_inner | 48 | 2.0713 | 0.5979 | 0.5097 | 2.0713 | -0.1474 | 1.9467 | 0.4248 | -0.1163 | -0.0238 | -0.0705 | -0.1163 |
| arousal | top25_train_entropy | eeg_multitask_val_affine_calibrated_inner | 48 | 2.0683 | 0.5794 | 0.5820 | 2.0683 | -0.1329 | 1.9467 | 0.3945 | -0.1134 | -0.0423 | 0.0018 | -0.1134 |
| arousal | top25_train_entropy | stimulus_fit_only | 48 | 1.9549 | 0.6217 | 0.5802 | 1.9549 |  | 1.9467 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| arousal | top25_train_score_std | eeg_multitask_uncalibrated_inner | 48 | 2.5319 | 0.5979 | 0.6155 | 2.5319 | -0.1120 | 2.3514 | 0.3469 | -0.0880 | -0.0185 | -0.0414 | -0.0880 |
| arousal | top25_train_score_std | eeg_multitask_val_affine_calibrated_inner | 48 | 2.5828 | 0.5741 | 0.6226 | 2.5828 | -0.1531 | 2.3514 | 0.3759 | -0.1388 | -0.0423 | -0.0344 | -0.1388 |
| arousal | top25_train_score_std | stimulus_fit_only | 48 | 2.4439 | 0.6164 | 0.6570 | 2.4439 |  | 2.3514 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Fold summary

| test_subject | model | best_epoch | rmse | dev_rmse | dev_pearson | true_dev_std | pred_dev_std | calibration_a | calibration_b | val_uncal_dev_rmse | val_cal_dev_rmse | val_uncal_dev_pearson | val_cal_dev_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | stimulus_fit_only | 2 | 1.8841 | 1.8841 |  | 1.8834 | 0.0000 | 0.0836 | -0.3423 | 1.9682 | 1.9495 | 0.0091 | 0.0091 |
| 1 | eeg_multitask_uncalibrated_inner | 2 | 1.8527 | 1.8527 | 0.2814 | 1.8834 | 0.1964 | 0.0836 | -0.3423 | 1.9682 | 1.9495 | 0.0091 | 0.0091 |
| 1 | eeg_multitask_val_affine_calibrated_inner | 2 | 1.9233 | 1.9233 | 0.2814 | 1.8834 | 0.0164 | 0.0836 | -0.3423 | 1.9682 | 1.9495 | 0.0091 | 0.0091 |
| 2 | stimulus_fit_only | 4 | 2.6727 | 2.6727 |  | 1.5917 | 0.0000 | 0.2915 | -0.5331 | 1.7963 | 1.7321 | 0.0843 | 0.0843 |
| 2 | eeg_multitask_uncalibrated_inner | 4 | 2.9974 | 2.9974 | -0.0086 | 1.5917 | 0.4904 | 0.2915 | -0.5331 | 1.7963 | 1.7321 | 0.0843 | 0.0843 |
| 2 | eeg_multitask_val_affine_calibrated_inner | 4 | 3.2071 | 3.2071 | -0.0086 | 1.5917 | 0.1430 | 0.2915 | -0.5331 | 1.7963 | 1.7321 | 0.0843 | 0.0843 |
| 3 | stimulus_fit_only | 1 | 1.8847 | 1.8847 |  | 1.3389 | 0.0000 | -0.6881 | -0.4380 | 2.1454 | 2.0669 | -0.0489 | 0.0489 |
| 3 | eeg_multitask_uncalibrated_inner | 1 | 1.8762 | 1.8762 | 0.0545 | 1.3389 | 0.0627 | -0.6881 | -0.4380 | 2.1454 | 2.0669 | -0.0489 | 0.0489 |
| 3 | eeg_multitask_val_affine_calibrated_inner | 1 | 1.6132 | 1.6132 | -0.0545 | 1.3389 | 0.0431 | -0.6881 | -0.4380 | 2.1454 | 2.0669 | -0.0489 | 0.0489 |
| 5 | stimulus_fit_only | 3 | 1.7759 | 1.7759 |  | 1.4944 | 0.0000 | -0.2168 | 0.5351 | 2.2107 | 2.1350 | -0.0346 | 0.0346 |
| 5 | eeg_multitask_uncalibrated_inner | 3 | 1.6993 | 1.6993 | -0.0933 | 1.4944 | 0.3112 | -0.2168 | 0.5351 | 2.2107 | 2.1350 | -0.0346 | 0.0346 |
| 5 | eeg_multitask_val_affine_calibrated_inner | 3 | 1.5662 | 1.5662 | 0.0933 | 1.4944 | 0.0675 | -0.2168 | 0.5351 | 2.2107 | 2.1350 | -0.0346 | 0.0346 |
| 6 | stimulus_fit_only | 1 | 3.7182 | 3.7182 |  | 1.8093 | 0.0000 | 1.5209 | -0.0304 | 1.8042 | 1.8009 | 0.0956 | 0.0956 |
| 6 | eeg_multitask_uncalibrated_inner | 1 | 3.8528 | 3.8528 | -0.0533 | 1.8093 | 0.1119 | 1.5209 | -0.0304 | 1.8042 | 1.8009 | 0.0956 | 0.0956 |
| 6 | eeg_multitask_val_affine_calibrated_inner | 1 | 3.9515 | 3.9515 | -0.0533 | 1.8093 | 0.1702 | 1.5209 | -0.0304 | 1.8042 | 1.8009 | 0.0956 | 0.0956 |
| 7 | stimulus_fit_only | 3 | 1.5868 | 1.5868 |  | 1.2045 | 0.0000 | 0.3319 | 0.0866 | 1.7986 | 1.7803 | 0.0656 | 0.0656 |
| 7 | eeg_multitask_uncalibrated_inner | 3 | 1.5279 | 1.5279 | 0.0359 | 1.2045 | 0.3511 | 0.3319 | 0.0866 | 1.7986 | 1.7803 | 0.0656 | 0.0656 |
| 7 | eeg_multitask_val_affine_calibrated_inner | 3 | 1.6134 | 1.6134 | 0.0359 | 1.2045 | 0.1165 | 0.3319 | 0.0866 | 1.7986 | 1.7803 | 0.0656 | 0.0656 |


## Interpretation guide

- Positive `lift_vs_stimulus_fit_only_rmse` means lower RMSE than the fit-only stimulus baseline.
- This smoke uses fit-only stimulus means because validation subjects are reserved for calibration.
- If calibrated rows improve RMSE/dev_pearson over uncalibrated rows, the issue is likely calibration/scale.
- If calibration hurts, the next step should be residual-sign auxiliary or a different regression head/loss.
