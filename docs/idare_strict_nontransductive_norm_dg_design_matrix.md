# I-DARE Strict Non-Transductive Normalization / DG Design Matrix

## Status

`created`

## Purpose

This matrix defines which normalization and domain-generalization directions are valid for future review under strict non-transductive constraints.

## Candidate Matrix

| Candidate | Strict non-transductive? | Rationale | Execution status |
|---|---|---|---|
| Train-fold StandardScaler | Yes | Fit only on training subjects and apply frozen to held-out subjects. | Design only |
| Train-fold RobustScaler | Yes | Same as StandardScaler but less sensitive to outliers. | Design only |
| Train-fold quantile/rank mapper | Potentially yes | Valid only if quantile/rank mapping is learned from training subjects only and applied frozen. | Design only |
| Per-subject z-score on held-out subject | No | Uses held-out subject feature statistics. | Forbidden as strict evidence |
| Per-subject rank transform on held-out subject | No | This is W1B B3 style transductive diagnostic. | Archive diagnostic only |
| Domain-adversarial training using training subjects as domains | Potentially yes | Valid only if domains are training subjects and no held-out stats are used. | Design only |
| IRM/VREx-style training-subject domain regularization | Potentially yes | Valid only if group penalties use training subjects only. | Design only |
| Test-time adaptation / TTA | No | Uses target-subject distribution. | Not strict non-transductive |
| W2E input-definition x normalization interaction | Reviewable later | Useful as design after strict leakage rules are fixed. | Not execution-authorized |
| Model capacity probe | Deferred | Should wait for better operating point. | Not now |
| Augmentation | Deferred | Needs leakage policy and stable config first. | Not now |
| Representation redesign | Fallback | Consider if strict design is judged weak. | Decision-only fallback |

## Evidence Required Before Execution

A future executable objective must include:

- exact cells,
- train-only fitting rule,
- leakage checks,
- fold protocol,
- outputs,
- closeout schema,
- unchanged thresholds,
- explicit freeze enforcement.

## Current Ruling

No execution is authorized by this matrix.
