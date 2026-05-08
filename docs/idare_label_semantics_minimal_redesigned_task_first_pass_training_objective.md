# I-DARE Label-Semantics Minimal Redesigned-Task First-Pass Objective

## Status

Status: objective created; minimal first-pass only; no broad search is authorized.

Created UTC: `2026-05-08T12:08:54+00:00`

## Scientific Question

Does the redesigned subject-relative ordinal/regression task produce a defensible signal under a minimal, frozen baseline/regression first-pass matrix before any neural, SupCon/DG, fusion, or broad-search work?

## Selected Task

Selected primary formulation: `subject_relative_ordinal_affect_regression_v1`

## Authorized Scope

Frozen run matrix: `docs/idare_label_semantics_minimal_redesigned_task_first_pass_run_matrix.csv`

Planned rows: `48`

Authorized models only:

- `mean_baseline_no_training`
- `ridge_regression_summary_features`

## Authorized Work

- Run exactly the frozen 48-row minimal first-pass matrix.
- Compute no-training mean baselines.
- Compute ridge regression summary-feature baselines.
- Use the selected redesigned task target only.
- Write predictions, run summary, metric summary, and report.
- Compare against smoke-test expectations and stop criteria.

## Not Authorized

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- deep neural training for redesigned task
- unregistered feature engineering

## Expected Outputs

- `docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.md`
- `docs/idare_label_semantics_minimal_redesigned_task_first_pass_report.json`
- `docs/idare_label_semantics_minimal_redesigned_task_first_pass_runs.csv`
- `docs/idare_label_semantics_minimal_redesigned_task_first_pass_predictions.csv`
- `docs/idare_label_semantics_minimal_redesigned_task_first_pass_metric_summary.csv`

## Pass Criteria

- All 48 planned rows are executed or explicitly accounted for.
- No unregistered model/method appears.
- Metrics include regression and directional/ordinal summaries per metric plan.
- Results are compared against no-training baseline.
- No final claim is made.
- Next step is selected only after human review.

## Next Allowed Step

Prepare a reviewed minimal redesigned-task first-pass run command/script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- deep neural training for redesigned task
- unregistered feature engineering
