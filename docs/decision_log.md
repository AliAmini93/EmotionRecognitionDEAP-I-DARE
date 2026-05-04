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
