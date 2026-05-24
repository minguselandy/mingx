# PAPER-REV-2 Related Work Review

Status: complete
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Scope

PAPER-REV-2 reframes related work so the paper is positioned as an
audit-first operational diagnostic framework, not as a stronger compressor,
adaptive router, or benchmark. This was a paper-only edit. No live API calls,
new experiments, POST-3 through POST-7 reruns, silver-label scaling, route
unlocks, raw API storage, staging, or excluded-leftover changes were made.

## Files Reviewed

| file | status | action |
|---|---|---|
| `docs/archive/context_projection_fixed_v12.md` | present | updated Section 7 into the required five-lane related-work structure |
| `docs/paper/related-work-live-api-operational-reframe.md` | absent | recorded as absent; closest manuscript-facing equivalent is Section 7 of `docs/archive/context_projection_fixed_v12.md` |
| `docs/paper/submission-experiment-summary.md` | present | reviewed; already states frozen operational-only evidence and backend boundary |
| `docs/reviews/reviewer-defense-live-api-operational-paper.md` | present | updated compressor/router defense to match the related-work reframe |

## Required Structure

Section 7 now uses the required organization:

1. Context compression and adaptive retrieval comparators.
2. Sufficiency, abstention, and long-context diagnostics.
3. V-information and budgeted subset-selection theory.
4. LLM-as-judge and weak supervision.
5. Runtime audit artifacts and claim gates.

The manuscript includes the required stance:

```text
We do not claim to be the first context compressor, adaptive RAG router, sufficiency evaluator, automated judge pipeline, or weak-supervision system. Our contribution is a claim-gated operational audit framework for dispatch-time evidence projection under live-API constraints.
```

## Nonclaims Preserved

The related-work reframe states that compression, pruning, routing, and
adaptive retrieval are crowded adjacent literatures and are not the novelty
claim. It positions sufficiency / abstention as the closest positive
experimental lane, but only as operational diagnostics. It keeps V-information
as a formal anchor while stating that the current experiments do not estimate
deployed V-information. It frames LLM judges and weak supervision as noisy
operational signals rather than stronger measurement evidence.

The related-work and reviewer-defense edits preserve these denied claims:

- measurement validation,
- human/external gold validation,
- fixed-target teacher-forced NLL support,
- fixed-target continuation scoring support,
- teacher-forced scoring support,
- metric bridge support,
- `calibrated_proxy_supported`,
- `vinfo_proxy_supported`,
- paper-grade evidence / paper evidence,
- deployed V-information verification,
- selector superiority,
- global selector superiority,
- Route 5 unlock,
- Route 8 unlock.

## Checks

Recorded after execution:

| command | result |
|---|---|
| `git diff --check` | passed; Git reported LF-to-CRLF working-copy warnings for dirty Markdown files only |
| `uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q` | passed: `20 passed` |
| related-work structure scan | passed: all five required lanes, required stance sentence, live-API backend boundary, and audit-artifact terms present |
| related-work superiority scan | passed: no positive compressor-superiority or selector-superiority phrases found |

## Verdict

PAPER-REV-2 related work no longer invites a selector-superiority or
compressor-superiority reading. It makes the live-API constraint and
weak-evidence posture explicit under `operational_utility_only/no_claim_upgrade`.
