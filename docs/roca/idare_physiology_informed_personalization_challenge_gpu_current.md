# I-DARE GPU Physiology-Informed Personalization Challenge

This is the CUDA/PyTorch version of the 05ah challenge. It keeps the scientific target locked: EEG/EMG must beat the B2 `kernel_residual_shrink4` personalization baseline, not merely `stimulus_only`.

Backend: `cuda:0`; PyTorch `2.11.0+cu128`.

GPU: `NVIDIA GeForce RTX 5090`.


## Verdict

| target | decision | best_block | best_model | best_k_calibration | best_rmse | locked_reference_rmse | best_lift_vs_locked_rmse | rmse_win_margin_vs_locked | mean_delta_rmse_model_minus_locked | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_GO_PHYSIOLOGY_VS_LOCKED_PERSONALIZATION_GPU | eeg_entropy_complexity | physio_residual_ridge1000 | 4 | 1.940719 | 1.799078 | -0.141642 | -33.000000 | 0.124976 | physiology-informed models do not improve over locked B2 personalization baseline; pooled lift < 0.02; subject win margin < 3; mean subject RMSE delta is not better than locked baseline |
| valence | NO_GO_PHYSIOLOGY_VS_LOCKED_PERSONALIZATION_GPU | emg_lagged_interaction_experimental | physio_residual_ridge1000 | 4 | 1.257912 | 1.215711 | -0.042201 | -29.000000 | 0.042181 | physiology-informed models do not improve over locked B2 personalization baseline; pooled lift < 0.02; subject win margin < 3; mean subject RMSE delta is not better than locked baseline |


## Best physiology-informed rows by lift over locked B2

| target | block | k_calibration | model | n | rmse | locked_reference_rmse | lift_vs_locked_rmse | pearson | ccc | rmse_wins_vs_locked | rmse_losses_vs_locked | rmse_win_margin_vs_locked | mean_delta_rmse_model_minus_locked |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | eeg_entropy_complexity | 4 | physio_residual_ridge1000 | 88200 | 1.940719 | 1.799078 | -0.141642 | 0.637424 | 0.592996 | 15.000000 | 48.000000 | -33.000000 | 0.124976 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_residual_ridge1000 | 88200 | 1.949914 | 1.796727 | -0.153186 | 0.631240 | 0.576922 | 13.000000 | 50.000000 | -37.000000 | 0.136399 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_residual_ridge100 | 88200 | 1.952679 | 1.796727 | -0.155951 | 0.629983 | 0.576409 | 13.000000 | 50.000000 | -37.000000 | 0.139478 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_context_ridge100 | 88200 | 1.953122 | 1.796727 | -0.156395 | 0.629448 | 0.563992 | 13.000000 | 50.000000 | -37.000000 | 0.141026 |
| arousal | eeg_bandpower | 4 | physio_residual_ridge1000 | 88200 | 1.960436 | 1.803165 | -0.157270 | 0.629052 | 0.587561 | 17.000000 | 46.000000 | -29.000000 | 0.141262 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_similarity_knn64 | 88200 | 1.954647 | 1.796727 | -0.157920 | 0.629817 | 0.581903 | 16.000000 | 47.000000 | -31.000000 | 0.143141 |
| arousal | eeg_bandpower | 4 | physio_similarity_knn64 | 88200 | 1.966272 | 1.803165 | -0.163107 | 0.624532 | 0.575213 | 14.000000 | 49.000000 | -35.000000 | 0.147005 |
| arousal | emg_bsl_stats_22 | 4 | physio_similarity_knn64 | 88200 | 1.968658 | 1.799826 | -0.168832 | 0.624790 | 0.575137 | 8.000000 | 55.000000 | -47.000000 | 0.155879 |
| arousal | eeg_entropy_complexity | 4 | physio_similarity_knn64 | 88200 | 1.974267 | 1.799078 | -0.175190 | 0.621940 | 0.574262 | 10.000000 | 53.000000 | -43.000000 | 0.157776 |
| arousal | emg_existing_22 | 4 | physio_similarity_knn64 | 88200 | 1.985712 | 1.798977 | -0.186735 | 0.615955 | 0.568160 | 10.000000 | 53.000000 | -43.000000 | 0.173242 |
| arousal | eeg_entropy_complexity | 8 | physio_residual_ridge1000 | 75600 | 1.944496 | 1.732702 | -0.211795 | 0.635692 | 0.591331 | 11.000000 | 52.000000 | -41.000000 | 0.192864 |
| arousal | eeg_entropy_complexity | 4 | physio_context_ridge1000 | 88200 | 2.014669 | 1.799078 | -0.215591 | 0.614026 | 0.477070 | 15.000000 | 48.000000 | -33.000000 | 0.201611 |
| arousal | emg_lagged_interaction_experimental | 8 | physio_residual_ridge1000 | 75600 | 1.949048 | 1.731053 | -0.217995 | 0.632431 | 0.578146 | 8.000000 | 55.000000 | -47.000000 | 0.200437 |
| arousal | emg_lagged_interaction_experimental | 8 | physio_residual_ridge100 | 75600 | 1.951714 | 1.731053 | -0.220661 | 0.631226 | 0.577716 | 8.000000 | 55.000000 | -47.000000 | 0.203416 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_context_ridge1000 | 88200 | 2.017398 | 1.796727 | -0.220671 | 0.627272 | 0.457443 | 12.000000 | 51.000000 | -39.000000 | 0.208865 |
| arousal | emg_lagged_interaction_experimental | 8 | physio_context_ridge100 | 75600 | 1.952216 | 1.731053 | -0.221163 | 0.630701 | 0.565304 | 8.000000 | 55.000000 | -47.000000 | 0.204982 |
| arousal | emg_lagged_interaction_experimental | 8 | physio_similarity_knn64 | 75600 | 1.953820 | 1.731053 | -0.222767 | 0.630982 | 0.582997 | 9.000000 | 54.000000 | -45.000000 | 0.207196 |
| arousal | eeg_entropy_complexity | 4 | physio_residual_ridge100 | 88200 | 2.027477 | 1.799078 | -0.228399 | 0.602759 | 0.570792 | 14.000000 | 49.000000 | -35.000000 | 0.208173 |
| arousal | eeg_entropy_complexity | 4 | physio_context_ridge100 | 88200 | 2.030248 | 1.799078 | -0.231171 | 0.597431 | 0.558230 | 13.000000 | 50.000000 | -37.000000 | 0.211760 |
| arousal | eeg_bandpower | 8 | physio_residual_ridge1000 | 75600 | 1.962547 | 1.729849 | -0.232697 | 0.628251 | 0.586431 | 11.000000 | 52.000000 | -41.000000 | 0.214485 |
| arousal | eeg_bandpower | 4 | physio_context_ridge1000 | 88200 | 2.037718 | 1.803165 | -0.234553 | 0.595170 | 0.470790 | 14.000000 | 49.000000 | -35.000000 | 0.218946 |
| arousal | eeg_bandpower | 8 | physio_similarity_knn64 | 75600 | 1.966767 | 1.729849 | -0.236918 | 0.624548 | 0.575093 | 11.000000 | 52.000000 | -41.000000 | 0.218901 |
| arousal | emg_bsl_stats_22 | 8 | physio_similarity_knn64 | 75600 | 1.975437 | 1.737947 | -0.237490 | 0.621088 | 0.571355 | 8.000000 | 55.000000 | -47.000000 | 0.223330 |
| arousal | eeg_entropy_complexity | 8 | physio_similarity_knn64 | 75600 | 1.977425 | 1.732702 | -0.244724 | 0.620373 | 0.572771 | 7.000000 | 56.000000 | -49.000000 | 0.224702 |
| arousal | emg_existing_22 | 8 | physio_similarity_knn64 | 75600 | 1.984563 | 1.733269 | -0.251294 | 0.617889 | 0.569546 | 8.000000 | 55.000000 | -47.000000 | 0.237575 |
| arousal | eeg_bandpower | 4 | physio_residual_ridge100 | 88200 | 2.067070 | 1.803165 | -0.263905 | 0.589514 | 0.563977 | 14.000000 | 49.000000 | -35.000000 | 0.236179 |
| arousal | eeg_bandpower | 4 | physio_context_ridge100 | 88200 | 2.070850 | 1.803165 | -0.267685 | 0.582832 | 0.551642 | 14.000000 | 49.000000 | -35.000000 | 0.239677 |
| arousal | eeg_entropy_complexity | 8 | physio_context_ridge1000 | 75600 | 2.017233 | 1.732702 | -0.284532 | 0.612292 | 0.475714 | 15.000000 | 48.000000 | -33.000000 | 0.268391 |
| arousal | emg_lagged_interaction_experimental | 8 | physio_context_ridge1000 | 75600 | 2.017165 | 1.731053 | -0.286112 | 0.628526 | 0.458596 | 10.000000 | 53.000000 | -43.000000 | 0.273127 |
| arousal | eeg_entropy_complexity | 16 | physio_residual_ridge1000 | 50400 | 1.945350 | 1.659237 | -0.286113 | 0.635163 | 0.590808 | 8.000000 | 55.000000 | -47.000000 | 0.269143 |
| arousal | emg_lagged_interaction_experimental | 16 | physio_residual_ridge1000 | 50400 | 1.948179 | 1.650906 | -0.297273 | 0.633761 | 0.579330 | 7.000000 | 56.000000 | -49.000000 | 0.282039 |
| arousal | eeg_entropy_complexity | 8 | physio_residual_ridge100 | 75600 | 2.031520 | 1.732702 | -0.298819 | 0.600921 | 0.569085 | 13.000000 | 50.000000 | -37.000000 | 0.276031 |
| arousal | emg_lagged_interaction_experimental | 16 | physio_residual_ridge100 | 50400 | 1.951011 | 1.650906 | -0.300105 | 0.632474 | 0.578797 | 7.000000 | 56.000000 | -49.000000 | 0.285145 |
| arousal | emg_lagged_interaction_experimental | 16 | physio_context_ridge100 | 50400 | 1.951684 | 1.650906 | -0.300778 | 0.631937 | 0.566339 | 7.000000 | 56.000000 | -49.000000 | 0.286848 |
| arousal | eeg_entropy_complexity | 8 | physio_context_ridge100 | 75600 | 2.034188 | 1.732702 | -0.301487 | 0.595568 | 0.556534 | 11.000000 | 52.000000 | -41.000000 | 0.279549 |
| arousal | emg_lagged_interaction_experimental | 16 | physio_similarity_knn64 | 50400 | 1.954023 | 1.650906 | -0.303117 | 0.631785 | 0.583772 | 8.000000 | 55.000000 | -47.000000 | 0.289710 |
| arousal | eeg_bandpower | 16 | physio_residual_ridge1000 | 50400 | 1.954832 | 1.649772 | -0.305060 | 0.632847 | 0.590252 | 7.000000 | 56.000000 | -49.000000 | 0.290382 |
| arousal | eeg_bandpower | 16 | physio_similarity_knn64 | 50400 | 1.960571 | 1.649772 | -0.310799 | 0.628653 | 0.578311 | 8.000000 | 55.000000 | -47.000000 | 0.296294 |
| arousal | eeg_bandpower | 8 | physio_context_ridge1000 | 75600 | 2.040664 | 1.729849 | -0.310814 | 0.593836 | 0.469150 | 10.000000 | 53.000000 | -43.000000 | 0.293314 |
| arousal | emg_bsl_stats_22 | 16 | physio_similarity_knn64 | 50400 | 1.964721 | 1.649119 | -0.315602 | 0.623524 | 0.574372 | 6.000000 | 57.000000 | -51.000000 | 0.304195 |


## Interpretation

- `GO_PHYSIOLOGY_BEATS_LOCKED_PERSONALIZATION_GPU` means EEG/EMG adds incremental value over the locked personalized B2 baseline.

- `NO_GO_PHYSIOLOGY_VS_LOCKED_PERSONALIZATION_GPU` means the tested physiology features do not yet improve over the locked personalization baseline.

- This GPU step is intentionally documented separately from CPU 05ah to preserve reproducibility and backend comparability.
