#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import os
import re
from pathlib import Path
from typing import Any

ROOT = Path.cwd()
CACHE = ROOT / ".cache"
DOCS = ROOT / "docs"
ROCA = DOCS / "roca"
OUT_PREFIX = "idare_06a1b_input_window_policy_audit_current"

ASSUMED_SAMPLE_RATE_HZ = 128.0
DEAP_EXPECTED_FULL_SAMPLES = 8064
DEAP_BASELINE_SAMPLES = 384
DEAP_STIMULUS_SAMPLES = 7680
DEAP_EEG_CHANNELS = 32
DEAP_TOTAL_CHANNELS = 40

CACHE_GLOBS = [
    ".cache/*eeg*window*.npy",
    ".cache/*emg*window*.npy",
    ".cache/*raw*emg*.npy",
    ".cache/*features*.npy",
    ".cache/*index*.csv",
    ".cache/*label*.csv",
    "docs/roca/*trial_labels*.csv",
    "docs/roca/*locked_baselines*.csv",
    "docs/roca/*high_disagreement*thresholds*.csv",
    "docs/roca/*high_disagreement*verdict*.csv",
    "docs/roca/*direct_deviation*decision_table*.csv",
]

SCRIPT_PATHS = [
    ROOT / "scripts/roca/05c_eeg_residual_training_stabilized_smoke.py",
    ROOT / "scripts/roca/05g_eeg_residual_sign_aux_smoke.py",
    ROOT / "scripts/roca/05u_eeg_oracle_arch_ablation.py",
    ROOT / "scripts/roca/06a0_idare_deep_data_and_prior_model_inventory.py",
]

SUBJECT_KEYS = ["subject_id", "subject", "participant_id", "participant", "subj", "test_subject", "held_subject"]
STIMULUS_KEYS = ["stimulus_id", "stimulus", "video_id", "trial", "trial_id", "image_id"]
TIME_KEYS = ["start", "end", "sample", "offset", "window", "time", "sec", "baseline", "stimulus"]


def safe_float(x: Any) -> float | None:
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except Exception:
        return None


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


def read_csv_rows(path: Path, max_rows: int = 100_000) -> tuple[list[str], list[dict[str, str]], int | None]:
    rows: list[dict[str, str]] = []
    total = 0
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.DictReader(f)
            fields = list(reader.fieldnames or [])
            for r in reader:
                total += 1
                if len(rows) < max_rows:
                    rows.append(dict(r))
        return fields, rows, total
    except Exception:
        return [], [], None


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
        return s[:450]
    out = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for r in shown:
        out.append("| " + " | ".join(clean(r.get(k, "")) for k in fields) + " |")
    if max_rows is not None and len(rows) > max_rows:
        out.append(f"\n_Showing {max_rows} of {len(rows)} rows._")
    return "\n".join(out) + "\n"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def infer_modality(path: Path, shape: list[int] | None = None) -> str:
    s = str(path).lower()
    if "emg" in s:
        return "EMG"
    if "eeg" in s:
        return "EEG"
    if shape and len(shape) >= 2:
        if shape[1] == 32:
            return "EEG_likely"
        if shape[1] == 2:
            return "EMG_likely"
        if shape[1] == 40:
            return "DEAP_40ch_likely"
    return "unknown"


def npy_info(path: Path) -> dict[str, Any]:
    import numpy as np
    arr = np.load(path, mmap_mode="r")
    shape = list(arr.shape)
    dtype = str(arr.dtype)
    modality = infer_modality(path, shape)

    samples = shape[-1] if len(shape) >= 3 else None
    channels = shape[1] if len(shape) >= 3 else None
    seconds = None
    if samples is not None:
        seconds = samples / ASSUMED_SAMPLE_RATE_HZ

    if modality.startswith("EEG") and samples is not None:
        if samples == DEAP_EXPECTED_FULL_SAMPLES:
            window_status = "FULL_DEAP_63S_BASELINE_PLUS_STIMULUS"
        elif samples == DEAP_STIMULUS_SAMPLES:
            window_status = "FULL_DEAP_60S_STIMULUS"
        elif samples == DEAP_BASELINE_SAMPLES:
            window_status = "DEAP_3S_BASELINE_ONLY"
        elif samples == 640:
            window_status = "SHORT_5S_WINDOW_AT_128HZ"
        else:
            window_status = "NONSTANDARD_EEG_WINDOW"
    elif modality.startswith("EMG") and samples is not None:
        window_status = "EMG_WINDOW_CHECK_SAMPLE_RATE_POLICY"
    else:
        window_status = "NOT_TIME_SERIES_OR_UNKNOWN"

    return {
        "path": rel(path),
        "kind": "npy",
        "size_mb": round(path.stat().st_size / (1024 * 1024), 4),
        "shape": str(shape),
        "dtype": dtype,
        "rows_trials": shape[0] if shape else None,
        "channels": channels,
        "samples": samples,
        "seconds_if_128hz": round(seconds, 4) if seconds is not None else None,
        "inferred_modality": modality,
        "window_status": window_status,
        "baseline_policy_in_filename": "baseline_corrected" if "baseline_corrected" in path.name.lower() else ("raw_or_unspecified" if samples else ""),
    }


def csv_info(path: Path) -> dict[str, Any]:
    fields, rows, total = read_csv_rows(path, max_rows=100_000)
    subj_col = next((c for c in fields if c.lower() in SUBJECT_KEYS), None)
    stim_col = next((c for c in fields if c.lower() in STIMULUS_KEYS), None)
    time_cols = [c for c in fields if any(k in c.lower() for k in TIME_KEYS)]
    label_cols = [c for c in fields if c.lower() in {"valence", "arousal", "valence_score", "arousal_score", "dominance", "liking"}]

    def unique_count(c: str | None) -> int | None:
        if not c:
            return None
        return len({r.get(c, "") for r in rows if r.get(c, "") != ""})

    duplicate_subject_stimulus_pairs = None
    full_grid_hint = ""
    if subj_col and stim_col and rows:
        pairs = [(r.get(subj_col, ""), r.get(stim_col, "")) for r in rows]
        pairs = [p for p in pairs if p[0] != "" and p[1] != ""]
        duplicate_subject_stimulus_pairs = len(pairs) - len(set(pairs))
        s_count = len({p[0] for p in pairs})
        t_count = len({p[1] for p in pairs})
        if s_count and t_count:
            full_grid_hint = f"unique_subjects*unique_stimuli={s_count*t_count}; rows_sample_or_total={total if total is not None else len(rows)}"

    minmax = {}
    for c in time_cols[:20]:
        vals = [safe_float(r.get(c)) for r in rows]
        vals = [v for v in vals if v is not None]
        if vals:
            minmax[c] = f"{min(vals):.6g}..{max(vals):.6g}"

    return {
        "path": rel(path),
        "kind": "csv",
        "size_mb": round(path.stat().st_size / (1024 * 1024), 4),
        "estimated_rows": total,
        "columns": ", ".join(fields[:80]),
        "subject_col": subj_col or "",
        "stimulus_col": stim_col or "",
        "unique_subjects_sample": unique_count(subj_col),
        "unique_stimuli_sample": unique_count(stim_col),
        "duplicate_subject_stimulus_pairs_sample": duplicate_subject_stimulus_pairs,
        "full_grid_hint": full_grid_hint,
        "label_cols": ", ".join(label_cols),
        "time_policy_cols": ", ".join(time_cols[:40]),
        "time_policy_minmax_sample": json.dumps(minmax, ensure_ascii=False),
    }


def gather_paths() -> list[Path]:
    paths: list[Path] = []
    for g in CACHE_GLOBS:
        paths.extend(ROOT.glob(g))
    # add data inventory discovered files from 06a0 if present
    data_inv = ROCA / "idare_06a0_deep_data_and_prior_model_inventory_current_data_inventory.csv"
    if data_inv.exists():
        fields, rows, _ = read_csv_rows(data_inv, max_rows=2000)
        for r in rows:
            p = ROOT / (r.get("path") or "")
            if p.exists() and p.suffix.lower() in {".npy", ".csv"}:
                paths.append(p)
    seen = set()
    out = []
    for p in paths:
        if not p.exists() or not p.is_file():
            continue
        key = rel(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def script_usage_rows() -> list[dict[str, Any]]:
    rows = []
    for p in SCRIPT_PATHS:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        cache_refs = sorted(set(re.findall(r'["\']([^"\']*(?:\.npy|\.csv))["\']', text)))
        flags = sorted(set(re.findall(r'--[a-zA-Z0-9_-]+', text)))
        relevant_lines = []
        for i, line in enumerate(text.splitlines(), 1):
            low = line.lower()
            if any(k in low for k in ["cache", "baseline", "window", "subject", "stimulus", "target", "residual", "deviation", "max-fold", "epochs"]):
                relevant_lines.append(f"L{i}: {line.strip()[:220]}")
            if len(relevant_lines) >= 20:
                break
        rows.append({
            "script": rel(p),
            "cache_refs": " | ".join(cache_refs[:30]),
            "arg_flags": " ".join(flags[:80]),
            "policy_lines": " || ".join(relevant_lines),
        })
    return rows


def main() -> None:
    paths = gather_paths()
    cache_rows: list[dict[str, Any]] = []
    index_rows: list[dict[str, Any]] = []
    alignment_rows: list[dict[str, Any]] = []

    for p in paths:
        try:
            if p.suffix.lower() == ".npy":
                cache_rows.append(npy_info(p))
            elif p.suffix.lower() == ".csv":
                info = csv_info(p)
                index_rows.append(info)
        except Exception as e:
            if p.suffix.lower() == ".npy":
                cache_rows.append({"path": rel(p), "kind": "npy", "read_error": repr(e)})
            else:
                index_rows.append({"path": rel(p), "kind": "csv", "read_error": repr(e)})

    # Alignment between likely npy caches and likely index files.
    npy_by_rows = {}
    for r in cache_rows:
        rows_trials = r.get("rows_trials")
        if rows_trials:
            npy_by_rows.setdefault(int(rows_trials), []).append(r)

    for ir in index_rows:
        n = ir.get("estimated_rows")
        if not n:
            continue
        n_int = int(n)
        matches = npy_by_rows.get(n_int, [])
        if matches:
            for m in matches:
                alignment_rows.append({
                    "index_path": ir.get("path"),
                    "npy_path": m.get("path"),
                    "rows_match": True,
                    "rows": n_int,
                    "npy_shape": m.get("shape"),
                    "subject_col": ir.get("subject_col"),
                    "stimulus_col": ir.get("stimulus_col"),
                    "unique_subjects_sample": ir.get("unique_subjects_sample"),
                    "unique_stimuli_sample": ir.get("unique_stimuli_sample"),
                    "duplicate_subject_stimulus_pairs_sample": ir.get("duplicate_subject_stimulus_pairs_sample"),
                    "time_policy_cols": ir.get("time_policy_cols"),
                })

    # Core decisions.
    eeg_640 = [r for r in cache_rows if str(r.get("shape", "")).startswith("[2016, 32, 640]") or r.get("samples") == 640 and "eeg" in str(r.get("path", "")).lower()]
    emg_10000 = [r for r in cache_rows if r.get("samples") == 10000 and "emg" in str(r.get("path", "")).lower()]
    full_eeg = [r for r in cache_rows if r.get("samples") in {DEAP_EXPECTED_FULL_SAMPLES, DEAP_STIMULUS_SAMPLES} and "eeg" in str(r.get("path", "")).lower()]

    decision_rows = [
        {
            "decision_item": "EEG_window_length",
            "observed": f"{len(eeg_640)} EEG-like 640-sample cache(s)" if eeg_640 else "no 640-sample EEG cache found",
            "interpretation": "640 samples at 128 Hz is 5 seconds, far shorter than DEAP's 60 s stimulus / 63 s baseline+stimulus expectation.",
            "risk_for_06a1": "A deep model may fail because the input window is too short or not the right temporal segment, not because EEG lacks residual signal.",
            "decision": "LOCK_CURRENT_06A1_AS_SHORT_WINDOW_FEASIBILITY_ONLY",
            "required_before_final_claim": "Either document exactly what the 640 samples represent or build/use full-window or multi-window EEG cache.",
        },
        {
            "decision_item": "EEG_baseline_policy",
            "observed": "baseline_corrected EEG cache found" if any("baseline_corrected" in str(r.get("path", "")).lower() for r in eeg_640) else "baseline policy not obvious",
            "interpretation": "Baseline correction is likely already applied for the main EEG cache, but the exact segment and correction rule need to be tied to index metadata.",
            "risk_for_06a1": "Inconsistent baseline handling can hide stimulus/residual structure or introduce silent leakage.",
            "decision": "USE_BASELINE_CORRECTED_CACHE_FOR_SMOKE_BUT_DOCUMENT_POLICY",
            "required_before_final_claim": "Record baseline/stimulus split and transformation in 06a1 report.",
        },
        {
            "decision_item": "EMG_window_length",
            "observed": f"{len(emg_10000)} EMG 10000-sample cache(s)" if emg_10000 else "no 10000-sample EMG cache found",
            "interpretation": "Raw EMG appears available as longer 2-channel windows, but sampling rate and alignment to EEG/stimulus need explicit documentation.",
            "risk_for_06a1": "Do not mix EMG into first deep prototype until EEG-only arousal high-disagreement route is understood.",
            "decision": "DEFER_EMG_TO_06A2_OR_AFTER_EEG_PROTOTYPE",
            "required_before_final_claim": "Audit EMG sample rate, channels, and alignment before multimodal fusion.",
        },
        {
            "decision_item": "full_trial_availability",
            "observed": f"{len(full_eeg)} full/stimulus-length EEG cache(s) found" if full_eeg else "no full 7680/8064-sample EEG cache found in current scan",
            "interpretation": "Current ready-to-train deep cache seems short-window rather than full-trial.",
            "risk_for_06a1": "Architecture search over short windows may be an unfair test of representation learning.",
            "decision": "RUN_06A1_MINIMAL_ONLY_THEN_DECIDE_FULL_WINDOW_CACHE",
            "required_before_final_claim": "If 06a1 short-window fails, do not conclude learned EEG is exhausted; run full/multi-window cache audit/build first.",
        },
        {
            "decision_item": "evaluation_scope",
            "observed": "Current confirmed positive physiology pocket is arousal high-disagreement EEG-bandpower.",
            "interpretation": "The next deep prototype should target arousal high-disagreement residual/deviation first.",
            "risk_for_06a1": "Training on full valence+arousal will dilute the only confirmed signal.",
            "decision": "06A1_TARGET_AROUSAL_HIGH_DISAGREEMENT_ONLY",
            "required_before_final_claim": "Must beat fixed EEG-bandpower high-disagreement ridge from 05ajb before any locked-B2 bridge claim.",
        },
    ]

    candidate_config_rows = [
        {
            "config_id": "06a1_smoke_short_window_eeg",
            "status": "GO_AS_FEASIBILITY_SMOKE",
            "input_cache": ".cache/idare_eeg_windows_32x640_float32_baseline_corrected.npy",
            "input_shape_expected": "[2016,32,640]",
            "window_policy": "5s at 128Hz if sample-rate assumption holds; exact segment must be documented",
            "target": "arousal residual/deviation on high-disagreement trials",
            "model": "small CNN/TCN encoder; residual head; GPU",
            "success_gate": "Beat 05ajb fixed EEG-bandpower residual model on arousal high-disagreement G2.",
            "non_success_interpretation": "Failure only means current 5s cache/prototype failed, not that representation learning is exhausted.",
        },
        {
            "config_id": "06a1_full_or_multiwindow_eeg",
            "status": "REQUIRED_IF_SHORT_WINDOW_FAILS_OR_FOR_FINAL_CLAIM",
            "input_cache": "to_build_or_locate",
            "input_shape_expected": "[trials,32,7680] or [trials,32,8064] or multi-window representation",
            "window_policy": "full 60s stimulus or documented baseline+stimulus split",
            "target": "same arousal high-disagreement residual/deviation gate",
            "model": "same or slightly larger TCN/Transformer after smoke",
            "success_gate": "Improves over short-window and fixed EEG-bandpower under same gates.",
            "non_success_interpretation": "Stronger evidence for representation/label bottleneck.",
        },
        {
            "config_id": "06a2_subject_adaptive_multimodal",
            "status": "DEFER",
            "input_cache": "EEG learned embedding + EMG learned/engineered embedding + k-shot subject context",
            "input_shape_expected": "depends on 06a1 and EMG alignment audit",
            "window_policy": "explicit alignment across modalities",
            "target": "residual correction or calibration sample reduction",
            "model": "adapter/FiLM/prototypical residual head",
            "success_gate": "Beat B2 locked or match B2 with fewer calibration samples.",
            "non_success_interpretation": "Current dataset/features likely insufficient for actionable physiology personalization.",
        },
    ]

    scripts_rows = script_usage_rows()

    payload = {
        "title": "I-DARE 06a1b input-window policy audit",
        "assumed_sample_rate_hz": ASSUMED_SAMPLE_RATE_HZ,
        "expected_deap": {
            "full_samples": DEAP_EXPECTED_FULL_SAMPLES,
            "baseline_samples": DEAP_BASELINE_SAMPLES,
            "stimulus_samples": DEAP_STIMULUS_SAMPLES,
            "eeg_channels": DEAP_EEG_CHANNELS,
            "total_channels": DEAP_TOTAL_CHANNELS,
        },
        "decision_table": decision_rows,
        "candidate_06a1_configs": candidate_config_rows,
        "cache_shape_inventory": cache_rows,
        "index_inventory": index_rows,
        "alignment_rows": alignment_rows,
        "script_usage_rows": scripts_rows,
    }

    write_csv(ROCA / f"{OUT_PREFIX}_cache_shape_inventory.csv", cache_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_index_inventory.csv", index_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_alignment_audit.csv", alignment_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_script_usage_audit.csv", scripts_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_decision_table.csv", decision_rows)
    write_csv(ROCA / f"{OUT_PREFIX}_candidate_06a1_configs.csv", candidate_config_rows)
    (ROCA / f"{OUT_PREFIX}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = []
    lines.append("# I-DARE 06a1b Input-Window Policy Audit\n")
    lines.append("## Decision table\n")
    lines.append(md_table(decision_rows))
    lines.append("\n## Candidate 06a1 configurations\n")
    lines.append(md_table(candidate_config_rows))
    lines.append("\n## Cache shape inventory, top rows\n")
    top_cache = sorted(cache_rows, key=lambda r: float(r.get("size_mb") or 0), reverse=True)[:25]
    lines.append(md_table(top_cache, max_rows=25))
    lines.append("\n## Alignment audit, top rows\n")
    lines.append(md_table(alignment_rows[:25], max_rows=25))
    lines.append("\n## Interpretation\n")
    lines.append(
        "The current ready-to-train EEG representation cache appears to be a short 640-sample window. "
        "At the assumed DEAP/I-DARE sample rate of 128 Hz, that is 5 seconds, not a full 60-second stimulus. "
        "Therefore 06a1 can be run as a controlled feasibility smoke for the confirmed arousal high-disagreement signal, "
        "but a negative result must not be interpreted as exhausting deep EEG representation learning. "
        "A final learned-representation claim needs either full-window/multi-window EEG or a documented justification "
        "for why the 640-sample segment is the intended physiological representation.\n"
    )
    (ROCA / f"{OUT_PREFIX}.md").write_text("\n".join(lines), encoding="utf-8")

    print("ROCA step 06a1b completed.")
    for suffix in [
        "_cache_shape_inventory.csv",
        "_index_inventory.csv",
        "_alignment_audit.csv",
        "_script_usage_audit.csv",
        "_decision_table.csv",
        "_candidate_06a1_configs.csv",
        ".json",
        ".md",
    ]:
        print("wrote:", ROCA / f"{OUT_PREFIX}{suffix}")

    print("\nDecision table:")
    for r in decision_rows:
        print(f"- {r['decision_item']}: {r['decision']} | {r['observed']}")

    print("\nCandidate 06a1 configs:")
    for r in candidate_config_rows:
        print(f"- {r['config_id']}: {r['status']} -> {r['success_gate']}")


if __name__ == "__main__":
    main()
