# Goal ID: POST-3-CONFIG / Judge weak-evidence stability configuration

## Objective

Configure the judge weak-evidence stability pilot without running live API calls. This goal prepares schemas, prompts, manifests, and dry-run validation only.

## Hard constraints

- Configuration only.
- No live API calls.
- No model judging.
- No silver-label scaling.
- No Route 5 or Route 8 unlock.
- No raw API responses.
- No claim upgrade.

## Read first

- `configs/post-lapi/judge_stability_pilot_config.yaml` if installed
- `docs/api/live-api-capability-contract.md`
- `docs/paper/live-api-experiment-boundaries.md`
- LAPI-4 judge weak-evidence harness docs and tests

## Create or update

- `configs/post_lapi/judge_stability_pilot_config.yaml`
- `docs/experiments/POST-LAPI-judge-stability-config.md`
- `docs/paper/post-lapi-judge-stability-table-template.md`
- `schemas/post_lapi_judge_stability.schema.json` if schema conventions exist
- `tests/test_post_lapi_judge_stability_config.py`

## Required conditions to configure

- original_order
- order_swapped
- duplicate_judging
- rubric_paraphrase

## Required labels

- support
- insufficient
- contradict
- uncertain
- parse_failed

## Required metrics

- parse_success_rate
- duplicate_agreement
- order_swap_agreement
- rubric_paraphrase_agreement
- confidence_bucket_stability
- position_bias_rate
- uncertain_rate
- parse_failed_rate
- cost_per_judgment
- latency_per_judgment

## Claim rules

Allowed:
- model_adjudicated_weak_evidence
- operational_diagnostic_evidence

Denied:
- human gold
- measurement validation
- judge validation
- paper-grade evidence
- selector superiority

## Checks

```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py tests/test_post_lapi_judge_stability_config.py -q
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
