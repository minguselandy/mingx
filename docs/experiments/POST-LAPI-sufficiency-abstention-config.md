# POST-LAPI Sufficiency / Abstention Configuration

Goal ID: POST-4-CONFIG / Sufficiency and abstention configuration
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This document records the configuration-only package for the sufficiency /
abstention pilot. It prepares the schema, prompt-template binding, config,
dry-run input selection, regime ledger, metrics, and paper table template. It
does not run live API calls, run new model judging, store raw API responses,
unlock Route 5, unlock Route 8, or upgrade claims.

## Configured Inputs

- Config: `configs/post_lapi/sufficiency_abstention_config.yaml`
- Schema: `schemas/post_lapi_sufficiency_abstention.schema.json`
- Prompt template: `prompts/reprojection/sufficiency_abstention_v1.md`
- Paper table template: `docs/paper/post-lapi-sufficiency-abstention-table-template.md`
- Dry-run manifest builder: `cps.evaluation.sufficiency_regime.build_sufficiency_manifest`

## Labels

Allowed normalized labels:
- `support`
- `insufficient`
- `contradict`
- `uncertain`
- `parse_failed`

## Required Additional Fields

Every later pilot row must include:
- `abstain_recommended`
- `missing_evidence_type`
- `confidence_bucket`
- `prompt_hash`
- `model_snapshot`
- `endpoint`
- `raw_response_stored=false`

The config also keeps `live_api_call_performed=false`,
`measurement_validation_claim=false`, `truth_validation_claim=false`, and
`counts_as_human_or_external_gold=false` in the dry-run fixture records.

## Regime Ledger

| Regime | Meaning | Desired behavior |
| --- | --- | --- |
| `sufficient_kept` | Projected evidence was enough and the system answered. | Answer. |
| `sufficient_dropped` | Omitted evidence appears necessary in hindsight. | Flag as reprojection candidate. |
| `insufficient_and_answered` | Projected evidence was not enough but the system answered. | Unsafe answer diagnostic. |
| `insufficient_and_abstained` | Projected evidence was not enough and the system abstained or escalated. | Fail-closed abstention. |

## Metrics

Configured metrics:
- `support_rate`
- `insufficient_rate`
- `contradict_rate`
- `uncertain_rate`
- `parse_failed_rate`
- `abstain_rate`
- `abstain_when_insufficient_rate`
- `unsafe_answer_rate`
- `missing_evidence_type_distribution`
- `cost_per_case`
- `latency_per_case`

## Claim Boundary

Allowed:
- `sufficiency_abstention_diagnostic`
- `model_adjudicated_weak_evidence`
- `operational_utility_only`

Denied:
- truth validation
- human-calibrated abstention
- measurement validation
- paper-grade evidence

Boundary flags:
- Live API calls run during this config goal: no
- New model judging run during this config goal: no
- Raw API responses stored: no
- Route 5 locked: yes
- Route 8 locked: yes
- Claim upgrade introduced: no

## Dry-Run Validation

The focused test `tests/test_post_lapi_sufficiency_abstention_config.py`
validates the config and schema, confirms the prompt template exists, builds an
offline manifest over static fixture items, and classifies fixture records that
cover every required regime. The dry-run fixture records are static and local;
they do not call a live API, run a model judge, or store raw provider bodies.

Run:

```powershell
uv run pytest tests/test_post_lapi_sufficiency_abstention_config.py -q
```
