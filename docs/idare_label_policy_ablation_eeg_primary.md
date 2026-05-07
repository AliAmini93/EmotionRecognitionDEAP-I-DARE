# I-DARE Label-Policy Ablation: EEG STIM-BSL-only

## Status

Primary label-policy matrix complete.

This is controlled ablation evidence, not final LOSO evidence.

## Validation

| Policy | Runs | Prediction rows | Fold 1 aligned? |
|---|---:|---:|---|
| discard_midpoint | 24 | 6932 | yes |
| midpoint_as_low | 24 | 8064 | yes |
| midpoint_as_high | 24 | 8064 | yes |

## Best Recipe Per Task and Policy

| Task | Policy | Best recipe | Macro F1 | Balanced acc | Accuracy | One-class runs |
|---|---|---|---:|---:|---:|---:|
| valence | discard_midpoint | balanced_sampler_ce | 0.5066 | 0.5219 | 0.5209 | 0 |
| valence | midpoint_as_low | balanced_sampler_ce | 0.4777 | 0.4908 | 0.4931 | 0 |
| valence | midpoint_as_high | ce_class_weighted | 0.5014 | 0.5069 | 0.5340 | 0 |
| arousal | discard_midpoint | balanced_sampler_ce | 0.5089 | 0.5206 | 0.5400 | 0 |
| arousal | midpoint_as_low | balanced_sampler_ce | 0.5160 | 0.5248 | 0.5579 | 0 |
| arousal | midpoint_as_high | ce_class_weighted | 0.5313 | 0.5416 | 0.5338 | 0 |

## Best Policy Per Task

| Task | Best policy | Recipe | Macro F1 | Balanced acc | Interpretation |
|---|---|---|---:|---:|---|
| valence | discard_midpoint | balanced_sampler_ce | 0.5066 | 0.5219 | pending human review |
| arousal | midpoint_as_high | ce_class_weighted | 0.5313 | 0.5416 | pending human review |

## Next Step

Use the combined label-policy report for human review before locking any final policy.

