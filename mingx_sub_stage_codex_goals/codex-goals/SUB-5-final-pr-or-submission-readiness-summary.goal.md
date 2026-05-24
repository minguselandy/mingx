# Goal ID: SUB-5 / final PR or submission readiness summary

## Objective

Produce a final readiness summary for either a PR/merge package or paper-submission package after SUB-0 through SUB-4. This is docs-only.

## Hard constraints

- No live API calls.
- No new experiments.
- No claim upgrade.
- No Route 5 / Route 8 unlock.
- No `git add -A`.
- Do not stage unrelated leftovers.

## Create or update

- `docs/reviews/POST-LAPI-final-readiness-summary.md`
- `docs/paper/submission-readiness-checklist.md`
- `docs/paper/submission-artifact-index.md`

## Required readiness summary

Include:

- branch
- latest commit
- pushed remote status
- changed files since SUB-0
- committed/uncommitted status
- untracked leftovers summary
- evidence freeze manifest path
- checksums path
- main results tables path
- claim ledger path
- reviewer defense path
- independent review verdict
- gap-filling decision
- checks run and results
- claim level
- denied claims
- Route 5 / Route 8 status
- raw_response_stored status
- live API calls run during SUB goals

## Submission readiness checklist

Checklist items:

- [ ] Main results tables complete
- [ ] Evidence freeze ledger complete
- [ ] Claim boundary summary complete
- [ ] Independent claim review complete
- [ ] Reviewer defense complete
- [ ] Limitations complete
- [ ] Abstract claim-safe
- [ ] Conclusion claim-safe
- [ ] Artifact index complete
- [ ] Checks pass or documented
- [ ] No claim upgrade
- [ ] Route 5 / Route 8 locked
- [ ] No raw API response storage

## Artifact index

Index all paper-facing artifacts and reports:

- POST-3 judge stability artifacts
- POST-4 sufficiency / abstention artifacts
- POST-5 reprojection witness artifacts
- POST-6 operational replay artifacts
- POST-7 extraction audit artifacts
- evidence freeze manifest
- checksums
- table inputs
- review docs
- claim contracts

## Suggested PR title

```text
POST-LAPI: freeze operational evidence package and prepare claim-safe manuscript synthesis
```

## Suggested PR summary

Must state:

```text
This PR freezes and integrates the completed POST-LAPI candidate operational evidence package. It adds paper-ready results tables, claim-boundary summaries, reviewer defense materials, and final readiness artifacts. It does not introduce new live API calls, new experiments, fixed-target NLL support, metric bridge support, measurement validation, human/external gold validation, selector superiority, or Route 5 / Route 8 unlock.
```

## Checks

Run:

```bash
git status --short --untracked-files=all
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
python -m compileall cps tests scripts
```

## Done condition

- Final readiness summary created.
- Submission readiness checklist created.
- Submission artifact index created.
- Checks pass or failures are documented.
- No live API calls run.
- No new experiments started.
- No claim upgrade introduced.
