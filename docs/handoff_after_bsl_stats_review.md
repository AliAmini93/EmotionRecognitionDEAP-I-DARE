# Handoff After I-DARE BSL-stats Review

## Current checkpoint

The project is at a clean stopping point after the I-DARE single-modality BSL-stats vs baseline comparison review.

Latest reviewed status:

- Comparison review is frozen.
- Mainlines are unchanged.
- EEG practical mainline remains baseline-corrected `STIM-BSL`-only.
- EMG practical mainline remains feature-level EMG.
- BSL-stats sidecars remain controlled ablations.
- EEG+EMG fusion has not started.
- Full `model(BSL, STIM, STIM-BSL)` has not started.
- No final LOSO claim is made.
- `midpoint_as_high` is not locked as final label policy.

## Latest important commits

- `0e9594d` — smoke standardized I-DARE EEG STIM-BSL baseline.
- `18da637` — freeze standardized I-DARE EEG STIM-BSL baseline status.
- `915a099` — compare I-DARE BSL stats against baselines.
- `55e7bc6` — record I-DARE BSL stats comparison review.

## What was decided

### EEG

Keep baseline-corrected `STIM-BSL`-only as the practical I-DARE EEG mainline for now.

Reason: in the smoke comparison, the standardized EEG `STIM-BSL`-only baseline beat the EEG BSL-stats sidecar on final macro-F1 for both valence and arousal.

### EMG

Keep feature-level EMG as the practical I-DARE EMG mainline for now.

Reason: EMG BSL-stats sidecar showed small positive deltas, but they were marginal and smoke-level only.

### BSL-stats

Keep BSL-stats sidecars as controlled I-DARE-aware ablations.

Do not promote them to mainline based on current smoke evidence.

## What must not start yet

Do not start:

- EEG+EMG fusion.
- Full `model(BSL, STIM, STIM-BSL)`.
- Final LOSO / final performance claim.
- Locking `midpoint_as_high`.
- Raw EMG mainline.
- Architecture ablations.
- Data augmentation.
- SupCon / VREx / domain generalization.

## Allowed next work

Allowed without a new experiment objective:

- Handoff/status summary.
- Documentation cleanup if stale notes are found.
- Planning a broader standardized single-modality evaluation.

Requires explicit new short-term objective before execution:

- Broader standardized single-modality evaluation.
- Any full or expanded rerun.
- Any fusion experiment.
- Any architecture ablation.

## Best next step

Stop here, or create a plan for broader standardized single-modality evaluation only if explicitly requested.

Do not run it automatically.
