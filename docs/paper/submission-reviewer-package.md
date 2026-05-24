# Submission Reviewer Package

Status: PAPER-REV-7 reviewer package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This package map points reviewers to the claim-safe defense materials for the live-API operational audit paper. It does not add evidence, run experiments, store raw API responses, unlock Route 5, unlock Route 8, or upgrade claims.

## Reviewer Defense Materials

| material | purpose | boundary |
|---|---|---|
| `docs/paper/final-reviewer-response-bank.md` | Complete ten-question reviewer response bank | preserves `operational_utility_only/no_claim_upgrade` in every answer |
| `docs/reviews/reviewer-defense-live-api-operational-paper.md` | Longer reviewer-defense note | operational audit / diagnostic only |
| `docs/paper/final-submission-nonclaims.md` | Reviewer-visible nonclaims | denied claims stay denied |
| `docs/paper/post-lapi-claim-boundary-summary.md` | POST-LAPI claim-boundary summary | Route 5 / Route 8 locked |
| `docs/paper/final-submission-artifact-index.md` | Appendix artifact map | replayable artifact evidence only |

## Required NLL Bridge Answer

The supported live-API route exposes generated output-token diagnostics, not documented fixed-target continuation scoring. We therefore fail closed rather than relabel sampled chat logprobs as teacher-forced NLL.

## Reviewer-Safe Boundary

- Current claim: `operational_utility_only/no_claim_upgrade`.
- Route 5: locked.
- Route 8: locked.
- Raw API responses stored: false.
- Metric bridge support: denied.
- V-information proxy support: denied.
- Measurement validation: denied.
- Selector superiority: denied.
- Claim upgrade introduced: false.
