# Goal ID: SUB-2 / independent claim-boundary review for POST-LAPI submission package

## Objective

Review the POST-LAPI evidence freeze and manuscript integration for claim-boundary violations. Do not modify code unless docs-only corrections are needed.

## Hard constraints

- No live API calls.
- No new experiments.
- No claim upgrade.
- No Route 5 / Route 8 unlock.
- No `git add -A`.
- Do not stage unrelated leftovers.

## Review targets

- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper/v12-evidence-ledger.md`
- `docs/paper/v12-manuscript-integration-checklist.md`
- `docs/paper/post-lapi-main-results-tables.md`
- `docs/paper/post-lapi-claim-boundary-summary.md`
- `docs/paper/post-lapi-evidence-freeze-ledger.md`
- `docs/reviews/POST-LAPI-evidence-freeze-review.md`
- `docs/reviews/POST-LAPI-manuscript-integration-review.md`
- any POST-LAPI paper-facing docs created in SUB-0 or SUB-1

## Create

- `docs/reviews/POST-LAPI-independent-claim-boundary-review.md`

## Review checklist

Verify:

- no measurement validation claim
- no human/external gold validation claim
- no fixed-target NLL claim
- no teacher-forced scoring claim
- no fixed-target continuation scoring claim
- no metric bridge support claim
- no `calibrated_proxy_supported` claim
- no `vinfo_proxy_supported` claim
- no paper-grade evidence claim
- no selector superiority claim
- no global selector superiority claim
- no Route 5 / Route 8 unlock
- raw API responses not stored
- model-adjudicated labels described as weak evidence only
- operational replay described as scoped only
- extraction audit described as model-adjudicated extraction-risk evidence only
- reprojection described as operational witness only
- generated-token chat logprobs described as output-side confidence diagnostics only
- oracle baselines marked `non_deployable_upper_bound`

## Verdict options

Choose one:

- `ACCEPT`
- `ACCEPT_WITH_NOTES`
- `REQUEST_CHANGES`
- `BLOCK`

## Required content

The review doc must include:

- verdict
- reviewed files
- pass/fail checklist
- required corrections, if any
- residual reviewer risks
- final allowed claim level
- denied-claim summary
- whether SUB-3 can proceed

## Checks

Run:

```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
```

Run a forbidden-claim grep over active docs/tests/scripts, excluding `.git`, `.codex`, raw artifacts, and unrelated leftovers.

## Done condition

- Review doc written.
- Verdict assigned.
- Required corrections listed or explicitly marked none.
- No live API calls run.
- No claim upgrade introduced.
