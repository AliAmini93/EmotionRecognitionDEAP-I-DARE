# I-DARE Alternative Pairwise Feature Patch Archive-Closeout Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-09T01:30:55+00:00`

## Executive Closeout

Diagnosis: `feature_patch_branch_archived_as_negative_result`

Decision: `archive_closeout_complete_for_patch_a_eeg_arousal_bandpower_temporal_stats`

Recommendation: `optional_read_only_pairwise_target_sampling_audit_after_review`

Recommended next objective: `label_semantics_alternative_pairwise_target_sampling_audit_objective`

## What Is Archived

The narrow feature patch branch is archived:

`PATCH_A_eeg_arousal_bandpower_temporal_stats_v1`

Best observed cell:

`bandpower_temporal_stats_v1` / `ridge_classifier_pairwise_feature_patch`

Best mean balanced accuracy: `0.516756`

Delta vs majority baseline: `0.016756`

## What Is Not Archived

The broader pairwise formulation is not archived by this closeout:

`within_subject_pairwise_affect_preference_ranking_v1`

## Archive Status

| status_id | component | archive_status | rationale |
| --- | --- | --- | --- |
| STATUS_001 | PATCH_A_eeg_arousal_bandpower_temporal_stats_v1 | archived_as_negative_result | best mean balanced accuracy and fold thresholds did not justify confirmation |
| STATUS_002 | bandpower_temporal_stats_v1 | best_cell_preserved | best cell ridge_classifier_pairwise_feature_patch; mean balanced accuracy 0.516756; delta vs majority 0.016756 |
| STATUS_003 | within_subject_pairwise_affect_preference_ranking_v1 | not_archived_by_this_closeout | feature patch closeout does not invalidate the entire pairwise formulation |
| STATUS_004 | future training/search | blocked | no confirmation, broad search, SupCon/DG, fusion, or final LOSO claim authorized |

## Archive Manifest

| manifest_id | artifact | role | archive_status | notes |
| --- | --- | --- | --- | --- |
| ARCH_MAN_001 | docs/idare_label_semantics_alternative_pairwise_feature_patch_archive_closeout_objective.md | archive-closeout objective | included | defines closeout scope and guardrails |
| ARCH_MAN_002 | docs/idare_label_semantics_alternative_pairwise_feature_patch_archive_closeout_report.md | archive-closeout report | generated_by_this_run | final closeout artifact for this branch |
| ARCH_MAN_003 | docs/idare_label_semantics_alternative_pairwise_feature_patch_archive_or_rethink_report.md | archive/rethink evidence | included | accepted decision to archive feature patch branch only |
| ARCH_MAN_004 | docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_report.md | first-pass evidence | included | source negative/non-actionable result |
| ARCH_MAN_005 | docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_runs.csv | run-level evidence | included | frozen 96-row run outputs |
| ARCH_MAN_006 | docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_metric_summary.csv | metric summary evidence | included | best cell and feature-set comparison |
| ARCH_MAN_007 | scripts/idare/analysis/run_idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass.py | reproducibility script | included | committed script used for first-pass run |
| ARCH_MAN_008 | docs/idare_label_semantics_alternative_pairwise_feature_patch_archive_closeout_scope.csv | closeout scope | included | states patch-only archive and pairwise formulation remains open |
| ARCH_MAN_009 | docs/idare_label_semantics_alternative_pairwise_feature_patch_archive_closeout_stop_criteria.csv | stop criteria | included | criteria supporting branch closeout |

## Stop Criteria

| criterion_id | criterion | observed | met |
| --- | --- | --- | --- |
| STOP_001 | best mean balanced accuracy below 0.53 | 0.5167558046828528 | True |
| STOP_002 | delta vs majority below 0.03 | 0.01675580468285276 | True |
| STOP_003 | no fold over 0.55 | 0 | True |
| STOP_004 | archive/rethink accepted feature patch archive, not whole formulation archive | archive_feature_patch_branch=true; archive_entire_pairwise_formulation=false | True |

## Next Options After Closeout

| rank | next_option | type | allowed_after_review | why |
| --- | --- | --- | --- | --- |
| 1 | label_semantics_alternative_pairwise_target_sampling_audit_objective | read_only_objective | True | audit whether target/pair construction diluted the weak pairwise signal without new training |
| 2 | pause_pairwise_line_after_feature_patch_archive | pause | True | acceptable if no target/sampling audit is desired |
| 3 | new_feature_patch_search | blocked | False | would become broad feature/model search after non-actionable evidence |
| 4 | SupCon_DG_or_fusion | blocked | False | not supported by this branch and outside authorization |

## Interpretation

The feature-representation patch branch is now closed as a negative result. The result is scientifically useful because it prevents further narrow feature-patch searching on this branch.

The pairwise formulation remains open only for read-only/spec-only follow-up, especially target/sampling audit. No training or broad search is authorized by this closeout.

## Next Allowed Step

`human_review_closeout_then_optional_target_sampling_audit_objective`
