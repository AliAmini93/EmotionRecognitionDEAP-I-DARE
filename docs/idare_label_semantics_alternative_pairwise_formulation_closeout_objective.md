# I-DARE Alternative Pairwise Formulation Closeout Objective

## Status

Status: objective created; read-only closeout only; no training is authorized.

Created UTC: `2026-05-10T15:26:04+00:00`

## Scientific Question

Should the broader `within_subject_pairwise_affect_preference_ranking_v1` branch remain active, or should the current branch be closed as a weak reference-only baseline before systematic ablation planning?

## Accepted Context

The broader pairwise branch produced a weak but somewhat consistent signal, not a strong actionable result.

Best known cell:

| Field | Value |
|---|---|
| Modality | `EEG` |
| Task | `arousal` |
| Model | `ridge_classifier_pairwise_summary_diff` |
| Mean balanced accuracy | `0.5216709095350218` |
| Delta vs majority baseline | `0.02167090953502182` |
| Subject positive lift fraction | `` |

## Decision Target

`close_current_broader_pairwise_branch_as_reference_only`

The closeout should not erase the pairwise work. It should close the current branch as a **reference-only baseline** and stop ad hoc continuation until a systematic ablation/intervention roadmap is reviewed.

## Authorized Work

- Create a read-only closeout report for the current broader pairwise formulation branch.
- Preserve current weak pairwise result as a reference-only baseline.
- Explicitly block training/rerun/search until a new reviewed objective exists.
- Recommend systematic ablation/intervention roadmap as the next scientific step.

## Not Authorized

- No training.
- No rerun.
- No model fitting.
- No first-pass execution.
- No feature/model/hyperparameter search.
- No augmentation run.
- No SupCon/DG run.
- No EEG+EMG fusion.
- No final LOSO claim.

## Evidence Summary

| evidence_id | branch | diagnosis | key_result | interpretation |
| --- | --- | --- | --- | --- |
| E001 | within_subject_pairwise_affect_preference_ranking_v1 | alternative_pairwise_minimal_first_pass_weak_mixed_signal | best=EEG arousal ridge_classifier_pairwise_summary_diff; mean_bal_acc=0.5216709095350218; delta_vs_majority=0.02167090953502182 | weak signal exists but is below practical/actionable threshold |
| E002 | pairwise metric debug | alternative_pairwise_metric_debug_weak_but_consistent_signal | subject_positive_lift_fraction= | weak but somewhat consistent signal; preserve as reference, not solution |
| E003 | PATCH_A_eeg_arousal_bandpower_temporal_stats_v1 | feature_patch_branch_archived_as_negative_result | feature patch archived | simple bandpower/temporal patch did not rescue the pairwise formulation |
| E004 | target/sampling audit | alternative_pairwise_target_sampling_audit_possible_sampling_artifact | possible sampling artifact detected | target/sampling needs systematic ablation, not ad hoc continuation |
| E005 | TS_A_margin_thresholded_pairs | target_sampling_rethink_margin_rule_should_be_archived | margin-thresholded rule archived before first-pass | new target/sampling rule failed guardrails before training |
| E006 | current broader pairwise branch | weak_but_non_actionable_reference_baseline | close as reference-only baseline | do not spend more ad hoc iterations until systematic roadmap is defined |

## Branch Status

| branch_id | branch | status | reason |
| --- | --- | --- | --- |
| BR001 | subject_relative_ordinal_affect_regression_v1 | archived_prior_negative_result | weak rank signal plus metric conflict; not reopened here |
| BR002 | within_subject_pairwise_affect_preference_ranking_v1 | closeout_objective_created_reference_only | weak but consistent signal; insufficient for claim; preserve as comparator |
| BR003 | PATCH_A_eeg_arousal_bandpower_temporal_stats_v1 | archived_prior_negative_result | feature patch did not improve actionable signal |
| BR004 | TS_A_margin_thresholded_pairs | archived_prior_negative_smoke_result | validation direction imbalance smoke-test failure |

## Closeout Scope

| scope_id | item | action | allowed | rationale |
| --- | --- | --- | --- | --- |
| S001 | within_subject_pairwise_affect_preference_ranking_v1 | close current branch as reference-only baseline | True | best result is weak/non-actionable but useful as comparator |
| S002 | current_summary_diff_pairwise_baseline_outputs | preserve as reference artifacts | True | future ablations need a stable anchor |
| S003 | new training or first-pass rerun | not allowed | False | closeout is decision/documentation only |
| S004 | augmentation/SupCon/input ablations | not allowed in this objective | False | must be planned in systematic roadmap |

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

## Pass Criteria

- Closeout report states that current broader pairwise branch is closed as reference-only baseline.
- Report preserves weak pairwise baseline as comparator, not as solved claim.
- Report does not archive unrelated future ablation directions.
- Report recommends systematic ablation/intervention roadmap.
- All training/search/fusion/final-claim authorizations remain false.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_pairwise_formulation_closeout_report`
