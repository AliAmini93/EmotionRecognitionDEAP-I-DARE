# DEAP Official Mapping Resolution

Read-only audit. No model training or Joint-CV folds were created.

## Decision

- Status: **VERIFIED_DAT_ROWS_FOLLOW_COMMON_EXPERIMENT_ID_ORDER**
- DEAP stimulus-aware manifest ready: `True`
- DEAP Joint-CV ready: `True`
- Verified mapping rows: `1280`

Embedded .dat labels exactly match participant_ratings rows sorted by Experiment_id. Therefore .dat row position is already aligned to common stimulus identity.

## Metadata Search

- Search roots: `['/mnt/HDD/AliWorks', '/home/armin/Downloads', '/home/armin/Documents']`
- Candidates found: `1`
- participant_ratings.csv files found: `1`

| filename | path | exact_expected_name | archive_candidate | size_bytes |
| --- | --- | --- | --- | --- |
| participant_ratings.csv | /home/armin/Downloads/DEAP_metadata/participant_ratings.csv | True | False | 51471 |

## Alignment Tests Against Embedded DEAP Labels

| participant_ratings_path | hypothesis | subjects_compared | mean_abs_error | max_abs_error | exact_match_fraction_1e-8 |
| --- | --- | --- | --- | --- | --- |
| /home/armin/Downloads/DEAP_metadata/participant_ratings.csv | trial_order_alignment | 32 | 2.21842578125 | 8.0 | 0.0482421875 |
| /home/armin/Downloads/DEAP_metadata/participant_ratings.csv | experiment_order_alignment | 32 | 0.0 | 0.0 | 1.0 |

## Actual Project-Code Evidence

| artifact_path | line_number | category | line |
| --- | --- | --- | --- |
| scripts/roca/01_deap_stimulus_only_loso.py | 324 | stimulus_assignment | out = test[["subject_id", "stimulus_id", "trial_id"]].rename(columns={"subject_id": "test_subject"}).copy() |
| scripts/roca/01_deap_stimulus_only_loso.py | 324 | trial_assignment | out = test[["subject_id", "stimulus_id", "trial_id"]].rename(columns={"subject_id": "test_subject"}).copy() |
| scripts/roca/01_deap_stimulus_only_loso.py | 324 | explicit_assumption | out = test[["subject_id", "stimulus_id", "trial_id"]].rename(columns={"subject_id": "test_subject"}).copy() |
| scripts/roca/01_deap_stimulus_only_loso.py | 398 | explicit_assumption | "DEAP trial_id is treated as stimulus/video id.", |
| scripts/roca/01c_prior_baselines_no_global.py | 235 | stimulus_assignment | out["stimulus_id"] = out["stimulus_id"].astype(str) |
| scripts/roca/01c_prior_baselines_no_global.py | 236 | stimulus_assignment | out = out.drop_duplicates(["subject_id", "stimulus_id"]).reset_index(drop=True) |
| scripts/roca/01c_prior_baselines_no_global.py | 300 | stimulus_assignment | stim_code = pd.Categorical(df["stimulus_id"].astype(str), categories=stimuli).codes |

## Interpretation

The official metadata candidate has been verified by exact agreement with all four embedded DEAP ratings for all 32 subjects. The generated mapping may now be used to build the DEAP canonical physical-trial manifest.

- Mapping file: `docs/joint_cv/deap_verified_trial_stimulus_mapping.csv`