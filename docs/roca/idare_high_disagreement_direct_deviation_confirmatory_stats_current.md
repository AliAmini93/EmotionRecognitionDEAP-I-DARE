# I-DARE High-Disagreement Direct-Deviation Confirmatory Statistics

This report locks the exploratory 05aj high-disagreement physiology signal and tests it with paired subject-level bootstrap, sign-flip, sign-test, and residual-prediction permutation checks.

Positive improvement means `zero residual baseline RMSE - physiology residual-model RMSE`; positive is good for physiology.

## Confirmatory verdict

| target | decision | quantile | feature_block | model | n | subjects | baseline_residual_rmse | model_residual_rmse | pooled_lift_vs_zero_residual_rmse | residual_pearson | residual_sign_acc | mean_subject_improvement_baseline_minus_model | ci95_low_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | permutation_p_alignment | wins | losses | win_margin | passes_confirmatory_gate | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | GO_CONFIRMED_HIGH_DISAGREEMENT_PHYSIOLOGY | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 508 | 63 | 3.240139 | 3.168414 | 0.071725 | 0.212972 | 0.557087 | 0.099588 | 0.010963 | 0.018849 | 4.999750e-05 | 35 | 28 | 7 | True | candidate passes pooled, paired subject-level, sign-flip, permutation, and correlation gates |
| valence | WEAK_OR_NO_GO_HIGH_DISAGREEMENT_PHYSIOLOGY | 0.750000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 505 | 63 | 2.118605 | 2.116596 | 0.002009 | 0.047266 | 0.487129 | 0.004321 | -0.002194 | 0.106495 | 0.057297 | 29 | 34 | -5 | False | pooled residual RMSE lift <= 0.02; bootstrap CI lower bound is not > 0; sign-flip p is not < 0.05; permutation p is not < 0.05; win margin < 3; residual Pearson <= 0.1 |


## Sensitivity curve for locked candidates

| target | quantile | feature_block | model | n | baseline_residual_rmse | model_residual_rmse | pooled_lift_vs_zero_residual_rmse | residual_pearson | residual_sign_acc | ci95_low_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | permutation_p_alignment | wins | losses | win_margin | passes_confirmatory_gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0.500000 | eeg_bandpower | physio_eeg_bandpower_ridge | 1008 | 2.622719 | 2.588825 | 0.033894 | 0.172998 | 0.548611 | -0.025493 | 0.127294 | 4.999750e-05 | 33 | 30 | 3 | False |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 508 | 3.240139 | 3.168414 | 0.071725 | 0.212972 | 0.557087 | 0.010963 | 0.018849 | 4.999750e-05 | 35 | 28 | 7 | True |
| arousal | 0.900000 | eeg_bandpower | physio_eeg_bandpower_ridge | 209 | 4.025323 | 3.935624 | 0.089699 | 0.215804 | 0.583732 | 0.066182 | 0.002450 | 4.999750e-05 | 35 | 20 | 15 | True |
| valence | 0.500000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 1015 | 1.701274 | 1.701292 | -1.818118e-05 | 0.021723 | 0.488670 | -0.002774 | 0.285736 | 0.104595 | 28 | 35 | -7 | False |
| valence | 0.750000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 505 | 2.118605 | 2.116596 | 0.002009 | 0.047266 | 0.487129 | -0.002194 | 0.106495 | 0.057297 | 29 | 34 | -5 | False |
| valence | 0.900000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 202 | 2.655947 | 2.653743 | 0.002204 | 0.049463 | 0.450495 | -0.008719 | 0.245538 | 0.078746 | 25 | 33 | -8 | False |


## Permutation summary

| target | quantile | feature_block | model | permutation_p_alignment | signflip_p_one_sided_mean_gt_zero | sign_test_p_one_sided_wins_gt_losses | pooled_lift_vs_zero_residual_rmse | mean_subject_improvement_baseline_minus_model | ci95_low_mean_subject_improvement | wins | losses | win_margin | passes_confirmatory_gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0.500000 | eeg_bandpower | physio_eeg_bandpower_ridge | 4.999750e-05 | 0.127294 | 0.400653 | 0.033894 | 0.039439 | -0.025493 | 33 | 30 | 3 | False |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 4.999750e-05 | 0.018849 | 0.224981 | 0.071725 | 0.099588 | 0.010963 | 35 | 28 | 7 | True |
| arousal | 0.900000 | eeg_bandpower | physio_eeg_bandpower_ridge | 4.999750e-05 | 0.002450 | 0.029032 | 0.089699 | 0.185609 | 0.066182 | 35 | 20 | 15 | True |
| valence | 0.500000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.104595 | 0.285736 | 0.843248 | -1.818118e-05 | 0.001314 | -0.002774 | 28 | 35 | -7 | False |
| valence | 0.750000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.057297 | 0.106495 | 0.775019 | 0.002009 | 0.004321 | -0.002194 | 29 | 34 | -5 | False |
| valence | 0.900000 | emg_lagged_interaction_experimental | physio_emg_lagged_interaction_experimental_ridge | 0.078746 | 0.245538 | 0.881476 | 0.002204 | 0.008103 | -0.008719 | 25 | 33 | -8 | False |


## Worst failure subjects for primary candidate

| target | quantile | feature_block | model | subject_id | baseline_residual_rmse | model_residual_rmse | improvement_baseline_minus_model | delta_rmse_model_minus_baseline |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 59 | 3.506077 | 4.071364 | -0.565286 | 0.565286 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 32 | 2.362816 | 2.916966 | -0.554150 | 0.554150 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 56 | 2.415292 | 2.888138 | -0.472846 | 0.472846 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 43 | 2.778691 | 3.181042 | -0.402351 | 0.402351 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 41 | 3.610984 | 3.941015 | -0.330032 | 0.330032 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 8 | 2.780179 | 3.103904 | -0.323725 | 0.323725 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 62 | 3.477411 | 3.766789 | -0.289378 | 0.289378 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 30 | 2.467742 | 2.747573 | -0.279831 | 0.279831 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 50 | 2.508155 | 2.766984 | -0.258829 | 0.258829 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 40 | 3.798886 | 4.014273 | -0.215387 | 0.215387 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 42 | 3.685246 | 3.881165 | -0.195920 | 0.195920 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 17 | 2.636976 | 2.830317 | -0.193341 | 0.193341 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 46 | 3.304961 | 3.462213 | -0.157252 | 0.157252 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 6 | 4.379451 | 4.515882 | -0.136430 | 0.136430 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 29 | 2.585924 | 2.714970 | -0.129047 | 0.129047 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 34 | 2.303047 | 2.413170 | -0.110123 | 0.110123 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 21 | 3.029623 | 3.139445 | -0.109822 | 0.109822 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 22 | 3.096914 | 3.194804 | -0.097890 | 0.097890 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 19 | 3.100795 | 3.196479 | -0.095684 | 0.095684 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 25 | 3.568759 | 3.646450 | -0.077692 | 0.077692 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 15 | 3.007812 | 3.076594 | -0.068782 | 0.068782 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 24 | 2.276320 | 2.328400 | -0.052080 | 0.052080 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 54 | 2.668103 | 2.719188 | -0.051085 | 0.051085 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 39 | 3.051462 | 3.090905 | -0.039443 | 0.039443 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 52 | 3.337034 | 3.375473 | -0.038439 | 0.038439 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 44 | 3.665941 | 3.695127 | -0.029185 | 0.029185 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 7 | 2.661458 | 2.685594 | -0.024136 | 0.024136 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 47 | 3.523932 | 3.547694 | -0.023762 | 0.023762 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 57 | 3.447972 | 3.447019 | 0.000953 | -0.000953 |
| arousal | 0.750000 | eeg_bandpower | physio_eeg_bandpower_ridge | 12 | 2.313940 | 2.309998 | 0.003942 | -0.003942 |


## Interpretation

- If arousal/q75/eeg_bandpower passes here, the claim is still scoped: EEG bandpower contains a confirmed high-disagreement arousal residual signal under the current fixed-feature audit.

- This does not yet mean EEG beats the locked personalized kernel baseline; it means the residual signal is real enough to justify representation-learning or physiology-assisted calibration follow-up.

- If it fails, 05aj should be treated as exploratory only and not used as a scientific claim.
