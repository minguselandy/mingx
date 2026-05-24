# Mingx Paper Revision Codex Goals

This package contains paper-only Codex `/goal` documents for the final manuscript modification stage.

The project has already completed EPF, PAPER-RS, LAPI, POST-LAPI pilots, and SUB-stage synthesis. The next work is **not** experimentation. It is final manuscript revision, table/caption consistency, appendix/reproducibility packaging, reviewer-defense polish, and independent claim-boundary review.

## Recommended execution order

1. `PAPER-REV-0-baseline-and-scope-lock.goal.md`
2. `PAPER-REV-1-title-abstract-intro-contributions.goal.md`
3. `PAPER-REV-2-related-work-reframe.goal.md`
4. `PAPER-REV-3-methods-backend-artifact-claim-ledger.goal.md`
5. `PAPER-REV-4-evaluation-results-tables-captions.goal.md`
6. `PAPER-REV-5-limitations-conclusion-nonclaims.goal.md`
7. `PAPER-REV-6-appendix-artifact-index-reproducibility.goal.md`
8. `PAPER-REV-7-reviewer-defense-response-bank.goal.md`
9. `PAPER-REV-8-independent-final-claim-audit.goal.md`
10. `PAPER-REV-9-final-paper-readiness-summary.goal.md`

Optional only after the main sequence:
- `PAPER-REV-OPTIONAL-venue-formatting-no-claim-change.goal.md`

## How to use

From the repository root, run Codex and paste one goal at a time:

```text
/goal Read mingx_paper_revision_codex_goals/codex-goals/PAPER-REV-0-baseline-and-scope-lock.goal.md and execute exactly. Stop at the Done condition and report.
```

Do not execute later goals until the previous goal reports success or a clear `REQUEST_CHANGES` state.

## Global rule

Every goal preserves:

```text
operational_utility_only/no_claim_upgrade
```

No goal in this package authorizes live API calls, new experiments, Route 5 / Route 8 unlock, teacher-forced scoring, metric bridge claims, measurement validation claims, or selector superiority claims.
