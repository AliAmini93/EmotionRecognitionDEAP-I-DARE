# I-DARE Alternative Pairwise Feature-Representation Patch Smoke Tests Objective

## Status

Status: objective created; smoke-test only; no training is authorized.

Created UTC: `2026-05-09T00:52:45+00:00`

## Scientific Question

Can the selected narrow EEG/arousal feature-representation patch be constructed safely, deterministically, and without leakage before any patch training is considered?

## Accepted Spec

Accepted patch spec: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_spec.md`

Selected primary patch: `PATCH_A_eeg_arousal_bandpower_temporal_stats_v1`

Selected formulation: `within_subject_pairwise_affect_preference_ranking_v1`

Frozen matrix rows to audit: `96`

## Authorized Scope

- Smoke-test feature extraction.
- Validate cache/window alignment.
- Validate fold-local transform logic.
- Validate same-subject pair construction.
- Validate frozen run matrix scope.
- Write committed script and docs for reproducibility.

## Not Authorized

- patch model training before smoke-test review
- broad hyperparameter search
- direct full SupCon/DG training
- EEG+EMG fusion
- final LOSO claim
- changing label formulation during this patch branch

## Smoke Requirements

See: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_requirements.csv`

## Feature Guardrails

See: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_feature_guardrails.csv`

## Input Map

See: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_input_map.csv`

## Expected Outputs

See: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_expected_outputs.csv`

## Decision Tree

See: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_smoke_decision_tree.csv`

## Pass Criteria

- All smoke requirements pass.
- Feature matrices are finite and shape-consistent.
- Pair targets are within-subject only and aligned to arousal.
- Fold-local transform guard passes.
- Frozen matrix scope is unchanged.
- No learned patch model training is run.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_pairwise_feature_representation_patch_smoke_tests_command`
