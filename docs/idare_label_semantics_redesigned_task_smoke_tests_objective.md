# I-DARE Label-Semantics Redesigned-Task Smoke Tests Objective

## Status

Status: objective created; smoke-test only; no training is authorized.

Created UTC: `2026-05-08T11:18:25+00:00`

## Scientific Question

Does the redesigned subject-relative ordinal/regression task pass construction, leakage, metric, distribution, and null-control smoke tests before any training is authorized?

## Selected Task

Selected formulation: `subject_relative_ordinal_affect_regression_v1`

Scientific claim: Predict within-subject affect-rating order/percentile for held-out subjects, not global high/low affect by an absolute threshold.

## Authorized Scope

- Read the task redesign spec and guardrails.
- Construct labels/targets for audit only.
- Run target-construction integrity checks.
- Run fold leakage checks.
- Run metric-computation sanity checks.
- Run no-training baseline and shuffled/permutation controls.
- Audit target distribution by subject/fold/task/modality.
- Validate that the future run matrix remains minimal.
- Write a smoke-test report and decision matrix.

## Required Smoke Tests

| Smoke test | Purpose | Pass condition |
|---|---|---|
| `target_construction_integrity` | Verify per-subject rank-percentile targets are valid and deterministic. | no out-of-range targets; expected rows; ties handled deterministically |
| `fold_leakage_guard` | Verify subject-heldout split isolation. | zero subject overlap and zero row-id overlap |
| `metric_computation_sanity` | Validate Spearman/MAE/RMSE/q33 audit behavior. | perfect predictions score best; reversed predictions score worst |
| `baseline_no_training_control` | Compute no-training controls before training. | finite controls; near expected null behavior |
| `target_distribution_audit` | Find degenerate fold/task/subject target distributions. | no unflagged degenerate target cells |
| `future_run_matrix_guard` | Confirm future training plan is minimal. | no direct full SupCon/DG training; no fusion; no broad search |

## Expected Outputs

- `docs/idare_label_semantics_redesigned_task_smoke_tests_report.md`
- `docs/idare_label_semantics_redesigned_task_smoke_tests_report.json`
- `docs/idare_label_semantics_redesigned_task_target_audit.csv`
- `docs/idare_label_semantics_redesigned_task_fold_audit.csv`
- `docs/idare_label_semantics_redesigned_task_metric_sanity.csv`
- `docs/idare_label_semantics_redesigned_task_baseline_control_summary.csv`
- `docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv`

## Pass Criteria

- All required smoke tests pass.
- Target construction is deterministic and complete.
- Fold leakage is zero.
- Metrics behave correctly on toy predictions.
- No-training controls are finite and documented.
- Future run matrix remains minimal.
- direct full SupCon/DG training remains blocked.
- broad hyperparameter search remains blocked.
- final LOSO claim remains blocked.

## Next Allowed Step

Prepare a reviewed redesigned-task smoke-test command/script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- redesigned-task training before smoke-test review
