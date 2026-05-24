# Live API Only Development Plan

Status: LAPI-1 roadmap
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This roadmap sequences future live-API-only development while preserving the
current claim boundary. It does not authorize live API calls by itself and does
not unlock any route.

## Current State

- PAPER-RS has aligned the manuscript and evidence docs to the EPF-FINAL
  evidence state.
- EPF-FINAL is candidate operational evidence only.
- Generated output-token logprobs are answer-side confidence diagnostics only.
- Fixed-target teacher-forced NLL is blocked.
- Fixed-target continuation scoring is blocked.
- WS5 human/external measurement validation is blocked because human/external
  gold labels are unavailable.
- Route 5 locked: true
- Route 8 locked: true
- Route 5 unlock: false
- Route 8 unlock: false
- Raw API responses stored: false
- Human/external gold labels available: false
- EPF-FINAL validates the paper: false

## Allowed Future Work

Future live-API-only packages may add operational diagnostics and reviewable
candidate artifacts under these constraints:

1. Use only the approved DashScope-compatible live API surface.
2. Treat generated output-token logprobs as answer-side confidence diagnostics
   only.
3. Treat constrained label generation as candidate proxy only.
4. Treat model-adjudicated weak labels as candidate operational evidence only.
5. Preserve replayable artifact evidence for auditability.
6. Store normalized outputs, hashes, provenance, and compact reports only.
7. Preserve `operational_utility_only/no_claim_upgrade`.

## Denied Future Work Without New Review

The following remain denied unless a separate future review explicitly changes
the evidence state:

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

## Development Sequence

1. Maintain claim guardrails and tests before adding any new live-API package.
2. Build projection-bundle and artifact-normalization work only if it can avoid
   raw API response storage.
3. Run backend audits as diagnostics, not bridge evidence.
4. Use judge or silver-label harnesses only as weak-source candidate evidence.
5. Keep operational replay expansion scoped and matched-budget.
6. Integrate manuscript wording only after guardrails confirm no denied claim is
   activated.

## Stop Conditions

Stop future work if a change would require raw API responses, secret logging,
non-approved backends, local HF, torch, transformers scorer, vLLM,
fixed-target teacher-forced NLL support, fixed-target continuation scoring
support, measurement validation, metric bridge support, calibrated proxy
support, V-information proxy support, paper-grade evidence, selector
superiority, Route 5 unlock, or Route 8 unlock.
