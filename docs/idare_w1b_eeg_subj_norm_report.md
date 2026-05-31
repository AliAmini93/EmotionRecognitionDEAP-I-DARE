# W1B — EEG Subject Normalization Report

- status: `complete_pending_control_tower_review`
- branch: `idare/wave1/eeg-subject-normalization`
- reference: `REF-PW-EEG-ARO-001` mean balanced accuracy `0.5216709095`
- registered runs: `24`

## Scope

- I-DARE only.
- EEG only.
- Arousal only.
- Current STIM-BSL summary input fixed.
- Within-subject pairwise affect preference ranking.
- Ridge classifier fixed.
- No neural training, no DEAP, no fusion, no rereference/CAR, no downsampling rebuild, no cache overwrite.

## Methodology Note

B1 and B3 are explicitly transductive because they use unlabeled held-out subject feature statistics. They are diagnostic/calibration-style conditions only and must not be reported as strict non-transductive results.

## Summary

| cell_id | cell_name | transductive | mean_balanced_accuracy | delta_vs_ref_mean_balanced_accuracy | fold_stdev_balanced_accuracy | fold_stdev_delta_vs_B0 | bimodal_gap_top3_minus_bottom3 | bimodal_gap_delta_vs_B0 | positive_fold_count_bal_acc_gt_0_5 | positive_fold_count_vs_B0 | moderate_pass_mean_bal_acc_ge_0_53 | strong_pass_mean_bal_acc_ge_0_55 | heterogeneity_pass_candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B0 | none_current | False | 0.514987 | -0.006684 | 0.012990 | 0.000000 | 0.020606 | 0.000000 | 5 |  | False | False | False |
| B1 | per_subject_zscore_transductive | True | 0.508142 | -0.013529 | 0.013971 | 0.000981 | 0.019843 | -0.000763 | 4 | 2 | False | False | False |
| B2 | train_fold_standard_scaler_nontransductive | False | 0.514987 | -0.006684 | 0.012990 | 0.000000 | 0.020606 | 0.000000 | 5 | 0 | False | False | False |
| B3 | per_subject_rank_transform_transductive | True | 0.527786 | 0.006115 | 0.006535 | -0.006456 | 0.008848 | -0.011758 | 6 | 5 | False | False | True |

## Diagnosis

`heterogeneity_pass_candidate_observed`

## Output Files

- runs_csv: `docs/idare_w1b_eeg_subj_norm_runs.csv`
- fold_diagnostics_csv: `docs/idare_w1b_eeg_subj_norm_fold_diagnostics.csv`
- report_md: `docs/idare_w1b_eeg_subj_norm_report.md`
- report_json: `docs/idare_w1b_eeg_subj_norm_report.json`
- closeout_md: `docs/idare_w1b_eeg_subj_norm_closeout.md`
- closeout_json: `docs/idare_w1b_eeg_subj_norm_closeout.json`

