# Handoff Delta After Discard-Midpoint Sanity Baseline

The cache-based discard-midpoint sanity baseline completed successfully.

Results:

- valence/discard_midpoint: macro_f1=0.3877, balanced_acc=0.5018, best_f1=0.4280, one_class=6/12
- arousal/discard_midpoint: macro_f1=0.4202, balanced_acc=0.5190, best_f1=0.4915, one_class=1/12

Comparison:

- midpoint_as_high remains the temporary main score-5 policy for both valence and arousal.
- discard_midpoint remains a secondary sanity / ablation candidate.

Immediate next technical step:

Move from label-policy selection to training-recipe stabilization, especially reducing one-class collapse for valence.
