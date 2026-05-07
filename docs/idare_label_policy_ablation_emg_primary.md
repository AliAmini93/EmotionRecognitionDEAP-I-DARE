# I-DARE Label-Policy Ablation: EMG feature-only

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
| valence | discard_midpoint | ce_class_weighted | 0.5043 | 0.5055 | 0.5056 | 0 |
| valence | midpoint_as_low | ce_class_weighted | 0.5018 | 0.5072 | 0.5070 | 0 |
| valence | midpoint_as_high | ce_class_weighted | 0.5140 | 0.5202 | 0.5226 | 0 |
| arousal | discard_midpoint | ce_class_weighted | 0.5253 | 0.5365 | 0.5396 | 0 |
| arousal | midpoint_as_low | balanced_sampler_ce | 0.5124 | 0.5331 | 0.5268 | 0 |
| arousal | midpoint_as_high | ce_class_weighted | 0.5159 | 0.5192 | 0.5211 | 0 |

## Best Policy Per Task

| Task | Best policy | Recipe | Macro F1 | Balanced acc | Interpretation |
|---|---|---|---:|---:|---|
| valence | midpoint_as_high | ce_class_weighted | 0.5140 | 0.5202 | pending human review |
| arousal | discard_midpoint | ce_class_weighted | 0.5253 | 0.5365 | pending human review |

## Next Step

Use the combined label-policy report for human review before locking any final policy.

