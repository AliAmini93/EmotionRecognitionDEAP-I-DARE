# I-DARE Root-Cause Triage Evaluation/Protocol Alignment Report

Status: `completed`

## Summary

- Protocol alignment is a primary decision risk: current held-out-subject targets must be reconciled with the original I-DARE evaluation framing.
- If original claims are not comparable to strict held-out-subject evaluation, more modeling would chase an unstable or misaligned target.
- Protocol reconciliation should be resolved before representation v2 or DG execution.

## Classification Pressure

- **A**: moderate if protocol exposes label/task mismatch
- **B**: strong support as primary if source protocol and locked protocol are not comparable
- **C**: blocked until protocol target is confirmed
- **D**: blocked until protocol target is confirmed
- **E**: strong fallback if current strict protocol is valid but unsupported by available evidence

## Evidence Snippets

- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_supcon_dg_pair_sampler_failure_analysis_objective.json:21` — "Was A5 better because of cross-subject SupCon, VREx, or their interaction?",
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_representation_label_task_redesign_objective.md:13` — The validation-only calibration protocol report was reviewed.
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_representation_label_task_redesign_objective.md:23` — 1. Are the current binary labels too noisy, unstable, or subject-dependent for the current subject-heldout setup?
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_representation_label_task_redesign_objective.md:107` — - final LOSO / final paper claim
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_diagnostic_sanity_tests_objective.md:66` — ### 3. Within-subject vs subject-heldout contrast
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_diagnostic_sanity_tests_objective.md:70` — Separate learnability from cross-subject generalization difficulty.
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_diagnostic_sanity_tests_objective.md:74` — - within-subject good and subject-heldout bad: subject/domain generalization is the likely core issue.
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_diagnostic_sanity_tests_objective.md:110` — - If within-subject is strong but subject-heldout is weak: recommend subject-generalization objective.
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_diagnostic_sanity_tests_objective.md:116` — - final LOSO / final paper claim
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md:34` — 3. Within-subject pair structure may have reinforced idiosyncratic subject patterns.
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md:68` — 3. cross-subject-positive-only SupCon
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md:69` — 4. within-subject anchor + cross-subject positive SupCon
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md:71` — 6. cross-subject SupCon + VREx
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md:80` — - same label and cross-subject only
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md:82` — - within-subject stable examples plus cross-subject positives
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md:93` — - cross-subject only
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_targeted_supcon_dg_pair_sampler_objective_ablation_design.md:141` — - If cross-subject positives help, the original pair definition was weak.
- `/mnt/HDD/AliWorks/EmotionRecognitionDEAP-I-DARE-root-cause-triage/docs/idare_project_synthesis_review_and_final_registry_update.md:65` — | current representation family | insufficient for robust cross-subject transfer |

## Notes

- No evaluation protocol was changed.
- No new operating-point claim was made.

