# P59 ReprojectionWitness Replay Integration Plan

Status: P59 scaffold
Framing: Proxy-Regime Diagnosis
Claim ceiling: operational audit only

## Purpose

P59 defines a replay-integration scaffold for connecting `ReprojectionWitness` records to replay records. The goal is to make re-projection interventions auditable and comparable by binding the witness to dispatch identity, replay identity, candidate-pool hashes, materialized-context hashes, context diffs, budget status, before/after output hashes, evaluator policy, uncertainty label, and metric bridge status.

P59 evaluates witness auditability only. It does not execute live APIs, import operator data, run new replay traces, or generate claim-bearing artifacts.

P59 is non-P55/P56-success-dependent. P55 remains failed_closed_no_rows / blocked_operator_required. P56 remains no_imported_traces. P57 remains extraction-risk scaffold only. P58 remains operational diagnostic scaffold only. P59 does not proceed from P55/P56 success. P59 does not convert P57/P58 scaffolds into evidence claims. P59 does not repair P55/P56 blocked states.

## Claim Boundary

`ReprojectionWitness` is an audit witness, not validation.

P59 does not prove deployed runtime improvement.
P59 does not prove selector validity.
P59 does not establish metric bridge support.
P59 does not establish V-information support.
P59 does not establish measurement validation.
P59 does not establish calibrated proxy support.
P59 does not make fixture or template outputs paper evidence.

Before/after improvement in fixture or test data is operational audit only. It is not deployed runtime improvement, paper evidence, or measurement validation. Missing, stale, mismatched, underpowered, or failed metric bridge status prevents metric claim upgrade.

## Required Witness Fields

The P59 replay-integration template records:

- `record_schema_version`
- `witness_id`
- `initial_run_id`
- `initial_dispatch_id`
- `initial_agent_id`
- `initial_round_id`
- `source_replay_record_id`
- `trigger_type`
- `trigger_rationale`
- `original_budget`
- `revised_budget`
- `budget_delta`
- `selector_before`
- `selector_after`
- `candidate_pool_hash_before`
- `candidate_pool_hash_after`
- `candidate_pool_expansion_documented`
- `materialized_context_hash_before`
- `materialized_context_hash_after`
- `selected_context_before`
- `selected_context_after`
- `excluded_context_before`
- `excluded_context_after`
- `context_diff_summary`
- `output_before_hash`
- `output_after_hash`
- `evaluator_policy`
- `uncertainty_label`
- `over_budget_flag`
- `metric_bridge_status`
- `metric_bridge_contract_id`
- `claim_gate_result`
- `paper_evidence_eligible`
- `measurement_validation_claim`
- `deployed_runtime_improvement_claim`
- `denied_claims`

## Trigger Types

The P59 template supports these conservative trigger types:

- `unknown_due_to_missing_context`
- `hallucination_risk`
- `wrong_despite_context`
- `ambiguous`
- `operator_review_requested`
- `budget_overflow`
- `candidate_pool_mismatch`

Additional trigger types must be documented before use and must preserve the same fail-closed claim boundaries.

## Replay Binding Rules

Each `ReprojectionWitness` must bind to a source replay record through:

- full dispatch identity: `initial_run_id`, `initial_dispatch_id`, `initial_agent_id`, `initial_round_id`;
- `source_replay_record_id`;
- candidate-pool hashes before and after re-projection;
- materialized-context hashes before and after re-projection;
- selected and excluded context before and after re-projection;
- budget before and after re-projection;
- output hashes before and after re-projection;
- evaluator and uncertainty policy;
- metric bridge status and contract id.

The replay binding is not allowed to infer missing identity, missing candidate-pool expansion, or missing materialized-context hashes. Missing or mismatched binding fails closed.

## Decision Rules

### Identity mismatch

If dispatch identity does not bind to a replay record:

```text
classification: not_comparable
paper_evidence_eligible: false
no metric claim upgrade
```

### Candidate-pool mismatch

If candidate-pool hashes differ without documented expansion:

```text
classification: fail_closed_candidate_pool_mismatch
paper_evidence_eligible: false
no metric claim upgrade
```

Candidate-pool expansion is comparable only when it is explicitly documented and reviewed. Undocumented expansion remains fail-closed.

### Over-budget revised context

If the revised context exceeds the declared budget:

```text
classification: operational_violation
paper_evidence_eligible: false
no metric claim upgrade
```

### Missing or stale bridge

If the metric bridge is missing, stale, mismatched, underpowered, ambiguous, or failed:

```text
metric_claim_level: ambiguous_metric or operational_utility_only
no calibrated_proxy_supported
no vinfo_proxy_supported
```

### Fixture-only before/after improvement

If fixture or test rows show before/after improvement:

```text
operational audit only
not deployed runtime improvement
not paper evidence
not measurement validation
```

## Conservative Defaults

The P59 JSON template defaults are:

- `paper_evidence_eligible: false`
- `measurement_validation_claim: false`
- `deployed_runtime_improvement_claim: false`
- `metric_bridge_status: missing`
- `claim_gate_result: audit_only_or_not_comparable`

The template must not default to `calibrated_proxy_supported`, `vinfo_proxy_supported`, `measurement_validated`, or `deployed_runtime_improvement`.

## Claim-Gate Rules

P59 denies these inferences:

- `ReprojectionWitness` as deployed runtime improvement
- before/after fixture improvement as validation
- before/after fixture improvement as paper evidence
- replay integration as selector validity
- replay integration as metric bridge support
- replay integration as V-information support
- replay integration as measurement validation
- P55 or P56 blocked-state repair
- P57 or P58 scaffold conversion into evidence claims

## P55/P56/P57/P58 Boundary Preservation

P55 remains failed_closed_no_rows / blocked_operator_required. Rows imported/validated remain 0. P55 review ceiling remains none. P55 paper evidence remains false. P55 fit metrics remain not computed. P55 `vinfo_proxy_supported` and `calibrated_proxy_supported` remain denied.

P56 remains no_imported_traces. Traces imported/validated remain 0. P56 review ceiling remains none. P56 paper evidence remains false. P56 measurement validation remains false. P56 `vinfo_proxy_supported` and `calibrated_proxy_supported` remain denied.

P57 remains extraction-risk scaffold only. It is not selector validity, not metric bridge support, and not measurement validation.

P58 remains operational diagnostic scaffold only. It is not selector validity, not metric bridge support, and not measurement validation.

P59 does not proceed from P55/P56 success. P59 does not convert P57/P58 scaffolds into evidence claims. P59 does not repair P55/P56 blocked states.

## Future Execution Gate

Future P59 execution may import real replay-linked `ReprojectionWitness` rows only after a reviewed input-source policy. Fixture and template rows remain operational audit only and paper-ineligible. Any future metric or paper claim requires separate review of bridge status, replay binding, contamination, and claim eligibility.

Independent review is required before P60 proceeds from this scaffold.
