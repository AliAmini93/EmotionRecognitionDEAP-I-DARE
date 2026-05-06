# DEAP EMG Feature-Only Smoke Status Append

## Summary

The DEAP preprocessed Python download and modality audit are now complete enough to support the feature-level EMG-only path.

The full DEAP EMG feature cache was built successfully from zEMG and tEMG channels:

- feature cache: `.cache/deap_emg_features.npy`
- feature index: `.cache/deap_emg_feature_cache_index.csv`
- shape: `[15360, 22]`
- subjects: `32`
- subject-trial pairs: `1280`
- windows per trial: `12`
- feature dim: `22`
- NaN/Inf: `0`
- build status: `PASSED`

The feature set is baseline-corrected, window-level, time-domain EMG features from DEAP preprocessed zEMG/tEMG, not raw waveform training.

## Training Smoke Results

### Valence / midpoint_as_high / feature-level EMG-only

Smoke command used `TinyEMGMLP(feature_dim=22, hidden_dim=64)`, 20 epochs, 2 folds, seed 11, and compared:

- `ce_class_weighted`
- `balanced_sampler_ce`

Aggregate result:

| Recipe | Runs | Macro F1 | Balanced accuracy | Threshold Macro F1 | Threshold Balanced accuracy | One-class runs |
|---|---:|---:|---:|---:|---:|---:|
| ce_class_weighted | 2 | 0.5394 | 0.5454 | 0.5494 | 0.5508 | 0 |
| balanced_sampler_ce | 2 | 0.5245 | 0.5295 | 0.5294 | 0.5294 | 0 |

Interpretation: valence shows weak-to-moderate signal in the feature-level EMG-only path, especially with `ce_class_weighted`, but this is still a smoke result, not a final LOSO estimate.

### Arousal / midpoint_as_high / feature-level EMG-only

Smoke command used the same feature cache and model, but only the arousal task.

Aggregate result:

| Recipe | Runs | Macro F1 | Balanced accuracy | Threshold Macro F1 | Threshold Balanced accuracy | One-class runs |
|---|---:|---:|---:|---:|---:|---:|
| ce_class_weighted | 2 | 0.4908 | 0.4930 | 0.4981 | 0.5002 | 0 |
| balanced_sampler_ce | 2 | 0.4911 | 0.4926 | 0.4911 | 0.4926 | 0 |

Interpretation: arousal does not show useful signal in this small EMG feature-only smoke. The important positive diagnostic is that there is no one-class collapse.

## Decision

Freeze the current DEAP EMG feature-only diagnostic state as follows:

- DEAP preprocessed modality audit: complete.
- DEAP zEMG/tEMG feature-cache builder: smoke-tested and full cache built.
- DEAP EMG feature-only training smoke:
  - valence: promising enough for later fuller LOSO-style evaluation.
  - arousal: weak/near-chance in this smoke.
- Do not claim final DEAP EMG-only performance from these smoke tests.
- Keep raw EMG-only waveform training as a separate ablation, not the main EMG path.
- For the proposal/mainline, feature-level EMG remains the cleaner first EMG representation.

## Related commits

- `159de07` — add DEAP EMG feature cache builder smoke.
- `bc142e8` — record full DEAP EMG feature cache build.
- `a1567a9` — smoke DEAP EMG feature-only valence training.
- `5c62936` — smoke DEAP EMG feature-only arousal training.

## Suggested next step

Add this status summary to the project status documentation, then move to one of:

1. DEAP EEG full cache build and EEG-only smoke, to align DEAP with the I-DARE EEG path.
2. I-DARE EMG feature-cache smoke, to fix the current raw-EMG mismatch against the proposal.
3. A compact cross-dataset status freeze that records what is done and what remains before broader experiments.
