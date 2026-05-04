# Project State

## Current Phase
Milestone 0 - Project scaffolding and local setup.

## Current Goal
Create a clean local/GitHub-ready project structure before downloading datasets or running experiments.

## Completed
- Git installed.
- GitHub repository cloned locally.
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

## In Progress
- Preparing dataset acquisition and dataset audit.

## Next Steps
1. Commit proposal V1.1 to GitHub.
2. Start dataset acquisition and audit.
3. Create `scripts/01_audit_datasets.py`.
4. Document DEAP and I-DARE file structures after download.

## Current Open Questions
- /mnt/HDD is not a separate mount; confirm whether this is acceptable before downloading datasets.
- DEAP and I-DARE are not downloaded yet.
- Exact DEAP file format after download still needs auditing.
- Exact I-DARE processed folder structure still needs auditing.

## Last Updated
2026-05-04
