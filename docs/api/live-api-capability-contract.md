# Live API Capability Contract

Status: LAPI-1 claim guardrail contract
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This contract defines the live-API-only capability surface used by the current
mingx evidence packages. It is a guardrail document, not a new experiment and
not a claim upgrade.

The two planned configuration inputs named by the LAPI-1 goal were not present
in this checkout at implementation time:

- `configs/claim_gate_contract.yaml`
- `configs/live_api_only_experiment_plan.yaml`

This document therefore records the operative contract directly from the current
paper-facing claim ledger, EPF-FINAL artifacts, and PAPER-RS restructuring docs.

## Allowed Capability Surface

The allowed live API surface is narrow:

- DashScope-compatible live API.
- Generated output-token logprobs are answer-side confidence diagnostics only.
- Constrained label generation is candidate proxy only.
- Model-adjudicated weak labels are candidate operational evidence only.
- Replayable artifact evidence may be used for auditability and operational
  diagnosis.
- Normalized labels, compact confidence fields, input hashes, prompt hashes,
  evidence hashes, model identifiers, and provenance may be stored.

The allowed surface does not include raw response storage, local backend
fallbacks, or fixed-target scoring claims.

## Methods Capability Table

| Capability | Methods use | ClaimLedger status |
|---|---|---|
| Generated output-token logprobs | answer-side confidence diagnostics only | denied as fixed-target teacher-forced NLL and fixed-target continuation scoring |
| Constrained label generation | normalized candidate labels for operational review | denied as metric bridge support |
| Model-adjudicated weak labels | disagreement, stability, sufficiency, and extraction-risk diagnostics | denied as human/external gold labels |
| ProjectionBundleV1 artifacts | replayable audit chain for dispatch-time projection | denied as validation by themselves |
| Fixed-target teacher-forced NLL | unsupported | fail closed |
| Fixed-target continuation scoring | unsupported | fail closed |
| Human/external gold labels | unavailable in the current package | no measurement validation |
| Raw API responses | not stored | normalized records and hashes only |

## Denied Capability Surface

The current live-API-only package denies the following as active capabilities or
claims:

- local HF
- torch
- transformers scorer
- vLLM
- other APIs outside the approved DashScope-compatible live API surface
- prompt_logprobs support
- fixed-target teacher-forced NLL
- fixed-target continuation scoring
- metric bridge support
- calibrated_proxy_supported
- vinfo_proxy_supported
- measurement validation
- human/external gold validation
- paper-grade evidence
- selector superiority
- global selector superiority
- Route 5 unlock
- Route 8 unlock

## Fixed-Target Scoring Boundary

Generated output-token logprobs are answer-side confidence diagnostics only. They
are not fixed-target teacher-forced NLL and are not fixed-target continuation
scoring. They score the model output path exposed by the available chat API, not
a predetermined target continuation under a fixed materialization policy.

They are not fixed-target continuation scoring.

Because fixed-target teacher-forced NLL is blocked, generated-token chat
logprobs must not be used as metric bridge support, calibrated proxy support,
V-information proxy support, Route 5 unlock evidence, Route 8 unlock evidence,
or paper evidence.

## Label Boundary

Constrained label generation and LLM-generated silver labels are candidate
operational evidence only. They are not human/external gold labels, not
measurement validation, and not paper-grade validation evidence.

Model-adjudicated weak labels may support reviewable candidate diagnostics when
stored as normalized enum labels with provenance. They must not be represented
as human labels, external gold labels, human-human agreement, kappa, or
measurement validation.

## Claim Flags

| claim flag | value |
|---|---|
| claim status | `operational_utility_only/no_claim_upgrade` |
| generated output-token logprobs are answer-side confidence diagnostics only | true |
| fixed-target teacher-forced NLL support | false |
| fixed-target continuation scoring support | false |
| metric bridge support | false |
| calibrated_proxy_supported | false |
| vinfo_proxy_supported | false |
| measurement validation | false |
| human/external gold validation | false |
| paper-grade evidence | false |
| selector superiority | false |
| global selector superiority | false |
| Route 5 locked: true | true |
| Route 8 locked: true | true |
| Route 5 unlock: false | false |
| Route 8 unlock: false | false |
| raw API responses stored: false | false |
| human/external gold labels available: false | false |
| EPF-FINAL validates the paper: false | false |

EPF-FINAL is candidate operational evidence only. It is a backend-constrained
candidate evidence factory, not validation of the paper.

## Guardrail Interpretation

Future code, docs, and artifacts must fail closed if they imply any denied
claim. The safe replacement is to describe the package as live-API-only,
backend-constrained, operational, candidate, or diagnostic, and to keep the
claim status at `operational_utility_only/no_claim_upgrade`.

The ClaimLedger for any methods-facing package must record allowed claims,
denied claims, Route 5 / Route 8 lock state, raw-response storage state,
human/external gold-label state, metric-bridge state, and the claim-upgrade
flag. Unsupported, stale, absent, underpowered, or stratum-mismatched evidence
must be recorded as a denied stronger claim.
