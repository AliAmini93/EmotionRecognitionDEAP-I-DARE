# DEAP Strict Joint-CV Label-Blind Partition Capacity

No model training was performed. Every reference partition was constructed without labels.

| scheme | random_partitions | outer_cells | held_subjects | held_stimuli | min_test_class_random_min | min_test_class_p05 | min_test_class_median | min_test_class_p95 | strong_pass_rate | minimal_pass_rate | single_class_test_partition_rate | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| deap_4x4 | 1000 | 16 | 8..8 | 10..10 | 8 | 14.0 | 20.0 | 25.0 | 0.997 | 1.0 | 0.0 | ROBUST_STRONG |
| deap_5x5 | 1000 | 25 | 6..7 | 8..8 | 2 | 6.0 | 10.0 | 13.0 | 0.644 | 0.985 | 0.0 | ROBUST_MINIMAL |

## Decision

- Recommended pre-freeze scheme: **deap_4x4**
- This is not yet a frozen benchmark.
- The next step is deterministic repeated label-blind freezing of the defensible scheme, without rerolling after support review.
