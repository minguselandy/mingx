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
| synthetic-only evidence | `synthetic_structural_only` / `ambiguous_metric` |
| fixture-only evidence | no `vinfo_proxy_supported` or `calibrated_proxy_supported` |
| replay completeness only | replay / observability evidence |
| model-adjudicated labels | `model_adjudicated_pilot_only` or `operational_utility_only` |
| live API success alone | operational evidence only |

## Explicitly Denied Claims

- `measurement_validated` without human labels, human-human kappa,
  contamination closure, and a fresh matching metric bridge.
- deployed V-information verification.
- synthetic evidence as bridge evidence.
- fixture evidence as paper-grade evidence.
- replay usability as metric support.
- extraction audit as selector validity.
- `ReprojectionWitness` as deployed runtime improvement.

## Boundary Rules

- Fixture-only evidence cannot produce `vinfo_proxy_supported` or
  `calibrated_proxy_supported`.
- Replay usability is not metric support.
- Extraction audit is not selector validity.
- `ReprojectionWitness` is an audit artifact, not deployed runtime
  improvement.
- Model-adjudicated fixture labels are not human labels or human-human kappa.

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
