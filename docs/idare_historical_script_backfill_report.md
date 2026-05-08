# I-DARE Historical Script Backfill Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T13:54:10+00:00`

## Executive Result

Diagnosis: `historical_download_scripts_backfilled_byte_for_byte`

Recommended next objective: `resume_committed_failure_or_confirmation_analysis_after_backfill_review`

## Backfill Summary

- Source archive: `/home/armin/Downloads/Downloads.tar.gz`
- Source script count: `71`
- Copied script count: `71`
- Target root: `scripts/idare/archive_or_reconstructed/from_downloads_bundle`
- SHA256 validation: `passed`
- Any historical script executed: `false`

## Provenance

The scripts were copied byte-for-byte from the user-provided `Downloads.tar.gz` archive.

They are not curated reusable pipeline scripts and must not be treated as reviewed production commands.

Each copied script is marked as:

`user_uploaded_downloads_archive_original_if_sha_matches_archive`

and:

`archived_not_executed_review_required_before_any_use`

## Type / Stage Summary

| script_type_guess | scientific_stage_guess | n_scripts |
| --- | --- | --- |
| build_or_commit_command | broader_eval | 1 |
| fix_or_salvage_command | idare_emg | 2 |
| fix_or_salvage_command | label_semantics_task_redesign | 1 |
| fix_or_salvage_command | minimal_subject_relative_preprocessed | 1 |
| fix_or_salvage_command | minimal_supcon_dg | 2 |
| fix_or_salvage_command | supcon_dg_pair_sampler | 1 |
| guardrailed_training_or_ablation_run | label_policy | 1 |
| guardrailed_training_or_ablation_run | label_semantics_minimal_redesigned_task | 1 |
| guardrailed_training_or_ablation_run | minimal_subject_relative_preprocessed | 1 |
| guardrailed_training_or_ablation_run | minimal_subject_relative_training | 1 |
| guardrailed_training_or_ablation_run | minimal_supcon_dg | 1 |
| guardrailed_training_or_ablation_run | supcon_dg_pair_sampler | 1 |
| objective_or_review_creator | broader_eval | 2 |
| objective_or_review_creator | calibration | 2 |
| objective_or_review_creator | diagnostic_sanity | 1 |
| objective_or_review_creator | failure_analysis | 1 |
| objective_or_review_creator | label_policy | 2 |
| objective_or_review_creator | label_semantics_minimal_redesigned_task | 2 |
| objective_or_review_creator | label_semantics_redesigned_task | 4 |
| objective_or_review_creator | label_semantics_task_redesign | 2 |
| objective_or_review_creator | minimal_subject_relative_preprocessed | 1 |
| objective_or_review_creator | minimal_subject_relative_training | 1 |
| objective_or_review_creator | minimal_supcon_dg | 1 |
| objective_or_review_creator | representation_or_label_semantics | 1 |
| objective_or_review_creator | root_cause | 1 |
| objective_or_review_creator | script_archival | 1 |
| objective_or_review_creator | subject_relative_representation_preprocessing | 1 |
| objective_or_review_creator | subject_relative_task_formulation | 1 |
| objective_or_review_creator | subject_variability_intervention_failure | 1 |
| objective_or_review_creator | subject_variability_supcon_dg | 3 |
| objective_or_review_creator | supcon_dg_failure | 1 |
| objective_or_review_creator | supcon_dg_pair_sampler | 3 |
| objective_or_review_creator | unknown_stage | 1 |
| prepared_run_command | broader_eval | 1 |
| read_only_or_design_report_run | calibration | 2 |
| read_only_or_design_report_run | diagnostic_sanity | 2 |
| read_only_or_design_report_run | failure_analysis | 1 |
| read_only_or_design_report_run | label_semantics_redesigned_task | 3 |
| read_only_or_design_report_run | label_semantics_task_redesign | 2 |
| read_only_or_design_report_run | representation_or_label_semantics | 1 |
| read_only_or_design_report_run | root_cause | 1 |
| read_only_or_design_report_run | script_archival | 1 |
| read_only_or_design_report_run | subject_relative_representation_preprocessing | 1 |
| read_only_or_design_report_run | subject_relative_task_formulation | 1 |
| read_only_or_design_report_run | subject_variability_intervention_failure | 1 |
| read_only_or_design_report_run | subject_variability_supcon_dg | 2 |
| read_only_or_design_report_run | supcon_dg_failure | 1 |
| read_only_or_design_report_run | supcon_dg_pair_sampler | 1 |
| read_only_or_design_report_run | unknown_stage | 2 |
| uncategorized_download_script | idare_single_modality | 1 |

## Outputs

- `docs/idare_historical_script_backfill_manifest_delta.csv`
- `docs/idare_historical_script_backfill_report.md`
- `docs/idare_historical_script_backfill_report.json`
- Updated `docs/idare_script_archival_manifest.csv`
- Copied scripts under `scripts/idare/archive_or_reconstructed/from_downloads_bundle/`

## Interpretation

The historical shell-script reproducibility gap is now closed for the provided archive.

This does not certify the scripts as correct, current, or safe to execute. It only preserves the historical commands with verifiable provenance.

## Next Allowed Step

Human review / closeout, then resume the committed failure-or-confirmation analysis script:

`scripts/idare/analysis/run_idare_label_semantics_minimal_redesigned_task_failure_or_confirmation_analysis.py`

## Blocked

- executing historical scripts during archival
- running active scientific analysis before historical backfill review
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change unrelated to archival
