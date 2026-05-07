# I-DARE Single-Modality BSL-stats vs Baseline Review Status

## Status

Frozen human-review closeout.

This document records human review of `docs/idare_single_modality_bsl_stats_vs_baseline_comparison.md`.

This is **not** a final LOSO result and does **not** start EEG+EMG fusion.

## Reviewed Evidence

- Comparison report: `docs/idare_single_modality_bsl_stats_vs_baseline_comparison.md`
- Comparison JSON: `docs/idare_single_modality_bsl_stats_vs_baseline_comparison.json`

## Review Decision

Accepted.

| Area | Decision |
|---|---|
| Mainline changed? | no |
| EEG practical mainline | keep baseline-corrected `STIM-BSL`-only for now |
| EMG practical mainline | keep feature-level EMG for now |
| EEG BSL-stats sidecar | keep as controlled ablation |
| EMG BSL-stats sidecar | keep as controlled ablation; smoke-level marginal gains do not justify mainline change |
| EEG+EMG fusion | not started |
| Full `model(BSL, STIM, STIM-BSL)` | not started |
| Label policy | do not lock `midpoint_as_high` |

## Rationale

- EEG: the standardized `STIM-BSL`-only baseline beats the EEG BSL-stats sidecar on final macro-F1 for both valence and arousal in the smoke comparison.
- EMG: the BSL-stats sidecar has small positive deltas over feature-only EMG, but these are smoke-level and marginal.
- The comparison is useful for roadmap control, but it is not final performance evidence.

## Next Allowed Step

No experiment is automatically authorized by this review.

Allowed next work without a new experimental objective:

- Handoff/status summary.
- Documentation cleanup if stale notes are found.
- Planning a broader standardized single-modality evaluation.

Execution of any broader evaluation, fusion, full paired model, or architecture ablation requires an explicit new short-term objective first.

## Intentionally Not Started

- EEG+EMG fusion.
- Full `model(BSL, STIM, STIM-BSL)`.
- Final LOSO / final performance claim.
- Locking `midpoint_as_high`.
- Raw EMG mainline.
- Architecture ablations.
- Data augmentation.
- SupCon / VREx / domain generalization.
