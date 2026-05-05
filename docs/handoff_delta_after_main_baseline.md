# Handoff Delta After I-DARE EEG Main Baseline

## Added / confirmed

- `scripts/18_run_idare_eeg_cache_main_baseline.py`
- `docs/idare_eeg_cache_main_baseline.md`
- `docs/idare_eeg_cache_main_baseline.json`
- `docs/idare_eeg_main_baseline_status.md`

## Current temporary main policy

`midpoint_as_high` for both valence and arousal.

## Current interpretation

This is a cache-based subject-fold baseline, not final LOSO.

Current aggregate:

```text
arousal/midpoint_as_high: macro_f1=0.4825, bal_acc=0.5159, best_f1=0.4918, one_class=1/12
valence/midpoint_as_high: macro_f1=0.3953, bal_acc=0.4995, best_f1=0.4566, one_class=4/12
```

Arousal is more promising than valence. Valence still has one-class-collapse risk.

## Immediate next step

Run a secondary `discard_midpoint` cache-based sanity baseline, then decide whether to tune the training recipe or start a stricter LOSO protocol.
