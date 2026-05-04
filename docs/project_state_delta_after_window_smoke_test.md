# Project State Delta After I-DARE Window Extraction Smoke Test

## Add to Completed

- I-DARE window extraction smoke test added and passed:
  - `scripts/07_smoke_idare_window_extraction.py`
  - `docs/idare_window_extraction_smoke_test.md`
  - `docs/idare_window_extraction_smoke_test.json`

Smoke test result:

```text
Status: PASSED
Sample rows tested: 8
Issues: 0
Warnings: 0
```

## Add to Current Findings

I-DARE extraction convention:

```text
Use raw event begin/end values as Python half-open slices:
data[int(begin):int(end), :]
```

I-DARE EEG loader findings:

```text
Raw EEG sampling rate: 512 Hz
Raw EEG orientation: time x channels
Raw EEG channels: 38
Initial channel policy: first 32 channels
Target model sampling rate: 128 Hz
Target model length: 640 samples
Target model shape: [32, 640]
```

Important EEG fixed-length note:

```text
Resampling may produce lengths such as 638, 640, or 641.
The final loader must crop/pad to exactly 640 samples.
```

I-DARE EMG loader findings:

```text
Raw EMG sampling rate: 2000 Hz
Raw EMG orientation: time x channels
Raw EMG channels: 2
Main design: feature-level EMG, not raw EMG deep branch
```

## Replace / Update Next Practical Step

Previous next step:

```text
Build and validate I-DARE trial index.
```

New next step:

```text
Create reusable I-DARE loader/extraction module.
```

Recommended files:

```text
src/emotion_deap_idare/data/idare_loader.py
scripts/08_validate_idare_loader.py
```

Do not start model training yet.
