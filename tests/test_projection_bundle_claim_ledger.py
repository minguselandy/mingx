import pytest

from cps.artifacts.claim_ledger import ClaimLedger as ArtifactClaimLedger
from cps.artifacts.claim_ledger import CostLatencyLedger as ArtifactCostLatencyLedger
from cps.schema import ClaimLedger, CostLatencyLedger


def test_default_claim_ledger_denies_claim_upgrades_and_locks_routes():
    ledger = ClaimLedger.for_artifact_status("complete").to_dict()

    assert ledger["current_claim_level"] == "operational_utility_only/no_claim_upgrade"
    assert ledger["allowed_claims"] == ["replayable_artifact_evidence"]
    assert "metric_bridge_support" in ledger["denied_claims"]
    assert "measurement_validation" in ledger["denied_claims"]
    assert "vinfo_proxy_supported" in ledger["denied_claims"]
    assert "selector_superiority" in ledger["denied_claims"]
    assert ledger["claim_upgrade"] is False
    assert ledger["route_5_locked"] is True
    assert ledger["route_8_locked"] is True
    assert ledger["raw_response_stored"] is False
    assert ledger["human_external_gold_label"] is False


def test_goal_named_claim_ledger_module_reexports_schema_ledgers():
    assert ArtifactClaimLedger is ClaimLedger
    assert ArtifactCostLatencyLedger is CostLatencyLedger


def test_incomplete_artifact_claim_ledger_fails_closed():
    ledger = ClaimLedger.for_artifact_status("incomplete").to_dict()

    assert ledger["artifact_status"] == "incomplete"
    assert ledger["allowed_claims"] == []
    assert "no_aggregated_headline_claim" in ledger["denied_claims"]
    assert "replayable_artifact_evidence" not in ledger["denied_claims"]
    assert ledger["metric_claim_level"] == "operational_utility_only"


def test_claim_ledger_rejects_raw_response_storage():
    with pytest.raises(ValueError, match="raw_response_stored"):
        ClaimLedger.from_dict(
            {
                "artifact_status": "complete",
                "raw_response_stored": True,
                "human_external_gold_label": False,
            }
        )


def test_claim_ledger_requires_future_support_for_unlocks_or_validation_claims():
    with pytest.raises(ValueError, match="explicit future evidence"):
        ClaimLedger.from_dict(
            {
                "artifact_status": "complete",
                "raw_response_stored": False,
                "allowed_claims": ["measurement_validation"],
                "denied_claims": ["metric_bridge_support"],
                "claim_upgrade": True,
                "route_5_locked": False,
                "route_8_locked": False,
            }
        )


def test_claim_ledger_allows_future_support_only_when_explicitly_gated():
    ledger = ClaimLedger.from_dict(
        {
            "artifact_status": "complete",
            "raw_response_stored": False,
            "allowed_claims": ["replayable_artifact_evidence", "measurement_validation"],
            "denied_claims": ["metric_bridge_support"],
            "claim_upgrade": True,
            "route_5_locked": False,
            "route_8_locked": False,
            "supporting_future_evidence": {
                "controller_review_complete": True,
                "independent_review_complete": True,
                "accepted_evidence_package": "future-placeholder",
            },
        }
    ).to_dict()

    assert ledger["claim_upgrade"] is True
    assert ledger["supporting_future_evidence"]["controller_review_complete"] is True


def test_cost_latency_ledger_requires_consistent_token_totals():
    ledger = CostLatencyLedger.from_dict(
        {
            "input_tokens": 7,
            "output_tokens": 5,
            "total_tokens": 12,
            "estimated_cost": 0.01,
            "latency_ms": 99,
        }
    ).to_dict()

    assert ledger["total_tokens"] == 12

    with pytest.raises(ValueError, match="total_tokens"):
        CostLatencyLedger.from_dict(
            {
                "input_tokens": 7,
                "output_tokens": 5,
                "total_tokens": 11,
                "estimated_cost": 0.01,
                "latency_ms": 99,
            }
        )
