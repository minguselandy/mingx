# Related Work: Live-API Operational Audit

Status: LAPI-8 related-work positioning note
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This note positions the live-API-only package in the related-work narrative. It
does not add evidence, run a live API call, or change any route state.

## Audit-First Operational Evaluation

The live-api operational audit belongs to audit-first operational evaluation:
systems are instrumented so their context-projection decisions, candidate
pools, materialization choices, costs, and downstream diagnostics can be
reviewed without claiming that the observed utility is already a calibrated
metric proxy.

For this paper, the audit surface is the contribution boundary. Projection
bundles, claim ledgers, backend witnesses, replay manifests, sufficiency
witnesses, and extraction-risk ledgers support operational inspection. They are
not measurement validation, not metric bridge support, and not paper evidence.

## Formal Objective Versus Hosted Backend Surface

The formal related-work anchor is predictive V-information for dispatch-time
content selection. The hosted live-API backend is a different layer: it exposes
generated output-token confidence signals and normalized model outputs, but it
does not expose fixed-target teacher-forced NLL or fixed-target continuation
scoring.

This separation is the paper's bridge discipline. The formal objective can
motivate the selector and the diagnostics, while the current experiments remain
operational diagnostics or candidate evidence only.

## LLM Judges And Weak Supervision

LLM judges and weak supervision are useful for scalable review, rubric-based
triage, parse-failure detection, disagreement analysis, and candidate labeling.
The LAPI weak-evidence harness therefore treats judge outputs as weak-source
candidate diagnostics with stability gates.

This is not measurement validation. Model-adjudicated outputs do not become
human/external gold labels, human-human agreement, or kappa evidence. They also
do not establish selector superiority or global selector superiority.

## Structured Extraction And Faithfulness

Structured extraction and faithfulness work motivates the `M* -> M` bottleneck:
free-form worker outputs must be converted into structured findings before the
selector optimizes over the candidate pool. The LAPI extraction audit reports
stratified extraction-risk diagnostics such as missing findings, qualifier
loss, temporal-scope errors, provenance loss, and selector-impact risk.

These diagnostics are not theorem transfer from `M` to `M*`, not selector
validity, not measurement validation, and not metric bridge support. A future
human sentinel lane can estimate bias only after separate approval, actual
human labels, agreement calculation, and contamination review.

## Operational Replay And Candidate Evidence

Operational replay belongs in the related work as a deployment audit practice:
matched candidate pools, budgets, baselines, and materialization policies make
the run inspectable. In this paper, hard replay evidence is separated from weak
model-adjudicated evidence because only the former has fixed replay conditions,
and neither replaces a missing bridge.

The safe related-work claim is therefore narrow: the paper combines a formal
V-information objective with claim-gated live-API operational audit. It does
not claim measurement validation, metric bridge support, calibrated proxy
support, V-information proxy support, paper evidence, selector superiority,
Route 5 unlock, or Route 8 unlock.

This is not selector superiority.
