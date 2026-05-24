from __future__ import annotations

from cps.extraction.audit_schema import ExtractionAuditRecord
from cps.extraction.extraction_risk_ledger import (
    DENIED_EXTRACTION_CLAIMS,
    build_extraction_risk_ledger,
    evaluate_extraction_claim_gate,
)


def _record(record_id, *, stratum="simple_factual", label="captured", value_weight=1.0):
    return ExtractionAuditRecord.from_dict(
        {
            "record_id": record_id,
            "source_document_id": f"doc-{record_id}",
            "source_document_hash": f"doc-hash-{record_id}",
            "source_span_hash": f"span-hash-{record_id}",
            "extracted_item_id": f"item-{record_id}",
            "extracted_item_hash": f"item-hash-{record_id}",
            "candidate_pool_hash": "pool-hash",
            "stratum": stratum,
            "label": label,
            "label_source_kind": "model_adjudicated",
            "judge_model_snapshot": "static-judge-snapshot",
            "judge_prompt_hash": "prompt-hash",
            "rubric_version": "extraction_quality_audit_v1",
            "rubric_paraphrase_id": "p0",
            "order_swap": False,
            "duplicate_index": 0,
            "value_weight": value_weight,
            "selector_impact": "candidate_pool_risk_only",
            "raw_response_stored": False,
            "live_api_call_performed": False,
        }
    )


def test_extraction_claim_gate_allows_only_model_adjudicated_risk_evidence() -> None:
    gate = evaluate_extraction_claim_gate(
        [
            _record("a", stratum="simple_factual", label="captured"),
            _record("b", stratum="qualifier_heavy", label="lost_qualifier"),
            _record("c", stratum="temporal_scope", label="temporal_scope_error"),
        ]
    )

    assert gate["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert gate["allowed_claims"] == ["model_adjudicated_extraction_risk_evidence"]
    assert set(gate["denied_claims"]) >= DENIED_EXTRACTION_CLAIMS
    assert gate["final_gate_status"] == "model_adjudicated_extraction_risk_ready"
    assert gate["audit_diagnostic_only"] is True
    assert gate["measurement_validation_claim"] is False
    assert gate["metric_bridge_support"] is False
    assert gate["calibrated_proxy_supported"] is False
    assert gate["vinfo_proxy_supported"] is False
    assert gate["paper_evidence_eligible"] is False
    assert gate["selector_superiority_claim"] is False
    assert gate["route_5_locked"] is True
    assert gate["route_8_locked"] is True
    assert gate["raw_response_stored"] is False
    assert gate["live_api_call_performed"] is False
    assert gate["metrics"]["capture_rate_by_stratum"]["simple_factual"] == 1.0
    assert gate["metrics"]["qualifier_loss_rate"] == 1 / 3
    assert gate["metrics"]["temporal_scope_error_rate"] == 1 / 3


def test_extraction_claim_gate_suppresses_empty_or_malformed_evidence() -> None:
    empty_gate = evaluate_extraction_claim_gate([])

    assert empty_gate["allowed_claims"] == []
    assert empty_gate["final_gate_status"] == "suppressed_no_records"
    assert "no_records" in empty_gate["reason_codes"]

    raw_record = _record("raw").to_dict()
    raw_record["raw_response_stored"] = True
    gate = evaluate_extraction_claim_gate([raw_record])

    assert gate["allowed_claims"] == []
    assert gate["final_gate_status"] == "downgraded_to_ambiguous"
    assert "invalid_record" in gate["reason_codes"]
    assert gate["raw_response_stored"] is False


def test_extraction_risk_ledger_serializes_with_claim_ledger_boundary() -> None:
    ledger = build_extraction_risk_ledger(
        [
            _record("a", stratum="high_provenance_value", label="provenance_loss"),
            _record("b", stratum="prerequisite", label="missing", value_weight=2.0),
        ]
    )
    payload = ledger.to_dict(include_claim_ledger=True)

    assert payload["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert payload["allowed_claims"] == ["model_adjudicated_extraction_risk_evidence"]
    assert payload["human_sentinel_audit"]["enabled_now"] is False
    assert payload["human_sentinel_audit"]["current_evidence"] is False
    assert payload["claim_ledger"]["current_claim_level"] == "operational_utility_only/no_claim_upgrade"
    assert payload["claim_ledger"]["allowed_claims"] == [
        "model_adjudicated_extraction_risk_evidence"
    ]
    assert "human_validated_extraction_measurement" in payload["claim_ledger"]["denied_claims"]
    assert payload["claim_ledger"]["claim_upgrade"] is False
    assert payload["claim_ledger"]["route_5_locked"] is True
    assert payload["claim_ledger"]["route_8_locked"] is True
    assert payload["claim_ledger"]["raw_response_stored"] is False
    assert payload["metrics"]["missing_rate"] == 0.5
    assert payload["metrics"]["provenance_loss_rate"] == 0.5


def test_extraction_denied_claims_cover_goal_forbidden_claims() -> None:
    assert DENIED_EXTRACTION_CLAIMS >= {
        "human_validated_extraction_measurement",
        "end_to_end_measurement_validation",
        "theorem_transfer_to_M_star",
        "measurement_validation",
        "metric_bridge_support",
        "calibrated_proxy_supported",
        "vinfo_proxy_supported",
        "paper_evidence",
        "selector_superiority",
        "route_5_unlock",
        "route_8_unlock",
    }
