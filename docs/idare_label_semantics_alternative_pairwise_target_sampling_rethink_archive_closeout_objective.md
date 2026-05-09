# I-DARE Alternative Pairwise Target/Sampling Rethink Archive-Closeout Objective

## Status

Status: objective created; archive-closeout only; no training is authorized.

Created UTC: `2026-05-09T08:22:30+00:00`

## Scientific Question

How do we close out the failed TS_A margin-thresholded target/sampling rethink as a negative smoke result without closing the broader pairwise formulation?

## Accepted Decision

Accepted diagnosis: `target_sampling_rethink_margin_rule_should_be_archived`

Accepted decision: `archive_ts_a_margin_thresholded_pair_sampling_rule`

Selected rule to archive: `margin_thresholded_within_subject_pairwise_preference_v1`

Selected candidate to archive: `TS_A_margin_thresholded_pairs`

Archive TS_A margin rule: `True`

Archive broader pairwise formulation: `False`

## Authorized Work

- Create archive closeout report for TS_A margin-thresholded sampling.
- Build archive manifest for the failed smoke-test branch.
- Mark TS_A as a negative smoke result.
- Preserve broader within-subject pairwise formulation as open-but-blocked pending a separate objective.

## Not Authorized

- training
- rerun
- model fitting
- first-pass execution
- feature/model search
- broad hyperparameter search
- direct full SupCon/DG training
- EEG+EMG fusion
- final LOSO claim
- archive of the broader pairwise formulation

## Archive Closeout Scope

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_archive_closeout_scope.csv`

## Manifest Seed

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_archive_closeout_manifest_seed.csv`

## Stop Criteria

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_archive_closeout_stop_criteria.csv`

## Next Option Policy

`docs/idare_label_semantics_alternative_pairwise_target_sampling_rethink_archive_closeout_next_option_policy.csv`

## Pass Criteria

- The closeout must archive TS_A margin-thresholded sampling as a negative smoke result.
- The closeout must not archive the broader pairwise formulation.
- No training or first-pass execution may be authorized.
- Any future target design must require a new reviewed objective.

## Next Allowed Step

`prepare_reviewed_label_semantics_alternative_pairwise_target_sampling_rethink_archive_closeout_command`
