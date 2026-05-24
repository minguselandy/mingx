# Live API Experiment Boundaries

Status: LAPI-1 paper boundary note
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This note states how live-API-only results may be described in paper-facing
documentation. It does not add evidence, run experiments, or change any claim
ledger state.

## Paper-Safe Description

The live-API-only package may be described as a backend-constrained operational
diagnostic and candidate evidence factory. It can organize generated
output-token logprobs, constrained label-generation outputs, LLM-generated
silver labels, uncertainty buckets, and replayable artifacts for review.

Methods-facing capability boundary:

| component | methods role | denied interpretation |
|---|---|---|
| generated output-token logprobs | output-side confidence diagnostics | fixed-target teacher-forced NLL or fixed-target continuation scoring |
| constrained label generation | normalized operational candidate labels | metric bridge support |
| model-adjudicated weak labels | weak judge protocol and bias-control surface | human/external gold labels |
| ProjectionBundleV1 | replayable artifact chain tying plan, budget, context, witnesses, and ClaimLedger | validation by itself |
| ClaimLedger | fail-closed allowed/denied claim record | route unlock or claim upgrade |

Generated output-token logprobs are answer-side confidence diagnostics only.
They are not fixed-target teacher-forced NLL and not fixed-target continuation
scoring. They must not be interpreted as a bridge from operational utility to
formal V-information or fixed deployed-model log-loss.

They are not fixed-target continuation scoring.

Constrained label generation is candidate proxy only. Model-adjudicated weak
labels and LLM-generated silver labels are candidate operational evidence only.
They are not human/external gold labels and cannot supply measurement
validation.

## Paper-Facing Claim Ceiling

| item | status | paper-facing ceiling |
|---|---|---|
| DashScope-compatible live API | allowed backend surface | operational diagnostics |
| generated output-token logprobs | available | answer-side confidence diagnostics only |
| constrained label generation | available | candidate proxy only |
| model-adjudicated weak labels | available | candidate operational evidence only |
| replayable artifact evidence | available | auditability and operational diagnosis |
| fixed-target teacher-forced NLL | blocked | no metric bridge |
| fixed-target continuation scoring | blocked | no Route 5 unlock |
| human/external gold labels | unavailable | no measurement validation |
| EPF-FINAL | accepted with notes | candidate operational evidence only |

## Explicit Denials

The live-API-only evidence package does not support:

- local HF
- torch
- transformers scorer
- vLLM
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

## Route Locks

Route 5 locked: true

Route 8 locked: true

Route 5 unlock: false

Route 8 unlock: false

Route 5 and Route 8 remain locked because the live API does not expose
fixed-target continuation scoring and the current package has no human/external
gold validation. EPF-FINAL remains candidate operational evidence only, and
raw API responses stored: false.

Human/external gold labels available: false.

EPF-FINAL validates the paper: false.

## Manuscript Wording Rule

Use wording such as "backend-constrained operational diagnostic", "candidate
operational evidence", "model-adjudicated silver labels", and "reviewable
candidate package". Do not write that live-API results establish measurement
validation, metric bridge support, calibrated proxy support, V-information proxy
support, teacher-forced NLL support, paper evidence, or selector superiority.
