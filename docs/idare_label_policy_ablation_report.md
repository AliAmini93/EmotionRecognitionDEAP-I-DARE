# I-DARE Controlled Label-Policy Ablation Report

## Status

Primary matrix complete.

This is controlled label-policy ablation evidence, not final LOSO evidence.

No final label policy is locked automatically by this report.

## Run Matrix

| Item | Value |
|---|---:|
| Modalities | 2 |
| Tasks | 2 |
| Label policies | 3 |
| Recipes | 2 |
| Folds | 6 |
| Seeds | 1 (`11`) |
| Total runs | 144 |

## Best Policy Summary

| Modality | Task | Best policy | Best recipe | Macro F1 | Balanced acc |
|---|---|---|---|---:|---:|
| EEG | valence | discard_midpoint | balanced_sampler_ce | 0.5066 | 0.5219 |
| EEG | arousal | midpoint_as_high | ce_class_weighted | 0.5313 | 0.5416 |
| EMG | valence | midpoint_as_high | ce_class_weighted | 0.5140 | 0.5202 |
| EMG | arousal | discard_midpoint | ce_class_weighted | 0.5253 | 0.5365 |

## Policy Detail

| Modality | Task | Policy | Recipe | Macro F1 | Balanced acc | One-class runs |
|---|---|---|---|---:|---:|---:|
| EEG | valence | discard_midpoint | balanced_sampler_ce | 0.5066 | 0.5219 | 0 |
| EEG | valence | midpoint_as_low | balanced_sampler_ce | 0.4777 | 0.4908 | 0 |
| EEG | valence | midpoint_as_high | ce_class_weighted | 0.5014 | 0.5069 | 0 |
| EEG | arousal | discard_midpoint | balanced_sampler_ce | 0.5089 | 0.5206 | 0 |
| EEG | arousal | midpoint_as_low | balanced_sampler_ce | 0.5160 | 0.5248 | 0 |
| EEG | arousal | midpoint_as_high | ce_class_weighted | 0.5313 | 0.5416 | 0 |
| EMG | valence | discard_midpoint | ce_class_weighted | 0.5043 | 0.5055 | 0 |
| EMG | valence | midpoint_as_low | ce_class_weighted | 0.5018 | 0.5072 | 0 |
| EMG | valence | midpoint_as_high | ce_class_weighted | 0.5140 | 0.5202 | 0 |
| EMG | arousal | discard_midpoint | ce_class_weighted | 0.5253 | 0.5365 | 0 |
| EMG | arousal | midpoint_as_low | balanced_sampler_ce | 0.5124 | 0.5331 | 0 |
| EMG | arousal | midpoint_as_high | ce_class_weighted | 0.5159 | 0.5192 | 0 |

## Interpretation

- All 144 authorized primary runs completed and produced valid combined outputs.

- This report does not lock a final label policy.
- This report does not authorize fusion or final LOSO claims.
- A human review / closeout decision is the next step.

## Not Authorized

- EEG+EMG fusion
- full model(BSL, STIM, STIM-BSL)
- final LOSO / final paper claim
- locking a final label policy without review
- raw EMG mainline
- architecture ablations
- data augmentation
- SupCon / VREx / domain generalization

## Next Allowed Step

Human review / closeout decision for the label-policy ablation.

