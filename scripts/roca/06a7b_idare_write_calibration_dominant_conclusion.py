#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

import pandas as pd

ROOT = Path('.')
OUT = ROOT / 'docs/roca/idare_06a7b_calibration_dominant_conclusion_current'

SOURCES = {
    '06a3': ROOT / 'docs/roca/idare_06a3_residual_identifiability_noise_bound_current_decision_table.csv',
    '06a4': ROOT / 'docs/roca/idare_06a4_subject_normalization_domain_adaptation_current_decision_table.csv',
    '06a4b': ROOT / 'docs/roca/idare_06a4b_kshot_calibration_locked_bridge_confirm_current_decision_table.csv',
    '06a5': ROOT / 'docs/roca/idare_06a5_augmentation_locked_gate_probe_current_decision_table.csv',
    '06a5b': ROOT / 'docs/roca/idare_06a5b_gaussian10_locked_gate_rerun_current_decision_table.csv',
    '06a6': ROOT / 'docs/roca/idare_06a6_neural_anchor_fixed_bandpower_current_decision_table.csv',
    '06a7': ROOT / 'docs/roca/idare_06a7_final_loso_root_cause_report_current_decision_table.csv',
}


def read_one(step: str, path: Path) -> dict:
    row = {'step': step, 'path': str(path), 'exists': path.exists()}
    if not path.exists():
        row['decision'] = 'MISSING'
        return row
    try:
        df = pd.read_csv(path)
        row['n_rows'] = int(len(df))
        if len(df):
            first = df.iloc[0].to_dict()
            for key in [
                'target', 'decision', 'final_decision', 'primary_root_cause',
                'best_method', 'best_model_rmse_high', 'best_lift_vs_zero_high',
                'best_lift_vs_fixed_same_eval_high', 'best_lift_vs_locked_bridge_rmse',
                'gaussian_delta_rmse_vs_noaug', 'passes_zero_gate',
                'passes_fixed_reference_gate', 'passes_locked_bridge_gate',
                'paper_claim', 'recommended_next_action'
            ]:
                if key in first:
                    row[key] = first[key]
    except Exception as exc:
        row['decision'] = 'READ_ERROR'
        row['error'] = str(exc)
    return row


def safe_float(x):
    try:
        if pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def md_table(df: pd.DataFrame) -> str:
    if df.empty:
        return '_No rows._'
    cols = list(df.columns)
    lines = ['| ' + ' | '.join(cols) + ' |', '| ' + ' | '.join(['---'] * len(cols)) + ' |']
    for _, r in df.iterrows():
        vals = []
        for c in cols:
            x = r[c]
            if pd.isna(x):
                vals.append('')
            elif isinstance(x, float):
                vals.append(f'{x:.6g}')
            else:
                txt = str(x).replace('\n', ' ').replace('|', '\\|')
                vals.append(txt[:240] + '...' if len(txt) > 243 else txt)
        lines.append('| ' + ' | '.join(vals) + ' |')
    return '\n'.join(lines)


def main() -> None:
    rows = [read_one(step, path) for step, path in SOURCES.items()]
    rollup = pd.DataFrame(rows)

    # Compact conclusion table for the manuscript / decision log.
    conclusion = {
        'result_type': 'calibration_dominant_negative_result',
        'scope': 'arousal high-disagreement residual under strict LOSO',
        'main_root_cause': 'subject calibration/domain shift plus weak transferable residual identifiability',
        'not_primary_fixes': 'generic gaussian augmentation; raw EEG neural capacity search; unanchored larger CNN search',
        'what_worked_partially': 'k-shot/subject calibration improved residuals but did not beat locked B2 personalization bridge',
        'best_stable_nonpersonalized_reference': 'fixed EEG bandpower is weak but more stable than raw neural anchor',
        'final_action': 'stop blind global residual decoding search; write result or redesign task as explicitly personalized/calibrated',
    }

    current = {r['step']: r for r in rows}
    for step, key in [('06a5b', 'gaussian10_locked_gate_decision'), ('06a6', 'neural_anchor_decision'), ('06a7', 'final_roca_decision')]:
        r = current.get(step, {})
        conclusion[key] = r.get('decision') or r.get('final_decision') or ''

    conclusion_df = pd.DataFrame([conclusion])

    payload = {
        'generated_at': datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'conclusion': conclusion,
        'sources': rows,
    }

    (OUT.with_suffix('.json')).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    rollup.to_csv(str(OUT) + '_evidence_rollup.csv', index=False)
    conclusion_df.to_csv(str(OUT) + '_conclusion_table.csv', index=False)

    lines = []
    lines.append('# I-DARE LOSO root-cause conclusion: calibration-dominant negative result')
    lines.append('')
    lines.append('## One-sentence conclusion')
    lines.append('Under strict LOSO, the current arousal high-disagreement residual target is dominated by subject calibration/domain shift, and global raw-EEG residual decoding is not supported by the locked gates.')
    lines.append('')
    lines.append('## Decision')
    lines.append(md_table(conclusion_df))
    lines.append('')
    lines.append('## Evidence rollup')
    keep_cols = [c for c in ['step','target','decision','final_decision','best_method','best_model_rmse_high','best_lift_vs_zero_high','best_lift_vs_fixed_same_eval_high','best_lift_vs_locked_bridge_rmse','passes_zero_gate','passes_fixed_reference_gate','passes_locked_bridge_gate'] if c in rollup.columns]
    lines.append(md_table(rollup[keep_cols]))
    lines.append('')
    lines.append('## Plain-language interpretation')
    lines.append('- Old Gaussian augmentation looked promising in older/oracle-style reports, but the locked rerun did not fix LOSO.')
    lines.append('- The raw neural pipeline did not even anchor to the weak fixed-bandpower reference under the high-disagreement locked gate.')
    lines.append('- K-shot calibration helps because it captures subject bias/style, but it is not a new global physiology model and it did not beat the locked B2 bridge.')
    lines.append('- The correct next research move is not another bigger CNN. It is either a paper/report conclusion, or a new task definition that explicitly allows calibration/personalization.')
    lines.append('')
    lines.append('## Recommended next step')
    lines.append('Write the calibration-dominant result into the manuscript/decision log. Only start 06a8 if the project explicitly accepts a personalized/calibrated protocol with a stated calibration budget.')

    (OUT.with_suffix('.md')).write_text('\n'.join(lines) + '\n', encoding='utf-8')

    print('ROCA step 06a7b completed.')
    print('wrote:', OUT.with_suffix('.md'))
    print('wrote:', OUT.with_suffix('.json'))
    print('wrote:', str(OUT) + '_evidence_rollup.csv')
    print('wrote:', str(OUT) + '_conclusion_table.csv')
    print('\nConclusion:')
    print(conclusion_df.to_string(index=False))
    print('\nIf OK:')
    print('git add scripts/roca/06a7b_idare_write_calibration_dominant_conclusion.py docs/roca/idare_06a7b_calibration_dominant_conclusion_current*')
    print('git commit -m "Add I-DARE calibration-dominant conclusion"')
    print('git push')


if __name__ == '__main__':
    main()
