# I-DARE Diagnostic Sanity Tests Review Status

## Status

Frozen human-review closeout.

The diagnostic sanity tests report has been reviewed and accepted.

Reviewed report: `docs/idare_diagnostic_sanity_tests_report.md`

Reviewed JSON: `docs/idare_diagnostic_sanity_tests_report.json`

## Review Decision

The report is accepted.

Selected next objective:

`calibration_and_subject_generalization_objective`

## Accepted Findings

- Micro-overfit passed for EEG and EMG.
- Shuffled-label negative control passed.
- A total pipeline/model/data-feeding failure is weakened.
- Major leakage/split/metric failure is not supported by this diagnostic.
- Within-subject vs subject-heldout evidence is mixed.
- Simple classical baselines are mostly near chance, except weak EEG arousal signal.
- The next step should focus on calibration and subject/fold generalization diagnostics.

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

Create a calibration and subject-generalization objective.

This objective must remain diagnostic/analysis-first and must not start fusion or architecture escalation.
