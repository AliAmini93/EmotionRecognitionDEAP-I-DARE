# I-DARE Alternative Pairwise Target/Sampling Audit Objective

## Status

Status: objective created; read-only target/sampling audit only; no training is authorized.

Created UTC: `2026-05-09T07:27:24+00:00`

## Scientific Question

Did target construction or pair sampling dilute the weak pairwise signal, and is there any read-only reason to keep the pairwise formulation alive?

## Accepted Context

Feature patch archive-closeout diagnosis: `feature_patch_branch_archived_as_negative_result`

Feature patch archive-closeout decision: `archive_closeout_complete_for_patch_a_eeg_arousal_bandpower_temporal_stats`

Closed feature patch: `PATCH_A_eeg_arousal_bandpower_temporal_stats_v1`

Pairwise formulation remains not archived by this objective: `within_subject_pairwise_affect_preference_ranking_v1`

## Authorized Work

- Read existing committed pairwise smoke-test and first-pass outputs.
- Audit pair counts, fold distribution, subject concentration, and metric alignment.
- Produce read-only diagnostics explaining whether sampling/target construction may explain weak signal.
- Recommend only one of: pause, archive after review, or create a future spec-only target/sampling rethink objective.

## Not Authorized

- any training or rerun
- model fitting
- new feature patch search
- broad hyperparameter search
- direct full SupCon/DG training
- EEG+EMG fusion
- final LOSO claim
- changing labels or fold definitions
- changing the task formulation

## Required Questions

`docs/idare_label_semantics_alternative_pairwise_target_sampling_audit_questions.csv`

## Input Map

`docs/idare_label_semantics_alternative_pairwise_target_sampling_audit_input_map.csv`

## Scope

`docs/idare_label_semantics_alternative_pairwise_target_sampling_audit_scope.csv`

## Decision Tree

`docs/idare_label_semantics_alternative_pairwise_target_sampling_audit_decision_tree.csv`

## Expected Outputs

`docs/idare_label_semantics_alternative_pairwise_target_sampling_audit_expected_outputs.csv`

## Guardrails

`docs/idare_label_semantics_alternative_pairwise_target_sampling_audit_guardrails.csv`

## Pass Criteria

- Audit remains read-only.
- No model training, rerun, feature search, or broad search is performed.
- Report explicitly states whether target/sampling explains the weak signal.
- Report explicitly states whether the pairwise line should pause/archive, or whether a future spec-only sampling rethink objective is justified.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_pairwise_target_sampling_audit_command`
