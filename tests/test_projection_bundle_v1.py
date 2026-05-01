import json

import pytest

from cps.experiments.artifacts import (
    BudgetWitness,
    CandidatePool,
    MaterializedContext,
    MetricBridgeWitness,
    ProjectionDiagnostics,
    ProjectionPlan,
)
from cps.schema import ProjectionBundleV1, projection_bundle_from_dict


def _minimal_payload():
    return {
        "run_id": "run-1",
        "dispatch_id": "dispatch-1",
        "agent_id": "agent-a",
        "round_id": "round-1",
        "candidate_pool": {
            "dispatch_id": "dispatch-1",
            "agent_id": "agent-a",
            "round_id": "round-1",
            "items": [{"item_id": "a", "metadata": {"b": 2, "a": 1}}],
        },
        "projection_plan": {
            "dispatch_id": "dispatch-1",
            "agent_id": "agent-a",
            "round_id": "round-1",
            "selected_ids": ["a"],
            "score_config": {"beta": 2, "alpha": 1},
        },
        "budget_witness": {
            "dispatch_id": "dispatch-1",
            "agent_id": "agent-a",
            "round_id": "round-1",
            "within_budget": True,
        },
        "materialized_context": {
            "dispatch_id": "dispatch-1",
            "agent_id": "agent-a",
            "round_id": "round-1",
            "content": "[a]\nA",
        },
        "metric_bridge_witness": {
            "dispatch_id": "dispatch-1",
            "agent_id": "agent-a",
            "round_id": "round-1",
            "diagnostic_claim_level": "structural_synthetic_only",
        },
        "source_mode": "mock",
    }


def _reordered_payload():
    payload = _minimal_payload()
    payload["candidate_pool"] = {
        "items": [{"metadata": {"a": 1, "b": 2}, "item_id": "a"}],
        "round_id": "round-1",
        "agent_id": "agent-a",
        "dispatch_id": "dispatch-1",
    }
    payload["projection_plan"] = {
        "score_config": {"alpha": 1, "beta": 2},
        "selected_ids": ["a"],
        "round_id": "round-1",
        "agent_id": "agent-a",
        "dispatch_id": "dispatch-1",
    }
    return payload


def _artifact_dataclasses():
    return {
        "candidate_pool": CandidatePool(
            dispatch_id="dispatch-1",
            agent_id="agent-a",
            round_id="round-1",
            regime="redundancy_dominated",
            budget_tokens=10,
            items=[{"item_id": "a", "token_cost": 5, "text": "A", "singleton_value": 1.0}],
            candidate_pool_hash="pool-hash",
        ),
        "projection_plan": ProjectionPlan(
            dispatch_id="dispatch-1",
            agent_id="agent-a",
            round_id="round-1",
            regime="redundancy_dominated",
            algorithm="greedy",
            budget_tokens=10,
            candidate_pool_hash="pool-hash",
            selected_ids=["a"],
            excluded_ids=[],
            trace=[],
            score_config={},
        ),
        "budget_witness": BudgetWitness(
            dispatch_id="dispatch-1",
            agent_id="agent-a",
            round_id="round-1",
            regime="redundancy_dominated",
            budget_tokens=10,
            estimated_tokens=5,
            realized_tokens=5,
            within_budget=True,
            selected_ids=["a"],
            excluded_ids=[],
            tolerance_violations=[],
        ),
        "materialized_context": MaterializedContext(
            dispatch_id="dispatch-1",
            agent_id="agent-a",
            round_id="round-1",
            regime="redundancy_dominated",
            selected_ids=["a"],
            section_order=["a"],
            content="[a]\nA",
            token_count=5,
            context_hash="context-hash",
        ),
        "metric_bridge_witness": MetricBridgeWitness(
            dispatch_id="dispatch-1",
            agent_id="agent-a",
            round_id="round-1",
            regime="redundancy_dominated",
            calibration_epoch=None,
            active_stratum={"regime": "redundancy_dominated"},
            model_tier=None,
            utility_metric="synthetic_oracle_value",
            metric_class="synthetic_oracle",
            materialization_policy={"algorithm": "greedy"},
            decoding_policy={"mode": "not_applicable"},
            bridge_scale=None,
            bridge_residual_zeta=None,
            effective_sample_size=None,
            drift_status="not_applicable",
            diagnostic_mode="synthetic_oracle",
            diagnostic_claim_level="structural_synthetic_only",
        ),
        "diagnostics": ProjectionDiagnostics(
            dispatch_id="dispatch-1",
            agent_id="agent-a",
            round_id="round-1",
            regime="redundancy_dominated",
            block_ratio_lcb_b2=1.0,
            block_ratio_lcb_star=1.0,
            block_ratio_lcb_star_semantics="placeholder_conservative_min_b2_b3_not_degree_adaptive_star",
            block_ratio_lcb_b3=None,
            block_ratio_uninformative_count=0,
            block_ratio_sample_count=1,
            trace_decay_proxy=1.0,
            gamma_hat=1.0,
            synergy_fraction=0.0,
            positive_interaction_mass_ucb=0.0,
            triple_excess_lcb_max=None,
            triple_excess_flag="not_evaluable",
            higher_order_ambiguity_flag=False,
            greedy_augmented_gap=0.0,
            metric_claim_level="structural_synthetic_only",
            selector_regime_label="greedy_valid",
            selector_action="monitored_greedy",
            policy_recommendation="monitored_greedy",
            greedy_value=1.0,
            augmented_value=1.0,
            local_search_value=1.0,
            pairwise_samples=[],
            block_ratio_samples=[],
            triple_samples=[],
            thresholds={},
            notes="fixture",
        ),
    }


def test_constructs_from_minimal_dict_artifact_payloads():
    bundle = ProjectionBundleV1.from_dict(_minimal_payload())

    payload = bundle.to_dict()

    assert payload["bundle_version"] == "ProjectionBundleV1"
    assert payload["run_id"] == "run-1"
    assert payload["source_mode"] == "mock"
    assert "diagnostics" not in payload


def test_roundtrip_preserves_canonical_json():
    bundle = ProjectionBundleV1.from_dict(_minimal_payload())
    roundtripped = projection_bundle_from_dict(bundle.to_dict())

    assert roundtripped.to_canonical_json() == bundle.to_canonical_json()


def test_canonical_json_is_stable_under_reordered_input_keys():
    first = ProjectionBundleV1.from_dict(_minimal_payload())
    second = ProjectionBundleV1.from_dict(_reordered_payload())

    assert first.to_canonical_json() == second.to_canonical_json()


def test_canonical_hash_is_stable_under_reordered_input_keys():
    first = ProjectionBundleV1.from_dict(_minimal_payload())
    second = ProjectionBundleV1.from_dict(_reordered_payload())

    assert first.canonical_hash() == second.canonical_hash()


@pytest.mark.parametrize("field_name", ["run_id", "dispatch_id", "agent_id", "round_id"])
def test_missing_identity_fields_are_rejected(field_name):
    payload = _minimal_payload()
    payload.pop(field_name)

    with pytest.raises(ValueError, match=f"{field_name} is required"):
        ProjectionBundleV1.from_dict(payload)


@pytest.mark.parametrize("field_name", ["run_id", "dispatch_id", "agent_id", "round_id"])
def test_empty_identity_fields_are_rejected(field_name):
    payload = _minimal_payload()
    payload[field_name] = " "

    with pytest.raises(ValueError, match=f"{field_name} is required"):
        ProjectionBundleV1.from_dict(payload)


def test_optional_diagnostics_are_preserved_if_present():
    payload = _minimal_payload()
    payload["diagnostics"] = {"metric_claim_level": "structural_synthetic_only", "samples": []}

    bundle = ProjectionBundleV1.from_dict(payload)

    assert bundle.to_dict()["diagnostics"] == payload["diagnostics"]


def test_existing_artifact_dataclasses_can_be_serialized():
    payload = {
        "run_id": "run-1",
        "dispatch_id": "dispatch-1",
        "agent_id": "agent-a",
        "round_id": "round-1",
        **_artifact_dataclasses(),
    }

    bundle = ProjectionBundleV1(**payload)
    bundle_payload = bundle.to_dict()

    assert bundle_payload["candidate_pool"]["candidate_pool_hash"] == "pool-hash"
    assert bundle_payload["metric_bridge_witness"]["diagnostic_claim_level"] == "structural_synthetic_only"
    assert bundle_payload["diagnostics"]["metric_claim_level"] == "structural_synthetic_only"


def test_no_timestamps_or_uuids_are_introduced_by_default():
    payload = ProjectionBundleV1.from_dict(_minimal_payload()).to_dict()

    serialized = json.dumps(payload, sort_keys=True)

    assert "timestamp" not in serialized.lower()
    assert "uuid" not in serialized.lower()
    assert "created_at" not in serialized.lower()


def test_incoming_canonical_hash_is_preserved_but_excluded_from_computed_hash():
    payload = _minimal_payload()
    payload["canonical_hash"] = "incoming-hash"
    with_incoming = ProjectionBundleV1.from_dict(payload)

    without_incoming = ProjectionBundleV1.from_dict(_minimal_payload())

    assert with_incoming.to_dict()["canonical_hash"] == "incoming-hash"
    assert "incoming-hash" not in with_incoming.to_canonical_json()
    assert with_incoming.to_canonical_json() == without_incoming.to_canonical_json()
    assert with_incoming.canonical_hash() == without_incoming.canonical_hash()
