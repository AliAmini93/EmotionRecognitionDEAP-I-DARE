# Project State Delta After I-DARE EEG Main Baseline

## Current state

The cache-based EEG training path is operational and fast enough for controlled baselines.

The current temporary main I-DARE score-5 policy is:

```text
valence: midpoint_as_high
arousal: midpoint_as_high
```

## Latest baseline

`midpoint_as_high` was evaluated across:

```text
2 tasks
6 subject folds
2 seeds
5 epochs
cache-based EEG windows
```

Aggregate results:

```text
arousal/midpoint_as_high: macro_f1=0.4825, bal_acc=0.5159, best_f1=0.4918, one_class=1/12
valence/midpoint_as_high: macro_f1=0.3953, bal_acc=0.4995, best_f1=0.4566, one_class=4/12
```

## Risk / caveat

This is not a final LOSO experiment. Valence remains unstable and still shows one-class collapse in several runs.

## Next action

Run a compact `discard_midpoint` sanity baseline using the same cache-based infrastructure.
