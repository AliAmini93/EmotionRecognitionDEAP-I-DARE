# I-DARE Subject-variability SupCon/DG Smoke Tests Objective

## Status

Objective created.

This is a smoke-test-only objective.

No full SupCon/DG training is authorized by this document.

Generated UTC: `2026-05-08T09:29:54.424115+00:00`

## Parent Review

- Review: `docs/idare_subject_variability_supcon_dg_design_spec_review_status.md`
- Design spec: `docs/idare_subject_variability_supcon_dg_design_spec.md`

## Scientific Question

Can the proposed SupCon/DG intervention be implemented safely enough to justify a future minimal first-pass training objective?

This objective does not ask whether SupCon/DG improves final performance.

It asks whether the pair sampler, leakage guards, loss implementation, negative controls, and minimal one-fold execution are valid.

## Authorized Scope

Authorized:

- smoke tests only;
- temporary local implementation/helpers if needed;
- fold-1-only diagnostic runs unless the script is explicitly read-only;
- subject-relative q33 labels;
- CE+SupCon smoke branch;
- logs for pair coverage, loss traces, embedding separation, and negative controls.

Not authorized:

- full first-pass SupCon/DG training matrix
- broad hyperparameter search
- fusion
- mainline change
- final LOSO claim

## Required Smoke Tests

1. `pair_sampler_integrity_smoke` — pass gate: all audited batches contain both classes, at least 4 subjects, positive_pair_coverage >= 0.95, anchors_without_positive <= 0.05
2. `leakage_guard_smoke` — pass gate: no validation sample appears in train scaler, train pairs, positive/negative pools, or environment-risk terms
3. `supcon_micro_overfit_smoke` — pass gate: tiny train-only subset overfits; CE and SupCon losses are finite and decreasing; embeddings do not collapse
4. `shuffled_label_negative_control` — pass gate: train-label-shuffled control remains near chance and does not show suspicious gain
5. `one_fold_one_task_minimal_smoke` — pass gate: one fold/task run completes with valid logs, non-collapsed predictions, and embedding/pair diagnostics

## Expected Outputs

- `docs/idare_subject_variability_supcon_dg_smoke_tests_report.md`
- `docs/idare_subject_variability_supcon_dg_smoke_tests_report.json`
- `docs/idare_subject_variability_supcon_dg_pair_sampler_audit.csv`
- `docs/idare_subject_variability_supcon_dg_loss_trace_summary.csv`
- `docs/idare_subject_variability_supcon_dg_embedding_diagnostic_summary.csv`

## Pass Criteria

The smoke-test objective passes only if:

- all required smoke tests execute or fail with a clear diagnostic reason;
- leakage guard passes;
- pair sampler audit satisfies the design gates;
- micro-overfit succeeds without collapse;
- shuffled-label negative control does not show suspicious performance;
- one-fold minimal smoke produces interpretable predictions and diagnostics;
- the report recommends either implementation fixes, sampler fixes, or a future minimal training objective.

## Failure Interpretation

If smoke tests fail, the correct response is not to tune broadly.

The correct response is to localize the failure:

- sampler failure -> fix positive/negative pair construction;
- leakage failure -> fix protocol;
- micro-overfit failure -> fix implementation/optimization;
- negative-control failure -> audit leakage/evaluation;
- one-fold smoke failure -> inspect pair coverage, loss traces, embedding diagnostics, and prediction collapse.

## Next Allowed Step

Prepare a reviewed Bash command/script for smoke tests only.
