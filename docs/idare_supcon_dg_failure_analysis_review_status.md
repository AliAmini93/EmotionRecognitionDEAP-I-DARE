# I-DARE SupCon/DG Failure-analysis Review Status

## Status

Human review closed on: `2026-05-08T10:06:00+00:00`

The read-only SupCon/DG failure-analysis report is accepted for planning purposes.

Reviewed report:

- `docs/idare_supcon_dg_failure_analysis_report.md`
- `docs/idare_supcon_dg_failure_analysis_report.json`

## Review Decision

Accepted diagnosis:

`supcon_dg_first_pass_failed_despite_valid_smokes`

Scientific interpretation:

- SupCon/DG smoke tests passed, so the basic plumbing, sampler integrity, leakage guards, micro-overfit behavior, and negative-control behavior were not the obvious blocker.
- The minimal first-pass training did not produce a reliable subject-heldout improvement.
- The failure should not be treated as evidence that SupCon/DG is intrinsically unsuitable.
- The failure should be treated as evidence that the first-pass pair/sampler/objective design was probably too broad or too weak for the subject-variability mechanism.

Best first-pass cell recorded by the failure-analysis report:

```json
{"folds_over_055_macro_f1": 2, "folds_under_050_macro_f1": 3, "max_macro_f1": 0.5563108336859924, "mean_accuracy": 0.5185094553335976, "mean_balanced_accuracy": 0.5151315622001712, "mean_macro_f1": 0.5064987409626325, "method": "CE_plus_VREx", "min_macro_f1": 0.4376097222411236, "modality": "EMG", "n_runs": 6, "one_class_pred_count": 0, "std_macro_f1": 0.04144051165063541, "task": "valence"}
```

## Caution Requirement

No broad SupCon/DG training is authorized from this review.

The next step must be a design/spec objective that makes the pair definition, negative definition, batch sampler, loss weights, and diagnostic pass/fail rules explicit before any new training run.

## Next Selected Step

Create a targeted SupCon/DG pair/sampler ablation-design objective.

Selected objective:

`targeted_supcon_dg_pair_sampler_objective_ablation_design`

## Explicitly Blocked

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change
