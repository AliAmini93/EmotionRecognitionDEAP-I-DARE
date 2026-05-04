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
134 files
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
