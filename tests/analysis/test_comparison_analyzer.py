from __future__ import annotations

from cps.analysis.comparison_analyzer import analyze_selector_comparison


def _record(selector: str, recall: float) -> dict:
    return {
        "budget": 512,
        "candidate_pool_hash": "pool-hash-1",
        "dataset": "HotpotQA",
        "evaluation": {"supporting_fact_recall_at_budget": recall, "selected_tokens": 10},
        "metric_claim_level": "operational_utility_only",
        "selector_name": selector,
    }


def test_comparison_analyzer_outputs_shadow_superiority_gate():
    result = analyze_selector_comparison(
        [_record("bm25_topk", 0.5), _record("mmr_density_greedy", 0.5), _record("v12_diagnostic_policy", 1.0)],
        target_selector="v12_diagnostic_policy",
    )

    assert result["superiority_claim_gate"]["claim_mode"] == "shadow"
    assert result["superiority_claim_gate"]["selector_superiority_claimed"] is False
    assert result["superiority_claim_gate"]["global_selector_superiority"] is False
    assert result["diagnostic_safety_report"]["metric_claim_level"] == "operational_utility_only"
    assert result["statistical_tests"]["v12_diagnostic_policy::vs::bm25_topk::budget_512"]["mean_delta"] == 0.5
