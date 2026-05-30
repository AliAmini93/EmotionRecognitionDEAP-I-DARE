# I-DARE Failure-Subject Physiology Rescue Audit

This audit asks whether the physiology signal can rescue the subjects where the locked personalized kernel-residual model still regresses relative to its locked few-shot reference.

## Decision table

| target | decision | feature_block | model | quantile | gamma_physio_blend | failure_subjects | locked_failure_rmse | candidate_failure_rmse | lift_vs_locked_failure_rmse | mean_subject_improvement_locked_minus_candidate | ci95_low_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | wins | losses | win_margin | passes_failure_rescue_gate | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_GO_FAILURE_SUBJECT_PHYSIOLOGY_RESCUE | eeg_bandpower | physio_eeg_bandpower_ridge | 0.750000 | 0.050000 | 16 | 2.430520 | 2.455475 | -0.024954 | -0.021967 | -0.036044 | 0.998800 | 4 | 12 | -8 | False | failure-subject pooled RMSE lift < 0.02; bootstrap CI lower bound is not > 0; sign-flip p is not < 0.05; win margin < 3 |
| valence | NO_GO_FAILURE_SUBJECT_PHYSIOLOGY_RESCUE | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.750000 | 0.050000 | 20 | 2.115952 | 2.116233 | -0.000280 | -0.002273 | -0.006289 | 0.858857 | 10 | 10 | 0 | False | failure-subject pooled RMSE lift < 0.02; bootstrap CI lower bound is not > 0; sign-flip p is not < 0.05; win margin < 3 |


## Top failure-rescue metrics

| target | feature_block | model | quantile | gamma_physio_blend | failure_subjects | rows | locked_failure_rmse | candidate_failure_rmse | lift_vs_locked_failure_rmse | mean_subject_improvement_locked_minus_candidate | median_subject_improvement_locked_minus_candidate | ci95_low_mean_subject_improvement | ci95_high_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | wins | losses | ties | win_margin | sign_test_p_one_sided_wins_gt_losses | passes_failure_rescue_gate | gamma_is_positive |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | eeg_bandpower | physio_eeg_bandpower_ridge | 0.750000 | 0.000000 | 16 | 16 | 2.430520 | 2.430520 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 16 | 0 |  | False | False |
| arousal | eeg_bandpower | physio_eeg_bandpower_ridge | 0.750000 | 0.050000 | 16 | 16 | 2.430520 | 2.455475 | -0.024954 | -0.021967 | -0.012133 | -0.036044 | -0.009560 | 0.998800 | 4 | 12 | 0 | -8 | 0.989365 | False | True |
| arousal | eeg_bandpower | physio_eeg_bandpower_ridge | 0.750000 | 0.100000 | 16 | 16 | 2.430520 | 2.481779 | -0.051259 | -0.044571 | -0.024449 | -0.072553 | -0.019585 | 0.998850 | 4 | 12 | 0 | -8 | 0.989365 | False | True |
| arousal | eeg_bandpower | physio_eeg_bandpower_ridge | 0.750000 | 0.200000 | 16 | 16 | 2.430520 | 2.538271 | -0.107751 | -0.091582 | -0.052771 | -0.149340 | -0.041039 | 0.999150 | 4 | 12 | 0 | -8 | 0.989365 | False | True |
| arousal | eeg_bandpower | physio_eeg_bandpower_ridge | 0.750000 | 0.350000 | 16 | 16 | 2.430520 | 2.632074 | -0.201554 | -0.166252 | -0.102255 | -0.267508 | -0.077773 | 0.999500 | 4 | 12 | 0 | -8 | 0.989365 | False | True |
| arousal | eeg_bandpower | physio_eeg_bandpower_ridge | 0.750000 | 0.500000 | 16 | 16 | 2.430520 | 2.735751 | -0.305231 | -0.245448 | -0.159686 | -0.387977 | -0.118888 | 0.999400 | 3 | 13 | 0 | -10 | 0.997910 | False | True |
| arousal | eeg_bandpower | physio_eeg_bandpower_ridge | 0.750000 | 0.750000 | 16 | 16 | 2.430520 | 2.927598 | -0.497077 | -0.386361 | -0.271429 | -0.601124 | -0.195044 | 0.999650 | 3 | 13 | 0 | -10 | 0.997910 | False | True |
| arousal | eeg_bandpower | physio_eeg_bandpower_ridge | 0.750000 | 1.000000 | 16 | 16 | 2.430520 | 3.139429 | -0.708908 | -0.537041 | -0.391773 | -0.821640 | -0.284006 | 0.999800 | 3 | 13 | 0 | -10 | 0.997910 | False | True |
| valence | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.750000 | 0.000000 | 20 | 20 | 2.115952 | 2.115952 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 1.000000 | 0 | 0 | 20 | 0 |  | False | False |
| valence | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.750000 | 0.050000 | 20 | 20 | 2.115952 | 2.116233 | -0.000280 | -0.002273 | 0.000269 | -0.006289 | 0.001350 | 0.858857 | 10 | 10 | 0 | 0 | 0.588099 | False | True |
| valence | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.750000 | 0.100000 | 20 | 20 | 2.115952 | 2.116757 | -0.000805 | -0.004739 | 0.000455 | -0.012828 | 0.002597 | 0.868707 | 10 | 10 | 0 | 0 | 0.588099 | False | True |
| valence | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.750000 | 0.200000 | 20 | 20 | 2.115952 | 2.118537 | -0.002585 | -0.010241 | 0.000408 | -0.026689 | 0.004179 | 0.883656 | 10 | 10 | 0 | 0 | 0.588099 | False | True |
| valence | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.750000 | 0.350000 | 20 | 20 | 2.115952 | 2.123030 | -0.007077 | -0.019886 | -0.000624 | -0.048641 | 0.005841 | 0.908755 | 10 | 10 | 0 | 0 | 0.588099 | False | True |
| valence | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.750000 | 0.500000 | 20 | 20 | 2.115952 | 2.129697 | -0.013744 | -0.031158 | -0.002804 | -0.072181 | 0.006510 | 0.923904 | 10 | 10 | 0 | 0 | 0.588099 | False | True |
| valence | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.750000 | 0.750000 | 20 | 20 | 2.115952 | 2.145582 | -0.029630 | -0.053418 | -0.008977 | -0.117017 | 0.002833 | 0.945203 | 10 | 10 | 0 | 0 | 0.588099 | False | True |
| valence | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.750000 | 1.000000 | 20 | 20 | 2.115952 | 2.167317 | -0.051365 | -0.079828 | -0.018304 | -0.165458 | -0.003806 | 0.961552 | 9 | 11 | 0 | -2 | 0.748278 | False | True |


## Locked failure-subject set

| target | failure_subjects |
| --- | --- |
| arousal | 16 |
| valence | 20 |


## Next steps

| priority | step | title | purpose | success_condition |
| --- | --- | --- | --- | --- |
| 1 | 05am | Physiology-assisted calibration sample reduction | Test whether physiology can reduce calibration samples even if it cannot beat the locked k=16 personalization model. | A lower-k physiology-assisted model matches locked k=16 RMSE with stable paired subject evidence. |
| 2 | 05an | Representation-learning feasibility gate | Move beyond fixed engineered EEG/EMG features if failure-subject rescue remains no-go. | Learned EEG/EMG representations beat fixed-feature physiology under the same locked gates. |
| 3 | 05ao | Targeted arousal high-disagreement model refinement | Use the confirmed arousal high-disagreement EEG-bandpower signal as a detection/triage signal rather than a direct additive correction. | A gating or uncertainty-aware model improves high-disagreement arousal without degrading locked personalization. |
