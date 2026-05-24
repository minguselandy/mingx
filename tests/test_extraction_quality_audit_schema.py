from __future__ import annotations

import json
from pathlib import Path

import pytest

from cps.extraction.audit_schema import (
    ALLOWED_EXTRACTION_LABELS,
    REQUIRED_EXTRACTION_STRATA,
    ExtractionAuditRecord,
    build_extraction_audit_manifest,
)
from tests.conftest import assert_importing_modules_does_not_load_forbidden_sdks


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_DOC = ROOT / "docs" / "experiments" / "extraction-quality-audit-protocol.md"


def _payload(**overrides):
    payload = {
        "record_id": "extract-1",
        "source_document_id": "doc-1",
        "source_document_hash": "doc-hash",
        "source_span_hash": "span-hash",
        "extracted_item_id": "item-1",
        "extracted_item_hash": "item-hash",
        "candidate_pool_hash": "pool-hash",
        "stratum": "qualifier_heavy",
        "label": "lost_qualifier",
        "label_source_kind": "model_adjudicated",
        "judge_model_snapshot": "static-judge-snapshot",
        "judge_prompt_hash": "prompt-hash",
        "rubric_version": "extraction_quality_audit_v1",
        "rubric_paraphrase_id": "p0",
        "order_swap": False,
        "duplicate_index": 0,
        "value_weight": 1.5,
        "selector_impact": "candidate_pool_risk_only",
        "raw_response_stored": False,
        "live_api_call_performed": False,
    }
    payload.update(overrides)
    return payload


def test_required_strata_and_labels_match_lapi7_contract() -> None:
    assert REQUIRED_EXTRACTION_STRATA == {
        "simple_factual",
        "complex_conditional",
        "qualifier_heavy",
        "temporal_scope",
        "cross_chunk",
        "long_tail_entity",
        "high_provenance_value",
        "prerequisite",
        "contradictory",
        "adversarial",
    }
    assert ALLOWED_EXTRACTION_LABELS == {
        "captured",
        "captured_core_preserved",
        "captured_core_materially_changed",
        "missing",
        "lost_qualifier",
        "temporal_scope_error",
        "provenance_loss",
        "selector_impact",
    }


def test_extraction_audit_record_serializes_audit_diagnostic_only() -> None:
    record = ExtractionAuditRecord.from_dict(_payload())
    payload = record.to_dict()

    assert payload["stratum"] == "qualifier_heavy"
    assert payload["label"] == "lost_qualifier"
    assert payload["allowed_claim_level"] == "model_adjudicated_extraction_risk_evidence"
    assert payload["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert payload["audit_diagnostic_only"] is True
    assert payload["measurement_validation_claim"] is False
    assert payload["metric_bridge_support"] is False
    assert payload["calibrated_proxy_supported"] is False
    assert payload["vinfo_proxy_supported"] is False
    assert payload["paper_evidence_eligible"] is False
    assert payload["selector_superiority_claim"] is False
    assert payload["route_5_locked"] is True
    assert payload["route_8_locked"] is True
    assert payload["raw_response_stored"] is False
    assert payload["live_api_call_performed"] is False
    assert '"raw_response":' not in json.dumps(payload, sort_keys=True)


def test_extraction_audit_record_rejects_invalid_labels_raw_storage_and_live_calls() -> None:
    with pytest.raises(ValueError, match="stratum"):
        ExtractionAuditRecord.from_dict(_payload(stratum="unknown"))

    with pytest.raises(ValueError, match="label"):
        ExtractionAuditRecord.from_dict(_payload(label="captured_exact"))

    with pytest.raises(ValueError, match="raw_response_stored"):
        ExtractionAuditRecord.from_dict(_payload(raw_response_stored=True))

    with pytest.raises(ValueError, match="raw_response"):
        ExtractionAuditRecord.from_dict(_payload(raw_response_body={"choices": []}))

    with pytest.raises(ValueError, match="live_api_call_performed"):
        ExtractionAuditRecord.from_dict(_payload(live_api_call_performed=True))

    with pytest.raises(ValueError, match="measurement_validation_claim"):
        ExtractionAuditRecord.from_dict(_payload(measurement_validation_claim=True))


def test_extraction_audit_manifest_is_deterministic_and_controlled() -> None:
    items = [{"item_id": "b"}, {"item_id": "a"}]
    first = build_extraction_audit_manifest(run_id="extract-audit", items=items)
    second = build_extraction_audit_manifest(run_id="extract-audit", items=reversed(items))

    assert first == second
    assert first["run_id"] == "extract-audit"
    assert first["extraction_quality_audit_version"] == "v1_model_adjudicated_only"
    assert first["required_strata"] == sorted(REQUIRED_EXTRACTION_STRATA)
    assert first["allowed_labels"] == sorted(ALLOWED_EXTRACTION_LABELS)
    assert first["controls"]["frozen_prompts"] is True
    assert first["controls"]["prompt_hashes_required"] is True
    assert first["controls"]["duplicate_judging"] is True
    assert first["controls"]["order_swap"] is True
    assert first["controls"]["raw_response_stored"] is False
    assert first["live_api_call_performed"] is False
    assert first["human_sentinel_audit"]["enabled_now"] is False
    assert first["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert [item["item_id"] for item in first["items"]] == ["a", "b"]


def test_protocol_doc_documents_future_optional_human_sentinel_only() -> None:
    text = PROTOCOL_DOC.read_text(encoding="utf-8").lower()

    assert "model_adjudicated_extraction_risk_evidence" in text
    assert "operational_utility_only/no_claim_upgrade" in text
    assert "human sentinel" in text
    assert "future optional" in text
    assert "enabled now: false" in text
    assert "not current evidence" in text
    assert "not measurement validation" in text
    assert "not metric bridge support" in text
    assert "route 5 locked" in text
    assert "route 8 locked" in text


def test_extraction_import_does_not_load_live_api_sdks() -> None:
    assert_importing_modules_does_not_load_forbidden_sdks(
        ["cps.extraction.audit_schema", "cps.extraction.extraction_risk_ledger"]
    )
