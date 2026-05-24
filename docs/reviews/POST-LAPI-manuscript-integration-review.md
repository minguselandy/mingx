# POST-LAPI Manuscript Integration Review

Status: SUB-1 manuscript integration review
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Changed Files

- `docs/archive/context_projection_fixed_v12.md`
- `docs/paper/v12-evidence-ledger.md`
- `docs/paper/v12-manuscript-integration-checklist.md`
- `docs/paper/post-lapi-main-results-tables.md`
- `docs/paper/post-lapi-claim-boundary-summary.md`
- `docs/reviews/POST-LAPI-manuscript-integration-review.md`

## Section-Level Summary

- Manuscript section `Operational evaluation and weak-evidence diagnostics` now integrates the frozen POST-LAPI result summaries.
- Evidence ledger now includes POST-3 through POST-7 plus artifact hygiene / raw-response policy.
- Main results tables now cross-reference the manuscript section and state evidence tier, live API call count, human label status, metric bridge status, Route 5 / Route 8 status, and `raw_response_stored` status.
- Claim-boundary summary now records the SUB-1 integration boundary and preserves the no-upgrade conclusion.
- Manuscript checklist now records the SUB-1 source artifacts, required result summaries, and denied upgrades for later review.

## Evidence Integrated

| Result | Integrated evidence | Live API calls | Evidence tier |
|---|---|---:|---|
| POST-3 judge stability | duplicate agreement `0.9833`; order-swap agreement `0.9833`; rubric paraphrase agreement `0.9667`; 30 examples / 240 normalized rows | 240 | weak/model-adjudicated candidate evidence |
| POST-4 sufficiency / abstention | gate `sufficiency_abstention_candidate_ready`; 50 normalized rows; 50 final artifact calls / 100 total turn calls | 50 final artifact calls / 100 total turn calls | operational diagnostic candidate evidence |
| POST-5 reprojection witness | repair candidate rate `0.576923`; label change rate `0.576923`; unsupported-to-supported rate `0.576923`; parse failed rate `0.0`; 26 normalized rows | 26 | operational omitted-evidence evidence only |
| POST-6 operational replay expansion | 2,000 replay records; 200 candidate pools; budgets `512` and `1024`; oracle `non_deployable_upper_bound` | 0 | scoped operational replay evidence only |
| POST-7 extraction quality audit | 100 extraction audit records; 10 per stratum; value-weighted loss proxy `0.197403`; gate `post7_extraction_quality_audit_completed` | 100 | model-adjudicated extraction-risk evidence only |
| Artifact hygiene / raw-response policy | 27 JSON files; 5 JSONL files; 2,416 JSONL rows; secret scan passed; raw-response-storage scan passed; forbidden-path scan passed | 0 during SUB-0/SUB-1 synthesis | reproducibility and storage-policy evidence only |

## Claim Boundary

- Conclusion: `operational_utility_only/no_claim_upgrade`.
- Route 5 status: locked.
- Route 8 status: locked.
- Human/external gold labels: absent.
- Metric bridge: absent.
- Raw API responses stored: false.
- Live API calls run during SUB-1: 0.
- New experiments run during SUB-1: 0.

Generated-token chat logprobs are operational confidence diagnostics only. Model-adjudicated labels are weak evidence only. Operational replay is scoped to named datasets, budgets, baselines, metrics, and materialization regime. Extraction audit is model-adjudicated extraction-risk evidence only. Reprojection witness is operational omitted-evidence evidence only.

## Forbidden Claims Checked

The integration explicitly denies:

- fixed-target NLL support;
- teacher-forced scoring support;
- metric bridge support;
- `calibrated_proxy_supported`;
- `vinfo_proxy_supported`;
- measurement validation;
- human/external gold validation;
- paper-grade evidence;
- selector superiority;
- global selector superiority;
- Route 5 unlock;
- Route 8 unlock.

The denied-claim terms may appear in boundary tables and checklist guardrails as denials only. They are not positive claims.

## Remaining Manuscript Gaps

- SUB-1 does not perform an independent claim-boundary review.
- SUB-1 does not create a reviewer defense package.
- SUB-1 does not add human sentinel audit evidence.
- SUB-1 does not add a fixed-target teacher-forced scoring backend, metric bridge, calibrated proxy, V-information proxy, or Route 5 / Route 8 unlock.
- SUB-1 does not rerun POST-3 through POST-7 artifacts; it integrates the frozen SUB-0 outputs only.

## Recommendation for SUB-2 Independent Review

Proceed to SUB-2 as an independent claim-boundary review over the manuscript integration. SUB-2 should verify that all POST-LAPI mentions remain weak/model-adjudicated candidate evidence, that no forbidden claim appears outside an explicit denial or false/locked boundary row, and that the exact manuscript section title remains `Operational evaluation and weak-evidence diagnostics`.
