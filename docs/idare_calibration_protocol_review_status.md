# I-DARE Calibration Protocol Review Status

## Status

Frozen human-review closeout.

The validation-only calibration protocol report has been reviewed and accepted.

Reviewed report: `docs/idare_calibration_protocol_report.md`

Reviewed JSON: `docs/idare_calibration_protocol_report.json`

## Review Decision

The report is accepted.

Diagnosis:

`calibration_not_sufficient_as_primary_fix`

Selected next objective:

`representation_label_task_redesign_objective`

## Accepted Findings

- Validation-only calibration gains are too small or inconsistent.
- Calibration alone should not be treated as the main fix.
- The next step should inspect representation, labels, and task formulation before any model-change or fusion objective.
- No new performance-training claim is authorized.

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

Create a representation/label-task redesign objective.

The objective must stay diagnostic/planning-first and must not start broad model training or final claims.
