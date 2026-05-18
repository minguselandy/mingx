from __future__ import annotations

from cps.evaluators.registry import default_evaluator_registry
from cps.evaluators.workbench_types import EvaluationRequest


def _request() -> EvaluationRequest:
    return EvaluationRequest(
        dataset="HotpotQA",
        instance_id="hp-1",
        query="Who founded Example Labs?",
        target={"label": "Alice", "target_type": "answer_string"},
        candidate_pool_hash="pool-hash-1",
        selected_packets=[
            {
                "content": "Alice founded Example Labs in 1999.",
                "gold_support_label": "gold_supporting",
                "packet_id": "p1",
                "token_cost": 8,
            }
        ],
        all_packets=[
            {
                "content": "Alice founded Example Labs in 1999.",
                "gold_support_label": "gold_supporting",
                "packet_id": "p1",
                "token_cost": 8,
            },
            {
                "content": "Example Labs hired Alice after school.",
                "gold_support_label": "gold_supporting",
                "packet_id": "p2",
                "token_cost": 8,
            },
        ],
        claim_mode="shadow",
    )


def test_default_evaluator_registry_has_shadow_safe_evaluators():
    registry = default_evaluator_registry()

    assert {"operational", "sufficiency", "logloss", "diagnostic_safety", "claim_ledger"} <= set(registry.names())


def test_operational_evaluator_runs_without_live_api():
    result = default_evaluator_registry().evaluate("operational", _request())

    assert result.evaluator_name == "operational"
    assert result.metrics["supporting_fact_recall_at_budget"] == 0.5
    assert result.metrics["answer_available_if_present"] is True
    assert result.claim_mode == "shadow"
    assert result.claim_flags["measurement_validated"] is False


def test_shadow_evaluators_do_not_emit_accepted_proxy_or_measurement_claims():
    registry = default_evaluator_registry()

    sufficiency = registry.evaluate("sufficiency", _request())
    logloss = registry.evaluate("logloss", _request())
    safety = registry.evaluate("diagnostic_safety", _request())

    assert sufficiency.claim_flags["shadow_measurement_candidate"] is True
    assert logloss.claim_flags["shadow_vinfo_proxy"] is True
    assert safety.claim_flags["calibrated_proxy_supported"] is False
    assert safety.claim_flags["vinfo_proxy_supported"] is False
    assert safety.claim_flags["selector_superiority_claimed"] is False
