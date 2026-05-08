# I-DARE Minimal Redesigned-Task Failure-or-Confirmation Analysis Objective

## Status

Status: objective created; read-only analysis only; no training is authorized.

Created UTC: `2026-05-08T12:23:16+00:00`

## Scientific Question

Should the minimal redesigned-task first-pass result be interpreted as a real but weak signal worth confirming, or as another failure mode requiring redesign/stop?

## Triggering Evidence

- First-pass diagnosis: `minimal_redesigned_task_first_pass_mixed_signal`
- Recommended next objective from first pass: `label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective`
- ridge_best_spearman: `0.019171068580299756`
- ridge_cells_over_010_spearman: `0`
- ridge_cells_positive_spearman: `2`
- ridge_cells_mae_improved_vs_mean_baseline: `0`
- permutation_abs_max_mean_spearman: `0.011130770077244055`

## Authorized Work

- Read-only fold/task/cell instability analysis.
- Compare ridge cells against mean baseline and permutation control.
- Identify whether positive Spearman is concentrated in specific modality/task/folds.
- Audit whether MAE/RMSE worsening invalidates the small positive Spearman signal.
- Audit hard-subject concentration from subject-error summary.
- Produce a decision matrix with one of: confirmation objective, targeted metric/debug analysis, or stop/archive.

## Required Analysis Questions

1. Are positive Spearman values robust across folds or driven by one/two folds?
2. Does any modality/task cell beat mean baseline on both Spearman and MAE/RMSE?
3. Is q33 balanced accuracy consistent with ordinal Spearman or just noise around 0.5?
4. Does permutation control remain near zero for every candidate cell?
5. Are errors concentrated in particular held-out subjects?
6. Is the redesigned task promising enough for a confirmation run, or should it stop?

## Expected Outputs

- `docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_report.md`
- `docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_report.json`
- `docs/idare_label_semantics_minimal_redesigned_task_cell_decision_matrix.csv`
- `docs/idare_label_semantics_minimal_redesigned_task_fold_instability_audit.csv`
- `docs/idare_label_semantics_minimal_redesigned_task_subject_error_audit.csv`
- `docs/idare_label_semantics_minimal_redesigned_task_metric_conflict_audit.csv`

## Pass Criteria

- Uses only committed first-pass outputs.
- Does not run new training.
- Explains why mixed signal is or is not confirmable.
- Selects exactly one next objective.
- Keeps SupCon/DG, fusion, broad search, and final claims blocked.

## Next Allowed Step

Prepare a reviewed read-only failure-or-confirmation analysis command/script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- deep neural training for redesigned task
- unregistered feature engineering
- confirmation training before this analysis closes
