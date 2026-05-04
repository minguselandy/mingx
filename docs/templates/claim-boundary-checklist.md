# Claim Boundary Checklist

Use this checklist for every experiment, review, and manuscript integration milestone.

## Evidence Inputs

- [ ] contamination status known
- [ ] human-label status known
- [ ] human-human kappa status known
- [ ] metric bridge status known
- [ ] artifact completeness known
- [ ] live API status known
- [ ] Route A / Route B route identified

## Downgrade Rules

| Condition | Required claim boundary |
|---|---|
| contamination failure | `pilot_only` |
| missing human labels | not `measurement_validated` |
| missing human-human kappa | not `measurement_validated` |
| stale metric bridge | `operational_utility_only` or `ambiguous` |
| missing metric bridge | `operational_utility_only` or `ambiguous` |
| synthetic-only evidence | `structural_synthetic_only` |
| replay completeness only | replay / observability evidence |
| model-adjudicated labels | `model_adjudicated_pilot_only` or `operational_utility_only` |
| live API success alone | operational evidence only |

## Required Report Fields

```text
metric_claim_level
selector_regime_label
selector_action
contamination_status
human_labels_present
kappa_present
metric_bridge_status
artifact_completeness_status
route
max_allowed_claim
```

## Route Boundary

Route A:

- requires human labels;
- requires human-human kappa;
- requires contamination pass;
- requires fresh metric bridge;
- requires complete artifacts;
- may eventually support `measurement_validated_candidate` only if claim gate allows.

Route B:

- uses model prelabels, model/Codex audit, and model adjudication;
- does not require human labels;
- does not establish human-human kappa;
- cannot claim `measurement_validated`;
- maximum claim is `model_adjudicated_pilot_only` or `operational_utility_only`.
