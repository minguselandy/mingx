# POST-LAPI Reprojection Witness Configuration

Goal ID: POST-5-CONFIG / Reprojection witness configuration
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This document records the configuration-only package for the reprojection
witness pilot. It prepares the controlled replay schema, offline manifest
binding, eligible-case rules, required controls, metrics, and paper table
template. It does not run live API calls, execute controlled replay calls, store
raw API responses, unlock Route 5, unlock Route 8, or upgrade claims.

## Configured Inputs

- Config: `configs/post_lapi/reprojection_witness_config.yaml`
- Schema: `schemas/post_lapi_reprojection_witness.schema.json`
- POST-4 dependency: `configs/post_lapi/sufficiency_abstention_config.yaml`
- Offline manifest builder: `cps.replay.reprojection_witness.build_reprojection_manifest`
- Paper table template: `docs/paper/post-lapi-reprojection-witness-table-template.md`

## Eligible Cases

Configured eligible cases:
- `sufficient_dropped`
- `insufficient_and_answered`
- high `missing_evidence_type` confidence
- replay artifact complete

The config limits the first pilot to at most 30 flagged cases and requires
explicit approval before any later controlled replay run.

## Required Controlled Fields

Each later witness row must carry:
- `downstream_prompt_hash`
- `model_snapshot`
- `endpoint`
- `thinking_mode`
- `decoding_policy`
- `token_budget_accounting`
- `selected_evidence_before_hash`
- `restored_evidence_hash`
- `context_diff_hash`
- `before_output_hash`
- `after_output_hash`
- `judge_prompt_hash`
- `claim_ledger_entry`

The config maps these POST-LAPI names onto the existing offline
`ReprojectionWitness` scaffold without changing the claim ceiling.

## Metrics

Configured metrics:
- `repair_rate`
- `label_change_rate`
- `abstain_to_support_rate`
- `unsupported_to_supported_rate`
- `cost_delta`
- `latency_delta`
- `position_sensitivity_rate`

These metrics remain operational witness diagnostics. They are not validated
repair, truth correction guarantees, metric bridge support, selector
superiority, or paper-grade evidence.

## Claim Boundary

Allowed:
- `operational_reprojection_witness`
- `omitted_evidence_operational_diagnostic`
- `replayable_artifact_evidence`

Denied:
- validated repair
- truth correction guarantee
- metric bridge support
- selector superiority

Boundary flags:
- Live API calls run during this config goal: no
- Controlled replay calls run during this config goal: no
- Raw API responses stored: no
- Route 5 locked: yes
- Route 8 locked: yes
- Claim upgrade introduced: no

## Dry-Run Validation

The focused test `tests/test_post_lapi_reprojection_witness_config.py` validates
the config and schema, confirms the POST-4 dependency exists, builds an offline
manifest over static fixture items, and normalizes fixture witness records
without live API calls or controlled replay calls. The dry run is metadata-only
and writes no raw provider bodies.

Run:

```powershell
uv run pytest tests/test_post_lapi_reprojection_witness_config.py -q
```
