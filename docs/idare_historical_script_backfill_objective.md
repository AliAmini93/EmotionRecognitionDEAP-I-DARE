# I-DARE Historical Script Backfill Objective

## Status

Status: objective created; historical script backfill design only; no script copy or execution is authorized by this document.

Created UTC: `2026-05-08T13:44:25+00:00`

## Current Pause Point

Active scientific objective remains paused:

`docs/idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis_objective.md`

Pause commit before this objective: `5dfddbe`

## Scientific / Reproducibility Question

How do we backfill the historical `~/Downloads` shell scripts into the repository without misrepresenting provenance, rewriting history, or executing any old experiment code?

## Source Evidence

- Prior reproducibility report: `docs/idare_script_archival_and_reproducibility_report.md`
- Prior manifest: `docs/idare_script_archival_manifest.csv`
- User-provided downloads archive: `Downloads.tar.gz`
- Source inventory: `docs/idare_historical_script_backfill_source_inventory.csv`

## Archive Inventory Summary

Total shell scripts discovered in the uploaded archive: `71`

Type counts:

- `build_or_commit_command`: 1
- `fix_or_salvage_command`: 7
- `guardrailed_training_or_ablation_run`: 6
- `objective_or_review_creator`: 33
- `prepared_run_command`: 1
- `read_only_or_design_report_run`: 22
- `uncategorized_download_script`: 1

## Authorized Work

- Preserve the uploaded historical scripts byte-for-byte under `scripts/idare/archive_or_reconstructed/from_downloads_bundle/`.
- Use `docs/idare_historical_script_backfill_target_map.csv` to decide target paths.
- Extend `docs/idare_script_archival_manifest.csv` with one row per backfilled script.
- Record SHA-256 and provenance for each script.
- Produce a backfill report after copy/manifest update.

## Not Authorized

- Executing any historical script.
- Rewriting the historical scripts into curated reusable scripts during this backfill.
- Running the active failure-or-confirmation analysis before backfill review.
- New training, broad hyperparameter search, EEG+EMG fusion, direct full SupCon/DG training, or final LOSO claims.

## Required Outputs For The Next Backfill Command

- `scripts/idare/archive_or_reconstructed/from_downloads_bundle/**.sh`
- updated `docs/idare_script_archival_manifest.csv`
- `docs/idare_historical_script_backfill_report.md`
- `docs/idare_historical_script_backfill_report.json`
- `docs/idare_historical_script_backfill_manifest_delta.csv`

## Pass Criteria

- Every `.sh` file in the uploaded archive is either copied byte-for-byte or explicitly marked as skipped with reason.
- Every copied script has a manifest row with source archive, source path, target path, SHA-256, and provenance.
- No copied historical script is executed.
- The active scientific pause point remains documented.
- `project_status_current.md/json` identify the backfill status and next allowed step.

## Next Allowed Step

`prepare_reviewed_historical_script_backfill_command`

## Blocked

- active failure-or-confirmation analysis until historical backfill review
- executing historical scripts during archival
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
