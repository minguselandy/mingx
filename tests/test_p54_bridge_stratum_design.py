from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "runs" / "bridge-calibration-evidence-packet-selection-microtask-v1-dryrun.json"
DESIGN_PATH = ROOT / "docs" / "experiments" / "P54-new-bridge-stratum-design-v12.md"

REQUIRED_CONFIG_FIELDS = {
    "phase",
    "stratum_id",
    "task_family",
    "target_type",
    "model_tier",
    "materialization_policy",
    "decoding_policy",
    "candidate_slice_band",
    "block_size",
    "utility_metric",
    "logloss_measurement",
    "data_source_kind",
    "contamination_policy",
    "claim_gate",
    "diagnostic_threshold_contract",
    "operator_gates",
    "negative_controls",
    "expected_outputs",
    "claim_boundaries",
}

REQUIRED_NEGATIVE_CONTROLS = {
    "redundancy_heavy_cases",
    "pairwise_complementarity_cases",
    "underpowered_noisy_cases_expected_ambiguous_metric",
    "stale_bridge_witness_fail_closed",
    "mismatched_bridge_witness_fail_closed",
    "candidate_pool_hash_mismatch_paper_ineligible",
    "distractor_evidence_packets",
    "prerequisite_missing_cases",
    "qualifier_sensitive_cases",
    "source_conflict_cases",
}


def _config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_p54_dryrun_config_is_valid_and_complete() -> None:
    payload = _config()

    assert REQUIRED_CONFIG_FIELDS <= set(payload)
    assert payload["phase"] == "P54"
    assert payload["stratum_id"] == "evidence_packet_selection_microtask_v1"
    assert payload["task_family"] == "evidence_packet_selection_microtask_v1"
    assert payload["stratum_id"] != "bio_attribute"
    assert payload["block_size"]["maximum"] <= 2


def test_p54_dryrun_config_is_machine_neutral_and_does_not_enable_execution() -> None:
    text = CONFIG_PATH.read_text(encoding="utf-8")
    payload = _config()

    assert not re.search(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", text, re.I)
    assert not re.search(r"\b20\d{2}-\d{2}-\d{2}(?:t|\s)\d{2}:\d{2}", text, re.I)
    assert "C:\\" not in text
    assert "/Users/" not in text
    assert "\\Users\\" not in text
    assert "api_key" not in text.lower()
    assert "secret" not in text.lower()

    gates = payload["operator_gates"]
    assert gates["p55_execution_default"] == "blocked_until_independent_review_and_operator_approval"
    assert gates["imported_rows_allowed"] is False
    assert gates["live_api_allowed"] is False
    assert gates["human_labeled_rows_allowed"] is False


def test_p54_claim_gate_blocks_current_phase_claim_upgrades() -> None:
    payload = _config()
    gate = payload["claim_gate"]
    ceiling = gate["p54_claim_ceiling"]

    assert ceiling["metric_claim_level_max"] == "none"
    assert ceiling["selector_regime_label_max"] == "none"
    assert ceiling["paper_evidence_eligible"] is False
    assert ceiling["measurement_validation_claim"] is False
    assert "measurement_validated" in gate["blocked_claims"]
    assert "current_p45_bio_attribute_as_calibrated_proxy_supported" in gate["blocked_claims"]
    assert gate["calibrated_proxy_supported_allowed_in_p54"] is False
    assert gate["vinfo_proxy_supported_allowed_in_p54"] is False
    assert gate["calibrated_proxy_supported_allowed_in_p55_only_if_all_future_gates_pass"] is True


def test_p54_negative_controls_and_p53_contract_reference_are_present() -> None:
    payload = _config()

    assert REQUIRED_NEGATIVE_CONTROLS <= set(payload["negative_controls"])
    contract = payload["diagnostic_threshold_contract"]
    assert contract["contract_reference"] == "docs/templates/diagnostic-threshold-contract-template.json"
    assert contract["protocol_reference"] == "docs/protocols/diagnostic-threshold-contract-v12.md"
    assert contract["required_for_p55"] is True
    assert contract["thresholds_may_be_changed_post_hoc"] is False


def test_p54_design_doc_selects_one_materially_new_stratum_without_claim_upgrade() -> None:
    text = DESIGN_PATH.read_text(encoding="utf-8")

    assert "Chosen stratum:" in text
    assert "evidence_packet_selection_microtask_v1" in text
    assert "P45 `bio_attribute` involved a closed/current stratum" in text
    assert "P54 is materially different" in text
    assert "P54 does not execute a bridge pilot" in text
    assert "P54 design as `calibrated_proxy_supported`" in text
    assert "P54 design as `vinfo_proxy_supported`" in text
