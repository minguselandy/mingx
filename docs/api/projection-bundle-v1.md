# ProjectionBundleV1 API

Status: LAPI-2 artifact schema and claim-gate contract
Claim ceiling: `operational_utility_only/no_claim_upgrade`

ProjectionBundleV1 is the canonical metadata envelope for auditable
context-projection runs. It records enough structured state to replay,
inspect, and claim-gate an operational run without storing raw API response
bodies.

The contract is sourced from:

- `docs/goals/mingx_codex_goal_live_api_plan/configs/artifact_bundle_schema.yaml`
- `docs/goals/mingx_codex_goal_live_api_plan/configs/claim_gate_contract.yaml`
- `docs/archive/context_projection_fixed_v12.md`, Section 6
- `docs/paper/v12-evidence-ledger.md`

## Required Records

ProjectionBundleV1 keeps the existing identity fields:

- `run_id`
- `dispatch_id`
- `agent_id`
- `round_id`

It then records the required operational artifacts:

- `candidate_pool`
- `projection_plan`
- `budget_witness`
- `materialized_context`
- `metric_bridge_witness`
- `claim_ledger`
- `cost_latency_ledger`

The schema also accepts optional witnesses when they are present:

- `counterfactual_replay_witness`
- `reprojection_witness`
- `judge_run_manifest`

Optional witnesses are validated as complete records when included. Missing
optional witnesses do not invalidate a bundle.

## Completeness

The LAPI-2 contract fields are checked for the four paper-facing runtime
artifacts:

- `ProjectionPlan`
- `BudgetWitness`
- `MaterializedContext`
- `MetricBridgeWitness`

If any required contract field is absent, `artifact_status` becomes
`incomplete`. Incomplete bundles fail closed in the embedded `claim_ledger`:

- `allowed_claims` is empty.
- `no_aggregated_headline_claim` is added to `denied_claims`.
- Route 5 and Route 8 stay locked.
- `metric_claim_level` stays `operational_utility_only`.

Complete bundles may support only `replayable_artifact_evidence` by artifact
completeness alone. Artifact completeness does not support validation, metric
bridge support, V-information proxy support, paper-grade evidence, selector
superiority, Route 5 unlock, or Route 8 unlock.

## Raw Response Policy

`raw_response_stored` defaults to `false` and must remain false. The schema
rejects raw response body keys such as:

- `raw_response`
- `raw_response_body`
- `raw_response_payload`
- `raw_api_response`
- `raw_api_response_body`
- `raw_api_response_payload`

False-valued storage flags such as `raw_response_stored: false` and
`raw_api_responses_stored: false` are allowed because they document the storage
policy. True-valued raw-response storage flags fail the bundle.

## Logprob Boundary

Generated-token logprobs may appear only as answer-side confidence diagnostics.
When a metric bridge witness includes generated-token logprob metadata,
`generated_token_logprobs_used_as_answer_side_diagnostic_only` must be true.

Generated-token logprobs do not provide:

- fixed-target NLL support
- teacher-forced scoring support
- fixed-target continuation scoring support
- metric bridge support
- calibrated proxy support
- V-information proxy support
- Route 5 unlock
- Route 8 unlock

## ClaimLedger

The embedded `ClaimLedger` records:

- `current_claim_level`
- `allowed_claims`
- `denied_claims`
- `claim_upgrade`
- `route_5_locked`
- `route_8_locked`
- `raw_response_stored`
- claim-gate statuses for artifact, bridge, judge, replay, and reprojection

By default it preserves:

- `current_claim_level: operational_utility_only/no_claim_upgrade`
- `metric_claim_level: operational_utility_only`
- `claim_upgrade: false`
- `route_5_locked: true`
- `route_8_locked: true`
- `raw_response_stored: false`
- `human_external_gold_label: false`

Metric bridge support, measurement validation, V-information proxy support,
selector superiority, global selector superiority, Route 5 unlock, and Route 8
unlock remain denied unless a future evidence package explicitly records
controller review, independent review, and an accepted evidence package.

## CostLatencyLedger

The embedded `CostLatencyLedger` records compact accounting metadata:

- `input_tokens`
- `output_tokens`
- `total_tokens`
- `estimated_cost`
- `latency_ms`

The ledger stores summaries only. It does not store prompts, completions, raw
responses, or raw API payloads.

## EPF-FINAL Mapping

`projection_bundle_from_epf_final_metadata(...)` maps EPF-FINAL metadata into a
ProjectionBundleV1 envelope. The mapper consumes normalized metadata such as:

- `final_epf_manifest.json`
- `final_claim_request.json`
- `scoped_operational_evaluation_summary.json`

The mapping stores artifact paths, hashes, label counts, claim flags, and
compact provenance. It does not store raw API responses or raw model outputs.

The EPF-FINAL mapping preserves the current boundary:

- EPF-FINAL is backend-constrained candidate operational evidence.
- `raw_response_stored` remains false.
- fixed-target NLL support remains false.
- measurement validation remains denied.
- metric bridge support remains denied.
- Route 5 and Route 8 remain locked.
