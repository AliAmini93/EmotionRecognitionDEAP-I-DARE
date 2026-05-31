# I-DARE Midpoint/Fold/Subject-Bias Report

## Status

`complete`

## Conclusion

The audit reviewed midpoint/fold/subject-bias metadata from existing cache/index files only. No threshold was changed and no cache array was loaded for model computation.

## Subject Label-Bias Metadata

| index | label_column | subject_rate_min | subject_rate_max | subject_rate_range | subject_rate_std |
|---|---|---|---|---|---|
| .cache/idare_eeg_cache_index.csv | valence_score | 1.0 | 1.0 | 0.0 | 0.0 |
| .cache/idare_eeg_cache_index.csv | arousal_score | 1.0 | 1.0 | 0.0 | 0.0 |
| .cache/idare_eeg_cache_index.csv | valence_discard_midpoint | 0.36666666666666664 | 0.6666666666666666 | 0.3 | 0.06686245434939579 |
| .cache/idare_eeg_cache_index.csv | valence_midpoint_as_low | 0.28125 | 0.625 | 0.34375 | 0.07380712361688836 |
| .cache/idare_eeg_cache_index.csv | valence_midpoint_as_high | 0.40625 | 0.75 | 0.34375 | 0.07219264504252723 |
| .cache/idare_eeg_cache_index.csv | arousal_discard_midpoint | 0.0 | 0.9375 | 0.9375 | 0.19108832418603897 |
| .cache/idare_eeg_cache_index.csv | arousal_midpoint_as_low | 0.0 | 0.9375 | 0.9375 | 0.17410078335963888 |
| .cache/idare_eeg_cache_index.csv | arousal_midpoint_as_high | 0.0 | 0.9375 | 0.9375 | 0.18459713298265762 |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | valence_score | 1.0 | 1.0 | 0.0 | 0.0 |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | arousal_score | 1.0 | 1.0 | 0.0 | 0.0 |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | valence_discard_midpoint | 0.36666666666666664 | 0.6666666666666666 | 0.3 | 0.06686245434939579 |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | valence_midpoint_as_low | 0.28125 | 0.625 | 0.34375 | 0.07380712361688836 |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | valence_midpoint_as_high | 0.40625 | 0.75 | 0.34375 | 0.07219264504252723 |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | arousal_discard_midpoint | 0.0 | 0.9375 | 0.9375 | 0.19108832418603897 |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | arousal_midpoint_as_low | 0.0 | 0.9375 | 0.9375 | 0.17410078335963888 |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | arousal_midpoint_as_high | 0.0 | 0.9375 | 0.9375 | 0.18459713298265762 |
| .cache/idare_trial_index.csv | valence_score | 1.0 | 1.0 | 0.0 | 0.0 |
| .cache/idare_trial_index.csv | arousal_score | 1.0 | 1.0 | 0.0 | 0.0 |
| .cache/idare_trial_index.csv | valence_label_gt5 | 0.36666666666666664 | 0.6666666666666666 | 0.3 | 0.06686245434939579 |
| .cache/idare_trial_index.csv | arousal_label_gt5 | 0.0 | 0.9375 | 0.9375 | 0.19108832418603897 |
| .cache/idare_trial_index.csv | valence_is_discard_score5 |  |  |  |  |
| .cache/idare_trial_index.csv | arousal_is_discard_score5 |  |  |  |  |

## Boundary

This is metadata audit only, not an experiment.
