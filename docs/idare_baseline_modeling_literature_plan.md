# I-DARE Baseline-Aware Modeling Literature Plan

## Status

Created as a focused planning note before implementing a BSL/STIM-aware I-DARE model.

Current recommendation:

- Mainline representation for I-DARE remains `response = STIM - BSL`.
- Raw `STIM only` remains a legacy/control baseline.
- A paired model such as `model(BSL, STIM, STIM-BSL)` should be treated as a controlled ablation, not as the next default architecture.
- The first paired ablation should be a low-capacity version: `STIM-BSL + BSL summary features`, before a full three-branch neural model.

## Why this document exists

I-DARE is not simply a collection of independent EEG windows. Each emotional STIM event has a dedicated preceding BSL event. A model that sees only STIM can ignore part of the experimental design.

We already created baseline-corrected caches for I-DARE, which is the right first correction. The remaining question is whether the model should explicitly see BSL and STIM as paired inputs.

## Dataset contrast: I-DARE vs DEAP

| Dataset | Stimulus unit | Baseline structure | Modeling implication |
|---|---|---|---|
| I-DARE | 32 emotional pictures per subject | A dedicated black-screen BSL immediately precedes each picture STIM | Trial-wise paired modeling is meaningful: `BSL`, `STIM`, and `STIM-BSL` all have interpretable roles. |
| DEAP | 40 one-minute music videos per subject | DEAP preprocessed Python contains a short baseline segment before the 60s stimulus signal | Baseline correction is appropriate, but DEAP is less naturally a paired 5s BSL/STIM design. |

Project consequence:

- A fully paired I-DARE model will be more faithful to I-DARE.
- But it will no longer be architecture-identical to the current DEAP-style pipeline.
- That is acceptable if introduced as an I-DARE-aware ablation.

## Initial literature-review targets

| Source | What to extract | Relevance |
|---|---|---|
| I-DARE dataset paper, Frontiers in Human Neuroscience 2024, DOI `10.3389/fnhum.2024.1347327`, PMC `PMC10987697` | Exact trial timeline, modalities, number of subjects, stimulus type, SAM ratings, preprocessing notes | Primary justification for BSL/STIM-aware modeling. |
| DEAP paper, IEEE TAC 2012, DOI `10.1109/T-AFFC.2011.15` | Trial timing, baseline/fixation design, modalities, rating structure | Defines what should stay comparable with DEAP and what does not have to be identical. |
| Hu et al., NeuroImage 2014, `Single-trial time-frequency analysis of electrocortical signals: baseline correction and beyond` | Baseline subtraction vs percentage correction; role of pre-stimulus variability | Supports `STIM-BSL` as mainline and motivates BSL-aware ablations. |
| EEG emotion recognition review, Frontiers in Computational Neuroscience 2021, DOI `10.3389/fncom.2021.758212` | Common EEG emotion-recognition architectures and dataset taxonomy | Helps position our method in related work. |
| SEED / SEED-IV model papers | Long clip segmentation and EEG feature/model design | Useful contrast, but not direct evidence for I-DARE's short BSL/STIM picture protocol. |
| DREAMER and AMIGOS papers | Multimodal affective datasets with video stimuli | Broad comparison only; not central to I-DARE BSL/STIM modeling. |
| Baseline reduction papers on DEAP/DREAMER/AMIGOS | Alternative baseline-removal methods | Candidate future ablations only after the current protocol is stable. |

## Modeling candidates

### Candidate A: STIM-only legacy baseline

```text
model(STIM)
```

Purpose:

- Control condition.
- Answers how much we lose by ignoring the dedicated BSL event.

Expected role:

- Not the main I-DARE-aware model.

### Candidate B: baseline-corrected response mainline

```text
response = STIM - mean(BSL)
model(response)
```

Purpose:

- Current best practical mainline.
- Respects I-DARE's trial-wise BSL/STIM structure without increasing model complexity too much.
- Maintains reasonable comparability with DEAP-style baseline-corrected preprocessing.

Expected role:

- Mainline representation for the next EEG-only and EEG+EMG fusion smokes.

### Candidate C: response plus baseline summary statistics

```text
response = STIM - mean(BSL)
bsl_stats = summary(BSL)
model(response, bsl_stats)
```

Possible BSL summaries:

- per-channel mean
- per-channel standard deviation
- global BSL energy / variance
- bandpower summaries, if a frequency-domain pipeline exists

Purpose:

- Captures whether the participant's pre-stimulus state explains additional variation.
- Lower risk than feeding full BSL waveforms to a neural branch.

Expected role:

- First I-DARE-aware ablation after the current baseline-corrected cache path.

### Candidate D: two-branch paired model

```text
h_bsl = encoder(BSL)
h_stim = encoder(STIM)
h_delta = h_stim - h_bsl
classifier(concat(h_stim, h_delta))
```

Purpose:

- Lets the model learn a paired transformation.
- More faithful to I-DARE trial design.

Risk:

- Overfitting with only 2016 trials.
- Subject/session leakage if capacity is too high.

Expected role:

- Ablation after Candidate C.

### Candidate E: three-branch paired model

```text
h_bsl = encoder_bsl(BSL)
h_stim = encoder_stim(STIM)
h_delta = encoder_delta(STIM-BSL)
classifier(concat(h_bsl, h_stim, h_delta))
```

Purpose:

- Full `model(BSL, STIM, STIM-BSL)` design.

Risk:

- Highest capacity and highest overfit risk.
- Less directly comparable with DEAP.

Expected role:

- Advanced ablation only after Candidates B and C are stable.

## Recommended ablation order

1. Freeze current `STIM-BSL` baseline-corrected I-DARE EEG result.
2. Build a paired audit/index that confirms both BSL and STIM references are available.
3. Smoke Candidate C: `STIM-BSL + BSL stats`.
4. If Candidate C beats `STIM-BSL` on macro F1 and balanced accuracy without calibration collapse, try Candidate D.
5. Only then consider Candidate E.

## Evaluation rules

Use the same discipline as previous smoke work:

- subject-held-out first
- LOSO or full protocol only after smoke stability
- same label policy, preferably `midpoint_as_high` unless a prior status document says otherwise
- report macro F1, balanced accuracy, accuracy, majority baseline, threshold sweep, one-class collapse
- standardize features using train-fold statistics only
- never mix trials from the same subject across train and validation
- keep model capacity deliberately small for paired models

## Decision gates

A paired model is worth keeping only if it satisfies all of the following in smoke runs:

- no one-class collapse
- stable probability distribution across folds
- final macro F1 improves over `STIM-BSL` baseline-corrected model, or threshold-tuned macro F1 improves without unstable thresholds
- balanced accuracy does not drop while macro F1 improves
- improvement appears in both valence and arousal, or there is a clear task-specific explanation

## Current decision

For now:

- Use `STIM-BSL` as the main I-DARE EEG response representation.
- Do not replace it with `model(BSL, STIM, STIM-BSL)` yet.
- Start with `STIM-BSL + BSL stats` as the next model ablation.

## Proposed next implementation step

Create a small audit/plan script for Candidate C.

Suggested outputs:

- `docs/idare_eeg_bsl_stats_ablation_plan.md`
- `docs/idare_eeg_bsl_stats_ablation_plan.json`

The audit should confirm:

- baseline-corrected EEG cache path
- cache index path
- whether BSL metadata is retained
- whether per-trial BSL summary stats already exist
- if not, whether they can be computed from raw EEG HDF5/MAT files using the same preceding-BSL convention

After that audit passes, build a sidecar:

- `.cache/idare_eeg_bsl_stats.npy`
- `.cache/idare_eeg_bsl_stats_index.csv`

Then smoke-test:

```text
model(STIM-BSL EEG cache + BSL stats sidecar)
```
