# I-DARE Label-Blind Repeated 4x4 Protocol Decision

No model training was performed.

## Why 5x5 Was Not Selected

The 5x5 scheme was partition-sensitive under label-blind randomization. Its earlier balanced split was more balanced than over 99% of random partitions and therefore is not suitable as the sole headline benchmark.

## Frozen Construction Rule

- Manifest SHA-256: `72cbefb8a437959abd7a4892070ac468a27dff4c04e05ef8b56344ecbebb3a4b`
- Repetitions: `5`
- Repetition 0: primary benchmark
- Repetitions 1–4: sensitivity analysis
- Subject folds: `4`
- Stimulus folds: `4`
- Outer cells per repetition: `16`
- All subject-fold × stimulus-fold combinations are evaluated
- Partition construction uses no labels
- Seeds are derived deterministically from the manifest hash
- No rerolling or replacement of unfavorable repetitions

## Capacity Audit

| repetition | role | held_subjects | held_stimuli | min_test_class | min_train_class | min_test_retained | max_midpoint_removed_fraction | single_class_test_flags | single_class_train_flags | strong_pass | minimal_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | primary | 15..16 | 8..8 | 15 | 314 | 91 | 0.273438 | 0 | 0 | True | True |
| 1 | sensitivity | 15..16 | 8..8 | 24 | 289 | 84 | 0.34375 | 0 | 0 | True | True |
| 2 | sensitivity | 15..16 | 8..8 | 17 | 288 | 82 | 0.316667 | 0 | 0 | True | True |
| 3 | sensitivity | 15..16 | 8..8 | 19 | 307 | 87 | 0.320312 | 0 | 0 | True | True |
| 4 | sensitivity | 15..16 | 8..8 | 6 | 337 | 97 | 0.242188 | 0 | 0 | False | True |

## Decision

- Decision: **LOCK_LABEL_BLIND_4X4_PROTOCOL**
- Reason: The pre-registered primary repetition passes the strong capacity gate, and every pre-registered sensitivity repetition passes the minimum capacity gate.
- All repetitions pass minimum capacity: `True`
- All repetitions pass strong capacity: `False`
- Sensitivity strong-pass rate: `0.7500`

## Status of Earlier Candidate Splits

- Label-balanced 5x5: rejected as primary due partition sensitivity.
- Label-balanced 4x4: retained only as a diagnostic capacity-upper-bound split; it is not the headline benchmark.

## Next Audit Before Model Training

Run leakage-safe shortcut baselines and null/permutation analyses on the frozen primary and sensitivity partitions. Do not tune architectures on sensitivity repetitions.
