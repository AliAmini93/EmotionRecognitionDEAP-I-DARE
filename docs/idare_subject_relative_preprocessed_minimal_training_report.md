# I-DARE Subject-relative Preprocessed Minimal Training Report

## Status

24-run minimal subject-relative preprocessed first pass complete; pending human review.

Generated UTC: `2026-05-07T16:40:30.000483+00:00`

## Run Matrix

- Modalities: `EEG`, `EMG`
- Tasks: `valence`, `arousal`
- Folds: `6`
- Seed: `11`
- Recipe: `ce_class_weighted`
- Formulation: `subject_top_bottom_quantile_q33`
- EEG preprocessing: `eeg_window_channel_zscore_train_standard_scaled`
- EMG preprocessing: `emg_signed_log1p_train_standard_scaled`

## Aggregate Comparison

| Modality | Task | Current macro F1 | Previous subject-relative macro F1 | Delta vs previous | Global-label reference macro F1 | Delta vs global ref | Current balanced acc |
|---|---|---:|---:|---:|---:|---:|---:|
| EEG | valence | 0.4961 | NA | NA | NA | NA | 0.4977 |
| EEG | arousal | 0.4792 | NA | NA | NA | NA | 0.4812 |
| EEG | ALL | 0.4876 | NA | NA | NA | NA | 0.4895 |
| EMG | valence | 0.5273 | NA | NA | NA | NA | 0.5287 |
| EMG | arousal | 0.5086 | NA | NA | NA | NA | 0.5120 |
| EMG | ALL | 0.5180 | NA | NA | NA | NA | 0.5204 |

## Diagnosis

- Diagnosis: `preprocessed_subject_relative_first_pass_not_sufficient`
- Recommended next objective: `subject_relative_feature_engineering_objective`
- Mean macro-F1 across modality-level ALL rows: `0.5028`
- Mean delta macro-F1 vs previous subject-relative minimal run: `NA`
- Max one-class prediction count per modality/task: `0`

## Output Files

- `docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json`
- `docs/idare_subject_relative_preprocessed_minimal_eeg_primary.md`
- `docs/idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv`
- `docs/idare_subject_relative_preprocessed_minimal_emg_primary.json`
- `docs/idare_subject_relative_preprocessed_minimal_emg_primary.md`
- `docs/idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv`
- `docs/idare_subject_relative_preprocessed_minimal_training_report.json`

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- mainline change
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- balanced-sampler second pass
- BSL-stats sidecars

## Next Allowed Step

Human review / closeout before optional second pass, feature engineering, or stopping.
