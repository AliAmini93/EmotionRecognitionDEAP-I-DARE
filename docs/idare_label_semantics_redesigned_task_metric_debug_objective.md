# I-DARE Label-Semantics Redesigned-Task Metric-Debug Objective

## Status

Status: objective created; read-only metric-debug only; no training is authorized.

Created UTC: `2026-05-08T15:03:47+00:00`

## Scientific Question

Why does the minimal redesigned-task first pass show weak positive rank signal while MAE/RMSE worsen against the mean baseline?

## Triggering Evidence

- Accepted diagnosis: `minimal_redesigned_task_weak_rank_signal_metric_conflict`
- Decision reason: The best cell has weak positive rank signal but worsens MAE/RMSE against mean baseline.
- Recommended next objective: `label_semantics_redesigned_task_metric_debug_objective`
- Best cell: `EMG` / `valence`
- Best mean Spearman rho: `0.019171068580299766`
- Best mean MAE vs baseline MAE: `0.27383986981751823` vs `0.2524529569892473`
- Best mean RMSE vs baseline RMSE: `0.3726750009621769` vs `0.29255926858015163`
- Best q33 balanced accuracy: `0.5070515450953589`

## Authorized Work

- Read existing committed CSV/JSON outputs only.
- Debug the metric conflict across Spearman, MAE, RMSE, q33 balanced accuracy, fold stability, and subject errors.
- Decide whether the weak rank signal is stable, an artifact, a metric-definition issue, or insufficient evidence.

## Required Analysis Questions

1. Is the weak Spearman signal stable across folds, or driven by a small number of folds?
2. Why do MAE/RMSE worsen while Spearman is weakly positive?
3. Is q33 top-bottom balanced accuracy consistent with Spearman?
4. Does the mean baseline dominate because the target is too centered/compressed?
5. Are errors concentrated in specific subjects, folds, modalities, or tasks?
6. Should the next step be confirmation, metric-plan patch, task redesign, or archive?

See: `docs/idare_label_semantics_redesigned_task_metric_debug_questions.csv`

## Required Inputs

See: `docs/idare_label_semantics_redesigned_task_metric_debug_input_map.csv`

## Expected Outputs

- `docs/idare_label_semantics_redesigned_task_metric_debug_report.md`
- `docs/idare_label_semantics_redesigned_task_metric_debug_report.json`
- `docs/idare_label_semantics_redesigned_task_metric_debug_fold_signal.csv`
- `docs/idare_label_semantics_redesigned_task_metric_debug_metric_decomposition.csv`
- `docs/idare_label_semantics_redesigned_task_metric_debug_subject_concentration.csv`
- `docs/idare_label_semantics_redesigned_task_metric_debug_decision_matrix.csv`

## Pass Criteria

- No new training is run.
- No task redesign is performed in this objective.
- No stop/archive decision is finalized in this objective.
- All conclusions are derived from committed first-pass and failure/confirmation analysis outputs.
- Exactly one recommended next objective is produced.

## Next Allowed Step

`prepare_reviewed_label_semantics_redesigned_task_metric_debug_command`

## Blocked

- new training
- task redesign
- stop/archive decision
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change unrelated to metric-debug analysis
