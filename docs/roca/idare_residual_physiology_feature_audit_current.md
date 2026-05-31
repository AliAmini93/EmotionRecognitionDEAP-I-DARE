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
| emg_existing_22 | [2016, 22] | 22 | [emg_existing_22_f0000, emg_existing_22_f0001, emg_existing_22_f0002, emg_existing_22_f0003, emg_existing_22_f0004, emg_existing_22_f0005, emg_existing_22_f0006, emg_existing_22_f0007, ...] |
| emg_bsl_stats_22 | [2016, 22] | 22 | [emg_bsl_stats_22_f0000, emg_bsl_stats_22_f0001, emg_bsl_stats_22_f0002, emg_bsl_stats_22_f0003, emg_bsl_stats_22_f0004, emg_bsl_stats_22_f0005, emg_bsl_stats_22_f0006, emg_bsl_stats_22_f0007, ...] |
| emg_expanded_812 | [2016, 812] | 812 | [emg_expanded_812_f0000, emg_expanded_812_f0001, emg_expanded_812_f0002, emg_expanded_812_f0003, emg_expanded_812_f0004, emg_expanded_812_f0005, emg_expanded_812_f0006, emg_expanded_812_f0007, ...] |
| eeg_bandpower | [2016, 330] | 330 | [eeg_delta_logpower_ch00, eeg_delta_logpower_ch01, eeg_delta_logpower_ch02, eeg_delta_logpower_ch03, eeg_delta_logpower_ch04, eeg_delta_logpower_ch05, eeg_delta_logpower_ch06, eeg_delta_logpower_ch07, ...] |
| eeg_entropy_complexity | [2016, 192] | 192 | [eeg_log_activity_ch00, eeg_log_activity_ch01, eeg_log_activity_ch02, eeg_log_activity_ch03, eeg_log_activity_ch04, eeg_log_activity_ch05, eeg_log_activity_ch06, eeg_log_activity_ch07, ...] |
| eeg_cov_riemannian | [2016, 560] | 560 | [eeg_cov_ch00_ch00, eeg_cov_ch00_ch01, eeg_cov_ch00_ch02, eeg_cov_ch00_ch03, eeg_cov_ch00_ch04, eeg_cov_ch00_ch05, eeg_cov_ch00_ch06, eeg_cov_ch00_ch07, ...] |
| emg_lagged_interaction_experimental | [2016, 6] | 6 | [emg_env_corr_lag0, emg_env_corr_max, emg_env_corr_lag_at_max_scaled, emg_env_lead_lag_asym, emg_burst_coactivation_fraction, emg_burst_xor_fraction] |
| eeg_directed_connectivity_experimental | [2016, 280] | 280 | [eeg_directed_lagcorr_roi0_to_roi1_lag1, eeg_directed_lagcorr_roi0_to_roi2_lag1, eeg_directed_lagcorr_roi0_to_roi3_lag1, eeg_directed_lagcorr_roi0_to_roi4_lag1, eeg_directed_lagcorr_roi0_to_roi5_lag1, eeg_directed_lagcorr_roi0_to_roi6_lag1, eeg_directed_lagcorr_roi0_to_roi7_lag1, eeg_directed_lagcorr_roi1_to_roi0_lag1, ...] |


## Main metrics

| target | model | n | mae | rmse | pearson | spearman | ccc | dev_rmse | dev_pearson | dev_sign_acc | true_dev_std | pred_dev_std | lift_vs_stimulus_rmse | lift_vs_stimulus_dev_rmse | lift_vs_stimulus_dev_pearson | lift_vs_stimulus_pred_dev_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | physio_eeg_bandpower_ridge | 2016 | 1.5915 | 1.9611 | 0.6287 | 0.6131 | 0.5871 | 1.9624 | 0.1255 | 0.5278 | 1.9442 | 0.6054 | -0.0169 | -0.0182 |  | 0.6054 |
| arousal | physio_eeg_cov_riemannian_ridge | 2016 | 1.6124 | 1.9994 | 0.6112 | 0.5908 | 0.5706 | 2.0030 | 0.0668 | 0.5149 | 1.9442 | 0.6284 | -0.0552 | -0.0588 |  | 0.6284 |
| arousal | physio_eeg_directed_connectivity_experimental_ridge | 2016 | 1.5988 | 1.9659 | 0.6257 | 0.6073 | 0.5808 | 1.9664 | 0.0652 | 0.5188 | 1.9442 | 0.4465 | -0.0217 | -0.0222 |  | 0.4465 |
| arousal | physio_eeg_entropy_complexity_ridge | 2016 | 1.5723 | 1.9464 | 0.6349 | 0.6205 | 0.5911 | 1.9485 | 0.1317 | 0.5615 | 1.9442 | 0.5429 | -0.0022 | -0.0043 |  | 0.5429 |
| arousal | physio_emg_bsl_stats_22_ridge | 2016 | 1.5820 | 1.9525 | 0.6306 | 0.6081 | 0.5781 | 3.0388 | 0.0498 | 0.5104 | 1.9442 | 2.4336 | -0.0083 | -1.0946 |  | 2.4336 |
| arousal | physio_emg_existing_22_ridge | 2016 | 1.5934 | 1.9619 | 0.6262 | 0.6035 | 0.5742 | 3.3934 | 0.0221 | 0.4931 | 1.9442 | 2.8242 | -0.0177 | -1.4491 |  | 2.8242 |
| arousal | physio_emg_expanded_812_ridge | 2016 | 1.6512 | 2.0469 | 0.5900 | 0.5811 | 0.5526 | 485887.2715 | 0.0140 | 0.5040 | 1.9442 | 484700.6028 | -0.1027 | -485885.3273 |  | 484700.6028 |
| arousal | physio_emg_lagged_interaction_experimental_ridge | 2016 | 1.5878 | 1.9540 | 0.6298 | 0.6095 | 0.5760 | 1.9540 | -0.0441 | 0.5144 | 1.9442 | 0.1277 | -0.0098 | -0.0098 |  | 0.1277 |
| arousal | stimulus_only | 2016 | 1.5799 | 1.9442 | 0.6344 | 0.5985 | 0.5794 | 1.9442 |  | 0.0000 | 1.9442 | 0.0000 | 0.0000 | 0.0000 |  | 0.0000 |
| valence | physio_eeg_bandpower_ridge | 2016 | 1.0428 | 1.2914 | 0.8586 | 0.8468 | 0.8507 | 1.2914 | -0.0348 | 0.4965 | 1.2578 | 0.2522 | -0.0336 | -0.0337 |  | 0.2522 |
| valence | physio_eeg_cov_riemannian_ridge | 2016 | 1.0533 | 1.3174 | 0.8527 | 0.8420 | 0.8462 | 1.3226 | -0.0222 | 0.5025 | 1.2578 | 0.3821 | -0.0597 | -0.0649 |  | 0.3821 |
| valence | physio_eeg_directed_connectivity_experimental_ridge | 2016 | 1.0348 | 1.2820 | 0.8608 | 0.8476 | 0.8531 | 1.2820 | -0.0426 | 0.4965 | 1.2578 | 0.2002 | -0.0242 | -0.0242 |  | 0.2002 |
| valence | physio_eeg_entropy_complexity_ridge | 2016 | 1.0300 | 1.2787 | 0.8615 | 0.8500 | 0.8537 | 1.2788 | -0.0096 | 0.5109 | 1.2578 | 0.2188 | -0.0210 | -0.0210 |  | 0.2188 |
| valence | physio_emg_bsl_stats_22_ridge | 2016 | 1.0256 | 1.2631 | 0.8651 | 0.8493 | 0.8571 | 1.8400 | -0.0215 | 0.4777 | 1.2578 | 1.3158 | -0.0054 | -0.5822 |  | 1.3158 |
| valence | physio_emg_existing_22_ridge | 2016 | 1.0214 | 1.2592 | 0.8660 | 0.8500 | 0.8578 | 3.2794 | 0.0510 | 0.4960 | 1.2578 | 3.0928 | -0.0014 | -2.0217 |  | 3.0928 |
| valence | physio_emg_expanded_812_ridge | 2016 | 1.0503 | 1.3309 | 0.8496 | 0.8389 | 0.8430 | 39226.4804 | -0.0133 | 0.4955 | 1.2578 | 39125.6902 | -0.0731 | -39225.2227 |  | 39125.6902 |
| valence | physio_emg_lagged_interaction_experimental_ridge | 2016 | 1.0233 | 1.2592 | 0.8660 | 0.8489 | 0.8578 | 1.2592 | 0.0022 | 0.4816 | 1.2578 | 0.0617 | -0.0014 | -0.0014 |  | 0.0617 |
| valence | stimulus_only | 2016 | 1.0221 | 1.2578 | 0.8663 | 0.8414 | 0.8581 | 1.2578 |  | 0.0000 | 1.2578 | 0.0000 | 0.0000 | 0.0000 |  | 0.0000 |


## Subject win/loss vs stimulus-only

| target | model | subjects | rmse_wins | rmse_losses | mean_delta_rmse_model_minus_stimulus | median_delta_rmse_model_minus_stimulus | worst_regression_delta_rmse | best_gain_delta_rmse | dev_rmse_wins | dev_rmse_losses |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | physio_eeg_bandpower_ridge | 63 | 28 | 35 | 0.0161 | 0.0078 | 0.6513 | -0.6704 | 28 | 35 |
| arousal | physio_eeg_cov_riemannian_ridge | 63 | 24 | 39 | 0.0515 | 0.0324 | 0.7708 | -0.4701 | 23 | 40 |
| arousal | physio_eeg_directed_connectivity_experimental_ridge | 63 | 24 | 39 | 0.0249 | 0.0222 | 0.3785 | -0.1651 | 23 | 40 |
| arousal | physio_eeg_entropy_complexity_ridge | 63 | 31 | 32 | -0.0014 | 0.0047 | 0.4782 | -0.6369 | 31 | 32 |
| arousal | physio_emg_bsl_stats_22_ridge | 63 | 32 | 31 | 0.0071 | -0.0014 | 0.2560 | -0.1323 | 31 | 32 |
| arousal | physio_emg_existing_22_ridge | 63 | 26 | 37 | 0.0174 | 0.0041 | 0.2522 | -0.0927 | 26 | 37 |
| arousal | physio_emg_expanded_812_ridge | 63 | 19 | 44 | 0.0995 | 0.0481 | 1.7309 | -0.1670 | 19 | 44 |
| arousal | physio_emg_lagged_interaction_experimental_ridge | 63 | 28 | 35 | 0.0100 | 0.0028 | 0.2177 | -0.0759 | 28 | 35 |
| valence | physio_eeg_bandpower_ridge | 63 | 23 | 40 | 0.0340 | 0.0177 | 0.4821 | -0.1005 | 23 | 40 |
| valence | physio_eeg_cov_riemannian_ridge | 63 | 19 | 44 | 0.0497 | 0.0218 | 1.2363 | -0.3082 | 19 | 44 |
| valence | physio_eeg_directed_connectivity_experimental_ridge | 63 | 23 | 40 | 0.0235 | 0.0134 | 0.4185 | -0.0995 | 23 | 40 |
| valence | physio_eeg_entropy_complexity_ridge | 63 | 24 | 39 | 0.0214 | 0.0034 | 0.2372 | -0.1026 | 24 | 39 |
| valence | physio_emg_bsl_stats_22_ridge | 63 | 25 | 38 | 0.0047 | 0.0016 | 0.1678 | -0.0373 | 25 | 38 |
| valence | physio_emg_existing_22_ridge | 63 | 25 | 38 | 0.0010 | 0.0027 | 0.0466 | -0.0972 | 24 | 39 |
| valence | physio_emg_expanded_812_ridge | 63 | 21 | 42 | 0.0529 | 0.0168 | 1.8912 | -0.0861 | 21 | 42 |
| valence | physio_emg_lagged_interaction_experimental_ridge | 63 | 29 | 34 | 0.0012 | 0.0019 | 0.0314 | -0.0387 | 29 | 34 |


## Interpretation

- Positive `lift_vs_stimulus_rmse` means the physiological block reduced score RMSE beyond stimulus-only.
- Positive `lift_vs_stimulus_dev_rmse` means the block improved residual/deviation RMSE.
- `dev_pearson` is central: it tests whether the block tracks subject-specific residual variation.
- Experimental directed/lagged features are not causal claims; they are exploratory directed-dynamics summaries.
