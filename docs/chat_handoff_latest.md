# Chat Handoff - Latest

## Project
Cross-subject EEG-EMG emotion recognition on DEAP and I-DARE.

## Main Goal
Evaluate whether auxiliary EMG and trial-aware temporal modeling improve cross-subject EEG emotion recognition.

## Current Design
- Main datasets: DEAP and I-DARE.
- Tasks: binary valence and binary arousal.
- Evaluation: strict LOSO.
- Main window: 5 seconds, no overlap.
- DEAP: 12 windows per 60s trial.
- I-DARE: 1 natural 5s stimulus window unless subwindowing is later added.
- Current paper version does not include cross-dataset transfer.

## Current Model Plan
- EEGSegmentEncoder
- EEGSegmentClassifier
- OldStyleEEGClassifier
- Later:
  - EMG feature-level branch
  - EEG sequence encoder
  - EMG sequence encoder
  - segment-level fusion vs trial-level fusion

## Current Code Status
- Repository scaffold exists locally and has been pushed to GitHub.
- Three EEG model files are added under `src/emotion_deap_idare/models/`.
- Virtual environment is created.
- PyTorch CUDA 12.8 is installed.
- GPU smoke test passed on NVIDIA GeForce RTX 5090.
- EEGSegmentClassifier-v1 lite has 337,955 trainable parameters.
- Working proposal V1.1 is stored at `docs/proposal_v1_1.md`.
- Complete handoff bundle is stored at `docs/handoff_bundle_latest.md`.
- Repository was pushed successfully and is expected to be synced with `origin/main` at the time of handoff.
- To verify the latest commit, run `git status` and `git log --oneline -5`.

## Immediate Next Step
Begin Milestone 1: dataset acquisition and audit preparation.

Before writing training code or starting any experiment:
1. Confirm dataset storage location.
2. Decide the exact DEAP version.
3. Decide the exact I-DARE files/release.
4. Confirm access/permissions.
5. Download datasets.
6. Create dataset audit script and audit reports.

## Critical Decisions
- Dataset files are not tracked by git.
- configs/paths.local.yaml is gitignored.
- EMG main branch will be feature-level, not raw waveform.
- Fusion location is an experimental question:
  - segment-level fusion
  - modality-specific sequence encoding + trial-level fusion
- Contrastive learning is reserved for later ablation.

## Important Local Paths
- Project root: /mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE
- DEAP root: /mnt/HDD/AliWorks/DEAP
- I-DARE root: /mnt/HDD/AliWorks/I-DARE
