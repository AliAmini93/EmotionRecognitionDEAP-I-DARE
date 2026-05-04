# Chat Handoff - Latest

## Project

Cross-subject EEG-EMG emotion recognition on DEAP and I-DARE.

## Main Goal

Evaluate whether auxiliary EMG and trial-aware temporal modeling improve cross-subject EEG emotion recognition.

The current paper focuses on:

```text
within-dataset cross-subject generalization
strict LOSO evaluation
DEAP and I-DARE
```

The current paper version does not include cross-dataset transfer.

---

## Current Phase

Milestone 1 - Dataset acquisition and audit preparation.

Milestone 0 has already been completed.

Current status:

```text
I-DARE first-stage acquisition is complete.
I-DARE files have been downloaded and checksum-verified.
DEAP acquisition is still pending.
```

---

## Important Local Paths

Project root:

```text
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE
```

DEAP root:

```text
/mnt/HDD/AliWorks/DEAP
```

I-DARE root:

```text
/mnt/HDD/AliWorks/I-DARE
```

---

## Current Design

- Main datasets:
  - DEAP
  - I-DARE
- Tasks:
  - binary valence
  - binary arousal
- Evaluation:
  - strict LOSO
  - within-dataset cross-subject
- Main window:
  - 5 seconds
  - no overlap
- DEAP:
  - 60s trial -> 12 non-overlapping 5s windows
- I-DARE:
  - one natural 5s stimulus window
- Current paper version:
  - no cross-dataset transfer

---

## Current Model Plan

Current EEG model files:

```text
src/emotion_deap_idare/models/eeg_segment_encoder.py
src/emotion_deap_idare/models/eeg_segment_classifier.py
src/emotion_deap_idare/models/old_style_eeg_classifier.py
```

Current model status:

```text
EEGSegmentClassifier-v1 lite
GPU smoke test passed
trainable parameters: 337,955
```

Smoke test shapes:

```text
input: [8, 32, 640]
logits: [8, 2]
embedding z: [8, 128]
projection z_proj: [8, 64]
temporal attention: [8, 32, 320]
channel attention: [8, 32]
```

Later planned modules:

```text
EMG feature-level branch
EEG sequence encoder
EMG sequence encoder
segment-level fusion
trial-level modality-specific fusion
contrastive learning ablation
```

Do not implement these yet. Dataset audit comes first.

---

## Critical Decisions

- Dataset files are not tracked by Git.
- `configs/paths.local.yaml` is Git-ignored.
- Storage location accepted for initial phase:
  - `/mnt/HDD/AliWorks/DEAP`
  - `/mnt/HDD/AliWorks/I-DARE`
- DEAP target version:
  - official preprocessed Python version, 128Hz
  - `Data_preprocessed_python.zip`
- EMG main branch:
  - feature-level, not raw waveform
- Fusion location is an experimental question:
  1. segment-level EEG-EMG fusion
  2. modality-specific sequence encoding + trial-level fusion
- Contrastive learning:
  - later ablation only
  - not part of the first training step
- I-DARE main subject set:
  - use 63 common EEG+EMG subjects
  - exclude subject 4 from main EEG+EMG protocol
  - subject 4 may be used only for optional EMG-only secondary analysis

---

## I-DARE Source Listing Status

I-DARE Figshare source listing has been generated.

Listing files:

```text
scripts/list_idare_figshare_files.py
docs/data_sources_idare.md
docs/data_sources_idare.json
docs/data_sources_idare_summary.txt
```

Listing result:

```text
Articles discovered: 5
Files discovered: 263
Total listed size: 6.98 GB
First-stage required files: 133
First-stage required size: 6.88 GB
EEG subjects: 63
EMG subjects: 64
Common EEG+EMG subjects: 63
EMG-only subject: 4
```

---

## I-DARE Download Manifest Status

Manifest files:

```text
scripts/build_idare_download_manifest.py
docs/idare_download_manifest.csv
docs/idare_download_manifest_summary.md
```

Manifest result:

```text
Total listed files: 263
First-stage files: 133
Main-protocol files: 132
First-stage total size: 6.88 GB
Main-protocol total size: 6.85 GB
```

Checksum status:

```text
computed_md5 present for all 133 first-stage files
missing md5 in first-stage files: 0
```

---

## I-DARE Acquisition Status

I-DARE first-stage files have been downloaded and verified.

Downloaded subset:

```text
EEG files
EMG files
label CSV files
metadata CSV files
```

Final verification result:

```text
selected_files: 133
selected_total_size: 6.88 GB
verified_ok: 133
verify_failed: 0
```

Local disk usage:

```text
6.9G /mnt/HDD/AliWorks/I-DARE
```

Final verification report:

```text
docs/idare_download_report.md
```

Acquisition status doc:

```text
docs/idare_acquisition_status.md
```

---

## DEAP Status

DEAP has not been downloaded yet.

Target version:

```text
DEAP official preprocessed Python version
Data_preprocessed_python.zip
128Hz
```

Current open item:

```text
Confirm or request official DEAP access credentials.
```

---

## Immediate Next Step

Create and run the dataset audit script:

```text
scripts/01_audit_datasets.py
```

Audit I-DARE first, because I-DARE has now been downloaded and verified.

The audit should generate:

```text
docs/data_audit_idare.md
```

Do not start training yet.  
Do not implement EMG fusion yet.  
Do not implement sequence modeling yet.  
Do not start contrastive learning yet.

---

## What the I-DARE Audit Must Verify

The I-DARE audit should inspect:

```text
- folder structure
- file counts
- downloaded EEG files
- downloaded EMG files
- label CSV files
- metadata CSV files
- subject IDs
- EEG/EMG subject intersection
- subject 4 handling
- .mat fields
- Fs / sampling rates
- channel names
- data shapes
- time vector shapes
- event_id
- event_begin
- event_end
- feasibility of one 5s stimulus window per event
- alignment between label CSVs and event IDs
```

The audit should not assume channel count, sampling rate, event duration, or `.mat` structure. It must verify them from the downloaded files.
