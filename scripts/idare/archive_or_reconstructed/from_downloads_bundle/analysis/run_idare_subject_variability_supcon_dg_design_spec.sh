#!/usr/bin/env bash
set -euo pipefail

echo "===== 0) start cautious SupCon/DG design spec generation ====="
date
git status --short --branch
echo

echo "===== 1) choose python and require clean repo ====="
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif [ -x ".venv/bin/python3" ]; then
  PY=".venv/bin/python3"
else
  PY="python3"
fi
echo "PY=$PY"
"$PY" - <<'PY'
import sys
print(sys.executable)
import json, csv, re
from pathlib import Path
print("OK_IMPORTS")
PY

if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: repository is not clean. Commit/stash changes before creating design spec." >&2
  git status --short --branch >&2
  exit 1
fi
echo "OK_REPO_CLEAN"
echo

echo "===== 2) check required objective/evidence docs ====="
ls -lh \
  docs/idare_subject_variability_supcon_dg_design_objective.md \
  docs/idare_subject_variability_supcon_dg_design_objective.json \
  docs/idare_subject_variability_intervention_failure_analysis_review_status.md \
  docs/idare_subject_variability_intervention_failure_analysis_report.md \
  docs/idare_subject_variability_intervention_failure_analysis_report.json \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 3) scan project docs/scripts and generate SupCon/DG design spec ====="
"$PY" - <<'PY'
import csv
import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")
SCRIPTS = Path("scripts")
NOW = datetime.now(timezone.utc).isoformat()

OBJECTIVE_MD = DOCS / "idare_subject_variability_supcon_dg_design_objective.md"
OBJECTIVE_JSON = DOCS / "idare_subject_variability_supcon_dg_design_objective.json"
REVIEW_MD = DOCS / "idare_subject_variability_intervention_failure_analysis_review_status.md"
FAIL_REPORT_MD = DOCS / "idare_subject_variability_intervention_failure_analysis_report.md"
FAIL_REPORT_JSON = DOCS / "idare_subject_variability_intervention_failure_analysis_report.json"

SPEC_MD = DOCS / "idare_subject_variability_supcon_dg_design_spec.md"
SPEC_JSON = DOCS / "idare_subject_variability_supcon_dg_design_spec.json"
PAIR_CSV = DOCS / "idare_subject_variability_supcon_dg_pair_sampler_spec.csv"
HP_CSV = DOCS / "idare_subject_variability_supcon_dg_hyperparameter_registry.csv"
SMOKE_CSV = DOCS / "idare_subject_variability_supcon_dg_smoke_test_plan.csv"
RUN_CSV = DOCS / "idare_subject_variability_supcon_dg_first_pass_run_matrix.csv"

PROJECT_MD = DOCS / "project_status_current.md"
PROJECT_JSON = DOCS / "project_status_current.json"

for p in [OBJECTIVE_MD, OBJECTIVE_JSON, REVIEW_MD, FAIL_REPORT_MD, FAIL_REPORT_JSON, PROJECT_MD, PROJECT_JSON]:
    if not p.exists():
        raise SystemExit(f"ERROR: required file missing: {p}")

objective = json.loads(OBJECTIVE_JSON.read_text(encoding="utf-8"))
failure = json.loads(FAIL_REPORT_JSON.read_text(encoding="utf-8"))
diagnosis = failure.get("diagnosis", "subject_variability_diagnosis_still_supported_intervention_too_weak")

# Search project docs/scripts for existing SupCon/DG notes.
keyword_groups = {
    "supcon": [
        "supcon", "supervised contrastive", "contrastive", "positive pair",
        "positive pairs", "negative pair", "negative pairs", "hard negative",
        "temperature", "projection head", "contrastive loss",
    ],
    "domain_generalization": [
        "domain generalization", "domain-generalization", "vrex", "vr-ex", "risk variance",
        "irm", "coral", "dann", "environment", "environments", "domain", "subject as environment",
    ],
    "sampler": [
        "sampler", "batch sampler", "subject-aware", "balanced sampler",
        "class-balanced", "subject balanced", "anchor", "positive coverage",
    ],
}

skip_dirs = {".git", ".venv", "venv", "__pycache__", ".cache", "data", "datasets"}
candidate_files = []
for root in [DOCS, SCRIPTS]:
    if not root.exists():
        continue
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in skip_dirs for part in p.parts):
            continue
        if p.suffix.lower() not in {".md", ".py", ".json", ".txt", ".csv", ".yaml", ".yml"}:
            continue
        # Avoid scanning huge prediction CSVs and huge result JSONs.
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size > 2_000_000:
            continue
        candidate_files.append(p)

evidence_hits = []
for p in sorted(candidate_files):
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        continue
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        low = line.lower()
        matched = []
        for group, terms in keyword_groups.items():
            if any(t in low for t in terms):
                matched.append(group)
        if not matched:
            continue
        snippet_start = max(1, i - 1)
        snippet_end = min(len(lines), i + 1)
        snippet = []
        for j in range(snippet_start, snippet_end + 1):
            s = lines[j - 1].strip()
            if len(s) > 220:
                s = s[:217] + "..."
            snippet.append(f"L{j}: {s}")
        evidence_hits.append({
            "path": str(p),
            "line": i,
            "groups": sorted(set(matched)),
            "snippet": " | ".join(snippet),
        })

# Rank evidence: files with many relevant hits first, but keep compact.
file_counts = defaultdict(int)
for h in evidence_hits:
    file_counts[h["path"]] += 1

ranked_files = sorted(file_counts.items(), key=lambda kv: (-kv[1], kv[0]))
top_files = [{"path": path, "hit_count": count} for path, count in ranked_files[:25]]

# Keep up to 90 representative hits. Prioritize files with supcon/domain terms and docs over generated reports.
def hit_score(h):
    p = h["path"]
    group_score = 0
    if "supcon" in h["groups"]:
        group_score += 5
    if "domain_generalization" in h["groups"]:
        group_score += 4
    if "sampler" in h["groups"]:
        group_score += 3
    if p.startswith("docs/"):
        group_score += 2
    if "project_status_current" in p:
        group_score -= 2
    return (-group_score, p, h["line"])

evidence_hits_sorted = sorted(evidence_hits, key=hit_score)
representative_hits = evidence_hits_sorted[:90]

def has_group(group):
    return any(group in h["groups"] for h in evidence_hits)

found_summary = {
    "total_files_scanned": len(candidate_files),
    "total_hits": len(evidence_hits),
    "top_files": top_files,
    "has_supcon_notes": has_group("supcon"),
    "has_domain_generalization_notes": has_group("domain_generalization"),
    "has_sampler_notes": has_group("sampler"),
    "representative_hits": representative_hits,
}

# Design spec content.
pair_rows = [
    {
        "component": "task_scope",
        "rule_id": "TASK_001",
        "definition": "Run SupCon/DG only within one task at a time; never mix valence and arousal labels inside one contrastive target.",
        "required": "yes",
        "diagnostic_reason": "Avoids false positives/negatives caused by task-label mismatch.",
        "failure_action": "Abort smoke; fix task routing.",
    },
    {
        "component": "label_formulation",
        "rule_id": "LABEL_001",
        "definition": "First-pass labels use subject_top_bottom_quantile_q33 unless design review overrides it.",
        "required": "yes",
        "diagnostic_reason": "Targets subject-relative affect rather than global raw rating thresholds.",
        "failure_action": "Do not compare with prior first-pass results.",
    },
    {
        "component": "positive_pair",
        "rule_id": "POS_001",
        "definition": "Valid positive: same task, same subject-relative class, different trial/window.",
        "required": "yes",
        "diagnostic_reason": "Minimum SupCon validity.",
        "failure_action": "Drop anchor or rebuild batch.",
    },
    {
        "component": "positive_pair",
        "rule_id": "POS_002",
        "definition": "Preferred positive: same task, same class, different subject.",
        "required": "yes_when_feasible",
        "diagnostic_reason": "Directly targets cross-subject alignment.",
        "failure_action": "Log positive coverage; if coverage is low, revise sampler before training.",
    },
    {
        "component": "positive_pair",
        "rule_id": "POS_003",
        "definition": "Do not use validation samples as positives for train anchors.",
        "required": "yes",
        "diagnostic_reason": "Leakage prevention.",
        "failure_action": "Abort leakage smoke.",
    },
    {
        "component": "negative_pair",
        "rule_id": "NEG_001",
        "definition": "Valid negative: same task, opposite subject-relative class.",
        "required": "yes",
        "diagnostic_reason": "Ensures label-contrast signal is present.",
        "failure_action": "Rebuild batch.",
    },
    {
        "component": "hard_negative",
        "rule_id": "HNEG_001",
        "definition": "Optional hard negative: same or similar stimulus/context but opposite subject-relative class, if metadata supports it.",
        "required": "optional_first_pass_log_only",
        "diagnostic_reason": "May expose individual interpretation differences without forcing unstable mining initially.",
        "failure_action": "Do not enable hard-negative weighting until coverage is audited.",
    },
    {
        "component": "sampler",
        "rule_id": "SAMP_001",
        "definition": "Each SupCon batch must include at least 4 subjects and both classes.",
        "required": "yes",
        "diagnostic_reason": "Prevents subject-collapsed contrastive batches.",
        "failure_action": "Abort pair sampler integrity smoke.",
    },
    {
        "component": "sampler",
        "rule_id": "SAMP_002",
        "definition": "Each anchor should have at least one positive; cross-subject positive is preferred.",
        "required": "yes_log_anchor_exceptions",
        "diagnostic_reason": "SupCon loss can silently degrade if anchors lack positives.",
        "failure_action": "If anchor exceptions exceed 5%, revise sampler.",
    },
    {
        "component": "sampler",
        "rule_id": "SAMP_003",
        "definition": "Log per-batch subject count, class count, positive-pair coverage, and anchors_without_positive.",
        "required": "yes",
        "diagnostic_reason": "Makes failure diagnosable.",
        "failure_action": "Do not accept smoke without logs.",
    },
    {
        "component": "domain_generalization",
        "rule_id": "DG_001",
        "definition": "Default environment is subject_id.",
        "required": "yes",
        "diagnostic_reason": "Subject variability is the target diagnosis.",
        "failure_action": "Any alternative environment must be justified in a separate design update.",
    },
    {
        "component": "domain_generalization",
        "rule_id": "DG_002",
        "definition": "VREx/risk variance term is computed across train subjects/environments only.",
        "required": "yes",
        "diagnostic_reason": "Avoid validation leakage and direct target subject risk instability.",
        "failure_action": "Abort leakage smoke.",
    },
]
with PAIR_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(pair_rows[0].keys()))
    writer.writeheader()
    writer.writerows(pair_rows)

hp_rows = [
    {
        "parameter": "loss_family",
        "candidate_values": "CE+SupCon | CE+VREx | CE+SupCon+VREx",
        "default_first_pass": "CE+SupCon",
        "stage": "design_select_then_smoke",
        "why": "CE anchors task classification; SupCon directly tests cross-subject alignment.",
        "not_full_grid": "yes",
    },
    {
        "parameter": "supcon_temperature_tau",
        "candidate_values": "0.07 | 0.10 | 0.20",
        "default_first_pass": "0.10",
        "stage": "smoke_then_limited_ablation",
        "why": "Controls contrastive softness; too small can destabilize, too large can under-separate.",
        "not_full_grid": "yes",
    },
    {
        "parameter": "lambda_supcon",
        "candidate_values": "0.05 | 0.10 | 0.20 | 0.50",
        "default_first_pass": "0.10",
        "stage": "smoke_then_limited_ablation",
        "why": "Must be strong enough to align but not overpower CE.",
        "not_full_grid": "yes",
    },
    {
        "parameter": "lambda_vrex",
        "candidate_values": "0.01 | 0.05 | 0.10",
        "default_first_pass": "0.05 if VREx selected",
        "stage": "only_after_CE_SupCon_smoke_or_parallel_one_config",
        "why": "Penalizes environment risk variance; may reduce subject instability.",
        "not_full_grid": "yes",
    },
    {
        "parameter": "projection_dim",
        "candidate_values": "32 | 64 | 128",
        "default_first_pass": "64",
        "stage": "smoke_then_single_alternative_if_needed",
        "why": "Projection head capacity affects contrastive geometry.",
        "not_full_grid": "yes",
    },
    {
        "parameter": "warmup_epochs",
        "candidate_values": "0 | 3 | 5",
        "default_first_pass": "3",
        "stage": "smoke_required",
        "why": "Warmup can prevent early contrastive collapse.",
        "not_full_grid": "yes",
    },
    {
        "parameter": "batch_policy",
        "candidate_values": "largest_valid_subject_class_balanced_batch | fixed_64_if_valid | fixed_128_if_valid",
        "default_first_pass": "largest_valid_subject_class_balanced_batch",
        "stage": "sampler_integrity_smoke",
        "why": "Batch validity matters more than nominal batch size for SupCon.",
        "not_full_grid": "yes",
    },
    {
        "parameter": "optimizer_lr",
        "candidate_values": "reuse_current_mainline | one_lower_lr_if_micro_overfit_unstable",
        "default_first_pass": "reuse_current_mainline",
        "stage": "only_change_if_smoke_fails_due_to_optimization",
        "why": "Avoid mixing method effect with optimizer retuning.",
        "not_full_grid": "yes",
    },
]
with HP_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(hp_rows[0].keys()))
    writer.writeheader()
    writer.writerows(hp_rows)

smoke_rows = [
    {
        "order": 1,
        "smoke_test": "pair_sampler_integrity_smoke",
        "scope": "train folds only; one modality/task first",
        "pass_gate": "all batches have both classes, >=4 subjects, positive_pair_coverage >= 0.95, anchors_without_positive <= 0.05",
        "failure_interpretation": "Sampler/design issue; do not train.",
        "outputs_required": "batch_sampler_audit.csv; pair_coverage_summary.json",
    },
    {
        "order": 2,
        "smoke_test": "leakage_guard_smoke",
        "scope": "all preprocessing, scaling, pair construction",
        "pass_gate": "no validation labels/features used in train scaler, sampler, pair mining, environment risk computation",
        "failure_interpretation": "Protocol invalid; fix before any model run.",
        "outputs_required": "leakage_guard_report.md/json",
    },
    {
        "order": 3,
        "smoke_test": "supcon_micro_overfit_smoke",
        "scope": "tiny train-only subset",
        "pass_gate": "CE+SupCon loss decreases; train macro_f1 or proxy overfits; no NaN/collapse",
        "failure_interpretation": "Implementation or optimization bug.",
        "outputs_required": "micro_overfit_loss_trace.csv; embedding_trace.csv",
    },
    {
        "order": 4,
        "smoke_test": "shuffled_label_negative_control",
        "scope": "same fold/task with train labels shuffled",
        "pass_gate": "performance near chance; no suspicious leakage-driven gain",
        "failure_interpretation": "Leakage or invalid evaluation.",
        "outputs_required": "negative_control_report.md/json",
    },
    {
        "order": 5,
        "smoke_test": "one_fold_one_task_minimal_smoke",
        "scope": "one modality/task/fold; default hp only",
        "pass_gate": "no collapse; valid pair coverage logs; embedding diagnostics produced",
        "failure_interpretation": "Use loss/embedding diagnostics before expanding.",
        "outputs_required": "one_fold_smoke_report.md/json; predictions.csv",
    },
]
with SMOKE_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(smoke_rows[0].keys()))
    writer.writeheader()
    writer.writerows(smoke_rows)

run_rows = []
run_id = 1
for stage, method, hp_tag in [
    ("smoke", "CE_plus_SupCon", "tau0p10_lambdaSupCon0p10_proj64_warmup3"),
    ("first_pass_minimal", "CE_plus_SupCon", "tau0p10_lambdaSupCon0p10_proj64_warmup3"),
    ("first_pass_dg_probe", "CE_plus_VREx", "lambdaVREx0p05_warmup3"),
    ("first_pass_combined_probe", "CE_plus_SupCon_plus_VREx", "tau0p10_lambdaSupCon0p10_lambdaVREx0p05_proj64_warmup3"),
]:
    for modality in ["EEG", "EMG"]:
        for task in ["valence", "arousal"]:
            # Keep first-pass minimal: smoke is only fold1; minimal/probes can be 6 folds after smoke review.
            folds = "fold1_only" if stage == "smoke" else "folds_1_to_6"
            authorized_runs = 1 if stage == "smoke" else 6
            run_rows.append({
                "run_id": run_id,
                "stage": stage,
                "method": method,
                "modality": modality,
                "task": task,
                "fold_scope": folds,
                "label_formulation": "subject_top_bottom_quantile_q33",
                "recipe": "ce_class_weighted_base_plus_method_loss",
                "hyperparameter_tag": hp_tag,
                "authorized_runs_after_design_review": authorized_runs,
                "expand_condition": "Only after all smoke tests pass and design review authorizes training.",
            })
            run_id += 1
with RUN_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(run_rows[0].keys()))
    writer.writeheader()
    writer.writerows(run_rows)

# Interpret if existing notes were sparse.
evidence_risk = []
if not found_summary["has_supcon_notes"]:
    evidence_risk.append("No explicit SupCon notes were found by keyword scan; design spec must be treated as provisional until manually reviewed.")
if not found_summary["has_domain_generalization_notes"]:
    evidence_risk.append("No explicit domain-generalization notes were found by keyword scan; VREx/DG design must be checked manually.")
if not found_summary["has_sampler_notes"]:
    evidence_risk.append("No explicit sampler notes were found by keyword scan; sampler design is a high-risk implementation item.")

selected_first_pass = {
    "primary": "CE_plus_SupCon",
    "reason": "SupCon directly targets cross-subject same-class alignment; VREx/DG remains a controlled probe after smoke tests.",
    "dg_probe": "CE_plus_VREx and CE_plus_SupCon_plus_VREx are listed as design-stage probes, not full-grid runs.",
    "not_selected": "A full Cartesian hyperparameter search is explicitly not selected.",
}

decision_tree = [
    {
        "condition": "pair_sampler_integrity_smoke fails",
        "interpretation": "The method has not been tested; sampler is invalid.",
        "next_action": "Fix sampler/pair rules before any training.",
    },
    {
        "condition": "leakage_guard_smoke fails",
        "interpretation": "Protocol is invalid.",
        "next_action": "Fix preprocessing/pair construction and rerun smoke only.",
    },
    {
        "condition": "micro_overfit fails",
        "interpretation": "Implementation/optimization bug likely.",
        "next_action": "Inspect loss implementation, projection head, tau, lambda, lr.",
    },
    {
        "condition": "shuffled-label negative control succeeds too well",
        "interpretation": "Leakage or invalid evaluation likely.",
        "next_action": "Stop; audit labels, folds, sampler and metrics.",
    },
    {
        "condition": "SupCon loss decreases but validation macro-F1 does not improve",
        "interpretation": "Embedding alignment alone may not solve task signal, labels, or classifier calibration.",
        "next_action": "Inspect embedding distance metrics and per-subject risk before adding VREx or changing labels.",
    },
    {
        "condition": "VREx reduces risk variance but macro-F1 does not improve",
        "interpretation": "Subject risk stability improved without enough class signal.",
        "next_action": "Consider CE/SupCon balance, task formulation, or representation—not claim success.",
    },
    {
        "condition": "Only EMG or only EEG improves",
        "interpretation": "Subject variability may be modality-dependent or representation-dependent.",
        "next_action": "Keep modality-specific conclusions; do not fuse.",
    },
]

spec = {
    "status": "design_spec_complete_pending_human_review",
    "created_or_updated_utc": NOW,
    "objective": str(OBJECTIVE_MD),
    "objective_json": str(OBJECTIVE_JSON),
    "parent_review": str(REVIEW_MD),
    "evidence": {
        "intervention_failure_report": str(FAIL_REPORT_MD),
        "intervention_failure_json": str(FAIL_REPORT_JSON),
        "diagnosis": diagnosis,
    },
    "project_scan_summary": found_summary,
    "evidence_risks": evidence_risk,
    "selected_first_pass": selected_first_pass,
    "pair_sampler_spec": str(PAIR_CSV),
    "hyperparameter_registry": str(HP_CSV),
    "smoke_test_plan": str(SMOKE_CSV),
    "first_pass_run_matrix": str(RUN_CSV),
    "decision_tree": decision_tree,
    "not_authorized_by_this_spec": [
        "training",
        "performance claim",
        "mainline change",
        "fusion",
        "final LOSO claim",
        "broad hyperparameter search",
    ],
    "recommended_next_objective": "supcon_dg_smoke_tests_objective_after_human_review",
}
SPEC_JSON.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# Build compact evidence markdown.
top_file_md = "\n".join(
    f"- `{item['path']}`: {item['hit_count']} hits"
    for item in top_files[:15]
) or "- No keyword hits found."

hit_md_lines = []
for h in representative_hits[:35]:
    hit_md_lines.append(f"- `{h['path']}` L{h['line']} [{', '.join(h['groups'])}]: {h['snippet']}")
hit_md = "\n".join(hit_md_lines) if hit_md_lines else "- No representative hits found."

risk_md = "\n".join(f"- {r}" for r in evidence_risk) if evidence_risk else "- Keyword scan found at least some SupCon/DG/sampler-related evidence."

hp_md = "\n".join(
    f"- `{r['parameter']}`: candidates `{r['candidate_values']}`, default `{r['default_first_pass']}`"
    for r in hp_rows
)

smoke_md = "\n".join(
    f"{r['order']}. `{r['smoke_test']}` — pass gate: {r['pass_gate']}"
    for r in smoke_rows
)

decision_md = "\n".join(
    f"- If **{d['condition']}**: {d['interpretation']} Next: {d['next_action']}"
    for d in decision_tree
)

spec_md = f"""# I-DARE Subject-variability SupCon/DG Design Spec

## Status

Design/spec complete, pending human review.

No training is authorized by this document.

Generated UTC: `{NOW}`

## Parent Objective

- Objective: `{OBJECTIVE_MD}`
- Parent review: `{REVIEW_MD}`

## Starting Diagnosis

The accepted diagnosis is:

- `{diagnosis}`

Interpretation:

- subject variability remains supported;
- the subject-relative + preprocessing intervention was too weak/incomplete;
- SupCon/DG is scientifically plausible only if staged, smoke-tested, and diagnosable.

## Project Scan Summary

Files scanned: `{found_summary['total_files_scanned']}`

Keyword hits: `{found_summary['total_hits']}`

Top matching files:

{top_file_md}

## Evidence Risk

{risk_md}

## Representative SupCon/DG/Sampler Notes Found

{hit_md}

## Selected First-pass Direction

Primary design path:

- `CE_plus_SupCon`

Reason:

- SupCon directly targets cross-subject same-class representation alignment.
- This is closer to the accepted diagnosis than plain preprocessing or CE-only training.

Controlled probes:

- `CE_plus_VREx`
- `CE_plus_SupCon_plus_VREx`

Not selected:

- full Cartesian hyperparameter grid
- direct broad performance training
- fusion

## Pair and Sampler Rules

Detailed CSV:

- `{PAIR_CSV}`

Core rules:

- positives: same task, same class, cross-subject preferred/required when feasible;
- negatives: same task, opposite class;
- hard negatives: log/audit first, do not weight aggressively in first pass;
- sampler: at least 4 subjects and both classes per contrastive batch;
- anchor exceptions must be logged;
- validation samples must never be used in train pairs.

## Hyperparameter Registry

Detailed CSV:

- `{HP_CSV}`

Initial registry:

{hp_md}

Important rule:

- do not run the full Cartesian product.
- use smoke tests first, then a small staged matrix.

## Smoke Test Plan

Detailed CSV:

- `{SMOKE_CSV}`

Required smoke gates:

{smoke_md}

## Minimal First-pass Run Matrix Draft

Detailed CSV:

- `{RUN_CSV}`

This matrix is a draft for a future training objective only.

It is not authorized until human review accepts this design spec.

## Diagnostic Metrics to Log

Mandatory logs:

- macro-F1
- balanced accuracy
- one-class prediction flag
- CE loss
- SupCon loss
- VREx loss when applicable
- environment risk variance
- same-class cross-subject embedding distance
- different-class cross-subject embedding distance
- positive-pair coverage
- anchors without positives
- batch subject count distribution

## Failure Interpretation Decision Tree

{decision_md}

## Pass/Fail Interpretation

A future SupCon/DG run should be considered scientifically useful only if it can answer:

1. Did sampler integrity hold?
2. Did leakage controls hold?
3. Did SupCon loss behave correctly?
4. Did embedding geometry move in the expected cross-subject direction?
5. Did task metrics improve beyond previous subject-relative/preprocessed first pass?
6. If not, did diagnostics identify whether the failure was task-label, sampler, optimization, or representation related?

## Recommendation

Next objective after human review:

- `supcon_dg_smoke_tests_objective_after_human_review`

That objective should implement smoke tests only.

Full SupCon/DG performance training should wait until smoke tests pass.

## Not Authorized

- training
- performance claim
- mainline change
- EEG+EMG fusion
- final LOSO claim
- broad hyperparameter search
"""
SPEC_MD.write_text(spec_md, encoding="utf-8")

# Update central roadmap.
project_md = PROJECT_MD.read_text(encoding="utf-8")
row = "| I-DARE subject-variability SupCon/DG design spec | cautious design/spec complete; pending human review; smoke tests required before training | yes | `docs/idare_subject_variability_supcon_dg_design_spec.md` | Human review / closeout before SupCon/DG smoke-test objective. | EEG+EMG fusion; final LOSO claim; direct SupCon/DG training; broad hyperparameter search; mainline change. |"
if row not in project_md:
    lines = project_md.splitlines()
    out = []
    inserted = False
    for line in lines:
        out.append(line)
        if line.startswith("| I-DARE cautious subject-variability SupCon/DG design objective |"):
            out.append(row)
            inserted = True
    if not inserted:
        raise SystemExit("ERROR: could not find cautious SupCon/DG objective row in project_status_current.md")
    project_md = "\n".join(out) + "\n"

bullet = "- Cautious SupCon/DG design spec is complete in `docs/idare_subject_variability_supcon_dg_design_spec.md`; next work is human review/closeout, then smoke tests only—not full training."
if bullet not in project_md:
    marker = "\n## Documentation Gap Closed by This File"
    if marker not in project_md:
        raise SystemExit("ERROR: marker not found in project_status_current.md")
    project_md = project_md.replace(marker, "\n" + bullet + "\n" + marker)
PROJECT_MD.write_text(project_md, encoding="utf-8")

project_json = json.loads(PROJECT_JSON.read_text(encoding="utf-8"))
decisions = project_json.setdefault("decisions", {})
decisions["idare_subject_variability_supcon_dg_design_spec"] = {
    "status": "design_spec_complete_pending_human_review",
    "evidence": str(SPEC_MD),
    "evidence_json": str(SPEC_JSON),
    "pair_sampler_spec": str(PAIR_CSV),
    "hyperparameter_registry": str(HP_CSV),
    "smoke_test_plan": str(SMOKE_CSV),
    "first_pass_run_matrix": str(RUN_CSV),
    "diagnosis": diagnosis,
    "recommended_next_objective": "supcon_dg_smoke_tests_objective_after_human_review",
    "training_authorized": False,
    "mainline_changed": False,
}
PROJECT_JSON.write_text(json.dumps(project_json, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")

print("OK_SUPCON_DG_DESIGN_SPEC_WRITTEN")
print(SPEC_MD)
print(SPEC_JSON)
print(PAIR_CSV)
print(HP_CSV)
print(SMOKE_CSV)
print(RUN_CSV)
print("scan_hits=", found_summary["total_hits"])
print("recommended_next_objective= supcon_dg_smoke_tests_objective_after_human_review")
PY
echo

echo "===== 4) validate generated outputs ====="
"$PY" - <<'PY'
import csv
import json
from pathlib import Path

json_paths = [
    Path("docs/idare_subject_variability_supcon_dg_design_spec.json"),
    Path("docs/project_status_current.json"),
]
for p in json_paths:
    data = json.loads(p.read_text(encoding="utf-8"))
    print("OK_JSON:", p)
    if p.name == "idare_subject_variability_supcon_dg_design_spec.json":
        if data.get("status") != "design_spec_complete_pending_human_review":
            raise SystemExit("ERROR: wrong design spec status")
        for key in ["pair_sampler_spec", "hyperparameter_registry", "smoke_test_plan", "first_pass_run_matrix"]:
            if key not in data:
                raise SystemExit(f"ERROR: missing {key}")

csv_expect = {
    "docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv": 8,
    "docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv": 6,
    "docs/idare_subject_variability_supcon_dg_smoke_test_plan.csv": 5,
    "docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv": 8,
}
for name, min_rows in csv_expect.items():
    p = Path(name)
    with p.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(p.name, "rows=", len(rows))
    if len(rows) < min_rows:
        raise SystemExit(f"ERROR: too few rows in {p}: {len(rows)} < {min_rows}")

text = Path("docs/idare_subject_variability_supcon_dg_design_spec.md").read_text(encoding="utf-8")
for term in ["Smoke Test Plan", "Hyperparameter Registry", "Failure Interpretation", "positive", "negative", "VREx", "SupCon"]:
    if term not in text:
        raise SystemExit(f"ERROR: missing term in design spec md: {term}")

print("ALL_SUPCON_DG_DESIGN_OUTPUTS_VALID")
PY

grep -n "## Status\|## Project Scan Summary\|## Selected First-pass Direction\|## Hyperparameter Registry\|## Smoke Test Plan\|## Failure Interpretation" docs/idare_subject_variability_supcon_dg_design_spec.md
grep -n "SupCon/DG design spec\|smoke tests only" docs/project_status_current.md
echo

echo "===== 5) file list ====="
ls -lh \
  docs/idare_subject_variability_supcon_dg_design_spec.md \
  docs/idare_subject_variability_supcon_dg_design_spec.json \
  docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv \
  docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv \
  docs/idare_subject_variability_supcon_dg_smoke_test_plan.csv \
  docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv \
  docs/project_status_current.md \
  docs/project_status_current.json
echo

echo "===== 6) status before commit ====="
git status --short --branch
echo

echo "===== 7) commit and push design spec ====="
git add \
  docs/idare_subject_variability_supcon_dg_design_spec.md \
  docs/idare_subject_variability_supcon_dg_design_spec.json \
  docs/idare_subject_variability_supcon_dg_pair_sampler_spec.csv \
  docs/idare_subject_variability_supcon_dg_hyperparameter_registry.csv \
  docs/idare_subject_variability_supcon_dg_smoke_test_plan.csv \
  docs/idare_subject_variability_supcon_dg_first_pass_run_matrix.csv \
  docs/project_status_current.md \
  docs/project_status_current.json

git commit -m "docs: add I-DARE SupCon DG design spec"

git push origin main
echo

echo "===== 8) final status ====="
git status --short --branch
echo "LOG_SAVED_TO=/tmp/idare_supcon_dg_design_spec.log"
