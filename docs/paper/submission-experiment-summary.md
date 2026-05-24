# Submission Experiment Summary

Status: POST-8 submission package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This summary organizes existing POST-LAPI and v12 evidence for reviewer-facing
submission. It does not run live API calls, execute experiments, create labels,
or store raw API responses.

## Operational evaluation and weak-evidence diagnostics

The operational evaluation is limited to named datasets, baselines, budgets,
and artifact contracts. Route 2 supports a scoped HotpotQA operational
comparison under matched budgets. It does not support selector superiority,
global selector superiority, metric bridge support, measurement validation, or
V-information verification.

Weak-evidence diagnostics include LLM judge stability, sufficiency and
abstention regimes, EPF-FINAL candidate silver labels, and extraction-quality
audit configuration. These diagnostics are useful as operational risk
interfaces and candidate evidence, but they are not human/external gold labels
and do not supply measurement validation.

## Backend capability and claim boundary

The live API provides generated-token chat logprobs, not fixed-target
teacher-forced NLL or fixed-target continuation scoring. We do not relabel
generated-token chat logprobs as teacher-forced NLL. We do not claim
V-information verification. We do not claim measurement validation.

The live-API-only constraint contributes a concrete backend boundary: it shows
which audit artifacts can be reproduced through deployed APIs and where formal
metric claims must fail closed because the needed scoring backend is absent.

## Replayable artifact interface

The paper package emphasizes replayable artifacts, manifests, claim ledgers,
prompt and model snapshots where applicable, candidate-pool hashes, and
normalized outputs. This interface lets reviewers inspect the operational
audit trail without treating operational artifacts as validation.

Raw API responses are not stored. Route 5 remains locked. Route 8 remains
locked.

## Sufficiency, abstention, and reprojection witnesses

Sufficiency and abstention tables are planned diagnostics for support,
contradict, insufficient, abstain, and parse-failure regimes. Reprojection
witness tables are planned replayability and repair-audit surfaces. These are
not truth validation, human-calibrated abstention, validated repair, or theorem
transfer.

They are included to show the submission's fail-closed audit architecture:
when weak evidence is unstable, insufficient, or provenance-losing, the claim
stays operational-only or is suppressed.

## Limitations and non-claims

The submission does not claim a fixed-target NLL bridge, metric bridge support,
calibrated proxy support, V-information proxy support, measurement validation,
paper evidence, selector superiority, global selector superiority, Route 5
unlock, or Route 8 unlock.

The contribution is a fail-closed, replayable, claim-gated operational audit
framework for dispatch-time evidence selection. It connects formal motivation,
backend capability checks, operational replay, and weak-evidence diagnostics
while keeping claim boundaries explicit.

## Current Completion State

| component | status | allowed use | non-claim |
|---|---|---|---|
| Backend capability boundary | complete | explain live-API limits | no fixed-target NLL bridge |
| Route 2 operational replay | complete for scoped HotpotQA package | operational comparison under matched budgets | no selector superiority |
| Artifact replay integrity | complete offline audit | replayable artifact interface | no measurement validation |
| POST-LAPI table/readiness plan | complete | submission organization | no experiment result upgrade |
| Judge stability | config/table template | weak-evidence diagnostic after approved run | no human gold or judge validation |
| Sufficiency and abstention | config/table template | operational diagnostic after approved run | no truth validation |
| Reprojection witness | config/table template | replayable witness after approved run | no validated repair |
| Operational replay expansion | config/table template | future matched-budget expansion after approval | no global superiority |
| Extraction quality audit | config/table template | M* -> M extraction-risk audit after approval | no extraction measurement validation |
