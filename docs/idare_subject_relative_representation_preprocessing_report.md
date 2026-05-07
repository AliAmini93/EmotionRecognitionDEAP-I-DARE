# I-DARE Subject-relative Representation/Preprocessing Report

## Status

Read-only representation/preprocessing diagnostic complete; pending human review.

Generated UTC: `2026-05-07T16:31:11.473066+00:00`

No new performance training was run.

## Diagnostic Summary

- Diagnosis: `preprocessing_candidate_worth_testing`
- Recommended next objective: `minimal_subject_relative_preprocessed_training_objective`
- Best candidate: `emg_signed_log1p_train_standard_scaled`
- Best candidate modality: `EMG`
- Diagnostic score: `0.5220`
- Mean shift reduction vs raw: `0.2173`
- Mean validation-separation gain vs raw: `-0.0071`

## Candidate Ranking

| Rank | Modality | Candidate | Raw baseline | Shift reduction vs raw | Val sep gain vs raw | Domain shift | Val class sep | Leakage risk | Implementation risk | Score |
|---:|---|---|---:|---:|---:|---:|---:|---|---|---:|
| 1 | EMG | `emg_signed_log1p_train_standard_scaled` | False | 0.2173 | -0.0071 | 0.1931 | 0.0966 | low | low | 0.5220 |
| 2 | EMG | `emg_record_l2_normalized` | False | 0.2155 | -0.0023 | 0.1949 | 0.1014 | low | medium | 0.4709 |
| 3 | EEG | `eeg_window_channel_zscore_train_standard_scaled` | False | 0.0868 | 0.0048 | 0.1286 | 0.1079 | low | low | 0.2738 |
| 4 | EEG | `eeg_window_channel_zscore_summary` | False | 0.0868 | 0.0048 | 0.1286 | 0.1079 | low | medium | 0.2238 |
| 5 | EMG | `emg_train_robust_scaled` | False | -0.0000 | 0.0000 | 0.4104 | 0.1037 | low | low | 0.0910 |
| 6 | EMG | `emg_raw_features` | True | 0.0000 | 0.0000 | 0.4104 | 0.1037 | low | low | 0.0910 |
| 7 | EMG | `emg_train_standard_scaled` | False | 0.0000 | -0.0000 | 0.4104 | 0.1037 | low | low | 0.0910 |
| 8 | EEG | `eeg_summary_train_robust_scaled` | False | -0.0000 | 0.0000 | 0.2154 | 0.1031 | low | low | 0.0907 |
| 9 | EEG | `eeg_summary_train_standard_scaled` | False | -0.0000 | 0.0000 | 0.2154 | 0.1031 | low | low | 0.0907 |
| 10 | EEG | `eeg_summary_raw` | True | 0.0000 | 0.0000 | 0.2154 | 0.1031 | low | low | 0.0907 |

## Label Audit

| Modality | Task | Rating column | Valid subjects | Valid samples | Class 0 | Class 1 |
|---|---|---|---:|---:|---:|---:|
| EEG | valence | `valence_score` | 63 | 1629 | 829 | 800 |
| EEG | arousal | `arousal_score` | 62 | 1643 | 846 | 797 |
| EMG | valence | `valence_score` | 63 | 1629 | 829 | 800 |
| EMG | arousal | `arousal_score` | 62 | 1643 | 846 | 797 |

## Output Files

- `docs/idare_subject_relative_preprocessing_candidate_matrix.csv`
- `docs/idare_subject_relative_distribution_shift_summary.csv`
- `docs/idare_subject_relative_representation_preprocessing_report.json`

## Interpretation

At least one low-leakage preprocessing candidate has enough diagnostic support to justify a small separately authorized training test.

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

Human review / closeout before any minimal preprocessed training objective or feature-engineering objective.
