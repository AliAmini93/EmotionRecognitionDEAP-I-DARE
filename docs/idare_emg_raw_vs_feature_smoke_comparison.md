# I-DARE EMG Raw-vs-Feature Smoke Comparison

This report compares the frozen I-DARE EMG feature-only and raw EMG-only smoke results.

This is a smoke/stabilization comparison, not a final LOSO result.

## Sources

- feature / valence: `docs/idare_emg_feature_valence_training_smoke.json`
- feature / arousal: `docs/idare_emg_feature_arousal_training_smoke.json`
- raw / valence: `docs/idare_raw_emg_valence_training_smoke.json`
- raw / arousal: `docs/idare_raw_emg_arousal_training_smoke.json`

## Aggregate Comparison

| Representation | Task | Recipe | Runs | Final macro F1 | Final bal acc | Final acc | Threshold macro F1 | Threshold bal acc | Threshold | Majority acc | One-class runs |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| feature | arousal | balanced_sampler_ce | 2 | 0.5065 | 0.5130 | 0.5142 | 0.5202 | 0.5235 | 0.5250 | 0.5838 | 0 |
| feature | arousal | ce_class_weighted | 2 | 0.5223 | 0.5319 | 0.5327 | 0.5223 | 0.5319 | 0.5000 | 0.5838 | 0 |
| raw | arousal | balanced_sampler_ce | 2 | 0.4464 | 0.4969 | 0.4787 | 0.5187 | 0.5294 | 0.8750 | 0.5625 | 0 |
| raw | arousal | ce_class_weighted | 2 | 0.4131 | 0.5006 | 0.5170 | 0.4761 | 0.5086 | 0.5000 | 0.5625 | 0 |
| feature | valence | balanced_sampler_ce | 2 | 0.4776 | 0.4935 | 0.5511 | 0.4798 | 0.4902 | 0.5250 | 0.6065 | 0 |
| feature | valence | ce_class_weighted | 2 | 0.5004 | 0.5083 | 0.5156 | 0.5004 | 0.5083 | 0.5000 | 0.6065 | 0 |
| raw | valence | balanced_sampler_ce | 2 | 0.4607 | 0.5318 | 0.5199 | 0.5067 | 0.5290 | 0.4250 | 0.5753 | 0 |
| raw | valence | ce_class_weighted | 2 | 0.4863 | 0.5000 | 0.5085 | 0.4945 | 0.5005 | 0.5000 | 0.5753 | 0 |

## Best Rows by Metric

### Final macro F1

| Task | Representation | Recipe | Value |
|---|---|---|---:|
| arousal | feature | ce_class_weighted | 0.5223 |
| valence | feature | ce_class_weighted | 0.5004 |

### Final balanced accuracy

| Task | Representation | Recipe | Value |
|---|---|---|---:|
| arousal | feature | ce_class_weighted | 0.5319 |
| valence | raw | balanced_sampler_ce | 0.5318 |

### Threshold macro F1

| Task | Representation | Recipe | Value |
|---|---|---|---:|
| arousal | feature | ce_class_weighted | 0.5223 |
| valence | raw | balanced_sampler_ce | 0.5067 |

### Threshold balanced accuracy

| Task | Representation | Recipe | Value |
|---|---|---|---:|
| arousal | feature | ce_class_weighted | 0.5319 |
| valence | raw | balanced_sampler_ce | 0.5290 |

## Interpretation

- For valence, feature-level and raw EMG are close, but feature-level `ce_class_weighted` has the best final macro F1 among the current smoke rows.
- For arousal, feature-level EMG is clearly stronger than raw EMG on final macro F1 and final balanced accuracy.
- Raw EMG threshold sweeps can improve some rows, but the thresholds are unstable, which suggests calibration sensitivity.
- No one-class final collapse was observed in these smoke rows.

## Decision

- Mainline I-DARE EMG representation: `feature-level EMG`.
- Keep raw EMG-only as an ablation, not the main EMG path.
- Next practical step: start EEG+EMG fusion smoke using the feature-level EMG cache first.
