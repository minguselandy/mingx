from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from cps.replay.reprojection_witness import ReprojectionWitness, build_reprojection_manifest


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "post_lapi" / "reprojection_witness_config.yaml"
POST4_CONFIG_PATH = ROOT / "configs" / "post_lapi" / "sufficiency_abstention_config.yaml"
SCHEMA_PATH = ROOT / "schemas" / "post_lapi_reprojection_witness.schema.json"
CONFIG_DOC = ROOT / "docs" / "experiments" / "POST-LAPI-reprojection-witness-config.md"
TABLE_TEMPLATE = ROOT / "docs" / "paper" / "post-lapi-reprojection-witness-table-template.md"

ELIGIBLE_CASES = {
    "sufficient_dropped",
    "insufficient_and_answered",
    "high_missing_evidence_type_confidence",
    "replay_artifact_complete",
}
REQUIRED_CONTROL_FIELDS = {
    "downstream_prompt_hash",
    "model_snapshot",
    "endpoint",
    "thinking_mode",
    "decoding_policy",
    "token_budget_accounting",
    "selected_evidence_before_hash",
    "restored_evidence_hash",
    "context_diff_hash",
    "before_output_hash",
    "after_output_hash",
    "judge_prompt_hash",
    "claim_ledger_entry",
}
REQUIRED_METRICS = {
    "repair_rate",
    "label_change_rate",
    "abstain_to_support_rate",
    "unsupported_to_supported_rate",
    "cost_delta",
    "latency_delta",
    "position_sensitivity_rate",
}
ALLOWED_CLAIMS = {
    "operational_reprojection_witness",
    "omitted_evidence_operational_diagnostic",
    "replayable_artifact_evidence",
}
DENIED_CLAIMS = {
    "validated_repair",
    "truth_correction_guarantee",
    "metric_bridge_support",
    "selector_superiority",
}


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_post_lapi_reprojection_config_schema_docs_and_template_exist() -> None:
    assert CONFIG_PATH.exists()
    assert POST4_CONFIG_PATH.exists()
    assert SCHEMA_PATH.exists()
    assert CONFIG_DOC.exists()
    assert TABLE_TEMPLATE.exists()


def test_post_lapi_reprojection_config_pins_eligibility_controls_metrics_and_claims() -> None:
    config = _load_json(CONFIG_PATH)

    assert config["pilot_id"] == "post_lapi_reprojection_witness"
    assert set(config["eligible_cases"]) == ELIGIBLE_CASES
    assert set(config["eligible_regimes"]) == {"sufficient_dropped", "insufficient_and_answered"}
    assert set(config["required_control_fields"]) == REQUIRED_CONTROL_FIELDS
    assert set(config["metrics"]) == REQUIRED_METRICS
    assert set(config["claim"]["allowed"]) == ALLOWED_CLAIMS
    assert set(config["claim"]["denied"]) == DENIED_CLAIMS


def test_post_lapi_reprojection_config_is_config_only_and_claim_safe() -> None:
    config = _load_json(CONFIG_PATH)

    assert config["configuration_only_default"] is True
    assert config["live_api_calls_allowed_by_default"] is False
    assert config["controlled_replay_calls_allowed_by_default"] is False
    assert config["requires_explicit_approval_to_run"] is True
    assert config["claim_level"] == "operational_utility_only/no_claim_upgrade"
    assert config["diagnostic_claim_level"] == "operational_reprojection_witness"
    assert config["route_5_locked"] is True
    assert config["route_8_locked"] is True
    assert config["raw_response_storage_allowed"] is False
    assert config["raw_response_stored"] is False
    assert config["controlled_replay_defaults"]["raw_response_stored"] is False
    assert config["controlled_replay_defaults"]["live_api_call_performed"] is False
    assert config["controlled_replay_defaults"]["controlled_replay_call_performed"] is False
    assert config["output_policy"]["store_raw_api_responses"] is False
    assert config["output_policy"]["measurement_validation_claim"] is False
    assert config["output_policy"]["truth_correction_guarantee"] is False
    assert config["output_policy"]["validated_repair_claim"] is False
    assert config["output_policy"]["claim_upgrade_introduced"] is False


def test_post_lapi_reprojection_schema_pins_fail_closed_config_contract() -> None:
    schema = _load_json(SCHEMA_PATH)

    assert schema["properties"]["pilot_id"]["const"] == "post_lapi_reprojection_witness"
    assert schema["properties"]["configuration_only_default"]["const"] is True
    assert schema["properties"]["live_api_calls_allowed_by_default"]["const"] is False
    assert schema["properties"]["controlled_replay_calls_allowed_by_default"]["const"] is False
    assert schema["properties"]["claim_level"]["const"] == "operational_utility_only/no_claim_upgrade"
    assert schema["properties"]["diagnostic_claim_level"]["const"] == "operational_reprojection_witness"
    assert schema["properties"]["route_5_locked"]["const"] is True
    assert schema["properties"]["route_8_locked"]["const"] is True
    assert schema["properties"]["raw_response_storage_allowed"]["const"] is False
    assert "dry_run_manifest" in schema["required"]
    assert "output_policy" in schema["required"]


def test_post_lapi_reprojection_dry_run_manifest_builds_without_api_or_replay_calls() -> None:
    config = _load_json(CONFIG_PATH)
    dry_run = config["dry_run_manifest"]

    manifest = build_reprojection_manifest(
        run_id=dry_run["run_id"],
        items=dry_run["items"],
        downstream_prompt_template_hash=dry_run["downstream_prompt_hash"],
        model_snapshot=dry_run["model_snapshot"],
        endpoint=dry_run["endpoint"],
        thinking_mode=dry_run["thinking_mode"],
        decoding_policy=dry_run["decoding_policy"],
    )

    assert manifest["live_api_call_performed"] is False
    assert manifest["raw_response_stored"] is False
    assert dry_run["controlled_replay_call_performed"] is False
    assert manifest["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert manifest["route_5_locked"] is True
    assert manifest["route_8_locked"] is True
    assert manifest["pilot_readiness_status"] == "offline_framework_ready_live_api_not_run"
    assert [item["item_id"] for item in manifest["items"]] == sorted(
        item["item_id"] for item in dry_run["items"]
    )
    assert '"raw_response":' not in json.dumps(manifest, sort_keys=True)


def test_post_lapi_reprojection_fixture_witnesses_cover_required_controls() -> None:
    config = _load_json(CONFIG_PATH)
    witness_records = config["dry_run_manifest"]["fixture_witness_records"]

    for record in witness_records:
        assert REQUIRED_CONTROL_FIELDS.issubset(record.keys())
        assert record["raw_response_stored"] is False
        assert record["live_api_call_performed"] is False
        assert record["claim_ledger_entry"]["claim_upgrade"] is False
        assert record["claim_ledger_entry"]["route_5_locked"] is True
        assert record["claim_ledger_entry"]["route_8_locked"] is True
        assert record["claim_ledger_entry"]["raw_response_stored"] is False

        witness = ReprojectionWitness.from_dict(record)
        payload = witness.to_dict(include_claim_ledger=True)
        assert payload["raw_response_stored"] is False
        assert payload["live_api_call_performed"] is False
        assert payload["claim_status"] == "operational_utility_only/no_claim_upgrade"
        assert payload["route_5_locked"] is True
        assert payload["route_8_locked"] is True
        assert payload["candidate_operational_evidence_only"] is True
        assert payload["measurement_validation_claim"] is False
        assert payload["truth_validation_claim"] is False
        assert payload["claim_ledger"]["claim_upgrade"] is False
        assert '"raw_response":' not in json.dumps(payload, sort_keys=True)


def test_post_lapi_reprojection_docs_and_table_template_state_config_only_boundary() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (CONFIG_DOC, TABLE_TEMPLATE)
    )

    assert "operational_utility_only/no_claim_upgrade" in combined
    assert "live api calls run during this config goal: no" in combined
    assert "controlled replay calls run during this config goal: no" in combined
    assert "raw api responses stored: no" in combined
    assert "route 5 locked: yes" in combined
    assert "route 8 locked: yes" in combined
    assert "claim upgrade introduced: no" in combined
    assert "truth correction guarantee" in combined
    assert "metric bridge support" in combined
