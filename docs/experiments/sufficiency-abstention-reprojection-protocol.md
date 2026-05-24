# Sufficiency Abstention Reprojection Protocol

This document defines the offline LAPI-5 framework for sufficiency classification, abstention diagnostics, and reprojection witness records. It is a framework and manifest layer only; it does not run a live API pilot.

## Claim Boundary

- Claim level: `sufficiency_abstention_diagnostic_only`
- Claim status: `operational_utility_only/no_claim_upgrade`
- Candidate operational evidence only: true
- Route 5 locked: true
- Route 8 locked: true
- Measurement validation claim: false
- Human/external gold label claim: false
- Live API call performed: false
- Provider body storage: false

All judge/model outputs remain candidate operational diagnostics. They are not measurement validation, truth validation, calibrated abstention, fixed-target NLL bridge evidence, paper-grade validation, Route 5 unlock evidence, or Route 8 unlock evidence.

## Regime Labels

- `sufficient_kept`: projected evidence was enough and the system answered.
- `sufficient_dropped`: omitted evidence appears necessary in hindsight and should become a reprojection candidate.
- `insufficient_and_answered`: projected evidence was not enough but the system answered.
- `insufficient_and_abstained`: projected evidence was not enough and the system abstained or escalated.

## Reprojection Triggers

- `sufficient_dropped`
- `insufficient_and_answered`
- `unknown_due_to_missing_context`
- `hallucination_risk`

## Controlled Replay

Reprojection witnesses hold the following controls fixed:

- Downstream prompt template hash
- Model snapshot
- Endpoint
- Thinking mode
- Decoding policy
- Token-budget accounting method

Witnesses record token-budget delta, selector change, context diff hash, before/after output hashes, repair status, and optional position-aware replay manifests.

## Pilot Readiness

The current readiness status is `offline_framework_ready_live_api_not_run`. A live API pilot remains out of scope until the earlier LAPI gates are accepted by the controller.
