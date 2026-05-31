# I-DARE Prior Best Cell Confirmation Authorization Package

## Status

`created`

## Package ID

`idare_prior_best_cell_confirmation_authorization_package`

## Execution Authorization

`NOT_AUTHORIZED`

Execution requires explicit human approval phrase:

`APPROVE_IDARE_PRIOR_BEST_CELL_CONFIRMATION_EXECUTION`

## Scope

Control Tower documentation/authorization package only.

Forbidden:
- no execution
- no runner creation
- no branch creation
- no worktree creation
- no new audit
- no experiments
- no model results
- no Wave 2 execution
- no DG execution
- no model-capacity probe
- no augmentation
- no representation redesign v2
- no DEAP execution
- no fusion execution
- no preprocessing changes
- no threshold changes
- no main push

## Future Executable Branch

`idare/postwave1/idare-prior-best-cell-confirmation`

## Future Worktree

`/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-idare-prior-best-confirm`

## Future Allowed File Prefix

`idare_prior_best_confirm_`

## Rationale

The prior I-DARE label-policy ablation already covered:

- 2 tasks: valence and arousal
- 2 modalities: EEG and EMG
- 3 label policies
- 2 recipes
- 6 folds
- 144 total runs

Therefore, the full 144-run matrix should be reused as controlled prior evidence and must not be rerun by default.

This package defines only a possible future confirmation of the prior best I-DARE cells.

## Future Confirmation Matrix

If later approved, the exact future confirmation matrix is:

| Cell | Dataset | Modality | Task | Label policy | Recipe | Prior mean BA | Role |
|---|---|---|---|---|---|---:|---|
| C0 | I-DARE | EEG | arousal | midpoint_as_high | ce_class_weighted | 0.5416327026 | prior best moderate cell |
| C1 | I-DARE | EEG | valence | discard_midpoint | balanced_sampler_ce | 0.5218687144 | prior best weaker cell |
| C2 | I-DARE | EMG | arousal | discard_midpoint | ce_class_weighted | 0.5364967332 | prior best moderate cell |
| C3 | I-DARE | EMG | valence | midpoint_as_high | ce_class_weighted | 0.5201507594 | prior best weaker cell |

Future run count, if later approved:

`4 cells x 6 folds = 24 confirmation runs`

## Future Evaluation Target

Future confirmation must remain:

- I-DARE only
- EEG and EMG separately
- valence and arousal
- cross-subject / held-out-subject
- prior best label-policy cells only
- no fusion
- no DEAP
- no threshold changes
- no new label-policy search

## Required Future Outputs

If execution is later approved, the future branch must produce:

- objective doc/json
- guarded runner/script
- validation report
- confirmation runs CSV
- metric summary
- fold-level report
- prior-vs-confirmation comparison report
- leakage/scope audit
- closeout report/json
- artifact review bundle

## Required Confirmation Questions

The closeout must answer:

1. Do prior best I-DARE cells reproduce under the current locked protocol?
2. Do EEG arousal and EMG arousal remain moderate-pass candidates?
3. Do valence cells remain weak and comparator-only?
4. Is there enough confirmed single-modality evidence to later consider DEAP equivalent review?
5. Is there enough confirmed single-modality evidence to later consider fusion readiness review?

## Stop / Blocker Rules

Stop and notify Control Tower if:

- required prior label-policy artifacts are missing
- required I-DARE cache/index files are missing
- future runner cannot reproduce the exact four registered cells
- scope expands beyond the 24-run confirmation matrix
- any DEAP or fusion work is requested
- any threshold change is requested
- output paths escape the allowed prefix
- main push is requested

## Current Ruling

This package does not authorize execution.

## Next State

`AWAITING_APPROVE_IDARE_PRIOR_BEST_CELL_CONFIRMATION_EXECUTION`
