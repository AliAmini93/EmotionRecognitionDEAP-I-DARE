# I-DARE Alternative Pairwise Minimal First-Pass Objective

## Status

Status: objective created; minimal diagnostic first pass only; no broad search is authorized.

Created UTC: `2026-05-08T16:58:43+00:00`

## Scientific Question

Does a minimal classical first pass show actionable signal for the within-subject pairwise affect preference formulation beyond no-training controls?

## Selected Formulation

Formulation: `within_subject_pairwise_affect_preference_ranking_v1`

Accepted smoke diagnosis: `alternative_pairwise_formulation_smoke_tests_passed`

## Authorized Scope

This objective authorizes only the frozen minimal first-pass matrix in:

`docs/idare_label_semantics_alternative_pairwise_minimal_first_pass_run_matrix.csv`

Planned rows: `96`

Authorized models:

- `random_balanced_no_training`
- `majority_train_label_no_training`
- `logistic_regression_pairwise_summary_diff`
- `ridge_classifier_pairwise_summary_diff`

Authorized modalities: `EEG`, `EMG`

Authorized tasks: `valence`, `arousal`

Authorized folds: `1..6`

## Not Authorized

- broad hyperparameter search
- direct full SupCon/DG training
- EEG+EMG fusion
- final LOSO claim
- training outside frozen minimal first-pass matrix
- using archived `subject_relative_ordinal_affect_regression_v1` formulation
- claiming final performance from this diagnostic first pass

## Guardrails

See: `docs/idare_label_semantics_alternative_pairwise_minimal_first_pass_guardrails.csv`

## Metric Thresholds

See: `docs/idare_label_semantics_alternative_pairwise_minimal_first_pass_metric_thresholds.csv`

## Expected Outputs

See: `docs/idare_label_semantics_alternative_pairwise_minimal_first_pass_expected_outputs.csv`

## Pass Criteria

- Run exactly the frozen matrix.
- Commit the run script under `scripts/idare/analysis`.
- Report no-training baselines separately.
- Use pairwise balanced accuracy and macro F1 as primary diagnostic metrics.
- Do not make a final LOSO claim.
- Recommend confirm/patch/archive only after first-pass analysis.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_pairwise_minimal_first_pass_run_command`
