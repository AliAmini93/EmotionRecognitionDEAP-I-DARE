# I-DARE Label-Semantics Alternative-Formulation Smoke Tests Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-08T16:47:26+00:00`

## Executive Result

Selected formulation: `within_subject_pairwise_affect_preference_ranking_v1`

Diagnosis: `alternative_pairwise_formulation_smoke_tests_passed`

All smoke tests passed: `True`

Recommended next objective: `label_semantics_alternative_pairwise_minimal_first_pass_objective`

## Detected Label Columns

- Subject column: `subject_id`
- Trial column: `stimulus_id`
- Valence column: `valence_score`
- Arousal column: `arousal_score`

## Pair Target Audit

| task | n_subjects | n_trials | rating_unique_values | margin | unique_pairs_kept | retention_rate | subjects_with_zero_pairs | target_construction_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| valence | 63 | 2016 | 9 | 1.0 | 26754 | 0.8561827956989247 | 0 | True |
| arousal | 63 | 2016 | 9 | 1.0 | 26096 | 0.8351254480286738 | 0 | True |

## Pair Balance Audit

| task | unique_pairs_kept | oriented_pairs_if_counterbalanced | retention_rate | canonical_positive_rate | counterbalanced_positive_rate | min_val_pairs_per_fold | pair_balance_pass |
| --- | --- | --- | --- | --- | --- | --- | --- |
| valence | 26754 | 53508 | 0.8561827956989247 | 0.5174553337818644 | 0.5 | 364 | True |
| arousal | 26096 | 52192 | 0.8351254480286738 | 0.5575950337216432 | 0.5 | 313 | True |

## Baseline Control

| task | canonical_majority_baseline | counterbalanced_majority_baseline | position_shortcut_risk | baseline_control_pass |
| --- | --- | --- | --- | --- |
| valence | 0.5174553337818644 | 0.5 | low_or_moderate | True |
| arousal | 0.5575950337216432 | 0.5 | low_or_moderate | True |

## Metric Sanity

| case | balanced_accuracy | macro_f1 | expected_behavior_pass |
| --- | --- | --- | --- |
| perfect | 1.0 | 1.0 | True |
| random | 0.477 | 0.4769743717442154 | True |
| shuffled_labels | 0.46 | 0.46 | True |
| majority_zero | 0.5 | 0.3333333333333333 | True |

## Smoke-Test Decision Matrix

| smoke_test | passed | evidence | interpretation |
| --- | --- | --- | --- |
| pair_target_construction_integrity | True | docs/idare_label_semantics_alternative_formulation_pair_target_audit.csv | Pairwise targets are constructible with ordered within-subject ratings. |
| LOSO_pair_leakage_guard | True | docs/idare_label_semantics_alternative_formulation_pair_fold_audit.csv | LOSO pair partitions are subject-disjoint and leak-free. |
| pair_retention_balance_audit | True | docs/idare_label_semantics_alternative_formulation_pair_balance_audit.csv | Pair retention and fold coverage are sufficient for a later minimal first-pass design. |
| position_and_majority_baseline_control | True | docs/idare_label_semantics_alternative_formulation_pair_baseline_control.csv | Counterbalanced orientation plan blocks trivial majority/position shortcut. |
| metric_sanity_control | True | docs/idare_label_semantics_alternative_formulation_pair_metric_sanity.csv | Pairwise metrics behave correctly on synthetic sanity controls. |
| reproducibility_guard | True | docs/idare_label_semantics_alternative_formulation_smoke_reproducibility_audit.csv | Committed script exists for replay. |

## Interpretation

These smoke tests do not train any model. They only evaluate whether the selected within-subject pairwise formulation is a valid candidate for a later minimal first-pass objective.

If all smoke tests pass after human review, the next scientific step is to create a tightly guardrailed minimal first-pass objective. If any hard gate fails, the next step is patch-or-archive, not training.

## Next Allowed Step

`human_review_closeout_then_create_alternative_pairwise_minimal_first_pass_objective`

## Blocked

- training before smoke-test review
- model search
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
