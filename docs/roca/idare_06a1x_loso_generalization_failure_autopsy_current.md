# I-DARE LOSO generalization failure autopsy

## Purpose

This diagnostic tries to localize why the previous deep residual model failed under LOSO: weak residual signal, subject/domain shift, residual variance structure, or model/training instability.

## Decision table

| diagnostic_item | finding | key_number | interpretation | action |
| --- | --- | --- | --- | --- |
| previous_deep_model_result | PREVIOUS_DEEP_MODEL_UNDERPERFORMS_SIMPLE_FIXED_BANDPOWER_SIGNAL | -0.0563594 | The old deep EEGSegmentEncoder residual probe did not beat zero residual or the fixed EEG-bandpower high-disagreement reference. | Do not continue blind architecture search on the same LOSO residual target. |
| random_vs_loso_split_control | MIXED_SPLIT_CONTROL_RESULT_REQUIRES_REVIEW | 0.0366775 | This checks whether residual predictability appears only when subjects overlap between train and test. | If subject-overlap works but LOSO fails, prioritize domain adaptation/subject normalization; if both fail, prioritize representation/target audit. |
| residual_variance_structure | SUBJECT_STYLE_EXPLAINS_NONTRIVIAL_RESIDUAL_VARIANCE_CALIBRATION_IS_STRUCTURALLY_NEEDED | 0.269176 | A large subject-mean residual component means physiology has to solve a subject-style/calibration problem, not just decode stimulus emotion. | Keep B2 personalization as required baseline; use physiology only if it adds beyond subject calibration. |
| confirmed_positive_pocket | AROUSAL_HIGH_DISAGREEMENT_FIXED_EEG_BANDPOWER_SIGNAL_IS_REAL_BUT_WEAK | 0.0717248 | The positive pocket exists, but it has not bridged into global personalization or failure rescue. | Use it as a diagnostic/gating signal, not yet as an additive correction. |


## Split-control metrics

| split | folds | alpha | n_all | n_high | zero_rmse_all | model_rmse_all | lift_vs_zero_all | pearson_all | sign_acc_all | zero_rmse_high | model_rmse_high | lift_vs_zero_high | pearson_high | sign_acc_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_trial_kfold_subjects_overlap | 5 | 100 | 2016 | 508 | 1.9442 | 1.8528 | 0.0914047 | 0.317877 | 0.60119 | 3.24014 | 2.90605 | 0.334087 | 0.49844 | 0.708661 |
| within_subject_trial_kfold_subjects_overlap | 5 | 100 | 2016 | 508 | 1.9442 | 1.85522 | 0.0889819 | 0.313934 | 0.604167 | 3.24014 | 2.91131 | 0.328831 | 0.49558 | 0.716535 |
| loso_leave_one_subject_out | 63 | 100 | 2016 | 508 | 1.9442 | 2.09215 | -0.147945 | 0.075018 | 0.513889 | 3.24014 | 3.20346 | 0.0366775 | 0.166714 | 0.574803 |
| leave_one_stimulus_out | 32 | 100 | 2016 | 508 | 1.9442 | 1.84063 | 0.103578 | 0.331497 | 0.602183 | 3.24014 | 2.88802 | 0.352122 | 0.515765 | 0.728346 |


## Residual variance decomposition

| quantity | variance | proportion_of_total |
| --- | --- | --- |
| raw_rating_total | 6.32327 | 1 |
| raw_rating_subject_mean_component | 0.985425 | 0.155841 |
| raw_rating_stimulus_mean_component | 2.66238 | 0.421045 |
| leave_subject_out_deviation_total | 3.77993 | 1 |
| deviation_subject_mean_component | 1.01747 | 0.269176 |
| deviation_stimulus_mean_component | 1.16643e-32 | 3.08584e-33 |


## Next steps

| priority | step | title | purpose | success_condition |
| --- | --- | --- | --- | --- |
| 1 | 06a1y | Split-control learning probe | Train the same lightweight model under random/within-subject/LOSO splits to isolate whether the failure is subject shift or weak signal. | Subject-overlap success plus LOSO failure proves generalization/domain shift; failure in all splits points to representation/target weakness. |
| 2 | 06a2 | Subject-adaptive residual representation | If split controls show subject shift, add explicit subject adaptation rather than larger generic CNNs. | Improves beyond B2 locked or matches B2 with fewer calibration samples under paired subject gates. |
| 3 | 06a3 | Residual identifiability and label-noise bound | Quantify whether single-trial subjective residuals have enough repeatable structure to support learning. | A clear upper bound explains whether more model capacity can realistically help. |
