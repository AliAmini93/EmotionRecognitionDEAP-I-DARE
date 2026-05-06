# I-DARE EMG Feature-Only Smoke Status

## Status

Frozen after successful I-DARE EMG feature-cache build and feature-only training smokes.

This document records the current interpretation before moving to raw EMG-only ablation or EEG+EMG fusion.

## Inputs

- Feature cache: `.cache/idare_emg_features.npy`
- Feature index: `.cache/idare_emg_feature_cache_index.csv`
- Cache build report:
  - `docs/idare_emg_feature_cache_build_report.md`
  - `docs/idare_emg_feature_cache_build_report.json`

## Feature Cache

The full I-DARE EMG feature cache was built from raw I-DARE EMG HDF5/MAT files using the trial index.

- rows: `2016`
- subjects: `63`
- feature_dim: `22`
- channels: `emg_ch1`, `emg_ch2`
- feature policy: baseline-corrected EMG time-domain features
- baseline source: preceding BSL event inferred from `event_index_0based - 1`
- baseline correction: subtract preceding BSL per-channel mean
- NaN count: `0`
- Inf count: `0`

## Feature Columns

Each EMG channel contributes 11 time-domain features:

- mean
- std
- rms
- mav
- iemg
- waveform_length
- zero_crossings
- slope_sign_changes
- min
- max
- log_variance

Total feature dimension: `2 x 11 = 22`.

## Training Smoke Scope

Training was run with:

- model: `TinyEMGMLP(feature_dim=22, hidden_dim=64)`
- label policy: `midpoint_as_high`
- recipes:
  - `ce_class_weighted`
  - `balanced_sampler_ce`
- folds: `6`
- seed: `11`
- epochs: `20`
- max_runs per task: `4`

Reports:

- Valence:
  - `docs/idare_emg_feature_valence_training_smoke.md`
  - `docs/idare_emg_feature_valence_training_smoke.json`
  - `docs/idare_emg_feature_valence_training_smoke_predictions.csv`
- Arousal:
  - `docs/idare_emg_feature_arousal_training_smoke.md`
  - `docs/idare_emg_feature_arousal_training_smoke.json`
  - `docs/idare_emg_feature_arousal_training_smoke_predictions.csv`

## Valence Smoke Result

Aggregate over two folds:

| Recipe | Runs | Macro F1 | Balanced accuracy | Final accuracy | One-class runs | Majority accuracy |
|---|---:|---:|---:|---:|---:|---:|
| ce_class_weighted | 2 | 0.5004 | 0.5083 | 0.5156 | 0 | 0.6065 |
| balanced_sampler_ce | 2 | 0.4776 | 0.4935 | 0.5511 | 0 | 0.6065 |

Interpretation:

- Valence feature-only EMG is stable enough to run.
- It does not collapse.
- It does not yet show strong signal.
- `ce_class_weighted` is the better smoke recipe.

## Arousal Smoke Result

Aggregate over two folds:

| Recipe | Runs | Macro F1 | Balanced accuracy | Final accuracy | One-class runs | Majority accuracy |
|---|---:|---:|---:|---:|---:|---:|
| ce_class_weighted | 2 | 0.5223 | 0.5319 | 0.5327 | 0 | 0.5838 |
| balanced_sampler_ce | 2 | 0.5065 | 0.5130 | 0.5142 | 0 | 0.5838 |

Interpretation:

- Arousal is slightly more promising than valence for I-DARE EMG feature-only.
- No one-class collapse was observed.
- `ce_class_weighted` is again the better smoke recipe.
- The result is still a smoke/stabilization result, not a final LOSO experiment.

## Current Decision

Use `ce_class_weighted` as the temporary preferred recipe for I-DARE EMG feature-only follow-up.

Do not claim feature-level EMG is strong yet. The safe claim is:

> I-DARE EMG feature-only is now integrated, cache-backed, and trainable without collapse in short subject-held-out smokes; arousal shows slightly better smoke behavior than valence.

## Next Step

The next ablation should test raw EMG-only against this feature-level EMG-only path.

Recommended next implementation order:

1. Build an I-DARE raw EMG cache smoke.
2. Run raw EMG-only training smoke for valence and arousal.
3. Compare raw EMG-only vs feature EMG-only.
4. Only after that, move to EEG+EMG fusion smoke.

## Guardrails

- Keep feature-level EMG as the proposal-aligned main EMG path.
- Keep raw EMG-only as an ablation.
- Do not mix raw EMG and feature EMG in the same baseline until both paths are individually smoke-tested.
- Do not treat these smoke results as final LOSO results.
