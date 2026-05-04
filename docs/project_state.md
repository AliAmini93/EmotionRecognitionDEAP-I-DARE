# Project State

## Current Phase
Milestone 1 - Dataset acquisition and audit preparation.

## Current Goal
Decide the exact DEAP and I-DARE dataset versions/files to download, then audit their structure before any training.

## Completed
- Git installed.
- GitHub repository cloned locally.
- SSH authentication with GitHub works.
- Empty local dataset folders created:
  - /mnt/HDD/AliWorks/DEAP
  - /mnt/HDD/AliWorks/I-DARE
- Python version checked: 3.12.3.
- Project scaffold created.
- Virtual environment created at `.venv`.
- PyTorch installed with CUDA 12.8 support.
- GPU detected successfully:
  - NVIDIA GeForce RTX 5090
- Three EEG model files added:
  - eeg_segment_encoder.py
  - eeg_segment_classifier.py
  - old_style_eeg_classifier.py
- EEGSegmentClassifier-v1 GPU smoke test passed.
- Model parameter count:
  - EEGSegmentClassifier-v1 lite: 337,955 trainable parameters.
- Working proposal V1.1 added:
  - docs/proposal_v1_1.md
- Complete handoff bundle added:
  - docs/handoff_bundle_latest.md
- Dataset acquisition plan added:
  - docs/dataset_acquisition_plan.md
- I-DARE Figshare source listing completed:
  - scripts/list_idare_figshare_files.py
  - docs/data_sources_idare.md
  - docs/data_sources_idare.json
  - docs/data_sources_idare_summary.txt
- I-DARE source listing result:
  - Articles discovered: 5
  - Files discovered: 263
  - Total listed size: 6.98 GB
  - First-stage required files: 134
  - First-stage required size: 6.88 GB
  - Common EEG+EMG subjects: 63
  - EMG-only subject excluded from main protocol: subject 4
- Repository was pushed successfully and is expected to be synced with `origin/main` at the time of handoff.
- To verify the latest commit, run `git status` and `git log --oneline -5`.

## In Progress
- Preparing Milestone 1: dataset acquisition and dataset audit.
- Next practical step: build `docs/idare_download_manifest.csv` before downloading I-DARE files.

## Next Steps
1. Build `docs/idare_download_manifest.csv` from:
   - docs/data_sources_idare.json
2. Review the I-DARE download manifest before downloading files.
3. Download selected I-DARE first-stage files:
   - EEG files
   - EMG files
   - label CSV files
   - metadata CSV files
4. Confirm or request official DEAP access credentials.
5. Download DEAP preprocessed Python archive:
   - Data_preprocessed_python.zip
6. Create `scripts/01_audit_datasets.py`.
7. Generate:
   - docs/data_audit_deap.md
   - docs/data_audit_idare.md

## Current Open Questions
- Are official DEAP access credentials ready?
- Has `Data_preprocessed_python.zip` been downloaded from the official DEAP source?
- Has the I-DARE download manifest been reviewed and approved?
- Have the selected I-DARE files been downloaded?

## Last Updated
2026-05-04
