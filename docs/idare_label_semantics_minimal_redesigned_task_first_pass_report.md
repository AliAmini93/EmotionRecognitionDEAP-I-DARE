# I-DARE Label-Semantics Minimal Redesigned-Task First-Pass Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T12:17:50+00:00`

## Run Matrix

| item | value |
| --- | --- |
| n_runs | 48 |
| n_predictions | 16128 |
| selected_primary_formulation | subject_relative_ordinal_affect_regression_v1 |
| diagnosis | minimal_redesigned_task_first_pass_mixed_signal |
| recommended_next_objective | label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective |

## Key Indicators

| item | value |
| --- | --- |
| ridge_mean_spearman | -0.0010 |
| ridge_best_spearman | 0.0192 |
| ridge_cells_over_010_spearman | 0 |
| ridge_cells_positive_spearman | 2 |
| ridge_cells_mae_improved_vs_mean_baseline | 0 |
| permutation_abs_max_mean_spearman | 0.0111 |

## Metric Summary

| model | modality | task | n_runs | mean_spearman_rho | std_spearman_rho | mean_mae_rank_percentile | mean_rmse_rank_percentile | mean_top_bottom_q33_balanced_accuracy | mean_permutation_control_spearman | delta_vs_mean_baseline_spearman | delta_vs_mean_baseline_mae | folds_positive_spearman | folds_over_010_spearman |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mean_baseline_no_training | EEG | arousal | 6 | 0.0000 | 0.0000 | 0.2540 | 0.2906 | 0.5000 | nan | 0.0000 | 0.0000 | 0 | 0 |
| mean_baseline_no_training | EEG | valence | 6 | 0.0000 | 0.0000 | 0.2525 | 0.2926 | 0.5000 | nan | 0.0000 | 0.0000 | 0 | 0 |
| mean_baseline_no_training | EMG | arousal | 6 | 0.0000 | 0.0000 | 0.2540 | 0.2906 | 0.5000 | nan | 0.0000 | 0.0000 | 0 | 0 |
| mean_baseline_no_training | EMG | valence | 6 | 0.0000 | 0.0000 | 0.2525 | 0.2926 | 0.5000 | nan | 0.0000 | 0.0000 | 0 | 0 |
| ridge_regression_summary_features | EEG | arousal | 6 | 0.0069 | 0.0420 | 0.2692 | 0.3193 | 0.5049 | 0.0082 | 0.0069 | -0.0152 | 4 | 0 |
| ridge_regression_summary_features | EEG | valence | 6 | -0.0105 | 0.0452 | 0.2731 | 0.3256 | 0.5017 | -0.0111 | -0.0105 | -0.0207 | 3 | 0 |
| ridge_regression_summary_features | EMG | arousal | 6 | -0.0198 | 0.0207 | 0.2578 | 0.2971 | 0.4775 | 0.0093 | -0.0198 | -0.0037 | 1 | 0 |
| ridge_regression_summary_features | EMG | valence | 6 | 0.0192 | 0.0362 | 0.2738 | 0.3727 | 0.5071 | 0.0034 | 0.0192 | -0.0214 | 4 | 0 |

## Top Ridge Cells

| modality | task | n_runs | mean_spearman_rho | std_spearman_rho | mean_mae_rank_percentile | delta_vs_mean_baseline_mae | mean_permutation_control_spearman | folds_over_010_spearman |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EMG | valence | 6 | 0.0192 | 0.0362 | 0.2738 | -0.0214 | 0.0034 | 0 |
| EEG | arousal | 6 | 0.0069 | 0.0420 | 0.2692 | -0.0152 | 0.0082 | 0 |
| EEG | valence | 6 | -0.0105 | 0.0452 | 0.2731 | -0.0207 | -0.0111 | 0 |
| EMG | arousal | 6 | -0.0198 | 0.0207 | 0.2578 | -0.0037 | 0.0093 | 0 |

## Interpretation

The minimal redesigned-task first pass shows mixed evidence. The next step should analyze whether the signal is robust enough for confirmation or whether it reflects fold/task instability.


## Next Allowed Step

Human review / closeout before any confirmation or failure-analysis objective.


Recommended next objective: `label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective`


## Blocked

- direct full SupCon/DG training

- broad hyperparameter search

- EEG+EMG fusion

- final LOSO claim

- mainline change

- deep neural training for redesigned task

- unregistered feature engineering
