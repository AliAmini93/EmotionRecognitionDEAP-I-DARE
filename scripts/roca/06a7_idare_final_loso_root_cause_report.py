#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path('.')
OUT = ROOT / 'docs/roca/idare_06a7_final_loso_root_cause_report_current'

SOURCES = [
    ('06a1z_prior_map', 'docs/roca/idare_06a1z_prior_experiment_map_and_root_cause_autopsy_current_root_cause_table.csv'),
    ('06a3_identifiability', 'docs/roca/idare_06a3_residual_identifiability_noise_bound_current_decision_table.csv'),
    ('06a4_subject_adaptation', 'docs/roca/idare_06a4_subject_normalization_domain_adaptation_current_decision_table.csv'),
    ('06a4b_locked_bridge_confirm', 'docs/roca/idare_06a4b_kshot_calibration_locked_bridge_confirm_current_decision_table.csv'),
    ('06a5_prior_aug_probe', 'docs/roca/idare_06a5_augmentation_locked_gate_probe_current_decision_table.csv'),
    ('06a5b_gaussian10_locked_rerun', 'docs/roca/idare_06a5b_gaussian10_locked_gate_rerun_current_decision_table.csv'),
    ('06a6_neural_anchor', 'docs/roca/idare_06a6_neural_anchor_fixed_bandpower_current_decision_table.csv'),
]

METHOD_SOURCES = [
    ('06a5b_gaussian10_locked_rerun', 'docs/roca/idare_06a5b_gaussian10_locked_gate_rerun_current_method_metrics.csv'),
    ('06a6_neural_anchor', 'docs/roca/idare_06a6_neural_anchor_fixed_bandpower_current_method_metrics.csv'),
    ('06a4b_locked_bridge_confirm', 'docs/roca/idare_06a4b_kshot_calibration_locked_bridge_confirm_current_method_metrics.csv'),
]


def read_csv(path: str) -> pd.DataFrame:
    p = ROOT / path
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p)
    except Exception as exc:
        return pd.DataFrame([{'read_error': str(exc), 'path': path}])


def first_value(df: pd.DataFrame, col: str, default=None):
    if df.empty or col not in df.columns:
        return default
    vals = df[col].dropna().tolist()
    return vals[0] if vals else default


def add_evidence_rows() -> pd.DataFrame:
    rows = []
    for name, rel in SOURCES:
        df = read_csv(rel)
        if df.empty:
            rows.append({'source': name, 'path': rel, 'status': 'missing_or_empty'})
            continue
        row = {'source': name, 'path': rel, 'status': 'loaded', 'n_rows': len(df)}
        for col in [
            'target', 'decision', 'best_method', 'best_model_rmse_high',
            'best_lift_vs_zero_high', 'best_lift_vs_fixed_same_eval_high',
            'best_lift_vs_locked_bridge_rmse', 'gaussian_delta_rmse_vs_noaug',
            'gaussian_delta_rmse_vs_noaug_positive_means_help',
            'passes_zero_gate', 'passes_fixed_reference_gate', 'passes_locked_bridge_gate',
            'subject_mean_oracle_lift', 'k16_subject_mean_oracle_lift',
            'subject_style_reliability_mean_r', 'shared_stimulus_residual_reliability_mean_r',
            'high_disagreement_shared_residual_reliability_mean_r',
            'interpretation', 'recommended_next_action', 'root_cause_hypothesis', 'evidence',
        ]:
            if col in df.columns:
                row[col] = first_value(df, col)
        rows.append(row)
    return pd.DataFrame(rows)


def add_method_rows() -> pd.DataFrame:
    frames = []
    for name, rel in METHOD_SOURCES:
        df = read_csv(rel)
        if df.empty:
            continue
        df = df.copy()
        df.insert(0, 'source', name)
        df.insert(1, 'path', rel)
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True, sort=False)


def df_to_md(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return '_No rows._'
    d = df.copy()

    def fmt(x):
        if pd.isna(x):
            return ''
        if isinstance(x, float):
            return f'{x:.6g}'
        txt = str(x).replace('\n', ' ').replace('|', '\\|')
        return txt[:237] + '...' if len(txt) > 240 else txt

    cols = [str(c).replace('|', '\\|') for c in d.columns]
    lines = ['| ' + ' | '.join(cols) + ' |', '| ' + ' | '.join(['---'] * len(cols)) + ' |']
    for _, row in d.iterrows():
        lines.append('| ' + ' | '.join(fmt(row[c]) for c in d.columns) + ' |')
    return '\n'.join(lines)


def main() -> None:
    evidence = add_evidence_rows()
    methods = add_method_rows()

    final_decision = pd.DataFrame([
        {
            'target': 'arousal_high_disagreement_residual_LOSO',
            'final_decision': 'FINAL_CALIBRATION_DOMINANT_NEGATIVE_RESULT_FOR_GLOBAL_RAW_EEG_RESIDUAL_DECODING',
            'primary_root_cause': 'subject calibration/domain shift plus weak transferable residual identifiability',
            'ruled_out_as_primary_fix': 'generic Gaussian augmentation; raw EEG neural capacity search; unanchored larger CNNs',
            'what_did_help': 'explicit subject calibration/k-shot bias correction helps, but does not beat the locked B2 personalization bridge',
            'fixed_feature_status': 'fixed EEG-bandpower remains a weak but more stable reference than raw neural anchor under the locked high-disagreement gate',
            'paper_claim': 'Under strict LOSO, the current residual target is calibration-dominant. Global physiology decoding from raw EEG is not supported by the locked gates.',
            'recommended_next_action': 'Stop blind architecture/augmentation search. Write the result as a calibration-dominant finding, or start a new explicitly personalized/calibrated target formulation.',
        }
    ])

    next_steps = pd.DataFrame([
        {
            'priority': 1,
            'step': 'paper_note',
            'title': 'Write calibration-dominant negative-result section',
            'purpose': 'Turn the ROCA evidence into a defensible project conclusion instead of running more blind models.',
            'success_condition': 'The manuscript/report separates old oracle/overlap gains from locked LOSO residual evidence.',
        },
        {
            'priority': 2,
            'step': 'optional_06a8',
            'title': 'Only if needed: explicit personalized/calibrated formulation',
            'purpose': 'If the project needs a positive model, change the task to include allowed calibration context rather than pretending global LOSO residual decoding works.',
            'success_condition': 'Model is evaluated against locked B2 and reports calibration budget honestly.',
        },
        {
            'priority': 3,
            'step': 'archive',
            'title': 'Archive failed global residual routes',
            'purpose': 'Prevent repeated re-running of augmentation/deep searches that have already failed locked gates.',
            'success_condition': 'Decision log records gaussian_0p10 and neural anchor as no-go under current locked gate.',
        },
    ])

    payload = {
        'final_decision': final_decision.to_dict(orient='records'),
        'evidence_rollup': evidence.to_dict(orient='records'),
        'method_rollup': methods.to_dict(orient='records'),
        'next_steps': next_steps.to_dict(orient='records'),
    }

    final_decision.to_csv(str(OUT) + '_decision_table.csv', index=False)
    evidence.to_csv(str(OUT) + '_evidence_rollup.csv', index=False)
    methods.to_csv(str(OUT) + '_method_rollup.csv', index=False)
    next_steps.to_csv(str(OUT) + '_next_steps.csv', index=False)
    Path(str(OUT) + '.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')

    lines = []
    lines.append('# I-DARE Final LOSO Root-Cause Report')
    lines.append('')
    lines.append('## Final decision')
    lines.append(df_to_md(final_decision))
    lines.append('')
    lines.append('## Core interpretation')
    lines.append('The locked evidence now points to one main diagnosis: the weak LOSO result is not primarily caused by missing Gaussian augmentation or by an under-sized raw EEG CNN. The current high-disagreement residual target is dominated by subject calibration/domain shift and weak transferable residual identifiability.')
    lines.append('')
    lines.append('The old gaussian_0p10 result was useful as a clue, but the clean locked rerun did not reproduce it as a valid improvement under the current residual gate. The neural anchor also failed to reproduce even the fixed bandpower reference. So the safe conclusion is: stop blind deep/augmentation search and frame the result as calibration-dominant.')
    lines.append('')
    lines.append('## Evidence rollup')
    keep_cols = [c for c in ['source', 'decision', 'best_method', 'best_model_rmse_high', 'best_lift_vs_zero_high', 'best_lift_vs_fixed_same_eval_high', 'best_lift_vs_locked_bridge_rmse', 'passes_zero_gate', 'passes_fixed_reference_gate', 'passes_locked_bridge_gate', 'interpretation'] if c in evidence.columns]
    lines.append(df_to_md(evidence[keep_cols] if keep_cols else evidence))
    lines.append('')
    lines.append('## Method rollup')
    keep_m = [c for c in ['source', 'method', 'n_eval', 'n_high', 'zero_rmse_high', 'model_rmse_high', 'lift_vs_zero_high', 'fixed_rmse_same_eval_high', 'lift_vs_fixed_same_eval_high', 'locked_bridge_rmse_05ak', 'lift_vs_locked_bridge_rmse', 'pearson_high', 'sign_acc_high'] if c in methods.columns]
    lines.append(df_to_md(methods[keep_m] if keep_m else methods))
    lines.append('')
    lines.append('## Next steps')
    lines.append(df_to_md(next_steps))
    lines.append('')

    Path(str(OUT) + '.md').write_text('\n'.join(lines), encoding='utf-8')

    print('ROCA step 06a7 completed.')
    for suffix in ['.md', '.json', '_decision_table.csv', '_evidence_rollup.csv', '_method_rollup.csv', '_next_steps.csv']:
        print('wrote:', str(OUT) + suffix)
    print('\nDecision table:')
    print(final_decision.to_string(index=False))
    print('\nNext steps:')
    print(next_steps.to_string(index=False))


if __name__ == '__main__':
    main()
