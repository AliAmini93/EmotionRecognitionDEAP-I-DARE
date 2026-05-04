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
- Repository scaffold exists locally.
- Three EEG model files are added under `src/emotion_deap_idare/models/`.
- Virtual environment is created.
- PyTorch CUDA 12.8 is installed.
- GPU smoke test passed on NVIDIA GeForce RTX 5090.
- EEGSegmentClassifier-v1 lite has 337,955 trainable parameters.

## Immediate Next Step
Run local setup audit script and commit scaffold/model files.

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
