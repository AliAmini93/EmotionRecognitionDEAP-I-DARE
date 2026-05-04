# Working Proposal — Version V1.1

## Provisional Title

**Cross-Subject EEG–EMG Emotion Recognition with Trial-Aware Temporal Modeling: A Controlled Study on DEAP and I-DARE**

This version extends V1.0 by adding two key components:

1. An **EMG branch** as an auxiliary modality, designed conservatively to remain compatible with both DEAP and I-DARE.
2. **Trial / sequence modeling** to address the trial-level labeling structure of DEAP.

In this version, **cross-dataset transfer between DEAP and I-DARE is not included**. The focus is strictly on **within-dataset cross-subject generalization**.

---

## 1. Motivation and Research Problem

Cross-subject emotion recognition from EEG is difficult because EEG signals vary strongly across individuals. These variations are caused by neural, anatomical, cognitive, attentional, fatigue-related, and recording-related differences.

In emotion recognition, an affective response is not only a property of the stimulus. It is also a property of the individual response to that stimulus. The same video or image may be exciting for one person, neutral for another, and unpleasant for someone else.

DEAP and I-DARE were selected because both contain EEG and EMG recordings. This enables the study to address two central questions:

1. Does auxiliary EMG improve EEG-based cross-subject emotion recognition?
2. Does modeling the temporal structure inside a trial improve performance, especially for DEAP?

In DEAP, each trial is approximately 60 seconds long, but the label is assigned at the **trial level**. If the trial is divided into shorter 5-second segments and each segment is classified independently, the model is trained with weak segment-level labels. Therefore, DEAP requires a careful evaluation of **trial-level sequence encoding**.

---

## 2. Research Questions

### RQ1 — Contribution of EMG

Does adding EMG as an auxiliary modality improve cross-subject emotion recognition compared with EEG-only models?

### RQ2 — Contribution of Trial-Aware Temporal Modeling

For DEAP, does modeling the sequence of twelve 5-second segments inside each trial improve performance compared with independent segment-level classification?

### RQ3 — Interaction Between EMG and Sequence Modeling

If temporal sequence encoding is added, does EMG still provide additional value?

### RQ4 — Best Fusion Location

Should EEG and EMG be fused at every 5-second segment, or should each modality first build its own trial-level sequence representation before information fusion?

### RQ5 — Contrastive Learning as a Later Ablation

Can an affective-response-aware contrastive loss improve cross-subject generalization?

In V1.1, RQ5 is not part of the core model. It is reserved for later ablation after the baseline models are stabilized.

---

## 3. Current Locked Decisions

### Datasets

- Main datasets: **DEAP** and **I-DARE**
- Evaluation setting: **strict cross-subject / LOSO**
- Cross-dataset transfer is not included in this paper version.

### Tasks

- Binary valence classification
- Binary arousal classification

Suggested label harmonization:

```python
label = 1 if score > 5 else 0
score == 5 -> discard
```

The midpoint score is discarded to reduce label noise.

### Windowing

#### DEAP

```text
60s trial -> 12 windows × 5s
stride = 5s
overlap = 0 in the main protocol
```

#### I-DARE

```text
5s stimulus block -> 1 window
```

If event structure allows it, internal subwindows may be explored later. However, the main sequence-modeling claim is made on DEAP, not I-DARE.

### Normalization

- Normalization statistics must be computed using **training subjects only** in each fold.
- No statistics from the held-out test subject should be used for training, validation, model selection, or normalization.

---

## 4. EMG Design and the Need for a Conservative Strategy

DEAP and I-DARE do not provide perfectly matched EMG channels.

- DEAP commonly provides **zEMG** and **tEMG**.
- I-DARE uses facial EMG channels such as **zygomaticus** and **corrugator**.

This means that a raw, muscle-specific EMG encoder may learn dataset-specific muscle identity, electrode placement, or amplitude patterns rather than general affective information.

Therefore, the main decision in V1.1 is:

> EMG will be used as a **feature-level auxiliary modality**, not as a raw waveform branch in the main model.

This lowers the risk of overfitting to dataset-specific EMG characteristics and helps harmonize DEAP and I-DARE.

---

## 5. EMG Branch Design

### 5.1 EMG Input

For each 5-second window, features are extracted from each EMG channel.

Suggested input shape:

```text
x_emg_feat: [B, N_emg, F]
```

For DEAP and I-DARE, the expected default is:

```text
N_emg = 2
F = 7
```

### 5.2 Proposed EMG Features

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

For two EMG channels:

```text
2 × 7 = 14 features
```

However, instead of flattening these features directly, each EMG channel is encoded separately using a shared channel-level encoder.

---

### 5.3 Channel-Shared EMG Encoder

To reduce dependence on exact muscle identity, a **shared MLP** is applied to each EMG channel:

```text
x_emg_feat: [B, N_emg, 7]

Shared MLP per channel:
    Linear(7, 32)
    LayerNorm
    GELU
    Dropout
    Linear(32, d_emg)

Attention pooling over EMG channels:
    [B, N_emg, d_emg] -> [B, d_emg]
```

Advantages:

- Compatible with both DEAP and I-DARE.
- Does not assume anatomical equivalence between all EMG channels.
- Keeps the parameter count low.
- Can be extended later if needed.

---

### 5.4 EMG-Only Baseline

An EMG-only baseline is necessary:

```text
EMG features -> shared EMG MLP -> EMG channel attention pooling -> classifier
```

This baseline answers whether EMG alone contains usable affective information. If EMG-only is weak but EEG+EMG improves over EEG-only, EMG is acting as a useful auxiliary cue.

---

## 6. EEG Branch Design

The EEG branch is based on `EEGSegmentClassifier-v1`:

```text
EEG window [B, C, T]
-> multi-branch temporal stem
-> depthwise/grouped TCN
-> temporal attention pooling
-> channel position embedding
-> channel self-attention
-> channel attention pooling
-> z_eeg
```

Default EEG settings:

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

The spectral branch remains optional and disabled in the main model.

---

## 7. Trial / Sequence Modeling

### 7.1 Why Sequence Modeling Is Needed

In DEAP, labels are assigned at the trial level, not at the segment level. If every 5-second segment is classified independently, the model is forced to assign the global trial label to every segment.

Proposed solution:

```text
60s trial
-> 12 × 5s windows
-> segment embeddings
-> trial sequence encoder
-> trial-level prediction
```

---

### 7.2 EEG Sequence Encoder Options

For a sequence length of 12, very large models such as large Transformers or Mamba are not necessary at this stage.

Candidate EEG sequence encoders, ordered by complexity:

```text
1. Mean pooling
2. Temporal attention pooling
3. Lightweight TCN + attention pooling
4. BiGRU + attention pooling
5. Lightweight Transformer
6. Mamba / SSM only if sequence length is increased
```

Default V1.1 candidate for EEG:

```text
Lightweight TCN over segment embeddings + temporal attention pooling
```

Reasons:

- The sequence is short.
- TCN is lightweight.
- It provides a useful temporal inductive bias.
- It is less prone to overfitting than a Transformer in this setting.

---

### 7.3 EMG Sequence Encoder

EMG is feature-level, low-dimensional, and potentially noisy. Therefore, the EMG sequence encoder should remain lightweight.

Candidate EMG sequence encoders:

```text
1. Temporal attention pooling
2. Tiny TCN + attention pooling
3. Small GRU
```

Default V1.1 candidate for EMG:

```text
Temporal attention pooling
```

Ablation:

```text
Tiny TCN + attention pooling
```

---

## 8. Two Main Fusion Families

In V1.1, fusion is treated as an independent design axis. Two main fusion families are considered.

---

### 8.1 Segment-Level Fusion

EEG and EMG are fused at every 5-second window:

```text
for each segment t:
    EEG_t -> z_eeg_t
    EMG_t -> z_emg_t
    fuse(z_eeg_t, z_emg_t) -> z_fused_t

then:
    [z_fused_1, ..., z_fused_12]
    -> shared trial sequence encoder
    -> trial prediction
```

Suggested name:

```text
Early temporal fusion / segment-level fusion
```

Advantages:

- Simpler
- Fewer parameters
- Models simultaneous EEG–EMG information within each 5-second window

Limitations:

- Assumes EEG and EMG should be aligned within the same 5-second window
- May be less suitable if EMG responses are sparse, delayed, or asynchronous relative to EEG

---

### 8.2 Modality-Specific Sequence Encoding + Trial-Level Fusion

Each modality first builds its own trial-level representation:

```text
EEG sequence:
    [EEG_1, ..., EEG_12]
    -> EEG segment encoder
    -> EEG sequence encoder
    -> h_eeg_trial

EMG sequence:
    [EMG_1, ..., EMG_12]
    -> EMG segment encoder
    -> EMG sequence encoder
    -> h_emg_trial

Fusion:
    fuse(h_eeg_trial, h_emg_trial)
    -> classifier
```

Suggested name:

```text
Late trial-level fusion / modality-specific sequence fusion
```

Advantages:

- Each modality learns its own temporal dynamics.
- More compatible with trial-level labels in DEAP.
- Better handles sparse or delayed EMG responses.

Limitations:

- More parameters
- EMG sequence encoder may overfit if it is too large

---

## 9. Fusion Operation

For both fusion families, the actual fusion operation can remain simple.

Main fusion operators:

```text
1. concat + MLP
2. gated fusion
```

Default candidate:

```text
gated fusion
```

However, `concat + MLP` must also be tested as a baseline.

Gated fusion formula:

```text
g = sigmoid(MLP([z_eeg, z_emg]))
z = g * z_eeg + (1 - g) * z_emg
```

In segment-level fusion, this is applied at each segment.

In trial-level fusion, this is applied to `h_eeg_trial` and `h_emg_trial`.

---

## 10. V1.1 Model Variants

### M0 — EEG-Only Segment Baseline

```text
EEG 5s window
-> EEGSegmentClassifier-v1
-> logits
```

Use case:

- Initial EEG-only baseline
- Suitable for I-DARE
- Useful for DEAP if segment-level evaluation is needed

---

### M1 — EEG-Only Trial Sequence Model

For DEAP:

```text
60s trial
-> 12 × 5s EEG windows
-> EEGSegmentEncoder per window
-> EEG sequence encoder
-> classifier
```

This model tests RQ2 without EMG.

---

### M2 — EMG-Only Segment Model

```text
EMG 5s features
-> channel-shared EMG encoder
-> classifier
```

---

### M3 — EMG-Only Trial Sequence Model

For DEAP:

```text
12 × 5s EMG feature windows
-> EMG encoder per window
-> EMG temporal attention / tiny TCN
-> classifier
```

---

### M4 — EEG+EMG Segment-Level Fusion

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

---

### M5 — EEG+EMG Modality-Specific Sequence Fusion

For DEAP:

```text
EEG windows -> EEG sequence encoder -> h_eeg_trial
EMG windows -> EMG sequence encoder -> h_emg_trial
fuse(h_eeg_trial, h_emg_trial)
-> classifier
```

This is potentially the strongest representation but must be compared against M4.

---

## 11. Experimental Roadmap

### Phase 0 — Data Protocol

- Use DEAP preprocessed data
- Use I-DARE processed EEG/EMG data
- Resample to 128 Hz if needed
- Strict LOSO
- Validation subjects selected only from training subjects
- Normalization computed only from training subjects

---

### Phase 1 — EEG-Only Baselines

```text
R0: OldEncoder + classifier
R1: EEGSegmentClassifier-v1
R2: EEGNet / ShallowConvNet
```

Goal:

> Stabilize the EEG backbone before adding EMG and sequence modeling.

---

### Phase 2 — EEG Sequence Modeling on DEAP

```text
S0: Mean pooling over 12 segment embeddings
S1: Temporal attention pooling
S2: Lightweight TCN + attention pooling
S3: BiGRU + attention pooling
```

Default candidate:

```text
S2: Lightweight TCN + attention pooling
```

---

### Phase 3 — EMG Baselines

```text
E0: EMG-only segment classifier
E1: EMG-only trial attention model
E2: EMG-only tiny TCN sequence model
```

---

### Phase 4 — EEG+EMG Fusion

```text
F1: Segment-level concat fusion
F2: Segment-level gated fusion
F3: Modality-specific sequence + concat fusion
F4: Modality-specific sequence + gated fusion
```

Key comparison:

```text
F2 vs F4
```

This comparison answers:

> Is fusion at every 5-second window better, or should each modality first build its own sequence-level representation before fusion?

---

### Phase 5 — I-DARE

For I-DARE:

```text
I1: EEG-only
I2: EMG-only
I3: EEG+EMG concat
I4: EEG+EMG gated
```

Since the natural sequence length is likely 1, no main sequence-modeling claim is made on I-DARE unless subwindow experiments are later added.

---

### Phase 6 — Contrastive / Regularization Ablation

Only after the main model is stabilized:

```text
CE only
CE + Affective SupCon
CE + VREx
CE + SupCon + VREx
```

Contrastive learning is applied to the trial-level representation.

---

## 12. Contrastive Learning in V1.1

The proposed contrastive design is:

```text
positive:
    same emotion label
    different subject
    optionally close continuous rating

hard negative:
    same video/stimulus
    different reported emotion
```

This is preferred over stimulus-only contrastive learning because the same stimulus does not necessarily evoke the same emotion across subjects.

Application location:

```text
trial-level representation
```

Not segment-level representation.

---

## 13. Metrics

For each main run:

```text
Accuracy
Macro-F1
Balanced Accuracy
Per-subject accuracy
Mean ± std across LOSO folds
95% confidence interval
Wilcoxon signed-rank test for key model comparisons
```

For DEAP, segment-level and trial-level reporting must be clearly separated. The primary result should be trial-level.

---

## 14. Visualizations

Minimum required visualizations:

```text
1. Confusion matrix
2. Per-subject performance bar plot
3. Temporal attention over 12 DEAP segments
4. EMG channel attention
5. Fusion gate distribution
6. EEG vs EMG contribution analysis
7. UMAP / t-SNE of embeddings before and after sequence encoding
```

---

## 15. Main Ablations

### DEAP

| Code | EEG | EMG | Sequence | Fusion | Purpose |
|---|---:|---:|---:|---|---|
| D1 | Yes | No | No | — | EEG segment baseline |
| D2 | Yes | No | Yes | — | Effect of EEG sequence modeling |
| D3 | No | Yes | No | — | EMG segment baseline |
| D4 | No | Yes | Yes | — | EMG temporal dynamics |
| D5 | Yes | Yes | No | Segment fusion | EMG effect without sequence |
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

### I-DARE

| Code | EEG | EMG | Fusion | Purpose |
|---|---:|---:|---|---|
| I1 | Yes | No | — | EEG baseline |
| I2 | No | Yes | — | EMG baseline |
| I3 | Yes | Yes | concat | Fusion baseline |
| I4 | Yes | Yes | gated | Main I-DARE candidate |

---

## 16. Suggested V1.1 Defaults

### EEG Segment Encoder

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

### EEG Sequence Encoder

```text
Lightweight TCN + temporal attention pooling
```

### EMG Encoder

```text
Channel-shared feature MLP + EMG channel attention pooling
```

### EMG Sequence Encoder

```text
Temporal attention pooling
```

Ablation:

```text
Tiny TCN + attention pooling
```

### Fusion

Initial baseline:

```text
concat + MLP
```

Main candidate:

```text
gated fusion
```

Both must be tested in segment-level and trial-level fusion settings.

---

## 17. Summary of Version V1.1

V1.1 extends the project from an EEG-only segment classifier to a complete controlled framework including:

1. EEG-only baseline
2. EMG-only baseline
3. EEG sequence modeling
4. EMG sequence modeling
5. EEG+EMG segment-level fusion
6. EEG+EMG modality-specific trial-level fusion
7. Contrastive learning as a later ablation

The central methodological decision in V1.1 is that fusion is not assumed to be fixed. Instead, the paper tests two competing hypotheses:

```text
H1: EEG and EMG should be fused at every 5-second window.
H2: EEG and EMG should first build modality-specific sequence representations, followed by trial-level fusion.
```

This allows the paper to answer not only whether EMG helps, but also **where and how EMG should be integrated with EEG** in cross-subject emotion recognition.
