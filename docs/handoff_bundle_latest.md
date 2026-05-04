# Handoff Bundle - Latest

This file is a complete project handoff bundle for continuing the project in a new chat.

Generated from local repository files.


## How to Use This File in a New Chat


Copy and paste this whole file into the first message of a new chat and say:

"Please continue the EmotionRecognitionDEAP-I-DARE project from this handoff bundle. First summarize the current state, then continue from the immediate next step. Do not jump into training before dataset acquisition and audit."

---




# FILE: docs/next_chat_prompt.md


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



# FILE: docs/project_state.md


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
1. Confirm whether `/mnt/HDD` on the root filesystem with around 500GB free space is acceptable for dataset storage.
2. Decide the exact DEAP version to download.
   - Current likely starting choice: DEAP preprocessed 128Hz version.
   - This is not yet confirmed.
3. Decide the exact I-DARE release/files to download.
4. Confirm dataset access/permissions for DEAP and I-DARE.
5. Download datasets into:
   - /mnt/HDD/AliWorks/DEAP
   - /mnt/HDD/AliWorks/I-DARE
6. Build `docs/idare_download_manifest.csv`.
7. Review the I-DARE download manifest.
8. Download selected I-DARE files.
9. Create `scripts/01_audit_datasets.py`.
10. Generate:
   - docs/data_audit_deap.md
   - docs/data_audit_idare.md

## Current Open Questions
- Is using `/mnt/HDD` acceptable even though it is not a separate mount?
- Should DEAP start from the preprocessed 128Hz version?
- What exact I-DARE release/files are available?
- Are DEAP and I-DARE download permissions/access already ready?

## Last Updated
2026-05-04



# FILE: docs/chat_handoff_latest.md


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



# FILE: docs/decision_log.md


# Decision Log

## D001 - Use 5-second windows as the main protocol

Date: 2026-05-04

Decision:
Use 5-second non-overlapping windows as the main segmentation strategy.

Reason:
- DEAP 60s trials become 12 windows.
- I-DARE stimulus blocks are naturally 5s.
- Avoids inflated results from overlap in the main protocol.

Status:
Accepted.

---

## D002 - Keep EMG feature-level in the main model

Date: 2026-05-04

Decision:
Use window-level EMG features and a shared MLP instead of a raw EMG branch in the main model.

Reason:
- DEAP and I-DARE have mismatched EMG muscle channels.
- Feature-level harmonization is lower risk.
- Raw EMG can be tested later as an ablation.

Status:
Accepted.

---

## D003 - Treat fusion location as an experimental question

Date: 2026-05-04

Decision:
Do not assume one fusion strategy is best. Compare:
1. Segment-level EEG-EMG fusion.
2. Modality-specific sequence encoding followed by trial-level fusion.

Reason:
- DEAP labels are trial-level.
- EEG and EMG may have different temporal dynamics.
- Fusion location may affect representation quality.

Status:
Accepted.

---

## D004 - Use common EEG+EMG subject set for main I-DARE experiments

Date: 2026-05-04

Decision:
Use the 63 subjects that have both EEG and EMG files for the main I-DARE experiments.

Reason:
The I-DARE Figshare source listing found:
- EEG files: 63 subjects
- EMG files: 64 subjects
- Common EEG+EMG subjects: 63
- EMG-only subjects: [4]

For fair EEG-only, EMG-only, and EEG+EMG comparisons, the main protocol should use the same subject set across all conditions.

Subject 4 has EMG but no EEG, so it should be excluded from the main EEG+EMG protocol. It may be kept only for optional EMG-only secondary analysis.

Status:
Accepted.



# FILE: docs/proposal_v1_1.md


# Working Proposal — Version V1.1

## Provisional Title

**Cross-Subject EEG–EMG Emotion Recognition with Trial-Aware Temporal Modeling: A Controlled Study on DEAP and I-DARE**

---

## Version Scope

This document is the working proposal for the current project stage. It extends the initial EEG-only segment model into a complete experimental plan for:

1. **EEG-only cross-subject baselines**
2. **Feature-level EMG modeling**
3. **Trial-aware temporal modeling**
4. **EEG–EMG fusion at different representation levels**
5. **Affective-response-aware contrastive learning as a later, controlled ablation**

The paper version described here focuses on **within-dataset cross-subject generalization** on DEAP and I-DARE.  
**Cross-dataset transfer between DEAP and I-DARE is intentionally excluded from the current paper version** to keep the experimental story controlled.

---

# 1. Motivation and Research Problem

Cross-subject EEG emotion recognition is difficult because EEG signals vary strongly across individuals. These variations are caused by many factors, including:

- neural and anatomical differences,
- electrode impedance and placement variability,
- fatigue and attention,
- subject-specific emotional response patterns,
- recording noise and physiological artifacts.

In emotion recognition, the label is not simply a property of the stimulus. It is a property of the **subjective affective response**. The same stimulus can evoke different emotional responses in different participants. Therefore, a cross-subject model must generalize across people without erasing the fact that emotional responses are individually variable.

DEAP and I-DARE were selected because both provide EEG and EMG recordings. This makes them suitable for studying whether peripheral muscular activity can complement EEG in emotion recognition.

The core questions are:

1. Does EMG improve EEG-based cross-subject emotion recognition?
2. Does trial-aware temporal modeling improve performance when labels are provided at the trial level?
3. Where should EEG and EMG be fused: at the segment level or after modality-specific trial-level sequence encoding?
4. Can contrastive learning improve generalization if it is designed around affective response rather than stimulus identity?

---

# 2. Main Research Questions

## RQ1 — Contribution of EMG

Does adding EMG as an auxiliary modality improve cross-subject emotion recognition compared with EEG-only models?

## RQ2 — Contribution of Trial-Aware Temporal Modeling

For DEAP, does modeling the sequence of twelve 5-second segments inside each 60-second trial improve performance compared with independent segment-level classification?

## RQ3 — Interaction Between EMG and Sequence Modeling

If temporal sequence encoding is added, does EMG still provide additional value?

## RQ4 — Best Fusion Location

Should EEG and EMG be fused at every 5-second segment, or should each modality first build its own trial-level sequence representation before information fusion?

## RQ5 — Contrastive Learning for Cross-Subject Generalization

Can an affective-response-aware supervised contrastive objective improve cross-subject generalization?

This question is treated as a **later ablation**, not part of the first baseline model. The reason is that contrastive learning can easily be misdesigned in emotion recognition if positive and negative pairs are constructed from stimulus identity alone.

---

# 3. Current Locked Decisions

## 3.1 Datasets

Main datasets:

- **DEAP**
- **I-DARE**

Current evaluation setting:

- **within-dataset cross-subject evaluation**
- strict **LOSO** or subject-held-out evaluation
- no cross-dataset transfer in the current paper version

Dataset storage paths:

```text
DEAP:   /mnt/HDD/AliWorks/DEAP
I-DARE: /mnt/HDD/AliWorks/I-DARE
```

Dataset files must not be committed to Git.

---

## 3.2 Tasks

Main tasks:

- binary valence classification
- binary arousal classification

Label harmonization:

```python
label = 1 if score > 5 else 0
score == 5 -> discard
```

Rationale:

- both DEAP and I-DARE use valence/arousal ratings compatible with a midpoint-based low/high split,
- score 5 is ambiguous and may increase label noise,
- removing midpoint samples gives a cleaner binary task.

The same protocol must be applied consistently across folds.

---

## 3.3 Evaluation Protocol

Main evaluation protocol:

```text
Strict LOSO
```

For each fold:

```text
test_subject = one held-out subject
validation_subjects = subset of remaining training subjects
train_subjects = all other subjects
```

Strict rules:

1. No window, trial, or feature from the test subject may enter training or validation.
2. Normalization statistics must be computed only from training subjects.
3. Early stopping must use validation subjects only.
4. Hyperparameter choices must not be based on test fold results.
5. For DEAP, trial-level and segment-level results must be reported separately.

---

# 4. Windowing Protocol

## 4.1 DEAP

Main windowing:

```text
60s trial -> 12 windows × 5s
stride = 5s
overlap = 0
```

Rationale:

- DEAP provides trial-level labels for 60-second trials.
- 5-second windows create a manageable sequence length of 12.
- No overlap avoids inflated sample counts and reduces the risk of overly correlated training samples.

Ablation options:

```text
4s windows
5s windows
6s windows
50% overlap only as a later ablation
```

The main result should use **5s non-overlapping windows**.

---

## 4.2 I-DARE

Main windowing:

```text
5s stimulus block -> 1 window
```

Rationale:

- I-DARE naturally contains 5-second stimulus blocks.
- Therefore, the main sequence-modeling claim should not be made on I-DARE unless later subwindowing is explicitly introduced.

Possible later ablation:

```text
5s block -> five 1s subwindows
```

This is not part of the main protocol.

---

# 5. EEG Modeling

## 5.1 Current EEG Segment Encoder

The current EEG model is `EEGSegmentClassifier-v1`, which contains:

```text
EEG window [B, C, T]
-> multi-branch temporal stem
-> depthwise/grouped TCN
-> temporal attention pooling
-> channel position embedding
-> channel self-attention
-> channel attention pooling
-> EEG embedding
-> classifier
```

Default input for 5-second windows:

```text
C = 32
sampling_rate = 128 Hz
T = 640
```

Default configuration:

```python
window_sec = 5.0
sampling_rate = 128
modelsize = "lite"
stem_fusion = "concat"
channel_pos_mode = "learnable"
channel_mixer = "mha"
norm_kind = "gn"
use_spectral_branch = False
```

Current smoke-test result:

```text
EEGSegmentClassifier-v1 lite
Input: [8, 32, 640]
Logits: [8, 2]
Embedding: [8, 128]
Projection: [8, 64]
Trainable parameters: 337,955
GPU smoke test: passed on NVIDIA GeForce RTX 5090
```

---

## 5.2 Why the EEG Encoder Was Modified

The previous conference model was designed for continuous valence regression on MAHNOB-HCI. For the current project, the model is adapted for:

- binary classification,
- 4/5/6-second EEG windows,
- modular temporal kernel sizes,
- multi-scale temporal extraction,
- optional spectral features,
- channel position embeddings,
- channel-level attention,
- future sequence modeling.

The goal is to keep the encoder compact but stronger than a plain EEGNet-style baseline.

---

## 5.3 EEG Spectral Branch

The spectral branch is optional and disabled in the main model.

If enabled, spectral features are computed outside the model:

```text
x_spec: [B, C, num_bands]
```

Possible bands:

```text
delta
theta
alpha
beta
gamma
```

Main decision:

```text
use_spectral_branch = False
```

Reason:

- first establish a raw/minimally processed EEG baseline,
- avoid adding too many variables before the first DEAP runs,
- later test raw-only vs raw+spectral as an ablation.

---

# 6. EMG Modeling

## 6.1 Why EMG Requires a Conservative Design

DEAP and I-DARE do not provide perfectly matched EMG channels.

Typical situation:

```text
DEAP:
    zEMG + tEMG

I-DARE:
    zygomaticus + corrugator
```

Only part of the EMG setup is semantically aligned across datasets. A raw waveform EMG branch may overfit to:

- muscle identity,
- amplitude scaling,
- electrode placement,
- recording protocol,
- dataset-specific preprocessing.

Therefore, the main EMG design should not assume strict anatomical equivalence between all EMG channels.

---

## 6.2 Main EMG Decision

Main EMG representation:

```text
feature-level EMG
```

Not main:

```text
raw EMG waveform branch
```

Raw EMG can be added later as an ablation, but the main model should use robust window-level features.

---

## 6.3 EMG Window-Level Features

For each EMG channel and each 5-second window:

```text
1. RMS
2. MAV
3. Waveform Length
4. Zero Crossing Rate
5. Log-energy
6. Mean Frequency
7. Median Frequency
```

Input shape:

```text
x_emg_feat: [B, N_emg, F]
```

Default:

```text
N_emg = 2
F = 7
```

For DEAP:

```text
12 windows per trial -> [B, 12, N_emg, 7]
```

For I-DARE:

```text
1 stimulus window -> [B, 1, N_emg, 7]
```

---

## 6.4 Channel-Shared EMG Encoder

To reduce dependence on channel identity, each EMG channel is passed through the same MLP:

```text
x_emg_feat: [B, N_emg, 7]

shared MLP per channel:
    Linear(7, 32)
    LayerNorm
    GELU
    Dropout
    Linear(32, d_emg)

attention pooling over EMG channels:
    [B, N_emg, d_emg] -> [B, d_emg]
```

Advantages:

- compatible with DEAP and I-DARE,
- low parameter count,
- avoids assuming that DEAP tEMG and I-DARE corrugator are equivalent,
- gives interpretable EMG channel attention scores.

---

## 6.5 EMG-Only Baselines

Required baselines:

```text
E0: EMG-only segment classifier
E1: EMG-only trial attention model
E2: EMG-only tiny TCN sequence model
```

Purpose:

- determine whether EMG has standalone predictive signal,
- determine whether EMG contributes only when fused with EEG,
- prevent overclaiming the value of EMG.

---

# 7. Trial-Aware Sequence Modeling

## 7.1 Why Sequence Modeling Is Needed

DEAP labels are assigned at the trial level. If each 5-second segment is classified independently, each segment receives the trial label even though the emotional response may vary across the trial.

This creates weak supervision:

```text
trial label -> copied to all segments
```

A better approach is:

```text
60s trial
-> 12 windows
-> 12 segment embeddings
-> trial sequence encoder
-> trial-level prediction
```

The final prediction should be trial-level.

---

## 7.2 EEG Sequence Encoder Options

Candidate encoders:

```text
S0: mean pooling
S1: temporal attention pooling
S2: lightweight TCN + attention pooling
S3: BiGRU + attention pooling
S4: lightweight Transformer
S5: Mamba / SSM only if sequence length increases
```

Default candidate:

```text
S2: lightweight TCN + attention pooling
```

Reason:

- DEAP sequence length is only 12,
- TCN has useful temporal inductive bias,
- fewer parameters than BiGRU or Transformer,
- less likely to overfit than self-attention on small EEG datasets.

---

## 7.3 EMG Sequence Encoder Options

Because EMG is low-dimensional and potentially noisy, the EMG sequence encoder should remain small.

Candidate encoders:

```text
M0: temporal attention pooling
M1: tiny TCN + attention pooling
M2: small GRU
```

Default candidate:

```text
M0: temporal attention pooling
```

Ablation:

```text
M1: tiny TCN + attention pooling
```

---

# 8. EEG–EMG Fusion

Fusion is treated as an experimental design axis, not a fixed assumption.

Two competing hypotheses:

```text
H1: EEG and EMG should be fused at every 5-second segment.
H2: EEG and EMG should first build modality-specific trial-level sequence representations, then be fused.
```

---

## 8.1 Segment-Level Fusion

In segment-level fusion, EEG and EMG are fused at each 5-second window:

```text
for each segment t:
    EEG_t -> z_eeg_t
    EMG_t -> z_emg_t
    fuse(z_eeg_t, z_emg_t) -> z_fused_t

DEAP:
    [z_fused_1, ..., z_fused_12]
    -> shared sequence encoder
    -> trial prediction

I-DARE:
    z_fused_1
    -> classifier
```

Advantages:

- simpler,
- fewer parameters,
- directly models simultaneous EEG–EMG information.

Limitations:

- assumes EEG and EMG are temporally aligned in each 5-second window,
- may be less suitable if EMG is delayed or sparse.

---

## 8.2 Modality-Specific Sequence Encoding + Trial-Level Fusion

In trial-level fusion, each modality first builds its own temporal representation:

```text
EEG:
    [EEG_1, ..., EEG_12]
    -> EEG segment encoder
    -> EEG sequence encoder
    -> h_eeg_trial

EMG:
    [EMG_1, ..., EMG_12]
    -> EMG segment encoder
    -> EMG sequence encoder
    -> h_emg_trial

Fusion:
    fuse(h_eeg_trial, h_emg_trial)
    -> classifier
```

Advantages:

- each modality can learn its own dynamics,
- more consistent with DEAP trial-level labels,
- better handles sparse or delayed EMG responses.

Limitations:

- more parameters,
- EMG branch can overfit if the sequence encoder is too large.

---

## 8.3 Fusion Operators

Two operators should be tested:

```text
1. concat + MLP
2. gated fusion
```

Gated fusion:

```text
g = sigmoid(MLP([z_eeg, z_emg]))
z = g * z_eeg + (1 - g) * z_emg
```

For segment-level fusion:

```text
z_eeg = z_eeg_t
z_emg = z_emg_t
```

For trial-level fusion:

```text
z_eeg = h_eeg_trial
z_emg = h_emg_trial
```

Gate diagnostics should be reported:

```text
mean gate value
gate distribution
per-subject gate behavior
gate behavior for valence vs arousal
```

---

# 9. Contrastive Learning Design

## 9.1 Why Contrastive Learning Needs Careful Design

A naive contrastive objective can be harmful in emotion recognition.

Incorrect assumption:

```text
same stimulus -> same emotion
```

This is not always true. A stimulus may evoke different emotional responses in different subjects. Therefore, stimulus identity alone should not define positive pairs.

Correct principle:

```text
contrastive pairs should reflect affective response, not only stimulus identity
```

The goal is not to make all responses to the same video identical.  
The goal is to make representations more consistent across subjects **when the affective label is similar**, while preserving differences when subjects report different emotions.

---

## 9.2 Where to Apply Contrastive Loss

Contrastive loss should be applied to:

```text
trial-level representation
```

Not the raw segment representation.

Reason:

- DEAP labels are trial-level.
- segment labels are weak labels copied from the trial.
- trial-level representation better matches the semantic level of the emotion label.

Possible representations:

```text
EEG-only trial model:
    h_trial

EEG+EMG segment-level fusion model:
    h_fused_trial

EEG+EMG modality-specific sequence model:
    h_fused_trial after EEG/EMG trial-level fusion
```

The contrastive projection head should receive the same representation used by the classifier, or a detached copy depending on the ablation.

---

## 9.3 Projection Head

A small projection head maps trial embeddings to the contrastive space:

```text
h_trial -> projection head -> z_proj
```

Example:

```text
LayerNorm(D)
Linear(D, 128)
GELU
Linear(128, 64)
L2 normalize
```

Output:

```text
z_proj: [B, 64]
```

Classification uses `h_trial`, not necessarily `z_proj`.

---

## 9.4 Main Contrastive Pair Definition

For binary valence or arousal:

```text
positive pair:
    same emotion label
    different subject

negative pair:
    different emotion label
```

This encourages subject-invariant representations for the same affective class.

Important constraint:

```text
positive pairs should preferably come from different subjects
```

Reason:

- same-subject positives may encourage subject-specific clustering,
- the goal is cross-subject generalization.

---

## 9.5 Optional Continuous-Rating Constraint

If continuous scores are retained before binarization, positives can be made stricter:

```text
positive pair:
    same binary label
    different subject
    absolute score difference <= delta
```

Example:

```text
abs(score_i - score_j) <= 1.0
```

This is optional and should be tested only after the simpler label-based SupCon is stable.

---

## 9.6 Hard Negative Definition

A useful hard negative is:

```text
same stimulus/video
different reported emotion label
```

This is important because it prevents the model from collapsing stimulus identity into emotion identity.

Example:

```text
subject A watches video k -> high valence
subject B watches video k -> low valence
```

These two samples should not be pulled together simply because the stimulus is the same.

This can be implemented as:

1. normal supervised contrastive loss with labels,
2. optional hard-negative weighting for same-stimulus/different-label pairs.

---

## 9.7 SupCon Loss

For a batch of projected normalized embeddings:

```text
z_i = normalized projection of sample i
```

Similarity:

```text
sim(i, j) = z_i dot z_j / temperature
```

For each anchor `i`, positives are:

```text
P(i) = {j | y_j == y_i and subject_j != subject_i}
```

Loss:

```text
L_i = - 1 / |P(i)| * sum_{p in P(i)}
      log exp(sim(i,p)) / sum_{a != i} exp(sim(i,a))
```

Total:

```text
L_supcon = mean_i L_i
```

Samples with no valid positives in the batch should be skipped for the contrastive part.

---

## 9.8 Total Training Objective

Baseline:

```text
L_total = L_CE
```

Contrastive ablation:

```text
L_total = L_CE + lambda_contrastive * L_supcon
```

Optional later regularization:

```text
L_total = L_CE + lambda_contrastive * L_supcon + lambda_vrex * L_vrex
```

Default starting values:

```text
temperature = 0.07
lambda_contrastive = 0.1 or 0.3
projection_dim = 64
```

Small grid:

```text
temperature: [0.07, 0.1]
lambda_contrastive: [0.1, 0.3, 0.5]
projection_dim: [64]
```

The grid must remain small to avoid tuning-driven results.

---

## 9.9 Batch Construction for Contrastive Learning

Contrastive learning requires careful batch composition.

A regular random batch may not contain enough cross-subject positive pairs.

Recommended sampler:

```text
subject-balanced label-balanced sampler
```

Batch should ideally contain:

```text
multiple subjects
both emotion classes
at least 2 subjects per class
```

Example for binary classification:

```text
batch_size = 64

32 samples high label
32 samples low label

within each label:
    samples drawn from multiple subjects
```

For DEAP trial-level contrastive learning:

```text
batch item = one trial representation
```

For segment-level training, contrastive should not be activated unless segments are aggregated to trial-level first.

---

## 9.10 Contrastive Learning Ablation Plan

Contrastive learning should not be added before the baseline architecture is stable.

Ablation order:

```text
C0: CE only
C1: CE + SupCon with same-label/different-subject positives
C2: CE + SupCon + continuous-rating constraint
C3: CE + SupCon + hard-negative weighting
C4: CE + SupCon + VREx
```

Minimum required comparison:

```text
C0 vs C1
```

Only if C1 improves or behaves reasonably should C2–C4 be tested.

---

## 9.11 What Contrastive Learning Should Not Do

The contrastive design should not:

1. pull all samples from the same video together,
2. force all subjects to respond identically to the same stimulus,
3. use test-subject statistics,
4. operate on heavily overlapping windows in the main result,
5. dominate CE loss with a large lambda,
6. be tuned based on test fold performance.

---

## 9.12 Reporting Contrastive Results

For contrastive experiments, report:

```text
Accuracy
Macro-F1
Balanced Accuracy
Per-subject performance
Mean ± std across LOSO folds
Wilcoxon signed-rank test vs CE-only
UMAP/t-SNE before and after SupCon
Subject clustering score if possible
Class separation score if possible
```

Diagnostic question:

```text
Does SupCon reduce subject clustering while preserving emotion separation?
```

This is more important than only showing a small accuracy gain.

---

# 10. Domain Generalization Regularization

VREx or GroupDRO can be tested after baseline and SupCon are stable.

The subject can be treated as the domain:

```text
domain = subject
```

VREx intuition:

```text
encourage similar risk across training subjects
```

Possible objective:

```text
L_total = mean_subject CE_subject + lambda_vrex * variance_subject(CE_subject)
```

This should be a later ablation because:

- it changes training dynamics,
- it depends on subject-balanced batches,
- it may interact with SupCon.

Suggested ablation:

```text
CE
CE + VREx
CE + SupCon
CE + SupCon + VREx
```

---

# 11. Model Variants

## M0 — EEG-Only Segment Baseline

```text
EEG 5s window
-> EEGSegmentClassifier-v1
-> logits
```

Purpose:

- sanity check,
- segment-level baseline,
- first model to run.

---

## M1 — EEG-Only Trial Sequence Model

For DEAP:

```text
60s trial
-> 12 × 5s EEG windows
-> EEGSegmentEncoder per window
-> EEG sequence encoder
-> classifier
```

Purpose:

- test whether trial-aware sequence modeling improves EEG-only performance.

---

## M2 — EMG-Only Segment Model

```text
EMG 5s features
-> channel-shared EMG encoder
-> classifier
```

Purpose:

- measure standalone EMG signal.

---

## M3 — EMG-Only Trial Sequence Model

For DEAP:

```text
12 × 5s EMG feature windows
-> EMG encoder per window
-> EMG temporal attention / tiny TCN
-> classifier
```

Purpose:

- test whether EMG temporal dynamics contain useful information.

---

## M4 — EEG+EMG Segment-Level Fusion

```text
for each 5s window:
    EEG_t -> z_eeg_t
    EMG_t -> z_emg_t
    fuse_t -> z_fused_t

DEAP:
    [z_fused_1, ..., z_fused_12]
    -> sequence encoder
    -> classifier

I-DARE:
    z_fused_1 -> classifier
```

Purpose:

- test early temporal fusion.

---

## M5 — EEG+EMG Modality-Specific Sequence Fusion

For DEAP:

```text
EEG windows -> EEG sequence encoder -> h_eeg_trial
EMG windows -> EMG sequence encoder -> h_emg_trial
fuse(h_eeg_trial, h_emg_trial)
-> classifier
```

Purpose:

- test whether modality-specific temporal dynamics should be learned before fusion.

---

# 12. Experimental Roadmap

## Phase 0 — Local Setup

Completed:

- repository scaffold created,
- virtual environment created,
- PyTorch CUDA installed,
- RTX 5090 verified,
- EEG model files added,
- GPU smoke test passed.

---

## Phase 1 — Dataset Acquisition and Audit

Goals:

1. download DEAP,
2. download I-DARE,
3. inspect file structures,
4. verify EEG and EMG availability,
5. confirm channel names and sampling rates,
6. document dataset versions.

Scripts:

```text
scripts/01_audit_datasets.py
```

Expected outputs:

```text
docs/data_audit_deap.md
docs/data_audit_idare.md
```

---

## Phase 2 — DEAP EEG-Only Segment Baseline

Models:

```text
R0: OldEncoder + classifier
R1: EEGSegmentClassifier-v1
R2: EEGNet / ShallowConvNet
```

Main purpose:

```text
Establish a trustworthy EEG-only baseline before adding EMG or sequence modeling.
```

---

## Phase 3 — DEAP EEG Trial Sequence Modeling

Models:

```text
S0: mean pooling
S1: temporal attention pooling
S2: lightweight TCN + attention pooling
S3: BiGRU + attention pooling
```

Main comparison:

```text
EEG segment-level vs EEG trial-level
```

---

## Phase 4 — EMG Baselines

Models:

```text
E0: EMG-only segment classifier
E1: EMG-only trial attention model
E2: EMG-only tiny TCN sequence model
```

Purpose:

```text
Estimate EMG-only signal quality before EEG–EMG fusion.
```

---

## Phase 5 — EEG+EMG Fusion

Models:

```text
F1: segment-level concat fusion
F2: segment-level gated fusion
F3: modality-specific sequence + concat fusion
F4: modality-specific sequence + gated fusion
```

Key comparison:

```text
F2 vs F4
```

This answers whether fusion is better before or after modality-specific sequence encoding.

---

## Phase 6 — I-DARE Experiments

Models:

```text
I1: EEG-only
I2: EMG-only
I3: EEG+EMG concat
I4: EEG+EMG gated
```

Sequence modeling is not a main claim for I-DARE unless subwindowing is explicitly introduced.

---

## Phase 7 — Contrastive / Regularization Ablations

Only after the best baseline/fusion model is identified:

```text
C0: CE only
C1: CE + SupCon
C2: CE + SupCon + continuous-rating constraint
C3: CE + SupCon + hard-negative weighting
C4: CE + SupCon + VREx
```

---

# 13. Main DEAP Ablation Table

| Code | EEG | EMG | Sequence | Fusion | Purpose |
|---|---:|---:|---:|---|---|
| D1 | Yes | No | No | — | EEG segment baseline |
| D2 | Yes | No | Yes | — | Effect of EEG sequence modeling |
| D3 | No | Yes | No | — | EMG segment baseline |
| D4 | No | Yes | Yes | — | EMG temporal dynamics |
| D5 | Yes | Yes | No | Segment fusion | EMG effect without trial sequence |
| D6 | Yes | Yes | Yes | Segment-level fusion | Fusion before sequence |
| D7 | Yes | Yes | Yes | Trial-level fusion | Fusion after modality-specific sequence encoding |

Key comparisons:

```text
D2 - D1 = effect of sequence modeling on EEG
D5 - D1 = effect of EMG without sequence
D6 - D2 = effect of EMG with shared sequence modeling
D7 - D2 = effect of EMG with modality-specific sequence modeling
D7 vs D6 = better fusion location
```

---

# 14. Main I-DARE Ablation Table

| Code | EEG | EMG | Fusion | Purpose |
|---|---:|---:|---|---|
| I1 | Yes | No | — | EEG baseline |
| I2 | No | Yes | — | EMG baseline |
| I3 | Yes | Yes | concat | Fusion baseline |
| I4 | Yes | Yes | gated | Main I-DARE candidate |

---

# 15. Metrics

For all main runs:

```text
Accuracy
Macro-F1
Balanced Accuracy
Per-subject accuracy
Mean ± std across LOSO folds
95% confidence interval
Wilcoxon signed-rank test for key comparisons
```

For DEAP:

```text
segment-level results and trial-level results must be reported separately
```

The primary DEAP result should be trial-level.

---

# 16. Visualizations

Required visualizations:

```text
1. Confusion matrix
2. Per-subject performance bar plot
3. Temporal attention over 12 DEAP segments
4. EMG channel attention
5. Fusion gate distribution
6. EEG vs EMG contribution analysis
7. UMAP/t-SNE of embeddings before and after sequence encoding
8. Contrastive embedding visualization if SupCon is used
```

For contrastive learning:

```text
visualize whether subject clustering decreases and emotion clustering improves
```

---

# 17. Repository and Project Memory

The project must maintain code and memory separately.

Key project memory files:

```text
docs/project_state.md
docs/chat_handoff_latest.md
docs/decision_log.md
experiments/registry.csv
```

Purpose:

- enable continuation across multiple chat sessions,
- prevent loss of design decisions,
- track experiments and results,
- keep the project reproducible.

End-of-session routine:

```text
1. Update docs/project_state.md
2. Update docs/chat_handoff_latest.md
3. Update docs/decision_log.md if a new decision was made
4. Update experiments/registry.csv if any run was executed
5. Commit and push
```

---

# 18. Suggested Defaults for the Next Implementation Stage

## EEG Segment Encoder

```python
window_sec = 5.0
sampling_rate = 128
modelsize = "lite"
stem_fusion = "concat"
channel_pos_mode = "learnable"
channel_mixer = "mha"
norm_kind = "gn"
use_spectral_branch = False
```

## EEG Sequence Encoder

```text
lightweight TCN + temporal attention pooling
```

## EMG Encoder

```text
channel-shared feature MLP + EMG channel attention pooling
```

## EMG Sequence Encoder

```text
temporal attention pooling
```

## Fusion

Initial baseline:

```text
concat + MLP
```

Main candidate:

```text
gated fusion
```

## Contrastive Learning

Initial ablation only:

```text
CE + SupCon
positive = same label + different subject
temperature = 0.07
lambda_contrastive = 0.1 or 0.3
projection_dim = 64
```

---

# 19. Summary of Version V1.1

V1.1 defines a controlled study of cross-subject EEG–EMG emotion recognition on DEAP and I-DARE.

The main methodological contributions under investigation are:

1. a compact EEG segment encoder adapted from the previous conference model,
2. feature-level EMG modeling to handle EMG mismatch between datasets,
3. trial-aware temporal modeling for DEAP,
4. comparison of segment-level fusion versus modality-specific trial-level fusion,
5. carefully designed affective-response-aware contrastive learning as a later ablation.

The key principle of this proposal is controlled progression:

```text
EEG-only baseline
-> EEG trial sequence
-> EMG-only baseline
-> EEG+EMG fusion
-> contrastive / regularization ablation
```

This prevents blindly combining many ideas before knowing which inductive biases actually help.



# FILE: docs/dataset_acquisition_plan.md


# Dataset Acquisition Plan

## Project

**Cross-Subject EEG–EMG Emotion Recognition with Trial-Aware Temporal Modeling on DEAP and I-DARE**

This document defines the dataset acquisition and audit plan for **Milestone 1**.

The goal of Milestone 1 is not training. The goal is to obtain the correct dataset files, inspect their structure, verify EEG/EMG availability, and document all assumptions before writing loaders or running experiments.

---

## Current Status

Local project root:

```text
/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE
```

Local dataset folders:

```text
/mnt/HDD/AliWorks/DEAP
/mnt/HDD/AliWorks/I-DARE
```

Current state:

```text
DEAP folder: exists but empty
I-DARE folder: exists but empty
```

Storage decision:

```text
Use /mnt/HDD/AliWorks/... for the initial phase.
```

Important note:

```text
/mnt/HDD is currently not a separate mount. It is on the root filesystem.
Available free space is about 500GB.
```

This is acceptable for the current phase because we will start from **preprocessed physiological data**, not raw videos or large redundant archives.

---

# 1. Milestone 1 Objective

Milestone 1 is:

```text
Dataset acquisition and audit
```

It has four concrete outputs:

```text
1. DEAP files downloaded and stored locally.
2. I-DARE files downloaded and stored locally.
3. scripts/01_audit_datasets.py created.
4. Audit reports generated:
   - docs/data_audit_deap.md
   - docs/data_audit_idare.md
```

No training should be started before these four outputs exist.

---

# 2. DEAP Acquisition Decision

## 2.1 Selected DEAP Version

For the first implementation stage, use:

```text
DEAP preprocessed Python version
Data_preprocessed_python.zip
```

Do **not** start from raw `.bdf` files.

## 2.2 Rationale

The preprocessed Python version is selected because:

- it is commonly used in DEAP emotion recognition studies,
- it is already downsampled to **128Hz**,
- it avoids raw BioSemi preprocessing at this stage,
- it matches the current model design:
  - 5-second windows,
  - 128Hz sampling rate,
  - 640 samples per window,
- it includes EEG and peripheral channels, including EMG.

## 2.3 Expected File

Expected official archive:

```text
Data_preprocessed_python.zip
```

Expected local destination:

```text
/mnt/HDD/AliWorks/DEAP/Data_preprocessed_python.zip
```

Expected extraction destination:

```text
/mnt/HDD/AliWorks/DEAP/data_preprocessed_python/
```

The exact extracted folder name should be verified during audit.

---

## 2.4 Expected DEAP Structure

Expected contents after extraction:

```text
s01.dat
s02.dat
...
s32.dat
```

Expected number of participant files:

```text
32
```

Expected content of each `.dat` file:

```text
data
labels
```

Expected shapes:

```text
data   -> [40 trials, 40 channels, 8064 samples]
labels -> [40 trials, 4 labels]
```

Expected label order:

```text
labels[:, 0] = valence
labels[:, 1] = arousal
labels[:, 2] = dominance
labels[:, 3] = liking
```

---

## 2.5 DEAP Channels Needed for This Project

Main EEG channels:

```text
first 32 channels
```

Main EMG channels of interest:

```text
zEMG
tEMG
```

Important implementation note:

DEAP channel indexing must be verified directly from the official channel list and the loaded `.dat` files. The audit script should not silently assume wrong indexing. It must print and document the final EEG/EMG channel indices used by the project.

---

## 2.6 DEAP Windowing Assumption

Main DEAP windowing:

```text
60-second trial -> 12 non-overlapping 5-second windows
```

At 128Hz:

```text
5 seconds = 640 samples
12 windows = 7680 samples
```

Important detail:

DEAP preprocessed data has 8064 samples per trial. The audit must verify how these samples correspond to baseline/stimulus duration in the selected official preprocessed archive.

The implementation should not blindly use all 8064 samples as 60 seconds. The audit should explicitly determine:

```text
- whether the usable stimulus portion is exactly 60s,
- whether baseline samples are included,
- which sample range should be used for the 12 x 5s windows.
```

Until verified, the working assumption is:

```text
Use the 60s stimulus part only for the main 12-window protocol.
```

---

## 2.7 DEAP Label Rule

For binary valence:

```python
valence_label = 1 if valence_score > 5 else 0
valence_score == 5 -> discard
```

For binary arousal:

```python
arousal_label = 1 if arousal_score > 5 else 0
arousal_score == 5 -> discard
```

The audit must report:

```text
- min/max valence score
- min/max arousal score
- number of score == 5 valence trials
- number of score == 5 arousal trials
- class balance after removing score == 5
```

---

## 2.8 DEAP Access Status

Current status:

```text
DEAP has not been downloaded yet.
DEAP access credentials are not confirmed yet.
```

Action required:

```text
Request or confirm access to the official DEAP dataset download server.
```

The project should use the official dataset source, not unofficial mirrors, unless official access fails and a separate decision is recorded.

---

# 3. I-DARE Acquisition Decision

## 3.1 Selected I-DARE Source

Use the official I-DARE Figshare project:

```text
https://figshare.com/projects/I_DARE/186558
```

Current status:

```text
I-DARE has not been downloaded yet.
Exact files/release are not yet listed locally.
```

Action required:

```text
List available Figshare files and sizes before downloading.
```

---

## 3.2 Expected I-DARE Characteristics

Expected high-level dataset properties:

```text
Subjects: 63
Stimuli: 32 emotional images
Modalities: EEG, EMG, SC, PPG, ET
```

Current project uses:

```text
EEG
EMG
SAM labels / ratings
```

Other modalities are not needed for the first paper stage.

---

## 3.3 Expected I-DARE Processed Modality Folders

Expected processed modality folders:

```text
EEG/
EMG/
SC&PPG/
ET/
```

Expected number of processed `.mat` files:

```text
63 files per modality folder
1 file per subject
```

For the current project, required folders are:

```text
EEG/
EMG/
```

Required label files:

```text
Valence_SAM.csv
Arousal_SAM.csv
Quadrants_SAM.csv
```

Potentially useful metadata files:

```text
Sample.csv
Stimuli_Specification.csv
Agreement_Raters.csv
```

The exact file list must be verified from Figshare before download.

---

## 3.4 Expected I-DARE `.mat` Fields

Expected fields inside processed `.mat` modality files:

```text
subject
Fs
channels
channels_type
channels_unit
data
time
event_id
event_begin
event_end
```

The audit script must verify these fields and report missing or unexpected fields.

---

## 3.5 I-DARE EEG Assumptions to Verify

Expected EEG properties from the dataset description:

```text
EEG recorded from 40 electrodes
10-10 system
```

Processed EEG details must be verified from the files:

```text
sampling rate
number of channels
channel names
event boundaries
stimulus event duration
```

The current model expects 32 channels at 128Hz for the first EEG baseline. Therefore, the audit must determine:

```text
- whether I-DARE processed EEG is already resampled,
- whether we need to resample to 128Hz,
- which 32-channel intersection/canonical set can be used,
- whether all required DEAP-like channels are present.
```

No channel selection should be finalized before the audit.

---

## 3.6 I-DARE EMG Assumptions to Verify

I-DARE EMG is expected to contain:

```text
zygomaticus major
corrugator supercilii
```

This does not perfectly match DEAP EMG:

```text
DEAP: zEMG + tEMG
I-DARE: zygomaticus + corrugator
```

Therefore, the main EMG design remains:

```text
feature-level EMG harmonization
```

Do not start with a raw shared EMG waveform encoder.

The audit must report:

```text
- EMG channel names
- EMG sampling rate
- EMG event alignment with EEG
- EMG signal shape per subject
- availability of all 63 subjects
```

---

## 3.7 I-DARE Windowing Assumption

Main I-DARE windowing:

```text
one 5-second stimulus block -> one 5-second window
```

The audit must verify:

```text
- event_begin / event_end indexing
- actual duration of each stimulus event
- consistency across subjects
- alignment between label CSVs and event_id
```

No subwindowing should be used in the main protocol.

Possible later ablation:

```text
5s stimulus block -> 1s subwindows
```

This is not part of the first baseline.

---

# 4. Download Strategy

## 4.1 DEAP

Planned local structure:

```text
/mnt/HDD/AliWorks/DEAP/
    Data_preprocessed_python.zip
    data_preprocessed_python/
        s01.dat
        ...
        s32.dat
```

Do not commit any dataset files to Git.

---

## 4.2 I-DARE

Planned local structure, pending actual Figshare file list:

```text
/mnt/HDD/AliWorks/I-DARE/
    raw_downloads/
    processed/
        EEG/
        EMG/
        SC&PPG/
        ET/
    labels/
        Valence_SAM.csv
        Arousal_SAM.csv
        Quadrants_SAM.csv
    metadata/
        Sample.csv
        Stimuli_Specification.csv
        Agreement_Raters.csv
```

The exact structure may change after inspecting the Figshare archive. Any change must be documented in:

```text
docs/data_audit_idare.md
```

---

# 5. Dataset Audit Script Requirements

Create:

```text
scripts/01_audit_datasets.py
```

This script should be runnable before and after downloads.

Before downloads, it should report:

```text
DEAP folder exists but no recognized dataset files found.
I-DARE folder exists but no recognized dataset files found.
```

After downloads, it should inspect and report dataset structure.

---

## 5.1 DEAP Audit Requirements

The audit script must check:

```text
- DEAP root exists
- archive exists
- extracted folder exists
- number of `.dat` files
- file names
- ability to load one `.dat` file
- keys inside `.dat`
- shape of `data`
- shape of `labels`
- dtype of arrays
- number of trials
- number of channels
- number of samples
- inferred sampling rate assumption
- label ranges
- score == 5 counts
- class balance after removing score == 5
- EEG channel index plan
- EMG channel index plan
- feasibility of 12 non-overlapping 5s windows
```

Expected output file:

```text
docs/data_audit_deap.md
```

---

## 5.2 I-DARE Audit Requirements

The audit script must check:

```text
- I-DARE root exists
- downloaded archive/file list
- extracted folder structure
- presence of EEG folder
- presence of EMG folder
- number of EEG `.mat` files
- number of EMG `.mat` files
- presence of label CSV files
- label CSV shape and columns
- subject IDs
- event IDs
- `.mat` fields
- EEG sampling rates from `Fs`
- EMG sampling rates from `Fs`
- EEG channel names
- EMG channel names
- data matrix shapes
- time vector shapes
- event_begin / event_end consistency
- feasibility of one 5s window per stimulus event
```

Expected output file:

```text
docs/data_audit_idare.md
```

---

# 6. Project Decisions Confirmed in This Plan

## D-M1-001 — Use Current Storage Location

Decision:

```text
Use /mnt/HDD/AliWorks/DEAP and /mnt/HDD/AliWorks/I-DARE for the initial dataset phase.
```

Reason:

```text
Around 500GB free space is available.
The first phase uses preprocessed datasets only.
```

Status:

```text
Accepted for initial phase.
```

---

## D-M1-002 — Start DEAP from Preprocessed Python Version

Decision:

```text
Use DEAP Data_preprocessed_python.zip.
```

Reason:

```text
It matches the 128Hz model design and avoids raw preprocessing.
```

Status:

```text
Accepted.
```

---

## D-M1-003 — Discover I-DARE Files Before Download

Decision:

```text
Do not assume I-DARE archive structure. First list Figshare files and sizes.
```

Reason:

```text
The exact downloadable files/release have not been inspected locally yet.
```

Status:

```text
Accepted.
```

---

# 7. Immediate Next Actions

## Action A — DEAP Access

Check whether DEAP credentials are available.

If not available:

```text
Request official DEAP access.
```

Required target file:

```text
Data_preprocessed_python.zip
```

---

## Action B — I-DARE File Listing

Before downloading I-DARE, list the files from the Figshare project:

```text
https://figshare.com/projects/I_DARE/186558
```

The listing should capture:

```text
file name
file size
download URL if available
whether it contains EEG
whether it contains EMG
whether it contains labels/metadata
```

The file listing can be documented in:

```text
docs/data_sources_idare.md
```

or inside:

```text
docs/data_audit_idare.md
```

---

## Action C — Build Audit Script

After confirming dataset download/access plan:

```text
scripts/01_audit_datasets.py
```

The audit script should not assume the datasets are already present. It must gracefully handle missing data.

---

# 8. Do Not Do Yet

Do not start:

```text
training
baseline runs
contrastive learning
VREx
EMG fusion implementation
sequence modeling implementation
hyperparameter tuning
```

until dataset acquisition and audit are complete.

---

# 9. References and Source Notes

This plan is based on the official DEAP dataset documentation and the I-DARE dataset paper / public project description.

Important sources to verify during implementation:

```text
DEAP official download/readme pages
I-DARE Frontiers dataset paper
I-DARE Figshare project page
```

Reference URLs:

```text
https://eecs.qmul.ac.uk/mmv/datasets/deap/download.html
https://eecs.qmul.ac.uk/mmv/datasets/deap/readme.html
https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2024.1347327/full
https://figshare.com/projects/I_DARE/186558
```

---

# 10. Summary

Milestone 1 begins with dataset acquisition and audit, not model training.

Confirmed choices:

```text
DEAP: official preprocessed Python version, 128Hz
I-DARE: official Figshare project, files to be listed before download
Storage: current /mnt/HDD/AliWorks paths accepted for initial phase
```

Immediate next step:

```text
Confirm/download DEAP preprocessed Python archive and list I-DARE Figshare files.
```



# FILE: docs/data_sources_idare.md


# I-DARE Figshare Source Listing and Acquisition Summary

This document summarizes the I-DARE Figshare source listing generated during **Milestone 1 — Dataset acquisition and audit**.

It is based on the output of:

```text
scripts/list_idare_figshare_files.py
```

No I-DARE dataset files have been downloaded yet.  
This document only records the discovered Figshare metadata and the resulting acquisition decisions.

---

## 1. Project Summary

Figshare project:

```text
I DARE
```

Figshare project ID:

```text
186558
```

Project URL:

```text
https://figshare.com/projects/I_DARE/186558
```

API project URL observed during listing:

```text
https://api.figshare.com/v2/projects/186558
```

Listing result:

```text
Articles discovered: 5
Files discovered: 263
Total listed file size: 6.98 GB
```

This confirms that the full public Figshare project is small enough for the current storage situation.

---

## 2. Discovered Articles

| Article ID | Title | File count | DOI |
|---:|---|---:|---|
| 24680694 | Supplementary material | 7 | 10.6084/m9.figshare.24680694.v3 |
| 24678000 | EEG modality | 63 | 10.6084/m9.figshare.24678000.v1 |
| 24680640 | EMG modality | 64 | 10.6084/m9.figshare.24680640.v1 |
| 24680646 | SC&PPG modalities | 64 | 10.6084/m9.figshare.24680646.v1 |
| 24680751 | ET modality | 65 | 10.6084/m9.figshare.24680751.v1 |

---

## 3. Category Summary

| Category | File count | Total size |
|---|---:|---:|
| EEG | 63 | 4.90 GB |
| EMG | 64 | 1.99 GB |
| ET | 65 | 66.35 MB |
| SC/PPG | 64 | 31.46 MB |
| Labels | 4 | 21.90 KB |
| Metadata | 3 | 229.81 KB |

The full project size is approximately:

```text
6.98 GB
```

The first-stage required subset is approximately:

```text
6.88 GB
```

The difference is small because EEG and EMG dominate the storage cost.

---

## 4. First-Stage Required Files

For the current project, the required modalities are:

```text
EEG
EMG
SAM labels
basic metadata
```

Required categories:

```text
EEG files
EMG files
labels
metadata
```

Required first-stage count:

```text
134 files
```

Required first-stage size:

```text
6.88 GB
```

Optional / not needed for the first stage:

```text
SC&PPG
ET
Stimuli_Selection.pdf
```

These can be ignored for the initial EEG–EMG paper unless later analyses require them.

---

## 5. Supplementary / Label / Metadata Files

The supplementary material article contains:

| File name | Category | Size |
|---|---|---:|
| Agreement_Raters.csv | metadata | 2.90 KB |
| Arousal_SAM.csv | labels | 4.84 KB |
| Quadrants_SAM.csv | labels | 11.02 KB |
| Sample.csv | labels / sample table | 1.21 KB |
| Stimuli_Specifications.csv | metadata | 40.15 KB |
| Valence_SAM.csv | labels | 4.84 KB |
| Stimuli_Selection.pdf | metadata / documentation | 186.75 KB |

For the first stage, the minimum required files are:

```text
Valence_SAM.csv
Arousal_SAM.csv
Quadrants_SAM.csv
Sample.csv
Stimuli_Specifications.csv
Agreement_Raters.csv
```

`Stimuli_Selection.pdf` is not necessary for training but may be useful for dataset documentation.

---

## 6. Subject Coverage

Subject IDs were inferred from filenames matching:

```text
sbj_P_XX.mat
```

### EEG

```text
n_subjects = 63
```

EEG subject IDs:

```text
[1, 2, 3, 5, 6, 7, 8, 9, 10, 11,
 12, 13, 14, 15, 16, 17, 18, 19, 20, 21,
 22, 23, 24, 25, 26, 27, 28, 29, 30, 31,
 32, 33, 34, 35, 36, 37, 38, 39, 40, 41,
 42, 43, 44, 45, 46, 47, 48, 49, 50, 52,
 53, 54, 55, 56, 57, 58, 59, 60, 61, 62,
 63, 64, 65]
```

Missing EEG subject:

```text
4
```

### EMG

```text
n_subjects = 64
```

EMG subject IDs:

```text
[1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
 21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
 52, 53, 54, 55, 56, 57, 58, 59, 60, 61,
 62, 63, 64, 65]
```

### EEG–EMG Intersection

```text
EEG subjects: 63
EMG subjects: 64
Common EEG+EMG subjects: 63
EEG-only subjects: []
EMG-only subjects: [4]
```

---

## 7. Main Protocol Decision

Use the **63 common EEG+EMG subjects** for the main I-DARE experiments.

Subject 4 has EMG but no EEG. Therefore:

```text
Subject 4 must be excluded from the main EEG+EMG comparison.
```

Rationale:

The main paper compares:

```text
EEG-only
EMG-only
EEG+EMG
```

For fair comparison, all three conditions should use the same subject set. Therefore, the main I-DARE protocol should use only the subjects with both EEG and EMG.

Subject 4 may be kept only for an optional EMG-only secondary analysis, but not for the main comparison.

---

## 8. Download Decision

The first-stage I-DARE download should include:

```text
1. All EEG modality files
2. All EMG modality files
3. Supplementary label/metadata CSV files
```

Do not download yet:

```text
SC&PPG modality
ET modality
```

unless later needed.

---

## 9. Expected Local Storage Structure

Target root:

```text
/mnt/HDD/AliWorks/I-DARE
```

Recommended local structure:

```text
/mnt/HDD/AliWorks/I-DARE/
    raw_downloads/
        EEG/
        EMG/
        supplementary/
    processed/
        EEG/
        EMG/
    labels/
        Valence_SAM.csv
        Arousal_SAM.csv
        Quadrants_SAM.csv
        Sample.csv
    metadata/
        Stimuli_Specifications.csv
        Agreement_Raters.csv
```

The exact structure may be adjusted after download, but the audit report must document the final structure.

---

## 10. Implications for Audit

The dataset audit must verify:

```text
- all 63 EEG files are present
- all EMG files needed for the 63 common EEG+EMG subjects are present
- subject 4 is handled correctly
- label CSV files are present
- subject IDs in EEG, EMG, and labels can be aligned
- event IDs and stimulus IDs can be aligned
- EEG sampling rate is available from the files
- EMG sampling rate is available from the files
- channel names are available
- event_begin / event_end fields are available
- one 5-second stimulus window per event is feasible
```

Important audit rule:

```text
Do not assume I-DARE channel counts, sampling rates, or event durations.
Verify them from the downloaded files.
```

---

## 11. Current Git/Project Status

At the time this document is prepared:

```text
I-DARE file listing script exists:
scripts/list_idare_figshare_files.py

Generated metadata files exist locally:
docs/data_sources_idare.md
docs/data_sources_idare.json
docs/data_sources_idare_summary.txt
```

This document should replace or update the existing `docs/data_sources_idare.md`.

After adding this file to the repository, regenerate:

```text
docs/handoff_bundle_latest.md
```

so that the I-DARE source decision is available in future chats.

---

## 12. Next Steps

### Step 1 — Save this document

Copy this file to:

```text
docs/data_sources_idare.md
```

### Step 2 — Commit the source listing artifacts

Commit:

```text
scripts/list_idare_figshare_files.py
docs/data_sources_idare.md
docs/data_sources_idare.json
docs/data_sources_idare_summary.txt
```

### Step 3 — Update project memory

Update:

```text
docs/project_state.md
docs/chat_handoff_latest.md
docs/decision_log.md
docs/handoff_bundle_latest.md
```

Key decision to record:

```text
Use the 63 common EEG+EMG subjects for main I-DARE experiments.
Subject 4 is excluded from main EEG+EMG protocol.
```

### Step 4 — Build I-DARE download manifest

Create:

```text
docs/idare_download_manifest.csv
```

The manifest should include:

```text
category
article_id
file_id
file_name
size_bytes
size_human
subject_id
download_url
local_relative_path
include_in_first_stage
notes
```

### Step 5 — Download I-DARE only after manifest review

Only after manifest review should the dataset files be downloaded.

---

## 13. Do Not Do Yet

Do not start:

```text
training
baseline runs
contrastive learning
VREx
EMG fusion implementation
sequence modeling implementation
hyperparameter tuning
```

until dataset acquisition and audit are complete.



# FILE: docs/data_sources_idare_summary.txt


I-DARE Figshare Source Summary
==============================

Category summary:
- EEG: count=63, size=4.90 GB
- EMG: count=64, size=1.99 GB
- ET: count=65, size=66.35 MB
- SC/PPG: count=64, size=31.46 MB
- labels: count=4, size=21.90 KB
- metadata: count=3, size=229.81 KB

Subject coverage:
- EEG: n_subjects=63, ids=[1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65]
- EMG: n_subjects=64, ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65]
- SC/PPG: n_subjects=64, ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65]
- ET: n_subjects=65, ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65]

EEG/EMG intersection:
- EEG subjects: 63
- EMG subjects: 64
- Common EEG+EMG subjects: 63
- EEG-only subjects: []
- EMG-only subjects: [4]

First-stage required files:
- required_files: 134
- required_total_size: 6.88 GB



# FILE: experiments/registry.csv


run_id,date,dataset,task,split,model,config,status,main_metric,notes,commit_hash
R001,2026-05-04,DEAP,valence,LOSO,EEGSegmentClassifier-v1,configs/deap_eeg_segment_v1.yaml,planned,,First EEG-only DEAP run,
