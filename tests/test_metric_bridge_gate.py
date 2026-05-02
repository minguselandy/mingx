from __future__ import annotations

import socket
from pathlib import Path

from cps.experiments.evidence_ledger import (
    REQUIRED_EVIDENCE_ARTIFACTS,
    build_evidence_ledger_from_summary,
)
from cps.experiments.metric_bridge_gate import evaluate_metric_bridge_gate


def _ledger(**overrides):
    summary = {
        "run_id": "run-bridge",
        "claim_level": "operational_utility_only",
        "artifact_counts": {name: 1 for name in REQUIRED_EVIDENCE_ARTIFACTS},
    }
    defaults = {
        "metric_bridge_witness_count": 1,
        "bridge_freshness": "fresh",
        "metric_class": "validated_bridge",
        "diagnostic_claim_level": "measurement_candidate",
        "human_labels_present": True,
        "kappa_present": True,
        "contamination_status": "passed",
        "evidence_mode": "operational_utility_only",
        "required_artifacts_present": True,
        "projection_bundle_count": 1,
        "measurement_validation_evidence_present": True,
        "p04_status": "ACCEPT",
        "p09_status": "BLOCKED_OPERATOR_REQUIRED",
    }
    defaults.update(overrides)
    return build_evidence_ledger_from_summary(summary, **defaults)


def test_missing_metric_bridge_witness_count_gives_missing_reason():
    gate = evaluate_metric_bridge_gate(_ledger(metric_bridge_witness_count=0))

    assert gate["bridge_gate_status"] == "missing_bridge"
    assert gate["allowed_bridge_claim_level"] == "ambiguous"
    assert "missing_metric_bridge" in gate["reason_codes"]
    assert gate["measurement_validated_allowed"] is False


def test_stale_bridge_freshness_gives_stale_reason():
    gate = evaluate_metric_bridge_gate(_ledger(bridge_freshness="stale"))

    assert gate["bridge_gate_status"] == "stale_bridge"
    assert gate["allowed_bridge_claim_level"] == "operational_utility_only"
    assert "stale_metric_bridge" in gate["reason_codes"]
    assert gate["measurement_validated_allowed"] is False


def test_missing_human_labels_denies_measurement_validated():
    gate = evaluate_metric_bridge_gate(_ledger(human_labels_present=False))

    assert "missing_human_labels" in gate["reason_codes"]
    assert gate["measurement_validated_allowed"] is False


def test_missing_kappa_denies_measurement_validated():
    gate = evaluate_metric_bridge_gate(_ledger(kappa_present=False))

    assert "missing_kappa" in gate["reason_codes"]
    assert gate["measurement_validated_allowed"] is False


def test_contamination_failed_forces_pilot_only():
    gate = evaluate_metric_bridge_gate(_ledger(contamination_status="failed"))

    assert gate["bridge_gate_status"] == "failed"
    assert gate["allowed_bridge_claim_level"] == "pilot_only"
    assert gate["reason_codes"][0] == "contamination_failed"
    assert gate["measurement_validated_allowed"] is False


def test_operational_only_metric_class_denies_measurement_validated():
    gate = evaluate_metric_bridge_gate(_ledger(metric_class="operational_only"))

    assert gate["allowed_bridge_claim_level"] == "operational_utility_only"
    assert "operational_metric_class_only" in gate["reason_codes"]
    assert gate["measurement_validated_allowed"] is False


def test_operational_utility_diagnostic_claim_denies_measurement_validated():
    gate = evaluate_metric_bridge_gate(_ledger(diagnostic_claim_level="operational_utility_only"))

    assert gate["allowed_bridge_claim_level"] == "operational_utility_only"
    assert "operational_diagnostic_claim_only" in gate["reason_codes"]
    assert gate["measurement_validated_allowed"] is False


def test_synthetic_evidence_denies_deployed_v_information_certification():
    gate = evaluate_metric_bridge_gate(_ledger(evidence_mode="synthetic_structural_only"))

    assert "deployed_v_information_certification" in gate["denied_claims"]
    assert "synthetic_only_not_deployed_certification" in gate["reason_codes"]
    assert gate["measurement_validated_allowed"] is False


def test_engineering_only_evidence_denies_scientific_validation():
    gate = evaluate_metric_bridge_gate(_ledger(evidence_mode="engineering_smoke_only"))

    assert "scientific_validation" in gate["denied_claims"]
    assert "engineering_evidence_only" in gate["reason_codes"]
    assert gate["measurement_validated_allowed"] is False


def test_complete_artifacts_alone_still_deny_measurement_validated():
    gate = evaluate_metric_bridge_gate(
        _ledger(
            human_labels_present=False,
            kappa_present=False,
            bridge_freshness="missing",
            evidence_mode="replayable_artifact_evidence",
        )
    )

    assert gate["allowed_bridge_claim_level"] in {"ambiguous", "operational_utility_only"}
    assert "complete_artifacts_not_validation" in gate["reason_codes"]
    assert gate["measurement_validated_allowed"] is False


def test_live_api_used_alone_still_denies_measurement_validated():
    gate = evaluate_metric_bridge_gate(_ledger(live_api_used=True, human_labels_present=False))

    assert "live_api_not_validation" in gate["reason_codes"]
    assert gate["measurement_validated_allowed"] is False


def test_external_runtime_used_alone_still_denies_measurement_validated():
    gate = evaluate_metric_bridge_gate(_ledger(external_runtime_used=True, human_labels_present=False))

    assert "external_runtime_not_validation" in gate["reason_codes"]
    assert gate["measurement_validated_allowed"] is False


def test_reason_code_ordering_is_stable():
    first = evaluate_metric_bridge_gate(
        _ledger(
            contamination_status="failed",
            human_labels_present=False,
            kappa_present=False,
            bridge_freshness="stale",
            evidence_mode="synthetic_structural_only",
        )
    )
    second = evaluate_metric_bridge_gate(
        _ledger(
            contamination_status="failed",
            human_labels_present=False,
            kappa_present=False,
            bridge_freshness="stale",
            evidence_mode="synthetic_structural_only",
        )
    )

    assert first["reason_codes"] == second["reason_codes"]
    assert first["reason_codes"] == sorted(first["reason_codes"], key=first["reason_code_order"].index)


def test_p04_and_p09_status_are_visible_in_gate_summary():
    gate = evaluate_metric_bridge_gate(_ledger(p04_status="BLOCKED_OPERATOR_REQUIRED"))

    assert gate["p04_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert gate["p09_status"] == "BLOCKED_OPERATOR_REQUIRED"
    assert "P04 remains BLOCKED_OPERATOR_REQUIRED" in gate["summary"]
    assert "P09 remains BLOCKED_OPERATOR_REQUIRED" in gate["summary"]


def test_metric_bridge_gate_does_not_use_network_or_reference(monkeypatch):
    real_open = Path.open

    def guarded_open(self, *args, **kwargs):
        if "reference" in self.parts:
            raise AssertionError(f"reference path must not be opened: {self}")
        return real_open(self, *args, **kwargs)

    def blocked_socket(*_args, **_kwargs):
        raise AssertionError("metric bridge gate must not open sockets")

    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(socket, "socket", blocked_socket)

    gate = evaluate_metric_bridge_gate(_ledger())

    assert gate["bridge_gate_status"] == "eligible_for_measurement_review"
