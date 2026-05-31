# I-DARE Physiology After Few-Shot Calibration Audit

This audit tests whether EEG/EMG features add value after the subject has already been calibrated with a few labeled trials.

Baseline reference inside each `(target, block, k)` group is `stimulus_plus_fewshot_bias_shrink4` when available.

The full run intentionally does not write the giant predictions CSV; smoke runs with `--max-subjects` do.

## Verdict

| target | decision | best_block | best_model | best_k_calibration | best_rmse | best_lift_vs_fewshot_rmse | rmse_win_margin_vs_fewshot | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | WEAK_GO_PHYSIOLOGY_AFTER_FEWSHOT_NEEDS_CONFIRMATION | emg_lagged_interaction_experimental | stimulus_plus_fewshot_bias_plus_physio | 0 | 2.417738 | 0.080178 | 2.000000 | physiology has positive pooled lift beyond few-shot but subject-level margin or practical lift is weak |
| valence | WEAK_GO_PHYSIOLOGY_AFTER_FEWSHOT_NEEDS_CONFIRMATION | eeg_entropy_complexity | stimulus_plus_fewshot_bias_shrink4_plus_physio | 4 | 1.549040 | 0.018783 | 2.000000 | physiology has positive pooled lift beyond few-shot but subject-level margin or practical lift is weak |


## Best physiology rows by lift vs few-shot baseline

| target | block | k_calibration | model | n | rmse | lift_vs_fewshot_rmse | pearson | ccc | fewshot_reference_model |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | emg_lagged_interaction_experimental | 0 | stimulus_plus_fewshot_bias_plus_physio | 128 | 2.417738 | 0.080178 | 0.365078 | 0.340030 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 0 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 128 | 2.417738 | 0.080178 | 0.365078 | 0.340030 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 0 | stimulus_plus_physio | 128 | 2.417738 | 0.080178 | 0.365078 | 0.340030 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 4 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 2240 | 2.084395 | 0.046757 | 0.559680 | 0.531624 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 0 | stimulus_plus_fewshot_bias_plus_physio | 128 | 2.467298 | 0.030618 | 0.340572 | 0.319141 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 0 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 128 | 2.467298 | 0.030618 | 0.340572 | 0.319141 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 0 | stimulus_plus_physio | 128 | 2.467298 | 0.030618 | 0.340572 | 0.319141 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 4 | stimulus_plus_fewshot_bias_plus_physio | 2240 | 2.110656 | 0.020496 | 0.608815 | 0.606066 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 4 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 2240 | 2.068307 | 0.017371 | 0.561051 | 0.535746 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 16 | stimulus_plus_fewshot_bias_plus_physio | 1280 | 1.941313 | 0.015955 | 0.647647 | 0.641606 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 16 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 1280 | 1.946483 | 0.010785 | 0.627213 | 0.610771 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 16 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 1280 | 1.929387 | 0.007574 | 0.644148 | 0.630540 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_existing_22 | 0 | stimulus_plus_fewshot_bias_plus_physio | 128 | 2.506266 | -0.008350 | 0.325921 | 0.307870 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_existing_22 | 0 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 128 | 2.506266 | -0.008350 | 0.325921 | 0.307870 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_existing_22 | 0 | stimulus_plus_physio | 128 | 2.506266 | -0.008350 | 0.325921 | 0.307870 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 16 | stimulus_plus_fewshot_bias_plus_physio | 1280 | 1.949553 | -0.012592 | 0.657917 | 0.653093 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_existing_22 | 4 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 2240 | 2.108592 | -0.015401 | 0.554931 | 0.530862 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 4 | stimulus_plus_fewshot_bias_plus_physio | 2240 | 2.110435 | -0.024757 | 0.612448 | 0.610906 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_existing_22 | 16 | stimulus_plus_fewshot_bias_plus_physio | 1280 | 1.996242 | -0.030023 | 0.634334 | 0.628656 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_existing_22 | 16 | stimulus_plus_fewshot_bias_shrink4_plus_physio | 1280 | 1.999109 | -0.032889 | 0.613703 | 0.598318 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_existing_22 | 4 | stimulus_plus_fewshot_bias_plus_physio | 2240 | 2.147681 | -0.054489 | 0.611335 | 0.609406 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 4 | stimulus_plus_physio | 2240 | 2.427255 | -0.296103 | 0.363132 | 0.338066 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 4 | stimulus_plus_physio | 2240 | 2.450789 | -0.365111 | 0.345188 | 0.324116 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_existing_22 | 4 | stimulus_plus_physio | 2240 | 2.500463 | -0.407272 | 0.334013 | 0.314297 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_lagged_interaction_experimental | 16 | stimulus_plus_physio | 1280 | 2.392379 | -0.455419 | 0.379610 | 0.354546 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | eeg_entropy_complexity | 16 | stimulus_plus_physio | 1280 | 2.479150 | -0.521882 | 0.328444 | 0.308281 | stimulus_plus_fewshot_bias_shrink4 |
| arousal | emg_existing_22 | 16 | stimulus_plus_physio | 1280 | 2.522760 | -0.556540 | 0.322007 | 0.303944 | stimulus_plus_fewshot_bias_shrink4 |
| valence | eeg_entropy_complexity | 4 | stimulus_plus_physio | 2240 | 1.502191 | 0.065631 | 0.838710 | 0.835531 | stimulus_plus_fewshot_bias_shrink4 |
| valence | emg_lagged_interaction_experimental | 4 | stimulus_plus_physio | 2240 | 1.531322 | 0.038783 | 0.832089 | 0.828997 | stimulus_plus_fewshot_bias_shrink4 |
| valence | eeg_entropy_complexity | 16 | stimulus_plus_physio | 1280 | 1.528226 | 0.025539 | 0.836440 | 0.832999 | stimulus_plus_fewshot_bias_shrink4 |


## Feature manifest

| block | shape | feature_dim | feature_names_preview |
| --- | --- | --- | --- |
| emg_existing_22 | [128, 22] | 22 | ['emg_existing_00', 'emg_existing_01', 'emg_existing_02', 'emg_existing_03', 'emg_existing_04', 'emg_existing_05', 'emg_existing_06', 'emg_existing_07', 'emg_existing_08', 'emg_existing_09'] |
| eeg_entropy_complexity | [128, 160] | 160 | ['eeg_mean_ch00', 'eeg_mean_ch01', 'eeg_mean_ch02', 'eeg_mean_ch03', 'eeg_mean_ch04', 'eeg_mean_ch05', 'eeg_mean_ch06', 'eeg_mean_ch07', 'eeg_mean_ch08', 'eeg_mean_ch09'] |
| emg_lagged_interaction_experimental | [128, 6] | 6 | ['emg_lag_direction_diff_1', 'emg_lag_direction_diff_5', 'emg_lag_direction_diff_10', 'emg_lag_direction_diff_25', 'emg_lag_direction_diff_50', 'emg_madiff_channel0_minus_channel1'] |


## Interpretation

- If `GO_PHYSIOLOGY_ADDS_AFTER_FEWSHOT`, physiology helps beyond subject calibration.

- If `NO_GO_PHYSIOLOGY_AFTER_FEWSHOT`, then the useful route is personalization/calibration, not the current physiology feature set.

- A positive pooled lift alone is not sufficient; subject-level win margin is also required.
