# DEAP Label-Blind Repeated 4x4 Protocol Decision

No model training was performed.

## Frozen Construction Rule

- Manifest SHA-256: `c40aa73e17098e17c95c79417176308e2459e1f709fe0f8583b48cfcd659a478`
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
| 0 | primary | 8..8 | 10..10 | 20 | 267 | 75 | 0.0625 | 0 | 0 | True | True |
| 1 | sensitivity | 8..8 | 10..10 | 21 | 271 | 77 | 0.0375 | 0 | 0 | True | True |
| 2 | sensitivity | 8..8 | 10..10 | 19 | 247 | 77 | 0.0375 | 0 | 0 | True | True |
| 3 | sensitivity | 8..8 | 10..10 | 20 | 252 | 77 | 0.0375 | 0 | 0 | True | True |
| 4 | sensitivity | 8..8 | 10..10 | 19 | 268 | 77 | 0.0375 | 0 | 0 | True | True |

## Decision

- Decision: **LOCK_LABEL_BLIND_4X4_PROTOCOL**
- Reason: The pre-registered primary repetition passes the strong capacity gate, and every pre-registered sensitivity repetition passes the minimum capacity gate.
- All repetitions pass minimum capacity: `True`
- All repetitions pass strong capacity: `True`
- Sensitivity strong-pass rate: `1.0000`

## Status of 5x5

- The 5x5 scheme remains non-primary because its strong-pass rate was only 0.644 under label-blind random partitions.
- Do not substitute or reroll the 4x4 repetitions after seeing their support.

## Next Audit Before Model Training

Run leakage-safe shortcut baselines, presentation-order confounding analysis, and null/permutation tests on the frozen DEAP partitions.
