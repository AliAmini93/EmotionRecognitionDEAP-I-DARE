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
