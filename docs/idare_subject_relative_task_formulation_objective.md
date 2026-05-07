# I-DARE Subject-relative Task Formulation Objective

## Status

Short-term objective created.

This is a diagnostic/design objective.

No new model training is authorized.

## Why This Objective Exists

The representation/label-task diagnostic report was reviewed.

Accepted findings:

- The leading blocker is label/task subject dependence.
- Global binary labels are likely unstable under subject-heldout evaluation.
- Subject-relative task formulation should be tested before architecture, fusion, augmentation, or domain generalization.

## Scientific Questions

1. Can subject-relative labels reduce between-subject label skew while preserving within-subject affective ordering?
2. Which subject-relative formulation is least leaky and most compatible with subject-heldout evaluation?
3. Can a future small controlled training run use only train-subject statistics to define or calibrate task labels without touching heldout subjects?
4. What exact run matrix should be used next if this formulation passes design review?

## Authorized Work

### 1. Subject-relative label design

Purpose:

Define candidate subject-relative labels using only within-subject rating structure.

Candidate formulations:

- `subject_median_split`
- `subject_zscore_sign`
- `subject_top_bottom_quantile`
- `within_subject_pairwise_or_ranking_task`

### 2. Leakage audit

Purpose:

Specify which statistics are computed per subject and which are allowed at train/test time.

Must answer:

- Does the formulation require heldout-subject label distribution knowledge?
- Can it be applied using only the heldout subject's own trial ratings without using predictions?
- Is the formulation compatible with the project's scientific question?

### 3. Class-balance and coverage audit

Purpose:

Compute expected sample retention, per-fold balance, and subject coverage for each candidate formulation.

### 4. Future controlled run-matrix design

Purpose:

Prepare but do not execute the next minimal controlled training matrix if one formulation is selected.

## Expected Outputs

- `docs/idare_subject_relative_task_formulation_report.md`
- `docs/idare_subject_relative_task_formulation_report.json`
- `docs/idare_subject_relative_label_balance_summary.csv`
- `docs/idare_subject_relative_candidate_matrix.csv`

## Pass Criteria

This objective passes only if:

- no new model training is run
- no fusion, architecture improvement, augmentation, DG, or final LOSO claim is authorized
- at least three subject-relative candidate formulations are audited
- the report states leakage risks and whether each formulation is scientifically valid
- the report recommends exactly one next objective after human review
- if a future training objective is recommended, it must be small, controlled, and explicitly separated from this planning objective

## Candidate Next Objectives After Review

- `minimal_subject_relative_training_objective`
- `subject_relative_label_quality_audit_objective`
- `representation_preprocessing_redesign_objective`
- `data_quality_or_label_noise_audit_objective`
- `stop_or_handoff_objective`

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

Prepare a reviewed read-only subject-relative task formulation report command/script.
