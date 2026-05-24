# Mingx SUB-Stage Codex Goal Pack

This package contains Codex `/goal` documents for the paper-synthesis phase after the completed POST-LAPI candidate operational evidence package.

The package assumes:

- EPF / PAPER-RS / LAPI are complete.
- POST-0 through POST-8-CONFIG are complete.
- POST-3 through POST-7 pilots are complete and pushed.
- Current evidence is useful for an **operational audit / weak evidence / replay / extraction-risk candidate package**.
- Current claim remains `operational_utility_only/no_claim_upgrade`.

## Goal order

Run the goals in this order:

1. `SUB-0-evidence-freeze-and-paper-synthesis-baseline.goal.md`
2. `SUB-1-manuscript-integration-post-lapi-evidence.goal.md`
3. `SUB-2-independent-claim-boundary-review.goal.md`
4. `SUB-3-submission-reviewer-package.goal.md`
5. `SUB-4-gap-filling-decision-gate.optional.goal.md`
6. `SUB-5-final-pr-or-submission-readiness-summary.goal.md`

## Recommended Codex usage

From repo root:

```text
/goal Read mingx_sub_stage_codex_goals/codex-goals/SUB-0-evidence-freeze-and-paper-synthesis-baseline.goal.md and execute exactly. Stop at the Done condition and report.
```

Then proceed to the next goal only after reviewing the previous report.

## Important

These goals are intentionally **no-live-API** goals. They are for freezing evidence, creating paper-ready tables, integrating the manuscript, auditing claim boundaries, and preparing the reviewer/submission package.

Do not run new experiments unless `SUB-4` explicitly concludes that a concrete evidence gap exists and the user separately approves a new pilot.
