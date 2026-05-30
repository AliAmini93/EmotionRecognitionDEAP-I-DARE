#!/usr/bin/env python3
from __future__ import annotations

import ast
import csv
import json
import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
ROCA = ROOT / "docs" / "roca"
OUT_PREFIX = "idare_06a0b_prior_deep_learning_forensic_review_current"

INVENTORY_CANDIDATES = ROCA / "idare_06a0_deep_data_and_prior_model_inventory_current_prior_dl_candidates.csv"
DATA_INVENTORY = ROCA / "idare_06a0_deep_data_and_prior_model_inventory_current_data_inventory.csv"

FORCE_CANDIDATES = [
    "scripts/roca/05c_eeg_residual_training_stabilized_smoke.py",
    "scripts/roca/05g_eeg_residual_sign_aux_smoke.py",
    "scripts/roca/05u_eeg_oracle_arch_ablation.py",
    "docs/roca/eeg_oracle_arch_ablation_valence_current_predictions.csv",
    "docs/roca/eeg_oracle_arch_ablation_arousal_current_predictions.csv",
    "docs/chat_handoff_latest.md",
    "docs/handoff_bundle_latest.md",
    "docs/proposal_v1_1.md",
    "docs/idare_label_semantics_task_redesign_spec.md",
    "docs/idare_label_semantics_alternative_pairwise_feature_representation_patch_first_pass_predictions.csv",
]

IGNORE_NAME_RE = re.compile(r"06a0|06a0b|prior_dl_candidates|deep_data_and_prior_model_inventory", re.I)

ARCH_TERMS = [
    "CNN", "CONV", "LSTM", "GRU", "TRANSFORMER", "ATTENTION", "MHA",
    "TCN", "EEGNET", "MIXER", "MOE", "MLP", "RNN", "TEMPORAL",
    "RESIDUAL", "SIGN_AUX", "ORACLE",
]
INPUT_TERMS = [
    "idare_eeg_windows_32x640_float32_baseline_corrected.npy",
    "idare_eeg_windows_32x640_float32.npy",
    "idare_raw_emg_windows_2x10000_float32.npy",
    "idare_eeg_cache_index_baseline_corrected.csv",
    "idare_eeg_cache_index.csv",
    "baseline_corrected",
    "raw_emg",
    "eeg_windows",
]
SPLIT_TERMS = ["LOSO", "held", "held-out", "test_subject", "fold", "val_subject", "subject"]
TARGET_TERMS = ["valence", "arousal", "residual", "deviation", "stimulus_mean", "score", "binary", "macro_f1"]
METRIC_TERMS = ["rmse", "mae", "pearson", "spearman", "ccc", "macro", "f1", "auc", "accuracy", "loss"]
RISK_TERMS = [
    "smoke", "max-folds", "max_subjects", "epochs", "early", "seed",
    "oracle", "leak", "fold_safe", "selected_stimuli", "stimulus_only",
    "baseline", "no_global", "midpoint", "discard_midpoint",
]

def safe_read_text(path: Path, max_bytes: int = 600_000) -> str:
    try:
        with path.open("rb") as f:
            b = f.read(max_bytes)
        return b.decode("utf-8", errors="replace")
    except Exception as e:
        return f"[READ_ERROR] {e!r}"

def read_csv_head(path: Path, max_rows: int = 200) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.DictReader(f)
            rows = []
            for i, r in enumerate(reader):
                if i >= max_rows:
                    break
                rows.append(dict(r))
            return list(reader.fieldnames or []), rows
    except Exception:
        return [], []

def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

def md_table(rows: list[dict[str, Any]], max_rows: int | None = None) -> str:
    if not rows:
        return "_No rows._\n"
    shown = rows if max_rows is None else rows[:max_rows]
    fields: list[str] = []
    for r in shown:
        for k in r:
            if k not in fields:
                fields.append(k)
    def clean(x: Any) -> str:
        s = "" if x is None else str(x)
        s = s.replace("\n", " ").replace("|", "\\|")
        return s[:500]
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for r in shown:
        out.append("| " + " | ".join(clean(r.get(k, "")) for k in fields) + " |")
    if max_rows is not None and len(rows) > max_rows:
        out.append(f"\n_Showing {max_rows} of {len(rows)} rows._")
    return "\n".join(out) + "\n"

def find_lines(text: str, terms: list[str], max_hits: int = 12) -> list[str]:
    hits = []
    lower_terms = [t.lower() for t in terms]
    for i, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        if any(t.lower() in low for t in lower_terms):
            hits.append(f"L{i}: {line.strip()[:260]}")
        if len(hits) >= max_hits:
            break
    return hits

def grep_files(patterns: list[str], max_files: int = 2000) -> list[Path]:
    exts = {".py", ".sh", ".md", ".json", ".yaml", ".yml", ".csv", ".txt"}
    out = []
    for p in ROOT.rglob("*"):
        if len(out) >= max_files:
            break
        if not p.is_file():
            continue
        rel = str(p.relative_to(ROOT))
        if any(part in {".git", ".venv", "venv", "__pycache__"} for part in p.parts):
            continue
        if p.suffix.lower() not in exts:
            continue
        name = p.name.lower()
        rel_low = rel.lower()
        if any(x.lower() in rel_low for x in patterns):
            out.append(p)
    return out

def parse_py_ast_summary(path: Path, text: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "classes": "",
        "nn_modules": "",
        "functions": "",
        "argparse_flags": "",
        "imports": "",
    }
    try:
        tree = ast.parse(text)
    except Exception:
        return out
    classes = []
    nn_modules = []
    funcs = []
    imports = []
    flags = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
            base_names = []
            for b in node.bases:
                if isinstance(b, ast.Attribute):
                    base_names.append(b.attr)
                elif isinstance(b, ast.Name):
                    base_names.append(b.id)
            if any("Module" in b for b in base_names) or "Dataset" in base_names:
                nn_modules.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            funcs.append(node.name)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            # argparse.add_argument("--foo", ...)
            if isinstance(node.func, ast.Attribute) and node.func.attr == "add_argument" and node.args:
                a0 = node.args[0]
                if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                    flags.append(a0.value)
    out["classes"] = ", ".join(classes[:30])
    out["nn_modules"] = ", ".join(nn_modules[:20])
    out["functions"] = ", ".join(funcs[:50])
    out["argparse_flags"] = ", ".join(flags[:80])
    out["imports"] = ", ".join(sorted(set(imports))[:50])
    return out

def summarize_metrics_from_csv(path: Path) -> dict[str, Any]:
    fields, rows = read_csv_head(path, max_rows=5000)
    out: dict[str, Any] = {"csv_columns": ", ".join(fields[:40]), "csv_rows_sampled": len(rows)}
    if not rows:
        return out

    numeric_fields = []
    for f in fields:
        vals = []
        for r in rows[:200]:
            try:
                vals.append(float(r.get(f, "")))
            except Exception:
                pass
        if vals:
            numeric_fields.append(f)
    metric_fields = [f for f in numeric_fields if any(t in f.lower() for t in ["rmse", "mae", "pearson", "ccc", "f1", "acc", "auc", "loss", "score"])]
    summaries = []
    for f in metric_fields[:18]:
        vals = []
        for r in rows:
            try:
                v = float(r.get(f, ""))
                if math.isfinite(v):
                    vals.append(v)
            except Exception:
                continue
        if vals:
            summaries.append(f"{f}: min={min(vals):.6g}, mean={sum(vals)/len(vals):.6g}, max={max(vals):.6g}")
    out["metric_summary_sample"] = " || ".join(summaries)

    for key in ["target", "model", "arch_config", "arch_description", "task", "policy", "recipe", "fold", "test_subject", "subject_id"]:
        if key in fields:
            vals = []
            seen = set()
            for r in rows:
                v = str(r.get(key, ""))
                if v and v not in seen:
                    seen.add(v)
                    vals.append(v)
                if len(vals) >= 20:
                    break
            out[f"unique_{key}_sample"] = ", ".join(vals)
    return out

def load_candidate_paths() -> list[Path]:
    paths: list[Path] = []
    for s in FORCE_CANDIDATES:
        p = ROOT / s
        if p.exists():
            paths.append(p)

    if INVENTORY_CANDIDATES.exists():
        fields, rows = read_csv_head(INVENTORY_CANDIDATES, max_rows=300)
        for r in rows:
            s = r.get("path") or r.get("file") or ""
            if not s:
                continue
            p = ROOT / s
            if p.exists() and not IGNORE_NAME_RE.search(str(p)):
                paths.append(p)

    # Expand likely outputs around known deep scripts.
    extra_patterns = [
        "eeg_residual", "oracle_arch", "label_semantics", "representation_transfer",
        "diagnostic_sanity", "broader_eval_eeg", "broader_eval_emg",
    ]
    paths.extend(grep_files(extra_patterns, max_files=700))

    # de-dup preserving order
    seen = set()
    out = []
    for p in paths:
        rel = str(p.relative_to(ROOT))
        if rel in seen:
            continue
        seen.add(rel)
        if IGNORE_NAME_RE.search(rel) and "06a0b" not in rel:
            continue
        out.append(p)
    return out

def classify_failure_mode(row: dict[str, Any]) -> str:
    text = " ".join(str(v).lower() for v in row.values())
    modes = []
    if "smoke" in text or "max-folds" in text or "epochs 1" in text or "--epochs" in text:
        modes.append("possibly_smoke_or_not_final")
    if "oracle" in text:
        modes.append("oracle_or_arch_ablation_not_claim_model")
    if "macro_f1" in text or "binary" in text or "midpoint" in text:
        modes.append("old_binary_or_label_semantics_target")
    if "baseline_corrected" in text or "32x640" in text:
        modes.append("uses_short_eeg_window_cache")
    if "residual" in text or "deviation" in text:
        modes.append("residual_or_deviation_target_relevant")
    if "loso" in text or "test_subject" in text or "held" in text:
        modes.append("has_subject_holdout_language")
    if not modes:
        modes.append("needs_manual_review")
    return "; ".join(modes)

def main() -> None:
    paths = load_candidate_paths()

    candidate_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    decision_rows: list[dict[str, Any]] = []

    for p in paths:
        rel = str(p.relative_to(ROOT))
        size_kb = p.stat().st_size / 1024.0
        suffix = p.suffix.lower()

        row: dict[str, Any] = {
            "path": rel,
            "extension": suffix,
            "size_kb": round(size_kb, 2),
        }

        if suffix == ".csv":
            row.update(summarize_metrics_from_csv(p))
            metric_rows.append(dict(row))
            text_for_lines = safe_read_text(p, max_bytes=80_000)
        else:
            text_for_lines = safe_read_text(p)
            row.update(parse_py_ast_summary(p, text_for_lines) if suffix == ".py" else {})
            row["architecture_lines"] = " || ".join(find_lines(text_for_lines, ARCH_TERMS, max_hits=10))
            row["input_lines"] = " || ".join(find_lines(text_for_lines, INPUT_TERMS, max_hits=10))
            row["split_lines"] = " || ".join(find_lines(text_for_lines, SPLIT_TERMS, max_hits=10))
            row["target_metric_lines"] = " || ".join(find_lines(text_for_lines, TARGET_TERMS + METRIC_TERMS, max_hits=14))
            row["risk_lines"] = " || ".join(find_lines(text_for_lines, RISK_TERMS, max_hits=12))

        row["architecture_terms_found"] = ", ".join(t for t in ARCH_TERMS if t.lower() in text_for_lines.lower())
        row["input_terms_found"] = ", ".join(t for t in INPUT_TERMS if t.lower() in text_for_lines.lower())
        row["split_terms_found"] = ", ".join(t for t in SPLIT_TERMS if t.lower() in text_for_lines.lower())
        row["target_terms_found"] = ", ".join(t for t in TARGET_TERMS if t.lower() in text_for_lines.lower())
        row["metric_terms_found"] = ", ".join(t for t in METRIC_TERMS if t.lower() in text_for_lines.lower())
        row["forensic_failure_mode_hypothesis"] = classify_failure_mode(row)

        candidate_rows.append(row)

    # Synthesize the most relevant prior deep experiments.
    def has_path(sub: str) -> bool:
        return any(sub in r["path"] for r in candidate_rows)

    # Pull known evidence from files if present.
    handoff_text = safe_read_text(ROOT / "docs" / "chat_handoff_latest.md") if (ROOT / "docs" / "chat_handoff_latest.md").exists() else ""
    status_json = ROOT / "docs" / "project_status_current.json"
    status_text = safe_read_text(status_json) if status_json.exists() else ""

    decision_rows.append({
        "topic": "data_readiness_for_deep_representation",
        "finding": "Raw/near-raw caches exist: EEG [2016,32,640], baseline-corrected EEG [2016,32,640], raw EMG [2016,2,10000] from 06a0 inventory.",
        "implication": "Representation learning is possible locally, but current EEG window is 640 samples, not the full DEAP 60s stimulus; input policy must be explicit.",
        "risk": "A model on 5s windows may fail for reasons unrelated to physiology if the useful affect dynamics are outside the window.",
        "recommended_action": "Before 06a1, verify cache index alignment and whether 640-sample EEG windows are enough or were selected for prior pipeline constraints.",
    })
    decision_rows.append({
        "topic": "prior_deep_model_scope",
        "finding": "Candidate scripts/logs indicate prior deep experiments were mostly smoke/stabilization/oracle/architecture ablations rather than a final locked representation-learning claim.",
        "implication": "They are useful failure evidence, but should not be treated as having exhausted deep learning.",
        "risk": "Repeating these scripts without changing target/evaluation will reproduce the same no-go.",
        "recommended_action": "Use them as baselines and extract their input/split/target before building a minimal 06a1 prototype.",
    })
    decision_rows.append({
        "topic": "old_binary_classification_path",
        "finding": "Project handoff references old macro-F1 binary baselines: valence around 0.3953 and arousal around 0.4825, plus discard-midpoint sanity numbers.",
        "implication": "That path is not the same as current residual/deviation ROCA target and should not guide the new deep residual model too strongly.",
        "risk": "Binary label semantics can hide or distort subject-specific residual structure.",
        "recommended_action": "Do not optimize 06a1 for binary macro-F1; use residual/deviation gates, especially arousal high-disagreement G2 and locked B2 compatibility.",
    })
    decision_rows.append({
        "topic": "confirmed_positive_pocket",
        "finding": "05ajb confirmed arousal high-disagreement EEG-bandpower residual predictability; valence did not pass.",
        "implication": "The first deep model should target arousal high-disagreement residual/deviation, not full-task valence/arousal at once.",
        "risk": "Full-task deep training will dilute the only confirmed physiology signal pocket.",
        "recommended_action": "Build 06a1 as a small GPU EEG representation prototype for arousal high-disagreement trials first.",
    })
    decision_rows.append({
        "topic": "locked_baseline_constraint",
        "finding": "B2 locked personalization remains the main challenge baseline; fixed physiology failed bridge/rescue/sample-reduction.",
        "implication": "Deep physiology must either beat fixed EEG-bandpower on high-disagreement arousal or become a gate/uncertainty signal before trying to beat B2 globally.",
        "risk": "A direct additive physiology correction can worsen a strong personalization baseline.",
        "recommended_action": "Start with detection/triage and residual sign/scale calibration, then test locked-B2 bridge only if high-disagreement representation improves.",
    })

    # Add specific rows for top known scripts if present.
    for needle, interpretation in [
        ("05c_eeg_residual_training_stabilized_smoke.py", "prior EEG residual training smoke/stabilization"),
        ("05g_eeg_residual_sign_aux_smoke.py", "prior residual sign auxiliary smoke"),
        ("05u_eeg_oracle_arch_ablation.py", "prior oracle architecture ablation"),
    ]:
        matches = [r for r in candidate_rows if needle in r["path"]]
        if matches:
            m = matches[0]
            decision_rows.append({
                "topic": interpretation,
                "finding": f"Found {m['path']}. Architecture terms: {m.get('architecture_terms_found','')}. Inputs: {m.get('input_terms_found','')}.",
                "implication": m.get("forensic_failure_mode_hypothesis", ""),
                "risk": "Must inspect whether it was smoke-only/oracle-only and whether metrics are comparable to current locked ROCA gates.",
                "recommended_action": "Keep as prior baseline evidence; do not call it final until exact output metrics are tied to LOSO residual/deviation gates.",
            })

    next_rows = [
        {
            "priority": 1,
            "step": "06a1",
            "title": "Minimal arousal high-disagreement EEG representation prototype",
            "input": "baseline-corrected EEG cache [2016,32,640] plus index/labels",
            "model": "small CNN/TCN encoder with residual/deviation head; GPU smoke first",
            "evaluation_gate": "G2 high-disagreement arousal residual: beat fixed EEG-bandpower ridge from 05ajb; then check no degradation against locked B2 bridge",
            "why_this_next": "This is the only confirmed physiology signal pocket and avoids unbounded architecture fishing.",
        },
        {
            "priority": 2,
            "step": "06a1b",
            "title": "Input-window policy audit",
            "input": "DEAP/I-DARE cache indexes and raw/preprocessed files",
            "model": "no model; verify timing/channel/sample-rate policy",
            "evaluation_gate": "Document whether 640 EEG samples are sufficient and what portion of baseline/stimulus they represent.",
            "why_this_next": "If the cache only covers a weak/short segment, model design cannot fix missing signal.",
        },
        {
            "priority": 3,
            "step": "06a2",
            "title": "Subject-adaptive residual representation",
            "input": "learned EEG/EMG embedding plus k-shot subject context",
            "model": "FiLM/adapters/prototypical residual head",
            "evaluation_gate": "Beat B2 locked baseline or match B2 with fewer calibration samples.",
            "why_this_next": "Only after 06a1 proves learned features improve the confirmed arousal pocket.",
        },
    ]

    # Write outputs.
    write_csv(ROCA / f"{OUT_PREFIX}_candidate_forensics.csv", candidate_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_metric_file_summaries.csv", metric_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_decision_table.csv", decision_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_next_steps.csv", next_rows)

    payload = {
        "title": "I-DARE prior deep-learning forensic review",
        "candidate_count": len(candidate_rows),
        "metric_file_count": len(metric_rows),
        "decision_table": decision_rows,
        "next_steps": next_rows,
        "top_candidates": candidate_rows[:40],
    }
    (ROCA / f"{OUT_PREFIX}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines: list[str] = []
    lines.append("# I-DARE Prior Deep-Learning Forensic Review\n")
    lines.append("## Decision table\n")
    lines.append(md_table(decision_rows))
    lines.append("\n## Next steps\n")
    lines.append(md_table(next_rows))
    lines.append("\n## Top candidate files\n")
    slim = []
    for r in candidate_rows[:30]:
        slim.append({
            "path": r.get("path"),
            "size_kb": r.get("size_kb"),
            "architecture_terms_found": r.get("architecture_terms_found"),
            "input_terms_found": r.get("input_terms_found"),
            "target_terms_found": r.get("target_terms_found"),
            "forensic_failure_mode_hypothesis": r.get("forensic_failure_mode_hypothesis"),
        })
    lines.append(md_table(slim, max_rows=30))
    lines.append("\n## Interpretation\n")
    lines.append(
        "The prior deep-learning artifacts are useful, but the current evidence suggests they mostly document "
        "smoke/stabilization, binary-label, oracle, or architecture-ablation paths. The current ROCA target has shifted "
        "to residual/deviation predictability under locked subject-held-out gates. Therefore the next model should not be "
        "a broad architecture search. It should start with a minimal arousal high-disagreement EEG representation prototype, "
        "because 05ajb is the only place where fixed physiology produced confirmed residual signal.\n"
    )
    (ROCA / f"{OUT_PREFIX}.md").write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 06a0b completed.")
    for suffix in [
        "_candidate_forensics.csv",
        "_metric_file_summaries.csv",
        "_decision_table.csv",
        "_next_steps.csv",
        ".json",
        ".md",
    ]:
        print("wrote:", ROCA / f"{OUT_PREFIX}{suffix}")
    print("\nDecision table:")
    for r in decision_rows:
        print(f"- {r['topic']}: {r['finding']} -> {r['recommended_action']}")
    print("\nNext steps:")
    for r in next_rows:
        print(f"{r['priority']}. {r['step']} - {r['title']}")

if __name__ == "__main__":
    main()
