# I-DARE 4x4 Leakage-Safe Shortcut Baseline Audit

No EEG/EMG or deep model was trained. Only fixed, simple label/metadata baselines were fitted inside each legal train region.

## Leakage Contract

- No target-subject labels were used for fitting.
- No target-stimulus labels were used for fitting.
- No EEG or EMG features were used.
- Primary-test stimulus-only and subject-only priors are intentionally absent because both identities are unseen.

## Primary Repetition: Legal Primary-Test Baselines

| task | policy | baseline | n | balanced_accuracy | macro_f1 | roc_auc | brier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | discard_midpoint | global_train_prior | 1799 | 0.5 | 0.382 | 0.3308 | 0.2511 |
| arousal | discard_midpoint | order_bin_prior | 1799 | 0.5849 | 0.5813 | 0.5713 | 0.252 |
| arousal | discard_midpoint | order_quadratic_logistic | 1799 | 0.6065 | 0.6067 | 0.6171 | 0.2325 |
| arousal | midpoint_as_high | global_train_prior | 2016 | 0.4547 | 0.3802 | 0.3636 | 0.258 |
| arousal | midpoint_as_high | order_bin_prior | 2016 | 0.5279 | 0.5262 | 0.5606 | 0.2644 |
| arousal | midpoint_as_high | order_quadratic_logistic | 2016 | 0.6032 | 0.6004 | 0.6195 | 0.2418 |
| arousal | midpoint_as_low | global_train_prior | 2016 | 0.5 | 0.3973 | 0.3363 | 0.2377 |
| arousal | midpoint_as_low | order_bin_prior | 2016 | 0.5824 | 0.5815 | 0.5739 | 0.2379 |
| arousal | midpoint_as_low | order_quadratic_logistic | 2016 | 0.5792 | 0.579 | 0.6029 | 0.2223 |
| valence | discard_midpoint | global_train_prior | 1667 | 0.4113 | 0.3776 | 0.3893 | 0.2589 |
| valence | discard_midpoint | order_bin_prior | 1667 | 0.5755 | 0.5753 | 0.5389 | 0.3187 |
| valence | discard_midpoint | order_quadratic_logistic | 1667 | 0.6119 | 0.6117 | 0.6836 | 0.2412 |
| valence | midpoint_as_high | global_train_prior | 2016 | 0.5 | 0.3739 | 0.4034 | 0.2461 |
| valence | midpoint_as_high | order_bin_prior | 2016 | 0.5879 | 0.5876 | 0.5668 | 0.2865 |
| valence | midpoint_as_high | order_quadratic_logistic | 2016 | 0.6461 | 0.6477 | 0.6815 | 0.2318 |
| valence | midpoint_as_low | global_train_prior | 2016 | 0.5 | 0.3654 | 0.3953 | 0.2517 |
| valence | midpoint_as_low | order_bin_prior | 2016 | 0.5334 | 0.5332 | 0.4853 | 0.3218 |
| valence | midpoint_as_low | order_quadratic_logistic | 2016 | 0.6142 | 0.6124 | 0.6217 | 0.2457 |

## Primary Repetition: Diagnostic Identity Shortcuts

| task | region | baseline | balanced_accuracy_macro | roc_auc_macro |
| --- | --- | --- | --- | --- |
| arousal | seen_subject_unseen_stimulus | global_train_prior | 0.5 | 0.5 |
| arousal | seen_subject_unseen_stimulus | subject_prior | 0.6116 | 0.7124 |
| arousal | unseen_subject_seen_stimulus | global_train_prior | 0.5 | 0.5 |
| arousal | unseen_subject_seen_stimulus | stimulus_prior | 0.7805 | 0.8526 |
| valence | seen_subject_unseen_stimulus | global_train_prior | 0.5 | 0.5 |
| valence | seen_subject_unseen_stimulus | subject_prior | 0.5285 | 0.5448 |
| valence | unseen_subject_seen_stimulus | global_train_prior | 0.5 | 0.5 |
| valence | unseen_subject_seen_stimulus | stimulus_prior | 0.9554 | 0.9834 |

The subject-prior and stimulus-prior results are diagnostic only. Their cells overlap across the 16 outer combinations, so the report uses macro cell averages rather than pretending they are one independent pooled test set.

## Presentation-Order Null Tests

Main policy: discard midpoint. Train labels were shuffled within each source subject inside each outer cell, preserving subject prevalence while breaking order association.

| repetition | role | task | observed_ba | null_median | effect | p_value | fdr_q | significant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | primary | valence | 0.5755 | 0.4478 | 0.1277 | 0.001996 | 0.002495 | True |
| 0 | primary | arousal | 0.5849 | 0.4892 | 0.0956 | 0.001996 | 0.002495 | True |
| 1 | sensitivity | valence | 0.5234 | 0.4857 | 0.0378 | 0.147705 | 0.147705 | False |
| 1 | sensitivity | arousal | 0.5352 | 0.5 | 0.0352 | 0.001996 | 0.002495 | True |
| 2 | sensitivity | valence | 0.4926 | 0.3968 | 0.0958 | 0.001996 | 0.002495 | True |
| 2 | sensitivity | arousal | 0.5825 | 0.4953 | 0.0871 | 0.001996 | 0.002495 | True |
| 3 | sensitivity | valence | 0.5088 | 0.3787 | 0.13 | 0.001996 | 0.002495 | True |
| 3 | sensitivity | arousal | 0.525 | 0.4949 | 0.0301 | 0.001996 | 0.002495 | True |
| 4 | sensitivity | valence | 0.4409 | 0.3974 | 0.0435 | 0.093812 | 0.104236 | False |
| 4 | sensitivity | arousal | 0.5398 | 0.4905 | 0.0493 | 0.001996 | 0.002495 | True |

## Decision

- Decision: **PROCEED_WITH_MATERIAL_ORDER_SHORTCUT_GATE**
- Reason: The primary repetition shows a statistically material presentation-order shortcut under the main label policy.

## Mandatory Gates for Future Models

1. On the primary unseen-subject × unseen-stimulus test, report improvement over the best legal shortcut baseline, not only over 0.5 chance.
2. On source-subject × unseen-stimulus diagnostics, compare against the train-only subject prior.
3. On unseen-subject × source-stimulus diagnostics, compare against the train-only stimulus prior.
4. Keep repetitions 1–4 as sensitivity analyses; do not tune architectures or hyperparameters on them.
5. Use paired uncertainty analysis over physical trials and outer cells when comparing a future model with these baselines.
