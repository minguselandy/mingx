# POST-LAPI Extraction Quality Audit

Goal ID: POST-7-RUN / Extraction quality audit
Run ID: `post_lapi_extraction_quality_audit_live_v1`
Claim ceiling: `operational_utility_only/no_claim_upgrade`

## Scope

This owner-approved pilot ran a bounded DashScope-compatible extraction quality audit over 100 HotpotQA candidate-pool examples. Outputs are model-adjudicated candidate operational extraction-risk evidence only. They are not human-validated extraction measurement, measurement validation, metric bridge support, calibrated proxy support, V-information proxy support, paper evidence, selector superiority, Route 5 unlock evidence, or Route 8 unlock evidence.

## Run Metadata

- Live API calls run: `100`
- Example count: `100`
- Stratum count: `10`
- Model snapshot: `qwen3.6-flash`
- Endpoint family: `dashscope_openai_compatible_chat_completions`
- Endpoint: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- Raw API responses stored: `false`
- Route 5 locked: `true`
- Route 8 locked: `true`
- Claim upgrade introduced: `false`
- Gate status: `post7_extraction_quality_audit_completed`

## Aggregate Metrics

- Value-weighted loss proxy: `0.197403`
- Value-weighted loss proxy interpretation: `candidate_operational_evidence_only`
- Qualifier loss rate: `0.01`
- Temporal scope error rate: `0.08`
- Provenance loss rate: `0.0`
- Selector impact rate: `0.0`
- Parse failed rate: `0.0`

## Claim Boundary

Allowed interpretation is model-adjudicated extraction-risk evidence and operational extraction audit only. The value-weighted loss proxy is candidate operational evidence only. Denied interpretations include human-validated extraction measurement, measurement validation, theorem transfer to M*, end-to-end validation, metric bridge support, calibrated proxy support, V-information proxy support, paper evidence, selector superiority, Route 5 unlock, and Route 8 unlock.

## Artifact Index

- `artifacts/experiments/post_lapi_extraction_quality_audit/audit_records.jsonl`
- `artifacts/experiments/post_lapi_extraction_quality_audit/stratum_summary.csv`
- `artifacts/experiments/post_lapi_extraction_quality_audit/stratum_summary.json`
- `artifacts/experiments/post_lapi_extraction_quality_audit/aggregate_report.json`
- `artifacts/experiments/post_lapi_extraction_quality_audit/run_manifest.json`
- `artifacts/experiments/post_lapi_extraction_quality_audit/claim_ledger.json`
