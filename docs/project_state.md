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
- Latest pushed commit:
  - c65fb1b docs: add working proposal and complete handoff bundle

## In Progress
- Preparing Milestone 1: dataset acquisition and dataset audit.

## Next Steps
1. Confirm whether `/mnt/HDD` on the root filesystem with around 500GB free space is acceptable for dataset storage.
2. Decide the exact DEAP version to download.
   - Current likely starting choice: DEAP preprocessed 128Hz version.
   - This is not yet confirmed.
3. Decide the exact I-DARE release/files to download.
4. Confirm dataset access/permissions for DEAP and I-DARE.
5. Download datasets into:
   - /mnt/HDD/AliWorks/DEAP
   - /mnt/HDD/AliWorks/I-DARE
6. Create `scripts/01_audit_datasets.py`.
7. Generate:
   - docs/data_audit_deap.md
   - docs/data_audit_idare.md

## Current Open Questions
- Is using `/mnt/HDD` acceptable even though it is not a separate mount?
- Should DEAP start from the preprocessed 128Hz version?
- What exact I-DARE release/files are available?
- Are DEAP and I-DARE download permissions/access already ready?

## Last Updated
2026-05-04
