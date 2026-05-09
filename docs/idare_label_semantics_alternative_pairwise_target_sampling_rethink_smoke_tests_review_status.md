# I-DARE Alternative Pairwise Target/Sampling Rethink Smoke-Tests Review Status

## Status

Status: human review accepted.

Created UTC: `2026-05-09T08:10:20+00:00`

## Review Decision

Accepted diagnosis: `target_sampling_rethink_smoke_tests_failed`

All smoke tests passed: `False`

Accepted recommended next objective: `label_semantics_alternative_pairwise_target_sampling_rethink_fix_or_archive_objective`

Selected rule under review: `margin_thresholded_within_subject_pairwise_preference_v1`

## Main Failure Signal

The smoke-test failure is driven by target/direction balance after the margin-thresholded rule, not by pair-count sufficiency, fold-locality, or reproducibility.

Maximum validation direction imbalance from 0.5: `0.1410537870472009`

Minimum balanced training pairs: `8972`

Minimum validation pairs: `1822`

## Next Allowed Step

`create_target_sampling_rethink_fix_or_archive_objective`
