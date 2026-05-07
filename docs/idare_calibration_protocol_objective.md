# I-DARE Calibration Protocol Objective

## Status

Short-term objective created.

This is a validation-only calibration protocol objective.

No new model training is authorized.

## Why This Objective Exists

The calibration and subject-generalization report was reviewed.

Accepted finding:

- Calibration instability is supported.
- Threshold sweeps show repeated macro-F1 gains.
- Best thresholds vary substantially across folds and conditions.
- A calibration protocol must be defined before any model-change objective.

## Scientific Questions

1. Can a validation-only calibration rule improve macro-F1/balanced accuracy without using test labels?
2. Is a global threshold per modality/task enough, or are fold/task/policy-specific thresholds required?
3. Do calibrated predictions reduce one-class/collapse risk without inflating performance through leakage?
4. Can calibration be defined in a reproducible way suitable for future LOSO-style evaluation?

## Authorized Work

### 1. Define validation-only threshold protocol

Purpose:

Define how thresholds are learned only from train/validation folds and applied to held-out fold predictions.

This must prevent:

- choosing threshold directly on the held-out/test fold
- using test labels for calibration
- reporting oracle-threshold results as performance

### 2. Simulate non-oracle calibration from existing folds

Purpose:

Use existing fold predictions to approximate leave-one-fold-out threshold selection.

Outputs:

- per-modality/task/policy/recipe calibrated metrics
- oracle-vs-non-oracle calibration gap
- collapse/one-class risk

### 3. Compare global vs fold-transfer thresholds

Purpose:

Check if one global threshold transfers better than fold-specific thresholds.

Outputs:

- global threshold stability
- fold-transfer threshold stability
- recommended protocol granularity

### 4. Calibration protocol pass/fail report

Purpose:

Decide whether calibration is worth becoming part of the next controlled evaluation.

Outputs:

- pass/fail decision
- recommended next objective
- explicit non-authorization list

## Expected Outputs

- `docs/idare_calibration_protocol_report.md`
- `docs/idare_calibration_protocol_report.json`
- `docs/idare_calibration_protocol_summary.csv`

## Pass Criteria

This objective passes only if:

- no new model training is run
- no held-out/test labels are used to choose thresholds for the same held-out/test predictions
- oracle threshold gains are clearly separated from validation-only simulated gains
- the report states whether calibration is strong enough to justify a controlled calibration evaluation
- the report recommends exactly one next objective after review
- the report does not authorize fusion, architecture, augmentation, DG, or final claims

## Stop Conditions

- If validation-only calibration gains are materially smaller than oracle gains, recommend against calibration as a fix.
- If validation-only calibration gives stable gains without collapse, recommend a controlled calibration evaluation objective.
- If calibration gains are unstable or subject-specific, recommend subject-stratified/generalization objective.
- If neither calibration nor subject grouping helps, recommend representation/label-task redesign objective.

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

Prepare a reviewed read-only calibration protocol analysis command/script.
