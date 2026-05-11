# P50 ReprojectionWitness Pilot Report

P50 records optional fixture re-projection decisions. It is an audit scaffold, not a new selector algorithm and not metric bridge evidence.

## Claim Boundary

- Data source kind: fixture
- Evidence scope: fixture_reprojection_witness_only
- Paper evidence eligible: false
- Measurement validation claim: false
- Live API used: false
- Prior P47/P48/P49 claims are not upgraded.

## Summary

- Witnesses: 8
- Replay-safe witnesses: 5
- Trigger counts: `{"ambiguous_selector_regime": 1, "budget_violation": 1, "candidate_pool_hash_mismatch": 1, "identity_mismatch": 1, "missing_critical_finding": 1, "operator_requested": 1, "pairwise_escalation": 1, "unsupported_finding": 1}`
- Action counts: `{"abstain_no_safe_reprojection": 3, "add_missing_finding": 2, "compress_redundant_context": 1, "downgrade_to_ambiguous": 1, "remove_unsupported_finding": 1}`
- Budget status counts: `{"not_applicable_fail_closed": 2, "over_budget_non_comparable": 1, "within_budget": 5}`

## Claim Gate

- Calibrated proxy support: false
- V-information proxy support: false
- Selector-regime claim upgraded: false
