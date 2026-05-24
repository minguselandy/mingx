# Goal ID: POST-4-RUN / Sufficiency and abstention pilot

## Objective

Run a small live-API sufficiency / abstention pilot using the frozen POST-4 configuration. This goal is only allowed after owner approval.

## Required owner approval gate

Before doing any live API call, verify that the user has explicitly written:

`APPROVE_LIVE_API_POST_4_SUFFICIENCY_ABSTENTION=true`

If absent, stop and report blocked.

## Scale

- 50 examples maximum for first pilot.
- Prefer HotpotQA packets first.
- FEVER-style packets only if already configured and low-risk.

## Hard constraints

- Use only DashScope-compatible live API.
- Do not use vLLM or local scorer.
- Do not compute teacher-forced NLL.
- Do not store raw API responses.
- Do not claim measurement validation.
- Do not unlock Route 5 or Route 8.

## Outputs

- `artifacts/experiments/post_lapi_sufficiency_abstention/`
- `docs/experiments/POST-LAPI-sufficiency-abstention-pilot.md`
- `docs/paper/post-lapi-sufficiency-abstention-table.md`

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

## Done condition

- Live API call count is reported.
- `raw_response_stored=false` is confirmed.
- Regime ledger is produced.
- Cost and latency summary is produced.
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
