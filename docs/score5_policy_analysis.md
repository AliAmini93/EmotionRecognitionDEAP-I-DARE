# Score-5 Policy Analysis for I-DARE Binary Labels

## Context

The current project label rule is:

```text
label = 1 if score > 5 else 0
score == 5 is discarded
```

This document explains why `score == 5` is currently discarded in the main binary preset, how much I-DARE data is affected, and which ablations should remain available.

---

## Why Score 5 Was Discarded

I-DARE valence/arousal ratings use a 1--9 score scale. In a binary high/low setup, score `5` is the midpoint.

For a clean binary target:

```text
1,2,3,4 -> low
6,7,8,9 -> high
5       -> neutral / ambiguous midpoint
```

The reason for discarding score `5` in the current main preset is not that the data is bad. The reason is that score `5` is not clearly high or low. Keeping it in one binary class would inject neutral trials into a low/high classifier.

---

## I-DARE Drop Rate from Score-5 Discard

The current I-DARE trial index has:

```text
63 subjects
32 STIM trials per subject
2016 total subject-trial rows
```

### Valence

```text
score == 5 rows: 349 / 2016
drop rate: 17.31%
rows after discard: 1667
binary label counts after discard:
  class 0: 812
  class 1: 855
```

### Arousal

```text
score == 5 rows: 217 / 2016
drop rate: 10.76%
rows after discard: 1799
binary label counts after discard:
  class 0: 1112
  class 1: 687
```

---

## What Happens If Score 5 Is Kept as Class 0?

If score `5` is treated as class `0`, the rule becomes:

```text
label = 1 if score > 5 else 0
```

This preserves all rows, but class 0 becomes "low or neutral" rather than cleanly low.

### Valence with Score 5 as Class 0

```text
class 0: 812 + 349 = 1161
class 1: 855
total: 2016
class 0 fraction: 57.59%
class 1 fraction: 42.41%
```

### Arousal with Score 5 as Class 0

```text
class 0: 1112 + 217 = 1329
class 1: 687
total: 2016
class 0 fraction: 65.92%
class 1 fraction: 34.08%
```

This gives more data, but it changes the semantic meaning of class 0 and increases imbalance, especially for arousal.

---

## Recommended Policy

Use configurable presets rather than hard-coding one irreversible policy.

### Preset A - Main Binary Protocol

```text
name: discard_midpoint
low:  score < 5
high: score > 5
drop: score == 5
```

Use this as the first main protocol because it is the cleanest high-vs-low binary definition.

### Preset B - Sensitivity / Ablation

```text
name: midpoint_as_low
low:  score <= 5
high: score > 5
drop: none
```

Use this as an ablation to test whether keeping neutral/midpoint samples changes results.

### Preset C - Strong-Label Ablation

```text
name: strong_labels_only
low:  score <= 3
high: score >= 7
drop: score in {4,5,6}
```

Use this later if we want cleaner labels at the cost of a much smaller dataset.

### Preset D - 3-Class Task

```text
name: ternary_low_neutral_high
low:     score < 5
neutral: score == 5
high:    score > 5
```

This is not recommended for the first baseline because the current model and evaluation plan are binary, but it may be useful later.

---

## Current Recommendation

For the immediate EEG-only smoke test and first controlled baseline smoke path:

```text
Use discard_midpoint as the main preset.
Do not treat score == 5 as a final settled scientific choice.
Keep midpoint_as_low as a planned sensitivity ablation.
```

This gives us a clean baseline first, while preserving the option to test the alternative label policy explicitly.
