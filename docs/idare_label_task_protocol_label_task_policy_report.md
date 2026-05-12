# I-DARE Label/Task Policy Report

## Status

`complete`

## Conclusion

No final global label policy is locked. The audit classifies label/task redesign or reconciliation as the recommended next decision path before more modeling.

## Detected Label Columns

| index | label_column | nonnull | missing | counts |
|---|---|---|---|---|
| .cache/idare_eeg_cache_index.csv | valence_score | 2016 | 0 | `{"1": 283, "2.0": 188, "3.0": 155, "4.0": 186, "5.0": 349, "6.0": 241, "7.0": 247, "8.0": 190, "9.0": 177}` |
| .cache/idare_eeg_cache_index.csv | arousal_score | 2016 | 0 | `{"1": 341, "2.0": 294, "3.0": 246, "4.0": 231, "5.0": 217, "6.0": 206, "7.0": 193, "8.0": 170, "9.0": 118}` |
| .cache/idare_eeg_cache_index.csv | valence_discard_midpoint | 1667 | 349 | `{"0": 812, "1": 855}` |
| .cache/idare_eeg_cache_index.csv | valence_midpoint_as_low | 2016 | 0 | `{"0": 1161, "1": 855}` |
| .cache/idare_eeg_cache_index.csv | valence_midpoint_as_high | 2016 | 0 | `{"0": 812, "1": 1204}` |
| .cache/idare_eeg_cache_index.csv | arousal_discard_midpoint | 1799 | 217 | `{"0": 1112, "1": 687}` |
| .cache/idare_eeg_cache_index.csv | arousal_midpoint_as_low | 2016 | 0 | `{"0": 1329, "1": 687}` |
| .cache/idare_eeg_cache_index.csv | arousal_midpoint_as_high | 2016 | 0 | `{"0": 1112, "1": 904}` |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | valence_score | 2016 | 0 | `{"1": 283, "2.0": 188, "3.0": 155, "4.0": 186, "5.0": 349, "6.0": 241, "7.0": 247, "8.0": 190, "9.0": 177}` |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | arousal_score | 2016 | 0 | `{"1": 341, "2.0": 294, "3.0": 246, "4.0": 231, "5.0": 217, "6.0": 206, "7.0": 193, "8.0": 170, "9.0": 118}` |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | valence_discard_midpoint | 1667 | 349 | `{"0": 812, "1": 855}` |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | valence_midpoint_as_low | 2016 | 0 | `{"0": 1161, "1": 855}` |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | valence_midpoint_as_high | 2016 | 0 | `{"0": 812, "1": 1204}` |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | arousal_discard_midpoint | 1799 | 217 | `{"0": 1112, "1": 687}` |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | arousal_midpoint_as_low | 2016 | 0 | `{"0": 1329, "1": 687}` |
| .cache/idare_eeg_cache_index_baseline_corrected.csv | arousal_midpoint_as_high | 2016 | 0 | `{"0": 1112, "1": 904}` |
| .cache/idare_trial_index.csv | valence_score | 2016 | 0 | `{"1": 283, "2.0": 188, "3.0": 155, "4.0": 186, "5.0": 349, "6.0": 241, "7.0": 247, "8.0": 190, "9.0": 177}` |
| .cache/idare_trial_index.csv | arousal_score | 2016 | 0 | `{"1": 341, "2.0": 294, "3.0": 246, "4.0": 231, "5.0": 217, "6.0": 206, "7.0": 193, "8.0": 170, "9.0": 118}` |
| .cache/idare_trial_index.csv | valence_label_gt5 | 1667 | 349 | `{"0": 812, "1": 855}` |
| .cache/idare_trial_index.csv | arousal_label_gt5 | 1799 | 217 | `{"0": 1112, "1": 687}` |
| .cache/idare_trial_index.csv | valence_is_discard_score5 | 0 | 2016 | `{}` |
| .cache/idare_trial_index.csv | arousal_is_discard_score5 | 0 | 2016 | `{}` |

## Boundary

This report changes no thresholds and creates no model results.
