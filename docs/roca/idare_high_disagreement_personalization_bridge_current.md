# I-DARE High-Disagreement Physiology-to-Personalization Bridge

This audit asks whether the confirmed high-disagreement physiology residual signal can improve a locked-style personalized residual baseline, rather than only improving stimulus-only residual prediction.

## Decision

| target | decision | quantile | feature_block | model | gamma_physio_blend | locked_rmse | candidate_rmse | lift_vs_locked_rmse | lift_vs_locked_residual_rmse | residual_pearson | ci95_low_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | wins | losses | win_margin | passes_bridge_gate | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_GO_PHYSIOLOGY_BRIDGE_TO_LOCKED_PERSONALIZATION | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 0.000000 | 2.622267 | 2.622267 | 0.000000 | 0.000000 | 0.670733 | 0.000000 | 1.000000 | 0 | 0 | 0 | False | pooled RMSE lift vs locked < 0.02; residual RMSE lift vs locked < 0.02; bootstrap CI lower bound is not > 0; sign-flip p is not < 0.05; win margin <= 3 |
| valence | NO_GO_PHYSIOLOGY_BRIDGE_TO_LOCKED_PERSONALIZATION | 0.750000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.000000 | 1.929769 | 1.929769 | 0.000000 | 0.000000 | 0.471549 | 0.000000 | 1.000000 | 0 | 0 | 0 | False | pooled RMSE lift vs locked < 0.02; residual RMSE lift vs locked < 0.02; bootstrap CI lower bound is not > 0; sign-flip p is not < 0.05; win margin <= 3 |


## Bridge metrics, top rows

| target | quantile | feature_block | model | gamma_physio_blend | n | subjects | locked_rmse | candidate_rmse | lift_vs_locked_rmse | locked_residual_rmse | candidate_residual_rmse | lift_vs_locked_residual_rmse | residual_pearson | mean_subject_improvement_locked_minus_candidate | median_subject_improvement_locked_minus_candidate | ci95_low_mean_subject_improvement | ci95_high_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | wins | losses | ties | win_margin | passes_bridge_gate | abs_residual_threshold | source_05ajb_passed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 0.000000 | 25250 | 63 | 2.622267 | 2.622267 | 0.000000 | 2.622267 | 2.622267 | 0.000000 | 0.670733 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 63 | 0 | False | 2.209677 | True |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 0.050000 | 25250 | 63 | 2.622267 | 2.640183 | -0.017916 | 2.622267 | 2.640183 | -0.017916 | 0.672624 | -0.016339 | -0.007567 | -0.023812 | -0.009502 | 1.000000 | 18 | 45 | 0 | -27 | False | 2.209677 | True |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 0.100000 | 25250 | 63 | 2.622267 | 2.659237 | -0.036970 | 2.622267 | 2.659237 | -0.036970 | 0.674135 | -0.033167 | -0.016891 | -0.047834 | -0.019441 | 1.000000 | 18 | 45 | 0 | -27 | False | 2.209677 | True |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 0.200000 | 25250 | 63 | 2.622267 | 2.700662 | -0.078395 | 2.622267 | 2.700662 | -0.078395 | 0.675375 | -0.068198 | -0.034431 | -0.097598 | -0.040304 | 1.000000 | 17 | 46 | 0 | -29 | False | 2.209677 | True |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 0.350000 | 25250 | 63 | 2.622267 | 2.770708 | -0.148441 | 2.622267 | 2.770708 | -0.148441 | 0.668899 | -0.123930 | -0.061925 | -0.176563 | -0.075492 | 1.000000 | 17 | 46 | 0 | -29 | False | 2.209677 | True |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 0.500000 | 25250 | 63 | 2.622267 | 2.849616 | -0.227349 | 2.622267 | 2.849616 | -0.227349 | 0.641634 | -0.183170 | -0.097452 | -0.260486 | -0.113813 | 1.000000 | 16 | 47 | 0 | -31 | False | 2.209677 | True |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 0.750000 | 25250 | 63 | 2.622267 | 2.998887 | -0.376620 | 2.622267 | 2.998887 | -0.376620 | 0.496773 | -0.288987 | -0.151356 | -0.404427 | -0.184996 | 1.000000 | 15 | 48 | 0 | -33 | False | 2.209677 | True |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 1.000000 | 25250 | 63 | 2.622267 | 3.167596 | -0.545329 | 2.622267 | 3.167596 | -0.545329 | 0.215713 | -0.402887 | -0.210048 | -0.556298 | -0.261517 | 1.000000 | 14 | 49 | 0 | -35 | False | 2.209677 | True |
| valence | 0.750000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.000000 | 25314 | 63 | 1.929769 | 1.929769 | 0.000000 | 1.929769 | 1.929769 | 0.000000 | 0.471549 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 63 | 0 | False | 1.435484 | False |
| valence | 0.750000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.050000 | 25314 | 63 | 1.929769 | 1.936272 | -0.006503 | 1.929769 | 1.936272 | -0.006503 | 0.471806 | -0.007784 | -0.006407 | -0.010405 | -0.005275 | 1.000000 | 16 | 47 | 0 | -31 | False | 1.435484 | False |
| valence | 0.750000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.100000 | 25314 | 63 | 1.929769 | 1.943109 | -0.013340 | 1.929769 | 1.943109 | -0.013340 | 0.472066 | -0.015799 | -0.012983 | -0.021054 | -0.010717 | 1.000000 | 16 | 47 | 0 | -31 | False | 1.435484 | False |
| valence | 0.750000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.200000 | 25314 | 63 | 1.929769 | 1.957776 | -0.028007 | 1.929769 | 1.957776 | -0.028007 | 0.472579 | -0.032502 | -0.026636 | -0.043226 | -0.022460 | 1.000000 | 15 | 48 | 0 | -33 | False | 1.435484 | False |
| valence | 0.750000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.350000 | 25314 | 63 | 1.929769 | 1.982197 | -0.052428 | 1.929769 | 1.982197 | -0.052428 | 0.473181 | -0.059170 | -0.048339 | -0.077744 | -0.040821 | 1.000000 | 15 | 48 | 0 | -33 | False | 1.435484 | False |
| valence | 0.750000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.500000 | 25314 | 63 | 1.929769 | 2.009430 | -0.079661 | 1.929769 | 2.009430 | -0.079661 | 0.472856 | -0.087666 | -0.071463 | -0.114967 | -0.062136 | 1.000000 | 15 | 48 | 0 | -33 | False | 1.435484 | False |
| valence | 0.750000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.750000 | 25314 | 63 | 1.929769 | 2.060756 | -0.130987 | 1.929769 | 2.060756 | -0.130987 | 0.455335 | -0.138936 | -0.117422 | -0.180508 | -0.099383 | 1.000000 | 15 | 48 | 0 | -33 | False | 1.435484 | False |
| valence | 0.750000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 1.000000 | 25314 | 63 | 1.929769 | 2.119032 | -0.189263 | 1.929769 | 2.119032 | -0.189263 | 0.046060 | -0.194541 | -0.170937 | -0.249873 | -0.142634 | 1.000000 | 14 | 49 | 0 | -35 | False | 1.435484 | False |


## Locked baseline validation

| target | reimplemented_locked_model | k_calibration | n_repeats | reimplemented_locked_full_rmse | reported_B2_locked_rmse | abs_difference_vs_reported_B2 | note |
| --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | kernel_residual_shrink4_bridge_reimplementation | 16 | 100 | 1.663750 | 1.657667 | 0.006083 | This bridge script reimplements locked-style kernel residual predictions to obtain per-trial predictions for conditional physiology tests. |
| valence | kernel_residual_shrink4_bridge_reimplementation | 16 | 100 | 1.171771 | 1.159189 | 0.012582 | This bridge script reimplements locked-style kernel residual predictions to obtain per-trial predictions for conditional physiology tests. |


## Interpretation

- A pass here would mean physiology is not merely detectable in high-disagreement residuals, but can be used as a conditional correction on top of personalization.

- A no-go here does not erase the 05ajb arousal signal; it means the current fixed-feature physiology signal is not yet strong enough to improve the locked personalized predictor.

- The locked model is reimplemented here to obtain per-trial predictions for conditional testing; compare the validation table against the reported B2 RMSE before treating this as a final locked-baseline replacement.


## Next steps

| priority | step | title | purpose | success_condition |
| --- | --- | --- | --- | --- |
| 1 | 05al | Failure-subject physiology rescue audit | Test confirmed arousal EEG-bandpower residual signal specifically on subjects where personalization still fails. | Physiology improves failure-subject RMSE without worsening pooled or paired metrics. |
| 2 | 05am | Physiology-assisted calibration sample reduction | Test whether physiology can reduce calibration samples, e.g. k=4/k=8 approaching locked k=16. | Lower-k physiology-assisted model matches locked k=16 with stable subject-level evidence. |
| 3 | 05an | Representation-learning feasibility gate | If fixed-feature physiology cannot bridge to personalization, define raw/learned EEG representation experiments. | Learned representation beats fixed-feature high-disagreement physiology under the same gates. |
