# I-DARE 06a1y Split-Control Deep Learning Probe


## Purpose

This diagnostic reruns a previous-model-style lightweight EEG residual encoder under split controls to separate weak physiology from subject/domain-shift failure.


## Decision

| target | decision | random_trial_lift | within_subject_lift | leave_one_stimulus_lift | loso_lift | best_subject_overlap_lift | overlap_minus_loso_lift_gap | fixed_eeg_bandpower_reference_lift | loso_minus_fixed_reference_lift | interpretation | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | NO_CLEAR_DEEP_PHYSIOLOGY_SIGNAL_EVEN_WITH_SUBJECT_OVERLAP | 0.0189856 | 0.0190294 | -0.0120388 | -0.00272282 | 0.0190294 | 0.0217523 | 0.0717248 | -0.0744476 | This would suggest the target/input representation is weak even before LOSO generalization. | Audit residual target identifiability and input window/feature quality before more modeling. |


## Split summary

| split | folds | n_high | subjects_high | zero_rmse_high | model_rmse_high | lift_vs_zero_high | pearson_high | sign_acc_high | mean_subject_improvement_zero_minus_model | ci95_low_mean_subject_improvement | ci95_high_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | wins_vs_zero | losses_vs_zero | ties_vs_zero | win_margin_vs_zero | missing_stimulus_prior_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| leave_one_stimulus_out | 23 | 1103 | 63 | 3.26787 | 3.27991 | -0.0120388 | 0.00218632 | 0.475068 | -0.0119731 | -0.0342297 | 0.0126839 | 0.844408 | 29 | 34 | 0 | -5 | 1 |
| loso_leave_one_subject_out | 63 | 676 | 63 | 3.33086 | 3.33358 | -0.00272282 | 0.0273822 | 0.514793 | 0.00653407 | -0.0353286 | 0.0515071 | 0.380131 | 32 | 31 | 0 | 1 | 0 |
| random_trial_kfold_subjects_overlap | 5 | 708 | 63 | 3.29769 | 3.2787 | 0.0189856 | 0.126245 | 0.564972 | 0.030853 | -0.00136284 | 0.0657595 | 0.0435478 | 36 | 27 | 0 | 9 | 0 |
| within_subject_trial_kfold_subjects_overlap | 5 | 691 | 63 | 3.32698 | 3.30795 | 0.0190294 | 0.114568 | 0.536903 | 0.0247853 | -0.0175555 | 0.0707235 | 0.141993 | 37 | 26 | 0 | 11 | 0 |


## 05ajb fixed reference

| source | abs_residual_threshold | fixed_reference_residual_rmse | fixed_reference_lift_vs_zero | fixed_reference_residual_pearson | fixed_reference_block | fixed_reference_model |
| --- | --- | --- | --- | --- | --- | --- |
| docs/roca/idare_high_disagreement_direct_deviation_confirmatory_stats_current_verdict.csv | 2.20968 | 3.16841 | 0.0717248 | 0.212972 | eeg_bandpower | physio_eeg_bandpower_ridge |


## Next steps

| priority | step | title | purpose | success_condition |
| --- | --- | --- | --- | --- |
| 1 | 06a2 | Subject-adaptive residual representation | If subject-overlap works but LOSO fails, add explicit subject/domain adaptation instead of blindly scaling architecture. | Improves high-disagreement arousal under LOSO and then improves/matches locked B2 with paired subject support. |
| 2 | 06a3 | Residual identifiability and label-noise bound | Quantify whether single-trial subjective residuals have enough repeatable structure for physiology learning. | Upper/lower bounds explain whether model capacity can realistically help under LOSO. |
| 3 | 06a4 | Subject-normalization and calibration ablation | Test per-subject EEG normalization, CORAL/MMD alignment, and k-shot calibration context before larger deep models. | Reduces overlap-vs-LOSO gap without worsening high-disagreement residual metrics. |


## Notes

- Target is arousal high-disagreement residual/deviation.

- The zero baseline predicts zero residual around a training-only stimulus prior when available.

- Leave-one-stimulus-out uses the training global mean as fallback for unseen stimulus IDs; inspect `missing_stimulus_prior_rate`.

- This is a diagnostic probe, not a final claim model.
