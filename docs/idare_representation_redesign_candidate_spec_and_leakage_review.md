# I-DARE Representation Redesign Candidate Spec and Leakage Review

## Status

`created`

## Scope

Control Tower documentation/design/leakage review only.

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

## Purpose

Define the smallest actionable representation-redesign candidate set before either:

1. creating a future smoke authorization package, or
2. stopping/pivoting.

This is not a broad roadmap.

## Candidate Families

| Cell | Candidate | Status | Rationale |
|---|---|---|---|
| R0 | current representation anchor | required anchor | Needed for direct comparison. |
| R1 | train-only subject-residualized features | low-risk future smoke candidate | Directly targets subject-dominated geometry using training subjects only. |
| R2 | train-only subject-invariant feature selection | low-risk future smoke candidate | Selects features with lower subject dominance and retained label signal using training subjects only. |
| R3 | diagnostics-first representation quality filter / stable-feature subset | low-risk future smoke candidate | Uses train-only diagnostics to keep stable, less subject-dominated features. |
| R4 | temporal/spectral redesign candidate | deferred | Only reviewable later if it does not blindly repeat failed PATCH_A. |

## Leakage Boundaries

All future representation candidates must obey:

- all statistics fit only on training subjects
- no held-out/test-subject feature statistics
- no target adaptation
- no global all-subject feature selection
- no test-label use
- no threshold tuning on held-out subjects
- no preprocessing/cache rebuild
- no DEAP or fusion
- no W1 branch-owned file edits

## Risk Classification

| Candidate | Risk | Decision |
|---|---|---|
| R0 current anchor | low | include |
| R1 train-only subject-residualized features | low/medium | include in future smoke design |
| R2 train-only subject-invariant feature selection | low/medium | include in future smoke design |
| R3 diagnostics-first stable-feature subset | low | include in future smoke design |
| R4 temporal/spectral redesign | medium/high | defer |
| DG execution | high | defer until better representation exists |
| model-capacity probe | high | defer |
| augmentation | high | defer |
| fusion | out of scope | forbidden |
| DEAP | out of scope | frozen |
| per-test-subject adaptation | invalid/transductive | forbidden |
| global feature selection across all subjects | invalid/leaky | forbidden |

## Minimum Future Smoke Matrix

A smallest defensible future smoke should use no more than 4 cells x 6 folds:

| Cell | Description |
|---|---|
| R0 | current representation anchor |
| R1 | train-only subject-residualized features |
| R2 | train-only subject-invariant feature selection |
| R3 | train-only diagnostics-first stable-feature subset |

Recommended scope, if later authorized:
- I-DARE only
- EEG-first
- arousal-only
- pairwise formulation
- ridge fixed unless separately reviewed
- 4 cells x 6 folds = 24 runs maximum

## Comparison References

Future results must compare against:

- `REF-PW-EEG-ARO-001`
- W1A input-definition no-pass
- W1B heterogeneity diagnostic
- W1D subject-dominance diagnosis
- Strict NTD clean weak-effect smoke
- majority baseline

## Stop Criteria

Archive representation redesign if:

- R1/R2/R3 fail to improve meaningfully over R0
- subject separability remains dominant without label-separability gain
- gains appear only through transductive/leaky transforms
- no candidate approaches unchanged moderate gate
- diagnostics show the redesigned representation is unstable across folds

Consider DG design only if:

- at least one representation candidate improves geometry or performance enough to justify domain-focused modeling
- leakage boundaries remain clean
- Control Tower explicitly authorizes a DG design step

Stop/pivot if:

- representation redesign remains weak
- DG would only add complexity without better features
- further small smokes are unlikely to change the conclusion

## DG Position

DG remains secondary until a better representation candidate exists.

DG execution is not authorized.

## Current Ruling

No execution is authorized by this review.

## Next Decision

After this review, Control Tower should choose exactly one:

1. create a representation redesign smoke authorization package, or
2. stop/pivot.
