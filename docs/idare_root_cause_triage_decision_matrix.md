# I-DARE Root-Cause Triage Decision Matrix

Status: `completed`

Primary recommendation: `A+B first; treat D as mechanism; defer C; keep E as fallback`

| Code | Direction | Classification | Confidence | Recommended Next Control Decision |
|---|---|---|---|---|
| A | label/task redesign as primary | PRIMARY_RECOMMENDED | high | authorize label/task redesign design only, not training |
| B | evaluation/protocol reconciliation as primary | PRIMARY_RECOMMENDED | high | authorize protocol reconciliation documentation only |
| C | representation redesign v2 as primary | NOT_PRIMARY_NOW | medium | defer representation redesign v2 until label/protocol reconciliation |
| D | subject/domain-generalization as primary | MECHANISM_PRIMARY_BUT_EXECUTION_DEFERRED | medium_high | do not authorize DG execution yet |
| E | stop/pivot away from current I-DARE cross-subject formulation | CONTINGENT_FALLBACK | medium | keep stop/pivot available if A/B reconciliation fails |

## Boundary

- No new operating point is claimed.
- No forbidden scope was touched.
