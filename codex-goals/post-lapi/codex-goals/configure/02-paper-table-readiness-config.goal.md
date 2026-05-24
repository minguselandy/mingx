# Goal ID: POST-2 / Paper table readiness package

## Objective

Create a post-LAPI paper table and experiment-readiness package. This goal is docs-only and must not run experiments.

## Hard constraints

- No live API calls.
- No new experiments.
- No claim upgrade.
- No Route 5 or Route 8 unlock.
- Do not stage unrelated leftovers.
- Do not use `git add -A`.

## Create or update

- `configs/post_lapi/post_lapi_table_manifest.yaml`
- `docs/paper/post-lapi-table-plan.md`
- `docs/paper/post-lapi-experiment-readiness-ledger.md`
- `docs/reviews/POST-LAPI-paper-readiness-review.md`

## Required paper tables

The table plan must include:
1. Backend capability / claim boundary
2. Artifact replay integrity
3. Matched-budget operational replay
4. Judge weak-evidence stability
5. Sufficiency / abstention regimes
6. Reprojection witness repair

Appendices:
- EPF-FINAL candidate package
- denied claims / claim ledger
- optional extraction quality audit
- related work gap matrix
- live API capability matrix

Each table entry must include:
- evidence source
- current completion status
- required next experiment, if any
- allowed claim
- denied claim
- whether live API is needed
- whether human labels are needed
- paper section target
- expected artifact location

## Allowed claim classes

- operational replay evidence
- candidate operational evidence
- model-adjudicated weak evidence
- sufficiency / abstention diagnostic
- replayable artifact evidence
- fail-closed bridge audit
- scoped operational improvement under matched budgets

## Denied claim classes

- fixed-target NLL support
- teacher-forced scoring support
- metric bridge support
- calibrated_proxy_supported
- vinfo_proxy_supported
- measurement validation
- human/external gold validation
- paper-grade evidence
- selector superiority
- global selector superiority
- Route 5 unlock
- Route 8 unlock

## Checks

```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
```

## Done condition

- Table plan, readiness ledger, and review doc are written.
- No live API calls are run.
- No claim upgrade is introduced.
- Do not commit automatically unless explicitly instructed after review.


Report format:
- Goal ID:
- Branch:
- HEAD:
- Changed files:
- Staged files:
- Checks run:
- Check results:
- Live API calls run: yes/no
- Raw API responses stored: yes/no
- Claim level:
- Claim upgrade introduced: yes/no
- Route 5 locked: yes/no
- Route 8 locked: yes/no
- Unrelated leftovers staged: yes/no
- Next recommended goal:
