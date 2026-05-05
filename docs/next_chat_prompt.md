<!-- NEW_CHAT_START_PROTOCOL_MARKER -->

## New Chat Start Protocol

Before continuing this project in a new chat, follow `docs/new_chat_start_protocol.md`.

Hard rule: every new script/training recipe/experiment runner must start with a smoke test first, such as `--max-runs 2 --epochs 1`, before any full run is proposed.

The new chat must also verify file/context access before claiming it has read project files.

Minimum expected facts:
- Temporary main score-5 policy: `midpoint_as_high`.
- `discard_midpoint` remains a secondary sanity / ablation candidate.
- Main baseline: valence macro F1 `0.3953`, arousal macro F1 `0.4825`.
- Discard-midpoint sanity: valence macro F1 `0.3877`, arousal macro F1 `0.4202`.
- Next technical step: cache-based EEG training-recipe stabilization, smoke-test first.

# Prompt for Continuing This Project in a New Chat

We are continuing the project:

Cross-Subject EEG-EMG Emotion Recognition with Trial-Aware Temporal Modeling on DEAP and I-DARE.

GitHub repo:
https://github.com/AliAmini93/EmotionRecognitionDEAP-I-DARE

Local project root:
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE

Local dataset folders:
/mnt/HDD/AliWorks/DEAP
/mnt/HDD/AliWorks/I-DARE

Important:
The dataset folders currently exist but are empty. DEAP and I-DARE have not been downloaded yet.

Please first read these project memory files:
- docs/project_state.md
- docs/chat_handoff_latest.md
- docs/decision_log.md
- docs/proposal_v1_1.md
- experiments/registry.csv

Current completed status:
- Milestone 0 is completed.
- Proposal V1.1 and the complete handoff bundle have been committed and pushed.
- Repository is expected to be synced with `origin/main` at the time of handoff.
- To verify the latest commit, run `git status` and `git log --oneline -5`.
- Repository scaffold exists and was pushed to GitHub.
- SSH authentication with GitHub works.
- Python virtual environment exists at .venv.
- PyTorch with CUDA 12.8 is installed.
- GPU detected: NVIDIA GeForce RTX 5090.
- EEGSegmentClassifier-v1 was smoke-tested successfully on GPU.
- Smoke test shapes:
  - input: [8, 32, 640]
  - logits: [8, 2]
  - embedding z: [8, 128]
  - projection z_proj: [8, 64]
  - temporal attention: [8, 32, 320]
  - channel attention: [8, 32]
- EEGSegmentClassifier-v1 lite has 337,955 trainable parameters.

Current model files:
- src/emotion_deap_idare/models/eeg_segment_encoder.py
- src/emotion_deap_idare/models/eeg_segment_classifier.py
- src/emotion_deap_idare/models/old_style_eeg_classifier.py

Current proposal file:
- docs/proposal_v1_1.md

Current proposal decisions:
- Main datasets: DEAP and I-DARE.
- Main evaluation: within-dataset cross-subject / strict LOSO.
- Current paper version does not include cross-dataset transfer.
- Main tasks: binary valence and binary arousal.
- Label rule: label = 1 if score > 5 else 0; score == 5 is discarded.
- Main DEAP windowing: 60s trial -> 12 non-overlapping 5s windows.
- Main I-DARE windowing: one natural 5s stimulus window.
- EEG model starts with EEGSegmentClassifier-v1.
- EMG will initially be feature-level, not raw waveform.
- Fusion location is an experimental question:
  1. segment-level EEG-EMG fusion
  2. modality-specific sequence encoding followed by trial-level fusion
- Contrastive learning is a later ablation.
- Contrastive design:
  - positive = same emotion label + different subject
  - hard negative = same stimulus/video + different reported emotion
  - apply contrastive loss at trial-level representation, not raw segment level.

Immediate next step:
Begin Milestone 1 - Dataset acquisition and audit preparation.

Before downloading or coding, clarify:
1. Is /mnt/HDD acceptable even though it is not a separate mount?
2. Should DEAP start from the preprocessed 128Hz version?
3. What exact I-DARE release/files are available?
4. Are dataset access/permissions ready?

Do not jump into training yet. First:
1. Decide exact DEAP version to download.
2. Decide exact I-DARE version/files to download.
3. Download datasets into the local dataset folders.
4. Create scripts/01_audit_datasets.py.
5. Generate:
   - docs/data_audit_deap.md
   - docs/data_audit_idare.md
6. Verify EEG/EMG availability, sampling rates, channel names, labels, and file structures.

Important local issue:
/mnt/HDD is currently not a separate mount. It is on the root filesystem. There is around 500GB free space, but before downloading large datasets, confirm whether this is acceptable.
