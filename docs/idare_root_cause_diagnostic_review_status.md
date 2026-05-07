# I-DARE Root-Cause Diagnostic Review Status

## Status

Frozen human-review closeout.

The read-only root-cause diagnostic report has been reviewed and accepted.

Reviewed report: `docs/idare_root_cause_diagnostic_report.md`

Reviewed JSON: `docs/idare_root_cause_diagnostic_report.json`

## Review Decision

The report is accepted.

Selected next objective:

`diagnostic_sanity_tests_objective`

Reason:

The read-only report strongly suggests subject/fold generalization difficulty and representation weakness, but it cannot rule out a model/pipeline learning issue.

Therefore, before proposing any fix, we need diagnostic-only sanity tests.

## Accepted Findings

- The current evidence does not support another blind training sweep.
- Subject/fold generalization is the highest-ranked likely issue.
- Representation weakness is also highly plausible.
- Model/pipeline learning failure cannot be ruled out from read-only outputs.
- Calibration/threshold issues exist but do not explain everything alone.
- Label/task definition sensitivity exists but does not explain everything alone.

## Next Allowed Step

Create and run a controlled diagnostic-sanity-tests objective.

These tests are allowed only as diagnosis, not as performance training.

## Intentionally Not Started

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- architecture ablation
- data augmentation
- SupCon / VREx / domain generalization
- mainline change
