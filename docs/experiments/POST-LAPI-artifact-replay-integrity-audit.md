# POST-LAPI Artifact Replay Integrity Audit

Goal ID: POST-1 / Artifact replay integrity configuration and offline audit

## Scope

This audit configures and runs an offline replay-integrity check over existing EPF-FINAL, PAPER-RS, and LAPI-facing artifacts. It uses only committed or locally present artifact metadata and documentation. It does not run live API calls, create new labels, run model judging, unlock Route 5, unlock Route 8, or store raw API responses.

Claim ceiling: `operational_utility_only/no_claim_upgrade`

Allowed claim labels:
- `replayable_artifact_evidence`
- `artifact_hygiene_evidence`
- `operational_audit_evidence`

Denied claim labels:
- `scientific_validation`
- `measurement_validation`
- `paper_grade_evidence`
- `metric_bridge_support`
- `vinfo_proxy_supported`
- `selector_superiority`

## Inputs

Configuration:
- `configs/post_lapi/artifact_replay_integrity_config.yaml`

Generated summaries:
- `artifacts/audits/post_lapi_replay_integrity/summary.json`
- `artifacts/audits/post_lapi_replay_integrity/summary.csv`

Primary replay bundle source:
- `artifacts/experiments/epf_final/final_epf_manifest.json`
- `artifacts/experiments/epf_final/final_claim_request.json`
- `artifacts/experiments/epf_final/scoped_operational_evaluation_summary.json`

Excluded from evidence scanning:
- `.codex`
- `artifacts/operator_inputs`
- `operator_inputs`
- `raw_api_dumps`
- `raw_dataset_mirrors`

## Audit Results

| Metric | Result |
| --- | ---: |
| Bundle count | 1 |
| Schema valid count | 1 |
| Schema valid rate | 1.0 |
| ProjectionPlan present rate | 1.0 |
| BudgetWitness present rate | 1.0 |
| MaterializedContext present rate | 1.0 |
| MetricBridgeWitness present rate | 1.0 |
| ClaimLedger present rate | 1.0 |
| selected_evidence_ids present rate | 1.0 |
| excluded_evidence_ids present rate | 1.0 |
| materialization_order present rate | 1.0 |
| downstream_prompt_hash present rate | 1.0 |
| model_snapshot / endpoint present rate | 1.0 |
| raw_response_stored=false rate | 1.0 |
| Replay reconstruction pass rate | 1.0 |
| Claim boundary consistency rate | 1.0 |
| Denied-claim leakage count | 0 |
| Supporting artifact existence rate | 1.0 |

## Boundary Statement

The audit supports only an operational artifact-hygiene statement: the selected existing artifacts can be reconstructed into a schema-valid projection bundle with required replay fields present, raw-response storage flags remaining false, Route 5 and Route 8 remaining locked, and no denied-claim leakage detected by the offline audit script.

It does not support scientific validation, measurement validation, paper-grade evidence, metric bridge support, `vinfo_proxy_supported`, or selector-superiority claims.

## Reproduction

Run:

```powershell
python scripts/audit_projection_bundle_integrity.py
```

Expected output files:
- `artifacts/audits/post_lapi_replay_integrity/summary.json`
- `artifacts/audits/post_lapi_replay_integrity/summary.csv`

Observed run status:
- Live API calls run: no
- New model judging run: no
- New silver labels created: no
- Raw API responses stored: no
- Route 5 locked: yes
- Route 8 locked: yes
- Claim upgrade introduced: no
