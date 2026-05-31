# I-DARE Root-Cause Triage Null/Permutation Sanity Report

Status: `completed`

## Summary

- Null/permutation sanity should be treated as a decision gate, not a new modeling direction.
- Existing majority/fold/null evidence should decide whether moderate-looking gains are distinguishable from noise.
- This audit summarizes existing null-like baselines and cache-majority metadata; it does not run a new permutation experiment.

## Classification Pressure

- **A**: moderate if majority/fold baselines explain apparent gains
- **B**: moderate if null comparisons show protocol target is too noisy
- **C**: weak unless signal clears null sanity
- **D**: weak unless subject-shift evidence clears null sanity
- **E**: strong if observed gains do not clear null/fold-majority sanity

## Evidence Snippets

- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_project_synthesis_review_and_final_registry_update.md:43` — | W1C EMG independent baseline | accepted | no aggregate pass | EMG reference only |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_project_synthesis_review_and_final_registry_update.md:45` — | Strict NTD normalization smoke | accepted | no pass | clean weak-effect baseline |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:9` — - cache_npy: `.cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy`
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:10` — - cache_index: `.cache/idare_eeg_cache_index_baseline_corrected.csv`
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:16` — - recipes: `balanced_sampler_ce`
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:23` — | Task | Policy | Recipe | Runs | Final macro F1 | Final bal acc | Final acc | Best macro F1 | One-class final runs | Majority acc |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:25` — | arousal | midpoint_as_high | balanced_sampler_ce | 4 | 0.4958 | 0.5339 | 0.5185 | 0.4958 | 0 | 0.5798 |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:29` — | Task | Policy | Recipe | Runs | Threshold macro F1 | Threshold bal acc | Mean threshold | Macro F1 gain | Bal acc gain | Threshold one-class runs |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:31` — | arousal | midpoint_as_high | balanced_sampler_ce | 4 | 0.5321 | 0.5390 | 0.5000 | 0.0363 | 0.0051 | 0 |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:35` — | Run | Task | Recipe | Fold | Seed | Train n | Val n | Macro F1 | Bal acc | Acc | Pred 0 | Pred 1 | TN | FP | FN | TP | One-class | Majority acc |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:37` — | 1 | arousal | balanced_sampler_ce | 1 | 11 | 1664 | 352 | 0.4375 | 0.5394 | 0.4631 | 61 | 291 | 44 | 172 | 17 | 119 | false | 0.6136 |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:38` — | 2 | arousal | balanced_sampler_ce | 2 | 11 | 1664 | 352 | 0.5182 | 0.5299 | 0.5199 | 161 | 191 | 102 | 110 | 59 | 81 | false | 0.6023 |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:39` — | 3 | arousal | balanced_sampler_ce | 3 | 11 | 1664 | 352 | 0.5143 | 0.5398 | 0.5284 | 246 | 106 | 123 | 43 | 123 | 63 | false | 0.5284 |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:40` — | 4 | arousal | balanced_sampler_ce | 4 | 11 | 1696 | 320 | 0.5130 | 0.5265 | 0.5625 | 238 | 82 | 141 | 43 | 97 | 39 | false | 0.5750 |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:42` — ## Train vs Validation Probability Diagnostics
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:44` — | Run | Task | Recipe | Fold | Train P1 mean | Val P1 mean | Mean shift | Train P1 median | Val P1 median | Median shift | Train pred 0 | Train pred 1 | Val pred 0 | Val pred 1 |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:46` — | 1 | arousal | balanced_sampler_ce | 1 | 0.5485 | 0.5724 | 0.0239 | 0.5601 | 0.5791 | 0.0191 | 466 | 1198 | 61 | 291 |
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_arousal_baseline_corrected_balanced_sampler_stability_smoke.md:47` — | 2 | arousal | balanced_sampler_ce | 2 | 0.4850 | 0.5144 | 0.0294 | 0.4883 | 0.5077 | 0.0193 | 883 | 781 | 161 | 191 |

## Cache Label Metadata Summary

```json
{
  "label_columns": {
    "arousal_discard_midpoint": {
      "counts": {
        "0": 1112,
        "1": 687,
        "other_or_missing": 217
      },
      "majority_accuracy": 0.6181211784324625,
      "one_class_subject_count": 4,
      "one_class_subject_examples": [
        "7",
        "13",
        "41",
        "55"
      ],
      "subject_count_with_valid_labels": 63,
      "valid_rows": 1799
    },
    "arousal_midpoint_as_high": {
      "counts": {
        "0": 1112,
        "1": 904,
        "other_or_missing": 0
      },
      "majority_accuracy": 0.5515873015873016,
      "one_class_subject_count": 1,
      "one_class_subject_examples": [
        "41"
      ],
      "subject_count_with_valid_labels": 63,
      "valid_rows": 2016
    },
    "arousal_midpoint_as_low": {
      "counts": {
        "0": 1329,
        "1": 687,
        "other_or_missing": 0
      },
      "majority_accuracy": 0.6592261904761905,
      "one_class_subject_count": 4,
      "one_class_subject_examples": [
        "7",
        "13",
        "41",
        "55"
      ],
      "subject_count_with_valid_labels": 63,
      "valid_rows": 2016
    },
    "arousal_score": {
      "counts": {
        "0": 0,
        "1": 341,
        "other_or_missing": 1675
      },
      "majority_accuracy": 1.0,
      "one_class_subject_count": 51,
      "one_class_subject_examples": [
        "1",
        "3",
        "5",
        "8",
        "9",
        "10",
        "11",
        "13",
        "14",
        "15",
        "16",
        "17"
      ],
      "subject_count_with_valid_labels": 51,
      "valid_rows": 341
    },
    "valence_discard_midpoint": {
      "counts": {
        "0": 812,
        "1": 855,
        "other_or_missing": 349
      },
      "majority_accuracy": 0.5128974205158968,
      "one_class_subject_count": 0,
      "one_class_subject_examples": [],
      "subject_count_with_valid_labels": 63,
      "valid_rows": 1667
    },
    "valence_midpoint_as_high": {
      "counts": {
        "0": 812,
        "1": 1204,
        "other_or_missing": 0
      },
      "majority_accuracy": 0.5972222222222222,
      "one_class_subject_count": 0,
      "one_class_subject_examples": [],
      "subject_count_with_valid_labels": 63,
      "valid_rows": 2016
    },
    "valence_midpoint_as_low": {
      "counts": {
        "0": 1161,
        "1": 855,
        "other_or_missing": 0
      },
      "majority_accuracy": 0.5758928571428571,
      "one_class_subject_count": 0,
      "one_class_subject_examples": [],
      "subject_count_with_valid_labels": 63,
      "valid_rows": 2016
    },
    "valence_score": {
      "counts": {
        "0": 0,
        "1": 283,
        "other_or_missing": 1733
      },
      "majority_accuracy": 1.0,
      "one_class_subject_count": 55,
      "one_class_subject_examples": [
        "1",
        "2",
        "3",
        "5",
        "6",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14"
      ],
      "subject_count_with_valid_labels": 55,
      "valid_rows": 283
    }
  },
  "path": ".cache/idare_eeg_cache_index.csv",
  "rows": 2016,
  "status": "present"
}
```

## Notes

- No new permutation computation was run.
- No experiment was run.
- No model result was created.

