# ROCA-I-DARE Joint Valence/Arousal Subject-Macro Diagnostic Report

No model training was performed here. This report merges full LOSO Valence and Arousal predictions.

## Evaluation levels

- `pooled_trial`: metrics over all 2016 trials pooled together.
- `subject`: metrics computed separately for each held-out subject over that subject's 32 trials.
- `subject_macro_summary`: mean/median/std/min/max of subject-level metrics across subjects.

## Label definitions

- Valence high: `valence_score > 5`
- Arousal high: `arousal_score > 5`
- Joint classes: `LV_LA`, `LV_HA`, `HV_LA`, `HV_HA`

## Pooled trial-level metrics

| scope | model_group | task | n | subjects | accuracy | balanced_accuracy | macro_f1 | weighted_f1 | mcc | cohen_kappa | auroc | average_precision | accuracy_lift_vs_majority | dimension_hamming_accuracy | both_dimensions_correct_rate | neither_dimension_correct_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pooled_trial | eeg_gaussian10_oracle | valence_high_low | 2016 | 63 | 0.8661 | 0.8799 | 0.8658 | 0.8667 | 0.7526 | 0.7348 | 0.9521 | 0.9211 | 0.2902 |  |  |  |
| pooled_trial | eeg_gaussian10_oracle | arousal_high_low | 2016 | 63 | 0.8041 | 0.7776 | 0.7800 | 0.8032 | 0.5603 | 0.5600 | 0.8551 | 0.7443 | 0.1448 |  |  |  |
| pooled_trial | eeg_gaussian10_oracle | joint_4class_valence_arousal | 2016 | 63 | 0.6880 | 0.6444 | 0.6424 | 0.6737 | 0.5744 | 0.5605 |  |  | 0.3557 | 0.8351 | 0.6880 | 0.0179 |
| pooled_trial | stimulus_only | valence_high_low | 2016 | 63 | 0.8661 | 0.8796 | 0.8658 | 0.8667 | 0.7518 | 0.7347 | 0.9433 | 0.8997 | 0.2902 |  |  |  |
| pooled_trial | stimulus_only | arousal_high_low | 2016 | 63 | 0.8011 | 0.7686 | 0.7739 | 0.7989 | 0.5494 | 0.5482 | 0.8161 | 0.6678 | 0.1419 |  |  |  |
| pooled_trial | stimulus_only | joint_4class_valence_arousal | 2016 | 63 | 0.6840 | 0.6309 | 0.6321 | 0.6696 | 0.5672 | 0.5531 |  |  | 0.3517 | 0.8336 | 0.6840 | 0.0169 |


## Subject-macro summary

| scope | model_group | task | subjects | accuracy_mean | accuracy_median | balanced_accuracy_mean | balanced_accuracy_median | macro_f1_mean | macro_f1_median | mcc_mean | cohen_kappa_mean | auroc_mean | dimension_hamming_accuracy_mean | both_dimensions_correct_rate_mean | neither_dimension_correct_rate_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| subject_macro_summary | eeg_gaussian10_oracle | arousal_high_low | 63 | 0.8041 | 0.8125 | 0.8040 | 0.8182 | 0.7580 | 0.8057 | 0.5998 | 0.5809 | 0.8782 |  |  |  |
| subject_macro_summary | eeg_gaussian10_oracle | joint_4class_valence_arousal | 63 | 0.6880 | 0.6875 | 0.6833 | 0.6766 | 0.6082 | 0.6328 | 0.5902 | 0.5622 |  | 0.8351 | 0.6880 | 0.0179 |
| subject_macro_summary | eeg_gaussian10_oracle | valence_high_low | 63 | 0.8661 | 0.8750 | 0.8870 | 0.8784 | 0.8647 | 0.8745 | 0.7597 | 0.7358 | 0.9589 |  |  |  |
| subject_macro_summary | stimulus_only | arousal_high_low | 63 | 0.8011 | 0.8438 | 0.8056 | 0.8237 | 0.7555 | 0.8129 | 0.6058 | 0.5795 | 0.8780 |  |  |  |
| subject_macro_summary | stimulus_only | joint_4class_valence_arousal | 63 | 0.6840 | 0.6562 | 0.6806 | 0.6893 | 0.6079 | 0.6252 | 0.5863 | 0.5575 |  | 0.8336 | 0.6840 | 0.0169 |
| subject_macro_summary | stimulus_only | valence_high_low | 63 | 0.8661 | 0.8750 | 0.8868 | 0.8784 | 0.8647 | 0.8745 | 0.7587 | 0.7355 | 0.9579 |  |  |  |


## Pooled EEG vs stimulus-only comparison

| scope | test_subject | task | eeg_accuracy | stimulus_accuracy | delta_accuracy_eeg_minus_stimulus | eeg_balanced_accuracy | stimulus_balanced_accuracy | delta_balanced_accuracy_eeg_minus_stimulus | eeg_macro_f1 | stimulus_macro_f1 | delta_macro_f1_eeg_minus_stimulus | eeg_mcc | stimulus_mcc | delta_mcc_eeg_minus_stimulus |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pooled_trial |  | valence_high_low | 0.8661 | 0.8661 | 0.0000 | 0.8799 | 0.8796 | 0.0003 | 0.8658 | 0.8658 | 0.0000 | 0.7526 | 0.7518 | 0.0008 |
| pooled_trial |  | arousal_high_low | 0.8041 | 0.8011 | 0.0030 | 0.7776 | 0.7686 | 0.0089 | 0.7800 | 0.7739 | 0.0061 | 0.5603 | 0.5494 | 0.0109 |
| pooled_trial |  | joint_4class_valence_arousal | 0.6880 | 0.6840 | 0.0040 | 0.6444 | 0.6309 | 0.0135 | 0.6424 | 0.6321 | 0.0103 | 0.5744 | 0.5672 | 0.0072 |


## Worst subjects by diagnostic failure score

| test_subject | failure_score | valence_high_low_delta_accuracy | valence_high_low_delta_macro_f1 | arousal_high_low_delta_accuracy | arousal_high_low_delta_macro_f1 | joint_4class_valence_arousal_delta_accuracy | joint_4class_valence_arousal_delta_macro_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 26 | 1.3621 | -0.0312 | -0.0306 | -0.0625 | -0.1338 | -0.0938 | -0.1546 |
| 63 | 0.9845 | 0.0000 | 0.0000 | -0.0938 | -0.1015 | -0.0938 | -0.1487 |
| 6 | 0.6183 | 0.0000 | 0.0000 | -0.0312 | -0.0460 | 0.0000 | -0.0033 |
| 15 | 0.4253 | 0.0000 | 0.0000 | -0.0312 | -0.0459 | -0.0312 | -0.0732 |
| 16 | 0.3634 | 0.0000 | 0.0000 | -0.0312 | -0.0423 | -0.0312 | -0.0269 |
| 25 | 0.3567 | 0.0312 | 0.0311 | -0.0625 | -0.0634 | 0.0000 | -0.0562 |
| 49 | 0.3378 | -0.0625 | -0.0605 | 0.0312 | 0.0199 | -0.0312 | -0.0323 |
| 12 | 0.2861 | -0.0312 | -0.0312 | 0.0000 | 0.0000 | -0.0312 | -0.0298 |
| 44 | 0.2836 | -0.0312 | -0.0309 | 0.0312 | 0.0253 | 0.0000 | -0.0848 |
| 23 | 0.2651 | -0.0312 | -0.0312 | 0.0000 | 0.0000 | -0.0312 | -0.0285 |
| 61 | 0.2521 | -0.0312 | -0.0311 | 0.0000 | 0.0000 | -0.0312 | -0.0245 |
| 20 | 0.2144 | 0.0000 | 0.0000 | 0.0000 | 0.0040 | -0.0312 | -0.0159 |
| 42 | 0.1916 | 0.0000 | 0.0000 | 0.0000 | -0.0015 | 0.0000 | -0.0114 |
| 47 | 0.1724 | 0.0000 | 0.0000 | -0.0312 | -0.0302 | 0.0000 | 0.0072 |
| 10 | 0.1707 | 0.0000 | 0.0000 | -0.0312 | -0.0322 | 0.0000 | -0.0167 |
| 57 | 0.1648 | -0.0312 | -0.0320 | 0.0000 | 0.0482 | 0.0000 | 0.0341 |
| 22 | 0.1490 | 0.0000 | 0.0000 | -0.0312 | -0.0317 | 0.0000 | 0.0082 |
| 37 | 0.1193 | 0.0000 | 0.0000 | 0.0000 | 0.0139 | -0.0312 | -0.0367 |
| 11 | 0.0812 | 0.0000 | 0.0000 | -0.0312 | 0.0019 | -0.0312 | 0.0048 |
| 18 | 0.0287 | 0.0000 | 0.0000 | 0.0000 | 0.0039 | 0.0312 | 0.0383 |


## Confusion matrices


### eeg_gaussian10_oracle / arousal_high_low

| actual_label | high | low |
| --- | --- | --- |
| high | 477 | 210 |
| low | 185 | 1144 |


### eeg_gaussian10_oracle / joint_4class_valence_arousal

| actual_label | HV_HA | HV_LA | LV_HA | LV_LA |
| --- | --- | --- | --- | --- |
| HV_HA | 79 | 113 | 1 | 3 |
| HV_LA | 33 | 605 | 1 | 20 |
| LV_HA | 16 | 15 | 381 | 79 |
| LV_LA | 17 | 197 | 134 | 322 |


### eeg_gaussian10_oracle / valence_high_low

| actual_label | high | low |
| --- | --- | --- |
| high | 830 | 25 |
| low | 245 | 916 |


### stimulus_only / arousal_high_low

| actual_label | high | low |
| --- | --- | --- |
| high | 458 | 229 |
| low | 172 | 1157 |


### stimulus_only / joint_4class_valence_arousal

| actual_label | HV_HA | HV_LA | LV_HA | LV_LA |
| --- | --- | --- | --- | --- |
| HV_HA | 68 | 124 | 0 | 4 |
| HV_LA | 34 | 602 | 0 | 23 |
| LV_HA | 13 | 19 | 377 | 82 |
| LV_LA | 11 | 200 | 127 | 332 |


### stimulus_only / valence_high_low

| actual_label | high | low |
| --- | --- | --- |
| high | 828 | 27 |
| low | 243 | 918 |


## Diagnostic notes

- Accuracy shows exact correctness, but can be misleading under class imbalance.
- Balanced accuracy is the mean recall over available classes and is safer when high/low are imbalanced.
- Macro-F1 weights classes equally and helps detect one-class collapse.
- MCC and Cohen's kappa are stricter agreement diagnostics; values near 0 mean weak practical classification agreement.
- Joint 4-class accuracy equals both Valence and Arousal being correct for a trial.
- Dimension hamming accuracy gives partial credit: one dimension correct = 0.5, both correct = 1.0.
- Subject-macro metrics are crucial because the protocol is cross-subject LOSO.
