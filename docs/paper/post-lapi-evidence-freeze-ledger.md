# POST-LAPI Evidence Freeze Ledger

Status: SUB-0 evidence freeze baseline
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This ledger freezes the completed POST-LAPI candidate operational evidence package at the pushed baseline. It does not run new experiments, does not run live API calls, and does not upgrade any claim.

## Baseline

- Branch: `codex/integrated-validation-workbench`
- Commit: `ce1f7fa307bcacf794befc49eb34beb8f4e4c1e8`
- Remote status: `origin/codex/integrated-validation-workbench` at `ce1f7fa307bcacf794befc49eb34beb8f4e4c1e8`; aligned: `true`
- Recent commit: `POST-LAPI add pilot audit outputs`
- Index status: `no staged files before SUB-0 write phase`
- Untracked leftovers summary: `72` unrelated untracked paths observed before SUB-0 outputs; not staged by this goal.

## Evidence Package

Caption: Evidence tier: frozen POST-LAPI evidence package plus backend capability boundary and replayable artifact evidence. Allowed claim: operational diagnostics under `operational_utility_only/no_claim_upgrade` only. Denied claim: fixed-target teacher-forced NLL support, fixed-target continuation scoring support, metric bridge support, measurement validation, human/external gold validation, paper-grade evidence, selector superiority, global selector superiority, Route 5 unlock, and Route 8 unlock. Human labels present: false. Metric bridge present: false. Route 5 / Route 8: locked / locked.

| Goal | Evidence type | Calls | Rows / records | Artifact files | Gate | Allowed claim | Denied claim |
|---|---|---:|---:|---:|---|---|---|
| Backend | Capability boundary | 0 during SUB-0/SUB-1 synthesis | no new rows | docs/contracts | claim ceiling preserved | backend-constrained operational diagnostics | fixed-target NLL support / metric bridge support |
| POST-3 | Judge stability | 240 | 240 normalized rows | 5 | `weak_evidence_candidate_ready` | model-adjudicated weak evidence | validation / paper-grade evidence |
| POST-4 | Sufficiency / abstention | 50 final / 100 total | 50 final normalized rows | 6 | `sufficiency_abstention_candidate_ready` | sufficiency / abstention diagnostic | truth validation / measurement validation |
| POST-5 | Reprojection witness | 26 | 26 normalized rows | 6 | `reprojection_witness_candidate_ready` | operational reprojection witness | validated repair / selector superiority |
| POST-6 | Operational replay | 0 | 2000 replay records | 9 | `post6_operational_replay_completed` | scoped operational comparison | selector superiority / metric bridge support |
| POST-7 | Extraction audit | 100 | 100 extraction records | 8 | `post7_extraction_quality_audit_completed` | extraction-risk evidence | measurement validation / theorem transfer to M* |
| Artifact hygiene | Evidence freeze | 0 during SUB-0/SUB-1 synthesis | 27 JSON files / 5 JSONL files / 2416 JSONL rows | audit package | hygiene checks passed | replayable artifact evidence | new experiment / raw response storage |

## Specific Metrics

- POST-3: 30 examples, duplicate agreement `0.9833`, order-swap agreement `0.9833`, rubric paraphrase agreement `0.9667`.
- POST-4: final artifact run calls `50`, total turn calls `100`, diagnostic label `sufficiency_abstention_diagnostic_only`.
- POST-5: repair candidate rate `0.576923`, label change rate `0.576923`, unsupported-to-supported rate `0.576923`, parse failed rate `0.0`.
- POST-6: `200` HotpotQA candidate pools, budgets `[512, 1024]`, oracle `non_deployable_upper_bound`.
- POST-7: records per stratum `{'adversarial': 10, 'complex_conditional': 10, 'contradictory': 10, 'cross_chunk': 10, 'high_provenance_value': 10, 'long_tail_entity': 10, 'prerequisite': 10, 'qualifier_heavy': 10, 'simple_factual': 10, 'temporal_scope': 10}`, value-weighted loss proxy `0.197403` as candidate operational evidence only.

## JSON/JSONL and Hygiene Checks

Caption: Evidence tier: replayable artifact evidence for frozen file-format, checksum, scan, and storage-policy checks. Allowed claim: artifact hygiene and evidence-freeze evidence only. Denied claim: new experiment, new live API evidence, raw response storage, measurement validation, human/external gold validation, paper-grade evidence, selector superiority, Route 5 unlock, and Route 8 unlock. Human labels present: false. Metric bridge present: false. Route 5 / Route 8: locked / locked.

| Check | Result |
|---|---|
| Focused POST-3 to POST-7 tests + guardrails | `59 passed` |
| SUB-0 guardrail pytest command | `20 passed` |
| JSON validation | `27` JSON files |
| JSONL validation | `5` JSONL files / `2416` rows |
| Secret scan | passed |
| Raw-response-storage scan | passed |
| Forbidden-path scan | passed |
| Forbidden-claim grep | documented contextual matches only; no positive claim upgrade introduced |
| Compileall | passed |
| git diff --check | passed |

## Appendix Reproducibility Map

| appendix item | frozen source | reviewer-facing location |
|---|---|---|
| Manuscript-facing docs | manuscript anchor and submission summaries | `docs/archive/context_projection_fixed_v12.md`; `docs/paper/submission-experiment-summary.md` |
| Claim-boundary docs | claim ledgers and live-API boundary docs | `docs/paper/submission-claim-ledger.md`; `docs/paper/final-submission-nonclaims.md`; `docs/api/live-api-capability-contract.md` |
| Evidence ledgers | POST-LAPI freeze and v12 evidence ledgers | `docs/paper/post-lapi-evidence-freeze-ledger.md`; `docs/paper/v12-evidence-ledger.md` |
| POST-3 artifact summary | 5 judge-stability artifacts | `docs/paper/final-submission-artifact-index.md` |
| POST-4 artifact summary | 6 sufficiency / abstention artifacts | `docs/paper/final-submission-artifact-index.md` |
| POST-5 artifact summary | 6 reprojection-witness artifacts | `docs/paper/final-submission-artifact-index.md` |
| POST-6 artifact summary | 9 operational-replay artifacts | `docs/paper/final-submission-artifact-index.md` |
| POST-7 artifact summary | 8 extraction-quality artifacts | `docs/paper/final-submission-artifact-index.md` |
| Evidence freeze checksums | `artifacts/audits/post_lapi_evidence_freeze/checksums.sha256` | `docs/paper/final-submission-artifact-index.md` |
| Table inputs | `artifacts/audits/post_lapi_evidence_freeze/table_inputs.json` | `docs/paper/post-lapi-main-results-tables.md` |
| JSON/JSONL validation artifacts | `artifacts/audits/post_lapi_evidence_freeze/manifest.json` | this ledger and final artifact index |
| Scan summaries | manifest scan fields and this hygiene table | this ledger and final artifact index |
| Excluded leftovers ledger | category-only ledger | `docs/paper/final-excluded-leftovers-ledger.md` |

## Reproducibility Statement

- No raw API responses are stored.
- Normalized rows, hashes, compact provenance, prompts/templates where appropriate, and checksums are stored.
- Live API model snapshots and endpoints are documented in run manifests where applicable; offline replay artifacts document their offline replay source instead.
- Replays are operational and scoped by dataset, budgets, baselines, metrics, and materialization/evaluator regime. They do not validate V-information, metric bridge support, calibrated proxy support, measurement validation, selector superiority, Route 5 unlock, or Route 8 unlock.

## Claim Boundary

- Current claim: `operational_utility_only/no_claim_upgrade`
- Allowed claims: model-adjudicated weak evidence, sufficiency / abstention operational diagnostics, operational reprojection witness, scoped operational comparison under matched budgets, and model-adjudicated extraction-risk diagnostics.
- Denied claims: teacher-forced NLL support; fixed-target continuation scoring support; metric bridge support; calibrated_proxy_supported; vinfo_proxy_supported; measurement validation; human/external gold validation; paper-grade evidence; selector superiority; global selector superiority; Route 5 unlock; Route 8 unlock.
- Route 5: locked
- Route 8: locked
- Raw API responses stored: false
