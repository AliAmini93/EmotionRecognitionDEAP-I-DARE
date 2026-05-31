# W1A EEG Input Definition Closeout

## Status

`closeout_complete`

## Scope

- I-DARE only.
- EEG only.
- arousal only.
- within-subject pairwise affect preference ranking.
- ridge classifier only.
- normalization fixed to current/default none.
- 18 registered runs completed: A1/A2/A3 × 6 folds.
- no neural training.
- no normalization ablation.
- no DEAP.
- no fusion.
- no rereference/CAR.
- no downsampling rebuild.
- no cache overwrite.

## Result

Diagnosis: `no_gate_pass`

Best cell: `A2` / `BSL_stats_sidecar`

Best mean balanced accuracy: `0.5141089601689579`

Moderate pass threshold `0.53`: not reached.

Strong pass threshold `0.55`: not reached.

## Cell Summary

| Cell | Input definition | Runs | Mean balanced accuracy | Std balanced accuracy | Delta vs REF-PW-EEG-ARO-001 | Delta vs REF-BSL-EEG-ARO-001 | Moderate pass | Strong pass |
|---|---|---:|---:|---:|---:|---:|---|---|
| A1 | current_STIM_BSL_summary | 6 | 0.499863 | 0.021590 | -0.021808 | -0.042837 | False | False |
| A2 | BSL_stats_sidecar | 6 | 0.514109 | 0.017287 | -0.007562 | -0.028591 | False | False |
| A3 | STIM_BSL_summary_plus_BSL_stats_concat | 6 | 0.503618 | 0.018544 | -0.018053 | -0.039082 | False | False |

## Interpretation for Control Tower

W1A did not find evidence that the tested EEG input definitions expose enough hidden arousal pairwise signal to pass the Wave 1 gates.

A2, the BSL-stats sidecar, was the best W1A cell, but it stayed below both the pairwise moderate pass gate and the binary BSL reference.

This branch does not suggest pairwise reopen, Wave 2 design, preprocessing change, normalization ablation, neural training, DEAP, or fusion.

## Recommended Branch Action

Archive or hold W1A as `no_gate_pass` evidence and let Control Tower compare it against W1B/W1C/W1D closeouts.
