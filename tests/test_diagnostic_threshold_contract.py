from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "docs" / "templates" / "diagnostic-threshold-contract-template.json"
PROTOCOL_PATH = ROOT / "docs" / "protocols" / "diagnostic-threshold-contract-v12.md"

REQUIRED_TOP_LEVEL_FIELDS = {
    "contract_id",
    "contract_schema_version",
    "calibration_epoch",
    "active_stratum",
    "metric_claim_level_precondition",
    "block_size_max",
    "signal_threshold",
    "ratio_lcb_method",
    "ratio_quantile",
    "ratio_lcb_threshold",
    "pairwise_excess_threshold",
    "sag_gap_threshold",
    "triple_excess_threshold",
    "min_effective_sample_size",
    "drift_policy",
    "underpowered_policy",
    "fixture_policy",
    "synthetic_policy",
    "decision_logic",
    "claim_boundary",
    "paper_evidence_policy",
}

REQUIRED_ACTIVE_STRATUM_FIELDS = {
    "task_family",
    "model_tier",
    "materialization_policy",
    "block_size",
    "candidate_slice",
    "metric",
    "data_source_kind",
}

DEPRECATED_LABELS = {
    "Vinfo_proxy_certified",
    "greedy_valid",
    "measurement_validated",
}


def _template() -> dict:
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


def test_diagnostic_threshold_contract_template_is_valid_json_and_has_required_fields() -> None:
    payload = _template()

    assert REQUIRED_TOP_LEVEL_FIELDS <= set(payload)
    assert REQUIRED_ACTIVE_STRATUM_FIELDS <= set(payload["active_stratum"])
    assert isinstance(payload["contract_schema_version"], str)
    assert payload["contract_schema_version"].startswith("diagnostic_threshold_contract.v12.")
    assert not any(label in TEMPLATE_PATH.read_text(encoding="utf-8") for label in DEPRECATED_LABELS)


def test_diagnostic_threshold_contract_template_is_stable_and_machine_neutral() -> None:
    text = TEMPLATE_PATH.read_text(encoding="utf-8")

    assert not re.search(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", text, re.I)
    assert not re.search(r"\b20\d{2}-\d{2}-\d{2}(?:t|\s)\d{2}:\d{2}", text, re.I)
    assert "C:\\" not in text
    assert "/Users/" not in text
    assert "\\Users\\" not in text


def test_drift_underpowered_fixture_and_synthetic_policies_fail_closed() -> None:
    payload = _template()

    assert set(payload["drift_policy"]) == {"fresh", "stale", "ambiguous", "missing", "mismatched"}
    for status in ("stale", "ambiguous", "missing", "mismatched"):
        assert payload["drift_policy"][status]["metric_claim_level"] == "ambiguous_metric"
        assert payload["drift_policy"][status]["selector_regime_label"] == "ambiguous"

    underpowered = payload["underpowered_policy"]
    assert underpowered["if_effective_sample_size_below_min"]["metric_claim_level"] == "ambiguous_metric"
    assert underpowered["if_effective_sample_size_below_min"]["selector_regime_label"] == "ambiguous"
    assert set(underpowered["allowed_fail_closed_outputs"]) == {
        "ambiguous",
        "ambiguous_metric",
        "operational_utility_only",
    }

    for policy_name in ("fixture_policy", "synthetic_policy"):
        policy = payload[policy_name]
        assert policy["paper_evidence_eligible"] is False
        assert "vinfo_proxy_supported" in policy["cannot_emit_metric_claim_levels"]
        assert "calibrated_proxy_supported" in policy["cannot_emit_metric_claim_levels"]


def test_threshold_values_are_numeric_or_explicitly_fail_closed_when_inactive() -> None:
    payload = _template()

    for field in ("block_size_max", "ratio_quantile", "ratio_lcb_threshold", "pairwise_excess_threshold", "sag_gap_threshold"):
        assert isinstance(payload[field], int | float)

    for field in ("signal_threshold", "triple_excess_threshold"):
        threshold = payload[field]
        assert threshold["inactive"] is False
        assert isinstance(threshold["value"], int | float)
        assert threshold["null_behavior"] == "fail_closed_to_ambiguous"

    assert isinstance(payload["min_effective_sample_size"], int)
    assert payload["threshold_policy"]["null_threshold_allowed_only_when_gate_inactive"] is True
    assert payload["threshold_policy"]["inactive_gate_must_fail_closed"] is True
    assert payload["threshold_policy"]["missing_threshold_interpreted_post_hoc"] is False


def test_decision_logic_precedence_blocks_late_upgrades() -> None:
    payload = _template()
    decision_logic = payload["decision_logic"]

    assert decision_logic["precedence_order"] == [
        "hard_claim_boundary_failures",
        "metric_bridge_missing_stale_mismatched_underpowered",
        "fixture_only_or_synthetic_only_restrictions",
        "signal_denominator_and_effective_sample_size_checks",
        "triple_or_higher_order_risk_checks",
        "pairwise_escalation_checks",
        "greedy_supported_checks",
        "ambiguous_fallback",
    ]

    bridge_rule = next(rule for rule in decision_logic["rules"] if rule["name"] == "metric_bridge_fail_closed")
    assert bridge_rule["metric_claim_level"] == "ambiguous_metric"
    assert bridge_rule["selector_regime_label"] == "ambiguous"
    assert set(bridge_rule["denied_metric_claim_levels"]) == {
        "vinfo_proxy_supported",
        "calibrated_proxy_supported",
    }


def test_metric_bridge_witness_semantics_and_claim_boundaries_are_conservative() -> None:
    payload = _template()
    semantics = payload["metric_bridge_witness_semantics"]
    boundary = payload["claim_boundary"]

    assert semantics["presence_is_not_support"] is True
    assert semantics["stale_missing_mismatched_underpowered_or_failed_witness_downgrades_claims"] is True
    assert semantics["replay_usability_does_not_imply_metric_support"] is True
    assert "replay_completeness" in semantics["do_not_infer_bridge_from"]
    assert "model_adjudicated_labels" in semantics["do_not_infer_bridge_from"]

    assert boundary["metric_claim_level_max_for_template"] == "none"
    assert boundary["selector_regime_label_max_for_template"] == "none"
    assert boundary["contract_is_bridge_evidence"] is False
    assert boundary["contract_is_validation"] is False
    assert boundary["measurement_validation_claim"] is False
    assert boundary["deployed_v_information_verification_claim"] is False
    assert boundary["current_p45_bio_attribute_calibrated_proxy_supported"] is False


def test_protocol_doc_declares_scaffold_not_validation_and_required_semantics() -> None:
    text = PROTOCOL_PATH.read_text(encoding="utf-8")

    for required in (
        "The diagnostic threshold contract is a pre-registration / audit artifact.",
        "It is not bridge evidence.",
        "It is not validation.",
        "It does not by itself authorize `vinfo_proxy_supported` or `calibrated_proxy_supported`.",
        "Fixture-only evidence cannot emit `vinfo_proxy_supported`.",
        "Fixture-only evidence cannot emit `calibrated_proxy_supported`.",
        "Synthetic-only evidence cannot emit `vinfo_proxy_supported`.",
        "Synthetic-only evidence cannot emit `calibrated_proxy_supported`.",
        "`MetricBridgeWitness` presence is not automatically bridge support.",
        "Replay usability does not imply metric support.",
        "current P45 `bio_attribute` stratum as `calibrated_proxy_supported`",
    ):
        assert required in text
