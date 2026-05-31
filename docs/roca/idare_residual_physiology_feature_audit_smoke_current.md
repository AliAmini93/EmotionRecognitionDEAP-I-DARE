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
| emg_existing_22 | [256, 22] | 22 | [emg_existing_22_f0000, emg_existing_22_f0001, emg_existing_22_f0002, emg_existing_22_f0003, emg_existing_22_f0004, emg_existing_22_f0005, emg_existing_22_f0006, emg_existing_22_f0007, ...] |
| emg_bsl_stats_22 | [256, 22] | 22 | [emg_bsl_stats_22_f0000, emg_bsl_stats_22_f0001, emg_bsl_stats_22_f0002, emg_bsl_stats_22_f0003, emg_bsl_stats_22_f0004, emg_bsl_stats_22_f0005, emg_bsl_stats_22_f0006, emg_bsl_stats_22_f0007, ...] |
| eeg_bandpower | [256, 330] | 330 | [eeg_delta_logpower_ch00, eeg_delta_logpower_ch01, eeg_delta_logpower_ch02, eeg_delta_logpower_ch03, eeg_delta_logpower_ch04, eeg_delta_logpower_ch05, eeg_delta_logpower_ch06, eeg_delta_logpower_ch07, ...] |
| eeg_entropy_complexity | [256, 192] | 192 | [eeg_log_activity_ch00, eeg_log_activity_ch01, eeg_log_activity_ch02, eeg_log_activity_ch03, eeg_log_activity_ch04, eeg_log_activity_ch05, eeg_log_activity_ch06, eeg_log_activity_ch07, ...] |
| emg_lagged_interaction_experimental | [256, 6] | 6 | [emg_env_corr_lag0, emg_env_corr_max, emg_env_corr_lag_at_max_scaled, emg_env_lead_lag_asym, emg_burst_coactivation_fraction, emg_burst_xor_fraction] |


## Main metrics

| target | model | n | mae | rmse | pearson | spearman | ccc | dev_rmse | dev_pearson | dev_sign_acc | true_dev_std | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_dev_rmse | lift_vs_stimulus_dev_pearson | lift_vs_stimulus_pred_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | physio_eeg_bandpower_ridge | 256 | 2.6223 | 3.2008 | 0.0675 | 0.0738 | 0.0610 | 3.4611 | -0.1886 | 0.4648 | 2.4114 | 1.8364 | -0.7894 | -1.0496 |  | 1.8364 |
| arousal | physio_eeg_entropy_complexity_ridge | 256 | 2.2295 | 2.6056 | 0.3005 | 0.3135 | 0.2836 | 2.6827 | 0.1089 | 0.4531 | 2.4114 | 1.4326 | -0.1941 | -0.2713 |  | 1.4326 |
| arousal | physio_emg_bsl_stats_22_ridge | 256 | 2.1715 | 2.6003 | 0.2953 | 0.2942 | 0.2764 | 2.6158 | 0.0612 | 0.5547 | 2.4114 | 1.1259 | -0.1888 | -0.2043 |  | 1.1259 |
| arousal | physio_emg_existing_22_ridge | 256 | 2.1387 | 2.5751 | 0.2911 | 0.2958 | 0.2724 | 2.5814 | 0.0718 | 0.5039 | 2.4114 | 1.1068 | -0.1637 | -0.1699 |  | 1.1068 |
| arousal | physio_emg_lagged_interaction_experimental_ridge | 256 | 2.2262 | 2.6120 | 0.2144 | 0.2374 | 0.1881 | 2.6147 | -0.1935 | 0.5469 | 2.4114 | 0.6260 | -0.2006 | -0.2033 |  | 0.6260 |
| arousal | stimulus_only | 256 | 2.0391 | 2.4114 | 0.3202 | 0.3210 | 0.2675 | 2.4114 |  | 0.0000 | 2.4114 | 0.0000 | 0.0000 | 0.0000 |  | 0.0000 |
| valence | physio_eeg_bandpower_ridge | 256 | 1.1916 | 1.5608 | 0.8208 | 0.7971 | 0.8181 | 1.6595 | -0.0679 | 0.5394 | 1.2899 | 0.9475 | -0.2709 | -0.3695 |  | 0.9475 |
| valence | physio_eeg_entropy_complexity_ridge | 256 | 1.1438 | 1.4637 | 0.8402 | 0.8122 | 0.8374 | 1.4992 | -0.0868 | 0.5354 | 1.2899 | 0.6593 | -0.1738 | -0.2092 |  | 0.6593 |
| valence | physio_emg_bsl_stats_22_ridge | 256 | 1.0448 | 1.3243 | 0.8696 | 0.8444 | 0.8660 | 1.3249 | 0.0251 | 0.5315 | 1.2899 | 0.3313 | -0.0344 | -0.0349 |  | 0.3313 |
| valence | physio_emg_existing_22_ridge | 256 | 1.1022 | 1.3605 | 0.8637 | 0.8302 | 0.8586 | 1.3605 | -0.1850 | 0.3858 | 1.2899 | 0.2298 | -0.0706 | -0.0706 |  | 0.2298 |
| valence | physio_emg_lagged_interaction_experimental_ridge | 256 | 1.0467 | 1.3131 | 0.8716 | 0.8412 | 0.8679 | 1.3174 | 0.0119 | 0.5591 | 1.2899 | 0.2830 | -0.0232 | -0.0274 |  | 0.2830 |
| valence | stimulus_only | 256 | 1.0368 | 1.2899 | 0.8760 | 0.8418 | 0.8720 | 1.2899 |  | 0.0000 | 1.2899 | 0.0000 | 0.0000 | 0.0000 |  | 0.0000 |


## Subject win/loss vs stimulus-only

| target | model | subjects | rmse_wins | rmse_losses | mean_delta_rmse_model_minus_stimulus | median_delta_rmse_model_minus_stimulus | worst_regression_delta_rmse | best_gain_delta_rmse | dev_rmse_wins | dev_rmse_losses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | physio_eeg_bandpower_ridge | 8 | 1 | 7 | 0.7067 | 0.3579 | 2.3115 | -0.3440 | 1 | 7 |
| arousal | physio_eeg_entropy_complexity_ridge | 8 | 1 | 7 | 0.2068 | 0.0919 | 0.7426 | -0.0962 | 0 | 8 |
| arousal | physio_emg_bsl_stats_22_ridge | 8 | 4 | 4 | 0.1994 | -0.0086 | 1.0189 | -0.2877 | 4 | 4 |
| arousal | physio_emg_existing_22_ridge | 8 | 4 | 4 | 0.1369 | 0.0079 | 0.8427 | -0.9407 | 4 | 4 |
| arousal | physio_emg_lagged_interaction_experimental_ridge | 8 | 5 | 3 | 0.1900 | -0.0143 | 1.4232 | -0.0595 | 5 | 3 |
| valence | physio_eeg_bandpower_ridge | 8 | 4 | 4 | 0.2144 | -0.0073 | 1.1043 | -0.0653 | 4 | 4 |
| valence | physio_eeg_entropy_complexity_ridge | 8 | 3 | 5 | 0.1464 | 0.0227 | 0.7164 | -0.0731 | 3 | 5 |
| valence | physio_emg_bsl_stats_22_ridge | 8 | 4 | 4 | 0.0305 | 0.0036 | 0.2850 | -0.0635 | 4 | 4 |
| valence | physio_emg_existing_22_ridge | 8 | 1 | 7 | 0.0712 | 0.0758 | 0.1530 | -0.0063 | 1 | 7 |
| valence | physio_emg_lagged_interaction_experimental_ridge | 8 | 4 | 4 | 0.0223 | 0.0033 | 0.1716 | -0.0332 | 4 | 4 |


## Interpretation

- Positive `lift_vs_stimulus_rmse` means the physiological block reduced score RMSE beyond stimulus-only.
- Positive `lift_vs_stimulus_dev_rmse` means the block improved residual/deviation RMSE.
- `dev_pearson` is central: it tests whether the block tracks subject-specific residual variation.
- Experimental directed/lagged features are not causal claims; they are exploratory directed-dynamics summaries.
