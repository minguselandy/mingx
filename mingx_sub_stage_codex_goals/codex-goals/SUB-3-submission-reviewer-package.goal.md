# Goal ID: SUB-3 / submission and reviewer defense package

## Objective

Create a paper-submission and reviewer-defense package from the frozen POST-LAPI evidence. This is docs-only.

## Hard constraints

- No live API calls.
- No new experiments.
- No claim upgrade.
- No Route 5 / Route 8 unlock.
- No validation language beyond explicit denials.
- No metric bridge support language.
- No selector-superiority language.
- No `git add -A`.
- Do not stage unrelated leftovers.

## Create or update

- `docs/paper/submission-claim-ledger.md`
- `docs/paper/submission-experiment-summary.md`
- `docs/paper/submission-limitations.md`
- `docs/paper/submission-abstract-claim-safe.md`
- `docs/paper/submission-conclusion-claim-safe.md`
- `docs/reviews/reviewer-defense-live-api-operational-paper.md`
- `docs/reviews/POST-LAPI-submission-package-review.md`

## Required sections

### 1. Core positioning

State that the paper is:

```text
V-information anchored,
live-API-only,
claim-gated,
operational audit / diagnostic paper.
```

State that it is not:

```text
compression paper,
router paper,
validation paper,
calibrated proxy paper,
selector superiority paper.
```

### 2. Abstract-safe language

Must include:

- dispatch-time evidence projection
- live-agent / live-API setting
- formal V-information anchor
- operational-only evidence
- weak model-adjudicated diagnostics
- sufficiency / abstention
- reprojection witness
- replayable artifact evidence
- fail-closed claim gates

Must deny:

- fixed-target teacher-forced NLL
- metric bridge support
- V-information proxy validation
- measurement validation
- human/external gold validation
- selector superiority

### 3. Main results summary

Summarize:

- POST-3 judge stability
- POST-4 sufficiency / abstention
- POST-5 reprojection witness
- POST-6 operational replay
- POST-7 extraction audit
- JSON / JSONL validation and scan hygiene

### 4. Reviewer Q&A

Must answer:

- Why no NLL bridge?
- Why mention V-information?
- Why use LLM judges?
- Why not claim selector superiority?
- Why is this not just another compressor/router?
- What does the live-API-only constraint contribute scientifically?
- Why are artifacts a contribution rather than just logs?
- Why is extraction quality separate from selector quality?

### 5. Limitations

Must include:

- no true fixed-target teacher-forced NLL
- no metric bridge
- no measurement validation
- no human/external gold validation
- LLM judges are weak sources
- operational replay is scoped
- extraction audit is model-adjudicated only
- artifacts are replay/audit evidence, not validation
- Route 5 / Route 8 locked

## Suggested conclusion sentence

Use or adapt:

```text
The current evidence package is operational rather than validating: under the supported live API, we do not establish a fixed-target teacher-forced bridge from dispatch-time projection to V-information or calibrated answer likelihood. Instead, we contribute a replayable, claim-gated audit framework that isolates when dispatch-time evidence projection helps, when it should abstain, and how those outcomes can be reproduced and inspected.
```

## Checks

Run:

```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
```

## Done condition

- Submission claim ledger created.
- Submission experiment summary created.
- Limitations doc created.
- Claim-safe abstract and conclusion created.
- Reviewer defense doc created.
- Submission package review doc created.
- No live API calls run.
- No claim upgrade introduced.
