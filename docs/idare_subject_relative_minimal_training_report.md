# I-DARE Minimal Subject-relative Training Report

## Status

Minimal subject-relative first-pass diagnostic training complete; pending human review.

Generated UTC: `2026-05-07T16:24:58.380389+00:00`

No final LOSO claim or mainline change is made.

## Run Matrix

| Dimension | Value |
|---|---|
| Formulation | `subject_top_bottom_quantile_q33` |
| Definition | per-subject bottom third = 0, top third = 1, middle third discarded |
| Modalities | EEG `STIM-BSL`-only; EMG feature-only |
| Tasks | valence; arousal |
| Recipe | `ce_class_weighted` |
| Folds / seed | 6 folds, seed 11 |
| Completed runs | 24 |

## Validation

- EEG prediction rows: `3272`
- EMG prediction rows: `3272`
- All runs annotated with formulation and retained validation count: `True`

## Comparison Against Previous Global-label Mainline

| Modality | Task | Subject-relative macro F1 | Global-label macro F1 | Delta macro F1 | Subject-relative bal acc | Global-label bal acc | Delta bal acc | Retained val n total | One-class runs |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EEG | valence | 0.4991 | 0.5073 | -0.0082 | 0.5157 | 0.5196 | -0.0039 | 1629 | 0 |
| EEG | arousal | 0.4764 | 0.5103 | -0.0338 | 0.4893 | 0.5151 | -0.0258 | 1643 | 0 |
| EMG | valence | 0.5213 | 0.5140 | 0.0073 | 0.5225 | 0.5202 | 0.0023 | 1629 | 0 |
| EMG | arousal | 0.4888 | 0.5159 | -0.0271 | 0.4946 | 0.5192 | -0.0246 | 1643 | 0 |

## Diagnosis

`subject_relative_first_pass_not_sufficient_alone`

Mean delta macro F1 across modality/task cells: `-0.0154`

Positive delta cells: `1/4`

## Recommendation

Recommended next objective after human review: `subject_relative_representation_preprocessing_objective`

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change
- BSL-stats sidecars in first pass

## Next Allowed Step

Human review / closeout before any optional balanced-sampler pass, preprocessing objective, BSL-stats sidecar, or stop/handoff decision.
