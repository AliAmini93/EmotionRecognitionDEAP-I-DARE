# ROCA-I-DARE EMG Augmented Probe

Strict LOSO. Train-only feature-space augmentation. Fixed config. No test tuning.

## Configuration

- feature_dim: `812`
- aug_copies: `2`
- aug_noise_std: `0.1`
- ridge_alpha: `100.0`
- ExtraTrees: `{"n_estimators": 200, "max_depth": 6, "min_samples_leaf": 8, "max_features": 0.5, "random_state": 11, "n_jobs": -1}`
- mean_features_kept_per_fold: `806.00`

## Main metrics

| target | model | n | mae | rmse | pearson | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse | lift_vs_stimulus_dev_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | stimulus_only | 2016 | 1.5799 | 1.9442 | 0.6344 | 0.7686 | 0.8161 | 1.9442 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| arousal | emg_expanded_ridge_residual_noaug | 2016 | 1.6359 | 2.0255 | 0.6013 | 0.7660 | 0.8116 | 2.0255 | 0.0323 | 0.5208 | 0.6343 | -0.0813 | -0.0026 | -0.0045 | -0.0813 |  |
| arousal | emg_expanded_ridge_residual_aug | 2016 | 1.6587 | 2.0532 | 0.5913 | 0.7597 | 0.8090 | 2.0532 | 0.0388 | 0.5109 | 0.7394 | -0.1090 | -0.0089 | -0.0071 | -0.1090 |  |
| arousal | emg_expanded_extratrees_residual_noaug | 2016 | 1.5996 | 1.9708 | 0.6223 | 0.7692 | 0.8176 | 1.9708 | -0.0285 | 0.4965 | 0.2717 | -0.0265 | 0.0006 | 0.0015 | -0.0265 |  |
| arousal | emg_expanded_extratrees_residual_aug | 2016 | 1.6012 | 1.9702 | 0.6225 | 0.7692 | 0.8187 | 1.9702 | -0.0370 | 0.4960 | 0.2548 | -0.0260 | 0.0006 | 0.0026 | -0.0260 |  |
| valence | stimulus_only | 2016 | 1.0221 | 1.2578 | 0.8663 | 0.8796 | 0.9433 | 1.2578 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| valence | emg_expanded_ridge_residual_noaug | 2016 | 1.0514 | 1.3126 | 0.8538 | 0.8749 | 0.9418 | 1.3126 | -0.0179 | 0.4881 | 0.3537 | -0.0549 | -0.0046 | -0.0015 | -0.0549 |  |
| valence | emg_expanded_ridge_residual_aug | 2016 | 1.0657 | 1.3309 | 0.8497 | 0.8757 | 0.9395 | 1.3309 | -0.0133 | 0.4881 | 0.4188 | -0.0731 | -0.0039 | -0.0038 | -0.0731 |  |
| valence | emg_expanded_extratrees_residual_noaug | 2016 | 1.0214 | 1.2637 | 0.8650 | 0.8796 | 0.9470 | 1.2637 | 0.0113 | 0.5149 | 0.1369 | -0.0059 | 0.0000 | 0.0037 | -0.0059 |  |
| valence | emg_expanded_extratrees_residual_aug | 2016 | 1.0226 | 1.2644 | 0.8648 | 0.8794 | 0.9470 | 1.2644 | 0.0110 | 0.5020 | 0.1433 | -0.0066 | -0.0002 | 0.0037 | -0.0066 |  |


## Fold-safe hard subset metrics

| target | subset | model | n | rmse | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse | lift_vs_stimulus_dev_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | top25_train_entropy | stimulus_only | 504 | 2.0764 | 0.6474 | 0.6232 | 2.0764 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| arousal | top25_train_entropy | emg_expanded_ridge_residual_noaug | 504 | 2.1677 | 0.6107 | 0.6453 | 2.1677 | 0.0141 | 0.5060 | 0.6531 | -0.0913 | -0.0367 | 0.0221 | -0.0913 |  |
| arousal | top25_train_entropy | emg_expanded_ridge_residual_aug | 504 | 2.1921 | 0.5985 | 0.6482 | 2.1921 | 0.0266 | 0.5079 | 0.7611 | -0.1157 | -0.0490 | 0.0249 | -0.1157 |  |
| arousal | top25_train_entropy | emg_expanded_extratrees_residual_noaug | 504 | 2.1147 | 0.6304 | 0.6409 | 2.1147 | -0.0725 | 0.4583 | 0.2779 | -0.0383 | -0.0171 | 0.0177 | -0.0383 |  |
| arousal | top25_train_entropy | emg_expanded_extratrees_residual_aug | 504 | 2.1128 | 0.6339 | 0.6433 | 2.1128 | -0.0746 | 0.4742 | 0.2649 | -0.0364 | -0.0135 | 0.0201 | -0.0364 |  |
| arousal | top25_train_score_std | stimulus_only | 504 | 2.2740 | 0.6498 | 0.6700 | 2.2740 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| arousal | top25_train_score_std | emg_expanded_ridge_residual_noaug | 504 | 2.3636 | 0.6484 | 0.6804 | 2.3636 | -0.0012 | 0.5099 | 0.6422 | -0.0896 | -0.0014 | 0.0104 | -0.0896 |  |
| arousal | top25_train_score_std | emg_expanded_ridge_residual_aug | 504 | 2.3953 | 0.6274 | 0.6750 | 2.3953 | -0.0017 | 0.5099 | 0.7481 | -0.1213 | -0.0224 | 0.0050 | -0.1213 |  |
| arousal | top25_train_score_std | emg_expanded_extratrees_residual_noaug | 504 | 2.3047 | 0.6516 | 0.6968 | 2.3047 | -0.0510 | 0.4921 | 0.2765 | -0.0307 | 0.0018 | 0.0268 | -0.0307 |  |
| arousal | top25_train_score_std | emg_expanded_extratrees_residual_aug | 504 | 2.2997 | 0.6520 | 0.6997 | 2.2997 | -0.0425 | 0.4861 | 0.2600 | -0.0257 | 0.0022 | 0.0297 | -0.0257 |  |
| valence | top25_train_entropy | stimulus_only | 504 | 1.3231 | 0.5038 | 0.6853 | 1.3231 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| valence | top25_train_entropy | emg_expanded_ridge_residual_noaug | 504 | 1.3742 | 0.5146 | 0.6838 | 1.3742 | -0.0121 | 0.4940 | 0.3562 | -0.0512 | 0.0108 | -0.0015 | -0.0512 |  |
| valence | top25_train_entropy | emg_expanded_ridge_residual_aug | 504 | 1.4008 | 0.5157 | 0.6716 | 1.4008 | -0.0220 | 0.4742 | 0.4333 | -0.0778 | 0.0119 | -0.0136 | -0.0778 |  |
| valence | top25_train_entropy | emg_expanded_extratrees_residual_noaug | 504 | 1.3260 | 0.5064 | 0.7264 | 1.3260 | 0.0297 | 0.5139 | 0.1292 | -0.0030 | 0.0027 | 0.0412 | -0.0030 |  |
| valence | top25_train_entropy | emg_expanded_extratrees_residual_aug | 504 | 1.3274 | 0.5049 | 0.7252 | 1.3274 | 0.0209 | 0.4921 | 0.1323 | -0.0043 | 0.0011 | 0.0400 | -0.0043 |  |
| valence | top25_train_score_std | stimulus_only | 504 | 1.2972 | 0.7381 | 0.8359 | 1.2972 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| valence | top25_train_score_std | emg_expanded_ridge_residual_noaug | 504 | 1.3518 | 0.7400 | 0.8501 | 1.3518 | -0.0089 | 0.5020 | 0.3691 | -0.0547 | 0.0019 | 0.0142 | -0.0547 |  |
| valence | top25_train_score_std | emg_expanded_ridge_residual_aug | 504 | 1.3856 | 0.7419 | 0.8421 | 1.3856 | -0.0332 | 0.4782 | 0.4461 | -0.0885 | 0.0038 | 0.0061 | -0.0885 |  |
| valence | top25_train_score_std | emg_expanded_extratrees_residual_noaug | 504 | 1.3046 | 0.7401 | 0.8563 | 1.3046 | -0.0053 | 0.5099 | 0.1316 | -0.0075 | 0.0020 | 0.0203 | -0.0075 |  |
| valence | top25_train_score_std | emg_expanded_extratrees_residual_aug | 504 | 1.3047 | 0.7401 | 0.8554 | 1.3047 | -0.0006 | 0.5060 | 0.1386 | -0.0076 | 0.0020 | 0.0194 | -0.0076 |  |


## Interpretation guide

- Compare `*_aug` directly against matching `*_noaug`.
- Positive `lift_vs_stimulus_rmse` means lower RMSE than stimulus-only.
- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.
- This is an exploratory augmentation smoke test, not a tuned final result.
