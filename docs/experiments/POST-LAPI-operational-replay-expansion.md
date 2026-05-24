# POST-LAPI Operational Replay Expansion

Goal ID: POST-6-RUN / Matched-budget operational replay expansion
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Scope

This owner-approved POST-6 run packages existing offline HotpotQA matched-budget operational replay traces into POST-LAPI scoped operational comparison artifacts. It does not run live API calls and does not store raw API responses.

## Run Metadata

- Live API calls run: `0`
- Replay records: `2000`
- Candidate pools: `200`
- Budgets: `[512, 1024]`
- Raw API responses stored: `false`
- Route 5 locked: `true`
- Route 8 locked: `true`
- Claim upgrade introduced: `false`
- Gate status: `post6_operational_replay_completed`

## Matched-Budget Conditions

Rows are comparable only within the same candidate-pool hash and fixed budget. The package records fixed downstream placeholders for offline replay: prompt hash, model snapshot, endpoint, thinking mode, decoding policy, and token-budget accounting are held constant as offline replay conditions.

## Oracle Treatment

`gold_support_oracle_upper_bound` is retained only as `non_deployable_upper_bound` and is not used as a deployable baseline.

## Claim Boundary

Allowed interpretation is scoped operational improvement evidence under matched budgets and `operational_utility_only`. Denied interpretations include selector superiority, global selector superiority, metric bridge support, measurement validation, calibrated proxy support, vinfo proxy support, paper evidence, Route 5 unlock, and Route 8 unlock.

## Artifact Index

- `artifacts/experiments/post_lapi_operational_replay/replay_records.jsonl`
- `artifacts/experiments/post_lapi_operational_replay/comparison_summary.csv`
- `artifacts/experiments/post_lapi_operational_replay/paired_comparisons.json`
- `artifacts/experiments/post_lapi_operational_replay/candidate_pool_manifest.json`
- `artifacts/experiments/post_lapi_operational_replay/run_manifest.json`
- `artifacts/experiments/post_lapi_operational_replay/claim_ledger.json`
