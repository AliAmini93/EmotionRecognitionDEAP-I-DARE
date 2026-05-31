# I-DARE Physiology After Few-Shot Calibration Audit

This audit tests whether EEG/EMG features add value after the subject has already been calibrated with a few labeled trials.

Baseline reference inside each `(target, block, k)` group is `stimulus_plus_fewshot_bias_shrink4` when available.

The full run intentionally does not write the giant predictions CSV; smoke runs with `--max-subjects` do.

## Verdict

| target | decision | best_block | best_model | best_k_calibration | best_rmse | best_lift_vs_fewshot_rmse | rmse_win_margin_vs_fewshot | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_GO_PHYSIOLOGY_AFTER_FEWSHOT | emg_lagged_interaction_experimental | stimulus_plus_fewshot_bias_shrink4_plus_physio | 16 | 1.735607 | -0.000802 | -5.000000 | physiology does not improve the few-shot calibrated baseline |
| valence | NO_GO_PHYSIOLOGY_AFTER_FEWSHOT | emg_lagged_interaction_experimental | stimulus_plus_fewshot_bias_shrink4_plus_physio | 8 | 1.256356 | -0.001151 | -23.000000 | physiology does not improve the few-shot calibrated baseline |


## Best physiology rows by lift vs few-shot baseline

| target | block | k_calibration | model | n | rmse | lift_vs_fewshot_rmse | pearson | ccc | fewshot_reference_model |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | emg_lagged_interaction_experimental | 16 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 100800 | 1.735607 | -0.000802 | 0.724757 | 0.689405 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 8 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 151200 | 1.769914 | -0.000975 | 0.709754 | 0.670534 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 2 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 189000 | 1.852298 | -0.001023 | 0.676142 | 0.628350 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 4 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 176400 | 1.806024 | -0.001127 | 0.695818 | 0.652292 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 1 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 195300 | 1.888352 | -0.001307 | 0.660216 | 0.609349 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 0 | stimulus_plus_fewshot_bias_plus_physio | 2016 | 1.945514 | -0.001309 | 0.633753 | 0.578768 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 0 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 2016 | 1.945514 | -0.001309 | 0.633753 | 0.578768 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 0 | stimulus_plus_physio | 2016 | 1.945514 | -0.001309 | 0.633753 | 0.578768 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 16 | stimulus_plus_fewshot_bias_plus_physio | 100800 | 1.741764 | -0.006959 | 0.723776 | 0.699276 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_bandpower | 0 | stimulus_plus_fewshot_bias_plus_physio | 2016 | 1.951258 | -0.007053 | 0.631208 | 0.578511 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_bandpower | 0 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 2016 | 1.951258 | -0.007053 | 0.631208 | 0.578511 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_bandpower | 0 | stimulus_plus_physio | 2016 | 1.951258 | -0.007053 | 0.631208 | 0.578511 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_bandpower | 1 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 195300 | 1.894360 | -0.008713 | 0.657618 | 0.609262 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 0 | stimulus_plus_fewshot_bias_plus_physio | 2016 | 1.954020 | -0.009815 | 0.629917 | 0.577400 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 0 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 2016 | 1.954020 | -0.009815 | 0.629917 | 0.577400 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 0 | stimulus_plus_physio | 2016 | 1.954020 | -0.009815 | 0.629917 | 0.577400 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_bandpower | 2 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 189000 | 1.862736 | -0.010394 | 0.671758 | 0.626473 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_bandpower | 4 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 176400 | 1.816918 | -0.011002 | 0.691554 | 0.650578 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 2 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 189000 | 1.859816 | -0.011007 | 0.673317 | 0.627931 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 1 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 195300 | 1.898855 | -0.011140 | 0.655870 | 0.607374 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_bandpower | 8 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 151200 | 1.775290 | -0.012129 | 0.708560 | 0.672301 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 4 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 176400 | 1.817459 | -0.012340 | 0.691482 | 0.650179 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_bandpower | 16 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 100800 | 1.746300 | -0.012431 | 0.720533 | 0.687722 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 16 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 100800 | 1.747375 | -0.012518 | 0.718655 | 0.685738 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 8 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 151200 | 1.776848 | -0.012849 | 0.707755 | 0.670846 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 16 | stimulus_plus_fewshot_bias_plus_physio | 100800 | 1.756341 | -0.021484 | 0.717411 | 0.694923 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_bandpower | 16 | stimulus_plus_fewshot_bias_plus_physio | 100800 | 1.755638 | -0.021769 | 0.719108 | 0.696744 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 8 | stimulus_plus_fewshot_bias_plus_physio | 151200 | 1.794041 | -0.025102 | 0.704611 | 0.684312 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_existing_22 | 0 | stimulus_plus_fewshot_bias_plus_physio | 2016 | 1.981475 | -0.037270 | 0.617448 | 0.568944 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_existing_22 | 0 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 2016 | 1.981475 | -0.037270 | 0.617448 | 0.568944 | stimulus_plus_fewshot_bias_shrink4 |


## Feature manifest

| block | shape | feature_dim | feature_names_preview |
| --- | --- | --- | --- |
| emg_existing_22 | [2016, 22] | 22 | ['emg_existing_00', 'emg_existing_01', 'emg_existing_02', 'emg_existing_03', 'emg_existing_04', 'emg_existing_05', 'emg_existing_06', 'emg_existing_07', 'emg_existing_08', 'emg_existing_09'] |
| emg_bsl_stats_22 | [2016, 22] | 22 | ['emg_bsl_00', 'emg_bsl_01', 'emg_bsl_02', 'emg_bsl_03', 'emg_bsl_04', 'emg_bsl_05', 'emg_bsl_06', 'emg_bsl_07', 'emg_bsl_08', 'emg_bsl_09'] |
| eeg_entropy_complexity | [2016, 160] | 160 | ['eeg_mean_ch00', 'eeg_mean_ch01', 'eeg_mean_ch02', 'eeg_mean_ch03', 'eeg_mean_ch04', 'eeg_mean_ch05', 'eeg_mean_ch06', 'eeg_mean_ch07', 'eeg_mean_ch08', 'eeg_mean_ch09'] |
| eeg_bandpower | [2016, 352] | 352 | ['eeg_logbp_delta_ch00', 'eeg_logbp_delta_ch01', 'eeg_logbp_delta_ch02', 'eeg_logbp_delta_ch03', 'eeg_logbp_delta_ch04', 'eeg_logbp_delta_ch05', 'eeg_logbp_delta_ch06', 'eeg_logbp_delta_ch07', 'eeg_logbp_delta_ch08', 'eeg_logbp_delta_ch09'] |
| emg_lagged_interaction_experimental | [2016, 6] | 6 | ['emg_lag_direction_diff_1', 'emg_lag_direction_diff_5', 'emg_lag_direction_diff_10', 'emg_lag_direction_diff_25', 'emg_lag_direction_diff_50', 'emg_madiff_channel0_minus_channel1'] |


## Interpretation

- If `GO_PHYSIOLOGY_ADDS_AFTER_FEWSHOT`, physiology helps beyond subject calibration.

- If `NO_GO_PHYSIOLOGY_AFTER_FEWSHOT`, then the useful route is personalization/calibration, not the current physiology feature set.

- A positive pooled lift alone is not sufficient; subject-level win margin is also required.
