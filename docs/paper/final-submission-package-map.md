# Final Submission Package Map

Status: PAPER-REV-6 appendix package
Claim ceiling: `operational_utility_only/no_claim_upgrade`

This map is the reviewer-facing navigation layer for the final submission package. It points to existing docs and frozen artifacts only. It does not modify evidence artifacts, regenerate checksums, run live API calls, or upgrade claims.

## Package Layers

| layer | primary entries | purpose | boundary |
|---|---|---|---|
| Manuscript | `docs/archive/context_projection_fixed_v12.md` | source manuscript anchor | operational-audit claim only |
| Submission overview | `docs/paper/submission-experiment-summary.md`; `docs/paper/final-conclusion-claim-safe.md`; `docs/paper/final-submission-nonclaims.md` | reviewer-facing summary, conclusion, and nonclaims | no validation or selector-superiority claim |
| Artifact index | `docs/paper/final-submission-artifact-index.md`; `docs/paper/submission-artifact-index.md` | appendix map over frozen evidence | index only |
| Claim boundary | `docs/paper/submission-claim-ledger.md`; `docs/paper/post-lapi-claim-boundary-summary.md`; `docs/api/live-api-capability-contract.md`; `docs/paper/live-api-experiment-boundaries.md` | explicit allowed and denied claims | Route 5 / Route 8 locked |
| Evidence freeze | `docs/paper/post-lapi-evidence-freeze-ledger.md`; `artifacts/audits/post_lapi_evidence_freeze/manifest.json`; `artifacts/audits/post_lapi_evidence_freeze/checksums.sha256`; `artifacts/audits/post_lapi_evidence_freeze/table_inputs.json` | frozen counts, checksums, table inputs, validation and scan summaries | artifact hygiene only |
| POST-3 | `artifacts/experiments/post_lapi_judge_stability/`; `docs/paper/post-lapi-judge-stability-table.md` | judge stability artifact summary | weak model-adjudicated diagnostics only |
| POST-4 | `artifacts/experiments/post_lapi_sufficiency_abstention/`; `docs/paper/post-lapi-sufficiency-abstention-table.md` | sufficiency / abstention artifact summary | diagnostic only |
| POST-5 | `artifacts/experiments/post_lapi_reprojection_witness/`; `docs/paper/post-lapi-reprojection-witness-table.md` | reprojection witness artifact summary | candidate operational evidence only |
| POST-6 | `artifacts/experiments/post_lapi_operational_replay/`; `docs/paper/post-lapi-operational-replay-table.md` | matched-budget replay artifact summary | scoped operational replay only |
| POST-7 | `artifacts/experiments/post_lapi_extraction_quality_audit/`; `docs/paper/post-lapi-extraction-quality-table.md` | extraction-risk artifact summary | extraction-risk diagnostics only |
| Excluded leftovers | `docs/paper/final-excluded-leftovers-ledger.md` | category-only excluded-leftovers ledger | not submission evidence; not staged |
| Review notes | `docs/reviews/PAPER-REV-6-appendix-reproducibility-review.md` | final review of this appendix/reproducibility pass | docs-only audit |

## Reproducibility Contract

- No raw API responses are stored.
- Normalized rows, hashes, compact provenance, prompts/templates where appropriate, and checksums are stored.
- Live API model snapshots and endpoints should be documented in run manifests where applicable. The current POST-LAPI run manifests record model snapshot / endpoint data for live-API packages and an offline replay marker for POST-6.
- Replays are operational and scoped; they do not validate V-information, metric bridge support, calibrated proxy support, measurement validation, human/external gold validation, selector superiority, Route 5 unlock, or Route 8 unlock.

## Submission-Appendix Order

1. Read the manuscript anchor and conclusion posture.
2. Read the final nonclaims and claim ledger.
3. Use the final artifact index to locate evidence ledgers, table inputs, checksums, JSON/JSONL validation artifacts, and scan summaries.
4. Use POST-3 through POST-7 rows only within their stated evidence tiers.
5. Use the excluded leftovers ledger only as category-level hygiene context, not as paper evidence.

## Boundary Summary

- Claim level: `operational_utility_only/no_claim_upgrade`.
- Route 5: locked.
- Route 8: locked.
- Raw API responses stored: false.
- Evidence artifacts changed by this package map: false.
