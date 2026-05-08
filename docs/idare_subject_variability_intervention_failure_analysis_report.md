# I-DARE Subject-variability Intervention-failure Analysis Report

## Status

Read-only intervention-failure analysis complete.

Generated UTC: `2026-05-08T08:56:44.158159+00:00`

Objective:

- `docs/idare_subject_variability_intervention_failure_analysis_objective.md`

Parent review:

- `docs/idare_subject_relative_preprocessed_minimal_training_review_status.md`

## Executive Diagnosis

`subject_variability_diagnosis_still_supported_intervention_too_weak`

The failed subject-relative + preprocessing first pass does **not** falsify the subject-variability diagnosis.

It shows that the tested intervention was not strong enough or not specific enough: it changed labels and preprocessing, but it did not explicitly force cross-subject affective alignment or suppress subject identity in the learned representation.

Recommended next objective:

- `subject_variability_supcon_dg_design_objective`

## What Failed

The tested intervention combined:

- subject-relative `top/bottom q33` labels
- EEG window/channel z-score summary preprocessing
- EMG signed-log1p preprocessing
- train-fold-only scaling
- CE-only first-pass training

Overall preprocessed subject-relative result:

- completed fold/task runs: `24`
- mean macro-F1: `0.5028`
- median macro-F1: `0.4974`
- runs below macro-F1 0.50: `13`
- runs at or above macro-F1 0.55: `2`

## Fold/Task Aggregate

| Modality | Task | Folds | Mean macro-F1 | Median macro-F1 | Min | Max | Folds < 0.50 | Folds >= 0.55 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| EEG | arousal | 6 | 0.4792 | 0.4880 | 0.4327 | 0.5072 | 5 | 0 |
| EEG | valence | 6 | 0.4961 | 0.4978 | 0.4612 | 0.5487 | 3 | 0 |
| EMG | arousal | 6 | 0.5086 | 0.5072 | 0.4683 | 0.5403 | 3 | 0 |
| EMG | valence | 6 | 0.5273 | 0.5321 | 0.4901 | 0.5655 | 2 | 2 |

Full fold/task table:

- `docs/idare_subject_variability_intervention_failure_fold_task_summary.csv`

## Why This Does Not Invalidate Subject Variability

The key distinction is:

1. The diagnosis may still be correct.
2. The intervention may have been too weak.

Preprocessing can reduce scale or distribution differences, but it does not necessarily learn a subject-invariant affective representation.

The current evidence favors this interpretation:

- the sanity tests previously showed the pipeline can learn/memorize, so the pipeline is not simply dead.
- the root-cause diagnostics previously pointed to subject/fold generalization as a leading blocker.
- the preprocessed first pass remained near chance/mixed.
- the tested CE-only objective had no mechanism to pull same-affect samples across subjects together.

## Intervention Adequacy

Preprocessing diagnostic context:

- preprocessing diagnosis: `preprocessing_candidate_worth_testing`
- selected candidate: `{'modality': 'EMG', 'candidate': 'emg_signed_log1p_train_standard_scaled', 'description': 'signed log1p EMG features plus train-only standard scaling', 'diagnostic_score': 0.5219554947235828, 'mean_shift_reduction_vs_raw': 0.21727928519248962, 'mean_val_sep_gain_vs_raw': -0.007143065954248111, 'leakage_risk': 'low', 'implementation_risk': 'low'}`
- selected candidate shift reduction: `NA`
- selected candidate validation-separation gain: `NA`

Interpretation:

- If preprocessing reduces distribution shift but does not improve class separation, it should not be expected to fix subject-heldout affect recognition by itself.
- The failed training pass is therefore best read as an intervention failure, not as proof that subject variability is irrelevant.

## Failure Reason Ranking

| Rank | Failure reason | Confidence | Evidence |
|---:|---|---|---|
| 1 | Intervention targeted scale/distribution more than cross-subject affective alignment. | high | Preprocessing was weak/diagnostic and first-pass macro-F1 remained near chance. |
| 2 | CE-only objective does not explicitly suppress subject identity or align same-affect samples across subjects. | medium-high | Previous diagnostics found subject-dominated representations; current CE-only preprocessed run was insufficient. |
| 3 | Subject-relative labels improved balance/definition but did not guarantee separable affective representation. | medium | Both EEG and EMG subject-relative preprocessed runs remain mixed across folds/tasks. |
| 4 | Some fold/task effects persist, so the problem is not localized to one isolated run. | medium | 13 of 24 fold-task runs are below macro-F1 0.50. |

## Next-method Decision Matrix

| Candidate next method | Directly targets subject variability? | Decision | Recommended scope |
|---|---|---|---|
| Affective SupCon across subjects | yes | justified_as_next_design_candidate | implementation/spec objective before training; lock positive/negative pairs and sampler |
| VREx / domain generalization | yes | justified_as_next_design_candidate | pair with CE and optionally SupCon in controlled first pass |
| Generic feature engineering | weakly | pause_as_primary_next_step | only after subject-targeted methods are specified or if analysis later rejects subject-variability hypothesis |
| Subject-aware calibration/adaptation | yes_if_protocol_allows | defer_until_protocol_question | separate protocol objective if allowed by research claim |
| Further task/label redesign | partly | keep_as_backup_path | revisit after SupCon/DG design decision or if within-subject signal is weak |

Full decision matrix:

- `docs/idare_subject_variability_intervention_failure_decision_matrix.csv`

## SupCon / DG Interpretation

Affective SupCon and VREx / domain generalization are justified as the next **design target**, but not as an immediate unreviewed training run.

They are justified because they directly address the remaining failure mode:

- SupCon can pull same-affect samples from different subjects together.
- hard negatives can separate same-stimulus but different-reported-affect cases.
- VREx/DG can penalize risk instability across subject environments.

However, they require a locked implementation design before training:

- positive-pair definition
- negative-pair and hard-negative definition
- batch sampler guaranteeing cross-subject positives
- subject/environment definition
- loss weights and schedule
- leakage controls
- train-fold-only preprocessing

## Recommendation

Create a new design/spec objective:

- `docs/idare_subject_variability_supcon_dg_design_objective.md`
- `docs/idare_subject_variability_supcon_dg_design_objective.json`

This objective should study the existing project docs and lock the SupCon/DG implementation details before any training.

## Next Allowed Step

Human review / closeout of this report, then create the SupCon/DG design objective if accepted.

## Not Authorized

- EEG+EMG fusion
- final LOSO / final paper claim
- mainline change
- broad hyperparameter search
- direct SupCon/DG training without design/spec review
- generic feature engineering as the primary next step
