# I-DARE Direct Deviation Predictability Audit

This audit asks the core mathematical question directly:

`rating = stimulus_prior + subjective_deviation`

and tests whether the current fixed EEG/EMG feature blocks can predict the subjective deviation/residual.

## Verdict

| target | decision | best_block_by_direct_dev | best_model_by_direct_dev | best_dev_rmse | best_lift_vs_stimulus_dev_rmse | best_dev_pearson | best_dev_sign_acc | rmse_win_margin | high_residual_q75_best_block | high_residual_q75_lift_vs_zero | passes_direct_deviation_gate | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | WEAK_SIGNAL_BUT_NOT_ACTIONABLE_WITH_CURRENT_FEATURES | eeg_entropy_complexity | physio_eeg_entropy_complexity_ridge | 1.94852 | -0.00431253 | 0.131747 | 0.561508 | -1 |  |  | False | direct residual/dev RMSE lift is below practical threshold; subject-level win margin is not stable |
| valence | NO_GO_CURRENT_FIXED_FEATURES_FOR_DIRECT_DEVIATION | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 1.25915 | -0.00137846 | 0.0022038 | 0.481647 | -5 |  |  | False | direct residual/dev RMSE lift is below practical threshold; direct residual correlation is weak; subject-level win margin is not stable |


## Interpretation

- A successful physiology model must predict the residual/deviation itself, not merely correlate with the original rating.
- `NO_GO_CURRENT_FIXED_FEATURES_FOR_DIRECT_DEVIATION` means the current engineered EEG/EMG features do not provide a stable, practically useful residual predictor under the current audit.
- This does **not** prove that EEG/EMG has no usable signal. It says the current fixed-feature route is not sufficient.
- The next scientific move is either a high-disagreement residual challenge or representation learning from richer EEG/EMG signals.

Residual prediction handling: `prediction file lacks usable y_true/y_pred columns`

## Direct model metrics

| target | block | model | n | rmse | lift_vs_stimulus_rmse | dev_rmse | lift_vs_stimulus_dev_rmse | dev_pearson | dev_sign_acc | pred_dev_std | true_dev_std | rmse_wins | rmse_losses | rmse_win_margin | mean_delta_rmse_model_minus_stimulus | worst_regression_delta_rmse | best_gain_delta_rmse | passes_direct_deviation_gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | eeg_entropy_complexity | physio_eeg_entropy_complexity_ridge | 2016 | 1.94637 | -0.00216287 | 1.94852 | -0.00431253 | 0.131747 | 0.561508 | 0.542936 | 1.9442 | 31 | 32 | -1 | -0.00137992 | 0.478246 | -0.636857 | False |
| arousal | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 2016 | 1.954 | -0.00979641 | 1.954 | -0.00979641 | -0.0440718 | 0.514385 | 0.127693 | 1.9442 | 28 | 35 | -7 | 0.0100116 | 0.217705 | -0.075852 | False |
| arousal | eeg_bandpower | physio_eeg_bandpower_ridge | 2016 | 1.9611 | -0.0168994 | 1.96244 | -0.0182386 | 0.125466 | 0.527778 | 0.605425 | 1.9442 | 28 | 35 | -7 | 0.0160945 | 0.651327 | -0.67039 | False |
| arousal | eeg_directed_connectivity_experimental | physio_eeg_directed_connectivity_experimental_ridge | 2016 | 1.96588 | -0.0216776 | 1.96638 | -0.0221706 | 0.0651702 | 0.518849 | 0.4465 | 1.9442 | 24 | 39 | -15 | 0.0248705 | 0.37849 | -0.165119 | False |
| arousal | eeg_cov_riemannian | physio_eeg_cov_riemannian_ridge | 2016 | 1.99937 | -0.0551651 | 2.00303 | -0.0588235 | 0.0667697 | 0.514881 | 0.628423 | 1.9442 | 24 | 39 | -15 | 0.0514837 | 0.770769 | -0.470091 | False |
| arousal | emg_bsl_stats_22 | physio_emg_bsl_stats_22_ridge | 2016 | 1.95249 | -0.00828696 | 3.0388 | -1.0946 | 0.0498134 | 0.510417 | 2.43358 | 1.9442 | 32 | 31 | 1 | 0.00707677 | 0.256049 | -0.132271 | False |
| arousal | emg_existing_22 | physio_emg_existing_22_ridge | 2016 | 1.96186 | -0.0176556 | 3.39335 | -1.44915 | 0.0221471 | 0.493056 | 2.82419 | 1.9442 | 26 | 37 | -11 | 0.0174159 | 0.252239 | -0.0926867 | False |
| arousal | emg_expanded_812 | physio_emg_expanded_812_ridge | 2016 | 2.04691 | -0.102706 | 485887 | -485885 | 0.014012 | 0.503968 | 484701 | 1.9442 | 19 | 44 | -25 | 0.0994811 | 1.73085 | -0.167015 | False |
| valence | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 2016 | 1.25915 | -0.00137846 | 1.25915 | -0.00137846 | 0.0022038 | 0.481647 | 0.0617383 | 1.25777 | 29 | 34 | -5 | 0.00118309 | 0.0313847 | -0.0387327 | False |
| valence | eeg_entropy_complexity | physio_eeg_entropy_complexity_ridge | 2016 | 1.27874 | -0.0209657 | 1.27875 | -0.0209793 | -0.00964865 | 0.510913 | 0.218824 | 1.25777 | 24 | 39 | -15 | 0.0214025 | 0.237228 | -0.102571 | False |
| valence | eeg_directed_connectivity_experimental | physio_eeg_directed_connectivity_experimental_ridge | 2016 | 1.28202 | -0.0242416 | 1.28202 | -0.0242477 | -0.042613 | 0.496528 | 0.200155 | 1.25777 | 23 | 40 | -17 | 0.0234983 | 0.418547 | -0.0994809 | False |
| valence | eeg_bandpower | physio_eeg_bandpower_ridge | 2016 | 1.29135 | -0.0335779 | 1.29144 | -0.0336627 | -0.0348174 | 0.496528 | 0.25222 | 1.25777 | 23 | 40 | -17 | 0.0339603 | 0.482059 | -0.100534 | False |
| valence | eeg_cov_riemannian | physio_eeg_cov_riemannian_ridge | 2016 | 1.31743 | -0.0596594 | 1.32264 | -0.0648671 | -0.0222117 | 0.50248 | 0.382066 | 1.25777 | 19 | 44 | -25 | 0.0496616 | 1.2363 | -0.308246 | False |
| valence | emg_bsl_stats_22 | physio_emg_bsl_stats_22_ridge | 2016 | 1.26315 | -0.00537392 | 1.83998 | -0.582202 | -0.0215111 | 0.477679 | 1.31583 | 1.25777 | 25 | 38 | -13 | 0.0046785 | 0.16781 | -0.037329 | False |
| valence | emg_existing_22 | physio_emg_existing_22_ridge | 2016 | 1.25918 | -0.00141111 | 3.27943 | -2.02166 | 0.0510498 | 0.496032 | 3.09275 | 1.25777 | 25 | 38 | -13 | 0.000955599 | 0.0465815 | -0.0971678 | False |
| valence | emg_expanded_812 | physio_emg_expanded_812_ridge | 2016 | 1.33091 | -0.0731334 | 39226.5 | -39225.2 | -0.0133325 | 0.495536 | 39125.7 | 1.25777 | 21 | 42 | -21 | 0.0529292 | 1.89119 | -0.0861139 | False |


## High-residual subset metrics

_High-residual metrics could not be computed from the available prediction schema._


## Feature bottleneck matrix

| hypothesis | status | evidence | next_test |
| --- | --- | --- | --- |
| H1_current_fixed_EEG_EMG_features_are_insufficient | SUPPORTED_BY_CURRENT_AUDITS | 05w direct residual/dev metrics and 05ah/05ahx locked-baseline challenge do not show incremental physiology value. | representation_learning_or_raw_signal_modeling |
| H2_current_adaptation_method_is_insufficient | PARTLY_SUPPORTED | Calibration/personalization works without physiology, but fixed-feature physiology does not improve it. | physiology_as_gating_or_reliability_weighting_after_direct_deviation_test |
| H3_no_learnable_physiology_signal_exists | NOT_TESTED_AS_FINAL_CLAIM | Current audits only reject current feature/model route; they do not prove raw EEG/EMG lacks usable signal. | deep_representation_learning_and_high_disagreement_protocol |


## Recommended next steps

| priority | step | title | purpose | success_condition |
| --- | --- | --- | --- | --- |
| 1 | 05aj | High-disagreement direct deviation challenge | Restrict or weight samples where subjects disagree most with stimulus mean, then test EEG/EMG residual prediction. | Positive residual RMSE lift, positive paired subject statistics, and stable win margin. |
| 2 | 05ak | Representation-learning feasibility plan | Move beyond fixed engineered EEG/EMG features if direct deviation remains no-go. | Learned EEG/EMG representation beats fixed-feature residual models under locked evaluation. |
| 3 | 05al | Failure-subject physiology rescue | Test whether physiology helps only where locked personalization fails. | Improves failure-subject RMSE without harming pooled or paired metrics. |

