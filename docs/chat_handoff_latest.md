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

## Current Data Source Status
- DEAP has not been downloaded yet.
- DEAP target version: official preprocessed Python version, 128Hz.
- I-DARE has not been downloaded yet.
- I-DARE Figshare source listing has been completed.
- I-DARE listing files:
  - scripts/list_idare_figshare_files.py
  - docs/data_sources_idare.md
  - docs/data_sources_idare.json
  - docs/data_sources_idare_summary.txt
- I-DARE listing result:
  - Articles discovered: 5
  - Files discovered: 263
  - Total listed size: 6.98 GB
  - First-stage required files: 134
  - First-stage required size: 6.88 GB
  - EEG subjects: 63
  - EMG subjects: 64
  - Common EEG+EMG subjects: 63
  - EMG-only subject: 4
- Main I-DARE decision:
  - Use the 63 common EEG+EMG subjects for main experiments.
  - Exclude subject 4 from the main EEG+EMG protocol.
- Next practical step:
  - Build `docs/idare_download_manifest.csv`.

## Current Code Status
- Repository scaffold exists locally and has been pushed to GitHub.
- Three EEG model files are added under `src/emotion_deap_idare/models/`.
- Virtual environment is created.
- PyTorch CUDA 12.8 is installed.
- GPU smoke test passed on NVIDIA GeForce RTX 5090.
- EEGSegmentClassifier-v1 lite has 337,955 trainable parameters.
- Working proposal V1.1 is stored at `docs/proposal_v1_1.md`.
- Dataset acquisition plan is stored at `docs/dataset_acquisition_plan.md`.
- Complete handoff bundle is stored at `docs/handoff_bundle_latest.md`.
- Repository was pushed successfully and is expected to be synced with `origin/main` at the time of handoff.
- To verify the latest commit, run `git status` and `git log --oneline -5`.

## Immediate Next Step
Build and review `docs/idare_download_manifest.csv` before downloading I-DARE files.

Current Milestone 1 status:
- Storage location accepted for the initial phase.
- DEAP target version accepted: official preprocessed Python version, 128Hz.
- I-DARE Figshare source listing completed.
- Main I-DARE subject set decided: 63 common EEG+EMG subjects.
- Subject 4 is excluded from the main EEG+EMG protocol.

Do not start training yet.
Do not implement EMG fusion or sequence modeling yet.
Next practical step is the I-DARE download manifest.

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
