# I-DARE Physiology Challenge Synthesis

This synthesis closes the previous 05ah GPU physiology-informed personalization challenge. The locked comparison is no longer `stimulus_only`; it is the personalized `kernel_residual_shrink4` baseline.

## Final decision

| target | final_status | locked_baseline | locked_baseline_rmse | best_physiology_model | best_physiology_block | best_physiology_k | best_physiology_rmse | lift_vs_locked_rmse | win_margin_vs_locked | mean_delta_rmse_model_minus_locked | passes_incremental_physiology_gate | interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | CURRENT_PHYSIOLOGY_NO_GO_AGAINST_LOCKED_PERSONALIZATION | B2_LOCKED_kernel_residual_shrink4 | 1.657667 | physio_residual_ridge1000 | eeg_entropy_complexity | 4.000000 | 1.940719 | -0.141642 | -33.000000 | 0.124976 | False | Current fixed EEG/EMG feature blocks and the tested physiology-informed models do not add incremental value over the locked personalized kernel residual baseline. This does not prove physiology is useless; it says the current representation/modeling route is not sufficient. |
| valence | CURRENT_PHYSIOLOGY_NO_GO_AGAINST_LOCKED_PERSONALIZATION | B2_LOCKED_kernel_residual_shrink4 | 1.159189 | physio_residual_ridge1000 | emg_lagged_interaction_experimental | 4.000000 | 1.257912 | -0.042201 | -29.000000 | 0.042181 | False | Current fixed EEG/EMG feature blocks and the tested physiology-informed models do not add incremental value over the locked personalized kernel residual baseline. This does not prove physiology is useless; it says the current representation/modeling route is not sufficient. |


## Evidence table

| target | stimulus_only_rmse_B0 | fewshot_bias_shrink4_rmse_B1 | locked_kernel_residual_rmse_B2 | model_family_confirmatory_decision | physiology_gpu_decision | physiology_best_block | physiology_best_model | physiology_best_k | physiology_best_rmse | physiology_locked_reference_rmse | physiology_lift_vs_locked_rmse | physiology_win_margin_vs_locked | physiology_mean_delta_model_minus_locked |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 1.944205 | 1.733828 | 1.657667 | GO_CONFIRMED_MODEL_FAMILY_CALIBRATION | NO_GO_PHYSIOLOGY_VS_LOCKED_PERSONALIZATION_GPU | eeg_entropy_complexity | physio_residual_ridge1000 | 4.000000 | 1.940719 | 1.799078 | -0.141642 | -33.000000 | 0.124976 |
| valence | 1.257774 | 1.241848 | 1.159189 | GO_CONFIRMED_MODEL_FAMILY_CALIBRATION | NO_GO_PHYSIOLOGY_VS_LOCKED_PERSONALIZATION_GPU | emg_lagged_interaction_experimental | physio_residual_ridge1000 | 4.000000 | 1.257912 | 1.215711 | -0.042201 | -29.000000 | 0.042181 |


## Closest physiology-informed rows from 05ah GPU

| target | block | k_calibration | model | rmse | locked_reference_rmse | lift_vs_locked_rmse | rmse_win_margin_vs_locked | mean_delta_rmse_model_minus_locked | pearson | ccc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | eeg_entropy_complexity | 4 | physio_residual_ridge1000 | 1.940719 | 1.799078 | -0.141642 | -33.000000 | 0.124976 | 0.637424 | 0.592996 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_residual_ridge1000 | 1.949914 | 1.796727 | -0.153186 | -37.000000 | 0.136399 | 0.631240 | 0.576922 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_residual_ridge100 | 1.952679 | 1.796727 | -0.155951 | -37.000000 | 0.139478 | 0.629983 | 0.576409 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_context_ridge100 | 1.953122 | 1.796727 | -0.156395 | -37.000000 | 0.141026 | 0.629448 | 0.563992 |
| arousal | eeg_bandpower | 4 | physio_residual_ridge1000 | 1.960436 | 1.803165 | -0.157270 | -29.000000 | 0.141262 | 0.629052 | 0.587561 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_similarity_knn64 | 1.954647 | 1.796727 | -0.157920 | -31.000000 | 0.143141 | 0.629817 | 0.581903 |
| arousal | eeg_bandpower | 4 | physio_similarity_knn64 | 1.966272 | 1.803165 | -0.163107 | -35.000000 | 0.147005 | 0.624532 | 0.575213 |
| arousal | emg_bsl_stats_22 | 4 | physio_similarity_knn64 | 1.968658 | 1.799826 | -0.168832 | -47.000000 | 0.155879 | 0.624790 | 0.575137 |
| arousal | eeg_entropy_complexity | 4 | physio_similarity_knn64 | 1.974267 | 1.799078 | -0.175190 | -43.000000 | 0.157776 | 0.621940 | 0.574262 |
| arousal | emg_existing_22 | 4 | physio_similarity_knn64 | 1.985712 | 1.798977 | -0.186735 | -43.000000 | 0.173242 | 0.615955 | 0.568160 |
| valence | emg_lagged_interaction_experimental | 4 | physio_residual_ridge1000 | 1.257912 | 1.215711 | -0.042201 | -29.000000 | 0.042181 | 0.866720 | 0.858499 |
| valence | emg_lagged_interaction_experimental | 4 | physio_residual_ridge100 | 1.258460 | 1.215711 | -0.042749 | -29.000000 | 0.042699 | 0.866596 | 0.858399 |
| valence | emg_lagged_interaction_experimental | 4 | physio_context_ridge100 | 1.262088 | 1.215711 | -0.046377 | -23.000000 | 0.045051 | 0.866549 | 0.851618 |
| valence | emg_bsl_stats_22 | 4 | physio_similarity_knn64 | 1.263699 | 1.216158 | -0.047541 | -25.000000 | 0.047652 | 0.865045 | 0.857410 |
| valence | emg_existing_22 | 4 | physio_similarity_knn64 | 1.267195 | 1.215617 | -0.051578 | -25.000000 | 0.051915 | 0.864365 | 0.856456 |
| valence | eeg_bandpower | 4 | physio_similarity_knn64 | 1.272713 | 1.219243 | -0.053470 | -27.000000 | 0.054286 | 0.862862 | 0.854884 |
| valence | eeg_entropy_complexity | 4 | physio_similarity_knn64 | 1.271709 | 1.216896 | -0.054813 | -25.000000 | 0.054456 | 0.863092 | 0.855260 |
| valence | emg_lagged_interaction_experimental | 4 | physio_similarity_knn64 | 1.270683 | 1.215711 | -0.054972 | -29.000000 | 0.055218 | 0.863827 | 0.855941 |
| valence | eeg_entropy_complexity | 4 | physio_residual_ridge1000 | 1.277873 | 1.216896 | -0.060977 | -29.000000 | 0.061613 | 0.861650 | 0.853866 |
| valence | emg_lagged_interaction_experimental | 8 | physio_residual_ridge1000 | 1.260039 | 1.190944 | -0.069094 | -27.000000 | 0.071437 | 0.865498 | 0.857299 |


## Interpretation

- The strongest confirmed non-physiology baseline is `B2_LOCKED = kernel_residual_shrink4`.
- Current EEG/EMG feature blocks did not beat this locked personalized baseline.
- Therefore, physiology is still scientifically central, but the next claim must be stricter: EEG/EMG must predict subject-specific deviation or reduce calibration burden beyond B2.
- This result points to two likely bottlenecks: either the current fixed EEG/EMG features are insufficient, or the current adaptation/calibration formulation is not extracting the right subject-specific signal.


## Next questions

| priority | question | audit | purpose | success_condition |
| --- | --- | --- | --- | --- |
| 1 | Can physiology predict individual deviation directly? | direct_deviation_predictability_audit | Model rating - stimulus_mean directly, especially on high-disagreement stimuli. | EEG/EMG or EEG+EMG predicts deviation above locked non-physiology baselines with paired subject-level support. |
| 2 | Can physiology reduce calibration burden? | calibration_sample_reduction_challenge | Test whether physiology-assisted k=4 or k=8 can match locked k=16 personalization. | Lower-k physiology-assisted model matches or beats B2 locked k=16 without subject-level instability. |
| 3 | Can physiology rescue failure subjects? | failure_subject_physiology_rescue | Focus on subjects where locked personalization still regresses. | Physiology improves failure-subject RMSE while preserving pooled metrics. |
| 4 | Are current hand-crafted EEG/EMG features the bottleneck? | representation_learning_plan | If direct deviation remains no-go, move from fixed features to learned representations. | Feature-learning method beats fixed-feature physiology against the locked challenge baseline. |
