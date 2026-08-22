# Candidate G1 Evidence Summary

Candidate planning document. **Not manuscript prose, not frozen, not registered.**

## The G1 claim under test

> Subject-only cross-validation correctly controls test-subject overlap, but when
> canonical elicitors are reused across participants it does not establish
> generalization to unseen stimuli. The source side can contain
> stimulus-associated prior information even when stimulus ID is not an explicit
> model input.

## Verdict

**Supported for DEAP and I-DARE, both tasks. Supported for DEJA-VU Valence.
NOT supported for DEJA-VU Arousal.**

The claim survives, but it must be stated as conditional rather than universal.

## Evidence table (the two recommended metrics)

| Dataset | Task | Canonical-stimulus overlap | Stimulus-only BA | No-stimulus baseline BA | Bits/trial [95% CI] | Permutation p |
|---|---|---:|---:|---:|---|---:|
| DEAP | Valence | **1.000** | 0.739 | 0.500 | 0.289 [0.198, 0.365] | 1.0×10⁻⁴ |
| DEAP | Arousal | **1.000** | 0.619 | 0.500 | 0.069 [0.020, 0.118] \* | 1.0×10⁻⁴ |
| I-DARE | Valence | **1.000** | 0.956 | 0.500 | 0.794 [0.751, 0.833] | 1.0×10⁻⁴ |
| I-DARE | Arousal | **1.000** | 0.786 | 0.500 | 0.303 [0.234, 0.366] | 1.0×10⁻⁴ |
| DEJA-VU | Valence | 0.947 | 0.803 | 0.500 | 0.423 [0.272, 0.567] | 1.0×10⁻⁴ |
| DEJA-VU | Arousal | 0.958 | 0.531 | 0.434 | **−0.057 [−0.234, 0.104]** | **0.204** |

\* DEAP Arousal is the one condition whose bootstrap interval is variant-sensitive:
it spans zero under the refit bootstrap ([−0.006, 0.101]). Cite the permutation
result (p = 1.0×10⁻⁴) for that condition, not the interval. All other conditions
are stable under both variants.

View A (leave-one-participant-out), pooled out-of-fold. DEJA-VU is external
validation and is never pooled with the Primary datasets. Primary-4 macro
(DEAP + I-DARE only): overlap 1.000, BA 0.775 vs 0.500, 0.364 bits/trial.

## What each half of the claim rests on

**"canonical elicitors are reused across participants"** — DEAP and I-DARE are
fully crossed designs (32×40 = 1280 and 63×32 = 2016 trials, zero duplicate
participant×stimulus pairs). Under *any* subject-only split, every held-out trial
uses a source-seen stimulus, backed by a median of 31 (DEAP) and 56–57 (I-DARE)
source participants. Overlap is exactly 1.000 in all 32 and all 63 LOPO folds and
in all three project subject folds. There is no unseen-stimulus fallback anywhere
in either Primary dataset.

**"the source side can contain stimulus-associated prior information"** — a
predictor given *only* the canonical stimulus ID, with the stimulus→label tendency
estimated from source participants alone, beats the best source-only no-stimulus
baseline in five of six conditions, by 11.9 to 45.6 balanced-accuracy points and
0.069 to 0.794 bits per trial. All five sit at the 10,000-permutation floor
(p = 1.0×10⁻⁴), and four of the five also have participant-clustered bootstrap CIs
excluding zero under **both** bootstrap variants; DEAP Arousal is the exception,
where the interval spans zero under the refit variant and the permutation result
carries the claim.

**"even when stimulus ID is not an explicit model input"** — this audit does not
and cannot test what a trained model does. It establishes that the information is
*present and reachable* from the source side. The manuscript must say exactly
that and no more.

## The counter-example that must be reported

**DEJA-VU Arousal.** Stimulus-only BA 0.531 (chance), AUC 0.520, and a *negative*
0.057 bits per trial. The bootstrap CI spans zero, the permutation p-value is
0.204, the gain is negative in all five fold repetitions, and the independent
continuous-rating analysis also fails to beat the global mean (RMSE 1.986 vs
1.906, R² = −0.14, r = 0.02).

This is not a weak positive — it is a null, and it is scientifically load-bearing:

* It demonstrates that the stimulus prior is a **measurable empirical property of
  a dataset–task pair**, not an inevitability of shared elicitors. Structural
  overlap of 0.958 coexists with zero usable label information.
* It pre-empts the strongest reviewer objection ("you would find this everywhere,
  so it means nothing").
* It separates the two halves of G1 cleanly: reuse can be near-total and still
  uninformative.

## Consequence for the frozen storyline

The frozen G1 storyline is **not** contradicted, but one edit is required: it must
not be phrased as a universal property of canonical-stimulus reuse. The defensible
form is that reuse *can* leave stimulus-associated prior information on the source
side, that in DEAP and I-DARE it demonstrably does and overlap is complete, and
that the magnitude is dataset- and task-dependent — with DEJA-VU Arousal as the
worked counter-example.

Candidate sentences are in `CANDIDATE_WORDING_OPTIONS.md`.

## Confidence and its limits

Strong on the structural claim (arithmetic over frozen authorities; the DEAP
overlap = 1.0 result independently reproduces a prior frozen artefact).

Strong on the Primary predictive claim (large N, permutation floor, View A and
View B agree, and I-DARE Arousal BA reproduces a prior independent artefact to
0.001) — with the single qualification that DEAP Arousal, the weakest positive
condition, has a bootstrap interval that is sensitive to the bootstrap variant.

Moderate on DEJA-VU, in both directions — 75 and 71 retained trials over 24
participants give wide intervals. The Valence effect is nonetheless stable across
all five fold repetitions, and the Arousal null is negative in all five.

Nothing here licenses a statement about what MM-SAGE-DG or any baseline model
actually learns.
