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

<!-- BEGIN EEG_CACHE_RECIPE_STABILIZATION_HANDOFF_2026_05_05 -->
## Current Next-Chat Prompt Addendum

Continue the `EmotionRecognitionDEAP-I-DARE` project from the current repository state.

Latest known commit after EEG cache recipe stabilization summary:

```text
7586c99 docs: summarize EEG cache recipe stabilization phase
```

Before proposing any new experiment, training recipe, or script, first verify that project context files were read.

Important context files to inspect:

```bash
git status --short
git log --oneline -10

sed -n '1,260p' docs/new_chat_start_protocol.md
sed -n '1,260p' docs/project_state.md
sed -n '1,260p' docs/chat_handoff_latest.md
sed -n '1,260p' docs/next_chat_prompt.md
sed -n '1,320p' docs/idare_eeg_cache_recipe_stabilization_summary.md
sed -n '1,260p' docs/idare_eeg_cache_recipe_stabilization_status.md
```

Facts the next assistant must preserve:

1. The project is smoke-first.
2. Do not run a full LOSO/final/full experiment yet.
3. Do not load raw MATLAB/HDF5 `.mat` files inside training loops.
4. Use EEG cache only:
   - `.cache/idare_eeg_windows_32x640_float32.npy`
   - `.cache/idare_eeg_cache_index.csv`
5. Cache shape is `[2016, 32, 640]`.
6. Current main label policy is `midpoint_as_high`.
7. `discard_midpoint` remains a documented secondary sanity/ablation candidate, not the main policy.
8. The current main phase is cache-based EEG training-recipe stabilization / closeout.

Current stabilization findings:

- Arousal is more promising than valence.
- Arousal's best current diagnostic direction is `balanced_sampler_ce` plus threshold diagnostics.
- Valence remains unstable with fold-sensitive learned boundary behavior near `0.50`.
- Valence `lr=3e-4` fold 2 drifted mostly to class 1.
- Valence `lr=1e-4` fold 2 drifted mostly to class 0.
- `ce_label_smoothing_0p05` is non-promising and should not be expanded.
- Threshold diagnostics are useful but are not a final evaluation policy.

Recommended next action:

- Prefer closing handoff/project-state docs.
- If doing one more technical item, add per-class train/validation recall aggregate diagnostics to script 20.
- Any next technical change must be tested first with a tiny smoke command such as:

```bash
--max-runs 2 --epochs 2
```

Do not provide a full-run command until a relevant smoke test passes and the output is reviewed.
<!-- END EEG_CACHE_RECIPE_STABILIZATION_HANDOFF_2026_05_05 -->
