# Old vs New Comparison

Performed **after** the fresh independent results were computed and written to
`derived/`. No old value entered the new computation.

Verdict vocabulary: `CONFIRMED` · `NUMERICALLY DIFFERENT BUT SAME CONCLUSION` ·
`SUPERSEDED BY BETTER METRIC` · `INCORRECT` · `NOT COMPARABLE`.

**No existing frozen file was modified by this audit.**

---

## 1. DEAP Valence — stimulus prior

| | |
|---|---|
| **Old value** | BA `0.8346800258564965`; AUROC `0.8814641241111829`; macro-F1 `0.8413701363485201`; log loss `0.536707132766562`; Brier `0.12075714264008162`; N = 159; 20 stimuli |
| **Old source** | `PM-SSI-DG/runs/guard_region_decomposition_final_20260725_151051/metadata_prior_metrics.csv:2` |
| **New value** | View A (LOPO): BA `0.7395`, AUC `0.8372`, macro-F1 `0.7389`, log loss `0.4868`, Brier `0.1551`, N = 1264, 40 stimuli. View B (project subject folds): BA `0.7709`, AUC `0.8354` |
| **Difference** | BA −0.095 (LOPO) / −0.064 (View B); AUROC −0.044 |
| **Same labels?** | Yes — identical `<5 LOW / >5 HIGH / =5 DROP` rule, same DEAP verified stimulus mapping. |
| **Same midpoint rule?** | Yes. |
| **Same canonical mapping?** | Yes (`deap_verified_stimulus_mapping.csv`, cross-checked against `deap_subject_presentation_order.csv`). |
| **Same evaluation unit?** | **No.** Old = `inner_subject_guard` region of the 3×3 joint subject×stimulus CV (N = 159, 20 of 40 stimuli, `key_coverage = 1.0` enforced). New = every retained trial (N = 1264, all 40 stimuli). Old used an unsmoothed source mean; new uses Jeffreys smoothing. |
| **Verdict** | **NUMERICALLY DIFFERENT BUT SAME CONCLUSION.** Both show a large, well-above-chance stimulus-only prior for a held-out subject. The old figure is higher because the guard region is a restricted, higher-agreement subset. |

## 2. DEAP Arousal — stimulus prior

| | |
|---|---|
| **Old value** | BA `0.6668462643678161`; AUROC `0.7126436781609196`; N = 154; 20 stimuli (`:11`) |
| **New value** | View A: BA `0.6190`, AUC `0.6653`, N = 1263, 40 stimuli. View B: BA `0.6401`, AUC `0.6815` |
| **Difference** | BA −0.048 (LOPO) / −0.027 (View B); AUROC −0.047 |
| **Comparability** | Same labels, midpoint rule and canonical mapping; different evaluation unit and smoothing (as §1). |
| **Verdict** | **NUMERICALLY DIFFERENT BUT SAME CONCLUSION.** Both show a modest but clearly above-chance prior, and both rank Arousal well below Valence. |

## 3. I-DARE Valence — stimulus prior

| | |
|---|---|
| **Old value** | BA `0.9739018087855298`; AUROC `0.9856589147286822`; N = 219; 16 stimuli (`:20`) |
| **New value** | View A: BA `0.9559`, AUC `0.9813`, N = 1667, 32 stimuli. View B: BA `0.9559`, AUC `0.9831` |
| **Difference** | BA −0.018; AUROC −0.004 |
| **Comparability** | Same label rule and canonical stimulus normalisation. Different evaluation unit (as §1). The old run additionally carried `"scientific_gate1_status": "BLOCKED"`, `"full_run_authorized": false`, and used a partial cache (`guard_trial_count: 504` of `624`). |
| **Verdict** | **NUMERICALLY DIFFERENT BUT SAME CONCLUSION.** Both are near-ceiling. This remains the strongest condition in the corpus. |

## 4. I-DARE Arousal — stimulus prior

| | |
|---|---|
| **Old value** | BA `0.7849999999999999`; AUROC `0.8722799999999999`; N = 225; 16 stimuli (`:29`) |
| **New value** | View A: BA `0.7861`, AUC `0.8380`, N = 1799, 32 stimuli. View B: identical to View A |
| **Difference** | **BA +0.0011**; AUROC −0.034 |
| **Verdict** | **CONFIRMED.** The balanced accuracies agree to about one part in a thousand despite an eight-fold difference in N and a doubling of the stimulus set. |

## 5. DEJA-VU Valence — video prior

| | |
|---|---|
| **Old value** | BA `0.814988963421626`; macro-F1 `0.8257193349263242`; ROC-AUC `0.9063929533801824`; Brier `0.10911759765834986`; N = 150; coverage 0.92 (repetition 0, primary) |
| **Old source** | `DEJA-VU-Emotion-Recognition/docs/dejavu_shortcut_baseline_summary.csv`, region `unseen_subject_seen_video`, baseline `video_train_prior` |
| **New value** | View B rep 0: BA `0.8259`, AUC `0.9322`, Brier gain `0.1085`, N = 75, overlap 0.933. View A (LOPO): BA `0.8032`, AUC `0.9224` |
| **Difference** | BA +0.011 (View B rep 0) |
| **Same labels?** | Yes — `after` rating, `<5/>5/=5` rule; independently re-derived and cross-checked row-by-row against the manifest's own `primary_valence_label`. |
| **Same evaluation unit?** | **No.** Old = macro-average over 9 joint subject×video cells with the same trial counted in several cells (old N = 150 counts cell memberships; the cohort has only 75 retained Valence trials). New = each retained physical trial predicted exactly once. |
| **Verdict** | **CONFIRMED.** Agreement is close despite the different aggregation, and the new figure is the cleaner one (no trial double-counting). |

## 6. DEJA-VU Arousal — video prior

| | |
|---|---|
| **Old value** | BA `0.5032990974167446`; macro-F1 `0.4214174280457315`; ROC-AUC `0.5449164452105628`; N = 142; coverage 0.9296 (rep 0) |
| **New value** | View B rep 0: BA `0.4502`, AUC `0.4290`, bits/trial `−0.1774`. View A: BA `0.5311`, AUC `0.5199`, bits/trial `−0.0572`, permutation p `0.204`, bits 95% CI `[−0.234, 0.104]` |
| **Difference** | BA −0.053 (View B rep 0) / +0.028 (View A) |
| **Verdict** | **CONFIRMED (null in both).** Both analyses put DEJA-VU Arousal at chance. The new audit strengthens the conclusion by adding a bootstrap CI spanning zero, a non-significant permutation p-value, a negative bits-per-trial in all five fold repetitions, and an independent continuous-rating analysis that also fails to beat the global mean. |

## 7. DEJA-VU leave-one-trial-out video prior AUROC

| | |
|---|---|
| **Old value** | Valence `0.9252`; Arousal `0.5237` |
| **Old source** | `PM-SSI-DG-dejavu-paper1/docs/audits/dejavu_arousal_root_cause_v1/DEJAVU_AROUSAL_ROOT_CAUSE_AUDIT.json` |
| **New value** | LOPO stimulus-prior AUC: Valence `0.9224`; Arousal `0.5199` |
| **Difference** | −0.0028 and −0.0038 |
| **Same evaluation unit?** | **No.** Old = leave-one-**trial**-out over all 90 presentations (not subject-respecting). New = leave-one-**participant**-out (all of a participant's sessions held out together). |
| **Verdict** | **CONFIRMED.** The near-identical values indicate that, for DEJA-VU, tightening the held-out unit from trial to participant changes the video prior very little — the prior is carried by video identity, not by participant identity. |

## 8. DEJA-VU video majority-label purity

| | |
|---|---|
| **Old value** | Valence `0.906667`; Arousal `0.704225` |
| **Old source** | `MM-SAGE-DG-dejavu-paper2/docs/dejavu/paper2-training-selection-v1/evidence/claude_dejavu_d0s_results.json:7062, :7052` |
| **New value** | Trial-weighted majority agreement: Valence `0.9067`; Arousal `0.7042` (`derived/STIMULUS_LABEL_CONSISTENCY_SUMMARY.csv`) |
| **Difference** | `0.000000` — exact agreement to six decimal places |
| **Verdict** | **CONFIRMED (exact).** This is the strongest available evidence that the audit's independent DEJA-VU reconstruction matches the shared authority. |

Note: the *root-cause* audit's "Video mean purity" (0.9228 / 0.7636) is a
**macro** mean over videos and must not be compared with the trial-weighted
figure above; this audit's macro equivalents are `0.9228` (Valence) and `0.7636`
(Arousal) — also an exact match.

## 9. DEAP canonical-stimulus overlap

| | |
|---|---|
| **Old value** | `Stimulus mapping identical across all subjects: True`, `Stimulus consensus one-to-one: True`, 1280 source rows / 32 subjects / 40 stimuli → overlap 1.0 |
| **Old source** | `MM-SAGE-DG/docs/implementation/JOINT_CV_PRIOR_EVIDENCE_DECISION.md:26-33` |
| **New value** | Trial-weighted and unique-stimulus overlap = `1.000` in every one of 32 LOPO folds and all 3 project subject folds; 0 fallback trials; fully-crossed check passes (1280 = 32×40, zero duplicate pairs) |
| **Verdict** | **CONFIRMED.** |

## 10. DEJA-VU frozen cohort and label support

| | |
|---|---|
| **Old value** | 90 emotional physical trials, 16 videos, 24 participants, 30 sessions; Valence LOW 53 / HIGH 22 / DROP 15 / retained 75; Arousal LOW 33 / HIGH 38 / DROP 19 / retained 71 |
| **Old source** | `paper2-label-v3/DEJAVU_PAPER2_LABEL_STATE_v3.json`, re-derived from shared authority `01351073…` |
| **New value** | Identical on all 12 quantities (`validation/DATA_AUTHORITY_VALIDATION.json → dejavu_authority_crosscheck_all_match: true`) |
| **Verdict** | **CONFIRMED (exact).** |

## 11. Paper-1 frozen storyline quartet

| | |
|---|---|
| **Old value** | DEAP Valence `0.894`, DEAP Arousal `0.718`, I-DARE Valence `0.990`, I-DARE Arousal `0.875` stimulus-prior AUROC |
| **Old source** | `PM-SSI-DG-parallel-universe-paper1/docs/parallel-universe/paper1/writing/PAPER1_INTRO_RELATED_WORK_STRUCTURE_AND_STORYLINE_v1_FROZEN.md:47` |
| **New value** | LOPO stimulus-prior AUC `0.8372` / `0.6653` / `0.9813` / `0.8380` |
| **Verdict** | **NOT COMPARABLE — and the old values are unsourced.** They match neither this audit nor any artefact found in seven searched repositories (which uniformly report `0.8815` / `0.7126` / `0.9857` / `0.8723`). The document already gates them behind provenance re-verification. This is a **Paper-1** file, outside this task's scope; it was **not** modified. Flagged for its owner. |

---

## Overall

Every prior **qualitative** conclusion survives the independent recomputation.
Two quantities reproduce **exactly** (DEJA-VU video majority purity, DEJA-VU
cohort/support). One reproduces to ~0.001 (I-DARE Arousal BA). Four differ
numerically for a fully identified and legitimate reason — the earlier DEAP and
I-DARE figures were computed on a restricted guard region of the joint CV rather
than on the full retained trial set.

No previously frozen artefact required correction as a result of this audit. The
one integrity issue found (§11) predates this work, belongs to Paper 1, and is
already self-gated in its own document.
