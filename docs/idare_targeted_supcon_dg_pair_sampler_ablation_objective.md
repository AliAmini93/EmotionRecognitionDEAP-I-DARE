# I-DARE Targeted SupCon/DG Pair-Sampler Ablation Objective

## Status

Created: `2026-05-08T10:14:18+00:00`

Status: objective created for one guardrailed diagnostic ablation.

This objective follows:

- `docs/idare_supcon_dg_failure_analysis_report.md`
- `docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_design_matrix.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_smoke_test_plan.csv`

## Scientific Question

Does a targeted pair/sampler definition improve subject-heldout performance compared with CE and VREx controls?

More specifically:

1. Do cross-subject positives help more than naive label-only positives?
2. Do rating-distance-guarded positives/negatives reduce label-threshold noise?
3. Is VREx alone stronger than SupCon for this subject-variability problem?
4. Does SupCon + VREx help only when pair definitions are more careful?

## Authorized Scope

This is a **minimal diagnostic ablation**, not full training.

Authorized:

- required smoke tests before training
- fixed candidate matrix only
- fixed hyperparameters only
- EEG and EMG
- valence and arousal
- 6 subject-heldout folds
- no broad hyperparameter search

## Planned Run Matrix

Planned run matrix:

`docs/idare_targeted_supcon_dg_pair_sampler_ablation_run_matrix.csv`

Planned run rows: `120`

Selected candidates:

| Candidate | Mechanism |
|---|---|
| `A0_CE_control` | matched CE baseline |
| `A2_cross_subject_positive_only` | same-label positives across subjects only |
| `A4_rating_distance_guarded_supcon` | avoids borderline positive/negative contradictions |
| `A6_vrex_only_recheck` | checks best first-pass DG family without SupCon |
| `A5_cross_subject_supcon_vrex` | combines cross-subject SupCon with VREx |

## Required Guardrails

Guardrails are stored in:

`docs/idare_targeted_supcon_dg_pair_sampler_ablation_guardrails.csv`

The run command must stop if:

- repo is not clean
- leakage guard fails
- pair coverage fails
- batch balance fails
- rating-distance audit fails for guarded candidates
- micro-overfit fails
- shuffled-label negative control fails

## Required Smoke Tests Before Training

The run command must execute the smoke tests defined in:

`docs/idare_targeted_supcon_dg_pair_sampler_smoke_test_plan.csv`

Training is blocked if any required smoke test fails.

## Fixed Hyperparameters

The first ablation must use the fixed values in:

`docs/idare_targeted_supcon_dg_pair_sampler_ablation_run_matrix.csv`

This objective does not authorize broad hyperparameter search.

## Expected Outputs

The run command should write:

- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv`

## Pass Criteria

This objective passes only if:

- all required smoke tests are reported
- all candidate/fold/task/modality rows are either complete or explicitly failed
- pair audit shows valid pair coverage
- no leakage is detected
- candidate-level comparison is written
- the decision tree is applied
- direct full SupCon/DG training remains blocked pending human review

## Decision Rules

Use:

`docs/idare_targeted_supcon_dg_pair_sampler_decision_tree.csv`

No isolated best fold is enough. A candidate is only promising if gains are consistent across tasks/folds and interpretable against the candidate mechanism.

## Explicitly Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change

## Next Allowed Step

Prepare and run the guardrailed targeted pair/sampler ablation command.
