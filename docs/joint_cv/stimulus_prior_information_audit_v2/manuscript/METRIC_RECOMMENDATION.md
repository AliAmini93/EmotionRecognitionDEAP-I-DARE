# Metric Recommendation for the G1 Claim

Candidate planning document. Not manuscript prose.

## What G1 needs to establish

> Subject-only cross-validation correctly controls test-subject overlap, but when
> canonical elicitors are reused across participants it does not establish
> generalization to unseen stimuli. The source side can contain
> stimulus-associated prior information even when stimulus ID is not an explicit
> model input.

That is two separable assertions:

* **(i) reuse happens** — held-out subjects are evaluated on elicitors the source
  side already contains; and
* **(ii) reuse is informative** — that reuse carries label-relevant information
  about a *new* participant.

A reviewer can reject the claim by attacking either. The recommended metric pair
answers exactly one each, and nothing more.

---

## Recommendation

### Preferred minimal pair

**1. Structural canonical-stimulus overlap fraction** (Analysis A)

DEAP 1.000, I-DARE 1.000, DEJA-VU 0.947 (Valence) / 0.958 (Arousal).

* Answers (i) directly and completely.
* No model, no estimator, no smoothing, no seed — it is a counting argument over
  the frozen trial tables, so there is nothing for a reviewer to dispute except
  the canonical stimulus mapping itself, which is already a frozen repository
  authority.
* Immune to class imbalance by construction.
* Comparable across all three datasets on the same 0–1 scale.
* Carries the strongest single sentence in the audit: for DEAP and I-DARE **not
  one trial** of **any** held-out subject uses a stimulus absent from the source
  set, and each is backed by a median of 31 and 56 source participants
  respectively.

**2. Cross-validated stimulus-ID-only balanced accuracy against a source-only
no-stimulus baseline** (Analysis B)

DEAP V 0.739 / A 0.619; I-DARE V 0.956 / A 0.786; DEJA-VU V 0.803 / A 0.531;
baseline 0.500 in all Primary conditions.

* Answers (ii) in the units a T-AFFC reviewer already reads emotion-recognition
  results in.
* Balanced accuracy is the right choice over accuracy here because the retained
  class balance ranges from 0.29 to 0.58 HIGH across conditions; plain accuracy
  would flatter the imbalanced conditions.
* The comparator is principled: a source-only global class prior, so the
  contrast isolates *stimulus identity* rather than *class prevalence*.
* The baseline sits at exactly 0.500 in the four Primary conditions, so the
  effect size reads off directly.

### Optional supplementary metric

**3. Cross-validated bits per trial** (log-loss gain ÷ ln 2)

DEAP V 0.289 / A 0.069; I-DARE V 0.794 / A 0.303; DEJA-VU V 0.423 / A **−0.057**.

If quoting an interval alongside it, note that DEAP Arousal's bootstrap interval
is variant-sensitive (spans zero under the refit variant); for that condition cite
the permutation p-value instead. See `REPORT.md` §C.

Include this if space allows, for three reasons:

* It is the only metric in the set that makes the **DEJA-VU Arousal null legible
  as a null**. Balanced accuracy reports 0.531 there, which a skimming reader may
  round up to "slightly positive"; −0.057 bits/trial with a CI spanning zero is
  unambiguous.
* It is a proper scoring rule, so it rewards calibration rather than just
  thresholded ranking — a reviewer asking "is the prior actually *informative* or
  just luckily thresholded?" is answered by this number.
* It is the honest counterpart to the plug-in mutual information. The audit shows
  plug-in MI overstates the effect in every condition (most starkly 0.219 vs
  −0.057 for DEJA-VU Arousal), so quoting the cross-validated version pre-empts
  the obvious methodological objection.

---

## What NOT to use, and why

| Metric | Why not |
|---|---|
| **ΔAUC** | Degenerate. Under leave-one-participant-out the source global prior for participant *p* excludes *p*'s labels, so high-prevalence participants get a systematically lower constant score. The baseline is anti-correlated with the target **by construction** (global AUC 0.07–0.42), inflating ΔAUC. Quote the stimulus-prior AUC alone if an AUC is wanted at all. |
| **ΔMacro-F1** | Partly degenerate for the same reason: a constant-probability baseline scores F1 = 0 on one class, so the global macro-F1 (0.32–0.41) reflects the comparator's degeneracy rather than the stimulus effect. |
| **Plug-in mutual information I(Y;S)** | Finite-sample biased upward in every condition. Descriptive only; would invert the DEJA-VU Arousal conclusion if quoted naively. |
| **Accuracy** | Not imbalance-resistant across a 0.29–0.58 prevalence range. |
| **DEJA-VU Arousal ΔBA (+9.69 pp)** | Measured against a global BA of 0.434, not 0.500. Reporting it as a gain would misrepresent a null as a positive result. |
| **Any Primary-4 average including DEJA-VU** | Prohibited by the evaluation contract; DEJA-VU is external validation. A Primary-4 macro over DEAP+I-DARE only is available (BA 0.775, 0.364 bits/trial, overlap 1.000). |
| **Continuous rating prior (Analysis D)** | Secondary/descriptive only. It corroborates but does not redefine the binary Paper-2 task. |

---

## Exact caveats that must travel with whichever metrics are used

1. Stimulus identity is **not** an explicit MM-SAGE-DG model input. These numbers
   quantify *available* structure, not model behaviour.
2. A positive stimulus prior does **not** prove any trained model exploits it.
3. Canonical-stimulus reuse is **not** sample or trial leakage. No trial, subject
   or window is shared between source and target in any analysis here.
4. The permutation test is an association test, not a causal test.
5. Overlap fractions reflect experimental schedules and are not a quality ranking
   of the datasets.
6. DEJA-VU's intervals are wide (75 / 71 retained trials, 24 participants); its
   point estimates should not be over-read.
7. The effect is **task- and dataset-dependent and is absent for DEJA-VU
   Arousal**. Any G1 sentence must be scoped accordingly.

---

## Bottom line

Use **overlap fraction + stimulus-only balanced accuracy vs a source-only
no-stimulus baseline** as the minimal pair, and add **bits per trial** if a
third number can be afforded. Report DEJA-VU Arousal as a null in the same
sentence or table row, not in a footnote — it is the condition that makes the
claim credible rather than convenient.
