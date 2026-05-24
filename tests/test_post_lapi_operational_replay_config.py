from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cps.benchmarks.candidate_pool_manifest import build_candidate_pool_manifest


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "post_lapi" / "operational_replay_expansion_config.yaml"
DOC = ROOT / "docs" / "experiments" / "POST-LAPI-operational-replay-config.md"
TABLE_TEMPLATE = ROOT / "docs" / "paper" / "post-lapi-operational-replay-table-template.md"

DEPLOYABLE_BASELINES = {
    "random_budget",
    "topk_relevance_or_token_budget",
    "mmr_density_greedy",
    "v12_cost_aware_diagnostic_policy_operational_only",
}
OPTIONAL_BASELINES = {
    "dashscope_llm_prune_extract_operational_only",
    "adaptive_budget_router_operational_only",
}
REQUIRED_METRICS = [
    "supporting_fact_recall",
    "evidence_recall",
    "selected_tokens",
    "quality_per_1k_tokens",
    "latency",
    "cost",
    "parse_success_rate",
    "claim_gate_distribution",
    "abstain_rate",
]
FIXED_DOWNSTREAM_CONDITIONS = {
    "candidate_pool_hash",
    "budget",
    "downstream_prompt_hash",
    "model_snapshot",
    "endpoint",
    "thinking_mode",
    "decoding_policy",
    "token_budget_accounting",
}
DENIED_CLAIMS = {
    "selector_superiority",
    "global_selector_superiority",
    "metric_bridge_support",
    "measurement_validation",
    "V_information_verification",
    "calibrated_proxy_supported",
    "vinfo_proxy_supported",
    "teacher_forced_nll_support",
    "route_5_unlock",
    "route_8_unlock",
}


def _load() -> dict[str, Any]:
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
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


def test_post_lapi_replay_config_and_docs_exist() -> None:
    assert CONFIG.exists()
    assert DOC.exists()
    assert TABLE_TEMPLATE.exists()


def test_dataset_registry_is_config_only_and_deferred_where_required() -> None:
    config = _load()
    registry = config["replay_config_registry"]

    assert [entry["priority"] for entry in registry] == [1, 2, 3]
    assert registry[0]["dataset"] == "HotpotQA_continuation"
    assert registry[0]["config_path"] == "configs/experiments/hotpotqa_operational_replay_v1.yaml"
    assert registry[1]["dataset"] == "FEVER_style_closed_label"
    assert registry[1]["config_path"] == "configs/experiments/fever_style_sufficiency_v1.yaml"
    assert registry[2]["dataset"] == "2Wiki_or_MuSiQue_later_only"
    assert registry[2]["status"] == "deferred_until_post6_config_passes_and_owner_approves"

    for entry in registry:
        assert entry["run_now"] is False
        assert entry["live_api_needed_for_config"] is False
        assert entry["replay_pilot_run_performed"] is False

    assert set(config["do_not_start_until_owner_approval"]) == {"2Wiki", "MuSiQue"}


def test_baseline_registry_separates_deployable_optional_and_oracle() -> None:
    registry = _load()["baseline_registry"]

    deployable = {entry["baseline_id"] for entry in registry["deployable"] if entry["enabled"]}
    optional = {entry["baseline_id"] for entry in registry["optional_candidates"]}
    disabled_optional = {entry["baseline_id"] for entry in registry["optional_candidates"] if not entry["enabled"]}
    oracle = registry["oracle"]

    assert deployable == DEPLOYABLE_BASELINES
    assert optional == OPTIONAL_BASELINES
    assert disabled_optional == OPTIONAL_BASELINES
    assert oracle == [
        {
            "baseline_id": "gold_support_oracle_upper_bound",
            "enabled": True,
            "claim_scope": "non_deployable_upper_bound",
            "deployable": False,
            "reporting_rule": "must_be_marked_non_deployable_upper_bound",
        }
    ]


def test_metrics_manifest_contracts_and_fixed_controls_are_present() -> None:
    config = _load()

    assert config["metrics"] == REQUIRED_METRICS
    assert set(config["fixed_downstream_conditions"]) == FIXED_DOWNSTREAM_CONDITIONS

    controls = config["matched_budget_controls"]
    assert controls["compare_only_with_matched_candidate_pool"] is True
    assert controls["hold_budget_fixed"] is True
    assert controls["hold_downstream_prompt_hash_fixed"] is True
    assert controls["hold_model_snapshot_fixed"] is True
    assert controls["hold_endpoint_fixed"] is True
    assert controls["hold_thinking_mode_fixed"] is True
    assert controls["hold_decoding_policy_fixed"] is True
    assert controls["budget_mismatch_action"] == "stop_fail_closed"
    assert controls["prompt_hash_drift_action"] == "stop_fail_closed"
    assert controls["model_snapshot_mismatch_action"] == "stop_fail_closed"
    assert controls["candidate_pool_mismatch_action"] == "stop_fail_closed"

    manifest = config["manifest_contracts"]
    assert manifest["candidate_pool_manifest"]["builder"] == (
        "cps.benchmarks.candidate_pool_manifest.build_candidate_pool_manifest"
    )
    assert set(manifest["claim_ledger"]["required_fields"]) >= {
        "current_claim_level",
        "allowed_claims",
        "denied_claims",
        "claim_upgrade",
        "route_5_locked",
        "route_8_locked",
        "raw_response_stored",
    }
    assert set(manifest["cost_latency_ledger"]["required_fields"]) >= {
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "estimated_cost",
        "latency_ms",
    }


def test_claim_boundary_denies_upgrade_and_keeps_routes_locked() -> None:
    config = _load()

    assert config["claim_level"] == "operational_utility_only/no_claim_upgrade"
    assert config["diagnostic_claim_level"] == "scoped_operational_improvement_under_matched_budgets_only"
    assert set(config["claim"]["allowed"]) == {
        "scoped_operational_improvement_under_matched_budgets",
        "operational_utility_only",
    }
    assert set(config["claim"]["denied"]) >= DENIED_CLAIMS
    assert config["route_5_locked"] is True
    assert config["route_8_locked"] is True
    assert config["output_policy"]["claim_upgrade_introduced"] is False
    assert config["metric_bridge_claim_allowed"] is False
    assert config["calibrated_proxy_supported"] is False
    assert config["vinfo_proxy_supported"] is False
    assert config["teacher_forced_nll_allowed"] is False


def test_config_goal_does_not_run_live_api_replay_or_store_raw_responses() -> None:
    config = _load()

    assert config["configuration_only_default"] is True
    assert config["live_api_calls_allowed_by_default"] is False
    assert config["operational_replay_pilot_allowed_by_default"] is False
    assert config["dataset_scale_execution_allowed_by_default"] is False
    assert config["live_api_call_performed"] is False
    assert config["operational_replay_pilot_performed"] is False
    assert config["replay_run_performed"] is False
    assert config["raw_response_storage_allowed"] is False
    assert config["raw_response_stored"] is False
    assert config["raw_api_responses_stored"] is False

    for node in _walk(config):
        if "raw_response_stored" in node:
            assert node["raw_response_stored"] is False
        if "raw_api_responses_stored" in node:
            assert node["raw_api_responses_stored"] is False
        if "live_api_call_performed" in node:
            assert node["live_api_call_performed"] is False
        assert "raw_response" not in node
        assert "raw_api_response" not in node


def test_dry_run_manifest_is_static_and_schema_valid_without_execution() -> None:
    dry_run = _load()["dry_run_manifest"]
    manifest = build_candidate_pool_manifest(
        [{"candidate_pool": pool} for pool in dry_run["fixture_candidate_pools"]],
        dataset=dry_run["dataset"],
        budgets=dry_run["budgets"],
    )

    assert dry_run["run_id"] == "post_lapi_operational_replay_config_dry_run"
    assert dry_run["live_api_call_performed"] is False
    assert dry_run["operational_replay_pilot_performed"] is False
    assert dry_run["raw_response_stored"] is False
    assert manifest["schema_valid"] is True
    assert manifest["claim_status"] == "operational_utility_only; no_claim_upgrade"
    assert manifest["dataset"] == "HotpotQA"
    assert manifest["gold_reachable_by_budget"] == {"512": 1, "1024": 1}


def test_docs_and_template_state_config_only_boundaries() -> None:
    doc_text = DOC.read_text(encoding="utf-8")
    table_text = TABLE_TEMPLATE.read_text(encoding="utf-8")

    for text in (doc_text, table_text):
        lower = text.lower()
        assert "operational_utility_only/no_claim_upgrade" in text
        assert "selector superiority" in lower
        assert "metric bridge support" in lower
        assert "measurement validation" in lower
        assert "route 5" in lower
        assert "route 8" in lower

    assert "configuration only" in doc_text.lower()
    assert "no POST-6 replay results are reported here" in table_text
