# Independent Revalidation — Stimulus-Prior Information Audit

Date: 2026-08-22  
Reviewer: independent ChatGPT-side recomputation from the archived candidate package  
Status: **PASS**

## Scope

The candidate package was independently unpacked and checked without importing or executing its analysis module. The verification reconstructed the reported source-only stimulus prior directly from the canonical trial tables and the emitted OOF fold memberships.

The verification covered:

- canonical binary-label rule `<5 -> LOW`, `>5 -> HIGH`, `=5 -> DROP`;
- retained-trial counts and physical-trial uniqueness;
- exact OOF coverage and canonical label/stimulus correspondence;
- source-only Jeffreys-smoothed stimulus priors for every emitted dataset/task/view/repetition;
- hard predictions, fallback logic, pooled metrics, per-fold metrics, subject-macro metrics, and structural-overlap statistics;
- all six primary LOPO conditions;
- exact 10,000-replicate primary participant-cluster bootstrap for all six LOPO conditions;
- exact 10,000-replicate refit-bootstrap sensitivity analysis for all six LOPO conditions;
- exact 10,000-permutation within-participant stimulus-identity null for all six LOPO conditions.

## Result integrity

All 12,862 emitted OOF prediction rows were reconstructed from source-side labels only. The maximum absolute discrepancy from the archived probabilities was at floating-point roundoff:

- stimulus-conditioned probability: `1.11e-16`
- source-global probability: `5.55e-17`

All 280 per-fold metric rows and all 280 structural-overlap rows matched independently recomputed values with no discrepancies above `1e-12`.

All pooled summary metrics matched to floating-point precision. All 10,000-replicate primary bootstrap intervals, all 10,000-replicate refit-sensitivity intervals, and all 10,000-permutation null summaries for the six LOPO conditions reproduced exactly up to floating-point rounding.

## Primary LOPO evidence

| Dataset | Task | Stimulus overlap | Stimulus-only BA | Global-prior BA | Delta BA (pp) | Bits/trial | Permutation p (bits) |
|---|---|---:|---:|---:|---:|---:|---:|
| DEAP | Valence | 1.000 | 0.7395 | 0.5000 | +23.95 | +0.2889 | 1.0e-4 |
| DEAP | Arousal | 1.000 | 0.6190 | 0.5000 | +11.90 | +0.0693 | 1.0e-4 |
| I-DARE | Valence | 1.000 | 0.9559 | 0.5000 | +45.59 | +0.7938 | 1.0e-4 |
| I-DARE | Arousal | 1.000 | 0.7861 | 0.5000 | +28.61 | +0.3031 | 1.0e-4 |
| DEJA-VU | Valence | 0.9467 | 0.8032 | 0.5000 | +30.32 | +0.4234 | 1.0e-4 |
| DEJA-VU | Arousal | 0.9577 | 0.5311 | 0.4342 | +9.69 | -0.0572 | 0.2036 |

The empirical p-value floor with 10,000 permutations is `(0+1)/(10000+1) = 9.999e-5`; manuscript prose should use `p < 10^-4` only if the journal's rounding convention permits it, otherwise report `p = 1.0 x 10^-4` / `p <= 1.0 x 10^-4` with the permutation count stated.

## Uncertainty check

The archived fixed-prediction participant-cluster bootstrap reproduces exactly. The refit-bootstrap sensitivity also reproduces exactly.

A wording qualification is required for DEAP Arousal:

- fixed-prediction bits/trial 95% CI: `[0.0204, 0.1178]`
- refit-sensitivity bits/trial 95% CI: `[-0.0058, 0.1010]`

Therefore a blanket sentence saying that "bootstrap intervals exclude zero in all four DEAP/I-DARE conditions" is only true for the primary fixed-prediction interval and should not be stated without identifying that interval. The stronger, safer G1 prose should rely on complete overlap plus stimulus-only BA; the refit sensitivity can remain in Methods/Results/Supplement.

## Scientific interpretation authorized by this audit

The results support the bounded claim that subject-only cross-validation can leave canonical-stimulus novelty uncontrolled, and that in DEAP and I-DARE the source side contains substantial stimulus-associated prior information about held-out-participant labels.

The results do **not** show that:
- subject-only cross-validation is intrinsically invalid;
- there is sample/data leakage;
- a physiological model necessarily exploits stimulus identity;
- stimulus identity causally determines emotion labels.

DEJA-VU Arousal is a genuine null/counter-example and should remain visible when discussing heterogeneity.

## Package-level archival notes

The candidate contains one `__pycache__/...pyc` file. It is not scientific evidence and should be excluded from the frozen successor package.

The original `FINAL_AUDIT_VALIDATION.json` reports `audit_status=PASS` but does not itself gate on `determinism_result`; `REPRODUCIBILITY_VALIDATION.json` separately records `determinism_result=PASS`. The frozen successor should preserve both original files and add a final freeze gate requiring both conditions, rather than silently rewriting the original generated validation.

## Final decision

**INDEPENDENT_REVALIDATION = PASS**  
**SCIENTIFIC_NUMBERS_CHANGED = false**  
**READY_FOR_VERSIONED_SHARED_FREEZE = true**
