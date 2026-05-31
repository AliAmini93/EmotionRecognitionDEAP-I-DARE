# I-DARE Representation Redesign Smoke Representation Diagnostic Report

- base_feature_count: `288`

| Run | Cell | Fold | Selected Features | Notes |
|---:|---|---:|---:|---|
| 1 | R0 | 1 | 288 | R0 anchor: all base EEG summary features; StandardScaler fit on training fold only. |
| 2 | R1 | 1 | 288 | R1: train-subject residualization fit only on training subjects; unseen held-out subject receives no per-subject fitted offset. |
| 3 | R2 | 1 | 96 | R2: train-only subject-invariant feature selection using training labels and training-subject variability only. |
| 4 | R3 | 1 | 64 | R3: diagnostics-first stable subset selected only from training-subject label effects. |
| 5 | R0 | 2 | 288 | R0 anchor: all base EEG summary features; StandardScaler fit on training fold only. |
| 6 | R1 | 2 | 288 | R1: train-subject residualization fit only on training subjects; unseen held-out subject receives no per-subject fitted offset. |
| 7 | R2 | 2 | 96 | R2: train-only subject-invariant feature selection using training labels and training-subject variability only. |
| 8 | R3 | 2 | 64 | R3: diagnostics-first stable subset selected only from training-subject label effects. |
| 9 | R0 | 3 | 288 | R0 anchor: all base EEG summary features; StandardScaler fit on training fold only. |
| 10 | R1 | 3 | 288 | R1: train-subject residualization fit only on training subjects; unseen held-out subject receives no per-subject fitted offset. |
| 11 | R2 | 3 | 96 | R2: train-only subject-invariant feature selection using training labels and training-subject variability only. |
| 12 | R3 | 3 | 64 | R3: diagnostics-first stable subset selected only from training-subject label effects. |
| 13 | R0 | 4 | 288 | R0 anchor: all base EEG summary features; StandardScaler fit on training fold only. |
| 14 | R1 | 4 | 288 | R1: train-subject residualization fit only on training subjects; unseen held-out subject receives no per-subject fitted offset. |
| 15 | R2 | 4 | 96 | R2: train-only subject-invariant feature selection using training labels and training-subject variability only. |
| 16 | R3 | 4 | 64 | R3: diagnostics-first stable subset selected only from training-subject label effects. |
| 17 | R0 | 5 | 288 | R0 anchor: all base EEG summary features; StandardScaler fit on training fold only. |
| 18 | R1 | 5 | 288 | R1: train-subject residualization fit only on training subjects; unseen held-out subject receives no per-subject fitted offset. |
| 19 | R2 | 5 | 96 | R2: train-only subject-invariant feature selection using training labels and training-subject variability only. |
| 20 | R3 | 5 | 64 | R3: diagnostics-first stable subset selected only from training-subject label effects. |
| 21 | R0 | 6 | 288 | R0 anchor: all base EEG summary features; StandardScaler fit on training fold only. |
| 22 | R1 | 6 | 288 | R1: train-subject residualization fit only on training subjects; unseen held-out subject receives no per-subject fitted offset. |
| 23 | R2 | 6 | 96 | R2: train-only subject-invariant feature selection using training labels and training-subject variability only. |
| 24 | R3 | 6 | 64 | R3: diagnostics-first stable subset selected only from training-subject label effects. |
