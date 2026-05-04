# Handoff Bundle - Latest

This file is a complete project handoff bundle for continuing the project in a new chat.

Generated from local repository files.


## How to Use This File in a New Chat


Copy and paste this whole file into the first message of a new chat and say:

"Please continue the EmotionRecognitionDEAP-I-DARE project from this handoff bundle. First summarize the current state, then continue from the immediate next step. Do not jump into training before dataset acquisition and audit."

---




# FILE: docs/next_chat_prompt.md


# Prompt for Continuing This Project in a New Chat

We are continuing the project:

Cross-Subject EEG-EMG Emotion Recognition with Trial-Aware Temporal Modeling on DEAP and I-DARE.

GitHub repo:
https://github.com/AliAmini93/EmotionRecognitionDEAP-I-DARE

Local project root:
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE

Local dataset folders:
/mnt/HDD/AliWorks/DEAP
/mnt/HDD/AliWorks/I-DARE

Important:
The dataset folders currently exist but are empty. DEAP and I-DARE have not been downloaded yet.

Please first read these project memory files:
- docs/project_state.md
- docs/chat_handoff_latest.md
- docs/decision_log.md
- docs/proposal_v1_1.md
- experiments/registry.csv

Current completed status:
- Milestone 0 is completed.
- Proposal V1.1 and the complete handoff bundle have been committed and pushed.
- Repository is expected to be synced with `origin/main` at the time of handoff.
- To verify the latest commit, run `git status` and `git log --oneline -5`.
- Repository scaffold exists and was pushed to GitHub.
- SSH authentication with GitHub works.
- Python virtual environment exists at .venv.
- PyTorch with CUDA 12.8 is installed.
- GPU detected: NVIDIA GeForce RTX 5090.
- EEGSegmentClassifier-v1 was smoke-tested successfully on GPU.
- Smoke test shapes:
  - input: [8, 32, 640]
  - logits: [8, 2]
  - embedding z: [8, 128]
  - projection z_proj: [8, 64]
  - temporal attention: [8, 32, 320]
  - channel attention: [8, 32]
- EEGSegmentClassifier-v1 lite has 337,955 trainable parameters.

Current model files:
- src/emotion_deap_idare/models/eeg_segment_encoder.py
- src/emotion_deap_idare/models/eeg_segment_classifier.py
- src/emotion_deap_idare/models/old_style_eeg_classifier.py

Current proposal file:
- docs/proposal_v1_1.md

Current proposal decisions:
- Main datasets: DEAP and I-DARE.
- Main evaluation: within-dataset cross-subject / strict LOSO.
- Current paper version does not include cross-dataset transfer.
- Main tasks: binary valence and binary arousal.
- Label rule: label = 1 if score > 5 else 0; score == 5 is discarded.
- Main DEAP windowing: 60s trial -> 12 non-overlapping 5s windows.
- Main I-DARE windowing: one natural 5s stimulus window.
- EEG model starts with EEGSegmentClassifier-v1.
- EMG will initially be feature-level, not raw waveform.
- Fusion location is an experimental question:
  1. segment-level EEG-EMG fusion
  2. modality-specific sequence encoding followed by trial-level fusion
- Contrastive learning is a later ablation.
- Contrastive design:
  - positive = same emotion label + different subject
  - hard negative = same stimulus/video + different reported emotion
  - apply contrastive loss at trial-level representation, not raw segment level.

Immediate next step:
Begin Milestone 1 - Dataset acquisition and audit preparation.

Before downloading or coding, clarify:
1. Is /mnt/HDD acceptable even though it is not a separate mount?
2. Should DEAP start from the preprocessed 128Hz version?
3. What exact I-DARE release/files are available?
4. Are dataset access/permissions ready?

Do not jump into training yet. First:
1. Decide exact DEAP version to download.
2. Decide exact I-DARE version/files to download.
3. Download datasets into the local dataset folders.
4. Create scripts/01_audit_datasets.py.
5. Generate:
   - docs/data_audit_deap.md
   - docs/data_audit_idare.md
6. Verify EEG/EMG availability, sampling rates, channel names, labels, and file structures.

Important local issue:
/mnt/HDD is currently not a separate mount. It is on the root filesystem. There is around 500GB free space, but before downloading large datasets, confirm whether this is acceptable.



# FILE: docs/project_state.md


# Project State

## Current Phase

Milestone 1 - Dataset acquisition and audit / I-DARE loader-design preparation.

## Current Goal

Finish the I-DARE dataset audit path by turning the verified acquisition and trial-index probes into a clean I-DARE trial index builder / loader design.

No model training should be started before dataset audit reports and loader assumptions are finalized.

---

## Completed

- Git installed.
- GitHub repository cloned locally.
- SSH authentication with GitHub works.
- Local dataset folders created:
  - `/mnt/HDD/AliWorks/DEAP`
  - `/mnt/HDD/AliWorks/I-DARE`
- Python version checked:
  - Python 3.12.3
- Project scaffold created.
- Virtual environment created at:
  - `.venv`
- PyTorch installed with CUDA 12.8 support.
- GPU detected successfully:
  - NVIDIA GeForce RTX 5090
- Three EEG model files added:
  - `src/emotion_deap_idare/models/eeg_segment_encoder.py`
  - `src/emotion_deap_idare/models/eeg_segment_classifier.py`
  - `src/emotion_deap_idare/models/old_style_eeg_classifier.py`
- `EEGSegmentClassifier-v1` GPU smoke test passed.
- Model parameter count:
  - `EEGSegmentClassifier-v1 lite`: 337,955 trainable parameters.
- Working proposal V1.1 added:
  - `docs/proposal_v1_1.md`
- Dataset acquisition plan added:
  - `docs/dataset_acquisition_plan.md`
- Complete handoff bundle exists:
  - `docs/handoff_bundle_latest.md`

---

## I-DARE Source Listing Completed

I-DARE Figshare source listing completed:

```text
scripts/list_idare_figshare_files.py
docs/data_sources_idare.md
docs/data_sources_idare.json
docs/data_sources_idare_summary.txt
```

I-DARE source listing result:

```text
Articles discovered: 5
Files discovered: 263
Total listed size: 6.98 GB
First-stage required files: 133
First-stage required size: 6.88 GB
Common EEG+EMG subjects: 63
EMG-only subject excluded from main protocol: subject 4
```

---

## I-DARE Download Manifest Completed

I-DARE download manifest generated:

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

Checksum metadata was added:

```text
computed_md5 present for all 133 first-stage files
missing md5 in first-stage files: 0
```

---

## I-DARE Acquisition Completed

I-DARE first-stage files downloaded and verified:

```text
Downloaded file count: 133
Verified files: 133
Verification failures: 0
Local disk usage: 6.9G
```

Relevant files:

```text
scripts/download_idare_from_manifest.py
docs/idare_download_report.md
docs/idare_acquisition_status.md
docs/handoff_delta_after_idare_acquisition.md
```

Local I-DARE root:

```text
/mnt/HDD/AliWorks/I-DARE
```

Observed folder structure:

```text
/mnt/HDD/AliWorks/I-DARE
/mnt/HDD/AliWorks/I-DARE/labels
/mnt/HDD/AliWorks/I-DARE/metadata
/mnt/HDD/AliWorks/I-DARE/raw_downloads
/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG
/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG
```

---

## I-DARE Dataset Audit Completed

I-DARE dataset audit script added and executed:

```text
scripts/01_audit_datasets.py
docs/data_audit_idare.md
docs/data_audit_idare.json
```

Audit result after adding `h5py` support:

```text
Status: PASSED
Issues: 0
Warnings: 0
```

Important loader observation:

```text
I-DARE `.mat` files are MATLAB v7.3 / HDF5 files.
They should be read with `h5py`.
```

Dependency added:

```text
h5py
```

---

## I-DARE Structure and Trial-Index Probes Completed

The following probes were created:

```text
scripts/02_probe_idare_hdf5_structure.py
docs/idare_hdf5_structure_probe.md
docs/idare_hdf5_structure_probe.json

scripts/03_probe_idare_mat73_loader.py
docs/idare_mat73_probe.md
docs/idare_mat73_probe.json

scripts/04_probe_idare_refs_and_events.py
docs/idare_refs_and_events_probe.md
docs/idare_refs_and_events_probe.json

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

For each sampled subject:

```text
stim_rows_count: 32
labeled_stim_rows_count: 32
all_labeled_stim_eeg_4p5_to_5p5: true
all_labeled_stim_emg_4p5_to_5p5: true
```

---

## Current I-DARE Loader Design Decision

Use only `STIM_*` rows as emotional trials.

Do not use `BSL_*` or `SAM_*` rows as emotion-classification samples.

Map labels by stripping the `STIM_` prefix:

```text
STIM_3053 -> 3053
STIM_Dog_18 -> Dog_18
```

Use the row order in `Stimuli_Specifications.csv` as the event order for `event_begin` and `event_end`.

Candidate loader design:

```text
1. Load `.mat` files with `h5py`.
2. Use raw h5py data orientation:
   - EEG: time x channels
   - EMG: time x channels
3. Use the 63 common EEG+EMG subjects for the main protocol.
4. For each subject:
   - read EEG file,
   - read EMG file,
   - read `Stimuli_Specifications.csv`,
   - keep only `STIM_*` rows,
   - extract matching EEG and EMG event windows,
   - attach valence and arousal scores from label CSV files.
5. Apply binary label rule:
   - score > 5 -> 1
   - score < 5 -> 0
   - score == 5 -> discard for that specific task
6. EEG will later be resampled from 512Hz to 128Hz.
7. EMG will be converted to feature-level descriptors.
```

Decision registered in:

```text
docs/decision_log.md
```

Decision ID:

```text
D005 - Use STIM events as I-DARE emotional trials
```

---

## DEAP Status

DEAP has not been downloaded yet.

Expected first DEAP target:

```text
DEAP preprocessed Python version
Data_preprocessed_python.zip
```

DEAP local folder:

```text
/mnt/HDD/AliWorks/DEAP
```

DEAP access/credentials still need to be confirmed or requested.

---

## Current Git Status at Last Check

Repository was pushed successfully and is expected to be synced with `origin/main` at the time of handoff.

To verify the latest commit, run:

```bash
git status
git log --oneline -5
```

---

## In Progress

- Preparing I-DARE trial index builder / loader implementation.
- DEAP acquisition is still pending.

---

## Next Steps

1. Update and commit this project-state / handoff refresh.
2. Regenerate `docs/handoff_bundle_latest.md`.
3. Implement an I-DARE trial index builder.
4. Generate a clean machine-readable I-DARE trial index table.
5. Validate label counts after applying:
   - valence: score > 5 / score < 5 / score == 5 discard
   - arousal: score > 5 / score < 5 / score == 5 discard
6. Continue DEAP access/download process.
7. Download DEAP preprocessed Python archive:
   - `Data_preprocessed_python.zip`
8. Extend `scripts/01_audit_datasets.py` to audit DEAP after download.
9. Generate:
   - `docs/data_audit_deap.md`

---

## Current Open Questions

- Are official DEAP access credentials ready?
- Has `Data_preprocessed_python.zip` been downloaded from the official DEAP source?
- Should the first I-DARE loader output include only metadata/trial index, or also extracted `.npz` windows?
- Which exact EEG channels from I-DARE should be used in the first model input after inspecting channel metadata?
- How should I-DARE EEG channel set be harmonized with DEAP later?

## Last Updated

2026-05-04



# FILE: docs/chat_handoff_latest.md


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



# FILE: docs/decision_log.md


# Decision Log

## D001 - Use 5-second windows as the main protocol

Date: 2026-05-04

Decision:
Use 5-second non-overlapping windows as the main segmentation strategy.

Reason:
- DEAP 60s trials become 12 windows.
- I-DARE stimulus blocks are naturally 5s.
- Avoids inflated results from overlap in the main protocol.

Status:
Accepted.

---

## D002 - Keep EMG feature-level in the main model

Date: 2026-05-04

Decision:
Use window-level EMG features and a shared MLP instead of a raw EMG branch in the main model.

Reason:
- DEAP and I-DARE have mismatched EMG muscle channels.
- Feature-level harmonization is lower risk.
- Raw EMG can be tested later as an ablation.

Status:
Accepted.

---

## D003 - Treat fusion location as an experimental question

Date: 2026-05-04

Decision:
Do not assume one fusion strategy is best. Compare:
1. Segment-level EEG-EMG fusion.
2. Modality-specific sequence encoding followed by trial-level fusion.

Reason:
- DEAP labels are trial-level.
- EEG and EMG may have different temporal dynamics.
- Fusion location may affect representation quality.

Status:
Accepted.

---

## D004 - Use common EEG+EMG subject set for main I-DARE experiments

Date: 2026-05-04

Decision:
Use the 63 subjects that have both EEG and EMG files for the main I-DARE experiments.

Reason:
The I-DARE Figshare source listing found:
- EEG files: 63 subjects
- EMG files: 64 subjects
- Common EEG+EMG subjects: 63
- EMG-only subjects: [4]

For fair EEG-only, EMG-only, and EEG+EMG comparisons, the main protocol should use the same subject set across all conditions.

Subject 4 has EMG but no EEG, so it should be excluded from the main EEG+EMG protocol. It may be kept only for optional EMG-only secondary analysis.

Status:
Accepted.
# Decision Log Update — I-DARE Trial Index and Loader Design

Append the following decision to `docs/decision_log.md`.

---

## D005 - Use STIM events as I-DARE emotional trials

Date: 2026-05-04

Decision:
For the main I-DARE protocol, use only `STIM_*` rows from `Stimuli_Specifications.csv` as emotional stimulus trials.

Use the row order of `Stimuli_Specifications.csv` as the event order corresponding to `event_begin` and `event_end` arrays in each subject `.mat` file.

For labels, strip the `STIM_` prefix and match the remaining stimulus ID to `Valence_SAM.csv` and `Arousal_SAM.csv`.

Reason:
The I-DARE trial-index probe found:
- `Stimuli_Specifications.csv` has 100 rows.
- Each sampled subject `.mat` file has 100 event begin/end pairs.
- There are exactly 32 `STIM_*` rows.
- Label CSV files contain exactly 32 matching stimulus IDs after removing the `STIM_` prefix.
- `stim_rows_match_label_stimuli = true`.
- Sample subjects 1, 2, and 3 each have:
  - 32 `STIM_*` rows,
  - 32 labeled stimulus rows,
  - EEG stimulus durations between approximately 4.984s and 5.002s,
  - EMG stimulus durations between approximately 4.986s and 5.004s.
- Non-stimulus rows such as `BSL_*` and `SAM_*` should not be used as emotional trials.

Implementation implications:
- Load I-DARE `.mat` files with `h5py`.
- Treat raw `h5py` data orientation as `time x channels`.
- EEG sampling rate is 512Hz.
- EMG sampling rate is 2000Hz.
- Use one natural stimulus window per `STIM_*` event.
- Resample EEG from 512Hz to 128Hz later for model input.
- Extract feature-level EMG descriptors from the corresponding EMG stimulus window.
- Apply the project label rule:
  - label = 1 if score > 5
  - label = 0 if score < 5
  - score == 5 is discarded for that task

Status:
Accepted.
---

## D006 - Build I-DARE trial index before signal window extraction

Date: 2026-05-04

Decision:
Build a reproducible I-DARE trial index as an intermediate artifact before implementing EEG/EMG signal window extraction or training.

The trial index is generated by:

```text
scripts/06_build_idare_trial_index.py
```

Outputs:

```text
.cache/idare_trial_index.csv
docs/idare_trial_index_summary.md
docs/idare_trial_index_summary.json
```

Reason:
The I-DARE files are MATLAB v7.3/HDF5 files and the experiment structure must be mapped carefully before loaders are finalized. The trial index creates one row per subject × emotional stimulus trial and records:
- subject ID
- stimulus ID
- raw event name
- event index
- EEG/EMG file paths
- EEG/EMG sampling rates
- EEG/EMG begin/end samples
- EEG/EMG trial durations
- valence/arousal scores
- binary labels using `score > 5`
- discard flags for `score == 5`
- quadrant labels

Accepted trial-index result:
- rows: 2016
- subjects: 63
- trials per subject: 32
- unique stimuli: 32
- EEG duration range: 4.982421875 to 5.064453125 seconds
- EMG duration range: 4.985 to 5.067 seconds
- issues: 0
- warnings: 0

Label summary:
- Valence:
  - total rows: 2016
  - score == 5 discarded rows: 349
  - rows after discard: 1667
  - binary 0 count: 812
  - binary 1 count: 855
- Arousal:
  - total rows: 2016
  - score == 5 discarded rows: 217
  - rows after discard: 1799
  - binary 0 count: 1112
  - binary 1 count: 687

Status:
Accepted.

---

## D007 - Use Python half-open slicing and fixed-length EEG windows for I-DARE

Date: 2026-05-04

Decision:
Use raw I-DARE event begin/end values as Python half-open slices:

```python
data[int(begin):int(end), :]
```

For EEG, resample each STIM window from 512 Hz to 128 Hz and then enforce exactly 640 samples using crop/pad.

Reason:
The I-DARE window extraction smoke test passed with this slicing convention. It gives:

```text
sample_count = end - begin
```

which matches the duration stored in `.cache/idare_trial_index.csv`.

The MATLAB 1-based inclusive interpretation gives one extra sample and is not the current working convention.

Observed resampled EEG lengths can be slightly different from 640 because the I-DARE STIM durations are close to, but not always exactly, 5.000 seconds. The smoke test observed examples such as:

```text
638
640
641
```

Therefore, resampling alone is not enough. The loader must apply a deterministic fixed-length policy.

Current fixed-length policy:
- EEG raw window: slice with Python half-open indexing.
- EEG channel selection: first 32 channels for the first implementation.
- EEG resampling: 512 Hz to 128 Hz.
- EEG final length: crop/pad to exactly 640 samples.
- EEG output shape: `[32, 640]`.

For EMG, keep the main feature-level design:
- slice the same STIM window,
- keep raw 2-channel EMG only long enough to compute features,
- do not build a raw EMG deep branch in the main first implementation.

Status:
Accepted.



# FILE: docs/proposal_v1_1.md


# Working Proposal — Version V1.1

## Provisional Title

**Cross-Subject EEG–EMG Emotion Recognition with Trial-Aware Temporal Modeling: A Controlled Study on DEAP and I-DARE**

---

## Version Scope

This document is the working proposal for the current project stage. It extends the initial EEG-only segment model into a complete experimental plan for:

1. **EEG-only cross-subject baselines**
2. **Feature-level EMG modeling**
3. **Trial-aware temporal modeling**
4. **EEG–EMG fusion at different representation levels**
5. **Affective-response-aware contrastive learning as a later, controlled ablation**

The paper version described here focuses on **within-dataset cross-subject generalization** on DEAP and I-DARE.  
**Cross-dataset transfer between DEAP and I-DARE is intentionally excluded from the current paper version** to keep the experimental story controlled.

---

# 1. Motivation and Research Problem

Cross-subject EEG emotion recognition is difficult because EEG signals vary strongly across individuals. These variations are caused by many factors, including:

- neural and anatomical differences,
- electrode impedance and placement variability,
- fatigue and attention,
- subject-specific emotional response patterns,
- recording noise and physiological artifacts.

In emotion recognition, the label is not simply a property of the stimulus. It is a property of the **subjective affective response**. The same stimulus can evoke different emotional responses in different participants. Therefore, a cross-subject model must generalize across people without erasing the fact that emotional responses are individually variable.

DEAP and I-DARE were selected because both provide EEG and EMG recordings. This makes them suitable for studying whether peripheral muscular activity can complement EEG in emotion recognition.

The core questions are:

1. Does EMG improve EEG-based cross-subject emotion recognition?
2. Does trial-aware temporal modeling improve performance when labels are provided at the trial level?
3. Where should EEG and EMG be fused: at the segment level or after modality-specific trial-level sequence encoding?
4. Can contrastive learning improve generalization if it is designed around affective response rather than stimulus identity?

---

# 2. Main Research Questions

## RQ1 — Contribution of EMG

Does adding EMG as an auxiliary modality improve cross-subject emotion recognition compared with EEG-only models?

## RQ2 — Contribution of Trial-Aware Temporal Modeling

For DEAP, does modeling the sequence of twelve 5-second segments inside each 60-second trial improve performance compared with independent segment-level classification?

## RQ3 — Interaction Between EMG and Sequence Modeling

If temporal sequence encoding is added, does EMG still provide additional value?

## RQ4 — Best Fusion Location

Should EEG and EMG be fused at every 5-second segment, or should each modality first build its own trial-level sequence representation before information fusion?

## RQ5 — Contrastive Learning for Cross-Subject Generalization

Can an affective-response-aware supervised contrastive objective improve cross-subject generalization?

This question is treated as a **later ablation**, not part of the first baseline model. The reason is that contrastive learning can easily be misdesigned in emotion recognition if positive and negative pairs are constructed from stimulus identity alone.

---

# 3. Current Locked Decisions

## 3.1 Datasets

Main datasets:

- **DEAP**
- **I-DARE**

Current evaluation setting:

- **within-dataset cross-subject evaluation**
- strict **LOSO** or subject-held-out evaluation
- no cross-dataset transfer in the current paper version

Dataset storage paths:

```text
DEAP:   /mnt/HDD/AliWorks/DEAP
I-DARE: /mnt/HDD/AliWorks/I-DARE
```

Dataset files must not be committed to Git.

---

## 3.2 Tasks

Main tasks:

- binary valence classification
- binary arousal classification

Label harmonization:

```python
label = 1 if score > 5 else 0
score == 5 -> discard
```

Rationale:

- both DEAP and I-DARE use valence/arousal ratings compatible with a midpoint-based low/high split,
- score 5 is ambiguous and may increase label noise,
- removing midpoint samples gives a cleaner binary task.

The same protocol must be applied consistently across folds.

---

## 3.3 Evaluation Protocol

Main evaluation protocol:

```text
Strict LOSO
```

For each fold:

```text
test_subject = one held-out subject
validation_subjects = subset of remaining training subjects
train_subjects = all other subjects
```

Strict rules:

1. No window, trial, or feature from the test subject may enter training or validation.
2. Normalization statistics must be computed only from training subjects.
3. Early stopping must use validation subjects only.
4. Hyperparameter choices must not be based on test fold results.
5. For DEAP, trial-level and segment-level results must be reported separately.

---

# 4. Windowing Protocol

## 4.1 DEAP

Main windowing:

```text
60s trial -> 12 windows × 5s
stride = 5s
overlap = 0
```

Rationale:

- DEAP provides trial-level labels for 60-second trials.
- 5-second windows create a manageable sequence length of 12.
- No overlap avoids inflated sample counts and reduces the risk of overly correlated training samples.

Ablation options:

```text
4s windows
5s windows
6s windows
50% overlap only as a later ablation
```

The main result should use **5s non-overlapping windows**.

---

## 4.2 I-DARE

Main windowing:

```text
5s stimulus block -> 1 window
```

Rationale:

- I-DARE naturally contains 5-second stimulus blocks.
- Therefore, the main sequence-modeling claim should not be made on I-DARE unless later subwindowing is explicitly introduced.

Possible later ablation:

```text
5s block -> five 1s subwindows
```

This is not part of the main protocol.

---

# 5. EEG Modeling

## 5.1 Current EEG Segment Encoder

The current EEG model is `EEGSegmentClassifier-v1`, which contains:

```text
EEG window [B, C, T]
-> multi-branch temporal stem
-> depthwise/grouped TCN
-> temporal attention pooling
-> channel position embedding
-> channel self-attention
-> channel attention pooling
-> EEG embedding
-> classifier
```

Default input for 5-second windows:

```text
C = 32
sampling_rate = 128 Hz
T = 640
```

Default configuration:

```python
window_sec = 5.0
sampling_rate = 128
modelsize = "lite"
stem_fusion = "concat"
channel_pos_mode = "learnable"
channel_mixer = "mha"
norm_kind = "gn"
use_spectral_branch = False
```

Current smoke-test result:

```text
EEGSegmentClassifier-v1 lite
Input: [8, 32, 640]
Logits: [8, 2]
Embedding: [8, 128]
Projection: [8, 64]
Trainable parameters: 337,955
GPU smoke test: passed on NVIDIA GeForce RTX 5090
```

---

## 5.2 Why the EEG Encoder Was Modified

The previous conference model was designed for continuous valence regression on MAHNOB-HCI. For the current project, the model is adapted for:

- binary classification,
- 4/5/6-second EEG windows,
- modular temporal kernel sizes,
- multi-scale temporal extraction,
- optional spectral features,
- channel position embeddings,
- channel-level attention,
- future sequence modeling.

The goal is to keep the encoder compact but stronger than a plain EEGNet-style baseline.

---

## 5.3 EEG Spectral Branch

The spectral branch is optional and disabled in the main model.

If enabled, spectral features are computed outside the model:

```text
x_spec: [B, C, num_bands]
```

Possible bands:

```text
delta
theta
alpha
beta
gamma
```

Main decision:

```text
use_spectral_branch = False
```

Reason:

- first establish a raw/minimally processed EEG baseline,
- avoid adding too many variables before the first DEAP runs,
- later test raw-only vs raw+spectral as an ablation.

---

# 6. EMG Modeling

## 6.1 Why EMG Requires a Conservative Design

DEAP and I-DARE do not provide perfectly matched EMG channels.

Typical situation:

```text
DEAP:
    zEMG + tEMG

I-DARE:
    zygomaticus + corrugator
```

Only part of the EMG setup is semantically aligned across datasets. A raw waveform EMG branch may overfit to:

- muscle identity,
- amplitude scaling,
- electrode placement,
- recording protocol,
- dataset-specific preprocessing.

Therefore, the main EMG design should not assume strict anatomical equivalence between all EMG channels.

---

## 6.2 Main EMG Decision

Main EMG representation:

```text
feature-level EMG
```

Not main:

```text
raw EMG waveform branch
```

Raw EMG can be added later as an ablation, but the main model should use robust window-level features.

---

## 6.3 EMG Window-Level Features

For each EMG channel and each 5-second window:

```text
1. RMS
2. MAV
3. Waveform Length
4. Zero Crossing Rate
5. Log-energy
6. Mean Frequency
7. Median Frequency
```

Input shape:

```text
x_emg_feat: [B, N_emg, F]
```

Default:

```text
N_emg = 2
F = 7
```

For DEAP:

```text
12 windows per trial -> [B, 12, N_emg, 7]
```

For I-DARE:

```text
1 stimulus window -> [B, 1, N_emg, 7]
```

---

## 6.4 Channel-Shared EMG Encoder

To reduce dependence on channel identity, each EMG channel is passed through the same MLP:

```text
x_emg_feat: [B, N_emg, 7]

shared MLP per channel:
    Linear(7, 32)
    LayerNorm
    GELU
    Dropout
    Linear(32, d_emg)

attention pooling over EMG channels:
    [B, N_emg, d_emg] -> [B, d_emg]
```

Advantages:

- compatible with DEAP and I-DARE,
- low parameter count,
- avoids assuming that DEAP tEMG and I-DARE corrugator are equivalent,
- gives interpretable EMG channel attention scores.

---

## 6.5 EMG-Only Baselines

Required baselines:

```text
E0: EMG-only segment classifier
E1: EMG-only trial attention model
E2: EMG-only tiny TCN sequence model
```

Purpose:

- determine whether EMG has standalone predictive signal,
- determine whether EMG contributes only when fused with EEG,
- prevent overclaiming the value of EMG.

---

# 7. Trial-Aware Sequence Modeling

## 7.1 Why Sequence Modeling Is Needed

DEAP labels are assigned at the trial level. If each 5-second segment is classified independently, each segment receives the trial label even though the emotional response may vary across the trial.

This creates weak supervision:

```text
trial label -> copied to all segments
```

A better approach is:

```text
60s trial
-> 12 windows
-> 12 segment embeddings
-> trial sequence encoder
-> trial-level prediction
```

The final prediction should be trial-level.

---

## 7.2 EEG Sequence Encoder Options

Candidate encoders:

```text
S0: mean pooling
S1: temporal attention pooling
S2: lightweight TCN + attention pooling
S3: BiGRU + attention pooling
S4: lightweight Transformer
S5: Mamba / SSM only if sequence length increases
```

Default candidate:

```text
S2: lightweight TCN + attention pooling
```

Reason:

- DEAP sequence length is only 12,
- TCN has useful temporal inductive bias,
- fewer parameters than BiGRU or Transformer,
- less likely to overfit than self-attention on small EEG datasets.

---

## 7.3 EMG Sequence Encoder Options

Because EMG is low-dimensional and potentially noisy, the EMG sequence encoder should remain small.

Candidate encoders:

```text
M0: temporal attention pooling
M1: tiny TCN + attention pooling
M2: small GRU
```

Default candidate:

```text
M0: temporal attention pooling
```

Ablation:

```text
M1: tiny TCN + attention pooling
```

---

# 8. EEG–EMG Fusion

Fusion is treated as an experimental design axis, not a fixed assumption.

Two competing hypotheses:

```text
H1: EEG and EMG should be fused at every 5-second segment.
H2: EEG and EMG should first build modality-specific trial-level sequence representations, then be fused.
```

---

## 8.1 Segment-Level Fusion

In segment-level fusion, EEG and EMG are fused at each 5-second window:

```text
for each segment t:
    EEG_t -> z_eeg_t
    EMG_t -> z_emg_t
    fuse(z_eeg_t, z_emg_t) -> z_fused_t

DEAP:
    [z_fused_1, ..., z_fused_12]
    -> shared sequence encoder
    -> trial prediction

I-DARE:
    z_fused_1
    -> classifier
```

Advantages:

- simpler,
- fewer parameters,
- directly models simultaneous EEG–EMG information.

Limitations:

- assumes EEG and EMG are temporally aligned in each 5-second window,
- may be less suitable if EMG is delayed or sparse.

---

## 8.2 Modality-Specific Sequence Encoding + Trial-Level Fusion

In trial-level fusion, each modality first builds its own temporal representation:

```text
EEG:
    [EEG_1, ..., EEG_12]
    -> EEG segment encoder
    -> EEG sequence encoder
    -> h_eeg_trial

EMG:
    [EMG_1, ..., EMG_12]
    -> EMG segment encoder
    -> EMG sequence encoder
    -> h_emg_trial

Fusion:
    fuse(h_eeg_trial, h_emg_trial)
    -> classifier
```

Advantages:

- each modality can learn its own dynamics,
- more consistent with DEAP trial-level labels,
- better handles sparse or delayed EMG responses.

Limitations:

- more parameters,
- EMG branch can overfit if the sequence encoder is too large.

---

## 8.3 Fusion Operators

Two operators should be tested:

```text
1. concat + MLP
2. gated fusion
```

Gated fusion:

```text
g = sigmoid(MLP([z_eeg, z_emg]))
z = g * z_eeg + (1 - g) * z_emg
```

For segment-level fusion:

```text
z_eeg = z_eeg_t
z_emg = z_emg_t
```

For trial-level fusion:

```text
z_eeg = h_eeg_trial
z_emg = h_emg_trial
```

Gate diagnostics should be reported:

```text
mean gate value
gate distribution
per-subject gate behavior
gate behavior for valence vs arousal
```

---

# 9. Contrastive Learning Design

## 9.1 Why Contrastive Learning Needs Careful Design

A naive contrastive objective can be harmful in emotion recognition.

Incorrect assumption:

```text
same stimulus -> same emotion
```

This is not always true. A stimulus may evoke different emotional responses in different subjects. Therefore, stimulus identity alone should not define positive pairs.

Correct principle:

```text
contrastive pairs should reflect affective response, not only stimulus identity
```

The goal is not to make all responses to the same video identical.  
The goal is to make representations more consistent across subjects **when the affective label is similar**, while preserving differences when subjects report different emotions.

---

## 9.2 Where to Apply Contrastive Loss

Contrastive loss should be applied to:

```text
trial-level representation
```

Not the raw segment representation.

Reason:

- DEAP labels are trial-level.
- segment labels are weak labels copied from the trial.
- trial-level representation better matches the semantic level of the emotion label.

Possible representations:

```text
EEG-only trial model:
    h_trial

EEG+EMG segment-level fusion model:
    h_fused_trial

EEG+EMG modality-specific sequence model:
    h_fused_trial after EEG/EMG trial-level fusion
```

The contrastive projection head should receive the same representation used by the classifier, or a detached copy depending on the ablation.

---

## 9.3 Projection Head

A small projection head maps trial embeddings to the contrastive space:

```text
h_trial -> projection head -> z_proj
```

Example:

```text
LayerNorm(D)
Linear(D, 128)
GELU
Linear(128, 64)
L2 normalize
```

Output:

```text
z_proj: [B, 64]
```

Classification uses `h_trial`, not necessarily `z_proj`.

---

## 9.4 Main Contrastive Pair Definition

For binary valence or arousal:

```text
positive pair:
    same emotion label
    different subject

negative pair:
    different emotion label
```

This encourages subject-invariant representations for the same affective class.

Important constraint:

```text
positive pairs should preferably come from different subjects
```

Reason:

- same-subject positives may encourage subject-specific clustering,
- the goal is cross-subject generalization.

---

## 9.5 Optional Continuous-Rating Constraint

If continuous scores are retained before binarization, positives can be made stricter:

```text
positive pair:
    same binary label
    different subject
    absolute score difference <= delta
```

Example:

```text
abs(score_i - score_j) <= 1.0
```

This is optional and should be tested only after the simpler label-based SupCon is stable.

---

## 9.6 Hard Negative Definition

A useful hard negative is:

```text
same stimulus/video
different reported emotion label
```

This is important because it prevents the model from collapsing stimulus identity into emotion identity.

Example:

```text
subject A watches video k -> high valence
subject B watches video k -> low valence
```

These two samples should not be pulled together simply because the stimulus is the same.

This can be implemented as:

1. normal supervised contrastive loss with labels,
2. optional hard-negative weighting for same-stimulus/different-label pairs.

---

## 9.7 SupCon Loss

For a batch of projected normalized embeddings:

```text
z_i = normalized projection of sample i
```

Similarity:

```text
sim(i, j) = z_i dot z_j / temperature
```

For each anchor `i`, positives are:

```text
P(i) = {j | y_j == y_i and subject_j != subject_i}
```

Loss:

```text
L_i = - 1 / |P(i)| * sum_{p in P(i)}
      log exp(sim(i,p)) / sum_{a != i} exp(sim(i,a))
```

Total:

```text
L_supcon = mean_i L_i
```

Samples with no valid positives in the batch should be skipped for the contrastive part.

---

## 9.8 Total Training Objective

Baseline:

```text
L_total = L_CE
```

Contrastive ablation:

```text
L_total = L_CE + lambda_contrastive * L_supcon
```

Optional later regularization:

```text
L_total = L_CE + lambda_contrastive * L_supcon + lambda_vrex * L_vrex
```

Default starting values:

```text
temperature = 0.07
lambda_contrastive = 0.1 or 0.3
projection_dim = 64
```

Small grid:

```text
temperature: [0.07, 0.1]
lambda_contrastive: [0.1, 0.3, 0.5]
projection_dim: [64]
```

The grid must remain small to avoid tuning-driven results.

---

## 9.9 Batch Construction for Contrastive Learning

Contrastive learning requires careful batch composition.

A regular random batch may not contain enough cross-subject positive pairs.

Recommended sampler:

```text
subject-balanced label-balanced sampler
```

Batch should ideally contain:

```text
multiple subjects
both emotion classes
at least 2 subjects per class
```

Example for binary classification:

```text
batch_size = 64

32 samples high label
32 samples low label

within each label:
    samples drawn from multiple subjects
```

For DEAP trial-level contrastive learning:

```text
batch item = one trial representation
```

For segment-level training, contrastive should not be activated unless segments are aggregated to trial-level first.

---

## 9.10 Contrastive Learning Ablation Plan

Contrastive learning should not be added before the baseline architecture is stable.

Ablation order:

```text
C0: CE only
C1: CE + SupCon with same-label/different-subject positives
C2: CE + SupCon + continuous-rating constraint
C3: CE + SupCon + hard-negative weighting
C4: CE + SupCon + VREx
```

Minimum required comparison:

```text
C0 vs C1
```

Only if C1 improves or behaves reasonably should C2–C4 be tested.

---

## 9.11 What Contrastive Learning Should Not Do

The contrastive design should not:

1. pull all samples from the same video together,
2. force all subjects to respond identically to the same stimulus,
3. use test-subject statistics,
4. operate on heavily overlapping windows in the main result,
5. dominate CE loss with a large lambda,
6. be tuned based on test fold performance.

---

## 9.12 Reporting Contrastive Results

For contrastive experiments, report:

```text
Accuracy
Macro-F1
Balanced Accuracy
Per-subject performance
Mean ± std across LOSO folds
Wilcoxon signed-rank test vs CE-only
UMAP/t-SNE before and after SupCon
Subject clustering score if possible
Class separation score if possible
```

Diagnostic question:

```text
Does SupCon reduce subject clustering while preserving emotion separation?
```

This is more important than only showing a small accuracy gain.

---

# 10. Domain Generalization Regularization

VREx or GroupDRO can be tested after baseline and SupCon are stable.

The subject can be treated as the domain:

```text
domain = subject
```

VREx intuition:

```text
encourage similar risk across training subjects
```

Possible objective:

```text
L_total = mean_subject CE_subject + lambda_vrex * variance_subject(CE_subject)
```

This should be a later ablation because:

- it changes training dynamics,
- it depends on subject-balanced batches,
- it may interact with SupCon.

Suggested ablation:

```text
CE
CE + VREx
CE + SupCon
CE + SupCon + VREx
```

---

# 11. Model Variants

## M0 — EEG-Only Segment Baseline

```text
EEG 5s window
-> EEGSegmentClassifier-v1
-> logits
```

Purpose:

- sanity check,
- segment-level baseline,
- first model to run.

---

## M1 — EEG-Only Trial Sequence Model

For DEAP:

```text
60s trial
-> 12 × 5s EEG windows
-> EEGSegmentEncoder per window
-> EEG sequence encoder
-> classifier
```

Purpose:

- test whether trial-aware sequence modeling improves EEG-only performance.

---

## M2 — EMG-Only Segment Model

```text
EMG 5s features
-> channel-shared EMG encoder
-> classifier
```

Purpose:

- measure standalone EMG signal.

---

## M3 — EMG-Only Trial Sequence Model

For DEAP:

```text
12 × 5s EMG feature windows
-> EMG encoder per window
-> EMG temporal attention / tiny TCN
-> classifier
```

Purpose:

- test whether EMG temporal dynamics contain useful information.

---

## M4 — EEG+EMG Segment-Level Fusion

```text
for each 5s window:
    EEG_t -> z_eeg_t
    EMG_t -> z_emg_t
    fuse_t -> z_fused_t

DEAP:
    [z_fused_1, ..., z_fused_12]
    -> sequence encoder
    -> classifier

I-DARE:
    z_fused_1 -> classifier
```

Purpose:

- test early temporal fusion.

---

## M5 — EEG+EMG Modality-Specific Sequence Fusion

For DEAP:

```text
EEG windows -> EEG sequence encoder -> h_eeg_trial
EMG windows -> EMG sequence encoder -> h_emg_trial
fuse(h_eeg_trial, h_emg_trial)
-> classifier
```

Purpose:

- test whether modality-specific temporal dynamics should be learned before fusion.

---

# 12. Experimental Roadmap

## Phase 0 — Local Setup

Completed:

- repository scaffold created,
- virtual environment created,
- PyTorch CUDA installed,
- RTX 5090 verified,
- EEG model files added,
- GPU smoke test passed.

---

## Phase 1 — Dataset Acquisition and Audit

Goals:

1. download DEAP,
2. download I-DARE,
3. inspect file structures,
4. verify EEG and EMG availability,
5. confirm channel names and sampling rates,
6. document dataset versions.

Scripts:

```text
scripts/01_audit_datasets.py
```

Expected outputs:

```text
docs/data_audit_deap.md
docs/data_audit_idare.md
```

---

## Phase 2 — DEAP EEG-Only Segment Baseline

Models:

```text
R0: OldEncoder + classifier
R1: EEGSegmentClassifier-v1
R2: EEGNet / ShallowConvNet
```

Main purpose:

```text
Establish a trustworthy EEG-only baseline before adding EMG or sequence modeling.
```

---

## Phase 3 — DEAP EEG Trial Sequence Modeling

Models:

```text
S0: mean pooling
S1: temporal attention pooling
S2: lightweight TCN + attention pooling
S3: BiGRU + attention pooling
```

Main comparison:

```text
EEG segment-level vs EEG trial-level
```

---

## Phase 4 — EMG Baselines

Models:

```text
E0: EMG-only segment classifier
E1: EMG-only trial attention model
E2: EMG-only tiny TCN sequence model
```

Purpose:

```text
Estimate EMG-only signal quality before EEG–EMG fusion.
```

---

## Phase 5 — EEG+EMG Fusion

Models:

```text
F1: segment-level concat fusion
F2: segment-level gated fusion
F3: modality-specific sequence + concat fusion
F4: modality-specific sequence + gated fusion
```

Key comparison:

```text
F2 vs F4
```

This answers whether fusion is better before or after modality-specific sequence encoding.

---

## Phase 6 — I-DARE Experiments

Models:

```text
I1: EEG-only
I2: EMG-only
I3: EEG+EMG concat
I4: EEG+EMG gated
```

Sequence modeling is not a main claim for I-DARE unless subwindowing is explicitly introduced.

---

## Phase 7 — Contrastive / Regularization Ablations

Only after the best baseline/fusion model is identified:

```text
C0: CE only
C1: CE + SupCon
C2: CE + SupCon + continuous-rating constraint
C3: CE + SupCon + hard-negative weighting
C4: CE + SupCon + VREx
```

---

# 13. Main DEAP Ablation Table

| Code | EEG | EMG | Sequence | Fusion | Purpose |
|---|---:|---:|---:|---|---|
| D1 | Yes | No | No | — | EEG segment baseline |
| D2 | Yes | No | Yes | — | Effect of EEG sequence modeling |
| D3 | No | Yes | No | — | EMG segment baseline |
| D4 | No | Yes | Yes | — | EMG temporal dynamics |
| D5 | Yes | Yes | No | Segment fusion | EMG effect without trial sequence |
| D6 | Yes | Yes | Yes | Segment-level fusion | Fusion before sequence |
| D7 | Yes | Yes | Yes | Trial-level fusion | Fusion after modality-specific sequence encoding |

Key comparisons:

```text
D2 - D1 = effect of sequence modeling on EEG
D5 - D1 = effect of EMG without sequence
D6 - D2 = effect of EMG with shared sequence modeling
D7 - D2 = effect of EMG with modality-specific sequence modeling
D7 vs D6 = better fusion location
```

---

# 14. Main I-DARE Ablation Table

| Code | EEG | EMG | Fusion | Purpose |
|---|---:|---:|---|---|
| I1 | Yes | No | — | EEG baseline |
| I2 | No | Yes | — | EMG baseline |
| I3 | Yes | Yes | concat | Fusion baseline |
| I4 | Yes | Yes | gated | Main I-DARE candidate |

---

# 15. Metrics

For all main runs:

```text
Accuracy
Macro-F1
Balanced Accuracy
Per-subject accuracy
Mean ± std across LOSO folds
95% confidence interval
Wilcoxon signed-rank test for key comparisons
```

For DEAP:

```text
segment-level results and trial-level results must be reported separately
```

The primary DEAP result should be trial-level.

---

# 16. Visualizations

Required visualizations:

```text
1. Confusion matrix
2. Per-subject performance bar plot
3. Temporal attention over 12 DEAP segments
4. EMG channel attention
5. Fusion gate distribution
6. EEG vs EMG contribution analysis
7. UMAP/t-SNE of embeddings before and after sequence encoding
8. Contrastive embedding visualization if SupCon is used
```

For contrastive learning:

```text
visualize whether subject clustering decreases and emotion clustering improves
```

---

# 17. Repository and Project Memory

The project must maintain code and memory separately.

Key project memory files:

```text
docs/project_state.md
docs/chat_handoff_latest.md
docs/decision_log.md
experiments/registry.csv
```

Purpose:

- enable continuation across multiple chat sessions,
- prevent loss of design decisions,
- track experiments and results,
- keep the project reproducible.

End-of-session routine:

```text
1. Update docs/project_state.md
2. Update docs/chat_handoff_latest.md
3. Update docs/decision_log.md if a new decision was made
4. Update experiments/registry.csv if any run was executed
5. Commit and push
```

---

# 18. Suggested Defaults for the Next Implementation Stage

## EEG Segment Encoder

```python
window_sec = 5.0
sampling_rate = 128
modelsize = "lite"
stem_fusion = "concat"
channel_pos_mode = "learnable"
channel_mixer = "mha"
norm_kind = "gn"
use_spectral_branch = False
```

## EEG Sequence Encoder

```text
lightweight TCN + temporal attention pooling
```

## EMG Encoder

```text
channel-shared feature MLP + EMG channel attention pooling
```

## EMG Sequence Encoder

```text
temporal attention pooling
```

## Fusion

Initial baseline:

```text
concat + MLP
```

Main candidate:

```text
gated fusion
```

## Contrastive Learning

Initial ablation only:

```text
CE + SupCon
positive = same label + different subject
temperature = 0.07
lambda_contrastive = 0.1 or 0.3
projection_dim = 64
```

---

# 19. Summary of Version V1.1

V1.1 defines a controlled study of cross-subject EEG–EMG emotion recognition on DEAP and I-DARE.

The main methodological contributions under investigation are:

1. a compact EEG segment encoder adapted from the previous conference model,
2. feature-level EMG modeling to handle EMG mismatch between datasets,
3. trial-aware temporal modeling for DEAP,
4. comparison of segment-level fusion versus modality-specific trial-level fusion,
5. carefully designed affective-response-aware contrastive learning as a later ablation.

The key principle of this proposal is controlled progression:

```text
EEG-only baseline
-> EEG trial sequence
-> EMG-only baseline
-> EEG+EMG fusion
-> contrastive / regularization ablation
```

This prevents blindly combining many ideas before knowing which inductive biases actually help.



# FILE: docs/dataset_acquisition_plan.md


# Dataset Acquisition Plan

## Project

**Cross-Subject EEG–EMG Emotion Recognition with Trial-Aware Temporal Modeling on DEAP and I-DARE**

This document defines the dataset acquisition and audit plan for **Milestone 1**.

The goal of Milestone 1 is not training. The goal is to obtain the correct dataset files, inspect their structure, verify EEG/EMG availability, and document all assumptions before writing loaders or running experiments.

---

## Current Status

Local project root:

```text
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE
```

Local dataset folders:

```text
/mnt/HDD/AliWorks/DEAP
/mnt/HDD/AliWorks/I-DARE
```

Current state:

```text
DEAP folder: exists but empty
I-DARE folder: exists but empty
```

Storage decision:

```text
Use /mnt/HDD/AliWorks/... for the initial phase.
```

Important note:

```text
/mnt/HDD is currently not a separate mount. It is on the root filesystem.
Available free space is about 500GB.
```

This is acceptable for the current phase because we will start from **preprocessed physiological data**, not raw videos or large redundant archives.

---

# 1. Milestone 1 Objective

Milestone 1 is:

```text
Dataset acquisition and audit
```

It has four concrete outputs:

```text
1. DEAP files downloaded and stored locally.
2. I-DARE files downloaded and stored locally.
3. scripts/01_audit_datasets.py created.
4. Audit reports generated:
   - docs/data_audit_deap.md
   - docs/data_audit_idare.md
```

No training should be started before these four outputs exist.

---

# 2. DEAP Acquisition Decision

## 2.1 Selected DEAP Version

For the first implementation stage, use:

```text
DEAP preprocessed Python version
Data_preprocessed_python.zip
```

Do **not** start from raw `.bdf` files.

## 2.2 Rationale

The preprocessed Python version is selected because:

- it is commonly used in DEAP emotion recognition studies,
- it is already downsampled to **128Hz**,
- it avoids raw BioSemi preprocessing at this stage,
- it matches the current model design:
  - 5-second windows,
  - 128Hz sampling rate,
  - 640 samples per window,
- it includes EEG and peripheral channels, including EMG.

## 2.3 Expected File

Expected official archive:

```text
Data_preprocessed_python.zip
```

Expected local destination:

```text
/mnt/HDD/AliWorks/DEAP/Data_preprocessed_python.zip
```

Expected extraction destination:

```text
/mnt/HDD/AliWorks/DEAP/data_preprocessed_python/
```

The exact extracted folder name should be verified during audit.

---

## 2.4 Expected DEAP Structure

Expected contents after extraction:

```text
s01.dat
s02.dat
...
s32.dat
```

Expected number of participant files:

```text
32
```

Expected content of each `.dat` file:

```text
data
labels
```

Expected shapes:

```text
data   -> [40 trials, 40 channels, 8064 samples]
labels -> [40 trials, 4 labels]
```

Expected label order:

```text
labels[:, 0] = valence
labels[:, 1] = arousal
labels[:, 2] = dominance
labels[:, 3] = liking
```

---

## 2.5 DEAP Channels Needed for This Project

Main EEG channels:

```text
first 32 channels
```

Main EMG channels of interest:

```text
zEMG
tEMG
```

Important implementation note:

DEAP channel indexing must be verified directly from the official channel list and the loaded `.dat` files. The audit script should not silently assume wrong indexing. It must print and document the final EEG/EMG channel indices used by the project.

---

## 2.6 DEAP Windowing Assumption

Main DEAP windowing:

```text
60-second trial -> 12 non-overlapping 5-second windows
```

At 128Hz:

```text
5 seconds = 640 samples
12 windows = 7680 samples
```

Important detail:

DEAP preprocessed data has 8064 samples per trial. The audit must verify how these samples correspond to baseline/stimulus duration in the selected official preprocessed archive.

The implementation should not blindly use all 8064 samples as 60 seconds. The audit should explicitly determine:

```text
- whether the usable stimulus portion is exactly 60s,
- whether baseline samples are included,
- which sample range should be used for the 12 x 5s windows.
```

Until verified, the working assumption is:

```text
Use the 60s stimulus part only for the main 12-window protocol.
```

---

## 2.7 DEAP Label Rule

For binary valence:

```python
valence_label = 1 if valence_score > 5 else 0
valence_score == 5 -> discard
```

For binary arousal:

```python
arousal_label = 1 if arousal_score > 5 else 0
arousal_score == 5 -> discard
```

The audit must report:

```text
- min/max valence score
- min/max arousal score
- number of score == 5 valence trials
- number of score == 5 arousal trials
- class balance after removing score == 5
```

---

## 2.8 DEAP Access Status

Current status:

```text
DEAP has not been downloaded yet.
DEAP access credentials are not confirmed yet.
```

Action required:

```text
Request or confirm access to the official DEAP dataset download server.
```

The project should use the official dataset source, not unofficial mirrors, unless official access fails and a separate decision is recorded.

---

# 3. I-DARE Acquisition Decision

## 3.1 Selected I-DARE Source

Use the official I-DARE Figshare project:

```text
https://figshare.com/projects/I_DARE/186558
```

Current status:

```text
I-DARE has not been downloaded yet.
Exact files/release are not yet listed locally.
```

Action required:

```text
List available Figshare files and sizes before downloading.
```

---

## 3.2 Expected I-DARE Characteristics

Expected high-level dataset properties:

```text
Subjects: 63
Stimuli: 32 emotional images
Modalities: EEG, EMG, SC, PPG, ET
```

Current project uses:

```text
EEG
EMG
SAM labels / ratings
```

Other modalities are not needed for the first paper stage.

---

## 3.3 Expected I-DARE Processed Modality Folders

Expected processed modality folders:

```text
EEG/
EMG/
SC&PPG/
ET/
```

Expected number of processed `.mat` files:

```text
63 files per modality folder
1 file per subject
```

For the current project, required folders are:

```text
EEG/
EMG/
```

Required label files:

```text
Valence_SAM.csv
Arousal_SAM.csv
Quadrants_SAM.csv
```

Potentially useful metadata files:

```text
Sample.csv
Stimuli_Specification.csv
Agreement_Raters.csv
```

The exact file list must be verified from Figshare before download.

---

## 3.4 Expected I-DARE `.mat` Fields

Expected fields inside processed `.mat` modality files:

```text
subject
Fs
channels
channels_type
channels_unit
data
time
event_id
event_begin
event_end
```

The audit script must verify these fields and report missing or unexpected fields.

---

## 3.5 I-DARE EEG Assumptions to Verify

Expected EEG properties from the dataset description:

```text
EEG recorded from 40 electrodes
10-10 system
```

Processed EEG details must be verified from the files:

```text
sampling rate
number of channels
channel names
event boundaries
stimulus event duration
```

The current model expects 32 channels at 128Hz for the first EEG baseline. Therefore, the audit must determine:

```text
- whether I-DARE processed EEG is already resampled,
- whether we need to resample to 128Hz,
- which 32-channel intersection/canonical set can be used,
- whether all required DEAP-like channels are present.
```

No channel selection should be finalized before the audit.

---

## 3.6 I-DARE EMG Assumptions to Verify

I-DARE EMG is expected to contain:

```text
zygomaticus major
corrugator supercilii
```

This does not perfectly match DEAP EMG:

```text
DEAP: zEMG + tEMG
I-DARE: zygomaticus + corrugator
```

Therefore, the main EMG design remains:

```text
feature-level EMG harmonization
```

Do not start with a raw shared EMG waveform encoder.

The audit must report:

```text
- EMG channel names
- EMG sampling rate
- EMG event alignment with EEG
- EMG signal shape per subject
- availability of all 63 subjects
```

---

## 3.7 I-DARE Windowing Assumption

Main I-DARE windowing:

```text
one 5-second stimulus block -> one 5-second window
```

The audit must verify:

```text
- event_begin / event_end indexing
- actual duration of each stimulus event
- consistency across subjects
- alignment between label CSVs and event_id
```

No subwindowing should be used in the main protocol.

Possible later ablation:

```text
5s stimulus block -> 1s subwindows
```

This is not part of the first baseline.

---

# 4. Download Strategy

## 4.1 DEAP

Planned local structure:

```text
/mnt/HDD/AliWorks/DEAP/
    Data_preprocessed_python.zip
    data_preprocessed_python/
        s01.dat
        ...
        s32.dat
```

Do not commit any dataset files to Git.

---

## 4.2 I-DARE

Planned local structure, pending actual Figshare file list:

```text
/mnt/HDD/AliWorks/I-DARE/
    raw_downloads/
    processed/
        EEG/
        EMG/
        SC&PPG/
        ET/
    labels/
        Valence_SAM.csv
        Arousal_SAM.csv
        Quadrants_SAM.csv
    metadata/
        Sample.csv
        Stimuli_Specification.csv
        Agreement_Raters.csv
```

The exact structure may change after inspecting the Figshare archive. Any change must be documented in:

```text
docs/data_audit_idare.md
```

---

# 5. Dataset Audit Script Requirements

Create:

```text
scripts/01_audit_datasets.py
```

This script should be runnable before and after downloads.

Before downloads, it should report:

```text
DEAP folder exists but no recognized dataset files found.
I-DARE folder exists but no recognized dataset files found.
```

After downloads, it should inspect and report dataset structure.

---

## 5.1 DEAP Audit Requirements

The audit script must check:

```text
- DEAP root exists
- archive exists
- extracted folder exists
- number of `.dat` files
- file names
- ability to load one `.dat` file
- keys inside `.dat`
- shape of `data`
- shape of `labels`
- dtype of arrays
- number of trials
- number of channels
- number of samples
- inferred sampling rate assumption
- label ranges
- score == 5 counts
- class balance after removing score == 5
- EEG channel index plan
- EMG channel index plan
- feasibility of 12 non-overlapping 5s windows
```

Expected output file:

```text
docs/data_audit_deap.md
```

---

## 5.2 I-DARE Audit Requirements

The audit script must check:

```text
- I-DARE root exists
- downloaded archive/file list
- extracted folder structure
- presence of EEG folder
- presence of EMG folder
- number of EEG `.mat` files
- number of EMG `.mat` files
- presence of label CSV files
- label CSV shape and columns
- subject IDs
- event IDs
- `.mat` fields
- EEG sampling rates from `Fs`
- EMG sampling rates from `Fs`
- EEG channel names
- EMG channel names
- data matrix shapes
- time vector shapes
- event_begin / event_end consistency
- feasibility of one 5s window per stimulus event
```

Expected output file:

```text
docs/data_audit_idare.md
```

---

# 6. Project Decisions Confirmed in This Plan

## D-M1-001 — Use Current Storage Location

Decision:

```text
Use /mnt/HDD/AliWorks/DEAP and /mnt/HDD/AliWorks/I-DARE for the initial dataset phase.
```

Reason:

```text
Around 500GB free space is available.
The first phase uses preprocessed datasets only.
```

Status:

```text
Accepted for initial phase.
```

---

## D-M1-002 — Start DEAP from Preprocessed Python Version

Decision:

```text
Use DEAP Data_preprocessed_python.zip.
```

Reason:

```text
It matches the 128Hz model design and avoids raw preprocessing.
```

Status:

```text
Accepted.
```

---

## D-M1-003 — Discover I-DARE Files Before Download

Decision:

```text
Do not assume I-DARE archive structure. First list Figshare files and sizes.
```

Reason:

```text
The exact downloadable files/release have not been inspected locally yet.
```

Status:

```text
Accepted.
```

---

# 7. Immediate Next Actions

## Action A — DEAP Access

Check whether DEAP credentials are available.

If not available:

```text
Request official DEAP access.
```

Required target file:

```text
Data_preprocessed_python.zip
```

---

## Action B — I-DARE File Listing

Before downloading I-DARE, list the files from the Figshare project:

```text
https://figshare.com/projects/I_DARE/186558
```

The listing should capture:

```text
file name
file size
download URL if available
whether it contains EEG
whether it contains EMG
whether it contains labels/metadata
```

The file listing can be documented in:

```text
docs/data_sources_idare.md
```

or inside:

```text
docs/data_audit_idare.md
```

---

## Action C — Build Audit Script

After confirming dataset download/access plan:

```text
scripts/01_audit_datasets.py
```

The audit script should not assume the datasets are already present. It must gracefully handle missing data.

---

# 8. Do Not Do Yet

Do not start:

```text
training
baseline runs
contrastive learning
VREx
EMG fusion implementation
sequence modeling implementation
hyperparameter tuning
```

until dataset acquisition and audit are complete.

---

# 9. References and Source Notes

This plan is based on the official DEAP dataset documentation and the I-DARE dataset paper / public project description.

Important sources to verify during implementation:

```text
DEAP official download/readme pages
I-DARE Frontiers dataset paper
I-DARE Figshare project page
```

Reference URLs:

```text
https://eecs.qmul.ac.uk/mmv/datasets/deap/download.html
https://eecs.qmul.ac.uk/mmv/datasets/deap/readme.html
https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2024.1347327/full
https://figshare.com/projects/I_DARE/186558
```

---

# 10. Summary

Milestone 1 begins with dataset acquisition and audit, not model training.

Confirmed choices:

```text
DEAP: official preprocessed Python version, 128Hz
I-DARE: official Figshare project, files to be listed before download
Storage: current /mnt/HDD/AliWorks paths accepted for initial phase
```

Immediate next step:

```text
Confirm/download DEAP preprocessed Python archive and list I-DARE Figshare files.
```



# FILE: docs/data_sources_idare.md


# I-DARE Figshare Source Listing and Acquisition Summary

This document summarizes the I-DARE Figshare source listing generated during **Milestone 1 — Dataset acquisition and audit**.

It is based on the output of:

```text
scripts/list_idare_figshare_files.py
```

No I-DARE dataset files have been downloaded yet.  
This document only records the discovered Figshare metadata and the resulting acquisition decisions.

---

## 1. Project Summary

Figshare project:

```text
I DARE
```

Figshare project ID:

```text
186558
```

Project URL:

```text
https://figshare.com/projects/I_DARE/186558
```

API project URL observed during listing:

```text
https://api.figshare.com/v2/projects/186558
```

Listing result:

```text
Articles discovered: 5
Files discovered: 263
Total listed file size: 6.98 GB
```

This confirms that the full public Figshare project is small enough for the current storage situation.

---

## 2. Discovered Articles

| Article ID | Title | File count | DOI |
|---:|---|---:|---|
| 24680694 | Supplementary material | 7 | 10.6084/m9.figshare.24680694.v3 |
| 24678000 | EEG modality | 63 | 10.6084/m9.figshare.24678000.v1 |
| 24680640 | EMG modality | 64 | 10.6084/m9.figshare.24680640.v1 |
| 24680646 | SC&PPG modalities | 64 | 10.6084/m9.figshare.24680646.v1 |
| 24680751 | ET modality | 65 | 10.6084/m9.figshare.24680751.v1 |

---

## 3. Category Summary

| Category | File count | Total size |
|---|---:|---:|
| EEG | 63 | 4.90 GB |
| EMG | 64 | 1.99 GB |
| ET | 65 | 66.35 MB |
| SC/PPG | 64 | 31.46 MB |
| Labels | 4 | 21.90 KB |
| Metadata | 3 | 229.81 KB |

The full project size is approximately:

```text
6.98 GB
```

The first-stage required subset is approximately:

```text
6.88 GB
```

The difference is small because EEG and EMG dominate the storage cost.

---

## 4. First-Stage Required Files

For the current project, the required modalities are:

```text
EEG
EMG
SAM labels
basic metadata
```

Required categories:

```text
EEG files
EMG files
labels
metadata
```

Required first-stage count:

```text
133 files
```

Required first-stage size:

```text
6.88 GB
```

Optional / not needed for the first stage:

```text
SC&PPG
ET
Stimuli_Selection.pdf
```

These can be ignored for the initial EEG–EMG paper unless later analyses require them.

---

## 5. Supplementary / Label / Metadata Files

The supplementary material article contains:

| File name | Category | Size |
|---|---|---:|
| Agreement_Raters.csv | metadata | 2.90 KB |
| Arousal_SAM.csv | labels | 4.84 KB |
| Quadrants_SAM.csv | labels | 11.02 KB |
| Sample.csv | labels / sample table | 1.21 KB |
| Stimuli_Specifications.csv | metadata | 40.15 KB |
| Valence_SAM.csv | labels | 4.84 KB |
| Stimuli_Selection.pdf | metadata / documentation | 186.75 KB |

For the first stage, the minimum required files are:

```text
Valence_SAM.csv
Arousal_SAM.csv
Quadrants_SAM.csv
Sample.csv
Stimuli_Specifications.csv
Agreement_Raters.csv
```

`Stimuli_Selection.pdf` is not necessary for training but may be useful for dataset documentation.

---

## 6. Subject Coverage

Subject IDs were inferred from filenames matching:

```text
sbj_P_XX.mat
```

### EEG

```text
n_subjects = 63
```

EEG subject IDs:

```text
[1, 2, 3, 5, 6, 7, 8, 9, 10, 11,
 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
 22, 23, 24, 25, 26, 27, 28, 29, 30, 31,
 32, 33, 34, 35, 36, 37, 38, 39, 40, 41,
 42, 43, 44, 45, 46, 47, 48, 49, 50, 52,
 53, 54, 55, 56, 57, 58, 59, 60, 61, 62,
 63, 64, 65]
```

Missing EEG subject:

```text
4
```

### EMG

```text
n_subjects = 64
```

EMG subject IDs:

```text
[1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
 21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
 52, 53, 54, 55, 56, 57, 58, 59, 60, 61,
 62, 63, 64, 65]
```

### EEG–EMG Intersection

```text
EEG subjects: 63
EMG subjects: 64
Common EEG+EMG subjects: 63
EEG-only subjects: []
EMG-only subjects: [4]
```

---

## 7. Main Protocol Decision

Use the **63 common EEG+EMG subjects** for the main I-DARE experiments.

Subject 4 has EMG but no EEG. Therefore:

```text
Subject 4 must be excluded from the main EEG+EMG comparison.
```

Rationale:

The main paper compares:

```text
EEG-only
EMG-only
EEG+EMG
```

For fair comparison, all three conditions should use the same subject set. Therefore, the main I-DARE protocol should use only the subjects with both EEG and EMG.

Subject 4 may be kept only for an optional EMG-only secondary analysis, but not for the main comparison.

---

## 8. Download Decision

The first-stage I-DARE download should include:

```text
1. All EEG modality files
2. All EMG modality files
3. Supplementary label/metadata CSV files
```

Do not download yet:

```text
SC&PPG modality
ET modality
```

unless later needed.

---

## 9. Expected Local Storage Structure

Target root:

```text
/mnt/HDD/AliWorks/I-DARE
```

Recommended local structure:

```text
/mnt/HDD/AliWorks/I-DARE/
    raw_downloads/
        EEG/
        EMG/
        supplementary/
    processed/
        EEG/
        EMG/
    labels/
        Valence_SAM.csv
        Arousal_SAM.csv
        Quadrants_SAM.csv
        Sample.csv
    metadata/
        Stimuli_Specifications.csv
        Agreement_Raters.csv
```

The exact structure may be adjusted after download, but the audit report must document the final structure.

---

## 10. Implications for Audit

The dataset audit must verify:

```text
- all 63 EEG files are present
- all EMG files needed for the 63 common EEG+EMG subjects are present
- subject 4 is handled correctly
- label CSV files are present
- subject IDs in EEG, EMG, and labels can be aligned
- event IDs and stimulus IDs can be aligned
- EEG sampling rate is available from the files
- EMG sampling rate is available from the files
- channel names are available
- event_begin / event_end fields are available
- one 5-second stimulus window per event is feasible
```

Important audit rule:

```text
Do not assume I-DARE channel counts, sampling rates, or event durations.
Verify them from the downloaded files.
```

---

## 11. Current Git/Project Status

At the time this document is prepared:

```text
I-DARE file listing script exists:
scripts/list_idare_figshare_files.py

Generated metadata files exist locally:
docs/data_sources_idare.md
docs/data_sources_idare.json
docs/data_sources_idare_summary.txt
```

This document should replace or update the existing `docs/data_sources_idare.md`.

After adding this file to the repository, regenerate:

```text
docs/handoff_bundle_latest.md
```

so that the I-DARE source decision is available in future chats.

---

## 12. Next Steps

### Step 1 — Save this document

Copy this file to:

```text
docs/data_sources_idare.md
```

### Step 2 — Commit the source listing artifacts

Commit:

```text
scripts/list_idare_figshare_files.py
docs/data_sources_idare.md
docs/data_sources_idare.json
docs/data_sources_idare_summary.txt
```

### Step 3 — Update project memory

Update:

```text
docs/project_state.md
docs/chat_handoff_latest.md
docs/decision_log.md
docs/handoff_bundle_latest.md
```

Key decision to record:

```text
Use the 63 common EEG+EMG subjects for main I-DARE experiments.
Subject 4 is excluded from main EEG+EMG protocol.
```

### Step 4 — Build I-DARE download manifest

Create:

```text
docs/idare_download_manifest.csv
```

The manifest should include:

```text
category
article_id
file_id
file_name
size_bytes
size_human
subject_id
download_url
local_relative_path
include_in_first_stage
notes
```

### Step 5 — Download I-DARE only after manifest review

Only after manifest review should the dataset files be downloaded.

---

## 13. Do Not Do Yet

Do not start:

```text
training
baseline runs
contrastive learning
VREx
EMG fusion implementation
sequence modeling implementation
hyperparameter tuning
```

until dataset acquisition and audit are complete.



# FILE: docs/data_sources_idare_summary.txt


I-DARE Figshare Source Summary
==============================

Category summary:
- EEG: count=63, size=4.90 GB
- EMG: count=64, size=1.99 GB
- ET: count=65, size=66.35 MB
- SC/PPG: count=64, size=31.46 MB
- labels: count=4, size=21.90 KB
- metadata: count=3, size=229.81 KB

Subject coverage:
- EEG: n_subjects=63, ids=[1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65]
- EMG: n_subjects=64, ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65]
- SC/PPG: n_subjects=64, ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65]
- ET: n_subjects=65, ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65]

EEG/EMG intersection:
- EEG subjects: 63
- EMG subjects: 64
- Common EEG+EMG subjects: 63
- EEG-only subjects: []
- EMG-only subjects: [4]

First-stage required files:
- required_files: 133
- required_total_size: 6.88 GB



# FILE: docs/idare_download_manifest_summary.md


# I-DARE Download Manifest Summary
This file was generated by `scripts/build_idare_download_manifest.py`.
No dataset files were downloaded by this script.
## Manifest Outputs
- `docs/idare_download_manifest.csv`
- `docs/idare_download_manifest_summary.md`
## Counts
- Total listed files: 263
- First-stage files: 133
- Main-protocol files: 132
- First-stage total size: 6.88 GB
- Main-protocol total size: 6.85 GB
## First-Stage Files by Category
| Category | Count | Size |
|---|---:|---:|
| EEG | 63 | 4.90 GB |
| EMG | 64 | 1.99 GB |
| labels | 4 | 0.00 GB |
| metadata | 2 | 0.00 GB |

## Main Protocol Subject Decision
- Use the 63 common EEG+EMG subjects for main I-DARE experiments.
- Subject 4 has EMG but no EEG.
- Subject 4 is included in the manifest but excluded from `include_in_main_protocol`.
- Subject 4 may be used only for optional EMG-only secondary analysis.

## Next Step
Review `docs/idare_download_manifest.csv` before downloading files.



# FILE: docs/idare_acquisition_status.md


# I-DARE Acquisition Status

## Status

I-DARE first-stage acquisition is complete.

Dataset files were downloaded into:

```text
/mnt/HDD/AliWorks/I-DARE
```

Downloaded first-stage subset:

```text
EEG files
EMG files
label CSV files
metadata CSV files
```

The download was performed using:

```text
scripts/download_idare_from_manifest.py
```

Source manifest:

```text
docs/idare_download_manifest.csv
```

Final verification report:

```text
docs/idare_download_report.md
```

---

## Final Verification Result

The full verification command was:

```bash
python scripts/download_idare_from_manifest.py --verify-only
```

Final result:

```text
selected_files: 133
selected_total_size: 6.88 GB
verified_ok: 133
verify_failed: 0
```

Downloaded file count:

```text
133
```

Local disk usage:

```text
6.9G /mnt/HDD/AliWorks/I-DARE
```

Available disk space after download:

```text
about 491G free on /mnt/HDD
```

---

## Local Folder Structure

Observed folder structure:

```text
/mnt/HDD/AliWorks/I-DARE
/mnt/HDD/AliWorks/I-DARE/labels
/mnt/HDD/AliWorks/I-DARE/metadata
/mnt/HDD/AliWorks/I-DARE/raw_downloads
/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG
/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG
```

---

## Downloaded Content

The first-stage I-DARE subset includes:

```text
EEG: 63 subject files
EMG: 64 subject files
Labels: 4 CSV files
Metadata: 2 CSV files
Total: 133 files
```

The downloaded subset excludes:

```text
SC&PPG modality
ET modality
Stimuli_Selection.pdf
```

These files are not required for the first EEG–EMG stage.

---

## Main Protocol Subject Decision

The main I-DARE protocol uses the 63 subjects with both EEG and EMG.

Subject 4 has EMG but no EEG and is excluded from the main EEG+EMG protocol.

Subject 4 remains downloaded and may be used only for optional EMG-only secondary analysis.

---

## Integrity Check

All first-stage downloaded files were verified using the checksum metadata stored in:

```text
docs/idare_download_manifest.csv
```

Verification result:

```text
verified_ok: 133
verification failures: 0
```

This means the local I-DARE first-stage files are ready for structural audit.

---

## Next Step

Create and run the dataset audit script:

```text
scripts/01_audit_datasets.py
```

The audit should inspect I-DARE first, because I-DARE has now been downloaded and verified.

DEAP acquisition is still pending.



# FILE: docs/idare_download_report.md


# I-DARE Download Report

- Mode: verify-only
- Main protocol only: False
- Selected files: 133
- Selected total size: 6.88 GB

| Status | Category | File | Local path | Notes |
|---|---|---|---|---|
| verified_ok | EEG | sbj_P_01.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_01.mat` |  |
| verified_ok | EEG | sbj_P_02.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_02.mat` |  |
| verified_ok | EEG | sbj_P_03.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_03.mat` |  |
| verified_ok | EEG | sbj_P_05.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_05.mat` |  |
| verified_ok | EEG | sbj_P_06.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_06.mat` |  |
| verified_ok | EEG | sbj_P_07.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_07.mat` |  |
| verified_ok | EEG | sbj_P_08.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_08.mat` |  |
| verified_ok | EEG | sbj_P_09.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_09.mat` |  |
| verified_ok | EEG | sbj_P_10.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_10.mat` |  |
| verified_ok | EEG | sbj_P_11.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_11.mat` |  |
| verified_ok | EEG | sbj_P_12.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_12.mat` |  |
| verified_ok | EEG | sbj_P_13.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_13.mat` |  |
| verified_ok | EEG | sbj_P_14.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_14.mat` |  |
| verified_ok | EEG | sbj_P_15.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_15.mat` |  |
| verified_ok | EEG | sbj_P_16.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_16.mat` |  |
| verified_ok | EEG | sbj_P_17.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_17.mat` |  |
| verified_ok | EEG | sbj_P_18.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_18.mat` |  |
| verified_ok | EEG | sbj_P_19.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_19.mat` |  |
| verified_ok | EEG | sbj_P_20.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_20.mat` |  |
| verified_ok | EEG | sbj_P_21.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_21.mat` |  |
| verified_ok | EEG | sbj_P_22.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_22.mat` |  |
| verified_ok | EEG | sbj_P_23.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_23.mat` |  |
| verified_ok | EEG | sbj_P_24.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_24.mat` |  |
| verified_ok | EEG | sbj_P_25.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_25.mat` |  |
| verified_ok | EEG | sbj_P_26.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_26.mat` |  |
| verified_ok | EEG | sbj_P_27.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_27.mat` |  |
| verified_ok | EEG | sbj_P_28.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_28.mat` |  |
| verified_ok | EEG | sbj_P_29.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_29.mat` |  |
| verified_ok | EEG | sbj_P_30.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_30.mat` |  |
| verified_ok | EEG | sbj_P_31.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_31.mat` |  |
| verified_ok | EEG | sbj_P_32.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_32.mat` |  |
| verified_ok | EEG | sbj_P_33.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_33.mat` |  |
| verified_ok | EEG | sbj_P_34.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_34.mat` |  |
| verified_ok | EEG | sbj_P_35.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_35.mat` |  |
| verified_ok | EEG | sbj_P_36.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_36.mat` |  |
| verified_ok | EEG | sbj_P_37.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_37.mat` |  |
| verified_ok | EEG | sbj_P_38.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_38.mat` |  |
| verified_ok | EEG | sbj_P_39.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_39.mat` |  |
| verified_ok | EEG | sbj_P_40.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_40.mat` |  |
| verified_ok | EEG | sbj_P_41.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_41.mat` |  |
| verified_ok | EEG | sbj_P_42.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_42.mat` |  |
| verified_ok | EEG | sbj_P_43.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_43.mat` |  |
| verified_ok | EEG | sbj_P_44.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_44.mat` |  |
| verified_ok | EEG | sbj_P_45.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_45.mat` |  |
| verified_ok | EEG | sbj_P_46.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_46.mat` |  |
| verified_ok | EEG | sbj_P_47.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_47.mat` |  |
| verified_ok | EEG | sbj_P_48.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_48.mat` |  |
| verified_ok | EEG | sbj_P_49.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_49.mat` |  |
| verified_ok | EEG | sbj_P_50.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_50.mat` |  |
| verified_ok | EEG | sbj_P_52.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_52.mat` |  |
| verified_ok | EEG | sbj_P_53.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_53.mat` |  |
| verified_ok | EEG | sbj_P_54.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_54.mat` |  |
| verified_ok | EEG | sbj_P_55.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_55.mat` |  |
| verified_ok | EEG | sbj_P_56.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_56.mat` |  |
| verified_ok | EEG | sbj_P_57.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_57.mat` |  |
| verified_ok | EEG | sbj_P_58.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_58.mat` |  |
| verified_ok | EEG | sbj_P_59.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_59.mat` |  |
| verified_ok | EEG | sbj_P_60.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_60.mat` |  |
| verified_ok | EEG | sbj_P_61.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_61.mat` |  |
| verified_ok | EEG | sbj_P_62.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_62.mat` |  |
| verified_ok | EEG | sbj_P_63.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_63.mat` |  |
| verified_ok | EEG | sbj_P_64.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_64.mat` |  |
| verified_ok | EEG | sbj_P_65.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_65.mat` |  |
| verified_ok | EMG | sbj_P_01.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_01.mat` |  |
| verified_ok | EMG | sbj_P_02.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_02.mat` |  |
| verified_ok | EMG | sbj_P_03.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_03.mat` |  |
| verified_ok | EMG | sbj_P_04.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_04.mat` |  |
| verified_ok | EMG | sbj_P_05.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_05.mat` |  |
| verified_ok | EMG | sbj_P_06.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_06.mat` |  |
| verified_ok | EMG | sbj_P_07.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_07.mat` |  |
| verified_ok | EMG | sbj_P_08.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_08.mat` |  |
| verified_ok | EMG | sbj_P_09.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_09.mat` |  |
| verified_ok | EMG | sbj_P_10.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_10.mat` |  |
| verified_ok | EMG | sbj_P_11.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_11.mat` |  |
| verified_ok | EMG | sbj_P_12.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_12.mat` |  |
| verified_ok | EMG | sbj_P_13.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_13.mat` |  |
| verified_ok | EMG | sbj_P_14.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_14.mat` |  |
| verified_ok | EMG | sbj_P_15.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_15.mat` |  |
| verified_ok | EMG | sbj_P_16.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_16.mat` |  |
| verified_ok | EMG | sbj_P_17.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_17.mat` |  |
| verified_ok | EMG | sbj_P_18.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_18.mat` |  |
| verified_ok | EMG | sbj_P_19.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_19.mat` |  |
| verified_ok | EMG | sbj_P_20.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_20.mat` |  |
| verified_ok | EMG | sbj_P_21.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_21.mat` |  |
| verified_ok | EMG | sbj_P_22.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_22.mat` |  |
| verified_ok | EMG | sbj_P_23.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_23.mat` |  |
| verified_ok | EMG | sbj_P_24.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_24.mat` |  |
| verified_ok | EMG | sbj_P_25.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_25.mat` |  |
| verified_ok | EMG | sbj_P_26.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_26.mat` |  |
| verified_ok | EMG | sbj_P_27.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_27.mat` |  |
| verified_ok | EMG | sbj_P_28.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_28.mat` |  |
| verified_ok | EMG | sbj_P_29.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_29.mat` |  |
| verified_ok | EMG | sbj_P_30.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_30.mat` |  |
| verified_ok | EMG | sbj_P_31.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_31.mat` |  |
| verified_ok | EMG | sbj_P_32.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_32.mat` |  |
| verified_ok | EMG | sbj_P_33.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_33.mat` |  |
| verified_ok | EMG | sbj_P_34.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_34.mat` |  |
| verified_ok | EMG | sbj_P_35.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_35.mat` |  |
| verified_ok | EMG | sbj_P_36.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_36.mat` |  |
| verified_ok | EMG | sbj_P_37.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_37.mat` |  |
| verified_ok | EMG | sbj_P_38.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_38.mat` |  |
| verified_ok | EMG | sbj_P_39.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_39.mat` |  |
| verified_ok | EMG | sbj_P_40.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_40.mat` |  |
| verified_ok | EMG | sbj_P_41.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_41.mat` |  |
| verified_ok | EMG | sbj_P_42.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_42.mat` |  |
| verified_ok | EMG | sbj_P_43.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_43.mat` |  |
| verified_ok | EMG | sbj_P_44.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_44.mat` |  |
| verified_ok | EMG | sbj_P_45.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_45.mat` |  |
| verified_ok | EMG | sbj_P_46.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_46.mat` |  |
| verified_ok | EMG | sbj_P_47.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_47.mat` |  |
| verified_ok | EMG | sbj_P_48.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_48.mat` |  |
| verified_ok | EMG | sbj_P_49.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_49.mat` |  |
| verified_ok | EMG | sbj_P_50.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_50.mat` |  |
| verified_ok | EMG | sbj_P_52.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_52.mat` |  |
| verified_ok | EMG | sbj_P_53.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_53.mat` |  |
| verified_ok | EMG | sbj_P_54.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_54.mat` |  |
| verified_ok | EMG | sbj_P_55.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_55.mat` |  |
| verified_ok | EMG | sbj_P_56.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_56.mat` |  |
| verified_ok | EMG | sbj_P_57.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_57.mat` |  |
| verified_ok | EMG | sbj_P_58.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_58.mat` |  |
| verified_ok | EMG | sbj_P_59.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_59.mat` |  |
| verified_ok | EMG | sbj_P_60.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_60.mat` |  |
| verified_ok | EMG | sbj_P_61.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_61.mat` |  |
| verified_ok | EMG | sbj_P_62.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_62.mat` |  |
| verified_ok | EMG | sbj_P_63.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_63.mat` |  |
| verified_ok | EMG | sbj_P_64.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_64.mat` |  |
| verified_ok | EMG | sbj_P_65.mat | `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_65.mat` |  |
| verified_ok | labels | Arousal_SAM.csv | `/mnt/HDD/AliWorks/I-DARE/labels/Arousal_SAM.csv` |  |
| verified_ok | labels | Quadrants_SAM.csv | `/mnt/HDD/AliWorks/I-DARE/labels/Quadrants_SAM.csv` |  |
| verified_ok | labels | Sample.csv | `/mnt/HDD/AliWorks/I-DARE/labels/Sample.csv` |  |
| verified_ok | labels | Valence_SAM.csv | `/mnt/HDD/AliWorks/I-DARE/labels/Valence_SAM.csv` |  |
| verified_ok | metadata | Agreement_Raters.csv | `/mnt/HDD/AliWorks/I-DARE/metadata/Agreement_Raters.csv` |  |
| verified_ok | metadata | Stimuli_Specifications.csv | `/mnt/HDD/AliWorks/I-DARE/metadata/Stimuli_Specifications.csv` |  |

## Status Counts

- verified_ok: 133



# FILE: docs/data_audit_idare.md


# I-DARE Data Audit

This report was generated by `scripts/01_audit_datasets.py`.

No training was performed.

## Audit Status

Status: **PASSED**

## Local Paths

- I-DARE root: `/mnt/HDD/AliWorks/I-DARE`

- Manifest: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/docs/idare_download_manifest.csv`

## File Counts

| Item | Count |

|---|---:|

| Manifest first-stage rows | 133 |

| EEG `.mat` files | 63 |

| EMG `.mat` files | 64 |

| Label CSV files | 4 |

| Metadata CSV files | 2 |

| Missing expected first-stage files | 0 |

| Unexpected local files | 0 |


## Subject Coverage

- EEG subjects: `63`

- EMG subjects: `64`

- Common EEG+EMG subjects: `63`

- EEG-only subjects: `[]`

- EMG-only subjects: `[4]`


### Common Subject IDs

```text

[1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65]

```

## Label and Metadata CSV Summaries

### `Arousal_SAM.csv`

- Path: `/mnt/HDD/AliWorks/I-DARE/labels/Arousal_SAM.csv`

- Shape: `[32, 65]`

- Columns: `['Stimulus', 'sbj_P_01', 'sbj_P_02', 'sbj_P_03', 'sbj_P_04', 'sbj_P_05', 'sbj_P_06', 'sbj_P_07', 'sbj_P_08', 'sbj_P_09', 'sbj_P_10', 'sbj_P_11', 'sbj_P_12', 'sbj_P_13', 'sbj_P_14', 'sbj_P_15', 'sbj_P_16', 'sbj_P_17', 'sbj_P_18', 'sbj_P_19', 'sbj_P_20', 'sbj_P_21', 'sbj_P_22', 'sbj_P_23', 'sbj_P_24', 'sbj_P_25', 'sbj_P_26', 'sbj_P_27', 'sbj_P_28', 'sbj_P_29', 'sbj_P_30 ', 'sbj_P_31', 'sbj_P_32', 'sbj_P_33', 'sbj_P_34', 'sbj_P_35', 'sbj_P_36', 'sbj_P_37', 'sbj_P_38', 'sbj_P_39', 'sbj_P_40', 'sbj_P_41', 'sbj_P_42', 'sbj_P_43', 'sbj_P_44', 'sbj_P_45', 'sbj_P_46', 'sbj_P_47', 'sbj_P_48', 'sbj_P_49', 'sbj_P_50', 'sbj_P_52', 'sbj_P_53', 'sbj_P_54', 'sbj_P_55', 'sbj_P_56', 'sbj_P_57', 'sbj_P_58', 'sbj_P_59', 'sbj_P_60', 'sbj_P_61', 'sbj_P_62', 'sbj_P_63', 'sbj_P_64', 'sbj_P_65']`

- Missing values:

```json

{
  "Stimulus": 0,
  "sbj_P_01": 0,
  "sbj_P_02": 0,
  "sbj_P_03": 0,
  "sbj_P_04": 0,
  "sbj_P_05": 0,
  "sbj_P_06": 0,
  "sbj_P_07": 0,
  "sbj_P_08": 0,
  "sbj_P_09": 0,
  "sbj_P_10": 0,
  "sbj_P_11": 0,
  "sbj_P_12": 0,
  "sbj_P_13": 0,
  "sbj_P_14": 0,
  "sbj_P_15": 0,
  "sbj_P_16": 0,
  "sbj_P_17": 0,
  "sbj_P_18": 0,
  "sbj_P_19": 0,
  "sbj_P_20": 0,
  "sbj_P_21": 0,
  "sbj_P_22": 0,
  "sbj_P_23": 0,
  "sbj_P_24": 0,
  "sbj_P_25": 0,
  "sbj_P_26": 0,
  "sbj_P_27": 0,
  "sbj_P_28": 0,
  "sbj_P_29": 0,
  "sbj_P_30 ": 0,
  "sbj_P_31": 0,
  "sbj_P_32": 0,
  "sbj_P_33": 0,
  "sbj_P_34": 0,
  "sbj_P_35": 0,
  "sbj_P_36": 0,
  "sbj_P_37": 0,
  "sbj_P_38": 0,
  "sbj_P_39": 0,
  "sbj_P_40": 0,
  "sbj_P_41": 0,
  "sbj_P_42": 0,
  "sbj_P_43": 0,
  "sbj_P_44": 0,
  "sbj_P_45": 0,
  "sbj_P_46": 0,
  "sbj_P_47": 0,
  "sbj_P_48": 0,
  "sbj_P_49": 0,
  "sbj_P_50": 0,
  "sbj_P_52": 0,
  "sbj_P_53": 0,
  "sbj_P_54": 0,
  "sbj_P_55": 0,
  "sbj_P_56": 0,
  "sbj_P_57": 0,
  "sbj_P_58": 0,
  "sbj_P_59": 0,
  "sbj_P_60": 0,
  "sbj_P_61": 0,
  "sbj_P_62": 0,
  "sbj_P_63": 0,
  "sbj_P_64": 0,
  "sbj_P_65": 0
}

```

- Preview:

```json

[
  {
    "Stimulus": "1441",
    "sbj_P_01": "2",
    "sbj_P_02": "8",
    "sbj_P_03": "4",
    "sbj_P_04": "2",
    "sbj_P_05": "6",
    "sbj_P_06": "8",
    "sbj_P_07": "2",
    "sbj_P_08": "1",
    "sbj_P_09": "3",
    "sbj_P_10": "3",
    "sbj_P_11": "2",
    "sbj_P_12": "5",
    "sbj_P_13": "2",
    "sbj_P_14": "2",
    "sbj_P_15": "1",
    "sbj_P_16": "2",
    "sbj_P_17": "1",
    "sbj_P_18": "1",
    "sbj_P_19": "5",
    "sbj_P_20": "7",
    "sbj_P_21": "2",
    "sbj_P_22": "1",
    "sbj_P_23": "3",
    "sbj_P_24": "4",
    "sbj_P_25": "2",
    "sbj_P_26": "1",
    "sbj_P_27": "3",
    "sbj_P_28": "2",
    "sbj_P_29": "3",
    "sbj_P_30 ": "2",
    "sbj_P_31": "1",
    "sbj_P_32": "4",
    "sbj_P_33": "3",
    "sbj_P_34": "1",
    "sbj_P_35": "2",
    "sbj_P_36": "2",
    "sbj_P_37": "3",
    "sbj_P_38": "2",
    "sbj_P_39": "1",
    "sbj_P_40": "1",
    "sbj_P_41": "2",
    "sbj_P_42": "7",
    "sbj_P_43": "1",
    "sbj_P_44": "2",
    "sbj_P_45": "2",
    "sbj_P_46": "3",
    "sbj_P_47": "1",
    "sbj_P_48": "2",
    "sbj_P_49": "1",
    "sbj_P_50": "4",
    "sbj_P_52": "4",
    "sbj_P_53": "2",
    "sbj_P_54": "1",
    "sbj_P_55": "2",
    "sbj_P_56": "4",
    "sbj_P_57": "2",
    "sbj_P_58": "1",
    "sbj_P_59": "2",
    "sbj_P_60": "2",
    "sbj_P_61": "1",
    "sbj_P_62": "1",
    "sbj_P_63": "1",
    "sbj_P_64": "6",
    "sbj_P_65": "1"
  },
  {
    "Stimulus": "1750",
    "sbj_P_01": "3",
    "sbj_P_02": "6",
    "sbj_P_03": "4",
    "sbj_P_04": "5",
    "sbj_P_05": "2",
    "sbj_P_06": "8",
    "sbj_P_07": "3",
    "sbj_P_08": "2",
    "sbj_P_09": "7",
    "sbj_P_10": "2",
    "sbj_P_11": "6",
    "sbj_P_12": "4",
    "sbj_P_13": "1",
    "sbj_P_14": "3",
    "sbj_P_15": "4",
    "sbj_P_16": "2",
    "sbj_P_17": "3",
    "sbj_P_18": "1",
    "sbj_P_19": "4",
    "sbj_P_20": "6",
    "sbj_P_21": "3",
    "sbj_P_22": "2",
    "sbj_P_23": "2",
    "sbj_P_24": "3",
    "sbj_P_25": "1",
    "sbj_P_26": "1",
    "sbj_P_27": "3",
    "sbj_P_28": "1",
    "sbj_P_29": "3",
    "sbj_P_30 ": "2",
    "sbj_P_31": "3",
    "sbj_P_32": "1",
    "sbj_P_33": "5",
    "sbj_P_34": "2",
    "sbj_P_35": "5",
    "sbj_P_36": "4",
    "sbj_P_37": "3",
    "sbj_P_38": "3",
    "sbj_P_39": "6",
    "sbj_P_40": "8",
    "sbj_P_41": "3",
    "sbj_P_42": "7",
    "sbj_P_43": "1",
    "sbj_P_44": "2",
    "sbj_P_45": "3",
    "sbj_P_46": "6",
    "sbj_P_47": "5",
    "sbj_P_48": "4",
    "sbj_P_49": "2",
    "sbj_P_50": "1",
    "sbj_P_52": "5",
    "sbj_P_53": "1",
    "sbj_P_54": "2",
    "sbj_P_55": "1",
    "sbj_P_56": "3",
    "sbj_P_57": "1",
    "sbj_P_58": "4",
    "sbj_P_59": "6",
    "sbj_P_60": "1",
    "sbj_P_61": "1",
    "sbj_P_62": "1",
    "sbj_P_63": "1",
    "sbj_P_64": "2",
    "sbj_P_65": "1"
  },
  {
    "Stimulus": "2314",
    "sbj_P_01": "4",
    "sbj_P_02": "6",
    "sbj_P_03": "2",
    "sbj_P_04": "5",
    "sbj_P_05": "4",
    "sbj_P_06": "7",
    "sbj_P_07": "3",
    "sbj_P_08": "1",
    "sbj_P_09": "7",
    "sbj_P_10": "4",
    "sbj_P_11": "6",
    "sbj_P_12": "4",
    "sbj_P_13": "1",
    "sbj_P_14": "3",
    "sbj_P_15": "3",
    "sbj_P_16": "2",
    "sbj_P_17": "1",
    "sbj_P_18": "7",
    "sbj_P_19": "6",
    "sbj_P_20": "4",
    "sbj_P_21": "4",
    "sbj_P_22": "1",
    "sbj_P_23": "3",
    "sbj_P_24": "2",
    "sbj_P_25": "2",
    "sbj_P_26": "1",
    "sbj_P_27": "6",
    "sbj_P_28": "3",
    "sbj_P_29": "5",
    "sbj_P_30 ": "4",
    "sbj_P_31": "3",
    "sbj_P_32": "2",
    "sbj_P_33": "5",
    "sbj_P_34": "2",
    "sbj_P_35": "4",
    "sbj_P_36": "5",
    "sbj_P_37": "5",
    "sbj_P_38": "3",
    "sbj_P_39": "2",
    "sbj_P_40": "1",
    "sbj_P_41": "2",
    "sbj_P_42": "5",
    "sbj_P_43": "1",
    "sbj_P_44": "2",
    "sbj_P_45": "6",
    "sbj_P_46": "4",
    "sbj_P_47": "5",
    "sbj_P_48": "3",
    "sbj_P_49": "2",
    "sbj_P_50": "5",
    "sbj_P_52": "7",
    "sbj_P_53": "2",
    "sbj_P_54": "4",
    "sbj_P_55": "1",
    "sbj_P_56": "2",
    "sbj_P_57": "4",
    "sbj_P_58": "2",
    "sbj_P_59": "7",
    "sbj_P_60": "6",
    "sbj_P_61": "1",
    "sbj_P_62": "3",
    "sbj_P_63": "1",
    "sbj_P_64": "5",
    "sbj_P_65": "1"
  }
]

```

### `Quadrants_SAM.csv`

- Path: `/mnt/HDD/AliWorks/I-DARE/labels/Quadrants_SAM.csv`

- Shape: `[32, 66]`

- Columns: `['Stimulus', 'Quadrant (GS)', 'sbj_P_01', 'sbj_P_02', 'sbj_P_03', 'sbj_P_04', 'sbj_P_05', 'sbj_P_06', 'sbj_P_07', 'sbj_P_08', 'sbj_P_09', 'sbj_P_10', 'sbj_P_11', 'sbj_P_12', 'sbj_P_13', 'sbj_P_14', 'sbj_P_15', 'sbj_P_16', 'sbj_P_17', 'sbj_P_18', 'sbj_P_19', 'sbj_P_20', 'sbj_P_21', 'sbj_P_22', 'sbj_P_23', 'sbj_P_24', 'sbj_P_25', 'sbj_P_26', 'sbj_P_27', 'sbj_P_28', 'sbj_P_29', 'sbj_P_30 ', 'sbj_P_31', 'sbj_P_32', 'sbj_P_33', 'sbj_P_34', 'sbj_P_35', 'sbj_P_36', 'sbj_P_37', 'sbj_P_38', 'sbj_P_39', 'sbj_P_40', 'sbj_P_41', 'sbj_P_42', 'sbj_P_43', 'sbj_P_44', 'sbj_P_45', 'sbj_P_46', 'sbj_P_47', 'sbj_P_48', 'sbj_P_49', 'sbj_P_50', 'sbj_P_52', 'sbj_P_53', 'sbj_P_54', 'sbj_P_55', 'sbj_P_56', 'sbj_P_57', 'sbj_P_58', 'sbj_P_59', 'sbj_P_60', 'sbj_P_61', 'sbj_P_62', 'sbj_P_63', 'sbj_P_64', 'sbj_P_65']`

- Missing values:

```json

{
  "Stimulus": 0,
  "Quadrant (GS)": 0,
  "sbj_P_01": 0,
  "sbj_P_02": 0,
  "sbj_P_03": 0,
  "sbj_P_04": 0,
  "sbj_P_05": 0,
  "sbj_P_06": 0,
  "sbj_P_07": 0,
  "sbj_P_08": 0,
  "sbj_P_09": 0,
  "sbj_P_10": 0,
  "sbj_P_11": 0,
  "sbj_P_12": 0,
  "sbj_P_13": 0,
  "sbj_P_14": 0,
  "sbj_P_15": 0,
  "sbj_P_16": 0,
  "sbj_P_17": 0,
  "sbj_P_18": 0,
  "sbj_P_19": 0,
  "sbj_P_20": 0,
  "sbj_P_21": 0,
  "sbj_P_22": 0,
  "sbj_P_23": 0,
  "sbj_P_24": 0,
  "sbj_P_25": 0,
  "sbj_P_26": 0,
  "sbj_P_27": 0,
  "sbj_P_28": 0,
  "sbj_P_29": 0,
  "sbj_P_30 ": 0,
  "sbj_P_31": 0,
  "sbj_P_32": 0,
  "sbj_P_33": 0,
  "sbj_P_34": 0,
  "sbj_P_35": 0,
  "sbj_P_36": 0,
  "sbj_P_37": 0,
  "sbj_P_38": 0,
  "sbj_P_39": 0,
  "sbj_P_40": 0,
  "sbj_P_41": 0,
  "sbj_P_42": 0,
  "sbj_P_43": 0,
  "sbj_P_44": 0,
  "sbj_P_45": 0,
  "sbj_P_46": 0,
  "sbj_P_47": 0,
  "sbj_P_48": 0,
  "sbj_P_49": 0,
  "sbj_P_50": 0,
  "sbj_P_52": 0,
  "sbj_P_53": 0,
  "sbj_P_54": 0,
  "sbj_P_55": 0,
  "sbj_P_56": 0,
  "sbj_P_57": 0,
  "sbj_P_58": 0,
  "sbj_P_59": 0,
  "sbj_P_60": 0,
  "sbj_P_61": 0,
  "sbj_P_62": 0,
  "sbj_P_63": 0,
  "sbj_P_64": 0,
  "sbj_P_65": 0
}

```

- Preview:

```json

[
  {
    "Stimulus": "1441",
    "Quadrant (GS)": "HVLA",
    "sbj_P_01": "HVLA",
    "sbj_P_02": "HVHA",
    "sbj_P_03": "HVLA",
    "sbj_P_04": "HVLA",
    "sbj_P_05": "HVHA",
    "sbj_P_06": "HVHA",
    "sbj_P_07": "HVLA",
    "sbj_P_08": "HVLA",
    "sbj_P_09": "HVLA",
    "sbj_P_10": "HVLA",
    "sbj_P_11": "HVLA",
    "sbj_P_12": "HVLA",
    "sbj_P_13": "HVLA",
    "sbj_P_14": "HVLA",
    "sbj_P_15": "HVLA",
    "sbj_P_16": "LVLA",
    "sbj_P_17": "HVLA",
    "sbj_P_18": "HVLA",
    "sbj_P_19": "HVLA",
    "sbj_P_20": "HVHA",
    "sbj_P_21": "HVLA",
    "sbj_P_22": "HVLA",
    "sbj_P_23": "HVLA",
    "sbj_P_24": "HVLA",
    "sbj_P_25": "HVLA",
    "sbj_P_26": "LVLA",
    "sbj_P_27": "HVLA",
    "sbj_P_28": "HVLA",
    "sbj_P_29": "HVLA",
    "sbj_P_30 ": "HVLA",
    "sbj_P_31": "HVLA",
    "sbj_P_32": "HVLA",
    "sbj_P_33": "HVLA",
    "sbj_P_34": "HVLA",
    "sbj_P_35": "HVLA",
    "sbj_P_36": "HVLA",
    "sbj_P_37": "HVLA",
    "sbj_P_38": "HVLA",
    "sbj_P_39": "HVLA",
    "sbj_P_40": "HVLA",
    "sbj_P_41": "HVLA",
    "sbj_P_42": "HVHA",
    "sbj_P_43": "HVLA",
    "sbj_P_44": "HVLA",
    "sbj_P_45": "HVLA",
    "sbj_P_46": "HVLA",
    "sbj_P_47": "HVLA",
    "sbj_P_48": "HVLA",
    "sbj_P_49": "HVLA",
    "sbj_P_50": "HVLA",
    "sbj_P_52": "HVLA",
    "sbj_P_53": "HVLA",
    "sbj_P_54": "HVLA",
    "sbj_P_55": "HVLA",
    "sbj_P_56": "HVLA",
    "sbj_P_57": "HVLA",
    "sbj_P_58": "HVLA",
    "sbj_P_59": "HVLA",
    "sbj_P_60": "HVLA",
    "sbj_P_61": "HVLA",
    "sbj_P_62": "HVLA",
    "sbj_P_63": "HVLA",
    "sbj_P_64": "LVHA",
    "sbj_P_65": "HVLA"
  },
  {
    "Stimulus": "1750",
    "Quadrant (GS)": "HVLA",
    "sbj_P_01": "LVLA",
    "sbj_P_02": "HVHA",
    "sbj_P_03": "HVLA",
    "sbj_P_04": "HVLA",
    "sbj_P_05": "HVLA",
    "sbj_P_06": "HVHA",
    "sbj_P_07": "HVLA",
    "sbj_P_08": "HVLA",
    "sbj_P_09": "HVHA",
    "sbj_P_10": "HVLA",
    "sbj_P_11": "HVHA",
    "sbj_P_12": "HVLA",
    "sbj_P_13": "HVLA",
    "sbj_P_14": "HVLA",
    "sbj_P_15": "HVLA",
    "sbj_P_16": "HVLA",
    "sbj_P_17": "HVLA",
    "sbj_P_18": "HVLA",
    "sbj_P_19": "HVLA",
    "sbj_P_20": "HVHA",
    "sbj_P_21": "HVLA",
    "sbj_P_22": "LVLA",
    "sbj_P_23": "HVLA",
    "sbj_P_24": "HVLA",
    "sbj_P_25": "HVLA",
    "sbj_P_26": "LVLA",
    "sbj_P_27": "HVLA",
    "sbj_P_28": "HVLA",
    "sbj_P_29": "HVLA",
    "sbj_P_30 ": "HVLA",
    "sbj_P_31": "HVLA",
    "sbj_P_32": "HVLA",
    "sbj_P_33": "HVLA",
    "sbj_P_34": "LVLA",
    "sbj_P_35": "HVLA",
    "sbj_P_36": "HVLA",
    "sbj_P_37": "HVLA",
    "sbj_P_38": "HVLA",
    "sbj_P_39": "HVHA",
    "sbj_P_40": "HVHA",
    "sbj_P_41": "HVLA",
    "sbj_P_42": "HVHA",
    "sbj_P_43": "HVLA",
    "sbj_P_44": "HVLA",
    "sbj_P_45": "HVLA",
    "sbj_P_46": "HVHA",
    "sbj_P_47": "HVLA",
    "sbj_P_48": "HVLA",
    "sbj_P_49": "HVLA",
    "sbj_P_50": "HVLA",
    "sbj_P_52": "HVLA",
    "sbj_P_53": "HVLA",
    "sbj_P_54": "HVLA",
    "sbj_P_55": "HVLA",
    "sbj_P_56": "HVLA",
    "sbj_P_57": "HVLA",
    "sbj_P_58": "HVLA",
    "sbj_P_59": "HVHA",
    "sbj_P_60": "HVLA",
    "sbj_P_61": "HVLA",
    "sbj_P_62": "HVLA",
    "sbj_P_63": "HVLA",
    "sbj_P_64": "HVLA",
    "sbj_P_65": "HVLA"
  },
  {
    "Stimulus": "2314",
    "Quadrant (GS)": "HVLA",
    "sbj_P_01": "HVLA",
    "sbj_P_02": "HVHA",
    "sbj_P_03": "HVLA",
    "sbj_P_04": "HVLA",
    "sbj_P_05": "HVLA",
    "sbj_P_06": "HVHA",
    "sbj_P_07": "HVLA",
    "sbj_P_08": "HVLA",
    "sbj_P_09": "HVHA",
    "sbj_P_10": "HVLA",
    "sbj_P_11": "HVHA",
    "sbj_P_12": "HVLA",
    "sbj_P_13": "LVLA",
    "sbj_P_14": "HVLA",
    "sbj_P_15": "HVLA",
    "sbj_P_16": "HVLA",
    "sbj_P_17": "HVLA",
    "sbj_P_18": "HVHA",
    "sbj_P_19": "HVHA",
    "sbj_P_20": "LVLA",
    "sbj_P_21": "HVLA",
    "sbj_P_22": "HVLA",
    "sbj_P_23": "HVLA",
    "sbj_P_24": "HVLA",
    "sbj_P_25": "HVLA",
    "sbj_P_26": "HVLA",
    "sbj_P_27": "HVHA",
    "sbj_P_28": "HVLA",
    "sbj_P_29": "HVLA",
    "sbj_P_30 ": "HVLA",
    "sbj_P_31": "HVLA",
    "sbj_P_32": "HVLA",
    "sbj_P_33": "HVLA",
    "sbj_P_34": "HVLA",
    "sbj_P_35": "HVLA",
    "sbj_P_36": "HVLA",
    "sbj_P_37": "LVLA",
    "sbj_P_38": "LVLA",
    "sbj_P_39": "HVLA",
    "sbj_P_40": "HVLA",
    "sbj_P_41": "LVLA",
    "sbj_P_42": "HVLA",
    "sbj_P_43": "HVLA",
    "sbj_P_44": "LVLA",
    "sbj_P_45": "HVHA",
    "sbj_P_46": "LVLA",
    "sbj_P_47": "HVLA",
    "sbj_P_48": "HVLA",
    "sbj_P_49": "HVLA",
    "sbj_P_50": "HVLA",
    "sbj_P_52": "HVHA",
    "sbj_P_53": "HVLA",
    "sbj_P_54": "HVLA",
    "sbj_P_55": "HVLA",
    "sbj_P_56": "HVLA",
    "sbj_P_57": "HVLA",
    "sbj_P_58": "HVLA",
    "sbj_P_59": "HVHA",
    "sbj_P_60": "HVHA",
    "sbj_P_61": "HVLA",
    "sbj_P_62": "HVLA",
    "sbj_P_63": "HVLA",
    "sbj_P_64": "LVLA",
    "sbj_P_65": "HVLA"
  }
]

```

### `Sample.csv`

- Path: `/mnt/HDD/AliWorks/I-DARE/labels/Sample.csv`

- Shape: `[63, 3]`

- Columns: `['Subject', 'Gender', 'Age']`

- Missing values:

```json

{
  "Subject": 0,
  "Gender": 0,
  "Age": 0
}

```

- Preview:

```json

[
  {
    "Subject": "sbj_P_01",
    "Gender": "FEMALE",
    "Age": "23"
  },
  {
    "Subject": "sbj_P_02",
    "Gender": "MALE",
    "Age": "24"
  },
  {
    "Subject": "sbj_P_03",
    "Gender": "FEMALE",
    "Age": "24"
  }
]

```

### `Valence_SAM.csv`

- Path: `/mnt/HDD/AliWorks/I-DARE/labels/Valence_SAM.csv`

- Shape: `[32, 65]`

- Columns: `['Stimulus', 'sbj_P_01', 'sbj_P_02', 'sbj_P_03', 'sbj_P_04', 'sbj_P_05', 'sbj_P_06', 'sbj_P_07', 'sbj_P_08', 'sbj_P_09', 'sbj_P_10', 'sbj_P_11', 'sbj_P_12', 'sbj_P_13', 'sbj_P_14', 'sbj_P_15', 'sbj_P_16', 'sbj_P_17', 'sbj_P_18', 'sbj_P_19', 'sbj_P_20', 'sbj_P_21', 'sbj_P_22', 'sbj_P_23', 'sbj_P_24', 'sbj_P_25', 'sbj_P_26', 'sbj_P_27', 'sbj_P_28', 'sbj_P_29', 'sbj_P_30 ', 'sbj_P_31', 'sbj_P_32', 'sbj_P_33', 'sbj_P_34', 'sbj_P_35', 'sbj_P_36', 'sbj_P_37', 'sbj_P_38', 'sbj_P_39', 'sbj_P_40', 'sbj_P_41', 'sbj_P_42', 'sbj_P_43', 'sbj_P_44', 'sbj_P_45', 'sbj_P_46', 'sbj_P_47', 'sbj_P_48', 'sbj_P_49', 'sbj_P_50', 'sbj_P_52', 'sbj_P_53', 'sbj_P_54', 'sbj_P_55', 'sbj_P_56', 'sbj_P_57', 'sbj_P_58', 'sbj_P_59', 'sbj_P_60', 'sbj_P_61', 'sbj_P_62', 'sbj_P_63', 'sbj_P_64', 'sbj_P_65']`

- Missing values:

```json

{
  "Stimulus": 0,
  "sbj_P_01": 0,
  "sbj_P_02": 0,
  "sbj_P_03": 0,
  "sbj_P_04": 0,
  "sbj_P_05": 0,
  "sbj_P_06": 0,
  "sbj_P_07": 0,
  "sbj_P_08": 0,
  "sbj_P_09": 0,
  "sbj_P_10": 0,
  "sbj_P_11": 0,
  "sbj_P_12": 0,
  "sbj_P_13": 0,
  "sbj_P_14": 0,
  "sbj_P_15": 0,
  "sbj_P_16": 0,
  "sbj_P_17": 0,
  "sbj_P_18": 0,
  "sbj_P_19": 0,
  "sbj_P_20": 0,
  "sbj_P_21": 0,
  "sbj_P_22": 0,
  "sbj_P_23": 0,
  "sbj_P_24": 0,
  "sbj_P_25": 0,
  "sbj_P_26": 0,
  "sbj_P_27": 0,
  "sbj_P_28": 0,
  "sbj_P_29": 0,
  "sbj_P_30 ": 0,
  "sbj_P_31": 0,
  "sbj_P_32": 0,
  "sbj_P_33": 0,
  "sbj_P_34": 0,
  "sbj_P_35": 0,
  "sbj_P_36": 0,
  "sbj_P_37": 0,
  "sbj_P_38": 0,
  "sbj_P_39": 0,
  "sbj_P_40": 0,
  "sbj_P_41": 0,
  "sbj_P_42": 0,
  "sbj_P_43": 0,
  "sbj_P_44": 0,
  "sbj_P_45": 0,
  "sbj_P_46": 0,
  "sbj_P_47": 0,
  "sbj_P_48": 0,
  "sbj_P_49": 0,
  "sbj_P_50": 0,
  "sbj_P_52": 0,
  "sbj_P_53": 0,
  "sbj_P_54": 0,
  "sbj_P_55": 0,
  "sbj_P_56": 0,
  "sbj_P_57": 0,
  "sbj_P_58": 0,
  "sbj_P_59": 0,
  "sbj_P_60": 0,
  "sbj_P_61": 0,
  "sbj_P_62": 0,
  "sbj_P_63": 0,
  "sbj_P_64": 0,
  "sbj_P_65": 0
}

```

- Preview:

```json

[
  {
    "Stimulus": "1441",
    "sbj_P_01": "7",
    "sbj_P_02": "8",
    "sbj_P_03": "8",
    "sbj_P_04": "7",
    "sbj_P_05": "9",
    "sbj_P_06": "8",
    "sbj_P_07": "7",
    "sbj_P_08": "8",
    "sbj_P_09": "6",
    "sbj_P_10": "8",
    "sbj_P_11": "9",
    "sbj_P_12": "9",
    "sbj_P_13": "6",
    "sbj_P_14": "7",
    "sbj_P_15": "6",
    "sbj_P_16": "5",
    "sbj_P_17": "9",
    "sbj_P_18": "8",
    "sbj_P_19": "7",
    "sbj_P_20": "8",
    "sbj_P_21": "9",
    "sbj_P_22": "6",
    "sbj_P_23": "8",
    "sbj_P_24": "7",
    "sbj_P_25": "7",
    "sbj_P_26": "4",
    "sbj_P_27": "8",
    "sbj_P_28": "7",
    "sbj_P_29": "7",
    "sbj_P_30 ": "8",
    "sbj_P_31": "9",
    "sbj_P_32": "6",
    "sbj_P_33": "7",
    "sbj_P_34": "6",
    "sbj_P_35": "7",
    "sbj_P_36": "9",
    "sbj_P_37": "6",
    "sbj_P_38": "8",
    "sbj_P_39": "7",
    "sbj_P_40": "9",
    "sbj_P_41": "6",
    "sbj_P_42": "8",
    "sbj_P_43": "7",
    "sbj_P_44": "6",
    "sbj_P_45": "7",
    "sbj_P_46": "8",
    "sbj_P_47": "9",
    "sbj_P_48": "8",
    "sbj_P_49": "7",
    "sbj_P_50": "8",
    "sbj_P_52": "7",
    "sbj_P_53": "7",
    "sbj_P_54": "8",
    "sbj_P_55": "8",
    "sbj_P_56": "8",
    "sbj_P_57": "9",
    "sbj_P_58": "8",
    "sbj_P_59": "9",
    "sbj_P_60": "8",
    "sbj_P_61": "9",
    "sbj_P_62": "8",
    "sbj_P_63": "9",
    "sbj_P_64": "5",
    "sbj_P_65": "9"
  },
  {
    "Stimulus": "1750",
    "sbj_P_01": "5",
    "sbj_P_02": "6",
    "sbj_P_03": "9",
    "sbj_P_04": "8",
    "sbj_P_05": "9",
    "sbj_P_06": "8",
    "sbj_P_07": "7",
    "sbj_P_08": "6",
    "sbj_P_09": "7",
    "sbj_P_10": "6",
    "sbj_P_11": "9",
    "sbj_P_12": "6",
    "sbj_P_13": "6",
    "sbj_P_14": "7",
    "sbj_P_15": "6",
    "sbj_P_16": "6",
    "sbj_P_17": "9",
    "sbj_P_18": "9",
    "sbj_P_19": "6",
    "sbj_P_20": "7",
    "sbj_P_21": "9",
    "sbj_P_22": "5",
    "sbj_P_23": "9",
    "sbj_P_24": "7",
    "sbj_P_25": "7",
    "sbj_P_26": "5",
    "sbj_P_27": "6",
    "sbj_P_28": "6",
    "sbj_P_29": "7",
    "sbj_P_30 ": "7",
    "sbj_P_31": "8",
    "sbj_P_32": "6",
    "sbj_P_33": "8",
    "sbj_P_34": "5",
    "sbj_P_35": "7",
    "sbj_P_36": "9",
    "sbj_P_37": "6",
    "sbj_P_38": "7",
    "sbj_P_39": "7",
    "sbj_P_40": "9",
    "sbj_P_41": "6",
    "sbj_P_42": "8",
    "sbj_P_43": "7",
    "sbj_P_44": "7",
    "sbj_P_45": "6",
    "sbj_P_46": "6",
    "sbj_P_47": "9",
    "sbj_P_48": "7",
    "sbj_P_49": "6",
    "sbj_P_50": "9",
    "sbj_P_52": "8",
    "sbj_P_53": "6",
    "sbj_P_54": "8",
    "sbj_P_55": "9",
    "sbj_P_56": "8",
    "sbj_P_57": "6",
    "sbj_P_58": "8",
    "sbj_P_59": "8",
    "sbj_P_60": "8",
    "sbj_P_61": "8",
    "sbj_P_62": "9",
    "sbj_P_63": "7",
    "sbj_P_64": "6",
    "sbj_P_65": "7"
  },
  {
    "Stimulus": "2314",
    "sbj_P_01": "6",
    "sbj_P_02": "7",
    "sbj_P_03": "7",
    "sbj_P_04": "8",
    "sbj_P_05": "7",
    "sbj_P_06": "8",
    "sbj_P_07": "7",
    "sbj_P_08": "8",
    "sbj_P_09": "8",
    "sbj_P_10": "6",
    "sbj_P_11": "8",
    "sbj_P_12": "6",
    "sbj_P_13": "5",
    "sbj_P_14": "7",
    "sbj_P_15": "7",
    "sbj_P_16": "7",
    "sbj_P_17": "9",
    "sbj_P_18": "9",
    "sbj_P_19": "8",
    "sbj_P_20": "5",
    "sbj_P_21": "8",
    "sbj_P_22": "7",
    "sbj_P_23": "6",
    "sbj_P_24": "7",
    "sbj_P_25": "9",
    "sbj_P_26": "8",
    "sbj_P_27": "6",
    "sbj_P_28": "7",
    "sbj_P_29": "8",
    "sbj_P_30 ": "7",
    "sbj_P_31": "9",
    "sbj_P_32": "6",
    "sbj_P_33": "7",
    "sbj_P_34": "7",
    "sbj_P_35": "6",
    "sbj_P_36": "9",
    "sbj_P_37": "5",
    "sbj_P_38": "4",
    "sbj_P_39": "7",
    "sbj_P_40": "9",
    "sbj_P_41": "5",
    "sbj_P_42": "9",
    "sbj_P_43": "8",
    "sbj_P_44": "5",
    "sbj_P_45": "7",
    "sbj_P_46": "4",
    "sbj_P_47": "9",
    "sbj_P_48": "8",
    "sbj_P_49": "7",
    "sbj_P_50": "8",
    "sbj_P_52": "6",
    "sbj_P_53": "7",
    "sbj_P_54": "8",
    "sbj_P_55": "9",
    "sbj_P_56": "7",
    "sbj_P_57": "8",
    "sbj_P_58": "7",
    "sbj_P_59": "8",
    "sbj_P_60": "9",
    "sbj_P_61": "9",
    "sbj_P_62": "7",
    "sbj_P_63": "6",
    "sbj_P_64": "5",
    "sbj_P_65": "9"
  }
]

```

### `Agreement_Raters.csv`

- Path: `/mnt/HDD/AliWorks/I-DARE/metadata/Agreement_Raters.csv`

- Shape: `[32, 18]`

- Columns: `['Stimulus', 'Dataset', 'Quadrant', 'Rater 1', 'Rater 2', 'Rater 3', 'Rater 4', 'Rater 5', 'Rater 6', 'Rater 7', 'Rater 8', 'Rater 9', 'Agreement', 'Distance', 'Valence (M)', 'Valence (SD)', 'Arousal (M)', 'Arousal (SD)']`

- Missing values:

```json

{
  "Stimulus": 0,
  "Dataset": 0,
  "Quadrant": 0,
  "Rater 1": 0,
  "Rater 2": 0,
  "Rater 3": 0,
  "Rater 4": 0,
  "Rater 5": 0,
  "Rater 6": 0,
  "Rater 7": 0,
  "Rater 8": 0,
  "Rater 9": 0,
  "Agreement": 0,
  "Distance": 0,
  "Valence (M)": 0,
  "Valence (SD)": 0,
  "Arousal (M)": 0,
  "Arousal (SD)": 0
}

```

- Preview:

```json

[
  {
    "Stimulus": "Flowers 6",
    "Dataset": "OASIS",
    "Quadrant": "HVLA",
    "Rater 1": "1",
    "Rater 2": "1",
    "Rater 3": "1",
    "Rater 4": "1",
    "Rater 5": "1",
    "Rater 6": "1",
    "Rater 7": "1",
    "Rater 8": "1",
    "Rater 9": "1",
    "Agreement": "1.0",
    "Distance": "0.117",
    "Valence (M)": "5.944444444",
    "Valence (SD)": "0.915426802",
    "Arousal (M)": "3.009615385",
    "Arousal (SD)": "1.663399212"
  },
  {
    "Stimulus": "1441",
    "Dataset": "IAPS",
    "Quadrant": "HVLA",
    "Rater 1": "1",
    "Rater 2": "1",
    "Rater 3": "1",
    "Rater 4": "1",
    "Rater 5": "1",
    "Rater 6": "1",
    "Rater 7": "1",
    "Rater 8": "1",
    "Rater 9": "1",
    "Agreement": "1.0",
    "Distance": "0.09",
    "Valence (M)": "7.97",
    "Valence (SD)": "1.28",
    "Arousal (M)": "3.94",
    "Arousal (SD)": "2.38"
  },
  {
    "Stimulus": "Garbage dump 6",
    "Dataset": "OASIS",
    "Quadrant": "LVLA",
    "Rater 1": "1",
    "Rater 2": "0",
    "Rater 3": "1",
    "Rater 4": "1",
    "Rater 5": "1",
    "Rater 6": "1",
    "Rater 7": "1",
    "Rater 8": "1",
    "Rater 9": "1",
    "Agreement": "0.888888889",
    "Distance": "0.242",
    "Valence (M)": "1.962962963",
    "Valence (SD)": "0.946473296",
    "Arousal (M)": "3.317307692",
    "Arousal (SD)": "1.876085695"
  }
]

```

### `Stimuli_Specifications.csv`

- Path: `/mnt/HDD/AliWorks/I-DARE/metadata/Stimuli_Specifications.csv`

- Shape: `[100, 66]`

- Columns: `['Stimulus', 'Description', 'sbj_P_01', 'sbj_P_02', 'sbj_P_03', 'sbj_P_04', 'sbj_P_05', 'sbj_P_06', 'sbj_P_07', 'sbj_P_08', 'sbj_P_09', 'sbj_P_10', 'sbj_P_11', 'sbj_P_12', 'sbj_P_13', 'sbj_P_14', 'sbj_P_15', 'sbj_P_16', 'sbj_P_17', 'sbj_P_18', 'sbj_P_19', 'sbj_P_20', 'sbj_P_21', 'sbj_P_22', 'sbj_P_23', 'sbj_P_24', 'sbj_P_25', 'sbj_P_26', 'sbj_P_27', 'sbj_P_28', 'sbj_P_29', 'sbj_P_30', 'sbj_P_31', 'sbj_P_32', 'sbj_P_33', 'sbj_P_34', 'sbj_P_35', 'sbj_P_36', 'sbj_P_37', 'sbj_P_38', 'sbj_P_39', 'sbj_P_40', 'sbj_P_41', 'sbj_P_42', 'sbj_P_43', 'sbj_P_44', 'sbj_P_45', 'sbj_P_46', 'sbj_P_47', 'sbj_P_48', 'sbj_P_49', 'sbj_P_50', 'sbj_P_52', 'sbj_P_53', 'sbj_P_54', 'sbj_P_55', 'sbj_P_56', 'sbj_P_57', 'sbj_P_58', 'sbj_P_59', 'sbj_P_60', 'sbj_P_61', 'sbj_P_62', 'sbj_P_63', 'sbj_P_64', 'sbj_P_65']`

- Missing values:

```json

{
  "Stimulus": 0,
  "Description": 0,
  "sbj_P_01": 0,
  "sbj_P_02": 0,
  "sbj_P_03": 0,
  "sbj_P_04": 0,
  "sbj_P_05": 0,
  "sbj_P_06": 0,
  "sbj_P_07": 0,
  "sbj_P_08": 0,
  "sbj_P_09": 0,
  "sbj_P_10": 0,
  "sbj_P_11": 0,
  "sbj_P_12": 0,
  "sbj_P_13": 0,
  "sbj_P_14": 0,
  "sbj_P_15": 0,
  "sbj_P_16": 0,
  "sbj_P_17": 0,
  "sbj_P_18": 0,
  "sbj_P_19": 0,
  "sbj_P_20": 0,
  "sbj_P_21": 0,
  "sbj_P_22": 0,
  "sbj_P_23": 0,
  "sbj_P_24": 0,
  "sbj_P_25": 0,
  "sbj_P_26": 0,
  "sbj_P_27": 0,
  "sbj_P_28": 0,
  "sbj_P_29": 0,
  "sbj_P_30": 0,
  "sbj_P_31": 0,
  "sbj_P_32": 0,
  "sbj_P_33": 0,
  "sbj_P_34": 0,
  "sbj_P_35": 0,
  "sbj_P_36": 0,
  "sbj_P_37": 0,
  "sbj_P_38": 0,
  "sbj_P_39": 0,
  "sbj_P_40": 0,
  "sbj_P_41": 0,
  "sbj_P_42": 0,
  "sbj_P_43": 0,
  "sbj_P_44": 0,
  "sbj_P_45": 0,
  "sbj_P_46": 0,
  "sbj_P_47": 0,
  "sbj_P_48": 0,
  "sbj_P_49": 0,
  "sbj_P_50": 0,
  "sbj_P_52": 0,
  "sbj_P_53": 0,
  "sbj_P_54": 0,
  "sbj_P_55": 0,
  "sbj_P_56": 0,
  "sbj_P_57": 0,
  "sbj_P_58": 0,
  "sbj_P_59": 0,
  "sbj_P_60": 0,
  "sbj_P_61": 0,
  "sbj_P_62": 0,
  "sbj_P_63": 0,
  "sbj_P_64": 0,
  "sbj_P_65": 0
}

```

- Preview:

```json

[
  {
    "Stimulus": "EYC",
    "Description": "60s-long eye-closed baseline",
    "sbj_P_01": "59.997",
    "sbj_P_02": "59.989",
    "sbj_P_03": "59.999",
    "sbj_P_04": "59.996",
    "sbj_P_05": "59.996",
    "sbj_P_06": "60.009",
    "sbj_P_07": "60.007",
    "sbj_P_08": "60.0",
    "sbj_P_09": "59.992",
    "sbj_P_10": "59.997",
    "sbj_P_11": "60.001",
    "sbj_P_12": "60.016",
    "sbj_P_13": "60.004",
    "sbj_P_14": "60.002",
    "sbj_P_15": "60.012",
    "sbj_P_16": "59.996",
    "sbj_P_17": "59.997",
    "sbj_P_18": "59.989",
    "sbj_P_19": "59.991",
    "sbj_P_20": "59.998",
    "sbj_P_21": "59.998",
    "sbj_P_22": "59.999",
    "sbj_P_23": "59.999",
    "sbj_P_24": "59.991",
    "sbj_P_25": "59.997",
    "sbj_P_26": "60.002",
    "sbj_P_27": "59.989",
    "sbj_P_28": "59.999",
    "sbj_P_29": "60.001",
    "sbj_P_30": "59.999",
    "sbj_P_31": "59.999",
    "sbj_P_32": "59.995",
    "sbj_P_33": "60.012",
    "sbj_P_34": "60.011",
    "sbj_P_35": "60.005",
    "sbj_P_36": "59.998",
    "sbj_P_37": "59.997",
    "sbj_P_38": "60.003",
    "sbj_P_39": "60.013",
    "sbj_P_40": "60.013",
    "sbj_P_41": "59.991",
    "sbj_P_42": "60.005",
    "sbj_P_43": "60.0",
    "sbj_P_44": "59.99",
    "sbj_P_45": "59.996",
    "sbj_P_46": "59.997",
    "sbj_P_47": "59.995",
    "sbj_P_48": "60.005",
    "sbj_P_49": "60.0",
    "sbj_P_50": "59.996",
    "sbj_P_52": "59.998",
    "sbj_P_53": "60.001",
    "sbj_P_54": "59.991",
    "sbj_P_55": "59.999",
    "sbj_P_56": "59.998",
    "sbj_P_57": "59.994",
    "sbj_P_58": "59.997",
    "sbj_P_59": "59.999",
    "sbj_P_60": "59.991",
    "sbj_P_61": "60.009",
    "sbj_P_62": "59.995",
    "sbj_P_63": "59.994",
    "sbj_P_64": "59.994",
    "sbj_P_65": "59.994"
  },
  {
    "Stimulus": "IST_BSL",
    "Description": "Instructions for the 120s-long neutral baseline",
    "sbj_P_01": "19.995",
    "sbj_P_02": "14.959",
    "sbj_P_03": "19.998",
    "sbj_P_04": "19.996",
    "sbj_P_05": "20.002",
    "sbj_P_06": "19.995",
    "sbj_P_07": "19.988",
    "sbj_P_08": "19.988",
    "sbj_P_09": "19.999",
    "sbj_P_10": "20.0",
    "sbj_P_11": "20.002",
    "sbj_P_12": "20.0",
    "sbj_P_13": "19.992",
    "sbj_P_14": "19.99",
    "sbj_P_15": "19.995",
    "sbj_P_16": "19.991",
    "sbj_P_17": "20.0",
    "sbj_P_18": "19.992",
    "sbj_P_19": "19.992",
    "sbj_P_20": "19.997",
    "sbj_P_21": "20.001",
    "sbj_P_22": "20.0",
    "sbj_P_23": "19.985",
    "sbj_P_24": "20.0",
    "sbj_P_25": "20.0",
    "sbj_P_26": "19.995",
    "sbj_P_27": "19.999",
    "sbj_P_28": "19.99",
    "sbj_P_29": "19.996",
    "sbj_P_30": "19.995",
    "sbj_P_31": "20.014",
    "sbj_P_32": "20.009",
    "sbj_P_33": "19.987",
    "sbj_P_34": "19.998",
    "sbj_P_35": "19.999",
    "sbj_P_36": "19.993",
    "sbj_P_37": "19.993",
    "sbj_P_38": "20.007",
    "sbj_P_39": "19.996",
    "sbj_P_40": "9.057",
    "sbj_P_41": "19.991",
    "sbj_P_42": "19.996",
    "sbj_P_43": "20.008",
    "sbj_P_44": "19.995",
    "sbj_P_45": "20.0",
    "sbj_P_46": "20.001",
    "sbj_P_47": "19.992",
    "sbj_P_48": "19.993",
    "sbj_P_49": "19.999",
    "sbj_P_50": "20.001",
    "sbj_P_52": "19.993",
    "sbj_P_53": "19.996",
    "sbj_P_54": "19.999",
    "sbj_P_55": "19.999",
    "sbj_P_56": "19.993",
    "sbj_P_57": "19.996",
    "sbj_P_58": "19.993",
    "sbj_P_59": "19.997",
    "sbj_P_60": "19.995",
    "sbj_P_61": "19.992",
    "sbj_P_62": "20.012",
    "sbj_P_63": "19.994",
    "sbj_P_64": "19.988",
    "sbj_P_65": "19.989"
  },
  {
    "Stimulus": "BSL",
    "Description": "120s-long neutral baseline",
    "sbj_P_01": "119.994",
    "sbj_P_02": "119.988",
    "sbj_P_03": "120.001",
    "sbj_P_04": "120.003",
    "sbj_P_05": "119.99",
    "sbj_P_06": "119.997",
    "sbj_P_07": "119.996",
    "sbj_P_08": "119.997",
    "sbj_P_09": "120.005",
    "sbj_P_10": "119.995",
    "sbj_P_11": "119.99",
    "sbj_P_12": "120.005",
    "sbj_P_13": "120.009",
    "sbj_P_14": "119.991",
    "sbj_P_15": "119.993",
    "sbj_P_16": "119.993",
    "sbj_P_17": "119.989",
    "sbj_P_18": "119.989",
    "sbj_P_19": "119.998",
    "sbj_P_20": "119.999",
    "sbj_P_21": "119.985",
    "sbj_P_22": "119.996",
    "sbj_P_23": "120.004",
    "sbj_P_24": "119.994",
    "sbj_P_25": "119.992",
    "sbj_P_26": "119.993",
    "sbj_P_27": "119.994",
    "sbj_P_28": "120.0",
    "sbj_P_29": "119.989",
    "sbj_P_30": "120.0",
    "sbj_P_31": "119.996",
    "sbj_P_32": "119.997",
    "sbj_P_33": "120.0",
    "sbj_P_34": "119.996",
    "sbj_P_35": "120.0",
    "sbj_P_36": "119.999",
    "sbj_P_37": "120.004",
    "sbj_P_38": "119.988",
    "sbj_P_39": "119.997",
    "sbj_P_40": "119.989",
    "sbj_P_41": "119.997",
    "sbj_P_42": "119.991",
    "sbj_P_43": "120.003",
    "sbj_P_44": "120.001",
    "sbj_P_45": "119.999",
    "sbj_P_46": "120.002",
    "sbj_P_47": "120.005",
    "sbj_P_48": "120.01",
    "sbj_P_49": "119.989",
    "sbj_P_50": "119.991",
    "sbj_P_52": "119.999",
    "sbj_P_53": "119.998",
    "sbj_P_54": "119.99",
    "sbj_P_55": "120.001",
    "sbj_P_56": "119.995",
    "sbj_P_57": "120.001",
    "sbj_P_58": "120.003",
    "sbj_P_59": "119.997",
    "sbj_P_60": "119.996",
    "sbj_P_61": "119.992",
    "sbj_P_62": "119.991",
    "sbj_P_63": "120.0",
    "sbj_P_64": "120.01",
    "sbj_P_65": "119.994"
  }
]

```

## Sample `.mat` Structure

Deep-inspected EEG files: `3`

Deep-inspected EMG files: `3`

### EEG

- File: `sbj_P_01.mat`
  - Subject ID: `1`
  - Size: `92.92 MB`
  - Loader: `h5py`
  - Keys: `['#refs#', '#refs#/a', '#refs#/b', '#refs#/c', '#refs#/d', '#refs#/e', '#refs#/f', '#refs#/g', '#refs#/h', '#refs#/i', '#refs#/j', '#refs#/k', '#subsystem#', '#subsystem#/MCOS', 'sbj_P_01', 'sbj_P_01/Fs', 'sbj_P_01/channels', 'sbj_P_01/channels_type', 'sbj_P_01/channels_unit', 'sbj_P_01/data', 'sbj_P_01/event_begin', 'sbj_P_01/event_end', 'sbj_P_01/event_id', 'sbj_P_01/subject', 'sbj_P_01/time']`
  - HDF5 content preview:
    - `#refs#`: {'type': 'Group'}
    - `#refs#/a`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#refs#/b`: {'type': 'Dataset', 'shape': [1, 376], 'dtype': 'uint8'}
    - `#refs#/c`: {'type': 'Dataset', 'shape': [7, 1], 'dtype': 'uint64'}
    - `#refs#/d`: {'type': 'Dataset', 'shape': [66, 1], 'dtype': 'uint64'}
    - `#refs#/e`: {'type': 'Dataset', 'shape': [71, 1], 'dtype': 'uint64'}
    - `#refs#/f`: {'type': 'Dataset', 'shape': [61, 1], 'dtype': 'uint64'}
    - `#refs#/g`: {'type': 'Dataset', 'shape': [367, 1], 'dtype': 'uint64'}
    - `#refs#/h`: {'type': 'Dataset', 'shape': [1, 2], 'dtype': 'int32'}
    - `#refs#/i`: {'type': 'Dataset', 'shape': [1, 2], 'dtype': 'object'}
    - `#refs#/j`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#refs#/k`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#subsystem#`: {'type': 'Group'}
    - `#subsystem#/MCOS`: {'type': 'Dataset', 'shape': [1, 9], 'dtype': 'object'}
    - `sbj_P_01`: {'type': 'Group'}
    - `sbj_P_01/Fs`: {'type': 'Dataset', 'shape': [1, 1], 'dtype': 'float64'}
    - `sbj_P_01/channels`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_01/channels_type`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_01/channels_unit`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_01/data`: {'type': 'Dataset', 'shape': [565159, 38], 'dtype': 'float64'}
    - `sbj_P_01/event_begin`: {'type': 'Dataset', 'shape': [100, 1], 'dtype': 'float64'}
    - `sbj_P_01/event_end`: {'type': 'Dataset', 'shape': [100, 1], 'dtype': 'float64'}
    - `sbj_P_01/event_id`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_01/subject`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_01/time`: {'type': 'Dataset', 'shape': [565159, 1], 'dtype': 'float64'}

- File: `sbj_P_02.mat`
  - Subject ID: `2`
  - Size: `88.90 MB`
  - Loader: `h5py`
  - Keys: `['#refs#', '#refs#/a', '#refs#/b', '#refs#/c', '#refs#/d', '#refs#/e', '#refs#/f', '#refs#/g', '#refs#/h', '#refs#/i', '#refs#/j', '#refs#/k', '#subsystem#', '#subsystem#/MCOS', 'sbj_P_02', 'sbj_P_02/Fs', 'sbj_P_02/channels', 'sbj_P_02/channels_type', 'sbj_P_02/channels_unit', 'sbj_P_02/data', 'sbj_P_02/event_begin', 'sbj_P_02/event_end', 'sbj_P_02/event_id', 'sbj_P_02/subject', 'sbj_P_02/time']`
  - HDF5 content preview:
    - `#refs#`: {'type': 'Group'}
    - `#refs#/a`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#refs#/b`: {'type': 'Dataset', 'shape': [1, 376], 'dtype': 'uint8'}
    - `#refs#/c`: {'type': 'Dataset', 'shape': [7, 1], 'dtype': 'uint64'}
    - `#refs#/d`: {'type': 'Dataset', 'shape': [66, 1], 'dtype': 'uint64'}
    - `#refs#/e`: {'type': 'Dataset', 'shape': [71, 1], 'dtype': 'uint64'}
    - `#refs#/f`: {'type': 'Dataset', 'shape': [61, 1], 'dtype': 'uint64'}
    - `#refs#/g`: {'type': 'Dataset', 'shape': [367, 1], 'dtype': 'uint64'}
    - `#refs#/h`: {'type': 'Dataset', 'shape': [1, 2], 'dtype': 'int32'}
    - `#refs#/i`: {'type': 'Dataset', 'shape': [1, 2], 'dtype': 'object'}
    - `#refs#/j`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#refs#/k`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#subsystem#`: {'type': 'Group'}
    - `#subsystem#/MCOS`: {'type': 'Dataset', 'shape': [1, 9], 'dtype': 'object'}
    - `sbj_P_02`: {'type': 'Group'}
    - `sbj_P_02/Fs`: {'type': 'Dataset', 'shape': [1, 1], 'dtype': 'float64'}
    - `sbj_P_02/channels`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_02/channels_type`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_02/channels_unit`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_02/data`: {'type': 'Dataset', 'shape': [540472, 38], 'dtype': 'float64'}
    - `sbj_P_02/event_begin`: {'type': 'Dataset', 'shape': [100, 1], 'dtype': 'float64'}
    - `sbj_P_02/event_end`: {'type': 'Dataset', 'shape': [100, 1], 'dtype': 'float64'}
    - `sbj_P_02/event_id`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_02/subject`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_02/time`: {'type': 'Dataset', 'shape': [540472, 1], 'dtype': 'float64'}

- File: `sbj_P_03.mat`
  - Subject ID: `3`
  - Size: `73.74 MB`
  - Loader: `h5py`
  - Keys: `['#refs#', '#refs#/a', '#refs#/b', '#refs#/c', '#refs#/d', '#refs#/e', '#refs#/f', '#refs#/g', '#refs#/h', '#refs#/i', '#refs#/j', '#refs#/k', '#subsystem#', '#subsystem#/MCOS', 'sbj_P_03', 'sbj_P_03/Fs', 'sbj_P_03/channels', 'sbj_P_03/channels_type', 'sbj_P_03/channels_unit', 'sbj_P_03/data', 'sbj_P_03/event_begin', 'sbj_P_03/event_end', 'sbj_P_03/event_id', 'sbj_P_03/subject', 'sbj_P_03/time']`
  - HDF5 content preview:
    - `#refs#`: {'type': 'Group'}
    - `#refs#/a`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#refs#/b`: {'type': 'Dataset', 'shape': [1, 376], 'dtype': 'uint8'}
    - `#refs#/c`: {'type': 'Dataset', 'shape': [7, 1], 'dtype': 'uint64'}
    - `#refs#/d`: {'type': 'Dataset', 'shape': [66, 1], 'dtype': 'uint64'}
    - `#refs#/e`: {'type': 'Dataset', 'shape': [71, 1], 'dtype': 'uint64'}
    - `#refs#/f`: {'type': 'Dataset', 'shape': [61, 1], 'dtype': 'uint64'}
    - `#refs#/g`: {'type': 'Dataset', 'shape': [367, 1], 'dtype': 'uint64'}
    - `#refs#/h`: {'type': 'Dataset', 'shape': [1, 2], 'dtype': 'int32'}
    - `#refs#/i`: {'type': 'Dataset', 'shape': [1, 2], 'dtype': 'object'}
    - `#refs#/j`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#refs#/k`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#subsystem#`: {'type': 'Group'}
    - `#subsystem#/MCOS`: {'type': 'Dataset', 'shape': [1, 9], 'dtype': 'object'}
    - `sbj_P_03`: {'type': 'Group'}
    - `sbj_P_03/Fs`: {'type': 'Dataset', 'shape': [1, 1], 'dtype': 'float64'}
    - `sbj_P_03/channels`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_03/channels_type`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_03/channels_unit`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_03/data`: {'type': 'Dataset', 'shape': [501013, 38], 'dtype': 'float64'}
    - `sbj_P_03/event_begin`: {'type': 'Dataset', 'shape': [100, 1], 'dtype': 'float64'}
    - `sbj_P_03/event_end`: {'type': 'Dataset', 'shape': [100, 1], 'dtype': 'float64'}
    - `sbj_P_03/event_id`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_03/subject`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_03/time`: {'type': 'Dataset', 'shape': [501013, 1], 'dtype': 'float64'}

### EMG

- File: `sbj_P_01.mat`
  - Subject ID: `1`
  - Size: `37.04 MB`
  - Loader: `h5py`
  - Keys: `['#refs#', '#refs#/a', '#refs#/b', '#refs#/c', '#refs#/d', '#refs#/e', '#refs#/f', '#refs#/g', '#refs#/h', '#refs#/i', '#refs#/j', '#refs#/k', '#subsystem#', '#subsystem#/MCOS', 'sbj_P_01', 'sbj_P_01/Fs', 'sbj_P_01/channels', 'sbj_P_01/channels_type', 'sbj_P_01/channels_unit', 'sbj_P_01/data', 'sbj_P_01/event_begin', 'sbj_P_01/event_end', 'sbj_P_01/event_id', 'sbj_P_01/subject', 'sbj_P_01/time']`
  - HDF5 content preview:
    - `#refs#`: {'type': 'Group'}
    - `#refs#/a`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#refs#/b`: {'type': 'Dataset', 'shape': [1, 376], 'dtype': 'uint8'}
    - `#refs#/c`: {'type': 'Dataset', 'shape': [7, 1], 'dtype': 'uint64'}
    - `#refs#/d`: {'type': 'Dataset', 'shape': [8, 1], 'dtype': 'uint64'}
    - `#refs#/e`: {'type': 'Dataset', 'shape': [8, 1], 'dtype': 'uint64'}
    - `#refs#/f`: {'type': 'Dataset', 'shape': [7, 1], 'dtype': 'uint64'}
    - `#refs#/g`: {'type': 'Dataset', 'shape': [367, 1], 'dtype': 'uint64'}
    - `#refs#/h`: {'type': 'Dataset', 'shape': [1, 2], 'dtype': 'int32'}
    - `#refs#/i`: {'type': 'Dataset', 'shape': [1, 2], 'dtype': 'object'}
    - `#refs#/j`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#refs#/k`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#subsystem#`: {'type': 'Group'}
    - `#subsystem#/MCOS`: {'type': 'Dataset', 'shape': [1, 9], 'dtype': 'object'}
    - `sbj_P_01`: {'type': 'Group'}
    - `sbj_P_01/Fs`: {'type': 'Dataset', 'shape': [1, 1], 'dtype': 'float64'}
    - `sbj_P_01/channels`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_01/channels_type`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_01/channels_unit`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_01/data`: {'type': 'Dataset', 'shape': [2207651, 2], 'dtype': 'float64'}
    - `sbj_P_01/event_begin`: {'type': 'Dataset', 'shape': [100, 1], 'dtype': 'float64'}
    - `sbj_P_01/event_end`: {'type': 'Dataset', 'shape': [100, 1], 'dtype': 'float64'}
    - `sbj_P_01/event_id`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_01/subject`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_01/time`: {'type': 'Dataset', 'shape': [2207651, 1], 'dtype': 'float64'}

- File: `sbj_P_02.mat`
  - Subject ID: `2`
  - Size: `35.39 MB`
  - Loader: `h5py`
  - Keys: `['#refs#', '#refs#/a', '#refs#/b', '#refs#/c', '#refs#/d', '#refs#/e', '#refs#/f', '#refs#/g', '#refs#/h', '#refs#/i', '#refs#/j', '#refs#/k', '#subsystem#', '#subsystem#/MCOS', 'sbj_P_02', 'sbj_P_02/Fs', 'sbj_P_02/channels', 'sbj_P_02/channels_type', 'sbj_P_02/channels_unit', 'sbj_P_02/data', 'sbj_P_02/event_begin', 'sbj_P_02/event_end', 'sbj_P_02/event_id', 'sbj_P_02/subject', 'sbj_P_02/time']`
  - HDF5 content preview:
    - `#refs#`: {'type': 'Group'}
    - `#refs#/a`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#refs#/b`: {'type': 'Dataset', 'shape': [1, 376], 'dtype': 'uint8'}
    - `#refs#/c`: {'type': 'Dataset', 'shape': [7, 1], 'dtype': 'uint64'}
    - `#refs#/d`: {'type': 'Dataset', 'shape': [8, 1], 'dtype': 'uint64'}
    - `#refs#/e`: {'type': 'Dataset', 'shape': [8, 1], 'dtype': 'uint64'}
    - `#refs#/f`: {'type': 'Dataset', 'shape': [7, 1], 'dtype': 'uint64'}
    - `#refs#/g`: {'type': 'Dataset', 'shape': [367, 1], 'dtype': 'uint64'}
    - `#refs#/h`: {'type': 'Dataset', 'shape': [1, 2], 'dtype': 'int32'}
    - `#refs#/i`: {'type': 'Dataset', 'shape': [1, 2], 'dtype': 'object'}
    - `#refs#/j`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#refs#/k`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#subsystem#`: {'type': 'Group'}
    - `#subsystem#/MCOS`: {'type': 'Dataset', 'shape': [1, 9], 'dtype': 'object'}
    - `sbj_P_02`: {'type': 'Group'}
    - `sbj_P_02/Fs`: {'type': 'Dataset', 'shape': [1, 1], 'dtype': 'float64'}
    - `sbj_P_02/channels`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_02/channels_type`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_02/channels_unit`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_02/data`: {'type': 'Dataset', 'shape': [2111215, 2], 'dtype': 'float64'}
    - `sbj_P_02/event_begin`: {'type': 'Dataset', 'shape': [100, 1], 'dtype': 'float64'}
    - `sbj_P_02/event_end`: {'type': 'Dataset', 'shape': [100, 1], 'dtype': 'float64'}
    - `sbj_P_02/event_id`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_02/subject`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_02/time`: {'type': 'Dataset', 'shape': [2111215, 1], 'dtype': 'float64'}

- File: `sbj_P_03.mat`
  - Subject ID: `3`
  - Size: `32.76 MB`
  - Loader: `h5py`
  - Keys: `['#refs#', '#refs#/a', '#refs#/b', '#refs#/c', '#refs#/d', '#refs#/e', '#refs#/f', '#refs#/g', '#refs#/h', '#refs#/i', '#refs#/j', '#refs#/k', '#subsystem#', '#subsystem#/MCOS', 'sbj_P_03', 'sbj_P_03/Fs', 'sbj_P_03/channels', 'sbj_P_03/channels_type', 'sbj_P_03/channels_unit', 'sbj_P_03/data', 'sbj_P_03/event_begin', 'sbj_P_03/event_end', 'sbj_P_03/event_id', 'sbj_P_03/subject', 'sbj_P_03/time']`
  - HDF5 content preview:
    - `#refs#`: {'type': 'Group'}
    - `#refs#/a`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#refs#/b`: {'type': 'Dataset', 'shape': [1, 376], 'dtype': 'uint8'}
    - `#refs#/c`: {'type': 'Dataset', 'shape': [7, 1], 'dtype': 'uint64'}
    - `#refs#/d`: {'type': 'Dataset', 'shape': [8, 1], 'dtype': 'uint64'}
    - `#refs#/e`: {'type': 'Dataset', 'shape': [8, 1], 'dtype': 'uint64'}
    - `#refs#/f`: {'type': 'Dataset', 'shape': [7, 1], 'dtype': 'uint64'}
    - `#refs#/g`: {'type': 'Dataset', 'shape': [367, 1], 'dtype': 'uint64'}
    - `#refs#/h`: {'type': 'Dataset', 'shape': [1, 2], 'dtype': 'int32'}
    - `#refs#/i`: {'type': 'Dataset', 'shape': [1, 2], 'dtype': 'object'}
    - `#refs#/j`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#refs#/k`: {'type': 'Dataset', 'shape': [2], 'dtype': 'uint64'}
    - `#subsystem#`: {'type': 'Group'}
    - `#subsystem#/MCOS`: {'type': 'Dataset', 'shape': [1, 9], 'dtype': 'object'}
    - `sbj_P_03`: {'type': 'Group'}
    - `sbj_P_03/Fs`: {'type': 'Dataset', 'shape': [1, 1], 'dtype': 'float64'}
    - `sbj_P_03/channels`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_03/channels_type`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_03/channels_unit`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_03/data`: {'type': 'Dataset', 'shape': [1957081, 2], 'dtype': 'float64'}
    - `sbj_P_03/event_begin`: {'type': 'Dataset', 'shape': [100, 1], 'dtype': 'float64'}
    - `sbj_P_03/event_end`: {'type': 'Dataset', 'shape': [100, 1], 'dtype': 'float64'}
    - `sbj_P_03/event_id`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_03/subject`: {'type': 'Dataset', 'shape': [1, 6], 'dtype': 'uint32'}
    - `sbj_P_03/time`: {'type': 'Dataset', 'shape': [1957081, 1], 'dtype': 'float64'}

## Issues

- None.

## Warnings

- None.

## Audit Interpretation

- The downloaded I-DARE first-stage files are present according to the manifest.

- EEG and EMG subject coverage matches the expected main protocol decision.

- Subject 4 remains EMG-only and should be excluded from main EEG+EMG experiments.

- The next step is to inspect the `.mat` fields in this report and decide the exact loader design.



# FILE: docs/idare_hdf5_structure_probe.md


# I-DARE HDF5 Structure Probe

This report was generated by `scripts/02_probe_idare_hdf5_structure.py`.

No training or preprocessing was performed.

## Label Stimulus Summary

### `Arousal_SAM.csv`

- Exists: `True`

- Shape: `[32, 1]`

- Stimulus count: `None`

- First 10 stimulus values: `[]`

### `Valence_SAM.csv`

- Exists: `True`

- Shape: `[32, 1]`

- Stimulus count: `None`

- First 10 stimulus values: `[]`

### `Quadrants_SAM.csv`

- Exists: `True`

- Shape: `[32, 1]`

- Stimulus count: `None`

- First 10 stimulus values: `[]`

## EEG Sample Files

### `sbj_P_01.mat`

- Subject: `{'shape': [1, 6], 'dtype': 'uint32', 'values': [3707764736, 2, 1, 1, 1, 1], 'decoded': [3707764736, 2, 1, 1, 1, 1]}`

- Exists: `True`

- Group keys: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

- `Fs`: shape=[1, 1], dtype=float64

  - decoded preview: `512.0`

- `data`: shape=[565159, 38], dtype=float64

- `time`: shape=[565159, 1], dtype=float64

- `event_begin`: shape=[100, 1], dtype=float64

  - decoded preview: `[102228.0, 132965.0, 143230.0, 204692.0, 209831.0, 212425.0, 214994.0, 223897.0, 226483.0, 229073.0, 236411.0, 239003.0, 241576.0, 251362.0, 253964.0, 256541.0, 261968.0, 264561.0, 267131.0, 273642.0]`

- `event_end`: shape=[100, 1], dtype=float64

  - decoded preview: `[132945.0, 143201.0, 204666.0, 209809.0, 212386.0, 214977.0, 223869.0, 226451.0, 229044.0, 236395.0, 238971.0, 241563.0, 251335.0, 253924.0, 256521.0, 261927.0, 264521.0, 267118.0, 273593.0, 276194.0]`

- `event_id`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 5, 1]`

- `channels`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 2, 1]`

- `channels_type`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 3, 1]`

- `channels_unit`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 4, 1]`

- `subject`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 1, 1]`

- Data orientation guess:

```json

{
  "data_shape": [
    565159,
    38
  ],
  "time_shape": [
    565159,
    1
  ],
  "n_decoded_channels": 6,
  "guess": "unknown"
}

```

- Derived event summary:

```json

{
  "fs": 512.0,
  "num_events": 6,
  "event_id_preview": [
    "3707764736",
    "2",
    "1",
    "1",
    "5",
    "1"
  ],
  "event_begin_preview": [
    102228.0,
    132965.0,
    143230.0,
    204692.0,
    209831.0,
    212425.0,
    214994.0,
    223897.0,
    226483.0,
    229073.0
  ],
  "event_end_preview": [
    132945.0,
    143201.0,
    204666.0,
    209809.0,
    212386.0,
    214977.0,
    223869.0,
    226451.0,
    229044.0,
    236395.0
  ],
  "duration_samples_preview": [
    30717.0,
    10236.0,
    61436.0,
    5117.0,
    2555.0,
    2552.0,
    8875.0,
    2554.0,
    2561.0,
    7322.0
  ],
  "duration_sec_preview": [
    59.994140625,
    19.9921875,
    119.9921875,
    9.994140625,
    4.990234375,
    4.984375,
    17.333984375,
    4.98828125,
    5.001953125,
    14.30078125
  ],
  "duration_sec_unique_rounded": [
    4.984375,
    4.986328,
    4.988281,
    4.990234,
    4.992188,
    4.994141,
    4.996094,
    4.998047,
    5.0,
    5.001953,
    5.003906,
    5.013672,
    5.394531,
    6.304688,
    6.410156,
    6.662109,
    6.708984,
    7.380859,
    7.416016,
    7.5,
    7.976562,
    8.03125,
    8.09375,
    8.421875,
    8.466797,
    8.490234,
    8.595703,
    8.759766,
    8.980469,
    9.046875,
    9.107422,
    9.251953,
    9.724609,
    9.814453,
    9.994141,
    10.519531,
    10.542969,
    10.599609,
    11.318359,
    11.583984,
    12.621094,
    14.300781,
    17.333984,
    19.060547,
    19.992188,
    59.994141,
    74.21875,
    119.992188
  ],
  "min_duration_sec": 4.984375,
  "max_duration_sec": 119.9921875
}

```

### `sbj_P_02.mat`

- Subject: `{'shape': [1, 6], 'dtype': 'uint32', 'values': [3707764736, 2, 1, 1, 1, 1], 'decoded': [3707764736, 2, 1, 1, 1, 1]}`

- Exists: `True`

- Group keys: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

- `Fs`: shape=[1, 1], dtype=float64

  - decoded preview: `512.0`

- `data`: shape=[540472, 38], dtype=float64

- `time`: shape=[540472, 1], dtype=float64

- `event_begin`: shape=[100, 1], dtype=float64

  - decoded preview: `[81581.0, 112322.0, 120021.0, 181485.0, 186638.0, 189235.0, 191823.0, 201146.0, 203757.0, 206348.0, 215138.0, 217743.0, 220336.0, 224853.0, 227464.0, 230055.0, 233693.0, 236337.0, 238927.0, 242991.0]`

- `event_end`: shape=[100, 1], dtype=float64

  - decoded preview: `[112294.0, 119980.0, 181454.0, 186598.0, 189191.0, 191792.0, 201100.0, 203701.0, 206310.0, 215095.0, 217696.0, 220302.0, 224808.0, 227407.0, 230024.0, 233647.0, 236247.0, 238895.0, 242921.0, 245543.0]`

- `event_id`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 5, 1]`

- `channels`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 2, 1]`

- `channels_type`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 3, 1]`

- `channels_unit`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 4, 1]`

- `subject`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 1, 1]`

- Data orientation guess:

```json

{
  "data_shape": [
    540472,
    38
  ],
  "time_shape": [
    540472,
    1
  ],
  "n_decoded_channels": 6,
  "guess": "unknown"
}

```

- Derived event summary:

```json

{
  "fs": 512.0,
  "num_events": 6,
  "event_id_preview": [
    "3707764736",
    "2",
    "1",
    "1",
    "5",
    "1"
  ],
  "event_begin_preview": [
    81581.0,
    112322.0,
    120021.0,
    181485.0,
    186638.0,
    189235.0,
    191823.0,
    201146.0,
    203757.0,
    206348.0
  ],
  "event_end_preview": [
    112294.0,
    119980.0,
    181454.0,
    186598.0,
    189191.0,
    191792.0,
    201100.0,
    203701.0,
    206310.0,
    215095.0
  ],
  "duration_samples_preview": [
    30713.0,
    7658.0,
    61433.0,
    5113.0,
    2553.0,
    2557.0,
    9277.0,
    2555.0,
    2553.0,
    8747.0
  ],
  "duration_sec_preview": [
    59.986328125,
    14.95703125,
    119.986328125,
    9.986328125,
    4.986328125,
    4.994140625,
    18.119140625,
    4.990234375,
    4.986328125,
    17.083984375
  ],
  "duration_sec_unique_rounded": [
    3.994141,
    4.154297,
    4.587891,
    4.599609,
    4.728516,
    4.779297,
    4.984375,
    4.986328,
    4.988281,
    4.990234,
    4.992188,
    4.994141,
    4.996094,
    4.998047,
    5.0,
    5.001953,
    5.085938,
    5.1875,
    5.3125,
    6.185547,
    6.730469,
    7.015625,
    7.800781,
    7.886719,
    8.609375,
    8.734375,
    8.884766,
    9.412109,
    9.986328,
    10.529297,
    12.675781,
    14.669922,
    14.921875,
    14.957031,
    15.302734,
    16.021484,
    16.908203,
    17.083984,
    18.119141,
    19.490234,
    19.943359,
    20.117188,
    24.898438,
    28.335938,
    59.986328,
    119.986328
  ],
  "min_duration_sec": 3.994140625,
  "max_duration_sec": 119.986328125
}

```

### `sbj_P_03.mat`

- Subject: `{'shape': [1, 6], 'dtype': 'uint32', 'values': [3707764736, 2, 1, 1, 1, 1], 'decoded': [3707764736, 2, 1, 1, 1, 1]}`

- Exists: `True`

- Group keys: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

- `Fs`: shape=[1, 1], dtype=float64

  - decoded preview: `512.0`

- `data`: shape=[501013, 38], dtype=float64

- `time`: shape=[501013, 1], dtype=float64

- `event_begin`: shape=[100, 1], dtype=float64

  - decoded preview: `[101655.0, 132425.0, 142720.0, 204206.0, 209372.0, 212000.0, 214606.0, 222288.0, 224907.0, 227511.0, 231051.0, 233661.0, 236285.0, 242299.0, 244928.0, 247534.0, 251876.0, 254512.0, 257118.0, 261837.0]`

- `event_end`: shape=[100, 1], dtype=float64

  - decoded preview: `[132373.0, 142663.0, 204160.0, 209319.0, 211929.0, 214559.0, 222237.0, 224845.0, 227465.0, 230990.0, 233605.0, 236216.0, 242226.0, 244854.0, 247486.0, 251812.0, 254431.0, 257071.0, 261770.0, 264389.0]`

- `event_id`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 5, 1]`

- `channels`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 2, 1]`

- `channels_type`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 3, 1]`

- `channels_unit`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 4, 1]`

- `subject`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 1, 1]`

- Data orientation guess:

```json

{
  "data_shape": [
    501013,
    38
  ],
  "time_shape": [
    501013,
    1
  ],
  "n_decoded_channels": 6,
  "guess": "unknown"
}

```

- Derived event summary:

```json

{
  "fs": 512.0,
  "num_events": 6,
  "event_id_preview": [
    "3707764736",
    "2",
    "1",
    "1",
    "5",
    "1"
  ],
  "event_begin_preview": [
    101655.0,
    132425.0,
    142720.0,
    204206.0,
    209372.0,
    212000.0,
    214606.0,
    222288.0,
    224907.0,
    227511.0
  ],
  "event_end_preview": [
    132373.0,
    142663.0,
    204160.0,
    209319.0,
    211929.0,
    214559.0,
    222237.0,
    224845.0,
    227465.0,
    230990.0
  ],
  "duration_samples_preview": [
    30718.0,
    10238.0,
    61440.0,
    5113.0,
    2557.0,
    2559.0,
    7631.0,
    2557.0,
    2558.0,
    3479.0
  ],
  "duration_sec_preview": [
    59.99609375,
    19.99609375,
    120.0,
    9.986328125,
    4.994140625,
    4.998046875,
    14.904296875,
    4.994140625,
    4.99609375,
    6.794921875
  ],
  "duration_sec_unique_rounded": [
    3.373047,
    3.945312,
    4.443359,
    4.447266,
    4.982422,
    4.984375,
    4.986328,
    4.988281,
    4.990234,
    4.992188,
    4.994141,
    4.996094,
    4.998047,
    5.0,
    5.001953,
    5.003906,
    5.027344,
    5.564453,
    5.611328,
    6.470703,
    6.550781,
    6.597656,
    6.621094,
    6.726562,
    6.794922,
    6.927734,
    7.003906,
    7.066406,
    7.095703,
    7.134766,
    7.164062,
    7.324219,
    7.357422,
    7.494141,
    7.904297,
    8.355469,
    9.085938,
    9.478516,
    9.488281,
    9.597656,
    9.767578,
    9.986328,
    11.591797,
    11.603516,
    14.904297,
    19.996094,
    59.996094,
    120.0
  ],
  "min_duration_sec": 3.373046875,
  "max_duration_sec": 120.0
}

```

## EMG Sample Files

### `sbj_P_01.mat`

- Subject: `{'shape': [1, 6], 'dtype': 'uint32', 'values': [3707764736, 2, 1, 1, 1, 1], 'decoded': [3707764736, 2, 1, 1, 1, 1]}`

- Exists: `True`

- Group keys: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

- `Fs`: shape=[1, 1], dtype=float64

  - decoded preview: `2000.0`

- `data`: shape=[2207651, 2], dtype=float64

- `time`: shape=[2207651, 1], dtype=float64

- `event_begin`: shape=[100, 1], dtype=float64

  - decoded preview: `[399327.0, 519391.0, 559491.0, 799575.0, 819649.0, 829783.0, 839817.0, 874593.0, 884697.0, 894815.0, 923477.0, 933601.0, 943653.0, 981881.0, 992045.0, 1002111.0, 1023311.0, 1033439.0, 1043479.0, 1068911.0]`

- `event_end`: shape=[100, 1], dtype=float64

  - decoded preview: `[519321.0, 559381.0, 799479.0, 819567.0, 829635.0, 839757.0, 874489.0, 884575.0, 894705.0, 923419.0, 933479.0, 943605.0, 981777.0, 991893.0, 1002039.0, 1023155.0, 1033289.0, 1043431.0, 1068727.0, 1078883.0]`

- `event_id`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 5, 1]`

- `channels`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 2, 1]`

- `channels_type`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 3, 1]`

- `channels_unit`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 4, 1]`

- `subject`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 1, 1]`

- Data orientation guess:

```json

{
  "data_shape": [
    2207651,
    2
  ],
  "time_shape": [
    2207651,
    1
  ],
  "n_decoded_channels": 6,
  "guess": "unknown"
}

```

- Derived event summary:

```json

{
  "fs": 2000.0,
  "num_events": 6,
  "event_id_preview": [
    "3707764736",
    "2",
    "1",
    "1",
    "5",
    "1"
  ],
  "event_begin_preview": [
    399327.0,
    519391.0,
    559491.0,
    799575.0,
    819649.0,
    829783.0,
    839817.0,
    874593.0,
    884697.0,
    894815.0
  ],
  "event_end_preview": [
    519321.0,
    559381.0,
    799479.0,
    819567.0,
    829635.0,
    839757.0,
    874489.0,
    884575.0,
    894705.0,
    923419.0
  ],
  "duration_samples_preview": [
    119994.0,
    39990.0,
    239988.0,
    19992.0,
    9986.0,
    9974.0,
    34672.0,
    9982.0,
    10008.0,
    28604.0
  ],
  "duration_sec_preview": [
    59.997,
    19.995,
    119.994,
    9.996,
    4.993,
    4.987,
    17.336,
    4.991,
    5.004,
    14.302
  ],
  "duration_sec_unique_rounded": [
    4.986,
    4.987,
    4.988,
    4.989,
    4.99,
    4.991,
    4.992,
    4.993,
    4.994,
    4.995,
    4.996,
    4.997,
    4.998,
    4.999,
    5.0,
    5.001,
    5.002,
    5.004,
    5.006,
    5.016,
    5.397,
    6.307,
    6.412,
    6.664,
    6.71,
    7.383,
    7.417,
    7.501,
    7.978,
    8.034,
    8.095,
    8.423,
    8.468,
    8.493,
    8.598,
    8.762,
    8.982,
    9.048,
    9.109,
    9.254,
    9.727,
    9.817,
    9.996,
    10.522,
    10.545,
    10.601,
    11.321,
    11.586,
    12.624,
    14.302,
    17.336,
    19.062,
    19.995,
    59.997,
    74.22,
    119.994
  ],
  "min_duration_sec": 4.986,
  "max_duration_sec": 119.994
}

```

### `sbj_P_02.mat`

- Subject: `{'shape': [1, 6], 'dtype': 'uint32', 'values': [3707764736, 2, 1, 1, 1, 1], 'decoded': [3707764736, 2, 1, 1, 1, 1]}`

- Exists: `True`

- Group keys: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

- `Fs`: shape=[1, 1], dtype=float64

  - decoded preview: `2000.0`

- `data`: shape=[2111215, 2], dtype=float64

- `time`: shape=[2111215, 1], dtype=float64

- `event_begin`: shape=[100, 1], dtype=float64

  - decoded preview: `[318673.0, 438755.0, 468831.0, 708923.0, 729051.0, 739195.0, 749307.0, 785725.0, 795923.0, 806043.0, 840379.0, 850557.0, 860683.0, 878331.0, 888529.0, 898651.0, 912859.0, 923189.0, 933307.0, 949179.0]`

- `event_end`: shape=[100, 1], dtype=float64

  - decoded preview: `[438651.0, 468673.0, 708807.0, 728899.0, 739027.0, 749189.0, 785549.0, 795711.0, 805901.0, 840213.0, 850377.0, 860557.0, 878155.0, 888313.0, 898533.0, 912687.0, 922841.0, 933187.0, 948913.0, 959153.0]`

- `event_id`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 5, 1]`

- `channels`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 2, 1]`

- `channels_type`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 3, 1]`

- `channels_unit`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 4, 1]`

- `subject`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 1, 1]`

- Data orientation guess:

```json

{
  "data_shape": [
    2111215,
    2
  ],
  "time_shape": [
    2111215,
    1
  ],
  "n_decoded_channels": 6,
  "guess": "unknown"
}

```

- Derived event summary:

```json

{
  "fs": 2000.0,
  "num_events": 6,
  "event_id_preview": [
    "3707764736",
    "2",
    "1",
    "1",
    "5",
    "1"
  ],
  "event_begin_preview": [
    318673.0,
    438755.0,
    468831.0,
    708923.0,
    729051.0,
    739195.0,
    749307.0,
    785725.0,
    795923.0,
    806043.0
  ],
  "event_end_preview": [
    438651.0,
    468673.0,
    708807.0,
    728899.0,
    739027.0,
    749189.0,
    785549.0,
    795711.0,
    805901.0,
    840213.0
  ],
  "duration_samples_preview": [
    119978.0,
    29918.0,
    239976.0,
    19976.0,
    9976.0,
    9994.0,
    36242.0,
    9986.0,
    9978.0,
    34170.0
  ],
  "duration_sec_preview": [
    59.989,
    14.959,
    119.988,
    9.988,
    4.988,
    4.997,
    18.121,
    4.993,
    4.989,
    17.085
  ],
  "duration_sec_unique_rounded": [
    3.997,
    4.157,
    4.589,
    4.602,
    4.73,
    4.782,
    4.987,
    4.988,
    4.989,
    4.99,
    4.991,
    4.992,
    4.993,
    4.994,
    4.995,
    4.996,
    4.997,
    4.998,
    4.999,
    5.0,
    5.001,
    5.002,
    5.004,
    5.087,
    5.19,
    5.315,
    6.188,
    6.733,
    7.018,
    7.803,
    7.888,
    8.611,
    8.736,
    8.887,
    9.414,
    9.988,
    10.531,
    12.677,
    14.672,
    14.923,
    14.959,
    15.305,
    16.024,
    16.91,
    17.085,
    18.121,
    19.492,
    19.945,
    20.119,
    24.9,
    28.338,
    59.989,
    119.988
  ],
  "min_duration_sec": 3.997,
  "max_duration_sec": 119.988
}

```

### `sbj_P_03.mat`

- Subject: `{'shape': [1, 6], 'dtype': 'uint32', 'values': [3707764736, 2, 1, 1, 1, 1], 'decoded': [3707764736, 2, 1, 1, 1, 1]}`

- Exists: `True`

- Group keys: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

- `Fs`: shape=[1, 1], dtype=float64

  - decoded preview: `2000.0`

- `data`: shape=[1957081, 2], dtype=float64

- `time`: shape=[1957081, 1], dtype=float64

- `event_begin`: shape=[100, 1], dtype=float64

  - decoded preview: `[397087.0, 517281.0, 557497.0, 797677.0, 817857.0, 828123.0, 838301.0, 868311.0, 878541.0, 888711.0, 902541.0, 912735.0, 922987.0, 946477.0, 956749.0, 966925.0, 983887.0, 994185.0, 1004365.0, 1022799.0]`

- `event_end`: shape=[100, 1], dtype=float64

  - decoded preview: `[517085.0, 557277.0, 797499.0, 817653.0, 827851.0, 838123.0, 868113.0, 878303.0, 888537.0, 902305.0, 912523.0, 922719.0, 946197.0, 956461.0, 966747.0, 983641.0, 993873.0, 1004185.0, 1022541.0, 1032773.0]`

- `event_id`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 5, 1]`

- `channels`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 2, 1]`

- `channels_type`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 3, 1]`

- `channels_unit`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 4, 1]`

- `subject`: shape=[1, 6], dtype=uint32

  - decoded preview: `[3707764736, 2, 1, 1, 1, 1]`

- Data orientation guess:

```json

{
  "data_shape": [
    1957081,
    2
  ],
  "time_shape": [
    1957081,
    1
  ],
  "n_decoded_channels": 6,
  "guess": "unknown"
}

```

- Derived event summary:

```json

{
  "fs": 2000.0,
  "num_events": 6,
  "event_id_preview": [
    "3707764736",
    "2",
    "1",
    "1",
    "5",
    "1"
  ],
  "event_begin_preview": [
    397087.0,
    517281.0,
    557497.0,
    797677.0,
    817857.0,
    828123.0,
    838301.0,
    868311.0,
    878541.0,
    888711.0
  ],
  "event_end_preview": [
    517085.0,
    557277.0,
    797499.0,
    817653.0,
    827851.0,
    838123.0,
    868113.0,
    878303.0,
    888537.0,
    902305.0
  ],
  "duration_samples_preview": [
    119998.0,
    39996.0,
    240002.0,
    19976.0,
    9994.0,
    10000.0,
    29812.0,
    9992.0,
    9996.0,
    13594.0
  ],
  "duration_sec_preview": [
    59.999,
    19.998,
    120.001,
    9.988,
    4.997,
    5.0,
    14.906,
    4.996,
    4.998,
    6.797
  ],
  "duration_sec_unique_rounded": [
    3.375,
    3.948,
    4.446,
    4.45,
    4.985,
    4.986,
    4.987,
    4.988,
    4.989,
    4.99,
    4.991,
    4.992,
    4.993,
    4.994,
    4.995,
    4.996,
    4.997,
    4.998,
    4.999,
    5.0,
    5.001,
    5.002,
    5.004,
    5.005,
    5.029,
    5.567,
    5.613,
    6.473,
    6.553,
    6.599,
    6.623,
    6.729,
    6.797,
    6.929,
    7.006,
    7.068,
    7.098,
    7.137,
    7.166,
    7.327,
    7.359,
    7.497,
    7.907,
    8.358,
    9.088,
    9.48,
    9.49,
    9.599,
    9.77,
    9.988,
    11.594,
    11.605,
    14.906,
    19.998,
    59.999,
    120.001
  ],
  "min_duration_sec": 3.375,
  "max_duration_sec": 120.001
}

```



# FILE: docs/idare_mat73_probe.md


# I-DARE mat73 Loader Probe

This report was generated by `scripts/03_probe_idare_mat73_loader.py`.

No training or preprocessing was performed.

## CSV Label Summary

### `Arousal_SAM.csv`

- Exists: `True`

- Shape: `[32, 65]`

- Columns preview: `['Stimulus', 'sbj_P_01', 'sbj_P_02', 'sbj_P_03', 'sbj_P_04', 'sbj_P_05', 'sbj_P_06', 'sbj_P_07', 'sbj_P_08', 'sbj_P_09', 'sbj_P_10', 'sbj_P_11']`

- Stimulus count: `32`

- First 10 stimulus values: `['1441', '1750', '2314', '2491', '3053', '3063', '3080', '3170', '4220', '5760']`

### `Valence_SAM.csv`

- Exists: `True`

- Shape: `[32, 65]`

- Columns preview: `['Stimulus', 'sbj_P_01', 'sbj_P_02', 'sbj_P_03', 'sbj_P_04', 'sbj_P_05', 'sbj_P_06', 'sbj_P_07', 'sbj_P_08', 'sbj_P_09', 'sbj_P_10', 'sbj_P_11']`

- Stimulus count: `32`

- First 10 stimulus values: `['1441', '1750', '2314', '2491', '3053', '3063', '3080', '3170', '4220', '5760']`

### `Quadrants_SAM.csv`

- Exists: `True`

- Shape: `[32, 66]`

- Columns preview: `['Stimulus', 'Quadrant (GS)', 'sbj_P_01', 'sbj_P_02', 'sbj_P_03', 'sbj_P_04', 'sbj_P_05', 'sbj_P_06', 'sbj_P_07', 'sbj_P_08', 'sbj_P_09', 'sbj_P_10']`

- Stimulus count: `32`

- First 10 stimulus values: `['1441', '1750', '2314', '2491', '3053', '3063', '3080', '3170', '4220', '5760']`

### `Sample.csv`

- Exists: `True`

- Shape: `[63, 3]`

- Columns preview: `['Subject', 'Gender', 'Age']`

## EEG Sample Files

### `sbj_P_01.mat`

- Exists: `True`

- Top-level keys: `['sbj_P_01']`

- Field names: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

### Field summaries

- `Fs`: present=True, type=ndarray, shape=[], dtype=float64

  - preview: `[512.0]`

- `data`: present=True, type=ndarray, shape=[38, 565159], dtype=float64

  - preview: `[-12.527053833007812, -15.028985977172852, -17.420482635498047, -19.55874252319336, -21.465940475463867, -23.274446487426758, -25.04665756225586, -26.729000091552734, -28.126327514648438, -29.112709045410156, -29.641557693481445, -29.747081756591797, -29.44567108154297, -28.8461856842041, -28.167417526245117, -27.708518981933594, -27.651073455810547, -28.063655853271484, -28.926898956298828, -30.141313552856445]`

- `time`: present=True, type=ndarray, shape=[565159], dtype=float64

  - preview: `[1.953125e-06, 0.001955078125, 0.003908203125, 0.005861328125, 0.007814453125, 0.009767578125, 0.011720703125, 0.013673828125, 0.015626953125, 0.017580078125, 0.019533203125, 0.021486328125, 0.023439453125, 0.025392578125, 0.027345703125, 0.029298828125, 0.031251953125, 0.033205078125, 0.035158203125, 0.037111328125]`

- `channels`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `channels_type`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `channels_unit`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `event_begin`: present=True, type=ndarray, shape=[100], dtype=float64

  - preview: `[102228.0, 132965.0, 143230.0, 204692.0, 209831.0, 212425.0, 214994.0, 223897.0, 226483.0, 229073.0, 236411.0, 239003.0, 241576.0, 251362.0, 253964.0, 256541.0, 261968.0, 264561.0, 267131.0, 273642.0]`

- `event_end`: present=True, type=ndarray, shape=[100], dtype=float64

  - preview: `[132945.0, 143201.0, 204666.0, 209809.0, 212386.0, 214977.0, 223869.0, 226451.0, 229044.0, 236395.0, 238971.0, 241563.0, 251335.0, 253924.0, 256521.0, 261927.0, 264521.0, 267118.0, 273593.0, 276194.0]`

- `event_id`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `subject`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

### Derived summary

```json

{
  "fs": 512.0,
  "data_shape": [
    38,
    565159
  ],
  "time_shape": [
    565159
  ],
  "event_begin_shape": [
    100
  ],
  "event_end_shape": [
    100
  ],
  "event_id_shape": [],
  "num_event_begin": 100,
  "num_event_end": 100,
  "num_event_id": 1,
  "event_id_preview": [
    "None"
  ],
  "duration_sec_preview": [
    59.994141,
    19.992188,
    119.992188,
    9.994141,
    4.990234,
    4.984375,
    17.333984,
    4.988281,
    5.001953,
    14.300781,
    5.0,
    5.0,
    19.060547,
    5.003906,
    4.994141,
    10.519531,
    4.986328,
    4.994141,
    12.621094,
    4.984375
  ],
  "duration_sec_unique_rounded": [
    4.984375,
    4.986328,
    4.988281,
    4.990234,
    4.992188,
    4.994141,
    4.996094,
    4.998047,
    5.0,
    5.001953,
    5.003906,
    5.013672,
    5.394531,
    6.304688,
    6.410156,
    6.662109,
    6.708984,
    7.380859,
    7.416016,
    7.5,
    7.976562,
    8.03125,
    8.09375,
    8.421875,
    8.466797,
    8.490234,
    8.595703,
    8.759766,
    8.980469,
    9.046875,
    9.107422,
    9.251953,
    9.724609,
    9.814453,
    9.994141,
    10.519531,
    10.542969,
    10.599609,
    11.318359,
    11.583984,
    12.621094,
    14.300781,
    17.333984,
    19.060547,
    19.992188,
    59.994141,
    74.21875,
    119.992188
  ],
  "num_around_5s_events_4p5_to_5p5": 65,
  "min_duration_sec": 4.984375,
  "max_duration_sec": 119.9921875,
  "data_orientation_guess": "channels x time",
  "n_channels_from_data": null
}

```

### `sbj_P_02.mat`

- Exists: `True`

- Top-level keys: `['sbj_P_02']`

- Field names: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

### Field summaries

- `Fs`: present=True, type=ndarray, shape=[], dtype=float64

  - preview: `[512.0]`

- `data`: present=True, type=ndarray, shape=[38, 540472], dtype=float64

  - preview: `[-4.999059677124023, -5.850787162780762, -6.570327281951904, -7.013596057891846, -7.083208084106445, -6.812187194824219, -6.273292064666748, -5.585827350616455, -4.882972717285156, -4.255456447601318, -3.8219194412231445, -3.6530561447143555, -3.806394577026367, -4.273313522338867, -4.968592643737793, -5.774641990661621, -6.540451526641846, -7.168474197387695, -7.629125595092773, -8.012873649597168]`

- `time`: present=True, type=ndarray, shape=[540472], dtype=float64

  - preview: `[1.953125e-06, 0.001955078125, 0.003908203125, 0.005861328125, 0.007814453125, 0.009767578125, 0.011720703125, 0.013673828125, 0.015626953125, 0.017580078125, 0.019533203125, 0.021486328125, 0.023439453125, 0.025392578125, 0.027345703125, 0.029298828125, 0.031251953125, 0.033205078125, 0.035158203125, 0.037111328125]`

- `channels`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `channels_type`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `channels_unit`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `event_begin`: present=True, type=ndarray, shape=[100], dtype=float64

  - preview: `[81581.0, 112322.0, 120021.0, 181485.0, 186638.0, 189235.0, 191823.0, 201146.0, 203757.0, 206348.0, 215138.0, 217743.0, 220336.0, 224853.0, 227464.0, 230055.0, 233693.0, 236337.0, 238927.0, 242991.0]`

- `event_end`: present=True, type=ndarray, shape=[100], dtype=float64

  - preview: `[112294.0, 119980.0, 181454.0, 186598.0, 189191.0, 191792.0, 201100.0, 203701.0, 206310.0, 215095.0, 217696.0, 220302.0, 224808.0, 227407.0, 230024.0, 233647.0, 236247.0, 238895.0, 242921.0, 245543.0]`

- `event_id`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `subject`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

### Derived summary

```json

{
  "fs": 512.0,
  "data_shape": [
    38,
    540472
  ],
  "time_shape": [
    540472
  ],
  "event_begin_shape": [
    100
  ],
  "event_end_shape": [
    100
  ],
  "event_id_shape": [],
  "num_event_begin": 100,
  "num_event_end": 100,
  "num_event_id": 1,
  "event_id_preview": [
    "None"
  ],
  "duration_sec_preview": [
    59.986328,
    14.957031,
    119.986328,
    9.986328,
    4.986328,
    4.994141,
    18.119141,
    4.990234,
    4.986328,
    17.083984,
    4.996094,
    4.998047,
    8.734375,
    4.988281,
    5.0,
    7.015625,
    4.988281,
    4.996094,
    7.800781,
    4.984375
  ],
  "duration_sec_unique_rounded": [
    3.994141,
    4.154297,
    4.587891,
    4.599609,
    4.728516,
    4.779297,
    4.984375,
    4.986328,
    4.988281,
    4.990234,
    4.992188,
    4.994141,
    4.996094,
    4.998047,
    5.0,
    5.001953,
    5.085938,
    5.1875,
    5.3125,
    6.185547,
    6.730469,
    7.015625,
    7.800781,
    7.886719,
    8.609375,
    8.734375,
    8.884766,
    9.412109,
    9.986328,
    10.529297,
    12.675781,
    14.669922,
    14.921875,
    14.957031,
    15.302734,
    16.021484,
    16.908203,
    17.083984,
    18.119141,
    19.490234,
    19.943359,
    20.117188,
    24.898438,
    28.335938,
    59.986328,
    119.986328
  ],
  "num_around_5s_events_4p5_to_5p5": 71,
  "min_duration_sec": 3.994140625,
  "max_duration_sec": 119.986328125,
  "data_orientation_guess": "channels x time",
  "n_channels_from_data": null
}

```

### `sbj_P_03.mat`

- Exists: `True`

- Top-level keys: `['sbj_P_03']`

- Field names: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

### Field summaries

- `Fs`: present=True, type=ndarray, shape=[], dtype=float64

  - preview: `[512.0]`

- `data`: present=True, type=ndarray, shape=[38, 501013], dtype=float64

  - preview: `[-4.540689468383789, -1.8396668434143066, 0.05031871795654297, 0.7081766128540039, -0.05244302749633789, -1.852433204650879, -3.991023063659668, -5.480795860290527, -5.793539047241211, -4.889490127563477, -2.856779098510742, -0.15314483642578125, 2.66793155670166, 4.870136260986328, 5.976276874542236, 5.878448963165283, 4.63348388671875, 2.411409854888916, -0.4327049255371094, -3.4172754287719727]`

- `time`: present=True, type=ndarray, shape=[501013], dtype=float64

  - preview: `[1.953125e-06, 0.001955078125, 0.003908203125, 0.005861328125, 0.007814453125, 0.009767578125, 0.011720703125, 0.013673828125, 0.015626953125, 0.017580078125, 0.019533203125, 0.021486328125, 0.023439453125, 0.025392578125, 0.027345703125, 0.029298828125, 0.031251953125, 0.033205078125, 0.035158203125, 0.037111328125]`

- `channels`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `channels_type`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `channels_unit`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `event_begin`: present=True, type=ndarray, shape=[100], dtype=float64

  - preview: `[101655.0, 132425.0, 142720.0, 204206.0, 209372.0, 212000.0, 214606.0, 222288.0, 224907.0, 227511.0, 231051.0, 233661.0, 236285.0, 242299.0, 244928.0, 247534.0, 251876.0, 254512.0, 257118.0, 261837.0]`

- `event_end`: present=True, type=ndarray, shape=[100], dtype=float64

  - preview: `[132373.0, 142663.0, 204160.0, 209319.0, 211929.0, 214559.0, 222237.0, 224845.0, 227465.0, 230990.0, 233605.0, 236216.0, 242226.0, 244854.0, 247486.0, 251812.0, 254431.0, 257071.0, 261770.0, 264389.0]`

- `event_id`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `subject`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

### Derived summary

```json

{
  "fs": 512.0,
  "data_shape": [
    38,
    501013
  ],
  "time_shape": [
    501013
  ],
  "event_begin_shape": [
    100
  ],
  "event_end_shape": [
    100
  ],
  "event_id_shape": [],
  "num_event_begin": 100,
  "num_event_end": 100,
  "num_event_id": 1,
  "event_id_preview": [
    "None"
  ],
  "duration_sec_preview": [
    59.996094,
    19.996094,
    120.0,
    9.986328,
    4.994141,
    4.998047,
    14.904297,
    4.994141,
    4.996094,
    6.794922,
    4.988281,
    4.990234,
    11.603516,
    4.990234,
    4.996094,
    8.355469,
    4.990234,
    4.998047,
    9.085938,
    4.984375
  ],
  "duration_sec_unique_rounded": [
    3.373047,
    3.945312,
    4.443359,
    4.447266,
    4.982422,
    4.984375,
    4.986328,
    4.988281,
    4.990234,
    4.992188,
    4.994141,
    4.996094,
    4.998047,
    5.0,
    5.001953,
    5.003906,
    5.027344,
    5.564453,
    5.611328,
    6.470703,
    6.550781,
    6.597656,
    6.621094,
    6.726562,
    6.794922,
    6.927734,
    7.003906,
    7.066406,
    7.095703,
    7.134766,
    7.164062,
    7.324219,
    7.357422,
    7.494141,
    7.904297,
    8.355469,
    9.085938,
    9.478516,
    9.488281,
    9.597656,
    9.767578,
    9.986328,
    11.591797,
    11.603516,
    14.904297,
    19.996094,
    59.996094,
    120.0
  ],
  "num_around_5s_events_4p5_to_5p5": 65,
  "min_duration_sec": 3.373046875,
  "max_duration_sec": 120.0,
  "data_orientation_guess": "channels x time",
  "n_channels_from_data": null
}

```

## EMG Sample Files

### `sbj_P_01.mat`

- Exists: `True`

- Top-level keys: `['sbj_P_01']`

- Field names: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

### Field summaries

- `Fs`: present=True, type=ndarray, shape=[], dtype=float64

  - preview: `[2000.0]`

- `data`: present=True, type=ndarray, shape=[2, 2207651], dtype=float64

  - preview: `[-4.349200904047668, 0.3615707479026422, 2.9005301213739414, 2.447689359422288, 0.09329228676698009, -1.975751243666318, -2.1931511058968822, -0.7300767336828953, 0.9835942131865443, 1.7004903221919299, 1.2948465689627202, 0.48440880750780174, -0.07773407500525292, -0.3169975994853398, -0.5633596249577445, -1.1674142791621953, -2.2161966771926767, -3.278271168192877, -3.453455965207174, -2.159983050034433]`

- `time`: present=True, type=ndarray, shape=[2207651], dtype=float64

  - preview: `[0.0, 0.0005000000000023874, 0.0010000000000012221, 0.0015000000000000568, 0.0020000000000024443, 0.002500000000001279, 0.0030000000000001137, 0.003500000000002501, 0.004000000000001336, 0.0045000000000001705, 0.005000000000002558, 0.005500000000001393, 0.006000000000000227, 0.006500000000002615, 0.0070000000000014495, 0.007500000000000284, 0.008000000000002672, 0.008500000000001506, 0.009000000000000341, 0.009500000000002728]`

- `channels`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `channels_type`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `channels_unit`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `event_begin`: present=True, type=ndarray, shape=[100], dtype=float64

  - preview: `[399327.0, 519391.0, 559491.0, 799575.0, 819649.0, 829783.0, 839817.0, 874593.0, 884697.0, 894815.0, 923477.0, 933601.0, 943653.0, 981881.0, 992045.0, 1002111.0, 1023311.0, 1033439.0, 1043479.0, 1068911.0]`

- `event_end`: present=True, type=ndarray, shape=[100], dtype=float64

  - preview: `[519321.0, 559381.0, 799479.0, 819567.0, 829635.0, 839757.0, 874489.0, 884575.0, 894705.0, 923419.0, 933479.0, 943605.0, 981777.0, 991893.0, 1002039.0, 1023155.0, 1033289.0, 1043431.0, 1068727.0, 1078883.0]`

- `event_id`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `subject`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

### Derived summary

```json

{
  "fs": 2000.0,
  "data_shape": [
    2,
    2207651
  ],
  "time_shape": [
    2207651
  ],
  "event_begin_shape": [
    100
  ],
  "event_end_shape": [
    100
  ],
  "event_id_shape": [],
  "num_event_begin": 100,
  "num_event_end": 100,
  "num_event_id": 1,
  "event_id_preview": [
    "None"
  ],
  "duration_sec_preview": [
    59.997,
    19.995,
    119.994,
    9.996,
    4.993,
    4.987,
    17.336,
    4.991,
    5.004,
    14.302,
    5.001,
    5.002,
    19.062,
    5.006,
    4.997,
    10.522,
    4.989,
    4.996,
    12.624,
    4.986
  ],
  "duration_sec_unique_rounded": [
    4.986,
    4.987,
    4.988,
    4.989,
    4.99,
    4.991,
    4.992,
    4.993,
    4.994,
    4.995,
    4.996,
    4.997,
    4.998,
    4.999,
    5.0,
    5.001,
    5.002,
    5.004,
    5.006,
    5.016,
    5.397,
    6.307,
    6.412,
    6.664,
    6.71,
    7.383,
    7.417,
    7.501,
    7.978,
    8.034,
    8.095,
    8.423,
    8.468,
    8.493,
    8.598,
    8.762,
    8.982,
    9.048,
    9.109,
    9.254,
    9.727,
    9.817,
    9.996,
    10.522,
    10.545,
    10.601,
    11.321,
    11.586,
    12.624,
    14.302,
    17.336,
    19.062,
    19.995,
    59.997,
    74.22,
    119.994
  ],
  "num_around_5s_events_4p5_to_5p5": 65,
  "min_duration_sec": 4.986,
  "max_duration_sec": 119.994,
  "data_orientation_guess": "channels x time",
  "n_channels_from_data": null
}

```

### `sbj_P_02.mat`

- Exists: `True`

- Top-level keys: `['sbj_P_02']`

- Field names: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

### Field summaries

- `Fs`: present=True, type=ndarray, shape=[], dtype=float64

  - preview: `[2000.0]`

- `data`: present=True, type=ndarray, shape=[2, 2111215], dtype=float64

  - preview: `[-0.15845215858831085, -9.470981310194984, -14.718281544775795, -14.558700998557194, -10.490869416166351, -4.884396345500187, 0.536723463233371, 4.665294733566835, 6.624945311750676, 6.077117234861623, 3.6116848292031203, 0.2942325185232495, -3.2834533500668517, -7.296899645418183, -11.89964251006615, -16.21113228975524, -18.325220449035356, -16.657931213764616, -11.531780549599745, -5.333117595356799]`

- `time`: present=True, type=ndarray, shape=[2111215], dtype=float64

  - preview: `[0.0, 0.0005000000000023874, 0.000999999999990564, 0.0014999999999929514, 0.001999999999995339, 0.0024999999999977263, 0.0030000000000001137, 0.003500000000002501, 0.003999999999990678, 0.004499999999993065, 0.0049999999999954525, 0.00549999999999784, 0.006000000000000227, 0.006500000000002615, 0.006999999999990791, 0.007499999999993179, 0.007999999999995566, 0.008499999999997954, 0.009000000000000341, 0.009499999999988518]`

- `channels`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `channels_type`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `channels_unit`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `event_begin`: present=True, type=ndarray, shape=[100], dtype=float64

  - preview: `[318673.0, 438755.0, 468831.0, 708923.0, 729051.0, 739195.0, 749307.0, 785725.0, 795923.0, 806043.0, 840379.0, 850557.0, 860683.0, 878331.0, 888529.0, 898651.0, 912859.0, 923189.0, 933307.0, 949179.0]`

- `event_end`: present=True, type=ndarray, shape=[100], dtype=float64

  - preview: `[438651.0, 468673.0, 708807.0, 728899.0, 739027.0, 749189.0, 785549.0, 795711.0, 805901.0, 840213.0, 850377.0, 860557.0, 878155.0, 888313.0, 898533.0, 912687.0, 922841.0, 933187.0, 948913.0, 959153.0]`

- `event_id`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `subject`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

### Derived summary

```json

{
  "fs": 2000.0,
  "data_shape": [
    2,
    2111215
  ],
  "time_shape": [
    2111215
  ],
  "event_begin_shape": [
    100
  ],
  "event_end_shape": [
    100
  ],
  "event_id_shape": [],
  "num_event_begin": 100,
  "num_event_end": 100,
  "num_event_id": 1,
  "event_id_preview": [
    "None"
  ],
  "duration_sec_preview": [
    59.989,
    14.959,
    119.988,
    9.988,
    4.988,
    4.997,
    18.121,
    4.993,
    4.989,
    17.085,
    4.999,
    5.0,
    8.736,
    4.991,
    5.002,
    7.018,
    4.991,
    4.999,
    7.803,
    4.987
  ],
  "duration_sec_unique_rounded": [
    3.997,
    4.157,
    4.589,
    4.602,
    4.73,
    4.782,
    4.987,
    4.988,
    4.989,
    4.99,
    4.991,
    4.992,
    4.993,
    4.994,
    4.995,
    4.996,
    4.997,
    4.998,
    4.999,
    5.0,
    5.001,
    5.002,
    5.004,
    5.087,
    5.19,
    5.315,
    6.188,
    6.733,
    7.018,
    7.803,
    7.888,
    8.611,
    8.736,
    8.887,
    9.414,
    9.988,
    10.531,
    12.677,
    14.672,
    14.923,
    14.959,
    15.305,
    16.024,
    16.91,
    17.085,
    18.121,
    19.492,
    19.945,
    20.119,
    24.9,
    28.338,
    59.989,
    119.988
  ],
  "num_around_5s_events_4p5_to_5p5": 71,
  "min_duration_sec": 3.997,
  "max_duration_sec": 119.988,
  "data_orientation_guess": "channels x time",
  "n_channels_from_data": null
}

```

### `sbj_P_03.mat`

- Exists: `True`

- Top-level keys: `['sbj_P_03']`

- Field names: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

### Field summaries

- `Fs`: present=True, type=ndarray, shape=[], dtype=float64

  - preview: `[2000.0]`

- `data`: present=True, type=ndarray, shape=[2, 1957081], dtype=float64

  - preview: `[1.2334977315650155, -1.1264692675461407, -1.2571325667026443, -0.025963386197955962, -0.2323861276191088, -2.782509564585221, -5.415614932412712, -5.591492545464672, -3.451052588727357, -0.9956058002174535, 0.8630965627207637, 3.072437718430791, 6.3675480475726935, 9.786316600806174, 11.822724271246745, 12.08754627644893, 10.92697076118856, 8.106418714946349, 3.256582694142954, -2.341223736783592]`

- `time`: present=True, type=ndarray, shape=[1957081], dtype=float64

  - preview: `[0.0, 0.000499999999995282, 0.0009999999999976694, 0.0015000000000000568, 0.001999999999995339, 0.0024999999999977263, 0.0030000000000001137, 0.0034999999999953957, 0.003999999999997783, 0.0045000000000001705, 0.0049999999999954525, 0.00549999999999784, 0.006000000000000227, 0.006499999999995509, 0.006999999999997897, 0.007500000000000284, 0.007999999999995566, 0.008499999999997954, 0.009000000000000341, 0.009499999999995623]`

- `channels`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `channels_type`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `channels_unit`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `event_begin`: present=True, type=ndarray, shape=[100], dtype=float64

  - preview: `[397087.0, 517281.0, 557497.0, 797677.0, 817857.0, 828123.0, 838301.0, 868311.0, 878541.0, 888711.0, 902541.0, 912735.0, 922987.0, 946477.0, 956749.0, 966925.0, 983887.0, 994185.0, 1004365.0, 1022799.0]`

- `event_end`: present=True, type=ndarray, shape=[100], dtype=float64

  - preview: `[517085.0, 557277.0, 797499.0, 817653.0, 827851.0, 838123.0, 868113.0, 878303.0, 888537.0, 902305.0, 912523.0, 922719.0, 946197.0, 956461.0, 966747.0, 983641.0, 993873.0, 1004185.0, 1022541.0, 1032773.0]`

- `event_id`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

- `subject`: present=True, type=NoneType, shape=[], dtype=object

  - preview: `['None']`

### Derived summary

```json

{
  "fs": 2000.0,
  "data_shape": [
    2,
    1957081
  ],
  "time_shape": [
    1957081
  ],
  "event_begin_shape": [
    100
  ],
  "event_end_shape": [
    100
  ],
  "event_id_shape": [],
  "num_event_begin": 100,
  "num_event_end": 100,
  "num_event_id": 1,
  "event_id_preview": [
    "None"
  ],
  "duration_sec_preview": [
    59.999,
    19.998,
    120.001,
    9.988,
    4.997,
    5.0,
    14.906,
    4.996,
    4.998,
    6.797,
    4.991,
    4.992,
    11.605,
    4.992,
    4.999,
    8.358,
    4.993,
    5.0,
    9.088,
    4.987
  ],
  "duration_sec_unique_rounded": [
    3.375,
    3.948,
    4.446,
    4.45,
    4.985,
    4.986,
    4.987,
    4.988,
    4.989,
    4.99,
    4.991,
    4.992,
    4.993,
    4.994,
    4.995,
    4.996,
    4.997,
    4.998,
    4.999,
    5.0,
    5.001,
    5.002,
    5.004,
    5.005,
    5.029,
    5.567,
    5.613,
    6.473,
    6.553,
    6.599,
    6.623,
    6.729,
    6.797,
    6.929,
    7.006,
    7.068,
    7.098,
    7.137,
    7.166,
    7.327,
    7.359,
    7.497,
    7.907,
    8.358,
    9.088,
    9.48,
    9.49,
    9.599,
    9.77,
    9.988,
    11.594,
    11.605,
    14.906,
    19.998,
    59.999,
    120.001
  ],
  "num_around_5s_events_4p5_to_5p5": 65,
  "min_duration_sec": 3.375,
  "max_duration_sec": 120.001,
  "data_orientation_guess": "channels x time",
  "n_channels_from_data": null
}

```



# FILE: docs/idare_refs_and_events_probe.md


# I-DARE MATLAB References and Event Probe

This report was generated by `scripts/04_probe_idare_refs_and_events.py`.

No training or preprocessing was performed.

## CSV / Stimulus Cross-check

```json

{
  "arousal_count": 32,
  "valence_count": 32,
  "specs_count": 100,
  "arousal_equals_valence": true,
  "labels_subset_of_specs": false,
  "label_stimuli_not_in_specs": [
    "1441",
    "1750",
    "2314",
    "2491",
    "3053",
    "3063",
    "3080",
    "3170",
    "4220",
    "5760",
    "8080",
    "8370",
    "8492",
    "9220",
    "9331",
    "9360",
    "Angry_face_1",
    "Beach_1",
    "Depressed_pose_4",
    "Dog_18",
    "Dog_26",
    "Dog_6",
    "Dummy_1",
    "Flowers_6",
    "Garbage_dump_6",
    "Lake_12",
    "Lake_3",
    "Miserable_pose_3",
    "Pinecone_1",
    "Snow_1",
    "Tumor_1",
    "Yarn_1"
  ],
  "specs_stimuli_not_in_labels_count": 100,
  "label_stimuli_sorted": [
    "1441",
    "1750",
    "2314",
    "2491",
    "3053",
    "3063",
    "3080",
    "3170",
    "4220",
    "5760",
    "8080",
    "8370",
    "8492",
    "9220",
    "9331",
    "9360",
    "Angry_face_1",
    "Beach_1",
    "Depressed_pose_4",
    "Dog_18",
    "Dog_26",
    "Dog_6",
    "Dummy_1",
    "Flowers_6",
    "Garbage_dump_6",
    "Lake_12",
    "Lake_3",
    "Miserable_pose_3",
    "Pinecone_1",
    "Snow_1",
    "Tumor_1",
    "Yarn_1"
  ]
}

```

### `Stimuli_Specifications.csv`

- Exists: `True`

- Shape: `[100, 66]`

- Columns preview: `['Stimulus', 'Description', 'sbj_P_01', 'sbj_P_02', 'sbj_P_03', 'sbj_P_04', 'sbj_P_05', 'sbj_P_06', 'sbj_P_07', 'sbj_P_08', 'sbj_P_09', 'sbj_P_10', 'sbj_P_11', 'sbj_P_12', 'sbj_P_13']`

- Stimulus count: `100`

- First 10 stimulus values: `['EYC', 'IST_BSL', 'BSL', 'IST_START', 'BSL_Dummy_1', 'STIM_Dummy_1', 'SAM_Dummy_1', 'BSL_3053', 'STIM_3053', 'SAM_3053']`

- `sbj_P_01` non-empty count: `100`

- `sbj_P_01` non-empty preview:

```json

[
  {
    "Stimulus": "EYC",
    "Description": "60s-long eye-closed baseline",
    "sbj_P_01": "59.997"
  },
  {
    "Stimulus": "IST_BSL",
    "Description": "Instructions for the 120s-long neutral baseline",
    "sbj_P_01": "19.995"
  },
  {
    "Stimulus": "BSL",
    "Description": "120s-long neutral baseline",
    "sbj_P_01": "119.994"
  },
  {
    "Stimulus": "IST_START",
    "Description": "Experiment description",
    "sbj_P_01": "9.996"
  },
  {
    "Stimulus": "BSL_Dummy_1",
    "Description": "Black-screen baseline",
    "sbj_P_01": "4.993"
  },
  {
    "Stimulus": "STIM_Dummy_1",
    "Description": "Emotional stimulus",
    "sbj_P_01": "4.987"
  },
  {
    "Stimulus": "SAM_Dummy_1",
    "Description": "SAM evaluation",
    "sbj_P_01": "17.336"
  },
  {
    "Stimulus": "BSL_3053",
    "Description": "Black-screen baseline",
    "sbj_P_01": "4.991"
  },
  {
    "Stimulus": "STIM_3053",
    "Description": "Emotional stimulus",
    "sbj_P_01": "5.004"
  },
  {
    "Stimulus": "SAM_3053",
    "Description": "SAM evaluation",
    "sbj_P_01": "14.302"
  }
]

```

- `sbj_P_02` non-empty count: `100`

- `sbj_P_02` non-empty preview:

```json

[
  {
    "Stimulus": "EYC",
    "Description": "60s-long eye-closed baseline",
    "sbj_P_02": "59.989"
  },
  {
    "Stimulus": "IST_BSL",
    "Description": "Instructions for the 120s-long neutral baseline",
    "sbj_P_02": "14.959"
  },
  {
    "Stimulus": "BSL",
    "Description": "120s-long neutral baseline",
    "sbj_P_02": "119.988"
  },
  {
    "Stimulus": "IST_START",
    "Description": "Experiment description",
    "sbj_P_02": "9.988"
  },
  {
    "Stimulus": "BSL_Dummy_1",
    "Description": "Black-screen baseline",
    "sbj_P_02": "4.996"
  },
  {
    "Stimulus": "STIM_Dummy_1",
    "Description": "Emotional stimulus",
    "sbj_P_02": "4.996"
  },
  {
    "Stimulus": "SAM_Dummy_1",
    "Description": "SAM evaluation",
    "sbj_P_02": "4.602"
  },
  {
    "Stimulus": "BSL_3053",
    "Description": "Black-screen baseline",
    "sbj_P_02": "4.993"
  },
  {
    "Stimulus": "STIM_3053",
    "Description": "Emotional stimulus",
    "sbj_P_02": "5.0"
  },
  {
    "Stimulus": "SAM_3053",
    "Description": "SAM evaluation",
    "sbj_P_02": "4.157"
  }
]

```

- `sbj_P_03` non-empty count: `100`

- `sbj_P_03` non-empty preview:

```json

[
  {
    "Stimulus": "EYC",
    "Description": "60s-long eye-closed baseline",
    "sbj_P_03": "59.999"
  },
  {
    "Stimulus": "IST_BSL",
    "Description": "Instructions for the 120s-long neutral baseline",
    "sbj_P_03": "19.998"
  },
  {
    "Stimulus": "BSL",
    "Description": "120s-long neutral baseline",
    "sbj_P_03": "120.001"
  },
  {
    "Stimulus": "IST_START",
    "Description": "Experiment description",
    "sbj_P_03": "9.988"
  },
  {
    "Stimulus": "BSL_Dummy_1",
    "Description": "Black-screen baseline",
    "sbj_P_03": "4.986"
  },
  {
    "Stimulus": "STIM_Dummy_1",
    "Description": "Emotional stimulus",
    "sbj_P_03": "5.001"
  },
  {
    "Stimulus": "SAM_Dummy_1",
    "Description": "SAM evaluation",
    "sbj_P_03": "11.594"
  },
  {
    "Stimulus": "BSL_3053",
    "Description": "Black-screen baseline",
    "sbj_P_03": "4.992"
  },
  {
    "Stimulus": "STIM_3053",
    "Description": "Emotional stimulus",
    "sbj_P_03": "4.999"
  },
  {
    "Stimulus": "SAM_3053",
    "Description": "SAM evaluation",
    "sbj_P_03": "5.613"
  }
]

```

### `Arousal_SAM.csv`

- Exists: `True`

- Shape: `[32, 65]`

- Columns preview: `['Stimulus', 'sbj_P_01', 'sbj_P_02', 'sbj_P_03', 'sbj_P_04', 'sbj_P_05', 'sbj_P_06', 'sbj_P_07', 'sbj_P_08', 'sbj_P_09', 'sbj_P_10', 'sbj_P_11', 'sbj_P_12', 'sbj_P_13', 'sbj_P_14']`

- Stimulus count: `32`

- First 10 stimulus values: `['1441', '1750', '2314', '2491', '3053', '3063', '3080', '3170', '4220', '5760']`

### `Valence_SAM.csv`

- Exists: `True`

- Shape: `[32, 65]`

- Columns preview: `['Stimulus', 'sbj_P_01', 'sbj_P_02', 'sbj_P_03', 'sbj_P_04', 'sbj_P_05', 'sbj_P_06', 'sbj_P_07', 'sbj_P_08', 'sbj_P_09', 'sbj_P_10', 'sbj_P_11', 'sbj_P_12', 'sbj_P_13', 'sbj_P_14']`

- Stimulus count: `32`

- First 10 stimulus values: `['1441', '1750', '2314', '2491', '3053', '3063', '3080', '3170', '4220', '5760']`

### `Quadrants_SAM.csv`

- Exists: `True`

- Shape: `[32, 66]`

- Columns preview: `['Stimulus', 'Quadrant (GS)', 'sbj_P_01', 'sbj_P_02', 'sbj_P_03', 'sbj_P_04', 'sbj_P_05', 'sbj_P_06', 'sbj_P_07', 'sbj_P_08', 'sbj_P_09', 'sbj_P_10', 'sbj_P_11', 'sbj_P_12', 'sbj_P_13']`

- Stimulus count: `32`

- First 10 stimulus values: `['1441', '1750', '2314', '2491', '3053', '3063', '3080', '3170', '4220', '5760']`

### `Agreement_Raters.csv`

- Exists: `True`

- Shape: `[32, 18]`

- Columns preview: `['Stimulus', 'Dataset', 'Quadrant', 'Rater 1', 'Rater 2', 'Rater 3', 'Rater 4', 'Rater 5', 'Rater 6', 'Rater 7', 'Rater 8', 'Rater 9', 'Agreement', 'Distance', 'Valence (M)']`

- Stimulus count: `32`

- First 10 stimulus values: `['Flowers 6', '1441', 'Garbage dump 6', 'Snow 1', 'Pinecone 1', 'Dog 6', '3053', '1750', '4220', 'Depressed pose 4']`

## HDF5 File: `EEG_sbj_P_01`

- Path: `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_01.mat`

- Top keys: `['#refs#', '#subsystem#', 'sbj_P_01']`

- Group keys: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

- Refs keys: `['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k']`

### Raw data orientation

```json

{
  "data_shape": [
    565159,
    38
  ],
  "time_shape": [
    565159,
    1
  ],
  "guess": "time x channels"
}

```

### Event timing summary

```json

{
  "fs": 512.0,
  "num_events": 100,
  "num_around_5s_4p5_to_5p5": 65,
  "duration_unique_rounded": [
    4.984375,
    4.986328,
    4.988281,
    4.990234,
    4.992188,
    4.994141,
    4.996094,
    4.998047,
    5.0,
    5.001953,
    5.003906,
    5.013672,
    5.394531,
    6.304688,
    6.410156,
    6.662109,
    6.708984,
    7.380859,
    7.416016,
    7.5,
    7.976562,
    8.03125,
    8.09375,
    8.421875,
    8.466797,
    8.490234,
    8.595703,
    8.759766,
    8.980469,
    9.046875,
    9.107422,
    9.251953,
    9.724609,
    9.814453,
    9.994141,
    10.519531,
    10.542969,
    10.599609,
    11.318359,
    11.583984,
    12.621094,
    14.300781,
    17.333984,
    19.060547,
    19.992188,
    59.994141,
    74.21875,
    119.992188
  ],
  "events_first_40": [
    {
      "event_index_1based": 1,
      "event_begin": 102228.0,
      "event_end": 132945.0,
      "duration_sec": 59.994140625,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 2,
      "event_begin": 132965.0,
      "event_end": 143201.0,
      "duration_sec": 19.9921875,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 3,
      "event_begin": 143230.0,
      "event_end": 204666.0,
      "duration_sec": 119.9921875,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 4,
      "event_begin": 204692.0,
      "event_end": 209809.0,
      "duration_sec": 9.994140625,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 5,
      "event_begin": 209831.0,
      "event_end": 212386.0,
      "duration_sec": 4.990234375,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 6,
      "event_begin": 212425.0,
      "event_end": 214977.0,
      "duration_sec": 4.984375,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 7,
      "event_begin": 214994.0,
      "event_end": 223869.0,
      "duration_sec": 17.333984375,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 8,
      "event_begin": 223897.0,
      "event_end": 226451.0,
      "duration_sec": 4.98828125,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 9,
      "event_begin": 226483.0,
      "event_end": 229044.0,
      "duration_sec": 5.001953125,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 10,
      "event_begin": 229073.0,
      "event_end": 236395.0,
      "duration_sec": 14.30078125,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 11,
      "event_begin": 236411.0,
      "event_end": 238971.0,
      "duration_sec": 5.0,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 12,
      "event_begin": 239003.0,
      "event_end": 241563.0,
      "duration_sec": 5.0,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 13,
      "event_begin": 241576.0,
      "event_end": 251335.0,
      "duration_sec": 19.060546875,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 14,
      "event_begin": 251362.0,
      "event_end": 253924.0,
      "duration_sec": 5.00390625,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 15,
      "event_begin": 253964.0,
      "event_end": 256521.0,
      "duration_sec": 4.994140625,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 16,
      "event_begin": 256541.0,
      "event_end": 261927.0,
      "duration_sec": 10.51953125,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 17,
      "event_begin": 261968.0,
      "event_end": 264521.0,
      "duration_sec": 4.986328125,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 18,
      "event_begin": 264561.0,
      "event_end": 267118.0,
      "duration_sec": 4.994140625,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 19,
      "event_begin": 267131.0,
      "event_end": 273593.0,
      "duration_sec": 12.62109375,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 20,
      "event_begin": 273642.0,
      "event_end": 276194.0,
      "duration_sec": 4.984375,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 21,
      "event_begin": 276235.0,
      "event_end": 278795.0,
      "duration_sec": 5.0,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 22,
      "event_begin": 278813.0,
      "event_end": 284744.0,
      "duration_sec": 11.583984375,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 23,
      "event_begin": 284769.0,
      "event_end": 287321.0,
      "duration_sec": 4.984375,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 24,
      "event_begin": 287363.0,
      "event_end": 289922.0,
      "duration_sec": 4.998046875,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 25,
      "event_begin": 289940.0,
      "event_end": 294252.0,
      "duration_sec": 8.421875,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 26,
      "event_begin": 294299.0,
      "event_end": 296857.0,
      "duration_sec": 4.99609375,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 27,
      "event_begin": 296904.0,
      "event_end": 299459.0,
      "duration_sec": 4.990234375,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 28,
      "event_begin": 299489.0,
      "event_end": 303268.0,
      "duration_sec": 7.380859375,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 29,
      "event_begin": 303295.0,
      "event_end": 305850.0,
      "duration_sec": 4.990234375,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 30,
      "event_begin": 305880.0,
      "event_end": 308434.0,
      "duration_sec": 4.98828125,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 31,
      "event_begin": 308463.0,
      "event_end": 312810.0,
      "duration_sec": 8.490234375,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 32,
      "event_begin": 312835.0,
      "event_end": 315394.0,
      "duration_sec": 4.998046875,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 33,
      "event_begin": 315458.0,
      "event_end": 318018.0,
      "duration_sec": 5.0,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 34,
      "event_begin": 318048.0,
      "event_end": 323446.0,
      "duration_sec": 10.54296875,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 35,
      "event_begin": 323478.0,
      "event_end": 326034.0,
      "duration_sec": 4.9921875,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 36,
      "event_begin": 326070.0,
      "event_end": 328625.0,
      "duration_sec": 4.990234375,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 37,
      "event_begin": 328638.0,
      "event_end": 332782.0,
      "duration_sec": 8.09375,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 38,
      "event_begin": 332819.0,
      "event_end": 335377.0,
      "duration_sec": 4.99609375,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 39,
      "event_begin": 335422.0,
      "event_end": 337978.0,
      "duration_sec": 4.9921875,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 40,
      "event_begin": 337995.0,
      "event_end": 342658.0,
      "duration_sec": 9.107421875,
      "is_around_5s_4p5_to_5p5": false
    }
  ],
  "around_5s_event_indices_1based": [
    5,
    6,
    8,
    9,
    11,
    12,
    14,
    15,
    17,
    18,
    20,
    21,
    23,
    24,
    26,
    27,
    29,
    30,
    32,
    33,
    35,
    36,
    38,
    39,
    41,
    42,
    44,
    45,
    47,
    48,
    50,
    51,
    53,
    54,
    56,
    57,
    59,
    60,
    62,
    63,
    65,
    66,
    68,
    69,
    71,
    72,
    74,
    75,
    77,
    78,
    80,
    81,
    83,
    84,
    85,
    86,
    87,
    89,
    90,
    92,
    93,
    95,
    96,
    98,
    99
  ]
}

```

### Field reference candidates

#### `subject`

```json

{
  "field": "subject",
  "shape": [
    1,
    6
  ],
  "dtype": "uint32",
  "attrs": {
    "H5PATH": "/sbj_P_01",
    "MATLAB_class": "string",
    "MATLAB_object_decode": 3
  },
  "values": [
    3707764736,
    2,
    1,
    1,
    1,
    1
  ],
  "candidate": {
    "raw": [
      3707764736,
      2,
      1,
      1,
      1,
      1
    ],
    "is_candidate": true,
    "ref_index_guess": 1,
    "ref_name_guess": "a"
  },
  "referenced_object_preview": {
    "type": "Dataset",
    "shape": [
      2
    ],
    "dtype": "uint64",
    "attrs": {
      "MATLAB_class": "canonical empty",
      "MATLAB_empty": 1
    },
    "values": [
      0,
      0
    ]
  }
}

```

#### `channels`

```json

{
  "field": "channels",
  "shape": [
    1,
    6
  ],
  "dtype": "uint32",
  "attrs": {
    "H5PATH": "/sbj_P_01",
    "MATLAB_class": "string",
    "MATLAB_object_decode": 3
  },
  "values": [
    3707764736,
    2,
    1,
    1,
    2,
    1
  ],
  "candidate": {
    "raw": [
      3707764736,
      2,
      1,
      1,
      2,
      1
    ],
    "is_candidate": true,
    "ref_index_guess": 2,
    "ref_name_guess": "b"
  },
  "referenced_object_preview": {
    "type": "Dataset",
    "shape": [
      1,
      376
    ],
    "dtype": "uint8",
    "attrs": {
      "H5PATH": "/#refs#/b",
      "MATLAB_class": "uint8"
    },
    "preview": [
      3,
      0,
      0,
      0,
      2,
      0,
      0,
      0,
      56,
      0,
      0,
      0,
      88,
      0,
      0,
      0,
      176,
      0,
      0,
      0,
      64,
      1,
      0,
      0,
      72,
      1,
      0,
      0,
      120,
      1,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      97,
      110,
      121,
      0,
      115,
      116,
      114,
      105,
      110,
      103,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      2,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      1,
      0,
      0,
      0
    ],
    "uint_char_decode": "\u0003\u00028X°@\u0001H\u0001x\u0001anystring\u0002\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0002\u0001\u0001\u0001\u0003\u0001\u0001\u0001\u0004\u0001\u0001\u0001\u0001\u0002\u0002\u0001\u0003\u0003\u0001\u0004\u0004\u0001\u0005\u0005"
  }
}

```

#### `channels_type`

```json

{
  "field": "channels_type",
  "shape": [
    1,
    6
  ],
  "dtype": "uint32",
  "attrs": {
    "H5PATH": "/sbj_P_01",
    "MATLAB_class": "string",
    "MATLAB_object_decode": 3
  },
  "values": [
    3707764736,
    2,
    1,
    1,
    3,
    1
  ],
  "candidate": {
    "raw": [
      3707764736,
      2,
      1,
      1,
      3,
      1
    ],
    "is_candidate": true,
    "ref_index_guess": 3,
    "ref_name_guess": "c"
  },
  "referenced_object_preview": {
    "type": "Dataset",
    "shape": [
      7,
      1
    ],
    "dtype": "uint64",
    "attrs": {
      "H5PATH": "/#refs#/c",
      "MATLAB_class": "uint64"
    },
    "values": [
      1,
      2,
      1,
      1,
      8,
      26740578060468339,
      13792480023478352
    ],
    "uint_char_decode": "\u0001\u0002\u0001\u0001\b"
  }
}

```

#### `channels_unit`

```json

{
  "field": "channels_unit",
  "shape": [
    1,
    6
  ],
  "dtype": "uint32",
  "attrs": {
    "H5PATH": "/sbj_P_01",
    "MATLAB_class": "string",
    "MATLAB_object_decode": 3
  },
  "values": [
    3707764736,
    2,
    1,
    1,
    4,
    1
  ],
  "candidate": {
    "raw": [
      3707764736,
      2,
      1,
      1,
      4,
      1
    ],
    "is_candidate": true,
    "ref_index_guess": 4,
    "ref_name_guess": "d"
  },
  "referenced_object_preview": {
    "type": "Dataset",
    "shape": [
      66,
      1
    ],
    "dtype": "uint64",
    "attrs": {
      "H5PATH": "/#refs#/d",
      "MATLAB_class": "uint64"
    },
    "values": [
      1,
      2,
      38,
      1,
      3,
      3,
      3,
      2,
      2,
      2,
      2,
      2,
      3,
      3,
      3,
      3,
      3,
      2,
      2,
      2,
      2,
      2,
      3,
      3,
      3,
      3,
      3,
      2,
      2,
      2,
      2,
      2,
      2,
      3,
      3,
      3,
      2,
      3,
      2,
      2,
      2,
      3,
      19703458830483526,
      31525498047299696,
      19703484597534770,
      19703772360343603,
      19703488892502068,
      27866323345670260,
      34340372365049907,
      19703471714533446,
      14355584593166452,
      34340234924851267,
      14637059569614915,
      18859059670155348,
      31525485157744752,
      14637179829682298,
      23644138569203796,
      22518217185427509,
      23644121387237498,
      22518225775362102,
      31244066015608943,
      14637175535566970,
      31244066015805520,
      22236733618716727,
      22518212890394746,
      3670127
    ],
    "uint_char_decode": "\u0001\u0002&\u0001\u0003\u0003\u0003\u0002\u0002\u0002\u0002\u0002\u0003\u0003\u0003\u0003\u0003\u0002\u0002\u0002\u0002\u0002\u0003\u0003\u0003\u0003\u0003\u0002\u0002\u0002\u0002\u0002\u0002\u0003\u0003\u0003\u0002\u0003\u0002\u0002\u0002\u0003"
  }
}

```

#### `event_id`

```json

{
  "field": "event_id",
  "shape": [
    1,
    6
  ],
  "dtype": "uint32",
  "attrs": {
    "H5PATH": "/sbj_P_01",
    "MATLAB_class": "string",
    "MATLAB_object_decode": 3
  },
  "values": [
    3707764736,
    2,
    1,
    1,
    5,
    1
  ],
  "candidate": {
    "raw": [
      3707764736,
      2,
      1,
      1,
      5,
      1
    ],
    "is_candidate": true,
    "ref_index_guess": 5,
    "ref_name_guess": "e"
  },
  "referenced_object_preview": {
    "type": "Dataset",
    "shape": [
      71,
      1
    ],
    "dtype": "uint64",
    "attrs": {
      "H5PATH": "/#refs#/e",
      "MATLAB_class": "uint64"
    },
    "values": [
      1,
      2,
      38,
      1,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      3,
      19422078340235333,
      19422069750431813,
      19985019703722055,
      19422078340235333,
      19422069750431813,
      19985019703722055,
      19422078340235333,
      19422069750431813,
      19985019703722055,
      19422078340235333,
      19422069750431813,
      19985019703722055,
      19422078340235333,
      19422069750431813,
      19985019703722055,
      19422078340235333,
      19422069750431813,
      19985019703722055,
      19422078340235333,
      19422069750431813,
      19985019703722055,
      19422078340235333,
      19422069750431813,
      19985019703722055,
      19422078340235333,
      19422069750431813,
      19985019703722055,
      19422078340235333,
      4653125
    ],
    "uint_char_decode": "\u0001\u0002&\u0001\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003"
  }
}

```

### `#refs#` object previews

#### `#refs#/a`

```json

{
  "type": "Dataset",
  "shape": [
    2
  ],
  "dtype": "uint64",
  "attrs": {
    "MATLAB_class": "canonical empty",
    "MATLAB_empty": 1
  },
  "values": [
    0,
    0
  ]
}

```

#### `#refs#/b`

```json

{
  "type": "Dataset",
  "shape": [
    1,
    376
  ],
  "dtype": "uint8",
  "attrs": {
    "H5PATH": "/#refs#/b",
    "MATLAB_class": "uint8"
  },
  "preview": [
    3,
    0,
    0,
    0,
    2,
    0,
    0,
    0,
    56,
    0,
    0,
    0,
    88,
    0,
    0,
    0,
    176,
    0,
    0,
    0,
    64,
    1,
    0,
    0,
    72,
    1,
    0,
    0,
    120,
    1,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    97,
    110,
    121,
    0,
    115,
    116,
    114,
    105,
    110,
    103,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    2,
    0,
    0,
    0
  ],
  "uint_char_decode": "\u0003\u00028X°@\u0001H\u0001x\u0001anystring\u0002\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0002\u0001\u0001\u0001\u0003\u0001\u0001\u0001\u0004\u0001\u0001\u0001\u0001\u0002\u0002\u0001\u0003\u0003\u0001\u0004\u0004\u0001\u0005\u0005"
}

```

#### `#refs#/c`

```json

{
  "type": "Dataset",
  "shape": [
    7,
    1
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/c",
    "MATLAB_class": "uint64"
  },
  "values": [
    1,
    2,
    1,
    1,
    8,
    26740578060468339,
    13792480023478352
  ],
  "uint_char_decode": "\u0001\u0002\u0001\u0001\b"
}

```

#### `#refs#/d`

```json

{
  "type": "Dataset",
  "shape": [
    66,
    1
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/d",
    "MATLAB_class": "uint64"
  },
  "values": [
    1,
    2,
    38,
    1,
    3,
    3,
    3,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    3,
    3,
    3,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    3,
    3,
    3,
    2,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    3,
    2,
    3,
    2,
    2,
    2,
    3,
    19703458830483526,
    31525498047299696,
    19703484597534770,
    19703772360343603,
    19703488892502068,
    27866323345670260,
    34340372365049907,
    19703471714533446,
    14355584593166452,
    34340234924851267,
    14637059569614915,
    18859059670155348,
    31525485157744752,
    14637179829682298,
    23644138569203796,
    22518217185427509,
    23644121387237498,
    22518225775362102,
    31244066015608943,
    14637175535566970,
    31244066015805520,
    22236733618716727,
    22518212890394746,
    3670127
  ],
  "uint_char_decode": "\u0001\u0002&\u0001\u0003\u0003\u0003\u0002\u0002\u0002\u0002\u0002\u0003\u0003\u0003\u0003\u0003\u0002\u0002\u0002\u0002\u0002\u0003\u0003\u0003\u0003\u0003\u0002\u0002\u0002\u0002\u0002\u0002\u0003\u0003\u0003\u0002\u0003\u0002\u0002\u0002\u0003"
}

```

#### `#refs#/e`

```json

{
  "type": "Dataset",
  "shape": [
    71,
    1
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/e",
    "MATLAB_class": "uint64"
  },
  "values": [
    1,
    2,
    38,
    1,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    19422078340235333,
    19422069750431813,
    19985019703722055,
    19422078340235333,
    19422069750431813,
    19985019703722055,
    19422078340235333,
    19422069750431813,
    19985019703722055,
    19422078340235333,
    19422069750431813,
    19985019703722055,
    19422078340235333,
    19422069750431813,
    19985019703722055,
    19422078340235333,
    19422069750431813,
    19985019703722055,
    19422078340235333,
    19422069750431813,
    19985019703722055,
    19422078340235333,
    19422069750431813,
    19985019703722055,
    19422078340235333,
    19422069750431813,
    19985019703722055,
    19422078340235333,
    4653125
  ],
  "uint_char_decode": "\u0001\u0002&\u0001\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003\u0003"
}

```

#### `#refs#/f`

```json

{
  "type": "Dataset",
  "shape": [
    61,
    1
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/f",
    "MATLAB_class": "uint64"
  },
  "values": [
    1,
    2,
    38,
    1,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261,
    24207350513926261
  ],
  "uint_char_decode": "\u0001\u0002&\u0001\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002\u0002"
}

```

#### `#refs#/g`

```json

{
  "type": "Dataset",
  "shape": [
    367,
    1
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/g",
    "MATLAB_class": "uint64"
  },
  "preview": [
    1,
    2,
    1,
    100,
    3,
    7,
    3,
    9,
    11,
    12,
    11,
    8,
    9,
    8,
    11,
    12,
    11,
    10,
    11,
    10,
    20,
    21,
    20,
    14,
    15,
    14,
    18,
    19,
    18,
    20,
    21,
    20,
    16,
    17,
    16,
    10,
    11,
    10,
    8,
    9,
    8,
    9,
    10,
    9,
    8,
    9,
    8,
    11,
    12,
    11,
    8,
    9,
    8,
    8,
    9,
    8,
    8,
    9,
    8,
    8,
    9,
    8,
    13,
    14,
    13,
    10,
    11,
    10,
    8,
    9,
    8,
    11,
    12,
    11,
    8,
    9,
    8,
    8,
    9,
    8
  ],
  "uint_char_decode": "\u0001\u0002\u0001d\u0003\u0007\u0003\t\u000b\f\u000b\b\t\b\u000b\f\u000b\n\u000b\n\u0014\u0015\u0014\u000e\u000f\u000e\u0012\u0013\u0012\u0014\u0015\u0014\u0010\u0011\u0010\n\u000b\n\b\t\b\t\n\t\b\t\b\u000b\f\u000b\b\t\b\b\t\b\b\t\b\b\t\b\r\u000e\r\n\u000b\n\b\t\b\u000b\f\u000b\b\t\b\b\t\b\n\u000b\n\b\t\b\b\t\b\n\u000b\n\b\t\b\b\t\b\b\t\b\b\t\b"
}

```

#### `#refs#/h`

```json

{
  "type": "Dataset",
  "shape": [
    1,
    2
  ],
  "dtype": "int32",
  "attrs": {
    "H5PATH": "/#refs#/h",
    "MATLAB_class": "int32"
  },
  "values": [
    0,
    0
  ]
}

```

#### `#refs#/i`

```json

{
  "type": "Dataset",
  "shape": [
    1,
    2
  ],
  "dtype": "object",
  "attrs": {
    "H5PATH": "/#refs#/i",
    "MATLAB_class": "cell"
  },
  "values": [
    "<HDF5 object reference>",
    "<HDF5 object reference>"
  ]
}

```

#### `#refs#/j`

```json

{
  "type": "Dataset",
  "shape": [
    2
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/j",
    "MATLAB_class": "struct",
    "MATLAB_empty": 1
  },
  "values": [
    1,
    0
  ],
  "uint_char_decode": "\u0001"
}

```

#### `#refs#/k`

```json

{
  "type": "Dataset",
  "shape": [
    2
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/k",
    "MATLAB_class": "struct",
    "MATLAB_empty": 1
  },
  "values": [
    1,
    0
  ],
  "uint_char_decode": "\u0001"
}

```

## HDF5 File: `EMG_sbj_P_01`

- Path: `/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_01.mat`

- Top keys: `['#refs#', '#subsystem#', 'sbj_P_01']`

- Group keys: `['Fs', 'channels', 'channels_type', 'channels_unit', 'data', 'event_begin', 'event_end', 'event_id', 'subject', 'time']`

- Refs keys: `['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k']`

### Raw data orientation

```json

{
  "data_shape": [
    2207651,
    2
  ],
  "time_shape": [
    2207651,
    1
  ],
  "guess": "time x channels"
}

```

### Event timing summary

```json

{
  "fs": 2000.0,
  "num_events": 100,
  "num_around_5s_4p5_to_5p5": 65,
  "duration_unique_rounded": [
    4.986,
    4.987,
    4.988,
    4.989,
    4.99,
    4.991,
    4.992,
    4.993,
    4.994,
    4.995,
    4.996,
    4.997,
    4.998,
    4.999,
    5.0,
    5.001,
    5.002,
    5.004,
    5.006,
    5.016,
    5.397,
    6.307,
    6.412,
    6.664,
    6.71,
    7.383,
    7.417,
    7.501,
    7.978,
    8.034,
    8.095,
    8.423,
    8.468,
    8.493,
    8.598,
    8.762,
    8.982,
    9.048,
    9.109,
    9.254,
    9.727,
    9.817,
    9.996,
    10.522,
    10.545,
    10.601,
    11.321,
    11.586,
    12.624,
    14.302,
    17.336,
    19.062,
    19.995,
    59.997,
    74.22,
    119.994
  ],
  "events_first_40": [
    {
      "event_index_1based": 1,
      "event_begin": 399327.0,
      "event_end": 519321.0,
      "duration_sec": 59.997,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 2,
      "event_begin": 519391.0,
      "event_end": 559381.0,
      "duration_sec": 19.995,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 3,
      "event_begin": 559491.0,
      "event_end": 799479.0,
      "duration_sec": 119.994,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 4,
      "event_begin": 799575.0,
      "event_end": 819567.0,
      "duration_sec": 9.996,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 5,
      "event_begin": 819649.0,
      "event_end": 829635.0,
      "duration_sec": 4.993,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 6,
      "event_begin": 829783.0,
      "event_end": 839757.0,
      "duration_sec": 4.987,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 7,
      "event_begin": 839817.0,
      "event_end": 874489.0,
      "duration_sec": 17.336,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 8,
      "event_begin": 874593.0,
      "event_end": 884575.0,
      "duration_sec": 4.991,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 9,
      "event_begin": 884697.0,
      "event_end": 894705.0,
      "duration_sec": 5.004,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 10,
      "event_begin": 894815.0,
      "event_end": 923419.0,
      "duration_sec": 14.302,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 11,
      "event_begin": 923477.0,
      "event_end": 933479.0,
      "duration_sec": 5.001,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 12,
      "event_begin": 933601.0,
      "event_end": 943605.0,
      "duration_sec": 5.002,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 13,
      "event_begin": 943653.0,
      "event_end": 981777.0,
      "duration_sec": 19.062,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 14,
      "event_begin": 981881.0,
      "event_end": 991893.0,
      "duration_sec": 5.006,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 15,
      "event_begin": 992045.0,
      "event_end": 1002039.0,
      "duration_sec": 4.997,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 16,
      "event_begin": 1002111.0,
      "event_end": 1023155.0,
      "duration_sec": 10.522,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 17,
      "event_begin": 1023311.0,
      "event_end": 1033289.0,
      "duration_sec": 4.989,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 18,
      "event_begin": 1033439.0,
      "event_end": 1043431.0,
      "duration_sec": 4.996,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 19,
      "event_begin": 1043479.0,
      "event_end": 1068727.0,
      "duration_sec": 12.624,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 20,
      "event_begin": 1068911.0,
      "event_end": 1078883.0,
      "duration_sec": 4.986,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 21,
      "event_begin": 1079041.0,
      "event_end": 1089043.0,
      "duration_sec": 5.001,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 22,
      "event_begin": 1089111.0,
      "event_end": 1112283.0,
      "duration_sec": 11.586,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 23,
      "event_begin": 1112377.0,
      "event_end": 1122349.0,
      "duration_sec": 4.986,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 24,
      "event_begin": 1122509.0,
      "event_end": 1132509.0,
      "duration_sec": 5.0,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 25,
      "event_begin": 1132577.0,
      "event_end": 1149423.0,
      "duration_sec": 8.423,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 26,
      "event_begin": 1149601.0,
      "event_end": 1159599.0,
      "duration_sec": 4.999,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 27,
      "event_begin": 1159777.0,
      "event_end": 1169761.0,
      "duration_sec": 4.992,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 28,
      "event_begin": 1169877.0,
      "event_end": 1184643.0,
      "duration_sec": 7.383,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 29,
      "event_begin": 1184743.0,
      "event_end": 1194727.0,
      "duration_sec": 4.992,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 30,
      "event_begin": 1194841.0,
      "event_end": 1204823.0,
      "duration_sec": 4.991,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 31,
      "event_begin": 1204929.0,
      "event_end": 1221915.0,
      "duration_sec": 8.493,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 32,
      "event_begin": 1222009.0,
      "event_end": 1232009.0,
      "duration_sec": 5.0,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 33,
      "event_begin": 1232255.0,
      "event_end": 1242257.0,
      "duration_sec": 5.001,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 34,
      "event_begin": 1242373.0,
      "event_end": 1263463.0,
      "duration_sec": 10.545,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 35,
      "event_begin": 1263583.0,
      "event_end": 1273573.0,
      "duration_sec": 4.995,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 36,
      "event_begin": 1273707.0,
      "event_end": 1283693.0,
      "duration_sec": 4.993,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 37,
      "event_begin": 1283739.0,
      "event_end": 1299929.0,
      "duration_sec": 8.095,
      "is_around_5s_4p5_to_5p5": false
    },
    {
      "event_index_1based": 38,
      "event_begin": 1300073.0,
      "event_end": 1310071.0,
      "duration_sec": 4.999,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 39,
      "event_begin": 1310239.0,
      "event_end": 1320227.0,
      "duration_sec": 4.994,
      "is_around_5s_4p5_to_5p5": true
    },
    {
      "event_index_1based": 40,
      "event_begin": 1320291.0,
      "event_end": 1338509.0,
      "duration_sec": 9.109,
      "is_around_5s_4p5_to_5p5": false
    }
  ],
  "around_5s_event_indices_1based": [
    5,
    6,
    8,
    9,
    11,
    12,
    14,
    15,
    17,
    18,
    20,
    21,
    23,
    24,
    26,
    27,
    29,
    30,
    32,
    33,
    35,
    36,
    38,
    39,
    41,
    42,
    44,
    45,
    47,
    48,
    50,
    51,
    53,
    54,
    56,
    57,
    59,
    60,
    62,
    63,
    65,
    66,
    68,
    69,
    71,
    72,
    74,
    75,
    77,
    78,
    80,
    81,
    83,
    84,
    85,
    86,
    87,
    89,
    90,
    92,
    93,
    95,
    96,
    98,
    99
  ]
}

```

### Field reference candidates

#### `subject`

```json

{
  "field": "subject",
  "shape": [
    1,
    6
  ],
  "dtype": "uint32",
  "attrs": {
    "H5PATH": "/sbj_P_01",
    "MATLAB_class": "string",
    "MATLAB_object_decode": 3
  },
  "values": [
    3707764736,
    2,
    1,
    1,
    1,
    1
  ],
  "candidate": {
    "raw": [
      3707764736,
      2,
      1,
      1,
      1,
      1
    ],
    "is_candidate": true,
    "ref_index_guess": 1,
    "ref_name_guess": "a"
  },
  "referenced_object_preview": {
    "type": "Dataset",
    "shape": [
      2
    ],
    "dtype": "uint64",
    "attrs": {
      "MATLAB_class": "canonical empty",
      "MATLAB_empty": 1
    },
    "values": [
      0,
      0
    ]
  }
}

```

#### `channels`

```json

{
  "field": "channels",
  "shape": [
    1,
    6
  ],
  "dtype": "uint32",
  "attrs": {
    "H5PATH": "/sbj_P_01",
    "MATLAB_class": "string",
    "MATLAB_object_decode": 3
  },
  "values": [
    3707764736,
    2,
    1,
    1,
    2,
    1
  ],
  "candidate": {
    "raw": [
      3707764736,
      2,
      1,
      1,
      2,
      1
    ],
    "is_candidate": true,
    "ref_index_guess": 2,
    "ref_name_guess": "b"
  },
  "referenced_object_preview": {
    "type": "Dataset",
    "shape": [
      1,
      376
    ],
    "dtype": "uint8",
    "attrs": {
      "H5PATH": "/#refs#/b",
      "MATLAB_class": "uint8"
    },
    "preview": [
      3,
      0,
      0,
      0,
      2,
      0,
      0,
      0,
      56,
      0,
      0,
      0,
      88,
      0,
      0,
      0,
      176,
      0,
      0,
      0,
      64,
      1,
      0,
      0,
      72,
      1,
      0,
      0,
      120,
      1,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      97,
      110,
      121,
      0,
      115,
      116,
      114,
      105,
      110,
      103,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      2,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      0,
      0,
      0,
      0,
      1,
      0,
      0,
      0,
      1,
      0,
      0,
      0
    ],
    "uint_char_decode": "\u0003\u00028X°@\u0001H\u0001x\u0001anystring\u0002\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0002\u0001\u0001\u0001\u0003\u0001\u0001\u0001\u0004\u0001\u0001\u0001\u0001\u0002\u0002\u0001\u0003\u0003\u0001\u0004\u0004\u0001\u0005\u0005"
  }
}

```

#### `channels_type`

```json

{
  "field": "channels_type",
  "shape": [
    1,
    6
  ],
  "dtype": "uint32",
  "attrs": {
    "H5PATH": "/sbj_P_01",
    "MATLAB_class": "string",
    "MATLAB_object_decode": 3
  },
  "values": [
    3707764736,
    2,
    1,
    1,
    3,
    1
  ],
  "candidate": {
    "raw": [
      3707764736,
      2,
      1,
      1,
      3,
      1
    ],
    "is_candidate": true,
    "ref_index_guess": 3,
    "ref_name_guess": "c"
  },
  "referenced_object_preview": {
    "type": "Dataset",
    "shape": [
      7,
      1
    ],
    "dtype": "uint64",
    "attrs": {
      "H5PATH": "/#refs#/c",
      "MATLAB_class": "uint64"
    },
    "values": [
      1,
      2,
      1,
      1,
      8,
      26740578060468339,
      13792480023478352
    ],
    "uint_char_decode": "\u0001\u0002\u0001\u0001\b"
  }
}

```

#### `channels_unit`

```json

{
  "field": "channels_unit",
  "shape": [
    1,
    6
  ],
  "dtype": "uint32",
  "attrs": {
    "H5PATH": "/sbj_P_01",
    "MATLAB_class": "string",
    "MATLAB_object_decode": 3
  },
  "values": [
    3707764736,
    2,
    1,
    1,
    4,
    1
  ],
  "candidate": {
    "raw": [
      3707764736,
      2,
      1,
      1,
      4,
      1
    ],
    "is_candidate": true,
    "ref_index_guess": 4,
    "ref_name_guess": "d"
  },
  "referenced_object_preview": {
    "type": "Dataset",
    "shape": [
      8,
      1
    ],
    "dtype": "uint64",
    "attrs": {
      "H5PATH": "/#refs#/d",
      "MATLAB_class": "uint64"
    },
    "values": [
      1,
      2,
      2,
      1,
      3,
      4,
      18859265828126810,
      489633742959
    ],
    "uint_char_decode": "\u0001\u0002\u0002\u0001\u0003\u0004"
  }
}

```

#### `event_id`

```json

{
  "field": "event_id",
  "shape": [
    1,
    6
  ],
  "dtype": "uint32",
  "attrs": {
    "H5PATH": "/sbj_P_01",
    "MATLAB_class": "string",
    "MATLAB_object_decode": 3
  },
  "values": [
    3707764736,
    2,
    1,
    1,
    5,
    1
  ],
  "candidate": {
    "raw": [
      3707764736,
      2,
      1,
      1,
      5,
      1
    ],
    "is_candidate": true,
    "ref_index_guess": 5,
    "ref_name_guess": "e"
  },
  "referenced_object_preview": {
    "type": "Dataset",
    "shape": [
      8,
      1
    ],
    "dtype": "uint64",
    "attrs": {
      "H5PATH": "/#refs#/e",
      "MATLAB_class": "uint64"
    },
    "values": [
      1,
      2,
      2,
      1,
      3,
      3,
      19422078340759621,
      4653133
    ],
    "uint_char_decode": "\u0001\u0002\u0002\u0001\u0003\u0003"
  }
}

```

### `#refs#` object previews

#### `#refs#/a`

```json

{
  "type": "Dataset",
  "shape": [
    2
  ],
  "dtype": "uint64",
  "attrs": {
    "MATLAB_class": "canonical empty",
    "MATLAB_empty": 1
  },
  "values": [
    0,
    0
  ]
}

```

#### `#refs#/b`

```json

{
  "type": "Dataset",
  "shape": [
    1,
    376
  ],
  "dtype": "uint8",
  "attrs": {
    "H5PATH": "/#refs#/b",
    "MATLAB_class": "uint8"
  },
  "preview": [
    3,
    0,
    0,
    0,
    2,
    0,
    0,
    0,
    56,
    0,
    0,
    0,
    88,
    0,
    0,
    0,
    176,
    0,
    0,
    0,
    64,
    1,
    0,
    0,
    72,
    1,
    0,
    0,
    120,
    1,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    97,
    110,
    121,
    0,
    115,
    116,
    114,
    105,
    110,
    103,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    2,
    0,
    0,
    0
  ],
  "uint_char_decode": "\u0003\u00028X°@\u0001H\u0001x\u0001anystring\u0002\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0001\u0002\u0001\u0001\u0001\u0003\u0001\u0001\u0001\u0004\u0001\u0001\u0001\u0001\u0002\u0002\u0001\u0003\u0003\u0001\u0004\u0004\u0001\u0005\u0005"
}

```

#### `#refs#/c`

```json

{
  "type": "Dataset",
  "shape": [
    7,
    1
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/c",
    "MATLAB_class": "uint64"
  },
  "values": [
    1,
    2,
    1,
    1,
    8,
    26740578060468339,
    13792480023478352
  ],
  "uint_char_decode": "\u0001\u0002\u0001\u0001\b"
}

```

#### `#refs#/d`

```json

{
  "type": "Dataset",
  "shape": [
    8,
    1
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/d",
    "MATLAB_class": "uint64"
  },
  "values": [
    1,
    2,
    2,
    1,
    3,
    4,
    18859265828126810,
    489633742959
  ],
  "uint_char_decode": "\u0001\u0002\u0002\u0001\u0003\u0004"
}

```

#### `#refs#/e`

```json

{
  "type": "Dataset",
  "shape": [
    8,
    1
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/e",
    "MATLAB_class": "uint64"
  },
  "values": [
    1,
    2,
    2,
    1,
    3,
    3,
    19422078340759621,
    4653133
  ],
  "uint_char_decode": "\u0001\u0002\u0002\u0001\u0003\u0003"
}

```

#### `#refs#/f`

```json

{
  "type": "Dataset",
  "shape": [
    7,
    1
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/f",
    "MATLAB_class": "uint64"
  },
  "values": [
    1,
    2,
    2,
    1,
    2,
    2,
    24207350513926261
  ],
  "uint_char_decode": "\u0001\u0002\u0002\u0001\u0002\u0002"
}

```

#### `#refs#/g`

```json

{
  "type": "Dataset",
  "shape": [
    367,
    1
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/g",
    "MATLAB_class": "uint64"
  },
  "preview": [
    1,
    2,
    1,
    100,
    3,
    7,
    3,
    9,
    11,
    12,
    11,
    8,
    9,
    8,
    11,
    12,
    11,
    10,
    11,
    10,
    20,
    21,
    20,
    14,
    15,
    14,
    18,
    19,
    18,
    20,
    21,
    20,
    16,
    17,
    16,
    10,
    11,
    10,
    8,
    9,
    8,
    9,
    10,
    9,
    8,
    9,
    8,
    11,
    12,
    11,
    8,
    9,
    8,
    8,
    9,
    8,
    8,
    9,
    8,
    8,
    9,
    8,
    13,
    14,
    13,
    10,
    11,
    10,
    8,
    9,
    8,
    11,
    12,
    11,
    8,
    9,
    8,
    8,
    9,
    8
  ],
  "uint_char_decode": "\u0001\u0002\u0001d\u0003\u0007\u0003\t\u000b\f\u000b\b\t\b\u000b\f\u000b\n\u000b\n\u0014\u0015\u0014\u000e\u000f\u000e\u0012\u0013\u0012\u0014\u0015\u0014\u0010\u0011\u0010\n\u000b\n\b\t\b\t\n\t\b\t\b\u000b\f\u000b\b\t\b\b\t\b\b\t\b\b\t\b\r\u000e\r\n\u000b\n\b\t\b\u000b\f\u000b\b\t\b\b\t\b\n\u000b\n\b\t\b\b\t\b\n\u000b\n\b\t\b\b\t\b\b\t\b\b\t\b"
}

```

#### `#refs#/h`

```json

{
  "type": "Dataset",
  "shape": [
    1,
    2
  ],
  "dtype": "int32",
  "attrs": {
    "H5PATH": "/#refs#/h",
    "MATLAB_class": "int32"
  },
  "values": [
    0,
    0
  ]
}

```

#### `#refs#/i`

```json

{
  "type": "Dataset",
  "shape": [
    1,
    2
  ],
  "dtype": "object",
  "attrs": {
    "H5PATH": "/#refs#/i",
    "MATLAB_class": "cell"
  },
  "values": [
    "<HDF5 object reference>",
    "<HDF5 object reference>"
  ]
}

```

#### `#refs#/j`

```json

{
  "type": "Dataset",
  "shape": [
    2
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/j",
    "MATLAB_class": "struct",
    "MATLAB_empty": 1
  },
  "values": [
    1,
    0
  ],
  "uint_char_decode": "\u0001"
}

```

#### `#refs#/k`

```json

{
  "type": "Dataset",
  "shape": [
    2
  ],
  "dtype": "uint64",
  "attrs": {
    "H5PATH": "/#refs#/k",
    "MATLAB_class": "struct",
    "MATLAB_empty": 1
  },
  "values": [
    1,
    0
  ],
  "uint_char_decode": "\u0001"
}

```



# FILE: docs/idare_trial_index_probe.md


# I-DARE Trial Index Probe

This report was generated by `scripts/05_probe_idare_trial_index.py`.

No training or preprocessing was performed.

## Summary

```json

{
  "specs_rows": 100,
  "specs_stim_rows": 32,
  "label_stimuli": 32,
  "stim_rows_match_label_stimuli": true,
  "specs_stim_ids_sorted": [
    "1441",
    "1750",
    "2314",
    "2491",
    "3053",
    "3063",
    "3080",
    "3170",
    "4220",
    "5760",
    "8080",
    "8370",
    "8492",
    "9220",
    "9331",
    "9360",
    "Angry_face_1",
    "Beach_1",
    "Depressed_pose_4",
    "Dog_18",
    "Dog_26",
    "Dog_6",
    "Dummy_1",
    "Flowers_6",
    "Garbage_dump_6",
    "Lake_12",
    "Lake_3",
    "Miserable_pose_3",
    "Pinecone_1",
    "Snow_1",
    "Tumor_1",
    "Yarn_1"
  ],
  "label_stim_ids_sorted": [
    "1441",
    "1750",
    "2314",
    "2491",
    "3053",
    "3063",
    "3080",
    "3170",
    "4220",
    "5760",
    "8080",
    "8370",
    "8492",
    "9220",
    "9331",
    "9360",
    "Angry_face_1",
    "Beach_1",
    "Depressed_pose_4",
    "Dog_18",
    "Dog_26",
    "Dog_6",
    "Dummy_1",
    "Flowers_6",
    "Garbage_dump_6",
    "Lake_12",
    "Lake_3",
    "Miserable_pose_3",
    "Pinecone_1",
    "Snow_1",
    "Tumor_1",
    "Yarn_1"
  ],
  "common_subject_count": 63,
  "sample_subjects": [
    1,
    2,
    3
  ]
}

```

## Loader Interpretation

- `Stimuli_Specifications.csv` has 100 rows.

- Each subject `.mat` file has 100 event begin/end pairs.

- Rows appear to align with event indices in order.

- Main emotional trials should use `STIM_*` rows only.

- Label CSV files store stimulus IDs without the `STIM_` prefix.

- Therefore, loader should map `STIM_<id>` to label stimulus `<id>`.

## Subject `sbj_P_01`

### Event summaries

```json

{
  "eeg": {
    "fs": 512.0,
    "data_shape": [
      565159,
      38
    ],
    "time_shape": [
      565159,
      1
    ],
    "num_events": 100
  },
  "emg": {
    "fs": 2000.0,
    "data_shape": [
      2207651,
      2
    ],
    "time_shape": [
      2207651,
      1
    ],
    "num_events": 100
  },
  "all_rows_count": 100,
  "stim_rows_count": 32,
  "labeled_stim_rows_count": 32,
  "duration_checks": {
    "all_labeled_stim_eeg_4p5_to_5p5": true,
    "all_labeled_stim_emg_4p5_to_5p5": true,
    "eeg_labeled_stim_min_duration": 4.984375,
    "eeg_labeled_stim_max_duration": 5.001953125,
    "emg_labeled_stim_min_duration": 4.986,
    "emg_labeled_stim_max_duration": 5.004
  }
}

```

### Labeled STIM row preview

```json

[
  {
    "subject_id": 1,
    "subject_col": "sbj_P_01",
    "event_index_1based": 6,
    "raw_event_name": "STIM_Dummy_1",
    "stimulus_id": "Dummy_1",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.987,
    "eeg_begin": 212425.0,
    "eeg_end": 214977.0,
    "eeg_duration_sec": 4.984375,
    "emg_begin": 829783.0,
    "emg_end": 839757.0,
    "emg_duration_sec": 4.987,
    "valence_score": 1,
    "arousal_score": 4,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 1,
    "subject_col": "sbj_P_01",
    "event_index_1based": 9,
    "raw_event_name": "STIM_3053",
    "stimulus_id": "3053",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 5.004,
    "eeg_begin": 226483.0,
    "eeg_end": 229044.0,
    "eeg_duration_sec": 5.001953125,
    "emg_begin": 884697.0,
    "emg_end": 894705.0,
    "emg_duration_sec": 5.004,
    "valence_score": 1,
    "arousal_score": 6,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVHA"
  },
  {
    "subject_id": 1,
    "subject_col": "sbj_P_01",
    "event_index_1based": 12,
    "raw_event_name": "STIM_Tumor_1",
    "stimulus_id": "Tumor_1",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 5.002,
    "eeg_begin": 239003.0,
    "eeg_end": 241563.0,
    "eeg_duration_sec": 5.0,
    "emg_begin": 933601.0,
    "emg_end": 943605.0,
    "emg_duration_sec": 5.002,
    "valence_score": 4,
    "arousal_score": 5,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": null,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 1,
    "subject_col": "sbj_P_01",
    "event_index_1based": 15,
    "raw_event_name": "STIM_Dog_18",
    "stimulus_id": "Dog_18",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.997,
    "eeg_begin": 253964.0,
    "eeg_end": 256521.0,
    "eeg_duration_sec": 4.994140625,
    "emg_begin": 992045.0,
    "emg_end": 1002039.0,
    "emg_duration_sec": 4.997,
    "valence_score": 8,
    "arousal_score": 1,
    "valence_binary_gt5_discard5": 1,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "HVHA ",
    "quadrant_subject": "HVLA"
  },
  {
    "subject_id": 1,
    "subject_col": "sbj_P_01",
    "event_index_1based": 18,
    "raw_event_name": "STIM_Miserable_pose_3",
    "stimulus_id": "Miserable_pose_3",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.996,
    "eeg_begin": 264561.0,
    "eeg_end": 267118.0,
    "eeg_duration_sec": 4.994140625,
    "emg_begin": 1033439.0,
    "emg_end": 1043431.0,
    "emg_duration_sec": 4.996,
    "valence_score": 1,
    "arousal_score": 5,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": null,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 1,
    "subject_col": "sbj_P_01",
    "event_index_1based": 21,
    "raw_event_name": "STIM_Pinecone_1",
    "stimulus_id": "Pinecone_1",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 5.001,
    "eeg_begin": 276235.0,
    "eeg_end": 278795.0,
    "eeg_duration_sec": 5.0,
    "emg_begin": 1079041.0,
    "emg_end": 1089043.0,
    "emg_duration_sec": 5.001,
    "valence_score": 5,
    "arousal_score": 3,
    "valence_binary_gt5_discard5": null,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "HVLA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 1,
    "subject_col": "sbj_P_01",
    "event_index_1based": 24,
    "raw_event_name": "STIM_Garbage_dump_6",
    "stimulus_id": "Garbage_dump_6",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 5.0,
    "eeg_begin": 287363.0,
    "eeg_end": 289922.0,
    "eeg_duration_sec": 4.998046875,
    "emg_begin": 1122509.0,
    "emg_end": 1132509.0,
    "emg_duration_sec": 5.0,
    "valence_score": 2,
    "arousal_score": 7,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "LVLA",
    "quadrant_subject": "LVHA"
  },
  {
    "subject_id": 1,
    "subject_col": "sbj_P_01",
    "event_index_1based": 27,
    "raw_event_name": "STIM_Depressed_pose_4",
    "stimulus_id": "Depressed_pose_4",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.992,
    "eeg_begin": 296904.0,
    "eeg_end": 299459.0,
    "eeg_duration_sec": 4.990234375,
    "emg_begin": 1159777.0,
    "emg_end": 1169761.0,
    "emg_duration_sec": 4.992,
    "valence_score": 4,
    "arousal_score": 3,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "LVLA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 1,
    "subject_col": "sbj_P_01",
    "event_index_1based": 30,
    "raw_event_name": "STIM_Angry_face_1",
    "stimulus_id": "Angry_face_1",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.991,
    "eeg_begin": 305880.0,
    "eeg_end": 308434.0,
    "eeg_duration_sec": 4.98828125,
    "emg_begin": 1194841.0,
    "emg_end": 1204823.0,
    "emg_duration_sec": 4.991,
    "valence_score": 5,
    "arousal_score": 3,
    "valence_binary_gt5_discard5": null,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "LVLA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 1,
    "subject_col": "sbj_P_01",
    "event_index_1based": 33,
    "raw_event_name": "STIM_Dog_26",
    "stimulus_id": "Dog_26",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 5.001,
    "eeg_begin": 315458.0,
    "eeg_end": 318018.0,
    "eeg_duration_sec": 5.0,
    "emg_begin": 1232255.0,
    "emg_end": 1242257.0,
    "emg_duration_sec": 5.001,
    "valence_score": 2,
    "arousal_score": 6,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVHA"
  },
  {
    "subject_id": 1,
    "subject_col": "sbj_P_01",
    "event_index_1based": 36,
    "raw_event_name": "STIM_8370",
    "stimulus_id": "8370",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.993,
    "eeg_begin": 326070.0,
    "eeg_end": 328625.0,
    "eeg_duration_sec": 4.990234375,
    "emg_begin": 1273707.0,
    "emg_end": 1283693.0,
    "emg_duration_sec": 4.993,
    "valence_score": 6,
    "arousal_score": 8,
    "valence_binary_gt5_discard5": 1,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "HVHA ",
    "quadrant_subject": "HVHA"
  },
  {
    "subject_id": 1,
    "subject_col": "sbj_P_01",
    "event_index_1based": 39,
    "raw_event_name": "STIM_Dog_6",
    "stimulus_id": "Dog_6",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.994,
    "eeg_begin": 335422.0,
    "eeg_end": 337978.0,
    "eeg_duration_sec": 4.9921875,
    "emg_begin": 1310239.0,
    "emg_end": 1320227.0,
    "emg_duration_sec": 4.994,
    "valence_score": 7,
    "arousal_score": 1,
    "valence_binary_gt5_discard5": 1,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "HVHA ",
    "quadrant_subject": "HVLA"
  }
]

```

## Subject `sbj_P_02`

### Event summaries

```json

{
  "eeg": {
    "fs": 512.0,
    "data_shape": [
      540472,
      38
    ],
    "time_shape": [
      540472,
      1
    ],
    "num_events": 100
  },
  "emg": {
    "fs": 2000.0,
    "data_shape": [
      2111215,
      2
    ],
    "time_shape": [
      2111215,
      1
    ],
    "num_events": 100
  },
  "all_rows_count": 100,
  "stim_rows_count": 32,
  "labeled_stim_rows_count": 32,
  "duration_checks": {
    "all_labeled_stim_eeg_4p5_to_5p5": true,
    "all_labeled_stim_emg_4p5_to_5p5": true,
    "eeg_labeled_stim_min_duration": 4.984375,
    "eeg_labeled_stim_max_duration": 5.001953125,
    "emg_labeled_stim_min_duration": 4.987,
    "emg_labeled_stim_max_duration": 5.004
  }
}

```

### Labeled STIM row preview

```json

[
  {
    "subject_id": 2,
    "subject_col": "sbj_P_02",
    "event_index_1based": 6,
    "raw_event_name": "STIM_Dummy_1",
    "stimulus_id": "Dummy_1",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.996,
    "eeg_begin": 189235.0,
    "eeg_end": 191792.0,
    "eeg_duration_sec": 4.994140625,
    "emg_begin": 739195.0,
    "emg_end": 749189.0,
    "emg_duration_sec": 4.997,
    "valence_score": 2,
    "arousal_score": 8,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVHA"
  },
  {
    "subject_id": 2,
    "subject_col": "sbj_P_02",
    "event_index_1based": 9,
    "raw_event_name": "STIM_3053",
    "stimulus_id": "3053",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 5.0,
    "eeg_begin": 203757.0,
    "eeg_end": 206310.0,
    "eeg_duration_sec": 4.986328125,
    "emg_begin": 795923.0,
    "emg_end": 805901.0,
    "emg_duration_sec": 4.989,
    "valence_score": 1,
    "arousal_score": 9,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVHA"
  },
  {
    "subject_id": 2,
    "subject_col": "sbj_P_02",
    "event_index_1based": 12,
    "raw_event_name": "STIM_Tumor_1",
    "stimulus_id": "Tumor_1",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 5.004,
    "eeg_begin": 217743.0,
    "eeg_end": 220302.0,
    "eeg_duration_sec": 4.998046875,
    "emg_begin": 850557.0,
    "emg_end": 860557.0,
    "emg_duration_sec": 5.0,
    "valence_score": 1,
    "arousal_score": 9,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVHA"
  },
  {
    "subject_id": 2,
    "subject_col": "sbj_P_02",
    "event_index_1based": 15,
    "raw_event_name": "STIM_Dog_18",
    "stimulus_id": "Dog_18",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.994,
    "eeg_begin": 227464.0,
    "eeg_end": 230024.0,
    "eeg_duration_sec": 5.0,
    "emg_begin": 888529.0,
    "emg_end": 898533.0,
    "emg_duration_sec": 5.002,
    "valence_score": 3,
    "arousal_score": 8,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "HVHA ",
    "quadrant_subject": "LVHA"
  },
  {
    "subject_id": 2,
    "subject_col": "sbj_P_02",
    "event_index_1based": 18,
    "raw_event_name": "STIM_Miserable_pose_3",
    "stimulus_id": "Miserable_pose_3",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.992,
    "eeg_begin": 236337.0,
    "eeg_end": 238895.0,
    "eeg_duration_sec": 4.99609375,
    "emg_begin": 923189.0,
    "emg_end": 933187.0,
    "emg_duration_sec": 4.999,
    "valence_score": 1,
    "arousal_score": 9,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVHA"
  },
  {
    "subject_id": 2,
    "subject_col": "sbj_P_02",
    "event_index_1based": 21,
    "raw_event_name": "STIM_Pinecone_1",
    "stimulus_id": "Pinecone_1",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.992,
    "eeg_begin": 245587.0,
    "eeg_end": 248144.0,
    "eeg_duration_sec": 4.994140625,
    "emg_begin": 959323.0,
    "emg_end": 969317.0,
    "emg_duration_sec": 4.997,
    "valence_score": 6,
    "arousal_score": 2,
    "valence_binary_gt5_discard5": 1,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "HVLA",
    "quadrant_subject": "HVLA"
  },
  {
    "subject_id": 2,
    "subject_col": "sbj_P_02",
    "event_index_1based": 24,
    "raw_event_name": "STIM_Garbage_dump_6",
    "stimulus_id": "Garbage_dump_6",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.992,
    "eeg_begin": 255389.0,
    "eeg_end": 257945.0,
    "eeg_duration_sec": 4.9921875,
    "emg_begin": 997609.0,
    "emg_end": 1007597.0,
    "emg_duration_sec": 4.994,
    "valence_score": 2,
    "arousal_score": 5,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": null,
    "quadrant_gs": "LVLA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 2,
    "subject_col": "sbj_P_02",
    "event_index_1based": 27,
    "raw_event_name": "STIM_Depressed_pose_4",
    "stimulus_id": "Depressed_pose_4",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.991,
    "eeg_begin": 269309.0,
    "eeg_end": 271862.0,
    "eeg_duration_sec": 4.986328125,
    "emg_begin": 1051985.0,
    "emg_end": 1061963.0,
    "emg_duration_sec": 4.989,
    "valence_score": 4,
    "arousal_score": 6,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "LVLA",
    "quadrant_subject": "LVHA"
  },
  {
    "subject_id": 2,
    "subject_col": "sbj_P_02",
    "event_index_1based": 30,
    "raw_event_name": "STIM_Angry_face_1",
    "stimulus_id": "Angry_face_1",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.996,
    "eeg_begin": 276987.0,
    "eeg_end": 279543.0,
    "eeg_duration_sec": 4.9921875,
    "emg_begin": 1081979.0,
    "emg_end": 1091969.0,
    "emg_duration_sec": 4.995,
    "valence_score": 3,
    "arousal_score": 7,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "LVLA",
    "quadrant_subject": "LVHA"
  },
  {
    "subject_id": 2,
    "subject_col": "sbj_P_02",
    "event_index_1based": 33,
    "raw_event_name": "STIM_Dog_26",
    "stimulus_id": "Dog_26",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.998,
    "eeg_begin": 284295.0,
    "eeg_end": 286849.0,
    "eeg_duration_sec": 4.98828125,
    "emg_begin": 1110523.0,
    "emg_end": 1120505.0,
    "emg_duration_sec": 4.991,
    "valence_score": 1,
    "arousal_score": 8,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVHA"
  },
  {
    "subject_id": 2,
    "subject_col": "sbj_P_02",
    "event_index_1based": 36,
    "raw_event_name": "STIM_8370",
    "stimulus_id": "8370",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 5.0,
    "eeg_begin": 297065.0,
    "eeg_end": 299624.0,
    "eeg_duration_sec": 4.998046875,
    "emg_begin": 1160407.0,
    "emg_end": 1170407.0,
    "emg_duration_sec": 5.0,
    "valence_score": 8,
    "arousal_score": 8,
    "valence_binary_gt5_discard5": 1,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "HVHA ",
    "quadrant_subject": "HVHA"
  },
  {
    "subject_id": 2,
    "subject_col": "sbj_P_02",
    "event_index_1based": 39,
    "raw_event_name": "STIM_Dog_6",
    "stimulus_id": "Dog_6",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.998,
    "eeg_begin": 308805.0,
    "eeg_end": 311359.0,
    "eeg_duration_sec": 4.98828125,
    "emg_begin": 1206267.0,
    "emg_end": 1216247.0,
    "emg_duration_sec": 4.99,
    "valence_score": 9,
    "arousal_score": 8,
    "valence_binary_gt5_discard5": 1,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "HVHA ",
    "quadrant_subject": "HVHA"
  }
]

```

## Subject `sbj_P_03`

### Event summaries

```json

{
  "eeg": {
    "fs": 512.0,
    "data_shape": [
      501013,
      38
    ],
    "time_shape": [
      501013,
      1
    ],
    "num_events": 100
  },
  "emg": {
    "fs": 2000.0,
    "data_shape": [
      1957081,
      2
    ],
    "time_shape": [
      1957081,
      1
    ],
    "num_events": 100
  },
  "all_rows_count": 100,
  "stim_rows_count": 32,
  "labeled_stim_rows_count": 32,
  "duration_checks": {
    "all_labeled_stim_eeg_4p5_to_5p5": true,
    "all_labeled_stim_emg_4p5_to_5p5": true,
    "eeg_labeled_stim_min_duration": 4.984375,
    "eeg_labeled_stim_max_duration": 5.001953125,
    "emg_labeled_stim_min_duration": 4.986,
    "emg_labeled_stim_max_duration": 5.004
  }
}

```

### Labeled STIM row preview

```json

[
  {
    "subject_id": 3,
    "subject_col": "sbj_P_03",
    "event_index_1based": 6,
    "raw_event_name": "STIM_Dummy_1",
    "stimulus_id": "Dummy_1",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 5.001,
    "eeg_begin": 212000.0,
    "eeg_end": 214559.0,
    "eeg_duration_sec": 4.998046875,
    "emg_begin": 828123.0,
    "emg_end": 838123.0,
    "emg_duration_sec": 5.0,
    "valence_score": 1,
    "arousal_score": 4,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 3,
    "subject_col": "sbj_P_03",
    "event_index_1based": 9,
    "raw_event_name": "STIM_3053",
    "stimulus_id": "3053",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.999,
    "eeg_begin": 224907.0,
    "eeg_end": 227465.0,
    "eeg_duration_sec": 4.99609375,
    "emg_begin": 878541.0,
    "emg_end": 888537.0,
    "emg_duration_sec": 4.998,
    "valence_score": 1,
    "arousal_score": 6,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 1,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVHA"
  },
  {
    "subject_id": 3,
    "subject_col": "sbj_P_03",
    "event_index_1based": 12,
    "raw_event_name": "STIM_Tumor_1",
    "stimulus_id": "Tumor_1",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.997,
    "eeg_begin": 233661.0,
    "eeg_end": 236216.0,
    "eeg_duration_sec": 4.990234375,
    "emg_begin": 912735.0,
    "emg_end": 922719.0,
    "emg_duration_sec": 4.992,
    "valence_score": 2,
    "arousal_score": 5,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": null,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 3,
    "subject_col": "sbj_P_03",
    "event_index_1based": 15,
    "raw_event_name": "STIM_Dog_18",
    "stimulus_id": "Dog_18",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.988,
    "eeg_begin": 244928.0,
    "eeg_end": 247486.0,
    "eeg_duration_sec": 4.99609375,
    "emg_begin": 956749.0,
    "emg_end": 966747.0,
    "emg_duration_sec": 4.999,
    "valence_score": 9,
    "arousal_score": 4,
    "valence_binary_gt5_discard5": 1,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "HVHA ",
    "quadrant_subject": "HVLA"
  },
  {
    "subject_id": 3,
    "subject_col": "sbj_P_03",
    "event_index_1based": 18,
    "raw_event_name": "STIM_Miserable_pose_3",
    "stimulus_id": "Miserable_pose_3",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.999,
    "eeg_begin": 254512.0,
    "eeg_end": 257071.0,
    "eeg_duration_sec": 4.998046875,
    "emg_begin": 994185.0,
    "emg_end": 1004185.0,
    "emg_duration_sec": 5.0,
    "valence_score": 1,
    "arousal_score": 4,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 3,
    "subject_col": "sbj_P_03",
    "event_index_1based": 21,
    "raw_event_name": "STIM_Pinecone_1",
    "stimulus_id": "Pinecone_1",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.999,
    "eeg_begin": 264450.0,
    "eeg_end": 267008.0,
    "eeg_duration_sec": 4.99609375,
    "emg_begin": 1033005.0,
    "emg_end": 1043003.0,
    "emg_duration_sec": 4.999,
    "valence_score": 5,
    "arousal_score": 1,
    "valence_binary_gt5_discard5": null,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "HVLA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 3,
    "subject_col": "sbj_P_03",
    "event_index_1based": 24,
    "raw_event_name": "STIM_Garbage_dump_6",
    "stimulus_id": "Garbage_dump_6",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.988,
    "eeg_begin": 273293.0,
    "eeg_end": 275846.0,
    "eeg_duration_sec": 4.986328125,
    "emg_begin": 1067547.0,
    "emg_end": 1077525.0,
    "emg_duration_sec": 4.989,
    "valence_score": 1,
    "arousal_score": 2,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "LVLA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 3,
    "subject_col": "sbj_P_03",
    "event_index_1based": 27,
    "raw_event_name": "STIM_Depressed_pose_4",
    "stimulus_id": "Depressed_pose_4",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.998,
    "eeg_begin": 283478.0,
    "eeg_end": 286030.0,
    "eeg_duration_sec": 4.984375,
    "emg_begin": 1107333.0,
    "emg_end": 1117307.0,
    "emg_duration_sec": 4.987,
    "valence_score": 4,
    "arousal_score": 3,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "LVLA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 3,
    "subject_col": "sbj_P_03",
    "event_index_1based": 30,
    "raw_event_name": "STIM_Angry_face_1",
    "stimulus_id": "Angry_face_1",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.998,
    "eeg_begin": 292147.0,
    "eeg_end": 294701.0,
    "eeg_duration_sec": 4.98828125,
    "emg_begin": 1141197.0,
    "emg_end": 1151177.0,
    "emg_duration_sec": 4.99,
    "valence_score": 3,
    "arousal_score": 4,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "LVLA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 3,
    "subject_col": "sbj_P_03",
    "event_index_1based": 33,
    "raw_event_name": "STIM_Dog_26",
    "stimulus_id": "Dog_26",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 4.988,
    "eeg_begin": 302306.0,
    "eeg_end": 304862.0,
    "eeg_duration_sec": 4.9921875,
    "emg_begin": 1180879.0,
    "emg_end": 1190869.0,
    "emg_duration_sec": 4.995,
    "valence_score": 2,
    "arousal_score": 5,
    "valence_binary_gt5_discard5": 0,
    "arousal_binary_gt5_discard5": null,
    "quadrant_gs": "LVHA",
    "quadrant_subject": "LVLA"
  },
  {
    "subject_id": 3,
    "subject_col": "sbj_P_03",
    "event_index_1based": 36,
    "raw_event_name": "STIM_8370",
    "stimulus_id": "8370",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 5.001,
    "eeg_begin": 311428.0,
    "eeg_end": 313984.0,
    "eeg_duration_sec": 4.9921875,
    "emg_begin": 1216513.0,
    "emg_end": 1226501.0,
    "emg_duration_sec": 4.994,
    "valence_score": 8,
    "arousal_score": 4,
    "valence_binary_gt5_discard5": 1,
    "arousal_binary_gt5_discard5": 0,
    "quadrant_gs": "HVHA ",
    "quadrant_subject": "HVLA"
  },
  {
    "subject_id": 3,
    "subject_col": "sbj_P_03",
    "event_index_1based": 39,
    "raw_event_name": "STIM_Dog_6",
    "stimulus_id": "Dog_6",
    "description": "Emotional stimulus",
    "is_stim_event": true,
    "is_labeled": true,
    "metadata_duration_sec": 5.004,
    "eeg_begin": 320053.0,
    "eeg_end": 322606.0,
    "eeg_duration_sec": 4.986328125,
    "emg_begin": 1250203.0,
    "emg_end": 1260179.0,
    "emg_duration_sec": 4.988,
    "valence_score": 9,
    "arousal_score": 5,
    "valence_binary_gt5_discard5": 1,
    "arousal_binary_gt5_discard5": null,
    "quadrant_gs": "HVHA ",
    "quadrant_subject": "HVLA"
  }
]

```

## Candidate Loader Decision

Use the following candidate design unless later evidence contradicts it:

1. Load I-DARE `.mat` files with `h5py`.

2. Use data orientation as `time x channels`.

3. Use `Stimuli_Specifications.csv` row order as the event order.

4. Keep only rows whose `Stimulus` starts with `STIM_`.

5. Strip `STIM_` to match label CSV stimulus IDs.

6. Extract one natural stimulus window per STIM event.

7. EEG: resample from 512Hz to 128Hz later for model input.

8. EMG: extract window-level features from 2000Hz EMG.



# FILE: docs/idare_trial_index_summary.md


# I-DARE Trial Index Summary
This report was generated by `scripts/06_build_idare_trial_index.py`.
No model training was performed.
No signal windows were extracted.
## Outputs
- Trial index CSV: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/.cache/idare_trial_index.csv`
- Summary JSON: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/docs/idare_trial_index_summary.json`
- Summary Markdown: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/docs/idare_trial_index_summary.md`
## Core Counts
| Item | Value |
|---|---:|
| n_rows | 2016 |
| n_subjects | 63 |
| expected_subjects | 63 |
| expected_rows | 2016 |
| trials_per_subject_min | 32 |
| trials_per_subject_max | 32 |
| unique_stimuli | 32 |

## Valence Label Summary
```json
{
  "n_total_rows": 2016,
  "n_scores_present": 2016,
  "score_counts": {
    "1": 283,
    "2": 188,
    "3": 155,
    "4": 186,
    "5": 349,
    "6": 241,
    "7": 247,
    "8": 190,
    "9": 177
  },
  "n_score_eq_5_discard": 349,
  "binary_label_counts_after_discard": {
    "0": 812,
    "1": 855
  },
  "n_rows_after_discard": 1667
}
```

## Arousal Label Summary
```json
{
  "n_total_rows": 2016,
  "n_scores_present": 2016,
  "score_counts": {
    "1": 341,
    "2": 294,
    "3": 246,
    "4": 231,
    "5": 217,
    "6": 206,
    "7": 193,
    "8": 170,
    "9": 118
  },
  "n_score_eq_5_discard": 217,
  "binary_label_counts_after_discard": {
    "0": 1112,
    "1": 687
  },
  "n_rows_after_discard": 1799
}
```

## Duration Checks
```json
{
  "eeg_duration_sec": {
    "min": 4.982421875,
    "max": 5.064453125,
    "mean": 4.994547526041667,
    "all_4p5_to_5p5": true
  },
  "emg_duration_sec": {
    "min": 4.985,
    "max": 5.067,
    "mean": 4.996669642857143,
    "all_4p5_to_5p5": true
  }
}
```

## Issues
- None.

## Warnings
- None.

## Loader Notes
- Use only `STIM_*` rows as emotional trials.
- Strip the `STIM_` prefix to match label CSV stimulus IDs.
- Use the 63 common EEG+EMG subjects for the main I-DARE protocol.
- `score == 5` is marked as discard separately for valence and arousal.
- Raw event begin/end values are preserved. The exact Python slicing convention should be finalized during window extraction.



# FILE: docs/idare_window_extraction_smoke_test.md


# I-DARE Window Extraction Smoke Test

This report was generated by `scripts/07_smoke_idare_window_extraction.py`.

No model training was performed.

No final processed dataset was created.

## Status

Status: **PASSED**

## Inputs / Outputs

- Trial index: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/.cache/idare_trial_index.csv`

- JSON report: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/docs/idare_window_extraction_smoke_test.json`

- Small sample NPZ: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE/.cache/idare_window_smoke_sample.npz`

## Chosen Slicing Convention

```json

{
  "candidate": "raw begin/end as Python half-open slices: data[int(begin):int(end), :]",
  "reason": "This convention gives sample_count = end - begin, matching the duration stored in .cache/idare_trial_index.csv.",
  "note": "The MATLAB 1-based inclusive convention gives one extra sample. The final loader can revisit this, but the half-open convention is the clean working choice for the first extraction implementation."
}

```

## Summary

- Sample rows tested: `8`

- Target EEG model channels: `32`

- Target EEG sampling rate after resampling: `128.0`

- Issues: `0`

- Warnings: `0`

## Window Summaries

### Subject 1 - `Dummy_1`

- Raw event: `STIM_Dummy_1`

- Event index 1-based: `6`

- Valence score / label: `1` / `0`

- Arousal score / label: `4` / `0`

#### EEG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_01.mat",
  "fs": 512.0,
  "raw_data_shape": [
    565159,
    38
  ],
  "begin_raw": 212425.0,
  "end_raw": 214977.0,
  "trial_index_duration_samples": 2552.0,
  "trial_index_duration_sec": 4.984375,
  "half_open_shape_time_x_channels": [
    2552,
    38
  ],
  "half_open_duration_sec": 4.984375,
  "matlab_1based_inclusive_shape_time_x_channels": [
    2553,
    38
  ],
  "matlab_1based_inclusive_duration_sec": 4.986328125,
  "model_candidate_first32_shape_channels_x_time": [
    32,
    2552
  ],
  "model_candidate_first32_resampled_128hz_shape_channels_x_time": [
    32,
    638
  ],
  "model_candidate_first32_resampled_128hz_duration_sec": 4.984375
}

```

#### EMG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_01.mat",
  "fs": 2000.0,
  "raw_data_shape": [
    2207651,
    2
  ],
  "begin_raw": 829783.0,
  "end_raw": 839757.0,
  "trial_index_duration_samples": 9974.0,
  "trial_index_duration_sec": 4.987,
  "half_open_shape_time_x_channels": [
    9974,
    2
  ],
  "half_open_duration_sec": 4.987,
  "matlab_1based_inclusive_shape_time_x_channels": [
    9975,
    2
  ],
  "matlab_1based_inclusive_duration_sec": 4.9875
}

```

### Subject 1 - `3053`

- Raw event: `STIM_3053`

- Event index 1-based: `9`

- Valence score / label: `1` / `0`

- Arousal score / label: `6` / `1`

#### EEG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_01.mat",
  "fs": 512.0,
  "raw_data_shape": [
    565159,
    38
  ],
  "begin_raw": 226483.0,
  "end_raw": 229044.0,
  "trial_index_duration_samples": 2561.0,
  "trial_index_duration_sec": 5.001953125,
  "half_open_shape_time_x_channels": [
    2561,
    38
  ],
  "half_open_duration_sec": 5.001953125,
  "matlab_1based_inclusive_shape_time_x_channels": [
    2562,
    38
  ],
  "matlab_1based_inclusive_duration_sec": 5.00390625,
  "model_candidate_first32_shape_channels_x_time": [
    32,
    2561
  ],
  "model_candidate_first32_resampled_128hz_shape_channels_x_time": [
    32,
    641
  ],
  "model_candidate_first32_resampled_128hz_duration_sec": 5.0078125
}

```

#### EMG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_01.mat",
  "fs": 2000.0,
  "raw_data_shape": [
    2207651,
    2
  ],
  "begin_raw": 884697.0,
  "end_raw": 894705.0,
  "trial_index_duration_samples": 10008.0,
  "trial_index_duration_sec": 5.004,
  "half_open_shape_time_x_channels": [
    10008,
    2
  ],
  "half_open_duration_sec": 5.004,
  "matlab_1based_inclusive_shape_time_x_channels": [
    10009,
    2
  ],
  "matlab_1based_inclusive_duration_sec": 5.0045
}

```

### Subject 1 - `Tumor_1`

- Raw event: `STIM_Tumor_1`

- Event index 1-based: `12`

- Valence score / label: `4` / `0`

- Arousal score / label: `5` / `None`

#### EEG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_01.mat",
  "fs": 512.0,
  "raw_data_shape": [
    565159,
    38
  ],
  "begin_raw": 239003.0,
  "end_raw": 241563.0,
  "trial_index_duration_samples": 2560.0,
  "trial_index_duration_sec": 5.0,
  "half_open_shape_time_x_channels": [
    2560,
    38
  ],
  "half_open_duration_sec": 5.0,
  "matlab_1based_inclusive_shape_time_x_channels": [
    2561,
    38
  ],
  "matlab_1based_inclusive_duration_sec": 5.001953125,
  "model_candidate_first32_shape_channels_x_time": [
    32,
    2560
  ],
  "model_candidate_first32_resampled_128hz_shape_channels_x_time": [
    32,
    640
  ],
  "model_candidate_first32_resampled_128hz_duration_sec": 5.0
}

```

#### EMG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_01.mat",
  "fs": 2000.0,
  "raw_data_shape": [
    2207651,
    2
  ],
  "begin_raw": 933601.0,
  "end_raw": 943605.0,
  "trial_index_duration_samples": 10004.0,
  "trial_index_duration_sec": 5.002,
  "half_open_shape_time_x_channels": [
    10004,
    2
  ],
  "half_open_duration_sec": 5.002,
  "matlab_1based_inclusive_shape_time_x_channels": [
    10005,
    2
  ],
  "matlab_1based_inclusive_duration_sec": 5.0025
}

```

### Subject 1 - `Dog_18`

- Raw event: `STIM_Dog_18`

- Event index 1-based: `15`

- Valence score / label: `8` / `1`

- Arousal score / label: `1` / `0`

#### EEG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_01.mat",
  "fs": 512.0,
  "raw_data_shape": [
    565159,
    38
  ],
  "begin_raw": 253964.0,
  "end_raw": 256521.0,
  "trial_index_duration_samples": 2557.0,
  "trial_index_duration_sec": 4.994140625,
  "half_open_shape_time_x_channels": [
    2557,
    38
  ],
  "half_open_duration_sec": 4.994140625,
  "matlab_1based_inclusive_shape_time_x_channels": [
    2558,
    38
  ],
  "matlab_1based_inclusive_duration_sec": 4.99609375,
  "model_candidate_first32_shape_channels_x_time": [
    32,
    2557
  ],
  "model_candidate_first32_resampled_128hz_shape_channels_x_time": [
    32,
    640
  ],
  "model_candidate_first32_resampled_128hz_duration_sec": 5.0
}

```

#### EMG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_01.mat",
  "fs": 2000.0,
  "raw_data_shape": [
    2207651,
    2
  ],
  "begin_raw": 992045.0,
  "end_raw": 1002039.0,
  "trial_index_duration_samples": 9994.0,
  "trial_index_duration_sec": 4.997,
  "half_open_shape_time_x_channels": [
    9994,
    2
  ],
  "half_open_duration_sec": 4.997,
  "matlab_1based_inclusive_shape_time_x_channels": [
    9995,
    2
  ],
  "matlab_1based_inclusive_duration_sec": 4.9975
}

```

### Subject 1 - `Miserable_pose_3`

- Raw event: `STIM_Miserable_pose_3`

- Event index 1-based: `18`

- Valence score / label: `1` / `0`

- Arousal score / label: `5` / `None`

#### EEG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_01.mat",
  "fs": 512.0,
  "raw_data_shape": [
    565159,
    38
  ],
  "begin_raw": 264561.0,
  "end_raw": 267118.0,
  "trial_index_duration_samples": 2557.0,
  "trial_index_duration_sec": 4.994140625,
  "half_open_shape_time_x_channels": [
    2557,
    38
  ],
  "half_open_duration_sec": 4.994140625,
  "matlab_1based_inclusive_shape_time_x_channels": [
    2558,
    38
  ],
  "matlab_1based_inclusive_duration_sec": 4.99609375,
  "model_candidate_first32_shape_channels_x_time": [
    32,
    2557
  ],
  "model_candidate_first32_resampled_128hz_shape_channels_x_time": [
    32,
    640
  ],
  "model_candidate_first32_resampled_128hz_duration_sec": 5.0
}

```

#### EMG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_01.mat",
  "fs": 2000.0,
  "raw_data_shape": [
    2207651,
    2
  ],
  "begin_raw": 1033439.0,
  "end_raw": 1043431.0,
  "trial_index_duration_samples": 9992.0,
  "trial_index_duration_sec": 4.996,
  "half_open_shape_time_x_channels": [
    9992,
    2
  ],
  "half_open_duration_sec": 4.996,
  "matlab_1based_inclusive_shape_time_x_channels": [
    9993,
    2
  ],
  "matlab_1based_inclusive_duration_sec": 4.9965
}

```

### Subject 1 - `Pinecone_1`

- Raw event: `STIM_Pinecone_1`

- Event index 1-based: `21`

- Valence score / label: `5` / `None`

- Arousal score / label: `3` / `0`

#### EEG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_01.mat",
  "fs": 512.0,
  "raw_data_shape": [
    565159,
    38
  ],
  "begin_raw": 276235.0,
  "end_raw": 278795.0,
  "trial_index_duration_samples": 2560.0,
  "trial_index_duration_sec": 5.0,
  "half_open_shape_time_x_channels": [
    2560,
    38
  ],
  "half_open_duration_sec": 5.0,
  "matlab_1based_inclusive_shape_time_x_channels": [
    2561,
    38
  ],
  "matlab_1based_inclusive_duration_sec": 5.001953125,
  "model_candidate_first32_shape_channels_x_time": [
    32,
    2560
  ],
  "model_candidate_first32_resampled_128hz_shape_channels_x_time": [
    32,
    640
  ],
  "model_candidate_first32_resampled_128hz_duration_sec": 5.0
}

```

#### EMG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_01.mat",
  "fs": 2000.0,
  "raw_data_shape": [
    2207651,
    2
  ],
  "begin_raw": 1079041.0,
  "end_raw": 1089043.0,
  "trial_index_duration_samples": 10002.0,
  "trial_index_duration_sec": 5.001,
  "half_open_shape_time_x_channels": [
    10002,
    2
  ],
  "half_open_duration_sec": 5.001,
  "matlab_1based_inclusive_shape_time_x_channels": [
    10003,
    2
  ],
  "matlab_1based_inclusive_duration_sec": 5.0015
}

```

### Subject 1 - `Garbage_dump_6`

- Raw event: `STIM_Garbage_dump_6`

- Event index 1-based: `24`

- Valence score / label: `2` / `0`

- Arousal score / label: `7` / `1`

#### EEG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_01.mat",
  "fs": 512.0,
  "raw_data_shape": [
    565159,
    38
  ],
  "begin_raw": 287363.0,
  "end_raw": 289922.0,
  "trial_index_duration_samples": 2559.0,
  "trial_index_duration_sec": 4.998046875,
  "half_open_shape_time_x_channels": [
    2559,
    38
  ],
  "half_open_duration_sec": 4.998046875,
  "matlab_1based_inclusive_shape_time_x_channels": [
    2560,
    38
  ],
  "matlab_1based_inclusive_duration_sec": 5.0,
  "model_candidate_first32_shape_channels_x_time": [
    32,
    2559
  ],
  "model_candidate_first32_resampled_128hz_shape_channels_x_time": [
    32,
    640
  ],
  "model_candidate_first32_resampled_128hz_duration_sec": 5.0
}

```

#### EMG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_01.mat",
  "fs": 2000.0,
  "raw_data_shape": [
    2207651,
    2
  ],
  "begin_raw": 1122509.0,
  "end_raw": 1132509.0,
  "trial_index_duration_samples": 10000.0,
  "trial_index_duration_sec": 5.0,
  "half_open_shape_time_x_channels": [
    10000,
    2
  ],
  "half_open_duration_sec": 5.0,
  "matlab_1based_inclusive_shape_time_x_channels": [
    10001,
    2
  ],
  "matlab_1based_inclusive_duration_sec": 5.0005
}

```

### Subject 1 - `Depressed_pose_4`

- Raw event: `STIM_Depressed_pose_4`

- Event index 1-based: `27`

- Valence score / label: `4` / `0`

- Arousal score / label: `3` / `0`

#### EEG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EEG/sbj_P_01.mat",
  "fs": 512.0,
  "raw_data_shape": [
    565159,
    38
  ],
  "begin_raw": 296904.0,
  "end_raw": 299459.0,
  "trial_index_duration_samples": 2555.0,
  "trial_index_duration_sec": 4.990234375,
  "half_open_shape_time_x_channels": [
    2555,
    38
  ],
  "half_open_duration_sec": 4.990234375,
  "matlab_1based_inclusive_shape_time_x_channels": [
    2556,
    38
  ],
  "matlab_1based_inclusive_duration_sec": 4.9921875,
  "model_candidate_first32_shape_channels_x_time": [
    32,
    2555
  ],
  "model_candidate_first32_resampled_128hz_shape_channels_x_time": [
    32,
    639
  ],
  "model_candidate_first32_resampled_128hz_duration_sec": 4.9921875
}

```

#### EMG

```json

{
  "file": "/mnt/HDD/AliWorks/I-DARE/raw_downloads/EMG/sbj_P_01.mat",
  "fs": 2000.0,
  "raw_data_shape": [
    2207651,
    2
  ],
  "begin_raw": 1159777.0,
  "end_raw": 1169761.0,
  "trial_index_duration_samples": 9984.0,
  "trial_index_duration_sec": 4.992,
  "half_open_shape_time_x_channels": [
    9984,
    2
  ],
  "half_open_duration_sec": 4.992,
  "matlab_1based_inclusive_shape_time_x_channels": [
    9985,
    2
  ],
  "matlab_1based_inclusive_duration_sec": 4.9925
}

```

## Issues

- None.

## Warnings

- None.

## Next Step

- If this smoke test passes, implement reusable I-DARE window extraction / dataset loader code.

- The first model-facing EEG input candidate is 32 channels × 640 samples after 512Hz to 128Hz resampling.

- EMG should remain feature-level in the main protocol, so the next loader step should compute window-level EMG features rather than pass raw EMG to the main model.



# FILE: docs/idare_window_extraction_status.md


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



# FILE: docs/handoff_delta_after_idare_acquisition.md


# Handoff Delta - After Verified I-DARE Acquisition

Use this file as a compact addendum if the full handoff bundle has not yet been regenerated.

## New Completed Work

I-DARE first-stage acquisition is complete.

Downloaded files:

```text
133
```

Downloaded local root:

```text
/mnt/HDD/AliWorks/I-DARE
```

Downloaded subset:

```text
EEG files
EMG files
label CSV files
metadata CSV files
```

Verification result:

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

## Files to Commit

```text
docs/idare_acquisition_status.md
docs/idare_download_report.md
docs/project_state.md
docs/chat_handoff_latest.md
```

The handoff bundle should be regenerated after these files are added locally.

## Immediate Next Step

Create and run:

```text
scripts/01_audit_datasets.py
```

First audit target:

```text
I-DARE
```

Expected audit report:

```text
docs/data_audit_idare.md
```

DEAP acquisition is still pending.



# FILE: docs/handoff_delta_after_trial_index_probe.md


# Handoff Delta — After I-DARE Trial Index Probe

## New Completed Work

The I-DARE trial/event alignment was probed using:

```text
scripts/05_probe_idare_trial_index.py
```

Generated outputs:

```text
docs/idare_trial_index_probe.md
docs/idare_trial_index_probe.json
```

## Main Findings

The probe confirmed:

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

For each sampled subject:

```text
stim_rows_count: 32
labeled_stim_rows_count: 32
all_labeled_stim_eeg_4p5_to_5p5: true
all_labeled_stim_emg_4p5_to_5p5: true
```

## I-DARE Loader Design Decision

Use only `STIM_*` rows as emotional trials.

Do not use `BSL_*` or `SAM_*` rows as emotion-classification samples.

Map labels by stripping the `STIM_` prefix:

```text
STIM_3053 -> 3053
STIM_Dog_18 -> Dog_18
```

Use the row order in `Stimuli_Specifications.csv` as the event order for `event_begin` and `event_end`.

## Current Candidate Loader Design

1. Load `.mat` files with `h5py`.
2. Use raw `h5py` data orientation:
   - EEG: `time x channels`
   - EMG: `time x channels`
3. Use the 63 common EEG+EMG subjects for the main protocol.
4. For each subject:
   - read EEG file,
   - read EMG file,
   - read `Stimuli_Specifications.csv`,
   - keep only `STIM_*` rows,
   - extract matching EEG and EMG event windows,
   - attach valence and arousal scores from label CSV files.
5. Apply binary label rule:
   - score > 5 -> 1
   - score < 5 -> 0
   - score == 5 -> discard for that specific task
6. EEG will later be resampled from 512Hz to 128Hz.
7. EMG will be converted to feature-level descriptors.

## Immediate Next Step

Commit the probe scripts/reports and decision update, then update the handoff bundle.

After that, begin implementing the actual I-DARE trial index builder / dataset loader.

Do not start model training yet.



# FILE: docs/handoff_delta_after_trial_index_builder.md


# Handoff Delta - After I-DARE Trial Index Builder

## What Changed

A reproducible I-DARE trial index builder was created and successfully executed.

New script:

```text
scripts/06_build_idare_trial_index.py
```

New documentation outputs:

```text
docs/idare_trial_index_summary.md
docs/idare_trial_index_summary.json
```

Generated local cache output:

```text
.cache/idare_trial_index.csv
```

Note:

```text
.cache/ is gitignored, so .cache/idare_trial_index.csv is not committed.
It can be regenerated from the script.
```

## Trial Index Result

The trial index creation passed with no issues and no warnings.

Core result:

```text
n_rows: 2016
n_subjects: 63
expected_subjects: 63
expected_rows: 2016
trials_per_subject_min: 32
trials_per_subject_max: 32
unique_stimuli: 32
issues: 0
warnings: 0
```

This means the index contains:

```text
63 common EEG+EMG subjects × 32 emotional STIM trials = 2016 rows
```

## Label Result

Valence:

```text
total rows: 2016
score == 5 discard rows: 349
rows after discard: 1667
binary label 0 count: 812
binary label 1 count: 855
```

Arousal:

```text
total rows: 2016
score == 5 discard rows: 217
rows after discard: 1799
binary label 0 count: 1112
binary label 1 count: 687
```

## Duration Check

EEG:

```text
min duration: 4.982421875 s
max duration: 5.064453125 s
mean duration: 4.994547526041667 s
all trials in 4.5s to 5.5s range: true
```

EMG:

```text
min duration: 4.985 s
max duration: 5.067 s
mean duration: 4.996669642857143 s
all trials in 4.5s to 5.5s range: true
```

## Loader Assumptions Confirmed

- Use only `STIM_*` rows as emotional trials.
- Strip the `STIM_` prefix to match labels.
- Use the 63 common EEG+EMG subjects.
- Use `score > 5` as positive class.
- Mark `score == 5` as discard separately for valence and arousal.
- Preserve raw event begin/end values in the trial index.
- Final Python slicing convention should be finalized during window extraction.

## Immediate Next Step

Do not start training yet.

Next practical step:

```text
Create a small I-DARE window extraction smoke test.
```

Suggested next script:

```text
scripts/07_smoke_idare_window_extraction.py
```

The smoke test should:
1. Load `.cache/idare_trial_index.csv`.
2. Pick a few rows from subject 1.
3. Read EEG and EMG `.mat` files with `h5py`.
4. Extract the indexed 5-second EEG/EMG segment.
5. Confirm shapes and durations.
6. Decide final sample slicing convention.
7. Optionally resample EEG 512Hz to 128Hz for model compatibility.
8. Generate a report:
   - `docs/idare_window_extraction_smoke_test.md`
   - `docs/idare_window_extraction_smoke_test.json`

Still do not train models until the window extraction smoke test is clean.



# FILE: docs/handoff_delta_after_window_smoke_test.md


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



# FILE: docs/project_state_delta_after_trial_index_probe.md


# Project State Delta — I-DARE Trial Index Probe

## Add to Completed

- I-DARE HDF5 and mat73 structure probes were generated:
  - `scripts/02_probe_idare_hdf5_structure.py`
  - `docs/idare_hdf5_structure_probe.md`
  - `docs/idare_hdf5_structure_probe.json`
  - `scripts/03_probe_idare_mat73_loader.py`
  - `docs/idare_mat73_probe.md`
  - `docs/idare_mat73_probe.json`
- I-DARE MATLAB reference/event probe was generated:
  - `scripts/04_probe_idare_refs_and_events.py`
  - `docs/idare_refs_and_events_probe.md`
  - `docs/idare_refs_and_events_probe.json`
- I-DARE trial index probe was generated:
  - `scripts/05_probe_idare_trial_index.py`
  - `docs/idare_trial_index_probe.md`
  - `docs/idare_trial_index_probe.json`
- I-DARE trial/event alignment was confirmed for sample subjects 1, 2, and 3.
- I-DARE loader design was clarified:
  - use `STIM_*` rows only,
  - strip `STIM_` prefix for label matching,
  - use `Stimuli_Specifications.csv` row order as event order,
  - load `.mat` data with `h5py`,
  - treat raw data orientation as `time x channels`.

## Update In Progress

- Preparing I-DARE dataset loader / trial index builder.
- DEAP acquisition is still pending.

## Update Next Steps

1. Commit I-DARE probe scripts and reports.
2. Add D005 to `docs/decision_log.md`.
3. Refresh `docs/handoff_bundle_latest.md`.
4. Implement an I-DARE trial index builder.
5. Generate a clean machine-readable I-DARE trial index table.
6. Continue DEAP access/download process.



# FILE: docs/project_state_delta_after_trial_index_builder.md


# Project State Delta - After I-DARE Trial Index Builder

## Add to Completed

- I-DARE trial index builder created:
  - `scripts/06_build_idare_trial_index.py`
- I-DARE trial index builder executed successfully.
- I-DARE trial index summary generated:
  - `docs/idare_trial_index_summary.md`
  - `docs/idare_trial_index_summary.json`
- Local regenerable trial index generated:
  - `.cache/idare_trial_index.csv`

## Important Note

`.cache/idare_trial_index.csv` is not tracked by git because `.cache/` is gitignored.

This is acceptable because the file is reproducible from:

```bash
python scripts/06_build_idare_trial_index.py
```

## Trial Index Result

```text
n_rows: 2016
n_subjects: 63
expected_subjects: 63
expected_rows: 2016
trials_per_subject_min: 32
trials_per_subject_max: 32
unique_stimuli: 32
issues: 0
warnings: 0
```

## Label Summary

Valence:

```text
score == 5 discard rows: 349
rows after discard: 1667
binary label 0 count: 812
binary label 1 count: 855
```

Arousal:

```text
score == 5 discard rows: 217
rows after discard: 1799
binary label 0 count: 1112
binary label 1 count: 687
```

## Update Current Goal

Finish the I-DARE loader path by validating real 5-second signal extraction from `.mat` files using the trial index.

## Update In Progress

- Preparing I-DARE window extraction smoke test.
- Next practical step:
  - create `scripts/07_smoke_idare_window_extraction.py`
  - generate `docs/idare_window_extraction_smoke_test.md`
  - generate `docs/idare_window_extraction_smoke_test.json`

## Update Next Steps

1. Commit current trial-index builder files:
   - `requirements.txt`
   - `scripts/06_build_idare_trial_index.py`
   - `docs/idare_trial_index_summary.md`
   - `docs/idare_trial_index_summary.json`
2. Commit this documentation delta.
3. Create I-DARE window extraction smoke test.
4. Validate exact sample slicing convention.
5. Validate EEG shape and EMG shape for extracted 5-second windows.
6. Decide whether to resample I-DARE EEG from 512Hz to 128Hz before the first model input.
7. Only after this, implement the reusable I-DARE dataset/loader code.



# FILE: docs/project_state_delta_after_window_smoke_test.md


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



# FILE: experiments/registry.csv


run_id,date,dataset,task,split,model,config,status,main_metric,notes,commit_hash
R001,2026-05-04,DEAP,valence,LOSO,EEGSegmentClassifier-v1,configs/deap_eeg_segment_v1.yaml,planned,,First EEG-only DEAP run,
