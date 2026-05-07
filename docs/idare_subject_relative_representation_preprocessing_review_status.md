# I-DARE Subject-relative Representation/Preprocessing Review Status

## Status

Frozen human review closeout.

Created/updated UTC: `2026-05-07T16:34:01.007092+00:00`

## Reviewed Evidence

- Report: `docs/idare_subject_relative_representation_preprocessing_report.md`
- JSON: `docs/idare_subject_relative_representation_preprocessing_report.json`

## Review Decision

The read-only representation/preprocessing diagnostic is accepted as completed and reviewed.

Decision:

- Accept that at least one low-leakage preprocessing candidate is worth a minimal controlled training test.
- Do not change mainline yet.
- Do not run broad search, fusion, architecture work, augmentation, or domain generalization.
- Create a minimal subject-relative preprocessed training objective as the next step.

## Result Summary

- Diagnosis: `preprocessing_candidate_worth_testing`
- Recommended next objective: `minimal_subject_relative_preprocessed_training_objective`
- Best candidate: `emg_signed_log1p_train_standard_scaled`
- Best candidate modality: `EMG`
- Diagnostic score: `0.5220`
- Mean shift reduction vs raw: `0.2173`
- Mean validation-separation gain vs raw: `-0.0071`

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

Create a minimal subject-relative preprocessed training objective; then prepare a reviewed implementation/run command.
