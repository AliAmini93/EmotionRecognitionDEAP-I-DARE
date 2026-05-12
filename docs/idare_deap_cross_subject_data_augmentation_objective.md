# I-DARE / DEAP Cross-Subject Data Augmentation Objective

## Status

`created`

## Objective ID

`idare_deap_cross_subject_data_augmentation_objective`

## Process Rule

Use one active working chat/branch at a time.

When a chat becomes exhausted, continue using GitHub documentation plus exported chat-context PDFs/notes from the previous chat.

## Scope

Control Tower documentation/objective only.

This objective defines the next execution-oriented technical track, but does not authorize branch creation, runner creation, or execution.

Forbidden now:
- no execution
- no runner creation
- no branch creation
- no worktree creation
- no experiments
- no model results
- no DEAP execution in stage 1
- no EEG+EMG fusion
- no preprocessing changes
- no threshold tuning on held-out subjects
- no DG
- no SupCon
- no augmentation plus model search
- no model-capacity probe
- no main push

## Human Direction

The project is reset to a single active working chat/process.

The selected next technical direction is:

`DATA_AUGMENTATION`

Reason:

Prior small classical, normalization, representation, and prior-best confirmation diagnostics did not produce a robust operating point. Major intervention families such as data augmentation have not yet been systematically tested in this project. Prior related EEG work suggests training-only Additive Gaussian Noise can improve cross-subject EEG performance, but this project must adapt the idea carefully rather than copy it blindly.

## Long-Range Project Target

The original project target remains:

- datasets: I-DARE and DEAP
- modalities: EEG, EMG, and later EEG+EMG fusion
- setting: cross-subject / held-out-subject
- targets: valence and arousal
- goal: improve performance enough for a defensible paper-level result

## Stage 1 Target

Stage 1 is I-DARE only.

Allowed future stage-1 target, if later approved:

- dataset: I-DARE
- setting: cross-subject / held-out-subject
- targets: valence and arousal
- modalities: EEG and EMG separately
- fusion: blocked
- DEAP: blocked
- preprocessing changes: forbidden
- threshold tuning on held-out subjects: forbidden

## Requested Future Branch

`idare/postwave1/data-augmentation-track`

## Requested Future Worktree

`/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-data-augmentation`

## Requested Future Prefix

`idare_data_augmentation_`

## Stage 1 Data Augmentation Candidates

### EEG DA policies

| Policy | Meaning |
|---|---|
| E0_none_baseline | no augmentation |
| E1_additive_gaussian_noise_weak | weak training-only Gaussian noise |
| E2_additive_gaussian_noise_medium | medium training-only Gaussian noise |
| E3_amplitude_scaling | training-only amplitude scaling |
| E4_time_channel_masking_or_dropout | training-only time/channel masking or dropout |

### EMG DA policies

| Policy | Meaning |
|---|---|
| M0_none_baseline | no augmentation |
| M1_feature_gaussian_jitter_weak | weak training-only feature jitter |
| M2_feature_gaussian_jitter_medium | medium training-only feature jitter |
| M3_feature_scaling | training-only feature scaling |
| M4_feature_dropout | training-only feature dropout |

## Leakage Rules

Any future DA runner must enforce:

- augmentation only on training subjects/folds
- no augmentation-derived statistics from held-out/test subjects
- no test labels
- no target-subject adaptation
- no threshold tuning on held-out subjects
- all DA parameters fixed before seeing fold results, or selected only inside train folds
- no global all-subject augmentation fitting
- no preprocessing changes disguised as augmentation

## First Smoke Matrix

Preferred option, if feasible:

`2 targets x 2 modalities x 5 DA policies x 6 folds = 120 runs`

Runtime fallback option:

`2 targets x 1 modality x 5 DA policies x 6 folds = 60 runs`

Fallback starts with EEG-first only.

## Required Future Outputs

If execution is later approved, the DA branch must produce:

- objective doc/json
- guarded runner/script
- validation report
- run matrix CSV
- fold-level metrics
- metric summary by target x modality x DA policy
- leakage audit
- best DA policy per target/modality
- comparison against no-augmentation baseline
- one-class collapse count
- closeout report/json
- artifact review bundle

## Decision Criteria

Moderate pass:

`mean balanced accuracy >= 0.53 AND positive delta vs no-DA baseline`

Strong pass:

`mean balanced accuracy >= 0.55`

DA is useful only if improvement is consistent enough across folds, not only a one-fold spike.

If EEG improves:
- plan EEG confirmation.

If EMG improves:
- plan EMG confirmation.

If either modality confirms:
- consider DEAP equivalent only after Control review.

Fusion remains blocked until at least one EEG/EMG DA configuration is confirmed.

## Current Ruling

This objective does not authorize execution.

## Next State

`REQUEST_DATA_AUGMENTATION_TRACK_EXECUTION_AUTHORIZATION_PACKAGE`
