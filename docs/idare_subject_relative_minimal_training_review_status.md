# I-DARE Subject-relative Minimal Training Review Status

## Status

Frozen human review closeout.

Created/updated UTC: `2026-05-07T16:27:32.454763+00:00`

## Reviewed Evidence

- Report: `docs/idare_subject_relative_minimal_training_report.md`
- JSON: `docs/idare_subject_relative_minimal_training_report.json`

## Review Decision

The 24-run minimal subject-relative first pass is accepted as completed and reviewed.

Decision:

- Do not promote subject-relative q33 as a mainline change.
- Do not run the optional balanced-sampler second pass yet.
- Do not start fusion or final LOSO claims.
- Move to a controlled representation/preprocessing objective.

## Result Summary

- Diagnosis: `subject_relative_first_pass_not_sufficient_alone`
- Recommended next objective in the report: `subject_relative_representation_preprocessing_objective`

| Modality | Task | Subject-relative macro F1 | Global-label macro F1 | Delta macro F1 | Subject-relative bal acc | Global-label bal acc | Delta bal acc |
|---|---|---:|---:|---:|---:|---:|---:|
| EEG | valence | 0.4991 | 0.5073 | -0.0082 | 0.5157 | 0.5196 | -0.0039 |
| EEG | arousal | 0.4764 | 0.5103 | -0.0338 | 0.4893 | 0.5151 | -0.0258 |
| EMG | valence | 0.5213 | 0.5140 | 0.0073 | 0.5225 | 0.5202 | 0.0023 |
| EMG | arousal | 0.4888 | 0.5159 | -0.0271 | 0.4946 | 0.5192 | -0.0246 |

## Next Allowed Step

Create and review a controlled representation/preprocessing objective before any new training.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change
- BSL-stats sidecars
- balanced-sampler second pass before a separate objective
