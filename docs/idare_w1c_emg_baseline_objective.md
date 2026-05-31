# W1C EMG Independent Baseline Objective

Scope: I-DARE only, EMG only, binary formulation, ridge only, arousal and valence, maximum 72 registered runs.

Forbidden: EEG, fusion, DEAP, pairwise EMG reopen, neural training, broad hyperparameter search, cache overwrite, push to main.

Question: Can EMG independently reach a useful cross-subject baseline before fusion?

Cells:

| Cell | Input | Normalization |
|---|---|---|
| C1 | current EMG features | none |
| C2 | current EMG features | per-subject z-score |
| C3 | current EMG features | train-fold StandardScaler |
| C4 | EMG + BSL-stats | none |
| C5 | EMG + BSL-stats | per-subject z-score |
| C6 | EMG + BSL-stats | train-fold StandardScaler |

Model: closed-form binary ridge, alpha = 1.0, no hyperparameter search.

Label policy for this Wave 1 branch: midpoint_as_high only. This does not lock the final paper label policy.

Comparison baselines:
- REF-BIN-EMG-ARO-001: arousal bal_acc = 0.5365
- REF-BIN-EMG-VAL-001: valence bal_acc = 0.5202

Pass gates:
- moderate pass: any aggregated cell balanced accuracy >= 0.54
- strong pass: any aggregated cell balanced accuracy >= 0.55
