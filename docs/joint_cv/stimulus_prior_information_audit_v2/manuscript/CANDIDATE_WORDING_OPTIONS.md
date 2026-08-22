# Candidate Wording Options

**These are drafting inputs, not final manuscript prose.** Nothing here is
registered, frozen, or approved. Numbers are from
`derived/STIMULUS_PRIOR_SUMMARY.csv` and `derived/STIMULUS_OVERLAP_BY_FOLD.csv`
at candidate v1.

## Terminology constraints observed throughout

Per the frozen storyline authority, the following are used:
*stimulus overlap*, *canonical-stimulus reuse*, *stimulus-associated prior
information*, *subject-only evaluation leaves stimulus novelty uncontrolled*.

The following are **avoided**: "data leakage", "leakage", "contamination",
"cheating", "invalid evaluation", and any phrasing implying cross-subject
evaluation is inherently wrong.

---

## Option 1 — Minimal, structural only (1 sentence)

> In DEAP and I-DARE every participant is presented with the same canonical
> stimulus set, so under subject-only cross-validation the canonical-stimulus
> overlap between the source and held-out sides is complete (1.000), and stimulus
> novelty is therefore left uncontrolled.

*Use when:* space is tight and the predictive claim is made elsewhere.
*Strength:* essentially unattackable — a counting argument.
*Weakness:* establishes reuse but not that reuse matters.

---

## Option 2 — Recommended pair (2 sentences)

> In DEAP and I-DARE the canonical stimulus set is shared across all participants,
> so subject-only cross-validation yields complete canonical-stimulus overlap
> (1.000 of held-out trials, with a median of 31 and 56 source participants per
> held-out stimulus respectively). A predictor given only the canonical stimulus
> identity, with stimulus-conditioned label tendencies estimated from source
> participants alone, then reaches 0.74 and 0.62 balanced accuracy on DEAP
> Valence and Arousal and 0.96 and 0.79 on I-DARE, against a source-only
> no-stimulus baseline of 0.50 — indicating that stimulus-associated prior
> information is available on the source side even though stimulus identity is
> not an explicit model input.

*Use when:* this is the primary G1 evidence sentence. **Recommended default.**

---

## Option 3 — With the information-theoretic quantity (3 sentences)

> Option 2, followed by:
>
> Expressed as predictive information, the same stimulus-only predictor supplies
> 0.29 and 0.07 bits per trial on DEAP Valence and Arousal and 0.79 and 0.30 bits
> per trial on I-DARE, with the **primary fixed-prediction** participant-clustered
> bootstrap intervals excluding zero in all four cases. The refit-bootstrap
> sensitivity interval for DEAP Arousal includes zero, so this statement should
> not be used without that qualification.

*Use when:* a reviewer is likely to ask whether the balanced-accuracy gain is
calibration or thresholding luck.

---

## Option 4 — Including the DEJA-VU counter-example (recommended for Discussion)

> The magnitude of this effect is dataset- and task-dependent rather than
> automatic. In DEJA-VU, where each session presents only three of sixteen videos
> and canonical-stimulus overlap is partial (0.95), the same stimulus-only
> predictor reaches 0.80 balanced accuracy for Valence but only 0.53 for Arousal
> — the latter indistinguishable from chance (−0.06 bits per trial, 95% CI
> [−0.23, 0.10], permutation p = 0.20). Canonical-stimulus reuse therefore
> creates the *opportunity* for stimulus-associated prior information without
> guaranteeing it.

*Use when:* the Discussion or Limitations needs to demonstrate that the claim was
tested rather than assumed. **Strongly recommended somewhere in the paper.**

---

## Option 5 — Methodological framing (for the evaluation-protocol section)

> Because canonical elicitors recur across participants, holding out subjects
> controls test-subject overlap but does not control stimulus novelty: a held-out
> participant is evaluated almost entirely on elicitors the source side has
> already observed. Subject-only cross-validation therefore establishes
> generalization across people, not across stimuli, and a joint subject×stimulus
> protocol is required to establish the latter.

*Use when:* motivating the joint CV design rather than reporting a number.

---

## Sentences to avoid

| Do not write | Why |
|---|---|
| "Subject-only cross-validation leaks label information." | Frames reuse as leakage. No trial, subject or window is shared between source and target. |
| "Cross-subject evaluation is invalid." | Contradicted by the storyline authority; cross-subject evaluation is correct for the question it asks. |
| "Stimulus identity determines the label." | Overstated. True only near-ceiling for I-DARE Valence (0.956); false for DEJA-VU Arousal. |
| "Models exploit stimulus identity to inflate cross-subject scores." | Not tested here. This audit measures available structure, not model behaviour. |
| "The stimulus prior explains reported cross-subject performance." | Causal claim; the permutation test licenses association only. |
| "All three datasets show strong stimulus-associated prior information." | False. DEJA-VU Arousal does not. |
| Any Primary-4 average that includes DEJA-VU. | Prohibited by the evaluation contract. |

---

## Number-formatting notes for whichever option is used

* Overlap: 3 decimals (`1.000`, `0.947`) — the exactness of `1.000` is the point.
* Balanced accuracy: 2 decimals in prose, 4 in tables.
* Bits per trial: 2 decimals in prose, 3 in tables; always with the CI.
* Permutation p: report `p < 10⁻⁴` for the five significant conditions (the
  10,000-permutation floor is `1.0×10⁻⁴`); report `p = 0.20` exactly for DEJA-VU
  Arousal.
* Always name the baseline as "source-only no-stimulus (global class prior)
  baseline", never just "chance".
* **Do not quote ΔAUC or ΔMacro-F1** — see `METRIC_RECOMMENDATION.md`.
