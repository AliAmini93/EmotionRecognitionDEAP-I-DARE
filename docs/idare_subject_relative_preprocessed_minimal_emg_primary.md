# I-DARE Subject-relative Preprocessed Minimal EMG Primary

## Status

Primary first-pass matrix complete.

Generated UTC: `2026-05-07T16:38:05.309243+00:00`

## Setup

- Formulation: `subject_top_bottom_quantile_q33`
- Preprocessing: `emg_signed_log1p_train_standard_scaled`
- Recipe: `ce_class_weighted`
- Runs: `12`

## Aggregate Results

| Task | Runs | Mean macro F1 | Mean balanced accuracy |
|---|---:|---:|---:|
| valence | 6 | 0.5273 | 0.5287 |
| arousal | 6 | 0.5086 | 0.5120 |
| ALL | 12 | 0.5180 | 0.5204 |

## Output Files

- `docs/idare_subject_relative_preprocessed_minimal_emg_primary.json`
- `docs/idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv`
