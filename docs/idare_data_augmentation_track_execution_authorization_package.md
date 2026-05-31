# I-DARE Data Augmentation Track Execution Authorization Package

## Status

`created`

## Package ID

`idare_data_augmentation_track_execution_authorization_package`

## Execution Authorization

`NOT_AUTHORIZED`

Execution/setup requires explicit human approval phrase:

`APPROVE_DATA_AUGMENTATION_TRACK_EXECUTION`

Important: this approval, if later issued, authorizes branch/worktree setup and preflight only. Runner creation and DA execution require separate Control approvals.

## Scope

Control Tower documentation/authorization package only.

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
- no augmentation plus broad model search
- no model-capacity probe
- no main push

## Future Branch

`idare/postwave1/data-augmentation-track`

## Future Worktree

`/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-data-augmentation`

## Future Allowed File Prefix

`idare_data_augmentation_`

## Process Rule

Use one active working chat/branch for this track.

No parallel branch chats.

When the chat becomes exhausted, continue from GitHub documentation plus exported chat-context PDFs/notes.

## Stage 1 Scope

Stage 1 is I-DARE only.

Allowed future target if later approved:

- dataset: I-DARE
- setting: cross-subject / held-out-subject
- targets: valence and arousal
- modalities: EEG and EMG separately
- no fusion
- no DEAP
- no preprocessing changes
- no threshold tuning
- no DG
- no SupCon
- no model-capacity probe
- no augmentation plus model search

## Stage 1 DA Candidates

### EEG

| Policy | Description |
|---|---|
| E0_none_baseline | no augmentation |
| E1_additive_gaussian_noise_weak | weak training-only Gaussian noise |
| E2_additive_gaussian_noise_medium | medium training-only Gaussian noise |
| E3_amplitude_scaling | training-only amplitude scaling |
| E4_time_channel_masking_or_dropout | training-only time/channel masking/dropout |

### EMG

| Policy | Description |
|---|---|
| M0_none_baseline | no augmentation |
| M1_feature_gaussian_jitter_weak | weak training-only feature jitter |
| M2_feature_gaussian_jitter_medium | medium training-only feature jitter |
| M3_feature_scaling | training-only feature scaling |
| M4_feature_dropout | training-only feature dropout |

## Future Smoke Matrix

Preferred matrix, if feasible:

`2 targets x 2 modalities x 5 DA policies x 6 folds = 120 runs`

Runtime fallback:

`2 targets x 1 modality x 5 DA policies x 6 folds = 60 EEG-first runs`

Control must choose Option A or Option B before DA execution.

## Leakage Rules

Any future DA runner must enforce:

- augmentation only on training subjects/folds
- never augment held-out/test subjects
- no augmentation-derived statistics from held-out/test subjects
- no test labels
- no target-subject adaptation
- no threshold tuning on held-out folds
- DA parameters fixed before fold results, or selected only inside train folds
- no global all-subject augmentation fitting
- no preprocessing changes disguised as augmentation

## Future Runner Requirements

If runner creation is later authorized, runner must:

- support modes: `status`, `validate`, `run`, `closeout`
- default to `status` or `validate`, never `run`
- print explicit `BLOCKER` messages
- validate branch/worktree
- validate `.cache` and `.venv`
- validate I-DARE EEG and EMG inputs
- validate prior Control docs
- validate planned run matrix
- validate allowed output prefix
- refuse to run if execution is not explicitly authorized
- refuse any DEAP/fusion/DG/SupCon/model-capacity/preprocessing/threshold scope

## Required Future Outputs

If DA execution is later approved, outputs must include:

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

DA is useful only if improvement is consistent enough across folds, not just one fold spike.

If EEG improves:
- plan EEG confirmation only after artifact review.

If EMG improves:
- plan EMG confirmation only after artifact review.

If either modality confirms:
- consider DEAP equivalent only after Control review.

Fusion remains blocked until at least one EEG/EMG DA configuration is confirmed.

## Stop / Blocker Rules

Stop and notify Control Tower if:

- required I-DARE EEG/EMG cache/index files are missing
- branch/worktree is wrong
- outputs escape `idare_data_augmentation_`
- runner attempts DEAP in stage 1
- runner attempts fusion
- runner attempts preprocessing or threshold changes
- runner attempts DG/SupCon/model-capacity/model search
- run matrix differs from approved Option A or Option B
- main push is requested

## Current Ruling

This package does not authorize execution, branch creation, worktree creation, runner creation, or DA run.

## Next State

`AWAITING_APPROVE_DATA_AUGMENTATION_TRACK_EXECUTION`
