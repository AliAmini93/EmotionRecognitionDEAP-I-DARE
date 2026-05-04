# Handoff Delta After I-DARE Window Extraction Smoke Test

## What changed

A real I-DARE signal extraction smoke test was added and passed.

New script:

```text
scripts/07_smoke_idare_window_extraction.py
```

New reports:

```text
docs/idare_window_extraction_smoke_test.md
docs/idare_window_extraction_smoke_test.json
```

Local-only cache output:

```text
.cache/idare_window_smoke_sample.npz
```

Do not commit `.cache` outputs.

---

## Result

The smoke test passed:

```text
Status: PASSED
Sample rows tested: 8
Issues: 0
Warnings: 0
```

The script confirmed that real EEG and EMG windows can be extracted from I-DARE `.mat` files using:

```text
.cache/idare_trial_index.csv
```

---

## Current I-DARE loader assumptions

I-DARE files are MATLAB v7.3 / HDF5 and should be read with `h5py`.

Use Python half-open slicing:

```python
data[int(begin):int(end), :]
```

EEG:

```text
raw sampling rate: 512 Hz
raw orientation: time x channels
raw channels: 38
first implementation channels: first 32
target sampling rate: 128 Hz
target length: 640 samples
target output shape: [32, 640]
```

Important: after resampling, EEG lengths may be slightly different from 640, for example:

```text
638
640
641
```

So the reusable loader must crop/pad to exactly 640.

EMG:

```text
raw sampling rate: 2000 Hz
raw orientation: time x channels
raw channels: 2
main design: feature-level EMG
```

---

## Immediate next step

Create a reusable I-DARE loader/extraction module.

Recommended file:

```text
src/emotion_deap_idare/data/idare_loader.py
```

Recommended validation script:

```text
scripts/08_validate_idare_loader.py
```

The validation script should confirm:

```text
EEG shape: [32, 640]
EMG feature vector exists and has stable length
valence/arousal labels match trial index
score == 5 discard policy is preserved
multiple subjects load successfully
no model training is performed
```
