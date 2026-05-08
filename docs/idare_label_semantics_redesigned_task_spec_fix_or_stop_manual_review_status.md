# I-DARE Redesigned-Task Spec-Fix-or-Stop Manual Review Status

## Status

Status: human review supersedes the prior stop/archive recommendation for this specific smoke-guard failure.

Created UTC: `2026-05-08T12:01:45+00:00`

## Manual Review Decision

Prior report diagnosis: `redesigned_task_smoke_failure_not_yet_fixable`

Prior report recommendation: `stop_archive_objective`

Manual audit diagnosis: `future_run_matrix_guard_false_positive_from_notes_and_ridge_token`

Manual review decision: `do_not_stop_archive_yet_create_narrow_smoke_guard_patch_objective`

## Evidence

Manual inspection of `docs/idare_label_semantics_task_redesign_future_run_matrix.csv` shows:

- model column contains only `mean_baseline_no_training` and `ridge_regression_summary_features`;
- there are zero actual SupCon/DG/VREx/fusion/contrastive model rows;
- `SupCon/DG` appears only in notes as a negative guardrail phrase: `no SupCon/DG or broad search`;
- `ridge_regression_summary_features` is an allowed baseline and must not trigger a substring `dg` check.

## Scientific Meaning

The redesigned task is not cleared for training yet.

However, the current failure is now interpreted as a smoke-guard implementation/spec mismatch, not sufficient evidence for stop/archive.

## Next Selected Step

Create a narrow smoke-guard patch objective and then rerun the same redesigned-task smoke tests.

## Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- minimal regression training before patched smoke-test review
