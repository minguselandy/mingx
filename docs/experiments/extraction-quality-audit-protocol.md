# Extraction Quality Audit Protocol

Status: LAPI-7 framework only
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This protocol defines a model-adjudicated extraction quality audit framework for the `M* -> M` bottleneck. It records extraction-risk diagnostics only. It is not measurement validation, not metric bridge support, and not current evidence for calibrated proxy support, V-information proxy support, paper evidence, selector superiority, Route 5 unlock, or Route 8 unlock.

No live API call is run by this framework goal. Raw provider bodies are not stored.

## Allowed Claim

- `model_adjudicated_extraction_risk_evidence`

This claim is audit diagnostic only. Route 5 locked: true. Route 8 locked: true.

## Required Strata

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

## Required Labels

- `captured`
- `captured_core_preserved`
- `captured_core_materially_changed`
- `missing`
- `lost_qualifier`
- `temporal_scope_error`
- `provenance_loss`
- `selector_impact`

`selector_impact` is a candidate-pool risk signal only. It is not selector validity, selector superiority, or metric support.

## Controls

- Frozen prompts: true
- Prompt hashes required: true
- Duplicate judging: true
- Order swap: true
- Raw response stored: false
- Live API call performed: false

## Metrics

- `capture_rate_by_stratum`
- `core_preserved_rate`
- `material_change_rate`
- `missing_rate`
- `qualifier_loss_rate`
- `temporal_scope_error_rate`
- `provenance_loss_rate`
- `value_weighted_loss_candidate`

These metrics are extraction-risk diagnostics. They do not provide theorem transfer from `M` to `M*`.

## Human Sentinel Lane

Human sentinel audit is future optional. Enabled now: false. It is not current evidence.

A future human sentinel lane may become relevant only after separate approval and review. It must record actual human labels, annotator independence, valid agreement calculation, contamination handling, and whether outputs are sentinel-only or measurement-validation candidates. Model-adjudicated labels must not be substituted for missing human labels or missing kappa.

## Denied Claims

- `human_validated_extraction_measurement`
- `end_to_end_measurement_validation`
- `theorem_transfer_to_M_star`
- `measurement_validation`
- `metric_bridge_support`
- `calibrated_proxy_supported`
- `vinfo_proxy_supported`
- `paper_evidence`
- `selector_superiority`
- `global_selector_superiority`
- `route_5_unlock`
- `route_8_unlock`
