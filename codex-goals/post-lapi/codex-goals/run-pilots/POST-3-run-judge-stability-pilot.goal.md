# Goal ID: POST-3-RUN / Judge weak-evidence stability pilot

## Objective

Run the small live-API judge stability pilot using the frozen POST-3 configuration. This goal is only allowed after POST-0 through POST-2 have passed and the project owner explicitly approves live API calls.

## Required owner approval gate

Before doing any live API call, verify that the user has explicitly written:

`APPROVE_LIVE_API_POST_3_JUDGE_STABILITY=true`

If that exact approval is absent, stop and report that the run is blocked.

## Scale

- 30 to 50 examples maximum.
- No silver-label scaling beyond this pilot.
- Store no raw API responses.

## Hard constraints

- Use only DashScope-compatible live API.
- Do not use vLLM.
- Do not use local HF / torch / transformers scorer.
- Do not use other APIs.
- Do not compute or claim teacher-forced NLL.
- Do not unlock Route 5 or Route 8.
- Do not store raw API responses.
- Do not claim validation.

## Conditions

- original_order
- order_swapped
- duplicate_judging
- rubric_paraphrase

## Outputs

- `artifacts/experiments/post_lapi_judge_stability/`
- `docs/experiments/POST-LAPI-judge-stability-pilot.md`
- `docs/paper/post-lapi-judge-stability-table.md`

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
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
python -m compileall cps tests scripts
```

## Done condition

- Live API call count is reported.
- Model snapshot / endpoint are reported.
- `raw_response_stored=false` is confirmed.
- Cost and latency summary is produced.
- Claim remains `model_adjudicated_weak_evidence` / `operational_utility_only`.
- No claim upgrade is introduced.


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
