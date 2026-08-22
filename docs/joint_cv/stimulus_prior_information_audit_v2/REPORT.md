# Stimulus-Associated Prior Information Audit — REPORT (candidate v1)

**Status:** CANDIDATE ANALYSIS. Not frozen, not committed, not manuscript prose.
**Date:** 2026-08-22
**Root audit seed:** `20260822`
**Audit status:** `PASS` (source-only leakage suite: 16/16 assertions PASS, of which
12 are independent computations, 3 restate one computation and 1 is a code-inspection
assertion; all 12 derived artefacts bitwise identical across two independent processes)

Question answered: *when participants are held out but stimuli are not, how much
information about a held-out participant's binary Valence/Arousal label is
recoverable from the identity of the eliciting stimulus alone, using source
participants' labels only?*

Everything below was recomputed from authoritative dataset metadata and labels.
No previously derived project number was used as an input. Comparison with prior
project claims is in Section E and was performed only after the fresh results
were written to disk.

---

## A. Executive answer

| Dataset | Task | Stimulus prior carries source-derived predictive information? | How large | How certain | Canonical-stimulus overlap |
|---|---|---|---|---|---|
| DEAP | Valence | **Yes** | BA 0.739 vs 0.500; 0.289 bits/trial | 95% CI [0.198, 0.365] bits; permutation p = 1.0×10⁻⁴ | **Complete (1.000)** |
| DEAP | Arousal | **Yes, but modest** | BA 0.619 vs 0.500; 0.069 bits/trial | 95% CI [0.020, 0.118] bits (spans zero under the refit variant — rely on p = 1.0×10⁻⁴) | **Complete (1.000)** |
| I-DARE | Valence | **Yes, very strong** | BA 0.956 vs 0.500; 0.794 bits/trial | 95% CI [0.751, 0.833] bits; p = 1.0×10⁻⁴ | **Complete (1.000)** |
| I-DARE | Arousal | **Yes, strong** | BA 0.786 vs 0.500; 0.303 bits/trial | 95% CI [0.234, 0.366] bits; p = 1.0×10⁻⁴ | **Complete (1.000)** |
| DEJA-VU | Valence | **Yes, strong** | BA 0.803 vs 0.500; 0.423 bits/trial | 95% CI [0.272, 0.567] bits; p = 1.0×10⁻⁴ | **Partial (0.947)** |
| DEJA-VU | Arousal | **No — null / slightly negative** | BA 0.531 vs 0.434; **−0.057 bits/trial** | 95% CI [**−0.234, 0.104**] bits (spans zero); **p = 0.204** | **Partial (0.958)** |

`p = 1.0×10⁻⁴` is the smallest attainable value with 10,000 permutations
(`(0+1)/(10000+1)`); it means no permutation of 10,000 reached the observed value.

**Headline finding.** In five of six dataset–task conditions, knowing only *which
stimulus was shown* — with the stimulus→label tendency estimated exclusively from
other participants — predicts a new participant's label substantially better than
the best source-only no-stimulus baseline. The sixth condition, DEJA-VU Arousal,
shows **no** such information and is preserved as a negative result.

**Second finding.** For DEAP and I-DARE, canonical-stimulus overlap under
subject-only splitting is **exactly complete**: every trial of every held-out
subject uses a stimulus that appears in the source set, supported by a median of
31 (DEAP) and 56–57 (I-DARE) source participants. There is no unseen-stimulus
fallback anywhere. DEJA-VU is the only dataset where overlap is partial.

---

## B. Structural stimulus overlap (Analysis A)

View A = leave-one-participant-out. Trial-weighted overlap = fraction of retained
target trials whose canonical stimulus also occurs in the source set.

| Dataset | Task | Held-out units | Trial-weighted overlap (mean / min) | Unique-stimulus overlap (mean / min) | Fallback trials | Source participants per target stimulus (min / median / max) |
|---|---|---|---|---|---|---|
| DEAP | Valence | 32 | **1.000 / 1.000** | **1.000 / 1.000** | **0 / 1264** | 29 / 31 / 31 |
| DEAP | Arousal | 32 | **1.000 / 1.000** | **1.000 / 1.000** | **0 / 1263** | 28 / 31 / 31 |
| I-DARE | Valence | 63 | **1.000 / 1.000** | **1.000 / 1.000** | **0 / 1667** | 24 / 57 / 62 |
| I-DARE | Arousal | 63 | **1.000 / 1.000** | **1.000 / 1.000** | **0 / 1799** | 48 / 56 / 62 |
| DEJA-VU | Valence | 24 | 0.967 / 0.600 | 0.967 / 0.600 | 4 / 75 | 0 / 6 / 9 |
| DEJA-VU | Arousal | 24 | 0.972 / 0.667 | 0.972 / 0.667 | 3 / 71 | 0 / 5 / 8 |

Pooled over all held-out predictions, the trial-weighted overlap is 1.000 for
DEAP and I-DARE (both tasks), 0.947 for DEJA-VU Valence and 0.958 for DEJA-VU
Arousal.

Under the project's own subject folds (View B, 3 folds), DEAP and I-DARE remain at
1.000. DEJA-VU drops slightly — pooled trial-weighted overlap 0.920 (Valence) and
0.930 (Arousal) at the primary repetition — because larger held-out blocks strand
more single-participant videos. All overlap figures quoted in this report are
**pooled trial-weighted** (total non-fallback trials / total target trials); the
per-fold unweighted mean is a different estimator and is not used here, though
both can be recomputed from `derived/STIMULUS_OVERLAP_BY_FOLD.csv`.

DEAP and I-DARE are **fully crossed** designs — every participant sees every
canonical stimulus exactly once (32×40 = 1280; 63×32 = 2016, zero duplicate
participant×stimulus pairs). Complete overlap under any subject-only split is
therefore a structural property of the datasets, not an artefact of one split.

---

## C. Predictive stimulus prior (Analysis B) — View A, pooled out-of-fold

| Dataset | Task | N | Stim BA | Global BA | ΔBA (pp) | Stim macro-F1 | Stim AUC | Stim log loss | Global log loss | Log-loss gain | Bits/trial | Brier gain |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DEAP | Valence | 1264 | 0.7395 | 0.5000 | +23.95 | 0.7389 | 0.8372 | 0.4868 | 0.6870 | 0.2002 | **0.2889** | 0.0918 |
| DEAP | Arousal | 1263 | 0.6190 | 0.5000 | +11.90 | 0.6191 | 0.6653 | 0.6344 | 0.6824 | 0.0480 | **0.0693** | 0.0244 |
| I-DARE | Valence | 1667 | 0.9559 | 0.5000 | +45.59 | 0.9561 | 0.9813 | 0.1429 | 0.6931 | 0.5502 | **0.7938** | 0.2125 |
| I-DARE | Arousal | 1799 | 0.7861 | 0.5000 | +28.61 | 0.7953 | 0.8380 | 0.4575 | 0.6676 | 0.2101 | **0.3031** | 0.0937 |
| DEJA-VU | Valence | 75 | 0.8032 | 0.5000 | +30.32 | 0.8154 | 0.9224 | 0.3239 | 0.6175 | 0.2935 | **0.4234** | 0.1129 |
| DEJA-VU | Arousal | 71 | 0.5311 | 0.4342 | +9.69 | 0.5061 | 0.5199 | 0.7630 | 0.7233 | −0.0396 | **−0.0572** | −0.0044 |
| *Primary-4 macro (DEAP+I-DARE only)* | — | — | *0.7751* | *0.5000* | *+27.51* | *0.7774* | *0.8305* | *0.4304* | *0.6825* | *0.2521* | *0.3638* | *0.1056* |

DEJA-VU is **not** included in the Primary-4 macro; it remains external validation.

### Uncertainty (participant-clustered bootstrap, 10,000 replicates) and permutation null (10,000 permutations)

| Dataset | Task | Stim BA 95% CI | ΔBA pp 95% CI | Bits/trial 95% CI | Permutation p (bits/trial) | Permutation p (ΔBA) |
|---|---|---|---|---|---:|---:|
| DEAP | Valence | [0.706, 0.769] | [20.57, 26.93] | [0.198, 0.365] | 1.0×10⁻⁴ | 1.0×10⁻⁴ |
| DEAP | Arousal | [0.582, 0.659] | [8.15, 15.87] | [0.020, 0.118] | 1.0×10⁻⁴ | 1.0×10⁻⁴ |
| I-DARE | Valence | [0.943, 0.968] | [44.33, 46.78] | [0.751, 0.833] | 1.0×10⁻⁴ | 1.0×10⁻⁴ |
| I-DARE | Arousal | [0.756, 0.817] | [25.65, 31.67] | [0.234, 0.366] | 1.0×10⁻⁴ | 1.0×10⁻⁴ |
| DEJA-VU | Valence | [0.687, 0.922] | [18.71, 42.19] | [0.272, 0.567] | 1.0×10⁻⁴ | 2.0×10⁻⁴ |
| DEJA-VU | Arousal | [0.449, 0.621] | [**−1.66**, 21.84] | [**−0.234**, 0.104] | **0.2036** | **0.1939** |

Zero invalid bootstrap replicates in all six conditions (no resample was
single-class). The permutation null is centred slightly **below** zero
(mean −0.011 to −0.092 bits/trial), which is the expected finite-sample penalty
for estimating a stimulus-conditioned prior that carries no real signal.

### Bootstrap variant sensitivity — one interval is not robust

The primary interval above holds the out-of-fold probabilities **fixed** while
resampling the participants that produced them. It therefore propagates
evaluation-set sampling variability but **not** the estimation variability of the
source-side prior, and understates total uncertainty. A sensitivity variant
refits the leave-one-participant-out prior *inside* each resample (all duplicate
copies of a participant held out together, so no copy is ever in its own source
set). That variant is itself conservative — a resample holds only ~63% distinct
participants, so its prior is estimated from fewer effective sources — so the two
bracket the truth.

| Dataset | Task | Bits/trial — primary | Bits/trial — refit sensitivity | Width ratio |
|---|---|---|---|---:|
| DEAP | Valence | [0.198, 0.365] | [0.164, 0.355] | 1.14 |
| DEAP | Arousal | [0.020, 0.118] | [**−0.006**, 0.101] | 1.10 |
| I-DARE | Valence | [0.751, 0.833] | [0.740, 0.832] | 1.12 |
| I-DARE | Arousal | [0.234, 0.366] | [0.222, 0.358] | 1.04 |
| DEJA-VU | Valence | [0.272, 0.567] | [0.168, 0.580] | 1.40 |
| DEJA-VU | Arousal | [−0.234, 0.104] | [−0.433, 0.128] | 1.66 |

**Consequence.** Five of six conclusions are unchanged. The exception is **DEAP
Arousal**, whose bits/trial interval excludes zero under the primary variant but
**spans zero under the refit variant**. That specific significance claim should
therefore rest on the permutation test (p = 1.0×10⁻⁴), which is better powered
and is unaffected by this choice — not on the bootstrap interval. DEJA-VU Arousal
remains a null under both variants, and the other four remain clearly positive
under both.

### Two comparators that must NOT be headlined

Two columns in the derived CSVs are degenerate by construction and are reported
only for completeness:

* **Global-prior AUC / ΔAUC.** Under leave-one-participant-out the source global
  prior for participant *p* excludes *p*'s own labels, so a high-prevalence
  participant receives a systematically *lower* constant score. The global-prior
  "ranking" is therefore anti-correlated with the target by construction, giving
  global AUC values of 0.07–0.42 and inflating ΔAUC. **Use the stimulus-prior AUC
  on its own; do not use ΔAUC.**
* **DEJA-VU Arousal ΔBA = +9.69 pp** is measured against a global-prior BA of
  0.434 rather than 0.500, for the same reason. The honest statement is that the
  stimulus-prior BA is **0.531**, i.e. essentially chance — which is what the
  bits/trial, the bootstrap CI and the permutation test all independently say.

### View B — project-aligned subject-fold counterpart

| Dataset | Task | Rep | N | Stim BA | ΔBA pp | Stim AUC | Bits/trial | Overlap |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| DEAP | Valence | 0 | 1264 | 0.7709 | +27.09 | 0.8354 | 0.2642 | 1.000 |
| DEAP | Arousal | 0 | 1263 | 0.6401 | +14.01 | 0.6815 | 0.0707 | 1.000 |
| I-DARE | Valence | 0 | 1667 | 0.9559 | +45.59 | 0.9831 | 0.7950 | 1.000 |
| I-DARE | Arousal | 0 | 1799 | 0.7861 | +28.61 | 0.8416 | 0.2903 | 1.000 |
| DEJA-VU | Valence | 0 (primary) | 75 | 0.8259 | +32.59 | 0.9322 | 0.4000 | 0.920 |
| DEJA-VU | Valence | 1–4 (sensitivity) | 75 | 0.777 – 0.822 | +27.7 … +32.2 | 0.869 – 0.938 | 0.354 – 0.427 | 0.920–0.947 |
| DEJA-VU | Arousal | 0 (primary) | 71 | 0.4502 | +10.93 | 0.4290 | **−0.1774** | 0.930 |
| DEJA-VU | Arousal | 1–4 (sensitivity) | 71 | 0.492 – 0.579 | +5.5 … +15.0 | 0.513 – 0.600 | **−0.013 … −0.120** | 0.930–0.958 |

View B reproduces View A closely for all four Primary conditions. For DEJA-VU
Valence the effect is stable across all five repetitions. For DEJA-VU Arousal the
bits/trial gain is **negative in all five repetitions** — the null result is not a
repetition artefact.

---

## D. Dataset-specific interpretation

### DEAP
DEAP is fully crossed: 32 subjects × 40 canonical stimuli, every pair present
exactly once. Under any subject-only split, canonical-stimulus overlap is
**exactly 1.000** — a held-out subject never encounters a novel elicitor, and each
of their stimuli is backed by ~31 source subjects. Stimulus identity alone
recovers a new subject's Valence label at BA 0.739 (0.289 bits/trial) and Arousal
at BA 0.619 (0.069 bits/trial). Valence is roughly four times more
stimulus-determined than Arousal in information terms. Per-participant, the
stimulus prior beats the global prior for 29/32 subjects on Valence and 20/32 on
Arousal.

### I-DARE
I-DARE is also fully crossed: 63 subjects (the EEG∩EMG cohort) × 32 canonical
stimuli = 2016 trials, overlap **exactly 1.000**. This is the strongest condition
in the audit: I-DARE Valence reaches BA 0.956 and 0.794 bits/trial — a held-out
subject's valence label is very nearly determined by which IAPS/affective image
they were shown, and 63/63 participants show a positive gain. Arousal is weaker
but still substantial (BA 0.786, 0.303 bits/trial). The I-DARE stimulus set is
heavily polarised by design (trial-weighted majority agreement 0.956 for Valence),
which is precisely why subject-only evaluation on this dataset is least able to
demonstrate generalisation to unseen elicitors.

### DEJA-VU
DEJA-VU behaves differently on both axes, which is why it is valuable as external
validation.

*Structure.* 24 participants / 30 sessions / 90 emotional physical trials / 16
videos, **not** fully crossed — each session shows only 3 videos. Overlap is
therefore **partial** (0.947 Valence, 0.958 Arousal in LOPO), and four videos are
seen by a single participant, producing genuine unseen-stimulus fallbacks. This
makes DEJA-VU the only dataset in the audit where subject-only splitting
incidentally delivers some stimulus novelty.

*Valence.* Despite partial overlap, the prior is strong (BA 0.803, AUC 0.922,
0.423 bits/trial). The reason is visible in the per-video table: of the 11 videos
with 3 or more retained Valence trials, 7 are perfectly single-class, and
trial-weighted majority agreement is 0.907.

*Arousal.* **Null.** BA 0.531, AUC 0.520, and a *negative* 0.057 bits/trial; the
bootstrap CI spans zero and the permutation p-value is 0.204. Arousal ratings in
this cohort are not aligned to video identity across participants — of the 11
videos with 3 or more retained Arousal trials, none exceeds 0.875 majority
agreement and two split exactly 50/50; trial-weighted majority agreement is only
0.704. The
continuous analysis agrees independently: the stimulus-mean predictor is *worse*
than the global mean (RMSE 1.986 vs 1.906, R² = −0.14, r = 0.02). This is a real
negative result and must be preserved in the manuscript.

Note also that 15 of 24 participants are single-class on Arousal (10 of 24 on
Valence), so per-participant balanced accuracy is undefined for those
participants; the subject-macro denominators are reported explicitly (9/24 and
14/24 respectively) and no participant was silently dropped from the pooled
analysis.

### Supporting descriptive analyses

Analysis C (label consistency / entropy), computed on the full authoritative
tables — plug-in mutual information is **descriptive and finite-sample biased**;
the cross-validated bits/trial in Section C is the safe predictive estimate:

| Dataset | Task | H(Y) bits | H(Y \| stimulus) bits | Plug-in I(Y;S) bits *(descriptive)* | Trial-weighted majority agreement |
|---|---|---:|---:|---:|---:|
| DEAP | Valence | 0.9895 | 0.6547 | 0.3349 | 0.7919 |
| DEAP | Arousal | 0.9798 | 0.8686 | 0.1112 | 0.6849 |
| I-DARE | Valence | 0.9995 | 0.1832 | 0.8164 | 0.9562 |
| I-DARE | Arousal | 0.9594 | 0.6339 | 0.3255 | 0.8143 |
| DEJA-VU | Valence | 0.8730 | 0.2520 | 0.6210 | 0.9067 |
| DEJA-VU | Arousal | 0.9964 | 0.7777 | 0.2187 | 0.7042 |

The plug-in MI exceeds the cross-validated bits/trial in every condition, as
expected from its upward finite-sample bias — most dramatically for DEJA-VU
Arousal (0.219 plug-in vs −0.057 cross-validated). This is a concrete
demonstration of why the manuscript should quote the cross-validated quantity.

Analysis D (continuous ratings, raw SAM scores before midpoint removal, LOPO)
points the same way: MAE improves by 0.58 (DEAP V), 0.15 (DEAP A), 1.08 (I-DARE
V), 0.61 (I-DARE A), 0.58 (DEJA-VU V) and **0.01 (DEJA-VU A, with RMSE getting
worse and R² = −0.14)**.

---

## E. Old-vs-new comparison

Full detail in `provenance/OLD_VS_NEW_COMPARISON.md`. Summary of verdicts:

| Prior claim | Old value | New (most comparable) | Verdict |
|---|---|---|---|
| DEAP Valence stimulus prior BA | 0.8347 | 0.7395 (LOPO) / 0.7709 (View B) | NUMERICALLY DIFFERENT BUT SAME CONCLUSION |
| DEAP Arousal stimulus prior BA | 0.6668 | 0.6190 / 0.6401 | NUMERICALLY DIFFERENT BUT SAME CONCLUSION |
| I-DARE Valence stimulus prior BA | 0.9739 | 0.9559 | NUMERICALLY DIFFERENT BUT SAME CONCLUSION |
| I-DARE Arousal stimulus prior BA | 0.7850 | 0.7861 | **CONFIRMED** (Δ = 0.0011) |
| DEJA-VU Valence video prior BA | 0.8150 | 0.8259 (View B rep 0) | **CONFIRMED** |
| DEJA-VU Arousal video prior BA | 0.5033 | 0.4502 (View B rep 0) | **CONFIRMED (null in both)** |
| DEJA-VU Valence video LOO prior AUROC | 0.9252 | 0.9224 (LOPO AUC) | **CONFIRMED** |
| DEJA-VU Arousal video LOO prior AUROC | 0.5237 | 0.5199 (LOPO AUC) | **CONFIRMED** |
| DEJA-VU video majority-label purity, Valence | 0.906667 | 0.906667 | **CONFIRMED (exact)** |
| DEJA-VU video majority-label purity, Arousal | 0.704225 | 0.704225 | **CONFIRMED (exact)** |
| DEAP canonical-stimulus overlap = 1.0 | 1.0 | 1.000 | **CONFIRMED** |
| Paper-1 storyline quartet 0.894 / 0.718 / 0.990 / 0.875 (AUROC) | — | 0.8372 / 0.6653 / 0.9813 / 0.8380 | **NOT COMPARABLE — and unsourced** |

**Every previous qualitative conclusion survives.** The DEAP and I-DARE balanced
accuracies differ because the earlier PM-SSI-DG figures were computed on the
`inner_subject_guard` region of a 3×3 joint subject×stimulus CV — a subset of
N ≈ 154–225 trials over 16–20 stimuli, with an unsmoothed source mean — whereas
this audit evaluates every retained trial (N = 1263–1799 over 32–40 stimuli) with
Jeffreys smoothing. The two are measuring the same construct on different
supports; the differences are in the expected direction (the restricted guard
region over-represents high-agreement stimuli).

The two exact reproductions (DEJA-VU video majority purity to six decimal places)
are strong independent evidence that this audit's DEJA-VU reconstruction matches
the shared authority.

**One flag, out of scope for this task:** the four AUROC values in the *frozen
Paper-1* storyline (`PM-SSI-DG-parallel-universe-paper1`, line 47) match no
artefact in any searched repository, and match none of this audit's values
either. That document already gates them behind "may be used only after canonical
manuscript-level provenance re-verification", so the guardrail is working. It is a
Paper-1 file and has **not** been modified.

---

## F. Manuscript recommendation for G1

Full reasoning in `manuscript/METRIC_RECOMMENDATION.md`. In brief:

**Preferred minimal pair:**
1. **Structural canonical-stimulus overlap fraction** (DEAP 1.000, I-DARE 1.000,
   DEJA-VU 0.947/0.958). Direct, assumption-free, arithmetic evidence that
   subject-only CV reuses elicitors.
2. **Cross-validated stimulus-ID-only balanced accuracy vs a source-only
   no-stimulus baseline** (DEAP V 0.739, DEAP A 0.619, I-DARE V 0.956, I-DARE A
   0.786, DEJA-VU V 0.803, DEJA-VU A 0.531; baseline 0.500). Intuitive to a
   T-AFFC reviewer and resistant to class imbalance.

**Optional supplementary metric:** cross-validated **bits per trial**
(log-loss gain / ln 2), which is what makes the DEJA-VU Arousal null legible as a
null rather than as a small positive number.

**Smallest defensible claim.** Recommended wording is in
`manuscript/CANDIDATE_WORDING_OPTIONS.md`; the claim the data support is that in
DEAP and I-DARE canonical-stimulus overlap under subject-only evaluation is
complete and stimulus identity alone carries substantial source-derived
predictive information about a held-out participant's label, so subject-only
evaluation does not establish generalisation to unseen stimuli — with the explicit
qualification that the magnitude is task- and dataset-dependent and **absent for
DEJA-VU Arousal**.

**The frozen G1 storyline survives, with one required correction:** it must not be
stated as a universal claim. DEJA-VU Arousal is a genuine counter-example and
should be reported as such.

---

## G. Limitations

1. **Stimulus identity is not an explicit model input** in MM-SAGE-DG. This audit
   measures *available* structure in the data, not what any trained network does.
2. **Available structure ≠ exploited structure.** A positive stimulus prior
   demonstrates that source-side information tied to elicitor identity exists and
   is reachable; it does not prove a neural model recovers or uses it.
3. **Shared elicitors are not sample leakage.** No trial, subject or window is
   duplicated across source and target in any analysis here. The correct framing
   is canonical-stimulus reuse / stimulus-associated prior information, and
   subject-only evaluation leaving stimulus novelty uncontrolled.
4. **This is an association test, not a causal test.** The permutation null
   destroys cross-subject stimulus–label alignment; it licenses "not explainable
   by chance alignment", not "caused by".
5. **Datasets differ in schedule and cohort.** DEAP/I-DARE are fully crossed;
   DEJA-VU shows 3 videos per session with 4 single-participant videos. Overlap
   fractions are therefore not comparable as measures of experimental quality.
6. **Small-N for DEJA-VU.** 75/71 retained trials over 24 participants gives wide
   intervals (e.g. Valence ΔBA 95% CI spans 18.7–42.2 pp). Point estimates should
   not be over-read.
7. **DEJA-VU remains external validation** and is never pooled into the Primary-4
   average.
8. **Plug-in mutual information is biased upward** and is labelled descriptive
   throughout; only the cross-validated bits/trial should be quoted as an
   information estimate.
9. **ΔAUC and ΔMacro-F1 are degenerate comparators** under leave-one-participant-out
   (Section C) and should not be quoted.
10. **The I-DARE cohort is the 63-subject EEG∩EMG intersection** defined by the
    repository's own loader; the label files contain 64 subject columns. A
    different cohort definition would change N but not the structural conclusion
    (overlap remains 1.000 for any subset of a fully crossed design).
11. **`configs/paths/local.yaml` does not exist** in this worktree; dataset roots
    were resolved to their on-disk locations and recorded explicitly in
    `provenance/INPUT_AUTHORITY.json`.
12. **The primary bootstrap conditions on the fitted prior** and understates
    uncertainty; see the variant-sensitivity table in Section C. Only the DEAP
    Arousal interval is materially affected.
13. **The `=5` midpoint rule has a very different bite across datasets.** DEAP
    ratings are *continuous*, so exact equality to 5.0 is nearly measure-zero and
    drops only 16 Valence / 17 Arousal trials (1.2-1.3%); 33 Valence and 20 Arousal
    DEAP trials lie within 0.02 of the midpoint and are retained as confident
    LOW/HIGH. I-DARE and DEJA-VU ratings are *integers*, so the identical rule
    drops 349/217 and 15/19 trials (up to 17.3%). The cross-dataset Paper-2
    convention is applied faithfully and identically, but it is not equally
    selective, and DEAP retains near-midpoint trials that the other datasets
    would have discarded.
14. **The leakage suite contains 16 assertions but 12 independent computations.**
    T04/T05/T06 restate the single T02 computation and T03 is a structural
    assertion about the source code whose empirical evidence is T02. The
    `kind` field in `validation/SOURCE_ONLY_LEAKAGE_TESTS.json` marks this; quote
    `n_independent_computations`, not `n_assertions`.

---

## Reproduction

```bash
"/mnt/HDD/AliWorks/HCI Tagging Database/HCI/bin/python3" source/run_stimulus_prior_audit.py
```

Runtime ≈ 92 s. See `source/README_REPRODUCE.md`.

To regenerate the machine-verified reproducibility block, run once to a scratch
directory and then again with `--verify-against <that directory>`.
