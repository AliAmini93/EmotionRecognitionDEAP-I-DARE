# I-DARE Alternative Pairwise Feature-Representation Patch First-Pass Objective

## Status

Status: objective created; limited first-pass only; no broad search is authorized.

Created UTC: `2026-05-09T01:02:05+00:00`

## Scientific Question

Does the frozen narrow EEG/arousal feature-representation patch improve pairwise preference ranking enough to justify a later confirmation objective?

## Accepted Smoke-Test Result

Accepted diagnosis: `feature_representation_patch_smoke_tests_passed`

Selected patch: `PATCH_A_eeg_arousal_bandpower_temporal_stats_v1`

Selected formulation: `within_subject_pairwise_affect_preference_ranking_v1`

Frozen run matrix rows: `96`

## Authorized Scope

This objective authorizes only a limited first-pass run of the frozen 96-row matrix.

Allowed:

- `current_summary_diff_control`
- `robust_scaled_current_summary_diff_control`
- `bandpower_only_control_v1`
- `bandpower_temporal_stats_v1`
- no-training controls
- `ridge_classifier_pairwise_feature_patch`
- `logistic_regression_pairwise_feature_patch`
- EEG / arousal only
- fold-local transforms only

## Not Authorized

- broad hyperparameter search
- direct full SupCon/DG training
- EEG+EMG fusion
- final LOSO claim
- changing label formulation during this patch branch
- running outside the frozen 96-row matrix

## Frozen Run Matrix

`docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_run_matrix.csv`

## Guardrails

`docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_guardrails.csv`

## Metric Thresholds

`docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_metric_thresholds.csv`

## Expected Outputs

`docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_expected_outputs.csv`

## Pass Criteria

- Script executes the frozen 96-row matrix only.
- All feature transforms are fold-local.
- No broad search is introduced.
- First-pass metrics are reported against no-training controls.
- A decision matrix evaluates thresholds before any confirmation objective is proposed.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_run_command`
