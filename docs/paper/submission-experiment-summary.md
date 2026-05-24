# Submission Experiment Summary

Status: SUB-3 submission package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This summary organizes the frozen POST-LAPI evidence for reviewer-facing submission. It does not run live API calls, execute experiments, create labels, or store raw API responses.

## Operational evaluation and weak-evidence diagnostics

The empirical section should be read as operational audit and weak-evidence diagnostics in a live-agent / live-API setting. The formal V-information anchor motivates dispatch-time evidence projection, but the evidence below remains operational-only and claim-gated.

## Main Results Summary

Caption: Evidence tier: reviewer-facing synthesis of backend capability, model-adjudicated weak evidence, sufficiency-abstention diagnostics, candidate operational evidence, matched-budget operational replay only, extraction-risk diagnostics, and replayable artifact evidence. Allowed claim: operational diagnostics under `operational_utility_only/no_claim_upgrade` only. Denied claim: fixed-target teacher-forced NLL support, fixed-target continuation scoring support, metric bridge support, measurement validation, human/external gold validation, paper-grade evidence, selector superiority, global selector superiority, Route 5 unlock, and Route 8 unlock. Human labels present: false. Metric bridge present: false. Route 5 / Route 8: locked / locked.

| result | evidence source | sample / call count | paper-facing use | non-claim |
|---|---|---|---|---|
| Backend capability and claim boundary | `LAPI + POST-LAPI contracts and docs/paper/v12-live-api-operational-paper-claim-table.md` | 0 new live API calls during submission synthesis | Backend capability boundary: generated-token chat logprobs are operational confidence diagnostics only; fixed-target scoring backends are absent. | Not fixed-target teacher-forced NLL support, fixed-target continuation scoring support, metric bridge support, Route 5 unlock, or Route 8 unlock. |
| POST-3 judge stability | `artifacts/experiments/post_lapi_judge_stability/` | 30 examples / 240 normalized rows / 240 live API calls | Weak model-adjudicated diagnostics over duplicate, order-swap, and rubric-paraphrase stability. | Not human/external gold validation, measurement validation, or paper-grade evidence. |
| POST-4 sufficiency / abstention | `artifacts/experiments/post_lapi_sufficiency_abstention/` | 50 final normalized rows / 50 final artifact calls / 100 total turn calls | Sufficiency / abstention operational diagnostic. | Not truth validation, human-calibrated abstention, measurement validation, or paper-grade evidence. |
| POST-5 reprojection witness | `artifacts/experiments/post_lapi_reprojection_witness/` | 26 normalized rows / 26 live API calls | Operational omitted-evidence and reprojection witness evidence. | Not validated repair, truth correction guarantee, metric bridge support, or selector superiority. |
| POST-6 operational replay | `artifacts/experiments/post_lapi_operational_replay/` | 2,000 normalized replay records / 200 candidate pools / 0 live API calls | Scoped operational replay under matched budgets `512` and `1024`; oracle marked `non_deployable_upper_bound`. | Not selector superiority, global selector superiority, metric bridge support, measurement validation, or paper-grade evidence. |
| POST-7 extraction audit | `artifacts/experiments/post_lapi_extraction_quality_audit/` | 100 model-adjudicated extraction audit records / 10 per stratum / 100 live API calls | Model-adjudicated extraction-risk candidate evidence; value-weighted loss proxy `0.197403`. | Not human-validated extraction measurement, measurement validation, theorem transfer to M-star, or selector validity. |
| JSON / JSONL and scan hygiene | `artifacts/audits/post_lapi_evidence_freeze/` | 27 JSON files / 5 JSONL files / 2,416 JSONL rows | Artifact hygiene, replayability, checksums, and storage-policy evidence. | Not a new experiment, new live API evidence, or raw response storage. |

## Backend Capability and Claim Boundary

The supported live API provides generated-token chat logprobs, not fixed-target teacher-forced NLL or fixed-target continuation scoring. The submission does not relabel generated-token chat logprobs as teacher-forced NLL. It does not claim metric bridge support, V-information proxy validation, calibrated proxy support, measurement validation, or human/external gold validation.

The live-API-only constraint contributes a concrete backend boundary: it shows which operational artifacts can be reproduced through deployed APIs and where formal metric claims must fail closed because the needed scoring backend is absent.

## Replayable Artifact Evidence

The paper package emphasizes replayable artifacts, manifests, claim ledgers, prompt and schema hashes where applicable, candidate-pool hashes, materialization constraints, normalized outputs, and storage-policy checks. These artifacts are a contribution because they let reviewers inspect the operational audit trail and reproduce claim-gate decisions. They are replay/audit evidence, not validation evidence.

Raw API responses are not stored. Route 5 remains locked. Route 8 remains locked.

The appendix-facing package map is `docs/paper/final-submission-package-map.md`, with the artifact index in `docs/paper/final-submission-artifact-index.md` and the category-only leftovers ledger in `docs/paper/final-excluded-leftovers-ledger.md`. The reproducibility contract is unchanged: normalized rows, hashes, compact provenance, prompts/templates where appropriate, model snapshot / endpoint metadata where applicable, table inputs, checksums, JSON/JSONL validation artifacts, and scan summaries are stored; raw API responses are not stored. Replays remain operational and scoped, not V-information validation.

## Sufficiency, Abstention, and Reprojection Witness

Sufficiency / abstention diagnostics expose support, contradiction, insufficiency, abstention, and parse-failure behavior in a bounded model-adjudicated setting. Reprojection witness artifacts expose omitted-evidence and repair-candidate behavior. These are not truth validation, human-calibrated abstention, validated repair, or theorem transfer.

They are included to show the submission's fail-closed audit architecture: when weak evidence is unstable, insufficient, provenance-losing, or backend-limited, the claim remains operational-only or is suppressed.

## Extraction Quality Boundary

Extraction quality is separate from selector quality because the selector operates over an extracted pool, while end-to-end task performance also depends on what the extraction gate omitted or distorted. POST-7 therefore reports model-adjudicated extraction-risk evidence only. It does not establish selector validity, measurement validation, or transfer from M-star to the extracted pool.

## Current Completion State

Caption: Evidence tier: submission-state synthesis and replayable artifact evidence. Allowed claim: frozen submission package readiness under `operational_utility_only/no_claim_upgrade` only. Denied claim: new live API evidence, new experiment, fixed-target teacher-forced NLL support, metric bridge support, measurement validation, paper-grade evidence, selector superiority, Route 5 unlock, and Route 8 unlock. Human labels present: false. Metric bridge present: false. Route 5 / Route 8: locked / locked.

| component | status | allowed use | non-claim |
|---|---|---|---|
| SUB-0 evidence freeze | complete | frozen normalized source package | no live API calls during SUB-0 synthesis |
| SUB-1 manuscript integration | complete | manuscript-facing integration under exact operational section | no claim upgrade |
| SUB-2 independent review | complete, `ACCEPT_WITH_NOTES` | claim-boundary review and SUB-3 go-ahead | no required corrections |
| SUB-3 submission package | this package | reviewer-facing summary, ledger, limitations, abstract, conclusion, Q&A, and review | no live API calls or new experiments |

## Non-Claims

The submission does not claim fixed-target teacher-forced NLL, fixed-target continuation scoring support, metric bridge support, calibrated proxy support, `vinfo_proxy_supported`, V-information proxy validation, measurement validation, human/external gold validation, paper-grade evidence, selector superiority, global selector superiority, Route 5 unlock, or Route 8 unlock.
