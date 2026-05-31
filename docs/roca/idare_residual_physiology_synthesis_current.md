# I-DARE Residual Physiology Synthesis

This report synthesizes prior baselines, label variance decomposition, and the 05w residual physiology feature audit.

## Go / No-Go verdict

| target | decision | best_model | best_rmse | stimulus_rmse_reference | best_lift_vs_stimulus_rmse | best_lift_vs_stimulus_dev_rmse | best_dev_pearson | rmse_wins | rmse_losses | win_margin | stimulus_r2_in_sample | subject_r2_in_sample | residual_std_ratio_after_loso_stimulus | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_GO_CURRENT_FEATURE_SET | physio_eeg_entropy_complexity_ridge | 1.946368 | 1.944205 | -0.002163 | -0.004313 | 0.131747 | 31.000000 | 32.000000 | -1.000000 | 0.421045 | 0.155841 | 0.773163 | best physiologic block does not beat stimulus-only RMSE; residual/dev RMSE does not improve over stimulus-only; subject-level win margin is not meaningfully positive; required > 3 |
| valence | NO_GO_CURRENT_FEATURE_SET | physio_emg_lagged_interaction_experimental_ridge | 1.259152 | 1.257774 | -0.001378 | -0.001378 | 0.002204 | 29.000000 | 34.000000 | -5.000000 | 0.758326 | 0.022422 | 0.499532 | best physiologic block does not beat stimulus-only RMSE; residual/dev RMSE does not improve over stimulus-only; subject-level win margin is not meaningfully positive; required > 3 |


## Interpretation

- `NO_GO_CURRENT_FEATURE_SET` means the current EEG/EMG engineered feature blocks do not provide reliable residual improvement beyond stimulus-only under the current LOSO audit.
- This does not prove physiology contains no signal; it means the tested feature blocks and Ridge audit did not extract a cross-subject residual signal strong enough to justify architecture optimization as a scientific claim.
- A model is only interesting here if it improves stimulus-only in pooled RMSE, residual/dev RMSE, and subject-level win/loss stability.


## Top physiology models by RMSE lift vs stimulus-only

| target | model | n | rmse | lift_vs_stimulus_rmse | dev_rmse | lift_vs_stimulus_dev_rmse | dev_pearson | dev_sign_acc | rmse_wins | rmse_losses | mean_delta_rmse_model_minus_stimulus | median_delta_rmse_model_minus_stimulus | worst_regression_delta_rmse | best_gain_delta_rmse |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | physio_eeg_entropy_complexity_ridge | 2016 | 1.946368 | -0.002163 | 1.948518 | -0.004313 | 0.131747 | 0.561508 | 31 | 32 | -0.001380 | 0.004715 | 0.478246 | -0.636857 |
| arousal | physio_emg_bsl_stats_22_ridge | 2016 | 1.952492 | -0.008287 | 3.038804 | -1.094599 | 0.049813 | 0.510417 | 32 | 31 | 0.007077 | -0.001428 | 0.256049 | -0.132271 |
| arousal | physio_emg_lagged_interaction_experimental_ridge | 2016 | 1.954001 | -0.009796 | 1.954001 | -0.009796 | -0.044072 | 0.514385 | 28 | 35 | 0.010012 | 0.002840 | 0.217705 | -0.075852 |
| arousal | physio_eeg_bandpower_ridge | 2016 | 1.961104 | -0.016899 | 1.962444 | -0.018239 | 0.125466 | 0.527778 | 28 | 35 | 0.016095 | 0.007837 | 0.651327 | -0.670390 |
| arousal | physio_emg_existing_22_ridge | 2016 | 1.961861 | -0.017656 | 3.393354 | -1.449149 | 0.022147 | 0.493056 | 26 | 37 | 0.017416 | 0.004149 | 0.252239 | -0.092687 |
| arousal | physio_eeg_directed_connectivity_experimental_ridge | 2016 | 1.965883 | -0.021678 | 1.966376 | -0.022171 | 0.065170 | 0.518849 | 24 | 39 | 0.024870 | 0.022159 | 0.378490 | -0.165119 |
| arousal | physio_eeg_cov_riemannian_ridge | 2016 | 1.999370 | -0.055165 | 2.003028 | -0.058824 | 0.066770 | 0.514881 | 24 | 39 | 0.051484 | 0.032445 | 0.770769 | -0.470091 |
| arousal | physio_emg_expanded_812_ridge | 2016 | 2.046911 | -0.102706 | 485887.271514 | -485885.327309 | 0.014012 | 0.503968 | 19 | 44 | 0.099481 | 0.048081 | 1.730852 | -0.167015 |
| valence | physio_emg_lagged_interaction_experimental_ridge | 2016 | 1.259152 | -0.001378 | 1.259152 | -0.001378 | 0.002204 | 0.481647 | 29 | 34 | 0.001183 | 0.001928 | 0.031385 | -0.038733 |
| valence | physio_emg_existing_22_ridge | 2016 | 1.259185 | -0.001411 | 3.279431 | -2.021658 | 0.051050 | 0.496032 | 25 | 38 | 0.000956 | 0.002651 | 0.046581 | -0.097168 |
| valence | physio_emg_bsl_stats_22_ridge | 2016 | 1.263148 | -0.005374 | 1.839976 | -0.582202 | -0.021511 | 0.477679 | 25 | 38 | 0.004678 | 0.001554 | 0.167810 | -0.037329 |
| valence | physio_eeg_entropy_complexity_ridge | 2016 | 1.278739 | -0.020966 | 1.278753 | -0.020979 | -0.009649 | 0.510913 | 24 | 39 | 0.021403 | 0.003351 | 0.237228 | -0.102571 |
| valence | physio_eeg_directed_connectivity_experimental_ridge | 2016 | 1.282015 | -0.024242 | 1.282021 | -0.024248 | -0.042613 | 0.496528 | 23 | 40 | 0.023498 | 0.013433 | 0.418547 | -0.099481 |
| valence | physio_eeg_bandpower_ridge | 2016 | 1.291352 | -0.033578 | 1.291436 | -0.033663 | -0.034817 | 0.496528 | 23 | 40 | 0.033960 | 0.017701 | 0.482059 | -0.100534 |
| valence | physio_eeg_cov_riemannian_ridge | 2016 | 1.317433 | -0.059659 | 1.322641 | -0.064867 | -0.022212 | 0.502480 | 19 | 44 | 0.049662 | 0.021816 | 1.236304 | -0.308246 |
| valence | physio_emg_expanded_812_ridge | 2016 | 1.330907 | -0.073133 | 39226.480441 | -39225.222667 | -0.013333 | 0.495536 | 21 | 42 | 0.052929 | 0.016761 | 1.891188 | -0.086114 |


## I-DARE prior baseline summary

| dataset | target | protocol | model | rmse | pearson | ccc | label_policy | accuracy | balanced_accuracy | macro_f1 | auroc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| I-DARE | arousal | leave_one_stimulus_out | subject_only | 2.384906 | 0.324873 | 0.222370 | discard_midpoint | 0.648138 | 0.586032 | 0.580583 | 0.664719 |
| I-DARE | arousal | leave_one_stimulus_out | subject_only | 2.384906 | 0.324873 | 0.222370 | midpoint_as_high | 0.604663 | 0.577390 | 0.558323 | 0.651826 |
| I-DARE | arousal | leave_one_stimulus_out | subject_only | 2.384906 | 0.324873 | 0.222370 | midpoint_as_low | 0.666667 | 0.583694 | 0.583698 | 0.647621 |
| I-DARE | arousal | leave_one_subject_out | stimulus_only | 1.944205 | 0.634375 | 0.579381 | discard_midpoint | 0.814341 | 0.786121 | 0.795276 | 0.844989 |
| I-DARE | arousal | leave_one_subject_out | stimulus_only | 1.944205 | 0.634375 | 0.579381 | midpoint_as_high | 0.759921 | 0.743164 | 0.745365 | 0.810002 |
| I-DARE | arousal | leave_one_subject_out | stimulus_only | 1.944205 | 0.634375 | 0.579381 | midpoint_as_low | 0.801091 | 0.768623 | 0.773911 | 0.816074 |
| I-DARE | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | 1.715681 | 0.731644 | 0.704979 | discard_midpoint | 0.851584 | 0.833215 | 0.839480 | 0.916427 |
| I-DARE | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | 1.715681 | 0.731644 | 0.704979 | midpoint_as_high | 0.797619 | 0.784579 | 0.788528 | 0.879835 |
| I-DARE | arousal | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | 1.715681 | 0.731644 | 0.704979 | midpoint_as_low | 0.829861 | 0.811890 | 0.811122 | 0.889332 |
| I-DARE | valence | leave_one_stimulus_out | subject_only | 2.569822 | -0.059524 | -0.017809 | discard_midpoint | 0.503899 | 0.506650 | 0.499516 | 0.439200 |
| I-DARE | valence | leave_one_stimulus_out | subject_only | 2.569822 | -0.059524 | -0.017809 | midpoint_as_high | 0.477679 | 0.492940 | 0.477521 | 0.436728 |
| I-DARE | valence | leave_one_stimulus_out | subject_only | 2.569822 | -0.059524 | -0.017809 | midpoint_as_low | 0.525298 | 0.508786 | 0.508284 | 0.456774 |
| I-DARE | valence | leave_one_subject_out | stimulus_only | 1.257774 | 0.866307 | 0.858090 | discard_midpoint | 0.956209 | 0.955885 | 0.956148 | 0.981840 |
| I-DARE | valence | leave_one_subject_out | stimulus_only | 1.257774 | 0.866307 | 0.858090 | midpoint_as_high | 0.888393 | 0.897339 | 0.886520 | 0.953116 |
| I-DARE | valence | leave_one_subject_out | stimulus_only | 1.257774 | 0.866307 | 0.858090 | midpoint_as_low | 0.866071 | 0.879559 | 0.865804 | 0.943286 |
| I-DARE | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | 1.236653 | 0.871171 | 0.864579 | discard_midpoint | 0.955609 | 0.955239 | 0.955541 | 0.984216 |
| I-DARE | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | 1.236653 | 0.871171 | 0.864579 | midpoint_as_high | 0.888889 | 0.897354 | 0.886950 | 0.957570 |
| I-DARE | valence | leave_one_subject_stimulus_pair_out | subject_stimulus_additive_loo_cell | 1.236653 | 0.871171 | 0.864579 | midpoint_as_low | 0.864583 | 0.878422 | 0.864342 | 0.951987 |


## Recommended next action

Do not start another architecture search yet. First, treat this as a negative/near-null feature audit and decide whether to: (1) write up the stimulus-prior finding, or (2) run one stricter confirmatory residual test with permutation/bootstrap and a small number of neuroscience-motivated features.
