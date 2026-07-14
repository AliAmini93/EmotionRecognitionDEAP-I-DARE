# DEAP Verified Physical-Trial Manifest Audit

No model training was performed.

## Mapping Resolution

- `.dat` row order: common `Experiment_id` order
- `stimulus_id`: verified `Experiment_id`
- `presentation_order`: participant-specific metadata `Trial`
- Embedded-rating comparisons: `5120`
- Exact-match fraction: `1.000000`
- Maximum absolute error: `0.000000000000`

## Canonical Manifest

- Rows: `1280`
- Grid: `32 subjects × 40 stimuli = 1280`
- Duplicate subject–stimulus cells: `0`
- Chronology-verified rows: `1280`
- Stimulus-identity-verified rows: `1280`
- EEG-available rows: `1280`
- EMG-available rows: `1280`
- Manifest action: `REPLACED_WITH_BACKUP`
- Manifest SHA-256: `c40aa73e17098e17c95c79417176308e2459e1f709fe0f8583b48cfcd659a478`

## Presentation Sequences

- Unique complete sequences: `32` of `32`
- Largest identical-sequence group: `1`
- Mean pairwise same-position fraction: `0.0245`
- Maximum pairwise same-position fraction: `0.1000`
- Unique positions per stimulus, min/median/max: `19/22.0/25`

## Label Counts

| task | policy | retained | midpoints_removed | low | high |
| --- | --- | --- | --- | --- | --- |
| valence | discard_midpoint | 1264 | 16 | 556 | 708 |
| valence | midpoint_as_low | 1280 | 0 | 572 | 708 |
| valence | midpoint_as_high | 1280 | 0 | 556 | 724 |
| arousal | discard_midpoint | 1263 | 17 | 526 | 737 |
| arousal | midpoint_as_low | 1280 | 0 | 543 | 737 |
| arousal | midpoint_as_high | 1280 | 0 | 526 | 754 |

## Decision

- DEAP stimulus-aware manifest: **READY**
- DEAP chronology-aware manifest: **READY**
- DEAP Strict Joint CV construction: **READY**
