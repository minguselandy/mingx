# PAPER-REV-5 Limitations and Conclusion Review

Status: complete
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Scope

Reviewed and updated the PAPER-REV-5 limitations, conclusion, nonclaims, and claim-ledger surfaces:

- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper/submission-limitations.md`
- `docs/paper/final-submission-nonclaims.md`
- `docs/paper/final-conclusion-claim-safe.md`
- `docs/paper/submission-conclusion-claim-safe.md`
- `docs/paper/submission-claim-ledger.md`

## Required Posture

The present evidence is operational rather than validating. The contribution is a replayable, claim-gated operational audit framework for dispatch-time evidence projection under live-API constraints.

## Limitations Audit

| requirement | status |
|---|---|
| No fixed-target teacher-forced NLL | explicit |
| No fixed-target continuation scoring | explicit |
| Generated-token logprobs are output-side diagnostics only | explicit |
| No metric bridge support | explicit |
| No calibrated proxy support | explicit |
| No V-information proxy support | explicit |
| No human/external gold validation | explicit |
| No measurement validation | explicit |
| No selector superiority | explicit |
| Operational replay scoped by dataset, budgets, baselines, metrics, and materialization/evaluator regime | explicit |
| Extraction audit is model-adjudicated extraction-risk evidence only | explicit |
| Judge outputs are weak evidence only | explicit |

## Nonclaim Placement

Nonclaims are now duplicated in reviewer-visible locations:

- `docs/paper/final-submission-nonclaims.md`
- `docs/paper/submission-limitations.md`
- `docs/paper/submission-claim-ledger.md`
- `docs/archive/context_projection_fixed_v12.md`

## Verification

Passed:

- `git diff --check`
- `uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q`
- targeted nonclaim and claim-boundary scans

No live API calls, new experiments, POST-3 through POST-7 reruns, silver-label scaling, raw artifact rewrites, staging, commits, or pushes were performed for this review.
