# I-DARE Data Augmentation No-Augmentation Comparison

| target | modality | da_policy | runs | mean_balanced_accuracy | std_balanced_accuracy | mean_accuracy | mean_macro_f1 | one_class_collapse_count | baseline_mean_balanced_accuracy | delta_vs_no_aug_baseline | moderate_pass | strong_pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| arousal | EEG | E0_none_baseline | 6 | 0.536486 | 0.055194 | 0.542045 | 0.527337 | 0 | 0.536486 | 0.000000 | False | False |
| arousal | EEG | E1_additive_gaussian_noise_weak | 6 | 0.535900 | 0.057077 | 0.541525 | 0.526951 | 0 | 0.536486 | -0.000586 | False | False |
| arousal | EEG | E2_additive_gaussian_noise_medium | 6 | 0.539593 | 0.056751 | 0.545644 | 0.530994 | 0 | 0.536486 | 0.003108 | True | False |
| arousal | EEG | E3_amplitude_scaling | 6 | 0.535982 | 0.052530 | 0.541383 | 0.528166 | 0 | 0.536486 | -0.000504 | False | False |
| arousal | EEG | E4_time_channel_masking_or_dropout | 6 | 0.555382 | 0.026641 | 0.556439 | 0.548124 | 0 | 0.536486 | 0.018896 | True | True |
| arousal | EMG | M0_none_baseline | 6 | 0.467619 | 0.021133 | 0.475379 | 0.462267 | 0 | 0.467619 | 0.000000 | False | False |
| arousal | EMG | M1_feature_gaussian_jitter_weak | 6 | 0.467471 | 0.019862 | 0.474432 | 0.461866 | 0 | 0.467619 | -0.000148 | False | False |
| arousal | EMG | M2_feature_gaussian_jitter_medium | 6 | 0.469185 | 0.018954 | 0.476799 | 0.463251 | 0 | 0.467619 | 0.001567 | False | False |
| arousal | EMG | M3_feature_scaling | 6 | 0.464659 | 0.023067 | 0.473153 | 0.459345 | 0 | 0.467619 | -0.002960 | False | False |
| arousal | EMG | M4_feature_dropout | 6 | 0.462491 | 0.029030 | 0.473343 | 0.461446 | 0 | 0.467619 | -0.005128 | False | False |
| valence | EEG | E0_none_baseline | 6 | 0.497950 | 0.026443 | 0.500947 | 0.491460 | 0 | 0.497950 | 0.000000 | False | False |
| valence | EEG | E1_additive_gaussian_noise_weak | 6 | 0.496783 | 0.028552 | 0.500331 | 0.490436 | 0 | 0.497950 | -0.001167 | False | False |
| valence | EEG | E2_additive_gaussian_noise_medium | 6 | 0.499815 | 0.026942 | 0.502841 | 0.493154 | 0 | 0.497950 | 0.001865 | False | False |
| valence | EEG | E3_amplitude_scaling | 6 | 0.496785 | 0.027930 | 0.500379 | 0.490521 | 0 | 0.497950 | -0.001165 | False | False |
| valence | EEG | E4_time_channel_masking_or_dropout | 6 | 0.493923 | 0.020865 | 0.494271 | 0.488116 | 0 | 0.497950 | -0.004027 | False | False |
| valence | EMG | M0_none_baseline | 6 | 0.507676 | 0.025086 | 0.499763 | 0.491505 | 0 | 0.507676 | 0.000000 | False | False |
| valence | EMG | M1_feature_gaussian_jitter_weak | 6 | 0.509199 | 0.026752 | 0.502225 | 0.493439 | 0 | 0.507676 | 0.001524 | False | False |
| valence | EMG | M2_feature_gaussian_jitter_medium | 6 | 0.497714 | 0.033800 | 0.492756 | 0.482705 | 0 | 0.507676 | -0.009962 | False | False |
| valence | EMG | M3_feature_scaling | 6 | 0.503108 | 0.021206 | 0.493229 | 0.486124 | 0 | 0.507676 | -0.004568 | False | False |
| valence | EMG | M4_feature_dropout | 6 | 0.494518 | 0.026739 | 0.508239 | 0.485756 | 0 | 0.507676 | -0.013158 | False | False |
