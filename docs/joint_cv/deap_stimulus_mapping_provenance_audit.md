# DEAP Stimulus-Mapping Provenance Audit

Read-only audit. No training or fold construction was performed.

## Result

- Verdict: **UNVERIFIED_TRIAL_POSITION_AS_STIMULUS_ID**
- DEAP stimulus-aware manifest ready: `False`
- Strong authoritative local candidates: `0`
- Trial-position-as-stimulus assignment evidence: `1`

Project code appears to use the DEAP row/trial position as stimulus_id, while no authoritative local mapping from participant trial position to video/stimulus identity was found. Previous DEAP stimulus-only results must therefore be treated as relying on an unverified alignment assumption.

## Scientific Interpretation

A DEAP physical-trial row can be identified as `(subject_id, row_index)`, but Strict Joint subject–stimulus CV additionally requires a verified common stimulus identity across subjects. A project script assigning `stimulus_id = trial_index` is not by itself evidence that row positions represent the same video for every participant.

## Dataset-Level Mapping Candidates

| root_kind | relative_path | candidate_strength | authoritative_column_match | name_hits | columns |
| --- | --- | --- | --- | --- | --- |
| repository | docs/roca/deap_stimulus_only_loso_current_trial_labels.csv | project-derived-or-weak | True |  | subject_id;subject_file;stimulus_id;trial_id;trial_index_0based;data_shape;valence_score;arousal_score;dominance_score;liking_score |
| repository | docs/roca/deap_stimulus_only_loso_midpoint_high_current_trial_labels.csv | project-derived-or-weak | True |  | subject_id;subject_file;stimulus_id;trial_id;trial_index_0based;data_shape;valence_score;arousal_score;dominance_score;liking_score |

## Trial-Position Assignment Evidence

| artifact_path | source_kind | commit_sha | line_number | line |
| --- | --- | --- | --- | --- |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 579 | "`stimulus_id = trial_index` is not by itself evidence that row positions " |

## Mapping-Source References

| artifact_path | source_kind | commit_sha | line_number | line |
| --- | --- | --- | --- | --- |
| docs/roca/deap_stimulus_only_loso_current.json | current_worktree |  | 20 | "DEAP trial_id is treated as stimulus/video id.", |
| docs/roca/deap_stimulus_only_loso_midpoint_high_current.json | current_worktree |  | 20 | "DEAP trial_id is treated as stimulus/video id.", |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 8 | (subject_id, physical_trial_index) -> stimulus_id / video_id |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 33 | "participant_ratings", "video_list", "video_order", "stimulus_order", |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 34 | "trial_order", "experiment_id", "playlist", "sequence", "metadata", |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 38 | {"participant_id", "trial", "experiment_id"}, |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 39 | {"participant", "trial", "video_id"}, |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 56 | re.compile(r"participant_ratings", re.I), |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 57 | re.compile(r"experiment_id", re.I), |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 107 | "md": out_dir / "deap_stimulus_mapping_provenance_audit.md", |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 108 | "json": out_dir / "deap_stimulus_mapping_provenance_audit.json", |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 109 | "evidence": out_dir / "deap_stimulus_mapping_code_evidence.csv", |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 378 | "stimulus mapping schema. Its completeness and semantics must still be " |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 405 | verdict = "NO_VERIFIED_DEAP_STIMULUS_MAPPING" |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 491 | .get("stimulus_mapping_assessment", {}) |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 524 | "audit_type": "deap_stimulus_mapping_provenance", |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 558 | "# DEAP Stimulus-Mapping Provenance Audit", |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 648 | "trials/windowing and do not constitute a verified subject-trial-to-video " |
| scripts/joint_cv/02_audit_deap_stimulus_mapping.py | current_worktree |  | 657 | print("DEAP stimulus-mapping provenance audit completed.") |
| scripts/roca/01_deap_stimulus_only_loso.py | current_worktree |  | 398 | "DEAP trial_id is treated as stimulus/video id.", |

## Corrected Readiness

- I-DARE manifest ready: `True`
- I-DARE Joint-CV fold construction ready: `True`
- DEAP stimulus-aware manifest ready: `False`
- DEAP Joint-CV fold construction ready: `False`
- Combined DEAP+I-DARE Joint-CV ready: `False`

## Required Next Evidence

Locate and verify an authoritative DEAP mapping such as participant ratings or experiment metadata containing participant/subject ID, trial or presentation order, and experiment/video/stimulus ID. Until then, DEAP stimulus-held-out and Strict Joint results must remain blocked.
