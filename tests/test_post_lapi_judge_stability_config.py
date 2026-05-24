from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from cps.judge.judge_manifest import build_judge_run_manifest


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "post_lapi" / "judge_stability_pilot_config.yaml"
SCHEMA_PATH = ROOT / "schemas" / "post_lapi_judge_stability.schema.json"
CONFIG_DOC = ROOT / "docs" / "experiments" / "POST-LAPI-judge-stability-config.md"
TABLE_TEMPLATE = ROOT / "docs" / "paper" / "post-lapi-judge-stability-table-template.md"

REQUIRED_CONDITIONS = {
    "original_order",
    "order_swapped",
    "duplicate_judging",
    "rubric_paraphrase",
}
REQUIRED_LABELS = {
    "support",
    "insufficient",
    "contradict",
    "uncertain",
    "parse_failed",
}
REQUIRED_METRICS = {
    "parse_success_rate",
    "duplicate_agreement",
    "order_swap_agreement",
    "rubric_paraphrase_agreement",
    "confidence_bucket_stability",
    "position_bias_rate",
    "uncertain_rate",
    "parse_failed_rate",
    "cost_per_judgment",
    "latency_per_judgment",
}
ALLOWED_CLAIMS = {
    "model_adjudicated_weak_evidence",
    "operational_diagnostic_evidence",
}
DENIED_CLAIMS = {
    "human_gold",
    "measurement_validation",
    "judge_validation",
    "paper_grade_evidence",
    "selector_superiority",
}


def _load_json(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_post_lapi_judge_config_and_schema_exist() -> None:
    assert CONFIG_PATH.exists()
    assert SCHEMA_PATH.exists()
    assert CONFIG_DOC.exists()
    assert TABLE_TEMPLATE.exists()


def test_post_lapi_judge_config_pins_conditions_labels_metrics_and_claims() -> None:
    config = _load_json(CONFIG_PATH)

    assert config["pilot_id"] == "post_lapi_judge_stability"
    assert set(config["conditions"]) == REQUIRED_CONDITIONS
    assert set(config["labels"]) == REQUIRED_LABELS
    assert set(config["metrics"]) == REQUIRED_METRICS
    assert set(config["claim"]["allowed"]) == ALLOWED_CLAIMS
    assert DENIED_CLAIMS.issubset(set(config["claim"]["denied"]))


def test_post_lapi_judge_config_is_config_only_and_claim_safe() -> None:
    config = _load_json(CONFIG_PATH)

    assert config["configuration_only_default"] is True
    assert config["live_api_calls_allowed_by_default"] is False
    assert config["model_judging_allowed_by_default"] is False
    assert config["silver_label_scaling_allowed"] is False
    assert config["requires_explicit_approval_to_run"] is True
    assert config["claim_level"] == "operational_utility_only/no_claim_upgrade"
    assert config["route_5_locked"] is True
    assert config["route_8_locked"] is True
    assert config["raw_response_storage_allowed"] is False
    assert config["raw_response_stored"] is False
    assert config["output_policy"]["store_raw_api_responses"] is False
    assert config["output_policy"]["counts_as_human_or_external_gold"] is False
    assert config["output_policy"]["measurement_validation_claim"] is False
    assert config["output_policy"]["claim_upgrade_introduced"] is False
    assert "later POST-3 run-pilot goal only" in config["pilot_execution_approval_scope"]


def test_post_lapi_judge_schema_pins_fail_closed_config_contract() -> None:
    schema = _load_json(SCHEMA_PATH)

    assert schema["properties"]["pilot_id"]["const"] == "post_lapi_judge_stability"
    assert schema["properties"]["configuration_only_default"]["const"] is True
    assert schema["properties"]["live_api_calls_allowed_by_default"]["const"] is False
    assert schema["properties"]["model_judging_allowed_by_default"]["const"] is False
    assert schema["properties"]["claim_level"]["const"] == "operational_utility_only/no_claim_upgrade"
    assert schema["properties"]["route_5_locked"]["const"] is True
    assert schema["properties"]["route_8_locked"]["const"] is True
    assert schema["properties"]["raw_response_storage_allowed"]["const"] is False
    assert "dry_run_manifest" in schema["required"]
    assert "output_policy" in schema["required"]


def test_post_lapi_judge_prompt_assets_exist_and_keep_boundary_language() -> None:
    config = _load_json(CONFIG_PATH)
    prompt_paths = {ROOT / asset["prompt_path"] for asset in config["prompt_assets"]}

    assert prompt_paths == {
        ROOT / "prompts" / "judge" / "weak_evidence_v1.md",
        ROOT / "prompts" / "judge" / "weak_evidence_v1_order_swapped.md",
    }
    for path in prompt_paths:
        text = path.read_text(encoding="utf-8").lower()
        assert "model-adjudicated weak evidence" in text
        assert "not human/external gold" in text
        assert "not measurement validation" in text
        assert "raw api response" not in text


def test_post_lapi_judge_dry_run_manifest_builds_without_api_calls() -> None:
    config = _load_json(CONFIG_PATH)
    dry_run = config["dry_run_manifest"]

    manifest = build_judge_run_manifest(
        run_id=dry_run["run_id"],
        items=dry_run["fixture_items"],
        judge_model_snapshot="static-judge-snapshot",
    )

    expected_count = len(dry_run["fixture_items"]) * dry_run["expected_request_count_per_item"]
    assert len(manifest["judgment_requests"]) == expected_count
    assert manifest["live_api_call_performed"] is False
    assert manifest["raw_response_stored"] is False
    assert manifest["claim_status"] == "operational_utility_only/no_claim_upgrade"
    assert manifest["route_5_locked"] is True
    assert manifest["route_8_locked"] is True
    assert manifest["allowed_claim_level"] == "model_adjudicated_weak_evidence"
    assert '"raw_response":' not in json.dumps(manifest, sort_keys=True)


def test_post_lapi_judge_docs_and_table_template_state_config_only_boundary() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (CONFIG_DOC, TABLE_TEMPLATE)
    )

    assert "operational_utility_only/no_claim_upgrade" in combined
    assert "live api calls run during this config goal: no" in combined
    assert "model judging run during this config goal: no" in combined
    assert "raw api responses stored: no" in combined
    assert "route 5 locked: yes" in combined
    assert "route 8 locked: yes" in combined
    assert "claim upgrade introduced: no" in combined
    assert "measurement validation" in combined
    assert "selector superiority" in combined
