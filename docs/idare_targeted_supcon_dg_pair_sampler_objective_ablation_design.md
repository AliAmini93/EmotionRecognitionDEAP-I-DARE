# I-DARE Targeted SupCon/DG Pair-Sampler Objective Ablation Design

## Status

Created: `2026-05-08T10:06:00+00:00`

Status: objective created; no training is authorized by this document.

This objective follows:

- `docs/idare_supcon_dg_failure_analysis_report.md`
- `docs/idare_minimal_supcon_dg_first_pass_report.md`
- `docs/idare_subject_variability_supcon_dg_design_spec.md`
- `docs/idare_supcon_dg_failure_analysis_review_status.md`

## Scientific Question

The first SupCon/DG pass failed despite valid smoke tests.

The question is no longer "does SupCon/DG run?"

The question is:

**Which pair definition, negative definition, subject-balanced sampler, and domain-generalization penalty actually targets subject variability rather than adding another weak regularizer?**

## Core Hypothesis

Subject variability remains a plausible blocker, but the first intervention was likely too weak or too broad.

The most likely failure modes are:

1. Positive pairs were label-compatible but not necessarily affect-compatible.
2. Negative pairs may have pushed borderline or rating-similar samples apart.
3. Within-subject pair structure may have reinforced idiosyncratic subject patterns.
4. VREx regularized losses but may not have created subject-invariant embeddings.
5. Hyperparameters were not wrong in a generic sense; they were not tied tightly enough to the pair/sampler mechanism.

## Authorized Scope

This objective authorizes design/spec work only:

- define targeted SupCon/DG pair-sampler ablation candidates
- define positive-pair policies
- define negative-pair policies
- define batch sampler constraints
- define minimal hyperparameter registry
- define smoke tests required before any new training
- define decision rules for interpreting the next small ablation

## Not Authorized

- direct full SupCon/DG training
- broad hyperparameter search
- EEG+EMG fusion
- final LOSO claim
- mainline change

## Required Ablation Design Matrix

The implementation-ready candidate matrix is stored in:

`docs/idare_targeted_supcon_dg_pair_sampler_ablation_design_matrix.csv`

Required candidate families:

1. CE control
2. label-only SupCon
3. cross-subject-positive-only SupCon
4. within-subject anchor + cross-subject positive SupCon
5. rating-distance-guarded SupCon
6. cross-subject SupCon + VREx
7. VREx-only recheck
8. subject-adversarial design-only candidate, not first-pass training

## Positive Pair Design Rules

Candidate policies must explicitly state whether positives are:

- same binary label only
- same label and cross-subject only
- same label with rating-distance or quantile-distance guard
- within-subject stable examples plus cross-subject positives
- subject-relative top/bottom quantile aligned

A candidate is invalid if it cannot explain what "positive" means beyond matching the final binary label.

## Negative Pair Design Rules

Candidate policies must explicitly state whether negatives are:

- opposite binary label only
- opposite label plus rating-distance margin
- cross-subject only
- subject-balanced
- forbidden when rating distance is too small

A candidate is invalid if it aggressively pushes borderline affect states apart without an audit.

## Batch Sampler Design Rules

The sampler must satisfy these constraints before training:

- subject-heldout validation subjects are never used in training pairs
- batches contain multiple subjects per class when possible
- no single subject dominates a batch
- each eligible anchor has at least one positive and one negative
- pair coverage is reported by modality, task, fold, and candidate
- sampler failures block training for that candidate

## Hyperparameter Registry

The minimal hyperparameter registry is stored in:

`docs/idare_targeted_supcon_dg_pair_sampler_hyperparameter_registry.csv`

This is not a broad search. It is a constrained registry so that if a future ablation works or fails, the mechanism remains interpretable.

## Required Smoke Tests

The smoke-test plan is stored in:

`docs/idare_targeted_supcon_dg_pair_sampler_smoke_test_plan.csv`

Required tests before any future training:

1. pair coverage
2. leakage guard
3. batch balance
4. rating-distance audit
5. micro-overfit
6. shuffled-label negative control

## Failure Interpretation Decision Tree

The decision tree is stored in:

`docs/idare_targeted_supcon_dg_pair_sampler_decision_tree.csv`

The next ablation must be interpreted according to that tree. In particular:

- If cross-subject positives help, the original pair definition was weak.
- If VREx-only helps, DG regularization may matter more than SupCon.
- If distance-guarded pairs help, the binary labels are too noisy for naive supervised contrastive learning.
- If nothing helps and smoke tests are valid, representation/task formulation must be revisited.

## Pass Criteria

This objective passes only if:

- review closeout is created
- the targeted ablation matrix is written
- the pair/sampler hyperparameter registry is written
- smoke tests are defined before training
- decision rules are defined before training
- direct full SupCon/DG training remains blocked

## Next Allowed Step

Prepare a reviewed implementation/run command for the targeted pair/sampler ablation, or generate a more detailed implementation spec if the design is not yet sufficient.

No broad training is allowed before review.
