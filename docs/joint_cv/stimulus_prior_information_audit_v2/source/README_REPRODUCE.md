# Reproduction Instructions

## Interpreter

The MM-SAGE-DG documented local interpreter:

```bash
"/mnt/HDD/AliWorks/HCI Tagging Database/HCI/bin/python3"
```

Python 3.11.15 · numpy 1.26.4 · pandas 2.2.2 · scipy 1.16.0 · h5py ·
Linux-7.0.0-28-generic-x86_64-with-glibc2.39. No package was installed, upgraded
or removed; no new environment was created. `scikit-learn` is present in the
environment but is **not** used — all metrics are implemented in-module so the
scoring rules are auditable in one file.

## Run

```bash
cd /mnt/HDD/AliWorks/MM-SAGE-DG-PARALLEL-UNIVERSE/docs/parallel-universe/v4/stimulus-prior-information-audit-v1-candidate
"/mnt/HDD/AliWorks/HCI Tagging Database/HCI/bin/python3" source/run_stimulus_prior_audit.py
```

Runtime ≈ 92 s. Writes into `derived/`, `validation/` and `provenance/` of the
package directory. Peak memory ≈ 1 GB (one DEAP subject container at a time).

To write somewhere else (used for the reproducibility check):

```bash
"/mnt/HDD/AliWorks/HCI Tagging Database/HCI/bin/python3" source/run_stimulus_prior_audit.py \
  --output-root /tmp/audit-rerun
```

Optional: `--bootstrap N` and `--permutations N` (defaults 10000 / 10000). Use
`--bootstrap 300 --permutations 300` for a ~9 s smoke run.

Runtime is ~92 s at the defaults; the refit-sensitivity bootstrap accounts for
about 20 s of that.

## Determinism

The root audit seed is `20260822`. Every stochastic step draws from a child seed
derived as `SHA256("MM-SAGE-DG|stimulus-prior-audit-v1|root=20260822|<parts>")`,
so bootstrap and permutation streams are independent per dataset/task/view yet
fully reproducible. The predictor itself contains no stochastic step.

Verified: two independent process runs produced hash-identical content for all
**12** derived artefacts. The comparison is **machine-generated**, not hand-written:

```bash
# run 1 -> a scratch directory
python3 source/run_stimulus_prior_audit.py --output-root /tmp/audit-refrun
# run 2 -> the package, comparing itself against run 1
python3 source/run_stimulus_prior_audit.py --verify-against /tmp/audit-refrun
```

The second invocation writes the `cross_process_rerun` block of
`validation/REPRODUCIBILITY_VALIDATION.json` itself
(`generated_by: run_stimulus_prior_audit.py --verify-against`). Without
`--verify-against`, `determinism_result` is `NOT_CHECKED_THIS_RUN` — the file never
asserts a comparison that was not actually performed by the script.

## Inputs

Resolved paths and sha256 for every input are in
`provenance/INPUT_AUTHORITY.json`. Summary:

| Input | Path |
|---|---|
| DEAP root | `/mnt/HDD/AliWorks/DEAP` |
| I-DARE root | `/mnt/HDD/AliWorks/I-DARE` |
| DEJA-VU shared authority (pinned `01351073…`) | `/mnt/HDD/AliWorks/DEJA-VU-Emotion-Recognition` |
| DEJA-VU Paper-2 pointers | `/mnt/HDD/AliWorks/MM-SAGE-DG-dejavu-paper2/docs/dejavu/` |
| DEAP/I-DARE configs, folds, loaders | `/mnt/HDD/AliWorks/MM-SAGE-DG-PARALLEL-UNIVERSE` |

**Note:** `configs/paths/local.yaml` does not exist in this worktree — only
`configs/paths/local.example.yaml`, which contains placeholder paths. Dataset
roots were therefore resolved to their actual on-disk locations (the ones the
repository's own loaders and tests use) and are recorded explicitly as constants
at the top of the script and in `INPUT_AUTHORITY.json`. If a real `local.yaml` is
later added, point `DEAP_ROOT` / `IDARE_ROOT` at its values and re-run.

**Note:** the DEJA-VU Paper-2 authority pointer documents live in the integration
repository `MM-SAGE-DG-dejavu-paper2`, not under `docs/dejavu/` of this worktree.

## External dependencies imported from the repository

The script reuses two stable, frozen repository loaders rather than
re-implementing dataset parsing:

* `mm_sage_dg.data.build_deap_inventory` — `src/mm_sage_dg/data/deap_inventory.py`
* `mm_sage_dg.data.build_idare_inventory` — `src/mm_sage_dg/data/idare_inventory.py`

Both are read-only, validate their own invariants (DEAP 1280 trials / 40 verified
stimuli; I-DARE 63 EEG∩EMG subjects × 32 stimuli = 2016 trials), and apply the
same `strict_binary_label` midpoint rule this audit requires. Their sha256 values
are recorded in `INPUT_AUTHORITY.json`. Both authorities are independently
cross-checked inside this script against the raw config CSVs
(`deap_subject_presentation_order.csv`, `idare_event_pairing.csv`); a disagreement
raises rather than being silently accepted.

DEJA-VU is read directly from the pinned shared authority's
`manifests/dejavu_cohort_b_primary_labels.csv` and
`folds/dejavu_joint_cv_repeated_assignments.csv`. The binary labels are
re-derived independently from the `after_valence` / `after_arousal` columns and
cross-checked row-by-row against the manifest's own `primary_*_label` columns.

## Signal data

This is a metadata/label analysis. No EEG or EMG values are read, transformed,
windowed or persisted.

The one unavoidable exception is mechanical: DEAP's official
`data_preprocessed_python/sNN.dat` pickle stores `data` and `labels` in a single
object, so deserialising it to reach `labels` necessarily materialises the
`(40, 40, 8064)` signal array in memory. The array is never indexed, transformed
or written, and is deleted immediately. This is documented in the upstream loader
docstring. I-DARE reads only `Fs`, `data.shape`, `event_begin` and `event_end`
via h5py — no signal samples. DEJA-VU touches no signal file at all.

## What the run produces

12 derived CSV artefacts, 4 validation JSONs, 2 provenance JSONs. The console
prints the View-A headline table, the leakage-suite tally (split into independent
computations vs restatements vs code-inspection assertions), the reproducibility
result and `AUDIT_STATUS`.

`STIMULUS_PRIOR_BOOTSTRAP_CI.csv` carries a `bootstrap_variant` column with two
values: `primary_fixed_predictions` (conditions on the fitted prior; understates
uncertainty) and `sensitivity_refit_within_resample` (refits the prior inside each
resample; conservative upper bound). Both are reported for View A.

## Verifying package integrity

```bash
cd /mnt/HDD/AliWorks/MM-SAGE-DG-PARALLEL-UNIVERSE/docs/parallel-universe/v4/stimulus-prior-information-audit-v1-candidate
sha256sum -c HASHES.sha256
```

`HASHES.sha256` is generated after the run and therefore does not contain an entry
for itself.
