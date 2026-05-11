# W1D Feature Discriminability Closeout

## Branch

`idare/wave1/feature-discriminability`

## Scope

- I-DARE only.
- EEG and EMG.
- Arousal and valence.
- Read-only feature discriminability analysis.
- 0 training runs.
- No fusion.
- No DEAP.
- No cache overwrite.
- No push to main.

## Outputs

```text
docs/idare_w1d_feat_discrim_objective.md
scripts/idare_w1d_feat_discrim_audit.py
docs/idare_w1d_feat_discrim_report.md
docs/idare_w1d_feat_discrim_report.json
docs/idare_w1d_feat_discrim_top_features.csv
docs/idare_w1d_feat_discrim_decision_matrix.md
docs/idare_w1d_feat_discrim_closeout.md
```

## Main Finding

Current I-DARE EEG/EMG features are not completely label-signal-free, but the usable label signal is primarily within-subject.

Cross-subject label discriminability is weak after subject centering, while subject identity strongly dominates feature geometry.

## Key Results

| Modality | Task | Cross-subject centered top-k d | Within-subject top-k d | Subject/label eta2 ratio | Diagnosis |
|---|---:|---:|---:|---:|---|
| EEG | valence | 0.1066 | 0.8023 | 893.72 | within-subject signal, cross-subject collapse |
| EEG | arousal | 0.1035 | 0.8389 | 364.05 | within-subject signal, cross-subject collapse |
| EMG | valence | 0.0368 | 0.3568 | 890.14 | within-subject signal, cross-subject collapse |
| EMG | arousal | 0.0322 | 0.3390 | 521.80 | within-subject signal, cross-subject collapse |

## Official Diagnosis

```text
within_subject_signal_present_cross_subject_signal_collapses_subject_normalization_or_domain_generalization_priority
```

## Interpretation

W1D does not support the claim that current EEG/EMG features contain no affective signal at all.

Instead, W1D supports this diagnosis:

```text
within-subject signal exists,
cross-subject signal is weak,
subject identity dominates feature geometry.
```

If classifiers remain weak, the likely bottleneck is not simply absence of signal. The more likely bottleneck is subject normalization, domain generalization, preprocessing/formulation, or evaluation formulation.

## Decision Impact

Recommended priority after W1D:

1. Treat subject normalization / subject-invariant formulation as a priority.
2. Do not expand to bigger training runs merely to compensate for this failure mode.
3. Use W1D as evidence that current EEG/EMG features have within-subject affective structure but poor cross-subject portability.
4. Keep EMG as diagnostic/auxiliary until cross-subject utility improves; EMG shows weaker cross-subject signal than EEG.
5. Consider follow-up branches that explicitly test subject normalization, domain generalization, or subject-invariant representations.

## Limitations

- EEG discriminability was computed from diagnostic channel-level summary features derived from the EEG window cache, not from a trained representation.
- EMG used the existing feature cache directly.
- No classifier was trained.
- This closeout is diagnostic only and is not final model performance evidence.

## Final W1D Decision

W1D is complete.

Final classification:

```text
within_subject_signal_present_cross_subject_signal_collapses_subject_normalization_or_domain_generalization_priority
```
