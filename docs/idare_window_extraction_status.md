# I-DARE Window Extraction Smoke-Test Status

## Status

I-DARE real signal window extraction smoke test is complete.

The smoke test was performed using:

```text
scripts/07_smoke_idare_window_extraction.py
```

The script generated:

```text
docs/idare_window_extraction_smoke_test.md
docs/idare_window_extraction_smoke_test.json
.cache/idare_window_smoke_sample.npz
```

The `.cache` output is local-only and should not be committed.

---

## Final Result

The smoke test result was:

```text
Status: PASSED
Sample rows tested: 8
Issues: 0
Warnings: 0
```

This confirms that real I-DARE EEG and EMG windows can be extracted from the downloaded `.mat` files using the trial index.

---

## Inputs

The smoke test used the generated I-DARE trial index:

```text
.cache/idare_trial_index.csv
```

The trial index was produced by:

```text
scripts/06_build_idare_trial_index.py
```

Trial index summary:

```text
Rows: 2016
Subjects: 63
Trials per subject: 32
Unique stimuli: 32
```

---

## Slicing Convention

The selected working slicing convention is:

```python
data[int(begin):int(end), :]
```

Interpretation:

```text
Use raw begin/end values as Python half-open slices.
```

Reason:

```text
This gives sample_count = end - begin, matching the duration stored in .cache/idare_trial_index.csv.
```

The MATLAB 1-based inclusive interpretation gives one extra sample and is not the current working convention.

---

## EEG Extraction Finding

I-DARE EEG files use:

```text
Sampling rate: 512 Hz
Data orientation after h5py loading: time x channels
Number of raw EEG channels in files: 38
```

The current model expects:

```text
32 EEG channels
128 Hz
5 seconds
640 samples
```

Therefore, the I-DARE EEG loader should:

```text
1. Read data as time x channels.
2. Slice the STIM window with Python half-open indexing.
3. Select the first 32 EEG channels for the first implementation.
4. Resample from 512 Hz to 128 Hz.
5. Enforce fixed length of 640 samples using crop/pad.
6. Return EEG as channels x time: [32, 640].
```

---

## Important Length Observation

After resampling, sample lengths can vary slightly because I-DARE STIM events are close to, but not always exactly, 5.000 seconds.

Observed examples:

```text
638 samples
640 samples
641 samples
```

Therefore, the final loader must not assume that resampling alone gives exactly 640 samples.

Working policy:

```text
After resampling to 128 Hz, center-crop or zero-pad to exactly 640 samples.
```

---

## EMG Extraction Finding

I-DARE EMG files use:

```text
Sampling rate: 2000 Hz
Data orientation after h5py loading: time x channels
Number of EMG channels: 2
```

The main project design uses feature-level EMG, not raw waveform EMG.

Therefore, the I-DARE EMG loader should:

```text
1. Read data as time x channels.
2. Slice the same STIM window using Python half-open indexing.
3. Extract window-level EMG features.
4. Store features as tabular/numeric vectors for model input.
```

Candidate EMG features remain:

```text
RMS
MAV
Waveform length
Zero crossing rate
Log-energy
Mean frequency
Median frequency
```

---

## Label Handling

The existing project label rule remains:

```text
label = 1 if score > 5 else 0
score == 5 is discarded
```

The smoke test confirmed that labels from the I-DARE trial index are attached to real signal windows.

---

## Current Loader-Design Status

The following are now established for I-DARE:

```text
I-DARE acquisition: complete
I-DARE checksum verification: complete
I-DARE audit: passed
I-DARE trial index: built
I-DARE real signal extraction smoke test: passed
```

Next implementation step:

```text
Create the real reusable I-DARE loader/extraction module.
```

Recommended next script/module:

```text
src/emotion_deap_idare/data/idare_loader.py
```

Recommended next validation script:

```text
scripts/08_validate_idare_loader.py
```

No model training should start until the reusable loader is implemented and validated.
