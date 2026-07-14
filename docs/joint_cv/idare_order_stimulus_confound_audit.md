# I-DARE Presentation-Order and Stimulus Confounding Audit

No EEG/EMG or physiological model was trained.

## Sequence Structure

- Unique complete stimulus sequences: `1` of `63` subjects
- Largest identical-sequence group: `63`
- Mean pairwise same-position fraction: `1.0000`
- Maximum pairwise same-position fraction: `1.0000`

## Stimulus–Order Association

- NMI(stimulus, exact presentation position): `1.0000`
- NMI(stimulus, 4-trial order bin): `0.7500`
- Median unique positions per stimulus: `1.0`
- Median modal-position fraction: `1.0000`
- Median normalized order entropy: `0.0000`

## Label Prevalence by Order Bin

| task | order_bin | positions | retained | high_prevalence | mean_score |
| --- | --- | --- | --- | --- | --- |
| valence | 1 | 1-4 | 237 | 0.2532 | 3.5794 |
| valence | 2 | 5-8 | 188 | 0.1436 | 3.4762 |
| valence | 3 | 9-12 | 214 | 0.5421 | 5.0992 |
| valence | 4 | 13-16 | 237 | 0.7384 | 6.0754 |
| valence | 5 | 17-20 | 190 | 0.9211 | 6.5635 |
| valence | 6 | 21-24 | 182 | 0.4505 | 5.0913 |
| valence | 7 | 25-28 | 196 | 0.6071 | 5.0595 |
| valence | 8 | 29-32 | 223 | 0.4529 | 4.3452 |
| arousal | 1 | 1-4 | 216 | 0.7222 | 6.0278 |
| arousal | 2 | 5-8 | 219 | 0.3516 | 4.123 |
| arousal | 3 | 9-12 | 220 | 0.4864 | 4.8492 |
| arousal | 4 | 13-16 | 232 | 0.194 | 3.3929 |
| arousal | 5 | 17-20 | 236 | 0.2331 | 3.4286 |
| arousal | 6 | 21-24 | 217 | 0.1659 | 3.3294 |
| arousal | 7 | 25-28 | 225 | 0.3556 | 4.123 |
| arousal | 8 | 29-32 | 234 | 0.5598 | 5.1905 |

## Quadratic Order-Only Null Tests

Train labels are permuted within source subject inside every outer cell. Primary test labels remain untouched.

| rep | role | task | observed_ba | null_median | effect | p | q | significant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | primary | valence | 0.6119 | 0.4215 | 0.1904 | 0.003984 | 0.003984 | True |
| 0 | primary | arousal | 0.6065 | 0.5 | 0.1065 | 0.003984 | 0.003984 | True |
| 1 | sensitivity | valence | 0.69 | 0.4912 | 0.1988 | 0.003984 | 0.003984 | True |
| 1 | sensitivity | arousal | 0.6185 | 0.5 | 0.1185 | 0.003984 | 0.003984 | True |
| 2 | sensitivity | valence | 0.5933 | 0.3813 | 0.212 | 0.003984 | 0.003984 | True |
| 2 | sensitivity | arousal | 0.5898 | 0.5 | 0.0898 | 0.003984 | 0.003984 | True |
| 3 | sensitivity | valence | 0.5743 | 0.3679 | 0.2064 | 0.003984 | 0.003984 | True |
| 3 | sensitivity | arousal | 0.5524 | 0.5 | 0.0524 | 0.003984 | 0.003984 | True |
| 4 | sensitivity | valence | 0.661 | 0.3939 | 0.2671 | 0.003984 | 0.003984 | True |
| 4 | sensitivity | arousal | 0.6278 | 0.5 | 0.1278 | 0.003984 | 0.003984 | True |

## Decision

- Decision: **ORDER_IS_A_MATERIAL_STIMULUS_COFOUNDER**

## Consequences for Future Models

- Do not provide presentation order as an input feature.
- Treat order-only quadratic performance as a mandatory legal shortcut baseline.
- Report order-stratified or order-adjusted uncertainty.
- A physiological model must improve beyond this shortcut, not merely beyond 0.5 balanced accuracy.
