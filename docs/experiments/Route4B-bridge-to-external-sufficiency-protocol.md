# Route 4B Bridge to External Sufficiency Protocol

Status: model-adjudicated pilot protocol
Claim status: `no_claim_upgrade`

Route 4B joins fixed Route 4A answer-NLL deltas to Route 6A external sufficiency labels.
The external utility is derived only from normalized Route 6A label enums, not from logloss, gold support labels, or Route 4 utility scores.

## Gates

- Minimum rows: `500`
- Minimum unique original instances: `150`
- Minimum effective sample size: `100`
- Sign agreement: `>= 0.7`
- Spearman rho: `>= 0.4`
- Normalized residual: `<= 0.5`

Model-adjudicated labels do not count as human labels and do not permit measurement validation or human-human kappa claims.
Any underpowered or failed gate result remains `no_claim_upgrade`.
