# I-DARE Subject-relative Preprocessed Minimal EEG Primary

## Status

Primary first-pass matrix complete.

Generated UTC: `2026-05-07T16:38:05.309243+00:00`

## Setup

- Formulation: `subject_top_bottom_quantile_q33`
- Preprocessing: `eeg_window_channel_zscore_train_standard_scaled`
- Recipe: `ce_class_weighted`
- Runs: `12`

## Aggregate Results

| Task | Runs | Mean macro F1 | Mean balanced accuracy |
|---|---:|---:|---:|
| valence | 6 | 0.4961 | 0.4977 |
| arousal | 6 | 0.4792 | 0.4812 |
| ALL | 12 | 0.4876 | 0.4895 |

## Output Files

- `docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json`
- `docs/idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv`
