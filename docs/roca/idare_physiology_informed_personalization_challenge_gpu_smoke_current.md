# I-DARE GPU Physiology-Informed Personalization Challenge

This is the CUDA/PyTorch version of the 05ah challenge. It keeps the scientific target locked: EEG/EMG must beat the B2 `kernel_residual_shrink4` personalization baseline, not merely `stimulus_only`.

Backend: `cuda:0`; PyTorch `2.11.0+cu128`.

GPU: `NVIDIA GeForce RTX 5090`.


## Verdict

| target | decision | best_block | best_model | best_k_calibration | best_rmse | locked_reference_rmse | best_lift_vs_locked_rmse | rmse_win_margin_vs_locked | mean_delta_rmse_model_minus_locked | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_GO_PHYSIOLOGY_VS_LOCKED_PERSONALIZATION_GPU | emg_existing_22 | physio_residual_ridge1000 | 4 | 2.439631 | 2.039192 | -0.400439 | -2.000000 | 0.356739 | physiology-informed models do not improve over locked B2 personalization baseline; pooled lift < 0.02; subject win margin < 3; mean subject RMSE delta is not better than locked baseline |
| valence | WEAK_GO_PHYSIOLOGY_VS_LOCKED_NEEDS_CONFIRMATION_GPU | emg_lagged_interaction_experimental | physio_similarity_knn64 | 4 | 1.287580 | 1.291436 | 0.003855 | 0.000000 | 0.001548 | pooled lift < 0.02; subject win margin < 3; mean subject RMSE delta is not better than locked baseline |


## Best physiology-informed rows by lift over locked B2

| target | block | k_calibration | model | n | rmse | locked_reference_rmse | lift_vs_locked_rmse | pearson | ccc | rmse_wins_vs_locked | rmse_losses_vs_locked | rmse_win_margin_vs_locked | mean_delta_rmse_model_minus_locked |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | emg_existing_22 | 4 | physio_residual_ridge1000 | 2240 | 2.439631 | 2.039192 | -0.400439 | 0.314125 | 0.268785 | 3.000000 | 5.000000 | -2.000000 | 0.356739 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_residual_ridge1000 | 2240 | 2.461572 | 2.016189 | -0.445383 | 0.290349 | 0.245741 | 2.000000 | 6.000000 | -4.000000 | 0.419675 |
| arousal | emg_existing_22 | 4 | physio_similarity_knn64 | 2240 | 2.485212 | 2.039192 | -0.446020 | 0.305533 | 0.261451 | 1.000000 | 7.000000 | -6.000000 | 0.404985 |
| arousal | eeg_entropy_complexity | 4 | physio_similarity_knn64 | 2240 | 2.538481 | 2.071609 | -0.466872 | 0.257390 | 0.222035 | 1.000000 | 7.000000 | -6.000000 | 0.434145 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_similarity_knn64 | 2240 | 2.498086 | 2.016189 | -0.481898 | 0.294922 | 0.257121 | 1.000000 | 7.000000 | -6.000000 | 0.452965 |
| arousal | eeg_entropy_complexity | 4 | physio_residual_ridge1000 | 2240 | 2.554073 | 2.071609 | -0.482464 | 0.263558 | 0.234690 | 0.000000 | 8.000000 | -8.000000 | 0.466559 |
| arousal | emg_existing_22 | 4 | physio_context_ridge1000 | 2240 | 2.554395 | 2.039192 | -0.515202 | -0.029517 | -0.011957 | 0.000000 | 8.000000 | -8.000000 | 0.503713 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_context_ridge100 | 2240 | 2.573962 | 2.016189 | -0.557773 | 0.147271 | 0.110876 | 0.000000 | 8.000000 | -8.000000 | 0.534680 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_residual_ridge100 | 2240 | 2.580459 | 2.016189 | -0.564270 | 0.231958 | 0.203645 | 1.000000 | 7.000000 | -6.000000 | 0.533093 |
| arousal | emg_lagged_interaction_experimental | 4 | physio_context_ridge1000 | 2240 | 2.588212 | 2.016189 | -0.572023 | -0.152705 | -0.053628 | 0.000000 | 8.000000 | -8.000000 | 0.569742 |
| arousal | emg_existing_22 | 4 | physio_context_ridge100 | 2240 | 2.618198 | 2.039192 | -0.579006 | 0.193711 | 0.164717 | 2.000000 | 6.000000 | -4.000000 | 0.489728 |
| arousal | emg_existing_22 | 4 | physio_residual_ridge100 | 2240 | 2.646344 | 2.039192 | -0.607152 | 0.259154 | 0.241448 | 2.000000 | 6.000000 | -4.000000 | 0.499177 |
| arousal | eeg_entropy_complexity | 4 | physio_context_ridge1000 | 2240 | 2.684674 | 2.071609 | -0.613064 | -0.072986 | -0.043781 | 0.000000 | 8.000000 | -8.000000 | 0.618503 |
| arousal | emg_existing_22 | 16 | physio_residual_ridge1000 | 1280 | 2.398013 | 1.776498 | -0.621516 | 0.318256 | 0.272744 | 3.000000 | 5.000000 | -2.000000 | 0.586851 |
| arousal | emg_existing_22 | 16 | physio_similarity_knn64 | 1280 | 2.448082 | 1.776498 | -0.671584 | 0.308435 | 0.264286 | 2.000000 | 6.000000 | -4.000000 | 0.640534 |
| arousal | emg_lagged_interaction_experimental | 16 | physio_residual_ridge1000 | 1280 | 2.518752 | 1.838899 | -0.679853 | 0.279053 | 0.234195 | 2.000000 | 6.000000 | -4.000000 | 0.662421 |
| arousal | emg_lagged_interaction_experimental | 16 | physio_similarity_knn64 | 1280 | 2.554126 | 1.838899 | -0.715226 | 0.283331 | 0.245687 | 1.000000 | 7.000000 | -6.000000 | 0.694064 |
| arousal | eeg_entropy_complexity | 16 | physio_similarity_knn64 | 1280 | 2.533003 | 1.804906 | -0.728097 | 0.272342 | 0.235478 | 3.000000 | 5.000000 | -2.000000 | 0.689622 |
| arousal | emg_existing_22 | 16 | physio_context_ridge1000 | 1280 | 2.506282 | 1.776498 | -0.729784 | -0.013124 | -0.005410 | 0.000000 | 8.000000 | -8.000000 | 0.725773 |
| arousal | eeg_entropy_complexity | 16 | physio_residual_ridge1000 | 1280 | 2.555007 | 1.804906 | -0.750101 | 0.278012 | 0.249425 | 2.000000 | 6.000000 | -4.000000 | 0.731384 |
| arousal | eeg_entropy_complexity | 4 | physio_residual_ridge100 | 2240 | 2.833480 | 2.071609 | -0.761871 | 0.205811 | 0.199886 | 0.000000 | 8.000000 | -8.000000 | 0.733889 |
| arousal | eeg_entropy_complexity | 4 | physio_context_ridge100 | 2240 | 2.843733 | 2.071609 | -0.772124 | 0.126165 | 0.117677 | 0.000000 | 8.000000 | -8.000000 | 0.746159 |
| arousal | emg_lagged_interaction_experimental | 16 | physio_context_ridge100 | 1280 | 2.633034 | 1.838899 | -0.794134 | 0.136666 | 0.102785 | 2.000000 | 6.000000 | -4.000000 | 0.781528 |
| arousal | emg_lagged_interaction_experimental | 16 | physio_residual_ridge100 | 1280 | 2.640747 | 1.838899 | -0.801848 | 0.221277 | 0.193735 | 2.000000 | 6.000000 | -4.000000 | 0.781271 |
| arousal | emg_lagged_interaction_experimental | 16 | physio_context_ridge1000 | 1280 | 2.641272 | 1.838899 | -0.802373 | -0.162578 | -0.056827 | 0.000000 | 8.000000 | -8.000000 | 0.808322 |
| arousal | emg_existing_22 | 16 | physio_context_ridge100 | 1280 | 2.581988 | 1.776498 | -0.805490 | 0.198953 | 0.171088 | 1.000000 | 7.000000 | -6.000000 | 0.722363 |
| arousal | emg_existing_22 | 16 | physio_residual_ridge100 | 1280 | 2.615340 | 1.776498 | -0.838842 | 0.261645 | 0.244587 | 1.000000 | 7.000000 | -6.000000 | 0.737536 |
| arousal | eeg_entropy_complexity | 16 | physio_context_ridge1000 | 1280 | 2.700993 | 1.804906 | -0.896087 | -0.065035 | -0.039689 | 0.000000 | 8.000000 | -8.000000 | 0.903870 |
| arousal | eeg_entropy_complexity | 16 | physio_residual_ridge100 | 1280 | 2.817500 | 1.804906 | -1.012594 | 0.234281 | 0.228533 | 0.000000 | 8.000000 | -8.000000 | 0.982598 |
| arousal | eeg_entropy_complexity | 16 | physio_context_ridge100 | 1280 | 2.827944 | 1.804906 | -1.023038 | 0.153709 | 0.144037 | 0.000000 | 8.000000 | -8.000000 | 0.999929 |
| valence | emg_lagged_interaction_experimental | 4 | physio_similarity_knn64 | 2240 | 1.287580 | 1.291436 | 0.003855 | 0.876753 | 0.873116 | 4.000000 | 4.000000 | 0.000000 | 0.001548 |
| valence | emg_lagged_interaction_experimental | 4 | physio_residual_ridge1000 | 2240 | 1.287875 | 1.291436 | 0.003561 | 0.876448 | 0.872223 | 4.000000 | 4.000000 | 0.000000 | 0.001806 |
| valence | emg_lagged_interaction_experimental | 4 | physio_residual_ridge100 | 2240 | 1.298816 | 1.291436 | -0.007380 | 0.874397 | 0.870500 | 5.000000 | 3.000000 | 2.000000 | 0.012004 |
| valence | emg_existing_22 | 4 | physio_residual_ridge1000 | 2240 | 1.299954 | 1.275886 | -0.024068 | 0.874624 | 0.870481 | 3.000000 | 5.000000 | -2.000000 | 0.032016 |
| valence | eeg_entropy_complexity | 4 | physio_similarity_knn64 | 2240 | 1.308759 | 1.284219 | -0.024540 | 0.872766 | 0.868840 | 4.000000 | 4.000000 | 0.000000 | 0.032461 |
| valence | emg_lagged_interaction_experimental | 16 | physio_similarity_knn64 | 1280 | 1.289020 | 1.262970 | -0.026050 | 0.875693 | 0.872290 | 3.000000 | 5.000000 | -2.000000 | 0.039397 |
| valence | emg_lagged_interaction_experimental | 16 | physio_residual_ridge1000 | 1280 | 1.292204 | 1.262970 | -0.029234 | 0.874717 | 0.870672 | 4.000000 | 4.000000 | 0.000000 | 0.042738 |
| valence | emg_existing_22 | 4 | physio_similarity_knn64 | 2240 | 1.305401 | 1.275886 | -0.029515 | 0.873764 | 0.869535 | 4.000000 | 4.000000 | 0.000000 | 0.035836 |
| valence | emg_existing_22 | 16 | physio_residual_ridge1000 | 1280 | 1.316787 | 1.282540 | -0.034247 | 0.868782 | 0.865135 | 3.000000 | 5.000000 | -2.000000 | 0.050129 |
| valence | emg_existing_22 | 16 | physio_similarity_knn64 | 1280 | 1.318185 | 1.282540 | -0.035645 | 0.868600 | 0.864913 | 4.000000 | 4.000000 | 0.000000 | 0.048737 |


## Interpretation

- `GO_PHYSIOLOGY_BEATS_LOCKED_PERSONALIZATION_GPU` means EEG/EMG adds incremental value over the locked personalized B2 baseline.

- `NO_GO_PHYSIOLOGY_VS_LOCKED_PERSONALIZATION_GPU` means the tested physiology features do not yet improve over the locked personalization baseline.

- This GPU step is intentionally documented separately from CPU 05ah to preserve reproducibility and backend comparability.
