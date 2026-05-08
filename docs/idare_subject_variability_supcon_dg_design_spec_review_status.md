# I-DARE Subject-variability SupCon/DG Design Spec Review Status

## Status

Human review accepted the cautious SupCon/DG design spec for smoke-test preparation only.

Generated UTC: `2026-05-08T09:29:54.424115+00:00`

## Reviewed Artifact

- Design spec: `docs/idare_subject_variability_supcon_dg_design_spec.md`
- Design spec JSON: `docs/idare_subject_variability_supcon_dg_design_spec.json`
- Pair/sampler spec: `docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv`
- Hyperparameter registry: `docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv`
- Smoke-test plan: `docs/idare_subject_variability_supcon_dg_smoke_test_plan.csv`
- Draft first-pass matrix: `docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv`

## Review Decision

Accepted with caution.

The design is considered sufficient to create a smoke-test objective.

It does **not** authorize full SupCon/DG training.

## Accepted Constraints

- Pair/sampler integrity must be validated before training.
- Leakage guard must pass before any model result is trusted.
- SupCon micro-overfit must pass before any subject-heldout smoke.
- Shuffled-label negative control must not show suspicious performance.
- Hyperparameter selection must remain staged and registry-based.
- Any future improvement must be explainable through sampler logs, loss traces, and embedding/risk diagnostics.

## Next Selected Step

Create and run a smoke-test-only objective:

- `docs/idare_subject_variability_supcon_dg_smoke_tests_objective.md`

## Still Blocked

- full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- mainline change
- final LOSO claim
