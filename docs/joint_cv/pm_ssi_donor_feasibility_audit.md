# PM-SSI Legal Donor-Pool Feasibility Audit

No EEG/EMG representation or model was trained.

## Legal Donor Rule

For every source-training physical-trial anchor, the donor must be in the same source-train region, have the same binary class, come from a different subject and a different stimulus, have paired EEG+EMG, and be a different physical trial.

No primary-test or diagnostic-test trial is allowed to act as a donor.

## Primary Repetition, Discard-Midpoint Policy

| dataset | task | anchors | min | p10 | median | p90 | max | zero_rate | below_5_rate | below_20_rate | min_unique_subjects | min_unique_stimuli | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEAP | arousal | 11367 | 230 | 257.0 | 361.0 | 400.0 | 424 | 0.0 | 0.0 | 0.0 | 23 | 29 | PASS_STRONG |
| DEAP | valence | 11376 | 249 | 264.0 | 334.0 | 387.0 | 412 | 0.0 | 0.0 | 0.0 | 23 | 26 | PASS_STRONG |
| I-DARE | arousal | 16191 | 254 | 319.0 | 536.0 | 627.0 | 679 | 0.0 | 0.0 | 0.0 | 41 | 21 | PASS_STRONG |
| I-DARE | valence | 15003 | 348 | 368.0 | 432.0 | 468.0 | 515 | 0.0 | 0.0 | 0.0 | 46 | 14 | PASS_STRONG |

## Dataset Decisions

### DEAP

- Verdict: **PM_SSI_DONOR_SUPPORT_STRONG**
- Primary discard-midpoint maximum zero-donor rate: `0.000000`
- Primary discard-midpoint minimum legal donors: `230`
- Worst minimum over all policies and repetitions: `209`

### I-DARE

- Verdict: **PM_SSI_DONOR_SUPPORT_STRONG**
- Primary discard-midpoint maximum zero-donor rate: `0.000000`
- Primary discard-midpoint minimum legal donors: `254`
- Worst minimum over all policies and repetitions: `236`

## Interpretation Boundary

- This audit establishes availability, not usefulness.
- Donor labels are used only inside source training.
- The donor cannot share the anchor subject or stimulus.
- A later implementation must sample donors only after the outer split is fixed.
- Hyperparameters must not be tuned on repetitions 1–4.

## Next Step

After reviewing this donor-capacity result, audit LRSC-TTA chronological stream feasibility for both datasets using the verified presentation order and frozen folds.
