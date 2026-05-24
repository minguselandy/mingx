from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from cps.extraction.audit_schema import build_extraction_audit_manifest
from cps.extraction.extraction_risk_ledger import build_extraction_risk_ledger


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "post_lapi" / "extraction_quality_audit_config.yaml"
SCHEMA_PATH = ROOT / "schemas" / "post_lapi_extraction_quality.schema.json"
CONFIG_DOC = ROOT / "docs" / "experiments" / "POST-LAPI-extraction-quality-audit-config.md"
TABLE_TEMPLATE = ROOT / "docs" / "paper" / "post-lapi-extraction-quality-table-template.md"

REQUIRED_STRATA = {
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
REQUIRED_LABELS = {
    "captured",
    "captured_core_preserved",
    "captured_core_materially_changed",
    "missing",
    "lost_qualifier",
    "temporal_scope_error",
    "provenance_loss",
    "selector_impact",
}
REQUIRED_METRICS = {
    "completeness_by_stratum",
    "value_weighted_loss_proxy",
    "qualifier_loss_rate",
    "temporal_scope_error_rate",
    "provenance_loss_rate",
    "selector_impact_rate",
}
ALLOWED_CLAIMS = {
    "model_adjudicated_extraction_risk_evidence",
    "operational_extraction_audit",
}
DENIED_CLAIMS = {
    "human_validated_extraction_measurement",
    "measurement_validation",
    "theorem_transfer_to_M_star",
    "end_to_end_validation",
    "end_to_end_measurement_validation",
    "metric_bridge_support",
    "calibrated_proxy_supported",
    "vinfo_proxy_supported",
    "paper_evidence",
    "selector_superiority",
    "global_selector_superiority",
    "route_5_unlock",
    "route_8_unlock",
}


def _load_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def test_post_lapi_extraction_quality_files_exist() -> None:
    assert CONFIG_PATH.exists()
    assert SCHEMA_PATH.exists()
    assert CONFIG_DOC.exists()
    assert TABLE_TEMPLATE.exists()


def test_config_pins_required_strata_labels_metrics_and_claims() -> None:
    config = _load_json(CONFIG_PATH)

    assert config["audit_id"] == "post_lapi_extraction_quality_audit"
    assert config["goal_id"] == "POST-7-CONFIG"
    assert set(config["strata"]) == REQUIRED_STRATA
    assert set(config["labels"]) == REQUIRED_LABELS
    assert set(config["metrics"]) == REQUIRED_METRICS
    assert set(config["claim"]["allowed"]) == ALLOWED_CLAIMS
    assert set(config["claim"]["denied"]) >= DENIED_CLAIMS
    assert config["metric_definitions"]["completeness_by_stratum"]["implementation_metric"] == (
        "capture_rate_by_stratum"
    )
    assert config["metric_definitions"]["value_weighted_loss_proxy"]["implementation_metric"] == (
        "value_weighted_loss_candidate"
    )


def test_config_is_configuration_only_and_claim_safe() -> None:
    config = _load_json(CONFIG_PATH)

    assert config["configuration_only_default"] is True
    assert config["live_api_calls_allowed_by_default"] is False
    assert config["model_adjudicated_extraction_run_allowed_by_default"] is False
    assert config["requires_explicit_approval_to_run_if_model_adjudicated"] is True
    assert config["claim_level"] == "operational_utility_only/no_claim_upgrade"
    assert config["route_5_locked"] is True
    assert config["route_8_locked"] is True
    assert config["raw_response_storage_allowed"] is False
    assert config["raw_response_stored"] is False
    assert config["raw_api_responses_stored"] is False
    assert config["human_validation_claim_allowed"] is False
    assert config["measurement_validation_claim_allowed"] is False
    assert config["claim_upgrade_introduced"] is False
    assert config["output_policy"]["store_raw_api_responses"] is False
    assert config["output_policy"]["counts_as_human_validation"] is False
    assert config["output_policy"]["human_validation_claim"] is False
    assert config["output_policy"]["measurement_validation_claim"] is False
    assert config["output_policy"]["claim_upgrade_introduced"] is False
    assert "later POST-7 run-pilot goal only" in config["run_execution_approval_scope"]


def test_schema_pins_required_fail_closed_fields() -> None:
    schema = _load_json(SCHEMA_PATH)

    assert schema["properties"]["audit_id"]["const"] == "post_lapi_extraction_quality_audit"
    assert schema["properties"]["goal_id"]["const"] == "POST-7-CONFIG"
    assert schema["properties"]["configuration_only_default"]["const"] is True
    assert schema["properties"]["live_api_calls_allowed_by_default"]["const"] is False
    assert schema["properties"]["model_adjudicated_extraction_run_allowed_by_default"]["const"] is False
    assert schema["properties"]["claim_level"]["const"] == "operational_utility_only/no_claim_upgrade"
    assert schema["properties"]["route_5_locked"]["const"] is True
    assert schema["properties"]["route_8_locked"]["const"] is True
    assert schema["properties"]["raw_response_storage_allowed"]["const"] is False
    assert schema["properties"]["human_validation_claim_allowed"]["const"] is False
    assert schema["properties"]["measurement_validation_claim_allowed"]["const"] is False
    assert set(schema["properties"]["strata"]["items"]["enum"]) == REQUIRED_STRATA
    assert set(schema["properties"]["labels"]["items"]["enum"]) == REQUIRED_LABELS
    assert set(schema["properties"]["metrics"]["items"]["enum"]) == REQUIRED_METRICS
    assert "dry_run_manifest" in schema["required"]
    assert "output_policy" in schema["required"]


def test_dry_run_manifest_builds_without_api_calls_or_model_judging() -> None:
    config = _load_json(CONFIG_PATH)
    dry_run = config["dry_run_manifest"]

    manifest = build_extraction_audit_manifest(
        run_id=dry_run["run_id"],
        items=dry_run["fixture_items"],
    )
    ledger = build_extraction_risk_ledger(dry_run["fixture_records"]).to_dict(
        include_claim_ledger=True
    )

    assert manifest["run_id"] == "post_lapi_extraction_quality_config_dry_run"
    assert manifest["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert manifest["live_api_call_performed"] is False
    assert manifest["raw_response_stored"] is False
    assert manifest["route_5_locked"] is True
    assert manifest["route_8_locked"] is True
    assert sorted(item["item_id"] for item in manifest["items"]) == [
        "extract-dry-run-item-1",
        "extract-dry-run-item-2",
    ]
    assert dry_run["live_api_call_performed"] is False
    assert dry_run["model_adjudicated_extraction_run_performed"] is False
    assert dry_run["raw_response_stored"] is False
    assert ledger["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert ledger["allowed_claims"] == ["model_adjudicated_extraction_risk_evidence"]
    assert ledger["claim_ledger"]["claim_upgrade"] is False
    assert ledger["claim_ledger"]["route_5_locked"] is True
    assert ledger["claim_ledger"]["route_8_locked"] is True
    assert ledger["raw_response_stored"] is False
    assert ledger["live_api_call_performed"] is False


def test_config_text_has_no_active_live_raw_or_upgrade_flags() -> None:
    config = _load_json(CONFIG_PATH)

    for node in _walk(config):
        if "raw_response_stored" in node:
            assert node["raw_response_stored"] is False
        if "raw_api_responses_stored" in node:
            assert node["raw_api_responses_stored"] is False
        if "live_api_call_performed" in node:
            assert node["live_api_call_performed"] is False
        if "model_adjudicated_extraction_run_performed" in node:
            assert node["model_adjudicated_extraction_run_performed"] is False
        assert "raw_response" not in node
        assert "raw_api_response" not in node

    text = CONFIG_PATH.read_text(encoding="utf-8").lower()
    for forbidden in (
        '"claim_upgrade_introduced": true',
        '"human_validation_claim_allowed": true',
        '"measurement_validation_claim_allowed": true',
        '"route_5_locked": false',
        '"route_8_locked": false',
        '"store_raw_api_responses": true',
        '"live_api_call_performed": true',
        '"model_adjudicated_extraction_run_performed": true',
    ):
        assert forbidden not in text


def test_docs_and_table_template_state_config_only_boundary() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (CONFIG_DOC, TABLE_TEMPLATE)
    )

    assert "operational_utility_only/no_claim_upgrade" in combined
    assert "live api calls run during this config goal: no" in combined
    assert "model-adjudicated extraction run during this config goal: no" in combined
    assert "raw api responses stored: no" in combined
    assert "human validation claim introduced: no" in combined
    assert "measurement validation claim introduced: no" in combined
    assert "claim upgrade introduced: no" in combined
    assert "route 5 locked: yes" in combined
    assert "route 8 locked: yes" in combined
    assert "theorem transfer to m*" in combined
    assert "end-to-end validation" in combined
    assert "selector superiority" in combined
