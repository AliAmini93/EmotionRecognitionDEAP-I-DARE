# I-DARE Label-Semantics Alternative-Formulation Design Spec

## Status

Status: complete; pending human review; no training is authorized.

Created UTC: `2026-05-08T15:53:15+00:00`

## Executive Selection

Diagnosis: `alternative_formulation_design_spec_complete`

Decision: `select_within_subject_pairwise_preference_ranking_for_smoke_test_design`

Selected primary formulation: `within_subject_pairwise_affect_preference_ranking_v1`

Selected candidate: `ALT_A_within_subject_pairwise_preference_ranking`

Recommended next objective: `label_semantics_alternative_formulation_smoke_tests_objective`

## Archived Failure Mode Being Avoided

Archived formulation: `subject_relative_ordinal_affect_regression_v1`

The archived branch failed because the current subject-relative ordinal/continuous formulation produced no actionable signal: max mean Spearman was approximately `0.019171068580299766`, q33 was approximately `0.5070515450953589`, and no cells improved MAE/RMSE over the mean baseline.

The selected alternative changes the question from continuous subject-relative regression to within-subject pairwise preference ranking. This is materially different because it treats each subject's affect scale locally and evaluates pairwise preference consistency rather than absolute continuous error.

## Candidate Decision Matrix

| candidate_id | decision | material_difference_from_archived | metric_alignment | main_risk | selected |
| --- | --- | --- | --- | --- | --- |
| ALT_A_within_subject_pairwise_preference_ranking | selected_primary | Changes target from subject-relative continuous/rank regression to within-subject pairwise preference labels. | Primary metric becomes pairwise ranking accuracy/balanced accuracy instead of weak continuous MAE/RMSE rescue. | Pair construction can introduce leakage or inflated dependence if pairs cross folds or reuse held-out trials. | yes |
| ALT_B_subject_centered_continuous_regression_v2 | rejected_too_close_to_archived | Insufficient; still attempts a continuous subject-normalized target similar to archived branch. | High risk of repeating Spearman vs MAE/RMSE conflict. | Rename/retry of archived branch. | no |
| ALT_C_extreme_within_subject_contrast_classification | reserve_candidate | Uses only high-confidence top/bottom within-subject contrasts. | Classification metrics align better than continuous MAE/RMSE, but sample retention may be poor. | Retention and fold balance may be too low. | no |
| ALT_D_stop_line_no_new_task | fallback_if_smokes_fail | No new formulation. | Avoids further weak task search. | Ends this line without further exploration. | no |

## Selected Task Definition

| field | value | locked | notes |
| --- | --- | --- | --- |
| formulation_id | within_subject_pairwise_affect_preference_ranking_v1 | yes | Selected design/spec candidate; not yet authorized for training. |
| base_candidate | ALT_A_within_subject_pairwise_preference_ranking | yes | Primary alternative candidate selected from candidate matrix. |
| target_type | binary_pairwise_within_subject_preference | yes | For a pair of trials from the same subject and same affect dimension, predict which trial has the higher rating. |
| pair_scope | within_subject_only | yes | No cross-subject positive/negative target semantics; subject rating scale is treated as local. |
| affect_dimensions | valence,arousal | yes | Each dimension must be audited separately. |
| minimum_rating_margin_seed | >=1.0_original_DEAP_rating_point_or_quantile_separation_if_original_scale_unavailable | no | Exact threshold must be finalized by smoke-test target audit; ambiguous/tied pairs are excluded. |
| pair_direction | label_1_if_anchor_rating_higher_than_comparison_else_0 | yes | Pair order must be randomized/balanced during future implementation to avoid positional shortcuts. |
| fold_protocol | LOSO_subject_disjoint_pairs | yes | All pairs involving held-out subjects must be validation/test only; train pairs contain train subjects only. |
| allowed_modalities_for_future_smokes | metadata_only_or_summary_feature_audits; no model training | yes | This spec does not authorize EEG/EMG training. |
| archived_formulation_reuse | forbidden | yes | Must not reproduce subject_relative_ordinal_affect_regression_v1 unchanged. |

## Metric Plan

| metric_id | metric | role | why_aligned | minimum_interesting_signal_for_future_first_pass | failure_condition |
| --- | --- | --- | --- | --- | --- |
| METRIC_ALT_001 | pairwise_balanced_accuracy | primary | Target is binary pairwise preference; balanced accuracy handles label imbalance. | mean >= 0.55 across folds and no catastrophic fold below 0.45 | near chance across folds or driven by one subject/fold |
| METRIC_ALT_002 | pairwise_macro_f1 | primary_support | Checks whether both preference directions are predicted, not one-class behavior. | mean >= 0.55 with zero one-class folds | one-class predictions or macro_f1 near 0.50 |
| METRIC_ALT_003 | per_subject_pairwise_accuracy_distribution | stability | Ensures signal is not concentrated in a few subjects. | positive lift over trivial baseline for a majority of held-out subjects | lift explained by few subjects or fold artifacts |
| METRIC_ALT_004 | trivial_baseline_delta | control | Pairwise task must beat random/majority/position baselines. | positive delta over random/majority/position controls | model does not beat no-feature controls |
| METRIC_ALT_005 | pair_retention_and_balance | pre_training_gate | Pairwise formulation is only usable if enough balanced pairs exist. | predeclared retention and class balance thresholds pass in smoke tests | too few pairs, severe imbalance, or fold-specific collapse |
| METRIC_ALT_006 | leakage_guard_pass | hard_gate | Pairs can leak if trial IDs cross train/test or if reversed duplicates are mishandled. | all leakage checks pass | any row, subject, pair, or reversed-pair leakage |

## Smoke-Test Plan

| smoke_id | name | scope | purpose | pass_criteria |
| --- | --- | --- | --- | --- |
| SMOKE_ALT_001 | pair_target_construction_integrity | valence/arousal; metadata only | Verify pair labels are constructible, non-ambiguous, and not dominated by ties. | All pairs have valid labels; tie/ambiguous exclusion is documented; per-task counts are nonzero. |
| SMOKE_ALT_002 | LOSO_pair_leakage_guard | all future folds | Verify train/test pairs are subject-disjoint and no trial pair or reversed pair leaks across folds. | subject_overlap=0; pair_overlap=0; reversed_pair_overlap=0; row_overlap=0 |
| SMOKE_ALT_003 | pair_retention_balance_audit | candidate formulation before training | Check whether enough pairs remain after margin/tie rules and whether labels are balanced. | retention, label balance, and fold coverage meet thresholds declared in the smoke objective |
| SMOKE_ALT_004 | position_and_majority_baseline_control | no-training controls | Ensure the target is not solved by pair order, majority class, or fold artifacts. | randomized pair order and no-feature controls remain near expected chance behavior |
| SMOKE_ALT_005 | metric_sanity_control | synthetic labels and shuffled labels | Verify pairwise metrics respond correctly to perfect, random, and shuffled predictions. | perfect synthetic cases score high; shuffled controls remain near chance |
| SMOKE_ALT_006 | reproducibility_guard | script/report generation | Ensure future executable smoke-test code is committed under scripts/idare or archived before use. | script path and manifest are committed before any smoke-test run |

## Stop / Archive Criteria

| criterion_id | phase | stop_condition | decision | rationale |
| --- | --- | --- | --- | --- |
| STOP_ALT_001 | design_spec | No candidate is materially different from the archived formulation. | stop_line_closeout | Avoid renaming/retrying archived failure. |
| STOP_ALT_002 | smoke_tests | Pair construction has low retention, severe imbalance, or leakage. | archive_alternative_before_training | Do not train on invalid pair semantics. |
| STOP_ALT_003 | smoke_tests | No-training controls reveal position/order/fold shortcuts. | fix_or_stop_before_training | Prevent false confidence from artifacts. |
| STOP_ALT_004 | minimal_first_pass_if_later_authorized | Mean pairwise balanced accuracy and macro F1 remain near chance or unstable across folds. | archive_alternative_branch | Avoid broad search on a weak alternative. |
| STOP_ALT_005 | any_phase | A proposed step requests broad search, SupCon/DG, fusion, or final claims before smoke-test evidence. | reject_step | Preserve guardrails after archived negative result. |

## Interpretation

The selected alternative is not approved for training. It is only approved, after human review, for a separate smoke-test objective.

The key scientific bet is narrow: within-subject pairwise affect preferences may be more defensible than global or subject-relative continuous regression because they avoid cross-subject scale mismatch and align metrics with a local preference target.

## Next Allowed Step

Human review / closeout, then create a guardrailed alternative-formulation smoke-tests objective.

## Blocked

- training
- model search
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- implementation before design/spec review
- reopening archived `subject_relative_ordinal_affect_regression_v1` unchanged
