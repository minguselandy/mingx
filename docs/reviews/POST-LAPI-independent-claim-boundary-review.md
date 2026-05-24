# POST-LAPI Independent Claim-Boundary Review

## Verdict

Verdict: `ACCEPT_WITH_NOTES`

SUB-0 evidence freeze and SUB-1 manuscript integration preserve the current claim ceiling. SUB-3 can proceed if it keeps the same `operational_utility_only/no_claim_upgrade` boundary and treats every POST-LAPI result as operational audit, weak-evidence, scoped replay, or extraction-risk candidate evidence only.

## Reviewed Files

- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper/v12-evidence-ledger.md`
- `docs/paper/v12-manuscript-integration-checklist.md`
- `docs/paper/post-lapi-main-results-tables.md`
- `docs/paper/post-lapi-claim-boundary-summary.md`
- `docs/paper/post-lapi-evidence-freeze-ledger.md`
- `docs/reviews/POST-LAPI-evidence-freeze-review.md`
- `docs/reviews/POST-LAPI-manuscript-integration-review.md`
- Active POST-LAPI paper-facing context docs and guardrail tests used for the forbidden-claim grep:
  `docs/paper/live-api-operational-evaluation-section.md`,
  `docs/paper/v12-live-api-operational-paper-claim-table.md`,
  `docs/paper/related-work-live-api-operational-audit.md`,
  `docs/reviews/POST-LAPI-paper-readiness-review.md`,
  `docs/reviews/POST-LAPI-baseline-verification.md`,
  `docs/reviews/reviewer-defense-live-api-operational-paper.md`,
  `docs/experiments/POST-LAPI-*.md`,
  `tests/test_revised_framing_guardrails.py`,
  `tests/test_live_api_claim_contract.py`,
  and `tests/test_no_teacher_forced_claims_live_api_only.py`.

## Pass / Fail Checklist

| Check | Pass / fail | Notes |
|---|---|---|
| No measurement validation claim | PASS | Mentions are denials, false rows, limitations, or guardrail tests. |
| No human/external gold validation claim | PASS | SUB-0/SUB-1 state human/external gold labels are absent. |
| No fixed-target NLL claim | PASS | Fixed-target NLL remains unavailable/unsupported. |
| No teacher-forced scoring claim | PASS | Teacher-forced scoring and fixed-target continuation scoring remain denied. |
| No fixed-target continuation scoring claim | PASS | The live-API backend limitation is preserved. |
| No metric bridge support claim | PASS | Metric bridge support appears only as denied, absent, failed, or not established. |
| No `calibrated_proxy_supported` claim | PASS | The flag remains false or denied. |
| No `vinfo_proxy_supported` claim | PASS | The flag remains false or denied. |
| No paper-grade evidence claim | PASS | POST-LAPI evidence remains candidate-only; paper-grade evidence is denied. |
| No selector superiority claim | PASS | Selector superiority and global selector superiority are denied. |
| No global selector superiority claim | PASS | Global selector superiority is denied. |
| No Route 5 / Route 8 unlock | PASS | Review docs and table inputs keep Route 5 and Route 8 locked / unlocked=false. |
| Raw API responses not stored | PASS | SUB-0 manifest and tables record `raw_api_responses_stored=false`; SUB-1 docs retain `raw_response_stored=false`. |
| Model-adjudicated labels described as weak evidence only | PASS | POST-3 and manuscript integration use weak/model-adjudicated candidate evidence language. |
| Operational replay described as scoped only | PASS | POST-6 is scoped to named datasets, budgets, baselines, metrics, and materialization regime; oracle is non-deployable. |
| Extraction audit described as model-adjudicated extraction-risk evidence only | PASS | POST-7 is described as model-adjudicated extraction-risk evidence only. |
| Reprojection described as operational witness only | PASS | POST-5 is operational omitted-evidence / reprojection witness evidence only. |
| Generated-token chat logprobs described as output-side confidence diagnostics only | PASS | Manuscript integration states generated-token chat logprobs are operational confidence diagnostics only. |
| Oracle baselines marked `non_deployable_upper_bound` | PASS | POST-6 and Route 2 oracle rows retain `non_deployable_upper_bound`. |

## Required Corrections

None.

The forbidden-claim grep over active docs/tests found expected matches in denied-claim columns, false/locked rows, limitations, and tests that reject unsafe wording. No correction is required because the matches do not introduce positive claim upgrades.

## Verification Results

- `git diff --check`: PASS. Git reported only existing LF-to-CRLF working-copy warnings on edited docs.
- `uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q`: PASS, `20 passed`.
- Forbidden-claim grep over active docs/tests/scripts: PASS with contextual matches only. Matches were reviewed as denied-claim columns, false/locked rows, limitations, or guardrail tests; no positive claim upgrade was found.
- Secret/raw-response scan over SUB-2 review targets: PASS. No secret markers, raw response bodies, `raw_response_stored=true`, or `raw_api_responses_stored=true` were found.
- Index state: no staged files.
- Live API calls run during SUB-2: 0.
- New experiments run during SUB-2: 0.

## Residual Reviewer Risks

- POST-LAPI evidence remains weak and model-adjudicated where applicable; it is not human/external gold evidence.
- POST-6 operational replay remains scoped to the frozen named datasets, budgets, baselines, metrics, and materialization regime.
- POST-7 value-weighted loss proxy is candidate extraction-risk evidence only.
- Broad grep is intentionally noisy because denial tables and tests contain the forbidden terms; later reviews should preserve the denial context rather than removing guardrail language.
- Mixed untracked leftovers remain in the worktree and should stay unstaged unless a later goal explicitly includes them.

## Final Allowed Claim Level

`operational_utility_only/no_claim_upgrade`

Allowed POST-LAPI wording:

- POST-3 judge stability: weak/model-adjudicated candidate evidence only.
- POST-4 sufficiency / abstention: operational diagnostic candidate evidence only.
- POST-5 reprojection witness: operational omitted-evidence witness only.
- POST-6 operational replay expansion: scoped operational replay under matched budgets only.
- POST-7 extraction quality audit: model-adjudicated extraction-risk evidence only.
- Artifact hygiene: normalized artifact, checksum, storage-policy, and no-raw-response evidence only.

## Denied-Claim Summary

The following remain denied: measurement validation, human/external gold validation, fixed-target NLL support, teacher-forced scoring support, fixed-target continuation scoring support, metric bridge support, `calibrated_proxy_supported`, `vinfo_proxy_supported`, paper-grade evidence, selector superiority, global selector superiority, Route 5 unlock, and Route 8 unlock.

## SUB-3 Recommendation

SUB-3 can proceed.

Proceed only with the same claim ceiling, locked Route 5 / Route 8 status, no raw API response storage, and no conversion of POST-LAPI weak/model-adjudicated outputs into stronger evidence.
