# I-DARE Label-Semantics Redesigned-Task Smoke Tests Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T11:24:30+00:00`

## Executive Result

Selected formulation: `subject_relative_ordinal_affect_regression_v1`

Diagnosis: `redesigned_task_smoke_tests_failed`

Recommended next objective: `label_semantics_redesigned_task_spec_fix_or_stop_objective`

All required smoke tests passed: `False`

## Smoke-Test Decision Matrix

| smoke_test | passed | evidence | action_if_failed |
| --- | --- | --- | --- |
| target_construction_integrity | True | 8064 targets; min=0.0000; max=1.0000 | fix target construction or stop/archive |
| fold_leakage_guard | True | max_subject_overlap=0; max_row_overlap=0 | fix split protocol before any training |
| metric_computation_sanity | True | perfect_spearman=1.0000; reversed_spearman=-1.0000 | fix metric code |
| baseline_no_training_control | True | 48 no-training control rows; mean_null_spearman=0.0021 | fix controls before training |
| target_distribution_audit | True | min_val_target_std=0.2884 | revise target or flag degenerate cells |
| future_run_matrix_guard | False | future_run_rows=48; no SupCon/DG/fusion rows=False | fix future matrix before training objective |

## Target Construction Summary

| modality | task | n_rows | n_targets | n_subjects | target_min | target_max | target_std | degenerate_subjects | target_construction_passed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EEG | valence | 2016 | 2016 | 63 | 0.0 | 1.0 | 0.2925792881583958 | 0 | True |
| EEG | arousal | 2016 | 2016 | 63 | 0.0 | 1.0 | 0.2905886979416474 | 0 | True |
| EMG | valence | 2016 | 2016 | 63 | 0.0 | 1.0 | 0.2925792881583958 | 0 | True |
| EMG | arousal | 2016 | 2016 | 63 | 0.0 | 1.0 | 0.2905886979416474 | 0 | True |

## Fold Leakage / Distribution Summary

| modality | task | max_subject_overlap | max_row_overlap | min_val_target_std | all_folds_passed |
| --- | --- | --- | --- | --- | --- |
| EEG | arousal | 0 | 0 | 0.2884 | True |
| EEG | valence | 0 | 0 | 0.2913 | True |
| EMG | arousal | 0 | 0 | 0.2884 | True |
| EMG | valence | 0 | 0 | 0.2913 | True |

## No-Training Control Summary

| modality | task | control | mean_spearman | mean_mae | mean_rmse | all_finite |
| --- | --- | --- | --- | --- | --- | --- |
| EEG | arousal | train_label_resample_null | 0.0031 | 0.3368 | 0.4136 | True |
| EEG | arousal | train_mean_no_training | 0.0000 | 0.2539 | 0.2905 | True |
| EEG | valence | train_label_resample_null | -0.0203 | 0.3427 | 0.4165 | True |
| EEG | valence | train_mean_no_training | 0.0000 | 0.2525 | 0.2925 | True |
| EMG | arousal | train_label_resample_null | 0.0082 | 0.3341 | 0.4109 | True |
| EMG | arousal | train_mean_no_training | 0.0000 | 0.2539 | 0.2905 | True |
| EMG | valence | train_label_resample_null | 0.0257 | 0.3317 | 0.4074 | True |
| EMG | valence | train_mean_no_training | 0.0000 | 0.2525 | 0.2925 | True |

## Interpretation

At least one required smoke test failed. Training should remain blocked until the spec or implementation is fixed, or the branch is stopped/archived.

## Next Allowed Step

Human review / closeout before the next objective.


Blocked until review:

- direct full SupCon/DG training

- broad hyperparameter search

- EEG+EMG fusion

- final LOSO claim

- mainline change

- full redesigned-task training before review
