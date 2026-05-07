# I-DARE Label-Policy Ablation Review Status

## Status

Frozen human-review closeout.

This closes the controlled 144-run I-DARE label-policy ablation at smoke/stabilization evidence level.

It does **not** make a final LOSO claim.

It does **not** lock a final global label policy.

## Reviewed Inputs

- Primary report: `docs/idare_label_policy_ablation_report.md`
- Primary JSON: `docs/idare_label_policy_ablation_report.json`
- EEG combined output: `docs/idare_label_policy_ablation_eeg_primary.json`
- EMG combined output: `docs/idare_label_policy_ablation_emg_primary.json`

## Result Summary

| Modality | Task | Best policy | Best recipe | Macro F1 | Balanced acc |
|---|---|---|---|---:|---:|
| EEG | valence | `discard_midpoint` | `balanced_sampler_ce` | 0.5066 | 0.5219 |
| EEG | arousal | `midpoint_as_high` | `ce_class_weighted` | 0.5313 | 0.5416 |
| EMG | valence | `midpoint_as_high` | `ce_class_weighted` | 0.5140 | 0.5202 |
| EMG | arousal | `discard_midpoint` | `ce_class_weighted` | 0.5253 | 0.5365 |

## Review Decision

- The 144-run label-policy matrix is accepted as a valid controlled smoke/stabilization ablation.
- The result is mixed: no single label policy wins across EEG/EMG and valence/arousal.
- Do **not** lock `midpoint_as_high`, `midpoint_as_low`, or `discard_midpoint` as the final global paper policy.
- Keep `midpoint_as_high` only as the practical continuity/default smoke policy for now.
- Keep `discard_midpoint` as a serious task-specific contender, especially for EEG valence and EMG arousal.

## Mainline / Policy Status After Review

- EEG practical mainline remains baseline-corrected `STIM-BSL`-only.
- EMG practical mainline remains feature-level EMG.
- Label policy remains unresolved for final claims.
- Any future final-label decision needs an explicit follow-up objective, likely robustness-focused.

## Not Authorized

- EEG+EMG fusion
- full model(BSL, STIM, STIM-BSL)
- final LOSO / final paper claim
- locking a final global label policy
- raw EMG mainline
- architecture ablations
- data augmentation
- SupCon / VREx / domain generalization
- optional extra seeds without explicit objective

## Next Allowed Step

Stop here, hand off, or create a separate explicit follow-up objective for label-policy robustness before locking any final policy.
