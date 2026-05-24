# POST-LAPI Evidence Freeze Ledger

## Baseline

- Branch:
- Commit:
- Remote status:
- Index status:
- Untracked leftovers summary:

## Evidence package

| Goal | Evidence type | Calls | Rows / records | Gate | Allowed claim | Denied claim |
|---|---|---:|---:|---|---|---|
| POST-3 | Judge stability | 240 | 240 normalized rows | weak_evidence_candidate_ready | model-adjudicated weak evidence | validation |
| POST-4 | Sufficiency / abstention | 50 final / 100 total | TBD | sufficiency_abstention_candidate_ready | sufficiency / abstention diagnostic | truth validation |
| POST-5 | Reprojection witness | 26 | TBD | reprojection_witness_candidate_ready | operational reprojection witness | validated repair |
| POST-6 | Operational replay | 0 | 2,000 replay records | TBD | scoped operational improvement | selector superiority |
| POST-7 | Extraction audit | 100 | 100 extraction records | post7_extraction_quality_audit_completed | extraction-risk evidence | measurement validation |

## Validation and hygiene

| Check | Result |
|---|---|
| Focused tests | 59 passed |
| JSON files | 27 |
| JSONL files | 5 |
| JSONL rows | 2,416 |
| Secret scan | passed |
| Raw-response-storage scan | passed |
| Forbidden-path scan | passed |
| Compileall | passed |

## Claim boundary

- Current claim: `operational_utility_only/no_claim_upgrade`
- Route 5: locked
- Route 8: locked
- Raw API responses stored: false
