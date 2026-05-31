# I-DARE Data Augmentation Track Branch Objective

## Status

`created`

## Objective ID

`idare_data_augmentation_objective`

## Branch

`idare/postwave1/data-augmentation-track`

## Scope

Branch-level objective and guarded runner creation only.

Authorized now:
- create objective docs
- create guarded runner
- run validation/status only

Not authorized:
- no DA execution
- no experiments
- no model results
- no DEAP
- no fusion
- no DG
- no SupCon
- no model-capacity probe
- no augmentation plus broad model search
- no preprocessing changes
- no threshold changes
- no main push

## Stage 1 Scope

- Dataset: I-DARE only
- Setting: cross-subject / held-out-subject
- Targets: valence and arousal
- Modalities: EEG and EMG separately
- Fusion: blocked
- DEAP: blocked

## Planned Matrix Metadata

Option A, preferred if later approved:

`2 targets x 2 modalities x 5 DA policies x 6 folds = 120 runs`

Option B, runtime fallback if later approved:

`2 targets x 1 modality x 5 DA policies x 6 folds = 60 EEG-first runs`

Neither option is authorized to run yet.

## DA Policies

EEG:
- E0 none baseline
- E1 additive Gaussian noise weak
- E2 additive Gaussian noise medium
- E3 amplitude scaling
- E4 time/channel masking or dropout

EMG:
- M0 none baseline
- M1 feature Gaussian jitter weak
- M2 feature Gaussian jitter medium
- M3 feature scaling
- M4 feature dropout

## Leakage Rules

- augmentation only on training subjects/folds
- never augment held-out/test subjects
- no augmentation-derived statistics from held-out/test subjects
- no test labels
- no target-subject adaptation
- no threshold tuning on held-out folds
- DA parameters fixed before seeing fold results or selected only inside train folds
- no preprocessing changes disguised as augmentation

## Current Boundary

`VALIDATION_ONLY`

## Next Required Control Decision

`AUTHORIZE_DATA_AUGMENTATION_OBJECTIVE_RUNNER_COMMIT_PUSH`
