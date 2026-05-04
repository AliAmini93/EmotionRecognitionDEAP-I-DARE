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
Begin Milestone 1 - Dataset acquisition and audit.

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

## Current Code Status
- Repository scaffold exists locally and has been pushed to GitHub.
- Three EEG model files are added under `src/emotion_deap_idare/models/`.
- Virtual environment is created.
- PyTorch CUDA 12.8 is installed.
- GPU smoke test passed on NVIDIA GeForce RTX 5090.
- EEGSegmentClassifier-v1 lite has 337,955 trainable parameters.
- Working proposal V1.1 is stored at `docs/proposal_v1_1.md`.

## Immediate Next Step
Commit proposal V1.1, then begin dataset acquisition and audit.

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



# FILE: experiments/registry.csv


run_id,date,dataset,task,split,model,config,status,main_metric,notes,commit_hash
R001,2026-05-04,DEAP,valence,LOSO,EEGSegmentClassifier-v1,configs/deap_eeg_segment_v1.yaml,planned,,First EEG-only DEAP run,
