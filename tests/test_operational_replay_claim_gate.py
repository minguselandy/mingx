from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATHS = (
    ROOT / "configs" / "experiments" / "hotpotqa_operational_replay_v1.yaml",
    ROOT / "configs" / "experiments" / "fever_style_sufficiency_v1.yaml",
)

DENIED_CLAIMS = {
    "selector_superiority",
    "global_selector_superiority",
    "measurement_validation",
    "metric_bridge_support",
    "calibrated_proxy_supported",
    "vinfo_proxy_supported",
    "paper_evidence",
    "route_5_unlock",
    "route_8_unlock",
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_claim_gate_preserves_live_api_boundary_for_each_replay_config() -> None:
    for path in CONFIG_PATHS:
        config = _load(path)
        claim = config["claim_boundary"]

        assert claim["current_claim_level"] == "operational_utility_only/no_claim_upgrade"
        assert claim["claim_level"] == "scoped_operational_improvement_under_matched_budgets_only"
        assert claim["allowed_claims"] == [
            "scoped_operational_improvement_under_matched_budgets_only"
        ]
        assert set(claim["denied_claims"]) >= DENIED_CLAIMS
        assert claim["claim_upgrade"] is False
        assert claim["route_5_locked"] is True
        assert claim["route_8_locked"] is True
        assert claim["raw_response_stored"] is False
        assert claim["live_api_call_performed"] is False
        assert claim["paper_evidence_eligible"] is False


def test_reporting_rules_fail_closed_on_forbidden_claims() -> None:
    for path in CONFIG_PATHS:
        reporting = _load(path)["reporting_rules"]

        assert reporting["compare_only_with_matched_candidate_pool_budget_prompt_and_model_snapshot"] is True
        assert reporting["report_oracle_only_as_non_deployable_upper_bound"] is True
        assert reporting["never_report_selector_superiority"] is True
        assert reporting["never_report_global_selector_superiority"] is True
        assert reporting["never_report_metric_bridge_support"] is True
        assert reporting["never_report_measurement_validation"] is True
        assert reporting["never_report_calibrated_proxy_support"] is True
        assert reporting["never_report_vinfo_proxy_support"] is True
        assert reporting["never_report_paper_evidence"] is True
        assert reporting["never_report_route_5_or_route_8_unlock"] is True


def test_stop_conditions_guard_matched_budget_and_claim_ledger_integrity() -> None:
    for path in CONFIG_PATHS:
        stop_conditions = set(_load(path)["stop_conditions"])

        assert stop_conditions >= {
            "parse_failure_rate_exceeds_0_15",
            "budget_mismatch_detected",
            "prompt_hash_drift_detected",
            "claim_ledger_missing_or_incomplete",
            "candidate_pool_mismatch_detected",
            "model_snapshot_mismatch_detected",
            "live_api_call_attempted_without_explicit_approval",
            "raw_response_storage_detected",
        }


def test_config_text_has_no_active_upgrade_language() -> None:
    for path in CONFIG_PATHS:
        text = path.read_text(encoding="utf-8").lower()

        for forbidden in (
            '"selector_superiority": true',
            '"global_selector_superiority": true',
            '"measurement_validation": true',
            '"metric_bridge_support": true',
            '"calibrated_proxy_supported": true',
            '"vinfo_proxy_supported": true',
            '"paper_evidence": true',
            '"route_5_locked": false',
            '"route_8_locked": false',
            '"claim_upgrade": true',
            '"raw_response_stored": true',
            '"live_api_call_performed": true',
            "replay completed",
            "experiment completed",
        ):
            assert forbidden not in text
