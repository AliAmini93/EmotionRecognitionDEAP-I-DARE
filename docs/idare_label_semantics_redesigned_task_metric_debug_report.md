# I-DARE Label-Semantics Redesigned-Task Metric-Debug Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T15:09:20+00:00`

## Executive Diagnosis

Diagnosis: `redesigned_task_metric_debug_no_actionable_signal`

Recommendation: `archive_or_alternative_formulation_after_review`

Recommended next objective: `label_semantics_redesigned_task_archive_or_alternative_formulation_objective`

Decision reason: The best rank signal is far below a practical threshold, q33 separation remains near chance, and no cell improves MAE/RMSE over the mean baseline.

## Metric Conflict Summary

The minimal redesigned-task first pass is not confirmatory. The strongest cell by Spearman is `EMG` / `valence`, but the effect is very small.

| Indicator | Value |
|---|---:|
| Max mean Spearman rho | 0.0192 |
| Max mean q33 balanced accuracy | 0.5071 |
| Cells with mean Spearman >= 0.10 | 0 |
| Cells with q33 balanced accuracy >= 0.55 | 0 |
| Cells improving MAE over mean baseline | 0 |
| Cells improving RMSE over mean baseline | 0 |
| Metric-conflict cells | 2 |

## Fold Signal Audit

| modality | task | mean_spearman_rho | folds_positive_spearman | folds_over_010_spearman | mean_q33_bal_acc | fold_signal_interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| EEG | arousal | 0.0069 | 4 | 0 | 0.5049 | weak_rank_signal_near_chance_threshold |
| EEG | valence | -0.0105 | 3 | 0 | 0.5017 | unstable_or_fold_dependent_signal |
| EMG | arousal | -0.0198 | 1 | 0 | 0.4775 | unstable_or_fold_dependent_signal |
| EMG | valence | 0.0192 | 4 | 0 | 0.5071 | weak_rank_signal_near_chance_threshold |

## Metric Decomposition

| modality | task | mean_spearman_rho | mean_q33_bal_acc | delta_mae_positive_is_better | delta_rmse_positive_is_better | metric_conflict_type |
| --- | --- | --- | --- | --- | --- | --- |
| EMG | valence | 0.0192 | 0.5071 | -0.0214 | -0.0801 | rank_signal_absolute_error_conflict |
| EEG | arousal | 0.0069 | 0.5049 | -0.0152 | -0.0287 | rank_signal_absolute_error_conflict |
| EEG | valence | -0.0105 | 0.5017 | -0.0207 | -0.0331 | no_rank_signal_and_worse_absolute_error |
| EMG | arousal | -0.0198 | 0.4775 | -0.0037 | -0.0065 | no_rank_signal_and_worse_absolute_error |

## Subject Concentration Audit

Subject-level error summaries were inspected from the committed first-pass subject-error table. This audit is used only as a read-only concentration check, not as a new training/evaluation step.

| model | modality | task | n_unique_subjects | mean_subject_mae | p90_subject_mae | max_subject_mae | subject_concentration_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| mean_baseline_no_training | EEG | arousal | 63 | 0.2540 | 0.2581 | 0.2581 | no_strong_subject_tail_by_available_summary |
| mean_baseline_no_training | EEG | valence | 63 | 0.2525 | 0.2581 | 0.2581 | no_strong_subject_tail_by_available_summary |
| mean_baseline_no_training | EMG | arousal | 63 | 0.2540 | 0.2581 | 0.2581 | no_strong_subject_tail_by_available_summary |
| mean_baseline_no_training | EMG | valence | 63 | 0.2525 | 0.2581 | 0.2581 | no_strong_subject_tail_by_available_summary |
| ridge_regression_summary_features | EEG | arousal | 63 | 0.2695 | 0.2823 | 0.6447 | no_strong_subject_tail_by_available_summary |
| ridge_regression_summary_features | EEG | valence | 63 | 0.2735 | 0.2923 | 0.4604 | no_strong_subject_tail_by_available_summary |
| ridge_regression_summary_features | EMG | arousal | 63 | 0.2577 | 0.2614 | 0.3660 | no_strong_subject_tail_by_available_summary |
| ridge_regression_summary_features | EMG | valence | 63 | 0.2730 | 0.2612 | 1.4441 | no_strong_subject_tail_by_available_summary |

## Decision Matrix

| decision_option | pass | evidence | interpretation |
| --- | --- | --- | --- |
| minimal_redesigned_task_confirmation | False | max_mean_spearman=0.0192; cells_q33_over_055=0; cells_mae_improved=0; cells_rmse_improved=0 | Not supported unless rank and absolute-error metrics agree. |
| metric_definition_patch | True | metric_conflict_cells=2; max_mean_spearman=0.0192; max_q33=0.5071 | Possible but weak: the rank signal is too small to justify metric-plan patch alone. |
| fold_or_subject_artifact_analysis | True | min_folds_positive=1; max_folds_under_zero=5 | Some instability exists, but the larger issue is weak/no actionable metric support. |
| archive_or_alternative_formulation | True | max_mean_spearman=0.0192; cells_q33_over_055=0; cells_mae_improved=0; cells_rmse_improved=0 | Supported: weak rank signal does not translate into actionable separation or absolute-error improvement. |
| ambiguous_metric_definition_rerun_read_only | False | confirm_pass=False; no_support_pass=True | Use only if the debug cannot select confirmation or no-support. |

## Interpretation

The redesigned task does not currently provide actionable evidence for continuing model search.

The positive rank signal is too weak (`max mean Spearman < 0.10`), high/low q33 separation remains near chance, and no evaluated cell improves both absolute-error metrics over the mean baseline. This points away from confirmation and toward either archiving this redesigned branch or proposing a materially different label/task formulation after review.

## Next Allowed Step

Human review / closeout before archive, metric-patch, confirmation, or alternative-formulation objective.

## Blocked

- new training
- task redesign
- stop/archive implementation
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
