# I-DARE Script Archival and Reproducibility Objective

## Status

Status: objective created; reproducibility-layer fix only; no training is authorized.

Created UTC: `2026-05-08T12:31:54+00:00`

## Current Pause Point

Active scientific objective: `docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.md`

Active scientific next step is paused: `prepare_reviewed_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_command`

First-pass diagnosis: `minimal_redesigned_task_first_pass_mixed_signal`

## Scientific Question

How do we restore reproducibility before continuing the active I-DARE failure-or-confirmation analysis?

## Problem Statement

The scientific outputs are committed, but many command scripts have been generated/executed from `~/Downloads` rather than committed under `scripts/`.

This creates a reproducibility gap: a reviewer can see the results, but not always the exact reusable command that produced them.

## Authorized Work

- Define script archival policy.
- Create `scripts/idare/` directory structure if missing.
- Commit the next active read-only analysis script under `scripts/idare/analysis/`.
- Create a reproducibility manifest linking objective, script, command, outputs, and commit.
- Optionally backfill earlier `~/Downloads` scripts only if reconstructable from logs.
- Update `docs/project_status_current.*` with script archival status.

## Not Authorized

- running failure-or-confirmation analysis before reproducibility layer is fixed
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change unrelated to script archival
- deep neural training for redesigned task
- unregistered feature engineering

## Required Outputs

- `scripts/idare/README.md`
- `scripts/idare/analysis/run_idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis.py`
- `docs/idare_script_archival_manifest.csv`
- `docs/idare_script_archival_and_reproducibility_report.md`
- `docs/idare_script_archival_and_reproducibility_report.json`

## Pass Criteria

- Active next analysis script exists under `scripts/idare/analysis/`.
- Script has executable shebang or documented command.
- Script references its objective document.
- Manifest links script to objective and expected outputs.
- No new training is executed.
- No broad search, SupCon/DG, fusion, or final claims are authorized.
- After this objective is complete, active failure-or-confirmation analysis may be run from committed script path.

## Next Allowed Step

Prepare a reviewed script archival and reproducibility command.

## Blocked

- running failure-or-confirmation analysis before reproducibility layer is fixed
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change unrelated to script archival
- deep neural training for redesigned task
- unregistered feature engineering
