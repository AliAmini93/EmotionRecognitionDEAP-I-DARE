<!-- NEW_CHAT_START_PROTOCOL_MARKER -->

## New Chat Start Protocol

Before continuing this project in a new chat, follow `docs/new_chat_start_protocol.md`.

Hard rule: every new script/training recipe/experiment runner must start with a smoke test first, such as `--max-runs 2 --epochs 1`, before any full run is proposed.

The new chat must also verify file/context access before claiming it has read project files.

Minimum expected facts:
- Temporary main score-5 policy: `midpoint_as_high`.
- `discard_midpoint` remains a secondary sanity / ablation candidate.
- Main baseline: valence macro F1 `0.3953`, arousal macro F1 `0.4825`.
- Discard-midpoint sanity: valence macro F1 `0.3877`, arousal macro F1 `0.4202`.
- Next technical step: cache-based EEG training-recipe stabilization, smoke-test first.

# Chat Handoff - Latest

## Project

Cross-subject EEG-EMG emotion recognition on DEAP and I-DARE.

## Main Goal

Evaluate whether auxiliary EMG and trial-aware temporal modeling improve cross-subject EEG emotion recognition.

The current paper version focuses on within-dataset cross-subject generalization. Cross-dataset transfer between DEAP and I-DARE is intentionally excluded from the current paper version.

---

## Current Phase

Milestone 1 - Dataset acquisition and audit / I-DARE loader-design preparation.

No training should be started yet.

---

## Local Paths

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

## Environment Status

- Python version: 3.12.3.
- Virtual environment: `.venv`.
- PyTorch with CUDA 12.8 installed.
- GPU detected: NVIDIA GeForce RTX 5090.
- GitHub SSH authentication works.
- Repository has been pushed successfully and is expected to be synced with `origin/main`.

Verify with:

```bash
git status
git log --oneline -5
```

---

## Current Code Status

Current EEG model files:

```text
src/emotion_deap_idare/models/eeg_segment_encoder.py
src/emotion_deap_idare/models/eeg_segment_classifier.py
src/emotion_deap_idare/models/old_style_eeg_classifier.py
```

Main smoke-tested model:

```text
EEGSegmentClassifier-v1 lite
```

Smoke test result:

```text
input: [8, 32, 640]
logits: [8, 2]
embedding z: [8, 128]
projection z_proj: [8, 64]
temporal attention: [8, 32, 320]
channel attention: [8, 32]
trainable parameters: 337,955
GPU smoke test: passed
```

---

## Project Memory Files

Important memory/documentation files:

```text
docs/project_state.md
docs/chat_handoff_latest.md
docs/decision_log.md
docs/proposal_v1_1.md
docs/dataset_acquisition_plan.md
docs/handoff_bundle_latest.md
experiments/registry.csv
```

I-DARE acquisition/audit/probe files:

```text
docs/data_sources_idare.md
docs/data_sources_idare.json
docs/data_sources_idare_summary.txt
docs/idare_download_manifest.csv
docs/idare_download_manifest_summary.md
docs/idare_download_report.md
docs/idare_acquisition_status.md
docs/data_audit_idare.md
docs/data_audit_idare.json
docs/idare_hdf5_structure_probe.md
docs/idare_hdf5_structure_probe.json
docs/idare_mat73_probe.md
docs/idare_mat73_probe.json
docs/idare_refs_and_events_probe.md
docs/idare_refs_and_events_probe.json
docs/idare_trial_index_probe.md
docs/idare_trial_index_probe.json
docs/handoff_delta_after_idare_acquisition.md
docs/handoff_delta_after_trial_index_probe.md
```

Relevant scripts:

```text
scripts/list_idare_figshare_files.py
scripts/build_idare_download_manifest.py
scripts/download_idare_from_manifest.py
scripts/01_audit_datasets.py
scripts/02_probe_idare_hdf5_structure.py
scripts/03_probe_idare_mat73_loader.py
scripts/04_probe_idare_refs_and_events.py
scripts/05_probe_idare_trial_index.py
```

---

## Locked Design Decisions

### Evaluation

- Strict LOSO / subject-held-out evaluation.
- Within-dataset cross-subject evaluation.
- No cross-dataset transfer in the current paper version.

### Tasks

- Binary valence.
- Binary arousal.

Label rule:

```text
label = 1 if score > 5
label = 0 if score < 5
score == 5 is discarded for that task
```

### Windowing

DEAP:

```text
60s trial -> 12 non-overlapping 5s windows
```

I-DARE:

```text
one natural 5s STIM window per emotional stimulus
```

### EMG

- Main EMG path is feature-level, not raw waveform.
- Raw EMG may be considered later as an ablation.

### Fusion

Fusion location remains an experimental question:

```text
1. segment-level EEG-EMG fusion
2. modality-specific sequence encoding + trial-level fusion
```

### Contrastive Learning

Contrastive learning is reserved for later ablation only.

Planned contrastive design:

```text
positive = same emotion label + different subject
hard negative = same stimulus/video + different reported emotion
loss location = trial-level representation, not raw segment level
```

---

## I-DARE Acquisition Status

I-DARE first-stage acquisition is complete.

Downloaded subset:

```text
EEG files: 63
EMG files: 64
Label CSV files: 4
Metadata CSV files: 2
Total files: 133
```

Verification result:

```text
verified_ok: 133
verify_failed: 0
local disk usage: 6.9G
```

Main protocol subject set:

```text
63 common EEG+EMG subjects
subject 4 is EMG-only and excluded from main EEG+EMG protocol
```

---

## I-DARE Dataset Audit Status

Audit script:

```text
scripts/01_audit_datasets.py
```

Audit outputs:

```text
docs/data_audit_idare.md
docs/data_audit_idare.json
```

Current audit result:

```text
Status: PASSED
Issues: 0
Warnings: 0
```

Important observation:

```text
I-DARE .mat files are MATLAB v7.3 / HDF5.
Use h5py.
```

Dependencies now include:

```text
h5py
mat73
```

Note:
`mat73` was useful for probing orientation but raw `h5py` remains the safer loader basis because it preserves direct HDF5 structure and event arrays.

---

## I-DARE Trial Index Findings

Trial-index probe:

```text
scripts/05_probe_idare_trial_index.py
docs/idare_trial_index_probe.md
docs/idare_trial_index_probe.json
```

Main findings:

```text
Stimuli_Specifications.csv rows: 100
I-DARE .mat event_begin/event_end pairs: 100
STIM_* rows: 32
Label stimulus IDs: 32
stim_rows_match_label_stimuli: true
```

Sample subjects checked:

```text
sbj_P_01
sbj_P_02
sbj_P_03
```

For all three sampled subjects:

```text
stim_rows_count: 32
labeled_stim_rows_count: 32
all_labeled_stim_eeg_4p5_to_5p5: true
all_labeled_stim_emg_4p5_to_5p5: true
```

I-DARE loader interpretation:

```text
Use only STIM_* rows as emotional trials.
Strip STIM_ prefix to match label CSV stimulus IDs.
Use row order in Stimuli_Specifications.csv as event order.
Read data with h5py.
Raw h5py data orientation is time x channels.
EEG Fs = 512Hz.
EMG Fs = 2000Hz.
```

Decision added:

```text
D005 - Use STIM events as I-DARE emotional trials
```

---

## DEAP Status

DEAP is not downloaded yet.

Planned DEAP starting point:

```text
DEAP preprocessed Python version
Data_preprocessed_python.zip
```

DEAP access/credentials still need confirmation.

---

## Immediate Next Step

Refresh project state and handoff files after the I-DARE trial-index probe, then implement the I-DARE trial index builder.

The next coding target should produce a clean table with one row per subject-stimulus emotional trial.

Do not train models yet.

---

## Next Practical Coding Target

Create an I-DARE trial index builder, likely something like:

```text
scripts/06_build_idare_trial_index.py
```

Expected output candidates:

```text
data/idare_trial_index.csv       # likely gitignored if under data/
docs/idare_trial_index_summary.md
```

Because dataset-derived tables may reveal dataset contents and may become large later, decide before committing whether the generated trial-index CSV should be tracked or gitignored.

Minimum trial-index columns:

```text
subject_id
subject_col
stimulus_id
raw_event_name
event_index_1based
eeg_file
emg_file
eeg_begin
eeg_end
eeg_duration_sec
emg_begin
emg_end
emg_duration_sec
valence_score
arousal_score
valence_label_gt5
arousal_label_gt5
valence_is_discard_score5
arousal_is_discard_score5
quadrant_gs
quadrant_subject
```

After the trial index is built, validate label counts for valence/arousal before any training.
