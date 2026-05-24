from __future__ import annotations

import json

import pytest

from cps.replay.reprojection_witness import (
    ALLOWED_REPROJECTION_INTERVENTIONS,
    CONTROLLED_REPLAY_HOLD_FIXED_FIELDS,
    ReprojectionWitness,
    build_reprojection_manifest,
)
from tests.conftest import assert_importing_modules_does_not_load_forbidden_sdks


def _witness_payload(**overrides):
    payload = {
        "witness_id": "rw-1",
        "item_id": "item-1",
        "trigger_label": "insufficient_and_answered",
        "intervention_type": "restore_excluded_evidence_span",
        "downstream_prompt_template_hash": "downstream-hash",
        "model_snapshot": "static-model-snapshot",
        "endpoint": "static-endpoint",
        "thinking_mode": "disabled",
        "decoding_policy": {"temperature": 0, "top_p": 1},
        "token_budget_accounting_method": "offline_token_estimate_v1",
        "original_budget_tokens": 100,
        "reprojected_budget_tokens": 132,
        "selector_before": "greedy",
        "selector_after": "pair_aware_local_search",
        "context_hash_before": "context-before",
        "context_hash_after": "context-after",
        "context_diff_hash": "context-diff",
        "before_output_hash": "before-output",
        "after_output_hash": "after-output",
        "repair_status": "reprojection_candidate",
        "position_aware_replay_manifest": {
            "enabled": True,
            "original_position_ids": ["e1"],
            "reprojected_position_ids": ["e1", "e2"],
            "position_policy_hash": "position-policy",
        },
        "raw_response_stored": False,
        "live_api_call_performed": False,
    }
    payload.update(overrides)
    return payload


def test_reprojection_constants_encode_goal_controls() -> None:
    assert CONTROLLED_REPLAY_HOLD_FIXED_FIELDS == {
        "downstream_prompt_template_hash",
        "model_snapshot",
        "endpoint",
        "thinking_mode",
        "decoding_policy",
        "token_budget_accounting_method",
    }
    assert ALLOWED_REPROJECTION_INTERVENTIONS == {
        "restore_excluded_evidence_span",
        "expand_budget_with_budget_delta_recorded",
        "switch_selector_to_pair_aware_local_search",
        "switch_selector_to_seeded_augmented_greedy",
    }


def test_reprojection_witness_serializes_required_projection_bundle_fields() -> None:
    witness = ReprojectionWitness.from_dict(_witness_payload())
    payload = witness.to_dict()

    for field in {
        "trigger_label",
        "budget_delta",
        "selector_change",
        "context_diff_hash",
        "before_output_hash",
        "after_output_hash",
        "repair_status",
    }:
        assert field in payload

    assert payload["budget_delta"] == 32
    assert payload["selector_change"] == {
        "before": "greedy",
        "after": "pair_aware_local_search",
    }
    assert payload["controlled_replay"]["downstream_prompt_template_hash"] == "downstream-hash"
    assert payload["raw_response_stored"] is False
    assert payload["live_api_call_performed"] is False
    assert payload["candidate_operational_evidence_only"] is True
    assert payload["measurement_validation_claim"] is False
    assert payload["route_5_locked"] is True
    assert payload["route_8_locked"] is True
    assert '"raw_response":' not in json.dumps(payload, sort_keys=True)


def test_reprojection_witness_serializes_with_claim_ledger() -> None:
    witness = ReprojectionWitness.from_dict(_witness_payload())
    payload = witness.to_dict(include_claim_ledger=True)

    claim_ledger = payload["claim_ledger"]
    assert claim_ledger["current_claim_level"] == "operational_utility_only/no_claim_upgrade"
    assert claim_ledger["allowed_claims"] == ["sufficiency_abstention_diagnostic_only"]
    assert "measurement_validation" in claim_ledger["denied_claims"]
    assert claim_ledger["claim_upgrade"] is False
    assert claim_ledger["route_5_locked"] is True
    assert claim_ledger["route_8_locked"] is True
    assert claim_ledger["raw_response_stored"] is False


def test_reprojection_witness_rejects_raw_or_live_outputs_and_invalid_controls() -> None:
    with pytest.raises(ValueError, match="raw_response_stored"):
        ReprojectionWitness.from_dict(_witness_payload(raw_response_stored=True))

    with pytest.raises(ValueError, match="raw_response"):
        ReprojectionWitness.from_dict(_witness_payload(raw_response_body="forbidden"))

    with pytest.raises(ValueError, match="live_api_call_performed"):
        ReprojectionWitness.from_dict(_witness_payload(live_api_call_performed=True))

    with pytest.raises(ValueError, match="intervention_type"):
        ReprojectionWitness.from_dict(_witness_payload(intervention_type="freeform_rewrite"))


def test_reprojection_manifest_is_deterministic_offline_and_position_aware() -> None:
    first = build_reprojection_manifest(
        run_id="reprojection-offline",
        items=[
            {"item_id": "b", "trigger_label": "hallucination_risk"},
            {"item_id": "a", "trigger_label": "sufficient_dropped"},
        ],
        downstream_prompt_template_hash="downstream-hash",
        model_snapshot="static-model-snapshot",
        endpoint="static-endpoint",
        thinking_mode="disabled",
        decoding_policy={"temperature": 0, "top_p": 1},
    )
    second = build_reprojection_manifest(
        run_id="reprojection-offline",
        items=reversed(
            [
                {"item_id": "b", "trigger_label": "hallucination_risk"},
                {"item_id": "a", "trigger_label": "sufficient_dropped"},
            ]
        ),
        downstream_prompt_template_hash="downstream-hash",
        model_snapshot="static-model-snapshot",
        endpoint="static-endpoint",
        thinking_mode="disabled",
        decoding_policy={"temperature": 0, "top_p": 1},
    )

    assert first == second
    assert first["live_api_call_performed"] is False
    assert first["raw_response_stored"] is False
    assert first["position_aware_replay"]["enabled"] is True
    assert first["controlled_replay"]["hold_fixed"] == sorted(
        CONTROLLED_REPLAY_HOLD_FIXED_FIELDS
    )
    assert first["controlled_replay"]["downstream_prompt_template_hash"] == "downstream-hash"
    assert first["pilot_readiness_status"] == "offline_framework_ready_live_api_not_run"
    assert [item["item_id"] for item in first["items"]] == ["a", "b"]


def test_reprojection_import_does_not_load_live_api_sdks() -> None:
    assert_importing_modules_does_not_load_forbidden_sdks(["cps.replay.reprojection_witness"])
