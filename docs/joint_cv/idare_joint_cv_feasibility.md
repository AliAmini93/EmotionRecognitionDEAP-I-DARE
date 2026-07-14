# I-DARE Strict Joint Subject–Stimulus CV Feasibility

No model training was performed.

## Protocol

For every outer cell:

- Train = source subjects × source stimuli
- Primary test = held-out subjects × held-out stimuli
- Diagnostic A = source subjects × held-out stimuli
- Diagnostic B = held-out subjects × source stimuli

All subject-fold × stimulus-fold combinations are evaluated. Diagonal-only fold pairing is not used.

## Manifest

- Source manifest: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/docs/joint_cv/idare_trial_manifest.csv`
- Statistical unit: one physical trial
- Physical grid: 63 subjects × 32 stimuli = 2016 trials
- Repeated-session nesting: absent in the current manifest (one session per subject)

## Construction Method

Entity folds are constructed deterministically using label-support profiles and exact fold capacities, followed by deterministic pairwise-swap refinement. No EEG/EMG features, model outputs, predictions, or trained metrics are used.

## Scheme Summary

| scheme | outer_cells | held_subjects | held_stimuli | test_trials_before_policy | min_test_class | min_train_class | single_class_flags | leakage_free | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| idare_4x4 | 16 | 15..16 | 8..8 | 120..128 | 37 | 378 | 0 | True | PASS_STRONG_CAPACITY |
| idare_5x5 | 25 | 12..13 | 6..7 | 72..91 | 20 | 419 | 0 | True | PASS_STRONG_CAPACITY |

## Task and Label-Policy Support

| scheme | task | policy | min_test_class | min_train_class | single_class_test_cells | single_class_train_cells | test_retained | max_midpoint_removed_fraction | majority_accuracy_range | max_test_stimulus_label_nmi |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| idare_4x4 | valence | discard_midpoint | 41 | 447 | 0 | 0 | 97..111 | 0.210938 | 0.4775..0.5773 | 0.461268 |
| idare_4x4 | valence | midpoint_as_low | 50 | 471 | 0 | 0 | 120..128 | 0.0 | 0.5333..0.6094 | 0.400074 |
| idare_4x4 | valence | midpoint_as_high | 41 | 447 | 0 | 0 | 120..128 | 0.0 | 0.5469..0.6583 | 0.377366 |
| idare_4x4 | arousal | discard_midpoint | 37 | 378 | 0 | 0 | 105..117 | 0.15625 | 0.5810..0.6574 | 0.262883 |
| idare_4x4 | arousal | midpoint_as_low | 37 | 378 | 0 | 0 | 120..128 | 0.0 | 0.6250..0.7109 | 0.212199 |
| idare_4x4 | arousal | midpoint_as_high | 49 | 497 | 0 | 0 | 120..128 | 0.0 | 0.5078..0.5938 | 0.204024 |
| idare_5x5 | valence | discard_midpoint | 24 | 495 | 0 | 0 | 56..79 | 0.230769 | 0.4531..0.5714 | 0.530517 |
| idare_5x5 | valence | midpoint_as_low | 26 | 529 | 0 | 0 | 72..91 | 0.0 | 0.5139..0.6484 | 0.442213 |
| idare_5x5 | valence | midpoint_as_high | 24 | 495 | 0 | 0 | 72..91 | 0.0 | 0.5476..0.6667 | 0.456236 |
| idare_5x5 | arousal | discard_midpoint | 20 | 419 | 0 | 0 | 61..84 | 0.217949 | 0.5833..0.6721 | 0.464218 |
| idare_5x5 | arousal | midpoint_as_low | 20 | 419 | 0 | 0 | 72..91 | 0.0 | 0.6154..0.7436 | 0.418122 |
| idare_5x5 | arousal | midpoint_as_high | 30 | 557 | 0 | 0 | 72..91 | 0.0 | 0.5128..0.6154 | 0.37334 |

## Leakage and Modality Availability

- Subject leakage: zero if all scheme rows report leakage-free.
- Stimulus leakage: zero if all scheme rows report leakage-free.
- Maximum rows removed by EEG+EMG availability filtering in any cell-policy combination: `0`
- This is an availability-level check, not a signal-quality artifact rejection analysis.

## Effective Independent Support

An exact statistical effective sample size cannot be identified before a fitted model because two-way residual dependence and ICC are unknown. The audit therefore reports physical-trial count, independent held-out subject count, independent held-out stimulus count, and the conservative minimum-axis capacity proxy separately.

## Decision

`idare_5x5` is the leading candidate under the current pre-training support heuristic. This is not a model-selection result and must be locked before training.

- Recommended candidate: `idare_5x5`
- Fold assignments must be committed and frozen before any model training or hyperparameter comparison.
- Chance distributions, shortcut baselines, donor availability, and stream/TTA capacity remain separate next-stage audits.
