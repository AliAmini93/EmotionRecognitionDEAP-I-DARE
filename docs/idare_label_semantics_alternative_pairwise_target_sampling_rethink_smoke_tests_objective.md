# I-DARE Alternative Pairwise Target/Sampling Rethink Smoke-Tests Objective

## Status

Status: objective created; smoke-test only; no training is authorized.

Created UTC: `2026-05-09T07:55:48+00:00`

## Scientific Question

Do smoke tests show that the margin-thresholded within-subject pairwise sampling rule is fold-local, deterministic, balanced, and sufficiently populated before any training?

## Accepted Spec

Accepted diagnosis: `target_sampling_rethink_spec_complete`

Accepted decision: `select_margin_thresholded_within_subject_pairwise_preference_for_smoke_test_design`

Selected candidate: `TS_A_margin_thresholded_pairs`

Selected rule: `margin_thresholded_within_subject_pairwise_preference_v1`

Selected formulation: `within_subject_pairwise_affect_preference_ranking_v1`

## Authorized Scope

- Construct and audit pairs under the selected rule.
- Audit train-only margin thresholds.
- Audit within-subject and LOSO fold locality.
- Audit direction balance after deterministic downsampling.
- Audit pair-count sufficiency and reproducibility.

## Not Authorized

- training or rerun
- model fitting
- feature/model search
- broad hyperparameter search
- direct full SupCon/DG training
- EEG+EMG fusion
- final LOSO claim
- minimal first-pass execution before smoke review

## Smoke Requirements

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_requirements.csv`

## Guardrails

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_guardrails.csv`

## Input Map

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_input_map.csv`

## Expected Outputs

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_expected_outputs.csv`

## Decision Tree

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_decision_tree.csv`

## Pass Criteria

- No threshold leakage from validation subjects.
- Zero cross-subject or cross-fold leakage.
- Sufficient train/validation pairs after margin filtering.
- Direction balance passes deterministic bounds.
- Reproducibility audit is stable.
- No training, rerun, or model fitting is performed.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_pairwise_target_sampling_rethink_smoke_tests_command`
