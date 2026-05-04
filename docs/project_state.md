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

## In Progress
- Preparing first clean repository commit.

## Next Steps
1. Run `scripts/00_audit_local_setup.py`.
2. Add proposal V1.1 markdown to docs.
3. Commit scaffold and model files to GitHub.
4. Start dataset acquisition and audit.

## Current Open Questions
- /mnt/HDD is not a separate mount; confirm whether this is acceptable before downloading datasets.
- DEAP and I-DARE are not downloaded yet.
- Exact DEAP file format after download still needs auditing.
- Exact I-DARE processed folder structure still needs auditing.

## Last Updated
2026-05-04
