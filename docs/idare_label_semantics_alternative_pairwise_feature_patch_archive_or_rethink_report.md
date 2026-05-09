# I-DARE Alternative Pairwise Feature Patch Archive-or-Rethink Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-09T01:22:22+00:00`

## Executive Decision

Diagnosis: `feature_patch_branch_should_be_archived_as_negative_result`

Decision: `archive_patch_a_eeg_arousal_bandpower_temporal_stats_branch`

Recommendation: `archive_feature_patch_closeout_then_optional_read_only_pairwise_target_sampling_audit`

Recommended next objective: `label_semantics_alternative_pairwise_feature_patch_archive_closeout_objective`

## Evidence Summary

| Metric | Value | Interpretation |
|---|---:|---|
| best feature set | `bandpower_temporal_stats_v1` | best observed feature patch cell |
| best model | `ridge_classifier_pairwise_feature_patch` | best observed model in frozen matrix |
| mean balanced accuracy | `0.516756` | below actionable threshold |
| delta vs majority baseline | `0.016756` | too small for confirmation |
| delta vs random baseline | `0.016160` | too small for confirmation |
| folds over 0.55 | `0` | no fold passed practical threshold |
| folds under 0.45 | `0` | no collapse, but not confirmatory |
| subject positive lift fraction | `0.396825` | not enough to override weak aggregate signal |

## Archive Decision

| decision_id | scope | item | decision | reason |
| --- | --- | --- | --- | --- |
| ARCH_DEC_001 | feature patch branch only | PATCH_A_eeg_arousal_bandpower_temporal_stats_v1 | archive | best mean balanced accuracy below 0.53 and no fold over 0.55 |
| ARCH_DEC_002 | current pairwise formulation | within_subject_pairwise_affect_preference_ranking_v1 | do_not_archive_here | this report only evaluates the feature patch; pairwise formulation was not fully invalidated |
| ARCH_DEC_003 | confirmation training | feature patch confirmation | not_authorized | mean balanced accuracy and fold thresholds were not met |
| ARCH_DEC_004 | future work | target/sampling audit | optional_read_only_after_archive_closeout | weak pairwise signal may still merit read-only target/sampling analysis, not new training |

## Rethink Decision Matrix

| option_id | option | allowed | recommended | training_required | rationale |
| --- | --- | --- | --- | --- | --- |
| OPT_001 | archive_feature_patch_closeout | True | True | False | preserves negative result and prevents repeated patch search |
| OPT_002 | read_only_pairwise_target_sampling_audit | True | True | False | may explain weak signal without launching new training |
| OPT_003 | new_feature_patch_search | False | False | True | would become broad feature/model search after a weak first-pass |
| OPT_004 | feature_patch_confirmation | False | False | True | thresholds for confirmation were not met |
| OPT_005 | jump_to_supcon_dg | False | False | True | not justified by patch evidence and outside current scope |

## Next Options After Archive

| rank | next_option | type | allowed_after_review | why |
| --- | --- | --- | --- | --- |
| 1 | label_semantics_alternative_pairwise_feature_patch_archive_closeout_objective | archive_closeout | True | close feature patch branch as negative result |
| 2 | pairwise_target_sampling_read_only_audit_objective | optional_read_only |  | inspect whether target/pair construction diluted signal before any new formulation |
| 3 | new_feature_or_model_search | blocked | False | would be broad search after non-actionable evidence |
| 4 | supcon_dg_or_fusion | blocked | False | outside authorized scope and not supported by evidence |

## Interpretation

The feature patch produced a small positive lift, but not an actionable or confirmatory signal.

This report archives only the narrow feature-representation patch branch. It does not archive the entire pairwise formulation.

The next safe step is archive closeout for this patch branch, followed only optionally by read-only target/sampling audit.

## Next Allowed Step

`human_review_closeout_then_create_feature_patch_archive_closeout_objective`
