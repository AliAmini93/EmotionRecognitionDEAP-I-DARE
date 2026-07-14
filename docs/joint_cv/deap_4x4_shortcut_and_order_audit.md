# DEAP 4x4 Leakage-Safe Shortcut and Order Audit

No EEG/EMG feature or physiological model was trained.

## Verified Sequence Structure

- Unique complete sequences: `32` of `32`
- Largest identical-sequence group: `1`
- Mean pairwise same-position fraction: `0.0245`
- Maximum pairwise same-position fraction: `0.1000`
- Unique positions per stimulus, min/median/max: `19/22.0/25`

## Stimulus–Order Association Against Randomized Sequences

| association | observed_nmi | null_median | effect | p | q | significant |
| --- | --- | --- | --- | --- | --- | --- |
| exact_position | 0.1856 | 0.1864 | -0.0008 | 0.562874 | 0.93014 | False |
| five_trial_bin | 0.035 | 0.0408 | -0.0057 | 0.93014 | 0.93014 | False |

## Primary Repetition: Legal Strict-Joint Baselines

| task | policy | baseline | n | balanced_accuracy | macro_f1 | roc_auc | brier |
| --- | --- | --- | --- | --- | --- | --- | --- |
| arousal | discard_midpoint | global_train_prior | 1263 | 0.5 | 0.3685 | 0.419 | 0.2471 |
| arousal | discard_midpoint | order_bin_prior | 1263 | 0.4947 | 0.3708 | 0.4293 | 0.2512 |
| arousal | discard_midpoint | order_quadratic_logistic | 1263 | 0.5 | 0.3685 | 0.425 | 0.2488 |
| arousal | midpoint_as_high | global_train_prior | 1280 | 0.5 | 0.3707 | 0.4217 | 0.246 |
| arousal | midpoint_as_high | order_bin_prior | 1280 | 0.4949 | 0.3731 | 0.4323 | 0.2497 |
| arousal | midpoint_as_high | order_quadratic_logistic | 1280 | 0.5 | 0.3707 | 0.4207 | 0.2479 |
| arousal | midpoint_as_low | global_train_prior | 1280 | 0.5 | 0.3654 | 0.4179 | 0.2484 |
| arousal | midpoint_as_low | order_bin_prior | 1280 | 0.4984 | 0.3797 | 0.4262 | 0.2527 |
| arousal | midpoint_as_low | order_quadratic_logistic | 1280 | 0.4989 | 0.3665 | 0.4318 | 0.2498 |
| valence | discard_midpoint | global_train_prior | 1264 | 0.4756 | 0.3739 | 0.4021 | 0.2533 |
| valence | discard_midpoint | order_bin_prior | 1264 | 0.4598 | 0.3932 | 0.41 | 0.2565 |
| valence | discard_midpoint | order_quadratic_logistic | 1264 | 0.4625 | 0.3721 | 0.3978 | 0.2544 |
| valence | midpoint_as_high | global_train_prior | 1280 | 0.5 | 0.3613 | 0.4042 | 0.2522 |
| valence | midpoint_as_high | order_bin_prior | 1280 | 0.4696 | 0.3869 | 0.4126 | 0.2556 |
| valence | midpoint_as_high | order_quadratic_logistic | 1280 | 0.4692 | 0.3735 | 0.3983 | 0.2534 |
| valence | midpoint_as_low | global_train_prior | 1280 | 0.4751 | 0.3703 | 0.3997 | 0.2541 |
| valence | midpoint_as_low | order_bin_prior | 1280 | 0.4554 | 0.395 | 0.411 | 0.2571 |
| valence | midpoint_as_low | order_quadratic_logistic | 1280 | 0.452 | 0.3792 | 0.4 | 0.2551 |

## Primary Repetition: Diagnostic Identity Priors

Identity priors are diagnostic only and are not legal in the primary unseen-subject × unseen-stimulus test.

| task | region | baseline | balanced_accuracy_macro | roc_auc_macro |
| --- | --- | --- | --- | --- |
| arousal | seen_subject_unseen_stimulus | global_train_prior | 0.5 | 0.5 |
| arousal | seen_subject_unseen_stimulus | subject_prior | 0.5794 | 0.648 |
| arousal | unseen_subject_seen_stimulus | global_train_prior | 0.5 | 0.5 |
| arousal | unseen_subject_seen_stimulus | stimulus_prior | 0.6451 | 0.6844 |
| valence | seen_subject_unseen_stimulus | global_train_prior | 0.5 | 0.5 |
| valence | seen_subject_unseen_stimulus | subject_prior | 0.5206 | 0.5517 |
| valence | unseen_subject_seen_stimulus | global_train_prior | 0.5 | 0.5 |
| valence | unseen_subject_seen_stimulus | stimulus_prior | 0.7765 | 0.8434 |

## Quadratic Order-Only Null Tests

Train labels were shuffled within each source subject inside every outer cell. Primary test labels remained untouched.

| rep | role | task | observed_ba | null_median | effect | p | q | significant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | primary | valence | 0.4625 | 0.4743 | -0.0119 | 0.920319 | 0.944223 | False |
| 0 | primary | arousal | 0.5 | 0.4992 | 0.0008 | 0.350598 | 0.701195 | False |
| 1 | sensitivity | valence | 0.4686 | 0.4767 | -0.0082 | 0.848606 | 0.944223 | False |
| 1 | sensitivity | arousal | 0.5012 | 0.5 | 0.0012 | 0.143426 | 0.544489 | False |
| 2 | sensitivity | valence | 0.4757 | 0.466 | 0.0097 | 0.119522 | 0.544489 | False |
| 2 | sensitivity | arousal | 0.4925 | 0.4988 | -0.0062 | 0.944223 | 0.944223 | False |
| 3 | sensitivity | valence | 0.5 | 0.4954 | 0.0046 | 0.163347 | 0.544489 | False |
| 3 | sensitivity | arousal | 0.4947 | 0.4966 | -0.0019 | 0.61753 | 0.944223 | False |
| 4 | sensitivity | valence | 0.481 | 0.4774 | 0.0036 | 0.334661 | 0.701195 | False |
| 4 | sensitivity | arousal | 0.4991 | 0.5 | -0.0009 | 0.677291 | 0.944223 | False |

## Decision

- Decision: **NO_MATERIAL_PRIMARY_ORDER_SHORTCUT**
- Best legal Valence shortcut under discard-midpoint: `global_train_prior`, BA=`0.4756`
- Best legal Arousal shortcut under discard-midpoint: `global_train_prior`, BA=`0.5000`

## Mandatory Gates for Future Models

- Do not provide presentation order as a model input.
- Compare the physiological model with the best legal shortcut, not only with 0.5 balanced chance.
- Report legal subject-prior and stimulus-prior diagnostics.
- Keep repetitions 1–4 as sensitivity analyses and do not tune on them.
- Use paired uncertainty that respects crossed subjects and stimuli.
