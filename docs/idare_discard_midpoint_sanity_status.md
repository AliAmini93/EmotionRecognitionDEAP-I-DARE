# I-DARE Discard-Midpoint Sanity Baseline Status

This note records the secondary `discard_midpoint` sanity baseline.

## Result

| Task | Policy | Final macro F1 | Final balanced acc | Best macro F1 | One-class final runs |
|---|---|---:|---:|---:|---:|
| valence | discard_midpoint | 0.3877 | 0.5018 | 0.4280 | 6/12 |
| arousal | discard_midpoint | 0.4202 | 0.5190 | 0.4915 | 1/12 |

## Comparison to Temporary Main Policy

Temporary main policy remains `midpoint_as_high`.

| Task | Main policy macro F1 | Discard-midpoint macro F1 | Decision |
|---|---:|---:|---|
| valence | 0.3953 | 0.3877 | keep midpoint_as_high |
| arousal | 0.4825 | 0.4202 | keep midpoint_as_high |

## Interpretation

`discard_midpoint` is valid as a secondary sanity / ablation candidate, but it does not outperform the current temporary main policy on macro F1.

## Source Report

- `docs/idare_eeg_cache_discard_midpoint_sanity.md`
- `docs/idare_eeg_cache_discard_midpoint_sanity.json`
