# Submission Claim Ledger

Status: SUB-3 submission package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This ledger packages the frozen POST-LAPI evidence for paper submission and reviewer defense. It does not run live API calls, start experiments, create labels, store raw API responses, unlock Route 5, unlock Route 8, or upgrade claims.

## Core Positioning

The paper is:

```text
V-information anchored,
live-API-only,
claim-gated,
operational audit / diagnostic paper.
```

The paper is not:

```text
compression paper,
router paper,
metric-proof paper,
calibrated proxy paper,
selector superiority paper.
```

## Claim Boundary

Allowed paper-facing language:

- dispatch-time evidence projection in a live-agent / live-API setting;
- formal V-information anchor for the problem statement and theory;
- operational-only evidence under named datasets, budgets, baselines, metrics, and materialization regime;
- weak model-adjudicated diagnostics;
- sufficiency / abstention operational diagnostics;
- operational reprojection witness and omitted-evidence diagnostics;
- replayable artifact evidence;
- model-adjudicated extraction-risk candidate evidence;
- fail-closed claim gates.

Required stance:

- Generated-token chat logprobs are output-side confidence diagnostics only.
- Model-adjudicated labels are weak evidence only.
- POST-6 operational replay is scoped and does not generalize beyond the frozen named conditions.
- POST-7 extraction audit is model-adjudicated extraction-risk evidence only.
- POST-5 reprojection witness is operational omitted-evidence evidence only.
- The conclusion remains `operational_utility_only/no_claim_upgrade`.

## Denied Claims

| claim | submission status | safe wording |
|---|---|---|
| fixed-target teacher-forced NLL | denied | live API generated-token confidence diagnostics only |
| fixed-target continuation scoring support | denied | current backend limitation |
| metric bridge support | denied | bridge attempts failed closed or are unavailable |
| calibrated proxy support | denied | no `calibrated_proxy_supported` claim |
| V-information proxy validation | denied | V-information is the formal anchor, not a deployed verified measure |
| `vinfo_proxy_supported` | denied | no V-information proxy support claim |
| measurement validation | denied | no human/external gold route or accepted measurement route |
| human/external gold validation | denied | human/external gold labels are absent |
| paper-grade evidence | denied | current live-API outputs remain operational or candidate-only |
| selector superiority | denied | only scoped operational comparisons are allowed |
| global selector superiority | denied | no global superiority claim |
| Route 5 unlock | denied | Route 5 locked |
| Route 8 unlock | denied | Route 8 locked |

## Reviewer-Facing Nonclaims

These nonclaims are intentionally duplicated in one place so reviewers can find the boundary quickly:

- No fixed-target teacher-forced NLL.
- No fixed-target continuation scoring.
- Generated-token logprobs are output-side diagnostics only.
- No metric bridge support.
- No calibrated proxy support.
- No V-information proxy support.
- No human/external gold validation.
- No measurement validation.
- No selector superiority or global selector superiority.
- POST-6 operational replay is scoped by dataset, budgets, baselines, metrics, and materialization/evaluator regime.
- POST-7 extraction audit is model-adjudicated extraction-risk evidence only.
- POST-3 judge outputs are weak evidence only.
- Route 5 remains locked.
- Route 8 remains locked.

## Package Ledger

| package | current state | allowed use | denied boundary |
|---|---|---|---|
| Backend capability | Live API exposes generated-token chat logprobs but not fixed-target continuation scoring. | Explain backend limits and fail-closed claim gating. | No fixed-target teacher-forced NLL, metric bridge support, calibrated proxy support, V-information proxy support, Route 5 unlock, or Route 8 unlock. |
| POST-3 judge stability | 30 examples, 240 normalized rows, 240 live API calls; duplicate agreement `0.9833`, order-swap agreement `0.9833`, rubric paraphrase agreement `0.9667`. | Weak model-adjudicated diagnostics only. | No measurement validation, human/external gold validation, paper-grade evidence, or selector superiority. |
| POST-4 sufficiency / abstention | 50 final normalized rows, 50 final artifact calls, 100 total turn calls; gate `sufficiency_abstention_candidate_ready`. | Sufficiency / abstention operational diagnostic only. | No truth validation, human-calibrated abstention, measurement validation, or paper-grade evidence. |
| POST-5 reprojection witness | 26 normalized rows; repair candidate, label-change, and unsupported-to-supported rates each `0.576923`; parse failed rate `0.0`. | Candidate operational evidence only. | No validated repair, truth correction guarantee, metric bridge support, or selector superiority. |
| POST-6 operational replay | 2,000 normalized replay records over 200 candidate pools; budgets `512` and `1024`; oracle `non_deployable_upper_bound`; 0 live API calls. | Scoped operational replay only under matched budgets. | No selector superiority, global selector superiority, metric bridge support, measurement validation, or paper-grade evidence. |
| POST-7 extraction audit | 100 model-adjudicated extraction audit records, 10 per stratum; value-weighted loss proxy `0.197403`. | Extraction-risk diagnostics only. | No human-validated extraction measurement, measurement validation, theorem transfer to M-star, or selector validity claim. |
| JSON / JSONL and scan hygiene | 27 JSON files, 5 JSONL files, 2,416 JSONL rows; secret scan, raw-response-storage scan, forbidden-path scan, compileall, and guardrails passed in SUB-0. | Artifact hygiene, replayability, and storage-policy evidence only. | No new experiment, new live API evidence, raw response storage, or stronger empirical claim. |
| SUB-2 independent review | Verdict `ACCEPT_WITH_NOTES`; required corrections: none; SUB-3 can proceed under same claim ceiling. | Reviewer-facing boundary control. | No claim upgrade. |

## Methods Artifact Chain

The submission methods use ProjectionBundleV1 as the audit interface:

| component | method role | claim boundary |
|---|---|---|
| ProjectionPlan | records considered, selected, and excluded evidence for a dispatch | audit interface only |
| BudgetWitness | records estimated/realized token use, trims, and overflow handling | audit interface only |
| MaterializedContext | records realized ordering, section boundaries, and content inventory | replay interface only |
| MetricBridgeWitness | records metric class, freshness, active stratum, and bridge status | claim-level gate, not validation by itself |
| CounterfactualReplayWitness | records frozen state, intervention, evaluator, replicates, and effective sample size | scoped operational replay only |
| ReprojectionWitness | records uncertainty trigger, restored evidence, context diff, budget delta, selector before/after, and before/after outputs | operational omitted-evidence diagnostic only |
| ClaimLedger | records allowed claims, denied claims, Route 5 / Route 8 locks, raw-response state, human/external gold-label state, and claim-upgrade flag | fail-closed boundary control |

Fail-closed rule: unsupported, stale, absent, underpowered, or
stratum-mismatched evidence cannot upgrade a claim. Generated-token logprobs
remain output-side confidence diagnostics only; fixed-target continuation
scoring remains unsupported; judge labels remain weak/model-adjudicated
signals rather than gold labels.

## Locks

Route 5 locked: yes

Route 8 locked: yes

Raw API responses stored: no

Claim upgrade introduced: no
