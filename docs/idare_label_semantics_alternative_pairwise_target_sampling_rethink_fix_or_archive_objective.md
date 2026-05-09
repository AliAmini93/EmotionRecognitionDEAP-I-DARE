# I-DARE Alternative Pairwise Target/Sampling Rethink Fix-or-Archive Objective

## Status

Status: objective created; read-only fix/archive decision analysis only; no training is authorized.

Created UTC: `2026-05-09T08:10:20+00:00`

## Scientific Question

Should the failed margin-thresholded target/sampling rethink be patched with a stricter spec-only rule, narrowed to arousal-only, or archived as a negative smoke result?

## Accepted Context

Accepted smoke diagnosis: `target_sampling_rethink_smoke_tests_failed`

All smoke tests passed: `False`

Selected rule under review: `margin_thresholded_within_subject_pairwise_preference_v1`

Selected candidate: `TS_A_margin_thresholded_pairs`

Maximum validation direction imbalance from 0.5: `0.1410537870472009`

Minimum balanced training pairs: `8972`

Minimum validation pairs: `1822`

## Authorized Work

- Read the failed smoke report and audits.
- Explain the direction-balance failure.
- Decide between spec-only fix, narrowed arousal-only rule, or archive.
- Produce a reviewed next-step recommendation.

## Not Authorized

- training
- rerun
- model fitting
- feature/model search
- broad hyperparameter search
- direct full SupCon/DG training
- EEG+EMG fusion
- final LOSO claim
- first-pass execution

## Evidence Summary

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_fix_or_archive_evidence_summary.csv`

## Fix Options

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_fix_options.csv`

## Archive Scope

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_archive_scope.csv`

## Decision Tree

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_fix_or_archive_decision_tree.csv`

## Expected Outputs

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_fix_or_archive_expected_outputs.csv`

## Pass Criteria

- The decision must not authorize training.
- The direction-balance failure must be explicitly explained.
- If a fix is recommended, it must be spec-only and train-label-safe.
- If archive is recommended, archive scope must be explicit.
- The broader pairwise formulation must not be archived unless explicitly justified by a separate branch-level objective.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_pairwise_target_sampling_rethink_fix_or_archive_command`
