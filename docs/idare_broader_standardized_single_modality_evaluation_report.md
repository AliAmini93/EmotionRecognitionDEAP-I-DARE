# I-DARE Broader Standardized Single-Modality Evaluation Report

## Status

Primary matrix complete.

This is broader standardized single-modality evidence, not final LOSO evidence.

No mainline is changed automatically by this report.

## Run Matrix

| Item | Value |
|---|---:|
| Conditions | 4 |
| Tasks | 2 |
| Recipes | 2 |
| Folds | 6 |
| Seeds | 1 (`11`) |
| Total runs | 96 |

## Validation

| Condition | Runs | Prediction rows | Fold 1 aligned? |
|---|---:|---:|---|
| EEG-B0 | 24 | 8064 | yes |
| EEG-B1 | 24 | 8064 | yes |
| EMG-B0 | 24 | 8064 | yes |
| EMG-B1 | 24 | 8064 | yes |

## Best Recipe Per Condition and Task

| Condition | Task | Best recipe | Macro F1 | Balanced acc | Accuracy | One-class runs |
|---|---|---|---:|---:|---:|---:|
| EEG-B0 | valence | ce_class_weighted | 0.5073 | 0.5196 | 0.5513 | 0 |
| EEG-B0 | arousal | ce_class_weighted | 0.5103 | 0.5151 | 0.5319 | 0 |
| EEG-B1 | valence | ce_class_weighted | 0.4835 | 0.5078 | 0.5205 | 0 |
| EEG-B1 | arousal | balanced_sampler_ce | 0.5302 | 0.5427 | 0.5330 | 0 |
| EMG-B0 | valence | ce_class_weighted | 0.5140 | 0.5202 | 0.5226 | 0 |
| EMG-B0 | arousal | ce_class_weighted | 0.5159 | 0.5192 | 0.5211 | 0 |
| EMG-B1 | valence | ce_class_weighted | 0.5116 | 0.5163 | 0.5198 | 0 |
| EMG-B1 | arousal | balanced_sampler_ce | 0.5103 | 0.5143 | 0.5153 | 0 |

## Direct Baseline vs BSL-stats Comparison

| Modality | Task | Baseline recipe | Baseline macro F1 | Sidecar recipe | Sidecar macro F1 | Delta macro F1 | Baseline bal acc | Sidecar bal acc | Delta bal acc | Interpretation |
|---|---|---|---:|---|---:|---:|---:|---:|---:|---|
| EEG | valence | ce_class_weighted | 0.5073 | ce_class_weighted | 0.4835 | -0.0238 | 0.5196 | 0.5078 | -0.0117 | baseline_better_broader_eval |
| EEG | arousal | ce_class_weighted | 0.5103 | balanced_sampler_ce | 0.5302 | 0.0199 | 0.5151 | 0.5427 | 0.0276 | roughly_neutral_or_mixed |
| EMG | valence | ce_class_weighted | 0.5140 | ce_class_weighted | 0.5116 | -0.0024 | 0.5202 | 0.5163 | -0.0038 | roughly_neutral_or_mixed |
| EMG | arousal | ce_class_weighted | 0.5159 | balanced_sampler_ce | 0.5103 | -0.0056 | 0.5192 | 0.5143 | -0.0049 | roughly_neutral_or_mixed |

## Interpretation

- All 96 authorized primary runs completed and produced valid JSON plus prediction CSVs.

- Fold 1 alignment was verified across all four conditions.

- This report does not automatically change the EEG or EMG mainline.

- This report does not authorize fusion or final LOSO claims.

- A human review / closeout decision is the next step.


## Not Authorized From This Report

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

Human review / closeout decision for the broader standardized single-modality evaluation.

