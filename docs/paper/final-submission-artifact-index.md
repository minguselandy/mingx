# Final Submission Artifact Index

Status: PAPER-REV-6 appendix package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This appendix-facing index maps the replayable operational-audit package to the paper surfaces reviewers need. It is an index only. It does not create evidence, modify JSON/JSONL artifacts, regenerate checksums, run live API calls, unlock Route 5, unlock Route 8, or upgrade claims.

## Appendix Map

| appendix item | paper-facing location | source artifacts / docs | claim boundary |
|---|---|---|---|
| Manuscript-facing docs | `docs/archive/context_projection_fixed_v12.md`; `docs/paper/submission-experiment-summary.md`; `docs/paper/final-conclusion-claim-safe.md` | final manuscript anchor and submission summaries | operational audit / diagnostic paper only |
| Claim-boundary docs | `docs/paper/submission-claim-ledger.md`; `docs/paper/final-submission-nonclaims.md`; `docs/paper/post-lapi-claim-boundary-summary.md`; `docs/api/live-api-capability-contract.md`; `docs/paper/live-api-experiment-boundaries.md`; `docs/paper/v12-live-api-operational-paper-claim-table.md` | claim ledgers, live-API boundary, denied-claim tables | no claim upgrade; Route 5 / Route 8 locked |
| Evidence ledgers | `docs/paper/post-lapi-evidence-freeze-ledger.md`; `docs/paper/v12-evidence-ledger.md`; `docs/paper/submission-claim-ledger.md` | freeze manifest and claim ledgers | replayable artifact evidence only |
| POST-3 artifact summary | `docs/paper/post-lapi-main-results-tables.md`; `docs/paper/post-lapi-judge-stability-table.md` | `artifacts/experiments/post_lapi_judge_stability/` | model-adjudicated weak diagnostics only |
| POST-4 artifact summary | `docs/paper/post-lapi-main-results-tables.md`; `docs/paper/post-lapi-sufficiency-abstention-table.md` | `artifacts/experiments/post_lapi_sufficiency_abstention/` | sufficiency-abstention diagnostics only |
| POST-5 artifact summary | `docs/paper/post-lapi-main-results-tables.md`; `docs/paper/post-lapi-reprojection-witness-table.md` | `artifacts/experiments/post_lapi_reprojection_witness/` | candidate operational evidence only |
| POST-6 artifact summary | `docs/paper/post-lapi-main-results-tables.md`; `docs/paper/post-lapi-operational-replay-table.md` | `artifacts/experiments/post_lapi_operational_replay/` | scoped operational replay only |
| POST-7 artifact summary | `docs/paper/post-lapi-main-results-tables.md`; `docs/paper/post-lapi-extraction-quality-table.md` | `artifacts/experiments/post_lapi_extraction_quality_audit/` | extraction-risk diagnostics only |
| Evidence freeze checksums | `docs/paper/post-lapi-evidence-freeze-ledger.md` | `artifacts/audits/post_lapi_evidence_freeze/checksums.sha256` | checksum and storage-policy evidence only |
| Table inputs | `docs/paper/post-lapi-main-results-tables.md` | `artifacts/audits/post_lapi_evidence_freeze/table_inputs.json` | normalized table source only |
| JSON/JSONL validation artifacts | `docs/paper/post-lapi-evidence-freeze-ledger.md` | `artifacts/audits/post_lapi_evidence_freeze/manifest.json` | file-format validation only |
| Scan summaries | `docs/paper/post-lapi-evidence-freeze-ledger.md` | `manifest.json` scan fields: secret scan, raw-response-storage scan, forbidden-path scan, forbidden-claim grep | hygiene evidence only |
| Excluded leftovers ledger | `docs/paper/final-excluded-leftovers-ledger.md` | category-only ledger | leftovers are not staged and are not submission evidence |

## Artifact Summaries

| package | stored artifacts | normalized rows / records | live API calls in package | stored provenance | allowed reading |
|---|---:|---:|---:|---|---|
| POST-3 judge stability | 5 | 240 rows | 240 | run manifest, prompt hashes, schema hash, model snapshot, endpoint, claim ledger, checksums | weak model-adjudicated diagnostics only |
| POST-4 sufficiency / abstention | 6 | 50 rows | 50 final / 100 total turns | run manifest, prompt/template hash, schema hash, model snapshot, endpoint, claim ledger, checksums | sufficiency-abstention diagnostics only |
| POST-5 reprojection witness | 6 | 26 rows | 26 | run manifest, downstream prompt hash, schema hash, model snapshot, endpoint, witness-record hash, claim ledger, checksums | candidate operational evidence only |
| POST-6 matched-budget replay | 9 | 2,000 replay records / 200 candidate pools | 0 | run manifest, candidate-pool hash, replay-record hash, source trace/config hashes, claim ledger, checksums | scoped operational replay only |
| POST-7 extraction audit | 8 | 100 records / 10 per stratum | 100 | run manifest, schema hash, model snapshot, endpoint, cost/latency hash, claim ledger, checksums | extraction-risk diagnostics only |
| Evidence freeze | audit package | 27 JSON files / 5 JSONL files / 2,416 JSONL rows | 0 during SUB-0/SUB-1 synthesis | freeze manifest, table inputs, checksums, scan summaries | artifact hygiene and replayability only |

## Reproducibility Statement

- No raw API responses are stored.
- Normalized rows, hashes, compact provenance, prompts/templates where appropriate, and checksums are stored.
- Live API model snapshots and endpoints are documented in run manifests where applicable. POST-3, POST-4, POST-5, and POST-7 record `qwen3.6-flash` with the DashScope OpenAI-compatible chat-completions endpoint; POST-6 records an offline existing replay artifact and 0 live API calls.
- Replays are operational and scoped by dataset, budgets, baselines, metrics, and materialization/evaluator regime. They do not validate V-information, metric bridge support, calibrated proxy support, measurement validation, selector superiority, Route 5 unlock, or Route 8 unlock.

## Boundary Summary

- Claim level: `operational_utility_only/no_claim_upgrade`.
- Route 5: locked.
- Route 8: locked.
- Human labels present: false.
- Metric bridge present: false.
- Raw API responses stored: false.
- Evidence artifacts changed by this index: false.
