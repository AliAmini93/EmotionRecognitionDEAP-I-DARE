# I-DARE Score-5 Policy Selection Status

## Status

Cache-based multi-fold score-5 policy selection has been completed.

This is not a final LOSO result and not a final experiment result.

## Compared Policies

```text
discard_midpoint
midpoint_as_low
midpoint_as_high
```

## Main Result

```text
arousal/midpoint_as_low:  macro_f1=0.4433, bal_acc=0.4998, best_f1=0.4646, one_class=0/8
arousal/midpoint_as_high: macro_f1=0.4369, bal_acc=0.4884, best_f1=0.4733, one_class=1/8
arousal/discard_midpoint: macro_f1=0.3975, bal_acc=0.5004, best_f1=0.4531, one_class=2/8

valence/midpoint_as_low:  macro_f1=0.3697, bal_acc=0.4959, best_f1=0.3991, one_class=3/8
valence/midpoint_as_high: macro_f1=0.3428, bal_acc=0.4993, best_f1=0.3751, one_class=6/8
valence/discard_midpoint: macro_f1=0.3332, bal_acc=0.5000, best_f1=0.3538, one_class=8/8
```

## Interpretation

`midpoint_as_low` is currently the most stable aggregate option, but not by a large enough margin to finalize the policy.

`discard_midpoint` is currently the weakest option for valence because all final validation runs collapsed to one class.

## Provisional Working Decision

Use the following setup for the next short cache-based baseline:

```text
Primary policy: midpoint_as_low
Secondary comparison policy: midpoint_as_high
Deprioritized policy: discard_midpoint
```

Do not remove `discard_midpoint` from the codebase. Keep it available as a preset for later literature-aligned reporting or final ablations.

## Related Files

```text
scripts/16_run_idare_eeg_cache_policy_multifold_selection.py
docs/idare_eeg_cache_policy_multifold_selection_plan.md
docs/idare_eeg_cache_policy_multifold_selection.md
docs/idare_eeg_cache_policy_multifold_selection.json
```
