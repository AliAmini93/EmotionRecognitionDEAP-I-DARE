# I-DARE Representation Redesign Confirmation Closeout Report

## Status

`closeout_ready`

## Produced Files

- `docs/idare_repr_redesign_confirm_runs.csv`
- `docs/idare_repr_redesign_confirm_metric_summary.csv`
- `docs/idare_repr_redesign_confirm_fold_level_report.md`
- `docs/idare_repr_redesign_confirm_leakage_audit.json`
- `docs/idare_repr_redesign_confirm_r2_vs_r3_stability_comparison.csv`
- `docs/idare_repr_redesign_confirm_closeout_report.md`
- `docs/idare_repr_redesign_confirm_closeout_report.json`
- `docs/idare_repr_redesign_confirm_artifact_review_bundle.json`
- `docs/idare_repr_redesign_confirm_artifact_review_bundle.md`

## Mean Balanced Accuracy

- R0_current_representation_anchor: 0.524883
- R2_train_only_subject_invariant_feature_selection: 0.520177
- R3_diagnostics_first_stable_feature_subset: 0.492628

## R2 vs R3 Stability

- R2 wins vs R3: 4
- R3 wins vs R2: 2
- R2 fold wins vs R0: 3
- R3 fold wins vs R0: 2

## Leakage / Gate Result

- leakage audit pass: `True`
- one-class collapse total: `0`
- forbidden scope touched: `False`
- thresholds changed: `False`
- R3 >= 0.53 moderate gate: `False`
- R3 >= 0.55 strong gate: `False`
- R3 positive delta vs R0: `False`
- confirmation gate pass: `False`

No DEAP, fusion, preprocessing changes, threshold changes, DG execution, model-capacity probe, augmentation, W1-owned edits, or main push were performed by this runner.
