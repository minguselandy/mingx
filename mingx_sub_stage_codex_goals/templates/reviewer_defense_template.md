# Reviewer Defense Package

## Core one-paragraph defense

This paper studies dispatch-time evidence projection as an audit-first operational problem in a live-API setting. V-information is used as a formal anchor for usable information, but the current backend does not provide true fixed-target teacher-forced NLL, so the empirical claims are intentionally operational-only. We report replayable artifacts, weak model-adjudicated evidence, sufficiency / abstention diagnostics, reprojection witnesses, and scoped matched-budget replay outcomes under fail-closed claim gates.

## Why no NLL bridge?

The supported live API exposes generated-token chat logprobs, which are output-side diagnostics. It does not provide the fixed-target continuation scoring needed for teacher-forced NLL. The paper therefore refuses to relabel generated-token logprobs as metric-bridge evidence.

## Why mention V-information?

V-information defines the formal target: preserve usable information for a bounded downstream predictor. The current evidence package does not validate V-information; it uses the formal object to organize an operational audit protocol.

## Why use LLM judges?

LLM judges are treated as weak noisy annotators. Order swaps, duplicate judging, and rubric paraphrases support stability diagnostics, not human-equivalent validation.

## Why not claim selector superiority?

The matched-budget replay evidence is regime-scoped and operational. It supports scoped comparisons under fixed budgets and materialization conditions, not global selector superiority.

## Why is this not just another compressor/router?

Compression and routing prior art optimizes token efficiency and answer accuracy. This paper contributes a claim-gated audit surface: selected and excluded evidence IDs, materialization order, budget witnesses, claim ledgers, weak-evidence stability controls, sufficiency/abstention diagnostics, and reprojection witnesses.
