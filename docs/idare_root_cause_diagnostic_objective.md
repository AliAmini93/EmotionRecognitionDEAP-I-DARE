# I-DARE Root-Cause Diagnostic Objective

## Status

Short-term objective created.

No new performance training is authorized by this document.

## Why this objective exists

Recent I-DARE EEG/EMG experiments did not produce a clear performance improvement.

The controlled failure analysis shows that the project should stop blind ablations and diagnose the root cause first.

## Scientific Question

Why do current I-DARE EEG/EMG models remain near chance/majority or unstable across folds?

The diagnosis must rank the most likely cause:

1. label/task definition issue
2. subject/fold generalization issue
3. calibration/threshold issue
4. representation weakness
5. model/pipeline learning issue

## Authorized Scope

### Phase 1: read-only root-cause report

Authorized now.

Use only existing committed outputs:

- label-policy ablation prediction CSVs and JSON reports
- broader single-modality prediction CSVs and JSON reports
- failure-analysis report and fold summary

Expected outputs:

- `docs/idare_root_cause_diagnostic_report.md`
- `docs/idare_root_cause_diagnostic_report.json`
- `docs/idare_root_cause_subject_summary.csv`
- `docs/idare_root_cause_calibration_summary.csv`
- `docs/idare_root_cause_error_overlap_summary.csv`

### Phase 2: diagnostic-only sanity tests

Not authorized yet.

These may be proposed only after the read-only report is reviewed:

- micro-overfit subset test
- shuffled-label negative control
- within-subject vs subject-held-out contrast
- simple classical baseline on existing features

## Required Analyses

### Subject and fold difficulty

- per-subject macro F1
- per-subject balanced accuracy
- per-fold macro F1
- per-fold balanced accuracy
- repeated weak subjects/folds
- overlap across EEG and EMG
- overlap across valence and arousal

### Label and class-balance sensitivity

- class balance by subject/fold/task/policy
- label-policy sensitivity by subject
- label-policy sensitivity by fold
- whether `discard_midpoint`, `midpoint_as_low`, or `midpoint_as_high` creates unstable subjects

### Calibration and threshold behavior

- probability mean/median/quantiles
- Brier score
- expected calibration error
- threshold sensitivity
- prediction skew
- whether ranking is better than default threshold classification

### Representation and modality behavior

- EEG STIM-BSL-only vs EEG BSL-stats
- EMG feature-only vs EMG BSL-stats
- whether EEG and EMG fail on the same subjects
- whether one modality is complementary or just equally weak

### Model/pipeline suspicion flags

The read-only report should flag whether later diagnostic sanity tests are needed.

Possible flags:

- model cannot separate even easy folds
- probability distributions collapse
- repeated one-sided prediction skew
- no representation/label-policy setting consistently beats majority
- suspiciously strong/weak behavior that suggests leakage or data feeding issues

## Pass Criteria

The objective passes only if the generated report:

- reconstructs per-subject and per-fold diagnostics from existing predictions
- computes calibration/threshold diagnostics where probabilities are available
- identifies repeated weak subjects/folds and overlap patterns
- ranks likely root causes with evidence and confidence
- recommends exactly one next objective
- does not run new performance training
- does not start fusion or architecture work

## Not Authorized

- new training for performance improvement
- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation
- data augmentation
- SupCon / VREx / domain generalization
- diagnostic sanity tests before read-only root-cause report review

## Next Allowed Step

Prepare a read-only root-cause diagnostic script/command.

That command should consume existing committed outputs and write the root-cause diagnostic report files.
