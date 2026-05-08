# I-DARE Subject-relative Preprocessed Minimal Training Review Status

## Status

Frozen human-review closeout.

Generated UTC: `2026-05-08T08:53:32.888984+00:00`

## Reviewed Evidence

- Report: `docs/idare_subject_relative_preprocessed_minimal_training_report.md`
- JSON: `docs/idare_subject_relative_preprocessed_minimal_training_report.json`
- Evidence level: 24-run minimal diagnostic training; not final LOSO performance.

## Review Decision

Accepted.

The subject-relative preprocessed first-pass result is accepted as a failed or insufficient intervention, not as evidence that the full subject-variability diagnosis is wrong.

Current diagnosis from the report:

- `preprocessed_subject_relative_first_pass_not_sufficient`

Original recommended next objective from the report:

- `subject_relative_feature_engineering_objective`

Human review pauses the immediate move to generic feature engineering.

## Scientific Interpretation

The result does not prove that subject variability is not the problem.

It shows that the tested intervention was not strong enough:

- subject-relative labels
- EEG window/channel z-score summary features
- EMG signed-log1p features
- train-fold-only scaling
- CE-only first-pass training

This combination did not produce enough subject-heldout improvement to justify a mainline change.

## Review Rationale

A failed intervention should be audited before proposing another fix.

The next question is not merely:

> What else can we try?

The next question is:

> Why did this intervention fail if subject variability was the hypothesized blocker?

Possible explanations include:

1. The subject-variability diagnosis is correct, but preprocessing is too weak.
2. Subject-relative labels reduce global bias but do not create separable affective representation.
3. Subject identity remains dominant after preprocessing.
4. The tested CE-only objective does not explicitly force cross-subject affect alignment.
5. A SupCon / VREx / DG method may be justified only if the failure analysis shows the remaining blocker is specifically cross-subject representation mismatch.
6. The issue may also involve label/task formulation or low within-subject signal, in which case SupCon/DG would not be enough.

## Mainline After Review

No mainline changes.

## Next Allowed Step

Create and run the controlled subject-variability intervention-failure analysis objective:

- `docs/idare_subject_variability_intervention_failure_analysis_objective.md`

## Intentionally Not Authorized

- EEG+EMG fusion
- Final LOSO / final paper claim
- Mainline change
- Generic feature engineering objective
- SupCon / VREx / domain generalization training
- Architecture ablation for improvement
- Data augmentation
- Broad hyperparameter search
