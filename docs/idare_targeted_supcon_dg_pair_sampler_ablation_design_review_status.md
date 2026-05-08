# I-DARE Targeted SupCon/DG Pair-Sampler Design Review Status

## Status

Human review closed on: `2026-05-08T10:14:18+00:00`

Reviewed design objective:

- `docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md`
- `docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.json`

## Review Decision

The targeted pair/sampler design is accepted for a **minimal diagnostic ablation**, not broad training.

The review accepts the following scientific logic:

- First-pass SupCon/DG failed despite valid smoke tests.
- The failure-analysis report recommended targeted pair/sampler ablation.
- The design now separates pair definition, negative definition, sampler policy, and DG penalty.
- The next run must be small, guardrailed, and interpretable.

## Selected First Ablation Candidates

The first ablation matrix is limited to these candidates:

1. `A0_CE_control`
2. `A2_cross_subject_positive_only`
3. `A4_rating_distance_guarded_supcon`
4. `A6_vrex_only_recheck`
5. `A5_cross_subject_supcon_vrex`

The candidate matrix is stored in:

`docs/idare_targeted_supcon_dg_pair_sampler_ablation_run_matrix.csv`

Planned diagnostic run rows: `120`

## Caution Requirement

This review does **not** authorize direct full SupCon/DG training.

It authorizes one guardrailed first-pass ablation with fixed hyperparameters and required smoke tests.

## Explicitly Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change

## Next Selected Step

Prepare/run the guardrailed targeted pair/sampler ablation command.
