# I-DARE Residual Physiology Feature Audit

This audit asks whether EEG/EMG feature blocks add cross-subject residual value beyond stimulus-only prior.

## Leakage control

- Outer protocol: leave-one-subject-out.
- Test-subject stimulus prior is computed from train subjects only.
- Physiological models predict residual/deviation over train-subject stimulus mean.
- Ridge alpha is selected using inner validation subjects only.

## Feature blocks

| block | shape | feature_dim | feature_names_preview |
| --- | --- | --- | --- |
| emg_existing_22 | [128, 22] | 22 | [emg_existing_22_f0000, emg_existing_22_f0001, emg_existing_22_f0002, emg_existing_22_f0003, emg_existing_22_f0004, emg_existing_22_f0005, emg_existing_22_f0006, emg_existing_22_f0007, ...] |
| eeg_entropy_complexity | [128, 192] | 192 | [eeg_log_activity_ch00, eeg_log_activity_ch01, eeg_log_activity_ch02, eeg_log_activity_ch03, eeg_log_activity_ch04, eeg_log_activity_ch05, eeg_log_activity_ch06, eeg_log_activity_ch07, ...] |
| emg_lagged_interaction_experimental | [128, 6] | 6 | [emg_env_corr_lag0, emg_env_corr_max, emg_env_corr_lag_at_max_scaled, emg_env_lead_lag_asym, emg_burst_coactivation_fraction, emg_burst_xor_fraction] |


## Main metrics

| target | model | n | mae | rmse | pearson | spearman | ccc | dev_rmse | dev_pearson | dev_sign_acc | true_dev_std | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_dev_rmse | lift_vs_stimulus_dev_pearson | lift_vs_stimulus_pred_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | physio_eeg_entropy_complexity_ridge | 128 | 2.5611 | 3.1708 | 0.1351 | 0.1317 | 0.1213 | 3.8703 | -0.2556 | 0.5159 | 2.4979 | 2.0621 | -0.6729 | -1.3724 |  | 2.0621 |
| arousal | physio_emg_existing_22_ridge | 128 | 2.1392 | 2.5498 | 0.3136 | 0.3180 | 0.2948 | 2.5498 | -0.0153 | 0.4048 | 2.4979 | 0.3921 | -0.0518 | -0.0518 |  | 0.3921 |
| arousal | physio_emg_lagged_interaction_experimental_ridge | 128 | 2.1830 | 2.6218 | 0.2965 | 0.3049 | 0.2847 | 2.6386 | -0.1091 | 0.4762 | 2.4979 | 0.5892 | -0.1239 | -0.1407 |  | 0.5892 |
| arousal | stimulus_only | 128 | 2.0990 | 2.4979 | 0.3217 | 0.3217 | 0.3014 | 2.4979 |  | 0.0000 | 2.4979 | 0.0000 | 0.0000 | 0.0000 |  | 0.0000 |
| valence | physio_eeg_entropy_complexity_ridge | 128 | 1.3390 | 1.7153 | 0.7992 | 0.7788 | 0.7902 | 1.8449 | 0.1046 | 0.5667 | 1.5298 | 1.0882 | -0.1855 | -0.3151 |  | 1.0882 |
| valence | physio_emg_existing_22_ridge | 128 | 1.3053 | 1.6458 | 0.8058 | 0.8001 | 0.8028 | 1.6656 | 0.0231 | 0.4833 | 1.5298 | 0.6933 | -0.1160 | -0.1359 |  | 0.6933 |
| valence | physio_emg_lagged_interaction_experimental_ridge | 128 | 1.3983 | 1.9280 | 0.7498 | 0.7156 | 0.7480 | 2.7671 | -0.0873 | 0.4583 | 1.5298 | 2.1664 | -0.3982 | -1.2373 |  | 2.1664 |
| valence | stimulus_only | 128 | 1.2240 | 1.5298 | 0.8324 | 0.8089 | 0.8294 | 1.5298 |  | 0.0000 | 1.5298 | 0.0000 | 0.0000 | 0.0000 |  | 0.0000 |


## Subject win/loss vs stimulus-only

| target | model | subjects | rmse_wins | rmse_losses | mean_delta_rmse_model_minus_stimulus | median_delta_rmse_model_minus_stimulus | worst_regression_delta_rmse | best_gain_delta_rmse | dev_rmse_wins | dev_rmse_losses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | physio_eeg_entropy_complexity_ridge | 4 | 1 | 3 | 0.4990 | 0.1612 | 2.1230 | -0.4491 | 1 | 3 |
| arousal | physio_emg_existing_22_ridge | 4 | 2 | 2 | 0.0476 | 0.0395 | 0.1207 | -0.0094 | 2 | 2 |
| arousal | physio_emg_lagged_interaction_experimental_ridge | 4 | 1 | 3 | 0.1181 | 0.1184 | 0.2860 | -0.0506 | 1 | 3 |
| valence | physio_eeg_entropy_complexity_ridge | 4 | 2 | 2 | 0.1528 | -0.0088 | 0.6996 | -0.0706 | 2 | 2 |
| valence | physio_emg_existing_22_ridge | 4 | 0 | 4 | 0.1124 | 0.1021 | 0.2362 | 0.0094 | 0 | 4 |
| valence | physio_emg_lagged_interaction_experimental_ridge | 4 | 1 | 3 | 0.3167 | 0.0059 | 1.2561 | -0.0012 | 1 | 3 |


## Interpretation

- Positive `lift_vs_stimulus_rmse` means the physiological block reduced score RMSE beyond stimulus-only.
- Positive `lift_vs_stimulus_dev_rmse` means the block improved residual/deviation RMSE.
- `dev_pearson` is central: it tests whether the block tracks subject-specific residual variation.
- Experimental directed/lagged features are not causal claims; they are exploratory directed-dynamics summaries.
