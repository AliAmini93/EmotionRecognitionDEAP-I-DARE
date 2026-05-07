# I-DARE Calibration and Subject-Generalization Review Status

## Status

Frozen human-review closeout.

The calibration and subject-generalization report has been reviewed and accepted.

Reviewed report: `docs/idare_calibration_subject_generalization_report.md`

Reviewed JSON: `docs/idare_calibration_subject_generalization_report.json`

## Review Decision

The report is accepted.

Selected next objective:

`calibration_protocol_objective`

## Accepted Findings

- Calibration instability is supported.
- Threshold sweeps show repeated macro-F1 gains.
- Best thresholds vary substantially across folds and conditions.
- Hard-subject and cross-modality effects exist.
- The immediate next step is a calibration protocol objective.
- No new performance-training claim is authorized.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- new performance training
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Next Allowed Step

Create a calibration protocol objective.

The objective must define a validation-only calibration plan and must not start fusion, broad architecture work, or final claims.
