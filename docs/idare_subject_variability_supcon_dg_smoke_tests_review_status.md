# I-DARE Subject-variability SupCon/DG Smoke Tests Review Status

## Status

Human review accepted the SupCon/DG smoke-test report.

Created UTC: `2026-05-08T09:39:01.179380+00:00`

Smoke-test report: `docs/idare_subject_variability_supcon_dg_smoke_tests_report.md`

Smoke-test objective: `docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md`

Design spec: `docs/idare_subject_variability_supcon_dg_design_spec.md`

## Review Decision

The smoke-test gate is accepted as passed.

Accepted evidence:

- pair/sampler integrity passed for EEG/EMG valence/arousal;
- leakage guard passed with no row or subject overlap;
- SupCon micro-overfit passed for all selected modality/task checks;
- shuffled-label negative control stayed near chance;
- one-fold minimal smoke did not collapse and produced finite two-class predictions.

## Scientific Interpretation

This does **not** prove SupCon/DG improves performance.

It only proves that the implementation path is safe enough for a minimal first-pass training objective.

Full SupCon/DG training, broad hyperparameter search, fusion, and final claims remain blocked.

## Next Selected Step

Create and run a minimal first-pass SupCon/DG training objective.

The first pass must remain diagnostic and small. It should use the reviewed design spec and first-pass run matrix, not invent new settings mid-run.

## Explicitly Still Blocked

- direct full SupCon/DG training;
- broad hyperparameter search;
- EEG+EMG fusion;
- final LOSO/paper claim;
- mainline/default replacement.
