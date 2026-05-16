# Human Sentinel Extraction Audit Protocol Template

Status: template only
Claim ceiling: sentinel extraction-risk evidence only

## Purpose

This protocol defines a future operator-gated human-sentinel lane for P57 extraction audit v2. It checks whether model-adjudicated or fixture extraction labels miss systematic extraction defects, especially for high-value, prerequisite, qualifier-heavy, contradiction-sensitive, provenance-sensitive, temporal-scope, and long-tail findings.

The protocol is not executed by this template. It does not create human labels, kappa, measurement validation, selector validity, or metric bridge support.

## Operator Gate

Human sentinel execution requires explicit operator approval before any human annotation starts.

The operator gate must record:

- approved source material;
- allowed annotator pool;
- label protocol version;
- contamination review procedure;
- adjudication owner;
- whether outputs are sentinel-only or candidates for later measurement-validation review.

## Annotator Requirements

Future human annotators must be actual independent human reviewers for any human-label or agreement claim.

The protocol must record:

- annotator count;
- annotator independence statement;
- training or calibration material;
- allowed access to source material;
- blinded or unblinded status;
- adjudication policy.

## Label Instructions

Annotators label each ground-truth finding against the extracted finding with one primary label:

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

`selector_impact_estimate` is risk estimate only. It is not selector validity and not metric support.

Annotators must cite the source span, expected provenance, expected qualifiers, temporal scope, contradiction context, and prerequisite context when those fields are applicable.

## Adjudication Procedure

The adjudication procedure must keep raw labels separate from adjudicated labels.

Required records:

- per-annotator label;
- adjudicated label;
- adjudication rationale;
- disagreement categories;
- source-span references used in adjudication;
- whether the item remains unresolved.

Model assistance may be used only as a non-authoritative aid if the operator approved it. Model output must be marked as model-adjudicated or model-assisted, not human.

## Agreement Statistic Requirements

Human-human agreement may be reported only when there are actual independent human annotators, a valid label set, and a documented calculation method.

If agreement is unavailable, invalid, or underpowered, the record must say so directly. Missing agreement must not be filled by model adjudication.

## Kappa Handling

Kappa may be reported only when actual human annotators and a valid agreement calculation are present.

Missing human labels or missing kappa must not be filled by model adjudication.

Model-adjudicated labels are not human labels.

## Contamination Review

The protocol must review whether annotators or model aids had prior access to answers, generated labels, or source transformations that would contaminate the sentinel task.

If contamination is unknown or failed, the labels remain sentinel-only and paper-ineligible unless a later review says otherwise.

## Sentinel Evidence Only

Labels remain sentinel evidence only when:

- annotator count is insufficient;
- agreement is unavailable, invalid, or underpowered;
- contamination status is unknown or failed;
- source coverage is narrow;
- label adjudication relies on model output;
- the audit is fixture-only;
- metric bridge status is missing, stale, or irrelevant.

Human sentinel evidence is not automatically measurement validation.

## Measurement-Validation Candidate Gate

Labels could become measurement-validation candidates only after a separate review confirms:

- operator approval;
- actual human labels;
- valid agreement calculation;
- contamination handling;
- source coverage fit for the claim;
- no model substitution for human labels;
- relevant metric-bridge evidence when a metric claim is being considered.

This template does not grant that status.

## Explicit Non-Substitution Rule

Missing human labels or missing kappa must not be filled by model adjudication.

Model-adjudicated labels are not human labels.

Human sentinel evidence is not automatically measurement validation.

Extraction audit results do not prove selector validity.

Extraction audit results do not establish metric bridge support.

## Claim Boundaries

extraction audit is not selector validity

extraction audit is not metric bridge support

extraction audit is not V-information support

extraction audit is not measurement validation

fixture-only extraction audit is not paper-grade evidence

model-adjudicated audit is not human validation

P55 remains failed_closed_no_rows / blocked_operator_required.

P56 remains no_imported_traces.

P57 does not proceed from P55/P56 success and does not repair P55/P56 blocked states.
