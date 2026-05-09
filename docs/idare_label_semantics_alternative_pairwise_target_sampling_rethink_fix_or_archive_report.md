# I-DARE Alternative Pairwise Target/Sampling Rethink Fix-or-Archive Report

## Status

Status: complete; pending human review.

Created UTC: `2026-05-09T08:15:52+00:00`

## Executive Decision

Diagnosis: `target_sampling_rethink_margin_rule_should_be_archived`

Decision: `archive_ts_a_margin_thresholded_pair_sampling_rule`

Recommendation: `archive_closeout_then_optional_new_target_design_only_after_review`

Recommended next objective: `label_semantics_alternative_pairwise_target_sampling_rethink_archive_closeout_objective`

Archive TS_A margin-thresholded sampling rule: `True`

Archive broader pairwise formulation: `False`

## Evidence Summary

| Check | Pass rows | Interpretation |
|---|---:|---|
| Margin threshold construction | `12/12` | train-only threshold construction was technically valid |
| Pair count sufficiency | `12/12` | pair counts were sufficient |
| Direction balance | `9/12` | failed smoke guard; this is the blocking issue |
| Fold locality | `12/12` | fold locality passed |
| Reproducibility | `3/3` | deterministic construction passed |

Maximum validation direction imbalance from 0.5: `0.141054`

Direction failure rows: `3`

Severe direction failure rows above 0.10 imbalance: `3`

Minimum balanced training pairs: `8972`

Minimum validation pairs: `1822`

## Direction Failure Audit

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_direction_failure_audit.csv`

Top failure rows:

| task | fold | train_balanced_positive_fraction | validation_positive_fraction | validation_imbalance_abs | pass | failure_mode |
| --- | --- | --- | --- | --- | --- | --- |
| arousal | 5 | 0.5 | 0.358946 | 0.141054 | False | validation_direction_imbalance |
| valence | 6 | 0.5 | 0.608939 | 0.108939 | False | validation_direction_imbalance |
| valence | 3 | 0.5 | 0.601698 | 0.101698 | False | validation_direction_imbalance |
| valence | 4 | 0.5 | 0.598476 | 0.0984757 | True | within_guard |
| valence | 1 | 0.5 | 0.597077 | 0.0970772 | True | within_guard |
| valence | 5 | 0.5 | 0.592277 | 0.0922766 | True | within_guard |

## Fix Decision Matrix

| option_id | allowed_now | selected | decision | reason |
| --- | --- | --- | --- | --- |
| FIX_A_direction_balance_train_and_validation_guard | True | False | reject_for_now | would require validation-direction-aware evaluation sampling; do not patch into first-pass without a new target design |
| FIX_B_adaptive_train_only_margin_quantile | True | False | reject_for_now | a lower train-only margin threshold may reduce imbalance but also reintroduces near-tie noise; speculative after failed smoke |
| FIX_C_task_specific_arousal_only_rule | True | False | defer | arousal-only narrowing may be defensible, but it changes claim scope and needs a separate spec rather than a patch to TS_A |
| ARCHIVE_TS_A | True | True | select | the TS_A margin-thresholded rule failed a pre-training smoke guard on validation direction balance |
| STOP_PAIRWISE_LABEL_SEMANTICS_BRANCH | False | False | not_authorized_here | broader pairwise formulation remains open; only the TS_A rethink rule should be closed by this branch |

## Next Options

| option_id | next_option | allowed_after_review | recommended | objective |
| --- | --- | --- | --- | --- |
| NEXT_001 | archive_ts_a_margin_thresholded_sampling_rule | True | True | label_semantics_alternative_pairwise_target_sampling_rethink_archive_closeout_objective |
| NEXT_002 | new_target_design_spec_not_patch | True | False | future_label_semantics_pairwise_target_design_spec_objective |
| NEXT_003 | direction_balance_patch_first_pass | False | False | blocked_without_new_spec_and_smoke |
| NEXT_004 | train_or_model_fit_now | False | False | blocked |

## Interpretation

The margin-thresholded target/sampling rethink did not fail because of too few pairs, fold leakage, or nondeterminism. It failed because validation direction balance remained too skewed in at least one fold/task.

A quick patch would likely need validation-direction-aware sampling or a changed target definition. That is too close to optimizing the evaluation construction after seeing the validation-label distribution. So the conservative decision is to archive the TS_A margin-thresholded rule as a negative smoke result, while keeping the broader pairwise formulation open for a separately justified target design.

No training, rerun, model fitting, first-pass execution, feature/model search, SupCon/DG, fusion, or final LOSO claim is authorized by this report.

## Next Allowed Step

`human_review_then_label_semantics_alternative_pairwise_target_sampling_rethink_archive_closeout_objective`
