# Goal ID: POST-8-CONFIG / Submission and reviewer package configuration

## Objective

Create the paper-facing submission and reviewer-defense package after POST-LAPI configs. This is docs-only and must not run experiments.

## Hard constraints

- No live API calls.
- No new experiments.
- No claim upgrade.
- No Route 5 or Route 8 unlock.
- Do not use validation language for operational evidence.
- Do not stage unrelated leftovers.

## Create or update

- `docs/paper/submission-claim-ledger.md`
- `docs/paper/submission-experiment-summary.md`
- `docs/paper/submission-limitations.md`
- `docs/reviews/reviewer-defense-live-api-operational-paper.md`
- `docs/paper/final-abstract-claim-safe.md`
- `docs/paper/final-conclusion-claim-safe.md`

## Required reviewer questions

Answer:
- Why no fixed-target NLL bridge?
- Why mention V-information?
- Why use LLM judges?
- Why not claim selector superiority?
- Why is this not just another RAG compressor?
- What does live-API-only constraint contribute scientifically?
- Why are EPF-FINAL silver labels candidate-only?
- Why are Route 5 and Route 8 still locked?

## Required stance

Use language equivalent to:
- We do not relabel generated-token chat logprobs as teacher-forced NLL.
- We do not claim V-information verification.
- We do not claim measurement validation.
- The contribution is a fail-closed, replayable, claim-gated operational audit framework for dispatch-time evidence selection.

## Required section names

- Operational evaluation and weak-evidence diagnostics
- Backend capability and claim boundary
- Replayable artifact interface
- Sufficiency, abstention, and reprojection witnesses
- Limitations and non-claims

## Checks

```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
```

## Done condition

- Submission claim ledger is written.
- Experiment summary is written.
- Limitations are claim-safe.
- Reviewer-defense doc is written.
- Claim-safe abstract and conclusion drafts are written.
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
