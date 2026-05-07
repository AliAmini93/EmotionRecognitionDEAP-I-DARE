# I-DARE Failure Analysis Report

## Status

Failure analysis complete; pending human review.

No new training was run for this report.

Evidence level: post-hoc analysis of existing smoke/stabilization outputs, not final LOSO performance.

## Validation

- Total prediction sources analyzed: 6
- Total reconstructed runs: 240
- Fold summary CSV: `docs/idare_failure_analysis_fold_summary.csv`

## Failure-label counts

| Failure label | Aggregate rows |
| --- | --- |
| fold_specific_instability | 13 |
| no_major_failure_flag | 8 |
| prediction_skew | 1 |
| weak_signal_near_chance | 27 |

## Best label policy by modality/task

| Modality | Task | Best policy | Recipe | Macro F1 | Balanced acc |
| --- | --- | --- | --- | --- | --- |
| EEG | arousal | `midpoint_as_high` | `ce_class_weighted` | 0.5313 | 0.5416 |
| EEG | valence | `discard_midpoint` | `balanced_sampler_ce` | 0.5066 | 0.5219 |
| EMG | arousal | `discard_midpoint` | `ce_class_weighted` | 0.5253 | 0.5365 |
| EMG | valence | `midpoint_as_high` | `ce_class_weighted` | 0.5140 | 0.5202 |

## Best representation by modality/task in broader single-modality matrix

| Modality | Task | Best representation | Policy | Recipe | Macro F1 | Balanced acc |
| --- | --- | --- | --- | --- | --- | --- |
| EEG | arousal | STIM-BSL+BSL-stats | `midpoint_as_high` | `balanced_sampler_ce` | 0.5302 | 0.5427 |
| EEG | valence | STIM-BSL-only | `midpoint_as_high` | `ce_class_weighted` | 0.5073 | 0.5196 |
| EMG | arousal | feature-only | `midpoint_as_high` | `ce_class_weighted` | 0.5159 | 0.5192 |
| EMG | valence | feature-only | `midpoint_as_high` | `ce_class_weighted` | 0.5140 | 0.5202 |

## Aggregate failure map

| Matrix | Modality | Representation | Task | Policy | Recipe | Macro F1 | Bal acc | Delta macro vs majority | Pred skew | Weakest fold | Labels |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| broader_single_modality | EEG | STIM-BSL+BSL-stats | arousal | `midpoint_as_high` | `balanced_sampler_ce` | 0.5302 | 0.5427 | 0.1736 | 0.5855 | 2 | `no_major_failure_flag` |
| broader_single_modality | EEG | STIM-BSL+BSL-stats | arousal | `midpoint_as_high` | `ce_class_weighted` | 0.5059 | 0.5273 | 0.1492 | 0.6741 | 2 | `no_major_failure_flag` |
| broader_single_modality | EEG | STIM-BSL-only | arousal | `midpoint_as_high` | `balanced_sampler_ce` | 0.5029 | 0.5164 | 0.1463 | 0.6359 | 1 | `weak_signal_near_chance` |
| broader_single_modality | EEG | STIM-BSL-only | arousal | `midpoint_as_high` | `ce_class_weighted` | 0.5103 | 0.5151 | 0.1536 | 0.6391 | 5 | `weak_signal_near_chance`, `fold_specific_instability` |
| broader_single_modality | EEG | STIM-BSL+BSL-stats | valence | `midpoint_as_high` | `balanced_sampler_ce` | 0.4832 | 0.5104 | 0.1091 | 0.6259 | 2 | `weak_signal_near_chance`, `fold_specific_instability` |
| broader_single_modality | EEG | STIM-BSL+BSL-stats | valence | `midpoint_as_high` | `ce_class_weighted` | 0.4835 | 0.5078 | 0.1094 | 0.6928 | 5 | `weak_signal_near_chance`, `fold_specific_instability` |
| broader_single_modality | EEG | STIM-BSL-only | valence | `midpoint_as_high` | `balanced_sampler_ce` | 0.4891 | 0.4939 | 0.1151 | 0.6557 | 4 | `weak_signal_near_chance` |
| broader_single_modality | EEG | STIM-BSL-only | valence | `midpoint_as_high` | `ce_class_weighted` | 0.5073 | 0.5196 | 0.1332 | 0.6769 | 1 | `weak_signal_near_chance` |
| broader_single_modality | EMG | feature+BSL-stats | arousal | `midpoint_as_high` | `balanced_sampler_ce` | 0.5103 | 0.5143 | 0.1537 | 0.5565 | 5 | `weak_signal_near_chance` |
| broader_single_modality | EMG | feature+BSL-stats | arousal | `midpoint_as_high` | `ce_class_weighted` | 0.4966 | 0.5015 | 0.1399 | 0.5791 | 6 | `weak_signal_near_chance`, `fold_specific_instability` |
| broader_single_modality | EMG | feature-only | arousal | `midpoint_as_high` | `balanced_sampler_ce` | 0.5131 | 0.5196 | 0.1565 | 0.5616 | 2 | `weak_signal_near_chance` |
| broader_single_modality | EMG | feature-only | arousal | `midpoint_as_high` | `ce_class_weighted` | 0.5159 | 0.5192 | 0.1592 | 0.5581 | 2 | `weak_signal_near_chance` |
| broader_single_modality | EMG | feature+BSL-stats | valence | `midpoint_as_high` | `balanced_sampler_ce` | 0.5094 | 0.5200 | 0.1353 | 0.5760 | 3 | `no_major_failure_flag` |
| broader_single_modality | EMG | feature+BSL-stats | valence | `midpoint_as_high` | `ce_class_weighted` | 0.5116 | 0.5163 | 0.1375 | 0.5379 | 1 | `weak_signal_near_chance` |
| broader_single_modality | EMG | feature-only | valence | `midpoint_as_high` | `balanced_sampler_ce` | 0.4924 | 0.5174 | 0.1184 | 0.6383 | 6 | `weak_signal_near_chance`, `fold_specific_instability` |
| broader_single_modality | EMG | feature-only | valence | `midpoint_as_high` | `ce_class_weighted` | 0.5140 | 0.5202 | 0.1399 | 0.5515 | 1 | `no_major_failure_flag` |
| label_policy_ablation | EEG | STIM-BSL-only | arousal | `discard_midpoint` | `balanced_sampler_ce` | 0.5089 | 0.5206 | 0.1270 | 0.6535 | 1 | `fold_specific_instability` |
| label_policy_ablation | EEG | STIM-BSL-only | arousal | `discard_midpoint` | `ce_class_weighted` | 0.4787 | 0.5074 | 0.0969 | 0.7078 | 3 | `weak_signal_near_chance`, `prediction_skew` |
| label_policy_ablation | EEG | STIM-BSL-only | arousal | `midpoint_as_high` | `balanced_sampler_ce` | 0.4966 | 0.5096 | 0.1400 | 0.6357 | 3 | `weak_signal_near_chance`, `fold_specific_instability` |
| label_policy_ablation | EEG | STIM-BSL-only | arousal | `midpoint_as_high` | `ce_class_weighted` | 0.5313 | 0.5416 | 0.1747 | 0.5790 | 2 | `no_major_failure_flag` |
| label_policy_ablation | EEG | STIM-BSL-only | arousal | `midpoint_as_low` | `balanced_sampler_ce` | 0.5160 | 0.5248 | 0.1187 | 0.6551 | 5 | `fold_specific_instability` |
| label_policy_ablation | EEG | STIM-BSL-only | arousal | `midpoint_as_low` | `ce_class_weighted` | 0.4961 | 0.5132 | 0.0987 | 0.6248 | 4 | `weak_signal_near_chance` |
| label_policy_ablation | EEG | STIM-BSL-only | valence | `discard_midpoint` | `balanced_sampler_ce` | 0.5066 | 0.5219 | 0.1663 | 0.6602 | 3 | `no_major_failure_flag` |
| label_policy_ablation | EEG | STIM-BSL-only | valence | `discard_midpoint` | `ce_class_weighted` | 0.4936 | 0.5045 | 0.1533 | 0.6214 | 3 | `weak_signal_near_chance` |
| label_policy_ablation | EEG | STIM-BSL-only | valence | `midpoint_as_high` | `balanced_sampler_ce` | 0.4904 | 0.5047 | 0.1163 | 0.6123 | 5 | `weak_signal_near_chance`, `fold_specific_instability` |
| label_policy_ablation | EEG | STIM-BSL-only | valence | `midpoint_as_high` | `ce_class_weighted` | 0.5014 | 0.5069 | 0.1273 | 0.6294 | 3 | `weak_signal_near_chance` |
| label_policy_ablation | EEG | STIM-BSL-only | valence | `midpoint_as_low` | `balanced_sampler_ce` | 0.4777 | 0.4908 | 0.1123 | 0.6135 | 6 | `weak_signal_near_chance` |
| label_policy_ablation | EEG | STIM-BSL-only | valence | `midpoint_as_low` | `ce_class_weighted` | 0.4721 | 0.4911 | 0.1066 | 0.6522 | 4 | `weak_signal_near_chance` |
| label_policy_ablation | EMG | feature-only | arousal | `discard_midpoint` | `balanced_sampler_ce` | 0.5055 | 0.5223 | 0.1237 | 0.5799 | 1 | `fold_specific_instability` |
| label_policy_ablation | EMG | feature-only | arousal | `discard_midpoint` | `ce_class_weighted` | 0.5253 | 0.5365 | 0.1435 | 0.5787 | 2 | `no_major_failure_flag` |
| label_policy_ablation | EMG | feature-only | arousal | `midpoint_as_high` | `balanced_sampler_ce` | 0.5131 | 0.5196 | 0.1565 | 0.5616 | 2 | `weak_signal_near_chance` |
| label_policy_ablation | EMG | feature-only | arousal | `midpoint_as_high` | `ce_class_weighted` | 0.5159 | 0.5192 | 0.1592 | 0.5581 | 2 | `weak_signal_near_chance` |
| label_policy_ablation | EMG | feature-only | arousal | `midpoint_as_low` | `balanced_sampler_ce` | 0.5124 | 0.5331 | 0.1151 | 0.5584 | 2 | `fold_specific_instability` |
| label_policy_ablation | EMG | feature-only | arousal | `midpoint_as_low` | `ce_class_weighted` | 0.5121 | 0.5287 | 0.1147 | 0.5948 | 2 | `fold_specific_instability` |
| label_policy_ablation | EMG | feature-only | valence | `discard_midpoint` | `balanced_sampler_ce` | 0.4971 | 0.5034 | 0.1568 | 0.5925 | 1 | `weak_signal_near_chance` |
| label_policy_ablation | EMG | feature-only | valence | `discard_midpoint` | `ce_class_weighted` | 0.5043 | 0.5055 | 0.1640 | 0.5375 | 1 | `weak_signal_near_chance` |
| label_policy_ablation | EMG | feature-only | valence | `midpoint_as_high` | `balanced_sampler_ce` | 0.4924 | 0.5174 | 0.1184 | 0.6383 | 6 | `weak_signal_near_chance`, `fold_specific_instability` |
| label_policy_ablation | EMG | feature-only | valence | `midpoint_as_high` | `ce_class_weighted` | 0.5140 | 0.5202 | 0.1399 | 0.5515 | 1 | `no_major_failure_flag` |
| label_policy_ablation | EMG | feature-only | valence | `midpoint_as_low` | `balanced_sampler_ce` | 0.4805 | 0.4877 | 0.1151 | 0.5795 | 3 | `weak_signal_near_chance` |
| label_policy_ablation | EMG | feature-only | valence | `midpoint_as_low` | `ce_class_weighted` | 0.5018 | 0.5072 | 0.1364 | 0.5597 | 1 | `weak_signal_near_chance` |

## Cross-modality weak-fold overlap

| Task | EEG bottom folds | EMG bottom folds | Shared | Interpretation |
| --- | --- | --- | --- | --- |
| arousal | [3] | [1, 2] | [] | complementary_or_policy_specific_failure_signal |
| valence | [5, 6] | [1, 6] | [6] | shared_failure_signal |

## Interpretation

- Current evidence remains smoke/stabilization-level and close to majority/chance behavior in many aggregates.
- Label-policy winners remain mixed by modality/task; no final global label policy should be locked.
- BSL-stats and label-policy changes do not yet justify fusion, architecture escalation, or final claims.
- The next useful improvement step should focus on calibration and fold/subject difficulty, using existing predictions first.

## Recommended next objective

`calibration_and_fold_difficulty_analysis`

- Most aggregate rows remain close to chance/majority baselines.
- Best label policies are mixed by modality/task, so no global label policy should be locked.
- Before architecture, augmentation, DG, or fusion, inspect fold difficulty and calibration/threshold behavior on existing predictions.
- Some rows are not hard failures, but gains are still smoke-level and need robustness evidence.
- Policy instability is present across modality/task winners.
- Some weak-fold overlap exists across modalities, suggesting split/subject difficulty should be inspected.

## Not authorized from this report

- new training from this report
- EEG+EMG fusion
- final LOSO / final paper claim
- locking final global label policy
- architecture ablation
- augmentation
- SupCon / VREx / domain generalization

## Next allowed step

Human review / closeout of this failure-analysis report. After review, create one explicit follow-up objective if needed.
