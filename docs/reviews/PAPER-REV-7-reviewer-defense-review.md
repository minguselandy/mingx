# PAPER-REV-7 Reviewer Defense Review

Status: complete
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Scope

Reviewed and updated reviewer-defense material for the live-API operational audit paper:

- `docs/reviews/reviewer-defense-live-api-operational-paper.md`
- `docs/paper/submission-reviewer-package.md`
- `docs/paper/final-submission-nonclaims.md`
- `docs/paper/post-lapi-claim-boundary-summary.md`
- `docs/paper/final-reviewer-response-bank.md`

## Response-Bank Coverage

| required reviewer question | status |
|---|---|
| Why no fixed-target NLL bridge? | included |
| Why mention V-information at all? | included |
| Why use LLM judges? | included |
| Why is this not a context-compression paper? | included |
| Why not claim selector superiority? | included |
| What does the live-API-only constraint contribute scientifically? | included |
| Why are the POST-LAPI results useful if they are not validation? | included |
| Why no more experiments are recommended? | included |
| Why raw API responses are not stored? | included |
| What would be required for future claim upgrade? | included |

## Required Direct Answer

The supported live-API route exposes generated output-token diagnostics, not documented fixed-target continuation scoring. We therefore fail closed rather than relabel sampled chat logprobs as teacher-forced NLL.

## Claim-Boundary Audit

Every response preserves `operational_utility_only/no_claim_upgrade`. The response bank does not imply validation, metric bridge support, V-information proxy support, selector superiority, Route 5 unlock, Route 8 unlock, paper-grade evidence, human/external gold validation, or measurement validation.

## Verification

Passed:

- `git diff --check`
- `uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q`
- targeted response-bank and claim-boundary scans

No live API calls, new experiments, POST-3 through POST-7 reruns, silver-label scaling, raw artifact rewrites, staging, commits, or pushes were performed for this review.
