# I-DARE Subject-relative Representation/Preprocessing Objective

## Status

Short-term diagnostic/design objective created.

Created/updated UTC: `2026-05-07T16:27:32.454763+00:00`

This objective does not authorize new performance training, final LOSO claims, fusion, architecture improvement, augmentation, or domain generalization.

## Why This Objective Exists

The minimal subject-relative first-pass training report was reviewed.

The selected subject-relative formulation was tested, but it was not sufficient alone.

The next controlled step is to diagnose representation and preprocessing before trying another training pass.

## Scientific Questions

- Is the remaining blocker primarily representation/preprocessing rather than label formulation alone?
- Can controlled preprocessing candidates improve train/validation separability without leakage?
- Which minimal preprocessing candidate should be tested first in a separately reviewed training objective?

## Authorized Work

- Read existing caches, cache indices, diagnostics, and prediction outputs.
- Audit EEG and EMG feature distributions under subject-relative labels.
- Compare train-only scaling, robust scaling, per-channel/window normalization, and summary-feature extraction as design candidates.
- For EEG, create read-only diagnostics on baseline-corrected STIM-BSL windows and summary features; no model training in this objective.
- For EMG, create read-only diagnostics on feature scaling and subject/fold distribution shift; no model training in this objective.
- Produce a ranked candidate list for a future minimal preprocessing training objective.

## Expected Outputs

- `docs/idare_subject_relative_representation_preprocessing_report.md`
- `docs/idare_subject_relative_representation_preprocessing_report.json`
- `docs/idare_subject_relative_preprocessing_candidate_matrix.csv`
- `docs/idare_subject_relative_distribution_shift_summary.csv`

## Pass Criteria

- Report is generated from existing committed/cached artifacts only.
- No new performance training is run.
- No heldout subject leakage is introduced.
- Candidate preprocessing options are ranked by diagnostic evidence and implementation risk.
- Report recommends exactly one next objective after human review.

## Candidate Next Objectives After Review

- `minimal_subject_relative_preprocessed_training_objective`
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

Prepare reviewed read-only representation/preprocessing diagnostic command/script.
