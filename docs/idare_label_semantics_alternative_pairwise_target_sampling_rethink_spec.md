# I-DARE Alternative Pairwise Target/Sampling Rethink Spec

## Status

Status: complete; pending human review; no training is authorized.

Created UTC: `2026-05-09T07:46:36+00:00`

## Executive Selection

Diagnosis: `target_sampling_rethink_spec_complete`

Decision: `select_margin_thresholded_within_subject_pairwise_preference_for_smoke_test_design`

Selected candidate: `TS_A_margin_thresholded_pairs`

Selected rule: `margin_thresholded_within_subject_pairwise_preference_v1`

Recommended next objective: `label_semantics_alternative_pairwise_target_sampling_rethink_smoke_tests_objective`

## Why This Rule Was Selected

The accepted audit diagnosis was `alternative_pairwise_target_sampling_audit_possible_sampling_artifact`.

The audit flagged `class_balance_issue=true`, while fold pair-count CV was modest: `0.053701`.

Therefore, the narrowest defensible rethink is not a new model, not a new feature patch, and not broad search. It is a target/sampling rule that removes ambiguous near-tie pairs and balances pair direction deterministically.

## Frozen Formulation

Formulation remains: `within_subject_pairwise_affect_preference_ranking_v1`

Pair scope: within-subject only.

Fold scope: LOSO fold-local only.

Primary future scope: arousal primary, valence as guard/control only.

## Candidate Decision Matrix

| candidate_id | decision | priority | rationale |
| --- | --- | --- | --- |
| TS_A_margin_thresholded_pairs | selected | 1 | Audit accepted a possible sampling artifact with class-balance issue; margin thresholding directly targets near-tie/ambiguous pair contamination without changing models. |
| TS_B_fold_balanced_pair_subsampling | defer | 2 | Fold pair-count CV was modest (0.053701); keep as smoke-test guard rather than primary rethink. |
| TS_C_subject_balanced_pair_quota | defer | 3 | Subject concentration audit was inconclusive in current CSV schema; add as smoke-test diagnostic, not primary rule. |
| TS_D_archive_pairwise_line | not_selected | 4 | Do not archive the full pairwise line before testing the one narrow sampling-level rethink suggested by the audit. |

## Selected Rule

| rule_id | task_scope | pair_scope | label_margin_rule | class_balance_rule | validation_rule |
| --- | --- | --- | --- | --- | --- |
| margin_thresholded_within_subject_pairwise_preference_v1 | arousal_primary_with_valence_as_guard_only | within_subject_only | eligible pair only if absolute within-subject target difference is at least the training-fold median nonzero absolute difference for that task; threshold computed on training subjects only | after margin filtering, deterministic downsample majority direction within each training fold to at most the minority direction count | apply training-derived margin threshold to validation subject pairs; no validation labels are used to choose threshold |

## Smoke-Test Plan

| test_id | name | purpose | pass_criterion |
| --- | --- | --- | --- |
| SMOKE_001 | margin_threshold_train_only | verify margin threshold is computed using training subjects only | no validation subject label contributes to threshold |
| SMOKE_002 | non_tie_pair_count_sufficient | verify margin-filtered pairs remain sufficient | each task/fold has at least 1000 validation pairs and at least 500 training pairs after balancing |
| SMOKE_003 | direction_balance_after_sampling | verify class balance artifact is reduced | positive direction fraction is within [0.45, 0.55] for every training fold and within [0.40, 0.60] for validation audit |
| SMOKE_004 | fold_locality_guard | verify pairs never cross LOSO fold boundaries | validation pairs only contain the held-out subject; training pairs exclude held-out subject |
| SMOKE_005 | task_scope_guard | verify arousal is primary and valence is guard only | future first-pass objective cannot expand beyond the selected scope without a separate review |
| SMOKE_006 | baseline_control_sanity | verify no-training baselines stay near chance | random/majority controls remain in expected range before any first-pass execution |

## Stop / Archive Criteria

| criterion_id | criterion | decision |
| --- | --- | --- |
| STOP_001 | smoke test fails fold locality or threshold leakage | archive/pause target-sampling rethink immediately |
| STOP_002 | margin filtering leaves insufficient pairs in any fold | archive/pause target-sampling rethink; do not lower threshold ad hoc |
| STOP_003 | class balance remains outside allowed range after deterministic balancing | archive/pause target-sampling rethink |
| STOP_004 | future first-pass best cell does not exceed 0.55 mean balanced accuracy or does not improve at least +0.03 over majority baseline | archive/pause pairwise line after review |
| STOP_005 | future first-pass signal is fold/subject concentrated rather than broad | read-only failure analysis before any further branch |

## Not Authorized

- training or rerun
- model fitting
- feature/model search
- broad hyperparameter search
- direct full SupCon/DG training
- EEG+EMG fusion
- final LOSO claim
- executing a redesigned sampling matrix before a separate smoke-test objective

## Interpretation

No execution is authorized by this spec.


This spec keeps the pairwise formulation alive only as a tightly constrained sampling-rule hypothesis.

The next step is a smoke-test objective for the selected rule. If the smoke tests fail, this line should be archived or paused without training.

## Next Allowed Step

`human_review_then_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_tests_objective`
