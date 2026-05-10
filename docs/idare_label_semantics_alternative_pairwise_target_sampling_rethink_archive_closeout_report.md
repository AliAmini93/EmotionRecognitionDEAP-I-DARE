# I-DARE Alternative Pairwise Target/Sampling Rethink Archive-Closeout Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-10T12:22:31+00:00`

## Executive Closeout

Diagnosis: `target_sampling_rethink_rule_archived_as_negative_smoke_result`

Decision: `archive_closeout_complete_for_ts_a_margin_thresholded_pair_sampling_rule`

Recommendation: `create_systematic_ablation_intervention_roadmap_after_review`

Recommended next objective: `idare_systematic_ablation_intervention_roadmap_objective`

Archive TS_A margin-thresholded rule: `True`

Archive broader pairwise formulation: `False`

## What Is Archived

| item_id | item | status | reason |
| --- | --- | --- | --- |
| ARCHIVE_001 | TS_A_margin_thresholded_pairs | archived_negative_smoke_result | margin-thresholded target/sampling rethink failed validation direction balance smoke guard |
| ARCHIVE_002 | margin_thresholded_within_subject_pairwise_preference_v1 | archived_negative_smoke_result | rule is blocked from first-pass execution |

## What Is Not Archived

| item_id | item | status | reason |
| --- | --- | --- | --- |
| ARCHIVE_003 | within_subject_pairwise_affect_preference_ranking_v1 | not_archived_keep_open | broader within-subject pairwise formulation remains open pending systematic ablation roadmap |
| ARCHIVE_004 | feature_patch_branch | already_archived_prior_negative_result | not reopened by this target/sampling closeout |

## Evidence Summary

| Evidence | Value |
|---|---:|
| Direction failure rows | `3` |
| Severe direction failure rows > 0.10 | `3` |
| Max validation direction imbalance from 0.5 | `0.1410537870472009` |
| Archive manifest rows | `10` |
| Archive status rows | `4` |

## Archive Manifest

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_archive_manifest.csv`

| manifest_id | artifact | role | archive_status | closeout_status |
| --- | --- | --- | --- | --- |
| M001 | docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_spec.md | archived TS_A target/sampling rethink spec | negative_smoke_result_context | included |
| M002 | docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_tests_report.md | failed smoke-test report | primary evidence | included |
| M003 | docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_direction_balance_audit.csv | direction-balance failure evidence | primary evidence | included |
| M004 | docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_fix_or_archive_report.md | archive decision report | primary decision | included |
| M005 | docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_fix_decision_matrix.csv | fix/archive decision matrix | decision support | included |
| M006 | scripts/idare/analysis/run_idare_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_tests.py | committed reproducible smoke-test script | reproducibility evidence | included |
| M007 | docs/idare_label_semantics_alternative_pairwise_target_sampling_audit_report.md | upstream sampling artifact audit | context | included |
| M008 | docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_archive_closeout_report.md | final archive-closeout report | primary closeout | created |
| M009 | docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_archive_status.csv | machine-readable archive status | primary closeout | created |
| M010 | docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_next_options_after_closeout.csv | post-closeout next options | decision handoff | created |

## Stop Criteria

| criterion_id | criterion | satisfied |
| --- | --- | --- |
| STOP_001 | No first-pass training is allowed for TS_A margin-thresholded sampling. | True |
| STOP_002 | No validation-direction-aware sampling patch is allowed without a new target-design spec and smoke objective. | True |
| STOP_003 | Broader pairwise formulation is not closed by this archive closeout. | True |
| STOP_004 | Any future target design must be a new reviewed objective before execution. | True |

## Next Options After Closeout

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_next_options_after_closeout.csv`

| option_id | next_option | allowed_after_human_review | recommended | reason |
| --- | --- | --- | --- | --- |
| NEXT_001 | idare_systematic_ablation_intervention_roadmap_objective | True | True | before trying augmentation/SupCon/new sampling, consolidate open ablations and diagnosis rules |
| NEXT_002 | new_pairwise_target_design_spec | True | False | should be subordinate to the systematic roadmap, not launched ad hoc |
| NEXT_003 | augmentation_feasibility_objective | True | False | promising, but should be placed in ablation roadmap with leakage guardrails first |
| NEXT_004 | training_or_first_pass_now | False | False | blocked until a reviewed objective authorizes it |

## Interpretation

The TS_A margin-thresholded target/sampling rethink branch is now closed as a negative smoke result. Its failure mode was not insufficient pair count or fold leakage; the decisive blocker was validation direction imbalance under the proposed margin-thresholded sampling rule.

This closeout does not invalidate the broader within-subject pairwise formulation. It only closes this specific target/sampling rethink rule and blocks it from first-pass execution.

The clean next scientific move is not to immediately launch another experiment. The next recommended move is a systematic I-DARE ablation/intervention roadmap objective that explicitly tracks label formulation, midpoint handling, Signal-vs-Baseline input assumptions, sampling, augmentation, and future SupCon/DG assumptions.

No training, rerun, model fitting, first-pass execution, feature/model search, SupCon/DG, fusion, or final LOSO claim is authorized by this report.

## Next Allowed Step

`human_review_then_idare_systematic_ablation_intervention_roadmap_objective`
