# Reviewer Defense: Live-API-Only Evidence Boundary

Status: LAPI-8 reviewer-defense note
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This note answers expected reviewer questions about the live-API-only package.
It defends the paper's audit-first positioning without converting operational
diagnostics or candidate evidence into validation.

## Why no teacher-forced NLL?

The current live API exposes generated-token chat logprobs, not a fixed-target
teacher-forced scoring backend. Generated-token chat logprobs are answer-side
confidence diagnostics only. They score the model output path returned by the
chat API, not a predetermined target continuation under a fixed materialization
policy.

Generated-token chat logprobs are answer-side confidence diagnostics only.

Teacher-forced NLL support: false. Fixed-target continuation scoring support:
false. Because that backend is unavailable, the paper must not use live-API
logprobs as metric bridge support, calibrated proxy support, V-information
proxy support, paper evidence, Route 5 unlock, or Route 8 unlock.

## Why mention V-information?

The formal V-information objective is the anchor, not a current deployed measurement claim.
It defines the mathematical target for dispatch-time,
per-agent, token-budgeted context projection and explains why the selector
should care about information value rather than only lexical relevance.

The live-API package does not certify that the deployed proxy estimates formal
V-information. It keeps the formal objective, fixed-target scoring, operational
utility, heuristic selector behavior, and metric-claim level separate.

## What is the contribution without a bridge?

The contribution is a claim-gated operational audit surface for context
projection. The paper contributes a formal objective, conditional structural
theory, explicit bridge requirements, replayable operational artifacts,
fail-closed bridge diagnostics, and weak-evidence controls for candidate
diagnostics.

Without an accepted bridge, the empirical contribution is narrower: operational
diagnostics and candidate evidence that reveal backend limits, replay behavior,
judge stability, sufficiency failure modes, and extraction risk. That is useful
because it prevents an unsupported metric claim from being smuggled into the
paper by wording.

## Why use LLM judges?

LLM judges are weak-source candidate diagnostics. They can scale candidate
review, expose ambiguous cases, test order-swap or duplicate stability, and
prioritize human review. They are not human labels, external gold labels,
human-human agreement, kappa evidence, or measurement validation.

The safe claim is model-adjudicated weak evidence when stability gates pass.
When parse failures, order sensitivity, duplicate disagreement, or rubric
paraphrase instability appear, the claim is downgraded to ambiguous.

## Why not claim superior router/selector?

No superior router or selector claim is made. Route 2 HotpotQA replay is scoped
to named datasets, candidate pools, budgets, baselines, and operational metrics.
It is hard replay evidence for a matched-budget operational comparison only.

Global selector superiority, selector superiority, paper evidence, metric
bridge support, calibrated proxy support, V-information proxy support, and
measurement validation remain false. Route 5 locked: true. Route 8 locked:
true.

## Reviewer-Safe Summary

The paper is V-information-anchored but operational-only. The live-API package
is a backend-constrained audit and candidate-evidence layer: hard replay evidence
is separated from weak model-adjudicated evidence, and both are claim-gated.
The current claim level remains `operational_utility_only/no_claim_upgrade`.
