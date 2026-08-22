# Existing-Analysis Discovery (Section 4 of the audit brief)

Read-only sweep performed **before** the fresh computation, over:
`MM-SAGE-DG-PARALLEL-UNIVERSE`, `MM-SAGE-DG`, `MM-SAGE-DG-dejavu-paper2`,
`DEJA-VU-Emotion-Recognition`, `PM-SSI-DG`, `PM-SSI-DG-parallel-universe-paper1`,
`PM-SSI-DG-dejavu-paper1`.

`/mnt/HDD/AliWorks/MM-SAGE-DG-FULL-LEAKAGE-ORACLE` was **hard-excluded** from every
`find`/`grep` per the audit brief and was never read or listed.

Search terms (filenames and content, case-insensitive): *stimulus prior, prior
knowledge, prior information, stimulus-only, stimulus identity, canonical stimulus
overlap, stimulus overlap, label consistency, stimulus predictability, stimulus
majority, majority label, elicitor, content bias, video prior, video-only, seen
stimulus, unseen stimulus, stimulus novelty, bits per trial*.

**No old derived result was used as an input to the fresh computation.** These are
comparison targets only. Verdicts are in `OLD_VS_NEW_COMPARISON.md`.

---

## DEAP and I-DARE

### A1 — Authoritative prior numbers (ACTIVE)

* **Path:** `/mnt/HDD/AliWorks/PM-SSI-DG/runs/guard_region_decomposition_final_20260725_151051/metadata_prior_metrics.csv`
* **Repo:** `PM-SSI-DG`, branch `feat/baseline-joint-pipeline`, HEAD `23b09659bea4ee23da3b01ca86cf0560a1c42f90`
  (the run's own `provenance.json` records `git_commit: a0cc2350b70df79409bce7669b573c167352a615`)
* **Method:** `prior_type = train_stimulus_id_label_mean` — per-`stimulus_id` mean
  binary label over source-training trials only, applied as the predicted
  probability for held-out-subject trials. Implementation:
  `PM-SSI-DG/src/pm_ssi_dg/training/guard_region_analysis.py:160-199`.
* **Evaluation unit:** **not** LOSO. The `inner_subject_guard` region of the frozen
  3×3 joint subject×stimulus CV = unseen subjects × source-seen stimuli, with
  `key_coverage = 1.0` contractually enforced.
* **Status:** ACTIVE. `summary.json` reports `"status": "PASS"`,
  `"outer_test_opened": false`. Seed-invariant across seeds 17/29/43 (it is a
  label-only prior, not a model). Identical values re-appear in three sibling
  diagnostic runs (`frozen_readout_diagnostic_…`, `pooling_fault_isolation_…`,
  `fusion_fault_isolation_…`) — provenance, not independent evidence.

| Dataset | Task | Balanced accuracy | AUROC | Macro-F1 | Log loss | Brier | N | #stimuli | line |
|---|---|---|---|---|---|---|---:|---:|---|
| DEAP | Valence | 0.8346800258564965 | 0.8814641241111829 | 0.8413701363485201 | 0.536707132766562 | 0.12075714264008162 | 159 | 20 | `:2` |
| DEAP | Arousal | 0.6668462643678161 | 0.7126436781609196 | 0.6727452433901655 | 0.6131505205939297 | 0.21055269983226768 | 154 | 20 | `:11` |
| I-DARE | Valence | 0.9739018087855298 | 0.9856589147286822 | 0.9762971621533866 | 0.13402018943257263 | 0.021856924116293263 | 219 | 16 | `:20` |
| I-DARE | Arousal | 0.7849999999999999 | 0.8722799999999999 | 0.7885338345864661 | 0.5064896888862412 | 0.14733892699136483 | 225 | 16 | `:29` |

Caveats recorded in the same run: I-DARE carries
`"scientific_gate1_status": "BLOCKED"` and `"full_run_authorized": false`, computed
from a read-only inner-guard cache (`guard_trial_count: 504` of
`base_cached_trial_count: 624`). ADR-0004 additionally declares *"I-DARE arousal
remains a negative-control cell and is excluded from the overall agreement gate."*

### A2 — Governing decision record (ACTIVE, qualitative only)

* **Path:** `/mnt/HDD/AliWorks/PM-SSI-DG/docs/adr/ADR-0004-guard-region-decomposition.md`
  (byte-identical copies in `PM-SSI-DG-parallel-universe-paper1` and `PM-SSI-DG-dejavu-paper1`)
* Line 18–19: *"seen stimuli have strong source-label priors, so a cross-subject
  score can be high without EEG/EMG carrying subject-invariant emotion
  information."* Status line 5: `Accepted for bounded development diagnostics only.`

### A3 — Structural overlap fact (ACTIVE)

* **Path:** `MM-SAGE-DG/docs/implementation/JOINT_CV_PRIOR_EVIDENCE_DECISION.md`
  (canonical copy; byte-identical in 4 other locations incl. two archives)
* **Repo:** `MM-SAGE-DG`, branch `feat/light-v1.2-baseline-pipeline`, HEAD `6c4729371a729fa43750b7250d364635d150921e`
* Lines 26–33: `Source rows: 1280`, `Source subjects: 32`,
  `Stimulus consensus rows: 40`, `Stimulus mapping identical across all subjects: True`,
  `Stimulus consensus one-to-one: True` — i.e. DEAP canonical-stimulus overlap = 1.0.
* `decision_version: 3`; supersedes the Step-10 conclusion
  (`step10_unresolved_conclusion_superseded: true`).

### A4 — Adjacent, NOT the same construct (feature-side, not label-side)

* `PM-SSI-DG/runs/deap_window_signal_localization_20260728_104915/unseen_stimulus_pair_metrics.csv`
  — `UNSEEN_STIMULUS_PAIR_VERIFICATION`, feature-based same-vs-different-stimulus
  verifier, all 16 rows at chance.
* `…/seen_stimulus_identity_control.csv` — 20-way stimulus-ID decoding from
  features; `balanced_accuracy = 0.0`, `permutation_p_value = 1.0`.
* `…/guard_region_decomposition_final_…/leakage_probes.csv:2-3` — stimulus
  decodable from fused features at 0.0111/0.0167 vs chance 0.05.
* `MM-SAGE-DG/artifacts/diagnostic_counterfactuals/label_signal_identifiability_probe_results_resumable_v1/…/SOURCE_FIT_STIMULUS_HELDOUT.json`
  — held-out-*stimulus* feature probes; opposite direction.

---

## DEJA-VU

### B1 — Authoritative video prior (ACTIVE, explicitly diagnostic-only)

* **Paths:** `DEJA-VU-Emotion-Recognition/docs/dejavu_shortcut_and_null_audit.md`,
  `…/docs/dejavu_shortcut_baseline_summary.csv`, `…/docs/dejavu_shortcut_and_null_audit.json`;
  generator `scripts/12_audit_dejavu_shortcuts_and_nulls.py`
* **Repo:** `DEJA-VU-Emotion-Recognition`, branch `dejavu-cohort-b-joint-cv-audit`,
  HEAD `01351073683eaa6c4469bf8b8728227a184b1ac4` (the pinned shared authority).
  Generated at commit `2efbb28`; script asserts ancestor prefix `719d300`.
* **Target rows:** region `unseen_subject_seen_video`, baseline `video_train_prior`.
* **Evaluation unit:** macro-average over the 9 defined cells of the 3×3 joint CV
  (`cells_evaluated = 9`), *not* a pooled set. `identity_prior_coverage` is
  **< 1.0** (0.92–0.958).

| Rep | Role | Task | BA | Macro-F1 | ROC-AUC | Accuracy | Brier | N | coverage |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | **primary** | valence | 0.814988963421626 | 0.8257193349263242 | 0.9063929533801824 | 0.8698385940414926 | 0.10911759765834986 | 150 | 0.92 |
| 0 | **primary** | arousal | 0.5032990974167446 | 0.4214174280457315 | 0.5449164452105628 | 0.4715181504655189 | 0.3827154579504693 | 142 | 0.9295774647887324 |
| 1 | sensitivity | valence | 0.8270573108808403 | 0.8023418925543109 | 0.9219152307387601 | — | — | 150 | 0.9466666666666667 |
| 1 | sensitivity | arousal | 0.5438552188552188 | 0.5163863388215029 | 0.619818722943723 | — | — | 142 | 0.9577464788732394 |
| 2 | sensitivity | valence | 0.8088945654735128 | 0.784843452672456 | 0.9037557147206271 | — | — | 150 | 0.92 |
| 2 | sensitivity | arousal | 0.554900654900655 | 0.4740062406729073 | 0.5726555950663094 | — | — | 142 | 0.9295774647887324 |
| 3 | sensitivity | valence | 0.825842521675855 | 0.8118699271081452 | 0.8774609264192598 | — | — | 150 | 0.9466666666666667 |
| 3 | sensitivity | arousal | 0.612238841405508 | 0.5352869665602424 | 0.5837295420628754 | — | — | 142 | 0.9577464788732394 |
| 4 | sensitivity | valence | 0.8084215167548501 | 0.7483419414694175 | 0.8993106995884774 | — | — | 150 | 0.9466666666666667 |
| 4 | sensitivity | arousal | 0.5384680134680134 | 0.49781018202070837 | 0.5752645502645503 | — | — | 142 | 0.9577464788732394 |

**Status:** ACTIVE but explicitly diagnostic-only. Audit line 55: *"These identity
priors are diagnostic only."* `dejavu_data_protocol_status.md` (final line):
*"Diagnostic identity priors remain secondary and are not legal priors in the
primary unseen-subject plus unseen-video test."* The legal primary baselines
(`global_train_prior`, `position_train_prior`) sit at BA 0.5000 / 0.3194.

### B2 — Independent leave-one-trial-out estimate (ACTIVE)

* **Paths:** `PM-SSI-DG-dejavu-paper1/docs/audits/dejavu_arousal_root_cause_v1/DEJAVU_AROUSAL_ROOT_CAUSE_AUDIT.md` (+ `.json`)
* **Repo:** `PM-SSI-DG-dejavu-paper1`, branch `feat/dejavu-paper1-integration`, HEAD `3b719efa69579ebe7815d11d3cc489a4c26d7555`
* `valence_video_loo_prior_auroc = 0.9252`, `arousal_video_loo_prior_auroc = 0.5237`,
  `arousal_quadrant_loo_prior_auroc = 0.504`, `valence_quadrant_loo_prior_auroc = 0.8465`,
  `arousal_participant_loo_prior_auroc = 0.7551`, `arousal_participant_mean_purity = 0.858333`.
* Video mean purity: 0.7636 (arousal) / 0.9228 (valence). Single-class
  participants: 15/24 arousal, 10/24 valence.
* **Evaluation unit:** leave-one-**trial**-out over all 90 presentations — not
  subject-fold-respecting. Different unit from B1.
* Line 15: *"Arousal is predominantly participant-specific … while
  stimulus/quadrant information is weak."*

### B3 — Video majority-label purity (ACTIVE, frozen before training)

* **Paths:** `MM-SAGE-DG-dejavu-paper2/docs/dejavu/paper2-training-selection-v1/evidence/claude_dejavu_d0s_report.md`
  and `…/claude_dejavu_d0s_results.json`
* **Repo:** `MM-SAGE-DG-dejavu-paper2`, branch `feat/dejavu-paper2-integration`, HEAD `189d417d020de08ac1e26cabbac9ec7838b184b6`
* `"video_majority_label_purity": 0.906667` (valence, JSON line 7062);
  `0.704225` (arousal, line 7052). Pooled over the Cohort-B manifest, no fold
  structure.
* Report lines 105–117: only 4 of 16 videos carry both Valence classes; 14 of 24
  participants carry both Valence classes (arousal: 9 of 24).
* **Status:** ACTIVE, `"status": "ACTIVE_FROZEN_BEFORE_DEJAVU_TRAINING"`.

### B4 — Capacity audit (context, no prior-predictability number)

`DEJA-VU-Emotion-Recognition/docs/dejavu_mm_sage_gradient_support_audit.md`.
Verdict `LIMITED_OR_WEAK_MECHANISM_SUPPORT`; not a stimulus-label predictability
measure.

---

## Terminology origin (ACTIVE, zero numbers)

`MM-SAGE-DG-PARALLEL-UNIVERSE/docs/parallel-universe/v4/manuscript-writing/intro-related-work-storyline-v1/PAPER2_INTRO_RELATED_WORK_STORYLINE_AND_STRUCTURE_v1.md`
(branch `parallel-universe/manuscript-blueprint-v1`, HEAD `d1b7a86…`) coins the
Paper-2 phrase. Line 38 fixes the preferred terminology; line 127 is effectively
the request that generated this audit. The sibling freeze registration marks it
`CLOSED / FROZEN STRUCTURAL STORYLINE v1`, item 5: *"Canonical-stimulus overlap is
distinguished from actual sample/trial leakage."*

---

## FINDING — unsourced quartet in a frozen Paper-1 storyline

* **Path:** `PM-SSI-DG-parallel-universe-paper1/docs/parallel-universe/paper1/writing/PAPER1_INTRO_RELATED_WORK_STRUCTURE_AND_STORYLINE_v1_FROZEN.md`, **line 47**
* **Repo/HEAD:** branch `parallel-universe/paper1-manuscript`, HEAD `0527f0c0808679a38d7ff908f914b70cfb2e7007`
* Verbatim: *"Internal diagnostic slot. Prior Paper-1 audit values may be used only
  after canonical manuscript-level provenance re-verification: DEAP Valence 0.894,
  DEAP Arousal 0.718, I-DARE Valence 0.990, I-DARE Arousal 0.875 stimulus-prior
  AUROC. No DEJA-VU value is assumed."*

These four values match **no artefact** in any searched repository. Every artefact
carrying `prior_key=stimulus_id` + `protocol=cross_subject_only` reports the frozen
quartet 0.8815 / 0.7126 / 0.9857 / 0.8723 instead:

| Dataset / Task | Storyline line 47 | Frozen artefact (A1) | Δ |
|---|---:|---:|---:|
| DEAP Valence | 0.894 | 0.8814641241111829 | +0.0125 |
| DEAP Arousal | 0.718 | 0.7126436781609196 | +0.0054 |
| I-DARE Valence | 0.990 | 0.9856589147286822 | +0.0043 |
| I-DARE Arousal | 0.875 | 0.8722799999999999 | +0.0027 |

The document gates them behind explicit provenance re-verification, so its
guardrail is working. **This is a Paper-1 file and was not modified.** Flagged for
the Paper-1 owner. `PM-SSI-DG-local-notes` was outside the given search roots and
is the most plausible remaining provenance source.

---

## Explicit nulls (nothing found)

* **Bits-per-trial / mutual-information-in-bits framing** for *any* dataset: none.
  This audit introduces it.
* **DEAP or I-DARE label-based stimulus-novelty / unseen-stimulus prior:** none
  (the DEAP `UNSEEN_STIMULUS_PAIR_VERIFICATION` artefact is feature-based).
* **DEAP or I-DARE majority-label / stimulus-majority purity number:** none. The
  purity framing exists only for DEJA-VU.
* **Any DEJA-VU prior number cited in an MM-SAGE-DG or PM-SSI-DG manuscript
  document:** none. Paper-1 explicitly says *"No DEJA-VU value is assumed."*
* **`MM-SAGE-DG-PARALLEL-UNIVERSE`, `MM-SAGE-DG`, `MM-SAGE-DG-dejavu-paper2`** hold
  no stimulus-label-prior predictability numbers of their own beyond the
  structural overlap (A3) and the DEJA-VU purity (B3).
* **Cluster-bootstrap CIs or permutation nulls on a stimulus prior:** none found
  for any dataset. This audit introduces them.

## Repositories searched

| Repo | Branch | HEAD |
|---|---|---|
| `MM-SAGE-DG-PARALLEL-UNIVERSE` | `parallel-universe/manuscript-blueprint-v1` | `d1b7a86ccb4f6ac384f2af9ace8887c204b3644b` |
| `MM-SAGE-DG` | `feat/light-v1.2-baseline-pipeline` | `6c4729371a729fa43750b7250d364635d150921e` |
| `MM-SAGE-DG-dejavu-paper2` | `feat/dejavu-paper2-integration` | `189d417d020de08ac1e26cabbac9ec7838b184b6` |
| `DEJA-VU-Emotion-Recognition` | `dejavu-cohort-b-joint-cv-audit` | `01351073683eaa6c4469bf8b8728227a184b1ac4` |
| `PM-SSI-DG` | `feat/baseline-joint-pipeline` | `23b09659bea4ee23da3b01ca86cf0560a1c42f90` |
| `PM-SSI-DG-parallel-universe-paper1` | `parallel-universe/paper1-manuscript` | `0527f0c0808679a38d7ff908f914b70cfb2e7007` |
| `PM-SSI-DG-dejavu-paper1` | `feat/dejavu-paper1-integration` | `3b719efa69579ebe7815d11d3cc489a4c26d7555` |

**Not searched** (outside the given roots; possible remaining provenance for the
unsourced quartet): `PM-SSI-DG-local-notes`, `PM-SSI-DG-dejavu-leakage-oracle`,
`PM-SSI-DG-full-leakage-upper-bound`, `MM-SAGE-DG-DEJAVU-LEAKAGE-ORACLE`,
`PM-SSI-DG-dejavu-arousal-rescue`. `MM-SAGE-DG-FULL-LEAKAGE-ORACLE` is hard-excluded.
