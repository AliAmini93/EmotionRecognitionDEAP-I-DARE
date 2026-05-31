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
| pooled_trial | eeg_gaussian10 | valence_high_low | 2016 | 63 | 0.8636 | 0.8774 | 0.8633 | 0.8642 | 0.7478 | 0.7299 | 0.9474 | 0.9069 | 0.2877 |  |  |  |
| pooled_trial | eeg_gaussian10 | arousal_high_low | 2016 | 63 | 0.7971 | 0.7674 | 0.7710 | 0.7956 | 0.5427 | 0.5422 | 0.8119 | 0.6798 | 0.1379 |  |  |  |
| pooled_trial | eeg_gaussian10 | joint_4class_valence_arousal | 2016 | 63 | 0.6796 | 0.6285 | 0.6267 | 0.6650 | 0.5617 | 0.5479 |  |  | 0.3472 | 0.8304 | 0.6796 | 0.0188 |
| pooled_trial | stimulus_only | valence_high_low | 2016 | 63 | 0.8661 | 0.8796 | 0.8658 | 0.8667 | 0.7518 | 0.7347 | 0.9433 | 0.8997 | 0.2902 |  |  |  |
| pooled_trial | stimulus_only | arousal_high_low | 2016 | 63 | 0.8011 | 0.7686 | 0.7739 | 0.7989 | 0.5494 | 0.5482 | 0.8161 | 0.6678 | 0.1419 |  |  |  |
| pooled_trial | stimulus_only | joint_4class_valence_arousal | 2016 | 63 | 0.6840 | 0.6309 | 0.6321 | 0.6696 | 0.5672 | 0.5531 |  |  | 0.3517 | 0.8336 | 0.6840 | 0.0169 |


## Subject-macro summary

| scope | model_group | task | subjects | accuracy_mean | accuracy_median | balanced_accuracy_mean | balanced_accuracy_median | macro_f1_mean | macro_f1_median | mcc_mean | cohen_kappa_mean | auroc_mean | dimension_hamming_accuracy_mean | both_dimensions_correct_rate_mean | neither_dimension_correct_rate_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| subject_macro_summary | eeg_gaussian10 | arousal_high_low | 63 | 0.7971 | 0.8125 | 0.8046 | 0.8125 | 0.7528 | 0.7818 | 0.6021 | 0.5749 | 0.8746 |  |  |  |
| subject_macro_summary | eeg_gaussian10 | joint_4class_valence_arousal | 63 | 0.6796 | 0.6562 | 0.6769 | 0.6861 | 0.6030 | 0.6125 | 0.5818 | 0.5523 |  | 0.8304 | 0.6796 | 0.0188 |
| subject_macro_summary | eeg_gaussian10 | valence_high_low | 63 | 0.8636 | 0.8438 | 0.8847 | 0.8784 | 0.8623 | 0.8436 | 0.7550 | 0.7310 | 0.9574 |  |  |  |
| subject_macro_summary | stimulus_only | arousal_high_low | 63 | 0.8011 | 0.8438 | 0.8056 | 0.8237 | 0.7555 | 0.8129 | 0.6058 | 0.5795 | 0.8780 |  |  |  |
| subject_macro_summary | stimulus_only | joint_4class_valence_arousal | 63 | 0.6840 | 0.6562 | 0.6806 | 0.6893 | 0.6079 | 0.6252 | 0.5863 | 0.5575 |  | 0.8336 | 0.6840 | 0.0169 |
| subject_macro_summary | stimulus_only | valence_high_low | 63 | 0.8661 | 0.8750 | 0.8868 | 0.8784 | 0.8647 | 0.8745 | 0.7587 | 0.7355 | 0.9579 |  |  |  |


## Pooled EEG vs stimulus-only comparison

| scope | test_subject | task | eeg_accuracy | stimulus_accuracy | delta_accuracy_eeg_minus_stimulus | eeg_balanced_accuracy | stimulus_balanced_accuracy | delta_balanced_accuracy_eeg_minus_stimulus | eeg_macro_f1 | stimulus_macro_f1 | delta_macro_f1_eeg_minus_stimulus | eeg_mcc | stimulus_mcc | delta_mcc_eeg_minus_stimulus |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pooled_trial |  | valence_high_low | 0.8636 | 0.8661 | -0.0025 | 0.8774 | 0.8796 | -0.0022 | 0.8633 | 0.8658 | -0.0025 | 0.7478 | 0.7518 | -0.0040 |
| pooled_trial |  | arousal_high_low | 0.7971 | 0.8011 | -0.0040 | 0.7674 | 0.7686 | -0.0013 | 0.7710 | 0.7739 | -0.0029 | 0.5427 | 0.5494 | -0.0067 |
| pooled_trial |  | joint_4class_valence_arousal | 0.6796 | 0.6840 | -0.0045 | 0.6285 | 0.6309 | -0.0025 | 0.6267 | 0.6321 | -0.0054 | 0.5617 | 0.5672 | -0.0055 |


## Worst subjects by diagnostic failure score

| test_subject | failure_score | valence_high_low_delta_accuracy | valence_high_low_delta_macro_f1 | arousal_high_low_delta_accuracy | arousal_high_low_delta_macro_f1 | joint_4class_valence_arousal_delta_accuracy | joint_4class_valence_arousal_delta_macro_f1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 17 | 1.2705 | 0.0000 | 0.0000 | -0.1562 | -0.1569 | -0.1562 | -0.1469 |
| 26 | 0.4685 | -0.0625 | -0.0613 | 0.0000 | 0.0000 | -0.0625 | -0.0508 |
| 25 | 0.4448 | -0.0312 | -0.0312 | -0.0312 | -0.0322 | -0.0312 | -0.0581 |
| 31 | 0.3632 | 0.0000 | 0.0000 | -0.0312 | -0.0359 | -0.0312 | -0.0746 |
| 64 | 0.3055 | 0.0000 | 0.0000 | -0.0312 | -0.0306 | -0.0312 | -0.0412 |
| 2 | 0.2978 | -0.0312 | -0.0309 | 0.0000 | 0.0000 | -0.0312 | -0.0400 |
| 63 | 0.2522 | -0.0312 | -0.0309 | 0.0000 | 0.0000 | -0.0312 | -0.0273 |
| 20 | 0.2479 | -0.0312 | -0.0302 | 0.0000 | 0.0000 | -0.0312 | -0.0289 |
| 47 | 0.1724 | 0.0000 | 0.0000 | -0.0312 | -0.0302 | 0.0000 | 0.0072 |
| 22 | 0.1490 | 0.0000 | 0.0000 | -0.0312 | -0.0317 | 0.0000 | 0.0082 |
| 7 | 0.1478 | 0.0000 | 0.0000 | -0.0625 | -0.0228 | 0.0000 | 0.0148 |
| 28 | 0.1457 | 0.0000 | 0.0000 | -0.0312 | -0.0350 | 0.0000 | 0.0085 |
| 35 | 0.1403 | 0.0000 | 0.0000 | -0.0312 | -0.0310 | 0.0000 | 0.0071 |
| 38 | 0.0360 | 0.0000 | 0.0000 | 0.0000 | 0.0052 | 0.0000 | -0.0360 |
| 37 | 0.0131 | 0.0000 | 0.0000 | 0.0312 | 0.0428 | 0.0000 | -0.0095 |
| 9 | 0.0066 | 0.0000 | 0.0000 | 0.0312 | 0.0349 | 0.0000 | -0.0049 |
| 15 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 16 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 13 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 12 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |


## Confusion matrices


### eeg_gaussian10 / arousal_high_low

| actual_label | high | low |
| --- | --- | --- |
| high | 463 | 224 |
| low | 185 | 1144 |


### eeg_gaussian10 / joint_4class_valence_arousal

| actual_label | HV_HA | HV_LA | LV_HA | LV_LA |
| --- | --- | --- | --- | --- |
| HV_HA | 69 | 123 | 1 | 3 |
| HV_LA | 36 | 600 | 1 | 22 |
| LV_HA | 16 | 17 | 377 | 81 |
| LV_LA | 17 | 198 | 131 | 324 |


### eeg_gaussian10 / valence_high_low

| actual_label | high | low |
| --- | --- | --- |
| high | 828 | 27 |
| low | 248 | 913 |


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
