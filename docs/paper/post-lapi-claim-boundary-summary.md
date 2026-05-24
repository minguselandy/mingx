# POST-LAPI Claim Boundary Summary

Status: SUB-0 claim-boundary synthesis
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Allowed Interpretation

- The frozen POST-LAPI package may be described as candidate operational evidence and weak/model-adjudicated diagnostics.
- The manuscript section title for the integrated empirical record is `Operational evaluation and weak-evidence diagnostics`.
- POST-6 may be described as scoped matched-budget operational replay evidence only; the oracle remains non-deployable.
- POST-7 may be described as model-adjudicated extraction-risk diagnostics only; the value-weighted loss proxy is candidate operational evidence only.
- Reviewer defense responses are centralized in `docs/paper/final-reviewer-response-bank.md` and preserve `operational_utility_only/no_claim_upgrade`.

## Denied Interpretations

| Denied claim | Status | Rationale |
|---|---|---|
| teacher-forced NLL support | denied | Not established by POST-LAPI; claim ceiling remains `operational_utility_only/no_claim_upgrade`. |
| fixed-target continuation scoring support | denied | Not established by POST-LAPI; claim ceiling remains `operational_utility_only/no_claim_upgrade`. |
| metric bridge support | denied | Not established by POST-LAPI; claim ceiling remains `operational_utility_only/no_claim_upgrade`. |
| calibrated_proxy_supported | denied | Not established by POST-LAPI; claim ceiling remains `operational_utility_only/no_claim_upgrade`. |
| vinfo_proxy_supported | denied | Not established by POST-LAPI; claim ceiling remains `operational_utility_only/no_claim_upgrade`. |
| measurement validation | denied | Not established by POST-LAPI; claim ceiling remains `operational_utility_only/no_claim_upgrade`. |
| human/external gold validation | denied | Not established by POST-LAPI; claim ceiling remains `operational_utility_only/no_claim_upgrade`. |
| paper-grade evidence | denied | Not established by POST-LAPI; claim ceiling remains `operational_utility_only/no_claim_upgrade`. |
| selector superiority | denied | Not established by POST-LAPI; claim ceiling remains `operational_utility_only/no_claim_upgrade`. |
| global selector superiority | denied | Not established by POST-LAPI; claim ceiling remains `operational_utility_only/no_claim_upgrade`. |
| Route 5 unlock | denied | Not established by POST-LAPI; claim ceiling remains `operational_utility_only/no_claim_upgrade`. |
| Route 8 unlock | denied | Not established by POST-LAPI; claim ceiling remains `operational_utility_only/no_claim_upgrade`. |

## Locks and Storage

| Boundary | Value |
|---|---|
| Claim level | `operational_utility_only/no_claim_upgrade` |
| Route 5 locked | `true` |
| Route 8 locked | `true` |
| Raw API responses stored | `false` |
| Human/external gold labels present | `false` |
| Metric bridge present | `false` |
| Paper-grade evidence claim | `false` |

## Manuscript Integration Boundary

SUB-1 integrates POST-3 through POST-7 and artifact hygiene into manuscript-facing docs without changing the claim level. The allowed conclusion remains `operational_utility_only/no_claim_upgrade`.

| Result | Evidence tier | Live API calls | Human labels | Metric bridge | Route 5 / Route 8 | raw_response_stored |
|---|---|---:|---|---|---|---|
| POST-3 judge stability | weak/model-adjudicated candidate evidence | 240 | absent | absent | locked / locked | false |
| POST-4 sufficiency / abstention | operational diagnostic candidate evidence | 50 final artifact calls / 100 total turn calls | absent | absent | locked / locked | false |
| POST-5 reprojection witness | operational omitted-evidence evidence only | 26 | absent | absent | locked / locked | false |
| POST-6 operational replay expansion | scoped operational replay evidence only | 0 | absent | absent | locked / locked | false |
| POST-7 extraction quality audit | model-adjudicated extraction-risk evidence only | 100 | absent | absent | locked / locked | false |
| Artifact hygiene / raw-response policy | reproducibility and storage-policy evidence only | 0 during SUB-0/SUB-1 synthesis | absent | absent | locked / locked | false |

Generated-token chat logprobs are operational confidence diagnostics only. Model-adjudicated labels are weak evidence only. Operational replay is scoped to named datasets, budgets, baselines, metrics, and materialization regime. Extraction audit is model-adjudicated extraction-risk evidence only. Reprojection witness is operational omitted-evidence evidence only.

## Methods Artifact Boundary

The methods-facing artifact chain is ProjectionBundleV1:
ProjectionPlan, BudgetWitness, MaterializedContext, MetricBridgeWitness,
CounterfactualReplayWitness when replay is present, ReprojectionWitness when
adaptive re-projection is present, and ClaimLedger. These artifacts make the
dispatch-time audit trail replayable; they are not validation by themselves.

ClaimLedger entries must fail closed. They record the claim ceiling, allowed
claims, denied claims, Route 5 / Route 8 lock state, raw-response storage
state, human/external gold-label state, metric-bridge state, and
claim-upgrade flag. If fixed-target continuation scoring, fixed-target
teacher-forced NLL, human/external gold labels, or a fresh matching bridge are
absent, the corresponding stronger claim stays denied.

Sufficiency / abstention rows use regime labels such as `sufficient_kept`,
`sufficient_dropped`, `insufficient_and_answered`, and
`insufficient_and_abstained`. ReprojectionWitness rows record before/after
controlled replay fields including candidate-pool hash, selected evidence,
restored evidence, context diff, before/after packet refs, before/after output
hashes, budget delta, selector before/after, held-fixed model/prompt/endpoint
fields, and embedded claim ledger. Both remain operational diagnostics.

The integrated manuscript boundary explicitly denies fixed-target NLL support, teacher-forced scoring support, metric bridge support, `calibrated_proxy_supported`, `vinfo_proxy_supported`, measurement validation, human/external gold validation, paper-grade evidence, selector superiority, global selector superiority, Route 5 unlock, and Route 8 unlock.

## Forbidden-Claim Grep Result

The SUB-0 forbidden-claim grep found the expected denied-claim terms in boundary tables, false/locked status rows, runner denied-claim constants, and tests that assert forbidden language is rejected. These matches are contextual guardrails, not positive evidence claims. No SUB-0 output unlocks Route 5 or Route 8, and no SUB-0 output introduces measurement validation, metric bridge support, calibrated proxy support, V-information proxy support, human/external gold validation, paper-grade evidence, selector superiority, or global selector superiority.
