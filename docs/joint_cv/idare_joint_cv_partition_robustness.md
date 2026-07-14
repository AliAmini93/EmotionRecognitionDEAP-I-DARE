# I-DARE Joint-CV Partition Robustness Audit

No model training was performed.

## Why This Audit Was Necessary

The current candidate folds were constructed using label-support profiles. Stratification can be acceptable for a benchmark, but the apparent feasibility must not depend on a specially balanced partition. Therefore the same capacity gates were evaluated over `1000` label-blind random partitions for each scheme, with identical fold sizes.

## Summary

| scheme | random_partitions | current_min_test_class | random_min_test_class_p05 | random_min_test_class_median | random_min_test_class_p95 | current_min_test_class_percentile | random_strong_pass_rate | random_minimal_pass_rate | robustness_verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| idare_4x4 | 1000 | 37 | 9.95 | 22.0 | 30.0 | 1.0 | 0.95 | 0.988 | ROBUST_MINIMAL |
| idare_5x5 | 1000 | 20 | 2.0 | 10.0 | 16.0 | 0.998 | 0.568 | 0.856 | PARTITION_SENSITIVE |

## Balance Extremeness

- `idare_4x4`: Current split is more label-balanced than over 99% of label-blind random partitions.
- `idare_5x5`: Current split is more label-balanced than over 99% of label-blind random partitions.

## Decision

- Recommendation: **DO_NOT_LOCK_STRICT_JOINT_SCHEME**
- Reason: Neither candidate demonstrates strong partition-robust capacity.

## Interpretation Boundary

- This audit addresses partition-capacity robustness only.
- It does not establish model performance.
- It does not replace shortcut baselines, permutation/null tests, donor-support audits, or TTA stream audits.
- If a label-balanced benchmark split is retained, it must be frozen before training and its construction must be reported transparently.
