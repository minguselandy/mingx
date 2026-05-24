# Goal ID: POST-5-CONFIG / Reprojection witness configuration

## Objective

Configure the reprojection witness pilot without running live API calls. This goal prepares controlled replay schemas, manifests, and table templates.

## Hard constraints

- Configuration only.
- No live API calls.
- No controlled replay calls.
- No raw API responses.
- No Route 5 or Route 8 unlock.
- No validated-repair language.
- No claim upgrade.

## Read first

- `configs/post-lapi/reprojection_witness_config.yaml` if installed
- LAPI-5 reprojection framework
- POST-4 sufficiency/abstention config if present
- `docs/api/live-api-capability-contract.md`

## Create or update

- `configs/post_lapi/reprojection_witness_config.yaml`
- `docs/experiments/POST-LAPI-reprojection-witness-config.md`
- `docs/paper/post-lapi-reprojection-witness-table-template.md`
- `schemas/post_lapi_reprojection_witness.schema.json` if schema conventions exist
- `tests/test_post_lapi_reprojection_witness_config.py`

## Eligible cases

- sufficient_dropped
- insufficient_and_answered
- high missing_evidence_type confidence
- replay artifact complete

## Required controlled fields

- downstream_prompt_hash
- model_snapshot
- endpoint
- thinking_mode
- decoding_policy
- token_budget_accounting
- selected_evidence_before_hash
- restored_evidence_hash
- context_diff_hash
- before_output_hash
- after_output_hash
- judge_prompt_hash
- claim_ledger_entry

## Metrics

- repair_rate
- label_change_rate
- abstain_to_support_rate
- unsupported_to_supported_rate
- cost_delta
- latency_delta
- position_sensitivity_rate

## Claim rules

Allowed:
- operational_reprojection_witness
- omitted_evidence_operational_diagnostic
- replayable_artifact_evidence

Denied:
- validated repair
- truth correction guarantee
- metric bridge support
- selector superiority

## Checks

```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py tests/test_post_lapi_reprojection_witness_config.py -q
python -m compileall cps tests scripts
```

## Done condition

- Config and schema are present.
- Dry-run validation passes without API calls.
- Paper table template is written.
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
