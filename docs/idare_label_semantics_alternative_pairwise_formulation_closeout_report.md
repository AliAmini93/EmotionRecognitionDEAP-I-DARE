# I-DARE Alternative Pairwise Formulation Closeout Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-10T15:31:40+00:00`

## Executive Closeout

Diagnosis: `alternative_pairwise_formulation_closed_as_reference_only`

Decision: `close_current_within_subject_pairwise_branch_as_weak_reference_baseline`

Recommendation: `proceed_to_systematic_ablation_intervention_roadmap_after_review`

Recommended next objective: `idare_systematic_ablation_intervention_roadmap_objective`

## Closed Branch

Branch: `within_subject_pairwise_affect_preference_ranking_v1`

Closeout status: `closed_reference_only_baseline`

This branch is not being erased or treated as scientifically useless. It is being closed as the current active branch because its best signal is weak and non-actionable, while preserving it as a reference comparator for future I-DARE ablations.

## Best Known Reference Baseline

| Field | Value |
|---|---|
| Modality | `EEG` |
| Task | `arousal` |
| Model | `ridge_classifier_pairwise_summary_diff` |
| Mean balanced accuracy | `0.5216709095350218` |
| Delta vs majority baseline | `0.02167090953502182` |
| Subject positive lift fraction | `` |

## Evidence Summary

| evidence_id | branch | evidence | diagnosis | key_result | interpretation |
| --- | --- | --- | --- | --- | --- |
| E001 | within_subject_pairwise_affect_preference_ranking_v1 | minimal first-pass | alternative_pairwise_minimal_first_pass_weak_mixed_signal | best=EEG arousal ridge_classifier_pairwise_summary_diff; mean_bal_acc=0.5216709095350218; delta_vs_majority=0.02167090953502182 | weak signal exists but is below practical/actionable threshold |
| E002 | pairwise metric debug | metric-debug report | alternative_pairwise_metric_debug_weak_but_consistent_signal | subject_positive_lift_fraction= | weak but somewhat consistent signal; preserve as reference, not solution |
| E003 | PATCH_A_eeg_arousal_bandpower_temporal_stats_v1 | feature patch closeout | feature_patch_branch_archived_as_negative_result | feature patch archived | simple bandpower/temporal patch did not rescue the pairwise formulation |
| E004 | target/sampling audit | read-only sampling audit | alternative_pairwise_target_sampling_audit_possible_sampling_artifact | possible sampling artifact detected | target/sampling needs systematic ablation, not ad hoc continuation |
| E005 | TS_A_margin_thresholded_pairs | smoke/fix/archive reports | target_sampling_rethink_margin_rule_should_be_archived | margin-thresholded rule archived before first-pass | new target/sampling rule failed guardrails before training |
| E006 | current broader pairwise branch | synthesis | weak_but_non_actionable_reference_baseline | close as reference-only baseline | do not spend more ad hoc iterations until systematic roadmap is defined |

## Branch Status After Closeout

| branch_id | branch | status | reason |
| --- | --- | --- | --- |
| BR001 | subject_relative_ordinal_affect_regression_v1 | archived_prior_negative_result | weak rank signal plus metric conflict; not reopened here |
| BR002 | within_subject_pairwise_affect_preference_ranking_v1 | closeout_objective_created_reference_only | weak but consistent signal; insufficient for claim; preserve as comparator |
| BR003 | PATCH_A_eeg_arousal_bandpower_temporal_stats_v1 | archived_prior_negative_result | feature patch did not improve actionable signal |
| BR004 | TS_A_margin_thresholded_pairs | archived_prior_negative_smoke_result | validation direction imbalance smoke-test failure |

## Reference Baseline Status

`docs/idare_label_semantics_alternative_pairwise_formulation_reference_baseline_status.csv`

| reference_id | formulation | status | best_modality | best_task | best_model | mean_balanced_accuracy | delta_vs_majority_baseline_bal_acc | claim_allowed | rerun_allowed | use_as_future_comparator |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REF001 | within_subject_pairwise_affect_preference_ranking_v1 | closed_reference_only_baseline | EEG | arousal | ridge_classifier_pairwise_summary_diff | 0.5216709095350218 | 0.02167090953502182 | False | False | True |
| REF002 | PATCH_A_eeg_arousal_bandpower_temporal_stats_v1 | archived_negative_result | EEG | arousal | ridge_classifier_pairwise_feature_patch |  |  | False | False | False |
| REF003 | TS_A_margin_thresholded_pairs | archived_negative_smoke_result |  |  |  |  |  | False | False | False |

## Archive Manifest

`docs/idare_label_semantics_alternative_pairwise_formulation_archive_manifest.csv`

| manifest_id | artifact | role | status |
| --- | --- | --- | --- |
| M001 | docs/idare_label_semantics_alternative_pairwise_minimal_first_pass_report.md | weak first-pass result | preserved_reference_evidence |
| M002 | docs/idare_label_semantics_alternative_pairwise_minimal_first_pass_metric_summary.csv | weak baseline metric summary | preserved_reference_evidence |
| M003 | docs/idare_label_semantics_alternative_pairwise_failure_or_metric_debug_report.md | metric-debug synthesis | preserved_reference_evidence |
| M004 | docs/idare_label_semantics_alternative_pairwise_failure_or_metric_debug_cell_audit.csv | best-cell audit | preserved_reference_evidence |
| M005 | docs/idare_label_semantics_alternative_pairwise_feature_patch_archive_closeout_report.md | feature patch negative closeout | preserved_archive_evidence |
| M006 | docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_archive_closeout_report.md | target/sampling rethink negative closeout | preserved_archive_evidence |
| M007 | docs/idare_label_semantics_alternative_pairwise_formulation_closeout_report.md | broader pairwise branch closeout report | created_primary_closeout |
| M008 | docs/idare_label_semantics_alternative_pairwise_formulation_reference_baseline_status.csv | machine-readable reference baseline status | created_primary_closeout |

## Decision Tree

| decision_id | condition | observed | decision |
| --- | --- | --- | --- |
| D001 | pairwise branch has strong actionable signal | False | do not promote to solved branch |
| D002 | pairwise branch has weak but consistent signal | True | preserve as reference baseline |
| D003 | feature patch improves pairwise branch | False | keep feature patch archived |
| D004 | target/sampling rethink passes smoke tests | False | keep TS_A archived |
| D005 | open ablations remain unstructured | True | next objective must be systematic ablation/intervention roadmap |

## Reference Policy

| policy_id | policy | meaning | applies_to |
| --- | --- | --- | --- |
| P001 | reference_baseline_only | branch may be used as comparator but not as solution claim | within_subject_pairwise_affect_preference_ranking_v1 |
| P002 | no_rerun_without_new_objective | no direct rerun or hyperparameter search is authorized | all pairwise branch scripts/results |
| P003 | future_ablation_anchor | future ablations should compare to best weak pairwise baseline when relevant | systematic ablation roadmap |
| P004 | claim_blocked | no final LOSO or solved-accuracy claim can be made from this branch | within_subject_pairwise_affect_preference_ranking_v1 |

## Next Options After Closeout

`docs/idare_label_semantics_alternative_pairwise_formulation_next_options_after_closeout.csv`

| option_id | next_option | allowed_after_human_review | recommended | reason |
| --- | --- | --- | --- | --- |
| NEXT001 | idare_systematic_ablation_intervention_roadmap_objective | True | True | all current pairwise sub-branches are closed or reference-only; next step should organize ablations and interventions |
| NEXT002 | input_definition_ablation_objective | True | False | important but should be included inside/after the systematic roadmap |
| NEXT003 | augmentation_feasibility_objective | True | False | promising but requires no-leakage guardrails and ablation priority order |
| NEXT004 | direct_training_or_search | False | False | blocked until a reviewed objective authorizes a specific run matrix |

## Interpretation

The broader within-subject pairwise formulation is now closed as the current active branch for I-DARE. The best result was weak but informative: it suggests some nonzero signal may exist, but the branch did not reach an actionable threshold and its follow-up feature/sampling sub-branches failed or were archived.

This closeout does not block future pairwise ideas forever. It blocks ad hoc continuation of this current branch. Any future pairwise-related work should re-enter through the systematic ablation/intervention roadmap with explicit guardrails for input definition, midpoint handling, sampling, augmentation, subject normalization, and representation assumptions.

No training, rerun, model fitting, first-pass execution, feature/model search, augmentation, SupCon/DG, fusion, or final LOSO claim is authorized by this report.

## Next Allowed Step

`human_review_then_idare_systematic_ablation_intervention_roadmap_objective`
