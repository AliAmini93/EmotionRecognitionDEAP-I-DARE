# Project State Delta - After I-DARE Policy Multi-Fold Selection

## Current Phase Update

The project has moved from cache validation into short cache-based policy-selection baselines.

## Newly Completed

- Cache-based multi-fold EEG-only policy-selection pilot completed.
- The previous HDF5 bottleneck has been bypassed successfully using the EEG cache.
- Score-5 label policy remains provisional, but the next baseline can be narrowed.

## Current Practical Decision

Use `midpoint_as_low` as the provisional primary score-5 policy for the next short cache-based baseline.

Use `midpoint_as_high` as the secondary comparison policy.

Do not remove `discard_midpoint`; keep it available as a preset.

## Immediate Next Step

Create and run a cache-based short baseline script that focuses on:

```text
Tasks: valence, arousal
Policies: midpoint_as_low, midpoint_as_high
More folds or more subjects than the pilot
Still not full LOSO unless explicitly chosen
```

The goal is to decide whether the model has a usable EEG-only signal before moving to heavier LOSO or multimodal EEG+EMG experiments.
