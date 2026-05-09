# I-DARE Alternative Pairwise Feature Patch Archive-Closeout Objective

## Status

Status: objective created; archive-closeout only; no training is authorized.

Created UTC: `2026-05-09T01:26:43+00:00`

## Scientific Question

How do we close out the narrow feature patch branch as a negative result without archiving the full pairwise formulation?

## Accepted Decision

Accepted diagnosis: `feature_patch_branch_should_be_archived_as_negative_result`

Accepted decision: `archive_patch_a_eeg_arousal_bandpower_temporal_stats_branch`

Selected patch: `PATCH_A_eeg_arousal_bandpower_temporal_stats_v1`

Selected formulation: `within_subject_pairwise_affect_preference_ranking_v1`

Best first-pass cell: `bandpower_temporal_stats_v1` / `ridge_classifier_pairwise_feature_patch`

Best mean balanced accuracy: `0.516756`

Delta vs majority baseline: `0.016756`

## Authorized Work

- Archive-closeout only.
- Preserve the feature patch branch as a negative result.
- Write an archive manifest and archive status.
- Keep the broader pairwise formulation explicitly not archived by this closeout.
- Define only post-closeout options that are read-only or spec-only.

## Not Authorized

- feature patch confirmation training
- broad hyperparameter search
- new feature patch search
- direct full SupCon/DG training
- EEG+EMG fusion
- final LOSO claim
- changing label formulation before feature patch archive closeout

## Archive Closeout Scope

`docs/idare_label_semantics_alternative_pairwise_feature_patch_archive_closeout_scope.csv`

## Manifest Seed

`docs/idare_label_semantics_alternative_pairwise_feature_patch_archive_closeout_manifest_seed.csv`

## Stop Criteria

`docs/idare_label_semantics_alternative_pairwise_feature_patch_archive_closeout_stop_criteria.csv`

## Next Option Policy

`docs/idare_label_semantics_alternative_pairwise_feature_patch_archive_closeout_next_option_policy.csv`

## Pass Criteria

- Closeout report must archive only the feature patch branch.
- Closeout report must not archive the whole pairwise formulation.
- Closeout report must not authorize training, confirmation, broad search, SupCon/DG, fusion, or final claim.
- Closeout report must identify any future work as read-only/spec-only and only after review.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_pairwise_feature_patch_archive_closeout_command`
