# Project State

## Current Phase

Milestone 1 - Dataset acquisition and audit preparation.

## Current Goal

Audit the downloaded I-DARE first-stage files and continue DEAP acquisition.

No training should be started before dataset audit reports are generated.

---

## Completed

- Git installed.
- GitHub repository cloned locally.
- SSH authentication with GitHub works.
- Empty local dataset folders created:
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
- Complete handoff bundle added:
  - `docs/handoff_bundle_latest.md`
- Dataset acquisition plan added:
  - `docs/dataset_acquisition_plan.md`

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

I-DARE manifest result:

```text
Total listed files: 263
First-stage files: 133
Main-protocol files: 132
First-stage total size: 6.88 GB
Main-protocol total size: 6.85 GB
```

Checksum metadata was added to the manifest:

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
docs/idare_acquisition_status.md
docs/idare_download_report.md
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

## Current Git Status at Last Check

Repository was pushed successfully and is expected to be synced with `origin/main` at the time of handoff.

To verify the latest commit, run:

```bash
git status
git log --oneline -5
```

Latest known pushed commit before this update:

```text
e2f4c6e scripts: add I-DARE downloader dry run
```

After committing this update, the latest commit will change.

---

## In Progress

- Preparing Milestone 1: dataset acquisition and dataset audit.
- I-DARE acquisition is complete.
- Next practical step:
  - create `scripts/01_audit_datasets.py`
  - audit I-DARE downloaded files
  - generate `docs/data_audit_idare.md`

---

## Next Steps

1. Add/update the I-DARE acquisition status docs.
2. Commit the final I-DARE acquisition verification report:
   - `docs/idare_download_report.md`
3. Create:
   - `scripts/01_audit_datasets.py`
4. Audit I-DARE downloaded files and generate:
   - `docs/data_audit_idare.md`
5. Confirm or request official DEAP access credentials.
6. Download DEAP preprocessed Python archive:
   - `Data_preprocessed_python.zip`
7. Extend the audit script for DEAP and generate:
   - `docs/data_audit_deap.md`

---

## Current Open Questions

- Are official DEAP access credentials ready?
- Has `Data_preprocessed_python.zip` been downloaded from the official DEAP source?
- What are the exact I-DARE `.mat` field shapes, sampling rates, channel names, and event structures after audit?

---

## Last Updated

2026-05-04
