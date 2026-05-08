# I-DARE Label-Semantics Redesigned-Task Spec-Fix-or-Stop Objective

## Status

Status: objective created; read-only failure triage only; no training is authorized.

Created UTC: `2026-05-08T11:32:40+00:00`

## Scientific Question

Why did the redesigned-task smoke tests fail, and should the issue be fixed with a narrow spec/implementation patch or should the redesigned branch be stopped/archived?

## Current Smoke-Test Result

Selected formulation: `subject_relative_ordinal_affect_regression_v1`

Diagnosis: `redesigned_task_smoke_tests_failed`

All smoke tests passed: `False`

Failed smoke tests:

- `future_run_matrix_guard`

## Authorized Work

- Read the smoke-test decision matrix and all smoke audit CSVs.
- Identify the exact failed smoke condition(s).
- Classify each failure as one of:
  - implementation bug;
  - spec mismatch;
  - data/label degeneracy;
  - stop/archive trigger.
- Recommend exactly one of:
  - `narrow_fix_objective`;
  - `stop_archive_objective`.
- No training.
- No minimal regression run.
- No direct full SupCon/DG training.
- No broad hyperparameter search.

## Required Inputs

- `docs/idare_label_semantics_redesigned_task_smoke_tests_report.md`
- `docs/idare_label_semantics_redesigned_task_smoke_tests_report.json`
- `docs/idare_label_semantics_redesigned_task_smoke_decision_matrix.csv`
- `docs/idare_label_semantics_redesigned_task_target_audit.csv`
- `docs/idare_label_semantics_redesigned_task_fold_audit.csv`
- `docs/idare_label_semantics_redesigned_task_metric_sanity.csv`
- `docs/idare_label_semantics_redesigned_task_baseline_control_summary.csv`
- `docs/idare_label_semantics_task_redesign_spec.md`
- `docs/idare_label_semantics_task_redesign_stop_criteria.csv`

## Expected Outputs

- `docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.md`
- `docs/idare_label_semantics_redesigned_task_spec_fix_or_stop_report.json`
- `docs/idare_label_semantics_redesigned_task_failed_smoke_diagnosis.csv`
- `docs/idare_label_semantics_redesigned_task_fix_or_stop_decision_matrix.csv`

## Pass Criteria

- Every failed smoke test has an explicit cause classification.
- The recommendation is exactly one of:
  - `narrow_fix_objective`;
  - `stop_archive_objective`.
- If a fix is recommended, it is narrow and does not authorize training.
- If stop/archive is recommended, no further redesigned-task training is authorized.
- direct full SupCon/DG training remains blocked.
- broad hyperparameter search remains blocked.
- final LOSO claim remains blocked.

## Next Allowed Step

Prepare a reviewed redesigned-task spec-fix-or-stop analysis command/script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- minimal regression training before smoke-fix/stop review
