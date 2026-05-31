# W1D Feature Discriminability Decision Matrix

| Condition | Interpretation | Priority |
|---|---|---|
| Cross-subject signal present, classifiers weak | Model/formulation/preprocessing bottleneck | Improve formulation before bigger runs |
| Within-subject signal present, cross-subject signal weak | Subject normalization/domain generalization bottleneck | Prioritize normalization/DG |
| Subject eta2 dominates label eta2 | Subject identity dominates feature geometry | Control subject effects before training expansion |
| No measurable label signal | Representation bottleneck | Revisit feature extraction/representation |

## Observed diagnoses

| Modality | Task | Diagnosis |
|---|---|---|
| EEG | valence | `within_subject_signal_present_cross_subject_signal_collapses_subject_normalization_or_domain_generalization_priority` |
| EEG | arousal | `within_subject_signal_present_cross_subject_signal_collapses_subject_normalization_or_domain_generalization_priority` |
| EMG | valence | `within_subject_signal_present_cross_subject_signal_collapses_subject_normalization_or_domain_generalization_priority` |
| EMG | arousal | `within_subject_signal_present_cross_subject_signal_collapses_subject_normalization_or_domain_generalization_priority` |
