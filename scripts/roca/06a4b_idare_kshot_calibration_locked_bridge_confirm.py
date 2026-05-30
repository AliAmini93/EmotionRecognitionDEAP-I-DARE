#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROCA = Path("docs/roca")
OUT_PREFIX = "idare_06a4b_kshot_calibration_locked_bridge_confirm_current"


def read_csv_optional(path: Path) -> pd.DataFrame:
    try:
        if path.exists():
            return pd.read_csv(path)
    except Exception as exc:
        print(f"[WARN] failed to read {path}: {exc}")
    return pd.DataFrame()


def first_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    cols = list(df.columns)
    low = {c.lower(): c for c in cols}
    for c in candidates:
        if c in cols:
            return c
        if c.lower() in low:
            return low[c.lower()]
    return None


def rmse(err: np.ndarray) -> float:
    err = np.asarray(err, dtype=float)
    err = err[np.isfinite(err)]
    if err.size == 0:
        return float("nan")
    return float(np.sqrt(np.mean(err * err)))


def corr(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    a = a[m]
    b = b[m]
    if a.size < 3 or float(np.std(a)) <= 1e-12 or float(np.std(b)) <= 1e-12:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def sign_acc(y: np.ndarray, p: np.ndarray) -> float:
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    m = np.isfinite(y) & np.isfinite(p)
    if not np.any(m):
        return float("nan")
    return float(np.mean(np.sign(y[m]) == np.sign(p[m])))


def bootstrap_ci(x: np.ndarray, rng: np.random.Generator, n_boot: int = 3000) -> tuple[float, float]:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return float("nan"), float("nan")
    if x.size == 1:
        return float(x[0]), float(x[0])
    vals = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        idx = rng.integers(0, x.size, size=x.size)
        vals[i] = float(np.mean(x[idx]))
    return float(np.quantile(vals, 0.025)), float(np.quantile(vals, 0.975))


def signflip_p_gt_zero(x: np.ndarray, rng: np.random.Generator, n_perm: int = 5000) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return float("nan")
    obs = float(np.mean(x))
    sims = []
    for _ in range(n_perm):
        signs = rng.choice([-1.0, 1.0], size=x.size)
        sims.append(float(np.mean(signs * x)))
    sims = np.asarray(sims)
    return float((np.sum(sims >= obs) + 1) / (n_perm + 1))


def md_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df is None or df.empty:
        return "_empty_\n"
    x = df.copy()
    if max_rows is not None:
        x = x.head(max_rows)
    x = x.fillna("")
    cols = list(x.columns)
    rows = [[str(v) for v in row] for row in x.to_numpy().tolist()]
    widths = []
    for i, c in enumerate(cols):
        widths.append(max(len(str(c)), *(len(r[i]) for r in rows)))
    def fmt(row: list[str]) -> str:
        return "| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(cols))) + " |"
    out = [fmt([str(c) for c in cols]), "| " + " | ".join("-" * w for w in widths) + " |"]
    out.extend(fmt(r) for r in rows)
    return "\n".join(out) + "\n"


def git_short() -> str:
    try:
        return subprocess.check_output(["git", "status", "--short"], text=True, stderr=subprocess.STDOUT)
    except Exception as exc:
        return f"[git status failed: {exc}]"


def loso_stimulus_prior_residual(df: pd.DataFrame, y_col: str, stim_col: str) -> tuple[np.ndarray, np.ndarray]:
    y = df[y_col].astype(float).to_numpy()
    stim_sum = df.groupby(stim_col)[y_col].transform("sum").astype(float).to_numpy()
    stim_count = df.groupby(stim_col)[y_col].transform("count").astype(float).to_numpy()
    pred = np.where(stim_count > 1, (stim_sum - y) / np.maximum(stim_count - 1, 1), np.nan)
    pred = np.where(np.isfinite(pred), pred, float(np.nanmean(y)))
    return pred.astype(float), (y - pred).astype(float)


def get_high_threshold(target: str, residual: np.ndarray) -> tuple[float, str]:
    verdict = read_csv_optional(ROCA / "idare_high_disagreement_direct_deviation_confirmatory_stats_current_verdict.csv")
    if not verdict.empty and "target" in verdict.columns and "abs_residual_threshold" in verdict.columns:
        m = verdict[verdict["target"].astype(str) == target]
        if not m.empty:
            return float(m.iloc[0]["abs_residual_threshold"]), "05ajb_confirmatory_threshold"
    return float(np.nanquantile(np.abs(residual), 0.75)), "q75_fallback"


def get_locked_bridge_rmse(target: str) -> tuple[float, str]:
    candidates = [
        ROCA / "idare_high_disagreement_personalization_bridge_current_decision_table.csv",
        ROCA / "idare_high_disagreement_personalization_bridge_current_bridge_metrics.csv",
    ]
    for path in candidates:
        df = read_csv_optional(path)
        if df.empty:
            continue
        if "target" not in df.columns or "locked_rmse" not in df.columns:
            continue
        m = df[df["target"].astype(str) == target].copy()
        if m.empty:
            continue
        # Prefer the q=.75 decision row if present.
        if "quantile" in m.columns:
            mq = m[np.isclose(m["quantile"].astype(float), 0.75)]
            if not mq.empty:
                m = mq
        return float(m.iloc[0]["locked_rmse"]), str(path)
    return float("nan"), "locked_bridge_file_missing"


def load_fixed_bandpower_pred(df: pd.DataFrame, target: str, subj_col: str, stim_col: str) -> tuple[np.ndarray | None, str]:
    path = ROCA / "idare_residual_physiology_feature_audit_current_predictions.csv"
    pred_df = read_csv_optional(path)
    if pred_df.empty:
        return None, f"missing {path}"

    tcol = first_col(pred_df, ["target"])
    bcol = first_col(pred_df, ["feature_block", "block"])
    pcol = first_col(pred_df, ["y_pred_deviation", "pred_deviation", "y_pred_residual"])
    pscol = first_col(pred_df, ["test_subject", "subject_id", "subject"])
    stcol = first_col(pred_df, ["stimulus_id", "stimulus"])
    if any(x is None for x in [tcol, bcol, pcol, pscol, stcol]):
        return None, "fixed prediction columns missing"

    f = pred_df[(pred_df[tcol].astype(str) == target) & (pred_df[bcol].astype(str) == "eeg_bandpower")].copy()
    if f.empty:
        return None, "no eeg_bandpower fixed rows"
    f = f.drop_duplicates(subset=[pscol, stcol], keep="first")
    f["subject_key"] = f[pscol].astype(str)
    f["stimulus_key"] = f[stcol].astype(str)
    f = f[["subject_key", "stimulus_key", pcol]].rename(columns={pcol: "fixed_pred"})

    base = pd.DataFrame({
        "row_id": np.arange(len(df)),
        "subject_key": df[subj_col].astype(str).to_numpy(),
        "stimulus_key": df[stim_col].astype(str).to_numpy(),
    })
    merged = base.merge(f, on=["subject_key", "stimulus_key"], how="left").sort_values("row_id")
    arr = merged["fixed_pred"].to_numpy(dtype=float)
    finite_rate = float(np.mean(np.isfinite(arr)))
    if finite_rate < 0.95:
        return None, f"fixed alignment incomplete finite_rate={finite_rate:.3f}"
    return arr, f"loaded {path} rows={len(f)} finite_rate={finite_rate:.3f}"


def eval_kshot_method(
    residual: np.ndarray,
    base_pred: np.ndarray,
    high_mask: np.ndarray,
    subjects: np.ndarray,
    k: int,
    repeats: int,
    rng: np.random.Generator,
    locked_rmse: float,
    fixed_pred: np.ndarray | None,
) -> tuple[dict[str, Any], pd.DataFrame]:
    y_all = []
    p_all = []
    f_all = []
    repeat_subject_rows = []

    unique_subjects = np.array(sorted(pd.unique(subjects)))
    for rep in range(repeats):
        for s in unique_subjects:
            idx_s = np.flatnonzero(subjects == s)
            if idx_s.size <= k:
                continue
            cal = rng.choice(idx_s, size=k, replace=False)
            cal_set = set(cal.tolist())
            eval_idx = np.array([i for i in idx_s if i not in cal_set and high_mask[i]], dtype=int)
            if eval_idx.size == 0:
                continue

            bias = float(np.mean(residual[cal] - base_pred[cal]))
            pred = base_pred[eval_idx] + bias

            y_all.append(residual[eval_idx])
            p_all.append(pred)
            if fixed_pred is not None:
                f_all.append(fixed_pred[eval_idx])

            z = rmse(residual[eval_idx])
            m = rmse(residual[eval_idx] - pred)
            repeat_subject_rows.append({
                "repeat": rep,
                "subject": s,
                "k_calibration": k,
                "n_eval": int(eval_idx.size),
                "zero_rmse": z,
                "candidate_rmse": m,
                "improvement_zero_minus_candidate": z - m,
            })

    if not y_all:
        return {}, pd.DataFrame()

    y = np.concatenate(y_all)
    p = np.concatenate(p_all)
    zero = rmse(y)
    cand = rmse(y - p)
    fixed_same = rmse(y - np.concatenate(f_all)) if fixed_pred is not None and f_all else float("nan")

    rs = pd.DataFrame(repeat_subject_rows)
    imps = rs["improvement_zero_minus_candidate"].to_numpy(dtype=float)
    ci_lo, ci_hi = bootstrap_ci(imps, rng)
    wins = int(np.sum(imps > 1e-12))
    losses = int(np.sum(imps < -1e-12))

    row = {
        "k_calibration": k,
        "n_repeats": repeats,
        "n_eval_repeated": int(y.size),
        "subjects": int(len(unique_subjects)),
        "zero_rmse": zero,
        "candidate_rmse": cand,
        "lift_vs_zero": zero - cand,
        "fixed_rmse_same_eval": fixed_same,
        "lift_vs_fixed_same_eval": fixed_same - cand if np.isfinite(fixed_same) else float("nan"),
        "locked_bridge_rmse_05ak": locked_rmse,
        "candidate_minus_locked_bridge_rmse": cand - locked_rmse if np.isfinite(locked_rmse) else float("nan"),
        "lift_vs_locked_bridge_rmse": locked_rmse - cand if np.isfinite(locked_rmse) else float("nan"),
        "pearson": corr(y, p),
        "sign_acc": sign_acc(y, p),
        "mean_repeat_subject_improvement_zero_minus_candidate": float(np.mean(imps)),
        "ci95_low_repeat_subject_improvement": ci_lo,
        "ci95_high_repeat_subject_improvement": ci_hi,
        "signflip_p_mean_improvement_gt_zero": signflip_p_gt_zero(imps, rng),
        "wins_vs_zero_repeat_subject": wins,
        "losses_vs_zero_repeat_subject": losses,
        "win_margin_vs_zero_repeat_subject": wins - losses,
    }
    return row, rs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=Path, default=Path(".cache/idare_eeg_cache_index_baseline_corrected.csv"))
    ap.add_argument("--target", type=str, default="arousal")
    ap.add_argument("--repeats", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20260531)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)

    if not args.index.exists():
        raise FileNotFoundError(args.index)
    df = pd.read_csv(args.index)

    subj_col = first_col(df, ["subject_id", "subject", "test_subject", "participant_id", "participant"])
    stim_col = first_col(df, ["stimulus_id", "stimulus", "trial_id"])
    y_col = first_col(df, [f"{args.target}_score", args.target, f"{args.target}_rating", f"label_{args.target}"])
    if subj_col is None or stim_col is None or y_col is None:
        raise SystemExit(f"required columns missing. columns={list(df.columns)}")

    subjects = df[subj_col].to_numpy()
    _stim_pred, residual = loso_stimulus_prior_residual(df, y_col, stim_col)
    threshold, threshold_src = get_high_threshold(args.target, residual)
    high_mask = np.abs(residual) >= threshold

    locked_rmse, locked_src = get_locked_bridge_rmse(args.target)
    fixed_pred, fixed_note = load_fixed_bandpower_pred(df, args.target, subj_col, stim_col)

    print(f"[INFO] target={args.target} rows={len(df)} high_n={int(high_mask.sum())} threshold={threshold:.6f} src={threshold_src}")
    print(f"[INFO] locked_bridge_rmse_05ak={locked_rmse} src={locked_src}")
    print(f"[INFO] fixed_bandpower={fixed_note}")

    methods: dict[str, np.ndarray] = {
        "kshot_subject_mean_only": np.zeros(len(df), dtype=float),
    }
    if fixed_pred is not None:
        methods["fixed_eeg_bandpower_plus_kshot_bias"] = fixed_pred

    metric_rows = []
    repeat_subject_frames = []
    for method, base_pred in methods.items():
        for k in [4, 8, 16]:
            print(f"[INFO] evaluating method={method} k={k} repeats={args.repeats}")
            row, rs = eval_kshot_method(
                residual=residual,
                base_pred=base_pred,
                high_mask=high_mask,
                subjects=subjects,
                k=k,
                repeats=args.repeats,
                rng=rng,
                locked_rmse=locked_rmse,
                fixed_pred=fixed_pred,
            )
            if row:
                row = {"target": args.target, "method": method, **row}
                metric_rows.append(row)
                rs.insert(0, "method", method)
                rs.insert(0, "target", args.target)
                repeat_subject_frames.append(rs)

    metrics = pd.DataFrame(metric_rows)
    repeat_subject = pd.concat(repeat_subject_frames, ignore_index=True) if repeat_subject_frames else pd.DataFrame()

    if metrics.empty:
        decision = "NO_RESULT"
        best = {}
        interpretation = "No k-shot confirmation metrics were produced."
        action = "Inspect inputs."
    else:
        metrics["passes_zero_gate"] = (
            (metrics["lift_vs_zero"] > 0.02)
            & (metrics["ci95_low_repeat_subject_improvement"] > 0)
            & (metrics["win_margin_vs_zero_repeat_subject"] > 3)
        )
        metrics["passes_fixed_reference_gate"] = metrics["lift_vs_fixed_same_eval"] > 0.02
        metrics["passes_locked_bridge_gate"] = metrics["lift_vs_locked_bridge_rmse"] > 0.02
        metrics = metrics.sort_values(
            by=["passes_locked_bridge_gate", "passes_fixed_reference_gate", "passes_zero_gate", "lift_vs_locked_bridge_rmse", "lift_vs_fixed_same_eval", "lift_vs_zero"],
            ascending=[False, False, False, False, False, False],
            na_position="last",
        ).reset_index(drop=True)

        best = metrics.iloc[0].to_dict()

        subject_mean_k16 = metrics[
            (metrics["method"] == "kshot_subject_mean_only")
            & (metrics["k_calibration"] == 16)
        ]
        fixed_plus_k16 = metrics[
            (metrics["method"] == "fixed_eeg_bandpower_plus_kshot_bias")
            & (metrics["k_calibration"] == 16)
        ]

        physio_increment = float("nan")
        if not subject_mean_k16.empty and not fixed_plus_k16.empty:
            physio_increment = float(subject_mean_k16.iloc[0]["candidate_rmse"] - fixed_plus_k16.iloc[0]["candidate_rmse"])

        if bool(best.get("passes_locked_bridge_gate", False)):
            decision = "GO_KSHOT_ADAPTATION_BEATS_LOCKED_B2_BRIDGE"
            interpretation = "The best k-shot calibration candidate beats the locked B2 high-disagreement bridge by the practical margin."
            action = "Run a final confirmatory locked bridge with predictions and prepare this as the calibration-first result."
        elif bool(best.get("passes_fixed_reference_gate", False)) and bool(best.get("passes_zero_gate", False)):
            decision = "PARTIAL_GO_CALIBRATION_BEATS_FIXED_BUT_NOT_LOCKED_B2"
            interpretation = "K-shot calibration strongly beats zero/fixed physiology, but it does not beat the locked B2 personalization bridge. This means the apparent 06a4 gain is mostly the same calibration effect that B2 already captures."
            action = "Do not claim a new physiology/deep gain. Either test augmentation under locked gates or write the calibration-dominant conclusion."
        else:
            decision = "NO_GO_KSHOT_ADAPTATION_CONFIRMATION"
            interpretation = "K-shot calibration did not pass the practical comparison gates."
            action = "Stop this route and move to target reformulation or augmentation-only sanity check."

        if np.isfinite(physio_increment) and physio_increment < 0:
            interpretation += " Fixed EEG-bandpower plus k-shot improved over subject-mean-only in this run."
        elif np.isfinite(physio_increment) and physio_increment >= 0:
            interpretation += " Adding fixed EEG-bandpower after k-shot does not improve over subject-mean-only."

    decision_df = pd.DataFrame([{
        "target": args.target,
        "decision": decision,
        "high_threshold": threshold,
        "high_threshold_source": threshold_src,
        "locked_bridge_rmse_05ak": locked_rmse,
        "locked_bridge_source": locked_src,
        "fixed_prediction_note": fixed_note,
        "best_method": best.get("method"),
        "best_k_calibration": best.get("k_calibration"),
        "best_candidate_rmse": best.get("candidate_rmse"),
        "best_lift_vs_zero": best.get("lift_vs_zero"),
        "best_lift_vs_fixed_same_eval": best.get("lift_vs_fixed_same_eval"),
        "best_lift_vs_locked_bridge_rmse": best.get("lift_vs_locked_bridge_rmse"),
        "best_passes_zero_gate": best.get("passes_zero_gate"),
        "best_passes_fixed_reference_gate": best.get("passes_fixed_reference_gate"),
        "best_passes_locked_bridge_gate": best.get("passes_locked_bridge_gate"),
        "interpretation": interpretation,
        "recommended_next_action": action,
    }])

    next_steps = pd.DataFrame([
        {
            "priority": 1,
            "step": "06a5",
            "title": "Augmentation rerun under current residual locked gates",
            "purpose": "Only rerun prior augmentation if it can be compared to zero, fixed EEG-bandpower, and locked B2 under the current arousal high-disagreement residual protocol.",
            "success_condition": "Augmentation beats fixed EEG-bandpower and locked B2 by practical paired gates.",
        },
        {
            "priority": 2,
            "step": "06a6",
            "title": "Neural pipeline anchor against fixed EEG-bandpower",
            "purpose": "Before any larger deep model, force the neural route to reproduce the simple fixed EEG-bandpower signal.",
            "success_condition": "Neural or hybrid model matches/exceeds fixed EEG-bandpower under pure LOSO without k-shot labels.",
        },
        {
            "priority": 3,
            "step": "paper_note",
            "title": "Calibration-dominant negative-result framing",
            "purpose": "If neither augmentation nor neural anchor helps, finalize the finding that physiology residual decoding is mostly subject calibration under LOSO.",
            "success_condition": "A defensible paper section explaining why generic deep LOSO failed and why personalization/calibration is necessary.",
        },
    ])

    ROCA.mkdir(parents=True, exist_ok=True)
    decision_df.to_csv(ROCA / f"{OUT_PREFIX}_decision_table.csv", index=False)
    metrics.to_csv(ROCA / f"{OUT_PREFIX}_method_metrics.csv", index=False)
    repeat_subject.to_csv(ROCA / f"{OUT_PREFIX}_repeat_subject_stats.csv", index=False)
    next_steps.to_csv(ROCA / f"{OUT_PREFIX}_next_steps.csv", index=False)

    payload = {
        "title": "I-DARE k-shot calibration versus locked B2 bridge confirmation",
        "inputs": {
            "index": str(args.index),
            "target": args.target,
            "seed": args.seed,
            "repeats": args.repeats,
            "subject_column": subj_col,
            "stimulus_column": stim_col,
            "score_column": y_col,
        },
        "decision_table": decision_df.to_dict(orient="records"),
        "method_metrics": metrics.to_dict(orient="records"),
        "next_steps": next_steps.to_dict(orient="records"),
    }
    with open(ROCA / f"{OUT_PREFIX}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)

    report = []
    report.append("# I-DARE k-shot calibration versus locked B2 bridge confirmation\n")
    report.append("This step checks the important caveat from 06a4: k-shot subject calibration can look strong against zero/fixed physiology, but the real question is whether it adds anything beyond the locked B2 personalization bridge.\n")
    report.append("\n## Decision table\n")
    report.append(md_table(decision_df))
    report.append("\n## Method metrics\n")
    cols = [
        "method", "k_calibration", "n_eval_repeated", "zero_rmse", "candidate_rmse",
        "lift_vs_zero", "fixed_rmse_same_eval", "lift_vs_fixed_same_eval",
        "locked_bridge_rmse_05ak", "lift_vs_locked_bridge_rmse",
        "pearson", "sign_acc", "passes_zero_gate", "passes_fixed_reference_gate",
        "passes_locked_bridge_gate",
    ]
    report.append(md_table(metrics[[c for c in cols if c in metrics.columns]] if not metrics.empty else metrics))
    report.append("\n## Next steps\n")
    report.append(md_table(next_steps))
    report.append("\n## Interpretation guardrail\n")
    report.append("- `kshot_subject_mean_only` is not a physiology model and not zero-shot LOSO. It tests how much labelled subject calibration alone can explain the high-disagreement residuals.\n")
    report.append("- A positive result versus zero/fixed physiology is useful, but it only becomes a new contribution if it also beats the locked B2 personalization bridge.\n")
    report.append("- If fixed EEG-bandpower plus k-shot is worse than subject-mean-only, physiology is not adding useful information after calibration.\n")
    (ROCA / f"{OUT_PREFIX}.md").write_text("\n".join(report), encoding="utf-8")

    print("ROCA step 06a4b completed.")
    for suffix in [".md", ".json", "_decision_table.csv", "_method_metrics.csv", "_repeat_subject_stats.csv", "_next_steps.csv"]:
        print(f"wrote: {ROCA / (OUT_PREFIX + suffix)}")

    print("\nDecision table:")
    print(decision_df.to_string(index=False))
    print("\nMethod metrics:")
    print(metrics[[c for c in cols if c in metrics.columns]].to_string(index=False))
    print("\nNext steps:")
    print(next_steps.to_string(index=False))

    print("\n================== KEY OUTPUTS ==================")
    print(decision_df.to_csv(index=False).strip())
    print()
    print(metrics[[c for c in cols if c in metrics.columns]].to_csv(index=False).strip())
    print()
    print(next_steps.to_csv(index=False).strip())

    print("\n================== SIZE CHECK ==================")
    for p in sorted(ROCA.glob(f"{OUT_PREFIX}*")):
        print(f"{p.stat().st_size/1024:.1f}K\t{p}")

    print("\n================== GIT STATUS ==================")
    print(git_short())

    print("[INFO] If inspection is OK:")
    print(f"git add scripts/roca/06a4b_idare_kshot_calibration_locked_bridge_confirm.py docs/roca/{OUT_PREFIX}*")
    print('git commit -m "Add I-DARE k-shot calibration locked bridge confirmation"')
    print("git push")


if __name__ == "__main__":
    main()
