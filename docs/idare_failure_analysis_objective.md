# I-DARE Controlled Failure Analysis Objective

## Status

Short-term objective created.

No new training is authorized by this document.

This objective is a post-hoc analysis of existing committed smoke/stabilization outputs.

## Why this objective exists

The broader standardized single-modality evaluation and the 144-run label-policy ablation are complete and reviewed.

Both phases showed mixed or weak improvements. Before launching another model experiment, the project needs a controlled failure map.

## Parent medium-term objective

Improve I-DARE single-modality EEG/EMG results by identifying dominant failure modes before launching architecture, calibration, robustness, augmentation, domain-generalization, or fusion work.

## Scientific question

Given the completed broader single-modality and label-policy matrices, which modality/task/fold/policy/recipe combinations fail, why do they fail, and what is the most justified next improvement objective?

## Technical questions

1. Which folds and subjects are consistently weak across EEG and EMG?
2. Which runs fail to beat majority baseline on macro-F1, balanced accuracy, or both?
3. Are failures driven by class imbalance, one-class prediction collapse, probability calibration/threshold issues, or fold-specific subject effects?
4. Do EEG and EMG fail on the same folds, suggesting dataset/split difficulty, or on different folds, suggesting possible complementary errors?
5. Does threshold tuning improve macro-F1 without creating unstable one-class predictions?
6. Which next objective is best supported: threshold/calibration, subject normalization, extra-seed robustness, lightweight architecture, or a carefully scoped fusion-readiness analysis?

## Authorized scope

- New training: **not authorized**.
- New model experiment: **not authorized**.
- Source: existing committed JSON and prediction CSV reports only.
- Modalities: I-DARE EEG mainline and I-DARE EMG mainline.
- Tasks: valence and arousal.
- Label policies: `discard_midpoint`, `midpoint_as_low`, `midpoint_as_high`.
- Recipes: `ce_class_weighted`, `balanced_sampler_ce`.

## Input artifacts

### Label-policy ablation

- `docs/idare_label_policy_ablation_report.md`
- `docs/idare_label_policy_ablation_report.json`
- `docs/idare_label_policy_ablation_eeg_primary.json`
- `docs/idare_label_policy_ablation_eeg_primary_predictions.csv`
- `docs/idare_label_policy_ablation_emg_primary.json`
- `docs/idare_label_policy_ablation_emg_primary_predictions.csv`
- `docs/idare_label_policy_ablation_review_status.md`

### Broader single-modality evaluation

- `docs/idare_broader_standardized_single_modality_evaluation_report.md`
- `docs/idare_broader_standardized_single_modality_evaluation_report.json`
- `docs/idare_broader_eval_eeg_stim_bsl_only_primary.json`
- `docs/idare_broader_eval_eeg_stim_bsl_only_primary_predictions.csv`
- `docs/idare_broader_eval_emg_feature_only_primary.json`
- `docs/idare_broader_eval_emg_feature_only_primary_predictions.csv`
- `docs/idare_broader_standardized_single_modality_evaluation_review_status.md`

### Optional context only

- `docs/idare_single_modality_bsl_stats_vs_baseline_comparison.md`
- `docs/idare_single_modality_bsl_stats_vs_baseline_review_status.md`
- `docs/idare_eeg_stim_bsl_only_standardized_status.md`
- `docs/idare_emg_feature_only_status.md`

## Expected outputs

- `docs/idare_failure_analysis_report.md`
- `docs/idare_failure_analysis_report.json`
- Optional: `docs/idare_failure_analysis_fold_summary.csv`
- After human review: `docs/idare_failure_analysis_review_status.md`

## Minimum report contents

- per-modality/task/policy/recipe aggregate table
- per-fold weakness map
- majority-baseline comparison
- one-class/collapse summary
- probability/threshold diagnostics summary where available
- cross-modality fold-overlap summary
- failure taxonomy labels and counts
- recommended next objective with rationale
- explicit not-authorized list

## Pass criteria

- All required source files are present and readable.
- Report covers EEG and EMG, valence and arousal, and all three label policies.
- Every conclusion is grounded in existing committed outputs.
- No new training, model patch, fusion, final LOSO claim, or final label-policy lock is introduced.
- The output identifies either a clear next improvement objective or states that evidence is inconclusive.

## Failure taxonomy

| Failure type | Meaning |
|---|---|
| `majority_not_beaten` | Run or aggregate fails to beat majority baseline on key balanced metrics. |
| `fold_specific_weakness` | A small set of folds dominates performance loss. |
| `policy_instability` | Best policy changes by modality/task or fold. |
| `recipe_instability` | Best recipe changes without a consistent modality/task pattern. |
| `prediction_collapse_or_skew` | Prediction counts are one-class or highly skewed despite two-class labels. |
| `threshold_sensitive` | Threshold diagnostics improve macro-F1 materially but may indicate calibration instability. |
| `cross_modality_shared_failure` | EEG and EMG are weak on the same fold/task. |
| `cross_modality_complementary_failure` | EEG and EMG are weak on different fold/task cases. |
| `insufficient_evidence` | Existing outputs do not support a stable next action. |

## Not authorized

- new training runs
- EEG+EMG fusion
- full model(BSL, STIM, STIM-BSL)
- final LOSO / final performance claim
- locking a final label policy
- raw EMG mainline
- architecture ablation
- data augmentation
- SupCon / VREx / domain generalization
- extra seeds unless a follow-up objective is created

## Next step after this objective

Prepare a read-only analysis command/script that consumes existing committed outputs and writes docs/idare_failure_analysis_report.md/json, then review/close out before choosing the next improvement objective.
