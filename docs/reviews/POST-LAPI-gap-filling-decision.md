# POST-LAPI Gap-Filling Decision

Status: SUB-4 optional gap-filling decision gate
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Decision

Decision option selected:

```text
NO_MORE_EXPERIMENTS_RECOMMENDED
```

The current POST-LAPI evidence package is submission-ready as operational audit / weak-evidence / replay / extraction-risk candidate evidence. No additional experiment is recommended for the current submission boundary.

## Source Inputs Reviewed

- `docs/paper/post-lapi-main-results-tables.md`
- `docs/paper/submission-experiment-summary.md`
- `docs/paper/submission-limitations.md`
- `docs/reviews/POST-LAPI-independent-claim-boundary-review.md`
- `docs/reviews/reviewer-defense-live-api-operational-paper.md`
- `docs/reviews/POST-LAPI-submission-package-review.md`

## Decision Criteria Audit

| criterion | result | evidence |
|---|---|---|
| POST-3 through POST-7 summarized clearly | PASS | Main results tables and submission experiment summary cover judge stability, sufficiency / abstention, reprojection witness, operational replay, extraction audit, and JSON / JSONL hygiene. |
| Claim boundaries clean | PASS | SUB-2 independent review verdict is `ACCEPT_WITH_NOTES`; required corrections are none; final allowed claim level remains `operational_utility_only/no_claim_upgrade`. |
| Reviewer defense covers missing NLL bridge | PASS | Reviewer defense answers "Why no NLL bridge?" and states generated-token chat logprobs are not fixed-target teacher-forced NLL. |
| Main results tables complete | PASS | Tables T1 through T8 include evidence source, sample / row / call count, primary metric, allowed claim, denied claim, evidence tier, live API call count, human label status, metric bridge status, Route 5 / Route 8 status, and `raw_response_stored`. |
| No unresolved artifact or sample-count gap | PASS | POST-3 through POST-7 row/call counts are explicit; JSON / JSONL hygiene reports 27 JSON files, 5 JSONL files, and 2,416 JSONL rows; POST-6 oracle remains `non_deployable_upper_bound`. |
| Raw response storage policy preserved | PASS | Main tables and SUB-2 review keep raw response storage false. |
| Route locks preserved | PASS | Route 5 and Route 8 remain locked / unlocked=false. |

## Optional Gap-Filling Options Considered

| option | decision | reason |
|---|---|---|
| `OPTIONAL_POSITION_AWARE_REPROJECTION_ONLY` | not recommended now | SUB-3 does not identify materialization order as the only material weak spot for the current submission boundary. |
| `OPTIONAL_SECOND_TASK_SUFFICIENCY_ONLY` | not recommended now | The current package is submission-ready as scoped operational evidence; adding a second task would be a future expansion, not a prerequisite for this boundary. |
| `OPTIONAL_HUMAN_SENTINEL_AUDIT_ONLY` | not recommended now | Human annotation would support a future stronger evidence lane, but the current docs do not claim human/external gold evidence and do not need that lane for the operational-only submission boundary. |
| `BLOCK_SUBMISSION_UNTIL_CORRECTED` | not selected | Active docs do not claim measurement validation, metric bridge support, selector superiority, or route unlock; core results tables trace to artifacts; raw response storage policy remains intact. |

## Boundary Conditions

- Live API calls run during SUB-4: 0.
- New experiments started during SUB-4: 0.
- Gap-filling work implemented during SUB-4: none.
- Claim upgrade introduced during SUB-4: no.
- Final claim level: `operational_utility_only/no_claim_upgrade`.
- Route 5: locked.
- Route 8: locked.

## Denied Claims

The following remain denied: fixed-target teacher-forced NLL, teacher-forced scoring support, fixed-target continuation scoring support, metric bridge support, `calibrated_proxy_supported`, `vinfo_proxy_supported`, measurement validation, human/external gold validation, paper-grade evidence, selector superiority, global selector superiority, Route 5 unlock, and Route 8 unlock.

## Recommendation

Proceed without a gap-filling experiment. The next step can be SUB-5 final readiness summary or packaging work, provided it preserves the same claim ceiling, route locks, raw-response policy, and operational audit / weak-evidence / replay / extraction-risk candidate-evidence framing.
