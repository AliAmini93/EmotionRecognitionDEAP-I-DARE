# I-DARE Alternative Pairwise Target/Sampling Rethink Smoke-Tests Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-09T08:02:58+00:00`

## Executive Result

Diagnosis: `target_sampling_rethink_smoke_tests_failed`

All smoke tests passed: `False`

Recommendation: `archive_or_revise_target_sampling_rethink_after_review`

Recommended next objective: `label_semantics_alternative_pairwise_target_sampling_rethink_fix_or_archive_objective`

Selected rule: `margin_thresholded_within_subject_pairwise_preference_v1`

## Detected Columns

Subject column: `subject_id`

Trial/sample column: `__row_id__`

Target columns: `{'valence': 'valence_score', 'arousal': 'arousal_score'}`

Subjects: `63`

Folds: `6`

## Margin Threshold Audit

Minimum train-only margin threshold: `3`

Maximum train-only margin threshold: `3`

Validation labels used for threshold selection: `False`

Audit file: `docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_margin_threshold_audit.csv`

## Pair Count Audit

Minimum balanced training pairs after margin filtering: `8972`

Minimum validation pairs after margin filtering: `1822`

Required minimum balanced training pairs: `500`

Required minimum validation pairs: `1000`

Audit file: `docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_pair_count_audit.csv`

## Direction Balance Audit

Maximum absolute validation direction imbalance from 0.5: `0.141054`

Training direction balance is deterministic after downsampling.

Audit file: `docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_direction_balance_audit.csv`

## Fold Locality Audit

Within-subject only: `True`

Cross-fold pairs constructed: `False`

Audit file: `docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_fold_locality_audit.csv`

## Reproducibility Audit

Digest stable: `True`

Audit file: `docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_reproducibility_audit.csv`

## Smoke Decision Matrix

| check_id | check_name | status | required_for_pass | interpretation |
| --- | --- | --- | --- | --- |
| D001 | train_only_margin_threshold | pass | True | margin thresholds are positive and computed from training subjects only |
| D002 | pair_count_sufficiency | pass | True | margin filtering leaves enough train and validation pairs |
| D003 | direction_balance | fail | True | deterministic balancing fixes training direction imbalance and validation remains within guard range |
| D004 | fold_locality | pass | True | no train/validation subject overlap and no cross-fold pairs |
| D005 | reproducibility | pass | True | deterministic digest is stable |
| D006 | overall_smoke_result | fail | True | one or more required smoke checks failed |

## Interpretation

The selected margin-thresholded within-subject pairwise sampling rule is smoke-tested only.

No training, model fitting, feature/model search, SupCon/DG, fusion, or final LOSO claim is authorized by this report.

## Next Allowed Step

`human_review_then_label_semantics_alternative_pairwise_target_sampling_rethink_fix_or_archive_objective`
