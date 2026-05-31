# I-DARE Representation Redesign Design Objective

## Status

`created`

## Objective ID

`idare_representation_redesign_design_objective`

## Scope

Control Tower documentation/design only.

Forbidden:
- no experiments
- no runner creation
- no Wave 2 execution
- no DG execution
- no model-capacity probe
- no augmentation
- no DEAP
- no fusion
- no preprocessing changes
- no threshold changes
- no main push
- no W1 branch-owned file modifications

## Current Decision Context

Representation redesign is the primary next design path after:

- Wave 1 performance gate failed.
- W1D showed within-subject signal exists but cross-subject signal collapses due to subject-dominated geometry.
- W1B showed only transductive diagnostic heterogeneity reduction.
- W1A input-definition variants did not rescue pairwise arousal performance.
- W1C EMG aggregate no-pass.
- Strict NTD normalization smoke was technically clean but weak.

## Evidence for Subject-Dominated Representation

The current representation is considered subject-dominated because:

1. W1D found strong within-subject affective signal but weak cross-subject label discriminability.
2. W1D showed subject identity dominates feature geometry.
3. W1B B3 reduced heterogeneity only with transductive per-subject rank normalization.
4. Strict NTD normalization did not materially improve cross-subject pairwise performance.
5. W1A input-definition variants did not expose hidden cross-subject arousal signal.

## Weak / Archived Representations

The following are archived as insufficient as primary next drivers:

| Representation / path | Status | Reason |
|---|---|---|
| W1A A1 current STIM-BSL summary | insufficient | did not pass pairwise gate |
| W1A A2 BSL-stats sidecar | insufficient but best W1A | below gate |
| W1A A3 concat | insufficient | below gate |
| W1B B3 per-subject rank | diagnostic only | transductive, not strict evidence |
| W1C EMG ridge features | independent reference only | aggregate no-pass |
| Strict NTD S0/S1/S2/S3 | clean weak-effect baseline | no gate pass |
| PATCH_A-style blind reuse | not approved | should not be reused blindly without representation diagnostics |

## Candidate Representation Redesign Families

| Family | Status | Rationale |
|---|---|---|
| R1 train-only subject-residualized features | primary design candidate | Directly targets subject-dominated geometry while preserving strict train-only constraints. |
| R2 subject-invariant feature selection using train subjects only | primary design candidate | Selects features with label signal but low subject separability. |
| R3 representation quality diagnostics before training | required design layer | Avoids blindly launching models before checking subject/label geometry. |
| R4 improved temporal/spectral representations | reviewable candidate | Could improve signal extraction, but must not reuse failed PATCH_A blindly. |
| R5 EEG-first redesigned summaries | primary modality | EEG shows stronger within-subject signal than EMG. |
| R6 EMG representation redesign | deferred | EMG no-pass; keep as reference unless explicitly justified. |
| R7 DG on top of redesigned representation | secondary | DG should wait until representation assumptions are improved. |
| R8 neural/model-capacity representation learning | deferred | Too broad before a small interpretable representation smoke. |
| R9 augmentation-based representation change | deferred | Premature before leakage policy and stable representation design. |

## Low-Risk Future Smoke Candidates

If execution is later authorized, the lowest-risk smoke should be small and diagnostic-first:

| Cell | Candidate | Description |
|---|---|---|
| R0 | current best anchor | strict NTD S3 or current pairwise reference, depending on finalized design |
| R1 | train-only subject-residualized features | residualization learned on training subjects only |
| R2 | train-only subject-invariant feature selection | select low subject-dominance / nonzero label-signal features using train subjects only |
| R3 | representation diagnostic-only cell | no classifier claim; quantify subject separability vs label separability |

## High-Risk / Deferred Candidates

| Candidate | Reason for deferral |
|---|---|
| full neural representation learning | model-capacity confound |
| DG execution | should be secondary until representation is improved |
| augmentation | leakage and attribution risk |
| fusion | single-modality readiness not established |
| DEAP transfer | outside locked scope |
| preprocessing rebuild | forbidden |
| broad temporal/spectral search | too wide without diagnostic filter |

## Leakage Boundaries

All future representation redesign candidates must obey:

- train-subject-only fitting
- no held-out/test-subject feature statistics
- no held-out/test labels
- no global transform fit across all subjects
- no per-test-subject normalization
- no target-domain adaptation
- no threshold tuning on held-out subjects
- no preprocessing/cache rebuild
- no DEAP or fusion
- no W1 branch-owned file edits

## Minimum Future Smoke Matrix

A defensible future smoke, if separately authorized, should be minimal:

| Cell | Type | Description |
|---|---|---|
| R0 | anchor | current strict NTD best or REF-PW-EEG-ARO-001 anchor |
| R1 | residualized | train-only subject-residualized EEG features |
| R2 | selected | train-only subject-invariant feature-selected EEG features |
| R3 | diagnostic | subject-vs-label separability report before classifier interpretation |

This should remain EEG-first and arousal-only unless Control Tower explicitly expands scope.

## References for Future Comparison

Future results must compare against:

- REF-PW-EEG-ARO-001
- W1A A2 best pairwise input-definition result
- W1B B3 transductive diagnostic result, clearly labeled non-strict
- W1D subject-dominance diagnosis
- Strict NTD S3 smoke result
- majority baseline

## Stop Criteria

Representation redesign should be archived or pivoted if:

- no redesigned representation improves meaningfully over R0 anchor
- subject separability remains dominant with no label-separability gain
- gains appear only in transductive or leakage-prone settings
- no cell approaches the unchanged moderate gate
- diagnostics suggest representation redesign is too broad or unstable

## DG Position

DG remains secondary until a better representation exists.

DG design may remain reviewable, but DG execution is not authorized by this objective.

## Current Ruling

This objective does not authorize execution.

## Next State

`REQUEST_REPRESENTATION_REDESIGN_DESIGN_REVIEW`
