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
