# PAPER-REV-4 Evaluation Table Review

Status: complete
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Scope

Reviewed and updated the PAPER-REV-4 evaluation/table surfaces:

- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper/post-lapi-main-results-tables.md`
- `docs/paper/submission-experiment-summary.md`
- `docs/paper/post-lapi-evidence-freeze-ledger.md`

`docs/paper/final-submission-package-map.md` is absent, so no update was made there.

## Required Table Set

Caption: Evidence tier: review summary over backend capability boundary, model-adjudicated weak evidence, sufficiency-abstention diagnostics, candidate operational evidence, matched-budget operational replay only, extraction-risk diagnostics, and replayable artifact evidence. Allowed claim: operational diagnostics under `operational_utility_only/no_claim_upgrade` only. Denied claim: fixed-target teacher-forced NLL support, fixed-target continuation scoring support, metric bridge support, measurement validation, human/external gold validation, paper-grade evidence, selector superiority, global selector superiority, Route 5 unlock, and Route 8 unlock. Human labels present: false. Metric bridge present: false. Route 5 / Route 8: locked / locked.

| Table requirement | Status | Frozen fact used | Claim label |
|---|---|---|---|
| Backend capability and claim boundary | included | generated-token logprobs only; no fixed-target scoring backend; 0 synthesis calls | backend-constrained operational diagnostics only |
| POST-3 judge stability | included | 240 live API calls; 30 examples; 240 normalized rows; duplicate agreement `0.9833`; order-swap agreement `0.9833`; rubric paraphrase agreement `0.9667` | model-adjudicated weak diagnostics only |
| POST-4 sufficiency / abstention | included | 50 final normalized rows | sufficiency-abstention diagnostics only |
| POST-5 reprojection witness | included | 26 rows; repair candidate rate `0.576923`; label change rate `0.576923`; unsupported-to-supported rate `0.576923`; parse failed rate `0.0` | candidate operational evidence only |
| POST-6 matched-budget operational replay | included | 2,000 replay records; 200 HotpotQA candidate pools; budgets `512` and `1024`; 0 live API calls; oracle `non_deployable_upper_bound` | scoped operational replay only |
| POST-7 extraction quality audit | included | 100 records; 10 records per stratum; value-weighted loss proxy `0.197403` | extraction-risk diagnostics only |
| Artifact hygiene and evidence freeze | included | JSON/JSONL checks, checksums, scans, and `raw_response_stored=false` | replayable artifact evidence only |

## Caption Audit

Every PAPER-REV-4 table caption now states:

- evidence tier
- allowed claim
- denied claim
- human labels present: false
- metric bridge present: false
- Route 5 / Route 8: locked / locked

The captions state denied claims as denials, not as positive validation or selector-superiority claims.

## Verification

Passed:

- `git diff --check`
- `uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q`
- Targeted caption/fact scans

No live API calls, new experiments, POST-3 through POST-7 reruns, silver-label scaling, artifact rewrites, staging, commits, or pushes were performed for this review.
