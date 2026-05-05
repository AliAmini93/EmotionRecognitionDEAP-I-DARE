# I-DARE Loader Status

## Status

I-DARE loader validation is complete and passed.

The loader was added at:

```text
src/emotion_deap_idare/datasets/idare_loader.py
src/emotion_deap_idare/datasets/__init__.py
```

The validation script was added at:

```text
scripts/08_validate_idare_loader.py
```

The validation reports were generated at:

```text
docs/idare_loader_validation.md
docs/idare_loader_validation.json
```

No model training was performed.

---

## Validated Design

The loader validates the following working design:

```text
Main subject set: 63 common EEG+EMG subjects
Trial unit: one I-DARE emotional STIM_* event
Label rule: label = 1 if score > 5 else 0
Discard rule: score == 5 is discarded separately for each task
Signal slicing: start at event_begin and extract exactly 5.0 seconds
```

EEG design:

```text
Source sampling rate: 512 Hz
Selected channels: first 32 channels
Downsampling: take every 4th sample
Target sampling rate: 128 Hz
Output tensor shape: [32, 640]
```

EMG design:

```text
Source sampling rate: 2000 Hz
Channels: 2
Output tensor shape: [2, 10000]
```

Normalization:

```text
Per-window, per-channel z-normalization is enabled by default for EEG and EMG.
```

---

## Validation Result

Validation command:

```bash
python scripts/08_validate_idare_loader.py
```

Observed result:

```text
Status: PASSED
Issues: 0
Warnings: 0
```

Task-level results:

```text
valence:
  rows after score==5 discard: 1667
  subjects: 63
  label counts:
    0: 812
    1: 855

arousal:
  rows after score==5 discard: 1799
  subjects: 63
  label counts:
    0: 1112
    1: 687
```

Batch smoke-test result:

```text
EEG batch shape: [4, 32, 640]
EMG batch shape: [4, 2, 10000]
Label batch shape: [4]
EEG finite check: true
EMG finite check: true
```

Checked item result:

```text
EEG item shape: [32, 640]
EMG item shape: [2, 10000]
All checked tensors finite
Per-window z-normalization produces near-zero mean and near-unit standard deviation
```

---

## Current Interpretation

The I-DARE data path is now loader-ready for the first EEG-only baseline smoke test.

This does not mean full training should start immediately. The next controlled step should be a small EEG-only forward/batch smoke test using the validated loader and the existing `EEGSegmentClassifier-v1`.

---

## Recommended Next Step

Run a small I-DARE EEG-only model-forward smoke test:

```text
I-DARE loader -> EEG batch [B, 32, 640] -> EEGSegmentClassifier-v1 -> logits [B, 2]
```

The smoke test should verify:

```text
DataLoader works
EEG tensor shape is correct
Labels are correct
Model forward pass works
Loss computation works
One optimizer step works
No NaN/Inf appears
No full training is performed
```
