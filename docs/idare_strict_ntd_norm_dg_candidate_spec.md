# I-DARE Strict Non-Transductive Normalization / DG Candidate Spec

## Status

`created`

## Scope

Control Tower documentation/design only.

Forbidden:
- no experiments
- no runner creation
- no Wave 2 execution
- no W2E execution
- no DEAP
- no fusion
- no preprocessing changes
- no threshold changes
- no main push
- no W1 branch-owned file edits

## Core Definition

A candidate is strict non-transductive only if every fitted statistic, transform, hyperparameter choice, calibration rule, and model parameter is learned without using held-out/test subject rows, labels, or unlabeled feature distributions.

If a method uses held-out subject feature statistics, even without labels, it is transductive and cannot be reported as strict non-transductive evidence.

## Strict Non-Transductive Candidates

| ID | Candidate | Strict? | Notes |
|---|---|---|---|
| N0 | current no normalization | yes | Baseline / anchor. |
| N1 | train-fold StandardScaler | yes | Fit on training subjects only; apply frozen to held-out subjects. |
| N2 | train-fold RobustScaler | yes | Fit median/IQR on training subjects only; apply frozen. |
| N3 | train-fold quantile/rank mapper | conditional yes | Valid only if mapping is fit on training subjects only and frozen. |
| N4 | train-fold PCA/whitening feature transform | conditional yes | Valid only if fitted on training subjects only; no cache rebuild. |
| DG1 | train-subject domain regularization | conditional yes | Uses training subjects as domains only. |
| DG2 | VREx/IRM-style training-subject penalties | conditional yes | No held-out subject statistics. |
| DG3 | source-only DANN/domain-adversarial training | conditional yes | Domains are training subjects only; no target adaptation. |
| DG4 | GroupDRO across training subjects | conditional yes | No target-subject usage. |

## Transductive / Semi-Transductive / Invalid Candidates

| Candidate | Class | Reason |
|---|---|---|
| per-test-subject z-score | transductive | Uses held-out subject mean/std. |
| per-test-subject rank transform | transductive | W1B B3 style; diagnostic only. |
| per-test-subject quantile normalization | transductive | Uses held-out distribution. |
| test-time adaptation | transductive | Uses target distribution. |
| target CORAL/MMD alignment | transductive | Aligns to target/test distribution. |
| batch norm updated on test batches | transductive | Uses held-out batch stats. |
| global scaler fit on all subjects | invalid | Direct fold leakage. |
| threshold calibration on held-out/test | invalid | Test-set tuning. |
| preprocessing/cache rebuild | invalid here | Out of scope and forbidden. |

## Scientifically Worth Considering

Most defensible future candidates:

1. N0 current none anchor.
2. N1 train-fold StandardScaler.
3. N2 train-fold RobustScaler.
4. N3 train-fold frozen quantile/rank mapper.
5. DG2 VREx/IRM-style train-subject regularization.
6. DG4 GroupDRO across training subjects.

Less immediate:
- N4 PCA/whitening, because it adds another transform that may complicate attribution.
- DG3 DANN, because it may require model capacity decisions before operating point is stable.

## Minimum Future Cell Matrix If Execution Is Later Authorized

A minimal future executable objective, if later approved, should not start broad.

Recommended minimal design:

| Cell | Type | Description |
|---|---|---|
| S0 | anchor | current none/current normalization |
| S1 | strict normalization | train-fold StandardScaler |
| S2 | strict normalization | train-fold RobustScaler |
| S3 | strict normalization | train-fold frozen quantile/rank mapper |
| D1 | strict DG | training-subject VREx or GroupDRO only if model family is explicitly approved |

The first executable matrix should prefer S0/S1/S2/S3 before DG training unless Control Tower explicitly approves DG model design.

## W2E Position

W2E interaction-grid should remain a design subsection for now.

It may become a later independent objective only if:
- strict leakage rules are approved,
- minimal strict normalization cells are accepted,
- interaction with W1A input definitions is justified as design-only first,
- human review explicitly authorizes W2E objective creation.

## Pivot Condition

If strict non-transductive candidates are judged too weak, too leakage-prone, or scientifically unlikely to improve cross-subject transfer, Control Tower should consider pivoting toward representation redesign rather than incremental normalization probes.

## Current Ruling

No execution is authorized by this spec.
