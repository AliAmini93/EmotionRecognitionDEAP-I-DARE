# I-DARE Minimal Subject-relative Training Objective

## Status

Short-term objective created.

This objective authorizes only a minimal controlled diagnostic training first pass.

It does not authorize a final LOSO claim, mainline change, fusion, architecture improvement, augmentation, or domain generalization.

## Why This Objective Exists

The subject-relative task formulation report was reviewed and accepted.

Selected formulation:

`subject_top_bottom_quantile_q33`

Reason:

- Global binary labels appear unstable under subject-heldout evaluation.
- Subject-relative top/bottom quantile labels are the selected controlled first fix candidate.
- A minimal training run is needed to test whether the task redesign improves subject-heldout macro-F1 / balanced accuracy before considering architecture, fusion, augmentation, or DG.

## Authorized Scope

### Training type

Minimal controlled diagnostic training only.

### Label formulation

`subject_top_bottom_quantile_q33`

Definition:

For each subject and task:

- bottom third of the subject's ratings -> class `0`
- top third of the subject's ratings -> class `1`
- middle third -> discarded

### Modalities

- EEG `STIM-BSL`-only
- EMG feature-only

### Tasks

- valence
- arousal

### Folds

- sidecar-compatible 6 folds
- seed `11`

### First-pass recipe

- `ce_class_weighted`

### First-pass matrix size

24 runs:

`2 modalities x 2 tasks x 6 folds x 1 recipe x seed 11`

### Optional second pass

`balanced_sampler_ce` may be run only after first-pass validation, if outputs are valid and the first pass is not obviously broken.

Optional second pass size:

24 additional runs.

## Implementation Requirements

- Create or patch scripts so subject-relative labels are generated deterministically from existing per-trial valence/arousal ratings.
- Fold splitting must remain sidecar-compatible: `numpy.default_rng(seed=11)`, 6 folds.
- No heldout-subject predictions may be used to define labels.
- Generated outputs must record retained sample counts per task/fold/modality.
- Run EEG and EMG mainlines only.
- Do not include BSL-stats sidecars in this first pass.

## Expected Outputs First Pass

- `docs/idare_subject_relative_minimal_eeg_primary.md`
- `docs/idare_subject_relative_minimal_eeg_primary.json`
- `docs/idare_subject_relative_minimal_eeg_primary_predictions.csv`
- `docs/idare_subject_relative_minimal_emg_primary.md`
- `docs/idare_subject_relative_minimal_emg_primary.json`
- `docs/idare_subject_relative_minimal_emg_primary_predictions.csv`
- `docs/idare_subject_relative_minimal_training_report.md`
- `docs/idare_subject_relative_minimal_training_report.json`

## Pass Criteria

This objective passes only if:

- first pass completes 24 planned diagnostic runs
- all first-pass JSON outputs validate
- all first-pass prediction CSV outputs are non-empty
- every run records subject-relative formulation and retained validation sample count
- no fusion, architecture/DG/augmentation, broad hyperparameter search, final LOSO claim, or mainline change is made
- a combined report compares subject-relative results against the previous global-label mainline baseline at diagnostic level
- the combined report recommends exactly one next objective after human review

## Candidate Next Objectives After Review

- `minimal_subject_relative_balanced_sampler_pass_objective`
- `subject_relative_representation_preprocessing_objective`
- `subject_relative_bsl_stats_sidecar_objective`
- `stop_or_handoff_objective`

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change
- BSL-stats sidecars in first pass

## Next Allowed Step

Prepare reviewed implementation/run command for the 24-run first-pass minimal subject-relative training matrix.
