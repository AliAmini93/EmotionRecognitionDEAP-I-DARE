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
| arousal | physio_eeg_entropy_complexity_ridge | dev_rmse | 63 | -0.001439 | -0.004715 | -0.048617 | 0.047154 | 0.527124 | 31 | 32 | 0 | -1 | 0.599347 | -0.002163 | -0.004313 | False |
| arousal | physio_emg_lagged_interaction_experimental_ridge | dev_rmse | 63 | -0.010012 | -0.002840 | -0.023892 | 0.001886 | 0.925154 | 28 | 35 | 0 | -7 | 0.843248 | -0.009796 | -0.009796 | False |
| arousal | physio_eeg_bandpower_ridge | dev_rmse | 63 | -0.017777 | -0.007837 | -0.067342 | 0.033222 | 0.742613 | 28 | 35 | 0 | -7 | 0.843248 | -0.016899 | -0.018239 | False |
| arousal | physio_eeg_directed_connectivity_experimental_ridge | dev_rmse | 63 | -0.025386 | -0.022159 | -0.050843 | -0.001102 | 0.975851 | 23 | 40 | 0 | -17 | 0.988713 | -0.021678 | -0.022171 | False |
| arousal | physio_eeg_cov_riemannian_ridge | dev_rmse | 63 | -0.055497 | -0.033021 | -0.100879 | -0.011723 | 0.991450 | 23 | 40 | 0 | -17 | 0.988713 | -0.055165 | -0.058824 | False |
| arousal | physio_emg_bsl_stats_22_ridge | dev_rmse | 63 | -0.265690 | -0.001122 | -0.786476 | 0.000125 | 0.957352 | 31 | 32 | 0 | -1 | 0.599347 | -0.008287 | -1.094599 | False |
| arousal | physio_emg_existing_22_ridge | dev_rmse | 63 | -0.346622 | -0.004149 | -1.014049 | -0.007028 | 0.994400 | 26 | 37 | 0 | -11 | 0.935041 | -0.017656 | -1.449149 | False |
| arousal | physio_emg_expanded_812_ridge | dev_rmse | 63 | -61234.966492 | -0.048081 | -183685.887248 | -0.055651 | 1.000000 | 19 | 44 | 0 | -25 | 0.999551 | -0.102706 | -485885.327309 | False |
| arousal | physio_eeg_entropy_complexity_ridge | rmse | 63 | 0.001380 | -0.004715 | -0.047069 | 0.050633 | 0.486226 | 31 | 32 | 0 | -1 | 0.599347 | -0.002163 | -0.004313 | False |
| arousal | physio_emg_bsl_stats_22_ridge | rmse | 63 | -0.007077 | 0.001428 | -0.020969 | 0.006084 | 0.833408 | 32 | 31 | 0 | 1 | 0.500000 | -0.008287 | -1.094599 | False |
| arousal | physio_emg_lagged_interaction_experimental_ridge | rmse | 63 | -0.010012 | -0.002840 | -0.023807 | 0.001854 | 0.931003 | 28 | 35 | 0 | -7 | 0.843248 | -0.009796 | -0.009796 | False |
| arousal | physio_eeg_bandpower_ridge | rmse | 63 | -0.016095 | -0.007837 | -0.067537 | 0.035607 | 0.729564 | 28 | 35 | 0 | -7 | 0.843248 | -0.016899 | -0.018239 | False |
| arousal | physio_emg_existing_22_ridge | rmse | 63 | -0.017416 | -0.004149 | -0.031797 | -0.004616 | 0.994250 | 26 | 37 | 0 | -11 | 0.935041 | -0.017656 | -1.449149 | False |
| arousal | physio_eeg_directed_connectivity_experimental_ridge | rmse | 63 | -0.024870 | -0.022159 | -0.049985 | -0.000944 | 0.972551 | 24 | 39 | 0 | -15 | 0.978522 | -0.021678 | -0.022171 | False |
| arousal | physio_eeg_cov_riemannian_ridge | rmse | 63 | -0.051484 | -0.032445 | -0.097940 | -0.007944 | 0.985601 | 24 | 39 | 0 | -15 | 0.978522 | -0.055165 | -0.058824 | False |
| arousal | physio_emg_expanded_812_ridge | rmse | 63 | -0.099481 | -0.048081 | -0.175381 | -0.042938 | 1.000000 | 19 | 44 | 0 | -25 | 0.999551 | -0.102706 | -485885.327309 | False |
| valence | physio_emg_lagged_interaction_experimental_ridge | dev_rmse | 63 | -0.001183 | -0.001928 | -0.003959 | 0.001607 | 0.794310 | 29 | 34 | 0 | -5 | 0.775019 | -0.001378 | -0.001378 | False |
| valence | physio_eeg_entropy_complexity_ridge | dev_rmse | 63 | -0.021414 | -0.003351 | -0.037384 | -0.006633 | 0.996050 | 24 | 39 | 0 | -15 | 0.978522 | -0.020966 | -0.020979 | False |
| valence | physio_eeg_directed_connectivity_experimental_ridge | dev_rmse | 63 | -0.023503 | -0.013433 | -0.043759 | -0.007625 | 0.999500 | 23 | 40 | 0 | -17 | 0.988713 | -0.024242 | -0.024248 | False |
| valence | physio_eeg_bandpower_ridge | dev_rmse | 63 | -0.034026 | -0.017701 | -0.056321 | -0.015713 | 0.999950 | 23 | 40 | 0 | -17 | 0.988713 | -0.033578 | -0.033663 | False |
| valence | physio_eeg_cov_riemannian_ridge | dev_rmse | 63 | -0.052486 | -0.021816 | -0.107772 | -0.013499 | 0.997900 | 19 | 44 | 0 | -25 | 0.999551 | -0.059659 | -0.064867 | False |
| valence | physio_emg_bsl_stats_22_ridge | dev_rmse | 63 | -0.150996 | -0.001554 | -0.447125 | -0.000299 | 0.964002 | 25 | 38 | 0 | -13 | 0.961537 | -0.005374 | -0.582202 | False |
| valence | physio_emg_existing_22_ridge | dev_rmse | 63 | -0.367140 | -0.002826 | -1.097880 | -0.000042 | 0.964302 | 24 | 39 | 0 | -15 | 0.978522 | -0.001411 | -2.021658 | False |
| valence | physio_emg_expanded_812_ridge | dev_rmse | 63 | -5038.258065 | -0.016761 | -15017.600374 | -0.013125 | 0.999450 | 21 | 42 | 0 | -21 | 0.997424 | -0.073133 | -39225.222667 | False |
| valence | physio_emg_existing_22_ridge | rmse | 63 | -0.000956 | -0.002651 | -0.005324 | 0.003997 | 0.646168 | 25 | 38 | 0 | -13 | 0.961537 | -0.001411 | -2.021658 | False |
| valence | physio_emg_lagged_interaction_experimental_ridge | rmse | 63 | -0.001183 | -0.001928 | -0.003939 | 0.001585 | 0.793260 | 29 | 34 | 0 | -5 | 0.775019 | -0.001378 | -0.001378 | False |
| valence | physio_emg_bsl_stats_22_ridge | rmse | 63 | -0.004678 | -0.001554 | -0.011416 | 0.000493 | 0.941053 | 25 | 38 | 0 | -13 | 0.961537 | -0.005374 | -0.582202 | False |
| valence | physio_eeg_entropy_complexity_ridge | rmse | 63 | -0.021403 | -0.003351 | -0.037560 | -0.006467 | 0.996800 | 24 | 39 | 0 | -15 | 0.978522 | -0.020966 | -0.020979 | False |
| valence | physio_eeg_directed_connectivity_experimental_ridge | rmse | 63 | -0.023498 | -0.013433 | -0.043167 | -0.007807 | 0.999300 | 23 | 40 | 0 | -17 | 0.988713 | -0.024242 | -0.024248 | False |
| valence | physio_eeg_bandpower_ridge | rmse | 63 | -0.033960 | -0.017701 | -0.055566 | -0.015757 | 0.999700 | 23 | 40 | 0 | -17 | 0.988713 | -0.033578 | -0.033663 | False |
| valence | physio_eeg_cov_riemannian_ridge | rmse | 63 | -0.049662 | -0.021816 | -0.099348 | -0.013484 | 0.997450 | 19 | 44 | 0 | -25 | 0.999551 | -0.059659 | -0.064867 | False |
| valence | physio_emg_expanded_812_ridge | rmse | 63 | -0.052929 | -0.016761 | -0.121750 | -0.011871 | 0.999550 | 21 | 42 | 0 | -21 | 0.997424 | -0.073133 | -39225.222667 | False |


## Interpretation

- A positive pooled correlation is not enough.
- The model must beat stimulus-only per subject and in residual/dev RMSE.
- If the verdict is `NO_GO_CONFIRMED_CURRENT_FEATURE_SET`, current engineered EEG/EMG feature blocks should not be used to claim cross-subject physiological decoding beyond stimulus prior.
