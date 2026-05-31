# W1A EEG Input Definition Report

- status: `complete`
- diagnosis: `no_gate_pass`
- fold_source: `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-w1a/docs/idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv`
- subject_column: `subject_id`
- arousal_rating_column: `arousal_score`

## Cell Summary

| cell | input_definition | runs | mean_balanced_accuracy | std_balanced_accuracy | delta_vs_REF_PW_EEG_ARO_001 | delta_vs_REF_BSL_EEG_ARO_001 | moderate_pass | strong_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | current_STIM_BSL_summary | 6 | 0.49986284463672437 | 0.021589717071821193 | -0.021808064863275578 | -0.04283715536327559 | False | False |
| A2 | BSL_stats_sidecar | 6 | 0.5141089601689579 | 0.017286866710911463 | -0.007561949331042039 | -0.028591039831042053 | False | False |
| A3 | STIM_BSL_summary_plus_BSL_stats_concat | 6 | 0.5036175765867598 | 0.018543609699805588 | -0.018053332913240183 | -0.0390824234132402 | False | False |

## Interpretation

Best cell: `A2` with mean balanced accuracy `0.5141089601689579`.

Moderate pass threshold: `0.53`.

Strong pass threshold: `0.55`.

No Wave 2 design is included in this report.
