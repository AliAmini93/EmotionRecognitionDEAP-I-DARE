# I-DARE Main-Model Data Augmentation Full Closeout

- completed_runs: `120`
- leakage_status: `PASSED`

| Modality | Task | Best DA | Mean BA | Delta vs no DA | Wins vs no DA |
|---|---|---|---:|---:|---:|
| EEG | arousal | E1_additive_gaussian_noise_weak | 0.5486 | 0.0143 | 4 |
| EEG | valence | E1_additive_gaussian_noise_weak | 0.5065 | 0.0084 | 4 |
| EMG | arousal | M4_feature_dropout | 0.5251 | 0.0199 | 5 |
| EMG | valence | M2_feature_gaussian_jitter_medium | 0.5165 | 0.0013 | 4 |
