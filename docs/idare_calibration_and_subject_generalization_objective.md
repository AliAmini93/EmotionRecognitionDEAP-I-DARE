# I-DARE Calibration and Subject-Generalization Objective

## Status

Short-term objective created.

This is diagnostic/analysis-first.

No new performance training is authorized.

## Why This Objective Exists

The diagnostic sanity tests were reviewed.

Main findings:

- Micro-overfit passed for EEG and EMG.
- Shuffled-label negative control passed.
- Total pipeline/model/data-feeding failure is weakened.
- Major leakage/split/metric failure is not supported by this diagnostic.
- Results remain weak/mixed.
- The next useful target is calibration and subject/fold generalization.

## Scientific Questions

1. Are the models producing useful ranking/probability information that is hidden by a fixed 0.5 threshold?
2. Do fold-specific thresholds or calibration improve macro-F1/balanced accuracy enough to justify a calibration protocol?
3. Are a small number of subjects/folds systematically driving failure across modalities and tasks?
4. Are EEG and EMG failing on the same subjects/tasks?
5. Can subject/fold grouping reveal trainable strata without starting fusion or architecture changes?

## Authorized Analyses

### 1. Threshold sweep by modality/task/policy

Purpose:

Quantify whether fixed-threshold inference hides useful signal.

Outputs:

- best threshold
- macro-F1 gain
- balanced-accuracy gain
- one-class threshold risk

### 2. Fold-specific calibration diagnostic

Purpose:

Measure threshold instability across folds.

Outputs:

- fold-wise best thresholds
- threshold variance
- fold-wise gain distribution
- calibration instability flag

### 3. Subject difficulty ranking

Purpose:

Rank subjects by repeated failure across existing outputs.

Outputs:

- subject failure count
- mean correctness
- task/modality failure overlap
- hard-subject shortlist

### 4. Cross-modality error overlap

Purpose:

Check whether EEG and EMG fail on the same subjects/tasks.

Outputs:

- overlap rates
- subject-level common-failure score
- modality-specific vs subject-level failure flag

### 5. Recipe/policy stability map

Purpose:

Identify whether any recipe or label policy is consistently less fragile.

Outputs:

- ranking by macro-F1
- ranking by balanced accuracy
- ranking by threshold gain
- stability flag

## Expected Outputs

- `docs/idare_calibration_subject_generalization_report.md`
- `docs/idare_calibration_subject_generalization_report.json`
- `docs/idare_calibration_subject_threshold_summary.csv`
- `docs/idare_subject_difficulty_ranking.csv`
- `docs/idare_cross_modality_error_overlap.csv`

## Pass Criteria

This objective passes only if the report:

- is generated from existing outputs only
- runs no new performance training
- separates threshold/calibration failure from subject/fold generalization difficulty
- identifies whether hard subjects/folds are stable across modalities/tasks
- recommends exactly one next objective after review
- does not authorize fusion, architecture, augmentation, DG, or final claims

## Stop Conditions

- If threshold gains are large but unstable across folds: recommend calibration protocol objective, not architecture work.
- If hard subjects dominate failure across modalities/tasks: recommend subject-generalization or subject-stratified diagnostic objective.
- If neither calibration nor subject effects explain the weakness: recommend representation/label-task redesign objective.
- If evidence suggests a data/split inconsistency: recommend data-integrity audit objective.

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

Prepare a reviewed read-only analysis command/script for calibration and subject-generalization diagnostics.
