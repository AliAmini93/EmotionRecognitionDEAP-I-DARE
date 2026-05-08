# I-DARE Subject-variability Intervention-failure Analysis Objective

## Status

Short-term objective created.

No new performance training is authorized by this document.

Generated UTC: `2026-05-08T08:53:32.888984+00:00`

## Why This Objective Exists

The minimal subject-relative preprocessed training first pass is complete, but the result was not sufficient.

Current report diagnosis:

- `preprocessed_subject_relative_first_pass_not_sufficient`

The project should not immediately jump to another fix.

Instead, it must answer why the intervention failed and whether the subject-variability diagnosis remains valid.

## Scientific Question

Why did the subject-relative + preprocessing intervention fail, and does the failure support or weaken the hypothesis that low accuracy is primarily caused by subject variability?

## Key Distinction

This objective separates two different questions:

1. Was the root-cause diagnosis wrong?
2. Or was the tested intervention too weak / incomplete for the diagnosed problem?

This distinction is required before choosing SupCon, VREx, domain generalization, feature engineering, or another task formulation.

## Authorized Scope

Read-only diagnostic analysis from existing committed outputs.

Allowed inputs include:

- `docs/idare_subject_relative_preprocessed_minimal_training_report.md`
- `docs/idare_subject_relative_preprocessed_minimal_training_report.json`
- `docs/idare_subject_relative_representation_preprocessing_report.md`
- `docs/idare_subject_relative_representation_preprocessing_report.json`
- `docs/idare_root_cause_diagnostic_report.md`
- `docs/idare_diagnostic_sanity_tests_report.md`
- Existing fold/task/subject/prediction summaries already committed under `docs/`

No new performance training is authorized.

## Required Analysis Questions

### 1. Diagnosis validity

Does subject variability remain a leading blocker after the failed intervention?

### 2. Intervention adequacy

Did preprocessing reduce domain shift without improving label separation enough?

### 3. Label/task formulation

Did subject-relative labels improve balance but still fail to create a separable affective task?

### 4. Failure localization

Is the failure broad or concentrated?

### 5. Next-method justification

Which next method is scientifically justified?

Candidates to evaluate:

- affective SupCon across subjects
- VREx / domain generalization
- subject-aware adaptation or calibration
- feature engineering
- further task/label redesign
- stop / handoff

The report must decide whether SupCon/DG is justified by the evidence, not merely because it exists in the project plan.

## Expected Outputs

- `docs/idare_subject_variability_intervention_failure_analysis_report.md`
- `docs/idare_subject_variability_intervention_failure_analysis_report.json`
- `docs/idare_subject_variability_intervention_failure_fold_task_summary.csv`
- `docs/idare_subject_variability_intervention_failure_decision_matrix.csv`

## Pass Criteria

The analysis passes only if it:

1. Explains the failure of the tested intervention or explicitly says evidence is insufficient.
2. Separates root-cause validity from intervention adequacy.
3. States whether subject variability remains a leading blocker.
4. States whether affective SupCon / VREx / DG is justified as a targeted next step.
5. Avoids final LOSO, fusion, architecture, augmentation, or mainline-change claims.
6. Updates the central roadmap.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- mainline change
- SupCon / VREx / domain generalization training
- generic feature engineering training
- architecture ablation for improvement
- data augmentation
- broad hyperparameter search

## Next Allowed Step

Prepare and run a reviewed read-only intervention-failure analysis script.
