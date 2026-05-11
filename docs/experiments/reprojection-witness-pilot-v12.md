# P50 ReprojectionWitness Pilot v12

P50 adds an optional fixture scaffold for recording re-projection decisions:

```text
initial candidate pool M
-> initial ProjectionPlan / MaterializedContext
-> diagnostic or runtime trigger
-> re-projection decision
-> revised ProjectionPlan / MaterializedContext
-> ReprojectionWitness
```

The witness is an audit artifact. It is not a new selector algorithm, not a live
runtime integration, and not metric bridge evidence.

## What The Witness Records

Each `ReprojectionWitness` records:

- full dispatch identity: `run_id`, `dispatch_id`, `agent_id`, `round_id`
- candidate-pool provenance through `candidate_pool_hash`
- initial and reprojected projection-plan hashes
- initial and reprojected materialized-context hashes
- trigger type, trigger source, and deterministic reason codes
- re-projection action and finding-level diff fields
- initial/reprojected token counts and budget status
- conservative claim fields

## Trigger And Action Taxonomy

The fixture pilot uses deterministic trigger labels such as
`ambiguous_selector_regime`, `pairwise_escalation`, `budget_violation`,
`missing_critical_finding`, `unsupported_finding`,
`candidate_pool_hash_mismatch`, and `identity_mismatch`.

Actions include `add_missing_finding`, `remove_unsupported_finding`,
`compress_redundant_context`, `downgrade_to_ambiguous`, and
`abstain_no_safe_reprojection`.

These labels describe audit behavior only. They do not prove that the revised
projection improves deployed runtime behavior.

## Fixture Outputs

The deterministic fixture run is located at:

- `artifacts/experiments/reprojection_witness_pilot_v12/`

It writes:

- `reprojection_cases.jsonl`
- `reprojection_witnesses.jsonl`
- `reprojection_actions.csv`
- `reprojection_trigger_counts.csv`
- `reprojection_claim_gate_report.json`
- `reprojection_summary.json`
- `reprojection_manifest.json`
- `reprojection_report.md`

## Claim Boundary

The P50 fixture pilot remains conservative:

- `data_source_kind = fixture`
- `audit_scope = reprojection_witness_pilot`
- `evidence_scope = fixture_reprojection_witness_only`
- `paper_evidence_eligible = false`
- `measurement_validation_claim = false`
- `live_api_used = false`
- `calibrated_proxy_supported = false`
- `vinfo_proxy_supported = false`

`ReprojectionWitness` records why and how a re-projection decision occurred. It
does not establish selector-regime validity, V-information support, calibrated
utility-to-logloss bridge support, measurement validation, paper-grade benchmark
evidence, or deployed runtime improvement.

## Run

```bash
uv run python -m cps.experiments.reprojection_witness --config configs/runs/reprojection-witness-pilot-v12.json --output-dir artifacts/experiments/reprojection_witness_pilot_v12
```
