# I-DARE Minimal Redesigned-Task Failure-or-Confirmation Analysis Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T14:58:31+00:00`

## Executive Diagnosis

Diagnosis: `minimal_redesigned_task_weak_rank_signal_metric_conflict`

Recommended next objective: `label_semantics_redesigned_task_metric_debug_objective`

Decision reason: The best cell has weak positive rank signal but worsens MAE/RMSE against mean baseline.

## Cell Decision Matrix

| modality | task | mean_spearman_rho | folds_positive_spearman | folds_over_010_spearman | delta_vs_mean_baseline_mae_positive_is_better | mean_q33_bal_acc | decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EEG | valence | -0.0105 | 3 | 0 | -0.0207 | 0.5017 | not_confirmable |
| EMG | arousal | -0.0198 | 1 | 0 | -0.0037 | 0.4775 | not_confirmable |
| EMG | valence | 0.0192 | 4 | 0 | -0.0214 | 0.5071 | weak_signal_metric_conflict |
| EEG | arousal | 0.0069 | 4 | 0 | -0.0152 | 0.5049 | weak_signal_metric_conflict |

## Metric Conflict Audit

| modality | task | mean_spearman_rho | delta_mae_positive_is_better | delta_rmse_positive_is_better | mean_q33_bal_acc | metric_conflict_flags |
| --- | --- | --- | --- | --- | --- | --- |
| EEG | valence | -0.0105 | -0.0207 | -0.0331 | 0.5017 | no_positive_rank_signal |
| EMG | arousal | -0.0198 | -0.0037 | -0.0065 | 0.4775 | no_positive_rank_signal;q33_not_strict_chance |
| EMG | valence | 0.0192 | -0.0214 | -0.0801 | 0.5071 | positive_spearman_but_mae_worse;positive_spearman_but_rmse_worse |
| EEG | arousal | 0.0069 | -0.0152 | -0.0287 | 0.5049 | positive_spearman_but_mae_worse;positive_spearman_but_rmse_worse |

## Fold Instability Interpretation

The first-pass result is interpreted from ridge regression cells only, against the no-training mean baseline and permutation control.

The analysis checks whether positive Spearman is robust across folds, whether MAE/RMSE improve over baseline, and whether q33 balanced accuracy is consistent with the rank-order signal.

## Subject Error Audit

Subject-level errors were summarized in `docs/idare_label_semantics_minimal_redesigned_task_subject_error_audit.csv`.

Rows in source subject-error file: `504`

## Interpretation

This report does not authorize training.

Confirmation requires both a rank-order signal and no major conflict with error metrics. A weak positive Spearman with worse MAE/RMSE is treated as a metric conflict rather than confirmation.

## Next Allowed Step

Human review / closeout before `label_semantics_redesigned_task_metric_debug_objective`.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- deep neural training for redesigned task
- unregistered feature engineering
