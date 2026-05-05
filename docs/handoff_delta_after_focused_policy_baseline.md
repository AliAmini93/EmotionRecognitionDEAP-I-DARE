# Handoff Delta - After Focused I-DARE Score-5 Policy Baseline

## What Changed

A focused cache-based EEG baseline was completed and committed.

Latest relevant commit before this delta:

```text
0e063f9 scripts: run focused cache-based I-DARE EEG baseline
```

The focused run compared:

```text
midpoint_as_low
midpoint_as_high
```

for both:

```text
valence
arousal
```

## Decision

Use `midpoint_as_high` as the temporary primary score-5 policy for both valence and arousal.

Keep all three score-5 policies available:

```text
discard_midpoint
midpoint_as_low
midpoint_as_high
```

## Important Interpretation

This is not a final LOSO result. It is a practical near-term preset choice for moving the pipeline forward.

`discard_midpoint` should remain as a supported ablation/sensitivity baseline because dropping score 5 is a defensible and common way to handle neutral/ambiguous affect scores.

## Immediate Next Step

Build or update the cache-based EEG baseline training script so it:

- uses the validated EEG cache,
- defaults to `midpoint_as_high`,
- still accepts `--label-policy discard_midpoint`, `--label-policy midpoint_as_low`, and `--label-policy midpoint_as_high`,
- writes clear reports under `docs/`,
- avoids reading raw MATLAB/HDF5 files during training.
