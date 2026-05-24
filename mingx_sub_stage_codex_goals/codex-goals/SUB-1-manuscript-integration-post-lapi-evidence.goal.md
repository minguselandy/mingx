# Goal ID: SUB-1 / manuscript integration of POST-LAPI operational evidence

## Objective

Integrate the frozen POST-LAPI candidate operational evidence package into manuscript-facing docs. This is docs-only. Do not run experiments.

## Hard constraints

- No live API calls.
- No new experiments.
- No claim upgrade.
- No Route 5 or Route 8 unlock.
- No validation language.
- No metric bridge support language.
- No selector-superiority language.
- No `git add -A`.
- Do not stage unrelated leftovers.

## Required framing

The manuscript must present the empirical section as:

```text
Operational evaluation and weak-evidence diagnostics
```

Do not use:

```text
Validation
```

as the section title for current evidence.

## Update

- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper/v12-evidence-ledger.md`
- `docs/paper/v12-manuscript-integration-checklist.md`
- `docs/paper/post-lapi-main-results-tables.md`
- `docs/paper/post-lapi-claim-boundary-summary.md`
- `docs/reviews/POST-LAPI-manuscript-integration-review.md`

## Required manuscript changes

1. Add POST-LAPI result summaries:
   - POST-3 Judge stability
   - POST-4 Sufficiency / abstention
   - POST-5 Reprojection witness
   - POST-6 Operational replay expansion
   - POST-7 Extraction quality audit
   - Artifact hygiene / raw-response policy

2. For every result, state:
   - allowed claim
   - denied claim
   - evidence tier
   - live API call count
   - human label status
   - metric bridge status
   - Route 5 / Route 8 status
   - raw_response_stored status

3. Keep conclusion:
   - `operational_utility_only/no_claim_upgrade`

4. Explicitly deny:
   - measurement validation
   - human/external gold validation
   - fixed-target NLL support
   - teacher-forced scoring support
   - metric bridge support
   - `calibrated_proxy_supported`
   - `vinfo_proxy_supported`
   - paper-grade evidence
   - selector superiority
   - global selector superiority

5. State that:
   - generated-token chat logprobs are operational confidence diagnostics only;
   - model-adjudicated labels are weak evidence only;
   - operational replay is scoped to named datasets, budgets, baselines, metrics, and materialization regime;
   - extraction audit is model-adjudicated extraction-risk evidence only;
   - reprojection witness is operational omitted-evidence evidence only.

## Required review doc

Create `docs/reviews/POST-LAPI-manuscript-integration-review.md` with:

- changed files
- section-level summary
- evidence integrated
- claim boundary
- forbidden claims checked
- remaining manuscript gaps
- recommendation for SUB-2 independent review

## Checks

Run:

```bash
git diff --check
uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q
```

## Done condition

- Manuscript docs integrate POST-LAPI results.
- Evidence ledger includes POST-3 through POST-7.
- Results tables cross-reference the manuscript sections.
- No claim upgrade introduced.
- No live API calls run.
