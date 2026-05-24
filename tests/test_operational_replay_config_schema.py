from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HOTSPOT_CONFIG = ROOT / "configs" / "experiments" / "hotpotqa_operational_replay_v1.yaml"
FEVER_CONFIG = ROOT / "configs" / "experiments" / "fever_style_sufficiency_v1.yaml"
PLAN_DOC = ROOT / "docs" / "experiments" / "operational-replay-expansion-plan.md"

EXPECTED_BUDGETS = [512, 1024]
DEPLOYABLE_BASELINES = {
    "random_budget",
    "topk_relevance_or_token_budget",
    "mmr_density_greedy",
    "v12_cost_aware_diagnostic_policy_operational_only",
}
OPTIONAL_BASELINES = {
    "seeded_augmented_greedy_operational_only",
    "pair_aware_local_search_operational_only",
    "adaptive_budget_router_operational_only",
}
HARD_OPERATIONAL_METRICS = {
    "supporting_fact_recall",
    "evidence_recall",
    "selected_gold_support_packets",
    "selected_tokens",
    "quality_per_1k_tokens",
    "latency",
    "estimated_cost",
}
WEAK_DIAGNOSTIC_METRICS = {
    "judge_support_rate",
    "judge_insufficient_rate",
    "abstain_rate",
    "order_swap_agreement",
    "parse_failure_rate",
}
CLAIM_LEDGER_FIELDS = {
    "current_claim_level",
    "allowed_claims",
    "denied_claims",
    "claim_upgrade",
    "route_5_locked",
    "route_8_locked",
    "raw_response_stored",
}
COST_LATENCY_FIELDS = {
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "estimated_cost",
    "latency_ms",
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _configs() -> list[dict[str, Any]]:
    return [_load(HOTSPOT_CONFIG), _load(FEVER_CONFIG)]


def _walk(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def test_operational_replay_configs_exist_and_are_json_yaml() -> None:
    hotpotqa = _load(HOTSPOT_CONFIG)
    fever = _load(FEVER_CONFIG)

    assert hotpotqa["dataset"]["name"] == "HotpotQA"
    assert fever["dataset"]["name"] == "FEVER_style_closed_label"
    assert hotpotqa["dataset_sequence"]["primary"] == "HotpotQA"
    assert "FEVER_style_closed_label" in hotpotqa["dataset_sequence"]["deferred"]
    assert fever["dataset_sequence"]["depends_on"] == ["HotpotQA_controlled_replay_acceptance"]
    assert PLAN_DOC.exists()


def test_initial_budgets_and_matched_controls_are_required() -> None:
    for config in _configs():
        assert config["budgets"]["initial"] == EXPECTED_BUDGETS
        assert config["budgets"]["optional_after_pilot"] == [2048]
        controls = config["matched_budget_controls"]
        assert controls["compare_only_with_matched_candidate_pool"] is True
        assert controls["hold_prompt_hash_fixed"] is True
        assert controls["hold_model_snapshot_fixed"] is True
        assert controls["hold_endpoint_and_thinking_mode_fixed"] is True
        assert controls["hold_decoding_policy_fixed"] is True
        assert controls["budget_mismatch_action"] == "stop_fail_closed"
        assert controls["prompt_hash_drift_action"] == "stop_fail_closed"


def test_baseline_registry_separates_deployable_optional_and_oracle() -> None:
    for config in _configs():
        baselines = config["baselines"]
        assert set(baselines["deployable"]) == DEPLOYABLE_BASELINES
        assert set(baselines["optional_after_pilot"]) == OPTIONAL_BASELINES
        assert baselines["non_deployable_upper_bound"] == ["gold_support_oracle_upper_bound"]
        assert "gold_support_oracle_upper_bound" not in baselines["deployable"]
        assert "gold_support_oracle_upper_bound" not in baselines["optional_after_pilot"]


def test_metrics_and_ledgers_match_lapi6_contract() -> None:
    for config in _configs():
        assert set(config["metrics"]["hard_operational"]) == HARD_OPERATIONAL_METRICS
        assert set(config["metrics"]["weak_diagnostic"]) == WEAK_DIAGNOSTIC_METRICS
        assert set(config["cost_latency_ledger_fields"]) == COST_LATENCY_FIELDS
        assert set(config["claim_ledger_fields"]) == CLAIM_LEDGER_FIELDS
        assert config["raw_response_stored"] is False
        assert config["live_api_call_performed"] is False
        assert config["replay_run_performed"] is False


def test_operational_replay_configs_do_not_store_raw_responses_or_run_live_api() -> None:
    for config in _configs():
        for node in _walk(config):
            if "raw_response_stored" in node:
                assert node["raw_response_stored"] is False
            if "raw_api_responses_stored" in node:
                assert node["raw_api_responses_stored"] is False
            if "live_api_call_performed" in node:
                assert node["live_api_call_performed"] is False
            assert "raw_response" not in node
            assert "raw_api_response" not in node


def test_plan_document_scopes_replay_as_future_config_only() -> None:
    text = PLAN_DOC.read_text(encoding="utf-8").lower()

    assert "matched-budget operational evidence" in text
    assert "no replay run has been executed" in text
    assert "operational_utility_only/no_claim_upgrade" in text
    assert "route 5 locked" in text
    assert "route 8 locked" in text
    assert "not selector superiority" in text
    assert "not metric bridge support" in text
    assert "not measurement validation" in text
