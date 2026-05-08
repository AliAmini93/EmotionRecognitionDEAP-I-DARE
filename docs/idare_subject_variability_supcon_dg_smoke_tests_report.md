# I-DARE Subject-variability SupCon/DG Smoke Tests Report

## Status

Smoke tests complete.

Generated UTC: `2026-05-08T09:34:48.154438+00:00`

Objective: `docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md`

Design spec: `docs/idare_subject_variability_supcon_dg_design_spec.md`

## Executive Result

Diagnosis: `supcon_dg_smoke_tests_passed_ready_for_minimal_first_pass_objective`

Recommended next objective: `minimal_supcon_dg_first_pass_training_objective`

All smoke tests passed: `True`

Device: `cuda`

## Smoke-test Summary

- `leakage_guard_smoke`: 4 passed, 0 failed
- `one_fold_one_task_minimal_smoke`: 4 passed, 0 failed
- `pair_sampler_integrity_smoke`: 4 passed, 0 failed
- `shuffled_label_negative_control`: 4 passed, 0 failed
- `supcon_micro_overfit_smoke`: 4 passed, 0 failed

## Failed Smoke Tests

- none

## Pair/Sampler Audit

Detailed CSV:

- `docs/idare_subject_variability_supcon_dg_pair_sampler_audit.csv`

The pair/sampler audit checks that balanced batches contain both classes, multiple subjects, and cross-subject positive-pair availability.

## Loss Trace Summary

Detailed CSV:

- `docs/idare_subject_variability_supcon_dg_loss_trace_summary.csv`

The loss trace summary records CE, SupCon, and total loss movement for micro-overfit, shuffled-label negative control, and one-fold minimal smoke tests.

## Embedding Diagnostic Summary

Detailed CSV:

- `docs/idare_subject_variability_supcon_dg_embedding_diagnostic_summary.csv`

The embedding diagnostic summary records embedding variance, norm, centroid distance, collapse flag, prediction counts, and one-class prediction status.

## One-fold Minimal Smoke Metrics

- EEG valence: macro-F1=0.414, balanced-accuracy=0.419, one-class=False
- EEG arousal: macro-F1=0.450, balanced-accuracy=0.453, one-class=False
- EMG valence: macro-F1=0.531, balanced-accuracy=0.531, one-class=False
- EMG arousal: macro-F1=0.541, balanced-accuracy=0.552, one-class=False

## Interpretation

This report still does **not** authorize full SupCon/DG training.

If all smoke tests passed, the next scientific step is a human review/closeout and then a minimal first-pass training objective.

If any smoke test failed, the next step must be a targeted fix objective, not broader training.

Failure interpretation:

- sampler failure -> fix positive/negative pair construction;
- leakage failure -> fix protocol and data split;
- micro-overfit failure -> fix implementation or optimization;
- negative-control failure -> audit leakage/evaluation;
- one-fold smoke failure -> inspect pair coverage, loss traces, embedding diagnostics, and prediction collapse.

## Next Allowed Step

Human review / closeout before any minimal SupCon/DG first-pass training objective.
