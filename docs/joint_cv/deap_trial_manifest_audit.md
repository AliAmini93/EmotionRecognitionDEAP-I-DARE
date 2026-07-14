# DEAP Canonical Physical-Trial Manifest Audit

No model training or fold construction was performed.

## Summary

- Manifest: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/docs/joint_cv/deap_trial_manifest.csv`
- Audit passed: `True`
- Rows: `1280`
- Columns: `32`
- Subjects: `32`
- Verified/non-missing stimuli: `0`
- Trials per subject: `40..40`
- Duplicate trial IDs: `0`
- Missing stimulus IDs: `1280`
- Chronology-unverified rows: `1280`
- Missing EEG rows: `0`
- Missing EMG rows: `0`

## Label Policy Counts

| task | policy | low_0 | high_1 | discard_or_missing |
| --- | --- | --- | --- | --- |
| valence | discard_midpoint | 556 | 708 | 16 |
| valence | midpoint_as_low | 572 | 708 | 0 |
| valence | midpoint_as_high | 556 | 724 | 0 |
| arousal | discard_midpoint | 526 | 737 | 17 |
| arousal | midpoint_as_low | 543 | 737 | 0 |
| arousal | midpoint_as_high | 526 | 754 | 0 |

## Issues

- None.

## Warnings

- DEAP physical-trial manifest is valid for subject-held-out analyses only; stimulus-held-out and Strict Joint folds remain blocked.