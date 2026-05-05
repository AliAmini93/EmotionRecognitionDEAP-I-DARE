# I-DARE Valence Fold-Bias Diagnostics

This diagnostic reads the cache index and existing smoke JSON only.

It does not train a model and does not load raw MATLAB/HDF5 files.

## Inputs

- cache_index: `.cache/idare_eeg_cache_index.csv`
- smoke_json: `docs/idare_eeg_cache_recipe_stabilization_valence_threshold_aggregate_compare_smoke.json`
- label_col: `valence_midpoint_as_high`

## Run-Level Diagnostics

| Run | Recipe | Fold | Train 0 | Train 1 | Val 0 | Val 1 | Pred 0 | Pred 1 | Macro F1 | Bal acc | P1 mean | P1 median | Best threshold |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | ce_class_weighted | 1 | 671 | 993 | 141 | 211 | 274 | 78 | 0.4394 | 0.5133 | 0.4909 | 0.4911 | 0.50 |
| 2 | balanced_sampler_ce | 1 | 671 | 993 | 141 | 211 | 103 | 249 | 0.4982 | 0.5044 | 0.5146 | 0.5194 | 0.50 |
| 3 | ce_class_weighted | 2 | 671 | 993 | 141 | 211 | 3 | 349 | 0.3889 | 0.5047 | 0.5235 | 0.5234 | 0.50 |
| 4 | balanced_sampler_ce | 2 | 671 | 993 | 141 | 211 | 1 | 351 | 0.3825 | 0.5035 | 0.5294 | 0.5300 | 0.50 |

## Interpretation

- This file is diagnostic only.
- It is intended to explain fold/class-bias behavior before any broader run.
- If fold 2 has near-collapse despite similar validation label counts, the issue is more likely model/probability bias than a trivial validation-label imbalance.
- Any follow-up should remain smoke-first.
