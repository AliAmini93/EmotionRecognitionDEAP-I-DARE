# I-DARE Residual Signal Diagnosis Lock

This note freezes the current diagnosis before/alongside the corrected residual signal reliability audit.

## Core question

After removing the stimulus-only prior, is the remaining residual:

1. learnable and reliable physiological target signal,
2. stable subject-specific bias / calibration structure,
3. stimulus-specific residual structure,
4. or mostly noise?

## Current working decomposition

For LOSO stimulus-only:

```text
y_hat_stimulus_only(s, v) = mean_rating(v, train_subjects excluding s)
residual(s, v) = y(s, v) - y_hat_stimulus_only(s, v)
```

A physiological model is scientifically meaningful only if it predicts this residual/deviation better than stimulus-only.

## Corrected diagnosis

The residual is not pure noise.

However, the reliable part detected so far is mostly subject-structured:

- some subjects systematically rate above/below the stimulus-only prior;
- this appears especially strong for arousal;
- valence has weaker but still non-zero subject-level residual structure.

This means the current negative result should be stated precisely:

```text
NO-GO for current engineered EEG/EMG feature blocks under pure LOSO zero-shot physiology decoding.
Not NO-GO for every possible subject-adaptive physiology setting.
```

## Important artifact warning

Do not interpret split-half `stimulus residual across subjects` from LOSO residuals as scientific stimulus reliability.

Reason:

```text
residual(s, v) = y(s, v) - mean_y(other subjects, v)
```

For a balanced design, residuals are algebraically centered within each stimulus. If subjects are split into two halves, the two half-means for the same stimulus can become near-perfectly anti-correlated. A correlation near `-1` in that calculation is an artifact of the residual definition, not evidence of negative stimulus reliability.

Therefore, the corrected 05z audit:
- does not use stimulus split-half residual reliability in the verdict;
- focuses on subject residual profiles across stimuli;
- marks stimulus residual structure as not supported under the current residual definition.

## Scientific implication

The current evidence suggests that the remaining residual is more compatible with:

```text
subject response style / subject calibration bias / individual affective scale offset
```

than with:

```text
a zero-shot cross-subject physiological residual signal captured by the tested feature blocks
```

## Recommended next test

The correct next test is a few-shot / subject-calibration audit:

```text
05aa: held-out subject, k calibration stimuli, predict residual on remaining stimuli
```

Test values:

```text
k = 1, 2, 4, 8, 16
```

Decision criterion:
- if a tiny amount of subject calibration substantially improves residual prediction, the project should pivot from zero-shot cross-subject decoding to subject-adaptive affect modeling;
- if calibration still fails, residual may be mostly irreducible/noisy under available labels and sensors.
