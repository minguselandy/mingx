# P58 Provenance-Aware Redundancy Diagnostics Plan

Status: P58 scaffold
Framing: Proxy-Regime Diagnosis
Claim ceiling: operational diagnostic improvement only

## Purpose

P58 defines a provenance-aware redundancy diagnostic scaffold. The goal is to distinguish duplicate waste, independent corroboration, adversarial repetition, source conflict, prerequisite overlap, paraphrase near-duplicates, qualifier mismatch, and temporal-scope mismatch before redundancy-sensitive selector heuristics treat them as the same signal.

This phase is non-P55/P56/P57-success-dependent. P55 remains failed_closed_no_rows / blocked_operator_required. P56 remains no_imported_traces. P57 remains extraction-risk scaffold only. P58 does not proceed from P55/P56 success. P58 does not convert P57 extraction audit into selector validity. P58 does not repair P55/P56 blocked states.

## Claim Boundary

P58 is an operational diagnostic scaffold only.

P58 does not establish selector validity.
P58 does not establish metric bridge support.
P58 does not establish V-information support.
P58 does not establish measurement validation.
P58 does not establish calibrated proxy support.
P58 does not establish paper-grade validation.
P58 does not establish deployed runtime improvement.

Provenance-aware redundancy diagnostics are operational heuristics unless separately calibrated. P58 does not make fixture or template outputs paper evidence. P58 does not repair P55/P56 blocked states. P58 does not proceed from P57 extraction scaffold as selector proof.

## Diagnostic Categories

Each category records a description, selector implication, escalation behavior, claim ceiling, and failure modes.

| Category | Description | Selector Implication | Escalation Behavior | Claim Ceiling | Failure Modes |
|---|---|---|---|---|---|
| `duplicate_redundancy` | Two candidates carry the same finding from the same or effectively identical provenance, confirmed by finding and source-span hashes. | Penalize strongly only when provenance and finding hashes confirm true duplication. | No escalation is needed when identity and provenance agree; otherwise downgrade to ambiguous and audit. | operational diagnostic improvement only | false duplicate from paraphrase, lost source distinction, over-penalized independent corroboration |
| `independent_corroboration` | Candidates support the same or compatible claim from independent sources or independently derived evidence. | Preserve when source independence is high and the claim is important. | Escalate only if source independence is uncertain, provenance is missing, or the claim is high-criticality. | operational diagnostic improvement only | mistaken source independence, source laundering, unsupported consensus |
| `adversarial_repetition` | A claim is repeated, paraphrased, or amplified in a way that may create artificial salience or false consensus. | Do not apply a simple diversity penalty; trigger contradiction/provenance audit. | Audit required; escalate if repetition source, incentive, or contradiction context is unresolved. | operational diagnostic improvement only | adversarial restatement mistaken for corroboration, spam counted as signal, contradiction hidden by repetition |
| `source_conflict_pair` | Candidates disagree, cite conflicting evidence, or encode mutually incompatible claims. | Escalate or adjudicate; do not collapse to a redundancy penalty. | Audit required and adjudication recommended before selector downgrades either side. | operational diagnostic improvement only | false consensus, dropped minority evidence, unsupported adjudication |
| `prerequisite_overlap` | Candidates overlap because one finding is prerequisite context for another. | Preserve or escalate until the prerequisite chain is resolved. | Escalate if the prerequisite link is incomplete, missing, or affects downstream interpretation. | operational diagnostic improvement only | prerequisite dropped as duplicate, causal chain broken, downstream finding overpromoted |
| `paraphrase_near_duplicate` | Candidates are semantically close but not hash-identical; provenance may or may not differ. | Lower priority unless provenance differs or claim criticality requires preservation. | Escalate when provenance differs, qualifiers differ, or source independence is unclear. | operational diagnostic improvement only | independent corroboration collapsed, qualifier drift missed, semantic similarity over-trusted |
| `qualifier_mismatch` | Candidates appear redundant but differ in caveats, scope words, thresholds, negation, or uncertainty. | Escalate because qualifier loss can change claim meaning. | Audit required; preserve both until qualifier meaning is resolved. | operational diagnostic improvement only | caveat loss, overclaim, condition erased by redundancy merge |
| `temporal_scope_mismatch` | Candidates appear redundant but apply to different dates, epochs, releases, phases, or validity windows. | Escalate because time scope can change claim truth. | Audit required; preserve or separate by epoch until temporal scope is resolved. | operational diagnostic improvement only | stale evidence treated as current, phase order corrupted, temporal contradiction hidden |

## Required Feature Fields

The P58 diagnostic template records:

- `record_schema_version`
- `diagnostic_id`
- `candidate_pair_id`
- `candidate_a_id`
- `candidate_b_id`
- `finding_a_hash`
- `finding_b_hash`
- `source_a_id`
- `source_b_id`
- `source_span_a_hash`
- `source_span_b_hash`
- `provenance_handle_a`
- `provenance_handle_b`
- `source_independence_score`
- `provenance_overlap_score`
- `semantic_similarity_score`
- `contradiction_flag`
- `qualifier_mismatch_flag`
- `temporal_scope_mismatch_flag`
- `prerequisite_relation_flag`
- `category_label`
- `category_confidence`
- `selector_implication`
- `escalation_required`
- `audit_required`
- `claim_ceiling`
- `metric_claim_level`
- `selector_regime_label`
- `paper_evidence_eligible`
- `measurement_validation_claim`
- `denied_claims`

## Diagnostic Policy

Duplicate redundancy and independent corroboration must not be treated identically. Duplicate redundancy is safe to penalize strongly only when provenance and finding hashes confirm true duplication. Independent corroboration is preserved when source independence is high and the claim is important.

Adversarial repetition and source conflict trigger audit or escalation, not a simple diversity penalty. Prerequisite overlap is preserved or escalated until the prerequisite chain is resolved. Qualifier mismatch and temporal-scope mismatch are escalated because they can change the meaning or truth of an otherwise similar claim.

The default selector label remains `ambiguous`. The default metric claim level is `operational_utility_only` or `ambiguous_metric`, not bridge support. Any future selector change from this scaffold remains heuristic and operational unless separately calibrated under a reviewed diagnostic threshold contract.

## Conservative Defaults

The P58 template defaults are conservative:

- `paper_evidence_eligible: false`
- `measurement_validation_claim: false`
- `metric_claim_level: operational_utility_only`
- `selector_regime_label: ambiguous`

The template must not default to `greedy_supported`, `calibrated_proxy_supported`, `vinfo_proxy_supported`, or `measurement_validated`.

## Claim-Gate Rules

P58 does not establish metric bridge support from redundancy diagnostics. P58 does not establish selector validity from redundancy categories. P58 does not establish V-information support, measurement validation, calibrated proxy support, or paper-grade evidence.

P58 denies these inferences:

- redundancy category as selector validity
- provenance-aware diagnostic as metric bridge support
- provenance-aware diagnostic as V-information support
- provenance-aware diagnostic as measurement validation
- template or fixture output as paper-grade evidence
- P55 or P56 blocked-state repair
- P57 extraction-risk scaffold as selector proof

## P55/P56/P57 Boundary Preservation

P55 remains failed_closed_no_rows / blocked_operator_required. Rows imported/validated remain 0. P55 review ceiling remains none. P55 paper evidence remains false. P55 fit metrics remain not computed.

P56 remains no_imported_traces. Traces imported/validated remain 0. P56 review ceiling remains none. P56 paper evidence remains false. P56 measurement validation remains false. P56 `vinfo_proxy_supported` and `calibrated_proxy_supported` remain denied.

P57 remains extraction-risk scaffold only. P58 does not proceed from P55/P56 success. P58 does not convert P57 extraction audit into selector validity. P58 does not repair P55/P56 blocked states.

## Future Execution Gate

Future execution may add imported or fixture redundancy records only after a reviewed input-source policy. Fixture records remain fixture-only and paper-ineligible. Imported records remain operational diagnostic evidence unless a later phase independently reviews calibration, bridge status, contamination, and claim eligibility.

Independent review is required before P59 or P60 proceeds from this scaffold.
