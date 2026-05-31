# I-DARE High-Disagreement Direct Deviation Challenge

This audit asks whether fixed EEG/EMG feature blocks predict residuals specifically where the subject rating deviates strongly from the stimulus prior.

Residual target: `rating - train_stimulus_mean`. The zero-residual baseline is the stimulus-only prediction.

## Decision table

| target | decision | quantile | best_block | best_model | n | subjects | abs_residual_threshold | stimulus_residual_rmse_on_subset | best_model_residual_rmse_on_subset | best_lift_vs_zero_residual_rmse | best_residual_pearson | best_residual_sign_acc | rmse_wins | rmse_losses | rmse_win_margin | mean_delta_rmse_model_minus_stimulus | passes_high_disagreement_gate | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | GO_HIGH_DISAGREEMENT_DIRECT_DEVIATION_PHYSIOLOGY | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 508 | 63 | 2.209677 | 3.240139 | 3.168414 | 0.071725 | 0.212972 | 0.557087 | 35 | 28 | 7 | -0.099588 | True | physiology predicts high-disagreement residuals with practical RMSE lift and paired subject stability |
| valence | WEAK_HIGH_DISAGREEMENT_SIGNAL_NEEDS_CONFIRMATION | 0.750000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 505 | 63 | 1.435484 | 2.118605 | 2.116596 | 0.002009 | 0.047266 | 0.487129 | 29 | 34 | -5 | -0.004321 | False | residual RMSE lift on high-disagreement subset is below practical threshold; residual correlation is weak; subject-level win margin is not stable |


## High-disagreement thresholds

| target | quantile | abs_residual_threshold | n_samples | n_subjects | stimulus_residual_rmse_on_subset | mean_abs_residual_on_subset |
| --- | --- | --- | --- | --- | --- | --- |
| arousal | 0.500000 | 1.427419 | 1008 | 63 | 2.622719 | 2.452125 |
| arousal | 0.750000 | 2.209677 | 508 | 63 | 3.240139 | 3.120237 |
| arousal | 0.900000 | 3.000000 | 209 | 55 | 4.025323 | 3.948372 |
| valence | 0.500000 | 0.822581 | 1015 | 63 | 1.701274 | 1.580788 |
| valence | 0.750000 | 1.435484 | 505 | 63 | 2.118605 | 2.036602 |
| valence | 0.900000 | 1.911290 | 202 | 58 | 2.655947 | 2.600607 |


## Top high-disagreement physiology metrics

| target | quantile | abs_residual_threshold | block | model | n | subjects | stimulus_residual_rmse_on_subset | model_score_rmse_on_subset | model_residual_rmse_on_subset | lift_vs_zero_residual_rmse | residual_pearson | residual_spearman | residual_sign_acc | pred_residual_std | true_residual_std | rmse_wins | rmse_losses | rmse_ties | rmse_win_margin | mean_delta_rmse_model_minus_stimulus | median_delta_rmse_model_minus_stimulus | worst_regression_delta_rmse | best_gain_delta_rmse | passes_high_disagreement_gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0.500000 | 1.427419 | eeg_entropy_complexity | physio_eeg_entropy_complexity_ridge | 1008 | 63 | 2.622719 | 2.584392 | 2.586907 | 0.035813 | 0.171569 | 0.174683 | 0.592262 | 0.559046 | 2.620480 | 38 | 25 | 0 | 13 | -0.044373 | -0.044218 | 0.417653 | -0.795633 | True |
| arousal | 0.500000 | 1.427419 | eeg_bandpower | physio_eeg_bandpower_ridge | 1008 | 63 | 2.622719 | 2.587798 | 2.588825 | 0.033894 | 0.172998 | 0.168918 | 0.548611 | 0.616203 | 2.620480 | 33 | 30 | 0 | 3 | -0.039439 | -0.030147 | 0.497212 | -0.877116 | True |
| arousal | 0.500000 | 1.427419 | eeg_directed_connectivity_experimental | physio_eeg_directed_connectivity_experimental_ridge | 1008 | 63 | 2.622719 | 2.617622 | 2.617622 | 0.005098 | 0.092836 | 0.076943 | 0.526786 | 0.428772 | 2.620480 | 30 | 33 | 0 | -3 | -0.003626 | 0.009467 | 0.389410 | -0.722724 | False |
| arousal | 0.500000 | 1.427419 | none | stimulus_only | 1008 | 63 | 2.622719 | 2.622719 | 2.622719 | 0.000000 |  |  | 0.000000 | 0.000000 | 2.620480 | 0 | 0 | 63 | 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | False |
| arousal | 0.500000 | 1.427419 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 1008 | 63 | 2.622719 | 2.631349 | 2.631349 | -0.008629 | -0.040767 | 0.015139 | 0.533730 | 0.129744 | 2.620480 | 31 | 32 | 0 | -1 | 0.006030 | 0.000594 | 0.241838 | -0.113921 | False |
| arousal | 0.500000 | 1.427419 | eeg_cov_riemannian | physio_eeg_cov_riemannian_ridge | 1008 | 63 | 2.622719 | 2.643435 | 2.644687 | -0.021968 | 0.089350 | 0.070882 | 0.520833 | 0.631859 | 2.620480 | 30 | 33 | 0 | -3 | 0.012110 | 0.031700 | 0.694479 | -0.743028 | False |
| arousal | 0.500000 | 1.427419 | emg_bsl_stats_22 | physio_emg_bsl_stats_22_ridge | 1008 | 63 | 2.622719 | 2.631358 | 4.215241 | -1.592521 | 0.053020 | -0.073867 | 0.483135 | 3.436424 | 2.620480 | 28 | 35 | 0 | -7 | 0.332080 | 0.006768 | 20.475931 | -0.227216 | False |
| arousal | 0.500000 | 1.427419 | emg_existing_22 | physio_emg_existing_22_ridge | 1008 | 63 | 2.622719 | 2.639458 | 4.717147 | -2.094427 | 0.021994 | -0.044968 | 0.478175 | 3.980364 | 2.620480 | 28 | 35 | 0 | -7 | 0.503176 | 0.004072 | 31.261255 | -0.150595 | False |
| arousal | 0.500000 | 1.427419 | emg_expanded_812 | physio_emg_expanded_812_ridge | 1008 | 63 | 2.622719 | 2.682367 | 287207.077413 | -287204.454693 | 0.041722 | 0.002883 | 0.505952 | 286784.997164 | 2.620480 | 22 | 41 | 0 | -19 | 38706.953056 | 0.042882 | 2437030.207741 | -0.411368 | False |
| arousal | 0.750000 | 2.209677 | eeg_bandpower | physio_eeg_bandpower_ridge | 508 | 63 | 3.240139 | 3.167854 | 3.168414 | 0.071725 | 0.212972 | 0.182790 | 0.557087 | 0.589505 | 3.215878 | 35 | 28 | 0 | 7 | -0.099588 | -0.020773 | 0.565286 | -1.794632 | True |
| arousal | 0.750000 | 2.209677 | eeg_entropy_complexity | physio_eeg_entropy_complexity_ridge | 508 | 63 | 3.240139 | 3.173358 | 3.173358 | 0.066781 | 0.204120 | 0.192080 | 0.604331 | 0.551978 | 3.215878 | 37 | 26 | 0 | 11 | -0.096039 | -0.033071 | 0.486561 | -1.783671 | True |
| arousal | 0.750000 | 2.209677 | eeg_directed_connectivity_experimental | physio_eeg_directed_connectivity_experimental_ridge | 508 | 63 | 3.240139 | 3.219151 | 3.219151 | 0.020988 | 0.110694 | 0.097780 | 0.525591 | 0.446850 | 3.215878 | 30 | 33 | 0 | -3 | -0.013627 | 0.012754 | 0.774406 | -1.291388 | False |
| arousal | 0.750000 | 2.209677 | eeg_cov_riemannian | physio_eeg_cov_riemannian_ridge | 508 | 63 | 3.240139 | 3.229018 | 3.229032 | 0.011107 | 0.118733 | 0.093439 | 0.539370 | 0.604286 | 3.215878 | 32 | 31 | 0 | 1 | -0.031451 | -0.023782 | 0.749631 | -1.815960 | False |
| arousal | 0.750000 | 2.209677 | none | stimulus_only | 508 | 63 | 3.240139 | 3.240139 | 3.240139 | 0.000000 |  |  | 0.000000 | 0.000000 | 3.215878 | 0 | 0 | 63 | 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | False |
| arousal | 0.750000 | 2.209677 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 508 | 63 | 3.240139 | 3.251814 | 3.251814 | -0.011675 | -0.061715 | 0.002731 | 0.521654 | 0.130998 | 3.215878 | 30 | 33 | 0 | -3 | 0.010622 | 0.000546 | 0.295508 | -0.163529 | False |
| valence | 0.500000 | 0.822581 | none | stimulus_only | 1015 | 63 | 1.701274 | 1.701274 | 1.701274 | 0.000000 |  |  | 0.000000 | 0.000000 | 1.697303 | 0 | 0 | 63 | 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | False |
| valence | 0.500000 | 0.822581 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 1015 | 63 | 1.701274 | 1.701292 | 1.701292 | -0.000018 | 0.021723 | -0.016631 | 0.488670 | 0.063653 | 1.697303 | 28 | 35 | 0 | -7 | -0.001314 | 0.000839 | 0.043263 | -0.082034 | False |
| valence | 0.500000 | 0.822581 | eeg_entropy_complexity | physio_eeg_entropy_complexity_ridge | 1015 | 63 | 1.701274 | 1.717128 | 1.717148 | -0.015874 | -0.007617 | 0.012214 | 0.521182 | 0.222025 | 1.697303 | 33 | 30 | 0 | 3 | 0.015865 | -0.004542 | 0.320348 | -0.140544 | False |
| valence | 0.500000 | 0.822581 | eeg_directed_connectivity_experimental | physio_eeg_directed_connectivity_experimental_ridge | 1015 | 63 | 1.701274 | 1.724445 | 1.724445 | -0.023171 | -0.059807 | -0.024290 | 0.500493 | 0.201496 | 1.697303 | 27 | 36 | 0 | -9 | 0.023546 | 0.010341 | 0.486971 | -0.110347 | False |
| valence | 0.500000 | 0.822581 | eeg_bandpower | physio_eeg_bandpower_ridge | 1015 | 63 | 1.701274 | 1.729674 | 1.729674 | -0.028400 | -0.039111 | -0.007679 | 0.509360 | 0.256050 | 1.697303 | 28 | 35 | 0 | -7 | 0.030134 | 0.011156 | 0.594334 | -0.135766 | False |
| valence | 0.500000 | 0.822581 | eeg_cov_riemannian | physio_eeg_cov_riemannian_ridge | 1015 | 63 | 1.701274 | 1.749238 | 1.750672 | -0.049398 | -0.026573 | 0.024927 | 0.509360 | 0.367858 | 1.697303 | 25 | 38 | 0 | -13 | 0.038300 | 0.009539 | 1.451169 | -0.397502 | False |
| valence | 0.500000 | 0.822581 | emg_bsl_stats_22 | physio_emg_bsl_stats_22_ridge | 1015 | 63 | 1.701274 | 1.705641 | 2.542530 | -0.841256 | -0.018965 | -0.024228 | 0.479803 | 1.851921 | 1.697303 | 28 | 35 | 0 | -7 | 0.198415 | 0.001091 | 12.304262 | -0.101847 | False |
| valence | 0.500000 | 0.822581 | emg_existing_22 | physio_emg_existing_22_ridge | 1015 | 63 | 1.701274 | 1.700952 | 4.594019 | -2.892745 | 0.055604 | -0.009777 | 0.477833 | 4.356648 | 1.697303 | 25 | 38 | 0 | -13 | 0.574522 | 0.002609 | 36.101388 | -0.077794 | False |
| valence | 0.500000 | 0.822581 | emg_expanded_812 | physio_emg_expanded_812_ridge | 1015 | 63 | 1.701274 | 1.758555 | 33721.818032 | -33720.116758 | -0.015889 | -0.017806 | 0.494581 | 33638.167459 | 1.697303 | 26 | 37 | 0 | -11 | 4856.731669 | 0.019050 | 297813.402677 | -0.127266 | False |
| valence | 0.750000 | 1.435484 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 505 | 63 | 2.118605 | 2.116596 | 2.116596 | 0.002009 | 0.047266 | -0.026673 | 0.487129 | 0.066455 | 2.117781 | 29 | 34 | 0 | -5 | -0.004321 | 0.000432 | 0.059040 | -0.093457 | False |
| valence | 0.750000 | 1.435484 | none | stimulus_only | 505 | 63 | 2.118605 | 2.118605 | 2.118605 | 0.000000 |  |  | 0.000000 | 0.000000 | 2.117781 | 0 | 0 | 63 | 0 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | False |
| valence | 0.750000 | 1.435484 | eeg_entropy_complexity | physio_eeg_entropy_complexity_ridge | 505 | 63 | 2.118605 | 2.132281 | 2.132281 | -0.013676 | -0.006465 | 0.001864 | 0.542574 | 0.228912 | 2.117781 | 35 | 28 | 0 | 7 | 0.015397 | -0.013280 | 0.365264 | -0.199024 | False |
| valence | 0.750000 | 1.435484 | eeg_directed_connectivity_experimental | physio_eeg_directed_connectivity_experimental_ridge | 505 | 63 | 2.118605 | 2.142434 | 2.142434 | -0.023830 | -0.076591 | -0.057091 | 0.489109 | 0.195471 | 2.117781 | 26 | 37 | 0 | -11 | 0.023517 | 0.005031 | 0.543761 | -0.151098 | False |
| valence | 0.750000 | 1.435484 | eeg_bandpower | physio_eeg_bandpower_ridge | 505 | 63 | 2.118605 | 2.144449 | 2.144449 | -0.025844 | -0.038035 | -0.023948 | 0.512871 | 0.262587 | 2.117781 | 29 | 34 | 0 | -5 | 0.030874 | 0.013708 | 0.683923 | -0.218344 | False |
| valence | 0.750000 | 1.435484 | eeg_cov_riemannian | physio_eeg_cov_riemannian_ridge | 505 | 63 | 2.118605 | 2.167550 | 2.169681 | -0.051077 | -0.042461 | 0.004362 | 0.514851 | 0.386365 | 2.117781 | 27 | 36 | 0 | -9 | 0.035289 | 0.009343 | 1.557889 | -0.535005 | False |


## Interpretation

- `GO` means EEG/EMG predicts subjective deviation where stimulus-only is weakest.

- `WEAK` means some correlation or small lift appears, but it is not stable enough for a scientific claim.

- `NO_GO` means current fixed EEG/EMG features remain insufficient even on high-disagreement samples.


## Next steps

| priority | step | title | purpose | success_condition |
| --- | --- | --- | --- | --- |
| 1 | 05ak | Representation-learning feasibility plan | If high-disagreement residuals still do not pass, move beyond fixed engineered EEG/EMG features. | Learned EEG/EMG representations beat fixed-feature residual models under the locked evaluation. |
| 2 | 05al | Failure-subject physiology rescue | Test whether physiology helps only for subjects where locked personalization still regresses. | Improves failure-subject RMSE without harming pooled or paired metrics. |
| 3 | 05am | Physiology-assisted calibration sample reduction | Test if physiology can reduce k even when it cannot beat the k=16 locked model. | Physiology-assisted lower-k model matches the locked k=16 baseline with subject-level stability. |
