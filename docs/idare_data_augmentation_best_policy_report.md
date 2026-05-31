# I-DARE Data Augmentation Best Policy Report

| target | modality | da_policy | runs | mean_balanced_accuracy | std_balanced_accuracy | mean_accuracy | mean_macro_f1 | one_class_collapse_count | baseline_mean_balanced_accuracy | delta_vs_no_aug_baseline | moderate_pass | strong_pass | fold_wins_vs_baseline | consistent_enough |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| arousal | EEG | E4_time_channel_masking_or_dropout | 6 | 0.555382 | 0.026641 | 0.556439 | 0.548124 | 0 | 0.536486 | 0.018896 | True | True | 4 | True |
| arousal | EMG | M2_feature_gaussian_jitter_medium | 6 | 0.469185 | 0.018954 | 0.476799 | 0.463251 | 0 | 0.467619 | 0.001567 | False | False | 4 | True |
| valence | EEG | E2_additive_gaussian_noise_medium | 6 | 0.499815 | 0.026942 | 0.502841 | 0.493154 | 0 | 0.497950 | 0.001865 | False | False | 5 | True |
| valence | EMG | M1_feature_gaussian_jitter_weak | 6 | 0.509199 | 0.026752 | 0.502225 | 0.493439 | 0 | 0.507676 | 0.001524 | False | False | 3 | False |
