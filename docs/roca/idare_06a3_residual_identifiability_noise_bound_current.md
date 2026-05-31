# I-DARE residual identifiability and label-noise bound

This report asks whether the residual target has repeatable structure strong enough to justify more physiology/deep modeling.

Residual definition: rating minus LOSO stimulus prior. The zero-residual baseline predicts no subjective deviation beyond the stimulus prior.


## Decision table

| target  | decision                                          | zero_residual_rmse | subject_mean_oracle_lift | k16_subject_mean_oracle_lift | subject_style_reliability_mean_r | shared_stimulus_residual_reliability_mean_r | high_disagreement_shared_residual_reliability_mean_r | interpretation                                                                                                                                                                                             | recommended_next_action                                                                                                                          |
| ------- | ------------------------------------------------- | ------------------ | ------------------------ | ---------------------------- | -------------------------------- | ------------------------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| arousal | CALIBRATION_DOMINANT_NOT_GLOBAL_RESIDUAL_DECODING | 1.9442049821165959 | 0.22852372006498567      | 0.20187276756915357          | 0.8432316375671187               | -1.0                                        | 0.8751509512146085                                   | Subject-style residual structure is repeatable, but shared stimulus residual structure is weak/non-repeatable. The viable route is explicit calibration/subject adaptation, not larger generic CNN search. | Run 06a4 subject-normalization/domain-adaptation and k-shot context ablations; require improvement over fixed EEG-bandpower and B2 locked gates. |
| valence | NO_GO_VALENCE_CURRENT_RESIDUAL_IDENTIFIABILITY    | 1.257773694673858  | 0.02112091085416079      | 0.003861636837145584         | 0.5312172780409428               | -1.0                                        | 0.7627248397441191                                   | Valence residual has weak shared structure and weak calibration/oracle headroom under the current target.                                                                                                  | Do not run more valence physiology models until target/label formulation changes or a stronger representation source appears.                    |


## Residual identifiability

| target  | zero_residual_rmse_after_loso_stimulus_prior | leave_one_trial_subject_mean_oracle_lift_vs_zero | k16_pooled_lift_vs_zero_mean | subject_style_split_half_mean_r | shared_stimulus_residual_split_half_mean_r | high_disagreement_shared_stimulus_residual_split_half_mean_r |
| ------- | -------------------------------------------- | ------------------------------------------------ | ---------------------------- | ------------------------------- | ------------------------------------------ | ------------------------------------------------------------ |
| arousal | 1.9442049821165959                           | 0.22852372006498567                              | 0.20187276756915357          | 0.8432316375671187              | -1.0                                       | 0.8751509512146085                                           |
| valence | 1.257773694673858                            | 0.02112091085416079                              | 0.003861636837145584         | 0.5312172780409428              | -1.0                                       | 0.7627248397441191                                           |


## Reliability bootstrap

| target  | subset                                      | subject_style_split_half_mean_r | subject_style_split_half_median_r | subject_style_split_half_p10_r | subject_style_split_half_p90_r | subject_style_split_half_n_valid | shared_stimulus_residual_split_half_mean_r | shared_stimulus_residual_split_half_median_r | shared_stimulus_residual_split_half_p10_r | shared_stimulus_residual_split_half_p90_r | shared_stimulus_residual_split_half_n_valid | n_rows_used | n_subjects_used | n_stimuli_used |
| ------- | ------------------------------------------- | ------------------------------- | --------------------------------- | ------------------------------ | ------------------------------ | -------------------------------- | ------------------------------------------ | -------------------------------------------- | ----------------------------------------- | ----------------------------------------- | ------------------------------------------- | ----------- | --------------- | -------------- |
| arousal | all_trials                                  | 0.8432316375671187              | 0.8438419261786094                | 0.8081599540817285             | 0.8771832832171407             | 1000                             | -1.0                                       | -1.0                                         | -1.0                                      | -0.9999999999999997                       | 1000                                        | 2016        | 63              | 32             |
| arousal | high_disagreement_abs_residual_q75_or_05ajb | 0.7812443317771156              | 0.7857951188844964                | 0.7218935397680339             | 0.8335147416204123             | 500                              | 0.8751509512146085                         | 0.8837538952574284                           | 0.8186206270193429                        | 0.9262951889549887                        | 500                                         | 508         | 63              | 32             |
| valence | all_trials                                  | 0.5312172780409428              | 0.5320506988456233                | 0.4438141669887588             | 0.6160221514487346             | 1000                             | -1.0                                       | -1.0                                         | -1.0                                      | -0.9999999999999998                       | 1000                                        | 2016        | 63              | 32             |
| valence | high_disagreement_abs_residual_q75_or_05ajb | 0.39829189564763073             | 0.39802029598946875               | 0.31048476267287134            | 0.48707619670206764            | 500                              | 0.7627248397441191                         | 0.7715071459428162                           | 0.6534979193796464                        | 0.8563769628389063                        | 500                                         | 505         | 63              | 32             |


## K-shot subject-mean oracle

| target  | k_calibration_trials | n_repeats | pooled_rmse_mean   | pooled_lift_vs_zero_mean | pooled_lift_vs_zero_p10 | pooled_lift_vs_zero_p90 | subject_lift_mean_over_repeats |
| ------- | -------------------- | --------- | ------------------ | ------------------------ | ----------------------- | ----------------------- | ------------------------------ |
| arousal | 1                    | 500       | 2.370959048121633  | -0.42675406600503707     | -0.5496280650078496     | -0.29998180988222295    | -0.3481037070474671            |
| arousal | 2                    | 500       | 2.068559133497712  | -0.12435415138111629     | -0.20660326953166844    | -0.051480492149004374   | -0.09409356177518512           |
| arousal | 4                    | 500       | 1.8844279095216345 | 0.05977707259496134      | 0.012090687831787239    | 0.10691369605608529     | 0.06160775532486011            |
| arousal | 8                    | 500       | 1.7892714521347364 | 0.15493352998185947      | 0.12195226423033596     | 0.18575558266638076     | 0.14597286768473056            |
| arousal | 16                   | 500       | 1.7423322145474425 | 0.20187276756915357      | 0.16855644393608168     | 0.23926858198124704     | 0.18954162888004136            |
| valence | 1                    | 500       | 1.7242485463574295 | -0.46647485168357145     | -0.5648308582113443     | -0.3713736960251384     | -0.39130450906314734           |
| valence | 2                    | 500       | 1.4921480482304132 | -0.23437435355655517     | -0.2953366560719823     | -0.17795138597449733    | -0.20113457263647583           |
| valence | 4                    | 500       | 1.3611895698098173 | -0.1034158751359594      | -0.1382419936484531     | -0.06936828318489294    | -0.09065085437996429           |
| valence | 8                    | 500       | 1.2912241682360728 | -0.0334504735622149      | -0.05738360959272091    | -0.009567256197205791   | -0.02889215495612919           |
| valence | 16                   | 500       | 1.2539120578367124 | 0.003861636837145584     | -0.02199624988842241    | 0.029286305178664044    | 0.005527126794400774           |


## High-disagreement bounds

| target  | abs_residual_threshold | n_high | zero_rmse_high     | subject_style_split_half_mean_r_high | shared_stimulus_residual_split_half_mean_r_high | interpretation                                                 |
| ------- | ---------------------- | ------ | ------------------ | ------------------------------------ | ----------------------------------------------- | -------------------------------------------------------------- |
| arousal | 2.2096774193548385     | 508    | 3.24013921212341   | 0.7812443317771156                   | 0.8751509512146085                              | high-disagreement subset has enough rows for targeted analysis |
| valence | 1.435483870967742      | 505    | 2.1186046331336152 | 0.39829189564763073                  | 0.7627248397441191                              | high-disagreement subset has enough rows for targeted analysis |


## Next steps

| priority | step | title                                                   | purpose                                                                                                                                      | success_condition                                                                                                        |
| -------- | ---- | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 1        | 06a4 | Subject-normalization and domain-adaptation ablation    | Test whether subject/domain normalization, CORAL-style alignment, and k-shot context can turn subject-style structure into LOSO improvement. | Arousal high-disagreement LOSO improves beyond fixed EEG-bandpower and does not harm locked B2 gates.                    |
| 2        | 06a5 | Augmentation rerun under current residual gates         | Only rerun prior augmentation if it is evaluated under 05ajb/06a1y residual gates, not old binary/oracle metrics.                            | Augmentation beats zero residual and fixed EEG-bandpower under subject-held-out residual gates.                          |
| 3        | 06a6 | Neural pipeline anchor test against fixed EEG-bandpower | Before larger deep models, force the neural pipeline to reproduce the simple bandpower/summary signal.                                       | A neural or hybrid model matches/exceeds fixed EEG-bandpower on confirmed arousal high-disagreement residual prediction. |


## Git status note

This script intentionally writes only 06a3 outputs. Existing unrelated untracked files are not touched.
