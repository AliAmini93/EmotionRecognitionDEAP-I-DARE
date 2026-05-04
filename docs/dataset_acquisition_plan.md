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
