# I-DARE Label Variance Decomposition

This report measures how much of I-DARE valence/arousal is explained by stimulus identity before adding EEG/EMG features.

## Configuration

- trial_index: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/.cache/idare_trial_index.csv`
- subjects: `63`
- stimuli: `32`
- rows: `2016`
- leakage control: LOSO stimulus-only predictions use train subjects only.

## Continuous score decomposition

| target | n | subjects | stimuli | y_std | r2_stimulus_in_sample | r2_subject_in_sample | r2_subject_plus_stimulus_in_sample | unique_stimulus_r2_over_subject | unique_subject_r2_over_stimulus | loso_global_rmse | loso_stimulus_rmse | lift_stimulus_vs_global_rmse | loso_stimulus_pearson | loso_stimulus_ccc | loso_stimulus_r2_vs_loso_global | loso_stimulus_residual_std | residual_std_ratio_after_loso_stimulus |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| valence | 2016 | 63 | 32 | 2.5179 | 0.7583 | 0.0224 | 0.7807 | 0.7583 | 0.0224 | 2.5188 | 1.2578 | 1.2610 | 0.8663 | 0.8581 | 0.7506 | 1.2578 | 0.4995 |
| arousal | 2016 | 63 | 32 | 2.5146 | 0.4210 | 0.1558 | 0.5769 | 0.4210 | 0.1558 | 2.5210 | 1.9442 | 0.5768 | 0.6344 | 0.5794 | 0.4052 | 1.9442 | 0.7732 |


## Binary LOSO stimulus-only metrics

| target | label_policy | model | binary_n | accuracy | balanced_accuracy | macro_f1 | auroc | n_low | n_high | true_high_rate | pred_high_rate | lift_vs_global_accuracy | lift_vs_global_balanced_accuracy | lift_vs_global_macro_f1 | lift_vs_global_auroc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| valence | midpoint_as_low | global_train_mean | 2016 | 0.5759 | 0.5000 | 0.3654 | 0.4405 | 1161 | 855 | 0.4241 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| valence | midpoint_as_low | stimulus_only | 2016 | 0.8661 | 0.8796 | 0.8658 | 0.9433 | 1161 | 855 | 0.4241 | 0.5312 | 0.2902 | 0.3796 | 0.5004 | 0.5028 |
| valence | midpoint_as_high | global_train_mean | 2016 | 0.4028 | 0.5000 | 0.2871 | 0.4574 | 812 | 1204 | 0.5972 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| valence | midpoint_as_high | stimulus_only | 2016 | 0.8884 | 0.8973 | 0.8865 | 0.9531 | 812 | 1204 | 0.5972 | 0.5312 | 0.4856 | 0.3973 | 0.5994 | 0.4957 |
| valence | discard_midpoint | global_train_mean | 1667 | 0.4871 | 0.5000 | 0.3276 | 0.4399 | 812 | 855 | 0.5129 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| valence | discard_midpoint | stimulus_only | 1667 | 0.9562 | 0.9559 | 0.9561 | 0.9818 | 812 | 855 | 0.5129 | 0.5243 | 0.4691 | 0.4559 | 0.6286 | 0.5419 |
| arousal | midpoint_as_low | global_train_mean | 2016 | 0.6592 | 0.5000 | 0.3973 | 0.3047 | 1329 | 687 | 0.3408 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| arousal | midpoint_as_low | stimulus_only | 2016 | 0.8011 | 0.7686 | 0.7739 | 0.8161 | 1329 | 687 | 0.3408 | 0.3125 | 0.1419 | 0.2686 | 0.3766 | 0.5114 |
| arousal | midpoint_as_high | global_train_mean | 2016 | 0.5516 | 0.5000 | 0.3555 | 0.3015 | 1112 | 904 | 0.4484 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| arousal | midpoint_as_high | stimulus_only | 2016 | 0.7599 | 0.7432 | 0.7454 | 0.8100 | 1112 | 904 | 0.4484 | 0.3125 | 0.2083 | 0.2432 | 0.3899 | 0.5085 |
| arousal | discard_midpoint | global_train_mean | 1799 | 0.6181 | 0.5000 | 0.3820 | 0.2839 | 1112 | 687 | 0.3819 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| arousal | discard_midpoint | stimulus_only | 1799 | 0.8143 | 0.7861 | 0.7953 | 0.8450 | 1112 | 687 | 0.3819 | 0.3130 | 0.1962 | 0.2861 | 0.4133 | 0.5611 |


## Interpretation

- `r2_stimulus_in_sample` is descriptive: how much score variance is explainable by stimulus identity using all rows.
- `r2_subject_in_sample` is also descriptive and is not available for an unseen subject.
- `loso_stimulus_r2_vs_loso_global` is the more relevant cross-subject stimulus-prior number.
- `residual_std_ratio_after_loso_stimulus` tells how much score variation remains after removing the train-subject stimulus mean.
- A future EEG/EMG model must improve on `stimulus_only`, especially in residual metrics, not merely raw accuracy.
