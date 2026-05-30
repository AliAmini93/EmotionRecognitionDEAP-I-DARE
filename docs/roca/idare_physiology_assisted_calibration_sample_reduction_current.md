# I-DARE Physiology-Assisted Calibration Sample Reduction Audit
Question: can EEG/EMG reduce the number of subject calibration samples needed to approach the locked k=16 personalization baseline?

## Decision table
| target | decision | best_lower_k_feature_block | best_lower_k_model | best_lower_k | best_lower_k_rmse | locked_B2_k16_rmse | pooled_delta_rmse_candidate_minus_locked_B2 | pooled_lift_vs_locked_B2_rmse | subjects_with_pair | ci95_high_mean_delta_candidate_minus_locked_B2 | wins_vs_locked_B2 | losses_vs_locked_B2 | win_margin_vs_locked_B2 | passes_sample_reduction_gate | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_GO_PHYSIOLOGY_ASSISTED_SAMPLE_REDUCTION | eeg_entropy_complexity | physio_residual_ridge1000 | 4 | 1.940719 | 1.657667 | 0.283052 | -0.283052 | 63 | 0.359042 | 9 | 54 | -45 | False | pooled candidate RMSE is not within +0.020 of locked k=16 B2; bootstrap upper CI for subject delta is not <= +0.020; win margin vs locked B2 is below -3 |
| valence | NO_GO_PHYSIOLOGY_ASSISTED_SAMPLE_REDUCTION | emg_lagged_interaction_experimental | physio_residual_ridge1000 | 4 | 1.257912 | 1.159189 | 0.098723 | -0.098723 | 63 | 0.146410 | 16 | 47 | -31 | False | pooled candidate RMSE is not within +0.020 of locked k=16 B2; bootstrap upper CI for subject delta is not <= +0.020; win margin vs locked B2 is below -3 |

## Criteria
- Reference: locked B2 `kernel_residual_shrink4` at k=16.
- Candidate lower-k physiology-assisted models are accepted only if pooled RMSE is within +0.020 of B2 and paired subject evidence is stable.
- This is a sample-reduction test, not a global physiology-beats-personalization test.

## Top sample-reduction metrics
| target | k_calibration | feature_block | model | candidate_rmse | locked_B2_k16_rmse | pooled_delta_rmse_candidate_minus_locked_B2 | ci95_high_mean_delta_candidate_minus_locked_B2 | wins_vs_locked_B2 | losses_vs_locked_B2 | win_margin_vs_locked_B2 | passes_sample_reduction_gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 4 | eeg_entropy_complexity | physio_residual_ridge1000 | 1.940719 | 1.657667 | 0.283052 | 0.359042 | 9 | 54 | -45 | False |
| arousal | 8 | eeg_entropy_complexity | physio_residual_ridge1000 | 1.944496 | 1.657667 | 0.286829 | 0.362576 | 8 | 55 | -47 | False |
| arousal | 16 | eeg_entropy_complexity | physio_residual_ridge1000 | 1.945350 | 1.657667 | 0.287683 | 0.365226 | 10 | 53 | -43 | False |
| arousal | 16 | emg_lagged_interaction_experimental | physio_residual_ridge1000 | 1.948179 | 1.657667 | 0.290511 | 0.368864 | 8 | 55 | -47 | False |
| arousal | 8 | emg_lagged_interaction_experimental | physio_residual_ridge1000 | 1.949048 | 1.657667 | 0.291380 | 0.372228 | 9 | 54 | -45 | False |
| arousal | 4 | emg_lagged_interaction_experimental | physio_residual_ridge1000 | 1.949914 | 1.657667 | 0.292246 | 0.370852 | 7 | 56 | -49 | False |
| arousal | 16 | emg_lagged_interaction_experimental | physio_residual_ridge100 | 1.951011 | 1.657667 | 0.293344 | 0.372970 | 8 | 55 | -47 | False |
| arousal | 16 | emg_lagged_interaction_experimental | physio_context_ridge100 | 1.951684 | 1.657667 | 0.294017 | 0.374194 | 7 | 56 | -49 | False |
| arousal | 8 | emg_lagged_interaction_experimental | physio_residual_ridge100 | 1.951714 | 1.657667 | 0.294047 | 0.372404 | 9 | 54 | -45 | False |
| arousal | 8 | emg_lagged_interaction_experimental | physio_context_ridge100 | 1.952216 | 1.657667 | 0.294549 | 0.373570 | 8 | 55 | -47 | False |
| arousal | 4 | emg_lagged_interaction_experimental | physio_residual_ridge100 | 1.952679 | 1.657667 | 0.295011 | 0.373747 | 8 | 55 | -47 | False |
| arousal | 4 | emg_lagged_interaction_experimental | physio_context_ridge100 | 1.953122 | 1.657667 | 0.295455 | 0.371330 | 6 | 57 | -51 | False |
| arousal | 8 | emg_lagged_interaction_experimental | physio_similarity_knn64 | 1.953820 | 1.657667 | 0.296153 | 0.377778 | 9 | 54 | -45 | False |
| arousal | 16 | emg_lagged_interaction_experimental | physio_similarity_knn64 | 1.954023 | 1.657667 | 0.296356 | 0.377477 | 10 | 53 | -43 | False |
| arousal | 4 | emg_lagged_interaction_experimental | physio_similarity_knn64 | 1.954647 | 1.657667 | 0.296980 | 0.376621 | 9 | 54 | -45 | False |
| arousal | 16 | eeg_bandpower | physio_residual_ridge1000 | 1.954832 | 1.657667 | 0.297164 | 0.377001 | 9 | 54 | -45 | False |
| arousal | 4 | eeg_bandpower | physio_residual_ridge1000 | 1.960436 | 1.657667 | 0.302768 | 0.383778 | 8 | 55 | -47 | False |
| arousal | 16 | eeg_bandpower | physio_similarity_knn64 | 1.960571 | 1.657667 | 0.302904 | 0.378727 | 9 | 54 | -45 | False |
| arousal | 8 | eeg_bandpower | physio_residual_ridge1000 | 1.962547 | 1.657667 | 0.304880 | 0.383459 | 7 | 56 | -49 | False |
| arousal | 16 | emg_bsl_stats_22 | physio_similarity_knn64 | 1.964721 | 1.657667 | 0.307054 | 0.381881 | 7 | 56 | -49 | False |
| arousal | 4 | eeg_bandpower | physio_similarity_knn64 | 1.966272 | 1.657667 | 0.308605 | 0.387914 | 9 | 54 | -45 | False |
| arousal | 8 | eeg_bandpower | physio_similarity_knn64 | 1.966767 | 1.657667 | 0.309100 | 0.386787 | 9 | 54 | -45 | False |
| arousal | 4 | emg_bsl_stats_22 | physio_similarity_knn64 | 1.968658 | 1.657667 | 0.310991 | 0.385617 | 6 | 57 | -51 | False |
| arousal | 4 | eeg_entropy_complexity | physio_similarity_knn64 | 1.974267 | 1.657667 | 0.316600 | 0.393538 | 8 | 55 | -47 | False |
| arousal | 8 | emg_bsl_stats_22 | physio_similarity_knn64 | 1.975437 | 1.657667 | 0.317770 | 0.394358 | 6 | 57 | -51 | False |
| arousal | 8 | eeg_entropy_complexity | physio_similarity_knn64 | 1.977425 | 1.657667 | 0.319758 | 0.394990 | 7 | 56 | -49 | False |
| arousal | 16 | eeg_entropy_complexity | physio_similarity_knn64 | 1.979473 | 1.657667 | 0.321806 | 0.398997 | 7 | 56 | -49 | False |
| arousal | 8 | emg_existing_22 | physio_similarity_knn64 | 1.984563 | 1.657667 | 0.326896 | 0.408311 | 7 | 56 | -49 | False |
| arousal | 4 | emg_existing_22 | physio_similarity_knn64 | 1.985712 | 1.657667 | 0.328045 | 0.410778 | 6 | 57 | -51 | False |
| arousal | 16 | emg_existing_22 | physio_similarity_knn64 | 1.987373 | 1.657667 | 0.329706 | 0.410500 | 6 | 57 | -51 | False |

## Interpretation
- **arousal**: NO_GO_PHYSIOLOGY_ASSISTED_SAMPLE_REDUCTION. Best lower-k candidate did not satisfy the sample-reduction gate: pooled candidate RMSE is not within +0.020 of locked k=16 B2; bootstrap upper CI for subject delta is not <= +0.020; win margin vs locked B2 is below -3.
- **valence**: NO_GO_PHYSIOLOGY_ASSISTED_SAMPLE_REDUCTION. Best lower-k candidate did not satisfy the sample-reduction gate: pooled candidate RMSE is not within +0.020 of locked k=16 B2; bootstrap upper CI for subject delta is not <= +0.020; win margin vs locked B2 is below -3.

## Next steps
| priority | step | title | purpose | success_condition |
| --- | --- | --- | --- | --- |
| 1 | 05an | Representation-learning feasibility gate | Decide whether fixed engineered EEG/EMG features are exhausted and define raw/learned representation experiments. | A learned EEG/EMG representation beats fixed-feature physiology under the same locked gates. |
| 2 | 05ao | Targeted arousal high-disagreement gating refinement | Use the confirmed arousal EEG-bandpower high-disagreement signal as a risk/gating signal rather than direct additive correction. | A gating or uncertainty-aware model improves high-disagreement arousal without degrading locked personalization. |
| 3 | 05ap | Cross-dataset physiology representation sanity check | Check whether current DEAP fixed-feature bottleneck is dataset/representation-specific by using another affective physiology dataset if available. | Physiology representation transfers or pretrains into an improved residual/deviation predictor. |
