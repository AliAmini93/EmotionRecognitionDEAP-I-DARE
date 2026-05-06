# Adapted Legacy MAHNOB EEG Encoder R0 Plan

## Decision

Keep the old MAHNOB EEG encoder line as an R0 / historical baseline, not as the main model.

## Why

`OldStyleEEGClassifier` is only a wrapper around an already-existing encoder. It is not a full old model by itself. This plan adds a real adapted legacy encoder so that `OldStyleEEGClassifier` can become a meaningful R0 baseline.

## Files Added

- `src/emotion_deap_idare/models/legacy_mahnob_eeg_encoder.py`
- `scripts/24_smoke_idare_eeg_legacy_r0.py`
- `docs/legacy_mahnob_eeg_r0_plan.md`

## Model Meaning

- `legacy_r0`: adapted MAHNOB-family EEG encoder wrapped by `OldStyleEEGClassifier`
- `eeg_segment_v1`: current EEGSegmentClassifier-v1 lite baseline

## Scope

This is a smoke-test step only.

Default smoke:

```bash
python scripts/24_smoke_idare_eeg_legacy_r0.py \
  --cache-npy .cache/idare_eeg_windows_32x640_float32.npy \
  --cache-index .cache/idare_eeg_cache_index.csv \
  --tasks valence \
  --label-policy midpoint_as_high \
  --models legacy_r0 eeg_segment_v1 \
  --recipes ce_class_weighted \
  --folds 6 \
  --seeds 11 \
  --epochs 1 \
  --max-runs 2
```

## Guardrails

- Do not run a full comparison before this smoke passes.
- Do not treat the smoke result as a final model comparison.
- Do not replace `EEGSegmentClassifier-v1` as the main model based on smoke output.
- If the smoke passes, commit the model file, smoke runner, plan, and generated smoke reports after review.

## Expected Outputs

- `docs/idare_eeg_legacy_r0_smoke.md`
- `docs/idare_eeg_legacy_r0_smoke.json`
