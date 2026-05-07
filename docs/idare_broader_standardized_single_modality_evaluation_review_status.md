# I-DARE Broader Standardized Single-Modality Evaluation Review Status

## Status

Frozen human-review closeout.

The 96-run primary matrix is accepted as completed and valid broader single-modality evidence.

This is not final LOSO evidence and does not change any mainline automatically.

## Reviewed Evidence

- Report: `docs/idare_broader_standardized_single_modality_evaluation_report.md`
- JSON: `docs/idare_broader_standardized_single_modality_evaluation_report.json`
- Evidence level: broader standardized single-modality primary matrix, not final LOSO.

## Review Decision

| Item | Decision |
|---|---|
| Accept primary matrix? | yes |
| Change EEG mainline? | no |
| Change EMG mainline? | no |
| Promote BSL-stats to mainline? | no |
| Start EEG+EMG fusion? | no |
| Start full BSL/STIM paired model? | no |
| Lock `midpoint_as_high`? | no |
| Claim final LOSO? | no |

## Result Summary

| Modality | Task | Baseline macro F1 | Sidecar macro F1 | Delta | Interpretation |
|---|---|---:|---:|---:|---|
| EEG | valence | 0.5073 | 0.4835 | -0.0238 | baseline_better_broader_eval |
| EEG | arousal | 0.5103 | 0.5302 | 0.0199 | roughly_neutral_or_mixed |
| EMG | valence | 0.5140 | 0.5116 | -0.0024 | roughly_neutral_or_mixed |
| EMG | arousal | 0.5159 | 0.5103 | -0.0056 | roughly_neutral_or_mixed |

## Rationale

- EEG valence favors the `STIM-BSL`-only baseline.
- EEG arousal is a small BSL-stats gain, but the combined report labels it roughly neutral or mixed.
- EMG valence and EMG arousal are both roughly neutral or mixed.
- Because the evidence is mixed and still not final LOSO, keep mainlines unchanged.
- Keep BSL-stats sidecars as controlled ablations.

## Mainline After Review

- EEG practical mainline: baseline-corrected `STIM-BSL`-only.
- EMG practical mainline: feature-only EMG.
- BSL-stats: controlled ablation only.
- Fusion: not started.

## Not Authorized

- EEG+EMG fusion
- full model(BSL, STIM, STIM-BSL)
- final LOSO / final paper claim
- locking midpoint_as_high
- raw EMG mainline
- architecture ablations
- data augmentation
- SupCon / VREx / domain generalization
- optional robustness seed 13 without explicit objective

## Next Allowed Step

Stop here, hand off, or create a separate explicit objective for a future controlled follow-up.

Do not start fusion automatically from this closeout.

