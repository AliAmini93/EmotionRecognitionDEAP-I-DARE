# I-DARE Alternative Pairwise Target/Sampling Rethink Spec Objective

## Status

Status: objective created; spec-only target/sampling rethink; no training is authorized.

Created UTC: `2026-05-09T07:41:38+00:00`

## Scientific Question

Can we define one narrow, deterministic target/sampling rethink that addresses the accepted sampling artifact without authorizing training?

## Accepted Context

Accepted audit diagnosis: `alternative_pairwise_target_sampling_audit_possible_sampling_artifact`

Accepted audit recommendation: `create_spec_only_pair_sampling_rethink_after_review`

Selected formulation still under consideration: `within_subject_pairwise_affect_preference_ranking_v1`

Closed feature patch: `PATCH_A_eeg_arousal_bandpower_temporal_stats_v1`

## Evidence Summary

- Actionable sampling issue: `true`
- Max pair-count CV: `0.053701307121725314`
- Class-balance issue: `True`
- Best prior mean balanced accuracy: `0.5216709095350218`
- Best prior delta vs majority: `0.02167090953502182`
- Subject positive fraction: `nan`
- Top-20% absolute lift share: `nan`

## Authorized Work

- Choose exactly one narrow target/sampling rethink candidate, or choose pause/archive.
- Produce an implementation-ready spec.
- Define smoke-test requirements for any future execution.
- Define stop/archive criteria before any future first-pass training.

## Not Authorized

- training or rerun
- model fitting
- feature/model search
- broad hyperparameter search
- direct full SupCon/DG training
- EEG+EMG fusion
- final LOSO claim
- executing a redesigned sampling matrix

## Candidate Matrix

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_candidate_matrix.csv`

## Design Constraints

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_design_constraints.csv`

## Input Map

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_input_map.csv`

## Guardrails

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_guardrails.csv`

## Decision Tree

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_decision_tree.csv`

## Expected Outputs

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_expected_outputs.csv`

## Spec Requirements

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_spec_requirements.csv`

## Pass Criteria

- The output remains spec-only.
- Exactly one target/sampling rule or archive/pause option is selected.
- Any future execution is blocked behind a separate smoke-test objective.
- No training, rerun, model fitting, feature search, or final claim is authorized.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_pairwise_target_sampling_rethink_spec_command`
