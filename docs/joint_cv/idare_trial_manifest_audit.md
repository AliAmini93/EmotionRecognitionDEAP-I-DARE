# I-DARE Canonical Physical-Trial Manifest Audit

No model training or fold construction was performed.

## Summary

- Manifest: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/docs/joint_cv/idare_trial_manifest.csv`
- Audit passed: `True`
- Rows: `2016`
- Columns: `31`
- Subjects: `63`
- Verified/non-missing stimuli: `32`
- Trials per subject: `32..32`
- Duplicate trial IDs: `0`
- Missing stimulus IDs: `0`
- Chronology-unverified rows: `0`
- Missing EEG rows: `0`
- Missing EMG rows: `0`

## Label Policy Counts

| task | policy | low_0 | high_1 | discard_or_missing |
| --- | --- | --- | --- | --- |
| valence | discard_midpoint | 812 | 855 | 349 |
| valence | midpoint_as_low | 1161 | 855 | 0 |
| valence | midpoint_as_high | 812 | 1204 | 0 |
| arousal | discard_midpoint | 1112 | 687 | 217 |
| arousal | midpoint_as_low | 1329 | 687 | 0 |
| arousal | midpoint_as_high | 1112 | 904 | 0 |

## Issues

- None.

## Warnings

- None.