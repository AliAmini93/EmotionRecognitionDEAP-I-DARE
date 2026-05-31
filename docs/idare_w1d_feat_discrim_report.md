# W1D Feature Discriminability Report

Generated UTC: `2026-05-11T12:32:35.423123+00:00`

## Scope

- I-DARE only.
- EEG and EMG.
- Arousal and valence.
- Read-only feature diagnostic.
- 0 training runs.
- No fusion.
- No DEAP.
- No cache overwrite.

## Inputs

- eeg_npy: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-w1d/.cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy`
- eeg_index: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-w1d/.cache/idare_eeg_cache_index_baseline_corrected.csv`
- emg_npy: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-w1d/.cache/idare_emg_features.npy`
- emg_index: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-w1d/.cache/idare_emg_feature_cache_index.csv`

## Summary

| Modality | Task | N | Features | Subjects | Label counts | Centered top-k | Within top-k | Subject/label eta2 ratio | Stability Jaccard | Diagnosis |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|---|
| EEG | valence | 2016 | 256 | 63 | 0=812, 1=1204 | 0.1066 | 0.8023 | 893.7220 | 0.3526 | `within_subject_signal_present_cross_subject_signal_collapses_subject_normalization_or_domain_generalization_priority` |
| EEG | arousal | 2016 | 256 | 63 | 0=1112, 1=904 | 0.1035 | 0.8389 | 364.0495 | 0.4229 | `within_subject_signal_present_cross_subject_signal_collapses_subject_normalization_or_domain_generalization_priority` |
| EMG | valence | 2016 | 22 | 63 | 0=812, 1=1204 | 0.0368 | 0.3568 | 890.1365 | 0.8949 | `within_subject_signal_present_cross_subject_signal_collapses_subject_normalization_or_domain_generalization_priority` |
| EMG | arousal | 2016 | 22 | 63 | 0=1112, 1=904 | 0.0322 | 0.3390 | 521.7988 | 0.8297 | `within_subject_signal_present_cross_subject_signal_collapses_subject_normalization_or_domain_generalization_priority` |

## Notes

- Cohen's d is computed on diagnostic feature summaries, not by training any classifier.
- EEG cache windows are converted into simple channel-level summary features for this diagnostic only.
- EMG uses the existing feature cache directly.
- Subject-centered effect sizes are used as the main cross-subject signal proxy.
- This report is diagnostic and cannot be treated as final model performance.
