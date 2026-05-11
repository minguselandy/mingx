# P49 Extraction Audit Pilot v12

P49 adds a deterministic fixture pilot for auditing the extraction boundary:

```text
raw source records -> extraction gate -> structured findings -> candidate pool M
```

The pilot is not a selector benchmark and not bridge calibration evidence. It
checks whether extracted findings preserve source support, source spans,
provenance handles, and candidate-pool hashes before context projection.

## Scope

The fixture run is located at:

- `artifacts/experiments/extraction_audit_pilot_v12/`

It covers six fixture case families:

- clean extraction
- missing critical finding
- unsupported or hallucinated finding
- duplicate or over-merged finding
- contradictory source
- provenance-missing finding

## Schema

The pilot writes:

- `extraction_audit_cases.jsonl`
- `extraction_audit_findings.jsonl`
- `extraction_audit_labels.jsonl`
- `extraction_ground_truth_findings.jsonl`
- `extraction_audit_defects.csv`
- `stratum_completeness_report.csv`
- `value_weighted_loss.csv`
- `extraction_audit_summary.json`
- `extraction_claim_gate_report.json`
- `extraction_audit_manifest.json`
- `extraction_audit_report.md`

Each extracted finding records:

- `finding_id`
- `finding_text`
- `finding_type`
- `source_record_ids`
- `source_span_refs`
- `provenance_refs`
- `candidate_pool_hash`
- `finding_hash`
- `support_status`
- `extraction_defects`

Supported findings require source records, source span refs, and provenance refs.
Unsupported, over-merged, duplicate, contradictory, missing-span, and
missing-provenance findings are represented as audit defects.

## Determinism

The fixture path uses stable row ordering, sorted JSON keys, deterministic
finding hashes, and deterministic candidate-pool hashes. Canonical artifacts do
not include timestamps, UUIDs, absolute local paths, file URIs, or live API
responses.

## Claim Boundary

The claim gate remains conservative:

- `data_source_kind = fixture`
- `audit_scope = extraction_audit_pilot`
- `evidence_scope = fixture_extraction_audit_only`
- `paper_evidence_eligible = false`
- `measurement_validation_claim = false`
- `metric_claim_level = operational_utility_only`
- `calibrated_proxy_supported = false`
- `vinfo_proxy_supported = false`
- `live_api_used = false`

This audit may identify extraction defects in the M-star to M boundary. It does
not establish selector-regime support, V-information proxy support, calibrated
utility-to-logloss bridge support, measurement validation, or paper-grade
benchmark evidence.

## Run

```bash
uv run python -m cps.experiments.extraction_audit --config configs/runs/extraction-audit-pilot-v12.json --output-dir artifacts/experiments/extraction_audit_pilot_v12
```
