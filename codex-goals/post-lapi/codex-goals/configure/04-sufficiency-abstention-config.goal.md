# Goal ID: POST-4-CONFIG / Sufficiency and abstention configuration

## Objective

Configure the sufficiency / abstention pilot without running live API calls. Prepare schemas, prompt templates, config, dry-run input selection, and paper table templates.

## Hard constraints

- Configuration only.
- No live API calls.
- No new model judging.
- No Route 5 or Route 8 unlock.
- No raw API responses.
- No measurement-validation language.
- No claim upgrade.

## Read first

- `configs/post-lapi/sufficiency_abstention_config.yaml` if installed
- LAPI-5 sufficiency / abstention / reprojection framework
- `docs/api/live-api-capability-contract.md`
- `docs/paper/live-api-experiment-boundaries.md`

## Create or update

- `configs/post_lapi/sufficiency_abstention_config.yaml`
- `docs/experiments/POST-LAPI-sufficiency-abstention-config.md`
- `docs/paper/post-lapi-sufficiency-abstention-table-template.md`
- `schemas/post_lapi_sufficiency_abstention.schema.json` if schema conventions exist
- `tests/test_post_lapi_sufficiency_abstention_config.py`

## Required labels

- support
- insufficient
- contradict
- uncertain
- parse_failed

## Required additional fields

- abstain_recommended
- missing_evidence_type
- confidence_bucket
- prompt_hash
- model_snapshot
- endpoint
- raw_response_stored=false

## Required regime ledger

- sufficient_kept
- sufficient_dropped
- insufficient_and_answered
- insufficient_and_abstained

## Required metrics

- support_rate
- insufficient_rate
- contradict_rate
- uncertain_rate
- parse_failed_rate
- abstain_rate
- abstain_when_insufficient_rate
- unsafe_answer_rate
- missing_evidence_type_distribution
- cost_per_case
- latency_per_case

## Claim rules

Allowed:
- sufficiency_abstention_diagnostic
- model_adjudicated_weak_evidence
- operational_utility_only

Denied:
- truth validation
- human-calibrated abstention
- measurement validation
- paper-grade evidence

## Checks

```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py tests/test_post_lapi_sufficiency_abstention_config.py -q
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
