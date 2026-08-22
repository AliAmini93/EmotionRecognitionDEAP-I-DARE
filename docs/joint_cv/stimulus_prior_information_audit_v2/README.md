# Stimulus-Associated Prior Information Audit — candidate v1

**CANDIDATE ANALYSIS ONLY.** Not frozen, not registered, not committed, not
manuscript prose. Nothing outside this directory was created or modified.

## What this is

A fresh, independent, dataset-derived audit quantifying how much information
about a held-out participant's binary Valence/Arousal label is available from the
identity of the eliciting stimulus alone, when the stimulus→label tendency is
estimated from source participants only.

Six conditions: DEAP × {Valence, Arousal}, I-DARE × {Valence, Arousal},
DEJA-VU × {Valence, Arousal}.

Everything was recomputed from authoritative dataset metadata and labels. No
previously derived project number entered the computation; prior claims were used
only as after-the-fact comparison targets.

## Headline

| Dataset | Task | Stimulus overlap | Stimulus-only BA | Baseline BA | Bits/trial [95% CI] | Perm. p |
|---|---|---:|---:|---:|---|---:|
| DEAP | Valence | **1.000** | 0.739 | 0.500 | 0.289 [0.198, 0.365] | 1.0×10⁻⁴ |
| DEAP | Arousal | **1.000** | 0.619 | 0.500 | 0.069 [0.020, 0.118] * | 1.0×10⁻⁴ |
| I-DARE | Valence | **1.000** | 0.956 | 0.500 | 0.794 [0.751, 0.833] | 1.0×10⁻⁴ |
| I-DARE | Arousal | **1.000** | 0.786 | 0.500 | 0.303 [0.234, 0.366] | 1.0×10⁻⁴ |
| DEJA-VU | Valence | 0.947 | 0.803 | 0.500 | 0.423 [0.272, 0.567] | 1.0×10⁻⁴ |
| DEJA-VU | Arousal | 0.958 | 0.531 | 0.434 | **−0.057 [−0.234, 0.104]** | **0.204** |

Five of six conditions show substantial stimulus-associated prior information.
**DEJA-VU Arousal is a genuine null and is preserved as such.**

\* The DEAP Arousal bits/trial interval spans zero under the refit bootstrap
variant ([-0.006, 0.101]); that condition's significance rests on the permutation
test, not the bootstrap. See `REPORT.md` §C.

DEAP and I-DARE are fully crossed designs, so canonical-stimulus overlap under
subject-only splitting is **exactly complete** — zero unseen-stimulus fallbacks in
any fold.

Read `REPORT.md` for the full result.

## Audit status

* `AUDIT_STATUS = PASS`
* Source-only leakage suite: 16/16 assertions PASS, of which **12 are independent
  computations**, 3 restate one computation and 1 is a code-inspection assertion
  (see the `kind` field in `SOURCE_ONLY_LEAKAGE_TESTS.json`; quote
  `n_independent_computations`)
* Bitwise reproducible: all **12** derived artefacts hash-identical across two
  independent process runs (machine-generated via `--verify-against`), including
  every 10,000-replicate resampling loop
* DEJA-VU cohort and label support reproduce the frozen authority exactly on all
  12 checked quantities
* Zero invalid bootstrap replicates in all six conditions

## Layout

```
README.md                    this file
REPORT.md                    full report (sections A-G per the audit brief)
HASHES.sha256                sha256 of every file in this package

source/
  run_stimulus_prior_audit.py   self-contained analysis (single file)
  README_REPRODUCE.md           how to re-run

derived/
  CANONICAL_TRIAL_TABLE_{DEAP,IDARE,DEJAVU}.csv.gz   reconstructed trial tables
  STIMULUS_OVERLAP_BY_FOLD.csv                       Analysis A
  STIMULUS_PRIOR_OOF_PREDICTIONS.csv.gz              per-trial OOF predictions
  STIMULUS_PRIOR_METRICS_BY_FOLD.csv                 per-fold metrics
  STIMULUS_PRIOR_SUMMARY.csv                         pooled OOF summary (headline)
  STIMULUS_LABEL_CONSISTENCY.csv                     Analysis C, per stimulus
  STIMULUS_LABEL_CONSISTENCY_SUMMARY.csv             Analysis C, per dataset-task
  STIMULUS_PRIOR_BOOTSTRAP_CI.csv                    10,000-replicate cluster bootstrap
                                                     (primary + refit sensitivity variant)
  STIMULUS_PRIOR_PERMUTATION_SUMMARY.csv             10,000-permutation matched null
  CONTINUOUS_RATING_PRIOR_SUMMARY.csv                Analysis D

validation/
  DATA_AUTHORITY_VALIDATION.json     counts, supports, design facts, authority cross-checks
  SOURCE_ONLY_LEAKAGE_TESTS.json     16 machine-readable PASS/FAIL assertions
                                     (12 independent computations; see `kind`)
  REPRODUCIBILITY_VALIDATION.json    content hashes + cross-process rerun result
  FINAL_AUDIT_VALIDATION.json        overall gate

provenance/
  INPUT_AUTHORITY.json               every input file with sha256
  ENVIRONMENT.json                   interpreter, versions, platform, repo HEADs
  EXISTING_ANALYSIS_DISCOVERY.md     prior-analysis sweep (Section 4 of the brief)
  OLD_VS_NEW_COMPARISON.md           per-claim verdicts

manuscript/
  CANDIDATE_G1_EVIDENCE_SUMMARY.md   what the data support for G1
  CANDIDATE_WORDING_OPTIONS.md       drafting inputs (NOT final prose)
  METRIC_RECOMMENDATION.md           which metrics to use, and which not to
```

## Method in one paragraph

For each dataset × task, retained trials (task-specific `=5` midpoint drop) are
partitioned by held-out participant. **View A** is leave-one-participant-out;
**View B** uses the project's own frozen subject folds (DEAP and I-DARE:
`configs/cv/folds/*_subject_folds.csv`; DEJA-VU: the pinned shared-authority
participant folds, primary repetition 0 plus repetitions 1–4 as sensitivity). For
each held-out unit, a Jeffreys-smoothed per-stimulus HIGH probability
`p = (n_HIGH + 0.5)/(n_total + 1)` is estimated **from source participants only**;
target stimuli absent from the source fall back to the source-only global class
prior and are counted. The comparator is that same source-only global prior
applied to every trial. Uncertainty is a 10,000-replicate bootstrap clustered on
held-out participants, reported in two variants (primary, which conditions on the
fitted prior, and a refit-within-resample sensitivity variant); the null permutes canonical-stimulus identity **within each
participant**, preserving every participant's trial count, label multiset and
stimulus multiset exactly. DEJA-VU participants are held out with all their
sessions together.

## Read-only guarantees

* No dataset file was written.
* The pinned DEJA-VU shared authority (`01351073…`) was read only; not checked
  out, reset, edited or committed.
* No existing frozen v4 artefact, figure, table or manuscript authority was
  modified.
* No `git add`, `commit`, `push`, `reset` or `clean` was run.
* `/mnt/HDD/AliWorks/MM-SAGE-DG-FULL-LEAKAGE-ORACLE` was never accessed.

## Known caveats

See `REPORT.md` §G. The most important: this measures *available* structure in the
data, not what any trained model does; canonical-stimulus reuse is **not** sample
leakage; and ΔAUC / ΔMacro-F1 are degenerate comparators under
leave-one-participant-out and must not be quoted.
