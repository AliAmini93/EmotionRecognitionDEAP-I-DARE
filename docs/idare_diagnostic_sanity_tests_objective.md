# I-DARE Diagnostic Sanity Tests Objective

## Status

Short-term objective created.

This is diagnostic-only.

No performance-training claim is authorized.

## Why this objective exists

The read-only root-cause diagnostic report was reviewed.

It showed that subject/fold generalization and representation weakness are likely, but a model/pipeline learning issue cannot be ruled out.

Before proposing fixes, we need sanity tests that answer a simpler question:

Can the current pipeline learn any usable signal under controlled conditions?

## Scientific Question

Can the current I-DARE EEG/EMG data/model pipeline learn signal at all?

Or are near-chance results caused by:

1. subject/fold generalization difficulty
2. representation weakness
3. label/task noise
4. calibration/threshold weakness
5. model/pipeline learning failure

## Authorized Tests

### 1. Micro-overfit subset test

Purpose:

Check whether each mainline model can memorize a small clean subset.

Interpretation:

- Pass: training/data feeding/model/loss can learn at least local signal.
- Fail: strong evidence for pipeline/model/loss/data-feeding issue.

Allowed scope:

- EEG `STIM-BSL`-only
- EMG feature-only
- valence and arousal
- `midpoint_as_high` continuity/default policy only
- small subset
- diagnostic-only

### 2. Shuffled-label negative control

Purpose:

Check for leakage or suspicious behavior under randomized labels.

Interpretation:

- Pass: performance stays near chance/majority.
- Fail: potential leakage, split bug, or metric/reporting bug.

### 3. Within-subject vs subject-heldout contrast

Purpose:

Separate learnability from cross-subject generalization difficulty.

Interpretation:

- within-subject good and subject-heldout bad: subject/domain generalization is the likely core issue.
- both bad: representation, label/task, or pipeline learning issue remains likely.

### 4. Simple classical baseline

Purpose:

Check whether simple models on existing features can beat the neural setup or reveal linearly available signal.

Interpretation:

- classical better than neural: neural setup/training may be weak.
- classical also near chance: representation/label/generalization issue is more likely.

## Expected Outputs

- `docs/idare_diagnostic_sanity_tests_report.md`
- `docs/idare_diagnostic_sanity_tests_report.json`
- `docs/idare_diagnostic_sanity_tests_summary.csv`
- optional `docs/idare_diagnostic_sanity_tests_predictions.csv` only if needed and not too large

## Pass Criteria

The objective passes only if the report:

- runs diagnostic sanity tests only
- gives pass/fail interpretation for each test
- states whether model/pipeline learning failure is supported, weakened, or unresolved
- distinguishes subject/domain generalization difficulty from total learnability failure
- recommends exactly one next objective after review
- does not start fusion, architecture, augmentation, DG, or final claim work

## Stop Conditions

- If micro-overfit fails: stop and recommend pipeline/data-feeding/loss audit.
- If shuffled-label control performs suspiciously above chance: stop and recommend leakage/split audit.
- If within-subject is strong but subject-heldout is weak: recommend subject-generalization objective.
- If all diagnostics remain near chance: recommend representation/label-task redesign objective.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Next Allowed Step

Prepare a reviewed command/script that runs these diagnostic sanity tests and writes the diagnostic report.
