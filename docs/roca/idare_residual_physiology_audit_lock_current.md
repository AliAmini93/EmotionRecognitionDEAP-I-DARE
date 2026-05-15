# I-DARE Residual Physiology Audit Lock

This note freezes the current methodological decisions before building the next audit scripts.

## Current objective

Primary objective is not merely to improve leaderboard numbers.

Primary objective:
- determine whether EEG/EMG contains cross-subject physiological signal beyond stimulus-only prior;
- quantify residual physiological value after removing stimulus/stimulus-mean effects;
- only then decide whether model/architecture optimization is scientifically justified.

## Dataset target

Current target dataset:
- I-DARE only.

DEAP stimulus-only LOSO was used as external sanity/context, not the immediate modeling target.

## Current known stimulus-only problem

Stimulus-only prior is strong enough that raw accuracy can be misleading.

Therefore future physiological models must be evaluated against:
- stimulus-only baseline;
- residual prediction over train-subject stimulus mean;
- per-subject failure/success deltas;
- not just pooled accuracy.

## Existing I-DARE EMG assets

Detected local cache assets:

- `.cache/idare_emg_features.npy`: `(2016, 22)` float32
- `.cache/idare_emg_features_smoke.npy`: `(2016, 22)` float32
- `.cache/idare_emg_bsl_stats.npy`: `(2016, 22)` float32
- `.cache/idare_emg_bsl_stats_smoke.npy`: `(64, 22)` float32
- `.cache/idare_raw_emg_windows_2x10000_float32.npy`: `(2016, 2, 10000)` float32
- `.cache/idare_raw_emg_windows_2x10000_float32_smoke.npy`: `(64, 2, 10000)` float32
- `.cache/roca_idare_emg_expanded_features.npy`: `(2016, 812)` float32

Important caveat:
- `idare_emg_features_smoke.npy` has shape `(2016, 22)`, so despite the name it may not be a smoke subset. Must verify before using.

## Existing EMG feature status

Initial grep showed classical time-domain features such as:
- rms
- mav
- iemg
- waveform_length
- zero_crossings
- slope_sign_changes
- log_variance

But actual feature dimension is 22, so feature-name mapping must be audited before claiming exact coverage.

Do not rebuild existing classical EMG features blindly.

## Candidate physiological feature families still worth auditing

### EEG

1. Bandpower
   - delta/theta/alpha/beta/gamma or dataset-appropriate frequency bands
   - absolute and relative power
   - train-fold normalization only

2. Asymmetry
   - frontal/hemispheric asymmetry if channel pairing is known
   - log-power left-right differences
   - avoid arbitrary pairs unless explicitly documented

3. Complexity / entropy
   - Hjorth activity/mobility/complexity
   - sample entropy or approximate entropy if computationally feasible
   - line length / zero-crossing-like temporal complexity
   - fractal dimension only if stable and not too noisy

4. Covariance / Riemannian
   - per-trial EEG covariance
   - tangent-space features or stable covariance summaries
   - must be fold-safe

5. Connectivity
   - coherence / PLV / correlation features only if computationally controlled
   - likely secondary after simpler covariance/bandpower audit

### EMG

Existing 22-dim and expanded 812-dim features must be audited first.

Potential additional EMG features only if not already present:
- envelope statistics
- burst count / burst duration / burst amplitude
- frequency-domain features
- entropy/complexity
- Hjorth/fractal
- early/mid/late temporal segmentation

## Mandatory next step

Before building physiological feature models, run:

`scripts/roca/05v_idare_label_variance_decomposition.py`

Purpose:
- quantify how much label variance is explained by stimulus;
- quantify subject effect;
- quantify residual variance left after stimulus prior;
- compute target-specific residual ceiling/space for valence and arousal.

Expected outputs:
- `docs/roca/idare_label_variance_decomposition_current.md`
- `docs/roca/idare_label_variance_decomposition_current.json`
- `docs/roca/idare_label_variance_decomposition_current.csv`

## Step after 05v

If residual variance is non-trivial, build:

`scripts/roca/05w_idare_residual_physiology_feature_audit.py`

This should test feature blocks against stimulus-only, not raw score prediction alone.

Candidate blocks:
- existing EMG 22-dim
- EMG baseline stats 22-dim
- EMG expanded 812-dim
- raw EMG derived complexity/envelope/burst if not duplicated
- EEG bandpower
- EEG asymmetry
- EEG entropy/complexity
- EEG covariance/Riemannian
- late fusion of stimulus-only + physiological residual prediction

## Go / no-go criteria

A physiological feature/model is only interesting if it improves stimulus-only consistently, not accidentally.

Required reporting:
- pooled RMSE lift vs stimulus-only
- balanced accuracy lift vs stimulus-only
- AUROC lift vs stimulus-only
- residual/deviation RMSE lift
- residual correlation / dev_pearson
- subject-level win/loss count
- worst-subject regressions
- bootstrap or fold/subject-level uncertainty where feasible

Preliminary practical criterion:
- average improvement must be positive;
- subject-level wins should exceed losses meaningfully;
- worst regressions should not be large enough to make deployment/scientific claim fragile;
- improvement must appear in residual metrics, not only thresholded accuracy.

## Methodological warning

Do not interpret high accuracy as physiological decoding unless stimulus-only is beaten.

Do not claim EEG/EMG cross-subject value from raw valence/arousal accuracy alone.

Do not optimize architecture blindly before measuring residual physiological signal.
