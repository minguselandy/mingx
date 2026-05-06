# AGENTS.md

## Project identity

This repository uses the Lightweight Agentic Development Framework to manage Codex-assisted work through explicit phases, review gates, and local state files.

## Core principles

- Local-first.
- File-based.
- No auto-merge.
- No external services required for framework checks.
- No live LLM/API calls in tests.
- Human/operator gates stop automation.
- Scientific or evaluation claims must not be upgraded automatically.

## Workflow

1. Read this file.
2. Read `docs/phase-plan.md`.
3. Read `.state/codex/current_phase.json`.
4. Execute only the current phase.
5. Run focused checks.
6. Write a phase review under `docs/reviews/`.
7. Advance only if allowed by `scripts/framework_guard.py`.

## Verdict enum

- ACCEPT
- ACCEPT_WITH_NOTES
- REQUEST_CHANGES
- BLOCKED_OPERATOR_REQUIRED
- REJECT

## Auto-advance rules

Auto-advance is allowed only for offline, deterministic phases where the review accepts the phase, checks pass or skips are documented, and no human/operator, credential, external service, live API, license, security, or scientific-claim gate exists.
