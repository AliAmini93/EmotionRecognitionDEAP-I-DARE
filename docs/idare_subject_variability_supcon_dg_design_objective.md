# I-DARE Cautious Subject-variability SupCon/DG Design Objective

## Status

Short-term design objective created.

No SupCon/DG training is authorized by this document.

Generated UTC: `2026-05-08T09:24:04.815694+00:00`

## Why This Objective Exists

The subject-variability intervention-failure analysis concluded:

- `subject_variability_diagnosis_still_supported_intervention_too_weak`

The failed subject-relative + preprocessing intervention was judged too weak/incomplete, not proof that subject variability is irrelevant.

The next method must directly target subject variability.

SupCon and domain generalization are plausible because they can directly target cross-subject representation mismatch, but only if the design is precise and staged.

## Scientific Question

How should SupCon and/or domain-generalization losses be designed, staged, smoke-tested, and interpreted so the next controlled run directly targets subject variability and remains scientifically diagnosable?

## Core Principle

Do not jump directly to a performance run.

First lock:

- assumptions;
- pair definitions;
- sampler guarantees;
- smoke tests;
- hyperparameter registry;
- staged run matrix;
- failure interpretation rules.

## Authorized Work

Read-only design/spec work.

This objective authorizes:

1. Searching project docs and scripts for existing SupCon/DG notes.
2. Summarizing the intended implementation.
3. Locking positive-pair, negative-pair, and hard-negative definitions.
4. Locking subject-aware sampler requirements.
5. Locking VREx/domain environment definitions.
6. Creating smoke-test gates.
7. Creating a small staged hyperparameter registry.
8. Creating a minimal first-pass run matrix.

No new model training is authorized.

## Design Decisions to Lock

### 1. Task formulation

Decide whether the first pass should use subject-relative q33 labels, and justify the choice.

### 2. Positive pairs

Define valid positives.

Minimum expected principle:

- same task
- same class
- cross-subject preferred/required when feasible

### 3. Negative pairs

Define valid negatives.

Minimum expected principle:

- same task
- opposite class
- hard negatives should be considered if same-stimulus/different-label or same-subject/opposite-class cases are available.

### 4. Sampler

Define a sampler that makes SupCon batches valid.

It should specify:

- minimum subjects per batch
- minimum samples per class
- whether each anchor must have at least one positive
- fallback behavior when a fold/task lacks enough positives
- logging for anchors without positives
- batch subject/class distribution diagnostics

### 5. Domain generalization

Define environment.

Expected default:

- subject ID as domain/environment

Alternative definitions must be justified.

### 6. Loss and schedule

Choose one first-pass setup:

- CE + SupCon
- CE + VREx/DG
- CE + SupCon + VREx/DG

Specify weights, warmup, and when each loss is active.

### 7. Hyperparameter registry

Define candidate values before any run.

Initial registry to refine:

- SupCon temperature tau: `0.07`, `0.1`, `0.2`
- SupCon weight: `0.05`, `0.1`, `0.2`, `0.5`
- VREx/DG weight: `0.01`, `0.05`, `0.1`
- projection dimension: `32`, `64`, `128`
- warmup epochs: `0`, `3`, `5`
- batch policy: largest valid subject/class-balanced batch first

The first pass must not be a full Cartesian grid.

### 8. Smoke tests

Before any full training run, define and require:

1. pair sampler integrity smoke;
2. leakage guard smoke;
3. SupCon micro-overfit smoke;
4. shuffled-label negative control;
5. one-fold/one-task minimal smoke.

### 9. Evaluation

Keep first pass minimal and diagnostic.

Metrics must include:

- macro-F1
- balanced accuracy
- one-class prediction flag
- environment risk variance
- same-class cross-subject embedding distance
- different-class cross-subject embedding distance
- positive-pair coverage
- anchors without positives
- CE/SupCon/VREx loss components

### 10. Failure interpretation

The design spec must explain what to conclude if:

- smoke tests fail;
- SupCon loss decreases but validation macro-F1 does not improve;
- embeddings align but task performance remains near chance;
- VREx reduces risk variance but not performance;
- only one modality/task improves;
- improvement appears only under one temperature/loss-weight combination.

## Expected Outputs

- `docs/idare_subject_variability_supcon_dg_design_spec.md`
- `docs/idare_subject_variability_supcon_dg_design_spec.json`
- `docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv`
- `docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv`
- `docs/idare_subject_variability_supcon_dg_smoke_test_plan.csv`
- `docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv`

## Pass Criteria

The design passes only if it:

1. Reviews existing project SupCon/DG notes.
2. Defines positive/negative/hard-negative pairs.
3. Defines subject-aware sampler constraints.
4. Defines smoke tests before training.
5. Defines a small staged hyperparameter plan.
6. Defines VREx/DG environment rules.
7. Defines leakage controls.
8. Defines minimal first-pass run matrix.
9. Includes failure-interpretation logic.
10. Avoids training and performance claims.
11. Updates the central roadmap.

## Not Authorized

- SupCon/DG training
- EEG+EMG fusion
- final LOSO / final paper claim
- mainline change
- architecture/augmentation work
- broad hyperparameter search

## Next Allowed Step

Search/read existing project docs and scripts, then generate the cautious SupCon/DG design spec with smoke tests and hyperparameter registry.
