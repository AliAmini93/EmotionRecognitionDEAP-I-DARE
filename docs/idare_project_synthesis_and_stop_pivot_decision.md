# I-DARE Project Synthesis and Stop/Pivot Decision

## Status

`created`

## Scope

Control Tower documentation/decision only.

Forbidden:
- no execution
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

## Current Evidence Summary

| Evidence block | Result | Decision impact |
|---|---|---|
| Wave 1 | performance gate failed | no branch produced robust aggregate operating point |
| W1D | within-subject signal exists, cross-subject signal collapses | problem is subject-dominated geometry, not total signal absence |
| W1A | input-definition variants no-pass | simple EEG input alternatives did not rescue pairwise arousal |
| W1B | B3 reduced heterogeneity only transductively | useful diagnostic, not strict non-transductive evidence |
| W1C | EMG aggregate no-pass | EMG remains independent reference only |
| Strict NTD smoke | clean weak effect, no gate pass | simple strict normalization insufficient |
| Representation redesign smoke | R3 moderate pass once | promising but fragile |
| Representation confirmation | failed | R3 not robust; R2 weak comparator; R0 remains reference only |

## Formal Synthesis

The project has not established a robust cross-subject I-DARE operating point.

The evidence supports this diagnosis:

- affective signal exists within subject,
- current cross-subject representations are dominated by subject geometry,
- simple input changes are insufficient,
- strict non-transductive normalization is insufficient,
- the representation redesign smoke produced a moderate signal once,
- confirmation failed to reproduce that operating point.

Therefore, the R3 path is closed as not robust, and R2 is not sufficient as a replacement.

## Stop / Pivot Decision Matrix

| Option | Decision | Rationale |
|---|---|---|
| Continue execution immediately | reject | no robust operating point confirmed |
| Wave 2 interaction grid | reject for now | weak components should not be expanded into larger grid |
| DG execution | reject for now | DG should not be launched on unstable representation |
| Model-capacity probe | reject for now | capacity probing risks noise chasing |
| Augmentation | reject for now | premature and leakage-prone |
| Fusion | reject/frozen | no single-modality readiness |
| DEAP | frozen | outside current locked scope |
| Stop execution and synthesize | accept | most defensible current action |
| Pivot to new representation theory | reviewable later | only after project synthesis is accepted |

## Control Decision

Execution should pause.

Current result should be reported as:

`NO_ROBUST_CROSS_SUBJECT_OPERATING_POINT_FOUND`

This is not a failure of all signal. It is evidence that the current feature/representation family is not sufficient for robust cross-subject transfer under the locked I-DARE-only, single-modality constraints.

## Archived / Closed Paths

| Path | Status |
|---|---|
| W1A tested EEG input definitions | archived no-pass |
| W1B strict non-transductive normalization | archived no-pass |
| W1B B3 transductive rank | diagnostic-only |
| W1C EMG ridge baseline | independent reference only |
| Strict NTD normalization smoke | archived clean weak-effect |
| Representation R3 | rejected not robust |
| Representation R2 | weak comparator, not operating point |

## Future Pivot, If Any

A future pivot must be documentation-first and must define a genuinely new representation hypothesis before execution.

Allowed future pivot themes for review only:

- new representation theory for subject-invariant affect features,
- better label/task formulation audit,
- train-only representation diagnostics,
- potentially alternative EEG feature extraction design.

Still forbidden unless separately approved:

- DEAP,
- fusion,
- preprocessing rebuild,
- broad model search,
- DG execution,
- augmentation.

## Final Current State

`EXECUTION_PAUSED_PENDING_PROJECT_SYNTHESIS_REVIEW`

## Next State

`REQUEST_PROJECT_SYNTHESIS_REVIEW_AND_FINAL_REGISTRY_UPDATE`
