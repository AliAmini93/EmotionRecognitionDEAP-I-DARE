# I-DARE Score-5 Policy Selection Status - D011

## Status

Focused cache-based score-5 policy selection is complete for the current EEG-only pilot stage.

The temporary primary score-5 policy is:

```text
midpoint_as_high
```

This applies to both:

```text
valence
arousal
```

---

## Policies to Keep

All three policies remain supported:

```text
discard_midpoint
midpoint_as_low
midpoint_as_high
```

Do not delete or deprecate `discard_midpoint`.

---

## Current Interpretation

`midpoint_as_high` is promoted only as a temporary primary preset because the focused cache baseline favored it for both valence and arousal.

However, balanced accuracy remains close to chance in several runs, especially for valence. Therefore, the decision is not final and should not be treated as a publication-level conclusion.

---

## Why Keep `discard_midpoint`

`discard_midpoint` is still valuable because:

- It is a defensible affect-classification convention when score 5 is treated as neutral or ambiguous.
- It helps compare against prior binary-affect setups.
- It gives a sensitivity check for whether results depend heavily on score-5 handling.
- It may become useful again after model, split, or preprocessing changes.

---

## Recommended Near-Term Default

Use:

```text
midpoint_as_high
```

as the default policy for the next cache-based EEG baseline.

Keep the policy configurable through CLI/config, for example:

```bash
--label-policy midpoint_as_high
```

and continue supporting:

```bash
--label-policy discard_midpoint
--label-policy midpoint_as_low
--label-policy midpoint_as_high
```

---

## Next Step

Update the next training script so that:

1. It trains from the validated EEG cache.
2. It defaults to `midpoint_as_high`.
3. It exposes `--label-policy` as an explicit argument.
4. It can still run `discard_midpoint` and `midpoint_as_low` as follow-up baselines.
