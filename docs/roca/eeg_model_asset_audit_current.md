# ROCA-I-DARE EEG Model Asset Audit

No model training was performed.

## Status

Status: **PASSED**

## Cache audit

| Cache | Shape | Dtype | Rows | Subjects | Stimuli | Size | Issues |
|---|---:|---|---:|---:|---:|---:|---|
| raw | [2016, 32, 640] | float32 | 2016 | 63 | 32 | 157.50 MB | None |
| baseline_corrected | [2016, 32, 640] | float32 | 2016 | 63 | 32 | 157.50 MB | None |

## Alignment checks

```json
[
  {
    "label": "raw",
    "trial_index_merge": {
      "cache_rows": 2016,
      "matched_rows": 2016,
      "unmatched_rows": 0
    },
    "stimulus_only_prediction_merge": {
      "cache_rows": 2016,
      "matched_rows": 2016,
      "unmatched_rows": 0
    },
    "fold_safe_selected_merge": {
      "rows": 2016,
      "subjects": 63,
      "stimuli": 22,
      "subsets": [
        "top25_train_entropy",
        "top25_train_score_std"
      ],
      "targets": [
        "arousal",
        "valence"
      ]
    },
    "issues": []
  },
  {
    "label": "baseline_corrected",
    "trial_index_merge": {
      "cache_rows": 2016,
      "matched_rows": 2016,
      "unmatched_rows": 0
    },
    "stimulus_only_prediction_merge": {
      "cache_rows": 2016,
      "matched_rows": 2016,
      "unmatched_rows": 0
    },
    "fold_safe_selected_merge": {
      "rows": 2016,
      "subjects": 63,
      "stimuli": 22,
      "subsets": [
        "top25_train_entropy",
        "top25_train_score_std"
      ],
      "targets": [
        "arousal",
        "valence"
      ]
    },
    "issues": []
  }
]
```

## Forward smoke tests

| Cache | Device | Input | Logits | z | z_proj | Temporal attn | Channel pool attn | Params |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| raw | cuda | [8, 32, 640] | [8, 2] | [8, 128] | [8, 64] | [8, 32, 320] | [8, 32] | 337955 |
| baseline_corrected | cuda | [8, 32, 640] | [8, 2] | [8, 128] | [8, 64] | [8, 32, 320] | [8, 32] | 337955 |

## Model import

```json
{
  "EEGSegmentEncoder": "<class 'emotion_deap_idare.models.eeg_segment_encoder.EEGSegmentEncoder'>",
  "EEGSegmentClassifier": "<class 'emotion_deap_idare.models.eeg_segment_classifier.EEGSegmentClassifier'>",
  "status": "OK"
}
```

## Issues

- None.

## Next step

If this audit passes, design the EEG training protocol before writing the training script: target, loss, fold split, validation policy, cache choice, model head, and metrics.
