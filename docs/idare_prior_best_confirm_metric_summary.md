# I-DARE Prior Best Confirmation Metric Summary

Smoke/stabilization confirmation only. This is not a final paper-level performance claim.

| Cell | Modality | Task | Policy | Recipe | Runs | Final macro-F1 mean | Final balanced acc mean | One-class final runs |
|---|---|---|---|---|---:|---:|---:|---:|
| C0 | EEG | arousal | midpoint_as_high | ce_class_weighted | 6 | 0.5256 | 0.5294 | 0 |
| C1 | EEG | valence | discard_midpoint | balanced_sampler_ce | 6 | 0.4813 | 0.5056 | 0 |
| C2 | EMG | arousal | discard_midpoint | ce_class_weighted | 6 | 0.4998 | 0.5164 | 0 |
| C3 | EMG | valence | midpoint_as_high | ce_class_weighted | 6 | 0.5113 | 0.5218 | 0 |
