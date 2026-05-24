# PAPER-REV-6 Appendix Reproducibility Review

Status: complete
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Scope

Reviewed and updated the PAPER-REV-6 appendix, artifact-index, package-map, excluded-leftovers, and reproducibility surfaces:

- `docs/paper/final-submission-artifact-index.md`
- `docs/paper/final-submission-package-map.md`
- `docs/paper/final-excluded-leftovers-ledger.md`
- `docs/paper/post-lapi-evidence-freeze-ledger.md`
- `docs/paper/submission-experiment-summary.md`

## Appendix Map Audit

| required map item | status |
|---|---|
| Manuscript-facing docs | included |
| Claim-boundary docs | included |
| Evidence ledgers | included |
| POST-3 artifact summary | included |
| POST-4 artifact summary | included |
| POST-5 artifact summary | included |
| POST-6 artifact summary | included |
| POST-7 artifact summary | included |
| Evidence freeze checksums | included |
| Table inputs | included |
| JSON/JSONL validation artifacts | included |
| Scan summaries | included |
| Excluded leftovers ledger by category only | included |

## Reproducibility Audit

| required statement | status |
|---|---|
| No raw API responses are stored | explicit |
| Normalized rows are stored | explicit |
| Hashes are stored | explicit |
| Compact provenance is stored | explicit |
| Prompts/templates are stored where appropriate | explicit |
| Checksums are stored | explicit |
| Live API model snapshots/endpoints should be documented where applicable | explicit |
| Replays are operational and scoped | explicit |
| Replays do not validate V-information | explicit |

## Evidence-Artifact Hygiene

This PAPER-REV-6 pass is docs-only. It did not modify JSON/JSONL evidence outputs, regenerate checksums, stage leftovers, run live API calls, start experiments, rerun POST-3 through POST-7, scale silver labels, commit, or push.

## Verification

Passed:

- `git diff --check`
- `uv run pytest tests/test_revised_framing_guardrails.py tests/test_live_api_claim_contract.py tests/test_no_teacher_forced_claims_live_api_only.py -q`
- targeted appendix/reproducibility/no-artifact-change scans
