# I-DARE Targeted SupCon/DG Pair-Sampler Ablation Review Status

## Status

Status: human review accepted targeted pair/sampler ablation as insufficient.

Created UTC: `2026-05-08T10:30:45+00:00`

## Review Decision

The targeted SupCon/DG pair-sampler ablation is accepted as a completed diagnostic run, not as a successful fix.

Primary diagnosis from the report:

`targeted_pair_sampler_ablation_not_sufficient`

Recommended next objective:

`supcon_dg_pair_sampler_failure_analysis_objective`

Best aggregate candidate:

- Candidate: `A5_cross_subject_supcon_vrex`
- Mean macro-F1: `0.5119`
- Mean balanced accuracy: `0.5164`

## Evidence Reviewed

- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.md`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_report.json`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_runs.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_predictions.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_pair_audit.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_loss_embedding_summary.csv`
- `docs/idare_targeted_supcon_dg_pair_sampler_ablation_candidate_summary.csv`

## Result Summary

The ablation completed `120` runs and `40320` prediction rows. Guardrails passed, but the best candidate was still not stable enough to justify full SupCon/DG training.

The failure should now be analyzed before any new training or broad hyperparameter search.

## Next Selected Step

Create and run a read-only SupCon/DG pair-sampler failure-analysis objective.

## Blocked Until Review

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
- new training before failure-analysis review
