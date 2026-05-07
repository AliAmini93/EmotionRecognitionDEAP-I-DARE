# I-DARE Representation and Label-task Redesign Diagnostic Report

## Status

Representation/label-task diagnostic complete; pending human review.

Generated UTC: `2026-05-07T16:05:47.556677+00:00`

This report is read-only. No new model training was run.

## Executive Diagnosis

- Leading blocker: `label_task_subject_dependence`
- Diagnosis: `subject_relative_label_task_problem_supported`
- Recommended next objective: `subject_relative_task_formulation_objective`

- Per-subject label balance/skew is large enough that global binary labels are likely unstable under subject-heldout evaluation.
- A subject-relative task formulation should be tested before architecture, fusion, or augmentation.

## Label and Task Evidence

| Metric | Value |
|---|---:|
| mean_exact_midpoint_fraction | 0.1404 |
| mean_near_midpoint_fraction | 0.1404 |
| max_subject_prop_skew_midpoint_as_high | 0.4891 |
| mean_subject_prop_skew_midpoint_as_high | 0.1022 |
| high_skew_subject_rows_ge_0p20 | 32.0000 |
| n_subject_balance_rows | 252.0000 |

Discovered rating/label columns:

| Modality | Valence column | Arousal column |
|---|---|---|
| EEG | `valence_score` | `arousal_score` |
| EMG | `valence_score` | `arousal_score` |

### Highest Subject Label-skew Rows

| Mod | Task | Subject | Fold | N | Rating mean | Midpoint frac | Near-mid frac | Prop high | Abs skew | Error rate |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| EEG | arousal | 6 | 1 | 32 | 7.5312 | 0.0000 | 0.0000 | 0.9375 | 0.4891 | 0.4531 |
| EMG | arousal | 6 | 1 | 32 | 7.5312 | 0.0000 | 0.0000 | 0.9375 | 0.4891 | 0.1172 |
| EMG | arousal | 41 | 6 | 32 | 2.3750 | 0.0000 | 0.0000 | 0.0000 | 0.4484 | 0.5195 |
| EEG | arousal | 41 | 6 | 32 | 2.3750 | 0.0000 | 0.0000 | 0.0000 | 0.4484 | 0.4062 |
| EEG | arousal | 13 | 1 | 32 | 2.3750 | 0.0625 | 0.0625 | 0.0625 | 0.3859 | 0.4229 |
| EMG | arousal | 13 | 1 | 32 | 2.3750 | 0.0625 | 0.0625 | 0.0625 | 0.3859 | 0.3729 |
| EMG | arousal | 55 | 4 | 32 | 2.0938 | 0.0938 | 0.0938 | 0.0938 | 0.3547 | 0.2978 |
| EEG | arousal | 55 | 4 | 32 | 2.0938 | 0.0938 | 0.0938 | 0.0938 | 0.3547 | 0.2670 |
| EEG | arousal | 42 | 4 | 32 | 6.3438 | 0.0938 | 0.0938 | 0.7812 | 0.3328 | 0.5641 |
| EMG | arousal | 2 | 2 | 32 | 6.5000 | 0.0938 | 0.0938 | 0.7812 | 0.3328 | 0.5325 |
| EEG | arousal | 2 | 2 | 32 | 6.5000 | 0.0938 | 0.0938 | 0.7812 | 0.3328 | 0.5043 |
| EMG | arousal | 42 | 4 | 32 | 6.3438 | 0.0938 | 0.0938 | 0.7812 | 0.3328 | 0.4406 |
| EEG | arousal | 7 | 1 | 32 | 3.2812 | 0.1250 | 0.1250 | 0.1250 | 0.3234 | 0.6088 |
| EMG | arousal | 7 | 1 | 32 | 3.2812 | 0.1250 | 0.1250 | 0.1250 | 0.3234 | 0.2974 |
| EEG | arousal | 49 | 2 | 32 | 2.6562 | 0.1250 | 0.1250 | 0.1562 | 0.2922 | 0.2188 |

## Representation-signal Evidence

| Metric | Value |
|---|---:|
| mean_subject_eta | 0.3551 |
| mean_label_eta | 0.0006 |
| median_subject_to_label_eta_ratio | 651.9177 |
| max_subject_to_label_eta_ratio | 1593.5411 |
| subject_dominance_rows | 12.0000 |
| n_representation_rows | 12.0000 |

### Strongest Subject-vs-label Dominance Rows

| Mod | Task | Policy | N | Features | Subject eta | Label eta | Ratio | Max label corr | Centroid sep | Subject dominated |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| EEG | valence | midpoint_as_low | 2016 | 96 | 0.4419 | 0.0003 | 1593.5411 | 0.0543 | 0.0366 | True |
| EEG | valence | discard_midpoint | 1667 | 96 | 0.4419 | 0.0004 | 1221.2174 | 0.0624 | 0.0411 | True |
| EEG | valence | midpoint_as_high | 2016 | 96 | 0.4419 | 0.0005 | 912.2014 | 0.0600 | 0.0486 | True |
| EMG | valence | midpoint_as_high | 2016 | 22 | 0.2683 | 0.0003 | 890.1365 | 0.0273 | 0.0554 | True |
| EMG | valence | midpoint_as_low | 2016 | 22 | 0.2683 | 0.0003 | 846.7433 | 0.0317 | 0.0571 | True |
| EMG | valence | discard_midpoint | 1667 | 22 | 0.2683 | 0.0003 | 782.0365 | 0.0295 | 0.0612 | True |
| EMG | arousal | midpoint_as_high | 2016 | 22 | 0.2683 | 0.0005 | 521.7988 | 0.0468 | 0.0716 | True |
| EEG | arousal | midpoint_as_low | 2016 | 96 | 0.4419 | 0.0011 | 419.6193 | 0.1000 | 0.0745 | True |
| EEG | arousal | midpoint_as_high | 2016 | 96 | 0.4419 | 0.0012 | 373.4783 | 0.0910 | 0.0753 | True |
| EMG | arousal | discard_midpoint | 1799 | 22 | 0.2683 | 0.0008 | 348.3243 | 0.0518 | 0.0905 | True |
| EMG | arousal | midpoint_as_low | 2016 | 22 | 0.2683 | 0.0008 | 341.7058 | 0.0447 | 0.0919 | True |
| EEG | arousal | discard_midpoint | 1799 | 96 | 0.4419 | 0.0013 | 336.3376 | 0.1096 | 0.0808 | True |

## Recommendation

Recommended next objective: `subject_relative_task_formulation_objective`

Reasoning:

- Per-subject label balance/skew is large enough that global binary labels are likely unstable under subject-heldout evaluation.
- A subject-relative task formulation should be tested before architecture, fusion, or augmentation.

## Expected Review Decision

Human review should decide whether to accept this blocker diagnosis and create the recommended next objective.

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

Human review / closeout of this representation and label-task diagnostic report.

Do not start fusion, architecture changes, augmentation, DG, broad hyperparameter search, or final claims from this report alone.
