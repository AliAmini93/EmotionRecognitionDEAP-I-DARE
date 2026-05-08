# I-DARE Label-Semantics Alternative-Formulation Smoke Tests Objective

## Status

Status: objective created; smoke-test only; no training is authorized.

Created UTC: `2026-05-08T15:59:11+00:00`

## Scientific Question

Do read-only smoke tests support the selected within-subject pairwise affect preference formulation before any training is considered?

## Selected Formulation

Selected primary formulation: `within_subject_pairwise_affect_preference_ranking_v1`

Selected candidate: `ALT_A_within_subject_pairwise_preference_ranking`

Archived formulation remains closed: `subject_relative_ordinal_affect_regression_v1`

## Authorized Work

- Construct/audit pairwise targets from existing labels/metadata.
- Audit LOSO pair leakage and reversed-pair leakage.
- Audit pair retention, class balance, and fold coverage.
- Run no-training/position/majority baseline controls.
- Run metric sanity controls.
- Write smoke-test report and decision matrix.

## Not Authorized

- training
- model search
- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- alternative first-pass training
- reopening archived `subject_relative_ordinal_affect_regression_v1` unchanged

## Required Smoke Tests

See: `docs/idare_label_semantics_alternative_formulation_smoke_requirements.csv`

## Pair Guardrails

See: `docs/idare_label_semantics_alternative_formulation_pair_guardrails.csv`

## Expected Outputs

See: `docs/idare_label_semantics_alternative_formulation_smoke_expected_outputs.csv`

## Pass Criteria

- No model training is run.
- All pair leakage guards pass.
- Pair construction has enough retention and class/fold balance to justify later minimal first-pass planning.
- No-feature/position/majority controls do not indicate trivial shortcut success.
- Metric sanity controls behave as expected.
- Decision matrix recommends either minimal first-pass objective, spec patch, or archive/stop.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_formulation_smoke_tests_command`
