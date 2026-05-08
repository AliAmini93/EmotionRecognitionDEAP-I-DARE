# I-DARE Reproducibility-Layer Pause Status

## Status

Status: paused for reproducibility-layer fix.

Created UTC: `2026-05-08T12:31:54+00:00`

## Pause Point

HEAD at pause: `47379cf`

Branch: `main`

Active scientific objective: `docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.md`

Active next allowed scientific step: `prepare_reviewed_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_command`

First-pass diagnosis: `minimal_redesigned_task_first_pass_mixed_signal`

First-pass recommended next objective: `label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective`

## Reason for Pause

Workflow outputs have been generated and committed, but the reusable scripts/commands have mostly lived outside the repository under `~/Downloads`.

That weakens reproducibility even when reports are committed.

## Decision

Pause the active read-only failure-or-confirmation analysis until a script archival and reproducibility objective is created.

## Next Selected Step

Create/use `docs/idare_script_archival_and_reproducibility_objective.md`.

## Blocked

- running failure-or-confirmation analysis before reproducibility layer is fixed
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change unrelated to script archival
- deep neural training for redesigned task
- unregistered feature engineering
