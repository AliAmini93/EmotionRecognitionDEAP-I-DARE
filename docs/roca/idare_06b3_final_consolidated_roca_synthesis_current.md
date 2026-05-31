# I-DARE 06b3 Final Consolidated ROCA Synthesis

Generated at: `2026-05-31T12:33:57+00:00`

## Final decision

- **Decision:** `CONSOLIDATION_READY_FOR_REVIEW_NOT_MAIN`
- **Scientific conclusion changed by historical merges:** `NO`
- **Current branch:** `roca-consolidate-branches`
- **Consolidated branch tip:** `a64315d`
- **ROCA truth branch tip:** `fe4c7b3`
- **Main branch tip:** `dd44d0f`

## Current scientific conclusion

Strict LOSO global raw EEG/EMG residual decoding remains unsupported by locked gates. The dominant issue is subject calibration/domain shift plus weak transferable residual identifiability. Historical branches are useful evidence, but they do not overturn the final ROCA locked-gate conclusion.

## Merged historical branches

| Branch | Role | Status | Scientific use |
|---|---|---|---|
| `origin/idare/postwave1/data-augmentation-track` | historical augmentation evidence | merged_into_roca_consolidate_branches_as_historical_evidence | preserve/cite as evidence; do not override locked-gate ROCA conclusion |
| `origin/idare/postwave1/idare-prior-best-cell-confirmation` | prior-best confirmation evidence | merged_into_roca_consolidate_branches_as_historical_evidence | preserve/cite as evidence; do not override locked-gate ROCA conclusion |
| `origin/idare/postwave1/label-task-protocol-reconciliation` | label/task protocol evidence | merged_into_roca_consolidate_branches_as_historical_evidence | preserve/cite as evidence; do not override locked-gate ROCA conclusion |
| `origin/idare/postwave1/root-cause-triage` | root-cause triage evidence | merged_into_roca_consolidate_branches_as_historical_evidence | preserve/cite as evidence; do not override locked-gate ROCA conclusion |
| `origin/idare/postwave1/representation-redesign-confirmation` | representation redesign confirmation evidence | merged_into_roca_consolidate_branches_as_historical_evidence | preserve/cite as evidence; do not override locked-gate ROCA conclusion |
| `origin/idare/postwave1/representation-redesign-smoke` | representation redesign smoke evidence | merged_into_roca_consolidate_branches_as_historical_evidence | preserve/cite as evidence; do not override locked-gate ROCA conclusion |
| `origin/idare/postwave1/strict-ntd-norm-smoke` | strict non-transductive normalization evidence | merged_into_roca_consolidate_branches_as_historical_evidence | preserve/cite as evidence; do not override locked-gate ROCA conclusion |
| `origin/idare/wave1/eeg-input-definition` | early EEG input definition evidence | merged_into_roca_consolidate_branches_as_historical_evidence | preserve/cite as evidence; do not override locked-gate ROCA conclusion |
| `origin/idare/wave1/eeg-subject-normalization` | early EEG subject-normalization evidence | merged_into_roca_consolidate_branches_as_historical_evidence | preserve/cite as evidence; do not override locked-gate ROCA conclusion |
| `origin/idare/wave1/emg-baseline-ablation` | early EMG baseline evidence | merged_into_roca_consolidate_branches_as_historical_evidence | preserve/cite as evidence; do not override locked-gate ROCA conclusion |
| `origin/idare/wave1/feature-discriminability` | early feature discriminability evidence | merged_into_roca_consolidate_branches_as_historical_evidence | preserve/cite as evidence; do not override locked-gate ROCA conclusion |

## What this means

The historical branches are now preserved in the consolidation branch. They provide useful evidence about augmentation, protocol choices, representation redesign, normalization, EMG baselines, and feature discriminability. However, they do not replace the newer locked-gate ROCA conclusion.

The current conclusion remains calibration-dominant: EEG/EMG signals under strict LOSO are not enough, under the tested formulations, to support a strong global residual emotion-recognition claim. Future positive claims should be framed around calibration, personalization, adaptation, or a redesigned target.

## Recommended next steps

| Priority | Step | Action | Success condition |
|---:|---|---|---|
| 1 | `review_06b3` | Review final consolidated ROCA synthesis. | No historical branch is misrepresented as final proof. |
| 2 | `merge_to_roca` | Merge roca-consolidate-branches into roca-idare-killtest. | origin/roca-idare-killtest points to a commit containing 06b1, 06b2, 06b3 and historical evidence merges. |
| 3 | `archive_old_branches` | After verification, optionally delete/archive old idare/* remote branches. | GitHub branch list is reduced without losing evidence. |
| 4 | `scientific_next_track` | Start next research track only after deciding whether the claim is calibrated/personalized or strict zero-calibration LOSO. | No more blind EEG/EMG architecture search without a success gate. |

## Merge instruction

If this synthesis is accepted, merge `roca-consolidate-branches` into `roca-idare-killtest`. Do **not** merge it into `main`.
