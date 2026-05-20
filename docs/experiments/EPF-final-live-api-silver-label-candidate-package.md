# EPF Final Live-API Silver-Label Candidate Package

## Status

- terminal_state: `EPF_FINAL_REVIEWABLE`
- claim_ceiling: `operational_utility_only/no_claim_upgrade`
- evidence_class: `backend_constrained_operational_candidate_package`
- review_status: `candidate_pending_independent_review`

## Package

The EPF final package adds a live-API-only silver-label layer on top of the
WS0-WS10 candidate evidence package. The silver labels are LLM-generated,
model-adjudicated candidate labels. They are not human labels, external gold
labels, measurement validation, metric bridge evidence, calibrated proxy
support, V-information proxy support, teacher-forced NLL support, paper
evidence, or global selector superiority evidence.

Generated artifacts:

- `artifacts/experiments/epf_c_silver_labels/label_schema.json`
- `artifacts/experiments/epf_c_silver_labels/silver_label_manifest.json`
- `artifacts/experiments/epf_c_silver_labels/silver_labels.jsonl`
- `artifacts/experiments/epf_c_silver_labels/label_generation_report.json`
- `artifacts/experiments/epf_c_silver_labels/uncertainty_disagreement_report.json`
- `artifacts/experiments/epf_final/final_epf_manifest.json`
- `artifacts/experiments/epf_final/final_claim_request.json`
- `artifacts/experiments/epf_final/scoped_operational_evaluation_summary.json`
- `artifacts/experiments/epf_final/independent_review_checklist.md`

The package stores normalized enum labels, confidence buckets,
uncertainty/disagreement buckets, hashes, and compact provenance. It does not
store raw API responses, secrets, raw dataset mirrors, operator inputs, or
free-form generated rationale text.

## Denied Claims

- `teacher_forced_nll_support`
- `fixed_target_continuation_scoring_available`
- `metric_bridge_support`
- `calibrated_proxy_supported`
- `vinfo_proxy_supported`
- `measurement_validation`
- `human_external_gold_validation`
- `paper_evidence`
- `global_selector_superiority`

Route 5 and Route 8 remain locked.
