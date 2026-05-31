# I-DARE Residual Physiology Confirmatory Statistics

Positive improvement means `stimulus_only RMSE - physiology_model RMSE`; positive is good for physiology.

## Confirmatory verdict

| target | confirmatory_verdict | best_candidate_model | best_candidate_pooled_lift_vs_stimulus_rmse | criterion |
| --- | --- | --- | --- | --- |
| arousal | NO_GO_CONFIRMED_CURRENT_FEATURE_SET | physio_eeg_entropy_complexity_ridge | -0.002163 | requires positive paired subject-level RMSE and dev-RMSE improvement, bootstrap CI lower bound > 0, sign-flip p < 0.05, win margin > 3, and pooled RMSE lift >= 0.02 |
| valence | NO_GO_CONFIRMED_CURRENT_FEATURE_SET | physio_emg_lagged_interaction_experimental_ridge | -0.001378 | requires positive paired subject-level RMSE and dev-RMSE improvement, bootstrap CI lower bound > 0, sign-flip p < 0.05, win margin > 3, and pooled RMSE lift >= 0.02 |


## Paired subject-level statistics

| target | model | metric | subjects | mean_improvement_stimulus_minus_model | median_improvement_stimulus_minus_model | ci95_low_mean_improvement | ci95_high_mean_improvement | signflip_p_one_sided_mean_gt_zero | wins | losses | ties | win_margin | sign_test_p_one_sided_wins_gt_losses | pooled_lift_vs_stimulus_rmse | pooled_lift_vs_stimulus_dev_rmse | passes_confirmatory_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | physio_eeg_entropy_complexity_ridge | dev_rmse | 63 | -0.001439 | -0.004715 | -0.049849 | 0.046202 | 0.519924 | 31 | 32 | 0 | -1 | 0.599347 | -0.002163 | -0.004313 | False |
| arousal | physio_emg_lagged_interaction_experimental_ridge | dev_rmse | 63 | -0.010012 | -0.002840 | -0.023791 | 0.001950 | 0.925604 | 28 | 35 | 0 | -7 | 0.843248 | -0.009796 | -0.009796 | False |
| arousal | physio_eeg_bandpower_ridge | dev_rmse | 63 | -0.017777 | -0.007837 | -0.067795 | 0.033750 | 0.753212 | 28 | 35 | 0 | -7 | 0.843248 | -0.016899 | -0.018239 | False |
| arousal | physio_eeg_directed_connectivity_experimental_ridge | dev_rmse | 63 | -0.025386 | -0.022159 | -0.050676 | -0.001034 | 0.974151 | 23 | 40 | 0 | -17 | 0.988713 | -0.021678 | -0.022171 | False |
| arousal | physio_eeg_cov_riemannian_ridge | dev_rmse | 63 | -0.055497 | -0.033021 | -0.100958 | -0.011795 | 0.992050 | 23 | 40 | 0 | -17 | 0.988713 | -0.055165 | -0.058824 | False |
| arousal | physio_emg_bsl_stats_22_ridge | dev_rmse | 63 | -0.265690 | -0.001122 | -0.786740 | 0.000220 | 0.956752 | 31 | 32 | 0 | -1 | 0.599347 | -0.008287 | -1.094599 | False |
| arousal | physio_emg_existing_22_ridge | dev_rmse | 63 | -0.346622 | -0.004149 | -1.011511 | -0.006646 | 0.994350 | 26 | 37 | 0 | -11 | 0.935041 | -0.017656 | -1.449149 | False |
| arousal | physio_emg_expanded_812_ridge | dev_rmse | 63 | -61234.966492 | -0.048081 | -183685.893132 | -0.057554 | 1.000000 | 19 | 44 | 0 | -25 | 0.999551 | -0.102706 | -485885.327309 | False |
| arousal | physio_eeg_entropy_complexity_ridge | rmse | 63 | 0.001380 | -0.004715 | -0.047622 | 0.050646 | 0.473676 | 31 | 32 | 0 | -1 | 0.599347 | -0.002163 | -0.004313 | False |
| arousal | physio_emg_bsl_stats_22_ridge | rmse | 63 | -0.007077 | 0.001428 | -0.020981 | 0.006177 | 0.834608 | 32 | 31 | 0 | 1 | 0.500000 | -0.008287 | -1.094599 | False |
| arousal | physio_emg_lagged_interaction_experimental_ridge | rmse | 63 | -0.010012 | -0.002840 | -0.023738 | 0.002118 | 0.931853 | 28 | 35 | 0 | -7 | 0.843248 | -0.009796 | -0.009796 | False |
| arousal | physio_eeg_bandpower_ridge | rmse | 63 | -0.016095 | -0.007837 | -0.067127 | 0.035218 | 0.724564 | 28 | 35 | 0 | -7 | 0.843248 | -0.016899 | -0.018239 | False |
| arousal | physio_emg_existing_22_ridge | rmse | 63 | -0.017416 | -0.004149 | -0.032053 | -0.004659 | 0.994050 | 26 | 37 | 0 | -11 | 0.935041 | -0.017656 | -1.449149 | False |
| arousal | physio_eeg_directed_connectivity_experimental_ridge | rmse | 63 | -0.024870 | -0.022159 | -0.049767 | -0.000908 | 0.973151 | 24 | 39 | 0 | -15 | 0.978522 | -0.021678 | -0.022171 | False |
| arousal | physio_eeg_cov_riemannian_ridge | rmse | 63 | -0.051484 | -0.032445 | -0.097471 | -0.007964 | 0.987501 | 24 | 39 | 0 | -15 | 0.978522 | -0.055165 | -0.058824 | False |
| arousal | physio_emg_expanded_812_ridge | rmse | 63 | -0.099481 | -0.048081 | -0.174539 | -0.043770 | 1.000000 | 19 | 44 | 0 | -25 | 0.999551 | -0.102706 | -485885.327309 | False |
| valence | physio_emg_lagged_interaction_experimental_ridge | dev_rmse | 63 | -0.001183 | -0.001928 | -0.003993 | 0.001595 | 0.794210 | 29 | 34 | 0 | -5 | 0.775019 | -0.001378 | -0.001378 | False |
| valence | physio_eeg_entropy_complexity_ridge | dev_rmse | 63 | -0.021414 | -0.003351 | -0.037493 | -0.006454 | 0.995800 | 24 | 39 | 0 | -15 | 0.978522 | -0.020966 | -0.020979 | False |
| valence | physio_eeg_directed_connectivity_experimental_ridge | dev_rmse | 63 | -0.023503 | -0.013433 | -0.043701 | -0.007688 | 0.999450 | 23 | 40 | 0 | -17 | 0.988713 | -0.024242 | -0.024248 | False |
| valence | physio_eeg_bandpower_ridge | dev_rmse | 63 | -0.034026 | -0.017701 | -0.055539 | -0.015767 | 0.999800 | 23 | 40 | 0 | -17 | 0.988713 | -0.033578 | -0.033663 | False |
| valence | physio_eeg_cov_riemannian_ridge | dev_rmse | 63 | -0.052486 | -0.021816 | -0.108104 | -0.012918 | 0.998050 | 19 | 44 | 0 | -25 | 0.999551 | -0.059659 | -0.064867 | False |
| valence | physio_emg_bsl_stats_22_ridge | dev_rmse | 63 | -0.150996 | -0.001554 | -0.448195 | -0.000400 | 0.962852 | 25 | 38 | 0 | -13 | 0.961537 | -0.005374 | -0.582202 | False |
| valence | physio_emg_existing_22_ridge | dev_rmse | 63 | -0.367140 | -0.002826 | -1.098104 | -0.000018 | 0.965252 | 24 | 39 | 0 | -15 | 0.978522 | -0.001411 | -2.021658 | False |
| valence | physio_emg_expanded_812_ridge | dev_rmse | 63 | -5038.258065 | -0.016761 | -15017.601070 | -0.013079 | 0.999750 | 21 | 42 | 0 | -21 | 0.997424 | -0.073133 | -39225.222667 | False |
| valence | physio_emg_existing_22_ridge | rmse | 63 | -0.000956 | -0.002651 | -0.005392 | 0.004026 | 0.642518 | 25 | 38 | 0 | -13 | 0.961537 | -0.001411 | -2.021658 | False |
| valence | physio_emg_lagged_interaction_experimental_ridge | rmse | 63 | -0.001183 | -0.001928 | -0.003931 | 0.001600 | 0.793760 | 29 | 34 | 0 | -5 | 0.775019 | -0.001378 | -0.001378 | False |
| valence | physio_emg_bsl_stats_22_ridge | rmse | 63 | -0.004678 | -0.001554 | -0.011566 | 0.000514 | 0.942153 | 25 | 38 | 0 | -13 | 0.961537 | -0.005374 | -0.582202 | False |
| valence | physio_eeg_entropy_complexity_ridge | rmse | 63 | -0.021403 | -0.003351 | -0.037546 | -0.006598 | 0.995500 | 24 | 39 | 0 | -15 | 0.978522 | -0.020966 | -0.020979 | False |
| valence | physio_eeg_directed_connectivity_experimental_ridge | rmse | 63 | -0.023498 | -0.013433 | -0.043883 | -0.007731 | 0.999350 | 23 | 40 | 0 | -17 | 0.988713 | -0.024242 | -0.024248 | False |
| valence | physio_eeg_bandpower_ridge | rmse | 63 | -0.033960 | -0.017701 | -0.055474 | -0.015674 | 0.999850 | 23 | 40 | 0 | -17 | 0.988713 | -0.033578 | -0.033663 | False |
| valence | physio_eeg_cov_riemannian_ridge | rmse | 63 | -0.049662 | -0.021816 | -0.100916 | -0.013114 | 0.997850 | 19 | 44 | 0 | -25 | 0.999551 | -0.059659 | -0.064867 | False |
| valence | physio_emg_expanded_812_ridge | rmse | 63 | -0.052929 | -0.016761 | -0.121176 | -0.012004 | 0.999500 | 21 | 42 | 0 | -21 | 0.997424 | -0.073133 | -39225.222667 | False |


## Interpretation

- A positive pooled correlation is not enough.
- The model must beat stimulus-only per subject and in residual/dev RMSE.
- If the verdict is `NO_GO_CONFIRMED_CURRENT_FEATURE_SET`, current engineered EEG/EMG feature blocks should not be used to claim cross-subject physiological decoding beyond stimulus prior.
