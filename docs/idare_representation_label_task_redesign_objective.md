# I-DARE Representation and Label-task Redesign Objective

## Status

Short-term objective created.

This is a diagnostic/design objective.

No new model training is authorized.

## Why This Objective Exists

The validation-only calibration protocol report was reviewed.

Accepted finding:

- Calibration is not sufficient as the primary fix.
- Near-chance/mixed results remain after BSL-stats, label-policy, failure, sanity, and calibration diagnostics.
- Before changing architecture or starting fusion, the project needs a diagnostic redesign of representation, label construction, and task framing.

## Scientific Questions

1. Are the current binary labels too noisy, unstable, or subject-dependent for the current subject-heldout setup?
2. Is the current `STIM-BSL` representation preserving emotion-related signal or mostly subject/session nuisance structure?
3. Are arousal/valence being treated as single global binary tasks when subject-relative or trial-relative formulations would be more appropriate?
4. Which future fix should be tested first: label redesign, representation redesign, or subject-normalized task formulation?

## Authorized Work

### 1. Label-noise and label-policy diagnosis

Purpose:

Audit original rating distributions, midpoint density, class balance by subject/fold/task, and label-policy disagreement.

Outputs:

- per-subject/task label balance
- midpoint/near-midpoint burden
- policy disagreement map
- candidate label policies for future controlled test

### 2. Subject-dependency diagnosis

Purpose:

Quantify whether errors and labels are dominated by subject identity, fold composition, or subject-specific baselines.

Outputs:

- hard-subject clusters
- subject-label skew table
- subject-vs-task confounding indicators

### 3. Representation-signal diagnosis

Purpose:

Test whether current EEG/EMG representations separate labels beyond subject/session nuisance using read-only feature summaries.

Outputs:

- representation separability checks
- subject separability vs label separability
- feature/representation redesign recommendations

### 4. Task-redesign options

Purpose:

Define a small set of future controlled objectives without running them yet.

Outputs:

- recommended task formulation
- candidate future objective list
- one selected next objective after review

## Expected Outputs

- `docs/idare_representation_label_task_redesign_report.md`
- `docs/idare_representation_label_task_redesign_report.json`
- `docs/idare_label_noise_subject_balance_summary.csv`
- `docs/idare_representation_signal_diagnostic_summary.csv`

## Pass Criteria

This objective passes only if:

- no new model training is run
- no fusion, architecture improvement, augmentation, DG, or final LOSO claim is authorized
- the report identifies whether the leading blocker is label/task design, representation design, subject generalization, or unresolved/mixed
- the report recommends exactly one next objective after human review
- the report states which tempting next steps are still not authorized

## Candidate Next Objectives After Review

- `subject_normalized_labeling_objective`
- `subject_relative_task_formulation_objective`
- `representation_preprocessing_redesign_objective`
- `minimal_controlled_training_objective`
- `data_quality_or_label_noise_audit_objective`

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- new model training
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Next Allowed Step

Prepare a reviewed read-only representation/label-task diagnostic report command/script.
