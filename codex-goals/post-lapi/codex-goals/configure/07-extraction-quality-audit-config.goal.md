# Goal ID: POST-7-CONFIG / Extraction quality audit configuration

## Objective

Configure the extraction quality audit over the M* -> M bottleneck. This goal prepares strata, labels, schema, config, and table templates without model judging or live API calls.

## Hard constraints

- Configuration only.
- No live API calls.
- No model-adjudicated extraction run.
- No human-validation claim.
- No measurement-validation claim.
- No Route 5 or Route 8 unlock.
- No raw API responses.
- No claim upgrade.

## Read first

- `configs/post-lapi/extraction_quality_audit_config.yaml` if installed
- LAPI-7 extraction quality audit framework
- `docs/paper/live-api-experiment-boundaries.md`
- `docs/paper/v12-evidence-ledger.md`

## Create or update

- `configs/post_lapi/extraction_quality_audit_config.yaml`
- `docs/experiments/POST-LAPI-extraction-quality-audit-config.md`
- `docs/paper/post-lapi-extraction-quality-table-template.md`
- `schemas/post_lapi_extraction_quality.schema.json` if schema conventions exist
- `tests/test_post_lapi_extraction_quality_config.py`

## Required strata

- simple_factual
- complex_conditional
- qualifier_heavy
- temporal_scope
- cross_chunk
- long_tail_entity
- high_provenance_value
- prerequisite
- contradictory
- adversarial

## Required labels

- captured
- captured_core_preserved
- captured_core_materially_changed
- missing
- lost_qualifier
- temporal_scope_error
- provenance_loss
- selector_impact

## Metrics

- completeness_by_stratum
- value_weighted_loss_proxy
- qualifier_loss_rate
- temporal_scope_error_rate
- provenance_loss_rate
- selector_impact_rate

## Claim rules

Allowed:
- model_adjudicated_extraction_risk_evidence
- operational_extraction_audit

Denied:
- human-validated extraction measurement
- measurement validation
- theorem transfer to M*
- end-to-end validation

## Checks

```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py tests/test_post_lapi_extraction_quality_config.py -q
python -m compileall cps tests scripts
```

## Done condition

- Config and schema are present.
- Table template is written.
- Tests pass without API calls.
- No claim upgrade is introduced.
- Do not commit automatically unless explicitly instructed after review.


Report format:
- Goal ID:
- Branch:
- HEAD:
- Changed files:
- Staged files:
- Checks run:
- Check results:
- Live API calls run: yes/no
- Raw API responses stored: yes/no
- Claim level:
- Claim upgrade introduced: yes/no
- Route 5 locked: yes/no
- Route 8 locked: yes/no
- Unrelated leftovers staged: yes/no
- Next recommended goal:
