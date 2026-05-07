# I-DARE Subject-relative Task Formulation Report

## Status

Subject-relative task formulation diagnostic/design report complete; pending human review.

Generated UTC: `2026-05-07T16:16:55.745021+00:00`

No new model training was run.

## Executive Recommendation

- Selected formulation: `subject_top_bottom_quantile_q33`
- Recommended next objective: `minimal_subject_relative_training_objective`

- The formulation is subject-relative and directly targets the diagnosed label/task subject-dependence blocker.
- It provides better within-subject class balance than global binary labels.
- It can be evaluated with the existing subject-heldout folds if the task definition is frozen before model fitting.
- A future run must be explicitly small and controlled; this report does not authorize training by itself.

## Candidate Matrix

| Mod | Task | Formulation | Coverage / usable | Prop high | Mean subj gap | Max subj gap | Mean fold gap | Empty subjects | Leakage risk | Score |
|---|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| EEG | valence | `subject_zscore_sign` | 0.9975 | 0.5316 | 0.0683 | 0.1875 | 0.0317 | 0 | medium | 0.8475 |
| EMG | valence | `subject_zscore_sign` | 0.9975 | 0.5316 | 0.0683 | 0.1875 | 0.0317 | 0 | medium | 0.8475 |
| EMG | arousal | `subject_zscore_sign` | 0.9960 | 0.4706 | 0.0780 | 0.2188 | 0.0325 | 0 | medium | 0.8355 |
| EEG | arousal | `subject_zscore_sign` | 0.9960 | 0.4706 | 0.0780 | 0.2188 | 0.0325 | 0 | medium | 0.8355 |
| EEG | valence | `subject_median_split` | 0.8313 | 0.5048 | 0.0338 | 0.1500 | 0.0067 | 0 | medium | 0.7409 |
| EMG | valence | `subject_median_split` | 0.8313 | 0.5048 | 0.0338 | 0.1500 | 0.0067 | 0 | medium | 0.7409 |
| EMG | arousal | `subject_median_split` | 0.8403 | 0.5089 | 0.0528 | 0.5000 | 0.0221 | 0 | medium | 0.7153 |
| EEG | arousal | `subject_median_split` | 0.8403 | 0.5089 | 0.0528 | 0.5000 | 0.0221 | 0 | medium | 0.7153 |
| EMG | valence | `subject_top_bottom_quantile_q33` | 0.8080 | 0.4911 | 0.0481 | 0.1562 | 0.0228 | 0 | medium | 0.6871 |
| EEG | valence | `subject_top_bottom_quantile_q33` | 0.8080 | 0.4911 | 0.0481 | 0.1562 | 0.0228 | 0 | medium | 0.6871 |
| EEG | arousal | `subject_top_bottom_quantile_q33` | 0.8150 | 0.4851 | 0.0405 | 0.1562 | 0.0184 | 1 | medium | 0.6761 |
| EMG | arousal | `subject_top_bottom_quantile_q33` | 0.8150 | 0.4851 | 0.0405 | 0.1562 | 0.0184 | 1 | medium | 0.6761 |
| EMG | valence | `within_subject_pairwise_or_ranking_task` | 0.8562 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0 | medium_high | 0.6362 |
| EEG | valence | `within_subject_pairwise_or_ranking_task` | 0.8562 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0 | medium_high | 0.6362 |
| EEG | arousal | `within_subject_pairwise_or_ranking_task` | 0.8351 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0 | medium_high | 0.6151 |
| EMG | arousal | `within_subject_pairwise_or_ranking_task` | 0.8351 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0 | medium_high | 0.6151 |

## Average Formulation Scores

| Formulation | Mean score | Mean coverage | Mean subj gap | Mean fold gap | Empty subjects |
|---|---:|---:|---:|---:|---:|
| `subject_zscore_sign` | 0.8415 | 0.9968 | 0.0732 | 0.0321 | 0 |
| `subject_median_split` | 0.7281 | 0.8358 | 0.0433 | 0.0144 | 0 |
| `subject_top_bottom_quantile_q33` | 0.6816 | 0.8115 | 0.0443 | 0.0206 | 2 |
| `within_subject_pairwise_or_ranking_task` | 0.6257 | 0.8457 | 0.0000 | 0.0000 | 0 |

## Leakage and Scientific Validity Audit

| Formulation | Leakage risk | Scientifically valid | Notes |
|---|---|---|---|
| `subject_median_split` | medium | True | Uses each subject's own rating distribution to define low/high. Valid for subject-relative affect if labels are available for evaluation, but not a deployment classifier without subject calibration. |
| `subject_zscore_sign` | medium | True | Uses each subject's own mean/std. Similar leakage profile to median split, slightly more sensitive to outliers. |
| `subject_top_bottom_quantile_q33` | medium | True | Uses only within-subject extremes and discards ambiguous middle trials. Lower coverage but cleaner labels. |
| `within_subject_pairwise_or_ranking_task` | medium_high | conditional | Best matches within-subject affective ordering, but requires a different pairwise/ranking training objective and careful subject-heldout evaluation design. |

## Future Controlled Run Matrix Draft

This is only a draft for the next objective. It is not authorized by this report.

| Dimension | Draft value |
|---|---|
| Task formulation | `subject_top_bottom_quantile_q33` |
| Modalities | EEG STIM-BSL-only, EMG feature-only |
| Tasks | valence, arousal |
| Folds | sidecar-compatible 6 folds, seed 11 |
| Recipes | start with `ce_class_weighted` only, then add `balanced_sampler_ce` only if the first pass is valid |
| Matrix size | minimal first pass: 24 runs; optional recipe pass: +24 runs |
| Claim level | diagnostic only, no final LOSO claim |

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- final global label-policy lock
- new model training
- architecture ablation for improvement
- data augmentation
- SupCon / VREx / domain generalization
- broad hyperparameter search
- mainline change

## Next Allowed Step

Human review / closeout of this subject-relative task formulation report.

If accepted, create a separate minimal controlled training objective. Do not start training from this report alone.
