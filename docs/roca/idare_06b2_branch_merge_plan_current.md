# I-DARE Branch Merge Plan

- generated_at: `2026-05-31T12:28:10+00:00`
- current_branch: `roca-consolidate-branches`
- target: `origin/roca-idare-killtest` @ `fe4c7b3`
- local_head: `bea7dcb`

## Decision

Merge only non-redundant branch tips into `roca-consolidate-branches` first.
Branches that are ancestors of another candidate should not be merged separately unless manual review shows missing artifacts.

Current ROCA locked-gate conclusion remains the scientific truth; old branches are imported as historical evidence, not as replacement conclusions.

## Recommended merge tips

| branch | classification | commits ahead | files | last commit |
|---|---:|---:|---:|---|
| `origin/idare/postwave1/data-augmentation-track` | MERGE_AS_HISTORICAL_AUGMENTATION_EVIDENCE | 29 | 96 | f9728de exp: run I-DARE main-model data augmentation matrix |
| `origin/idare/postwave1/idare-prior-best-cell-confirmation` | MERGE_AS_PRIOR_BEST_CONFIRMATION_EVIDENCE | 23 | 84 | 2b72f40 exp: run I-DARE prior-best confirmation |
| `origin/idare/postwave1/label-task-protocol-reconciliation` | MERGE_AS_PROTOCOL_LABEL_POLICY_EVIDENCE | 18 | 60 | 19188db analysis: run label task protocol reconciliation audit |
| `origin/idare/postwave1/root-cause-triage` | MERGE_AS_ROOT_CAUSE_TRIAGE_EVIDENCE | 17 | 58 | 86b239a analysis: run root-cause triage audit |
| `origin/idare/postwave1/representation-redesign-confirmation` | MERGE_AS_REPRESENTATION_REDESIGN_EVIDENCE | 12 | 40 | 79438a0 docs: add representation redesign confirmation closeout |
| `origin/idare/postwave1/representation-redesign-smoke` | MERGE_AS_REPRESENTATION_REDESIGN_EVIDENCE | 12 | 43 | 2fd7f18 chore: normalize representation redesign smoke CSV outputs |
| `origin/idare/postwave1/strict-ntd-norm-smoke` | MERGE_AS_STRICT_NORMALIZATION_DG_EVIDENCE | 7 | 25 | 908dd55 analysis: add strict NTD norm smoke results |
| `origin/idare/wave1/eeg-input-definition` | MERGE_AS_EARLY_WAVE1_DIAGNOSTIC_EVIDENCE | 2 | 11 | 195c148 analysis: close out W1A EEG input definition |
| `origin/idare/wave1/eeg-subject-normalization` | MERGE_AS_EARLY_WAVE1_DIAGNOSTIC_EVIDENCE | 1 | 9 | 91f6573 analysis: add W1B EEG subject normalization audit |
| `origin/idare/wave1/emg-baseline-ablation` | MERGE_AS_EARLY_WAVE1_DIAGNOSTIC_EVIDENCE | 1 | 11 | 5a008c8 analysis: add W1C EMG independent ridge baseline |
| `origin/idare/wave1/feature-discriminability` | MERGE_AS_EARLY_WAVE1_DIAGNOSTIC_EVIDENCE | 2 | 7 | f35d1a2 analysis: close out W1D feature discriminability audit |

## Covered / redundant branches

| branch | covered by | commits ahead | files |
|---|---|---:|---:|
| `origin/idare/control-tower` | origin/idare/postwave1/data-augmentation-track | 24 | 65 |

## Concrete merge order

```bash
git merge --no-ff origin/idare/postwave1/data-augmentation-track -m "Merge historical I-DARE evidence from origin/idare/postwave1/data-augmentation-track"
git merge --no-ff origin/idare/postwave1/idare-prior-best-cell-confirmation -m "Merge historical I-DARE evidence from origin/idare/postwave1/idare-prior-best-cell-confirmation"
git merge --no-ff origin/idare/postwave1/label-task-protocol-reconciliation -m "Merge historical I-DARE evidence from origin/idare/postwave1/label-task-protocol-reconciliation"
git merge --no-ff origin/idare/postwave1/root-cause-triage -m "Merge historical I-DARE evidence from origin/idare/postwave1/root-cause-triage"
git merge --no-ff origin/idare/postwave1/representation-redesign-confirmation -m "Merge historical I-DARE evidence from origin/idare/postwave1/representation-redesign-confirmation"
git merge --no-ff origin/idare/postwave1/representation-redesign-smoke -m "Merge historical I-DARE evidence from origin/idare/postwave1/representation-redesign-smoke"
git merge --no-ff origin/idare/postwave1/strict-ntd-norm-smoke -m "Merge historical I-DARE evidence from origin/idare/postwave1/strict-ntd-norm-smoke"
git merge --no-ff origin/idare/wave1/eeg-input-definition -m "Merge historical I-DARE evidence from origin/idare/wave1/eeg-input-definition"
git merge --no-ff origin/idare/wave1/eeg-subject-normalization -m "Merge historical I-DARE evidence from origin/idare/wave1/eeg-subject-normalization"
git merge --no-ff origin/idare/wave1/emg-baseline-ablation -m "Merge historical I-DARE evidence from origin/idare/wave1/emg-baseline-ablation"
git merge --no-ff origin/idare/wave1/feature-discriminability -m "Merge historical I-DARE evidence from origin/idare/wave1/feature-discriminability"
```

After each merge, run:

```bash
git status --short
```
