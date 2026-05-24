# Goal ID: POST-5-RUN / Reprojection witness pilot

## Objective

Run a controlled reprojection witness pilot on flagged sufficiency / omitted-evidence failures from POST-4.

## Required owner approval gate

Before doing any live API call, verify that the user has explicitly written:

`APPROVE_LIVE_API_POST_5_REPROJECTION_WITNESS=true`

If absent, stop and report blocked.

## Scale

- 20 to 30 flagged cases maximum.
- No broad dataset expansion.
- No claim upgrade.

## Eligible cases

- sufficient_dropped
- insufficient_and_answered
- high missing_evidence_type confidence
- replay artifact complete

## Hard constraints

- Use only DashScope-compatible live API.
- Do not use vLLM or local scorer.
- Do not compute fixed-target NLL.
- Do not store raw API responses.
- Do not unlock Route 5 or Route 8.
- Do not claim validated repair.

## Outputs

- `artifacts/experiments/post_lapi_reprojection_witness/`
- `docs/experiments/POST-LAPI-reprojection-witness-pilot.md`
- `docs/paper/post-lapi-reprojection-witness-table.md`

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

## Done condition

- Reprojection witnesses are produced for eligible cases.
- Cost and latency deltas are summarized.
- `raw_response_stored=false` is confirmed.
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
