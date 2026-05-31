# I-DARE 06a1y Split-Control Deep Learning Probe


## Purpose

This diagnostic reruns a previous-model-style lightweight EEG residual encoder under split controls to separate weak physiology from subject/domain-shift failure.


## Decision

| target | decision | random_trial_lift | within_subject_lift | leave_one_stimulus_lift | loso_lift | best_subject_overlap_lift | overlap_minus_loso_lift_gap | fixed_eeg_bandpower_reference_lift | loso_minus_fixed_reference_lift | interpretation | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | MIXED_SPLIT_CONTROL_RESULT_REQUIRES_REVIEW | -0.0229219 | -0.0206453 | 0.034348 | -0.0861426 | 0.034348 | 0.120491 | 0.0717248 | -0.157867 | The split-control pattern is not clean enough for a single diagnosis. Inspect split summaries and subject outliers. | Review split-specific subject stats, then decide between subject-adaptation and target/input audit. |


## Split summary

| split | folds | n_high | subjects_high | zero_rmse_high | model_rmse_high | lift_vs_zero_high | pearson_high | sign_acc_high | mean_subject_improvement_zero_minus_model | ci95_low_mean_subject_improvement | ci95_high_mean_subject_improvement | signflip_p_one_sided_mean_gt_zero | wins_vs_zero | losses_vs_zero | ties_vs_zero | win_margin_vs_zero | missing_stimulus_prior_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| leave_one_stimulus_out | 4 | 466 | 63 | 3.17566 | 3.14131 | 0.034348 | 0.108688 | 0.564378 | 0.0325078 | 0.00850421 | 0.0572048 | 0.00354982 | 41 | 22 | 0 | 19 | 1 |
| loso_leave_one_subject_out | 4 | 44 | 4 | 3.4533 | 3.53944 | -0.0861426 | -0.178232 | 0.340909 | -0.0697679 | -0.125627 | 0.0034242 | 0.938703 | 1 | 3 | 0 | -2 | 0 |
| random_trial_kfold_subjects_overlap | 3 | 705 | 63 | 3.32005 | 3.34297 | -0.0229219 | 0.0447688 | 0.483688 | -0.0159935 | -0.0392143 | 0.00908315 | 0.885256 | 27 | 36 | 0 | -9 | 0 |
| within_subject_trial_kfold_subjects_overlap | 3 | 692 | 63 | 3.32896 | 3.34961 | -0.0206453 | 0.0799563 | 0.501445 | -0.0167381 | -0.043174 | 0.0115832 | 0.870306 | 25 | 38 | 0 | -13 | 0 |


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
