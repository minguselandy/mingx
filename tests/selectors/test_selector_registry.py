from __future__ import annotations

from cps.selectors.registry import default_selector_registry
from cps.selectors.workbench_types import SelectionRequest


def _pool() -> dict:
    return {
        "candidate_pool_hash": "pool-hash-1",
        "packets": [
            {
                "content": "Alice founded Example Labs in 1999.",
                "gold_support_label": "gold_supporting",
                "packet_id": "p1",
                "source_doc_id": "Alice",
                "token_cost": 8,
            },
            {
                "content": "Example Labs hired Alice after school.",
                "gold_support_label": "gold_supporting",
                "packet_id": "p2",
                "source_doc_id": "Example Labs",
                "token_cost": 8,
            },
            {
                "content": "Public parks often include libraries.",
                "gold_support_label": "same_context_distractor",
                "packet_id": "p3",
                "source_doc_id": "City",
                "token_cost": 8,
            },
        ],
    }


def test_default_selector_registry_has_required_workbench_selectors():
    registry = default_selector_registry()

    assert {"bm25_topk", "mmr_density_greedy", "v12_diagnostic_policy"} <= set(registry.names())


def test_registered_selectors_share_candidate_pool_and_budget_contract():
    registry = default_selector_registry()
    request = SelectionRequest(
        dataset="HotpotQA",
        instance_id="hp-1",
        query="Who founded Example Labs?",
        candidate_pool=_pool(),
        budget=16,
        role="evidence_grounded_answerer",
    )

    results = [registry.select(name, request) for name in ("bm25_topk", "mmr_density_greedy", "v12_diagnostic_policy")]

    assert {result.candidate_pool_hash for result in results} == {"pool-hash-1"}
    assert all(result.budget_used <= 16 for result in results)
    assert all(set(result.selected_packet_ids) | set(result.excluded_packet_ids) == {"p1", "p2", "p3"} for result in results)
    assert results[-1].metric_claim_level == "operational_utility_only"
    assert results[-1].selector_regime_label in {"greedy_supported", "pairwise_escalate", "higher_order_risk", "ambiguous"}
