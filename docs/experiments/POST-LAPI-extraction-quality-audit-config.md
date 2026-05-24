# POST-LAPI Extraction Quality Audit Config

Status: configuration only
Goal ID: POST-7-CONFIG
Claim level: `operational_utility_only/no_claim_upgrade`

## Scope

This config prepares an extraction quality audit over the M* -> M bottleneck.
It defines strata, labels, schema, metrics, manifest requirements, and table
templates for a later owner-approved audit. It does not run model judging, does
not run live API calls, does not collect human labels, and does not store raw
API responses.

## Source References

- `configs/post-lapi/extraction_quality_audit_config.yaml`
- `docs/experiments/extraction-quality-audit-protocol.md`
- `docs/paper/live-api-experiment-boundaries.md`
- `docs/paper/v12-evidence-ledger.md`

## Strata

- `simple_factual`
- `complex_conditional`
- `qualifier_heavy`
- `temporal_scope`
- `cross_chunk`
- `long_tail_entity`
- `high_provenance_value`
- `prerequisite`
- `contradictory`
- `adversarial`

## Labels

- `captured`
- `captured_core_preserved`
- `captured_core_materially_changed`
- `missing`
- `lost_qualifier`
- `temporal_scope_error`
- `provenance_loss`
- `selector_impact`

`selector_impact` is configured as a candidate-pool risk signal only. It is not
selector validity, selector superiority, or global selector superiority.

## Metrics

- `completeness_by_stratum`
- `value_weighted_loss_proxy`
- `qualifier_loss_rate`
- `temporal_scope_error_rate`
- `provenance_loss_rate`
- `selector_impact_rate`

The value-weighted loss metric is an operational extraction-risk proxy only.
It does not transfer theorem claims from M to M*.

## Claim Boundary

Allowed claims:

- `model_adjudicated_extraction_risk_evidence`
- `operational_extraction_audit`

Denied claims:

- human-validated extraction measurement
- measurement validation
- theorem transfer to M*
- end-to-end validation
- metric bridge support
- calibrated proxy support
- V-information proxy support
- paper evidence
- selector superiority
- global selector superiority
- Route 5 unlock
- Route 8 unlock

## Execution Record

- Live API calls run during this config goal: no
- Model-adjudicated extraction run during this config goal: no
- Human validation claim introduced: no
- Measurement validation claim introduced: no
- Raw API responses stored: no
- Claim upgrade introduced: no
- Route 5 locked: yes
- Route 8 locked: yes
