# I-DARE Label-Semantics Redesigned-Task Smoke-Guard Patch Objective

## Status

Status: objective created; narrow smoke-guard patch only; no training is authorized.

Created UTC: `2026-05-08T12:01:45+00:00`

## Scientific Question

Can the redesigned-task smoke future-run guard be patched narrowly so that it blocks actual SupCon/DG/fusion/broad-search rows without failing on negated notes or the substring `dg` inside `ridge`?

## Manual Audit Diagnosis

Diagnosis: `future_run_matrix_guard_false_positive_from_notes_and_ridge_token`

Prior stop/archive recommendation is superseded for this specific smoke-guard failure.

## Evidence Summary

- Future run matrix rows: `48`.
- Authorized-now rows all `no`: `True`.
- Unique model values: `mean_baseline_no_training, ridge_regression_summary_features`.
- Actual forbidden model rows: `0`.
- Notes mention SupCon/DG only as negative guardrail prose.
- Ridge baseline rows: `24`.

## Authorized Work

- Patch only the `future_run_matrix_guard` logic in the smoke-test script/command.
- Evaluate forbidden methods only from explicit `model` / `method` columns.
- Use token-aware matching for DG / domain-generalization.
- Treat notes as explanatory metadata unless an explicit authorization field says otherwise.
- Rerun the same redesigned-task smoke tests.
- Write a patched smoke-test report.
- Do not run minimal regression training.
- Do not run SupCon/DG training.
- Do not run broad hyperparameter search.

## Required Inputs

- `docs/idare_label_semantics_redesigned_task_smoke_tests_report.md`
- `docs/idare_label_semantics_redesigned_task_smoke_tests_report.json`
- `docs/idare_label_semantics_task_redesign_future_run_matrix.csv`
- `docs/idare_label_semantics_redesigned_task_future_matrix_manual_audit.csv`
- `docs/idare_label_semantics_redesigned_task_smoke_guard_patch_requirements.csv`

## Expected Outputs

- `docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.md`
- `docs/idare_label_semantics_redesigned_task_smoke_guard_patch_report.json`
- `docs/idare_label_semantics_redesigned_task_smoke_guard_audit.csv`
- Updated `docs/idare_label_semantics_redesigned_task_smoke_tests_report.md`
- Updated `docs/idare_label_semantics_redesigned_task_smoke_tests_report.json`

## Pass Criteria

- Future matrix guard passes for the current mean/ridge-only matrix.
- Actual forbidden model rows would still fail the guard.
- All other smoke tests are rerun and reported.
- Training remains blocked unless patched smoke report passes and is reviewed.
- direct full SupCon/DG training remains blocked.
- broad hyperparameter search remains blocked.
- final LOSO claim remains blocked.

## Next Allowed Step

Prepare a reviewed redesigned-task smoke-guard patch command/script.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- minimal regression training before patched smoke-test review
