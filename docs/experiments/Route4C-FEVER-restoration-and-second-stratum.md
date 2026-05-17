# Route4C FEVER Restoration and Second Stratum

Status: `blocked_fever_source_unavailable`
Claim status: `no_claim_upgrade`

## Decision

Route 4C is blocked fail-closed. The complete FEVER evidence source is not available in the repository, so evidence sentence provenance cannot be verified for a second bridge stratum. FEVER candidate pools were not generated, and no FEVER logloss scoring readiness is claimed.

No fabricated FEVER evidence was introduced.

## Evidence Checked

- Official FEVER source restored: `false`.
- Evidence sentence provenance verified: `false`.
- Candidate-pool rows available: `0`.
- Delta-record rows available: `0`.
- Logloss scoring ready: `false`.
- Raw dataset mirror committed: `false`.

## Reason Codes

- `full_fever_evidence_source_unavailable`
- `evidence_sentence_provenance_unverified`
- `missing_fever_candidate_pools`
- `missing_fever_delta_records`
- `fever_logloss_scoring_not_ready`
- `route4c_second_stratum_not_established`

## Claim Boundary

- `calibrated_proxy_supported` remains false.
- `vinfo_proxy_supported` remains false.
- `measurement_validated` remains false.
- Route 5 start conditions are not satisfied by Route 4C.

## Produced Artifacts

- `artifacts/experiments/route4c_fever/readiness_report.json`
- `artifacts/experiments/route4c_fever/source_manifest.json`
- `artifacts/experiments/route4c_fever/candidate_pool_manifest.json`
- `artifacts/experiments/route4c_fever/blocked_report.json`
