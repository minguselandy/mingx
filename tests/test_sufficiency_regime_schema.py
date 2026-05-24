from __future__ import annotations

import json
from pathlib import Path

import pytest

from cps.evaluation.sufficiency_regime import (
    ALLOWED_SUFFICIENCY_TRIGGERS,
    REQUIRED_REGIME_LABELS,
    SufficiencyRegimeRecord,
    build_sufficiency_manifest,
    classify_sufficiency_regime,
)
from tests.conftest import assert_importing_modules_does_not_load_forbidden_sdks


def _payload(**overrides):
    payload = {
        "record_id": "suff-1",
        "item_id": "item-1",
        "judge_label": "support",
        "projected_evidence_sufficient": True,
        "answer_emitted": True,
        "abstained": False,
        "missing_evidence_types": [],
        "input_token_count": 64,
        "output_token_count": 8,
        "raw_response_stored": False,
        "live_api_call_performed": False,
    }
    payload.update(overrides)
    return payload


def test_required_regime_labels_and_triggers_are_exact_protocol_values() -> None:
    assert REQUIRED_REGIME_LABELS == {
        "sufficient_kept",
        "sufficient_dropped",
        "insufficient_and_answered",
        "insufficient_and_abstained",
    }
    assert ALLOWED_SUFFICIENCY_TRIGGERS == {
        "sufficient_dropped",
        "insufficient_and_answered",
        "unknown_due_to_missing_context",
        "hallucination_risk",
    }


def test_classify_sufficiency_regime_covers_required_offline_states() -> None:
    assert classify_sufficiency_regime(_payload())["regime_label"] == "sufficient_kept"
    assert (
        classify_sufficiency_regime(
            _payload(answer_emitted=False, omitted_evidence_necessary=True)
        )["regime_label"]
        == "sufficient_dropped"
    )
    assert (
        classify_sufficiency_regime(
            _payload(projected_evidence_sufficient=False, judge_label="insufficient")
        )["regime_label"]
        == "insufficient_and_answered"
    )
    assert (
        classify_sufficiency_regime(
            _payload(
                projected_evidence_sufficient=False,
                answer_emitted=False,
                abstained=True,
                judge_label="uncertain",
                missing_evidence_types=["bridge_fact"],
            )
        )["regime_label"]
        == "insufficient_and_abstained"
    )


def test_sufficiency_record_serializes_operational_candidate_evidence_only() -> None:
    record = SufficiencyRegimeRecord.from_dict(
        _payload(
            projected_evidence_sufficient=False,
            judge_label="contradict",
            missing_evidence_types=["entity", "unknown"],
        )
    )
    payload = record.to_dict()

    assert payload["regime_label"] == "insufficient_and_answered"
    assert payload["trigger_label"] == "hallucination_risk"
    assert payload["claim_level"] == "sufficiency_abstention_diagnostic_only"
    assert payload["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert payload["candidate_operational_evidence_only"] is True
    assert payload["measurement_validation_claim"] is False
    assert payload["human_external_gold_label"] is False
    assert payload["raw_response_stored"] is False
    assert payload["live_api_call_performed"] is False
    assert payload["route_5_locked"] is True
    assert payload["route_8_locked"] is True
    assert '"raw_response":' not in json.dumps(payload, sort_keys=True)


def test_sufficiency_record_rejects_raw_response_storage_or_live_api_claims() -> None:
    with pytest.raises(ValueError, match="raw_response_stored"):
        SufficiencyRegimeRecord.from_dict(_payload(raw_response_stored=True))

    with pytest.raises(ValueError, match="raw_response"):
        SufficiencyRegimeRecord.from_dict(_payload(raw_response={"choices": []}))

    with pytest.raises(ValueError, match="live_api_call_performed"):
        SufficiencyRegimeRecord.from_dict(_payload(live_api_call_performed=True))


def test_sufficiency_manifest_is_static_and_hashes_prompt_assets() -> None:
    manifest = build_sufficiency_manifest(
        run_id="sufficiency-offline",
        items=[{"item_id": "b"}, {"item_id": "a"}],
        downstream_prompt_template_hash="downstream-hash",
    )
    second = build_sufficiency_manifest(
        run_id="sufficiency-offline",
        items=reversed([{"item_id": "b"}, {"item_id": "a"}]),
        downstream_prompt_template_hash="downstream-hash",
    )

    assert manifest == second
    assert manifest["run_id"] == "sufficiency-offline"
    assert manifest["protocol_version"] == "v1_operational_only"
    assert manifest["live_api_call_performed"] is False
    assert manifest["raw_response_stored"] is False
    assert manifest["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert manifest["route_5_locked"] is True
    assert manifest["route_8_locked"] is True
    assert manifest["pilot_readiness_status"] == "offline_framework_ready_live_api_not_run"
    assert "prompts/reprojection/sufficiency_abstention_v1.md" in manifest["prompt_hashes"]
    assert [item["item_id"] for item in manifest["items"]] == ["a", "b"]


def test_prompt_and_doc_pin_operational_boundary() -> None:
    prompt = Path("prompts/reprojection/sufficiency_abstention_v1.md").read_text(
        encoding="utf-8"
    ).lower()
    doc = Path(
        "docs/experiments/sufficiency-abstention-reprojection-protocol.md"
    ).read_text(encoding="utf-8").lower()

    for text in (prompt, doc):
        assert "sufficiency_abstention_diagnostic_only" in text
        assert "operational_utility_only/no_claim_upgrade" in text
        assert "route 5 locked" in text
        assert "route 8 locked" in text
        assert "not measurement validation" in text
        assert "raw response" not in text


def test_sufficiency_import_does_not_load_live_api_sdks() -> None:
    assert_importing_modules_does_not_load_forbidden_sdks(
        ["cps.evaluation.sufficiency_regime"]
    )
