# I-DARE Alternative Pairwise Feature-Representation Patch Objective

## Status

Status: objective created; design/spec only; no training is authorized.

Created UTC: `2026-05-09T00:42:47+00:00`

## Scientific Question

Can a narrow, deterministic feature-representation patch explain or strengthen the weak-but-consistent EEG/arousal pairwise signal without broad search or changing label semantics?

## Accepted Context

Accepted metric-debug diagnosis: `alternative_pairwise_metric_debug_weak_but_consistent_signal`

Best current cell: `ridge_classifier_pairwise_summary_diff` / `EEG` / `arousal`

- Mean balanced accuracy: `0.521671`
- Delta vs majority baseline: `0.021671`
- Positive-delta folds: `6` / `6`
- Subject positive-lift fraction: `0.603175`

Interpretation: signal is weak but consistent; current summary features may be limiting.

## Authorized Work

- Design a narrow feature-representation patch specification.
- Keep label formulation frozen: `within_subject_pairwise_affect_preference_ranking_v1`.
- Keep scope centered on EEG/arousal pairwise branch.
- Define fixed candidate matrix, metrics, thresholds, stop criteria, and reproducibility plan.
- Prepare a future reviewed command/script only after this objective is accepted.

## Not Authorized

- broad hyperparameter search
- direct full SupCon/DG training
- EEG+EMG fusion
- final LOSO claim
- training before reviewed patch spec/run matrix
- changing the label formulation during feature patching

## Candidate Matrix

See: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_candidate_matrix.csv`

## Guardrails

See: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_guardrails.csv`

## Input Map

See: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_input_map.csv`

## Decision Tree

See: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_decision_tree.csv`

## Expected Outputs

See: `docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_expected_outputs.csv`

## Pass Criteria

- The patch objective remains design/spec only.
- No training is run.
- Candidate patch matrix is narrow and frozen.
- All transforms must be fold-local.
- Stop/archive criteria must be explicit before any future patch execution.
- Broad search, SupCon/DG, fusion, and final claims remain blocked.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_pairwise_feature_representation_patch_command`
