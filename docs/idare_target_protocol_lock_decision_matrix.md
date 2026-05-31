# I-DARE Target/Protocol Lock Decision Matrix

## Status

`created`

## Policy Lock Matrix

| Code | Decision area | Ruling | Execution implication |
|---|---|---|---|
| P0 | current held-out binary arousal | comparator only | use as reference, not final target |
| P1 | label/task redesign | primary | define final label/task policy before new runs |
| P2 | protocol target reconciliation | primary | define final evaluation target before new runs |
| P3 | subject-relative / within-subject | scoped diagnostic candidate | not auto-mainline |
| P4 | stop/pivot | fallback only | not selected now |

## Prior Coverage Matrix

| Dataset | Modality | Task | Prior coverage | Reuse decision |
|---|---|---|---|---|
| I-DARE | EEG | arousal | label-policy matrix + broader single-modality evidence | reuse; confirmation candidate |
| I-DARE | EEG | valence | label-policy matrix + broader single-modality evidence | reuse |
| I-DARE | EMG | arousal | label-policy matrix + broader single-modality evidence | reuse; confirmation candidate |
| I-DARE | EMG | valence | label-policy matrix + broader single-modality evidence | reuse |
| I-DARE | EEG+EMG fusion | valence/arousal | not ready / frozen | missing; do not execute now |
| DEAP | EEG/EMG | valence/arousal | frozen / not in current active branch | missing; do not execute now |
| DEAP | EEG+EMG fusion | valence/arousal | frozen | missing; do not execute now |

## Minimal Next-Run Recommendation

No run is authorized.

If a future run is requested after target/protocol lock, Control should prefer:

1. confirmation of prior best I-DARE cells,
2. then missing DEAP equivalent only if DEAP is unfrozen by explicit review,
3. then fusion readiness only after single-modality readiness,
4. not a duplicate 144-run label-policy rerun.

## Current Decision

`NO_NEW_EXECUTION_UNTIL_TARGET_PROTOCOL_LOCK_REVIEW_ACCEPTED`
