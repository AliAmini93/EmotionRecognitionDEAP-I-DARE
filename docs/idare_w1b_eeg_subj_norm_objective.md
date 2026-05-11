# W1B — EEG Subject Normalization Objective

## Branch

`idare/wave1/eeg-subject-normalization`

## Scope

- I-DARE only.
- EEG only.
- Arousal only.
- Within-subject pairwise affect preference ranking.
- Current STIM-BSL summary input fixed.
- Ridge classifier fixed.
- Existing 6-fold subject-held-out structure.
- Maximum 24 registered runs: 4 cells × 6 folds.
- No DEAP.
- No fusion.
- No neural training.
- No rereference/CAR.
- No downsampling rebuild.
- No cache overwrite.

## Scientific Question

Does normalization reduce subject/fold heterogeneity in EEG arousal pairwise signal?

## Registered Cells

| Cell | Normalization | Transductive? | Claim boundary |
|---|---|---:|---|
| B0 | none/current | no | non-transductive comparator |
| B1 | per-subject z-score | yes | diagnostic/calibration-style only |
| B2 | train-fold StandardScaler | no | strict non-transductive |
| B3 | per-subject rank transform | yes | diagnostic/calibration-style only |

B1 and B3 use unlabeled held-out subject feature statistics. They are allowed here only as transductive diagnostics and must not be reported as strict non-transductive results.

## Fixed Reference

`REF-PW-EEG-ARO-001 = 0.5216709095` mean balanced accuracy.

## Primary Diagnostics

- Mean balanced accuracy.
- Delta vs `REF-PW-EEG-ARO-001`.
- Fold-level standard deviation.
- Bimodal fold-pattern reduction via top-3 minus bottom-3 fold balanced-accuracy gap.
- Positive fold count.
- Transductive/non-transductive labeling check.

## Pass Gates

- Moderate pass: any cell mean balanced accuracy >= 0.53.
- Strong pass: any cell mean balanced accuracy >= 0.55.
- Heterogeneity pass candidate: fold stdev and top3-bottom3 fold gap lower than B0/current.

## Intentionally Not Started

- Input-definition ablation.
- Neural training.
- DEAP.
- Fusion.
- Rereference/CAR.
- Downsampling rebuild.
- Cache overwrite.
- Push to main.
