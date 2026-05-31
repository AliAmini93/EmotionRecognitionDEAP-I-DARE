# ROCA-I-DARE Expanded EMG Probe

Strict LOSO. Expanded EMG features. Fixed hyperparameters. No test tuning.

## Configuration

- feature_dim: `812`
- ridge_alpha: `100.0`
- ExtraTrees: `{"n_estimators": 300, "max_depth": 6, "min_samples_leaf": 8, "max_features": 0.5, "random_state": 11, "n_jobs": -1}`
- mean_features_kept_per_fold: `806.00`

## Main metrics

| target | model | n | mae | rmse | pearson | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse | lift_vs_stimulus_dev_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | stimulus_only | 2016 | 1.5799 | 1.9442 | 0.6344 | 0.7686 | 0.8161 | 1.9442 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| arousal | emg_expanded_ridge_direct | 2016 | 2.2302 | 2.5999 | 0.0487 | 0.5223 | 0.5290 | 2.5999 | 0.0327 | 0.4425 | 1.7909 | -0.6557 | -0.2463 | -0.2870 | -0.6557 |  |
| arousal | emg_expanded_ridge_residual | 2016 | 1.6359 | 2.0255 | 0.6013 | 0.7660 | 0.8116 | 2.0255 | 0.0323 | 0.5208 | 0.6343 | -0.0813 | -0.0026 | -0.0045 | -0.0813 |  |
| arousal | emg_expanded_extratrees_direct | 2016 | 2.2048 | 2.5514 | -0.0318 | 0.5062 | 0.4920 | 2.5514 | 0.0057 | 0.4306 | 1.6631 | -0.6072 | -0.2624 | -0.3241 | -0.6072 |  |
| arousal | emg_expanded_extratrees_residual | 2016 | 1.6010 | 1.9722 | 0.6216 | 0.7696 | 0.8170 | 1.9722 | -0.0323 | 0.5000 | 0.2740 | -0.0279 | 0.0010 | 0.0009 | -0.0279 |  |
| valence | stimulus_only | 2016 | 1.0221 | 1.2578 | 0.8663 | 0.8796 | 0.9433 | 1.2578 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| valence | emg_expanded_ridge_direct | 2016 | 2.1898 | 2.6222 | -0.0095 | 0.5065 | 0.4965 | 2.6222 | 0.0041 | 0.4965 | 2.3059 | -1.3644 | -0.3731 | -0.4468 | -1.3644 |  |
| valence | emg_expanded_ridge_residual | 2016 | 1.0514 | 1.3126 | 0.8538 | 0.8749 | 0.9418 | 1.3126 | -0.0179 | 0.4881 | 0.3537 | -0.0549 | -0.0046 | -0.0015 | -0.0549 |  |
| valence | emg_expanded_extratrees_direct | 2016 | 2.1267 | 2.5374 | -0.0466 | 0.4860 | 0.4829 | 2.5374 | 0.0067 | 0.5079 | 2.2121 | -1.2796 | -0.3936 | -0.4604 | -1.2796 |  |
| valence | emg_expanded_extratrees_residual | 2016 | 1.0209 | 1.2631 | 0.8651 | 0.8796 | 0.9472 | 1.2631 | 0.0170 | 0.5124 | 0.1388 | -0.0053 | 0.0000 | 0.0039 | -0.0053 |  |


## Fold-safe hard subset metrics

| target | subset | model | n | rmse | balanced_accuracy | auroc | dev_rmse | dev_pearson | dev_sign_acc | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_balanced_accuracy | lift_vs_stimulus_auroc | lift_vs_stimulus_dev_rmse | lift_vs_stimulus_dev_pearson |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | top25_train_entropy | stimulus_only | 504 | 2.0764 | 0.6474 | 0.6232 | 2.0764 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| arousal | top25_train_entropy | emg_expanded_ridge_direct | 504 | 2.7544 | 0.5372 | 0.5372 | 2.7544 | 0.0214 | 0.4325 | 1.1060 | -0.6780 | -0.1103 | -0.0860 | -0.6780 |  |
| arousal | top25_train_entropy | emg_expanded_ridge_residual | 504 | 2.1677 | 0.6107 | 0.6453 | 2.1677 | 0.0141 | 0.5060 | 0.6531 | -0.0913 | -0.0367 | 0.0221 | -0.0913 |  |
| arousal | top25_train_entropy | emg_expanded_extratrees_direct | 504 | 2.7187 | 0.5142 | 0.4777 | 2.7187 | -0.0613 | 0.4365 | 0.8793 | -0.6423 | -0.1332 | -0.1455 | -0.6423 |  |
| arousal | top25_train_entropy | emg_expanded_extratrees_residual | 504 | 2.1118 | 0.6339 | 0.6428 | 2.1118 | -0.0595 | 0.4782 | 0.2811 | -0.0354 | -0.0135 | 0.0196 | -0.0354 |  |
| arousal | top25_train_score_std | stimulus_only | 504 | 2.2740 | 0.6498 | 0.6700 | 2.2740 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| arousal | top25_train_score_std | emg_expanded_ridge_direct | 504 | 2.5657 | 0.5073 | 0.4833 | 2.5657 | 0.0473 | 0.4385 | 1.3004 | -0.2917 | -0.1425 | -0.1867 | -0.2917 |  |
| arousal | top25_train_score_std | emg_expanded_ridge_residual | 504 | 2.3636 | 0.6484 | 0.6804 | 2.3636 | -0.0012 | 0.5099 | 0.6422 | -0.0896 | -0.0014 | 0.0104 | -0.0896 |  |
| arousal | top25_train_score_std | emg_expanded_extratrees_direct | 504 | 2.4995 | 0.5130 | 0.4802 | 2.4995 | 0.0158 | 0.4306 | 1.0743 | -0.2255 | -0.1368 | -0.1898 | -0.2255 |  |
| arousal | top25_train_score_std | emg_expanded_extratrees_residual | 504 | 2.3035 | 0.6520 | 0.6977 | 2.3035 | -0.0475 | 0.4901 | 0.2752 | -0.0295 | 0.0022 | 0.0277 | -0.0295 |  |
| valence | top25_train_entropy | stimulus_only | 504 | 1.3231 | 0.5038 | 0.6853 | 1.3231 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| valence | top25_train_entropy | emg_expanded_ridge_direct | 504 | 2.0184 | 0.4604 | 0.4555 | 2.0184 | -0.0132 | 0.5079 | 0.8794 | -0.6953 | -0.0434 | -0.2297 | -0.6953 |  |
| valence | top25_train_entropy | emg_expanded_ridge_residual | 504 | 1.3742 | 0.5146 | 0.6838 | 1.3742 | -0.0121 | 0.4940 | 0.3562 | -0.0512 | 0.0108 | -0.0015 | -0.0512 |  |
| valence | top25_train_entropy | emg_expanded_extratrees_direct | 504 | 1.9338 | 0.4651 | 0.4500 | 1.9338 | 0.0070 | 0.5397 | 0.5452 | -0.6107 | -0.0387 | -0.2352 | -0.6107 |  |
| valence | top25_train_entropy | emg_expanded_extratrees_residual | 504 | 1.3256 | 0.5038 | 0.7286 | 1.3256 | 0.0335 | 0.5079 | 0.1315 | -0.0026 | 0.0000 | 0.0433 | -0.0026 |  |
| valence | top25_train_score_std | stimulus_only | 504 | 1.2972 | 0.7381 | 0.8359 | 1.2972 |  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  |
| valence | top25_train_score_std | emg_expanded_ridge_direct | 504 | 2.1480 | 0.4956 | 0.4900 | 2.1480 | -0.0192 | 0.4861 | 1.5770 | -0.8509 | -0.2425 | -0.3460 | -0.8509 |  |
| valence | top25_train_score_std | emg_expanded_ridge_residual | 504 | 1.3518 | 0.7400 | 0.8501 | 1.3518 | -0.0089 | 0.5020 | 0.3691 | -0.0547 | 0.0019 | 0.0142 | -0.0547 |  |
| valence | top25_train_score_std | emg_expanded_extratrees_direct | 504 | 2.0569 | 0.4720 | 0.4541 | 2.0569 | -0.0100 | 0.5159 | 1.4419 | -0.7598 | -0.2660 | -0.3818 | -0.7598 |  |
| valence | top25_train_score_std | emg_expanded_extratrees_residual | 504 | 1.3048 | 0.7381 | 0.8553 | 1.3048 | -0.0040 | 0.5139 | 0.1351 | -0.0076 | 0.0000 | 0.0193 | -0.0076 |  |


## Interpretation guide

- Positive `lift_vs_stimulus_rmse` means lower RMSE than stimulus-only.
- Positive `lift_vs_stimulus_auroc` means better high/low ranking than stimulus-only.
- `dev_pearson` is read directly because stimulus-only predicted deviation is constant zero.
- Residual models are more important than direct models for ROCA.
