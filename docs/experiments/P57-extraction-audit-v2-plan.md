# P57 Extraction Audit v2 Plan

Status: P57 scaffold
Framing: Proxy-Regime Diagnosis
Claim ceiling: extraction-risk evidence only

## Purpose

P57 defines a value-stratified plan for auditing the upstream extraction boundary:

```text
source material M-star -> extraction and ingestion gate -> structured candidate pool M
```

The audit asks whether findings that matter for context projection are lost, distorted, unsupported, over-merged, or stripped of provenance before selector diagnostics operate.

P57 is non-P55/P56-success-dependent. P55 remains failed_closed_no_rows / blocked_operator_required. P56 remains no_imported_traces. P57 does not proceed from P55/P56 success. P57 does not repair P55/P56 blocked states.

## Claim Boundary

P57 is an extraction-risk scaffold only.

The following boundaries are active:

- extraction audit is not selector validity
- extraction audit is not metric bridge support
- extraction audit is not V-information support
- extraction audit is not measurement validation
- fixture-only extraction audit is not paper-grade evidence
- model-adjudicated audit is not human validation
- human labels require operator approval
- human-human kappa requires actual human annotators and valid agreement calculation

No P57 plan, template, fixture, or future audit row may upgrade P55, P56, metric-bridge, selector-regime, or paper-evidence claims by itself.

## Output Surfaces

P57 creates planning and template surfaces only:

- `docs/templates/extraction-audit-v2-record-template.json`
- `docs/templates/human-sentinel-extraction-audit-protocol-template.md`

No extraction audit execution is performed in P57. No human labeling is performed in P57.

## Extraction-Risk Strata

Each stratum must record description, context-projection relevance, expected failure modes, minimum record fields, and claim ceiling.

| Stratum | Description | Why It Matters | Expected Failure Modes | Minimum Record Fields | Claim Ceiling |
|---|---|---|---|---|---|
| `simple_factual` | Atomic source-supported fact with one clear proposition. | Baseline extraction health; failures here indicate basic ingestion risk. | missing, unsupported_added, provenance_lost. | source span, extracted item, label, provenance expected/observed. | extraction-risk evidence only |
| `complex_conditional` | Finding whose truth depends on conditions, exceptions, or if-then structure. | Conditional facts often control whether a candidate is useful or harmful. | captured_core_changed, qualifier_lost, unsupported_added. | qualifier expected/observed, label rationale, source span. | extraction-risk evidence only |
| `qualifier_heavy` | Finding with scope words, caveats, thresholds, uncertainty, or negation. | Lost qualifiers can convert cautious evidence into overclaims. | qualifier_lost, captured_core_changed, unsupported_added. | qualifier expected/observed, ground truth finding, extracted finding. | extraction-risk evidence only |
| `temporal_scope` | Finding whose validity depends on date, epoch, release, phase, or ordering. | Wrong temporal scope can poison replay and phase-state decisions. | temporal_scope_error, missing, provenance_lost. | temporal scope expected/observed, source document hash, label. | extraction-risk evidence only |
| `cross_chunk` | Finding requiring material from multiple source spans or chunks. | Candidate generation can drop links between distributed evidence. | missing, captured_core_changed, duplicate_or_overmerged. | source span hash, prerequisite context, provenance expected/observed. | extraction-risk evidence only |
| `long_tail_entity` | Finding about rare entities, uncommon file paths, unusual labels, or low-frequency concepts. | Long-tail misses can remove exactly the candidate that makes projection useful. | missing, unsupported_added, provenance_lost. | source document id, source span hash, extracted item id, stratum. | extraction-risk evidence only |
| `high_provenance_value` | Finding where source identity, citation, or artifact lineage is central. | Provenance-sensitive findings can be unusable if detached from source support. | provenance_lost, unsupported_added, captured_core_changed. | provenance expected/observed, source document hash, extracted item hash. | extraction-risk evidence only |
| `prerequisite` | Finding that unlocks or constrains later findings. | Dropping prerequisites can make selector diagnostics look healthy over an already-biased M. | missing, prerequisite_context_lost, captured_core_changed. | prerequisite context, value weight, criticality, selector impact estimate. | extraction-risk evidence only |
| `contradictory` | Finding embedded in source conflict, disagreement, or mutually exclusive claims. | Losing contradiction context can turn uncertain evidence into a false consensus. | contradiction_lost, unsupported_added, duplicate_or_overmerged. | contradiction context, provenance expected/observed, label rationale. | extraction-risk evidence only |
| `adversarial_repetition_sensitive` | Repeated or paraphrased finding where redundancy, spam, or adversarial restatement matters. | Over-merging or duplicate counting can bias candidate-pool value and redundancy diagnostics. | duplicate_or_overmerged, captured_core_changed, provenance_lost. | candidate pool hash, extracted item hash, provenance expected/observed. | extraction-risk evidence only |

## Required Labels

The P57 record template supports these labels:

- `captured_exact`
- `captured_core_preserved`
- `captured_core_changed`
- `missing`
- `unsupported_added`
- `duplicate_or_overmerged`
- `contradiction_lost`
- `qualifier_lost`
- `temporal_scope_error`
- `provenance_lost`
- `selector_impact_estimate`

`selector_impact_estimate` is a risk estimate only. It is not selector validity and not metric support.

## Extraction Metrics

P57 uses extraction-specific metric names:

- `extraction_completeness_by_stratum`
- `effective_extraction_completeness`
- `value_weighted_extraction_loss`
- `critical_finding_miss_rate`
- `unsupported_finding_rate`
- `provenance_loss_rate`

Do not use `c_s` or `zeta_s` for extraction audit metrics. Those names are bridge-calibration quantities and remain separate from extraction-risk reporting.

## Record Schema Requirements

Each future P57 audit record must include:

- stable source and extracted-item identity fields;
- source and extracted-item hashes;
- candidate-pool hash;
- stratum;
- ground-truth and extracted finding text;
- extraction label and rationale;
- expected and observed provenance, qualifier, and temporal-scope fields;
- contradiction and prerequisite context;
- value weight and criticality;
- selector impact estimate marked as risk only;
- data source kind and label source kind;
- annotator count and adjudication status;
- agreement statistic and human-human kappa status;
- model-adjudication status;
- paper-evidence and measurement-validation booleans;
- denied claims.

## Human-Sentinel Lane

Human sentinel work is operator-gated. It is not executed in P57.

If a future phase runs the human-sentinel lane, it must record annotator count, label protocol version, adjudication procedure, agreement statistic when valid, disagreement analysis, contamination review, and whether labels are sentinel-only or measurement-validation candidates.

Missing human labels or missing kappa must not be filled by model adjudication.

Human sentinel evidence is not automatically measurement validation. It may become a measurement-validation candidate only after separate review confirms operator approval, actual human labels, valid agreement calculation, contamination handling, and relevant metric-bridge evidence.

## P55/P56 Preservation

P55 remains failed_closed_no_rows / blocked_operator_required. Rows imported/validated remain 0. P55 review ceiling remains none. P55 paper evidence remains false. P55 fit metrics remain not computed.

P56 remains no_imported_traces. Traces imported/validated remain 0. P56 review ceiling remains none. P56 paper evidence remains false. P56 measurement validation remains false. P56 `vinfo_proxy_supported` and `calibrated_proxy_supported` remain denied.

P57 does not proceed from P55/P56 success. P57 does not repair P55/P56 blocked states.

## Future Execution Gate

Future execution requires a reviewed input source and label-source policy. Human labels require operator approval. A fixture-only audit remains fixture-only. A model-adjudicated audit remains model-adjudicated and cannot be described as human validation.

Independent review is required before P58, P59, or P60 proceeds from this scaffold.
