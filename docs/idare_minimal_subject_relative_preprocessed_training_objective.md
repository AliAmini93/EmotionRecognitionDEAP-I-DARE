# I-DARE Minimal Subject-relative Preprocessed Training Objective

## Status

Short-term diagnostic training objective created.

Created/updated UTC: `2026-05-07T16:34:01.007092+00:00`

This objective authorizes only a small 24-run first pass. It does not authorize final LOSO claims, fusion, mainline changes, architecture work, augmentation, domain generalization, or broad hyperparameter search.

## Why This Objective Exists

The subject-relative representation/preprocessing diagnostic was reviewed.

The diagnostic identified a low-leakage preprocessing candidate worth minimal testing.

## Authorized Scope

- Total runs: `24`
- Modalities: `EEG`, `EMG`
- Tasks: `valence`, `arousal`
- Folds: `6`
- Seed: `11`
- Recipe: `ce_class_weighted` only
- Label formulation: `subject_top_bottom_quantile_q33`

## Preprocessing Candidates

| Modality | Candidate | Description | Diagnostic source rank |
|---|---|---|---:|
| EEG | `eeg_window_channel_zscore_train_standard_scaled` | per-trial channel zscore summary features plus train-only standard scaling | 3 |
| EMG | `emg_signed_log1p_train_standard_scaled` | signed log1p EMG features plus train-only standard scaling | 1 |

## Authorized Work

- Create a small reviewed implementation/run script for the 24-run first pass.
- Use the same subject-relative q33 label formulation already audited.
- Apply preprocessing with train-only fit where scaling is needed.
- For EEG, use a minimal summary-feature pipeline based on per-trial channel zscore plus train-only standard scaling.
- For EMG, use signed log1p feature transform plus train-only standard scaling.
- Write predictions, JSON, markdown report, and retained validation counts.
- Compare against the previous subject-relative minimal run and the global-label mainline.

## Expected Outputs

- `docs/idare_subject_relative_preprocessed_minimal_eeg_primary.md`
- `docs/idare_subject_relative_preprocessed_minimal_eeg_primary.json`
- `docs/idare_subject_relative_preprocessed_minimal_eeg_primary_predictions.csv`
- `docs/idare_subject_relative_preprocessed_minimal_emg_primary.md`
- `docs/idare_subject_relative_preprocessed_minimal_emg_primary.json`
- `docs/idare_subject_relative_preprocessed_minimal_emg_primary_predictions.csv`
- `docs/idare_subject_relative_preprocessed_minimal_training_report.md`
- `docs/idare_subject_relative_preprocessed_minimal_training_report.json`

## Pass Criteria

- Exactly 24 planned runs are executed or explicitly failed with a logged reason.
- No heldout-subject leakage is introduced; all scaling is fitted on train folds only.
- Every run records fold, seed, task, modality, preprocessing candidate, retained train samples, and retained validation samples.
- No one-class prediction collapse in more than one run per modality/task.
- Report compares macro-F1 and balanced accuracy against prior subject-relative minimal training and global-label mainline.
- Report recommends exactly one next objective after human review.

## Candidate Next Objectives After Review

- `subject_relative_preprocessed_training_review_closeout`
- `preprocessed_balanced_sampler_second_pass_objective`
- `subject_relative_feature_engineering_objective`
- `stop_or_handoff_objective`

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

Prepare a reviewed implementation/run command for the 24-run minimal subject-relative preprocessed first pass.
