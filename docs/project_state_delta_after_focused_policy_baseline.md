# Project State Delta - After Focused I-DARE Score-5 Policy Baseline

## Newly Completed

- Focused cache-based I-DARE EEG baseline completed.
- Focused run favored `midpoint_as_high` over `midpoint_as_low` for both valence and arousal.
- Temporary primary label policy selected:
  - `valence`: `midpoint_as_high`
  - `arousal`: `midpoint_as_high`

## Policy Status

Current supported policies:

```text
discard_midpoint
midpoint_as_low
midpoint_as_high
```

Current temporary primary policy:

```text
midpoint_as_high
```

Secondary candidate:

```text
midpoint_as_low
```

Retained ablation / sensitivity baseline:

```text
discard_midpoint
```

## Current Goal

Move from policy-selection pilots to a proper cache-based EEG baseline using the temporary primary policy while keeping policy choice configurable.

## Next Practical Step

Create or update the next cache-based EEG baseline script with:

```text
--label-policy midpoint_as_high
```

as the default, while preserving CLI support for:

```text
discard_midpoint
midpoint_as_low
midpoint_as_high
```

The script should not read raw I-DARE `.mat` files during training. It should use:

```text
.cache/idare_eeg_windows_32x640_float32.npy
.cache/idare_eeg_cache_index.csv
```
