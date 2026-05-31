# I-DARE Cross-Subject Failure Root-Cause Triage Objective

## Status

`created`

## Objective ID

`idare_cross_subject_failure_root_cause_triage_objective`

## Scope

Control Tower documentation-only objective.

Forbidden:
- no execution
- no runner creation
- no Wave 2 execution
- no DG execution
- no model-capacity probe
- no augmentation
- no DEAP
- no fusion
- no preprocessing changes
- no threshold changes
- no main push

## Current Project State

`PROJECT_EXECUTION_PAUSED_PENDING_HUMAN_PIVOT_DECISION`

Accepted pivot decision:

Do not continue with Wave 2, DG, model-capacity probe, augmentation, fusion, DEAP, preprocessing changes, or more representation smoke branches right now.

New goal:

Identify why no robust cross-subject operating point has been found, and decide whether the next real solution should be label/task redesign, evaluation-protocol reconciliation, representation redesign v2, subject/domain-generalization, or stopping the current formulation.

## Minimal Root-Cause Audit Questions

### 1. Label / Task Sanity

Questions:
- Are arousal/valence labels too subject-dependent?
- Are midpoint policies causing instability?
- Are fold-level label distributions or subject label biases dominating performance?
- Does pairwise formulation reduce or amplify subject-specific bias?

Required evidence:
- fold-level label balance
- subject-level label tendency
- midpoint-policy sensitivity from existing records
- comparison to majority/fold baselines

### 2. Subject-Domain Shift

Questions:
- How much of feature geometry is subject identity vs affect?
- Which folds/subjects consistently break generalization?
- Are failures concentrated in specific held-out subject groups?

Required evidence:
- W1D subject-dominance diagnosis
- fold-level failures from W1A/W1B/strict NTD/representation confirmation
- subject/fold instability patterns

### 3. Evaluation / Protocol Alignment

Questions:
- Is our cross-subject setting comparable to the I-DARE paper?
- Did the paper use subject-dependent, cross-subject, within-subject, or another protocol?
- Are we chasing a target the original protocol does not support?

Required evidence:
- documented I-DARE protocol comparison
- clear distinction between subject-dependent and held-out-subject evaluation
- gap between paper claims and current locked protocol

### 4. Representation Failure

Questions:
- Do current EEG/EMG features preserve affect signal only within subject?
- Did R2/R3 fail confirmation because selection was unstable, fold-sensitive, or genuinely weak?
- Should representation redesign continue, or is label/task redesign more appropriate?

Required evidence:
- representation smoke vs confirmation mismatch
- R2/R3 fold-level stability
- W1D within-subject vs cross-subject signal evidence

### 5. Null / Permutation Sanity

Questions:
- Are observed BA gains above simple null/permutation or majority/fold baselines?
- Are moderate-looking gains distinguishable from fold noise?

Required evidence:
- majority baseline comparison
- fold baseline comparison
- optional future null/permutation audit design, not execution here

## Decision Matrix

| Direction | Review status | Current bias |
|---|---|---|
| A. label/task redesign | primary candidate | Label subject-dependence may be the root issue. |
| B. evaluation/protocol reconciliation | primary candidate | We must verify whether the target protocol is realistic and paper-aligned. |
| C. representation redesign v2 | secondary | Current R2/R3 failed confirmation; only continue if root-cause audit supports it. |
| D. subject/domain-generalization | deferred | DG should not run until label/protocol/representation root cause is clearer. |
| E. stop/pivot away from current I-DARE cross-subject formulation | reviewable | If protocol or labels do not support robust cross-subject learning, stop/pivot is valid. |

## Control Ruling

This objective does not authorize execution.

The next step may be a compact execution authorization package for a root-cause triage audit only.

## Next State

`REQUEST_ROOT_CAUSE_TRIAGE_EXECUTION_AUTHORIZATION_PACKAGE`
