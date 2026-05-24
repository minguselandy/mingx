from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from cps.evaluation.sufficiency_regime import (
    SufficiencyRegimeRecord,
    build_sufficiency_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "post_lapi" / "sufficiency_abstention_config.yaml"
SCHEMA_PATH = ROOT / "schemas" / "post_lapi_sufficiency_abstention.schema.json"
CONFIG_DOC = ROOT / "docs" / "experiments" / "POST-LAPI-sufficiency-abstention-config.md"
TABLE_TEMPLATE = ROOT / "docs" / "paper" / "post-lapi-sufficiency-abstention-table-template.md"

REQUIRED_LABELS = {
    "support",
    "insufficient",
    "contradict",
    "uncertain",
    "parse_failed",
}
REQUIRED_ADDITIONAL_FIELDS = {
    "abstain_recommended",
    "missing_evidence_type",
    "confidence_bucket",
    "prompt_hash",
    "model_snapshot",
    "endpoint",
    "raw_response_stored",
}
REQUIRED_REGIMES = {
    "sufficient_kept",
    "sufficient_dropped",
    "insufficient_and_answered",
    "insufficient_and_abstained",
}
REQUIRED_METRICS = {
    "support_rate",
    "insufficient_rate",
    "contradict_rate",
    "uncertain_rate",
    "parse_failed_rate",
    "abstain_rate",
    "abstain_when_insufficient_rate",
    "unsafe_answer_rate",
    "missing_evidence_type_distribution",
    "cost_per_case",
    "latency_per_case",
}
ALLOWED_CLAIMS = {
    "sufficiency_abstention_diagnostic",
    "model_adjudicated_weak_evidence",
    "operational_utility_only",
}
DENIED_CLAIMS = {
    "truth_validation",
    "human_calibrated_abstention",
    "measurement_validation",
    "paper_grade_evidence",
}


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_post_lapi_sufficiency_config_schema_docs_and_template_exist() -> None:
    assert CONFIG_PATH.exists()
    assert SCHEMA_PATH.exists()
    assert CONFIG_DOC.exists()
    assert TABLE_TEMPLATE.exists()


def test_post_lapi_sufficiency_config_pins_required_labels_fields_regimes_and_metrics() -> None:
    config = _load_json(CONFIG_PATH)

    assert config["pilot_id"] == "post_lapi_sufficiency_abstention"
    assert set(config["labels"]) == REQUIRED_LABELS
    assert set(config["additional_fields"]) == REQUIRED_ADDITIONAL_FIELDS
    assert {row["regime"] for row in config["regime_ledger"]} == REQUIRED_REGIMES
    assert set(config["metrics"]) == REQUIRED_METRICS
    assert set(config["claim"]["allowed"]) == ALLOWED_CLAIMS
    assert set(config["claim"]["denied"]) == DENIED_CLAIMS


def test_post_lapi_sufficiency_config_is_config_only_and_claim_safe() -> None:
    config = _load_json(CONFIG_PATH)

    assert config["configuration_only_default"] is True
    assert config["live_api_calls_allowed_by_default"] is False
    assert config["model_judging_allowed_by_default"] is False
    assert config["requires_explicit_approval_to_run"] is True
    assert config["claim_level"] == "operational_utility_only/no_claim_upgrade"
    assert config["diagnostic_claim_level"] == "sufficiency_abstention_diagnostic_only"
    assert config["route_5_locked"] is True
    assert config["route_8_locked"] is True
    assert config["raw_response_storage_allowed"] is False
    assert config["raw_response_stored"] is False
    assert config["field_defaults"]["raw_response_stored"] is False
    assert config["field_defaults"]["live_api_call_performed"] is False
    assert config["field_defaults"]["measurement_validation_claim"] is False
    assert config["field_defaults"]["truth_validation_claim"] is False
    assert config["output_policy"]["store_raw_api_responses"] is False
    assert config["output_policy"]["measurement_validation_claim"] is False
    assert config["output_policy"]["truth_validation_claim"] is False
    assert config["output_policy"]["claim_upgrade_introduced"] is False


def test_post_lapi_sufficiency_schema_pins_fail_closed_config_contract() -> None:
    schema = _load_json(SCHEMA_PATH)

    assert schema["properties"]["pilot_id"]["const"] == "post_lapi_sufficiency_abstention"
    assert schema["properties"]["configuration_only_default"]["const"] is True
    assert schema["properties"]["live_api_calls_allowed_by_default"]["const"] is False
    assert schema["properties"]["model_judging_allowed_by_default"]["const"] is False
    assert schema["properties"]["claim_level"]["const"] == "operational_utility_only/no_claim_upgrade"
    assert schema["properties"]["diagnostic_claim_level"]["const"] == "sufficiency_abstention_diagnostic_only"
    assert schema["properties"]["route_5_locked"]["const"] is True
    assert schema["properties"]["route_8_locked"]["const"] is True
    assert schema["properties"]["raw_response_storage_allowed"]["const"] is False
    assert "dry_run_input_selection" in schema["required"]
    assert "output_policy" in schema["required"]


def test_post_lapi_sufficiency_prompt_template_exists_and_keeps_boundary_language() -> None:
    config = _load_json(CONFIG_PATH)
    prompt_paths = {ROOT / item["prompt_path"] for item in config["prompt_templates"]}

    assert prompt_paths == {
        ROOT / "prompts" / "reprojection" / "sufficiency_abstention_v1.md",
    }
    for path in prompt_paths:
        text = path.read_text(encoding="utf-8").lower()
        assert "sufficiency_abstention_diagnostic_only" in text
        assert "operational_utility_only/no_claim_upgrade" in text
        assert "not human/external gold" in text
        assert "not measurement validation" in text
        assert "provider body" in text


def test_post_lapi_sufficiency_dry_run_manifest_builds_without_api_calls() -> None:
    config = _load_json(CONFIG_PATH)
    dry_run = config["dry_run_input_selection"]

    manifest = build_sufficiency_manifest(
        run_id=dry_run["run_id"],
        items=dry_run["fixture_items"],
        downstream_prompt_template_hash=dry_run["downstream_prompt_template_hash"],
    )

    assert manifest["live_api_call_performed"] is False
    assert manifest["raw_response_stored"] is False
    assert manifest["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert manifest["claim_level"] == "sufficiency_abstention_diagnostic_only"
    assert manifest["route_5_locked"] is True
    assert manifest["route_8_locked"] is True
    assert manifest["pilot_readiness_status"] == "offline_framework_ready_live_api_not_run"
    assert "prompts/reprojection/sufficiency_abstention_v1.md" in manifest["prompt_hashes"]
    assert [item["item_id"] for item in manifest["items"]] == sorted(
        item["item_id"] for item in dry_run["fixture_items"]
    )
    assert '"raw_response":' not in json.dumps(manifest, sort_keys=True)


def test_post_lapi_sufficiency_dry_run_records_cover_required_regimes_without_api_calls() -> None:
    config = _load_json(CONFIG_PATH)
    fixture_records = config["dry_run_input_selection"]["fixture_records"]
    records = [SufficiencyRegimeRecord.from_dict(record) for record in fixture_records]
    payloads = [record.to_dict() for record in records]

    assert {payload["regime_label"] for payload in payloads} == REQUIRED_REGIMES
    for payload in payloads:
        assert payload["claim_status"] == "operational_utility_only/no_claim_upgrade"
        assert payload["claim_level"] == "sufficiency_abstention_diagnostic_only"
        assert payload["candidate_operational_evidence_only"] is True
        assert payload["raw_response_stored"] is False
        assert payload["live_api_call_performed"] is False
        assert payload["measurement_validation_claim"] is False
        assert payload["truth_validation_claim"] is False
        assert payload["human_external_gold_label"] is False
        assert payload["route_5_locked"] is True
        assert payload["route_8_locked"] is True


def test_post_lapi_sufficiency_docs_and_table_template_state_config_only_boundary() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (CONFIG_DOC, TABLE_TEMPLATE)
    )

    assert "operational_utility_only/no_claim_upgrade" in combined
    assert "live api calls run during this config goal: no" in combined
    assert "new model judging run during this config goal: no" in combined
    assert "raw api responses stored: no" in combined
    assert "route 5 locked: yes" in combined
    assert "route 8 locked: yes" in combined
    assert "claim upgrade introduced: no" in combined
    assert "measurement validation" in combined
    assert "truth validation" in combined
