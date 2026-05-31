# I-DARE Strict Non-Transductive Normalization / DG Design Objective

## Status

`created`

## Objective ID

`idare_strict_nontransductive_norm_dg_design_objective`

## Scope

This is a Control Tower documentation/design objective only.

Allowed:
- define strict non-transductive normalization for this project.
- distinguish strict non-transductive normalization from W1B B3 transductive rank normalization.
- define scientifically valid normalization / DG candidates without using test-subject statistics.
- define leakage boundaries.
- define evidence required before any future executable objective.
- decide whether W2E interaction-grid should remain a design subsection or become a future objective.

Forbidden:
- no experiments.
- no runner.
- no Wave 2 execution.
- no W2E execution.
- no DEAP.
- no fusion.
- no preprocessing changes.
- no threshold changes.
- no main push.
- no W1A/W1B/W1C/W1D branch-owned file modification.

## Background

Wave 1 is formally closed and accepted.

- W1A: tested EEG input definitions did not rescue pairwise arousal performance.
- W1B: transductive rank transform reduced heterogeneity, but no strict non-transductive pass.
- W1C: EMG ridge aggregate no-pass; keep EMG as independent reference.
- W1D: within-subject signal exists, but cross-subject signal collapses due to subject-dominated geometry.

Therefore, the next decision focus is not execution. The next focus is a rigorous design definition for strict non-transductive normalization and domain-generalization candidates.

## Definition: Strict Non-Transductive Normalization

In this project, strict non-transductive normalization means:

1. All normalization parameters must be estimated using training subjects only.
2. No feature statistics from held-out/test subjects may be used, even if labels are not used.
3. No per-test-subject centering, scaling, ranking, quantile mapping, or distribution fitting is allowed.
4. Any validation-fold statistics must be treated consistently with the fold protocol and must not leak test-subject distribution information.
5. The same learned train-side transform must be applied to held-out subjects without adaptation to their feature distribution.
6. If target-subject unlabeled statistics are used, the method is transductive and must not be reported as strict non-transductive evidence.

## Difference from W1B B3

W1B B3 used per-subject rank transform and reduced heterogeneity, but it used each held-out subject's own unlabeled feature distribution. Therefore:

- B3 is useful diagnostic evidence.
- B3 supports the subject-heterogeneity hypothesis.
- B3 is not strict non-transductive evidence.
- B3 must remain archived as transductive diagnostic-only evidence.

## Valid Candidate Families

Scientifically valid candidates must avoid test-subject statistics.

Candidate families:

1. Train-fold StandardScaler / RobustScaler.
2. Train-fold quantile or rank mapping learned only from training subjects, then applied frozen to held-out subjects.
3. Leave-subject-out domain-invariant feature standardization using training-subject groups only.
4. Group-aware regularization that penalizes subject-specific separability using training subjects only.
5. Domain-adversarial or invariant-risk style objectives using training subjects as domains only.
6. Batch/covariate correction estimated only on training subjects and frozen before held-out evaluation.
7. Feature residualization against subject/domain structure only if learned without held-out subject statistics.

Invalid as strict non-transductive:

- per-test-subject z-score.
- per-test-subject rank transform.
- per-test-subject quantile normalization.
- any target-subject adaptation using unlabeled held-out statistics.
- any normalization fitted jointly on train + test.
- any method that silently uses held-out subject identity distribution at transform-fit time.

## Leakage Boundaries

A method is blocked if it uses:

- held-out/test subject feature means, variances, medians, ranks, quantiles, covariance, PCA, ICA, whitening, or batch statistics.
- held-out/test subject labels.
- held-out/test subject distribution for threshold calibration.
- fold-global statistics that include held-out subject rows.
- preprocessing/cache rebuilds not already validated and approved.

Allowed:

- train-subject-only statistics.
- train-fold-only model fitting.
- validation logic that does not fit transforms on test subjects.
- reporting transductive diagnostics separately, clearly labeled as transductive.

## Evidence Required for Future Executable Objective

A future executable objective may be reviewable only if the design specifies:

1. exact candidate cells,
2. exact train-only fitting rule,
3. exact folds and held-out subject protocol,
4. leakage validation checks,
5. expected outputs and closeout schema,
6. gate criteria without threshold changes,
7. how results compare against Wave 1 references,
8. explicit statement that DEAP/fusion/preprocessing changes remain frozen.

## W2E Interaction-Grid Position

W2E should remain a design subsection for now.

Reason:
- W1A alone did not pass.
- W1B strict non-transductive cells did not pass.
- W1B B3 was diagnostic but transductive.
- The interaction between input definition and strict non-transductive normalization may be worth designing, but execution is not authorized.

W2E can become a future objective only after human review approves a strict non-transductive design.

## Freeze Enforcement

The following remain enforced:

- DEAP frozen.
- fusion frozen.
- preprocessing changes forbidden.
- rereference/CAR forbidden.
- downsampling rebuild forbidden.
- threshold changes forbidden unless explicitly approved by human review.
- main push from branch chats forbidden.
- Wave 2 execution not authorized by this document.

## Next State

After this objective is committed, the next state is:

`REQUEST_STRICT_NTD_NORM_DG_DESIGN_REVIEW`
