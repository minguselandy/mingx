# Goal ID: SUB-4 / optional gap-filling decision gate

## Objective

Decide whether any additional experiment is needed after SUB-0 through SUB-3. This goal must not run new experiments. It only produces a recommendation.

## Hard constraints

- No live API calls.
- No new experiments.
- No claim upgrade.
- No Route 5 / Route 8 unlock.
- No `git add -A`.
- Do not stage unrelated leftovers.

## Inputs

Review:

- `docs/paper/post-lapi-main-results-tables.md`
- `docs/paper/submission-experiment-summary.md`
- `docs/paper/submission-limitations.md`
- `docs/reviews/POST-LAPI-independent-claim-boundary-review.md`
- `docs/reviews/reviewer-defense-live-api-operational-paper.md`
- `docs/reviews/POST-LAPI-submission-package-review.md`

## Create

- `docs/reviews/POST-LAPI-gap-filling-decision.md`

## Decision options

Choose exactly one:

1. `NO_MORE_EXPERIMENTS_RECOMMENDED`
2. `OPTIONAL_POSITION_AWARE_REPROJECTION_ONLY`
3. `OPTIONAL_SECOND_TASK_SUFFICIENCY_ONLY`
4. `OPTIONAL_HUMAN_SENTINEL_AUDIT_ONLY`
5. `BLOCK_SUBMISSION_UNTIL_CORRECTED`

## Decision criteria

Recommend no more experiments if:

- POST-3 through POST-7 are summarized clearly.
- claim boundaries are clean.
- reviewer defense covers missing NLL bridge.
- main results tables are complete.
- no table has an unresolved artifact or sample-count gap.

Recommend optional position-aware reprojection only if:

- SUB-3 reviewer package identifies materialization order as the only weak spot.
- Existing POST-5 cases are enough to run a small controlled position-order test later.
- User explicitly approves a future live API or offline replay run.

Recommend optional second-task sufficiency only if:

- HotpotQA-only evidence is judged too narrow.
- FEVER-style packets are already configured.
- User explicitly approves a future run.

Recommend optional human sentinel audit only if:

- human annotation resources exist.
- the goal is a future stronger evidence lane.
- no current doc suggests current evidence is human-validated.

Block submission only if:

- active docs claim validation, metric bridge, selector superiority, or Route unlock;
- core results tables cannot be traced to artifacts;
- raw response storage policy is violated.

## Done condition

- Decision doc written.
- Exactly one decision option selected.
- No live API calls run.
- No new experiments started.
- No claim upgrade introduced.
