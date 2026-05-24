# Goal ID: POST-7-RUN / Extraction quality audit

## Objective

Run the extraction quality audit if and only if the owner approves model-adjudicated audit calls. This result remains model-adjudicated extraction-risk evidence only.

## Required owner approval gate

Before doing any model-adjudicated audit or live API call, verify that the user has explicitly written:

`APPROVE_LIVE_API_POST_7_EXTRACTION_AUDIT=true`

If absent, stop and report blocked.

## Scale

- Target first pass: 100 examples.
- Aim for 10 examples per stratum where feasible.

## Hard constraints

- Use only DashScope-compatible live API if model adjudication is needed.
- Do not use vLLM or local scorer.
- Do not store raw API responses.
- Do not claim human-validated extraction measurement.
- Do not claim measurement validation.
- No Route 5 or Route 8 unlock.

## Outputs

- `artifacts/experiments/post_lapi_extraction_quality_audit/`
- `docs/experiments/POST-LAPI-extraction-quality-audit.md`
- `docs/paper/post-lapi-extraction-quality-table.md`

## Claim rules

Allowed:
- model_adjudicated_extraction_risk_evidence
- operational_extraction_audit

Denied:
- human-validated extraction measurement
- measurement validation
- theorem transfer to M*
- end-to-end validation

## Done condition

- Per-stratum summary is produced.
- Value-weighted loss proxy is reported only as candidate operational evidence.
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
